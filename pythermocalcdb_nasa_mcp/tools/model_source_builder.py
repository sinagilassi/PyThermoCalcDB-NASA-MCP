# SECTION: Imports
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, List
from pyThermoLinkDB import (
    build_components_model_source,
    build_model_source
)
from pyThermoLinkDB.models import (
    ComponentModelSource,
    ModelSource
)
from pythermodb_settings.models import Component
from pyThermoDB import (
    ComponentThermoDB,
    build_component_thermodb_from_reference,
)
from pythermocalcdb_nasa import (
    build_model_source_from_database as build_nasa_model_source_from_database,
    check_component_availability,
)
from pythermocalcdb_nasa_mcp.interface.validation import validate_reference_content
from pythermocalcdb_nasa_mcp.models.nasa import Source, TemperatureInput

# NOTE: logger
logger = logging.getLogger(__name__)


# SECTION: ModelSource builder result
@dataclass(frozen=True)
class ModelSourceBuildResult:
    success: bool
    message: str
    source: Source
    model_source: Optional[ModelSource] = None
    components: List[Component] = field(default_factory=list)
    analysis: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# SECTION: Build ModelSource from selected source
def build_model_source_for_request(
        components: List[Component],
        temperature: TemperatureInput,
        source: Source,
        reference_content: str | None = None,
) -> ModelSourceBuildResult:
    if source == "database":
        return _build_model_source_from_database(
            components=components,
            temperature=temperature,
        )

    if not reference_content or not reference_content.strip():
        return ModelSourceBuildResult(
            success=False,
            message="reference_content must not be blank when source='reference'.",
            source=source,
        )

    reference_validation = validate_reference_content(reference_content)
    if not reference_validation.success:
        return ModelSourceBuildResult(
            success=False,
            message=reference_validation.message,
            source=source,
            warnings=list(reference_validation.warnings),
        )

    model_source = build_model_source_from_reference(
        components=components,
        reference_content=reference_content,
    )
    if model_source is None:
        return ModelSourceBuildResult(
            success=False,
            message="Could not build ModelSource from reference_content for the requested components.",
            source=source,
            components=components,
        )

    return ModelSourceBuildResult(
        success=True,
        message="ModelSource built from caller-supplied reference_content.",
        source=source,
        model_source=model_source,
        components=components,
        analysis={"source": source},
    )


# SECTION: Build ModelSource from embedded NASA SQLite database
def _build_model_source_from_database(
        components: List[Component],
        temperature: TemperatureInput,
) -> ModelSourceBuildResult:
    try:
        availability_results = check_component_availability(
            components=components,
        )
    except Exception as exc:
        logger.exception("Database component availability check failed.")
        return ModelSourceBuildResult(
            success=False,
            message=f"NASA database availability check failed: {exc}",
            source="database",
        )

    matched_components = availability_results.get("matched_components", [])
    missing_components = availability_results.get("missing_components", [])

    analysis = {
        "source": "database",
        "matched_components": [_component_to_dict(component) for component in matched_components],
        "missing_components": [_component_to_dict(component) for component in missing_components],
    }

    if missing_components:
        return ModelSourceBuildResult(
            success=False,
            message=(
                "Some components are missing from the embedded NASA-9 database. "
                "The MCP server does not search external scientific data; provide an externally prepared "
                "REFERENCE and call again with source='reference'."
            ),
            source="database",
            components=matched_components,
            analysis=analysis,
            warnings=[
                "Missing database component: "
                f"{component.name}/{component.formula}({component.state})"
                for component in missing_components
            ],
        )

    try:
        model_source = build_nasa_model_source_from_database(
            components=matched_components,
            temperature=temperature,
        )
    except Exception as exc:
        logger.exception("Database ModelSource build failed.")
        return ModelSourceBuildResult(
            success=False,
            message=f"Could not build ModelSource from embedded NASA-9 database: {exc}",
            source="database",
            components=matched_components,
            analysis=analysis,
        )

    return ModelSourceBuildResult(
        success=True,
        message="ModelSource built from embedded NASA-9 database.",
        source="database",
        model_source=model_source,
        components=matched_components,
        analysis=analysis,
    )


# SECTION: Serialize shared Component model
def _component_to_dict(component: Component) -> dict[str, Any]:
    if hasattr(component, "model_dump"):
        return component.model_dump()
    if hasattr(component, "dict"):
        return component.dict()
    return {
        "name": component.name,
        "formula": component.formula,
        "state": component.state,
    }


# SECTION: Build component ThermoDB objects


def _build_components_thermodb_from_reference(
        components: List[Component],
        reference_content: str,
) -> Optional[List[ComponentThermoDB]]:
    try:
        # NOTE: Collect one pyThermoDB component object per requested MCP component.
        thermodb_components: List[ComponentThermoDB] = []

        # NOTE: Build each component using the caller-supplied reference content.
        for comp in components:
            thermodb_component = build_component_thermodb_from_reference(
                component_name=comp.name,
                component_formula=comp.formula,
                component_state=comp.state,
                reference_content=reference_content,
                check_labels=False,
            )
            # ! A missing component row makes the ModelSource unusable for this request.
            if thermodb_component is None:
                logger.error(
                    f"Component {comp.name} could not be built from reference.")
                return None

            # NOTE: Preserve component order for downstream reaction construction.
            thermodb_components.append(thermodb_component)

        # NOTE: Return raw ThermoDB components; ModelSource conversion happens one layer up.
        return thermodb_components
    except Exception as e:
        logger.error(
            f"Error in _build_components_thermodb_from_reference: {e}")
        return None


# SECTION: Build ModelSource from reference content


def build_model_source_from_reference(
        components: List[Component],
        reference_content: str,
) -> Optional[ModelSource]:

    try:
        # NOTE: NASA calculations require component-level data sources only.
        if components:
            thermodb_components: List[ComponentThermoDB] | None = _build_components_thermodb_from_reference(
                components=components,
                reference_content=reference_content,
            )

            # ! Stop early if pyThermoDB could not build the requested component set.
            if thermodb_components is None:
                logger.error(
                    "Failed to build components thermodb from reference.")
                return None

            # ! Every requested component source must be available for NASA calculations.
            if len(thermodb_components) != len(components):
                logger.error(
                    "Failed to build thermodb source for every requested component.")
                return None

            # NOTE: Convert pyThermoDB component records into PyThermoLinkDB component sources.
            component_model_source: List[ComponentModelSource] = build_components_model_source(
                components_thermodb=thermodb_components,
                rules=None,
            )
        else:
            # NOTE: Empty component lists produce an empty ModelSource.
            component_model_source: List[ComponentModelSource] = []

        # NOTE: Assemble the source list consumed by build_model_source.
        source: list = []
        # ! Component model sources are the only source type supported by this NASA MCP wrapper.
        if len(component_model_source) > 0:
            source.extend(component_model_source)

        # NOTE: Build the final ModelSource passed to pythermocalcdb-nasa.
        model_source: ModelSource = build_model_source(
            source=source,
        )

        # NOTE: Return a package-native ModelSource, not a serialized copy.
        return model_source
    except Exception as e:
        logger.error(f"Error in build_model_source_from_reference: {e}")
        return None

# SECTION: Imports
import logging
from typing import Optional, List
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

# NOTE: logger
logger = logging.getLogger(__name__)

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

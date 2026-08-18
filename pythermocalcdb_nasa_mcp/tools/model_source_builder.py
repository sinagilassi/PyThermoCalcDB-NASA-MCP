# import packages/modules
import logging
from typing import Optional, List
from pyThermoLinkDB import (
    build_components_model_source,
    build_mixture_model_source,
    build_model_source
)
from pyThermoLinkDB.models import (
    ComponentModelSource,
    MixtureModelSource,
    ModelSource
)
from pythermodb_settings.models import Component
from pyThermoDB import (
    ComponentThermoDB,
    MixtureThermoDB,
    build_component_thermodb_from_reference,
    build_mixture_thermodb_from_reference
)

# NOTE: logger
logger = logging.getLogger(__name__)

# SECTION: BUILD COMPONENTS THERMODB


def _build_components_thermodb_from_reference(
        components: List[Component],
        reference_content: str,
        ignore_state_props: Optional[List[str]] = None
) -> Optional[List[ComponentThermoDB]]:
    try:
        # init list
        thermodb_components: List[ComponentThermoDB] = []

        # iterate over components and build thermodb component from reference
        for comp in components:
            thermodb_component = build_component_thermodb_from_reference(
                component_name=comp.name,
                component_formula=comp.formula,
                component_state=comp.state,
                reference_content=reference_content,
                ignore_state_props=ignore_state_props,
            )
            # >> check if component was built successfully
            if thermodb_component is None:
                logger.error(
                    f"Component {comp.name} could not be built from reference.")
                return None

            # add to list
            thermodb_components.append(thermodb_component)

        # res
        return thermodb_components
    except Exception as e:
        logger.error(
            f"Error in _build_components_thermodb_from_reference: {e}")
        return None


# SECTION: BUILD MIXTURE THERMODB
def _build_mixture_thermodb_from_reference(
        mixture: List[Component],
        reference_content: str,
) -> Optional[MixtureThermoDB]:
    try:
        # NOTE: build mixture thermodb
        mixture_thermodb: MixtureThermoDB | None = build_mixture_thermodb_from_reference(
            components=mixture,
            reference_content=reference_content,
        )
        return mixture_thermodb
    except Exception as e:
        logger.error(f"Error in _build_mixture_thermodb_from_reference: {e}")
        return None


# SECTION: BUILD MODEL SOURCE


def build_model_source_from_reference(
        components: List[Component],
        reference_content: str,
        mixture: Optional[List[Component]] = None,
        ignore_state_props: Optional[List[str]] = None,
) -> Optional[ModelSource]:

    try:
        # NOTE: EOS callers only need component model sources, so mixture is optional.
        if mixture is None:
            # ! Normalize missing mixture input before checking the activity-capable path.
            mixture = []

        # NOTE: build components thermodb
        if components:
            thermodb_components: List[ComponentThermoDB] | None = _build_components_thermodb_from_reference(
                components=components,
                reference_content=reference_content,
                ignore_state_props=ignore_state_props,
            )

            # >> check
            if thermodb_components is None:
                logger.error(
                    "Failed to build components thermodb from reference.")
                return None

            # ! Every requested component source must be available for activity models.
            if len(thermodb_components) != len(components):
                logger.error(
                    "Failed to build thermodb source for every requested component.")
                return None

            # ! build component model source
            # ! with partially matched rules
            component_model_source: List[ComponentModelSource] = build_components_model_source(
                components_thermodb=thermodb_components,
                rules=None,
            )
        else:
            # >> if no components, return empty list
            component_model_source: List[ComponentModelSource] = []

        # NOTE: build mixture thermodb
        mixture_model_source: Optional[MixtureModelSource] = None

        if mixture:
            mixture_thermodb: MixtureThermoDB | None = _build_mixture_thermodb_from_reference(
                mixture=mixture,
                reference_content=reference_content,
            )

            # >> check
            if mixture_thermodb is None:
                logger.error(
                    "Failed to build mixture thermodb from reference.")
                return None

            # ! build mixture model source
            # ! with partially matched rules
            mixture_model_source = build_mixture_model_source(
                mixture_thermodb=mixture_thermodb,
            )

        # NOTE: model source
        source: list = []
        # >>> component model source
        if len(component_model_source) > 0:
            source.extend(component_model_source)
        # >>> mixture model source
        if mixture_model_source is not None:
            source.append(mixture_model_source)

        model_source: ModelSource = build_model_source(
            source=source,
        )

        # return
        return model_source
    except Exception as e:
        logger.error(f"Error in build_model_source_from_reference: {e}")
        return None

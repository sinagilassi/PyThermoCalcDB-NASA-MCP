from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from pyreactlab_core.models.reaction import Reaction
from pythermodb_settings.models import Component, Temperature

from pythermocalcdb_nasa import (
    Cp_T,
    G_T,
    H_T,
    Keq,
    S_T,
    dG_rxn_STD,
    dH_rxn_STD,
    dS_rxn_STD,
)
from pythermocalcdb_nasa_mcp.interface.validation import (
    validate_model_source_symbols,
    validate_reaction_components,
    validate_reference_content,
    validate_temperature_ranges,
)
from pythermocalcdb_nasa_mcp.models.nasa import (
    ComponentInput,
    MCPResponse,
    ReactionPropertyRequest,
    SpeciesPropertyRequest,
)
from pythermocalcdb_nasa_mcp.tools.model_source_builder import (
    build_model_source_from_reference,
)


logger = logging.getLogger(__name__)


# SECTION: Calculate enthalpy at temperature T
def calc_H_T(request: SpeciesPropertyRequest) -> dict[str, Any]:
    """Calculate component enthalpy at temperature T from NASA reference content."""
    return _run_species_property("H_T", H_T, request)


# SECTION: Calculate entropy at temperature T
def calc_S_T(request: SpeciesPropertyRequest) -> dict[str, Any]:
    """Calculate component entropy at temperature T from NASA reference content."""
    return _run_species_property("S_T", S_T, request)


# SECTION: Calculate Gibbs free energy at temperature T
def calc_G_T(request: SpeciesPropertyRequest) -> dict[str, Any]:
    """Calculate component Gibbs free energy at temperature T from NASA reference content."""
    return _run_species_property("G_T", G_T, request)


# SECTION: Calculate heat capacity at temperature T
def calc_Cp_T(request: SpeciesPropertyRequest) -> dict[str, Any]:
    """Calculate component heat capacity at temperature T from NASA reference content."""
    return _run_species_property("Cp_T", Cp_T, request)


# SECTION: Calculate standard enthalpy change of reaction
def calc_dH_rxn_STD(request: ReactionPropertyRequest) -> dict[str, Any]:
    """Calculate standard enthalpy change of reaction at temperature T."""
    return _run_reaction_property("dH_rxn_STD", dH_rxn_STD, request)


# SECTION: Calculate standard entropy change of reaction
def calc_dS_rxn_STD(request: ReactionPropertyRequest) -> dict[str, Any]:
    """Calculate standard entropy change of reaction at temperature T."""
    return _run_reaction_property("dS_rxn_STD", dS_rxn_STD, request)


# SECTION: Calculate standard Gibbs free energy change of reaction
def calc_dG_rxn_STD(request: ReactionPropertyRequest) -> dict[str, Any]:
    """Calculate standard Gibbs free energy change of reaction at temperature T."""
    return _run_reaction_property("dG_rxn_STD", dG_rxn_STD, request)


# SECTION: Calculate equilibrium constant
def calc_Keq(request: ReactionPropertyRequest) -> dict[str, Any]:
    """Calculate reaction equilibrium constant at temperature T."""
    return _run_reaction_property("Keq", Keq, request)


# SECTION: Run species property pipeline
def _run_species_property(
    operation: str,
    calculator: Callable[..., Any],
    request: SpeciesPropertyRequest,
) -> dict[str, Any]:
    # NOTE: Level 1 reference validation before creating pyThermoDB objects.
    reference_validation = validate_reference_content(request.reference_content)
    if not reference_validation.success:
        return _failure(reference_validation.message)

    # NOTE: Convert MCP inputs into deterministic domain objects.
    component = _to_domain_component(request.component)
    model_source = build_model_source_from_reference(
        components=[component],
        reference_content=request.reference_content,
    )
    if model_source is None:
        return _failure("Could not build ModelSource from reference_content for the requested component.")

    # NOTE: Validate required NASA symbols after ModelSource construction.
    symbol_validation = validate_model_source_symbols(
        model_source,
        [request.component],
        nasa_type=request.nasa_type,
        basis=request.basis,
    )
    if not symbol_validation.success:
        return _failure(symbol_validation.message, list(symbol_validation.warnings))

    # NOTE: v1 strictly rejects calculations outside Tmin/Tmax.
    range_validation = validate_temperature_ranges(
        model_source,
        [request.component],
        request.temperature.value,
    )
    if not range_validation.success:
        return _failure(range_validation.message, list(range_validation.warnings))

    # ! Numerical work is delegated to pythermocalcdb-nasa.
    try:
        result = calculator(
            component=component,
            temperature=_to_domain_temperature(request.temperature.value),
            model_source=model_source,
            component_key=request.component_key,
            nasa_type=request.nasa_type,
            basis=request.basis,
            **_optional_mode(request.mode),
        )
    except Exception as exc:
        logger.exception("%s failed.", operation)
        return _failure(f"{operation} failed: {exc}", list(range_validation.warnings))

    # NOTE: Convert package output to a JSON-safe response.
    return _result_response(
        operation,
        result,
        warnings=list(range_validation.warnings),
        analysis={
            "component": request.component.model_dump(),
            "temperature": request.temperature.model_dump(),
            "basis": request.basis,
            "nasa_type": request.nasa_type,
            "component_key": request.component_key,
        },
    )


# SECTION: Run reaction property pipeline
def _run_reaction_property(
    operation: str,
    calculator: Callable[..., Any],
    request: ReactionPropertyRequest,
) -> dict[str, Any]:
    # NOTE: Level 1 reference validation before creating pyThermoDB objects.
    reference_validation = validate_reference_content(request.reference_content)
    if not reference_validation.success:
        return _failure(reference_validation.message)

    # NOTE: Ensure Reaction.components covers every species token in the equation.
    component_validation = validate_reaction_components(request.reaction, request.components)
    if not component_validation.success:
        return _failure(component_validation.message)

    # NOTE: Convert MCP component inputs and build one shared ModelSource.
    components = [_to_domain_component(component) for component in request.components]
    model_source = build_model_source_from_reference(
        components=components,
        reference_content=request.reference_content,
    )
    if model_source is None:
        return _failure("Could not build ModelSource from reference_content for the requested reaction components.")

    # NOTE: Every reaction species needs the NASA coefficient pack.
    symbol_validation = validate_model_source_symbols(
        model_source,
        request.components,
        nasa_type=request.nasa_type,
    )
    if not symbol_validation.success:
        return _failure(symbol_validation.message, list(symbol_validation.warnings))

    # NOTE: Strictly enforce the available polynomial temperature range for every species.
    range_validation = validate_temperature_ranges(
        model_source,
        request.components,
        request.temperature.value,
    )
    if not range_validation.success:
        return _failure(range_validation.message, list(range_validation.warnings))

    # NOTE: Construct the pyreactlab Reaction object after MCP-level validation passes.
    reaction = Reaction(
        name=request.name,
        reaction=request.reaction,
        components=components,
    )
    # ! Numerical work is delegated to pythermocalcdb-nasa.
    try:
        result = calculator(
            reaction=reaction,
            temperature=_to_domain_temperature(request.temperature.value),
            model_source=model_source,
            component_key=request.component_key,
            nasa_type=request.nasa_type,
            **_optional_mode(request.mode),
        )
    except Exception as exc:
        logger.exception("%s failed.", operation)
        return _failure(f"{operation} failed: {exc}", list(range_validation.warnings))

    # NOTE: Convert package output to a JSON-safe response.
    return _result_response(
        operation,
        result,
        warnings=list(range_validation.warnings),
        analysis={
            "reaction": {"name": request.name, "equation": request.reaction},
            "components": [component.model_dump() for component in request.components],
            "temperature": request.temperature.model_dump(),
            "nasa_type": request.nasa_type,
            "component_key": request.component_key,
        },
    )


# SECTION: Build domain component
def _to_domain_component(component: ComponentInput) -> Component:
    return Component(name=component.name, formula=component.formula, state=component.state)


# SECTION: Build domain temperature
def _to_domain_temperature(value: float) -> Temperature:
    return Temperature(value=value, unit="K")


# SECTION: Build optional calculation kwargs
def _optional_mode(mode: str | None) -> dict[str, str]:
    return {"mode": mode} if mode is not None else {}


# SECTION: Build success response
def _result_response(
    operation: str,
    result: Any,
    *,
    warnings: list[str],
    analysis: dict[str, Any],
) -> dict[str, Any]:
    # ! A None result means the underlying package rejected or could not complete the calculation.
    if result is None:
        return _failure(
            f"{operation} returned no result. Check component identities, reaction species, NASA type, and reference content.",
            warnings,
            analysis,
        )

    # NOTE: Pydantic outputs are normalized to primitive dict/list/scalar values.
    if hasattr(result, "model_dump"):
        result_data = result.model_dump()
    elif hasattr(result, "dict"):
        result_data = result.dict()
    else:
        result_data = {"value": result, "unit": None}

    return MCPResponse(
        success=True,
        message=f"{operation} completed successfully.",
        results={
            "operation": operation,
            "value": result_data.get("value"),
            "unit": result_data.get("unit"),
        },
        analysis=analysis,
        warnings=warnings,
    ).model_dump()


# SECTION: Build failure response
def _failure(
    message: str,
    warnings: list[str] | None = None,
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return MCPResponse(
        success=False,
        message=message,
        results=None,
        analysis=analysis or {},
        warnings=warnings or [],
    ).model_dump()

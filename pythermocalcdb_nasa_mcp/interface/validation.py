from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import yaml
from pyThermoDB.references import check_custom_reference
from pyThermoLinkDB.models import ModelSource

from pythermocalcdb_nasa_mcp.models.nasa import ComponentInput


# SECTION: NASA validation constants
# NOTE: These symbols are the minimum coefficient sets expected by the NASA helper functions.
NASA9_REQUIRED_SYMBOLS = ("a1", "a2", "a3", "a4", "a5", "a6", "a7", "b1", "b2")
NASA7_REQUIRED_SYMBOLS = ("a1", "a2", "a3", "a4", "a5", "a6", "a7")
REACTION_SPECIES_PATTERN = re.compile(r"([A-Za-z][A-Za-z0-9]*)\((g|l|s|aq)\)")


# SECTION: Validation response
@dataclass(frozen=True)
class ValidationResult:
    success: bool
    message: str = ""
    warnings: tuple[str, ...] = ()


# SECTION: Validate reference content
def validate_reference_content(reference_content: str) -> ValidationResult:
    # NOTE: Parse YAML first so syntax failures produce local, actionable messages.
    try:
        parsed = yaml.safe_load(reference_content)
    except yaml.YAMLError as exc:
        return ValidationResult(False, f"reference_content is not valid YAML: {exc}")

    if not isinstance(parsed, dict) or "REFERENCES" not in parsed:
        return ValidationResult(False, "reference_content must contain a top-level REFERENCES mapping.")

    # NOTE: Let pyThermoDB remain the authority for its own reference schema.
    try:
        if not check_custom_reference({"reference": [reference_content]}):
            return ValidationResult(False, "reference_content failed pyThermoDB custom reference validation.")
    except Exception as exc:
        return ValidationResult(False, f"reference_content failed pyThermoDB validation: {exc}")

    return ValidationResult(True)


# SECTION: Validate NASA coefficient symbols
def validate_model_source_symbols(
    model_source: ModelSource,
    components: Iterable[ComponentInput],
    *,
    nasa_type: str,
    basis: str = "molar",
) -> ValidationResult:
    required: list[str] = list(NASA9_REQUIRED_SYMBOLS if nasa_type == "nasa9" else NASA7_REQUIRED_SYMBOLS)
    if basis == "mass":
        required.append("MW")

    missing: list[str] = []
    for component in components:
        # NOTE: ModelSource stores aliases for a component; check all supported key styles.
        source_data = _find_component_data(model_source, component)
        if source_data is None:
            missing.append(f"{component.name}/{component.formula}({component.state}): no model_source entry")
            continue
        for symbol in required:
            if symbol not in source_data:
                missing.append(f"{component.name}/{component.formula}({component.state}): missing {symbol}")

    if missing:
        return ValidationResult(False, "Reference data is missing required NASA symbols.", tuple(missing))
    return ValidationResult(True)


# SECTION: Validate temperature ranges
def validate_temperature_ranges(
    model_source: ModelSource,
    components: Iterable[ComponentInput],
    temperature_value: float,
) -> ValidationResult:
    failures: list[str] = []
    warnings: list[str] = []
    for component in components:
        # NOTE: Strict range enforcement prevents NASA polynomial extrapolation.
        source_data = _find_component_data(model_source, component)
        if source_data is None:
            failures.append(f"{component.name}/{component.formula}({component.state}): no model_source entry")
            continue
        try:
            t_min = float(source_data["Tmin"]["value"])
            t_max = float(source_data["Tmax"]["value"])
        except KeyError as exc:
            failures.append(f"{component.name}/{component.formula}({component.state}): missing {exc.args[0]}")
            continue
        except (TypeError, ValueError):
            failures.append(f"{component.name}/{component.formula}({component.state}): Tmin/Tmax must be numeric")
            continue

        if temperature_value < t_min or temperature_value > t_max:
            failures.append(
                f"{component.name}/{component.formula}({component.state}) supports {t_min:g}-{t_max:g} K, "
                f"but {temperature_value:g} K was requested."
            )
        elif temperature_value == t_min or temperature_value == t_max:
            warnings.append(
                f"{component.name}/{component.formula}({component.state}) is being evaluated at a reference range boundary."
            )

    if failures:
        return ValidationResult(False, "Requested temperature is outside the available reference range.", tuple(failures))
    return ValidationResult(True, warnings=tuple(warnings))


# SECTION: Validate reaction component coverage
def validate_reaction_components(reaction: str, components: Iterable[ComponentInput]) -> ValidationResult:
    # NOTE: Reaction equations must include state-qualified species such as CO(g).
    required_tokens = set(REACTION_SPECIES_PATTERN.findall(reaction))
    if not required_tokens:
        return ValidationResult(
            False,
            "reaction must include species tokens with states, for example CO(g) + H2O(g) => CO2(g) + H2(g).",
        )

    provided_tokens = {(component.formula, component.state) for component in components}
    missing = sorted(required_tokens - provided_tokens)
    if missing:
        formatted = ", ".join(f"{formula}({state})" for formula, state in missing)
        return ValidationResult(False, f"components is missing reaction species: {formatted}.")

    return ValidationResult(True)


# SECTION: Find component data in ModelSource
def _find_component_data(model_source: ModelSource, component: ComponentInput) -> dict | None:
    data_source = getattr(model_source, "data_source", {})
    # NOTE: pyThermoLinkDB creates multiple aliases; use all keys supported by the tool input.
    keys = (
        f"{component.name}-{component.state}",
        f"{component.formula}-{component.state}",
        f"{component.name}-{component.formula}",
        component.name,
        component.formula,
        f"{component.name}-{component.formula}-{component.state}",
        f"{component.formula}-{component.name}-{component.state}",
    )
    for key in keys:
        data = data_source.get(key)
        if isinstance(data, dict):
            return data
    return None

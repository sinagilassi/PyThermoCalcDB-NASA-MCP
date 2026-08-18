from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pythermodb_settings.models import Component, ComponentKey, Temperature


# SECTION: Shared type aliases
# NOTE: These aliases mirror the accepted public options in pythermocalcdb-nasa.
NASAType = Literal["nasa7", "nasa9"]
Basis = Literal["molar", "mass"]


# SECTION: Domain-backed input models
# NOTE: Keep MCP aliases while using the shared pythermodb_settings models directly.
ComponentInput = Component
TemperatureInput = Temperature


# SECTION: Standard MCP response model
class MCPResponse(BaseModel):
    """Predictable JSON-safe MCP response contract."""

    success: bool
    message: str
    results: dict[str, Any] | None = None
    analysis: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


# SECTION: Species property request model
class SpeciesPropertyRequest(BaseModel):
    """Request for a single-component NASA property calculation."""

    model_config = ConfigDict(extra="forbid")

    component: ComponentInput
    temperature: TemperatureInput
    reference_content: str = Field(description="pyThermoDB YAML reference content.")
    component_key: ComponentKey = Field(default="Name-Formula")
    nasa_type: NASAType = Field(default="nasa9")
    basis: Basis = Field(default="molar")
    mode: str | None = Field(default=None, description="Optional mode forwarded to the underlying package.")

    @field_validator("reference_content")
    @classmethod
    def reference_content_must_not_be_blank(cls, value: str) -> str:
        # NOTE: Empty references cannot be passed to pyThermoDB safely.
        if not value.strip():
            raise ValueError("reference_content must not be blank.")
        return value

    @field_validator("temperature")
    @classmethod
    def temperature_unit_must_be_kelvin(cls, value: TemperatureInput) -> TemperatureInput:
        # NOTE: v1 accepts only Kelvin even though pythermodb_settings.Temperature supports more units.
        if value.unit != "K":
            raise ValueError("temperature.unit must be 'K'.")
        return value


# SECTION: Reaction property request model
class ReactionPropertyRequest(BaseModel):
    """Request for a reaction NASA property calculation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Human-readable reaction name.")
    reaction: str = Field(description='Reaction equation, for example "CO(g) + H2O(g) => CO2(g) + H2(g)".')
    components: list[ComponentInput] = Field(min_length=1)
    temperature: TemperatureInput
    reference_content: str = Field(description="pyThermoDB YAML reference content.")
    component_key: ComponentKey = Field(default="Name-Formula")
    nasa_type: NASAType = Field(default="nasa9")
    mode: str | None = Field(default=None, description="Optional mode forwarded to the underlying package.")

    @field_validator("reference_content")
    @classmethod
    def reference_content_must_not_be_blank(cls, value: str) -> str:
        # NOTE: Empty references cannot be passed to pyThermoDB safely.
        if not value.strip():
            raise ValueError("reference_content must not be blank.")
        return value

    @field_validator("temperature")
    @classmethod
    def temperature_unit_must_be_kelvin(cls, value: TemperatureInput) -> TemperatureInput:
        # NOTE: v1 accepts only Kelvin even though pythermodb_settings.Temperature supports more units.
        if value.unit != "K":
            raise ValueError("temperature.unit must be 'K'.")
        return value

# PyThermoCalcDB-NASA-MCP

## Overview

PyThermoCalcDB-NASA-MCP exposes selected `pythermocalcdb-nasa` calculations as MCP tools. It is an interface and orchestration layer: it validates structured MCP inputs, builds a `ModelSource` from supplied pyThermoDB YAML reference content, calls the deterministic scientific package, and returns JSON-safe results.

## Relationship to PyThermoCalcDB-NASA

`pythermocalcdb-nasa` owns the NASA thermodynamic calculations. This package owns MCP transport, request validation, model-source construction, tool registration, resources, and response formatting.

## Architecture

The server follows:

```text
MCP request -> Pydantic model -> validation -> ModelSource builder -> pythermocalcdb-nasa -> JSON-safe response
```

`server.py` registers MCP capabilities only. Calculation orchestration lives in `interface/`, input contracts live in `models/`, reusable reference/model-source utilities live in `tools/`, and agent guidance lives in `resources/`.

## Available MCP Tools

- `calc_H_T`: component enthalpy at temperature T
- `calc_S_T`: component entropy at temperature T
- `calc_G_T`: component Gibbs free energy at temperature T
- `calc_Cp_T`: component heat capacity at temperature T
- `calc_dH_rxn_STD`: standard enthalpy change of reaction
- `calc_dS_rxn_STD`: standard entropy change of reaction
- `calc_dG_rxn_STD`: standard Gibbs free energy change of reaction
- `calc_Keq`: reaction equilibrium constant
- `check_yaml_reference`: validate pyThermoDB YAML reference content

## Available MCP Resources

- `pythermocalcdb-nasa://references/nasa-requirements`
- `pythermocalcdb-nasa://workflows/species-properties`
- `pythermocalcdb-nasa://workflows/reaction-properties`
- `pythermocalcdb-nasa://guidance/agent-checklist`

## Installation

```bash
uv sync
```

## Running with stdio

```bash
uv run pythermocalcdb-nasa-mcp
```

## Running with HTTP

```bash
uv run pythermocalcdb-nasa-mcp --mode http --host 127.0.0.1 --port 8000 --path /mcp
```

## MCP Client Configuration

```json
{
  "mcpServers": {
    "pythermocalcdb-nasa": {
      "command": "uv",
      "args": ["run", "pythermocalcdb-nasa-mcp"]
    }
  }
}
```

## Tool Input Examples

Species property requests use this shape:

```json
{
  "request": {
    "component": {"name": "carbon dioxide", "formula": "CO2", "state": "g"},
    "temperature": {"value": 300.0, "unit": "K"},
    "reference_content": "REFERENCES: ...",
    "component_key": "Name-Formula",
    "nasa_type": "nasa9",
    "basis": "molar"
  }
}
```

Reaction property requests use this shape:

```json
{
  "request": {
    "name": "Water-Gas Shift Reaction",
    "reaction": "CO(g) + H2O(g) => CO2(g) + H2(g)",
    "components": [
      {"name": "carbon monoxide", "formula": "CO", "state": "g"},
      {"name": "dihydrogen monoxide", "formula": "H2O", "state": "g"},
      {"name": "carbon dioxide", "formula": "CO2", "state": "g"},
      {"name": "dihydrogen", "formula": "H2", "state": "g"}
    ],
    "temperature": {"value": 300.0, "unit": "K"},
    "reference_content": "REFERENCES: ...",
    "component_key": "Name-Formula",
    "nasa_type": "nasa9"
  }
}
```

Responses are predictable:

```json
{
  "success": true,
  "message": "H_T completed successfully.",
  "results": {"operation": "H_T", "value": 0.0, "unit": "J/mol"},
  "analysis": {},
  "warnings": []
}
```

## Scientific Workflow

1. Read the NASA reference requirements resource.
2. Provide a pyThermoDB YAML reference string with matching component rows.
3. Keep temperature inputs in K and inside each component row's `Tmin`/`Tmax`.
4. Call the property-specific tool.
5. Check `success`, `message`, and `warnings` before reporting results.

## Examples

- Use the request shapes above with caller-supplied `reference_content`.
- Bundled test fixtures or example data files are not authoritative data sources for MCP operation.

## Underlying Package

This package depends on `pythermocalcdb-nasa` and does not reimplement NASA thermodynamic equations.

## License

Apache-2.0

# PyThermoCalcDB-NASA-MCP

[![PyPI Downloads](https://static.pepy.tech/badge/pythermocalcdb-nasa-mcp/month)](https://pepy.tech/projects/pythermocalcdb-nasa-mcp)
![PyPI](https://img.shields.io/pypi/v/pythermocalcdb-nasa-mcp)
![Python Version](https://img.shields.io/pypi/pyversions/pythermocalcdb-nasa-mcp.svg)
![License](https://img.shields.io/pypi/l/pythermocalcdb-nasa-mcp)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-Compatible-orange)](https://modelcontextprotocol.io)

PyThermoCalcDB-NASA-MCP is a Model Context Protocol (MCP) server for running
selected `pythermocalcdb-nasa` thermodynamic calculations from agents and
MCP-compatible clients.

## Overview 🌐

The package exposes NASA polynomial species-property, reaction-property, and
YAML reference-validation workflows as MCP tools. Each calculation receives
structured arguments, builds a `ModelSource` from caller-supplied `pyThermoDB`
YAML reference content, calls the corresponding `pythermocalcdb-nasa` function,
and returns JSON-safe data.

Use this package when an agent or MCP client needs to:

- Calculate component enthalpy, entropy, Gibbs free energy, or heat capacity.
- Calculate standard reaction enthalpy, entropy, or Gibbs free energy changes.
- Calculate a reaction equilibrium constant from NASA thermodynamic data.
- Validate whether YAML reference content is usable by the pyThermoDB reference pipeline.

The server does not search for, load, or assemble reference files automatically.
Callers must pass complete YAML reference content in each tool request.

## Requirements 📋

- Python `>=3.11`
- `pip` or `uv`

## Installation 📦

```bash
pip install pythermocalcdb-nasa-mcp
```

This installs the `pythermocalcdb-nasa-mcp` command.

For local development from this repository:

```bash
uv sync
```

## Running the MCP Server ▶️

The server entrypoints are:

- CLI: `pythermocalcdb-nasa-mcp`
- Module: `python -m pythermocalcdb_nasa_mcp.server`

Both support the same options.

### STDIO Transport 🧵

Use STDIO for local MCP desktop and agent clients:

```bash
pythermocalcdb-nasa-mcp --mode stdio
```

Equivalent module command:

```bash
python -m pythermocalcdb_nasa_mcp.server --mode stdio
```

When running from a local checkout with `uv`:

```bash
uv run pythermocalcdb-nasa-mcp --mode stdio
```

### HTTP Transport 🌍

Use HTTP when a network-accessible MCP endpoint is needed:

```bash
pythermocalcdb-nasa-mcp --mode http --host 127.0.0.1 --port 8000 --path /mcp
```

Equivalent module command:

```bash
python -m pythermocalcdb_nasa_mcp.server --mode http --host 127.0.0.1 --port 8000 --path /mcp
```

When running from a local checkout with `uv`:

```bash
uv run pythermocalcdb-nasa-mcp --mode http --host 127.0.0.1 --port 8000 --path /mcp
```

## CLI Options ⌨️

- `--mode`: MCP transport mode, either `stdio` or `http` (default: `stdio`)
- `--host`: HTTP bind host (default: `127.0.0.1`)
- `--port`: HTTP bind port (default: `8000`)
- `--path`: HTTP endpoint path (default: `/mcp`)
- `-V`, `--version`: print package version

## MCP Client Configuration 🔌

### STDIO

```json
{
  "mcpServers": {
    "pythermocalcdb-nasa": {
      "command": "pythermocalcdb-nasa-mcp",
      "args": ["--mode", "stdio"]
    }
  }
}
```

For a source checkout managed by `uv`:

```json
{
  "mcpServers": {
    "pythermocalcdb-nasa": {
      "command": "uv",
      "args": ["run", "pythermocalcdb-nasa-mcp", "--mode", "stdio"]
    }
  }
}
```

### HTTP

```json
{
  "mcpServers": {
    "pythermocalcdb-nasa": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## MCP Resources 📚

The server exposes four guidance resources:

- `pythermocalcdb-nasa://references/nasa-requirements`
  - YAML guidance for required pyThermoDB reference structure, component rows,
    NASA coefficients, supported component keys, and temperature range rules.
- `pythermocalcdb-nasa://workflows/species-properties`
  - Agent workflow for `H_T`, `S_T`, `G_T`, and `Cp_T` species-property calculations.
- `pythermocalcdb-nasa://workflows/reaction-properties`
  - Agent workflow for `dH_rxn_STD`, `dS_rxn_STD`, `dG_rxn_STD`, and `Keq` reaction calculations.
- `pythermocalcdb-nasa://guidance/agent-checklist`
  - Resource-first checklist for reliable NASA calculation tool calls.

## MCP Tools 🧰

### Species Property Tools 🔥

Species tools require `component`, `temperature`, and `reference_content`.
Temperature must use Kelvin (`K`). Supported NASA polynomial types are `nasa7`
and `nasa9`.

- `calc_H_T`
  - Calculates component enthalpy at temperature `T`.
- `calc_S_T`
  - Calculates component entropy at temperature `T`.
- `calc_G_T`
  - Calculates component Gibbs free energy at temperature `T`.
- `calc_Cp_T`
  - Calculates component heat capacity at temperature `T`.

### Reaction Property Tools ⚗️

Reaction tools require `name`, `reaction`, `components`, `temperature`, and
`reference_content`. Temperature must use Kelvin (`K`), and every species in
the reaction equation must be represented in `components`.

- `calc_dH_rxn_STD`
  - Calculates standard enthalpy change of reaction.
- `calc_dS_rxn_STD`
  - Calculates standard entropy change of reaction.
- `calc_dG_rxn_STD`
  - Calculates standard Gibbs free energy change of reaction.
- `calc_Keq`
  - Calculates the reaction equilibrium constant.

### Utility Tool 🛠️

- `check_yaml_reference`
  - Validates YAML reference content with the pyThermoDB custom-reference checker and returns `true` or `false`.

## Input Model Notes 📝

Calculation tools receive one Pydantic argument named `request`. Typical species
tool input therefore looks like:

```json
{
  "request": {
    "component": {
      "name": "carbon dioxide",
      "formula": "CO2",
      "state": "g"
    },
    "temperature": {
      "value": 300.0,
      "unit": "K"
    },
    "reference_content": "REFERENCES:\n  ...",
    "component_key": "Name-Formula",
    "nasa_type": "nasa9",
    "basis": "molar"
  }
}
```

Typical reaction tool input looks like:

```json
{
  "request": {
    "name": "Water-Gas Shift Reaction",
    "reaction": "CO(g) + H2O(g) => CO2(g) + H2(g)",
    "components": [
      {
        "name": "carbon monoxide",
        "formula": "CO",
        "state": "g"
      },
      {
        "name": "dihydrogen monoxide",
        "formula": "H2O",
        "state": "g"
      },
      {
        "name": "carbon dioxide",
        "formula": "CO2",
        "state": "g"
      },
      {
        "name": "dihydrogen",
        "formula": "H2",
        "state": "g"
      }
    ],
    "temperature": {
      "value": 300.0,
      "unit": "K"
    },
    "reference_content": "REFERENCES:\n  ...",
    "component_key": "Name-Formula",
    "nasa_type": "nasa9"
  }
}
```

Tool responses follow a predictable JSON-safe contract:

```json
{
  "success": true,
  "message": "H_T completed successfully.",
  "results": {
    "operation": "H_T",
    "value": 0.0,
    "unit": "J/mol"
  },
  "analysis": {},
  "warnings": []
}
```

Use the resource documents for full reference-content requirements before
calling tools.

## Best Practices ✅

- Pass complete, non-empty `reference_content` in every calculation request.
- Use `check_yaml_reference` before calculations when reference content is generated dynamically.
- Keep `component_key` choices consistent across related calls.
- Keep temperature inputs in Kelvin and within each component row's `Tmin` and `Tmax`.
- Make sure every reaction species appears in both the reaction equation and `components`.
- Use `nasa_type` consistently with the coefficient format in the supplied reference content.
- Check `success`, `message`, and `warnings` before reporting calculated results.

## Development Quick Check 🧪

```bash
python -m py_compile pythermocalcdb_nasa_mcp/server.py
python -m py_compile pythermocalcdb_nasa_mcp/interface/core.py
python -m py_compile pythermocalcdb_nasa_mcp/models/nasa.py
python -m unittest discover tests
```

## Examples 🚀

Example scripts and payload shapes are available under:

- `examples/request_payloads.py`
- `examples/references`

They show how to structure tool payloads and pass caller-supplied
`reference_content`. Bundled fixtures or example data are not authoritative
data sources for MCP operation.

## Troubleshooting 🩺

- `pythermocalcdb-nasa-mcp: command not found`
  - Install the package in the active environment: `pip install -e .`
  - Confirm the active Python environment is the one used by your MCP client.
- Port already in use in HTTP mode
  - Choose another port, for example `--port 8010`.
- Empty or invalid reference errors
  - Confirm that `reference_content` is complete YAML content and includes all component rows and NASA coefficients required by the selected calculation.
- Component not found errors
  - Confirm `component.name`, `component.formula`, `component.state`, and `component_key` match the supplied reference content.
- Temperature range errors
  - Confirm the requested Kelvin temperature is inside the matching reference row's `Tmin` and `Tmax` range.

## FAQ ❓

For questions, contact [Sina Gilassi on LinkedIn](https://www.linkedin.com/in/sina-gilassi/).

## License 📄

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).

## Author 👨‍💻

- [@sinagilassi](https://www.github.com/sinagilassi)

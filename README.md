# 🧪 PyThermoCalcDB-NASA-MCP

[![PyPI Downloads](https://static.pepy.tech/badge/pythermocalcdb-nasa-mcp/month)](https://pepy.tech/projects/pythermocalcdb-nasa-mcp)
![PyPI](https://img.shields.io/pypi/v/pythermocalcdb-nasa-mcp)
![Python Version](https://img.shields.io/pypi/pyversions/pythermocalcdb-nasa-mcp.svg)
![License](https://img.shields.io/pypi/l/pythermocalcdb-nasa-mcp)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-Compatible-orange)](https://modelcontextprotocol.io)

PyThermoCalcDB-NASA-MCP is a Model Context Protocol server for running selected
`pythermocalcdb-nasa` thermodynamic calculations from agents and MCP-compatible
clients.

## 🌐 Overview

The MCP package is an interface and orchestration layer. It validates structured
requests, builds a `ModelSource`, calls deterministic `pythermocalcdb-nasa`
functions, and returns JSON-safe results. It does not implement the scientific
calculation itself.

The default source workflow uses the embedded NASA-9 SQLite database included by
`pythermocalcdb-nasa`. If a component is unavailable locally, the MCP server
returns a structured failure. External data search is not this MCP server's
responsibility; another agent or caller should prepare complete pyThermoDB
`REFERENCE` content and call the tool with `source: "reference"`.

Use this package to:

- Calculate `H_T`, `S_T`, `G_T`, and `Cp_T` for one component.
- Calculate `dH_rxn_STD`, `dS_rxn_STD`, `dG_rxn_STD`, `Keq`, and `Keq_vh_shortcut` for reactions.
- Validate externally prepared pyThermoDB YAML reference content.

## 📦 Installation

```bash
pip install pythermocalcdb-nasa-mcp
```

For local development:

```bash
uv sync
```

## ▶️ Running

STDIO is the default transport:

```bash
pythermocalcdb-nasa-mcp --mode stdio
```

HTTP transport is also supported:

```bash
pythermocalcdb-nasa-mcp --mode http --host 127.0.0.1 --port 8000 --path /mcp
```

From a local checkout:

```bash
uv run pythermocalcdb-nasa-mcp --mode stdio
```

## 🔌 MCP Client Configuration

🧵 STDIO:

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

🌍 HTTP:

```json
{
  "mcpServers": {
    "pythermocalcdb-nasa": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## 🕵️ MCP Inspector

You can test the server with the official MCP Inspector.

For direct STDIO testing from a local checkout:

```bash
npx @modelcontextprotocol/inspector uv run pythermocalcdb-nasa-mcp --mode stdio
```

For HTTP testing, start the server first:

```bash
uv run pythermocalcdb-nasa-mcp --mode http --host 127.0.0.1 --port 8000 --path /mcp
```

Then connect Inspector to:

```text
http://127.0.0.1:8000/mcp
```

## 📚 MCP Resources

- `pythermocalcdb-nasa://references/nasa-requirements`
  - Source policy, NASA symbols, units, temperature ranges, and agent boundaries.
- `pythermocalcdb-nasa://workflows/species-properties`
  - Workflow for `H_T`, `S_T`, `G_T`, and `Cp_T`.
- `pythermocalcdb-nasa://workflows/reaction-properties`
  - Workflow for `dH_rxn_STD`, `dS_rxn_STD`, `dG_rxn_STD`, `Keq`, and `Keq_vh_shortcut`.
- `pythermocalcdb-nasa://guidance/agent-checklist`
  - Checklist for reliable database-first and reference-backed calls.

## 🧰 MCP Tools

🔥 Species tools:

- `calc_H_T`
- `calc_S_T`
- `calc_G_T`
- `calc_Cp_T`

⚗️ Reaction tools:

- `calc_dH_rxn_STD`
- `calc_dS_rxn_STD`
- `calc_dG_rxn_STD`
- `calc_Keq`
- `calc_Keq_vh_shortcut`

🛠️ Utility tool:

- `check_yaml_reference`

## 📝 Input Model Notes

Calculation tools receive one Pydantic argument named `request`. They use shared
domain models from `pythermodb_settings`, including `Component`, `Temperature`,
and `ComponentKey`.

🗄️ Database-backed species request:

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
    "source": "database",
    "component_key": "Name-Formula",
    "nasa_type": "nasa9",
    "basis": "molar"
  }
}
```

📄 Reference-backed species request:

```json
{
  "request": {
    "component": {
      "name": "component name from prepared reference",
      "formula": "Formula",
      "state": "g"
    },
    "temperature": {
      "value": 300.0,
      "unit": "K"
    },
    "source": "reference",
    "reference_content": "REFERENCES:\n  ...",
    "component_key": "Name-Formula",
    "nasa_type": "nasa9",
    "basis": "molar"
  }
}
```

🗄️ Database-backed reaction request:

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
    "temperature": {
      "value": 398.15,
      "unit": "K"
    },
    "source": "database",
    "component_key": "Name-Formula",
    "nasa_type": "nasa9"
  }
}
```

Use the same reaction request shape with `calc_Keq_vh_shortcut` when a van't
Hoff shortcut estimate is requested. It returns a dimensionless equilibrium
constant.

Responses follow this contract:

```json
{
  "success": true,
  "message": "H_T completed successfully.",
  "results": {
    "operation": "H_T",
    "value": 0.0,
    "unit": "J/mol"
  },
  "analysis": {
    "source": "database"
  },
  "warnings": []
}
```

## ✅ Best Practices

- Use `source: "database"` first for NASA-9 data in supported `g`, `l`, and `s` phases.
- Use `source: "reference"` only with complete externally prepared `reference_content`.
- Do not ask this MCP server to search external scientific data.
- Keep temperature inputs in Kelvin.
- Make sure every reaction species appears in both the reaction equation and `components`.
- Use `nasa_type: "nasa9"` with the database source.
- Check `success`, `message`, and `warnings` before reporting results.

## 🧪 Development Quick Check

```bash
python -m py_compile pythermocalcdb_nasa_mcp/server.py
python -m py_compile pythermocalcdb_nasa_mcp/interface/core.py
python -m py_compile pythermocalcdb_nasa_mcp/models/nasa.py
python -m unittest discover tests
```

## 🚀 Examples

Example payload shapes are available in `examples/request_payloads.py`.

## 📄 License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).

## 👤 Author

- [@sinagilassi](https://www.github.com/sinagilassi)

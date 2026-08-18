from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from fastmcp import Client

from pythermocalcdb_nasa_mcp.server import create_mcp_server


logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("pyThermoLinkDB").setLevel(logging.ERROR)

CO2 = {
    "name": "carbon dioxide",
    "formula": "CO2",
    "state": "g",
}
CH4 = {
    "name": "methane",
    "formula": "CH4",
    "state": "g",
}
WGS_COMPONENTS = [
    {
        "name": "carbon monoxide",
        "formula": "CO",
        "state": "g",
    },
    {
        "name": "dihydrogen monoxide",
        "formula": "H2O",
        "state": "g",
    },
    CO2,
    {
        "name": "dihydrogen",
        "formula": "H2",
        "state": "g",
    },
]


@dataclass(frozen=True)
class ToolCase:
    name: str
    arguments: dict[str, Any]


def _species_request(component: dict[str, Any], temperature: float) -> dict[str, Any]:
    return {
        "request": {
            "component": component,
            "temperature": {
                "value": temperature,
                "unit": "K",
            },
            "source": "database",
            "component_key": "Name-Formula",
            "nasa_type": "nasa9",
            "basis": "molar",
        }
    }


def _reaction_request(temperature: float) -> dict[str, Any]:
    return {
        "request": {
            "name": "Water-Gas Shift Reaction",
            "reaction": "CO(g) + H2O(g) => CO2(g) + H2(g)",
            "components": WGS_COMPONENTS,
            "temperature": {
                "value": temperature,
                "unit": "K",
            },
            "source": "database",
            "component_key": "Name-Formula",
            "nasa_type": "nasa9",
        }
    }


def _tool_cases() -> list[ToolCase]:
    return [
        ToolCase("calc_H_T", _species_request(CO2, 300.0)),
        ToolCase("calc_S_T", _species_request(CH4, 400.0)),
        ToolCase("calc_G_T", _species_request(CO2, 500.0)),
        ToolCase("calc_Cp_T", _species_request(CH4, 600.0)),
        ToolCase("calc_dH_rxn_STD", _reaction_request(398.15)),
        ToolCase("calc_dS_rxn_STD", _reaction_request(398.15)),
        ToolCase("calc_dG_rxn_STD", _reaction_request(398.15)),
        ToolCase("calc_Keq", _reaction_request(1000.0)),
        ToolCase("calc_Keq_vh_shortcut", _reaction_request(1000.0)),
    ]


def _extract_payload(result: Any) -> dict[str, Any]:
    if getattr(result, "data", None) is not None:
        return result.data
    if getattr(result, "structured_content", None) is not None:
        return result.structured_content
    return {
        "success": not getattr(result, "is_error", False),
        "message": str(result),
        "results": None,
        "analysis": {},
        "warnings": [],
    }


async def run_server_feed() -> None:
    server_start = time.perf_counter()
    server = create_mcp_server()
    server_elapsed = time.perf_counter() - server_start

    cases = _tool_cases()
    rows: list[dict[str, Any]] = []

    async with Client(server) as client:
        for case in cases:
            started = time.perf_counter()
            result = await client.call_tool(case.name, case.arguments)
            elapsed = time.perf_counter() - started
            payload = _extract_payload(result)
            rows.append(
                {
                    "tool": case.name,
                    "elapsed_ms": round(elapsed * 1000, 3),
                    "success": payload.get("success"),
                    "value": (payload.get("results") or {}).get("value"),
                    "unit": (payload.get("results") or {}).get("unit"),
                    "warnings": payload.get("warnings", []),
                }
            )

    total_ms = sum(row["elapsed_ms"] for row in rows)
    summary = {
        "server_create_ms": round(server_elapsed * 1000, 3),
        "tool_calls": len(rows),
        "total_call_ms": round(total_ms, 3),
        "average_call_ms": round(total_ms / len(rows), 3),
        "calls": rows,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(run_server_feed())

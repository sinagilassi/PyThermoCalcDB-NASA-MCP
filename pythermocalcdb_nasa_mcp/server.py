import argparse
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    # NOTE: FastMCP import is type-checking only to keep runtime imports local.
    from fastmcp import FastMCP
    # NOTE: HTTP config is only needed when type checkers inspect run_mcp.
    from pythermocalcdb_nasa_mcp.models.refs import MCPHTTPConfig


# SECTION: Transport mode type
RunMode = Literal["stdio", "http"]


# SECTION: Package version
def get_package_version() -> str:
    # NOTE: Prefer local pyproject metadata when running directly from source.
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject_path.exists():
        with pyproject_path.open("rb") as pyproject_file:
            project_metadata = tomllib.load(pyproject_file).get("project", {})
        pyproject_version = project_metadata.get("version")
        if isinstance(pyproject_version, str):
            return pyproject_version

    try:
        # NOTE: Fall back to installed distribution metadata.
        return version("pythermocalcdb-nasa-mcp")
    except PackageNotFoundError:
        # Useful when running directly from source without installing the package.
        return "development"


# SECTION: MCP server setup and execution


def create_mcp_server() -> "FastMCP":
    # NOTE: Keep imports local so importing server.py stays lightweight.
    from fastmcp import FastMCP

    from pythermocalcdb_nasa_mcp.interface.core import (
        calc_Cp_T,
        calc_G_T,
        calc_H_T,
        calc_Keq,
        calc_S_T,
        calc_dG_rxn_STD,
        calc_dH_rxn_STD,
        calc_dS_rxn_STD,
    )
    from pythermocalcdb_nasa_mcp.resources import (
        AGENT_CHECKLIST,
        NASA_REFERENCE_REQUIREMENTS,
        REACTION_PROPERTY_WORKFLOW,
        SPECIES_PROPERTY_WORKFLOW,
    )
    from pythermocalcdb_nasa_mcp.tools.check_reference import check_yaml_reference

    mcp = FastMCP("PyThermoCalcDB-NASA-MCP")

    # SECTION: MCP resources
    # ! NASA reference requirements
    @mcp.resource(
        uri="pythermocalcdb-nasa://references/nasa-requirements",
        name="NASA Reference Requirements",
        description=(
            "Required pyThermoDB YAML structure, component rows, NASA coefficients, "
            "and temperature range rules for PyThermoCalcDB-NASA-MCP."
        ),
        mime_type="application/yaml",
        tags={
            "references",
            "requirements",
            "nasa",
            "thermodynamics",
        },
    )
    def get_nasa_reference_requirements() -> str:
        return NASA_REFERENCE_REQUIREMENTS

    # ! Species property workflow
    @mcp.resource(
        uri="pythermocalcdb-nasa://workflows/species-properties",
        name="Species Property Workflow",
        description="Agent workflow for H_T, S_T, G_T, and Cp_T species property calculations.",
        mime_type="application/yaml",
        tags={
            "workflow",
            "species",
            "nasa",
            "enthalpy",
            "entropy",
            "gibbs",
            "heat-capacity",
        },
    )
    def get_species_property_workflow() -> str:
        return SPECIES_PROPERTY_WORKFLOW

    # ! Reaction property workflow
    @mcp.resource(
        uri="pythermocalcdb-nasa://workflows/reaction-properties",
        name="Reaction Property Workflow",
        description="Agent workflow for dH_rxn_STD, dS_rxn_STD, dG_rxn_STD, and Keq reaction calculations.",
        mime_type="application/yaml",
        tags={
            "workflow",
            "reaction",
            "nasa",
            "equilibrium",
        },
    )
    def get_reaction_property_workflow() -> str:
        return REACTION_PROPERTY_WORKFLOW

    # ! Agent checklist
    @mcp.resource(
        uri="pythermocalcdb-nasa://guidance/agent-checklist",
        name="Agent Checklist",
        description="Resource-first checklist for reliable NASA calculation tool calls.",
        mime_type="application/yaml",
        tags={
            "guidance",
            "agent",
            "validation",
            "nasa",
        },
    )
    def get_agent_checklist() -> str:
        return AGENT_CHECKLIST

    # SECTION: MCP tools
    # ! Species property tools
    mcp.tool(
        calc_H_T,
        description="Calculate component enthalpy H_T using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    mcp.tool(
        calc_S_T,
        description="Calculate component entropy S_T using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    mcp.tool(
        calc_G_T,
        description="Calculate component Gibbs free energy G_T using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    mcp.tool(
        calc_Cp_T,
        description="Calculate component heat capacity Cp_T using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    # ! Reaction property tools
    mcp.tool(
        calc_dH_rxn_STD,
        description="Calculate standard enthalpy change of reaction using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    mcp.tool(
        calc_dS_rxn_STD,
        description="Calculate standard entropy change of reaction using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    mcp.tool(
        calc_dG_rxn_STD,
        description="Calculate standard Gibbs free energy change of reaction using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    mcp.tool(
        calc_Keq,
        description="Calculate reaction equilibrium constant Keq using the embedded NASA-9 database by default, or caller-supplied reference_content when source='reference'.",
    )
    # ! Supporting diagnostic tool
    mcp.tool(
        check_yaml_reference,
        description="Validate pythermodb YAML reference content for use with pyThermoDB.",
    )

    return mcp

# SECTION: MCP server execution


def run_mcp(
        mode: RunMode = "stdio",
        http_config: "MCPHTTPConfig | None" = None
) -> None:
    # NOTE: Server creation is centralized so stdio and HTTP expose identical capabilities.
    mcp = create_mcp_server()
    if mode == "stdio":
        mcp.run()
        return

    if http_config is None:
        from pythermocalcdb_nasa_mcp.models.refs import MCPHTTPConfig

        config = MCPHTTPConfig()
    else:
        config = http_config
    # NOTE: HTTP settings are transport-only and do not affect scientific calculations.
    mcp.run(transport="http", host=config.host,
            port=config.port, path=config.path)


# SECTION: Main execution
def main() -> None:
    # NOTE: CLI entrypoint for MCP clients and local development.
    parser = argparse.ArgumentParser(
        prog="pythermocalcdb-nasa-mcp",
        description="Run PyThermoCalcDB-NASA MCP server.",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {get_package_version()}",
    )

    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport mode.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP host (http mode only).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP port (http mode only).",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="HTTP path (http mode only).",
    )

    args = parser.parse_args()

    # NOTE: Route to HTTP only when explicitly requested; stdio is the default MCP transport.
    if args.mode == "http":
        from pythermocalcdb_nasa_mcp.models.refs import MCPHTTPConfig

        run_mcp(
            mode="http",
            http_config=MCPHTTPConfig(
                host=args.host,
                port=args.port,
                path=args.path,
            ),
        )
        return

    run_mcp(mode="stdio")


if __name__ == "__main__":
    main()

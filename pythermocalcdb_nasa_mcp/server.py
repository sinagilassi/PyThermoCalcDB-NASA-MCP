# import libs
import argparse
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    # fastmcp
    from fastmcp import FastMCP
    # pythermocalcdb_nasa_mcp
    from pythermocalcdb_nasa_mcp.models.refs import MCPHTTPConfig


RunMode = Literal["stdio", "http"]


# SECTION: Package version
def get_package_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject_path.exists():
        with pyproject_path.open("rb") as pyproject_file:
            project_metadata = tomllib.load(pyproject_file).get("project", {})
        pyproject_version = project_metadata.get("version")
        if isinstance(pyproject_version, str):
            return pyproject_version

    try:
        return version("pythermomodels-mcp")
    except PackageNotFoundError:
        # Useful when running directly from source without installing the package.
        return "development"


# SECTION: MCP server setup and execution


def create_mcp_server() -> "FastMCP":
    from fastmcp import FastMCP

    from pythermocalcdb_nasa_mcp.interface.core import (
        calculate_gas_fugacity,
        calculate_liquid_fugacity,
        calculate_mixture_fugacity,
        check_mixture_eos_roots,
        check_pure_component_eos_roots,
    )

    from pythermocalcdb_nasa_mcp.resources import (
        AGENT_WORKFLOW_REQUIREMENTS,
    )
    from pythermocalcdb_nasa_mcp.tools.check_reference import check_yaml_reference

    mcp = FastMCP("PyThermoModels-MCP")

    # NOTE: RESOURCES
    # ! agent workflow resource
    @mcp.resource(
        uri="pythermomodels://guidance/agent-workflow",
        name="PyThermoModels Agent Workflow",
        description=(
            "Resource-first routing, validation, argument-integrity, diagnostic, "
            "error-handling, and result-reporting instructions for agents using "
            "PyThermoModels-MCP tools."
        ),
        mime_type="application/yaml",
        tags={
            "guidance",
            "agent",
            "workflow",
            "tool-routing",
            "validation",
            "thermodynamics",
        },
    )
    def get_agent_workflow_requirements() -> str:
        return AGENT_WORKFLOW_REQUIREMENTS

    # ! eos reference
    @mcp.resource(
        uri="pythermomodels://references/eos-requirements",
        name="EOS Reference Requirements",
        description=(""),
        mime_type="application/yaml",
        tags={
            "references",
            "requirements",
            "eos",
            "equation-of-state",
            "fugacity",
            "root-analysis",
            "peng-robinson",
            "soave-redlich-kwong",
            "redlich-kwong",
            "van-der-waals",
        },
    )
    def get_eos_reference_requirements() -> str:
        return EOS_REFERENCE_REQUIREMENTS

    # ! activity reference
    @mcp.resource(
        uri="pythermomodels://references/activity-requirements",
        name="Activity Reference Requirements",
        description=(""),
        mime_type="application/yaml",
        tags={
            "references",
            "requirements",
            "activity-models",
            "liquid-phase",
            "activity-coefficients",
            "NRTL",
            "UNIQUAC",
        },
    )
    def get_activity_reference_requirements() -> str:
        return ACTIVITY_REFERENCE_REQUIREMENTS

    # NOTE: TOOLS
    # ! pure component eos roots tool
    mcp.tool(
        check_pure_component_eos_roots,
        description=(
            "Check pure-component EOS roots using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! gas fugacity calculation tool
    mcp.tool(
        calculate_gas_fugacity,
        description=(
            "Calculate pure-component gas fugacity using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! liquid fugacity calculation tool
    mcp.tool(
        calculate_liquid_fugacity,
        description=(
            "Calculate pure-component liquid fugacity using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! mixture eos roots tool
    mcp.tool(
        check_mixture_eos_roots,
        description=(
            "Check mixture EOS roots using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! mixture fugacity calculation tool
    mcp.tool(
        calculate_mixture_fugacity,
        description=(
            "Calculate mixture fugacity using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! NRTL activity coefficient tool
    mcp.tool(
        calculate_nrtl_activity_coefficient,
        description=(
            "Calculate NRTL activity coefficients using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! UNIQUAC activity coefficient tool
    mcp.tool(
        calculate_uniquac_activity_coefficient,
        description=(
            "Calculate UNIQUAC activity coefficients using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! NRTL tau_ij tool
    mcp.tool(
        calculate_nrtl_tau_ij,
        description=(
            "Calculate NRTL tau_ij using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! UNIQUAC tau_ij tool
    mcp.tool(
        calculate_uniquac_tau_ij,
        description=(
            "Calculate UNIQUAC tau_ij using pyThermoDB YAML reference_content supplied in args to build the ModelSource."
        ),
    )
    # ! reference validation tool
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
    mcp = create_mcp_server()
    if mode == "stdio":
        mcp.run()
        return

    if http_config is None:
        from pythermomodels_mcp.models.refs import MCPHTTPConfig

        config = MCPHTTPConfig()
    else:
        config = http_config
    mcp.run(transport="http", host=config.host,
            port=config.port, path=config.path)


# SECTION: Main execution
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pythermomodels-mcp",
        description="Run PyThermoModels MCP server.",
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

    if args.mode == "http":
        from pythermomodels_mcp.models.refs import MCPHTTPConfig

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

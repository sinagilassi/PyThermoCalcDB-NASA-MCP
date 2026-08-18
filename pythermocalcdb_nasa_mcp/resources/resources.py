from importlib.resources import files


# SECTION: Resource document loader
def _read_resource_doc(file_name: str) -> str:
    # NOTE: Keep resource content in external files so agent guidance can be detailed and maintainable.
    return (
        files("pythermocalcdb_nasa_mcp.resources.docs")
        .joinpath(file_name)
        .read_text(encoding="utf-8")
    )


# SECTION: External MCP resource documents
# ! NASA reference requirements
NASA_REFERENCE_REQUIREMENTS = _read_resource_doc("nasa_reference_requirements.yaml")

# ! Species property workflow
SPECIES_PROPERTY_WORKFLOW = _read_resource_doc("species_property_workflow.yaml")

# ! Reaction property workflow
REACTION_PROPERTY_WORKFLOW = _read_resource_doc("reaction_property_workflow.yaml")

# ! Agent checklist
AGENT_CHECKLIST = _read_resource_doc("agent_checklist.yaml")

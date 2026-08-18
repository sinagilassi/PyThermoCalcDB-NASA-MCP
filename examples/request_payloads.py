"""Example MCP request payload shapes without bundled scientific data."""


# SECTION: Caller-supplied reference content
# NOTE: The MCP wrapper expects the caller to provide authoritative pyThermoDB YAML.
REFERENCE_CONTENT = "REFERENCES: ..."


# SECTION: Species property request payload
SPECIES_PROPERTY_REQUEST = {
    "request": {
        "component": {
            "name": "component name from caller reference",
            "formula": "Formula",
            "state": "g",
        },
        "temperature": {
            "value": 300.0,
            "unit": "K",
        },
        "reference_content": REFERENCE_CONTENT,
        "component_key": "Name-Formula",
        "nasa_type": "nasa9",
        "basis": "molar",
    }
}


# SECTION: Reaction property request payload
REACTION_PROPERTY_REQUEST = {
    "request": {
        "name": "Caller Supplied Reaction",
        "reaction": "A(g) => B(g)",
        "components": [
            {
                "name": "component A name from caller reference",
                "formula": "A",
                "state": "g",
            },
            {
                "name": "component B name from caller reference",
                "formula": "B",
                "state": "g",
            },
        ],
        "temperature": {
            "value": 300.0,
            "unit": "K",
        },
        "reference_content": REFERENCE_CONTENT,
        "component_key": "Name-Formula",
        "nasa_type": "nasa9",
    }
}

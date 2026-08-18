"""Example MCP request payload shapes.

Database-backed requests are the default. Caller-supplied REFERENCE content is
used only when source="reference"; the MCP server does not search external data.
"""


# SECTION: Externally prepared reference content
REFERENCE_CONTENT = "REFERENCES: ..."


# SECTION: Database-backed species property request payload
SPECIES_PROPERTY_DATABASE_REQUEST = {
    "request": {
        "component": {
            "name": "carbon dioxide",
            "formula": "CO2",
            "state": "g",
        },
        "temperature": {
            "value": 300.0,
            "unit": "K",
        },
        "source": "database",
        "component_key": "Name-Formula",
        "nasa_type": "nasa9",
        "basis": "molar",
    }
}


# SECTION: Reference-backed species property request payload
SPECIES_PROPERTY_REFERENCE_REQUEST = {
    "request": {
        "component": {
            "name": "component name from prepared reference",
            "formula": "Formula",
            "state": "g",
        },
        "temperature": {
            "value": 300.0,
            "unit": "K",
        },
        "source": "reference",
        "reference_content": REFERENCE_CONTENT,
        "component_key": "Name-Formula",
        "nasa_type": "nasa9",
        "basis": "molar",
    }
}


# SECTION: Database-backed reaction property request payload
REACTION_PROPERTY_DATABASE_REQUEST = {
    "request": {
        "name": "Water-Gas Shift Reaction",
        "reaction": "CO(g) + H2O(g) => CO2(g) + H2(g)",
        "components": [
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
            {
                "name": "carbon dioxide",
                "formula": "CO2",
                "state": "g",
            },
            {
                "name": "dihydrogen",
                "formula": "H2",
                "state": "g",
            },
        ],
        "temperature": {
            "value": 398.15,
            "unit": "K",
        },
        "source": "database",
        "component_key": "Name-Formula",
        "nasa_type": "nasa9",
    }
}


# SECTION: Reference-backed reaction property request payload
REACTION_PROPERTY_REFERENCE_REQUEST = {
    "request": {
        "name": "Caller Supplied Reaction",
        "reaction": "A(g) => B(g)",
        "components": [
            {
                "name": "component A name from prepared reference",
                "formula": "A",
                "state": "g",
            },
            {
                "name": "component B name from prepared reference",
                "formula": "B",
                "state": "g",
            },
        ],
        "temperature": {
            "value": 300.0,
            "unit": "K",
        },
        "source": "reference",
        "reference_content": REFERENCE_CONTENT,
        "component_key": "Name-Formula",
        "nasa_type": "nasa9",
    }
}

import unittest

from examples.references.reference_1 import REFERENCE_CONTENT
from pyThermoDB import build_component_thermodb_from_reference
from pythermodb_settings.models import Component

from pythermocalcdb_nasa_mcp.interface.core import (
    calc_Cp_T,
    calc_G_T,
    calc_H_T,
    calc_Keq,
    calc_Keq_vh_shortcut,
    calc_S_T,
    calc_dG_rxn_STD,
    calc_dH_rxn_STD,
    calc_dS_rxn_STD,
)
from pythermocalcdb_nasa_mcp.interface.validation import validate_reaction_components
from pythermocalcdb_nasa_mcp.models.nasa import (
    ComponentInput,
    ReactionPropertyRequest,
    SpeciesPropertyRequest,
    TemperatureInput,
)
from pythermocalcdb_nasa_mcp.resources import (
    AGENT_CHECKLIST,
    NASA_REFERENCE_REQUIREMENTS,
    REACTION_PROPERTY_WORKFLOW,
    SPECIES_PROPERTY_WORKFLOW,
)
from pythermocalcdb_nasa_mcp.tools.model_source_builder import build_model_source_from_reference


CH4 = ComponentInput(name="methane", formula="CH4", state="g")
CO2 = ComponentInput(name="carbon dioxide", formula="CO2", state="g")
CO = ComponentInput(name="carbon monoxide", formula="CO", state="g")
H2O = ComponentInput(name="dihydrogen monoxide", formula="H2O", state="g")
H2 = ComponentInput(name="dihydrogen", formula="H2", state="g")
WGS_COMPONENTS = [CO, H2O, CO2, H2]
WGS_REACTION = "CO(g) + H2O(g) => CO2(g) + H2(g)"


class NASAInterfaceTests(unittest.TestCase):
    def test_species_property_outputs_match_expected_values(self):
        cases = [
            (calc_H_T, CO2, 300.0, -393438.9409053566, "J/mol"),
            (calc_S_T, CH4, 400.0, 197.51222341454707, "J/mol.K"),
            (calc_G_T, CO2, 500.0, -502649.138334726, "J/mol"),
            (calc_Cp_T, CH4, 600.0, 52.751445532576895, "J/mol.K"),
        ]
        for tool, component, temperature, expected_value, expected_unit in cases:
            with self.subTest(tool=tool.__name__):
                response = tool(
                    SpeciesPropertyRequest(
                        component=component,
                        temperature=TemperatureInput(value=temperature, unit="K"),
                    )
                )

                self.assertTrue(response["success"])
                self.assertEqual(response["results"]["unit"], expected_unit)
                self.assertAlmostEqual(response["results"]["value"], expected_value)

    def test_reaction_property_outputs_match_expected_values(self):
        cases = [
            (calc_dH_rxn_STD, 398.15, -40640.598455531974, "J/mol"),
            (calc_dS_rxn_STD, 398.15, -40.56815645513373, "J/mol.K"),
            (calc_dG_rxn_STD, 398.15, -24488.38696292042, "J/mol"),
            (calc_Keq, 1000.0, 1.4245384317027154, "dimensionless"),
            (calc_Keq_vh_shortcut, 1000.0, 0.8993756873966166, "dimensionless"),
        ]
        for tool, temperature, expected_value, expected_unit in cases:
            with self.subTest(tool=tool.__name__):
                response = tool(
                    ReactionPropertyRequest(
                        name="Water-Gas Shift Reaction",
                        reaction=WGS_REACTION,
                        components=WGS_COMPONENTS,
                        temperature=TemperatureInput(value=temperature, unit="K"),
                    )
                )

                self.assertTrue(response["success"])
                self.assertEqual(response["results"]["unit"], expected_unit)
                self.assertAlmostEqual(response["results"]["value"], expected_value)

    def test_reference_species_property_still_supported(self):
        response = calc_H_T(
            SpeciesPropertyRequest(
                component=CO2,
                temperature=TemperatureInput(value=300.0, unit="K"),
                source="reference",
                reference_content=REFERENCE_CONTENT,
            )
        )

        self.assertTrue(response["success"])
        self.assertEqual(response["analysis"]["source"], "reference")
        self.assertEqual(response["results"]["unit"], "J/mol")
        self.assertAlmostEqual(response["results"]["value"], -393438.9409053566)

    def test_reference_reaction_property_still_supported(self):
        cases = [
            (calc_Keq, 1.4245384317027154),
            (calc_Keq_vh_shortcut, 0.8993756873966166),
        ]
        for tool, expected_value in cases:
            with self.subTest(tool=tool.__name__):
                response = tool(
                    ReactionPropertyRequest(
                        name="Water-Gas Shift Reaction",
                        reaction=WGS_REACTION,
                        components=WGS_COMPONENTS,
                        temperature=TemperatureInput(value=1000.0, unit="K"),
                        source="reference",
                        reference_content=REFERENCE_CONTENT,
                    )
                )

                self.assertTrue(response["success"])
                self.assertEqual(response["analysis"]["source"], "reference")
                self.assertEqual(response["results"]["unit"], "dimensionless")
                self.assertAlmostEqual(response["results"]["value"], expected_value)

    def test_reference_source_without_reference_content_returns_structured_failure(self):
        response = calc_H_T(
            SpeciesPropertyRequest(
                component=CO2,
                temperature=TemperatureInput(value=300.0, unit="K"),
                source="reference",
            )
        )

        self.assertFalse(response["success"])
        self.assertIn("reference_content must not be blank", response["message"])

    def test_invalid_yaml_returns_structured_failure(self):
        response = calc_H_T(
            SpeciesPropertyRequest(
                component=CO2,
                temperature=TemperatureInput(value=300.0, unit="K"),
                source="reference",
                reference_content="REFERENCES: [",
            )
        )

        self.assertFalse(response["success"])
        self.assertIn("not valid YAML", response["message"])

    def test_missing_component_returns_structured_failure(self):
        response = calc_H_T(
            SpeciesPropertyRequest(
                component=ComponentInput(name="not-a-real-component", formula="Xx999", state="g"),
                temperature=TemperatureInput(value=300.0, unit="K"),
            )
        )

        self.assertFalse(response["success"])
        self.assertIn("missing from the embedded NASA-9 database", response["message"])
        self.assertIn("source='reference'", response["message"])
        self.assertIn("not-a-real-component/Xx999(g)", response["warnings"][0])

    def test_out_of_range_temperature_returns_structured_failure(self):
        response = calc_H_T(
            SpeciesPropertyRequest(
                component=CO2,
                temperature=TemperatureInput(value=1500.0, unit="K"),
                source="reference",
                reference_content=REFERENCE_CONTENT,
            )
        )

        self.assertFalse(response["success"])
        self.assertIn("outside the available reference range", response["message"])

    def test_reaction_missing_component_fails_validation(self):
        result = validate_reaction_components(WGS_REACTION, [CO, H2O, H2])

        self.assertFalse(result.success)
        self.assertIn("CO2(g)", result.message)

    def test_builder_returns_model_source(self):
        components = [Component(name=CH4.name, formula=CH4.formula, state=CH4.state)]
        model_source = build_model_source_from_reference(components, REFERENCE_CONTENT)

        self.assertIsNotNone(model_source)
        self.assertIn("methane-CH4", model_source.data_source)

    def test_reference_builder_direct_component(self):
        component = Component(name=CH4.name, formula=CH4.formula, state=CH4.state)
        thermodb_component = build_component_thermodb_from_reference(
            component_name=component.name,
            component_formula=component.formula,
            component_state=component.state,
            reference_content=REFERENCE_CONTENT,
            check_labels=False,
        )

        self.assertIsNotNone(thermodb_component)

    def test_resource_documents_are_loaded_from_external_files(self):
        self.assertIn("reference_content_contract", NASA_REFERENCE_REQUIREMENTS)
        self.assertIn("decision_rules", SPECIES_PROPERTY_WORKFLOW)
        self.assertIn("reaction_requirements", REACTION_PROPERTY_WORKFLOW)
        self.assertIn("situational_guidance", AGENT_CHECKLIST)


if __name__ == "__main__":
    unittest.main()

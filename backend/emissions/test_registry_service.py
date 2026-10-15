
from backend.emissions.calculator import EmissionFactor
from backend.emissions.factor_registry import EmissionFactorRegistry
from backend.emissions.registry_service import calculate_registered_activity


def test_registered_scope_2_calculation():
    registry = EmissionFactorRegistry()

    registry.register(
        "purchased_electricity",
        EmissionFactor(
            activity_unit="kWh",
            kg_co2e_per_unit=0.7,
            source="Illustrative test factor only",
            geography="Test",
            year=2026,
        ),
    )

    result = calculate_registered_activity(
        activity_id="ELEC-001",
        scope="scope_2",
        category="purchased_electricity",
        activity_type="purchased_electricity",
        activity_value=10000,
        activity_unit="kWh",
        geography="Test",
        year=2026,
        reporting_period="2026",
        source_reference="test-data.csv:row-1",
        registry=registry,
    )

    assert result.emissions.emissions_kg_co2e == 7000
    assert result.emissions.emissions_tonnes_co2e == 7
    assert result.emissions.factor_source == "Illustrative test factor only"
    assert result.source_reference == "test-data.csv:row-1"

    print("Registry-to-scope integration test passed!")
    print(f"Calculated emissions: {result.emissions.emissions_tonnes_co2e} tonnes CO2e")


if __name__ == "__main__":
    test_registered_scope_2_calculation()

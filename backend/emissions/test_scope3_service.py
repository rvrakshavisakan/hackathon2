
from backend.emissions.calculator import EmissionFactor
from backend.emissions.factor_registry import EmissionFactorRegistry
from backend.emissions.scope3_service import calculate_registered_scope3


def test_registered_scope3_calculation():
    registry = EmissionFactorRegistry()

    registry.register(
        "business_travel",
        EmissionFactor(
            activity_unit="km",
            kg_co2e_per_unit=0.15,
            source="Illustrative test factor only",
            geography="Test",
            year=2026,
        ),
    )

    result = calculate_registered_scope3(
        activity_id="S3-TRAVEL-001",
        category="business_travel",
        calculation_method="activity_based",
        activity_type="business_travel",
        activity_value=1000,
        activity_unit="km",
        geography="Test",
        year=2026,
        reporting_period="2026",
        source_reference="travel.csv:row-1",
        registry=registry,
    )

    assert result.emissions.emissions_kg_co2e == 150
    assert result.emissions.emissions_tonnes_co2e == 0.15
    assert result.source_reference == "travel.csv:row-1"

    print("Scope 3 registry integration test passed!")
    print(
        "Emissions:",
        result.emissions.emissions_tonnes_co2e,
        "tonnes CO2e",
    )


if __name__ == "__main__":
    test_registered_scope3_calculation()


from backend.emissions.calculator import EmissionFactor
from backend.emissions.scope2 import calculate_scope2


def make_factor(value, source):
    return EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=value,
        source=source,
        geography="Test",
        year=2026,
    )


def test_dual_scope2_calculation():
    result = calculate_scope2(
        activity_value=10000,
        activity_unit="kWh",
        location_factor=make_factor(
            0.7, "Illustrative grid factor"
        ),
        market_factor=make_factor(
            0.2, "Illustrative contractual factor"
        ),
        reporting_period="2026",
        source_reference="electricity.csv:row-1",
    )

    assert result.location_based.emissions_kg_co2e == 7000
    assert result.market_based.emissions_kg_co2e == 2000
    assert result.location_based.emissions_tonnes_co2e == 7
    assert result.market_based.emissions_tonnes_co2e == 2
    assert result.reporting_period == "2026"

    print("Scope 2 dual calculation test passed!")
    print(
        "Location-based:",
        result.location_based.emissions_tonnes_co2e,
        "tonnes CO2e",
    )
    print(
        "Market-based:",
        result.market_based.emissions_tonnes_co2e,
        "tonnes CO2e",
    )


def test_invalid_market_factor_unit_rejected():
    invalid_factor = EmissionFactor(
        activity_unit="litres",
        kg_co2e_per_unit=0.2,
        source="Illustrative test factor",
        geography="Test",
        year=2026,
    )

    try:
        calculate_scope2(
            activity_value=10000,
            activity_unit="kWh",
            location_factor=make_factor(
                0.7, "Illustrative grid factor"
            ),
            market_factor=invalid_factor,
            reporting_period="2026",
            source_reference="electricity.csv:row-1",
        )
    except ValueError:
        print("Scope 2 unit validation test passed!")
    else:
        raise AssertionError(
            "An incompatible market factor unit must be rejected."
        )


if __name__ == "__main__":
    test_dual_scope2_calculation()
    test_invalid_market_factor_unit_rejected()

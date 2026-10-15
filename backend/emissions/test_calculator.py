
from backend.emissions.calculator import (
    EmissionFactor,
    calculate_emissions,
)


def test_electricity_emissions():
    factor = EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=0.7,
        source="Illustrative test factor",
        geography="Test",
        year=2026,
    )

    result = calculate_emissions(
        activity_value=10000,
        activity_unit="kWh",
        emission_factor=factor,
    )

    assert result.emissions_kg_co2e == 7000
    assert result.emissions_tonnes_co2e == 7
    assert result.factor_source == "Illustrative test factor"

    print("Electricity emissions test passed!")
    print(f"Emissions: {result.emissions_kg_co2e} kg CO2e")
    print(f"Emissions: {result.emissions_tonnes_co2e} tonnes CO2e")


def test_zero_activity():
    factor = EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=0.7,
        source="Illustrative test factor",
        geography="Test",
        year=2026,
    )

    result = calculate_emissions(0, "kWh", factor)

    assert result.emissions_kg_co2e == 0
    print("Zero activity test passed!")


def test_negative_activity_rejected():
    factor = EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=0.7,
        source="Illustrative test factor",
        geography="Test",
        year=2026,
    )

    try:
        calculate_emissions(-100, "kWh", factor)
    except ValueError:
        print("Negative activity validation test passed!")
    else:
        raise AssertionError("Negative activity should be rejected.")


def test_incompatible_units_rejected():
    factor = EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=0.7,
        source="Illustrative test factor",
        geography="Test",
        year=2026,
    )

    try:
        calculate_emissions(100, "litres", factor)
    except ValueError:
        print("Unit validation test passed!")
    else:
        raise AssertionError("Incompatible units should be rejected.")


if __name__ == "__main__":
    test_electricity_emissions()
    test_zero_activity()
    test_negative_activity_rejected()
    test_incompatible_units_rejected()

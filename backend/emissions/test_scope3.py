
from backend.emissions.calculator import EmissionFactor
from backend.emissions.scope3 import calculate_scope3


def make_factor(unit, value):
    return EmissionFactor(
        activity_unit=unit,
        kg_co2e_per_unit=value,
        source="Illustrative test factor only",
        geography="Test",
        year=2026,
    )


def test_activity_based_calculation():
    result = calculate_scope3(
        activity_id="S3-001",
        category="business_travel",
        calculation_method="activity_based",
        activity_value=1000,
        activity_unit="km",
        emission_factor=make_factor("km", 0.15),
        reporting_period="2026",
        source_reference="travel.csv:row-1",
    )

    assert result.emissions.emissions_kg_co2e == 150
    assert result.emissions.emissions_tonnes_co2e == 0.15
    assert result.category == "business_travel"

    print("Scope 3 activity-based test passed!")


def test_spend_based_calculation():
    result = calculate_scope3(
        activity_id="S3-002",
        category="purchased_goods_and_services",
        calculation_method="spend_based",
        activity_value=10000,
        activity_unit="INR",
        emission_factor=make_factor("INR", 0.0002),
        reporting_period="2026",
        source_reference="purchases.csv:row-2",
    )

    assert result.emissions.emissions_kg_co2e == 2
    assert result.calculation_method == "spend_based"

    print("Scope 3 spend-based test passed!")


def test_waste_based_calculation():
    result = calculate_scope3(
        activity_id="S3-003",
        category="waste_generated",
        calculation_method="waste_based",
        activity_value=500,
        activity_unit="kg",
        emission_factor=make_factor("kg", 0.4),
        reporting_period="2026",
        source_reference="waste.csv:row-3",
    )

    assert result.emissions.emissions_kg_co2e == 200

    print("Scope 3 waste-based test passed!")


def test_unsupported_method_rejected():
    try:
        calculate_scope3(
            activity_id="S3-004",
            category="business_travel",
            calculation_method="guess_based",
            activity_value=100,
            activity_unit="km",
            emission_factor=make_factor("km", 0.15),
            reporting_period="2026",
            source_reference="travel.csv:row-4",
        )
    except ValueError:
        print("Scope 3 method validation test passed!")
    else:
        raise AssertionError("Unsupported methods must be rejected.")


def test_negative_activity_rejected():
    try:
        calculate_scope3(
            activity_id="S3-005",
            category="business_travel",
            calculation_method="activity_based",
            activity_value=-100,
            activity_unit="km",
            emission_factor=make_factor("km", 0.15),
            reporting_period="2026",
            source_reference="travel.csv:row-5",
        )
    except ValueError:
        print("Scope 3 negative activity test passed!")
    else:
        raise AssertionError("Negative activity must be rejected.")


def test_invalid_scope3_category_rejected():
    try:
        calculate_scope3(
            activity_id="S3-006",
            category="purchased_electricity",
            calculation_method="activity_based",
            activity_value=100,
            activity_unit="kWh",
            emission_factor=make_factor("kWh", 0.7),
            reporting_period="2026",
            source_reference="test.csv:row-6",
        )
    except ValueError:
        print("Scope 3 category validation test passed!")
    else:
        raise AssertionError("Invalid Scope 3 categories must be rejected.")


if __name__ == "__main__":
    test_activity_based_calculation()
    test_spend_based_calculation()
    test_waste_based_calculation()
    test_unsupported_method_rejected()
    test_negative_activity_rejected()
    test_invalid_scope3_category_rejected()

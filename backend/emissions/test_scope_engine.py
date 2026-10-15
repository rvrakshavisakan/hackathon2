
from backend.emissions.calculator import EmissionFactor
from backend.emissions.scope_engine import (
    EmissionActivity,
    calculate_activity,
    summarize_emissions,
)


def make_activity(
    activity_id,
    scope,
    category,
    value,
    unit,
    factor_value,
):
    return EmissionActivity(
        activity_id=activity_id,
        scope=scope,
        category=category,
        activity_value=value,
        activity_unit=unit,
        emission_factor=EmissionFactor(
            activity_unit=unit,
            kg_co2e_per_unit=factor_value,
            source="Illustrative test factor only",
            geography="Test",
            year=2026,
        ),
        reporting_period="2026",
        source_reference="test-data.csv:row-1",
    )


def test_scope_1_calculation():
    activity = make_activity(
        "A1", "scope_1", "stationary_combustion",
        100, "litres", 2.5,
    )

    result = calculate_activity(activity)

    assert result.scope == "scope_1"
    assert result.emissions.emissions_kg_co2e == 250
    print("Scope 1 test passed!")


def test_scope_2_calculation():
    activity = make_activity(
        "A2", "scope_2", "purchased_electricity",
        10000, "kWh", 0.7,
    )

    result = calculate_activity(activity)

    assert result.scope == "scope_2"
    assert result.emissions.emissions_tonnes_co2e == 7
    print("Scope 2 test passed!")


def test_scope_3_calculation():
    activity = make_activity(
        "A3", "scope_3", "business_travel",
        1000, "km", 0.15,
    )

    result = calculate_activity(activity)

    assert result.scope == "scope_3"
    assert result.emissions.emissions_kg_co2e == 150
    print("Scope 3 test passed!")


def test_invalid_scope_category_rejected():
    activity = make_activity(
        "A4", "scope_1", "purchased_electricity",
        100, "kWh", 0.7,
    )

    try:
        calculate_activity(activity)
    except ValueError:
        print("Invalid scope/category test passed!")
    else:
        raise AssertionError(
            "A Scope 2 category must not be accepted as Scope 1."
        )


def test_scope_totals():
    activities = [
        make_activity(
            "A1", "scope_1", "stationary_combustion",
            100, "litres", 2.5,
        ),
        make_activity(
            "A2", "scope_2", "purchased_electricity",
            10000, "kWh", 0.7,
        ),
        make_activity(
            "A3", "scope_3", "business_travel",
            1000, "km", 0.15,
        ),
    ]

    results = [calculate_activity(a) for a in activities]
    totals = summarize_emissions(results)

    assert totals["scope_1"] == 0.25
    assert totals["scope_2"] == 7
    assert totals["scope_3"] == 0.15
    assert totals["total"] == 7.4

    print("Scope totals test passed!")


if __name__ == "__main__":
    test_scope_1_calculation()
    test_scope_2_calculation()
    test_scope_3_calculation()
    test_invalid_scope_category_rejected()
    test_scope_totals()

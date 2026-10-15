
from backend.emissions.calculator import EmissionFactor
from backend.emissions.factor_registry import EmissionFactorRegistry


def test_factor_lookup():
    registry = EmissionFactorRegistry()

    factor = EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=0.7,
        source="Illustrative test factor only",
        geography="Test",
        year=2026,
    )

    registry.register("purchased_electricity", factor)

    result = registry.get(
        "purchased_electricity",
        "kWh",
        "Test",
        2026,
    )

    assert result == factor
    print("Factor lookup test passed!")


def test_lookup_ignores_text_case_and_spaces():
    registry = EmissionFactorRegistry()

    factor = EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=0.7,
        source="Illustrative test factor only",
        geography="Test",
        year=2026,
    )

    registry.register("Purchased_Electricity", factor)

    result = registry.get(
        " purchased_electricity ",
        "KWH",
        " test ",
        2026,
    )

    assert result == factor
    print("Case and whitespace normalization test passed!")


def test_missing_factor_rejected():
    registry = EmissionFactorRegistry()

    try:
        registry.get("purchased_electricity", "kWh", "Test", 2026)
    except LookupError:
        print("Missing factor test passed!")
    else:
        raise AssertionError("Missing factors must be rejected.")


def test_duplicate_factor_rejected():
    registry = EmissionFactorRegistry()

    factor = EmissionFactor(
        activity_unit="kWh",
        kg_co2e_per_unit=0.7,
        source="Illustrative test factor only",
        geography="Test",
        year=2026,
    )

    registry.register("purchased_electricity", factor)

    try:
        registry.register("purchased_electricity", factor)
    except ValueError:
        print("Duplicate factor test passed!")
    else:
        raise AssertionError("Duplicate factors must be rejected.")


if __name__ == "__main__":
    test_factor_lookup()
    test_lookup_ignores_text_case_and_spaces()
    test_missing_factor_rejected()
    test_duplicate_factor_rejected()

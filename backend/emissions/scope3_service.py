
from backend.emissions.factor_registry import EmissionFactorRegistry
from backend.emissions.scope3 import Scope3Result, calculate_scope3


def calculate_registered_scope3(
    activity_id: str,
    category: str,
    calculation_method: str,
    activity_type: str,
    activity_value: float,
    activity_unit: str,
    geography: str,
    year: int,
    reporting_period: str,
    source_reference: str,
    registry: EmissionFactorRegistry,
) -> Scope3Result:
    factor = registry.get(
        activity_type=activity_type,
        activity_unit=activity_unit,
        geography=geography,
        year=year,
    )

    return calculate_scope3(
        activity_id=activity_id,
        category=category,
        calculation_method=calculation_method,
        activity_value=activity_value,
        activity_unit=activity_unit,
        emission_factor=factor,
        reporting_period=reporting_period,
        source_reference=source_reference,
    )
    
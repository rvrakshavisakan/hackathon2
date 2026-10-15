
from backend.emissions.factor_registry import EmissionFactorRegistry
from backend.emissions.scope_engine import (
    EmissionActivity,
    ScopedEmissionResult,
    calculate_activity,
)


def calculate_registered_activity(
    activity_id: str,
    scope: str,
    category: str,
    activity_type: str,
    activity_value: float,
    activity_unit: str,
    geography: str,
    year: int,
    reporting_period: str,
    source_reference: str,
    registry: EmissionFactorRegistry,
) -> ScopedEmissionResult:
    factor = registry.get(
        activity_type=activity_type,
        activity_unit=activity_unit,
        geography=geography,
        year=year,
    )

    activity = EmissionActivity(
        activity_id=activity_id,
        scope=scope,
        category=category,
        activity_value=activity_value,
        activity_unit=activity_unit,
        emission_factor=factor,
        reporting_period=reporting_period,
        source_reference=source_reference,
    )

    return calculate_activity(activity)

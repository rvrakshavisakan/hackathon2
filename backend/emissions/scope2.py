
from dataclasses import dataclass

from backend.emissions.calculator import (
    EmissionFactor,
    EmissionResult,
    calculate_emissions,
)


@dataclass(frozen=True)
class Scope2Result:
    activity_value: float
    activity_unit: str
    location_based: EmissionResult
    market_based: EmissionResult
    reporting_period: str
    source_reference: str


def calculate_scope2(
    activity_value: float,
    activity_unit: str,
    location_factor: EmissionFactor,
    market_factor: EmissionFactor,
    reporting_period: str,
    source_reference: str,
) -> Scope2Result:
    if not reporting_period.strip():
        raise ValueError("Reporting period is required.")

    if not source_reference.strip():
        raise ValueError("Source reference is required.")

    location_result = calculate_emissions(
        activity_value=activity_value,
        activity_unit=activity_unit,
        emission_factor=location_factor,
    )

    market_result = calculate_emissions(
        activity_value=activity_value,
        activity_unit=activity_unit,
        emission_factor=market_factor,
    )

    return Scope2Result(
        activity_value=activity_value,
        activity_unit=activity_unit,
        location_based=location_result,
        market_based=market_result,
        reporting_period=reporting_period,
        source_reference=source_reference,
    )

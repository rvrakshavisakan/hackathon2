
from dataclasses import dataclass
from typing import Literal

from backend.emissions.calculator import (
    EmissionFactor,
    EmissionResult,
    calculate_emissions,
)


Scope = Literal["scope_1", "scope_2", "scope_3"]

SCOPE_CATEGORIES = {
    "scope_1": {
        "stationary_combustion",
        "mobile_combustion",
        "process_emissions",
        "fugitive_emissions",
    },
    "scope_2": {
        "purchased_electricity",
        "purchased_steam",
        "purchased_heating",
        "purchased_cooling",
    },
    "scope_3": {
        "purchased_goods_and_services",
        "capital_goods",
        "fuel_and_energy_related_activities",
        "upstream_transportation",
        "waste_generated",
        "business_travel",
        "employee_commuting",
        "upstream_leased_assets",
        "downstream_transportation",
        "processing_of_sold_products",
        "use_of_sold_products",
        "end_of_life_of_sold_products",
        "downstream_leased_assets",
        "franchises",
        "investments",
    },
}


@dataclass(frozen=True)
class EmissionActivity:
    activity_id: str
    scope: Scope
    category: str
    activity_value: float
    activity_unit: str
    emission_factor: EmissionFactor
    reporting_period: str
    source_reference: str


@dataclass(frozen=True)
class ScopedEmissionResult:
    activity_id: str
    scope: Scope
    category: str
    reporting_period: str
    emissions: EmissionResult
    source_reference: str


def calculate_activity(
    activity: EmissionActivity,
) -> ScopedEmissionResult:
    if activity.scope not in SCOPE_CATEGORIES:
        raise ValueError("Unsupported emissions scope.")

    if activity.category not in SCOPE_CATEGORIES[activity.scope]:
        raise ValueError(
            f"Category '{activity.category}' does not belong "
            f"to {activity.scope}."
        )

    if not activity.activity_id.strip():
        raise ValueError("Activity ID is required.")

    if not activity.reporting_period.strip():
        raise ValueError("Reporting period is required.")

    if not activity.source_reference.strip():
        raise ValueError("Source reference is required.")

    emissions = calculate_emissions(
        activity_value=activity.activity_value,
        activity_unit=activity.activity_unit,
        emission_factor=activity.emission_factor,
    )

    return ScopedEmissionResult(
        activity_id=activity.activity_id,
        scope=activity.scope,
        category=activity.category,
        reporting_period=activity.reporting_period,
        emissions=emissions,
        source_reference=activity.source_reference,
    )


def summarize_emissions(
    results: list[ScopedEmissionResult],
) -> dict[str, float]:
    totals = {
        "scope_1": 0.0,
        "scope_2": 0.0,
        "scope_3": 0.0,
    }

    for result in results:
        totals[result.scope] += (
            result.emissions.emissions_tonnes_co2e
        )

    totals["total"] = sum(totals.values())
    return totals

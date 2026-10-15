
from dataclasses import dataclass
import math

from backend.emissions.calculator import (
    EmissionFactor,
    EmissionResult,
    calculate_emissions,
)


SCOPE3_METHODS = {
    "purchased_goods_and_services": {
        "activity_based",
        "spend_based",
    },
    "capital_goods": {
        "activity_based",
        "spend_based",
    },
    "fuel_and_energy_related_activities": {
        "activity_based",
    },
    "upstream_transportation": {
        "activity_based",
        "spend_based",
    },
    "waste_generated": {
        "waste_based",
        "spend_based",
    },
    "business_travel": {
        "activity_based",
        "spend_based",
    },
    "employee_commuting": {
        "activity_based",
        "spend_based",
    },
    "upstream_leased_assets": {
        "activity_based",
        "spend_based",
    },
    "downstream_transportation": {
        "activity_based",
        "spend_based",
    },
    "processing_of_sold_products": {
        "activity_based",
    },
    "use_of_sold_products": {
        "activity_based",
    },
    "end_of_life_of_sold_products": {
        "activity_based",
        "waste_based",
    },
    "downstream_leased_assets": {
        "activity_based",
        "spend_based",
    },
    "franchises": {
        "activity_based",
        "spend_based",
    },
    "investments": {
        "activity_based",
        "spend_based",
    },
}


@dataclass(frozen=True)
class Scope3Result:
    activity_id: str
    category: str
    calculation_method: str
    reporting_period: str
    emissions: EmissionResult
    source_reference: str


def calculate_scope3(
    activity_id: str,
    category: str,
    calculation_method: str,
    activity_value: float,
    activity_unit: str,
    emission_factor: EmissionFactor,
    reporting_period: str,
    source_reference: str,
) -> Scope3Result:
    if not activity_id.strip():
        raise ValueError("Activity ID is required.")

    normalized_category = category.strip().lower()
    normalized_method = calculation_method.strip().lower()

    if normalized_category not in SCOPE3_METHODS:
        raise ValueError("Unsupported Scope 3 category.")

    if normalized_method not in SCOPE3_METHODS[normalized_category]:
        raise ValueError(
            "Calculation method is not supported for this category."
        )

    if not reporting_period.strip():
        raise ValueError("Reporting period is required.")

    if not source_reference.strip():
        raise ValueError("Source reference is required.")

    if not math.isfinite(activity_value):
        raise ValueError("Activity value must be finite.")

    if activity_value < 0:
        raise ValueError("Activity value cannot be negative.")

    emissions = calculate_emissions(
        activity_value=activity_value,
        activity_unit=activity_unit,
        emission_factor=emission_factor,
    )

    return Scope3Result(
        activity_id=activity_id,
        category=normalized_category,
        calculation_method=normalized_method,
        reporting_period=reporting_period,
        emissions=emissions,
        source_reference=source_reference,
    )

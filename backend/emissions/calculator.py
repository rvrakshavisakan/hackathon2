
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class EmissionFactor:
    activity_unit: str
    kg_co2e_per_unit: float
    source: str
    geography: str
    year: int


@dataclass(frozen=True)
class EmissionResult:
    activity_value: float
    activity_unit: str
    emission_factor: float
    emissions_kg_co2e: float
    emissions_tonnes_co2e: float
    factor_source: str
    geography: str
    year: int


def calculate_emissions(
    activity_value: float,
    activity_unit: str,
    emission_factor: EmissionFactor,
) -> EmissionResult:
    if not math.isfinite(activity_value):
        raise ValueError("Activity value must be finite.")

    if activity_value < 0:
        raise ValueError("Activity value cannot be negative.")

    if not activity_unit.strip():
        raise ValueError("Activity unit is required.")

    if activity_unit.strip().lower() != emission_factor.activity_unit.strip().lower():
        raise ValueError(
            f"Unit mismatch: activity uses '{activity_unit}', "
            f"but the emission factor expects "
            f"'{emission_factor.activity_unit}'."
        )

    if not math.isfinite(emission_factor.kg_co2e_per_unit):
        raise ValueError("Emission factor must be finite.")

    if emission_factor.kg_co2e_per_unit < 0:
        raise ValueError("Emission factor cannot be negative.")

    if not emission_factor.source.strip():
        raise ValueError("Emission factor source is required.")

    emissions_kg_co2e = (
        activity_value * emission_factor.kg_co2e_per_unit
    )

    return EmissionResult(
        activity_value=activity_value,
        activity_unit=activity_unit,
        emission_factor=emission_factor.kg_co2e_per_unit,
        emissions_kg_co2e=emissions_kg_co2e,
        emissions_tonnes_co2e=emissions_kg_co2e / 1000,
        factor_source=emission_factor.source,
        geography=emission_factor.geography,
        year=emission_factor.year,
    )

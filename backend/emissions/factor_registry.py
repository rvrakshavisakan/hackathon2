
from backend.emissions.calculator import EmissionFactor


class EmissionFactorRegistry:
    def __init__(self):
        self._factors = {}

    def register(
        self,
        activity_type: str,
        factor: EmissionFactor,
    ) -> None:
        if not activity_type.strip():
            raise ValueError("Activity type is required.")

        if not factor.activity_unit.strip():
            raise ValueError("Activity unit is required.")

        if not factor.source.strip():
            raise ValueError("Factor source is required.")

        if not factor.geography.strip():
            raise ValueError("Factor geography is required.")

        if factor.year < 1:
            raise ValueError("Factor year must be valid.")

        key = self._make_key(
            activity_type,
            factor.activity_unit,
            factor.geography,
            factor.year,
        )

        if key in self._factors:
            raise ValueError(
                "A factor already exists for this activity, "
                "unit, geography and year."
            )

        self._factors[key] = factor

    def get(
        self,
        activity_type: str,
        activity_unit: str,
        geography: str,
        year: int,
    ) -> EmissionFactor:
        key = self._make_key(
            activity_type,
            activity_unit,
            geography,
            year,
        )

        factor = self._factors.get(key)

        if factor is None:
            raise LookupError(
                "No emission factor matches the requested "
                "activity, unit, geography and year."
            )

        return factor

    @staticmethod
    def _make_key(
        activity_type: str,
        activity_unit: str,
        geography: str,
        year: int,
    ) -> tuple:
        return (
            activity_type.strip().lower(),
            activity_unit.strip().lower(),
            geography.strip().lower(),
            year,
        )

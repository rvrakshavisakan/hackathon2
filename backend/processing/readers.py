
import math
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

from backend.processing.records import (
    DocumentExtractionResult,
    DocumentRecord,
)


FIELD_ALIASES = {
    "supplier": [
        "supplier",
        "supplier name",
        "vendor",
        "vendor name",
        "provider",
        "company",
    ],
    "reporting_period": [
        "reporting period",
        "period",
        "reporting year",
        "year",
        "date",
        "month",
    ],
    "activity": [
        "activity",
        "activity type",
        "description",
        "category",
        "emission source",
        "source",
    ],
    "quantity": [
        "quantity",
        "amount",
        "consumption",
        "activity data",
        "activity quantity",
        "value",
    ],
    "unit": [
        "unit",
        "units",
        "uom",
        "unit of measure",
    ],
    "emissions_value": [
        "emissions",
        "emissions value",
        "co2e",
        "co2e emissions",
        "carbon emissions",
        "total emissions",
        "emission value",
    ],
}


MISSING_TEXT_VALUES = {
    "",
    "-",
    "--",
    "n/a",
    "na",
    "n.a.",
    "none",
    "null",
    "nil",
    "not available",
    "not applicable",
}


UNIT_ALIASES = {
    "kwh": "kWh",
    "kilowatt hour": "kWh",
    "kilowatt hours": "kWh",
    "mwh": "MWh",
    "megawatt hour": "MWh",
    "megawatt hours": "MWh",
    "wh": "Wh",
    "watt hour": "Wh",
    "watt hours": "Wh",
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "kilometre": "km",
    "kilometres": "km",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "tonne": "t",
    "tonnes": "t",
    "metric ton": "t",
    "metric tons": "t",
    "m3": "m³",
    "m^3": "m³",
    "cubic meter": "m³",
    "cubic meters": "m³",
    "l": "L",
    "liter": "L",
    "liters": "L",
    "litre": "L",
    "litres": "L",
}


def normalize_column_name(name: Any) -> str:
    text = unicodedata.normalize("NFKC", str(name))
    text = text.strip().lower()
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def build_column_mapping(columns: list[Any]) -> dict[str, Any]:
    normalized_columns = {}

    for column in columns:
        normalized = normalize_column_name(column)

        if normalized not in normalized_columns:
            normalized_columns[normalized] = column

    mapping = {}

    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)

            if normalized_alias in normalized_columns:
                mapping[field] = normalized_columns[normalized_alias]
                break

    return mapping


def clean_value(value: Any) -> Any:
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def optional_text(value: Any) -> str | None:
    value = clean_value(value)

    if value is None or isinstance(value, bool):
        return None

    text = str(value).strip()

    if text.casefold() in MISSING_TEXT_VALUES:
        return None

    return text


def optional_number(value: Any) -> float | None:
    value = clean_value(value)

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, str):
        text = value.strip()

        if text.casefold() in MISSING_TEXT_VALUES:
            return None

        if text.startswith("(") and text.endswith(")"):
            text = "-" + text[1:-1].strip()

        text = text.replace(",", "")

        if not re.fullmatch(
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
            text,
        ):
            return None

        value = text

    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    return number if math.isfinite(number) else None


def normalize_unit(value: Any) -> str | None:
    text = optional_text(value)

    if text is None:
        return None

    key = text.casefold().replace("³", "3")
    key = " ".join(key.split())

    if key in {"kg co2e", "kgco2e"}:
        return "kg CO2e"

    if key in {
        "t co2e",
        "tonnes co2e",
        "tonne co2e",
    }:
        return "t CO2e"

    return UNIT_ALIASES.get(key, text)


def normalize_reporting_period(value: Any) -> str | None:
    value = clean_value(value)

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        number = optional_number(value)

        if number is not None and number.is_integer():
            year = int(number)

            if 1900 <= year <= 2200:
                return str(year)

        return optional_text(value)

    if isinstance(value, str):
        text = optional_text(value)

        if text is None:
            return None

        if re.fullmatch(r"(?:19|20|21|22)\d{2}", text):
            return text

        return text

    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    return optional_text(value)


def dataframe_to_result(
    dataframe: pd.DataFrame,
    source_filename: str,
    source_type: str,
    sheet_name: str | None = None,
    first_data_row: int = 2,
) -> DocumentExtractionResult:
    result = DocumentExtractionResult(
        source_filename=Path(source_filename).name,
        source_type=source_type,
    )

    if dataframe.empty:
        result.errors.append("Document contains no data rows.")
        return result

    mapping = build_column_mapping(list(dataframe.columns))

    if not mapping:
        result.errors.append(
            "No recognized activity or emissions fields were found."
        )

    for index, row in dataframe.iterrows():
        raw_fields = {
            str(column): clean_value(value)
            for column, value in row.items()
        }

        if all(value is None for value in raw_fields.values()):
            continue

        fields = {
            field: row[column]
            for field, column in mapping.items()
        }

        record = DocumentRecord(
            supplier=optional_text(fields.get("supplier")),
            reporting_period=normalize_reporting_period(
                fields.get("reporting_period")
            ),
            activity=optional_text(fields.get("activity")),
            quantity=optional_number(fields.get("quantity")),
            unit=normalize_unit(fields.get("unit")),
            emissions_value=optional_number(
                fields.get("emissions_value")
            ),
            source_filename=Path(source_filename).name,
            source_type=source_type,
            sheet_name=sheet_name,
            row_number=first_data_row + int(index),
            raw_fields=raw_fields,
        )

        result.records.append(record)

    return result


def read_csv(file_path: str | Path) -> DocumentExtractionResult:
    path = Path(file_path)

    if not path.is_file():
        return DocumentExtractionResult(
            source_filename=path.name,
            source_type="csv",
            errors=["File does not exist."],
        )

    if path.suffix.lower() != ".csv":
        return DocumentExtractionResult(
            source_filename=path.name,
            source_type="csv",
            errors=["Expected a .csv file."],
        )

    dataframe = None
    last_error = None

    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            dataframe = pd.read_csv(path, encoding=encoding)
            break
        except (
    	    UnicodeDecodeError,
    	    pd.errors.ParserError,
            pd.errors.EmptyDataError,
            LookupError,
        ) as exc:
            last_error = exc

    if dataframe is None:
        return DocumentExtractionResult(
            source_filename=path.name,
            source_type="csv",
            errors=[f"Could not read CSV: {last_error}"],
        )

    return dataframe_to_result(
        dataframe=dataframe,
        source_filename=path.name,
        source_type="csv",
    )


def read_excel(file_path: str | Path) -> DocumentExtractionResult:
    path = Path(file_path)
    extension = path.suffix.lower()

    if not path.is_file():
        return DocumentExtractionResult(
            source_filename=path.name,
            source_type="excel",
            errors=["File does not exist."],
        )

    if extension not in (".xlsx", ".xls"):
        return DocumentExtractionResult(
            source_filename=path.name,
            source_type="excel",
            errors=["Expected an .xlsx or .xls file."],
        )

    result = DocumentExtractionResult(
        source_filename=path.name,
        source_type="excel",
    )

    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except Exception as exc:
        result.errors.append(
            f"Could not read Excel workbook: {type(exc).__name__}: {exc}"
        )
        return result

    for sheet_name, dataframe in sheets.items():
        sheet_result = dataframe_to_result(
            dataframe=dataframe,
            source_filename=path.name,
            source_type="excel",
            sheet_name=sheet_name,
        )

        result.records.extend(sheet_result.records)

        for error in sheet_result.errors:
            result.errors.append(f"Sheet '{sheet_name}': {error}")

    return result

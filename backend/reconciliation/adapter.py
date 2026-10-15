from datetime import date
from typing import Literal

from backend.processing.records import DocumentRecord
from backend.reconciliation.inputs import Record, ReconciliationInput
from backend.reconciliation.models import SourceRef


ValueField = Literal["quantity", "emissions_value"]


def _parse_period(value: str | None) -> tuple[date | None, date | None]:
    if not value:
        return None, None

    value = value.strip()

    if len(value) == 4 and value.isdigit():
        year = int(value)
        return date(year, 1, 1), date(year, 12, 31)

    try:
        parsed_date = date.fromisoformat(value)
        return parsed_date, parsed_date
    except ValueError:
        return None, None


def document_record_to_record(
    document: DocumentRecord,
    value_field: ValueField = "quantity",
    value_unit: str | None = None,
) -> Record:
    value = getattr(document, value_field)

    period_start, period_end = _parse_period(
        document.reporting_period
    )

    if document.sheet_name and document.row_number is not None:
        location = f"{document.sheet_name}, row {document.row_number}"
    elif document.row_number is not None:
        location = f"row {document.row_number}"
    elif document.page_number is not None:
        location = f"page {document.page_number}"
    else:
        location = None

    source = SourceRef(
        file=document.source_filename,
        location=location,
    )

    return Record(
        category=(document.activity or "uncategorized").strip().lower(),
        value=value,
        unit=value_unit or document.unit,
        period_start=period_start,
        period_end=period_end,
        source=source,
        record_id="|".join(
            str(part)
            for part in (
                document.source_filename,
                document.sheet_name,
                document.row_number,
                document.page_number,
            )
            if part is not None
        ),
    )


def documents_to_reconciliation_input(
    reported_documents: list[DocumentRecord],
    evidence_documents: list[DocumentRecord],
    required_evidence: list[str] | None = None,
    value_field: ValueField = "quantity",
    value_unit: str | None = None,
) -> ReconciliationInput:
    return ReconciliationInput(
        reported=[
            document_record_to_record(
                document, value_field, value_unit
            )
            for document in reported_documents
        ],
        evidence=[
            document_record_to_record(
                document, value_field, value_unit
            )
            for document in evidence_documents
        ],
        required_evidence=required_evidence or [],
    )

"""Deterministic reconciliation rules for CarbonWise AI."""

from collections import Counter
from uuid import uuid4

from backend.reconciliation.inputs import ReconciliationInput, Record
from backend.reconciliation.models import (
    Finding,
    FindingStatus,
    Severity,
    SourceRef,
)


def _category(value: str) -> str:
    return value.strip().lower()


def _finding(
    rule_id: str,
    title: str,
    severity: Severity,
    explanation: str,
    recommended_action: str,
    sources: list[SourceRef] | None = None,
    reported_value: float | None = None,
    evidence_value: float | None = None,
    unit: str | None = None,
    uncertainty_notes: str | None = None,
) -> Finding:
    difference = None

    if reported_value is not None and evidence_value is not None:
        difference = reported_value - evidence_value

    return Finding(
        finding_id=str(uuid4()),
        rule_id=rule_id,
        title=title,
        severity=severity,
        explanation=explanation,
        recommended_action=recommended_action,
        status=FindingStatus.OPEN,
        reported_value=reported_value,
        evidence_value=evidence_value,
        unit=unit,
        difference=difference,
        sources=sources or [],
        uncertainty_notes=uncertainty_notes,
    )


def _check_units(records: list[Record]) -> list[Finding]:
    findings = []

    for record in records:
        if record.value is None:
            continue

        if not record.unit or not record.unit.strip():
            findings.append(
                _finding(
                    rule_id="R2",
                    title="Unit is missing",
                    severity=Severity.MEDIUM,
                    explanation=(
                        f"A {record.category} record has a value "
                        "but no usable unit. It cannot be safely "
                        "compared or used in a calculation."
                    ),
                    recommended_action=(
                        "Confirm the unit from the original source "
                        "before comparing or calculating this value."
                    ),
                    sources=[record.source],
                )
            )

    grouped = {}

    for record in records:
        if record.value is None or not record.unit:
            continue

        grouped.setdefault(
            _category(record.category), {}
        ).setdefault(
            record.unit.strip().lower(), []
        ).append(record)

    for category, units in grouped.items():
        if len(units) > 1:
            records_with_units = [
                record
                for unit_records in units.values()
                for record in unit_records
            ]

            findings.append(
                _finding(
                    rule_id="R2",
                    title=f"Inconsistent units for {category}",
                    severity=Severity.MEDIUM,
                    explanation=(
                        f"The {category} records use different units: "
                        f"{', '.join(sorted(units))}. These values "
                        "must not be added or compared directly."
                    ),
                    recommended_action=(
                        "Convert values to a common compatible unit "
                        "and confirm the conversion before comparison."
                    ),
                    sources=[
                        record.source for record in records_with_units
                    ],
                    uncertainty_notes=(
                        "Different units are not necessarily an error; "
                        "they may be compatible after conversion."
                    ),
                )
            )

    return findings


def _check_totals(
    reported: list[Record],
    evidence: list[Record],
    category: str,
    rule_id: str,
) -> list[Finding]:
    findings = []

    reported_records = [
        record
        for record in reported
        if _category(record.category) == category
        and record.value is not None
    ]

    evidence_records = [
        record
        for record in evidence
        if _category(record.category) == category
        and record.value is not None
    ]

    if not reported_records or not evidence_records:
        return findings

    reported_units = {
        record.unit.strip().lower()
        for record in reported_records
        if record.unit
    }

    evidence_units = {
        record.unit.strip().lower()
        for record in evidence_records
        if record.unit
    }

    if (
        len(reported_units) != 1
        or len(evidence_units) != 1
        or reported_units != evidence_units
    ):
        return findings

    unit = reported_records[0].unit
    reported_total = sum(record.value for record in reported_records)
    evidence_total = sum(record.value for record in evidence_records)

    if abs(reported_total - evidence_total) < 1e-9:
        return findings

    findings.append(
        _finding(
            rule_id=rule_id,
            title=f"{category.title()} total needs review",
            severity=Severity.MEDIUM,
            explanation=(
                f"The reported {category} total is "
                f"{reported_total:g} {unit}, while the supplied "
                f"evidence totals {evidence_total:g} {unit}. "
                f"The difference is "
                f"{reported_total - evidence_total:g} {unit}."
            ),
            recommended_action=(
                "Confirm reporting dates, facility boundaries, "
                "record completeness, and whether all values cover "
                "the same reporting period."
            ),
            sources=[
                record.source
                for record in reported_records + evidence_records
            ],
            reported_value=reported_total,
            evidence_value=evidence_total,
            unit=unit,
            uncertainty_notes=(
                "This comparison assumes the supplied records are "
                "comparable and complete. A difference alone does "
                "not prove that either figure is incorrect."
            ),
        )
    )

    return findings


def _check_missing_evidence(
    data: ReconciliationInput,
) -> list[Finding]:
    findings = []

    available = {
        _category(record.category)
        for record in data.evidence
    }

    required = {
        _category(category)
        for category in data.required_evidence
    }

    for category in sorted(required - available):
        findings.append(
            _finding(
                rule_id="R7",
                title=f"Required evidence missing: {category}",
                severity=Severity.HIGH,
                explanation=(
                    f"The evidence checklist requires '{category}', "
                    "but no record with that category was supplied."
                ),
                recommended_action=(
                    "Request the relevant supporting document and "
                    "confirm whether it applies to this reporting period."
                ),
                uncertainty_notes=(
                    "The document may exist but have been omitted "
                    "during document processing."
                ),
            )
        )

    return findings


def _check_duplicate_ids(
    data: ReconciliationInput,
) -> list[Finding]:
    findings = []

    for label, records in (
        ("reported data", data.reported),
        ("supporting evidence", data.evidence),
    ):
        ids = [
            record.record_id
            for record in records
            if record.record_id and record.record_id.strip()
        ]

        duplicate_ids = {
            record_id
            for record_id, count in Counter(ids).items()
            if count > 1
        }

        for duplicate_id in sorted(duplicate_ids):
            duplicate_records = [
                record
                for record in records
                if record.record_id == duplicate_id
            ]

            findings.append(
                _finding(
                    rule_id="R8",
                    title="Potential duplicate record",
                    severity=Severity.MEDIUM,
                    explanation=(
                        f"Record ID '{duplicate_id}' occurs multiple "
                        f"times in {label}."
                    ),
                    recommended_action=(
                        "Inspect the source records and determine "
                        "whether they are duplicates or legitimate "
                        "separate entries."
                    ),
                    sources=[
                        record.source for record in duplicate_records
                    ],
                    uncertainty_notes=(
                        "Repeated IDs indicate a potential duplicate, "
                        "not proof of duplicated activity."
                    ),
                )
            )

    return findings


def _check_periods(
    reported: list[Record],
    evidence: list[Record],
) -> list[Finding]:
    findings = []

    categories = {
        _category(record.category)
        for record in reported + evidence
    }

    for category in sorted(categories):
        reported_records = [
            record
            for record in reported
            if _category(record.category) == category
            and record.value is not None
        ]

        evidence_records = [
            record
            for record in evidence
            if _category(record.category) == category
            and record.value is not None
        ]

        if not reported_records or not evidence_records:
            continue

        reported_periods = {
            (record.period_start, record.period_end)
            for record in reported_records
        }

        evidence_periods = {
            (record.period_start, record.period_end)
            for record in evidence_records
        }

        if reported_periods == evidence_periods:
            continue

        findings.append(
            _finding(
                rule_id="R1",
                title=f"Reporting period mismatch: {category}",
                severity=Severity.HIGH,
                explanation=(
                    f"The reported {category} records and supporting "
                    "evidence do not cover matching reporting periods. "
                    "Their totals should not be compared until the "
                    "periods have been verified."
                ),
                recommended_action=(
                    "Verify the start and end dates of the reported "
                    "records and supporting evidence. Align the "
                    "reporting periods before comparing totals."
                ),
                sources=[
                    record.source
                    for record in reported_records + evidence_records
                ],
            )
        )

    return findings


def _periods_match(
    reported: list[Record],
    evidence: list[Record],
    category: str,
) -> bool:
    reported_records = [
        record
        for record in reported
        if _category(record.category) == category
        and record.value is not None
    ]

    evidence_records = [
        record
        for record in evidence
        if _category(record.category) == category
        and record.value is not None
    ]

    if not reported_records or not evidence_records:
        return False

    reported_periods = {
        (record.period_start, record.period_end)
        for record in reported_records
    }

    evidence_periods = {
        (record.period_start, record.period_end)
        for record in evidence_records
    }

    if reported_periods != evidence_periods:
        return False

    if any(
        start is None or end is None
        for start, end in reported_periods | evidence_periods
    ):
        return False

    return True


def run_reconciliation(
    data: ReconciliationInput,
) -> list[Finding]:
    """Run implemented checks and return findings for human review."""

    all_records = data.reported + data.evidence

    findings = _check_units(all_records)
    findings.extend(_check_periods(data.reported, data.evidence))

    findings.extend(
        _check_totals(
            data.reported,
            data.evidence,
            "electricity",
            "R3",
        )
        if _periods_match(
            data.reported, data.evidence, "electricity"
        )
        else []
    )

    findings.extend(
        _check_totals(
            data.reported,
            data.evidence,
            "production",
            "R5",
        )
        if _periods_match(
            data.reported, data.evidence, "production"
        )
        else []
    )

    findings.extend(_check_missing_evidence(data))
    findings.extend(_check_duplicate_ids(data))

    return findings

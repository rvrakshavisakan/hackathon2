from datetime import date

from backend.reconciliation.engine import run_reconciliation
from backend.reconciliation.inputs import Record, ReconciliationInput
from backend.reconciliation.models import SourceRef


def test_electricity_mismatch():
    reported = Record(
        category="electricity",
        value=125000,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("emissions_report.xlsx", "Sheet1!B12"),
        record_id="report-electricity-001",
    )

    evidence = Record(
        category="electricity",
        value=118000,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("electricity_records.xlsx", "Sheet1!B7"),
        record_id="evidence-electricity-001",
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    electricity_findings = [
        finding for finding in findings if finding.rule_id == "R3"
    ]

    assert len(electricity_findings) == 1

    finding = electricity_findings[0]
    assert finding.reported_value == 125000
    assert finding.evidence_value == 118000
    assert finding.difference == 7000
    assert finding.status.value == "open"

    print("Electricity mismatch test passed!")
    print(f"Reported: {finding.reported_value} {finding.unit}")
    print(f"Evidence:  {finding.evidence_value} {finding.unit}")
    print(f"Difference: {finding.difference} {finding.unit}")
    print(f"Finding: {finding.title}")


def test_matching_electricity_values():
    reported = Record(
        category="electricity",
        value=125000,
        unit="kWh",
        source=SourceRef("emissions_report.xlsx", "Sheet1!B12"),
    )

    evidence = Record(
        category="electricity",
        value=125000,
        unit="kWh",
        source=SourceRef("electricity_records.xlsx", "Sheet1!B7"),
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    assert not any(f.rule_id == "R3" for f in findings)
    print("Matching electricity values test passed!")


def test_different_periods_skip_electricity_comparison():
    reported = Record(
        category="electricity",
        value=125000,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("emissions_report.xlsx", "Sheet1!B12"),
    )

    evidence = Record(
        category="electricity",
        value=118000,
        unit="kWh",
        period_start=date(2026, 2, 1),
        period_end=date(2026, 2, 28),
        source=SourceRef("electricity_records.xlsx", "Sheet1!B7"),
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    assert any(f.rule_id == "R1" for f in findings)
    assert not any(f.rule_id == "R3" for f in findings)
    print("Different reporting periods test passed!")


def test_missing_unit():
    reported = Record(
        category="electricity",
        value=1000,
        unit="",
        source=SourceRef("report.csv", "row 1"),
        record_id="R-UNIT-1",
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported])
    )

    assert any(f.rule_id == "R2" for f in findings)
    print("Missing unit test passed!")


def test_production_mismatch():
    reported = Record(
        category="production",
        value=500,
        unit="tonnes",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("report.csv", "row 1"),
        record_id="R-PROD-1",
    )

    evidence = Record(
        category="production",
        value=450,
        unit="tonnes",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("production_log.csv", "row 1"),
        record_id="E-PROD-1",
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    assert any(f.rule_id == "R5" for f in findings)
    print("Production mismatch test passed!")


def test_missing_required_evidence():
    findings = run_reconciliation(
        ReconciliationInput(
            required_evidence=["electricity"]
        )
    )

    assert any(f.rule_id == "R7" for f in findings)
    print("Missing required evidence test passed!")


def test_duplicate_record_ids():
    first_record = Record(
        category="electricity",
        value=100,
        unit="kWh",
        source=SourceRef("report.csv", "row 1"),
        record_id="DUP-1",
    )

    second_record = Record(
        category="electricity",
        value=200,
        unit="kWh",
        source=SourceRef("report.csv", "row 2"),
        record_id="DUP-1",
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[first_record, second_record])
    )

    assert any(f.rule_id == "R8" for f in findings)
    print("Duplicate record ID test passed!")


def test_inconsistent_units_skip_comparison():
    reported = Record(
        category="electricity",
        value=1000,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("report.csv", "row 1"),
    )

    evidence = Record(
        category="electricity",
        value=1,
        unit="MWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("evidence.csv", "row 1"),
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    assert any(
        f.rule_id == "R2" and "inconsistent units" in f.title.lower()
        for f in findings
    )
    assert not any(f.rule_id == "R3" for f in findings)
    print("Inconsistent units test passed!")


def test_multiple_records_totals():
    reported = [
        Record(
            category="electricity",
            value=600,
            unit="kWh",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            source=SourceRef("report.csv", "row 1"),
        ),
        Record(
            category="electricity",
            value=400,
            unit="kWh",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            source=SourceRef("report.csv", "row 2"),
        ),
    ]

    evidence = [
        Record(
            category="electricity",
            value=500,
            unit="kWh",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            source=SourceRef("evidence.csv", "row 1"),
        ),
        Record(
            category="electricity",
            value=450,
            unit="kWh",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            source=SourceRef("evidence.csv", "row 2"),
        ),
    ]

    findings = run_reconciliation(
        ReconciliationInput(reported=reported, evidence=evidence)
    )

    electricity_findings = [
        f for f in findings if f.rule_id == "R3"
    ]

    assert len(electricity_findings) == 1
    finding = electricity_findings[0]
    assert finding.reported_value == 1000
    assert finding.evidence_value == 950
    assert finding.difference == 50
    print("Multiple records totals test passed!")


def test_duplicate_ids_across_reported_and_evidence():
    reported = Record(
        category="electricity",
        value=100,
        unit="kWh",
        source=SourceRef("report.csv", "row 1"),
        record_id="SHARED-1",
    )

    evidence = Record(
        category="electricity",
        value=100,
        unit="kWh",
        source=SourceRef("evidence.csv", "row 1"),
        record_id="SHARED-1",
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    assert not any(f.rule_id == "R8" for f in findings)
    print("Cross-group duplicate ID behavior test passed!")


def test_missing_reporting_dates_skip_comparison():
    reported = Record(
        category="electricity",
        value=1000,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=None,
        source=SourceRef("report.csv", "row 1"),
    )

    evidence = Record(
        category="electricity",
        value=900,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("evidence.csv", "row 1"),
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    assert any(f.rule_id == "R1" for f in findings)
    assert not any(f.rule_id == "R3" for f in findings)
    print("Missing reporting dates test passed!")


def test_zero_values():
    reported = Record(
        category="electricity",
        value=0,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("report.csv", "row 1"),
    )

    evidence = Record(
        category="electricity",
        value=0,
        unit="kWh",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        source=SourceRef("evidence.csv", "row 1"),
    )

    findings = run_reconciliation(
        ReconciliationInput(reported=[reported], evidence=[evidence])
    )

    assert not any(f.rule_id == "R3" for f in findings)
    print("Zero values test passed!")


if __name__ == "__main__":
    test_electricity_mismatch()
    test_matching_electricity_values()
    test_different_periods_skip_electricity_comparison()
    test_missing_unit()
    test_production_mismatch()
    test_missing_required_evidence()
    test_duplicate_record_ids()
    test_inconsistent_units_skip_comparison()
    test_multiple_records_totals()
    test_duplicate_ids_across_reported_and_evidence()
    test_missing_reporting_dates_skip_comparison()
    test_zero_values()

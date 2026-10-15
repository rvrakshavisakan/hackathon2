"""CarbonWise AI document-to-review pipeline."""

from pathlib import Path

from backend.processing.records import DocumentExtractionResult
from backend.reconciliation.adapter import (
    ValueField,
    documents_to_reconciliation_input,
)
from backend.reconciliation.engine import run_reconciliation
from backend.rag.evidence import enrich_findings


def run_pipeline(
    reported_extraction: DocumentExtractionResult,
    evidence_extractions: list[DocumentExtractionResult],
    required_evidence: list[str] | None = None,
    value_field: ValueField = "quantity",
    value_unit: str | None = None,
    guidance_results: int = 3,
    guidance_database_dir: Path | None = None,
    max_guidance_distance: float | None = None,
) -> dict:
    """Run extraction-result validation, reconciliation, and RAG enrichment."""

    all_extractions = [reported_extraction, *evidence_extractions]

    extraction_errors = [
        {
            "source_filename": extraction.source_filename,
            "source_type": extraction.source_type,
            "errors": list(extraction.errors),
        }
        for extraction in all_extractions
        if extraction.errors
    ]

    reported_documents = reported_extraction.records
    evidence_documents = [
        record
        for extraction in evidence_extractions
        for record in extraction.records
    ]

    reconciliation_input = documents_to_reconciliation_input(
        reported_documents=reported_documents,
        evidence_documents=evidence_documents,
        required_evidence=required_evidence,
        value_field=value_field,
        value_unit=value_unit,
    )

    findings = run_reconciliation(reconciliation_input)

    enrichment_options = {"n_results": guidance_results}

    if guidance_database_dir is not None:
        enrichment_options["database_dir"] = guidance_database_dir

    if max_guidance_distance is not None:
        enrichment_options["max_distance"] = max_guidance_distance

    enriched_findings = enrich_findings(
        findings,
        **enrichment_options,
    )

    return {
        "status": (
            "completed_with_extraction_errors"
            if extraction_errors
            else "completed"
        ),
        "summary": {
            "reported_records": len(reported_documents),
            "evidence_records": len(evidence_documents),
            "findings": len(findings),
            "extraction_error_sources": len(extraction_errors),
        },
        "extraction_errors": extraction_errors,
        "findings": enriched_findings,
        "limitations": [
            "Findings are reasons for human review, not proof of errors "
            "or compliance verdicts.",
            "Extraction errors may mean that some source information "
            "was unavailable to reconciliation.",
            "PDF page text is not automatically converted into "
            "structured activity records.",
        ],
    }

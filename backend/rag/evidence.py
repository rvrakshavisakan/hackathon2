
from pathlib import Path

from backend.rag.ingest import DEFAULT_DATABASE_DIR
from backend.rag.retriever import search_guidance


def build_guidance_query(finding) -> str:
    """Build a focused search query from an existing finding."""
    parts = [
        finding.rule_id,
        finding.title,
        finding.explanation,
        finding.recommended_action,
    ]

    if finding.uncertainty_notes:
        parts.append(finding.uncertainty_notes)

    return " ".join(part.strip() for part in parts if part and part.strip())


def explain_finding(finding, evidence: list[dict]) -> dict:
    """Create transparent review assistance without changing the finding."""
    if evidence:
        evidence_summary = (
            f"Retrieved {len(evidence)} potentially relevant guidance "
            "passage(s). Review the cited text to determine whether it "
            "applies to this finding."
        )
    else:
        evidence_summary = (
            "No guidance passages passed the retrieval criteria. "
            "The finding remains valid as a reconciliation result, "
            "but no supporting guidance was attached."
        )

    return {
        "finding_summary": finding.explanation,
        "recommended_review": finding.recommended_action,
        "possible_causes": (
            "The discrepancy may have more than one explanation. "
            "Check the original records, reporting period, units, "
            "boundaries, and completeness as relevant to this finding."
        ),
        "guidance_summary": evidence_summary,
        "uncertainty": finding.uncertainty_notes,
        "interpretation_limit": (
            "Retrieved guidance is contextual evidence, not proof of an "
            "error or a compliance verdict. A reviewer must verify its "
            "applicability to the records and reporting circumstances."
        ),
    }


def enrich_finding(
    finding,
    n_results: int = 3,
    database_dir: Path = DEFAULT_DATABASE_DIR,
    max_distance: float | None = None,
) -> dict:
    """Return a finding dictionary with separate RAG evidence."""
    query = build_guidance_query(finding)

    evidence = search_guidance(
        query=query,
        n_results=n_results,
        database_dir=database_dir,
        max_distance=max_distance,
    )

    # Copy the existing contract; do not mutate the Finding object.
    result = finding.to_dict()

    result["guidance_evidence"] = [
        {
            "text": match["text"],
            "source_filename": match["source_filename"],
            "page_number": match["page_number"],
            "chunk_index": match["chunk_index"],
            "distance": match["distance"],
        }
        for match in evidence
    ]

    result["review_assistance"] = explain_finding(finding, evidence)

    result["guidance_status"] = (
        "evidence_retrieved" if evidence else "no_relevant_evidence"
    )

    return result


def enrich_findings(
    findings: list,
    n_results: int = 3,
    database_dir: Path = DEFAULT_DATABASE_DIR,
    max_distance: float | None = None,
) -> list[dict]:
    """Enrich multiple reconciliation findings without changing them."""
    return [
        enrich_finding(
            finding,
            n_results=n_results,
            database_dir=database_dir,
            max_distance=max_distance,
        )
        for finding in findings
    ]

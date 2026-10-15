"""Retrieve cited GHG Protocol passages for a saved emissions evaluation."""

SCOPE_GUIDANCE = {
    "scope1": {
        "label": "Scope 1 · Direct emissions",
        "query": "GHG Protocol Scope 1 direct emissions stationary combustion mobile combustion process and fugitive sources activity data boundaries",
        "review_check": "Check that direct sources within the reporting boundary are represented and that the activity data and units agree with source records.",
    },
    "scope2": {
        "label": "Scope 2 · Purchased energy",
        "query": "GHG Protocol Scope 2 purchased electricity steam heating cooling location based and market based methods emission factors",
        "review_check": "Check purchased energy quantities and factor sources. Review location-based and market-based results where the Scope 2 Standard requires both.",
    },
    "scope3": {
        "label": "Scope 3 · Value chain",
        "query": "GHG Protocol Scope 3 value chain categories purchased goods services supplier specific activity based spend based data quality",
        "review_check": "Check the selected value-chain category and calculation method; retain supplier or activity evidence where available and document estimates.",
    },
}


def retrieve_evaluation_guidance(evaluation):
    """Return retrieved source passages and clearly labeled review checks.

    Retrieval is best-effort so a missing/empty index cannot prevent the
    emissions results page from loading.
    """
    try:
        from backend.rag.ingest import create_collection
        from backend.rag.retriever import search_guidance

        collection = create_collection()
        if collection.count() == 0:
            return {
                "status": "not_indexed",
                "message": "Guidance documents are present but not indexed yet. Run `python -m backend.rag.ingest` from the project folder, then refresh this results page.",
                "sections": [],
            }

        totals = {
            "scope1": evaluation.scope1_emission,
            "scope2": evaluation.scope2_emission,
            "scope3": evaluation.scope3_emission,
        }
        active_scopes = [scope for scope, total in totals.items() if total > 0]
        if not active_scopes:
            active_scopes = list(SCOPE_GUIDANCE)

        sections = []
        seen = set()
        for scope in active_scopes:
            metadata = SCOPE_GUIDANCE[scope]
            matches = search_guidance(metadata["query"], n_results=2)
            evidence = []
            for match in matches:
                key = (match.get("source_filename"), match.get("page_number"), match.get("text"))
                if key in seen:
                    continue
                seen.add(key)
                evidence.append(match)
            sections.append({
                "scope": scope,
                "label": metadata["label"],
                "review_check": metadata["review_check"],
                "evidence": evidence,
            })

        has_evidence = any(section["evidence"] for section in sections)
        return {
            "status": "ready" if has_evidence else "no_matches",
            "message": "" if has_evidence else "The guidance index is available, but no matching passages were returned for these scope queries.",
            "sections": sections,
        }
    except Exception:
        return {
            "status": "unavailable",
            "message": "Guidance retrieval is unavailable. Confirm the RAG dependencies are installed and run `python -m backend.rag.ingest` from the project folder.",
            "sections": [],
        }

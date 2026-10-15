"""Shared data contract for the CarbonWise reconciliation engine.

A Finding is a reason for human review, NOT proof of an error or a
compliance verdict. Convention: difference = reported_value - evidence_value.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    INFO = "info"      # worth knowing, no action needed
    LOW = "low"        # small or explainable difference
    MEDIUM = "medium"  # needs reviewer attention
    HIGH = "high"      # large mismatch or blocking evidence gap


class FindingStatus(str, Enum):
    OPEN = "open"                # engine always creates findings as OPEN
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"      # reviewer judged it a false alarm


@dataclass(frozen=True)
class SourceRef:
    """Where a value came from. None means the location is unavailable;
    we never invent one."""
    file: Optional[str] = None
    location: Optional[str] = None  # e.g. "Sheet1!B7" or "row 12"

    def to_dict(self) -> dict:
        return {"file": self.file, "location": self.location}


@dataclass
class Finding:
    finding_id: str
    rule_id: str                  # "R1" ... "R8"
    title: str
    severity: Severity
    explanation: str              # what differs/is missing and why it matters
    recommended_action: str       # what the reviewer should do next
    status: FindingStatus = FindingStatus.OPEN
    reported_value: Optional[float] = None
    evidence_value: Optional[float] = None
    unit: Optional[str] = None
    difference: Optional[float] = None
    sources: list = field(default_factory=list)  # list[SourceRef]
    uncertainty_notes: Optional[str] = None      # what remains unknown

    def to_dict(self) -> dict:
        """Plain dict for JSON, used by the API and frontend."""
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity.value,
            "status": self.status.value,
            "reported_value": self.reported_value,
            "evidence_value": self.evidence_value,
            "unit": self.unit,
            "difference": self.difference,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
            "sources": [s.to_dict() for s in self.sources],
            "uncertainty_notes": self.uncertainty_notes,
        }
"""Input contract: the normalized records Person 2 hands to the engine.

The engine never reads files. It only sees Record objects, so it does not
care whether the source was CSV, Excel or PDF.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from backend.reconciliation.models import SourceRef


@dataclass(frozen=True)
class Record:
    category: str                       # e.g. "electricity", "production"
    value: Optional[float]              # None if missing or unreadable
    unit: Optional[str]                 # e.g. "kWh", "tonne"; None if unknown
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    source: SourceRef = field(default_factory=SourceRef)
    record_id: Optional[str] = None     # used later for duplicate checks


@dataclass
class ReconciliationInput:
    reported: list = field(default_factory=list)   # list[Record] from the emissions report
    evidence: list = field(default_factory=list)   # list[Record] from supporting documents
    required_evidence: list = field(default_factory=list)  # categories the checklist demands (for R7)

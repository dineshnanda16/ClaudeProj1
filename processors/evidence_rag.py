"""Level 6: retrieve page text and generate source-grounded finding cards.

This is local extractive RAG. It never calls an LLM or invents a clinical claim.
"""

import re
import sqlite3
from dataclasses import dataclass
from typing import List

from .normalization_storage import MedicationRecord, RunData
from .reconciliation_engine import Finding


@dataclass
class Citation:
    filename: str
    document_type: str
    page: int
    quote: str
    verified: bool


@dataclass
class EvidenceCard:
    finding: Finding
    citations: List[Citation]
    note: str


def _snippet(text, needle):
    """Return complete source lines, never a character slice through a word."""
    if not needle:
        return ""
    pattern = r"\s+".join(re.escape(token) for token in needle.split())
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""
    start = text.rfind("\n", 0, match.start()) + 1
    end = text.find("\n", match.end())
    if end == -1:
        end = len(text)
    elif end < len(text):
        # The next line often contains the dose or frequency for a drug name.
        next_end = text.find("\n", end + 1)
        end = len(text) if next_end == -1 else next_end
    return text[start:end].strip()


def _retrieve(db, data, record):
    """Prefer an exact LLM evidence excerpt, then a literal name mention on page."""
    rows = db.execute("SELECT page, text FROM pages WHERE run_id=? AND document_id=? ORDER BY page",
                      (data.run_id, record.document_id)).fetchall()
    ordered = sorted(rows, key=lambda row: row[0] != record.page)
    for number, page_text in ordered:
        if record.evidence_text:
            snippet = _snippet(page_text, record.evidence_text)
            if snippet:
                return Citation(record.filename, record.document_type, number, snippet, True)
    # A name mention is a weaker match: show it to assist human review, with its status explicit.
    for number, page_text in ordered:
        for name in (record.name, record.generic_name):
            if name and len(name) >= 4:
                snippet = _snippet(page_text, name)
                if snippet:
                    return Citation(record.filename, record.document_type, number, snippet, False)
    return None


def build_evidence_cards(data: RunData, findings: List[Finding], database_path="data/reconciliation.sqlite3"):
    by_id = {r.id: r for r in data.records}
    cards = []
    with sqlite3.connect(str(database_path)) as db:
        for finding in findings:
            citations = []
            for record_id in finding.record_ids:
                record = by_id[record_id]
                citation = _retrieve(db, data, record)
                if citation:
                    citations.append(citation)
            note = ("Extracted evidence excerpts were found on the cited pages. Check each stated field in context." if citations and all(c.verified for c in citations)
                    and len(citations) == len(finding.record_ids) else
                    "Some source excerpts are missing or name-only matches. Review the original pages before using this finding.")
            if finding.code in {"not_listed", "newly_listed"}:
                note += " Absence in another document cannot be proven by a citation."
            cards.append(EvidenceCard(finding, citations, note))
    return cards

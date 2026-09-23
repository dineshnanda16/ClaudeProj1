"""Level 4: conservative normalization and local SQLite persistence.

No brand/generic equivalence is inferred unless Level 3 supplied a generic name.
Run data can contain health information: use synthetic data for demonstrations.
"""

import json
import re
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


SOURCE_TYPES = {
    "old_prescription": "Old Prescription",
    "new_prescription": "New Prescription",
    "discharge_summary": "Discharge Summary",
    "pharmacy_list": "Pharmacy Medication List",
}


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def key(value):
    return re.sub(r"[^a-z0-9]+", " ", clean(value).casefold()).strip()


def canonical_quantity(value):
    """Convert only a single, explicit mass value; otherwise preserve literal text."""
    raw = clean(value).casefold().replace("μ", "µ")
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(mcg|µg|ug|mg|g)", raw)
    if not match:
        return key(raw)
    from decimal import Decimal
    number = Decimal(match.group(1))
    multiplier = {"mcg": 1, "µg": 1, "ug": 1, "mg": 1000, "g": 1000000}[match.group(2)]
    amount = number * multiplier
    return "{} mcg".format(format(amount.normalize(), "f"))


FREQUENCIES = {
    "once daily": "daily", "every day": "daily",
    "twice daily": "twice daily", "bid": "twice daily",
    "three times daily": "three times daily", "tid": "three times daily",
    "four times daily": "four times daily", "qid": "four times daily",
}


def canonical_frequency(value):
    raw = key(value)
    return FREQUENCIES.get(raw, raw)


def source_type(value):
    raw = getattr(value, "value", value)
    raw = clean(raw)
    return next((k for k, label in SOURCE_TYPES.items() if key(label) == key(raw)),
                next((k for k in SOURCE_TYPES if key(k) == key(raw)), "unknown"))


@dataclass
class MedicationRecord:
    id: str
    document_id: str
    document_type: str
    filename: str
    name: str
    normalized_name: str
    strength: str
    dose: str
    route: str
    frequency: str
    status: str
    page: Optional[int]
    evidence_text: str
    generic_name: str = ""
    brand_name: str = ""
    dosage_form: str = ""
    instructions: str = ""

    @property
    def is_stopped(self):
        return key(self.status) in {"stopped", "discontinued", "stop", "discontinue", "ceased"}


@dataclass
class RunData:
    run_id: str
    records: List[MedicationRecord]
    warnings: List[str]


def normalize_and_store(processed_documents, extracted_documents, database_path="data/reconciliation.sqlite3"):
    """Persist a new run. Correlate docs using type and filename, never list position."""
    run_id = uuid.uuid4().hex
    records, warnings = [], []
    pages = []
    for doc in processed_documents:
        dtype = source_type(doc.document_type)
        filename = clean(doc.filename)
        document_id = "{}:{}".format(dtype, filename)
        for page in getattr(doc, "pages", []):
            page_number = getattr(page, "page_number", None)
            if page_number is not None:
                pages.append((document_id, int(page_number), str(getattr(page, "text", "") or "")))
    available = {row[0] for row in pages}
    for doc in extracted_documents:
        dtype, filename = source_type(doc.document_type), clean(doc.filename)
        document_id = "{}:{}".format(dtype, filename)
        if document_id not in available:
            warnings.append("No processed page text for {} ({})".format(dtype, filename))
        status = key(getattr(getattr(doc, "extraction_status", ""), "value", getattr(doc, "extraction_status", "")))
        if status in {"failed", "partial"}:
            warnings.append("Extraction {} for {} ({})".format(status, dtype, filename))
        if not getattr(doc, "medications", []):
            warnings.append("No medication entries extracted for {} ({}); absence cannot be assessed reliably.".format(dtype, filename))
        for index, med in enumerate(getattr(doc, "medications", [])):
            name = clean(getattr(med, "medication_name", ""))
            generic = clean(getattr(med, "generic_name", ""))
            if not name and not generic:
                warnings.append("Unnamed medication in {} ({}) omitted".format(dtype, filename))
                continue
            source_page = getattr(med, "source_page", None)
            try:
                page_number = int(source_page) if source_page else None
            except (TypeError, ValueError):
                page_number = None
            records.append(MedicationRecord(
                id="{}:{}:{}".format(run_id, document_id, index),
                document_id=document_id, document_type=dtype, filename=filename,
                name=name or generic, normalized_name=key(generic or name),
                generic_name=generic, brand_name=clean(getattr(med, "brand_name", "")),
                strength=canonical_quantity(getattr(med, "strength", "")),
                dose=canonical_quantity(getattr(med, "dose", "")),
                route=key(getattr(med, "route", "")),
                frequency=canonical_frequency(getattr(med, "frequency", "")),
                status=clean(getattr(med, "status", "")), page=page_number,
                evidence_text=clean(getattr(med, "evidence_text", "")),
                dosage_form=key(getattr(med, "dosage_form", "")),
                instructions=clean(getattr(med, "instructions", "")),
            ))
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS pages (
                run_id TEXT NOT NULL, document_id TEXT NOT NULL, page INTEGER NOT NULL, text TEXT NOT NULL,
                PRIMARY KEY(run_id, document_id, page), FOREIGN KEY(run_id) REFERENCES runs(id));
            CREATE TABLE IF NOT EXISTS medications (
                id TEXT PRIMARY KEY, run_id TEXT NOT NULL, document_id TEXT NOT NULL,
                payload TEXT NOT NULL, FOREIGN KEY(run_id) REFERENCES runs(id));
        """)
        db.execute("INSERT INTO runs(id) VALUES (?)", (run_id,))
        db.executemany("INSERT INTO pages VALUES (?,?,?,?)", [(run_id, *row) for row in pages])
        db.executemany("INSERT INTO medications VALUES (?,?,?,?)",
                       [(r.id, run_id, r.document_id, json.dumps(asdict(r))) for r in records])
    return RunData(run_id, records, warnings)

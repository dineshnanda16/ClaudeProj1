"""Level 5: transparent, rule-based discrepancies for professional review."""

from dataclasses import dataclass
from itertools import combinations
from typing import List, Tuple

from .normalization_storage import MedicationRecord, RunData, SOURCE_TYPES


@dataclass
class Finding:
    code: str
    medication: str
    summary: str
    detail: str
    record_ids: Tuple[str, ...]
    review_status: str = "Needs clinician/pharmacist review"


@dataclass
class Comparison:
    findings: List[Finding]
    warnings: List[str]


def _label(record):
    return "{} ({})".format(SOURCE_TYPES.get(record.document_type, record.document_type), record.filename)


def reconcile(data: RunData) -> Comparison:
    findings, warnings = [], list(data.warnings)
    if len({r.document_id for r in data.records}) < 2:
        warnings.append("Fewer than two documents contain medications; cross-document comparison is limited.")
    groups = {}
    for record in data.records:
        groups.setdefault(record.normalized_name, []).append(record)
    for normalized_name, group in sorted(groups.items()):
        for left, right in combinations(group, 2):
            if left.document_id == right.document_id:
                # Multiple entries are not proof of duplicate therapy.
                findings.append(Finding("multiple_entries", left.name,
                    "Multiple entries in one document",
                    "Two extracted entries for {} appear in {}. Check the original text for repeats or distinct orders.".format(left.name, _label(left)),
                    (left.id, right.id)))
                continue
            if left.is_stopped != right.is_stopped:
                findings.append(Finding("status_difference", left.name, "Medication status differs",
                    "{}: status '{}'; {}: status '{}'. Verify dates and intended plan.".format(
                        _label(left), left.status or "unspecified", _label(right), right.status or "unspecified"),
                    (left.id, right.id)))
            if left.is_stopped or right.is_stopped:
                continue  # A stopped order is not an active dose for comparison.
            for field, title in (("strength", "Strength differs"), ("dose", "Dose differs"),
                                 ("route", "Route differs"), ("frequency", "Frequency differs")):
                a, b = getattr(left, field), getattr(right, field)
                # A blank field means unknown, never zero or an implied change.
                if a and b and a != b:
                    findings.append(Finding("{}_difference".format(field), left.name, title,
                        "{}: {}; {}: {}. Verify against the original documents.".format(
                            _label(left), a, _label(right), b), (left.id, right.id)))
        old = [r for r in group if r.document_type == "old_prescription"]
        newer = [r for r in group if r.document_type == "new_prescription"]
        # This reports document presence only. It never infers a stopped medication.
        if old and not newer and any(r.document_type == "new_prescription" for r in data.records):
            findings.append(Finding("not_listed", old[0].name, "Not listed in new prescription",
                "Present in the old prescription, but no matching extracted entry was found in the new prescription. This does not establish discontinuation.",
                (old[0].id,)))
        if newer and not old and any(r.document_type == "old_prescription" for r in data.records):
            findings.append(Finding("newly_listed", newer[0].name, "Listed in new prescription only",
                "Present in the new prescription, but no matching extracted entry was found in the old prescription. Confirm with the complete medication history.",
                (newer[0].id,)))
    # A missing or failed extraction makes absence claims especially unreliable.
    if any("Extraction failed" in w or "Extraction partial" in w for w in warnings):
        warnings.append("Presence and absence findings may reflect extraction errors.")
    return Comparison(findings, warnings)

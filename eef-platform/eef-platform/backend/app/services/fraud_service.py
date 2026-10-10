"""
Fraud Intelligence (Section 15). Every signal here is computed with real
SQL aggregation queries against the platform's own database -- not simulated.
"""
from __future__ import annotations
from collections import defaultdict
from typing import List, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models._all import (
    Document, DeviceLink, IPLink, VerificationSession, FraudCase, FraudCaseStatus, RiskLevel,
)


def find_shared_documents(db: Session) -> List[dict]:
    """Document numbers used by more than one identity."""
    rows = (
        db.query(Document.document_number, func.count(func.distinct(Document.identity_id)).label("n"))
        .filter(Document.document_number.isnot(None))
        .group_by(Document.document_number)
        .having(func.count(func.distinct(Document.identity_id)) > 1)
        .all()
    )
    results = []
    for doc_number, n in rows:
        identity_ids = [
            d.identity_id for d in db.query(Document.identity_id)
            .filter(Document.document_number == doc_number).distinct()
        ]
        results.append({"document_number": doc_number, "identity_count": n, "identity_ids": identity_ids})
    return results


def find_shared_devices(db: Session, min_identities: int = 2) -> List[dict]:
    rows = (
        db.query(DeviceLink.device_id, func.count(func.distinct(DeviceLink.identity_id)).label("n"))
        .group_by(DeviceLink.device_id)
        .having(func.count(func.distinct(DeviceLink.identity_id)) >= min_identities)
        .all()
    )
    results = []
    for device_id, n in rows:
        identity_ids = [
            l.identity_id for l in db.query(DeviceLink.identity_id)
            .filter(DeviceLink.device_id == device_id).distinct()
        ]
        results.append({"device_id": device_id, "identity_count": n, "identity_ids": identity_ids})
    return results


def find_shared_ips(db: Session, min_identities: int = 3) -> List[dict]:
    rows = (
        db.query(IPLink.ip_id, func.count(func.distinct(IPLink.identity_id)).label("n"))
        .group_by(IPLink.ip_id)
        .having(func.count(func.distinct(IPLink.identity_id)) >= min_identities)
        .all()
    )
    results = []
    for ip_id, n in rows:
        identity_ids = [
            l.identity_id for l in db.query(IPLink.identity_id)
            .filter(IPLink.ip_id == ip_id).distinct()
        ]
        results.append({"ip_id": ip_id, "identity_count": n, "identity_ids": identity_ids})
    return results


def find_repeated_failed_verifications(db: Session, min_failures: int = 2) -> List[dict]:
    rows = (
        db.query(VerificationSession.identity_id, func.count(VerificationSession.id).label("n"))
        .filter(VerificationSession.status == "REJECTED")
        .group_by(VerificationSession.identity_id)
        .having(func.count(VerificationSession.id) >= min_failures)
        .all()
    )
    return [{"identity_id": identity_id, "failed_count": n} for identity_id, n in rows]


def get_fraud_signal_count_for_identity(db: Session, identity_id: int) -> int:
    """Used live during verification to feed the trust-scoring penalty."""
    count = 0
    for group in find_shared_documents(db):
        if identity_id in group["identity_ids"]:
            count += 1
    for group in find_shared_devices(db):
        if identity_id in group["identity_ids"]:
            count += 1
    for group in find_shared_ips(db):
        if identity_id in group["identity_ids"]:
            count += 1
    for row in find_repeated_failed_verifications(db):
        if row["identity_id"] == identity_id:
            count += 1
    return count


def build_fraud_cases(db: Session) -> List[FraudCase]:
    """Materializes FraudCase rows from currently-detected signals (idempotent-ish: creates new snapshot cases)."""
    created = []

    for group in find_shared_documents(db):
        if group["identity_count"] >= 2:
            fc = FraudCase(
                severity=RiskLevel.HIGH.value if group["identity_count"] > 2 else RiskLevel.MEDIUM.value,
                status=FraudCaseStatus.OPEN.value,
                signals=["document_reuse"],
                related_identities=group["identity_ids"],
                related_documents=[group["document_number"]],
                related_devices=[],
                investigation_notes=[],
            )
            db.add(fc)
            created.append(fc)

    for group in find_shared_devices(db):
        fc = FraudCase(
            severity=RiskLevel.HIGH.value if group["identity_count"] > 3 else RiskLevel.MEDIUM.value,
            status=FraudCaseStatus.OPEN.value,
            signals=["device_sharing"],
            related_identities=group["identity_ids"],
            related_documents=[],
            related_devices=[group["device_id"]],
            investigation_notes=[],
        )
        db.add(fc)
        created.append(fc)

    for row in find_repeated_failed_verifications(db):
        fc = FraudCase(
            severity=RiskLevel.MEDIUM.value,
            status=FraudCaseStatus.OPEN.value,
            signals=["repeated_failed_verification"],
            related_identities=[row["identity_id"]],
            related_documents=[], related_devices=[],
            investigation_notes=[f"{row['failed_count']} rejected verification sessions on record."],
        )
        db.add(fc)
        created.append(fc)

    db.commit()
    for fc in created:
        db.refresh(fc)
    return created

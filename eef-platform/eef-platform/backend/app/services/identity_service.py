"""
Identity Verification Engine (Sections 6 & 51) - orchestrates the full
pipeline: document OCR -> face match -> liveness -> trust scoring -> fraud
intelligence -> decision -> audit -> alerts.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from app.core.logging import logger, Timer
from app.models._all import (
    Identity, Document, VerificationSession, FaceResult, LivenessResult,
    TrustScore, Device, DeviceLink, IPAddress, IPLink,
)
from app.services import document_service, face_service, liveness_service, trust_service
from app.services import fraud_service, alert_service, audit_service


def _get_or_create_device(db: Session, identity_id: int, fingerprint: Optional[str]):
    if not fingerprint:
        return
    device = db.query(Device).filter(Device.device_fingerprint == fingerprint).first()
    if not device:
        device = Device(device_fingerprint=fingerprint, device_type="unknown", os="unknown")
        db.add(device)
        db.commit()
        db.refresh(device)
    existing_link = (
        db.query(DeviceLink)
        .filter(DeviceLink.identity_id == identity_id, DeviceLink.device_id == device.id)
        .first()
    )
    if not existing_link:
        db.add(DeviceLink(identity_id=identity_id, device_id=device.id))
        db.commit()


def _get_or_create_ip(db: Session, identity_id: int, ip: Optional[str]):
    if not ip:
        return
    ip_row = db.query(IPAddress).filter(IPAddress.ip == ip).first()
    if not ip_row:
        ip_row = IPAddress(ip=ip)
        db.add(ip_row)
        db.commit()
        db.refresh(ip_row)
    existing_link = (
        db.query(IPLink).filter(IPLink.identity_id == identity_id, IPLink.ip_id == ip_row.id).first()
    )
    if not existing_link:
        db.add(IPLink(identity_id=identity_id, ip_id=ip_row.id))
        db.commit()


def run_verification(
    db: Session,
    identity: Identity,
    document_type: str,
    document_bytes: bytes,
    selfie_bytes: bytes,
    device_fingerprint: Optional[str] = None,
    ip_address: Optional[str] = None,
    actor: str = "system",
) -> VerificationSession:
    timings = {}

    session = VerificationSession(
        identity_id=identity.id, status="PROCESSING",
        device_fingerprint=device_fingerprint, ip_address=ip_address,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # 1-6: Document OCR + validation
    with Timer("document_ocr") as t:
        doc_result = document_service.analyze_document(document_bytes)
    timings["document_ocr_ms"] = round(t.elapsed_ms, 2)

    document = Document(
        identity_id=identity.id, document_type=document_type,
        document_number=doc_result.extracted_fields.get("document_number"),
        file_hash=doc_result.file_hash, ocr_text=doc_result.ocr_text,
        extracted_fields=doc_result.extracted_fields, ocr_confidence=doc_result.ocr_confidence,
        document_score=doc_result.document_score, anomalies=doc_result.anomalies,
        model_type=doc_result.model_type,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    session.document_id = document.id

    # 7-10: Face extraction, embedding, comparison
    with Timer("face_match") as t:
        face_match = face_service.match_faces(document_bytes, selfie_bytes)
    timings["face_match_ms"] = round(t.elapsed_ms, 2)

    face_row = FaceResult(
        verification_id=session.id, similarity_score=face_match.similarity_score,
        match_decision=face_match.match_decision,
        faces_detected_reference=face_match.faces_detected_reference,
        faces_detected_comparison=face_match.faces_detected_comparison,
        quality_score=face_match.quality_score, threshold_used=face_match.threshold_used,
        model_type=face_match.model_type,
    )
    db.add(face_row)

    # 11: Liveness (passive, on the selfie)
    with Timer("liveness") as t:
        liveness = liveness_service.verify_passive_liveness(selfie_bytes)
    timings["liveness_ms"] = round(t.elapsed_ms, 2)

    liveness_row = LivenessResult(
        verification_id=session.id, liveness_score=liveness.liveness_score,
        challenge=liveness.challenge, completed_steps=liveness.completed_steps,
        spoof_indicators=liveness.spoof_indicators, mode=liveness.mode,
        model_type=liveness.model_type,
    )
    db.add(liveness_row)
    db.commit()

    # Link device/IP for graph & fraud intelligence
    _get_or_create_device(db, identity.id, device_fingerprint)
    _get_or_create_ip(db, identity.id, ip_address)

    # 12-13: Fraud intelligence + trust scoring
    fraud_signal_count = fraud_service.get_fraud_signal_count_for_identity(db, identity.id)

    identity_score = 0.85 if doc_result.extracted_fields.get("name") else 0.5
    biometric_score = face_match.similarity_score
    liveness_score = liveness.liveness_score
    document_score_norm = doc_result.document_score / 100.0

    trust_result = trust_service.compute_trust_score(
        identity_score=identity_score,
        biometric_score=biometric_score,
        liveness_score=liveness_score,
        document_score=document_score_norm,
        fraud_signal_count=fraud_signal_count,
        face_mismatch=not face_match.match_decision,
        low_liveness=liveness.liveness_score < 0.55,
    )

    trust_row = TrustScore(
        identity_id=identity.id, verification_id=session.id,
        trust_score=trust_result.trust_score, risk_level=trust_result.risk_level,
        positive_signals=trust_result.positive_signals, negative_signals=trust_result.negative_signals,
        weights_used=trust_result.weights_used, explanation=trust_result.explanation,
    )
    db.add(trust_row)

    identity.trust_score_cached = trust_result.trust_score
    identity.risk_level_cached = trust_result.risk_level

    # 14: Verification decision
    status = trust_service.decide_verification_status(
        trust_result.trust_score, strong_fraud_signal=fraud_signal_count >= 3,
    )

    fraud_indicators = []
    if not face_match.match_decision:
        fraud_indicators.append("FACE_MISMATCH")
    if liveness.liveness_score < 0.55:
        fraud_indicators.append("LOW_LIVENESS")
    if doc_result.anomalies:
        fraud_indicators.append("DOCUMENT_ANOMALY")
    if fraud_signal_count > 0:
        fraud_indicators.append("FRAUD_SIGNAL_MATCH")

    session.status = status
    session.identity_match_score = face_match.similarity_score
    session.liveness_score = liveness.liveness_score
    session.document_score = doc_result.document_score
    session.risk_score = round(100 - trust_result.trust_score, 2)
    session.trust_score = trust_result.trust_score
    session.fraud_indicators = fraud_indicators
    session.explanation = {
        "document": {"score": doc_result.document_score, "anomalies": doc_result.anomalies,
                      "model_type": doc_result.model_type},
        "face": {"similarity": face_match.similarity_score, "match": face_match.match_decision,
                 "explanation": face_match.explanation, "model_type": face_match.model_type},
        "liveness": {"score": liveness.liveness_score, "indicators": liveness.spoof_indicators,
                     "model_type": liveness.model_type, "note": liveness.note},
        "trust": trust_result.explanation,
        "fraud_signal_count": fraud_signal_count,
        "decision_reasoning": _decision_reasoning(status, trust_result, face_match, liveness, doc_result, fraud_signal_count),
        "timings_ms": timings,
    }

    db.commit()
    db.refresh(session)

    # 15: Audit
    audit_service.record(
        db, actor=actor, action="IDENTITY_VERIFICATION", resource=f"verification:{session.id}",
        result=status, ip=ip_address or "", meta={"identity_id": identity.id, "trust_score": trust_result.trust_score},
    )

    # 16: Alerts
    if not face_match.match_decision:
        alert_service.create_alert(db, "FACE_MISMATCH", "HIGH", identity.id,
                                    "Face similarity below configured threshold during verification.",
                                    {"verification_id": session.id, "similarity": face_match.similarity_score})
    if liveness.liveness_score < 0.55:
        alert_service.create_alert(db, "LOW_LIVENESS", "MEDIUM", identity.id,
                                    "Passive liveness score below pass threshold.",
                                    {"verification_id": session.id, "score": liveness.liveness_score})
    if trust_result.risk_level in ("HIGH", "CRITICAL"):
        alert_service.create_alert(db, "HIGH_RISK_IDENTITY", trust_result.risk_level, identity.id,
                                    "Identity trust score indicates elevated risk.",
                                    {"verification_id": session.id, "trust_score": trust_result.trust_score})
    if fraud_signal_count >= 2:
        alert_service.create_alert(db, "MULTIPLE_IDENTITY_USAGE", "HIGH", identity.id,
                                    "Fraud intelligence matched shared device/document/IP signals.",
                                    {"verification_id": session.id, "signal_count": fraud_signal_count})

    logger.info(f"verification {session.id} completed status={status} trust={trust_result.trust_score}")
    return session


def _decision_reasoning(status, trust_result, face_match, liveness, doc_result, fraud_signal_count) -> list[str]:
    reasons = []
    reasons.append(f"Trust score {trust_result.trust_score} -> status {status} "
                    f"(VERIFIED>={_settings_verified()}, REVIEW>={_settings_review()}).")
    if not face_match.match_decision:
        reasons.append("Face similarity below threshold.")
    if liveness.liveness_score < 0.55:
        reasons.append("Liveness score below pass threshold.")
    if doc_result.anomalies:
        reasons.append(f"Document anomalies: {', '.join(doc_result.anomalies)}")
    if fraud_signal_count:
        reasons.append(f"{fraud_signal_count} fraud intelligence signal(s) matched.")
    return reasons


def _settings_verified():
    from app.core.config import settings
    return settings.TRUST_VERIFIED_MIN


def _settings_review():
    from app.core.config import settings
    return settings.TRUST_REVIEW_MIN

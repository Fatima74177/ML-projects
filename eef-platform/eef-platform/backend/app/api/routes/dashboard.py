from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_viewer
from app.models._all import (
    Identity, VerificationSession, Alert, FraudCase, DeepfakeResult, VoiceResult, TrustScore,
)

router = APIRouter()


@router.get("/stats", summary="Executive dashboard summary statistics",
            description="All figures are computed live from the database -- never hardcoded. Returns totals, "
                        "success/failure counts, risk breakdown, and alert/fraud counts.")
def stats(db: Session = Depends(get_db), _user=Depends(require_viewer)):
    total_identities = db.query(func.count(Identity.id)).scalar() or 0
    total_verifications = db.query(func.count(VerificationSession.id)).scalar() or 0
    verified = db.query(func.count(VerificationSession.id)).filter(VerificationSession.status == "VERIFIED").scalar() or 0
    rejected = db.query(func.count(VerificationSession.id)).filter(VerificationSession.status == "REJECTED").scalar() or 0
    review = db.query(func.count(VerificationSession.id)).filter(VerificationSession.status == "REVIEW_REQUIRED").scalar() or 0

    high_risk = db.query(func.count(Identity.id)).filter(Identity.risk_level_cached.in_(["HIGH", "CRITICAL"])).scalar() or 0
    deepfake_alerts = db.query(func.count(Alert.id)).filter(Alert.type == "DEEPFAKE_DETECTED").scalar() or 0
    document_alerts = db.query(func.count(Alert.id)).filter(Alert.type == "FAKE_DOCUMENT").scalar() or 0
    voice_alerts = db.query(func.count(Alert.id)).filter(Alert.type == "VOICE_CLONE_SUSPECTED").scalar() or 0
    open_fraud_cases = db.query(func.count(FraudCase.id)).filter(FraudCase.status != "CLOSED").scalar() or 0

    return {
        "total_users": total_identities,
        "total_verifications": total_verifications,
        "successful_verifications": verified,
        "failed_verifications": rejected,
        "review_required_verifications": review,
        "high_risk_identities": high_risk,
        "deepfake_alerts": deepfake_alerts,
        "document_fraud_alerts": document_alerts,
        "voice_alerts": voice_alerts,
        "open_fraud_cases": open_fraud_cases,
        "success_rate_pct": round((verified / total_verifications * 100), 2) if total_verifications else 0.0,
    }


@router.get("/charts/risk-distribution", summary="Risk-level distribution across identities")
def risk_distribution(db: Session = Depends(get_db), _user=Depends(require_viewer)):
    rows = db.query(Identity.risk_level_cached, func.count(Identity.id)).group_by(Identity.risk_level_cached).all()
    return [{"risk_level": r or "UNKNOWN", "count": c} for r, c in rows]


@router.get("/charts/trust-score-distribution", summary="Trust score histogram buckets (0-100 in steps of 10)")
def trust_score_distribution(db: Session = Depends(get_db), _user=Depends(require_viewer)):
    scores = [s for (s,) in db.query(Identity.trust_score_cached).all()]
    buckets = {f"{i}-{i+10}": 0 for i in range(0, 100, 10)}
    for s in scores:
        idx = min(int(s // 10) * 10, 90)
        buckets[f"{idx}-{idx+10}"] += 1
    return [{"bucket": k, "count": v} for k, v in buckets.items()]


@router.get("/charts/alert-severity", summary="Alert severity distribution")
def alert_severity(db: Session = Depends(get_db), _user=Depends(require_viewer)):
    rows = db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all()
    return [{"severity": s, "count": c} for s, c in rows]


@router.get("/charts/verification-trend", summary="Verification volume by day (last 30 records grouped)")
def verification_trend(db: Session = Depends(get_db), _user=Depends(require_viewer)):
    rows = (
        db.query(func.date(VerificationSession.created_at), func.count(VerificationSession.id))
        .group_by(func.date(VerificationSession.created_at))
        .order_by(func.date(VerificationSession.created_at))
        .all()
    )
    return [{"date": str(d), "count": c} for d, c in rows]

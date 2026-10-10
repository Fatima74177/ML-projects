from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_analyst, require_viewer
from app.models._all import Identity, TrustScore
from app.services import trust_service, fraud_service

router = APIRouter()


class TrustScoreRequest(BaseModel):
    identity_score: float = Field(ge=0, le=1)
    biometric_score: float = Field(ge=0, le=1)
    liveness_score: float = Field(ge=0, le=1)
    document_score: float = Field(ge=0, le=1)
    behavior_score: float = Field(default=0.7, ge=0, le=1)
    device_score: float = Field(default=0.7, ge=0, le=1)
    fraud_signal_count: int = 0
    deepfake_flag: bool = False
    face_mismatch: bool = False
    low_liveness: bool = False


@router.post("/compute", summary="Compute a trust score from raw signal inputs (utility/testing endpoint)",
             description="Exposes the transparent weighted trust-scoring formula directly. Weights are read from "
                         "server configuration (never hidden) and returned in the response.")
def compute_trust(payload: TrustScoreRequest, _user=Depends(require_analyst)):
    result = trust_service.compute_trust_score(**payload.model_dump())
    return {
        "trust_score": result.trust_score, "risk_level": result.risk_level,
        "positive_signals": result.positive_signals, "negative_signals": result.negative_signals,
        "weights_used": result.weights_used, "explanation": result.explanation,
    }


@router.get("/identity/{identity_id}", summary="Get the latest trust score for an identity")
def get_identity_trust(identity_id: int, db: Session = Depends(get_db), _user=Depends(require_viewer)):
    row = db.query(TrustScore).filter(TrustScore.identity_id == identity_id) \
        .order_by(TrustScore.created_at.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="No trust score computed for this identity yet")
    return row

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import require_analyst, get_current_user
from app.models._all import Identity, VerificationSession, DocumentType
from app.services import identity_service
from app.utils.validators import validate_and_read

router = APIRouter()


@router.post("/verify", summary="Run the full identity verification pipeline",
             description="Accepts identity info, a document image, and a selfie. Runs OCR, face matching, "
                         "liveness, trust scoring, fraud intelligence, and a final VERIFIED/REVIEW_REQUIRED/"
                         "REJECTED decision. Every stage is logged and alerts are raised automatically when "
                         "thresholds are crossed.")
async def verify_identity(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    document_type: str = Form(...),
    device_fingerprint: str = Form(""),
    document: UploadFile = File(...),
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_analyst),
):
    if document_type not in [d.value for d in DocumentType]:
        raise HTTPException(status_code=422, detail=f"document_type must be one of {[d.value for d in DocumentType]}")

    doc_bytes = await validate_and_read(document, settings.ALLOWED_DOC_EXT)
    selfie_bytes = await validate_and_read(selfie, settings.ALLOWED_IMAGE_EXT)

    identity = Identity(full_name=full_name, email=email or None, phone=phone or None)
    db.add(identity)
    db.commit()
    db.refresh(identity)

    ip = request.client.host if request.client else ""
    session = identity_service.run_verification(
        db, identity, document_type, doc_bytes, selfie_bytes,
        device_fingerprint=device_fingerprint or None, ip_address=ip, actor=user.username,
    )

    return {
        "verification_id": session.id,
        "identity_id": identity.id,
        "status": session.status,
        "identity_match_score": session.identity_match_score,
        "liveness_score": session.liveness_score,
        "document_score": session.document_score,
        "risk_score": session.risk_score,
        "trust_score": session.trust_score,
        "fraud_indicators": session.fraud_indicators,
        "explanation": session.explanation,
        "timestamp": session.created_at,
    }


@router.get("/{verification_id}", summary="Get a verification session by ID")
def get_verification(verification_id: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    session = db.query(VerificationSession).filter(VerificationSession.id == verification_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")
    return session


@router.get("", summary="List recent verification sessions")
def list_verifications(limit: int = 50, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(VerificationSession).order_by(VerificationSession.created_at.desc()).limit(limit).all()

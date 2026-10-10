from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
import random

from app.core.database import get_db
from app.core.config import settings
from app.core.security import require_analyst
from app.services import face_service, liveness_service
from app.utils.validators import validate_and_read
from app.services import audit_service

router = APIRouter()


@router.post("/match", summary="Compare a reference image against a comparison image",
             description="Detects faces in both images, computes an embedding-based similarity score, and returns "
                         "a match decision against the configured threshold (see FACE_MATCH_THRESHOLD).")
async def face_match(
    reference: UploadFile = File(...),
    comparison: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_analyst),
):
    ref_bytes = await validate_and_read(reference, settings.ALLOWED_IMAGE_EXT)
    cmp_bytes = await validate_and_read(comparison, settings.ALLOWED_IMAGE_EXT)
    result = face_service.match_faces(ref_bytes, cmp_bytes)
    audit_service.record(db, actor=user.username, action="FACE_MATCH", result="SUCCESS")
    return {
        "similarity_score": result.similarity_score,
        "match_decision": result.match_decision,
        "faces_detected_reference": result.faces_detected_reference,
        "faces_detected_comparison": result.faces_detected_comparison,
        "quality_score": result.quality_score,
        "threshold_used": result.threshold_used,
        "model_type": result.model_type,
        "explanation": result.explanation,
    }


@router.get("/liveness/challenge", summary="Generate a random active-liveness challenge sequence")
def liveness_challenge(steps: int = 3):
    return {"challenge": liveness_service.generate_challenge(steps),
            "note": "Prototype liveness detection -- not a certified liveness result."}


@router.post("/liveness/active", summary="Verify an active-liveness challenge from uploaded frames",
             description="Accepts the challenge sequence and a list of frame images; verifies motion between "
                         "frames as a proxy for challenge completion. Prototype only.")
async def liveness_active(
    challenge: str = Form(..., description="Comma-separated challenge steps, e.g. 'blink,turn_left,smile'"),
    frames: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_analyst),
):
    challenge_list = [c.strip() for c in challenge.split(",") if c.strip()]
    frame_bytes = [await validate_and_read(f, settings.ALLOWED_IMAGE_EXT) for f in frames]
    result = liveness_service.verify_active_liveness(challenge_list, frame_bytes)
    audit_service.record(db, actor=user.username, action="LIVENESS_CHECK", result="SUCCESS")
    return result


@router.post("/liveness/passive", summary="Run passive anti-spoof analysis on a single image",
             description="Analyzes texture, lighting, and boundary artifacts for spoof indicators. Prototype only "
                         "-- not a certified liveness/anti-spoofing result.")
async def liveness_passive(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_analyst),
):
    img_bytes = await validate_and_read(image, settings.ALLOWED_IMAGE_EXT)
    result = liveness_service.verify_passive_liveness(img_bytes)
    audit_service.record(db, actor=user.username, action="LIVENESS_CHECK", result="SUCCESS")
    return result

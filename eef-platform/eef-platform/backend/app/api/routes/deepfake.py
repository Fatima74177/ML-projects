import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import require_analyst, require_viewer
from app.models._all import DeepfakeResult
from app.services import deepfake_service, audit_service, alert_service
from app.utils.validators import validate_and_read

router = APIRouter()


@router.post("/analyze", summary="Analyze an image or video for deepfake/manipulation indicators",
             description="Computes explainable forensic signals (frequency-domain artifacts, facial boundary "
                         "discontinuity, compression inconsistency, and for video: temporal/frame consistency). "
                         "This is a prototype forensic heuristic, not a certified deepfake classifier -- every "
                         "result requires human review.")
async def analyze_deepfake(
    media_type: str,
    identity_id: int | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_analyst),
):
    media_type = media_type.upper()
    if media_type not in ("IMAGE", "VIDEO"):
        raise HTTPException(status_code=422, detail="media_type must be IMAGE or VIDEO")

    if media_type == "IMAGE":
        data = await validate_and_read(file, settings.ALLOWED_IMAGE_EXT)
        result = deepfake_service.analyze_image(data)
        file_path = None
    else:
        data = await validate_and_read(file, settings.ALLOWED_VIDEO_EXT)
        suffix = "." + (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "mp4")
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            result = deepfake_service.analyze_video(tmp_path)
        finally:
            os.unlink(tmp_path)
        file_path = None

    row = DeepfakeResult(
        identity_id=identity_id, media_type=media_type, file_path=file_path,
        deepfake_probability=result.deepfake_probability, real_probability=result.real_probability,
        confidence=result.confidence, indicators=result.indicators, frame_results=result.frame_results,
        metadata_json=result.metadata, model_type=result.model_type,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_service.record(db, actor=user.username, action="DEEPFAKE_ANALYSIS", result="SUCCESS",
                          meta={"deepfake_probability": result.deepfake_probability})

    if result.deepfake_probability >= settings.DEEPFAKE_ALERT_THRESHOLD:
        alert_service.create_alert(db, "DEEPFAKE_DETECTED", "HIGH", identity_id,
                                    f"Deepfake probability {result.deepfake_probability} exceeded alert threshold.",
                                    {"deepfake_result_id": row.id, "indicators": result.indicators})

    return {
        "id": row.id,
        "deepfake_probability": result.deepfake_probability,
        "real_probability": result.real_probability,
        "confidence": result.confidence,
        "indicators": result.indicators,
        "frame_results": result.frame_results,
        "metadata": result.metadata,
        "model_type": result.model_type,
        "disclaimer": result.disclaimer,
    }


@router.get("/{result_id}", summary="Get a stored deepfake analysis result")
def get_deepfake_result(result_id: int, db: Session = Depends(get_db), _user=Depends(require_viewer)):
    row = db.query(DeepfakeResult).filter(DeepfakeResult.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deepfake result not found")
    return row

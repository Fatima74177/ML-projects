from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import require_analyst
from app.services import document_service, audit_service
from app.utils.validators import validate_and_read

router = APIRouter()


@router.post("/analyze", summary="Run OCR and field extraction on a document image",
             description="Runs Tesseract OCR (real OCR engine), extracts identity fields via deterministic "
                         "pattern matching, and flags anomalies. Confidence values are always returned; this "
                         "endpoint never claims legal document authenticity.")
async def analyze_document(
    document: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_analyst),
):
    data = await validate_and_read(document, settings.ALLOWED_DOC_EXT)
    try:
        data = document_service.normalize_document_image(data, document.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = document_service.analyze_document(data)
    audit_service.record(db, actor=user.username, action="DOCUMENT_ANALYSIS", result="SUCCESS")
    return {
        "ocr_text": result.ocr_text,
        "extracted_fields": result.extracted_fields,
        "ocr_confidence": result.ocr_confidence,
        "document_score": result.document_score,
        "anomalies": result.anomalies,
        "model_type": result.model_type,
        "file_hash": result.file_hash,
        "quality_score": result.quality_score,
        "note": "OCR/field extraction only -- does not constitute legal verification of document authenticity.",
    }

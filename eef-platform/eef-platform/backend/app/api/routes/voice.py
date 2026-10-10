from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import require_analyst, require_viewer
from app.models._all import VoiceResult
from app.services import voice_service, audit_service, alert_service
from app.utils.validators import validate_and_read

router = APIRouter()


@router.post("/analyze", summary="Analyze an audio clip for voice authentication signals",
             description="Computes real waveform statistics (duration, sample rate, RMS energy, clipping, "
                         "silence ratio) and a prototype speaker-consistency score. Transcript is a labeled "
                         "DEMO_SIMULATION placeholder pending a production STT integration (e.g. Whisper). "
                         "Accepts WAV (PCM) reliably; MP3/M4A are accepted for upload but not decoded in this "
                         "prototype.")
async def analyze_voice(
    identity_id: int | None = None,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_analyst),
):
    data = await validate_and_read(audio, settings.ALLOWED_AUDIO_EXT)
    result = voice_service.analyze_voice(data)

    row = VoiceResult(
        identity_id=identity_id, duration_seconds=result.duration_seconds, sample_rate=result.sample_rate,
        transcript=result.transcript, speaker_score=result.speaker_score, audio_quality=result.audio_quality,
        risk_indicators=result.risk_indicators, decision=result.decision, model_type=result.model_type,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_service.record(db, actor=user.username, action="VOICE_ANALYSIS", result="SUCCESS")

    if result.decision == "REVIEW_REQUIRED" and result.speaker_score < 0.4:
        alert_service.create_alert(db, "VOICE_CLONE_SUSPECTED", "MEDIUM", identity_id,
                                    "Voice analysis returned low speaker-consistency score.",
                                    {"voice_result_id": row.id, "speaker_score": result.speaker_score})

    return {
        "id": row.id,
        "duration_seconds": result.duration_seconds,
        "sample_rate": result.sample_rate,
        "transcript": result.transcript,
        "transcript_model_type": result.transcript_model_type,
        "speaker_score": result.speaker_score,
        "audio_quality": result.audio_quality,
        "risk_indicators": result.risk_indicators,
        "decision": result.decision,
        "model_type": result.model_type,
    }


@router.get("/{result_id}", summary="Get a stored voice analysis result")
def get_voice_result(result_id: int, db: Session = Depends(get_db), _user=Depends(require_viewer)):
    row = db.query(VoiceResult).filter(VoiceResult.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Voice result not found")
    return row

from fastapi import APIRouter, Depends
from app.core.config import settings
from app.core.security import require_viewer

router = APIRouter()

MODEL_REGISTRY = [
    {"component": "Document OCR", "model_name": "Tesseract OCR", "model_version": "5.3.4",
     "model_type": "REAL_MODEL", "device": settings.MODEL_DEVICE, "status": "healthy",
     "notes": "Real open-source OCR engine. Field extraction on top of OCR text is a deterministic heuristic."},
    {"component": "Face Matching", "model_name": "OpenCV Haar + HOG cosine similarity", "model_version": "opencv-4.13",
     "model_type": "HEURISTIC", "device": settings.MODEL_DEVICE, "status": "healthy",
     "notes": "Prototype embedding. InsightFace/ArcFace integration point documented in app/services/face_service.py."},
    {"component": "Liveness (active/passive)", "model_name": "OpenCV motion/texture heuristics", "model_version": "n/a",
     "model_type": "HEURISTIC", "device": settings.MODEL_DEVICE, "status": "healthy",
     "notes": "Prototype liveness detection -- not a certified liveness result."},
    {"component": "Deepfake Detection (image/video)", "model_name": "FFT/boundary/compression forensic heuristics",
     "model_version": "n/a", "model_type": "HEURISTIC", "device": settings.MODEL_DEVICE, "status": "healthy",
     "notes": "AI prototype result -- requires human review."},
    {"component": "Voice signal analysis", "model_name": "Waveform DSP (wave + numpy)", "model_version": "n/a",
     "model_type": "REAL_MODEL", "device": settings.MODEL_DEVICE, "status": "healthy",
     "notes": "Real DSP on raw audio. Transcript is DEMO_SIMULATION pending a production STT integration."},
    {"component": "Trust Scoring", "model_name": "Configurable weighted formula", "model_version": "1.0",
     "model_type": "REAL_MODEL", "device": "cpu", "status": "healthy",
     "notes": "Deterministic, fully transparent -- see app/services/trust_service.py and app/core/config.py."},
    {"component": "Fraud Intelligence", "model_name": "SQL aggregation signal detection", "model_version": "1.0",
     "model_type": "REAL_MODEL", "device": "cpu", "status": "healthy", "notes": "Real queries, no simulation."},
    {"component": "Knowledge Graph", "model_name": "NetworkX in-process graph", "model_version": "3.6",
     "model_type": "REAL_MODEL", "device": "cpu", "status": "healthy",
     "notes": "Neo4j-ready; enable NEO4J_ENABLED to switch to Neo4j-backed traversal."},
    {"component": "AI Identity Copilot", "model_name": "Tool-grounded template composer", "model_version": "1.0",
     "model_type": "DEMO_SIMULATION", "device": "cpu", "status": "healthy",
     "notes": "Set LLM_PROVIDER=anthropic + LLM_API_KEY to have an LLM phrase answers from the same grounded tool output."},
]


@router.get("/status", summary="Report the status and honesty-label of every AI component in the platform")
def models_status(_user=Depends(require_viewer)):
    return {"models": MODEL_REGISTRY}

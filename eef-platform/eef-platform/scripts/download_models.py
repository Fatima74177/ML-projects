"""
download_models.py -- documents and attempts to fetch the optional heavyweight
AI models this platform is designed to swap in (Section 57/3B: AI MODE).

By default the platform runs entirely on REAL_MODEL (Tesseract OCR, real DSP,
real SQL/graph algorithms) and HEURISTIC/DEMO_SIMULATION components that need
no external downloads (see README's "Model Honesty & Limitations"). This
script is for operators who want to upgrade specific components to trained
neural models when running in an environment with internet access to model
hosts (this is NOT guaranteed in every deployment/sandbox).

Usage:
    python3 scripts/download_models.py --list
    python3 scripts/download_models.py --component face
"""
import argparse
import shutil
import subprocess
import sys

COMPONENTS = {
    "face": {
        "package": "insightface",
        "swap_point": "backend/app/services/face_service.py (HeuristicFaceEngine -> a new InsightFaceEngine)",
        "note": "Requires the `insightface` pip package plus its ONNX model weights "
                "(downloaded automatically by the library on first use, from a model zoo "
                "that must be reachable from this host).",
    },
    "deepfake": {
        "package": "N/A -- no single canonical pretrained checkpoint ships with a pip package",
        "swap_point": "backend/app/services/deepfake_service.py",
        "note": "Would require sourcing a FaceForensics++ or Celeb-DF trained classifier "
                "checkpoint (e.g. a fine-tuned Xception/EfficientNet) from a model hub and "
                "loading it with `torch`/`timm`. Not automated here since no single "
                "canonical public checkpoint is bundled with a pip install.",
    },
    "voice_stt": {
        "package": "openai-whisper",
        "swap_point": "backend/app/services/voice_service.py (transcribe())",
        "note": "`pip install openai-whisper` then `whisper.load_model('base')` -- the "
                "model checkpoint is downloaded from OpenAI's public blob storage on "
                "first use.",
    },
    "document_ocr": {
        "package": "paddleocr",
        "swap_point": "backend/app/services/document_service.py (run_ocr())",
        "note": "Optional alternative/upgrade to the currently-used Tesseract OCR "
                "(already a real OCR engine, not a placeholder). PaddleOCR downloads its "
                "own detection/recognition model weights on first use.",
    },
}


def list_components():
    print("Optional upgrade components (platform runs fully without these):\n")
    for name, info in COMPONENTS.items():
        print(f"  [{name}]")
        print(f"    package:    {info['package']}")
        print(f"    swap point: {info['swap_point']}")
        print(f"    note:       {info['note']}\n")


def attempt_install(component: str):
    info = COMPONENTS.get(component)
    if not info:
        print(f"Unknown component '{component}'. Use --list to see options.")
        sys.exit(1)
    pkg = info["package"]
    if pkg == "N/A -- no single canonical pretrained checkpoint ships with a pip package":
        print(f"[{component}] {info['note']}")
        return
    print(f"[{component}] Attempting: pip install {pkg}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", pkg], check=True)
        print(f"[{component}] Installed. See swap point: {info['swap_point']}")
        print("NOTE: the underlying model *weights* still need to download on first use, "
              "which requires network access to that library's model host at runtime -- "
              "this is environment-dependent and not guaranteed to succeed everywhere "
              "(e.g. offline or network-restricted deployments).")
    except subprocess.CalledProcessError as e:
        print(f"[{component}] pip install failed: {e}")
        print("The platform will continue to run on its HEURISTIC/DEMO_SIMULATION fallback "
              "for this component -- see GET /api/v1/models/status.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optional AI model upgrade helper.")
    parser.add_argument("--list", action="store_true", help="List upgradeable components")
    parser.add_argument("--component", choices=list(COMPONENTS.keys()), help="Attempt to install one component")
    args = parser.parse_args()

    if args.list or not args.component:
        list_components()
    if args.component:
        attempt_install(args.component)

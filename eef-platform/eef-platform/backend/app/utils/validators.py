"""File security & validation helpers (Section 28)."""
from __future__ import annotations
import os
import uuid
from fastapi import HTTPException, UploadFile

from app.core.config import settings

MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"RIFF": "webp_or_wav",  # disambiguated further below
    b"BM": "bmp",
    b"\x00\x00\x00": "mp4_family",  # ftyp box variants
    b"ID3": "mp3",
    b"\xff\xfb": "mp3",
}


def _ext(filename: str) -> str:
    return (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()


async def validate_and_read(file: UploadFile, allowed_ext: list[str], max_size: int | None = None) -> bytes:
    """Reads an uploaded file into memory after validating extension, size, and a magic-byte sniff."""
    max_size = max_size or settings.MAX_UPLOAD_SIZE
    ext = _ext(file.filename or "")
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension '.{ext}'. Allowed: {allowed_ext}")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > max_size:
        raise HTTPException(status_code=400, detail=f"File exceeds max upload size of {max_size} bytes.")

    # Lightweight magic-byte sniff; filenames are never trusted alone.
    header = data[:12]
    plausible = any(header.startswith(sig) for sig in MAGIC_BYTES) or ext in ("mp4", "mov", "avi", "webm", "m4a", "pdf")
    if not plausible:
        raise HTTPException(status_code=400, detail="File content does not match a recognized format signature.")

    return data


def secure_filename(original: str) -> str:
    """Never trust the client-provided filename -- generate an internal one, keeping only the extension."""
    ext = _ext(original)
    return f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex


def save_upload(data: bytes, original_filename: str, subdir: str = "") -> str:
    directory = os.path.join(settings.UPLOAD_DIRECTORY, subdir)
    os.makedirs(directory, exist_ok=True)
    fname = secure_filename(original_filename)
    path = os.path.join(directory, fname)
    with open(path, "wb") as f:
        f.write(data)
    return path

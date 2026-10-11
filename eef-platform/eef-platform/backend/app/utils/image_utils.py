"""Shared image helpers built on OpenCV + numpy (no external network calls)."""
from __future__ import annotations
import hashlib
import io
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps

_FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
MAX_IMAGE_SIDE = 2000


def bytes_to_cv2(data: bytes) -> np.ndarray:
    """Decode and bound image dimensions before OpenCV processing."""
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE), Image.Resampling.LANCZOS)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_faces(img_bgr: np.ndarray) -> List[Tuple[int, int, int, int]]:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    return [tuple(f) for f in faces]


def crop_largest_face(img_bgr: np.ndarray) -> np.ndarray | None:
    faces = detect_faces(img_bgr)
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return img_bgr[y:y + h, x:x + w]


def image_quality_score(img_bgr: np.ndarray) -> float:
    """
    Deterministic prototype quality metric combining sharpness (Laplacian
    variance), brightness, and resolution. Returns 0..1.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_norm = min(sharpness / 500.0, 1.0)

    brightness = float(np.mean(gray))
    brightness_norm = 1.0 - min(abs(brightness - 128) / 128.0, 1.0)

    h, w = gray.shape[:2]
    res_norm = min((h * w) / (640 * 480), 1.0)

    score = 0.5 * sharpness_norm + 0.3 * brightness_norm + 0.2 * res_norm
    return round(float(max(0.0, min(1.0, score))), 4)


def face_embedding_heuristic(face_bgr: np.ndarray) -> np.ndarray:
    """
    PROTOTYPE embedding: a normalized HOG-like descriptor built from a resized,
    histogram-equalized grayscale crop. This is NOT a deep-learning face
    embedding (e.g. ArcFace/InsightFace); it is a deterministic, explainable
    baseline used when no GPU-hosted embedding model is available offline.
    Labeled ModelType.HEURISTIC everywhere it is used.
    """
    gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (96, 96))
    gray = cv2.equalizeHist(gray)
    hog = cv2.HOGDescriptor((96, 96), (16, 16), (8, 8), (8, 8), 9)
    vec = hog.compute(gray).flatten()
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0 or a.shape != b.shape:
        return 0.0
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.clip(np.dot(a, b) / denom, -1.0, 1.0))

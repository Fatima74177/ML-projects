"""
Deepfake Detection (Section 11 & 12).

PROTOTYPE LABELING: no deep deepfake-classifier network (e.g. a
Xception/EfficientNet fine-tuned on FaceForensics++) is bundled -- those
checkpoints are not fetchable from this offline environment. Instead this
service computes real, measurable forensic signals and combines them into an
explainable probability:
  - frequency-domain (FFT) high-frequency energy irregularity, a documented
    GAN-artifact indicator in deepfake-forensics literature
  - face-boundary blending discontinuity (edge-gradient jump at the face mask
    border, a common face-swap artifact)
  - block-level compression-noise inconsistency
  - (video) frame-to-frame face-region consistency / temporal jitter
Every result is tagged ModelType.HEURISTIC and the API response always
includes: "AI prototype result -- requires human review."
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

import cv2
import numpy as np

from app.core.config import settings
from app.models._all import ModelType
from app.utils.image_utils import bytes_to_cv2, detect_faces


@dataclass
class DeepfakeResultDTO:
    deepfake_probability: float
    real_probability: float
    confidence: float
    indicators: List[str]
    frame_results: List[dict]
    metadata: dict
    model_type: str = ModelType.HEURISTIC.value
    disclaimer: str = "AI prototype result -- requires human review."


def _fft_high_freq_ratio(gray: np.ndarray) -> float:
    f = np.fft.fft2(gray.astype(np.float32))
    fshift = np.fft.fftshift(f)
    mag = np.abs(fshift)
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    r = min(h, w) // 6
    low_mask = np.zeros_like(mag)
    cv2.circle(low_mask, (cx, cy), r, 1, -1)
    low_energy = float(np.sum(mag * low_mask))
    total_energy = float(np.sum(mag)) + 1e-6
    high_ratio = 1.0 - (low_energy / total_energy)
    return high_ratio


def _boundary_discontinuity(img_bgr: np.ndarray, box) -> float:
    x, y, w, h = box
    H, W = img_bgr.shape[:2]
    pad = int(0.15 * max(w, h))
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(W, x + w + pad), min(H, y + h + pad)
    region = cv2.cvtColor(img_bgr[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    if region.size == 0:
        return 0.0
    edges = cv2.Canny(region, 60, 140)
    fh, fw = region.shape
    ring_w = max(2, min(fh, fw) // 15)
    ring_mask = np.zeros_like(edges)
    ring_mask[0:ring_w, :] = 1
    ring_mask[-ring_w:, :] = 1
    ring_mask[:, 0:ring_w] = 1
    ring_mask[:, -ring_w:] = 1
    ring_density = float(np.sum((edges > 0) & (ring_mask > 0))) / max(np.sum(ring_mask), 1)
    return min(ring_density * 3.0, 1.0)


def _compression_block_inconsistency(gray: np.ndarray) -> float:
    h, w = gray.shape
    h8, w8 = h - h % 8, w - w % 8
    if h8 < 8 or w8 < 8:
        return 0.0
    g = gray[:h8, :w8].astype(np.float32)
    blocks = g.reshape(h8 // 8, 8, w8 // 8, 8).swapaxes(1, 2).reshape(-1, 8, 8)
    variances = blocks.var(axis=(1, 2))
    if len(variances) < 2:
        return 0.0
    cv_ratio = float(np.std(variances) / (np.mean(variances) + 1e-6))
    return min(cv_ratio / 3.0, 1.0)


def analyze_image(image_bytes: bytes) -> DeepfakeResultDTO:
    img = bytes_to_cv2(image_bytes)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detect_faces(img)
    indicators = []

    high_freq = _fft_high_freq_ratio(gray)
    block_incons = _compression_block_inconsistency(gray)
    boundary = _boundary_discontinuity(img, max(faces, key=lambda f: f[2] * f[3])) if faces else 0.0

    if not faces:
        indicators.append("No face detected -- forensic signals computed on full frame (lower confidence).")

    score = 0.4 * high_freq + 0.3 * boundary + 0.3 * block_incons
    deepfake_prob = round(float(np.clip(score, 0.0, 1.0)), 4)
    real_prob = round(1.0 - deepfake_prob, 4)
    confidence = round(0.5 + 0.5 * (1 if faces else 0) * min(1.0, len(faces)), 4)
    confidence = min(confidence, 0.85)  # prototype methods never claim high confidence

    if high_freq > 0.55:
        indicators.append("Elevated high-frequency spectral energy (possible GAN upsampling artifact).")
    if boundary > 0.4:
        indicators.append("Inconsistent facial boundary blending detected.")
    if block_incons > 0.4:
        indicators.append("Unusual block-level compression variance across the image.")
    if not indicators:
        indicators.append("No strong forensic anomalies detected in prototype checks.")

    return DeepfakeResultDTO(
        deepfake_probability=deepfake_prob,
        real_probability=real_prob,
        confidence=confidence,
        indicators=indicators,
        frame_results=[],
        metadata={"faces_detected": len(faces), "width": img.shape[1], "height": img.shape[0]},
    )


def analyze_video(video_path: str, max_frames: int = 24) -> DeepfakeResultDTO:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return DeepfakeResultDTO(
            deepfake_probability=0.0, real_probability=0.0, confidence=0.0,
            indicators=["Could not open video file."], frame_results=[], metadata={},
        )

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = (total_frames / fps) if fps else 0.0

    step = max(1, (total_frames // max_frames) if total_frames else 1)
    frame_results = []
    prev_box = None
    frame_idx = 0
    read_count = 0

    while cap.isOpened() and read_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detect_faces(frame)
            high_freq = _fft_high_freq_ratio(gray)
            block_incons = _compression_block_inconsistency(gray)
            boundary = 0.0
            jitter = 0.0
            box = None
            if faces:
                box = max(faces, key=lambda f: f[2] * f[3])
                boundary = _boundary_discontinuity(frame, box)
                if prev_box:
                    dx = abs((box[0] + box[2] / 2) - (prev_box[0] + prev_box[2] / 2))
                    dsz = abs((box[2] * box[3]) - (prev_box[2] * prev_box[3])) / max(prev_box[2] * prev_box[3], 1)
                    jitter = min((dx / max(frame.shape[1], 1)) * 5 + dsz, 1.0)
                prev_box = box

            frame_score = round(0.35 * high_freq + 0.3 * boundary + 0.2 * block_incons + 0.15 * jitter, 4)
            anomalies = []
            if boundary > 0.4:
                anomalies.append("boundary_artifact")
            if jitter > 0.35:
                anomalies.append("temporal_jitter")
            if block_incons > 0.4:
                anomalies.append("compression_inconsistency")

            frame_results.append({
                "frame_number": frame_idx,
                "timestamp": round(frame_idx / fps, 3) if fps else None,
                "score": frame_score,
                "detected_faces": len(faces),
                "anomalies": anomalies,
            })
            read_count += 1
        frame_idx += 1

    cap.release()

    if not frame_results:
        return DeepfakeResultDTO(
            deepfake_probability=0.0, real_probability=1.0, confidence=0.0,
            indicators=["No frames could be sampled from the video."], frame_results=[],
            metadata={"fps": fps, "duration_seconds": duration, "total_frames": total_frames},
        )

    scores = [f["score"] for f in frame_results]
    avg_score = float(np.mean(scores))
    volatility = float(np.std(scores))
    deepfake_prob = round(float(np.clip(avg_score + 0.2 * volatility, 0.0, 1.0)), 4)

    indicators = []
    face_frames = sum(1 for f in frame_results if f["detected_faces"] > 0)
    if face_frames < len(frame_results) * 0.5:
        indicators.append("Face detected in fewer than half of sampled frames -- inconsistent face presence.")
    boundary_hits = sum(1 for f in frame_results if "boundary_artifact" in f["anomalies"])
    if boundary_hits > len(frame_results) * 0.3:
        indicators.append("Repeated facial boundary inconsistencies across frames.")
    jitter_hits = sum(1 for f in frame_results if "temporal_jitter" in f["anomalies"])
    if jitter_hits > len(frame_results) * 0.3:
        indicators.append("Elevated temporal face-position jitter (possible frame-level inconsistency).")
    if volatility > 0.2:
        indicators.append("High frame-to-frame score volatility -- inconsistent embeddings across frames.")
    if not indicators:
        indicators.append("No strong forensic anomalies detected across sampled frames in prototype checks.")

    return DeepfakeResultDTO(
        deepfake_probability=deepfake_prob,
        real_probability=round(1 - deepfake_prob, 4),
        confidence=round(min(0.5 + 0.3 * (face_frames / len(frame_results)), 0.85), 4),
        indicators=indicators,
        frame_results=frame_results,
        metadata={"fps": fps, "duration_seconds": round(duration, 2), "total_frames": total_frames,
                  "sampled_frames": len(frame_results)},
    )

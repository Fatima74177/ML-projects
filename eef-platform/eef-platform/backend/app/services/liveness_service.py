"""
Liveness / anti-spoofing (Sections 9 & 10).

PROTOTYPE LABELING: there is no certified liveness model bundled here. Both
the active-challenge verifier and the passive spoof detector are deterministic,
explainable heuristics over OpenCV signal (frame-to-frame motion via face
bounding-box displacement as a stand-in for blink/turn detection, and texture/
frequency statistics for passive spoof cues). Everything returned is tagged
ModelType.HEURISTIC and the API always surfaces
"Prototype liveness detection -- not a certified liveness result."
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List

import cv2
import numpy as np

from app.core.config import settings
from app.models._all import ModelType
from app.utils.image_utils import detect_faces, bytes_to_cv2

CHALLENGE_ACTIONS = ["blink", "turn_left", "turn_right", "smile"]


def generate_challenge(n: int = 3) -> List[str]:
    return random.sample(CHALLENGE_ACTIONS, k=min(n, len(CHALLENGE_ACTIONS)))


@dataclass
class LivenessResultDTO:
    liveness_score: float
    challenge: List[str]
    completed_steps: List[str]
    spoof_indicators: List[str]
    mode: str
    model_type: str = ModelType.HEURISTIC.value
    note: str = "Prototype liveness detection -- not a certified liveness result."


def verify_active_liveness(challenge: List[str], frames: List[bytes]) -> LivenessResultDTO:
    """
    Prototype active-liveness verifier. Since we don't have a landmark model
    bundled offline, "completion" of a step is approximated from measurable
    face bounding-box movement/size-change between consecutive frames -- a
    real, if coarse, motion signal (not a hardcoded pass).
    """
    completed = []
    spoof_indicators = []
    boxes = []
    for fb in frames:
        img = bytes_to_cv2(fb)
        faces = detect_faces(img)
        if faces:
            boxes.append(max(faces, key=lambda f: f[2] * f[3]))
        else:
            boxes.append(None)

    if any(b is None for b in boxes):
        spoof_indicators.append("Face not detected in one or more challenge frames.")

    movements = []
    for i in range(1, len(boxes)):
        if boxes[i] and boxes[i - 1]:
            x1, y1, w1, h1 = boxes[i - 1]
            x2, y2, w2, h2 = boxes[i]
            dx = abs((x2 + w2 / 2) - (x1 + w1 / 2))
            dscale = abs((w2 * h2) - (w1 * h1)) / max(w1 * h1, 1)
            movements.append((dx, dscale))

    # Distribute observed motion across the requested challenge steps.
    for idx, step in enumerate(challenge):
        if idx < len(movements):
            dx, dscale = movements[idx]
            moved = dx > 4 or dscale > 0.03
            if moved:
                completed.append(step)

    if not movements:
        spoof_indicators.append("Insufficient frames to assess motion between challenge steps.")

    liveness_score = round(len(completed) / max(len(challenge), 1), 4)
    if liveness_score < settings.LIVENESS_PASS_THRESHOLD:
        spoof_indicators.append(
            f"Completed {len(completed)}/{len(challenge)} challenge steps -- below pass threshold "
            f"{settings.LIVENESS_PASS_THRESHOLD}."
        )

    return LivenessResultDTO(
        liveness_score=liveness_score, challenge=challenge, completed_steps=completed,
        spoof_indicators=spoof_indicators, mode="ACTIVE",
    )


def verify_passive_liveness(image_bytes: bytes) -> LivenessResultDTO:
    """
    Prototype passive anti-spoof heuristic. Analyzes texture high-frequency
    energy, edge-artifact ratio near the face boundary, and flat-lighting
    variance -- all measurable signals often associated with screen replay /
    printed-photo spoofing, combined into a single explainable score.
    """
    img = bytes_to_cv2(image_bytes)
    faces = detect_faces(img)
    indicators = []
    if not faces:
        return LivenessResultDTO(
            liveness_score=0.0, challenge=[], completed_steps=[],
            spoof_indicators=["No face detected."], mode="PASSIVE",
        )

    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face = img[y:y + h, x:x + w]
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

    # High-frequency texture energy (screens/prints often show moire/aliasing)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    texture_score = min(laplacian_var / 400.0, 1.0)

    # Lighting flatness: real faces usually show some gradient; flat lighting
    # can indicate a flat printed/photo surface.
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_mean = float(np.mean(np.sqrt(grad_x ** 2 + grad_y ** 2)))
    lighting_score = min(gradient_mean / 40.0, 1.0)

    # Edge-artifact ratio around the crop boundary (screen bezels / photo edges)
    edges = cv2.Canny(gray, 80, 160)
    border_thickness = max(2, min(w, h) // 20)
    border_mask = np.zeros_like(edges)
    border_mask[:border_thickness, :] = 1
    border_mask[-border_thickness:, :] = 1
    border_mask[:, :border_thickness] = 1
    border_mask[:, -border_thickness:] = 1
    border_edge_ratio = float(np.sum((edges > 0) & (border_mask > 0))) / max(np.sum(border_mask), 1)
    boundary_score = 1.0 - min(border_edge_ratio * 4, 1.0)

    liveness_score = round(0.4 * texture_score + 0.35 * lighting_score + 0.25 * boundary_score, 4)

    if texture_score < 0.25:
        indicators.append("Low high-frequency texture detail -- possible screen/print replay.")
    if lighting_score < 0.25:
        indicators.append("Unusually flat lighting gradient across the face region.")
    if boundary_score < 0.5:
        indicators.append("Elevated edge artifacts near face boundary -- possible bezel/frame.")
    if liveness_score < settings.LIVENESS_PASS_THRESHOLD:
        indicators.append(f"Composite passive liveness score {liveness_score} below threshold {settings.LIVENESS_PASS_THRESHOLD}.")

    return LivenessResultDTO(
        liveness_score=liveness_score, challenge=[], completed_steps=[],
        spoof_indicators=indicators, mode="PASSIVE",
    )

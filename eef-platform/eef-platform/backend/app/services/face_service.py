"""
Face detection / embedding / matching (Section 8).

Model note: InsightFace (ArcFace) requires downloading ONNX weights from
hosts unreachable in offline/restricted environments. This service is built
around a pluggable `FaceEngine` interface: `HeuristicFaceEngine` (OpenCV Haar
+ HOG descriptor cosine similarity) ships by default and is always labeled
ModelType.HEURISTIC. Dropping in `insightface.app.FaceAnalysis` behind the
same interface upgrades every caller to ModelType.REAL_MODEL with no API
changes -- see ai/face/README in this module's docstring for the swap point.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from app.core.config import settings
from app.models._all import ModelType
from app.utils.image_utils import (
    detect_faces, crop_largest_face, face_embedding_heuristic,
    cosine_similarity, image_quality_score,
)


@dataclass
class FaceMatchResult:
    similarity_score: float
    match_decision: bool
    faces_detected_reference: int
    faces_detected_comparison: int
    quality_score: float
    threshold_used: float
    model_type: str
    explanation: List[str] = field(default_factory=list)


class FaceEngine:
    """Abstract engine boundary -- swap implementation without touching callers."""
    model_type = ModelType.HEURISTIC.value

    def match(self, reference_bytes: bytes, comparison_bytes: bytes) -> FaceMatchResult:
        raise NotImplementedError


class HeuristicFaceEngine(FaceEngine):
    model_type = ModelType.HEURISTIC.value

    def match(self, reference_bytes: bytes, comparison_bytes: bytes) -> FaceMatchResult:
        from app.utils.image_utils import bytes_to_cv2

        ref_img = bytes_to_cv2(reference_bytes)
        cmp_img = bytes_to_cv2(comparison_bytes)

        ref_faces = detect_faces(ref_img)
        cmp_faces = detect_faces(cmp_img)

        explanation = []
        if not ref_faces or not cmp_faces:
            explanation.append("No face detected in one or both images.")
            return FaceMatchResult(
                similarity_score=0.0, match_decision=False,
                faces_detected_reference=len(ref_faces), faces_detected_comparison=len(cmp_faces),
                quality_score=0.0, threshold_used=settings.FACE_MATCH_THRESHOLD,
                model_type=self.model_type, explanation=explanation,
            )

        ref_crop = crop_largest_face(ref_img)
        cmp_crop = crop_largest_face(cmp_img)
        ref_vec = face_embedding_heuristic(ref_crop)
        cmp_vec = face_embedding_heuristic(cmp_crop)
        similarity = cosine_similarity(ref_vec, cmp_vec)
        # Map cosine [-1,1] -> [0,1] similarity-ish score for readability
        similarity_0_1 = round((similarity + 1) / 2, 4)

        quality = round((image_quality_score(ref_crop) + image_quality_score(cmp_crop)) / 2, 4)
        match = similarity_0_1 >= settings.FACE_MATCH_THRESHOLD

        if len(ref_faces) > 1:
            explanation.append(f"Reference image contains {len(ref_faces)} faces; largest face was used.")
        if len(cmp_faces) > 1:
            explanation.append(f"Comparison image contains {len(cmp_faces)} faces; largest face was used.")
        explanation.append(
            f"Similarity {similarity_0_1:.3f} {'>=' if match else '<'} threshold {settings.FACE_MATCH_THRESHOLD}."
        )
        if quality < 0.4:
            explanation.append("Low image quality detected -- result confidence reduced.")

        return FaceMatchResult(
            similarity_score=similarity_0_1,
            match_decision=match,
            faces_detected_reference=len(ref_faces),
            faces_detected_comparison=len(cmp_faces),
            quality_score=quality,
            threshold_used=settings.FACE_MATCH_THRESHOLD,
            model_type=self.model_type,
            explanation=explanation,
        )


_engine: FaceEngine = HeuristicFaceEngine()


def match_faces(reference_bytes: bytes, comparison_bytes: bytes) -> FaceMatchResult:
    return _engine.match(reference_bytes, comparison_bytes)

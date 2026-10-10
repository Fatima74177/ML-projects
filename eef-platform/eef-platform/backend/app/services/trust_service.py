"""
Trust Scoring Engine (Section 14). Fully transparent weighted formula; all
weights live in app.core.config.settings.TRUST_WEIGHTS and are never hidden.

  trust_score = 100 * (
      identity_score  * w_identity +
      biometric_score * w_biometric +
      liveness_score  * w_liveness +
      document_score  * w_document +
      behavior_score  * w_behavior +
      device_score    * w_device
  ) - risk_penalties

Each *_score input is expected in [0, 1]. risk_penalties are additive point
deductions for concrete negative signals (fraud history, deepfake flags,
face mismatch, low liveness), each independently configurable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from app.core.config import settings
from app.models._all import RiskLevel


@dataclass
class TrustScoreResult:
    trust_score: float
    risk_level: str
    positive_signals: List[str]
    negative_signals: List[str]
    weights_used: dict
    explanation: dict


def risk_level_from_score(score: float) -> str:
    if score >= settings.TRUST_VERIFIED_MIN:
        return RiskLevel.LOW.value
    if score >= settings.TRUST_REVIEW_MIN:
        return RiskLevel.MEDIUM.value if score >= 55 else RiskLevel.HIGH.value
    return RiskLevel.CRITICAL.value


def compute_trust_score(
    identity_score: float,
    biometric_score: float,
    liveness_score: float,
    document_score: float,
    behavior_score: float = 0.7,
    device_score: float = 0.7,
    fraud_signal_count: int = 0,
    deepfake_flag: bool = False,
    face_mismatch: bool = False,
    low_liveness: bool = False,
) -> TrustScoreResult:
    w = settings.TRUST_WEIGHTS
    base = (
        identity_score * w["identity_score"]
        + biometric_score * w["biometric_score"]
        + liveness_score * w["liveness_score"]
        + document_score * w["document_score"]
        + behavior_score * w["behavior_score"]
        + device_score * w["device_score"]
    ) * 100.0

    penalties = 0.0
    negative_signals: List[str] = []
    positive_signals: List[str] = []

    if fraud_signal_count:
        p = fraud_signal_count * settings.TRUST_RISK_PENALTY_PER_FRAUD_SIGNAL
        penalties += p
        negative_signals.append(f"{fraud_signal_count} fraud intelligence signal(s) matched (-{p:.1f}).")
    if deepfake_flag:
        penalties += settings.TRUST_RISK_PENALTY_DEEPFAKE
        negative_signals.append(f"Deepfake indicators present (-{settings.TRUST_RISK_PENALTY_DEEPFAKE}).")
    if face_mismatch:
        penalties += settings.TRUST_RISK_PENALTY_FACE_MISMATCH
        negative_signals.append(f"Face similarity below threshold (-{settings.TRUST_RISK_PENALTY_FACE_MISMATCH}).")
    if low_liveness:
        penalties += settings.TRUST_RISK_PENALTY_LOW_LIVENESS
        negative_signals.append(f"Liveness score below pass threshold (-{settings.TRUST_RISK_PENALTY_LOW_LIVENESS}).")

    if identity_score >= 0.8:
        positive_signals.append("Strong identity data consistency.")
    if biometric_score >= 0.8:
        positive_signals.append("Strong biometric (face) match.")
    if document_score >= 0.8:
        positive_signals.append("High document OCR/consistency confidence.")
    if liveness_score >= 0.8:
        positive_signals.append("High liveness confidence.")
    if fraud_signal_count == 0 and not deepfake_flag:
        positive_signals.append("No fraud intelligence signals matched.")

    final_score = round(max(0.0, min(100.0, base - penalties)), 2)
    risk_level = risk_level_from_score(final_score)

    explanation = {
        "formula": "trust_score = 100*(identity*w1 + biometric*w2 + liveness*w3 + document*w4 + behavior*w5 + device*w6) - penalties",
        "inputs": {
            "identity_score": identity_score, "biometric_score": biometric_score,
            "liveness_score": liveness_score, "document_score": document_score,
            "behavior_score": behavior_score, "device_score": device_score,
        },
        "base_score_before_penalties": round(base, 2),
        "total_penalties": round(penalties, 2),
        "thresholds": {
            "VERIFIED_min": settings.TRUST_VERIFIED_MIN,
            "REVIEW_min": settings.TRUST_REVIEW_MIN,
        },
    }

    return TrustScoreResult(
        trust_score=final_score, risk_level=risk_level,
        positive_signals=positive_signals, negative_signals=negative_signals,
        weights_used=dict(w), explanation=explanation,
    )


def decide_verification_status(trust_score: float, strong_fraud_signal: bool = False) -> str:
    """Decision Engine (Section 52)."""
    if strong_fraud_signal and trust_score < settings.TRUST_VERIFIED_MIN:
        return "REJECTED"
    if trust_score >= settings.TRUST_VERIFIED_MIN:
        return "VERIFIED"
    if trust_score >= settings.TRUST_REVIEW_MIN:
        return "REVIEW_REQUIRED"
    return "REJECTED"

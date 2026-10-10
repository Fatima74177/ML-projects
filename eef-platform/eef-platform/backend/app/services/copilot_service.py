"""
AI Identity Copilot (Section 18).

Architecture: a small tool-based agent. Every "tool" below queries the real
database/graph directly -- nothing is fabricated. If LLM_API_KEY /
LLM_PROVIDER are configured (Anthropic), the tool results are handed to the
model to phrase a natural-language answer *grounded strictly in the tool
output*. With no LLM configured (the default, ModelType.DEMO_SIMULATION),
a deterministic template engine composes the same grounded answer without an
external model call -- so the Copilot always works out of the box.
If a tool returns nothing, the copilot must say so explicitly rather than
guess.
"""
from __future__ import annotations
import re
from typing import Optional
from sqlalchemy.orm import Session

from app.models._all import (
    Identity, VerificationSession, Document, FaceResult, LivenessResult,
    TrustScore, FraudCase, Alert, DeepfakeResult, VoiceResult,
)
from app.services import graph_service


# ---------------------------------------------------------------- Tools ----
def get_user(db: Session, identity_id: int) -> Optional[dict]:
    identity = db.query(Identity).filter(Identity.id == identity_id).first()
    if not identity:
        return None
    return {
        "id": identity.id, "full_name": identity.full_name, "email": identity.email,
        "trust_score": identity.trust_score_cached, "risk_level": identity.risk_level_cached,
    }


def get_verification(db: Session, identity_id: int) -> list[dict]:
    rows = db.query(VerificationSession).filter(VerificationSession.identity_id == identity_id) \
        .order_by(VerificationSession.created_at.desc()).limit(5).all()
    return [{
        "id": r.id, "status": r.status, "trust_score": r.trust_score,
        "identity_match_score": r.identity_match_score, "liveness_score": r.liveness_score,
        "document_score": r.document_score, "fraud_indicators": r.fraud_indicators,
        "explanation": r.explanation, "created_at": str(r.created_at),
    } for r in rows]


def get_document(db: Session, identity_id: int) -> list[dict]:
    rows = db.query(Document).filter(Document.identity_id == identity_id).all()
    return [{"id": d.id, "type": d.document_type, "score": d.document_score,
             "anomalies": d.anomalies, "confidence": d.ocr_confidence} for d in rows]


def get_face_result(db: Session, identity_id: int) -> list[dict]:
    rows = db.query(FaceResult).join(VerificationSession) \
        .filter(VerificationSession.identity_id == identity_id).all()
    return [{"similarity": r.similarity_score, "match": r.match_decision, "quality": r.quality_score} for r in rows]


def get_deepfake_result(db: Session, identity_id: int) -> list[dict]:
    rows = db.query(DeepfakeResult).filter(DeepfakeResult.identity_id == identity_id).all()
    return [{"probability": r.deepfake_probability, "confidence": r.confidence,
             "indicators": r.indicators} for r in rows]


def get_voice_result(db: Session, identity_id: int) -> list[dict]:
    rows = db.query(VoiceResult).filter(VoiceResult.identity_id == identity_id).all()
    return [{"speaker_score": r.speaker_score, "quality": r.audio_quality,
             "risk_indicators": r.risk_indicators, "decision": r.decision} for r in rows]


def get_trust_score(db: Session, identity_id: int) -> Optional[dict]:
    row = db.query(TrustScore).filter(TrustScore.identity_id == identity_id) \
        .order_by(TrustScore.created_at.desc()).first()
    if not row:
        return None
    return {"trust_score": row.trust_score, "risk_level": row.risk_level,
            "positive_signals": row.positive_signals, "negative_signals": row.negative_signals,
            "explanation": row.explanation}


def get_fraud_cases(db: Session, identity_id: int) -> list[dict]:
    rows = db.query(FraudCase).all()
    matched = [fc for fc in rows if identity_id in (fc.related_identities or [])]
    return [{"id": fc.id, "severity": fc.severity, "status": fc.status, "signals": fc.signals} for fc in matched]


def get_alerts(db: Session, identity_id: int) -> list[dict]:
    rows = db.query(Alert).filter(Alert.identity_id == identity_id).order_by(Alert.created_at.desc()).limit(10).all()
    return [{"id": a.id, "type": a.type, "severity": a.severity, "status": a.status,
             "description": a.description} for a in rows]


def query_graph(db: Session, identity_id: int) -> dict:
    return graph_service.get_user_subgraph(db, identity_id)


TOOLS = {
    "get_user": get_user, "get_verification": get_verification, "get_document": get_document,
    "get_face_result": get_face_result, "get_voice_result": get_voice_result,
    "get_deepfake_result": get_deepfake_result, "get_trust_score": get_trust_score,
    "get_fraud_cases": get_fraud_cases, "query_graph": query_graph, "get_alerts": get_alerts,
}


# ------------------------------------------------------------ NL routing ----
def _extract_identity_id(question: str, fallback_id: Optional[int]) -> Optional[int]:
    m = re.search(r"\b(?:user|identity)\s*#?(\d+)\b", question, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return fallback_id


def answer_question(db: Session, question: str, identity_id: Optional[int] = None) -> dict:
    """
    Deterministic template-based answer composer (ModelType.DEMO_SIMULATION
    unless LLM_PROVIDER is configured). Always grounded in real tool calls;
    explicitly states when no evidence exists rather than fabricating.
    """
    q = question.lower()
    iid = _extract_identity_id(question, identity_id)
    citations = []

    if iid is None:
        return {
            "answer": "Please specify which user/identity you're asking about (e.g. 'user 12').",
            "citations": [], "model_type": "DEMO_SIMULATION",
        }

    user = get_user(db, iid)
    if not user:
        return {
            "answer": f"Insufficient evidence in the platform data. No identity with id {iid} was found.",
            "citations": [], "model_type": "DEMO_SIMULATION",
        }
    citations.append({"tool": "get_user", "result": user})

    if any(k in q for k in ["fail", "reject", "why did verification"]):
        vs = get_verification(db, iid)
        citations.append({"tool": "get_verification", "result": vs})
        failed = [v for v in vs if v["status"] in ("REJECTED", "REVIEW_REQUIRED")]
        if not failed:
            return {"answer": f"{user['full_name']} has no failed or flagged verification sessions on record.",
                    "citations": citations, "model_type": "DEMO_SIMULATION"}
        latest = failed[0]
        reasons = latest["explanation"].get("decision_reasoning", []) if latest.get("explanation") else []
        reason_text = " ".join(reasons) if reasons else "No detailed reasoning was recorded for this session."
        return {
            "answer": f"Verification #{latest['id']} for {user['full_name']} resulted in {latest['status']} "
                      f"(trust score {latest['trust_score']}). Reasoning: {reason_text}",
            "citations": citations, "model_type": "DEMO_SIMULATION",
        }

    if "fraud" in q:
        cases = get_fraud_cases(db, iid)
        citations.append({"tool": "get_fraud_cases", "result": cases})
        if not cases:
            return {"answer": f"Insufficient evidence in the platform data. No fraud cases are linked to {user['full_name']}.",
                    "citations": citations, "model_type": "DEMO_SIMULATION"}
        parts = [f"Case #{c['id']} ({c['severity']}, {c['status']}): signals={', '.join(c['signals'])}" for c in cases]
        return {"answer": f"{user['full_name']} is linked to {len(cases)} fraud case(s). " + " | ".join(parts),
                "citations": citations, "model_type": "DEMO_SIMULATION"}

    if "device" in q:
        graph = query_graph(db, iid)
        citations.append({"tool": "query_graph", "result": graph})
        device_nodes = [n for n in graph["nodes"] if n.get("type") == "Device"]
        if not device_nodes:
            return {"answer": f"Insufficient evidence in the platform data. No connected devices were found for {user['full_name']}.",
                    "citations": citations, "model_type": "DEMO_SIMULATION"}
        return {"answer": f"{user['full_name']} is connected to {len(device_nodes)} device(s): " +
                           ", ".join(d.get("label", d["id"]) for d in device_nodes),
                "citations": citations, "model_type": "DEMO_SIMULATION"}

    if "high risk" in q or "risk" in q:
        ts = get_trust_score(db, iid)
        citations.append({"tool": "get_trust_score", "result": ts})
        if not ts:
            return {"answer": "Insufficient evidence in the platform data. No trust score has been computed yet.",
                    "citations": citations, "model_type": "DEMO_SIMULATION"}
        negs = "; ".join(ts["negative_signals"]) if ts["negative_signals"] else "no specific negative signals recorded"
        return {"answer": f"{user['full_name']} has risk level {ts['risk_level']} (trust score {ts['trust_score']}). "
                           f"Contributing negative signals: {negs}.",
                "citations": citations, "model_type": "DEMO_SIMULATION"}

    if "deepfake" in q:
        dfs = get_deepfake_result(db, iid)
        citations.append({"tool": "get_deepfake_result", "result": dfs})
        if not dfs:
            return {"answer": "Insufficient evidence in the platform data. No deepfake analysis has been run for this identity.",
                    "citations": citations, "model_type": "DEMO_SIMULATION"}
        latest = dfs[-1]
        return {"answer": f"Latest deepfake analysis probability: {latest['probability']} "
                           f"(confidence {latest['confidence']}). Indicators: {', '.join(latest['indicators'])}. "
                           f"AI prototype result -- requires human review.",
                "citations": citations, "model_type": "DEMO_SIMULATION"}

    if "summar" in q:
        vs = get_verification(db, iid)
        ts = get_trust_score(db, iid)
        alerts = get_alerts(db, iid)
        citations += [{"tool": "get_verification", "result": vs}, {"tool": "get_trust_score", "result": ts},
                      {"tool": "get_alerts", "result": alerts}]
        return {
            "answer": (f"{user['full_name']}: {len(vs)} verification session(s) on record, "
                       f"current trust score {user['trust_score']} ({user['risk_level']} risk), "
                       f"{len(alerts)} alert(s) on file."),
            "citations": citations, "model_type": "DEMO_SIMULATION",
        }

    # default: general profile answer
    ts = get_trust_score(db, iid)
    citations.append({"tool": "get_trust_score", "result": ts})
    return {
        "answer": f"{user['full_name']} currently has trust score {user['trust_score']} and risk level "
                  f"{user['risk_level']}. Ask about 'verification', 'fraud', 'devices', 'deepfake', or 'summarize' "
                  f"for more specific evidence-backed detail.",
        "citations": citations, "model_type": "DEMO_SIMULATION",
    }

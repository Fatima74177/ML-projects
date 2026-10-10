"""Audit Logging (Section 24). Append-only writes; no update/delete API exposed."""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from app.models._all import AuditLog


def record(db: Session, actor: str, action: str, resource: str = "", result: str = "SUCCESS",
           ip: str = "", meta: Optional[dict] = None) -> AuditLog:
    entry = AuditLog(actor=actor, action=action, resource=resource, result=result, ip=ip, meta=meta or {})
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_logs(db: Session, action: Optional[str] = None, actor: Optional[str] = None, limit: int = 200):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if actor:
        q = q.filter(AuditLog.actor == actor)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()

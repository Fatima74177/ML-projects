"""Alert Center (Section 20)."""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from app.models._all import Alert, AlertStatus


def create_alert(db: Session, type_: str, severity: str, identity_id: Optional[int],
                  description: str, evidence: dict) -> Alert:
    alert = Alert(
        type=type_, severity=severity, identity_id=identity_id,
        description=description, evidence=evidence, status=AlertStatus.OPEN.value,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts(db: Session, status: Optional[str] = None, severity: Optional[str] = None,
                 type_: Optional[str] = None, limit: int = 100):
    q = db.query(Alert)
    if status:
        q = q.filter(Alert.status == status)
    if severity:
        q = q.filter(Alert.severity == severity)
    if type_:
        q = q.filter(Alert.type == type_)
    return q.order_by(Alert.created_at.desc()).limit(limit).all()


def update_alert_status(db: Session, alert_id: int, status: str) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    alert.status = status
    db.commit()
    db.refresh(alert)
    return alert

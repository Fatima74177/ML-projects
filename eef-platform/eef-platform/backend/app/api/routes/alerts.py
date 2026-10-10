from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_analyst, require_viewer
from app.services import alert_service

router = APIRouter()


@router.get("", summary="List alerts with optional filters",
            description="Filter by status (OPEN/INVESTIGATING/RESOLVED/FALSE_POSITIVE), severity, or type.")
def list_alerts(status: str | None = None, severity: str | None = None, type: str | None = None,
                 limit: int = 100, db: Session = Depends(get_db), _user=Depends(require_viewer)):
    return alert_service.list_alerts(db, status=status, severity=severity, type_=type, limit=limit)


class StatusUpdate(BaseModel):
    status: str


@router.patch("/{alert_id}/status", summary="Update an alert's status",
              description="Valid transitions: OPEN -> INVESTIGATING -> RESOLVED or FALSE_POSITIVE.")
def update_alert(alert_id: int, payload: StatusUpdate, db: Session = Depends(get_db), _user=Depends(require_analyst)):
    if payload.status not in ("OPEN", "INVESTIGATING", "RESOLVED", "FALSE_POSITIVE"):
        raise HTTPException(status_code=422, detail="Invalid status value")
    alert = alert_service.update_alert_status(db, alert_id, payload.status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

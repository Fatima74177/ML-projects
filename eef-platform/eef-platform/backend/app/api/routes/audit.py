from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_viewer
from app.services import audit_service

router = APIRouter()


@router.get("", summary="List audit log entries (immutable, read-only)",
            description="Audit logs are append-only; there is no update or delete endpoint in the normal API "
                        "surface, by design.")
def list_logs(action: str | None = None, actor: str | None = None, limit: int = 200,
              db: Session = Depends(get_db), _user=Depends(require_viewer)):
    return audit_service.list_logs(db, action=action, actor=actor, limit=limit)

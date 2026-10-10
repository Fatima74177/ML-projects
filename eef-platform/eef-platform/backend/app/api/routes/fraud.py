from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_analyst, require_viewer
from app.models._all import FraudCase
from app.services import fraud_service

router = APIRouter()


@router.post("/scan", summary="Scan the platform for fraud signals and materialize FraudCase records",
             description="Runs SQL-based detection for shared documents, shared devices, shared IPs, and "
                         "repeated failed verifications, then creates FraudCase rows for each match found.")
def scan_for_fraud(db: Session = Depends(get_db), _user=Depends(require_analyst)):
    created = fraud_service.build_fraud_cases(db)
    return {"cases_created": len(created), "case_ids": [c.id for c in created]}


@router.get("/cases", summary="List fraud cases")
def list_cases(status: str | None = None, db: Session = Depends(get_db), _user=Depends(require_viewer)):
    q = db.query(FraudCase)
    if status:
        q = q.filter(FraudCase.status == status)
    return q.order_by(FraudCase.created_at.desc()).all()


@router.get("/cases/{case_id}", summary="Get a fraud case by ID")
def get_case(case_id: int, db: Session = Depends(get_db), _user=Depends(require_viewer)):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Fraud case not found")
    return case


class NoteRequest(BaseModel):
    note: str


class StatusRequest(BaseModel):
    status: str


@router.post("/cases/{case_id}/notes", summary="Add an investigation note to a fraud case")
def add_note(case_id: int, payload: NoteRequest, db: Session = Depends(get_db), user=Depends(require_analyst)):
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Fraud case not found")
    notes = list(case.investigation_notes or [])
    notes.append(f"[{user.username}] {payload.note}")
    case.investigation_notes = notes
    db.commit()
    db.refresh(case)
    return case


@router.patch("/cases/{case_id}/status", summary="Update a fraud case's status")
def update_status(case_id: int, payload: StatusRequest, db: Session = Depends(get_db), _user=Depends(require_analyst)):
    if payload.status not in ("OPEN", "INVESTIGATING", "CLOSED"):
        raise HTTPException(status_code=422, detail="status must be OPEN, INVESTIGATING, or CLOSED")
    case = db.query(FraudCase).filter(FraudCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Fraud case not found")
    case.status = payload.status
    db.commit()
    db.refresh(case)
    return case

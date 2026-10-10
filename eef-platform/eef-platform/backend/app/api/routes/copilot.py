from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_analyst
from app.services import copilot_service, audit_service

router = APIRouter()


class CopilotQuery(BaseModel):
    question: str
    identity_id: int | None = None


@router.post("/ask", summary="Ask the AI Identity Copilot a question about platform data",
             description="Tool-based assistant grounded strictly in real database/graph queries. Never fabricates "
                         "records -- if evidence is missing it says so explicitly. Example questions: 'Why did "
                         "verification fail?', 'Explain the fraud indicators for user 5', 'Show connected devices "
                         "for user 5'.")
def ask_copilot(payload: CopilotQuery, db: Session = Depends(get_db), user=Depends(require_analyst)):
    result = copilot_service.answer_question(db, payload.question, payload.identity_id)
    audit_service.record(db, actor=user.username, action="COPILOT_QUERY", result="SUCCESS",
                          meta={"question": payload.question})
    return result

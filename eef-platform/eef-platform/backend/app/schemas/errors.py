from pydantic import BaseModel
from typing import Any, Optional


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict[str, Any]] = None

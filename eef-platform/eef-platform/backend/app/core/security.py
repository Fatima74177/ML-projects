"""
Authentication & authorization primitives (Section 5, 29).
- Passwords: bcrypt (via the `bcrypt` library directly - never plaintext).
- Sessions: stateless JWT (HS256), secret pulled from environment.
- RBAC: ADMIN / ANALYST / VIEWER, enforced with FastAPI dependencies.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def hash_password(plain: str) -> str:
    # bcrypt has a 72-byte input limit; truncate defensively & deterministically.
    return bcrypt.hashpw(plain.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, role: str, user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "uid": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.models.user import User  # local import to avoid circular import

    payload = decode_token(token)
    user_id = payload.get("uid")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


class RequireRole:
    """Dependency factory for RBAC: RequireRole('ADMIN', 'ANALYST')."""

    def __init__(self, *roles: str):
        self.roles = set(roles)

    def __call__(self, user=Depends(get_current_user)):
        if user.role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not permitted to perform this action. Requires one of: {sorted(self.roles)}",
            )
        return user


require_admin = RequireRole("ADMIN")
require_analyst = RequireRole("ADMIN", "ANALYST")
require_viewer = RequireRole("ADMIN", "ANALYST", "VIEWER")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, require_admin, get_current_user
from app.models._all import User
from app.schemas.auth import UserCreateRequest, UserOut

router = APIRouter()


@router.post("", response_model=UserOut, summary="Create a platform user (ADMIN only)",
             description="Creates a new login user with a bcrypt-hashed password and an RBAC role.")
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    if payload.role not in ("ADMIN", "ANALYST", "VIEWER"):
        raise HTTPException(status_code=422, detail="role must be one of ADMIN, ANALYST, VIEWER")
    user = User(username=payload.username, email=payload.email, full_name=payload.full_name,
                hashed_password=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserOut], summary="List platform users",
            description="Requires an authenticated session; any role may list users (read access).")
def list_users(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(User).all()

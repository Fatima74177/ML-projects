from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user
from app.models._all import User
from app.schemas.auth import TokenResponse, UserOut
from app.services import audit_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse,
             summary="Authenticate and receive a JWT access token",
             description="Validates username/password against bcrypt-hashed credentials and returns a signed JWT "
                          "carrying the user's role (ADMIN/ANALYST/VIEWER) for RBAC enforcement.")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        audit_service.record(db, actor=form_data.username, action="LOGIN", result="FAILURE",
                              ip=request.client.host if request.client else "")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    token = create_access_token(subject=user.username, role=user.role, user_id=user.id)
    audit_service.record(db, actor=user.username, action="LOGIN", result="SUCCESS",
                          ip=request.client.host if request.client else "")
    return TokenResponse(access_token=token, role=user.role, user_id=user.id, username=user.username)


@router.post("/logout", summary="Logout (client-side token discard + audit record)",
             description="JWTs are stateless; logout is recorded for audit purposes and the client should discard "
                          "the token. No server-side session is invalidated in this prototype.")
def logout(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    audit_service.record(db, actor=user.username, action="LOGOUT", result="SUCCESS",
                          ip=request.client.host if request.client else "")
    return {"success": True, "message": "Logged out."}


@router.get("/me", response_model=UserOut, summary="Get the current authenticated user's profile")
def me(user: User = Depends(get_current_user)):
    return user

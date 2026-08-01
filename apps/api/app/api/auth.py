from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.auth import AuditLog, User


router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str | None = Field(default=None, max_length=150)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.access_token_cookie,
        value=token,
        httponly=True,
        secure=settings.access_token_secure,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = body.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=email,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
        role="USER",
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="USER_REGISTERED",
            entity_type="USER",
            entity_id=str(user.id),
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email, user.role)
    _set_auth_cookie(response, token)
    return {"user": _user_payload(user), "access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    email = body.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    user.last_login_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_user_id=user.id,
            action="USER_LOGIN",
            entity_type="USER",
            entity_id=str(user.id),
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()

    token = create_access_token(user.id, user.email, user.role)
    _set_auth_cookie(response, token)
    return {"user": _user_payload(user), "access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.access_token_cookie, path="/")
    return {"status": "logged_out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_payload(user)

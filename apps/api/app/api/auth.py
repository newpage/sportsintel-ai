from datetime import datetime, timedelta, timezone

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import clear_login_attempts, consume_login_attempt
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    new_token_family,
    password_needs_rehash,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import AuditLog, RefreshToken, SecurityToken, User

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, max_length=150)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = Field(default=None, min_length=6, max_length=8)


class TokenRequest(BaseModel):
    token: str = Field(min_length=20)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetComplete(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=12, max_length=128)


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_active": user.is_active,
        "email_verified": user.email_verified_at is not None,
        "mfa_enabled": user.mfa_enabled,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "locked_until": user.locked_until,
    }


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


def audit(db: Session, user_id: int | None, action: str, request: Request, details: str | None = None):
    db.add(AuditLog(actor_user_id=user_id, action=action, entity_type="AUTH", entity_id=str(user_id) if user_id else None, details=details, ip_address=client_ip(request)))


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(settings.access_token_cookie, access_token, httponly=True, secure=settings.access_token_secure, samesite="lax", max_age=settings.access_token_expire_minutes * 60, path="/")
    response.set_cookie(settings.refresh_token_cookie, refresh_token, httponly=True, secure=settings.access_token_secure, samesite="lax", max_age=settings.refresh_token_expire_days * 86400, path="/api/v1/auth")


def issue_token_pair(db: Session, user: User, request: Request, family_id: str | None = None) -> tuple[str, str]:
    access = create_access_token(user.id, user.email, user.role, mfa=user.mfa_enabled)
    refresh = generate_opaque_token()
    db.add(RefreshToken(
        user_id=user.id,
        family_id=family_id or new_token_family(),
        token_hash=hash_opaque_token(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        created_ip=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    ))
    return access, refresh


def create_security_token(db: Session, user: User, purpose: str, ttl: timedelta) -> str:
    raw = generate_opaque_token()
    db.add(SecurityToken(user_id=user.id, purpose=purpose, token_hash=hash_opaque_token(raw), expires_at=datetime.now(timezone.utc) + ttl))
    return raw


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, display_name=body.display_name, password_hash=hash_password(body.password), role="USER", is_active=True, password_changed_at=datetime.now(timezone.utc))
    db.add(user); db.flush()
    verification = create_security_token(db, user, "EMAIL_VERIFY", timedelta(hours=settings.email_verification_expire_hours))
    audit(db, user.id, "USER_REGISTERED", request)
    access, refresh = issue_token_pair(db, user, request)
    db.commit(); db.refresh(user)
    set_auth_cookies(response, access, refresh)
    result = {"user": user_payload(user), "verification_required": True}
    if settings.auth_return_tokens_in_response:
        result.update({"access_token": access, "refresh_token": refresh, "email_verification_token": verification, "token_type": "bearer"})
    return result


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower().strip(); ip = client_ip(request)
    attempts, retry_after = consume_login_attempt(email, ip)
    if attempts > settings.login_max_attempts:
        raise HTTPException(status_code=429, detail=f"Too many login attempts. Retry in {retry_after} seconds")
    user = db.scalar(select(User).where(User.email == email))
    now = datetime.now(timezone.utc)
    if user and user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=423, detail="Account is temporarily locked")
    if not user or not verify_password(body.password, user.password_hash):
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= settings.login_max_attempts:
                user.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
            audit(db, user.id, "LOGIN_FAILED", request)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    if user.mfa_enabled:
        if not body.mfa_code or not pyotp.TOTP(user.mfa_secret).verify(body.mfa_code, valid_window=1):
            audit(db, user.id, "MFA_FAILED", request); db.commit()
            raise HTTPException(status_code=401, detail="Valid MFA code required")
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    user.failed_login_count = 0; user.locked_until = None; user.last_login_at = now
    clear_login_attempts(email, ip)
    audit(db, user.id, "USER_LOGIN", request)
    access, refresh = issue_token_pair(db, user, request)
    db.commit()
    set_auth_cookies(response, access, refresh)
    result = {"user": user_payload(user)}
    if settings.auth_return_tokens_in_response:
        result.update({"access_token": access, "refresh_token": refresh, "token_type": "bearer"})
    return result


@router.post("/refresh")
def refresh(request: Request, response: Response, body: TokenRequest | None = None, db: Session = Depends(get_db)):
    raw = (body.token if body else None) or request.cookies.get(settings.refresh_token_cookie)
    if not raw:
        raise HTTPException(status_code=401, detail="Refresh token required")
    token_hash = hash_opaque_token(raw)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)
    if not stored or stored.revoked_at or stored.expires_at <= now:
        if stored:
            db.execute(update(RefreshToken).where(RefreshToken.family_id == stored.family_id, RefreshToken.revoked_at.is_(None)).values(revoked_at=now))
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.get(User, stored.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User unavailable")
    stored.revoked_at = now
    access, new_refresh = issue_token_pair(db, user, request, family_id=stored.family_id)
    stored.replaced_by_hash = hash_opaque_token(new_refresh)
    audit(db, user.id, "TOKEN_REFRESHED", request)
    db.commit(); set_auth_cookies(response, access, new_refresh)
    result = {"status": "refreshed"}
    if settings.auth_return_tokens_in_response:
        result.update({"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"})
    return result


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw = request.cookies.get(settings.refresh_token_cookie)
    if raw:
        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(raw)))
        if stored and not stored.revoked_at:
            stored.revoked_at = datetime.now(timezone.utc); db.commit()
    response.delete_cookie(settings.access_token_cookie, path="/")
    response.delete_cookie(settings.refresh_token_cookie, path="/api/v1/auth")
    return {"status": "logged_out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_payload(user)


@router.post("/email-verification/request")
def request_verification(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.email_verified_at:
        return {"status": "already_verified"}
    token = create_security_token(db, user, "EMAIL_VERIFY", timedelta(hours=settings.email_verification_expire_hours))
    audit(db, user.id, "EMAIL_VERIFICATION_REQUESTED", request); db.commit()
    return {"status": "created", **({"token": token} if settings.auth_return_tokens_in_response else {})}


@router.post("/email-verification/confirm")
def confirm_verification(body: TokenRequest, request: Request, db: Session = Depends(get_db)):
    stored = db.scalar(select(SecurityToken).where(SecurityToken.token_hash == hash_opaque_token(body.token), SecurityToken.purpose == "EMAIL_VERIFY"))
    now = datetime.now(timezone.utc)
    if not stored or stored.used_at or stored.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user = db.get(User, stored.user_id); user.email_verified_at = now; stored.used_at = now
    audit(db, user.id, "EMAIL_VERIFIED", request); db.commit()
    return {"status": "verified"}


@router.post("/password-reset/request")
def request_password_reset(body: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower().strip()))
    token = None
    if user:
        token = create_security_token(db, user, "PASSWORD_RESET", timedelta(minutes=settings.password_reset_expire_minutes))
        audit(db, user.id, "PASSWORD_RESET_REQUESTED", request); db.commit()
    result = {"status": "accepted"}
    if token and settings.auth_return_tokens_in_response:
        result["token"] = token
    return result


@router.post("/password-reset/confirm")
def confirm_password_reset(body: PasswordResetComplete, request: Request, db: Session = Depends(get_db)):
    stored = db.scalar(select(SecurityToken).where(SecurityToken.token_hash == hash_opaque_token(body.token), SecurityToken.purpose == "PASSWORD_RESET"))
    now = datetime.now(timezone.utc)
    if not stored or stored.used_at or stored.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.get(User, stored.user_id)
    user.password_hash = hash_password(body.new_password); user.password_changed_at = now; user.failed_login_count = 0; user.locked_until = None; stored.used_at = now
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).values(revoked_at=now))
    audit(db, user.id, "PASSWORD_RESET_COMPLETED", request); db.commit()
    return {"status": "password_updated"}


@router.post("/mfa/setup")
def mfa_setup(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = pyotp.random_base32(); user.mfa_secret = secret; user.mfa_enabled = False
    audit(db, user.id, "MFA_SETUP_STARTED", request); db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=settings.mfa_issuer)
    return {"secret": secret, "provisioning_uri": uri}


@router.post("/mfa/enable")
def mfa_enable(body: MfaCodeRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    user.mfa_enabled = True; audit(db, user.id, "MFA_ENABLED", request); db.commit()
    return {"status": "enabled"}


@router.post("/mfa/disable")
def mfa_disable(body: MfaCodeRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    user.mfa_enabled = False; user.mfa_secret = None; audit(db, user.id, "MFA_DISABLED", request); db.commit()
    return {"status": "disabled"}

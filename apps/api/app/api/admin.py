from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from redis import Redis
from sqlalchemy import desc, func, select, text
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.config import settings
from app.db.session import get_db
from app.models.audit import ProviderRun
from app.models.auth import AuditLog, User
from app.models.lms import SurvivorPool
from app.models.sports import Game, League, Player, Team


router = APIRouter(prefix="/admin", tags=["administration"])


class RoleUpdate(BaseModel):
    role: str


class ActiveUpdate(BaseModel):
    is_active: bool


@router.get("/overview")
def overview(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))
    redis_ok = False
    try:
        redis_ok = bool(Redis.from_url(settings.redis_url).ping())
    except Exception:
        redis_ok = False

    latest_run = db.scalar(
        select(ProviderRun).order_by(desc(ProviderRun.started_at)).limit(1)
    )

    counts = {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "teams": db.scalar(select(func.count()).select_from(Team)) or 0,
        "players": db.scalar(select(func.count()).select_from(Player)) or 0,
        "games": db.scalar(select(func.count()).select_from(Game)) or 0,
        "lms_pools": db.scalar(select(func.count()).select_from(SurvivorPool)) or 0,
        "provider_runs": db.scalar(select(func.count()).select_from(ProviderRun)) or 0,
    }

    return {
        "status": "healthy" if redis_ok else "degraded",
        "environment": settings.app_env,
        "version": settings.app_version,
        "services": {
            "api": True,
            "database": True,
            "redis": redis_ok,
            "worker": latest_run is not None,
            "scheduler": latest_run is not None,
        },
        "counts": counts,
        "latest_provider_run": None if not latest_run else {
            "id": latest_run.id,
            "provider": latest_run.provider,
            "dataset": latest_run.dataset,
            "status": latest_run.status,
            "records_received": latest_run.records_received,
            "records_written": latest_run.records_written,
            "started_at": latest_run.started_at,
            "completed_at": latest_run.completed_at,
            "error_message": latest_run.error_message,
        },
    }


@router.get("/users")
def users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(User).order_by(desc(User.created_at))).all()
    return [
        {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
        }
        for user in rows
    ]


@router.patch("/users/{user_id}/role")
def update_role(
    user_id: int,
    body: RoleUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    allowed = {"USER", "PREMIUM", "ANALYST", "ADMIN"}
    role = body.role.upper()
    if role not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported role")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = role
    db.add(
        AuditLog(
            actor_user_id=admin.id,
            action="USER_ROLE_CHANGED",
            entity_type="USER",
            entity_id=str(user.id),
            details=f"{old_role} -> {role}",
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()
    return {"id": user.id, "role": user.role}


@router.patch("/users/{user_id}/active")
def update_active(
    user_id: int,
    body: ActiveUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == admin.id and not body.is_active:
        raise HTTPException(status_code=400, detail="You cannot disable your own account")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = body.is_active
    db.add(
        AuditLog(
            actor_user_id=admin.id,
            action="USER_STATUS_CHANGED",
            entity_type="USER",
            entity_id=str(user.id),
            details=f"is_active={body.is_active}",
            ip_address=request.client.host if request.client else None,
        )
    )
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.get("/provider-runs")
def provider_runs(
    limit: int = 50,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 200)
    rows = db.scalars(
        select(ProviderRun).order_by(desc(ProviderRun.started_at)).limit(limit)
    ).all()
    return [
        {
            "id": run.id,
            "provider": run.provider,
            "dataset": run.dataset,
            "status": run.status,
            "records_received": run.records_received,
            "records_written": run.records_written,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "error_message": run.error_message,
        }
        for run in rows
    ]


@router.get("/audit-logs")
def audit_logs(
    limit: int = 100,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 300)
    rows = db.scalars(
        select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "details": row.details,
            "ip_address": row.ip_address,
            "created_at": row.created_at,
        }
        for row in rows
    ]

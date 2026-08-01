from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.auth import AuditLog, User
from app.models.provider import ProviderConfiguration, ProviderExecution
from app.providers import register_builtin_providers
from app.providers.core.lifecycle import execute_provider
from app.providers.core.registry import provider_registry
from app.providers.core.types import DatasetType


router = APIRouter(prefix="/admin/providers", tags=["providers"])
register_builtin_providers()


def configuration_for(
    db: Session,
    provider_code: str,
    default_enabled: bool,
    priority: int,
) -> ProviderConfiguration:
    configuration = db.scalar(
        select(ProviderConfiguration).where(
            ProviderConfiguration.provider_code == provider_code
        )
    )
    if configuration:
        return configuration

    configuration = ProviderConfiguration(
        provider_code=provider_code,
        enabled=default_enabled,
        priority=priority,
        configuration={},
    )
    db.add(configuration)
    db.commit()
    db.refresh(configuration)
    return configuration


@router.get("")
def list_providers(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    result = []
    for provider in provider_registry.all():
        metadata = provider.metadata
        config = configuration_for(
            db,
            metadata.code,
            metadata.enabled_by_default,
            metadata.priority,
        )
        health = provider.health()
        latest = db.scalar(
            select(ProviderExecution)
            .where(ProviderExecution.provider_code == metadata.code)
            .order_by(desc(ProviderExecution.started_at))
            .limit(1)
        )

        result.append(
            {
                "metadata": {
                    **asdict(metadata),
                    "stage": metadata.stage.value,
                    "capabilities": [
                        {
                            **asdict(item),
                            "dataset": item.dataset.value,
                        }
                        for item in metadata.capabilities
                    ],
                },
                "configuration": {
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "configuration": config.configuration,
                },
                "health": {
                    **asdict(health),
                    "status": health.status.value,
                },
                "latest_execution": None if not latest else {
                    "id": latest.id,
                    "dataset": latest.dataset,
                    "status": latest.status,
                    "started_at": latest.started_at,
                    "completed_at": latest.completed_at,
                    "quality_score": latest.quality_score,
                    "confidence_score": latest.confidence_score,
                    "records_received": latest.records_received,
                    "records_inserted": latest.records_inserted,
                    "records_updated": latest.records_updated,
                    "records_rejected": latest.records_rejected,
                },
            }
        )
    return result


@router.post("/{provider_code}/enable")
def enable_provider(
    provider_code: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    provider = provider_registry.get(provider_code)
    config = configuration_for(
        db,
        provider_code,
        provider.metadata.enabled_by_default,
        provider.metadata.priority,
    )
    config.enabled = True
    config.updated_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_user_id=admin.id,
            action="PROVIDER_ENABLED",
            entity_type="PROVIDER",
            entity_id=provider_code,
        )
    )
    db.commit()
    return {"provider_code": provider_code, "enabled": True}


@router.post("/{provider_code}/disable")
def disable_provider(
    provider_code: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    provider = provider_registry.get(provider_code)
    config = configuration_for(
        db,
        provider_code,
        provider.metadata.enabled_by_default,
        provider.metadata.priority,
    )
    config.enabled = False
    config.updated_at = datetime.now(timezone.utc)
    db.add(
        AuditLog(
            actor_user_id=admin.id,
            action="PROVIDER_DISABLED",
            entity_type="PROVIDER",
            entity_id=provider_code,
        )
    )
    db.commit()
    return {"provider_code": provider_code, "enabled": False}


@router.post("/{provider_code}/run/{dataset}")
def run_provider(
    provider_code: str,
    dataset: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    provider = provider_registry.get(provider_code)
    try:
        dataset_type = DatasetType(dataset.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Unknown dataset")

    config = configuration_for(
        db,
        provider_code,
        provider.metadata.enabled_by_default,
        provider.metadata.priority,
    )
    if not config.enabled:
        raise HTTPException(status_code=409, detail="Provider is disabled")

    execution = execute_provider(
        db,
        provider_code,
        dataset_type,
        requested_by_user_id=admin.id,
    )
    db.add(
        AuditLog(
            actor_user_id=admin.id,
            action="PROVIDER_EXECUTED",
            entity_type="PROVIDER_EXECUTION",
            entity_id=str(execution.id),
            details=f"{provider_code}:{dataset_type.value}",
        )
    )
    db.commit()
    return {
        "id": execution.id,
        "provider_code": execution.provider_code,
        "dataset": execution.dataset,
        "status": execution.status,
        "duration_ms": execution.duration_ms,
        "records_received": execution.records_received,
        "records_inserted": execution.records_inserted,
        "records_updated": execution.records_updated,
        "records_rejected": execution.records_rejected,
        "quality_score": execution.quality_score,
        "confidence_score": execution.confidence_score,
        "confidence_reason": execution.confidence_reason,
        "details": execution.details,
        "error_message": execution.error_message,
    }


@router.get("/executions")
def executions(
    limit: int = 100,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(ProviderExecution)
        .order_by(desc(ProviderExecution.started_at))
        .limit(min(max(limit, 1), 300))
    ).all()
    return [
        {
            "id": row.id,
            "provider_code": row.provider_code,
            "dataset": row.dataset,
            "status": row.status,
            "started_at": row.started_at,
            "completed_at": row.completed_at,
            "duration_ms": row.duration_ms,
            "records_received": row.records_received,
            "records_validated": row.records_validated,
            "records_inserted": row.records_inserted,
            "records_updated": row.records_updated,
            "records_rejected": row.records_rejected,
            "quality_score": row.quality_score,
            "confidence_score": row.confidence_score,
            "confidence_reason": row.confidence_reason,
            "warning_count": row.warning_count,
            "error_count": row.error_count,
            "error_message": row.error_message,
            "details": row.details,
        }
        for row in rows
    ]

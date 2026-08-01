from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.models.provider import ProviderExecution
from app.providers.core.quality import calculate_quality
from app.providers.core.registry import provider_registry
from app.providers.core.types import DatasetType, ProviderResult


class ProviderExecutionError(RuntimeError):
    pass


def execute_provider(
    db: Session,
    provider_code: str,
    dataset: DatasetType,
    requested_by_user_id: int | None = None,
    parameters: dict[str, Any] | None = None,
) -> ProviderExecution:
    provider = provider_registry.get(provider_code)
    if not provider.supports(dataset):
        raise ProviderExecutionError(
            f"{provider_code} does not support {dataset.value}"
        )

    execution = ProviderExecution(
        provider_code=provider_code,
        dataset=dataset.value,
        status="RUNNING",
        requested_by_user_id=requested_by_user_id,
        started_at=datetime.now(timezone.utc),
        parameters=parameters or {},
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    started = perf_counter()
    try:
        payload = provider.fetch(dataset, **(parameters or {}))
        issues = provider.validate(dataset, payload)
        errors = [issue for issue in issues if issue.severity.upper() == "ERROR"]
        warnings = [issue for issue in issues if issue.severity.upper() != "ERROR"]
        if errors:
            result = ProviderResult(
                records_received=len(payload) if isinstance(payload, list) else 1,
                records_rejected=len(errors),
                warnings=warnings,
                errors=errors,
                confidence_score=0,
                confidence_reason="Validation errors prevented loading.",
            )
        else:
            records = provider.normalize(dataset, payload)
            result = provider.load(db, dataset, records)
            result.warnings.extend(warnings)

        result.quality_score = calculate_quality(result)
        execution.status = "SUCCESS" if not result.errors else "FAILED"
        execution.records_received = result.records_received
        execution.records_validated = result.records_validated
        execution.records_inserted = result.records_inserted
        execution.records_updated = result.records_updated
        execution.records_rejected = result.records_rejected
        execution.quality_score = result.quality_score
        execution.confidence_score = result.confidence_score
        execution.confidence_reason = result.confidence_reason
        execution.warning_count = len(result.warnings)
        execution.error_count = len(result.errors)
        execution.details = {
            **result.details,
            "warnings": [issue.__dict__ for issue in result.warnings],
            "errors": [issue.__dict__ for issue in result.errors],
        }
        execution.raw_payload_reference = result.raw_payload_reference
    except Exception as exc:
        execution.status = "FAILED"
        execution.error_count = 1
        execution.error_message = str(exc)
        execution.confidence_score = 0
        execution.confidence_reason = "Provider execution failed."
    finally:
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration_ms = round((perf_counter() - started) * 1000, 2)
        db.commit()
        db.refresh(execution)

    return execution

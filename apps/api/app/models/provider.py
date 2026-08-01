from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ProviderConfiguration(Base):
    __tablename__ = "provider_configurations"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ProviderExecution(Base):
    __tablename__ = "provider_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_code: Mapped[str] = mapped_column(String(120), index=True)
    dataset: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[float | None] = mapped_column(Float)
    records_received: Mapped[int] = mapped_column(Integer, default=0)
    records_validated: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    confidence_reason: Mapped[str | None] = mapped_column(Text)
    raw_payload_reference: Mapped[str | None] = mapped_column(String(500))
    error_message: Mapped[str | None] = mapped_column(Text)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ProviderDatasetState(Base):
    __tablename__ = "provider_dataset_states"
    __table_args__ = (
        UniqueConstraint("provider_code", "dataset"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_code: Mapped[str] = mapped_column(String(120), index=True)
    dataset: Mapped[str] = mapped_column(String(50), index=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str | None] = mapped_column(String(30))
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer)

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DatasetType(StrEnum):
    LEAGUE = "LEAGUE"
    SEASON = "SEASON"
    TEAM = "TEAM"
    VENUE = "VENUE"
    PLAYER = "PLAYER"
    COACH = "COACH"
    GAME = "GAME"
    GAME_STATUS = "GAME_STATUS"
    ROSTER = "ROSTER"
    DEPTH_CHART = "DEPTH_CHART"
    INJURY = "INJURY"
    ODDS = "ODDS"
    WEATHER = "WEATHER"
    NEWS = "NEWS"
    OFFICIALS = "OFFICIALS"
    STATISTICS = "STATISTICS"


class HealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    OFFLINE = "OFFLINE"
    DISABLED = "DISABLED"


class ProviderStage(StrEnum):
    EXPERIMENTAL = "EXPERIMENTAL"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True)
class ProviderCapability:
    dataset: DatasetType
    default_schedule_seconds: int | None = None
    description: str | None = None


@dataclass(frozen=True)
class ProviderMetadata:
    code: str
    name: str
    version: str
    stage: ProviderStage
    sports: tuple[str, ...]
    capabilities: tuple[ProviderCapability, ...]
    access_type: str
    license_name: str | None
    attribution_required: bool
    attribution_text: str | None
    commercial_use_allowed: bool | None
    redistribution_allowed: bool | None
    terms_url: str | None
    requires_api_key: bool
    self_hostable: bool
    enabled_by_default: bool = False
    priority: int = 100


@dataclass(frozen=True)
class ProviderValidationIssue:
    code: str
    message: str
    severity: str = "ERROR"
    record_reference: str | None = None


@dataclass
class ProviderHealth:
    status: HealthStatus
    message: str
    latency_ms: float | None = None
    checked_at: str | None = None


@dataclass
class ProviderResult:
    records_received: int = 0
    records_validated: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_rejected: int = 0
    warnings: list[ProviderValidationIssue] = field(default_factory=list)
    errors: list[ProviderValidationIssue] = field(default_factory=list)
    quality_score: float = 0.0
    confidence_score: float = 0.0
    confidence_reason: str | None = None
    raw_payload_reference: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

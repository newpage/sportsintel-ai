from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.providers.core.types import (
    DatasetType,
    ProviderHealth,
    ProviderMetadata,
    ProviderResult,
    ProviderValidationIssue,
)


class BaseProvider(ABC):
    metadata: ProviderMetadata

    def supports(self, dataset: DatasetType) -> bool:
        return any(item.dataset == dataset for item in self.metadata.capabilities)

    @abstractmethod
    def health(self) -> ProviderHealth:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, dataset: DatasetType, **kwargs: Any) -> Any:
        raise NotImplementedError

    def validate(
        self,
        dataset: DatasetType,
        payload: Any,
    ) -> list[ProviderValidationIssue]:
        return []

    def normalize(self, dataset: DatasetType, payload: Any) -> list[dict]:
        if isinstance(payload, list):
            return payload
        return [payload]

    @abstractmethod
    def load(
        self,
        db: Session,
        dataset: DatasetType,
        records: list[dict],
    ) -> ProviderResult:
        raise NotImplementedError

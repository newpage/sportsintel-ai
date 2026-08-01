from collections.abc import Iterable

from app.providers.core.base import BaseProvider
from app.providers.core.types import DatasetType


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        code = provider.metadata.code
        if code in self._providers:
            raise ValueError(f"Provider already registered: {code}")
        self._providers[code] = provider

    def get(self, code: str) -> BaseProvider:
        try:
            return self._providers[code]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {code}") from exc

    def all(self) -> list[BaseProvider]:
        return sorted(
            self._providers.values(),
            key=lambda provider: (
                provider.metadata.priority,
                provider.metadata.code,
            ),
        )

    def for_sport(self, sport: str) -> list[BaseProvider]:
        sport_code = sport.upper()
        return [
            provider
            for provider in self.all()
            if sport_code in {value.upper() for value in provider.metadata.sports}
        ]

    def for_dataset(self, dataset: DatasetType) -> list[BaseProvider]:
        return [provider for provider in self.all() if provider.supports(dataset)]

    def codes(self) -> Iterable[str]:
        return self._providers.keys()


provider_registry = ProviderRegistry()

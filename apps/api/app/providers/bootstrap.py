from app.providers.core.registry import provider_registry
from app.providers.nfl.demo.provider import DemoNFLProvider


_registered = False


def register_builtin_providers() -> None:
    global _registered
    if _registered:
        return
    provider_registry.register(DemoNFLProvider())
    _registered = True

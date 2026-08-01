import time
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def with_retry(
    operation: Callable[[], T],
    attempts: int = 3,
    base_delay_seconds: float = 0.5,
) -> T:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(base_delay_seconds * (2 ** attempt))
    assert last_error is not None
    raise last_error

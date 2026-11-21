"""A megszakítási jelző közös ellenőrzése a webexport ciklusaiban."""

from collections.abc import Callable


def check_cancelled(is_cancelled: Callable[[], bool] | None) -> None:
    """Megszakítási kérésnél állítsa le a webexport aktuális ciklusát."""
    if is_cancelled is not None and is_cancelled():
        raise InterruptedError("web export cancelled")

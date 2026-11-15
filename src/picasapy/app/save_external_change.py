"""A Visszaállítás külső módosítás-vizsgálata és a mentési ujjlenyomat (#6972).

Az eredeti Picasa a Revert előtt megnézi, hogy a fájl a mentés óta kívülről
módosult-e (`CThumbUI::FileRevert::changed1` / `changedX`), és ha igen,
külön figyelmeztet „Revert Anyway" gombbal. A vizsgálat alapja a mentéskor
rögzített ujjlenyomat (`picasapy.edit.saved_fingerprint`); itt csak a
vezérlő oldali kötés van: rögzítés mentés után, elfelejtés Visszaállítás és
Mentés visszavonása után, és a QML-nek szóló lekérdezés.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.edit.saved_fingerprint import (
    STORE_FILENAME,
    changed_outside,
    forget,
    record_saved,
)
from picasapy.halozati_ut import halozati_gyoker

_LOG = logging.getLogger(__name__)


def _helyi(paths: Iterable[Path]) -> list[Path]:
    """Csak a nem hálózati utak: a teljes fájl beolvasása hálózati mappán a
    fő szálat fogná (#6948), ezért ott ujjlenyomat és figyelmeztetés sincs."""
    return [path for path in paths if halozati_gyoker(path) is None]


class SaveExternalChangeMixin:
    """A mentett képek ujjlenyomata és a külső módosítás lekérdezése."""

    def _fingerprint_store(self) -> Path | None:
        """Az adatgyökérben élő tár (az index-SQLite mellett)."""
        db_path = getattr(self, "_db_path", None)
        return None if db_path is None else Path(db_path).parent / STORE_FILENAME

    def _record_saved_fingerprints(self, paths: Iterable[Path]) -> None:
        """A sikeresen mentett képek ujjlenyomata. A mentés nem bukhat rajta."""
        store = self._fingerprint_store()
        paths = _helyi(paths)
        if store is None or not paths:
            return
        try:
            record_saved(store, paths)
        except (OSError, ValueError):
            _LOG.warning("a mentési ujjlenyomatok nem írhatók (#6972)", exc_info=True)

    def _forget_saved_fingerprints(self, paths: Iterable[Path]) -> None:
        """Visszaállítás / Mentés visszavonása után a bejegyzés elavult."""
        store = self._fingerprint_store()
        paths = list(paths)
        if store is None or not paths:
            return
        try:
            forget(store, paths)
        except (OSError, ValueError):
            _LOG.warning("a mentési ujjlenyomatok nem törölhetők (#6972)", exc_info=True)

    @Slot(list, result=int)
    def externallyChangedCount(self, rows) -> int:  # noqa: N802 - QML-stílus
        """Hány kijelölt kép módosult a mentés óta kívülről (0 = egy sem).

        A Revert megerősítése után, még a lemezművelet előtt hívja a felület:
        ha nem nulla, a „changed outside of Picasa" figyelmeztetést mutatja.
        """
        store = self._fingerprint_store()
        if store is None:
            return 0
        paths = _helyi(
            Path(record.folder_path) / record.name
            for record in self._selected_records(rows)
        )
        return sum(1 for path in paths if changed_outside(store, path))

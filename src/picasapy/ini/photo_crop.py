"""A képszekció aktuális `crop=` kulcsának olvasása a közös ini-rétegen át."""

from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from pathlib import Path

from picasapy.ini.document import IniDocument
from picasapy.ini.io import load_or_empty

_log = logging.getLogger(__name__)
_CACHE_CAPACITY = 256
_UNREADABLE_LOCK = threading.Lock()
_UNREADABLE_LOGGED: set[Path] = set()


def log_unreadable_ini_once(path: str | Path, error: OSError) -> None:
    """A hibás ini miatt képenkénti kérések helyett fájlonként egyszer szól."""
    target = Path(path)
    with _UNREADABLE_LOCK:
        if target in _UNREADABLE_LOGGED:
            return
        _UNREADABLE_LOGGED.add(target)
    _log.warning(
        "A forrás .picasa.ini fájlja nem olvasható; a filters= lánc "
        "változatlan marad (%s): %s",
        target,
        error,
    )


class PhotoCropReader:
    """Képenkénti `crop=` olvasó, mappánkénti `.picasa.ini`-cache-sel.

    Az index nem tárolja a crop kulcsot. A gyorsítótár az ini méretét és
    módosítási idejét figyeli, ezért a Picasa vagy a szerkesztő mentése után
    a következő olvasás már a friss dokumentumból dolgozik.
    """

    def __init__(self) -> None:
        self._documents: OrderedDict[
            Path, tuple[tuple[int, int] | None, IniDocument]
        ] = OrderedDict()
        self._lock = threading.Lock()

    def read(self, ini_path: str | Path, section_name: str) -> tuple[str | None, bool]:
        """Visszaadja a crop értékét és az olvashatóságot.

        Hiányzó fájlnál `(None, True)` az eredmény. Olvasási hibánál
        `(None, False)` jön vissza, és naplózza, hogy a hívó a láncra essen
        vissza. Közvetlen fájlolvasást a hívóknak nem kell végezniük.
        """
        target = Path(ini_path)
        with self._lock:
            try:
                info = target.stat()
                signature: tuple[int, int] | None = (info.st_mtime_ns, info.st_size)
            except FileNotFoundError:
                signature = None
            except OSError as error:
                self._log_unreadable(target, error)
                return None, False

            cached = self._documents.get(target)
            if cached is not None and cached[0] == signature:
                document = cached[1]
                self._documents.move_to_end(target)
            else:
                try:
                    document = load_or_empty(target)
                except OSError as error:
                    self._log_unreadable(target, error)
                    return None, False
                self._documents[target] = (signature, document)
                self._documents.move_to_end(target)
                while len(self._documents) > _CACHE_CAPACITY:
                    self._documents.popitem(last=False)

        section = document.section(section_name)
        return (section.get("crop") if section is not None else None), True

    @staticmethod
    def _log_unreadable(path: Path, error: OSError) -> None:
        log_unreadable_ini_once(path, error)

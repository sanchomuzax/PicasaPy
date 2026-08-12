"""Adatbázis-tömörítés — „Compacting" (#449).

Az eredeti Picasa külön ablakban tömörítette az adatbázisát:

    „Picasa is compacting its database to save disk space. This may take
    several minutes."

…állapotsorral és **Mégse** gombbal (`CCompactStatus`, `Always Compact`,
`compactpercentage`). A tanulság nem a konkrét formátum, hanem a
viselkedés: a tömörítés **hosszú**, ezért őszintén meg kell mondani, és
**bármikor megszakíthatónak** kell lennie.

Nálunk ez SQLite `VACUUM`. Három dolgot ad ez a modul:

* `wasted_percent()` — mennyi a szabadlistán heverő, visszanyerhető hely.
  Ez a `compactpercentage` küszöb megfelelője: e fölött érdemes tömöríteni.
* `compact_database()` — a `VACUUM` haladás-jelzéssel és megszakítással.
* `CompactionCancelled` / `CompactionError` — a hívónak (vezérlő) szánt,
  a `picasapy.index.relocate` mintáját követő kivételek.

**Megszakítás:** az SQLite `VACUUM` egyetlen utasítás, félbehagyni csak
kívülről lehet — a `set_progress_handler` visszahívása nem nullát adva
megszakítja. Ez biztonságos: a `VACUUM` egy ideiglenes fájlba dolgozik, és
csak a legvégén cserél; megszakításkor az **eredeti adatbázis érintetlen**.

**Haladás:** a `VACUUM` nem mond százalékot, és nem is hazudunk egyet. Az
`OnTimer` nevű eredeti státusz-ablak mintáját követve „szívverést" adunk
(a visszahívás számlálóját), a felület ebből határozatlan (busy)
állapotsort rajzol — ez őszintébb, mint egy kitalált százalék.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

#: Ennyi szabad hely fölött ajánljuk fel a tömörítést (százalék). Az
#: eredeti `compactpercentage` értéke nem derül ki a binárisból, ezért ez a
#: MI döntésünk: a 20% már érezhető pazarlás, alatta a `VACUUM` percei nem
#: érik meg.
DEFAULT_COMPACT_PERCENT = 20

#: Ennyi SQLite-virtuálgép-utasításonként fut a haladás-visszahívás.
#:
#: Szándékosan KICSI: a `VACUUM` munkájának java C-ben zajlik, alig lép
#: virtuálgép-utasítást — egy 4000 soros adatbázis teljes tömörítése 10 000
#: lépés ALATT végez, azaz a nagy osztóval a visszahívás egyszer sem futna
#: le, és a Mégse gomb sosem érne célba (mérve: 10 000 → 0 hívás,
#: 100 → 10 hívás).
_PROGRESS_STEPS = 50


class CompactionError(RuntimeError):
    """A tömörítés nem sikerült — az adatbázis érintetlen."""


class CompactionCancelled(RuntimeError):
    """A felhasználó megszakította a tömörítést — az adatbázis érintetlen."""


@dataclass(frozen=True)
class CompactionResult:
    """A tömörítés mérlege — a felületnek („mennyit nyertünk")."""

    before_bytes: int
    after_bytes: int

    @property
    def saved_bytes(self) -> int:
        # a `VACUUM` elvileg sosem növel, de a lemezt nem mi írjuk: a
        # negatív „megtakarítást" nem mutatjuk meg a felhasználónak
        return max(0, self.before_bytes - self.after_bytes)


def wasted_percent(db_path: str | Path) -> float:
    """A szabadlistán heverő lapok aránya százalékban (0.0, ha üres/nincs).

    Ez a `compactpercentage`-küszöb bemenete: a `VACUUM` nagyjából ennyit
    tud visszaadni a lemezből.
    """
    try:
        conn = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
    except sqlite3.Error:
        return 0.0
    try:
        pages = conn.execute("PRAGMA page_count").fetchone()[0]
        free = conn.execute("PRAGMA freelist_count").fetchone()[0]
    except sqlite3.Error:
        return 0.0
    finally:
        conn.close()
    if not pages:
        return 0.0
    return 100.0 * free / pages


def needs_compaction(
    db_path: str | Path, threshold_percent: float = DEFAULT_COMPACT_PERCENT
) -> bool:
    """Érdemes-e most tömöríteni (a `compactpercentage` megfelelője)."""
    return wasted_percent(db_path) >= threshold_percent


def compact_database(
    db_path: str | Path,
    progress: Callable[[int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> CompactionResult:
    """A `VACUUM` lefuttatása — megszakíthatóan.

    `progress` a szívverés (a visszahívások száma), `should_cancel` pedig
    az „álljunk le" kérdés; mindkettő a `VACUUM` közben, az SQLite
    haladás-visszahívásából hívódik. Megszakításkor `CompactionCancelled`,
    egyéb hibánál `CompactionError` — mindkét esetben az **eredeti
    adatbázis érintetlen**, mert a `VACUUM` csak a végén cserél.
    """
    path = Path(db_path)
    if not path.exists():
        raise CompactionError(f"Az adatbázis nem található: {path}")
    before = path.stat().st_size

    cancelled = False
    ticks = 0

    def _handler() -> int:
        nonlocal cancelled, ticks
        ticks += 1
        if progress is not None:
            progress(ticks)
        if should_cancel is not None and should_cancel():
            cancelled = True
            return 1  # nem nulla → az SQLite megszakítja a futó utasítást
        return 0

    conn = sqlite3.connect(path)
    try:
        # a `VACUUM` WAL módban sem futhat nyitott tranzakcióban
        conn.isolation_level = None
        conn.set_progress_handler(_handler, _PROGRESS_STEPS)
        conn.execute("VACUUM")
    except sqlite3.Error as error:
        if cancelled:
            raise CompactionCancelled(
                "A tömörítést megszakítottad — az adatbázis érintetlen."
            ) from error
        raise CompactionError(str(error)) from error
    finally:
        conn.set_progress_handler(None, 0)
        conn.close()

    return CompactionResult(before_bytes=before, after_bytes=path.stat().st_size)


__all__ = [
    "DEFAULT_COMPACT_PERCENT",
    "CompactionCancelled",
    "CompactionError",
    "CompactionResult",
    "compact_database",
    "needs_compaction",
    "wasted_percent",
]

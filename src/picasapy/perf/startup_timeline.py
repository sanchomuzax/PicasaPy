"""Kapcsolható **indulási idővonal** (#1601).

A tulajdonos jelentése: *„Kibaszott lassan indul el a szoftververzió. Nem
tudom, miért van ez, egyre lassabb."* Az „egyre lassabb" azt jelenti, hogy
valami az adat méretével skálázódik — de amíg nem tudjuk, MI tart MEDDIG,
minden gyorsítás vaktában lövés.

Ez a modul a mérőeszköz. Az induló szekvencia (`app/application.py`)
szakaszokra osztva jelenti be a munkát, a végén pedig egy **egyszerű,
átküldhető szöveges jelentés** készül: szakaszonkénti idő
ezredmásodpercben, összeg, és a három leglassabb szakasz kiemelve.

## Bekapcsolás

Környezeti változó: ``PICASAPY_STARTUP_TIMELINE=1``. Alapból KI van
kapcsolva, és kikapcsolva **semmit nem csinál**: nem olvas órát, nem
gyűjt listát, nem ír fájlt — a hívási helyeken így nem kell `if`-ágat
tartani (`start_startup_timeline()` kikapcsolva is ad példányt).

## Adatvédelem

A jelentés — a `perf/logwriter.py` szabályát követve — **nem tartalmaz
fájlnevet és nem tartalmaz teljes útvonalat**: a szakaszcímkék rögzített,
a forrásban leírt szövegek, nem futásidejű útvonalak. A felhasználó a
fájlt megnyithatja és elolvashatja, mielőtt elküldi.
"""

from __future__ import annotations

import platform as _platform
import time
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

#: A bekapcsoló környezeti változó neve.
STARTUP_TIMELINE_ENV = "PICASAPY_STARTUP_TIMELINE"

#: Igaznak számító értékek — magyarul és angolul is, mert a kapcsolót a
#: felhasználónak (nem fejlesztőnek) kell begépelnie egy támogatási körben.
_IGAZ_ERTEKEK = frozenset({"1", "true", "yes", "on", "igen", "be"})


def timeline_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Be van-e kapcsolva a mérés a környezetben.

    A `environ` befecskendezhető (teszt); alapértelmezésben az
    `os.environ`. Ismeretlen érték = kikapcsolva — egy elgépelt kapcsoló
    ne kezdjen el némán mérni."""
    if environ is None:
        import os

        environ = os.environ
    return environ.get(STARTUP_TIMELINE_ENV, "").strip().casefold() in _IGAZ_ERTEKEK


class _NullPhase:
    """Kikapcsolt állapotban visszaadott, nulla költségű kontextuskezelő.

    EGYETLEN, előre létrehozott példány: kikapcsolva a `phase()` sem
    objektumot nem allokál, sem órát nem olvas."""

    __slots__ = ()

    def __enter__(self) -> None:
        return None

    def __exit__(self, *_exc) -> bool:
        return False


_NULL_PHASE = _NullPhase()


class StartupTimeline:
    """Szakaszonkénti indulási időmérés — kikapcsolva no-op.

    Két bejelentési mód van, keverhetők:

    * ``with timeline.phase("címke"):`` — a blokk ideje egy szakasz;
    * ``timeline.mark("címke")`` — az ELŐZŐ bejelentés óta eltelt idő egy
      szakasz (ez illeszkedik a meglévő `startup_status.report(...)`
      hívásokhoz, amelyek már ma is kijelölik az indulás lépéseit).

    A `total_ms` a példány létrehozásától az utolsó bejelentésig eltelt
    TELJES idő — ez SZÁNDÉKOSAN nem a szakaszok összege: a nem mért rés
    így nem tűnik el, hanem a különbségben látszik."""

    __slots__ = ("_enabled", "_clock", "_started", "_last", "_phases")

    def __init__(
        self,
        *,
        enabled: bool = True,
        clock=time.perf_counter,
    ) -> None:
        self._enabled = bool(enabled)
        self._clock = clock
        self._started = clock() if self._enabled else 0.0
        self._last = self._started
        self._phases: list[tuple[str, float]] = []

    @property
    def enabled(self) -> bool:
        """Mér-e egyáltalán ez a példány."""
        return self._enabled

    @property
    def phases(self) -> tuple[tuple[str, float], ...]:
        """A bejelentett szakaszok `(címke, ezredmásodperc)` párokként,
        bejelentési sorrendben. Kikapcsolva üres."""
        return tuple(self._phases)

    @property
    def total_ms(self) -> float:
        """A példány létrehozásától az utolsó bejelentésig eltelt idő."""
        if not self._enabled:
            return 0.0
        return (self._last - self._started) * 1000.0

    # -- bejelentés ----------------------------------------------------------

    def mark(self, label: str) -> None:
        """Az ELŐZŐ bejelentés óta eltelt idő lezárása `label` néven."""
        if not self._enabled:
            return
        now = self._clock()
        self._phases.append((label, (now - self._last) * 1000.0))
        self._last = now

    def mark_from(self, started: float, label: str) -> None:
        """Egy MÁR ELKEZDŐDÖTT szakasz lezárása a megadott kezdőpillanattól.

        Az indulás első szakaszához kell: a Python- és PySide6-importok már
        lefutottak, mire ez a modul egyáltalán példányt tud létrehozni. A
        `started` (a belépési pont legelső saját `time.monotonic()`-ja)
        korábbi, mint a példány születése — ilyenkor a kezdetet is
        visszahúzzuk rá, hogy az `ÖSSZESEN` valóban a teljes indulást
        mutassa, ne csak a maradékát."""
        if not self._enabled:
            return
        now = self._clock()
        self._phases.append((label, (now - started) * 1000.0))
        self._started = min(self._started, started)
        self._last = now

    def phase(self, label: str):
        """A blokk idejét mérő kontextuskezelő.

        A hibával végződő blokk ideje IS bekerül: különben pont a bajos
        szakasz tűnne el a jelentésből."""
        if not self._enabled:
            return _NULL_PHASE
        return self._phase(label)

    @contextmanager
    def _phase(self, label: str):
        started = self._clock()
        try:
            yield
        finally:
            now = self._clock()
            self._phases.append((label, (now - started) * 1000.0))
            self._last = now

    # -- jelentés ------------------------------------------------------------

    def render(self, app_version: str = "", qt_version: str = "") -> str:
        """A felhasználónak átküldhető, egyszerű szöveges jelentés.

        Kikapcsolva üres sztring — a hívónak nem kell `if`-elnie."""
        if not self._enabled:
            return ""
        sorok = [
            "PicasaPy — indulási idővonal (#1601)",
            f"verzió: {app_version or 'ismeretlen'}",
            f"rendszer: {_platform.platform()} · Python {_platform.python_version()}"
            + (f" · Qt {qt_version}" if qt_version else ""),
            f"mérés kezdete: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
            "",
            f"{'ms':>10}  szakasz",
            f"{'-' * 10}  {'-' * 44}",
        ]
        for label, ms in self._phases:
            sorok.append(f"{ms:10.1f}  {label}")
        merte = sum(ms for _label, ms in self._phases)
        sorok.append(f"{'-' * 10}  {'-' * 44}")
        sorok.append(f"{merte:10.1f}  a mért szakaszok összege")
        sorok.append(f"{self.total_ms:10.1f}  ÖSSZESEN (indulás → kész ablak)")
        sorok.append("")
        sorok.append("A három leglassabb szakasz:")
        for label, ms in sorted(self._phases, key=lambda item: -item[1])[:3]:
            arany = (ms / self.total_ms * 100.0) if self.total_ms else 0.0
            sorok.append(f"  {ms:9.1f} ms ({arany:4.1f}%)  {label}")
        sorok.append("")
        return "\n".join(sorok)

    def write(
        self, directory: Path, app_version: str = "", qt_version: str = ""
    ) -> Path | None:
        """A jelentés fájlba írása; a fájl útvonalát adja vissza.

        Kikapcsolva `None`, és nem hoz létre semmit. Írási hiba esetén is
        `None` — egy diagnosztika soha nem akadályozhatja az indulást."""
        if not self._enabled:
            return None
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = Path(directory) / f"indulas-{stamp}.txt"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                self.render(app_version=app_version, qt_version=qt_version),
                encoding="utf-8",
            )
        except OSError:
            return None
        return target


def start_startup_timeline(
    environ: Mapping[str, str] | None = None,
) -> StartupTimeline:
    """A környezet alapján bekapcsolt (vagy no-op) idővonal.

    Kikapcsolva is példányt ad: a hívási helyeken így nincs `if`-ág, és a
    mérőpontok a forrásban akkor is olvashatók, ha épp nem mérünk."""
    return StartupTimeline(enabled=timeline_enabled(environ))


__all__ = [
    "STARTUP_TIMELINE_ENV",
    "StartupTimeline",
    "start_startup_timeline",
    "timeline_enabled",
]

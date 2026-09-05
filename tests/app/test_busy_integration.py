"""isWorking (#505) valódi controller-műveletek alatt/után — legalább két
konkrét controllerre (kötegelt effekt + export, a jegy kifejezett kérése):
a közös `AppBusyRegistry`-be a `BackgroundWorkerMixin._start_background`
automatikusan bejelentkezik, ezért ezeknek NEM kellett külön busy-bekötés —
ez a teszt ezt a végponttól-végpontig viselkedést ellenőrzi.

## Miért NEM a pillanatnyi `isWorking is True`-t állítjuk (#2137)

Az eredeti alak az `applyEffectMany`/`exportRows` után azonnal arra várt,
hogy `controller.isWorking is True` legyen. Ez **versenyhelyzet volt**, és
2026-09-03-án pirosra vitte a main CI-jét a windowsos lábon.

Az ok a `busy_registry` **szándékos** viselkedése (`_on_end` →
`_show_timer.stop()`, illetve `_on_show_timeout` korai `return`, ha
`_active <= 0`): *„a munka a küszöb ideje alatt befejeződött — nincs
villanás."* A `begin()`/`end()` a háttérszálról **sorba állított** jelzés;
ha a munka (két apró teszt-JPEG) olyan gyors, hogy mindkettő UGYANABBAN az
eseményhurok-körben kézbesítődik, a megjelenítő időzítő elindul és le is
áll, mielőtt lejárna — az `isWorking` tehát **soha nem lesz igaz**. Nem
hiba: pontosan ezt kéri a #505 („ne villogjon").

A teszt állítása ezért arra változott, ami a #505 tényleges ígérete és
időzítéstől független:

1. a művelet **bejelentkezik** a nyilvántartásba (`begin` legalább egyszer),
2. és **ki is jelentkezik** ugyanannyiszor (`end` == `begin`) — enélkül a
   csík örökre pörögne,
3. a művelet végén az `isWorking` **hamis**.

Az 1–2. az igazi bekötés-állítás: ha a `_start_background` abbahagyná az
automatikus bejelentkezést, a `begin` száma nulla lenne, és a teszt bukik.
"""

from __future__ import annotations

import time

import pytest

from picasapy.app import busy_registry as busy_registry_module
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry

#: 0 ms küszöb + bőkezű (200 ms) minimális láthatóság: a valódi háttérmunka
#: (2 apró teszt-JPEG) néhány ezredmásodperc alatt lefuthat. A 0 ms küszöb
#: azt CÉLOZZA, hogy a csík az első eseményhurok-körben felgyulladjon — de
#: nem GARANTÁLJA (ld. a modul docstringjét), ezért nem is állítjuk.
_TEST_SHOW_DELAY_MS = 0
_TEST_MIN_VISIBLE_MS = 200


@pytest.fixture(autouse=True)
def _small_busy_timings(monkeypatch):
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", _TEST_SHOW_DELAY_MS)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", _TEST_MIN_VISIBLE_MS)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


def _wait_until(qt_app, predicate, timeout_s=5.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    return False


class _RegistryKemlelo:
    """Megszámolja a `begin()`/`end()` hívásokat a busy-nyilvántartáson.

    Időzítéstől FÜGGETLEN: akkor is számol, ha a munka olyan gyors, hogy a
    csík (helyesen) meg sem jelenik."""

    def __init__(self, monkeypatch):
        self.begin = 0
        self.end = 0
        registry = get_app_busy_registry()
        eredeti_begin = registry.begin
        eredeti_end = registry.end

        def begin_szamlalo():
            self.begin += 1
            eredeti_begin()

        def end_szamlalo():
            self.end += 1
            eredeti_end()

        monkeypatch.setattr(registry, "begin", begin_szamlalo)
        monkeypatch.setattr(registry, "end", end_szamlalo)

    def ellenoriz(self, mit: str) -> None:
        assert self.begin >= 1, (
            f"a(z) {mit} nem jelentkezett be a busy-nyilvántartásba "
            f"(begin={self.begin}) — a _start_background automatikus "
            "bekötése elromlott"
        )
        assert self.end == self.begin, (
            f"a(z) {mit} nem jelentkezett ki annyiszor, ahányszor be "
            f"(begin={self.begin}, end={self.end}) — a csík örökre pörögne"
        )


class TestBatchEffectBusy:
    def test_bejelentkezik_es_kijelentkezik_a_busy_nyilvantartasba(
        self, qml_app, qt_app, monkeypatch
    ):
        window, controller, lib, engine = qml_app
        rows = list(range(len(controller.photos.photos)))
        assert rows, "a fixture-nek legalább egy fotót be kell töltenie"

        kemlelo = _RegistryKemlelo(monkeypatch)
        finished = []
        controller.photoOpFinished.connect(lambda: finished.append(True))

        controller.applyEffectMany(rows, "autolight")
        assert _wait_until(qt_app, lambda: bool(finished)), (
            "a kötegelt effekt nem jelzett befejezést (photoOpFinished)"
        )
        kemlelo.ellenoriz("kötegelt effekt")
        assert _wait_until(qt_app, lambda: controller.isWorking is False), (
            "isWorking a kötegelt effekt után is igaz maradt"
        )


class TestExportBusy:
    def test_bejelentkezik_es_kijelentkezik_a_busy_nyilvantartasba(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, controller, lib, engine = qml_app
        rows = list(range(len(controller.photos.photos)))
        assert rows, "a fixture-nek legalább egy fotót be kell töltenie"
        target = tmp_path / "export-out"
        target.mkdir()

        kemlelo = _RegistryKemlelo(monkeypatch)
        finished = []
        controller.exportFinished.connect(lambda exported, failed: finished.append(True))

        controller.exportRows(rows, str(target), 0, 90, False, "")
        assert _wait_until(qt_app, lambda: bool(finished)), (
            "az export nem jelzett befejezést (exportFinished)"
        )
        kemlelo.ellenoriz("export")
        assert _wait_until(qt_app, lambda: controller.isWorking is False), (
            "isWorking az export után is igaz maradt"
        )

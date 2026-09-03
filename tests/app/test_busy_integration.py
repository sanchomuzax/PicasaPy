"""isWorking (#505) valódi controller-műveletek alatt/után — legalább két
konkrét controllerre (kötegelt effekt + export, a jegy kifejezett kérése):
a közös `AppBusyRegistry`-be a `BackgroundWorkerMixin._start_background`
automatikusan bejelentkezik, ezért ezeknek NEM kellett külön busy-bekötés —
ez a teszt ezt a végponttól-végpontig viselkedést ellenőrzi.

A küszöböt/min-láthatóságot itt is aprómra állítjuk (ld. `test_qml_busy.py`
docstringje), hogy a `isWorking` gyorsan, determinisztikusan kövesse a
tényleges munkát."""

from __future__ import annotations

import time

import pytest

from picasapy.app import busy_registry as busy_registry_module
from picasapy.app.busy_registry import reset_app_busy_registry

#: 0 ms küszöb + bőkezű (200 ms) minimális láthatóság: a valódi háttérmunka
#: (2 apró teszt-JPEG) néhány ezredmásodperc alatt lefuthat — a 0 ms küszöb
#: biztosítja, hogy a csík az ELSŐ eseményhurok-körben felgyulladjon (még ha
#: a munka addigra esetleg már véget is ért), a hosszú min-láthatóság pedig
#: elég időt ad a tesztnek, hogy `isWorking is True`-t ténylegesen
#: megfigyelje, mielőtt visszaáll.
_TEST_SHOW_DELAY_MS = 0
_TEST_MIN_VISIBLE_MS = 200


@pytest.fixture(autouse=True)
def _small_busy_timings(monkeypatch):
    monkeypatch.setattr(busy_registry_module, "SHOW_DELAY_MS", _TEST_SHOW_DELAY_MS)
    monkeypatch.setattr(busy_registry_module, "MIN_VISIBLE_MS", _TEST_MIN_VISIBLE_MS)
    reset_app_busy_registry()
    yield
    reset_app_busy_registry()


class _BusyNaplo:
    """#2136: rögzíti, hogy a busy-állapot MIKOR volt igaz.

    A korábbi alak külön `_wait_until(... isWorking is True)`-val várt egy
    ÁTMENETI állapotra. Ha a munka a legelső ellenőrzés előtt befejeződött
    (egy apró kép, gyors lemez, a windows-futó időzítése), a ciklus sosem
    látta igaznak, és a teszt elbukott — a `main` CI-jét is pirosra vitte
    (run 33727512901, windows 2/4).

    KÉT forrásból gyűjt, mert egyik sem elég önmagában:
      • a `busyChanged` jelzésből — ez akkor is megfog, ha a munka egy
        eseményhurok-körön belül lefut;
      • a befejezésre váró ciklus MINTAVÉTELÉBŐL — mert két eset egy
        fájlban futtatva a `reset_app_busy_registry()` után a jelzés
        elmaradhat, miközben az `isWorking` a friss nyilvántartást olvassa
        (#2138).
    """

    def __init__(self, controller):
        self._controller = controller
        self.ertekek: list[bool] = [bool(controller.isWorking)]
        controller.busyChanged.connect(self._jegyez)

    def _jegyez(self) -> None:
        self.ertekek.append(bool(self._controller.isWorking))

    def mintavetel(self) -> None:
        self.ertekek.append(bool(self._controller.isWorking))

    @property
    def volt_igaz(self) -> bool:
        return True in self.ertekek


def _wait_until(qt_app, predicate, timeout_s=5.0, naplo=None):
    """Vár a feltételre, és közben — ha kap naplót — MINTÁT VESZ."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if naplo is not None:
            naplo.mintavetel()
        if predicate():
            return True
        time.sleep(0.005)
    return False


class TestBatchEffectBusy:
    def test_is_working_true_during_apply_false_after(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        rows = list(range(len(controller.photos.photos)))
        assert rows, "a fixture-nek legalább egy fotót be kell töltenie"

        finished = []
        controller.photoOpFinished.connect(lambda: finished.append(True))
        naplo = _BusyNaplo(controller)

        controller.applyEffectMany(rows, "autolight")
        assert _wait_until(qt_app, lambda: bool(finished), naplo=naplo), (
            "a kötegelt effekt nem jelzett befejezést (photoOpFinished)"
        )
        assert naplo.volt_igaz, (
            "a kötegelt effekt alatt isWorking egyszer sem lett igaz — a "
            f"látott értékek: {naplo.ertekek}"
        )
        assert _wait_until(qt_app, lambda: controller.isWorking is False), (
            "isWorking a kötegelt effekt után is igaz maradt"
        )


class TestExportBusy:
    def test_is_working_true_during_export_false_after(self, qml_app, qt_app, tmp_path):
        window, controller, lib, engine = qml_app
        rows = list(range(len(controller.photos.photos)))
        assert rows, "a fixture-nek legalább egy fotót be kell töltenie"
        target = tmp_path / "export-out"
        target.mkdir()

        finished = []
        controller.exportFinished.connect(lambda exported, failed: finished.append(True))
        naplo = _BusyNaplo(controller)

        controller.exportRows(rows, str(target), 0, 90, False, "")
        assert _wait_until(qt_app, lambda: bool(finished), naplo=naplo), (
            "az export nem jelzett befejezést (exportFinished)"
        )
        assert naplo.volt_igaz, (
            "az export alatt isWorking egyszer sem lett igaz — a látott "
            f"értékek: {naplo.ertekek}"
        )
        assert _wait_until(qt_app, lambda: controller.isWorking is False), (
            "isWorking az export után is igaz maradt"
        )

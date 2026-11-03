"""#6458: ha az előző frissítés visszaállt, a program induláskor kiírja az okát.

A tulajdonos 2026-11-03-án: „Azt ígérted, kiír valamit, nem ír ki semmit.”
A teszt a renderelt ablakot nézi: megnyílik-e, és a szöveg benne van-e az
ablak keretében. `PICASAPY_RENDER_KIMENET` megadásakor a kép lemezre kerül.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Property, QObject, QPointF

from tests.app.qml_functional.test_update_dialog_6340 import (
    _FakeUpdateController,
    _wait_for,
)


class _ElozoHibaFake(_FakeUpdateController):
    def __init__(self, kod: str):
        super().__init__()
        self._kod = kod

    @Property(bool, notify=_FakeUpdateController.updateAvailableChanged)
    def updateAvailable(self):  # noqa: N802
        return False

    @Property(str, constant=True)
    def previousUpdateFailure(self):  # noqa: N802
        return self._kod


def _keret(elem, gyoker):
    bal_felso = elem.mapToItem(gyoker, QPointF(0, 0))
    return (bal_felso.x(), bal_felso.y(),
            bal_felso.x() + elem.property("width"),
            bal_felso.y() + elem.property("height"))


def _beallit(qml_app, qt_app, kod):
    window, _controller, engine = qml_app
    window.resize(1280, 800)
    fake = _ElozoHibaFake(kod)
    engine.rootContext().setContextProperty("updateController", fake)
    dialog = window.findChild(QObject, "updateDialog")
    return window, dialog, fake


def test_foglalt_fajl_utan_az_ablak_magatol_megnyilik_az_okkal(qml_app, qt_app):
    window, dialog, _fake = _beallit(qml_app, qt_app, "fajl-foglalt")

    _wait_for(qt_app, lambda: bool(dialog.property("opened")), "az ablak nem nyílt meg magától")
    for _ in range(3):
        qt_app.processEvents()
        window.grabWindow()

    visszajelzes = window.findChild(QObject, "updateDialogFeedback")
    szoveg = visszajelzes.property("text")
    assert visszajelzes.property("visible")
    assert "previous update could not be installed" in szoveg
    assert "in use by another process" in szoveg
    tartalom = dialog.property("contentItem")
    ablak = _keret(dialog.property("background"), tartalom)
    bal, fent, jobb, lent = _keret(visszajelzes, tartalom)
    assert ablak[0] <= bal and jobb <= ablak[2] and ablak[1] <= fent and lent <= ablak[3]
    bezar = window.findChild(QObject, "updateDialogCloseButton")
    assert bezar.property("visible")

    kimenet = os.environ.get("PICASAPY_RENDER_KIMENET")
    if kimenet:
        Path(kimenet).mkdir(parents=True, exist_ok=True)
        window.grabWindow().save(str(Path(kimenet) / "frissites-elozo-hiba-6458.png"))


def test_mas_okra_a_kezi_telepitest_javasolja(qml_app, qt_app):
    window, dialog, _fake = _beallit(qml_app, qt_app, "egyeb")

    _wait_for(qt_app, lambda: bool(dialog.property("opened")), "az ablak nem nyílt meg magától")
    szoveg = window.findChild(QObject, "updateDialogFeedback").property("text")
    assert "did not finish" in szoveg


def test_sikeres_elozmenynel_nem_nyilik_meg(qml_app, qt_app):
    window, dialog, _fake = _beallit(qml_app, qt_app, "")

    for _ in range(10):
        qt_app.processEvents()
    assert not dialog.property("opened")

"""#6381: a hosszú műveletek első kattintásra elfoglaltságot jeleznek."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.collage_canvas_harness import (
    ABLAK,
    _panel as _collage_panel,
    keszits_kepeket,
    nyitott_vezerlo,
)
from tests.app.qml_functional.test_nyomtatas_bekotes_1472 import (
    _kijelol,
    _menubol_nyit,
)


def _var(qt_app, feltetel, masodperc=10):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _elem(root, nev):
    from PySide6.QtCore import QObject

    elem = root.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


@pytest.fixture
def collage_library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def collage_controller(qt_app, tmp_path, collage_library):
    yield from nyitott_vezerlo(tmp_path, collage_library)


@pytest.mark.parametrize("height_offset", (-5, 0, 5))
def test_kollazs_valodi_kattintasra_azonnal_foglaltt_es_kepet_ad(
    qt_app, collage_controller, monkeypatch, height_offset
):
    """A mentésjelző a háttérfeladat indulása előtt megjelenik és zárja a gombot."""
    from picasapy.app.worker_thread import BackgroundWorkerMixin

    inditasok = []
    monkeypatch.setattr(
        BackgroundWorkerMixin,
        "_start_background",
        lambda _self, target, **kwargs: inditasok.append((target, kwargs)),
    )
    panel = _collage_panel(
        collage_controller, height=ABLAK[1] + height_offset
    )
    view = panel.property("_view")
    button = _elem(panel, "collageShareButton")
    overlay = _elem(panel, "collageProgressOverlay")
    elotte = view.grabWindow()
    assert not elotte.isNull()

    center = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
    QTest.mouseClick(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )

    assert _var(qt_app, overlay.isVisible), "a kollázsfolyamatjelző nem jelent meg"
    assert len(inditasok) == 1, "a kattintás nem egy háttérműveletet indított"
    assert button.property("enabled") is False, "a Létrehozás gomb újra kattintható"
    spinner = _elem(panel, "collageProgressSpinner")
    assert spinner.property("running") is True

    utana = view.grabWindow()
    assert not utana.isNull()
    dpr = utana.width() / view.width()
    kezdet = overlay.mapToScene(QPointF(5, 57))
    y = round(kezdet.y() * dpr)
    x0 = round(kezdet.x() * dpr)
    kulonbozo = sum(
        elotte.pixelColor(x, y) != utana.pixelColor(x, y)
        for x in range(x0, round((kezdet.x() + 90) * dpr))
    )
    assert kulonbozo > 0, "a folyamatjelző háttere nem látszik a renderelt képen"


@pytest.mark.parametrize("height_offset", (-5, 0, 5))
def test_nyomtatas_valodi_kattintasra_az_elso_festesi_kockaban_foglalt(
    qml_app, qt_app, monkeypatch, tmp_path, height_offset
):
    from picasapy.app.print_controller import PrintController

    window, _controller, _engine = qml_app
    _kijelol(window, qt_app, [0])
    dialog = _menubol_nyit(window, qt_app)
    assert _var(qt_app, lambda: not dialog.property("meretezesFuggoben"))
    dialog.setProperty("pdfTarget", (tmp_path / "nyomtatas.pdf").as_uri())
    qt_app.processEvents()
    alapmagassag = round(dialog.height())
    dialog.setHeight(alapmagassag + height_offset)
    assert _var(
        qt_app, lambda: round(dialog.height()) == alapmagassag + height_offset
    )
    busy = _elem(dialog, "printStartingBusyIndicator")
    megfigyelt = []

    def festes_helyett_allapotot_var(_self, *_args, **_kwargs):
        qt_app.processEvents()
        megfigyelt.append(busy.isVisible() and busy.property("running"))
        return True

    monkeypatch.setattr(PrintController, "_run", festes_helyett_allapotot_var)
    button = _elem(dialog, "printStartButton")
    assert button.property("enabled") is True
    center = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
    QTest.mouseClick(
        dialog,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )

    assert megfigyelt == [True], (
        "a nyomtatás első renderelési körében nem jelent meg a foglalt állapot"
    )
    assert button.property("enabled") is True, "a befejezett nyomtatás nem engedte vissza a gombot"

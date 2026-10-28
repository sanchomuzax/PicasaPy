"""A dátumszűrő fogantyúja két külön QML-felépítésben azonos (#6127)."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QPoint, QPointF, QRect
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


_MAGASSAGOK = (695, 700, 705)
_ELSO_KEPEK: dict[int, bytes] = {}


def _item(window, object_name: str) -> QQuickItem:
    item = window.findChild(QQuickItem, object_name)
    assert item is not None, f"a(z) {object_name} QML-elem nem található"
    return item


def _var_feltetelre(alkalmazas, feltetel, leiras: str) -> None:
    vege = time.monotonic() + 3.0
    while time.monotonic() < vege:
        alkalmazas.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(f"Időtúllépés: {leiras}")


def _fogantyu_kep(window, slider: QQuickItem, qt_app, magassag: int) -> bytes:
    """A szöveg nélküli fogantyú-téglalap fizikai képpontjait adja vissza."""
    from PySide6.QtGui import QImage

    window.setProperty("width", 1024)
    window.setProperty("height", magassag)
    QTest.mouseMove(window, QPoint(1, 1))
    slider.setProperty("value", 0.0)
    _var_feltetelre(
        qt_app,
        lambda: int(window.width()) == 1024
        and int(window.height()) == magassag
        and float(slider.property("value")) == 0.0
        and float(slider.property("visualPosition")) == 0.0,
        "az ablak és a dátumcsúszka alapállapota",
    )
    handle = slider.property("handle")
    assert isinstance(handle, QQuickItem), "a dátumcsúszkának nincs QML-fogantyúja"

    scene_origin = handle.mapToScene(QPointF(0, 0))
    image = window.grabWindow().convertToFormat(QImage.Format.Format_RGBA8888)
    assert not image.isNull(), "üres lett az eszköztár képe"
    scale = image.devicePixelRatio()
    fizikai_x = scene_origin.x() * scale
    fizikai_y = scene_origin.y() * scale
    assert abs(fizikai_x - round(fizikai_x)) < 1e-6, (
        f"a fogantyú x-helye részképpontos: {fizikai_x:.4f} fizikai px"
    )
    assert abs(fizikai_y - round(fizikai_y)) < 1e-6, (
        f"a fogantyú y-helye részképpontos: {fizikai_y:.4f} fizikai px"
    )
    rect = QRect(
        round(scene_origin.x() * scale),
        round(scene_origin.y() * scale),
        round(handle.width() * scale),
        round(handle.height() * scale),
    )
    assert QRect(0, 0, image.width(), image.height()).contains(rect), (
        f"a fogantyú képdobozon kívülre került: {rect} / "
        f"{image.width()}×{image.height()}"
    )
    crop = image.copy(rect)
    return bytes(crop.constBits())


@pytest.mark.parametrize("magassag", _MAGASSAGOK)
def test_a_fogantyu_kepe_elso_felepitesben(qml_app, qt_app, magassag: int) -> None:
    window, _, _engine = qml_app
    slider = _item(window, "dateRangeFilterSlider")
    _ELSO_KEPEK[magassag] = _fogantyu_kep(window, slider, qt_app, magassag)


@pytest.mark.parametrize("magassag", _MAGASSAGOK)
def test_a_fogantyu_kepe_azonos_kulon_felepitesben(
    qml_app, qt_app, magassag: int
) -> None:
    window, _, _engine = qml_app
    slider = _item(window, "dateRangeFilterSlider")
    masodik = _fogantyu_kep(window, slider, qt_app, magassag)
    assert magassag in _ELSO_KEPEK, "az első képfelépítés mérése hiányzik"
    assert masodik == _ELSO_KEPEK[magassag], (
        f"a dátumcsúszka fogantyújának képe eltér két külön felépítés között "
        f"({magassag}px ablakmagasságnál, value=0, visualPosition=0)"
    )

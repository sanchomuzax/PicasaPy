"""Megnyitott képnél (néző) az F2 az átnevező párbeszédet nyitja (#6530).

Eredeti: a menüsáv `0xd6da28` rekordja (Fájl ▸ Átnevezés…, `F2`, `cmd 0x9d4f`,
`0x00559150` tölti) a nézőben is él; spec: docs/specs/picasa-gyorsbillentyuk.md 3.3.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._racs_helyimenuk_5150_helpers import varj
from tests.app.qml_functional._racs_maradek_5150_helpers import kep_cellaja
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg


@pytest.fixture
def qml_app(qt_app, tmp_path):
    def kepek(lib):
        make_minta_jpeg(lib / "a.jpg", size=(320, 160), seed=3)
        make_minta_jpeg(lib / "b.jpg", size=(100, 100), seed=6)

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=kepek)


def _dupla_kattintas(window, item) -> None:
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseDClick(window, Qt.MouseButton.LeftButton, pos=QPoint(round(pont.x()), round(pont.y())), delay=10)


def _nezo_megnyitasa(window, controller, qt_app) -> None:
    window.show()
    window.requestActivate()
    assert varj(qt_app, lambda: window.property("active") is True)
    assert varj(qt_app, lambda: len(controller.photos.photos) == 2)
    _dupla_kattintas(window, kep_cellaja(window, 0))
    assert varj(qt_app, lambda: window.property("viewerOpen") is True), "a néző nem nyílt meg"


def _parbeszed_lathato(window) -> bool:
    dialog = window.findChild(QObject, "renameManyDialog")
    return dialog is not None and dialog.property("visible") is True


def test_a_nezoben_az_f2_a_latott_kepet_nevezi_at(qml_app, qt_app):
    window, controller, _engine = qml_app
    _nezo_megnyitasa(window, controller, qt_app)

    QTest.keyClick(window, Qt.Key.Key_F2)
    qt_app.processEvents()

    assert varj(qt_app, lambda: _parbeszed_lathato(window)), (
        "megnyitott képnél az F2 nem nyitotta meg az átnevező párbeszédet"
    )
    assert window.findChild(QObject, "renameManySelectionLabel").property("text") == (
        "1 file(s) selected for rename."
    )
    mezo = window.findChild(QObject, "renameManyField")
    assert mezo.property("text") == "a", "a néző képe helyett más fájlt nevezne át"

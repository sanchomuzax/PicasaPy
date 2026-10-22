"""#5541: a diavetítő ◀ és ▶▶ léptetőgombja LENYOMÁSRA lép, nem felengedésre.

## A mérés forrása

`oneup.tre` 75-81: a sáv `prev` és `next` gombján `Property mousedown 1`.
A kattintáskezelő a `0x008032e0`, amely a `0x8000004` eseményre lép.

## Amit ez a próba mér

VALÓDI egérlenyomás a gomb közepén, felengedés nélkül: a képindex már
egyet lépett. Felengedés után nem lép még egyet. Nyomva tartva (1,5 s) is
pontosan egy lépés, mert a gomb nem ismétlődik. A lejátszás gomb ezzel
szemben felengedésre marad.

⚠️ A lenyomás az ABLAKON megy át (`QTest.mousePress`), nem egy elemre küldött
szintetikus eseményen, ld. `test_lenyomasra_sul_885.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre

#: (objectName, kiindulási index, a várt index egy lépés után). A négy képes
#: vetítésben az 1-es index a b.jpg, a 2-es a c.jpg.
LEPTETO = [
    ("slideshowNextButton", 1, 2),  # ▶▶: előre
    ("slideshowPrevButton", 2, 1),  # ◀: vissza
]


def _negy_kep_keszit(lib: Path) -> None:
    """Négy kép: a következő és az előző kép különbözzön."""
    for nev in ("a.jpg", "b.jpg", "c.jpg", "d.jpg"):
        make_jpeg(lib / nev, size=(100, 100))


@pytest.fixture
def negykepes_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_negy_kep_keszit)


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _gomb(window, name) -> QQuickItem:
    gomb = window.findChild(QQuickItem, name)
    assert gomb is not None, f"{name} nem található"
    return gomb


def _invoke(qt_app, obj, name, *args):
    QMetaObject.invokeMethod(
        obj, name, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


def _wait_ms(qt_app, ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    qt_app.processEvents()


def _lenyom(gomb, qt_app):
    """Valódi egér-lenyomás az ablakon, a gomb közepére."""
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mousePress(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _felenged(gomb, qt_app):
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mouseRelease(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _vetites_savval(window, qt_app, index):
    """Diavetítés szünetben, a vezérlősáv látható állapotban.

    A sávot a mozgás-kezelő kapcsolja be (`shown`). A próba a gombot méri,
    nem a mozgást, ezért a jelzőt közvetlenül állítjuk. A sáv 200 ms-os
    áttűnéssel jelenik meg, ezért megvárjuk, míg az opacitás eléri az 1-et.
    """
    _invoke(qt_app, window, "startSlideshow", index)
    show = _child(window, "slideshowView")
    show.setProperty("playing", False)
    qt_app.processEvents()
    savlap = _child(window, "slideshowControls")
    savlap.setProperty("shown", True)
    assert varj_feltetelre(
        qt_app, lambda: savlap.property("opacity") == 1, 5.0
    ), "a vezérlősáv nem jelent meg"
    return show


class TestLeptetoGombok:
    @pytest.mark.parametrize(("nev", "kezdo", "vart"), LEPTETO)
    def test_lenyomasra_egyet_lep_felengedes_elott(
        self, negykepes_app, qt_app, nev, kezdo, vart
    ):
        window, _controller, _engine = negykepes_app
        show = _vetites_savval(window, qt_app, kezdo)
        gomb = _gomb(window, nev)

        _lenyom(gomb, qt_app)
        assert show.property("currentIndex") == vart, (
            f"{nev}: lenyomásra nem lépett (várt index: {vart})"
        )
        _felenged(gomb, qt_app)
        assert show.property("currentIndex") == vart, (
            f"{nev}: felengedés után is lépett"
        )
        _invoke(qt_app, show, "stop")

    @pytest.mark.parametrize(("nev", "kezdo", "vart"), LEPTETO)
    def test_nyomva_tartva_is_pontosan_egy_lepes(
        self, negykepes_app, qt_app, nev, kezdo, vart
    ):
        window, _controller, _engine = negykepes_app
        show = _vetites_savval(window, qt_app, kezdo)
        gomb = _gomb(window, nev)

        _lenyom(gomb, qt_app)
        _wait_ms(qt_app, 1500)
        assert show.property("currentIndex") == vart, (
            f"{nev}: nyomva tartva nem pontosan egy lépés"
        )
        _felenged(gomb, qt_app)
        assert show.property("currentIndex") == vart, (
            f"{nev}: felengedés után újabb lépés történt"
        )
        _invoke(qt_app, show, "stop")

    def test_lejatszas_gomb_felengedesre_marad(self, negykepes_app, qt_app):
        window, _controller, _engine = negykepes_app
        show = _vetites_savval(window, qt_app, 1)
        gomb = _gomb(window, "slideshowPlayButton")

        _lenyom(gomb, qt_app)
        assert show.property("playing") is False, (
            "a lejátszás lenyomásra váltott, pedig felengedésre kell"
        )
        _felenged(gomb, qt_app)
        assert show.property("playing") is True, (
            "a lejátszás felengedésre sem váltott"
        )
        assert show.property("currentIndex") == 1
        _invoke(qt_app, show, "stop")

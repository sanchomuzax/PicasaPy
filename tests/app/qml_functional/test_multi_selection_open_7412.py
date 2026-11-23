"""Többes kijelölésnél az Enter és a View and Edit a rács első képét nyitja (#7412).

Az Entert és a helyi menüt valódi Ctrl-kattintások, billentyűleütés és
menüpont-kattintás indítja. A dupla kattintás ellenpróbája a célzott képet
nyitja akkor is, ha előtte két kép volt kijelölve.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qml_focus import fokuszt_ad
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    keres_vizualis_mindenablakban,
    jobbklikk_fotón,
    varj,
)
from tests.app.qml_functional._racs_maradek_5150_helpers import kep_cellaja

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


@pytest.fixture
def qml_app_7412(qt_app, tmp_path, request):
    def tesztkepek(lib: Path) -> None:
        make_jpeg(lib / "color_patches.jpg", size=(80, 60))
        make_jpeg(lib / "gradient.jpg", size=(80, 60))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=tesztkepek,
        keep_modul=request.module,
        nezetek_elore_epit=request.node.get_closest_marker(
            "halasztott_nezetek"
        ) is None,
    )


def _sorok(window) -> list[int]:
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return [int(sor) for sor in ertek]


def _ket_kep(qml_app_7412, qt_app, height_delta: int):
    window, controller, _engine = qml_app_7412

    eredeti_magassag = window.height()
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()
    assert varj(qt_app, lambda: window.height() == eredeti_magassag + height_delta), (
        "az ablak nem vette fel a paraméterezett magasságot"
    )
    assert [Path(controller.photos.filePathAt(row)).name for row in range(2)] == [
        "color_patches.jpg",
        "gradient.jpg",
    ]
    return window


def _ctrl_kattintas(window, qt_app, row: int) -> None:
    cella = kep_cellaja(window, row)
    pont = cella.mapToScene(QPointF(cella.width() / 2, cella.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.ControlModifier,
        pont.toPoint(),
    )
    qt_app.processEvents()


def _ket_kep_kijelol(window, qt_app) -> None:
    _ctrl_kattintas(window, qt_app, 0)
    _ctrl_kattintas(window, qt_app, 1)
    assert sorted(_sorok(window)) == [0, 1]
    assert window.property("selectedIndex") == 1


def _nezo_sora(window, qt_app) -> int:
    assert varj(qt_app, lambda: window.property("viewerOpen") is True), (
        "a parancs nem nyitotta meg a nézőt"
    )
    nezo = window.findChild(QObject, "photoViewer")
    assert nezo is not None, "a photoViewer nem található"
    assert varj(qt_app, lambda: nezo.property("currentIndex") >= 0), (
        "a photoViewer nem állt be egy képre"
    )
    return int(nezo.property("currentIndex"))


@pytest.mark.parametrize("height_delta", _ABLAKMAGASSAG_ELTOLASOK)
def test_enter_a_racs_elso_kijelolt_kepet_nyit(
    qml_app_7412, qt_app, height_delta
):
    window = _ket_kep(qml_app_7412, qt_app, height_delta)
    _ket_kep_kijelol(window, qt_app)
    fokuszt_ad(window.findChild(QObject, "photoGrid"), qt_app)

    QTest.keyClick(window, Qt.Key.Key_Return)

    assert _nezo_sora(window, qt_app) == 0


@pytest.mark.parametrize("height_delta", _ABLAKMAGASSAG_ELTOLASOK)
def test_helyi_menu_elso_kijeloltet_nyit_dupla_kattintas_celzott(
    qml_app_7412, qt_app, height_delta
):
    window = _ket_kep(qml_app_7412, qt_app, height_delta)
    _ket_kep_kijelol(window, qt_app)

    jobbklikk_fotón(window, qt_app, 1)
    tetel = keres_vizualis_mindenablakban(window, "contextMenuOpen")
    assert tetel is not None, "a View and Edit menüpont nem látszik"
    kattints(window, qt_app, tetel)
    assert _nezo_sora(window, qt_app) == 0

    nezo = window.findChild(QObject, "photoViewer")
    window.setProperty("viewerOpen", False)
    qt_app.processEvents()
    assert window.property("viewerOpen") is False

    cella = kep_cellaja(window, 1)
    pont = cella.mapToScene(QPointF(cella.width() / 2, cella.height() / 2))
    QTest.mouseDClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )
    qt_app.processEvents()
    assert nezo is not None
    assert _nezo_sora(window, qt_app) == 1

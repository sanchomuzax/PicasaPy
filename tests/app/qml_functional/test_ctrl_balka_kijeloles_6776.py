"""#6776: Ctrl+Balra az előző képet jelöli ki a könyvtári rácsban."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    varj,
)


def _vizualis_elemek(gyoker):
    for gyerek in gyoker.childItems():
        yield gyerek
        yield from _vizualis_elemek(gyerek)


def _kijelolt_sorok(window) -> list[int]:
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return [int(sor) for sor in ertek]


def _kattints_a_kepre(window, qt_app, sor: int) -> None:
    """A tényleges bélyegkép közepére kattint, a vezérlő geometriájából."""
    for elem in _vizualis_elemek(window.contentItem()):
        if elem.objectName() != "thumbMouseArea":
            continue
        cella = elem.parentItem()
        while cella is not None and cella.property("index") is None:
            cella = cella.parentItem()
        if cella is None or cella.property("index") != sor:
            continue
        pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
        assert 0 <= pont.x() < window.width() and 0 <= pont.y() < window.height(), (
            f"a(z) {sor}. kép kattintási pontja kívül esik az ablakon: {pont}"
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(pont.x()), round(pont.y())),
        )
        assert varj(qt_app, lambda: _kijelolt_sorok(window) == [sor]), (
            f"a valódi kattintás nem jelölte ki a(z) {sor}. képet"
        )
        return
    raise AssertionError(f"a(z) {sor}. kép bélyegképe nem található a vizuális fában")


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_ctrl_balra_a_fokuszalt_racsban_az_elozo_kepet_jeloli_ki(
    qt_app, tmp_path, magassag_eltolas
):
    app = app_epitese(qt_app, tmp_path)
    window, _controller, _engine = next(app)
    try:
        elokeszit(window, qt_app, _controller)
        alapmagassag = window.height()
        ablakmagassag = alapmagassag + magassag_eltolas
        window.setHeight(ablakmagassag)
        assert varj(qt_app, lambda: window.height() == ablakmagassag), (
            f"az ablak nem vette fel a(z) {ablakmagassag} px-es magasságot"
        )

        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None, "a könyvtári rács nem található"
        tab_strip = window.findChild(QObject, "documentTabStrip")
        assert tab_strip is not None, "a projektlap-sáv nem található"
        assert tab_strip.property("hasProjectTabs") is False, (
            "a próba projektlapok mellett nem a könyvtári billentyűutat mérné"
        )

        _kattints_a_kepre(window, qt_app, 2)
        assert varj(qt_app, lambda: grid.property("activeFocus") is True), (
            "a képre kattintás nem adta a fókuszt a rácsnak"
        )
        assert _kijelolt_sorok(window) == [2]

        QTest.keyClick(
            window, Qt.Key.Key_Left, Qt.KeyboardModifier.ControlModifier
        )

        assert varj(
            qt_app, lambda: _kijelolt_sorok(window) == [1]
        ), "a fókuszált könyvtári rács Ctrl+Balrája nem az előző képet jelölte ki"
    finally:
        next(app, None)

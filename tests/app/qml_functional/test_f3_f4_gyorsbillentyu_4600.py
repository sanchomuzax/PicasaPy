"""#4600 — az F3 a keresést indítja, az F4 a csillagot kapcsolja.

Az eredeti módosító nélküli billentyűágában (`0x005e6710`, a
`picasa-gyorsbillentyuk.md` 10.10): F3 (`0x005e69a4`) a
`searchcontainer/searchbutton`-t kattintja (= `Ctrl+F`), F4 (`0x005e696c`) a
`thumbui/startoggle`-t, ha az nem tiltott. A próbák VALÓDI billentyűleütést
adnak a főablaknak.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Q_ARG, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index
from support.qt_wait import wait_for_photo_op


def _child(root, name: str) -> QObject:
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _select(window, qt_app, index: int) -> None:
    QMetaObject.invokeMethod(
        window,
        "handleThumbClick",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
        Q_ARG("QVariant", 0),
    )
    qt_app.processEvents()


def _index_star(controller, name: str) -> int:
    with open_index(controller._db_path) as conn:
        row = conn.execute(
            "SELECT star FROM photos WHERE name = ?", (name,)
        ).fetchone()
    assert row is not None
    return int(row[0])


def _focus_library_view(window, qt_app) -> None:
    folder_list = _child(window, "folderListView")
    folder_list.forceActiveFocus()
    qt_app.processEvents()
    assert window.property("_szovegmezoneVanFokusz") is False


class TestF3Kereses:
    def test_az_F3_a_keresomezore_viszi_a_fokuszt(self, qml_app, qt_app) -> None:
        window, _controller, _engine = qml_app
        window.show()
        window.requestActivate()
        mezo = _child(window, "searchField")
        _focus_library_view(window, qt_app)
        assert mezo.property("activeFocus") is False

        QTest.keyClick(window, Qt.Key.Key_F3)
        qt_app.processEvents()

        assert mezo.property("activeFocus") is True, (
            "az F3 nem vitte a fókuszt a keresőmezőre"
        )


class TestF4Csillag:
    def test_az_F4_megfordítja_a_kijelolt_kep_csillagat(
        self, qml_app, qt_app
    ) -> None:
        window, controller, _engine = qml_app
        window.show()
        window.requestActivate()
        _select(window, qt_app, 0)
        _focus_library_view(window, qt_app)
        assert _index_star(controller, "a.jpg") == 0

        wait_for_photo_op(
            controller,
            lambda: QTest.keyClick(window, Qt.Key.Key_F4),
            qt_app=qt_app,
        )
        assert _index_star(controller, "a.jpg") == 1

        wait_for_photo_op(
            controller,
            lambda: QTest.keyClick(window, Qt.Key.Key_F4),
            qt_app=qt_app,
        )
        assert _index_star(controller, "a.jpg") == 0

    def test_kijeloles_nelkul_a_gomb_tiltott_es_az_F4_nem_tesz_semmit(
        self, qml_app, qt_app
    ) -> None:
        window, controller, _engine = qml_app
        window.show()
        window.requestActivate()
        QMetaObject.invokeMethod(
            window, "clearSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        _focus_library_view(window, qt_app)
        assert _child(window, "trayStarButton").property("enabled") is False

        QTest.keyClick(window, Qt.Key.Key_F4)
        qt_app.processEvents()

        assert _index_star(controller, "a.jpg") == 0
        assert _index_star(controller, "b.jpg") == 0

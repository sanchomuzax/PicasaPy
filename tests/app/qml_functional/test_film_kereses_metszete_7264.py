"""#7264: a film gomb és a keresőszöveg ugyanannak a szűrésnek a része."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel) -> bool:
    return var_feltetelre(qt_app, feltetel, 10.0)


def _elem(window, nev: str):
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} QML-elem nem található"
    return elem


def _kattint(window, qt_app, elem) -> None:
    """Valódi kattintás az aktuális QML-helyre, nem rögzített képpontra."""
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _nevek(controller) -> set[str]:
    return {kep.name for kep in controller.photos.photos}


def test_a_filmgomb_es_a_szoveg_valodi_kattintassal_es_gepelessel_metsz(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    mappa = Path(controller.currentFolder)
    (mappa / "feliratos.mp4").write_bytes(b"video")
    (mappa / "felirat_nelkuli.avi").write_bytes(b"video")
    (mappa / ".picasa.ini").write_text(
        "[feliratos.mp4]\ncaption=zqvid\n", encoding="utf-8"
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, mappa)
    controller._reload_after_sync()
    qt_app.processEvents()

    film_gomb = _elem(window, "movieFilter")
    mezo = _elem(window, "searchField")
    alap_magassag = int(window.height())

    # A felületi kattintás útja a helyi ablakmérethez igazított három
    # magasságon is működjön; a kattintási pont minden körben az elem helye.
    for elteres in (-5, 0, 5):
        window.resize(int(window.width()), alap_magassag + elteres)
        qt_app.processEvents()
        assert int(window.height()) == alap_magassag + elteres

        _kattint(window, qt_app, film_gomb)
        assert _varj(qt_app, lambda: controller.buttonFilterName == "videos")
        assert controller.viewModeName == "videos"
        assert _nevek(controller) == {"feliratos.mp4", "felirat_nelkuli.avi"}

        mezo.forceActiveFocus()
        qt_app.processEvents()
        for karakter in "zqvid":
            QTest.keyClick(window, karakter)
        assert _varj(qt_app, lambda: controller.searchQuery == "zqvid")
        assert controller.buttonFilterName == "videos"
        assert _nevek(controller) == {"feliratos.mp4"}

        # Az aktív filmgomb kikapcsolása a keresőszöveget és annak találatát
        # hagyja meg.
        _kattint(window, qt_app, film_gomb)
        assert _varj(qt_app, lambda: controller.buttonFilterName == "")
        assert controller.viewModeName == "search"
        assert controller.searchQuery == "zqvid"
        assert str(mezo.property("text")) == "zqvid"
        assert _nevek(controller) == {"feliratos.mp4"}

        # Újra bekapcsolva a filmgomb marad aktív a szöveg törlésekor.
        _kattint(window, qt_app, film_gomb)
        assert _varj(qt_app, lambda: controller.buttonFilterName == "videos")
        mezo.forceActiveFocus()
        qt_app.processEvents()
        for _ in range(len(str(mezo.property("text")))):
            QTest.keyClick(window, Qt.Key.Key_Backspace)
        assert _varj(qt_app, lambda: str(mezo.property("text")) == "")
        assert _varj(qt_app, lambda: controller.searchQuery == "")
        assert controller.viewModeName == "videos"
        assert controller.buttonFilterName == "videos"
        assert _nevek(controller) == {"feliratos.mp4", "felirat_nelkuli.avi"}

        controller.clearFilter()
        qt_app.processEvents()

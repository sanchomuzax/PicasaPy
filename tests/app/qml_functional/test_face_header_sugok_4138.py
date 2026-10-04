"""A névvel ellátott Emberek-fejléc súgói tényleges főablakban (#4138).

A súgót nem a QML-forrásból olvassuk: valódi kurzormozgás után a látható
`picasaToolTipText` elem szövegét ellenőrizzük. A kurzuspont minden esetben a
vezérlő `mapToScene` geometriájából jön, és az ablakmagasságot ±5 képponttal
is eltoljuk.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Q_ARG,
    QCoreApplication,
    QEvent,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
    QUrl,
)
from PySide6.QtGui import QHoverEvent
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

import picasapy.app.application as app_module
from picasapy.index import open_index, sync_tree


_ROY = "b8e4117cf1d6615b"
_FEJLEC_SUGOK = {
    "headerFaceZoomButton": "Megjelenítés az arcra közelítve",
    "headerPictureZoomButton": "Megjelenítés a teljes képre távolítva",
    "headerPlayButton": "Diavetítés teljes képernyőn",
}
_SUGO_PROBA = """
import QtQuick
import QtQuick.Controls
QtObject {
    property var cel: null
    readonly property var buborek: cel ? cel.ToolTip.toolTip : null
    readonly property bool buborekLatszik:
        buborek ? buborek.visible : false
    readonly property string kirajzoltSzoveg:
        buborek && buborek.contentItem ? buborek.contentItem.text : ""
    readonly property bool szovegLatszik:
        buborek && buborek.contentItem ? buborek.contentItem.visible : false
}
"""


def _szemely_album(qml_app, tmp_path, qt_app):
    """A fixture képe Roy megerősített arcával valódi Emberek-albummá válik."""
    window, controller, engine = qml_app
    lib = tmp_path / "kepek"
    (lib / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n"
        f"[a.jpg]\nfaces=rect64(40004000c000c000),{_ROY};\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller.showPerson("Roy Avery")
    qt_app.processEvents()
    return window, controller, engine


def _vizualis_utodok(elem):
    for child in elem.childItems():
        yield child
        yield from _vizualis_utodok(child)


def _lathato_elem(window, nev):
    talalatok = [
        elem
        for elem in _vizualis_utodok(window.contentItem())
        if elem.objectName() == nev and elem.isVisible()
    ]
    assert len(talalatok) == 1, f"{nev}: {len(talalatok)} látható példány"
    return talalatok[0]


def _buborek_probe(engine, vez):
    komponens = QQmlComponent(engine)
    komponens.setData(_SUGO_PROBA.encode("utf-8"), QUrl())
    probe = komponens.create()
    assert probe is not None, komponens.errors()
    probe.setProperty("cel", vez)
    probe.setParent(engine)
    return probe


def _mutato_feletti_sugo(qt_app, engine, ablak, vez, vart):
    kozep = vez.mapToScene(QPointF(vez.width() / 2, vez.height() / 2))
    probe = _buborek_probe(engine, vez)
    try:
        # Offscreen módban a QTest.mouseMove nem vált hover-t (#706). Az
        # eseményt a valódi főablak kapja, a koordináták a tényleges
        # vezérlőből jönnek.
        for tipus, cel in (
            (QEvent.Type.HoverLeave, QPointF(0, 0)),
            (QEvent.Type.HoverEnter, kozep),
            (QEvent.Type.HoverMove, kozep),
        ):
            QCoreApplication.sendEvent(
                ablak,
                QHoverEvent(tipus, cel, cel, QPointF(-1, -1)),
            )
            qt_app.processEvents()
        helyi = QPointF(vez.width() / 2, vez.height() / 2)
        for tipus in (QEvent.Type.HoverEnter, QEvent.Type.HoverMove):
            QCoreApplication.sendEvent(
                vez,
                QHoverEvent(tipus, helyi, kozep, QPointF(-1, -1)),
            )
            qt_app.processEvents()
        QTest.qWait(750)  # a közös ToolTip késleltetése 600 ms
        qt_app.processEvents()
        assert probe.property("buborekLatszik"), (
            f"{vez.objectName()}: a buboréksúgó nem rajzolódott ki"
        )
        assert probe.property("szovegLatszik"), (
            f"{vez.objectName()}: a buboréksúgó szövege nem látható"
        )
        assert probe.property("kirajzoltSzoveg") == vart
    finally:
        # A ToolTip.visible HoverHandler/Control.hovered állapotán függ. Ha
        # itt bent marad a kurzor, a következő teszt popupját elnyomhatja.
        QCoreApplication.sendEvent(
            vez,
            QHoverEvent(
                QEvent.Type.HoverLeave,
                QPointF(-1, -1),
                kozep,
                kozep,
            ),
        )
        QCoreApplication.sendEvent(
            ablak,
            QHoverEvent(
                QEvent.Type.HoverLeave,
                QPointF(0, 0),
                QPointF(0, 0),
                kozep,
            ),
        )
        probe.deleteLater()
        qt_app.processEvents()


def _magyar_fordito(qt_app, engine):
    """A QML betöltése után a valódi magyar fordítót teszi aktívvá."""
    ford = app_module._install_translator(qt_app, "hu")
    assert ford is not None, "a magyar .qm fordító nem tölthető be"
    engine.retranslate()
    qt_app.processEvents()
    return ford


def test_faceheader_sugok_a_valodi_foablakban_es_valtozo_magassaggal(
    qml_app, tmp_path, qt_app
):
    window, controller, engine = _szemely_album(qml_app, tmp_path, qt_app)
    ford = _magyar_fordito(qt_app, engine)
    try:
        eredeti_magassag = window.height()
        arc = _lathato_elem(window, "headerFaceZoomButton")
        kozep = arc.mapToScene(QPointF(arc.width() / 2, arc.height() / 2))
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(kozep.x()), round(kozep.y())),
        )
        qt_app.processEvents()
        assert controller.personFaceZoom is True

        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        grid = window.findChild(QObject, "photoGrid")
        assert grid is not None

        for elteres in (0, -5, 5):
            window.resize(window.width(), eredeti_magassag + elteres)
            qt_app.processEvents()
            for nev, vart in _FEJLEC_SUGOK.items():
                _mutato_feletti_sugo(
                    qt_app, engine, window, _lathato_elem(window, nev), vart
                )
            film = _lathato_elem(window, "trayMovieButton")
            assert film.isEnabled(), "a kijelölt kép mellett a filmgomb le van tiltva"
            _mutato_feletti_sugo(
                qt_app, engine, window, film,
                "Mozgófilmes prezentáció létrehozása",
            )
            QMetaObject.invokeMethod(
                window,
                "openPhotoContextMenu",
                Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", 0),
                Q_ARG("QVariant", grid),
                Q_ARG("QVariant", 5),
                Q_ARG("QVariant", 5),
            )
            qt_app.processEvents()
            menu = window.findChild(QObject, "photoContextMenu")
            assert menu is not None and menu.property("visible")
            item = window.findChild(
                QObject, "contextMenuSetAsPeopleAlbumThumbnail"
            )
            assert item is not None and item.isVisible()
            _mutato_feletti_sugo(
                qt_app, engine, window, item,
                "Beállítás indexképként az Emberek albumban",
            )
            QMetaObject.invokeMethod(
                menu, "close", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()
    finally:
        qt_app.removeTranslator(ford)
        engine.retranslate()

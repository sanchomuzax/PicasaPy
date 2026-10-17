"""#5150: a maradék tálca TapHandler-ei valódi egérrel működnek.

Mindegyik próba megkeresi a vizsgált QML-vezérlő ``objectName``-jét, majd
képernyő-koordinátára küldött QTest-bemenettel ellenőrzi az eredményt.
Az első, letiltott kattintás a rontás-kontroll: ha a kezelő nem kapja meg az
eseményt, a menü vagy a kijelölés nem változik.
"""

# rontás-kontroll: TapHandler.enabled=False → nincs hatás; True → ugyanaz a
# valódi QTest-kattintás megnyitja a várt menüt vagy kijelöli a képet.

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional.test_version_link_706 import KIADASOK_URL

_HEIGHT_DELTAS = (-5, 0, 5)


class _UrlFogo(QObject):
    def __init__(self):
        super().__init__()
        self.urls: list[str] = []

    @Slot("QUrl")
    def handle(self, url):
        self.urls.append(url.toString())


def _var(qt_app, predicate, seconds: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(predicate), seconds)


def _object(window, name: str, qml_type=QObject):
    result = window.findChild(qml_type, name)
    assert result is not None, f"{name} nem található"
    return result


def _visual_items(window, name: str) -> list[QQuickItem]:
    found: list[QQuickItem] = []
    pending = [window.contentItem()]
    while pending:
        item = pending.pop()
        if item.objectName() == name:
            found.append(item)
        pending.extend(item.childItems())
    return found


def _center(item) -> QPoint:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    return QPoint(round(point.x()), round(point.y()))


def _click(window, qt_app, item, button=Qt.MouseButton.LeftButton) -> None:
    assert item.isVisible() and item.width() > 0 and item.height() > 0, (
        f"{item.objectName()} nem látszik vagy nem kattintható"
    )
    point = _center(item)
    assert 0 <= point.x() < window.width() and 0 <= point.y() < window.height(), (
        f"{item.objectName()} kattintási pontja az ablakon kívül van: {point}"
    )
    QTest.mouseClick(window, button, Qt.KeyboardModifier.NoModifier, point)
    qt_app.processEvents()


def _set_height(window, qt_app, base_height: int, offset: int) -> None:
    height = base_height + offset
    window.setHeight(height)
    assert _var(qt_app, lambda: int(window.height()) == height), (
        f"az ablak nem vette fel a {height} px magasságot"
    )


def test_verzio_tap_kattintasa_a_kiadasok_oldalat_nyitja(qml_app, qt_app):
    window = qml_app[0]
    base_height = int(window.height())
    label = _object(window, "versionLabel", QQuickItem)
    tap = _object(label, "versionTap")
    assert tap.property("enabled") is True

    recorder = _UrlFogo()
    QDesktopServices.setUrlHandler("https", recorder, "handle")
    try:
        for height_delta in _HEIGHT_DELTAS:
            _set_height(window, qt_app, base_height, height_delta)
            url_count_before = len(recorder.urls)
            tap.setProperty("enabled", False)
            _click(window, qt_app, label)
            assert len(recorder.urls) == url_count_before, (
                "a letiltott versionTap külső címet nyitott"
            )

            tap.setProperty("enabled", True)
            _click(window, qt_app, label)
            assert _var(
                qt_app,
                lambda url_count_before=url_count_before: len(recorder.urls)
                == url_count_before + 1,
            ), (
                f"a verzióhivatkozás nem nyitott címet: {recorder.urls}"
            )
        assert recorder.urls == [KIADASOK_URL] * len(_HEIGHT_DELTAS), (
            f"a verzióhivatkozás nem a kiadások oldalát nyitotta: {recorder.urls}"
        )
    finally:
        QDesktopServices.unsetUrlHandler("https")
        qt_app.processEvents()


def test_talca_helyi_menu_tap_handler_valodi_jobbklikket_kezel(
    qml_app, qt_app
):
    window = qml_app[0]
    base_height = int(window.height())
    handler = _object(window, "trayContextMenuHandler")
    strip = _object(window, "trayScratchStrip", QQuickItem)
    menu = _object(window, "trayContextMenu")
    assert handler.property("enabled") is True
    assert menu.property("opened") is False

    for height_delta in _HEIGHT_DELTAS:
        _set_height(window, qt_app, base_height, height_delta)
        handler.setProperty("enabled", False)
        _click(window, qt_app, strip, Qt.MouseButton.RightButton)
        assert menu.property("opened") is False, (
            "a letiltott helyi menükezelő mégis megnyitott"
        )

        handler.setProperty("enabled", True)
        _click(window, qt_app, strip, Qt.MouseButton.RightButton)
        assert _var(qt_app, lambda: menu.property("opened") is True), (
            "a képtálca jobbklikkje nem nyitotta meg a helyi menüt"
        )
        menu.close()
        qt_app.processEvents()


def test_talcakep_tap_handler_kijeloli_a_kepet(qml_app, qt_app):
    window, controller, _engine = qml_app
    base_height = int(window.height())
    rows = list(range(min(2, controller.photos.rowCount())))
    assert len(rows) == 2, "a próba két tálcaképet igényel"
    controller.holdRows(rows)
    assert _var(
        qt_app,
        lambda: len(_visual_items(window, "trayPreviewThumb")) == 2,
    ), "a két tálcaképhez tartozó TapHandler nem épült fel"

    thumbs = sorted(
        _visual_items(window, "trayPreviewThumb"),
        key=lambda item: item.mapToScene(QPointF(0, 0)).x(),
    )
    for index, height_delta in enumerate(_HEIGHT_DELTAS):
        _set_height(window, qt_app, base_height, height_delta)
        target_index = index % 2
        thumb = thumbs[target_index]
        handler = _object(thumb, "trayThumbTap")
        assert _var(
            qt_app, lambda thumb=thumb: thumb.isVisible() and thumb.width() > 0
        )
        before = list(controller.traySelectedIndexes)

        handler.setProperty("enabled", False)
        _click(window, qt_app, thumb)
        assert list(controller.traySelectedIndexes) == before, (
            "a letiltott trayThumbTap kattintása megváltoztatta a kijelölést"
        )

        handler.setProperty("enabled", True)
        _click(window, qt_app, thumb)
        assert _var(
            qt_app, lambda target_index=target_index: list(controller.traySelectedIndexes) == [target_index]
        ), f"a {target_index}. tálcaképre adott kattintás nem jelölte ki azt"


def test_kimeneti_gombsor_tap_handler_jobbklikkre_menu_nyit(qml_app, qt_app):
    window = qml_app[0]
    base_height = int(window.height())
    handler = _object(window, "trayConfigureButtonsContextMenuHandler")
    target = _object(window, "trayPrintButton", QQuickItem)
    menu = _object(window, "configureButtonsContextMenu")
    assert handler.property("enabled") is True
    assert menu.property("visible") is False

    for height_delta in _HEIGHT_DELTAS:
        _set_height(window, qt_app, base_height, height_delta)
        handler.setProperty("enabled", False)
        _click(window, qt_app, target, Qt.MouseButton.RightButton)
        assert menu.property("visible") is False, (
            "a letiltott gombsor-kezelő mégis megnyitotta a menüt"
        )

        handler.setProperty("enabled", True)
        _click(window, qt_app, target, Qt.MouseButton.RightButton)
        assert _var(qt_app, lambda: menu.property("visible") is True), (
            "a gombsor jobbklikkje nem nyitotta meg a gombbeállítások menüjét"
        )
        menu.close()
        qt_app.processEvents()

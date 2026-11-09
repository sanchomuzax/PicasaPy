"""#6714: a §12.13 alatti, PicasaPy-ban szándékosan nem kötött billentyűk."""

from __future__ import annotations

from pathlib import Path
from time import monotonic

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


_FAKE_VIDEO_PLAYER = b"""
import QtQuick
Item {
    objectName: "keyboardTestVideoPlayer"
    property int playbackState: 2
    property int position: 1234
    function togglePlayback() {
        playbackState = playbackState === 1 ? 2 : 1
    }
}
"""

_KEYS_WITHOUT_PICASAPY_BINDING = (
    ("Ctrl+6", Qt.Key.Key_6, Qt.KeyboardModifier.ControlModifier),
    ("Ctrl+G", Qt.Key.Key_G, Qt.KeyboardModifier.ControlModifier),
    (
        "Ctrl+Alt+G",
        Qt.Key.Key_G,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    ),
    (
        "Ctrl+Alt+Shift+G",
        Qt.Key.Key_G,
        Qt.KeyboardModifier.ControlModifier
        | Qt.KeyboardModifier.AltModifier
        | Qt.KeyboardModifier.ShiftModifier,
    ),
    (
        "Ctrl+Shift+L",
        Qt.Key.Key_L,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
    ),
    (
        "Ctrl+Alt+S",
        Qt.Key.Key_S,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier,
    ),
    (
        "Ctrl+Shift+U",
        Qt.Key.Key_U,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
    ),
    (
        "Ctrl+Shift+Y",
        Qt.Key.Key_Y,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
    ),
    ("F12", Qt.Key.Key_F12, Qt.KeyboardModifier.NoModifier),
)


def _keszits_probakonyvtarat(lib: Path) -> None:
    from PIL import Image

    Image.new("RGB", (1600, 900), (255, 0, 0)).save(lib / "a-nagy.jpg")
    Image.new("RGB", (320, 160), (0, 0, 255)).save(lib / "b-kicsi.jpg")
    # A scannernek elég a videó kiterjesztése; a lejátszót a próba helyettesíti.
    (lib / "c-video.mp4").write_bytes(b"fake video; never decoded")


@pytest.fixture
def qml_app_6714(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_probakonyvtarat,
    )


def _varj(qt_app, feltetel, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, timeout)


def _objektum(window, object_name: str):
    result = window.findChild(QObject, object_name)
    assert result is not None, f"{object_name} nem található"
    return result


def _valtozatra(value):
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    if isinstance(value, (list, tuple)):
        return tuple(_valtozatra(entry) for entry in value)
    if isinstance(value, dict):
        return tuple(sorted((key, _valtozatra(entry)) for key, entry in value.items()))
    return value


def _bool_property(item: QObject, name: str) -> bool:
    if item.metaObject().indexOfProperty(name) < 0:
        return False
    return bool(item.property(name))


def _nyitott_nevu_elemek(window) -> tuple[tuple[str, bool, bool], ...]:
    """Látható névvel bíró QML-elemek és megnyitott párbeszédpanelek."""
    all_items = [window, *window.findChildren(QObject)]
    opened = []
    for item in all_items:
        name = item.objectName()
        if not name:
            continue
        visible = _bool_property(item, "visible")
        is_opened = _bool_property(item, "opened")
        if visible or is_opened:
            opened.append((name, visible, is_opened))
    return tuple(sorted(opened))


def _allapot(window, controller) -> tuple:
    tabs = _objektum(window, "documentTabStrip")
    drawers = tuple(
        (name, bool(window.property(name)))
        for name in (
            "tagsPanelOpen",
            "placesPanelOpen",
            "propertiesPanelOpen",
            "peoplePanelOpen",
        )
    )
    windows = tuple(
        sorted(
            (item.objectName(), bool(item.isVisible()), bool(item.isActive()))
            for item in QGuiApplication.topLevelWindows()
            if isinstance(item, QQuickWindow)
        )
    )
    return (
        controller.viewModeName,
        bool(window.property("viewerOpen")),
        tuple(_valtozatra(window.property("selectedIndexes"))),
        int(window.property("selectedIndex")),
        drawers,
        tabs.property("activeTabId"),
        _valtozatra(tabs.property("projectTabs")),
        _nyitott_nevu_elemek(window),
        windows,
    )


def _maradjon_valtozatlan(qt_app, state_getter, expected, *, seconds=0.2) -> bool:
    """Rövid, határidős eseményciklusban figyeli, hogy nem nyílik-e meg UI."""
    deadline = monotonic() + seconds
    while True:
        qt_app.processEvents()
        if state_getter() != expected:
            return False
        remaining = deadline - monotonic()
        if remaining <= 0:
            return True
        QTest.qWait(min(50, max(1, round(remaining * 1000))))


def test_konyvtari_nem_bekotott_billentyuk_nem_valtoztatjak_meg_az_allapotot(
    qml_app_6714, qt_app
):
    window, controller, _engine = qml_app_6714
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: window.isActive()), "a főablak nem aktiválódott"
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 3), (
        "a könyvtár három tesztelemét nem indexelte a program"
    )
    grid = _objektum(window, "photoGrid")
    grid.forceActiveFocus()
    assert _varj(qt_app, lambda: grid.property("activeFocus") is True), (
        "a könyvtári rács nem kapott fókuszt"
    )
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)

    def state_getter():
        return _allapot(window, controller)

    for label, key, modifiers in _KEYS_WITHOUT_PICASAPY_BINDING:
        before = state_getter()
        QTest.keyClick(window, key, modifiers)
        assert _maradjon_valtozatlan(qt_app, state_getter, before), (
            f"a PicasaPy-ban szándékosan nem kötött {label} megváltoztatta "
            "a nézetet, kijelölést, fiókot, lapot vagy megnyitott ablakot"
        )


def _racs_szelessege(window, grid, qt_app, cel: int) -> None:
    window.setWidth(round(window.width() + cel - grid.width()))
    assert _varj(qt_app, lambda: round(grid.width()) == cel), (
        "a tartalomnézet szélessége nem állt be a Ctrl+Alt előnézet küszöbéhez"
    )


def _leszarmazottak(elem):
    for child in elem.childItems():
        yield child
        yield from _leszarmazottak(child)


def _thumb_area(window, row: int):
    return next(
        (
            area
            for area in _leszarmazottak(window.contentItem())
            if area.objectName() == "thumbMouseArea"
            and area.isVisible()
            and area.parentItem().property("index") == row
        ),
        None,
    )


def test_konyvtar_ctrl_alt_keyclick_megjeleniti_a_kijelolt_elonezetet(
    qml_app_6714, qt_app
):
    window, controller, _engine = qml_app_6714
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: window.isActive()), "a főablak nem aktiválódott"
    grid = _objektum(window, "photoGrid")
    popup = _objektum(window, "ctrlAltHoverPreviewWindow")
    _racs_szelessege(window, grid, qt_app, 1200)
    alapmagassag = window.height()

    sor_nevvel = {
        Path(controller.photos.filePathAt(row)).name: row
        for row in range(controller.photos.rowCount())
    }
    kis_sor = sor_nevvel["b-kicsi.jpg"]
    nagy_sor = sor_nevvel["a-nagy.jpg"]
    window.setProperty("selectedIndexes", [kis_sor])
    window.setProperty("selectedIndex", kis_sor)
    visibility_changes = []
    popup.visibleChanged.connect(
        lambda: visibility_changes.append(bool(popup.isVisible()))
    )
    for offset in (-5, 0, 5):
        celmagassag = alapmagassag + offset
        window.setHeight(celmagassag)
        assert _varj(
            qt_app, lambda height=celmagassag: window.height() == height
        ), (
            f"a főablak magassága nem állt be ({offset:+} px)"
        )
        assert _varj(qt_app, lambda: _thumb_area(window, nagy_sor) is not None), (
            "a nagy kép könyvtári egérterülete nem épült fel"
        )
        area = _thumb_area(window, nagy_sor)
        QTest.mouseMove(window, QPoint(1, 1), delay=10)
        center = area.mapToScene(QPointF(area.width() / 2, area.height() / 2))
        QTest.mouseMove(window, center.toPoint(), delay=10)
        assert _varj(
            qt_app, lambda target=area: target.property("containsMouse") is True
        ), (
            "a kurzor nem a nagy kép könyvtári celláján áll"
        )

        change_start = len(visibility_changes)
        QTest.keyClick(window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier)
        assert _varj(
            qt_app,
            lambda start=change_start: True in visibility_changes[start:],
        ), (
            "a Ctrl+Alt valódi billentyűleütése nem jelenítette meg az előnézetet"
        )
        assert popup.property("visible") is False, (
            "a keyClick Alt-elengedése után az előnézeti ablaknak el kell tűnnie"
        )
        assert controller.property("ctrlAltHeld") is False, (
            "a Ctrl+Alt leütés után nem állt vissza a módosító állapota"
        )


def test_videonezet_irasjelbillentyui_nem_valtoztatjak_a_lejatszast(
    qml_app_6714, qt_app
):
    window, controller, engine = qml_app_6714
    # #6700: a néző csak az első megnyitáskor épül fel; előbb egy állóképen
    # nyitjuk meg, így a videó Loader még üres, amikor a helyettesítő bekerül.
    kep_row = next(
        row
        for row in range(controller.photos.rowCount())
        if not controller.photos.isVideoAt(row)
    )
    window.setProperty("viewerOpen", True)
    assert _varj(
        qt_app, lambda: window.findChild(QObject, "photoViewer") is not None
    ), "a néző nem jött létre a megnyitáskor"
    viewer = _objektum(window, "photoViewer")
    viewer.setProperty("currentIndex", kep_row)
    loader = _objektum(window, "videoLoader")
    komponens = QQmlComponent(engine)
    komponens.setData(_FAKE_VIDEO_PLAYER, QUrl())
    assert not komponens.isError(), komponens.errorString()

    # Állóképnél a videó Loader üres, így a helyettesítő a MediaPlayer
    # létrehozása előtt kerül bele; a teszt sosem indít valódi Qt-videódekódolást.
    loader.setProperty("source", "")
    loader.setProperty("sourceComponent", komponens)
    video_row = next(
        row
        for row in range(controller.photos.rowCount())
        if controller.photos.isVideoAt(row)
    )
    viewer.setProperty("currentIndex", video_row)
    window.setProperty("viewerOpen", True)
    assert _varj(
        qt_app,
        lambda: viewer.isVisible()
        and viewer.property("isCurrentVideo") is True
        and loader.property("item") is not None,
    ), "a videós néző vagy a helyettesítő lejátszó nem épült fel"
    player = loader.property("item")
    assert player.objectName() == "keyboardTestVideoPlayer", (
        "a videó Loader nem a dekóder nélküli helyettesítőt használja"
    )
    viewer.forceActiveFocus()
    assert _varj(qt_app, lambda: viewer.property("activeFocus") is True), (
        "a videós néző nem kapott billentyűfókuszt"
    )

    for label, key in (
        ("/", Qt.Key.Key_Slash),
        (",", Qt.Key.Key_Comma),
        (".", Qt.Key.Key_Period),
    ):
        before = (player.property("playbackState"), player.property("position"))
        QTest.keyClick(window, key, Qt.KeyboardModifier.NoModifier)
        assert _maradjon_valtozatlan(
            qt_app,
            lambda: (player.property("playbackState"), player.property("position")),
            before,
        ), f"a videónézeti {label} módosította a lejátszási állapotot vagy pozíciót"

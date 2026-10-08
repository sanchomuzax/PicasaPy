"""QML-funkcionális teszt: az indexkép-kontextusmenü újonnan bekötött
parancsai (#422, 2. lépcső).

A menü SZERKEZETÉT (tételsor, sorrend, szürke tételek, felirat-váltás) a
`tests/app/test_qml_context_menu.py` őrzi, a komponenst önmagában. Itt a
`Main.qml`-beli BEKÖTÉS a tárgy: a jelzés tényleg elvégzi-e a műveletet.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
import shiboken6

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.ini import load_document, update_document
from picasapy.ini.text_overlay import (
    TextBlock,
    TextGeometry,
    TextOverlay,
    TextStyle,
    serialize_text,
)
from picasapy.scanner import PICASA_INI_NAME


# A QML által birtokolt Popup/menüpont-wrappert a PySide6 teszt közben
# felszabadíthatja, ezért a tesztfolyamat végéig Pythonból is megtartjuk.
_KEEP_QML_OBJECTS = []


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open_menu(window, qt_app, row=0):
    """A menüt a Main.qml belépőjén át nyitja (a ThumbDelegate valódi
    jobbklikkje helyett) — a `test_album_context_menu.py` mintája."""
    grid = _child(window, "photoGrid")
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", row), Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    return _child(window, "photoContextMenu")


def _close_menu(window, qt_app):
    QMetaObject.invokeMethod(
        _child(window, "photoContextMenu"), "close",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


def _wait_for(qt_app, condition, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(condition())


def _click_item(qt_app, item):
    assert item is not None
    assert item["enabled"] is True, f"{item['name']} le van tiltva"
    assert item["width"] > 0 and item["height"] > 0
    QTest.mouseClick(
        item["window"],
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(item["x"]), round(item["y"])),
    )
    qt_app.processEvents()


def _picture_menu_item(qt_app, window, object_name):
    menu_bar = window.property("menuBar")
    titles = {"&Picture", "&Kép"}
    menu = next(
        item for item in menu_bar.findChildren(QObject)
        if item.property("title") in titles
    )
    header = next(
        item for item in menu_bar.findChildren(QObject)
        if "MenuBarItem" in item.metaObject().className()
        and item.property("text") in titles
    )
    _KEEP_QML_OBJECTS.extend((menu_bar, menu, header))
    center = header.mapToScene(
        QPointF(header.width() / 2, header.height() / 2)
    )
    QTest.mouseClick(
        header.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    assert _wait_for(
        qt_app,
        lambda: menu.property("opened") is True,
    ), "a Picture menü nem nyílt meg"
    picture_menu = next(
        item for item in menu_bar.findChildren(QObject)
        if item.property("title") in titles
    )
    batch_menu = window.findChild(QObject, "menuPictureBatchEdit")
    assert batch_menu is not None
    _KEEP_QML_OBJECTS.append(batch_menu)
    submenu_item = _menu_item_info(
        picture_menu, "menuPictureBatchEdit", window, text="&Batch Edit"
    )
    _click_item(qt_app, submenu_item)
    assert _wait_for(
        qt_app,
        lambda: batch_menu.property("opened") is True,
    ), "a Batch Edit almenü nem nyílt meg"
    return _batch_menu_item_info(window, object_name)


def _find_menu_item(window, object_name):
    return _batch_menu_item_info(window, object_name)


def _batch_menu_item_info(window, object_name):
    batch_menu = window.findChild(QObject, "menuPictureBatchEdit")
    assert batch_menu is not None
    _KEEP_QML_OBJECTS.append(batch_menu)
    result = _menu_item_info(batch_menu, object_name, window)
    return result


def _batch_menu_item_names(window):
    batch_menu = window.findChild(QObject, "menuPictureBatchEdit")
    assert batch_menu is not None
    expression = QQmlExpression(
        qmlContext(batch_menu),
        batch_menu,
        "(function () {"
        "  var names = [];"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        "    if (item) names.push(item.objectName);"
        "  }"
        "  return names.join('|');"
        "})()",
    )
    result, error = expression.evaluate()
    assert not error, expression.error()
    return str(result).split("|")


def _menu_item_info(menu, object_name, window, *, text=None):
    expression = QQmlExpression(
        qmlContext(menu),
        menu,
        "(function () {"
        "  for (var i = 0; i < count; ++i) {"
        "    var item = itemAt(i);"
        f"    if (item && (item.objectName === '{object_name}'"
        f"        || item.text === '{text or ''}')) {{"
        "      return item;"
        "    }"
        "  }"
        "  return null;"
        "})()",
    )
    result, error = expression.evaluate()
    assert not error, expression.error()
    assert result is not None, f"{object_name} nincs a menüben"
    item = shiboken6.wrapInstance(
        shiboken6.getCppPointer(result)[0], QQuickItem
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    _KEEP_QML_OBJECTS.append(item)
    item_window = item.window()
    _KEEP_QML_OBJECTS.append(item_window)
    return {
        "name": object_name,
        "enabled": item.isEnabled(),
        "visible": item.isVisible(),
        "width": item.width(),
        "height": item.height(),
        "x": center.x(),
        "y": center.y(),
        "window": item_window,
        "qml_item": item,
    }


def _close_picture_menu(qt_app, window):
    menu_bar = window.property("menuBar")
    menu = next(
        item for item in menu_bar.findChildren(QObject)
        if item.property("title") in {"&Picture", "&Kép"}
    )
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _text_overlay_value():
    return serialize_text(
        TextOverlay(
            blocks=(
                TextBlock(
                    content="Synthetic overlay",
                    font="Arial",
                    geometry=TextGeometry(0.5, 0.5),
                    style=TextStyle(
                        fill_argb=0xFFFFFFFF, outline_argb=0xFF000000
                    ),
                ),
            )
        )
    )


def _write_overlay(controller, row, active):
    photo = controller.photos.photos[row]
    ini_path = Path(photo.folder_path) / PICASA_INI_NAME

    def mutate(document):
        document = document.with_value(
            photo.name, "text", _text_overlay_value()
        )
        return document.with_value(
            photo.name, "textactive", "1" if active else "0"
        )

    update_document(ini_path, mutate, backup=False)
    return ini_path, photo.name


def _photo_filters(controller, row):
    photo = controller.photos.photos[row]
    ini_path = Path(photo.folder_path) / PICASA_INI_NAME
    if not ini_path.exists():
        return None
    document = load_document(ini_path)
    section = document.section(photo.name)
    return section.get("filters") if section is not None else None


# A menü forgatás-parancsa a KÖTEGELT ágat hívja (`rotateRightMany`), ami a
# `_apply_batch`-en át SZINKRON fut — nincs háttérszál, és nem is bocsát ki
# külön végjelzésre. Az indexelt modell maga mutatja a művelet eredményét,
# ezért az ellenőrzés közvetlenül a valós, szinkron kötegelt művelet után fut.


class TestPhotoMenuCommands:
    def test_view_and_edit_opens_the_viewer_on_that_row(self, qml_app, qt_app):
        """A félkövér első tétel a duplakattintás művelete: megnyitja a
        nézőt a jobbklikkelt képen."""
        window, _controller, _engine = qml_app
        assert window.property("viewerOpen") is False
        menu = _open_menu(window, qt_app, row=1)
        menu.openRequested.emit()
        qt_app.processEvents()
        assert window.property("viewerOpen") is True
        assert _child(window, "photoViewer").property("currentIndex") == 1

    def test_rotate_right_turns_the_selected_photo(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        menu = _open_menu(window, qt_app, row=0)
        menu.rotateRightRequested.emit()
        qt_app.processEvents()
        assert controller.photos.photos[0].rotate_steps == 1
        _close_menu(window, qt_app)

    def test_rotate_left_turns_the_selected_photo(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        menu = _open_menu(window, qt_app, row=0)
        menu.rotateLeftRequested.emit()
        qt_app.processEvents()
        assert controller.photos.photos[0].rotate_steps == 3
        _close_menu(window, qt_app)

    def test_properties_toggles_the_properties_panel(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        before = window.property("propertiesPanelOpen")
        menu = _open_menu(window, qt_app)
        menu.propertiesRequested.emit()
        qt_app.processEvents()
        assert window.property("propertiesPanelOpen") is not before
        _close_menu(window, qt_app)

    @pytest.mark.parametrize("height_offset", (-5, 0, 5))
    def test_batch_sepia_es_bw_a_kijelolt_kepekre_kerul_es_undozhato(
        self, qml_app, qt_app, height_offset
    ):
        window, controller, _engine = qml_app
        window.setHeight(window.height() + height_offset)
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        sepia_item = _picture_menu_item(qt_app, window, "menuBatchSepia")
        names = _batch_menu_item_names(window)
        assert names.index("menuBatchSepia") == names.index("menuBatchSharpen") - 1
        assert names.index("menuBatchBlackWhite") == names.index("menuBatchSharpen") + 1
        assert sepia_item["qml_item"].property("text") == "&Sepia"
        _close_picture_menu(qt_app, window)

        kezdeti_lancok = {
            row: _photo_filters(controller, row) for row in (0, 1)
        }
        for object_name, effect_name, expected_label in (
            ("menuBatchSepia", "sepia", "&Sepia"),
            ("menuBatchBlackWhite", "bw", "&Black and White"),
        ):
            item = _picture_menu_item(qt_app, window, object_name)
            assert item["qml_item"].property("text") == expected_label
            _click_item(qt_app, item)

            assert _wait_for(
                qt_app,
                lambda effect_name=effect_name: not controller.batchEditActive
                and all(
                    f"{effect_name}=1;" in (_photo_filters(controller, row) or "")
                    for row in (0, 1)
                ),
            ), f"a {effect_name} nem került mindkét kijelölt képre"
            assert controller.canUndoBatchEdit is True

            controller.undoBatchEdit()
            assert _wait_for(
                qt_app,
                lambda: all(
                    _photo_filters(controller, row) == kezdeti_lancok[row]
                    for row in (0, 1)
                ),
            ), f"a {effect_name} nem vonódott vissza egy lépésben"
            assert controller.canUndoBatchEdit is False
            _close_picture_menu(qt_app, window)

    @pytest.mark.parametrize("height_offset", (-5, 0, 5))
    def test_picture_show_hide_text_clicks_follow_selected_overlay_state(
        self, qml_app, qt_app, height_offset
    ):
        window, controller, _engine = qml_app
        window.setHeight(window.height() + height_offset)
        window.setProperty("selectedIndexes", [0, 1])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        # Without text layers neither state-specific command is enabled.
        show_item = _picture_menu_item(qt_app, window, "menuPictureShowText")
        hide_item = _find_menu_item(window, "menuPictureHideText")
        assert show_item["enabled"] is False
        assert hide_item["enabled"] is False
        _close_picture_menu(qt_app, window)

        # A mixed selection enables each command. Real menu clicks should
        # apply the requested state to every selected photo with a text layer.
        first_ini, first_name = _write_overlay(controller, 0, active=False)
        second_ini, second_name = _write_overlay(controller, 1, active=True)

        hide_item = _picture_menu_item(qt_app, window, "menuPictureHideText")
        show_item = _find_menu_item(window, "menuPictureShowText")
        assert show_item["enabled"] is True
        assert hide_item["enabled"] is True
        _click_item(qt_app, hide_item)

        first = load_document(first_ini).section(first_name)
        second = load_document(second_ini).section(second_name)
        assert first.get("textactive") == "0"
        assert second.get("textactive") == "0"

        show_item = _picture_menu_item(qt_app, window, "menuPictureShowText")
        hide_item = _find_menu_item(window, "menuPictureHideText")
        assert show_item["enabled"] is True
        assert hide_item["enabled"] is False
        _click_item(qt_app, show_item)

        first = load_document(first_ini).section(first_name)
        second = load_document(second_ini).section(second_name)
        assert first.get("textactive") == "1"
        assert second.get("textactive") == "1"

        show_item = _picture_menu_item(qt_app, window, "menuPictureShowText")
        hide_item = _find_menu_item(window, "menuPictureHideText")
        assert show_item["enabled"] is False
        assert hide_item["enabled"] is True


class TestDeleteShortcutsAreContextDependent:
    """A lemezről törlés **mindkét helyi menüs felületen** `Ctrl+Delete`.

    ⚠️ **VISSZAVONT DÖNTÉS, kimondva (#1418).** A spec 3. szakasza korábban
    azt írta, hogy a nézőben a puszta `Delete` a helyes; ez a #422 feltevése
    volt. A #1154 mérése (a menüsáv rekordtáblája `0x00559150`-től és a
    helyi menük rekordjai a `0x00a6aee0` hívóiban) **felülírta**: a `0x9c9a`
    parancs FELÜLET szerint válik szét — **menüsávban** puszta `Delete`,
    **helyi menükben** (rács ÉS néző) `Ctrl+Delete`.

    Ez a teszt korábban a régi feltevést rögzítette szerződésként; most az
    új, mért állapotot rögzíti. A visszaesés ellen a
    `test_torles_billentyu_felulet_1418.py` ellenkező irányú őre véd (a
    nézőben a puszta `Delete` NEM törölhet)."""

    def test_grid_shortcut_is_ctrl_delete(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        shortcut = _child(window, "shortcutDeleteFromDiskGrid")
        sequence = str(shortcut.property("sequence"))
        assert sequence.startswith("Ctrl+") and sequence.endswith("Delete")

    def test_viewer_shortcut_is_ctrl_delete(self, qml_app, qt_app):
        """A néző is helyi menüs felület, tehát `Ctrl+Delete` (#1418)."""
        window, _controller, _engine = qml_app
        shortcut = _child(window, "shortcutDeleteFromDiskViewer")
        sequence = str(shortcut.property("sequence"))
        assert sequence.startswith("Ctrl+") and sequence.endswith("Delete")

    def test_only_one_of_them_is_live_at_a_time(self, qml_app, qt_app):
        """A nézőé csak nyitott nézőben, a rácsé csak zárt nézőben él —
        így ugyanaz a billentyű sosem jelent két dolgot egyszerre."""
        window, _controller, _engine = qml_app
        grid_shortcut = _child(window, "shortcutDeleteFromDiskGrid")
        viewer_shortcut = _child(window, "shortcutDeleteFromDiskViewer")

        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert grid_shortcut.property("enabled") is True
        assert viewer_shortcut.property("enabled") is False

        window.setProperty("viewerOpen", True)
        _child(window, "photoViewer").setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert grid_shortcut.property("enabled") is False
        assert viewer_shortcut.property("enabled") is True


class TestSaveCommandsInTheGridMenu:
    """#422: a mentés-szemantika három parancsa a rács jobbklikk-menüjéből
    is elérhető — a motorjuk a #444-ben elkészült, csak a menü maradt
    helyfoglaló. Az inaktív tétel LÁTSZIK, csak szürke (az eredeti
    szabálya: a menü magassága állandó, az izommemória működik)."""

    def test_they_are_present_with_their_labels(self, qml_app, qt_app):
        """A láthatóságot itt nem mérjük: zárt menüben a QML minden tételt
        rejtettnek mutat (a `visible` a szülőtől öröklődik)."""
        window, _controller, _engine = qml_app

        for name in (
            "contextMenuSave",
            "contextMenuRevert",
            "contextMenuUndoAllEdits",
        ):
            item = window.findChild(QObject, name)
            assert item is not None, f"{name} nem található"
            assert item.property("text")

    def test_save_is_disabled_without_edits(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        menu = window.findChild(QObject, "photoContextMenu")
        menu.setProperty("hasEdits", False)
        qt_app.processEvents()

        assert window.findChild(QObject, "contextMenuSave").property("enabled") is False
        assert (
            window.findChild(QObject, "contextMenuUndoAllEdits").property("enabled")
            is False
        )

    def test_save_becomes_available_with_edits(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        menu = window.findChild(QObject, "photoContextMenu")
        menu.setProperty("hasEdits", True)
        qt_app.processEvents()

        assert window.findChild(QObject, "contextMenuSave").property("enabled") is True

    def test_save_opens_the_same_confirmation_as_the_file_menu(
        self, qml_app, qt_app
    ):
        """Egy parancs, egy megerősítés — nem két, kicsit másképp
        viselkedő út ugyanarra."""
        window, _controller, _engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)

        QMetaObject.invokeMethod(
            window.findChild(QObject, "photoContextMenu"),
            "saveRequested",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert window.findChild(QObject, "saveConfirmDialog").property("visible")

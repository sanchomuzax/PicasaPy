"""QML-funkcionális teszt: az indexkép-kontextusmenü újonnan bekötött
parancsai (#422, 2. lépcső).

A menü SZERKEZETÉT (tételsor, sorrend, szürke tételek, felirat-váltás) a
`tests/app/test_qml_context_menu.py` őrzi, a komponenst önmagában. Itt a
`Main.qml`-beli BEKÖTÉS a tárgy: a jelzés tényleg elvégzi-e a műveletet.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt



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


# A menü forgatás-parancsa a KÖTEGELT ágat hívja (`rotateRightMany`), ami a
# `_apply_batch`-en át SZINKRON fut — nincs háttérszál, és nem is bocsát ki
# `photoOpFinished`-t. Korábban ez a teszt mégis arra várt: a néma, 2 mp-es
# vészfék miatt egyszerűen letelt az idő, és az utána következő állítás
# véletlenül helyes értéket talált. A #475-ös hangos vészfék ezt kibuktatta.


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

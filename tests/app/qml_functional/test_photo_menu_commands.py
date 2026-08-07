"""QML-funkcionális teszt: az indexkép-kontextusmenü újonnan bekötött
parancsai (#422, 2. lépcső).

A menü SZERKEZETÉT (tételsor, sorrend, szürke tételek, felirat-váltás) a
`tests/app/test_qml_context_menu.py` őrzi, a komponenst önmagában. Itt a
`Main.qml`-beli BEKÖTÉS a tárgy: a jelzés tényleg elvégzi-e a műveletet.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer


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


def _do_photo_op(controller, qt_app, action) -> None:
    """A forgatás háttérszálon fut — megvárja a `photoOpFinished`-t."""
    loop = QEventLoop()
    controller.photoOpFinished.connect(loop.quit)
    action()
    QTimer.singleShot(2000, loop.quit)
    loop.exec()
    qt_app.processEvents()


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
        _do_photo_op(controller, qt_app, menu.rotateRightRequested.emit)
        assert controller.photos.photos[0].rotate_steps == 1
        _close_menu(window, qt_app)

    def test_rotate_left_turns_the_selected_photo(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        menu = _open_menu(window, qt_app, row=0)
        _do_photo_op(controller, qt_app, menu.rotateLeftRequested.emit)
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
    """Spec 3.: a lemezről törlés a rácsban `Ctrl+Delete`, a nézőben
    `Delete` — a rácsban a puszta `Delete` mást jelent, ezért ott kell a
    módosító."""

    def test_grid_shortcut_is_ctrl_delete(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        shortcut = _child(window, "shortcutDeleteFromDiskGrid")
        sequence = str(shortcut.property("sequence"))
        assert sequence.startswith("Ctrl+") and sequence.endswith("Delete")

    def test_viewer_shortcut_is_plain_delete(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        shortcut = _child(window, "shortcutDeleteFromDiskViewer")
        assert str(shortcut.property("sequence")) == "Delete"

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

"""QML-funkcionális teszt: a néző jobbklikk-menüje (#422, 1. lépcső).

Az eredeti Picasában a nagy képen 17 tételes kontextusmenü él (`OneUp`
menüosztály); nálunk eddig EGYÁLTALÁN nem volt ilyen menü. A tételsort, a
csoportbontást és a viselkedési szabályokat a
`docs/specs/ui-audit-context-menus.md` 3. szakasza rögzíti:

- az első tétel FÉLKÖVÉR (= a dupla­kattintás alapértelmezett művelete),
  a nézőben „Visszatérés a könyvtárhoz" (`Esc`);
- az inaktív tétel is LÁTSZIK, szürkén — nem tűnik el, hogy a menü
  magassága és a tételek helye állandó maradjon;
- a lemezről törlés gyorsbillentyűje a nézőben `Delete` (a rácsban
  `Ctrl+Delete`, mert ott a puszta `Delete` mást jelent);
- az Elrejtés/Megjelenítés ugyanazon a helyen VÁLT feliratot.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer

# a spec 3. szakaszának teljes tételsora, sorrendben
_EXPECTED_ITEMS = [
    "viewerMenuBackToLibrary",
    "viewerMenuAddToAlbum",
    "viewerMenuRotateRight",
    "viewerMenuRotateLeft",
    "viewerMenuUndoAllEdits",
    "viewerMenuHide",
    "viewerMenuOpenFile",
    "viewerMenuOpenWith",
    "viewerMenuSave",
    "viewerMenuRevert",
    "viewerMenuLocate",
    "viewerMenuDelete",
    "viewerMenuCopyFullPath",
    "viewerMenuQuickUpload",
    "viewerMenuBlockUpload",
    "viewerMenuResetFaces",
    "viewerMenuProperties",
]

# amiknek MA sincs háttere — a Picasa ezeket is MEGJELENÍTI, szürkén.
# A Mentés / Visszaállítás / Összes szerkesztés visszavonása alapból
# szintén szürke, de NEM helyfoglaló: állapotfüggő (#422), ezért a saját
# tesztjük fedi őket lentebb.
_EXPECTED_DISABLED = [
    "viewerMenuOpenWith",
    "viewerMenuQuickUpload",
    "viewerMenuBlockUpload",
]


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _open_viewer(window, qt_app, row=0):
    window.setProperty("viewerOpen", True)
    viewer = _child(window, "photoViewer")
    viewer.setProperty("currentIndex", row)
    qt_app.processEvents()
    return viewer


def _open_menu(window, qt_app):
    """A menüt TÉNYLEGESEN megnyitja — zárt popupban a gyerek-elemek
    `visible`-je kötéstől függetlenül hamis (ld. test_album_context_menu)."""
    viewer = _child(window, "photoViewer")
    QMetaObject.invokeMethod(
        viewer, "openContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    return _child(window, "viewerContextMenu")


def _close_menu(window, qt_app):
    menu = _child(window, "viewerContextMenu")
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _do_photo_op(controller, qt_app, action) -> None:
    """A forgatás háttérszálon fut — megvárja a `photoOpFinished`-t
    (a `test_viewer.py` mintája)."""
    loop = QEventLoop()
    controller.photoOpFinished.connect(loop.quit)
    action()
    QTimer.singleShot(2000, loop.quit)
    loop.exec()
    qt_app.processEvents()


class TestViewerContextMenuStructure:
    def test_menu_exists_in_the_viewer(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)
        assert window.findChild(QObject, "viewerContextMenu") is not None

    def test_all_seventeen_commands_are_present_in_order(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)
        menu = _open_menu(window, qt_app)
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in _EXPECTED_ITEMS
        ]
        # a findChildren bejárási sorrendje a deklarációs sorrend
        assert found == _EXPECTED_ITEMS
        _close_menu(window, qt_app)

    def test_first_item_is_bold_and_returns_to_the_library(self, qml_app, qt_app):
        """A félkövér első tétel = a dupla­kattintás alapértelmezett
        művelete (spec 5.3.)."""
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)
        _open_menu(window, qt_app)
        item = _child(window, "viewerMenuBackToLibrary")
        assert item.property("font").bold() is True
        _close_menu(window, qt_app)

    def test_unbacked_commands_are_shown_but_disabled(self, qml_app, qt_app):
        """Az inaktív tétel is tétel: LÁTSZIK, de szürke (spec 5.1.)."""
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)
        _open_menu(window, qt_app)
        for name in _EXPECTED_DISABLED:
            item = _child(window, name)
            assert item.property("visible") is True, f"{name} eltűnt"
            assert item.property("enabled") is False, f"{name} nem szürke"
        _close_menu(window, qt_app)

    def test_delete_shortcut_is_plain_delete_in_the_viewer(self, qml_app, qt_app):
        """A rácsban `Ctrl+Delete`, a nézőben `Delete` — szándékos
        eltérés (spec 3.)."""
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)
        _open_menu(window, qt_app)
        # a projekt konvenciója: a gyorsbillentyű `\t` után áll a feliratban
        # (PicasaMenuBar.qml)
        assert _child(window, "viewerMenuDelete").property("text").endswith("\tDelete")
        _close_menu(window, qt_app)


class TestViewerContextMenuBehaviour:
    def test_rotate_right_turns_the_shown_photo(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _open_viewer(window, qt_app, row=0)
        menu = _open_menu(window, qt_app)
        _do_photo_op(
            controller, qt_app,
            lambda: QMetaObject.invokeMethod(
                menu, "triggerRotateRight", Qt.ConnectionType.DirectConnection
            ),
        )
        assert _child(window, "viewerImage").property("iniSteps") == 1
        _close_menu(window, qt_app)

    def test_hide_label_follows_the_hidden_state(self, qml_app, qt_app):
        """Elrejtés ↔ Megjelenítés UGYANAZON a helyen vált (spec A.2) — nem
        külön tétel, a menü magassága állandó marad.

        A menü `hidden` bemenetét közvetlenül állítjuk: a rejtett kép
        kiesik a rácsból (`toggleHiddenRows` után a sorindexek elcsúsznak),
        így a modellen keresztül nem lehetne stabilan a rejtett képre
        állni — a felirat-váltás szabálya viszont pont a bemenettől függ."""
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app, row=0)
        menu = _open_menu(window, qt_app)
        item = _child(window, "viewerMenuHide")

        menu.setProperty("hidden", False)
        qt_app.processEvents()
        shown_label = item.property("text")

        menu.setProperty("hidden", True)
        qt_app.processEvents()
        hidden_label = item.property("text")
        _close_menu(window, qt_app)

        assert shown_label and hidden_label
        assert shown_label != hidden_label

    def test_back_to_library_closes_the_viewer(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _open_viewer(window, qt_app)
        menu = _open_menu(window, qt_app)
        QMetaObject.invokeMethod(
            menu, "triggerBackToLibrary", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert window.property("viewerOpen") is False


class TestSaveCommandsInTheViewer:
    """#422: a mentés-szemantika a nézőben is elérhető — ugyanaz a motor,
    mint a rácsban és a menüsávban. Egy parancs, egy út."""

    def test_they_are_state_dependent_not_placeholders(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        menu = _child(window, "viewerContextMenu")

        menu.setProperty("hasEdits", False)
        qt_app.processEvents()
        assert _child(window, "viewerMenuSave").property("enabled") is False

        menu.setProperty("hasEdits", True)
        qt_app.processEvents()
        assert _child(window, "viewerMenuSave").property("enabled") is True
        assert (
            _child(window, "viewerMenuUndoAllEdits").property("enabled") is True
        )

    def test_revert_follows_the_backup(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        menu = _child(window, "viewerContextMenu")

        menu.setProperty("hasBackup", True)
        qt_app.processEvents()

        assert _child(window, "viewerMenuRevert").property("enabled") is True

    def test_reset_faces_is_live(self, qml_app, qt_app):
        window, _controller, _engine = qml_app

        assert _child(window, "viewerMenuResetFaces").property("enabled") is True

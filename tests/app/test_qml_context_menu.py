"""QML-funkcionális tesztek: PhotoContextMenu önálló komponens + a
ThumbDelegate jobbklikk-jelzése (#15).

A rácsba kötés (popup megnyitása a jobbklikk pozíciójában, a jelek
FileOpsControllerhez kapcsolása) az integrátor feladata — itt a
komponenseket önmagukban, a `tests/app/test_qml_editor_panel.py` mintája
szerint teszteljük.
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

# élő Python-referencia nélkül a JS-motor GC-je bármikor eltávolítaná a
# QML-ből létrehozott gyökér-objektumokat — CppOwnership-re váltva és itt
# megtartva éljük túl a teszt-futást (test_qml_editor_panel.py mintája).
_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


class TestPhotoContextMenu:
    # #422: az „Átnevezés…" KIKERÜLT — az eredetiben nem ebben a menüben
    # van, hanem a Fájl menüben (F2), ahol nálunk is működik.
    ITEMS = {
        "contextMenuOpen": "openRequested",
        "contextMenuRotateRight": "rotateRightRequested",
        "contextMenuRotateLeft": "rotateLeftRequested",
        "contextMenuMove": "moveRequested",
        "contextMenuOpenFile": "openFileRequested",
        "contextMenuLocate": "locateRequested",
        "contextMenuDelete": "deleteRequested",
        "contextMenuCopyFullPath": "copyFullPathRequested",
        "contextMenuProperties": "propertiesRequested",
    }

    # a spec 2. szakaszának teljes tételsora, sorrendben
    EXPECTED_ORDER = [
        "contextMenuOpen",
        "contextMenuAddToAlbum",
        "contextMenuRemoveFromAlbum",
        "contextMenuRotateRight",
        "contextMenuRotateLeft",
        "contextMenuUndoAllEdits",
        "contextMenuHide",
        "contextMenuMove",
        "contextMenuSplitFolder",
        "contextMenuOpenFile",
        "contextMenuOpenWith",
        "contextMenuSave",
        "contextMenuRevert",
        "contextMenuLocate",
        "contextMenuDelete",
        "contextMenuCopyFullPath",
        "contextMenuUploadToWebAlbums",
        "contextMenuBlockUpload",
        "contextMenuResetFaces",
        "contextMenuProperties",
    ]

    # amiknek még nincs háttere — a Picasa ezeket is MEGJELENÍTI, szürkén
    # Ezeknek MA sincs mögöttük működés — látszanak, de szürkék. A
    # Mentés / Visszaállítás / Összes szerkesztés visszavonása alapból
    # szintén szürke, de NEM helyfoglaló: állapotfüggő (#422), ezért a
    # saját tesztjük fedi őket (test_photo_menu_commands.py).
    EXPECTED_DISABLED = [
        "contextMenuSplitFolder",
        "contextMenuOpenWith",
        "contextMenuUploadToWebAlbums",
        "contextMenuBlockUpload",
    ]

    def _make_menu(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\nPhotoContextMenu { objectName: "menu" }\n',
        )

    def test_all_items_present_with_object_names(self, qml_engine):
        menu = self._make_menu(qml_engine)
        for name in self.ITEMS:
            assert menu.findChild(QObject, name) is not None, f"{name} nem található"

    @pytest.mark.parametrize("item_name,signal_name", list(ITEMS.items()))
    def test_item_trigger_emits_matching_signal(
        self, qml_engine, qt_app, item_name, signal_name
    ):
        menu = self._make_menu(qml_engine)
        events = []
        getattr(menu, signal_name).connect(lambda: events.append(True))
        item = menu.findChild(QObject, item_name)
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert events == [True]

    @pytest.mark.parametrize("item_name,signal_name", list(ITEMS.items()))
    def test_item_trigger_does_not_emit_other_signals(
        self, qml_engine, qt_app, item_name, signal_name
    ):
        menu = self._make_menu(qml_engine)
        other_events = []
        for name in self.ITEMS.values():
            if name != signal_name:
                getattr(menu, name).connect(lambda n=name: other_events.append(n))
        item = menu.findChild(QObject, item_name)
        QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert other_events == []


    def test_every_original_command_is_present_in_order(self, qml_engine):
        """#422: az eredeti `AlbumPhoto` menüosztály tételsora, a
        `docs/specs/ui-audit-context-menus.md` 2. szakaszának sorrendjében."""
        menu = self._make_menu(qml_engine)
        found = [
            child.objectName()
            for child in menu.findChildren(QObject)
            if child.objectName() in self.EXPECTED_ORDER
        ]
        assert found == self.EXPECTED_ORDER

    def test_rename_is_gone_from_this_menu(self, qml_engine):
        """Paritás: az eredetiben az átnevezés a Fájl menüben van (F2)."""
        menu = self._make_menu(qml_engine)
        assert menu.findChild(QObject, "contextMenuRename") is None

    def test_reset_faces_is_live(self, qml_engine):
        """#422: az „Arcok alaphelyzetbe állítása" már működik — nem
        helyfoglaló többé."""
        menu = self._make_menu(qml_engine)
        item = menu.findChild(QObject, "contextMenuResetFaces")
        assert item is not None
        assert item.property("enabled") is True

    def test_unbacked_commands_are_shown_but_disabled(self, qml_engine):
        """Az inaktív tétel is tétel: LÁTSZIK, de szürke (spec 5.1.)."""
        menu = self._make_menu(qml_engine)
        for name in self.EXPECTED_DISABLED:
            item = menu.findChild(QObject, name)
            assert item is not None, f"{name} hiányzik"
            assert item.property("enabled") is False, f"{name} nem szürke"

    def test_first_item_is_bold(self, qml_engine):
        """A félkövér első tétel = a duplakattintás művelete (spec 5.3.)."""
        menu = self._make_menu(qml_engine)
        item = menu.findChild(QObject, "contextMenuOpen")
        assert item.property("font").bold() is True

    def test_delete_shortcut_is_ctrl_delete_in_the_grid(self, qml_engine):
        """A rácsban `Ctrl+Delete`, a nézőben `Delete` (spec 3.)."""
        menu = self._make_menu(qml_engine)
        text = menu.findChild(QObject, "contextMenuDelete").property("text")
        assert text.endswith("\tCtrl+Delete")

    def test_hide_label_switches_instead_of_a_checkmark(self, qml_engine, qt_app):
        """Elrejtés ↔ Megjelenítés UGYANAZON a helyen vált (spec A.2) — az
        eredeti nem pipát tesz, hanem feliratot cserél."""
        menu = self._make_menu(qml_engine)
        item = menu.findChild(QObject, "contextMenuHide")
        menu.setProperty("hideChecked", False)
        qt_app.processEvents()
        shown = item.property("text")
        menu.setProperty("hideChecked", True)
        qt_app.processEvents()
        hidden = item.property("text")
        assert shown and hidden and shown != hidden


class TestThumbDelegateContextMenu:
    """#15: a ThumbDelegate jobbklikkre `contextMenuRequested`-et küld, a
    bal-klikk (`chosen`) viselkedése változatlan marad.

    A valós egéresemény-szintetizálás offscreen módban nem megbízható (a
    #53-as GIL-jegyzet szerint is), ezért — a `TestLasso.applyLasso`
    mintájára (test_qml_functional.py) — a `handleClicked` hívható
    QML-függvényt hívjuk közvetlenül, nem a MouseArea nyers `clicked`
    jelét szintetizáljuk."""

    def _make_delegate(self, qml_engine):
        import picasapy.app.application as app_module

        comp = QQmlComponent(
            qml_engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
            ),
        )
        delegate = comp.createWithInitialProperties(
            {
                "name": "a.jpg",
                "thumbUrl": "image://thumbs/1",
                "star": False,
                "caption": "",
                "isVideo": False,
                "index": 3,
                "keywords": "",
                "resolution": "320x160",
            }
        )
        assert comp.errors() == [], [e.toString() for e in comp.errors()]
        assert delegate is not None
        QQmlEngine.setObjectOwnership(delegate, QQmlEngine.ObjectOwnership.CppOwnership)
        _KEEPALIVE.append(comp)
        _KEEPALIVE.append(delegate)
        return delegate

    @staticmethod
    def _click(qt_app, delegate, button, modifiers=0, x=5, y=5):
        from PySide6.QtCore import Q_ARG

        QMetaObject.invokeMethod(
            delegate, "handleClicked", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", button), Q_ARG("QVariant", modifiers),
            Q_ARG("QVariant", x), Q_ARG("QVariant", y),
        )
        qt_app.processEvents()

    def test_mouse_area_accepts_right_button(self, qml_engine):
        delegate = self._make_delegate(qml_engine)
        mouse_area = delegate.findChild(QObject, "thumbMouseArea")
        assert mouse_area is not None
        accepted = mouse_area.property("acceptedButtons").value
        assert accepted & Qt.MouseButton.RightButton.value
        assert accepted & Qt.MouseButton.LeftButton.value

    def test_right_click_emits_context_menu_requested(self, qml_engine, qt_app):
        delegate = self._make_delegate(qml_engine)
        requests = []
        delegate.contextMenuRequested.connect(
            lambda index, x, y: requests.append((index, x, y))
        )
        self._click(qt_app, delegate, Qt.MouseButton.RightButton.value, x=7, y=9)
        assert requests == [(3, 7, 9)]

    def test_right_click_does_not_emit_chosen(self, qml_engine, qt_app):
        delegate = self._make_delegate(qml_engine)
        chosen = []
        delegate.chosen.connect(lambda index, mods: chosen.append((index, mods)))
        self._click(qt_app, delegate, Qt.MouseButton.RightButton.value)
        assert chosen == []

    def test_left_click_still_emits_chosen(self, qml_engine, qt_app):
        # regressziós védőháló: a jobbklikk-jel bevezetése nem törheti meg
        # a meglévő bal-klikkes kiválasztást
        delegate = self._make_delegate(qml_engine)
        chosen = []
        delegate.chosen.connect(lambda index, mods: chosen.append((index, mods)))
        self._click(qt_app, delegate, Qt.MouseButton.LeftButton.value)
        assert chosen == [(3, 0)]

    def test_left_click_does_not_emit_context_menu_requested(self, qml_engine, qt_app):
        delegate = self._make_delegate(qml_engine)
        requests = []
        delegate.contextMenuRequested.connect(
            lambda index, x, y: requests.append((index, x, y))
        )
        self._click(qt_app, delegate, Qt.MouseButton.LeftButton.value)
        assert requests == []

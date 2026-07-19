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
    ITEMS = {
        "contextMenuRename": "renameRequested",
        "contextMenuMove": "moveRequested",
        "contextMenuDelete": "deleteRequested",
        "contextMenuLocate": "locateRequested",
    }

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

"""QML-funkcionális tesztek: rejtett képek (#17).

Elrejtés a kijelölésre (menü/kontextusmenü útja: toggleHiddenSelection),
a rács alapból nem mutatja a rejtettet, a Nézet → Rejtett képek kapcsolóval
félig áttetszően igen (ThumbDelegate.isHidden → thumbFrame.opacity).
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


class TestHiddenInMain:
    def test_menu_item_enabled_and_checkable(self, qml_app):
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "menuViewHidden")
        assert item is not None
        assert item.property("enabled") is True
        assert item.property("checkable") is True
        assert item.property("checked") is False

    def test_hide_selection_removes_from_grid_and_clears_selection(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        QMetaObject.invokeMethod(
            window, "toggleHiddenSelection", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert controller.photos.rowCount() == 1
        selected = window.property("selectedIndexes")
        if hasattr(selected, "toVariant"):  # a QML var lista QJSValue-ként jön
            selected = selected.toVariant()
        assert list(selected or []) == []
        assert window.property("selectedIndex") == -1
        ini_text = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "hidden=yes" in ini_text

    def test_show_hidden_reveals_with_hidden_flag(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        QMetaObject.invokeMethod(
            window, "toggleHiddenSelection", Qt.ConnectionType.DirectConnection
        )
        controller.setShowHidden(True)
        qt_app.processEvents()
        assert controller.photos.rowCount() == 2
        hidden_flags = [
            controller.photos.itemAt(i)["hidden"] for i in range(2)
        ]
        assert hidden_flags.count(True) == 1

    def test_context_menu_has_hide_item(self, qml_app):
        window, controller, lib, engine = qml_app
        item = window.findChild(QObject, "contextMenuHide")
        assert item is not None
        assert item.property("checkable") is True


class TestThumbDelegateHiddenDimming:
    @pytest.fixture
    def qml_engine(self, qt_app):
        import picasapy.app.application as app_module

        engine = QQmlEngine()
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        yield engine
        engine.deleteLater()

    def _make(self, engine, is_hidden):
        component = QQmlComponent(engine)
        component.setData(
            (
                "import QtQuick\nimport PicasaPy 1.0\n"
                "ThumbDelegate { index: 0; name: \"a\"; thumbUrl: \"\";"
                " star: false; caption: \"\"; isVideo: false;"
                " keywords: \"\"; resolution: \"\"; isHidden: %s }\n"
                % ("true" if is_hidden else "false")
            ).encode("utf-8"),
            QUrl(),
        )
        obj = component.create()
        assert obj is not None, [e.toString() for e in component.errors()]
        QQmlEngine.setObjectOwnership(
            obj, QQmlEngine.ObjectOwnership.CppOwnership
        )
        _KEEPALIVE.extend([component, obj])
        return obj

    def test_hidden_thumb_semi_transparent(self, qml_engine, qt_app):
        cell = self._make(qml_engine, is_hidden=True)
        qt_app.processEvents()
        frame = cell.findChild(QObject, "thumbFrame")
        assert frame.property("opacity") < 1

    def test_visible_thumb_fully_opaque(self, qml_engine, qt_app):
        cell = self._make(qml_engine, is_hidden=False)
        qt_app.processEvents()
        frame = cell.findChild(QObject, "thumbFrame")
        assert frame.property("opacity") == 1

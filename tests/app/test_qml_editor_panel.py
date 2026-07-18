"""QML-funkcionális tesztek: EditorPanel és CropOverlay önálló komponensek.

A Main.qml-be való bekötés az integrátor feladata (19-es issue #2) — itt a
két komponenst önmagában, a PicasaPy modulon (`import PicasaPy 1.0`)
keresztül töltjük be, a tests/app/test_qml_functional.py mintája szerint
(pl. TestThumbCaption.test_thumb_delegate_shows_filename_caption).
"""

import pytest
from PySide6.QtCore import QMetaObject, QObject, QRectF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

# a QML-ből létrehozott gyökér-objektumok élő Python-referenciák nélkül a
# JS-motor tulajdonába kerülnek és a GC bármikor eltávolíthatja őket —
# CppOwnership-re váltva és itt megtartva éljük túl a teszt-futást.
_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    """QML-forrás betöltése inline szövegként (nincs saját fájl-URL-je)."""
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


class TestEditorPanelButtons:
    TOOLS = ["crop", "tilt", "redeye", "enhance", "autolight", "autocolor"]
    OBJECT_NAMES = {
        "crop": "editToolCrop",
        "tilt": "editToolTilt",
        "redeye": "editToolRedeye",
        "enhance": "editToolEnhance",
        "autolight": "editToolAutolight",
        "autocolor": "editToolAutocolor",
    }
    ACTIVE_PROPS = {
        "crop": "cropActive",
        "tilt": "tiltActive",
        "redeye": "redeyeActive",
        "enhance": "enhanceActive",
        "autolight": "autolightActive",
        "autocolor": "autocolorActive",
    }

    def _make_panel(self, qml_engine):
        return _load(
            qml_engine,
            'import QtQuick\nimport PicasaPy 1.0\nEditorPanel { objectName: "panel" }\n',
        )

    def test_all_buttons_present_with_object_names(self, qml_engine):
        panel = self._make_panel(qml_engine)
        for tool in self.TOOLS:
            name = self.OBJECT_NAMES[tool]
            button = panel.findChild(QObject, name)
            assert button is not None, f"{name} nem található"

    @pytest.mark.parametrize("tool", TOOLS)
    def test_tool_click_emits_tool_activated(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        activated = []
        panel.toolActivated.connect(lambda t: activated.append(t))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert activated == [tool]

    def test_crop_click_also_emits_crop_requested(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        requested = []
        panel.cropRequested.connect(lambda: requested.append(True))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg("crop"),
        )
        qt_app.processEvents()
        assert requested == [True]

    def test_non_crop_click_does_not_emit_crop_requested(self, qml_engine, qt_app):
        panel = self._make_panel(qml_engine)
        requested = []
        panel.cropRequested.connect(lambda: requested.append(True))
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg("redeye"),
        )
        qt_app.processEvents()
        assert requested == []

    @pytest.mark.parametrize("tool", TOOLS)
    def test_active_state_toggles_and_reflects_on_button(self, qml_engine, qt_app, tool):
        panel = self._make_panel(qml_engine)
        prop = self.ACTIVE_PROPS[tool]
        button = panel.findChild(QObject, self.OBJECT_NAMES[tool])

        assert panel.property(prop) is False
        assert button.property("active") is False

        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert panel.property(prop) is True
        assert button.property("active") is True  # benyomott állapot

        # ismételt kattintás visszakapcsol
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            *_string_arg(tool),
        )
        qt_app.processEvents()
        assert panel.property(prop) is False
        assert button.property("active") is False


def _string_arg(value):
    """Q_ARG segéd — a PySide6 verziók között eltér a string-argumentum
    átadásának preferált formája, ezért itt egyszerű változó-listát adunk
    vissza a QMetaObject.invokeMethod hívásokhoz."""
    from PySide6.QtCore import Q_ARG

    return (Q_ARG("QVariant", value),)


class TestCropOverlay:
    def _make_overlay(self, qml_engine, extra=""):
        return _load(
            qml_engine,
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'CropOverlay {{ width: 200; height: 100; {extra} }}\n',
        )

    def test_croprect_default_matches_selection_geometry(self, qml_engine):
        # #51: Picasa-hűen NINCS elő-kijelölés — a keret rejtve indul,
        # a kijelölést a felhasználó húzással hozza létre.
        overlay = self._make_overlay(qml_engine)
        selection = overlay.findChild(QObject, "cropSelection")
        assert selection is not None
        assert overlay.property("hasSelection") is False
        assert selection.property("visible") is False

    def test_croprect_change_updates_selection_geometry(self, qml_engine, qt_app):
        overlay = self._make_overlay(qml_engine)
        selection = overlay.findChild(QObject, "cropSelection")
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        qt_app.processEvents()
        assert round(selection.property("x")) == 50
        assert round(selection.property("y")) == 25
        assert round(selection.property("width")) == 100
        assert round(selection.property("height")) == 50

    def test_enter_emits_accepted_with_current_rect(self, qml_engine, qt_app):
        overlay = self._make_overlay(
            qml_engine,
            extra="cropRect: Qt.rect(0.1, 0.2, 0.3, 0.4); hasSelection: true",
        )
        accepted = []
        overlay.accepted.connect(lambda r: accepted.append(r))
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert len(accepted) == 1
        r = accepted[0]
        assert round(r.x(), 2) == 0.1
        assert round(r.y(), 2) == 0.2
        assert round(r.width(), 2) == 0.3
        assert round(r.height(), 2) == 0.4

    def test_escape_emits_cancelled(self, qml_engine, qt_app):
        overlay = self._make_overlay(qml_engine)
        cancelled = []
        overlay.cancelled.connect(lambda: cancelled.append(True))
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert cancelled == [True]

    def test_escape_does_not_emit_accepted(self, qml_engine, qt_app):
        overlay = self._make_overlay(qml_engine)
        accepted = []
        overlay.accepted.connect(lambda r: accepted.append(r))
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert accepted == []

    def test_object_names_present(self, qml_engine):
        overlay = self._make_overlay(qml_engine)
        assert overlay.objectName() == "cropOverlay"
        assert overlay.findChild(QObject, "cropSelection") is not None

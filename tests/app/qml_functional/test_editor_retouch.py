"""Retusálás eszközének QML- és vezérlő-összekötési próbái."""

from PySide6.QtCore import QObject
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers


class TestEditorRetouch(EditorTestHelpers):
    """A retusáló eszköz megnyitása, szerkesztése és visszavonása."""

    def test_retouch_tile_opens_tool_and_click_area_appears(
        self, qml_app, qt_app, tmp_path
    ):
        """#148: a Retusálás csempe megnyitja a módot, és a kép feletti
        kattintás-terület (retouchClickArea) csak ekkor látszik."""
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        area = window.findChild(QObject, "retouchClickArea")
        assert area is not None, "retouchClickArea nem található"
        assert area.property("visible") is False
        QMetaObject.invokeMethod(
            panel, "handleToolClick", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "retouch"),
        )
        qt_app.processEvents()
        assert panel.property("retouchActive") is True
        assert area.property("visible") is True

    def test_retouch_apply_writes_patch_and_closes_tool(
        self, qml_app, qt_app, tmp_path
    ):
        """#445: kétkattintásos, irányított klónozás — a cél kijelölése,
        forrás-előnézet, véglegesítés, majd Alkalmaz."""
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.beginRetouchPatch(0.5, 0.5)
        qt_app.processEvents()
        assert panel.property("retouchPatchPending") is True
        edit.previewRetouchSource(0.2, 0.2)
        edit.commitRetouchPatch(0.2, 0.2)
        qt_app.processEvents()
        assert panel.property("retouchRegionCount") == 1
        assert panel.property("retouchPatchPending") is False
        apply_button = window.findChild(QObject, "retouchApplyButton")
        assert apply_button is not None
        assert apply_button.property("enabled") is True
        from PySide6.QtCore import QMetaObject, Qt

        QMetaObject.invokeMethod(
            apply_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=retouch=2," in ini_text
        assert panel.property("retouchActive") is False

    def test_retouch_cancel_discards_pending_patches(
        self, qml_app, qt_app, tmp_path
    ):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.beginRetouchPatch(0.5, 0.5)
        edit.commitRetouchPatch(0.2, 0.2)
        qt_app.processEvents()
        cancel_button = window.findChild(QObject, "retouchCancelButton")
        from PySide6.QtCore import QMetaObject, Qt

        QMetaObject.invokeMethod(
            cancel_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("retouchActive") is False
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        assert not ini_path.exists() or "retouch" not in ini_path.read_text(
            encoding="utf-8"
        )

    def test_retouch_undo_redo_reset_buttons(self, qml_app, qt_app, tmp_path):
        """#445: Undo Patch/Redo Patch/Reset — a retusálás pufferén, NEM a
        globális Visszavonás-vermen."""
        from PySide6.QtCore import QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.beginRetouchPatch(0.3, 0.3)
        edit.commitRetouchPatch(0.4, 0.4)
        qt_app.processEvents()

        undo_button = window.findChild(QObject, "retouchUndoPatchButton")
        redo_button = window.findChild(QObject, "retouchRedoPatchButton")
        reset_button = window.findChild(QObject, "retouchResetButton")
        assert undo_button.property("enabled") is True
        assert redo_button.property("enabled") is False

        QMetaObject.invokeMethod(
            undo_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("retouchRegionCount") == 0
        assert redo_button.property("enabled") is True

        QMetaObject.invokeMethod(
            redo_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("retouchRegionCount") == 1

        QMetaObject.invokeMethod(
            reset_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("retouchRegionCount") == 0

    def test_retouch_brush_size_slider(self, qml_app, qt_app, tmp_path):
        """#445: a "Brush Size" csúszka [1..100] a kontroller `brushSize`
        tulajdonságát vezérli."""
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "retouchBrushSizeSlider")
        assert slider is not None
        assert slider.property("from") == 1
        assert slider.property("to") == 100
        edit = self._edit_controller(engine)
        edit.setBrushSize(75)
        qt_app.processEvents()
        assert panel.property("brushSize") == 75
        assert slider.property("value") == 75

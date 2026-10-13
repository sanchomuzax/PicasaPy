"""A képre írt szöveg QML-eszközének funkcionális próbái."""

import pytest
from PySide6.QtCore import QObject
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers


class TestEditorTextTool(EditorTestHelpers):
    """Felirat szerkesztése, megjelenése és stílusvezérlői."""

    def test_text_tile_opens_tool_and_click_area_appears(self, qml_app, qt_app):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        area = window.findChild(QObject, "textClickArea")
        assert area is not None, "textClickArea nem található"
        assert area.property("visible") is False
        QMetaObject.invokeMethod(
            panel, "handleToolClick", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "text"),
        )
        qt_app.processEvents()
        assert panel.property("textActive") is True
        assert area.property("visible") is True

    def test_text_apply_writes_text_and_textactive(self, qml_app, qt_app, tmp_path):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        field = window.findChild(QObject, "textContentField")
        assert field is not None, "textContentField nem található"
        field.setProperty("text", "Nyaralás")
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.previewTextPlacement(0.3, 0.6)
        qt_app.processEvents()
        apply_button = window.findChild(QObject, "textApplyButton")
        assert apply_button.property("enabled") is True
        from PySide6.QtCore import QMetaObject, Qt

        QMetaObject.invokeMethod(
            apply_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "text=1;" in ini_text
        assert "Nyaralás" in ini_text
        assert "textactive=1" in ini_text
        assert panel.property("textActive") is False

    def test_copy_caption_button_disabled_without_caption(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        button = window.findChild(QObject, "textCopyCaptionButton")
        assert button is not None, "textCopyCaptionButton nem található"
        assert button.property("enabled") is False

    def test_copy_caption_button_fills_text_field(self, qml_app, qt_app, tmp_path):
        from support.qt_wait import wait_for_photo_op
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app
        wait_for_photo_op(
            controller, lambda: controller.setCaption(0, "Nyári kirándulás"),
            qt_app=qt_app,
        )
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        button = window.findChild(QObject, "textCopyCaptionButton")
        assert button.property("enabled") is True
        QMetaObject.invokeMethod(
            button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        field = window.findChild(QObject, "textContentField")
        assert field.property("text") == "Nyári kirándulás"

    def test_copy_caption_asks_before_overwriting_typed_text(
        self, qml_app, qt_app
    ):
        """#465 4. pont: a felirat bemásolása FELÜLÍRJA a beírt szöveget —
        az eredeti Picasa erre kimondottan figyelmeztet („This operation is
        not undoable"), mert a beírt szöveg nem szerezhető vissza."""
        from support.qt_wait import wait_for_photo_op
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app
        wait_for_photo_op(
            controller, lambda: controller.setCaption(0, "Nyári kirándulás"),
            qt_app=qt_app,
        )
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        panel.setProperty("textDraftContent", "Kézzel írt szöveg")
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            window.findChild(QObject, "textCopyCaptionButton"),
            "buttonClicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        confirm = window.findChild(QObject, "copyCaptionConfirmDialog")
        assert confirm is not None and confirm.property("visible") is True
        assert panel.property("textDraftContent") == "Kézzel írt szöveg", (
            "a szöveg a megerősítés ELŐTT íródott felül"
        )

        QMetaObject.invokeMethod(
            window.findChild(QObject, "copyCaptionConfirmYesButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        assert panel.property("textDraftContent") == "Nyári kirándulás"

    def test_remove_all_text_button_clears_saved_overlay(
        self, qml_app, qt_app, tmp_path
    ):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        field = window.findChild(QObject, "textContentField")
        field.setProperty("text", "Nyaralás")
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.previewTextPlacement(0.3, 0.6)
        qt_app.processEvents()
        apply_button = window.findChild(QObject, "textApplyButton")
        QMetaObject.invokeMethod(
            apply_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert edit.property("hasTextOverlay") is True
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        remove_button = window.findChild(QObject, "textRemoveAllButton")
        assert remove_button is not None, "textRemoveAllButton nem található"
        assert remove_button.property("enabled") is True
        QMetaObject.invokeMethod(
            remove_button, "buttonClicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert edit.property("hasTextOverlay") is False
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "text=" not in ini_text

    def test_outline_and_opacity_controls_update_controller(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)

        thickness_slider = window.findChild(QObject, "textOutlineThicknessSlider")
        assert thickness_slider is not None
        # #2271: a csúszka mértékegysége [0, 1] lett — az eredetit követve
        # (`ytSliderHandler`, ami a sáv hosszához normalizál). A 4-es érték
        # a csúszka felső határán túl volt, ezért 1,0-ra vágódott.
        thickness_slider.setProperty("value", 0.5)
        QMetaObject.invokeMethod(
            thickness_slider, "moved", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert edit.property("textOutlineThickness") == pytest.approx(0.5)

        opacity_slider = window.findChild(QObject, "textOpacitySlider")
        assert opacity_slider is not None
        opacity_slider.setProperty("value", 0.5)
        QMetaObject.invokeMethod(
            opacity_slider, "moved", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert edit.property("textOpacity") == pytest.approx(0.5)

        fill_disabled_check = window.findChild(QObject, "textFillDisabledCheck")
        assert fill_disabled_check is not None
        fill_disabled_check.setProperty("checked", True)
        QMetaObject.invokeMethod(
            fill_disabled_check, "toggled", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert edit.property("textFillEnabled") is False

    @staticmethod
    def _find_item_by_name(root, name):
        """`QObject.findChild` nem találja meg a `Repeater`-rel gyártott
        delegate-eket (a QObject-tulajdonjoguk a Repeateré marad, a
        `parentItem()` viszont a szülő-itemre mutat — PySide6/Qt Quick
        részlet) — ezért a vizuális `childItems()`-fán kell keresni."""
        if root.objectName() == name:
            return root
        for child in root.childItems():
            found = TestEditorTextTool._find_item_by_name(child, name)
            if found is not None:
                return found
        return None

    def test_color_swatches_update_controller(self, qml_app, qt_app):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)

        fill_row = window.findChild(QObject, "textFillColorSwatches")
        assert fill_row is not None
        fill_swatch = self._find_item_by_name(fill_row, "textFillColorSwatchesSwatch2")
        assert fill_swatch is not None, "textFillColorSwatchesSwatch2 nem található"
        assert fill_swatch.property("color").name() == "#ff0000"

        QMetaObject.invokeMethod(
            fill_row, "colorPicked", Qt.ConnectionType.DirectConnection,
            Q_ARG(str, "#ff0000"),
        )
        qt_app.processEvents()
        assert edit.property("textFillColor") == "#ff0000"

        outline_row = window.findChild(QObject, "textOutlineColorSwatches")
        assert outline_row is not None
        outline_swatch = self._find_item_by_name(
            outline_row, "textOutlineColorSwatchesSwatch3"
        )
        assert outline_swatch is not None
        assert outline_swatch.property("color").name() == "#ffff00"

        QMetaObject.invokeMethod(
            outline_row, "colorPicked", Qt.ConnectionType.DirectConnection,
            Q_ARG(str, "#ffff00"),
        )
        qt_app.processEvents()
        assert edit.property("textOutlineColor") == "#ffff00"

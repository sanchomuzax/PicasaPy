"""Retusálás eszközének QML- és vezérlő-összekötési próbái."""

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
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

    def test_retouch_cancel_with_pending_target_keeps_tool_open_then_closes(
        self, qml_app, qt_app, tmp_path
    ):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.setBrushSize(31)
        edit.beginRetouchPatch(0.5, 0.5)
        qt_app.processEvents()
        assert panel.property("retouchPatchPending") is True

        cancel_button = window.findChild(QObject, "retouchCancelButton")
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=QPoint(
                round(cancel_button.mapToScene(cancel_button.boundingRect().center()).x()),
                round(cancel_button.mapToScene(cancel_button.boundingRect().center()).y()),
            ),
        )
        qt_app.processEvents()

        assert panel.property("retouchPatchPending") is False
        assert panel.property("retouchActive") is True
        slider = window.findChild(QObject, "retouchBrushSizeSlider")
        assert slider.property("value") == 31

        # A függő állapot sora eltűnt, a gombsor feljebb csúszhatott: a
        # második kattintás helyét újra a QML-geometriából számoljuk.
        second = cancel_button.mapToScene(cancel_button.boundingRect().center())
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=QPoint(round(second.x()), round(second.y())),
        )
        qt_app.processEvents()
        assert panel.property("retouchActive") is False

        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        assert slider.property("value") == 31

    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_retouch_neutral_panel_click_discards_pending_target(
        self, qml_app, qt_app, height_delta
    ):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        window.resize(window.width(), window.height() + height_delta)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.beginRetouchPatch(0.5, 0.5)
        qt_app.processEvents()
        assert panel.property("retouchPatchPending") is True

        scroll = window.findChild(QObject, "editorModeToolScroll")
        cancel_button = window.findChild(QObject, "retouchCancelButton")
        apply_button = window.findChild(QObject, "retouchApplyButton")
        apply_center = apply_button.mapToScene(apply_button.boundingRect().center())
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=QPoint(round(apply_center.x()), round(apply_center.y())),
        )
        qt_app.processEvents()
        assert panel.property("retouchPatchPending") is True

        cancel_center = cancel_button.mapToItem(
            scroll, cancel_button.boundingRect().center()
        )
        # A gombsor bal oldali, üres panelmargójára kattintunk. A pontot a
        # tényleges QML-geometriából számoljuk, nem rögzített képernyőpontból.
        neutral = scroll.mapToScene(QPointF(4, cancel_center.y()))
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=QPoint(round(neutral.x()), round(neutral.y())),
        )
        qt_app.processEvents()

        assert panel.property("retouchPatchPending") is False
        assert panel.property("retouchActive") is True

        area = window.findChild(QObject, "retouchClickArea")
        first_click = area.mapToScene(QPointF(area.width() * 0.30, area.height() * 0.45))
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=QPoint(round(first_click.x()), round(first_click.y())),
        )
        qt_app.processEvents()
        assert panel.property("retouchPatchPending") is True

    def test_retouch_click_below_buttons_discards_pending_target(
        self, qml_app, qt_app
    ):
        """#7426: az eredetiben a gombsor alatti üres panelsávra kattintás
        (job-949 __20, a (140, 600) pont) is eldobja a függő foltot."""
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("retouchActive", True)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        edit.beginRetouchPatch(0.5, 0.5)
        qt_app.processEvents()
        assert panel.property("retouchPatchPending") is True

        scroll = window.findChild(QObject, "editorModeToolScroll")
        cancel_button = window.findChild(QObject, "retouchCancelButton")
        buttons_bottom = cancel_button.mapToItem(
            scroll, QPointF(0, cancel_button.height())
        ).y()
        assert buttons_bottom + 20 < scroll.height(), (
            "a próba a gombsor alatti üres sávot méri; ilyen sáv nincs"
        )
        below = scroll.mapToScene(
            QPointF(scroll.width() / 2, (buttons_bottom + scroll.height()) / 2)
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            pos=QPoint(round(below.x()), round(below.y())),
        )
        qt_app.processEvents()

        assert panel.property("retouchPatchPending") is False
        assert panel.property("retouchActive") is True

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

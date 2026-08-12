"""QML-funkcionális tesztek: szerkesztő — EditorPanel/CropOverlay ↔
EditController ↔ ini bekötés, és a néző mappahatáron belüli lapozása
(#155: a korábbi `test_qml_functional.py` egyik szelete, processzenkénti
izolációhoz)."""

import pytest
from PySide6.QtCore import QObject

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg


class TestEditorWiring:
    """A #19-es bekötés: EditorPanel/CropOverlay ↔ EditController ↔ ini."""

    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def _edit_controller(self, engine):
        return engine.rootContext().contextProperty("editController")

    def test_viewer_open_starts_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        image = window.findChild(QObject, "viewerImage")
        assert image.property("source").toString().startswith("image://editpreview/")

    def test_viewer_close_ends_edit_session(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert self._edit_controller(engine).property("previewSource") == ""

    def test_panel_toggle_writes_ini_and_syncs_state(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "autolight"),
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[a.jpg]" in ini_text
        assert "autolight=1" in ini_text
        # a panel állapota az EditController igazságforrásából szinkronizált:
        # az egygombos javítás gombja tiltott, amíg ő a lánc utolsó eleme (#116)
        assert panel.property("autolightEnabled") is False
        # a kép forrása új ?rev=-et kap → az előnézet frissül
        image = window.findChild(QObject, "viewerImage")
        assert "?rev=" in image.property("source").toString()

    def test_crop_accept_persists_and_advances(self, qml_app, qt_app, tmp_path):
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        assert overlay is not None, "cropOverlay nem található"
        assert overlay.property("visible") is True
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "crop64=1," in ini_text
        # Enter-flow: elfogadás után a néző a következő képre lép, a
        # vágó-mód megmarad (sorozat-vágás)
        assert viewer.property("currentIndex") == 1
        assert panel.property("cropActive") is True

    def test_tilt_drag_previews_live_then_commits_on_release(
        self, qml_app, qt_app, tmp_path
    ):
        """#72: húzás közben élő előnézet, ini-mentés nélkül; elengedéskor ír."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        image = window.findChild(QObject, "viewerImage")
        before_source = image.property("source").toString()
        ini_path = tmp_path / "kepek" / ".picasa.ini"

        slider.setProperty("value", 0.3)
        qt_app.processEvents()
        assert not ini_path.exists(), "húzás közben nem szabadna ini-be írni"
        assert image.property("source").toString() != before_source

        slider.setProperty("pressed", True)
        slider.setProperty("pressed", False)
        qt_app.processEvents()
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,0.300000,0.000000;" in ini_text

    def test_tilt_tool_opens_with_saved_value_not_zero(
        self, qml_app, qt_app, tmp_path
    ):
        """#131: a döntés-csúszka a MENTETT tilt-értékről induljon, ne néma
        0-ról — különben az első érintés kinullázza a mentett döntést."""
        from PySide6.QtCore import Q_ARG, QMetaObject, Qt

        window, _, _ = qml_app
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_path.write_text(
            "[a.jpg]\nfilters=tilt=1,0.400000,0.000000;\n", encoding="utf-8"
        )
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        QMetaObject.invokeMethod(
            panel,
            "handleToolClick",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "tilt"),
        )
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"
        assert slider.property("value") == pytest.approx(0.4)

    def test_navigation_with_tilt_tool_active_preserves_next_photo_preview(
        self, qml_app, qt_app, tmp_path
    ):
        """#131: aktív döntés-eszköz melletti lapozás NEM nullázza a
        következő kép előnézetét — a csúszka a mentett tilt-értékére áll,
        a 0-ra állás nem vált ki previewTilt(0)-t."""
        window, _, _ = qml_app
        ini_path = tmp_path / "kepek" / ".picasa.ini"
        ini_path.write_text(
            "[a.jpg]\nfilters=tilt=1,0.400000,0.000000;\n"
            "[b.jpg]\nfilters=tilt=1,-0.200000,0.000000;\n",
            encoding="utf-8",
        )
        viewer = self._open_viewer(window, qt_app, index=0)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()
        slider = window.findChild(QObject, "tiltSlider")
        assert slider is not None, "tiltSlider nem található"

        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()

        # a csúszka a b.jpg mentett tilt-értékére állt, NEM 0-ra
        assert slider.property("value") == pytest.approx(-0.2)
        # a b.jpg mentett tilt-je az ini-ben érintetlen maradt
        ini_text = ini_path.read_text(encoding="utf-8")
        assert "filters=tilt=1,-0.200000,0.000000;" in ini_text

    def test_reopen_crop_tool_shows_uncropped_image_and_existing_selection(
        self, qml_app, qt_app, tmp_path
    ):
        """#71: a Vágás eszköz újranyitásakor a teljes (vágatlan) kép +
        a meglévő kijelölés látszik, a vágás folytatható marad."""
        from PySide6.QtCore import QMetaObject, QRectF, Qt

        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        overlay.setProperty("hasSelection", True)
        QMetaObject.invokeMethod(
            overlay, "acceptCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        # Enter-flow: elfogadás után a vágó-mód megmarad, de a kijelölés
        # üresre áll vissza a következő képre lépéskor
        assert panel.property("cropActive") is True
        assert overlay.property("hasSelection") is False

        # visszalépés az imént megvágott képre: a teljes kép + a mentett
        # kijelölés (nem a levágott eredmény) jelenjen meg
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        edit = self._edit_controller(engine)
        assert edit.property("previewSource").startswith("image://editpreview/")
        assert overlay.property("hasSelection") is True
        crop_rect = overlay.property("cropRect")
        assert crop_rect.x() == pytest.approx(0.25, abs=1e-3)
        assert crop_rect.width() == pytest.approx(0.5, abs=1e-3)

    def test_crop_cancel_leaves_crop_mode(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "cropOverlay")
        QMetaObject.invokeMethod(
            overlay, "cancelCrop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("cropActive") is False

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
        thickness_slider.setProperty("value", 4)
        QMetaObject.invokeMethod(
            thickness_slider, "moved", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert edit.property("textOutlineThickness") == 4

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
            found = TestEditorWiring._find_item_by_name(child, name)
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


class TestViewerFolderBoundedNavigation:
    """#84: a nagy nézőben (PhotoViewer) a lapozás CSAK az aktuális mappa
    képei között mozogjon — a rács (feed) nézet szűrői (pl. csillag-szűrő)
    több mappa fotóit is felsorolhatják egymás után, de a néző ne lépjen
    át a szomszéd mappába."""

    @pytest.fixture
    def qml_app_multi_folder(self, qt_app, tmp_path):
        """Két mappa csillagozott képekkel, egyetlen (mappaátlépő) rács-
        listában betöltve — ahogy a csillag-szűrő is összefésüli őket."""
        import picasapy.app.application as app_module
        from picasapy.app.controller import AppController
        from picasapy.app.discovery_controller import DiscoveryController
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.app.face_scan_controller import FaceScanController
        from picasapy.app.faces_helper import FacesHelper
        from picasapy.app.fileops_controller import FileOpsController
        from picasapy.app.folder_tree_controller import FolderTreeController
        from picasapy.app.import_source_controller import ImportSourceController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.app.timeline_controller import TimelineController
        from picasapy.thumbs import ThumbnailCache
        from picasapy.version import version_string
        from PySide6.QtCore import QSettings
        from PySide6.QtQml import QQmlApplicationEngine

        lib = tmp_path / "kepek"
        folder_a = lib / "nyaralas"
        folder_b = lib / "telek"
        folder_a.mkdir(parents=True)
        folder_b.mkdir()
        make_jpeg(folder_a / "a1.jpg")
        make_jpeg(folder_a / "a2.jpg")
        make_jpeg(folder_b / "b1.jpg")
        make_jpeg(folder_b / "b2.jpg")
        (folder_a / ".picasa.ini").write_text(
            "[a1.jpg]\nstar=yes\n\n[a2.jpg]\nstar=yes\n", encoding="utf-8"
        )
        (folder_b / ".picasa.ini").write_text(
            "[b1.jpg]\nstar=yes\n\n[b2.jpg]\nstar=yes\n", encoding="utf-8"
        )
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, lib)

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        controller = AppController(db, (str(lib),), provider, settings=settings)
        edit_preview = EditPreviewProvider()
        edit_controller = EditController(edit_preview)
        engine = QQmlApplicationEngine()
        engine.addImageProvider("thumbs", provider)
        engine.addImageProvider("editpreview", edit_preview)
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", controller)
        engine.rootContext().setContextProperty("editController", edit_controller)
        # #305: a Main.qml és a benne élő komponensek (MainToolbar,
        # PicasaImportDialog, FileOpsDialogs, AboutDialog, TimelineView…)
        # az application.py bekötésének megfelelően MINDIG várják ezeket a
        # context property-ket — hiányukban nem null-t, hanem "X is not
        # defined" ReferenceError-t dobnak. A fixture ezért a közös
        # qml_app-hoz hasonlóan mindegyiket regisztrálja (a teszt maga csak
        # a controller/editController-t használja, a többi csak a
        # figyelmeztetés-mentességhez kell).
        fileops_controller = FileOpsController()
        app_module.wire_fileops(fileops_controller, controller)
        engine.rootContext().setContextProperty(
            "fileOpsController", fileops_controller
        )
        discovery_controller = DiscoveryController(
            add_folder=controller.addWatchedFolder
        )
        engine.rootContext().setContextProperty(
            "discoveryController", discovery_controller
        )
        folder_tree_controller = FolderTreeController()
        engine.rootContext().setContextProperty(
            "folderTreeController", folder_tree_controller
        )
        faces_helper = FacesHelper()
        engine.rootContext().setContextProperty("facesHelper", faces_helper)
        face_scan_controller = FaceScanController(db, faces_helper=faces_helper)
        engine.rootContext().setContextProperty(
            "faceScanController", face_scan_controller
        )
        timeline_controller = TimelineController(db, provider)
        controller.syncFinished.connect(timeline_controller.reload)
        engine.rootContext().setContextProperty(
            "timelineController", timeline_controller
        )
        import_source_controller = ImportSourceController(
            provider, add_folder=controller.addWatchedFolder
        )
        engine.rootContext().setContextProperty(
            "importSourceController", import_source_controller
        )
        engine.rootContext().setContextProperty("appVersion", version_string())
        engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
        assert engine.rootObjects(), "Main.qml betöltése sikertelen"
        window = engine.rootObjects()[0]
        controller._reload()
        # a rács (feed) nézet: mindkét mappa csillagozott képei, folytonosan
        # (f.path, p.name szerint: nyaralas/a1, a2, telek/b1, b2)
        controller.showStarred()
        qt_app.processEvents()
        yield window, controller, engine
        engine.deleteLater()
        qt_app.processEvents()

    def _open_viewer(self, window, qt_app, index):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def test_next_stops_at_folder_end(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        assert controller.photos.rowCount() == 4  # a rács nem szűkül mappára
        viewer = self._open_viewer(window, qt_app, index=1)  # a2.jpg — nyaralas utolsó képe
        QMetaObject.invokeMethod(viewer, "next", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 1, (
            "a mappahatárnál a néző nem léphet át a szomszéd mappába"
        )

    def test_previous_stops_at_folder_start(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=2)  # b1.jpg — telek első képe
        QMetaObject.invokeMethod(
            viewer, "previous", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 2

    def test_next_moves_within_folder(self, qml_app_multi_folder, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=0)  # a1.jpg
        QMetaObject.invokeMethod(viewer, "next", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert viewer.property("currentIndex") == 1  # a2.jpg — még a nyaralas mappa

    def test_nav_buttons_disabled_at_folder_boundaries(
        self, qml_app_multi_folder, qt_app
    ):
        window, controller, _ = qml_app_multi_folder
        viewer = self._open_viewer(window, qt_app, index=1)  # a2.jpg — nyaralas utolsó
        next_button = window.findChild(QObject, "viewerNextButton")
        assert next_button is not None, "viewerNextButton nem található"
        assert next_button.property("enabled") is False
        # ugyanezen a nézőn (egyetlen engine) a telek mappa első képénél a
        # ◀ gomb is letiltva — egy fixture-példányban ellenőrizve, hogy az
        # offscreen tesztkörnyezetben ne kelljen két QQmlApplicationEngine-t
        # egymás után létrehozni (ismert instabilitás a tesztfuttatóban)
        viewer.setProperty("currentIndex", 2)  # b1.jpg — telek első képe
        qt_app.processEvents()
        prev_button = window.findChild(QObject, "viewerPrevButton")
        assert prev_button is not None, "viewerPrevButton nem található"
        assert prev_button.property("enabled") is False


class _ViewerOpenMixin:
    """Az `_open_viewer` segédet a #464-es tesztek is használják."""

    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer


class TestFinetuneTabQuickFixesAndPicker(_ViewerOpenMixin):
    """#464: a 2. fülön ott van a két egykattintásos javítás és a
    „semleges szín" pipetta.

    A tulajdonos képernyőképei (`referencia/finomhangolas/shot1..4.png`)
    pontosították a formát: a két egykattintásos javítás nem szöveges
    csempe, hanem KÉT VARÁZSPÁLCA-GOMB a csúszka-oszlop jobb szélén — az
    egyik a Kiemelések/Árnyékok párnál („…a megvilágításhoz"), a másik az
    Alapszínválasztás sorában („…a színhez")."""

    def test_wands_and_picker_present_on_the_finetune_tab(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 1)
        qt_app.processEvents()

        for name in (
            "finetuneLightingWand", "finetuneColorWand",
            "finetuneNeutralPicker", "finetuneNeutralSwatch",
        ):
            assert window.findChild(QObject, name) is not None, name

    def test_a_ket_palca_KULON_utat_indit(self, qml_app, qt_app):
        """A megvilágítás-pálca az Automatikus kontraszt műveletét indítja
        (a `referencia/varazspalcak/` mérése szerint), a SZÍN-pálca viszont
        NEM szűrőt fűz a láncra: a `finetune2` semleges szín (p4) mezőjét
        állítja be — a Picasa saját `.picasa.ini`-je bizonyítja (#551)."""
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 1)
        qt_app.processEvents()

        tools, wand = [], []
        panel.toolActivated.connect(tools.append)
        panel.colorWandRequested.connect(lambda: wand.append("color"))
        for name in ("finetuneLightingWand", "finetuneColorWand"):
            QMetaObject.invokeMethod(
                window.findChild(QObject, name),
                "clicked", Qt.ConnectionType.DirectConnection,
            )
        qt_app.processEvents()
        assert tools == ["autolight"]
        assert wand == ["color"]

    def test_picker_toggle_arms_the_sampling_area(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 1)
        qt_app.processEvents()

        area = window.findChild(QObject, "neutralPickArea")
        assert area is not None
        assert area.property("enabled") is False

        QMetaObject.invokeMethod(
            panel, "neutralPickerToggled", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("neutralPickerActive") is True
        assert area.property("enabled") is True


class TestEffectTabsFitWithoutScrolling(_ViewerOpenMixin):
    """#422 (felhasználói döntés): az effekt-füleknek KERET/GÖRGETÉS NÉLKÜL
    ki kell férniük.

    A rács azért lógott ki eredetileg, mert a három ismert fülre a spec
    listáján KÍVÜLI effektek is odakerültek; azok a 6., „További effektek"
    fülre kerültek. A görgethető keret (az én korábbi megoldásom) rossz
    válasz volt a tünetre — ez a teszt őrzi, hogy ne kerüljön vissza, és
    hogy a rács tényleg elférjen a gombsor fölött."""

    GRIDS = {2: "effectsGrid", 3: "effectsGrid2", 4: "effectsGrid3",
             5: "effectsGrid4"}

    def test_no_scroll_frame_on_the_effect_tabs(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        for name in (
            "editorEffectsTab1Scroll",
            "editorEffectsTab2Scroll",
            "editorEffectsTab3Scroll",
        ):
            assert window.findChild(QObject, name) is None, (
                f"visszakerült a görgethető keret: {name}"
            )

    def test_every_effect_tab_has_the_spec_button_count(self, qml_app, qt_app):
        """A fülek gombszáma az, ami az eredetin — ettől férnek ki.

        A tényleges GEOMETRIÁT szándékosan nem mérjük: a teszt-ablak
        panelje jóval alacsonyabb a valódinál, ott a legjobb elrendezés sem
        férne ki. A hiba forrása nem a magasság volt, hanem az, hogy a
        három ismert fülre a spec listáján kívüli effektek is odakerültek."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        expected = {2: 12, 3: 12, 4: 11, 5: 6}
        for tab, grid_name in self.GRIDS.items():
            panel.setProperty("activeTab", tab)
            qt_app.processEvents()
            grid = window.findChild(QObject, grid_name)
            assert grid is not None, grid_name
            buttons = [
                child for child in grid.children()
                if str(child.objectName()).startswith("effect")
            ]
            assert len(buttons) == expected[tab], (
                f"{tab}. fül: {len(buttons)} gomb, várt {expected[tab]}"
            )


class TestModeToolPanelsDoNotOverflow(_ViewerOpenMixin):
    """#464: ugyanaz a hibaosztály, mint az effekt-füleknél — a mód-eszközök
    (vágás/retusálás/vörösszem/szöveg) panelje a tartalmától függően
    magasabb lehet a rendelkezésre álló helynél, és rálógna a panel alján
    ülő, globális Visszavonás/Újra sorra."""

    def test_effect_param_panel_is_clipped_above_the_undo_row(
        self, qml_app, qt_app
    ):
        """A sok paraméteres effektek alpanelje (pl. Vignetta) is
        magasabb lehet a helynél."""
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        row = window.findChild(QObject, "editorGlobalUndoRow")
        scroll = window.findChild(QObject, "editorEffectParamScroll")
        assert scroll is not None
        assert scroll.property("clip") is True

        panel.setProperty("paramPanelActive", True)
        qt_app.processEvents()
        assert scroll.property("visible") is True
        bottom = scroll.mapToItem(panel, 0, scroll.property("height"))
        assert bottom.y() <= row.mapToItem(panel, 0, 0).y() + 1

    def test_mode_panels_are_clipped_above_the_undo_row(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        row = window.findChild(QObject, "editorGlobalUndoRow")
        scroll = window.findChild(QObject, "editorModeToolScroll")
        assert scroll is not None
        assert scroll.property("clip") is True

        for prop in ("cropActive", "retouchActive", "redeyeActive", "textActive"):
            panel.setProperty(prop, True)
            qt_app.processEvents()
            assert scroll.property("visible") is True, prop
            bottom = scroll.mapToItem(panel, 0, scroll.property("height"))
            assert bottom.y() <= row.mapToItem(panel, 0, 0).y() + 1, (
                f"{prop}: a mód-panel területe a Visszavonás-sor alá nyúlik"
            )
            panel.setProperty(prop, False)
            qt_app.processEvents()


class TestGlobalUndoRedoRow(_ViewerOpenMixin):
    """#464: a Visszavonás/Újra a panel alján, GLOBÁLISAN — nem fülönként
    ismételve (az eredetiben sem volt fülhöz kötve)."""

    def test_single_row_shared_by_every_tab(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")

        row = window.findChild(QObject, "editorGlobalUndoRow")
        assert row is not None
        for tab in range(5):
            panel.setProperty("activeTab", tab)
            qt_app.processEvents()
            assert row.property("visible") is True, f"{tab}. fülön eltűnt"

    def test_the_old_per_tab_buttons_are_gone(self, qml_app, qt_app):
        window, _, _ = qml_app
        self._open_viewer(window, qt_app)
        for name in (
            "finetuneUndoButton", "effectsUndoButton",
            "effects2UndoButton", "effects3UndoButton",
        ):
            assert window.findChild(QObject, name) is None, name



class TestTextToolTypography:
    """#450 (2. lépcső): a szöveg-eszköz tipográfia-vezérlői a panelen —
    betűcsalád, méret, félkövér/dőlt/aláhúzott, igazítás."""

    def _open_text_tool(self, window, qt_app):
        # a néző megnyitása indítja a beginEdit-et — enélkül a stílus-slotok
        # jogosan tiltakoznak („Nincs aktív szerkesztés")
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        return panel

    def test_every_control_is_present(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        self._open_text_tool(window, qt_app)
        for name in (
            "textFontFamilyBox", "textFontSizeBox", "textBoldButton",
            "textItalicButton", "textUnderlineButton",
            "textAlign_left", "textAlign_center", "textAlign_right",
        ):
            assert window.findChild(QObject, name) is not None, name

    def test_the_family_list_comes_from_the_catalogue(self, qml_app, qt_app):
        from picasapy.render.text_fonts import FONT_FAMILIES

        window, _controller, _engine = qml_app
        panel = self._open_text_tool(window, qt_app)
        keys = panel.property("fontFamilyKeys")
        keys = keys.toVariant() if hasattr(keys, "toVariant") else list(keys)
        assert keys == [family.key for family in FONT_FAMILIES]

    def test_the_style_buttons_reach_the_controller(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, Qt

        window, _controller, _engine = qml_app
        panel = self._open_text_tool(window, qt_app)
        seen = []
        panel.textBoldEdited.connect(seen.append)
        panel.textAlignEdited.connect(seen.append)

        for name in ("textBoldButton", "textAlign_center"):
            QMetaObject.invokeMethod(
                window.findChild(QObject, name), "buttonClicked",
                Qt.ConnectionType.DirectConnection,
            )
        qt_app.processEvents()

        assert seen == [True, "center"]

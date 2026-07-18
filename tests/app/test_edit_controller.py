"""EditController: EditSession + ini-perzisztencia + preview-regisztráció híd."""

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


class TestBeginEdit:
    def test_empty_ini_gives_empty_session(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.redeyeActive is False
        assert controller.enhanceActive is False
        assert controller.revision == 1
        assert controller.previewSource == "image://editpreview/1?rev=1"

    def test_existing_filters_loaded(self, controller, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text("[IMG_0001.jpg]\nfilters=enhance=1;\n", encoding="utf-8")
        controller.beginEdit("1", str(photo))
        assert controller.enhanceActive is True

    def test_registers_with_preview_provider(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (8, 6)


class TestEndEdit:
    def test_clears_preview_source(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.endEdit()
        assert controller.previewSource == ""

    def test_unregisters_from_provider(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.endEdit()
        image = provider.requestImage("1", None, None)
        assert image.width() == 16  # placeholder


class TestToggleTool:
    def test_writes_filters_to_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.toggleTool("enhance")
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=enhance=1;" in ini_text
        assert controller.enhanceActive is True

    def test_toggle_off_removes_key_when_chain_empty(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.toggleTool("enhance")
        controller.toggleTool("enhance")
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=" not in ini_text
        assert controller.enhanceActive is False

    def test_preserves_unrelated_keys(self, controller, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\nbackuphash=1234\nstar=yes\n", encoding="utf-8"
        )
        controller.beginEdit("1", str(photo))
        controller.toggleTool("autolight")
        ini_text = ini.read_text(encoding="utf-8")
        assert "backuphash=1234" in ini_text
        assert "star=yes" in ini_text
        assert "filters=autolight=1;" in ini_text

    def test_bumps_revision(self, controller, photo):
        controller.beginEdit("1", str(photo))
        before = controller.revision
        controller.toggleTool("redeye")
        assert controller.revision == before + 1

    def test_invalid_tool_raises(self, controller, photo):
        controller.beginEdit("1", str(photo))
        with pytest.raises(ValueError):
            controller.toggleTool("nemletezik")

    def test_without_active_edit_raises(self, controller):
        with pytest.raises(ValueError):
            controller.toggleTool("enhance")


class TestApplyCrop:
    def test_writes_crop64_to_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.1, 0.2, 0.5, 0.3)
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=crop64=1," in ini_text

    def test_changes_preview_source_revision(self, controller, photo):
        controller.beginEdit("1", str(photo))
        before = controller.previewSource
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        assert controller.previewSource != before

    def test_provider_reflects_cropped_size(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (4, 3)

    def test_out_of_range_values_are_clamped(self, controller, photo):
        controller.beginEdit("1", str(photo))
        # a jobb szél kilóg 1.0 fölé — clampelés, nem hiba
        controller.applyCrop(0.8, 0.0, 0.5, 0.5)
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=crop64=1," in ini_text

    def test_non_positive_size_raises(self, controller, photo):
        controller.beginEdit("1", str(photo))
        with pytest.raises(ValueError):
            controller.applyCrop(0.1, 0.1, 0.0, 0.5)


class TestClearCrop:
    def test_removes_crop_from_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        controller.clearCrop()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "crop64" not in ini_text
        assert "crop=" not in ini_text


class TestPicasaCompanionCropKey:
    """#73: a Picasa a filters= mellett külön crop=rect64(...) kulcsot is ír."""

    def test_apply_crop_writes_companion_key(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "crop=rect64(" in ini_text

    def test_undo_crop_removes_companion_key(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        controller.undo()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "crop=rect64(" not in ini_text


class TestSetTilt:
    def test_writes_tilt_with_picasa_zero_scale(self, controller, photo):
        """#73: Picasa-paritás — a skála-mező 0.000000, a kitöltő skálát a
        megjelenítő számolja (a Picasa is így ír)."""
        controller.beginEdit("1", str(photo))
        controller.setTilt(0.3)
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=tilt=1,0.300000,0.000000;" in ini_text

    def test_bumps_revision_and_preview(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.setTilt(0.2)
        image = provider.requestImage("1", None, None)
        assert not image.isNull()


class TestUndoRedoStack:
    """#59: valódi undo/redo verem művelet-nevekkel."""

    def _controller(self, tmp_path):
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider
        from support.jpeg_factory import make_jpeg

        make_jpeg(tmp_path / "a.jpg", size=(320, 160))
        ctl = EditController(EditPreviewProvider())
        ctl.beginEdit("1", str(tmp_path / "a.jpg"))
        return ctl

    def test_actions_stack_in_order(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path)
        assert ctl.canUndo is False
        ctl.applyCrop(0.1, 0.1, 0.5, 0.5)
        ctl.toggleTool("enhance")
        assert ctl.canUndo is True
        assert ctl.undoAction == "enhance"   # utoljára jött → először megy
        ctl.undo()
        assert ctl.undoAction == "crop"
        assert ctl.enhanceActive is False
        assert ctl.hasCrop is True
        ctl.undo()
        assert ctl.hasCrop is False
        assert ctl.canUndo is False

    def test_redo_restores_in_order(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path)
        ctl.applyCrop(0.1, 0.1, 0.5, 0.5)
        ctl.toggleTool("enhance")
        ctl.undo()
        ctl.undo()
        assert ctl.canRedo is True
        assert ctl.redoAction == "crop"
        ctl.redo()
        assert ctl.hasCrop is True
        ctl.redo()
        assert ctl.enhanceActive is True
        assert ctl.canRedo is False

    def test_new_action_clears_redo(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path)
        ctl.toggleTool("enhance")
        ctl.undo()
        ctl.toggleTool("autolight")
        assert ctl.canRedo is False

    def test_undo_writes_ini(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path)
        ctl.toggleTool("enhance")
        ctl.undo()
        ini_text = (tmp_path / ".picasa.ini").read_text(encoding="utf-8")
        assert "enhance" not in ini_text

    def test_begin_edit_resets_stacks(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path)
        ctl.toggleTool("enhance")
        ctl.beginEdit("1", str(tmp_path / "a.jpg"))
        assert ctl.canUndo is False and ctl.canRedo is False

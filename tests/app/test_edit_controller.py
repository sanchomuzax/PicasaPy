"""EditController: EditSession + ini-perzisztencia + preview-regisztráció híd."""

import os
import sys

import pytest

from picasapy.app.histogram_helper import EMPTY_HISTOGRAM
from support.jpeg_factory import make_jpeg

_SKIP_READONLY = pytest.mark.skipif(
    sys.platform.startswith("win") or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="chmod-alapú read-only szimuláció POSIX-only, és root megkerüli a jogokat",
)


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


class TestPagingMemory:
    """#128: lapozás a nézőben = beginEdit új id-vel, endEdit nélkül — a
    korábbi képek előnézete nem maradhat bent örökre a providerben."""

    def test_two_begin_edits_release_older_previews(self, controller, provider, tmp_path):
        from picasapy.app import edit_preview

        first = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        second = make_jpeg(tmp_path / "IMG_0002.jpg", size=(8, 6))
        controller.beginEdit("1", str(first))
        controller.beginEdit("2", str(second))
        # a cache mindkét lapozás után korlátos marad
        assert len(provider._sources) <= edit_preview._LRU_CAPACITY
        # tovább lapozva a legrégebbi ("1") felszabadul
        third = make_jpeg(tmp_path / "IMG_0003.jpg", size=(8, 6))
        controller.beginEdit("3", str(third))
        assert "1" not in provider._sources
        assert provider.requestImage("1", None, None).width() == 16  # placeholder

    def test_previous_photo_stays_cached_for_back_paging(
        self, controller, provider, tmp_path, monkeypatch
    ):
        from picasapy.app import edit_preview

        calls = []
        original = edit_preview._decode_source

        def counting_decode(path):
            calls.append(path)
            return original(path)

        monkeypatch.setattr(edit_preview, "_decode_source", counting_decode)
        first = make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))
        second = make_jpeg(tmp_path / "IMG_0002.jpg", size=(8, 6))
        controller.beginEdit("1", str(first))
        controller.beginEdit("2", str(second))
        controller.beginEdit("1", str(first))  # visszalapozás: nincs újradekód
        assert len(calls) == 2


class TestToggleTool:
    def test_writes_filters_to_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.toggleTool("enhance")
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=enhance=1;" in ini_text
        assert controller.enhanceActive is True

    def test_redeye_toggle_off_removes_key_when_chain_empty(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.toggleTool("redeye")
        controller.toggleTool("redeye")
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=" not in ini_text
        assert controller.redeyeActive is False

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


@_SKIP_READONLY
class TestReadOnlySave:
    """#459: a mentés (`_save`) csak-olvasható mappán NEM némán bukjon —
    látható jelzést kell adnia, nem néma no-op / kivétel."""

    def test_toggle_tool_on_readonly_folder_emits_signal_not_exception(
        self, controller, photo
    ):
        os.chmod(photo.parent, 0o500)
        try:
            signals = []
            controller.editSaveReadOnly.connect(lambda: signals.append(True))
            controller.beginEdit("1", str(photo))
            # nem szabad kivételt dobnia — a hívó (QML) egyébként sem
            # kapná el, csendben ölné meg a slot-hívást
            controller.toggleTool("redeye")
            assert signals == [True]
        finally:
            os.chmod(photo.parent, 0o700)

    def test_readonly_folder_does_not_write_ini(self, controller, photo):
        os.chmod(photo.parent, 0o500)
        try:
            controller.beginEdit("1", str(photo))
            controller.toggleTool("redeye")
            assert not (photo.parent / ".picasa.ini").exists()
        finally:
            os.chmod(photo.parent, 0o700)

    def test_writable_folder_still_saves_normally(self, controller, photo):
        signals = []
        controller.editSaveReadOnly.connect(lambda: signals.append(True))
        controller.beginEdit("1", str(photo))
        controller.toggleTool("redeye")
        assert signals == []
        assert (photo.parent / ".picasa.ini").exists()


class TestOneShotLayering:
    """#116: az egygombos javítások append-only rétegek, Picasa-mintára."""

    def test_repeated_click_is_noop_while_last(self, controller, photo):
        """Amíg a szűrő a lánc utolsó eleme, az újabb kattintás no-op —
        nem távolít el, nem duplikál, undo-lépést sem tol."""
        controller.beginEdit("1", str(photo))
        controller.toggleTool("enhance")
        assert controller.canUndo is True
        controller.toggleTool("enhance")
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert ini_text.count("enhance=1;") == 1
        assert controller.enhanceActive is True
        controller.undo()
        assert controller.canUndo is False  # csak EGY undo-lépés keletkezett

    def test_layering_a_b_a_appends_new_layer(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.toggleTool("autolight")
        controller.toggleTool("enhance")
        controller.toggleTool("autolight")
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=autolight=1;enhance=1;autolight=1;" in ini_text

    def test_enabled_follows_last_element_rule(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.enhanceEnabled is True
        controller.toggleTool("enhance")
        assert controller.enhanceEnabled is False
        assert controller.autolightEnabled is True
        controller.toggleTool("autolight")
        # másik effekt került a tetejére → az enhance újra nyomható
        assert controller.enhanceEnabled is True
        assert controller.autolightEnabled is False

    def test_undo_restores_layer_by_layer(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.toggleTool("autolight")
        controller.toggleTool("enhance")
        controller.toggleTool("autolight")
        controller.undo()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=autolight=1;enhance=1;" in ini_text
        controller.undo()
        controller.undo()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=" not in ini_text

    def test_picasa_written_duplicate_chain_not_damaged(self, controller, photo):
        """Round-trip: a valódi Picasa által írt, ismétlődő szűrős láncból
        egy kattintás nem törölhet előfordulásokat (1. rögzített döntés)."""
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\nfilters=autolight=1;enhance=1;autolight=1;\n",
            encoding="utf-8",
        )
        controller.beginEdit("1", str(photo))
        controller.toggleTool("autocolor")
        ini_text = ini.read_text(encoding="utf-8")
        assert "filters=autolight=1;enhance=1;autolight=1;autocolor=1;" in ini_text


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
        # #514: a mentett lánc újrarenderelése háttérszálon fut
        assert controller.waitForBackgroundWorkers(10.0)
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


class TestCropSelection:
    """#71: a jelenlegi crop64 relatív [0..1] téglalapja a QML-nek."""

    def test_none_when_no_crop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.cropSelection is None

    def test_reflects_applied_crop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.1, 0.2, 0.5, 0.3)
        sel = controller.cropSelection
        # rect64 kvantált (16 bites fixpontos) kódolás — kis eltérés várható
        assert sel["x"] == pytest.approx(0.1, abs=1e-3)
        assert sel["y"] == pytest.approx(0.2, abs=1e-3)
        assert sel["width"] == pytest.approx(0.5, abs=1e-3)
        assert sel["height"] == pytest.approx(0.3, abs=1e-3)


class TestCropToolPreview:
    """#71: a Vágás eszköz megnyitásakor a teljes (vágatlan) kép jelenik meg,
    a meglévő crop64-et a QML overlay rajzolja rá kijelölésként."""

    def test_enter_crop_tool_shows_uncropped_source(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        assert controller.waitForBackgroundWorkers(10.0)  # #514
        cropped = provider.requestImage("1", None, None)
        assert (cropped.width(), cropped.height()) == (4, 3)

        controller.enterCropTool()
        full = provider.requestImage("1", None, None)
        assert (full.width(), full.height()) == (8, 6)

    def test_enter_crop_tool_does_not_write_ini_or_undo(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        before_undo = controller.canUndo
        ini_before = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        controller.enterCropTool()
        assert controller.canUndo == before_undo
        ini_after = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert ini_after == ini_before

    def test_exit_crop_tool_restores_cropped_preview(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        controller.enterCropTool()
        controller.exitCropTool()
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (4, 3)

    def test_enter_crop_tool_without_active_edit_raises(self, controller):
        with pytest.raises(ValueError):
            controller.enterCropTool()

    def test_exit_crop_tool_without_active_edit_raises(self, controller):
        with pytest.raises(ValueError):
            controller.exitCropTool()

    def test_reopen_and_reapply_replaces_crop_in_place(self, controller, photo):
        """A vágás folytatható: az új téglalap a régi HELYÉRE kerül, nem
        fűződik hozzá második crop64."""
        controller.beginEdit("1", str(photo))
        controller.applyCrop(0.0, 0.0, 0.5, 0.5)
        controller.enterCropTool()
        controller.applyCrop(0.1, 0.1, 0.4, 0.4)
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert ini_text.count("crop64=") == 1
        assert "crop=rect64(" in ini_text


class TestPreviewTilt:
    """#72: élő forgatás-előnézet a csúszka húzása közben, mentés/undo nélkül."""

    def test_updates_preview_without_writing_ini(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.previewTilt(0.3)
        assert not (photo.parent / ".picasa.ini").exists()
        image = provider.requestImage("1", None, None)
        assert not image.isNull()

    def test_does_not_push_undo_step(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewTilt(0.3)
        assert controller.canUndo is False

    def test_bumps_revision(self, controller, photo):
        controller.beginEdit("1", str(photo))
        before = controller.revision
        controller.previewTilt(0.3)
        assert controller.revision == before + 1

    def test_does_not_mutate_session_value(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewTilt(0.3)
        # a következő setTilt (elengedéskor) az EREDETI (üres) láncból indul,
        # nem a previewTilt által ideiglenesen alkalmazott értékből
        controller.setTilt(0.5)
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=tilt=1,0.500000,0.000000;" in ini_text

    def test_without_active_edit_raises(self, controller):
        with pytest.raises(ValueError):
            controller.previewTilt(0.3)

    def test_set_tilt_after_preview_persists_and_allows_undo(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewTilt(0.3)
        controller.previewTilt(0.6)
        controller.setTilt(0.6)
        assert controller.canUndo is True
        assert controller.undoAction == "tilt"
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=tilt=1,0.600000,0.000000;" in ini_text


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

    def test_begin_edit_reseeds_undo_from_chain(self, qt_app, tmp_path):
        """Újranyitáskor a verem a mentett láncból épül újra (#116
        visszajelzés): a meglévő réteg visszavonható marad, a redo ürül."""
        ctl = self._controller(tmp_path)
        ctl.toggleTool("enhance")
        ctl.beginEdit("1", str(tmp_path / "a.jpg"))
        assert ctl.canUndo is True
        assert ctl.undoAction == "enhance"
        assert ctl.canRedo is False


class TestPersistentUndoFromChain:
    """#116 visszajelzés: annyi undo-réteg, ahány effekt a mentett láncon —
    képváltás/újranyitás után is, fordított sorrendben."""

    def _controller(self, tmp_path, filters_value):
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider
        from support.jpeg_factory import make_jpeg

        make_jpeg(tmp_path / "a.jpg", size=(320, 160))
        if filters_value:
            (tmp_path / ".picasa.ini").write_text(
                f"[a.jpg]\nfilters={filters_value}\n", encoding="utf-8"
            )
        ctl = EditController(EditPreviewProvider())
        ctl.beginEdit("1", str(tmp_path / "a.jpg"))
        return ctl

    def test_existing_chain_is_undoable_on_open(self, qt_app, tmp_path):
        """Aktív effekt mellett nem lehet szürke az Undo."""
        ctl = self._controller(tmp_path, "enhance=1;")
        assert ctl.enhanceActive is True
        assert ctl.canUndo is True

    def test_layers_undo_in_reverse_chain_order(self, qt_app, tmp_path):
        """1,2,4,1,2 sorrendű lánc → 2,1,4,2,1 sorrendben vonható vissza."""
        ctl = self._controller(
            tmp_path, "enhance=1;autolight=1;redeye=1;enhance=1;autolight=1;"
        )
        seen = []
        while ctl.canUndo:
            seen.append(ctl.undoAction)
            ctl.undo()
        assert seen == ["autolight", "enhance", "redeye", "autolight", "enhance"]
        ini_text = (tmp_path / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=" not in ini_text

    def test_undo_removes_only_last_layer(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path, "autolight=1;enhance=1;")
        ctl.undo()
        ini_text = (tmp_path / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=autolight=1;" in ini_text

    def test_crop_layer_labeled_as_crop(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path, "crop64=1,3f845bcb59418507;")
        assert ctl.undoAction == "crop"

    def test_unknown_picasa_filter_is_undoable_layer(self, qt_app, tmp_path):
        """Ismeretlen (valódi Picasa írta) szűrő is réteg: visszavonható, és
        a Visszavonásig bitre pontosan megmarad (round-trip elv)."""
        value = "enhance=1;finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
        ctl = self._controller(tmp_path, value)
        assert ctl.undoAction == "finetune2"
        ctl.undo()
        ini_text = (tmp_path / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=enhance=1;" in ini_text
        assert "finetune2" not in ini_text

    def test_redo_restores_seeded_layer(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path, "enhance=1;autolight=1;")
        ctl.undo()
        assert ctl.canRedo is True
        ctl.redo()
        ini_text = (tmp_path / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=enhance=1;autolight=1;" in ini_text

    def test_new_layer_after_seeded_history_stacks_on_top(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path, "enhance=1;")
        ctl.toggleTool("autolight")
        assert ctl.undoAction == "autolight"
        ctl.undo()
        assert ctl.undoAction == "enhance"
        ctl.undo()
        assert ctl.canUndo is False

    def test_empty_chain_has_no_undo(self, qt_app, tmp_path):
        ctl = self._controller(tmp_path, "")
        assert ctl.canUndo is False


class TestFinetune:
    """Finomhangolás (finetune2) csúszkák — #20."""

    def _filters(self, photo):
        from picasapy.ini import load_document

        ini = photo.parent / ".picasa.ini"
        if not ini.exists():
            return ""
        section = load_document(ini).section("IMG_0001.jpg")
        return (section.get("filters") if section else None) or ""

    def test_set_finetune_writes_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.5, 0.25, 0.1, -0.5)
        assert (
            self._filters(photo)
            == "finetune2=1,0.500000,0.250000,0.100000,00000000,-0.500000;"
        )

    def test_finetune_properties_reflect_saved(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.3, 0.6, 0.2, 0.8)
        assert controller.fillLight == pytest.approx(0.3)
        assert controller.highlights == pytest.approx(0.6)
        assert controller.shadows == pytest.approx(0.2)
        assert controller.colorTemp == pytest.approx(0.8)
        assert controller.hasFinetune is True

    def test_finetune_preloaded_from_existing_ini(self, controller, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\nfilters=finetune2=1,0.4,0,0,00000000,0;\n",
            encoding="utf-8",
        )
        controller.beginEdit("1", str(photo))
        assert controller.fillLight == pytest.approx(0.4)

    def test_set_finetune_pushes_undo(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.5, 0, 0, 0)
        assert controller.canUndo is True
        assert controller.undoAction == "finetune"
        controller.undo()
        assert controller.hasFinetune is False

    def test_all_zero_removes_finetune(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.5, 0, 0, 0)
        controller.setFinetune(0, 0, 0, 0)
        assert controller.hasFinetune is False
        assert self._filters(photo) == ""

    def test_preview_finetune_no_ini_write(self, controller, photo):
        controller.beginEdit("1", str(photo))
        rev_before = controller.revision
        controller.previewFinetune(0.5, 0, 0, 0)
        # előnézet frissült, de az ini üres maradt (nincs mentés)
        assert controller.revision == rev_before + 1
        assert self._filters(photo) == ""
        assert controller.canUndo is False

    def test_preview_then_save_single_finetune(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewFinetune(0.2, 0, 0, 0)
        controller.previewFinetune(0.7, 0, 0, 0)
        controller.setFinetune(0.7, 0, 0, 0)
        # a sok preview után is egyetlen finetune2 réteg marad
        assert self._filters(photo).count("finetune2=") == 1


class TestGpuFinetunePreview:
    """GPU élő-előnézet (#22) — `gpuPrefixSource`/`gpuLutSource` és a
    `previewFinetuneGpu` LUT-only gyors út."""

    def _filters(self, photo):
        from picasapy.ini import load_document

        ini = photo.parent / ".picasa.ini"
        if not ini.exists():
            return ""
        section = load_document(ini).section("IMG_0001.jpg")
        return (section.get("filters") if section else None) or ""

    def test_no_active_edit_gives_empty_sources(self, controller):
        assert controller.gpuPrefixSource == ""
        assert controller.gpuLutSource == ""

    def test_begin_edit_on_empty_chain_is_gpu_eligible(self, controller, photo):
        """Üres lánc: a `set_finetune` a végére fűzné → GPU-alkalmas."""
        controller.beginEdit("1", str(photo))
        assert controller.gpuPrefixSource.startswith("image://editpreview/1?gpuprefix=1")
        assert controller.gpuLutSource.startswith("image://editpreview/1?gpulut=1")

    def test_finetune_in_middle_of_chain_is_not_gpu_eligible(self, controller, photo):
        """Ha a finetune2 UTÁN másik effekt is van a mentett láncban, a
        GPU-előnézet nem biztonságos — üres URL-eket kell adnia."""
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\nfilters=finetune2=1,0.5,0,0,00000000,0;grain2=1,0.5;\n",
            encoding="utf-8",
        )
        controller.beginEdit("1", str(photo))
        assert controller.gpuPrefixSource == ""
        assert controller.gpuLutSource == ""

    def test_end_edit_clears_gpu_sources(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.gpuPrefixSource != ""
        controller.endEdit()
        assert controller.gpuPrefixSource == ""
        assert controller.gpuLutSource == ""

    def test_preview_finetune_gpu_updates_lut_source_not_preview_source(
        self, controller, photo
    ):
        """A GPU-gyors út csak a `gpuLutSource`-ot bumpolja — a
        `previewSource` (a `photo` Image forrása) NEM változhat, különben a
        drága numpy-lánc pont a GPU-réteg által elkerülni kívánt módon
        futna újra minden húzási lépésnél."""
        controller.beginEdit("1", str(photo))
        preview_before = controller.previewSource
        lut_before = controller.gpuLutSource
        controller.previewFinetuneGpu(0.0, 0.1, 0.2, -0.3)
        assert controller.previewSource == preview_before
        assert controller.gpuLutSource != lut_before

    def test_preview_finetune_gpu_does_not_write_ini_or_undo(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewFinetuneGpu(0.0, 0.2, 0, 0)
        assert self._filters(photo) == ""
        assert controller.canUndo is False

    def test_preview_finetune_gpu_updates_provider_lut(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.previewFinetuneGpu(0.0, 0.2, 0, 0)
        lut_image = provider.requestImage(
            f"1?gpulut=1&rev={controller._gpu_revision}", None, None
        )
        assert not lut_image.isNull()
        assert (lut_image.width(), lut_image.height()) == (256, 1)

    def test_preview_finetune_gpu_without_active_edit_raises(self, controller):
        with pytest.raises(ValueError):
            controller.previewFinetuneGpu(0.0, 0.2, 0, 0)

    def test_preview_finetune_gpu_falls_back_to_cpu_on_nonzero_fill(
        self, controller, photo
    ):
        """#551: nem nulla Derítőfénynél a GPU-út tilos — a kontroller a
        rendes CPU-előnézetre esik vissza: a `previewSource` bumpol — a
        GPU-úton épp ez NEM történne meg."""
        controller.beginEdit("1", str(photo))
        preview_before = controller.previewSource
        controller.previewFinetuneGpu(0.5, 0, 0, 0)
        assert controller.previewSource != preview_before

    def test_preview_finetune_gpu_noop_when_chain_not_eligible(self, controller, photo):
        """Ha a mentett lánc közben GPU-alkalmatlanná vált, a hívás néma
        no-op — nem bukik, csak nem frissít semmit."""
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\nfilters=finetune2=1,0.5,0,0,00000000,0;grain2=1,0.5;\n",
            encoding="utf-8",
        )
        controller.beginEdit("1", str(photo))
        lut_before = controller.gpuLutSource
        controller.previewFinetuneGpu(0.9, 0, 0, 0)
        assert controller.gpuLutSource == lut_before == ""


class TestEffects:
    """Effekt rétegek append-only alkalmazása — #20."""

    def _filters(self, photo):
        from picasapy.ini import load_document

        ini = photo.parent / ".picasa.ini"
        if not ini.exists():
            return ""
        section = load_document(ini).section("IMG_0001.jpg")
        return (section.get("filters") if section else None) or ""

    def test_apply_effect_appends(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyEffect("sepia")
        assert self._filters(photo) == "sepia=1;"

    def test_apply_effect_with_default_params(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyEffect("sat")
        assert self._filters(photo) == "sat=1,0.500000;"

    def test_apply_effect_layers(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyEffect("bw")
        controller.applyEffect("warm")
        assert self._filters(photo) == "bw=1;warm=1;"

    def test_apply_effect_pushes_undo(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyEffect("grain2")
        assert controller.undoAction == "grain2"
        controller.undo()
        assert self._filters(photo) == ""

    def test_apply_unknown_effect_raises(self, controller, photo):
        controller.beginEdit("1", str(photo))
        with pytest.raises(ValueError):
            controller.applyEffect("bogus")

    def test_apply_effect_requires_active(self, controller):
        with pytest.raises(ValueError):
            controller.applyEffect("sepia")


class TestHistogramAndCameraSummary:
    """A hisztogram-doboz kötési pontjai (#25): histogram + cameraSummary."""

    def test_no_active_edit_gives_empty_histogram(self, controller):
        histogram = controller.histogram
        assert set(histogram) == {"r", "g", "b"}
        assert all(v == 0.0 for v in histogram["r"])

    def test_no_active_edit_gives_empty_camera_summary(self, controller):
        assert controller.cameraSummary == ""

    def test_begin_edit_populates_histogram_from_solid_red_photo(
        self, controller, photo
    ):
        # a jpeg_factory tömör piros képet gyárt (Image.new("RGB", size, "red"));
        # a JPEG-tömörítés a csatorna-értéket kissé eltolhatja (pl. 254), a
        # LÉNYEG a magas-piros / nulla-zöld-kék eloszlás
        controller.beginEdit("1", str(photo))
        histogram = controller.histogram
        assert max(histogram["r"]) == 1.0
        assert histogram["r"].index(1.0) > 200
        # zöld/kék csatorna: minden pixel a 0-s vödörben — a csúcs ott van
        assert histogram["g"].index(1.0) == 0
        assert histogram["b"].index(1.0) == 0

    def test_histogram_updates_after_effect_applied(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyEffect("bw")
        assert controller.waitForBackgroundWorkers(10.0)  # #514
        histogram = controller.histogram
        # fekete-fehérben a három csatorna azonos eloszlású (szürkeárnyalat)
        assert histogram["r"] == histogram["g"] == histogram["b"]

    def test_camera_summary_is_string_after_begin_edit(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert isinstance(controller.cameraSummary, str)

    def test_end_edit_clears_histogram_and_camera_summary(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.endEdit()
        assert controller.cameraSummary == ""
        assert all(v == 0.0 for v in controller.histogram["r"])


class TestRetouchTool:
    """#445: a Vágás mintáját követő enter/exit + Alkalmaz/Mégse eszköz, DE
    a foltok maguk a Picasa súgószövege szerinti kétkattintásos, irányított
    klónozással jönnek létre (cél → forrás-előnézet → véglegesítés)."""

    def test_begin_patch_does_not_write_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "retouch" not in ini.read_text(encoding="utf-8")
        assert controller.retouchPendingCount == 0
        assert controller.retouchPatchPending is True

    def test_preview_source_does_not_write_ini_or_commit(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        controller.previewRetouchSource(0.2, 0.2)
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "retouch" not in ini.read_text(encoding="utf-8")
        assert controller.retouchPendingCount == 0
        assert controller.retouchPatchPending is True

    def test_preview_source_without_target_is_noop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.previewRetouchSource(0.2, 0.2)
        assert controller.retouchPendingCount == 0
        assert controller.retouchPatchPending is False

    def test_commit_finalizes_patch_in_buffer(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        controller.previewRetouchSource(0.2, 0.2)
        controller.commitRetouchPatch(0.2, 0.2)
        assert controller.retouchPendingCount == 1
        assert controller.retouchPatchPending is False

    def test_commit_without_target_is_noop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.commitRetouchPatch(0.2, 0.2)
        assert controller.retouchPendingCount == 0

    def test_cancel_patch_discards_target_only(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        controller.previewRetouchSource(0.2, 0.2)
        controller.commitRetouchPatch(0.2, 0.2)
        controller.beginRetouchPatch(0.6, 0.6)
        controller.cancelRetouchPatch()
        assert controller.retouchPatchPending is False
        assert controller.retouchPendingCount == 1  # a korábban véglegesített folt marad

    def test_apply_writes_retouch_chain_v2(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        controller.commitRetouchPatch(0.2, 0.2)
        controller.applyRetouch()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=retouch=2," in ini_text
        assert controller.retouchPendingCount == 0
        assert controller.hasRetouch is True

    def test_multiple_commits_accumulate_patches(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.2, 0.2)
        controller.commitRetouchPatch(0.3, 0.3)
        controller.beginRetouchPatch(0.8, 0.8)
        controller.commitRetouchPatch(0.7, 0.7)
        assert controller.retouchPendingCount == 2
        controller.applyRetouch()
        from picasapy.ini import load_document
        from picasapy.ini.retouch import parse_retouch_patches
        from picasapy.ini.filters import parse_filters

        document = load_document(photo.parent / ".picasa.ini")
        value = document.section("IMG_0001.jpg").get("filters")
        ops = parse_filters(value)
        patches = parse_retouch_patches(next(op for op in ops if op.matches("retouch")))
        assert len(patches) == 2

    def test_exit_without_apply_discards_pending(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        controller.commitRetouchPatch(0.2, 0.2)
        controller.exitRetouchTool()
        assert controller.retouchPendingCount == 0
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "retouch" not in ini.read_text(encoding="utf-8")

    def test_apply_with_empty_pending_is_noop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.applyRetouch()
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists()

    def test_enter_retouch_tool_seeds_pending_from_saved_patches(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.3, 0.3)
        controller.commitRetouchPatch(0.4, 0.4)
        controller.applyRetouch()
        controller.exitRetouchTool()
        controller.enterRetouchTool()
        assert controller.retouchPendingCount == 1

    def test_undo_removes_applied_retouch(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        controller.commitRetouchPatch(0.2, 0.2)
        controller.applyRetouch()
        controller.undo()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "retouch" not in ini_text
        assert controller.hasRetouch is False


class TestRetouchPatchUndoRedo:
    """#445: patch-enkénti Undo/Redo/Reset — a retusálás PUFFERÉN dolgozik,
    NEM a globális Visszavonás-verem (ld. `EditController.undoPatch`
    docsztringje)."""

    def _commit_patch(self, controller, target, source):
        controller.beginRetouchPatch(*target)
        controller.commitRetouchPatch(*source)

    def test_can_undo_patch_false_initially(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        assert controller.canUndoPatch is False
        assert controller.canRedoPatch is False

    def test_undo_patch_removes_last_commit(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        self._commit_patch(controller, (0.2, 0.2), (0.3, 0.3))
        self._commit_patch(controller, (0.6, 0.6), (0.7, 0.7))
        assert controller.retouchPendingCount == 2
        controller.undoPatch()
        assert controller.retouchPendingCount == 1
        assert controller.canUndoPatch is True
        assert controller.canRedoPatch is True

    def test_redo_patch_restores_undone_commit(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        self._commit_patch(controller, (0.2, 0.2), (0.3, 0.3))
        controller.undoPatch()
        assert controller.retouchPendingCount == 0
        controller.redoPatch()
        assert controller.retouchPendingCount == 1
        assert controller.canRedoPatch is False

    def test_new_commit_clears_redo_stack(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        self._commit_patch(controller, (0.2, 0.2), (0.3, 0.3))
        controller.undoPatch()
        self._commit_patch(controller, (0.5, 0.5), (0.4, 0.4))
        assert controller.canRedoPatch is False

    def test_undo_patch_without_history_is_noop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.undoPatch()  # nem dobhat
        assert controller.retouchPendingCount == 0

    def test_reset_patches_clears_buffer_with_undo_step(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        self._commit_patch(controller, (0.2, 0.2), (0.3, 0.3))
        self._commit_patch(controller, (0.6, 0.6), (0.7, 0.7))
        controller.resetPatches()
        assert controller.retouchPendingCount == 0
        assert controller.canUndoPatch is True
        controller.undoPatch()
        assert controller.retouchPendingCount == 2

    def test_reset_patches_discards_half_made_patch(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.beginRetouchPatch(0.5, 0.5)
        controller.resetPatches()
        assert controller.retouchPatchPending is False

    def test_reset_patches_empty_buffer_is_noop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRetouchTool()
        controller.resetPatches()
        assert controller.canUndoPatch is False


class TestRetouchBrushSize:
    """#445: kör alakú ecset, állítható mérettel — csúszka [1..100]."""

    def test_default_brush_size(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert 1 <= controller.brushSize <= 100

    def test_set_brush_size_updates_property(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setBrushSize(50)
        assert controller.brushSize == 50

    def test_set_brush_size_clamped_to_upper_bound(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setBrushSize(500)
        assert controller.brushSize == 100

    def test_set_brush_size_clamped_to_lower_bound(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setBrushSize(-5)
        assert controller.brushSize == 1

    def test_brush_size_resets_on_begin_edit(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setBrushSize(99)
        controller.endEdit()
        controller.beginEdit("1", str(photo))
        assert controller.brushSize != 99


#: A `.picasa.ini`-korpusz valódi, KÉTBLOKKOS `text=` sora (#371).
_KETBLOKKOS_GOLDEN = (
    "2;187;63;Kellemes karácsonyi ünnepeket és&#010;boldog újévet kívánunk!;Arial;"
    "0.105605,0.008726,0.059259,-4.712389;"
    "v1,4292215592,4293454056,128.000000,1.000000,0.500000,1.000000,700,258,49152;;"
    "126;4;2010;Arial;"
    "0.943794,0.039316,0.112127,1.308997;"
    "v1,4292215592,4293454056,128.000000,1.000000,0.500000,1.000000,700,258,49152;;"
)


def _text_ertek(photo) -> str:
    """A megírt `.picasa.ini` `text=` sorának ÉRTÉKE (a kulcs nélkül)."""
    for line in (photo.parent / ".picasa.ini").read_text(encoding="utf-8").splitlines():
        if line.startswith("text="):
            return line[len("text=") :]
    raise AssertionError("nincs text= sor a .picasa.ini-ben")


class TestTextTool:
    """#148: a szöveg-eszköz (`text=`/`textactive=`) enter/exit + Alkalmaz/Mégse."""

    def test_preview_placement_does_not_write_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Nyaralás")
        controller.previewTextPlacement(0.5, 0.5)
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "text=" not in ini.read_text(encoding="utf-8")
        assert controller.textHasPlacement is True

    def test_apply_writes_text_and_textactive(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Nyaralás")
        controller.previewTextPlacement(0.25, 0.75)
        controller.applyText()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "text=1;" in ini_text
        assert "Nyaralás" in ini_text
        assert "textactive=1" in ini_text
        assert controller.hasTextOverlay is True

    def test_apply_without_placement_is_noop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Nyaralás")
        controller.applyText()
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists()

    def test_apply_without_content_is_noop(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.previewTextPlacement(0.5, 0.5)
        controller.applyText()
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists()

    def test_exit_without_apply_discards_pending(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Nyaralás")
        controller.previewTextPlacement(0.5, 0.5)
        controller.exitTextTool()
        assert controller.textHasPlacement is False
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "text=" not in ini.read_text(encoding="utf-8")

    def test_enter_text_tool_seeds_draft_from_saved_content(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Cím")
        controller.previewTextPlacement(0.4, 0.6)
        controller.applyText()
        controller.exitTextTool()
        controller.enterTextTool()
        assert controller.textDraft == "Cím"

    def test_clear_text_removes_ini_keys(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Cím")
        controller.previewTextPlacement(0.4, 0.6)
        controller.applyText()
        controller.clearText()
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "text=" not in ini_text
        assert "textactive=" not in ini_text
        assert controller.hasTextOverlay is False

    # -- #371: a kiírt `text=` a VALÓDI Picasa-formátum -------------------

    def test_a_kiirt_sor_picasa_formatumu(self, controller, photo):
        """A 0.8.88-ig kiírt saját alak (`1;<x*10000>;<y*10000>;…`) a valódi
        Picasánál rosszul értelmeződött volna: a 2. mező nála blokkhossz, a
        3. szöveghossz. Mostantól szabályos, hét mezős blokkot írunk."""
        from picasapy.ini.text_overlay import parse_text

        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Nyaralás")
        controller.previewTextPlacement(0.25, 0.75)
        controller.applyText()
        raw = _text_ertek(photo)
        overlay = parse_text(raw)
        assert len(overlay.blocks) == 1
        block = overlay.blocks[0]
        assert block.content == "Nyaralás"
        assert block.geometry.x == pytest.approx(0.25)
        assert block.geometry.y == pytest.approx(0.75)
        assert raw.endswith(";;")

    def test_tobbsoros_felirat_entitassal_irodik_es_visszaolvashato(
        self, controller, photo
    ):
        """A sortörés `&#010;`-ként kerül a fájlba (ez maga is pontosvesszőre
        végződik) — a hossz-előtag miatt így is hibátlanul visszaolvasható."""
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("első sor\nmásodik sor")
        controller.previewTextPlacement(0.1, 0.1)
        controller.applyText()
        assert "&#010;" in _text_ertek(photo)
        controller.endEdit()
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        assert controller.textDraft == "első sor\nmásodik sor"

    def test_a_szinek_visszatoltodnek(self, controller, photo):
        """A `text=` stílus-mezője két színt hordoz — ezek mostantól
        mentődnek és a következő megnyitáskor visszaállnak."""
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextFillColor("#ff0000")
        controller.setTextOutlineColor("#0000ff")
        controller.setTextDraft("Piros")
        controller.previewTextPlacement(0.5, 0.5)
        controller.applyText()
        controller.endEdit()
        controller.beginEdit("1", str(photo))
        assert controller.textFillColor == "#ff0000"
        assert controller.textOutlineColor == "#0000ff"

    def test_a_masodik_picasa_blokk_nem_vesz_el_szerkeszteskor(
        self, controller, photo
    ):
        """Valódi, KÉTBLOKKOS Picasa-felirat átírásakor csak az első blokk
        cserélődik — a második érintetlenül marad a fájlban."""
        from picasapy.ini.text_overlay import parse_text

        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\ntext=" + _KETBLOKKOS_GOLDEN + "\ntextactive=1\n",
            encoding="utf-8",
        )
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        assert controller.textDraft.startswith("Kellemes")
        controller.setTextDraft("Új felirat")
        controller.previewTextPlacement(0.3, 0.3)
        controller.applyText()
        blocks = parse_text(_text_ertek(photo)).blocks
        assert len(blocks) == 2
        assert blocks[0].content == "Új felirat"
        assert blocks[1].content == "2010"

    def test_a_regi_picasapy_felirat_nem_vesz_el(self, controller, photo):
        """A 0.8.88-ig mentett saját alakú feliratot beolvassuk, és a
        pozícióját átszámoljuk — a felhasználó szövege nem tűnik el."""
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\ntext=1;2500;8000;Régi felirat;Arial\ntextactive=1\n",
            encoding="utf-8",
        )
        controller.beginEdit("1", str(photo))
        assert controller.hasTextOverlay is True
        controller.enterTextTool()
        assert controller.textDraft == "Régi felirat"

    def test_provider_receives_text_overlay_for_preview(
        self, controller, provider, photo
    ):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Nyaralás")
        controller.previewTextPlacement(0.5, 0.5)
        image = provider.requestImage("1", None, None)
        assert not image.isNull()

    def test_reload_after_apply_restores_relative_position(self, controller, photo):
        """A mentett felirat pozíciója kerek-úton (mentés → újranyitás) is
        pontos marad. #371 óta a `text=` geometria-mezője viszi, ugyanabban
        a normalizált [0..1] egységben, amit a szerkesztő használ."""
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Cím")
        controller.previewTextPlacement(0.25, 0.75)
        controller.applyText()
        controller.endEdit()
        controller.beginEdit("1", str(photo))
        assert controller.hasTextOverlay is True
        controller.enterTextTool()
        assert controller.textDraft == "Cím"


class TestTextStyle:
    """#450: kitöltés+körvonal szín, körvonal-vastagság, kitöltés ki/be,
    átlátszóság. #371 óta a KÉT SZÍN mentődik (a `text=` stílus-mezőjének
    van rá helye), a másik három továbbra is munkamenet-szintű állapot —
    ld. `_DEFAULT_TEXT_*` megjegyzését az edit_controller.py-ban."""

    def test_defaults(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.textFillColor == "#ffffff"
        assert controller.textOutlineColor == "#000000"
        assert controller.textOutlineThickness == 0
        assert controller.textFillEnabled is True
        assert controller.textOpacity == 1.0

    def test_setters_update_properties(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setTextFillColor("#ff0000")
        controller.setTextOutlineColor("#00ff00")
        controller.setTextOutlineThickness(3)
        controller.setTextFillEnabled(False)
        controller.setTextOpacity(0.5)
        assert controller.textFillColor == "#ff0000"
        assert controller.textOutlineColor == "#00ff00"
        assert controller.textOutlineThickness == 3
        assert controller.textFillEnabled is False
        assert controller.textOpacity == 0.5

    def test_reset_to_defaults_on_new_begin_edit(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setTextFillColor("#ff0000")
        controller.setTextOutlineThickness(5)
        controller.endEdit()
        controller.beginEdit("1", str(photo))
        assert controller.textFillColor == "#ffffff"
        assert controller.textOutlineThickness == 0

    def test_negative_outline_thickness_raises(self, controller, photo):
        controller.beginEdit("1", str(photo))
        with pytest.raises(ValueError):
            controller.setTextOutlineThickness(-1)

    def test_out_of_range_opacity_raises(self, controller, photo):
        controller.beginEdit("1", str(photo))
        with pytest.raises(ValueError):
            controller.setTextOpacity(1.5)

    def test_csak_a_ket_szin_kerul_iniba(self, controller, photo):
        """#371: a `text=` stílus-mezőjének KÉT színe van (kitöltés,
        körvonal) — ezek mentődnek. A körvonal-vastagságnak, a kitöltés
        ki/be-nek és az átlátszóságnak NINCS megfelelő mezője, ezért azok
        munkamenet-szintűek maradnak."""
        from picasapy.ini.text_overlay import parse_text

        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Nyaralás")
        controller.previewTextPlacement(0.5, 0.5)
        controller.setTextFillColor("#ff0000")
        controller.setTextOutlineColor("#00ff00")
        controller.setTextOutlineThickness(2)
        controller.setTextFillEnabled(False)
        controller.setTextOpacity(0.4)
        controller.applyText()
        style = parse_text(_text_ertek(photo)).blocks[0].style
        assert style.fill_argb == 0xFFFF0000
        assert style.outline_argb == 0xFF00FF00
        # a mentés utáni újranyitás a vastagságot/átlátszóságot alapértékre
        # állítja: ezeknek nincs hova mentődniük
        controller.endEdit()
        controller.beginEdit("1", str(photo))
        assert controller.textOutlineThickness == 0
        assert controller.textOpacity == 1.0
        assert controller.textFillEnabled is True

    def test_style_change_affects_live_preview(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("A")
        controller.previewTextPlacement(0.5, 0.5)
        base = provider.requestImage("1", None, None)
        controller.setTextOutlineThickness(4)
        controller.setTextOutlineColor("#00ff00")
        styled = provider.requestImage("1", None, None)
        assert base != styled


class TestEffectRenderRunsOffTheUiThread:
    """#514: a mentett lánc újrarenderelése NEM a felület szálán fut.

    Amíg a hosszú effektek (Lomo, Polaroid…) a GUI-szálon számoltak, a
    felület befagyottnak látszott, és a közös haladásjelző csík (#505) sem
    tudott animálni — ugyanaz a szál számolt, ami rajzol.
    """

    def test_apply_effect_returns_before_the_render_finishes(
        self, controller, provider, photo, monkeypatch
    ):
        """A hívás VISSZATÉR, miközben a renderelés még be sem fejeződött —
        ez az a tulajdonság, ami a felületet életben tartja."""
        import threading

        controller.beginEdit("1", str(photo))
        release = threading.Event()
        entered = threading.Event()
        original = provider.register

        def slow_register(*args, **kwargs):
            entered.set()
            assert release.wait(10.0), "a lassú render nem kapott elengedést"
            return original(*args, **kwargs)

        monkeypatch.setattr(provider, "register", slow_register)
        controller.applyEffect("bw")
        # ha a renderelés a hívó szálán futna, ide csak a release UTÁN
        # jutnánk el — a teszt önmagában holtpontra futna
        assert entered.wait(10.0), "a renderelés el sem indult"
        release.set()
        assert controller.waitForBackgroundWorkers(10.0)

    def test_busy_indicator_is_engaged_during_the_render(
        self, qt_app, controller, provider, photo, monkeypatch
    ):
        """A #505 csíkja MAGÁTÓL pörög: a `_start_background` jelentkezik be
        a busy-nyilvántartásba, a hívónak nem kell külön kérnie."""
        import threading

        from picasapy.app.busy_registry import get_app_busy_registry

        controller.beginEdit("1", str(photo))
        registry = get_app_busy_registry()
        # a be-/kijelentkezés szálhatáron át, sorba állítva érkezik (ld.
        # busy_registry modul-docstring) — a kiindulási állapotot is csak
        # az események leürítése után szabad leolvasni
        qt_app.processEvents()
        before = registry.activeCount
        release = threading.Event()
        entered = threading.Event()
        original = provider.register

        def slow_register(*args, **kwargs):
            entered.set()
            assert release.wait(10.0)
            return original(*args, **kwargs)

        monkeypatch.setattr(provider, "register", slow_register)
        controller.applyEffect("bw")
        assert entered.wait(10.0)
        qt_app.processEvents()
        assert registry.activeCount > before, "a haladásjelzés nem indult el"
        release.set()
        assert controller.waitForBackgroundWorkers(10.0)
        qt_app.processEvents()
        assert registry.activeCount == before, "a csík a munka után is pörögne"

    def test_the_rendered_image_is_the_last_requested_state(
        self, controller, provider, photo
    ):
        """Gyors kattintás-sorozat után is az UTOLSÓ állapot látszik — az
        elavult (közben túlhaladott) renderelések kihagyják magukat."""
        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.edit.session import EditSession

        controller.beginEdit("1", str(photo))
        controller.applyEffect("bw")
        controller.applyEffect("sepia")
        assert controller.waitForBackgroundWorkers(10.0)
        image = provider.requestImage("1", None, None)

        # viszonyítás: ugyanaz a lánc SZINKRON kirenderelve egy önálló
        # providerrel — a háttérszálas útnak pontosan ezt kell adnia
        reference_provider = EditPreviewProvider()
        session = EditSession().append_effect("bw", ("1",)).append_effect(
            "sepia", ("1",)
        )
        reference_provider.register("1", photo, session.ops)
        expected = reference_provider.requestImage("1", None, None)

        assert (image.width(), image.height()) == (
            expected.width(),
            expected.height(),
        )
        mismatched = [
            (x, y)
            for y in range(expected.height())
            for x in range(expected.width())
            if image.pixelColor(x, y) != expected.pixelColor(x, y)
        ]
        assert mismatched == [], "nem az utolsó (szépia) állapot látszik"

    def test_slider_preview_stays_synchronous(self, controller, provider, photo):
        """Az élő csúszka-előnézet marad szinkron: a húzás minden lépésénél
        AZONNAL friss képet kell adnia (nincs villogás, nincs késés)."""
        controller.beginEdit("1", str(photo))
        controller.previewEffect("sat", [2.0])
        # háttérszál el sem indult — a kép már most a helyén van
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (8, 6)


class TestBackgroundRenderRaces:
    """#546: a #514 háttérszálas renderének három versenyhelyzete."""

    @staticmethod
    def _blocking_register(provider, entered, release):
        """A provider `register()`-e beragad, amíg a teszt el nem engedi."""
        original = provider.register

        def slow(*args, **kwargs):
            entered.set()
            assert release.wait(10.0), "a lassú render nem kapott elengedést"
            return original(*args, **kwargs)

        return slow

    def test_a_csuszka_elonezet_nem_var_a_hatter_renderre(
        self, controller, provider, photo, monkeypatch
    ):
        """1. pont: lassú háttér-render ALATT a csúszka-húzás azonnali.

        Ha a szinkron út ugyanarra a zárra várna, mint a háttér-render, a
        `previewEffect` csak a `release` után térne vissza — a teszt
        holtpontra futna (a `release`-t csak utána állítjuk be).
        """
        import threading

        controller.beginEdit("1", str(photo))
        entered, release = threading.Event(), threading.Event()
        monkeypatch.setattr(
            provider, "register", self._blocking_register(provider, entered, release)
        )
        controller.applyEffect("bw")
        assert entered.wait(10.0), "a háttér-render el sem indult"

        monkeypatch.undo()  # a szinkron út a VALÓDI register()-t hívja
        controller.previewEffect("sat", [2.0])  # ← itt nem szabad várnia
        image = provider.requestImage("1", None, None)
        assert (image.width(), image.height()) == (8, 6)

        release.set()
        assert controller.waitForBackgroundWorkers(10.0)

    def test_az_elavult_render_nem_irja_felul_a_frissebbet(
        self, controller, provider, photo, monkeypatch
    ):
        """2. pont: a késleltetett, RÉGEBBI render nem kerülhet a tárba.

        Az első (lassú) rendert mesterségesen a második UTÁNIG tartjuk;
        a végeredménynek a másodiknak kell lennie.
        """
        import threading

        from picasapy.app.edit_preview import EditPreviewProvider
        from picasapy.edit.session import EditSession

        controller.beginEdit("1", str(photo))
        entered, release = threading.Event(), threading.Event()
        monkeypatch.setattr(
            provider, "register", self._blocking_register(provider, entered, release)
        )
        controller.applyEffect("bw")
        assert entered.wait(10.0)

        monkeypatch.undo()
        controller.applyEffect("sepia")  # az ÚJABB kérés
        release.set()  # …és csak most engedjük végig a régebbit
        assert controller.waitForBackgroundWorkers(10.0)

        reference = EditPreviewProvider()
        session = EditSession().append_effect("bw", ("1",)).append_effect(
            "sepia", ("1",)
        )
        reference.register("1", photo, session.ops)
        expected = reference.requestImage("1", None, None)
        image = provider.requestImage("1", None, None)
        mismatched = [
            (x, y)
            for y in range(expected.height())
            for x in range(expected.width())
            if image.pixelColor(x, y) != expected.pixelColor(x, y)
        ]
        assert mismatched == [], "az elavult render felülírta a frissebb képet"

    def test_end_edit_utan_a_hatter_render_nem_regisztral_vissza(
        self, controller, provider, photo, monkeypatch
    ):
        """3. pont: a lezárt fotót a futó render nem teheti vissza a tárba."""
        import threading

        controller.beginEdit("1", str(photo))
        entered, release = threading.Event(), threading.Event()
        monkeypatch.setattr(
            provider, "register", self._blocking_register(provider, entered, release)
        )
        controller.applyEffect("bw")
        assert entered.wait(10.0)

        monkeypatch.undo()
        controller.endEdit()
        release.set()
        assert controller.waitForBackgroundWorkers(10.0)

        assert provider.histogram_for("1") == EMPTY_HISTOGRAM, (
            "a lezárt fotó visszakerült a preview-tárba"
        )

    def test_a_render_hibaja_nem_nema(
        self, qt_app, controller, provider, photo, monkeypatch
    ):
        """#548: a háttérszálban elhaló kivétel eddig NÉMA volt (a
        `threading` excepthookja csak stderr-re ír) — a kép magyarázat
        nélkül maradt a régi. Most naplózódik, jelzést küld, és a
        busy-számláló is visszaáll."""

        def boom(*args, **kwargs):
            raise OSError("a NAS eltűnt a stat() alól")

        controller.beginEdit("1", str(photo))
        failures = []
        controller.editSaveFailed.connect(lambda message: failures.append(message))
        monkeypatch.setattr(provider, "register", boom)

        controller.applyEffect("bw")
        assert controller.waitForBackgroundWorkers(10.0)
        # a jelzés szálhatáron át, sorba állítva érkezik
        qt_app.processEvents()
        assert failures and "NAS" in failures[0]

    def test_cancel_pending_preview_utan_nincs_ertesites(
        self, qt_app, controller, provider, photo, monkeypatch
    ):
        """#547: kilépéskor a folyamatban lévő render se ne tároljon, se ne
        emitáljon — különben a daemon-szál egy közben megsemmisülő
        QObject-nek jelezne (a #430-as SIGSEGV-osztály)."""
        import threading

        controller.beginEdit("1", str(photo))
        entered, release = threading.Event(), threading.Event()
        monkeypatch.setattr(
            provider, "register", self._blocking_register(provider, entered, release)
        )
        controller.applyEffect("bw")
        assert entered.wait(10.0)

        revisions = []
        controller.revisionChanged.connect(lambda: revisions.append(controller.revision))
        controller.cancelPendingPreview()
        release.set()
        assert controller.waitForBackgroundWorkers(10.0)
        qt_app.processEvents()
        assert revisions == [], "az érvénytelenített render mégis értesített"


class TestNeutralColorPicker:
    """#464: a 2. fül pipettája — a képre kattintott pont színe lesz a
    finetune2 „semleges szín" paramétere (a lánc 4. paramétere)."""

    def test_picked_color_lands_in_the_finetune_layer(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.pickNeutralColor(0.5, 0.5) is True

        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "finetune2=" in ini_text
        # a negyedik paraméter az AARRGGBB szín — a semleges alapérték
        # (00000000) helyett most valódi, ff-fel kezdődő érték áll ott
        finetune = next(
            line for line in ini_text.splitlines() if "finetune2=" in line
        )
        neutral = finetune.split("finetune2=")[1].split(";")[0].split(",")[4]
        assert neutral.startswith("ff"), finetune

    def test_sliders_are_left_alone(self, controller, photo):
        """A pipetta CSAK a semleges színt írja át — a négy csúszka marad."""
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.25, 0.5, 0.125, -0.5)
        controller.pickNeutralColor(0.25, 0.75)

        assert controller.fillLight == 0.25
        assert controller.highlights == 0.5
        assert controller.shadows == 0.125
        assert controller.colorTemp == -0.5

    def test_point_outside_the_image_is_refused(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.pickNeutralColor(5.0, 5.0) is False


class TestRedeyeTool:
    """#445: a vörösszem-eszköz AUTOMATIKUS ÉS KÉZI — a megnyitáskor az
    automatika azonnal fut az előnézeten, a kézzel húzott téglalapok pedig
    az Alkalmazásig csak a pufferben élnek (a Vágás/Retusálás mintája)."""

    def test_enter_runs_auto_without_writing_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "redeye" not in ini.read_text(encoding="utf-8")
        # az automatika lefutott (a találat-szám már nem a -1 kezdőérték)
        assert controller.redeyeFoundCount >= 0
        assert controller.redeyeRegionCount == 0

    def test_add_region_buffers_without_writing_ini(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.1, 0.1)
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "redeye" not in ini.read_text(encoding="utf-8")
        assert controller.redeyeRegionCount == 1
        assert len(controller.redeyeRegions) == 1

    def test_zero_sized_region_is_noop(self, controller, photo):
        """Puszta kattintás (nem húzás) nem vesz fel régiót."""
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.5, 0.5, 0.0, 0.0)
        assert controller.redeyeRegionCount == 0

    def test_negative_size_region_is_normalized(self, controller, photo):
        """Jobbról balra húzás is érvényes téglalap."""
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.5, 0.5, -0.2, -0.2)
        assert controller.redeyeRegionCount == 1
        region = controller.redeyeRegions[0]
        assert region["x"] == pytest.approx(0.3, abs=1e-3)
        assert region["w"] == pytest.approx(0.2, abs=1e-3)

    def test_undo_region_removes_last(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.1, 0.1)
        controller.addRedeyeRegion(0.5, 0.5, 0.1, 0.1)
        assert controller.canUndoRedeyeRegion is True
        controller.undoRedeyeRegion()
        assert controller.redeyeRegionCount == 1

    def test_reset_clears_regions_and_is_undoable(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.1, 0.1)
        controller.resetRedeyeRegions()
        assert controller.redeyeRegionCount == 0
        controller.undoRedeyeRegion()
        assert controller.redeyeRegionCount == 1

    def test_cancel_discards_buffer(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.1, 0.1)
        controller.exitRedeyeTool()
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "redeye" not in ini.read_text(encoding="utf-8")
        assert controller.redeyeRegionCount == 0

    def test_apply_writes_regions(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.1, 0.1)
        controller.applyRedeye()
        text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert text.startswith("[IMG_0001.jpg]\nfilters=redeye=1,")
        assert controller.redeyeActive is True
        assert controller.redeyeRegionCount == 0

    def test_apply_without_regions_writes_plain_picasa_entry(self, controller, photo):
        """Kézi régió nélkül a bejegyzés bájtra a valódi Picasa alakja."""
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.applyRedeye()
        text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        assert "filters=redeye=1;" in text

    def test_reenter_loads_saved_regions(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.1, 0.1)
        controller.applyRedeye()
        controller.enterRedeyeTool()
        assert controller.redeyeRegionCount == 1

    def test_apply_is_undoable(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.1, 0.1)
        controller.applyRedeye()
        controller.undo()
        assert controller.redeyeActive is False

    def test_auto_reports_found_spots(self, controller, tmp_path):
        """A sikerüzenet a TÉNYLEGESEN talált foltokból jön."""
        import numpy as np
        from PIL import Image

        array = np.full((60, 60, 3), 120, dtype=np.uint8)
        array[20:30, 10:20] = (220, 40, 40)
        array[20:30, 40:50] = (220, 40, 40)
        path = tmp_path / "eyes.jpg"
        Image.fromarray(array).save(path, quality=100)
        controller.beginEdit("2", str(path))
        controller.enterRedeyeTool()
        assert controller.redeyeFoundCount == 2

    def test_auto_reports_zero_on_clean_photo(self, controller, tmp_path):
        """Semleges szürke képen az automatika nem talál semmit (a
        `make_jpeg` fixture VÉGIG PIROS, azon egyetlen nagy foltot találna)."""
        import numpy as np
        from PIL import Image

        path = tmp_path / "gray.jpg"
        Image.fromarray(np.full((40, 40, 3), 120, dtype=np.uint8)).save(path)
        controller.beginEdit("3", str(path))
        controller.enterRedeyeTool()
        assert controller.redeyeFoundCount == 0


class TestCropSuggestions:
    """#448: a vágás-panel három automatikus javaslata."""

    def _photo_with_faces(self, tmp_path):
        import numpy as np
        from PIL import Image

        path = tmp_path / "portre.jpg"
        array = np.full((240, 320, 3), 120, dtype=np.uint8)
        array[60:120, 130:190] = (210, 170, 150)   # „arc"
        Image.fromarray(array).save(path, quality=95)
        (tmp_path / ".picasa.ini").write_text(
            "[Contacts2]\n1111111111111111=Anna;;\n"
            "[portre.jpg]\nfaces=rect64(6666400099996000),1111111111111111\n",
            encoding="utf-8",
        )
        return path

    def test_three_suggestions_on_a_plain_photo(self, controller, photo):
        controller.beginEdit("1", str(photo))
        suggestions = controller.cropSuggestions
        assert len(suggestions) == 3
        assert [s["key"] for s in suggestions] == [
            "variance", "horizon", "red_green"
        ]

    def test_face_suggestions_when_the_ini_has_faces(self, controller, tmp_path):
        path = self._photo_with_faces(tmp_path)
        controller.beginEdit("2", str(path))
        keys = [s["key"] for s in controller.cropSuggestions]
        assert keys[:2] == ["faces_tight", "faces_compose"]

    def test_suggestions_are_inside_the_picture(self, controller, photo):
        controller.beginEdit("1", str(photo))
        for suggestion in controller.cropSuggestions:
            assert 0.0 <= suggestion["x"] <= 1.0
            assert 0.0 <= suggestion["y"] <= 1.0
            assert 0.0 < suggestion["w"] <= 1.0
            assert 0.0 < suggestion["h"] <= 1.0
            assert suggestion["x"] + suggestion["w"] <= 1.0 + 1e-6
            assert suggestion["y"] + suggestion["h"] <= 1.0 + 1e-6

    def test_requested_aspect_shapes_the_suggestions(self, controller, photo):
        """A javaslatok a KIVÁLASZTOTT arányban születnek."""
        controller.beginEdit("1", str(photo))
        controller.setCropAspect(1.0)
        width, height = controller._image_size
        for suggestion in controller.cropSuggestions:
            ratio = (suggestion["w"] * width) / (suggestion["h"] * height)
            assert ratio == pytest.approx(1.0, rel=0.03), suggestion["key"]

    def test_no_active_edit_gives_no_suggestions(self, controller):
        assert controller.cropSuggestions == []

    def test_aspect_resets_between_photos(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setCropAspect(1.0)
        controller.endEdit()
        controller.beginEdit("1", str(photo))
        assert controller._crop_aspect is None


class TestLegacyEffectsCatalogue:
    """#571: az „Régi effektek" fül adatai a vezérlőből, a renderelőhöz
    kötve — a QML nem tart kézzel írt engedélyezett-listát."""

    def test_catalogue_is_exposed_to_qml(self, controller):
        effects = controller.legacyEffects
        assert effects, "üres örökség-katalógus"
        keys = [item["key"] for item in effects]
        assert "radtint" in keys and "triple" in keys
        # a `debug` fejlesztői eszköz volt — szándékosan nincs a fülön
        assert "debug" not in keys

    def test_enabled_flag_follows_the_renderer(self, controller):
        by_key = {item["key"]: item for item in controller.legacyEffects}
        # #565/#567 után ezek renderelnek
        assert by_key["radtint"]["enabled"] is True
        assert by_key["autobacklight"]["enabled"] is True
        # #623 után az irányított család MIND A NÉGY tagja él
        assert by_key["dir_sat"]["enabled"] is True
        assert by_key["dir_brite"]["enabled"] is True
        assert by_key["dir_sharp"]["enabled"] is True
        assert by_key["linblur"]["enabled"] is True
        # #687 után a natív tónus-/szín-szűrők is élnek
        assert by_key["triple"]["enabled"] is True
        assert by_key["contrast"]["enabled"] is True
        assert by_key["colortemp"]["enabled"] is True
        # ez a natív kernele megfejtéséig szürke
        assert by_key["colorfix"]["enabled"] is False

    def test_dead_legacy_name_is_flagged(self, controller):
        by_key = {item["key"]: item for item in controller.legacyEffects}
        # #567: halott bejegyzés — más magyarázatot kap a felületen, mint a
        # „még nincs megfejtve"
        assert by_key["focalpixelate"]["dead"] is True
        assert by_key["dir_sat"]["dead"] is False

    def test_every_entry_has_a_label(self, controller):
        assert all(item["label"] for item in controller.legacyEffects)


class TestLegacyEffectsInChain:
    """#571 5. pont: ha a megnyitott kép láncában örökölt effekt van, a fül
    jelzést kap — ehhez a vezérlő megmondja, mi van a láncban."""

    def test_empty_chain_reports_nothing(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert list(controller.legacyEffectsInChain) == []

    def test_legacy_filter_in_the_ini_is_reported(self, controller, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(
            f"[{photo.name}]\nfilters=radtint=1,0.5,0.5,0.25;\n", encoding="utf-8"
        )
        controller.beginEdit("1", str(photo))
        assert list(controller.legacyEffectsInChain) == ["radtint"]

    def test_ordinary_filter_is_not_reported(self, controller, photo):
        ini = photo.parent / ".picasa.ini"
        ini.write_text(f"[{photo.name}]\nfilters=bw=1;\n", encoding="utf-8")
        controller.beginEdit("1", str(photo))
        assert list(controller.legacyEffectsInChain) == []


class TestChainRejectionReachesTheUser:
    """#643/2: a round-trip őr visszautasítása KEZELT hiba, és a felhasználó
    a VALÓDI okot olvassa.

    Két külön állítás: (a) a `FilterWriteError` benne van a kezelt írási
    hibákban, tehát nem szökhet ki nyers kivételként a QML-slotból (ott
    senki nem kapná el, a szerkesztés némán elmaradna); (b) NEM az
    `editSaveFailed` csatornán megy ki, mert azt a felület a „Lemezhiba. A
    lemez tele lehet vagy írásvédett." mondattal keretezi — a lemezzel
    viszont semmi baj, a fájlt meg sem érintettük.
    """

    def test_filter_write_error_is_a_handled_write_error(self):
        from picasapy.app.edit_controller import _WRITE_ERRORS
        from picasapy.ini import FilterWriteError

        assert FilterWriteError in _WRITE_ERRORS

    def test_rejected_chain_uses_its_own_channel(self, controller, photo, monkeypatch):
        import picasapy.app.edit_controller as edit_mod
        from picasapy.ini import FilterWriteError

        controller.beginEdit("1", str(photo))

        def failing_update_document(path, mutate, backup=True):
            raise FilterWriteError("A szerkesztés nem menthető: teszt.")

        rejected: list[str] = []
        failed: list[str] = []
        # ELŐBB a feliratkozás — a mentés hibaútja szinkron.
        controller.editChainRejected.connect(rejected.append)
        controller.editSaveFailed.connect(failed.append)
        monkeypatch.setattr(edit_mod, "update_document", failing_update_document)

        # Nem szabad kivételt dobnia: a QML-slotból kiszökő kivételt senki
        # nem kapná el, a felhasználó néma bukást látna.
        controller.toggleTool("redeye")

        assert rejected == ["A szerkesztés nem menthető: teszt."]
        assert failed == []

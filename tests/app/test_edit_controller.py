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
        controller.previewFinetuneGpu(0.5, 0.1, 0.2, -0.3)
        assert controller.previewSource == preview_before
        assert controller.gpuLutSource != lut_before

    def test_preview_finetune_gpu_does_not_write_ini_or_undo(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewFinetuneGpu(0.5, 0, 0, 0)
        assert self._filters(photo) == ""
        assert controller.canUndo is False

    def test_preview_finetune_gpu_updates_provider_lut(self, controller, provider, photo):
        controller.beginEdit("1", str(photo))
        controller.previewFinetuneGpu(0.5, 0, 0, 0)
        lut_image = provider.requestImage(
            f"1?gpulut=1&rev={controller._gpu_revision}", None, None
        )
        assert not lut_image.isNull()
        assert (lut_image.width(), lut_image.height()) == (256, 1)

    def test_preview_finetune_gpu_without_active_edit_raises(self, controller):
        with pytest.raises(ValueError):
            controller.previewFinetuneGpu(0.5, 0, 0, 0)

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
        """A raw_x/raw_y PicasaPy-saját skálázása (#148) kerek-út (round-trip)
        pontos legyen a relatív [0..1] koordinátára."""
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
    átlátszóság — munkamenet-szintű állapot, NEM kerül a `.picasa.ini`-be
    (ld. `_DEFAULT_TEXT_*` megjegyzését az edit_controller.py-ban)."""

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

    def test_style_does_not_write_ini(self, controller, photo):
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
        ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
        # csak az ismert öt mező + esetleges raw_tail kerül a text=-be —
        # a stílus-mezők NEM ini-kulcsok (#450)
        assert "ff0000" not in ini_text.lower()
        assert "00ff00" not in ini_text.lower()

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

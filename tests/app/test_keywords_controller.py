"""Gyorscímkék (#193) — a Címkék-panel `KeywordsMixin`-hez tartozó
konfigurációs/perzisztencia-logikája: 8 gomb-szlot, „legutóbb használt"
felül-írás a felső két gombon, és a gyakori-címke automatikus kitöltés.

A QML-viselkedést (gombrács, fogaskerék-dialógus) a
`test_qml_quicktags.py` fedi; ez a fájl a Python-oldali `AppController`
felületet (a `controller` fixture — a `test_controller.py` mintája)."""

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir(parents=True)
    make_jpeg(root / "a.jpg")
    make_jpeg(root / "b.jpg")
    make_jpeg(root / "c.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
    )
    ctl._reload()
    return ctl


def _new_controller(tmp_path, library, settings):
    """Második `AppController`-példány UGYANAZON `settings`-tárral —
    a perzisztencia (thumbCaptionMode-teszt mintájára) ellenőrzéséhez."""
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs2", size=32))
    return AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
    )


class TestQuickTagDefaults:
    def test_default_labels_all_empty(self, controller):
        assert controller.quickTagConfigLabels == [""] * 8

    def test_default_reserve_recent_is_true(self, controller):
        assert controller.quickTagsReserveRecent is True

    def test_default_autofill_is_false(self, controller):
        assert controller.quickTagsAutoFillFrequent is False

    def test_default_buttons_all_empty(self, controller):
        assert controller.quickTagButtons == [""] * 8


class TestSetQuickTagLabel:
    def test_sets_single_slot(self, controller):
        controller.setQuickTagLabel(2, "nyaralás")
        labels = controller.quickTagConfigLabels
        assert labels[2] == "nyaralás"
        assert labels.count("") == 7

    def test_comma_stripped_like_regular_keywords(self, controller):
        controller.setQuickTagLabel(0, "egy, kettő")
        assert controller.quickTagConfigLabels[0] == "egy kettő"

    def test_whitespace_only_clears_slot(self, controller):
        controller.setQuickTagLabel(0, "cím")
        controller.setQuickTagLabel(0, "   ")
        assert controller.quickTagConfigLabels[0] == ""

    @pytest.mark.parametrize("bad_slot", [-1, 8, 99])
    def test_out_of_range_slot_ignored(self, controller, bad_slot):
        before = list(controller.quickTagConfigLabels)
        controller.setQuickTagLabel(bad_slot, "x")
        assert controller.quickTagConfigLabels == before

    def test_persists_across_instances(self, tmp_path, library, controller):
        controller.setQuickTagLabel(3, "tenger")
        controller._get_settings().sync()
        other = _new_controller(tmp_path, library, controller._get_settings())
        assert other.quickTagConfigLabels[3] == "tenger"


class TestQuickTagToggles:
    def test_reserve_recent_toggle_persists(self, tmp_path, library, controller):
        controller.setQuickTagsReserveRecent(False)
        controller._get_settings().sync()
        other = _new_controller(tmp_path, library, controller._get_settings())
        assert other.quickTagsReserveRecent is False

    def test_autofill_toggle_persists(self, tmp_path, library, controller):
        controller.setQuickTagsAutoFillFrequent(True)
        controller._get_settings().sync()
        other = _new_controller(tmp_path, library, controller._get_settings())
        assert other.quickTagsAutoFillFrequent is True


class TestQuickTagButtonsReserveRecent:
    def test_top_two_show_recent_when_reserved(self, controller):
        controller.addKeywordToRows([0], "első")
        controller.addKeywordToRows([1], "második")
        buttons = controller.quickTagButtons
        assert buttons[0] == "második"  # legfrissebb elöl
        assert buttons[1] == "első"

    def test_reusing_a_tag_moves_it_to_front_without_duplicate_slot(
        self, controller
    ):
        controller.addKeywordToRows([0], "első")
        controller.addKeywordToRows([1], "második")
        controller.addKeywordToRows([2], "első")  # újra használva
        buttons = controller.quickTagButtons
        assert buttons[0] == "első"
        assert buttons[1] == "második"

    def test_configured_labels_ignored_on_top_two_when_reserved(self, controller):
        controller.setQuickTagLabel(0, "kézzel írt")
        controller.addKeywordToRows([0], "friss")
        buttons = controller.quickTagButtons
        assert buttons[0] == "friss"  # a kézzel írt címke felülíródik

    def test_top_two_empty_without_history(self, controller):
        assert controller.quickTagButtons[:2] == ["", ""]

    def test_slots_3_to_8_show_configured_labels_even_when_reserved(
        self, controller
    ):
        controller.setQuickTagLabel(2, "hegyek")
        controller.addKeywordToRows([0], "friss")
        assert controller.quickTagButtons[2] == "hegyek"


class TestQuickTagButtonsWithoutReserve:
    def test_top_two_show_configured_labels_when_not_reserved(self, controller):
        controller.setQuickTagsReserveRecent(False)
        controller.setQuickTagLabel(0, "első mező")
        controller.setQuickTagLabel(1, "második mező")
        controller.addKeywordToRows([0], "friss")  # ne írja felül
        buttons = controller.quickTagButtons
        assert buttons[0] == "első mező"
        assert buttons[1] == "második mező"


class TestQuickTagAutoFillFrequent:
    def test_disabled_by_default_leaves_slots_empty(self, controller):
        controller.addKeywordToRows([0], "gyakori")
        controller.addKeywordToRows([1], "gyakori")
        controller.addKeywordToRows([2], "gyakori")
        assert controller.quickTagButtons[2:] == [""] * 6

    def test_fills_empty_slots_by_frequency(self, controller):
        controller.setQuickTagsAutoFillFrequent(True)
        controller.setQuickTagsReserveRecent(False)
        # "gyakori" 3 fotón, "ritka" 1 fotón — a gyakoribb előbb töltendő
        controller.addKeywordToRows([0], "gyakori")
        controller.addKeywordToRows([1], "gyakori")
        controller.addKeywordToRows([2], "gyakori")
        controller.addKeywordToRows([0], "ritka")
        buttons = controller.quickTagButtons
        assert buttons[0] == "gyakori"
        assert buttons[1] == "ritka"
        assert buttons[2:] == [""] * 6

    def test_does_not_duplicate_a_label_already_shown(self, controller):
        controller.setQuickTagsAutoFillFrequent(True)
        controller.setQuickTagsReserveRecent(False)
        controller.setQuickTagLabel(0, "gyakori")  # már szerepel kézzel
        controller.addKeywordToRows([0], "gyakori")
        controller.addKeywordToRows([1], "gyakori")
        buttons = controller.quickTagButtons
        assert buttons[0] == "gyakori"
        assert buttons.count("gyakori") == 1

    def test_leaves_slot_empty_when_no_more_candidates(self, controller):
        controller.setQuickTagsAutoFillFrequent(True)
        controller.setQuickTagsReserveRecent(False)
        controller.addKeywordToRows([0], "egyetlen")
        buttons = controller.quickTagButtons
        assert buttons[0] == "egyetlen"
        assert buttons[1:] == [""] * 7

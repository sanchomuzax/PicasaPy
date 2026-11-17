"""Gyorscímkék (#193) — a Címkék-panel `KeywordsMixin`-hez tartozó
konfigurációs/perzisztencia-logikája: tíz gomb-szlot, „legutóbb használt"
felülírás a felső két gombon, és egyszeri Autofill-művelet.

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


#: #1788: a helyek száma 8 → 10 lett (`edit_0`…`edit_9` + `cmp eax, 0xa`).
#: A tesztek a KONSTANSRA hivatkoznak, hogy a szám egy helyen éljen — a
#: tízes szám MAGA külön állítás (`test_tiz_hely_van`), különben egy
#: visszacsúszás 10-ről 8-ra némán zöld maradna.
SZLOTOK = 10


def _set_index_keywords(controller, keywords_by_name):
    """Tesztadat: a címkekészletet az indexben állítja be, sorrend szerint."""
    from picasapy.index import open_index

    with open_index(controller._db_path) as conn:
        for name, keywords in keywords_by_name.items():
            conn.execute(
                "UPDATE photos SET keywords_ini = ?, keywords_file = ? "
                "WHERE name = ?",
                (keywords, keywords, name),
            )
        conn.commit()


class TestQuickTagDefaults:
    def test_tiz_hely_van(self):
        """#1788: az eredetiben TÍZ gyorscímke-hely van, nem nyolc."""
        from picasapy.app.keywords_controller import _QUICK_TAG_SLOTS

        assert _QUICK_TAG_SLOTS == SZLOTOK == 10

    def test_default_labels_all_empty(self, controller):
        assert controller.quickTagConfigLabels == [""] * SZLOTOK

    def test_default_reserve_recent_is_true(self, controller):
        assert controller.quickTagsReserveRecent is True

    def test_default_buttons_all_empty(self, controller):
        assert controller.quickTagButtons == [""] * SZLOTOK


def test_keywords_of_rows_frequency_then_reverse_ascii_name_5817():
    """A címkelista a gyakoriságot és csak ASCII-betűknél hajtást követi."""
    from types import SimpleNamespace

    from picasapy.app.keywords_controller import KeywordsMixin

    subject = SimpleNamespace(
        _photos=SimpleNamespace(
            photos=[
                SimpleNamespace(
                    keywords="ALPHA, Zulu, Árvíz, árvíz, common"
                ),
                SimpleNamespace(keywords="COMMON, beta"),
            ]
        )
    )

    assert KeywordsMixin.keywordsOfRows(subject, [0, 1]) == [
        "common",
        "árvíz",
        "Árvíz",
        "Zulu",
        "beta",
        "ALPHA",
    ]


class TestSetQuickTagLabel:
    def test_sets_single_slot(self, controller):
        controller.setQuickTagLabel(2, "nyaralás")
        labels = controller.quickTagConfigLabels
        assert labels[2] == "nyaralás"
        assert labels.count("") == SZLOTOK - 1

    def test_comma_stripped_like_regular_keywords(self, controller):
        controller.setQuickTagLabel(0, "egy, kettő")
        assert controller.quickTagConfigLabels[0] == "egy kettő"

    def test_whitespace_only_clears_slot(self, controller):
        controller.setQuickTagLabel(0, "cím")
        controller.setQuickTagLabel(0, "   ")
        assert controller.quickTagConfigLabels[0] == ""

    @pytest.mark.parametrize("bad_slot", [-1, SZLOTOK, 99])
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

class TestQuickTagButtonsReserveRecent:
    def test_top_two_show_recent_when_reserved(self, controller):
        controller.addKeywordToRows([0], "első")
        controller.addKeywordToRows([1], "második")
        buttons = controller.quickTagButtons
        assert buttons[0] == "második"  # legfrissebb elöl
        assert buttons[1] == "első"

    @pytest.mark.parametrize(
        ("recent", "keyword", "expected"),
        [
            (["második", "első"], "első", ["második", "első"]),
            (["első", "második"], "második", ["első", "második"]),
            (["első", "második"], "ELSŐ", ["ELSŐ", "első"]),
        ],
    )
    def test_reusing_either_recent_tag_keeps_its_order(
        self, controller, recent, keyword, expected
    ):
        controller._get_settings().setValue("quickTags/recentKeywords", recent)

        controller.addKeywordToRows([0], keyword)

        assert controller._quick_tag_recent() == expected

    def test_new_tag_keeps_only_two_recents_and_does_not_move_manual_slots(
        self, controller
    ):
        controller._get_settings().setValue(
            "quickTags/recentKeywords", ["régi első", "régi második"]
        )
        for slot in range(SZLOTOK):
            controller.setQuickTagLabel(slot, f"kézi {slot}")

        controller.addKeywordToRows([0], "új címke")

        assert controller._quick_tag_recent() == ["új címke", "régi első"]
        assert controller.quickTagConfigLabels == [
            f"kézi {slot}" for slot in range(SZLOTOK)
        ]

    def test_repeating_recent_trims_legacy_tail_without_reordering(self, controller):
        recent = ["újabb", "régebbi", *(f"régi {i}" for i in range(6))]
        controller._get_settings().setValue("quickTags/recentKeywords", recent)

        controller.addKeywordToRows([0], "régebbi")

        assert controller._quick_tag_recent() == ["újabb", "régebbi"]

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
    def test_adding_tag_without_reserving_recents_keeps_history_unchanged(
        self, controller
    ):
        controller.addKeywordToRows([0], "korábbi első")
        controller.addKeywordToRows([1], "korábbi második")
        korabbi = controller._quick_tag_recent()

        controller.setQuickTagsReserveRecent(False)
        controller.addKeywordToRows([2], "új címke")

        assert controller._quick_tag_recent() == korabbi

    def test_top_two_show_configured_labels_when_not_reserved(self, controller):
        controller.setQuickTagsReserveRecent(False)
        controller.setQuickTagLabel(0, "első mező")
        controller.setQuickTagLabel(1, "második mező")
        controller.addKeywordToRows([0], "friss")  # ne írja felül
        buttons = controller.quickTagButtons
        assert buttons[0] == "első mező"
        assert buttons[1] == "második mező"


class TestQuickTagAutoFill:
    def test_candidates_keep_first_occurrence_and_case_sensitive_identity(
        self, controller
    ):
        _set_index_keywords(
            controller,
            {
                "a.jpg": "Nap, Nap, nap, alpha",
                "b.jpg": "beta, Nap",
                "c.jpg": "gamma",
            },
        )
        controller.setQuickTagsReserveRecent(False)
        controller._get_settings().setValue(
            "quickTags/recentKeywords", ["beta", "recent-ketto"]
        )
        controller.beginQuickTagAutofill()

        result = controller.autofillQuickTagLabels(
            ["  kézi  ", "   ", *([""] * (SZLOTOK - 2))]
        )

        assert result == [
            "  kézi  ", "Nap", "nap", "alpha", "gamma",
            "", "", "", "", "",
        ]
        assert controller.quickTagConfigLabels[1:5] == [
            "Nap", "nap", "alpha", "gamma"
        ]

    def test_reserved_recent_slots_are_never_written(self, controller):
        _set_index_keywords(
            controller,
            {"a.jpg": "recent-egy, Nap, nap", "b.jpg": "alpha"},
        )
        controller._get_settings().setValue(
            "quickTags/recentKeywords", ["recent-egy"]
        )
        controller.setQuickTagLabel(0, "kézi nulla")
        controller.setQuickTagLabel(1, "kézi egy")
        controller.beginQuickTagAutofill()

        result = controller.autofillQuickTagLabels(
            ["kézi nulla", "kézi egy", *([""] * (SZLOTOK - 2))]
        )

        assert result[:5] == ["kézi nulla", "kézi egy", "Nap", "nap", "alpha"]
        assert controller.quickTagConfigLabels[:2] == ["kézi nulla", "kézi egy"]

    def test_repeated_fill_uses_next_candidate_then_stays_exhausted(self, controller):
        names = ["a.jpg", "b.jpg", "c.jpg"]
        candidates = [f"cimke-{i}" for i in range(12)]
        _set_index_keywords(
            controller,
            {name: ", ".join(candidates[index * 4 : index * 4 + 4])
             for index, name in enumerate(names)},
        )
        controller.setQuickTagsReserveRecent(False)
        controller.beginQuickTagAutofill()

        filled = controller.autofillQuickTagLabels([""] * SZLOTOK)
        assert filled == candidates[:10]
        cleared = ["", *filled[1:]]
        refilled = controller.autofillQuickTagLabels(cleared)
        assert refilled[0] == candidates[10]
        assert refilled[1:] == candidates[1:10]
        second_clear = ["", *refilled[1:]]
        second_refill = controller.autofillQuickTagLabels(second_clear)
        assert second_refill[0] == candidates[11]
        exhausted = ["", *second_refill[1:]]
        assert controller.autofillQuickTagLabels(exhausted) == exhausted

    def test_button_availability_requires_a_candidate(self, controller):
        assert controller.quickTagAutofillAvailable is False

        _set_index_keywords(controller, {"a.jpg": "Nap"})
        controller.beginQuickTagAutofill()

        assert controller.quickTagAutofillAvailable is True

    def test_candidate_list_excludes_recent_values_and_stops_at_100(self, controller):
        candidates = [f"cimke-{index}" for index in range(110)]
        _set_index_keywords(
            controller, {"a.jpg": ", ".join(["", *candidates, ""])}
        )
        controller._get_settings().setValue(
            "quickTags/recentKeywords", candidates[:2]
        )

        result = controller._quick_tag_autofill_candidates()

        assert result == candidates[2:100]
        assert len(result) == 98
        assert "" not in result
        assert not set(candidates[:2]).intersection(result)


class TestLegacyQuickTagAutoFillMigration:
    def test_persists_the_old_displayed_labels_and_removes_old_setting(
        self, controller
    ):
        from picasapy.app.keywords_controller import _KEY_QUICK_AUTOFILL

        _set_index_keywords(
            controller,
            {
                "a.jpg": "ritka, gyakori",
                "b.jpg": "gyakori, masik",
                "c.jpg": "gyakori",
            },
        )
        settings = controller._get_settings()
        settings.setValue(_KEY_QUICK_AUTOFILL, True)
        settings.setValue("quickTags/recentKeywords", ["legutobbi"])

        buttons = controller.quickTagButtons

        assert buttons[:4] == ["legutobbi", "gyakori", "masik", "ritka"]
        assert settings.contains(_KEY_QUICK_AUTOFILL) is False
        assert controller.quickTagConfigLabels[:4] == buttons[:4]

        _set_index_keywords(controller, {"a.jpg": "uj-cimke"})
        assert _new_controller(
            controller._db_path.parent,
            controller._photos.photos[0].folder_path,
            settings,
        ).quickTagButtons[:4] == buttons[:4]

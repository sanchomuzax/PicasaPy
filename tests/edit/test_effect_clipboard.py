"""`effect_clipboard` — a "mit viszünk át" szabály és a másolás/beillesztés
tiszta logikája (#426)."""

from picasapy.edit.effect_clipboard import (
    EXCLUDED_FILTER_NAMES,
    copy_all_effects,
    is_transferable,
    paste_all_effects,
)


class TestExcludedFilterNames:
    """A gépi szabály (`filterdesc` `mode="history"`/`persist="1"`) pontosan
    a #426 jegyben megnevezett halmazt adja."""

    def test_matches_issue_exclusion_list(self):
        # docs/specs/filterdesc-registry.md alapján levezetett halmaz — a
        # crop64/crop/redeye/retouch a mode="history" (redeye/retouch
        # ráadásul persist="1" is), a save/rot a history-only könyvelés
        # további tagjai, a moviestart/movieend pedig a modul docstringjében
        # dokumentált, explicit kiegészítés.
        assert EXCLUDED_FILTER_NAMES == frozenset(
            {
                "save",
                "crop64",
                "crop",
                "redeye",
                "retouch",
                "picnik",
                "rot",
                "moviestart",
                "movieend",
            }
        )

    def test_issue_named_entries_all_excluded(self):
        # a jegy szövegében kifejezetten megnevezett öt bejegyzés mindegyike
        # benne van — ez a legszorosabb elfogadási kritérium
        for name in ("crop64", "crop", "redeye", "retouch", "moviestart", "movieend"):
            assert not is_transferable(name)

    def test_ordinary_effects_transferable(self):
        for name in ("finetune2", "sat", "Vignette", "unsharp2", "glow2", "enhance"):
            assert is_transferable(name)

    def test_case_insensitive(self):
        assert not is_transferable("CROP64")
        assert not is_transferable("ReDeYe")


class TestCopyAllEffects:
    def test_strips_excluded_entries(self):
        chain = (
            "enhance=1;crop64=1,45930000ba03defe;"
            "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
            "redeye=1;retouch=1,10000000f1ddff49;"
        )
        result = copy_all_effects(chain)
        assert "crop64" not in result
        assert "redeye" not in result
        assert "retouch" not in result
        assert result == (
            "enhance=1;"
            "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
        )

    def test_preserves_order_of_kept_entries(self):
        chain = "sat=1,0.2;contrast=1,0.1;Vignette=1,35.0,1.4,0.0,00000000;"
        assert copy_all_effects(chain) == chain

    def test_none_input_gives_empty_chain(self):
        assert copy_all_effects(None) == ""

    def test_empty_input_gives_empty_chain(self):
        assert copy_all_effects("") == ""

    def test_all_excluded_gives_empty_chain(self):
        chain = "crop64=1,45930000ba03defe;redeye=1;"
        assert copy_all_effects(chain) == ""

    def test_unknown_filter_name_is_transferable(self):
        # ismeretlen (jövőbeli) szűrőnév a round-trip elv szerint átmegy,
        # nem dobódik el hallgatólagosan
        chain = "brandNewFilter=1,1.0;"
        assert copy_all_effects(chain) == chain


class TestPasteAllEffects:
    def test_returns_clipboard_value_verbatim(self):
        clipboard = "sat=1,0.2;contrast=1,0.1;"
        assert paste_all_effects(clipboard) == clipboard

    def test_empty_clipboard_clears_target(self):
        assert paste_all_effects("") == ""

    def test_roundtrip_copy_then_paste_excludes_geometry(self):
        source_chain = (
            "crop64=1,45930000ba03defe;sat=1,0.2;retouch=1,10000000f1ddff49;"
        )
        clipboard = copy_all_effects(source_chain)
        target_result = paste_all_effects(clipboard)
        assert "crop64" not in target_result
        assert "retouch" not in target_result
        assert target_result == "sat=1,0.2;"

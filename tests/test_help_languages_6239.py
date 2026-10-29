"""#6239: a beépített súgó tartalma követi a felület nyelvét."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PySide6.QtCore import Property

from picasapy.app.help_controller import HelpMixin
from picasapy.help_content import (
    fejezetek,
    fejezet_szovege,
    hivatkozas_celja,
)


_TRANSLATED = {
    "faq.md",
    "getting-started.md",
    "index.md",
    "features/adatbazis.md",
    "features/ajandek-cd.md",
    "features/beallitasok.md",
    "features/billentyuk.md",
    "features/biztonsagi-mentes.md",
    "features/csillag-felirat-cimke.md",
    "features/csoportos-szerkesztes.md",
    "features/duplikatumok.md",
    "features/effektek.md",
    "features/email.md",
    "features/exportalas.md",
    "features/fajlmuveletek.md",
    "features/google-fotok.md",
    "features/hatterkep.md",
    "features/helyek.md",
    "features/importalas.md",
    "features/kepernyovedo.md",
    "features/kereses.md",
    "features/kollazs.md",
    "features/mappakezelo.md",
    "features/meg-nem-erheto-el.md",
    "features/mentes.md",
    "features/mozgofilm.md",
    "features/nyomtatas.md",
    "features/nezegetes.md",
    "features/szerkeszto.md",
    "features/emberek.md",
    "features/poszter.md",
    "features/sugo.md",
    "features/utlevelkep.md",
}
_MISSING = {
    "changelog-user.md",
    "features/konyvtar.md",
}
_SUGO = Path(__file__).parents[1] / "src/picasapy/help"
_TS = Path(__file__).parents[1] / "src/picasapy/app/i18n/picasapy_hu.ts"


class _EnglishHelp(HelpMixin):
    @Property(str, constant=True)
    def language(self) -> str:
        return "en"


def _normalise(text: str) -> str:
    return " ".join(text.replace("&", "").split())


def test_english_help_is_explicitly_partial_until_every_page_is_translated():
    hungarian = set(fejezetek(language="hu"))
    english = set(fejezetek(language="en"))
    assert english == _TRANSLATED, f"angol súgólapok eltérése: {sorted(english ^ _TRANSLATED)}"
    assert hungarian == _TRANSLATED | _MISSING, (
        f"a fordítási állapot nincs teljesen felsorolva: {sorted(hungarian ^ (_TRANSLATED | _MISSING))}"
    )


def test_english_ui_gets_english_text_and_never_falls_back_to_hungarian():
    help_controller = _EnglishHelp()
    text = help_controller.helpTopicText("index.md")
    assert "PicasaPy Help" in text
    assert "PicasaPy súgó" not in text
    assert help_controller.helpTopicText("features/konyvtar.md") == ""
    assert help_controller.helpSearch("internet")


def test_translated_pages_are_not_served_from_the_hungarian_tree():
    for chapter in sorted(_TRANSLATED):
        english = fejezet_szovege(chapter, language="en")
        hungarian = fejezet_szovege(chapter, language="hu")
        assert english and hungarian
        assert _normalise(english) != _normalise(hungarian), chapter
        visible_text = re.sub(r"\]\([^)]*\)", "](...)", english)
        assert not re.search(
            r"\b(súgó|mappák|beállítások|nézőben|képek|adatbázis|nyomtatás|"
            r"igazságforrás|felirat|töröld)\b",
            visible_text,
            re.I,
        ), chapter


def test_translated_pages_keep_the_hungarian_link_targets_and_resolve_in_english():
    for chapter in sorted(_TRANSLATED):
        english = fejezet_szovege(chapter, language="en") or ""
        hungarian = fejezet_szovege(chapter, language="hu") or ""
        english_links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", english)
        hungarian_links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", hungarian)
        assert english_links == hungarian_links, chapter
        for target in english_links:
            if target in _TRANSLATED:
                assert hivatkozas_celja(chapter, target, language="en") == target


def test_english_ui_names_in_bold_are_original_picasa_ts_sources():
    root = ET.parse(_TS).getroot()
    sources = {_normalise(node.text or "") for node in root.iter("source")}
    bold_names = set()
    for chapter in _TRANSLATED:
        text = (_SUGO / "en" / chapter).read_text(encoding="utf-8")
        bold_names.update(_normalise(match) for match in re.findall(r"\*\*(.+?)\*\*", text, re.S))
    missing = sorted(name for name in bold_names if name not in sources)
    assert not missing, f"nincs eredeti Picasa <source> a félkövér felületi névhez: {missing}"

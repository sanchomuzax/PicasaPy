"""A japán fordítás teljességi és formázási őre (#5037)."""

from collections import Counter
from pathlib import Path
import re
from xml.etree import ElementTree as ET


_TS = Path(__file__).parents[1] / "src/picasapy/app/i18n/picasapy_ja.ts"
_PROTECTED = re.compile(r"%(?:n|\d+|[diu])|\{[\w]+\}")
_HTML_TAG = re.compile(r"</?[A-Za-z][^<>]*?>")
_NEW_MENU_SHORTCUTS = {
    "Re&verse sort": "V",
    "&Search for": "S",
    "&Simplified Tree View": "S",
    "&Reverse order": "R",
    "Recent &changes": "C",
    "&Clear Selection": "C",
    "Upload to Google &Photos...": "P",
    "&Manual order": "M",
}


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _signature(text: str) -> tuple[Counter[str], Counter[str], int]:
    return (
        Counter(_PROTECTED.findall(text)),
        Counter(_HTML_TAG.findall(text)),
        text.count("\n"),
    )


def test_japanese_catalog_has_no_unfinished_messages() -> None:
    root = ET.parse(_TS).getroot()
    unfinished = [
        f"{_text(context.find('name'))}: {_text(message.find('source'))}"
        for context in root.findall("context")
        for message in context.findall("message")
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, f"{len(unfinished)} fordítás unfinished maradt; példák: {unfinished[:12]}"


def test_japanese_translations_preserve_placeholders_markup_and_breaks() -> None:
    root = ET.parse(_TS).getroot()
    mismatches: list[str] = []
    for context in root.findall("context"):
        context_name = _text(context.find("name"))
        for message in context.findall("message"):
            source = _text(message.find("source"))
            translation = message.find("translation")
            if translation is None:
                continue

            variants = translation.findall("numerusform") or [translation]
            for variant in variants:
                translated = _text(variant)
                if _signature(source) != _signature(translated):
                    mismatches.append(f"{context_name}: {source!r} -> {translated!r}")

    assert not mismatches, (
        f"{len(mismatches)} fordításban eltér a helyőrző, HTML vagy sortörés; "
        f"példák: {mismatches[:12]}"
    )


def test_new_japanese_menu_shortcuts_keep_picasa_style() -> None:
    root = ET.parse(_TS).getroot()
    seen: set[str] = set()
    for context in root.findall("context"):
        for message in context.findall("message"):
            source = _text(message.find("source"))
            if source not in _NEW_MENU_SHORTCUTS:
                continue
            translation = message.find("translation")
            translated = _text(translation)
            shortcut = _NEW_MENU_SHORTCUTS[source]
            suffix = re.compile(rf"\(&{re.escape(shortcut)}\)(?:\.{{3}}|…)?$", re.IGNORECASE)
            assert suffix.search(translated), f"{source!r} gyorsbillentyűje hiányzik vagy rossz: {translated!r}"
            seen.add(source)

    assert seen == set(_NEW_MENU_SHORTCUTS), f"hiányzó menüsorok: {set(_NEW_MENU_SHORTCUTS) - seen}"

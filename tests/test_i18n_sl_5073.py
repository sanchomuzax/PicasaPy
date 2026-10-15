"""Teljességi és helyőrző-őr a szlovén fordítási katalógushoz (#5073)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SL_CATALOG = ROOT / "src/picasapy/app/i18n/picasapy_sl.ts"
EN_CATALOG = ROOT / "src/picasapy/app/i18n/picasapy_en.ts"

_QT_PLACEHOLDER = re.compile(r"%(?:L?n|L?\d+(?:\$[a-zA-Z])?|[sdif])")
_BRACE_PLACEHOLDER = re.compile(r"\{[^{}]*\}")
_HTML_TAG = re.compile(r"<\s*/?\s*[A-Za-z][^>]*>")


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name", ""), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _key(context: str, message: ET.Element) -> tuple[str, str, str | None]:
    return (
        context,
        message.findtext("source", ""),
        message.get("numerus"),
    )


def _signature(text: str) -> tuple[Counter[str], tuple[str, ...], int]:
    """A Qt-fordításokban megtartandó formázóelemek aláírása."""
    return (
        Counter(_QT_PLACEHOLDER.findall(text) + _BRACE_PLACEHOLDER.findall(text)),
        tuple(_HTML_TAG.findall(text)),
        text.count("\n"),
    )


def _shortcut_count(text: str) -> int:
    # A „B&W” rövidítés ampersandje szó szerinti karakter, nem gyorsbillentyű.
    return text.count("&") - text.count("B&W")


def test_every_slovene_message_is_finished() -> None:
    unfinished = [
        (context, message.findtext("source", ""))
        for context, message in _messages(SL_CATALOG)
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} befejezetlen szlovén üzenet maradt; "
        f"példák: {unfinished[:5]!r}"
    )


def test_slovene_translations_preserve_placeholders_and_plural_forms() -> None:
    english_by_key: dict[tuple[str, str, str | None], list[ET.Element]] = defaultdict(list)
    for context, message in _messages(EN_CATALOG):
        english_by_key[_key(context, message)].append(message)

    for context, message in _messages(SL_CATALOG):
        key = _key(context, message)
        english_matches = english_by_key[key]
        assert english_matches, f"Nincs angol megfelelő: {key!r}"
        source = message.findtext("source", "")
        english_source = english_matches[0].findtext("source", "")
        assert _signature(source) == _signature(english_source), (
            f"A szlovén és angol katalógus forrás-aláírása eltér: {key!r}"
        )

        translation = message.find("translation")
        assert translation is not None, f"Hiányzó fordítási elem: {key!r}"
        if message.get("numerus") == "yes":
            forms = translation.findall("numerusform")
            assert len(forms) == 4, (
                f"A szlovén többes üzenetnek négy alak kell: {key!r}; "
                f"kapott alakok: {len(forms)}"
            )
            translated_texts = [form.text or "" for form in forms]
        else:
            translated_texts = ["".join(translation.itertext())]

        for form_index, translated_text in enumerate(translated_texts):
            assert translated_text.strip(), (
                f"Üres szlovén fordítás: {key!r}, alak={form_index}"
            )
            assert _signature(source) == _signature(translated_text), (
                f"Eltérő helyőrző-, HTML-, sortörés- vagy gyorsbillentyű-aláírás: "
                f"{key!r}, alak={form_index}; "
                f"forrás={_signature(source)!r}, fordítás={_signature(translated_text)!r}"
            )
            if "picasapy-origin: picasapy" in message.findtext("extracomment", ""):
                assert _shortcut_count(source) == _shortcut_count(translated_text), (
                    f"Eltérő gyorsbillentyű-aláírás: {key!r}, alak={form_index}"
                )

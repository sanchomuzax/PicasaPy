"""A katalán katalógus teljességét és formázási helyőrzőit őrzi (#5082)."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


_CA_TS = (
    Path(__file__).resolve().parents[1]
    / "src/picasapy/app/i18n/picasapy_ca.ts"
)
_PLACEHOLDER = re.compile(r"%L?\d+|%n|%[A-Za-z]|\{(?:\d+|[A-Za-z_]\w*)\}")


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _messages():
    root = ET.parse(_CA_TS).getroot()
    for context in root.findall("context"):
        context_name = context.findtext("name", "")
        for message in context.findall("message"):
            yield context_name, message


def _translation_forms(translation: ET.Element) -> list[str]:
    forms = translation.findall("numerusform")
    return [_text(form) for form in forms] or [_text(translation)]


def test_catalan_catalog_has_no_unfinished_messages():
    unfinished = [
        f"{context}: {_text(message.find('source'))}"
        for context, message in _messages()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished katalán üzenet maradt; példák: "
        + "; ".join(unfinished[:8])
    )


def test_catalan_translations_preserve_placeholder_signatures():
    mismatches = []
    for context, message in _messages():
        source = _text(message.find("source"))
        translation = message.find("translation")
        if translation is None:
            mismatches.append(f"{context}: hiányzó fordítás: {source!r}")
            continue

        expected = Counter(_PLACEHOLDER.findall(source))
        for translated in _translation_forms(translation):
            actual = Counter(_PLACEHOLDER.findall(translated))
            if actual != expected:
                mismatches.append(
                    f"{context}: helyőrző-eltérés: {source!r} -> {translated!r}"
                )

    assert not mismatches, "\n".join(mismatches[:20])

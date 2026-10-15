"""A francia katalógus teljességét és helyőrzőit őrzi (#5021)."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


I18N_DIR = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
PLACEHOLDER_RE = re.compile(r"%L?\d+|%n|%[diu]|\{(?:\d+|[A-Za-z_]\w*)\}")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name", ""), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _translation_forms(translation: ET.Element) -> list[str]:
    forms = translation.findall("numerusform")
    if forms:
        return ["".join(form.itertext()) for form in forms]
    return ["".join(translation.itertext())]


def _signature(text: str) -> Counter[str]:
    return Counter(PLACEHOLDER_RE.findall(text))


def _html_signature(text: str) -> list[str]:
    return HTML_TAG_RE.findall(text)


def _aligned_catalogs() -> list[tuple[str, ET.Element, ET.Element]]:
    french = _messages(I18N_DIR / "picasapy_fr.ts")
    english = _messages(I18N_DIR / "picasapy_en.ts")
    assert len(french) == len(english)

    aligned = []
    for (fr_context, fr_message), (en_context, en_message) in zip(french, english, strict=True):
        assert fr_context == en_context
        assert fr_message.findtext("source", "") == en_message.findtext("source", "")
        aligned.append((fr_context, fr_message, en_message))
    return aligned


def test_french_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"{context}: {message.findtext('source', '')}"
        for context, message, _ in _aligned_catalogs()
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished French translations remain; "
        f"first entries: {unfinished[:10]}"
    )


def test_french_translations_keep_source_placeholder_signatures() -> None:
    missing = []
    mismatches = []
    formatting_mismatches = []
    for context, french_message, english_message in _aligned_catalogs():
        source = english_message.findtext("source", "")
        translation = french_message.find("translation")
        forms = _translation_forms(translation) if translation is not None else []
        if not forms or any(not form.strip() for form in forms):
            missing.append(f"{context}: {source}")
            continue

        expected = _signature(source)
        for form in forms:
            actual = _signature(form)
            if actual != expected:
                mismatches.append((context, source, form, expected, actual))
            if source.count("\n") != form.count("\n") or _html_signature(source) != _html_signature(form):
                formatting_mismatches.append((context, source, form))

    assert not missing, f"{len(missing)} French translations are empty; first: {missing[:10]}"
    assert not mismatches, f"French placeholder signatures differ: {mismatches[:10]}"
    assert not formatting_mismatches, f"French line breaks or HTML tags differ: {formatting_mismatches[:10]}"

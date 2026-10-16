"""#5066: Bulgarian translations are complete and preserve source formatting."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


I18N_DIR = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
PLACEHOLDER_RE = re.compile(r"%L?\d+|%n|%[diu]|\{(?:\d+|[A-Za-z_]\w*)\}")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
MNEMONIC_RE = re.compile(r"(?<!&)&([\w])")
LEGACY_MNEMONIC_EXCEPTIONS = {("FolderContextMenu", "&Color")}


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name", ""), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _aligned_catalogs() -> list[tuple[str, ET.Element, ET.Element]]:
    bulgarian = _messages(I18N_DIR / "picasapy_bg.ts")
    english = _messages(I18N_DIR / "picasapy_en.ts")
    assert len(bulgarian) == len(english)

    aligned = []
    for (bg_context, bg_message), (en_context, en_message) in zip(
        bulgarian, english, strict=True
    ):
        assert bg_context == en_context
        assert bg_message.findtext("source", "") == en_message.findtext(
            "source", ""
        )
        aligned.append((bg_context, bg_message, en_message))
    return aligned


def _forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return []
    forms = translation.findall("numerusform")
    return [_text(form) for form in forms] or [_text(translation)]


def test_bulgarian_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"{context}: {_text(message.find('source'))}"
        for context, message, _ in _aligned_catalogs()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished Bulgarian translations remain; "
        f"first entries: {unfinished[:10]}"
    )


def test_bulgarian_translations_preserve_source_placeholder_signatures() -> None:
    mismatches = []
    for context, bg_message, en_message in _aligned_catalogs():
        source = _text(en_message.find("source"))
        translation = bg_message.find("translation")
        if translation is None or translation.get("type") in {
            "unfinished",
            "obsolete",
            "vanished",
        }:
            continue
        expected = Counter(PLACEHOLDER_RE.findall(source))
        for translated in _forms(bg_message):
            actual = Counter(PLACEHOLDER_RE.findall(translated))
            if actual != expected:
                mismatches.append((context, source, translated, expected, actual))

    assert not mismatches, f"Bulgarian placeholder signatures differ: {mismatches[:10]}"


def test_bulgarian_translations_preserve_markup_line_breaks_and_shortcuts() -> None:
    mismatches = []
    for context, bg_message, en_message in _aligned_catalogs():
        source = _text(en_message.find("source"))
        translation = bg_message.find("translation")
        if translation is None or translation.get("type") in {
            "unfinished",
            "obsolete",
            "vanished",
        }:
            continue

        for translated in _forms(bg_message):
            if HTML_TAG_RE.findall(translated) != HTML_TAG_RE.findall(source):
                mismatches.append((context, source, translated, "HTML tags"))
            if translated.count("\n") != source.count("\n"):
                mismatches.append((context, source, translated, "line breaks"))
            if (context, source) in LEGACY_MNEMONIC_EXCEPTIONS:
                continue
            # In B&W, the ampersand is literal rather than a shortcut.
            normalized_source = source.replace("B&W", "BW")
            normalized_translation = translated.replace("B&W", "BW")
            # Localized Picasa menu strings may add a Bulgarian accelerator;
            # a source accelerator, when present, must not be lost.
            if len(MNEMONIC_RE.findall(normalized_translation)) < len(
                MNEMONIC_RE.findall(normalized_source)
            ):
                mismatches.append((context, source, translated, "mnemonics"))

    assert not mismatches, (
        "Bulgarian translations changed source formatting or shortcuts: "
        f"{mismatches[:10]}"
    )

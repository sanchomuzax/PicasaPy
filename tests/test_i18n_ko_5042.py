"""#5042: a koreai katalógus teljes, és megőrzi a forrás formázását."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


I18N_DIR = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
PLACEHOLDER_RE = re.compile(r"%L?\d+|%n|%[diu]|\{(?:\d+|[A-Za-z_]\w*)\}")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
SHORTCUT_RE = re.compile(r"(?<!&)&([A-Za-z])")


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _catalog(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (_text(context.find("name")), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return []
    forms = translation.findall("numerusform")
    return [_text(form) for form in forms] or [_text(translation)]


def _aligned_catalogs() -> list[tuple[str, ET.Element, ET.Element]]:
    korean = _catalog(I18N_DIR / "picasapy_ko.ts")
    english = _catalog(I18N_DIR / "picasapy_en.ts")
    assert len(korean) == len(english)

    aligned = []
    for (ko_context, ko_message), (en_context, en_message) in zip(
        korean, english, strict=True
    ):
        assert ko_context == en_context
        assert _text(ko_message.find("source")) == _text(en_message.find("source"))
        aligned.append((ko_context, ko_message, en_message))
    return aligned


def test_korean_catalog_is_complete_and_preserves_source_signatures() -> None:
    unfinished = []
    empty = []
    mismatches = []

    for context, korean_message, english_message in _aligned_catalogs():
        source = _text(english_message.find("source"))
        translation = korean_message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            unfinished.append(f"{context}: {source}")
            continue

        forms = _forms(korean_message)
        if not forms or any(not form.strip() for form in forms):
            empty.append(f"{context}: {source}")
            continue

        source_placeholders = Counter(PLACEHOLDER_RE.findall(source))
        source_html = HTML_TAG_RE.findall(source)
        source_newlines = source.count("\n")
        source_mnemonics = Counter(
            letter.upper()
            for letter in SHORTCUT_RE.findall(source.replace("B&W", "BW"))
        )
        for form in forms:
            actual_placeholders = Counter(PLACEHOLDER_RE.findall(form))
            actual_mnemonics = Counter(
                letter.upper() for letter in SHORTCUT_RE.findall(form)
            )
            if actual_placeholders != source_placeholders:
                mismatches.append(
                    (context, source, form, "placeholders", source_placeholders, actual_placeholders)
                )
            if HTML_TAG_RE.findall(form) != source_html:
                mismatches.append((context, source, form, "HTML", source_html, HTML_TAG_RE.findall(form)))
            if form.count("\n") != source_newlines:
                mismatches.append((context, source, form, "line breaks", source_newlines, form.count("\n")))
            source_extra = _text(korean_message.find("extracomment"))
            if "picasapy-origin: picasapy" in source_extra and (
                sum(actual_mnemonics.values()) != sum(source_mnemonics.values())
            ):
                mismatches.append(
                    (context, source, form, "mnemonics", source_mnemonics, actual_mnemonics)
                )

    assert not unfinished, (
        f"{len(unfinished)} unfinished Korean messages remain; "
        f"first entries: {unfinished[:10]}"
    )
    assert not empty, f"{len(empty)} Korean messages are empty; first entries: {empty[:10]}"
    assert not mismatches, f"Korean formatting or placeholder signatures differ: {mismatches[:10]}"

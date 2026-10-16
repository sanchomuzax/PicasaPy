"""#5059: the Greek catalog is complete and preserves source placeholders."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


I18N_DIR = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
PLACEHOLDER_RE = re.compile(r"%L?\d+|%n|%[diu]|\{(?:\d+|[A-Za-z_]\w*)\}")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
MNEMONIC_RE = re.compile(r"(?<!&)&([\w])")


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name", ""), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return []
    forms = translation.findall("numerusform")
    return ["".join(form.itertext()) for form in forms] or [
        "".join(translation.itertext())
    ]


def _aligned_catalogs() -> list[tuple[str, ET.Element, ET.Element]]:
    greek = _messages(I18N_DIR / "picasapy_el.ts")
    english = _messages(I18N_DIR / "picasapy_en.ts")
    assert len(greek) == len(english)

    aligned = []
    for (el_context, el_message), (en_context, en_message) in zip(
        greek, english, strict=True
    ):
        assert el_context == en_context
        assert el_message.findtext("source", "") == en_message.findtext("source", "")
        aligned.append((el_context, el_message, en_message))
    return aligned


def test_greek_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"{context}: {message.findtext('source', '')}"
        for context, message, _ in _aligned_catalogs()
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished Greek translations remain; "
        f"first entries: {unfinished[:10]}"
    )


def test_greek_translations_preserve_source_placeholder_signatures() -> None:
    mismatches = []
    for context, greek_message, english_message in _aligned_catalogs():
        source = english_message.findtext("source", "")
        translation = greek_message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            continue
        expected = Counter(PLACEHOLDER_RE.findall(source))
        for form in _forms(greek_message):
            actual = Counter(PLACEHOLDER_RE.findall(form))
            if actual != expected:
                mismatches.append((context, source, form, expected, actual))

    assert not mismatches, f"Greek placeholder signatures differ: {mismatches[:10]}"


def test_greek_translations_preserve_markup_line_breaks_and_shortcuts() -> None:
    mismatches = []
    for context, greek_message, english_message in _aligned_catalogs():
        source = english_message.findtext("source", "")
        translation = greek_message.find("translation")
        origin = greek_message.findtext("extracomment", "")
        if translation is None or translation.get("type") == "unfinished":
            mismatches.append((context, source, "unfinished"))
            continue

        for form in _forms(greek_message):
            if HTML_TAG_RE.findall(form) != HTML_TAG_RE.findall(source):
                mismatches.append((context, source, form, "HTML tags"))
            if form.count("\n") != source.count("\n"):
                mismatches.append((context, source, form, "line breaks"))

            # Picasa's old B&W label uses a literal ampersand, not a mnemonic.
            normalized_source = source.replace("B&W", "BW")
            normalized_form = form.replace("B&W", "BW")
            if (
                "picasapy-origin: picasapy" in origin
                and len(MNEMONIC_RE.findall(normalized_form))
                != len(MNEMONIC_RE.findall(normalized_source))
            ):
                mismatches.append((context, source, form, "mnemonics"))
            if source == "&Unhide" and len(MNEMONIC_RE.findall(form)) != 1:
                mismatches.append((context, source, form, "mnemonic"))

    assert not mismatches, (
        "Greek translations changed source formatting or shortcuts: "
        f"{mismatches[:10]}"
    )

"""Completeness and placeholder checks for the Vietnamese catalog (#5088)."""

from collections import defaultdict
from pathlib import Path
import re
import xml.etree.ElementTree as ET


I18N_DIR = Path(__file__).parents[1] / "src" / "picasapy" / "app" / "i18n"
PLACEHOLDER = re.compile(r"%\d+|%n|%d|\{[^{}]+\}")


def _messages(path: Path):
    root = ET.parse(path).getroot()
    messages = defaultdict(list)
    for context in root.findall("context"):
        context_name = context.findtext("name") or ""
        for message in context.findall("message"):
            key = (
                context_name,
                message.findtext("source") or "",
                message.findtext("comment") or "",
            )
            messages[key].append(message)
    return messages


def _placeholder_signature(text: str) -> tuple[str, ...]:
    return tuple(sorted(PLACEHOLDER.findall(text)))


def _translation_forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return [""]
    forms = translation.findall("numerusform")
    if forms:
        return ["".join(form.itertext()) for form in forms]
    return ["".join(translation.itertext())]


def test_vietnamese_catalog_is_complete_and_preserves_english_placeholders():
    vietnamese = _messages(I18N_DIR / "picasapy_vi.ts")
    english = _messages(I18N_DIR / "picasapy_en.ts")

    unfinished = [
        (key, message)
        for key, messages in vietnamese.items()
        for message in messages
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
        or not "".join(translation.itertext()).strip()
    ]
    assert not unfinished, (
        f"{len(unfinished)} Vietnamese messages are unfinished; first: "
        f"{unfinished[0][0] if unfinished else ''}"
    )

    mismatches = []
    for key, messages in vietnamese.items():
        english_messages = english.get(key, [])
        assert english_messages, f"No matching English message for {key!r}"
        source_signature = _placeholder_signature(
            "".join(english_messages[0].find("source").itertext())
        )
        for message in messages:
            for form in _translation_forms(message):
                actual_signature = _placeholder_signature(form)
                if actual_signature != source_signature:
                    mismatches.append((key, source_signature, actual_signature))

    assert not mismatches, (
        f"{len(mismatches)} Vietnamese translations have mismatched placeholders; "
        f"first: {mismatches[0] if mismatches else ''}"
    )

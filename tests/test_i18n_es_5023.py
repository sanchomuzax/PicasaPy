"""Guards the completeness and formatting of the Spanish catalog (#5023)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src/picasapy/app/i18n/picasapy_es.ts"

_PLACEHOLDER = re.compile(r"%L?\d+|%n|\{\d+\}")
_HTML_TAG = re.compile(r"</?([A-Za-z][\w:-]*)\b[^>]*?/?>")
_ACCELERATOR = re.compile(r"(?<!&)&(?!&)(?=\S)")

# Keep the established literal B&W spelling and baseline accelerator exceptions
# untouched; the other formatting parts remain checked for these rows.
_LEGACY_ACCELERATOR_EXCEPTIONS = {
    # In these effect names, B&W is the established abbreviation for
    # "black and white"; its ampersand is literal text, not a mnemonic.
    ("EditorPanel", "B&W"),
    ("PhotoViewer", "B&W"),
    ("EditorEffectsTab1", "B&W"),
    ("EditorPanel", "Focal B&W"),
    ("EditorPanel", "Filtered B&W"),
    ("PhotoViewer", "Filtered B&W"),
    ("EditorEffectsTab1", "Focal B&W"),
    ("EditorEffectsTab1", "Filtered B&W"),
    (
        "EditorEffectsTab1",
        "Makes a photo that looks like it was taken with B&W film and a color filter",
    ),
    ("FolderContextMenu", "&Color"),
}


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext())


def _translation_variants(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return []
    forms = translation.findall("numerusform")
    if forms:
        return [_text(form) for form in forms]
    return [_text(translation)]


def _format_signature(value: str) -> tuple[Counter[str], tuple[str, ...], int, int]:
    tags = tuple(
        ("/" if match.group(0).startswith("</") else "") + match.group(1).lower()
        for match in _HTML_TAG.finditer(value)
    )
    return (
        Counter(_PLACEHOLDER.findall(value)),
        tags,
        value.count("\n"),
        value.count("&&"),
    )


def test_spanish_catalog_has_no_unfinished_messages():
    root = ET.parse(CATALOG).getroot()
    unfinished = []
    for context in root.findall("context"):
        name = _text(context.find("name"))
        for message in context.findall("message"):
            translation = message.find("translation")
            if translation is not None and translation.get("type") == "unfinished":
                unfinished.append(f"{name}: {_text(message.find('source'))}")

    assert not unfinished, (
        f"{len(unfinished)} unfinished Spanish messages remain: "
        + "; ".join(unfinished[:10])
    )


def test_spanish_translations_preserve_format_signatures():
    root = ET.parse(CATALOG).getroot()
    mismatches = []
    for context in root.findall("context"):
        name = _text(context.find("name"))
        for message in context.findall("message"):
            source = _text(message.find("source"))
            source_signature = _format_signature(source)
            source_accelerators = len(_ACCELERATOR.findall(source))
            for translation in _translation_variants(message):
                if not translation.strip():
                    continue
                translation_signature = _format_signature(translation)
                translation_accelerators = len(_ACCELERATOR.findall(translation))
                accelerator_mismatch = (
                    source_accelerators
                    and source_accelerators != translation_accelerators
                    and (name, source) not in _LEGACY_ACCELERATOR_EXCEPTIONS
                )
                if source_signature != translation_signature or accelerator_mismatch:
                    mismatches.append(
                        f"{name}: {source!r} -> {translation!r} "
                        f"(forrás={source_signature!r}, fordítás={translation_signature!r}; "
                        f"gyorsbillentyűk={source_accelerators}/{translation_accelerators})"
                    )

    assert not mismatches, (
        f"{len(mismatches)} Spanish translations changed placeholders or formatting: "
        + "; ".join(mismatches[:10])
    )

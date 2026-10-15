"""Fullstendighet og Qt-plassholdere i bokmålkatalogen."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_I18N = Path(__file__).resolve().parents[1] / "src" / "picasapy" / "app" / "i18n"
_NO = _I18N / "picasapy_no.ts"
_EN = _I18N / "picasapy_en.ts"
_SIGNATURE = re.compile(
    r"%n|%[1-9][0-9]*|\{(?:[0-9]+|[A-Za-z_][A-Za-z0-9_]*)\}|&&|</?[A-Za-z][^>]*>|\\n|\n"
)
_LEGACY_MNEMONIC_EXCEPTIONS = {
    ("EditorPanel", "Focal B&W"),
    ("EditorPanel", "B&W"),
    ("EditorPanel", "Filtered B&W"),
    ("PublishPanel", "Choose folders & albums to back up"),
    ("PhotoViewer", "B&W"),
    ("PhotoViewer", "Filtered B&W"),
    ("EditorEffectsTab1", "Focal B&W"),
    ("EditorEffectsTab1", "B&W"),
    ("EditorEffectsTab1", "Filtered B&W"),
    (
        "EditorEffectsTab1",
        "Makes a photo that looks like it was taken with B&W film and a color filter",
    ),
    ("LegacyEffects", "Shadow & Highlight"),
    ("FolderContextMenu", "&Color"),
}


def _mnemonic_count(text: str) -> int:
    return text.count("&") - 2 * text.count("&&")


def _xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    parts = [element.text or ""]
    for child in element:
        parts.extend((f"<{child.tag}>", _xml_text(child), f"</{child.tag}>", child.tail or ""))
    return "".join(parts)


def _signature(text: str) -> Counter[str]:
    return Counter(_SIGNATURE.findall(text))


def test_norwegian_catalog_has_no_unfinished_messages() -> None:
    root = ET.parse(_NO).getroot()
    unfinished = [
        (context.findtext("name") or "", message.findtext("source") or "")
        for context in root.findall("context")
        for message in context.findall("message")
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]
    assert not unfinished, f"{len(unfinished)} unfinished: {unfinished[:10]}"


def test_norwegian_translations_preserve_qt_placeholder_signatures() -> None:
    english = ET.parse(_EN).getroot()
    norwegian = ET.parse(_NO).getroot()
    english_by_context = {
        context.findtext("name"): {
            message.findtext("source"): message
            for message in context.findall("message")
        }
        for context in english.findall("context")
    }
    mismatches: list[str] = []
    for context in norwegian.findall("context"):
        name = context.findtext("name") or ""
        for message in context.findall("message"):
            source = _xml_text(message.find("source"))
            translation = message.find("translation")
            if translation is None or translation.get("type") == "unfinished":
                continue
            english_message = english_by_context.get(name, {}).get(source)
            english_source = (
                _xml_text(english_message.find("source"))
                if english_message is not None
                else source
            )
            source_signature = _signature(english_source)
            forms = translation.findall("numerusform")
            targets = [_xml_text(form) for form in forms] or [_xml_text(translation)]
            for translated in targets:
                translated_signature = _signature(translated)
                if source_signature != translated_signature:
                    mismatches.append(
                        f"{name}: {source!r}: {source_signature} != {translated_signature}"
                    )
    assert not mismatches, "Ulike plassholdere: " + "; ".join(mismatches[:10])


def test_norwegian_translations_preserve_mnemonic_ampersands() -> None:
    root = ET.parse(_NO).getroot()
    mismatches: list[str] = []
    for context in root.findall("context"):
        name = context.findtext("name") or ""
        for message in context.findall("message"):
            source = _xml_text(message.find("source"))
            if (name, source) in _LEGACY_MNEMONIC_EXCEPTIONS:
                continue
            source_count = _mnemonic_count(source)
            if not source_count:
                continue
            translation = message.find("translation")
            forms = translation.findall("numerusform") if translation is not None else []
            targets = [_xml_text(form) for form in forms] or [_xml_text(translation)]
            for target in targets:
                if _mnemonic_count(target) < source_count:
                    mismatches.append(f"{name}: {source!r} -> {target!r}")
    assert not mismatches, "Mangler hurtigvalg: " + "; ".join(mismatches[:10])

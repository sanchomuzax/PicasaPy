"""A thai katalógus teljességét és formázási helyőrzőit őrzi (#5090)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_THAI = (
    Path(__file__).resolve().parents[1]
    / "src/picasapy/app/i18n/picasapy_th.ts"
)
_PLACEHOLDER = re.compile(
    r"%(?:\d+\$[diuoxXfFeEgGaAcsp]|L?\d+|n|[diuoxXfFeEgGaAcsp])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][\w:-]*\b[^>]*?/?>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&|\s)")
_LITERAL_AMPERSANDS = re.compile(r"\bB&W\b", re.IGNORECASE)
_EXISTING_MNEMONIC_EXCEPTIONS = {
    ("PicasaFileMenu", "Save &As..."),
    ("PicasaViewMenu", "Search &Options"),
    ("AlbumContextMenu", "Sort &Album By"),
    ("FolderContextMenu", "&Color"),
    ("FolderListContextMenu", "Sort by &Date"),
}


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _messages():
    root = ET.parse(_THAI).getroot()
    for context in root.findall("context"):
        context_name = _text(context.find("name"))
        for message in context.findall("message"):
            yield context_name, message


def _signature(value: str) -> tuple[Counter[str], Counter[str], int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    normalized = _LITERAL_AMPERSANDS.sub("BW", value)
    return len(_MNEMONIC.findall(normalized))


def test_thai_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"[{context}] {_text(message.find('source'))!r}"
        for context, message in _messages()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} thai üzenet maradt unfinished; "
        f"első példák: {unfinished[:10]!r}"
    )


def test_thai_translations_keep_format_signatures() -> None:
    mismatches = []
    for context, message in _messages():
        source = _text(message.find("source"))
        translation = message.find("translation")
        if translation is None:
            mismatches.append(f"[{context}] {source!r}: hiányzik a fordítás")
            continue

        forms = translation.findall("numerusform") or [translation]
        for index, form in enumerate(forms):
            translated = _text(form)
            if _signature(source) != _signature(translated):
                mismatches.append(
                    f"[{context}] alak {index}: {source!r} -> {translated!r}: "
                    f"{_signature(source)!r} != {_signature(translated)!r}"
                )
                break

    assert not mismatches, (
        f"{len(mismatches)} thai fordítás formázási aláírása hibás; "
        f"első példák: {mismatches[:10]!r}"
    )


def test_thai_translations_keep_source_mnemonics() -> None:
    mismatches = []
    for context, message in _messages():
        source = _text(message.find("source"))
        if (context, source) in _EXISTING_MNEMONIC_EXCEPTIONS:
            continue

        translation = message.find("translation")
        if translation is None:
            mismatches.append(f"[{context}] {source!r}: hiányzik a fordítás")
            continue

        forms = translation.findall("numerusform") or [translation]
        for index, form in enumerate(forms):
            translated = _text(form)
            if _mnemonic_count(translated) < _mnemonic_count(source):
                mismatches.append(
                    f"[{context}] alak {index}: {source!r} -> {translated!r}"
                )
                break

    assert not mismatches, (
        f"{len(mismatches)} thai feliratból hiányzik a forrás gyorsbillentyű-jelölése; "
        f"első példák: {mismatches[:10]!r}"
    )

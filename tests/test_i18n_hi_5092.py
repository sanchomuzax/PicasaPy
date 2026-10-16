"""#5092: the Hindi catalog is complete and preserves translation tokens."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_HINDI = _I18N / "picasapy_hi.ts"
_ENGLISH = _I18N / "picasapy_en.ts"
_PLACEHOLDER = re.compile(r"%L?\d+|%n|%[diouxXeEfFgGaAcsp]|\{\d+\}")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&|\s)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _signature(value: str) -> tuple[Counter[str], Counter[str], int, int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
        len(_MNEMONIC.findall(value)),
    )


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    hindi_root = ET.parse(_HINDI).getroot()
    english_root = ET.parse(_ENGLISH).getroot()
    hindi_messages = [
        (context.findtext("name", ""), message)
        for context in hindi_root.findall("context")
        for message in context.findall("message")
    ]
    english_messages = [
        (context.findtext("name", ""), message)
        for context in english_root.findall("context")
        for message in context.findall("message")
    ]
    assert len(hindi_messages) == len(english_messages)

    aligned = []
    for (hindi_context, hindi_message), (english_context, english_message) in zip(
        hindi_messages, english_messages, strict=True
    ):
        assert hindi_context == english_context
        assert _text(hindi_message.find("source")) == _text(
            english_message.find("source")
        )
        aligned.append((hindi_context, hindi_message, english_message))
    return aligned


def test_hindi_catalog_has_no_unfinished_messages() -> None:
    unfinished = []

    for context_name, message, _ in _aligned_messages():
        translation = message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            unfinished.append(f"[{context_name}] {_text(message.find('source'))!r}")

    assert not unfinished, (
        f"{len(unfinished)} unfinished Hindi messages remain:\n"
        + "\n".join(unfinished[:20])
    )


def test_hindi_catalog_preserves_placeholders_markup_breaks_and_shortcuts() -> None:
    mismatches = []

    for context_name, message, english_message in _aligned_messages():
        source = _text(english_message.find("source"))
        translation = message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            continue

        origin = _text(message.find("extracomment"))
        # Existing Picasa Hindi strings intentionally use their own mnemonic
        # placement, so preserve those legacy rows verbatim.
        compared = 4 if "picasapy-origin: picasapy" in origin else 3
        expected = _signature(source)
        forms = (
            translation.findall("numerusform")
            if message.get("numerus") == "yes"
            else [translation]
        )
        for index, form in enumerate(forms):
            actual = _signature(_text(form))
            if expected[:compared] != actual[:compared]:
                mismatches.append(
                    f"[{context_name}] {source!r} form {index} -> "
                    f"{_text(form)!r}: {expected[:compared]!r} != "
                    f"{actual[:compared]!r}"
                )

    assert not mismatches, (
        f"{len(mismatches)} Hindi placeholder/signature mismatches:\n"
        + "\n".join(mismatches[:20])
    )

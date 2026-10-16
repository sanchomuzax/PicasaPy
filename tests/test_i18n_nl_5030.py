"""#5030: the Dutch catalog is complete and keeps source placeholders intact."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_TS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "picasapy"
    / "app"
    / "i18n"
    / "picasapy_nl.ts"
)
_QT_PLACEHOLDER = re.compile(r"%L?\d+|%n|%[diouxXeEfFgGaAcsp]|\{\d+\}")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&|\s)")


def _text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext())


def _signature(value: str) -> tuple[Counter[str], Counter[str], int, int]:
    """Track interpolation tokens, HTML tags, line breaks, and mnemonics."""
    return (
        Counter(_QT_PLACEHOLDER.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
        len(_MNEMONIC.findall(value)),
    )


def test_dutch_catalog_has_no_unfinished_entries_and_keeps_signatures():
    root = ET.parse(_TS_PATH).getroot()
    unfinished: list[str] = []
    signature_mismatches: list[str] = []

    for context in root.findall("context"):
        context_name = _text(context.find("name"))
        for message in context.findall("message"):
            source = _text(message.find("source"))
            translation = message.find("translation")
            if translation is None or translation.get("type") == "unfinished":
                unfinished.append(f"[{context_name}] {source!r}")
                continue
            # Existing Picasa translations are deliberately left untouched;
            # this ticket adds only PicasaPy-owned Dutch strings.
            origin = _text(message.find("extracomment"))
            if "picasapy-origin: picasapy" not in origin:
                continue
            forms = (
                translation.findall("numerusform")
                if message.get("numerus") == "yes"
                else [translation]
            )
            for index, form in enumerate(forms):
                translated = _text(form)
                if _signature(source) != _signature(translated):
                    signature_mismatches.append(
                        f"[{context_name}] form {index}: {source!r} -> "
                        f"{translated!r}: {_signature(source)!r} != "
                        f"{_signature(translated)!r}"
                    )

    assert not unfinished, (
        f"{len(unfinished)} unfinished Dutch messages remain:\n"
        + "\n".join(unfinished)
    )
    assert not signature_mismatches, (
        f"{len(signature_mismatches)} placeholder/signature mismatches:\n"
        + "\n".join(signature_mismatches)
    )

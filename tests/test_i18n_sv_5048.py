"""Swedish catalog completeness and formatting checks for #5048."""

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
    / "picasapy_sv.ts"
)
_PROTECTED = re.compile(r"%L?\d+|%n|%(?:[diouxXeEfFgGaAcsp])|\{[^{}]+\}")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[\da-f]+;|&|\s)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _has_origin(message: ET.Element, origin: str) -> bool:
    return any(
        line.strip() == f"picasapy-origin: {origin}"
        for line in _text(message.find("extracomment")).splitlines()
    )


def _signature(value: str, *, include_mnemonics: bool = True) -> tuple[Counter[str], Counter[str], int, int]:
    """Track placeholders, HTML tags, line breaks, and optional menu mnemonics."""
    return (
        Counter(_PROTECTED.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
        len(_MNEMONIC.findall(value)) if include_mnemonics else 0,
    )


def _forms(message: ET.Element, translation: ET.Element) -> list[ET.Element]:
    forms = translation.findall("numerusform")
    return forms if message.get("numerus") == "yes" else [translation]


def test_swedish_catalog_has_no_unfinished_or_empty_translations() -> None:
    root = ET.parse(_TS_PATH).getroot()
    incomplete: list[str] = []

    for context in root.findall("context"):
        context_name = _text(context.find("name"))
        for message in context.findall("message"):
            translation = message.find("translation")
            if (
                translation is None
                or translation.get("type") == "unfinished"
                or not _forms(message, translation)
                or any(not _text(form).strip() for form in _forms(message, translation))
            ):
                incomplete.append(f"[{context_name}] {_text(message.find('source'))!r}")

    assert not incomplete, (
        f"{len(incomplete)} incomplete Swedish messages remain:\n"
        + "\n".join(incomplete[:20])
    )


def test_swedish_translations_preserve_placeholders_markup_breaks_and_shortcuts() -> None:
    root = ET.parse(_TS_PATH).getroot()
    mismatches: list[str] = []

    for context in root.findall("context"):
        context_name = _text(context.find("name"))
        for message in context.findall("message"):
            source = _text(message.find("source"))
            translation = message.find("translation")
            if translation is None:
                continue

            if not (_has_origin(message, "picasapy") or _has_origin(message, "picasa")):
                continue

            # Preserve existing official Picasa rows, whose legacy accelerator
            # placement is not consistent across contexts. New PicasaPy rows
            # keep their mnemonic count as well as placeholders and markup.
            include_mnemonics = _has_origin(message, "picasapy")
            expected = _signature(source, include_mnemonics=include_mnemonics)
            for index, form in enumerate(_forms(message, translation)):
                translated = _text(form)
                actual = _signature(translated, include_mnemonics=include_mnemonics)
                if expected != actual:
                    mismatches.append(
                        f"[{context_name}] form {index}: {source!r} -> {translated!r}: "
                        f"{expected!r} != {actual!r}"
                    )

    assert not mismatches, (
        f"{len(mismatches)} Swedish translations changed protected formatting:\n"
        + "\n".join(mismatches[:20])
    )

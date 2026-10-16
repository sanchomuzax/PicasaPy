"""#5101: the Hebrew catalog is complete and preserves source tokens."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_CATALOG = (
    Path(__file__).resolve().parents[1]
    / "src/picasapy/app/i18n/picasapy_iw.ts"
)
_PLACEHOLDER = re.compile(r"%L?\d+|%n|%[diouxXeEfFgGaAcsp]|\{(?:\d+|[A-Za-z_]\w*)\}")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&|\s)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _messages() -> list[tuple[str, ET.Element]]:
    root = ET.parse(_CATALOG).getroot()
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
    return [_text(form) for form in forms] or [_text(translation)]


def test_hebrew_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"[{context}] {_text(message.find('source'))!r}"
        for context, message in _messages()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished Hebrew messages remain:\n"
        + "\n".join(unfinished[:20])
    )


def test_hebrew_translations_preserve_placeholders_markup_breaks_and_shortcuts() -> None:
    mismatches = []

    for context, message in _messages():
        translation = message.find("translation")
        if translation is None or translation.get("type") in {
            "unfinished",
            "obsolete",
            "vanished",
        }:
            continue

        source = _text(message.find("source"))
        origin = _text(message.find("extracomment"))
        source_for_shortcuts = source.replace("B&W", "BW")
        expected = (
            Counter(_PLACEHOLDER.findall(source)),
            Counter(_HTML_TAG.findall(source)),
            source.count("\n"),
            len(_MNEMONIC.findall(source_for_shortcuts)),
        )
        translated_forms = _forms(message)
        if message.get("numerus") == "yes" and not translated_forms:
            mismatches.append(f"[{context}] {source!r}: missing plural forms")
            continue

        for index, translated in enumerate(translated_forms):
            actual = (
                Counter(_PLACEHOLDER.findall(translated)),
                Counter(_HTML_TAG.findall(translated)),
                translated.count("\n"),
                len(_MNEMONIC.findall(translated.replace("B&W", "BW"))),
            )
            # Official Picasa Hebrew strings have established accelerator
            # placement that may differ from the English source.
            compared = 3 if "picasapy-origin: picasa" in origin else 4
            if actual[:compared] != expected[:compared]:
                mismatches.append(
                    f"[{context}] {source!r} form {index}: "
                    f"{expected[:compared]!r} != {actual[:compared]!r}"
                )

    assert not mismatches, (
        f"{len(mismatches)} Hebrew translations changed source formatting:\n"
        + "\n".join(mismatches[:20])
    )


def test_hebrew_plural_messages_have_all_nonempty_forms() -> None:
    missing = []

    for context, message in _messages():
        if message.get("numerus") != "yes":
            continue
        translation = message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            continue
        forms = translation.findall("numerusform")
        if len(forms) != 2 or any(not _text(form).strip() for form in forms):
            missing.append(f"[{context}] {_text(message.find('source'))!r}")

    assert not missing, f"Hebrew plural forms are incomplete: {missing[:20]}"

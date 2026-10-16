"""A román katalógus teljességi és helyőrző-őrje a #5064-hez."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


CATALOG = Path(__file__).parents[1] / "src/picasapy/app/i18n/picasapy_ro.ts"
PLACEHOLDER = re.compile(
    r"%(?:L?\d+|Ln|n|[-+0-9.*]*[diuoxXfFeEgGaAcsp])|\{[^{}]+\}"
)
HTML_TAG = re.compile(r"</?([A-Za-z][A-Za-z0-9]*)\b[^>]*?/?>")
MNEMONIC = re.compile(r"(?<!&)&(?!&)")


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext())


def test_romanian_catalog_has_no_unfinished_translations() -> None:
    root = ET.parse(CATALOG).getroot()
    unfinished: list[str] = []

    for context in root.findall("context"):
        name = _text(context.find("name"))
        for message in context.findall("message"):
            translation = message.find("translation")
            if translation is None or translation.get("type") == "unfinished":
                unfinished.append(f"[{name}] {_text(message.find('source'))!r}")

    assert not unfinished, (
        f"{len(unfinished)} román fordítás maradt unfinished állapotban; "
        f"első példák: {unfinished[:12]!r}"
    )


def test_romanian_translations_preserve_source_placeholders() -> None:
    root = ET.parse(CATALOG).getroot()
    mismatches: list[str] = []

    for context in root.findall("context"):
        name = _text(context.find("name"))
        for message in context.findall("message"):
            source = _text(message.find("source"))
            extra = _text(message.find("extracomment"))
            picasapy_owned = "picasapy-origin: picasapy" in extra
            translation = message.find("translation")
            source_tokens = sorted(PLACEHOLDER.findall(source))
            if translation is None or translation.get("type") == "unfinished":
                if (
                    source_tokens
                    or "\n" in source
                    or HTML_TAG.search(source)
                    or (picasapy_owned and MNEMONIC.search(source))
                ):
                    mismatches.append(
                        f"[{name}] {source!r}: formázott üzenethez nincs "
                        "ellenőrizhető román fordítás"
                    )
                continue
            translations = translation.findall("numerusform") or [translation]
            for translated in translations:
                translated_text = _text(translated)
                translated_tokens = sorted(PLACEHOLDER.findall(translated_text))
                source_tags = sorted(HTML_TAG.findall(source))
                translated_tags = sorted(HTML_TAG.findall(translated_text))
                if (
                    source_tokens != translated_tokens
                    or source.count("\n") != translated_text.count("\n")
                    or source_tags != translated_tags
                    or (
                        picasapy_owned
                        and len(MNEMONIC.findall(source))
                        != len(MNEMONIC.findall(translated_text))
                    )
                ):
                    mismatches.append(
                        f"[{name}] {source!r}: placeholders {source_tokens!r} != "
                        f"{translated_tokens!r}, line breaks {source.count(chr(10))} != "
                        f"{translated_text.count(chr(10))}, HTML {source_tags!r} != "
                        f"{translated_tags!r}, owned shortcuts "
                        f"{len(MNEMONIC.findall(source))} != "
                        f"{len(MNEMONIC.findall(translated_text))}"
                    )

    assert not mismatches, "Eltérő román helyőrzők:\n" + "\n".join(mismatches[:20])


def test_romanian_numerus_messages_have_three_forms() -> None:
    root = ET.parse(CATALOG).getroot()
    incomplete: list[str] = []

    for context in root.findall("context"):
        name = _text(context.find("name"))
        for message in context.findall("message"):
            if message.get("numerus") != "yes":
                continue
            translation = message.find("translation")
            forms = translation.findall("numerusform") if translation is not None else []
            if len(forms) != 3 or any(not _text(form).strip() for form in forms):
                incomplete.append(f"[{name}] {_text(message.find('source'))!r}")

    assert not incomplete, (
        "A román többes szám három alakja nincs kitöltve ezeknél: "
        f"{incomplete[:20]!r}"
    )

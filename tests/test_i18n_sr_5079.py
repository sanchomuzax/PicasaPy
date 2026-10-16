"""Teljességi és formázási őr a szerb fordítási katalógushoz (#5079)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SR_CATALOG = ROOT / "src/picasapy/app/i18n/picasapy_sr.ts"
EN_CATALOG = ROOT / "src/picasapy/app/i18n/picasapy_en.ts"

_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[-+0-9.*]*[diouxXeEfFgGaAcsp])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?\s*[A-Za-z][\w:-]*(?:\s+[^<>]*?)?/?\s*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name", ""), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _signature(value: str) -> tuple[Counter[str], tuple[str, ...], int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        tuple(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    # The ampersand in the literal color label B&W is not a shortcut marker.
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    serbian = _messages(SR_CATALOG)
    english = _messages(EN_CATALOG)
    assert len(serbian) == len(english), "a szerb és angol katalógus elemszáma eltér"

    aligned = []
    for (sr_context, sr_message), (en_context, en_message) in zip(
        serbian, english, strict=True
    ):
        assert sr_context == en_context
        assert _text(sr_message.find("source")) == _text(en_message.find("source"))
        aligned.append((sr_context, sr_message, en_message))
    return aligned


def _forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return []
    forms = translation.findall("numerusform")
    return [_text(form) for form in forms] if forms else [_text(translation)]


def test_serbian_catalog_has_no_unfinished_translations() -> None:
    unfinished = [
        f"[{context}] {_text(english.find('source'))!r}"
        for context, message, english in _aligned_messages()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} szerb fordítás unfinished állapotú; "
        f"első példák: {unfinished[:12]!r}"
    )


def test_serbian_translations_preserve_source_signatures_and_plural_forms() -> None:
    mismatches: list[str] = []
    for context, message, english in _aligned_messages():
        source = _text(english.find("source"))
        translation = message.find("translation")
        if translation is None:
            mismatches.append(f"[{context}] {source!r}: hiányzó fordítás")
            continue
        if translation.get("type") == "unfinished":
            mismatches.append(f"[{context}] {source!r}: unfinished fordítás")
            continue

        forms = _forms(message)
        if message.get("numerus") == "yes" and len(forms) != 3:
            mismatches.append(
                f"[{context}] {source!r}: három alak helyett {len(forms)}"
            )
            continue
        for index, translated in enumerate(forms):
            keep_mnemonics = "picasapy-origin: picasapy" in _text(
                message.find("extracomment")
            )
            if (
                not translated.strip()
                or _signature(source) != _signature(translated)
                or (
                    keep_mnemonics
                    and _mnemonic_count(source) != _mnemonic_count(translated)
                )
            ):
                mismatches.append(
                    f"[{context}] alak {index}: {source!r} -> {translated!r}; "
                    f"{_signature(source)!r} != {_signature(translated)!r}; "
                    f"gyorsbillentyűk {_mnemonic_count(source)} != "
                    f"{_mnemonic_count(translated)}"
                )
                break

    assert not mismatches, (
        f"{len(mismatches)} szerb fordításnál eltér a helyőrző-, HTML- vagy "
        f"sortörés-aláírás, vagy hiányos a többes szám; első példák: "
        f"{mismatches[:12]!r}"
    )

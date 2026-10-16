"""A perzsa fordítás teljességi és formázási őre (#5099)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


_CATALOG = Path(__file__).parents[1] / "src/picasapy/app/i18n/picasapy_fa.ts"
_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[-+0-9.*]*[diouxXeEfFgGaAcsp])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?\s*[A-Za-z][\w:-]*(?:\s+[^<>]*?)?/?\s*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _signature(value: str) -> tuple[Counter[str], tuple[str, ...], int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        tuple(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    # A B&W címkében az ampersand szó szerinti karakter, nem gyorsbillentyű.
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def test_persian_catalog_has_no_unfinished_translations() -> None:
    root = ET.parse(_CATALOG).getroot()
    unfinished = [
        f"{_text(context.find('name'))}: {_text(message.find('source'))}"
        for context in root.findall("context")
        for message in context.findall("message")
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} perzsa fordítás unfinished maradt; példák: "
        f"{unfinished[:12]}"
    )


def test_persian_translations_preserve_placeholders_markup_breaks_and_shortcuts() -> None:
    root = ET.parse(_CATALOG).getroot()
    mismatches: list[str] = []
    for context in root.findall("context"):
        context_name = _text(context.find("name"))
        for message in context.findall("message"):
            source = _text(message.find("source"))
            translation = message.find("translation")
            if translation is None or translation.get("type") == "unfinished":
                continue

            variants = translation.findall("numerusform") or [translation]
            keep_shortcuts = "picasapy-origin: picasapy" in _text(
                message.find("extracomment")
            )
            for index, variant in enumerate(variants):
                translated = _text(variant)
                if (
                    not translated.strip()
                    or _signature(source) != _signature(translated)
                    or (
                        keep_shortcuts
                        and _mnemonic_count(source) != _mnemonic_count(translated)
                    )
                ):
                    mismatches.append(
                        f"{context_name} alak {index}: {source!r} -> {translated!r}"
                    )

    assert not mismatches, (
        f"{len(mismatches)} perzsa fordításnál eltér a helyőrző-, HTML-, "
        f"sortörés- vagy gyorsbillentyű-aláírás; példák: {mismatches[:12]}"
    )

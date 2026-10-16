"""A török katalógus teljessége és a helyőrzők megőrzése (#5046)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]
_I18N = _ROOT / "src" / "picasapy" / "app" / "i18n"
_TURKISH = _I18N / "picasapy_tr.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_PLACEHOLDER = re.compile(r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[diouxXeEfFgG])")
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&|\s)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (_text(context.find("name")), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _signature(value: str) -> tuple[Counter[str], Counter[str], Counter[str], int, int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_BRACE_PLACEHOLDER.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
        len(_MNEMONIC.findall(value)),
    )


def test_turkish_catalog_has_no_unfinished_messages() -> None:
    unfinished: list[str] = []
    for context, message in _messages(_TURKISH):
        translation = message.find("translation")
        if translation is not None and translation.get("type") == "unfinished":
            unfinished.append(f"[{context}] {_text(message.find('source'))!r}")

    assert not unfinished, (
        f"{len(unfinished)} török üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:10]!r}"
    )


def test_turkish_picasapy_translations_keep_format_signatures() -> None:
    mismatches: list[str] = []
    for context, message in _messages(_TURKISH):
        origin = _text(message.find("extracomment"))
        if "picasapy-origin: picasapy" not in origin:
            continue

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
        f"{len(mismatches)} török fordítás formázási aláírása hibás; "
        f"első példák: {mismatches[:10]!r}"
    )

"""A finn fordítás teljességét és formázási aláírásait őrzi (#5055)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_FINNISH = _I18N / "picasapy_fi.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_PLACEHOLDER = re.compile(r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[diouxXeEfFgG])")
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (_text(context.find("name")), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    finnish = _messages(_FINNISH)
    english = _messages(_ENGLISH)
    assert len(finnish) == len(english), "a finn és az angol katalógus üzenetszáma eltér"

    aligned: list[tuple[str, ET.Element, ET.Element]] = []
    for (fi_context, fi_message), (en_context, en_message) in zip(
        finnish, english, strict=True
    ):
        assert fi_context == en_context
        assert _text(fi_message.find("source")) == _text(en_message.find("source"))
        aligned.append((fi_context, fi_message, en_message))
    return aligned


def _format_signature(value: str) -> tuple[Counter[str], Counter[str], Counter[str], int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_BRACE_PLACEHOLDER.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    # B&W-merkinnässä & tarkoittaa sanaa "and", ei pikanäppäintä.
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def test_finnish_catalog_has_no_unfinished_messages() -> None:
    unfinished: list[str] = []
    for context, message, english_message in _aligned_messages():
        translation = message.find("translation")
        if translation is not None and translation.get("type") == "unfinished":
            unfinished.append(f"[{context}] {_text(english_message.find('source'))!r}")

    assert not unfinished, (
        f"{len(unfinished)} finn üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:10]!r}"
    )


def test_finnish_translations_keep_format_signatures() -> None:
    mismatches: list[str] = []
    for context, message, english_message in _aligned_messages():
        translation = message.find("translation")
        source = _text(english_message.find("source"))
        if translation is None or translation.get("type") == "unfinished":
            mismatches.append(f"[{context}] puuttuva suomennos: {source!r}")
            continue

        extra = _text(message.find("extracomment"))
        forms = translation.findall("numerusform") or [translation]
        for index, form in enumerate(forms):
            translated = _text(form)
            expected = _format_signature(source)
            actual = _format_signature(translated)
            if expected != actual:
                mismatches.append(
                    f"[{context}] alak {index}: {source!r} -> {translated!r}: "
                    f"{expected!r} != {actual!r}"
                )
                break
            if "picasapy-origin: picasapy" in extra:
                expected_mnemonics = _mnemonic_count(source)
                actual_mnemonics = _mnemonic_count(translated)
                if expected_mnemonics != actual_mnemonics:
                    mismatches.append(
                        f"[{context}] gyorsbillentyű: {source!r} -> {translated!r}: "
                        f"{expected_mnemonics} != {actual_mnemonics}"
                    )
                    break

    assert not mismatches, (
        f"{len(mismatches)} finn fordítás hiányzik vagy eltér a formázási aláírása; "
        f"első példák: {mismatches[:10]!r}"
    )

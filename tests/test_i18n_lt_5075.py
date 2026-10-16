"""A litván katalógus teljességét őrzi (#5075)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_LITHUANIAN = _I18N / "picasapy_lt.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[-+0-9.*]*[diouxXeEfFgGaAcsp])"
)
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?\s*[A-Za-z][\w:-]*(?:\s+[^<>]*?)?/?\s*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")


def _content(node: ET.Element | None) -> str:
    if node is None:
        return ""
    parts = [node.text or ""]
    for child in node:
        parts.append(ET.tostring(child, encoding="unicode"))
        parts.append(child.tail or "")
    return "".join(parts)


def _signature(
    value: str,
) -> tuple[Counter[str], Counter[str], Counter[str], tuple[str, ...], int]:
    tags = tuple(
        re.sub(r"\s*/\s*>", ">", re.sub(r"\s+", " ", tag.strip()))
        for tag in _HTML_TAG.findall(value)
    )
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_BRACE_PLACEHOLDER.findall(value)),
        Counter(re.findall(r"\\n", value)),
        tags,
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    lithuanian = ET.parse(_LITHUANIAN).getroot()
    english = ET.parse(_ENGLISH).getroot()
    lt_messages = [
        (context.findtext("name") or "", message)
        for context in lithuanian.findall("context")
        for message in context.findall("message")
    ]
    en_messages = [
        (context.findtext("name") or "", message)
        for context in english.findall("context")
        for message in context.findall("message")
    ]
    assert len(lt_messages) == len(en_messages), (
        "a litván és az angol katalógus üzenetszáma eltér"
    )

    aligned: list[tuple[str, ET.Element, ET.Element]] = []
    for (lt_context, lt_message), (en_context, en_message) in zip(
        lt_messages, en_messages, strict=True
    ):
        assert lt_context == en_context
        assert _content(lt_message.find("source")) == _content(
            en_message.find("source")
        )
        aligned.append((lt_context, lt_message, en_message))
    return aligned


def test_lithuanian_catalog_has_no_unfinished_translations() -> None:
    unfinished: list[str] = []
    for context, message, english_message in _aligned_messages():
        translation = message.find("translation")
        forms = translation.findall("numerusform") if translation is not None else []
        translated_forms = forms or ([translation] if translation is not None else [])
        if (
            translation is None
            or translation.get("type") == "unfinished"
            or any(not _content(form).strip() for form in translated_forms)
        ):
            unfinished.append(
                f"[{context}] {_content(english_message.find('source'))!r}"
            )

    assert not unfinished, (
        f"{len(unfinished)} litván fordítás maradt unfinished állapotban; "
        f"első példák: {unfinished[:12]!r}"
    )


def test_lithuanian_translations_preserve_source_signatures() -> None:
    mismatches: list[str] = []
    for context, message, english_message in _aligned_messages():
        source = _content(english_message.find("source"))
        translation = message.find("translation")
        forms = translation.findall("numerusform") if translation is not None else []
        translated_forms = forms or ([translation] if translation is not None else [])
        for index, form in enumerate(translated_forms):
            translated = _content(form)
            if _signature(source) != _signature(translated):
                mismatches.append(
                    f"[{context}] alak {index}: {source!r}: "
                    f"{_signature(source)!r} != {_signature(translated)!r}"
                )
                break

    assert not mismatches, "Eltérő litván formázási aláírások:\n" + "\n".join(
        mismatches[:20]
    )


def test_lithuanian_owned_mnemonics_are_preserved() -> None:
    mismatches: list[str] = []
    for context, message, english_message in _aligned_messages():
        if "picasapy-origin: picasapy" not in _content(message.find("extracomment")):
            continue
        source = _content(english_message.find("source"))
        source_mnemonics = _mnemonic_count(source)
        if not source_mnemonics:
            continue
        translation = message.find("translation")
        forms = translation.findall("numerusform") if translation is not None else []
        translated_forms = forms or ([translation] if translation is not None else [])
        for index, form in enumerate(translated_forms):
            translated_mnemonics = _mnemonic_count(_content(form))
            if translated_mnemonics != source_mnemonics:
                mismatches.append(
                    f"[{context}] alak {index}: {source!r}: "
                    f"{source_mnemonics} != {translated_mnemonics} gyorsbillentyű"
                )
                break

    assert not mismatches, "Eltérő litván gyorsbillentyűk:\n" + "\n".join(
        mismatches[:20]
    )


def test_lithuanian_numerus_messages_have_three_nonempty_forms() -> None:
    incomplete: list[str] = []
    for context, message, english_message in _aligned_messages():
        if message.get("numerus") != "yes":
            continue
        translation = message.find("translation")
        forms = translation.findall("numerusform") if translation is not None else []
        if len(forms) != 3 or any(not _content(form).strip() for form in forms):
            incomplete.append(
                f"[{context}] {_content(english_message.find('source'))!r}"
            )

    assert not incomplete, (
        "A litván többes szám mindhárom alakja nincs kitöltve ezeknél: "
        f"{incomplete[:20]!r}"
    )

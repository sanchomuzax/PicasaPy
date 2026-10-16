"""#5053: a dán fordítás legyen teljes, a formázási jelölők megőrzésével."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_I18N = _ROOT / "src" / "picasapy" / "app" / "i18n"
_DANISH = _I18N / "picasapy_da.ts"
_QT_PLACEHOLDER = re.compile(r"%(?:L[1-9]\d*|L?n|[1-9]\d*|d)")
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")

# Ezt a hivatalos, már kitöltött sort a jegy előtt nem jelölték gyorsbillentyűvel.
_EXISTING_MNEMONIC_EXCEPTIONS = {("FolderContextMenu", "&Color")}


def _messages() -> list[tuple[str, ET.Element]]:
    root = ET.parse(_DANISH).getroot()
    return [
        (context.findtext("name") or "", message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _format_signature(value: str) -> tuple[object, ...]:
    return (
        Counter(_QT_PLACEHOLDER.findall(value)),
        Counter(_BRACE_PLACEHOLDER.findall(value)),
        tuple(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    # A B&W rövidítésben az ampersand az „and” része, nem gyorsbillentyű.
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def _translated_values(translation: ET.Element | None) -> list[str]:
    if translation is None:
        return [""]
    forms = translation.findall("numerusform")
    if forms:
        return ["".join(form.itertext()) for form in forms]
    return ["".join(translation.itertext())]


def test_nincs_forditatlan_dan_uzenet():
    unfinished = [
        (context, message.findtext("source") or "")
        for context, message in _messages()
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} dán üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:10]!r}"
    )


def test_a_dan_forditasok_megorzik_a_formazasi_jeloloket():
    errors: list[str] = []
    for context, message in _messages():
        source = "".join(message.find("source").itertext())
        translations = _translated_values(message.find("translation"))
        for translated in translations:
            if _format_signature(source) != _format_signature(translated):
                errors.append(
                    f"[{context}] {source!r}: eltérő helyőrző/HTML/sortörés "
                    f"({translated!r})"
                )
                break

            if (
                (context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
                and _mnemonic_count(source) > _mnemonic_count(translated)
            ):
                errors.append(
                    f"[{context}] {source!r}: hiányzó gyorsbillentyű-jelölő "
                    f"({translated!r})"
                )
                break

    assert not errors, (
        f"{len(errors)} dán fordítás formázási aláírása hibás; "
        f"első példák: {errors[:10]!r}"
    )

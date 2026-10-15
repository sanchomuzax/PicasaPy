"""A brazíliai portugál katalógus teljessége és formázási jelölői (#5028)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_I18N = _ROOT / "src" / "picasapy" / "app" / "i18n"
_PORTUGUESE = _I18N / "picasapy_pt-BR.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_QT_PLACEHOLDER = re.compile(r"%(?:L[1-9]\d*|L?n|[1-9]\d*|d)")
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")

# Ez a sor a #5028 előtt is elvesztette a Picasa-forrás gyorsbillentyűjét.
_EXISTING_MNEMONIC_EXCEPTIONS = {("FolderContextMenu", "&Color")}


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name") or "", message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _translation_forms(translation: ET.Element) -> list[str]:
    forms = translation.findall("numerusform")
    if forms:
        return ["".join(form.itertext()) for form in forms]
    return ["".join(translation.itertext())]


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


def test_ptbr_catalog_is_complete_and_keeps_format_signatures() -> None:
    portuguese = _messages(_PORTUGUESE)
    english = _messages(_ENGLISH)
    portuguese_keys = Counter(
        (context, message.findtext("source") or "")
        for context, message in portuguese
    )
    english_keys = Counter(
        (context, message.findtext("source") or "")
        for context, message in english
    )
    assert portuguese_keys == english_keys, "a portugál és angol TS kulcsai eltérnek"

    unfinished = [
        (context, message.findtext("source") or "")
        for context, message in portuguese
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]
    assert not unfinished, (
        f"{len(unfinished)} brazíliai portugál üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:10]!r}"
    )

    errors: list[str] = []
    for (pt_context, pt_message), (_en_context, en_message) in zip(
        portuguese, english, strict=True
    ):
        source = en_message.findtext("source") or ""
        translation = pt_message.find("translation")
        translated_values = (
            _translation_forms(translation) if translation is not None else []
        )
        if not translated_values or any(not value.strip() for value in translated_values):
            errors.append(f"[{pt_context}] {source!r}: üres portugál fordítás")
            continue

        for translated in translated_values:
            if _format_signature(source) != _format_signature(translated):
                errors.append(
                    f"[{pt_context}] {source!r}: eltérő helyőrző/HTML/sortörés "
                    f"({translated!r})"
                )
                break

            source_mnemonics = _mnemonic_count(source)
            if (
                (pt_context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
                and _mnemonic_count(translated) < source_mnemonics
            ):
                errors.append(
                    f"[{pt_context}] {source!r}: hiányzó gyorsbillentyű-jelölő "
                    f"({translated!r})"
                )
                break

    assert not errors, (
        f"{len(errors)} brazíliai portugál fordítás formázási aláírása hibás; "
        f"első példák: {errors[:10]!r}"
    )

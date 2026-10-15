"""#5084: complete European Portuguese catalog with intact formatting tokens."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_I18N = _ROOT / "src" / "picasapy" / "app" / "i18n"
_PORTUGUESE = _I18N / "picasapy_pt.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_QT_PLACEHOLDER = re.compile(r"%(?:L[1-9]\d*|L?n|[1-9]\d*|d)")
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")
_EXISTING_MNEMONIC_EXCEPTIONS = {("FolderContextMenu", "&Color")}


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name") or "", message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _text(node: ET.Element | None) -> str:
    return "".join(node.itertext()) if node is not None else ""


def _signature(value: str) -> tuple[object, ...]:
    return (
        Counter(_QT_PLACEHOLDER.findall(value)),
        Counter(_BRACE_PLACEHOLDER.findall(value)),
        tuple(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def test_european_portuguese_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"[{context}] {_text(message.find('source'))!r}"
        for context, message in _messages(_PORTUGUESE)
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} European Portuguese messages remain unfinished:\n"
        + "\n".join(unfinished[:30])
    )


def test_european_portuguese_translations_preserve_source_signatures() -> None:
    portuguese = _messages(_PORTUGUESE)
    english = _messages(_ENGLISH)
    portuguese_keys = [
        (context, _text(message.find("source"))) for context, message in portuguese
    ]
    english_keys = [
        (context, _text(message.find("source"))) for context, message in english
    ]
    assert portuguese_keys == english_keys, (
        "the Portuguese and English TS message keys or ordering differ"
    )

    errors: list[str] = []
    for (context, message), (_, source_message) in zip(
        portuguese, english, strict=True
    ):
        source = _text(source_message.find("source"))
        translation = message.find("translation")
        if (
            translation is None
            or translation.get("type") == "unfinished"
            or not _text(translation).strip()
        ):
            errors.append(f"[{context}] {source!r}: translation is unfinished or empty")
            continue

        forms = translation.findall("numerusform")
        translated_forms = [_text(form) for form in forms] if forms else [_text(translation)]
        for index, translated in enumerate(translated_forms):
            if _signature(source) != _signature(translated):
                errors.append(
                    f"[{context}] form {index}: {source!r} -> {translated!r}: "
                    f"{_signature(source)!r} != {_signature(translated)!r}"
                )
            if (
                (context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
                and _mnemonic_count(translated) < _mnemonic_count(source)
            ):
                errors.append(
                    f"[{context}] form {index}: {source!r} -> {translated!r}: "
                    "missing a source mnemonic"
                )

    assert not errors, (
        f"{len(errors)} Portuguese translations change placeholders, HTML, or line breaks:\n"
        + "\n".join(errors[:30])
    )

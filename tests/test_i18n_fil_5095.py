"""#5095: the Filipino catalog is complete and keeps formatting tokens."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_I18N_DIR = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_FIL = _I18N_DIR / "picasapy_fil.ts"
_EN = _I18N_DIR / "picasapy_en.ts"

_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[diuoxXfFeEgGcrs])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")
_EXISTING_MNEMONIC_EXCEPTIONS = {
    ("FolderContextMenu", "&Color"),
    ("FolderContextMenu", "Mo&ve to Collection"),
}


def _text(node: ET.Element | None) -> str:
    return "".join(node.itertext()) if node is not None else ""


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (context.findtext("name", ""), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    filipino = _messages(_FIL)
    english = _messages(_EN)
    fil_keys = [(context, _text(message.find("source"))) for context, message in filipino]
    en_keys = [(context, _text(message.find("source"))) for context, message in english]
    assert fil_keys == en_keys, "the Filipino and English TS keys or ordering differ"
    return [
        (fil_context, fil_message, en_message)
        for (fil_context, fil_message), (_, en_message) in zip(
            filipino, english, strict=True
        )
    ]


def _signature(value: str) -> tuple[Counter[str], tuple[str, ...], int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        tuple(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    return len(_MNEMONIC.findall(value.replace("B&W", "BW")))


def test_filipino_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"[{context}] {_text(message.find('source'))!r}"
        for context, message, _ in _aligned_messages()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
        or not _text(translation).strip()
    ]

    assert not unfinished, (
        f"{len(unfinished)} Filipino messages remain unfinished:\n"
        + "\n".join(unfinished[:30])
    )


def test_filipino_translations_preserve_source_signatures() -> None:
    errors: list[str] = []
    for context, message, english_message in _aligned_messages():
        source = _text(english_message.find("source"))
        translation = message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            errors.append(f"[{context}] {source!r}: translation is unfinished")
            continue

        forms = translation.findall("numerusform")
        translated_forms = [_text(form) for form in forms] or [_text(translation)]
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
        f"{len(errors)} Filipino translations change placeholders, HTML, "
        "line breaks, or shortcuts:\n" + "\n".join(errors[:30])
    )

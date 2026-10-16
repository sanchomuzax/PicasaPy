"""#5039: the Simplified Chinese catalog is complete and preserves tokens."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_ZH_CN = _I18N / "picasapy_zh-CN.ts"
_EN = _I18N / "picasapy_en.ts"
_PLACEHOLDER = re.compile(r"%L?\d+|%n|%[diouxXeEfFgGaAcsp]|\{\d+\}")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&|\s)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    zh_root = ET.parse(_ZH_CN).getroot()
    en_root = ET.parse(_EN).getroot()
    zh_messages = [
        (context.findtext("name", ""), message)
        for context in zh_root.findall("context")
        for message in context.findall("message")
    ]
    en_messages = [
        (context.findtext("name", ""), message)
        for context in en_root.findall("context")
        for message in context.findall("message")
    ]
    assert len(zh_messages) == len(en_messages)

    aligned = []
    for (zh_context, zh_message), (en_context, en_message) in zip(
        zh_messages, en_messages, strict=True
    ):
        assert zh_context == en_context
        assert _text(zh_message.find("source")) == _text(en_message.find("source"))
        aligned.append((zh_context, zh_message, en_message))
    return aligned


def _signature(value: str) -> tuple[Counter[str], Counter[str], int, int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
        len(_MNEMONIC.findall(value)),
    )


def test_simplified_chinese_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"[{context}] {_text(zh_message.find('source'))!r}"
        for context, zh_message, _ in _aligned_messages()
        if (translation := zh_message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished Simplified Chinese messages remain:\n"
        + "\n".join(unfinished[:20])
    )


def test_simplified_chinese_translations_preserve_source_signatures() -> None:
    mismatches = []
    for context, zh_message, en_message in _aligned_messages():
        source = _text(en_message.find("source"))
        translation = zh_message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            mismatches.append((context, source, "<unfinished translation>"))
            continue
        origin = _text(zh_message.find("extracomment"))
        expected = _signature(source)
        forms = translation.findall("numerusform") or [translation]
        # Existing Picasa entries sometimes add Chinese keyboard mnemonics
        # even when the English source has none; keep their tokens, markup,
        # and line breaks checked without changing those established labels.
        compared = 4 if "picasapy-origin: picasapy" in origin else 3
        for index, form in enumerate(forms):
            actual = _signature(_text(form))
            if actual[:compared] != expected[:compared]:
                mismatches.append(
                    (context, source, f"form {index}: {_text(form)}", expected, actual)
                )

    assert not mismatches, (
        f"{len(mismatches)} placeholder/markup/mnemonic signature mismatches:\n"
        + "\n".join(repr(item) for item in mismatches[:20])
    )

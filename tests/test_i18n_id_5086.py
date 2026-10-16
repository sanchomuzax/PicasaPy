"""Az indonéz katalógus teljességét és helyőrző-aláírását őrzi (#5086)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_INDONESIAN = _I18N / "picasapy_id.ts"
_ENGLISH = _I18N / "picasapy_en.ts"
_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[-+0-9.*]*[diouxXeEfFgGaAcsp])"
    r"|\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?\s*[A-Za-z][\w:-]*(?:\s+[^<>]*?)?/?\s*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _catalog(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (_text(context.find("name")), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return []
    forms = translation.findall("numerusform")
    return [_text(form) for form in forms] if forms else [_text(translation)]


def _signature(value: str) -> tuple[Counter[str], Counter[str], int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    indonesian = _catalog(_INDONESIAN)
    english = _catalog(_ENGLISH)
    assert len(indonesian) == len(english), (
        "az indonéz és az angol katalógus üzenetszáma eltér"
    )

    aligned = []
    for (id_context, id_message), (en_context, en_message) in zip(
        indonesian, english, strict=True
    ):
        assert id_context == en_context
        assert _text(id_message.find("source")) == _text(en_message.find("source"))
        aligned.append((id_context, id_message, en_message))
    return aligned


def test_indonez_katalogusban_nincs_unfinished_forditas() -> None:
    unfinished = [
        f"[{context}] {_text(english_message.find('source'))!r}"
        for context, message, english_message in _aligned_messages()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
        or any(not form.strip() for form in _forms(message))
    ]

    assert not unfinished, (
        f"{len(unfinished)} indonéz fordítás hiányzik vagy unfinished; "
        f"első példák: {unfinished[:12]!r}"
    )


def test_indonez_forditasok_megorizik_a_helyorzo_alairast() -> None:
    mismatches = []
    for context, message, english_message in _aligned_messages():
        source = _text(english_message.find("source"))
        expected = _signature(source)
        for index, translated in enumerate(_forms(message)):
            if _signature(translated) != expected:
                mismatches.append(
                    f"[{context}] alak {index}: {source!r}: "
                    f"{expected!r} != {_signature(translated)!r}"
                )
                break

    assert not mismatches, "Hibás indonéz helyőrző/HTML/sortörés-aláírás:\n" + "\n".join(
        mismatches[:20]
    )


def test_indonez_sajat_feliratok_megorizik_a_gyorsbillentyuket() -> None:
    mismatches = []
    for context, message, english_message in _aligned_messages():
        extra = _text(message.find("extracomment"))
        if "picasapy-origin: picasapy" not in extra:
            continue
        source = _text(english_message.find("source"))
        expected = _mnemonic_count(source)
        if expected == 0:
            continue
        for index, translated in enumerate(_forms(message)):
            if _mnemonic_count(translated) != expected:
                mismatches.append(
                    f"[{context}] alak {index}: {source!r}: "
                    f"{expected} gyorsbillentyű, de {_mnemonic_count(translated)} van"
                )
                break

    assert not mismatches, "Hibás indonéz gyorsbillentyűk:\n" + "\n".join(
        mismatches[:20]
    )

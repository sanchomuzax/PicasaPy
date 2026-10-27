"""A hagyományos kínai katalógus teljessége és formázási jelölői (#5044)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_I18N = Path(__file__).resolve().parents[1] / "src" / "picasapy" / "app" / "i18n"
_TRADITIONAL = _I18N / "picasapy_zh-TW.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[diu])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")

# Ezek a kész, Picasa-eredetű sorok már a #5044 előtti katalógusban is
# elvesztették a forrásban jelölt gyorsbillentyűt; a kész fordításokhoz nem
# nyúlunk.
_EXISTING_MNEMONIC_EXCEPTIONS = {
    ("PicasaFolderViewMenu", "Re&verse sort"),
    ("FolderContextMenu", "&Color"),
    ("FolderListContextMenu", "Re&verse sort"),
}


def _aligned_messages() -> list[tuple[str, ET.Element, str]]:
    def collect(path: Path) -> list[tuple[str, ET.Element]]:
        root = ET.parse(path).getroot()
        return [
            (context.findtext("name", ""), message)
            for context in root.findall("context")
            for message in context.findall("message")
        ]

    traditional = collect(_TRADITIONAL)
    english = collect(_ENGLISH)
    assert len(traditional) == len(english)

    aligned = []
    for (tw_context, tw_message), (en_context, en_message) in zip(
        traditional, english, strict=True
    ):
        assert tw_context == en_context
        source = en_message.findtext("source", "")
        assert tw_message.findtext("source", "") == source
        aligned.append((tw_context, tw_message, source))
    return aligned


def _translation_forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return [""]
    forms = translation.findall("numerusform")
    if forms:
        return ["".join(form.itertext()) for form in forms]
    return ["".join(translation.itertext())]


def _mnemonic_count(value: str) -> int:
    # A B&W rövidítésben az ampersand az „and” része, nem gyorsbillentyű.
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def test_a_hagyomanyos_kinai_katalogusban_nincs_unfinished_uzenet() -> None:
    unfinished = [
        f"{context}: {source}"
        for context, message, source in _aligned_messages()
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished hagyományos kínai fordítás maradt; "
        f"első példák: {unfinished[:10]!r}"
    )


def test_a_hagyomanyos_kinai_forditasok_megtartjak_a_formazasi_alairast() -> None:
    errors = []
    for context, message, source in _aligned_messages():
        for translated in _translation_forms(message):
            if (
                Counter(_PLACEHOLDER.findall(source))
                != Counter(_PLACEHOLDER.findall(translated))
                or _HTML_TAG.findall(source) != _HTML_TAG.findall(translated)
                or source.count("\n") != translated.count("\n")
            ):
                errors.append(f"[{context}] {source!r}: {translated!r}")
                break

            if (
                (context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
                and _mnemonic_count(translated) < _mnemonic_count(source)
            ):
                errors.append(f"[{context}] hiányzó gyorsbillentyű: {source!r}")
                break

    assert not errors, (
        f"{len(errors)} hagyományos kínai fordítás formázási aláírása hibás; "
        f"első példák: {errors[:10]!r}"
    )

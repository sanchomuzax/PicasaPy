"""#5020: a német katalógus teljessége és formázási jelölői."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_I18N = _ROOT / "src" / "picasapy" / "app" / "i18n"
_GERMAN = _I18N / "picasapy_de.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_QT_PLACEHOLDER = re.compile(r"%(?:L[1-9]\d*|L?n|[1-9]\d*|d)")
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")

# Ezek a már kitöltött, hivatalos Picasa-sorok a #5020 előtt is elvesztették
# a gyorsbillentyű-jelölőt. A meglévő fordítások érintetlenül hagyása miatt
# csak ezeknél nem követeljük meg a forrásszöveg jelölőjét.
_EXISTING_MNEMONIC_EXCEPTIONS = {
    ("PicasaEditMenu", "&Paste"),
    ("FolderContextMenu", "&Color"),
}


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
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
    # A B&W rövidítésben az ampersand az „and” része, nem menügyorsbillentyű.
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def _translations(translation: ET.Element) -> list[str]:
    forms = translation.findall("numerusform")
    if forms:
        return ["".join(form.itertext()) for form in forms]
    return [translation.text or ""]


def test_a_nemet_katalogusban_nincs_unfinished_uzenet():
    unfinished = [
        (context, message.findtext("source") or "")
        for context, message in _messages(_GERMAN)
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} német üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:10]!r}"
    )


def test_a_nemet_kulcsok_es_a_formazasi_jelolok_megegyeznek():
    german = _messages(_GERMAN)
    english = _messages(_ENGLISH)
    german_keys = Counter(
        (context, message.findtext("source") or "")
        for context, message in german
    )
    english_keys = Counter(
        (context, message.findtext("source") or "")
        for context, message in english
    )
    assert german_keys == english_keys, "a német és angol TS kulcsai eltérnek"

    errors: list[str] = []
    for context, message in german:
        source = message.findtext("source") or ""
        translation = message.find("translation")
        translated_values = _translations(translation) if translation is not None else [""]
        for translated in translated_values:
            if _format_signature(source) != _format_signature(translated):
                errors.append(
                    f"[{context}] {source!r}: eltérő helyőrző/HTML/sortörés "
                    f"({translated!r})"
                )
                break

            source_mnemonics = _mnemonic_count(source)
            translated_mnemonics = _mnemonic_count(translated)
            if (
                (context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
                and translated_mnemonics < source_mnemonics
            ):
                errors.append(
                    f"[{context}] {source!r}: hiányzó gyorsbillentyű-jelölő "
                    f"({translated!r})"
                )
                break

    assert not errors, (
        f"{len(errors)} német fordítás formázási aláírása hibás; "
        f"első példák: {errors[:10]!r}"
    )

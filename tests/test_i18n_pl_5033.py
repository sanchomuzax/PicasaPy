"""#5033: a lengyel katalógus teljessége és formázási jelölői."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "src/picasapy/app/i18n/picasapy_pl.ts"
ENGLISH = ROOT / "src/picasapy/app/i18n/picasapy_en.ts"

_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[sd])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][\w:-]*\b[^>]*?/?>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")

# Régi, már lefordított Picasa-menüsor; a meglévő fordítást nem írjuk át.
_EXISTING_MNEMONIC_EXCEPTIONS = {("FolderContextMenu", "&Color")}


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (_text(context.find("name")), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _translation_forms(message: ET.Element) -> list[str]:
    translation = message.find("translation")
    if translation is None:
        return []
    forms = translation.findall("numerusform")
    return [_text(form) for form in forms] if forms else [_text(translation)]


def _format_signature(value: str) -> tuple[Counter[str], tuple[str, ...], int]:
    return (
        Counter(_PLACEHOLDER.findall(value)),
        tuple(_HTML_TAG.findall(value)),
        value.count("\n"),
    )


def _mnemonic_count(value: str) -> int:
    # W nazwie skrótu B&W ampersand jest tekstem, nie znacznikiem menu.
    normalized = re.sub(r"\bB&W\b", "BW", value, flags=re.IGNORECASE)
    return len(_MNEMONIC.findall(normalized))


def test_lengyel_katalogusban_nincs_forditatlan_uzenet():
    unfinished = [
        f"{context}: {_text(message.find('source'))}"
        for context, message in _messages(POLISH)
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} lengyel üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:10]!r}"
    )


def test_lengyel_tobbesszam_mindharom_alakja_ki_van_toltve():
    incomplete = []
    for context, message in _messages(POLISH):
        if message.get("numerus") != "yes":
            continue
        forms = _translation_forms(message)
        if len(forms) != 3 or any(not form.strip() for form in forms):
            incomplete.append(
                f"{context}: {_text(message.find('source'))} ({len(forms)} alak)"
            )

    assert not incomplete, (
        f"{len(incomplete)} lengyel többes üzenet alakjai hiányosak; "
        f"első példák: {incomplete[:10]!r}"
    )


def test_lengyel_forditasok_megorzik_a_helyorzo_es_html_alairast():
    polish = _messages(POLISH)
    english = _messages(ENGLISH)
    polish_keys = Counter(
        (context, _text(message.find("source"))) for context, message in polish
    )
    english_keys = Counter(
        (context, _text(message.find("source"))) for context, message in english
    )
    assert polish_keys == english_keys, "a lengyel és angol TS kulcsai eltérnek"

    mismatches = []
    for context, message in polish:
        source = _text(message.find("source"))
        source_signature = _format_signature(source)
        for translated in _translation_forms(message):
            if source_signature != _format_signature(translated):
                mismatches.append(f"{context}: {source!r} → {translated!r}")
                break
            if (
                (context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
                and _mnemonic_count(translated) < _mnemonic_count(source)
            ):
                mismatches.append(f"{context}: {source!r}: hiányzó gyorsbillentyű-jelölő")
                break

    assert not mismatches, (
        f"{len(mismatches)} lengyel üzenet helyőrző/HTML aláírása hibás; "
        f"első példák: {mismatches[:10]!r}"
    )

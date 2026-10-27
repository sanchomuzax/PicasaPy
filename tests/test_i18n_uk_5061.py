"""A ukrán katalógus teljességi, többes- és formázási őre (#5061)."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_UK = _I18N / "picasapy_uk.ts"
_EN = _I18N / "picasapy_en.ts"
_PLACEHOLDER = re.compile(
    r"%(?:\d+\$[diuoxXfFeEgGaAcsp]|L?\d+|n|[diuoxXfFeEgGaAcsp])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][\w:-]*\b[^>]*?/?>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")
_LITERAL_AMPERSANDS = re.compile(r"\bB&W\b", re.IGNORECASE)
_EXISTING_MNEMONIC_EXCEPTIONS = {
    ("PicasaFolderViewMenu", "Re&verse sort"),
    ("PicasaFolderMenu", "&Reverse order"),
    ("AlbumContextMenu", "&Reverse order"),
    ("FolderContextMenu", "&Color"),
    ("FolderContextMenu", "&Reverse order"),
    ("FolderListContextMenu", "Re&verse sort"),
}


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


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
    normalized = _LITERAL_AMPERSANDS.sub("BW", value)
    return len(_MNEMONIC.findall(normalized))


def _aligned_catalogs() -> list[tuple[str, ET.Element, ET.Element]]:
    ukrainian = _catalog(_UK)
    english = _catalog(_EN)
    assert len(ukrainian) == len(english), "az ukrán és angol katalógus elemszáma eltér"

    aligned = []
    for (uk_context, uk_message), (en_context, en_message) in zip(
        ukrainian, english, strict=True
    ):
        assert uk_context == en_context
        assert _text(uk_message.find("source")) == _text(en_message.find("source"))
        aligned.append((uk_context, uk_message, en_message))
    return aligned


def test_ukran_katalogusban_nincs_unfinished_uzenet() -> None:
    unfinished = [
        f"{context}: {_text(message.find('source'))}"
        for context, message, _ in _aligned_catalogs()
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} ukrán üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:12]!r}"
    )


def test_ukran_tobbesszam_mindharom_alakja_ki_van_toltve() -> None:
    incomplete = []
    for context, message, _ in _aligned_catalogs():
        if message.get("numerus") != "yes":
            continue
        forms = _forms(message)
        if len(forms) != 3 or any(not form.strip() for form in forms):
            incomplete.append(f"{context}: {_text(message.find('source'))} ({len(forms)} alak)")

    assert not incomplete, (
        f"{len(incomplete)} ukrán többes üzenet alakjai hiányosak; "
        f"első példák: {incomplete[:12]!r}"
    )


def test_ukran_forditasok_megorzik_a_formazasi_alairast() -> None:
    mismatches = []
    for context, message, english_message in _aligned_catalogs():
        source = _text(english_message.find("source"))
        expected = _signature(source)
        for translated in _forms(message):
            mnemonic_missing = (
                (context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
                and _mnemonic_count(translated) < _mnemonic_count(source)
            )
            if _signature(translated) != expected or mnemonic_missing:
                mismatches.append(f"{context}: {source!r} → {translated!r}")
                break

    assert not mismatches, (
        f"{len(mismatches)} ukrán üzenet helyőrző/HTML/sortörés/gyorsbillentyű-jelölése hibás; "
        f"első példák: {mismatches[:12]!r}"
    )

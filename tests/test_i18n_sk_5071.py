"""A szlovák katalógus teljességét és helyőrzőit őrzi (#5071)."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_PLACEHOLDER = re.compile(
    r"%(?:\d+\$[diuoxXfFeEgGaAcsp]|L?\d+|n|[diuoxXfFeEgGaAcsp])|"
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?[A-Za-z][\w:-]*\b[^>]*?/?>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")
_LITERAL_AMPERSANDS = re.compile(r"\bB&W\b", re.IGNORECASE)
_EXISTING_MNEMONIC_EXCEPTIONS = {("FolderContextMenu", "&Color")}


def _text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _catalog(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (_text(context.find("name")), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _aligned_catalogs() -> list[tuple[str, ET.Element, ET.Element]]:
    slovak = _catalog(_I18N / "picasapy_sk.ts")
    english = _catalog(_I18N / "picasapy_en.ts")
    assert len(slovak) == len(english), "a szlovák és angol katalógus elemszáma eltér"

    aligned = []
    for (sk_context, sk_message), (en_context, en_message) in zip(
        slovak, english, strict=True
    ):
        assert sk_context == en_context
        assert _text(sk_message.find("source")) == _text(en_message.find("source"))
        aligned.append((sk_context, sk_message, en_message))
    return aligned


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


def test_slovak_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"{context}: {_text(message.find('source'))}"
        for context, message, _ in _aligned_catalogs()
        if (translation := message.find("translation")) is None
        or translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} szlovák üzenet maradt unfinished állapotban; "
        f"első példák: {unfinished[:12]!r}"
    )


def test_slovak_translations_preserve_placeholders_and_all_plural_forms() -> None:
    mismatches = []
    for context, message, english_message in _aligned_catalogs():
        source = _text(english_message.find("source"))
        forms = _forms(message)
        if not forms or any(not form.strip() for form in forms):
            mismatches.append(f"[{context}] {source!r}: üres fordítási alak")
            continue

        if message.get("numerus") == "yes" and len(forms) != 3:
            mismatches.append(f"[{context}] {source!r}: {len(forms)} többes alak (3 kell)")
            continue

        expected = _signature(source)
        source_mnemonics = _mnemonic_count(source)
        check_mnemonics = (context, source) not in _EXISTING_MNEMONIC_EXCEPTIONS
        for form in forms:
            if _signature(form) != expected or (
                check_mnemonics and _mnemonic_count(form) < source_mnemonics
            ):
                mismatches.append(f"[{context}] {source!r} → {form!r}")
                break

    assert not mismatches, (
        f"{len(mismatches)} szlovák fordítás helyőrző/HTML/sortörés/gyorsbillentyű-"
        f"aláírása hibás; első példák: {mismatches[:12]!r}"
    )

"""#5035: az orosz katalógus legyen teljes és őrizze a formázást."""

from collections import Counter
from pathlib import Path
import re
import xml.etree.ElementTree as ET


I18N_DIR = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
PLACEHOLDER_RE = re.compile(r"%L?\d+|%n|%[diu]|\{(?:\d+|[A-Za-z_]\w*)\}")


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
    numerus_forms = translation.findall("numerusform")
    return [_text(form) for form in numerus_forms] or [_text(translation)]


def _placeholder_signature(value: str) -> Counter[str]:
    return Counter(PLACEHOLDER_RE.findall(value))


def _aligned_catalogs() -> list[tuple[str, ET.Element, ET.Element]]:
    russian = _catalog(I18N_DIR / "picasapy_ru.ts")
    english = _catalog(I18N_DIR / "picasapy_en.ts")
    assert len(russian) == len(english)

    aligned = []
    for (ru_context, ru_message), (en_context, en_message) in zip(
        russian, english, strict=True
    ):
        assert ru_context == en_context
        assert _text(ru_message.find("source")) == _text(en_message.find("source"))
        aligned.append((ru_context, ru_message, en_message))
    return aligned


def test_russian_catalog_has_no_unfinished_messages() -> None:
    unfinished = [
        f"{context}: {_text(message.find('source'))}"
        for context, message, _ in _aligned_catalogs()
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished Russian translations remain; "
        f"first entries: {unfinished[:10]}"
    )


def test_russian_translations_keep_source_placeholder_signatures() -> None:
    missing = []
    mismatches = []
    for context, russian_message, english_message in _aligned_catalogs():
        source = _text(english_message.find("source"))
        forms = _forms(russian_message)
        if not forms or any(not form.strip() for form in forms):
            missing.append(f"{context}: {source}")
            continue

        expected = _placeholder_signature(source)
        for form in forms:
            actual = _placeholder_signature(form)
            if actual != expected:
                mismatches.append((context, source, form, expected, actual))
        if russian_message.get("numerus") == "yes" and len(forms) != 3:
            mismatches.append((context, source, forms, "3 Russian plural forms", len(forms)))

    assert not missing, f"{len(missing)} Russian translations are empty; first: {missing[:10]}"
    assert not mismatches, f"Russian placeholder signatures differ: {mismatches[:10]}"

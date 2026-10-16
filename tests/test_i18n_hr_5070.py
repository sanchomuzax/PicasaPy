"""A horvát katalógus teljességét és formázási aláírásait őrzi (#5070)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_I18N = Path(__file__).resolve().parents[1] / "src/picasapy/app/i18n"
_CROATIAN = _I18N / "picasapy_hr.ts"
_ENGLISH = _I18N / "picasapy_en.ts"

_PLACEHOLDER = re.compile(
    r"%(?:L[1-9]\d*|L?n|[1-9]\d*|[-+0-9.*]*[diouxXeEfFgGaAcsp])"
)
_BRACE_PLACEHOLDER = re.compile(
    r"\{(?:\d+|[A-Za-z_]\w*)(?:![rsa])?(?::[^{}]*)?\}"
)
_HTML_TAG = re.compile(r"</?\s*[A-Za-z][\w:-]*(?:\s+[^<>]*?)?/?\s*>")
_MNEMONIC = re.compile(r"(?<!&)&(?!&)(?=\S)")


def _text(node: ET.Element | None) -> str:
    return "" if node is None else "".join(node.itertext())


def _content(node: ET.Element | None) -> str:
    if node is None:
        return ""
    parts = [node.text or ""]
    for child in node:
        parts.append(ET.tostring(child, encoding="unicode"))
        parts.append(child.tail or "")
    return "".join(parts)


def _messages(path: Path) -> list[tuple[str, ET.Element]]:
    root = ET.parse(path).getroot()
    return [
        (_text(context.find("name")), message)
        for context in root.findall("context")
        for message in context.findall("message")
    ]


def _aligned_messages() -> list[tuple[str, ET.Element, ET.Element]]:
    croatian = _messages(_CROATIAN)
    english = _messages(_ENGLISH)
    assert len(croatian) == len(english), "a horvát és az angol katalógus üzenetszáma eltér"

    aligned: list[tuple[str, ET.Element, ET.Element]] = []
    for (hr_context, hr_message), (en_context, en_message) in zip(
        croatian, english, strict=True
    ):
        assert hr_context == en_context
        assert _text(hr_message.find("source")) == _text(en_message.find("source"))
        aligned.append((hr_context, hr_message, en_message))
    return aligned


def _signature(value: str) -> tuple[Counter[str], Counter[str], tuple[str, ...], int]:
    html_tags = [
        re.sub(r"\s*/\s*>", ">", re.sub(r"\s+", " ", tag.strip()))
        for tag in _HTML_TAG.findall(value)
    ]
    return (
        Counter(_PLACEHOLDER.findall(value)),
        Counter(_BRACE_PLACEHOLDER.findall(value)),
        tuple(html_tags),
        value.count("\n"),
    )


def test_croatian_catalog_has_no_unfinished_translations() -> None:
    unfinished: list[str] = []
    for context, message, english_message in _aligned_messages():
        translation = message.find("translation")
        forms = translation.findall("numerusform") if translation is not None else []
        translated_forms = forms or ([translation] if translation is not None else [])
        if (
            translation is None
            or translation.get("type") == "unfinished"
            or any(not _content(form).strip() for form in translated_forms)
        ):
            unfinished.append(f"[{context}] {_text(english_message.find('source'))!r}")

    assert not unfinished, (
        f"{len(unfinished)} horvát fordítás maradt unfinished állapotban; "
        f"első példák: {unfinished[:12]!r}"
    )


def test_croatian_translations_preserve_source_signatures() -> None:
    mismatches: list[str] = []
    for context, message, english_message in _aligned_messages():
        source = _content(english_message.find("source"))
        extra = _text(message.find("extracomment"))
        translation = message.find("translation")
        if translation is None or translation.get("type") == "unfinished":
            continue

        forms = translation.findall("numerusform") or [translation]
        for index, form in enumerate(forms):
            translated = _content(form)
            source_mnemonics = len(
                _MNEMONIC.findall(re.sub(r"\bB&W\b", "BW", source, flags=re.IGNORECASE))
            )
            translated_mnemonics = len(
                _MNEMONIC.findall(
                    re.sub(r"\bB&W\b", "BW", translated, flags=re.IGNORECASE)
                )
            )
            # A Picasa-origin Croatian translation may legitimately place its
            # mnemonic differently from the English source. For PicasaPy-owned
            # strings, keep every source mnemonic exactly.
            keep_mnemonics = "picasapy-origin: picasapy" in extra
            if _signature(source) != _signature(translated) or (
                keep_mnemonics and source_mnemonics != translated_mnemonics
            ):
                mismatches.append(
                    f"[{context}] alak {index}: {source!r} -> {translated!r}: "
                    f"{_signature(source)!r} != {_signature(translated)!r}; "
                    f"gyorsbillentyűk {source_mnemonics} != {translated_mnemonics}"
                )
                break

    assert not mismatches, "Eltérő horvát formázási aláírások:\n" + "\n".join(
        mismatches[:20]
    )


def test_croatian_numerus_messages_have_three_nonempty_forms() -> None:
    incomplete: list[str] = []
    for context, message, english_message in _aligned_messages():
        if message.get("numerus") != "yes":
            continue
        translation = message.find("translation")
        forms = translation.findall("numerusform") if translation is not None else []
        if len(forms) != 3 or any(not _text(form).strip() for form in forms):
            incomplete.append(f"[{context}] {_text(english_message.find('source'))!r}")

    assert not incomplete, (
        "A horvát többes szám mindhárom alakja nincs kitöltve ezeknél: "
        f"{incomplete[:20]!r}"
    )

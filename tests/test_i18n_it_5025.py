"""#5025: az olasz katalógus teljes, a formázási jelölők változatlanok."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_TS_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "picasapy"
    / "app"
    / "i18n"
    / "picasapy_it.ts"
)

_QT_PLACEHOLDER = re.compile(r"%(?:L?\d+|n|[diuoxXfFeEgGaAcsp])")
_BRACE_PLACEHOLDER = re.compile(r"\{[^{}\r\n]+\}")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*?/?>")


def _plain_text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext())


def _signature(text: str) -> tuple[Counter[str], Counter[str], tuple[str, ...], int]:
    """Qt/Python helyőrzők, HTML-sorrend és sortörések."""
    return (
        Counter(_QT_PLACEHOLDER.findall(text)),
        Counter(_BRACE_PLACEHOLDER.findall(text)),
        tuple(_HTML_TAG.findall(text)),
        len(re.findall(r"\r\n|\r|\n", text)),
    )


def _translation_forms(translation: ET.Element) -> list[str]:
    forms = translation.findall("numerusform")
    if forms:
        return [_plain_text(form) for form in forms]
    return [_plain_text(translation)]


def test_olasz_katalogusban_nincs_befejezetlen_uzenet() -> None:
    root = ET.parse(_TS_PATH).getroot()
    unfinished: list[str] = []
    for context in root.findall("context"):
        name = _plain_text(context.find("name"))
        for message in context.findall("message"):
            translation = message.find("translation")
            if translation is not None and translation.get("type") == "unfinished":
                unfinished.append(
                    f"[{name}] {_plain_text(message.find('source'))!r}"
                )

    assert not unfinished, (
        f"{len(unfinished)} olasz üzenet unfinished; első példák:\n"
        + "\n".join(unfinished[:20])
    )


def test_olasz_forditasok_megorizik_a_helyorzo_alairast() -> None:
    root = ET.parse(_TS_PATH).getroot()
    mismatches: list[str] = []
    for context in root.findall("context"):
        name = _plain_text(context.find("name"))
        for message in context.findall("message"):
            translation = message.find("translation")
            if translation is None or translation.get("type") in {
                "unfinished",
                "obsolete",
                "vanished",
            }:
                continue

            source = _plain_text(message.find("source"))
            expected = _signature(source)
            for form in _translation_forms(translation):
                if _signature(form) != expected:
                    mismatches.append(
                        f"[{name}] {source!r} -> {form!r}: "
                        f"forrás={expected!r}, fordítás={_signature(form)!r}"
                    )
                    break

    assert not mismatches, (
        f"{len(mismatches)} olasz fordításban megváltozott a helyőrző-/"
        "HTML-/sortörés-aláírás; első példák:\n" + "\n".join(mismatches[:20])
    )

"""Arabic catalog completeness and placeholder contract for #5097."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


_CATALOG = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "picasapy"
    / "app"
    / "i18n"
    / "picasapy_ar.ts"
)
_PLACEHOLDER = re.compile(
    r"%(?:L?\d+|n|[diuoxXfFeEgGcs])|\{[A-Za-z0-9_]+\}"
)


def _content_signature(element: ET.Element) -> tuple[object, ...]:
    text = "".join(element.itertext())
    html_tags = Counter(
        (child.tag, tuple(sorted(child.attrib.items())))
        for child in element.iter()
        if child is not element
    )
    return (
        Counter(_PLACEHOLDER.findall(text)),
        text.count("\n"),
        html_tags,
    )


def test_arabic_catalog_has_no_unfinished_messages_and_preserves_signatures():
    root = ET.parse(_CATALOG).getroot()
    unfinished: list[str] = []
    placeholder_mismatches: list[str] = []
    plural_shape_errors: list[str] = []

    for context in root.findall("context"):
        context_name = context.findtext("name", "")
        for message in context.findall("message"):
            translation = message.find("translation")
            if translation is None or translation.get("type") == "unfinished":
                unfinished.append(
                    f"[{context_name}] {message.findtext('source', '')!r}"
                )
                continue
            if translation.get("type") in {"vanished", "obsolete"}:
                continue

            source = message.find("source")
            assert source is not None
            if message.get("numerus") == "yes":
                forms = translation.findall("numerusform")
                if len(forms) != 6 or any(not "".join(form.itertext()).strip() for form in forms):
                    plural_shape_errors.append(
                        f"[{context_name}] {message.findtext('source', '')!r}: "
                        f"{len(forms)} arabic forms"
                    )
                candidates = forms
            else:
                candidates = [translation]

            for index, candidate in enumerate(candidates, start=1):
                if _content_signature(source) != _content_signature(candidate):
                    placeholder_mismatches.append(
                        f"[{context_name}] {message.findtext('source', '')!r} "
                        f"(translation form {index})"
                    )

    assert not unfinished, (
        f"{len(unfinished)} unfinished arabic translations remain:\n"
        + "\n".join(unfinished)
    )
    assert not plural_shape_errors, (
        "Arabic plural messages must provide six nonempty forms:\n"
        + "\n".join(plural_shape_errors)
    )
    assert not placeholder_mismatches, (
        "Placeholder, shortcut, line-break, or HTML signatures differ:\n"
        + "\n".join(placeholder_mismatches)
    )

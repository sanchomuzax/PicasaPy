"""A lett fordítás teljessége és a Qt-helyőrzők megőrzése."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


TS_PATH = (
    Path(__file__).parents[1]
    / "src/picasapy/app/i18n/picasapy_lv.ts"
)
PLACEHOLDER = re.compile(r"%%|%(?:L?\d+|n|[A-Za-z])|\{\w+\}")
HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
LEGACY_ACCELERATOR_EXCEPTIONS = {
    ("EditorPanel", "Focal B&W"),
    ("EditorPanel", "Filtered B&W"),
    ("PublishPanel", "Choose folders & albums to back up"),
    ("PhotoViewer", "Filtered B&W"),
    ("PicasaMenuBar", "Re&verse sort"),
    ("EditorEffectsTab1", "Focal B&W"),
    ("EditorEffectsTab1", "Filtered B&W"),
    (
        "EditorEffectsTab1",
        "Makes a photo that looks like it was taken with B&W film and a color filter",
    ),
    ("LegacyEffects", "Shadow & Highlight"),
    ("FolderContextMenu", "&Color"),
    ("FolderListContextMenu", "Re&verse sort"),
}


def _signature(text: str) -> Counter[str]:
    return Counter(PLACEHOLDER.findall(text))


def test_latvian_translation_has_no_unfinished_messages() -> None:
    root = ET.parse(TS_PATH).getroot()
    unfinished = [
        message
        for message in root.findall(".//message")
        if (translation := message.find("translation")) is not None
        and translation.get("type") == "unfinished"
    ]

    assert not unfinished, (
        f"{len(unfinished)} unfinished lett üzenet maradt; első források: "
        f"{[message.findtext('source') for message in unfinished[:5]]}"
    )


def test_latvian_translation_preserves_placeholders_and_plural_forms() -> None:
    root = ET.parse(TS_PATH).getroot()
    failures = []

    for message in root.findall(".//message"):
        source = message.findtext("source") or ""
        translation = message.find("translation")
        assert translation is not None

        translated_forms = (
            [form.text or "" for form in translation.findall("numerusform")]
            if message.get("numerus") == "yes"
            else ["".join(translation.itertext())]
        )

        if message.get("numerus") == "yes" and len(translated_forms) != 3:
            failures.append((source, f"{len(translated_forms)} többes alak"))

        for translated in translated_forms:
            if _signature(source) != _signature(translated):
                failures.append(
                    (
                        source,
                        f"helyőrzők: {_signature(source)} != "
                        f"{_signature(translated)}",
                    )
                )
            if Counter(HTML_TAG.findall(source)) != Counter(
                HTML_TAG.findall(translated)
            ):
                failures.append((source, "a HTML-jelölők eltérnek"))
            if source.count("\n") != translated.count("\n"):
                failures.append((source, "a sortörések száma eltér"))

    assert not failures, (
        "Hibás lett fordítások (első 10): "
        f"{failures[:10]}"
    )


def test_latvian_translation_preserves_source_accelerators() -> None:
    root = ET.parse(TS_PATH).getroot()
    failures = []

    for context in root.findall("context"):
        context_name = context.findtext("name") or ""
        for message in context.findall("message"):
            source = message.findtext("source") or ""
            translation = message.find("translation")
            assert translation is not None
            forms = (
                [form.text or "" for form in translation.findall("numerusform")]
                if message.get("numerus") == "yes"
                else ["".join(translation.itertext())]
            )

            if (context_name, source) in LEGACY_ACCELERATOR_EXCEPTIONS:
                continue
            for translated in forms:
                if source.count("&") > translated.count("&"):
                    failures.append((context_name, source, translated))

    assert not failures, (
        "Eltűnt gyorsbillentyű-jelölők (első 10): "
        f"{failures[:10]}"
    )

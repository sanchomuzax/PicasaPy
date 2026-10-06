#!/usr/bin/env python3
"""A #4313 nyelvi TS-szótárak előállítása a helyi, csak olvasható referenciából.

Példa:

    python3 scripts/build_i18n_dictionaries.py \
        --references /home/sancho/picasapy-agent/referencia/i18n

A pár kulcsa a #2971 kinyerője szerinti `panel:azonosító`. Az első lépésben a
saját magyar fordítás normalizált alakja az eredeti magyar szöveghez kapcsolódik
(NFC, `&` és záró írásjel elhagyása, kisbetűsítés). A célnyelvi érték csak akkor
kerül be, ha az összes azonos magyar jelöltkulcs megvan, és mindegyik pontosan
ugyanazt a célnyelvi szöveget adja. Kétértelmű esetben üres `unfinished` marad.
Az eredeti fájlokhoz a program nem ír.
"""

from __future__ import annotations

import argparse
import copy
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from picasapy.app.i18n.dictionary import (
    ORIGIN_PICASA,
    ORIGIN_PICASAPY,
    dump_catalog,
    index_original_texts,
    match_original_translation,
    missing_count,
    set_message_origin,
)
from picasapy.app.language_controller import OWN_LANGUAGE_NAMES, SUPPORTED_LANGUAGES

_REFERENCE_LANGUAGES = (
    "ar", "fa", "iw", "id", "ca", "da", "de", "enUK", "enUS", "es", "fr",
    "hr", "it", "lv", "lt", "hu", "nl", "no", "pl", "pt", "pt-BR", "ro",
    "sk", "sl", "fi", "sv", "fil", "vi", "tr", "cs", "el", "ru", "sr",
    "uk", "bg", "hi", "th", "zh-CN", "zh-TW", "ja", "ko",
)
_APP_CODE = {"enUS": "en", **{code: code for code in _REFERENCE_LANGUAGES if code != "enUS"}}
_QT_LOCALE = {
    "en": "en_US",
    "enUK": "en_GB",
    "iw": "iw",
    "pt-BR": "pt_BR",
    "zh-CN": "zh_CN",
    "zh-TW": "zh_TW",
}


def _original_texts(folder: Path) -> dict[str, str]:
    """A #2971 `szovegek()`-kulcsokkal azonos, kizárólag olvasó XML-beolvasás."""
    output: dict[str, str] = {}
    for xml_path in sorted(folder.glob("*.xml")):
        try:
            root = ET.parse(xml_path).getroot()
        except (ET.ParseError, OSError):
            continue
        panel = xml_path.stem
        if root.tag == "resources":
            for item in root.iterfind(".//stringres"):
                value = (item.findtext("xmbtext") or "").strip()
                key = item.get("id")
                if key and value:
                    output[f"{panel}:{key}"] = value
        elif root.tag == "tooltips":
            for item in root.iterfind(".//action"):
                value = (item.findtext("xmbtext") or "").strip()
                key = item.get("xmbdesc") or item.get("target")
                if key and value:
                    output[f"{panel}:{key}"] = value
        elif root.tag == "Win32Res":
            for index, item in enumerate(root.iterfind(".//*[xmbtext]")):
                value = (item.findtext("xmbtext") or "").strip()
                if value:
                    output[f"{panel}:win32:{index}"] = value
    return output


def _translation(message: ET.Element) -> ET.Element:
    translation = message.find("translation")
    if translation is None:
        translation = ET.SubElement(message, "translation")
    return translation


def _set_text(element: ET.Element, source: ET.Element) -> None:
    element.text = source.text
    for child in list(element):
        element.remove(child)
    for child in source:
        element.append(copy.deepcopy(child))


def _set_finished(message: ET.Element, value: str) -> None:
    translation = _translation(message)
    translation.attrib.pop("type", None)
    for child in list(translation):
        translation.remove(child)
    translation.text = value


def _set_unfinished(message: ET.Element) -> None:
    translation = _translation(message)
    translation.set("type", "unfinished")
    forms = translation.findall("numerusform")
    if message.get("numerus") == "yes":
        if not forms:
            forms = [ET.SubElement(translation, "numerusform")]
        for form in forms:
            form.text = None
            for child in list(form):
                form.remove(child)
        translation.text = None
    else:
        for child in list(translation):
            translation.remove(child)
        translation.text = None


def _set_source_language(message: ET.Element) -> None:
    translation = _translation(message)
    translation.attrib.pop("type", None)
    source = message.find("source")
    if source is None:
        raise ValueError("Qt TS-üzenetből hiányzik a <source>")
    if message.get("numerus") == "yes":
        forms = translation.findall("numerusform")
        if not forms:
            forms = [ET.SubElement(translation, "numerusform")]
        for form in forms:
            _set_text(form, source)
        translation.text = None
    else:
        _set_text(translation, source)


def _hungarian_text(message: ET.Element) -> str:
    translation = message.find("translation")
    if translation is None:
        return ""
    forms = translation.findall("numerusform")
    if forms:
        return forms[0].text or ""
    return translation.text or ""


def _build_language(
    base: ET.Element,
    app_code: str,
    source_texts: dict[str, str],
    target_texts: dict[str, str],
    source_index: dict[str, tuple[str, ...]],
) -> ET.Element:
    catalog = copy.deepcopy(base)
    catalog.set("language", _QT_LOCALE.get(app_code, app_code))
    catalog.set("sourcelanguage", "en_US")

    for message in catalog.iter("message"):
        hungarian_translation = _hungarian_text(message)
        origin_match = match_original_translation(
            hungarian_translation,
            source_texts,
            source_texts,
            hungarian_index=source_index,
        )
        if origin_match is None:
            set_message_origin(message, ORIGIN_PICASAPY)
        else:
            set_message_origin(message, ORIGIN_PICASA, origin_match[1])

        if app_code == "en":
            _set_source_language(message)
            continue

        # A DLL-sor nem tárol Qt-numerus-alakokat. Ezeket inkább az 5. fázisra
        # hagyjuk, mintsem egyetlen eredeti alakból nyelvtani formát találjunk ki.
        if message.get("numerus") == "yes":
            _set_unfinished(message)
            continue

        if origin_match is None:
            _set_unfinished(message)
            continue

        match = match_original_translation(
            hungarian_translation,
            source_texts,
            target_texts,
            hungarian_index=source_index,
        )
        if match is None:
            _set_unfinished(message)
            continue
        value, keys = match
        _set_finished(message, value)
        set_message_origin(message, ORIGIN_PICASA, keys)
    return catalog


def build_dictionaries(references: Path, i18n_dir: Path, *, compile_qm: bool = True) -> list[tuple[str, int]]:
    """Mind a 41 TS fájl generálása; visszaadja a hiányzó sorok számát."""
    reference_folders = {path.name: path for path in references.iterdir() if path.is_dir()}
    if set(reference_folders) != set(_REFERENCE_LANGUAGES):
        missing = sorted(set(_REFERENCE_LANGUAGES) - set(reference_folders))
        extra = sorted(set(reference_folders) - set(_REFERENCE_LANGUAGES))
        raise ValueError(f"a referencia nyelvlistája eltér: hiányzó={missing}, fölös={extra}")
    if tuple(SUPPORTED_LANGUAGES) != tuple(_APP_CODE[code] for code in _REFERENCE_LANGUAGES):
        raise ValueError("a nyelvválasztó és az eredeti nyelvlista sorrendje eltér")
    if set(OWN_LANGUAGE_NAMES) != set(SUPPORTED_LANGUAGES):
        raise ValueError("a nyelvválasztó nyelvnevei hiányosak")

    hu_path = i18n_dir / "picasapy_hu.ts"
    base = ET.parse(hu_path).getroot()
    if base.tag != "TS":
        raise ValueError(f"nem Qt TS fájl: {hu_path}")
    hu_originals = _original_texts(reference_folders["hu"])
    hu_index = index_original_texts(hu_originals)
    originals = {
        language: _original_texts(folder)
        for language, folder in reference_folders.items()
    }

    summaries: list[tuple[str, int]] = []
    for reference_code in _REFERENCE_LANGUAGES:
        app_code = _APP_CODE[reference_code]
        if app_code == "hu":
            catalog = copy.deepcopy(base)
            catalog.set("sourcelanguage", "en_US")
            for message in catalog.iter("message"):
                match = match_original_translation(
                    _hungarian_text(message),
                    hu_originals,
                    hu_originals,
                    hungarian_index=hu_index,
                )
                if match is None:
                    set_message_origin(message, ORIGIN_PICASAPY)
                else:
                    set_message_origin(message, ORIGIN_PICASA, match[1])
        else:
            catalog = _build_language(
                base,
                app_code,
                hu_originals,
                originals[reference_code],
                hu_index,
            )

        ts_path = i18n_dir / f"picasapy_{app_code}.ts"
        ts_path.write_bytes(dump_catalog(catalog))
        if compile_qm:
            qm_path = i18n_dir / f"picasapy_{app_code}.qm"
            result = subprocess.run(
                ["pyside6-lrelease", str(ts_path), "-qm", str(qm_path), "-silent"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=60,
            )
            if result.returncode:
                raise RuntimeError(
                    f"pyside6-lrelease {app_code} hibával tért vissza:\n"
                    f"{result.stdout}{result.stderr}"
                )
        summaries.append((app_code, missing_count(catalog)))
    return summaries


def main(argv: list[str] | None = None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Qt nyelvi szótárak előállítása (#4313)")
    parser.add_argument(
        "--references",
        type=Path,
        default=Path.home() / "picasapy-agent" / "referencia" / "i18n",
    )
    parser.add_argument(
        "--i18n-dir",
        type=Path,
        default=project_root / "src" / "picasapy" / "app" / "i18n",
    )
    args = parser.parse_args(argv)
    summaries = build_dictionaries(args.references, args.i18n_dir)
    print("Nyelvenkénti hiányzó sorok (Qt TS):")
    for code, count in summaries:
        print(f"{code:5s} {count:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

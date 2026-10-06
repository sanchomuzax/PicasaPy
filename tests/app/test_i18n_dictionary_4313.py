"""#4313: nyelvenkénti Qt-szótárak eredetjelöléssel és veszteségmentes körúttal."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from picasapy.app.language_controller import (
    OWN_LANGUAGE_NAMES,
    SUPPORTED_LANGUAGES,
    coerce_language,
)

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"
_EXPECTED_CODES = (
    "ar", "fa", "iw", "id", "ca", "da", "de", "enUK", "en", "es", "fr",
    "hr", "it", "lv", "lt", "hu", "nl", "no", "pl", "pt", "pt-BR", "ro",
    "sk", "sl", "fi", "sv", "fil", "vi", "tr", "cs", "el", "ru", "sr",
    "uk", "bg", "hi", "th", "zh-CN", "zh-TW", "ja", "ko",
)

# A #4313 előtti teljes magyar TS tartalmának SHA-256 lenyomata. Csak az új
# eredetjelölők és az új gyökér sourcelanguage-attribútuma maradnak ki.
_HU_ORIGINAL_CONTENT_SHA256 = "42a7ebe4e9b034b59dcda074904532ae74bde56c5b645ce1469e92f23283011c"


def _catalog_fingerprint(path: Path) -> str:
    root = ET.parse(path).getroot()
    def content(element: ET.Element, *, document_root: bool = False):
        attributes = dict(element.attrib)
        if document_root:
            attributes.pop("sourcelanguage", None)

        if element.tag == "extracomment":
            lines = [
                line
                for line in (element.text or "").splitlines()
                if not line.startswith(("picasapy-origin:", "picasapy-origin-key:"))
            ]
            if not lines:
                return None
            text = "\n".join(lines)
        else:
            text = element.text
        if list(element) and text and not text.strip():
            text = None

        children = []
        for child in list(element):
            child_content = content(child)
            if child_content is not None:
                tail = child.tail if child.tail and child.tail.strip() else None
                children.append((child_content, tail))
        return element.tag, tuple(sorted(attributes.items())), text, tuple(children)

    payload = json.dumps(
        content(root, document_root=True), ensure_ascii=False, separators=(",", ":")
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def test_language_controller_lists_all_41_languages_with_native_names():
    assert SUPPORTED_LANGUAGES == _EXPECTED_CODES
    assert set(OWN_LANGUAGE_NAMES) == set(_EXPECTED_CODES)
    assert len(set(OWN_LANGUAGE_NAMES.values())) == 41


def test_locale_variants_select_the_matching_dictionary_without_english_fallback():
    assert coerce_language("en_GB") == "enUK"
    assert coerce_language("pt_BR") == "pt-BR"
    assert coerce_language("zh_TW") == "zh-TW"
    assert coerce_language("he_IL") == "iw"
    assert coerce_language("de_DE") == "de"


def test_original_pairing_keeps_ambiguous_rows_unmatched():
    from picasapy.app.i18n.dictionary import match_original_translation

    hu = {"ui:a": "  &Kezdőlap.  ", "ui:b": "kezdőlap"}
    assert match_original_translation(
        "Kezdőlap", hu, {"ui:a": "Start", "ui:b": "Start"}
    ) == ("Start", ("ui:a", "ui:b"))
    assert match_original_translation(
        "Kezdőlap", hu, {"ui:a": "Start", "ui:b": "Homepage"}
    ) is None
    assert match_original_translation("Más szöveg", hu, {"ui:a": "Start"}) is None


def test_all_languages_have_one_ts_and_runtime_qm():
    from PySide6.QtCore import QTranslator

    missing = [
        f"{code}: {suffix}"
        for code in SUPPORTED_LANGUAGES
        for suffix in ("ts", "qm")
        if not (_I18N / f"picasapy_{code}.{suffix}").is_file()
    ]
    assert not missing, "hiányzó nyelvi fájlok: " + ", ".join(missing)
    for code in SUPPORTED_LANGUAGES:
        translator = QTranslator()
        assert translator.load(str(_I18N / f"picasapy_{code}.qm")), (
            f"{code}: a Qt nem tudta betölteni a .qm fájlt"
        )


def test_selected_language_qm_is_installed_by_the_startup_path(monkeypatch):
    from PySide6.QtCore import QCoreApplication

    from picasapy.app import application
    from picasapy.app.i18n.dictionary import message_origin

    app = QCoreApplication.instance() or QCoreApplication([])
    monkeypatch.setattr(application, "_startup_language", lambda settings=None: "de")
    translator = application._install_translator(app)
    assert translator is not None, "a következő indításra kiválasztott .qm nem töltődött be"
    try:
        catalog = ET.parse(_I18N / "picasapy_de.ts").getroot()
        pair = next(
            message
            for message in catalog.iter("message")
            if message_origin(message) == "picasa"
            and message.find("translation") is not None
            and message.find("translation").text
        )
        context = next(
            context
            for context in catalog.findall("context")
            if pair in list(context.iter("message"))
        )
        translated = translator.translate(
            context.findtext("name") or "",
            pair.findtext("source") or "",
            pair.findtext("comment"),
        )
        assert translated == pair.findtext("translation")
        assert translated != pair.findtext("source")
    finally:
        app.removeTranslator(translator)


def test_hungarian_dictionary_preserves_all_pre_migration_messages():
    path = _I18N / "picasapy_hu.ts"
    assert _catalog_fingerprint(path) == _HU_ORIGINAL_CONTENT_SHA256, (
        "a magyar TS tartalma megváltozott az új eredetjelölőkön kívül"
    )


def test_hungarian_catalog_marks_inherited_picasa_text_with_its_origin():
    from picasapy.app.i18n.dictionary import message_origin

    root = ET.parse(_I18N / "picasapy_hu.ts").getroot()
    message = next(
        message
        for message in root.iter("message")
        if message.findtext("source") == "Choose Edits"
    )
    assert message.findtext("translation") == "Szerkesztett változatok kiválasztása"
    assert message_origin(message) == "picasa"
    assert "picasapy-origin-key: stringres:CThumbUI::Confirm2upEditTitle" in (
        message.findtext("extracomment") or ""
    )


def test_untranslated_picasa_row_keeps_its_origin_in_the_target_catalog():
    from picasapy.app.i18n.dictionary import message_origin

    root = ET.parse(_I18N / "picasapy_ro.ts").getroot()
    message = next(
        message
        for message in root.iter("message")
        if message.findtext("source") == "Close"
    )
    assert message.find("translation").get("type") == "unfinished"
    assert message_origin(message) == "picasa"
    origin_keys = (message.findtext("extracomment") or "").partition(
        "picasapy-origin-key: "
    )[2].split(";")
    assert "stringres:EXIF::Close" in origin_keys


def test_all_dictionaries_round_trip_byte_for_byte_and_report_missing_rows(capsys):
    from picasapy.app.i18n.dictionary import dump_catalog, load_catalog, missing_count

    summaries = []
    for code in SUPPORTED_LANGUAGES:
        path = _I18N / f"picasapy_{code}.ts"
        source = path.read_bytes()
        catalog = load_catalog(source)
        assert dump_catalog(catalog) == source, f"{code}: a TS körút nem bájtazonos"

        messages = list(catalog.iter("message"))
        assert messages, f"{code}: üres nyelvi szótár"
        for message in messages:
            extra = message.findtext("extracomment") or ""
            assert "picasapy-origin:" in extra, (
                f"{code}/{message.findtext('source')!r}: nincs gépi eredetjelölő"
            )

        summaries.append((code, missing_count(catalog)))

    assert len(summaries) == 41
    with capsys.disabled():
        print("Hiányzó aktív fordítások nyelvenként:")
        for code, count in summaries:
            print(f"{code:5s} {count:4d}")

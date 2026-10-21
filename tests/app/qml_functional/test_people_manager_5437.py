"""#5437: a csempe, a People-ablak és a mentett arc valódi felületi útja."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest

from picasapy.index import all_photos, open_index, photo_by_id
from picasapy.ini import contacts_of, load_document, parse_faces
from picasapy.scanner import PICASA_INI_NAME
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (
    _click,
    _find_item,
    _find_object,
    _seed_six_faces,
)
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (  # noqa: F401
    qml_app_5183,
)
from tests.support.varakozas import var_feltetelre


_HEIGHT_OFFSETS = (-5, 0, 5)
_TARGET_FACE = 5


def _open_unnamed(window, qt_app, face_scan, controller, engine, tmp_path, offset=0):
    window.setWidth(1280)
    window.setHeight(1005 + offset)
    if (
        face_scan._settings.status() != QSettings.Status.NoError
        or not face_scan._settings.fileName()
    ):
        face_scan._settings = QSettings(
            str(tmp_path / "facescan.ini"), QSettings.Format.IniFormat
        )
    _seed_six_faces(Path(controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)

    folder_pane = _find_item(window, "folderPane")
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert var_feltetelre(qt_app, lambda: unnamed_row is not None and unnamed_row.width() > 0)
    _click(qt_app, unnamed_row)
    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app, lambda: view is not None and view.property("visible") is True
    )
    welcome = _find_object(window, "unnamedWelcomeDialog")
    if welcome is not None and welcome.property("visible") is True:
        _click(qt_app, _find_item(window, "unnamedWelcomeCloseButton"))
        assert var_feltetelre(qt_app, lambda: welcome.property("visible") is False)
    return _find_item(window, f"unnamedFaceNameField_{_TARGET_FACE}")


def _type_text(window, qt_app, item, value: str) -> None:
    _click(qt_app, item)
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert value.isascii()
    if not value:
        QTest.keyClick(window, Qt.Key.Key_Backspace)
        qt_app.processEvents()
        return
    for character in value:
        if character.isupper():
            QTest.keyClick(window, character)
        else:
            key_name = "Space" if character == " " else character.upper()
            QTest.keyClick(window, getattr(Qt.Key, f"Key_{key_name}"))
        qt_app.processEvents()


def _enter_name(window, qt_app, name_field, value: str) -> None:
    _type_text(window, qt_app, name_field, value)
    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()


def _wait_dialog(window, qt_app):
    dialog = _find_object(window, "peopleManagerDialog")
    assert var_feltetelre(
        qt_app,
        lambda: dialog is not None and dialog.property("visible") is True,
        3.0,
    )
    return dialog


def _seed_person(face_scan, controller, face_id: int, name: str) -> None:
    assert face_scan.assignNameToFaces([face_id], name)
    controller.refreshCollections()
    controller.prepareNameSuggestions()


@pytest.mark.parametrize("height_offset", _HEIGHT_OFFSETS)
def test_csempebol_uj_szemely_mentese_az_arcot_is_hozzarendeli(
    qml_app_5183, qt_app, tmp_path, height_offset  # noqa: F811
):
    window, controller, engine = qml_app_5183
    face_scan = engine.rootContext().contextProperty("faceScanController")
    field = _open_unnamed(
        window, qt_app, face_scan, controller, engine, tmp_path, height_offset
    )

    _enter_name(window, qt_app, field, "Nora Kertesz")
    dialog = _wait_dialog(window, qt_app)
    search = _find_item(window, "peopleManagerSearchField")
    assert search.property("text") == "Nora Kertesz"
    new_button = _find_item(window, "peopleManagerNewButton")
    _click(qt_app, new_button)

    name = _find_item(window, "peopleManagerNameField")
    assert name.property("text") == "Nora Kertesz"
    _click(qt_app, _find_item(window, "peopleManagerOkButton"))
    assert var_feltetelre(qt_app, lambda: dialog.property("visible") is False, 3.0)
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 5, 3.0)
    assert any(person.name == "Nora Kertesz" for person in controller._people)
    assert _find_item(window, "personItem_Nora Kertesz") is not None

    with open_index(controller._db_path) as conn:
        face_row = conn.execute(
            "SELECT photo_id FROM face WHERE id = ?", (_TARGET_FACE,)
        ).fetchone()
        photo = photo_by_id(conn, face_row[0])
        photos = all_photos(conn)
    ini_path = Path(photo.folder_path) / PICASA_INI_NAME
    document = load_document(ini_path)
    matching = tuple(contact for contact in contacts_of(document) if contact.name == "Nora Kertesz")
    assert len(matching) == 1
    assert "Nora Kertesz" in controller._people_contacts_path().read_text(
        encoding="utf-8"
    )
    face_section = document.section(photo.name)
    raw_faces = face_section.get("faces")
    assert raw_faces
    assert any(face.contact_id == matching[0].person_id for face in parse_faces(raw_faces))
    assert "[Contacts2]" in ini_path.read_text(encoding="utf-8")
    assert "faces=" in ini_path.read_text(encoding="utf-8")
    assert any((Path(p.folder_path) / PICASA_INI_NAME).exists() for p in photos)


def test_a_nevszavas_sorrend_es_le_nyil_enter_a_kijelolt_nevet_valasztja(
    qml_app_5183, qt_app, tmp_path  # noqa: F811
):
    window, controller, engine = qml_app_5183
    face_scan = engine.rootContext().contextProperty("faceScanController")
    field = _open_unnamed(window, qt_app, face_scan, controller, engine, tmp_path)
    _seed_person(face_scan, controller, 1, "Kiss Anna")
    _seed_person(face_scan, controller, 2, "Anna Kiss")

    field = _find_item(window, f"unnamedFaceNameField_{_TARGET_FACE}")
    _type_text(window, qt_app, field, "ki")
    popup = _find_item(window, f"unnamedNameSuggestions_{_TARGET_FACE}")
    assert var_feltetelre(
        qt_app,
        lambda: popup is not None and popup.property("visible") is True,
        3.0,
    )
    first = _find_item(window, f"unnamedFaceSuggestion_{_TARGET_FACE}_0")
    second = _find_item(window, f"unnamedFaceSuggestion_{_TARGET_FACE}_1")
    assert first.property("personName") == "Kiss Anna"
    assert second.property("personName") == "Anna Kiss"

    QTest.keyClick(window, Qt.Key.Key_Down)
    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()
    _wait_dialog(window, qt_app)
    assert _find_item(window, "peopleManagerSearchField").property("text") == "Kiss Anna"


def test_people_kereso_ugyanazt_a_szavas_egyezest_es_rendezest_hasznalja(
    qml_app_5183, qt_app, tmp_path  # noqa: F811
):
    window, controller, engine = qml_app_5183
    face_scan = engine.rootContext().contextProperty("faceScanController")
    field = _open_unnamed(window, qt_app, face_scan, controller, engine, tmp_path)
    _seed_person(face_scan, controller, 1, "Kiss Anna")
    _seed_person(face_scan, controller, 2, "Anna Kiss")
    _seed_person(face_scan, controller, 3, "Nagykiss")

    field = _find_item(window, f"unnamedFaceNameField_{_TARGET_FACE}")
    _enter_name(window, qt_app, field, "ki")
    dialog = _wait_dialog(window, qt_app)

    assert _find_item(window, "peopleManagerSearchField").property("text") == "ki"
    entries = dialog.property("filteredEntries")
    assert [entry["name"] for entry in entries] == ["Kiss Anna", "Anna Kiss"]
    assert _find_item(window, "peopleManagerContact_Nagykiss") is None


def test_duplikalt_uj_szemelynel_igen_nem_kerdes_jelenik_meg(
    qml_app_5183, qt_app, tmp_path  # noqa: F811
):
    window, controller, engine = qml_app_5183
    face_scan = engine.rootContext().contextProperty("faceScanController")
    field = _open_unnamed(window, qt_app, face_scan, controller, engine, tmp_path)
    _seed_person(face_scan, controller, 1, "Kiss Anna")
    field = _find_item(window, f"unnamedFaceNameField_{_TARGET_FACE}")
    _enter_name(window, qt_app, field, "Kiss Anna")
    dialog = _wait_dialog(window, qt_app)
    _click(qt_app, _find_item(window, "peopleManagerNewButton"))
    _click(qt_app, _find_item(window, "peopleManagerOkButton"))

    duplicate = _find_object(window, "peopleManagerDuplicateDialog")
    assert var_feltetelre(
        qt_app,
        lambda: duplicate is not None and duplicate.property("visible") is True,
        3.0,
    )
    message = _find_item(window, "peopleManagerDuplicateMessage")
    assert "You already have a person with the name" in message.property("text")
    _click(qt_app, _find_item(window, "peopleManagerDuplicateNo"))
    assert dialog.property("visible") is True


def test_ures_uj_szemely_figyelmeztet_es_visszaallitja_a_sort(
    qml_app_5183, qt_app, tmp_path  # noqa: F811
):
    window, controller, engine = qml_app_5183
    face_scan = engine.rootContext().contextProperty("faceScanController")
    field = _open_unnamed(window, qt_app, face_scan, controller, engine, tmp_path)
    _enter_name(window, qt_app, field, "Uj Ember")
    dialog = _wait_dialog(window, qt_app)
    _click(qt_app, _find_item(window, "peopleManagerNewButton"))
    name = _find_item(window, "peopleManagerNameField")
    _type_text(window, qt_app, name, "")
    ok = _find_item(window, "peopleManagerOkButton")
    assert ok.property("enabled") is True
    _click(qt_app, ok)

    message_dialog = _find_object(window, "peopleManagerMessageDialog")
    assert var_feltetelre(
        qt_app,
        lambda: message_dialog is not None
        and message_dialog.property("visible") is True,
        3.0,
    )
    message = _find_item(window, "peopleManagerMessageText")
    assert "Empty People are not allowed." in message.property("text")
    _click(qt_app, _find_item(window, "peopleManagerMessageOk"))
    assert name.property("text") == ""
    assert dialog.property("visible") is True


def test_revert_csak_modositaskor_es_delete_megerositest_ker(
    qml_app_5183, qt_app, tmp_path  # noqa: F811
):
    window, controller, engine = qml_app_5183
    face_scan = engine.rootContext().contextProperty("faceScanController")
    field = _open_unnamed(window, qt_app, face_scan, controller, engine, tmp_path)
    _seed_person(face_scan, controller, 1, "Anna Kiss")
    field = _find_item(window, f"unnamedFaceNameField_{_TARGET_FACE}")
    _enter_name(window, qt_app, field, "Anna Kiss")
    _wait_dialog(window, qt_app)
    name = _find_item(window, "peopleManagerNameField")
    revert = _find_item(window, "peopleManagerRevertButton")
    assert revert.property("enabled") is False
    _type_text(window, qt_app, name, "Anna Kics")
    assert revert.property("enabled") is True
    _click(qt_app, revert)
    assert name.property("text") == "Anna Kiss"
    assert revert.property("enabled") is False

    _click(qt_app, _find_item(window, "peopleManagerDeleteButton"))
    confirmation = _find_object(window, "peopleManagerDeleteDialog")
    assert var_feltetelre(
        qt_app,
        lambda: confirmation is not None
        and confirmation.property("visible") is True,
        3.0,
    )
    assert _find_item(window, "peopleManagerDeleteDontWarn") is not None
    _click(qt_app, _find_item(window, "peopleManagerDeleteNo"))
    assert confirmation.property("visible") is False

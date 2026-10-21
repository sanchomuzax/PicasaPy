"""#5435: a név-javaslat első leütésre látszik és névadás után frissül."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

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

_WINDOW_HEIGHT_OFFSETS = (-5, 0, 5)
_TARGET_FACE = 5


def _open_name_field(window, qt_app, face_id: int):
    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert var_feltetelre(
        qt_app,
        lambda: unnamed_row is not None and unnamed_row.width() > 0,
    )
    _click(qt_app, unnamed_row)

    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app,
        lambda: view is not None and view.property("visible") is True,
    )
    welcome = _find_object(window, "unnamedWelcomeDialog")
    if welcome is not None and welcome.property("visible") is True:
        close_button = _find_item(window, "unnamedWelcomeCloseButton")
        assert close_button is not None
        _click(qt_app, close_button)
        assert var_feltetelre(
            qt_app, lambda: welcome.property("visible") is False
        )

    name_field = _find_item(window, f"unnamedFaceNameField_{face_id}")
    assert var_feltetelre(
        qt_app,
        lambda: name_field is not None and name_field.width() > 0,
    )
    return name_field


def _type_first_key(window, qt_app, name_field, key: Qt.Key):
    _click(qt_app, name_field)
    QTest.keyClick(window, key)
    qt_app.processEvents()


def _suggestion(window, face_id: int, expected_name: str):
    for index in range(30):
        item = _find_item(window, f"unnamedFaceSuggestion_{face_id}_{index}")
        if item is not None and item.property("personName") == expected_name:
            return item
    return None


@pytest.mark.parametrize("height_offset", _WINDOW_HEIGHT_OFFSETS)
def test_a_mezo_elso_valodi_leutesere_megjelenik_a_javaslat(
    qml_app_5183, qt_app, height_offset  # noqa: F811
):
    window, controller, engine = qml_app_5183
    window.setWidth(1280)
    window.setHeight(1005 + height_offset)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(controller._db_path)
    assert face_scan.assignNameToFaces([1], "Anna Kovács")
    controller.refreshCollections()
    assert callable(controller.prepareNameSuggestions)
    assert callable(controller.nameSuggestions)

    name_field = _open_name_field(window, qt_app, _TARGET_FACE)
    _type_first_key(window, qt_app, name_field, Qt.Key.Key_A)

    popup = _find_item(window, f"unnamedNameSuggestions_{_TARGET_FACE}")
    assert var_feltetelre(
        qt_app,
        lambda: popup is not None and popup.property("visible") is True,
    ), "az első leütés után nem jelent meg a javaslatlista"
    assert name_field.property("text") == "a"
    assert var_feltetelre(
        qt_app,
        lambda: _suggestion(window, _TARGET_FACE, "Anna Kovács") is not None,
    )


@pytest.mark.parametrize("height_offset", _WINDOW_HEIGHT_OFFSETS)
def test_a_nevadas_utan_az_uj_nev_a_kovetkezo_csempen_javasolhato(
    qml_app_5183, qt_app, height_offset  # noqa: F811
):
    window, controller, engine = qml_app_5183
    window.setWidth(1280)
    window.setHeight(1005 + height_offset)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(controller._db_path)
    assert face_scan.assignNameToFaces([1], "Anna Kovács")
    controller.refreshCollections()
    assert callable(controller.prepareNameSuggestions)
    assert callable(controller.nameSuggestions)
    controller.prepareNameSuggestions()

    assert face_scan.assignNameToFaces([2], "Nóra Nagy")
    # A valódi People-kezelő ugyanezt hívja a sikeres arcrögzítés után.
    controller.refreshCollections()

    name_field = _open_name_field(window, qt_app, _TARGET_FACE)
    _type_first_key(window, qt_app, name_field, Qt.Key.Key_N)

    popup = _find_item(window, f"unnamedNameSuggestions_{_TARGET_FACE}")
    assert var_feltetelre(
        qt_app,
        lambda: popup is not None and popup.property("visible") is True,
    )
    assert var_feltetelre(
        qt_app,
        lambda: _suggestion(window, _TARGET_FACE, "Nóra Nagy") is not None,
    ), "a névadás után az új személy nem került be a következő csempe javaslataiba"

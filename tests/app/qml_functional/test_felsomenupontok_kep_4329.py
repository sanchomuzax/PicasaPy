"""#4329: felső menüpontok — kep."""

from pathlib import Path

import pytest

from picasapy.app.faces_helper import FacesHelper
from picasapy.ini import load_document
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _kijeloles,
    _magassag,
    _nyisd_meg_felso_menut,
    _varj,
)


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_view_and_edit_kattintas_megnyitja_a_kijelolt_kepeket(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureViewAndEdit"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: window.property("viewerOpen") is True), (
        "a Kép ▸ View and Edit nem nyitotta meg a kijelölt képet"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_hide_es_unhide_kattintas_a_hidden_ini_allapotot_valtoztatja(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    controller.setShowHidden(True)
    qt_app.processEvents()
    kep = Path(controller.photos.filePathAt(0))
    ini = kep.parent / ".picasa.ini"

    def hidden_ertek():
        if not ini.exists():
            return None
        szakasz = load_document(ini).section(kep.name)
        return szakasz.get("hidden") if szakasz is not None else None

    assert hidden_ertek() is None

    _menu_bar, _menu, _fejléc, hide = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureHide"
    )
    assert hide.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: hide.property("enabled") is True)
    _kattints(qt_app, hide)

    assert _varj(qt_app, lambda: hidden_ertek() == "yes"), (
        "a Kép ▸ Hide nem írta be a hidden=yes értéket a .picasa.ini-be"
    )

    sor = next(
        index
        for index in range(controller.photos.rowCount())
        if controller.photos.itemAt(index)["name"] == kep.name
    )
    _menu_bar, _menu, _fejléc, unhide = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureUnhide"
    )
    assert unhide.property("enabled") is False
    _kijeloles(window, qt_app, [sor])
    assert _varj(qt_app, lambda: unhide.property("enabled") is True)
    _kattints(qt_app, unhide)

    assert _varj(qt_app, lambda: hidden_ertek() is None), (
        "a Kép ▸ Unhide nem törölte a hidden kulcsot a .picasa.ini-ből"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_hide_kattintas_mar_rejtett_kijelolest_rejtve_hagyja(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    controller.setShowHidden(True)
    controller.toggleHiddenRows([0])
    assert _varj(qt_app, lambda: controller.photos.itemAt(0)["hidden"] is True)

    _menu_bar, _menu, _fejléc, hide = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureHide"
    )
    assert hide.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: hide.property("enabled") is True)
    _kattints(qt_app, hide)

    assert _varj(qt_app, lambda: controller.photos.itemAt(0)["hidden"] is True), (
        "a Kép ▸ Hide megjelenítette a már rejtett kijelölt képet"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_unhide_kattintas_csak_a_rejtett_kijelolteket_jeleniti_meg(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    controller.setShowHidden(True)
    controller.toggleHiddenRows([0])
    qt_app.processEvents()
    assert controller.photos.itemAt(0)["hidden"] is True
    assert controller.photos.itemAt(1)["hidden"] is False
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureUnhide"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0, 1])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: controller.photos.itemAt(0)["hidden"] is False)
    assert controller.photos.itemAt(1)["hidden"] is False
    selected = window.property("selectedIndexes")
    if hasattr(selected, "toVariant"):
        selected = selected.toVariant()
    assert list(selected or []) == []


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_reset_faces_kattintas_a_kijelolt_kepek_meglevo_kezelot_hivja(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    first = tmp_path / "kepek" / "a.jpg"
    other = tmp_path / "kepek" / "b.jpg"
    helper = FacesHelper()
    assert helper.addFace(str(first), 0.1, 0.2, 0.4, 0.6, "Ada")
    assert helper.addFace(str(other), 0.2, 0.3, 0.5, 0.7, "Bela")
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureResetFaces"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    first_section = load_document(first.parent / ".picasa.ini").section(first.name)
    other_section = load_document(other.parent / ".picasa.ini").section(other.name)
    assert first_section is None or first_section.get("faces") is None
    assert other_section is not None and other_section.get("faces")

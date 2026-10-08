"""#4627: az Arcok alaphelyzetbe állítása Ctrl- és Shift-ágának megerősítése.

Külön fájlban, mert a #4329 tesztfájl egyben a CI 2400 MB-os memóriaplafonját
túllépte (exit -9).
"""

from __future__ import annotations


import pytest
from PySide6.QtCore import Qt

from picasapy.app.faces_helper import FacesHelper
from picasapy.ini import load_document

from tests.app.qml_functional.test_felsomenupontok_meglevo_muveletek_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _kijeloles,
    _magassag,
    _nyisd_meg_felso_menut,
    _objektum,
    _varj,
)


@pytest.fixture
def qml_app_hu(qml_app, qt_app):
    """A később megnyíló reset-párbeszédhez magyar fordítást telepít."""
    import picasapy.app.application as app_module
    from PySide6.QtCore import QTranslator

    translator = QTranslator(qt_app)
    assert translator.load(str(app_module._APP_DIR / "i18n" / "picasapy_hu.qm"))
    qt_app.installTranslator(translator)
    try:
        yield qml_app
    finally:
        qt_app.removeTranslator(translator)


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
@pytest.mark.parametrize(
    ("modifiers", "source", "translation"),
    [
        (
            Qt.KeyboardModifier.ControlModifier,
            "WARNING! This will DELETE all face data, people albums, and rescan all photos for faces again. This can REMOVE name tags on synced web albums. Do you want to do this?",
            "FIGYELEM! Ez a művelet TÖRLI az összes, arcokra vonatkozó adatot, a személyi albumokat, és újrakeresi az arcokat az összes fotón. A művelet egyúttal ELTÁVOLÍTHATJA a szinkronizált webalbumokban lévő névcímkéket is. Ezt szeretné tenni?",
        ),
        (
            Qt.KeyboardModifier.ShiftModifier,
            "WARNING! This will DELETE all people albums, and move all the faces to the unnamed album. This can REMOVE name tags on synced web albums also. Do you want to do this?",
            "FIGYELMEZTETÉS! Ez a művelet TÖRLI az összes személyi albumot, és a Név nélküliek albumba helyezi át az arcokat. A művelet a szinkronizált webalbumokból is ELTÁVOLÍTHATJA a névcímkéket. Ezt szeretné tenni?",
        ),
    ],
    ids=["ctrl", "shift"],
)
def test_reset_faces_modifier_branch_asks_before_global_change_and_cancel_is_safe(
    qml_app_hu,
    qt_app,
    tmp_path,
    height_offset,
    modifiers,
    source,
    translation,
):
    """# rontás-kontroll: Ctrl/Shift megerősítés nélkül → 1 failed"""
    from picasapy.ini import parse_faces

    window, controller, _engine = qml_app_hu
    _magassag(window, height_offset)
    first = tmp_path / "kepek" / "a.jpg"
    other = tmp_path / "kepek" / "b.jpg"
    helper = FacesHelper()
    assert helper.addFace(str(first), 0.1, 0.2, 0.4, 0.6, "Ada")
    assert helper.addFace(str(other), 0.2, 0.3, 0.5, 0.7, "Bela")

    row = controller.photos.rowOfPath(str(first))
    assert row >= 0
    _kijeloles(window, qt_app, [row])
    _menu_bar, _menu, _fejlec, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureResetFaces"
    )
    _kattints(qt_app, item, modifiers)

    assert _varj(
        qt_app,
        lambda: (
            (dialog := _objektum(window, "resetFacesConfirmDialog")) is not None
            and dialog.property("visible") is True
        ),
    ), "a módosítós ág nem nyitotta meg a megerősítő párbeszédet"
    message = _objektum(window, "resetFacesConfirmMessage")
    assert message is not None
    assert message.property("text") == translation, source
    for path in (first, other):
        document = load_document(path.parent / ".picasa.ini")
        section = document.section(path.name)
        assert section is not None and parse_faces(section.get("faces") or "")

    _kattints(qt_app, _objektum(window, "resetFacesCancelButton"))
    assert _varj(
        qt_app,
        lambda: _objektum(window, "resetFacesConfirmDialog").property("visible")
        is False,
    )
    for path in (first, other):
        document = load_document(path.parent / ".picasa.ini")
        section = document.section(path.name)
        assert section is not None and parse_faces(section.get("faces") or "")

    _menu_bar, _menu, _fejlec, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureResetFaces"
    )
    _kattints(qt_app, item, modifiers)
    assert _varj(
        qt_app,
        lambda: _objektum(window, "resetFacesConfirmDialog").property("visible")
        is True,
    )
    viewer = _objektum(window, "photoViewer")
    revision_before = viewer.property("facesEditRevision")
    _kattints(qt_app, _objektum(window, "resetFacesConfirmButton"))

    assert _varj(
        qt_app,
        lambda: viewer.property("facesEditRevision") > revision_before,
    ), "az arc-réteg nem frissült a megerősített művelet után"
    assert _varj(
        qt_app,
        lambda: _objektum(window, "resetFacesConfirmDialog").property("visible")
        is False,
    )
    for path in (first, other):
        document = load_document(path.parent / ".picasa.ini")
        section = document.section(path.name)
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            assert section is None or section.get("faces") is None
            assert section is None or section.get("facedata") is None
        else:
            assert section is not None
            faces = parse_faces(section.get("faces") or "")
            assert faces and all(face.contact_id == "0" for face in faces)

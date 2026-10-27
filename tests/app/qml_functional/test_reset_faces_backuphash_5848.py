"""#5848: a sima Reset Faces a faces törlésekor backuphash-t is ír."""

from __future__ import annotations

from pathlib import Path

import cv2
import pytest
from PySide6.QtQml import QQmlExpression, qmlContext

from picasapy.app.faces_helper import FacesHelper
from picasapy.ini import load_document, update_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _kijeloles,
    _magassag,
    _nyisd_meg_felso_menut,
    _objektum,
    _varj,
)
from tests.app.test_face_scan_controller import _FakeDetector


def _keszit_valodi_portret(library: Path) -> None:
    """A műszaki próbaportréból készít tiszta, valódi tesztfotót."""
    source = Path(__file__).resolve().parents[2] / "fixtures" / "face_type_a_name_reference_en38.png"
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    assert image is not None, f"A tesztportré nem olvasható: {source}"
    portrait = image[138:572, 96:444]
    assert portrait.size > 0
    assert cv2.imwrite(str(library / "portre_1_ff.jpg"), portrait)


@pytest.fixture
def qml_app_portrettel(qt_app, tmp_path, request):
    """Teljes QML-app valódi portréfotóval és a valódi bélyegkép-szolgáltatóval."""
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszit_valodi_portret,
        belyegkep_meret=220,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _elokeszit(qml_app_portrettel, qt_app, height_offset: int, *, faces: bool):
    window, controller, engine = qml_app_portrettel
    _magassag(window, height_offset)
    record = controller.photos.photos[0]
    photo = Path(record.folder_path) / record.name
    assert photo.name == "portre_1_ff.jpg"
    face_scan = engine.rootContext().contextProperty("faceScanController")
    face_scan._detector = _FakeDetector()

    ini_path = photo.parent / ".picasa.ini"
    helper = FacesHelper()
    if faces:
        assert helper.addFace(str(photo), 0.1, 0.2, 0.4, 0.6, "Ada")

    update_document(
        ini_path,
        lambda document: document.with_value(photo.name, "caption", "marad"),
        backup=False,
    )
    before = load_document(ini_path).section(photo.name)
    assert before is not None
    assert bool(before.get("faces")) is faces
    assert before.get("backuphash") is None

    row = controller.photos.rowOfPath(str(photo))
    assert row >= 0
    _kijeloles(window, qt_app, [row])
    return window, controller, engine, photo, ini_path, row


def _kattints_resetre(qt_app, window):
    _menu_bar, _menu, _header, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureResetFaces"
    )
    _kattints(qt_app, item)


def _bizonyit_backuphash_es_torolt_faces(qt_app, window, photo, ini_path):
    assert _varj(
        qt_app,
        lambda: (
            (section := load_document(ini_path).section(photo.name)) is not None
            and section.get("backuphash") is not None
            and section.get("faces") is None
        ),
    ), "a Reset Faces után nem jelent meg a backuphash vagy megmaradt a faces="

    section = load_document(ini_path).section(photo.name)
    assert section is not None
    value = section.get("backuphash")
    assert value is not None and value.isdecimal()
    assert 0 <= int(value) <= 0xFFFF
    assert section.get("caption") == "marad"
    dialog = _objektum(window, "resetFacesConfirmDialog")
    assert dialog is None or dialog.property("visible") is False


def _valodi_belyegkep_kesz(window) -> bool:
    def walk(item):
        for child in item.childItems():
            yield child
            yield from walk(child)

    for item in walk(window.contentItem()):
        if item.objectName() != "thumbImage" or not item.property("source"):
            continue
        expression = QQmlExpression(
            qmlContext(item), item, "status === Image.Ready"
        )
        value, error = expression.evaluate()
        if not error and value:
            return True
    return False


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_picture_menu_simple_reset_removes_faces_and_writes_backuphash(
    qml_app_portrettel, qt_app, height_offset
):
    window, _controller, _engine, photo, ini_path, _row = _elokeszit(
        qml_app_portrettel, qt_app, height_offset, faces=True
    )

    _kattints_resetre(qt_app, window)
    _bizonyit_backuphash_es_torolt_faces(qt_app, window, photo, ini_path)

    if height_offset == 0:
        assert _varj(
            qt_app, lambda: _valodi_belyegkep_kesz(window)
        ), "a kiadáskép előtt a valódi portré-bélyegkép nem töltődött be"
        output = Path(__file__).resolve().parents[3] / "scratch" / "kep-5848.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        image = window.grabWindow()
        assert not image.isNull()
        assert image.save(str(output)), f"A kiadáskép nem írható: {output}"


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_picture_menu_simple_reset_writes_backuphash_without_faces_key(
    qml_app_portrettel, qt_app, height_offset
):
    window, _controller, _engine, photo, ini_path, _row = _elokeszit(
        qml_app_portrettel, qt_app, height_offset, faces=False
    )
    assert load_document(ini_path).section(photo.name).get("faces") is None

    _kattints_resetre(qt_app, window)
    _bizonyit_backuphash_es_torolt_faces(qt_app, window, photo, ini_path)

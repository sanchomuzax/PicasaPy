"""A Név nélküliek nézetének törzse az eredeti szürke hátterével (#5352).

Az eredeti Picasa 3.9 képernyőképén (picasa-colab-jobs job-208; `.eredeti/
j1_csoportositott.png`, `j4_ignored_nezet.png`) a fejléc sávja (#eaeaea) alatti
törzs - az utasítás-sor, a csempék és a csempék közti rés - #e2e2e2. Nálunk a
törzs a tartalompanel fehérjét mutatta.

Lefedve, a renderelt ablakképen mérve:
- csoportosított, kibontott és mellőzött nézetben a törzs és a kártya
  fehér kerete (alul, jobbra) #e2e2e2;
- a sima mappa és a személyalbum háttere, a keretükkel együtt, változatlan
  (a mai szín);
- sötét témában a törzs a mai szín marad (arról nincs felvétel).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import all_photos, group_unnamed_faces, open_index, replace_faces, store_embedding
from support.fixture_guards import qml_warning_guard
from tests.support.varakozas import var_feltetelre

_BT = Path(__file__).resolve().parents[3] / ".bt"

# Az eredeti mért értéke (job-208, a fejléc alatti törzs): #e2e2e2 = `Theme.chromeBg`.
_REF_TORZS = (226, 226, 226)
# A mai szín, amelyet nem szabad elrontani: a tartalompanel (`contentPanel`),
# világosban #ffffff, sötétben #2e2e2e.
_MAI_FEHER = (255, 255, 255)
_MAI_SOTET = (46, 46, 46)
_TOLERANCIA = 2


def _face(left: int, top: int, right: int, bottom: int) -> FaceDetection:
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    return FaceDetection(
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        score=0.99,
        landmarks=FaceLandmarks(
            right_eye=(center_x - 20, center_y - 20),
            left_eye=(center_x + 20, center_y - 20),
            nose=(center_x, center_y),
            mouth_right=(center_x - 12, center_y + 24),
            mouth_left=(center_x + 12, center_y + 24),
        ),
    )


def _make_photos(library: Path) -> None:
    source = Path(__file__).resolve().parents[2] / "fixtures" / "face_type_a_name_reference_en38.png"
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    assert image is not None, f"A próbaportré nem olvasható: {source}"
    portrait = image[138:572, 96:444]
    variants = (portrait, cv2.flip(portrait, 1), cv2.convertScaleAbs(portrait, alpha=0.92, beta=9))
    for name, variant in zip(("a.jpg", "b.jpg", "c.jpg"), variants, strict=True):
        assert cv2.imwrite(str(library / name), variant)


def _seed_six_faces(db_path: Path) -> None:
    with open_index(db_path) as conn:
        photos = all_photos(conn)
        assert len(photos) == 3
        boxes = (
            ((18, 18, 270, 300), (72, 40, 330, 370)),
            ((16, 20, 264, 310), (68, 42, 328, 372)),
            ((20, 16, 268, 302), (70, 45, 326, 368)),
        )
        for photo, photo_boxes in zip(photos, boxes, strict=True):
            replace_faces(conn, photo.id, [_face(*box) for box in photo_boxes])
        ids = [row[0] for row in conn.execute("SELECT id FROM face ORDER BY id")]
        assert len(ids) == 6
        for index, face_id in enumerate(ids):
            embedding = np.zeros(128, dtype=np.float32)
            embedding[index] = 1.0
            store_embedding(conn, face_id, embedding)
        assert group_unnamed_faces(conn) == 6
        conn.commit()


def _arc_azonositok(db_path: Path) -> list[int]:
    with open_index(db_path) as conn:
        return [row[0] for row in conn.execute("SELECT id FROM face ORDER BY id")]


@pytest.fixture
def qml_app_5352(qt_app, tmp_path, monkeypatch, request):
    isolated_home = tmp_path / "home"
    for variable, folder in (
        ("HOME", isolated_home),
        ("XDG_CONFIG_HOME", isolated_home / ".config"),
        ("XDG_DATA_HOME", isolated_home / ".local" / "share"),
        ("XDG_CACHE_HOME", isolated_home / ".cache"),
        ("XDG_STATE_HOME", isolated_home / ".local" / "state"),
    ):
        folder.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(variable, str(folder))

    spec = importlib.util.spec_from_file_location(
        "picasapy_qml_functional_builder_5352", Path(__file__).with_name("conftest.py")
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    guard = qml_warning_guard()
    next(guard)
    try:
        yield from builder._build_qml_app(
            qt_app,
            tmp_path,
            kepeket_keszit=_make_photos,
            belyegkep_meret=220,
            valodi_belyegkep=True,
            keep_modul=request.module,
        )
    finally:
        try:
            next(guard)
        except StopIteration:
            pass


def _find_item(root, object_name: str):
    found = root.findChild(QQuickItem, object_name)
    if found is not None:
        return found

    def walk(item):
        for child in item.childItems():
            if child.objectName() == object_name:
                return child
            nested = walk(child)
            if nested is not None:
                return nested
        return None

    return walk(root.contentItem())


def _click(window, qt_app, item) -> None:
    assert item is not None, "A kattintandó felületi elem hiányzik."
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _scene_xy(item) -> tuple[int, int]:
    point = item.mapToScene(QPointF(0, 0))
    return round(point.x()), round(point.y())


def _rgb(image, x: int, y: int) -> tuple[int, int, int]:
    color = image.pixelColor(x, y)
    return color.red(), color.green(), color.blue()


def _kozel(szin: tuple[int, int, int], cel: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= _TOLERANCIA for a, b in zip(szin, cel, strict=True))


def _kepkocka(window, qt_app, nev: str):
    qt_app.processEvents()
    image = window.grabWindow()
    assert not image.isNull()
    _BT.mkdir(parents=True, exist_ok=True)
    assert image.save(str(_BT / nev))
    return image


def _nevnelkuliek_megnyitasa(window, qt_app, engine, controller):
    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(Path(controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)

    folder_pane = _find_item(window, "folderPane")
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert var_feltetelre(qt_app, lambda: unnamed_row.width() > 0, 3.0)
    _click(window, qt_app, unnamed_row)
    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(qt_app, lambda: view.property("visible") is True, 3.0)

    welcome = window.findChild(QObject, "unnamedWelcomeDialog")
    assert var_feltetelre(qt_app, lambda: welcome.property("visible") is True, 3.0)
    _click(window, qt_app, _find_item(window, "unnamedWelcomeCloseButton"))
    assert var_feltetelre(qt_app, lambda: welcome.property("visible") is False, 3.0)
    return view


def _fejlec_alatti_pont(window) -> tuple[int, int]:
    """A törzs egy pontja a fejléc sávja alatt, a nézet jobb szélénél."""
    band = _find_item(window, "unnamedHeaderBandFill")
    view = _find_item(window, "unnamedFacesView")
    _, band_y = _scene_xy(band)
    view_x, _ = _scene_xy(view)
    return round(view_x + view.width() - 60), round(band_y + band.height() + 4)


def _csempek_kozti_pont(csempe, cella: int) -> tuple[int, int]:
    """A csempe jobb széle és a cella közepe közti rés: a csempék közti törzs."""
    x, y = _scene_xy(csempe)
    return (
        round(x + csempe.width() + (cella - csempe.width()) // 2),
        round(y + csempe.height() // 2),
    )


def _keret_pontjai(window) -> dict[str, tuple[int, int]]:
    """A tartalompanel kerete a rács körül: alul a rács alja és a kártya széle
    közt, jobbra a rács széle és a fiók-fogó előtti sáv közt.

    A rács (`column`) a kártya (`panel`) belső margójában van, így a keret a
    két geometria közti rés. Mindkét nézetben (a Név nélküliekben és a sima
    mappában is) ugyanott van, a látható elemtől függetlenül.
    """
    column = _find_item(window, "unnamedFacesView").parentItem()
    panel = column.parentItem()
    column_x, column_y = _scene_xy(column)
    panel_x, panel_y = _scene_xy(panel)
    return {
        "az alsó keretben": (
            round(column_x + column.width() / 2),
            round((column_y + column.height() + panel_y + panel.height()) / 2),
        ),
        "a jobb keretben": (
            round((column_x + column.width() + panel_x + panel.width()) / 2),
            round(column_y + column.height() / 2),
        ),
    }


def _keret_merese(window, image) -> dict[str, tuple[int, int, int]]:
    return {hely: _rgb(image, *pont) for hely, pont in _keret_pontjai(window).items()}


def _torzs_merese(window, image, csempe, cella: int) -> dict[str, tuple[int, int, int]]:
    return {
        "a fejléc alatt": _rgb(image, *_fejlec_alatti_pont(window)),
        "a csempék között": _rgb(image, *_csempek_kozti_pont(csempe, cella)),
        **_keret_merese(window, image),
    }


def _torzs_ellenorzes(szinek, reference, nezet: str) -> None:
    for hely, szin in szinek.items():
        assert _kozel(szin, reference), (
            f"A {nezet} nézetben {hely} a szín {szin}, az eredeti {reference}."
        )


def _tartalompanel_sarok_pont(window) -> tuple[int, int]:
    """Egy pont a tartalompanel jobb alsó sarka közelében: üres terület a rácson."""
    view = _find_item(window, "unnamedFacesView")
    panel = view.parentItem().parentItem()
    x, y = _scene_xy(panel)
    return round(x + panel.width() - 60), round(y + panel.height() - 60)


def test_csoportositott_nezet_torzse_szurke(qml_app_5352, qt_app):
    window, controller, engine = qml_app_5352
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)

    image = _kepkocka(window, qt_app, "kep_5352.png")
    szinek = _torzs_merese(window, image, _find_item(window, "faceTile_1"), cella=194)
    _torzs_ellenorzes(szinek, _REF_TORZS, "csoportosított")


def test_kibontott_nezet_torzse_szurke(qml_app_5352, qt_app):
    window, controller, engine = qml_app_5352
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    view = _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)
    _click(window, qt_app, _find_item(window, "clusterToggleButton"))
    assert var_feltetelre(qt_app, lambda: view.property("grouped") is False, 3.0)

    image = _kepkocka(window, qt_app, "kep_5352_kibontott.png")
    szinek = _torzs_merese(window, image, _find_item(window, "faceTile_1"), cella=162)
    _torzs_ellenorzes(szinek, _REF_TORZS, "kibontott")


def test_mellozott_nezet_torzse_szurke(qml_app_5352, qt_app):
    window, controller, engine = qml_app_5352
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    face_scan = engine.rootContext().contextProperty("faceScanController")
    view = _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)
    face_id = _arc_azonositok(Path(controller._db_path))[0]
    assert face_scan.ignoreFaces([face_id]) == 1
    view.setProperty("hasIgnoredFaces", True)
    _click(window, qt_app, _find_item(window, "unknownfaceheaderpanel/showignored"))
    assert var_feltetelre(qt_app, lambda: view.property("ignoredMode") is True, 3.0)

    kep_nev = f"ignoredFaceImage_{face_id}"
    assert var_feltetelre(qt_app, lambda: _find_item(window, kep_nev) is not None, 3.0)
    image = _kepkocka(window, qt_app, "kep_5352_mellozott.png")
    csempe = _find_item(window, kep_nev).parentItem()
    szinek = _torzs_merese(window, image, csempe, cella=194)
    _torzs_ellenorzes(szinek, _REF_TORZS, "mellőzött")


def test_sima_mappa_hattere_nem_valtozik(qml_app_5352, qt_app):
    window, _controller, _engine = qml_app_5352
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    image = _kepkocka(window, qt_app, "kep_5352_mappa.png")
    szin = _rgb(image, *_tartalompanel_sarok_pont(window))
    assert _kozel(szin, _MAI_FEHER), f"A sima mappa háttere {szin}, a mai szín {_MAI_FEHER}."
    for hely, keret_szin in _keret_merese(window, image).items():
        assert _kozel(keret_szin, _MAI_FEHER), (
            f"A sima mappa háttere {hely} {keret_szin}, a mai szín {_MAI_FEHER}."
        )


def test_szemelyalbum_hattere_nem_valtozik(qml_app_5352, qt_app):
    window, controller, engine = qml_app_5352
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    db_path = Path(controller._db_path)
    _seed_six_faces(db_path)
    face_ids = _arc_azonositok(db_path)
    assert face_scan.assignNameToFaces(face_ids[:2], "Teszt Elek")
    controller.refreshCollections()
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 4, 3.0)

    folder_pane = _find_item(window, "folderPane")
    folder_pane.setProperty("peopleCollapsed", False)
    assert var_feltetelre(
        qt_app, lambda: _find_item(window, "personItem_Teszt Elek") is not None, 3.0
    )
    _click(window, qt_app, _find_item(window, "personItem_Teszt Elek"))
    assert var_feltetelre(qt_app, lambda: window.property("unnamedFacesOpen") is False, 3.0)

    image = _kepkocka(window, qt_app, "kep_5352_szemely.png")
    szin = _rgb(image, *_tartalompanel_sarok_pont(window))
    assert _kozel(szin, _MAI_FEHER), f"A személyalbum háttere {szin}, a mai szín {_MAI_FEHER}."
    for hely, keret_szin in _keret_merese(window, image).items():
        assert _kozel(keret_szin, _MAI_FEHER), (
            f"A személyalbum háttere {hely} {keret_szin}, a mai szín {_MAI_FEHER}."
        )


def test_sotet_temaban_a_torzs_a_mai_szin_marad(qml_app_5352, qt_app):
    window, controller, engine = qml_app_5352
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    controller.setDarkTheme(True)
    assert var_feltetelre(qt_app, lambda: controller.darkTheme is True, 3.0)
    _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)

    image = _kepkocka(window, qt_app, "kep_5352_sotet.png")
    szinek = _torzs_merese(window, image, _find_item(window, "faceTile_1"), cella=194)
    _torzs_ellenorzes(szinek, _MAI_SOTET, "csoportosított, sötét témájú")

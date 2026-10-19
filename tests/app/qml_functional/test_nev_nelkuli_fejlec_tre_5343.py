"""A Név nélküliek fejlécének címe, névmezője és háttere az eredeti TRE szerint (#5343)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import all_photos, group_unnamed_faces, open_index, replace_faces, store_embedding
from support.fixture_guards import qml_warning_guard
from tests.support.varakozas import var_feltetelre

_BT = Path(__file__).resolve().parents[3] / ".bt"


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


@pytest.fixture
def qml_app_5343(qt_app, tmp_path, monkeypatch, request):
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
        "picasapy_qml_functional_builder_5343", Path(__file__).with_name("conftest.py")
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


def _bbox(image, x0: int, y0: int, x1: int, y1: int, pred):
    """A `pred(r, g, b)` igaz pixelek befoglaló téglalapja (l, t, r, b), vagy None."""
    xs: list[int] = []
    ys: list[int] = []
    for y in range(y0, y1):
        for x in range(x0, x1):
            color = image.pixelColor(x, y)
            if pred(color.red(), color.green(), color.blue()):
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _rgb(image, x: int, y: int) -> tuple[int, int, int]:
    color = image.pixelColor(x, y)
    return color.red(), color.green(), color.blue()


# Az eredeti Picasa 3.9 képernyőképeiből mért értékek (1280×1024, `.eredeti/`).
# Vízszintes és függőleges távolságok az ikon látható szélétől/tetejétől.
_REF_CIM_MAGASSAG = 21          # j1_csoportositott.png: y 95..115
_REF_CIM_FELSO = 10             # cím teteje - ikon látható teteje (95 - 85)
_REF_CIM_BAL = 41               # cím bal széle - ikon bal széle (297 - 256)
_REF_MEZO_SZELESSEG = 163       # j1_kibontott.png: x 983..1145
_REF_SAV_BAL_IKONTOL = -12      # sáv bal széle - ikon bal széle (244 - 256)
_REF_SAV_FELSO_IKONTOL = -7     # sáv teteje - ikon eleme teteje (77 - 84)
_REF_SAV_MAGASSAG = 82          # sáv: y 77..158
_REF_SAV_SZIN = (234, 234, 234)  # #eaeaea
_REF_UTASITAS_FELSO = 85        # felirat teteje - ikon teteje (170 - 85)
_REF_RACS_FELSO = 109           # első csempe teteje - ikon teteje (194 - 85)
_TOLERANCIA = 2


def _ikon_latszo_teteje_es_bal(image, icon_x: int, icon_y: int) -> tuple[int, int]:
    box = _bbox(
        image, icon_x - 4, icon_y - 4, icon_x + 36, icon_y + 40,
        lambda r, g, b: r + g + b < 600,
    )
    assert box is not None, "Az ikon nem látszik a képkockán."
    return box[1], box[0]


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


def _kepkocka(window, qt_app, nev: str):
    qt_app.processEvents()
    image = window.grabWindow()
    assert not image.isNull()
    _BT.mkdir(parents=True, exist_ok=True)
    assert image.save(str(_BT / nev))
    return image


def _cim_merese(image, window) -> dict:
    icon = _find_item(window, "unnamedTitleIcon")
    title = _find_item(window, "unnamedAlbumTitle")
    icon_x, icon_y = _scene_xy(icon)
    title_x, title_y = _scene_xy(title)
    glyphs = _bbox(
        image, title_x, title_y - 4, title_x + 240, title_y + 30,
        lambda r, g, b: r + g + b < 640,
    )
    assert glyphs is not None, "A cím betűi nem látszanak a képkockán."
    icon_top, icon_left = _ikon_latszo_teteje_es_bal(image, icon_x, icon_y)
    return {
        "magassag": glyphs[3] - glyphs[1] + 1,
        "felso": glyphs[1] - icon_top,
        "bal": glyphs[0] - icon_left,
        "betumeret": title.property("font").pixelSize(),
        "csalad": title.property("font").family(),
    }


def test_cim_betukepe_es_helyzete_az_eredeti_szerint(qml_app_5343, qt_app):
    window, controller, engine = qml_app_5343
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    view = _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)

    grouped = _cim_merese(_kepkocka(window, qt_app, "kep_5343_csoportositott.png"), window)
    assert grouped["betumeret"] == 24, f"A cím betűmérete {grouped['betumeret']} px, az eredeti 24."
    assert grouped["csalad"] == "Georgia"
    assert abs(grouped["magassag"] - _REF_CIM_MAGASSAG) <= _TOLERANCIA, grouped
    assert abs(grouped["felso"] - _REF_CIM_FELSO) <= _TOLERANCIA, grouped
    assert abs(grouped["bal"] - _REF_CIM_BAL) <= _TOLERANCIA, grouped

    _click(window, qt_app, _find_item(window, "clusterToggleButton"))
    assert var_feltetelre(qt_app, lambda: view.property("grouped") is False, 3.0)
    expanded = _cim_merese(_kepkocka(window, qt_app, "kep_5343_kibontott.png"), window)
    assert abs(expanded["magassag"] - _REF_CIM_MAGASSAG) <= _TOLERANCIA, expanded
    assert abs(expanded["felso"] - _REF_CIM_FELSO) <= _TOLERANCIA, expanded
    assert abs(expanded["bal"] - _REF_CIM_BAL) <= _TOLERANCIA, expanded

    view.setProperty("hasIgnoredFaces", True)
    _click(window, qt_app, _find_item(window, "unknownfaceheaderpanel/showignored"))
    assert var_feltetelre(qt_app, lambda: view.property("ignoredMode") is True, 3.0)
    ignored = _cim_merese(_kepkocka(window, qt_app, "kep_5343_mellozott.png"), window)
    assert ignored["betumeret"] == 24
    assert abs(ignored["magassag"] - _REF_CIM_MAGASSAG) <= _TOLERANCIA, ignored
    assert abs(ignored["felso"] - _REF_CIM_FELSO) <= _TOLERANCIA, ignored


def _tooltip_szoveg(engine, item) -> str:
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    readonly property string tipText: String(targetItem.ToolTip.text)
}""",
        QUrl(),
    )
    assert komponens.isReady(), komponens.errors()
    probe = komponens.createWithInitialProperties({"targetItem": item})
    assert probe is not None, komponens.errors()
    text = probe.property("tipText")
    probe.deleteLater()
    return text


def test_nevmezo_merete_es_sugoja_az_eredeti_szerint(qml_app_5343, qt_app):
    window, controller, engine = qml_app_5343
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    view = _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)
    _click(window, qt_app, _find_item(window, "clusterToggleButton"))
    assert var_feltetelre(qt_app, lambda: view.property("grouped") is False, 3.0)

    field = _find_item(window, "unnamedNameField")
    assert field.property("width") == _REF_MEZO_SZELESSEG, (
        f"A névmező {field.property('width')} px, az eredeti {_REF_MEZO_SZELESSEG}."
    )
    assert field.property("height") == 20

    tooltip = _tooltip_szoveg(engine, field)
    assert tooltip == "Assign a name to all of the selected faces", tooltip


def test_fejlec_savja_es_helye_az_eredeti_szerint(qml_app_5343, qt_app):
    window, controller, engine = qml_app_5343
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)

    band = _find_item(window, "unnamedHeaderBandFill")
    assert band is not None, "A fejléc háttérsávja hiányzik."
    icon = _find_item(window, "unnamedTitleIcon")
    icon_x, icon_y = _scene_xy(icon)
    band_x, band_y = _scene_xy(band)
    assert band.property("height") == _REF_SAV_MAGASSAG
    assert band_x - icon_x == _REF_SAV_BAL_IKONTOL
    assert abs(band_y - icon_y - _REF_SAV_FELSO_IKONTOL) <= _TOLERANCIA
    assert band.property("color").name() == "#eaeaea"

    image = _kepkocka(window, qt_app, "kep_5343.png")
    assert _rgb(image, icon_x + 150, band_y + 3) == _REF_SAV_SZIN
    assert _rgb(image, icon_x + 150, band_y + _REF_SAV_MAGASSAG - 1) == _REF_SAV_SZIN
    assert _rgb(image, icon_x + 150, band_y + _REF_SAV_MAGASSAG) != _REF_SAV_SZIN


def test_fejlec_utasitasa_es_racsa_az_eredeti_szerint(qml_app_5343, qt_app):
    window, controller, engine = qml_app_5343
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()
    view = _nevnelkuliek_megnyitasa(window, qt_app, engine, controller)
    for kibontott in (False, True):
        if kibontott:
            _click(window, qt_app, _find_item(window, "clusterToggleButton"))
            assert var_feltetelre(qt_app, lambda: view.property("grouped") is False, 3.0)
        image = _kepkocka(window, qt_app, f"kep_5343_utasitas_{'kibontott' if kibontott else 'csoportositott'}.png")
        icon = _find_item(window, "unnamedTitleIcon")
        icon_x, icon_y = _scene_xy(icon)
        icon_top, _ = _ikon_latszo_teteje_es_bal(image, icon_x, icon_y)
        band = _find_item(window, "unnamedHeaderBandFill")
        _, band_y = _scene_xy(band)
        instruction = _find_item(window, "unnamedInstructions")
        instruction_x, instruction_y = _scene_xy(instruction)
        glyphs = _bbox(
            image, instruction_x, instruction_y - 2, instruction_x + 420, instruction_y + 20,
            lambda r, g, b: r + g + b < 500,
        )
        assert glyphs is not None, "A fejléc-utasítás nem látszik."
        assert abs(glyphs[1] - icon_top - _REF_UTASITAS_FELSO) <= _TOLERANCIA, (kibontott, glyphs[1] - icon_top)
        assert glyphs[1] > band_y + band.height(), "A fejléc-utasítás a sáv alá kerül."
        _, tile_y = _scene_xy(_find_item(window, "faceTile_1"))
        assert abs(tile_y - icon_top - _REF_RACS_FELSO) <= _TOLERANCIA, (kibontott, tile_y - icon_top)

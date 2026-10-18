"""#5341: a bal sáv People-csoportjának fejléc-darabszáma a LÁTHATÓ sorokat számolja.

Az eredeti Picasa képei (picasa-colab-jobs job-210, 13. és 16. kép; job-213, 29. kép):
- mellőzés után a normál nézetben csak az „Unnamed (5)” sor látszik, a fejléc
  „People (1)” (13. kép);
- mellőzött nézetben a People-csoportban csak a mellőzött sor látszik
  („Ignored (1)”), a Név nélküliek sora helyette nincs; a fejléc „People (1)”;
- személyalbumnál a Név nélküliek és a megnevezett személy sora látszik;
  a fejléc „People (2)”.

Ebből a szabály: a fejléc darabszáma a People-csoport látható sorainak száma.

Lefedve, VALÓDI kattintásokkal:
- mellőzés után a normál nézetben csak a Név nélküliek sora látszik, a fejléc
  „People (1)”;
- a „Show ignored faces” után a Név nélküliek sora eltűnik, a mellőzött sor
  veszi át a helyét, és a fejléc „People (1)”;
- egy megnevezett személy (két arc) és a négy névtelen után a személyalbum
  megnyitásakor a fejléc „People (2)”.

A mellőzött sor felirata az eredeti `CThumbDB::ignorefacealbum` szövege: „Ignored (N)”.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index
from support.fixture_guards import qml_warning_guard
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (
    _find_item,
    _find_object,
    _make_portrait_photos,
    _save_window,
    _seed_six_faces,
)
from tests.support.varakozas import var_feltetelre

_CSOPORT_SOROK = ("unnamedFacesItem", "ignoredFacesItem")


@pytest.fixture
def qml_app_5341(qt_app, tmp_path, monkeypatch, request):
    """Teljes app, valódi portré-bélyegképekkel és izolált felhasználói profillal."""
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

    warning_guard = qml_warning_guard()
    next(warning_guard)
    try:
        yield from _build_qml_app(
            qt_app,
            tmp_path,
            kepeket_keszit=_make_portrait_photos,
            belyegkep_meret=220,
            valodi_belyegkep=True,
            keep_modul=request.module,
        )
    finally:
        try:
            next(warning_guard)
        except StopIteration:
            pass


def _bejar(item):
    """Az elem összes leszármazottja, mélységi sorrendben."""
    for child in item.childItems():
        yield child
        yield from _bejar(child)


def _klikk(window, qt_app, item) -> None:
    """Valódi bal egérgomb-kattintás az elem közepén."""
    assert item is not None, "A kattintandó felületi elem hiányzik."
    assert item.property("enabled") is not False
    assert item.width() > 0 and item.height() > 0
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _latszo_elem(qt_app, window, nev: str):
    """Az első LÁTSZÓ elem a nevével."""
    for _ in range(150):
        qt_app.processEvents()
        for item in _bejar(window.contentItem()):
            if item.objectName() == nev and item.isVisible() and item.width() > 0:
                return item
        QTest.qWait(20)
    raise AssertionError(f"{nev} nem látszik")


def _latszo_gomb(qt_app, window, felirat: str):
    """A látszó gomb felirat szerint."""
    for _ in range(150):
        qt_app.processEvents()
        for item in _bejar(window.contentItem()):
            if (
                item.property("text") == felirat
                and item.isVisible()
                and item.width() > 0
                and item.metaObject().indexOfSignal("clicked()") >= 0
            ):
                return item
        QTest.qWait(20)
    raise AssertionError(f"a(z) {felirat!r} gomb nem látszik")


def _latszo_people_sorok(window) -> list[str]:
    """A People-csoport látszó sorainak objectName-jei, felülről lefelé."""
    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    return [
        item.objectName()
        for item in _bejar(folder_pane)
        if item.isVisible()
        and (
            item.objectName() in _CSOPORT_SOROK
            or item.objectName().startswith("personItem_")
        )
    ]


def _people_fejlec(window) -> str:
    header = _find_item(window, "peopleHeader")
    assert header is not None
    return header.property("text")


def test_mellozes_utan_a_fejlec_a_latszo_sorokat_szamolja(qml_app_5341, qt_app):
    window, controller, engine = qml_app_5341
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(Path(controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    _klikk(window, qt_app, _latszo_elem(qt_app, window, "unnamedFacesItem"))

    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app, lambda: view is not None and view.property("visible") is True, 3.0
    )
    _klikk(window, qt_app, _latszo_elem(qt_app, window, "unnamedWelcomeCloseButton"))

    # Valódi kattintás az első arc „x”-én, majd a megerősítő „Ignore Person”.
    _klikk(window, qt_app, _latszo_elem(qt_app, window, "faceIgnoreX_1"))
    confirm = _find_object(window, "ignoreFacesDialog")
    assert confirm is not None
    assert var_feltetelre(qt_app, lambda: confirm.property("visible") is True, 3.0)
    _klikk(window, qt_app, _latszo_gomb(qt_app, window, "Ignore Person"))
    assert var_feltetelre(qt_app, lambda: confirm.property("visible") is False, 3.0)
    assert face_scan.unnamedCount == 5

    # Normál nézet: csak a Név nélküliek sora látszik (job-210, 13. kép).
    ignored_label = _find_item(window, "ignoredFacesLabel")
    assert var_feltetelre(
        qt_app,
        lambda: ignored_label is not None
        and ignored_label.property("text") == "Ignored (1)",
        3.0,
    )
    assert _latszo_people_sorok(window) == ["unnamedFacesItem"]
    assert _people_fejlec(window) == "People (1)"


def test_mellozott_nezetben_a_fejlec_egy_sort_szamol(qml_app_5341, qt_app):
    window, controller, engine = qml_app_5341
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(Path(controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    _klikk(window, qt_app, _latszo_elem(qt_app, window, "unnamedFacesItem"))
    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app, lambda: view is not None and view.property("visible") is True, 3.0
    )
    _klikk(window, qt_app, _latszo_elem(qt_app, window, "unnamedWelcomeCloseButton"))

    _klikk(window, qt_app, _latszo_elem(qt_app, window, "faceIgnoreX_1"))
    confirm = _find_object(window, "ignoreFacesDialog")
    assert confirm is not None
    assert var_feltetelre(qt_app, lambda: confirm.property("visible") is True, 3.0)
    _klikk(window, qt_app, _latszo_gomb(qt_app, window, "Ignore Person"))
    assert var_feltetelre(qt_app, lambda: confirm.property("visible") is False, 3.0)
    assert face_scan.unnamedCount == 5

    # „Show ignored faces”: a mellőzött nézetben a mellőzött sor veszi át a
    # Név nélküliek helyét.
    show_ignored = _find_item(window, "unknownfaceheaderpanel/showignored")
    assert show_ignored is not None
    assert var_feltetelre(
        qt_app, lambda: show_ignored.property("enabled") is True, 3.0
    )
    _klikk(window, qt_app, show_ignored)
    assert var_feltetelre(
        qt_app, lambda: window.property("facesAlbumMode") == "ignored", 3.0
    )

    ignored_label = _find_item(window, "ignoredFacesLabel")
    assert ignored_label is not None
    assert var_feltetelre(
        qt_app,
        lambda: ignored_label.property("text") == "Ignored (1)",
        3.0,
    )
    assert _latszo_people_sorok(window) == ["ignoredFacesItem"]
    assert _people_fejlec(window) == "People (1)"
    _save_window(window, "kep_5341.png")


def test_megnevezett_szemely_utan_a_fejlec_ket_sort_szamol(qml_app_5341, qt_app):
    window, controller, engine = qml_app_5341
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    db_path = Path(controller._db_path)
    _seed_six_faces(db_path)
    with open_index(db_path) as conn:
        face_ids = [row[0] for row in conn.execute("SELECT id FROM face ORDER BY id")]
    assert face_scan.assignNameToFaces(face_ids[:2], "Teszt Elek")
    controller.refreshCollections()
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 4, 3.0)

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    assert var_feltetelre(
        qt_app,
        lambda: _find_item(window, "unnamedFacesItem") is not None,
        3.0,
    )

    # Személyalbum megnyitása valódi kattintással.
    _klikk(window, qt_app, _latszo_elem(qt_app, window, "personItem_Teszt Elek"))
    assert var_feltetelre(
        qt_app,
        lambda: window.property("facesAlbumMode") != "ignored",
        3.0,
    )

    assert _latszo_people_sorok(window) == [
        "unnamedFacesItem",
        "personItem_Teszt Elek",
    ]
    assert _people_fejlec(window) == "People (2)"

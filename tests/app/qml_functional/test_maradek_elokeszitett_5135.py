"""A #5135 előkészítést igénylő maradék vezérlői VALÓDI kattintással.

Az előző körökben kimaradt tételek: a felismert arc keretének kattintása
(`faceRegionArea_`), a „ne kérdezze újra” jelölő az Emberek-panel
figyelmen kívül hagyó párbeszédében, a térképre húzott kép Mégse gombja,
az importforrás bélyegképének kizárása, a nyomtatás előnézetének lapozása,
a film egyetlen klipje és a címdia körvonal-jelölője.

Állapot-előkészítés (arc, tmp forrásmappa, nyitott nézet) a meglévő
fixture-ökön és controlleren át történik; a TESZTELT műveletet mindenhol
valódi egérkattintás viszi. A film kimenetét a `export_movie` helyettesítő
veszi át, a nyomtatás lapgeometriáját nem írjuk át.

Lefedve:
- `faceRegionArea_0` - a felismert arc keretére kattintás megnyitja a
  névmezőt, és kijelöli az arcot;
- `peoplePanelIgnoreDontAskCheck` - a jelölő bepipálva az „Ignore Person”
  után elnyomja a további kérdezést;
- `dropGeotagCancelButton` - a térkép-húzás megerősítőjének Mégse gombja
  nem ír geotaget;
- `importSourceToggle:0` - a bélyegkép kizárása / visszavétele (tmp mappa).

A második rész (nyomtatási előnézet lapozása, `movieSoloClip`,
`titledialog/outline`) a `test_maradek_elokeszitett_5135_b.py`-ban van.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from test_helyek_terkep_drop_4583 import (
    _PROBA_TERKEP,
    _egerhuzas,
    _elem,
    _forras_kep,
)
from test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _keszits_konyvtarat,
)
from test_menu_talca_egyeb_valodi_5135_e import _import_megnyit
from test_people_panel_4573 import _click, _dialog_button
from test_people_panel_new_person_4522 import _named_item, _prepare_panel
from test_racs_vezerlok_valodi_5135 import (
    _kattints_mindenablakban,
    _vizualis,
    _vizualis_mindenablakban,
    _zar,
)

try:
    import PySide6.QtPrintSupport  # noqa: F401

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover
    _QTPRINTSUPPORT_VAN = False


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _kattint(window, qt_app, elem) -> None:
    """Valódi egérkattintás az elem aktuális ablakbeli közepén."""
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nem látszik / nulla méretű"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window() or window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _lista(value) -> list:
    if hasattr(value, "toVariant"):
        value = value.toVariant()
    return list(value or [])


def _filmet_nyit(window, qt_app):
    """A főablak Filmkészítő gombja (valódi kattintás)."""
    _kattint(window, qt_app, _elem(window, "trayMovieButton"))
    film = _elem(window, "movieDialog")
    assert _varj(qt_app, lambda: film.property("visible") is True), (
        "a Filmkészítő gomb nem nyitotta meg a párbeszédet"
    )
    return film


# ---------------------------------------------------------------------------
# 1. faceRegionArea_ - a felismert arc keretének kattintása (nézőben)
# ---------------------------------------------------------------------------


def _felismert_arc(controller) -> Path:
    """Egy felismert arcot ír az indexbe a teszt-könyvtár `a.jpg`-jéhez."""
    kep = Path(str(controller.watchedFolders[0])) / "a.jpg"
    with open_index(controller._db_path) as conn:
        foto = conn.execute(
            "SELECT id FROM photos WHERE name = ?", (kep.name,)
        ).fetchone()
        assert foto is not None, "a teszt-kép nincs az indexben"
        replace_faces(
            conn,
            int(foto["id"]),
            [
                FaceDetection(
                    left=100.0,
                    top=20.0,
                    right=200.0,
                    bottom=140.0,
                    score=0.99,
                    landmarks=FaceLandmarks(
                        right_eye=(130.0, 60.0),
                        left_eye=(170.0, 60.0),
                        nose=(150.0, 90.0),
                        mouth_right=(135.0, 115.0),
                        mouth_left=(165.0, 115.0),
                    ),
                )
            ],
        )
        conn.commit()
    return kep


class TestFelismertArc:
    def test_a_felismert_arc_keretere_kattintva_megnyilik_a_nevmezo(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        kep = _felismert_arc(controller)
        controller._reload()
        qt_app.processEvents()
        window.show()
        window.requestActivate()
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        assert viewer is not None
        sor = controller.photos.rowOfPath(str(kep))
        assert sor >= 0, "a teszt-kép nincs a rácson"
        viewer.setProperty("currentIndex", sor)
        qt_app.processEvents()

        overlay = window.findChild(QObject, "facesOverlay")
        assert overlay is not None
        # a delegált MouseArea a Repeaterben van: a vizuális fában keressük
        area = _vizualis(window, "faceRegionArea_0")
        assert _varj(qt_app, lambda: area is not None and area.isVisible()), (
            "a felismert arc keretének egérterülete nem látszik"
        )
        assert overlay.property("selectedDetectedFaceId") == -1, (
            "a próba feltétele: még nincs kijelölt felismert arc"
        )

        _kattint(window, qt_app, area)

        editor = window.findChild(QObject, "faceNameEditor")
        assert _varj(
            qt_app, lambda: editor is not None and editor.property("visible") is True
        ), "az arc keretére kattintás nem nyitotta meg a névmezőt"
        assert overlay.property("selectedDetectedFaceId") > 0, (
            "a keretre kattintás nem jelölte ki a felismert arcot"
        )


# ---------------------------------------------------------------------------
# 2. peoplePanelIgnoreDontAskCheck - „ne kérdezze újra” az Emberek-panelen
# ---------------------------------------------------------------------------


class TestEmberekIgnoralas:
    def test_a_jelolo_utan_az_ignoralas_elnyomja_a_kerdest(
        self, qml_app_valodi_belyegkep, qt_app, tmp_path
    ):
        window, _controller, panel, _lib, _photo, _row, face_ids = _prepare_panel(
            qml_app_valodi_belyegkep, qt_app, tmp_path
        )
        _w, _c, engine = qml_app_valodi_belyegkep
        bridge = engine.rootContext().contextProperty("confirmSettings")
        assert bridge is not None
        assert bridge.isSuppressed("ignoreFaces") is False, (
            "a próba feltétele: a kérdés még nincs elnyomva"
        )
        elso, masodik = face_ids[0], face_ids[1]

        ignore = _named_item(panel, f"peoplePanelIgnoreX_{elso}")
        assert ignore is not None and ignore.isVisible()
        _click(window, ignore)

        jelolo = window.findChild(QObject, "peoplePanelIgnoreDontAskCheck")
        assert jelolo is not None
        _click(window, jelolo)
        assert _varj(qt_app, lambda: jelolo.property("checked") is True), (
            "a „ne kérdezze újra” jelölőre kattintás nem jelölte be"
        )
        _click(window, _dialog_button(window, qt_app, "Ignore Person"))

        assert _varj(qt_app, lambda: bridge.isSuppressed("ignoreFaces") is True), (
            "a bejelölt „ne kérdezze újra” nem mentette el az elnyomást"
        )

        # az elnyomás után a következő ignorálás már nem nyit megerősítőt
        ignore2 = _named_item(panel, f"peoplePanelIgnoreX_{masodik}")
        assert ignore2 is not None and ignore2.isVisible()
        _click(window, ignore2)
        dialog = window.findChild(QObject, "peoplePanelIgnoreDialog")
        assert dialog is None or dialog.property("visible") is not True, (
            "az elnyomás után is megerősítőt kért az ignorálás"
        )


# ---------------------------------------------------------------------------
# 3. dropGeotagCancelButton - a térkép-húzás megerősítőjének Mégse gombja
# ---------------------------------------------------------------------------


class TestGeotagMegse:
    def test_a_mégse_gomb_nem_ir_geotaget(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        loader = window.findChild(QObject, "placesMapLoader")
        assert loader is not None
        probe_map = tmp_path / "probaterkep.qml"
        probe_map.write_text(_PROBA_TERKEP, encoding="utf-8")
        loader.setProperty("source", QUrl.fromLocalFile(str(probe_map)))
        window.setProperty("activeDrawerTab", "places")
        assert _varj(qt_app, lambda: _elem(window, "placesPanel") is not None
                     and _elem(window, "placesPanel").property("visible") is True)
        drop_area = _elem(window, "placesMapDropArea")
        assert _varj(qt_app, lambda: drop_area is not None
                     and drop_area.width() > 0 and drop_area.height() > 0)
        forras = _forras_kep(window)
        assert forras is not None, "a kijelölt rácskép egérterülete hiányzik"

        _egerhuzas(window, qt_app, forras, drop_area, QPoint(24, -16))

        dialog = _elem(window, "dropGeotagConfirm")
        assert _varj(qt_app, lambda: dialog is not None
                     and dialog.property("visible") is True), (
            "a térképre dobás nem nyitotta meg a megerősítést"
        )
        megse = _elem(window, "dropGeotagCancelButton")
        assert megse is not None
        _kattint(window, qt_app, megse)

        assert _varj(qt_app, lambda: dialog.property("visible") is not True), (
            "a Mégse gomb nem zárta be a megerősítést"
        )
        ini = Path(controller.photos.filePathAt(0)).parent / ".picasa.ini"
        szoveg = ini.read_text(encoding="utf-8") if ini.exists() else ""
        assert "geotag=" not in szoveg, "a Mégse mégis írt geotaget"


# ---------------------------------------------------------------------------
# 4. importSourceToggle:0 - bélyegkép kizárása / visszavétele (tmp mappa)
# ---------------------------------------------------------------------------


@pytest.fixture
def import_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _forras_mappa(tmp_path: Path) -> Path:
    """Két képet tartalmazó, a könyvtáron KÍVÜLI forrásmappa."""
    forras = tmp_path / "forras"
    forras.mkdir()
    make_jpeg(forras / "elso.jpg", size=(160, 120))
    make_jpeg(forras / "masodik.jpg", size=(160, 120))
    return forras


def _szoveg_mindenablakban(nev: str) -> str | None:
    _ablak, elem = _vizualis_mindenablakban(nev)
    return None if elem is None else str(elem.property("text"))


class TestImportForrasKizaras:
    def test_a_bélyegkep_kizarasa_es_visszavetele_valodi_kattintassal(
        self, import_app, qt_app, tmp_path
    ):
        window, controller, _engine = import_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        dialog.setProperty("sourceFolder", str(_forras_mappa(tmp_path)))
        dialog.setProperty("sourceFiles", [])
        # a FolderDialog elfogadása ezt hívja: a forrás beolvasása (állapot-előkészítés)
        QMetaObject.invokeMethod(
            dialog, "scanCurrentSource", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert _varj(qt_app, lambda: _szoveg_mindenablakban("importSourceToggleLabel:0") == "Exclude"), (
            "a tmp forrás bélyegképe nem jelent meg kizárható állapotban"
        )

        _kattints_mindenablakban(qt_app, "importSourceToggle:0")

        assert _varj(qt_app, lambda: _szoveg_mindenablakban("importSourceToggleLabel:0") == "Include"), (
            "a Kizárás kattintás nem jelölte ki a bélyegképet"
        )

        _kattints_mindenablakban(qt_app, "importSourceToggle:0")

        assert _varj(
            qt_app,
            lambda: _szoveg_mindenablakban("importSourceToggleLabel:0") == "Exclude",
        ), "a Visszavétel kattintás nem vette vissza a bélyegképet"
        _zar(qt_app, dialog)

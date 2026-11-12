"""A kép helyi menüjének mért folyamatai valódi QML-kattintásokkal (#6848)."""

from __future__ import annotations

import os
from pathlib import Path

import piexif
import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from picasapy.ini import load_document
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    varj,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek,
    jobbklikk_fotón,
    kattints,
    kijelol,
    kijelolt,
    keres_vizualis,
    zar,
)


def _keszits_24_kept(lib: Path) -> None:
    mappa = lib / "fotok"
    mappa.mkdir()
    for index in range(24):
        make_jpeg(
            mappa / f"kep_{index:02d}.jpg",
            size=(80, 60),
            taken_at="2026:11:11 00:00:00",
        )


def _keszits_tulajdonsagos_kepeket(lib: Path) -> None:
    mappa = lib / "fotok"
    mappa.mkdir()
    for nev, meret in (
        ("a_nagy.jpg", (640, 480)),
        ("b_kicsi.jpg", (40, 30)),
        ("c_kozepes.jpg", (200, 150)),
    ):
        make_jpeg(mappa / nev, size=meret)
    # A Properties-panel tesztadatában legyen mérhető Unique ID is.
    unique_id_tag = 42016
    piexif.TAGS["Exif"][unique_id_tag] = {
        "name": "ImageUniqueID",
        "type": piexif.TYPES.Ascii,
    }
    kep = mappa / "a_nagy.jpg"
    exif = piexif.load(str(kep))
    exif["Exif"][unique_id_tag] = "6848-test-image-id"
    piexif.insert(piexif.dump(exif), str(kep))


@pytest.fixture
def app_24(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=_keszits_24_kept)


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(
        qt_app, tmp_path, kepeket_keszit=_keszits_tulajdonsagos_kepeket
    )


def _mappa_elokeszitese(window, qt_app, controller, darab: int) -> Path:
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    mappa = Path(str(controller.watchedFolders[0])) / "fotok"
    controller.selectFolder(str(mappa))
    assert varj(qt_app, lambda: controller.photos.rowCount() == darab), (
        f"a tesztmappa {darab} képe nem töltődött be"
    )
    return mappa


def _magassag(window, qt_app, alap: int, elteres: int) -> None:
    window.setHeight(alap + elteres)
    assert varj(qt_app, lambda: window.height() == alap + elteres), (
        f"az ablak nem vette fel a {elteres:+d} px-es magasságeltolást"
    )


def _ini_ertek(ut: Path, nev: str, kulcs: str):
    ini = ut.parent / ".picasa.ini"
    if not ini.exists():
        return None
    szakasz = load_document(ini).section(nev)
    return szakasz.get(kulcs) if szakasz is not None else None


def _mappaszam(controller, mappa: Path):
    modell = controller.folders
    for sor in range(modell.rowCount()):
        index = modell.index(sor, 0)
        if modell.data(index, modell.PathRole) == str(mappa):
            return modell.data(index, modell.CountRole)
    return None


def test_mappa_felosztasa_a_kattintott_keptol_mozgat_es_kijeloli_az_uj_mappat(
    app_24, qt_app
):
    window, controller, _engine = app_24
    source = _mappa_elokeszitese(window, qt_app, controller, 24)
    alapmagassag = window.height()
    cel = source.parent / "Untitled"

    for elteres in (-5, 0, 5):
        _magassag(window, qt_app, alapmagassag, elteres)
        kijelol(window, qt_app, [4])
        menu = jobbklikk_fotón(window, qt_app, 4)
        kattints(window, qt_app, gyerek(window, "contextMenuSplitFolder"))
        dialog = gyerek(window, "folderPropertiesDialog")
        assert varj(qt_app, lambda dialog=dialog: dialog.property("visible") is True)
        nev = gyerek(window, "folderPropertiesNameField")
        assert dialog.property("title") == "Folder Properties"
        assert nev.property("text") == "Untitled"
        assert nev.property("selectedText") == "Untitled"
        assert gyerek(window, "folderPropertiesDateField").property("visible") is True
        assert gyerek(window, "folderPropertiesUseMusic").property("checked") is False
        if elteres < 5:
            kattints(window, qt_app, gyerek(window, "folderPropertiesCancelButton"))
            assert varj(qt_app, lambda dialog=dialog: dialog.property("visible") is False)
        else:
            kattints(window, qt_app, gyerek(window, "folderPropertiesOkButton"))
            assert varj(qt_app, lambda: len(list(cel.glob("*.jpg"))) == 20)
            assert varj(qt_app, lambda: Path(controller.currentFolder) == cel)
            assert varj(qt_app, lambda: _mappaszam(controller, cel) == 20)
            assert varj(qt_app, lambda: _mappaszam(controller, source) == 4)
            assert controller.photos.rowCount() == 24
        if menu.property("visible"):
            zar(qt_app, menu)

    assert len(list(source.glob("*.jpg"))) == 4
    assert len(list(cel.glob("*.jpg"))) == 20


def test_elrejtes_ket_keppel_csokkenti_a_lathato_racs_darabszamat(app_24, qt_app):
    window, controller, _engine = app_24
    source = _mappa_elokeszitese(window, qt_app, controller, 24)
    alapmagassag = window.height()

    for alkalom, (elteres, elso_sor) in enumerate(
        zip((-5, 0, 5), (0, 2, 4), strict=True), start=1
    ):
        _magassag(window, qt_app, alapmagassag, elteres)
        kijelol(window, qt_app, [elso_sor, elso_sor + 1])
        menu = jobbklikk_fotón(window, qt_app, elso_sor)
        kattints(window, qt_app, gyerek(window, "contextMenuHide"))
        vart_darab = 24 - 2 * alkalom
        assert varj(
            qt_app, lambda vart_darab=vart_darab: controller.photos.rowCount() == vart_darab
        ), (
            "az elrejtett képek nem tűntek el a mappanézet darabszámából"
        )
        assert varj(
            qt_app, lambda vart_darab=vart_darab: _mappaszam(controller, source) == vart_darab
        ), (
            "a bal oldali mappaszám nem követte az elrejtést"
        )
        assert kijelolt(window) == []
        assert menu.property("visible") is False
        assert len(list(source.glob("*.jpg"))) == 24


def test_forgatas_jobbra_ket_kepen_mentesre_varo_allapotot_ad(app_24, qt_app):
    window, controller, _engine = app_24
    _mappa_elokeszitese(window, qt_app, controller, 24)
    alapmagassag = window.height()

    for elteres, elso_sor in zip((-5, 0, 5), (0, 2, 4), strict=True):
        _magassag(window, qt_app, alapmagassag, elteres)
        kijelol(window, qt_app, [elso_sor, elso_sor + 1])
        utvonalak = [
            Path(controller.photos.filePathAt(index))
            for index in (elso_sor, elso_sor + 1)
        ]
        menu = jobbklikk_fotón(window, qt_app, elso_sor)
        kattints(window, qt_app, gyerek(window, "contextMenuRotateRight"))
        assert varj(
            qt_app,
            lambda utvonalak=utvonalak: all(
                _ini_ertek(ut, ut.name, "rotate") == "rotate(1)" for ut in utvonalak
            ),
        ), "a Rotate Clockwise nem forgatta el a kijelölt képpárt"
        save = keres_vizualis(window, "headerSaveEditsButton")
        assert save is not None, "a mappafejléc Save gombja hiányzik"
        assert varj(qt_app, lambda save=save: save.property("enabled") is True), (
            "a forgatás után a mappafejléc Save gombja inaktív maradt"
        )
        zar(qt_app, menu)


def test_tulajdonsagok_helyi_menuje_panelt_nyit_es_escape_nem_zarja_be(
    app, qt_app
):
    window, controller, _engine = app
    source = Path(str(controller.watchedFolders[0])) / "fotok"
    elokeszit(window, qt_app, controller)
    sor = window.property("selectedIndex")
    foto_nev = controller.photos.itemAt(sor)["name"]
    controller.addKeywordToRows([sor], "AI image")
    assert varj(qt_app, lambda: controller.keywordsOfRows([sor]) == ["AI image"])
    menu = jobbklikk_fotón(window, qt_app, sor)
    kattints(window, qt_app, gyerek(window, "contextMenuProperties"))

    panel = gyerek(window, "propertiesPanel")
    assert varj(qt_app, lambda: panel.property("visible") is True)
    assert varj(qt_app, lambda: window.property("activeDrawerTab") == "properties")
    drawer = gyerek(window, "rightDrawer")
    assert varj(
        qt_app,
        lambda: drawer.property("width")
        >= drawer.property("kivantSzelesseg") - 3,
    )
    assert varj(qt_app, lambda: len(panel.property("entries")) >= 6)
    title = panel.findChild(QObject, "propertiesFileTitle")
    assert title is not None
    assert varj(
        qt_app, lambda: title.property("text") == f"Properties of {foto_nev}:"
    )
    kep = os.environ.get("PICASAPY_6848_KEP")
    if kep:
        assert panel.window().grabWindow().save(kep)
    cimkek = {
        "Location" if entry["label"] == "File Path" else
        "Tags" if entry["label"] == "Keywords" else entry["label"]
        for entry in panel.property("entries")
    }
    label_szovegek = list(cimkek)
    assert "Location" in label_szovegek
    assert "File Size" in label_szovegek
    assert "Dimensions" in label_szovegek
    assert "File Date" in label_szovegek
    assert "JPEG Quality" in label_szovegek
    assert "Tags" in label_szovegek
    assert "Unique ID" in label_szovegek

    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()
    assert window.property("activeDrawerTab") == "properties"
    assert panel.property("visible") is True
    assert source.is_dir()
    zar(qt_app, menu)

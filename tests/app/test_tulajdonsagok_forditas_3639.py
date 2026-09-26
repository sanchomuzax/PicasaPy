"""#3639: a Tulajdonságok panel magyar nyelven a hivatalos magyar feliratokat
mutatja — az ÉLES fordítási úton mérve.

A hiba: a `formatting.py` szövegei a `.ts` NÉVTELEN (`""`) kontextusában
vannak (a `pyside6-lupdate` a modulszintű `tr(...)` hívásokat oda gyűjti),
a vezérlő viszont a saját `self.tr`-jét adta át, ami `AppController`
kontextusban keres. Így magyarul a teljes panel angol maradt.

Ezért a teszt NEM saját `tr`-rel dolgozik: betölti a valódi
`picasapy_hu.qm`-et, és a vezérlő `propertiesOf`-ját hívja.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg

piexif = pytest.importorskip("piexif")

_I18N = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"


@pytest.fixture
def magyar(qt_app):
    from PySide6.QtCore import QCoreApplication, QTranslator

    translator = QTranslator()
    assert translator.load("picasapy_hu", str(_I18N)), "a .qm nem tölthető be"
    QCoreApplication.installTranslator(translator)
    yield translator
    QCoreApplication.removeTranslator(translator)


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PIL import Image
    from PySide6.QtCore import QSettings

    library = tmp_path / "kepek"
    (library / "nyaralas").mkdir(parents=True)
    make_jpeg(library / "nyaralas" / "IMG_0001.jpg", taken_at="2025:05:01 07:00:00")
    exif = piexif.dump(
        {
            "0th": {
                piexif.ImageIFD.Make: b"Canon",
                piexif.ImageIFD.Model: b"EOS 550D",
                piexif.ImageIFD.Compression: 6,
                piexif.ImageIFD.Orientation: 1,
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: b"2025:05:01 07:00:00",
                piexif.ExifIFD.WhiteBalance: 0,
                piexif.ExifIFD.ExposureProgram: 7,  # Portrait
            },
        }
    )
    Image.new("RGB", (8, 6), "red").save(
        library / "nyaralas" / "IMG_0002.jpg", "JPEG", exif=exif
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library / "nyaralas"))
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _sorok(controller, nev: str) -> dict:
    row = [p.name for p in controller.photos.photos].index(nev)
    return {e["label"]: e["value"] for e in controller.propertiesOf(row)}


def test_alap_sorok_magyarul(controller, magyar):
    """A panel első három sora és a dátum-sor a `.ts` magyar szövegével."""
    sorok = _sorok(controller, "IMG_0001.jpg")
    for felirat in ("Fájl útvonala", "Fájlméret", "Méretek", "Fényképezőgép dátuma"):
        assert felirat in sorok, (felirat, list(sorok))
    assert "File Path" not in sorok
    # a Méretek ÉRTÉKE is fordított — a „%1x%2 pixels" sablonból
    assert sorok["Méretek"].endswith("képpont")


def test_fenykepezo_sorai_es_tomorites_magyarul(controller, magyar):
    """A szomszéd sorok (fényképező, fehéregyensúly) és a #3535 tömörítés-
    felirata is magyar — a sor NEVE és az ÉRTÉKE egyaránt."""
    sorok = _sorok(controller, "IMG_0002.jpg")
    assert sorok["Fényképezőgép gyártmánya"] == "Canon"
    assert sorok["Fényképezőgép típusa"] == "EOS 550D"
    assert sorok["Fehéregyensúly"] == "Automatikus"
    assert sorok["Tömörítés"] == "JPEG (régi típusú)"
    # az átnézés lelete: ezek a felsorolt értékek angolul maradtak
    assert "Normál" in sorok.values(), sorok
    assert "Álló" in sorok.values(), sorok


def test_angolul_valtozatlan(controller):
    """Betöltött fordítás nélkül az alapszövegek maradnak (nincs regresszió)."""
    sorok = _sorok(controller, "IMG_0001.jpg")
    assert list(sorok)[:3] == ["File Path", "File Size", "Dimensions"]


def test_kor_szuro_felirata_magyarul(controller, magyar):
    """Ugyanaz a hibaosztály a szomszédban: a kor-szűrő felirata is a
    névtelen kontextusban van, a vezérlő mégis `self.tr`-rel kérte."""
    controller._age_filter_days = 3
    assert controller.ageFilterText == "Legfeljebb 3 napos képek."

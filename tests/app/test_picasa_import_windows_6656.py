"""#6656: Windowson, ugyanazon a gépen a Picasa-import útvonal-átírás nélkül működik.

A tulajdonos Windows 11-en a Picasa adatmappáját adta meg, az alapértelmezett
`Z:\\ → /` (Wine-os) leképezés pedig minden `C:\\…` útvonalat kiejtett:
„0 mappa frissült”.
"""

from pathlib import Path

import pytest

from picasapy.app import picasa_import_controller as pic
from picasapy.pmpimport import remap as remap_modul
from picasapy.app.picasa_import_controller import PicasaImportController
from picasapy.pmpimport.db3_atvetel import AtvetelJelentes
from picasapy.pmpimport.remap import PathRemapper


def test_az_azonos_lekepezes_minden_utvonalat_valtozatlanul_atenged():
    azonos = PathRemapper.azonos_lekepezes()
    assert azonos.remap(r"C:\Users\felhasznalo\Pictures\kep.jpg") == r"C:\Users\felhasznalo\Pictures\kep.jpg"
    assert azonos.remap("D:/Fotok/2009") == r"D:\Fotok\2009"


@pytest.mark.parametrize(("platform", "varhato"), [
    ("win32", r"C:\Users\felhasznalo\Pictures\kep.jpg"),
    ("linux", None),
])
def test_az_alapertelmezett_lekepezes_platformfuggo(monkeypatch, platform, varhato):
    monkeypatch.setattr(remap_modul, "_platform", lambda: platform)
    assert remap_modul.alapertelmezett_lekepezes().remap(r"C:\Users\felhasznalo\Pictures\kep.jpg") == varhato


def test_kezi_import_ures_atiro_mezokkel_a_platform_alapertelmezeset_hasznalja(qt_app, tmp_path, monkeypatch):
    monkeypatch.setattr(remap_modul, "_platform", lambda: "win32")
    db3 = tmp_path / "Picasa2"
    db3.mkdir()
    olvasasok = []

    def olvaso(konyvtar, remapper):
        olvasasok.append((Path(konyvtar), remapper.remap(r"C:\Users\felhasznalo\Pictures\kep.jpg")))
        return ("rekord",)

    controller = PicasaImportController(
        felderito=lambda: (),
        olvaso=olvaso,
        atvevo=lambda _rekordok: AtvetelJelentes(mappak=1),
    )
    hibak = []
    controller.importFailed.connect(hibak.append)
    controller.startManualImport(str(db3), "", "")
    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()

    assert hibak == []
    assert olvasasok == [(db3, r"C:\Users\felhasznalo\Pictures\kep.jpg")]


def test_kezi_import_fel_kitoltott_atiro_mezovel_hibat_ad(qt_app, tmp_path):
    controller = PicasaImportController(felderito=lambda: (), olvaso=lambda *_: (), atvevo=lambda _r: AtvetelJelentes())
    hibak = []
    controller.importFailed.connect(hibak.append)
    controller.startManualImport(str(tmp_path), r"D:\Fotok", "")
    assert hibak == [pic._MANUAL_MAPPING_REQUIRED]


def test_a_felderites_windowson_a_localappdata_picasa_mappajat_is_megtalalja(tmp_path):
    from picasapy.scanner.discovery import discover_installations

    picasa2 = tmp_path / "Google" / "Picasa2"
    (picasa2 / "db3").mkdir(parents=True)
    talalt = discover_installations(home=tmp_path / "nincs", localappdata=tmp_path,
                                    windows_old=tmp_path / "nincs-old")
    assert [t.picasa2_dir for t in talalt] == [picasa2]


def test_a_vezerlo_megadja_a_felismert_adatmappat(tmp_path):
    from types import SimpleNamespace

    controller = PicasaImportController(
        felderito=lambda: (SimpleNamespace(picasa2_dir=tmp_path / "Picasa2"),))
    assert Path(controller.detectedDataFolder()) == tmp_path / "Picasa2"
    assert PicasaImportController(felderito=lambda: ()).detectedDataFolder() == ""

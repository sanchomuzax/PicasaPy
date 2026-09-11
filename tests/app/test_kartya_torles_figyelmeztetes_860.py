"""#860: a kártyatörlés ÖSSZEÁLLÍTOTT figyelmeztetése.

Az eredeti hét `CAcquireUI::WipeCard*` darabból fűzi össze a szöveget
(`docs/specs/picasa-importalas.md`). Nálunk eddig egyetlen, három pontra
rövidített mondat állt itt — épp a lényeget hallgatta el: a darabszámot, a
nem felismert fájlokat és a záró „A MŰVELET NEM VONHATÓ VISSZA." mondatot.

Ez a legsúlyosabb adatvesztési pont az egész programban, ezért az őr a
szöveg SZERKEZETÉT méri, nem a létezését.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

from picasapy.app.wipe_card_warning import WipeCardFacts, wipe_card_warning

_QML = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "ImportSourceDialog.qml"
).read_text(encoding="utf-8")


def _szoveg(**mezok) -> str:
    return wipe_card_warning(WipeCardFacts(**mezok))


class TestAZaroMondat:
    def test_MINDIG_kimegy(self):
        """A záró figyelmeztetés nem függ semmilyen darabszámtól."""
        for facts in (
            {},
            {"scan_done": True, "total": 0},
            {"scan_done": True, "total": 500, "duplicates": 12, "unrecognized": 7},
        ):
            assert "THIS CANNOT BE UNDONE." in _szoveg(**facts)

    def test_a_szoveg_VEGEN_all(self):
        szoveg = _szoveg(scan_done=True, total=9, duplicates=1, unrecognized=1)
        assert szoveg.rstrip().endswith("THIS CANNOT BE UNDONE.")


class TestADarabszam:
    def test_pasztazas_utan_a_SZAM_all_ott(self):
        assert "After importing, 42 file(s) will be deleted." in _szoveg(
            scan_done=True, total=42
        )

    def test_pasztazas_ELOTT_nem_talalgat(self):
        """A hamis szám rosszabb, mint a bevallott bizonytalanság — az
        eredetinek is külön erőforrása van rá (`WipeCardScanNotDone`)."""
        szoveg = _szoveg()
        assert "An unknown number of files will be deleted" in szoveg
        assert "file(s) will be deleted" not in szoveg


class TestAMasodpeldanyok:
    def test_egy_masodpeldany_EGYES_szamban(self):
        assert "1 file will not be imported" in _szoveg(scan_done=True, duplicates=1)

    def test_tobb_masodpeldany_TOBBES_szamban(self):
        assert "3 files will not be imported" in _szoveg(scan_done=True, duplicates=3)

    def test_nulla_masodpeldanynal_NINCS_ilyen_sor(self):
        assert "not be imported" not in _szoveg(scan_done=True, duplicates=0)


class TestANemFelismertFajlok:
    def test_egy_fajl_EGYES_szamban(self):
        assert "recognize 1 of the files" in _szoveg(scan_done=True, unrecognized=1)

    def test_tobb_fajl_a_SZAMMAL(self):
        assert "recognize 5 of the files" in _szoveg(scan_done=True, unrecognized=5)

    def test_nulla_eseten_NINCS_ilyen_sor(self):
        assert "recognize" not in _szoveg(scan_done=True, unrecognized=0)


class TestASorrend:
    def test_a_darabok_a_MERT_sorrendben_allnak(self):
        szoveg = _szoveg(
            scan_done=True, total=100, duplicates=2, unrecognized=3
        )
        helyek = [
            szoveg.index("WARNING"),
            szoveg.index("After importing"),
            szoveg.index("not be imported"),
            szoveg.index("recognize"),
            szoveg.index("Are you sure"),
        ]
        assert helyek == sorted(helyek)


class TestAFelulet:
    def test_a_parbeszed_a_VEZERLOTOL_keri_a_szoveget(self):
        """Nem beégetett mondat: a darabszámok csak a vezérlőben ismertek."""
        assert "importSourceController.wipeCardWarning()" in _QML
        assert "delete ALL FILES…" not in _QML


class TestANemMediaFajlokSzamolasa:
    def test_a_pasztazas_megszamolja_az_idegen_fajlokat(self, tmp_path):
        """A `.thm`/szövegfájl nem média — de a törlés elvinné, ezért a
        figyelmeztetésben szerepelnie kell."""
        from support.jpeg_factory import make_jpeg

        from picasapy.importsource import scan_source_detailed

        forras = tmp_path / "DCIM" / "100OLYMP"
        forras.mkdir(parents=True)
        make_jpeg(forras / "P1000001.jpg", size=(32, 24))
        make_jpeg(forras / "P1000002.jpg", size=(32, 24))
        (forras / "P1000001.THM").write_bytes(b"idegen")
        (forras / "CAMERA.TXT").write_text("beallitasok", encoding="utf-8")

        scan = scan_source_detailed(tmp_path)
        assert [p.path.name for p in scan.candidates] == [
            "P1000001.jpg", "P1000002.jpg"
        ]
        assert scan.unrecognized == 2

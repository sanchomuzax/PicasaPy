"""#2553: hol nyíljon a napló mentés-párbeszéde.

## Miért van erre külön őr

A #1654 a naplót EGYETLEN, beégetett helyre másolta
(`/mnt/nas`, Windowson `//DS215j/lemez`, azon belül `picasapy-naplo/`).
Az a hely a tulajdonos gépére volt szabva, és MÉRVE (2026-09-06) a
fejlesztői gépről nem is látszott: onnan a megosztásnak csak egy MÁSIK
almappája van csatolva. A napló tehát kiment — és senki nem érte el; a
tulajdonosnak kézzel kellett átküldenie a #2483 naplóját.

A döntés ezért tiszta függvény: se fájlrendszer, se `QSettings`, tehát
lehet rá állítást írni.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.perf.tesztuzem import NAPLO_ALMAPPA, kiindulo_naplo_mappa


class TestSorrend:
    def test_a_MEGJEGYZETT_mappa_nyer(self, tmp_path):
        megjegyzett = tmp_path / "valasztott"
        megjegyzett.mkdir()
        megosztas = tmp_path / "nas"
        megosztas.mkdir()
        assert (
            kiindulo_naplo_mappa(
                megjegyzett=str(megjegyzett),
                megosztas=megosztas,
                dokumentumok=tmp_path / "dok",
            )
            == megjegyzett
        )

    def test_megjegyzett_nelkul_a_megosztas_naplos_almappaja(self, tmp_path):
        megosztas = tmp_path / "nas"
        megosztas.mkdir()
        assert kiindulo_naplo_mappa(
            megjegyzett=None, megosztas=megosztas, dokumentumok=tmp_path / "dok"
        ) == megosztas / NAPLO_ALMAPPA

    def test_elerhetetlen_megosztasnal_a_DOKUMENTUMOK(self, tmp_path):
        """⚠️ Ez az ág sosem maradhat el: a párbeszédnek akkor is fel kell
        jönnie, ha a megosztás nem érhető el. A #1654-ben ilyenkor a
        felhasználó hibaüzenetet kapott a napló helyett."""
        dok = tmp_path / "dok"
        assert (
            kiindulo_naplo_mappa(
                megjegyzett=None, megosztas=None, dokumentumok=dok
            )
            == dok
        )


class TestAzElavultValasztas:
    """A megjegyzett mappa eltűnhet (kihúzott pendrive, törölt mappa) —
    ilyenkor nem oda kell nyitni, hanem tovább kell lépni a sorban."""

    def test_a_NEM_LETEZO_megjegyzett_mappat_atlepjuk(self, tmp_path):
        megosztas = tmp_path / "nas"
        megosztas.mkdir()
        assert kiindulo_naplo_mappa(
            megjegyzett=str(tmp_path / "mar-nincs"),
            megosztas=megosztas,
            dokumentumok=tmp_path / "dok",
        ) == megosztas / NAPLO_ALMAPPA

    def test_a_FAJLRA_mutato_megjegyzest_is_atlepjuk(self, tmp_path):
        fajl = tmp_path / "nem-mappa.txt"
        fajl.write_text("x", encoding="utf-8")
        dok = tmp_path / "dok"
        assert (
            kiindulo_naplo_mappa(
                megjegyzett=str(fajl), megosztas=None, dokumentumok=dok
            )
            == dok
        )

    def test_ures_megjegyzes_nem_szamit(self, tmp_path):
        dok = tmp_path / "dok"
        assert (
            kiindulo_naplo_mappa(
                megjegyzett="", megosztas=None, dokumentumok=dok
            )
            == dok
        )


class TestNemIrElesbe:
    """⚠️ A `/mnt/nas` ÉLES családi adat — ez a fájl SOHA nem ír oda."""

    def test_a_dontes_nem_nyul_a_fajlrendszerhez_iraskent(self, tmp_path):
        """A függvény csak OLVAS (`is_dir`), és a visszaadott útvonalat
        nem hozza létre — a mappát a mentés hozza majd, oda, ahova a
        felhasználó mutat."""
        cel = tmp_path / "nas"
        eredmeny = kiindulo_naplo_mappa(
            megjegyzett=None, megosztas=cel, dokumentumok=tmp_path / "dok"
        )
        assert isinstance(eredmeny, Path)
        assert not eredmeny.exists()

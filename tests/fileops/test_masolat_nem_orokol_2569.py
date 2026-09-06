"""#2569: a másolat NEM fogadja örökbe a célban heverő idegen eredetit.

## A lelet

A `copy.py::_unique_target` a foglaltság-vizsgálatot KAPUZTA:
`needs_originals_slot=bool(companions_of(path))`. Kísérő nélküli képnél
tehát TELJESEN elmaradt — ha a célmappa eredeti-mappájában ott hevert egy
azonos nevű ÁRVA eredeti, a másolat ráült.

MÉRVE (2026-09-06, a #2510 köre): a `copy_photo` után a másolatra hívott
`find_original_backup` az IDEGEN árva bájtjait adta vissza. A felhasználó
a saját, frissen másolt képén egy másik kép régi változatát kapná
„megőrzött eredetiként", és a „Vissza az eredetihez" azt töltené vissza.

## A javítás iránya — a jegy két jelöltje közül

A jegy (b) ágát választottuk: **az árva eredetihez nem nyúlunk**, a
másolat pedig pótnevet kap, tehát nem is örökölheti. Az (a) ág (a
másolatnak NE legyen megőrzött eredetije) ugyanide vezetne, de a
`find_original_backup` NÉV szerint keres — a másolatnak külön kellene
tudnia, hogy „az ott heverő nem az enyém", ami minden olvasót érintene.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.edit import ORIGINALS_DIR_NAME, find_original_backup
from picasapy.fileops import copy_photo

IDEGEN = b"IDEGEN ARVA EREDETI"
SAJAT = b"a masolando kep"


def _kep(mappa: Path, nev: str, tartalom: bytes = SAJAT) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    ut = mappa / nev
    ut.write_bytes(tartalom)
    return ut


def _arva_eredeti(mappa: Path, nev: str, tartalom: bytes = IDEGEN) -> Path:
    """Árva megőrzött eredeti: a KÉP maga nincs meg a mappában."""
    konyvtar = mappa / ORIGINALS_DIR_NAME
    konyvtar.mkdir(parents=True, exist_ok=True)
    ut = konyvtar / nev
    ut.write_bytes(tartalom)
    return ut


class TestAMasolatNemOrokol:
    def test_a_masolat_NEM_kapja_meg_az_arva_eredetit(self, tmp_path):
        """Ez a jegy magja: a másolatnak nem lehet olyan »megőrzött
        eredetije«, amit nem ő hagyott ott."""
        forras = _kep(tmp_path / "forras", "x.jpg")
        cel = tmp_path / "cel"
        cel.mkdir()
        _arva_eredeti(cel, "x.jpg")

        masolat = copy_photo(forras, cel)

        eredeti = find_original_backup(masolat)
        assert eredeti is None or eredeti.read_bytes() != IDEGEN, (
            f"a másolat ({masolat.name}) örökölte az idegen eredetit: "
            f"{eredeti}"
        )

    def test_a_masolat_POTNEVET_kap(self, tmp_path):
        forras = _kep(tmp_path / "forras", "x.jpg")
        cel = tmp_path / "cel"
        cel.mkdir()
        _arva_eredeti(cel, "x.jpg")

        masolat = copy_photo(forras, cel)

        assert masolat.name != "x.jpg", (
            "a másolat a foglalt névre került — épp arra, amin az idegen "
            "eredeti ül"
        )
        assert masolat.read_bytes() == SAJAT

    def test_az_ARVA_eredeti_SERTETLEN_marad(self, tmp_path):
        """⚠️ A javítás nem takaríthat: a felhasználó régi adata nem a mi
        dolgunk eldobni (a csokor kimondott elve, #2511)."""
        forras = _kep(tmp_path / "forras", "x.jpg")
        cel = tmp_path / "cel"
        cel.mkdir()
        arva = _arva_eredeti(cel, "x.jpg")

        copy_photo(forras, cel)

        assert arva.exists() and arva.read_bytes() == IDEGEN


class TestAMukodoEsetekValtozatlanok:
    """⚠️ A javítás nem ronthatja el azt, ami eddig jó volt."""

    def test_ures_celmappaba_a_SAJAT_neven_landol(self, tmp_path):
        forras = _kep(tmp_path / "forras", "x.jpg")
        cel = tmp_path / "cel"
        cel.mkdir()

        masolat = copy_photo(forras, cel)

        assert masolat.name == "x.jpg"

    def test_a_GAZDAS_pillanatkep_nem_foglal(self, tmp_path):
        """#2510: ha a célban egy ÖNÁLLÓ kép (`x.1.jpg`) áll a saját
        eredetijével, az a mi `x.jpg`-nknek nem foglalja el a helyet — a
        gazdás példányt a `snapshot_numbers` kizárja."""
        forras = _kep(tmp_path / "forras", "x.jpg")
        cel = tmp_path / "cel"
        _kep(cel, "x.1.jpg", b"onallo kep")
        konyvtar = cel / ORIGINALS_DIR_NAME
        konyvtar.mkdir(parents=True, exist_ok=True)
        (konyvtar / "x.1.jpg").write_bytes(b"az onallo kep eredetije")

        masolat = copy_photo(forras, cel)

        assert masolat.name == "x.jpg", (
            "a gazdás pillanatkép-példány fölöslegesen foglalta a helyet"
        )

    def test_KISEROS_kep_masolasa_valtozatlan(self, tmp_path):
        """#1450: ha a képnek VAN megőrzött eredetije, az a másolattal
        megy — ezt a javítás nem érintheti."""
        forras_mappa = tmp_path / "forras"
        forras = _kep(forras_mappa, "y.jpg", b"szerkesztett")
        konyvtar = forras_mappa / ORIGINALS_DIR_NAME
        konyvtar.mkdir(parents=True, exist_ok=True)
        (konyvtar / "y.jpg").write_bytes(b"az eredeti")
        cel = tmp_path / "cel"
        cel.mkdir()

        masolat = copy_photo(forras, cel)

        eredeti = find_original_backup(masolat)
        assert eredeti is not None and eredeti.read_bytes() == b"az eredeti"

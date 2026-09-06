"""#1452 — a kötegelt út MAPPÁNKÉNT EGYSZER listázzon, ne képenként kétszer.

A `plan_original_moves` képenként ÉS eredeti-mappanevenként egy teljes
könyvtárlistázást végzett, a `batch._conflicts` (`originals_slot_free`)
még egyet. A gyűjtemény NAS-on van, mért napló-korláttal (#1146), ahol egy
listázás drága.

MÉRVE (2026-09-06, 500 képes köteg, `os.scandir` becsomagolva és a
picasapy-beli hívási helyre visszavezetve):

===================================================== ======== =======
forgatókönyv (500 kép)                                 előtte   utána
===================================================== ======== =======
forrásban van eredeti, cél üres                            999       3
forrásban van eredeti, célban is van eredeti-mappa        1500       4
forrásban nincs eredeti, célban van eredeti-mappa         1000       2
===================================================== ======== =======

A gyorstár NEM „elévül", hanem KÖNYVELT: a modul minden saját
mozgatását/másolását/törlését átvezeti a tárolt névlistán. Az őrök ezért
nem csak a DARABSZÁMOT mérik — azt is, hogy a gyorstárral és nélküle
ugyanaz a végállapot jön ki, és hogy a hatókörön belül a saját írásaink
azonnal látszanak.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from picasapy.edit import ORIGINALS_DIR_NAME
from picasapy.fileops import originals as originals_modul
from picasapy.fileops.batch import RENAME, conflicting_names, move_photos
from picasapy.fileops.originals import listing_cache, originals_slot_free

KEPEK = 12


def _epit(base: Path, *, eredetivel: bool) -> tuple[Path, Path, list[Path]]:
    forras = base / "forras"
    cel = base / "cel"
    forras.mkdir()
    cel.mkdir()
    directory = forras / ORIGINALS_DIR_NAME
    if eredetivel:
        directory.mkdir()
    for i in range(KEPEK):
        (forras / f"k{i:02d}.jpg").write_bytes(f"kep{i}".encode())
        if eredetivel:
            (directory / f"k{i:02d}.jpg").write_bytes(f"eredeti{i}".encode())
    return forras, cel, sorted(forras.glob("*.jpg"))


def _szamlalo(monkeypatch) -> dict[str, int]:
    """A `_read_names` a modul EGYETLEN listázó pontja — azt csomagoljuk be.

    Nem az `os.scandir`-t: az a globális modult írná át, tehát a teszt
    minden más listázását is megzavarná (ugyanaz a csapda, amiért a `_move`
    is modulszintű fogantyú, #1375)."""
    valodi = originals_modul._read_names
    szamlalo = {"n": 0}

    def _burkolo(directory):
        szamlalo["n"] += 1
        return valodi(directory)

    monkeypatch.setattr(originals_modul, "_read_names", _burkolo)
    return szamlalo


def _ujjlenyomat(base: Path) -> list[str]:
    tetelek: list[str] = []
    for path in sorted(base.rglob("*")):
        rel = str(path.relative_to(base))
        if path.is_dir():
            tetelek.append(f"D {rel}")
        else:
            jegy = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
            tetelek.append(f"F {rel} {jegy}")
    return tetelek


class TestListazasSzam:
    def test_a_koteg_mappankent_egyszer_listaz(self, tmp_path, monkeypatch):
        """A listázások száma NE a képek számával nőjön.

        A korlát szándékosan a köteg méretétől független konstans: két
        mappa (a forrás és a cél eredeti-mappája) plusz a
        `conflicting_names` saját hatóköre. Ha valaha megnőne, az azt
        jelenti, hogy a könyvelés helyett újralistázunk."""
        forras, cel, kepek = _epit(tmp_path, eredetivel=True)
        szamlalo = _szamlalo(monkeypatch)

        conflicting_names(kepek, cel)
        eredmeny = move_photos(kepek, cel, RENAME)

        assert eredmeny.failed == ()
        assert len(eredmeny.done) == KEPEK
        assert szamlalo["n"] <= 6, (
            f"{KEPEK} képnél {szamlalo['n']} listázás — a képenkénti "
            f"listázás visszatért"
        )

    def test_kisero_nelkuli_kotegnel_egyaltalan_nem_listazunk(
        self, tmp_path, monkeypatch
    ):
        """Ha egyik mappában sincs eredeti-mappa, listázni sincs mit."""
        forras, cel, kepek = _epit(tmp_path, eredetivel=False)
        szamlalo = _szamlalo(monkeypatch)

        conflicting_names(kepek, cel)
        move_photos(kepek, cel, RENAME)

        assert szamlalo["n"] == 0


class TestUgyanazAVegallapot:
    """A gyorstár nem változtathat a MŰKÖDÉSEN — csak a listázások számán."""

    def test_gyorstarral_es_nelkule_azonos_eredmeny(self, tmp_path):
        vegallapotok = []
        for hanyadik, gyorstarral in enumerate((True, False)):
            base = tmp_path / f"kor{hanyadik}"
            base.mkdir()
            forras, cel, kepek = _epit(base, eredetivel=True)
            # egy ütközés is legyen a kötegben, hogy a `_free_name` is fusson
            (cel / "k00.jpg").write_bytes(b"mar ott volt")
            if gyorstarral:
                eredmeny = move_photos(kepek, cel, RENAME)
            else:
                # a `_run` saját hatóköre helyett semmi: a `listing_cache`
                # kikapcsolva ugyanaz a kód friss listázásokkal fut
                eredeti = originals_modul._LISTINGS.get()
                assert eredeti is None
                eredmeny = _gyorstar_nelkul(kepek, cel)
            assert eredmeny.failed == ()
            vegallapotok.append(_ujjlenyomat(base))

        assert vegallapotok[0] == vegallapotok[1]


def _gyorstar_nelkul(kepek, cel):
    """A köteg úgy, hogy a `listing_cache()` hatóköre üresen fut."""
    import contextlib

    import picasapy.fileops.batch as batch_modul

    @contextlib.contextmanager
    def _nincs():
        yield

    valodi = batch_modul.listing_cache
    batch_modul.listing_cache = _nincs
    try:
        return move_photos(kepek, cel, RENAME)
    finally:
        batch_modul.listing_cache = valodi


class TestKonyveles:
    """A gyorstár a SAJÁT írásainkat azonnal átvezeti — enélkül a köteg
    második képe egy elavult listából dolgozna, és a `_free_name` olyan
    nevet adna, amire a `_reject_unsafe_targets` aztán rádobna."""

    @staticmethod
    def _ket_mappa(tmp_path: Path) -> tuple[Path, Path]:
        """Forrás és cél, MINDKETTŐBEN meglévő (de a célban üres)
        eredeti-mappával.

        A célmappát azért hozzuk létre előre, mert az `originals_slot_free`
        nem létező mappát meg sem listáz — akkor a gyorstárnak nem is
        lenne mit könyvelnie, és az őr üresen zöldülne.

        A kísérő SORSZÁMOZOTT PILLANATKÉP, nem a megőrzött eredeti: a
        közvetlen névre az `originals_slot_free` `exists()`-tel kérdez (az
        egy stat, nem listázás), tehát az nem menne át a gyorstáron, és az
        őr megint üresen zöldülne. A pillanatkép-keresés viszont a
        listából dolgozik — épp azt mérjük."""
        forras = tmp_path / "A"
        cel = tmp_path / "B"
        forras.mkdir()
        cel.mkdir()
        (forras / "a.jpg").write_bytes(b"kep")
        (forras / ORIGINALS_DIR_NAME).mkdir()
        (forras / ORIGINALS_DIR_NAME / "a.1.jpg").write_bytes(b"pillanatkep")
        (cel / ORIGINALS_DIR_NAME).mkdir()
        return forras, cel

    def test_az_atkoltoztetett_eredeti_azonnal_foglal(self, tmp_path):
        from picasapy.fileops.originals import move_preserved_originals

        forras, cel = self._ket_mappa(tmp_path)

        with listing_cache():
            # a hatókörön belüli ELSŐ kérdés listáz — innentől a gyorstár felel
            assert originals_slot_free(cel, "a.jpg")
            assert not originals_slot_free(forras, "a.jpg")

            move_preserved_originals(forras / "a.jpg", cel / "a.jpg")

            # a saját írásunk azonnal látszik, újralistázás nélkül…
            assert not originals_slot_free(cel, "a.jpg")
            # …és a forrásból ugyanígy eltűnt
            assert originals_slot_free(forras, "a.jpg")

    def test_a_visszagorgetett_eredeti_ujra_szabadda_teszi(self, tmp_path):
        from picasapy.fileops.originals import (
            move_preserved_originals,
            undo_original_moves,
        )

        forras, cel = self._ket_mappa(tmp_path)

        with listing_cache():
            assert originals_slot_free(cel, "a.jpg")
            assert not originals_slot_free(forras, "a.jpg")

            megtett = move_preserved_originals(forras / "a.jpg", cel / "a.jpg")
            undo_original_moves(megtett)

            assert originals_slot_free(cel, "a.jpg")
            assert not originals_slot_free(forras, "a.jpg")

    def test_a_hatokoron_kivul_nincs_gyorstar(self, tmp_path):
        """Az egyfájlos utak érintetlenek: gyorstár nélkül minden kérdés
        friss listázás, pontosan úgy, mint a jegy előtt."""
        assert originals_modul._LISTINGS.get() is None
        with listing_cache():
            assert originals_modul._LISTINGS.get() == {}
        assert originals_modul._LISTINGS.get() is None

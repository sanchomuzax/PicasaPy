"""#7292: a mentésvezérlő bekötése a `.picasa.ini`-beli készlet-bélyegbe.

A bélyeg olvasását és írását a `tests/backup/test_mentes_belyeg_7292.py`
méri; ez a fájl azt, hogy a FELÜLETRŐL indított útvonalak mind bélyegeznek:
a mappába másolás, a lemezkép-írás, és hogy az „Edit Set” átnevezése
átviszi a kulcsokat.
"""

from __future__ import annotations

import pytest

from picasapy.backup import keszlet_kulcs
from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa
from picasapy.ini import load_document, update_document
from picasapy.ini.names import INI_NAME

_NEV = "Teszt"


@pytest.fixture
def kornyezet(tmp_path):
    forras = tmp_path / "kepek"
    (forras / "2020").mkdir(parents=True)
    for i in range(2):
        (forras / "2020" / f"IMG_{i}.jpg").write_bytes(
            b"\xff\xd8\xff" + bytes([i]) * 4000
        )
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        keszlet_id = keszlet_letrehozasa(
            conn, _NEV, str(tmp_path / "cel")
        ).id
        conn.commit()
    jeloltek = tuple(sorted(str(p) for p in (forras / "2020").glob("*.jpg")))
    return db, keszlet_id, jeloltek, str(forras), forras / "2020"


@pytest.fixture
def vezerlo(qt_app, kornyezet, monkeypatch):
    from picasapy.app import backup_controller as modul

    db, keszlet_id, jeloltek, gyoker, mappa = kornyezet
    ctl = modul.BackupController(db, (gyoker,))
    monkeypatch.setattr(ctl, "_jeloltek", lambda: jeloltek)
    yield ctl, keszlet_id, mappa
    ctl.waitForBackgroundWorkers(20.0)


def _var(ctl, qt_app) -> None:
    assert ctl.waitForBackgroundWorkers(60.0), "a háttérszál nem állt le"
    qt_app.processEvents()


def _ertek(mappa, fajl: str, kulcs: str) -> str | None:
    szakasz = load_document(mappa / INI_NAME).section(fajl)
    return None if szakasz is None else szakasz.get(kulcs)


def _szerkeszt(mappa, fajl: str) -> None:
    """Metaadat-szerkesztés: felirat és a sima `backuphash` új értéke."""
    uj = "65000" if _ertek(mappa, fajl, "backuphash") != "65000" else "64000"
    update_document(
        mappa / INI_NAME,
        lambda d: d.with_value(fajl, "caption", "új").with_value(
            fajl, "backuphash", uj
        ),
    )


class TestAMappabaMentes:
    def test_a_futas_belyegzi_a_forras_ini_jet(self, vezerlo, qt_app):
        ctl, keszlet_id, mappa = vezerlo
        ctl.futtasdMost(keszlet_id)
        _var(ctl, qt_app)
        for fajl in ("IMG_0.jpg", "IMG_1.jpg"):
            sima = _ertek(mappa, fajl, "backuphash")
            assert sima not in (None, "0")
            assert _ertek(mappa, fajl, keszlet_kulcs(_NEV)) == sima

    def test_a_szerkesztett_kep_a_kovetkezo_futasban_ujra_megy(
        self, vezerlo, qt_app
    ):
        ctl, keszlet_id, mappa = vezerlo
        ctl.futtasdMost(keszlet_id)
        _var(ctl, qt_app)
        _szerkeszt(mappa, "IMG_0.jpg")

        fogott: list[tuple[int, int]] = []
        ctl.futasKesz.connect(lambda db, bajt: fogott.append((db, bajt)))
        ctl.futtasdMost(keszlet_id)
        _var(ctl, qt_app)
        assert [db for db, _bajt in fogott] == [1]


class TestALemezkepbeMentes:
    def test_a_futas_belyegzi_a_forras_ini_jet(self, vezerlo, qt_app):
        ctl, keszlet_id, mappa = vezerlo
        ctl.futtasdLemezkepbe(keszlet_id, "cd")
        _var(ctl, qt_app)
        for fajl in ("IMG_0.jpg", "IMG_1.jpg"):
            sima = _ertek(mappa, fajl, "backuphash")
            assert sima not in (None, "0")
            assert _ertek(mappa, fajl, keszlet_kulcs(_NEV)) == sima

    def test_a_szerkesztett_kep_a_kovetkezo_futasban_ujra_megy(
        self, vezerlo, qt_app
    ):
        ctl, keszlet_id, mappa = vezerlo
        ctl.futtasdLemezkepbe(keszlet_id, "cd")
        _var(ctl, qt_app)
        _szerkeszt(mappa, "IMG_1.jpg")

        fogott: list[tuple[int, int]] = []
        ctl.lemezkepekKeszek.connect(lambda a, b: fogott.append((a, b)))
        ctl.futtasdLemezkepbe(keszlet_id, "cd")
        _var(ctl, qt_app)
        assert fogott[-1][1] == 1, "a szerkesztett kép nem került újra a lemezre"


class TestAzEditSetAtnevezese:
    def test_a_kulcsok_az_uj_nevre_kerulnek(self, vezerlo, qt_app):
        ctl, keszlet_id, mappa = vezerlo
        ctl.futtasdMost(keszlet_id)
        _var(ctl, qt_app)

        assert ctl.modositsdAKeszletet(keszlet_id, "Éves", "", "")
        for fajl in ("IMG_0.jpg", "IMG_1.jpg"):
            assert _ertek(mappa, fajl, keszlet_kulcs(_NEV)) is None
            assert _ertek(mappa, fajl, keszlet_kulcs("Éves")) == _ertek(
                mappa, fajl, "backuphash"
            )

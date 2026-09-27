"""#3776 [KRITIKUS javítás]: symlinkes/eltérő-betűzésű gyökérnél a mentés
NE veszítse el a mappaszerkezetet.

## A hiba

A `BackupController._jeloltek()` a fájlokat a figyelt gyökér FELOLDOTT
(`normalize_path`) alakja alól gyűjti — ugyanúgy, ahogy a szkenner
(`scanner/walker.py`) is teszi. A `BackupController._tervezd()` viszont a
`picasapy.backup.tervezd_meg`-nek a gyökereket FELOLDATLANUL adta tovább
(`self._gyokerek`), és a `_relativ_ut` (`backup/futtatas.py`) ott a
`fajl.relative_to(Path(gyoker))`-t hívja: egy feloldott fájlút és egy
feloldatlan gyökér között ez MINDIG `ValueError`, tehát a terv a
`Path(fajl.parent.name) / fajl.name` eséstartalékra esett — ez ELVESZTI a
mappaszerkezetet. Két, eltérő gyökér alatti, azonos nevű almappa
(pl. `2023/nyaralas/` és `2024/nyaralas/`) fájljai emiatt UGYANARRA a
célútra másolódtak, egymást felülírva.

A javítás a `_tervezd`-ben: `gyokerek=tuple(normalize_path(gy) for gy in
self._gyokerek)` — innentől a `_relativ_ut` ugyanazt a feloldott alakot
látja mindkét oldalon.

## Ami itt mérve van

A VALÓDI másolás (`futtasd`) a célmappában — ez az, amit a felhasználó
lemez esetén lát. A lemezkép-ág (`futtasdLemezkepbe` →
`lemezkepekbe`) ugyanezt a `terv.fajlok[i].relativ`-ot fogyasztja
változtatás nélkül, tehát a gyökér-feloldás ugyanazon a ponton dől el
mindkét ágra — külön ISO-integrációs próba nélkül is lefedett.
"""

from __future__ import annotations

import sys

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index.backup_sets import keszlet_letrehozasa, keszletek
from support.jpeg_factory import make_jpeg

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="szimbolikus link csak POSIX-on"
)


@pytest.fixture
def kornyezet(tmp_path):
    """Egy valódi gyökér, két azonos nevű almappával, ÉS egy rá mutató
    symlink — a figyelt gyökér ez utóbbi, ahogy a felület átadná."""
    valodi = tmp_path / "valodi"
    for ev in ("2023", "2024"):
        (valodi / ev / "nyaralas").mkdir(parents=True)
        make_jpeg(valodi / ev / "nyaralas" / "IMG_0001.jpg")
    link = tmp_path / "link"
    link.symlink_to(valodi, target_is_directory=True)
    cel = tmp_path / "mentes"
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, link)
        keszlet_id = keszlet_letrehozasa(conn, "Teszt", str(cel)).id
        conn.commit()
    return db, keszlet_id, link, cel


@pytest.fixture
def vezerlo(qt_app, kornyezet):
    from picasapy.app.backup_controller import BackupController

    db, keszlet_id, link, _cel = kornyezet
    ctl = BackupController(db_path=db, gyokerek=(str(link),))
    yield ctl, keszlet_id
    ctl.waitForBackgroundWorkers(20.0)


class TestATervRelativUtja:
    def test_a_ket_azonos_nevu_almappa_kulon_marad(self, vezerlo, kornyezet):
        """A terv relatív útjai — ez fogyasztja mind a valódi másolás
        (`futtasd`), mind a lemezkép-írás (`lemezkepekbe`)."""
        ctl, keszlet_id = vezerlo
        db, _keszlet_id, _link, _cel = kornyezet
        with open_index(db) as conn:
            keszlet = next(k for k in keszletek(conn) if k.id == keszlet_id)
            terv = ctl._tervezd(conn, keszlet, None)
        relativ = sorted(t.relativ.as_posix() for t in terv.fajlok)
        assert relativ == [
            "2023/nyaralas/IMG_0001.jpg",
            "2024/nyaralas/IMG_0001.jpg",
        ], (
            "a mappaszerkezet elveszett — mindkét fájl a saját éves "
            "almappája alatt kell maradjon, nem a puszta fájlnévnél"
        )


class TestAValodiMasolas:
    def test_a_celmappaban_mindket_ev_kulon_almappat_kap(
        self, vezerlo, kornyezet
    ):
        from picasapy.backup import futtasd

        ctl, keszlet_id = vezerlo
        db, _keszlet_id, _link, cel = kornyezet
        with open_index(db) as conn:
            keszlet = next(k for k in keszletek(conn) if k.id == keszlet_id)
            terv = ctl._tervezd(conn, keszlet, None)
            futtasd(conn, keszlet, terv)
            conn.commit()
        kimenet = sorted(
            p.relative_to(cel).as_posix() for p in cel.rglob("*.jpg")
        )
        assert kimenet == [
            "2023/nyaralas/IMG_0001.jpg",
            "2024/nyaralas/IMG_0001.jpg",
        ], (
            "a két azonos nevű fájl egymást írta felül — a mappaszerkezet "
            f"nem maradt meg a célban: {kimenet}"
        )

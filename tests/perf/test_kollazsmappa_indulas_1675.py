"""#1675 ŐR: a Kollázsok mappa önjavítása nem olvashatja újra a mappát.

## A hibaosztály, amit ez az őr befagyaszt

A #1667 kimérte: a `prune_foreign_folders` (#58) kidobja a figyelt
gyökereken kívüli mappákat, az önjavító ág pedig **nulláról építi vissza**
őket — és az üres `photos` tábla miatt a `sync_folder` inkrementális
kihagyása (#139) nem tud működni. Az exportcélokra ez a tulajdonos gépén
**8 406 ms** volt, az indulás 77,8%-a.

A `_onjavito_kollazsmappa` (#1075) UGYANEZT a szerkezetet hordozta. A
tulajdonos naplójában 15,3 ms — nem a legdrágább tétel —, de a #1667
bizonyította, hogy ez **mérethez kötötten robban**: nagy kollázs-mappánál
ugyanígy skálázódik.

## A döntés: a Kollázsok mappa VÉDETT gyökér

A #1675 azt kérte, hogy ez a #1075 SZÁNDÉKA alapján dőljön el, ne
analógiából. A `_onjavito_kollazsmappa` docstringje kimondja: a mappának
az indexben KELL lennie (a Projektek gyűjtemény két feltételének egyike),
és csak a MI kimenetünket jelöljük meg. Egy gyökér, amit minden induláskor
vissza kell építeni, definíció szerint nem „ottragadt idegen mappa".

## Miért DARABSZÁMOT mér, nem időt

A #1653 mérése szerint ugyanaz a szakasz 490–3 679 ms között szórt
(7,5-szeres). Egy nem-flaky időküszöb ~10 s-nál lenne — az egy kétszeres
lassulást sem fogna meg. A munkamennyiség viszont determinisztikus.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app import collage_prefs
from picasapy.app.application import _onjavito_kollazsmappa, _takaritas_gyokerei
from picasapy.index import open_index, prune_foreign_folders, sync_folder
from picasapy.index import sync as sync_modul
from support.jpeg_factory import make_jpeg

#: Kollázs-fájlok száma a próbamappában. Kicsi, de a hibás viselkedésnél
#: bizonyítottan pozitív számot ad (ld. a harmadik teszt).
_KOLLAZS_SZAM = 3


class _Szamlalo:
    """Az indulási kör MUNKAMENNYISÉGE — fájlnyitás és fotósor-írás."""

    def __init__(self) -> None:
        self.fajlnyitas = 0
        self.fotosor_iras = 0

    def figyeld_a_kapcsolatot(self, conn) -> None:
        def nyom(utasitas: str) -> None:
            elso = utasitas.strip().upper()
            if elso.startswith(("INSERT INTO PHOTOS", "UPDATE PHOTOS")):
                self.fotosor_iras += 1

        conn.set_trace_callback(nyom)


@pytest.fixture
def szamlalo(monkeypatch) -> _Szamlalo:
    """A `read_file_metadata` hívásainak számlálása a `sync` modulban — a
    modul FOGANTYÚJÁT cseréljük, nem a `metadata` csomagot."""
    szam = _Szamlalo()
    eredeti = sync_modul.read_file_metadata

    def merve(path):
        szam.fajlnyitas += 1
        return eredeti(path)

    monkeypatch.setattr(sync_modul, "read_file_metadata", merve)
    return szam


@pytest.fixture
def konyvtar(tmp_path):
    """Figyelt gyökér + a gyökéren KÍVÜLI Kollázsok mappa, kész indexszel."""
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "IMG_0001.jpg", size=(32, 24))

    kollazsok = tmp_path / "kimenet" / "Picasa" / "Kollázsok"
    kollazsok.mkdir(parents=True)
    for i in range(_KOLLAZS_SZAM):
        make_jpeg(kollazsok / f"kollazs{i}.jpg", size=(32, 24))

    # a #1682 tanulsága: ha a célmappa a figyelt gyökér ALATT volna, a
    # takarítás ki sem dobná — az őr üresen zöld lenne
    assert not kollazsok.resolve().is_relative_to(gyoker.resolve()), (
        "a Kollázsok mappa a figyelt gyökér alatt van — az őr nem mérne semmit"
    )

    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue(collage_prefs.OUTPUT_DIR_KEY, str(kollazsok))

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_folder(conn, gyoker, gyoker)
        sync_folder(conn, kollazsok, kollazsok)
    return db, gyoker, kollazsok, settings


def _indulasi_kor(db: Path, gyoker: Path, settings, szamlalo: _Szamlalo):
    """EGY indulás index-munkája, a `run()` lépéseivel és sorrendjében."""
    with open_index(db) as conn:
        prune_foreign_folders(conn, _takaritas_gyokerei((str(gyoker),), settings))
        szamlalo.figyeld_a_kapcsolatot(conn)
        _onjavito_kollazsmappa(conn, settings)
        conn.set_trace_callback(None)
        mappak = [row["path"] for row in conn.execute("SELECT path FROM folders")]
        kepek = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    return mappak, kepek


class TestAzIndulasNemOlvassaUjraAKollazsokat:
    def test_valtozatlan_kollazsmappanal_nulla_fajlnyitas_es_nulla_iras(
        self, konyvtar, szamlalo
    ):
        """A munkamennyiség-állítás — ez a #1675 javításának foga."""
        db, gyoker, _kollazsok, settings = konyvtar

        _mappak, kepek = _indulasi_kor(db, gyoker, settings, szamlalo)

        assert kepek == 1 + _KOLLAZS_SZAM, (
            f"az indulási kör után nincs meg minden kép az indexben "
            f"({kepek}) — az őr üres adaton mérne"
        )
        assert szamlalo.fajlnyitas == 0, (
            f"az indulás {szamlalo.fajlnyitas} kollázs-fájlt nyitott meg, "
            "pedig egyikük sem változott — a takarítás kidobta a mappát, és "
            "az önjavítás nulláról építette vissza (#1675)"
        )
        assert szamlalo.fotosor_iras == 0, (
            f"az indulás {szamlalo.fotosor_iras} fotósort írt változatlan "
            "kollázsmappára"
        )

    def test_a_kollazsmappa_bent_marad_a_takaritas_utan(self, konyvtar, szamlalo):
        """A védelem-állítás: a mappa sora túléli a takarítást.

        ⚠️ Ennek a tesztnek MAGÁBAN nincs foga: mutációval ellenőrizve
        akkor is átment, amikor a védelmet elvettem — mert az önjavítás a
        mappa SORÁT úgyis visszateszi. A javítás foga a fenti
        munkamennyiség-teszt (védelem nélkül három fájlnyitás, vele nulla).
        Ez a teszt azt zárja ki, hogy a mappa teljesen eltűnjön."""
        db, gyoker, kollazsok, settings = konyvtar

        mappak, _kepek = _indulasi_kor(db, gyoker, settings, szamlalo)

        assert any(Path(m).resolve() == kollazsok.resolve() for m in mappak), (
            "a Kollázsok mappa kiesett az indexből a takarítás után — a "
            "#1675 védelme nem hatott"
        )

    def test_a_meres_nem_uresedett_ki(self, tmp_path, szamlalo):
        """Pozitív kontroll: ELSŐ indexelésnél ugyanez a számláló pozitív.

        Enélkül a nulla azt is jelenthetné, hogy a mérőpont elromlott."""
        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        make_jpeg(gyoker / "IMG_0001.jpg", size=(32, 24))
        kollazsok = tmp_path / "kimenet" / "Picasa" / "Kollázsok"
        kollazsok.mkdir(parents=True)
        for i in range(_KOLLAZS_SZAM):
            make_jpeg(kollazsok / f"kollazs{i}.jpg", size=(32, 24))

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        settings.setValue(collage_prefs.OUTPUT_DIR_KEY, str(kollazsok))

        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_folder(conn, gyoker, gyoker)
        # a kollázsmappa MÉG NINCS az indexben — az első felvétel dolgozik
        _mappak, _kepek = _indulasi_kor(db, gyoker, settings, szamlalo)

        assert szamlalo.fajlnyitas >= _KOLLAZS_SZAM, (
            f"az ELSŐ indexelés is csak {szamlalo.fajlnyitas} fájlt nyitott "
            "meg — a számláló nem méri, amit mérni akarunk"
        )

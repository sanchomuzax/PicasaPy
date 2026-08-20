"""A KÉPHÁTTÉR túléli az újranyitást (#1103).

## A lelet

Az `_apply_cxf_project` a hátteret ELŐBB állította vissza, mint ahogy a
csomópontok a panelre kerültek:

```python
self._apply_cxf_background(projekt.background)   # a csomópontok még a RÉGIEK
self._set_nodes(_panel_nodes_of(...), dirty=False)
```

A képháttér a panelen INDEXKÉNT él (#1009), a `.cxf` viszont ÚTVONALAT tárol,
tehát a visszaállításnak meg kell keresnie a képet a csomópontok között. Két
sorral korábban viszont még nincsenek ott — az index `-1` lesz, és a #1085
védőága (ismeretlen kép → színre esünk vissza) **helyesen, de rossz
pillanatban** kérdezve elejti a hátteret.

A tulajdonos ezt a v0.8.20 óta látja: *„a háttérképet elfelejti, sima színre
kapcsolja vissza."*
"""

from __future__ import annotations


import pytest
from PySide6.QtCore import QSettings

from picasapy.app.controller import AppController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


@pytest.fixture
def keszlet(qt_app, tmp_path):
    """Gyár: minden hívás ÚJ vezérlőt ad, közös könyvtárral és mappával.

    Az újraindítás a lényeg: a valódi eset az, amikor a panel még ÜRES,
    és a visszatöltés akkor keresi a háttérképet a csomópontok között."""
    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir()
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(konyvtar / nev, size=(160, 120))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, konyvtar)
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    beallitas.setValue("collage/outputDir", str(tmp_path / "Kollazsok"))
    gyorstar = ThumbnailCache(tmp_path / "th", size=32)
    peldanyok = []

    def uj():
        peldany = AppController(
            db, (str(konyvtar),), ThumbnailProvider(gyorstar), settings=beallitas
        )
        peldany.selectFolder(str(konyvtar))
        qt_app.processEvents()
        peldanyok.append(peldany)
        return peldany

    try:
        yield uj
    finally:
        for peldany in peldanyok:
            peldany.waitForBackgroundWorkers(20.0)


def test_a_kephatter_tuleli_az_UJRAINDITAST(keszlet):
    """⚠️ A valódi eset: a piszkozat ÚJ vezérlőben, üres panelre töltődik.

    Ekkor a háttér-visszaállítás a csomópontok ELŐTT futott, tehát a
    képet nem találta meg a listában, és a #1085 védőága színre ejtette.
    Ugyanaz a fixtúra nyitott panellel NEM fogja meg a hibát — a
    csomópontok ott már a helyükön vannak."""
    elso = keszlet()
    elso.openCollage([0, 1, 2])
    elso.setCollageSelection([1])
    elso.setBackgroundFromSelection()
    assert elso.collageBackgroundMode == "image", "a háttér be sem állt"
    vart = elso.collageBackgroundImage
    assert vart, "nincs háttérkép-útvonal"
    elso.saveCollageDraft()

    masodik = keszlet()
    masodik.restoreCollageDraft()

    assert masodik.collageBackgroundMode == "image", (
        "a háttérkép elveszett — színre esett vissza"
    )
    assert masodik.collageBackgroundImage == vart

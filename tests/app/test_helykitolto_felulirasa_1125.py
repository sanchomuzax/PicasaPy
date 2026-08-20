"""A véglegesítés a saját HELYKITÖLTŐJÉT írja felül (#1125).

## A tulajdonos jelentése (v0.8.26)

> „Egy korábban csak piszkozatban létező kollázsból létrehoztam egy
> kollázst, és utána az indexképe nem frissült, maradt a »PISZKOZAT«
> felirat a listában."

## Mérve: nem a bélyegkép ragadt be

```
piszkozat fájl : L.jpg
„Létrehozás"   : L1.jpg          ← ÚJ FÁJL
a mappa most   : ['.picasa.ini', 'L.jpg', 'L1.cxf', 'L1.jpg']
```

A PISZKOZAT-kép **tényleg ott van még**, saját fájlként.

⚠️ **Ez a #1072 regressziója.** A helykitöltő a kollázs végleges nevét
kapja, és a szándék az volt, hogy ezzel lefoglalja a nevet. A foglalás
viszont csak a NYITOTT panelen élt (`collageSavedPath`); bezárás →
újranyitás után elveszett, és az `output_path()` sorszámozott.

⚠️ **A korábbi őr azért nem fogta meg, mert NYITOTT panellel dolgozott** —
az őr hatóköre szűkebb volt, mint a hibáé. Ez a teszt ezért a tulajdonos
pontos lépéssorát járja: piszkozat → BEZÁRÁS → újranyitás → Létrehozás.
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
    """Gyár: minden hívás ÚJ vezérlőt ad, közös könyvtárral és mappával."""
    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir()
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(konyvtar / nev, size=(160, 120))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, konyvtar)
    kimenet = tmp_path / "Kollazsok"
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    beallitas.setValue("collage/outputDir", str(kimenet))
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
        yield uj, kimenet
    finally:
        for peldany in peldanyok:
            peldany.waitForBackgroundWorkers(20.0)


def _keszre_vitel(vezerlo, qt_app) -> str:
    kesz: list[str] = []
    vezerlo.collageDone.connect(kesz.append)
    vezerlo.createCollage(False)
    for _ in range(900):
        qt_app.processEvents()
        if kesz:
            break
    vezerlo.waitForBackgroundWorkers(20.0)
    qt_app.processEvents()
    assert kesz, "a kollázs nem készült el"
    return kesz[0]


def test_bezaras_utan_ujranyitva_EGY_jpeg_marad(keszlet, qt_app):
    """A tulajdonos lépéssora: a helykitöltő helyére a kész kollázs lép."""
    uj, kimenet = keszlet
    elso = uj()
    elso.openCollage([0, 1, 2])
    elso.saveCollageDraft()
    elso.closeCollage()
    elso.waitForBackgroundWorkers(20.0)
    helykitolto = sorted(kimenet.glob("*.jpg"))
    assert len(helykitolto) == 1, "a helykitöltő el sem készült"

    masodik = uj()
    masodik.restoreCollageDraft()
    _keszre_vitel(masodik, qt_app)

    maradt = sorted(p.name for p in kimenet.glob("*.jpg"))
    assert maradt == [helykitolto[0].name], (
        f"a helykitöltő ottmaradt a kész kollázs mellett: {maradt}"
    )


def test_IDEGEN_jpeg_hez_NEM_nyulunk(keszlet, qt_app):
    """A felhasználó saját képe a Kollázsok mappában sérthetetlen.

    ⚠️ A „nincs `.cxf` párja" önmagában IGAZ egy idegen JPEG-re is —
    felülírni adatvesztés volna. A helykitöltőt ezért a piszkozat-
    nyilvántartás azonosítja, nem a név vagy a pár hiánya."""
    uj, kimenet = keszlet
    elso = uj()
    elso.openCollage([0, 1, 2])
    elso.saveCollageDraft()
    elso.closeCollage()
    elso.waitForBackgroundWorkers(20.0)
    idegen = kimenet / "sajat kepem.jpg"
    idegen.write_bytes(b"a felhasznalo sajat kepe")

    masodik = uj()
    masodik.restoreCollageDraft()
    _keszre_vitel(masodik, qt_app)

    assert idegen.read_bytes() == b"a felhasznalo sajat kepe"

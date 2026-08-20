"""A piszkozat LÁTHATÓ képe a bezáráskor (#1072).

A tulajdonos szava (v0.8.21, Windows):

    „A piszkozat nem jelenik meg alatt azt értem, hogy SEHOL SEM LÁTOM az
    alkalmazásban az indexképek között az új piszkozatot. … A »PISZKOZAT«
    felirat akkor jelenik meg mentéskor, amikor a »Bezárás« gombot
    megnyomom az eredeti Picasa appban. De csak addig van ott, amíg le nem
    menti. EZ A LÉPÉS TELJESEN HIÁNYZIK a PicasaPy-ben."

Lemérve a 0.8.21-en: a `.cxf` a bezárás után és az újraindítás után is a
lemezen van (nincs adatvesztés) — a Kollázsok mappában viszont EGYEDÜL az
`autosave.cxf` áll, tehát nincs mit mutatni. Ez a három eset azt őrzi, ami
a felhasználónak látszik.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.controller import AppController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.collage.autosave import AUTOSAVE_NAME
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


@dataclasses.dataclass(frozen=True)
class Kollazs:
    """A panelen nyitott kollázs és a hozzá tartozó útvonalak."""

    controller: AppController
    kimenet: Path
    db: Path
    cim: str


@pytest.fixture
def kollazs(qt_app, tmp_path):
    """Három képes kollázs a panelen, saját Kollázsok-mappával."""
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
    vezerlo = AppController(
        db,
        (str(konyvtar),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32)),
        settings=beallitas,
    )
    vezerlo.selectFolder(str(konyvtar))
    qt_app.processEvents()
    vezerlo.openCollage([0, 1, 2])
    assert vezerlo.collageOpen, "a kollázs-panel nem nyílt meg"
    try:
        yield Kollazs(vezerlo, kimenet, db, vezerlo.collageTitle)
    finally:
        vezerlo.waitForBackgroundWorkers(10.0)


def _jpg_ek(mappa: Path) -> list[str]:
    return sorted(p.name for p in mappa.glob("*.jpg"))


def test_a_bezaras_lathato_kepet_hagy_es_indexeli(kollazs):
    """A bezárás után van kép, ÉS a mappa bekerül az indexbe.

    A kettő EGYÜTT kell: a fájl önmagában nem elég, mert a bal hasáb a
    `folders` táblából dolgozik (#1048) — enélkül a felhasználó pontosan
    azt látja, amit jelentett: semmit."""
    kollazs.controller.saveCollageDraft()
    kollazs.controller.closeCollage()

    assert (kollazs.kimenet / AUTOSAVE_NAME).exists()
    assert _jpg_ek(kollazs.kimenet), "a piszkozatnak nincs látható képe"

    with open_index(kollazs.db) as conn:
        sorok = conn.execute("SELECT path FROM folders").fetchall()
    assert str(kollazs.kimenet) in {sor[0] for sor in sorok}


def test_ujra_bezarva_NEM_szaporodik(kollazs):
    """Visszaállítás után újra bezárva UGYANAZT a képet írjuk felül.

    A tulajdonos szerint a piszkozatnak egyetlen képe van; számozott
    `Kollázs1.jpg`, `Kollázs2.jpg` sorozat minden körben szemetet hagyna a
    Kollázsok mappában."""
    kollazs.controller.saveCollageDraft()
    kollazs.controller.closeCollage()
    elso = _jpg_ek(kollazs.kimenet)

    kollazs.controller.restoreCollageDraft()
    kollazs.controller.saveCollageDraft()
    kollazs.controller.closeCollage()

    assert _jpg_ek(kollazs.kimenet) == elso


def test_kesz_kollazst_NEM_ir_felul(kollazs):
    """A kész kollázst (van `.cxf` párja) a helykitöltő nem bántja.

    A megkülönböztető a projektfájl-pár: a helykitöltő mellett nincs saját
    `.cxf`, a kész kollázs mellett van. Ha ezt elrontjuk, egy piszkozat
    elviszi a felhasználó BEFEJEZETT munkáját — ez a legdrágább hiba, ami
    ezen az úton történhet."""
    kesz = kollazs.kimenet / f"{kollazs.cim}.jpg"
    kesz.parent.mkdir(parents=True, exist_ok=True)
    kesz.write_bytes(b"a felhasznalo kesz kollazsa")
    kesz.with_suffix(".cxf").write_text("<collage/>", encoding="utf-8")

    kollazs.controller.saveCollageDraft()
    kollazs.controller.closeCollage()

    assert kesz.read_bytes() == b"a felhasznalo kesz kollazsa"
    assert len(_jpg_ek(kollazs.kimenet)) == 2

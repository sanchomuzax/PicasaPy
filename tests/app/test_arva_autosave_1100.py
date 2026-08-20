"""A véglegesítés takarítsa el a piszkozatot (#1100).

## Miért baj az árva `autosave.cxf`

A valódi Picasa **elárvult automentésként** ismeri fel a kép nélkül maradt
`autosave.cxf`-et, és a saját 640 × 480-as, egyszínű sötétszürke
helykitöltőjét írja mellé — `autosave.jpg` néven, a felhasználó Kollázsok
mappájába. A tulajdonos ezt látta a v0.8.23-ban, és jogosan hitte a mi
kimenetünknek.

Vagyis a mi maradékunk **szemetet gyártat a valódi Picasával a felhasználó
mappájában**. A megoldás nem a szemét takarítása, hanem hogy ne hagyjunk
árva projektfájlt: ha a kollázs elkészült, a piszkozat betöltötte a
szerepét.

⚠️ A már ott lévő, **Picasa által írt `autosave.jpg`-hez nem nyúlunk** — az
nem a mi fájlunk.
"""

from __future__ import annotations


import pytest
from PySide6.QtCore import QSettings

from picasapy.app.controller import AppController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.collage.autosave import AUTOSAVE_NAME
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


@pytest.fixture
def vezerlo(qt_app, tmp_path):
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
    peldany = AppController(
        db,
        (str(konyvtar),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32)),
        settings=beallitas,
    )
    peldany.selectFolder(str(konyvtar))
    qt_app.processEvents()
    peldany.openCollage([0, 1, 2])
    try:
        yield peldany, kimenet
    finally:
        peldany.waitForBackgroundWorkers(20.0)


def _keszre_vitel(vezerlo, qt_app) -> None:
    """A kollázs végleges kiírása, megvárva a háttérszálat."""
    vezerlo.createCollage(False)
    for _ in range(600):
        qt_app.processEvents()
        if vezerlo.collageSavedPath:
            break
    vezerlo.waitForBackgroundWorkers(20.0)
    qt_app.processEvents()


def test_a_veglegesites_UTAN_nincs_arva_piszkozat(vezerlo, qt_app):
    """Elkészült kollázs mellett nem maradhat `autosave.cxf`."""
    peldany, kimenet = vezerlo
    peldany.saveCollageDraft()
    assert (kimenet / AUTOSAVE_NAME).exists(), "a piszkozat el sem készült"

    _keszre_vitel(peldany, qt_app)

    assert not (kimenet / AUTOSAVE_NAME).exists(), (
        "árva autosave.cxf maradt — a valódi Picasa szürke autosave.jpg-t "
        "gyárt rá a felhasználó mappájában"
    )


def test_a_veglegesites_utan_NEM_ajanlja_fel_a_helyreallitast(vezerlo, qt_app):
    """A takarítás a beállításból is kivezet: nincs mit helyreállítani.

    Ha csak a fájlt törölnénk, a program indításkor még mindig felajánlaná
    a piszkozatot — és a felhasználó egy nem létező munkát „állítana
    helyre"."""
    peldany, _ = vezerlo
    peldany.saveCollageDraft()

    _keszre_vitel(peldany, qt_app)

    assert not peldany.collageDraftAvailable


def test_a_Picasa_altal_irt_autosave_jpg_hez_NEM_nyulunk(vezerlo, qt_app):
    """Idegen fájl a felhasználó mappájában — nem a mi dolgunk törölni."""
    peldany, kimenet = vezerlo
    kimenet.mkdir(parents=True, exist_ok=True)
    idegen = kimenet / "autosave.jpg"
    idegen.write_bytes(b"a Picasa irta")
    peldany.saveCollageDraft()

    _keszre_vitel(peldany, qt_app)

    assert idegen.read_bytes() == b"a Picasa irta"

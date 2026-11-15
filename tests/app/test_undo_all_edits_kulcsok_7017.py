"""Az Összes szerkesztés visszavonása az eredeti Picasa 3.9 kulcslistáját törli
(#7017, a #7009 összevetése alapján).

Az eredeti képenkénti törlője (`0x005ef6b0`) a `crop`, `flipped`, `filters`,
`redo`, `text` és `textactive` kulcsot veszi le a kép `.picasa.ini`
szakaszából, a `rotate` kulcsot nem. A `Undo Batch Edit` mindegyiket
visszaírja, tehát a törlés nem veszít adatot.

A tesztek valódi `.picasa.ini`-n járják körbe a folyamatot: a vezérlő
`clearAllEffectsMany`/`undoBatchEdit` útja fut, az eredményt az `ini` csomag
olvasója adja vissza.

rontás-kontroll: a `batch_effect_controller._UNDO_ALL_KEYS` listából a `flipped`
kihagyása → test_az_osszes_eredeti_kulcs_torlodik_a_rotate_marad és
test_az_undo_az_osszes_torolt_kulcsot_visszairja bukik.
"""

from __future__ import annotations

import pytest
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op

from picasapy.ini import load_document

_FILTERS = "crop64=1,3f845bcb59418507;"
_CROP = "rect64(3f845bcb59418507)"
_REDO = "sat=1,-0.2;"
_FLIPPED = "flipped(1)"
_TEXT = "text=Synthetic overlay"
_TEXTACTIVE = "1"
_ROTATE = "rotate(1)"

_INI = (
    "[k.jpg]\n"
    f"filters={_FILTERS}\n"
    f"crop={_CROP}\n"
    f"flipped={_FLIPPED}\n"
    f"text={_TEXT}\n"
    f"textactive={_TEXTACTIVE}\n"
    f"redo={_REDO}\n"
    f"rotate={_ROTATE}\n"
    "[m.jpg]\n"
    f"rotate={_ROTATE}\n"
    f"flipped={_FLIPPED}\n"
)

_EREDETI_KULCSOK = {
    "filters": _FILTERS,
    "crop": _CROP,
    "flipped": _FLIPPED,
    "text": _TEXT,
    "textactive": _TEXTACTIVE,
    "redo": _REDO,
}


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    folder = root / "a"
    folder.mkdir(parents=True)
    make_jpeg(folder / "k.jpg", size=(800, 600))
    make_jpeg(folder / "m.jpg", size=(800, 600))
    (folder / ".picasa.ini").write_text(_INI, encoding="utf-8")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "a háttérszál nem állt le"


def _rows(controller, *names) -> list:
    by_name = {p.name: i for i, p in enumerate(controller.photos.photos)}
    return [by_name[name] for name in names]


def _section(library, name) -> dict:
    document = load_document(library / "a" / ".picasa.ini")
    section = document.section(name)
    assert section is not None, f"[{name}] szakasz hiányzik"
    return dict(section.items())


def _undo_all(controller, *names) -> None:
    rows = _rows(controller, *names)
    wait_for_photo_op(controller, lambda: controller.clearAllEffectsMany(rows))


def test_az_osszes_eredeti_kulcs_torlodik_a_rotate_marad(controller, library):
    _undo_all(controller, "k.jpg")

    section = _section(library, "k.jpg")

    assert set(section) == {"rotate", "backuphash"}, section
    assert section["rotate"] == _ROTATE
    assert section["backuphash"].isdecimal()
    assert 0 <= int(section["backuphash"]) <= 0xFFFF


def test_a_tobbi_kep_szakasza_erintetlen(controller, library):
    _undo_all(controller, "k.jpg")

    section = _section(library, "m.jpg")

    assert section == {"rotate": _ROTATE, "flipped": _FLIPPED}


def test_az_undo_az_osszes_torolt_kulcsot_visszairja(controller, library):
    _undo_all(controller, "k.jpg")
    # előfeltétel: a törlés tényleg megtörtént, különben az undo üresen zöld
    assert not set(_EREDETI_KULCSOK) & set(_section(library, "k.jpg"))

    controller.undoBatchEdit()

    section = _section(library, "k.jpg")
    for kulcs, ertek in _EREDETI_KULCSOK.items():
        assert section.get(kulcs) == ertek, f"{kulcs} nem állt vissza: {section}"
    assert section["rotate"] == _ROTATE


def test_az_undo_nem_szul_kulcsot_amely_eredetileg_nem_volt(
    controller, library
):
    """`m.jpg`-nek csak `rotate` és `flipped` kulcsa van: az undo után sem
    jelenhet meg rajta `text`, `textactive`, `redo`, `filters`, `crop`."""
    _undo_all(controller, "m.jpg")
    assert "flipped" not in _section(library, "m.jpg")

    controller.undoBatchEdit()

    section = _section(library, "m.jpg")
    assert section["flipped"] == _FLIPPED
    assert section["rotate"] == _ROTATE
    for kulcs in ("filters", "crop", "text", "textactive", "redo"):
        assert kulcs not in section, f"{kulcs} szellemkulcs az undo után"


def test_az_undo_ketkepes_kijeloleshez_kepenkent_a_sajat_kulcsait_adja_vissza(
    controller, library
):
    _undo_all(controller, "k.jpg", "m.jpg")
    assert set(_section(library, "k.jpg")) == {"rotate", "backuphash"}

    controller.undoBatchEdit()

    k = _section(library, "k.jpg")
    m = _section(library, "m.jpg")
    assert k["flipped"] == _FLIPPED and k["redo"] == _REDO
    assert k["text"] == _TEXT and k["textactive"] == _TEXTACTIVE
    assert "redo" not in m and "text" not in m

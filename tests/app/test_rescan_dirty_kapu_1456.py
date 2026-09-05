"""#1456: a `rescan()` a futó dirty-worker mellé se indítson második írót.

## A lelet

A `rescan()` (`library_controller.py:1091`) csak a `_sync_running`-ot
nézte, a #1440-ben bevezetett `_dirty_running`-ot nem. Ugyanaz a
hibaosztály és ugyanaz a felhasználói tünet, mint a #1440-ben — két
egyidejű index-író, `sqlite3.OperationalError` → `syncFailed` —, csak
másik belépési ponton: az ötperces időzítő és a „Frissítés" menüpont.

Mérve a javítás előtt, blokkolt dirty-worker mellett:

```
["picasapy-sync-dirty", "picasapy-sync-rescan"]
```

## Miért kihagyás, és nem várólista

A rescan úgyis csak KIHAGY: az ötperces időzítő öt perc múlva újra
próbál, és a futó szinkron végén amúgy is frissül a nézet. A #1440
`_pending_dirty` várólistája ott azért kell, mert egy KONKRÉT mappa
jelzése veszne el; itt nincs ilyen — a rescan az egészet nézi.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    for nev in ("nyaralas", "kollazsok"):
        (root / nev).mkdir(parents=True)
        make_jpeg(root / nev / "IMG_0001.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=beallitas,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def test_a_rescan_nem_indit_masodik_irot_futo_dirty_mellett(
    controller, library, monkeypatch
):
    """A `_start_background` csak jegyzetel — így a „még fut az első"
    állapot determinista, valódi időzítés nélkül (a #1440 mintája)."""
    inditasok: list[str | None] = []
    monkeypatch.setattr(
        controller,
        "_start_background",
        lambda *a, **k: inditasok.append(k.get("name")),
    )

    controller._on_folders_dirty([str(library / "nyaralas")])
    assert inditasok == ["picasapy-sync-dirty"], "a felkészítő jelzés nem hatott"

    controller.rescan()

    assert inditasok == ["picasapy-sync-dirty"], (
        "a rescan második index-írót indított a futó dirty-worker mellé — "
        f"indítások: {inditasok}"
    )


def test_a_rescan_a_dirty_utan_ujra_indithato(controller, library, monkeypatch):
    """A kapu nem RAGADHAT BE: a dirty-worker végeztével a rescan megy."""
    inditasok: list[str | None] = []
    monkeypatch.setattr(
        controller,
        "_start_background",
        lambda *a, **k: inditasok.append(k.get("name")),
    )
    controller._on_folders_dirty([str(library / "nyaralas")])
    controller._dirty_running = False  # a worker lefutott

    controller.rescan()

    assert inditasok == ["picasapy-sync-dirty", "picasapy-sync-rescan"], inditasok

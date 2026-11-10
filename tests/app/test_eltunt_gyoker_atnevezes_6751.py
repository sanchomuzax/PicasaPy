"""Az Intézőben átnevezett figyelt mappa régi neve nem ragadhat bent (#6751).

## A tulajdonos jelentése (1.0.85, Windows, OneDrive alatti helyi mappa)

A `202611-a` figyelt mappát (behúzással került fel) az Intézőben
`202611-b`-re nevezte. Az új név megjelent, a régi viszont dőlten bent
maradt, és minden szinkron „a szkennelendő gyökér nem létezik” hibát adott.
Az ok a #1560 védelme: az eltűnt figyelt gyökeret lecsatolt meghajtónak
vette, ezért a sorait nem takarította.

A különbség, amit a #1560 nem tett meg: ha a gyökér SZÜLŐMAPPÁJA megvan és
olvasható, a tároló jelen van, tehát a mappát a felhasználó nevezte át vagy
törölte. Ilyenkor:

* ha a régi mappa fájljai egy testvérmappában vannak, amelyet még semmi nem
  figyel, a program követi az új nevet (#1542 útja);
* különben (a testvér már figyelt, vagy nincs meg) a régi gyökér kikerül.

A lecsatolt meghajtó (a szülő sincs meg) védelme változatlan.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg


def _var(qt_app, feltetel, masodperc: float = 20.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.02)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _mappak(ctl) -> tuple[str, ...]:
    return ctl._folders.folder_paths()


@pytest.fixture
def kepernyokepek(tmp_path):
    szulo = tmp_path / "screenshots"
    a = szulo / "202611-a"
    masik = szulo / "202611"
    a.mkdir(parents=True)
    masik.mkdir()
    for nev in ("k1.jpg", "k2.jpg", "k3.jpg"):
        make_jpeg(a / nev)
    make_jpeg(masik / "m1.jpg")
    return szulo


def _vezerlo(qt_app, tmp_path, gyokerek):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        for gyoker in gyokerek:
            sync_tree(conn, gyoker)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        tuple(str(g) for g in gyokerek),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl.start()
    assert _var(qt_app, lambda: not ctl._sync_running, 20.0)
    return ctl


def _leallit(ctl):
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _ujraolvas(ctl, qt_app):
    assert _var(
        qt_app, lambda: not ctl._sync_running and not ctl._dirty_running, 20.0
    )
    kesz = []
    ctl.syncFinished.connect(lambda: kesz.append(True))
    ctl.rescan()
    assert _var(
        qt_app,
        lambda: bool(kesz) and not ctl._sync_running and not ctl._dirty_running,
        20.0,
    )


def test_atnevezes_mar_figyelt_testverre_a_regi_kikerul(
    qt_app, tmp_path, kepernyokepek
):
    """A tulajdonos esete: a régi és az új név is figyelt gyökér."""
    a = kepernyokepek / "202611-a"
    b = kepernyokepek / "202611-b"
    ctl = _vezerlo(qt_app, tmp_path, (a, kepernyokepek / "202611"))
    try:
        assert str(a) in _mappak(ctl)
        a.rename(b)
        ctl.addWatchedFolder(str(b))
        _ujraolvas(ctl, qt_app)

        assert _var(qt_app, lambda: str(a) not in _mappak(ctl)), (
            "az átnevezett mappa régi neve bent maradt a bal sávban"
        )
        assert str(a) not in ctl._roots
        assert str(b) in _mappak(ctl)
        assert (tmp_path / "WatchedFolders.txt").read_text(
            encoding="utf-8"
        ).count("202611-a") == 0
    finally:
        _leallit(ctl)


def test_atnevezes_nem_figyelt_nevre_kovetve(qt_app, tmp_path, kepernyokepek):
    """Az új név még nem figyelt: a program követi, a sorok átkerülnek."""
    a = kepernyokepek / "202611-a"
    b = kepernyokepek / "202611-b"
    ctl = _vezerlo(qt_app, tmp_path, (a,))
    try:
        a.rename(b)
        _ujraolvas(ctl, qt_app)

        assert _var(qt_app, lambda: str(b) in _mappak(ctl)), (
            "az átnevezett mappát a program nem követte az új nevére"
        )
        assert str(a) not in _mappak(ctl)
        assert [Path(r) for r in ctl._roots] == [b]
    finally:
        _leallit(ctl)


def test_lecsatolt_meghajto_vedelme_megmarad(qt_app, tmp_path, kepernyokepek):
    """Ha a szülő sincs meg (kihúzott meghajtó), a sorok megmaradnak (#1560)."""
    a = kepernyokepek / "202611-a"
    ctl = _vezerlo(qt_app, tmp_path, (a,))
    try:
        import shutil

        shutil.move(str(kepernyokepek), str(tmp_path / "elvitt"))
        _ujraolvas(ctl, qt_app)

        assert str(a) in ctl._roots, "lecsatolt meghajtónál a gyökér kikerült"
        assert str(a) in _mappak(ctl)
    finally:
        _leallit(ctl)

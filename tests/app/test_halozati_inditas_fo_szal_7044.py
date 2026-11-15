"""#7044: hálózati mappával az indulás és a mappára kattintás nem vár a hálózatra.

A tulajdonos Windowson látta: a NAS-mappa mellett az indulás percekig tartott,
a képek nem jelentek meg, a mappára kattintva a program lefagyott. A
`normalize_path`/`path_key` UNC-útvonalon `Path.resolve()`-ot hívott, és az
indulás (`_dedupe_roots`, `merge_duplicate_folders`) meg a gyökérkeresés ezt a
fő szálon, útvonalanként ismételte; minden hívás hálózati körülfordulás.

A rögzítés: a platform Windows (`paths._platform`, #1217), a szervert érintő
feloldás (`paths._feloldas`) lassú és nyilvántartja a hívó szálat, a megosztás
pedig nem válaszol. A fő szálon egyetlen szerver-hívás sem lehet, és a mért idő határon
belül marad."""

from __future__ import annotations

import threading
import time

import pytest

from picasapy import halozati_ut, paths

SZERVER = "ds215j"
GYOKER = "\\\\DS215j\\photo"
MAPPA = GYOKER + "\\2026\\2026-11-14"
KESLELTETES = 0.3
#: egy hálózatra váró hívás ennyit vár; az egész felépítés ennél jóval kevesebbet
HATAR_S = 0.25


@pytest.fixture
def fo_szal_hivasok(monkeypatch):
    """A szervert érintő feloldás lassú; a főszálról jött hívásokat gyűjti."""
    fo_szal = threading.get_ident()
    fo_szali: list[str] = []
    eredeti = paths._feloldas

    def lassu(szoveg):
        if SZERVER in szoveg.lower():
            if threading.get_ident() == fo_szal:
                fo_szali.append(szoveg)
            time.sleep(KESLELTETES)
        return eredeti(szoveg)

    monkeypatch.setattr(paths, "_feloldas", lassu)
    return fo_szali


@pytest.fixture
def halozati_vezerlo(qt_app, tmp_path, monkeypatch):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    monkeypatch.setattr(paths, "_platform", lambda: "win32")
    # a megosztás nem válaszol: a háttér-szinkron nem indít bejárást
    monkeypatch.setattr(halozati_ut, "_letezik", lambda _ut: False)
    halozati_ut._alaphelyzet()
    with open_index(tmp_path / "index.db") as conn:
        for nap in range(40):
            mappa_id = conn.execute(
                "INSERT INTO folders(path, has_ini) VALUES (?, 1) RETURNING id",
                (f"{GYOKER}\\2026\\2026-11-{nap + 1:02d}",),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO photos(folder_id, name, kind, size, mtime_ns)"
                " VALUES (?, 'a.jpg', 'photo', 10, 1)",
                (mappa_id,),
            )
        conn.commit()
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (GYOKER, GYOKER.lower()),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le a teardownban"
    halozati_ut._alaphelyzet()


def test_az_indulasi_gyokerkezeles_nem_er_halozatot(halozati_vezerlo, fo_szal_hivasok):
    kezdet = time.monotonic()
    halozati_vezerlo._dedupe_roots()
    assert halozati_vezerlo._find_root(GYOKER.lower()) == halozati_vezerlo._roots[0]
    assert halozati_vezerlo._root_for_folder(MAPPA) == halozati_vezerlo._roots[0]
    eltelt = time.monotonic() - kezdet

    assert fo_szal_hivasok == []
    assert eltelt < HATAR_S, f"a gyökérkezelés {eltelt:.2f} s-ig várt a hálózatra"
    # a két kis-nagybetűs alakban megadott gyökér egy gyökér
    assert len(halozati_vezerlo._roots) == 1


def test_az_indulas_es_a_mappakattintas_nem_var_a_halozatra(
    qt_app, halozati_vezerlo, fo_szal_hivasok
):
    kezdet = time.monotonic()
    halozati_vezerlo.start()
    halozati_vezerlo.selectFolder(MAPPA)
    eltelt = time.monotonic() - kezdet
    assert halozati_vezerlo.waitForBackgroundWorkers(15.0)
    qt_app.processEvents()

    assert fo_szal_hivasok == [], f"a fő szál hálózati hívása: {fo_szal_hivasok[:3]}"
    assert eltelt < 2.0, f"az indulás és a kattintás {eltelt:.2f} s-ig fogta a fő szálat"
    assert halozati_vezerlo.currentFolder == MAPPA
    # az indexelt mappák az indexből azonnal ott vannak a hasábban
    assert halozati_vezerlo._folders.rowCount() >= 40
    halozati_vezerlo.shutdown()

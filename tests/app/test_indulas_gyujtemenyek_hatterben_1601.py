"""#1601: az induláskori `.picasa.ini`-söprés lekerül a felület száláról.

## Mit mértünk (RPi5, tmpfs, szintetikus index, 2026-08-27)

Az induláskor SZINKRONBAN futó munka szakaszonként, ezredmásodpercben:

| szakasz | 100 mappa | 1 000 mappa | 5 000 mappa |
|---|---|---|---|
| `open_index` | 0,5 | 0,6 | 0,7 |
| `prune_foreign_folders` (#58) | 2,8 | 23,9 | 120,9 |
| `merge_duplicate_folders` (#507) | 3,1 | 29,6 | 154,3 |
| `sorted_folder_rows` (mappafa) | 1,1 | 15,2 | 78,7 |
| `albums_in_index` | 0,4 | 0,9 | 3,5 |
| **`people_in_index` (#26)** | **44,4** | **609,7** | **3 765,0** |
| **`project_folders` (#1029)** | **19,3** | **295,9** | **1 526,7** |

A két ini-olvasó gyűjtemény együtt az összes szinkron munka **94%-a**, és
egyedül ők skálázódnak érdemben — ez a tulajdonos „egyre lassabb"
tapasztalata. NAS-on (ahol a gyűjteménye él) egy fájlnyitás nagyságrenddel
drágább, mint helyben, tehát ott ez még rosszabb.

## Amit ez a teszt őriz

1. **Az indulás nem söpri az ini-ket a hívó szálon** — a `start()` alatt a
   felület szálán NULLA `.picasa.ini`-olvasás történik.
2. **A hasáb attól még feltöltődik** — csak háttérszálról.
3. **Egy söprés, nem kettő** — a szinkron úton is (`index/side_pane.py`).

Az 1. és a 3. pont DARABSZÁMOT állít, nem időt: nem flaky, mégis pontosan
azt fogja meg, ami elromlott.
"""

from __future__ import annotations

import threading

import pytest
from PySide6.QtCore import QSettings

from picasapy.index import folder_ini, open_index, sync_tree
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_RECT = "3f840000c3509f84"
_PROJECTS = "[Picasa]\nP2category=Projects (internal)\n"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    for name in ("nyaralas", "Kollázsok"):
        (root / name).mkdir(parents=True)
        make_jpeg(root / name / "a.jpg", size=(32, 24))
    (root / "nyaralas" / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n",
        encoding="utf-8",
    )
    (root / "Kollázsok" / ".picasa.ini").write_text(_PROJECTS, encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    return root


@pytest.fixture
def sopres_naplo(monkeypatch):
    """Minden ini-söprés-olvasás (szál, útvonal) párja."""
    eredeti = folder_ini.load_document
    naplo: list[tuple[int, str]] = []

    def szamlalo(path):
        naplo.append((threading.get_ident(), str(path)))
        return eredeti(path)

    monkeypatch.setattr(folder_ini, "load_document", szamlalo)
    return naplo


def _controller(tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )


@pytest.fixture
def controller(qt_app, tmp_path, library):
    instance = _controller(tmp_path, library)
    yield instance
    instance.shutdown()
    instance.waitForBackgroundWorkers(20.0)


class TestIndulasNemBlokkol:
    def test_a_start_nem_olvas_ini_t_a_felulet_szalan(
        self, controller, qt_app, sopres_naplo
    ):
        """A jegy magja: az induláskori söprés NEM a felület szálán fut.

        A `start()` visszatérése után a naplóban a HÍVÓ szálhoz tartozó
        bejegyzések száma nulla — a munka háttérszálra került."""
        fo_szal = threading.get_ident()
        controller.start()
        qt_app.processEvents()

        a_felulet_szalan = [item for item in sopres_naplo if item[0] == fo_szal]
        assert a_felulet_szalan == [], (
            "az induláskori .picasa.ini-söprés a felület szálán futott — "
            f"{len(a_felulet_szalan)} olvasás"
        )

    def test_a_hasab_gyujtemenyei_a_hatterben_feltoltodnek(
        self, controller, qt_app
    ):
        """A halasztás nem lehet elhagyás: az Emberek és a Projektek
        gyűjtemény a háttérmunka lefutása után MEGVAN."""
        controller.start()
        assert controller.waitForBackgroundWorkers(20.0)
        for _ in range(20):
            qt_app.processEvents()
            if controller.people and controller.projectFolders:
                break

        assert controller.people == [{"name": "Roy Avery", "count": 1}]
        assert [row["name"] for row in controller.projectFolders] == ["Kollázsok"]

    def test_a_hatterbeli_sopres_is_mappankent_egyszer_olvas(
        self, controller, qt_app, sopres_naplo
    ):
        """A háttérre tolt munka se legyen kétszeres: a két gyűjtemény
        EGY söprésből él (#1601, `index/side_pane.py`)."""
        controller.start()
        assert controller.waitForBackgroundWorkers(20.0)
        qt_app.processEvents()

        utvonalak = [path for _szal, path in sopres_naplo]
        assert len(utvonalak) == len(set(utvonalak)), (
            f"minden ini-t egyszer kell olvasni, mégis: {utvonalak}"
        )

    def test_a_szinkron_vegi_frissites_sem_sopor_a_felulet_szalan(
        self, controller, qt_app, sopres_naplo
    ):
        """A TELJES indulási kör (szinkron + az utána futó `_reload`) alatt
        a felület szála egyetlen `.picasa.ini`-t sem olvas.

        ⚠️ Ez az őr fedi le a `_sync_worker`-beli `_precompute_side_pane`
        hívást: nélküle a `syncFinished` utáni `_reload()` a felület szálán
        söpörné végig az egész könyvtárat — a `start()`-ot néző, szűkebb
        teszt ezt még nem venné észre, mert a szinkron akkor még futhat."""
        fo_szal = threading.get_ident()
        controller.start()
        assert controller.waitForBackgroundWorkers(20.0)
        for _ in range(20):
            qt_app.processEvents()
            if controller.people:
                break

        assert controller.people, "a gyűjtemények nem töltődtek fel"
        a_felulet_szalan = [item for item in sopres_naplo if item[0] == fo_szal]
        assert a_felulet_szalan == [], (
            "a szinkron utáni frissítés a felület szálán söpörte az ini-ket "
            f"({len(a_felulet_szalan)} olvasás) — a `_sync_worker` nem adta "
            "át az előre kiszámolt gyűjteményeket"
        )


class TestSzinkronUtVáltozatlanulMukodik:
    """A `_reload()` alapértelmezett (nem halasztó) útja változatlan —
    erre épül a #1029 és a #26 összes meglévő tesztje."""

    def test_a_reload_after_sync_feltolti_a_gyujtemenyeket(
        self, controller, qt_app
    ):
        controller._reload_after_sync()
        assert controller.people == [{"name": "Roy Avery", "count": 1}]
        assert [row["name"] for row in controller.projectFolders] == ["Kollázsok"]

    def test_a_szinkron_ut_is_egy_sopressel_dolgozik(
        self, controller, qt_app, sopres_naplo
    ):
        controller._reload_after_sync()
        utvonalak = [path for _szal, path in sopres_naplo]
        assert len(utvonalak) == 2, (
            f"két ini-s mappa → két olvasás, mégis: {utvonalak}"
        )

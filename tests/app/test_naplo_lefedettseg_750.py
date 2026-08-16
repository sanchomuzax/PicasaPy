"""A szerkesztés-napló (#644) lefedettsége MINDEN lánc-íróra — #750.

## Miért ez a teszt

A #643 élesben igazolta: a párhuzamosan futó eredeti Picasa a fotó
`.picasa.ini`-szakaszát a saját `db3`-rekordjából írja ki **egészben**, nem
kulcsonként fésüli össze — a mi `filters=` láncunk ilyenkor némán eltűnik.
A #644-es napló ezt hivatott észlelni és helyreállítani, csakhogy egyetlen
írót táplált (`edit_controller._save()` → `chainSaved`).

Ez a teszt a másik NÉGY írót rögzíti szerződésként:

1. `batch_effect_controller` — csoportos effekt (és az „Undo All Edits"),
2. `effects_controller.pasteEffects` — Paste All Effects (#152),
3. `photo_ops_controller.pasteAllEffects` — „Az összes effektus
   beillesztése" (#426),
4. `save_controller` — a lemezre mentés (`edit/save.py`, `redo=`) és az
   „Utolsó mentés visszavonása".

Mindegyik írónál KÉT dolgot állítunk: a napló tartalmazza-e a láncot, és a
`detect_lost_edits`/`editsOverwritten` út talál-e, ha a Picasa utóbb
felülír. A napló tartalma önmagában kevés — a #699 tanulsága szerint egy
eltérő kulcsképzés némán kiütné a védelmet, ezért a felülírás-próba is kell.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_signal

from picasapy.app.edit_journal_controller import JOURNAL_FILENAME
from picasapy.edit.edit_journal import load_journal
from picasapy.index import open_index, sync_tree

SAT = "sat=1,-0.2;"


@pytest.fixture
def library(tmp_path):
    """Két mappa, hogy a mappánkénti kötegelt írás is szóhoz jusson."""
    root = tmp_path / "kepek"
    folder_a = root / "a"
    folder_b = root / "b"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    make_jpeg(folder_a / "x.jpg", size=(64, 48))
    make_jpeg(folder_a / "y.jpg", size=(64, 48))
    make_jpeg(folder_b / "z.jpg", size=(64, 48))
    (folder_a / ".picasa.ini").write_text(
        f"[x.jpg]\nfilters={SAT}\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

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


def _naplo(controller) -> dict:
    return load_journal(Path(controller._db_path).parent / JOURNAL_FILENAME)


def _kulcs(library, mappa: str, nev: str) -> str:
    """A napló kulcsa — UGYANAZ a szabály, amit a `full_path()` használ."""
    return str(Path(library) / mappa / nev)


def _sorok(controller, *nevek) -> list[int]:
    photos = controller.photos.photos
    by_name = {p.name: i for i, p in enumerate(photos)}
    return [by_name[nev] for nev in nevek]


def _picasa_felulir(controller, library, mappa: str, ini_tartalom: str) -> list:
    """A párhuzamos Picasa viselkedése: a szakaszt EGÉSZBEN újraírja.

    Visszaadja az `editsOverwritten` jelzéseit — a nézetfrissítés (ahol a
    `_check_external_overwrites` fut) itt zajlik le.
    """
    (Path(library) / mappa / ".picasa.ini").write_text(
        ini_tartalom, encoding="utf-8"
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, Path(library))
    kapott: list = []
    controller.editsOverwritten.connect(kapott.append)
    controller._reload()
    controller.selectFolder(str(library))
    return kapott


class TestCsoportosEffekt:
    """`batch_effect_controller.applyEffectMany` — a legtömegesebb író."""

    def test_a_kotegelt_effekt_naploz(self, controller, library):
        wait_for_signal(
            controller.photoOpFinished,
            lambda: controller.applyEffectMany(
                _sorok(controller, "x.jpg", "y.jpg", "z.jpg"), "autolight"
            ),
            description="a csoportos effekt",
        )

        naplo = _naplo(controller)
        assert naplo[_kulcs(library, "a", "x.jpg")].chain == f"{SAT}autolight=1;"
        assert naplo[_kulcs(library, "a", "y.jpg")].chain == "autolight=1;"
        assert naplo[_kulcs(library, "b", "z.jpg")].chain == "autolight=1;"

    def test_a_felulirast_eszleli(self, controller, library):
        wait_for_signal(
            controller.photoOpFinished,
            lambda: controller.applyEffectMany(
                _sorok(controller, "x.jpg"), "autolight"
            ),
            description="a csoportos effekt",
        )

        kapott = _picasa_felulir(
            controller, library, "a", "[x.jpg]\nstar=yes\n"
        )

        assert [t["name"] for lista in kapott for t in lista] == ["x.jpg"]

    def test_a_mindent_vissza_torli_a_bejegyzest(self, controller, library):
        """„Undo All Edits": a felhasználó MAGA törölt — nincs mit védeni."""
        wait_for_signal(
            controller.photoOpFinished,
            lambda: controller.applyEffectMany(
                _sorok(controller, "x.jpg"), "autolight"
            ),
            description="a csoportos effekt",
        )
        wait_for_signal(
            controller.photoOpFinished,
            lambda: controller.clearAllEffectsMany(_sorok(controller, "x.jpg")),
            description="az összes szerkesztés visszavonása",
        )

        assert _kulcs(library, "a", "x.jpg") not in _naplo(controller)

    def test_a_koteg_visszavonasa_visszairja_a_naplot(self, controller, library):
        """A visszavont köteg után a napló a VISSZAÁLLÍTOTT láncot védi."""
        wait_for_signal(
            controller.photoOpFinished,
            lambda: controller.applyEffectMany(
                _sorok(controller, "x.jpg"), "autolight"
            ),
            description="a csoportos effekt",
        )

        controller.undoBatchEdit()

        assert _naplo(controller)[_kulcs(library, "a", "x.jpg")].chain == SAT


class TestEffektVagolap:
    """`effects_controller.pasteEffects` — Paste All Effects (#152)."""

    def test_a_beillesztes_naploz(self, controller, library):
        controller.copyEffects(_sorok(controller, "x.jpg"))
        controller.pasteEffects(_sorok(controller, "y.jpg"))

        assert _naplo(controller)[_kulcs(library, "a", "y.jpg")].chain == SAT

    def test_a_felulirast_eszleli(self, controller, library):
        controller.copyEffects(_sorok(controller, "x.jpg"))
        controller.pasteEffects(_sorok(controller, "y.jpg"))

        kapott = _picasa_felulir(
            controller, library, "a", f"[x.jpg]\nfilters={SAT}\n[y.jpg]\nstar=yes\n"
        )

        assert [t["name"] for lista in kapott for t in lista] == ["y.jpg"]

    def test_a_visszavonas_visszairja_a_naplot(self, controller, library):
        controller.copyEffects(_sorok(controller, "x.jpg"))
        controller.pasteEffects(_sorok(controller, "y.jpg"))

        controller.undoPasteEffects()

        assert _kulcs(library, "a", "y.jpg") not in _naplo(controller)


class TestOsszesEffektBeillesztese:
    """`photo_ops_controller.pasteAllEffects` — #426."""

    def test_a_beillesztes_naploz(self, controller, library):
        controller.copyAllEffects(_sorok(controller, "x.jpg"))
        controller.pasteAllEffects(_sorok(controller, "z.jpg"))

        assert _naplo(controller)[_kulcs(library, "b", "z.jpg")].chain == SAT

    def test_a_felulirast_eszleli(self, controller, library):
        controller.copyAllEffects(_sorok(controller, "x.jpg"))
        controller.pasteAllEffects(_sorok(controller, "z.jpg"))

        kapott = _picasa_felulir(
            controller, library, "b", "[z.jpg]\nstar=yes\n"
        )

        assert [t["name"] for lista in kapott for t in lista] == ["z.jpg"]

    def test_a_visszavonas_visszairja_a_naplot(self, controller, library):
        controller.copyAllEffects(_sorok(controller, "x.jpg"))
        controller.pasteAllEffects(_sorok(controller, "z.jpg"))

        controller.undoPasteAllEffects()

        assert _kulcs(library, "b", "z.jpg") not in _naplo(controller)


class TestLemezreMentes:
    """`save_controller` — a `redo=` írása (`edit/save.py`).

    A mentés a láncot a pixelekbe égeti, a `filters=`-t TÖRLI, és a `redo=`-ba
    forgatja át. A naplónak követnie kell: enélkül a következő
    nézetfrissítés HAMIS riasztást adna („a szerkesztésed eltűnt"), holott
    mi magunk vittük el.
    """

    def test_a_mentes_torli_a_bejegyzest(self, controller, library):
        controller.copyEffects(_sorok(controller, "x.jpg"))
        controller.pasteEffects(_sorok(controller, "y.jpg"))
        assert _kulcs(library, "a", "y.jpg") in _naplo(controller)

        wait_for_signal(
            controller.saveFinished,
            lambda: controller.saveRowsToDisk(_sorok(controller, "y.jpg")),
            description="a lemezre mentés",
        )

        assert _kulcs(library, "a", "y.jpg") not in _naplo(controller)

    def test_a_mentes_utan_nincs_hamis_riasztas(self, controller, library):
        controller.copyEffects(_sorok(controller, "x.jpg"))
        controller.pasteEffects(_sorok(controller, "y.jpg"))
        wait_for_signal(
            controller.saveFinished,
            lambda: controller.saveRowsToDisk(_sorok(controller, "y.jpg")),
            description="a lemezre mentés",
        )

        kapott: list = []
        controller.editsOverwritten.connect(kapott.append)
        with open_index(controller._db_path) as conn:
            sync_tree(conn, Path(library))
        controller._reload()
        controller.selectFolder(str(library))

        assert kapott == []

    def test_a_mentes_visszavonasa_ujra_naploz(self, controller, library):
        controller.copyEffects(_sorok(controller, "x.jpg"))
        controller.pasteEffects(_sorok(controller, "y.jpg"))
        wait_for_signal(
            controller.saveFinished,
            lambda: controller.saveRowsToDisk(_sorok(controller, "y.jpg")),
            description="a lemezre mentés",
        )

        wait_for_signal(
            controller.undoSaveFinished,
            lambda: controller.undoLastSave(_sorok(controller, "y.jpg")),
            description="az utolsó mentés visszavonása",
        )

        assert _naplo(controller)[_kulcs(library, "a", "y.jpg")].chain == SAT

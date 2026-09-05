"""#1458 — a várólistára tett FELHASZNÁLÓI frissítés is látszódjon.

A #1440 óta a futó író mellett érkező mappa-jelzés nem vész el: a
`_pending_dirty` halmazba kerül, és a szinkron végén lefut. A kérés tehát
megvan — de a felhasználó ebből SEMMIT nem lát. Rákattint a „Frissítés"-re,
és lassú hálózati köteten fél percig nem történik semmi látható.

A megoldás nem új felületi elem: a `_start_background` úgyis bejelentkezik az
alkalmazás foglaltság-nyilvántartójába (a kék sáv), csak a várólistás ágon
nem indul szál, tehát nincs mit bejelenteni. Itt ezért MAGA a várólistára
tétel jelentkezik be, és a `_flush_pending_dirty` zárja a bejegyzést.

⚠️ Az AUTOMATIKUS (figyelőből jövő) jelzésre ez NEM jár: ott nincs
kattintás, amire válaszolni kellene, és a folyamatosan pörgő sáv zavaró
lenne. A két utat a `felhasznaloi` kapcsoló választja szét.
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

    from picasapy.app.busy_registry import reset_app_busy_registry
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    reset_app_busy_registry()
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
    reset_app_busy_registry()


@pytest.fixture
def foglalt():
    from picasapy.app.busy_registry import get_app_busy_registry

    return get_app_busy_registry()


@pytest.fixture
def nincs_szalinditas(controller, monkeypatch):
    """A `_start_background` csak jegyzetel — a várólistás ág determinista."""
    monkeypatch.setattr(controller, "_start_background", lambda *a, **k: None)


class TestAFelhasznaloiKeresLatszik:
    def test_a_varolistara_tett_frissites_bejelentkezik(
        self, controller, library, foglalt, nincs_szalinditas
    ):
        controller._dirty_running = True  # fut egy másik író
        elotte = foglalt.activeCount

        controller.resyncFolder(str(library / "nyaralas"))

        assert controller._pending_dirty, "a kérés nem került várólistára"
        assert foglalt.activeCount == elotte + 1, (
            "a felhasználó rákattintott a Frissítésre, a kérés várólistára "
            "került, és semmi nem jelzi, hogy történik valami"
        )

    def test_a_bejegyzes_a_kiuritessel_zarul(
        self, controller, library, foglalt, nincs_szalinditas
    ):
        controller._dirty_running = True
        elotte = foglalt.activeCount
        controller.resyncFolder(str(library / "nyaralas"))
        assert foglalt.activeCount == elotte + 1

        controller._dirty_running = False
        controller._flush_pending_dirty()

        assert foglalt.activeCount == elotte, (
            "a foglaltság-bejegyzés nyitva maradt — a kék sáv örökre pörögne"
        )

    def test_tobb_keres_tobb_bejegyzes(
        self, controller, library, foglalt, nincs_szalinditas
    ):
        controller._dirty_running = True
        elotte = foglalt.activeCount

        controller.resyncFolder(str(library / "nyaralas"))
        controller.resyncFolder(str(library / "kollazsok"))

        assert foglalt.activeCount == elotte + 2

        controller._dirty_running = False
        controller._flush_pending_dirty()
        assert foglalt.activeCount == elotte


class TestAzAutomatikusJelzesNEMJelentkezikBe:
    def test_a_figyelo_jelzese_nem_pörgeti_a_savot(
        self, controller, library, foglalt, nincs_szalinditas
    ):
        """A watcher a `_on_folders_dirty`-t kapcsolatból hívja, argumentum
        nélkül — ott nincs kattintás, amire válaszolni kellene."""
        controller._dirty_running = True
        elotte = foglalt.activeCount

        controller._on_folders_dirty([str(library / "nyaralas")])

        assert controller._pending_dirty, "a jelzés így is várólistára kerül"
        assert foglalt.activeCount == elotte, (
            "az automatikus figyelő-jelzés nem indíthat foglaltság-jelzést"
        )

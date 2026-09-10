"""#2900 — a megszakítás-kérés MINDIG választ kap.

A main CI linuxos lába vörös volt: a `test_cancel_button_stops_the_scan`
15 másodpercet várt a `scanCancelled()`-re, és nem jött meg.

**MÉRVE (2026-09-11), és ez a jegy első kérdése:** a jelzés nem KÉSETT, hanem
**ELMARADT.** A régi `cancelScan()` csak akkor tett bármit, ha épp futott
keresés (`_stop_event is not None`); pár apró képen viszont a keresés a
„scan" és a „cancel" kattintás KÖZÖTT befejeződött, tehát a kérés némán
elveszett — a felület `scanning` jelzője csak a `scanFinished`-től tisztult,
a jelzésre váró hívó pedig időtúllépésbe futott.

A javítás: nincs futó keresés ⇒ a jelzést a `cancelScan` maga bocsátja ki. A
jelzés nem hazudik (a keresés valóban nem fut), és a `DedupDialog` kezelője
csak a `scanning` jelzőt oltja el — a talált csoportokat nem törli.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg
from support.qt_wait import hangos_hurok


@pytest.fixture
def provider(tmp_path):
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    return ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))


@pytest.fixture
def dedup(qt_app, tmp_path, provider):
    """Két bitre azonos képpel — a keresés így tényleg talál valamit."""
    from picasapy.app.dedup_controller import DedupController

    lib = tmp_path / "kepek"
    lib.mkdir()
    elso = make_jpeg(lib / "a.jpg", size=(40, 20))
    (lib / "b.jpg").write_bytes(elso.read_bytes())
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)
    ctl = DedupController(db, provider)
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), (
        "a dedup-keresés háttérszála nem állt le"
    )


class TestAKeresNelkuliMegszakitas:
    def test_futo_keres_NELKUL_is_megjon_a_jelzes(self, dedup, qt_app):
        """Ez a CI-bukás magja: a kérés a keresés vége UTÁN ér ide."""
        loop = hangos_hurok(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        jelek = []
        dedup.scanCancelled.connect(lambda: jelek.append("cancelled"))
        dedup.cancelScan()
        qt_app.processEvents()

        assert jelek == ["cancelled"], (
            "a megszakítás-kérés válasz nélkül maradt — a felület `scanning` "
            "jelzője beragadna, és a jelzésre váró hívó időtúllépésbe fut "
            "(#2900)"
        )

    def test_keres_NELKUL_sem_hibazik_es_azonnal_valaszol(self, dedup, qt_app):
        """Egyetlen keresés sem indult — a kérés akkor is válaszol."""
        jelek = []
        dedup.scanCancelled.connect(lambda: jelek.append("cancelled"))
        dedup.cancelScan()
        qt_app.processEvents()

        assert jelek == ["cancelled"]


class TestAFutoKeresMegszakitasa:
    def test_a_futo_kereses_megszakitasa_valtozatlan(self, dedup, qt_app):
        """Regresszió: a MEGSZAKÍTOTT futás továbbra is a workerből jelez, és
        eredményt NEM ad."""
        jelek = []
        dedup.scanCancelled.connect(lambda: jelek.append("cancelled"))
        dedup.scanFinished.connect(lambda groups: jelek.append("finished"))

        dedup.scanForDuplicates()
        dedup.cancelScan()
        assert dedup.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        assert "cancelled" in jelek
        assert "finished" not in jelek, (
            "a megszakított keresés eredményt adott — a részleges "
            "csoportosítás félrevezető lenne"
        )


class TestAzUjKeresesNEM_megszakitas:
    def test_az_uj_kereses_inditasa_NEM_bocsat_ki_cancelled_t(
        self, dedup, qt_app
    ):
        """Ez a javítás csapdája, amit a mérés fogott meg: az új keresés is
        leállítja az előzőt („egyszerre csak egy fusson"), de az NEM
        megszakítás-kérés. Ha ott a `cancelScan` futna, minden induló
        keresés kibocsátana egy hazug `scanCancelled`-t."""
        loop = hangos_hurok(dedup.scanFinished)
        dedup.scanForDuplicates()
        loop.exec()

        jelek = []
        dedup.scanCancelled.connect(lambda: jelek.append("cancelled"))
        masodik = hangos_hurok(dedup.scanFinished)
        dedup.scanForDuplicates()
        masodik.exec()

        assert jelek == [], (
            "az induló keresés hazug megszakítás-jelzést adott (#2900)"
        )

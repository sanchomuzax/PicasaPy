"""#3751 — a mentés-üzemmód képrács-szűrője a vezérlő oldalán.

A `backuptext2` („A Picasa most azokat a FÁJLOKAT jeleníti meg, amelyekről
korábban nem készült biztonsági másolat") fájlra szól, nem mappára: egy
részben elmentett mappából csak a még el nem mentett képek maradhatnak a
rácson. A szűrés ezért a `photos`/`feedGroups` páros ELŐÁLLÍTÁSAKOR történik
(`AppController._show`, a rejtett képek és a bezárt gyűjtemények mintájára),
így a sorindexek, a csoportok `start`/`count`-ja, a navigáció és a néző
lapozása egyszerre a szűrt listára mutat.

A lista forrása a `BackupController._mentetlen_sorok` — soronként a
csonkítatlan `utak` is benne van (a `fajlok` csak az első húsz név).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_signal


@pytest.fixture
def konyvtar(tmp_path):
    gyoker = tmp_path / "kepek"
    for mappa, fajlok in {
        "elmentett": ("a.jpg", "b.jpg"),
        "vegyes": ("c.jpg", "d.jpg", "e.jpg"),
        "friss": ("f.jpg",),
    }.items():
        (gyoker / mappa).mkdir(parents=True)
        for fajl in fajlok:
            make_jpeg(gyoker / mappa / fajl)
    return gyoker


@pytest.fixture
def controller(qt_app, tmp_path, konyvtar):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, konyvtar)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(konyvtar),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(konyvtar / "elmentett"))
    yield ctl
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _nevek(controller) -> list[str]:
    return [r.name for r in controller.photos.photos]


def _utak(konyvtar, *nevek) -> list[str]:
    return [
        str(p) for p in sorted(konyvtar.rglob("*.jpg")) if p.name in nevek
    ]


class TestARacsFajlSzerintSzukul:
    def test_szuro_nelkul_minden_kep_latszik(self, controller):
        assert controller.backupFilterActive is False
        assert sorted(_nevek(controller)) == [
            "a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg", "f.jpg",
        ]

    def test_reszben_mentett_mappabol_csak_a_mentetlen_fajl(
        self, controller, konyvtar
    ):
        controller.setBackupFilter(_utak(konyvtar, "e.jpg", "f.jpg"))

        assert controller.backupFilterActive is True
        assert sorted(_nevek(controller)) == ["e.jpg", "f.jpg"]
        csoportok = {c["name"]: c for c in controller.feedGroups}
        assert set(csoportok) == {"vegyes", "friss"}
        assert csoportok["vegyes"]["count"] == 1
        vegyes = csoportok["vegyes"]
        assert controller.photos.photos[vegyes["start"]].name == "e.jpg"

    def test_a_csoportok_start_count_a_szurt_listara_mutat(
        self, controller, konyvtar
    ):
        controller.setBackupFilter(_utak(konyvtar, "d.jpg", "e.jpg", "f.jpg"))
        csoportok = controller.feedGroups
        assert sum(c["count"] for c in csoportok) == controller.photos.rowCount()
        vart = 0
        for csoport in csoportok:
            assert csoport["start"] == vart
            vart += csoport["count"]

    def test_ures_lista_ures_racs(self, controller):
        controller.setBackupFilter([])
        assert controller.backupFilterActive is True
        assert controller.photos.rowCount() == 0
        assert controller.feedGroups == []

    def test_bezaraskor_minden_visszajon(self, controller, konyvtar):
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        controller.clearBackupFilter()
        assert controller.backupFilterActive is False
        assert controller.photos.rowCount() == 6

    def test_hatter_frissites_megtartja_a_szurot(self, controller, konyvtar):
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        controller._reload(preserve_scroll=True)
        assert _nevek(controller) == ["f.jpg"]

    def test_mappavaltas_gyorsutja_nem_hagyja_ki_a_szurot(
        self, controller, konyvtar
    ):
        """#142: a mappaváltás-gyorsút a TELJES feedre érvényes — a szűrt
        rácsot nem tekintheti annak."""
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        controller.selectFolder(str(konyvtar / "friss"))
        assert _nevek(controller) == ["f.jpg"]
        controller.clearBackupFilter()
        controller.selectFolder(str(konyvtar / "elmentett"))
        assert controller.photos.rowCount() == 6


class TestAJelzesekSorrendje:
    """A rács a jelzésből tudja, mikor kell a mentés előtti görgetési
    horgonyt eltennie, és mikor visszaállítania."""

    def _naplo(self, controller) -> list[str]:
        naplo: list[str] = []
        controller.backupFilterChanged.connect(lambda: naplo.append("szuro"))
        controller.feedChanged.connect(lambda: naplo.append("feed"))
        return naplo

    def test_bekapcsolaskor_a_szuro_jelzes_elobb_jon(self, controller, konyvtar):
        naplo = self._naplo(controller)
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        assert naplo == ["szuro", "feed"]

    def test_uj_listanal_is_a_szuro_jelzes_jon_elobb(self, controller, konyvtar):
        """Másik készlet, vagy a mentés utáni újraszámolás: a rács új
        tartalma is a tetejéről indul."""
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        naplo = self._naplo(controller)
        controller.setBackupFilter(_utak(konyvtar, "e.jpg", "f.jpg"))
        assert naplo == ["szuro", "feed"]

    def test_kikapcsolaskor_a_szuro_jelzes_utobb_jon(self, controller, konyvtar):
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        naplo = self._naplo(controller)
        controller.clearBackupFilter()
        assert naplo == ["feed", "szuro"]

    def test_azonos_listara_nincs_ujrarajzolas(self, controller, konyvtar):
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        naplo = self._naplo(controller)
        controller.setBackupFilter(_utak(konyvtar, "f.jpg"))
        assert naplo == []

    def test_szuro_nelkul_a_torles_nema(self, controller):
        naplo = self._naplo(controller)
        controller.clearBackupFilter()
        assert naplo == []


class TestAMentesVezerloTeljesUtlistat_Ad:
    def test_az_utak_csonkitatlanok(self, qt_app, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "picasapy.app.backup_controller._kepek_mappaja",
            lambda: str(tmp_path / "Kepek"),
        )
        from picasapy.app.backup_controller import BackupController
        from picasapy.index import open_index, sync_tree

        gyoker = tmp_path / "sok"
        (gyoker / "tele").mkdir(parents=True)
        for i in range(25):
            make_jpeg(gyoker / "tele" / f"k{i:02d}.jpg")
        db = tmp_path / "sok.db"
        with open_index(db) as conn:
            sync_tree(conn, gyoker)
        vezerlo = BackupController(db, (str(gyoker),))
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden")
        azonosito = vezerlo.keszletek()[0]["id"]

        kapott: list = []
        vezerlo.mentetlenMappakKeszek.connect(
            lambda _k, _a, sorok: kapott.append(list(sorok))
        )
        wait_for_signal(
            vezerlo.mentetlenMappakKeszek,
            lambda: vezerlo.mentetlenMappakLekerese(azonosito),
            description="a mentetlen mappák lekérdezése",
        )
        assert vezerlo.waitForBackgroundWorkers(20.0)
        sor = kapott[-1][0]
        assert len(sor["fajlok"]) == 20
        assert sor["utak"] == [
            str(gyoker / "tele" / f"k{i:02d}.jpg") for i in range(25)
        ]

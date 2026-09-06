"""#2506 — négy védtelen `.picasa.ini`-író hívás: a hiba NE legyen néma.

Ugyanaz a hibaosztály, amit a #2497 az „Minden effekt beillesztése"
útvonalon javított: írásvédett mappán vagy tele lemezen a kivétel a
QML-slotból szökik ki, a felület pedig már az ÚJ állapotot mutatja — a
felhasználó azt hiszi, mentett, közben a `.picasa.ini`-be nem került ki
semmi, és a párhuzamosan futó Picasa sem fogja látni.

A négy hely (mérve a #2497 körében):

| hely | mit ír |
|---|---|
| `controller.py` `setFolderDescription` | a mappa leírása |
| `folder_date_controller.py` `setFolderDate` | a mappa-dátum felülbírálása |
| `folder_date_controller.py` `clearFolderDate` | ugyanaz, a törlés ága |
| `keywords_controller.py` `applyKeywords` | a kulcsszavak |

A csatorna a MEGLÉVŐ (#459): `photoOpFailed` → `syncFailed` → `Main.qml`
`errorBanner`. Új csatornát nem vezetünk be.

⚠️ Két állítás kell hívásonként, nem egy:
1. a slot NEM dob (a QML-ből hívott slotból kiszökő kivétel a Qt-ben
   némán elnyelődik vagy a konzolra megy — a felhasználó nem látja);
2. a hiba MEGJELENIK a `photoOpFailed`-en (a bannerhez ez visz el).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "x.jpg", size=(120, 90))
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


def _torj_el(monkeypatch, modul: str, uzenet: str) -> None:
    """Az ini-írás bukása — a valóságban írásvédett mappa vagy tele lemez."""

    def bukik(*_args, **_kwargs):
        raise OSError(uzenet)

    monkeypatch.setattr(f"picasapy.app.{modul}.update_document", bukik)


class TestMappaLeiras:
    def test_az_iras_bukasa_LATHATO(self, controller, monkeypatch, library):
        hibak: list[str] = []
        controller.photoOpFailed.connect(hibak.append)
        _torj_el(monkeypatch, "controller", "teszt: írásvédett mappa")

        controller.setFolderDescriptionOf(str(library), "új leírás")

        assert hibak, "a mappa-leírás írási hibája NÉMÁN futott le"
        assert "teszt: írásvédett mappa" in hibak[0]

    def test_bukas_utan_a_felulet_NEM_mutatja_az_uj_allapotot(
        self, controller, monkeypatch, library
    ):
        """A #2497 tanulsága: nem elég jelezni — a nézet sem hazudhat."""
        _torj_el(monkeypatch, "controller", "teszt: tele a lemez")

        controller.setFolderDescriptionOf(str(library), "sosem mentett szöveg")

        assert (
            controller.folderDescriptionOf(str(library)) != "sosem mentett szöveg"
        ), "a felület a soha ki nem írt leírást mutatja"


class TestMappaDatum:
    def test_a_beallitas_bukasa_LATHATO(self, controller, monkeypatch, library):
        hibak: list[str] = []
        controller.photoOpFailed.connect(hibak.append)
        _torj_el(monkeypatch, "folder_date_controller", "teszt: dátum-írás bukott")

        controller.setFolderDate(str(library), "2020-01-02")

        assert hibak, "a mappa-dátum írási hibája NÉMÁN futott le"
        assert "teszt: dátum-írás bukott" in hibak[0]

    def test_a_torles_bukasa_LATHATO(self, controller, monkeypatch, library):
        hibak: list[str] = []
        controller.photoOpFailed.connect(hibak.append)
        _torj_el(monkeypatch, "folder_date_controller", "teszt: törlés bukott")

        controller.clearFolderDate(str(library))

        assert hibak, "a mappa-dátum törlésének írási hibája NÉMÁN futott le"
        assert "teszt: törlés bukott" in hibak[0]

    def test_bukott_iras_utan_NINCS_ujraszinkron(
        self, controller, monkeypatch, library
    ):
        """A `resyncFolder` a nézetet a lemez állapotára húzza — ha az írás
        elbukott, a lemezen a RÉGI érték van, tehát a szinkron csak
        felesleges munka; a lényeg, hogy a slot nem dob."""
        _torj_el(monkeypatch, "folder_date_controller", "teszt: bukás")
        controller.setFolderDate(str(library), "2020-01-02")
        assert controller.folderDateOverride(str(library)) == ""


class TestKulcsszavak:
    def test_az_iras_bukasa_LATHATO(self, controller, monkeypatch, library):
        hibak: list[str] = []
        controller.photoOpFailed.connect(hibak.append)
        # a PNG-re esik az ini-ág; a JPEG-nél az IPTC-írás megy előbb, ezért
        # azt is elrontjuk, hogy biztosan az ini-ágra fusson
        monkeypatch.setattr(
            "picasapy.app.keywords_controller.write_iptc_keywords",
            lambda *_a, **_k: False,
        )
        _torj_el(monkeypatch, "keywords_controller", "teszt: kulcsszó-írás bukott")

        controller.addKeywordToRows([0], "nyaralas")

        assert hibak, "a kulcsszó-írás hibája NÉMÁN futott le"
        assert "teszt: kulcsszó-írás bukott" in hibak[0]

    def test_a_slot_NEM_dob(self, controller, monkeypatch):
        monkeypatch.setattr(
            "picasapy.app.keywords_controller.write_iptc_keywords",
            lambda *_a, **_k: False,
        )
        _torj_el(monkeypatch, "keywords_controller", "teszt: bukás")
        controller.addKeywordToRows([0], "a")  # nem dobhat


class TestASlotokNemDobnak:
    """Együtt: a QML-ből hívott slotokból NEM szökhet ki kivétel."""

    def test_mind_a_negy(self, controller, monkeypatch, library):
        _torj_el(monkeypatch, "controller", "teszt")
        _torj_el(monkeypatch, "folder_date_controller", "teszt")
        _torj_el(monkeypatch, "keywords_controller", "teszt")
        monkeypatch.setattr(
            "picasapy.app.keywords_controller.write_iptc_keywords",
            lambda *_a, **_k: False,
        )
        controller.setFolderDescriptionOf(str(library), "x")
        controller.setFolderDate(str(library), "2020-01-02")
        controller.clearFolderDate(str(library))
        controller.addKeywordToRows([0], "a")


class TestABannerigELJUT:
    """A `photoOpFailed` önmagában nem elég — a BANNER a `syncFailed`-en él.

    ⚠️ Ez a jegy kifejezetten azt kéri, hogy a hiba „az `errorBanner`-en
    LÁTSZIK". A `photoOpFailed` → `syncFailed` továbbítást a
    `_ensure_photo_ops_wired()` köti be, azt viszont csak a FOTÓ-írás útja
    hívja (`_run_photo_write`). Ha a felhasználó első művelete egy
    mappa-leírás, egy mappa-dátum vagy egy címke, a jelzés bekötetlen
    csatornára megy — a jegyet „megoldó" őr zölden állna, a felhasználó
    pedig semmit nem látna.

    Ezért mind a négy útra FRISS vezérlőn, fotó-írás NÉLKÜL mérünk.
    """

    def test_mappa_leiras(self, controller, monkeypatch, library):
        uzenetek: list[str] = []
        controller.syncFailed.connect(uzenetek.append)
        _torj_el(monkeypatch, "controller", "teszt: banner-leírás")
        controller.setFolderDescriptionOf(str(library), "x")
        assert uzenetek, "a hiba nem jutott el a bannerig"

    def test_mappa_datum(self, controller, monkeypatch, library):
        uzenetek: list[str] = []
        controller.syncFailed.connect(uzenetek.append)
        _torj_el(monkeypatch, "folder_date_controller", "teszt: banner-dátum")
        controller.setFolderDate(str(library), "2020-01-02")
        assert uzenetek, "a hiba nem jutott el a bannerig"

    def test_mappa_datum_torles(self, controller, monkeypatch, library):
        uzenetek: list[str] = []
        controller.syncFailed.connect(uzenetek.append)
        _torj_el(monkeypatch, "folder_date_controller", "teszt: banner-törlés")
        controller.clearFolderDate(str(library))
        assert uzenetek, "a hiba nem jutott el a bannerig"

    def test_kulcsszavak(self, controller, monkeypatch):
        uzenetek: list[str] = []
        controller.syncFailed.connect(uzenetek.append)
        monkeypatch.setattr(
            "picasapy.app.keywords_controller.write_iptc_keywords",
            lambda *_a, **_k: False,
        )
        _torj_el(monkeypatch, "keywords_controller", "teszt: banner-címke")
        controller.addKeywordToRows([0], "a")
        assert uzenetek, "a hiba nem jutott el a bannerig"

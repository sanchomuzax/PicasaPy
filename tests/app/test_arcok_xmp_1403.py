"""Az „Arcinformációk írása XMP-adatokba" bekötése (#1403).

## Mi volt a hiány

Az XMP-építő MEGVOLT (`export/xmp.py`, arcrégiókkal), de **nulla hívója** volt
a csomagon kívül: a felhasználó felől nem vezetett hozzá út — a #1798
hibaosztálya. A jegy valódi tartalma tehát a bekötés.

Ez a fájl a vezérlő-oldalt méri: a látott mappa képeire kiíródik-e a sidecar,
ad-e a köteg EGY összegzést, és a csak olvasható hely NEM állítja-e le a
köteget (az eredetiben is megnevezett hibaeset: „Face tag write failed for
read only file: %s").
"""

from __future__ import annotations

import os
import stat

import pytest
from PySide6.QtCore import QCoreApplication
from support.jpeg_factory import make_jpeg

from picasapy.index import open_index, sync_tree


@pytest.fixture
def konyvtar(tmp_path):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    make_jpeg(gyoker / "a.jpg")
    make_jpeg(gyoker / "b.jpg")
    (gyoker / ".picasa.ini").write_text(
        "[a.jpg]\nkeywords=nyár\nfaces=rect64(4000400080008000),1\n"
        "[Contacts2]\n1=Anna;;\n",
        encoding="utf-8",
    )
    return gyoker


@pytest.fixture
def vezerlo(qt_app, tmp_path, konyvtar):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
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
    yield ctl
    ctl.shutdown()


def _osszegzes(vezerlo, konyvtar):
    """A mappa kiválasztása, az írás elindítása, az összegzés bevárása."""
    eredmeny = {}
    vezerlo.xmpFacesFinished.connect(
        lambda k, h, o: eredmeny.update(kiirt=k, kihagyott=h, ok=o)
    )
    vezerlo.selectFolder(str(konyvtar))
    QCoreApplication.processEvents()
    vezerlo.writeFacesToXmp()
    assert vezerlo.waitForBackgroundWorkers(15.0), "a köteg nem állt le 15 s alatt"
    QCoreApplication.processEvents()
    assert eredmeny, "nem jött összegzés a köteg végén"
    return eredmeny


class TestAzIras:
    def test_a_sidecar_kiirodik_arcregioval(self, vezerlo, konyvtar):
        eredmeny = _osszegzes(vezerlo, konyvtar)

        sidecar = konyvtar / "a.jpg.xmp"
        assert sidecar.exists(), "az arcadatot hordozó kép sidecarja nem jött létre"
        szoveg = sidecar.read_text(encoding="utf-8")
        assert "mwg-rs:Regions" in szoveg
        assert "MP:RegionInfo" in szoveg, "a Microsoft-séma blokkja is kell (#1403)"
        assert "Anna" in szoveg
        assert eredmeny["kiirt"] == 1, eredmeny
        assert eredmeny["kihagyott"] == 1, "az adat nélküli kép kimarad"

    def test_ures_mappara_is_ad_osszegzest(self, vezerlo):
        """Néma hatástalanság helyett üzenet: nulla/nulla."""
        eredmeny = {}
        vezerlo.xmpFacesFinished.connect(
            lambda k, h, o: eredmeny.update(kiirt=k, kihagyott=h, ok=o)
        )
        vezerlo.writeFacesToXmp()
        QCoreApplication.processEvents()

        assert eredmeny == {"kiirt": 0, "kihagyott": 0, "ok": ""}


@pytest.mark.skipif(os.name == "nt", reason="a POSIX írásvédelem nem érvényes")
class TestAzIrasvedettHely:
    def test_a_koteg_nem_all_le_es_MEGNEVEZI_az_okot(self, vezerlo, konyvtar):
        """Az eredetiben is külön, megnevezett hibaeset a csak olvasható fájl."""
        vezerlo.selectFolder(str(konyvtar))
        QCoreApplication.processEvents()
        eredmeny = {}
        vezerlo.xmpFacesFinished.connect(
            lambda k, h, o: eredmeny.update(kiirt=k, kihagyott=h, ok=o)
        )
        konyvtar.chmod(stat.S_IRUSR | stat.S_IXUSR)
        try:
            vezerlo.writeFacesToXmp()
            assert vezerlo.waitForBackgroundWorkers(15.0)
            QCoreApplication.processEvents()
        finally:
            konyvtar.chmod(stat.S_IRWXU)

        assert eredmeny, "összegzés írásvédett helyen is kell"
        assert eredmeny["ok"], (
            "írásvédett helyen a hibát MEG KELL nevezni — az eredeti is külön "
            "hibaüzenetet ad rá"
        )
        assert "a.jpg" in eredmeny["ok"], eredmeny

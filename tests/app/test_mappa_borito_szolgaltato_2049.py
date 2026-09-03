"""#2049: az `image://foldercover/<mappa>` szolgáltató.

A kupac mértanát a `tests/thumbs/test_album_borito_2049.py` méri; itt az
a kérdés, hogy a mappa fájljaiból tényleg összeáll-e egy kép, és hogy a
hibás bemenet NEM dönti-e le a felületet.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize

from picasapy.app.folder_cover_provider import (
    FolderCoverProvider,
    keszits_mappa_boritot,
)
from support.jpeg_factory import make_jpeg


def _mappa_kepekkel(gyoker: Path, darab: int) -> list[Path]:
    gyoker.mkdir(parents=True, exist_ok=True)
    return [make_jpeg(gyoker / f"k{i}.jpg", size=(120, 90)) or gyoker / f"k{i}.jpg" for i in range(darab)]


class TestABoritoOsszeall:
    def test_egy_kepbol_is_lesz_borito(self, tmp_path):
        fajlok = _mappa_kepekkel(tmp_path / "m", 1)
        borito = keszits_mappa_boritot(str(tmp_path / "m"), fajlok)
        assert borito is not None and borito.shape[2] == 4

    def test_legfeljebb_negy_lap_kerul_bele(self, tmp_path):
        """Hat fájlból is négylapos kupac lesz — a lista ELEJE számít."""
        sok = _mappa_kepekkel(tmp_path / "m", 6)
        negy = keszits_mappa_boritot(str(tmp_path / "m"), sok)
        ugyanaz = keszits_mappa_boritot(str(tmp_path / "m"), sok[:4])
        assert negy.shape == ugyanaz.shape

    def test_kep_nelkuli_mappara_nincs_borito(self, tmp_path):
        assert keszits_mappa_boritot(str(tmp_path), []) is None

    def test_a_ROMLOTT_fajl_nem_dont_le_semmit(self, tmp_path):
        mappa = tmp_path / "m"
        mappa.mkdir()
        romlott = mappa / "romlott.jpg"
        romlott.write_bytes(b"ez nem JPEG")
        jo = _mappa_kepekkel(mappa, 1)
        borito = keszits_mappa_boritot(str(mappa), [romlott, *jo])
        assert borito is not None, "a romlott fájl elnyelte a jó lapot is"

    def test_csak_romlott_fajlokra_nincs_borito(self, tmp_path):
        rossz = tmp_path / "x.jpg"
        rossz.write_bytes(b"nem kep")
        assert keszits_mappa_boritot(str(tmp_path), [rossz]) is None


class TestAProvider:
    def test_kepet_ad_vissza(self, qt_app, tmp_path):
        fajlok = _mappa_kepekkel(tmp_path / "m", 3)
        provider = FolderCoverProvider(lambda _mappa: fajlok)
        kep = provider.requestImage(str(tmp_path / "m"), QSize(), QSize())
        assert not kep.isNull() and kep.width() > 1

    def test_a_HIBAS_lekerdezo_sem_dont_le_semmit(self, qt_app, tmp_path):
        """A providerből kivétel nem szökhet ki (#66) — a fasor ilyenkor a
        mappaikonjára esik vissza."""

        def robban(_mappa):
            raise RuntimeError("szándékos hiba")

        provider = FolderCoverProvider(robban)
        kep = provider.requestImage("/nincs/ilyen", QSize(), QSize())
        # #2215: a válasz ÜRES (null) kép. A korábbi 1×1 átlátszó a
        # docstring ígéretét hiúsította meg: az sikeresen betöltődik, ezért
        # a QML elrejtette a mappaikont, és a sor üresen maradt.
        assert kep.isNull(), "hibánál nem az üres helyettesítő jött vissza"

    def test_masodszorra_a_GYORSTARBOL_jon(self, qt_app, tmp_path):
        fajlok = _mappa_kepekkel(tmp_path / "m", 2)
        hivasok = []

        def lekerdezo(mappa):
            hivasok.append(mappa)
            return fajlok

        provider = FolderCoverProvider(lekerdezo)
        provider.requestImage(str(tmp_path / "m"), QSize(), QSize())
        provider.requestImage(str(tmp_path / "m"), QSize(), QSize())
        assert len(hivasok) == 1, "a borító minden kérésre újra készült"

    def test_a_gyorstar_uritheto(self, qt_app, tmp_path):
        fajlok = _mappa_kepekkel(tmp_path / "m", 2)
        hivasok = []

        def lekerdezo(mappa):
            hivasok.append(mappa)
            return fajlok

        provider = FolderCoverProvider(lekerdezo)
        provider.requestImage(str(tmp_path / "m"), QSize(), QSize())
        provider.uritsd_a_gyorstarat()
        provider.requestImage(str(tmp_path / "m"), QSize(), QSize())
        assert len(hivasok) == 2, "az ürítés után sem készült újra"

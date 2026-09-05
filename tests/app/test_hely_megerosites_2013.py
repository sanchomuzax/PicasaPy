"""#2013: a Helyek panel két megerősítő küszöbe.

Mérve a `Picasa3.exe`-ből:

| művelet | küszöb | a SZÁM, amit mutat |
|---|---|---|
| hely megváltoztatása | **> 20** (`0x00652585`, `cmp ebx, 0x14`) | a teljes **kijelölés** |
| hely törlése | **> 5** (`0x006527ad`, `cmp esi, 5`) | a **geocímkézett** elemek (`0x006524c0`) |

⚠️ A két küszöb SZÁNDÉKOSAN különbözik, és a két szám sem ugyanaz: ha 100
kép van kijelölve és ebből 3 geocímkézett, az eredeti **nem kérdez**.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.geo_controller import (
    HELY_MODOSITAS_KUSZOB,
    HELY_TORLES_KUSZOB,
)


@pytest.fixture
def library(tmp_path):
    """Egy geocímkézett és két címke nélküli kép (a #30 mintája)."""
    from support.jpeg_factory import make_jpeg

    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "a.jpg")
    make_jpeg(root / "nyaralas" / "b.jpg")
    make_jpeg(root / "nyaralas" / "c.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )


class TestAMertKuszobok:
    def test_a_ket_kuszob_a_mert_ertek(self):
        assert HELY_MODOSITAS_KUSZOB == 20
        assert HELY_TORLES_KUSZOB == 5

    def test_a_ket_kuszob_KULONBOZIK(self):
        """Ne egységesítsük: a törlés visszafordíthatatlanabb."""
        assert HELY_MODOSITAS_KUSZOB != HELY_TORLES_KUSZOB
        assert HELY_TORLES_KUSZOB < HELY_MODOSITAS_KUSZOB


class TestAGeocimkezettSzamlalo:
    """A törlés küszöbe a GEOCÍMKÉZETT elemeket számolja."""

    def test_csak_a_geocimkezetteket_szamolja(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        osszes = list(range(controller.photos.rowCount()))
        assert osszes, "a fixture-nek képeket kell betöltenie"
        # kezdetben egyiknek sincs geocímkéje
        assert controller.geotaggedCount(osszes) == 0

        controller.setGeotagRows(osszes[:2], 47.5, 19.05)
        assert controller.geotaggedCount(osszes) == 2

    def test_a_kijeloles_MERETE_nem_szamit(self, controller, library):
        """100 kijelöltből 2 geocímkézett ⇒ a szám 2, nem 100."""
        controller.selectFolder(str(library / "nyaralas"))
        osszes = list(range(controller.photos.rowCount()))
        controller.setGeotagRows(osszes[:2], 47.5, 19.05)
        assert controller.geotaggedCount(osszes) == 2
        assert controller.geotaggedCount(osszes) != len(osszes)

    def test_ures_kijelolesre_nulla(self, controller):
        assert controller.geotaggedCount([]) == 0

    def test_tartomanyon_kivuli_index_nem_szamit(self, controller):
        assert controller.geotaggedCount([9999]) == 0


class TestAKuszobokAFeluletnekIsLathatok:
    """A jegy kifejezetten kéri: NE beégetett 20/5 legyen a hívás helyén."""

    def test_a_vezerlo_kiteszi_mindkettot(self, controller):
        assert controller.geoChangeConfirmThreshold == HELY_MODOSITAS_KUSZOB
        assert controller.geoClearConfirmThreshold == HELY_TORLES_KUSZOB

    def test_a_QML_a_NEVESITETT_kuszobot_hasznalja(self):
        """Forrás-őr: a `Main.qml` ne tartalmazzon beégetett küszöböt a
        két megerősítésnél."""
        from pathlib import Path

        import picasapy.app

        fo = (Path(picasapy.app.__file__).parent / "qml" / "Main.qml").read_text(
            encoding="utf-8"
        )
        kezdet = fo.index('objectName: "setGeotagConfirm"')
        blokk = fo[kezdet : fo.index('objectName: "panelClearGeotagConfirm"')]
        assert "geoChangeConfirmThreshold" in blokk
        assert "rowList.length <= 20" not in blokk

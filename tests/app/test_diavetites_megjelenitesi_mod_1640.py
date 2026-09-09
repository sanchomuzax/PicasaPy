"""A megjelenítési mód a DIAVETÍTÉSBEN is hat (#1640).

A `Nézet ▸ Megjelenítési mód` átalakítói a nagy nézőre (#1576/#1598) és a
bélyegkép-felületekre (#1596) hatottak; a **diavetítésre nem**, pedig a
„Projektor mód" (−14,1 % egyenletes sötétítés) épp a kivetítéshez való.

Az ok mérve (#1640): a `SlideshowView.qml` a NYERS fájl URL-jét töltötte be,
a mód pedig kizárólag az `editpreview`/`thumbs` úton fut.

## Amit ez a fájl mér

1. a `displayUrlAt` mód nélkül a sima `file://`-t adja (a mindennapi eset
   URL-je BÁJTRA változatlan — a Qt gyorstára nem duplázódik),
2. aktív módnál a `displayphoto` szolgáltatóra vált, a móddal az URL-ben,
3. a szolgáltató a fájl képpontjait TÉNYLEG átfesti — a várt értékek KIÍRT
   LITERÁLOK, a spec egész-aritmetikájából (`200 · 220 >> 8 = 171`), nem a
   termék konstansaiból olvasva,
4. és a QML-kötés a `displayUrlAt`-ot hívja (nem a `fileUrlAt`-ot) — enélkül
   a lánc a felület oldalán szakadna el.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtGui import QImage

from picasapy.app.display_mode_paint import set_current_display_mode
from picasapy.app.display_photo_provider import (
    PROVIDER_NAME,
    DisplayPhotoProvider,
)

#: A projektor mód mért, egész-aritmetikás eredménye a 200-as szürkén.
PROJEKTOROS = 171


@pytest.fixture
def kep(tmp_path: Path) -> Path:
    ut = tmp_path / "dia.png"
    tomb = np.full((8, 12, 3), 200, dtype=np.uint8)
    kep = QImage(tomb.data, 12, 8, 12 * 3, QImage.Format.Format_RGB888)
    assert kep.copy().save(str(ut))
    return ut


@pytest.fixture(autouse=True)
def alaphelyzet():
    """A modul-szintű mód GLOBÁLIS — minden próba után vissza kell állítani,
    különben a következő teszt más módban futna (és a bukása félrevezetne)."""
    yield
    set_current_display_mode("")


class TestASzolgaltato:
    def test_a_mod_nelkuli_keres_valtozatlanul_ad_kepet(self, kep: Path) -> None:
        provider = DisplayPhotoProvider()
        eredmeny = provider.requestImage(str(kep), None, None)
        assert not eredmeny.isNull()
        assert eredmeny.pixelColor(0, 0).red() == 200

    def test_a_projektor_mod_sotetit(self, kep: Path) -> None:
        provider = DisplayPhotoProvider()
        eredmeny = provider.requestImage(f"{kep}?d=projector", None, None)
        szin = eredmeny.pixelColor(3, 3)
        assert (szin.red(), szin.green(), szin.blue()) == (
            PROJEKTOROS,
            PROJEKTOROS,
            PROJEKTOROS,
        ), "#1640: a diavetítés szolgáltatója nem festette át a képet"

    def test_az_ekezetes_utvonal_is_betoltodik(self, tmp_path: Path) -> None:
        """Az URL-kódolt útvonalat vissza kell fejteni — enélkül az ékezetes
        mappanevű képek a diavetítésben ELTŰNNÉNEK."""
        from urllib.parse import quote

        mappa = tmp_path / "nyaralás öröm"
        mappa.mkdir()
        ut = mappa / "kép.png"
        tomb = np.full((4, 4, 3), 200, dtype=np.uint8)
        QImage(tomb.data, 4, 4, 12, QImage.Format.Format_RGB888).copy().save(str(ut))
        provider = DisplayPhotoProvider()
        eredmeny = provider.requestImage(f"{quote(str(ut))}?d=projector", None, None)
        assert not eredmeny.isNull(), "az ékezetes útvonal nem töltődött be"
        assert eredmeny.pixelColor(1, 1).red() == PROJEKTOROS

<<<<<<< HEAD
    def test_a_WINDOWSOS_utvonal_nem_esik_szet(self) -> None:
        """MÉRVE a windows-lábon (#1640): az `urlparse` a `C:` meghajtó-betűt
        URL-SÉMÁNAK olvassa, és az útvonal fele elveszik — a diavetítés képe
        be sem töltődik. A próba a szétszedőt közvetlenül méri, ezért
        LINUXON IS lefut (sztring-művelet, nem fájlrendszer)."""
        from picasapy.app.display_photo_provider import _szetszed

        utvonal, mod = _szetszed("C:/Users/sancho/K%C3%A9pek/a.jpg?d=projector")
        assert utvonal == "C:/Users/sancho/Képek/a.jpg", (
            "a meghajtó-betű URL-sémaként értelmezve levágta az útvonal elejét"
        )
        assert mod == "projector"

    def test_a_lekerdezes_nelkuli_windowsos_utvonal_is_ep(self) -> None:
        from picasapy.app.display_photo_provider import _szetszed

        assert _szetszed("D:/foto/nyaral%C3%A1s/b.jpg") == (
            "D:/foto/nyaralás/b.jpg",
            "",
        )
=======
    def test_a_MERETEZO_ag_is_mukodik(self, kep: Path) -> None:
        """A QML `sourceSize`-zal kér — ez az ág korábban `None` mérettel
        méretlen maradt, és élesben `ValueError`-ral szállt el (#1640)."""
        from PySide6.QtCore import QSize

        provider = DisplayPhotoProvider()
        eredmeny = provider.requestImage(
            f"{kep}?d=projector", QSize(), QSize(6, 4)
        )
        assert not eredmeny.isNull(), "a méretezés elszállt"
        assert eredmeny.width() == 6
        assert eredmeny.pixelColor(3, 2).red() == PROJEKTOROS
>>>>>>> 282005cf (fix(app): a diavetites modja a KIRAJZOLT kepen is hat — ket nema hiba (#1640))

    def test_a_hianyzo_fajl_URES_kepet_ad(self, tmp_path: Path) -> None:
        provider = DisplayPhotoProvider()
        assert provider.requestImage(str(tmp_path / "nincs.png"), None, None).isNull()


@pytest.fixture
def modell(qt_app, tmp_path: Path):
    """Egyetlen fotót tartalmazó rács-modell — a `displayUrlAt` mércéje."""
    from picasapy.app.models import PhotoGridModel
    from picasapy.index import PhotoRecord

    model = PhotoGridModel()
    model.set_photos(
        (
            PhotoRecord(
                id=1,
                folder_path=str(tmp_path),
                name="dia.png",
                kind="photo",
                size=10,
                mtime_ns=5,
                star=False,
                caption="",
                keywords="",
                rotate_steps=0,
                filters="",
                taken_at=None,
                orientation=1,
                width=12,
                height=8,
            ),
        )
    )
    return model


class TestAModellUrlje:
    def test_mod_nelkul_a_sima_file_url(self, modell) -> None:
        model = modell
        set_current_display_mode("")
        assert model.displayUrlAt(0) == model.fileUrlAt(0), (
            "mód nélkül az URL-nek BÁJTRA a réginek kell lennie, különben a "
            "Qt gyorstára minden képet kétszer tart"
        )

    def test_aktiv_modnal_a_szolgaltato_url_je(self, modell) -> None:
        model = modell
        set_current_display_mode("projector")
        url = model.displayUrlAt(0)
        assert url.startswith(f"image://{PROVIDER_NAME}/")
        assert url.endswith("?d=projector"), url

    def test_ervenytelen_indexre_ures(self, modell) -> None:
        model = modell
        set_current_display_mode("projector")
        assert model.displayUrlAt(99) == ""


class TestAQmlKotes:
    """A lánc a felület oldalán is összeér: a `SlideshowView.qml` a
    `displayUrlAt`-ot hívja, és a módra újraértékelődik."""

    def test_a_diavetites_a_displayUrlAt_ot_hivja(self) -> None:
        qml = (
            Path(__file__).resolve().parents[2]
            / "src/picasapy/app/qml/PicasaPy/SlideshowView.qml"
        ).read_text(encoding="utf-8")
        assert "displayUrlAt" in qml, (
            "#1640: a diavetítés visszaesett a nyers `fileUrlAt`-ra — a mód "
            "megint elveszne"
        )
        assert qml.count("displayUrlAt") >= 2, (
            "az ELŐ-BETÖLTŐ Image-nek is a mód-tudatos URL kell, különben a "
            "következő dia egy pillanatra festetlenül villan"
        )
        assert "controller.displayMode" in qml, (
            "a kötésnek hivatkoznia kell a módra, különben váltáskor nem "
            "értékelődik újra"
        )

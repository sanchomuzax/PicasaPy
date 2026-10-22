"""#5544: a diaidő felső határa 20 másodperc, nem 30.

Mérve az eredeti binárisban: a diavetítő sávjának `+` és `-` gombjai után a
kijelzési idő 1 és 20 másodperc közé szorul. Az alsó határ `0x00802b6d`
(`fld1`), a felső a `0x00cf4974` konstans (f32 = 20,0). A határ az
`AppController.SLIDESHOW_SECONDS_MAX`-ban él; ez a fájl a viselkedést zárja le.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir()
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    return AppController(
        tmp_path / "index.db",
        (str(konyvtar),),
        provider,
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )


def _ujraolvasott(tmp_path, gyorsitotar: str):
    """Új vezérlő ugyanabból a beállításfájlból: ez bizonyítja a mentést."""
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    return AppController(
        tmp_path / "index.db",
        (str(tmp_path / "kepek"),),
        ThumbnailProvider(ThumbnailCache(tmp_path / gyorsitotar, size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )


class TestAFelsoHatar20:
    def test_a_20_MEGY_BE(self, controller):
        controller.setSlideshowSeconds(20)
        assert controller.slideshowSeconds == 20

    def test_a_20_MEGMARAD(self, controller, tmp_path):
        controller.setSlideshowSeconds(20)
        assert _ujraolvasott(tmp_path, "thumbs2").slideshowSeconds == 20

    def test_a_21_NEM_megy_be(self, controller):
        controller.setSlideshowSeconds(8)
        controller.setSlideshowSeconds(21)
        assert controller.slideshowSeconds == 8, "a 21 másodperc bekerült"

    def test_a_30_MAR_NEM_megy_be(self, controller):
        controller.setSlideshowSeconds(30)
        assert controller.slideshowSeconds == 3, "a régi, 30-as határ még él"

    def test_a_TAROLT_25_olvasaskor_az_alapertek_HAROM(self, controller, tmp_path):
        from PySide6.QtCore import QSettings

        beallitasok = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        beallitasok.setValue("view/slideshowSeconds", 25)
        beallitasok.sync()
        assert _ujraolvasott(tmp_path, "thumbs3").slideshowSeconds == 3

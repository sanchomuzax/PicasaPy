"""#2992: a diaidő állítható, és megmarad.

A tulajdonos jelezte, hogy „a diaidőt nem lehet állítani úgy, mint az
eredetiben". A mérés szerint az eredeti sávján a `tpslabel` („Display
Time") mellett `minusone` / `tps` / `plusone` hármas áll, és a
`SlideshowEffectTime` alapértéke **3** másodperc
(`0x007facd3`, `picasa-create-features.md`).

Nálunk a vetítő `intervalMs`-e 3000 volt — az alapérték tehát stimmelt,
de nem volt se vezérlő, se megőrzés.

⚠️ **A tartomány NINCS kimérve.** Az eredeti alsó/felső korlátja nem
szerepel a specben; a 1–30 másodperc a mi választásunk, és a kód ezt ki is
mondja. Ha egyszer kimérjük, ez a szám cserélhető.
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


class TestADiaido:
    def test_az_alapertek_HAROM_masodperc(self, controller):
        """Mérve: `SlideshowEffectTime` = 3 (`0x007facd3`)."""
        assert controller.slideshowSeconds == 3

    def test_allithato_es_megmarad(self, controller, tmp_path):
        controller.setSlideshowSeconds(8)
        assert controller.slideshowSeconds == 8

        from PySide6.QtCore import QSettings

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        masik = AppController(
            tmp_path / "index.db",
            (str(tmp_path / "kepek"),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs2", size=32)),
            settings=QSettings(
                str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
            ),
        )
        assert masik.slideshowSeconds == 8, "a diaidő nem maradt meg"

    def test_a_tartomanyon_KIVULI_ertek_nem_megy_be(self, controller):
        controller.setSlideshowSeconds(0)
        assert controller.slideshowSeconds == 3, "a nulla másodperc elfogadva"
        controller.setSlideshowSeconds(999)
        assert controller.slideshowSeconds == 3, "a 999 másodperc elfogadva"

    def test_a_hatarok_MAGUK_elfogadottak(self, controller):
        controller.setSlideshowSeconds(1)
        assert controller.slideshowSeconds == 1
        controller.setSlideshowSeconds(30)
        assert controller.slideshowSeconds == 30

    def test_a_SERULT_beallitas_az_alapertekre_esik(self, controller, tmp_path):
        from PySide6.QtCore import QSettings

        beallitasok = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        beallitasok.setValue("view/slideshowSeconds", "nem szám")
        beallitasok.sync()

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        masik = AppController(
            tmp_path / "index.db",
            (str(tmp_path / "kepek"),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs3", size=32)),
            settings=beallitasok,
        )
        assert masik.slideshowSeconds == 3

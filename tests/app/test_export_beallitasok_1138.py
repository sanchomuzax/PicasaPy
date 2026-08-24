"""Az export-párbeszéd MEGJEGYZI az előző beállításokat (#1138).

Az eredeti levezetése: `docs/specs/export-parbeszed.md` 4. és 13.7
szakasz. A `0x00738c00` a `Preferences` alól olvassa vissza a kilenc
kulcsot, a `0x00739960` írja ki őket — és a 13.7 mérése szerint
**egyetlen menetben, csak az ELFOGADÁSKOR** (a közös párbeszéd-lezáró
`0x008d2720` a `vt[0x164]`-et hívja, ha a lezárási kód 0). A **Mégse**
ága a `vt[0x168]`, ami az üres tő (`0x00b0d990`, egyetlen `ret`) —
Mégsére tehát semmi nem íródik és semmi nem áll vissza.

Ezért a felület felől EGYETLEN mentő hívás van (`saveExportSettings`),
és egyetlen visszaolvasó (`exportSettings`).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "a.jpg", size=(64, 48))
    return root


@pytest.fixture
def controller(tmp_path, library, qt_app):
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
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le a teardownban"


class TestKilencKulcs:
    """A 4. szakasz kilenc kulcsa: a párbeszéd mindet visszahozza."""

    def test_az_alapertekek_a_specbol_valok(self, controller):
        beallitasok = controller.exportSettings()

        # `FileExportSize` alapértéke 3 (`0x00738c58`), a hét fogás
        # harmadik indexe → 800 képpont
        assert beallitasok["size"] == 3
        # a méret-rádió alapja az „Eredeti méret használata" (spec 3.2)
        assert beallitasok["resize"] is False
        # `FileExportQuality` alapértéke 0x55 = 85 (`0x0073962d`)
        assert beallitasok["quality"] == 85
        # `FileExportQualityType`: a mentetlen alapállapot az
        # „Automatikus" — az alapérték a specben NINCS kimérve, az
        # indoklás (és a mellette/ellene szóló jelek) az
        # `app/export_prefs.py`-ban, a mező kommentjében.
        assert beallitasok["qualityType"] == 0
        # `FileExportMovie` alapértéke 0 → „Első képkocka" (spec 11.1)
        assert beallitasok["movieFull"] is False
        # `ExportAddNumbers` alapértéke 0 (spec 12.7)
        assert beallitasok["addNumbers"] is False
        assert beallitasok["watermark"] is False
        assert beallitasok["watermarkText"] == ""
        assert beallitasok["customSize"] == 800

    def test_a_mentett_ertekek_visszajonnek(self, controller):
        controller.saveExportSettings({
            "size": 5,
            "customSize": 1100,
            "resize": True,
            "qualityType": 4,
            "quality": 60,
            "movieFull": True,
            "addNumbers": True,
            "watermark": True,
            "watermarkText": "© Sancho",
        })

        beallitasok = controller.exportSettings()

        assert beallitasok["size"] == 5
        assert beallitasok["customSize"] == 1100
        assert beallitasok["resize"] is True
        assert beallitasok["qualityType"] == 4
        assert beallitasok["quality"] == 60
        assert beallitasok["movieFull"] is True
        assert beallitasok["addNumbers"] is True
        assert beallitasok["watermark"] is True
        assert beallitasok["watermarkText"] == "© Sancho"

    def test_a_film_radio_regi_slotja_ugyanazt_a_kulcsot_hasznalja(self, controller):
        """Megőrző: a #1166 `exportMovieFull()`/`setExportMovieFull()`
        slotja és az új közös mentés UGYANARRA a tárolt értékre néz — két
        igazságforrás némán szétcsúszna."""
        controller.setExportMovieFull(True)

        assert controller.exportSettings()["movieFull"] is True

        controller.saveExportSettings({"movieFull": False})

        assert controller.exportMovieFull() is False

    def test_a_hianyzo_mezok_nem_torlik_a_tobbit(self, controller):
        """A mentés részleges térképet is elfogad — ami nincs benne, az
        marad a régi (a `setExportMovieFull` és a közös mentés így fér meg
        egymás mellett)."""
        controller.saveExportSettings({"quality": 40, "addNumbers": True})

        controller.saveExportSettings({"quality": 45})

        beallitasok = controller.exportSettings()
        assert beallitasok["quality"] == 45
        assert beallitasok["addNumbers"] is True


class TestAutomatikusFokozat:
    def test_a_vezerlo_meg_tudja_mondani_hogy_automatikus(self, controller):
        """Spec 3.3: az „Automatikus" nem szám, hanem külön jelző — a
        felületnek külön kell tudnia megkérdezni."""
        assert controller.exportQualityIsAutomatic("automatic") is True
        assert controller.exportQualityIsAutomatic("normal") is False

    def test_az_automatikus_export_atveszi_a_forras_tablait(
        self, controller, tmp_path, qt_app
    ):
        """Végponttól végpontig: a vezérlőn át indított export kimenetének
        DQT-je egyezzen a forráséval (spec 7.1 mércéje)."""
        from PIL import Image

        cel = tmp_path / "ki"
        kesz = []
        controller.exportFinished.connect(lambda d, f: kesz.append((d, f)))

        controller.exportRows(
            [0], str(cel), 32, 85, False, "", False, True
        )
        assert controller.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        assert kesz and kesz[0][1] == 0, kesz
        forras = next(iter(controller._photos.photos))
        from pathlib import Path

        forras_ut = Path(forras.folder_path) / forras.name
        kimenet = next(cel.glob("*.jpg"))
        with Image.open(forras_ut) as k1, Image.open(kimenet) as k2:
            assert dict(k2.quantization) == dict(k1.quantization)

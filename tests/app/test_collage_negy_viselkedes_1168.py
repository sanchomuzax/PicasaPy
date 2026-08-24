"""#1168: a kollázs négy hiányzó viselkedése — a VEZÉRLŐ oldala.

A jegy négy leletéből kettő a vezérlőn dől el:

1. **„Mentés mellőzve" a PISZKOZAT ágán** (spec `kollazs-eletciklus.md`
   16.2/a). A `saveCollageDraft()` eddig NÉMÁN tért vissza, ha egy klip
   sem maradt — az eredeti ilyenkor a `collageUI::noimages` dobozt
   mutatja. A néma ág ugyanaz a hibaosztály, mint a #1075-nél: a
   felhasználó megnyomja a „Piszkozat mentése" gombot, a lap bezárul, és
   semmi nem történik.

2. **A várakozó állapot a FŐABLAKBAN** (16.3, `CThumbUI::CreateCollageWait`
   = „Várakozás a kollázs elkészítésére…"). Ehhez a felületnek TUDNIA
   kell, hogy éppen rajzolunk-e — ezt adja a `collageRendering`.

A harmadik és a negyedik lelet nem itt lakik: a kattintható értesítés
QML-oldali (`test_kollazs_negy_viselkedes_1168.py`), a `hascollage` pedig
album-szintű, származtatott jelző (`tests/index/test_album_collage_1168.py`).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_kollazs_jelzesre


class _Photo:
    def __init__(self, folder_path, name, caption=None, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = caption
        self.width = width
        self.height = height


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "Nyaralás 2026"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def settings(tmp_path):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY

    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))
    return beallitasok


@pytest.fixture
def host(qt_app, settings, library):
    from picasapy.app.collage_controller import CollageMixin

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma"),
                    _Photo(str(library), "b.jpg", None, 300, 400),
                    _Photo(str(library), "c.jpg", "Cica", 200, 200),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

        def _collage_output_width(self):
            return 240

    instance = _Host()
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def nyitott(host):
    host.openCollage([0, 1, 2])
    return host


def _wait(signal, action, timeout_ms=20000):
    return varj_kollazs_jelzesre(signal, action, timeout_ms)


class TestPiszkozatMentesMellozve:
    """16.2/a — üres vászon piszkozatára a „Mentés mellőzve" doboz jár."""

    def test_ures_vaszon_piszkozata_noimages_jelzest_ad(self, nyitott):
        kaptunk: list[bool] = []
        nyitott.collageNoImages.connect(lambda: kaptunk.append(True))

        nyitott.selectAllNodes()
        nyitott.removeSelectedNodes()
        nyitott.saveCollageDraft()

        assert kaptunk == [True], "a piszkozat-mentés NÉMÁN maradt el"

    def test_ures_vaszon_piszkozata_NEM_ad_draftSaved_jelzest(self, nyitott):
        """A „mentve" jelzés hazugság volna: fájl nem keletkezett."""
        kaptunk: list[str] = []
        nyitott.collageDraftSaved.connect(kaptunk.append)

        nyitott.selectAllNodes()
        nyitott.removeSelectedNodes()
        nyitott.saveCollageDraft()

        assert kaptunk == []

    def test_klippel_a_piszkozat_tovabbra_is_elkeszul(self, nyitott):
        """Az őr foga: a rendes ág NEM sérülhet."""
        mentve: list[str] = []
        nincs_kep: list[bool] = []
        nyitott.collageDraftSaved.connect(mentve.append)
        nyitott.collageNoImages.connect(lambda: nincs_kep.append(True))

        nyitott.saveCollageDraft()

        assert len(mentve) == 1 and nincs_kep == []


class TestVarakozoAllapot:
    """16.3 — a főablak jelzi, hogy a kollázs készül."""

    def test_alaphelyzetben_nem_varakozunk(self, nyitott):
        assert nyitott.collageRendering is False

    def test_a_rajzolas_alatt_igaz_a_vegen_hamis(self, nyitott):
        allapotok: list[bool] = []
        nyitott.collageRenderingChanged.connect(
            lambda: allapotok.append(nyitott.collageRendering)
        )

        megjott, _ = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )

        assert megjott
        assert allapotok[0] is True, "a rajzolás indulásakor nem jelzett"
        assert allapotok[-1] is False, "a rajzolás végén beragadt a jelzés"
        assert nyitott.collageRendering is False

    def test_ures_vaszonra_nem_kapcsol_be(self, nyitott):
        """A `createCollage` a kép nélküli ágon azonnal visszafordul —
        ilyenkor várakozást jelezni beragadt sávot adna."""
        nyitott.selectAllNodes()
        nyitott.removeSelectedNodes()

        nyitott.createCollage(False)

        assert nyitott.collageRendering is False

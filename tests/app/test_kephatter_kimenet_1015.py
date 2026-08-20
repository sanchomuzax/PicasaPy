"""A háttérkép a RENDERELŐ-BEÁLLÍTÁSBA is átmegy (#1015).

A #1009 megjavította a kiválasztást, az előnézetet és a `.cxf`-et — a
kirajzolt JPEG háttere viszont a szín maradt. A rajzoló javítása
(`picasa_render._canvas`) önmagában kevés: a vezérlőnek **át is kell adnia**
a képet, és csak KÉP-módban.

Ez a fájl a vezérlő oldalát állítja; hogy a rajzoló tényleg kifesti, azt a
`tests/collage/test_kephatter_1015.py` dönti el.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from support.jpeg_factory import make_jpeg


class _Photo:
    def __init__(self, folder_path, name, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = None
        self.width = width
        self.height = height


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "Nyaralás 2026"
    root.mkdir()
    for name in ("a.jpg", "b.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def nyitott(qt_app, tmp_path, library):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [_Photo(str(library), "a.jpg"), _Photo(str(library), "b.jpg")]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    instance = _Host()
    instance.openCollage([0, 1])
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


class TestAzAtadas:
    def test_kep_modban_atmegy_a_hatterkep(self, nyitott):
        nyitott.setCollageBackgroundMode("image")

        beallitas = nyitott._render_settings()

        assert beallitas.background_image == nyitott.collageBackgroundImage
        assert beallitas.background_image != ""

    def test_szin_modban_NEM_megy_at(self, nyitott):
        """⚠️ A szín-mód nem romolhat el: ha a képet mindig átadnánk, a
        felhasználó a színt választaná, és képet kapna."""
        nyitott.setCollageBackgroundMode("solid")

        assert nyitott._render_settings().background_image == ""

    def test_atlagszin_modban_sem_megy_at(self, nyitott):
        """A #1004 (átlagszín) szintén SZÍN-mód — a kép ott sem járhat."""
        nyitott.setCollageBackgroundMode("avg")

        assert nyitott._render_settings().background_image == ""

    def test_modvaltas_utan_kovetkezetes(self, nyitott):
        """Oda-vissza váltás: a beállítás mindig a JELENLEGI módot tükrözi."""
        nyitott.setCollageBackgroundMode("image")
        kepes = nyitott._render_settings().background_image
        nyitott.setCollageBackgroundMode("solid")
        szines = nyitott._render_settings().background_image
        nyitott.setCollageBackgroundMode("image")

        assert (kepes != "", szines, nyitott._render_settings().background_image) == (
            True,
            "",
            kepes,
        )

"""Formátum- és tájolásváltás után ÚJRARENDEZŐDIK a vászon (#991).

## A lelet

Oldalformátum (méretarány) vagy tájolás váltása után **a lap alakja
megváltozik, de a kártyák a helyükön maradnak** — kilógnak, összetorlódnak,
vagy nagy üres rész marad.

A `setCollageTheme` helyesen hív `_relayout()`-ot; a `setCollageFormat` és a
`setCollageOrientation` **nem hívott**.

## Az eredeti

A képesség-maszk **1. bitje** pontosan ezt kapcsolja: „oldalformátum-
váltáskor lefut egy csomópontonkénti újraszámolás" (`0x0087e960`; a
kapcsolók a `0x00839f07` és a `0x0083a201` címen, spec 2.). A rácsos témák
pakolói eleve a lap arányából dolgoznak, tehát ott az újraszámolás a
formátumváltás természetes következménye.

## Mit állítunk

Itt nem a `_relayout` HÍVÁSÁT nézzük (az a megvalósítás), hanem azt, amit a
felhasználó lát: a váltás után a csomópontok az ÚJ lap alakja szerint
állnak, és a helyük tényleg MEGVÁLTOZOTT.

⚠️ **A mérce helyesbítve (#1094).** A jegy „Kész, ha" listája eredetileg a
**kilógást** kérte, és a teszt azt is állította. A tulajdonos három A4-es
FEKVŐ kollázsán mérve viszont a valódi Picasa kimenetében 89 csomópontból 3
kilóg — az eredeti a KÖZÉPPONTOT korlátozza sávra, a csempe téglalapját
nem. A „semmi nem lóg ki" tehát KITALÁLT követelmény volt; a #1045 ezt
beszorítással teljesítette, azóta visszavonva.

A helyes mérce: a középpontok az ÚJ lapra számolt sávban vannak. Ez az, ami
elbukik, ha a formátumváltás után elmarad az újraszámolás — a régi lapra
szórt középpontok a rövidebb lap sávjából kilógnának.
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
    for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"):
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
                [
                    _Photo(str(library), nev, w, h)
                    for nev, w, h in (
                        ("a.jpg", 400, 300),
                        ("b.jpg", 300, 400),
                        ("c.jpg", 400, 400),
                        ("d.jpg", 560, 300),
                        ("e.jpg", 300, 560),
                    )
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    peldany = _Host()
    peldany.openCollage([0, 1, 2, 3, 4])
    yield peldany
    assert peldany.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


def _helyek(vezerlo):
    return [
        (round(cs.center_x, 3), round(cs.center_y, 3))
        for cs in vezerlo.collageNodes.nodes
    ]


def _savon_kivul(vezerlo):
    """A csomópontok, amelyek KÖZÉPPONTJA az ÚJ lap sávján kívül esik.

    ⚠️ A csomópontok lapegységben élnek (`SHEET_UNITS = 1024`), a lap
    magassága az oldalarányból jön. Aki képpontban hasonlítana, jóval bővebb
    határt adna, mint a valódi lap — ezt a #1045 egyszer már elrontotta.

    A sáv a kupac szórásának korlátja (`scatter_centers`): a képszámmal
    tágul, és a valódi Picasa hat mintáján igazolt. A csempe MÉRETÉRE nincs
    állítás — az kilóghat, ez az eredeti viselkedése (#1094)."""
    from picasapy.collage.nodes import SHEET_UNITS
    from picasapy.collage.pile import PILE_BAND_FACTOR, pile_scale

    darab = len(vezerlo.collageNodes.nodes)
    band = 1.0 - pile_scale(darab) * PILE_BAND_FACTOR
    also = (1.0 - band) * 0.5
    felso = also + band
    lap_ma = SHEET_UNITS * vezerlo.collagePageRatio
    tures = 1.0
    return [
        cs
        for cs in vezerlo.collageNodes.nodes
        if not (also * SHEET_UNITS - tures <= cs.center_x <= felso * SHEET_UNITS + tures)
        or not (also * lap_ma - tures <= cs.center_y <= felso * lap_ma + tures)
    ]


class TestAFormatumvaltas:
    def test_a_valtas_utan_az_UJ_lapra_all_a_vaszon(self, nyitott):
        """⚠️ Ez a felhasználó panasza: a kártyák a helyükön maradnak.

        A `Desktop4x3` → `HDTV16x9` váltás a lapot MEGRÖVIDÍTI (fekvő
        oldalarány 0,75 → 0,5625). Ha elmarad az újraszámolás, a régi,
        magasabb lapra szórt középpontok az új lap sávján KÍVÜL esnek —
        pontosan azt a torlódást adva, amit a felhasználó jelentett."""
        nyitott.setCollageFormat("HDTV16x9")

        assert not _savon_kivul(nyitott)

    def test_a_csomopontok_helye_MEGVALTOZIK(self, nyitott):
        elotte = _helyek(nyitott)

        nyitott.setCollageFormat("HDTV16x9")

        assert _helyek(nyitott) != elotte

    def test_a_darabszam_valtozatlan(self, nyitott):
        """Az újraszámolás nem veszíthet el képet."""
        nyitott.setCollageFormat("HDTV16x9")

        assert nyitott.collageClipCount == 5

    def test_a_modositas_jelzo_igaz_marad(self, nyitott):
        nyitott.setCollageFormat("HDTV16x9")

        assert nyitott.collageDirty is True

    def test_azonos_formatumra_valtas_NEM_rendez_ujra(self, nyitott):
        """A korai kilépés marad: fölösleges újraszámolás elvenné a
        felhasználó kézi elrendezését a semmiért."""
        jelenlegi = nyitott.collageFormatKey
        elotte = _helyek(nyitott)

        nyitott.setCollageFormat(jelenlegi)

        assert _helyek(nyitott) == elotte


class TestATajolasvaltas:
    def test_a_valtas_utan_az_UJ_lapra_all_a_vaszon(self, nyitott):
        nyitott.setCollageOrientation("portrait")

        assert not _savon_kivul(nyitott)

    def test_a_csomopontok_helye_MEGVALTOZIK(self, nyitott):
        elotte = _helyek(nyitott)

        nyitott.setCollageOrientation("portrait")

        assert _helyek(nyitott) != elotte

    def test_oda_vissza_valtas_utan_is_az_UJ_lapra_all(self, nyitott):
        nyitott.setCollageOrientation("portrait")
        nyitott.setCollageOrientation("landscape")

        assert not _savon_kivul(nyitott)

    def test_azonos_tajolasra_valtas_NEM_rendez_ujra(self, nyitott):
        jelenlegi = nyitott.collageOrientation
        elotte = _helyek(nyitott)

        nyitott.setCollageOrientation(jelenlegi)

        assert _helyek(nyitott) == elotte

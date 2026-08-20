"""Klip hozzáadása/törlése után a téma SZABÁLYA szerint áll a vászon (#996).

## A lelet

| művelet | mi történt | mi a baj |
|---|---|---|
| **„+"** | az új klip a Képkupac alapméretével, döntetlenül, **szórt helyre** került | rácsos témánál kilóg a rácsból |
| **„–"** | a törölt kép helyén **lyuk maradt** | a rács hiányos lett |

Ugyanaz a család, mint a #991 (formátum- és tájolásváltás után nincs
újrarendezés).

## A határ: a téma `rotate` képessége

A szórás **csak a Képkupacnál** helyes — ott az elrendezés eleve szórás, és
a felhasználó kézzel rendezi. A `rotate` (szabad forgatás) képesség pontosan
egyetlen témánál áll: a Képkupacnál. A többinél a hely a pakoló dolga.

Ezért nem téma-nevek listáját írjuk a kódba, hanem a meglévő
képesség-maszkra kérdezünk — így egy új téma automatikusan a helyes ágra
kerül.

## Mit állítunk

A jegy a **KIMENETRE** kér tesztet („nem az, hogy meghívtuk a
`_relayout`-ot"). Ezért a mérce az, hogy a művelet után a geometria
AZONOS azzal, amit a téma pakolója ugyanezekre a képekre ad.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.themes import COLLAGE_THEMES, capabilities_for
from support.jpeg_factory import make_jpeg

#: A rácsos témák — azok, ahol a hely a pakolóé (nincs szabad forgatás).
RACSOS = tuple(t for t in COLLAGE_THEMES if not capabilities_for(t).rotate)

#: Az egyetlen téma, ahol a szórás a helyes viselkedés.
KUPAC = tuple(t for t in COLLAGE_THEMES if capabilities_for(t).rotate)


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
    for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg", "f.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def host(qt_app, tmp_path, library):
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
                        ("a.jpg", 400, 300), ("b.jpg", 300, 400),
                        ("c.jpg", 400, 400), ("d.jpg", 560, 300),
                        ("e.jpg", 300, 560), ("f.jpg", 400, 300),
                    )
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    peldany = _Host()
    yield peldany
    assert peldany.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


def _geometria(vezerlo):
    return [
        (
            round(cs.center_x, 2), round(cs.center_y, 2),
            round(cs.width, 2), round(cs.height, 2),
        )
        for cs in vezerlo.collageNodes.nodes
    ]


def _pakolo_szerint(vezerlo):
    """Amit a téma pakolója ADNA a jelenlegi képekre — ez a mérce."""
    from picasapy.app import collage_layout as layout

    return [
        (
            round(cs.center_x, 2), round(cs.center_y, 2),
            round(cs.width, 2), round(cs.height, 2),
        )
        for cs in layout.laid_out(
            vezerlo._current_sources(),
            vezerlo.collagePageRatio,
            vezerlo._collage_panel_border,
            theme=vezerlo._collage_panel_theme,
            spacing=vezerlo._collage_panel_spacing,
            frame_center=vezerlo._collage_panel_frame_center,
            seed=vezerlo._collage_panel_seed,
        )
    ]


@pytest.mark.parametrize("tema", RACSOS)
class TestARacsosTemak:
    """⚠️ Itt a hely a PAKOLÓÉ — a szórás kilógott a rácsból."""

    def test_hozzaadas_utan_a_pakolo_szerint_all(self, host, tema):
        host.openCollage([0, 1, 2])
        host.setCollageTheme(tema)

        host.addClips([3, 4])

        assert host.collageClipCount == 5
        assert _geometria(host) == _pakolo_szerint(host)

    def test_torles_utan_nem_marad_lyuk(self, host, tema):
        host.openCollage([0, 1, 2, 3, 4])
        host.setCollageTheme(tema)

        host.deleteClips([1, 3])

        assert host.collageClipCount == 3
        assert _geometria(host) == _pakolo_szerint(host)


@pytest.mark.parametrize("tema", KUPAC)
class TestAKepkupac:
    """A Képkupacnál a szórás a HELYES viselkedés — nem nyúlunk hozzá."""

    def test_hozzaadaskor_a_meglevo_kepek_NEM_mozdulnak(self, host, tema):
        host.openCollage([0, 1, 2])
        host.setCollageTheme(tema)
        elotte = _geometria(host)

        host.addClips([3])

        assert _geometria(host)[: len(elotte)] == elotte

    def test_torleskor_a_tobbi_kep_NEM_mozdul(self, host, tema):
        host.openCollage([0, 1, 2, 3])
        host.setCollageTheme(tema)
        elotte = _geometria(host)

        host.deleteClips([1])

        maradek = [g for i, g in enumerate(elotte) if i != 1]
        assert _geometria(host) == maradek


class TestAKozosSzabalyok:
    def test_ures_kereskor_nem_tortenik_semmi(self, host):
        host.openCollage([0, 1, 2])
        elotte = _geometria(host)

        host.addClips([])
        host.deleteClips([])

        assert _geometria(host) == elotte

    def test_MINDEN_klip_torlese_ures_vasznat_ad(self, host):
        """A pakoló nem hívható nulla képre — a törlésnek itt is működnie
        kell, üres vászonnal."""
        host.openCollage([0, 1])
        host.setCollageTheme(RACSOS[0])

        host.deleteClips([0, 1])

        assert host.collageClipCount == 0

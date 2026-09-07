"""#1600 — ugyanarra a bélyegkép-URL-re MINDENHOL ugyanaz a szűrés.

## A jelenség

A tulajdonos Windowson, futó programból jelentette (2026-08-27), a
munkamenet több pontján **hatszor**:

    QSGPlainTexture: Mipmap settings changed without having image data
    available. Call setImage() again or enable m_retain_image.
    Falling back to previous mipmap filtering mode.

## A diagnózis (MÉRVE, forrásból)

A Qt képgyorsítótára **URL + `sourceSize` szerint** kulcsol, és a
`QSGPlainTexture` a feltöltés után eldobja a `QImage`-et. Ha ugyanazt a
gyorsítótárazott képet két `Image` használja **eltérő `mipmap`
beállítással**, a második váltani akar — de a képadat már nincs meg, ezért
a Qt figyelmeztet, és **visszaesik a korábbi szűrésre**: a kép nem azzal a
szűréssel jelenik meg, amit kértünk.

A `thumbUrl`-t (`image://thumbs/…`) 2026-09-07-én **hét** helyen
használtuk `mipmap` nélkül, és **kettőn** mipmappal:

| mipmappal | mipmap nélkül |
|---|---|
| `ThumbDelegate.qml` (#83), `TimelineView.qml` | `DedupDialog`, `ImportSourceDialog`, `UnnamedFacesView`, `CollageClipsTab`, `PhotoViewer` (filmszalag), `TrayBar` (tálca) |

⇒ Elég a rácsot és a tálcát egyszerre látni, és a váltás megtörténik.

## Amit ez az őr rögzít

Minden `Image`, aminek a `source`-a bélyegkép-URL, **`mipmap: true`**-t
kér. Nem stílus-egységesítés: a `mipmap` a KICSINYÍTÉS minősége (a #83
mérése szerint a köztes csúszka-fokokon élesebb, moaré-mentes), és a
gyorsítótárazott textúra közös — a beállítás egységessége nélkül a Qt a
véletlenre bízza, melyik nyer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app as app_csomag
from tests.support.qml_blokk import blokkok_tipusra

_QML_MAPPA = Path(app_csomag.__file__).parent / "qml" / "PicasaPy"

#: A bélyegkép-szolgáltató URL-jét adó kötések neve a QML-ben.
_THUMB_KOTESEK = ("thumbUrl", "thumbUrlAt")


def _belyegkep_images() -> list[tuple[str, int, str]]:
    """(fájl, sorszám, blokk) minden `Image`-re, ami bélyegképet mutat.

    ⚠️ NEM sor-alapú keresés: a `source:` kötés több sorra is nyúlhat
    (a `TrayBar` és a `PhotoViewer` ternáriusa négy soros), és a
    sor-alapú első változat épp azt a hármat NEM találta meg, amelyik a
    tulajdonos képernyőjén a rács mellett látszik.
    """
    talalt: list[tuple[str, int, str]] = []
    for qml in sorted(_QML_MAPPA.glob("*.qml")):
        forras = qml.read_text(encoding="utf-8")
        for sorszam, blokk in blokkok_tipusra(forras, "Image"):
            if any(k in blokk for k in _THUMB_KOTESEK):
                talalt.append((qml.name, sorszam, blokk))
    return talalt


_BELYEGKEPEK = _belyegkep_images()
_AZONOSITOK = [f"{f}:{n}" for f, n, _ in _BELYEGKEPEK]


class TestAzOsszesBelyegkepMipmappal:
    def test_van_mit_merni(self):
        """A próba előfeltétele: ha a kötés neve megváltozik, ez bukjon —
        ne az legyen, hogy az őr némán nulla elemet ellenőriz.

        MÉRVE 2026-09-07: nyolc ilyen `Image` van a fában."""
        assert len(_BELYEGKEPEK) >= 8, (
            f"csak {len(_BELYEGKEPEK)} bélyegkép-forrású Image-et találtam "
            "(mérve 8) — a `thumbUrl` kötés neve megváltozott?"
        )

    @pytest.mark.parametrize(
        ("fajl", "sorszam", "blokk"), _BELYEGKEPEK, ids=_AZONOSITOK
    )
    def test_minden_belyegkep_mipmapos(self, fajl, sorszam, blokk):
        assert "mipmap: true" in blokk, (
            f"{fajl}:{sorszam} — ez az Image bélyegképet mutat, de nem kér "
            "mipmapot. Ugyanazt a gyorsítótárazott textúrát a rács "
            "MIPMAPPAL kéri; a Qt ilyenkor „Mipmap settings changed” "
            "figyelmeztetést ad, és VISSZAESIK a korábbi szűrésre (#1600)."
        )

    @pytest.mark.parametrize(
        ("fajl", "sorszam", "blokk"), _BELYEGKEPEK, ids=_AZONOSITOK
    )
    def test_minden_belyegkep_simitott(self, fajl, sorszam, blokk):
        """A `smooth` a felnagyítás nélküli oldalak bilineáris simítása —
        a `mipmap` mellé való, és szintén textúra-szintű beállítás."""
        assert "smooth: true" in blokk, (
            f"{fajl}:{sorszam} — hiányzik a `smooth: true`"
        )

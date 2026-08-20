r"""A `.cxf` kódolt útvonalainak feloldása (#1096).

## A felhasználói panasz, amit ez a fájl mér

A tulajdonos megnyitotta a **Picasával készült** kollázsát PicasaPy-ben, és
**egyetlen kép sem töltődött be**. A napló (v0.8.23, Windows):

```
QML QQuickImage: Cannot open: file:$My Pictures/lake/sunny_lake-1366x768.jpg
```

A `$My Pictures\…` szöveget szó szerint fájlnévként próbáltuk megnyitni.

## Miért ilyen kicsi a készlet

A kollázs-kutató kör **12 `.cxf`-et, 101 hivatkozást** mért: **101/101
`$My Pictures\…`**, nulla `$UNC`, nulla `[betű]\`, nulla nyers útvonal. A
tesztek ezért a **valódi** esetre szabottak; a másik két alakra csak azt
állítjuk, amit tudunk — hogy felismerjük őket, és hogy a fel nem oldható
alak **érintetlenül** megy tovább a hiányzó-kép ágra.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QStandardPaths

from picasapy.collage.cxf import CxfBackground, CxfNode, CxfProject
from picasapy.collage.draft import nodes_from_project
from picasapy.collage.win_paths import VALTOZOK, decode_cxf_path, encode_cxf_path


@pytest.fixture
def kepmappa(tmp_path, monkeypatch):
    """A rendszer képmappája a teszt saját mappájára térítve."""
    mappa = tmp_path / "Képek"
    mappa.mkdir()
    monkeypatch.setattr(
        QStandardPaths,
        "writableLocation",
        staticmethod(
            lambda location: str(mappa)
            if location == QStandardPaths.StandardLocation.PicturesLocation
            else ""
        ),
    )
    return mappa


class TestAValodiEset:
    """`$My Pictures\\…` — a mért 101/101 alak."""

    def test_a_kepmappa_ala_oldodik_fel(self, kepmappa):
        eredmeny = decode_cxf_path(r"$My Pictures\lake\sunny_lake-1366x768.jpg")

        assert Path(eredmeny) == kepmappa / "lake" / "sunny_lake-1366x768.jpg"

    def test_a_visszaperjelbol_HELYI_elvalaszto_lesz(self, kepmappa):
        """A `.cxf` windowsos, a futtató rendszer nem feltétlenül az."""
        eredmeny = decode_cxf_path(r"$My Pictures\AI\kep.png")

        assert Path(eredmeny).is_absolute()
        assert Path(eredmeny).name == "kep.png"

    def test_a_kor_bezarul(self, kepmappa):
        """Amit kiírunk, azt vissza is olvassuk ugyanoda."""
        eredeti = str(kepmappa / "AI" / "kep.png")

        kodolt = encode_cxf_path(eredeti)

        assert kodolt.startswith("$My Pictures\\")
        assert Path(decode_cxf_path(kodolt)) == Path(eredeti)


class TestAmitNemTudunkFELOLDANI:
    """A bevallott kudarc jobb, mint a kitalált útvonal."""

    def test_az_UNC_alak_ERINTETLEN_marad(self, kepmappa):
        """A `$UNC%s%s%s` hármas bontása nincs igazolva (0/101 minta)."""
        nyers = r"$UNC\\szerver\megosztas\kep.jpg"

        assert decode_cxf_path(nyers) == nyers

    def test_az_ismeretlen_valtozo_ERINTETLEN_marad(self, kepmappa):
        nyers = r"$Nincs Ilyen Valtozo\kep.jpg"

        assert decode_cxf_path(nyers) == nyers

    def test_a_Common_Application_Data_ERINTETLEN(self, kepmappa):
        """Ismert név, de nincs Qt-párja — nem találunk ki mappát hozzá."""
        nyers = r"$Common Application Data\kep.jpg"

        assert VALTOZOK["Common Application Data"] is None
        assert decode_cxf_path(nyers) == nyers

    def test_a_nyers_utvonal_valtozatlan(self, kepmappa):
        nyers = "/home/valaki/kepek/a.jpg"

        assert decode_cxf_path(nyers) == nyers

    @pytest.mark.parametrize("ures", ["", "   "])
    def test_az_ures_ures_marad(self, ures, kepmappa):
        assert decode_cxf_path(ures) == ""


class TestATablaHelyes:
    """A két csapda, amit a kutatói kör mért ki (#1109)."""

    def test_az_Application_Data_a_GENERIC(self):
        """Az `AppDataLocation` hozzáfűzi az alkalmazás nevét — más mappa."""
        assert (
            VALTOZOK["Application Data"]
            == QStandardPaths.StandardLocation.GenericDataLocation
        )

    def test_het_valtozo_van(self):
        assert len(VALTOZOK) == 7
        assert "My Pictures" in VALTOZOK


class TestAVaszonraIsAtjut:
    """A végponti állítás: a `.cxf`-ből épített csempe VALÓDI útvonalat kap.

    Ez a felhasználói panasz tesztje — a `nodes_from_project` a
    visszatöltés útja, és eddig a nyers `$My Pictures\\…` szöveg jutott el a
    `QQuickImage`-ig."""

    def test_a_csomopont_utvonala_feloldva_erkezik(self, kepmappa):
        projekt = CxfProject(
            aspect_ratio="15:10",
            orientation="landscape",
            theme="picturepile",
            shadows=True,
            captions=True,
            album_uid="",
            album_title="",
            album_date="",
            background=CxfBackground(type="solid", color="FF000000"),
            spacing=0.25,
            nodes=(
                CxfNode(
                    x=0.5, y=0.5, w=0.3, h=0.2, theta=0.0, scale=512.0,
                    theme="polaroid", src=r"$My Pictures\lake\a.jpg",
                ),
            ),
        )

        nodes = nodes_from_project(projekt)

        assert Path(nodes[0].path) == kepmappa / "lake" / "a.jpg"

    def test_a_feloldhatatlan_utvonal_valtozatlanul_jut_at(self, kepmappa):
        """Nem dobunk kivételt, és nem találunk ki útvonalat."""
        nyers = r"$UNC\\szerver\meg\a.jpg"
        projekt = CxfProject(
            aspect_ratio="15:10",
            orientation="landscape",
            theme="picturepile",
            shadows=True,
            captions=True,
            album_uid="",
            album_title="",
            album_date="",
            background=CxfBackground(type="solid", color="FF000000"),
            spacing=0.25,
            nodes=(
                CxfNode(
                    x=0.5, y=0.5, w=0.3, h=0.2, theta=0.0, scale=512.0,
                    theme="polaroid", src=nyers,
                ),
            ),
        )

        nodes = nodes_from_project(projekt)

        assert nodes[0].path == nyers


class TestAHatterIsFeloldodik:
    """A `.cxf` a HÁTTERET is kódolt alakban tárolja (#1096 × #1085/#1103).

    A háttérkép a panelen INDEXKÉNT él (a kollázs saját képeinek egyike), a
    `.cxf` viszont útvonalat tárol — a visszaállítás a csomópontok közt
    keresi meg. Ha a csomópontok útvonala már feloldva van, a HÁTTERÉT is
    fel kell oldani, különben az egyezés sosem jön össze, és a háttér némán
    színre esik vissza. Ez pontosan az a hiba, amit a #1085/#1103 javított —
    csak az eredeti Picasa fájljain jelentkezne újra.
    """

    def test_a_hatter_utvonala_ugyanoda_oldodik_fel(self, kepmappa):
        kodolt = r"$My Pictures\lake\a.jpg"

        assert Path(decode_cxf_path(kodolt)) == kepmappa / "lake" / "a.jpg"

    def test_a_csomopont_es_a_hatter_UGYANAZT_adja(self, kepmappa):
        """A két oldal ugyanazon a leképezésen megy át — ez az egyezés
        feltétele."""
        kodolt = r"$My Pictures\AI\hatter.png"
        projekt = CxfProject(
            aspect_ratio="15:10",
            orientation="landscape",
            theme="picturepile",
            shadows=True,
            captions=True,
            album_uid="",
            album_title="",
            album_date="",
            background=CxfBackground(type="image", color="FF000000", src=kodolt),
            spacing=0.25,
            nodes=(
                CxfNode(
                    x=0.5, y=0.5, w=0.3, h=0.2, theta=0.0, scale=512.0,
                    theme="polaroid", src=kodolt,
                ),
            ),
        )

        nodes = nodes_from_project(projekt)

        assert nodes[0].path == decode_cxf_path(projekt.background.src)

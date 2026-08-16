"""A `.cxf` kollázs-projektfájl írása és olvasása (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.6, 1.6/b, 1.6/c — a
formátum a felhasználó valódi, a windowsos Picasával készített mintájából
lett megfejtve (#436).
"""

from __future__ import annotations

import pytest

from picasapy.collage.cxf import (
    CXF_VERSION,
    CxfBackground,
    CxfNode,
    CxfProject,
    dumps,
    loads,
    read_cxf,
    write_cxf,
)

# A spec 1.6 mintája, a valódi fájl szerkezetével.
MINTA = (
    '<?xml version="1.0" encoding="utf-8" ?>\r\n'
    '<collage version="2" format="15:10" orientation="portrait"'
    ' theme="picturepile" shadows="1" captions="1"'
    ' albumUID="a4ef8e0fd2dbb152d25d79eb2bd2a28b">\r\n'
    " <albumTitle>AI</albumTitle>\r\n"
    " <albumDate>2023. november</albumDate>\r\n"
    ' <background type="solid" color="FFFFFFFF"/>\r\n'
    ' <spacing value="0.000000"/>\r\n'
    ' <node x="0.297852" y="0.248047" w="0.274210" h="0.219401"'
    ' theta="-0.009167" scale="337.000000">\r\n'
    "  <theme>polaroid</theme>\r\n"
    "  <src>$My Pictures\\AI\\kep.png</src>\r\n"
    "  <uid>129d7730c524d5240000000000000000</uid>\r\n"
    " </node>\r\n"
    "</collage>\r\n"
).encode("utf-8")


def _projekt() -> CxfProject:
    return CxfProject(
        aspect_ratio="15:10",
        orientation="portrait",
        theme="picturepile",
        shadows=True,
        captions=True,
        album_uid="a4ef8e0fd2dbb152d25d79eb2bd2a28b",
        album_title="AI",
        album_date="2023. november",
        background=CxfBackground(type="solid", color="FFFFFFFF"),
        spacing=0.0,
        nodes=(
            CxfNode(
                x=0.297852,
                y=0.248047,
                w=0.274210,
                h=0.219401,
                theta=-0.009167,
                scale=337.0,
                theme="polaroid",
                src="$My Pictures\\AI\\kep.png",
                uid="129d7730c524d5240000000000000000",
            ),
        ),
    )


# --- Olvasás ----------------------------------------------------------------


def test_a_valodi_minta_beolvasasa():
    projekt = loads(MINTA)
    assert projekt.version == CXF_VERSION == 2
    assert projekt.aspect_ratio == "15:10"
    assert projekt.orientation == "portrait"
    assert projekt.theme == "picturepile"
    assert projekt.shadows is True
    assert projekt.captions is True
    assert projekt.album_uid == "a4ef8e0fd2dbb152d25d79eb2bd2a28b"
    assert projekt.album_title == "AI"
    assert projekt.album_date == "2023. november"
    assert projekt.background == CxfBackground("solid", "FFFFFFFF")
    assert projekt.spacing == 0.0


def test_a_keret_KEPENKENT_all_nem_a_gyokerben():
    """A meglepetés a formátumban: a `<theme>` a `<node>`-on BELÜL van.

    A felület globálisnak mutatja, de az adatmodell megengedi a vegyes
    kollázst — ezért olvassuk csomópontonként."""
    (node,) = loads(MINTA).nodes
    assert node.theme == "polaroid"


def test_a_csomopont_mezoi():
    (node,) = loads(MINTA).nodes
    assert (node.x, node.y) == pytest.approx((0.297852, 0.248047))
    assert (node.w, node.h) == pytest.approx((0.274210, 0.219401))
    assert node.theta == pytest.approx(-0.009167)
    assert node.scale == pytest.approx(337.0)
    assert node.src == "$My Pictures\\AI\\kep.png"
    assert node.uid == "129d7730c524d5240000000000000000"


def test_a_src_valtozo_behelyettesitese_ERINTETLEN_marad():
    """Az `$My Pictures\\…` alakot szó szerint őrizzük — a feloldás az
    útvonal-réteg dolga, nem a formátumé. Ha itt „megjavítanánk", a fájl
    az eredeti Picasában használhatatlan lenne."""
    (node,) = loads(MINTA).nodes
    assert node.src.startswith("$My Pictures\\")
    assert "\\" in node.src  # windowsos fordított perjel, nem `/`


def test_a_nulla_kapcsolo_hamis():
    adat = MINTA.replace(b'shadows="1" captions="1"', b'shadows="0" captions="0"')
    projekt = loads(adat)
    assert projekt.shadows is False
    assert projekt.captions is False


# --- Írás -------------------------------------------------------------------


def test_a_kimenet_UTF8_es_CRLF():
    adat = dumps(_projekt())
    assert isinstance(adat, bytes)
    assert adat.startswith(b'<?xml version="1.0" encoding="utf-8" ?>\r\n')
    assert b"\r\n" in adat
    # nincs magányos LF (minden sorvég CRLF)
    assert adat.replace(b"\r\n", b"").count(b"\n") == 0


def test_az_ekezetes_cim_utf8_kent_megy_ki():
    projekt = CxfProject(album_title="Nyaralás — Görögország")
    assert "Nyaralás — Görögország".encode() in dumps(projekt)


def test_a_lebegopontos_mezok_hat_tizedessel_irodnak():
    """A Picasa `%f`-fel ír; a `theta` és a `scale` hat tizedese az, amit
    egy visszaolvasás pontosan visszaad."""
    adat = dumps(_projekt()).decode("utf-8")
    assert 'theta="-0.009167"' in adat
    assert 'scale="337.000000"' in adat
    assert 'value="0.000000"' in adat


def test_a_kapcsolok_egy_es_nulla():
    adat = dumps(CxfProject(shadows=True, captions=False)).decode("utf-8")
    assert 'shadows="1"' in adat
    assert 'captions="0"' in adat


def test_az_xml_karakterek_vedve_vannak():
    """Egy `&`-et vagy `<`-t tartalmazó albumcím nem törheti el a fájlt."""
    adat = dumps(CxfProject(album_title="Anyu & Apu <2020>")).decode("utf-8")
    assert "&amp;" in adat and "&lt;" in adat
    assert loads(adat).album_title == "Anyu & Apu <2020>"


# --- Oda-vissza -------------------------------------------------------------


def test_korbejaras_bajtra_azonos():
    """A `.cxf`-ből visszatöltésnek PONTOSNAK kell lennie — ez az egyetlen
    dolog, amit a nem determinisztikus Mozaiknál is garantálunk."""
    eredeti = dumps(_projekt())
    assert dumps(loads(eredeti)) == eredeti


def test_korbejaras_a_valodi_mintarol():
    projekt = loads(MINTA)
    assert loads(dumps(projekt)) == projekt


def test_alapertelmezesek_a_binarisbol():
    """`CollageSpec` (0x008342b0): téma `picturepile`, oldalarány 4:3,
    háttér `FF000000` (átlátszatlan fekete)."""
    projekt = CxfProject()
    assert projekt.theme == "picturepile"
    assert projekt.aspect_ratio == "4:3"
    assert projekt.background == CxfBackground("solid", "FF000000")
    assert projekt.nodes == ()


# --- Fájlműveletek ----------------------------------------------------------


def test_iras_es_olvasas_fajlbol(tmp_path):
    cel = tmp_path / "alkonyat" / "kollazs.cxf"
    write_cxf(cel, _projekt())
    assert cel.exists()
    assert read_cxf(cel) == _projekt()


def test_a_fajl_nyers_bajtjai_nem_alakulnak_at(tmp_path):
    """Szövegmódú írásnál a Python Linuxon LF-et írna — ezért bájt-alapú
    az IO, ahogy a `write_collage`-nál is (#190)."""
    cel = tmp_path / "kollazs.cxf"
    write_cxf(cel, _projekt())
    assert b"\r\n" in cel.read_bytes()


# --- Hibák ------------------------------------------------------------------


def test_rossz_gyokerelem():
    with pytest.raises(ValueError, match="collage"):
        loads(b'<?xml version="1.0"?><movie/>')


def test_ismeretlen_kollazs_tipus():
    with pytest.raises(ValueError, match="Ismeretlen kollázs-típus"):
        CxfProject(theme="kacsa")


def test_ismeretlen_keret_a_csomoponton():
    with pytest.raises(ValueError, match="Ismeretlen képkeret"):
        CxfNode(0.0, 0.0, 0.1, 0.1, 0.0, 10.0, theme="kacsa")


def test_ervenytelen_hatterszin():
    with pytest.raises(ValueError, match="ARGB"):
        CxfBackground("solid", "FFF")


def test_ervenytelen_terkoz():
    with pytest.raises(ValueError):
        CxfProject(spacing=1.5)


def test_serult_xml():
    with pytest.raises(ValueError):
        loads(b"<collage")

"""#2118: az Indexkép keretrajzát önálló őr védje.

## Miért kell

A keretrajz **helyes** — de egyetlen próba sem állította. A meglévő
`test_indexkep_1273.py::test_az_AI6_racsa_…` `WHITEBORDER`-rel mér az
`AI6.cxf` golden ellen, a **tűrése viszont elnyeli a keret elhagyását**:
ugyanaz az eset `noborder`-rel is átmegy (0,0017 / 0,0023 eltérés a
0,01 / 0,005 tűrésen belül). A `test_render_nodes_942.py` sem fogja meg —
az Indexképnél kimondottan `assert eltero > 0`-t állít, a keret-állások
KÖZTI különbséget nem nézi.

⇒ Ha valaki visszaállítaná a keret nélküli rajzot (pl. az
`effective_border`-t újra a `REGULARGRID` képességére kötné), a készlet
**zöld maradna**.

## Mit állít ez az őr

Nem golden-egyezést — azt a #1273 őrzi. Azt állítja, hogy a három
keret-állás **mérhetően külön geometriát** ad, tehát a keret tényleg hat.
Ez az a tulajdonság, amit a tűrés nem tud elnyelni.

**A mérés beállítása** (a számok ehhez tartoznak): `CONTACTSHEET` téma,
`800 × 600` lap, **hat** kép, mind `0.8` oldalarányú, cím „AI",
dátum „2023. november". Más aspektus-készlet más számokat ad — ezért áll
itt a beállítás is, nem csak az eredmény.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    layout_nodes_for_aspects,
)
from picasapy.collage.themes import CONTACTSHEET, NOBORDER, POLAROID, WHITEBORDER

ASPEKTUSOK = (0.8,) * 6
UTAK = tuple(Path(f"{i}.png") for i in range(6))

#: keret -> az ELSŐ csomópont mért szélessége/magassága lapegységben.
#:
#: #2583 óta a magasság `w / képarány` (a KIRAJZOLT kép doboza), nem a
#: cellamagasság — ezért a három keret-állás magassága is SZÉTVÁLIK (a
#: szélességgel arányosan), nem csak a szélessége. A számok újramérve a
#: javítás UTÁN; a docstring alján lévő 90. sor körüli megjegyzés a
#: RÉGI (hibás) viselkedést írta le.
MERT = {
    NOBORDER: (197.12, 247.04),
    WHITEBORDER: (200.96, 250.88),
    POLAROID: (156.16, 195.84),
}


def _elso_csomopont(border):
    beallitas = PicasaCollageSettings(
        theme=CONTACTSHEET,
        border=border,
        width=800,
        height=600,
        album_title="AI",
        album_date="2023. november",
    )
    return layout_nodes_for_aspects(ASPEKTUSOK, UTAK, beallitas)[0]


@pytest.mark.parametrize(("border", "vart"), sorted(MERT.items(), key=lambda x: str(x[0])))
def test_a_keret_merheto_geometriat_ad(border, vart) -> None:
    csomopont = _elso_csomopont(border)
    assert csomopont.border == border
    assert (csomopont.width, csomopont.height) == pytest.approx(vart, abs=0.01)


def test_a_harom_keret_SZELESSEGE_kulonbozik() -> None:
    """A foga: EZ bukik el, ha a keretrajz visszaáll keret nélkülire.

    #2583 előtt a magasság önmagában nem lett volna elég — a `noborder`
    és a `whiteborder` magassága AZONOS volt (a cella magassága volt a
    korlát), tehát a különbség csak a szélességen látszott. A #2583 óta a
    magasság is szétválik (`h = w / képarány`, ld. lent), de a szélesség
    marad a legegyszerűbb, közvetlen mérték a keret hatására.
    """
    szelessegek = {b: _elso_csomopont(b).width for b in MERT}
    assert len({round(v, 2) for v in szelessegek.values()}) == 3, (
        "a három keret-állás geometriája nem különbözik: " + str(szelessegek)
    )
    assert szelessegek[WHITEBORDER] > szelessegek[NOBORDER], (
        "a fehér keret NEM szűkíti a képet — a keretrajz hatástalan"
    )
    assert szelessegek[POLAROID] < szelessegek[NOBORDER], (
        "a polaroid keret NEM szélesebb a képnél"
    )


def test_a_magassag_a_szelesseggel_aranyosan_ter_el_kerettol_fuggoen() -> None:
    """#2583 óta a `h` a `w / képarány` — NEM a cellamagasság korlátozza.

    Régebben (a jegy előtt) ez a próba az ELLENKEZŐJÉT állította: a
    `noborder` és a `whiteborder` magassága AZONOS volt, mert mindkettő a
    cella magasságára volt levágva, és a kép saját aránya nem jutott
    érvényre a `h` mezőben. A #2583 pontosan ezt a hibát javítja
    (kollazs-eletciklus.md 18.5/18.8): a keret a SZÉLESSÉGET módosítja, a
    magasságnak ennek megfelelően, a KÉP ARÁNYÁVAL kell követnie — tehát a
    magasságnak is szét kell válnia a keret-állások közt."""
    a = _elso_csomopont(NOBORDER)
    b = _elso_csomopont(WHITEBORDER)
    assert a.height != pytest.approx(b.height, abs=0.01)
    # mindkettő ugyanazt az oldalarányt (0,8) követi a saját szélességéből
    assert a.height / a.width == pytest.approx(1.0 / 0.8, abs=0.01)
    assert b.height / b.width == pytest.approx(1.0 / 0.8, abs=0.01)

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
MERT = {
    NOBORDER: (194.56, 254.72),
    WHITEBORDER: (198.40, 254.72),
    POLAROID: (153.60, 253.44),
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

    A magasság önmagában nem elég — a `noborder` és a `whiteborder`
    magassága AZONOS ebben a lapméretben (a cella magassága a korlát),
    tehát a különbség csak a szélességen látszik.
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


def test_a_magassag_a_noborder_es_whiteborder_kozt_AZONOS() -> None:
    """Kimondva, hogy ne tűnjön hiánynak: ebben a lapméretben a cella
    magassága a korlát, ezért a magasságból nem derül ki a keret. Ha ez
    egyszer megváltozna, ez a próba szól — és akkor a fenti őr bővíthető."""
    a = _elso_csomopont(NOBORDER).height
    b = _elso_csomopont(WHITEBORDER).height
    assert a == pytest.approx(b, abs=0.01)

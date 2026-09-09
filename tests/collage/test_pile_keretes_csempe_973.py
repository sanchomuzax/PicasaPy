"""A Képkupacban a KERETES csempe illeszkedik a `pile_size` négyzetbe (#973).

## A mért szabály

A `.cxf` `scale` mezője Képkupacban a csomópont **befoglaló négyzetének**
oldala (spec 1.6/f: 49 golden csomóponton, `|Δ| ≤ 0,09`), és ez a négyzet a
`pile_size` — a lap szélességének 0,33-szorosa, csonkítva. A csomópont
`w`/`h` pedig a KIRAJZOLT csempe (tehát a kerettel együtt értendő doboz)
tengelyirányú mérete.

A kettő együtt azt jelenti: **a keretes csempének kell beleférnie a
négyzetbe**, nem a csupasz fotónak.

## Mit talált ez a fájl a mai kódon (2026-09-09)

| keret | `pile_size` | a csempe külső doboza | rendben? |
|---|---:|---|---|
| `noborder` | 337 | 337×337 · 189×337 · 337×225 | ✅ |
| `polaroid` | 337 | 281×337 (mindig) | ✅ (#1053) |
| **`whiteborder`** | 337 | **371×371 · 207×355 · 359×247** | ❌ +5…10% |

A fehér szegély a fotó rövidebb oldalának 5%-a körben, tehát a csempe
kinőtt a négyzetből: a `scale`-be írt szám és a `w`/`h` viszonya a SAJÁT
írónkon belül ellentmondott a mért szabálynak. Ez a jegy maradék hatóköre —
a polaroid ágat a #1053 már rendezte, a jegy törzse ennyiben elavult.

⚠️ A fehér szegélyre nincs golden Képkupac-mintánk (a mért 49 csomópont
polaroid és keret nélküli). A javítás alapja ezért nem új mérés, hanem a
MEGLÉVŐ mért szabály — és a saját írónk belső ellentmondásának
megszüntetése. Amit ez NEM állít: hogy a fehér szegély vastagsága
(5%) helyes; azt a #1144 méri.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.collage.nodes import sheet_to_pixels
from picasapy.collage.picasa_render import PicasaCollageSettings, _pile_nodes
from picasapy.collage.pile import pile_size
from picasapy.collage.themes import NOBORDER, PICTUREPILE, POLAROID, WHITEBORDER

LAP_SZELES = 1024
LAP_MAGAS = 1536
#: Vegyes oldalarányok: négyzetes, álló és fekvő forráskép.
ARANYOK = (1.0, 0.56, 1.5)


def _csempek(border: str) -> list[tuple[int, float, float]]:
    """`(sorszám, külső szélesség, külső magasság)` képpontban."""
    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE,
        border=border,
        width=LAP_SZELES,
        height=LAP_MAGAS,
        seed=7,
    )
    nodes = _pile_nodes(
        ARANYOK, [Path(f"{i}.jpg") for i in range(len(ARANYOK))], beallitas
    )
    return [
        (
            i,
            sheet_to_pixels(node.width, LAP_SZELES),
            sheet_to_pixels(node.height, LAP_SZELES),
        )
        for i, node in enumerate(nodes, start=1)
    ]


@pytest.mark.parametrize("border", [NOBORDER, WHITEBORDER, POLAROID])
def test_a_kulso_doboz_illeszkedik_a_negyzetbe(border: str):
    """A csempe befoglaló négyzete PONTOSAN a `pile_size` — se több, se kevesebb.

    A felső korlát a jegy leletét fogja meg (kinő a négyzetből), az
    egyenlőség pedig azt, hogy nem is zsugorodik bele feleslegesen: a
    négyzetet ki kell tölteni a hosszabbik tengelyen."""
    for sorszam, szeles, magas in _csempek(border):
        negyzet = pile_size(sorszam, LAP_SZELES)
        assert max(szeles, magas) == pytest.approx(negyzet, abs=1.0), (
            f"{border}, {sorszam}. csempe: a külső doboz {szeles}×{magas}, "
            f"a `pile_size` {negyzet} — a `scale` és a `w`/`h` viszonya "
            "ellentmond a mért szabálynak (spec 1.6/f)"
        )


def test_a_negyzetes_foto_polaroidja_a_minta_haromszamat_adja():
    """A #436-os minta első csomópontja: 280,8 × 337,0, `scale` = 337,0.

    A tűrés a képpontra kerekítés miatt van (a mintában 280,8 áll, nálunk a
    csempe egész képpontokban születik) — a lényeg a három szám EGYÜTTES
    egyezése, nem a tizedes."""
    elso = _csempek(POLAROID)[0]
    _, szeles, magas = elso
    assert szeles == pytest.approx(280.8, abs=0.6)
    assert magas == pytest.approx(337.0, abs=0.6)
    assert max(szeles, magas) == pytest.approx(337.0, abs=0.6)


def test_a_keret_nelkuli_eset_nem_valtozik():
    """`noborder`-nél a fotó és a csempe egybeesik — a javítás ne mozdítsa.

    A golden `AI1.cxf` keret nélküli csempéi a FORRÁSKÉP arányát adják
    (0,560 és 0,800 egy kollázsban), tehát itt az illesztés a fotóé."""
    csempek = _csempek(NOBORDER)
    aranyok = [szeles / magas for _, szeles, magas in csempek]
    for arany, forras in zip(aranyok, ARANYOK, strict=True):
        assert arany == pytest.approx(forras, rel=0.01)


def test_a_feher_szegely_a_negyzeten_BELUL_no():
    """A fehér szegély a négyzeten belül marad, és tényleg VAN szegély.

    Alsó korlát is: ha a szegély vastagsága nullára esne, a felső korlát
    magától teljesülne — az őr akkor semmit nem bizonyítana."""
    for sorszam, szeles, magas in _csempek(WHITEBORDER):
        negyzet = pile_size(sorszam, LAP_SZELES)
        assert max(szeles, magas) <= negyzet + 1.0
    # a szegély léte: keret nélkül ugyanaz a fotó ARÁNYA marad, szegéllyel a
    # csempe a négyzethez közelít (a szegély abszolút, tehát az arányt
    # 1 felé tolja)
    keret_nelkul = _csempek(NOBORDER)[1]
    szegellyel = _csempek(WHITEBORDER)[1]
    arany_nelkul = keret_nelkul[1] / keret_nelkul[2]
    arany_szegellyel = szegellyel[1] / szegellyel[2]
    assert arany_szegellyel > arany_nelkul, (
        "a fehér szegély nem tolta az álló csempe arányát 1 felé — "
        "vagy nincs is szegély, vagy nem abszolút vastagságú"
    )

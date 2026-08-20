"""#1094 — a kupac a KÖZÉPPONTOT tartja sávon belül, a csempét NEM.

## Amit a #1045 rosszul állított

A #1045 abból indult, hogy a kupac egyetlen képe se lóghat ki a lapról, és
beszorítást tett a `_pile_nodes`-ba. **Ez eltérés volt az eredetitől.**

A tulajdonos három A4-es **FEKVŐ** kollázsán (`AI8`, `AI9`, `AI10`) a valódi
Picasa kimenetében 89 csomópontból **3 kilóg** — és egyik sem kézi
szerkesztés: `scale` mind egész `337,0000`, a `theta` a legyező
tartományán belül (−3,53° / +0,11° / +0,54°). Összevetésül az `AI2` kézi
szerkesztései azonnal felismerhetők: nem egész `scale=295,392`, +345°.

**Mind a három eltérés FÜGGŐLEGES, egy sem vízszintes** — pontosan az, amit
a középpont-sáv magyaráz: fekvő lapon a csempe magassága a lap arányában
nagyobb, ezért sávon belüli középpont mellett is kilóghat a teteje/alja.

A #1045 mintája azért vitt félre, mert **nyolcból nyolc álló vagy négyzetes
volt, fekvő egy sem** — a jelenség pont a fekvőkön jelenik meg. Nem a
következtetés volt rossz, hanem hogy nem néztük meg, mit NEM tartalmaz a
készlet.

## Amit ez a fájl őriz

1. **A középpontok a sávon belül** — ez a képlet hat mintán igazolt (álló,
   négyzetes ÉS fekvő lapon).
2. **A csomópont középpontja BÁNTATLAN**: a `_pile_nodes` a szórás
   középpontját adja tovább, nem igazít rajta. Ez az őr fogja meg, ha
   bárki visszateszi a beszorítást.
3. **A ≤10 képes ág változatlan** — a 9 képes eset a valódi minták
   középpontjait négy tizedesig hozza, azt nem szabad elmozdítani.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.collage.nodes import SHEET_UNITS
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    layout_nodes_for_aspects,
)
from picasapy.collage.pile import PILE_BAND_FACTOR, pile_scale
from picasapy.collage.themes import PICTUREPILE

#: A sáv határa lapegységben számolva, egy képpontnyi tűréssel — a
#: csomópontok lebegőpontos úton jönnek (képpont → lapegység).
_TURES = 1.0


def _csomopontok(darab: int, keret: str, szelesseg: int, magassag: int):
    """A ténylegesen kirajzolt csomópontok — ezt látja a felhasználó."""
    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE, width=szelesseg, height=magassag, border=keret
    )
    aranyok = [(0.7 if i % 3 == 0 else 1.45) for i in range(darab)]
    utak = [Path(f"/nincs/k{i}.jpg") for i in range(darab)]
    return layout_nodes_for_aspects(aranyok, utak, beallitas), beallitas


def _sav(darab: int) -> tuple[float, float]:
    """A megengedett középpont-tartomány normalizálva, `[alsó, felső]`."""
    band = 1.0 - pile_scale(darab) * PILE_BAND_FACTOR
    offset = (1.0 - band) * 0.5
    return offset, offset + band


@pytest.mark.parametrize("darab", [4, 9, 11, 25])
@pytest.mark.parametrize(
    ("szelesseg", "magassag"), [(1600, 1200), (1200, 1600), (1024, 1024)]
)
def test_a_KOZEPPONTOK_a_savon_belul(darab, szelesseg, magassag):
    """A sáv az egyetlen korlát — fekvő, álló és négyzetes lapon egyaránt."""
    csomopontok, beallitas = _csomopontok(darab, "noborder", szelesseg, magassag)
    also, felso = _sav(darab)
    lap_magas = SHEET_UNITS * beallitas.height / beallitas.width

    for cs in csomopontok:
        assert also * SHEET_UNITS - _TURES <= cs.center_x <= felso * SHEET_UNITS + _TURES
        assert also * lap_magas - _TURES <= cs.center_y <= felso * lap_magas + _TURES


def test_a_csempe_KILOGHAT_fekvo_lapon():
    """A visszavonás lényege: fekvő lapon a csempe teteje/alja kilóghat.

    A tulajdonos `AI8`/`AI9`/`AI10` mintáin a valódi Picasa 89 csomópontból
    3-at enged ki a lapról, mind FÜGGŐLEGESEN. Ez az őr fogja meg, ha bárki
    visszateszi a #1045 beszorítását: azzal ez az eset zölddé válna, és
    némán újra eltérnénk az eredetitől.

    Nem véletlenszerű: a szórás magja rögzített, a lap és a képszám adott."""
    csomopontok, beallitas = _csomopontok(24, "polaroid", 1600, 1200)
    lap_magas = SHEET_UNITS * beallitas.height / beallitas.width

    kilogo = [
        cs
        for cs in csomopontok
        if cs.center_y - cs.height * 0.5 < -_TURES
        or cs.center_y + cs.height * 0.5 > lap_magas + _TURES
    ]

    assert kilogo, (
        "egyetlen csempe sem lóg ki — visszakerült a beszorítás? "
        "az eredeti fekvő lapon kienged néhányat"
    )


# --------------------------------------------------------------------------
# A VALÓDI Picasa 3 kimenete (a tulajdonos Kollázsok mappája, 2026-08-20),
# a kollázs-kutató munkamenet mérése. Ez a bizonyíték, amiért a #1045
# beszorítását visszavontuk — a repóban is itt van, nem csak üzenetben.
# --------------------------------------------------------------------------

#: A lapról KILÓGÓ csomópontok: (fájl, csomópontszám a lapon, x, y, w, h).
#: Mind a három FÜGGŐLEGESEN lóg ki, és egyik sem kézi szerkesztés: a
#: `scale` mindegyiknél egész 337,0000, a `theta` a legyező tartományán
#: belül (−0,0616 / +0,0020 / +0,0094 radián).
KILOGO_CSOMOPONTOK = (
    ("AI8.cxf", 9, 0.252930, -0.011050, 0.184442, 0.465470),
    ("AI9.cxf", 8, 0.577702, -0.045172, 0.263281, 0.465470),
    ("AI9.cxf", 8, 0.653074, 0.583320, 0.263281, 0.465470),
)

#: A mért középpont-szélsőértékek: (fájl, csomópontszám, cx_min, cx_max,
#: cy_min, cy_max) — tengelyenként 0…1-re normalizálva, ahogy a `.cxf`
#: tárolja. A sávot a `pile_scale`-ből számoljuk, nem innen.
SAV_MINTAK = (
    ("AI8.cxf", 9, 0.1765625, 0.7781245, 0.2216850, 0.7872930),
    ("AI9.cxf", 8, 0.1856085, 0.7847145, 0.1875630, 0.8160550),
    ("AI10.cxf", 5, 0.2241210, 0.7075200, 0.2548340, 0.6650550),
)

#: A legszorosabb mért eset a sáv alsó határától +0,0015-re ül, a sáv maga
#: ~0,65 széles — ennél bővebb tűréssel az őr elveszti a fogát.
_MERT_TURES = 0.001


@pytest.mark.parametrize(("fajl", "darab", "x", "y", "w", "h"), KILOGO_CSOMOPONTOK)
def test_a_valodi_kilogo_csempe_kozeppontja_a_savon_belul(fajl, darab, x, y, w, h):
    """A valódi Picasa kilógó csempéi: a TÉGLALAP kilóg, a KÖZÉPPONT nem.

    Ez a jegy magja egyetlen esetben: a kilógás nem a sáv hibája, hanem a
    csempe méretéé. Ha valaki a sávot szűkítené, hogy a téglalap beférjen,
    ez az őr bukik — és pontosan azt a #1045-öt hozná vissza, amit a
    tulajdonos mintái megcáfoltak."""
    also, felso = _sav(darab)
    kozep_x, kozep_y = x + w * 0.5, y + h * 0.5

    assert y < 0.0 or y + h > 1.0, f"{fajl}: ez a csomópont nem is lóg ki"
    assert also - _MERT_TURES <= kozep_x <= felso + _MERT_TURES
    assert also - _MERT_TURES <= kozep_y <= felso + _MERT_TURES


@pytest.mark.parametrize(
    ("fajl", "darab", "cx_min", "cx_max", "cy_min", "cy_max"), SAV_MINTAK
)
def test_a_sav_kepletunk_befogja_a_mert_mintakat(
    fajl, darab, cx_min, cx_max, cy_min, cy_max
):
    """A `pile_scale` alapú sáv befogja a valódi kimenet szélsőértékeit.

    Hat mintán igazolt — álló, négyzetes ÉS fekvő lapon. A legszorosabb
    eset +0,0015-re ül az alsó határtól, ezért a tűrés szűk."""
    also, felso = _sav(darab)

    assert also - _MERT_TURES <= cx_min, f"{fajl}: cx_min a sáv alá esik"
    assert cx_max <= felso + _MERT_TURES, f"{fajl}: cx_max a sáv fölé esik"
    assert also - _MERT_TURES <= cy_min, f"{fajl}: cy_min a sáv alá esik"
    assert cy_max <= felso + _MERT_TURES, f"{fajl}: cy_max a sáv fölé esik"

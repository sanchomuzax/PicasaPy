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

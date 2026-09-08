"""A kollázs-tesztek közös kapui.

## ⚠️ #1043: a pakoló órája MINDEN kollázs-teszt alatt rögzített

A Mozaik pakolója (`collage/packing.py::pack`) **időkorlátos keresés**: fél
másodpercig sorsol új képsorrendeket, és a legolcsóbbat tartja meg. **Hány**
jelöltet néz meg, az a gép pillanatnyi terheltségétől függ — terhelt gépen
kevesebbet, tehát MÁS elrendezést talál. A termékben ez szándékos — az
eredeti Picasa is a valós órához köti a keresést (spec 1.9.7:
`docs/specs/picasa-create-features.md`) —, a tesztben viszont azt
jelentené, hogy a mérés a GÉPET méri, nem a kódot.

**Mért bizonyíték (#1043, 2026-09-08)** A #942 bájtazonossági őre
(`test_render_nodes_942.py`) a régi és az új rajzolót egymás után futtatja;
a rácsos témákon (`picturegrid`, `framegrid`) mindkét oldal KÜLÖN futtatja a
keresést, két különböző pillanatban. Ugyanazon a négymagos gépen, ugyanazzal
a terheléssel (négy számoló folyamat; terhelési átlag 4,1 → 8,0):

| a pakoló órája | mérés | eltérő eset |
|---|---|---|
| valódi `time.perf_counter` | 108 | **5** (92 304 és 78 266 képpont: a vászon 72,9% és 61,8%-a) |
| lépkedő számláló (ez a fixture) | 288 | **0** |

Terhelés nélkül a valódi óra is tiszta volt (72 mérés, 0 eltérés) — pontosan
ez tette a jelenséget „megmagyarázhatatlanná": a hiba csak terhelés alatt jön
elő, és a rajzolóra tereli a gyanút.

**A jegy eredeti hipotézise (néma dekódolási hiba) MÉRVE MEGDŐLT:** ugyanez a
mérés 7560 dekódolást számolt meg, ebből **nulla** adott `None`-t — se
terhelés alatt, se anélkül. A dekódolási ág hangos jelzése (#2406) attól még
helyes védelem, csak nem ez okozta a #1043-at.

## Miért itt, és nem egyetlen tesztlapon

A #1018 ugyanezt a cserét MÁR elvégezte — de csak a `test_render_nodes_942.py`
lapján belül. A kockázat viszont nem egy lapé: minden kollázs-teszt, amely
rácsos témát rajzol (és főleg amelyik KÉT rajzot vet össze), ugyanezen az úton
mér véletlenszerűen. A fixture ezért a csomag egészére áll oda.

Mellékhaszon: a rögzített keret miatt a keresés nem tölti ki a fél
másodpercet — a `tests/collage` teljes futása terheletlen gépen **25,9 s**
helyett **11,0 s**.

## A kapu

A szabály mellé kapu jár, különben csak remény. Kettő van:

1. a `test_render_nodes_942.py` bájtazonossági őre a rácsos témákon
   ÁLLÍTJA, hogy a lenti számláló megmozdult (a fixture ezért adja vissza
   az állapotát);
2. a `test_pakolo_ora_kapu_1043.py` őrzi magát a patch-pontot: hogy a
   `pack` `clock=` nélkül tényleg a `packing._perf_counter`-t olvassa, és
   hogy a termékkód egyetlen hívása sem ad saját órát.
"""

from __future__ import annotations

import pytest

from picasapy.collage import packing


#: Hány jelöltet nézzen meg a pakoló a tesztek alatt. Elég nagy ahhoz, hogy a
#: keresés érdemi legyen, és elég kicsi, hogy a készlet gyorsan lefusson.
PAKOLASI_LEPESEK = 400


@pytest.fixture(autouse=True)
def determinisztikus_pakolas(monkeypatch):
    """A pakoló óráját LÉPKEDŐ számlálóra cseréli (ld. a lap tetejét).

    Minden órakérdés fix lépéssel halad, tehát a keresés mindig UGYANANNYI
    jelöltet néz meg — a mérés így a rajzot méri, nem a gépet. A produkciós
    viselkedés változatlan: a valódi órát csak a teszt cseréli le.

    A fixture **visszaadja a saját számlálóját**, hogy a rá támaszkodó őrök
    állíthassák: a csere tényleg hatott. Ez a #1043 kapuja — enélkül egy
    későbbi változás (átnevezett `_perf_counter`, saját `clock=` a hívónál)
    NÉMÁN visszahozná a terhelésfüggést."""
    allapot = {"t": 0.0, "orakerdes": 0}

    def _lepkedo() -> float:
        allapot["orakerdes"] += 1
        allapot["t"] += packing.PACK_TIME_LIMIT / PAKOLASI_LEPESEK
        return allapot["t"]

    monkeypatch.setattr(packing, "_perf_counter", _lepkedo)
    return allapot

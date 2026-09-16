"""#3195 — az ÜRES finetune-p4 nem viheti el az egész szűrőbejegyzést.

## A lelet

A `finetune`/`finetune2` negyedik paramétere a semleges szín (AARRGGBB). Ha
ÜRESEN állt (`,,`), a `parse_neutral_argb` kivételt dobott, a lánc pedig a
teljes bejegyzést kihagyta — tehát a **Derítőfény, a Csúcsfények, az Árnyékok
ÉS a Színhőmérséklet** beállítása is NÉMÁN elveszett, egyetlen hiányzó mező
miatt.

## Miért nem éles hiba, és miért javítjuk mégis

A referencia-korpuszban az eredeti Picasa **mindig kiírja** a `00000000`-t, ha
nincs semleges szín — üres p4 egyetlen valódi fájlban sem fordul elő. A
`.picasa.ini` viszont kézzel is szerkeszthető, és a projekt elve szerint egy
hibás mező nem viheti el az egész beolvasást (#301).

## A határ, amit ez az őr kimond

| p4 | eredmény |
|---|---|
| `00000000` | nincs semleges szín (alfa 0) |
| **üres** | nincs semleges szín — ÉS a bejegyzés lefut (#3195) |
| `006b8088` | nincs semleges szín (alfa 0), a szín mellékes |
| `ff6b8088` | van semleges szín |
| `zzz`, `12`, `#abcdef` | **kivétel** — a felhasználó írt valamit, aminek jelentése lett volna |
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.tone import parse_neutral_argb


@pytest.fixture
def minta() -> np.ndarray:
    rng = np.random.default_rng(3195)
    return rng.integers(0, 256, (24, 32, 3), dtype=np.uint8)


class TestAzUresP4:
    def test_az_ures_mezo_None(self):
        assert parse_neutral_argb("") is None
        assert parse_neutral_argb("   ") is None

    def test_a_nulla_alfa_is_None(self):
        """A mért, valódi alak — ez eddig is működött."""
        assert parse_neutral_argb("00000000") is None
        assert parse_neutral_argb("006b8088") is None

    def test_a_valodi_szin_atjon(self):
        assert parse_neutral_argb("ff6b8088") == (0x6B, 0x80, 0x88)

    @pytest.mark.parametrize("hibas", ["zzz", "12", "#abcdef", "gg000000"])
    def test_a_hibas_de_nem_ures_alak_KIVETEL(self, hibas):
        """A tűrés nem terjed ki arra, ami értelmezhetőnek LÁTSZIK."""
        with pytest.raises(ValueError):
            parse_neutral_argb(hibas)


class TestALancLefut:
    #: ugyanaz a lánc, csak a p4 más — a kettő kimenete EGYEZIK
    URES = "finetune=1,0.4,0.3,0.2,,0.250000;"
    NULLAS = "finetune=1,0.4,0.3,0.2,00000000,0.250000;"

    def test_az_ures_p4_mellett_a_bejegyzes_LEFUT(self, minta):
        jelentes = apply_filters(minta, parse_filters(self.URES))
        assert jelentes.skipped == (), (
            "az üres p4 miatt kihagyva a bejegyzés — a Derítőfény, a "
            "Csúcsfények, az Árnyékok és a Színhőmérséklet mind elveszett"
        )

    def test_a_kimenet_egyezik_a_nullas_alakkal(self, minta):
        ures = apply_filters(minta, parse_filters(self.URES))
        nullas = apply_filters(minta, parse_filters(self.NULLAS))
        np.testing.assert_array_equal(ures.image, nullas.image)

    def test_a_kep_tenyleg_valtozik(self, minta):
        """A fenti egyezés önmagában akkor is teljesülne, ha EGYIK sem hatna."""
        jelentes = apply_filters(minta, parse_filters(self.URES))
        assert not np.array_equal(jelentes.image, minta), (
            "a lánc nem változtatta meg a képet — a próba vakon zöld lenne"
        )

"""#1170: a képesség-maszk **6. bitje** — a kollázs csoport-csomópontja.

A bit jelentése 2026-08-21-ig „nem megállapított" volt. A megfejtés
(`docs/specs/picasa-kollazs-felulet.md` **2.** és **2/b**): a bit teszi a
`collagepanel/groupnode` csomópontot **külön, overlay feldolgozási ágba**,
a szokásos, szülőhöz kötött bejárás helyett.

```asm
0x0086046e  call edx        ; a téma képesség-maszkja (vt[0x1c])
0x00860470  shr  eax, 6
0x00860473  test al, 1      ; << a 6. BIT
0x00860475  je   0x86054f   ; nincs -> kihagyja
```

Ez a fájl két dolgot rögzít: hogy a bit **pontosan** a három rács-témánál
áll, és hogy a `themes.py` fejléce nem hirdeti tovább nyitottnak.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.collage import themes
from picasapy.collage.themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
    capabilities_for,
    capability_map,
)

#: A három RÁCS-téma — a jegy szerint pontosan ezek kapják a bitet.
RACS_TEMAK = {PICTUREGRID, FRAMEGRID, REGULARGRID}


class TestHatodikBit:
    @pytest.mark.parametrize(
        "tema",
        [PICTUREPILE, PICTUREGRID, FRAMEGRID, REGULARGRID, CONTACTSHEET, MULTIEXP],
    )
    def test_pontosan_a_harom_racs_temanal_all(self, tema):
        """A maszkokból FÜGGETLENÜL leírva: 0x1C55, 0x1C55, 0x0C55 → 6. bit
        áll; 0x1EBBF, 0x4B11, 0x0100 → nem áll."""
        assert capabilities_for(tema).group_overlay is (tema in RACS_TEMAK)

    def test_a_kepesseg_terkep_kiadja_a_felulettnek(self):
        """A QML a `collageCapabilities` térképből dolgozik — ha a mező nem
        kerül bele, a vászon sosem tudja meg, hogy rajzolhat."""
        for tema in (PICTUREPILE, PICTUREGRID, FRAMEGRID, REGULARGRID):
            terkep = capability_map(tema)
            assert "group_overlay" in terkep
            assert terkep["group_overlay"] is (tema in RACS_TEMAK)

    def test_a_regi_mezok_a_helyukon_maradtak(self):
        """Az ÚJ mező a sor VÉGÉN áll — a `NamedTuple` kicsomagolására épülő
        korábbi olvasatok (#923, #943) nem csúszhatnak el."""
        c = capabilities_for(PICTUREPILE)
        assert (c.borders, c.spacing, c.shadow, c.selection) == (
            True,
            False,
            True,
            True,
        )
        assert c._fields[-1] == "group_overlay"


class TestFejlec:
    """A jegy 1. pontja: a fejléc NE hirdesse tovább nyitottnak a bitet.

    Szövegre állítani szokatlan, de itt pont ez a szerződés: a lap fejléce
    a bit-tábla EGYETLEN olvasható forrása, és eddig épp az ellenkezőjét
    állította, mint amit a bizonyíték mutat."""

    @staticmethod
    def _forras() -> str:
        return Path(themes.__file__).read_text(encoding="utf-8")

    def test_nem_irja_tobbe_nyitottnak(self):
        forras = self._forras()
        assert "6. bit jelentése NYITOTT" not in forras

    def test_a_bit_tabla_visszakereshetoen_hivatkozik_a_cimre(self):
        forras = self._forras()
        assert "0x00860470" in forras
        assert "groupnode" in forras

"""A szűrőnév-illesztés kis-nagybetű-ÉRZÉKENY (#1141).

## Bizonyíték — eredeti Picasa-export, hat kép

A `PicasaPy merokit-2` mérőkit exportja (`export-202608151438`) szerint a
Picasa a nem kanonikus írásmódú tagot **nem futtatja le**; a mi
kimenetünk ugyanezeken a képeken 25–59 egységgel tért el a forrástól,
mert lefuttattuk:

| lánc | Picasa | mi (a javítás előtt) |
|---|---|---|
| `Tint=…` / `TINT=…` / `tInT=…` | nem fut (0,16 = újrakódolási zaj) | 58,86 ❌ |
| `vignette=…` / `VIGNETTE=…` | nem fut | 29,24 ❌ |
| `Sepia=1;` | nem fut | 25,57 ❌ |

A kanonikus alak mindhárom családban más mintázatú (`tint`, `Vignette`,
`sepia`) — tehát tényleg **bájtra pontos** egyezés kell, nem „csupa
kisbetű".

⚠️ A #1140-nel együtt ad helyes viselkedést: a rossz írásmódú tag nem
„kimarad", hanem **elvágja a lánc maradékát**.
"""

import numpy as np
import pytest

from picasapy.ini.filters import FilterOp, parse_filters_prefix
from picasapy.render import apply_filters


def _kep():
    tomb = np.zeros((16, 16, 3), dtype=np.uint8)
    tomb[:, :, 0] = 30
    tomb[:, :, 1] = 120
    tomb[:, :, 2] = 200
    return tomb


def _lefut(lanc: str) -> bool:
    """Változtatott-e a lánc a képen."""
    forras = _kep()
    eredmeny = apply_filters(forras.copy(), parse_filters_prefix(lanc))
    kep = eredmeny[0] if isinstance(eredmeny, tuple) else eredmeny.image
    return not np.array_equal(kep, forras)


class TestNemKanonikusNemFut:
    """A jegy hat mért esete."""

    @pytest.mark.parametrize(
        "lanc",
        [
            "Tint=1,79.842102,ffff;",
            "TINT=1,79.842102,ffff;",
            "tInT=1,79.842102,ffff;",
            "vignette=1,35,1.4,0,00000000;",
            "VIGNETTE=1,35,1.4,0,00000000;",
            "Sepia=1;",
        ],
    )
    def test_a_rossz_irasmod_nem_fut_le(self, lanc):
        assert not _lefut(lanc), f"a(z) {lanc!r} lefutott, pedig nem kellett volna"


class TestKanonikusFut:
    @pytest.mark.parametrize(
        "lanc",
        [
            "tint=1,79.842102,ffff;",
            "Vignette=1,35,1.4,0,00000000;",
            "sepia=1;",
        ],
    )
    def test_a_kanonikus_alak_lefut(self, lanc):
        assert _lefut(lanc), f"a(z) {lanc!r} NEM futott le, pedig kanonikus"


class TestLancVagas:
    def test_a_rossz_irasmod_elvagja_a_lancot(self):
        """#1140 + #1141: a hibás tag mögötti tagok sem futnak."""
        assert not _lefut("Sepia=1;bw=1;"), (
            "a rossz írásmódú tag után a `bw` lefutott"
        )

    def test_a_jo_elotag_lefut(self):
        assert _lefut("bw=1;Sepia=1;"), "az ép előtag nem futott le"


class TestMatches:
    def test_a_matches_pontosan_illeszt(self):
        assert FilterOp("tint", ()).matches("tint")
        assert not FilterOp("Tint", ()).matches("tint")
        assert not FilterOp("TINT", ()).matches("tint")

    def test_az_ini_megorzi_az_irasmodot(self, tmp_path):
        """⚠️ Round-trip: a lánc-vágás a RENDERELŐ útja — a `.picasa.ini`
        tartalmát nem érintheti. A rossz írásmódú tag nem fut le, de a
        fájlban bájtra ugyanaz marad."""
        from picasapy.ini import load_document, save_document

        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nfilters=Sepia=1;bw=1;\n", encoding="utf-8")

        dok = load_document(ini)
        save_document(dok, ini)

        assert "filters=Sepia=1;bw=1;" in ini.read_text(encoding="utf-8")

    def test_az_ismeretlen_nev_nem_vagja_el_a_lancot(self):
        """Az IDEGEN (regiszteren kívüli) nevet változatlanul beengedjük —
        azt a renderelő hagyja ki, a lánc többi tagja fut. Csak a
        FELISMERT név rossz írásmódja vág (#1140/#1141 együtt)."""
        ops = parse_filters_prefix("jovobeli_szuro=1;bw=1;")
        assert [op.name for op in ops] == ["jovobeli_szuro", "bw"]

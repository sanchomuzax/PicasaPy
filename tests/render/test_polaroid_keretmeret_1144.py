"""#1144: a Polaroid effekt kimenete 29%-kal nagyobb volt a kelleténél —
konstans `+235`/`+251` képpont, mindhárom mért méretben.

**Az őr egysége: KÉPPONT (pixel), pontos egyezés** (nem arány, nem
tűréshatáros összevetés). A bemenet mérete a `PicasaPy meroszett`
referenciakészlet fényképe, `960×960` szélesség×magasság helyett — FIGYELEM,
a Picasa-konvenció szerint a `(H, W)` sorrend a `numpy.ndarray.shape`, a
lenti nevek ezért `KEP_SZELESSEG`/`KEP_MAGASSAG` explicit párban szerepelnek.

Két forrás:
- a `TestValodiMeres` osztály a **valódi Windows Picasa 3.9-exporttal**
  (`/mnt/nas/My Pictures/PicasaPy meroszett/export-202608151229/`,
  bemenet: `polaroid__alap.jpg` mappa-testvére, `960×640`) mért, PIXELRE
  PONTOS méretet várja el — ez az #1144 jegy bizonyítéka.
- a `TestMasikKeparany` osztály NEM független Picasa-mérés — a jegyben
  levezetett képlet (négyzetes középvágás 6,45/9,68/25,8%-os
  kerettel + `margin = blur_px(8) + distance_px(3)` árnyék-margó + `floor`-
  kerekítésű forgatás) KONZISZTENCIÁJÁT ellenőrzi egy MÁSIK (álló) kép-
  arányon, hogy a javítás ne csak a mért fekvő mintán működjön (ld. #1045
  tanulsága: egyetlen képarányból ne vonjunk le szabályt). Ha ez a
  levezetés téves, csak azt jelzi, hogy a kód nem az itt leírt képletet
  követi — NEM helyettesíti a valódi Picasa-referenciát.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_frames as f


def _kep(szelesseg: int, magassag: int, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(20, 235, size=(magassag, szelesseg, 3), dtype=np.uint8)


class TestValodiMeres:
    """Bemenet: `960×640` (Szél×Mag), a `PicasaPy meroszett` referenciafotója.

    Elvárt kimenet — Windows Picasa 3.9, `export-202608151229`:
    `polaroid__alap` (Rotate=5, alapérték) → **818×950** (Szél×Mag);
    `polaroid__min`/`polaroid__max` (Rotate=-10/10, csúszka-szélek,
    a kettő egyezik) → **887×1004** (Szél×Mag).
    """

    KEP_SZELESSEG = 960
    KEP_MAGASSAG = 640

    def test_alap_rotate_5_pontos_meret(self) -> None:
        kep = _kep(self.KEP_SZELESSEG, self.KEP_MAGASSAG)
        eredmeny = f.apply_polaroid(kep, rotate=5.0)
        magassag, szelesseg = eredmeny.shape[:2]
        assert (szelesseg, magassag) == (818, 950), (
            f"a mai kód {szelesseg}×{magassag}-ot ad, a valódi Picasa 818×950-et "
            "(a #1144 régi hibája: 1053×1185, azaz +235/+235 többlet)"
        )

    @pytest.mark.parametrize("rotate", [-10.0, 10.0])
    def test_min_max_rotate_10_pontos_meret(self, rotate: float) -> None:
        kep = _kep(self.KEP_SZELESSEG, self.KEP_MAGASSAG)
        eredmeny = f.apply_polaroid(kep, rotate=rotate)
        magassag, szelesseg = eredmeny.shape[:2]
        assert (szelesseg, magassag) == (887, 1004), (
            f"a mai kód {szelesseg}×{magassag}-ot ad, a valódi Picasa 887×1004-et "
            "(a #1144 régi hibája: 1138×1255, azaz +251/+251 többlet)"
        )

    def test_min_es_max_azonos_meretet_ad(self) -> None:
        """A jegy táblázata szerint a `min` és a `max` az EREDETIBEN is és
        nálunk is azonos méretet ad — a `Rotate` előjele csak a forgatás
        irányát, nem a befoglaló méretét változtatja."""
        kep = _kep(self.KEP_SZELESSEG, self.KEP_MAGASSAG)
        min_eredmeny = f.apply_polaroid(kep, rotate=-10.0)
        max_eredmeny = f.apply_polaroid(kep, rotate=10.0)
        assert min_eredmeny.shape == max_eredmeny.shape


class TestMasikKeparany:
    """Álló bemenet (`500×800`, Szél×Mag) — MÁSIK képarány, mint a mért
    fekvő minta. Nem golden-referencia: a jegyben levezetett képlet saját
    konzisztenciáját ellenőrzi (ld. modul-docstring)."""

    KEP_SZELESSEG = 500
    KEP_MAGASSAG = 800

    @pytest.mark.parametrize(
        "rotate, vart_szelesseg, vart_magassag",
        [(5.0, 644, 747), (0.0, 586, 699)],
    )
    def test_allo_kep_szamolt_merete(self, rotate, vart_szelesseg, vart_magassag) -> None:
        kep = _kep(self.KEP_SZELESSEG, self.KEP_MAGASSAG)
        eredmeny = f.apply_polaroid(kep, rotate=rotate)
        magassag, szelesseg = eredmeny.shape[:2]
        assert (szelesseg, magassag) == (vart_szelesseg, vart_magassag)

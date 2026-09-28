"""#2159 → #3827: a Glow blur-átváltója (`0x00bb89b0`) és a belőle
következő lekicsinyítés.

A `filterdesc.xml` `xblur`-je (`Blur · 0,02 · max(W,H) / 4`) átmegy a natív
blur-átváltón, és a ragyogás a `csonk(f·W) × csonk(f·H)` pufferben készül. A
#2159 ebből egy teljes felbontású „levezetett sugarat" (`vignette_radius`)
számolt a régi erf-modellhez; a #3827 óta a natív lánc maga kicsinyít
(`belso_ragyogas.inner_glow`), a sugár-közelítés és az illesztett `/8`-as
konstans megszűnt.

Az őr az átváltó három mért pontját méri a spec táblájához
(`docs/specs/filterdesc-registry.md`, „A levezetett sugár").
"""

from __future__ import annotations

import pytest

from picasapy.render.belso_ragyogas import blur_atvalto

#: A referenciakép mérete — a spec táblája ezen a képen készült.
SZELESSEG, MAGASSAG = 2560, 1702


class TestABlurAtvalto:
    """A `0x00bb89b0` kiolvasott, zárt alakja."""

    def test_a_kis_blur_az_EGYETLEN_azonossag(self):
        """`p < 33,33` alatt az `X > 3` ág fut, és `k = 1`."""
        assert blur_atvalto(20.0, float(SZELESSEG)) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        "xblur,vart",
        [(448.0, 0.56920), (640.0, 0.39844), (128.0, 0.26042)],
    )
    def test_a_MERT_ertekek(self, xblur, vart):
        """A spec táblájának három független pontja."""
        assert blur_atvalto(xblur, float(SZELESSEG)) == pytest.approx(
            vart, abs=5e-5
        )

    def test_az_X_AG_hatara_a_kepszelessegbol_szamolhato(self):
        """Mikor lesz `p·f` PONTOSAN 255 — és mikor nem.

        A felső ág (`f = k = 255/p`) feltétele `X > 3`, azaz
        `d·(1 − 255/p) > 665` — a 2560 képpont széles referenciaképen ez
        `p > 344,5`. A `Vignette` mindkét mért állása (448 és 640) ide esik,
        tehát ott a lekicsinyített blur 255, amit a maszképítő 253-ra vág.

        ⚠️ A `p = 256` és a `p = 300` NEM ilyen: ott még az `X/3`-as ág fut
        (36,7 és 161,3). A „255 fölött mindig 255" első megfogalmazásom
        téves volt — a mérés javította, és a határ számolható."""
        for xblur in (448.0, 640.0, 1000.0):
            assert xblur * blur_atvalto(xblur, float(SZELESSEG)) == pytest.approx(
                255.0
            ), f"{xblur}: a felső ágon a lekicsinyített blur 255"
        for xblur in (256.0, 300.0, 344.0):
            assert xblur * blur_atvalto(xblur, float(SZELESSEG)) < 255.0, (
                f"{xblur}: a határ alatt még az X/3-as ág fut"
            )

    def test_a_255_HATARON_az_X_ag_fut(self):
        """A határeset kimondva, hogy ne tűnjön elírásnak."""
        assert blur_atvalto(255.0, float(SZELESSEG)) == pytest.approx(
            0.13072, abs=5e-5
        )

    def test_a_nulla_nem_oszt_nullaval(self):
        """A natív kód a 0-t `1e-05`-re cseréli — nálunk sem hibázhat."""
        assert blur_atvalto(0.0, float(SZELESSEG)) > 0.0


class TestAMuzeumiMattALeiroKepletevel:
    """#3827: a Múzeumi matt a leíró `/4`-es képletét adja a natív láncnak,
    az illesztett `/8`-as `VIGNETTE_RADIUS_FACTOR` (#317) nélkül."""

    def test_a_konstans_megszunt(self):
        import picasapy.render.glimmer_tone as tone

        assert not hasattr(tone, "VIGNETTE_RADIUS_FACTOR")
        assert not hasattr(tone, "vignette_radius")

    def test_a_matt_a_leiro_kepletet_hasznalja(self):
        from pathlib import Path

        import picasapy.render.glimmer_frames as frames

        forras = Path(frames.__file__).read_text(encoding="utf-8")
        assert "VIGNETTE_RADIUS_FACTOR" not in forras
        assert "xblur = 2.0 * 0.02 * max(height, width) / 4.0" in forras

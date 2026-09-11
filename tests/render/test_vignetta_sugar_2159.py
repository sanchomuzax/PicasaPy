"""#2159: a vignetta-sugár LEVEZETETT, nem illesztett.

A `filterdesc.xml` `xblur`-je (`Blur · 0,02 · max(W,H) / 4`) átmegy a natív
blur-átváltón (`0x00bb89b0`), a maszképítő a **lekicsinyített** térben
`[1, 253]`-ra vág, és menetenkénti dobozsugarat számol — teljes felbontásba
visszaváltva ez adja a sugarat. A korábbi `/8`-as konstans ugyanennek az
illesztett alakja volt.

Az őr a LEVEZETÉS három pontját méri a spec táblájához
(`docs/specs/filterdesc-registry.md`, „A levezetett sugár"), mert ott a
számok független Blur-állásokból jöttek — nem egy illesztésből.

⚠️ Amit ez az őr NEM mér: a látványt. A ΔE-számok a
`referencia/vignette/` nyolc valódi exportján állnak (privát repó, a CI nem
látja őket); a hozzá tartozó mérő az `eszkozok/export_keszletek_meres.py`
mintája szerint helyben fut.
"""

from __future__ import annotations

import math

import pytest

from picasapy.render.glimmer_tone import (
    VIGNETTE_RADIUS_FACTOR,
    blur_atvalto,
    vignette_radius,
)

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


class TestALevezetettSugar:
    @pytest.mark.parametrize(
        "blur,vart",
        [(10.0, 65.3), (35.0, 221.4), (50.0, 316.2)],
    )
    def test_a_spec_tablajat_adja(self, blur, vart):
        """A három pont a specben FÜGGETLEN Blur-állásokból jött."""
        assert vignette_radius(blur, SZELESSEG, MAGASSAG) == pytest.approx(
            vart, abs=0.1
        )

    @pytest.mark.parametrize(
        "blur,illesztett,levezetett",
        [(10.0, 64.0, 65.28), (35.0, 224.0, 221.365), (50.0, 320.0, 316.235)],
    )
    def test_az_illesztett_konstanshoz_2_szazalekon_belul(
        self, blur, illesztett, levezetett
    ):
        """A régi `/8` nem tévedés volt, hanem ugyanennek a közelítése —
        ezért nem mozdul el a látvány észrevehetően.

        A két érték MÉRT eltérése: `Blur 10` **+2,00 %**, `Blur 35`
        **−1,18 %**, `Blur 50` **−1,18 %**. A kis Blur-nál a legnagyobb,
        mert ott a `f = 1` ág fut, és a `⌈(p−1)/2⌉` kerekítés fölfelé
        billen."""
        assert vignette_radius(blur, SZELESSEG, MAGASSAG) == pytest.approx(
            levezetett, abs=0.005
        )
        assert blur * VIGNETTE_RADIUS_FACTOR * max(SZELESSEG, MAGASSAG) == (
            pytest.approx(illesztett)
        )
        assert abs(levezetett - illesztett) / illesztett <= 0.021

    def test_a_nulla_blur_nulla_sugarat_ad(self):
        """A `size min` export bájtra az érintetlen kép — a sugár ott 0."""
        assert vignette_radius(0.0, SZELESSEG, MAGASSAG) == 0.0

    def test_a_sugar_MONOTON_a_blurban(self):
        """A `Blur=35` és a `Blur=50` export ΔE 10,2-vel különbözik, tehát a
        sugárnak nőnie kell — a korábbi kör „minden Blur > 13,2 azonos"
        változata épp ezen bukott meg."""
        ertekek = [vignette_radius(b, SZELESSEG, MAGASSAG) for b in (10, 20, 35, 50)]
        assert ertekek == sorted(ertekek)
        assert ertekek[-1] > ertekek[0] * 4

    def test_a_kepmerettel_aranyos(self):
        """Kisebb képen kisebb a sugár — a hatás a kép arányában marad."""
        kicsi = vignette_radius(35.0, 640, 426)
        nagy = vignette_radius(35.0, SZELESSEG, MAGASSAG)
        assert kicsi < nagy

    def test_a_dobozsugar_EGESZ(self):
        """A maszképítő egész menetenkénti sugárral dolgozik: a `rp` egész,
        a teljes felbontású érték ennek az `f`-fel visszaváltott alakja."""
        for blur in (10.0, 35.0, 50.0):
            xblur = blur * (0.02 / 4.0) * max(SZELESSEG, MAGASSAG)
            f = blur_atvalto(xblur, float(SZELESSEG))
            rp = vignette_radius(blur, SZELESSEG, MAGASSAG) * f
            assert rp == pytest.approx(round(rp), abs=1e-6)
            assert rp == math.ceil((min(xblur * f, 253.0) - 1.0) / 2.0)


class TestAMuzeumiMattErintetlen:
    """A `VIGNETTE_RADIUS_FACTOR` MEGMARAD: a Múzeumi matt ragyogása a saját,
    független mérésén nyugszik (`referencia/museummatte/`, 3,67 → 2,07), azt
    ez a jegy nem érinti."""

    def test_a_konstans_megvan(self):
        assert VIGNETTE_RADIUS_FACTOR == pytest.approx(0.02 / 8.0)

    def test_a_matt_ezt_hasznalja(self):
        from pathlib import Path

        import picasapy.render.glimmer_frames as frames

        forras = Path(frames.__file__).read_text(encoding="utf-8")
        assert "VIGNETTE_RADIUS_FACTOR" in forras
        assert "vignette_radius" not in forras

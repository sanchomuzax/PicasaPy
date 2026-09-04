"""#2270 — a „Régi effektek" fül feliratai és a szövegtár.

A #2240 mérése szerint a `render/legacy_effects.py` katalógusából 11
felirat tér el az eredeti szövegtártól (`filter_*_label0`). A jegy két
csoportra bontotta őket, és a másodikra DÖNTÉST kért.

## (a) Öt sima eltérés — igazítva

`blur`, `dir_sharp`, `gamma`, `shadow`, `whitept`. Ezeknél az eredeti
felirat átvétele nem okoz ütközést: mindegyik egyedi marad a fülön.

## (b) Hat tétel, ami átvétel után MEGKÜLÖNBÖZTETHETETLEN lenne — marad

`autobacklight`/`fill` (mindkettő „Fill Light"), `triple`/`triple2`/
`triple3` (mindhárom „Lighting Fixes"), `focalpixelate`.

**A döntés indoka mérésen áll (#2148):** az eredetiben ezek a szűrők
**nem szerepelnek egy listában sem** — a 21 örökölt szűrőből mindössze
három érhető el a felületről (`radtint` a 12. csempén Shifttel,
`autobacklight` az Alapvető javítások gombján, `rainbow` a Kiegyenesítés
gombján ALT-tal), és azok is KÜLÖN helyeken. Az eredetinek tehát sosem
kellett megkülönböztetnie őket egymástól.

A mi 7. fülünk viszont **saját szerkezet** (#571): ott mind a húsz egymás
alatt áll. A toldat a MI igényünk, nem az eredeti hiánya — ezért marad.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.render.legacy_effects import LEGACY_EFFECTS

_SZOVEGTAR = (
    Path.home() / "picasapy-agent" / "referencia" / "stringres-en-hu.tsv"
)

#: (kulcs, az eredeti szövegtár szerinti angol felirat) — az (a) csoport.
IGAZITOTT = [
    ("blur", "Blur"),
    ("dir_sharp", "Directional Sharpen"),
    ("gamma", "Gamma Correct"),
    ("shadow", "Shadow & Highlight"),
    ("whitept", "Whitepoint"),
]

#: A (b) csoport: átvétel után ütköznének a fülön.
MEGTARTOTT_TOLDAT = [
    "autobacklight",
    "fill",
    "triple",
    "triple2",
    "triple3",
    "focalpixelate",
]


def _felirat(kulcs: str) -> str:
    for e in LEGACY_EFFECTS:
        if e.key == kulcs:
            return e.label
    raise AssertionError(f"nincs ilyen örökölt effekt: {kulcs}")


class TestAzOtSimaElteresIgazitva:
    @pytest.mark.parametrize("kulcs,vart", IGAZITOTT)
    def test_a_felirat_a_szovegtarat_koveti(self, kulcs, vart):
        assert _felirat(kulcs) == vart


class TestAToldatosakEGYEDIEK_maradnak:
    """A döntés lényege: a fülön minden sor megkülönböztethető legyen."""

    def test_a_ful_MINDEN_felirata_egyedi(self):
        feliratok = [e.label for e in LEGACY_EFFECTS]
        ismetlodo = {f for f in feliratok if feliratok.count(f) > 1}
        assert not ismetlodo, (
            f"a fülön azonos feliratú sorok lennének: {sorted(ismetlodo)} — "
            "a felhasználó nem tudná megmondani, melyikre kattint"
        )

    @pytest.mark.parametrize("kulcs", MEGTARTOTT_TOLDAT)
    def test_a_toldat_megmarad(self, kulcs):
        """Ha valaki »javítaná« őket a szövegtárra, a fenti egyediség-próba
        is elbukna — ez a próba megmondja, MELYIKET ne bántsa."""
        felirat = _felirat(kulcs)
        assert "(" in felirat or felirat not in (
            "Fill Light",
            "Lighting Fixes",
            "Focal Pixelate",
        ), f"{kulcs}: elveszett a megkülönböztető toldat"


@pytest.mark.skipif(
    not _SZOVEGTAR.exists(), reason="a szövegtár a privát repóban él"
)
class TestAzIgazitottakTENYLEG_a_szovegtarbol_valok:
    """⚠️ Ne a jegyből másoljuk — a forrásból olvassuk vissza."""

    @pytest.mark.parametrize("kulcs,vart", IGAZITOTT)
    def test_a_szovegtar_ezt_a_feliratot_adja(self, kulcs, vart):
        sorok = _SZOVEGTAR.read_text(encoding="utf-8").splitlines()
        elotag = f"filter_{kulcs}_label0\t"
        talalat = next((s for s in sorok if s.startswith(elotag)), None)
        assert talalat, f"a szövegtárban nincs {elotag!r} sor"
        angol = talalat.split("\t")[1].replace("&amp;", "&")
        assert angol == vart, f"{kulcs}: a szövegtár {angol!r}-t ad"

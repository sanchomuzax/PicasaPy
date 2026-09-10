"""#2800 — a Színinvertálás csempéje kék jelvényt kap (az ELŐLÉPTETÉS).

Az eredeti leíró-elemző a `</filter>` lezárásakor **előlépteti** az `effect`
módú szűrőt `oneclick`-re, ha öt mező mindegyike nulla
(`0x00900183`–`0x009001a9`) — vagyis ha a szűrő törzse **egyetlen
felhasználói vezérlőt sem hagyott hátra**. A szállított `filterdesc.xml` 84
szűrőjéből pontosan egy esik e szabály alá: az **`Invert`**, és a
tulajdonos felvételén a jelvény ott is VAN (13 × 12 képpont).

⚠️ A mi oldali megfelelés levezetett (a bináris öt mezőjének nincs egyenként
kimért neve), ezért a DARABSZÁM a kontroll: pontosan egy előléptetés, és az
`invert`. A `cinemascope` a legszűkebb határeset — annak `full_res` és
`resizes` jelzője áll, tehát NEM léphet elő.
"""

from __future__ import annotations

from picasapy.render.registry import (
    FILTER_REGISTRY,
    _elolepteteshez_ures,  # noqa: PLC2701 — az őr a szabályt magát méri
    one_click_keys,
)


class TestAKulcslista:
    def test_tizenharom_kulcs(self):
        assert len(one_click_keys()) == 13

    def test_az_invert_BENNE_van(self):
        assert "invert" in one_click_keys()

    def test_a_tizenkettő_korabbi_MEGMARADT(self):
        """Regresszió: az előléptetés nem vehet el jelvényt senkitől."""
        korabbi = {
            "autobacklight", "autocolor", "autocontrast", "autolight", "bw",
            "enhance", "grain", "grain2", "movieend", "moviestart", "sepia",
            "warm",
        }
        assert korabbi <= set(one_click_keys())


class TestAzEloleptetesSZUK:
    def test_PONTOSAN_egy_szuro_lep_elo(self):
        """Az eredetiben is pontosan egy — ez a mérés kontrollja."""
        eloleptetett = [
            kulcs
            for kulcs, spec in FILTER_REGISTRY.items()
            if spec.mode == "effect" and _elolepteteshez_ures(spec)
        ]
        assert eloleptetett == ["invert"]

    def test_a_cinemascope_NEM_lep_elo(self):
        """A legszűkebb határeset: csúszkája neki sincs, de méretez és teljes
        felbontást kér — ha a szabály csak a csúszkákat nézné, kettő lenne."""
        spec = FILTER_REGISTRY["cinemascope"]
        assert spec.mode == "effect"
        assert not spec.sliders, "a mérés megváltozott: már van csúszkája"
        assert _elolepteteshez_ures(spec) is False
        assert "cinemascope" not in one_click_keys()

    def test_csuszkas_effekt_sem_lep_elo(self):
        """Ismert negatív: a `lomo` effekt marad jelvény nélkül."""
        assert "lomo" not in one_click_keys()

    def test_a_szabaly_MINDEN_jelzore_hallgat(self):
        """Az »üres guard« ellen: ha a függvény bármelyik jelzőt elhagyná,
        ez bukik. A vizsgálat a valódi regiszter-bejegyzésekre épül."""
        import dataclasses

        alap = FILTER_REGISTRY["invert"]
        assert _elolepteteshez_ures(alap) is True
        for mezo in (
            "full_res", "slow", "resizes", "rotates", "persists_region",
            "has_puck",
        ):
            modositott = dataclasses.replace(alap, **{mezo: True})
            assert _elolepteteshez_ures(modositott) is False, mezo
        assert (
            _elolepteteshez_ures(dataclasses.replace(alap, color_kind="wheel_v1"))
            is False
        )

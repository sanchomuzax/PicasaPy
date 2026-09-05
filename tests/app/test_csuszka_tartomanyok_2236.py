"""#2236 — a felületi csúszkák a szűrő-regisztert kövessék.

A #2141 közben derült ki, hogy a katalógus (`app/effect_params.py`) és a
szűrő-regiszter (`render/registry_data.py`, a `filterdesc.xml`-ből)
tartományai eltérnek. A #2236 kutatói köre eldöntötte a kulcskérdést:
**nincs felületi leképezés** — a katalógus értéke változatlanul ér a
maghoz, tehát ahol eltér, ott a felhasználó más alapértéket és más
tartományt kap, mint az eredetiben.

⚠️ **Egy tételt kivettem a listából — mérve.** A `glow2` Radius csúszkája
**logaritmikus** (`log_base=250,0`, az egyetlen ilyen a katalógusban): a
regiszter [0…1] tartománya a LOG-skálán van, az alapértéke (3,0) pedig a
tényleges skálán — ezért is „nem fér bele" a saját maximumába. A két
oldal itt nem összehasonlítható, tehát nem hiba. A `chain_report.py`
ugyanezért hagyja ki a tartomány-ellenőrzésből.
"""

from __future__ import annotations

import pytest

from picasapy.app.effect_params import effect_params
from picasapy.render.registry import get_filter_spec


def _csuszka(kulcs: str, nev: str):
    for p in effect_params(kulcs):
        if p.key == nev:
            return p
    raise AssertionError(f"{kulcs}: nincs {nev!r} csúszka")


#: (szűrő, katalógus-kulcs, mező, elvárt érték) — mind a regiszterből.
JAVITANDO = [
    ("dir_tint", "shade", "default", 0.25),
    ("glow2", "intensity", "default", 0.65),
    ("radblur", "size", "minimum", -1.0),
    ("radblur", "amount", "minimum", -1.0),
    ("sat", "saturation", "minimum", -1.0),
    ("sat", "saturation", "default", 0.1618),
    ("tint", "preserve", "minimum", -1.0),
    ("tint", "preserve", "maximum", 255.0),
    ("unsharp", "amount", "maximum", 1.0),
]


class TestACsuszkakAregisztertKovetik:
    @pytest.mark.parametrize("kulcs,csuszka,mezo,vart", JAVITANDO)
    def test_a_mezo_a_regiszter_szerinti(self, kulcs, csuszka, mezo, vart):
        p = _csuszka(kulcs, csuszka)
        assert getattr(p, mezo) == pytest.approx(vart), (
            f"{kulcs}.{csuszka}.{mezo} = {getattr(p, mezo)}, a regiszter {vart}-t ad"
        )


class TestAsatNEGATIV_aga_elerheto:
    """Külön lelet a jegyből: a mag két külön ágra bomlik előjel szerint
    (#693), de a katalógus `min=0.0`-ja miatt a negatív ág felületről
    elérhetetlen volt — »a beállítás él, csak nem hat« (#1800 rokona)."""

    def test_a_telitettseg_negativ_erteket_is_felvehet(self):
        assert _csuszka("sat", "saturation").minimum < 0

    def test_a_negativ_ag_TENYLEG_mast_csinal(self):
        """Nem elég engedni: mérjük le, hogy a mag másképp viselkedik."""
        import numpy as np

        from picasapy.ini.filters import FilterOp
        from picasapy.render.chain import apply_filters

        rng = np.random.default_rng(3)
        kep = rng.integers(60, 200, size=(20, 25, 3), dtype=np.uint8)

        def elteres(ertek):
            r = apply_filters(kep, (FilterOp("sat", ("1", ertek)),))
            ki = np.asarray(r.image if hasattr(r, "image") else r)
            return int(np.abs(ki.astype(int) - kep.astype(int)).sum())

        assert elteres("-0.5") > 0, "a negatív telítettség nem változtat semmit"
        assert elteres("-0.5") != elteres("0.5"), (
            "a negatív és a pozitív ág ugyanazt adja — a #693 szerint két külön mag"
        )


class TestAmitSZANDEKOSAN_nem_igazitunk:
    """A négy képfüggő maximum és a log-skálás Radius NEM hiba."""

    @pytest.mark.parametrize(
        "kulcs,csuszka", [("border", "corner_radius"), ("focalzoom", "radius")]
    )
    def test_a_kepfuggo_maximum_veges_marad(self, kulcs, csuszka):
        """A `filterdesc` nem ad felső korlátot; mi képfüggő végeset adunk
        (#516). Végtelen maximumot nem lehet csúszkára tenni."""
        from picasapy.app.effect_params import resolve_effect_params

        p = next(
            x
            for x in resolve_effect_params(kulcs, width=1600, height=1200)
            if x.key == csuszka
        )
        assert p.maximum not in (None, float("inf"))
        assert p.maximum > 0

    def test_a_glow2_radius_LOG_skalas_marad(self):
        """A regiszter [0…1]-e a log-skálán van, az alapértéke (3,0) a
        tényleges skálán — ezért is nagyobb a saját maximumánál. A
        katalógus a TÉNYLEGES skálán dolgozik, tehát nem igazítjuk."""
        reg = next(
            cs for cs in get_filter_spec("glow2").sliders if cs.label == "Radius"
        )
        assert reg.log_base is not None, (
            "a glow2 Radius elvesztette a log_base-ét — akkor a #2236 "
            "kivétele újragondolandó"
        )
        assert reg.default > reg.maximum, (
            "a regiszter alapértéke már belefér a maximumába — a log-skála "
            "magyarázat megdőlt, nézd újra"
        )
        assert _csuszka("glow2", "radius").maximum == 100.0

"""#3229 1. lépés — MINDEN op deklarálja a saját forrás → kimenet leképezését.

## A mérce: a RENDERELT kimenet

A modul megjósolja, mekkora lesz egy op kimenete és hova kerül benne a forrás.
A próba ezt **nem képlethez hasonlítja**, hanem a valóban renderelt kimenethez:
minden bekötött szűrőt lefuttat egy próbaképen, és a `shape`-et veti össze a
megjósolt mérettel. Így egy jövőben bekötött, méretet változtató szűrő nem
csúszhat át némán — a teljességet a KÉSZLETRE állítjuk, nem felsorolásra
(a #3070 mintája).

## Amit NEM állít

Hogy egy szűrő KÉPPONTRA mit rajzol: a leképezés a kép HELYÉRŐL szól. A
keret-effektek képpont-szintű ellenőrzése a `test_keret_geometria_3166.py`
dolga (renderelt jelölővel).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import _FRAME_EFFECTS, _HANDLERS
from picasapy.render.chain_geometry import AZONOSSAG, keret_geometria
from picasapy.ini.filter_registry import CANONICAL_FILTER_NAMES
from picasapy.render.registry import FILTER_REGISTRY
from picasapy.render.op_geometry import (
    OpGeometria,
    SzingularisLekepezes,
    invertal,
    lanc_geometria,
    op_geometria,
)

SZELES, MAGAS = 120, 80

#: A hat név, amit ez az őr NEM tud egy általános, regiszterből épített
#: paraméter-listával megmérni (mérve 2026-09-16, a maradék 67 igen):
#:
#: * `Border`, `DropShadow`, `focalzoom`, `dir_tint` — a csúszka-INDEX nem
#:   paraméter-POZÍCIÓ: a `Border` 3. és 4. paramétere SZÍN (`000000`,
#:   `ffffff`), a csúszkák viszont 0–3 indexen állnak. Számot adva a szín
#:   helyére a bejegyzés hibára fut, és a lánc kihagyja;
#: * `finetune`, `finetune2` — az 5. mező nem csúszka, hanem AARRGGBB szín, és
#:   a csúszka-alapérték (`0`) érvénytelen színként elhasal.
#:
#: A keret-effektek geometriáját emiatt nem hagyjuk mérés nélkül: azt a
#: `test_keret_geometria_3166.py` méri renderelt jelölővel, hat szűrőre.
_ISMERT_KIHAGYAS = frozenset(
    {"border", "dropshadow", "focalzoom", "dir_tint", "finetune", "finetune2"}
)

#: Azok a nevek, amiket a lánc NEM a `_HANDLERS`-en át futtat (a `crop64` a
#: lánc végén, külön úton) — a teljesség-próba ezeket külön kéri.
KULON_UTON = ("crop64",)


@pytest.fixture
def minta() -> np.ndarray:
    rng = np.random.default_rng(3229)
    return rng.integers(0, 256, (MAGAS, SZELES, 3), dtype=np.uint8)


#: Kisbetűs kulcs → KANONIKUS lánc-név (a `CANONICAL_FILTER_NAMES`-ből).
_KANONIKUS = {n.casefold(): n for n in CANONICAL_FILTER_NAMES}

#: A két név, aminek a paramétere nem csúszka (nem a regiszterből jön).
_KEZI = {
    "crop64": "crop64=1,3c3c8c8c;",
    "tilt": "tilt=1,0.2,0.0;",
    "redeye": "redeye=1;",
    "retouch": "retouch=1;",
    # #3315: puck + négy csúszka + jelölőnégyzet — a regiszterből épített
    # lánc ezt nem adná ki (a puck x,y nincs a csúszkák közt)
    "picnikfocalpixelate": (
        "PicnikFocalPixelate=1,0.500000,0.500000,20.000000,10.000000,"
        "50.000000,0.000000,0;"
    ),
}


def _egy_op(nev: str) -> str:
    """Egy ÉRVÉNYES lánc-szöveg az adott névhez, a REGISZTERBŐL.

    ⚠️ Nem kitalált paraméter-lista: a szűrő csúszkáinak alapértékeit írjuk be,
    a regiszter sorrendjében. Egy találomra összeállított lista a fölös-paraméter
    kapun (#910) elhasalna, a lánc kihagyná a bejegyzést — és a próba VAKON
    zöld lenne (a mérés szerint 73-ból 62 név így csúszott át).
    """
    if nev in _KEZI:
        return _KEZI[nev]
    # #1141: a lánc-bejáró kis-nagybetű-ÉRZÉKENY (mérve hat exporton) — a
    # `_HANDLERS` kulcsai kisbetűsek, a láncba a KANONIKUS alak kell, különben
    # a bejegyzés ismeretlenként kimarad (és a próba vakon zöld lenne).
    kanonikus = _KANONIKUS.get(nev, nev)
    spec = FILTER_REGISTRY.get(nev)
    if spec is None or not spec.sliders:
        return f"{kanonikus}=1;"
    ertekek = ",".join(
        f"{(s.default if s.default is not None else s.minimum):.6f}"
        for s in sorted(spec.sliders, key=lambda s: s.index)
    )
    return f"{kanonikus}=1,{ertekek};"


class TestAzInverz:
    def test_az_egyseg_inverze_onmaga(self):
        assert invertal(AZONOSSAG) == AZONOSSAG

    def test_az_eltolas_inverze_visszavisz(self):
        m = ((1.0, 0.0, 17.0), (0.0, 1.0, -9.0))
        (a, b, c), (d, e, f) = invertal(m)
        assert (c, f) == (-17.0, 9.0)
        assert (a, b, d, e) == (1.0, 0.0, 0.0, 1.0)

    def test_a_szingularis_lekepezes_MEGALL(self):
        """Az eredeti is ellenőrzi a determinánst (`FUN_00a4a140`)."""
        with pytest.raises(SzingularisLekepezes):
            invertal(((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))

    def test_a_forgatas_inverze_visszahozza_a_pontot(self):
        geo = op_geometria(parse_filters("tilt=1,0.5,1.0;")[0], SZELES, MAGAS)
        (a, b, c), (d, e, f) = geo.matrix
        (ia, ib, ic), (id_, ie, if_) = geo.inverz
        x, y = 31.0, 17.0
        x2, y2 = a * x + b * y + c, d * x + e * y + f
        assert ia * x2 + ib * y2 + ic == pytest.approx(x, abs=1e-9)
        assert id_ * x2 + ie * y2 + if_ == pytest.approx(y, abs=1e-9)


class TestASzinmuveletekEgysegek:
    @pytest.mark.parametrize("nev", ["sepia", "bw", "warm", "sat", "contrast"])
    def test_nem_mozditja_a_kepet(self, nev):
        geo = op_geometria(parse_filters(f"{nev}=1;")[0], SZELES, MAGAS)
        assert geo.matrix == AZONOSSAG
        assert (geo.szelesseg, geo.magassag) == (SZELES, MAGAS)
        assert geo.valtoztat is False


class TestAMegjosoltMeretEGYEZIK:
    """A teljesség a KÉSZLETRE: minden bekötött szűrőt lefuttatunk."""

    def test_minden_bekotott_szuro_merete_egyezik(self, minta):
        from picasapy.render.chain import apply_filters

        eltero: list[str] = []
        mert: list[str] = []
        kihagyott: list[str] = []
        for nev in sorted(set(_HANDLERS) | set(KULON_UTON)):
            szoveg = _egy_op(nev)
            ops = parse_filters(szoveg)
            if not ops:
                continue
            jelentes = apply_filters(minta, ops)
            if jelentes.skipped:
                kihagyott.append(nev)
                continue  # ezt a paraméter-alakot a lánc kihagyta
            valodi = (jelentes.image.shape[1], jelentes.image.shape[0])
            try:
                jos = op_geometria(ops[0], SZELES, MAGAS)
            except Exception as hiba:  # noqa: BLE001 — a hibát is jelentjük
                eltero.append(f"{nev}: a jóslat hibázott ({hiba})")
                continue
            mert.append(nev)
            if (jos.szelesseg, jos.magassag) != valodi:
                eltero.append(
                    f"{nev}: jósolt {jos.szelesseg}×{jos.magassag}, "
                    f"renderelt {valodi[0]}×{valodi[1]}"
                )
        assert not eltero, "a megjósolt méret nem egyezik: " + " · ".join(eltero)
        # ⚠️ A zöld pipa nem elég: ki is mondjuk, MENNYIT mértünk. Az első
        # változatban 73 névből 62 kihagyva ment át (fölös-paraméter kapu),
        # tehát az őr majdnem vak volt.
        assert len(mert) >= 65, (
            f"csak {len(mert)} nevet mértünk a {len(_HANDLERS) + 1}-ből — a "
            f"kihagyottak: {', '.join(sorted(kihagyott))}"
        )
        # és a kihagyottak köre sem nőhet némán
        assert set(kihagyott) <= _ISMERT_KIHAGYAS, (
            "új név csúszott ki a mérésből: "
            + ", ".join(sorted(set(kihagyott) - _ISMERT_KIHAGYAS))
        )

    def test_a_keret_effektek_MIND_deklaralva_vannak(self):
        """Ami a méretet változtatja, arra nem maradhat egység-leképezés."""
        from picasapy.render.op_geometry import _OP_GEOMETRIA

        hianyzik = sorted(_FRAME_EFFECTS - set(_OP_GEOMETRIA))
        assert not hianyzik, (
            "keret-effekt deklarált leképezés nélkül: " + ", ".join(hianyzik)
        )


class TestALancEredetiSorrendben:
    def test_a_keret_nelkuli_lanc_egyseg(self):
        geo = lanc_geometria(parse_filters("sepia=1;bw=1;"), SZELES, MAGAS)
        assert geo.matrix == AZONOSSAG
        assert (geo.szelesseg, geo.magassag) == (SZELES, MAGAS)

    def test_a_keret_a_lanc_vegen_ugyanazt_adja_mint_a_3166(self):
        """Ahol nincs keret ELŐTT álló vágás, a két olvasat EGYEZIK.

        Ez a lépés viselkedés-változás nélküli: a #3166 `keret_geometria`-ja a
        mai (halasztott) sorrendet tükrözi, a `lanc_geometria` az eredetit — és
        egy `sepia;Border` láncon a kettő ugyanaz.
        """
        ops = parse_filters("sepia=1;Border=1,20,5,10,0;")
        uj = lanc_geometria(ops, SZELES, MAGAS)
        regi = keret_geometria(ops, SZELES, MAGAS)
        assert (uj.szelesseg, uj.magassag) == (regi.szelesseg, regi.magassag)
        assert uj.matrix == regi.matrix

    def test_a_vagas_es_a_keret_sorrendje_SZAMIT(self):
        """A jegy lényege: a `crop64;Border` MÁS, mint a `Border;crop64`.

        A mai `apply_filters` mindkettőt ugyanúgy futtatja (a vágást előre, a
        keretet a végére) — a mért, eredeti sorrendben viszont a kettő eltér.
        Ezt a leképezés is mutatja, tehát a 2. lépésnek van mit bekötnie.
        """
        elol = lanc_geometria(
            parse_filters("crop64=1,3c3c8c8c;Border=1,20,5,10,0;"), SZELES, MAGAS
        )
        hatul = lanc_geometria(
            parse_filters("Border=1,20,5,10,0;crop64=1,3c3c8c8c;"), SZELES, MAGAS
        )
        assert (elol.szelesseg, elol.magassag) != (hatul.szelesseg, hatul.magassag)


class TestAzApiAlakja:
    def test_az_OpGeometria_immutabilis(self):
        geo = OpGeometria(10, 20, AZONOSSAG)
        with pytest.raises(AttributeError):
            geo.szelesseg = 11  # type: ignore[misc]


class TestATartalomElhelyezesKesz:
    """A 2. lépés előfeltétele: a `content_placement` a `lanc_geometria`-ból is
    megvan — ugyanabban az alakban, mint ma a `keret_geometria`-ból.

    A mai `apply_filters` a keret-ág ELŐTTI méretből és a keret-opokból számolja
    a `content_placement`-et (#3166). A mért sorrendben viszont a keretek nem a
    lánc végén futnak, tehát a placement-nek a lánc EGÉSZ leképezéséből kell
    jönnie. Ez a próba kimondja, hogy ugyanaz az alak (`TartalomHely`) a
    `lanc_geometria` kimenetéből is előáll — a `tartalom_elhelyezes` a
    `szelesseg`/`magassag`/`matrix` hármast kéri, amit az `OpGeometria` is ad.
    """

    @pytest.mark.parametrize(
        "lanc",
        [
            "Border=1,20.000000,5.000000,0.000000,0.000000;",
            "Polaroid=1,5.000000;",
            "MuseumMatte=1,40.000000,1.200000,0.000000;",
            "Cinemascope=1;",
            "sepia=1;Border=1,20.000000,5.000000,0.000000,0.000000;",
        ],
    )
    def test_ugyanazt_adja_mint_a_3166_utja(self, lanc):
        from picasapy.render.chain_geometry import tartalom_elhelyezes

        ops = parse_filters(lanc)
        if not ops:
            pytest.skip(f"a lánc nem parszolt: {lanc}")
        uj = tartalom_elhelyezes(lanc_geometria(ops, SZELES, MAGAS), SZELES, MAGAS)
        regi = tartalom_elhelyezes(keret_geometria(ops, SZELES, MAGAS), SZELES, MAGAS)
        assert uj == regi, f"{lanc}: {uj} != {regi}"

    def test_a_keret_nelkuli_lanc_ERINTETLEN_helyet_ad(self):
        from picasapy.render.chain_geometry import tartalom_elhelyezes

        hely = tartalom_elhelyezes(
            lanc_geometria(parse_filters("sepia=1;bw=1;"), SZELES, MAGAS),
            SZELES,
            MAGAS,
        )
        assert hely.erintetlen is True

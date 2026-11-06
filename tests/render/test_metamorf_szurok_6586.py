"""#6586: regisztráció-vezérelt metamorf őr a renderelhető szűrőkre.

A relációs táblák a teszt regisztrációját adják; a renderelhető halmazt a
`can_render_filter`, a semleges állásokat pedig a `FILTER_REGISTRY` adja.
Az itt alkalmazott képi eltérések rövid, determinisztikus mérésből származnak,
az egyes képek pedig Hypothesis által generáltak.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.ini.filter_registry import CANONICAL_FILTER_NAMES
from picasapy.render.chain import apply_filters, can_render_filter
from picasapy.render.elonezeti_arany import elonezeti_arany
from picasapy.render.registry import FILTER_REGISTRY

_RENDERELHETOK = frozenset(
    nev for nev in CANONICAL_FILTER_NAMES if can_render_filter(nev)
)

# Az egypontos és a globális, de helyfüggetlen szűrők ugyanazt a pixelt
# ugyanazzal a leképezéssel írják át: a képpontok permutálása felcserélhető.
_PONTONKENTI = frozenset(
    {
        "autobacklight",
        "autolight",
        "autocolor",
        "bw",
        "warm",
        "sepia",
        "ansel",
        "tint",
        "sat",
        "colortemp",
        "shadow",
        "blur",
        "contrast",
        "gamma",
        "backlight",
        "Boost",
        "CrossProcess",
        "HeatMap",
        "Invert",
        "PicnikTint",
        "TwoTone",
    }
)

# Ezek térbeli műveletek, de a középpontjuk és a kernelük 180°-os forgatásra
# szimmetrikus. A numerikus eltérés határkezelésből és kerekítésből ered.
_KOZEP_SZIMMETRIKUS = frozenset(
    {
        "radblur",
        "radsat",
        "radtint",
        "glow",
        "glow2",
        "Comicize",
        "HDR",
        "IR",
        "LocalContrast",
        "Lomo",
        "Matte",
        "MuseumMatte",
        "Orton",
        "PencilSketch",
        "Pixelate",
        "QuantizePalette",
        "Vignette",
    }
)

# Az R/B csere érvényes, ha az effekt mindhárom csatornán ugyanazt a
# műveletet végzi, vagy a fix színe szürke. A dir_tint teszt szürke színt ad.
_CSATORNAFUGGETLEN = frozenset(
    {
        "unsharp",
        "unsharp2",
        "linblur",
        "dir_tint",
        "dir_brite",
        "dir_sharp",
        "radtint",
        "glow",
        "glow2",
        "shadow",
        "blur",
        "contrast",
        "gamma",
        "backlight",
        "autocontrast",
        "enhance",
        "fill",
        "Border",
        "DropShadow",
        "PicnikFocalPixelate",
        "FocalZoom",
        "PicnikGrain",
        "Invert",
        "LocalContrast",
        "Matte",
        "Pixelate",
        "Polaroid",
        "RoundedEdges",
        "Soften",
    }
)

# A teljes képből arányosan kicsinyített render és a preview arányban futó
# kisebb render összevetését ezeknél a méretfüggő kereteknél mérjük.
_ELONEZETI_SZUROK = frozenset({"Border", "MuseumMatte"})
_VIZSZINTES_TUKOR = frozenset({"rainbow", "Cinemascope"})
_ISMETELHETO_ZAJ = frozenset({"grain", "grain2"})

_NULLA_OP = {
    # Identity rect64, üres kijelölés vagy a FILTER_REGISTRY semleges állása.
    "crop64": "crop64=1,00000000ffffffff;",
    "redeye": "redeye=1;",
    "retouch": "retouch=1;",
    "triple": "triple=1,0,0,0;",
    "triple2": "triple2=1,0,0,1;",
    "triple3": "triple3=1,0,0,0;",
    "finetune": "finetune=1,0,0,0;",
    "finetune2": "finetune2=1,0,0,0;",
    "colorfix": "colorfix=1;",
    "tilt": "tilt=1,0,0;",
    "fill": "fill=1,0;",
    "whitept": "whitept=1;",
    "dir_sat": "dir_sat=1,0,0;",
    "Neon": "Neon=1,100;",
    "NightVision": "NightVision=1,0,0,100;",
    "Holga": "Holga=1,70,30,100;",
    "ReanimatedEyeColor": "ReanimatedEyeColor=1;",
    "Sixties": "Sixties=1,100,ffffff,0;",
}

_AKTIV_OP = {
    "tint": "tint=1,0.500000,ff8040;",
    "sat": "sat=1,0.500000;",
    "fill": "fill=1,0.500000;",
    "dir_tint": "dir_tint=1,0.500000,0.500000,0.250000,0.250000,808080;",
    "dir_brite": "dir_brite=1,0.200000,-0.150000;",
    "dir_sharp": "dir_sharp=1,0.200000,-0.150000;",
    "PicnikFocalPixelate": "PicnikFocalPixelate=1,0.5,0.5,20,50,50,0,0;",
}


@dataclass(frozen=True)
class _MonotonEset:
    szuro: str
    csuszka: str
    alacsony: str
    magas: str
    mertek: str


_MONOTON_ESETEK = {
    "triple_brightness": _MonotonEset(
        "triple", "Brightness", "triple=1,0.100000,0,0;", "triple=1,0.400000,0,0;", "mean"
    ),
    "triple_contrast": _MonotonEset(
        "triple", "Contrast", "triple=1,0,0.100000,0;", "triple=1,0,0.400000,0;", "std"
    ),
    "contrast": _MonotonEset(
        "contrast", "Contrast", "contrast=1,0.100000;", "contrast=1,0.400000;", "std"
    ),
    "sat": _MonotonEset("sat", "Amount", "sat=1,0.100000;", "sat=1,0.700000;", "chroma"),
}

# A frame és a helyfüggő szűrők nem kapnak forgatási relációt paramétercsere
# nélkül. A képaláírás-sávot, az eltolt árnyékot és a rögzített sávszíneket
# nem forgatjuk együtt a bemenettel.
_FORGATAS_KIZARAS = {
    "Border": "a képaláírás-sáv a keret alsó oldalához kötött",
    "Cinemascope": "a letterbox vágási pereme 180°-nál nem pixelpontos",
    "DropShadow": "az eltolt árnyék szöge és eltolása helyhez kötött",
    "Polaroid": "az alsó feliratsáv a kerethez kötött",
    "rainbow": "a színpaletta függőleges sávokra van rögzítve",
    "linblur": "az elmosó kernel irányított",
    "dir_tint": "a színátmenet hely- és puckfüggő",
    "dir_sat": "a telítettségi gradiens irányított",
    "dir_brite": "a fényerő-gradiens irányított",
    "dir_sharp": "az élességi gradiens irányított",
    "grain": "a véletlenszám-sorozat a képpontbejáráshoz kötött",
    "grain2": "a véletlenszám-sorozat a képpontbejáráshoz kötött",
}


def _regisztralt_relaciok() -> dict[str, frozenset[str]]:
    relaciok = {nev: set() for nev in _RENDERELHETOK}
    csoportok = {
        "permutation": _PONTONKENTI,
        "rotation180": _KOZEP_SZIMMETRIKUS,
        "channel_swap": _CSATORNAFUGGETLEN,
        "preview_scale": _ELONEZETI_SZUROK,
        "horizontal_mirror": _VIZSZINTES_TUKOR,
        "repeatability": _ISMETELHETO_ZAJ,
    }
    for relacio, nevek in csoportok.items():
        for nev in nevek:
            if nev in relaciok:
                relaciok[nev].add(relacio)

    # A ZeroState lefedettség mindig a termékregiszterből származik.
    for nev in _RENDERELHETOK:
        spec = FILTER_REGISTRY.get(nev.casefold())
        if spec is not None and spec.zero_state != "none":
            relaciok[nev].add("neutral")
    for nev in _NULLA_OP:
        if nev in relaciok:
            relaciok[nev].add("neutral")
    for nev in ("triple", "sat", "contrast"):
        if nev in relaciok:
            relaciok[nev].add("monotonicity")
    return {nev: frozenset(tipusok) for nev, tipusok in relaciok.items()}


FILTER_RELATIONS = _regisztralt_relaciok()


def _muvelet(nev: str, *, semleges: bool = False) -> str:
    if semleges:
        return _NULLA_OP[nev]
    return _AKTIV_OP.get(nev, f"{nev}=1;")


def _render(kep: np.ndarray, nev: str, *, semleges: bool = False) -> np.ndarray:
    lanc = parse_filters(_muvelet(nev, semleges=semleges))
    jelentes = apply_filters(kep, lanc)
    assert not jelentes.skipped, f"A regisztrált szűrő kimaradt: {nev}"
    return jelentes.image


def _minta_kep(alak: tuple[int, int, int], also: int = 0, felso: int = 255):
    generator = np.random.default_rng(6586)
    return generator.integers(also, felso + 1, size=alak, dtype=np.uint8)


def _hypothesis_kepeken(ellenorzes, alak=(48, 64, 3), also=0, felso=255):
    """Előbb helyi smoke-minta, majd Hypothesis az aktív suite-profillal.

    Nincs helyi `@settings` felülírás: ha a #6582 betölti a `ci` profilt a
    tesztkonfigurációban, a Hypothesis ezt az alapértelmezést örökli.
    """
    ellenorzes(_minta_kep(alak, also, felso))
    pytest.importorskip("hypothesis")
    from hypothesis import given, strategies as st
    from hypothesis.extra.numpy import arrays

    strategy = arrays(
        dtype=np.uint8,
        shape=alak,
        elements=st.integers(min_value=also, max_value=felso),
    )

    @given(strategy)
    def property_test(kep):
        ellenorzes(kep)

    property_test()


def test_minden_renderelheto_szurohoz_van_regisztralt_relacio():
    assert set(FILTER_RELATIONS) == set(_RENDERELHETOK)
    assert all(FILTER_RELATIONS.values()), "Üres relációjú szűrő maradt"
    assert set(_NULLA_OP) <= set(_RENDERELHETOK)
    assert set(_FORGATAS_KIZARAS) <= set(_RENDERELHETOK)

    nullas_regiszter = {
        nev
        for nev in _RENDERELHETOK
        if FILTER_REGISTRY[nev.casefold()].zero_state != "none"
    }
    assert nullas_regiszter <= set(_NULLA_OP)
    assert all(
        "rotation180" not in FILTER_RELATIONS[nev]
        and "permutation" not in FILTER_RELATIONS[nev]
        for nev in _FORGATAS_KIZARAS
    )


def test_a_semleges_allasok_valtozatlanul_hagyjak_a_kepet():
    def ellenoriz(kep):
        for nev in sorted(_NULLA_OP):
            assert np.array_equal(_render(kep, nev, semleges=True), kep), nev

    _hypothesis_kepeken(ellenoriz)


def test_a_pontonkénti_szurok_felcserelhetok_a_keppontok_permutalasaval():
    transzformaciok = (
        lambda kep: np.rot90(kep, 1).copy(),
        lambda kep: np.rot90(kep, 2).copy(),
        lambda kep: np.fliplr(kep).copy(),
        lambda kep: np.flipud(kep).copy(),
        lambda kep: kep.transpose(1, 0, 2).copy(),
    )

    def ellenoriz(kep):
        for nev in sorted(_PONTONKENTI):
            eredeti = _render(kep, nev)
            for transzform in transzformaciok:
                bal = _render(transzform(kep), nev)
                jobb = transzform(eredeti)
                assert np.array_equal(bal, jobb), nev

    _hypothesis_kepeken(ellenoriz)


def test_a_kozepesen_szimmetrikus_szurok_180_fokos_relacioja_tureses():
    def ellenoriz(kep):
        for nev in sorted(_KOZEP_SZIMMETRIKUS):
            eredeti = _render(kep, nev)
            elforgatott = _render(np.rot90(kep, 2).copy(), nev)
            kulonbseg = np.abs(
                elforgatott.astype(np.int16) - np.rot90(eredeti, 2).astype(np.int16)
            )
            # Öt véletlen próbaképen mért tartomány: MAE legfeljebb 3,2 és
            # 99. percentilis legfeljebb 25,8. A lazább küszöb kerekítést
            # enged, de a forgatási/aszimmetriahibát továbbra is elkapja.
            assert float(kulonbseg.mean()) <= 5.0, nev
            assert float(np.quantile(kulonbseg, 0.99)) <= 40.0, nev

    _hypothesis_kepeken(ellenoriz)


def test_a_csatornafuggetlen_szuroknel_az_r_es_b_csere_felcserelheto():
    def ellenoriz(kep):
        csere = kep[..., (2, 1, 0)].copy()
        for nev in sorted(_CSATORNAFUGGETLEN):
            eredeti = _render(kep, nev)
            csere_eredmeny = _render(csere, nev)
            assert np.array_equal(csere_eredmeny, eredeti[..., (2, 1, 0)]), nev

    _hypothesis_kepeken(ellenoriz)


def test_a_sorhoz_kotott_szurok_vizszintes_tukrozassal_felcserelhetok():
    def ellenoriz(kep):
        tukrozott = np.fliplr(kep).copy()
        for nev in sorted(_VIZSZINTES_TUKOR):
            eredeti = _render(kep, nev)
            masik = _render(tukrozott, nev)
            kulonbseg = np.abs(masik.astype(np.int16) - np.fliplr(eredeti).astype(np.int16))
            assert int(kulonbseg.max()) <= 1, nev

    _hypothesis_kepeken(ellenoriz)


def _mertek(kep: np.ndarray, nev: str) -> float:
    lebego = kep.astype(np.float64)
    if nev == "mean":
        return float(lebego.mean())
    if nev == "std":
        return float(lebego.std())
    if nev == "chroma":
        kromatikus = lebego - lebego.mean(axis=2, keepdims=True)
        return float(kromatikus.std())
    raise AssertionError(f"Ismeretlen monotonitás-mérték: {nev}")


def test_a_fenyero_kontraszt_es_telitetseg_monoton_csuszka():
    def ellenoriz(kep):
        for azonosito, eset in _MONOTON_ESETEK.items():
            nev = eset.szuro
            regiszter = FILTER_REGISTRY[nev]
            assert eset.csuszka.casefold() in {
                slider.label.casefold() for slider in regiszter.sliders
            }
            alacsony = apply_filters(kep, parse_filters(eset.alacsony))
            magas = apply_filters(kep, parse_filters(eset.magas))
            assert not alacsony.skipped and not magas.skipped, nev
            assert _mertek(magas.image, eset.mertek) >= _mertek(
                alacsony.image, eset.mertek
            ), azonosito

    _hypothesis_kepeken(ellenoriz, also=32, felso=224)


def test_az_elonezeti_render_egyezik_a_teljes_render_kicsinyitett_valtozataval():
    import cv2

    def ellenoriz(teljes):
        kicsi = cv2.resize(teljes, (64, 48), interpolation=cv2.INTER_AREA)
        for nev in sorted(_ELONEZETI_SZUROK):
            lanc = parse_filters(
                "Border=1,20,4,0,000000,ffffff,0;"
                if nev == "Border"
                else "MuseumMatte=1,24,40,1a0e03,f0eae4;"
            )
            teljes_kimenet = apply_filters(teljes, lanc).image
            with elonezeti_arany(0.5):
                elonezet = apply_filters(kicsi, lanc).image
            teljes_kicsinyitve = cv2.resize(
                teljes_kimenet,
                (elonezet.shape[1], elonezet.shape[0]),
                interpolation=cv2.INTER_AREA,
            )
            assert teljes_kicsinyitve.shape == elonezet.shape, nev
            elt = np.abs(
                teljes_kicsinyitve.astype(np.int16) - elonezet.astype(np.int16)
            )
            # Öt képen mért MAE: Border 0,024; MuseumMatte 0,79.
            assert float(elt.mean()) <= 1.5, nev
            assert float(np.quantile(elt, 0.99)) <= 30.0, nev

    _hypothesis_kepeken(ellenoriz, alak=(96, 128, 3), also=16, felso=240)


def test_a_seedelt_grain_azonos_bemenetre_azonos_zajt_ad():
    def ellenoriz(kep):
        for nev in sorted(_ISMETELHETO_ZAJ):
            elso = _render(kep, nev)
            masodik = _render(kep, nev)
            assert np.array_equal(elso, masodik), nev

    _hypothesis_kepeken(ellenoriz, also=32, felso=224)

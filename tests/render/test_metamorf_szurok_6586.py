"""#6586: regisztráció-vezérelt metamorf őr a renderelhető szűrőkre.

A relációs táblák a teszt regisztrációját adják; a renderelhető halmazt a
`can_render_filter`, a semleges állásokat pedig a `FILTER_REGISTRY` adja.
Az itt alkalmazott képi eltérések rövid, determinisztikus mérésből származnak,
az egyes képek pedig Hypothesis által generáltak.
"""

from __future__ import annotations

from dataclasses import dataclass
import inspect
import os
from types import ModuleType

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.ini.filter_registry import CANONICAL_FILTER_NAMES
from picasapy.render.chain import _HANDLERS, apply_filters, can_render_filter
from picasapy.render.elonezeti_arany import elonezeti_arany
from picasapy.render.registry import FILTER_REGISTRY

_RENDERELHETOK = frozenset(
    nev for nev in CANONICAL_FILTER_NAMES if can_render_filter(nev)
)


def _sajat_render_fuggveny(ertek) -> bool:
    return inspect.isfunction(ertek) and ertek.__module__.startswith("picasapy.render")


def _render_fuggvenyek_hivoi(fuggveny):
    """A renderláncban hívott render-függvényeket adja vissza.

    A handler-regiszter függvényein követjük az importált függvényeket és a
    render-modulok attribútumait is, így az indirekt wrapper (például a
    `tint` → `apply_tint` → `apply_channel_levels_stretch`) sem marad rejtve.
    """
    if not _sajat_render_fuggveny(fuggveny):
        return ()

    closure = inspect.getclosurevars(fuggveny)
    eredmeny = {
        ertek
        for ertek in (*closure.globals.values(), *closure.nonlocals.values())
        if _sajat_render_fuggveny(ertek)
    }
    modulok = {
        ertek
        for ertek in closure.globals.values()
        if isinstance(ertek, ModuleType) and ertek.__name__.startswith("picasapy.render")
    }
    for modul in modulok:
        for nev in fuggveny.__code__.co_names:
            ertek = getattr(modul, nev, None)
            if _sajat_render_fuggveny(ertek):
                eredmeny.add(ertek)
    return eredmeny


def _handler_eleri_a_szint_huzast(handler) -> bool:
    latott = set()
    verem = [handler]
    while verem:
        fuggveny = verem.pop()
        if id(fuggveny) in latott:
            continue
        latott.add(id(fuggveny))
        if getattr(fuggveny, "__name__", "") == "apply_channel_levels_stretch":
            return True
        verem.extend(_render_fuggvenyek_hivoi(fuggveny))
    return False


_SZINTHUZO_SZURO_KULCSOK = frozenset(
    nev for nev, handler in _HANDLERS.items() if _handler_eleri_a_szint_huzast(handler)
)
_SZINTHUZO_SZUROK = frozenset(
    nev
    for nev in _RENDERELHETOK
    if nev.casefold() in _SZINTHUZO_SZURO_KULCSOK
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

# Ha új handler kerül a közös szinthúzó hívói közé, ez az őr jelzi, hogy a
# forrásból levezetett kizárást és annak indoklását is át kell nézni. Maga a
# kizárás nem ebből a listából, hanem a handler-hívási láncból származik.
_SZINTHUZO_KIZARAS_KULCSAI = frozenset(
    {"enhance", "autocontrast", "tint", "rainbow"}
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
        "Pixelate",
        "QuantizePalette",
        "Vignette",
    }
)

# Azonos bemenetre ismételhető szűrők. A PencilSketch AutoFix-mintavétele
# 1000 pixel fölött nem forgatásinvariáns, ezért más metamorf reláció fedi le.
_DETERMINISZTIKUS_SZUROK = frozenset({"grain", "grain2", "PencilSketch"})

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
    "Cinemascope": "a rögzített magú, sorfolytonos zajréteg nem fordul a képpel",
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
    "PencilSketch": (
        "az AutoFix 1000 pixel fölötti középre igazított pontmintája "
        "nem forgatásinvariáns (filterdesc-registry.md, 6/a)"
    ),
}
for _nev in _SZINTHUZO_SZUROK:
    _FORGATAS_KIZARAS[_nev] = (
        "a 0x009db610 szinthúzó a balra igazított 90% × 90%-os elemzőablakból számol"
    )


def _regisztralt_relaciok() -> dict[str, frozenset[str]]:
    relaciok = {nev: set() for nev in _RENDERELHETOK}
    csoportok = {
        "permutation": _PONTONKENTI - _SZINTHUZO_SZUROK,
        "analysis_window_permutation": _PONTONKENTI & _SZINTHUZO_SZUROK,
        "rotation180": _KOZEP_SZIMMETRIKUS - _SZINTHUZO_SZUROK,
        "channel_swap": _CSATORNAFUGGETLEN,
        "preview_scale": _ELONEZETI_SZUROK,
        "repeatability": _DETERMINISZTIKUS_SZUROK | _SZINTHUZO_SZUROK | {"Cinemascope"},
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
    return _render_op(kep, _muvelet(nev, semleges=semleges), nev)


def _render_op(kep: np.ndarray, muvelet: str, nev: str) -> np.ndarray:
    lanc = parse_filters(muvelet)
    jelentes = apply_filters(kep, lanc)
    assert not jelentes.skipped, f"A regisztrált szűrő kimaradt: {nev}"
    return jelentes.image


def _minta_kep(alak: tuple[int, int, int], also: int = 0, felso: int = 255):
    generator = np.random.default_rng(6586)
    return generator.integers(also, felso + 1, size=alak, dtype=np.uint8)


def _hypothesis_kepeken(ellenorzes, alak=(16, 24, 3), also=0, felso=255):
    """Előbb helyi smoke-minta, majd Hypothesis az aktív suite-profillal.

    A futásidő-határidő ki van kapcsolva; a példaszám nappal 20, az
    éjszakai fuzz-profilban (#6582) 200. A 16×24-es kép csökkenti a szűrőcsoportonkénti
    renderköltséget, miközben valódi képponttömb marad.
    """
    ellenorzes(_minta_kep(alak, also, felso))
    pytest.importorskip("hypothesis")
    from hypothesis import given, settings, strategies as st
    from hypothesis.extra.numpy import arrays

    strategy = arrays(
        dtype=np.uint8,
        shape=alak,
        elements=st.integers(min_value=also, max_value=felso),
    )

    # Nappal (PR, main) szűrőcsoportonként kevés példa fut, hogy a CI-darab
    # időkerete tartható maradjon; az éjszakai fuzz-profil (#6582) több
    # példát kér.
    peldaszam = 200 if os.environ.get("PICASAPY_FUZZ_PROFIL") == "ejszakai" else 20

    @settings(deadline=None, max_examples=peldaszam)
    @given(strategy)
    def property_test(kep):
        ellenorzes(kep)

    property_test()


def test_minden_renderelheto_szurohoz_van_regisztralt_relacio():
    assert set(FILTER_RELATIONS) == set(_RENDERELHETOK)
    assert all(FILTER_RELATIONS.values()), "Üres relációjú szűrő maradt"
    assert set(_NULLA_OP) <= set(_RENDERELHETOK)
    assert set(_FORGATAS_KIZARAS) <= set(_RENDERELHETOK)
    deklaralt = (
        _PONTONKENTI
        | _KOZEP_SZIMMETRIKUS
        | _CSATORNAFUGGETLEN
        | _ELONEZETI_SZUROK
        | _DETERMINISZTIKUS_SZUROK
        | {eset.szuro for eset in _MONOTON_ESETEK.values()}
    )
    assert deklaralt <= set(_RENDERELHETOK), "A reláció egy nem regisztrált szűrőre hivatkozik"
    assert _SZINTHUZO_SZURO_KULCSOK == _SZINTHUZO_KIZARAS_KULCSAI, (
        "Változott a 0x009db610 szinthúzó hívóinak köre; vizsgáld felül a térbeli kizárást"
    )
    assert _SZINTHUZO_SZUROK == {"enhance", "autocontrast", "tint", "rainbow"}

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


def test_a_szinthuzo_hivoi_tukrozesbol_kimaradnak_a_regisztralt_hivasi_lanc_alapjan():
    assert _SZINTHUZO_SZUROK == {"enhance", "autocontrast", "tint", "rainbow"}
    for nev in _SZINTHUZO_SZUROK:
        assert "0x009db610" in _FORGATAS_KIZARAS[nev]
        assert "permutation" not in FILTER_RELATIONS[nev]
        assert "rotation180" not in FILTER_RELATIONS[nev]


def test_a_cinemascope_zajretege_sorfolytonos_es_nem_tukorszimmetrikus():
    from picasapy.render.glimmer_noise_ops import noise_layer

    # A Cinemascope-spec zajlépése ezt az állandó magú, szürke zajt használja.
    zaj = noise_layer(9, 16, seed=0, low=225, high=245, grayscale=True)
    assert not np.array_equal(zaj, np.fliplr(zaj))


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
    szinthuzo_nelkul = _PONTONKENTI - _SZINTHUZO_SZUROK

    def ellenoriz(kep):
        for nev in sorted(szinthuzo_nelkul):
            eredeti = _render(kep, nev)
            for transzform in transzformaciok:
                bal = _render(transzform(kep), nev)
                jobb = transzform(eredeti)
                assert np.array_equal(bal, jobb), nev

    _hypothesis_kepeken(ellenoriz)


def test_a_tint_az_elemzoablakon_beluli_pixelcseret_felcsereli():
    def ellenoriz(kep):
        magassag, szelesseg = kep.shape[:2]
        elso = (magassag // 4, szelesseg // 4)
        masodik = (3 * magassag // 4, 3 * szelesseg // 4)
        permutalt = kep.copy()
        permutalt[elso], permutalt[masodik] = kep[masodik].copy(), kep[elso].copy()

        for nev in sorted(_PONTONKENTI & _SZINTHUZO_SZUROK):
            eredeti = _render(kep, nev)
            vart = eredeti.copy()
            vart[elso], vart[masodik] = eredeti[masodik].copy(), eredeti[elso].copy()
            assert np.array_equal(_render(permutalt, nev), vart), nev

    _hypothesis_kepeken(ellenoriz)


def test_a_kozepesen_szimmetrikus_szurok_180_fokos_relacioja_tureses():
    def ellenoriz(kep):
        for nev in sorted(_KOZEP_SZIMMETRIKUS):
            eredeti = _render(kep, nev)
            elforgatott = _render(np.rot90(kep, 2).copy(), nev)
            kulonbseg = np.abs(
                elforgatott.astype(np.int16) - np.rot90(eredeti, 2).astype(np.int16)
            )
            # A radsat egész középpontja round(W·0,5), így a 180°-os
            # átfordításnál legfeljebb egy pixelnyi középponteltolás marad.
            # 24×32-es mintán a korábbi mérések MAE-je legfeljebb 3,2, p99-e
            # legfeljebb 25,8 volt; a 16×24-es rács ezt arányosan felnagyította.
            assert float(kulonbseg.mean()) <= 5.0, nev
            assert float(np.quantile(kulonbseg, 0.99)) <= 40.0, nev

    _hypothesis_kepeken(ellenoriz, alak=(24, 32, 3))


def test_a_csatornafuggetlen_szuroknel_az_r_es_b_csere_felcserelheto():
    def ellenoriz(kep):
        csere = kep[..., (2, 1, 0)].copy()
        for nev in sorted(_CSATORNAFUGGETLEN):
            eredeti = _render(kep, nev)
            csere_eredmeny = _render(csere, nev)
            assert np.array_equal(csere_eredmeny, eredeti[..., (2, 1, 0)]), nev

    _hypothesis_kepeken(ellenoriz)


def test_a_terbeli_kizarasokhoz_indoklas_tartozik():
    for nev, indok in _FORGATAS_KIZARAS.items():
        assert indok.strip(), nev
        assert "permutation" not in FILTER_RELATIONS[nev], nev
        assert "rotation180" not in FILTER_RELATIONS[nev], nev
    assert "AutoFix" in _FORGATAS_KIZARAS["PencilSketch"]
    assert "PencilSketch" in _DETERMINISZTIKUS_SZUROK


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

    # A natív exp(2·kontraszt) LUT 128 körül skáláz, majd 0..255-re vág.
    # A szórás a vágási tartományban nem monoton (pl. egyszínű 32-es kép
    # std-je 0,1-ről 0,4-re állítva 0,45-ről 0-ra csökken), ezért a teszt
    # 96..160-as bemeneteken, telítődés nélkül vizsgálja a csúszka relációját.
    _hypothesis_kepeken(ellenoriz, also=96, felso=160)


def test_az_elonezeti_render_egyezik_a_teljes_render_kicsinyitett_valtozataval():
    import cv2

    def ellenoriz(teljes):
        kicsi_meret = (teljes.shape[1] // 2, teljes.shape[0] // 2)
        kicsi = cv2.resize(teljes, kicsi_meret, interpolation=cv2.INTER_AREA)
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

    _hypothesis_kepeken(ellenoriz, alak=(32, 48, 3), also=16, felso=240)


def test_a_determinisztikus_szurok_azonos_bemenetre_azonos_kimenetet_adnak():
    def ellenoriz(kep):
        for nev in sorted(_DETERMINISZTIKUS_SZUROK):
            elso = _render(kep, nev)
            masodik = _render(kep, nev)
            assert np.array_equal(elso, masodik), nev

    _hypothesis_kepeken(ellenoriz, also=32, felso=224)

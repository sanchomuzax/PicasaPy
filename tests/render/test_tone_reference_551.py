"""A Finomhangolás pontonkénti modelljei a MÉRT görbékhez képest (#551).

Ez a készlet nem szintetikus horgonyértékeket ellenőriz, hanem a **valódi
Picasa 3.9 kimenetét**: a `tests/support/finetune_reference/` mért görbéi a
privát repó referencia-képpárjaiból készültek (ld. az ottani docstringet és
a `scripts/extract_finetune_reference.py`-t).

**Miért kell ez.** A projekt szabálya, hogy effekt-kalibrációnál a mérés az
igazságforrás — egy dekompilált, de rosszabbul illeszkedő képlet bevezetése
regresszió. A #551-nél ez élesben is előfordult: a Színhőmérséklet natív
`0x0090ea10` képlete 3–5-ször pontatlanabbnak mérődött a mai modellnél, és
emiatt NEM került be. Az ilyen csere eddig csak kézi méréssel bukott volna
ki; innentől a tesztkészlet fogja meg.

**Mit NEM fed le.** A Derítőfény nincs köztük: az nem pontonkénti művelet (a
natív mag a képpont világosságával súlyoz, #575), ezért egyetlen LUT nem
írja le — arra a `test_tone.py` natív-algoritmus tesztjei valók. A
szín-varázspálcánál a viszonyítási SZÍN kiválasztása sem fut újra (ahhoz a
forrásfotó kellene); a mentett becslésből viszont a teljes hatáslánc
(szín → csatorna-erősítés) ellenőrizhető.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.curves import lut_ramp
from picasapy.render.tone import (
    FINETUNE_LEVEL_PARAM_MAX,
    _apply_levels,
    apply_native_lut16,
    finetune_level_lut,
    apply_color_temperature,
    apply_highlights,
    apply_neutral_pipette,
    apply_shadows,
)
from tests.support.finetune_reference import MeasuredCase, measured_cases

#: Esetenkénti hibakorlát a mért görbéhez képest (átlagos abszolút
#: csatorna-eltérés a 0..255 skálán). Az értékek a MAI modellek mért
#: hibájából származnak, ~40 % ráhagyással — céljuk a regresszió elkapása,
#: nem a jövőbeli javítás megakadályozása. Ha egy modell javul, a korlát
#: lejjebb vihető; ha romlik, az a teszt dolga, hogy kiderüljön.
#:
#: A mért érték (2026-08-13) zárójelben. A Színhőmérséklet hideg vége a
#: leggyengébb (a modell konstans szorzó, a valóság a csúcsfényeknél vág);
#: a szín-varázspálcánál a hiba nagyobb részét a viszonyítási szín
#: BECSLÉSE adja, nem a csatorna-erősítés.
#:
#: **#879 (2026-08-18):** a Kiemelések/Árnyékok modellje a natív szinthúzó
#: LUT-ra (`0x0090c1e0` + `0x0090be70`) állt át, ezért a négy szintvágó eset
#: hibája újramérve. Három JAVULT (0,51→0,35 · 0,61→0,35 · 0,42→0,32), egy
#: kicsit ROMLOTT (0,64→0,87): a natív alkalmazó `>>8`-cal CSONKÍT, mi pedig
#: — a natívtól eltérően — nem ditherelünk, így félszintnyi lefelé torzítás
#: marad. Mind a négy hiba az adott eset JPEG-zajszintje alatt van, vagyis a
#: különbség nem mérhető ki élesben; cserébe a kompozit (két csúszkás) eset
#: hibája 217 szintről nullára esett.
HIBAKORLATOK: dict[str, float] = {
    "kiemelesek_mid": 1.2,  # 0,87
    "kiemelesek_max": 0.5,  # 0,35
    "arnyekok_mid": 0.5,  # 0,35
    "arnyekok_max": 0.45,  # 0,32
    # #951 KOMPOZIT — a két csúszka egyszerre. A #879 azt JÓSOLTA, hogy a
    # közös LUT-tal a hiba „217 szintről nullára esik"; ez most MÉRVE is
    # igaz: 0,74 és 0,55, mindkettő a saját zajszint közelében.
    "kompozit_mid": 1.1,  # 0,74 (zajszint 0,82)
    "kompozit_max": 0.9,  # 0,55 (zajszint 1,04)
    "szinho_0": 3.2,  # 2,26
    "szinho_10": 1.6,  # 1,12
    "szinho_25": 0.8,  # 0,48
    "szinho_75": 0.7,  # 0,38
    "szinho_90": 0.8,  # 0,54
    "szinho_100": 0.8,  # 0,54
    "szinpalca": 4.5,  # 3,40
}


def _model_luts(case: MeasuredCase) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A vizsgált modell három csatorna-LUT-ja az eset paraméterével.

    A LUT-okat a tényleges render-függvényekkel állítjuk elő (egy 256 szintű
    „létra"-képen), hogy a teszt a valódi kódutat mérje, ne egy külön,
    kézzel újraírt képletet.
    """
    ladder = np.arange(256, dtype=np.uint8).reshape(1, 256, 1).repeat(3, axis=2)
    if case.control == "highlights":
        rendered = apply_highlights(ladder, case.param)
    elif case.control == "shadows":
        rendered = apply_shadows(ladder, case.param)
    elif case.control == "temperature":
        rendered = apply_color_temperature(ladder, case.param)
    elif case.control == "highlights_shadows":
        # #951: a KOMPOZIT eset — a két csúszka EGYSZERRE. Szándékosan a
        # közös `_apply_levels`-en át megy: ez az egyetlen eset, ami
        # megkülönbözteti a KÖZÖS LUT-os modellt a két külön menetestől.
        rendered = _apply_levels(ladder, case.param, case.param)
    elif case.control == "color_wand":
        rendered = apply_neutral_pipette(ladder, case.neutral)
    else:  # pragma: no cover — új vezérlő esetén azonnal kiderüljön
        raise AssertionError(f"Ismeretlen vezérlő: {case.control!r}")
    return tuple(rendered[0, :, index].astype(np.float64) for index in range(3))  # type: ignore[return-value]


ESETEK = measured_cases()


def test_minden_eset_kapott_hibakorlatot() -> None:
    """Új mérési eset ne csússzon be némán, korlát nélkül."""
    assert {case.name for case in ESETEK} == set(HIBAKORLATOK)


@pytest.mark.parametrize("case", ESETEK, ids=lambda case: case.name)
def test_a_modell_illeszkedik_a_mert_gorbere(case: MeasuredCase) -> None:
    """A modell hibája a mért Picasa-kimenethez képest a korlát alatt van."""
    error = case.weighted_error(_model_luts(case))
    assert error <= HIBAKORLATOK[case.name], (
        f"{case.name}: a modell eltérése a mért Picasa-kimenettől {error:.2f} "
        f"(korlát {HIBAKORLATOK[case.name]}, a készlet zajszintje "
        f"{case.noise_floor:.2f})"
    )


@pytest.mark.parametrize("case", ESETEK, ids=lambda case: case.name)
def test_a_modell_erdemben_jobb_az_azonossagnal(case: MeasuredCase) -> None:
    """Kontroll: a mérés tényleg mozdít a képen.

    Ha az azonosság (a „ne csinálj semmit" modell) hasonlóan jó lenne, a
    fenti teszt semmit nem bizonyítana — ez zárja ki. A leggyengébb eset a
    szín-varázspálca (5,7 vs 3,4), mert az önmagában is finom hatás; a
    csúszkáknál az arány 10–130-szoros.
    """
    ramp = lut_ramp()
    identity_error = case.weighted_error((ramp, ramp, ramp))
    model_error = case.weighted_error(_model_luts(case))
    assert identity_error > 1.5 * model_error


def test_a_szintvago_csuszkak_parametere_a_mert_tartomanyban_van() -> None:
    """A mérőkészlet legerősebb állása épp a `filterdesc.xml` felső határa."""
    szintvagok = [case for case in ESETEK if case.control in ("highlights", "shadows")]
    assert szintvagok, "kellene lennie szintvágó esetnek a készletben"
    assert max(case.param for case in szintvagok) == pytest.approx(
        FINETUNE_LEVEL_PARAM_MAX
    )


# -- #951: a kompozit eset FOGA ---------------------------------------------
#
# Egy őr-teszt csak akkor ér valamit, ha a rossz modellt MEGBUKTATJA. A
# kompozit eset épp azért került be, mert ez az egyetlen, ami elkülöníti a
# KÖZÖS LUT-os megvalósítást a két külön menetestől (az utóbbi kétszer vág
# 8 bitre). Ha ez a teszt egyszer zöld lenne a szekvenciális modellel is,
# akkor a kompozit eset elvesztette az értelmét — és ezt tudni akarjuk.


def _szekvencialis_luts(case: MeasuredCase) -> tuple[np.ndarray, ...]:
    """A HIBÁS modell: két külön menet, mindkettő 8 bitre vág."""
    ladder = np.arange(256, dtype=np.uint8).reshape(1, 256, 1).repeat(3, axis=2)
    elso = apply_native_lut16(ladder, finetune_level_lut(case.param, 0.0))
    masodik = apply_native_lut16(elso, finetune_level_lut(0.0, case.param))
    return tuple(masodik[0, :, index].astype(np.float64) for index in range(3))


KOMPOZIT_ESETEK = [case for case in ESETEK if case.control == "highlights_shadows"]


def test_van_kompozit_eset() -> None:
    """A kompozit mérés nem tűnhet el némán a készletből (#951)."""
    assert KOMPOZIT_ESETEK, (
        "Nincs kompozit (két csúszkás) eset — pont az hiányzott 2026-08-23-ig, "
        "és pont az a hibaalak, amit a #879 javított."
    )


@pytest.mark.parametrize("case", KOMPOZIT_ESETEK, ids=lambda case: case.name)
def test_a_kompozit_eset_megbuktatja_a_szekvencialis_modellt(
    case: MeasuredCase,
) -> None:
    """A kettévágott (régi, hibás) modell NEM fér bele a korlátba.

    Ez a teszt „foga": ha egyszer átmenne, az azt jelentené, hogy a
    kompozit eset már nem különbözteti meg a két megvalósítást.
    """
    hibas = case.weighted_error(_szekvencialis_luts(case))
    assert hibas > HIBAKORLATOK[case.name] * 3, (
        f"{case.name}: a szekvenciális modell hibája {hibas:.2f}, ami NEM "
        f"lóg ki eléggé a {HIBAKORLATOK[case.name]} korlátból — a kompozit "
        f"eset elvesztette a megkülönböztető erejét."
    )

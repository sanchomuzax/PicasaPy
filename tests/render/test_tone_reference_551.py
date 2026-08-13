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
HIBAKORLATOK: dict[str, float] = {
    "kiemelesek_mid": 0.9,  # 0,64
    "kiemelesek_max": 0.8,  # 0,51
    "arnyekok_mid": 0.9,  # 0,61
    "arnyekok_max": 0.7,  # 0,42
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

"""#6691: a Fókuszált pixelesítés (`PicnikFocalPixelate`) az eredeti Picasa-exportokon.

A 9 mért eset (`docs/benchmarks/2026-11-08-6585-ujrabesorolas.md`, "PicnikFocalPixelate"
szakasz) 8-ban eltért az eredeti exportjától (SSIM 0,906-0,973, ΔE 1,24-3,17). Két ok:

1. **A kicsinyített méret kerekítése.** Az eredeti `ResizeImageOperation` a
   `W/Impact x H/Impact` célméretet `trunc(v + 0,5)`-tel egészíti (a `Pixelate`
   effektnél ez a #4912); nálunk csonkolás volt. Nem egész `W/Impact` esetén ez egy
   sorral vagy oszloppal kisebb rácsot adott, és a blokkhatárok az egész képen
   elcsúsztak.
2. **A Fade és a maszk keverése.** A `NestedImageOperation` (`BlendAlpha` + `Mask`)
   a natív egész képletekkel keveri a pixelezett képet: előbb `alpha_blend`
   (`0x009dc4b0`), utána `masked_blend` (`0x008f62a0`). Nálunk lebegőpontos
   lineáris keverés volt, ami a pixelezett részen átlagosan 1 szinttel világosabb.

A mérőteszt a feladatok eredeti Picasa-exportjából tárolt KIVÁGÁSOKRA épül (a
teljes, 1280 px-es képek nem férnek a tárba). Esetenként két kis, veszteségmentes
PNG van a `data/focal_pixelate_6691/` alatt
(`tools/golden/make_focal_pixelate_fixture_6691.py`): a forrás kivágása és a
Picasa-export ugyanazon ablaka. A forráskivágást a teljes kép helyére illesztjük egy
nulla vászonra, így a rács, a sugár és a maszk a valódi képmérettel számolódik; az
ablak értéke a vászon többi részétől független, mert a blokkértékek és a maszk
helyiek (a kivágás egy blokknyi margót tartalmaz).

A renderelt vásznat az export JPEG-beállításával (4:2:0, kvantálótáblák, az
`esetek.json`-ból) újrakódoljuk, mert a Picasa JPEG-je a blokkélek körül csilingel,
és a nyers ΔE ezt eltérésnek látná (#4940). Az ablak 16 px-hez igazított, ezért az
újrakódolás ott ugyanazt adja, mint a teljes képé.

⚠️ Amit ez a teszt NEM mér: a teljes képet (csak a 160 x 128-as ablakot), és a
fókuszpont körüli belső kört (az ablak a belső körön kívül van; a maszk 0 értékű
részét a `test_focal_pixelate_belso_kor_bitre_az_eredeti` szintetikus teszt őrzi).
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "tools" / "golden"))

from compare_render import _read_rgb, delta_e_cie76  # noqa: E402
from jpeg_reference import jpeg_encode_like  # noqa: E402
from picasapy.ini.filters import parse_filters_prefix  # noqa: E402
from picasapy.render import focal  # noqa: E402
from picasapy.render.chain import apply_filters  # noqa: E402
from picasapy.render.dinamikus_csuszka import (  # noqa: E402
    dinamikus_csuszka_ertek,
    fel_rovidebb_el,
)
from picasapy.render.glimmer_ops import alpha_blend, fade_alpha, masked_blend  # noqa: E402

_ADATOK = Path(__file__).parent / "data" / "focal_pixelate_6691"
_ADAT = json.loads((_ADATOK / "esetek.json").read_text(encoding="utf-8"))
_ESETEK = _ADAT["esetek"]
#: Az export JPEG-beállítása (mind a 9 azonos): a kvantálótábla kulcsa szám.
_JPEG = {
    "subsampling": _ADAT["jpeg"]["subsampling"],
    "qtables": {int(kulcs): tabla for kulcs, tabla in _ADAT["jpeg"]["qtables"].items()},
}

#: A jegy elfogadási küszöbe: ΔE átlag 1,0 alatt (`pixelhű`/`közelítés`). A javított
#: renderen az ablakok 0,000-0,726 közt vannak; a javítás előtt 1,0 fölött (a csak
#: kerekítést vagy csak a keverést javító változat is: 0,7-1,2, három ablakban >1,0).
_DELTA_E_ABLAK_MAX = 1.0
#: A teljesen pixelezett részen (maszk >= 0,99) a kimenet BITRE közeli: mért 0,000-0,037.
_DELTA_E_PIXELEZETT_MAX = 0.1
_PIXELEZETT_MASZK_MIN = 0.99
#: Ennél kevesebb teljesen pixelezett képpontnál a második mérés nem értelmes.
_PIXELEZETT_MIN_KEPPONT = 2000


def _maszk_ablak(eset: dict) -> np.ndarray:
    """A lánc maszkja az ablakban (a `Radius` százalék -> képpont, mint a láncban)."""
    szelesseg, magassag = eset["meret"]
    x0, y0, x1, y1 = eset["ablak"]
    x, y, _impact, radius, kemenyseg, _fade, _reverse = (
        float(ertek) for ertek in eset["filters"].split("=")[1].rstrip(";").split(",")[1:]
    )
    sugar = dinamikus_csuszka_ertek(radius, 10.0, fel_rovidebb_el(magassag, szelesseg))
    return focal.focal_mask(magassag, szelesseg, x, y, sugar, kemenyseg)[y0:y1, x0:x1]


def _render_ablak(eset: dict) -> np.ndarray:
    """A forráskivágást a valódi helyére illeszti, lefuttatja a láncot, és az ablakot adja."""
    szelesseg, magassag = eset["meret"]
    px0, py0, px1, py1 = eset["beillesztes"]
    x0, y0, x1, y1 = eset["ablak"]
    vaszon = np.zeros((magassag, szelesseg, 3), dtype=np.uint8)
    vaszon[py0:py1, px0:px1] = _read_rgb(_ADATOK / f"{eset['lanc']}_forras.png")
    kep = apply_filters(vaszon, parse_filters_prefix(eset["filters"])).image
    ujrakodolt = Image.open(io.BytesIO(jpeg_encode_like(kep, _JPEG))).convert("RGB")
    return np.asarray(ujrakodolt)[y0:y1, x0:x1]


def test_a_9_mert_eset_mind_szerepel() -> None:
    assert [eset["lanc"] for eset in _ESETEK] == [
        "lanc-0142", "lanc-0048", "lanc-0124", "lanc-0067", "lanc-0022",
        "lanc-0088", "lanc-0115", "lanc-0175", "lanc-0190",
    ]


@pytest.mark.parametrize("eset", _ESETEK, ids=lambda eset: f"{eset['lanc']}-{eset['feladat']}-{eset['kep']}")
def test_focal_pixelate_egyezik_az_eredeti_exporttal(eset: dict) -> None:
    export = _read_rgb(_ADATOK / f"{eset['lanc']}_export.png")
    kep = _render_ablak(eset)
    assert kep.shape == export.shape
    delta_e = delta_e_cie76(kep, export)
    atlag = float(delta_e.mean())
    assert atlag <= _DELTA_E_ABLAK_MAX, (
        f"{eset['lanc']}: ΔE átlag {atlag:.3f}, a küszöb {_DELTA_E_ABLAK_MAX}"
    )
    pixelezett = _maszk_ablak(eset) >= _PIXELEZETT_MASZK_MIN
    if int(pixelezett.sum()) >= _PIXELEZETT_MIN_KEPPONT:
        resz = float(delta_e[pixelezett].mean())
        assert resz <= _DELTA_E_PIXELEZETT_MAX, (
            f"{eset['lanc']}: a teljesen pixelezett részen ΔE {resz:.3f} > {_DELTA_E_PIXELEZETT_MAX}"
        )


def test_legalabb_hat_ablakban_van_teljesen_pixelezett_resz() -> None:
    """A második (bitre közeli) mérés ne üresedjen ki: legalább 6 ablaknak van hozzá elég képpontja."""
    szamok = [
        int((_maszk_ablak(eset) >= _PIXELEZETT_MASZK_MIN).sum()) for eset in _ESETEK
    ]
    assert sum(1 for szam in szamok if szam >= _PIXELEZETT_MIN_KEPPONT) >= 6, szamok


@pytest.mark.parametrize(
    ("szelesseg", "magassag", "impact", "kicsi"),
    [
        (1280, 853, 36.231898, (35, 24)),  # 35,33 -> 35 és 23,54 -> 24 (lanc-0124)
        (1280, 853, 5.110434, (250, 167)),  # 250,47 -> 250 és 166,91 -> 167 (lanc-0067)
        (1280, 720, 42.726991, (30, 17)),  # 29,96 -> 30 és 16,85 -> 17 (lanc-0142)
        (105, 105, 10.0, (11, 11)),  # pontosan 10,5 -> 11 (a `round()` párosra, 10-re kerekítene)
    ],
)
def test_focal_pixelate_celmeretet_kerekit_nem_csonkol(
    monkeypatch, szelesseg: int, magassag: int, impact: float, kicsi: tuple[int, int]
) -> None:
    """A kicsinyítő `Resize` célmérete `trunc(v + 0,5)`, mint a `Pixelate`-nél (#4912)."""
    hivasok: list[tuple[int, int, bool]] = []
    eredeti = focal.resize_image

    def figyelo(image, width, height, smoothing=True, lanczos3=False):
        hivasok.append((width, height, smoothing))
        return eredeti(image, width, height, smoothing=smoothing, lanczos3=lanczos3)

    monkeypatch.setattr(focal, "resize_image", figyelo)
    focal.apply_focal_pixelate(np.zeros((magassag, szelesseg, 3), dtype=np.uint8), impact=impact)

    kicsinyites, nagyitas = hivasok
    assert kicsinyites == (kicsi[0], kicsi[1], True)
    assert nagyitas == (szelesseg, magassag, False)


def _szintetikus_kep() -> np.ndarray:
    rng = np.random.default_rng(6691)
    return rng.integers(0, 256, size=(48, 64, 3), dtype=np.uint8)


@pytest.mark.parametrize("fade", [0.0, 4.7, 36.2, 63.2, 100.0])
def test_focal_pixelate_a_nativ_egesz_keveressel_kever(fade: float) -> None:
    """Előbb a Fade (`alpha_blend`), utána a maszk (`masked_blend`), egész képletekkel."""
    kep = _szintetikus_kep()
    x, y, impact, radius, kemenyseg = 0.4, 0.6, 8.0, 12.0, 40.0
    vart_pixelezett = focal.resize_image(
        focal.resize_image(kep, 8, 6, smoothing=True), 64, 48, smoothing=False
    )
    maszk = focal.focal_mask(48, 64, x, y, radius, kemenyseg)
    alap = kep.astype(np.float32)
    elhalvanyitott = alpha_blend(alap, vart_pixelezett.astype(np.float32), fade_alpha(fade))
    vart = np.clip(np.rint(masked_blend(alap, elhalvanyitott, maszk)), 0, 255).astype(np.uint8)

    kapott = focal.apply_focal_pixelate(
        kep, x=x, y=y, impact=impact, radius=radius, hardness=kemenyseg, fade=fade
    )
    np.testing.assert_array_equal(kapott, vart)


def test_focal_pixelate_belso_kor_bitre_az_eredeti() -> None:
    """A belső körön belül (maszk 0) a kép bitre azonos a bemenettel, bármilyen Fade mellett."""
    kep = _szintetikus_kep()
    kapott = focal.apply_focal_pixelate(
        kep, x=0.5, y=0.5, impact=8.0, radius=20.0, hardness=100.0, fade=30.0
    )
    maszk = focal.focal_mask(48, 64, 0.5, 0.5, 20.0, 100.0)
    belul = maszk == 0.0
    assert belul.any()
    np.testing.assert_array_equal(kapott[belul], kep[belul])

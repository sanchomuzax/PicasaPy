"""A GPU-shader „pontonkénti" előnézeti lánc CPU-oldali segédei (#22).

A GPU-renderpipeline (QML `ShaderEffect`) a `finetune2`/`fill`
(Fill Light/Highlights/Shadows/Color Temperature), `sat` és `bw` szűrőket
gyorsítja élő csúszka-húzás közben — ez a leggyakrabban, mozgatásonként
újra-renderelt út (`EditorPanel.qml` `finetunePreview` jele minden
egérmozgásra tüzel). A tényleges pixel-matematika a CPU-oldali
igazságforrás (`picasapy.render.tone`/`color`) EGYSZER kiszámolt eredménye:

- a `finetune2`/`fill` láncrész (fill → highlights → shadows → [semleges-
  pipetta] → színhőmérséklet) CSATORNÁNKÉNT FÜGGETLEN LUT — ezt bizonyítja,
  hogy mindegyik lépés vagy azonos (csatorna-vak) LUT-ot alkalmaz mindhárom
  csatornára (`apply_lut`), vagy már eleve csatornánkénti LUT-ot
  (`apply_channel_luts`), sosem keveri a csatornákat. Emiatt a teljes
  kompozit pontosan reprodukálható egyetlen 256×1 RGB textúrával: a
  `build_finetune2_lut()` egy szintetikus (1, 256, 3) „rámpa-képen" (minden
  pixel (i, i, i)) FUTTATJA a valódi `apply_finetune2()`-t, és a kimenet
  R/G/B csatornái pontosan a keresett LUT-ok — nem közelítés, hanem a
  termelési kód literális újrafelhasználása.
- a `sat` (telítettség) és `bw` (fekete-fehér) NEM csatornánkénti LUT (a
  luma mindhárom csatornától függ), ezért ezeket a fragment shader
  analitikusan számolja. A `sat` **negatív** ága luma-tartó skalár
  erősítés (`mix()`), az erősítést a CPU adja uniformként
  (`saturation_gain()` — ugyanaz az interpolált tábla, mint
  `picasapy.render.color.apply_saturation` negatív ága). A `sat`
  **pozitív** ága (#696, a #693 következménye) NEM erősítés — a
  `picasapy.render.saturation_positive` szerint csatornánkénti, MÁS
  kitevőjű gamma a `csatorna/luma` arányon, amire semmilyen skalár
  erősítés nem illeszthető. A shader ezért ezen az ágon a natív modellt
  futtatja (folytonos `pow()`, nem táblázat) —
  `simulate_positive_saturation_shader()` ennek a numpy-mása, a
  `PointFilter.frag` `applyPositiveSaturation()` szó szerint ezt a
  képletet ülteti át GLSL-be. Ez KÖZELÍTÉS a natív fixpontos, 2048
  elemű táblázathoz képest (nincs kvantálás), de a mért hiba
  nagyságrendekkel kisebb, mint a korábbi skalár-erősítéses közelítésé
  — ld. `tests/render/test_gpu_point_pipeline_positive_saturation.py`.

A `tint`/görbék GPU-fedezete KÖVETKEZŐ lépés (ld. a #22 jelentés
„hátralévő munka" pontját) — jelenleg csak a fenti három szűrő fut GPU-n.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from picasapy.render.color import saturation_gain as _saturation_gain
from picasapy.render.saturation_positive import CHANNEL_EXPONENTS
from picasapy.render.tone import apply_finetune2

#: A `csatorna/luma` arány felső vágása — a natív kód `apply_positive_
#: saturation`-jában ez a LUT-index-vágás (`_LUT_RANGE = 8.0`, `index =
#: min((k·csatorna) >> 8, 2047)`) közvetett következménye: a tábla `x`
#: tartománya `[0, 8)`, tehát minden ennél nagyobb arány ugyanarra a
#: szélső táblaértékre képződik le. A folytonos `pow()`-modellben ez
#: EXPLICIT vágásként jelenik meg — enélkül a majdnem-fekete, erősen
#: színezett pixeleken a hatványozás elszáll (mért: ~250 szintnyi hiba
#: egyetlen pixelen, ld. a teszt docsztringje). A szám szándékosan
#: duplikált (nem importált a `saturation_positive` privát `_LUT_RANGE`-
#: jéből) — az egyezést teszt őrzi
#: (`test_gpu_point_pipeline_positive_saturation.py`).
_POSITIVE_SATURATION_RATIO_CLAMP = 8.0

#: Nullosztás-védelem a luma-normalizált arány (`csatorna / luma`)
#: számításánál — a natív kód ezt a `luma > 0` ágválasztással kerüli el
#: (ld. `saturation_positive.apply_positive_saturation` `nem_fekete`),
#: a folytonos GLSL-modell pedig ugyanezt az ágválasztást reprodukálja
#: (`luma <= 0` esetén a pixel változatlan marad); ez az epsilon csak a
#: köztes osztás numerikus stabilitásához kell.
_POSITIVE_SATURATION_EPSILON = 1e-6

#: A LUT-textúra mérete (256×1 — minden bemeneti bájtértékhez egy sor).
LUT_SIZE = 256


def build_finetune2_lut(
    *,
    fill: float = 0.0,
    highlights: float = 0.0,
    shadows: float = 0.0,
    neutral: tuple[int, int, int] | None = None,
    temperature: float = 0.0,
) -> np.ndarray:
    """A `finetune2`/`fill` kompozit csatornánkénti LUT-ja `(256, 3)` uint8-ban.

    A GPU-shader ezt tölti fel 256×1 RGB8 textúraként, és mindhárom
    csatornát KÜLÖN mintavételezi (`texture(lut, vec2(r, 0.5)).r`, …) — a
    három lekérdezés együtt pontosan a `apply_channel_luts`-alapú CPU-utat
    adja vissza, mert a lánc (ld. modul-docsztring) csatornánként független.

    **Nem nulla `fill` esetén `ValueError`.** A #551 mérése kimondta, hogy a
    Derítőfény a pixel VILÁGOSSÁGÁTÓL függő hozzáadás, nem csatornánkénti
    tónusgörbe — LUT-tá alakítva a rámpa-képen még helyesnek LÁTSZANA, de
    valódi (nem szürke) képen más eredményt adna, mint a CPU-út. A
    csatorna-függetlenség tehát csak `fill == 0`-nál áll fenn; a hívó
    (`EditController.previewFinetuneGpu`) ilyenkor a CPU-útra esik vissza.
    """
    if fill != 0.0:
        raise ValueError(
            "A finetune2 GPU-LUT csak fill == 0 mellett érvényes (#551): "
            f"fill={fill!r}"
        )
    ramp = np.arange(LUT_SIZE, dtype=np.uint8)
    ramp_image = np.tile(ramp[np.newaxis, :, np.newaxis], (1, 1, 3))
    result = apply_finetune2(
        ramp_image,
        fill=fill,
        highlights=highlights,
        shadows=shadows,
        neutral=neutral,
        temperature=temperature,
    )
    return result[0]


def saturation_gain(strength: float) -> float:
    """A `sat` NEGATÍV ágának mért erősítés-táblája — azonos
    `picasapy.render.color.apply_saturation` negatív ágával, a skalár
    erősítést adja vissza (a shader ezt kapja `satGain` uniformként).

    A POZITÍV ágra (#696, #693) ez a függvény már NEM alkalmazandó — arra
    a shader `simulate_positive_saturation_shader()` szerinti gamma-
    modellt futtatja, `sat_positive_strength` uniformmal vezérelve."""
    return _saturation_gain(strength)


def simulate_positive_saturation_shader(image: np.ndarray, amount: float) -> np.ndarray:
    """A `PointFilter.frag` `applyPositiveSaturation()`-jának numpy-mása
    (#696) — a `sat` POZITÍV ágának natív, csatornánkénti gamma-modellje
    (`picasapy.render.saturation_positive`), a natív fixpontos táblázat
    helyett folytonos `pow()`-pal.

    ⚠️ **Ez a natív modell KÖZELÍTÉSE, nem bájtra pontos másolata.** A
    natív kód 2048 elemű, kvantált táblázatot használ csatornánként; ez a
    függvény (és a GLSL-portja) helyette valós idejű `pow()`-ot számol.
    A két lépés, ami nélkül a közelítés durván szétesne (mérve, ld. a
    teszt docsztringje):

    1. **A luma egész osztás** (`floor((2R + 5G + B) / 8)`, NEM folytonos
       osztás) — a natív kód `>> 3` bitléptetése ezt csinálja, és emiatt a
       majdnem-fekete pixelek egy része luma == 0-ra esik, ami a natív
       kódban „ne nyúlj a pixelhez" ágat választ. Folytonos luma esetén
       ugyanezek a pixelek téves gamma-számítást kapnának.
    2. **A `csatorna/luma` arány felülről vágva
       `_POSITIVE_SATURATION_RATIO_CLAMP`-nál** — ez a natív LUT
       index-vágásának (`min(index, 2047)`, `x` tartomány `[0, 8)`)
       közvetlen következménye. Enélkül majdnem-fekete, erősen színezett
       pixeleken a hatványozás elszáll.

    A CPU-igazságforráshoz (`saturation_positive.apply_positive_
    saturation`) képest mért átlagos abszolút eltérés a #696 mérőkészletén
    pozitív erősségeknél `<1,5` szint (a korábbi skalár-erősítéses
    GPU-közelítésnél mérve `13–19` szint volt) — ld.
    `tests/render/test_gpu_point_pipeline_positive_saturation.py`.

    `amount` a csúszka `[0, 1]` pozitív tartománya; `<= 0`-nál azonosság
    (a hívó ilyenkor a negatív ágat/`saturation_gain()`-t választja)."""
    if amount <= 0.0:
        return image.copy()
    strength = amount * 3.0
    exponent = 1.0 + strength * np.asarray(CHANNEL_EXPONENTS, dtype=np.float64)

    channels = image.astype(np.float64)
    red, green, blue = channels[..., 0], channels[..., 1], channels[..., 2]
    luma = np.floor((2.0 * red + 5.0 * green + blue) / 8.0)
    nem_fekete = luma > 0.0
    biztos_luma = np.maximum(luma, _POSITIVE_SATURATION_EPSILON)

    ratio = np.minimum(channels / biztos_luma[..., np.newaxis], _POSITIVE_SATURATION_RATIO_CLAMP)
    gamma_out = np.power(np.maximum(ratio, 0.0), exponent) * biztos_luma[..., np.newaxis]

    channel_max = np.max(gamma_out, axis=-1, keepdims=True)
    normalized = np.where(
        channel_max > 255.0,
        gamma_out * 255.0 / np.maximum(channel_max, _POSITIVE_SATURATION_EPSILON),
        gamma_out,
    )
    blended = np.where(nem_fekete[..., np.newaxis], normalized, channels)
    return np.clip(np.round(blended), 0, 255).astype(np.uint8)


@dataclass(frozen=True)
class PointPipelineUniforms:
    """A GPU pontonkénti-lánc shaderjének teljes uniform-készlete.

    A `lut` a `finetune2`/`fill` csatornánkénti textúrája. A telítettség
    KÉT uniformmal vezérelt, a natív `sat` két ágának megfelelően (#696):
    `sat_gain` a NEGATÍV ág luma-tartó skalár erősítése (1.0 = azonosság),
    `sat_positive_strength` a POZITÍV ág gamma-modelljének erőssége
    (`amount·3`, 0.0 = azonosság/negatív ág). A shader a kettő közül
    pontosan az egyiket alkalmazza (`sat_positive_strength > 0.0`
    választja a gamma-ágat), sosem mindkettőt. `bw_mix` 0.0/1.0 kapcsoló a
    fekete-fehér keveréshez (a Picasa `bw` egykattintásos, nem csúszka —
    a shaderben mégis folytonos `mix()`-ként implementált, hogy egy
    jövőbeli finomítás csúszkásíthassa)."""

    lut: np.ndarray  # (256, 3) uint8
    sat_gain: float
    sat_positive_strength: float
    bw_mix: float


def build_point_pipeline_uniforms(
    *,
    fill: float = 0.0,
    highlights: float = 0.0,
    shadows: float = 0.0,
    neutral: tuple[int, int, int] | None = None,
    temperature: float = 0.0,
    saturation: float = 0.0,
    black_and_white: bool = False,
) -> PointPipelineUniforms:
    """Az `EditController`/QML-integráció egyetlen belépési pontja: a
    finomhangolás-csúszkák + telítettség + fekete-fehér paramétereiből
    előállítja a GPU-shader teljes uniform-készletét."""
    lut = build_finetune2_lut(
        fill=fill,
        highlights=highlights,
        shadows=shadows,
        neutral=neutral,
        temperature=temperature,
    )
    if saturation > 0.0:
        # #696: a pozitív ág a shaderben a gamma-modellt futtatja — a
        # skalár `sat_gain` ilyenkor azonosságon marad (nem használja a
        # shader, de a dataclass mezője nem lehet None).
        gain = 1.0
        positive_strength = saturation * 3.0
    elif saturation < 0.0:
        gain = saturation_gain(saturation)
        positive_strength = 0.0
    else:
        gain = 1.0
        positive_strength = 0.0
    return PointPipelineUniforms(
        lut=lut,
        sat_gain=gain,
        sat_positive_strength=positive_strength,
        bw_mix=1.0 if black_and_white else 0.0,
    )


__all__ = [
    "LUT_SIZE",
    "PointPipelineUniforms",
    "build_finetune2_lut",
    "build_point_pipeline_uniforms",
    "saturation_gain",
    "simulate_positive_saturation_shader",
]

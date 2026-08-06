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
  analitikusan számolja (`GLOW`-mentes, egyszerű `dot()`+`mix()`), a
  `sat` erősítés-értékét (`gain(s)`) a CPU adja uniformként
  (`saturation_gain()` — ugyanaz az interpolált tábla, mint
  `picasapy.render.color.apply_saturation`).

A `tint`/görbék GPU-fedezete KÖVETKEZŐ lépés (ld. a #22 jelentés
„hátralévő munka" pontját) — jelenleg csak a fenti három szűrő fut GPU-n.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from picasapy.render.color import saturation_gain as _saturation_gain
from picasapy.render.tone import apply_finetune2

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
    """
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
    """A `sat` mért erősítés-táblájának interpolációja — azonos
    `picasapy.render.color.apply_saturation`-nal, csak a skalár erősítést
    adja vissza (a shader ezt kapja `satGain` uniformként)."""
    return _saturation_gain(strength)


@dataclass(frozen=True)
class PointPipelineUniforms:
    """A GPU pontonkénti-lánc shaderjének teljes uniform-készlete.

    A `lut` a `finetune2`/`fill` csatornánkénti textúrája; `sat_gain` a
    telítettség erősítése (1.0 = azonosság); `bw_mix` 0.0/1.0 kapcsoló a
    fekete-fehér keveréshez (a Picasa `bw` egykattintásos, nem csúszka —
    a shaderben mégis folytonos `mix()`-ként implementált, hogy egy
    jövőbeli finomítás csúszkásíthassa)."""

    lut: np.ndarray  # (256, 3) uint8
    sat_gain: float
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
    gain = saturation_gain(saturation) if saturation != 0.0 else 1.0
    return PointPipelineUniforms(
        lut=lut,
        sat_gain=gain,
        bw_mix=1.0 if black_and_white else 0.0,
    )


__all__ = [
    "LUT_SIZE",
    "PointPipelineUniforms",
    "build_finetune2_lut",
    "build_point_pipeline_uniforms",
    "saturation_gain",
]

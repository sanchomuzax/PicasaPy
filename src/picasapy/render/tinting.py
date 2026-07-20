"""Színező effekt-műveletek: tint, ansel, dir_tint.

Mért alapok (`docs/specs/filters-decoded.md`, 3. kör):

- **tint** — `tint=1,79.842102,ffff` szürke rámpán az R-csatornát nullázza,
  G és B változatlan: a rövid `ffff` szín balra nullákkal kiegészítve
  `0000ffff` (cián) → a luma csatornánkénti szorzása a színnel pontosan ezt
  adja. A `preserve` paraméter szürkén mérten hatástalan; színes képen a
  króma visszakeverésének súlyaként értelmezzük (0..100 skála) — KÖZELÍTÉS.
- **ansel** — `ansel=1,ffffffff` kimenete semleges (R=G=B), enyhe
  középemeléssel; a pontos tónusgörbe méretlen → gamma 0,93 KÖZELÍTÉS
  (végpont-tartó, enyhe középemelés). A színparaméter a tint-tel azonos
  módon színez.
- **dir_tint** — nincs mért kimeneti adat; a modell (függőleges színátmenet
  az y középpont körül, `gradiens` szélességű átmenettel, `árnyék` erősségű
  keveréssel a szín felé; az x és az irány szerepe méretlen) dokumentált
  KÖZELÍTÉS — a #115 golden-harness pontosítja majd.
"""

from __future__ import annotations

import re

import numpy as np

from picasapy.render.curves import validate_image

_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{1,8}$")

# ansel: enyhe középemelés — méretlen görbe helyett gamma-KÖZELÍTÉS
# (0→0, 255→255, 128→~134; a spec csak a jelleget rögzíti).
_ANSEL_GAMMA = 0.93

# tint: a preserve paraméter skálája (79.842102 az éles példa) — 0..100.
_PRESERVE_SCALE = 100.0


def parse_rgb_hex(value: str) -> tuple[int, int, int]:
    """A filters-beli hex színparaméter (AARRGGBB) értelmezése (R, G, B)-ként.

    A Picasa a vezető nullákat elhagyja (pl. `ffff` = `0000ffff` → cián),
    ezért az értéket balra nullákkal 8 jegyre egészítjük ki; az alfa-mezőt
    nem használjuk.
    """
    text = value.strip()
    if not _HEX_PATTERN.match(text):
        raise ValueError(f"Érvénytelen hex színérték: {value!r}")
    padded = text.rjust(8, "0")
    return (int(padded[2:4], 16), int(padded[4:6], 16), int(padded[6:8], 16))


def _luma(image: np.ndarray) -> np.ndarray:
    """Rec.601 luminancia float32 (H, W) tömbként."""
    image_f = image.astype(np.float32)
    return (
        np.float32(0.299) * image_f[..., 0]
        + np.float32(0.587) * image_f[..., 1]
        + np.float32(0.114) * image_f[..., 2]
    )


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def _colorize(gray: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """Szürke (H, W) float kép csatornánkénti színezése: `ki_c = szürke·c/255`."""
    factors = np.array(color, dtype=np.float32) / np.float32(255.0)
    return gray[..., np.newaxis] * factors


def apply_tint(
    image: np.ndarray, preserve: float, color: tuple[int, int, int]
) -> np.ndarray:
    """Színezés: a Rec.601 luma szorzása a színnel, króma-visszakeveréssel.

    `ki = luma·szín/255 + (preserve/100)·(be − luma)` — a mért cián eset
    (szürkén R=0, G=B változatlan) pontos; a preserve súly-értelmezése
    színes képen KÖZELÍTÉS.
    """
    validate_image(image)
    gray = _luma(image)
    tinted = _colorize(gray, color)
    keep = float(np.clip(preserve / _PRESERVE_SCALE, 0.0, 1.0))
    if keep > 0.0:
        tinted = tinted + np.float32(keep) * (
            image.astype(np.float32) - gray[..., np.newaxis]
        )
    return _to_uint8(tinted)


def apply_ansel(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """Ansel-effekt: fekete-fehér + enyhe középemelő tónusgörbe + színezés.

    A görbe gamma-KÖZELÍTÉS (`ki = 255·(luma/255)^0,93`): végpont-tartó,
    a mért „enyhe középemelés" jelleggel; fehér színparaméterrel a kimenet
    semleges (R=G=B), ahogy a golden-mérés mutatta.
    """
    validate_image(image)
    gray = _luma(image)
    lifted = np.float32(255.0) * np.power(
        gray / np.float32(255.0), np.float32(_ANSEL_GAMMA)
    )
    return _to_uint8(_colorize(lifted, color))


def apply_dir_tint(
    image: np.ndarray,
    x: float,
    y: float,
    gradient: float,
    shade: float,
    color: tuple[int, int, int],
) -> np.ndarray:
    """Irányított (átmenetes) színezés — dokumentált KÖZELÍTÉS.

    Függőleges színátmenet: az `y` normált magasság körüli, `gradient`
    szélességű sávban a súly 1-ről 0-ra fut le; felette a kép `shade`
    erősséggel a szín felé keveredik, alatta változatlan. Az `x` paraméter
    és az átmenet iránya méretlen — itt nem használt.
    """
    validate_image(image)
    height = image.shape[0]
    rows = (np.arange(height, dtype=np.float32) + 0.5) / np.float32(height)
    span = max(gradient, 1e-6)
    weight = np.clip(0.5 - (rows - np.float32(y)) / np.float32(span), 0.0, 1.0)
    strength = float(np.clip(shade, 0.0, 1.0))
    if strength == 0.0:
        return image.copy()
    image_f = image.astype(np.float32)
    target = np.array(color, dtype=np.float32)
    blend = weight[:, np.newaxis, np.newaxis] * np.float32(strength)
    return _to_uint8(image_f + blend * (target - image_f))

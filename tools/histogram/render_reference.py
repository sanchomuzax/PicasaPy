#!/usr/bin/env python3
"""Hisztogram-referencia renderelő a Picasa-összevetéshez (#236).

MIT csinál:
    Betölti a `tests/support/histogram_reference` determinisztikus
    referencia-képeit, mindegyikre kiszámítja a
    `picasapy.app.histogram_helper.compute_rgb_histogram` kimenetét, majd
    PNG-be rajzolja a visszafejtett Picasa-hisztogramot: 256 × 70-es belső
    kép, +85-ös összeadó RGBA-keverés, majd 213 × 59-es megjelenítés.
    Emellett kiírja a nyers referencia-képeket is.

MIÉRT nem valódi QML `grabToImage`:
    A fej nélküli QML-render időzítésfüggő lehet (#232). Ezért ez az eszköz
    közvetlenül a dokumentált natív konstansokból állítja elő a referenciát;
    a tényleges QML-kimenetet ettől független, valódi `QQuickView`-os
    képpontteszt ellenőrzi (`test_histogram_pixels_864.py`).

Futtatás (headless is jó):
    QT_QPA_PLATFORM=offscreen python3 tools/histogram/render_reference.py \
        --out tools/histogram/out

    Kimenet a --out könyvtárban:
      <név>.png            — a nyers referencia-kép (Picasába betölthető)
      <név>__hist.png      — a PicasaPy hisztogram-doboz renderje

Ez a szkript fejlesztői eszköz (nem a csomag része) — OpenCV-t igényel.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

# A repó gyökere és a `src/` a sys.path-ra, hogy a `picasapy` (src-layout) és
# a `tests.support` csomag közvetlen futtatáskor is importálható legyen (a
# pytest ugyanezt teszi a pyproject `pythonpath = ["src", "tests"]` alapján).
_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from picasapy.app.histogram_helper import compute_rgb_histogram  # noqa: E402
from tests.support.histogram_reference import (  # noqa: E402
    REFERENCES,
    write_reference_pngs,
)

# A natív bittérkép és a felületen látható doboz mérete (#864).
_INTERNAL_W = 256
_INTERNAL_H = 70
_DISPLAY_W = 213
_DISPLAY_H = 59
_CHANNEL_INCREMENT = 85


def _render_box(hist: dict[str, list[float]]) -> np.ndarray:
    """A bináris specifikációból levezetett, 213 × 59-es RGB-kép."""
    import cv2

    heights = np.rint(
        np.asarray([hist["r"], hist["g"], hist["b"]]) * _INTERNAL_H
    ).astype(np.int16)
    heights = np.clip(heights, 0, _INTERNAL_H)
    internal = np.full((_INTERNAL_H, _INTERNAL_W, 3), 255, dtype=np.uint8)

    for x in range(_INTERNAL_W):
        for from_bottom in range(int(heights[:, x].max(initial=0))):
            active = heights[:, x] > from_bottom
            channel_count = int(active.sum())
            alpha = channel_count * _CHANNEL_INCREMENT
            # Szorzott-alfa puffer fehér háttérre: rawRGB + 255 - alpha.
            raw_rgb = active.astype(np.int16) * _CHANNEL_INCREMENT
            displayed = raw_rgb + 255 - alpha
            internal[_INTERNAL_H - from_bottom - 1, x] = displayed.astype(np.uint8)

    return cv2.resize(
        internal,
        (_DISPLAY_W, _DISPLAY_H),
        interpolation=cv2.INTER_LINEAR,
    )


def render_all(out_dir: Path) -> list[Path]:
    """Minden referenciára kiírja a nyers képet és a hisztogram-renderjét."""
    import cv2

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # nyers referencia-képek (Picasába betölthetők)
    write_reference_pngs(out_dir)

    written: list[Path] = []
    for ref in REFERENCES:
        hist = compute_rgb_histogram(ref.array)
        box = _render_box(hist)
        path = out_dir / f"{ref.name}__hist.png"
        if not cv2.imwrite(str(path), box[:, :, ::-1]):  # RGB → BGR
            raise RuntimeError(f"PNG-írás sikertelen: {path}")
        written.append(path)
        print(f"  {ref.name:<18} → {path.name}  ({ref.title})")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "out",
        help="kimeneti könyvtár (alapértelmezés: tools/histogram/out)",
    )
    args = parser.parse_args(argv)
    print(f"Hisztogram-referencia renderelése ide: {args.out}")
    render_all(args.out)
    print("Kész.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

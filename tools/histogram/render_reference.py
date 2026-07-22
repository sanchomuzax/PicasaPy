#!/usr/bin/env python3
"""Hisztogram-referencia renderelő a Picasa-összevetéshez (#236).

MIT csinál:
    Betölti a `tests/support/histogram_reference` determinisztikus
    referencia-képeit, mindegyikre kiszámítja a
    `picasapy.app.histogram_helper.compute_rgb_histogram` kimenetét, majd
    PNG-be rajzolja a PicasaPy hisztogram-dobozát — pontosan azzal a
    skálázással és színvilággal, ahogy a QML-oldali `HistogramBox.qml`.
    Emellett kiírja a nyers referencia-képeket is (a felhasználó ezeket
    nyitja meg a Windows-os Picasa 3-ban a golden-screenshotokhoz).

MIÉRT nem valódi QML `grabToImage`:
    A HistogramBox egy deklaratív, sok apró `Rectangle`-oszlopból álló QML
    komponens (ld. #232). A `grabToImage` teljes QML-scene-graph render-loopot
    igényel, ami headless (offscreen) CI-környezetben törékeny és
    időzítés-függő — pont az a probléma, ami miatt a Canvas-t is lecseréltük.
    Ezért a golden előállításához a hisztogram-ADATOT rajzoljuk PNG-be, a
    QML-lel AZONOS képlettel (ld. lentebb a `_render_box`-ban a HistogramBox
    hivatkozásokat). Ez determinisztikus, gyors és pontosan reprodukálja a
    doboz kinézetét — a normalizálás (#232) hű összevetéséhez ez elég.

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

# A HistogramBox.qml / Theme.qml megfelelői (RGB). A QML a három csatornát
# 0.55 opacitással EGYMÁSRA rajzolja — ugyanezt tesszük alfa-keveréssel.
_BRAND_RED = (224, 74, 63)  # Theme.brandRed  #e04a3f
_BRAND_GREEN = (13, 171, 98)  # Theme.brandGreen #0dab62
_BRAND_BLUE = (68, 138, 253)  # Theme.brandBlue  #448afd
_PANEL = (255, 255, 255)  # Theme.contentPanel #ffffff
_BORDER = (205, 205, 205)  # Theme.chromeBorder #cdcdcd
_BAR_OPACITY = 0.55  # HistogramBox delegate opacity

# A render-doboz mérete (a plot-rész arányai a néző dobozát közelítik).
_BOX_W = 512
_PLOT_H = 200
_MARGIN = 8
_BUCKETS = 256


def _render_box(hist: dict[str, list[float]]) -> np.ndarray:
    """A hisztogram-dobozt RGB uint8 képbe rajzolja, a QML-lel azonos módon.

    A QML delegate: ``height = v * plot.height``, az oszlop alulról nő
    (``y = plot.height - height``), szélessége ``ceil(plot.width/256)``, és a
    három csatorna 0.55 opacitással egymásra keveredik. Ugyanezt reprodukáljuk.
    """
    plot_w = _BOX_W - 2 * _MARGIN
    canvas = np.zeros((_PLOT_H, plot_w, 3), dtype=np.float64)
    canvas[:, :] = _PANEL

    bar_w = int(np.ceil(plot_w / _BUCKETS))
    for values, colour in (
        (hist["r"], _BRAND_RED),
        (hist["g"], _BRAND_GREEN),
        (hist["b"], _BRAND_BLUE),
    ):
        colour_arr = np.asarray(colour, dtype=np.float64)
        for index, v in enumerate(values):
            if v <= 0:
                continue
            height = int(round(v * _PLOT_H))
            if height <= 0:
                continue
            x0 = int(index * (plot_w / _BUCKETS))
            x1 = min(x0 + bar_w, plot_w)
            y0 = _PLOT_H - height
            region = canvas[y0:_PLOT_H, x0:x1]
            # alfa-keverés (a QML opacity 0.55-ös rárajzolása)
            region[:] = region * (1 - _BAR_OPACITY) + colour_arr * _BAR_OPACITY

    # 1px keret a doboz köré (chromeBorder)
    framed = np.zeros((_PLOT_H + 2, plot_w + 2, 3), dtype=np.float64)
    framed[:, :] = _BORDER
    framed[1:-1, 1:-1] = canvas
    return np.clip(framed, 0, 255).astype(np.uint8)


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

#!/usr/bin/env python3
"""Golden-elemzés 2. kör: színmodellek (sepia/warm/tint/ansel), sat-gain,
fill görbeillesztés.

Használat: analyze_goldens2.py <golden-kit-result> <analysis_dir>
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

RESULT = Path(sys.argv[1])
AN = Path(sys.argv[2])


def gray_ramp_channels(folder, name):
    img = cv2.imread(str(RESULT / "export" / folder / name))
    band = img[60:240].astype(np.float64).mean(axis=0)  # (1600, BGR)
    xs = np.arange(1600) * 255.0 / 1599
    return xs, band


def main():
    print("=== 1) Színmodellek a szürke rámpán: g → (R,G,B) ===")
    for folder, name in (("05-tone", "sepia"), ("05-tone", "warm"),
                         ("05-tone", "grain2")):
        xs, band = gray_ramp_channels(folder, f"chart_ramp__{name}.jpg")
        print(f"\n  {name}:")
        for g in (32, 96, 160, 224):
            i = int(g * 1599 / 255)
            b, gr, r = band[i]
            print(f"    g={g:>3} → R={r:6.1f} G={gr:6.1f} B={b:6.1f}")
        # lineáris illesztés csatornánként a nem klippelt szakaszon
        mask = (band.max(axis=1) < 250) & (band.min(axis=1) > 5)
        if mask.sum() > 200:
            fits = []
            for ch in (2, 1, 0):  # R,G,B
                a, c = np.polyfit(xs[mask], band[mask, ch], 1)
                fits.append(f"{'RGB'[2-ch] if ch!=1 else 'G'}={a:.4f}g{c:+.1f}")
            print(f"    lineáris: {'  '.join(fits)}")

    print("\n=== 2) sat gain (klippeletlen, alacsony-S pixeleken) ===")
    base = cv2.cvtColor(cv2.imread(str(RESULT / "export/00-base/chart_color.jpg")),
                        cv2.COLOR_BGR2HSV)
    sel = base[..., 1] < 90
    s0 = base[..., 1][sel].astype(float)
    for v, expected in (("satm033", 1 - 0.333), ("satp025", 1.25),
                        ("satp050", 1.5), ("satp100", 2.0)):
        img = cv2.cvtColor(
            cv2.imread(str(RESULT / "export/06-sat" / f"chart_color__{v}.jpg")),
            cv2.COLOR_BGR2HSV)
        s1 = img[..., 1][sel].astype(float)
        gain = (s1.mean() / s0.mean())
        print(f"  {v}: mért gain={gain:.3f}   (1+s hipotézis: {expected:.3f})")

    print("\n=== 3) fill görbeillesztés (adaptív gamma család) ===")
    luts = json.loads((AN / "luts.json").read_text())
    t = np.arange(256) / 255.0
    best = None
    for k in np.arange(0.5, 4.01, 0.05):
        for p in np.arange(0.5, 3.01, 0.05):
            err = 0.0
            for s, key in ((0.25, "fill025"), (0.5, "fill050"),
                           (0.75, "fill075"), (1.0, "fill100")):
                y = np.array(luts[key]) / 255.0
                model = t ** (1.0 / (1.0 + k * s * (1 - t) ** p))
                err += float(((y - model) ** 2)[8:250].mean())
            if best is None or err < best[0]:
                best = (err, k, p)
    err, k, p = best
    rmse = (err / 4) ** 0.5 * 255
    print(f"  y = t^(1/(1+k·s·(1-t)^p))  →  k={k:.2f}, p={p:.2f}, "
          f"RMSE={rmse:.2f}/255")
    for s, key in ((0.5, "fill050"), (1.0, "fill100")):
        y = np.array(luts[key])
        model = 255 * t ** (1.0 / (1.0 + k * s * (1 - t) ** p))
        print(f"    fill{int(s*100):03d} max|Δ|: {np.abs(y - model)[8:250].max():.1f}")


if __name__ == "__main__":
    main()

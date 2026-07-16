#!/usr/bin/env python3
"""Golden-elemzés 1. kör: tónusgörbék (LUT-ok) kinyerése a chart_ramp
exportokból + gyors megállapítások.

A chart_ramp felépítése (make_golden_kit.py):
  y   0..300  vízszintes szürke rámpa (x → 0..255)
  y 300..600  16 lépcső
  y 600..800  kék rámpa, 800..1000 zöld, 1000..1200 piros

Használat: analyze_goldens.py <golden-kit-result> <kimenet_dir>
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

RESULT = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

W = 1600


def ramp_lut(img, y0=60, y1=240):
    """A szürke rámpából 256 elemű ki-bemeneti LUT (átlagolt sorokkal)."""
    band = img[y0:y1].astype(np.float64).mean(axis=(0, 2))  # x → szürke ki
    xs = np.arange(W)
    ins = xs * 255.0 / (W - 1)
    lut = np.interp(np.arange(256), ins, band)
    return lut


def channel_ramps(img):
    """A B/G/R rámpasávokból csatornánkénti kimenet (255 bemenetnél)."""
    out = {}
    for name, y0 in (("B", 660), ("G", 860), ("R", 1060)):
        band = img[y0:y0 + 80].astype(np.float64).mean(axis=0)  # (1600, 3)
        out[name] = band
    return out


def load(folder, name):
    p = RESULT / "export" / folder / name
    img = cv2.imread(str(p))
    assert img is not None, p
    return img


def main():
    base = load("00-base", "chart_ramp.jpg")
    base_lut = ramp_lut(base)
    luts = {"base": base_lut.tolist()}

    print("=== 1) Automaták (tartalomfüggő — chart-specifikus görbe) ===")
    for v in ("enhance", "autolight", "autocolor"):
        lut = ramp_lut(load("01-auto", f"chart_ramp__{v}.jpg"))
        luts[v] = lut.tolist()
        lo = np.argmax(lut > base_lut[0] + 2)
        d_mid = lut[128] - base_lut[128]
        d_lo = lut[32] - base_lut[32]
        d_hi = lut[224] - base_lut[224]
        print(f"  {v:<10} Δ@32={d_lo:+6.1f}  Δ@128={d_mid:+6.1f}  "
              f"Δ@224={d_hi:+6.1f}")

    print("\n=== 2) fill light sweep ===")
    for s in ("025", "050", "075", "100"):
        lut = ramp_lut(load("02-fill", f"chart_ramp__fill{s}.jpg"))
        luts[f"fill{s}"] = lut.tolist()
        print(f"  fill{s}: ki(32)={lut[32]:6.1f}  ki(128)={lut[128]:6.1f}  "
              f"ki(224)={lut[224]:6.1f}  ki(255)={lut[255]:6.1f}")

    print("\n=== 3) finetune2 paraméter-azonosítás ===")
    for v in ("b025", "b050", "b100", "h050", "h100", "s050", "s100",
              "tempA", "tempB", "u-05", "u+05", "u+10"):
        lut = ramp_lut(load("03-finetune2", f"chart_ramp__{v}.jpg"))
        luts[f"ft2_{v}"] = lut.tolist()
        print(f"  {v:<6} ki(16)={lut[16]:6.1f} ki(64)={lut[64]:6.1f} "
              f"ki(128)={lut[128]:6.1f} ki(192)={lut[192]:6.1f} "
              f"ki(240)={lut[240]:6.1f}")

    print("\n=== 4) finetune v1 == v2? ===")
    for v in ("b050", "u+05", "u-05"):
        l1 = ramp_lut(load("04-finetune1", f"chart_ramp__{v}.jpg"))
        l2 = np.array(luts[f"ft2_{v}"])
        print(f"  {v}: max|v1-v2| = {np.abs(l1 - l2).max():.2f}")

    print("\n=== 5) bw súlyok (R/G/B rámpákból) ===")
    ch_b = channel_ramps(load("05-tone", "chart_ramp__bw.jpg"))
    for name in ("B", "G", "R"):
        gray = ch_b[name].mean(axis=1)  # szürke kimenet
        # meredekség a lineáris szakaszon (x=200..1400)
        xs = np.arange(200, 1400) * 255.0 / (W - 1)
        slope = np.polyfit(xs, gray[200:1400], 1)[0]
        print(f"  {name}-rámpa → szürke meredekség: {slope:.4f}")

    print("\n=== 6) sat viselkedés (színes charton, HSV-ben) ===")
    base_c = cv2.cvtColor(load("00-base", "chart_color.jpg"),
                          cv2.COLOR_BGR2HSV)
    for v in ("satm033", "satp025", "satp050", "satp100"):
        img = cv2.cvtColor(load("06-sat", f"chart_color__{v}.jpg"),
                           cv2.COLOR_BGR2HSV)
        ratio = (img[..., 1].astype(float).mean()
                 / base_c[..., 1].astype(float).mean())
        print(f"  {v}: átlagos S-arány = {ratio:.3f}")

    (OUT / "luts.json").write_text(json.dumps(luts))
    print(f"\nLUT-ok mentve: {OUT}/luts.json ({len(luts)} görbe)")


if __name__ == "__main__":
    main()

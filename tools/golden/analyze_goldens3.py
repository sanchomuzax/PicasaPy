#!/usr/bin/env python3
"""Golden-elemzés 3. kör: autolight/autocolor/enhance modell, fill 2D LUT,
highlights/shadows/temp/sat sweep-ek, tint/ansel görbék.

Használat: analyze_goldens3.py <golden-kit3-result> <analysis_dir>
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

RESULT = Path(sys.argv[1])
AN = Path(sys.argv[2])
AN.mkdir(parents=True, exist_ok=True)


def band_of(path, y0=60, y1=540):
    img = cv2.imread(str(path))
    assert img is not None, path
    return img[y0:y1].astype(np.float64).mean(axis=0)  # (1600, BGR)


def gray_lut(folder, name, lo=0.0, hi=255.0):
    """LUT a (lo..hi) tartományú rámpából: bemenet-érték → kimenet (szürke)."""
    band = band_of(RESULT / "export" / folder / name).mean(axis=1)
    ins = lo + (hi - lo) * np.arange(1600) / 1599.0
    return ins, band


def main():
    print("=== 1) autolight — végpont-széthúzás vizsgálat ===")
    for name, lo, hi in (("ramp_030_200", 30, 200), ("ramp_060_160", 60, 160),
                         ("ramp_000_128", 0, 128), ("ramp_128_255", 128, 255)):
        ins, out = gray_lut("15-auto-limited", f"{name}__autolight.jpg", lo, hi)
        print(f"  {name}: ki({lo})={out[0]:6.1f}  ki({hi})={out[-1]:6.1f}  "
              f"ki(közép)={out[800]:6.1f}")

    print("\n=== 2) autolight színes öntetű rámpán (csatornánként v. együtt?) ===")
    for name in ("ramp_050_220_warmcast", "ramp_050_220_bluecast"):
        band = band_of(RESULT / "export/15-auto-limited" / f"{name}__autolight.jpg")
        base = band_of(RESULT / "export/00-base3" / f"{name}.jpg")
        d_lo = band[40] - base[40]
        d_hi = band[-40] - base[-40]
        print(f"  {name}: Δalj (B,G,R)=({d_lo[0]:+.1f},{d_lo[1]:+.1f},{d_lo[2]:+.1f})"
              f"  Δtető=({d_hi[0]:+.1f},{d_hi[1]:+.1f},{d_hi[2]:+.1f})")

    print("\n=== 3) autocolor a színes öntetű rámpákon ===")
    for name in ("ramp_050_220_warmcast", "ramp_050_220_bluecast"):
        band = band_of(RESULT / "export/15-auto-limited" / f"{name}__autocolor.jpg")
        base = band_of(RESULT / "export/00-base3" / f"{name}.jpg")
        mid_b, mid_e = base[800], band[800]
        print(f"  {name}: közép (B,G,R) {mid_b.round(1)} → {mid_e.round(1)}")

    print("\n=== 4) enhance ?= autolight (+valami) a korlátozott rámpákon ===")
    for name in ("ramp_030_200", "ramp_060_160", "ramp_050_220_warmcast"):
        al = band_of(RESULT / "export/15-auto-limited" / f"{name}__autolight.jpg")
        en = band_of(RESULT / "export/15-auto-limited" / f"{name}__enhance.jpg")
        print(f"  {name}: max|enhance−autolight| = {np.abs(en-al).max():.1f}  "
              f"átlag|Δ| = {np.abs(en-al).mean():.2f}")

    print("\n=== 5) fill 2D LUT építés + interpolációs hiba ===")
    fill2d = {}
    for s in np.arange(0.05, 1.001, 0.05):
        key = f"f{int(round(s*100)):03d}"
        ins, out = gray_lut("11-fill-sweep", f"chart_ramp__{key}.jpg")
        lut = np.interp(np.arange(256), ins, out)
        fill2d[round(float(s), 2)] = lut.tolist()
    keys = sorted(fill2d)
    worst = 0.0
    for i in range(1, len(keys) - 1):
        interp = (np.array(fill2d[keys[i-1]]) + np.array(fill2d[keys[i+1]])) / 2
        err = np.abs(interp - np.array(fill2d[keys[i]]))[8:250].max()
        worst = max(worst, err)
    print(f"  20 görbe mentve; szomszéd-interpoláció max hibája: {worst:.2f}/255")

    print("\n=== 6) highlights/shadows sweep (görbe-jelleg) ===")
    hs = {}
    for pre, vals in (("h", (10, 20, 30, 40, 60, 80)),
                      ("s", (10, 20, 30, 40, 60, 80))):
        for v in vals:
            ins, out = gray_lut("13-hs-sweep", f"chart_ramp__{pre}{v:03d}.jpg")
            lut = np.interp(np.arange(256), ins, out)
            hs[f"{pre}{v:03d}"] = lut.tolist()
            if v in (20, 40):
                print(f"  {pre}{v:03d}: ki(64)={lut[64]:6.1f} ki(128)={lut[128]:6.1f} "
                      f"ki(192)={lut[192]:6.1f}")

    print("\n=== 7) színhő sweep — csatorna-eltolások ===")
    temp = {}
    base_band = band_of(RESULT / "export/00-base3/chart_ramp.jpg")
    for v in ("tm100", "tm075", "tm050", "tm025", "tp025", "tp075", "tp100"):
        band = band_of(RESULT / "export/14-temp-sweep" / f"chart_ramp__{v}.jpg")
        d = (band - base_band)[400:1200].mean(axis=0)
        temp[v] = [float(x) for x in d]
        print(f"  {v}: ΔB={d[0]:+6.1f} ΔG={d[1]:+6.1f} ΔR={d[2]:+6.1f}")

    print("\n=== 8) tint / ansel csatornagörbék (szürke rámpán) ===")
    eff = {}
    for v in ("tint", "ansel", "glow1", "glow2", "vignette"):
        band = band_of(RESULT / "export/16-effects-ramp" / f"chart_ramp__{v}.jpg")
        eff[v] = band[::100].round(1).tolist()
        i = 800
        print(f"  {v}: közép (B,G,R) = {band[i].round(1)}")

    out = {"fill2d": fill2d, "hs": hs, "temp": temp}
    (AN / "luts3.json").write_text(json.dumps(out))
    print(f"\nMentve: {AN}/luts3.json")


if __name__ == "__main__":
    main()

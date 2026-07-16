#!/usr/bin/env python3
"""Golden-elemzés 4. kör: tilt-szemantika, unsharp-kernel, Vignette-maszk,
autocolor-csillapítás — a meglévő exportokból.

Használat: analyze_goldens4.py <kit1_result> <kit3_result>
"""
import sys
from pathlib import Path

import cv2
import numpy as np

K1 = Path(sys.argv[1])
K3 = Path(sys.argv[2])


def imread(p):
    img = cv2.imread(str(p))
    assert img is not None, p
    return img


def estimate_rot_scale(base, warped):
    """Elforgatás+skála becslés ORB feature-párosítással."""
    orb = cv2.ORB_create(3000)
    g1 = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    k1, d1 = orb.detectAndCompute(g1, None)
    k2, d2 = orb.detectAndCompute(g2, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    m = sorted(bf.match(d1, d2), key=lambda x: x.distance)[:400]
    src = np.float32([k1[x.queryIdx].pt for x in m])
    dst = np.float32([k2[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(src, dst, cv2.RANSAC,
                                         ransacReprojThreshold=2.0)
    angle = np.degrees(np.arctan2(M[1, 0], M[0, 0]))
    scale = float(np.hypot(M[0, 0], M[1, 0]))
    return angle, scale, int(inl.sum())


def main():
    print("=== 1) tilt szemantika (param → fok, autoskála) ===")
    base = imread(K1 / "00-base/photo01.jpg")
    for v, p in (("tiltm20", -0.2), ("tiltm05", -0.05),
                 ("tiltp05", 0.05), ("tiltp20", 0.2)):
        img = imread(K1 / "export/08-geom" / f"photo01__{v}.jpg")
        ang, sc, n = estimate_rot_scale(base, img)
        print(f"  param={p:+.2f} → szög={ang:+7.3f}°  skála={sc:.4f}  "
              f"(inlier: {n})  szög/param={ang/p:.2f}")

    print("\n=== 2) unsharp2 — él-profil elemzés (16px sakktábla éle) ===")
    base_d = imread(K1 / "00-base/chart_detail.jpg")
    gb = cv2.cvtColor(base_d, cv2.COLOR_BGR2GRAY).astype(float)
    # függőleges él keresése a 16px-es zónában (y=600..900): x=16k határok
    y = 750
    x_edge = 608  # 16*38 → fehér→fekete határ környéke
    for v in ("un1x1", "un2-030", "un2-060", "un2-100"):
        img = imread(K1 / "export/07-sharp" / f"chart_detail__{v}.jpg")
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(float)
        prof_b = gb[y - 40:y + 40, x_edge - 8:x_edge + 8].mean(axis=0)
        prof = g[y - 40:y + 40, x_edge - 8:x_edge + 8].mean(axis=0)
        over = (prof - prof_b)
        print(f"  {v}: túllövés max={over.max():+6.1f} min={over.min():+6.1f} "
              f"(profil Δ a ±8px sávban)")

    print("\n=== 3) Vignette maszk (kit3 rámpán, arány-kép) ===")
    base_r = imread(K3 / "export/00-base3/chart_ramp.jpg").astype(float)
    vin = imread(K3 / "export/16-effects-ramp/chart_ramp__vignette.jpg").astype(float)
    ratio = (vin.mean(axis=2) + 1) / (base_r.mean(axis=2) + 1)
    h, w = ratio.shape
    cy, cx = h // 2, w // 2
    print(f"  közép arány={ratio[cy, cx]:.3f}  sarok arány={ratio[20, 20]:.3f}")
    # radiális profil
    ys, xs = np.mgrid[0:h, 0:w]
    r = np.hypot((xs - cx) / w, (ys - cy) / h)
    for lo in (0.0, 0.2, 0.4, 0.6):
        m = (r >= lo) & (r < lo + 0.1)
        print(f"  r∈[{lo:.1f},{lo+0.1:.1f}): átlag arány={ratio[m].mean():.3f}")

    print("\n=== 4) autocolor csatorna-gain/offset a cast-rámpákon ===")
    for name in ("ramp_050_220_warmcast", "ramp_050_220_bluecast"):
        b0 = imread(K3 / f"export/00-base3/{name}.jpg").astype(float)
        b1 = imread(K3 / f"export/15-auto-limited/{name}__autocolor.jpg").astype(float)
        band0 = b0[60:540].mean(axis=0)
        band1 = b1[60:540].mean(axis=0)
        mask = (band1.max(axis=1) < 250) & (band1.min(axis=1) > 5)
        print(f"  {name}:")
        for ch, cname in ((2, "R"), ((1), "G"), (0, "B")):
            a, c = np.polyfit(band0[mask, ch], band1[mask, ch], 1)
            print(f"    {cname}: ki = {a:.4f}·be {c:+.2f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Golden kit 3. kör — sűrű sweep-ek + korlátozott tartományú rámpák.

Csak szintetikus chartok (kicsi, gyors export). Cél:
  - fill 2D LUT (20 lépéses s-sweep)
  - highlights/shadows/színhő/sat sweep-ek
  - enhance/autolight/autocolor modell (korlátozott tartományú rámpák)
  - effektek a szürke rámpán

Használat: make_golden_kit3.py <kit1_00base_dir> <kimenet_dir>
"""
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

BASE_IN = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def limited_ramp(lo, hi, tint=None):
    """Vízszintes rámpa lo..hi tartományban, opcionális színes öntettel."""
    img = np.zeros((600, 1600, 3), np.uint8)
    ramp = np.tile(np.linspace(lo, hi, 1600).astype(np.uint8), (600, 1))
    img[:] = ramp[..., None]
    if tint is not None:  # enyhe színeltolás az autocolor teszthez
        img = np.clip(img.astype(np.int16) + np.array(tint, np.int16),
                      0, 255).astype(np.uint8)
    return img


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    base_dir = OUT / "00-base3"
    base_dir.mkdir(parents=True)

    # korlátozott tartományú chartok (autolight-nak legyen mit széthúznia)
    charts = {
        "ramp_030_200.jpg": limited_ramp(30, 200),
        "ramp_060_160.jpg": limited_ramp(60, 160),
        "ramp_000_128.jpg": limited_ramp(0, 128),
        "ramp_128_255.jpg": limited_ramp(128, 255),
        "ramp_050_220_warmcast.jpg": limited_ramp(50, 220, tint=(0, 8, 22)),
        "ramp_050_220_bluecast.jpg": limited_ramp(50, 220, tint=(22, 8, 0)),
    }
    for name, img in charts.items():
        cv2.imwrite(str(base_dir / name), img, [cv2.IMWRITE_JPEG_QUALITY, 97])
    for src in ("chart_ramp.jpg", "chart_color.jpg"):
        shutil.copy2(BASE_IN / src, base_dir / src)

    folders = {}

    # 11: fill sűrű sweep (2D LUT-hoz)
    folders["11-fill-sweep"] = [
        ("chart_ramp.jpg", f"f{int(s*100):03d}", f"fill=1,{s:.6f};")
        for s in np.arange(0.05, 1.001, 0.05)
    ]
    # 12: sat sweep (negatív oldal is)
    folders["12-sat-sweep"] = [
        ("chart_color.jpg", f"s{'m' if v<0 else 'p'}{int(abs(v)*100):03d}",
         f"sat=1,{v:.6f};")
        for v in (-1.0, -0.75, -0.5, -0.25, -0.1, 0.1, 0.375, 0.625, 0.875)
    ]
    # 13: highlights + shadows sweep
    folders["13-hs-sweep"] = (
        [("chart_ramp.jpg", f"h{int(v*100):03d}",
          f"finetune2=1,0.000000,{v:.6f},0.000000,00000000,0.000000;")
         for v in (0.1, 0.2, 0.3, 0.4, 0.6, 0.8)]
        + [("chart_ramp.jpg", f"s{int(v*100):03d}",
            f"finetune2=1,0.000000,0.000000,{v:.6f},00000000,0.000000;")
           for v in (0.1, 0.2, 0.3, 0.4, 0.6, 0.8)]
    )
    # 14: színhő sweep (gray + színes charton)
    temps = (-1.0, -0.75, -0.5, -0.25, 0.25, 0.75, 1.0)
    folders["14-temp-sweep"] = (
        [("chart_ramp.jpg", f"t{'m' if v<0 else 'p'}{int(abs(v)*100):03d}",
          f"finetune2=1,0.000000,0.000000,0.000000,00000000,{v:.6f};")
         for v in temps]
        + [("chart_color.jpg", f"tc{'m' if v<0 else 'p'}{int(abs(v)*100):03d}",
            f"finetune2=1,0.000000,0.000000,0.000000,00000000,{v:.6f};")
           for v in (-0.5, 0.5)]
    )
    # 15: automaták a korlátozott rámpákon
    folders["15-auto-limited"] = [
        (chart, v, f"{v}=1;")
        for chart in charts
        for v in ("enhance", "autolight", "autocolor")
    ]
    # 16: effektek a szürke rámpán (1. körből hiányoztak innen)
    folders["16-effects-ramp"] = [
        ("chart_ramp.jpg", "tint", "tint=1,79.842102,ffff;"),
        ("chart_ramp.jpg", "ansel", "ansel=1,ffffffff;"),
        ("chart_ramp.jpg", "glow1", "glow=1,0.432749,2.469705;"),
        ("chart_ramp.jpg", "glow2", "glow2=1,0.650000,3.000000;"),
        ("chart_ramp.jpg", "vignette",
         "Vignette=1,35.000000,1.400000,0.000000,00000000;"),
        ("chart_ramp.jpg", "radblur",
         "radblur=1,0.500000,0.500000,0.300000,0.500000;"),
        ("chart_ramp.jpg", "dirtint",
         "dir_tint=1,0.500000,0.500000,0.250000,0.250000,ffffffff;"),
    ]

    total = 0
    for folder, items in folders.items():
        fdir = OUT / folder
        fdir.mkdir()
        ini = []
        for base_name, suffix, chain in items:
            name = f"{Path(base_name).stem}__{suffix}.jpg"
            shutil.copy2(base_dir / base_name, fdir / name)
            extra = ""
            if "crop64=1," in chain:
                rect = chain.split("crop64=1,")[1].split(";")[0]
                extra = f"crop=rect64({rect})\n"
            ini.append(f"[{name}]\n{extra}filters={chain}\n")
            total += 1
        (fdir / ".picasa.ini").write_text("\n".join(ini), encoding="utf-8")

    (OUT / "export").mkdir()
    (OUT / "OLVASS-EL.txt").write_text(
        "GOLDEN KIT 3. KÖR — ugyanaz a menet, mint korábban:\n"
        "1. Másold a golden-kit3 mappát a Windows-gépre.\n"
        "2. Picasa Folder Manager -> add hozzá (Scan Once).\n"
        "3. Mappánként (11..16): Ctrl+A -> Export\n"
        "   (Use Original Size, Maximum) a golden-kit3\\export alá.\n"
        "   A 00-base3 mappát NEM kell exportálni.\n"
        "4. Vissza a Pi-re: research/testdata/golden-kit3-result\n",
        encoding="utf-8")
    print(f"Kit3 kész: {OUT} — {len(folders)} mappa, {total} tesztkép")


if __name__ == "__main__":
    main()

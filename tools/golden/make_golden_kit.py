#!/usr/bin/env python3
"""Golden kit generátor — research-plan #2 (pixelhű szűrő-validálás).

Előre megírt .picasa.ini fájlokkal ellátott tesztmappákat készít. A Windows-os
Picasa 3.9 beolvassa a szűrő-láncokat, a felhasználó exportálja a renderelt
képeket ("golden" referenciák), amelyekhez a PicasaPy szűrő-implementációját
illesztjük (SSIM/dE elfogadási teszt).

Használat: make_golden_kit.py <fotok_dir> <kimenet_dir>
"""
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------- szűrők
F = {
    # 01: tartalom-adaptív automaták — minden alapképre
    "01-auto": [
        ("enhance", "enhance=1;"),
        ("autolight", "autolight=1;"),
        ("autocolor", "autocolor=1;"),
    ],
    # 02: fill light sweep
    "02-fill": [
        (f"fill{int(v*100):03d}", f"fill=1,{v:.6f};")
        for v in (0.25, 0.50, 0.75, 1.00)
    ],
    # 03: finetune2 — paraméterenkénti sweep (5. param ismeretlen → azonosítás)
    "03-finetune2": [
        ("b025", "finetune2=1,0.250000,0.000000,0.000000,00000000,0.000000;"),
        ("b050", "finetune2=1,0.500000,0.000000,0.000000,00000000,0.000000;"),
        ("b100", "finetune2=1,1.000000,0.000000,0.000000,00000000,0.000000;"),
        ("h050", "finetune2=1,0.000000,0.500000,0.000000,00000000,0.000000;"),
        ("h100", "finetune2=1,0.000000,1.000000,0.000000,00000000,0.000000;"),
        ("s050", "finetune2=1,0.000000,0.000000,0.500000,00000000,0.000000;"),
        ("s100", "finetune2=1,0.000000,0.000000,1.000000,00000000,0.000000;"),
        ("tempA", "finetune2=1,0.000000,0.000000,0.000000,fff7f5f3,0.000000;"),
        ("tempB", "finetune2=1,0.000000,0.000000,0.000000,ffccc6b2,0.000000;"),
        ("u-05", "finetune2=1,0.000000,0.000000,0.000000,00000000,-0.500000;"),
        ("u+05", "finetune2=1,0.000000,0.000000,0.000000,00000000,0.500000;"),
        ("u+10", "finetune2=1,0.000000,0.000000,0.000000,00000000,1.000000;"),
    ],
    # 04: finetune v1 (a régi változat — a valódi könyvtárban 459x fordul elő)
    "04-finetune1": [
        ("b050", "finetune=1,0.500000,0.000000,0.000000,00000000,0.000000;"),
        ("u+05", "finetune=1,0.000000,0.000000,0.000000,00000000,0.500000;"),
        ("u-05", "finetune=1,0.000000,0.000000,0.000000,00000000,-0.500000;"),
    ],
    # 05: fix tónusszűrők
    "05-tone": [
        ("bw", "bw=1;"),
        ("sepia", "sepia=1;"),
        ("warm", "warm=1;"),
        ("grain2", "grain2=1;"),
    ],
    # 06: telítettség (negatív érték élesben igazolt!)
    "06-sat": [
        (f"sat{'m' if v < 0 else 'p'}{int(abs(v)*100):03d}", f"sat=1,{v:.6f};")
        for v in (-0.333333, 0.250000, 0.500000, 1.000000)
    ],
    # 07: élesítés (v1 paraméter nélkül + v2 sweep)
    "07-sharp": [
        ("un1x1", "unsharp=1;"),
        ("un1x3", "unsharp=1;unsharp=1;unsharp=1;"),
        ("un2-030", "unsharp2=1,0.300000;"),
        ("un2-060", "unsharp2=1,0.600000;"),
        ("un2-100", "unsharp2=1,1.000000;"),
    ],
    # 08: geometria — tilt és crop
    "08-geom": [
        ("tiltm20", "tilt=1,-0.200000,0.000000;"),
        ("tiltm05", "tilt=1,-0.050000,0.000000;"),
        ("tiltp05", "tilt=1,0.050000,0.000000;"),
        ("tiltp20", "tilt=1,0.200000,0.000000;"),
        # 0.1,0.1,0.9,0.9
        ("cropsym", "crop64=1,19991999e666e666;"),
        # 0.25,0.25,0.75,0.75
        ("cropmid", "crop64=1,40004000c000c000;"),
        # aszimmetrikus: 0.05,0.2,0.6,0.95
        ("cropasy", "crop64=1,0ccd333399997333;"),
    ],
    # 09: effektek — paraméterek a valódi könyvtárból kinyert értékekkel
    "09-effects": [
        ("glow1", "glow=1,0.432749,2.469705;"),
        ("glow2", "glow2=1,0.650000,3.000000;"),
        ("vignette", "Vignette=1,35.000000,1.400000,0.000000,00000000;"),
        ("radblur", "radblur=1,0.411585,0.611111,0.000000,0.000000;"),
        ("dirtint", "dir_tint=1,0.432422,0.554167,0.250000,0.250000,ffffffff;"),
        ("tint", "tint=1,79.842102,ffff;"),
        ("ansel", "ansel=1,ffffffff;"),
    ],
    # 10: valódi komplex láncok a felhasználó könyvtárából (sorrend-teszt)
    "10-real-chains": [
        ("chainA", "enhance=1;fill=1,0.308411;finetune2=1,0.000000,0.000000,"
                   "0.000000,00000000,0.309942;tilt=1,-0.114659,0.000000;"),
        ("chainB", "crop64=1,30c00155dd7ffae3;fill=1,0.336449;finetune2=1,"
                   "0.000000,0.000000,0.067368,00000000,0.000000;"
                   "Vignette=1,35.000000,1.400000,0.000000,00000000;"),
        ("chainC", "warm=1;sat=1,0.824561;finetune=1,0.228070,0.103860,"
                   "0.000000,00000000,0.000000;tilt=1,0.154150,0.000000;"),
        ("chainD", "fill=1,0.579439;autolight=1;crop64=1,46060f47ab28d291;"
                   "finetune2=1,0.000000,0.000000,0.000000,ffccc6b2,0.000000;"
                   "finetune2=1,0.315789,0.000000,0.050526,00000000,0.000000;"),
        ("chainE", "tilt=1,0.122530,0.000000;crop64=1,1e3308cdb932ffff;"
                   "enhance=1;sepia=1;autolight=1;Vignette=1,35.000000,"
                   "1.400000,0.000000,00000000;"),
    ],
}

# mely mappa mely alapkép-osztályt kapja (chart = szintetikus, photo = valódi)
BASES = {
    "01-auto": ("charts", "photos"),       # tartalom-adaptív → minden
    "02-fill": ("charts", "photos2"),
    "03-finetune2": ("charts", "photos2"),
    "04-finetune1": ("charts",),
    "05-tone": ("charts", "photos2"),
    "06-sat": ("charts", "photos2"),
    "07-sharp": ("chart_detail", "photos2"),
    "08-geom": ("chart_detail", "photos2"),
    "09-effects": ("chart_color", "photos2"),
    "10-real-chains": ("charts", "photos2"),
}


# ---------------------------------------------------------------- chartok
def make_charts(out: Path):
    """Szintetikus tesztképek a tónusgörbék pontos visszafejtéséhez."""
    charts = {}

    # 1) ramp: vízszintes 0..255 szürke átmenet + 16 lépcső + RGB rámpák
    img = np.zeros((1200, 1600, 3), np.uint8)
    ramp = np.tile(np.linspace(0, 255, 1600, dtype=np.uint8), (300, 1))
    img[0:300] = ramp[..., None]
    steps = np.repeat(np.linspace(0, 255, 16, dtype=np.uint8), 100)[:1600]
    img[300:600] = np.tile(steps, (300, 1))[..., None]
    for i, ch in enumerate((0, 1, 2)):  # B, G, R rámpa
        band = np.zeros((200, 1600, 3), np.uint8)
        band[..., ch] = np.tile(np.linspace(0, 255, 1600, dtype=np.uint8),
                                (200, 1))
        img[600 + i * 200:800 + i * 200] = band
    charts["chart_ramp.jpg"] = img

    # 2) color: HSV mező + telítettség-rács + bőrtónus-minták
    hsv = np.zeros((600, 1600, 3), np.uint8)
    hsv[..., 0] = np.tile(np.linspace(0, 179, 1600, dtype=np.uint8), (600, 1))
    hsv[..., 1] = np.repeat(np.linspace(50, 255, 600, dtype=np.uint8),
                            1600).reshape(600, 1600)
    hsv[..., 2] = 220
    top = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    skin = np.zeros((600, 1600, 3), np.uint8)
    tones = [(198, 222, 245), (160, 195, 233), (117, 160, 214),
             (74, 112, 165), (47, 74, 116), (32, 47, 74)]
    w = 1600 // len(tones)
    for i, c in enumerate(tones):
        skin[:, i * w:(i + 1) * w] = c
    charts["chart_color.jpg"] = np.vstack([top, skin])

    # 3) detail: sakktáblák + vonalpárok (élesítés/geometria)
    img = np.full((1200, 1600, 3), 255, np.uint8)
    for size, y0 in ((4, 0), (8, 300), (16, 600)):
        for y in range(y0, y0 + 300, size):
            for x in range(0, 1600, size):
                if ((x // size) + (y // size)) % 2 == 0:
                    img[y:y + size, x:x + size] = 0
    for i, x in enumerate(range(0, 1600, 4)):  # sűrűsödő vonalpárok
        if (x // 4) % 2 == 0:
            img[900:1200, x:x + 2] = 0
    charts["chart_detail.jpg"] = img

    paths = {}
    for name, im in charts.items():
        p = out / name
        cv2.imwrite(str(p), im, [cv2.IMWRITE_JPEG_QUALITY, 97])
        paths[name] = p
    return paths


def pick_photos(photos_dir: Path, n=6):
    """Fényerő szerint szórt, változatos valódi fotók kiválasztása."""
    files = sorted(photos_dir.rglob("*.jp*g"))
    scored = []
    for f in files[:: max(1, len(files) // 120)]:
        img = cv2.imread(str(f), cv2.IMREAD_REDUCED_GRAYSCALE_8)
        if img is None:
            continue
        scored.append((float(img.mean()), f))
    scored.sort()
    idx = np.linspace(0, len(scored) - 1, n).astype(int)
    return [scored[i][1] for i in idx]


def main():
    photos_dir = Path(sys.argv[1]).expanduser()
    out = Path(sys.argv[2]).expanduser()
    if out.exists():
        shutil.rmtree(out)
    base_dir = out / "00-base"
    base_dir.mkdir(parents=True)

    chart_paths = make_charts(base_dir)
    photos = pick_photos(photos_dir)
    for i, p in enumerate(photos):
        shutil.copy2(p, base_dir / f"photo{i:02d}.jpg")

    base_sets = {
        "charts": sorted(base_dir.glob("chart_*.jpg")),
        "chart_detail": [base_dir / "chart_detail.jpg"],
        "chart_color": [base_dir / "chart_color.jpg"],
        "photos": sorted(base_dir.glob("photo*.jpg")),
        "photos2": [base_dir / "photo01.jpg", base_dir / "photo04.jpg"],
    }

    total = 0
    for folder, variants in F.items():
        fdir = out / folder
        fdir.mkdir()
        ini = []
        bases = [b for key in BASES[folder] for b in base_sets[key]]
        for base in bases:
            for suffix, chain in variants:
                name = f"{base.stem}__{suffix}.jpg"
                shutil.copy2(base, fdir / name)
                ini.append(f"[{name}]\nfilters={chain}\n")
                total += 1
        (fdir / ".picasa.ini").write_text("\n".join(ini), encoding="utf-8")

    (out / "export").mkdir()
    n_variants = sum(len(v) for v in F.values())
    print(f"Kit kész: {out}")
    print(f"  {len(chart_paths)} chart + {len(photos)} fotó alapkép")
    print(f"  {len(F)} mappa, {n_variants} szűrő-variáns, {total} tesztkép")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Képfeldolgozó lib benchmark — research-plan #3 (RPi5).

Mérések libenként (Pillow / pyvips / OpenCV):
  1. JPEG dekód + 256px thumbnail + JPEG enkód (a Picasa-scanner fő terhelése)
  2. JPEG dekód + 1600px "nézőkép" méretezés (viewer-útvonal)

Egy- és többszálú (4 worker) futás, két képosztályon (1080p valódi, 12MP szint.).
CSAK OLVASSA a forrásképeket; kimenet a scratch tmp-be megy és törlődik.
"""
import io
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RESULTS = {}
THUMB = 256
VIEW = 1600


def timed(fn, files, workers):
    t0 = time.perf_counter()
    if workers == 1:
        for f in files:
            fn(f)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(fn, files))
    dt = time.perf_counter() - t0
    return len(files) / dt  # kép/sec


# ---------------- Pillow ----------------
def pillow_thumb(path):
    from PIL import Image
    with Image.open(path) as im:
        im.draft("RGB", (THUMB, THUMB))  # JPEG gyors-dekód alacsony felbontásra
        im.thumbnail((THUMB, THUMB))
        buf = io.BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=85)


def pillow_view(path):
    from PIL import Image
    with Image.open(path) as im:
        im.draft("RGB", (VIEW, VIEW))
        im.thumbnail((VIEW, VIEW))
        im.convert("RGB").load()


# ---------------- pyvips ----------------
def vips_thumb(path):
    import pyvips
    im = pyvips.Image.thumbnail(str(path), THUMB)  # shrink-on-load
    im.jpegsave_buffer(Q=85)


def vips_view(path):
    import pyvips
    im = pyvips.Image.thumbnail(str(path), VIEW)
    im.write_to_memory()


# ---------------- OpenCV ----------------
def cv_thumb(path):
    import cv2
    img = cv2.imread(str(path), cv2.IMREAD_REDUCED_COLOR_8)  # 1/8 dekód
    h, w = img.shape[:2]
    scale = THUMB / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_AREA)
    cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])


def cv_view(path):
    import cv2
    img = cv2.imread(str(path), cv2.IMREAD_REDUCED_COLOR_2)
    h, w = img.shape[:2]
    scale = VIEW / max(h, w)
    if scale < 1:
        cv2.resize(img, (int(w * scale), int(h * scale)),
                   interpolation=cv2.INTER_AREA)


LIBS = {
    "Pillow": (pillow_thumb, pillow_view),
    "pyvips": (vips_thumb, vips_view),
    "OpenCV": (cv_thumb, cv_view),
}


def versions():
    out = {}
    import PIL
    out["Pillow"] = PIL.__version__
    import pyvips
    out["pyvips"] = f"{pyvips.__version__} (libvips {pyvips.version(0)}.{pyvips.version(1)})"
    import cv2
    out["OpenCV"] = cv2.__version__
    return out


def main(sets):
    print("verziók:", json.dumps(versions(), indent=None))
    for set_name, files in sets.items():
        print(f"\n### {set_name} ({len(files)} kép) ###")
        for lib, (thumb_fn, view_fn) in LIBS.items():
            for task_name, fn in (("thumb256+enc", thumb_fn), ("view1600", view_fn)):
                r1 = timed(fn, files, 1)
                r4 = timed(fn, files, 4)
                key = f"{set_name}/{lib}/{task_name}"
                RESULTS[key] = (round(r1, 2), round(r4, 2))
                print(f"  {lib:<7} {task_name:<14} 1 szál: {r1:6.2f} kép/s   "
                      f"4 szál: {r4:6.2f} kép/s")
    print("\nJSON:", json.dumps(RESULTS))


if __name__ == "__main__":
    real_dir = Path(sys.argv[1])
    synth_dir = Path(sys.argv[2])
    real = sorted(real_dir.glob("*.jp*g"))[:100]
    synth = sorted(synth_dir.glob("*.jpg"))[:40]
    assert real and synth, "hiányzó tesztkészlet"
    main({"1080p-valodi": real, "12MP-szint": synth})

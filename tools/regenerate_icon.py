"""Ikon-újragenerálás (#267): kitöltő PNG/ICO előállítása a forrásból.

A HIBA, amit ez a szkript javít: a `src/picasapy/app/assets/icon.png` (és az
ebből legyártott `icon.ico`) körül vastag, átlátszó margó volt, ezért a
Windows Start menüben / Asztalon a PicasaPy-ikon láthatóan kisebbnek tűnt,
mint az eredeti Picasa 3 ikon (ami majdnem kitölti a négyzetet).

MIT CSINÁL a szkript:
1. Beolvassa a FORRÁS képet (`tools/icon/icon_source.png`).
2. Levágja a forrás átlátszó keretét (alpha-csatorna bounding boxára).
3. A rajzolatot felskálázza úgy, hogy a hosszabb oldala a célvászon
   ``FILL_RATIO`` hányadát töltse ki (a képarány megmarad, a rövidebb
   tengelyen a rajzolat középre kerül).
4. Az eredményt középre igazítva egy új, teljesen átlátszó, négyzetes
   vászonra másolja.
5. Elmenti a `src/picasapy/app/assets/icon.png` fájlba, és ugyanebből az
   eredményből legyártja az `icon.ico`-t a szokásos méretváltozatokkal.

FORRÁSRÓL: jelenleg nincs külön nagyfelbontású SVG/vektoros forrásunk a
pinwheel-logóhoz (a `logo.svg` egy másik, szöveges/nagyobb arculati elem,
nem ez a kerek ikon). Ezért a forrás a #267 javítás ELŐTTI, margós
`icon.png` egy változatlan másolata, amit a
`tools/icon/icon_source.png` alatt őrzünk meg — ebből a szkript
ismételten, veszteségmentesen (a forrás sosem íródik felül) újra
legenerálhatja a kitöltő változatot. Ha a jövőben lesz dedikált
vektoros/nagyfelbontású forrás, a `SOURCE_PATH`-ot arra kell átállítani.

Használat:
    python3 tools/regenerate_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

# -- útvonalak --------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = _REPO_ROOT / "tools" / "icon" / "icon_source.png"
ASSETS_DIR = _REPO_ROOT / "src" / "picasapy" / "app" / "assets"
OUTPUT_PNG = ASSETS_DIR / "icon.png"
OUTPUT_ICO = ASSETS_DIR / "icon.ico"

# -- paraméterek --------------------------------------------------------------
CANVAS_SIZE = 256  # a kimeneti négyzet-vászon mérete pixelben
FILL_RATIO = 0.94  # a rajzolat ennyi hányadát töltse ki a vászon hosszabb oldalának
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def fit_content_to_canvas(
    source: Image.Image, canvas_size: int, fill_ratio: float
) -> Image.Image:
    """Levágja a forrás átlátszó margóját, majd a rajzolatot a megadott
    kitöltési arányra skálázza, középre igazítva egy új, átlátszó
    ``canvas_size`` x ``canvas_size`` méretű vásznon.

    A képarány megmarad: a rajzolat hosszabb oldala illeszkedik a célértékre,
    a rövidebb tengelyen a tartalom középre kerül.
    """
    rgba = source.convert("RGBA")
    bbox = rgba.getbbox()
    if bbox is None:
        raise ValueError("A forráskép teljesen átlátszó, nincs mit kitölteni.")

    cropped = rgba.crop(bbox)
    content_w, content_h = cropped.size

    target_long_side = round(canvas_size * fill_ratio)
    scale = target_long_side / max(content_w, content_h)
    new_w = max(1, round(content_w * scale))
    new_h = max(1, round(content_h * scale))
    resized = cropped.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    offset_x = (canvas_size - new_w) // 2
    offset_y = (canvas_size - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas


def main() -> None:
    """Beolvassa a forrást, előállítja a kitöltő PNG-t és ICO-t, majd kiírja
    az eredmény-fájlokat a helyükre."""
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"Nem található a forráskép: {SOURCE_PATH}. "
            "Ld. a szkript docstringjét a forrás eredetéről."
        )

    source = Image.open(SOURCE_PATH)
    result = fit_content_to_canvas(source, CANVAS_SIZE, FILL_RATIO)

    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    result.save(OUTPUT_PNG)
    result.save(OUTPUT_ICO, sizes=ICO_SIZES)

    print(
        f"Kész: {OUTPUT_PNG.relative_to(_REPO_ROOT)} és "
        f"{OUTPUT_ICO.relative_to(_REPO_ROOT)} frissítve "
        f"({CANVAS_SIZE}x{CANVAS_SIZE}, kitöltés {FILL_RATIO:.0%})."
    )


if __name__ == "__main__":
    main()

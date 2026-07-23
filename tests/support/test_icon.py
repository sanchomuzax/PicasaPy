"""Alkalmazás-ikon regressziós teszt (#267): az `icon.png` és `icon.ico`
rajzolata a vászon (legalább) ~90%-át töltse ki mindkét tengelyen.

A bug (#267) előtt a rajzolat körül vastag, átlátszó margó volt (~88%-os
kitöltés), emiatt a PicasaPy-ikon a Windows Start menüben/Asztalon látha-
tóan kisebbnek tűnt, mint az eredeti Picasa 3 ikon. Ez a teszt a levágott/
újraskálázott állapotot rögzíti védőhálóként: a régi, margós képen ez a
teszt BUKOTT volna (0.883 < 0.90).
"""

from pathlib import Path

from PIL import Image

_ASSETS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "picasapy"
    / "app"
    / "assets"
)
_ICON_PNG = _ASSETS_DIR / "icon.png"
_ICON_ICO = _ASSETS_DIR / "icon.ico"

_MIN_FILL_RATIO = 0.90


def _fill_ratio(image: Image.Image) -> tuple[float, float]:
    """Visszaadja az alpha-csatorna szerinti nem-átlátszó tartalom bounding
    boxának szélesség- és magasság-kitöltési arányát a teljes vászonhoz
    képest."""
    rgba = image.convert("RGBA")
    bbox = rgba.getbbox()
    assert bbox is not None, "A kép teljesen átlátszó, nincs tartalom."
    width, height = rgba.size
    x0, y0, x1, y1 = bbox
    return (x1 - x0) / width, (y1 - y0) / height


class TestIconPng:
    def test_icon_png_exists(self):
        assert _ICON_PNG.is_file()

    def test_icon_png_is_square(self):
        with Image.open(_ICON_PNG) as im:
            assert im.size[0] == im.size[1]

    def test_icon_png_content_fills_canvas(self):
        with Image.open(_ICON_PNG) as im:
            fill_w, fill_h = _fill_ratio(im)
        assert fill_w >= _MIN_FILL_RATIO, (
            f"A rajzolat vízszintes kitöltése ({fill_w:.3f}) "
            f"kisebb, mint az elvárt {_MIN_FILL_RATIO}."
        )
        assert fill_h >= _MIN_FILL_RATIO, (
            f"A rajzolat függőleges kitöltése ({fill_h:.3f}) "
            f"kisebb, mint az elvárt {_MIN_FILL_RATIO}."
        )


class TestIconIco:
    def test_icon_ico_exists(self):
        assert _ICON_ICO.is_file()

    def test_icon_ico_contains_256px_variant(self):
        with Image.open(_ICON_ICO) as ico:
            sizes = ico.info.get("sizes", set())
        assert (256, 256) in sizes

    def test_icon_ico_256px_content_fills_canvas(self):
        with Image.open(_ICON_ICO) as ico:
            ico.size = (256, 256)
            fill_w, fill_h = _fill_ratio(ico)
        assert fill_w >= _MIN_FILL_RATIO, (
            f"Az ICO 256px változatának vízszintes kitöltése ({fill_w:.3f}) "
            f"kisebb, mint az elvárt {_MIN_FILL_RATIO}."
        )
        assert fill_h >= _MIN_FILL_RATIO, (
            f"Az ICO 256px változatának függőleges kitöltése ({fill_h:.3f}) "
            f"kisebb, mint az elvárt {_MIN_FILL_RATIO}."
        )

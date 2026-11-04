"""Sanity checks for the generated application icon assets.

The exact per-size geometry is checked by ``test_icon_geometry_6514.py``.
These checks retain a broad fill guard around the measured 226 px circle.
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

_MIN_FILL_RATIO = 0.87
_MIN_AREA_RATIO = 0.60


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


def _area_ratio(image: Image.Image) -> float:
    """Visszaadja a nem-átlátszó (alpha > 0) pixelek arányát a teljes
    vászon pixelszámához képest, ez a tényleges, a felhasználó szeme
    által érzékelt optikai kitöltés, szemben a bbox-alapú (alak-vak)
    metrikával (#325)."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    histogram = alpha.histogram()  # 256 elemű lista: hányszor fordul elő az adott alpha-érték
    nonzero = sum(histogram[1:])  # minden alpha > 0 érték előfordulásainak összege
    return nonzero / (width * height)


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

    def test_icon_png_content_area_fills_canvas(self):
        """Keep a broad area sanity check for the measured circular frame."""
        with Image.open(_ICON_PNG) as im:
            area = _area_ratio(im)
        assert area >= _MIN_AREA_RATIO, (
            f"Az icon.png tényleges (nem-átlátszó) pixel-területe ({area:.3f}) "
            f"kisebb, mint az elvárt {_MIN_AREA_RATIO}; a logó optikailag "
            "kisebb a 256 px-es mért kör körüli sanity küszöbnél."
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

    def test_icon_ico_256px_content_area_fills_canvas(self):
        """Keep the area sanity check on the ICO's 256 px frame."""
        with Image.open(_ICON_ICO) as ico:
            ico.size = (256, 256)
            area = _area_ratio(ico)
        assert area >= _MIN_AREA_RATIO, (
            f"Az ICO 256px változatának tényleges pixel-területe ({area:.3f}) "
            f"kisebb, mint az elvárt {_MIN_AREA_RATIO} (#325)."
        )

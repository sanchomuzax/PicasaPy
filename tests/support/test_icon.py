"""Alkalmazás-ikon regressziós teszt (#267, #325): a generált ikonok
rajzolata a lehető legnagyobb mértékben töltse ki a négyzetes vászont.

#267 (RÉGI JAVÍTÁS) csak a bounding-box (átlátszó margó) kitöltési arányát
mérte. #325 kiderítette, hogy ez ÁLPOZITÍV (false-green) metrika volt: a
rajzolat maga egy KÖR (fehér korong + pinwheel), aminek a területe a
befoglaló négyzetének csak kb. 78,5%-a (π/4) — így a bbox akár 90%+-os
kitöltése mellett is a ténylegesen kirajzolt (nem-átlátszó) PIXELEK
aránya a teljes vászonhoz képest jóval alacsonyabb maradhat, és ez az,
amit a felhasználó szeme ténylegesen érzékel (optikai méret). A #267
előtti, margós képen ez kb. 0,469 volt; a #267 utáni, de #325 előtti
(FILL_RATIO=0.94) képen kb. 0,668 — ami a bbox-tesztet zölden tartotta,
miközben a felhasználói panasz (#325) szerint a logó továbbra is
kisebbnek látszott, mint az eredeti Picasa ikonja.

Ez a teszt ezért a TÉNYLEGES (nem-átlátszó) pixel-terület arányát méri a
kimeneti PNG/ICO fájlokon — nem a forrás-SVG-n/PNG-n, és nem csak a
bbox-on —, a MEMORY 2026-07-22-i „mérd a futásidejű kimenetet, ne a
tünetet" szabálya szerint. A régi (FILL_RATIO=0.94) állapoton ez a teszt
BUKOTT volna (0.668 < 0.72).
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

_MIN_FILL_RATIO = 0.90  # bbox-kitöltés (a régi #267-es metrika, sanity-ként megtartva)
_MIN_AREA_RATIO = 0.72  # #325: tényleges (nem-átlátszó) pixel-terület a teljes vásznon


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
    vászon pixelszámához képest — ez a tényleges, a felhasználó szeme
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
        """#325: a bbox mellett a TÉNYLEGES kitöltött pixel-terület is
        érje el a küszöböt — enélkül egy kör alakú rajzolat a bbox-tesztet
        megkerülve is optikailag kicsinek látszódhat."""
        with Image.open(_ICON_PNG) as im:
            area = _area_ratio(im)
        assert area >= _MIN_AREA_RATIO, (
            f"Az icon.png tényleges (nem-átlátszó) pixel-területe ({area:.3f}) "
            f"kisebb, mint az elvárt {_MIN_AREA_RATIO} — a logó optikailag "
            "kisebbnek tűnhet az eredeti Picasa-ikonnál (#325)."
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
        """#325: ugyanaz a terület-alapú védőháló az ICO 256px változatán."""
        with Image.open(_ICON_ICO) as ico:
            ico.size = (256, 256)
            area = _area_ratio(ico)
        assert area >= _MIN_AREA_RATIO, (
            f"Az ICO 256px változatának tényleges pixel-területe ({area:.3f}) "
            f"kisebb, mint az elvárt {_MIN_AREA_RATIO} (#325)."
        )

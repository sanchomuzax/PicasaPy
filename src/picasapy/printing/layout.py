"""Nyomtatás-elrendezés geometriája — Qt-független, determinisztikus.

A `picasapy.app.print_controller.PrintController` ezt hívja: az oldal
nyomtatható területét (`PageGeometry`, a nyomtató tényleges felbontásában/
mértékegységében) és a kép pixelméretét adja meg, a visszakapott
`ImagePlacement` pedig a kép rajzolási téglalapja UGYANABBAN a
mértékegységben, az oldal bal felső sarkától mérve. A tájolás (portré/
fekvő) a nyomtatandó képhez `resolve_orientation`-nel dől el, MIELŐTT a
hívó beállítja a `QPrinter` tájolását és lekéri a `PageGeometry`-t — ez a
modul már a végleges (tájolt) oldalterülettel dolgozik, nem forgat."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PrintFitMode(str, Enum):
    """Hogyan simuljon a kép a margón belüli területhez."""

    #: a teljes kép látszik — a rövidebb irányban üres sáv (letterbox) maradhat
    FIT = "fit"
    #: a terület teljesen kitöltve — a kép hosszabbik iránya levágódik
    FILL = "fill"


class PrintOrientation(str, Enum):
    """A nyomtatandó oldal tájolása."""

    #: a kép arányához igazodik (fekvő kép → fekvő oldal, egyébként portré)
    AUTO = "auto"
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass(frozen=True)
class PageGeometry:
    """Az oldal (már a végleges tájolásban mért) mérete + margója —
    bármely mértékegységben, amíg a hívó következetes (a `print_controller`
    eszközponttal — `QPrinter.resolution()` szerinti pixelt — használ)."""

    width: float
    height: float
    margin: float = 0.0

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Érvénytelen oldalméret: {self.width}x{self.height}")
        if self.margin < 0:
            raise ValueError(f"Érvénytelen margó: {self.margin}")
        if self.margin * 2 >= self.width or self.margin * 2 >= self.height:
            raise ValueError("A margó nem lehet nagyobb-egyenlő az oldal felénél")

    @property
    def printable_width(self) -> float:
        return self.width - 2 * self.margin

    @property
    def printable_height(self) -> float:
        return self.height - 2 * self.margin


@dataclass(frozen=True)
class ImagePlacement:
    """A kép rajzolási téglalapja az oldal bal felső sarkától mérve (nem a
    margón belüli terület sarkától!) — `FILL` módban a téglalap
    szélesebb/magasabb lehet a margón belüli területnél (a hívó painter a
    lapszélen úgyis levágja)."""

    x: float
    y: float
    width: float
    height: float


def resolve_orientation(
    image_width: int, image_height: int, orientation: PrintOrientation
) -> PrintOrientation:
    """`AUTO` esetén a kép arányához illő tájolást adja (fekvő kép → fekvő
    oldal, négyzetes/álló kép → portré); explicit kérésnél változatlanul
    visszaadja azt. Sosem ad `AUTO`-t vissza."""
    if image_width <= 0 or image_height <= 0:
        raise ValueError(f"Érvénytelen képméret: {image_width}x{image_height}")
    if orientation == PrintOrientation.PORTRAIT:
        return PrintOrientation.PORTRAIT
    if orientation == PrintOrientation.LANDSCAPE:
        return PrintOrientation.LANDSCAPE
    if orientation != PrintOrientation.AUTO:
        raise ValueError(f"Ismeretlen tájolás: {orientation!r}")
    return (
        PrintOrientation.LANDSCAPE
        if image_width > image_height
        else PrintOrientation.PORTRAIT
    )


def compute_print_layout(
    page: PageGeometry,
    image_width: int,
    image_height: int,
    fit_mode: PrintFitMode = PrintFitMode.FIT,
) -> ImagePlacement:
    """A kép elhelyezése a margón belüli területen, arányosan, középre
    igazítva — torzítás nélkül.

    `FIT`: a teljes kép látszik (a rövidebbik irányban üres sáv maradhat).
    `FILL`: a margón belüli terület teljesen kitöltve, a kép hosszabbik
    iránya levágódik. A `page` már a VÉGLEGES tájolásban értendő — ez a
    függvény nem forgat (ld. a modul docstringje)."""
    if image_width <= 0 or image_height <= 0:
        raise ValueError(f"Érvénytelen képméret: {image_width}x{image_height}")

    area_w, area_h = page.printable_width, page.printable_height
    image_ratio = image_width / image_height
    area_ratio = area_w / area_h

    # FIT: a szűkebb irány szabja meg a méretet (a kép ne lógjon ki);
    # FILL: a tágabb irány szabja meg (a terület ne maradjon fedetlen).
    fits_by_width = (
        image_ratio >= area_ratio if fit_mode == PrintFitMode.FIT else image_ratio <= area_ratio
    )
    if fits_by_width:
        width = area_w
        height = width / image_ratio
    else:
        height = area_h
        width = height * image_ratio

    # középre igazítás az oldal (nem csak a margón belüli terület) egészéhez
    x = (page.width - width) / 2
    y = (page.height - height) / 2
    return ImagePlacement(x=x, y=y, width=width, height=height)

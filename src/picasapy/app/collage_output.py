"""A kollázs mentése (#943) — spec 9.1, jelzések nélkül.

Tiszta réteg: a panel állapotából renderelő-beállítás, a célfájl neve, és
a tényleges renderelés + írás. A jelzéseket (`collageProgress`,
`collageDone`, `collageFailed`) a vezérlő adja — így ez a rész Qt-esemény-
hurok nélkül is tesztelhető.

⚠️ **Amíg a `render_nodes` (a bontás 1. jegye, spec 6.5) meg nem érkezik**,
a mentés a meglévő `make_picasa_collage`-dzsel dolgozik, ami MAGA rendezi el
a képeket — a kézi átrendezés tehát a mentett képen még nem látszik. A
csere egyetlen helyen, a `render_collage()`-ben történik majd; a felület
felé menő szerződés nem változik.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from picasapy.collage import write_collage
from picasapy.collage.picasa_render import PicasaCollageSettings, make_picasa_collage

#: A kimeneti fájl neve: `il_collagefilename` = „kollázs" (spec 9.1).
FILENAME_STEM = "kollázs"

#: A mentett kép szélessége képpontban; a magasság a lap arányából jön.
OUTPUT_WIDTH = 1600

#: A „Kollázsok" album alapértelmezett helye, ha nincs beállított mappa.
DEFAULT_OUTPUT_DIR = Path("Pictures") / "Kollázsok"


def output_dir(configured: str | None) -> Path:
    """A célmappa: a beállított, egyébként `~/Pictures/Kollázsok`.

    A mappanév MAGYAR („Kollázsok"), mert ez a felhasználónak megjelenő
    album neve (spec 9.1) — a szülőmappa viszont a rendszer szokásos
    képmappája marad."""
    if configured:
        return Path(str(configured))
    return Path.home() / DEFAULT_OUTPUT_DIR


def output_path(folder: Path, now: datetime | None = None) -> Path:
    """`kollázs-<időbélyeg>.jpg` — az időbélyeg mikroszekundumig megy, hogy
    két gyors egymás utáni mentés se írja felül egymást."""
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S-%f")
    return Path(folder) / f"{FILENAME_STEM}-{stamp}.jpg"


def render_settings(
    *,
    theme: str,
    border: str,
    spacing: float,
    shadows: bool,
    page_ratio: float,
    background_rgb: tuple[int, int, int],
    frame_center: int,
    seed: int,
    width: int = OUTPUT_WIDTH,
) -> PicasaCollageSettings:
    """A panel állapotából renderelő-beállítás.

    ⚠️ A `PicasaCollageSettings.background` **BGR** sorrendű (az OpenCV
    csatornasorrendje), a felület viszont RGB-ben gondolkodik — a fordítás
    ITT történik, egy helyen. Aki ezt kihagyja, kék helyett pirosat rajzol.
    A `frame_center` −1 értéke azt jelenti, hogy nincs rögzített kép."""
    red, green, blue = background_rgb
    return PicasaCollageSettings(
        theme=theme,
        border=border,
        width=width,
        height=max(16, round(width * page_ratio)),
        background=(blue, green, red),
        spacing=spacing,
        seed=seed,
        frame_center=None if frame_center < 0 else frame_center,
        shadow=shadows,
    )


def render_collage(
    sources: Sequence[Path], settings: PicasaCollageSettings, target: Path
) -> tuple[Path | None, int]:
    """Renderelés és írás. Visszatérés: (a kész fájl, a felhasznált képek
    száma). Ha egyetlen kép sem volt olvasható, az útvonal `None`."""
    report = make_picasa_collage(list(sources), settings)
    if not report.used:
        return None, 0
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    return write_collage(target, report.image), len(report.used)


__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "FILENAME_STEM",
    "OUTPUT_WIDTH",
    "output_dir",
    "output_path",
    "render_collage",
    "render_settings",
]

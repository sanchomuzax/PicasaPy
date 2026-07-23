"""Arc-régió adatmodell az XMP-exporthoz + EXIF-orientáció transzformáció.

A `.picasa.ini` `faces=` kulcsa (ld. `picasapy.ini.faces`) rect64-kódolású,
**a nyers (orientáció ELŐTTI) képkerethez viszonyított** relatív téglalapokat
tartalmaz (spec: docs/specs/picasa-ini-format.md, "EXIF-orientáció"
bekezdés). Az MWG-RS régiók viszont ahhoz a képkerethez tartoznak, amelyet
az `AppliedToDimensions` (szélesség/magasság) leír — ha a fogyasztó a
megjelenített (already-rotated) kerethez akarja igazítani a régiókat, a
hívónak előbb `apply_orientation`-nel kell transzformálnia a téglalapot,
majd a forgatott szélesség/magasságot adnia az `xmp_writer.build_xmp`-nek.

A `FaceRegion` maga NEM végez kontakt-feloldást: a hívó (aki ismeri a
Contacts2-t) adja át a már feloldott nevet — ez a modul csak a
geometriával foglalkozik.
"""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.ini.rect64 import Rect64

# A Picasa/EXIF-specifikáció csak az 1/3/6/8 értékeket dokumentálja
# (docs/specs/picasa-ini-format.md) — a ritkán előforduló tükrözött
# értékeket (2,4,5,7) nem transzformáljuk, változatlanul adjuk vissza.
_HANDLED_ORIENTATIONS = frozenset({1, 3, 6, 8})


@dataclass(frozen=True)
class FaceRegion:
    """Egy megnevezett arc-régió: már feloldott név + normalizált téglalap."""

    name: str
    rect: Rect64


def apply_orientation(rect: Rect64, orientation: int) -> Rect64:
    """A `rect` transzformálása a raw képkeretről az orientáció-korrigált
    (megjelenített) keretre.

    Az 1/3/6/8-on kívüli orientáció-értékekre (ritka, tükrözött esetek)
    változatlanul adjuk vissza a téglalapot.
    """
    if orientation not in _HANDLED_ORIENTATIONS or orientation == 1:
        return rect
    if orientation == 3:  # 180°
        return Rect64(
            left=1.0 - rect.right,
            top=1.0 - rect.bottom,
            right=1.0 - rect.left,
            bottom=1.0 - rect.top,
        )
    if orientation == 6:  # 90° CW (a raw kép elforgatva CW-ban jelenik meg)
        return Rect64(
            left=1.0 - rect.bottom,
            top=rect.left,
            right=1.0 - rect.top,
            bottom=rect.right,
        )
    # orientation == 8: 90° CCW
    return Rect64(
        left=rect.top,
        top=1.0 - rect.right,
        right=rect.bottom,
        bottom=1.0 - rect.left,
    )


def oriented_dimensions(
    width: int, height: int, orientation: int
) -> tuple[int, int]:
    """A megjelenített szélesség/magasság — 6/8-nál a raw méretek felcserélve."""
    if orientation in (6, 8):
        return height, width
    return width, height

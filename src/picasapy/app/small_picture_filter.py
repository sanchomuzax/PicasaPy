"""Az eredeti Picasa `Show only big images` méret- és arányszűrője (#4346).

Az `ID_VIEW_SMALL` preferencia alapértéke a Picasa mérésében 1. A képméret
vizsgálatánál a 60 000 px²-nél nagyobb terület önmagában átenged; az ezen
vagy alatta lévő képeknél az arány és a 200 px-es hosszabb él is számít.
"""

from __future__ import annotations

BIG_PICTURE_THRESHOLD = 60_000
MIN_BIG_PICTURE_ASPECT_RATIO = 0.33333
MAX_BIG_PICTURE_ASPECT_RATIO = 3.0
MIN_BIG_PICTURE_LONG_EDGE = 200

SHOW_ONLY_BIG_IMAGES_KEY = "view/showOnlyBigImages"


def is_big_picture(width: int | None, height: int | None) -> bool:
    """Visszaadja, átengedi-e a kép mérete az eredeti Picasa szűrőjét.

    A 0x0065f521–0x0065f561 ágai alapján a küszöb fölötti terület (`ja`)
    kihagyja a további próbákat; az azon vagy az alatti terület csak a
    0,33333…3,0 aránytartományban és 200 px-nél hosszabb éllel jut át.
    Hiányzó/üres méretnél az eredeti a közös hozzáadási ágra lép.
    """
    if width is None or height is None:
        return True

    width = int(width)
    height = int(height)
    if width <= 0 or height <= 0:
        return True

    if width * height > BIG_PICTURE_THRESHOLD:
        return True

    aspect_ratio = width / height
    return (
        MIN_BIG_PICTURE_ASPECT_RATIO
        <= aspect_ratio
        <= MAX_BIG_PICTURE_ASPECT_RATIO
        and max(width, height) > MIN_BIG_PICTURE_LONG_EDGE
    )


def coerce_show_only_big_images(value) -> bool:
    """A QSettings bool/sztring értékét alapértékkel logikai értékké teszi."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1"):
            return True
        if normalized in ("false", "0"):
            return False
    if value in (0, 1):
        return bool(value)
    return True

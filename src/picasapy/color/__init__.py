"""Színbesorolás — a Picasa `color:` keresője (#383, #1480).

`classify.py` a MÉRT Picasa-osztályozót adja (telítettséggel súlyozott
hue-hisztogram az egész raszterről, hét vödör, a legnagyobb nyer);
`picasapy.index.colors` ezt tárolja/gyorsítótárazza az SQLite-indexben,
`picasapy.index.queries.search_photos` pedig ezt használja a
`color:`/`szín:` keresőtokenekhez."""

from .classify import (
    ACHROMATIC_TOKENS,
    COLOR_TOKENS,
    HUE_BUCKET_TOKENS,
    SATURATION_MIN,
    TOKEN_ALIASES,
    average_color,
    avgcolor_to_rgb,
    classify_image,
    hue_histogram,
    pixel_bucket,
    resolve_color_alias,
    rgb_to_avgcolor,
)

__all__ = [
    "ACHROMATIC_TOKENS",
    "COLOR_TOKENS",
    "HUE_BUCKET_TOKENS",
    "SATURATION_MIN",
    "TOKEN_ALIASES",
    "average_color",
    "avgcolor_to_rgb",
    "classify_image",
    "hue_histogram",
    "pixel_bucket",
    "resolve_color_alias",
    "rgb_to_avgcolor",
]

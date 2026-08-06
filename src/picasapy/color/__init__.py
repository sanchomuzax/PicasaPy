"""Színbesorolás — az elveszett Picasa `color:` kereső (#383).

`classify.py` az átlagszín ↔ 10 névből álló Picasa-kategória besorolást
adja; `picasapy.index.colors` ezt tárolja/gyorsítótárazza az SQLite-
indexben, `picasapy.index.queries.search_photos` pedig ezt használja a
`color:`/`szín:` keresőtokenekhez."""

from .classify import (
    COLOR_TOKENS,
    TOKEN_ALIASES,
    average_color,
    avgcolor_to_rgb,
    classify_color,
    resolve_color_alias,
    rgb_to_avgcolor,
)

__all__ = [
    "COLOR_TOKENS",
    "TOKEN_ALIASES",
    "average_color",
    "avgcolor_to_rgb",
    "classify_color",
    "resolve_color_alias",
    "rgb_to_avgcolor",
]

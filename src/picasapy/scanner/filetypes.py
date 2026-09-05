"""Picasa-kompatibilis médiatípus-felismerés kiterjesztés alapján.

Forrás: a Picasa binárisának **fájltípus-táblája** — egy 30 ágú ugrótáblás
kapcsoló (`0x004fadb0`, a tábla `0x004fb948`), amelynek minden ága
kiterjesztés-sztringeket regisztrál (#2415). A korábbi forrás, a Picasa 3.9
hivatalos támogatott-formátum listája (NotebookLM notebook, Picasa help),
kiegészítésként megmarad — de a mért tábla az erősebb bizonyíték: a súgó
listájából három kiterjesztés hiányzott.

⚠️ A tábla **16. ága dinamikusan** tölti a listáját (`call 0x00a4c720`),
ezért az ott nem látszó videó-kiterjesztések (`.3g2` … `.tod`) hiánya
**nem** negatív bizonyíték — azokat a súgó-lista alapján tartjuk.

⛔ **HELYESBÍTÉS (#2344).** Ez a fejléc korábban azt állította, hogy „a WebP
szándékosan hiányzik — a Picasa nem támogatta". **Ez téves volt**, három
független bizonyítékkal:

1. a `SupportWEBP` beállítás **alapértéke 1** (a nyilvántartó `0x006e0cb0`);
2. a bináris ismeri a kiterjesztést: `.webp` a `0x00467ca0`-n, `*.webp;` a
   fájlszűrő-listában a `0x00520220`-on, `*.webp` a `0x005e6a20`-on; a
   `SupportWEBP` kulcs hat függvényben szerepel, köztük a
   Beállítások-kezelőben (`0x006e1100`);
3. a tulajdonos **valódi** `thumbindex.db`-jében van `.webp` fájl.

A WebP-képek emiatt **némán eltűntek** a beolvasásból.

⚠️ **A formátum-kapcsolók hatóköre NINCS mérve.** A Picasa formátumonként
kapcsolható (`SupportGIF` és `SupportPNG` alapértéke **0**, a többié 1), a
mi szűrőnk viszont feltétel nélküli — a tulajdonos katalógusában mégis 125
PNG van. Hogy a kapcsoló a beolvasást vezérli-e, külön kutatás (#2344).
"""

from __future__ import annotations

from pathlib import PurePath

PHOTO_EXTENSIONS = frozenset(
    {
        ".jpeg", ".jpg", ".tif", ".tiff", ".bmp", ".gif", ".psd", ".png",
        ".tga",
        # #2415: a 0. ág a `.jpg`/`.jpeg` mellett a `.jpe`-t is
        # regisztrálja (`0x004fadc1`). A súgó-listából hiányzott.
        ".jpe",
        # #2344: a Picasa alapból indexeli (`SupportWEBP` = 1), ld. a
        # modul fejlécét. A megjelenítés is rendben: a szállított PySide6
        # 6.11.2 `QImageReader`-e olvassa, és a Pillow/OpenCV úton is
        # megvan. (A fejlesztői gép régebbi 6.8.2.1-e NEM — az a Qt-építés
        # sajátja, nem termékhiba; ezért nem is szabad rá tesztet kötni.)
        ".webp",
    }
)

RAW_EXTENSIONS = frozenset(
    {
        ".3fr", ".arw", ".cr2", ".crw", ".dcr", ".dng", ".kdc", ".mrw",
        ".nef", ".nrw", ".orf", ".pef", ".raf", ".raw", ".rw2", ".sr2",
        ".srf", ".x3f",
    }
)

VIDEO_EXTENSIONS = frozenset(
    {
        ".3g2", ".3gp", ".asf", ".avi", ".divx", ".m2t", ".m2ts", ".m4v",
        ".mkv", ".mmv", ".mod", ".mov", ".mp4", ".mpg", ".mts", ".tod",
        ".wmv",
        # #2415: a 8. ág a `.mpg` mellett ezt a kettőt is regisztrálja
        # (`0x004fb0f1`). A súgó-listából mindkettő hiányzott.
        ".mpeg", ".ty",
    }
)


def media_kind_of(name: str) -> str | None:
    """'photo' / 'raw' / 'video', vagy None, ha nem Picasa-média."""
    extension = PurePath(name).suffix.lower()
    if extension in PHOTO_EXTENSIONS:
        return "photo"
    if extension in RAW_EXTENSIONS:
        return "raw"
    if extension in VIDEO_EXTENSIONS:
        return "video"
    return None

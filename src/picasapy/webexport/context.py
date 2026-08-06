"""Album-, kép-hurok- és cél-oldal-változó táblák (docs/specs/
picasa-program-resources.md 2.4. alfejezet) — a `.tpl`/HTML-sablonokban
`<%name%>` alakban felhasználható értékek Python-oldali forrása.

Ez a modul TISZTA adat-összeállítás: nem ír fájlt, nem generál képet — a
tényleges bélyegkép/nagyméretű kép elkészítése az `images` modulé, a
fájl-írás/hurkolás az `engine`-é."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PhotoExportData:
    """Egy exportált kép a webexporthoz — a `images.prepare_photo_exports`
    tölti fel (forrás-metaadat + a ténylegesen legenerált bélyegkép/
    nagyméretű kép relatív útja és mérete)."""

    name: str
    caption: str
    original_width: int
    original_height: int
    size_bytes: int
    thumbnail_rel_path: str
    thumbnail_width: int
    thumbnail_height: int
    large_rel_path: str
    large_width: int
    large_height: int

    @property
    def name_only(self) -> str:
        """Fájlnév kiterjesztés nélkül (`itemNameOnly`)."""
        stem, _dot, _ext = self.name.rpartition(".")
        return stem or self.name


@dataclass(frozen=True)
class AlbumExportData:
    """Egy exportálandó album (mappa) — a webexport-motor bemenete."""

    name: str
    caption: str = ""
    date: str = ""
    number: int = 1
    photos: tuple[PhotoExportData, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WebExportSettings:
    """A "parancs-változók" (2.4. alfejezet) kezdőértékei — a sablon
    `define`-jai felülírhatják futás közben, de a KÉPGENERÁLÁS (bélyegkép/
    nagyméretű kép mérete) ezekből indul, mert az már a `.tpl` feldolgozása
    ELŐTT lezajlik (ld. `images.py`)."""

    thumbnail_max_dimension: int | None = None  # None = eredeti méret (0 a .tpl-ben)
    image_max_dimension: int | None = None
    jpeg_quality: int = 85
    bg_color: str = "#FFFFFF"
    shadowed_thumbnails: bool = True
    shadowed_images: bool = False
    export_file_name: str = "index.html"


def _bool_var(value: bool) -> str:
    """Logikai érték `.tpl`-kompatibilis alakban (`<%if%>` truthy/falsy —
    ld. `tpl_lang._is_truthy`)."""
    return "true" if value else ""


def command_variables(settings: WebExportSettings) -> dict[str, str]:
    """A "parancs-változók" tábla (2.4.) kezdőértékei — ezeket a sablon
    `define` parancsai felülírhatják a futás során."""
    return {
        "exportFileName": settings.export_file_name,
        "imageWidth": str(settings.image_max_dimension or 0),
        "imageHeight": str(settings.image_max_dimension or 0),
        "thumbnailWidth": str(settings.thumbnail_max_dimension or 0),
        "thumbnailHeight": str(settings.thumbnail_max_dimension or 0),
        "bgColor": settings.bg_color,
        "shadowedThumbnails": _bool_var(settings.shadowed_thumbnails),
        "shadowedImages": _bool_var(settings.shadowed_images),
    }


def album_variables(album: AlbumExportData) -> dict[str, str]:
    """Album-szintű változók — minden oldalon elérhetők (2.4.)."""
    return {
        "albumNumber": str(album.number),
        "albumName": album.name,
        "albumCaption": album.caption,
        "albumDate": album.date,
        "albumItemCount": str(len(album.photos)),
    }


def image_loop_variables(photos: tuple[PhotoExportData, ...], index: int) -> dict[str, str]:
    """Kép-hurok változók (2.4.) egy adott indexű képhez — az album-
    változókon FELÜL érvényesek (a hívó fésüli össze)."""
    photo = photos[index]
    is_first = index == 0
    is_last = index == len(photos) - 1
    prev_photo = photos[index - 1] if not is_first else None
    next_photo = photos[index + 1] if not is_last else None
    first_photo = photos[0]
    last_photo = photos[-1]
    return {
        "itemNumber": str(index + 1),
        "itemName": photo.name,
        "itemNameOnly": photo.name_only,
        "itemOriginalPath": photo.name,
        "itemCaption": photo.caption,
        "itemWidth": str(photo.original_width),
        "itemHeight": str(photo.original_height),
        "itemSize": str(round(photo.size_bytes / 1024)),
        "itemThumbnailImage": photo.thumbnail_rel_path,
        "itemThumbnailWidth": str(photo.thumbnail_width),
        "itemThumbnailHeight": str(photo.thumbnail_height),
        "itemLargeImage": photo.large_rel_path,
        "isFirstImage": _bool_var(is_first),
        "isLastImage": _bool_var(is_last),
        "isNextImage": _bool_var(not is_last),
        "isPrevImage": _bool_var(not is_first),
        "nextImage": next_photo.large_rel_path if next_photo else "",
        "prevImage": prev_photo.large_rel_path if prev_photo else "",
        "nextThumbnail": next_photo.thumbnail_rel_path if next_photo else "",
        "prevThumbnail": prev_photo.thumbnail_rel_path if prev_photo else "",
        "firstImage": first_photo.large_rel_path,
        "lastImage": last_photo.large_rel_path,
        "firstThumbnail": first_photo.thumbnail_rel_path,
        "lastThumbnail": last_photo.thumbnail_rel_path,
    }


def target_page_variables(
    target_file_names: tuple[str, ...], index: int, referrer: str
) -> dict[str, str]:
    """Cél-oldal (`targetloop` által generált fájl) változói (2.4.) — az
    album- és kép-hurok változókon FELÜL. `target_file_names`: az ÖSSZES
    generált cél-fájl neve sorrendben (a next/prev/first/last kereséséhez);
    `referrer`: az őket tartalmazó (index) oldal fájlneve."""
    is_first = index == 0
    is_last = index == len(target_file_names) - 1
    return {
        "referrer": referrer,
        "outputIndex": str(index),
        "isFirstTarget": _bool_var(is_first),
        "isLastTarget": _bool_var(is_last),
        "isNextTarget": _bool_var(not is_last),
        "isPrevTarget": _bool_var(not is_first),
        "nextTarget": target_file_names[index + 1] if not is_last else "",
        "prevTarget": target_file_names[index - 1] if not is_first else "",
        "firstTarget": target_file_names[0],
        "lastTarget": target_file_names[-1],
    }

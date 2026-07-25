"""Fájl-metaadat olvasás/írás: EXIF (dátum, orientáció, méret) + IPTC
(felirat, kulcsszavak)."""

from .gps import (
    GeoPoint,
    format_geotag,
    gps_from_exif,
    parse_geotag,
    photo_location,
    read_exif_gps,
)
from .iptc_writer import write_iptc_caption, write_iptc_keywords
from .reader import (
    EMPTY_EXIF_DETAILS,
    EMPTY_METADATA,
    ExifDetails,
    FileMetadata,
    read_exif_details,
    read_file_metadata,
)

__all__ = [
    "GeoPoint",
    "format_geotag",
    "gps_from_exif",
    "parse_geotag",
    "photo_location",
    "read_exif_gps",
    "EMPTY_EXIF_DETAILS",
    "EMPTY_METADATA",
    "ExifDetails",
    "FileMetadata",
    "read_exif_details",
    "read_file_metadata",
    "write_iptc_caption",
    "write_iptc_keywords",
]

"""Fájl-metaadat olvasás/írás: EXIF (dátum, orientáció, méret) + IPTC
(felirat, kulcsszavak)."""

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
    "EMPTY_EXIF_DETAILS",
    "EMPTY_METADATA",
    "ExifDetails",
    "FileMetadata",
    "read_exif_details",
    "read_file_metadata",
    "write_iptc_caption",
    "write_iptc_keywords",
]

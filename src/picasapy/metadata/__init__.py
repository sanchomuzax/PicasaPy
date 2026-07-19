"""Fájl-metaadat olvasás/írás: EXIF (dátum, orientáció, méret) + IPTC
(felirat, kulcsszavak)."""

from .iptc_writer import write_iptc_caption, write_iptc_keywords
from .reader import EMPTY_METADATA, FileMetadata, read_file_metadata

__all__ = [
    "EMPTY_METADATA",
    "FileMetadata",
    "read_file_metadata",
    "write_iptc_caption",
    "write_iptc_keywords",
]

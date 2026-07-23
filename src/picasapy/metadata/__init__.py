"""Fájl-metaadat olvasás/írás: EXIF (dátum, orientáció, méret) + IPTC
(felirat, kulcsszavak) + XMP-export (arc-régiók, hierarchikus címkék)."""

from .iptc_writer import write_iptc_caption, write_iptc_keywords
from .reader import (
    EMPTY_EXIF_DETAILS,
    EMPTY_METADATA,
    ExifDetails,
    FileMetadata,
    read_exif_details,
    read_file_metadata,
)
from .xmp_regions import FaceRegion, apply_orientation, oriented_dimensions
from .xmp_writer import build_xmp, sidecar_path, write_sidecar

__all__ = [
    "EMPTY_EXIF_DETAILS",
    "EMPTY_METADATA",
    "ExifDetails",
    "FaceRegion",
    "FileMetadata",
    "apply_orientation",
    "build_xmp",
    "oriented_dimensions",
    "read_exif_details",
    "read_file_metadata",
    "sidecar_path",
    "write_iptc_caption",
    "write_iptc_keywords",
    "write_sidecar",
]

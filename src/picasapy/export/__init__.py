"""Exportálás: mappába (forgatás/átméretezés, #16) és XMP sidecar (#27)."""

from .exporter import ExportItem, ExportReport, ExportSettings, export_photos
from .xmp import (
    XmpImageMetadata,
    XmpRegion,
    build_sidecar_from_picasa,
    build_xmp,
    region_from_rect64,
    write_sidecar,
)
from .xmp_export import (
    build_sidecar_for_photo,
    export_sidecar_for_photo,
    export_sidecars,
)

__all__ = [
    "ExportItem",
    "ExportReport",
    "ExportSettings",
    "export_photos",
    "XmpImageMetadata",
    "XmpRegion",
    "build_sidecar_from_picasa",
    "build_xmp",
    "region_from_rect64",
    "write_sidecar",
    "build_sidecar_for_photo",
    "export_sidecar_for_photo",
    "export_sidecars",
]

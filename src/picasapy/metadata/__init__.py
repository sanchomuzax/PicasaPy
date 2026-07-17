"""Fájl-metaadat olvasás: EXIF (dátum, orientáció, méret) + IPTC (felirat)."""

from .reader import EMPTY_METADATA, FileMetadata, read_file_metadata

__all__ = ["EMPTY_METADATA", "FileMetadata", "read_file_metadata"]

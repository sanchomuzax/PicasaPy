"""A `movieeditpanel/export_movie` vezérlőhídja (#4564)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.movie.clip_export import export_clip
from .movie_output import pictures_dir
from .project_folder_names import ProjectFolderKind, letezo_vagy_honos_mappa

logger = logging.getLogger(__name__)


def exported_video_folder(language: str | None = None) -> Path:
    """Az eredeti Picasa `Exported Videos` célmappája."""
    if language is None:
        from .collage_output import _felulet_nyelve

        language = _felulet_nyelve()
    return letezo_vagy_honos_mappa(
        pictures_dir() / "Picasa", ProjectFolderKind.EXPORTED_VIDEOS, language
    )


class MovieClipExportMixin:
    """A modell vágását exportálja, miközben a felület szabad marad."""

    movieClipExported = Signal(str)
    movieClipExportFailed = Signal()

    @Slot(int)
    def exportMovieClip(self, row: int) -> None:  # noqa: N802 — QML-stílus
        photo = self._vago_sor(row)
        if photo is None:
            return

        trim = self.photos.movieTrimAt(row)
        source = Path(photo.folder_path) / photo.name
        start_ms = int(trim["start"])
        end_ms = int(trim["end"])

        def munka() -> None:
            try:
                output = export_clip(
                    source,
                    exported_video_folder(),
                    start_ms=start_ms,
                    end_ms=end_ms,
                )
            except Exception:
                logger.exception("#4564: a klip exportja elbukott: %s", source)
                self.movieClipExportFailed.emit()
                return
            self.movieClipExported.emit(str(output))

        self._start_background(munka, name="picasapy-export-movie-clip")


__all__ = ["MovieClipExportMixin", "exported_video_folder"]

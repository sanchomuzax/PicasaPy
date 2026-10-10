"""A `movieeditpanel/export_movie` vezérlőhídja (#4564)."""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import threading
from concurrent.futures import CancelledError

from PySide6.QtCore import Property, Signal, Slot

from picasapy.movie.clip_export import export_clip
from .project_folder_names import ProjectFolderKind, letezo_vagy_honos_mappa

logger = logging.getLogger(__name__)


def _platform() -> str:
    """A futó platform, cserélhető fogantyú a QML platformágához."""
    return sys.platform


def exported_video_folder(language: str | None = None) -> Path:
    """Az eredeti Picasa `Exported Videos` célmappája."""
    if language is None:
        from .collage_output import _felulet_nyelve

        language = _felulet_nyelve()
    from . import movie_output

    return letezo_vagy_honos_mappa(
        movie_output.pictures_dir() / "Picasa",
        ProjectFolderKind.EXPORTED_VIDEOS,
        language,
    )


class MovieClipExportMixin:
    """A modell vágását exportálja, miközben a felület szabad marad."""

    movieClipExported = Signal(str)
    movieClipExportFailed = Signal()

    @Property(bool, constant=True)
    def movieClipExportSupported(self) -> bool:  # noqa: N802 — QML-property-stílus
        """Windowson és macOS-en támogatott; Linuxon az eredeti tiltás marad."""
        return not _platform().startswith("linux")

    @Slot(int)
    def exportMovieClip(self, row: int) -> None:  # noqa: N802 — QML-stílus
        photo = self._vago_sor(row)
        if photo is None:
            return

        trim = self.photos.movieTrimAt(row)
        source = Path(photo.folder_path) / photo.name
        start_ms = int(trim["start"])
        end_ms = int(trim["end"])
        cancel_event = threading.Event()

        def munka() -> None:
            try:
                output = export_clip(
                    source,
                    exported_video_folder(),
                    start_ms=start_ms,
                    end_ms=end_ms,
                    cancel_event=cancel_event,
                )
            except CancelledError:
                return
            except Exception:
                logger.exception("#4564: a klip exportja elbukott: %s", source)
                self.movieClipExportFailed.emit()
                return
            self.movieClipExported.emit(str(output))

        self._start_background(
            munka,
            name="picasapy-export-movie-clip",
            cancel=cancel_event.set,
        )


__all__ = ["MovieClipExportMixin", "exported_video_folder"]

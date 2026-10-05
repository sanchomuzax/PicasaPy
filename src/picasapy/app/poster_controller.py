"""A Poszter készítése felületi vezérlője (#4268)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QLocale, Signal, Slot

from picasapy.lazy_cv2 import elore_betolt
from picasapy.printing.poster import make_poster_tiles

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

_POSTER_PAPER_SIZE_KEY = "paper"


class PosterMixin(BackgroundWorkerMixin):
    """A kiválasztott fotóból poszterlapokat készít háttérszálon."""

    posterFinished = Signal(list)
    posterFailed = Signal(str)

    @Slot(result=list)
    def posterPaperSizes(self) -> list[str]:  # noqa: N802
        """A rendszer területi beállításához tartozó két eredeti méret."""
        if QLocale().measurementSystem() == QLocale.MeasurementSystem.MetricSystem:
            return ["10x15", "20x25"]
        return ["4x6", "8.5x11"]

    @Slot(result=str)
    def posterPaperSize(self) -> str:  # noqa: N802
        """A régióban érvényes, legutóbb használt papírméret."""
        sizes = self.posterPaperSizes()
        stored = str(self._get_settings().value(_POSTER_PAPER_SIZE_KEY, sizes[0]))
        return stored if stored in sizes else sizes[0]

    @Slot(str)
    def setPosterPaperSize(self, paper_size: str) -> None:  # noqa: N802
        """A helyi méretkészletbe tartozó választás megőrzése."""
        if paper_size not in self.posterPaperSizes():
            return
        settings = self._get_settings()
        settings.setValue(_POSTER_PAPER_SIZE_KEY, paper_size)
        settings.sync()

    @Slot(str, int, str, bool)
    def createPoster(
        self,
        source_path: str,
        magnification_percent: int,
        paper_size: str,
        overlap: bool,
    ) -> None:  # noqa: N802
        """A kért poszterlapokat kiírja a forráskép mappájába."""
        local_path = to_local_path(source_path)
        if not local_path:
            self.posterFailed.emit("A kijelölt kép útvonala üres.")
            return

        # A cv2 első natív betöltését a GUI-szálon végezzük (#2370).
        elore_betolt()

        def work() -> None:
            try:
                pages = make_poster_tiles(
                    Path(local_path),
                    magnification_percent,
                    paper_size,
                    overlap,
                )
            except Exception as exc:  # noqa: BLE001 — a QML hibaüzenetet kap
                self.posterFailed.emit(str(exc))
                return
            self.posterFinished.emit([str(page) for page in pages])

        self._start_background(work, name="picasapy-poster")


__all__ = ["PosterMixin"]

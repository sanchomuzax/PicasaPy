"""Létrehozás menü: kollázs és mozgófilm (#29) — az AppController szelete.

Mindkét művelet háttérszálon fut (nagy képeknél, NAS-on percekig tarthat),
és ugyanazt a jelzés-mintát követi, mint az export (#16/#136):

- `...Finished(útvonal, felhasznált, kihagyott)` — sikeres futás,
- `...Failed(üzenet)` — emberi nyelvű hibaüzenet (a hívó dialógusa mutatja),
- a mozgófilm közben `movieProgress(kész, összes)` képenként.

A dialógusok a célfájlt `file://` URL-ként adják át (a QML FileDialog
alakja) — a `to_local_path` fordítja vissza helyi útvonallá.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.collage import COLLAGE_KINDS, CollageSettings, make_collage, write_collage
from picasapy.movie import MovieSettings, export_movie

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

# A kollázs alapértelmezett vászonmérete — nyomtatható, de nem irreális.
_COLLAGE_SIZE = (1600, 1200)
# Egy kollázsba/filmbe ennél több képet nincs értelme tenni: a cellák
# olvashatatlanul kicsik lennének, a videó pedig órákig tartana.
_MAX_ITEMS = 200
# A képek közti áttűnés felső korlátja (mp) — ennél hosszabb áttűnés
# elmossa a diavetítés ritmusát.
_MAX_TRANSITION_S = 0.5


class CreateMixin(BackgroundWorkerMixin):
    """Kollázs- és mozgófilm-készítés a kijelölésből, háttérszálon."""

    # (célfájl, felhasznált, kihagyott, ebből NEM TALÁLHATÓ) — #459/3: a
    # hiányzó fájl más eset, mint az olvashatatlan, külön mondatot kap
    collageFinished = Signal(str, int, int, int)
    collageFailed = Signal(str)
    movieProgress = Signal(int, int)
    movieFinished = Signal(str, int, int, int)
    movieFailed = Signal(str)

    def _selected_sources(self, rows) -> tuple[Path, ...]:
        """A kijelölt sorokból forrás-útvonalak, a rács sorrendjében."""
        photos = self._photos.photos
        return tuple(
            Path(photos[int(r)].folder_path) / photos[int(r)].name
            for r in rows
            if 0 <= int(r) < len(photos)
        )

    @Slot(list, str, str)
    def makeCollage(self, rows, kind: str, target_url: str) -> None:
        """Kollázs a kijelölt képekből a megadott célfájlba (JPEG).

        `kind`: a `picasapy.collage.COLLAGE_KINDS` egyike."""
        sources = self._selected_sources(rows)[:_MAX_ITEMS]
        target = to_local_path(target_url)
        if not sources:
            self.collageFailed.emit(self.tr("No pictures are selected."))
            return
        if not target:
            self.collageFailed.emit(self.tr("No target file was chosen."))
            return
        if kind not in COLLAGE_KINDS:
            self.collageFailed.emit(self.tr("Unknown collage type."))
            return

        settings = CollageSettings(
            kind=kind, width=_COLLAGE_SIZE[0], height=_COLLAGE_SIZE[1]
        )

        def worker():
            try:
                report = make_collage(sources, settings)
                if not report.used:
                    self.collageFailed.emit(
                        self.tr("None of the selected pictures could be read.")
                    )
                    return
                path = write_collage(Path(target), report.image)
            except (ValueError, OSError) as error:
                self.collageFailed.emit(str(error))
                return
            self.collageFinished.emit(
                str(path),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-collage")

    @Slot(list, str, int, float)
    def exportMovie(
        self, rows, target_url: str, height: int, seconds_per_photo: float
    ) -> None:
        """Diavetítés-videó a kijelölt képekből (MP4).

        `height`: a videó magassága (720/1080); a szélesség 16:9-ből jön."""
        sources = self._selected_sources(rows)[:_MAX_ITEMS]
        target = to_local_path(target_url)
        if not sources:
            self.movieFailed.emit(self.tr("No pictures are selected."))
            return
        if not target:
            self.movieFailed.emit(self.tr("No target file was chosen."))
            return
        try:
            settings = MovieSettings(
                width=(height * 16 // 9) // 2 * 2,
                height=height,
                seconds_per_photo=seconds_per_photo,
                # az áttűnés a képenkénti idő harmada, de legfeljebb 0,5 mp:
                # rövid diáknál (1 mp) a fix 0,5 mp-es áttűnés hosszabb
                # lenne, mint amennyi ideig a kép áll — az érvénytelen
                transition_seconds=min(_MAX_TRANSITION_S, seconds_per_photo / 3),
            )
        except ValueError as error:
            self.movieFailed.emit(str(error))
            return

        def worker():
            try:
                report = export_movie(
                    sources,
                    Path(target),
                    settings,
                    progress=lambda done, total: self.movieProgress.emit(done, total),
                )
            except (ValueError, OSError, RuntimeError) as error:
                self.movieFailed.emit(str(error))
                return
            if not report.used:
                self.movieFailed.emit(
                    self.tr("None of the selected pictures could be read.")
                )
                return
            self.movieFinished.emit(
                str(report.target),
                len(report.used),
                len(report.skipped),
                len(report.missing),
            )

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-movie")

"""A kijelölt képek mentése a lemezre („Mentés", Ctrl+S) és a festési
vonások bekötése a mentéshez (#3462)."""


from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.edit.session import EditSession
from picasapy.render.chain import can_render_filter

from .save_error_kind import save_error_kind
from .save_errors import _FAILED_DETAILS_LIMIT, _SAVE_ERRORS
from .save_render import _render_for_save


class SaveRowsMixin:
    """A „Mentés” művelet és a kijelölés-alapú lekérdezések."""

    #: #3462: a szerkesztő festésének vonásai útvonal szerint - az
    #: `application.py` köti be (`set_paint_strokes_provider`). Bekötés nélkül
    #: a mentés maszk nélkül renderel, ahogy eddig.
    _paint_strokes_provider = None

    def set_paint_strokes_provider(self, szolgaltato) -> None:
        """A `Path -> tuple[Vonas, ...]` szolgáltató bekötése (#3462)."""
        self._paint_strokes_provider = szolgaltato

    def _festes_vonasai(self, path: Path) -> tuple:
        """A képhez a munkamenetben élő festés vonásai - a FŐ szálon kell
        kiolvasni, a háttér-mentés már csak a kész sorozatot kapja."""
        szolgaltato = self._paint_strokes_provider
        if szolgaltato is None:
            return ()
        return tuple(szolgaltato(path) or ())

    def _selected_records(self, rows):
        photos = self._photos.photos
        return [
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        ]

    @Slot(list, result=list)
    def unrenderableFiltersIn(self, rows) -> list:  # noqa: N802 - QML-stílus
        """A kijelölésben szereplő, ÁLTALUNK NEM RENDERELHETŐ szűrőnevek.

        A mentés beégeti a láncot a fájlba: amit nem tudunk renderelni, az a
        beégetett képből kimarad, de a könyvelési lánc az eredeti-mappa
        ini-jében megmarad az „Undo Save” művelethez. A felület ezért a mentés előtt
        rákérdezhet (#444/#484).

        Ábécésorrendben, ismétlés nélkül; üres lista = nincs miért kérdezni.
        """
        names = set()
        for record in self._selected_records(rows):
            for op in EditSession.from_value(record.filters).ops:
                if not can_render_filter(op.name):
                    names.add(op.name.casefold())
        return sorted(names)

    def _start_row_save(self, rows, writer) -> None:
        """A „Mentés" háttérszálas útja.

        A `writer` a hívótól jön (a `save_controller.save_edited`): így a
        tesztek a modul nevén pótolhatják, és a futás a hívás pillanatában
        nézi meg.
        """
        self._ensure_disk_operation_feedback_wired()
        records = [
            (Path(r.folder_path) / r.name, int(r.rotate_steps or 0),
             r.filters or "", int(getattr(r, "flip_flags", 0) or 0),
             self._festes_vonasai(Path(r.folder_path) / r.name))
            for r in self._selected_records(rows)
        ]
        if not records:
            self.saveFinished.emit(0, 0)
            return
        self._ensure_save_progress()
        self._saveProgressTick.emit(0, len(records), 1)

        def worker():
            done, failed, details = 0, 0, []
            naplo: list[tuple[str, str]] = []
            successful_paths: list[Path] = []
            # #1527: ágonként EGY üzenet. Az eredeti sem sorolja fel a
            # fájlokat: három külön mondata van, és a lemezhiba-ágon az
            # ELSŐ érintett fájl neve + a hibakód jelenik meg.
            jelentett_agak: set[str] = set()
            for index, (path, rotate_steps, filters, flip, vonasok) in enumerate(records):
                try:
                    rendered = _render_for_save(
                        path, rotate_steps, filters, flip, paint_strokes=vonasok
                    )
                    writer(path, rendered, EditSession.from_value(filters))
                except _SAVE_ERRORS as error:
                    failed += 1
                    if len(details) < _FAILED_DETAILS_LIMIT:
                        details.append(f"{path.name}: {error}")
                    ag = save_error_kind(error)
                    if ag not in jelentett_agak:
                        jelentett_agak.add(ag)
                        self._report_save_error(error, path)
                else:
                    done += 1
                    successful_paths.append(path)
                    # #750: a sikeres mentés ÜRES lánccal jelent a naplónak,
                    # ami ott a bejegyzés TÖRLÉSÉT jelenti. Ld. a
                    # `_record_saved_state` docstringjében.
                    naplo.append((str(path), ""))
                self._saveProgressTick.emit(index + 1, len(records), 1)
            self._record_saved_state(naplo)
            self._resync_disk_operation_folders(successful_paths)
            self.diskOperationSucceededPaths.emit(
                [str(path) for path in successful_paths]
            )
            self._saveProgressTick.emit(len(records), len(records), 0)
            # #1527: a MENTÉS ága innentől a besorolt, hivatalos üzenetet
            # adja (`saveErrorOccurred`), nem a nyers „név: ok" listát -
            # az eredetiben is három konkrét mondat áll, nem felsorolás.
            # A `details` a naplónak marad, hogy a bukás oka ne vesszen el.
            if details:
                logging.getLogger(__name__).warning(
                    "mentés-hibák (#1527): %s", "; ".join(details)
                )
            self.saveFinished.emit(done, failed)

        self._start_background(worker, name="picasapy-save")


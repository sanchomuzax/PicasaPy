"""Lemezművelet-futtató a visszaállításhoz és az „Utolsó mentés visszavonásához",
valamint az ini-napló átvezetése a befejezett műveletek után."""


from __future__ import annotations

import logging
from pathlib import Path

from .save_error_kind import save_error_kind
from .save_errors import _FAILED_DETAILS_LIMIT, _SAVE_ERRORS


class SaveRestoreMixin:
    """A visszaállítás és a visszavonás közös háttérszálas útja."""

    def _record_saved_state(self, items) -> None:
        """A mentés-műveletek utáni ini-állapot átvezetése a #644-es naplóra.

        ## Miért kell (a hamis riasztás ugyanolyan kár, mint a néma veszteség)

        A napló azt őrzi, MI milyen `filters=` láncot írtunk ki utoljára, és
        a nézet feltöltésekor riaszt, ha az eltűnt. A mentés viszont MAGA
        veszi el a `filters=`-t: a láncot a pixelekbe égeti, a kulcsot törli,
        az eredeti-mappa ini-jébe teszi (`edit/save.py`). Ha a naplót nem
        vezetnénk át, a mentés utáni ELSŐ nézetfrissítés minden mentett képre
        azt állítaná, hogy „a szerkesztésed eltűnt" - a felhasználó pedig egy
        kattintással vissza is írhatná a láncot `filters=`-be, ami a már
        beégetett effektet MÁSODSZOR is ráfuttatná. Az átvezetés tehát nem
        kényelmi kérdés, hanem adatvédelem.

        ## A `redo=` NEM kerül a naplóba láncként (#750 döntés)

        Kézenfekvő lenne a `redo=` értékét is védeni - mégsem tesszük, két
        okból, és mindkettő a kár irányáról szól:

        1. **A detektor a `filters=`-t nézi.** A `detect_lost_edits` az index
           `filters=` mezőihez hasonlít; mentés után az minden mentett képnél
           üres. Egy `redo=`-t őrző bejegyzés így ÖRÖKKÉ veszteséget jelezne
           - a védelem zajjá válna, és a felhasználó megtanulná elhessegetni.
        2. **A helyreállítás célkulcsa rossz volna.** A
           `restoreOverwrittenEdit` a `filters=`-be ír vissza. Egy beégetett
           láncot oda visszatéve dupla-szerkesztés keletkezne (#297) - az
           eredménye ROSSZABB, mint a `redo=` elvesztése, amiből legfeljebb
           az „Utolsó mentés visszavonása" kényelme vész el, a pixelek nem: a
           mentés előtti bájtok a `.picasaoriginals` sorszámozott
           pillanatképében megvannak.

        A `redo=` az újra-listát jelenti. Régi PicasaPy-mentéseknél még ott
        maradhat a korábbi mentéslánc, de az új mentéseknél a lánc az
        eredeti-mappa ini-jébe kerül; a `redo=` újra-lista írása külön
        szerkesztési funkció.

        Az „Utolsó mentés visszavonása" ellenben VISSZAÍRJA a láncot
        `filters=`-be: onnantól megint van mit védeni, ezért ott a
        visszakapott láncot naplózzuk.
        """
        if items:
            self.recordSavedChains(items)

    def _run_restore(
        self, rows, operation, finished_signal, *, show_restore_progress=False
    ) -> None:
        self._ensure_disk_operation_feedback_wired()
        paths = [
            Path(r.folder_path) / r.name for r in self._selected_records(rows)
        ]
        if not paths:
            finished_signal.emit(0, 0)
            return

        if show_restore_progress:
            self._ensure_save_progress()
            self._save_progress_reverting = True
            self._saveProgressTick.emit(0, len(paths), 1)

        def worker():
            done, failed, details = 0, 0, []
            disk_error_occurred = False
            naplo: list[tuple[str, str]] = []
            successful_paths: list[Path] = []
            for index, path in enumerate(paths):
                try:
                    result = operation(path)
                except _SAVE_ERRORS as error:
                    failed += 1
                    if save_error_kind(error) == "disk":
                        disk_error_occurred = True
                    if len(details) < _FAILED_DETAILS_LIMIT:
                        details.append(f"{path.name}: {error}")
                else:
                    done += 1
                    successful_paths.append(path)
                    # #750: az „Utolsó mentés visszavonása" a visszaadott
                    # láncot `filters=`-be írja (`restored_filters`),
                    # onnantól megint van mit védeni. A „Visszaállítás"
                    # minden szerkesztés-könyvelést töröl, ott az üres lánc
                    # (a `getattr` alapértéke) törli a bejegyzést.
                    naplo.append((str(path), getattr(result, "restored_filters", "")))
                if show_restore_progress:
                    self._saveProgressTick.emit(index + 1, len(paths), 1)
            self._record_saved_state(naplo)
            self._resync_disk_operation_folders(successful_paths)
            self.diskOperationSucceededPaths.emit(
                [str(path) for path in successful_paths]
            )
            if details:
                if show_restore_progress and disk_error_occurred:
                    logging.getLogger(__name__).warning(
                        "visszaállítási hibák (#5268): %s", "; ".join(details)
                    )
                    self.revertErrorOccurred.emit()
                else:
                    self.saveFailedDetails.emit(details)
            if show_restore_progress:
                self._saveProgressTick.emit(len(paths), len(paths), 0)
            finished_signal.emit(done, failed)

        self._start_background(worker, name="picasapy-save-restore")


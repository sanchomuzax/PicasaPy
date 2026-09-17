"""RelocateController: a "Move Database" dialógus (`MoveDatabaseDialog.qml`,
#368, `move_database.fen`) QML-hídja.

Önálló QObject — a `DedupController`/`ImportSourceController` mintáját
követve NEM az `AppController` mixinje, hogy a `controller.py`/`Main.qml`
(forró fájlok, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést
kapja.

⚠️ **A vezérlő nem költöztet** (#3214). A mért eredetiben a párbeszéd
gombja csak SZÁNDÉKOT rögzít (`Preferences\\AppLocalDataPathCopy`, író
`0x007d1936`); a tényleges másolás a KÖVETKEZŐ induláskor fut, a
`moving_database.fen` haladásjelzőjével (olvasó `0x00404d97`). A vezérlő
dolga ezért kettő: a cél ELLENŐRZÉSE (#1402 — a művelet előtt, hogy
elutasításnál semmihez ne nyúljunk) és a szándék rögzítése. A költözést az
`app/startup_relocate.py` végzi el indulásnál."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from .data_location import clear_pending_root, write_pending_root
from .relocate_cel import (
    AKADALY_FORRASON_BELUL,
    AKADALY_HALOZATI,
    AKADALY_NEM_MAPPA,
    AKADALY_NEM_URES,
    cel_akadalya,
)
from .formatting import to_local_path

_log = logging.getLogger(__name__)


class RelocateController(QObject):
    """A `MoveDatabaseDialog.qml` háttér-hídja: cél-választás, a cél
    ellenőrzése és a költözési SZÁNDÉK rögzítése."""

    # a cél nem alkalmas — emberi nyelvű üzenet, semmi nem változott
    relocateFailed = Signal(str)
    # (a rögzített cél szövegesen) — a költözés a KÖVETKEZŐ induláskor fut
    relocateScheduled = Signal(str)

    def __init__(
        self,
        old_index_db: str | Path,
        old_cache_dir: str | Path,
        config_dir: str | Path,
        parent: QObject | None = None,
    ) -> None:
        """`old_index_db`/`old_cache_dir`: a jelenleg érvényes útvonalak
        (`application.py` `_data_dir()/"index.db"` és
        `_cache_dir()/"thumbs"`); `config_dir`: ahova a szándék és — a
        költözés után, indulásnál — az útvonal-felülbírálás kerül."""
        super().__init__(parent)
        self._old_index_db = Path(old_index_db)
        self._old_cache_dir = Path(old_cache_dir)
        self._config_dir = Path(config_dir)

    # #377: Qt-Property kell (nem sima @property) — a QML a sima Python-
    # property-t nem látja, és induláskor "Unable to assign [undefined] to
    # QString" figyelmeztetést adott. Az érték konstans (az áthelyezés
    # újraindítás után érvényesül), ezért constant=True.
    @Property(str, constant=True)
    def currentLocation(self) -> str:  # noqa: N802 — QML-property-stílus
        """A jelenlegi (egyesített) adatgyökér — a `pathbox
        name="current_location"` mezőnek. Az index és a cache külön XDG-
        mappában is élhet (első áthelyezés előtt) — ilyenkor az index
        mappáját mutatjuk, mert az a "fő" adat (a cache újraépíthető)."""
        return str(self._old_index_db.parent)

    @Slot(str)
    def startRelocate(self, new_location: str) -> None:
        """A költözés ELŐJEGYZÉSE a következő indulásra (#3214).

        `new_location` `file://` URL is lehet (a QML `FolderDialog`
        mintája, ld. `to_local_path`). A cél ellenőrzése ITT történik, a
        szándék rögzítése ELŐTT: elutasításnál semmi nem marad hátra —
        sem szándék, sem fájlmozgás.
        """
        target_text = to_local_path(new_location)
        if not target_text:
            self.relocateFailed.emit(
                self.tr("Choose a new database location first.")
            )
            return
        new_root = Path(target_text)

        # #1402: a mért eredeti a műveletet MEGELŐZŐEN ellenőriz, és
        # elutasításnál semmihez nem nyúl („No changes will be made").
        # Két feltétel van, mindkettő a binárisból: a cél írható HELYI
        # merevlemez (`MoveDatabase::LocalDriveOnly`), és ÜRES
        # (`MoveDatabase::Failure` — „make sure the destination is empty").
        hiba = self._elutasitas_oka(new_root)
        if hiba:
            self.relocateFailed.emit(hiba)
            return

        write_pending_root(self._config_dir, new_root)
        _log.info("adatbázis-költözés előjegyezve a következő indulásra: %s", new_root)
        self.relocateScheduled.emit(str(new_root))

    @Slot()
    def cancelScheduledRelocate(self) -> None:
        """Az előjegyzett költözés visszavonása — a következő indulás így
        marad a mostani helyen. Fájlt ez sem mozgat."""
        clear_pending_root(self._config_dir)

    def _elutasitas_oka(self, new_root: Path) -> str:
        """Miért nem alkalmas a cél — üres szöveg, ha alkalmas (#1402).

        Az ítéletet a `relocate_cel` adja (ugyanazt kérdezi az indulás is,
        #3214); itt csak a FELÜLETI, fordítható szöveg készül hozzá.
        """
        akadaly = cel_akadalya(
            new_root, (self._old_index_db.parent, self._old_cache_dir)
        )
        if akadaly == AKADALY_FORRASON_BELUL:
            return self.tr(
                "The destination is inside the current database folder. "
                "Choose a folder outside it."
            )
        if akadaly == AKADALY_NEM_MAPPA:
            return self.tr("The chosen destination is not a folder.")
        if akadaly == AKADALY_NEM_URES:
            return self.tr(
                "The destination folder is not empty. Choose an empty folder "
                "and try again."
            )
        if akadaly == AKADALY_HALOZATI:
            return self.tr(
                "The database cannot be moved to a network drive. Nothing "
                "has been changed."
            )
        return ""

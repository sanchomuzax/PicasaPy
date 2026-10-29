"""A mentés hibáinak felületi jelzése: a besorolt hibaág és a részletes lista.

A `_SAVE_ERRORS` a mentés kezelt hibáinak listája: egyik sem szökhet ki a
QML felé kivételként.
"""


from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal

from picasapy.edit.save import SaveError
from picasapy.ini import IniConflictError, IniSaveError

from .save_error_kind import save_error_code, save_error_kind


#: A mentés kezelt hibái: a fájlrendszeré, a kódolásé, a párhuzamos
#: ini-íróé és a magé - egyik sem szökhet ki a QML felé kivételként.
_SAVE_ERRORS = (OSError, ValueError, SaveError, IniSaveError, IniConflictError)


#: Ennyi hibás fájl nevét/okát mutatjuk az összegzésben (az export
#: `_EXPORT_FAILED_DETAILS_LIMIT` mintája) - tömeges hibánál a teljes lista
#: inkább zavaró, mint hasznos.
_FAILED_DETAILS_LIMIT = 5


class SaveErrorMixin:
    """A mentési hibák jelzései a felületnek."""

    #: az első néhány sikertelen fájl "név: ok" alakban
    saveFailedDetails = Signal(list)

    #: a HÁROM hivatalos hibaág: (ág, fájlnév, hibakód). Az ág-azonosítók
    #: a `save_error_kind.py`-ban; a SZÖVEGET a `SaveDialogs.qml` adja,
    #: mert a hivatalos feliratok fordítható erőforrások.
    saveErrorOccurred = Signal(str, str, int)
    #: a fájl-visszaállítás hivatalos, általános lemezhiba-üzenete (#5268)
    revertErrorOccurred = Signal()

    def _report_save_error(self, error: BaseException, path: Path) -> None:
        """Egy mentés-hiba besorolása és felküldése a felületnek."""
        self.saveErrorOccurred.emit(
            save_error_kind(error), path.name, save_error_code(error)
        )


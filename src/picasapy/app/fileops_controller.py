"""FileOpsController: fájlműveletek (átnevezés/áthelyezés/lomtár/fájlkezelő,
#15) QML-hídja.

Szándékosan útvonal-alapú (nem index-sor-alapú), hogy az `AppController`-től
(forró fájl, ld. CONTRIBUTING.md) függetlenül fejleszthető és tesztelhető
legyen — a QML a `photosModel.filePathAt(index)`-szel már meglévő
elérésiút-lekérdezést adja át. A rácshoz kötés (context-menü, index-
frissítés a sikeres műveletek után) az integrátor feladata."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.fileops import (
    delete_to_trash,
    move_photo,
    rename_photo,
    reveal_in_file_manager,
)
from picasapy.ini import IniConflictError, IniSaveError

from .controller import _to_local_path

# #295: az átnevezés/áthelyezés `.picasa.ini`-írása is elbukhat a
# párhuzamosan futó eredeti Picasa miatt (`IniConflictError`) vagy kódolási
# hibán (`IniSaveError`). Ezek nem `OSError`-ok, így a korábbi szűrő mellett
# néma bukásként (kezeletlen kivételként) tűntek volna el a QML felé — a
# `photo_ops_controller` mintájára itt is kezelt írási hibák.
_OPERATION_ERRORS = (ValueError, OSError, IniSaveError, IniConflictError)


class FileOpsController(QObject):
    """A QML fájlművelet-kontextusmenüjéhez tervezett híd."""

    photoRenamed = Signal(str, str)  # (régi_út, új_út)
    photoMoved = Signal(str, str)  # (régi_út, új_út)
    photoDeleted = Signal(str)  # (törölt_út)
    operationFailed = Signal(str, str)  # (művelet, hibaüzenet)

    @Slot(str, str)
    def renamePhoto(self, path: str, new_name: str) -> None:
        """Átnevezés (F2): a célnév- vagy forrás-hibákat `operationFailed`
        jelzi (nem emel Python-kivételt a QML felé)."""
        try:
            new_path = rename_photo(Path(path), new_name)
        except _OPERATION_ERRORS as error:
            self.operationFailed.emit("rename", str(error))
            return
        self.photoRenamed.emit(path, str(new_path))

    @Slot(str, str)
    def movePhoto(self, path: str, dest_folder: str) -> None:
        """Áthelyezés másik mappába. A célt a QML FolderDialog `file://`
        URL-ként adja — a lokális útvonallá alakítás itt történik."""
        try:
            new_path = move_photo(Path(path), Path(_to_local_path(dest_folder)))
        except _OPERATION_ERRORS as error:
            self.operationFailed.emit("move", str(error))
            return
        self.photoMoved.emit(path, str(new_path))

    @Slot(str)
    def deletePhoto(self, path: str) -> None:
        """Törlés a lomtárba (freedesktop.org Trash-specifikáció)."""
        try:
            delete_to_trash(Path(path))
        except OSError as error:
            self.operationFailed.emit("delete", str(error))
            return
        self.photoDeleted.emit(path)

    @Slot(str)
    def revealPhoto(self, path: str) -> None:
        """A fájlt tartalmazó mappa megnyitása a fájlkezelőben.

        Sikertelen megnyitás (hiányzó `xdg-open` vagy nemnulla kilépési
        kód) esetén `operationFailed`-et jelez, hogy a felhasználó ne
        maradjon visszajelzés nélkül (#112)."""
        try:
            reveal_in_file_manager(Path(path))
        except OSError as error:
            self.operationFailed.emit("reveal", str(error))

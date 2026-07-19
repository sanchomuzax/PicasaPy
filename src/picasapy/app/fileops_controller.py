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
        except (ValueError, OSError) as error:
            self.operationFailed.emit("rename", str(error))
            return
        self.photoRenamed.emit(path, str(new_path))

    @Slot(str, str)
    def movePhoto(self, path: str, dest_folder: str) -> None:
        """Áthelyezés másik mappába."""
        try:
            new_path = move_photo(Path(path), Path(dest_folder))
        except OSError as error:
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
        """A fájlt tartalmazó mappa megnyitása a fájlkezelőben."""
        reveal_in_file_manager(Path(path))

"""A FileOpsController delete mixin felelősségének mixinje."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

from PySide6.QtCore import Slot


def _controller_module():
    """A régi modul fogantyúihoz irányít, monkeypatch-kompatibilisen."""
    return import_module("picasapy.app.fileops_controller")


class FileOpsControllerDeleteMixin:
    @Slot(str)
    def deleteFolder(self, folder: str, trash_dir: Path | None = None) -> None:  # noqa: N802
        """A MAPPA a lomtárba, a tartalmával együtt (#1638).

        Az eredeti `Folder::ID_ALBUM_DELETE` parancsa. Hogy a lomtár a cél,
        és nem a végleges törlés, azt az eredeti megerősítő szövege mondja
        ki: *„…move the folder »%s« and its contents to the Recycle Bin?"*

        A `.picasa.ini` a mappával megy — nincs vele külön dolgunk —, tehát
        egy visszaállítás a feliratokat, címkéket és arc-hozzárendeléseket
        is visszahozza.

        A `trash_dir` CSAK a tesztek fogantyúja (a valódi lomtárba nem
        írunk próbaképp); a felületről mindig alapértelmezéssel hívjuk.

        Hiba esetén `operationFailed` megy ki emberi üzenettel, és a mappa
        érintetlen marad — néma bukás nincs."""
        _compat = _controller_module()
        source = _compat.Path(_compat._to_local_path(folder) or folder)
        try:
            _compat.delete_to_trash(source, trash_dir=trash_dir)
        except OSError as error:
            self.operationFailed.emit("delete_folder", str(error))
            return
        self.folderDeleted.emit(str(source))

    @Slot(str)
    def deletePhoto(self, path: str) -> None:
        """Törlés a lomtárba (freedesktop.org Trash-specifikáció).

        #1451: a megőrzött eredeti és a sorszámozott pillanatképek is mennek
        — enélkül láthatatlanul gyűltek, és a következő, azonos nevű kép egy
        IDEGEN fénykép eredetijét örökölte.

        A windowsos (rendszer-lomtáras) ágon a KÉP megy előbb, ezért ott a
        hiba a már megtörtént törlés UTÁN jöhet — ilyenkor a `photoDeleted`
        is kimegy, a hibaüzenet mellett (ld. `_torles_utan_hibaval`)."""
        _compat = _controller_module()
        try:
            _compat.delete_photo_to_trash(_compat.Path(path))
        except _compat.CompanionLeftBehindError as error:
            self._torles_utan_hibaval(path, error)
            return
        except OSError as error:
            self.operationFailed.emit("delete", str(error))
            return
        self.photoDeleted.emit(path)

    @Slot(str)
    def deletePhotoPermanently(self, path: str) -> None:
        """Végleges, azonnali törlés — akkor hívandó, ha a `path`-hoz nincs
        elérhető lomtár (#457: hálózati meghajtó/NAS), és a felhasználó a
        `deleteConfirmDialog` erre figyelmeztető, külön szövegű ágán mégis
        megerősítette a törlést.

        #1451: a megőrzött eredeti és a pillanatképek is törlődnek — árva
        fájl nem maradhat. A KÉP megy előbb (az a felhasználó kimondott
        szándéka), ezért egy kísérő bukása a már megtörtént törlés UTÁN
        jön — a felületnek mindkettőről tudnia kell."""
        _compat = _controller_module()
        try:
            _compat.delete_photo_permanently(_compat.Path(path))
        except _compat.CompanionLeftBehindError as error:
            self._torles_utan_hibaval(path, error)
            return
        except OSError as error:
            self.operationFailed.emit("delete", str(error))
            return
        self.photoDeleted.emit(path)

    def _torles_utan_hibaval(self, path: str, error: OSError) -> None:
        """A kép MÁR NINCS MEG, de a kísérője ott maradt (#1451 átnézés, 4.).

        A `photoDeleted` megy ELŐBB: a rács, az index és a duplikátum-lista
        a valóságot kövesse, mielőtt a hibaablak megjelenik. Enélkül a
        felületen ott maradt egy már nem létező kép bélyegképe, és a
        felhasználó egy olyan hibaüzenetet olvasott, ami épp azt mondja, a
        kép törlődött."""
        self.photoDeleted.emit(path)
        self.operationFailed.emit("delete", str(error))

    @Slot(list, result=bool)
    def trashAvailableFor(self, paths: list) -> bool:
        """True, ha MINDEN megadott útvonalhoz van elérhető lomtár (#457).
        Kevert kijelölésnél (van, ami nem) a szigorúbb ág nyer — `False` —,
        hogy a `deleteConfirmDialog` a végleges-törlés szövegét mutassa,
        és az ne törölje csendben azt is, amihez lett volna lomtár."""
        _compat = _controller_module()
        if not paths:
            return True
        return all(_compat.trash_available(_compat.Path(path)) for path in paths)

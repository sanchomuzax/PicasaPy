"""A QML által használt képrács-modell összeállítása."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, Property, Qt, Signal, Slot

from .photo_grid_access import PhotoGridAccess
from .photo_grid_navigation import PhotoGridNavigation
from .photo_grid_state import PhotoGridState


class PhotoGridModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1

    ThumbUrlRole = Qt.ItemDataRole.UserRole + 2

    StarRole = Qt.ItemDataRole.UserRole + 3

    CaptionRole = Qt.ItemDataRole.UserRole + 4

    IsVideoRole = Qt.ItemDataRole.UserRole + 5

    TakenAtRole = Qt.ItemDataRole.UserRole + 6

    FileUrlRole = Qt.ItemDataRole.UserRole + 7

    KeywordsRole = Qt.ItemDataRole.UserRole + 8

    ResolutionRole = Qt.ItemDataRole.UserRole + 9

    FolderPathRole = Qt.ItemDataRole.UserRole + 10

    revisionChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        PhotoGridState.initialize(self)

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        """Minden set_photos-nál nő — QML-kötések frissítés-triggere.

        (A statusText-re kötés nem elég: pl. forgatásnál a szöveg nem
        változik, így a kötés nem értékelődne újra.)
        """
        return self._revision

    # Az átvételek a Qt-osztály metaobjektumában tartják a slotokat.
    set_face_zoom = PhotoGridState.set_face_zoom
    _sor_url = PhotoGridState._sor_url
    set_thumb_level = PhotoGridState.set_thumb_level
    set_folder_photo_sort = PhotoGridState.set_folder_photo_sort
    set_display_mode = PhotoGridState.set_display_mode
    _in_folder_photo_order = PhotoGridState._in_folder_photo_order
    set_photos = PhotoGridState.set_photos
    set_linear_navigation = PhotoGridState.set_linear_navigation
    photos = PhotoGridState.photos
    remove_by_path = PhotoGridState.remove_by_path
    row_of_id = PhotoGridState.row_of_id
    update_photo = PhotoGridState.update_photo

    # A Qt-metaobjektum QML-tagjai a végső modell-osztályon maradnak.
    # A megvalósítás a megnevezett segédmodulokban van, a slot-aláírások
    # viszont változatlanul itt élnek.
    @Slot(int, result=int)
    def rotateAt(self, row: int) -> int:
        return PhotoGridState.rotateAt(self, row)

    @Slot(int, result=str)
    def thumbUrlAt(self, row: int) -> str:
        return PhotoGridAccess.thumbUrlAt(self, row)

    @Slot(int, result="QVariantMap")
    def itemAt(self, row: int) -> dict:
        return PhotoGridAccess.itemAt(self, row)

    @Slot(int, result=bool)
    def starAt(self, row: int) -> bool:
        return PhotoGridAccess.starAt(self, row)

    @Slot(int, result=bool)
    def isVideoAt(self, row: int) -> bool:
        return PhotoGridAccess.isVideoAt(self, row)

    @Slot(int, result="QVariantMap")
    def movieTrimAt(self, row: int) -> dict:
        return PhotoGridAccess.movieTrimAt(self, row)

    @Slot(int, result=str)
    def captionAt(self, row: int) -> str:
        return PhotoGridAccess.captionAt(self, row)

    @Slot(int, result=str)
    def fileUrlAt(self, row: int) -> str:
        return PhotoGridAccess.fileUrlAt(self, row)

    @Slot(int, str, result=str)
    @Slot(int, result=str)
    def displayUrlAt(self, row: int, mode: str = "") -> str:
        return PhotoGridAccess.displayUrlAt(self, row, mode)

    _megjelenitett = PhotoGridAccess._megjelenitett

    @Slot(int, result=int)
    def pixelWidthAt(self, row: int) -> int:
        return PhotoGridAccess.pixelWidthAt(self, row)

    @Slot(int, result=int)
    def pixelHeightAt(self, row: int) -> int:
        return PhotoGridAccess.pixelHeightAt(self, row)

    @Slot(int, result=bool)
    def pixelSidesSwappedAt(self, row: int) -> bool:
        return PhotoGridAccess.pixelSidesSwappedAt(self, row)

    @Slot(int, result=str)
    def idAt(self, row: int) -> str:
        return PhotoGridAccess.idAt(self, row)

    @Slot(int, result=int)
    def rowOfId(self, photo_id: int) -> int:
        return PhotoGridAccess.rowOfId(self, photo_id)

    @Slot(str, result=int)
    def rowOfPath(self, path: str) -> int:
        return PhotoGridAccess.rowOfPath(self, path)

    @Slot(int, result=str)
    def filePathAt(self, row: int) -> str:
        return PhotoGridAccess.filePathAt(self, row)

    @Slot(int, int, result=int)
    def folderNeighbor(self, row: int, delta: int) -> int:
        return PhotoGridNavigation.folderNeighbor(self, row, delta)

    @Slot(int, result="QVariantList")
    def folderRowRange(self, row: int) -> list:
        return PhotoGridNavigation.folderRowRange(self, row)

    _group_bounds = PhotoGridNavigation._group_bounds

    @Slot(int, result="QVariantList")
    def groupRange(self, row: int) -> list:
        return PhotoGridNavigation.groupRange(self, row)

    @Slot(int, str, int, result=int)
    def navigate(self, row: int, direction: str, columns: int) -> int:
        return PhotoGridNavigation.navigate(self, row, direction, columns)

    rowCount = PhotoGridNavigation.rowCount
    data = PhotoGridNavigation.data
    roleNames = PhotoGridNavigation.roleNames

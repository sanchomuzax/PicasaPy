"""A QML által használt képrács-modell összeállítása."""

from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, Property, Qt, Signal

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
    rotateAt = PhotoGridState.rotateAt
    thumbUrlAt = PhotoGridAccess.thumbUrlAt
    itemAt = PhotoGridAccess.itemAt
    starAt = PhotoGridAccess.starAt
    isVideoAt = PhotoGridAccess.isVideoAt
    movieTrimAt = PhotoGridAccess.movieTrimAt
    captionAt = PhotoGridAccess.captionAt
    fileUrlAt = PhotoGridAccess.fileUrlAt
    displayUrlAt = PhotoGridAccess.displayUrlAt
    _megjelenitett = PhotoGridAccess._megjelenitett
    pixelWidthAt = PhotoGridAccess.pixelWidthAt
    pixelHeightAt = PhotoGridAccess.pixelHeightAt
    pixelSidesSwappedAt = PhotoGridAccess.pixelSidesSwappedAt
    idAt = PhotoGridAccess.idAt
    rowOfId = PhotoGridAccess.rowOfId
    rowOfPath = PhotoGridAccess.rowOfPath
    filePathAt = PhotoGridAccess.filePathAt
    folderNeighbor = PhotoGridNavigation.folderNeighbor
    folderRowRange = PhotoGridNavigation.folderRowRange
    _group_bounds = PhotoGridNavigation._group_bounds
    groupRange = PhotoGridNavigation.groupRange
    navigate = PhotoGridNavigation.navigate
    rowCount = PhotoGridNavigation.rowCount
    data = PhotoGridNavigation.data
    roleNames = PhotoGridNavigation.roleNames


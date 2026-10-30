"""Az albumok, címkék és mappasorrend képműveleti témamixinje."""

# A régi modulnévtér kompatibilitási újraexportjai.
# ruff: noqa: F401

from __future__ import annotations

import secrets
from pathlib import Path

from PySide6.QtCore import QCoreApplication, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from picasapy.app.kezi_sorrend import mappa_prioritasai, mentsd_a_prioritasokat
from picasapy.index import (
    album_photos,
    open_index,
    photos_in_folder,
    photos_with_keyword,
)
from picasapy.index.album_sort import SORT_MODES, new_places, sorted_album
from picasapy.ini import (
    STAR_ALBUM_TOKEN,
    load_existing,
)
from picasapy.ini.albums import (
    albums_of,
    ensure_album,
    with_album,
    with_album_fields,
    without_album,
    without_album_everywhere,
)
from picasapy.ini.album_order import AlbumOrderWriteError, write_album_places
from picasapy.ini.document import ALBUM_SECTION_PREFIX
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .photo_ops_compat import _WRITE_ERRORS, update_document

from .photo_ops_album_membership_mixin import (
    PhotoOpsAlbumMembershipMixin,
)
from .photo_ops_album_order_mixin import PhotoOpsAlbumOrderMixin
from .photo_ops_album_properties_mixin import (
    PhotoOpsAlbumPropertiesMixin,
)
from .photo_ops_album_actions_mixin import PhotoOpsAlbumActionsMixin


class PhotoOpsAlbumMixin(
    PhotoOpsAlbumMembershipMixin,
    PhotoOpsAlbumOrderMixin,
    PhotoOpsAlbumPropertiesMixin,
    PhotoOpsAlbumActionsMixin,
):
    """A QML-kompatibilis homlokzat a kisebb albummixinekből."""

    albumWriteFailed = Signal(str)


del (
    PhotoOpsAlbumMembershipMixin,
    PhotoOpsAlbumOrderMixin,
    PhotoOpsAlbumPropertiesMixin,
    PhotoOpsAlbumActionsMixin,
)

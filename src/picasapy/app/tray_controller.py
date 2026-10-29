"""A képtálca vezérlőjének kompatibilis import-felülete.

A `TrayMixin` az eddigi nyilvános néven összefűzi a képtálca állapot-,
albumtoken- és Google Photos részeit. A QML- és Python-felület változatlan.
"""

from __future__ import annotations

# A régi modulnévtér importjai kompatibilitásból itt maradnak.
import threading  # noqa: F401
from pathlib import Path  # noqa: F401

from PySide6.QtCore import Property, QLocale, QUrl, Signal, Slot  # noqa: F401
from PySide6.QtGui import QDesktopServices  # noqa: F401

from picasapy import tray  # noqa: F401
from picasapy.index import open_index, photo_by_id, photos_in_folder  # noqa: F401
from picasapy.index.albums import album_photos  # noqa: F401
from picasapy.ini.albums import with_album  # noqa: F401
from picasapy.app import formatting  # noqa: F401
from picasapy.app.models import _thumb_url  # noqa: F401

from .tray_state_controller import TrayStateMixin
from .tray_album_controller import TrayAlbumMixin
from .tray_google_photos_controller import TrayGooglePhotosMixin


class TrayMixin(TrayStateMixin, TrayAlbumMixin, TrayGooglePhotosMixin):
    """A tálca teljes QML- és Python-API-ja, változatlan importnéven."""

    def expandFolderInTray(self, key: str) -> bool:
        """Python-segéd a token kivételéhez; nem QML-slot (#4316)."""
        return TrayAlbumMixin.expandFolderInTray(self, key)

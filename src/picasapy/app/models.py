"""QML-modellek a könyvtárlistákhoz.

A megvalósítás kisebb modulokban él; ez a modul megtartja a korábbi importútvonalat.
"""

from __future__ import annotations

import os
import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import quote
import zlib

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    Qt,
    QUrl,
    Signal,
    Slot,
)

from picasapy.metadata import megjelenitett_meret
from picasapy.index import PhotoRecord
from picasapy.index.hidden_scope import show_hidden_folders
from picasapy.paths import flat_key, path_key
from picasapy.ini.movie_trim import trim_from_filters

from .display_mode_paint import (
    current_display_mode,
    current_display_mode_suffix,
    display_mode_url_suffix,
)
from .arc_nagyitas_url import arc_cimke
from .photo_sort import DEFAULT_SORT_MODE, sort_folder_blocks
from .model_helpers import (
    REJTETT_MAPPAK_FEJLEC,
    _PATH_SEPARATORS as _PATH_SEPARATORS,
    _ROOT_INDEX as _ROOT_INDEX,
    _YEAR_PREFIX as _YEAR_PREFIX,
    _descending as _descending,
    _felbontas as _felbontas,
    _folder_year as _folder_year,
    _has_edits as _has_edits,
    _rejtett_csomopont as _rejtett_csomopont,
    _sort_key as _sort_key,
    _thumb_url as _thumb_url,
    _with_year_separators as _with_year_separators,
)
from .folder_list_model import FolderListModel, folder_order, sorted_folder_rows
from .photo_grid_model import PhotoGridModel

# QML-visible folder roles are unchanged: self.UnreadRole: b"unread".
FolderListModel.__module__ = __name__
PhotoGridModel.__module__ = __name__

__all__ = [
    "os",
    "re",
    "sqlite3",
    "Iterable",
    "Path",
    "quote",
    "zlib",
    "Property",
    "QAbstractListModel",
    "QModelIndex",
    "Qt",
    "QUrl",
    "Signal",
    "Slot",
    "megjelenitett_meret",
    "PhotoRecord",
    "show_hidden_folders",
    "flat_key",
    "path_key",
    "current_display_mode",
    "current_display_mode_suffix",
    "display_mode_url_suffix",
    "trim_from_filters",
    "arc_cimke",
    "DEFAULT_SORT_MODE",
    "sort_folder_blocks",
    "sorted_folder_rows",
    "folder_order",
    "FolderListModel",
    "REJTETT_MAPPAK_FEJLEC",
    "PhotoGridModel",
]

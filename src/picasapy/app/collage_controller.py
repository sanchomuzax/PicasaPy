"""A kollázs-panel vezérlőjének kompatibilis importhomlokzata (#943, #6254)."""

# A régi modulnevek a kompatibilitási homlokzaton maradnak.
# ruff: noqa: F401

from __future__ import annotations

import threading  # noqa: F401
from collections.abc import Sequence  # noqa: F401
from pathlib import Path  # noqa: F401

from PySide6.QtCore import Property, QObject, Signal, Slot  # noqa: F401
from PySide6.QtGui import QColor, QGuiApplication  # noqa: F401

from picasapy.app.collage_album_fields import album_fields_of  # noqa: F401
from picasapy.app.collage_sources import common_source_folder_name  # noqa: F401
from picasapy.collage import canvas  # noqa: F401
from picasapy.collage.fitting import MsvcRandom  # noqa: F401
from picasapy.collage.page_formats import (
    FALLBACK_SCREEN_RATIO,
    ORIENTATIONS,
    is_known_format,
    page_ratio,
)  # noqa: F401
from picasapy.collage.themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    CONTACTSHEET,
    MULTIEXP,
    NOBORDER,
    WHITEBORDER,
    capabilities_for,
    capability_map,
)  # noqa: F401

from . import collage_layout as layout  # noqa: F401
from . import collage_prefs as prefs
from .collage_background import BACKGROUND_MODES, CollageBackgroundMixin  # noqa: F401
from .collage_controller_settings import _CollageControllerSettingsMixin
from .collage_controller_state import _CollageControllerStateMixin
from .collage_controller_canvas import CollageCanvasMixin  # noqa: F401
from .collage_model import (
    CollageNode,
    CollageNodeModel,
    group_bounds,
    initial_node_width,
    selected_indices,
    with_selection,
)  # noqa: F401
from .collage_save import CollageSaveMixin  # noqa: F401
from .collage_shadow import CollageShadowMixin  # noqa: F401

#: A kimeneti mappa beállítás-kulcsa — a `collage_prefs`-ből átemelve, hogy a
#: felület és a teszt EGY nevet lásson.
COLLAGE_OUTPUT_DIR_KEY = prefs.OUTPUT_DIR_KEY


class CollageMixin(
    _CollageControllerStateMixin,
    _CollageControllerSettingsMixin,
    CollageCanvasMixin,
    CollageSaveMixin,
    CollageBackgroundMixin,
    CollageShadowMixin,
):
    """A kollázs-lap állapota és parancsai — a spec 8. szakasza."""


__all__ = [
    "BACKGROUND_MODES",
    "COLLAGE_OUTPUT_DIR_KEY",
    "CollageMixin",
]

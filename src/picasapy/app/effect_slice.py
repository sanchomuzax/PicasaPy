"""Effekt-térszelvény vezérlő és 3D QML-rajzoló (#6522).

# SAJÁT FUNKCIÓ (#6522): az eredeti Picasában nincs mini 3D effekt-térszelvény.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QObject,
    QRunnable,
    QSettings,
    QThreadPool,
    QTimer,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QPainter
from PySide6.QtQuick import QQuickPaintedItem
from PySide6.QtQml import qmlRegisterType

from picasapy.app.effect_params import resolve_effect_params
from picasapy.ini.filters import FilterOp, parse_filters
from picasapy.render.registry import FILTER_REGISTRY

from . import edit_preview_source
from .effect_slice_paint import (
    BASE_AZIMUTH,
    CHANNEL_COLORS,
    DIMENSIONS,
    ELEVATION,
    MARKER_COLOR,
    interpolate_row,
    make_projection,
    paint_color_cube,
    paint_frame,
    paint_polyline,
    paint_surface,
)
from .effect_slice_render import render_surface

# SAJÁT FUNKCIÓ (#6522): mind a PicasaPy filterdesc-regiszterének 84 effektje nézettípust kap.
_NEZETEK = {
    "none": {
        "border", "cinemascope", "crop", "crop64", "debug", "dropshadow", "matte",
        "movieend", "moviestart", "museummatte", "polaroid", "reanimatedeyecolor",
        "redeye", "retouch", "rot", "roundededges", "save", "tilt",
    },
    "grain": {"grain", "grain2", "picnikgrain"},
    "point": {
        "blur", "dir_sharp", "linblur", "radblur", "soften", "unsharp", "unsharp2",
    },
    "tone": {
        "autobacklight", "autocontrast", "autolight", "backlight", "contrast", "fill",
        "finetune", "finetune2", "gamma", "hdr", "localcontrast", "shadow", "triple",
        "triple2", "triple3",
    },
    "color": {
        "ansel", "autocolor", "bw", "colorfix", "colortemp", "crossprocess", "dir_tint",
        "heatmap", "holga", "invert", "ir", "lomo", "nightvision", "picniktint",
        "quantizepalette", "rainbow", "radsat", "radtint", "sat", "sepia", "tint",
        "twotone", "warm", "whitept",
    },
    "image": {
        "boost", "comicize", "dir_brite", "dir_sat", "enhance", "focalpixelate",
        "focalzoom", "glow", "glow2", "neon", "orton", "pencilsketch", "picnik",
        "picnikfocalpixelate", "pixelate", "sixties", "vignette",
    },
}
EFFECT_VIEW_TYPES = {
    effect: view_type
    for view_type, effects in _NEZETEK.items()
    for effect in effects
}
EFFECT_VIEW_TYPES.update({key: "none" for key in FILTER_REGISTRY if key not in EFFECT_VIEW_TYPES})
_VIEW_ORDER = ("tone", "color", "image", "point", "grain", "none")
# A Finomhangolás fül négy csúszkája: (finetune2-paraméterhely, min, max, felirat)
_FINETUNE_SLIDERS = (
    (1, 0.0, 1.0, "Fill Light"),
    (2, 0.0, 0.48, "Highlights"),
    (3, 0.0, 0.48, "Shadows"),
    (5, -1.0, 1.0, "Color Temperature"),
)
_PHOTO_PROBE_EFFECTS = frozenset(
    {
        "autobacklight", "autocolor", "autocontrast", "autolight", "enhance", "hdr",
        "localcontrast", "matte", "orton",
    }
)


def classify_effect(name: str) -> str:
    """Effekt nézettípusa. Ismeretlen lánctaghoz a biztonságos üres nézet jár."""
    return EFFECT_VIEW_TYPES.get(str(name).casefold(), "none")


def _file_mtime(path: Path | None) -> int | None:
    if path is None:
        return None
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return None


class RenderSignals(QObject):
    finished = Signal(int, object)


class _RenderTask(QRunnable):
    """A kis próbaképeket háttérszálon futtató feladat."""

    def __init__(self, job: int, request: dict, signals: RenderSignals) -> None:
        super().__init__()
        self.job = job
        self.request = request
        self.signals = signals

    def run(self) -> None:
        try:
            source = None
            if self.request["probeKind"] == "photo" and self.request["path"]:
                source = edit_preview_source._decode_source(
                    Path(self.request["path"]),
                    full_res=False,
                    color_managed=self.request["colorManaged"],
                )
                if source is not None:
                    from picasapy.lazy_cv2 import cv2

                    height, width = source.shape[:2]
                    scale = min(1.0, 96.0 / max(height, width, 1))
                    if scale < 1.0:
                        source = cv2.resize(
                            source,
                            (max(1, round(width * scale)), max(1, round(height * scale))),
                            interpolation=cv2.INTER_AREA,
                        )
            data = render_surface(
                source,
                self.request["operations"],
                self.request["viewType"],
                depth=self.request["depth"],
                probe_kind=self.request["probeKind"],
            )
        except Exception:  # noqa: BLE001 - a felület hibája nem döntheti le a nézőt
            data = {"kind": "none", "rows": [], "message": "none"}
        self.signals.finished.emit(self.job, data)


class EffectSliceController(QObject):
    """QSettings-állapot, mintakérés, gyorsítótár és nézetváltó a bal fióknak."""

    modeChanged = Signal()
    spinningChanged = Signal()
    surfaceChanged = Signal()
    viewTypeChanged = Signal()

    def __init__(self, edit_controller, settings: QSettings | None = None, parent=None):
        super().__init__(parent)
        self._edit = edit_controller
        self._settings = settings or QSettings("PicasaPy", "PicasaPy")
        self._mode = str(self._settings.value("view/effectSlice", "editing"))
        if self._mode not in {"always", "editing", "never"}:
            self._mode = "editing"
        self._spinning = self._settings.value("view/effectSliceSpin", True, type=bool)
        self._surface_data = {"kind": "none", "rows": [], "message": "none"}
        self._available_views = ["tone"]
        self._selected_view = "tone"
        self._active_effect = ""
        self._active_values: list = []
        self._depth_index = 0
        self._photo_path = ""
        self._chain_value = ""
        self._chain_length = 0
        self._slider_label = ""
        self._slider_current = 0.0
        self._pending = None
        self._job = 0
        self._last_cache_key = None
        self._last_target = None
        self._cache: OrderedDict[tuple, dict] = OrderedDict()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(60)
        self._timer.timeout.connect(self._start_render)

    @Property(str, notify=modeChanged)
    def mode(self) -> str:
        return self._mode

    @Property(bool, notify=spinningChanged)
    def spinning(self) -> bool:
        return self._spinning

    @Property("QVariantMap", notify=surfaceChanged)
    def surfaceData(self) -> dict:
        return self._surface_data

    @Property("QVariantList", notify=viewTypeChanged)
    def availableViewTypes(self) -> list[str]:
        return list(self._available_views)

    @Property(str, notify=viewTypeChanged)
    def selectedViewType(self) -> str:
        return self._selected_view

    @Property(int, notify=surfaceChanged)
    def chainLength(self) -> int:
        return self._chain_length

    @Property(str, notify=surfaceChanged)
    def sliderLabel(self) -> str:
        return self._slider_label

    @Property(float, notify=surfaceChanged)
    def sliderValue(self) -> float:
        return self._slider_current

    @Slot(str)
    def setMode(self, mode: str) -> None:
        mode = str(mode)
        if mode not in {"always", "editing", "never"} or mode == self._mode:
            return
        self._mode = mode
        self._settings.setValue("view/effectSlice", mode)
        self.modeChanged.emit()

    @Slot(bool)
    def setSpinning(self, spinning: bool) -> None:
        spinning = bool(spinning)
        if spinning == self._spinning:
            return
        self._spinning = spinning
        self._settings.setValue("view/effectSliceSpin", spinning)
        self.spinningChanged.emit()

    @Slot()
    def toggleSpinning(self) -> None:
        self.setSpinning(not self._spinning)

    def shutdown(self) -> None:
        """Kilépéskor leállítja a késleltetést és az esetleg futó mintamérést."""
        self._timer.stop()
        self._job += 1
        self._pending = None
        self._pool.clear()
        self._pool.waitForDone(1000)

    @Slot(str, "QVariantList", int, str, str, str)
    def request(
        self,
        effect_name: str,
        values: list,
        depth_index: int,
        preferred_view: str,
        photo_path: str,
        chain_value: str,
    ) -> None:
        """A QML legfrissebb állapotát 60 ms-os összevonással rendereli."""
        self._active_effect = str(effect_name or "").casefold()
        self._active_values = list(values or [])
        self._depth_index = max(0, int(depth_index))
        self._photo_path = str(photo_path or "")
        self._chain_value = str(chain_value or "")
        self._job += 1
        request = self._build_request(str(preferred_view or ""))
        self._pending = request
        self._timer.start()

    @Slot()
    def cycleViewType(self) -> None:
        if len(self._available_views) < 2:
            return
        index = self._available_views.index(self._selected_view)
        self._selected_view = self._available_views[(index + 1) % len(self._available_views)]
        self.viewTypeChanged.emit()
        self.request(
            self._active_effect,
            self._active_values,
            self._depth_index,
            self._selected_view,
            self._photo_path,
            self._chain_value,
        )

    def _build_request(self, preferred_view: str) -> dict:
        old_views = tuple(self._available_views)
        old_selected = self._selected_view
        active_session = None
        path = Path(self._photo_path) if self._photo_path else None
        chain_text = self._chain_value
        if self._active_effect and getattr(self._edit, "_photo_id", ""):
            active_session = self._active_session()
            if active_session is not None:
                path = self._edit._image_path
                chain_text = active_session.to_value()
        operations = (
            tuple(active_session.ops)
            if active_session is not None
            else tuple(parse_filters(chain_text))
        )
        self._chain_length = len(operations)
        views = {classify_effect(operation.name) for operation in operations}
        if self._active_effect:
            views.add(classify_effect(self._active_effect))
        if not views:
            views.add("tone")
        self._available_views = [view for view in _VIEW_ORDER if view in views]
        if preferred_view in self._available_views:
            self._selected_view = preferred_view
        elif self._selected_view not in self._available_views:
            self._selected_view = self._available_views[0]
        if old_views != tuple(self._available_views) or old_selected != self._selected_view:
            self.viewTypeChanged.emit()
        selected = self._selected_view

        target = self._active_depth_target(operations) if active_session is not None else None
        if target is None:
            target = self._chain_depth_target(operations, selected)
        self._slider_label = target["label"] if target else ""
        self._slider_current = float(target["current"]) if target else 0.0
        probe_kind = "photo" if self._requires_photo_probe(operations, target) else "gray"
        depth = None
        if target:
            depth = {
                "operationIndex": target["operationIndex"],
                "parameterIndex": target["parameterIndex"],
                "minimum": target["minimum"],
                "maximum": target["maximum"],
                "current": target["current"],
            }
        key_ops = list(operations)
        if target:
            item = key_ops[target["operationIndex"]]
            params = list(item.params)
            params[target["parameterIndex"]] = "__slice_axis__"
            key_ops[target["operationIndex"]] = FilterOp(item.name, tuple(params))
        cache_key = (
            str(path or ""), _file_mtime(path), selected, probe_kind,
            tuple((item.name, item.params) for item in key_ops),
            target["operationIndex"] if target else None,
            target["parameterIndex"] if target else None,
            target["minimum"] if target else None,
            target["maximum"] if target else None,
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._cache.move_to_end(cache_key)
            data = dict(cached)
            self._set_marker(data, target)
            self._surface_data = data
            self.surfaceChanged.emit()
            return {"cached": True}
        try:
            color_managed = bool(self._edit._provider.color_management)
        except (AttributeError, RuntimeError):
            color_managed = False
        return {
            "cached": False,
            "cacheKey": cache_key,
            "operations": operations,
            "viewType": selected,
            "depth": depth,
            "target": target,
            "path": str(path or ""),
            "probeKind": probe_kind,
            "colorManaged": color_managed,
        }

    def _active_session(self):
        if self._active_effect != "finetune2":
            return self._edit._session_with_effect(self._active_effect, self._active_values)
        values = [self._float_value(index) for index in range(4)]
        return self._edit._session.set_finetune(
            fill=values[0], highlights=values[1], shadows=values[2], temperature=values[3]
        )

    def _float_value(self, index: int) -> float:
        try:
            return float(self._active_values[index])
        except (IndexError, TypeError, ValueError):
            return 0.0

    def _finetune_target(self, operations: tuple[FilterOp, ...]) -> dict | None:
        operation_index = next(
            (
                index
                for index in range(len(operations) - 1, -1, -1)
                if operations[index].name.casefold() == "finetune2"
            ),
            -1,
        )
        if operation_index < 0:
            return None
        slider = min(max(self._depth_index, 0), len(_FINETUNE_SLIDERS) - 1)
        position, minimum, maximum, label = _FINETUNE_SLIDERS[slider]
        if position >= len(operations[operation_index].params):
            return None
        return {
            "operationIndex": operation_index,
            "parameterIndex": position,
            "minimum": minimum,
            "maximum": maximum,
            "current": self._float_value(slider),
            "label": label,
        }

    def _active_depth_target(self, operations: tuple[FilterOp, ...]) -> dict | None:
        if not operations:
            return None
        if self._active_effect == "finetune2":
            return self._finetune_target(operations)
        effect = self._active_effect
        params = resolve_effect_params(
            effect,
            *(self._edit._image_size if self._edit._image_size else (None, None)),
        )
        slider_index = self._depth_index
        if not (0 <= slider_index < len(params)) or params[slider_index].kind != "slider":
            slider_index = next((i for i, item in enumerate(params) if item.kind == "slider"), -1)
        if slider_index < 0:
            return None
        param = params[slider_index]
        operation_index = len(operations) - 1
        position = slider_index + 1
        operation = operations[operation_index]
        if position >= len(operation.params):
            return None
        try:
            current = float(self._active_values[slider_index])
        except (IndexError, TypeError, ValueError):
            current = float(param.default)
        return {
            "operationIndex": operation_index,
            "parameterIndex": position,
            "minimum": float(param.minimum),
            "maximum": float(param.maximum),
            "current": current,
            "label": param.label,
        }

    @staticmethod
    def _chain_depth_target(operations: tuple[FilterOp, ...], view_type: str) -> dict | None:
        for operation_index in range(len(operations) - 1, -1, -1):
            operation = operations[operation_index]
            if classify_effect(operation.name) != view_type:
                continue
            params = resolve_effect_params(operation.name)
            for index, param in enumerate(params):
                if param.kind != "slider" or index + 1 >= len(operation.params):
                    continue
                try:
                    current = float(operation.params[index + 1])
                except (TypeError, ValueError):
                    current = float(param.default)
                return {
                    "operationIndex": operation_index,
                    "parameterIndex": index + 1,
                    "minimum": float(param.minimum),
                    "maximum": float(param.maximum),
                    "current": current,
                    "label": param.label,
                }
        return None

    @staticmethod
    def _requires_photo_probe(operations: tuple[FilterOp, ...], target) -> bool:
        names = {item.name.casefold() for item in operations}
        if target:
            names.add(operations[target["operationIndex"]].name.casefold())
        return bool(names & _PHOTO_PROBE_EFFECTS)

    def _start_render(self) -> None:
        request = self._pending
        self._pending = None
        if not request or request.get("cached"):
            return
        self._last_cache_key = request["cacheKey"]
        self._last_target = request["target"]
        render_signals = RenderSignals()
        render_signals.finished.connect(
            self._on_render_finished, Qt.ConnectionType.QueuedConnection
        )
        self._pool.start(_RenderTask(self._job, request, render_signals))

    @Slot(int, object)
    def _on_render_finished(self, job: int, data: dict) -> None:
        if job != self._job:
            return
        request = self._pending
        if request is not None:
            return
        key = self._last_cache_key
        if key is not None:
            self._cache[key] = dict(data)
            self._cache.move_to_end(key)
            while len(self._cache) > 12:
                self._cache.popitem(last=False)
        self._set_marker(data, self._last_target)
        self._surface_data = data
        self.surfaceChanged.emit()

    def _set_marker(self, data: dict, target) -> None:
        # a mélységtengely csak a tónus-felületen csúszkaállás; a képsík-nézetek sora térbeli
        if not target or not data.get("rows") or data.get("kind") != "tone":
            data["hasMarker"] = False
            return
        data["minimum"] = target["minimum"]
        data["maximum"] = target["maximum"]
        span = target["maximum"] - target["minimum"]
        data["markerRow"] = max(
            0,
            min(
                len(data["rows"]) - 1,
                round((target["current"] - target["minimum"]) / span * (len(data["rows"]) - 1)),
            ),
        )
        data["hasMarker"] = True
        data["current"] = target["current"]

class EffectSliceSurface(QQuickPaintedItem):
    """Mesh-rajzoló QQuickPaintedItem; a QML Canvas-t nem használja."""

    surfaceDataChanged = Signal()
    angleChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._surface_data = {"kind": "none", "rows": []}
        self._angle = 0.0
        self.setAntialiasing(True)

    @Property("QVariantMap", notify=surfaceDataChanged)
    def surfaceData(self) -> dict:
        return self._surface_data

    @surfaceData.setter
    def surfaceData(self, value: dict) -> None:
        self._surface_data = dict(value or {})
        self.surfaceDataChanged.emit()
        self.update()

    @Property(float, notify=angleChanged)
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._angle = float(value) % 360.0
        self.angleChanged.emit()
        self.update()

    def paint(self, painter: QPainter) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        data = self._surface_data
        kind = data.get("kind", "none")
        if kind == "none":
            return
        dims = DIMENSIONS.get(kind, DIMENSIONS["tone"])
        project = make_projection(
            dims, BASE_AZIMUTH + self._angle, ELEVATION, self.boundingRect()
        )
        if kind == "color":
            paint_color_cube(painter, project, data.get("points") or [])
            return
        paint_frame(painter, project)
        if kind == "identity":
            # üres lánc: az azonos leképezés egyenes átlója
            paint_polyline(painter, project, 0.5, (0.0, 1.0), MARKER_COLOR, 1.5)
            return
        rows = data.get("rows") or []
        paint_surface(painter, project, rows, dims)
        if kind == "tone":
            self._paint_tone_marker(painter, project, rows)
        elif kind == "point" and rows:
            # a középen átmenő metszet
            paint_polyline(painter, project, 0.5, rows[len(rows) // 2], MARKER_COLOR, 1.2)

    def _paint_tone_marker(self, painter: QPainter, project, rows: list) -> None:
        data = self._surface_data
        if not data.get("hasMarker") or len(rows) < 2:
            return
        span = float(data.get("maximum", 1.0)) - float(data.get("minimum", 0.0))
        position = (
            (float(data.get("current", 0.0)) - float(data.get("minimum", 0.0))) / span
            if span
            else 0.0
        )
        channels = data.get("channels") or []
        if len(channels) == len(rows) and all(len(row) == 3 for row in channels):
            per_channel = [
                interpolate_row([row[index] for row in channels], position)
                for index in range(3)
            ]
            spread = max(
                (
                    max(abs(r - g), abs(g - b), abs(r - b))
                    for r, g, b in zip(*per_channel, strict=False)
                ),
                default=0.0,
            )
            if spread >= 0.01:
                for heights, color in zip(per_channel, CHANNEL_COLORS, strict=True):
                    paint_polyline(painter, project, position, heights, color, 1.2)
                return
        paint_polyline(
            painter, project, position, interpolate_row(rows, position), MARKER_COLOR, 1.5
        )


_QML_TYPES_REGISTERED = False


def register_qml_types() -> None:
    """A Python festett elemet a QML import előtt regisztrálja."""
    global _QML_TYPES_REGISTERED
    if _QML_TYPES_REGISTERED:
        return
    qmlRegisterType(EffectSliceSurface, "PicasaPy", 1, 0, "EffectSliceSurface")
    _QML_TYPES_REGISTERED = True

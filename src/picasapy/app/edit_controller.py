"""EditController: a szerkesztő-panel (QML) és az EditSession/ini-réteg
közti híd. A bekötést (QML-regisztráció, jelzések) az integrátor végzi."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from picasapy.edit.session import EditSession
from picasapy.ini import load_document, parse_document, save_document
from picasapy.ini.rect64 import Rect64, encode_rect64
from picasapy.scanner import PICASA_INI_NAME

from .edit_preview import EditPreviewProvider

_TOGGLE_NAMES = ("redeye", "enhance", "autolight", "autocolor")


class EditController(QObject):
    """A QML szerkesztő-panelhez tervezett híd: EditSession + ini-perzisztencia
    + EditPreviewProvider-regisztráció egy helyen."""

    revisionChanged = Signal()
    toolsChanged = Signal()

    def __init__(self, provider: EditPreviewProvider, parent=None) -> None:
        super().__init__(parent)
        self._provider = provider
        self._photo_id = ""
        self._image_path: Path | None = None
        self._ini_path: Path | None = None
        self._section_name = ""
        self._session = EditSession()
        self._revision = 0
        # undo/redo verem (#59): (filters-érték a művelet ELŐTT, művelet-kulcs)
        self._undo_stack: list[tuple[str, str]] = []
        self._redo_stack: list[tuple[str, str]] = []

    # -- QML-nek kitett tulajdonságok --------------------------------------

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        return self._revision

    @Property(str, notify=revisionChanged)
    def previewSource(self) -> str:
        """`image://editpreview/<id>?rev=<n>` vagy üres, ha nincs aktív
        szerkesztés. A QML-frissítés triggere a revision — a previewSource
        értéke (a ?rev= rész) attól függ, hogy a kép-URL biztosan változzon."""
        if not self._photo_id:
            return ""
        return f"image://editpreview/{self._photo_id}?rev={self._revision}"

    @Property(bool, notify=toolsChanged)
    def redeyeActive(self) -> bool:
        return self._session.has("redeye")

    @Property(bool, notify=toolsChanged)
    def enhanceActive(self) -> bool:
        return self._session.has("enhance")

    @Property(bool, notify=toolsChanged)
    def autolightActive(self) -> bool:
        return self._session.has("autolight")

    @Property(bool, notify=toolsChanged)
    def autocolorActive(self) -> bool:
        return self._session.has("autocolor")

    @Property(bool, notify=toolsChanged)
    def hasCrop(self) -> bool:
        """Van-e alkalmazott vágás — a „Visszavonás: Vágás" gombhoz (#51)."""
        return self._session.crop() is not None

    @Property(bool, notify=toolsChanged)
    def canUndo(self) -> bool:
        return bool(self._undo_stack)

    @Property(bool, notify=toolsChanged)
    def canRedo(self) -> bool:
        return bool(self._redo_stack)

    @Property(str, notify=toolsChanged)
    def undoAction(self) -> str:
        """A visszavonható művelet kulcsa (crop/tilt/redeye/…) — a gomb
        feliratához (#59)."""
        return self._undo_stack[-1][1] if self._undo_stack else ""

    @Property(str, notify=toolsChanged)
    def redoAction(self) -> str:
        return self._redo_stack[-1][1] if self._redo_stack else ""

    # -- műveletek ------------------------------------------------------------

    @Slot(str, str)
    def beginEdit(self, photo_id: str, image_path: str) -> None:
        """Szerkesztés indítása: a filters= betöltése az iniből (hiányzó
        ini/szekció/kulcs esetén üres lánc), regisztráció a previewnél."""
        path = Path(image_path)
        self._photo_id = photo_id
        self._image_path = path
        self._ini_path = path.parent / PICASA_INI_NAME
        self._section_name = path.name
        self._session = EditSession.from_value(self._read_filters_value())
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def endEdit(self) -> None:
        """Szerkesztés lezárása: leregisztrálás a previewnél, állapot ürítése."""
        if self._photo_id:
            self._provider.unregister(self._photo_id)
        self._photo_id = ""
        self._image_path = None
        self._ini_path = None
        self._section_name = ""
        self._session = EditSession()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(str)
    def toggleTool(self, name: str) -> None:
        """Paraméter nélküli szűrő be/ki (redeye, enhance, autolight,
        autocolor)."""
        self._require_active()
        if name.casefold() not in _TOGGLE_NAMES:
            raise ValueError(f"Érvénytelen szerkesztő-eszköz: {name!r}")
        self._push_undo(name.casefold())
        self._session = self._session.toggle(name)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(float, float, float, float)
    def applyCrop(self, x: float, y: float, w: float, h: float) -> None:
        """Relatív [0..1] (x, y, szélesség, magasság) → crop64.

        A UI-ról érkező határhibákat (pl. enyhén kilógó téglalap)
        [0..1]-re clampeljük; nem-UI (pl. nulla/negatív méret) hibára
        ValueError-t emelünk."""
        self._require_active()
        if w <= 0 or h <= 0:
            raise ValueError(f"A crop szélessége/magassága pozitív kell legyen: {w}x{h}")
        left = _clamp01(x)
        top = _clamp01(y)
        right = _clamp01(x + w)
        bottom = _clamp01(y + h)
        if right <= left or bottom <= top:
            raise ValueError(
                f"A clampelt crop üres lenne: ({left}, {top}, {right}, {bottom})"
            )
        rect = Rect64(left=left, top=top, right=right, bottom=bottom)
        self._push_undo("crop")
        self._session = self._session.set_crop(rect)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def clearCrop(self) -> None:
        """A crop64 eltávolítása."""
        self._require_active()
        self._push_undo("crop")
        self._session = self._session.clear_crop()
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(float)
    def setTilt(self, param: float) -> None:
        """A döntés-paraméter (-1..1 tartomány, Picasa-egység) beállítása.

        Picasa-paritás (#73): a skála-mezőbe 0.000000 kerül — a Picasa 3.x
        is így ír, a kitöltő skálát a megjelenítő számolja renderkor."""
        self._require_active()
        self._push_undo("tilt")
        self._session = self._session.set_tilt(param, 0.0)
        self._save()
        self._bump_revision()

    @Slot()
    def undo(self) -> None:
        """Az utolsó művelet visszavonása (a művelet ELŐTTI lánc áll vissza)."""
        if not self._undo_stack:
            return
        self._require_active()
        previous_value, action = self._undo_stack.pop()
        self._redo_stack.append((self._session.to_value(), action))
        self._session = EditSession.from_value(previous_value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def redo(self) -> None:
        """A visszavont művelet ismételt alkalmazása."""
        if not self._redo_stack:
            return
        self._require_active()
        redo_value, action = self._redo_stack.pop()
        self._undo_stack.append((self._session.to_value(), action))
        self._session = EditSession.from_value(redo_value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    # -- belső ------------------------------------------------------------

    def _push_undo(self, action: str) -> None:
        self._undo_stack.append((self._session.to_value(), action))
        self._redo_stack.clear()

    def _require_active(self) -> None:
        if not self._photo_id or self._image_path is None:
            raise ValueError("Nincs aktív szerkesztés (beginEdit hívása szükséges)")

    def _read_filters_value(self) -> str:
        if self._ini_path is None or not self._ini_path.exists():
            return ""
        section = load_document(self._ini_path).section(self._section_name)
        return (section.get("filters") if section else None) or ""

    def _save(self) -> None:
        assert self._ini_path is not None
        document = (
            load_document(self._ini_path)
            if self._ini_path.exists()
            else parse_document("")
        )
        if self._session.is_empty():
            document = document.with_removed(self._section_name, "filters")
        else:
            document = document.with_value(
                self._section_name, "filters", self._session.to_value()
            )
        # Picasa-paritás (#73): a vágás a filters= mellett külön
        # crop=rect64(...) kulcsba is kerül — a Picasa 3.x is így ír.
        crop = self._session.crop()
        if crop is not None:
            document = document.with_value(
                self._section_name, "crop", f"rect64({encode_rect64(crop)})"
            )
        else:
            document = document.with_removed(self._section_name, "crop")
        save_document(document, self._ini_path, backup=True)
        self._register_preview()

    def _register_preview(self) -> None:
        assert self._image_path is not None
        self._provider.register(self._photo_id, self._image_path, self._session.ops)

    def _bump_revision(self) -> None:
        self._revision += 1
        self.revisionChanged.emit()


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))

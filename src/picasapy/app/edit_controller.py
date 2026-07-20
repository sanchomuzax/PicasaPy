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

# redeye: teljes képes kapcsoló a régió-alapú eszközig (#116)
_TOGGLE_NAMES = ("redeye",)
# egygombos javítások: append-only rétegezés, levétel csak Visszavonással
_ONE_SHOT_NAMES = ("enhance", "autolight", "autocolor")
# Effektek (#20): append-only rétegek. A render-op nélküli effektek is a
# láncba kerülnek (round-trip), az előnézeten csak kimaradnak. A paramétert
# igénylők (pl. sat) dokumentált alapértékkel indulnak — a finomhangolt
# csúszkázás követő feladat.
_EFFECT_PARAMS: dict[str, tuple[str, ...]] = {
    "sat": ("1", "0.500000"),
}
_EFFECT_NAMES = (
    "sepia",
    "bw",
    "warm",
    "grain2",
    "tint",
    "sat",
    "radblur",
    "glow2",
    "ansel",
    "radsat",
    "dir_tint",
)


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

    # Gomb-tiltási szabály (#116): az egygombos javítás gombja addig tiltott,
    # amíg ugyanez a szűrő a lánc UTOLSÓ eleme — másik effekt után újra aktív.

    @Property(bool, notify=toolsChanged)
    def enhanceEnabled(self) -> bool:
        return not self._session.last_is("enhance")

    @Property(bool, notify=toolsChanged)
    def autolightEnabled(self) -> bool:
        return not self._session.last_is("autolight")

    @Property(bool, notify=toolsChanged)
    def autocolorEnabled(self) -> bool:
        return not self._session.last_is("autocolor")

    @Property(float, notify=toolsChanged)
    def tiltParam(self) -> float:
        """A mentett döntés-paraméter (-1..1 Picasa-egység), vagy 0.0, ha
        nincs tilt-szűrő a láncban. A döntés-csúszka ezzel áll be az eszköz
        megnyitásakor és lapozáskor a MENTETT értékre, ne 0-ra (#131)."""
        return self._session.tilt_param() or 0.0

    # Finomhangolás (#20): a négy csúszka a MENTETT finetune2 értékeire áll
    # az eszköz megnyitásakor és lapozáskor (a néző syncFinetuneSliders-e
    # ezekből tölt, a tilt-csúszka mintájára).

    @Property(float, notify=toolsChanged)
    def fillLight(self) -> float:
        return self._finetune_field("fill")

    @Property(float, notify=toolsChanged)
    def highlights(self) -> float:
        return self._finetune_field("highlights")

    @Property(float, notify=toolsChanged)
    def shadows(self) -> float:
        return self._finetune_field("shadows")

    @Property(float, notify=toolsChanged)
    def colorTemp(self) -> float:
        return self._finetune_field("temperature")

    @Property(bool, notify=toolsChanged)
    def hasFinetune(self) -> bool:
        """Van-e finomhangolás a láncban — a „Visszavonás" felirathoz."""
        return self._session.has_finetune()

    @Property(bool, notify=toolsChanged)
    def hasCrop(self) -> bool:
        """Van-e alkalmazott vágás — a „Visszavonás: Vágás" gombhoz (#51)."""
        return self._session.crop() is not None

    @Property("QVariant", notify=toolsChanged)
    def cropSelection(self):
        """A jelenlegi crop64 relatív [0..1] téglalapja (#71), vagy None ha
        nincs vágás — a Vágás eszköz ezzel tölti elő a meglévő kijelölést."""
        rect = self._session.crop()
        if rect is None:
            return None
        return {
            "x": rect.left,
            "y": rect.top,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
        }

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
        # Perzisztens, rétegenkénti undo (#116 visszajelzés): a mentett lánc
        # maga a réteg-verem — minden elemhez visszavonás-lépés jár, fordított
        # sorrendben, képváltás és újranyitás után is.
        self._undo_stack = self._seed_undo_from_chain(self._session)
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
        """Paraméter nélküli szűrő alkalmazása (#116).

        Egygombos javítás (enhance/autolight/autocolor): append-only réteg a
        lánc végére; ha ugyanez a szűrő a lánc utolsó eleme, a hívás no-op
        (a gomb ilyenkor a UI-ban tiltott — ez a védőkorlát). A redeye
        teljes képes be/ki kapcsoló a régió-alapú eszközig."""
        self._require_active()
        key = name.casefold()
        if key in _ONE_SHOT_NAMES:
            if self._session.last_is(key):
                return
            self._push_undo(key)
            self._session = self._session.apply(key)
        elif key in _TOGGLE_NAMES:
            self._push_undo(key)
            self._session = self._session.toggle(key)
        else:
            raise ValueError(f"Érvénytelen szerkesztő-eszköz: {name!r}")
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

    @Slot()
    def enterCropTool(self) -> None:
        """A Vágás eszköz megnyitásakor (#71): az előnézet a lánc crop64
        NÉLKÜLI változatát mutatja, hogy a teljes (vágatlan) forráskép
        látsszon — a meglévő kijelölést a `cropSelection` alapján a QML
        overlay rajzolja rá. Nem ír inibe, nem tol undo-lépést."""
        self._require_active()
        self._register_preview(self._session.clear_crop())
        self._bump_revision()

    @Slot()
    def exitCropTool(self) -> None:
        """A Vágás eszköz bezárásakor (Mégse) visszaáll a rendes, a
        ténylegesen mentett crop64-et is tartalmazó előnézetre."""
        self._require_active()
        self._register_preview()
        self._bump_revision()

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

    @Slot(float)
    def previewTilt(self, param: float) -> None:
        """Élő forgatás-előnézet a csúszka húzása közben (#72): a képet a
        pillanatnyi paraméterrel újrarenderli, de NEM ír ini-be és NEM tol
        undo-lépést — a tényleges mentés az elengedéskor hívott setTilt-tel
        történik."""
        self._require_active()
        preview_session = self._session.set_tilt(param, 0.0)
        self._register_preview(preview_session)
        self._bump_revision()

    @Slot(float, float, float, float)
    def previewFinetune(
        self, fill: float, highlights: float, shadows: float, temperature: float
    ) -> None:
        """Élő finomhangolás-előnézet a csúszkák húzása közben (#20): a képet
        a pillanatnyi négy értékkel újrarenderli, de NEM ír ini-be és NEM tol
        undo-lépést — a mentés az elengedéskor hívott setFinetune-nal történik
        (a previewTilt mintájára)."""
        self._require_active()
        preview_session = self._session.set_finetune(
            fill=fill, highlights=highlights, shadows=shadows, temperature=temperature
        )
        self._register_preview(preview_session)
        self._bump_revision()

    @Slot(float, float, float, float)
    def setFinetune(
        self, fill: float, highlights: float, shadows: float, temperature: float
    ) -> None:
        """A finomhangolás négy csúszkájának mentése egy finetune2 rétegbe.

        A csúszka elengedésekor hívódik: undo-lépést tol és ini-be ír. Ha
        mind a négy érték semleges (0), a réteget eltávolítja — így a
        visszahúzott csúszkák nem hagynak fölösleges no-op finetune2-t."""
        self._require_active()
        self._push_undo("finetune")
        if fill == 0.0 and highlights == 0.0 and shadows == 0.0 and temperature == 0.0:
            self._session = self._session.clear_finetune()
        else:
            self._session = self._session.set_finetune(
                fill=fill,
                highlights=highlights,
                shadows=shadows,
                temperature=temperature,
            )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(str)
    def applyEffect(self, name: str) -> None:
        """Effekt réteg a lánc végére (#20): append-only, undo-lépéssel.

        Az ismeretlen név ValueError; a paramétert igénylő effektek (pl. sat)
        dokumentált alapértékkel kerülnek be (`_EFFECT_PARAMS`)."""
        self._require_active()
        key = name.casefold()
        if key not in _EFFECT_NAMES:
            raise ValueError(f"Érvénytelen effekt: {name!r}")
        self._push_undo(key)
        self._session = self._session.append_effect(key, _EFFECT_PARAMS.get(key, ("1",)))
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

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

    @staticmethod
    def _seed_undo_from_chain(session: EditSession) -> list[tuple[str, str]]:
        """A mentett filters-láncból épített undo-verem: az i. lépés
        visszavonása az első i elemű láncot állítja vissza. Az ismeretlen
        (pl. valódi Picasa által írt) szűrők is rétegként vonhatók vissza —
        a Visszavonásig a round-trip elv szerint érintetlenek maradnak."""
        entries: list[tuple[str, str]] = []
        for index, op in enumerate(session.ops):
            previous_value = EditSession(ops=session.ops[:index]).to_value()
            entries.append((previous_value, _action_key(op.name)))
        return entries

    def _finetune_field(self, field: str) -> float:
        """A mentett finetune2 adott csúszka-értéke, vagy 0.0, ha nincs
        finomhangolás — a QML-csúszkák így a mentett értékre állnak (#20)."""
        values = self._session.finetune_values()
        return getattr(values, field) if values is not None else 0.0

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

    def _register_preview(self, session: EditSession | None = None) -> None:
        assert self._image_path is not None
        active_session = session if session is not None else self._session
        self._provider.register(self._photo_id, self._image_path, active_session.ops)

    def _bump_revision(self) -> None:
        self._revision += 1
        self.revisionChanged.emit()


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _action_key(filter_name: str) -> str:
    """Szűrő-név → művelet-kulcs a Visszavonás-felirathoz (crop64→crop)."""
    key = filter_name.casefold()
    if key == "crop64":
        return "crop"
    return key

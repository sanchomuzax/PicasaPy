"""A vágóeszköz tulajdonságai, javaslatai és parancsai."""

from __future__ import annotations

import logging
import math
import threading

from PySide6.QtCore import QMetaObject, Qt
from picasapy.edit.recrop import recrop, vegi_crop_frissitheto
from picasapy.halozati_ut import fajlrendszer_gyoker

from .edit_controller_shared import (
    EditSession,
    FilterOp,
    Path,
    Property,
    Rect64,
    Slot,
    _clamp01,
    encode_rect64,
    load_or_empty,
    normalize_crop_ops,
    parse_faces,
    suggest_crops,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals
from .edit_preview_source import _decode_source

_CROP_RESULT_LOCK = threading.Lock()
_log = logging.getLogger(__name__)


def _crop_tilt_utani_visszavetitese(
    rect: Rect64, width: int, height: int, tilt_ops: tuple[FilterOp, ...]
) -> Rect64 | None:
    """A kiegyenesített kijelölést a forrásképre vetíti (#7415).

    A megjelenített kijelölés négy sarkán a kiegyenesítés cél→forrás
    mátrixa fut. A forrásbeli kivágás magassága a vetített négyszög
    befoglaló magassága; az arányt megtartó méretet felfelé kerekítjük,
    a felső élhez és a befoglaló vízszintes közepéhez igazítva.
    """
    from picasapy.render.chain import _TILT_RADIANS_PER_UNIT
    from picasapy.render.ops_geometry import tilt_matrix

    matrices = []
    for op in tilt_ops:
        params = op.float_params()
        if params:
            matrices.append(
                tilt_matrix(width, height, params[0] * _TILT_RADIANS_PER_UNIT)
            )
    if not matrices:
        return None

    x0, x1 = rect.left * width, rect.right * width
    y0, y1 = rect.top * height, rect.bottom * height
    drag_width, drag_height = x1 - x0, y1 - y0
    if drag_width <= 0.0 or drag_height <= 0.0:
        return None

    pontok = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    # A láncban az utolsó tilt van legközelebb a kijelölt célképhez.
    for matrix in reversed(matrices):
        m0, m1, m2, m3, m4, m5 = matrix
        pontok = [
            (m0 * x + m1 * y + m2, m3 * x + m4 * y + m5)
            for x, y in pontok
        ]

    min_x = min(x for x, _ in pontok)
    max_x = max(x for x, _ in pontok)
    min_y = min(y for _, y in pontok)
    max_y = max(y for _, y in pontok)
    k = (max_y - min_y) / drag_height
    crop_width = min(width, math.ceil(drag_width * k))
    crop_height = min(height, math.ceil(drag_height * k))
    left = (min_x + max_x - crop_width) / 2.0
    top = min_y
    # A teljes kép határán a méret maradjon egész, a kijelölés pedig férjen
    # a forrásba; a mért minták egyik szélt sem érik el.
    left = max(0.0, min(left, width - crop_width))
    top = max(0.0, min(top, height - crop_height))
    return Rect64(
        left / width,
        top / height,
        (left + crop_width) / width,
        (top + crop_height) / height,
    )

class EditControllerCropMixin:
    """A vágóeszköz tulajdonságai, javaslatai és parancsai."""

    @Property(bool, notify=_Signals.hasCropChanged)
    def hasCrop(self) -> bool:
        """Van-e alkalmazott vágás — a „Visszavonás: Vágás" gombhoz (#51)."""
        return self.crop() is not None


    @staticmethod
    def _crop_ops(session: EditSession) -> tuple[FilterOp, ...]:
        """A szerkesztési lánc vágás-rétegei, az eredeti sorrendben."""
        return tuple(op for op in session.ops if op.matches("crop64"))


    def _crop_value_for_session(self, session: EditSession) -> tuple[str | None, bool]:
        """A megnyitáskori crop= vagy az azóta, a felhasználó által vágott crop.

        Régi crop64 rétegek csak akkor lesznek hatályosak, ha a képszekció
        megnyitásakor már volt crop=, vagy a felhasználó azóta módosította a
        vágás-rétegeket. Így egy független effekt nem éleszti fel az előzményt.
        """
        if self._crop_ops(session) != self._opening_crop_ops:
            rect = session.crop()
            value = f"rect64({encode_rect64(rect)})" if rect is not None else None
            return value, True
        return self._opening_crop, self._opening_crop_ini_readable


    def crop(self) -> Rect64 | None:
        """A munkamenet hatályos vágása a megnyitáskori crop= szabályával."""
        if not self._session.ops:
            # Üres láncban nincs `crop64`, így vágás sincs, akármi a `crop=`
            # (a normalizálás üres láncból mindig üres láncot ad). #6688: a
            # `hasCrop` induláskor, fotó nélkül is lefut, és a normalizálás
            # miatt be kellene tölteni a `picasapy.render` csomagot.
            return None
        # ugyanabból a normalizálásból, amelyik renderel: a felület és a kép
        # nem válhat el (árva `crop=` lánc-vágás nélkül → nincs aktív vágás)
        value, readable = self._crop_value_for_session(self._session)
        ops = normalize_crop_ops(self._session.ops, value, crop_ini_readable=readable)
        return EditSession(ops=ops).crop()


    @Property("QVariant", notify=_Signals.cropSelectionChanged)
    def cropSelection(self):
        """A jelenlegi crop64 relatív [0..1] téglalapja (#71), vagy None ha
        nincs vágás — a Vágás eszköz ezzel tölti elő a meglévő kijelölést."""
        rect = self.crop()
        if rect is None:
            return None
        return {
            "x": rect.left,
            "y": rect.top,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
        }


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
        tilt_ops = tuple(op for op in self._session.ops if op.matches("tilt"))
        if tilt_ops and self._image_path is not None:
            source_image = self._provider.source_image(self._kulcs, self._image_path)
            if source_image is not None:
                height, width = source_image.shape[:2]
                visszavetitett = _crop_tilt_utani_visszavetitese(
                    rect, width, height, tilt_ops
                )
                if visszavetitett is not None:
                    rect = visszavetitett
        # #7367: az eredeti Picasa a lánc VÉGÉN álló `crop64`-et írja át
        # (`0x006b4300`), minden más végrekordnál új elemet fűz hozzá (#1553).
        # A helyben frissítés nem hoz új Visszavonás-lépést és nem ürít redót:
        # egy Visszavonás a vágás előtti állapotot hozza vissza. A VÁLTOZATLAN
        # kijelölésnél hozzá sem nyúlunk az inihez (#1550: a változtatás
        # nélküli Alkalmaz nem írhatja át a képet), ez saját óvatossági
        # döntés, az eredetiről erre nincs adatunk.
        hatalyos = self.crop()
        if hatalyos is not None and encode_rect64(hatalyos) == encode_rect64(rect):
            return
        if not vegi_crop_frissitheto(self._session):
            self._push_undo("crop")
        self._session = recrop(self._session, rect)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def applyEmptyCrop(self) -> None:
        """Üres kijelöléssel nyomott Alkalmaz (#7367, `0x006b4300`).

        `crop64` végű láncnál az utolsó vágás törlődik, más végrekordnál a
        lánc nem változik. Eltérés az eredetitől: a törlés Visszavonás-lépést
        kap, hogy a kivett vágás ne vesszen el visszahozhatatlanul."""
        self._require_active()
        if not vegi_crop_frissitheto(self._session):
            return
        self._push_undo("crop")
        self._session = recrop(self._session, None)
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


    @Property("QVariant", notify=_Signals.cropSuggestionsChanged)
    def cropSuggestions(self):
        """A vágás-panel HÁROM automatikus javaslata (#448).

        Minden elem `{key, x, y, w, h}` — a `key` a felirat-kulcsa (a
        fordítás a QML dolga), a többi közvetlenül az `applyCrop`-nak adható.
        Aktív szerkesztés nélkül üres lista.

        A javaslatok a MENTETT lánc nélküli, nyers forrásképből számolnak: a
        Vágás eszköz is a vágatlan képet mutatja (`enterCropTool`), tehát a
        javaslat arra a képre vonatkozik, amit a felhasználó épp lát.
        """
        if not self._photo_id or self._image_path is None:
            return []
        if fajlrendszer_gyoker(self._image_path) is not None:
            if getattr(self, "_network_edit_load_pending", False):
                return []
            if getattr(self, "_network_edit_load_failed", False):
                return []
            key = (
                getattr(self, "_network_edit_generation", 0),
                str(self._image_path),
                self._crop_aspect,
            )
            if getattr(self, "_network_crop_suggestions_key", None) == key:
                return list(self._network_crop_suggestions)
            self._queue_network_crop_suggestions(key)
            return []
        image = self._provider.source_image(self._kulcs, self._image_path)
        if image is None:
            return []
        faces = self._saved_face_rects()
        suggestions = suggest_crops(image, faces=faces, aspect=self._crop_aspect)
        return [
            {
                "key": suggestion.key,
                "x": suggestion.rect.left,
                "y": suggestion.rect.top,
                "w": suggestion.rect.right - suggestion.rect.left,
                "h": suggestion.rect.bottom - suggestion.rect.top,
            }
            for suggestion in suggestions
        ]


    def _queue_network_crop_suggestions(self, key: tuple) -> None:
        """A hálózati kép dekódolása és a javaslatok számítása workerben fut."""
        pending = getattr(self, "_network_crop_suggestions_pending", None)
        if pending is None:
            pending = set()
            self._network_crop_suggestions_pending = pending
            self._network_crop_suggestion_results = {}
        with _CROP_RESULT_LOCK:
            if key in pending:
                return
            pending.add(key)
        generation, image_path, aspect = key
        path = Path(image_path)
        faces = self._saved_face_rects()
        color_managed = self._provider.color_management

        def worker() -> None:
            try:
                image = _decode_source(path, color_managed=color_managed)
                suggestions = suggest_crops(image, faces=faces, aspect=aspect) if image is not None else ()
                results = [
                    {
                        "key": suggestion.key,
                        "x": suggestion.rect.left,
                        "y": suggestion.rect.top,
                        "w": suggestion.rect.right - suggestion.rect.left,
                        "h": suggestion.rect.bottom - suggestion.rect.top,
                    }
                    for suggestion in suggestions
                ]
            except Exception as error:  # noqa: BLE001 - hálózati kép hibája üres javaslatot ad
                _log.warning("A hálózati vágási javaslat nem számítható ki (%s): %s", path, error)
                results = []
            with _CROP_RESULT_LOCK:
                self._network_crop_suggestion_results[key] = results
            QMetaObject.invokeMethod(
                self,
                "_apply_network_crop_suggestions",
                Qt.ConnectionType.QueuedConnection,
            )

        self._start_background(worker, name="picasapy-network-crop-suggestions", busy=False)


    @Slot()
    def _apply_network_crop_suggestions(self) -> None:
        """Az elkészült hálózati javaslatok átadása a GUI-kötésnek."""
        with _CROP_RESULT_LOCK:
            results = dict(self._network_crop_suggestion_results)
            self._network_crop_suggestion_results.clear()
            self._network_crop_suggestions_pending.difference_update(results)
        generation = getattr(self, "_network_edit_generation", -1)
        path = str(getattr(self, "_image_path", ""))
        aspect = self._crop_aspect
        for key, suggestions in results.items():
            if key == (generation, path, aspect):
                self._network_crop_suggestions_key = key
                self._network_crop_suggestions = suggestions
                self.cropSuggestionsChanged.emit()


    @Slot(float)
    def setCropAspect(self, aspect: float) -> None:
        """A javaslatokhoz használt képarány (szélesség/magasság); 0 = a
        forráskép arányát tartjuk (#448). A vágó-panel arány-választója
        hívja, hogy a javaslatok a KIVÁLASZTOTT arányban szülessenek."""
        self._crop_aspect = aspect if aspect and aspect > 0 else None
        self._bump_revision()


    def _saved_face_rects(self) -> tuple[Rect64, ...]:
        """A fotóhoz mentett arc-régiók (#448 javaslatok bemenete).

        A `.picasa.ini` `faces=` kulcsából, közvetlenül — hiányzó/sérült
        adatnál üres tuple (a #301-elv szerint idegen adat nem szökhet ki
        kivétellel, és arc nélkül a javaslatok a tartalom-alapú ágra esnek).
        """
        if self._ini_path is None:
            return ()
        if getattr(self, "_network_edit_load_pending", False):
            return ()
        try:
            document = (
                self._current_ini_document()
                if hasattr(self, "_current_ini_document")
                else load_or_empty(self._ini_path)
            )
            section = document.section(self._section_name)
            raw = section.get("faces") if section is not None else None
            if not raw:
                return ()
            return tuple(face.rect for face in parse_faces(raw))
        except (OSError, ValueError):
            return ()


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


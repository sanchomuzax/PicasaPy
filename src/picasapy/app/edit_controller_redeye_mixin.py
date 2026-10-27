"""A vörösszem-automatikus és kézi régióinak kezelése."""

from __future__ import annotations

from .edit_controller_shared import (
    AZONOSSAG,
    EditSession,
    EyeCircle64,
    Matrix,
    Property,
    Rect64,
    Slot,
    _RedeyeBufferState,
    _clamp01,
    invertal,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

class EditControllerRedeyeMixin:
    """A vörösszem-automatikus és kézi régióinak kezelése."""

    @Property(bool, notify=_Signals.toolsChanged)
    def hasSavedRedeye(self) -> bool:
        """Van-e a képen **MENTETT** vörösszem-javítás.

        ⚠️ #2393: ez **NEM** a nyitott eszköz jelzője. A neve korábban
        `redeyeActive` volt, ami ütközött az `EditorPanel.qml:132`
        azonos nevű, de ELLENTÉTES jelentésű mód-kapcsolójával (ott a
        csempe „benyomva" állapota, vagyis hogy az eszköz NYITVA van).

        A névazonosság már félrevitt egy jegyet: a #1485 duplikált
        állapotnak nézte a kettőt, és a panel összekötését írta elő. Az a
        javítás hibás lett volna — egy mentett javítású képnél a csempe
        állandóan benyomva látszana.

        Ugyanez a megkülönböztetés áll a `hasRetouch`-nál is, közvetlenül
        alább (#116).
        """
        return self._session.has("redeye")


    @Property(int, notify=_Signals.revisionChanged)
    def redeyeRegionCount(self) -> int:
        """Az automatikus és kézi, MÉG NEM alkalmazott keretek száma."""
        return len(self._redeye_regions) + len(self._redeye_auto_rectangles())


    @Property(bool, notify=_Signals.revisionChanged)
    def redeyeResetAvailable(self) -> bool:
        """Van-e automatikus vagy kézi javítás, amelyet a Reset visszavehet."""
        return bool(
            self._redeye_regions
            or self._redeye_eye_circles
            or self._redeye_full_image_fallback
        )


    @Property(bool, notify=_Signals.revisionChanged)
    def canUndoRedeyeRegion(self) -> bool:
        """Van-e régiónkénti visszavonható lépés a vörösszem-pufferben (NEM
        a globális Visszavonás-verem, ld. `undoRedeyeRegion`)."""
        return bool(self._redeye_region_undo)


    @Property("QVariant", notify=_Signals.revisionChanged)
    def redeyeRegions(self):
        """A puffer régiói relatív [0..1] `{x, y, w, h}` szótárakként — a QML
        overlay ebből rajzolja a kézi és automatikus kijelölő-négyzeteket.
        Az automatikus körökből négyzet lesz, a renderelő azonban továbbra is
        az eredeti körkoordinátát használja a tényleges javításhoz."""
        return [
            {
                "x": rect.left,
                "y": rect.top,
                "w": rect.right - rect.left,
                "h": rect.bottom - rect.top,
            }
            for rect in (
                *self._redeye_auto_rectangles(),
                *self._redeye_manual_overlay_rectangles(),
            )
        ]


    @Property(int, notify=_Signals.revisionChanged)
    def redeyeFoundCount(self) -> int:
        """Az automatika utolsó futásának találat-száma, vagy -1, ha még nem
        futott. A panel ebből írja ki a Picasa sikerüzenetét („Picasa has
        found and corrected red eye(s)"), illetve a talált-nulla esetet."""
        return self._redeye_found


    @Property(bool, notify=_Signals.revisionChanged)
    def canReapplyRedeyeAuto(self) -> bool:
        """Az Auto gomb csak akkor él, ha a felhasználó visszavont javítást."""
        return self._redeye_can_reapply_auto


    @Property(bool, notify=_Signals.revisionChanged)
    def redeyeAutoReset(self) -> bool:
        """A Reset utáni állapotüzenet (`AutoFixRedoMessage`) látható-e."""
        return self._redeye_reset_message


    @staticmethod
    def _map_redeye_rectangle(
        rect: Rect64,
        matrix: Matrix,
        source_size: tuple[int, int],
        output_size: tuple[int, int],
    ) -> Rect64:
        """Normalizált téglalap leképezése és az eredmény képhatáron tartása."""
        source_width, source_height = source_size
        output_width, output_height = output_size
        if min(source_width, source_height, output_width, output_height) <= 0:
            return Rect64(0.0, 0.0, 0.0, 0.0)
        (a, b, c), (d, e, f) = matrix
        corners = (
            (rect.left * source_width, rect.top * source_height),
            (rect.right * source_width, rect.top * source_height),
            (rect.right * source_width, rect.bottom * source_height),
            (rect.left * source_width, rect.bottom * source_height),
        )
        mapped = tuple(
            (a * x + b * y + c, d * x + e * y + f) for x, y in corners
        )
        left = max(0.0, min(point[0] for point in mapped))
        top = max(0.0, min(point[1] for point in mapped))
        right = min(float(output_width), max(point[0] for point in mapped))
        bottom = min(float(output_height), max(point[1] for point in mapped))
        if right <= left or bottom <= top:
            return Rect64(0.0, 0.0, 0.0, 0.0)
        return Rect64(
            left=left / output_width,
            top=top / output_height,
            right=right / output_width,
            bottom=bottom / output_height,
        )


    def _redeye_manual_overlay_rectangles(self) -> tuple[Rect64, ...]:
        eye_size = self._redeye_eye_image_size or self._image_size or (0, 0)
        overlay_size = self._redeye_eye_overlay_size or self._image_size or (0, 0)
        return tuple(
            self._map_redeye_rectangle(
                rect, self._redeye_eye_to_overlay, eye_size, overlay_size
            )
            for rect in self._redeye_regions
        )


    def _redeye_region_in_eye_coordinates(self, rect: Rect64) -> Rect64:
        eye_size = self._redeye_eye_image_size or self._image_size or (0, 0)
        overlay_size = self._redeye_eye_overlay_size or self._image_size or (0, 0)
        try:
            inverse = invertal(self._redeye_eye_to_overlay)
        except ValueError:
            return Rect64(0.0, 0.0, 0.0, 0.0)
        return self._map_redeye_rectangle(rect, inverse, overlay_size, eye_size)


    def _redeye_auto_rectangles(self) -> tuple[Rect64, ...]:
        """Az automatikus szemkörök négyzetes, normált keretei (#4541)."""
        eye_width, eye_height = self._redeye_eye_image_size or self._image_size or (0, 0)
        view_width, view_height = (
            self._redeye_eye_overlay_size or self._image_size or (0, 0)
        )
        if min(eye_width, eye_height, view_width, view_height) <= 0:
            return ()
        (a, b, c), (d, e, f) = self._redeye_eye_to_overlay
        rectangles = []
        for x, y, radius in self._redeye_eye_circles:
            center_x = x * eye_width
            center_y = y * eye_height
            radius_px = radius * min(eye_width, eye_height)
            corners = (
                (center_x - radius_px, center_y - radius_px),
                (center_x + radius_px, center_y - radius_px),
                (center_x + radius_px, center_y + radius_px),
                (center_x - radius_px, center_y + radius_px),
            )
            def vetit(point: tuple[float, float]) -> tuple[float, float]:
                px, py = point
                return a * px + b * py + c, d * px + e * py + f

            mapped = tuple(vetit(point) for point in corners)
            mapped_center = vetit((center_x, center_y))
            mapped_width = max(point[0] for point in mapped) - min(
                point[0] for point in mapped
            )
            mapped_height = max(point[1] for point in mapped) - min(
                point[1] for point in mapped
            )
            side = max(mapped_width, mapped_height)
            left = max(0.0, mapped_center[0] - side / 2.0)
            top = max(0.0, mapped_center[1] - side / 2.0)
            right = min(float(view_width), mapped_center[0] + side / 2.0)
            bottom = min(float(view_height), mapped_center[1] + side / 2.0)
            if right <= left or bottom <= top:
                rectangles.append(Rect64(0.0, 0.0, 0.0, 0.0))
            else:
                rectangles.append(
                    Rect64(
                        left=left / view_width,
                        top=top / view_height,
                        right=right / view_width,
                        bottom=bottom / view_height,
                    )
                )
        return tuple(rectangles)


    def _push_redeye_region_undo(self) -> None:
        """A kézi és automatikus puffer egy közös Undo-lépést kap."""
        self._redeye_region_undo.append(
            _RedeyeBufferState(
                regions=self._redeye_regions,
                eye_circles=self._redeye_eye_circles,
                eye_image_size=self._redeye_eye_image_size,
                eye_overlay_size=self._redeye_eye_overlay_size,
                eye_to_overlay=self._redeye_eye_to_overlay,
                full_image_fallback=self._redeye_full_image_fallback,
                found=self._redeye_found,
                can_reapply_auto=self._redeye_can_reapply_auto,
                reset_message=self._redeye_reset_message,
            )
        )


    @Slot()
    def runRedeyeAuto(self) -> None:
        """„Auto": az automatikus felismerés (újra)futtatása.

        Az app-oldali felismerő visszaadja a szemköröket és az azokon belüli
        találatszámot. A körök az előnézeti FilterOp-paraméterként jutnak a
        rendererhez; hiányzó modellnél a régi teljes képes út kerül jelölésre.
        """
        self._require_active()
        crop, crop_ini_readable = self._crop_value_for_session(self._session)
        (
            self._redeye_found,
            eye_circles,
            self._redeye_eye_image_size,
            self._redeye_eye_overlay_size,
            self._redeye_eye_to_overlay,
        ) = self._provider.redeye_auto_result_with_size(
            self._kulcs,
            self._image_path,
            self._session.redeye_detection_ops(),
            self._session.redeye_post_detection_ops(),
            crop,
            crop_ini_readable,
        )
        if self._redeye_eye_image_size is None:
            self._redeye_eye_image_size = self._image_size
        if self._redeye_eye_overlay_size is None:
            self._redeye_eye_overlay_size = self._image_size
        self._redeye_eye_circles = eye_circles or ()
        self._redeye_full_image_fallback = eye_circles is None
        self._redeye_can_reapply_auto = False
        self._redeye_reset_message = False
        self._register_preview(self._session_with_redeye_pending())
        self._bump_revision()


    @Slot()
    def enterRedeyeTool(self) -> None:
        """A Vörösszem eszköz megnyitása: a puffer a MENTETT kézi régiókkal
        indul, és az előnézeten AZONNAL lefut az automatikus vörösszem-
        eltávolítás is (akkor is, ha eddig nem volt `redeye` a láncban) —
        nem ír inibe, nem tol undo-lépést."""
        self._require_active()
        self._redeye_regions = self._session.redeye_regions()
        self._redeye_region_undo = []
        self.runRedeyeAuto()


    @Slot()
    def exitRedeyeTool(self) -> None:
        """A Vörösszem eszköz bezárása (Mégse): a puffer eldobása, visszaáll
        a ténylegesen mentett előnézet — a mentett állapot érintetlen."""
        self._require_active()
        self._redeye_regions = ()
        self._redeye_region_undo = []
        self._redeye_eye_circles = ()
        self._redeye_eye_image_size = None
        self._redeye_eye_overlay_size = None
        self._redeye_eye_to_overlay = AZONOSSAG
        self._redeye_full_image_fallback = False
        self._redeye_found = -1
        self._redeye_can_reapply_auto = False
        self._redeye_reset_message = False
        self._register_preview()
        self._bump_revision()


    @Slot(float, float, float, float)
    def addRedeyeRegion(self, x: float, y: float, w: float, h: float) -> None:
        """Egy kézzel húzott téglalap hozzáadása a pufferhez (relatív [0..1]).

        A UI-ról érkező határhibákat [0..1]-re clampeljük; a nulla méretű
        (puszta kattintás) kijelölés néma no-op — nem hiba, a felhasználó
        egyszerűen nem húzott téglalapot."""
        self._require_active()
        left = _clamp01(min(x, x + w))
        top = _clamp01(min(y, y + h))
        right = _clamp01(max(x, x + w))
        bottom = _clamp01(max(y, y + h))
        if right <= left or bottom <= top:
            return
        region = self._redeye_region_in_eye_coordinates(
            Rect64(left=left, top=top, right=right, bottom=bottom)
        )
        if region.right <= region.left or region.bottom <= region.top:
            return
        self._push_redeye_region_undo()
        self._redeye_regions = (
            *self._redeye_regions,
            region,
        )
        self._register_preview(self._session_with_redeye_pending())
        self._bump_revision()


    @Slot(float, float, result=bool)
    def removeRedeyeRegionAt(self, x: float, y: float) -> bool:
        """A megadott ponton lévő kijelölő-négyzet TÖRLÉSE (#604).

        Az eredeti eszköz mindhárom útmutató szövege ezt ígéri:
        *„Megjegyzés: a keretbe kattintva visszavonhatja a változást."*
        (`RedEye::AutoFixedMessage`, `::DragToSelectMessage`,
        `::AutoFixRedoMessage`) — vagyis a keretek EGYEDILEG is törölhetők, nem
        csak az utolsó (`undoRedeyeRegion`) vagy mind (`resetRedeyeRegions`).

        ⚠️ **Csak az Alkalmazás ELŐTT.** A javítás alkalmazáskor a mentett
        képpontokba kerül, és a keretek koordinátáit nem tároljuk — az eredeti
        maga is figyelmeztet rá (`IDS_CONFIRM_UNDO_REDEYE`: a
        vörösszemjavítások nem állíthatók helyre). Ez a hívás tehát a
        PUFFERT szerkeszti.

        Átfedő kereteknél a **legutóbb felvett** nyer (a lista vége felől
        keresünk): a felhasználó azt látja legfelül, és arra kattint.

        Visszatérés: törölt-e valamit. `False`, ha a pont egyetlen kereten sem
        volt — a hívó ebből tudja, hogy a kattintás nem törlés volt.
        """
        self._require_active()
        manual_overlay_rectangles = self._redeye_manual_overlay_rectangles()
        # A Repeater a detektált kereteket a kézi régiók elé rajzolja, így
        # az átfedésben a kézi, utoljára felvett keret marad legfelül.
        for index in range(len(manual_overlay_rectangles) - 1, -1, -1):
            rect = manual_overlay_rectangles[index]
            if rect.right <= rect.left or rect.bottom <= rect.top:
                continue
            if rect.left <= x <= rect.right and rect.top <= y <= rect.bottom:
                self._push_redeye_region_undo()
                self._redeye_regions = (
                    *self._redeye_regions[:index],
                    *self._redeye_regions[index + 1 :],
                )
                self._register_preview(self._session_with_redeye_pending())
                self._bump_revision()
                return True
        auto_rectangles = self._redeye_auto_rectangles()
        for index in range(len(auto_rectangles) - 1, -1, -1):
            rect = auto_rectangles[index]
            if rect.right <= rect.left or rect.bottom <= rect.top:
                continue
            if rect.left <= x <= rect.right and rect.top <= y <= rect.bottom:
                self._push_redeye_region_undo()
                self._redeye_eye_circles = (
                    *self._redeye_eye_circles[:index],
                    *self._redeye_eye_circles[index + 1 :],
                )
                self._redeye_can_reapply_auto = True
                self._register_preview(self._session_with_redeye_pending())
                self._bump_revision()
                return True
        return False


    @Slot(float, float, result=bool)
    def redeyeRegionHitAt(self, x: float, y: float) -> bool:
        """Van-e kijelölő-négyzet a megadott ponton (#604)?

        A felület ebből állítja a kurzort: a keret fölött jelezze, hogy
        kattintható. Állapotot NEM változtat — a kurzor-kötés minden
        mozgásra lefut, egy mellékhatásos vizsgálat itt drága és hibás is
        lenne."""
        return any(
            rect.right > rect.left
            and rect.bottom > rect.top
            and rect.left <= x <= rect.right
            and rect.top <= y <= rect.bottom
            for rect in (
                *self._redeye_auto_rectangles(),
                *self._redeye_manual_overlay_rectangles(),
            )
        )


    @Slot()
    def undoRedeyeRegion(self) -> None:
        """Az utoljára húzott téglalap visszavonása a pufferben."""
        if not self._redeye_region_undo:
            return
        self._require_active()
        state = self._redeye_region_undo.pop()
        self._redeye_regions = state.regions
        self._redeye_eye_circles = state.eye_circles
        self._redeye_eye_image_size = state.eye_image_size
        self._redeye_eye_overlay_size = state.eye_overlay_size
        self._redeye_eye_to_overlay = state.eye_to_overlay
        self._redeye_full_image_fallback = state.full_image_fallback
        self._redeye_found = state.found
        self._redeye_can_reapply_auto = state.can_reapply_auto
        self._redeye_reset_message = state.reset_message
        self._register_preview(self._session_with_redeye_pending())
        self._bump_revision()


    @Slot()
    def resetRedeyeRegions(self) -> None:
        """Minden automatikus és kézi vörösszem-javítás visszavonása (#4541).

        A változás egy régiónkénti Undo-lépés, és az Auto gomb újra
        alkalmazhatja az automatikus javítást. Üres pufferen néma no-op.
        """
        if not self.redeyeResetAvailable:
            return
        self._require_active()
        self._push_redeye_region_undo()
        self._redeye_regions = ()
        self._redeye_eye_circles = ()
        self._redeye_eye_image_size = None
        self._redeye_eye_overlay_size = None
        self._redeye_eye_to_overlay = AZONOSSAG
        self._redeye_full_image_fallback = False
        self._redeye_found = -1
        self._redeye_can_reapply_auto = True
        self._redeye_reset_message = True
        self._register_preview(self._session_with_redeye_pending())
        self._bump_revision()


    @Slot()
    def applyRedeye(self) -> None:
        """Alkalmaz: az automatikus és kézi vörösszem-területek mentése."""
        self._require_active()
        self._push_undo("redeye")
        self._session = self._session_with_redeye_pending()
        self._redeye_regions = ()
        self._redeye_region_undo = []
        self._redeye_eye_circles = ()
        self._redeye_eye_image_size = None
        self._redeye_eye_overlay_size = None
        self._redeye_eye_to_overlay = AZONOSSAG
        self._redeye_full_image_fallback = False
        self._redeye_found = -1
        self._redeye_can_reapply_auto = False
        self._redeye_reset_message = False
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    def _session_with_redeye_pending(self) -> EditSession:
        return self._session.set_redeye_regions(
            self._redeye_regions,
            eye_circles=tuple(
                EyeCircle64(x, y, radius)
                for x, y, radius in self._redeye_eye_circles
            ),
            full_image_fallback=self._redeye_full_image_fallback,
        )


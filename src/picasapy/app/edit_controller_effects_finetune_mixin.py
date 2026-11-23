"""A tilt és a finomhangolás csúszkái, mentése és élő előnézete (#6267)."""

from __future__ import annotations

from .edit_controller_shared import (
    EditSession,
    Property,
    Slot,
    build_finetune2_lut,
    gyors_elonezet,
    np,
    parse_neutral_argb,
)
from .edit_controller_signals import EditControllerSignalsMixin as _Signals


class EditControllerEffectsFinetuneMixin:
    """A tilt- és finomhangolás-tulajdonságok, csúszkák és előnézetek (#6267)."""

    @Property(float, notify=_Signals.tiltParamChanged)
    def tiltParam(self) -> float:
        """A mentett döntés-paraméter (-1..1 Picasa-egység), vagy 0.0, ha
        nincs tilt-szűrő a láncban. A döntés-csúszka ezzel áll be az eszköz
        megnyitásakor és lapozáskor a MENTETT értékre, ne 0-ra (#131)."""
        return self._session.tilt_param() or 0.0


    @Property(float, notify=_Signals.fillLightChanged)
    def fillLight(self) -> float:
        return self._finetune_field("fill")


    @Property(float, notify=_Signals.fixesFillLightChanged)
    def fixesFillLight(self) -> float:
        """A Gyakori javítások Derítőfénye: a `fill=1,<érték>` réteg erőssége,
        vagy 0.0, ha nincs ilyen réteg (#7369). A `finetune2`-től független:
        az eredeti Picasa a két fülön két külön szűrőt aktivál."""
        return self._session.fill_value() or 0.0


    @Property(float, notify=_Signals.highlightsChanged)
    def highlights(self) -> float:
        return self._finetune_field("highlights")


    @Property(float, notify=_Signals.shadowsChanged)
    def shadows(self) -> float:
        return self._finetune_field("shadows")


    @Property(float, notify=_Signals.colorTempChanged)
    def colorTemp(self) -> float:
        return self._finetune_field("temperature")


    @Property(str, notify=_Signals.neutralColorChanged)
    def neutralColor(self) -> str:
        """A kijelölt semleges szín `#rrggbb` alakban, vagy üres string, ha
        nincs kijelölve (#464).

        Az eredeti Finomhangolás fülén az „Alapszínválasztás" pipettája
        MELLETT egy színminta-korong ül, ami a kijelölt színt mutatja (ld. a
        `referencia/finomhangolas/shot1.png` képernyőképet) — ez a
        tulajdonság tölti azt.
        """
        # #7383: a minta a Hangolás-látogatás rétegének színét mutatja; látogatás
        # nélkül (belépés, Undo/Redo, képváltás) alaphelyzetben áll, mint a
        # csúszkák - az eredetiben a betöltött `ffccc6b2` mellett is fekete (J6c).
        values = self._visit_values()
        if values is None:
            return ""
        neutral = parse_neutral_argb(values.neutral)
        if neutral is None:
            return ""
        return "#{:02x}{:02x}{:02x}".format(*neutral)


    @Property(bool, notify=_Signals.hasFinetuneChanged)
    def hasFinetune(self) -> bool:
        """Van-e finomhangolás a láncban — a „Visszavonás" felirathoz."""
        return self._session.has_finetune()


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
        self.toolsChanged.emit()


    @Slot(float)
    def previewTilt(self, param: float) -> None:
        """Élő forgatás-előnézet a csúszka húzása közben (#72): a képet a
        pillanatnyi paraméterrel újrarenderli, de NEM ír ini-be és NEM tol
        undo-lépést — a tényleges mentést az Alkalmaz gomb indítja."""
        self._require_active()
        preview_session = self._session.set_tilt(param, 0.0)
        # #3846: húzás közben a gyors mintavevő (a natív 2560 px-en >10× lassabb);
        # az Alkalmazáskor hívott `setTilt` már a natív úton renderel.
        with gyors_elonezet():
            self._register_preview(preview_session)
        self._bump_revision()


    @Slot()
    def discardTiltPreview(self) -> None:
        """#4058: a Kiegyenesítés Mégséje a mentett láncot rajzolja újra.

        A csúszka-előnézet csak a szolgáltatónál él; a munkamenet, a fájl és
        az undo-verem az Alkalmazásig érintetlen. Az alap munkamenet újbóli
        regisztrálása ezért pontosan visszaállítja a nyitáskori képet akkor
        is, ha ott még tilt-réteg sem volt."""
        self._require_active()
        self._register_preview()
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
        preview_session = self._finetune_visit_session(
            self._session,
            fill=fill, highlights=highlights, shadows=shadows, temperature=temperature,
        )
        self._register_preview(preview_session)
        self._bump_revision()


    @Slot(float, float, float, float)
    def previewFinetuneGpu(
        self, fill: float, highlights: float, shadows: float, temperature: float
    ) -> None:
        """GPU-gyorsított élő finomhangolás-előnézet (#22).

        A `previewFinetune`-nal ellentétben ez NEM futtatja újra a teljes
        numpy filter-láncot minden húzási lépésnél — csak a (256×1, olcsó)
        LUT-ot számolja újra és frissíti a `gpuLutSource`-ot; a
        `GpuPointFilterPreview.qml` a drága munkát a GPU-n végzi, a
        `gpuPrefixSource` (a finetune2 ELŐTTI kép) a húzás alatt
        VÁLTOZATLAN. A hívó (PhotoViewer.qml) csak akkor hívja ezt
        previewFinetune HELYETT, ha a futtatókörnyezet RHI-alapú GPU-t
        biztosít ÉS a jelenlegi lánc GPU-alkalmas (`gpuPrefixSource`
        nem üres) — máskülönben a normál CPU-utat használja.

        NEM ír inibe, NEM tol undo-lépést, NEM bumpolja a `revision`-t (a
        `previewSource`/`photo` Image-nek a húzás alatt NEM szabad
        újratöltődnie) — csak a `gpuRevisionChanged`-et."""
        self._require_active()
        if fill != 0.0:
            # #551: a Derítőfény mért modellje világosság-vezérelt, tehát
            # nem fejezhető ki csatornánkénti LUT-tal — a GPU-út ilyenkor
            # más képet adna, mint a mentés. A hívó (QML) ezt már tudja és
            # nem is kéri, ez a védőkorlát a nem-UI hívók ellen.
            self.previewFinetune(fill, highlights, shadows, temperature)
            return
        prefix_ops = self._gpu_finetune_prefix()
        if prefix_ops is None:
            # a lánc időközben (pl. párhuzamos ini-módosítás) GPU-
            # alkalmatlanná vált — néma, biztonságos no-op, a hívó a
            # gpuPrefixSource újraolvasásával úgyis visszavált CPU-ra
            return
        # #7383: a látogatás rétegének pipetta-színe a LUT-ba is bekerül
        values = self._visit_values()
        lut = build_finetune2_lut(
            fill=fill, highlights=highlights, shadows=shadows,
            neutral=parse_neutral_argb(values.neutral) if values is not None else None,
            temperature=temperature,
        )
        self._provider.update_gpu_lut(self._kulcs, lut)
        self._bump_gpu_revision()


    @Slot(float, float, float, float)
    def setFinetune(
        self, fill: float, highlights: float, shadows: float, temperature: float
    ) -> None:
        """A finomhangolás négy csúszkájának mentése a Hangolás-látogatás
        `finetune2` rétegébe (#7383).

        A csúszka elengedésekor hívódik. A látogatás első mentése új réteget
        fűz a lánc végére és egy visszavonási lépést tol; a további mentések
        ugyanazt a réteget írják, lépés nélkül. Ha mind a négy érték semleges
        (0) és nincs pipetta-szín, a réteg nem kell: a lánc a látogatás előtti
        állapotra áll vissza."""
        self._require_active()
        if self._commit_finetune_layer(
            fill=fill, highlights=highlights, shadows=shadows, temperature=temperature
        ):
            self._save()
            self._bump_revision()
            self.toolsChanged.emit()


    @Slot(float)
    def previewFixesFill(self, value: float) -> None:
        """Élő Derítőfény-előnézet a Gyakori javítások csúszka húzása közben
        (#7369): NEM ír ini-be, NEM tol undo-lépést; a mentés az elengedéskor
        hívott `setFixesFill`-lel történik. A GPU-s LUT-út nem használható:
        a Derítőfény világosság-vezérelt (#551)."""
        self._require_active()
        self._register_preview(self._session_with_fill(self._session, value))
        self._bump_revision()


    @Slot(float)
    def setFixesFill(self, value: float) -> None:
        """A Gyakori javítások Derítőfényének mentése a `fill` rétegbe (#7369).

        Undo-lépést tol (felirata `Fill Light` / `Derítőfény`) és ini-be ír.
        Nulla értéknél a réteget eltávolítja, hogy a visszahúzott csúszka ne
        hagyjon fölösleges no-op `fill`-t. A `finetune2`-höz nem nyúl."""
        self._require_active()
        self._push_undo("fill")
        self._session = self._session_with_fill(self._session, value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    @staticmethod
    def _session_with_fill(session: EditSession, value: float) -> EditSession:
        return session.clear_fill() if value == 0.0 else session.set_fill(value)


    def _finetune_field(self, field: str) -> float:
        """A mentett finetune2 adott csúszka-értéke, vagy 0.0, ha nincs
        finomhangolás. A csúszkák #7383 óta NEM ebből töltődnek: a Hangolás
        fül mindig alaphelyzetben indul, a kép viszont a láncot mutatja."""
        values = self._session.finetune_values()
        return getattr(values, field) if values is not None else 0.0


    @staticmethod
    def _gpu_lut_for(session: EditSession) -> np.ndarray:
        """A `session` MENTETT finetune2-értékeiből (vagy semleges alapból,
        ha nincs finomhangolás) épített LUT (#22) — ez indítja a
        `gpuLutSource`-ot minden `_register_preview()`-nál, hogy a húzás
        KEZDETÉN (az első `previewFinetuneGpu` hívás ELŐTT is) már a
        mentett állapotot tükrözze. Az üres lánc semleges LUT-ja az
        azonosság-rámpa; ezt közvetlenül állítjuk elő, hogy a kép első
        megnyitásakor ne importálja a teljes renderláncot."""
        values = session.finetune_values()
        if values is None:
            ramp = np.arange(256, dtype=np.uint8)
            return np.repeat(ramp[:, None], 3, axis=1)
        neutral = parse_neutral_argb(values.neutral)
        return build_finetune2_lut(
            fill=values.fill,
            highlights=values.highlights,
            shadows=values.shadows,
            neutral=neutral,
            temperature=values.temperature,
        )

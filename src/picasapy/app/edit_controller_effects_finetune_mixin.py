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

    @Property(float, notify=_Signals.toolsChanged)
    def tiltParam(self) -> float:
        """A mentett döntés-paraméter (-1..1 Picasa-egység), vagy 0.0, ha
        nincs tilt-szűrő a láncban. A döntés-csúszka ezzel áll be az eszköz
        megnyitásakor és lapozáskor a MENTETT értékre, ne 0-ra (#131)."""
        return self._session.tilt_param() or 0.0


    @Property(float, notify=_Signals.toolsChanged)
    def fillLight(self) -> float:
        return self._finetune_field("fill")


    @Property(float, notify=_Signals.toolsChanged)
    def highlights(self) -> float:
        return self._finetune_field("highlights")


    @Property(float, notify=_Signals.toolsChanged)
    def shadows(self) -> float:
        return self._finetune_field("shadows")


    @Property(float, notify=_Signals.toolsChanged)
    def colorTemp(self) -> float:
        return self._finetune_field("temperature")


    @Property(str, notify=_Signals.toolsChanged)
    def neutralColor(self) -> str:
        """A kijelölt semleges szín `#rrggbb` alakban, vagy üres string, ha
        nincs kijelölve (#464).

        Az eredeti Finomhangolás fülén az „Alapszínválasztás" pipettája
        MELLETT egy színminta-korong ül, ami a kijelölt színt mutatja (ld. a
        `referencia/finomhangolas/shot1.png` képernyőképet) — ez a
        tulajdonság tölti azt.
        """
        values = self._session.finetune_values()
        if values is None:
            return ""
        neutral = parse_neutral_argb(values.neutral)
        if neutral is None:
            return ""
        return "#{:02x}{:02x}{:02x}".format(*neutral)


    @Property(bool, notify=_Signals.toolsChanged)
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
        preview_session = self._session.set_finetune(
            fill=fill, highlights=highlights, shadows=shadows, temperature=temperature
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
        prefix_ops = self._session.gpu_finetune_prefix()
        if prefix_ops is None:
            # a lánc időközben (pl. párhuzamos ini-módosítás) GPU-
            # alkalmatlanná vált — néma, biztonságos no-op, a hívó a
            # gpuPrefixSource újraolvasásával úgyis visszavált CPU-ra
            return
        lut = build_finetune2_lut(
            fill=fill, highlights=highlights, shadows=shadows, temperature=temperature
        )
        self._provider.update_gpu_lut(self._kulcs, lut)
        self._bump_gpu_revision()


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


    def _finetune_field(self, field: str) -> float:
        """A mentett finetune2 adott csúszka-értéke, vagy 0.0, ha nincs
        finomhangolás — a QML-csúszkák így a mentett értékre állnak (#20)."""
        values = self._session.finetune_values()
        return getattr(values, field) if values is not None else 0.0


    @staticmethod
    def _gpu_lut_for(session: EditSession) -> np.ndarray:
        """A `session` MENTETT finetune2-értékeiből (vagy semleges alapból,
        ha nincs finomhangolás) épített LUT (#22) — ez indítja a
        `gpuLutSource`-ot minden `_register_preview()`-nál, hogy a húzás
        KEZDETÉN (az első `previewFinetuneGpu` hívás ELŐTT is) már a
        mentett állapotot tükrözze."""
        values = session.finetune_values()
        if values is None:
            return build_finetune2_lut()
        neutral = parse_neutral_argb(values.neutral)
        return build_finetune2_lut(
            fill=values.fill,
            highlights=values.highlights,
            shadows=values.shadows,
            neutral=neutral,
            temperature=values.temperature,
        )

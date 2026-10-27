"""Az egygombos javítások, effektek, csúszkák és színpipetták."""

from __future__ import annotations

from .edit_controller_shared import (
    DEAD_LEGACY_OPS,
    EditSession,
    LEGACY_EFFECTS,
    LEGACY_EFFECT_KEYS,
    Property,
    QCoreApplication,
    QGuiApplication,
    Slot,
    _APPLICABLE_EFFECTS,
    _EFFECT_INI_NAMES,
    _EFFECT_PARAMS,
    _PICKER_COLOR_PATTERN,
    _PICKER_MRU_SETTINGS_KEYS,
    build_finetune2_lut,
    can_offer_filter_control,
    estimate_neutral_color,
    format_param_values,
    gyors_elonezet,
    has_params,
    np,
    one_click_keys,
    parse_neutral_argb,
    resolve_effect_params,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

class EditControllerEffectsMixin:
    """Az egygombos javítások, effektek, csúszkák és színpipetták."""

    @Property("QVariantList", notify=_Signals.pickerRecentColorsChanged)
    def recentPickerColors(self) -> list[str]:
        """A színválasztó öt MRU-rekesze (`picker/mru_0` a legfrissebb)."""
        return [
            str(self._picker_settings.value(key, "") or "")
            for key in _PICKER_MRU_SETTINGS_KEYS
        ]


    @Slot(str)
    def rememberPickerColor(self, color: str) -> None:
        """A választott `#RRGGBB` színt elölre teszi és tartósan elmenti."""
        normalized = str(color).strip().lower()
        if not _PICKER_COLOR_PATTERN.fullmatch(normalized):
            return

        colors = [normalized]
        for previous in self.recentPickerColors:
            previous = str(previous).strip().lower()
            if (
                _PICKER_COLOR_PATTERN.fullmatch(previous)
                and previous not in colors
                and len(colors) < len(_PICKER_MRU_SETTINGS_KEYS)
            ):
                colors.append(previous)

        for index, key in enumerate(_PICKER_MRU_SETTINGS_KEYS):
            self._picker_settings.setValue(
                key, colors[index] if index < len(colors) else ""
            )
        self._picker_settings.sync()
        self.pickerRecentColorsChanged.emit()


    @Property("QVariant", constant=True)
    def legacyEffects(self):
        """Az „Régi effektek" fül gombjai (#571) — a katalógusból, nem
        kézzel a QML-be írva.

        Minden elem: `key` (belső szűrőnév), `label` (angol felirat, a
        fordítás a szokásos `.ts` úton), `enabled` (van-e VALÓDI vizuális
        modellünk — a renderelő dönti el), `dead` (halott legacy név, #567:
        a Picasa natív regiszterében sincs hozzá feldolgozó).
        """
        return [
            {
                "key": effect.key,
                # a felirat MÁR fordítva megy a QML-nek: a katalógus adat,
                # nem forráskód, ezért `qsTr()` nem tudná kigyűjteni —
                # a `.ts`-ben a "LegacyEffects" kontextus tartja őket
                "label": QCoreApplication.translate("LegacyEffects", effect.label),
                "enabled": can_offer_filter_control(effect.key),
                "dead": effect.key in DEAD_LEGACY_OPS,
            }
            for effect in LEGACY_EFFECTS
        ]


    @Property("QVariant", notify=_Signals.revisionChanged)
    def legacyEffectsInChain(self):
        """A szerkesztési láncban szereplő ÖRÖKÖLT szűrőnevek (#571).

        Ebből teszi ki a szerkesztő az „Régi effektek" fülre a jelzést: a
        felhasználó egy régi képen ott találhat olyan effektet, amit a mai
        Picasa felülete nem is mutat — tudnia kell, hol nézze meg."""
        names = {op.name.casefold() for op in self._session.ops}
        return sorted(names & LEGACY_EFFECT_KEYS)


    @Property("QVariant", constant=True)
    def oneClickEffects(self):
        """#2126: a `mode="oneclick"` szűrők kulcsai — a kék jelvényhez.

        ÁLLANDÓ: a mód a szűrő-leíró tulajdonsága, nem a munkamenet
        állapota, ezért `constant=True` (a felületnek nem kell újraszámolnia
        minden lánc-módosításnál). A forrás egyetlen helyen van:
        `render.registry.one_click_keys()`.
        """
        return list(one_click_keys())


    @Property("QVariant", notify=_Signals.revisionChanged)
    def effectChainCounts(self):
        """Melyik szűrő HÁNYSZOR szerepel a szerkesztési láncban (#704).

        Ebből teszi ki a szerkesztő az „alkalmazva" jelvényt a csempékre: a
        felhasználó a rácsról ma egyáltalán nem tudja megállapítani, mely
        effektek vannak már a képen. Ez nem díszítés, hanem a szerkesztő
        egyik alapvető visszajelzése.

        DARABSZÁM, nem lánc-pozíció: a bejelentő képernyőképén az eredeti
        Picasa a Sepia és a Warmify csempéjén EGYARÁNT `1`-et mutat, holott
        a láncban a kettő nem lehet ugyanazon a helyen — vagyis a szám az
        adott szűrő előfordulásainak száma.

        A kulcsok a szűrőnév kisbetűs (casefold) alakjai, ahogy a QML-oldal
        is küldi őket (`effectRequested`, `applyEffectWithParams`).
        """
        counts: dict[str, int] = {}
        for op in self._session.ops:
            key = op.name.casefold()
            counts[key] = counts.get(key, 0) + 1
        return counts


    @Property(str, notify=_Signals.revisionChanged)
    def effectChain(self) -> str:
        """A szerkesztési lánc sorosított értéke az effekt-csempe előnézetéhez.

        A képszolgáltató könyvtárrekordja a szerkesztés megnyitásakor készült,
        ezért az aktuális láncot a csempe URL-jén kell átadni. A revíziójel
        minden sikeres láncmódosításkor újraköti ezt az értéket.
        """
        return self._session.to_value()


    @Property(bool, notify=_Signals.toolsChanged)
    def enhanceEnabled(self) -> bool:
        return not self._session.last_is("enhance")


    @Property(bool, notify=_Signals.toolsChanged)
    def autolightEnabled(self) -> bool:
        return not self._session.last_is("autolight")


    @Property(bool, notify=_Signals.toolsChanged)
    def autocolorEnabled(self) -> bool:
        return not self._session.last_is("autocolor")


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


    @Slot(str)
    def applyEffect(self, name: str) -> None:
        """Effekt réteg a lánc végére (#20): append-only, undo-lépéssel.

        Az ismeretlen név ValueError; a paramétert igénylő effektek (pl. sat)
        dokumentált alapértékkel kerülnek be (`_EFFECT_PARAMS`)."""
        self._require_active()
        key = name.casefold()
        if key not in _APPLICABLE_EFFECTS:
            raise ValueError(f"Érvénytelen effekt: {name!r}")
        self._push_undo(key)
        self._session = self._session.append_effect(
            _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot(str, result=bool)
    def effectHasParams(self, name: str) -> bool:
        """Nyíljon-e csúszkás alpanel a gombra kattintva?

        A paraméter nélküli effektek (Szépia, Fekete-fehér…) az eredeti
        Picasában is egy kattintással alkalmazódnak.
        """
        return has_params(name)


    @Slot(str, result="QVariant")
    def effectParams(self, name: str):
        """Az effekt vezérlői a QML-nek — LISTÁT adunk, nem tuple-t: a
        QML-oldalon a tuple NEM tömb (#232).

        #516: a képfüggő tartományokat (`CornerRadius` 0..min(W,H)/2 stb.)
        a JELENLEG szerkesztett kép valódi méretével számoljuk ki
        (`resolve_effect_params`) — nincs bebetonozott szám."""
        width, height = self._image_size if self._image_size else (None, None)
        return [
            {
                "key": param.key,
                "label": param.label,
                "kind": param.kind,
                "minimum": param.minimum,
                "maximum": param.maximum,
                "default": param.default,
                "step": param.step,
                "color": param.color,
            }
            for param in resolve_effect_params(name, width, height)
        ]


    @Slot(str, "QVariantList")
    def previewEffect(self, name: str, values) -> None:
        """Élő előnézet a csúszkák húzása közben: a képet a pillanatnyi
        értékekkel újrarendereli, de NEM ír ini-be és NEM tol undo-lépést
        (a previewFinetune mintájára, #20).

        #3862: a `gyors_elonezet()` blokk (a `previewTilt` mintájára) a
        Polaroid forgatását is a gyors mintavevőre váltja húzás közben — az
        `applyEffectWithParams` (elengedéskor/Alkalmaz) már a blokkon kívül,
        natívan renderel."""
        self._require_active()
        preview_session = self._session_with_effect(name, values)
        if preview_session is None:
            return
        with gyors_elonezet():
            self._register_preview(preview_session)
        self._bump_revision()


    @Slot()
    def discardEffectPreview(self) -> None:
        """Mégse: az előnézet elvetése, a mentett lánc visszaállítása."""
        self._require_active()
        self._register_preview()
        self._bump_revision()


    @Slot(str, "QVariantList")
    def applyEffectWithParams(self, name: str, values) -> None:
        """Alkalmaz: a beállított értékekkel fűzi a láncra (undo + mentés).

        Hiányzó vagy hiányos értéklistánál a katalógus alapértékei jönnek —
        így a gomb paraméter nélkül is ugyanazt adja, mint az `applyEffect`.
        """
        self._require_active()
        session = self._session_with_effect(name, values)
        if session is None:
            return
        self._push_undo(name.casefold())
        self._session = session
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    def _session_with_effect(self, name: str, values) -> EditSession | None:
        """A lánc az effekttel a végén; ismeretlen effektnél None.

        A hiányzó értékeket a katalógus alapértéke pótolja, a fölöslegeseket
        eldobjuk — a `filters=` sosem kaphat a katalógusnál több paramétert.
        """
        if not isinstance(name, str):
            return None
        key = name.casefold()
        if key not in _APPLICABLE_EFFECTS:
            return None
        width, height = self._image_size if self._image_size else (None, None)
        catalogue = resolve_effect_params(key, width, height)
        if not catalogue:
            # paraméter nélküli effekt: a meglévő, dokumentált alapérték-út
            return self._session.append_effect(
                _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
            )
        supplied = list(values) if values is not None else []
        resolved = [
            supplied[index]
            if index < len(supplied)
            else (param.color if param.kind == "color" else param.default)
            for index, param in enumerate(catalogue)
        ]
        try:
            formatted = format_param_values(resolved, catalogue, effect=key)
        except (TypeError, ValueError):
            return None
        return self._session.append_effect(
            _EFFECT_INI_NAMES.get(key, key), ("1", *formatted)
        )


    def _finetune_field(self, field: str) -> float:
        """A mentett finetune2 adott csúszka-értéke, vagy 0.0, ha nincs
        finomhangolás — a QML-csúszkák így a mentett értékre állnak (#20)."""
        values = self._session.finetune_values()
        return getattr(values, field) if values is not None else 0.0


    @Slot(float, float, result=bool)
    def pickNeutralColor(self, nx: float, ny: float) -> bool:  # noqa: N802
        """A pipetta (#464): a képre kattintott pont színe lesz a
        finetune2 „semleges szín" paramétere (a lánc 4. paramétere).

        A `finetune2` négy csúszkája változatlan marad — a pipetta csak a
        semleges színt írja át. `False`, ha a pont nem mintavételezhető
        (nincs regisztrált előnézet, vagy a pont a képen kívül esik).
        """
        self._require_active()
        sample = self._provider.sample_color(self._kulcs, nx, ny)
        if sample is None:
            return False
        red, green, blue = sample
        values = self._session.finetune_values()
        self._push_undo("finetune")
        self._session = self._session.set_finetune(
            fill=values.fill if values else 0.0,
            highlights=values.highlights if values else 0.0,
            shadows=values.shadows if values else 0.0,
            temperature=values.temperature if values else 0.0,
            neutral=f"ff{red:02x}{green:02x}{blue:02x}",
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()
        return True


    @Slot(float, float, result=str)
    def pickEffectColor(self, nx: float, ny: float) -> str:  # noqa: N802
        """Az effekt-színparaméter pipettája (#5674): a képre kattintott
        pont színe `#rrggbb` alakban.

        Csak adja vissza a színt: sem láncot, sem ini-t nem ír. A paramétert
        a QML állítja be a `panel.updateParamValue`-n át, így az Alkalmaz/Mégse
        az effekt szokásos útját járja be. Üres sztring, ha a pont nem
        mintavételezhető (nincs aktív szerkesztés, nincs regisztrált előnézet,
        vagy a pont a képen kívül esik).
        """
        sample = self._provider.sample_color(self._kulcs, nx, ny)
        if sample is None:
            return ""
        red, green, blue = sample
        return f"#{red:02x}{green:02x}{blue:02x}"


    @Slot(bool)
    def figyeldAShiftet(self, kell: bool) -> None:  # noqa: N802 — QML-slot
        """A Shift követésének be-/kikapcsolása (#798).

        ⚠️ **MÉRVE, miért nem állandó.** Az első változat az
        alkalmazás-szintű szűrőt a vezérlő születésekor tette fel, és ott
        is hagyta. Az eseményszűrő MINDEN eseményre átlép Pythonba: a
        `tests/app/qml_functional/test_people_panel_26.py` futásideje
        13 s-ról **25 s-ra** nőtt tőle, és két időzítésre épülő próba el is
        bukott. A felhasználó ugyanezt a lassulást kapná az egész
        felületen, egy olyan funkcióért, ami CSAK az effekt-fülön él.

        Ezért a szűrő addig van fent, amíg az effekt-fül látszik — a panel
        kapcsolja. Felrakáskor a pillanatnyi állapotot is beolvassuk, mert
        a felhasználó már a fül megnyitása előtt is nyomhatja a Shiftet.
        """
        kell = bool(kell)
        if kell == self._shift_figyeles:
            return
        alkalmazas = QGuiApplication.instance()
        if alkalmazas is None:
            return
        self._shift_figyeles = kell
        if kell:
            alkalmazas.installEventFilter(self)
            self._allitsd_a_shiftet(self.shiftLenyomva())
        else:
            alkalmazas.removeEventFilter(self)
            self._allitsd_a_shiftet(False)


    def _allitsd_a_shiftet(self, aktiv: bool) -> None:
        if aktiv == self._shift_aktiv:
            return
        self._shift_aktiv = aktiv
        self.shiftAktivChanged.emit()


    @Property(bool, notify=_Signals.shiftAktivChanged)
    def shiftAktiv(self) -> bool:
        """Le van-e nyomva ÉPPEN MOST a Shift (#798).

        Ez a kötés-barát alak: a QML rá köt, és a lenyomás pillanatában
        újraértékelődik. A `shiftLenyomva()` lekérdezés megmarad — a panel
        FELÉPÜLÉSEKOR arra van szükség, mert akkor még nem volt olyan
        billentyű-esemény, amiből a szűrő tudhatna (a felhasználó már a
        fül megnyitása előtt is nyomva tarthatja).
        """
        return self._shift_aktiv


    @Slot(result=bool)
    def shiftLenyomva(self) -> bool:  # noqa: N802 — QML-stílusú név
        """Le van-e nyomva a Shift ÉPPEN MOST (#2146)?

        Az eredeti az effekt-fül felépülésekor **egyszer** kérdezi le
        (`GetAsyncKeyState(VK_SHIFT)`, `0x005d7c91`), és a bitet eltárolja
        (`[ecx+0x33a8]`); a kilenc érintett csempe ezután ezt a tárolt
        értéket nézi, nem a pillanatnyi billentyűállapotot. A QML-ben
        nincs erre API — a `Qt.ShiftModifier` csak eseményből érhető el,
        a fül felépülése viszont nem billentyűesemény.

        ⚠️ A hívó felelőssége, hogy **egyszer** hívja (a fül láthatóvá
        válásakor), és az eredményt eltárolja. Ha képkockánként kérdezné,
        a csempék a Shift minden le-fel nyomására átbillennének — az
        eredeti pontosan ezt NEM teszi.
        """
        from PySide6.QtCore import Qt as QtNs
        from PySide6.QtGui import QGuiApplication

        return bool(
            QGuiApplication.queryKeyboardModifiers()
            & QtNs.KeyboardModifier.ShiftModifier
        )


    @Slot(result=bool)
    def applyColorWand(self) -> bool:  # noqa: N802 — QML-stílusú név
        """A szín-varázspálca (#551): a viszonyítási színt a PROGRAM választja.

        A mérés kimondta, hogy a pálca nem külön szűrő: ugyanabba a
        `finetune2` p4 mezőbe ír, mint a kézi pipetta — a Picasa saját
        `.picasa.ini`-je bizonyítja (`finetune2=1,0,0,0,006b8088,0`). A
        színt a kevéssé telített képpontok átlagából becsüljük
        (`estimate_neutral_color`), a zöldre normálva.

        `False`, ha a forráskép nem olvasható — ilyenkor a lánc érintetlen.
        """
        self._require_active()
        if self._image_path is None:
            return False
        source = self._provider.source_image(self._kulcs, self._image_path)
        if source is None:
            return False
        red, green, blue = estimate_neutral_color(source)
        values = self._session.finetune_values()
        self._push_undo("finetune")
        self._session = self._session.set_finetune(
            fill=values.fill if values else 0.0,
            highlights=values.highlights if values else 0.0,
            shadows=values.shadows if values else 0.0,
            temperature=values.temperature if values else 0.0,
            neutral=f"ff{red:02x}{green:02x}{blue:02x}",
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()
        return True


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


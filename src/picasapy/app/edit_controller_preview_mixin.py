"""Az előnézet, GPU-revízió és renderelési kérések kezelése."""

from __future__ import annotations

from .edit_controller_shared import (
    EMPTY_HISTOGRAM,
    EditSession,
    Image,
    Path,
    Property,
    Slot,
    UnidentifiedImageError,
    _GPU_REVIZIO,
    _REVIZIO,
    _log,
    chain_flags,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

class EditControllerPreviewMixin:
    """Az előnézet, GPU-revízió és renderelési kérések kezelése."""

    @property
    def _kulcs(self) -> str:
        """A SZOLGÁLTATÓ kulcsa (#3187) — a rekesszel megjelölve.

        Minden `self._provider.…` hívás és minden `image://editpreview/…`
        URL ezt viszi, sosem a nyers `self._photo_id`-t; erre külön
        forrás-szintű őr is fut (`test_masodik_elonezet_3187.py`)."""
        if not self._photo_id or not self._slot:
            return self._photo_id
        return f"{self._photo_id}@{self._slot}"


    @Property(int, notify=_Signals.revisionChanged)
    def revision(self) -> int:
        return self._revision


    @Property(str, notify=_Signals.revisionChanged)
    def previewSource(self) -> str:
        """`image://editpreview/<id>?rev=<n>` vagy üres, ha nincs aktív
        szerkesztés. A QML-frissítés triggere a revision — a previewSource
        értéke (a ?rev= rész) attól függ, hogy a kép-URL biztosan változzon."""
        if not self._photo_id:
            return ""
        return f"image://editpreview/{self._kulcs}?rev={self._revision}"


    @Property(str, notify=_Signals.gpuRevisionChanged)
    def gpuPrefixSource(self) -> str:
        """A finetune2 ELŐTTI köztes kép URL-je (#22), ha az el is érhető.

        Üres stringet ad, amíg nincs aktív, GPU-alkalmas lánc, illetve amíg a
        provider cache-ében nincs meg mindkét GPU-kép. Így a Qt nem kér le
        null képet egy még folyamatban lévő előnézet-render közben.
        """
        if (
            not self._photo_id
            or self._session.gpu_finetune_prefix() is None
            or not self._provider.gpu_preview_ready(self._kulcs)
        ):
            return ""
        return f"image://editpreview/{self._kulcs}?gpuprefix=1&rev={self._gpu_revision}"


    @Property(str, notify=_Signals.gpuRevisionChanged)
    def gpuLutSource(self) -> str:
        """A jelenlegi finetune2-LUT 256×1 képének URL-je (#22) — ugyanaz az
        elérhetőségi feltétel, mint `gpuPrefixSource`-nál."""
        if (
            not self._photo_id
            or self._session.gpu_finetune_prefix() is None
            or not self._provider.gpu_preview_ready(self._kulcs)
        ):
            return ""
        return f"image://editpreview/{self._kulcs}?gpulut=1&rev={self._gpu_revision}"


    @Property("QVariant", notify=_Signals.revisionChanged)
    def histogram(self):
        """A jelenleg renderelt előnézet RGB-hisztogramja (#25) — a
        HistogramBox.qml Canvas-a ebből rajzolja a három görbét. A revision
        minden előnézet-frissítéskor (csúszka-húzás közben is) bumpol, a
        provider a MEGJELENÍTETT képből számolja (ld. edit_preview.py)."""
        if not self._photo_id:
            return dict(EMPTY_HISTOGRAM)
        return self._provider.histogram_for(self._kulcs)


    @Property("QVariant", notify=_Signals.revisionChanged)
    def framePlacement(self):
        """Hol van a FÉNYKÉP a keretezett előnézetben (#3166)?

        A szerkesztő átfedő rétegei (vágás-téglalap, arckeretek) a kirajzolt
        képre horgonyozódnak, és relatív `[0..1]` koordinátákkal dolgoznak —
        keret-effekt esetén viszont a kirajzolt kép már a keretezett kimenet,
        tehát ugyanaz a koordináta a KERETRE skálázódik. Ez a tulajdonság adja
        meg a fénykép helyét a kimenetben; `None`, ha nincs keret a láncban
        (a rétegek ilyenkor a mai módon a teljes téglalapot kapják).

        A szög fokban, a renderelő előjelével — a QML `rotation`-je ennek a
        NEGÁLTJA (ld. `PhotoViewer.qml`, `frameContentArea`).
        """
        if not self._photo_id:
            return None
        hely = self._provider.frame_placement(self._kulcs)
        if hely is None or hely.erintetlen:
            return None
        return {
            "kozepX": hely.kozep_x,
            "kozepY": hely.kozep_y,
            "szelesseg": hely.szelesseg,
            "magassag": hely.magassag,
            "szog": hely.szog,
        }


    @Property(str, notify=_Signals.revisionChanged)
    def cameraSummary(self) -> str:
        """Picasa-stílusú, egysoros gép-összefoglaló (#25) a hisztogram
        alatt — a forrásfájl EXIF-jéből, beginEdit-kor gyorsítótárazva."""
        return self._camera_summary


    def refresh_displayed_image(self) -> None:
        """A megjelenített kép ÚJRAKÉRETÉSE a QML-lel, újrarenderelés nélkül.

        A `Nézet ▸ Megjelenítési mód` váltásakor hívódik (#1576): a
        szolgáltató a tárolt (érintetlen) képre a KÉRÉS pillanatában teszi rá
        a mód hatását, tehát sem dekódolni, sem a `filters=` láncot
        újrafuttatni nem kell — elég a `previewSource` `?rev=` cache-busterét
        léptetni, különben a QML a saját kép-gyorstárából a régi, jelöletlen
        képet tartaná meg.

        Nyitott szerkesztés nélkül no-op (a mód a rácsból is váltható).

        SZÁNDÉKOSAN nem `@Slot`: a hívó a Python-oldali `wire_display_mode()`,
        a QML-nek nincs dolga vele — `@Slot`-ként a `kepesseg_or.py` (joggal)
        felületről elérhetetlen vezérlő-tagként jelentené."""
        if not self._photo_id:
            return
        self._bump_revision()


    @staticmethod
    def _read_image_size(path: Path) -> tuple[int, int] | None:
        """A kép pixel-mérete a #516 képfüggő effekt-tartományaihoz
        (`CornerRadius` 0..min(W,H)/2, `CaptionHeight` 0..H/6 stb.) — a PIL
        `Image.open` csak a fejlécet olvassa, nem dekódolja a pixeleket, a
        próba tehát olcsó. Olvashatatlan/hiányzó fájlnál `None` — a hívó
        ilyenkor a katalógus fallback-méretére esik vissza."""
        try:
            with Image.open(path) as probe:
                return probe.size
        except (OSError, UnidentifiedImageError, ValueError):
            return None


    def _preview_request(self, session: EditSession | None = None) -> dict:
        """A `provider.register()` argumentumai a MOSTANI állapotból.

        Külön lépés, mert a háttérszálas út (#514) a kérést még a hívó
        (GUI-) szálán állítja össze: a háttérszál így nem olvassa a
        controller közben változó mezőit."""
        assert self._image_path is not None
        active_session = session if session is not None else self._session
        gpu_prefix_ops = active_session.gpu_finetune_prefix()
        gpu_lut = self._gpu_lut_for(active_session) if gpu_prefix_ops is not None else None
        crop, crop_ini_readable = self._crop_value_for_session(active_session)
        return {
            "photo_id": self._kulcs,
            "path": self._image_path,
            "ops": active_session.ops,
            "text": self._current_text_spec(),
            "gpu_prefix_ops": gpu_prefix_ops,
            "gpu_lut": gpu_lut,
            "paint_strokes": self._paint_strokes(),
            "crop": crop,
            "crop_ini_readable": crop_ini_readable,
        }


    def _register_preview(self, session: EditSession | None = None) -> None:
        """SZINKRON renderelés — az élő (csúszka-húzás alatti) előnézeté.

        Ezek az utak eleve a gyors, gyorsítótárazott lánc-prefixre épülnek
        (#140), és a húzás minden lépésénél friss képet kell adniuk: a
        háttérszálra tolásuk csak késleltetést és villogást hozna.

        #819: KIVÉVE, ha a láncban `slow` jelzős szűrő van. A regiszter 13
        ilyet jelöl meg; ezek a felület szálán számolva akadoztatják az
        ablakot (a #504 Lomója percekig is elfut). Ilyenkor a háttér-útra
        térünk — a kép így csak a renderelés VÉGÉN frissül, de a felület
        él, és a közös haladásjelző csík magától pörög."""
        aktiv = session if session is not None else self._session
        nevek = [op.name for op in aktiv.ops]
        _teljes, lassu, _ujrameretez = chain_flags(nevek)
        # #3570: a saját (mért) lassú szűrőink is ide tartoznak
        lassu = lassu or any(
            nev.lower() in self.SAJAT_LASSU_SZUROK for nev in nevek
        )
        if lassu:
            self._register_preview_async(session)
            return
        self._preview_job += 1
        self._provider.register(**self._preview_request(session))
        self._bump_gpu_revision()


    def _register_preview_async(self, session: EditSession | None = None) -> None:
        """#514: a MENTETT állapot újrarenderelése HÁTTÉRSZÁLON.

        Ide a lassú, egykattintásos műveletek tartoznak (effekt hozzáadása,
        vágás, visszavonás…). Korábban a GUI szálán futottak, ezért egy
        percekig számoló effekt (#504: Lomo) alatt a felület befagyottnak
        látszott, és a közös haladásjelző csík (#505) sem tudott animálni —
        ugyanaz a szál számolt, ami rajzol. A `BackgroundWorkerMixin`-en át
        indítva a csík MAGÁTÓL pörög (a busy-nyilvántartás a
        `_start_background`-ben jelentkezik be).

        A kép csak a renderelés VÉGÉN frissül: addig a korábbi előnézet
        látszik, ami így is jobb, mint a befagyott felület."""
        self._preview_job += 1
        job = self._preview_job
        request = self._preview_request(session)

        def still_current() -> bool:
            return job == self._preview_job

        def worker() -> None:
            # #546: az elavultság-ellenőrzés a providerben, a TÁROLÁSSAL egy
            # zár alatt fut le (`is_current`) — ha itt kívül néznénk meg,
            # a régebbi render a zárért állva utóbb végezne, és felülírná a
            # frissebb képet. A `shared_cache=False` miatt a háttér-render
            # lokálisan dekódol: a GUI-szál soha nem vár rá záron.
            try:
                self._provider.register(
                    **request, shared_cache=False, is_current=still_current
                )
            except Exception as error:  # noqa: BLE001 — ld. lent
                # #548: a háttérszálban elhaló kivétel NÉMA lenne (a
                # `threading` excepthookja csak stderr-re ír): a kép
                # magyarázat nélkül maradna a régi. A mentés maga már
                # sikerült, ezért nem hibaüzenetet állítunk elő, hanem a
                # meglévő, szálhatáron át sorba állított jelzést használjuk
                # — és naplózunk, hogy a hiba nyomozható legyen.
                _log.exception("Az előnézet háttérszálas renderelése elbukott")
                self.editSaveFailed.emit(str(error))
                return
            if still_current():
                self._previewRendered.emit()

        self._start_background(worker, name="picasapy-editpreview")


    @Slot()
    def cancelPendingPreview(self) -> None:  # noqa: N802 — QML-stílusú név
        """A folyamatban lévő háttér-render érvénytelenítése (#547).

        A `_preview_job` léptetése után a futó worker sem eltárolni, sem
        jelzést emitálni nem fog. Kilépéskor ez zárja be a #430-as
        SIGSEGV-ablakot: a daemon-szál az interpreter leépítése közben
        NEM emitálhat egy közben megsemmisült QObject-nek.
        """
        self._preview_job += 1


    def _on_preview_rendered(self) -> None:
        """A háttérszálas renderelés kész — a GUI-szálon frissítjük a
        képet (`revisionChanged` = cache-buster) és a GPU-rétegeket."""
        self._bump_gpu_revision()
        self._bump_revision()


    def _bump_revision(self) -> None:
        self._revision = next(_REVIZIO)
        self.revisionChanged.emit()
        # A QML-ecset láthatósága is a filters-láncból számolódik. A közös
        # revíziós pont lefedi az alkalmazást, a Visszavonást, az Újrát és
        # az ugyanarra a fotóra újraolvasott ini-t; csak bool-váltás jelez.
        self._notify_paint_mask_support_changed()


    def _bump_gpu_revision(self) -> None:
        """A gpuPrefixSource/gpuLutSource cache-bustere (#22) — KÜLÖN a
        `revisionChanged`-től, ld. a `gpuRevisionChanged` docsztringjét."""
        self._gpu_revision = next(_GPU_REVIZIO)
        self.gpuRevisionChanged.emit()


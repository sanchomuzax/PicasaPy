"""Beállítások, modellállapot és modellletöltés."""

from __future__ import annotations

from .face_scan_controller_signals import FaceScanControllerSignalsMixin as _Signals
from .face_scan_controller_shared import (
    CLUSTER_CALIBRATION_STEP,
    DEFAULT_CLUSTER_STEP,
    DEFAULT_SUGGEST_STEP,
    PICASA_STEPS,
    Property,
    QLocale,
    Slot,
    _log,
    detector_module,
    embedder_module,
    model_download,
    step_to_threshold,
    threading,
    threshold_to_cluster_step,
)


class FaceScanControllerSettingsMixin:
    """Beállítások, modellállapot és modellletöltés."""


    @Slot(result=bool)
    def isAvailable(self) -> bool:
        """Igaz, ha a modell betöltve, tehát a szkennelés ténylegesen futna."""
        return self._detector.available


    @Slot(result=bool)
    def isEmbeddingAvailable(self) -> bool:
        """Igaz, ha a lenyomat-modell (SFace) betöltve."""
        return self._embedder.available


    @Slot(result=bool)
    def automaticDetectionEnabled(self) -> bool:  # noqa: N802 — QML-slot-stílus
        """A háttérdetektálás kapcsolója; az eredeti alapértéke BE volt."""
        value = self._settings.value(self.AUTOMATIC_DETECTION_KEY, True)
        if isinstance(value, str):
            return value.strip().lower() not in {"", "0", "false", "no", "off"}
        return bool(value)


    @Slot(bool)
    def setAutomaticDetectionEnabled(self, enabled: bool) -> None:  # noqa: N802
        """A globális háttérdetektálás-kapcsoló mentése."""
        self._settings.setValue(self.AUTOMATIC_DETECTION_KEY, bool(enabled))
        if enabled:
            self.scanNewFaces()
        elif self._automatic_scan:
            self.cancelScan()


    @Slot(result=bool)
    def suggestionsEnabled(self) -> bool:  # noqa: N802 — QML-slot-stílus
        """A csoportosítás közbeni névjavaslatok kapcsolója (#4319)."""
        return self._beallitas_bool(self.SUGGESTIONS_ENABLED_KEY, True)


    @Slot(bool)
    def setSuggestionsEnabled(self, enabled: bool) -> None:  # noqa: N802 — QML-slot-stílus
        """A névjavaslatok beállításának mentése."""
        self._settings.setValue(self.SUGGESTIONS_ENABLED_KEY, bool(enabled))


    @Slot(result=int)
    def suggestionThreshold(self) -> int:  # noqa: N802 — QML-slot-stílus
        """A javaslatküszöb a specifikáció 50–95-ös létráján."""
        return self._kuszob_lepcso(self.SUGGEST_STEP_KEY, DEFAULT_SUGGEST_STEP)


    @Slot(int)
    def setSuggestionThreshold(self, step: int) -> None:  # noqa: N802 — QML-slot-stílus
        """A javaslatküszöb mentése a tízfokozatú beállítási létrán."""
        self._settings.setValue(
            self.SUGGEST_STEP_KEY,
            self._ervenyes_kuszob_lepcso(step, DEFAULT_SUGGEST_STEP),
        )


    @Slot(result=int)
    def clusterThreshold(self) -> int:  # noqa: N802 — QML-slot-stílus
        """A csoportküszöb 50-95-ös felületi lépcsője (#5512)."""
        stored = self._settings.value(self.CLUSTER_STEP_KEY, None)
        if stored is not None:
            return self._kuszob_lepcso(self.CLUSTER_STEP_KEY, DEFAULT_CLUSTER_STEP)

        legacy = self._settings.value(self.LEGACY_CLUSTER_STEP_KEY, None)
        if legacy is None:
            return DEFAULT_CLUSTER_STEP
        try:
            legacy_step = int(legacy)
        except (TypeError, ValueError):
            legacy_step = CLUSTER_CALIBRATION_STEP
        legacy_step = self._ervenyes_kuszob_lepcso(
            legacy_step, CLUSTER_CALIBRATION_STEP
        )
        migrated = threshold_to_cluster_step(step_to_threshold(legacy_step))
        self._settings.setValue(self.CLUSTER_STEP_KEY, migrated)
        return migrated


    @Slot(int)
    def setClusterThreshold(self, step: int) -> None:  # noqa: N802 — QML-slot-stílus
        """A csoportküszöb felületi lépcsőjének mentése (#5512)."""
        self._settings.setValue(
            self.CLUSTER_STEP_KEY,
            self._ervenyes_kuszob_lepcso(step, DEFAULT_CLUSTER_STEP),
        )


    def _beallitas_bool(self, key: str, default: bool) -> bool:
        value = self._settings.value(key, default)
        if isinstance(value, str):
            return value.strip().lower() not in {"", "0", "false", "no", "off"}
        return bool(value)


    def _kuszob_lepcso(self, key: str, default: int) -> int:
        value = self._settings.value(key, default)
        try:
            step = int(value)
        except (TypeError, ValueError):
            return default
        return self._ervenyes_kuszob_lepcso(step, default)


    @staticmethod
    def _ervenyes_kuszob_lepcso(step: int, default: int) -> int:
        try:
            requested = int(step)
        except (TypeError, ValueError):
            return default
        return min(PICASA_STEPS, key=lambda candidate: abs(candidate - requested))


    @Slot(result=str)
    def unavailableReason(self) -> str:  # noqa: N802 — QML-slot-stílus
        """Miért NEM indítható az arckeresés — üres sztring, ha indítható.

        #1473: a néma tiltás nálunk visszatérő hibaosztály. A szürke gomb
        önmagában csak annyit üzen, hogy „nem lehet"; a felhasználónak azt
        kell megtudnia, MI hiányzik és HOVA kell tennie. A szöveget azért a
        vezérlő adja, nem a QML: a modell helye XDG-függő felhasználói
        mappa, amit csak Python-oldalról tudunk kiszámolni."""
        if self._detector.available:
            return ""
        if detector_module.resolve_model_path() is not None:
            return self._model_load_failed_text()
        return self._model_missing_text(
            detector_module.MODEL_FILENAME,
            detector_module.MODEL_ENV_VAR,
        )


    @Slot(result=str)
    def embeddingUnavailableReason(self) -> str:  # noqa: N802 — QML-slot-stílus
        """Ugyanez a lenyomat-modellre (SFace) — üres, ha megvan."""
        if self._embedder.available:
            return ""
        if embedder_module.resolve_model_path() is not None:
            return self._model_load_failed_text()
        return self._model_missing_text(
            embedder_module.MODEL_FILENAME,
            embedder_module.MODEL_ENV_VAR,
        )


    def _model_load_failed_text(self) -> str:
        """A fájl megvan, de a modell nem indult el — ne mondjuk, hogy
        hiányzik, mert ez félrevezető és nem segít a hiba megértésében."""
        return self.tr(
            "The model file is present, but PicasaPy could not load it. "
            "Check the application log."
        )


    def _model_missing_text(self, filename: str, env_var: str) -> str:
        """A hiányzó modell egyetlen, cselekvésre váltható mondata.

        A két modell UGYANABBA a mappába kerül (`embedder.default_model_path`
        is a detektor `default_model_dir()`-jét használja), csak a fájlnév
        és a felülbíráló környezeti változó más.

        #1496: az üzenet ELSŐ mondata ma a letöltés gombjára mutat. Amíg a
        kézi másolás volt az egyetlen út, a mondat ott kezdődött — a
        tulajdonosnak, aki nem programozó, ez zsákutca volt. A kézi út
        megmarad (haladóknak és zárt hálózaton), de másodikként."""
        return self.tr(
            "The face recognition model file is missing, so this step cannot "
            'run. Press "Download the model" below, and PicasaPy will get it '
            'for you. If you would rather do it by hand: copy the file "{0}" '
            "into this folder — {1} — or point the {2} environment variable "
            "at it, and then restart PicasaPy."
        ).format(filename, str(detector_module.default_model_dir()), env_var)


    # -- #1496: a modellfájl beszerzése a felületről ------------------------

    @Property(int, notify=_Signals.modelDownloadPercentChanged)
    def modelDownloadPercent(self) -> int:  # noqa: N802 — QML-property-stílus
        """A futó modell-letöltés haladása (0–100), vagy −1, ha nem fut.

        A `scanPercent` mintáját követi: a párbeszéd sávja DEKLARATÍV
        kötéssel figyeli, nem jelzés-kezelőből frissül."""
        return self._model_download_percent


    def _set_model_download_percent(self, percent: int) -> None:
        if percent != self._model_download_percent:
            self._model_download_percent = percent
            self.modelDownloadPercentChanged.emit()


    @Slot(result=str)
    def modelDownloadOffer(self) -> str:  # noqa: N802 — QML-slot-stílus
        """Mit tölt le a program, honnan, mekkorát és milyen licenc alatt.

        Üres sztring, ha nincs mit letölteni — a párbeszéd ezt használja a
        letöltő rész elrejtésére is.

        Miért a vezérlő adja a szöveget, nem a QML: a méret és a licenc a
        `model_download` specjeiben él, a célmappa pedig XDG-függő —
        mindkettő csak Python-oldalról ismert (a `unavailableReason()`
        ugyanezt az elvet követi, #1473)."""
        hianyzo = model_download.missing_specs()
        if not hianyzo:
            return ""
        megabajt = model_download.total_missing_bytes() / (1024 * 1024)
        # A tizedesjegy elválasztója NYELVFÜGGŐ: magyarul vessző, angolul
        # pont. Az f-sztring mindig pontot adna („37.1 MB” magyar mondat
        # közepén) — a `QLocale` a felület nyelvéhez igazítja.
        licencek = " + ".join(dict.fromkeys(spec.license_name for spec in hianyzo))
        return self.tr(
            "PicasaPy downloads the model file from the OpenCV Zoo project "
            "({0} MB in total). Licence: {1} — free to use. The file is "
            "saved here: {2}"
        ).format(
            QLocale().toString(megabajt, "f", 1),
            licencek,
            str(detector_module.default_model_dir()),
        )


    @Slot()
    def downloadModels(self) -> None:  # noqa: N802 — QML-slot-stílus
        """A hiányzó arcfelismerő modellek letöltése — háttérszálon.

        A felhasználó kérésére indul, illetve tartalék útként akkor, ha a
        csoportosításhoz hiányzik az SFace. Normál telepítésen mindkét
        modell csomagolt, ezért nincs letöltési feladat."""
        if self._model_download_percent >= 0:
            return  # már fut — a második kattintás ne indítson újat
        if not model_download.missing_specs():
            # Nem néma: a fájl a helyén van, mégsem tölthető be — ilyenkor
            # a felhasználónak a TÖRLÉS a teendője, nem az újratöltés.
            self.modelDownloadFinished.emit(
                False,
                self.tr(
                    "The model file is already in place, but PicasaPy could "
                    "not load it. It may be damaged: delete it from {0} and "
                    "download it again."
                ).format(str(detector_module.default_model_dir())),
            )
            return
        stop_event = threading.Event()
        self._model_download_stop_event = stop_event
        self._set_model_download_percent(0)
        try:
            self._start_background(
                self._run_model_download,
                args=(stop_event,),
                name="picasapy-face-model-download",
            )
        except BaseException:
            # Beragadás elleni őr: ha a szál el sem indul, a `_run_…`
            # törzse — és vele a jelzőt visszaállító `finally` — SOSEM fut
            # le, a felület pedig örökre „letöltés alatt" maradna. Ez a
            # hibaosztály már kétszer megharapott minket (#550, #1375).
            self._model_download_stop_event = None
            self._set_model_download_percent(-1)
            self.modelDownloadFinished.emit(
                False, self.tr("The download could not be started.")
            )
            raise


    @Slot()
    def cancelModelDownload(self) -> None:  # noqa: N802 — QML-slot-stílus
        """A folyamatban lévő letöltés megszakítása darabhatáron — a
        félkész fájl NEM marad a modell helyén (`download_spec` takarít)."""
        if self._model_download_stop_event is not None:
            self._model_download_stop_event.set()


    def _run_model_download(self, stop_event: threading.Event) -> None:
        siker = False
        uzenet = ""
        try:
            eredmenyek = model_download.download_missing(
                progress=lambda kesz, ossz: self._report_model_download(
                    kesz, ossz, stop_event
                ),
                cancel=stop_event,
            )
            siker, uzenet = self._download_uzenet(eredmenyek)
            if siker:
                if not self._detector.available:
                    try:
                        # A frissen letöltött YuNet-modell azonnal használható
                        # legyen, újraindítás nélkül (#1496).
                        self._detector = self._detector_factory()
                    except Exception:
                        _log.exception(
                            "az ellenőrzött YuNet-modell betöltése hibázott"
                        )
                    if not self._detector.available:
                        siker = False
                        uzenet = self.tr(
                            "PicasaPy verified the downloaded YuNet model, but "
                            "could not load it. Face search is unavailable; "
                            "check the application log."
                        )

                if not self._embedder.available:
                    try:
                        # A YuNet-hiba nem akadályozza meg az SFace külön
                        # betöltési próbáját.
                        self._embedder = self._embedder_factory()
                    except Exception:
                        _log.exception(
                            "az ellenőrzött SFace-modell betöltése hibázott"
                        )
                    if not self._embedder.available and self._detector.available:
                        # A YuNet-keresés működik, csak a csoportosítás nem.
                        uzenet = self.tr(
                            "Face detection is ready, but face grouping is "
                            "unavailable because PicasaPy could not load the "
                            "SFace model. Check the application log."
                        )
        except Exception as error:  # noqa: BLE001 — a letöltés se fagyassza a UI-t
            _log.exception("arcfelismerő modell letöltése hiba")
            siker = False
            uzenet = self.tr("The download failed: {0}").format(str(error))
        finally:
            if self._model_download_stop_event is stop_event:
                self._model_download_stop_event = None
            self._set_model_download_percent(-1)
        if self._embedding_after_download:
            self._embedding_after_download = False
            if siker and self._embedder.available:
                options = self._embedding_options_after_download
                self._embedding_options_after_download = None
                if options is None:
                    options = self._csoportositasi_beallitasok()
                self._start_embedding_worker(*options)
            else:
                self._embedding_options_after_download = None
                self.embeddingModelUnavailable.emit()
        self.modelDownloadFinished.emit(siker, uzenet)


    def _report_model_download(
        self, kesz: int, ossz: int, stop_event: threading.Event
    ) -> None:
        if stop_event.is_set():
            return
        self._set_model_download_percent(round(100 * kesz / ossz) if ossz else 100)


    def _download_uzenet(self, eredmenyek) -> tuple[bool, str]:
        """A letöltés kimenete → EGY felhasználói mondat.

        A `model_download` megnevezett `status`-t ad (nem kivételt és nem
        puszta hamis értéket), hogy itt minden ághoz más, cselekvésre
        váltható mondat tartozhasson."""
        if not eredmenyek:
            return False, self.tr("There was nothing to download.")
        bukott = next((e for e in eredmenyek if not e.ok), None)
        if bukott is None:
            return True, self.tr(
                "The face recognition model has been downloaded. "
                "You can start the search now."
            )
        if bukott.status == model_download.STATUS_CANCELLED:
            return False, self.tr("The download was cancelled. Nothing was saved.")
        if bukott.status == model_download.STATUS_CORRUPT:
            return False, self.tr(
                "The downloaded file was damaged, so PicasaPy threw it away "
                "instead of using it — a damaged model would find faces "
                "wrongly. Please try again."
            )
        if bukott.status == model_download.STATUS_DISK:
            return False, self.tr(
                "The model could not be saved to disk: {0}"
            ).format(bukott.detail)
        return False, self.tr(
            "PicasaPy could not reach the download source. Check your "
            "internet connection and try again."
        )

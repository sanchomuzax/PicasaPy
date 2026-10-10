"""FaceScanController: a SAJÁT (YuNet) arc-detektálás háttérfolyamata és a
„Névtelenek" album QML-hídja (issue #26, javasolt 1. lépcső: „Detektálás +
arc-indexkép (szemvonalra igazítva) → Névtelenek album, csoportosítás
nélkül").

Önálló QObject — a `DedupController`/`FolderTreeController` mintáját
követve NEM az `AppController` mixinje, hogy a `controller.py` (forró
fájl, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést kapja; a
bekötés (öröklés-lista/context-property, Main.qml gomb, a bal hasáb
„Névtelenek" sora) az integrátor feladata — pontosan úgy, ahogy a
`PeopleMixin` is önállóan, host-osztályos teszttel készült (#397), és a
`controller.py`-beli bekötésére vár.

Ha valamelyik modell nincs sem a csomagban, sem a felhasználói
modellmappában, a szkennelés TISZTÁN kikapcsol: a `modelUnavailable`
jelzés megy ki, a meglévő index/alkalmazás-működés érintetlen. A szokásos
telepítés mindkét modellt tartalmazza, így ehhez nem kell hálózat.

IMPORTNÁL A PICASA DÖNTÉSEI SZENTEK: a saját detektorunk KIHAGYJA azokat a
fotókat, amelyeken már van EMBER ÁLTAL adott névcímke (`faces=` legalább
egy azonosított bejegyzéssel) — ezeket SOHA nem értékeljük újra.

#26 (2. lépcső): a `computeEmbeddings()` külön, alacsonyabb prioritású sor.
Az SFace a csomagból töltődik be; ha onnan és a felhasználói
modellmappából is hiányzik, az első csoportosítási kérés elindítja a
tartalék letöltést, majd a csoportosítás a betöltés után a háttérben
folytatódik.

#26 (3. lépcső, bekötés): `unnamedGroups()` adja a „Névtelenek" album
CSOPORTOSÍTOTT nézetét (Picasa „Group by face"/„Expand groups"), az
`assignNameToFaces()` pedig a tömeges névadást („Add a name") — a MEGLÉVŐ
`FacesHelper.addFace()` úton, majd a sikeresen megírt arcokat `'named'`
állapotba állítva (`index.mark_faces_named`), hogy se ez az album, se a
jövőbeli csoportosítás ne értékelje újra."""

from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QSettings, Property, QLocale, QObject, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from picasapy.cvimage import dekodolj_forrast, scale_down
from picasapy.faces import detector as detector_module
from picasapy.faces import embedder as embedder_module
from picasapy.faces import model_download
from picasapy.faces.detector import FaceDetector, rescale_face_detection
from picasapy.faces.embedder import FaceEmbedder
from picasapy.faces.clustering import (
    DEFAULT_CLUSTER_STEP,
    DEFAULT_SUGGEST_STEP,
    PICASA_STEPS,
    step_to_threshold,
)
from picasapy.export import export_sidecar_for_photo
from picasapy.index import (
    PhotoRecord,
    album_photos,
    all_photos,
    clear_faces,
    faces_for_photo,
    faces_missing_embedding,
    ignored_faces,
    group_unnamed_faces,
    ignored_ini_faces,
    javaslatokat_ujraszamol,
    lazitott_lepcso,
    mark_faces_ignored,
    set_suggested_name,
    suggested_faces_for,
    unignore_faces,
    mark_faces_named,
    open_index,
    photos_in_folder,
    face_scan_done,
    forget_face_scan,
    mark_face_scan,
    replace_faces,
    reset_all_faces as reset_all_faces_in_index,
    store_embedding,
    sync_tree,
    unnamed_album_photos,
    unnamed_faces,
)
from picasapy.index.faces_detected import UnnamedFace
from picasapy.index.ignored_ini_faces import IniIgnoredFace
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

from .face_ignore_ini import (
    best_region,
    ignored_regions,
    ini_face_key,
    ini_faces_of,
    match_regions,
    parse_ini_face_key,
    quantize_rect,
)
from .arc_nagyitas_url import arc_cimke
from .filetype_preferences import enabled_filetypes as load_enabled_filetypes
from .faces_helper import FacesHelper
from .worker_thread import BackgroundWorkerMixin
from .display_mode_paint import current_display_mode_suffix

_log = logging.getLogger(__name__)

# A detektálás bemenetének célmérete — a thumbs-cache alapértelmezett
# méreténél (256) nagyobb, hogy a kisebb arcok is megtalálhatók legyenek,
# de nem a teljes felbontás (nagy fotóknál ez percekre lassítaná a
# szkennelést). A YuNet kis felbontáson is jól teljesít (issue #26).
_DETECT_MAX_DIMENSION = detector_module.MAX_DETECTION_DIMENSION

# #26 (3. lépcső): egy csoportban ennyi arcot mutatunk „Expand groups"
# kikapcsolt állapotban — a teljes csoport a bekapcsolt állapotban látszik
# (ld. `unnamedGroups()`). Csak megjelenítési korlát, a kijelölés/névadás
# a NEM mutatott arcokat is eléri (a hívó a mutatott faceId-kat kapja meg,
# tehát ez a korlát a gyakorlatban a kijelölhető halmazt is szűkíti —
# szándékosan: „Expand groups" nélkül a felhasználó a reprezentatív
# részhalmazt nevezi el, ami a Picasa csoport-előnézetének felel meg).
_COLLAPSED_GROUP_PREVIEW = 12


def _path_key(path: str | Path) -> str:
    """A fájlútvonal platformhelyes összehasonlító alakja."""
    return os.path.normcase(os.path.normpath(str(path)))


class FaceScanController(BackgroundWorkerMixin, QObject):
    """A „Névtelenek" album feltöltése: saját arc-detektálás háttérszálon,
    majd a találatok lekérdezése a QML-nek."""

    scanStarted = Signal()
    scanProgress = Signal(int, int)  # (kész, összes)
    scanFinished = Signal(int, int)  # (talált arc, átvizsgált fotó)
    scanCancelled = Signal()
    scanFailed = Signal(str)
    #: #1403: az arc elnevezése után AUTOMATIKUS XMP-írás hibája — az
    #: eredetiben is megnevezett hibaeset („Face tag write failed for read
    #: only file: %s"), ezért nem nyeljük el.
    xmpAutoWriteFailed = Signal(str)
    # A modell hiányzik/nem tölthető be — a szkennelés el sem indul, ez
    # NEM hiba (a funkció tervezett, hiánytűrő kikapcsolása).
    modelUnavailable = Signal()
    _scanWorkerStopped = Signal()

    # #26 (2. lépcső): lenyomat-számítás + csoportosítás — a detektálásnál
    # ALACSONYABB PRIORITÁSÚ, KÜLÖN indítható sor (ld. osztály-docstring).
    embeddingStarted = Signal()
    embeddingProgress = Signal(int, int)  # (kész, összes)
    embeddingFinished = Signal(int, int)  # (lenyomatolt arc, csoportba került arc)
    embeddingCancelled = Signal()
    embeddingFailed = Signal(str)
    embeddingModelUnavailable = Signal()

    # #26 (3. lépcső): a „Névtelenek" album mérete változott (szkennelés,
    # csoportosítás, vagy sikeres tömeges névadás után) — a bal hasáb
    # sorának darabszáma ezt figyeli.
    unnamedCountChanged = Signal()
    # A függő név-javaslat változott; a főnézet erre frissíti a panelt és a
    # személy-album fejlécének javaslatszámát.
    faceSuggestionsChanged = Signal()

    # #4627: a menüsor és a helyi menük Ctrl/Shift ágának megerősítése.
    faceResetConfirmationRequested = Signal(str)

    # #449: a háttér-beolvasás haladása az ALBUMLISTÁBAN jelenik meg
    # („Scanning for faces… %d%% complete"), nem modális ablakban — semmi
    # nem blokkolja a felhasználót. A `scanProgress` jelzés erre kevés: a
    # bal hasáb sorának DEKLARATÍV kötés kell, ezért a százalék NOTIFY-
    # property is (−1 = épp nem fut).
    scanPercentChanged = Signal()

    # #1496: a modellfájl LETÖLTÉSE a felületről. A #1473 óta a párbeszéd
    # megmondja, mi hiányzik — de a felhasználó (aki nem programozó) ettől
    # még nem jutott modellhez, mert a `download_model()` a termékkódból
    # sehonnan nem hívódott.
    #: (siker, felhasználói mondat) — megszakításnál és hibánál is szól,
    #: néma bukás SEHOL.
    #:
    #: „Elindult" jelzés SZÁNDÉKOSAN NINCS (#1496 felülvizsgálat): a
    #: letöltést egyedül a párbeszéd `startDownload()`-ja indítja, ami maga
    #: állítja a `downloading` jelzőt — egy indulás-jelzés ugyanazt mondaná
    #: el másodszor. Az indulást a `modelDownloadPercent` 0-ra váltása is
    #: mutatja.
    modelDownloadFinished = Signal(bool, str)
    modelDownloadPercentChanged = Signal()
    AUTOMATIC_DETECTION_KEY = "faces/automaticDetection"
    SUGGESTIONS_ENABLED_KEY = "faces/suggestionsEnabled"
    CLUSTER_STEP_KEY = "faces/clusterStep"

    def __init__(
        self,
        db_path: str | Path,
        detector: FaceDetector | None = None,
        embedder: FaceEmbedder | None = None,
        faces_helper: FacesHelper | None = None,
        detector_factory: Callable[[], FaceDetector] | None = None,
        embedder_factory: Callable[[], FaceEmbedder] | None = None,
        settings: "QSettings | None" = None,
        face_detection_enabled: Callable[[str], bool] | None = None,
    ) -> None:
        super().__init__()
        self._db_path = Path(db_path)
        # #1403: az „arc elnevezésekor írjuk-e ki az XMP-t" kapcsoló tára. A
        # próbák SAJÁT tárolót adnak — a valódi beállításokat egy teszt nem
        # olvashatja (és nem is írhatja).
        self._settings = settings if settings is not None else QSettings()
        self._face_detection_enabled = face_detection_enabled or (lambda _path: True)
        # Tesztben/CI-ben injektálható helyettesítő detektor/embedder is
        # lehet — alapból a valódi (modell nélkül önmagát kikapcsoló)
        # YuNet/SFace-becsomagolás.
        # #1496: a modellek ÚJRAÉPÍTÉSE a letöltés után ezeken a gyárakon
        # megy. Enélkül a frissen letöltött modell csak újraindítás után
        # élne — a felhasználónak pedig azt ígérjük, hogy a letöltés után
        # rögtön kereshet.
        self._detector_factory = detector_factory or FaceDetector
        self._embedder_factory = embedder_factory or FaceEmbedder
        self._detector = detector if detector is not None else self._detector_factory()
        self._embedder = embedder if embedder is not None else self._embedder_factory()
        # #26 (3. lépcső): a tömeges névadás EZEN keresztül írja a
        # `faces=`/`[Contacts2]`-t — a MEGLÉVŐ `FacesHelper.addFace()` úton,
        # nem új írási logikával (ld. jegy). `None`-nal is működik (pl. a
        # `unnamedGroups`-ot önmagában tesztelő esetekben) — ekkor
        # `assignNameToFaces` egyszerűen hamis eredményt ad, nem hibázik.
        self._faces_helper = faces_helper
        #: #3670: az ini-kből olvasott, Picasa által mellőzött arcok — a bal
        #: hasáb darabszáma minden rács-frissítéskor kéri, a söprés viszont
        #: NAS-on drága. Az album megnyitása, a mellőzés/visszavétel és a
        #: keresés vége frissíti.
        self._ini_ignored_cache: tuple[IniIgnoredFace, ...] | None = None
        self._stop_event: threading.Event | None = None
        #: #4517: a modellhiány oka munkamenetenként egyszer kerül a naplóba.
        self._unavailable_logged = False
        self._automatic_scan = False
        self._pending_face_reset_paths: list[str] = []
        self._resume_scan_after_reset = False
        self._resume_face_reset_force_scan = False
        self._scanWorkerStopped.connect(self._finish_reset_after_scan)
        self._embedding_stop_event: threading.Event | None = None
        #: #449: a futó szkennelés haladása százalékban, −1 ha nem fut
        self._scan_percent = -1
        #: #1496: a futó modell-letöltés haladása, −1 ha nem fut
        self._model_download_percent = -1
        self._model_download_stop_event: threading.Event | None = None
        self._embedding_after_download = False
        self._embedding_options_after_download: tuple[bool, int, int] | None = None
        # #4619: a sikeres detektálás után a második lépés automatikusan
        # indul, ha a névjavaslatok be vannak kapcsolva. A scan-jelzés a
        # workerből érkezik; a kifejezetten sorba tett kapcsolat a GUI-szálra
        # viszi vissza a beállítások olvasását és a következő worker indítását.
        self.scanFinished.connect(
            self._auto_group_after_scan, Qt.ConnectionType.QueuedConnection
        )

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
        """A csoportküszöb SFace-hez kalibrált 50–95-ös lépcsője."""
        return self._kuszob_lepcso(self.CLUSTER_STEP_KEY, DEFAULT_CLUSTER_STEP)

    @Slot(int)
    def setClusterThreshold(self, step: int) -> None:  # noqa: N802 — QML-slot-stílus
        """A csoportküszöb mentése; az érték az SFace-skálára alakul át."""
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

    @Property(int, notify=scanPercentChanged)
    def scanPercent(self) -> int:  # noqa: N802 — QML-property-stílus
        """A futó arc-beolvasás haladása (0–100), vagy −1, ha nem fut.

        A bal hasáb „Scanning for faces…" sora ezt köti (#449) — modális
        ablak SEHOL, a munka a háttérben marad."""
        return self._scan_percent

    def _set_scan_percent(self, percent: int) -> None:
        if percent != self._scan_percent:
            self._scan_percent = percent
            self.scanPercentChanged.emit()

    # -- #1496: a modellfájl beszerzése a felületről ------------------------

    @Property(int, notify=modelDownloadPercentChanged)
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

    @Slot()
    def scanForFaces(self) -> None:
        """A teljes indexelt könyvtár átvizsgálása SAJÁT arc-detektálással.

        Modell hiányában azonnal `modelUnavailable`-t ad és nem indít
        szálat — a hívó UI ekkor a funkciót eleve rejtve/inaktívan
        tarthatja."""
        self._start_face_scan(automatic=False)

    @Slot(str)
    def scanFolder(self, folder_path: str) -> None:  # noqa: N802 — QML-slot-stílus
        """A helyi mappamenüből csak a megadott mappa képeit vizsgálja."""
        with open_index(self._db_path) as conn:
            photos = photos_in_folder(conn, folder_path)
        self._start_face_scan(automatic=False, photos=photos)

    @Slot(str)
    def scanAlbum(self, token: str) -> None:  # noqa: N802 — QML-slot-stílus
        """A helyi albummenüből csak az adott album tagképeit vizsgálja."""
        with open_index(self._db_path) as conn:
            photos = album_photos(conn, token)
        self._start_face_scan(automatic=False, photos=photos)

    def _start_face_scan(
        self,
        *,
        automatic: bool,
        photos: tuple[PhotoRecord, ...] | None = None,
    ) -> None:
        if not self._detector.available:
            # #4517: a felület jelzése mellett a hibanaplóba is kerüljön,
            # különben a „nem talál arcot” okát semmi nem rögzíti.
            if not self._unavailable_logged:
                self._unavailable_logged = True
                _log.warning(
                    "az arcfelismerés nem indul: %s", self.unavailableReason()
                )
            self.modelUnavailable.emit()
            return
        if automatic and self._stop_event is not None:
            return
        self.cancelScan()
        self._automatic_scan = automatic
        stop_event = threading.Event()
        self._stop_event = stop_event
        self._set_scan_percent(0)
        self.scanStarted.emit()
        self._start_background(
            self._run_scan, args=(stop_event, photos), name="picasapy-face-scan"
        )

    @Slot()
    def scanNewFaces(self) -> None:  # noqa: N802 — QML-slot-stílus
        """Az újonnan indexelt képek automatikus háttérvizsgálata.

        A könyvtárszinkron `syncFinished` jelzése hívja. Az indexben már
        vizsgált fájlok mtime/méret alapján kimaradnak; párhuzamos
        szinkronjelzés nem szakítja félbe a futó detektálást."""
        if not self.automaticDetectionEnabled() or self._stop_event is not None:
            return
        self._start_face_scan(automatic=True)

    @Slot(int, int)
    def _auto_group_after_scan(self, _found: int, _scanned: int) -> None:
        """Sikeres keresés után automatikusan indítja a 2. lépést (#4619).

        Az eredeti `FRAddSuggesetions` kapcsolója az egész csoportosítási/
        javaslati lépést kapuzza. A kézi csoportosítás változatlanul elérhető
        kikapcsolt beállítás mellett; az automatikus út a küszöböket a már
        meglévő `computeEmbeddings()` híváson keresztül veszi át.
        """
        if self.suggestionsEnabled():
            self.computeEmbeddings()

    @Slot()
    def cancelScan(self) -> None:
        """A folyamatban lévő szkennelés megszakítása mappa/fotó-határon —
        a már elmentett találatok az indexben maradnak."""
        if self._stop_event is not None:
            self._stop_event.set()

    @Slot(result="QVariantList")
    def unnamedAlbum(self) -> list[dict]:
        """A „Névtelenek" album QML-nek: `[{path, name}, ...]` — LISTA, nem
        tuple (a `people`/`albums` property mintája, MEMORY 2026-07-22)."""
        with open_index(self._db_path) as conn:
            records = unnamed_album_photos(conn)
        return [
            {"path": str(Path(record.folder_path) / record.name), "name": record.name}
            for record in records
        ]

    @Property(int, notify=unnamedCountChanged)
    def unnamedCount(self) -> int:
        """A „Névtelenek" album mérete — hány fotón van legalább egy még
        névtelen SAJÁT találat. A bal hasáb sora ezt mutatja (0 esetén a
        sor rejtve marad — modell nélkül ez a szám mindig 0, a szkennelés
        el sem indul, ld. `scanForFaces`)."""
        with open_index(self._db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT photo_id) AS n FROM face WHERE state = 'unnamed'"
            ).fetchone()
        return int(row["n"]) if row is not None else 0

    @Slot(bool, bool, result="QVariantList")
    def unnamedGroups(self, group_by_face: bool, expand_groups: bool) -> list[dict]:
        """A „Névtelenek" album QML-nek, CSOPORTOSÍTVA (issue #26, 3.
        lépcső) — `[{label, faces: [{faceId, thumbUrl}, ...]}, ...]`.

        `group_by_face=False`: egyetlen csoport, az összes névtelen arc (a
        Picasa „Group by face" kikapcsolt állapota — nincs csoportosítás,
        csak lista).

        `group_by_face=True`: egy csoport a `face_group`-onként (`id`
        szerint), plusz egy utolsó „még csoportosítatlan" csoport a
        `group_id IS NULL` araoknak (pl. lenyomat-számítás előtt/modell
        nélkül minden ide kerül). `expand_groups=False` esetén csoportonként
        legfeljebb `_COLLAPSED_GROUP_PREVIEW` arc látszik (a Picasa
        csoport-előnézete) — a lista maga is CSAK ennyi arcot ad vissza,
        tehát a kijelölés/névadás is erre a részhalmazra korlátozódik,
        amíg a felhasználó be nem kapcsolja a teljes listát.

        Hiányzó fotóméret (width/height az indexben) esetén az adott arc
        kimarad — `addFace()`-hez relatív (rect64) koordináta kell, amit
        méret nélkül nem lehet számolni (ld. `UnnamedFace.rect`)."""
        with open_index(self._db_path) as conn:
            faces = [face for face in unnamed_faces(conn) if face.rect is not None]
        if not group_by_face:
            return [_group_payload(faces, self.tr("All unnamed faces ({0})").format(len(faces)))]
        buckets: dict[int | None, list] = {}
        order: list[int | None] = []
        for face in faces:
            if face.group_id not in buckets:
                buckets[face.group_id] = []
                order.append(face.group_id)
            buckets[face.group_id].append(face)
        ordered_keys = sorted(key for key in order if key is not None)
        if None in buckets:
            ordered_keys.append(None)
        result = []
        for key in ordered_keys:
            members = buckets[key]
            shown = members if expand_groups else members[:_COLLAPSED_GROUP_PREVIEW]
            if key is None:
                label = self.tr("Not yet grouped ({0})").format(len(members))
            else:
                label = self.tr("Group {0} ({1})").format(key, len(members))
            if not expand_groups and len(shown) < len(members):
                label = f"{label}…"
            result.append(_group_payload(shown, label))
        return result

    @Slot("QVariantList", str, result=bool)
    def assignNameToFaces(self, face_ids, name: str) -> bool:
        """Tömeges névadás — a Picasa „Add a name" gombja: *„Assign a name
        to all of the selected faces"*. A MEGLÉVŐ `FacesHelper.addFace()`
        útján ír (nem új logika), majd a sikeresen megírt arcokat `'named'`
        állapotba állítja (`mark_faces_named`), hogy se a „Névtelenek"
        album, se a jövőbeli csoportosítás ne lássa többé — az ALAPSZABÁLY
        (a Picasa döntései szentek) innentől erre a friss, EMBER által
        adott névre is vonatkozik.

        Üres névnél/arclistánál, vagy ha nincs bekötött `FacesHelper`,
        hamis eredmény, írás nélkül. Igaz eredmény csak akkor, ha MINDEN
        kért arcot sikerült megírni — részleges sikernél (pl. egy fájl
        közben törlődött) a sikeres részt megtartjuk, de a visszatérési
        érték hamis, hogy a hívó UI jelezhesse a hiányosságot."""
        clean_name = (name or "").strip()
        if self._faces_helper is None or not face_ids or not clean_name:
            return False
        ids = {int(face_id) for face_id in face_ids}
        with open_index(self._db_path) as conn:
            by_id = {face.id: face for face in unnamed_faces(conn) if face.rect is not None}
        written_ids: list[int] = []
        touched_folders: set[str] = set()
        #: #1403: az érintett FOTÓK (nem mappák) — ezekhez írjuk ki az XMP-t
        written_paths: list[str] = []
        all_ok = True
        for face_id in ids:
            face = by_id.get(face_id)
            if face is None:
                all_ok = False
                continue
            # J1: a kereten túllógó arc keretét a rect64 tartományára vágjuk
            left, top, right, bottom = quantize_rect(face.rect)
            written = self._faces_helper.addFace(
                str(face.photo_path), left, top, right, bottom, clean_name
            )
            if written:
                written_ids.append(face_id)
                touched_folders.add(str(face.photo_path.parent))
                written_paths.append(str(face.photo_path))
            else:
                all_ok = False
        if written_ids:
            with open_index(self._db_path) as conn:
                mark_faces_named(conn, written_ids, clean_name)
                # a `people_in_index` a `folders.has_ini` alapján dönt,
                # melyik mappa `.picasa.ini`-jét olvassa (ld.
                # `index/people.py`) — az ÚJONNAN írt ini (első névadás egy
                # eddig ini nélküli mappában) e nélkül csak a KÖVETKEZŐ
                # háttér-szinkronnál látszana. A `photo_ops_controller`
                # mintáját követve azonnal újraszinkronizáljuk az érintett
                # mappákat, hogy az Emberek-gyűjtemény rögtön frissüljön.
                enabled_filetypes = load_enabled_filetypes(self._settings)
                for folder in touched_folders:
                    if enabled_filetypes is None:
                        sync_tree(conn, folder)
                    else:
                        sync_tree(
                            conn, folder, enabled_filetypes=enabled_filetypes
                        )
                conn.commit()
            self.unnamedCountChanged.emit()
            self._irj_xmp_ha_kell(written_paths)
        return all_ok and bool(written_ids)

    #: #1403: a kapcsoló kulcsa. Az eredeti a `Preferences` alatt tartja, és
    #: az **alapértéke 1 (BE)** — a kapu a `0x00485382`-n, a kezelő a
    #: `0x004852e0`. A Name Tags fül (#4319) vezérlője ezt az állapotot
    #: mutatja és módosítja; a `PersistFaceToFile` az XMP-oldalkocsi írását
    #: kapuzza névadáskor.
    XMP_ON_NAME_KEY = "faces/writeXmpOnName"

    @Slot(result=bool)
    def persistFaceToFile(self) -> bool:  # noqa: N802 — QML-slot-stílus
        """Az arcnév XMP-oldalkocsiba írásának beállítása."""
        return self._beallitas_bool(self.XMP_ON_NAME_KEY, True)

    @Slot(bool)
    def setPersistFaceToFile(self, enabled: bool) -> None:  # noqa: N802 — QML-slot-stílus
        """Az arcnév XMP-oldalkocsiba írásának beállítása."""
        self._settings.setValue(self.XMP_ON_NAME_KEY, bool(enabled))

    def _xmp_iras_bekapcsolva(self) -> bool:
        return self.persistFaceToFile()

    def _irj_xmp_ha_kell(self, utak) -> None:
        """Az elnevezett arcok fotóihoz XMP-sidecar (#1403).

        Az eredeti az arc elnevezése után MAGÁTÓL kiírja az arc-adatot
        (`0x004852e0`, alapérték BE) — ez a parancs második belépési pontja a
        menüpont mellett. A csak olvasható fájl megnevezett hibaeset, ezért a
        hibát jelezzük, de a többi fotót megírjuk."""
        if not utak or not self._xmp_iras_bekapcsolva():
            return
        for ut in dict.fromkeys(utak):
            try:
                export_sidecar_for_photo(Path(ut))
            except OSError as hiba:
                self.xmpAutoWriteFailed.emit(f"{Path(ut).name}: {hiba}")

    @Slot(int, result=bool)
    def acceptSuggestion(self, face_id: int) -> bool:  # noqa: N802
        """A név-javaslat ELFOGADÁSA (pipa): a javasolt nevet ténylegesen
        ráírjuk az arcra — ugyanazon az úton, mint a kézi névadás."""
        with open_index(self._db_path) as conn:
            row = conn.execute(
                "SELECT suggested_name FROM face WHERE id = ?", (int(face_id),)
            ).fetchone()
            name = row["suggested_name"] if row is not None else None
        if not name:
            return False
        accepted = self.assignNameToFaces([int(face_id)], name)
        if accepted:
            self.faceSuggestionsChanged.emit()
        return accepted

    @Slot(int, result=bool)
    def rejectSuggestion(self, face_id: int) -> bool:  # noqa: N802
        """Egyetlen arc név-javaslatának elvetése, az arc mellőzése nélkül."""
        azonosito = int(face_id)
        with open_index(self._db_path) as conn:
            row = conn.execute(
                "SELECT suggested_name FROM face WHERE id = ?", (azonosito,)
            ).fetchone()
            if row is None or not row["suggested_name"]:
                return False
            set_suggested_name(conn, azonosito, None)
            conn.commit()
        self.unnamedCountChanged.emit()
        self.faceSuggestionsChanged.emit()
        return True

    @Slot(str, result=int)
    def personSuggestionCount(self, name: str) -> int:  # noqa: N802
        """Hány MÉG EL NEM DÖNTÖTT javaslat tartozik ehhez a személyhez
        (#2187) — ebből lesz a személy-album fejlécének darabszáma.

        Üres névre nulla: a fejléc kötése akkor is hívja, amikor nem
        személy-album van nyitva."""
        if not name:
            return 0
        with open_index(self._db_path) as conn:
            return len(suggested_faces_for(conn, name))

    @Slot(str, result="QVariantList")
    def personSuggestionPaths(self, name: str) -> list[str]:  # noqa: N802
        """A személy függő javaslatait tartalmazó fotók útvonala (#4588).

        A fejléc egy fotósor-kijelölésen keresztül éri el a javaslatokat;
        ugyanazon a fotón több egyező arc is lehet, ezért az útvonalak
        egyediek. Az üres név nem tartozik személy-albumhoz.
        """
        if not name:
            return []
        with open_index(self._db_path) as conn:
            return list(dict.fromkeys(
                str(arc.photo_path) for arc in suggested_faces_for(conn, name)
            ))

    def _szemely_javaslatai(
        self, name: str, face_ids: list | None
    ) -> list[int]:
        """A művelet HATÓKÖRE: a személy függő javaslatai, opcionálisan a
        megadott arcokra szűkítve (#2187).

        A mérés szerint a `confirmsug` és a `confirmsel` UGYANAZ a kezelő
        (`0x00602640`), egyetlen logikai argumentummal — nálunk ezért egy
        művelet van, és ez a metódus dönti el a hatókört. A szűkítés
        MINDIG a személy javaslatain belül marad: idegen arc azonosítója
        nem hat, akkor sem, ha a hívó odaadja."""
        if not name:
            return []
        with open_index(self._db_path) as conn:
            sajat = [arc.id for arc in suggested_faces_for(conn, name)]
        if face_ids is None:
            return sajat
        kert = {int(azonosito) for azonosito in face_ids}
        return [azonosito for azonosito in sajat if azonosito in kert]

    @Slot(str, "QVariantList", result="QVariantList")
    def personSuggestionIdsForPaths(  # noqa: N802
        self, name: str, paths: list
    ) -> list[int]:
        """A kijelölt FOTÓKON ülő, e személyre szóló függő javaslatok
        arc-azonosítói — a `confirmsel`/`removesel` hatóköre (#2187).

        A rács sora a fotó, a művelet viszont arcokra hat: egy képen több
        arc is javasolhatja ugyanazt a nevet, és a kijelölés mindegyiküket
        lefedi. Idegen személy javaslata nem kerül bele."""
        if not name or not paths:
            return []
        kijelolt = {Path(ut) for ut in paths if ut}
        with open_index(self._db_path) as conn:
            return [
                arc.id
                for arc in suggested_faces_for(conn, name)
                if Path(arc.photo_path) in kijelolt
            ]

    @Slot(str, result=int)
    @Slot(str, "QVariantList", result=int)
    def confirmPersonSuggestions(  # noqa: N802
        self, name: str, face_ids: list | None = None
    ) -> int:
        """A személy javaslatainak JÓVÁHAGYÁSA — `confirmsug` (mind) és
        `confirmsel` (a kijelöltek) egyetlen műveletként.

        A jóváhagyás a nevet TÉNYLEGESEN ráírja az arcra, ugyanazon az
        úton, mint az egy arcra szóló `acceptSuggestion`. Visszatérési
        érték: hány javaslatot hagytunk jóvá."""
        celok = self._szemely_javaslatai(name, face_ids)
        if not celok:
            return 0
        return len(celok) if self.assignNameToFaces(celok, name) else 0

    @Slot(str, result=int)
    @Slot(str, "QVariantList", result=int)
    def removePersonSuggestions(  # noqa: N802
        self, name: str, face_ids: list | None = None
    ) -> int:
        """A személy javaslatainak ELVETÉSE — `removesel`.

        Az elvetés nem névadás és nem mellőzés: a javaslat eltűnik, az arc
        NÉVTELEN marad, hogy egy későbbi futás újra megvizsgálhassa. (A
        „Névtelenek" album csempéjének „x"-e ezzel szemben a MELLŐZÉS,
        #3670 — `ignoreFaces`.)"""
        celok = self._szemely_javaslatai(name, face_ids)
        if not celok:
            return 0
        with open_index(self._db_path) as conn:
            for azonosito in celok:
                set_suggested_name(conn, azonosito, None)
            conn.commit()
        return len(celok)

    #: #3237: a javaslat-lépcső beállítás-kulcsa. A „További javaslatok
    #: keresése" NEM ír bele — az eredeti sem írja vissza a küszöböt
    #: (`moresug`, kezelő `0x00602890`).
    SUGGEST_STEP_KEY = "faces/suggestStep"

    @Slot(result=int)
    def moreSuggestions(self) -> int:  # noqa: N802 — QML-slot-stílus
        """„További javaslatok keresése" — a lépcső TÍZZEL lejjebb (#3237).

        Az eredeti `moresug` a felismerési küszöböt `0,1`-del csökkenti, és a
        beállítást **nem írja vissza**: egy kattintás több javaslatot hoz, de
        a program alapviselkedése változatlan.

        ⚠️ A bináris `0,75`-ös SZÁMÁT nem vesszük át: nálunk a küszöb a
        `step_to_threshold` skáláján él, tehát a **lépcsőt** csökkentjük
        tízzel (`85 → 75`), és abból számolunk küszöböt — a vezérlőt vesszük
        át, nem a számot (#2187).

        Visszatérési érték: hány arcra került ÚJ javaslat.
        """
        if not self.suggestionsEnabled():
            return 0
        lepcso = self._javaslat_lepcso()
        lazitott = lazitott_lepcso(lepcso)
        kuszob = step_to_threshold(lazitott)
        try:
            with open_index(self._db_path) as conn:
                irt = javaslatokat_ujraszamol(conn, kuszob)
                conn.commit()
        except Exception as hiba:  # noqa: BLE001 — a nézet ne fagyjon le
            _log.exception("javaslat-lazítás hiba: %s", self._db_path)
            self.embeddingFailed.emit(str(hiba))
            return 0
        #: ⛔ A beállítást SZÁNDÉKOSAN nem írjuk vissza — ez a lazítás egyszeri.
        if irt:
            self.unnamedCountChanged.emit()
        return irt

    def _javaslat_lepcso(self) -> int:
        """A tárolt javaslat-lépcső (alapértéken a mért `85`)."""
        return self.suggestionThreshold()

    @Slot(list, result=int)
    def ignoreFaces(self, face_ids) -> int:  # noqa: N802 — QML-slot-stílus
        """A kijelölt arcok MELLŐZÉSE — a „Mellőzött emberek" album (#26).

        Az eredetiben ez nem törlés volt: *„Are you sure you want to move
        this person to the ignored people album?"* — a személy egy külön
        albumba került, tehát visszavehető. Nálunk ugyanez: az arc-sor
        megmarad, csak `state = 'ignored'` lesz, így sem a „Névtelenek"
        albumban, sem a csoportosításban nem bukkan fel újra.

        #3670: élőben mérve (picasa-arcfelismeres.md 15.3/b.1) a mellőzés a
        `.picasa.ini`-be is beír — a `faces=` kulcs érintett régiójának
        személy-mezőjébe `ffffffffffffffff` kerül, a fotó többi arca
        érintetlen marad. Enélkül az elvetés más gépre másolt könyvtárban,
        vagy egy friss újraindexelés után elveszne, mert csak a saját
        SQLite-indexünkben élt. Az írás a `FacesHelper.addIgnoredFace()`
        műveleten át megy; `None` `FacesHelper` mellett csak az index
        frissül.

        A mellőzött arcok száma a visszatérési érték."""
        ids = [int(face_id) for face_id in face_ids]
        if not ids:
            return 0
        with open_index(self._db_path) as conn:
            by_id = {face.id: face for face in unnamed_faces(conn) if face.rect is not None}
            mark_faces_ignored(conn, ids)
            conn.commit()
        self._write_ignore_markers([by_id[i] for i in ids if i in by_id])
        self._ini_ignored_cache = None
        self.unnamedCountChanged.emit()
        return len(ids)

    def _write_ignore_markers(self, targets: list[UnnamedFace]) -> None:
        """A `faces=rect64(…),ffffffffffffffff` bejegyzések írása (#3670).

        A keret a rect64 tartományára vágva és rácsára kerekítve megy (J1:
        a kereten túllógó arc különben `ValueError`-t dobna, és a köteg
        többi arca kimaradna). Ha a Picasa ugyanezt az arcot már mellőzte
        (saját, eltérő keretével), nem írunk mellé egy második bejegyzést.
        `None` `FacesHelper` mellett csak az index frissül."""
        if self._faces_helper is None:
            return
        for face in targets:
            rect = quantize_rect(face.rect)
            existing = ignored_regions(ini_faces_of(face.photo_path))
            if best_region(rect, existing) is not None:
                continue
            self._faces_helper.addIgnoredFace(str(face.photo_path), *rect)

    @Slot(list, result=int)
    def resetFacesForPhotos(self, image_paths) -> int:  # noqa: N802 — QML-slot-stílus
        """A kijelölt képek arcadatainak törlése és újrakeresése (#4510).

        A `.picasa.ini` írása kizárólag a `FacesHelper`/`ini` API-n megy.
        Az index saját találatai és átnézettségi jelölése az `index/`
        API-ján keresztül törlődik. A következő keresés a már meglévő
        automatikus háttérúton fut; futó keresés esetén annak biztonságos
        leállása után indul újra.

        Visszatérési értéke a kijelölt, érvényes útvonalak száma."""
        if not image_paths:
            return 0
        paths = tuple(dict.fromkeys(str(path) for path in image_paths if path))
        if not paths:
            return 0

        modifiers = QGuiApplication.keyboardModifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.faceResetConfirmationRequested.emit("removeAllFaceData")
            return 0
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.faceResetConfirmationRequested.emit("resetAllFaces")
            return 0

        for image_path in paths:
            if self._faces_helper is not None:
                self._faces_helper.removeAllFaces(image_path)

        return self._schedule_face_reset(paths)

    @Slot(result=int)
    def removeAllFaceData(self) -> int:  # noqa: N802 — QML-slot-stílus
        """A Ctrl-ág: teljes ini-/index-törlés, majd teljes újra-arcfelismerés."""
        paths = self._all_photo_paths()
        if not paths:
            return 0
        if self._faces_helper is not None and not self._faces_helper.removeAllFaceData(
            paths
        ):
            return 0
        self._ini_ignored_cache = None
        self._schedule_face_reset(paths, force_scan=True)
        return len(paths)

    @Slot(result=int)
    def resetAllFaces(self) -> int:  # noqa: N802 — QML-slot-stílus
        """A Shift-ág: a névhozzárendeléseket törli, az arcokat megtartja."""
        paths = self._all_photo_paths()
        if self._faces_helper is not None and not self._faces_helper.resetAllFaces(
            paths
        ):
            return 0
        with open_index(self._db_path) as conn:
            affected = reset_all_faces_in_index(conn)
            conn.commit()
        self._ini_ignored_cache = None
        self.unnamedCountChanged.emit()
        return affected

    def _all_photo_paths(self) -> tuple[str, ...]:
        """A jelenleg indexelt könyvtár összes fotójának abszolút útvonala."""
        with open_index(self._db_path) as conn:
            return tuple(
                str(Path(photo.folder_path) / photo.name) for photo in all_photos(conn)
            )

    def _schedule_face_reset(
        self, paths: tuple[str, ...], *, force_scan: bool = False
    ) -> int:
        """Az index törlése és az érintett fotók újra-arcfelismerése."""
        if self._stop_event is not None or self._pending_face_reset_paths:
            self._pending_face_reset_paths.extend(
                path
                for path in paths
                if path not in self._pending_face_reset_paths
            )
            self._resume_scan_after_reset = True
            self._resume_face_reset_force_scan |= force_scan
            self.cancelScan()
            return len(paths)

        self._reset_index_faces(paths)
        if not self._detector.available:
            self.modelUnavailable.emit()
        elif force_scan:
            self._start_face_scan(automatic=False)
        else:
            self.scanNewFaces()
        return len(paths)

    def _reset_index_faces(self, image_paths: tuple[str, ...] | list[str]) -> int:
        """A kijelölt fotók származtatott arcadatait üríti az `index/` API-val."""
        with open_index(self._db_path) as conn:
            photos_by_path = {
                _path_key(Path(photo.folder_path) / photo.name): photo.id
                for photo in all_photos(conn)
            }
            photo_ids = {
                photos_by_path[_path_key(path)]
                for path in image_paths
                if _path_key(path) in photos_by_path
            }
            if photo_ids and photo_ids == set(photos_by_path.values()):
                # A teljes könyvtár resetjénél a korábbi klaszter-centroidok
                # is elavulnak. Az index API előbb leválasztja és törli őket;
                # a részleges, kijelöléses ág érintetlen marad.
                reset_all_faces_in_index(conn)
            for photo_id in photo_ids:
                clear_faces(conn, photo_id)
                forget_face_scan(conn, photo_id=photo_id)
            conn.commit()
        if photo_ids:
            self._ini_ignored_cache = None
            self.unnamedCountChanged.emit()
        return len(photo_ids)

    @Slot()
    def _finish_reset_after_scan(self) -> None:
        """A futó szkennelés után érvényesíti a függő reseteket és újraindít."""
        if not self._resume_scan_after_reset:
            return
        paths = tuple(self._pending_face_reset_paths)
        self._pending_face_reset_paths.clear()
        self._resume_scan_after_reset = False
        force_scan = self._resume_face_reset_force_scan
        self._resume_face_reset_force_scan = False
        self._reset_index_faces(paths)
        if not self._detector.available:
            self.modelUnavailable.emit()
        elif force_scan:
            self._start_face_scan(automatic=False)
        else:
            self.scanNewFaces()

    @Slot(result=int)
    def ignoredCount(self) -> int:  # noqa: N802 — QML-slot-stílus
        """Hány arc van a „Mellőzött emberek" albumban — a saját indexben
        mellőzöttek és az eredeti Picasa által mellőzöttek (#3670) együtt."""
        with open_index(self._db_path) as conn:
            own = ignored_faces(conn)
            if self._ini_ignored_cache is None:
                self._ini_ignored_cache = ignored_ini_faces(conn)
        return len(own) + len(_ini_only(own, self._ini_ignored_cache))

    @Slot(result="QVariantList")
    def ignoredGroups(self) -> list[dict]:  # noqa: N802 — QML-slot-stílus
        """A „Mellőzött emberek" album tartalma — az `unnamedGroups()`
        alakjában, egyetlen csoportban.

        Az eredetiben ez egy ALBUM volt (`CAlbumLabel::Ignored` =
        „Ignored people"), nem egy elrejtett szemetes: meg lehetett nézni,
        tehát vissza is lehetett venni belőle.

        #3670 (B2): az eredeti Picasa által mellőzött arcok
        (`faces=…,ffffffffffffffff`) is itt vannak. Ha egy saját, mellőzött
        találat átfedi (`face_ignore_ini.match_regions`), a saját sor
        képviseli; különben az ini-régió önálló elemként, `ini:` kulcsú
        `faceId`-vel jelenik meg."""
        with open_index(self._db_path) as conn:
            faces = [face for face in ignored_faces(conn) if face.rect is not None]
            self._ini_ignored_cache = ignored_ini_faces(conn)
        extra = _ini_only(faces, self._ini_ignored_cache)
        total = len(faces) + len(extra)
        if not total:
            return []
        payload = _group_payload(faces, self.tr("Ignored people ({0})").format(total))
        return [
            {
                **payload,
                "faces": [*payload["faces"], *(_ini_face_payload(item) for item in extra)],
            }
        ]

    @Slot(list, result=int)
    def unignoreFaces(self, face_ids) -> int:  # noqa: N802 — QML-slot-stílus
        """A mellőzés VISSZAVONÁSA: az arcok újra a „Névtelenek" albumba
        kerülnek.

        #3670: a `.picasa.ini`-ben ez a mellőzés jelének törlése (mérve: „a
        visszavétel a névtelenek közé törli a `faces=` bejegyzést"). CSAK a
        pontos (régió, `ffffffffffffffff`) pár megy (`FacesHelper.
        removeIgnoredFace`, B3): ha a régióra közben névcímke került, az
        ember által adott név marad. A saját archoz az átfedés szerint
        illeszkedő ini-régió tartozik (a Picasa kerete eltér a miénktől);
        az `ini:` kulcsú elem a saját ini-régióját viszi."""
        own_ids: list[int] = []
        ini_items: list[tuple[int, tuple[float, float, float, float]]] = []
        for key in face_ids:
            parsed = parse_ini_face_key(key)
            if parsed is not None:
                ini_items.append(parsed)
            else:
                own_ids.append(int(key))
        if not own_ids and not ini_items:
            return 0
        with open_index(self._db_path) as conn:
            by_id = {face.id: face for face in ignored_faces(conn) if face.rect is not None}
            unignore_faces(conn, own_ids)
            conn.commit()
            paths = _photo_paths(conn, {photo_id for photo_id, _rect in ini_items})
        targets = [
            (face.photo_path, best_region(
                quantize_rect(face.rect), ignored_regions(ini_faces_of(face.photo_path))
            ))
            for face in (by_id[i] for i in own_ids if i in by_id)
        ]
        targets += [(paths[pid], rect) for pid, rect in ini_items if pid in paths]
        if self._faces_helper is not None:
            for path, region in targets:
                if region is not None:
                    self._faces_helper.removeIgnoredFace(str(path), *region)
        self._ini_ignored_cache = None
        self.unnamedCountChanged.emit()
        return len(own_ids) + len(ini_items)

    @Slot()
    def computeEmbeddings(self) -> None:
        """Lenyomat-számítás (SFace) a még lenyomat nélküli arcokon, majd a
        névtelen arcok inkrementális csoportosítása — KÜLÖN, a detektálásnál
        alacsonyabb prioritású sor. Ha az SFace a csomagból és a
        felhasználói modellmappából is hiányzik, elindítja a
        háttér-letöltést, majd automatikusan folytatja a csoportosítást."""
        grouping_options = self._csoportositasi_beallitasok()
        if not self._embedder.available:
            if any(
                spec.key == "embedder" for spec in model_download.missing_specs()
            ):
                self._embedding_after_download = True
                self._embedding_options_after_download = grouping_options
                self.downloadModels()
            else:
                self.embeddingModelUnavailable.emit()
            return
        self._start_embedding_worker(*grouping_options)

    def _csoportositasi_beallitasok(self) -> tuple[bool, int, int]:
        """A UI-szálról kiolvassa a csoportosító worker beállításait."""
        return (
            self.suggestionsEnabled(),
            self.suggestionThreshold(),
            self.clusterThreshold(),
        )

    def _start_embedding_worker(
        self, suggestions_enabled: bool, suggest_step: int, cluster_step: int
    ) -> None:
        """A betöltött SFace-szel, rögzített beállításokkal indítja a munkát."""
        self.cancelEmbedding()
        stop_event = threading.Event()
        self._embedding_stop_event = stop_event
        self.embeddingStarted.emit()
        self._start_background(
            self._run_embedding,
            args=(stop_event, suggestions_enabled, suggest_step, cluster_step),
            name="picasapy-face-embed",
        )

    @Slot()
    def cancelEmbedding(self) -> None:
        """A folyamatban lévő lenyomat-számítás megszakítása arc-határon —
        a már elmentett lenyomatok/csoportok az indexben maradnak."""
        if self._embedding_stop_event is not None:
            self._embedding_stop_event.set()

    # -- worker-szál törzse -------------------------------------------------

    def _run_scan(
        self,
        stop_event: threading.Event,
        scoped_photos: tuple[PhotoRecord, ...] | None = None,
    ) -> None:
        try:
            with open_index(self._db_path) as conn:
                photos = all_photos(conn) if scoped_photos is None else scoped_photos
                total = len(photos)
                found = 0
                scanned = 0
                for done, photo in enumerate(photos, start=1):
                    if stop_event.is_set():
                        conn.commit()
                        self.scanCancelled.emit()
                        return
                    photo_path = Path(photo.folder_path) / photo.name
                    if not self._face_detection_enabled(str(photo_path.parent)):
                        self._report_scan(done, total)
                        continue
                    ini_faces = ini_faces_of(photo_path)
                    if any(face.is_identified for face in ini_faces):
                        # a Picasa döntése szent — nem értékeljük újra
                        self._report_scan(done, total)
                        continue
                    if photo_path.suffix.lower() in VIDEO_EXTENSIONS:
                        self._report_scan(done, total)
                        continue
                    # #2519: már lefutott ezen a fájlállapoton — a `face`
                    # tábla ürességéből ez nem látszana (arc nélküli fotó =
                    # nulla sor), ezért kell a külön nyom. A `kizarva`
                    # jelölést a fájl változása sem oldja fel.
                    if face_scan_done(
                        conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
                    ):
                        # #3670: a Picasa a mi keresésünk UTÁN is mellőzhette
                        _mark_previously_ignored(conn, photo.id, ini_faces)
                        conn.commit()
                        self._report_scan(done, total)
                        continue
                    faces = self._detect(
                        photo_path,
                        source_width=photo.width,
                        source_height=photo.height,
                    )
                    replace_faces(conn, photo.id, faces)
                    _mark_previously_ignored(conn, photo.id, ini_faces)
                    mark_face_scan(
                        conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
                    )
                    found += len(faces)
                    scanned += 1
                    # A következő kép detektálása több másodperc lehet; ne
                    # tartsa addig az SQLite írási zárát.
                    conn.commit()
                    self._report_scan(done, total)
                conn.commit()
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-detektálás hiba: %s", self._db_path)
            self.scanFailed.emit(str(error))
            return
        finally:
            self._ini_ignored_cache = None
            if self._stop_event is stop_event:
                self._stop_event = None
                self._automatic_scan = False
            # a sor eltűnik a bal hasábból — akkor is, ha megszakadt vagy
            # hibára futott (#449)
            self._set_scan_percent(-1)
            self._scanWorkerStopped.emit()
        self.unnamedCountChanged.emit()
        self.scanFinished.emit(found, scanned)

    def _report_scan(self, done: int, total: int) -> None:
        """Haladás-jelzés + a bal hasáb sorának százaléka (#449)."""
        self._set_scan_percent(round(100 * done / total) if total else 100)
        self.scanProgress.emit(done, total)

    def _run_embedding(
        self,
        stop_event: threading.Event,
        suggestions_enabled: bool,
        suggest_step: int,
        cluster_step: int,
    ) -> None:
        try:
            with open_index(self._db_path) as conn:
                pending = faces_missing_embedding(conn)
                total = len(pending)
                embedded = 0
                for done, face in enumerate(pending, start=1):
                    if stop_event.is_set():
                        conn.commit()
                        self.embeddingCancelled.emit()
                        return
                    image = self._decode(face.photo_path)
                    detection = face.detection
                    if image is not None and face.photo_width and face.photo_height:
                        image_height, image_width = image.shape[:2]
                        detection = rescale_face_detection(
                            detection,
                            image_width / face.photo_width,
                            image_height / face.photo_height,
                        )
                    embedding = (
                        self._embedder.compute(image, detection)
                        if image is not None
                        else None
                    )
                    if embedding is not None:
                        store_embedding(conn, face.id, embedding)
                        embedded += 1
                    # Az SFace következő futása szintén a tranzakción kívül
                    # történjen.
                    conn.commit()
                    self.embeddingProgress.emit(done, total)
                conn.commit()
                grouped = group_unnamed_faces(
                    conn,
                    suggest_threshold=step_to_threshold(suggest_step),
                    cluster_threshold=step_to_threshold(cluster_step),
                    named_centroids=None if suggestions_enabled else {},
                )
                conn.commit()
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-lenyomat/csoportosítás hiba: %s", self._db_path)
            self.embeddingFailed.emit(str(error))
            return
        finally:
            if self._embedding_stop_event is stop_event:
                self._embedding_stop_event = None
        self.embeddingFinished.emit(embedded, grouped)

    def _detect(
        self,
        photo_path: Path,
        *,
        source_width: int | None = None,
        source_height: int | None = None,
    ):
        image = self._decode(photo_path)
        if image is None:
            return ()
        # A JPEG dekóder minőségi tartaléka a kért 960 px helyett teljes
        # vagy annál még mindig nagyobb képet adhat. A YuNet bemenetét ezért
        # itt is kötelező a határra kicsinyíteni.
        detector_image = scale_down(image, _DETECT_MAX_DIMENSION)
        detections = self._detector.detect(detector_image)
        decoded_height, decoded_width = image.shape[:2]
        if source_width and source_height:
            target_width, target_height = source_width, source_height
        else:
            target_width, target_height = decoded_width, decoded_height
        detector_height, detector_width = detector_image.shape[:2]
        scale_x = target_width / detector_width
        scale_y = target_height / detector_height
        if scale_x == 1 and scale_y == 1:
            return detections
        return tuple(
            rescale_face_detection(detection, scale_x, scale_y)
            for detection in detections
        )

    @staticmethod
    def _decode(photo_path: Path):
        """A fotó redukált dekódolása — a thumbs-cache/dedup mintáját
        követi (`cvimage.read_image_bytes` + `reduced_color_flag`), hogy
        ne épüljön új I/O-út a projektbe."""
        #: #3120: a KÖZÖS belépőn megy — a `cv2.imdecode`-nak nincs nyers
        #: dekódere, tehát a RAW fájlokban nem kerestünk arcot.
        return dekodolj_forrast(photo_path, goal=_DETECT_MAX_DIMENSION)


def _group_payload(faces, label: str) -> dict:
    """Egy `unnamedGroups()`-csoport QML-alakja — a bélyegkép ugyanazt a
    `image://thumbs/<photo_id>` szolgáltatót használja, mint a fő rács
    (ld. `app/models.py:_thumb_url`), forgatás-/szűrő-érzékeny cache-
    buster NÉLKÜL (a Névtelenek albumban ez nem kritikus)."""
    return {
        "label": label,
        "faces": [_face_tile_payload(face) for face in faces],
    }


def _face_tile_payload(face) -> dict:
    """Egy névtelen csempe URL-je arc-kivágással, a közös thumb-provideren."""
    thumb_url = f"image://thumbs/{face.photo_id}"
    if face.rect is not None:
        # A `?&fz=` mellett a provider a PhotoRecordból veszi az elforgatást;
        # nem írunk rá mesterséges `r=0` értéket. A megjelenítési mód marad
        # a szokásos URL-rész, ahogy a teljes képes csempén is volt.
        thumb_url += f"?{arc_cimke(face.rect)}"
    thumb_url += current_display_mode_suffix()
    return {
        "faceId": face.id,
        "thumbUrl": thumb_url,
        # #26 (4. lépcső): a MÉG EL NEM DÖNTÖTT név-javaslat. Az eredeti
        # kérdésként vetette fel (`PeoplePanel::SuggestionFmt` = „%s?"),
        # pipa/x gombbal.
        "suggestedName": face.suggested_name or "",
    }


def _mark_previously_ignored(conn, photo_id: int, ini_faces) -> None:
    """#3670, „kész, ha" 4. pont: a `.picasa.ini`-ben MÁR mellőzöttként
    (`faces=…,ffffffffffffffff`) jelölt régiók saját találatai `'ignored'`
    állapotba kerülnek — egy újraindexelés ne dobja vissza őket a
    „Névtelenek" közé.

    Átfedés alapú, páronkénti egyeztetés (`face_ignore_ini`): a Picasa
    kerete a miénknél mérten nagyobb, bitre sosem egyezik. Egy régió
    legfeljebb egy találatot visz, és csak a még névtelent fordítja át —
    a fotó többi arca névtelen marad."""
    regions = ignored_regions(ini_faces)
    if not regions:
        return
    faces = [face for face in faces_for_photo(conn, photo_id) if face.rect is not None]
    matched = match_regions([(face.id, face.rect) for face in faces], regions)
    unnamed_ids = [face.id for face in faces if face.id in matched and face.state == "unnamed"]
    if unnamed_ids:
        mark_faces_ignored(conn, unnamed_ids)


def _ini_only(
    own: tuple[UnnamedFace, ...] | list[UnnamedFace],
    ini_faces: tuple[IniIgnoredFace, ...],
) -> list[IniIgnoredFace]:
    """Az ini-ben mellőzött arcok közül azok, amelyeket egyetlen saját,
    mellőzött találat sem fed át (#3670, B2) — a többit a saját sor
    képviseli az albumban, így egy arc nem jelenik meg kétszer."""
    own_by_photo: dict[int, list[UnnamedFace]] = {}
    for face in own:
        if face.rect is not None:
            own_by_photo.setdefault(face.photo_id, []).append(face)
    ini_by_photo: dict[int, list[IniIgnoredFace]] = {}
    for item in ini_faces:
        ini_by_photo.setdefault(item.photo_id, []).append(item)
    result: list[IniIgnoredFace] = []
    for photo_id, items in ini_by_photo.items():
        mine = own_by_photo.get(photo_id, [])
        used = set(
            match_regions([(face.id, face.rect) for face in mine], [i.rect for i in items]).values()
        )
        result.extend(item for item in items if item.rect not in used)
    return result


def _ini_face_payload(item: IniIgnoredFace) -> dict:
    """Egy csak az ini-ben mellőzött arc az album QML-alakjában."""
    return {
        "faceId": ini_face_key(item.photo_id, item.rect),
        "thumbUrl": f"image://thumbs/{item.photo_id}{current_display_mode_suffix()}",
        "suggestedName": "",
    }


def _photo_paths(conn, photo_ids: set[int]) -> dict[int, Path]:
    """Fotó-azonosító → teljes útvonal, a megadott azonosítókra."""
    if not photo_ids:
        return {}
    ids = sorted(photo_ids)
    rows = conn.execute(
        "SELECT p.id, fo.path AS folder_path, p.name FROM photos p "
        "JOIN folders fo ON fo.id = p.folder_id "
        f"WHERE p.id IN ({','.join('?' * len(ids))})",
        ids,
    )
    return {int(row["id"]): Path(row["folder_path"]) / row["name"] for row in rows}

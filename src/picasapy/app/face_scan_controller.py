# ruff: noqa: F401 -- module-level names remain available for existing callers/tests.
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

from .face_scan_controller_shared import (
    BackgroundWorkerMixin,
    CLUSTER_CALIBRATION_STEP,
    Callable,
    DEFAULT_CLUSTER_STEP,
    DEFAULT_SUGGEST_STEP,
    FaceDetector,
    FaceEmbedder,
    FacesHelper,
    IniIgnoredFace,
    PICASA_STEPS,
    Path,
    PhotoRecord,
    Property,
    QGuiApplication,
    QLocale,
    QObject,
    QSettings,
    Qt,
    Signal,
    Slot,
    UnnamedFace,
    VIDEO_EXTENSIONS,
    _COLLAPSED_GROUP_PREVIEW,
    _DETECT_MAX_DIMENSION,
    _face_tile_payload,
    _group_payload,
    _ini_face_payload,
    _ini_only,
    _log,
    _mark_previously_ignored,
    _path_key,
    _photo_paths,
    album_photos,
    all_photos,
    arc_cimke,
    best_region,
    clear_faces,
    cluster_step_to_threshold,
    current_display_mode_suffix,
    dekodolj_forrast,
    detector_module,
    embedder_module,
    export_sidecar_for_photo,
    face_scan_done,
    faces_for_photo,
    faces_missing_embedding,
    forget_face_scan,
    group_unnamed_faces,
    hidden_folders_visible,
    ignored_faces,
    ignored_ini_faces,
    ignored_regions,
    ini_face_key,
    ini_faces_of,
    javaslatokat_ujraszamol,
    lazitott_lepcso,
    load_enabled_filetypes,
    logging,
    mark_face_scan,
    mark_faces_ignored,
    mark_faces_named,
    match_named_regions,
    match_regions,
    model_download,
    open_index,
    os,
    parse_ini_face_key,
    photos_in_folder,
    quantize_rect,
    replace_faces,
    rescale_face_detection,
    reset_all_faces_in_index,
    scale_down,
    set_suggested_name,
    step_to_threshold,
    store_embedding,
    suggested_faces_for,
    sync_tree,
    threading,
    threshold_to_cluster_step,
    unignore_faces,
    unnamed_album_photos,
    unnamed_faces,
)

from .face_scan_controller_settings_mixin import FaceScanControllerSettingsMixin
from .face_scan_controller_scan_mixin import FaceScanControllerScanMixin
from .face_scan_controller_unnamed_mixin import FaceScanControllerUnnamedMixin
from .face_scan_controller_suggestions_mixin import FaceScanControllerSuggestionsMixin
from .face_scan_controller_reset_mixin import FaceScanControllerResetMixin
from .face_scan_controller_embedding_mixin import FaceScanControllerEmbeddingMixin
from .face_scan_controller_signals import FaceScanControllerSignalsMixin


class FaceScanController(
    FaceScanControllerSettingsMixin,
    FaceScanControllerScanMixin,
    FaceScanControllerUnnamedMixin,
    FaceScanControllerSuggestionsMixin,
    FaceScanControllerResetMixin,
    FaceScanControllerEmbeddingMixin,
    FaceScanControllerSignalsMixin,
    BackgroundWorkerMixin,
    QObject,
):
    """A „Névtelenek" album QML-hídja; a műveletek tematikus mixinekben élnek."""

    AUTOMATIC_DETECTION_KEY = "faces/automaticDetection"

    SUGGESTIONS_ENABLED_KEY = "faces/suggestionsEnabled"

    CLUSTER_STEP_KEY = "faces/clusterStep2"

    LEGACY_CLUSTER_STEP_KEY = "faces/clusterStep"

    UNNAMED_WELCOME_SHOWN_KEY = "faces/unnamedWelcomeShown"


    #: #1403: a kapcsoló kulcsa. Az eredeti a `Preferences` alatt tartja, és
    #: az **alapértéke 1 (BE)** — a kapu a `0x00485382`-n, a kezelő a
    #: `0x004852e0`. A Name Tags fül (#4319) vezérlője ezt az állapotot
    #: mutatja és módosítja; a `PersistFaceToFile` az XMP-oldalkocsi írását
    #: kapuzza névadáskor.
    XMP_ON_NAME_KEY = "faces/writeXmpOnName"


    #: #3237: a javaslat-lépcső beállítás-kulcsa. A „További javaslatok
    #: keresése" NEM ír bele — az eredeti sem írja vissza a küszöböt
    #: (`moresug`, kezelő `0x00602890`).
    SUGGEST_STEP_KEY = "faces/suggestStep"


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
        #: #4586: a futó keresés hátralévő (még nem ellenőrzött) fájljai
        self._unchecked_files = 0
        #: #4586: a futó keresés által ténylegesen detektálandó, még nem
        #: kész fotók (`_path_key`); a szálak között `_pending_lock` védi
        self._pending_paths: set[str] = set()
        self._pending_lock = threading.Lock()
        #: #4586: a lenyomat-számítás haladása százalékban, −1 ha nem fut
        self._sorting_percent = -1
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

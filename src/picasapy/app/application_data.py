"""application data az alkalmazásindítóhoz."""

from __future__ import annotations

# ruff: noqa: F821
# These function bodies are rebound into application.py's shared namespace.

def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse (#1217).

    A modul többi platformfüggő ága nevesített `platform=` paramétert kap;
    ez az egyetlen, amit nem hívunk paraméterrel (a Qt indulása ELŐTT fut).
    """
    return sys.platform

def _thumbnail_cache_size(device_pixel_ratio: float) -> int:
    """A cache-elt thumbnail célmérete (leghosszabb oldal, px).

    A cél mindig legalább a rács legnagyobb megjelenítési mérete, a
    képernyő devicePixelRatio-jával szorozva — így a GridView-delegate
    Image-e (ThumbDelegate.qml) minden csúszka-fokon KICSINYÍTÉSSEL áll
    elő a cache-elt képből, sosem nagyítással (ami homályos lenne).
    Felfelé kerekítünk (math.ceil), hogy törtszámú DPR (pl. 1.5) se
    essen a küszöb alá. RPi5-ön jellemzően DPR=1 (natív HDMI kimenet),
    de HiDPI monitoron (DPR=2) is éles maradjon a legnagyobb fokozat —
    ezért nem rögzítünk fix 256-os cache-méretet, hanem a tényleges
    képernyőhöz igazítjuk.
    """
    ratio = max(device_pixel_ratio, 1.0)
    return math.ceil(_GRID_MAX_THUMB_PX * ratio)

def _screen_device_pixel_ratio(app: QGuiApplication) -> float:
    """A elsődleges képernyő devicePixelRatio-ja; hiányzó képernyőnél 1.0."""
    screen = app.primaryScreen()
    return screen.devicePixelRatio() if screen is not None else 1.0

def _onjavito_kollazsmappa(conn, settings: QSettings) -> None:
    """A Kollázsok mappa felvétele az indexbe INDULÁSKOR (#1075).

    A tulajdonos jelentése a v0.8.18-ról: *„nincsen Kollázsok mappa sehol,
    eltűnt. A Projektek mappa alatt sincsen semmi ismét."*

    A Projektek gyűjtemény két feltételt kér: a mappa legyen az indexben, és
    a `.picasa.ini`-je hordozza a `P2category`-t. Mindkettőt eddig KIZÁRÓLAG
    a mentés állította elő (#1046, #1048), tehát visszamenőleg semmi:

    * a 0.8.8 ELŐTT készült kollázsok mappájában nincs `.picasa.ini`, és a
      frissítés nem javította utólag;
    * ha az indexelés egyszer elbukott, a mentés-ág némán továbbment, és a
      mappa soha többé nem került be.

    Ezért fut ez minden induláskor. A megjelölés feltétele szigorú (ld.
    `ensure_project_album`): csak a MI kimenetünket jelöljük meg.

    A hiba nyelt — egy önjavítási kísérlet soha nem akadályozhatja meg az
    indulást —, de NAPLÓZVA: a #1075 másik fele éppen az volt, hogy a néma
    ág miatt vakon álltunk."""
    try:
        collage_output = _lazy_app_symbol("collage_output")
        collage_prefs = _lazy_app_symbol("collage_prefs")

        mappa = collage_output.output_dir(settings.value(collage_prefs.OUTPUT_DIR_KEY))
        if not mappa.is_dir():
            return
        collage_output.ensure_project_album(mappa)
        # #1674: inkrementális — a Kollázsok mappa induláskor rendszerint
        # változatlan, és a #1675 védelme óta a sorai is megmaradnak, tehát
        # a kihagyás feltétele teljesül. Így a mappa fájljait meg sem
        # statoljuk.
        enabled_filetypes = load_enabled_filetypes(settings)
        scan_options = (
            {"enabled_filetypes": enabled_filetypes}
            if enabled_filetypes is not None
            else {}
        )
        sync_folder(conn, mappa, mappa, incremental=True, **scan_options)
    except Exception:  # noqa: BLE001 - az indulás soha nem hiúsulhat meg tőle
        logging.getLogger(__name__).warning(
            "a Kollázsok mappa indulási felvétele hibára futott", exc_info=True
        )

def _ujraindexelt_exportcelok(conn, settings: QSettings) -> None:
    """A nyilvántartott exportcélok visszavétele az indexbe INDULÁSKOR
    (#1565) — a `_onjavito_kollazsmappa` (#1075) párja.

    ⚠️ **Enélkül a javítás egyetlen munkamenetig élne.** A közvetlenül
    előtte futó `prune_foreign_folders` (#58) MINDEN olyan mappát töröl az
    indexből, amely egyik figyelt gyökér alatt sincs — az exportcél pedig
    épp ilyen (`<Képek>/Picasa/Exports`). A felhasználó tehát exportálás
    után látná a képeit, a következő indításnál viszont az „Exportált
    képek" ismét üres rácsot nyitna. Ugyanez a szerkezet tartja bent a
    Kollázsok mappát is.

    A forrás a korlátos, létezésre szűrt nyilvántartás (`exported_folders`,
    #457) — figyelt gyökeret NEM veszünk fel a felhasználó nevében, a
    `WatchedFolders.txt` érintetlen marad. A gyökér mindig MAGA a célmappa,
    tehát egyetlen mappa kerül be, nem részfa.

    A hiba nyelt (az indulás soha nem hiúsulhat meg tőle), de naplózva."""
    try:
        mappak = existing_exported_folders(settings.value(EXPORTED_FOLDERS_SETTINGS_KEY))
    except Exception:  # noqa: BLE001 - olvashatatlan beállítás sem állíthat meg
        logging.getLogger(__name__).warning(
            "az exportcélok nyilvántartása nem olvasható", exc_info=True
        )
        return
    for mappa in mappak:
        try:
            # #1674: inkrementális — az exportcélok a #1667 védelme óta
            # bent maradnak az indexben, tehát változatlan célnál nincs
            # fájlonkénti statolás.
            enabled_filetypes = load_enabled_filetypes(settings)
            scan_options = (
                {"enabled_filetypes": enabled_filetypes}
                if enabled_filetypes is not None
                else {}
            )
            sync_folder(
                conn, Path(mappa), Path(mappa), incremental=True, **scan_options
            )
        except Exception:  # noqa: BLE001 - egy rossz cél ne vigye el a többit
            logging.getLogger(__name__).warning(
                "az exportcél indulási felvétele hibára futott: %s",
                mappa,
                exc_info=True,
            )

def _takaritas_gyokerei(roots: tuple[str | Path, ...], settings: QSettings) -> tuple[str, ...]:
    """A #58 induláskori takarítás VÉDETT gyökerei (#1667).

    A figyelt gyökerek mellé a **nyilvántartott exportcélok** is bekerülnek.
    Az exportcél a #1565 óta SAJÁT GYÖKÉRKÉNT van indexelve — a takarítás
    szempontjából tehát pontosan olyan jogos horgony, mint egy figyelt
    mappa, nem „ottragadt idegen mappa".

    ## Miért ez a #1667 javítása

    A takarítás eddig minden induláskor kidobta az exportcélok mappa- ÉS
    fotósorait (a `folder_scan_state`-tel együtt), a rá következő
    `_ujraindexelt_exportcelok` pedig NULLÁRÓL építette vissza őket. Az
    üres `photos` tábla miatt a `_sync_folder` inkrementális kihagyása nem
    tudott működni: minden exportált képre lefutott a (drága) EXIF/IPTC-
    olvasás. MÉRVE (RPi5, 4 exportcél / 180 kép): **180 fájlnyitás
    indulásonként**; a védelemmel **0**. A tulajdonos gépén ugyanez a
    szakasz **8 406 ms** volt — az indulás 77,8%-a (#1667).

    ## Amit a védelem nem tesz meg

    A már nem NYILVÁNTARTOTT exportcél (kiesett a 20 elemű listából)
    továbbra is kitakarítódik. A nyilvántartott, de a lemezen épp nem
    látható cél viszont bent marad: a hiány nem bizonyíték (#1560), és a
    listát szándékosan nem szűrjük létezésre — ld.
    `registered_exported_folders`."""
    return (
        *(str(root) for root in roots),
        *registered_exported_folders(settings.value(EXPORTED_FOLDERS_SETTINGS_KEY)),
        *_kollazs_gyoker(settings),
    )

def _kollazs_gyoker(settings: QSettings) -> tuple[str, ...]:
    """A Kollázsok mappa mint VÉDETT gyökér (#1675).

    Ugyanaz az eset, mint az exportcél (#1667): a MI kimenetünk, saját
    gyökérként indexelve — nem „ottragadt idegen mappa". A takarítás eddig
    minden induláskor kidobta, a `_onjavito_kollazsmappa` (#1075) pedig
    NULLÁRÓL építette vissza; az üres `photos` tábla miatt a `sync_folder`
    inkrementális kihagyása (#139) nem tudott működni, tehát **minden
    kollázs képfájlja megnyílt minden induláskor**. MÉRVE (mutációval, a
    #1675 őrében): három kollázsra három fájlnyitás, a védelemmel nulla.

    A #1675 kérdése az volt, a #1075 SZÁNDÉKA szerint védett-e — nem
    analógiából. Az: a `_onjavito_kollazsmappa` docstringje kimondja, hogy
    a mappának az indexben KELL lennie (a Projektek gyűjtemény két
    feltételének egyike), és hogy csak a MI kimenetünket jelöljük meg. Egy
    gyökér, amit minden induláskor vissza kell építeni, definíció szerint
    nem idegen.

    A létezésre — az exportcélokhoz hasonlóan — SZÁNDÉKOSAN nem szűrünk: a
    hiány nem bizonyíték (#1560), és egy épp leválasztott meghajtón lévő
    kollázsmappa sorai sem eshetnek ki emiatt.
    """
    try:
        collage_output = _lazy_app_symbol("collage_output")
        collage_prefs = _lazy_app_symbol("collage_prefs")

        return (str(collage_output.output_dir(settings.value(collage_prefs.OUTPUT_DIR_KEY))),)
    except Exception:  # noqa: BLE001 — a takarítás soha nem hiúsulhat meg tőle
        logging.getLogger(__name__).warning(
            "a Kollázsok mappa védett gyökérként nem oldható fel", exc_info=True
        )
        return ()

def _exportcelok_visszavetele(index_db: Path, settings: QSettings) -> None:
    """A #1565 visszavétele SAJÁT kapcsolaton, az első képkocka UTÁN (#1667).

    Az indexkarbantartásnak semmi köze ahhoz, hogy az ablak megjelenjen —
    a #1601 ugyanezért tolta a könyvtár betöltését a `frameSwapped` mögé.
    A `_takaritas_gyokerei` védelme óta ez a lépés önjavítás: azt hozza
    rendbe, ami a program KIKAPCSOLT állapotában változott (új fájl az
    exportmappában), illetve azt, amit egy korábbi verzió takarítása még
    kidobott.

    A hiba nyelt — egy önjavítás soha nem viheti el a felületet —, de
    naplózva."""
    try:
        with open_index(index_db) as conn:
            _ujraindexelt_exportcelok(conn, settings)
    except Exception:  # noqa: BLE001 - a felület már áll, ez csak karbantartás
        logging.getLogger(__name__).warning(
            "az exportcélok visszavétele hibára futott", exc_info=True
        )

def _data_dir(platform: str | None = None) -> Path:
    """Az index-SQLite (+ zárolófájl) mappája — ha a "Move Database"
    dialóguson (#368) keresztül egyszer már áthelyezésre került, az
    útvonal-felülbírálás (`data_location.py`) felülírja a platform-
    alapértelmezést; ilyenkor a cache-cel EGYESÍTVE ugyanazt a mappát
    adja vissza, mint `_cache_dir()` (ld. ott)."""
    active_platform = sys.platform if platform is None else platform
    override = read_data_root(_config_dir(platform=active_platform))
    if override is not None:
        return override
    return default_storage_paths(active_platform).data

def _cache_dir(platform: str | None = None) -> Path:
    """A thumbnail-lemezcache mappája — áthelyezés után (#368) a
    `_data_dir()`-rel EGYESÍTVE, hogy a Picasa-paritású "egy adatbázis-
    mappa" elv teljesüljön (a hívó ide illeszti a "thumbs" alkönyvtárat,
    ld. `run()`)."""
    active_platform = sys.platform if platform is None else platform
    override = read_data_root(_config_dir(platform=active_platform))
    if override is not None:
        return override
    return default_storage_paths(active_platform).cache

def _config_dir(platform: str | None = None) -> Path:
    active_platform = sys.platform if platform is None else platform
    return default_storage_paths(active_platform).config

def _bootstrap_storage(
    platform: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    acquire_lock: Callable[[Path], object | None] | None = None,
    migrate: Callable[[StoragePaths, StoragePaths], object] | None = None,
) -> StorageBootstrap:
    """A Qt-zárolót a platformfüggetlen, tesztelhető bootstraphoz köti."""
    active_platform = sys.platform if platform is None else platform
    return bootstrap_storage(
        active_platform,
        acquire_lock=(_acquire_instance_lock if acquire_lock is None else acquire_lock),
        environ=environ,
        home=home,
        migrate=migrate,
    )

def load_screensaver_window(
    engine: QQmlApplicationEngine, saver: ScreensaverRunBridge
):
    """A `--screensaver` önálló vetítőablaka (#4613); `None`, ha nem töltődött be.

    Itt, és nem a `screensaver_mode.py`-ban regisztrál, mert a
    `kepesseg_or.py` a kontextus-objektumokat ebben a fájlban méri.
    """
    engine.addImageProvider(
        display_photo_provider.PROVIDER_NAME,
        display_photo_provider.DisplayPhotoProvider(),
    )
    engine.addImportPath(str(_APP_DIR / "qml"))
    engine.rootContext().setContextProperty("saver", saver)
    engine.load(str(_APP_DIR / "qml" / "ScreensaverWindow.qml"))
    roots = engine.rootObjects()
    return roots[0] if roots else None

def _fuggo_koltozes_indulaskor() -> KoltozesEredmeny:
    """A KÖVETKEZŐ indulásra előjegyzett adatbázis-költözés elvégzése (#3214).

    A mért eredetiben a „Move Database" gomb csak szándékot rögzít, a
    másolás pedig induláskor fut, saját haladásjelző ablakkal
    (`moving_database.fen`). Ezért hívódik ez a tárhely-előkészítés
    (`_bootstrap_storage`, zár + útvonalak) **előtt**: mire az útvonalak
    kiszámolódnak, a felülbírálás már az új helyre mutat, tehát a program
    az ÚJ helyről indul — nem kell külön újraindítás.

    Szándék nélkül a függvény semmit nem tesz (ablak sem jön létre).
    """
    config_dir = _config_dir()
    cel = read_pending_root(config_dir)
    if cel is None:
        return KoltozesEredmeny()

    koltozes_hid = KoltozesHid(cel)
    indulasi_koltozo = IndulasiKoltozo(koltozes_hid)
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(_APP_DIR / "qml"))
    engine.rootContext().setContextProperty("koltozes", koltozes_hid)
    engine.load(str(_APP_DIR / "qml" / "StartupRelocateWindow.qml"))

    # a munka HÁTTÉRSZÁLON fut (nyilvántartva, #430/#438/#988), közben ez a
    # hurok tartja életben a haladásjelző ablakot
    hurok = QEventLoop()
    indulasi_koltozo.kesz.connect(hurok.quit, Qt.ConnectionType.QueuedConnection)
    indulasi_koltozo.inditsd(config_dir, _data_dir() / "index.db", _cache_dir() / "thumbs")
    hurok.exec()
    indulasi_koltozo.waitForBackgroundWorkers(60.0)

    for ablak in engine.rootObjects():
        ablak.close()
    engine.deleteLater()
    return indulasi_koltozo.eredmeny

def allitsd_be_a_stilust() -> None:
    """A Quick Controls stílusa: `PicasaStyle`, tartalékként `Fusion` (#901).

    A saját stílus EGYETLEN vezérlőt visz — a buboréksúgót
    (`qml/PicasaStyle/ToolTip.qml`): a felület mind a 24 `ToolTip`-használata
    a Qt CSATOLT alakját használja, az pedig egyetlen, a stílustól kapott
    példányt jelenít meg. Így lett „egy hely" a buborékból anélkül, hogy a
    lebegtetés/pozicionálás logikáját 253 hívóhelyen átírnánk.

    Minden más vezérlő a `Fusion` tartalékra esik — ez a Quick Controls
    dokumentált viselkedése, és pontosan a korábbi állapotot adja.

    A függvény a tesztekből is hívható: a stílus FOLYAMAT-szintű, tehát a
    QML-motor létrehozása ELŐTT kell beállítani.
    """
    QQuickStyle.setFallbackStyle("Fusion")
    QQuickStyle.setStyle("PicasaStyle")

def _watched_folders_path() -> Path:
    """A `WatchedFolders.txt` útvonala — kis-nagybetű-független kereséssel
    (#145): élesben (pl. importált/áthozott konfig-könyvtárban) kisbetűs
    néven is előfordulhat. Ha nincs ilyen fájl, a kanonikus nevet adja
    vissza (ide fog írni a `write_watched_folders`)."""
    config_dir = _config_dir()
    return find_watched_folders_file(config_dir) or (config_dir / WATCHED_FOLDERS_NAME)

def _exclude_folders_path() -> Path:
    """A `FRExcludeFolders.txt` útvonala — kis-nagybetű-független kereséssel
    (#145/#449, a `_watched_folders_path` mintáját követve). NEGYEDIK,
    a figyelt-mappa hármastól (Scan Always/Once/Remove) FÜGGETLEN
    kapcsoló: az arcfelismerésből kizárt mappák (ld.
    `library_controller.py`)."""
    config_dir = _config_dir()
    return find_exclude_folders_file(config_dir) or (config_dir / EXCLUDE_FOLDERS_NAME)

def _resolve_roots(argv: list[str]) -> tuple[str, ...]:
    if len(argv) > 1:
        return tuple(argv[1:])
    return read_watched_folders(_watched_folders_path())

def _offer_error_log(path: Path) -> None:
    """Adatbázis-hiba után felajánlja a napló megtekintését (#449).

    Az eredeti szövege: „There were errors loading the Picasa database.
    Would you like to view the error log?" — a megnyitás a rendszer
    társított alkalmazásával megy. A program a válasz után elindul: az
    index a következő beolvasáskor újraépül.
    """
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QMessageBox

    text = QCoreApplication.translate(
        "startup",
        "There were errors loading the PicasaPy database. Would you like to view the error log?",
    )
    answer = QMessageBox.question(
        None, QCoreApplication.translate("startup", "Database error"), text
    )
    if answer == QMessageBox.StandardButton.Yes and path.exists():
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

def _acquire_instance_lock(data_dir: Path) -> QLockFile | None:
    """Egy-példányos futás: zárolófájl; ha már fut a PicasaPy, None.

    A QLockFile a PID-et is tárolja, így az összeomlott példány elavult
    zárját magától felismeri és átveszi.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(data_dir / "picasapy.lock"))
    if lock.tryLock(100):
        return lock
    return None

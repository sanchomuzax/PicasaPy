"""application startup controllers az alkalmazásindítóhoz."""

from __future__ import annotations

# ruff: noqa: F821
# These function bodies are rebound into application.py's shared namespace.

def _startup_step_create_edit_and_file_controllers(state):
    controller = state.controller
    provider = state.provider

    # szerkesztő-előnézet (#19): a provider a filters= láncot alkalmazva
    # rendereli a képet; a hidat az EditController adja a QML-nek
    edit_preview = _lazy_app_symbol("EditPreviewProvider")()
    EditController = _lazy_app_symbol("EditController")
    edit_controller = EditController(edit_preview)
    # #3187: a kettős nézet MÁSODIK felének önálló szerkesztési állapota. A
    # rekesz (`slot`) miatt ugyanarra a fotóra is két független lánc állhat a
    # szolgáltató gyorsítótárában; a logikai fotó-azonosító (ini-írás)
    # változatlan. A második vezérlő CSAK előnézetet ad: a szerkesztő
    # parancsai továbbra is az elsőn dolgoznak (a parancs-irányítás a jegy
    # következő lépése).
    edit_controller_masodik = EditController(edit_preview, slot="masodik")
    SecondPreview = _lazy_app_symbol("SecondPreview")
    second_preview = SecondPreview(edit_controller_masodik)
    controller.set_edit_controllers(edit_controller, edit_controller_masodik)
    # #3649: a két „aa"-fél összekötése — a fókuszváltás (`swapAaFocus`)
    # ezen át cseréli a festett maszkot a két fél között, ahelyett hogy
    # kiürítené (docs/specs/ui-audit-editor.md 4/b.1).
    edit_controller.link_aa_partner(edit_controller_masodik)
    edit_controller_masodik.link_aa_partner(edit_controller)
    # #644: minden mentett szerkesztési lánc a TARTÓS naplóba is bekerül — ez
    # az egyetlen nyomunk, ha a párhuzamosan futó Picasa később felülírja a
    # `.picasa.ini`-t a saját adatbázis-rekordjával.
    #
    # #750: ez a JELZÉS-kötés csak a szerkesztőé, mert az `EditController`
    # önálló QObject. A többi lánc-író (csoportos effekt, a két effekt-
    # beillesztés, a lemezre mentés) maga is az `AppController` szelete,
    # ezért közvetlenül a `recordSavedChains()`-t hívja — nincs második
    # jelzés-út, amit itt el lehetne felejteni bekötni.
    edit_controller.chainSaved.connect(controller.recordSavedChain)
    # #3014: az „aa" mód memóriás fele a kilépéskor a második rekeszből ír —
    # az a lánc is a naplóba való
    edit_controller_masodik.chainSaved.connect(controller.recordSavedChain)
    # #3462: a mentés a szerkesztő munkamenetében élő festett maszkot is
    # beégeti — különben a festhető effekt a mentett fájlban az egész képre
    # kerülne, eltérően attól, amit az előnézet mutatott.
    controller.set_paint_strokes_provider(edit_controller.paint_strokes_for_path)

    # effekt-gomb bélyegképek (#338): a meglévő thumbnail-provider
    # regisztrációját (a teljes könyvtár fotóit) használja fel útvonal-
    # feloldásra, saját aszinkron poollal renderel
    effect_thumb_provider = _lazy_app_symbol("EffectThumbnailProvider")(
        provider.photo_record
    )

    # fájlműveletek (#15): kontextusmenü/F2 híd + resync a műveletek után
    FileOpsController = _lazy_app_symbol("FileOpsController")
    fileops_controller = FileOpsController()
    wire_fileops(fileops_controller, controller)

    # megjelenítési mód (#1575/#1576): a `Nézet ▸ Megjelenítési mód` almenü
    # állapota a KÉPERNYŐRE ható átalakítóig. A visszaadott átvezetőt névre
    # kötjük, hogy a kapcsolat a motor életében biztosan éljen.
    # #3837: a kettős nézet MÁSODIK vezérlője (`@masodik` rekesz) is
    # frissüljön módváltáskor — enélkül a második fél a régi (jelöletlen)
    # képet mutatta tovább.
    _display_mode_bridge = _lazy_app_symbol("wire_display_mode")(
        controller, edit_controller, edit_preview, edit_controller_masodik
    )

    # színkezelés (#1725): a `Nézet ▸ Színkezelés használata` kapcsoló a
    # beágyazott ICC-profil érvényesítéséig. Ugyanaz a névre kötés, mint
    # fentebb — a bekötés a motor életében éljen.
    _color_management_bridge = _lazy_app_symbol("wire_color_management")(
        controller, edit_controller, edit_preview
    )

    # #367: az általános ConfirmDialog "Ne kérdezze meg újra" tára — a
    # controllerrel közös QSettings("PicasaPy", "PicasaPy")-ba ír
    ConfirmSettingsBridge = _lazy_app_symbol("ConfirmSettingsBridge")
    confirm_settings = ConfirmSettingsBridge()
    # #4137: a webkamerapanelhez tartozó beállítások és kimeneti útvonalak.
    CameraCaptureController = _lazy_app_symbol("CameraCaptureController")
    camera_capture_controller = CameraCaptureController(
        QSettings("PicasaPy", "PicasaPy")
    )

    # #1792: az album-fejléc gombsorának összeállítása — ugyanabba a
    # közös QSettings("PicasaPy", "PicasaPy")-ba ír, mint a fenti híd
    GombsavBridge = _lazy_app_symbol("GombsavBridge")
    gombsav = GombsavBridge()

    # meglévő Picasa-telepítés átvétele (#146): felderítés + a kijelölt
    # mappák hozzáadása a meglévő addWatchedFolder úton
    DiscoveryController = _lazy_app_symbol("DiscoveryController")
    discovery_controller = DiscoveryController(
        add_folder=controller.addWatchedFolder,
        # #1622: az induláskori felajánlás EGYSZER fut le — a jelölőt a
        # KÖZÖS beállítás-tároló őrzi (`QSettings("PicasaPy", "PicasaPy")`,
        # ugyanaz, amibe a `ConfirmSettingsBridge` is ír).
        settings=QSettings(),
    )

    # kép/mappa ablakra ejtése (#237): a kép mappája (vagy maga a mappa)
    # figyelt gyökér lesz — az ImportDropArea.qml hídja
    DropImportController = _lazy_app_symbol("DropImportController")
    drop_import_controller = DropImportController(
        add_folder=controller.addWatchedFolder
    )

    # Mappakezelő fa-nézete (#231): a helyi fájlrendszer LUSTA, háttérszálas
    # listázása — a FolderManagerDialog.qml hídja
    FolderTreeController = _lazy_app_symbol("FolderTreeController")
    folder_tree_controller = FolderTreeController()

    state.edit_preview = edit_preview
    state.edit_controller = edit_controller
    state.edit_controller_masodik = edit_controller_masodik
    state.second_preview = second_preview
    state.effect_thumb_provider = effect_thumb_provider
    state.fileops_controller = fileops_controller
    state._display_mode_bridge = _display_mode_bridge
    state._color_management_bridge = _color_management_bridge
    state.confirm_settings = confirm_settings
    state.camera_capture_controller = camera_capture_controller
    state.gombsav = gombsav
    state.discovery_controller = discovery_controller
    state.drop_import_controller = drop_import_controller
    state.folder_tree_controller = folder_tree_controller

def _startup_step_create_library_controllers(state):
    app = state.app
    controller = state.controller
    data_dir = state.data_dir
    progress_log = state.progress_log
    provider = state.provider
    roots = state.roots
    startup_status = state.startup_status

    # A bal hasáb fa-mappanézete (#702): az INDEXELT mappák hierarchiája,
    # részfa-összegzett darabszámmal — a FolderHierarchyView.qml hídja.
    # Nem téveszthető össze a fenti `folder_tree_controller`-rel: az a
    # Mappakezelő dialógus fájlrendszer-böngészője, ez az indexé.
    FolderHierarchyController = _lazy_app_symbol("FolderHierarchyController")
    folder_hierarchy_controller = FolderHierarchyController()
    #: #1407: az „Egyszerűsített fanézet" a FIGYELT mappák ágaira szűkíti a
    #: fát — a vezérlőnek tudnia kell, melyek azok.
    folder_hierarchy_controller.setWatchedRoots(list(roots))

    startup_maintenance = StartupMaintenance(progress_log, parent=app)
    startup_maintenance.statusChanged.connect(
        startup_status.report, Qt.ConnectionType.QueuedConnection
    )

    def _maintenance_step_finished(key: str, result, error_type: str) -> None:
        if error_type:
            logging.getLogger(__name__).warning(
                "az indulási karbantartás egyik lépése hibára futott (%s): %s",
                key,
                error_type,
            )
            return
        if key == "folder_hierarchy" and result is not None:
            folder_hierarchy_controller.setFolders(result)

    startup_maintenance.stepFinished.connect(
        _maintenance_step_finished, Qt.ConnectionType.QueuedConnection
    )

    def _mappafa_sorai() -> list[dict[str, object]] | None:
        """Az indexelt mappafa sorai, a Qt-modell módosítása nélkül."""
        try:
            with open_index(data_dir / "index.db") as conn:
                return [
                    {"path": path, "count": count}
                    for _name, path, count, *_rest in _lazy_app_symbol(
                        "sorted_folder_rows"
                    )(conn)
                ]
        except sqlite3.DatabaseError:
            logging.getLogger(__name__).exception(
                "a fa-mappanézet frissítése hibára futott"
            )
            return None

    def _reload_folder_hierarchy() -> None:
        """Az indexelt mappafa újratöltése soros háttérmunkaként."""
        startup_maintenance.enqueue(
            "folder-hierarchy-refresh",
            (
                StartupMaintenanceStep(
                    key="folder_hierarchy",
                    name="A mappafa frissítése",
                    status_text=None,
                    work=_mappafa_sorai,
                ),
            ),
        )

    startup_maintenance.set_refresh_handler(_reload_folder_hierarchy)
    controller.syncFinished.connect(
        startup_maintenance.request_refresh, Qt.ConnectionType.QueuedConnection
    )

    # Időrend nézet (#24, Ctrl+5): a teljes könyvtár év/hónap szerinti
    # csoportosítása — a MEGLÉVŐ (AppControllerrel közös) thumbnail-
    # providert kapja, hogy a bélyegkép-URL-ek nála is regisztrálva
    # legyenek. Háttér-szinkron után a nézet friss adatot mutasson, ha
    # épp nyitva van — a TimelineView.qml a megnyitáskor is újratölt.
    TimelineController = _lazy_app_symbol("TimelineController")
    timeline_controller = TimelineController(data_dir / "index.db", provider)
    controller.syncFinished.connect(timeline_controller.reload)
    # #440: a mentés-készletek hídja. A jelölteket a FIGYELT GYÖKEREK
    # alól szedi (a szűrést a készlet fájlszűrője végzi).
    BackupController = _lazy_app_symbol("BackupController")
    backup_controller = BackupController(data_dir / "index.db", tuple(roots))
    # Duplikátum-kezelő (#287): a picasapy.dedup mag fölötti UI-híd —
    # a DedupDialog.qml-nek adja a csoportokat, a thumbnail-providernél
    # regisztrálja az érintett fotókat
    DedupController = _lazy_app_symbol("DedupController")
    dedup_controller = DedupController(data_dir / "index.db", provider)
    # #1539: a feloldás után a forrás- ÉS a célmappa is célzott
    # újraolvasást kap — enélkül a „Duplikátumok" mappa képei eltűnnek
    wire_dedup(dedup_controller, controller)

    # #1066: a levelezés és a webexportálás vezérlője. Mindkettő a JELENLEG
    # látható fotókat kéri (`photo_source`), ahogy a saját docstringjük
    # előírja.
    #
    # ⚠️ Miért került ez külön jegybe: egyik sem jött létre SOHA, és egyik
    # sem volt regisztrálva — miközben az `OptionsTabEmail.qml` és a
    # `WebExportDialog.qml` hivatkozott rájuk, `typeof`-őr mögül. Az őr nem
    # engedte elszállni a felületet, viszont el is REJTETTE a hiányt: az
    # e-mail beállításfül elfogadta a módosítást, és némán nem mentette.
    def _lathato_fotok():
        return controller.photos.photos

    # #1671: a nyomtatás és az e-mail a KÉPTÁLCA tartalmán dolgozik, ha az
    # nem üres — a mappába exportálás (#455) mintájára. Enélkül kijelölés
    # nélkül némák maradtak, és a MÁS mappából tartott képet sosem látták.
    def _talca_fotok():
        return controller._tray_records()

    EmailController = _lazy_app_symbol("EmailController")
    email_controller = EmailController(
        photo_source=_lathato_fotok, tray_source=_talca_fotok
    )
    WebExportController = _lazy_app_symbol("WebExportController")
    web_export_controller = WebExportController(
        photo_source=_lathato_fotok
    )
    # #1472: a nyomtatás vezérlője — UGYANARRA a `photo_source`-ra épül
    # (a `printRows`/`renderPrintPreviewPdf` sorindexei a látható fotók
    # listájába mutatnak). Ez a vezérlő 213 sor kész kóddal és két
    # tesztfájllal SOHA nem jött létre a futó alkalmazásban, ezért a
    # Ctrl+P és a képtálca „Nyomtatás" gombja halott volt.
    print_controller = _create_print_controller(_lathato_fotok, _talca_fotok)

    # Import forrásból (#23): külső mappa (kártya/fényképezőgép) képeinek
    # másolása/áthelyezése a könyvtárba — a thumbnail-providerrel adja az
    # előnézetet, sikeres import után az addWatchedFolder úton a cél-mappa
    # a könyvtár része lesz
    ImportSourceController = _lazy_app_symbol("ImportSourceController")
    import_source_controller = ImportSourceController(
        provider,
        add_folder=controller.addWatchedFolder,
        index_path=data_dir / "index.db",
    )

    state.folder_hierarchy_controller = folder_hierarchy_controller
    state.startup_maintenance = startup_maintenance
    state._mappafa_sorai = _mappafa_sorai
    state._reload_folder_hierarchy = _reload_folder_hierarchy
    state.timeline_controller = timeline_controller
    state.backup_controller = backup_controller
    state.dedup_controller = dedup_controller
    state.email_controller = email_controller
    state.web_export_controller = web_export_controller
    state.print_controller = print_controller
    state.import_source_controller = import_source_controller
    state._lathato_fotok = _lathato_fotok
    state._talca_fotok = _talca_fotok

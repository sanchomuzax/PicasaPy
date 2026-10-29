import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy
import "selection.js" as Selection

// Főablak (#150 után): a nagy nézet-blokkok külön komponensekben élnek
// (LightboxFeed = könyvtár-feed, MainToolbar = felső sáv, TrayBar = alsó
// sáv, MainPeopleAlbumState = személyalbum-műveletek,
// FileOpsDialogs/ExportDialogs/AboutDialog = dialógusok, selection.js =
// kijelölés-logika) — itt csak az állapot és a bekötés marad.
ApplicationWindow {
    id: window
    // A kivont komponens mellett a főablak korábbi QML-neve megmarad.
    property alias shortcutSave: mainKeyboardShortcuts.shortcutSave
    property alias errorBanner: mainErrorBanner
    property alias errorBannerText: mainErrorBanner.messageText
    width: 1280
    height: 800
    // #641: az ablak nem mehet olyan kicsire, hogy a szerkesztő bal panelje
    // ne férjen el — különben a Visszavonás/Újra sor kicsúszik a látható
    // területről, és a felhasználó egyáltalán nem látja. A #628 a panel
    // `implicitHeight`-jét már kiszámolta, de a garanciát egy
    // `Layout.minimumHeight`-re bízta, amit semmi nem érvényesít az ablak
    // szintjén — ez az a hely, ahol érvényesíteni kell.
    minimumHeight: photoViewer.requiredHeight
                   + (window.menuBar ? window.menuBar.height : 0)
    // #1367: az ablak nem mehet olyan keskenyre, hogy az alsó
    // műveletsáv kilógjon — a #1345 fix gombcellái óta a sáv nem
    // zsugorodik tovább. Az igény MÉRT (ld. `TrayBar.requiredWidth`),
    // és őr-teszt méri újra élőben.
    minimumWidth: trayBar.requiredWidth
    visible: true
    //: #671: az ablak „X"-e UGYANAZT az utat járja, mint a Fájl ▸ Kilépés.
    //: Ha háttérmunka fut, a bezárást visszavonjuk, és a kérdés dönt;
    //: egyébként a Qt zárja az ablakot, ahogy eddig.
    onClosing: function (close) {
        if (!window.aaKapu(window.kilepes)) {   // #3644
            close.accepted = false
            return
        }
        if (controller && controller.backgroundWorkRunning()) {
            close.accepted = false
            kilepesDialog.askExit()
        }
    }
    title: "PicasaPy"
    color: Theme.lightboxBg

    // #28: a téma a Theme-tokenekből jön, azok pedig a controller
    // kapcsolójából — az OS saját sötét módja sehol nem üthet át, a
    // váltás kizárólag a Nézet → Sötét téma menüponté (alapértelmezés:
    // világos; ld. design-guide).
    Binding {
        target: Theme
        property: "dark"
        value: controller ? controller.darkTheme : false
    }

    // #3070: a Nézet ▸ Megjelenítési mód a FELÜLET színeire is hat, nem csak
    // a fotóra. A vezérlő EGY menetben átalakítja a `Theme.nyers` tokenjeit
    // (`apply_display_mode` — ugyanaz a MÉRT szabály, ami a képen fut), és az
    // eredményt a szingleton palettájába tesszük; onnantól minden kötés
    // magától követi (a 11.7/2. szerződés „mindent újrafest" pontja nálunk a
    // szingleton jelzése). Üres paletta = a mód nem mozdít képpontot, tehát a
    // nyers értékek mennek ki változatlanul.
    //
    // A diavetítés SZÁNDÉKOSAN kimarad (11.7/3., NY-4): az a saját útján kapja
    // meg a módot (#1640), a téma színeit pedig nem használja.
    function frissitsdAMegjelenitesiPalettat() {
        Theme.megjelenitesiPaletta = controller
            ? controller.uiPalette(Theme.nyers) : ({})
    }

    Connections {
        target: controller
        function onDisplayModeChanged() { window.frissitsdAMegjelenitesiPalettat() }
        //: a sötét/világos váltás a NYERS értékeket cseréli ki, tehát a
        //: paletta is újraszámolandó — különben az előző téma átalakított
        //: színei ragadnának be
        function onDarkThemeChanged() { window.frissitsdAMegjelenitesiPalettat() }
    }

    palette {
        window: Theme.canvasBg
        active.windowText: Theme.ink
        inactive.windowText: Theme.ink
        base: Theme.controlBase
        alternateBase: Theme.panelBg
        active.text: Theme.ink
        inactive.text: Theme.ink
        button: Theme.buttonBg
        active.buttonText: Theme.ink
        inactive.buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: Theme.panelSelectionText
        placeholderText: Theme.placeholderText
        mid: Theme.chromeBorder
        light: Theme.shadeLight
        dark: Theme.shadeDark
        // #5874: az aktív/inaktív tinták ne írják felül a Qt Controls
        // disabled csoportját; a Theme token mindkét témában olvasható.
        disabled.windowText: Theme.textGray
        disabled.text: Theme.textGray
        disabled.buttonText: Theme.textGray
    }

    // #985: a globális `controller` egy KONTEXTUS-property, a `CollagePanel`
    // viszont saját `controller` property-t deklarál (hogy a komponens-
    // tesztekben becserélhető legyen). A `controller: controller` sor ezért
    // önmagára kötne (kötési hurok) — ez az álnév oldja fel, egy helyen.
    readonly property var appController: controller
    property alias peoplePanel: jobbFiok.peoplePanel

    property string pendingPeopleManagerPersonName: ""
    property int thumbSize: 144
    //: #598: a cellaméret átadása a bélyegkép-tárnak — a SZINTET (72 · 144 ·
    //: a maximum) a tár választja ki belőle. A csúszka húzása nem kér újra
    //: mindent: egy szint több fokozatot fed le.
    onThumbSizeChanged: if (controller) controller.setThumbCellSize(thumbSize)
    property int selectedIndex: -1        // horgony (utoljára kattintott)
    property var selectedIndexes: []      // a teljes kijelölés
    // #5396: átnevezéskor a fájl útvonal alapján új fotóazonosítót kaphat
    // az indexfrissítésben; a következő modell-reset visszateszi a kijelölést.
    property string _pendingRenamePhotoId: ""
    property string _pendingRenameTargetPath: ""
    // #142: a kijelölés set-alakban (sor → true) — a rács-cellák O(1)
    // lookupja; az indexOf-os kötés O(cellák × kijelöltek) volt, ami
    // Ctrl+A-nál minden cellán végigjárta a teljes kijelölés-listát
    property var selectedSet: ({})
    onSelectedIndexesChanged: {
        var s = {}
        for (var k = 0; k < selectedIndexes.length; ++k)
            s[selectedIndexes[k]] = true
        selectedSet = s
    }
    readonly property bool quickViewerLaunch:
        controller ? controller.quickViewActive === true : false
    property bool viewerOpen: quickViewerLaunch
    // #4656: a néző saját megjelenítési módot kap, bezáráskor visszaáll az
    // előző ablakállapot. A valódi megnyitás külön belépőn fut át, így a
    // közvetlen állapotbeállítások (például a QML-próbapadban) nem váltanak módot.
    property int visibilityBeforeViewer: Window.Windowed
    property bool viewerVisibilityManaged: false
    onViewerOpenChanged: {
        // A gyorsnézet a könyvtár beolvasása előtt indul. Bezáráskor
        // takarítsuk el az ideiglenes listát, és csak ekkor kérjük a rendes
        // könyvtár betöltését.
        if (!window.viewerOpen && window.quickViewerLaunch) {
            controller.returnToLibraryFromQuickView()
            Qt.callLater(function() {
                initialScanDialog.openIfNeeded()
                collageDraftDialog.openIfNeeded()
                if (typeof discoveryController !== "undefined"
                        && discoveryController)
                    discoveryController.discoverAtStartup()
            })
        }
        if (!window.viewerOpen && window.viewerVisibilityManaged) {
            window.visibility = window.visibilityBeforeViewer
            window.viewerVisibilityManaged = false
        }
    }
    property bool timelineOpen: false     // Időrend nézet (#24, Ctrl+5)
    property bool timelineSlideshowActive: false
    property var timelineSlideshowModel: null
    //: #1808: rács-nagyító be/ki. A rácsban a nagyító-réteg
    //: ELNYELI az egéreseményeket, tehát bekapcsolva a húzás nem
    //: jelöl ki — ez szándékos, ld. LightboxFeed.qml.
    //:
    //: ⚠️ #1911: ma SENKI nem billenti igazra — az eszköztári
    //: kapcsológomb kikerült, mert élesben felfedezhetetlen volt. A
    //: tulajdonság és a rács oldali réteg SZÁNDÉKOSAN marad: mérve van
    //: és működik, csak felfedezhető felület kell hozzá (külön jegy).
    //: Ne töröld „halott kódként" — a hiányzó darab a KAPCSOLÓ.
    property bool loupeActive: false
    // #1773: a jobb fiók négy lapja KIZÁRÓ csoport — egyszerre pontosan
    // egy látszik, vagy a fiók üres. Ezért EGYETLEN állapot írja le mind a
    // négyet; négy független billenőből a mérés szerint nem előfordulható
    // állapotok álltak elő (négy panel egyszerre nyitva).
    //
    // MÉRVE (`0x005d9760`, mind a négy ág): a vezérlő elrejti a másik
    // hármat, kikapcsolja a másik három fejléc-gombot, bekapcsolja a
    // sajátját, majd megjeleníti a saját panelt.
    //
    // Az érvényes értékek: "" (a fiók üres) · "tags" · "places" ·
    // "properties" · "people".
    property string activeDrawerTab: ""

    // A négy régi jelző SZÁRMAZTATOTT — a kötések és a menüpipák
    // változatlanul rájuk hivatkoznak, de már nem írhatók külön-külön.
    readonly property bool tagsPanelOpen:
        window.activeDrawerTab === "tags"        // Címkék-panel (#12, Ctrl+T)
    readonly property bool placesPanelOpen:
        window.activeDrawerTab === "places"      // Helyek-panel (#30, térkép)
    // Tulajdonságok-panel (#13, Alt+Enter)
    readonly property bool propertiesPanelOpen:
        window.activeDrawerTab === "properties"
    // Emberek-panel (#26) — a jobb fiók negyedik panelje
    // (`rightdrawerpanel/peoplepanel`), a Címkék/Helyek/Tulajdonságok mellett
    readonly property bool peoplePanelOpen:
        window.activeDrawerTab === "people"

    // #1773: a lapváltás EGYETLEN útja. Az aktív lapra kattintás
    // SZÁNDÉKOSAN nem zár be: a bináris a vizsgált ágon feltétel nélkül
    // 1-re állítja a saját gombját (a jegy „nyitott" pontja, ez az
    // alapértelmezés). A fiók ürítése az `ureseidAFiokot()`.
    function valtsFiokLapot(nev) {
        window.activeDrawerTab = nev
        if (nev !== "") window.utolsoFiokLap = nev
    }
    function ureseidAFiokot() {
        window.activeDrawerTab = ""
    }

    //: #2163: a `Ctrl+0` (`thumbui/toggle_right_drawer`, `0x005e6206`) a
    //: jobb fiókot BILLENTI. Bezárás után újranyitva ugyanaz a lap jöjjön
    //: vissza — enélkül a billentés fele-útja adatvesztésnek látszik: a
    //: felhasználó a Címkéket zárta be, és az Emberek nyílna ki.
    property string utolsoFiokLap: "tags"

    //: #2163: a `Ctrl+F` a fejléc keresőmezőjére viszi a fókuszt. A
    //: `header` a nézőben nincs jelen (ld. a `MainToolbar` bekötését),
    //: ezért a null-őr nem formaság.
    function fokuszAKeresore() {
        if (toolbar && toolbar.fokuszAKeresore) toolbar.fokuszAKeresore()
    }

    //: #2163: a `Ctrl+3` (Szerkesztési nézet, `0x005e624f` →
    //: `thumbui/fullview`) UGYANAZT teszi, mint a „Megjelenítés és
    //: szerkesztés" parancs: a kijelölt képet a nézőben nyitja meg, ahol a
    //: szerkesztő panel is ül. Egy belépő, több hívó — a tálca helyi
    //: menüje (#1917) is ezt hívja.
    // #4656: minden tényleges nézőnyitás ezt használja. A teljes képernyő
    // vagy ablakos mód a mentett jelölőt követi; bezáráskor a korábbi
    // ablakállapot áll vissza.
    function openPhotoViewer(row) {
        if (!window.viewerOpen) {
            window.visibilityBeforeViewer = window.visibility
            var fullscreenStartup = controller
                && controller.viewerFullscreenStartup !== undefined
                ? controller.viewerFullscreenStartup : true
            window.visibility = fullscreenStartup
                ? Window.FullScreen : Window.Windowed
            window.viewerVisibilityManaged = true
            window.viewerOpen = true
        }
        photoViewer.show(row)
    }

    // A közvetlen fájlargumentumos indulás ugyanazt a viewer-ablakmódot
    // használja, mint a Photo Viewer beállítása. Külön függvényben van, hogy
    // a rendes Component.onCompleted út és a QML-funkcióteszt is ezt hívja.
    function startQuickViewer() {
        if (!window.quickViewerLaunch) return
        window.visibilityBeforeViewer = window.visibility
        var fullscreenStartup = controller
            && controller.viewerFullscreenStartup !== undefined
            ? controller.viewerFullscreenStartup : true
        window.visibility = fullscreenStartup
            ? Window.FullScreen : Window.Windowed
        window.viewerVisibilityManaged = true
        window.viewerOpen = true
        photoViewer.show(0)
    }

    function nezdEsSzerkeszd() {
        if (window.viewerOpen) return
        var sorok = window.selectedRows()
        if (sorok.length === 0) return
        window.openPhotoViewer(sorok[0])
    }

    // #4329: az önálló Kép ▸ Unhide parancs kizárólag a rejtett kijelölt
    // képeket teszi láthatóvá. A toggleHiddenRows csak a rejtett sorokat
    // kapja meg, ezért a vegyes kijelölés látható képei nem rejtődnek el.
    // #4626: a Kép ▸ Hide mindig rejtve hagyja a kijelölést. A már rejtett
    // sorokat kihagyjuk, így a váltó művelet csak látható képeket rejt el.
    // A helyi menük külön megőrzik a Hide/Unhide váltó viselkedést.
    function hideSelection() {
        if (!controller) return
        var rows = window.photoActionRows()
        if (rows.length === 0) return
        var visibleRows = []
        for (var i = 0; i < rows.length; ++i) {
            var row = Number(rows[i])
            var photo = controller.photos.itemAt(row)
            if (photo && photo.hidden !== true) visibleRows.push(row)
        }
        if (visibleRows.length > 0) controller.toggleHiddenRows(visibleRows)
        if (!window.viewerOpen) window.clearSelection()
    }

    function unhideHiddenSelection() {
        if (!controller) return
        var rows = window.photoActionRows()
        var hiddenRows = []
        for (var i = 0; i < rows.length; ++i) {
            var row = Number(rows[i])
            var photo = controller.photos.itemAt(row)
            if (photo && photo.hidden === true) hiddenRows.push(row)
        }
        if (hiddenRows.length === 0) return
        controller.toggleHiddenRows(hiddenRows)
        if (!window.viewerOpen) window.clearSelection()
    }

    //: #2163: a `Ctrl+F7` az eredetiben a `searchoptions/loadsim`-et
    //: kattintja — a MINTA a jelenlegi kép, és a keresés a hozzá
    //: hasonlókat adja (a mag a #1833-ban kész).
    //: #2163: a `Ctrl+F6` a másodpéldány-módot kapcsolja (#1398). A
    //: null-őr FÜGGVÉNYBEN áll, nem a `Shortcut` törzsében: a #1616 őre
    //: egyetlen zárójel-szintet lát, az ágazó törzs láthatatlan neki.
    function masodpeldanyokMutatasa() {
        if (controller) controller.showDuplicateFiles()
    }

    //: #2163: a `clearsim` párja — ugyanezért függvény.
    function torolAHasonlosagMintat() {
        if (controller) controller.clearSimilarity()
    }

    function keressHasonlot() {
        if (!controller) return
        var sorok = window.selectedRows()
        if (sorok.length === 0) return
        controller.showSimilarTo(sorok[0])
    }

    //: #2163: a `Ctrl+Shift+B` és a `Ctrl+Shift+E` az eredetiben egyetlen
    //: szűrő-alkalmazóba megy (`0x005fe370(panel, "bw"|"enhance")`), ami a
    //: KIJELÖLÉSRE hat — nálunk ez a köteg-szerkesztés útja
    //: (`applyEffectMany`), ugyanaz, amit az Kép ▸ Köteg-szerkesztés
    //: menütételei hívnak. Nincs második ág.
    function kotegEffekt(nev) {
        if (!controller) return
        var sorok = window.selectedRows()
        if (sorok.length === 0) return
        controller.applyEffectMany(sorok, nev)
    }

    function billentsdAFiokot() {
        if (window.activeDrawerTab !== "") {
            window.utolsoFiokLap = window.activeDrawerTab
            window.ureseidAFiokot()
        } else {
            window.valtsFiokLapot(window.utolsoFiokLap)
        }
    }
    // #26 (3. lépcső): a „Névtelenek" nézet — a fő rács helyén jelenik
    // meg, amíg be van kapcsolva (ld. UnnamedFacesView.qml)
    property bool unnamedFacesOpen: false
    // #26: melyik arc-album van nyitva — „unnamed" vagy „ignored"
    // (`CAlbumLabel::Ignored` = „Mellőzött emberek")
    property string facesAlbumMode: "unnamed"
    // A névadás után a fotókijelölés nem változik, ezért külön frissítőjel
    // kell az Emberek-panel sorlistáinak újraolvasásához.
    property int peopleFaceRevision: 0
    // #4586: csak az `unnamedFacesHere` frissítéséhez (keresés közben)
    property int unnamedFaceRevision: 0
    Timer {
        id: unnamedFaceRefreshTimer
        interval: 500
        onTriggered: window.unnamedFaceRevision++
    }
    // nyitáskor az arc-lista friss: a nyitott-panel kapu miatt a zárt panel
    // alatt érkezett `facesStored` jelek kimaradtak
    onPeoplePanelOpenChanged: if (window.peoplePanelOpen) unnamedFaceRevision++
    Connections {
        target: photoViewer
        function onPeopleOpenChanged() {
            if (photoViewer.peopleOpen) window.unnamedFaceRevision++
        }
    }
    // a kijelölt képek közül a futó keresés által még nem ellenőrzöttek
    // száma — csak nyitott panelnél és nem a Név nélküliek albumban számolunk
    readonly property int _selectionPending:
        (window.peoplePanelOpen && !window.unnamedFacesOpen)
            ? window.selectionPendingCount() : 0

    // #4586: a kijelölt képek közül hányat nem vizsgált még át a futó
    // háttér-arckeresés (`PeoplePanel` betöltés / ellenőrizetlen fájlok)
    function selectionPendingCount() {
        var scan = window._faceScanController
        if (!scan || !controller)
            return 0
        // a függés az `uncheckedFiles`-en: a keresés haladására újraszámol
        var remaining = scan.uncheckedFiles
        if (remaining <= 0)
            return 0
        return scan.pendingAmong(window.selectedPaths())
    }
    // #1236: külön ablak-szintű név kell. Az UnnamedFacesView azonos nevű
    // property-jének jobb oldalán a `faceScanController` önmagára oldódna.
    readonly property var _faceScanController:
        typeof faceScanController !== "undefined" ? faceScanController : null
    // a jobbklikkelt kép sora (#15) — a kontextusmenü egyedi műveleteinek
    // (átnevezés, fájlkezelő) célpontja
    property int fileOpTargetRow: -1

    // -- Dokumentum-lapok (#985; a sáv maga a #944) -------------------------
    //
    // Az eredetiben a kollázs NEM párbeszédablak, hanem SAJÁT LAP a fülsávban
    // (`panelroot/collagetab`), a „Könyvtár" lapja mellett — ld.
    // `docs/specs/kollazs-panel-ui-spec.md` 3.1. Ma egyetlen projekt-laptípus
    // van, a kollázs; a lista mégis lista, mert a sáv szerződése az.
    readonly property string collageTabId: "collage"
    readonly property string movieMakerTabId: "movieMaker"
    property bool movieMakerTabOpen: false
    readonly property real documentTabsBottom:
        documentTabStrip.y + documentTabStrip.height
    readonly property string activeDocumentTabId:
        documentTabStrip.activeTabId
    readonly property bool movieMakerActive:
        window.movieMakerTabOpen
        && documentTabStrip.activeTabId === window.movieMakerTabId
    property bool backToMovieMakerPrompted: false
    readonly property var openProjectTabs: {
        var tabs = []
        if (controller && controller.collageOpen) {
            tabs.push({
                id: window.collageTabId,
                title: qsTr("Collage"),
                modified: controller.collageDirty === true
            })
        }
        if (window.movieMakerTabOpen) {
            tabs.push({
                id: window.movieMakerTabId,
                title: qsTr("Movie Maker"),
                modified: false
            })
        }
        return tabs
    }

    // #1026: a KÖNYVTÁR PANELJE — EGYETLEN kapcsoló, nem sávonkénti elrejtés.
    //
    // Az eredetiben a `panelroot/collagepanel` a `panelroot/mainuipanel`
    // TESTVÉRE, nem melléje kerül: a felső éle a fülsáv alatt van
    // (`YConstraint 0, 0, tabdiv`), az alsó az ablak alján
    // (`YConstraint 1, 1, 0`). A könyvtár teljes kerete viszont a
    // `mainuipanel` GYEREKE (`thumbui.tre`: `importbutton`, `sbutton`,
    // `timelinebutton`, `globalmode`, `bottombevel_base`, és a kimeneti sáv
    // az `outputlayout.tre`-ből). Vagyis a projekt-lapon nem két sáv
    // „rejtőzik el", hanem a könyvtár panelja tűnik el EGÉSZBEN — és a
    // vászon ezért kapja meg a fülsáv alatti TELJES területet, az ablak
    // aljáig (a felhasználó két képernyőképe ezt a különbséget mutatta).
    //
    // Ezért egy kapcsoló és nem három külön kötés: aki új darabot tesz a
    // könyvtár keretébe, erre köti — így nem maradhat ott egy elfelejtett
    // sáv. A menüsor és a fülsáv MINDKÉT panelen kívül van (`panelroot`),
    // azokat ez nem érinti.
    //
    // A néző/szerkesztő NEM projekt-lap: az a mai módon fedi le a
    // könyvtárat a saját kötéseivel, azon ez a kapcsoló nem változtat.
    readonly property bool libraryFrameVisible:
        (documentTabStrip.libraryActive || window.viewerOpen)
        && !window.slideshowRunning

    //: #2987: MÉRVE — a vetítés eddig az `ApplicationWindow` contentItem-jét
    //: töltötte ki, vagyis a fejléc ÉS a lábléc KÖZÖTTI sávot, a menüsáv
    //: nélkül: 800 képpontos ablakban 626 px jutott neki, és mind a három
    //: sáv látszott. Az ablak teljes képernyőre váltott (a kérés kiment),
    //: a vetítés mégis dobozban maradt — a jegy 3. esete, platformfüggetlenül.
    //: Az eredetiben a vetítés alatt SEMMI MÁS nem látszik (#1903).
    readonly property bool slideshowRunning: slideshow.visible

    // A „Vissza a kollázshoz" gomb csak a „Továbbiak..." után jelenik meg
    // (spec 4.3/13.): az eredeti is AKKOR rakja a könyvtár lapjára.
    property bool backToCollagePrompted: false

    // A kollázs forrása a mai `_sources_for` szabályt követi (#455): ha a
    // képtálcán van kép, AZ a forrás, egyébként a rács kijelölése.
    //
    // ⚠️ A tálca mappákon átnyúlik, a `openCollage` viszont RÁCS-SOROKAT vár
    // (#943 API). A jelenlegi mappán kívüli tálcaképeket ezért nem tudjuk
    // átadni — olyankor a kijelölésre esünk vissza. Az útvonal-alapú
    // megnyitás külön jegy; itt szándékosan nem építünk mellé második
    // forrás-szabályt.
    function collageSourceRows() {
        if (!controller) return []
        var held = controller.heldPaths || []
        var rows = []
        for (var i = 0; i < held.length; ++i) {
            var row = controller.photos.rowOfPath(String(held[i]))
            if (row >= 0) rows.push(row)
        }
        if (rows.length > 0) return rows
        return window.selectedRows()
    }

    /** A Kollázs LAP megnyitása — a Létrehozás menü és a tálca gombja is ide
        fut be (spec 3.2). Ha már nyitva van, csak visszaváltunk rá: a
        felhasználó munkáját újranyitással eldobni némán adatvesztés volna. */
    /** #1006: kollázs a MEGADOTT sorokból — a fejléc-gomb belépője.

        A `openCollageTab()` a tálcát vagy a kijelölést veszi
        (`collageSourceRows`); a fejléc viszont a SAJÁT csoportjához
        tartozik, tehát a sorokat ő adja meg. A többi lépés — a néző
        elhagyása, a lap aktiválása — ugyanaz, ezért egy helyen él. */
    function openCollageFromRows(rows) {
        if (!controller) return
        if (!window.aaKapu(function () { window.openCollageFromRows(rows) })) return
        window.backToCollagePrompted = false
        window.viewerOpen = false
        if (!controller.collageOpen)
            controller.openCollage(rows)
        documentTabStrip.activateTab(window.collageTabId)
    }

    //: #4539: a mappa-fejléc film-gombja — a csoport sorait a meglévő
    //: Filmkészítőbe adja (a kijelölés nem számít, mint a kollázsnál).
    function openMovieFromRows(rows) {
        if (!controller || rows.length === 0) return
        createDialogs.ensure().openMovieForRows(rows)
    }

    // A filmkészítő a kollázshoz hasonlóan saját dokumentumlap. A tartalom
    // a CreateDialogs.qml-ben marad, de a navigációt a főablak kezeli.
    function openMovieMakerTab() {
        window.viewerOpen = false
        window.backToMovieMakerPrompted = false
        window.movieMakerTabOpen = true
        documentTabStrip.activateTab(window.movieMakerTabId)
    }

    function openMovieClipCollector() {
        if (!window.movieMakerTabOpen) return
        window.backToMovieMakerPrompted = true
        documentTabStrip.activateTab(documentTabStrip.libraryTabId)
    }

    function returnToMovieMaker() {
        window.backToMovieMakerPrompted = false
        if (window.movieMakerTabOpen)
            documentTabStrip.activateTab(window.movieMakerTabId)
    }

    function closeMovieMakerTab() {
        window.movieMakerTabOpen = false
        if (documentTabStrip.activeTabId === window.movieMakerTabId)
            documentTabStrip.activateTab(documentTabStrip.libraryTabId)
    }

    function openCollageTab() {
        if (!controller) return
        if (!window.aaKapu(window.openCollageTab)) return
        window.backToCollagePrompted = false
        // #1055: a NÉZŐT (és vele a szerkesztőt) el kell hagyni. A kollázs
        // panelje `!viewerOpen`-re látszik, a képtálca kollázs-gombja
        // viszont a nézőben IS ott van (`libraryFrameVisible`) — enélkül a
        // lap megnyílik, a kollázs elkészül, és a felhasználó közben a
        // mappanézetet látja. Pontosan ezt jelentette a v0.8.7-en.
        window.viewerOpen = false
        if (!controller.collageOpen)
            controller.openCollage(window.collageSourceRows())
        documentTabStrip.activateTab(window.collageTabId)
    }

    /** Egy KÉSZ kollázs újranyitása szerkesztésre (#1002).

        A tulajdonos jelentése a v0.8.17-ről: *„Jelenleg ennek hiányában nem
        szerkeszthető a kollázs."* — a kész képtől nem vezetett vissza út a
        panelra.

        A nézőt elhagyjuk (#1055): a kollázs panelje `!viewerOpen`-re
        látszik, tehát enélkül a lap megnyílna, és a felhasználó közben a
        képet nézné. */
    /** #2114: a FILM újranyitása a projektfájljából.

        Az eredeti „Mozgófilm szerkesztése" gombja a forrásprojektet nyitja
        meg; nálunk a filmkészítő párbeszéd a szerkesztő felülete, ezért a
        projekt képeit KIJELÖLJÜK, és a párbeszéd a projekt diaidejével jön
        fel. A forrásképek tipikusan nem a jelenlegi nézetben állnak — a
        `locateSavedCollage` mintájára előbb a mappájukra állunk. */
    function openSavedMovie(path) {
        if (!controller) return
        if (!window.aaKapu(function () { window.openSavedMovie(path) })) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var projekt = controller.movieProject(cel)
        if (!projekt || !projekt.sources || projekt.sources.length === 0) return
        var elso = String(projekt.sources[0])
        if (controller.photos.rowOfPath(elso) < 0) {
            var mappa = window.folderOfPath(elso)
            if (mappa.length > 0) controller.selectFolder(mappa)
        }
        var sorok = []
        for (var i = 0; i < projekt.sources.length; ++i) {
            var sor = controller.photos.rowOfPath(String(projekt.sources[i]))
            if (sor >= 0) sorok.push(sor)
        }
        //: ha egyetlen forráskép sincs meg (törölt/áthelyezett mappa), a
        //: párbeszéd megnyitása félrevezető volna — a gomb inkább ne
        //: csináljon semmit, mint hogy MÁS képekből ajánljon filmet (#936)
        if (sorok.length === 0) return
        window.viewerOpen = false
        documentTabStrip.activateTab(documentTabStrip.libraryTabId)
        window.selectedIndex = sorok[0]
        window.selectedIndexes = sorok
        createDialogs.ensure().openMovieProject(
            projekt.seconds, projekt.burstmodethresh, cel)
    }

    function openSavedCollage(path) {
        if (!controller) return
        if (!window.aaKapu(function () { window.openSavedCollage(path) })) return
        var cel = String(path || "")
        if (cel.length === 0) return
        controller.openCollageProject(cel)
        if (!controller.collageOpen) return
        window.viewerOpen = false
        window.backToCollagePrompted = false
        documentTabStrip.activateTab(window.collageTabId)
    }

    /** A KÉSZ kollázs megkeresése a könyvtárban (#1028).

        Az eredeti mentő négy záró lépése közül ez a negyedik: `locate` az
        új fájlra. A lap bezárása (harmadik lépés) már megvan — az a
        `CollagePanel.finishSave` dolga; ide a NAVIGÁCIÓ tartozik.

        ⚠️ Nézőt szándékosan NEM nyit: az eredeti is csak kijelöl, a
        nagyban megnyitás a felhasználó kattintása az értesítésen. */
    function locateSavedCollage(path) {
        if (!controller) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var sor = controller.photos.rowOfPath(cel)
        if (sor < 0) {
            // A Kollázsok mappa tipikusan NEM a jelenlegi nézet: előbb oda
            // állunk, aztán kérdezünk újra. (Az indexbe a mentés veszi fel,
            // #1048 — enélkül a mappa üres volna.)
            var mappa = window.folderOfPath(cel)
            if (mappa.length > 0) {
                controller.selectFolder(mappa)
                sor = controller.photos.rowOfPath(cel)
            }
        }
        documentTabStrip.activateTab(documentTabStrip.libraryTabId)
        if (sor >= 0) {
            window.selectedIndex = sor
            window.selectedIndexes = [sor]
        }
        // #1119: a RENDES létrehozás után NINCS értesítés. A
        // `collage::done` értesítő a binárisban az „Asztali háttérkép"
        // ágához tartozik (a `0x0057aa10` a `Control Panel\\Desktop\\`
        // registrykulcsot és a `picasabackground.bmp`-t mozgatja), nem a
        // rendes kollázs-készítéshez. A tulajdonos háromszor jelezte, hogy
        // ilyen gomb a Picasa 3-ban nincs.
        //
        // ⚠️ A `CollageDoneNotice` komponens SZÁNDÉKOSAN marad: az
        // „Asztali háttérkép" ágé, aminek a bekötése külön jegy (ma a
        // `collageDesktopBackgroundReady` jelzésnek nincs fogadója).
        // A törlése visszafejlesztés volna.
    }

    /** Egy fájl útvonalának a mappája. A QML-ben nincs `Path`, a
        csomópont-útvonal pedig a PLATFORM elválasztóját hozza (a kollázs
        `Path`-ból építi, tehát Windowson fordított perjellel). */
    function folderOfPath(path) {
        var szoveg = String(path)
        var vago = Math.max(szoveg.lastIndexOf("/"), szoveg.lastIndexOf("\\"))
        return vago > 0 ? szoveg.substring(0, vago) : ""
    }

    /** #1001: a kollázs „Megjelenítés és szerkesztés" parancsa — a képet a
        SZERKESZTŐBEN nyitja meg.

        A vezérlő csak az ÚTVONALAT ismeri (`collageEditRequested`), a
        szerkesztő — nálunk a néző bal panelje — viszont SORINDEXET vár; a
        fordítás itt történik. A jelzésnek eddig egyetlen fogadója sem volt,
        ezért mindhárom belépési pont (gomb, duplakattintás, helyi menü)
        hatástalan maradt.

        Az eredetiben a `view_and_edit` a képet a KÖNYVTÁRBAN nyitja meg
        (`picasa-kollazs-felulet.md` 5.), a kollázs lapja pedig NYITVA marad
        — ezért váltunk a Könyvtár lapjára, és ott nyílik a szerkesztő. A
        visszautat a már meglévő „Vissza a kollázshoz" gomb adja (a
        „Továbbiak..." mintája, `kollazs-panel-ui-spec.md` 4.3/13.): a
        szerkesztő bezárása után ott áll a könyvtár lapján. */
    function openCollageNodeInEditor(path) {
        if (!controller) return
        var cel = String(path || "")
        if (cel.length === 0) return
        var sor = controller.photos.rowOfPath(cel)
        if (sor < 0) {
            // A kollázs képei mappákon átnyúlhatnak (a „+" gomb más mappából
            // is vehet fel klipet), a feed pedig szűrve/keresve szűkebb
            // lehet: előbb a kép mappájára állunk, aztán újra kérdezünk.
            var mappa = window.folderOfPath(cel)
            if (mappa.length > 0) {
                controller.selectFolder(mappa)
                sor = controller.photos.rowOfPath(cel)
            }
        }
        // Néma bukás helyett sem tehetünk mást: a kép nincs az indexben (pl.
        // időközben törölték). A kollázs lapja érintetlen marad.
        if (sor < 0) return

        window.backToCollagePrompted = true
        documentTabStrip.activateTab(documentTabStrip.libraryTabId)
        window.selectedIndex = sor
        window.selectedIndexes = [sor]
        window.openPhotoViewer(sor)
    }

    // a kijelölt sorok listája (#12) — több-kijelölés, vagy ha az nincs,
    // az utoljára kattintott kép
    function selectedRows() {
        return Selection.effectiveRows(
            window.selectedIndexes, window.selectedIndex)
    }

    // #5883: a mentés csak akkor írja lemezre a kijelölést, ha valamelyik
    // kép filters lánca eltér a lemezre mentett állapottól. A modell
    // `hasEdits` mezője ezt a `.picasa.ini`-ben tárolt láncból adja; a
    // `photos.revision` a QML-kötést a láncváltás után újraértékelteti.
    function vanMentetlenSzerkesztes(sorok) {
        if (!controller || !controller.photos || !sorok) return false
        for (var i = 0; i < sorok.length; ++i) {
            var foto = controller.photos.itemAt(Number(sorok[i]))
            if (foto && foto.hasEdits === true) return true
        }
        return false
    }

    readonly property bool kijelolesbenVanMentetlenSzerkesztes:
        controller
        ? (controller.photos.revision,
           window.vanMentetlenSzerkesztes(window.selectedRows())) : false
    readonly property bool muveletiCelbanVanMentetlenSzerkesztes:
        controller
        ? (controller.photos.revision,
           window.vanMentetlenSzerkesztes(window.photoActionRows())) : false

    // A fotóhoz kötött menük célpontja nézőben a szerkesztett oldal, a
    // könyvtárban pedig a kijelölés. A kijelölés megmarad a néző mögött,
    // ezért ott nem használható a menü célpontjának.
    function photoActionRows() {
        if (window.viewerOpen) {
            var sor = Number(photoViewer._kijeloltSort())
            return sor >= 0 ? [sor] : []
        }
        return window.selectedRows()
    }

    function prepareRenameSelection(row, newName) {
        if (!controller || !newName) return
        var oldPath = controller.photos.filePathAt(Number(row))
        var separator = oldPath.lastIndexOf("/")
        if (separator < 0) return
        _pendingRenamePhotoId = controller.photos.idAt(Number(row))
        _pendingRenameTargetPath = oldPath.substring(0, separator + 1) + newName
    }

    function photoActionIndex() {
        if (window.viewerOpen) return Number(photoViewer._kijeloltSort())
        if (window.selectedIndex >= 0) return window.selectedIndex
        var sorok = window.selectedRows()
        return sorok.length > 0 ? Number(sorok[0]) : -1
    }

    function photoActionPaths() {
        var rows = window.photoActionRows()
        var paths = []
        if (!controller) return paths
        for (var k = 0; k < rows.length; ++k) {
            var path = controller.photos.filePathAt(Number(rows[k]))
            if (path.length > 0) paths.push(path)
        }
        return paths
    }

    // #5835: mappa nélküli nézetben a kijelölt vagy fókuszban levő kép
    // mappája az üres album tárolási helye. Sima mappanézetben a #5812
    // szerinti aktuális mappa marad az elsődleges cél.
    function newAlbumFolderPath() {
        if (!controller) return ""
        if (controller.viewModeName === "folder" && controller.currentFolder)
            return controller.currentFolder

        var photoPath = ""
        var paths = window.photoActionPaths()
        if (paths.length > 0) {
            photoPath = paths[0]
        } else {
            var row = window.photoActionIndex()
            if (row >= 0 && controller.photos)
                photoPath = controller.photos.filePathAt(row)
        }
        var separator = Math.max(
            photoPath.lastIndexOf("/"), photoPath.lastIndexOf("\\")
        )
        return separator > 0 ? photoPath.substring(0, separator) : ""
    }

    function addPhotosToScreensaver(paths) {
        var added = controller ? controller.addScreensaverPhotos(paths) : 0
        errorBanner.notice = true
        errorBannerText.text = qsTr("Added %1 pictures to Screensaver.")
                .arg(added)
    }

    function requestAddToScreensaver() {
        var paths = window.photoActionPaths()
        if (controller && controller.currentAlbumToken !== "") {
            screensaverAlbumConfirmLoader.ensure().openFor(paths)
            return
        }
        window.addPhotosToScreensaver(paths)
    }

    // #4271: az eredeti megerősítési küszöb 30 fölött van; a kijelölést
    // pillanatfelvételként adjuk át, hogy a párbeszéd alatt ne változzon a cél.
    function addTagToRows(rowList, keyword) {
        if (!controller || !rowList || rowList.length === 0) return
        var rows = rowList.slice()
        if (rows.length <= 30) {
            controller.addKeywordToRows(rows, keyword)
            return
        }
        mainDialogs.bulkTagConfirmLoader.ensure().askFor(rows, keyword)
    }

    // a kijelölt képek abszolút útvonalai (#15/#16) — a fájlműveletek a
    // művelet ELŐTT gyűjtött útvonal-listán futnak, így a közben frissülő
    // rács-indexek nem tévesztenek célt
    function selectedPaths() {
        var rows = window.selectedRows()
        var paths = []
        for (var k = 0; k < rows.length; ++k) {
            var p = controller.photos.filePathAt(Number(rows[k]))
            if (p.length > 0) paths.push(p)
        }
        return paths
    }

    function resetFacesForPaths(paths) {
        if (!window._faceScanController || !paths || paths.length === 0)
            return
        if (window._faceScanController.resetFacesForPhotos(paths) > 0) {
            if (controller) controller.refreshCollections()
            photoViewer.facesEditRevision += 1
            // A hiányzó modellről a meglévő Arckeresés ablak ad érthető
            // okot és letöltési lehetőséget; reset után ne maradjon néma.
            if (!window._faceScanController.isAvailable())
                faceScanDialog.open()
        }
    }

    // jobbklikk a rácson (#15): a klikkelt kép kerüljön kijelölésbe (ha még
    // nincs benne), majd a kontextusmenü a kattintás helyén nyílik
    function openPhotoContextMenu(index, item, x, y) {
        if (window.selectedIndexes.indexOf(index) === -1) {
            window.selectedIndexes = [index]
            window.selectedIndex = index
        }
        window.fileOpTargetRow = index
        photoContextMenu.popup(item, x, y)
    }

    // #4534: a mappacsoport aktuális rácssorrendjében a legelső kijelölt
    // képtől a csoport végéig kijelöl, majd megnyitja a mappa tulajdonságait.
    function splitFolderHere() {
        if (!controller || controller.currentFolder === ""
                || controller.currentAlbumToken !== ""
                || controller.currentPersonName !== "")
            return
        var rows = window.selectedRows()
        if (rows.length === 0) return
        var currentFolder = controller.currentFolder
        var first = -1
        for (var i = 0; i < rows.length; ++i) {
            var row = Number(rows[i])
            var path = controller.photos.filePathAt(row)
            if (path.substring(0, path.lastIndexOf("/")) === currentFolder
                    && (first < 0 || row < first))
                first = row
        }
        if (first < 0) return
        var range = controller.photos.groupRange(first)
        if (range.length !== 2) return
        var paths = []
        var selected = []
        for (var row = first; row <= Number(range[1]); ++row) {
            var imagePath = controller.photos.filePathAt(row)
            if (imagePath.substring(0, imagePath.lastIndexOf("/"))
                    !== currentFolder)
                return
            paths.push(imagePath)
            selected.push(row)
        }
        if (paths.length === 0) return
        var photo = controller.photos.itemAt(first)
        var date = photo && photo.takenAt ? photo.takenAt.substring(0, 10) : ""
        if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return
        window.selectedIndexes = selected
        window.selectedIndex = first
        folderPane.openSplitFolderHere(paths, date)
    }

    // Kijelölés-logika (Picasa): sima katt = egy kép; Ctrl = hozzávesz/
    // elvesz; Shift = tartomány a horgonytól. (Számítás: selection.js)
    function handleThumbClick(index, modifiers) {
        var i = Number(index)
        var mods = Number(modifiers)
        if (mods & Qt.ControlModifier) {
            window.selectedIndexes =
                Selection.toggled(window.selectedIndexes, i)
            window.selectedIndex = i
        } else if ((mods & Qt.ShiftModifier) && window.selectedIndex >= 0) {
            // #1219: a tartomány a HORGONY mappacsoportján belül marad —
            // az eredetiben a tartomány-mag mindig egyetlen album
            // kijelölés-csomópontján fut, nem tud mappahatárt átlépni.
            var hatar = controller.photos.groupRange(window.selectedIndex)
            var veg = i
            if (hatar.length === 2)
                veg = Math.max(hatar[0], Math.min(hatar[1], i))
            window.selectedIndexes =
                Selection.range(window.selectedIndex, veg)
        } else {
            window.selectedIndexes = [i]
            window.selectedIndex = i
        }
    }
    // ⚠️ #1145: MAPPAVÁLTÁSKOR a kijelölés törlődik.
    //
    // Az eredetiben az előző mappa kijelölés-csomópontját a program
    // elengedi (`0x0056bc10` → `0x718a50`), és a helyére az újat teszi.
    // Nálunk a kijelölés túlélte a váltást — így egy másik mappában
    // végzett művelet (csillag, forgatás, törlés) a KORÁBBI mappa képeire
    // hatott volna.
    //
    // A `currentFolder` a `statusChanged`-en jelez, ezért a mappa saját
    // értékét figyeljük, nem a jelzést: így csak VALÓDI váltásra törlünk.
    property string _lastFolder: ""
    Connections {
        target: controller
        function onStatusChanged() {
            var folder = controller ? controller.currentFolder : ""
            if (folder === window._lastFolder) return
            window._lastFolder = folder
            // #1183: ha a kijelölés MÁR az új mappában van, akkor a váltást
            // épp a rács fókusza okozta (a felhasználó ott kattintott) —
            // nincs mit elengedni, az előző mappáé úgyis lecserélődött.
            if (window._selectionInFolder(folder)) return
            window.clearSelection()
        }
    }

    // #1183: a fókuszsor mappája — a bal hasáb kiemelése ezt követi
    function _folderOfRow(row) {
        if (!controller || row < 0) return ""
        var groups = controller.feedGroups
        if (!groups) return ""
        for (var i = 0; i < groups.length; ++i) {
            var g = groups[i]
            if (row >= g.start && row < g.start + g.count) return g.path
        }
        return ""
    }

    function _selectionInFolder(path) {
        return path !== "" && window._folderOfRow(window.selectedIndex) === path
    }

    // A rács fókusza vezeti a jelenlegi mappát (az eredetiben `0x0056bc10`
    // → `0x56b910`, „a jelenlegi album megváltozott"). Egy helyen kötjük be,
    // így a kattintás, a nyilas léptetés és a programból állított fókusz is
    // ugyanígy viselkedik.
    onSelectedIndexChanged: {
        var folder = window._folderOfRow(window.selectedIndex)
        if (folder !== "" && controller) controller.focusFolder(folder)
    }

    function clearSelection() {
        window.selectedIndexes = []
        window.selectedIndex = -1
    }
    // ⚠️ #1145: a kijelölés hatóköre a JELENLEGI MAPPA, nem a teljes feed.
    //
    // Az eredetiben az „Az összes kijelölése" (`0x9cb8`) kezelője
    // (`0x005e5070`) EGYETLEN kijelölés-csomóponton dolgozik, és az EGY
    // mappához tartozik (`CSelectionNode + 0x3c0`). A Picasában
    // egyáltalán nem létezik mappákon átnyúló kijelölés.
    //
    // Nálunk a Ctrl+A tízezres nagyságrendű sort jelölt ki — a tulajdonos
    // ezt jelentette (#1184), és emiatt „majdnem lefagyott az app".
    //
    // A csoportot a jelenlegi kijelölés/fókusz sora dönti el; ha nincs
    // ilyen, a jelenlegi mappa csoportja.
    function _currentGroup() {
        if (!controller) return null
        var groups = controller.feedGroups
        if (!groups || groups.length === 0) return null
        var row = window.selectedIndex
        if (row >= 0) {
            for (var i = 0; i < groups.length; ++i) {
                var g = groups[i]
                if (row >= g.start && row < g.start + g.count) return g
            }
        }
        var current = controller.currentFolder
        for (var j = 0; j < groups.length; ++j)
            if (groups[j].path === current) return groups[j]
        return groups[0]
    }

    function _groupRows() {
        var g = window._currentGroup()
        if (!g) return Selection.allRows(controller.photos.rowCount())
        var rows = []
        for (var i = g.start; i < g.start + g.count; ++i) rows.push(i)
        return rows
    }

    function selectAll() {
        var range = window._groupRows()
        window.selectedIndexes = range
        if (range.length > 0) window.selectedIndex = range[0]
    }
    // #422: „Kiválasztás megfordítása" (Ctrl+I) — a mappa-kontextusmenü és
    // a Szerkesztés menü tétele
    function invertSelection() {
        // #1145: a megfordítás is a jelenlegi mappán belül marad
        var scope = window._groupRows()
        var current = window.selectedIndexes
        var rows = []
        for (var i = 0; i < scope.length; ++i)
            if (current.indexOf(scope[i]) === -1) rows.push(scope[i])
        window.selectedIndexes = rows
        window.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
    // #426: „Csillagozottak kijelölése" (Szerkesztés menü) — a jelenlegi
    // nézet csillagos képeit jelöli ki (NEM a Mappák panel nézet-szűrője).
    function selectStarred() {
        // #1145: a csillagozottak is a jelenlegi mappából
        var scope = window._groupRows()
        var rows = []
        for (var i = 0; i < scope.length; ++i)
            if (controller.photos.starAt(scope[i])) rows.push(scope[i])
        window.selectedIndexes = rows
        window.selectedIndex = rows.length > 0 ? rows[0] : -1
    }
    // A személyalbum-javaslatok állapota külön komponensben él. A régi
    // főablak-tulajdonságok és függvények továbbra is nyilvánosak.
    MainPeopleAlbumState {
        id: mainPeopleAlbumState
        hostWindow: window
        hostController: controller
        hostFaceScanController: typeof faceScanController !== "undefined"
            ? faceScanController : null
        hostRemovePeopleFacesDialog: removePeopleFacesDialog
        hostCreateDialogs: createDialogs
    }
    property alias _javaslatRevizio: mainPeopleAlbumState._javaslatRevizio
    readonly property string personAlbumName:
        mainPeopleAlbumState.personAlbumName
    readonly property string personAlbumAvatarUrl:
        mainPeopleAlbumState.personAlbumAvatarUrl
    readonly property bool personAlbumCanRemoveSelection:
        mainPeopleAlbumState.personAlbumCanRemoveSelection
    readonly property bool personAlbumCanSetThumbnail:
        mainPeopleAlbumState.personAlbumCanSetThumbnail
    readonly property int personSuggestionCount:
        mainPeopleAlbumState.personSuggestionCount
    readonly property var personSelectedSuggestionIds:
        mainPeopleAlbumState.personSelectedSuggestionIds
    readonly property bool personSuggestionsOnly:
        mainPeopleAlbumState.personSuggestionsOnly
    readonly property bool personFaceZoom: mainPeopleAlbumState.personFaceZoom
    function removePersonAlbumSelection() {
        mainPeopleAlbumState.removePersonAlbumSelection()
    }
    function setPersonAlbumThumbnailFromSelection() {
        mainPeopleAlbumState.setPersonAlbumThumbnailFromSelection()
    }
    function openPersonAlbumMovie() { mainPeopleAlbumState.openPersonAlbumMovie() }
    function openPeopleAlbumsMovie() { mainPeopleAlbumState.openPeopleAlbumsMovie() }
    function selectPersonSuggestions() {
        mainPeopleAlbumState.selectPersonSuggestions()
    }
    function confirmPersonSuggestions() {
        mainPeopleAlbumState.confirmPersonSuggestions()
    }
    function removePersonSuggestions() {
        mainPeopleAlbumState.removePersonSuggestions()
    }
    function setPersonSuggestionsOnly(csak) {
        mainPeopleAlbumState.setPersonSuggestionsOnly(csak)
    }
    function setPersonFaceZoom(arc) {
        mainPeopleAlbumState.setPersonFaceZoom(arc)
    }
    function findMoreSuggestions() {
        mainPeopleAlbumState.findMoreSuggestions()
    }
    function _javaslatFrissult() {
        mainPeopleAlbumState._javaslatFrissult()
    }

    //: #1823: „szerkesztések mentése lemezre" a mappa-fejlécről. A
    //: művelet a #444 mentés-párbeszédéé — ez csak egy újabb belépési
    //: pont, ugyanazzal a megerősítéssel és biztonsági mentéssel.
    function saveSelectedEdits() {
        saveDialogs.ensure().openSave(window.selectedIndexes)
    }
    // #422: „Exportálás HTML-oldalként…" a mappa-kontextusmenüből — a
    // dialógus itt él (a menüsáv is ezt nyitja)
    function openWebExport() { webExportDialog.open() }
    // #1472: nyomtatás — HÁROM belépési pont vezet ide (Fájl ▸ Nyomtatás…,
    // Ctrl+P, és a képtálca „Nyomtatás" gombja), ahogy az exportnál is.
    // A célpont ugyanaz a HÁROM ág, mint a `rotateTargetRow()`-nál:
    // diavetítés közben a VETÍTETT kép, a nézőben a MEGJELENÍTETT kép, a
    // rácsban a kijelölés.
    //
    // ⚠️ A diavetítés ága nem elhagyható: a `startSlideshow()` NEM állítja
    // a `viewerOpen`-t, tehát a menü és a Ctrl+P vetítés közben is
    // engedélyezett marad — enélkül a felhasználó egy képet néz, és a
    // RÁCS kijelölése menne nyomtatásra.
    function printTargetRows() {
        if (slideshow.visible)
            return slideshow.currentIndex >= 0 ? [slideshow.currentIndex] : []
        if (window.viewerOpen)
            return window.photoActionRows()
        return window.selectedRows()
    }
    function openPrint() { printDialog.ensure().openForRows(window.printTargetRows()) }
    // #1590: Mappa ▸ Bélyegképek nyomtatása… — ugyanaz a párbeszéd,
    // indexkép-elrendezésre állítva. Kijelölés nélkül a MEGNYITOTT MAPPA
    // egésze a célpont: az eredetiben ez a parancs a mappa/album tétele,
    // nem a kijelölésé.
    function openContactSheetPrint() {
        var sorok = window.printTargetRows()
        // a `_groupRows` a MEGNYITOTT mappa sorai (nem az egész rácsé,
        // ha az több mappát mutat) — pontosan az, amire a mappa-menü
        // tétele vonatkozik
        if (sorok.length === 0) sorok = window._groupRows()
        printDialog.ensure().openForContactSheet(sorok)
    }
    // #422: a mappa-kontextusmenünek HÁROM megnyitási pontja van (a rács
    // üres területe, a bal panel mappa-sora, a rács mappa-fejléce), és
    // mindhárom UGYANAZT a menüt nyitja. A menü a FolderPane-ben él; a
    // másik két hívó ezen az ablak-szintű átjárón éri el.
    function openFolderContextMenu(path) {
        var target = path && path.length > 0
            ? path : (controller ? controller.currentFolder : "")
        if (target.length > 0) folderPane.openFolderContextMenu(target)
    }
    // #4637: az alsó kimeneti gombsor helyi menüje.
    function openConfigureButtonsContextMenu(anchorItem, x, y) {
        if (!anchorItem) return
        configureButtonsContextMenu.popup(anchorItem, x, y)
    }

    // A helyi gombsor-menü az ApplicationWindow része, nem a PicasaMenuBaré:
    // így a főmenü szerkezete és bejárási útvonalai változatlanok maradnak.
    Menu {
        id: configureButtonsContextMenu
        objectName: "configureButtonsContextMenu"
        MenuItem {
            objectName: "configureButtonsContextMenuItem"
            text: qsTr("Configure Buttons...")
            onTriggered: picasaMenuBar.configureButtonsRequested()
        }
    }

    // #135: a háttér-frissítés (5 perces rescan, watcher-jelzés) a
    // rács-modellt teljesen resetelheti — beszúrt/eltűnt fájloknál a
    // sor-indexek elcsúsznának, és a csillag/forgatás/elrejtés/export a
    // FELHASZNÁLÓ által kijelölttől eltérő képre hatna. A resetet
    // megelőzően elmentjük a kijelölt sorok fotó-id-it (a sor-index
    // ekkor még a RÉGI adatot tükrözi), majd a reset után az id-k
    // alapján képezzük újra a kijelölést — az eltűnt fotók kiesnek.
    property var _pendingSelectedIds: []
    property string _pendingAnchorId: ""
    Connections {
        // #305: engine-leépítéskor a `controller` context property null
        // lehet, miközben ez a kötés újra kiértékelődik — null-őr kell.
        target: controller ? controller.photos : null
        function onModelAboutToBeReset() {
            var ids = []
            for (var k = 0; k < window.selectedIndexes.length; ++k) {
                var id = controller.photos.idAt(Number(window.selectedIndexes[k]))
                if (id.length > 0) ids.push(parseInt(id, 10))
            }
            window._pendingSelectedIds = ids
            window._pendingAnchorId = window.selectedIndex >= 0
                ? controller.photos.idAt(window.selectedIndex) : ""
        }
        function onModelReset() {
            window.selectedIndexes = Selection.remapByIds(
                window._pendingSelectedIds, controller.photos.rowOfId)
            window.selectedIndex = window._pendingAnchorId.length > 0
                ? controller.photos.rowOfId(parseInt(window._pendingAnchorId, 10))
                : -1
            // Az átnevezett fájl új útvonal miatt új adatbázis-id-t kaphat.
            // Csak akkor helyettesítjük a régi azonosítót, ha az már eltűnt
            // a modellből és az új útvonal megjelent; sikertelen átnevezésnél
            // a régi ID-alapú állapot marad érvényben.
            if (window._pendingRenamePhotoId.length > 0
                    && window._pendingRenameTargetPath.length > 0) {
                var ujSor = controller.photos.rowOfPath(
                    window._pendingRenameTargetPath)
                var regiId = parseInt(window._pendingRenamePhotoId, 10)
                if (ujSor >= 0
                        && controller.photos.rowOfId(regiId) < 0
                        && window._pendingSelectedIds.indexOf(regiId) >= 0) {
                    var ujKijeloles = window.selectedIndexes.slice()
                    if (ujKijeloles.indexOf(ujSor) < 0)
                        ujKijeloles.push(ujSor)
                    ujKijeloles.sort(function (a, b) { return a - b })
                    window.selectedIndexes = ujKijeloles
                    if (window._pendingAnchorId === window._pendingRenamePhotoId)
                        window.selectedIndex = ujSor
                }
                window._pendingRenamePhotoId = ""
                window._pendingRenameTargetPath = ""
            }
        }
    }
    // A főablak gyorsbillentyűi önálló komponensben (#6136).
    MainKeyboardShortcuts {
        id: mainKeyboardShortcuts
        hostWindow: window
        hostController: controller
        hostDocumentTabStrip: documentTabStrip
        hostExportDialogs: exportDialogs
        hostFileOpsController: typeof fileOpsController !== "undefined"
            ? fileOpsController : null
        hostFileOpsDialogs: fileOpsDialogs
        hostHelpDialog: helpDialog
        hostPhotoViewer: photoViewer
        hostPicasaMenuBar: picasaMenuBar
        hostSaveDialogs: saveDialogs
        hostSlideshow: slideshow
        hostTrayBar: trayBar
    }

    //: #3544: amíg egy külön ablakos párbeszéd látszik, a főablak két
    //: súgó-billentyűje HALLGAT. A Qt 6 az ablakszintű gyorsbillentyűt a
    //: főablak TRANZIENS gyermekablakaiban is illeszti (és a főablak `active`-ja
    //: is igaz marad), ott pedig a párbeszéd saját F1-e/Shift+F1-e
    //: (`WindowHelp`) áll: a kettő kétértelmű, és MEGMÉRVE egyik sem sül el.
    //: A párbeszédek alkalmazás-modálisak, a főablak addig úgysem kezelhető.
    readonly property bool _kulonAblakosParbeszedNyitva:
        [folderManager, importSourceDialog, optionsDialog, webExportDialog,
         printDialog].some(function (d) { return d.item !== null && d.item.visible })

    //: #2054: a mutató helye a Shift+F1-hez. A `HoverHandler` a teljes
    //: ablakot lefedi, de NEM nyel el eseményt (`acceptedButtons: NoButton`),
    //: tehát semmilyen meglévő vezérlőt nem zavar.
    property point helpCursor: Qt.point(-1, -1)

    HoverHandler {
        objectName: "helpCursorTracker"
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onPointChanged: window.helpCursor = point.position
    }

    //: #2054: a mutató alatti elemtől FELFELÉ sétálunk a szülőláncon az
    //: első olyan ősig, amelyik deklarál `helpTopic`-ot. Így nem kell
    //: minden gombot felcímkézni: elég a panelekre és a párbeszédekre,
    //: a többi öröklődik. Ha egyik sem deklarál, ÜRES jön vissza, és a
    //: néző a főoldalt nyitja — néma kudarc nincs.
    //:
    //: #3463: a `childAt()` CSAK a közvetlen, legfelső gyermeket adja — az
    //: pedig gyakran egy üres, az egész ablakot kitöltő réteg (pl. egy
    //: halasztott párbeszéd `DeferredDialog`-betöltője), amelyben nincs
    //: téma. A keresés ezért MÉLYSÉGI: felülről lefelé minden olyan látható
    //: gyermeket kipróbál, amelyik a pontot tartalmazza, és a legmélyebb
    //: témát adja; ha egy ág üres, az alatta fekvővel folytatja. A réteg
    //: (`overlay`) párbeszédei NEM itt kapnak témát: amíg egy modális
    //: párbeszéd nyitva van, a saját Shift+F1-e a saját fejezetét nyitja.
    function _temaAPontban(elem, x, y) {
        var gyerekek = elem.children
        for (var i = gyerekek.length - 1; i >= 0; --i) {
            var gyerek = gyerekek[i]
            if (!gyerek.visible || gyerek.width <= 0 || gyerek.height <= 0)
                continue
            var pont = elem.mapToItem(gyerek, x, y)
            if (!gyerek.contains(pont))
                continue
            var tema = window._temaAPontban(gyerek, pont.x, pont.y)
            if (tema.length > 0)
                return tema
        }
        if (elem.helpTopic !== undefined && String(elem.helpTopic).length > 0)
            return String(elem.helpTopic)
        return ""
    }

    //: #3463: a súgó megnyitása egy fejezettel — a modális
    //: réteg-párbeszédek Shift+F1-e is ezt hívja (üres fejezet = főoldal).
    function nyisdASugot(tema) {
        helpDialog.ensure().nyisdMeg(tema)
    }

    function helpTopicUnderCursor() {
        if (window.helpCursor.x < 0) return ""
        //: a `helpCursor` a `contentItem` koordinátáiban áll (a
        //: `HoverHandler` ott ül)
        return window._temaAPontban(
            window.contentItem, window.helpCursor.x, window.helpCursor.y)
    }

    // #1526/#1571: a fájl-vágólap billentyűi — FÓKUSZ-ÉRZÉKENYEN.
    //
    // ⚠️ A kézenfekvő megoldás valódi regressziót okozna: egy sima
    // `WindowShortcut` a Ctrl+C-t ELVENNÉ a szövegmezőktől, tehát
    // átnevezés, keresés vagy feliratszerkesztés közben a felhasználó nem
    // tudná a beírt szöveget másolni. Ez rosszabb volna a mai állapotnál
    // (#1571).
    //
    // A kapu: ha a fókusz szövegmezőn van, a billentyű a MEZŐÉ. A próba a
    // `selectedText` tulajdonság megléte — ezt a `TextInput`/`TextEdit`
    // (és minden rájuk épülő `TextField`/`TextArea`) hordozza, más elem
    // nem. Így nem kell felsorolni a mezőtípusokat, és a jövőbeli
    // mezőkre is magától áll.
    readonly property bool _szovegmezoneVanFokusz:
        window.activeFocusItem !== null
        && window.activeFocusItem.selectedText !== undefined
    readonly property bool _konyvtariGyorsbillentyuEngedelyezve:
        !window.viewerOpen && !window._szovegmezoneVanFokusz
    //: #1406: `ID_SEARCHTOKEN` — a megadott címke tartalmából rendes album.
    //: A HÁROM szöveg mind a saját helyén: a menüfelirat a menüsorban, a cím
    //: és a felszólítás itt (mérve, `0x005d8330`).
    DeferredDialog {
        id: showTagAsAlbumDialog
        objectName: "showTagAsAlbumDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            NameInputDialog {
                objectName: "showTagAsAlbumDialog"
                //: `ThumbUI::addsearchtoken`
                title: qsTr("Add search tag")
                //: `CAlbumState::addsearchprompt`
                prompt: qsTr("Please enter a tag to show as an album")
                onAccepted: {
                    if (controller.showTagAsAlbum(enteredName) === "") {
                        errorBanner.notice = true
                        errorBannerText.text = qsTr("No pictures have that tag.")
                    }
                }
            }
        }
    }

    //: #1405: a keresés mentése albumként — a menütétel és a megerősítés is
    //: ezt hívja (egy hely, egy viselkedés).
    function mentsdAKeresest() {
        if (controller.saveSearchAsAlbum() === "") {
            errorBanner.notice = true
            errorBannerText.text = qsTr("The search results could not be saved as an album.")
        }
    }

    //: #1405: a megerősítés CSAK 1000 találat felett nyílik, ezért halasztott
    //: (#1720): a legtöbb munkamenetben fel sem épül.
    DeferredDialog {
        id: saveSearchDialog
        objectName: "saveSearchDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "saveSearchConfirm"
                namePrefix: "saveSearch"
                title: qsTr("Save search results")
                //: `CThumbUI::SaveSearchBigBtn` — az eredeti gombfelirata NEM
                //: „Igen", hanem a művelet megnevezése
                yesText: qsTr("Create Album")
                onConfirmed: window.mentsdAKeresest()
            }
        }
    }

    //: #3644: a néző elhagyása ELŐTT az „aa" mód kapuja dönt a két fél
    //: szerkesztéséről (`PhotoViewer.aaKilepesKapu`, spec
    //: `ui-audit-editor.md` 4/c.1). `true`: folytatható MOST; `false`: a
    //: párbeszéd nyitva, a `folytatas` a VÁLASZ után fut, Mégsére elmarad.
    //: Az eredeti a programzáráskor is kérdez (`SC_CLOSE` → `0x0057c4e0` →
    //: `0x005e45c0` → `0x0056aad0`), és Mégsére nem zár be (`0x0057c59c`).
    function aaKapu(folytatas) {
        return !window.viewerOpen || photoViewer.aaKilepesKapu(folytatas)
    }

    //: #671 4. pont: a kilépés NEM kérdez — KIVÉVE, ha háttérmunka fut.
    //: Az eredeti Picasa sem blokkolja a kilépést („Uploads will resume next
    //: time"), de rákérdez; nálunk a háttérmunka NEM folytatódik legközelebb,
    //: ezért a szöveg a mi valóságunkat mondja, nem az eredetit fordítja.
    //:
    //: Egy helyen fut: a Fájl ▸ Kilépés menütétel és az ablak „X"-e is ezt
    //: hívja — különben az egyik út megkérdezné, a másik nem.
    function kilepes() {
        if (!window.aaKapu(window.kilepes)) return   // #3644
        //: #305: null-őr — a leépülő motor is újraértékelheti a kötést
        if (controller && controller.backgroundWorkRunning()) {
            kilepesDialog.askExit()
            return
        }
        Qt.quit()
    }

    //: #1720: halasztott — a legtöbb munkamenetben fel sem épül.
    DeferredDialog {
        id: kilepesDialog
        objectName: "exitConfirmDialogLoader"
        anchors.fill: parent
        function askExit() {
            //: a `decisionKey` SZÁNDÉKOSAN üres: az adatvesztéssel járó
            //: kérdést nem lehet „ne kérdezze újra"-val elnyomni
            ensure().ask("", qsTr(
                "Background work is still running (export, web export or "
                + "face scanning). If you exit now, it stops and does not "
                + "resume later."))
        }
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "exitConfirm"
                namePrefix: "exit"
                title: qsTr("Exit PicasaPy")
                //: az eredeti gombpárja „Exit Now" / „Keep Going" — a
                //: viselkedés (accept/deny) változatlan, csak a felirat
                yesText: qsTr("Exit Now")
                noText: qsTr("Keep Going")
                onConfirmed: Qt.quit()
            }
        }
    }

    //: #1526: a beillesztés EGY helyen — a menütétel és a billentyű is ezt
    //: hívja. (⚠️ A billentyű-őr a `Shortcut` törzsét egy szintig elemzi,
    //: tehát ott nem lehet ágas kód: ha a logika a `Shortcut`-ba kerül, az
    //: őr NEM LÁTJA meg a kötést, és a menütétel „néma hirdetőnek" látszik.)
    // #5877: „Copy Text" - a kijelölés első képének Text eszközös rétege.
    function masoldASzovegreteget() {
        if (!controller) return
        var sorok = window.photoActionRows()
        if (sorok.length === 0) return
        controller.copyTextLayer(sorok)
    }

    // #5877: „Paste Text" - a másolt Text eszközös réteg a kijelölés minden
    // képére kerül; a kijelölt réteg pufferként is használható.
    function illeszdBeASzovegreteget() {
        if (!controller) return
        var sorok = window.photoActionRows()
        if (sorok.length === 0) return
        controller.pasteTextLayer(sorok)
    }

    function beillesztAVagolaprol() {
        if (fileOpsController.pasteFilesFromClipboard(controller.currentFolder))
            return
        errorBanner.notice = true
        errorBannerText.text = qsTr("There are no files on the clipboard to paste.")
    }

    // Picasa gyorsbillentyűk: Ctrl+R jobbra, Ctrl+Shift+R balra forgat.
    // Diavetítés közben (#8) a vetített kép a célpont, nem a rács-kijelölés.
    function rotateTargetRow() {
        if (slideshow.visible) return slideshow.currentIndex
        return trayBar.starTargetRow
    }
    // #103: csak-videó célpontnál a forgatás tiltott — a tálca ↺/↻
    // gombjainak őre (a controller-slotok defenzíven szintén kihagyják
    // a videókat, vegyes kijelölésnél csak a fotók forognak)
    function rotateTargetsAllVideo() {
        // #305: null-őr — a TrayBar `enabled:` kötése (ami ezt hívja)
        // a QML-engine leépítésekor is újraértékelődhet
        if (!controller) return false
        var rows = window.viewerOpen
            ? [photoViewer.currentIndex]
            : window.selectedRows()
        if (rows.length === 0) return false
        for (var k = 0; k < rows.length; ++k)
            if (!controller.photos.isVideoAt(Number(rows[k])))
                return false
        return true
    }
    //: #2902: tükrözés — az eredeti könyvtárnézeti kezelőjének két ága
    //: (`0x005e63d6` vízszintes, `0x005e6408` függőleges), a keymapben
    //: 35. *Flip Horizontal* / 36. *Flip Vertical*. MENÜPONT SZÁNDÉKOSAN
    //: NINCS hozzá: a 3.9 menüiben sem volt, a funkció csak billentyűvel
    //: érhető el (`docs/specs/picasa-gyorsbillentyuk.md` 10.3–10.4).
    //:
    //: A cél a KIJELÖLÉS (az eredeti ága is a panelre hat); nézőben a
    //: megnyitott kép, a forgatás `rotateTargetRow` mintája szerint.
    function tukrozesiSorok() {
        if (window.viewerOpen) return [photoViewer._kijeloltSort()]
        return window.selectedRows()
    }

    // -- Időrend bemutató (#5770, Ctrl+5) ------------------------------------
    // Mappa- és albumkártyás, teljes képernyős bemutató.
    function timelineCollectionForId(collectionId) {
        if (!timelineController || !timelineController.collections)
            return null
        var keresett = String(collectionId || "")
        for (var i = 0; i < timelineController.collections.length; ++i) {
            var collection = timelineController.collections[i]
            if (collection.collectionId === keresett
                    || collection.folderPath === keresett)
                return collection
        }
        return null
    }

    function selectTimelineCollection(collection) {
        if (!controller || !collection)
            return -1
        toolbar.clearSearch()
        window.clearSelection()
        window.unnamedFacesOpen = false
        if (collection.kind === "album")
            controller.showAlbum(collection.albumToken)
        else
            controller.selectFolder(collection.folderPath)
        var row = controller.photos.rowOfPath(collection.firstPhotoPath)
        window.selectedIndex = row
        window.selectedIndexes = row >= 0 ? [row] : []
        return row
    }

    function closeTimeline() {
        var collection = timelineView.collectionAt(timelineView.currentIndex)
        if (collection)
            window.selectTimelineCollection(collection)
        window.timelineOpen = false
    }

    function toggleTimeline() {
        if (window.timelineOpen) {
            window.closeTimeline()
            return
        }
        timelineController.reload()
        window.timelineOpen = true
    }

    function startTimelineSlideshow(collectionId) {
        if (!controller || !collectionId)
            return
        var collection = window.timelineCollectionForId(collectionId)
        if (!collection)
            return
        var collectionModel = timelineController.slideshowModel(
            collection.collectionId)
        if (!collectionModel || collectionModel.rowCount() <= 0)
            return
        window.selectTimelineCollection(collection)
        window.timelineOpen = false
        window.timelineSlideshowModel = collectionModel
        window.timelineSlideshowActive = true
        window.visibilityBeforeSlideshow = window.visibility
        window.visibility = Window.FullScreen
        slideshow.start(0)
        if (!slideshow.visible)
            window.exitSlideshow()
    }

    // #4569: az eredeti F11 a képnéző teljes képernyős módját kapcsolja.
    // A diavetítés saját teljes képernyős állapotát ez a parancs nem írhatja felül.
    property int visibilityBeforeViewerFullscreen: Window.Windowed
    function toggleViewerFullscreen() {
        if (!window.viewerOpen || slideshow.visible) return
        if (window.visibility === Window.FullScreen) {
            window.visibility =
                window.visibilityBeforeViewerFullscreen === Window.FullScreen
                    ? Window.Windowed : window.visibilityBeforeViewerFullscreen
        } else {
            window.visibilityBeforeViewerFullscreen = window.visibility
            window.visibility = Window.FullScreen
        }
    }

    // -- diavetítés (#8) ----------------------------------------------------
    // Indítás: viszonyítási pont a néző képe / a rács-kijelölés / az első
    // kép; a vetítés valódi teljes képernyőn fut, kilépéskor az ablak
    // visszaáll, és a rács/néző követi a vetítés utolsó képét.
    property int visibilityBeforeSlideshow: Window.Windowed
    function startSlideshow(fromIndex) {
        var index = fromIndex
        if (index < 0)
            index = window.viewerOpen ? photoViewer.currentIndex
                                      : Math.max(0, window.selectedIndex)
        window.visibilityBeforeSlideshow = window.visibility
        window.visibility = Window.FullScreen
        slideshow.start(index)
        if (!slideshow.visible)   // nincs vetíthető fotó — állítsuk vissza
            window.exitSlideshow()
    }
    function startScreensaverPreview() {
        if (!controller || controller.prepareScreensaverPreview() <= 0) {
            errorBanner.notice = false
            errorBannerText.text = qsTr(
                "The selected screensaver sources contain no available pictures.")
            return
        }
        window.visibilityBeforeSlideshow = window.visibility
        window.visibility = Window.FullScreen
        slideshow.startScreensaver()
        if (!slideshow.visible)
            window.exitSlideshow()
    }
    function exitSlideshow() {
        var wasScreensaver = slideshow.screensaverMode
        var wasTimelineSlideshow = window.timelineSlideshowActive
        window.visibility =
            window.visibilityBeforeSlideshow === Window.FullScreen
                ? Window.Windowed : window.visibilityBeforeSlideshow
        if (wasScreensaver)
            return
        if (wasTimelineSlideshow) {
            window.timelineSlideshowActive = false
            window.timelineSlideshowModel = null
            return
        }
        if (slideshow.currentIndex >= 0) {
            if (window.viewerOpen) {
                photoViewer.show(slideshow.currentIndex)
            } else {
                window.selectedIndex = slideshow.currentIndex
                window.selectedIndexes = [slideshow.currentIndex]
            }
        }
    }

    // #922: a képtálca tartalma ÁLLAPOTKÉNT, nem közvetlen kötésként. Egy
    // `controller.heldCount`-ra épülő kötés a `controller` null állapotában
    // ki tud értékelődni ELŐSZÖR — olyankor a QML nem regisztrálja a
    // függőséget, és a kötés soha többé nem frissül. Ez a `Connections`
    // ettől független.
    property bool trayHasPictures: false
    Connections {
        target: controller
        function onHeldChanged() {
            window.trayHasPictures = controller.heldCount > 0
        }
    }
    // A Súgó által használt főablak-tulajdonság neve változatlan.
    readonly property alias keyboardShortcutGroups:
        mainKeyboardShortcuts.keyboardShortcutGroups

    menuBar: MainMenuBar {
        id: picasaMenuBar
        hostWindow: window
        hostController: controller
        hostFileOpsController: typeof fileOpsController !== "undefined"
            ? fileOpsController : null
        hostPassportController: typeof passportController !== "undefined"
            ? passportController : null
        hostAboutDialog: aboutDialog
        hostAddFileDialog: addFileDialog
        hostBackupHost: backupHost
        hostCollectionPasswordDialog: collectionPasswordDialog
        hostCompactDatabaseDialog: compactDatabaseDialog
        hostConfigureButtonsDialog: configureButtonsDialog
        hostCreateDialogs: createDialogs
        hostDedupDialog: dedupDialog
        hostExportDialogs: exportDialogs
        hostFaceScanDialog: faceScanDialog
        hostFileOpsDialogs: fileOpsDialogs
        hostFolderManager: folderManager
        hostFolderPane: folderPane
        hostGiftCdHost: giftCdHost
        hostHelpDialog: helpDialog
        hostImportSourceDialog: importSourceDialog
        hostMainDialogs: mainDialogs
        hostMoveDatabaseDialog: moveDatabaseDialog
        hostOptionsDialog: optionsDialog
        hostPeopleManagerLoader: peopleManagerLoader
        hostPhotoViewer: photoViewer
        hostPhotoViewerSettingsDialog: photoViewerSettingsDialog
        hostPicasaDataImportDialog: picasaDataImportDialog
        hostRemoveFromAlbumDialog: removeFromAlbumDialog
        hostRemovePeopleFacesDialog: removePeopleFacesDialog
        hostSaveDialogs: saveDialogs
        hostSaveSearchDialog: saveSearchDialog
        hostScreensaverDialog: screensaverDialog
        hostShowTagAsAlbumDialog: showTagAsAlbumDialog
        hostToolbar: toolbar
        hostTrayBar: trayBar
        hostWebExportDialog: webExportDialog
        hostXmpFacesWriteDialog: xmpFacesWriteDialog
    }

    MainDialogs {
        id: mainDialogs
        anchors.fill: parent
    }

    // #17: Elrejtés/Megjelenítés a kijelölésre; elrejtés után a kijelölést
    // ürítjük — az elrejtett sorok kiesnek a rácsból, az indexek eltolódnak
    function toggleHiddenSelection() {
        var rows = window.photoActionRows()
        if (rows.length === 0) return
        controller.toggleHiddenRows(rows)
        if (!window.viewerOpen) window.clearSelection()
    }

    // #1798: a kijelölés elküldése levélben. A tárgyat és a szöveget
    // SZÁNDÉKOSAN nem kérjük be: az eredeti Picasa sem kérdez, a levelet a
    // levelezőprogram szerkeszti meg — mi csak a csatolmányokkal nyitjuk meg.
    function sendSelectionByEmail() {
        if (typeof emailController === "undefined" || !emailController)
            return
        var sorok = window.photoActionRows()
        if (sorok.length === 0)
            return
        var csatolmanyok = emailController.prepareAttachments(
            sorok, sorok.length > 1)
        if (csatolmanyok.length === 0)
            return
        // A `sendRows` a beállítás szerint vagy küld, vagy a
        // `mailChoiceRequested`-del kérdést kér — a válasz lentebb.
        emailController.sendRows(csatolmanyok, "", "")
    }

    // #4330: a Fájl menü és a Ctrl+Shift+O ugyanazt a kijelölés-pillanatképet
    // adja a rendszer alapértelmezett fájlmegnyitójának.
    function openSelectionInDefaultEditor() {
        if (!fileOpsController) return
        var paths = window.photoActionPaths()
        if (paths.length > 0)
            fileOpsController.openPhotosInDefaultEditor(paths)
    }

    // #1798: a küldési út két visszajelzése. A `mailChoiceRequested` a
    // „minden küldéskor kérdezz" mód kérdése, az `emailFailed` a hibáé —
    // ez utóbbinak eddig SEHOL nem volt kezelője, tehát a hibaüzenet
    // („nincs levelezőprogram") némán elveszett.
    //: #1407: a három rendszermappa-tétel (Képek / Dokumentumok / Asztal)
    //: NEM gyökeret vált, hanem a teljes fára váltás UTÁN felfedi és
    //: kijelöli a mappát (spec 4.5/b: `push "all"` mindhárom ágban). A
    //: felfedés a hierarchia-vezérlő dolga, a KIJELÖLÉS a bekötőé — ezért
    //: jön ide a jelzés.
    //:
    //: ⚠️ Feloldhatatlan mappánál a vezérlő NEM jelez (spec 4.6: visszaesés
    //: a Sajátgép-gyökérre, nem hibaüzenet), tehát itt nincs hibaág.
    Connections {
        target: (typeof folderHierarchyController !== "undefined")
                ? folderHierarchyController : null
        function onRootFolderRevealed(utvonal) {
            folderHierarchyController.revealPath(utvonal)
            if (typeof controller !== "undefined" && controller)
                controller.selectFolder(utvonal)
        }
    }

    Connections {
        target: (typeof emailController !== "undefined")
                ? emailController : null
        function onMailChoiceRequested(utvonalak, targy, szoveg) {
            var parbeszed = emailChoiceDialog.ensure()
            parbeszed.attachmentPaths = utvonalak
            parbeszed.subject = targy
            parbeszed.body = szoveg
            parbeszed.open()
        }
        // #1798b: az előkészítés jelzése. A `sendSelectionByEmail()` a
        // képeket a beállított méretre kicsinyíti, ami nagy fájloknál
        // másodpercekig tart — jelzés nélkül úgy tűnik, nem történik semmi.
        // A #459-es közös sávot használjuk, TÁJÉKOZTATÓ (borostyán)
        // tónussal: ez nem hiba.
        function onPreparingChanged(fut) {
            errorBanner.notice = true
            errorBannerText.text = fut
                ? qsTr("Preparing attachments...")
                : ""
        }
        function onEmailFailed(uzenet) {
            // a #459-es közös hibasáv — a levelezős hibának eddig SEHOL
            // nem volt kezelője, tehát némán elveszett
            errorBanner.notice = false
            errorBannerText.text = uzenet
        }
    }

    DeferredDialog {
        id: emailChoiceDialog
        anchors.fill: parent
        sourceComponent: Component {
            EmailChoiceDialog {
                objectName: "emailChoiceDialog"
                onAccepted: emailController.sendWithDefaultClient(
                    attachmentPaths, subject, body, rememberChoice)
            }
        }
    }

    // #4533: Társítás… — a fájltípushoz társított alkalmazások választója (Linux)
    DeferredDialog {
        id: openWithDialog
        anchors.fill: parent
        sourceComponent: Component {
            OpenWithDialog {
                objectName: "openWithDialog"
                onAccepted: fileOpsController.openWithApp(photoPath, selectedAppId)
            }
        }
    }

    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: folderManager
        anchors.fill: parent
        sourceComponent: Component { FolderManagerDialog { } }
    }

    function openPeopleManagerForPerson(name) {
        var targetName = String(name || "").trim()
        if (peopleManagerLoader.status === Loader.Ready) {
            peopleManagerLoader.item.openForPerson(targetName)
        } else {
            window.pendingPeopleManagerPersonName = targetName
            peopleManagerLoader.active = true
        }
    }

    // #4334: a komponens csak az első menükattintásra töltődik be; a
    // külön fájl miatt a forró Main.qml-ben csak a bekötés marad.
    Loader {
        id: peopleManagerLoader
        objectName: "peopleManagerLoader"
        active: false
        source: Qt.resolvedUrl("PicasaPy/PeopleManagerDialog.qml")
        onLoaded: {
            item.controller = controller
            var targetName = window.pendingPeopleManagerPersonName
            window.pendingPeopleManagerPersonName = ""
            if (targetName.length > 0)
                item.openForPerson(targetName)
            else
                item.open()
        }
    }
    // Duplikátum-kezelő (#287): a SAJÁT kezelő-párbeszéd. #1398 óta a
    // másodpéldány-mód eredménysávjáról nyílik („Manage Duplicates..."), nem
    // az Eszközök menüből — a mért menüparancs a keresési módot kapcsolja.
    // #294: az appWindow-bekötés a „kijelölt képek" hatókörhöz kell — enélkül
    // a dialógus a mappa-hatókörre esne vissza (integrátori bekötés).
    DeferredDialog {
        id: dedupDialog
        anchors.fill: parent
        sourceComponent: Component { DedupDialog { appWindow: window } }
    }
    // #1473: az arckeresés belépési pontja. A vezérlőt az ablak-szintű
    // álnéven kapja (#1236) — az ablak maga NEM modális, a keresés alatt a
    // felhasználó tovább dolgozhat (#449).
    DeferredDialog {
        id: faceScanDialog
        anchors.fill: parent
        sourceComponent: Component {
            FaceScanDialog { faceScan: window._faceScanController }
        }
    }
    DeferredDialog {
        id: screensaverDialog
        objectName: "screensaverDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ScreensaverDialog {
                saverController: controller
                onPreviewRequested: window.startScreensaverPreview()
            }
        }
    }
    //: #4618: album-nézetben az eredeti rákérdez (`addtosaver::warning`);
    //: halasztva (#1612), a közös megerősítő párbeszéddel
    DeferredDialog {
        id: screensaverAlbumConfirmLoader
        objectName: "screensaverAlbumConfirmDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                namePrefix: "screensaverAlbumConfirm"
                title: qsTr("Confirm")
                property var pendingPaths: []
                function openFor(paths) {
                    pendingPaths = paths ? paths.slice() : []
                    if (pendingPaths.length > 0)
                        ask("", qsTr("Are you sure you want to add all of the"
                                     + " selected album's images?"))
                }
                onConfirmed: window.addPhotosToScreensaver(pendingPaths)
            }
        }
    }
    DeferredDialog {
        id: photoViewerSettingsDialog
        anchors.fill: parent
        sourceComponent: Component {
            PhotoViewerSettingsDialog { viewerController: controller }
        }
    }
    // #146: meglévő Picasa-telepítés átvétele — nyitása a Mappakezelő
    // gombjából (discoveryController.dialogRequested) vagy induláskori
    // automatikus felajánlásból (integrátori bekötés: picasaImportDialog.openAndDiscover())
    PicasaImportDialog {
        id: picasaImportDialog
        //: #3463: modális réteg-párbeszéd — a főablak Shift+F1-ét a Qt
        //: letiltja, amíg nyitva van
        Shortcut {
            sequence: "Shift+F1"
            enabled: picasaImportDialog.opened
                     && !window._szovegmezoneVanFokusz
            onActivated: window.nyisdASugot(picasaImportDialog.helpTopic)
        }
    }
    // Import forrásból (#23): az eszköztár "Import" gombja nyitja
    DeferredDialog {
        id: importSourceDialog
        anchors.fill: parent
        sourceComponent: Component { ImportSourceDialog { } }
    }
    // #1633: Fájl ▸ Fájl felvétele a Picasába… / Ctrl+O — natív fájlválasztó
    AddFileDialog { id: addFileDialog }
    // #1654: a tesztüzem naplójának „Mentés másként…" tartaléka —
    // csak akkor nyílik meg, ha a NAS közös mappája nem érhető el
    TesztuzemNaploDialog { id: tesztuzemNaploDialog }

    // első indítás: nincs még figyelt mappa → Mappakezelő felajánlása
    // #449: első indítás — az eredeti EGYETLEN kérdést tett fel (teljes gép
    // vs. Dokumentumok/Képek/Asztal), és nem nyitott mappalistát. Eddig
    // nálunk üres könyvtárnál rögtön a Mappakezelő nyílt ki: az egy fát és
    // egy jóval nagyobb döntést tett a felhasználó elé az első percben.
    Component.onCompleted: {
        if (controller && controller.attachHoverPreviewKeyState)
            controller.attachHoverPreviewKeyState(window)
        //: #598: a kezdő cellaméret átadása a bélyegkép-tárnak — enélkül az
        //: induló rács a felső szintről dolgozna, pedig a 144-es fokozat a
        //: kisebb szintből tízszer olcsóbban áll elő.
        if (controller) controller.setThumbCellSize(window.thumbSize)
        //: #3070: a megjelenítési mód kezdőállapota a felület színein
        window.frissitsdAMegjelenitesiPalettat()
        if (window.quickViewerLaunch) {
            window.startQuickViewer()
            return
        }
        initialScanDialog.openIfNeeded()
        // #1051: ha az előző munkamenet piszkozatot hagyott, most kell
        // felajánlani — enélkül a lemezen ragad, ahogy a tulajdonosé is
        collageDraftDialog.openIfNeeded()
        // #922: a képtálca kezdőállapota (a Connections innentől frissíti)
        if (controller) window.trayHasPictures = controller.heldCount > 0
        // #1622: NÉMA felderítés korábbi telepítésből származó adatra —
        // az eredeti is magától megnézi (`0x00406770`, két `Windows.old`
        // útvonal). Találat nélkül semmi nem történik; találatnál a
        // PicasaImportDialog KÉRDEZ, mielőtt bármit átvennénk.
        if (typeof discoveryController !== "undefined" && discoveryController)
            discoveryController.discoverAtStartup()
    }

    // Eszköztár: a fejléc önálló komponens, változatlan ablakfejlécként.
    header: MainWindowToolbar {
        id: toolbar
        hostWindow: window
        hostRefs: ({
            searchSuggestionsBox: searchSuggestionsBox,
            suggestionsTimer: suggestionsTimer,
            picasaMenuBar: picasaMenuBar,
            importSourceDialog: importSourceDialog,
            fileOpsDialogs: fileOpsDialogs
        })
    }

    // Kereső-javaslatok (#7): gépelés után rövid szünettel (debounce)
    // kérjük le, hogy NAS-on se fusson lekérdezés minden billentyűre.
    // #1515: null-őr (#305 mintája). A 150 ms-os debounce miatt a hívás a
    // gépeléstől ELVÁLIK: ha közben az ablak lebomlik, a `controller`
    // kontextus-tulajdonság már null, és a hívás QML-szkripthibát dobna.
    // Ez a felület egyetlen olyan pontja, ahol IDŐZÍTŐ hívja a
    // controllert — a #1515 tesztje volt az első, amely a valódi
    // (searchEdited → suggestionsTimer) úton ment végig, és kibukott.
    function refreshSuggestions() {
        if (!controller)
            return
        searchSuggestionsBox.suggestions =
            controller.searchSuggestions(toolbar.searchText)
    }
    Timer {
        id: suggestionsTimer
        interval: 150
        onTriggered: window.refreshSuggestions()
    }
    SearchSuggestions {
        id: searchSuggestionsBox
        objectName: "searchSuggestions"
        parent: toolbar
        z: 50
        x: toolbar.searchBoxItem.x
        y: toolbar.searchBoxItem.y + toolbar.searchBoxItem.height
        width: toolbar.searchBoxItem.width
        query: toolbar.searchText
        // #1026: a keresődoboz a könyvtár keretének része, tehát a buborék
        // sem úszhat rá a projekt-lapra (a beírt szöveg megmarad, ezért a
        // hosszra kötött feltétel önmagában igazat adna)
        visible: suggestions.length > 0 && toolbar.searchText.length > 0
                 && !window.viewerOpen && window.libraryFrameVisible
        onChosen: function(kind, name, param) {
            if (kind === "folder") {
                toolbar.clearSearch()
                window.clearSelection()
                controller.selectFolder(param)
            } else if (kind === "album") {
                toolbar.clearSearch()
                window.clearSelection()
                window.unnamedFacesOpen = false
                controller.showAlbum(param)
            }
            suggestions = []
        }
    }

    // #8: a diavetítés a főablak önálló vetítési rétege.
    MainSlideshow {
        id: slideshow
        hostWindow: window
    }

    PhotoViewer {
        id: photoViewer
        objectName: "photoViewer"
        anchors.fill: parent
        visible: window.viewerOpen
        // #305: null-őr
        photosModel: controller ? controller.photos : null
        // #422: a mentés-parancsok a nézőből — ugyanazok a megerősítések,
        // mint a rácsból (egy parancs, egy út)
        onSaveRequested: function(row) { saveDialogs.ensure().openSave([row]) }
        onRevertRequested: function(row) { saveDialogs.ensure().openRevert([row]) }
        onUndoAllEditsRequested: function(row) {
            mainDialogs.undoAllEditsDialog.ensure().openFor([row])
        }
        onResetFacesRequested: resetFacesForPaths(
            controller && photoViewer.aktivSor >= 0
                ? [controller.photos.filePathAt(photoViewer.aktivSor)] : [])
        // #2566: a jobb fiók a nézőben is nyílik (a panelek a nézőn belül
        // élnek, ld. PhotoViewer.qml). A Helyek-panel két írási művelete
        // UGYANAZON a megerősítésen megy át, mint a könyvtár-nézetben —
        // egy parancs, egy út.
        onClearGeotagRequested: (rows) => mainDialogs.panelClearGeotagDialog.ensure().futtasd(rows)
        onSetGeotagRequested: (rows, la, lo) => mainDialogs.setGeotagDialog.ensure().futtasd(rows, la, lo)
        onDropGeotagRequested: (rows, la, lo) => mainDialogs.dropGeotagDialog.ensure().futtasd(rows, la, lo)
        // #2566: a fiók két KIVEZETŐ parancsa. Mindkettő a könyvtár rácsát
        // cseréli le, amit a néző eltakarna — ezért előbb ZÁRUL a néző.
        // Nem az `onClosed` útján: az `resyncFolderOfRow`-t hív, ami épp a
        // most beállított nézetet írná felül.
        onFindTaggedRequested: function(keyword) {
            if (!window.aaKapu(function () { photoViewer.findTaggedRequested(keyword) }))
                return
            window.viewerOpen = false
            if (controller) controller.search(keyword)
        }
        onPersonChosen: function(name) {
            if (!controller) return
            if (!window.aaKapu(function () { photoViewer.personChosen(name) }))
                return
            window.viewerOpen = false
            window.clearSelection()
            window.unnamedFacesOpen = false
            controller.showPerson(name)
        }
        onPlayRequested: window.startSlideshow(currentIndex)
        onStarRequested: function(row) {
            if (controller) controller.toggleStar(row)
        }
        onRotateRequested: function(row, delta) {
            if (!controller) return
            if (delta < 0) controller.rotateLeft(row)
            else controller.rotateRight(row)
        }
        // #1002: a néző csak JELEZ — a panel feltöltése és a lapváltás
        // a gazdáé, ugyanúgy, ahogy a `CollagePanel` jelzéseinél.
        onEditCollageRequested: function(path) {
            window.openSavedCollage(path)
        }
        //: #2114: a film forrásprojektje — a `.mxf` képeit kijelöljük, és
        //: a filmkészítő párbeszéd a projekt diaidejével nyílik.
        onEditMovieRequested: function(path) {
            window.openSavedMovie(path)
        }
        onClosed: {
            var quickViewWasActive = controller
                && controller.quickViewActive === true
            window.viewerOpen = false
            if (quickViewWasActive) return
            window.selectedIndex = currentIndex   // a rács kövesse a nézőt
            window.selectedIndexes = [currentIndex]
            // a szerkesztések (filters=) azonnal látsszanak a rácson —
            // NAS-on a fájlfigyelő nem szól, nem várhatunk a rescanre (#59);
            // a feedben (#64) a néző át is léphetett másik mappába, ezért a
            // nézett kép mappáját frissítjük
            // #173: a megnyitás előtti feed-pozíciót megőrizzük — a resync
            // modellcseréje után NE a mappa elejére ugorjunk. A rögzítés a
            // resync ELŐTT történik (a savedY még a megnyitáskori), az
            // alkalmazás pedig a modellcsere UTÁN (Qt.callLater), illetve az
            // onFeedChanged ágon.
            mainLibraryCanvas.grid.beginRevealAfterViewer()
            controller.resyncFolderOfRow(currentIndex)
            Qt.callLater(mainLibraryCanvas.grid.applyRevealAfterViewer)
        }
        onCurrentIndexChanged: if (visible) window.selectedIndex = currentIndex
        // #422: a néző kontextusmenüjének törlés-tétele — a megerősítő
        // dialógusok itt élnek (a menü maga a PhotoViewer-ben)
        // #4621: a néző saját `Ctrl+Delete`-je és a helyi menü tétele is a
        // menüsáv KÖZÖS, nézetfüggő elágazásán megy át
        deleteRemovesFromAlbum: picasaMenuBar.deleteRemovesFromAlbum
        onDeleteRequested: picasaMenuBar.activateDeleteCommand()
    }


    // #5770: a Picasa Időrend külön teljes képernyős ablak, saját vezérlőkkel.
    TimelineView {
        id: timelineView
        objectName: "timelineView"
        transientParent: window
        visible: window.timelineOpen
        collectionsModel: timelineController ? timelineController.collections : []
        onClosed: window.closeTimeline()
        onSlideshowRequested: function(collectionId) {
            window.startTimelineSlideshow(collectionId)
        }
    }

    // #985: a dokumentum-fülsáv (#944) a tartalomterület TETEJÉN, az
    // eszköztár alatt. Nyitott projekt-lap nélkül a magassága 0, tehát a mai
    // elrendezés egyetlen képponttal sem csúszik el — ezt a
    // `test_collage_panel_wiring_985.py` külön állítja.
    DocumentTabStrip {
        id: documentTabStrip
        textEntryHasFocus: window._szovegmezoneVanFokusz
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        projectTabs: window.openProjectTabs

        // A néző és az Időrend a TELJES ablakot fedi; ilyenkor a sáv se ne
        // látsszon, se ne foglaljon helyet (a komponens `height`-kötését
        // ezért írjuk felül, nem csak a `visible`-t).
        visible: documentTabStrip.hasProjectTabs
                 && !window.viewerOpen && !window.timelineOpen
        height: documentTabStrip.visible ? documentTabStrip.savMagassag : 0

        onCloseAccepted: function(tabId, saveDraft) {
            if (tabId === window.movieMakerTabId) {
                window.movieMakerTabOpen = false
                return
            }
            if (!controller || tabId !== window.collageTabId) return
            // A háromgombos kérdés már eldőlt (#944); itt csak a
            // következményt hajtjuk végre — a piszkozat a Kollázsok albumba
            // megy (#949), majd a lap bezárul.
            if (saveDraft) controller.saveCollageDraft()
            controller.closeCollage()
        }
    }

    SplitView {
        id: mainSplit
        objectName: "mainSplit"
        // #985: a `anchors.fill: parent` négy horgonyra bomlik, hogy a
        // tartalom a fülsáv ALATT kezdődjön. Üres sávnál a sáv magassága 0,
        // tehát `documentTabStrip.bottom === parent.top` — a mai elrendezés
        // képpontra ugyanaz marad.
        anchors.top: documentTabStrip.bottom
        anchors.left: parent.left
        //: #3037: a fiók a jobb szélen ül, a könyvtár mellette ér véget —
        //: ez a mért `RIGHTDRAWEROFFSET` viselkedés (a tartalom eltolása).
        anchors.right: jobbFiok.visible ? jobbFiok.left : parent.right
        //: #3503: nyitott Ajándék-CD panelnél a könyvtár a panel fölött ér
        //: véget — a panel nem takarhatja el a képeket
        //: #3504: ugyanez a mentés-panelre is vonatkozik
        anchors.bottom: giftCdHost.visible ? giftCdHost.top
                        : (backupHost.visible ? backupHost.top : parent.bottom)
        // A Könyvtár lapjának tartalma. NEM `Loader.active`: a lap váltásakor
        // a feed nem semmisülhet meg, különben elveszne a görgetési helye és
        // a kijelölése (a #944 kimérte, a #985 tesztje állítja).
        // #1026: a KERET közös kapcsolójára kötve (a `libraryFrameVisible`
        // a `documentTabStrip.libraryActive`-ot hordozza) — így a könyvtár
        // tartalma, az eszközsáv és az alsó sáv EGYSZERRE megy.
        visible: !window.viewerOpen && !window.timelineOpen
                 && window.libraryFrameVisible
        orientation: Qt.Horizontal

        // #322: látható, fogható elválasztó. A Fusion alap-fogantyúja olyan
        // halvány, hogy a felhasználó meg sem találta — ez a delegate a
        // Picasa vékony sávját adja, hover/húzás közben kiemelkedve, és a
        // kurzort is átváltja, hogy a húzhatóság magától látsszon.
        handle: Rectangle {
            objectName: "folderPaneHandle"
            implicitWidth: 6
            implicitHeight: 6
            color: SplitHandle.pressed
                   ? Qt.darker(Theme.chromeBorder, 1.35)
                   : (SplitHandle.hovered
                      ? Qt.darker(Theme.chromeBorder, 1.15)
                      : Theme.chromeBorder)

            Behavior on color {
                ColorAnimation { duration: 100 }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton  // csak a kurzorért
                cursorShape: Qt.SplitHCursor
            }
        }

        MainFolderPane {
            id: folderPane
            objectName: "folderPane"
            // #305: null-őr — a controller a leépítéskor átmenetileg null
            SplitView.preferredWidth: controller ? controller.folderPaneWidth : 240
            //: #2329: MÉRT korlátok. A legkisebb szélesség ugyanaz a szám,
            //: mint az alapértelmezés (240) — a hasáb nem húzható alá.
            SplitView.minimumWidth: 240
            //: A felső korlát az eredetiben ABLAKFÜGGŐ: a főpanel
            //: szélessége mínusz 240 (`0x009d9e21`–`0x009d9e50`). A fix 600
            //: széles ablakon szűkebb volt az eredetinél, keskenyen pedig
            //: tágabb. A `Math.max` azért kell, hogy nagyon keskeny
            //: ablakon se csússzon a maximum a minimum ALÁ — a `SplitView`
            //: ilyenkor kiszámíthatatlanul viselkedne.
            SplitView.maximumWidth: Math.max(240, mainSplit.width - 240)

            hostWindow: window
            hostController: controller
            hostToolbar: toolbar
            hostBackupHost: backupHost
            hostFileOpsDialogs: fileOpsDialogs
            hostCollectionPasswordDialog: collectionPasswordDialog
            hostFileOpsController: typeof fileOpsController !== "undefined"
                ? fileOpsController : null
            hostFaceScanController: typeof faceScanController !== "undefined"
                ? faceScanController : null
            hostFolderHierarchyController: typeof folderHierarchyController !== "undefined"
                ? folderHierarchyController : null
        }

        MainLibraryCanvas {
            id: mainLibraryCanvas
            hostWindow: window
            hostController: controller
            hostToolbar: toolbar
            hostSearchSuggestionsBox: searchSuggestionsBox
            hostBackupHost: backupHost
            hostRightDrawerHandle: jobbFiokFogo
            hostPeoplePanel: peoplePanel
        }

    }

    MainRightDrawer {
        id: jobbFiok
        hostWindow: window
        hostController: controller
        hostToolbar: toolbar
        hostPhotoViewer: photoViewer
        hostMainSplit: mainSplit
        hostMainLibraryCanvas: mainLibraryCanvas
        hostMainDialogs: mainDialogs
        propertiesLabel: qsTr("Properties")
        tagsLabel: qsTr("Tags:")
        peopleLabel: qsTr("People")
        placesLabel: qsTr("Places")
    }

    //: #3035: `m_fakehidden` (`thumbui.tre:696`) — NEM LÁTSZÓ, de
    //: kattintható sáv a fiók szélén, ami billenti a fiókot. Csukott
    //: fióknál is ott van: ez a MÁSIK belépési pont a Nézet menü mellett.
    Rectangle {
        id: jobbFiokFogo
        objectName: "toggle_right_drawer"
        //: a `kattints()` a próbáké is: a vezérlőre kattintunk, nem a
        //: kezelő metódusát hívjuk
        function kattints() { window.billentsdAFiokot() }
        visible: mainSplit.visible
        opacity: 0
        width: 6
        anchors.top: mainSplit.top
        anchors.bottom: mainSplit.bottom
        anchors.right: jobbFiok.visible ? jobbFiok.left : parent.right
        color: "transparent"
        TapHandler { onTapped: jobbFiokFogo.kattints() }
    }

    // #985: a Kollázs LAP tartalma — a Könyvtár lapjának TESTVÉRE, ugyanazon
    // a helyen. Az eredetiben a `panelroot/collagetab` a `panelroot/picasatab`
    // testvére, tehát a kollázs a mappapanellel EGYÜTT váltja le a könyvtárat
    // (`picasa-kollazs-felulet.md` 8.: a „Továbbiak..." visszavált a
    // `picasatab`-ra). A panel a saját bal hasábját hozza magával.
    // #1612: a panel az induláskor NEM látszik (külön dokumentum-lap), a
    // komponensenkénti mérés szerint viszont 74,5 ms-ba kerül. Ezért
    // `Loader` mögött él: az ELSŐ megnyitásig nem jön létre, utána viszont
    // MEGMARAD (`betoltve` ragadós) — a félkész kollázs nem veszhet el egy
    // fülváltáson. A `visible` feltétel változatlan, csak a betöltőre került.
    Loader {
        id: collagePanelLoader
        objectName: "collagePanelLoader"
        anchors.top: documentTabStrip.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        readonly property bool kellene: !window.viewerOpen && !window.timelineOpen
                 && documentTabStrip.activeTabId === window.collageTabId
        property bool betoltve: false
        onKelleneChanged: if (kellene) betoltve = true
        active: kellene || betoltve
        visible: kellene
        sourceComponent: collagePanelKomponens
    }

    Component {
        id: collagePanelKomponens

        CollagePanel {
            id: collagePanel
            // az álnév a kötési hurkot kerüli ki (ld. `appController`)
            controller: window.appController
            librarySelection: window.selectedIndexes

            // #1028: a mentés VÉGE — a panel jelez, a navigáció a gazdáé
            onCollageSaved: function(path) { window.locateSavedCollage(path) }

            // spec 4.3/13.: a panel csak JELEZ, a fülváltás a gazdáé
            onGetMoreClipsRequested: {
                window.backToCollagePrompted = true
                documentTabStrip.activateTab(documentTabStrip.libraryTabId)
            }
        }
    }

    // #1001: a „Megjelenítés és szerkesztés" FOGADÓJA. A parancs három
    // helyről indul (a `CollageRandomRow` gombja, a `CollageNode`
    // duplakattintása és a `CollageContextMenus` tétele), de mind a három a
    // vezérlő `viewAndEditSelection()`-jébe fut, tehát EGY fogadó elég — és
    // egy is kell, mert a lapváltás meg a néző a gazdáé, nem a panelé.
    Connections {
        target: controller
        function onCollageEditRequested(path) {
            window.openCollageNodeInEditor(path)
        }
    }

    // #1939: a „Vissza a kollázshoz" visszaútja AZ ALSÓ SÁVBA került
    // (`TrayBar.qml` → `traySingleActionBar`), mert az eredetiben a
    // „Továbbiak…" után egy teljes üzenetsáv ül a vezérlőkészletben
    // (`thumbui/single_action_container`), nem egy lebegő gomb a jobb
    // felső sarokban. A visszatérés MŰVELETE változatlan — csak a
    // felülete került a helyére; a kezelő lent, a `TrayBar`-on.
    //
    // Ezért NINCS itt `backToCollageButton`: ne tegye vissza egy későbbi
    // kör „hiányzó gombként", mert akkor két vezérlő kínálná ugyanazt.

    // #209: lebegő „Importálás" folyamat-panel — jobb oldalt lebeg, húzható;
    // a néző felett is látszik (a szkennelés közben is lehet dolgozni),
    // csak a diavetítés (z:100) takarja
    ImportProgressPanel {
        id: importPanel
        objectName: "importProgressPanel"
        z: 90
        // #305/#1572: null-őr
        visible: (controller && controller.importPanelVisible !== undefined)
            ? controller.importPanelVisible : false
        folderName: controller ? controller.importFolderName : ""
        doneCount: controller ? controller.importDoneCount : 0
        totalCount: controller ? controller.importTotalCount : 0
        newCount: controller ? controller.importNewCount : 0
        onCloseRequested: controller.dismissImportPanel()
        // induló hely: jobb felül, a kereső alatt; húzáskor a DragHandler
        // felülírja a kötést — a panel ott marad, ahova a felhasználó tette
        x: parent.width - width - 24
        y: 56
    }

    // #2966: KÖZÖS háttérművelet-jelző a jobb-felső sarokban. Alapból
    // rejtve; bármelyik, a közös nyilvántartásba bejelentkezett háttérmunka
    // futásakor magától megjelenik (`controller.isWorking`), és ha a munka
    // leállítható, a gombja is (`controller.activityCancellable`).
    ActivityBadge {
        id: activityBadge
        objectName: "activityBadge"
        z: 95
        // #305/#1572: null-őr — a controller a betöltés alatt lehet null
        working: (controller && controller.isWorking !== undefined)
            ? controller.isWorking : false
        cancellable: (controller && controller.activityCancellable !== undefined)
            ? controller.activityCancellable : false
        // a mért hely: felülről 5, jobbról 5 képpont (#3112)
        x: parent.width - width - 5
        y: 5
        onCancelRequested: activityCancelConfirm.ask()
    }

    //: #2966: a megszakítás megerősítése. Az eredeti címsora „Want to
    //: Cancel?" volt — azt NEM vesszük át, a miénk a műveletről szól.
    //: #1719/#1720: halasztott példányosítás — a párbeszéd csak az első
    //: megszakítás-kattintáskor épül fel.
    DeferredDialog {
        id: activityCancelConfirm
        objectName: "activityCancelConfirmLoader"
        anchors.fill: parent
        function ask() {
            //: a `decisionKey` SZÁNDÉKOSAN üres: a futó munka leállítását
            //: nem lehet „ne kérdezze újra"-val elnyomni
            //: `IBackgroundNotify::cancel` — az eredeti szövege (#3573)
            ensure().ask("", qsTr(
                "Do you want to cancel this operation?"))
        }
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "activityCancelConfirm"
                namePrefix: "activityCancel"
                //: `IBackgroundNotify::canceltitle` — az eredeti szövege (#3573)
                title: qsTr("Want to Cancel?")
                onConfirmed: controller.cancelActivity()
            }
        }
    }

    //: #4634: halasztott (#1720) — csak az Eszközök menüpontra épül fel.
    DeferredDialog {
        id: xmpFacesWriteDialog
        objectName: "xmpFacesWriteDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            XmpFacesWriteDialog {
                onWriteRequested: function (scope, rows) {
                    if (controller) controller.writeFacesToXmp(scope, rows)
                }
            }
        }
    }

    // #425: lebegő „Csoportos szerkesztés" folyamat-panel — az
    // ImportProgressPanel mintájára, Mégse gombbal (megszakítható köteg)
    //: #1403: az XMP-arcírás folyamat-panelje — MEGSZAKÍTHATÓ, ahogy az
    //: eredeti kötegelt munkája (`FaceTagJob::cancelled`). A már kiírt
    //: sidecarok érvényesek maradnak.
    XmpFacesProgressPanel {
        id: xmpFacesPanel
        objectName: "xmpFacesProgressPanel"
        z: 90
        visible: (controller && controller.xmpFacesActive !== undefined)
            ? controller.xmpFacesActive : false
        folderName: controller ? controller.currentFolder : ""
        doneCount: controller ? controller.xmpFacesDone : 0
        totalCount: controller ? controller.xmpFacesTotal : 0
        onCancelRequested: controller.cancelXmpFaces()
        x: parent.width - width - 24
        y: 56
    }

    BatchEditProgressPanel {
        id: batchEditPanel
        objectName: "batchEditProgressPanel"
        z: 90
        visible: (controller && controller.batchEditActive !== undefined)
            ? controller.batchEditActive : false
        folderName: controller ? controller.batchEditFolderName : ""
        doneCount: controller ? controller.batchEditDoneCount : 0
        totalCount: controller ? controller.batchEditTotalCount : 0
        onCancelRequested: controller.cancelBatchEdit()
        x: parent.width - width - 24
        y: 56 + importPanel.height + 12
    }

    // #1527/#5268: a mentés és a fájl-visszaállítás közös folyamatjelzője.
    // Mindkét művelet háttérszálon fut; a szöveg az eredeti hivatalos,
    // műveletfüggő alakja, mentéskor a százalék egy tizedesjegyre.
    SaveProgressPanel {
        id: saveProgressPanel
        objectName: "saveProgressPanel"
        z: 90
        visible: (controller && controller.saveProgressActive !== undefined)
            ? controller.saveProgressActive : false
        fileCount: controller ? controller.saveProgressFileCount : 0
        percent: controller ? controller.saveProgressPercent : 0
        isReverting: controller ? controller.saveProgressIsReverting : false
        x: parent.width - width - 24
        y: 56 + importPanel.height + batchEditPanel.height + 24
    }

    // #211: lebegő „Teljesítmény-monitor" panel — a Súgó menüből
    // kapcsolható; balra az importálás-paneltől, hogy ne fedjék egymást
    PerfMonitorPanel {
        id: perfPanel
        objectName: "perfMonitorPanel"
        z: 90
        // #305/#1572: null-őr
        visible: (controller && controller.perfMonitorEnabled !== undefined)
            ? controller.perfMonitorEnabled : false
        cpuPercent: controller ? controller.perfCpuPercent : 0
        rssMb: controller ? controller.perfRssMb : 0
        topActivity: controller ? controller.perfTopActivity : ""
        onCloseRequested: controller.setPerfMonitorEnabled(false)
        onSaveRequested: perfPanel.lastSavedPath = controller.saveDiagnostics()
        x: 24
        y: 56
    }

    // #237: kép/mappa ablakra ejtése → a kép mappája figyelt gyökér lesz
    // (ImportDropArea → dropImportController). Egér-eseményt nem fog el;
    // z:95 — a lebegő panelek (90) fölött, a diavetítés (100) alatt, hogy
    // a visszajelzés-buborék látsszon
    ImportDropArea {
        objectName: "importDropArea"
        anchors.fill: parent
        z: 95
    }

    MainErrorBanner {
        id: mainErrorBanner
        hostController: controller
        hostTestLogDialog: tesztuzemNaploDialog
        hostBrokenPhotoDialog: brokenPhotoDialog
        hostBrokenPhotoBatchTimer: brokenPhotoBatchTimer
    }

    //: #1403: az arc elnevezése után AUTOMATIKUS XMP-írás hibája. A jelzés a
    //: `faceScanController`-é (nem a `facesHelper`-é), és az eredetiben is
    //: megnevezett hibaeset (csak olvasható fájl) — a névadás maga sikeres
    //: volt, csak az XMP nem, ezért nem nyeljük el.
    Connections {
        target: window._faceScanController
        function onUnnamedCountChanged() { window.peopleFaceRevision++ }
        // #4586: a keresés közben is frissül a panel névtelen-arc listája —
        // összevonva, és csak nyitott panel mellett
        function onFacesStored() {
            if (window.peoplePanelOpen || photoViewer.peopleOpen)
                { if (!unnamedFaceRefreshTimer.running) unnamedFaceRefreshTimer.start() }
        }
        function onFaceSuggestionsChanged() { window._javaslatFrissult() }
        function onXmpAutoWriteFailed(reason) {
            errorBanner.notice = false
            errorBannerText.text = qsTr("Face data could not be written to XMP: %1").arg(reason)
        }
    }
    Connections {
        target: typeof facesHelper !== "undefined" ? facesHelper : null
        function onFaceWriteFailed(message) {
            errorBanner.notice = false
            errorBannerText.text = message
        }

    }

    // #459: sérült/betölthetetlen kép — ELREJTÉS felajánlása (nem törlés),
    // a felhasználó döntésével. A "Hide Files" a MEGLÉVŐ elrejtés-úton fut
    // (`controller.hidePhotosByIds` → `_apply_batch`, a `toggleHiddenRows`
    // mintája, `photo_ops_controller.py`) — itt NEM íródott újra.
    //: #1612: halasztva — a sérült kép elrejtés-felajánlása csak akkor kell, ha tényleg akad ilyen kép
    DeferredDialog {
        id: brokenPhotoDialog
        //: a BUROK neve — a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "brokenPhotoDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                //: a BELSŐ példány saját neve: a `brokenPhotoDialog` a
                //: halasztó `Loader`, tehát a saját mezőire innen NEM azon
                //: a néven kell hivatkozni (az `ensure()` visszatérése ez az
                //: objektum)
                id: brokenPhotoBelso
                namePrefix: "brokenPhoto"
                yesText: qsTr("Hide Files")
                noText: qsTr("Don't Hide")
                property var pendingIds: []
                //: #3573: a nevek az üzenet fájllistájához (a `pendingIds`
                //: párja, ugyanabban a sorrendben)
                property var pendingNames: []
                onConfirmed: {
                    controller.hidePhotosByIds(brokenPhotoBelso.pendingIds)
                    brokenPhotoBelso.pendingIds = []
                    brokenPhotoBelso.pendingNames = []
                }
                onDenied: {
                    brokenPhotoBelso.pendingIds = []
                    brokenPhotoBelso.pendingNames = []
                }
            }
        }
    }

    Timer {
        id: brokenPhotoBatchTimer
        interval: 400
        onTriggered: {
            if (brokenPhotoDialog.ensure().pendingIds.length > 0) {
                // #3573: az eredeti KÉT erőforrásból rakja össze az
                // üzenetet, és a kettő közé soronként a hibás fájlok nevét
                // szúrja be (`GetBadImages` + lista + `GetBadImages2`)
                var dialog = brokenPhotoDialog.ensure()
                dialog.ask("",
                    //: `CThumbUI::GetBadImages` — utána a fájllista jön
                    qsTr("PicasaPy had a problem loading this file(s)\n")
                    + dialog.pendingNames.join("\n")
                    //: `CThumbUI::GetBadImages2`
                    + qsTr("\nWould you like to hide the files on disk?"))
            }
        }
    }

    //: #3503: „Létrehozás ▸ Ajándék CD készítése…" — a kiadás-panel
    //: Ajándék-CD üzemmódja a könyvtár ALJÁN (az eredetiben is ott ül).
    //: Csak a könyvtár lapján látszik, ugyanazzal a feltétellel, mint a
    //: könyvtár maga.
    GiftCdHost {
        id: giftCdHost
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        appController: controller
        fileOps: typeof fileOpsController !== "undefined" ? fileOpsController : null
        visible: nyitva && !window.viewerOpen && !window.timelineOpen
                 && window.libraryFrameVisible
        //: #3504: a kiadás-panel EGYSZERRE egy üzemmódban látszik — az
        //: Ajándék-CD nyitása becsukja a mentést (az eredetiben is egy sáv
        //: vált módot, `biztonsagi-mentes.md` 10.)
        onNyitvaChanged: if (nyitva) backupHost.nyitva = false
    }

    //: #3504: „Eszközök ▸ Képek biztonsági mentése…" — a kiadás-panel
    //: mentés-üzemmódja, ugyanúgy a könyvtár alján, mint az Ajándék-CD.
    BackupHost {
        id: backupHost
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: nyitva && !window.viewerOpen && !window.timelineOpen
                 && window.libraryFrameVisible
        //: #3751: a rács-szűrő csak a panel melletti könyvtár-rácsra hat —
        //: keresésben, időrendben, más lapon a teljes lista látszik
        racsLatszik: visible && !(controller && controller.searchActive)
        nezoNyitva: window.viewerOpen || window.slideshowRunning
        //: a mentés nyitása becsukja az Ajándék-CD-t (ld. fent)
        onNyitvaChanged: if (nyitva) giftCdHost.nyitva = false
    }

    // alsó sáv: infó-sáv + kijelölés-tálca (TrayBar.qml, #150)
    footer: TrayBar {
        id: trayBar
        objectName: "trayBar"
        width: parent ? parent.width : 0
        // #1026: az alsó tálca- és kimeneti sáv a KÖNYVTÁR panelének
        // gyereke (`thumbui/bottombevel_base` + `outputlayout.tre`), tehát a
        // projekt-lapon a panellel együtt tűnik el — a felszabaduló sávot a
        // vászon kapja meg.
        visible: window.libraryFrameVisible && !window.quickViewerLaunch
        appWindow: window
        onPhotosDroppedOnTray: function(rows) {
            if (controller && rows && rows.length > 0)
                controller.holdRows(rows)
        }
        // #4637: a testreszabható alsó kimeneti gombsor közös helyi menüje.
        onConfigureButtonsContextMenuRequested: function(anchorItem, x, y) {
            window.openConfigureButtonsContextMenu(anchorItem, x, y)
        }
        //: #3756: a `currentIndex` MINDIG a jobb/alsó félé (ld.
        //: `PhotoViewer.qml` `photo` `source`-a) — kettős nézetben bal
        //: fókusznál a sávnak a KIJELÖLT (`aktivSor`) képet kell mutatnia.
        viewerIndex: photoViewer.aktivSor
        // #2564: a szerkesztő nagyítás-hármasa az ALSÓ SÁVBAN ül (mérve),
        // de a nagyítás állapota a nézőé — az állapot ide jön, a művelet
        // jelzésként megy vissza. Enélkül a tálcának ismernie kellene a
        // néző belsejét.
        viewerZoomValue: photoViewer.zoomValue
        viewerZoomAvailable: window.viewerOpen && photoViewer.photoOverlaysUsable
        onZoomFitRequested: photoViewer.zoomFit()
        onZoomActualRequested: photoViewer.zoomActual()
        onZoomValueRequested: (ertek) => photoViewer.setZoomValue(ertek)
        onExportRequested: exportDialogs.ensure().openForSelection()
        // #1917: a tálca helyi menüjének öt ÖRÖKÖLT tétele. Ugyanazokra a
        // vezérlőkre megy, mint a rács helyi menüjének párja — a tálca
        // kijelölésén, mert a menü a tálcára hat.
        //: #2163: EGY belépő — a `Ctrl+3` ugyanezt a függvényt hívja.
        onViewAndEditRequested: window.nezdEsSzerkeszd()
        onTrayRotateRightRequested: controller.rotateRightMany(window.selectedRows())
        onTrayRotateLeftRequested: controller.rotateLeftMany(window.selectedRows())
        onTrayLocateRequested: {
            var sorok = window.selectedRows()
            if (sorok.length === 0) return
            var ut = controller.photos.filePathAt(sorok[0])
            if (ut.length > 0) fileOpsController.revealPhoto(ut)
        }
        onTrayPropertiesRequested: window.valtsFiokLapot("properties")
        // #1472: a tálca „Nyomtatás" gombja — a jelzésnek eddig SEHOL nem
        // volt kezelője, a gomb kattintható volt, és nem történt semmi
        onPrintRequested: window.openPrint()
        // #361: kollázs/film a tálca ikonjairól is; #985: a kollázs innen is
        // a LAPOT nyitja (spec 3.2) — egy belépési út, nem kettő
        onCollageRequested: window.openCollageTab()
        onMovieRequested: createDialogs.ensure().openMovie()
        //: #1939: a klip-gyűjtő mód üzenetsávjának „Vissza" gombja. A
        //: MŰVELET ugyanaz, ami korábban a lebegő gombé volt: a mód
        //: jelzője lekerül, és a projekt lapja lesz az aktív.
        onBackToCollageRequested: {
            window.backToCollagePrompted = false
            documentTabStrip.activateTab(window.collageTabId)
        }
        onBackToMovieMakerRequested: window.returnToMovieMaker()
        // #1798: a tálca „E-Mail" gombja engedélyezve volt és kattintható,
        // a jelzését viszont SEHOL nem fogta el senki — a testvérei
        // (Kollázs, Exportálás, Nyomtatás) mind be voltak kötve. Ez volt a
        // valódi oka annak, hogy a Beállítások e-mail-módja némának
        // látszott: az egész küldési út néma volt.
        onEmailRequested: window.sendSelectionByEmail()
        onAddSelectedToScreensaverRequested: window.requestAddToScreensaver()
        onStarSelectedPhotosRequested: {
            if (controller)
                controller.toggleStarMany(window.photoActionRows())
        }
        onNewAlbumWithSelectionRequested: {
            fileOpsDialogs.ensure().openNewAlbumProperties(
                controller ? controller.currentFolder : "",
                window.photoActionRows())
        }
    }

    // -- fájlműveletek (#15): kontextusmenü + dialógusok --------------------

    PhotoContextMenu {
        id: photoContextMenu
        // #1613: a lemezt CSAK a menü megnyitásakor kérdezzük meg — egy
        // kötés minden képkockán fájlrendszert olvasna.
        onAboutToShow: {
            var ut = controller
                ? controller.photos.filePathAt(window.fileOpTargetRow) : ""
            photoContextMenu.hasOriginalOnDisk =
                ut.length > 0 && fileOpsController.hasOriginalOnDisk(ut)
            // #3468: a „Keresés" almenü csak EGY kijelölt képnél jelenik meg
            var db = window.selectedRows().length
            photoContextMenu.kijeloltKepekSzama = db > 0 ? db : 1
            photoContextMenu.peopleThumbnailFaceAvailable = controller
                ? controller.canSetPersonThumbnail(
                    Number(controller.photos.idAt(window.fileOpTargetRow)),
                    controller.currentPersonName)
                : false
            // #5195: a „Társítás ▸" almenü listája a megnyitáskor készül
            photoContextMenu.nativeOpenWith = fileOpsController.hasNativeOpenWith()
            photoContextMenu.openWithApps = ut.length > 0
                ? fileOpsController.openWithChoices(ut) : []
        }
        // #17: pipa, ha a jobbklikkelt kép rejtett (photos.revision-nel
        // együtt kötve, hogy a menü újranyitáskor friss legyen)
        // #305: null-őr
        hideChecked: controller
            ? (controller.photos.revision,
               (controller.photos.itemAt(window.fileOpTargetRow)
                    .hidden === true))
            : false
        // #422: a mentés-parancsok aktív állapota — a jobbklikkelt képen
        // van-e szerkesztés, illetve van-e mentés-előtti másolat
        hasEdits: controller
            ? (controller.photos.revision,
               (controller.photos.itemAt(window.fileOpTargetRow)
                    .hasEdits === true))
            : false
        hasBackup: controller
            ? controller.hasSavedBackup(window.selectedRows()) : false
        onSaveRequested: saveDialogs.ensure().openSave(window.selectedRows())
        onRevertRequested: saveDialogs.ensure().openRevert(window.selectedRows())
        onUndoAllEditsRequested: mainDialogs.undoAllEditsDialog.ensure().openForLibrary(
            window.selectedRows())
        onResetFacesRequested: resetFacesForPaths(window.selectedPaths())
        onHideToggleRequested: window.toggleHiddenSelection()
        onMoveRequested: fileOpsDialogs.ensure().openMove(window.selectedPaths())
        onDeleteRequested: fileOpsDialogs.ensure().openDelete(window.selectedPaths())
        onLocateRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length > 0) fileOpsController.revealPhoto(p)
        }
        // #1613: a „Keresés" almenü két új tétele.
        //
        // A `hasOriginalOnDisk` a menü MEGNYITÁSAKOR kérdez rá a lemezre
        // (`fileOpTargetRow` változásakor) — kötésben nem tehetnénk, mert
        // az minden képkockán fájlrendszert kérdezne.
        onLocateOriginalRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length > 0) fileOpsController.revealOriginal(p)
        }
        // az eredeti `IDS_LOCATE_SOURCE_IMAGE`: a kép VALÓDI mappájára ugrik
        // (album-/Emberek-nézetből, ahol a kép nem a saját mappájában látszik)
        onLocateInPicasaRequested: {
            var p = controller.photos.filePathAt(window.fileOpTargetRow)
            if (p.length === 0) return
            var mappa = p.substring(0, p.lastIndexOf("/"))
            if (mappa.length === 0) return
            toolbar.clearSearch()
            window.clearSelection()
            window.unnamedFacesOpen = false
            controller.selectFolder(mappa)
        }
        // #422 (2. lépcső): az eredeti AlbumPhoto-menü többi parancsa
        onOpenRequested: {
            window.openPhotoViewer(window.fileOpTargetRow)
        }
        onRotateRightRequested: controller.rotateRightMany(window.selectedRows())
        onRotateLeftRequested: controller.rotateLeftMany(window.selectedRows())
        onOpenFileRequested: {
            var target = controller.photos.filePathAt(window.fileOpTargetRow)
            if (target.length > 0) fileOpsController.openPhoto(target)
        }
        // #5195: a „Társítás ▸" almenü egy alkalmazása megnyitja a képet
        onOpenWithAppRequested: function(appId) {
            var target = controller.photos.filePathAt(window.fileOpTargetRow)
            if (target.length > 0) fileOpsController.openWithApp(target, appId)
        }
        // #4533: Társítás… — Windowson a héj saját párbeszéde, Linuxon a mi választónk
        onOpenWithRequested: {
            var target = controller.photos.filePathAt(window.fileOpTargetRow)
            if (target.length === 0) return
            if (fileOpsController.hasNativeOpenWith())
                fileOpsController.openWithNative(target)
            else
                openWithDialog.ensure().openFor(target)
        }
        onCopyFullPathRequested: {
            var full = controller.photos.filePathAt(window.fileOpTargetRow)
            if (full.length > 0) fileOpsController.copyFullPath(full)
        }
        onPropertiesRequested: window.valtsFiokLapot("properties")
        // #9 (2. lépés): albumtagság — #305 null-őr
        albums: controller ? controller.albums : []
        currentAlbumToken: controller ? controller.currentAlbumToken : ""
        currentFolder: controller ? controller.currentFolder : ""
        onSplitFolderRequested: window.splitFolderHere()
        onAddToAlbumRequested: function(token) {
            if (controller) controller.addRowsToAlbum(window.selectedRows(), token)
        }
        // #3539: megerősítéssel — a "Remove from album without
        // confirmation" beállítással elnyomható (`removeFromAlbumDialog`)
        onRemoveFromAlbumRequested: {
            if (controller) removeFromAlbumDialog.ensure().openFor(
                window.selectedRows(), controller.currentAlbumToken)
        }
        onNewAlbumRequested: fileOpsDialogs.ensure().openNewAlbum(window.selectedRows())
        // #422 4. lépcső: az Emberek-album kép-szintű parancsai. A tételek
        // csak személy-albumban látszanak (üres `personName` = rejtve).
        personName: controller ? controller.currentPersonName : ""
        people: controller ? controller.people : []
        onRemoveFromPeopleAlbumRequested: {
            if (controller) removePeopleFacesDialog.ensure().openFor(
                window.selectedRows(), controller.currentPersonName)
        }
        // #3464: a „Hozzáadás az Emberek albumhoz" almenü egy meglévő
        // személyére kattintva a kijelölt képeken az arc ÁTKERÜL hozzá
        onMoveToPersonRequested: function (name) {
            if (controller) controller.movePersonOnRows(
                window.selectedRows(), controller.currentPersonName, name)
        }
        onMoveToNewPersonRequested: {
            if (controller) moveToNewPersonDialog.ensure().openFor(
                window.selectedRows(), controller.currentPersonName)
        }
        onSetPeopleAlbumThumbnailRequested: {
            if (controller && controller.setPersonThumbnail(
                    Number(controller.photos.idAt(window.fileOpTargetRow)),
                    controller.currentPersonName))
                window.peopleFaceRevision++
        }
    }

    // #3539: „Eltávolítás az albumból" — a kijelölt képek albumtagságát
    // veszi le, megerősítéssel (a "Remove from album without confirmation"
    // beállítással elnyomható, a #367 törlés-elnyomás mintája szerint).
    //: #1612: halasztva — a megerősítés csak a menüpontból/billentyűből nyílik
    DeferredDialog {
        id: removeFromAlbumDialog
        objectName: "removeFromAlbumDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "removeFromAlbumDialog"
                namePrefix: "removeFromAlbum"
                //: DeleteMessage::RemoveItemsTitle (spec picasa-fen-dialogs.md 3.3.1)
                title: qsTr("Remove Items")
                property var rows: []
                property string token: ""
                function openFor(rowList, albumToken) {
                    if (rowList.length === 0 || albumToken.length === 0) return
                    rows = rowList
                    token = albumToken
                    if (rowList.length <= 1) {
                        //: DeleteMessage::RemoveSingleYesButton
                        yesText = qsTr("Remove Image")
                        //: DeleteMessage::RemoveSingle
                        ask("removeFromAlbum", qsTr(
                            "Are you sure you want to remove the selected "
                            + "image from the current album?"))
                    } else {
                        //: DeleteMessage::RemoveMultipleYesButton
                        yesText = qsTr("Remove Images")
                        //: DeleteMessage::RemoveMultiple
                        ask("removeFromAlbum", qsTr(
                            "Are you sure you want to remove the %n selected "
                            + "images from the current album?", "",
                            rowList.length))
                    }
                }
                onConfirmed: controller.removeRowsFromAlbum(rows, token)
            }
        }
    }

    // #422: „Eltávolítás az Emberek albumból" — a kijelölt képekről leveszi
    // az ADOTT személy arc-címkéjét (a régió is eltűnik: a Picasa is az
    // arcot veszi le, nem csak a nevet). Megerősítéssel: a névcímke
    // visszaállítása csak újbóli felismeréssel/kézi felvétellel lehetséges.
    // #3539: a cím és a szöveg a `DeleteMessage::` család szerint (spec
    // 3.3.1) — a korábbi saját "arc-címke" szöveg helyett.
    //: #1612: halasztva — az arcok eltávolításának megerősítése csak a menüpontból nyílik
    DeferredDialog {
        id: removePeopleFacesDialog
        //: a BUROK neve — a #1612 őre ezen hívja az `ensure()`-t, és
        //: ezzel bizonyítja, hogy induláskor tényleg nincs példány
        objectName: "removePeopleFacesDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "removePeopleFacesDialog"
                namePrefix: "removePeopleFaces"
                //: DeleteMessage::UnknownPeopleTitle (a fajta=2 ágon, tárolón kívül)
                title: qsTr("Remove People")
                property var rows: []
                property string person: ""
                function openFor(rowList, name) {
                    if (rowList.length === 0 || name.length === 0) return
                    rows = rowList
                    person = name
                    if (rowList.length <= 1) {
                        //: DeleteMessage::RemoveSingleYesButtonPeople
                        yesText = qsTr("Remove Person")
                        //: DeleteMessage::RemoveSinglePeople
                        ask("removePeopleFaces", qsTr(
                            "Are you sure you want to remove the selected "
                            + "person from the current album?"))
                    } else {
                        //: DeleteMessage::RemoveMultipleYesButtonPeople
                        yesText = qsTr("Remove People")
                        //: DeleteMessage::RemoveMultiplePeople
                        ask("removePeopleFaces", qsTr(
                            "Are you sure you want to remove the %n selected "
                            + "people from the current album?", "",
                            rowList.length))
                    }
                }
                onConfirmed: controller.removePersonFromRows(rows, person)
            }
        }
    }

    // #422: „Áthelyezés új személyhez…" — az adott személy arc-címkéje a
    // kijelölt képeken ÁTKERÜL egy másik névre (a régió marad).
    //: #1612: halasztva — az „Áthelyezés új személyhez" csak az arcpanel
    //: helyi menüjéből nyílik. Az `objectName` a BELSŐ párbeszédre marad,
    //: hogy a felépülés után ugyanúgy megtalálható legyen.
    DeferredDialog {
        id: moveToNewPersonDialog
        sourceComponent: Component {
            NameInputDialog {
                objectName: "moveToNewPersonDialog"
                title: qsTr("Move to New Person")
                prompt: qsTr("New person's name:")
                property var rows: []
                property string person: ""
                function openFor(rowList, name) {
                    if (rowList.length === 0 || name.length === 0) return
                    rows = rowList
                    person = name
                    openEmpty()
                }
                onAccepted: controller.movePersonOnRows(rows, person, enteredName)
            }
        }
    }

    // #449: első indítás — a kérdés az ablak megjelenése UTÁN jön elő, hogy
    // a felhasználó lássa, mibe kerül bele
    InitialScanDialog {
        id: initialScanDialog
        objectName: "initialScanDialog"
        // #1167: a migrációs „frissítés" ág a meglévő Picasa-átvételt
        // nyitja (#146) — a felderítést a PicasaImportDialog végzi újra
        onImportRequested: {
            if (typeof discoveryController !== "undefined" && discoveryController)
                discoveryController.openImportDialog()
        }
    }

    // #5704: ugyanaz a jelszókezelő szolgálja ki a felhasználói és a
    // beépített Rejtett mappák gyűjteményt. Hibás jelszónál a párbeszéd
    // nyitva marad, így a felhasználó azonnal újrapróbálhatja.
    DeferredDialog {
        id: collectionPasswordDialog
        anchors.fill: parent
        sourceComponent: Component {
            CollectionPasswordDialog {
                controller: window.appController
            }
        }
    }

    // #5704 (spec #5700): ajánlat a Rejtett mappák védelmére elrejtés után.
    DeferredDialog {
        id: hiddenPasswordOfferDialog
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                namePrefix: "hiddenPasswordOffer"
                title: qsTr("Add Password")
                message: qsTr("The \"Hidden Folders\" collection is not currently password protected.\nWould you like to add a password now?")
                yesText: qsTr("Add Password")
                noText: qsTr("Don't Add Password")
                rememberText: qsTr("Do not ask me again.")
                rememberOnDenied: true
                onConfirmed:
                    collectionPasswordDialog.ensure().openForHiddenCollection()
            }
        }
    }
    Connections {
        target: controller
        function onHiddenPasswordOfferRequested() {
            hiddenPasswordOfferDialog.ensure().ask(
                "DoNotConfirmHiddenPwd",
                qsTr("The \"Hidden Folders\" collection is not currently password protected.\nWould you like to add a password now?"))
        }
    }

    // #1051: a kollázs-piszkozat visszaállításának felajánlása. A LAPRA
    // váltás a gazdáé — a párbeszéd csak jelez, ahogy a `CollagePanel` is.

    CollageDraftDialog {
        id: collageDraftDialog
        onRestored: documentTabStrip.activateTab(window.collageTabId)
    }

    // #1129: a lebegő értesítősáv (Picasa Notifier) — önálló, keret nélküli
    // ablak a munkaterület jobb alsó részén. Az alkalmazás indítása hozza
    // létre, nem a főablak, ezért nincs `transientParent`-je.
    //
    // A `NotifierBus.attached` kapun át a `CollageDoneNotice` MAGÁTÓL
    // elhallgat, amint a sáv jelen van — így ugyanaz az esemény nem szólal
    // meg kétszer, két helyen. A `CollageDoneNotice` SZÁNDÉKOSAN marad a
    // fában: a #1119 őre a jelenlétét állítja, és a törlése önálló döntés
    // (a sáv nélküli üzemmód tartaléka).
    PicasaNotifier {
        id: picasaNotifier
        onActivated: function (kind, payload) {
            if (kind === "collage")
                window.openCollageNodeInEditor(payload)
        }
    }

    // #1028: „A kollázs kész (kattintson ide)" — a lapzárás UTÁN is látszik,
    // ezért a gazdában él, nem a panelben, ami közben bezárul.
    CollageDoneNotice {
        id: collageDoneNotice
        z: 100
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        onClicked: {
            var cel = collageDoneNotice.path
            collageDoneNotice.dismiss()
            window.openCollageNodeInEditor(cel)
        }
    }

    // #444: Mentés / Visszaállítás / Utolsó mentés visszavonása
    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: saveDialogs
        // ⚠️ Az `objectName` a BECSOMAGOLT párbeszédé marad, nem a
        // `Loader`-é: a `findChild(objectName)` így a megnyitás után a
        // VALÓDI komponenst adja vissza, nem a burkot.
        objectName: "saveDialogsLoader"
        anchors.fill: parent
        sourceComponent: Component {
            SaveDialogs { objectName: "saveDialogs"; appWindow: window }
        }
    }

    // átnevezés / áthelyezés / törlés / hiba (FileOpsDialogs.qml, #150)
    //: #1612: halasztva — a fájlművelet-párbeszédek 571 QObjectet építettek
    //: fel MINDEN induláskor, holott a legtöbb indulásnál egyet sem nyit meg
    //: a felhasználó. A vezérlő jelzéseit a lenti, MINDIG álló `Connections`
    //: fogadja, nem a komponens belseje (#1743, #2096).
    DeferredDialog {
        id: fileOpsDialogs
        objectName: "fileOpsDialogs"
        anchors.fill: parent
        sourceComponent: Component {
            //: a BELSŐ példány saját neve — a burok (`fileOpsDialogs`) a
            //: `Loader`, a párbeszédeket tartó `Item` ez. A tesztek az
            //: `ensure()` után ezen a néven érik el a nyilvános belépőket.
            FileOpsDialogs {
                objectName: "fileOpsDialogsItem"
                appWindow: window
            }
        }
    }

    //: #1612: a fájlművelet-vezérlő hallgatói. Azért ITT állnak és nem a
    //: komponensben, mert az halasztott: a `fileOpsController` jelzései nem
    //: csak a saját párbeszédeiből indulhatnak — a mappafa
    //: áthelyezés/törlés útja (`FolderPane.qml`) is ezen jelez. Az
    //: `ensure()` mindhárom ágon KÖTELEZŐ: mind a három a FELHASZNÁLÓNAK
    //: szól, tehát némán elmaradnia nem szabad.
    Connections {
        target: fileOpsController
        function onBatchProgress(operation, destination, done, total, speed) {
            fileOpsDialogs.ensure().reportBatch(
                operation, destination, done, total, speed)
        }
        function onBatchFinished(operation, done, skipped, failed, reason) {
            fileOpsDialogs.ensure().finishBatch(
                operation, done, skipped, failed, reason)
        }
        function onOperationFailed(operation, message) {
            fileOpsDialogs.ensure().showOperationError(operation, message)
        }
    }

    // exportálás mappába (#16, Ctrl+Shift+S; ExportDialogs.qml, #150)
    // #1720: halasztott példányosítás — a párbeszéd csak az első
    // megnyitáskor épül fel (ld. `DeferredDialog.qml`).
    DeferredDialog {
        id: exportDialogs
        anchors.fill: parent
        sourceComponent: Component {
            ExportDialogs { appWindow: window }
        }
    }

    // #1743: A HALLGATÓK MINDIG ÁLLNAK, a párbeszéd nem.
    //
    // A #1720 óta a mentés- és export-párbeszéd halasztott: csak az első
    // megnyitáskor épül fel. A vezérlő eredmény- és hibajelzéseit viszont
    // EDDIG a párbeszéden BELÜLI `Connections` fogadta — ami addig nem is
    // létezett. Amíg minden belépő az `ensure()`-ön át megy, ez nem okoz
    // bajt; egy ÚJ belépő (gyorsbillentyű, tálcagomb, kötegelt művelet)
    // viszont némán elnyelné a hibaüzenetet, és semmilyen teszt nem bukna
    // el rá.
    //
    // Ezért a hallgató ide került, a mindig felépülő ablakba: pár objektum,
    // a #1720 nyeresége érintetlen. Az `ensure()` a jelzés pillanatában
    // építi fel a párbeszédet — pontosan akkor, amikor tényleg kell.
    Connections {
        target: controller
        function onDiskOperationSucceededPaths(paths) {
            photoViewer.frissitsdALemezműveletUtániElőnézetet(paths)
        }
        function onSaveFailedDetails(details) {
            saveDialogs.ensure().jelezdAbukottMentest(details)
        }
        function onSaveErrorOccurred(kind, fileName, code) {
            saveDialogs.ensure().jelezdAmentesiHibat(kind, fileName, code)
        }
        function onRevertErrorOccurred() {
            saveDialogs.ensure().jelezdAVisszaallitasiHibat()
        }
        function onExportFailedDetails(details) {
            exportDialogs.ensure().jegyezdAbukottFajlokat(details)
        }
        function onExportFinished(done, failed) {
            exportDialogs.ensure().jelezdAzExportVeget(done, failed)
        }
        function onEarthExportFinished(kmlPath, placemarks, skipped) {
            exportDialogs.ensure().jelezdAzEarthExportVeget(
                kmlPath, placemarks, skipped)
        }
        function onEarthViewReady(kmlPath, placemarks, skipped) {
            exportDialogs.ensure().nyisdMegAzEarthFajlt(
                kmlPath, placemarks, skipped)
        }
    }

    // kollázs és mozgófilm a kijelölésből (#29; CreateDialogs.qml)
    //: #1612/#2096: halasztva — a Létrehozás-párbeszédek csak a menüből vagy
    //: a tálcáról nyílnak. A vezérlő jelzéseit a lenti, MINDIG álló
    //: `Connections` fogadja, nem a komponens belseje (#1743).
    DeferredDialog {
        id: createDialogs
        objectName: "createDialogs"
        // A belső Dialogok ehhez a felülethez igazodnak; méret nélkül a Loader 0×0 marad.
        anchors.fill: parent
        sourceComponent: Component {
            CreateDialogs { appWindow: window }
        }
    }

    // #2096: a Létrehozás-párbeszédek vezérlő-hallgatói. Azért ITT állnak és
    // nem a komponensben, mert az halasztott: amíg a felhasználó meg nem
    // nyitotta, egy belső `Connections` nem létezne, és a kollázs/film
    // visszajelzése NÉMÁN elmaradna. A kollázs a Kollázs panelről is
    // indítható, tehát ez nem elméleti eset.
    Connections {
        target: controller
        function onCollagePreviewReady(revision) {
            // ⚠️ Itt SZÁNDÉKOSAN nincs `ensure()`. Az élő előnézet csak a
            // NYITOTT kollázs-párbeszédnek szól: ha a párbeszéd nem áll, nincs
            // mit frissíteni, és felépíteni is fölösleges volna. A többi
            // jelzés (eredmény, hiba) viszont a felhasználónak szól, ott az
            // `ensure()` KÖTELEZŐ — különben némán elmaradna a visszajelzés.
            if (createDialogs.item)
                createDialogs.item.frissitsdAzElonezetet(revision)
        }
        function onMovieTransitionPreviewReady(source, generation) {
            // Mint a kollázs-előnézet: csak a NYITOTT párbeszédnek szól,
            // felépíteni fölösleges (nincs film-előnézet, ha nem áll).
            if (createDialogs.item)
                createDialogs.item.jelezdAFilmAtmenetElonezetet(source, generation)
        }
        function onCollageFinished(path, used, skipped, missing) {
            createDialogs.ensure().jelezdAKollazsSikert(path, used, skipped, missing)
        }
        function onCollagePreviewFailed(message) {
            // Az előnézet a háttérből a főablak lebontása közben is bukhat;
            // akkor már nincs párbeszéd, amelyben jelezni lehetne.
            const parbeszedek = createDialogs.ensure()
            if (parbeszedek)
                parbeszedek.jelezdAKollazsHibajat(message)
        }
        function onCollageFailed(message) {
            createDialogs.ensure().jelezdAKollazsHibajat(message)
        }
        function onMovieProgress(done, total) {
            createDialogs.ensure().frissitsdAFilmHaladast(done, total)
        }
        function onMovieFinished(path, used, skipped, missing) {
            createDialogs.ensure().jelezdAFilmSikert(path, used, skipped, missing)
        }
        function onMovieFailed(message) {
            createDialogs.ensure().jelezdAFilmHibajat(message)
        }
        function onPosterFinished(paths) {
            createDialogs.ensure().jelezdAPoszterSikert(paths)
        }
        function onPosterFailed(message) {
            createDialogs.ensure().jelezdAPoszterHibajat(message)
        }
    }

    // #2054: a felhasználói súgó — F1. Halasztott, mint a többi:
    // induláskor nem épül fel, csak az első megnyitáskor.
    DeferredDialog {
        id: helpDialog
        anchors.fill: parent
        sourceComponent: Component { HelpDialog { objectName: "helpDialog" } }
    }

    //: #1792: a fejlec gombsoranak testreszabasa — halasztott toltes, a
    //: tobbi parbeszed mintajara (a nev a BECSOMAGOLT parbeszede)
    DeferredDialog {
        id: configureButtonsDialog
        anchors.fill: parent
        sourceComponent: Component {
            ConfigureButtonsDialog { objectName: "configureButtonsDialog" }
        }
    }

    DeferredDialog {
        id: aboutDialog
        anchors.fill: parent
        // az `objectName` a BECSOMAGOLT párbeszédé — enélkül a #1720
        // őre üres halmazt vizsgálna, azaz némán mindig zöld lenne
        sourceComponent: Component { AboutDialog { objectName: "aboutDialog" } }
    }

    // #350: Beállítások-dialógus (options.fen)
    DeferredDialog {
        id: optionsDialog
        anchors.fill: parent
        sourceComponent: Component { OptionsDialog { } }
    }

    // #351: webexport-dialógus (.tpl sablonmotor)
    DeferredDialog {
        id: webExportDialog
        anchors.fill: parent
        sourceComponent: Component { WebExportDialog { } }
    }

    // #1472: nyomtatás-párbeszéd (nyomtató-választó + PDF-fájlba nyomtatás)
    DeferredDialog {
        id: printDialog
        anchors.fill: parent
        sourceComponent: Component { PrintDialog { } }
    }

    // #368: adatbázis-áthelyezés dialógus (relocateController hídon)
    DeferredDialog {
        id: moveDatabaseDialog
        anchors.fill: parent
        sourceComponent: Component { MoveDatabaseDialog { } }
    }
    // #644: figyelmeztetés, ha egy másik program felülírta a szerkesztéseinket
    DeferredDialog {
        id: editOverwriteDialog
        anchors.fill: parent
        sourceComponent: Component { EditOverwriteDialog { } }
    }
    Connections {
        target: controller
        function onEditsOverwritten(lost) { editOverwriteDialog.ensure().show(lost) }
    }
    DeferredDialog {
        id: compactDatabaseDialog
        anchors.fill: parent
        sourceComponent: Component { CompactDatabaseDialog { } }
    }
    // #1401: az Útlevélkép hibaablaka — a főablak tartalmában, tehát
    // fölötte látszik. Egy arcnál párbeszéd nélkül a MEGLÉVŐ nyomtatási
    // nézet nyílik (élő mérés, picasa-colab-jobs #54).
    DeferredDialog {
        id: passportErrorDialog
        anchors.fill: parent
        sourceComponent: Component { PassportErrorDialog { } }
    }
    Connections {
        target: typeof passportController !== "undefined" ? passportController : null
        function onPassportNoFace() {
            passportErrorDialog.ensure().showError("noFace")
        }
        function onPassportMultipleFaces() {
            passportErrorDialog.ensure().showError("multipleFaces")
        }
        function onPassportFailed(kind) {
            passportErrorDialog.ensure().showError(kind)
        }
        function onPassportReady(url) {
            printDialog.ensure().openForPassport(url)
        }
    }
    // #3132: a db3-import párbeszéde — ritkán nyitott, ezért halasztott
    DeferredDialog {
        id: picasaDataImportDialog
        anchors.fill: parent
        sourceComponent: Component { PicasaDataImportDialog { } }
    }

    // Indítóképernyő (#189): a legfelső rétegen ül, a startupStatus hídból
    // kapja az állapotot, és ready-re magától kifakul/eltűnik.
    // A kötés defenzív: híd (context property) nélkül — pl. célzott
    // tesztkörnyezetben — a splash készre áll, azaz rejtve marad.
    SplashScreen {
        readonly property var statusBridge:
            typeof startupStatus !== "undefined" ? startupStatus : null
        anchors.fill: parent
        z: 10000
        version: appVersion
        statusText: statusBridge ? statusBridge.statusText : ""
        ready: statusBridge ? statusBridge.ready : true
        // #243: félkész-figyelmeztetés + OK a betöltés végén, amíg az
        // effekt-paritás nem teljes (a kapcsoló az application.py-ban él)
        confirmationRequired:
            statusBridge ? statusBridge.requiresConfirmation : false
    }
}

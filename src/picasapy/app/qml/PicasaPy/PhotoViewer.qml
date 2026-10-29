import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import PicasaPy.Gpu
import "aranykenyszer.js" as AranyKenyszer

// Egyképes néző — a Picasa 3.9 "Megjelenítés és szerkesztés" képernyője
// alapján (#808080 háttér, felső filmszalag nyilakkal, bal eszközpanel;
// a szerkesztő-gombok a 2. fázisig szürkék). Enter/Jobbra: következő,
// Balra: előző, Esc: vissza a könyvtárba.
Rectangle {
    id: viewer

    // #4639: a főablak súgója közvetlenül ezekből a bekötött
    // Shortcut.sequence értékekből olvassa a néző és a kiegyenesítő sáv
    // billentyűit.
    readonly property var keyboardShortcutSequences: [
        viewerEditWorkflow.drawerShortcutSequence
    ].concat(editorToolBar.keyboardShortcutSequences)

    readonly property bool textEntryHasFocus:
        viewer.Window.window !== null
        && viewer.Window.window.activeFocusItem !== null
        && viewer.Window.window.activeFocusItem.selectedText !== undefined
    //: #3463: a Shift+F1 fejezete (ld. `Main.qml` `helpTopicUnderCursor`)
    property string helpTopic: "features/nezegetes.md"

    // #1816: látszik-e a felirat-sáv. A GYÖKÉREN áll, mert a sáv és a
    // „Make a caption!" helyőrző két külön szülő alatt él.
    // A `!== undefined` a #1572-őr mintája: a próbák stub-vezérlőjén a
    // tulajdonság hiányozhat.
    readonly property bool captionVisible:
        (controller && controller.captionVisible !== undefined)
            ? controller.captionVisible : true

    function billentsdAFeliratot() {
        if (controller && controller.toggleCaptionVisible !== undefined)
            controller.toggleCaptionVisible()
    }

    readonly property string currentFilePath:
        viewerState.currentFilePath
    readonly property bool controllerReady: viewerState.controllerReady
    readonly property bool singleClickExitEnabled:
        viewerState.singleClickExitEnabled
    readonly property bool currentIsCollageDraft: viewerState.currentIsCollageDraft
    readonly property bool currentIsSavedCollage: viewerState.currentIsSavedCollage
    readonly property bool currentIsSavedMovie: viewerState.currentIsSavedMovie
    readonly property real panelPreferredHeight:
        viewerState.panelPreferredHeight
    readonly property real minimumUsableHeight:
        viewerState.minimumUsableHeight
    readonly property var hostWindow: viewer.Window.window
    readonly property real windowChromeHeight: viewerState.windowChromeHeight
    readonly property real windowDecorationAllowance:
        viewerState.windowDecorationAllowance
    property alias screenHeightBudget: viewerState.screenHeightBudget
    readonly property real requiredHeight: viewerState.requiredHeight
    color: Theme.viewerBg

    property alias photosModel: viewerState.photosModel
    readonly property var editCtl: viewerState.editCtl
    readonly property var masodikEditCtl: viewerState.masodikEditCtl

    // GPU élő-előnézet (#22): a finetune-csúszkák AKTÍV húzása alatt igaz —
    // az EditorPanel finetunePreview→finetuneCommit életciklusa keretezi
    // (ld. lent, az editorPanel bekötésénél). `gpuFinetuneEligible` a
    // KÉT feltétel: (a) a futtatókörnyezet RHI-alapú grafikai kontextust
    // ad (GPU-képtelen — pl. CI offscreen/software — környezetben ez
    // MINDIG false, néma és biztonságos fallback a rendes CPU-útra), és
    // (b) a jelenlegi szerkesztési lánc GPU-alkalmas
    // (`EditController.gpuPrefixSource` nem üres — ld. ott a feltételt).
    property alias gpuFinetuneActive: viewerState.gpuFinetuneActive
    property alias gpuFinetunePointSafe: viewerState.gpuFinetunePointSafe
    property alias editorControlsVisible: viewerState.editorControlsVisible
    readonly property bool uiTransitionsEnabled:
        viewerState.uiTransitionsEnabled
    property alias editorDrawerOffset: viewerState.editorDrawerOffset
    readonly property bool editorDrawerAnimationRunning:
        viewerState.editorDrawerAnimationRunning
    function toggleEditorDrawer() { return viewerEditWorkflow.toggleEditorDrawer() }

    readonly property bool gpuCapable: GraphicsInfo.api !== GraphicsInfo.Software
                                        && GraphicsInfo.api !== GraphicsInfo.Unknown
                                        && GraphicsInfo.api !== GraphicsInfo.Null
    readonly property bool gpuFinetuneEligible: viewer.gpuCapable
        && viewer.editCtl && viewer.editCtl.gpuPrefixSource !== ""

    property alias currentIndex: viewerState.currentIndex
    // #4698: Ctrl+F9 az eredeti Picasában a nézőt folyamatosan lépteti.
    // A Timer minden betöltött kép után, a következő eseményciklusban hívja
    // a szokásos `next()` utat. A jelző megkülönbözteti ezt a lépést a kézi
    // lapozástól, amely leállítja az időzítőt.
    Timer {
        id: ctrlF9AutoAdvanceTimer
        objectName: "ctrlF9AutoAdvanceTimer"
        interval: 1
        repeat: true
        onTriggered: {
            if (!viewer.visible) {
                stop()
                return
            }
            // Csak akkor váltunk, ha az aktuális kép már betöltődött. Így a
            // 0/1 ms-os eseményközi ütemezés nem ugorja át a képkockákat.
            if (viewer.isCurrentVideo
                    ? videoLoader.status === Loader.Loading
                    : photo.status === Image.Loading)
                return
            if (!viewer.hasNext()) {
                stop()
                return
            }
            viewer.ctrlF9AutoStep = true
            viewer.next()
            viewer.ctrlF9AutoStep = false
        }
    }
    property alias ctrlF9AutoStep: viewerState.ctrlF9AutoStep
    function stopCtrlF9AutoAdvance() { return viewerNavigation.stopCtrlF9AutoAdvance() }
    function startCtrlF9AutoAdvance() { return viewerNavigation.startCtrlF9AutoAdvance() }
    property alias photoCount: viewerState.photoCount
    readonly property bool isCurrentVideo: viewerState.isCurrentVideo
    signal closed()
    // #8: a felső ▶ Lejátszás gomb — diavetítés az aktuális képtől
    signal playRequested()
    signal starRequested(int row)
    signal rotateRequested(int row, int delta)
    //: #1002: a megnyitott kollázs újranyitása SZERKESZTÉSRE. A néző
    //: csak JELEZ — a lapváltás és a panel feltöltése a gazdáé.
    signal editCollageRequested(string path)
    //: #2114: a film forrásprojektjének újranyitása
    signal editMovieRequested(string path)
    // #422/#4621: a néző törlés-parancsa (Ctrl+Delete és a helyi menü
    // tétele) — a nézetfüggő elágazás (lemezről törlés vagy eltávolítás az
    // albumból) és a megerősítők a Main.qml-ben élnek, ezért a kérés
    // jelként megy kifelé; a célt (az aktív kép sorát) a gazda adja
    signal deleteRequested()
    // #4621: albumból megnyitott képen a törlés-parancs az albumból
    // eltávolít — a helyi menü felirata ezt mutatja (a gazda köti)
    property bool deleteRemovesFromAlbum: false
    // #422: a mentés-szemantika parancsai a nézőből — a gazda (Main.qml)
    // ugyanazokat a megerősítéseket nyitja, mint a rácsban
    signal saveRequested(int row)
    signal revertRequested(int row)
    signal undoAllEditsRequested(int row)
    signal resetFacesRequested()
    //: #2566: a Helyek-panel két művelete a nézőből is a GAZDA
    //: megerősítésén megy át — ugyanazok a párbeszédek, mint a
    //: könyvtár-nézetben (`panelClearGeotagDialog`, `setGeotagDialog`).
    signal clearGeotagRequested(var rows)
    signal setGeotagRequested(var rows, real latitude, real longitude)
    signal dropGeotagRequested(var rows, real latitude, real longitude)
    signal manualFaceAddCancelRequested()
    //: #2566: a fiók két KIVEZETŐ parancsa. Mindkettő a könyvtár tartalmát
    //: cseréli le (keresés, illetve személy-album), amit a néző eltakarna —
    //: ezért nem a néző hajtja végre, hanem a gazda: az zárja a nézőt, és
    //: utána vált nézetet.
    signal findTaggedRequested(string keyword)
    signal personChosen(string name)

    // #192: a Tulajdonságok-panel a nézőben is — a könyvtár-nézet közös
    // kapcsolóját (Main.qml: window.propertiesPanelOpen) követi. A fő
    // ablakot a Window attached property adja, így a (forró) Main.qml-hez
    // nem kell hozzányúlni; önálló (teszt-)példányosításnál a kapcsoló
    // hiányzik → a panel rejtve marad.
    readonly property var appWindow: Window.window
    readonly property bool quickViewerMode: viewerState.quickViewerMode
    // A Picasa Web Albums feltöltése kivezetett funkció; a gomb csak
    // képességjelzésként jelenik meg, ezért a kezelőfelület nem aktiválhatja.
    readonly property bool quickUploadAvailable:
        viewerState.quickUploadAvailable
    readonly property bool propertiesOpen: viewerState.propertiesOpen
    readonly property bool tagsOpen: viewerState.tagsOpen
    readonly property bool placesOpen: viewerState.placesOpen
    readonly property bool peopleOpen: viewerState.peopleOpen
    readonly property var drawerRows: viewerState.drawerRows
    property alias facesVisible: viewerState.facesVisible
    function toggleFaces() { return viewerState.toggleFaces() }
    property alias facesEditMode: viewerState.facesEditMode
    function beginManualFaceAdd() { return viewerState.beginManualFaceAdd() }
    function cancelManualFaceAdd() { return viewerState.cancelManualFaceAdd() }
    function toggleFacesEdit() { return viewerState.toggleFacesEdit() }
    property alias facesEditRevision: viewerState.facesEditRevision
    property alias manualFaceAddRevision: viewerState.manualFaceAddRevision
    readonly property var currentFaces: viewerState.currentFaces
    readonly property bool hasDetectedFaceHitTargets:
        viewerState.hasDetectedFaceHitTargets

    // -- zoom-állapotgép (#6, #2492): fit / 1:1 / tetszőleges ------------
    //
    // ⚠️ #2492: az igazságforrás a NORMALIZÁLT csúszka-érték (`zoomValue`,
    // [0, 1]), nem a szorzó. Ez az eredeti Picasa mért működése
    // (`docs/specs/ui-audit-editor.md`, „A szerkesztő NAGYÍTÁS-HÁRMASA"):
    // a `FUN_005d1c70` a csúszka értékéből választja ki, melyik gomb az
    // aktív, `0.0` = illesztés és `0.5` = valódi méret. Korábban nálunk a
    // csúszka a SZORZÓT tárolta lineárisan (0,25…8), ezért az „1:1" nem
    // a felezőpontra esett — a tulajdonos ezt jelentette (v0.8.293).
    //
    // zoomValue: 0 = illesztés, 0,5 = valódi méret (100 %), 1 = 400 %.
    property real zoomValue: 0

    // A tálca nagyítás-csúszkája közvetlenül a fenti `zoomValue`-ból kapja
    // az értéket (`Main.qml` → `TrayBar.viewerZoomValue`). Az új komponensek
    // nyilvános aliasait csak ezután deklaráljuk, hogy a gyökér állapotforrása
    // készüljön el előbb a komponenshatáron átvezetett kötések előtt.
    property alias editorPanel: viewerLayout.editorPanel
    property alias cropOverlay: viewerLayout.cropOverlay
    property alias editorToolBar: viewerLayout.editorToolBar
    property alias effectColorPickArea: viewerLayout.effectColorPickArea
    property alias facesOverlay: viewerLayout.facesOverlay
    property alias gpuPrefixImage: viewerLayout.gpuPrefixImage
    property alias kepkockaJelzes: viewerLayout.kepkockaJelzes
    property alias neutralPickArea: viewerLayout.neutralPickArea
    property alias paintMaskArea: viewerLayout.paintMaskArea
    property alias photo: viewerLayout.photo
    property alias photoElotte: viewerLayout.photoElotte
    property alias photoElotteKeret: viewerLayout.photoElotteKeret
    property alias photoKeret: viewerLayout.photoKeret
    property alias redeyeDragArea: viewerLayout.redeyeDragArea
    property alias retouchClickArea: viewerLayout.retouchClickArea
    property alias textClickArea: viewerLayout.textClickArea
    property alias videoLoader: viewerLayout.videoLoader

    property alias layoutMode: viewerState.layoutMode
    property alias aktivOldal: viewerState.aktivOldal
    property alias fuggolegesElrendezes: viewerState.fuggolegesElrendezes
    property alias masodikIndex: viewerState.masodikIndex
    readonly property int aktivSor: viewerState.aktivSor
    readonly property bool balFokusz: viewerState.balFokusz
    readonly property int jelvenySzel: viewerState.jelvenySzel
    readonly property int jelvenyMag: viewerState.jelvenyMag
    readonly property int jelvenyParhuzamosRes: viewerState.jelvenyParhuzamosRes
    readonly property int jelvenyMerolegesRes: viewerState.jelvenyMerolegesRes
    readonly property int jelvenyHelyFent: viewerState.jelvenyHelyFent
    readonly property int jelvenyHelyBal: viewerState.jelvenyHelyBal

    // A fotó geometriai és nagyítási állapota.
    readonly property int texturaEl: viewerGeometry.texturaEl
    readonly property int abMasikSor: viewerGeometry.abMasikSor
    readonly property real zoomFactor: viewerGeometry.zoomFactor
    property alias zoomNavigatorDismissed: viewerGeometry.zoomNavigatorDismissed
    readonly property string zoomMode: viewerGeometry.zoomMode
    property alias panX: viewerGeometry.panX
    property alias panY: viewerGeometry.panY
    readonly property bool photoOverlaysUsable: viewerGeometry.photoOverlaysUsable
    readonly property real zoomDetent: viewerGeometry.zoomDetent
    readonly property rect zoomNavigatorViewRect: viewerGeometry.zoomNavigatorViewRect
    readonly property var forceFitFilters: viewerGeometry.forceFitFilters
    readonly property int valodiSzelesseg: viewerGeometry.valodiSzelesseg

    function illesztesiDoboz(keretSzel, keretMag, arany) { return viewerGeometry.illesztesiDoboz(keretSzel, keretMag, arany) }
    function forrasMeret(index, url) { return viewerGeometry.forrasMeret(index, url) }
    function _betoltesekIrasa() { return viewerGeometry._betoltesekIrasa() }
    function _betolt(kep, par) { return viewerGeometry._betolt(kep, par) }
    function _par(sor, url) { return viewerGeometry._par(sor, url) }
    function _videoE() { return viewerGeometry._videoE() }
    function _photoPar(sor) { return viewerGeometry._photoPar(sor) }
    function _elotoltoPar(irany) { return viewerGeometry._elotoltoPar(irany) }
    function _abMasikSort() { return viewerGeometry._abMasikSort() }
    function forceFitForFilter(filterName) { return viewerGeometry.forceFitForFilter(filterName) }
    function actualZoomFactor() { return viewerGeometry.actualZoomFactor() }
    function skalaErtekbol(v) { return viewerGeometry.skalaErtekbol(v) }
    function setZoomValue(v) { return viewerGeometry.setZoomValue(v) }
    function zoomFit() { return viewerGeometry.zoomFit() }
    function zoomActual() { return viewerGeometry.zoomActual() }
    function lepjZoom(delta) { return viewerGeometry.lepjZoom(delta) }
    function wheelZoom(delta) { return viewerGeometry.wheelZoom(delta) }
    function clampPan() { return viewerGeometry.clampPan() }
    function panFromZoomNavigator(deltaX, deltaY) { return viewerGeometry.panFromZoomNavigator(deltaX, deltaY) }
    function show(index) { return viewerGeometry.show(index) }
    function selectMenuEffect(name) { return viewerGeometry.selectMenuEffect(name) }
    function applyCrop(advance) { return viewerGeometry.applyCrop(advance) }

    PhotoViewerGeometryActions {
        id: viewerGeometry
        hostViewer: viewer
        hostPhotoArea: viewerLayout.photoArea
        hostEditController: viewer.editCtl
        nextPreloadImage: viewerLayout.overlayControls.nextPreloadImage
        previousPreloadImage: viewerLayout.overlayControls.previousPreloadImage
    }

    readonly property int masodikSor: viewerEditWorkflow.masodikSor
    property alias aaMunkamenet: viewerEditWorkflow.aaMunkamenet
    property alias aaKiindulas: viewerEditWorkflow.aaKiindulas
    property alias aaFotoId: viewerEditWorkflow.aaFotoId
    property alias aaFolytatas: viewerEditWorkflow.aaFolytatas
    property alias aaKerdesFut: viewerEditWorkflow.aaKerdesFut
    property alias endEditFolytatas: viewerEditWorkflow.endEditFolytatas
    property alias cropNyitaskoriKijeloles:
        viewerEditWorkflow.cropNyitaskoriKijeloles
    property alias tiltSzinkronFut: viewerEditWorkflow.tiltSzinkronFut
    property alias tiltAlkalmazasFut: viewerEditWorkflow.tiltAlkalmazasFut
    property alias tiltErtekNyitaskor: viewerEditWorkflow.tiltErtekNyitaskor

    function _kijeloltSort() { return viewerEditWorkflow._kijeloltSort() }
    function _masodikSort() { return viewerEditWorkflow._masodikSort() }
    function frissitsdAMasodikSzerkesztest() { return viewerEditWorkflow.frissitsdAMasodikSzerkesztest() }
    function frissitsdALemezműveletUtániElőnézetet(utvonalak) { return viewerEditWorkflow.frissitsdALemezműveletUtániElőnézetet(utvonalak) }
    function _cropKijeloles() { return viewerEditWorkflow._cropKijeloles() }
    function _cropNyitaskoriMegjegyez() { return viewerEditWorkflow._cropNyitaskoriMegjegyez() }
    function _cropModosult() { return viewerEditWorkflow._cropModosult() }
    function _aaFelLanca(fel) { return viewerEditWorkflow._aaFelLanca(fel) }
    function _aaAktivFel() { return viewerEditWorkflow._aaAktivFel() }
    function _aaDontes(neKerdezzen) { return viewerEditWorkflow._aaDontes(neKerdezzen) }
    function _aaMegtart(fel) { return viewerEditWorkflow._aaMegtart(fel) }
    function _aaLezaras() { return viewerEditWorkflow._aaLezaras() }
    function _aaNeKerdezzen() { return viewerEditWorkflow._aaNeKerdezzen() }
    function aaKilepesKapu(folytatas) { return viewerEditWorkflow.aaKilepesKapu(folytatas) }
    function _nyitottEszkozModosult() { return viewerEditWorkflow._nyitottEszkozModosult() }
    function _nyitottEszkozLezar(alkalmaz) { return viewerEditWorkflow._nyitottEszkozLezar(alkalmaz) }
    function _eszkozZarasKapu(folytatas, megseEngedve) { return viewerEditWorkflow._eszkozZarasKapu(folytatas, megseEngedve) }
    function modotValt(uj) { return viewerEditWorkflow.modotValt(uj) }
    function _modotValtEszkozUtan(uj) { return viewerEditWorkflow._modotValtEszkozUtan(uj) }
    function fokuszValt(uj) { return viewerEditWorkflow.fokuszValt(uj) }
    function _aaLapozasKapu() { return viewerEditWorkflow._aaLapozasKapu() }
    function kerBezaras() { return viewerEditWorkflow.kerBezaras() }
    function _aaFeleketCserel() { return viewerEditWorkflow._aaFeleketCserel() }
    function beginEditCurrent() { return viewerEditWorkflow.beginEditCurrent() }
    function syncTiltSlider() { return viewerEditWorkflow.syncTiltSlider() }
    function syncPanelFromController() { return viewerEditWorkflow.syncPanelFromController() }

    PhotoViewerEditWorkflow {
        id: viewerEditWorkflow
        hostViewer: viewer
        hostEditController: viewer.editCtl
    }

    property alias wheelAccum: viewerNavigation.wheelAccum
    function next() { return viewerNavigation.next() }
    function previous() { return viewerNavigation.previous() }
    function _vanSzomszed(sor, irany) { return viewerNavigation._vanSzomszed(sor, irany) }
    function hasNext() { return viewerNavigation.hasNext() }
    function hasPrevious() { return viewerNavigation.hasPrevious() }
    function wheelStep(delta) { return viewerNavigation.wheelStep(delta) }
    function urlAt(index) { return viewerNavigation.urlAt(index) }
    function preloadUrlAt(index) { return viewerNavigation.preloadUrlAt(index) }
    function handleReturnPressed() { return viewerNavigation.handleReturnPressed() }
    PhotoViewerNavigation {
        id: viewerNavigation
        hostViewer: viewer
        hostAutoAdvanceTimer: ctrlF9AutoAdvanceTimer
    }

    focus: visible
    Keys.forwardTo: [viewerKeyboard]
    function handleEscape() { return viewerKeyboard.handleEscape() }
    PhotoViewerKeyboard {
        id: viewerKeyboard
        hostViewer: viewer
    }

    PhotoViewerLayout {
        id: viewerLayout
        hostViewer: viewer
        hostContextActions: viewerContextActions
    }

    PhotoViewerQuickToolbar {
        hostViewer: viewer
    }

    readonly property string currentPath: viewerContextActions.currentPath

    function zarjaAFiokot() { viewerContextActions.zarjaAFiokot() }
    function _aktivUt() { return viewerContextActions._aktivUt() }
    function openContextMenu(x, y) {
        viewerContextActions.openContextMenu(x, y)
    }

    PhotoViewerContextActions {
        id: viewerContextActions
        hostViewer: viewer
    }

    PhotoViewerState {
        id: viewerState
        hostViewer: viewer
        hostController: typeof controller !== "undefined" ? controller : null
        hostEditController:
            typeof editController !== "undefined" ? editController : null
        hostSecondPreview:
            typeof secondPreview !== "undefined" ? secondPreview : null
        hostTopBar: viewerLayout.topBar
        hostEditorPanel: viewer.editorPanel
        hostWindow: viewer.hostWindow
        hostAppWindow: viewer.appWindow
        hostFacesHelper: typeof facesHelper !== "undefined" ? facesHelper : null
        hostFilmstrip: viewerLayout.filmstrip
        hostAutoAdvanceTimer: ctrlF9AutoAdvanceTimer
        hostScreenHeight: Screen.desktopAvailableHeight
    }

}

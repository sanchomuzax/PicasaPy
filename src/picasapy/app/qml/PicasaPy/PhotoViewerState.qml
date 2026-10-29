import QtQuick
import QtQml

// A PhotoViewer nyilvános állapotának belső gazdája. A gyökér a publikus
// tulajdonságokat aliasokon át továbbra is közvetlenül adja ki.
QtObject {
    id: viewerState

    property var hostViewer: null
    property var hostController: null
    property var hostEditController: null
    property var hostSecondPreview: null
    property var hostTopBar: null
    property var hostEditorPanel: null
    property var hostWindow: null
    property var hostAppWindow: null
    property var hostFacesHelper: null
    property var hostFilmstrip: null
    property var hostAutoAdvanceTimer: null
    property real hostScreenHeight: 0

    readonly property string currentFilePath:
        (viewerState.currentIndex >= 0 && viewerState.photosModel !== null)
            ? viewerState.photosModel.filePathAt(viewerState.currentIndex) : ""
    readonly property bool controllerReady:
        viewerState.hostController ? true : false
    readonly property bool singleClickExitEnabled:
        viewerState.controllerReady
            && viewerState.hostController.singleClickExitEnabled !== undefined
            ? viewerState.hostController.singleClickExitEnabled : false
    readonly property bool currentIsCollageDraft: {
        if (!viewerState.controllerReady
                || viewerState.currentFilePath.length === 0)
            return false
        return viewerState.hostController.collageSavedPath !== undefined
               && viewerState.hostController.isCollageDraft(
                   viewerState.currentFilePath) === true
    }
    readonly property bool currentIsSavedCollage: {
        if (!viewerState.controllerReady
                || viewerState.currentFilePath.length === 0)
            return false
        return viewerState.hostController.collageSavedPath !== undefined
               && viewerState.hostController.hasCollageProject(
                   viewerState.currentFilePath) === true
    }
    readonly property bool currentIsSavedMovie: {
        if (!viewerState.controllerReady
                || viewerState.currentFilePath.length === 0)
            return false
        return viewerState.hostController.hasMovieProject !== undefined
               && viewerState.hostController.hasMovieProject(
                   viewerState.currentFilePath) === true
    }

    readonly property real panelPreferredHeight:
        viewerState.hostTopBar.height + viewerState.hostEditorPanel.implicitHeight
    readonly property real minimumUsableHeight:
        viewerState.hostTopBar.height + viewerState.hostEditorPanel.chromeHeight
    readonly property real windowChromeHeight: {
        var w = viewerState.hostWindow
        if (!w) return 0
        var extra = 0
        if (w.menuBar) extra += w.menuBar.height
        if (w.header) extra += w.header.height
        if (w.footer) extra += w.footer.height
        return extra
    }
    readonly property real windowDecorationAllowance: 56
    property real screenHeightBudget:
        viewerState.hostScreenHeight - viewerState.windowChromeHeight
        - viewerState.windowDecorationAllowance
    readonly property real requiredHeight:
        Math.min(viewerState.panelPreferredHeight,
                 Math.max(viewerState.minimumUsableHeight,
                          viewerState.screenHeightBudget))

    property var photosModel: null
    readonly property var editCtl: viewerState.hostEditController
    readonly property var masodikEditCtl: viewerState.hostSecondPreview
    property bool gpuFinetuneActive: false
    property bool gpuFinetunePointSafe: true
    property bool editorControlsVisible:
        (viewerState.controllerReady
         && viewerState.hostController.editorControlsVisible !== undefined)
        ? viewerState.hostController.editorControlsVisible : true
    readonly property bool uiTransitionsEnabled:
        !viewerState.controllerReady
        || viewerState.hostController.uiTransitionsEnabled === undefined
            ? true : viewerState.hostController.uiTransitionsEnabled
    property real editorDrawerOffset:
        viewerState.editorControlsVisible ? 0 : -279
    readonly property bool editorDrawerAnimationRunning:
        editorDrawerOffsetAnimation.running
    Behavior on editorDrawerOffset {
        enabled: viewerState.uiTransitionsEnabled
        NumberAnimation {
            id: editorDrawerOffsetAnimation
            objectName: "viewerEditorDrawerAnimation"
            duration: 250
            easing.type: Easing.InOutQuad
        }
    }

    property int currentIndex: -1
    property bool ctrlF9AutoStep: false
    property int photoCount: viewerState.hostFilmstrip
        ? viewerState.hostFilmstrip.count : 0
    readonly property bool isCurrentVideo: viewerState.photosModel
        ? (viewerState.photosModel.revision,
           viewerState.photosModel.isVideoAt(viewerState.currentIndex)) === true
        : false
    //: #3013: a KETTŐS NÉZET üzemmódja — editpanel/layout_2up_group.
    //: "1up" (alapértelmezés), "aa" (ugyanaz a kép kétszer, két önálló
    //: szerkesztéssel — #3014), "ab" (két különböző kép). Váltani a
    //: modotValt()-tal kell.
    property string layoutMode: "1up"
    //: melyik oldal az aktív — a „Kijelölve" jelvény ezt mutatja.
    //: #3773: az eredeti Picasában 2-up módba lépéskor a BAL a kijelölt,
    //: mérve a Colab EN 33 referencia-képen.
    property string aktivOldal: "bal"
    //: swap_2up_layout: a két kép egymás MELLETT (hamis) vagy egymás
    //: ALATT (igaz); az ütközés-párbeszéd feliratai is ezen múlnak.
    property bool fuggolegesElrendezes: false
    property int masodikIndex: -1
    onMasodikIndexChanged: {
        if (viewerState.hostAutoAdvanceTimer.running
                && !viewerState.ctrlF9AutoStep)
            viewerState.hostViewer.stopCtrlF9AutoAdvance()
    }
    //: A kijelölt oldal rács-sora. Egy képes módban mindig a jelenlegi kép;
    //: kettős nézetben a fókuszált fél. Imperatív kezelőben a kötés helyett
    //: _kijeloltSort()-ot kell olvasni (#218, #3187).
    readonly property int aktivSor:
        (viewerState.layoutMode !== "1up"
         && viewerState.aktivOldal === "jobb")
            ? viewerState.hostViewer.abMasikSor : viewerState.currentIndex
    //: A kijelölt kép a BAL/FELSŐ félen áll (photoElotte). Egy képes
    //: módban mindig hamis.
    readonly property bool balFokusz: viewerState.layoutMode !== "1up"
        && viewerState.aktivOldal === "bal"
    //: A „Kijelölve" jelvény mért mérete és a képtől tartott rése
    //: (Colab EN 33, 1280×1024; #3663, #3756).
    readonly property int jelvenySzel: 86
    readonly property int jelvenyMag: 26
    readonly property int jelvenyParhuzamosRes: 61
    readonly property int jelvenyMerolegesRes: 27
    readonly property int jelvenyHelyFent: viewerState.layoutMode !== "1up"
        && !viewerState.fuggolegesElrendezes
        ? viewerState.jelvenyMag + viewerState.jelvenyMerolegesRes : 0
    readonly property int jelvenyHelyBal: viewerState.layoutMode !== "1up"
        && viewerState.fuggolegesElrendezes
        ? viewerState.jelvenySzel + viewerState.jelvenyParhuzamosRes : 0
    readonly property var appWindow: viewerState.hostAppWindow
    readonly property bool quickViewerMode: viewerState.appWindow
        && viewerState.appWindow.quickViewerLaunch === true
    readonly property bool quickUploadAvailable: false
    readonly property bool propertiesOpen: viewerState.quickViewerMode ? false
        : (viewerState.appWindow
           ? viewerState.appWindow.propertiesPanelOpen === true : false)
    readonly property bool tagsOpen: viewerState.quickViewerMode ? false
        : (viewerState.appWindow
           ? viewerState.appWindow.tagsPanelOpen === true : false)
    readonly property bool placesOpen: viewerState.quickViewerMode ? false
        : (viewerState.appWindow
           ? viewerState.appWindow.placesPanelOpen === true : false)
    readonly property bool peopleOpen: viewerState.quickViewerMode ? false
        : (viewerState.appWindow
           ? viewerState.appWindow.peoplePanelOpen === true : false)
    readonly property var drawerRows:
        viewerState.currentIndex >= 0 ? [viewerState.currentIndex] : []

    property bool facesVisible: false
    function toggleFaces() {
        viewerState.facesVisible = !viewerState.facesVisible
    }
    property bool facesEditMode: false
    function beginManualFaceAdd() {
        viewerState.facesEditMode = true
        viewerState.facesVisible = true
        if (viewerState.appWindow
                && typeof viewerState.appWindow.valtsFiokLapot === "function")
            viewerState.appWindow.valtsFiokLapot("people")
    }
    function cancelManualFaceAdd() {
        viewerState.hostViewer.manualFaceAddCancelRequested()
    }
    function toggleFacesEdit() {
        if (viewerState.facesEditMode)
            viewerState.cancelManualFaceAdd()
        else
            viewerState.beginManualFaceAdd()
    }
    property int facesEditRevision: 0
    property int manualFaceAddRevision: 0
    property Connections faceScanConnections: Connections {
        target: viewerState.appWindow
            ? viewerState.appWindow._faceScanController : null
        function onUnnamedCountChanged() {
            viewerState.facesEditRevision += 1
        }
    }
    readonly property var currentFaces:
        (!viewerState.photosModel || viewerState.hostViewer.aktivSor < 0
         || !viewerState.hostFacesHelper)
            ? []
            : (viewerState.photosModel.revision,
               viewerState.facesEditRevision,
               viewerState.hostFacesHelper.facesFor(
                   viewerState.photosModel.filePathAt(
                       viewerState.hostViewer.aktivSor)))
    readonly property bool hasDetectedFaceHitTargets: {
        var items = viewerState.currentFaces
        for (var i = 0; i < items.length; ++i)
            if (items[i].detected === true) return true
        return false
    }
}

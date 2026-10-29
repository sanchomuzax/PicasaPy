import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: movieDialog
    objectName: "movieDialog"
    required property var appWindow
    required property var movieDialogs
    required property bool trayHasPictures
    function setSeconds(value) { movieTabsComponent.movieSeconds.value = value }
    x: 0
    y: movieDialog.appWindow
            && typeof movieDialog.appWindow.documentTabsBottom === "number"
        ? movieDialog.appWindow.documentTabsBottom : 0
    width: parent.width
    height: Math.max(0, parent.height - y)
    visible: !!(movieDialog.appWindow && movieDialog.appWindow.movieMakerActive)
    focus: visible
    readonly property real layoutScale:
        Math.min(1, Math.min(width / 800, height / 534))
    function open() {
        movieDialog.appWindow.openMovieMakerTab()
    }
    function close() {
        movieDialog.appWindow.closeMovieMakerTab()
    }
    property string targetFile: ""
    // A korábbi sikeres kimenet útvonala: az eredeti panel is megjegyzi,
    // és újabb export előtt felajánlja a cserét vagy az új fájlt.
    property string previousMoviePath: ""
    property string audioFile: ""
    property bool audioFileFromFolderMusic: false
    property int audioOption: 0
    property int transitionIndex: typeof controller !== "undefined" && controller && controller.movieTransition !== undefined
            && typeof controller.movieTransition === "string"
        ? Math.max(0, transitionKeys.indexOf(controller.movieTransition)) : 1
    property bool personMovieMode: false
    property int movieResolutionIndex: 1
    property bool movieShowCaptionsEnabled:
        typeof controller !== "undefined" && controller && typeof controller.moviePreference === "function"
            ? controller.moviePreference("captions") : false
    property bool movieCropToFitEnabled:
        typeof controller !== "undefined" && controller && typeof controller.moviePreference === "function"
            ? controller.moviePreference("cropfit") : false
    property bool movieShowDatesEnabled: false
    property bool movieRemoveLowResFacesEnabled:
        typeof controller !== "undefined" && controller && typeof controller.moviePreference === "function"
            ? controller.moviePreference("removeLowResFaces") : false
    property int movieOrdering: 0
    property real movieLengthFactor: 1
    property real movieBurstFactor: 0
    property var movieClipIndexes: []
    property var movieClipSources: []
    property int movieInitialPhotoCount: 0
    property int previewIndex: 0
    property string previewSource: ""
    property int previewFromIndex: -1
    property real previewTransitionProgress: 1
    property int previewImageWidth: 0
    property int previewImageHeight: 0
    property int previewLatestRequestGeneration: 0
    property int previewDisplayedGeneration: 0
    property int previewGenerationFloor: 0
    property int previewAwaitingTransitionGeneration: 0
    readonly property real previewAudioVolume:
        typeof controller !== "undefined" && controller && controller.movieVolume !== undefined
            ? controller.movieVolume / 1000 : 0.5
    readonly property string previewTransitionKind:
        transitionKeys[transitionIndex] || "dissolve"
    property string previewTransitionFrameSource: ""
    property bool previewAwaitingTransitionFrame: false
    property bool previewResettingTransition: false
    readonly property int previewFramesPerSecond: 24
    readonly property bool previewTransitionServiceAvailable:
        typeof controller !== "undefined" && controller && typeof controller.requestMovieTransitionPreview === "function"
    readonly property real previewAspectRatio: {
        var size = sizeOptions[movieResolutionIndex]
        return size[0] / size[1]
    }
    readonly property int previewOutputWidth:
        sizeOptions[movieResolutionIndex][0]
    readonly property int previewOutputHeight:
        sizeOptions[movieResolutionIndex][1]
    readonly property int previewItemCount:
        movieClipSources.length + movieSlides.length
    // A spec szerint a `Preferences\makemovie1to1` alapja 1: a valódi méret a
    // kiinduló nézet, az 1:1 gomb bekapcsolva. A mentett választás (#5288)
    // ezt írja felül indításkor.
    property bool previewActualSizeEnabled:
        typeof controller !== "undefined" && controller && typeof controller.moviePreference === "function"
            ? controller.moviePreference("actualSize") : true
    property int previewWindowVisibilityBeforeFullscreen: Window.Windowed
    property bool previewOwnsFullscreen: false
    property var movieSlides: []
    onMovieSlidesChanged: refreshPreviewAfterItemsChanged()
    onMovieClipSourcesChanged: refreshPreviewAfterItemsChanged()
    onPreviewIndexChanged: Qt.callLater(function() {
        movieDialog.prefetchNextPreviewFrame()
    })
    readonly property var movieFilmstripItems: {
        var items = []
        movieClipSources.forEach(function(source, index) {
            var names = typeof controller !== "undefined" && controller && typeof controller.movieClipNames === "function"
                ? controller.movieClipNames([source]) : []
            items.push({
                kind: "photo",
                source: source,
                name: names.length ? names[0] : "",
                index: index,
            })
        })
        movieSlides.forEach(function(_slide, index) {
            items.push({
                kind: "text",
                name: qsTr("Text Slide"),
                index: index,
            })
        })
        return items
    }
    property var movieSlideSelection: []
    property int movieSlideEditingIndex: -1
    property string textColor: "#ffffff"
    property string backgroundColor: "#000000"
    property bool loadingTextSlide: false
    onTextColorChanged: updateSelectedTextSlide()
    onBackgroundColorChanged: updateSelectedTextSlide()
    //: #2114: projektfájlból nyitottuk-e — ilyenkor a párbeszéd
    //: kimondja, hogy a felbontás NEM a projektből jön.
    property bool projektbolNyilt: false
    // A `makemoviepanel` 2.1 listája, a binárisban használt kulcsokkal.
    readonly property var transitionKeys: [
        "cut", "dissolve", "dissolveblack", "dissolvewhite",
        "wipeleft", "wiperight", "wipeup", "wipedown",
        "diagwipeul", "diagwipeur", "diagwipedl", "diagwipedr",
        "pushleft", "pushright", "pushtop", "pushdown",
        "circlein", "circleout", "kenburns", "kenburnsaoi",
        "timelapse", "rect",
    ]
    readonly property var sizeOptions: [
        [320, 240], [640, 480], [800, 600], [1024, 768],
        [1600, 1200], [1280, 720], [1920, 1080],
    ]
    readonly property var textSizes: [
        8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96,
    ]
    readonly property var textStyleIds: [
        "textstyle0", "textstyle1", "textstyle2", "textstyle3",
        "textstyle4", "textstyle5", "textstyle6", "textstyle7",
        "textstyle8", "textstyle9", "textstyle10", "textstyle11",
    ]
    readonly property int defaultSizeIndex: personMovieMode
        ? (typeof controller !== "undefined" && controller && controller.faceMovieResolutionIndex !== undefined
            ? controller.faceMovieResolutionIndex : 3)
        : (typeof controller !== "undefined" && controller && controller.movieResolutionIndex !== undefined
            ? controller.movieResolutionIndex : 1)
    function applyDefaultSize() {
        var index = personMovieMode ? 3 : 1
        if (typeof controller !== "undefined" && controller) {
            var stored = personMovieMode
                ? controller.faceMovieResolutionIndex
                : controller.movieResolutionIndex
            if (stored !== undefined) index = stored
        }
        movieResolutionIndex = index
    }
    readonly property int movieUsedPhotoCount: Math.floor(
        movieLengthFactor * movieLengthFactor
        * movieInitialPhotoCount)
    readonly property int movieBurstThresholdSeconds: Math.floor(
        movieBurstFactor * movieBurstFactor * 86400)
    readonly property real previewSlideDurationSeconds:
        Math.max(
            0.5,
            (movieTabsComponent.movieSeconds && movieTabsComponent.movieSeconds.value !== undefined
                ? movieTabsComponent.movieSeconds.value : 40) / 10)
    readonly property real previewDurationSeconds:
        previewSlideDurationSeconds * previewItemCount
    function formatPreviewTime(seconds) { return movieMakerPreviewLogic.formatPreviewTime(seconds) }
    function togglePreviewPlayback() { movieMakerPreviewLogic.togglePreviewPlayback() }
    function setPreviewIndex(index) { movieMakerPreviewLogic.setPreviewIndex(index) }
    function stopPreviewTransition() { movieMakerPreviewLogic.stopPreviewTransition() }
    function refreshPreviewAfterItemsChanged() { movieMakerPreviewLogic.refreshPreviewAfterItemsChanged() }
    function requestPreviewFrame() { return movieMakerPreviewLogic.requestPreviewFrame() }
    function prefetchNextPreviewFrame() { movieMakerPreviewLogic.prefetchNextPreviewFrame() }
    function advancePreview() { movieMakerPreviewLogic.advancePreview() }
    function seekPreview(seconds) { movieMakerPreviewLogic.seekPreview(seconds) }
    function movieFolderName(source) { return movieMakerPreviewLogic.movieFolderName(source) }
    function movieInfoText() { return movieMakerPreviewLogic.movieInfoText() }
    function selectMovieFilmstripItem(index) { movieMakerPreviewLogic.selectMovieFilmstripItem(index) }
    function togglePreviewFullscreen() { movieMakerPreviewLogic.togglePreviewFullscreen() }
    function restorePreviewFullscreen() { movieMakerPreviewLogic.restorePreviewFullscreen() }
    function openForSelection() { movieMakerActions.openForSelection() }
    function useFolderMusicAsDefault() { movieMakerActions.useFolderMusicAsDefault() }
    function openForRows(rows, allowTray, preferTray) {
        movieMakerActions.openForRows(rows, allowTray, preferTray)
    }
    function openForSources(sources) { movieMakerActions.openForSources(sources) }
    function selectedPictureCaption() { return movieMakerActions.selectedPictureCaption() }
    function openTitleDialog() { movieMakerActions.openTitleDialog() }
        function addTextSlide(slide) { movieSlideLogic.addTextSlide(slide) }
        function loadTextSlide() { movieSlideLogic.loadTextSlide() }
        function updateSelectedTextSlide() { movieSlideLogic.updateSelectedTextSlide() }
        function removeTextSlide() { movieSlideLogic.removeTextSlide() }
        function selectTextSlide(index, modifiers) { movieSlideLogic.selectTextSlide(index, modifiers) }
        function moveTextSlides(targetIndex) { movieSlideLogic.moveTextSlides(targetIndex) }
        function editTextSlide(index) { movieSlideLogic.editTextSlide(index) }
        function updateSelectedText(text) { movieSlideLogic.updateSelectedText(text) }
    function recomputeMovie() { movieMakerActions.recomputeMovie() }
    function applyMovieRecompute() { movieMakerActions.applyMovieRecompute() }
    function addSelectedClips() { movieMakerActions.addSelectedClips() }
    function deleteSelectedClip() { movieMakerActions.deleteSelectedClip() }
    function exportMovie() { movieMakerActions.exportMovie() }
    function replacePreviousMovie() { movieMakerActions.replacePreviousMovie() }
    function createNewMovie() { movieMakerActions.createNewMovie() }
    function startMovieExport() { movieMakerActions.startMovieExport() }
    onVisibleChanged: {
        if (visible) {
            forceActiveFocus()
            movieDialog.requestPreviewFrame()
            movieDialog.prefetchNextPreviewFrame()
            return
        }
        movieDialog.projektbolNyilt = false
        moviePreviewRuntime.itemsRefreshTimer.stop()
        moviePreviewRuntime.previewTimer.stop()
        moviePreviewRuntime.transition.stop()
        if (moviePreviewRuntime.musicLoader.item)
            moviePreviewRuntime.musicLoader.item.stop()
        movieDialog.restorePreviewFullscreen()
    }
    Rectangle {
        anchors.fill: parent
        color: Theme.canvasBg
    }
        MovieMakerTabs {
            id: movieTabsComponent
            anchors.fill: parent
            movieDialog: movieDialog
            options: movieOptionsComponent
            moviePreviewTimer: moviePreviewRuntime.previewTimer
        }
        MovieMakerOptions {
            id: movieOptionsComponent
            movieDialog: movieDialog
            pagesWidth: movieTabsComponent.pagesWidth
        }
    RowLayout {
        id: movieFooter
        objectName: "movieFooter"
        x: 12 * movieDialog.layoutScale
        y: 451 * movieDialog.layoutScale
        width: 266 * movieDialog.layoutScale
        height: 28 * movieDialog.layoutScale
        spacing: 8 * movieDialog.layoutScale
        Button {
            objectName: "movieCancelButton"
            text: qsTr("Close")
            Layout.fillWidth: true
            Layout.preferredHeight: 28 * movieDialog.layoutScale
            onClicked: movieDialog.close()
        }
        Button {
            objectName: "movieCreateButton"
            text: qsTr("Create Movie")
            Layout.fillWidth: true
            Layout.preferredHeight: 28 * movieDialog.layoutScale
            onClicked: movieDialog.exportMovie()
        }
    }
        MovieMakerPreview {
            id: moviePreviewComponent
            anchors.fill: parent
            movieDialog: movieDialog
            moviePreviewMusicLoader: moviePreviewRuntime.musicLoader
            moviePreviewTransition: moviePreviewRuntime.transition
            resizeTimer: moviePreviewRuntime.resizeTimer
            moviePreviewTimer: moviePreviewRuntime.previewTimer
        }
        MovieMakerFilmstrip {
            anchors.fill: parent
            movieDialog: movieDialog
            tabs: movieTabsComponent
            previewPanel: moviePreviewComponent.previewPanel
        }
        MovieMakerSlideLogic {
            id: movieSlideLogic
            movieDialog: movieDialog
            tabs: movieTabsComponent
        }
        MovieMakerPreviewLogic {
            id: movieMakerPreviewLogic
            movieDialog: movieDialog
            tabs: movieTabsComponent
            previewComponent: moviePreviewComponent
            previewTimer: moviePreviewRuntime.previewTimer
            transition: moviePreviewRuntime.transition
            transitionFallbackTimer: moviePreviewRuntime.transitionFallbackTimer
            itemsRefreshTimer: moviePreviewRuntime.itemsRefreshTimer
            frameTimer: moviePreviewRuntime.frameTimer
        }
        MovieMakerActions {
            id: movieMakerActions
            movieDialog: movieDialog
            tabs: movieTabsComponent
            confirmDialog: movieRecomputeConfirm
            previewTimer: moviePreviewRuntime.previewTimer
        }
function jelezdAFilmAtmenetElonezetet(source, generation) {
    var readyGeneration = Number(generation)
    if (movieDialog.movieClipSources.length + movieDialog.movieSlides.length < 1
            || readyGeneration <= movieDialog.previewDisplayedGeneration
            || readyGeneration <= movieDialog.previewGenerationFloor)
        return
    movieDialog.previewDisplayedGeneration = readyGeneration
    movieDialog.previewTransitionFrameSource = String(source || "")
    if (movieDialog.previewAwaitingTransitionFrame
            && readyGeneration
                === movieDialog.previewAwaitingTransitionGeneration) {
        movieDialog.previewAwaitingTransitionFrame = false
        moviePreviewRuntime.transitionFallbackTimer.stop()
        if (!moviePreviewRuntime.transition.running)
            moviePreviewRuntime.transition.restart()
    }
}

MovieMakerPreviewRuntime {
    id: moviePreviewRuntime
    movieDialog: movieDialog
    tabs: movieTabsComponent
}

ConfirmDialog {
    id: movieRecomputeConfirm
    namePrefix: "movieRecomputeConfirm"
    title: qsTr("Please Confirm...")
    onConfirmed: movieDialog.applyMovieRecompute()
}
}

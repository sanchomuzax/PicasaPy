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
    function formatPreviewTime(seconds) {
        var total = Math.max(0, Math.floor(seconds))
        var hours = Math.floor(total / 3600)
        var minutes = Math.floor(total / 60) % 60
        var remainingSeconds = total % 60
        function ketjegyu(value) {
            return value < 10 ? "0" + value : String(value)
        }
        return ketjegyu(hours) + ":" + ketjegyu(minutes)
                + ":" + ketjegyu(remainingSeconds)
    }
    function togglePreviewPlayback() {
        if (!previewItemCount) {
            moviePreviewTimer.stop()
        } else if (moviePreviewTimer.running) {
            moviePreviewTimer.stop()
        } else {
            setPreviewIndex(0)
            moviePreviewTimer.start()
        }
    }
    function setPreviewIndex(index) {
        previewIndex = Math.max(0, Math.min(previewItemCount - 1, index))
        previewSource = previewIndex < movieClipSources.length
            ? movieClipSources[previewIndex] : ""
        stopPreviewTransition()
        previewFromIndex = -1
        previewTransitionProgress = 1
        previewAwaitingTransitionFrame = false
        previewGenerationFloor = previewLatestRequestGeneration
        moviePreviewTransitionFallbackTimer.stop()
        requestPreviewFrame()
        prefetchNextPreviewFrame()
    }
    function stopPreviewTransition() {
        previewResettingTransition = true
        moviePreviewTransition.stop()
        previewResettingTransition = false
    }
    function refreshPreviewAfterItemsChanged() {
        var itemCount = movieClipSources.length + movieSlides.length
        stopPreviewTransition()
        moviePreviewFrameTimer.stop()
        moviePreviewTransitionFallbackTimer.stop()
        previewAwaitingTransitionFrame = false
        previewGenerationFloor = previewLatestRequestGeneration
        previewFromIndex = -1
        previewTransitionProgress = 1
        if (itemCount < 1) {
            previewIndex = 0
            previewSource = ""
            previewTransitionFrameSource = ""
            return
        }
        previewIndex = Math.max(0, Math.min(itemCount - 1, previewIndex))
        previewSource = previewIndex < movieClipSources.length
            ? String(movieClipSources[previewIndex]) : ""
        // Egy gépelés/szerkesztés több tételváltozást is jelez (#4852):
        // a kérés rövid összevonás után, legfeljebb egyszer indul.
        movieItemsRefreshTimer.restart()
    }
    function requestPreviewFrame() {
        if (!movieDialog.visible || !previewTransitionServiceAvailable
                || movieClipSources.length + movieSlides.length < 1
                || moviePreviewComponent.previewViewport.width < 16
                || moviePreviewComponent.previewViewport.height < 16)
            return 0
        var outgoingIndex = previewFromIndex >= 0
            ? previewFromIndex : previewIndex
        var outgoingSlide = outgoingIndex >= movieClipSources.length
            ? movieSlides[outgoingIndex - movieClipSources.length] : null
        var incomingSlide = previewIndex >= movieClipSources.length
            ? movieSlides[previewIndex - movieClipSources.length] : null
        var hostWindow = moviePreviewComponent.previewViewport.Window.window
        var devicePixelRatio = hostWindow && hostWindow.devicePixelRatio > 0
            ? hostWindow.devicePixelRatio : 1
        var generation = Number(controller.requestMovieTransitionPreview(
            outgoingIndex < movieClipSources.length
                ? String(movieClipSources[outgoingIndex]) : "",
            previewIndex < movieClipSources.length
                ? String(movieClipSources[previewIndex]) : "",
            previewTransitionKind,
            previewTransitionProgress,
            previewOutputWidth,
            previewOutputHeight,
            movieCropToFitEnabled,
            movieShowCaptionsEnabled,
            movieShowDatesEnabled,
            outgoingSlide ? JSON.stringify(outgoingSlide) : "",
            incomingSlide ? JSON.stringify(incomingSlide) : "",
            previewActualSizeEnabled,
            moviePreviewComponent.previewViewport.width,
            moviePreviewComponent.previewViewport.height,
            devicePixelRatio
        ))
        if (generation > previewLatestRequestGeneration)
            previewLatestRequestGeneration = generation
        return generation
    }
    function prefetchNextPreviewFrame() {
        if (!movieDialog.visible || !previewTransitionServiceAvailable
                || previewItemCount < 2
                || typeof controller.prefetchMovieTransitionPreview !== "function")
            return
        var nextIndex = (previewIndex + 1) % previewItemCount
        var nextSlide = nextIndex >= movieClipSources.length
            ? movieSlides[nextIndex - movieClipSources.length] : null
        var hostWindow = moviePreviewComponent.previewViewport.Window.window
        var devicePixelRatio = hostWindow && hostWindow.devicePixelRatio > 0
            ? hostWindow.devicePixelRatio : 1
        controller.prefetchMovieTransitionPreview(
            nextIndex < movieClipSources.length
                ? String(movieClipSources[nextIndex]) : "",
            nextSlide ? JSON.stringify(nextSlide) : "",
            previewOutputWidth,
            previewOutputHeight,
            movieCropToFitEnabled,
            movieShowCaptionsEnabled,
            movieShowDatesEnabled,
            previewActualSizeEnabled,
            moviePreviewComponent.previewViewport.width,
            moviePreviewComponent.previewViewport.height,
            devicePixelRatio
        )
    }
    function advancePreview() {
        if (!previewItemCount) {
            moviePreviewTimer.stop()
            return
        }
        previewFromIndex = previewIndex
        previewIndex = (previewIndex + 1) % previewItemCount
        previewSource = previewIndex < movieClipSources.length
            ? movieClipSources[previewIndex] : ""
        if (previewTransitionKind === "cut") {
            previewFromIndex = -1
            previewTransitionProgress = 1
            stopPreviewTransition()
            requestPreviewFrame()
            return
        }
        previewTransitionProgress = 0
        previewAwaitingTransitionFrame = false
        var generation = requestPreviewFrame()
        if (generation > 0) {
            previewAwaitingTransitionGeneration = generation
            previewAwaitingTransitionFrame = true
            moviePreviewTransitionFallbackTimer.restart()
            return
        }
        moviePreviewTransition.restart()
    }
    function seekPreview(seconds) {
        if (!previewItemCount) return
        setPreviewIndex(Math.min(
            previewItemCount - 1,
            Math.max(0, Math.floor(seconds / previewSlideDurationSeconds)))
        )
    }
    // A fotó mappájának neve az URL utolsó előtti eleme (a Picasa „mappa > fájl" alakja).
    function movieFolderName(source) {
        var parts = String(source).split("/")
        if (parts.length < 2) return ""
        try {
            return decodeURIComponent(parts[parts.length - 2])
        } catch (error) {
            return parts[parts.length - 2]
        }
    }
    function movieInfoText() {
        var photoCount = movieClipSources.length
        var total = photoCount + movieSlides.length
        if (!total) return ""
        var selected = movieTabsComponent.movieClipList.currentIndex
        if (selected < photoCount) selected = previewIndex
        var name, width, height, position
        if (selected >= photoCount) {
            var slideIndex = selected - photoCount
            if (slideIndex < 0 || slideIndex >= movieSlides.length) return ""
            name = qsTr("Text Slide")
            var movieSize = sizeOptions[movieResolutionIndex]
            width = movieSize[0]
            height = movieSize[1]
            position = photoCount + slideIndex + 1
        } else {
            var names = typeof controller !== "undefined" && controller && typeof controller.movieClipNames === "function"
                ? controller.movieClipNames([movieClipSources[selected]]) : []
            name = names.length ? names[0] : ""
            var folder = movieFolderName(movieClipSources[selected])
            if (folder.length) name = folder + " > " + name
            var dimensions = typeof controller !== "undefined" && controller && typeof controller.moviePreviewImageSize === "function"
                ? controller.moviePreviewImageSize(
                    String(movieClipSources[selected])) : []
            width = dimensions.length > 1 && dimensions[0] > 0
                ? dimensions[0] : movieDialog.previewImageWidth
            height = dimensions.length > 1 && dimensions[1] > 0
                ? dimensions[1] : movieDialog.previewImageHeight
            position = selected + 1
        }
        return qsTr("%1     %2x%3 pixels")
                .arg(name).arg(width).arg(height)
                + " " + qsTr("(%1 of %2)").arg(position).arg(total)
    }
    function selectMovieFilmstripItem(index) {
        movieTabsComponent.movieClipList.currentIndex = index
        if (index < movieClipSources.length) {
            moviePreviewTimer.stop()
            setPreviewIndex(index)
            movieSlideSelection = []
            movieSlideEditingIndex = -1
            if (movieTabsComponent.movieSlideList.currentIndex >= 0)
                movieTabsComponent.movieSlideList.currentIndex = -1
        } else {
            moviePreviewTimer.stop()
            var slideIndex = index - movieClipSources.length
            if (slideIndex < 0 || slideIndex >= movieSlides.length) return
            movieSlideSelection = [slideIndex]
            movieSlideEditingIndex = -1
            movieTabsComponent.movieSlideList.currentIndex = slideIndex
            setPreviewIndex(index)
        }
    }
    function togglePreviewFullscreen() {
        var hostWindow = moviePreviewComponent.previewPanel.Window.window
        if (!hostWindow) return
        if (previewOwnsFullscreen
                && hostWindow.visibility === Window.FullScreen) {
            hostWindow.visibility = previewWindowVisibilityBeforeFullscreen
            previewOwnsFullscreen = false
        } else if (hostWindow.visibility !== Window.FullScreen) {
            previewWindowVisibilityBeforeFullscreen = hostWindow.visibility
            hostWindow.visibility = Window.FullScreen
            previewOwnsFullscreen = true
        }
    }
    function restorePreviewFullscreen() {
        var hostWindow = moviePreviewComponent.previewPanel.Window.window
        if (previewOwnsFullscreen && hostWindow
                && hostWindow.visibility === Window.FullScreen) {
            hostWindow.visibility = previewWindowVisibilityBeforeFullscreen
            previewOwnsFullscreen = false
        }
    }
    function openForSelection() {
        // #455: tartott képekkel a tálca a forrás — ilyenkor a
        // rácsban nem is kell kijelölésnek lennie
        openForRows(
            movieDialog.appWindow.selectedIndexes,
            movieDialog.trayHasPictures,
            true)
    }
    function useFolderMusicAsDefault() {
        if (audioFileFromFolderMusic) audioFile = ""
        audioFileFromFolderMusic = false
        if (!(typeof controller !== "undefined" && controller) || typeof controller.filmMusicForSources !== "function")
            return
        var configured = controller.filmMusicForSources(movieClipSources)
        if (configured) {
            audioFile = configured
            audioFileFromFolderMusic = true
        }
    }
    function openForRows(rows, allowTray, preferTray) {
        if ((!rows || rows.length === 0) && !allowTray) return
        personMovieMode = false
        applyDefaultSize()
        movieClipIndexes = rows ? rows.slice(0) : []
        movieClipSources = typeof controller !== "undefined" && controller
            ? (preferTray ? controller.movieSourceUrls(movieClipIndexes)
                : controller.selectedMovieSourceUrls(movieClipIndexes))
            : []
        useFolderMusicAsDefault()
        movieInitialPhotoCount = movieClipSources.length
        movieSlides = []
        movieSlideSelection = []
        movieSlideEditingIndex = -1
        movieTabsComponent.movieClipList.currentIndex = -1
        movieTabsComponent.movieSlideList.currentIndex = -1
        loadTextSlide()
        setPreviewIndex(0)
        targetFile = ""
        open()
    }
    function openForSources(sources) {
        if (!sources || sources.length === 0) return
        personMovieMode = true
        applyDefaultSize()
        movieClipIndexes = []
        movieClipSources = sources.slice(0)
        useFolderMusicAsDefault()
        movieInitialPhotoCount = movieClipSources.length
        movieSlides = []
        movieSlideSelection = []
        movieSlideEditingIndex = -1
        movieTabsComponent.movieClipList.currentIndex = -1
        movieTabsComponent.movieSlideList.currentIndex = -1
        loadTextSlide()
        setPreviewIndex(0)
        targetFile = ""
        open()
    }
    function selectedPictureCaption() {
        if (!(typeof controller !== "undefined" && controller)
                || !controller.photos || typeof controller.photos.captionAt !== "function")
            return ""
        var row = movieDialog.appWindow.selectedIndex
        if (row < 0 && movieDialog.appWindow.selectedIndexes.length)
            row = movieDialog.appWindow.selectedIndexes[0]
        return row >= 0 ? controller.photos.captionAt(row) : ""
    }
    function openTitleDialog() {
        movieDialog.movieDialogs.movieTitleDialog.openForCaption(selectedPictureCaption(), {
            text: movieTabsComponent.movieSlideText.text,
            font: movieTabsComponent.movieFontBox.currentText,
            size: textSizes[movieTabsComponent.movieTextSizeBox.currentIndex],
            style: movieTabsComponent.movieTextStyleBox.currentIndex,
            bold: movieTabsComponent.movieBoldBox.checked,
            italic: movieTabsComponent.movieItalicBox.checked,
            outline: movieTabsComponent.movieOutlineBox.checked,
        })
    }
        function addTextSlide(slide) { movieSlideLogic.addTextSlide(slide) }
        function loadTextSlide() { movieSlideLogic.loadTextSlide() }
        function updateSelectedTextSlide() { movieSlideLogic.updateSelectedTextSlide() }
        function removeTextSlide() { movieSlideLogic.removeTextSlide() }
        function selectTextSlide(index, modifiers) { movieSlideLogic.selectTextSlide(index, modifiers) }
        function moveTextSlides(targetIndex) { movieSlideLogic.moveTextSlides(targetIndex) }
        function editTextSlide(index) { movieSlideLogic.editTextSlide(index) }
        function updateSelectedText(text) { movieSlideLogic.updateSelectedText(text) }
    function recomputeMovie() {
        // #5668: az eredeti minden kézi újraszámolás előtt kérdez,
        // akkor is, ha nincs eltávolítandó szövegdia.
        movieRecomputeConfirm.ask(
            "askapplyconfirm",
            qsTr("This will generate a new movie removing all the text slides you added. Are you sure?")
        )
    }
    function applyMovieRecompute() {
        movieSlides = []
        movieSlideSelection = []
        movieSlideEditingIndex = -1
        movieTabsComponent.movieClipList.currentIndex = -1
        movieTabsComponent.movieSlideList.currentIndex = -1
        loadTextSlide()
        if (typeof controller !== "undefined" && controller)
            movieClipSources = controller.movieSourceUrls(movieClipSources)
        setPreviewIndex(0)
        moviePreviewTimer.stop()
        movieTabsComponent.movieTabs.currentIndex = 0
    }
    function addSelectedClips() {
        if (!(typeof controller !== "undefined" && controller)) return
        var sources = movieDialog.movieClipSources.slice(0)
        controller.selectedMovieSourceUrls(
            movieDialog.appWindow.selectedIndexes).forEach(function(url) {
            if (sources.indexOf(url) < 0) sources.push(url)
        })
        movieDialog.movieClipSources = sources
    }
    function deleteSelectedClip() {
        var selected = movieTabsComponent.movieClipList.currentIndex
        if (selected < 0) return
        if (selected >= movieDialog.movieClipSources.length) {
            movieDialog.removeTextSlide()
            return
        }
        var sources = movieDialog.movieClipSources.slice(0)
        sources.splice(selected, 1)
        movieDialog.movieClipSources = sources
        movieTabsComponent.movieClipList.currentIndex = Math.min(
            selected,
            sources.length + movieDialog.movieSlides.length - 1)
    }
    function exportMovie() {
        if (previousMoviePath.length > 0) {
            movieDialog.movieDialogs.movieReplaceDialog.open()
            return
        }
        startMovieExport()
    }
    function replacePreviousMovie() {
        targetFile = previousMoviePath
        startMovieExport()
    }
    function createNewMovie() {
        targetFile = ""
        startMovieExport()
    }
    function startMovieExport() {
        if (!(typeof controller !== "undefined" && controller)) return
        var meret = sizeOptions[movieResolutionIndex]
        var sources = movieClipSources.slice(0)
        if (movieTabsComponent.movieSoloClip.checked && sources.length) {
            var selected = movieTabsComponent.movieClipList.currentIndex < 0
                    || movieTabsComponent.movieClipList.currentIndex >= sources.length
                ? 0 : movieTabsComponent.movieClipList.currentIndex
            sources = [sources[selected]]
        }
        sources = sources.slice(0, movieUsedPhotoCount)
        movieDialog.movieDialogs.movieProgressDialog.done = 0
        movieDialog.movieDialogs.movieProgressDialog.total = sources.length
                + movieSlides.length
        movieDialog.movieDialogs.movieProgressDialog.open()
        controller.exportMovie(
            sources, targetFile, meret[1], movieTabsComponent.movieSeconds.value / 10.0,
            meret[0], transitionKeys[transitionIndex], movieTabsComponent.movieOverlapSlider.value,
            audioFile, audioOption, movieSlides, {
                ordering: movieOrdering,
                showcaptions: movieShowCaptionsEnabled,
                showdates: movieShowDatesEnabled,
                cropfit: movieCropToFitEnabled,
                removelowresfaces: movieRemoveLowResFacesEnabled,
                faceMovie: movieDialog.personMovieMode,
                burstmodethresh: movieBurstThresholdSeconds,
            })
        close()
    }
    onVisibleChanged: {
        if (visible) {
            forceActiveFocus()
            movieDialog.requestPreviewFrame()
            movieDialog.prefetchNextPreviewFrame()
            return
        }
        movieDialog.projektbolNyilt = false
        movieItemsRefreshTimer.stop()
        moviePreviewTimer.stop()
        moviePreviewTransition.stop()
        if (moviePreviewMusicLoader.item)
            moviePreviewMusicLoader.item.stop()
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
            moviePreviewTimer: moviePreviewTimer
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
            resizeTimer: moviePreviewResizeTimer
            moviePreviewTimer: moviePreviewTimer
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
        moviePreviewTransitionFallbackTimer.stop()
        if (!moviePreviewTransition.running)
            moviePreviewTransition.restart()
    }
}

Connections {
    target: moviePreviewTransition
    function onRunningChanged() {
        if (movieDialog.previewResettingTransition) return
        if (moviePreviewTransition.running) return
        moviePreviewFrameTimer.stop()
        movieDialog.requestPreviewFrame()
    }
}

Timer {
    id: moviePreviewTransitionFallbackTimer
    objectName: "moviePreviewTransitionFallbackTimer"
    interval: 100
    repeat: false
    onTriggered: {
        if (!movieDialog.previewAwaitingTransitionFrame) return
        movieDialog.previewAwaitingTransitionFrame = false
        moviePreviewTransition.restart()
    }
}

Timer {
    id: movieItemsRefreshTimer
    objectName: "movieItemsRefreshTimer"
    interval: 120
    repeat: false
    onTriggered: {
        movieDialog.requestPreviewFrame()
        movieDialog.prefetchNextPreviewFrame()
    }
}

Timer {
    id: moviePreviewResizeTimer
    objectName: "moviePreviewResizeTimer"
    interval: 120
    repeat: false
    onTriggered: movieDialog.requestPreviewFrame()
}

Timer {
    id: moviePreviewFrameTimer
    objectName: "moviePreviewFrameTimer"
    interval: Math.max(1, Math.round(1000 / movieDialog.previewFramesPerSecond))
    repeat: true
    running: moviePreviewTransition.running
        && !moviePreviewTransition.paused
        && !movieDialog.previewAwaitingTransitionFrame
    onTriggered: movieDialog.requestPreviewFrame()
}

Timer {
    id: moviePreviewTimer
    objectName: "moviePreviewTimer"
    interval: Math.max(
        500,
        (movieTabsComponent.movieSeconds && movieTabsComponent.movieSeconds.value !== undefined
            ? movieTabsComponent.movieSeconds.value : 40) * 100)
    repeat: true
    onRunningChanged: {
        if (!moviePreviewMusicLoader.item) return
        if (running) moviePreviewMusicLoader.item.play()
        else moviePreviewMusicLoader.item.pause()
    }
    onTriggered: movieDialog.advancePreview()
}

Loader {
    id: moviePreviewMusicLoader
    objectName: "moviePreviewMusicLoader"
    active: movieDialog.visible && moviePreviewTimer.running
        && movieDialog.audioFile.length > 0
    source: active ? "MoviePreviewMusicPlayer.qml" : ""
    property string audioSource: movieDialog.audioFile
    property real outputVolume: movieDialog.previewAudioVolume
    property bool loopMusic: movieDialog.audioOption === 2
    onLoaded: {
        item.source = audioSource
        item.volume = outputVolume
        item.loop = loopMusic
        if (moviePreviewTimer.running) item.play()
    }
    onAudioSourceChanged: {
        if (!item) return
        item.source = audioSource
        if (audioSource && moviePreviewTimer.running) item.play()
        else if (!audioSource) item.stop()
    }
    onOutputVolumeChanged: if (item) item.volume = outputVolume
    onLoopMusicChanged: if (item) item.loop = loopMusic
}

NumberAnimation {
    id: moviePreviewTransition
    objectName: "moviePreviewTransition"
    target: movieDialog
    property: "previewTransitionProgress"
    from: 0
    to: 1
    duration: Math.max(
        1,
        (movieTabsComponent.movieOverlapSlider && movieTabsComponent.movieOverlapSlider.value !== undefined
            ? movieTabsComponent.movieOverlapSlider.value : 0.5) * 1000)
}

ConfirmDialog {
    id: movieRecomputeConfirm
    namePrefix: "movieRecomputeConfirm"
    title: qsTr("Please Confirm...")
    onConfirmed: movieDialog.applyMovieRecompute()
}
}

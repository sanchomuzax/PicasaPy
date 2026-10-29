import QtQuick

QtObject {
    id: root
    required property var movieDialog
    required property var tabs
    required property var confirmDialog
    required property var previewTimer

    function openForSelection() {
        // #455: tartott képekkel a tálca a forrás — ilyenkor a
        // rácsban nem is kell kijelölésnek lennie
        root.openForRows(
            movieDialog.appWindow.selectedIndexes,
            movieDialog.trayHasPictures,
            true)
    }
    function useFolderMusicAsDefault() {
        if (movieDialog.audioFileFromFolderMusic) movieDialog.audioFile = ""
        movieDialog.audioFileFromFolderMusic = false
        if (!(typeof controller !== "undefined" && controller)
                || typeof controller.filmMusicForSources !== "function")
            return
        var configured = controller.filmMusicForSources(movieDialog.movieClipSources)
        if (configured) {
            movieDialog.audioFile = configured
            movieDialog.audioFileFromFolderMusic = true
        }
    }
    function openForRows(rows, allowTray, preferTray) {
        if ((!rows || rows.length === 0) && !allowTray) return
        movieDialog.personMovieMode = false
        movieDialog.applyDefaultSize()
        movieDialog.movieClipIndexes = rows ? rows.slice(0) : []
        movieDialog.movieClipSources = typeof controller !== "undefined" && controller
            ? (preferTray ? controller.movieSourceUrls(movieDialog.movieClipIndexes)
                : controller.selectedMovieSourceUrls(movieDialog.movieClipIndexes))
            : []
        root.useFolderMusicAsDefault()
        movieDialog.movieInitialPhotoCount = movieDialog.movieClipSources.length
        movieDialog.movieSlides = []
        movieDialog.movieSlideSelection = []
        movieDialog.movieSlideEditingIndex = -1
        root.tabs.movieClipList.currentIndex = -1
        root.tabs.movieSlideList.currentIndex = -1
        movieDialog.loadTextSlide()
        movieDialog.setPreviewIndex(0)
        movieDialog.targetFile = ""
        movieDialog.open()
    }
    function openForSources(sources) {
        if (!sources || sources.length === 0) return
        movieDialog.personMovieMode = true
        movieDialog.applyDefaultSize()
        movieDialog.movieClipIndexes = []
        movieDialog.movieClipSources = sources.slice(0)
        root.useFolderMusicAsDefault()
        movieDialog.movieInitialPhotoCount = movieDialog.movieClipSources.length
        movieDialog.movieSlides = []
        movieDialog.movieSlideSelection = []
        movieDialog.movieSlideEditingIndex = -1
        root.tabs.movieClipList.currentIndex = -1
        root.tabs.movieSlideList.currentIndex = -1
        movieDialog.loadTextSlide()
        movieDialog.setPreviewIndex(0)
        movieDialog.targetFile = ""
        movieDialog.open()
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
        movieDialog.movieDialogs.movieTitleDialog.openForCaption(root.selectedPictureCaption(), {
            text: root.tabs.movieSlideText.text,
            font: root.tabs.movieFontBox.currentText,
            size: movieDialog.textSizes[root.tabs.movieTextSizeBox.currentIndex],
            style: root.tabs.movieTextStyleBox.currentIndex,
            bold: root.tabs.movieBoldBox.checked,
            italic: root.tabs.movieItalicBox.checked,
            outline: root.tabs.movieOutlineBox.checked,
        })
    }
    function recomputeMovie() {
        // #5668: az eredeti minden kézi újraszámolás előtt kérdez,
        // akkor is, ha nincs eltávolítandó szövegdia.
        root.confirmDialog.ask(
            "askapplyconfirm",
            qsTr("This will generate a new movie removing all the text slides you added. Are you sure?")
        )
    }
    function applyMovieRecompute() {
        movieDialog.movieSlides = []
        movieDialog.movieSlideSelection = []
        movieDialog.movieSlideEditingIndex = -1
        root.tabs.movieClipList.currentIndex = -1
        root.tabs.movieSlideList.currentIndex = -1
        movieDialog.loadTextSlide()
        if (typeof controller !== "undefined" && controller)
            movieDialog.movieClipSources = controller.movieSourceUrls(movieDialog.movieClipSources)
        movieDialog.setPreviewIndex(0)
        root.previewTimer.stop()
        root.tabs.movieTabs.currentIndex = 0
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
        var selected = root.tabs.movieClipList.currentIndex
        if (selected < 0) return
        if (selected >= movieDialog.movieClipSources.length) {
            movieDialog.removeTextSlide()
            return
        }
        var sources = movieDialog.movieClipSources.slice(0)
        sources.splice(selected, 1)
        movieDialog.movieClipSources = sources
        root.tabs.movieClipList.currentIndex = Math.min(
            selected,
            sources.length + movieDialog.movieSlides.length - 1)
    }
    function exportMovie() {
        if (movieDialog.previousMoviePath.length > 0) {
            movieDialog.movieDialogs.movieReplaceDialog.open()
            return
        }
        root.startMovieExport()
    }
    function replacePreviousMovie() {
        movieDialog.targetFile = movieDialog.previousMoviePath
        root.startMovieExport()
    }
    function createNewMovie() {
        movieDialog.targetFile = ""
        root.startMovieExport()
    }
    function startMovieExport() {
        if (!(typeof controller !== "undefined" && controller)) return
        var meret = movieDialog.sizeOptions[movieDialog.movieResolutionIndex]
        var sources = movieDialog.movieClipSources.slice(0)
        if (root.tabs.movieSoloClip.checked && sources.length) {
            var selected = root.tabs.movieClipList.currentIndex < 0
                    || root.tabs.movieClipList.currentIndex >= sources.length
                ? 0 : root.tabs.movieClipList.currentIndex
            sources = [sources[selected]]
        }
        sources = sources.slice(0, movieDialog.movieUsedPhotoCount)
        movieDialog.movieDialogs.movieProgressDialog.done = 0
        movieDialog.movieDialogs.movieProgressDialog.total = sources.length
                + movieDialog.movieSlides.length
        movieDialog.movieDialogs.movieProgressDialog.open()
        controller.exportMovie(
            sources, movieDialog.targetFile, meret[1], root.tabs.movieSeconds.value / 10.0,
            meret[0], movieDialog.transitionKeys[movieDialog.transitionIndex],
            root.tabs.movieOverlapSlider.value,
            movieDialog.audioFile, movieDialog.audioOption, movieDialog.movieSlides, {
                ordering: movieDialog.movieOrdering,
                showcaptions: movieDialog.movieShowCaptionsEnabled,
                showdates: movieDialog.movieShowDatesEnabled,
                cropfit: movieDialog.movieCropToFitEnabled,
                removelowresfaces: movieDialog.movieRemoveLowResFacesEnabled,
                faceMovie: movieDialog.personMovieMode,
                burstmodethresh: movieDialog.movieBurstThresholdSeconds,
            })
        movieDialog.close()
    }
}

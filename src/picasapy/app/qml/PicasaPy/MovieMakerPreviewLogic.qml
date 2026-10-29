import QtQuick
import QtQuick.Window

QtObject {
    id: root
    required property var movieDialog
    required property var tabs
    required property var previewComponent
    required property var previewTimer
    required property var transition
    required property var transitionFallbackTimer
    required property var itemsRefreshTimer
    required property var frameTimer

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
        if (!movieDialog.previewItemCount) {
            root.previewTimer.stop()
        } else if (root.previewTimer.running) {
            root.previewTimer.stop()
        } else {
            root.setPreviewIndex(0)
            root.previewTimer.start()
        }
    }
    function setPreviewIndex(index) {
        movieDialog.previewIndex = Math.max(
            0, Math.min(movieDialog.previewItemCount - 1, index))
        movieDialog.previewSource = movieDialog.previewIndex < movieDialog.movieClipSources.length
            ? movieDialog.movieClipSources[movieDialog.previewIndex] : ""
        root.stopPreviewTransition()
        movieDialog.previewFromIndex = -1
        movieDialog.previewTransitionProgress = 1
        movieDialog.previewAwaitingTransitionFrame = false
        movieDialog.previewGenerationFloor = movieDialog.previewLatestRequestGeneration
        root.transitionFallbackTimer.stop()
        root.requestPreviewFrame()
        root.prefetchNextPreviewFrame()
    }
    function stopPreviewTransition() {
        movieDialog.previewResettingTransition = true
        root.transition.stop()
        movieDialog.previewResettingTransition = false
    }
    function refreshPreviewAfterItemsChanged() {
        var itemCount = movieDialog.movieClipSources.length + movieDialog.movieSlides.length
        root.stopPreviewTransition()
        root.frameTimer.stop()
        root.transitionFallbackTimer.stop()
        movieDialog.previewAwaitingTransitionFrame = false
        movieDialog.previewGenerationFloor = movieDialog.previewLatestRequestGeneration
        movieDialog.previewFromIndex = -1
        movieDialog.previewTransitionProgress = 1
        if (itemCount < 1) {
            movieDialog.previewIndex = 0
            movieDialog.previewSource = ""
            movieDialog.previewTransitionFrameSource = ""
            return
        }
        movieDialog.previewIndex = Math.max(
            0, Math.min(itemCount - 1, movieDialog.previewIndex))
        movieDialog.previewSource = movieDialog.previewIndex < movieDialog.movieClipSources.length
            ? String(movieDialog.movieClipSources[movieDialog.previewIndex]) : ""
        // Egy gépelés/szerkesztés több tételváltozást is jelez (#4852):
        // a kérés rövid összevonás után, legfeljebb egyszer indul.
        root.itemsRefreshTimer.restart()
    }
    function requestPreviewFrame() {
        if (!movieDialog.visible || !movieDialog.previewTransitionServiceAvailable
                || movieDialog.movieClipSources.length + movieDialog.movieSlides.length < 1
                || root.previewComponent.previewViewport.width < 16
                || root.previewComponent.previewViewport.height < 16)
            return 0
        var outgoingIndex = movieDialog.previewFromIndex >= 0
            ? movieDialog.previewFromIndex : movieDialog.previewIndex
        var outgoingSlide = outgoingIndex >= movieDialog.movieClipSources.length
            ? movieDialog.movieSlides[outgoingIndex - movieDialog.movieClipSources.length] : null
        var incomingSlide = movieDialog.previewIndex >= movieDialog.movieClipSources.length
            ? movieDialog.movieSlides[movieDialog.previewIndex - movieDialog.movieClipSources.length] : null
        var hostWindow = root.previewComponent.previewViewport.Window.window
        var devicePixelRatio = hostWindow && hostWindow.devicePixelRatio > 0
            ? hostWindow.devicePixelRatio : 1
        var generation = Number(controller.requestMovieTransitionPreview(
            outgoingIndex < movieDialog.movieClipSources.length
                ? String(movieDialog.movieClipSources[outgoingIndex]) : "",
            movieDialog.previewIndex < movieDialog.movieClipSources.length
                ? String(movieDialog.movieClipSources[movieDialog.previewIndex]) : "",
            movieDialog.previewTransitionKind,
            movieDialog.previewTransitionProgress,
            movieDialog.previewOutputWidth,
            movieDialog.previewOutputHeight,
            movieDialog.movieCropToFitEnabled,
            movieDialog.movieShowCaptionsEnabled,
            movieDialog.movieShowDatesEnabled,
            outgoingSlide ? JSON.stringify(outgoingSlide) : "",
            incomingSlide ? JSON.stringify(incomingSlide) : "",
            movieDialog.previewActualSizeEnabled,
            root.previewComponent.previewViewport.width,
            root.previewComponent.previewViewport.height,
            devicePixelRatio
        ))
        if (generation > movieDialog.previewLatestRequestGeneration)
            movieDialog.previewLatestRequestGeneration = generation
        return generation
    }
    function prefetchNextPreviewFrame() {
        if (!movieDialog.visible || !movieDialog.previewTransitionServiceAvailable
                || movieDialog.previewItemCount < 2
                || typeof controller.prefetchMovieTransitionPreview !== "function")
            return
        var nextIndex = (movieDialog.previewIndex + 1) % movieDialog.previewItemCount
        var nextSlide = nextIndex >= movieDialog.movieClipSources.length
            ? movieDialog.movieSlides[nextIndex - movieDialog.movieClipSources.length] : null
        var hostWindow = root.previewComponent.previewViewport.Window.window
        var devicePixelRatio = hostWindow && hostWindow.devicePixelRatio > 0
            ? hostWindow.devicePixelRatio : 1
        controller.prefetchMovieTransitionPreview(
            nextIndex < movieDialog.movieClipSources.length
                ? String(movieDialog.movieClipSources[nextIndex]) : "",
            nextSlide ? JSON.stringify(nextSlide) : "",
            movieDialog.previewOutputWidth,
            movieDialog.previewOutputHeight,
            movieDialog.movieCropToFitEnabled,
            movieDialog.movieShowCaptionsEnabled,
            movieDialog.movieShowDatesEnabled,
            movieDialog.previewActualSizeEnabled,
            root.previewComponent.previewViewport.width,
            root.previewComponent.previewViewport.height,
            devicePixelRatio
        )
    }
    function advancePreview() {
        if (!movieDialog.previewItemCount) {
            root.previewTimer.stop()
            return
        }
        movieDialog.previewFromIndex = movieDialog.previewIndex
        movieDialog.previewIndex =
            (movieDialog.previewIndex + 1) % movieDialog.previewItemCount
        movieDialog.previewSource = movieDialog.previewIndex < movieDialog.movieClipSources.length
            ? movieDialog.movieClipSources[movieDialog.previewIndex] : ""
        if (movieDialog.previewTransitionKind === "cut") {
            movieDialog.previewFromIndex = -1
            movieDialog.previewTransitionProgress = 1
            root.stopPreviewTransition()
            root.requestPreviewFrame()
            return
        }
        movieDialog.previewTransitionProgress = 0
        movieDialog.previewAwaitingTransitionFrame = false
        var generation = root.requestPreviewFrame()
        if (generation > 0) {
            movieDialog.previewAwaitingTransitionGeneration = generation
            movieDialog.previewAwaitingTransitionFrame = true
            root.transitionFallbackTimer.restart()
            return
        }
        root.transition.restart()
    }
    function seekPreview(seconds) {
        if (!movieDialog.previewItemCount) return
        root.setPreviewIndex(Math.min(
            movieDialog.previewItemCount - 1,
            Math.max(0, Math.floor(seconds / movieDialog.previewSlideDurationSeconds)))
        )
    }
    // A fotó mappájának neve az URL utolsó előtti eleme (a Picasa „mappa > fájl” alakja).
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
        var photoCount = movieDialog.movieClipSources.length
        var total = photoCount + movieDialog.movieSlides.length
        if (!total) return ""
        var selected = root.tabs.movieClipList.currentIndex
        if (selected < photoCount) selected = movieDialog.previewIndex
        var name, width, height, position
        if (selected >= photoCount) {
            var slideIndex = selected - photoCount
            if (slideIndex < 0 || slideIndex >= movieDialog.movieSlides.length) return ""
            name = qsTr("Text Slide")
            var movieSize = movieDialog.sizeOptions[movieDialog.movieResolutionIndex]
            width = movieSize[0]
            height = movieSize[1]
            position = photoCount + slideIndex + 1
        } else {
            var names = typeof controller !== "undefined" && controller && typeof controller.movieClipNames === "function"
                ? controller.movieClipNames([movieDialog.movieClipSources[selected]]) : []
            name = names.length ? names[0] : ""
            var folder = root.movieFolderName(movieDialog.movieClipSources[selected])
            if (folder.length) name = folder + " > " + name
            var dimensions = typeof controller !== "undefined" && controller && typeof controller.moviePreviewImageSize === "function"
                ? controller.moviePreviewImageSize(
                    String(movieDialog.movieClipSources[selected])) : []
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
        root.tabs.movieClipList.currentIndex = index
        if (index < movieDialog.movieClipSources.length) {
            root.previewTimer.stop()
            root.setPreviewIndex(index)
            movieDialog.movieSlideSelection = []
            movieDialog.movieSlideEditingIndex = -1
            if (root.tabs.movieSlideList.currentIndex >= 0)
                root.tabs.movieSlideList.currentIndex = -1
        } else {
            root.previewTimer.stop()
            var slideIndex = index - movieDialog.movieClipSources.length
            if (slideIndex < 0 || slideIndex >= movieDialog.movieSlides.length) return
            movieDialog.movieSlideSelection = [slideIndex]
            movieDialog.movieSlideEditingIndex = -1
            root.tabs.movieSlideList.currentIndex = slideIndex
            root.setPreviewIndex(index)
        }
    }
    function togglePreviewFullscreen() {
        var hostWindow = root.previewComponent.previewPanel.Window.window
        if (!hostWindow) return
        if (movieDialog.previewOwnsFullscreen
                && hostWindow.visibility === Window.FullScreen) {
            hostWindow.visibility = movieDialog.previewWindowVisibilityBeforeFullscreen
            movieDialog.previewOwnsFullscreen = false
        } else if (hostWindow.visibility !== Window.FullScreen) {
            movieDialog.previewWindowVisibilityBeforeFullscreen = hostWindow.visibility
            hostWindow.visibility = Window.FullScreen
            movieDialog.previewOwnsFullscreen = true
        }
    }
    function restorePreviewFullscreen() {
        var hostWindow = root.previewComponent.previewPanel.Window.window
        if (movieDialog.previewOwnsFullscreen && hostWindow
                && hostWindow.visibility === Window.FullScreen) {
            hostWindow.visibility = movieDialog.previewWindowVisibilityBeforeFullscreen
            movieDialog.previewOwnsFullscreen = false
        }
    }
}

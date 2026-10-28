import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: root
    anchors.fill: parent
    required property var movieDialog
    required property var resizeTimer
    property var moviePreviewTimer: null
    property alias previewPanel: moviePreviewPanel
    property alias previewViewport: moviePreviewViewport

    ColumnLayout {
        id: moviePreviewPanel
        objectName: "moviePreviewPanel"
        x: 287 * movieDialog.layoutScale
        y: 11 * movieDialog.layoutScale
        width: Math.max(0, parent.width - x)
        // A lejátszósor a filmcsík fölött, a panel alján marad: az
        // előnézet a köztes helyet kitölti (a főablak méretét követi).
        height: Math.max(0, parent.height - y - 90 * movieDialog.layoutScale)
        spacing: 4
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 118 * movieDialog.layoutScale
            Item {
                id: moviePreviewViewport
                objectName: "moviePreviewViewport"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 118 * movieDialog.layoutScale
                clip: true
                onWidthChanged: if (movieDialog.visible) resizeTimer.restart()
                onHeightChanged: if (movieDialog.visible) resizeTimer.restart()
                Rectangle {
                    objectName: "moviePreviewViewportBg"
                    anchors.fill: parent
                    color: Theme.viewerBg
                }
                Rectangle {
                    id: moviePreviewFrameBox
                    objectName: "moviePreviewFrameBox"
                    // Valódi méretben (1:1) a kimeneti képkocka mérete, nyújtás nélkül,
                    // a szürke panel margójával. Egyébként a panelhez igazított keret,
                    // egész, páros pixelekre igazítva (a renderelő is így méretez),
                    // hogy a kép széle és a keret széle egybeessen.
                    readonly property real pixelRatio: {
                        var hostWindow = moviePreviewViewport.Window.window
                        return hostWindow && hostWindow.devicePixelRatio > 0
                            ? hostWindow.devicePixelRatio : 1
                    }
                    width: movieDialog.previewActualSizeEnabled
                        ? Math.round(movieDialog.previewOutputWidth / pixelRatio)
                        : 2 * Math.floor(Math.round(Math.min(parent.width,
                            parent.height * movieDialog.previewAspectRatio)) / 2)
                    height: movieDialog.previewActualSizeEnabled
                        ? Math.round(movieDialog.previewOutputHeight / pixelRatio)
                        : Math.round(width / movieDialog.previewAspectRatio)
                    x: Math.round((parent.width - width) / 2)
                    y: Math.round((parent.height - height) / 2)
                    color: "#000000"
                }
                MoviePreviewFrame {
                    objectName: "moviePreviewOutgoingFrame"
                    anchors.fill: moviePreviewFrameBox
                    z: 0
                    visible: !movieDialog.previewTransitionServiceAvailable
                        && moviePreviewTransition.running
                        && movieDialog.previewFromIndex >= 0
                    photoSources: movieDialog.movieClipSources
                    slides: movieDialog.movieSlides
                    itemIndex: movieDialog.previewFromIndex
                    aspectRatio: movieDialog.previewAspectRatio
                    outputHeight: movieDialog.previewOutputHeight
                    actualSizeEnabled: movieDialog.previewActualSizeEnabled
                    imageObjectName: "moviePreviewOutgoingImage"
                    onImageSizeChanged: function(width, height) {
                        if (itemIndex === movieDialog.previewIndex) {
                            movieDialog.previewImageWidth = width
                            movieDialog.previewImageHeight = height
                        }
                    }
                }
                MoviePreviewFrame {
                    objectName: "moviePreviewIncomingFrame"
                    anchors.fill: moviePreviewFrameBox
                    z: 1
                    visible: !movieDialog.previewTransitionServiceAvailable
                        && movieDialog.previewItemCount > 0
                    photoSources: movieDialog.movieClipSources
                    slides: movieDialog.movieSlides
                    itemIndex: movieDialog.previewIndex
                    aspectRatio: movieDialog.previewAspectRatio
                    outputHeight: movieDialog.previewOutputHeight
                    actualSizeEnabled: movieDialog.previewActualSizeEnabled
                    imageObjectName: "moviePreviewImage"
                    onImageSizeChanged: function(width, height) {
                        if (itemIndex === movieDialog.previewIndex) {
                            movieDialog.previewImageWidth = width
                            movieDialog.previewImageHeight = height
                        }
                    }
                }
                Image {
                    id: moviePreviewTransitionImage
                    objectName: "moviePreviewTransitionImage"
                    anchors.centerIn: moviePreviewFrameBox
                    z: 2
                    visible: source !== ""
                        && movieDialog.movieClipSources.length
                            + movieDialog.movieSlides.length > 0
                    source: movieDialog.previewTransitionFrameSource
                    width: movieDialog.previewActualSizeEnabled
                            && sourceSize.width > 0
                        ? sourceSize.width / moviePreviewDpr
                        : moviePreviewFrameBox.width
                    height: movieDialog.previewActualSizeEnabled
                            && sourceSize.height > 0
                        ? sourceSize.height / moviePreviewDpr
                        : moviePreviewFrameBox.height
                    // A keret egész pixel (lásd fent), a kép kitölti. A letterbox-sávok
                    // a kész képkockában vannak, tehát a kitöltés nem vág le fotót.
                    fillMode: Image.PreserveAspectCrop
                    cache: false
                    readonly property real moviePreviewDpr: {
                        var hostWindow = moviePreviewViewport.Window.window
                        return hostWindow && hostWindow.devicePixelRatio > 0
                            ? hostWindow.devicePixelRatio : 1
                    }
                }
            }
        }
        RowLayout {
            objectName: "video_control_bar2/controlbar"
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            spacing: 6
            Item {
                objectName: "video_control_bar2/moviecontrolsclip"
                Layout.preferredWidth: 34
                Layout.preferredHeight: 30
                Item {
                    objectName: "video_control_bar2/moviecontrols"
                    anchors.fill: parent
                    PicasaButton {
                        objectName: "moviePreviewButton"
                        anchors.fill: parent
                        text: root.moviePreviewTimer
                                && root.moviePreviewTimer.running ? "❚❚" : "▶"
                        checkable: true
                        checked: root.moviePreviewTimer
                                && root.moviePreviewTimer.running
                        ToolTip.text: root.moviePreviewTimer
                                && root.moviePreviewTimer.running
                                ? qsTr("Pause") : qsTr("Preview")
                        ToolTip.delay: Theme.tooltipDelay
                        ToolTip.visible: hovered
                        onClicked: movieDialog.togglePreviewPlayback()
                    }
                }
            }
            RowLayout {
                objectName: "video_control_bar2/moviescrubslider_container"
                Layout.fillWidth: true
                Layout.preferredHeight: 30
                PicasaSlider {
                    id: moviePreviewScrubSlider
                    objectName: "video_control_bar2/scaleslider"
                    Layout.fillWidth: true
                    from: 0
                    to: Math.max(1, movieDialog.previewDurationSeconds)
                    stepSize: movieDialog.previewSlideDurationSeconds
                    enabled: movieDialog.previewItemCount > 1
                    Binding on value {
                        when: !moviePreviewScrubSlider.pressed
                        value: movieDialog.previewIndex
                                * movieDialog.previewSlideDurationSeconds
                    }
                    onMoved: movieDialog.seekPreview(value)
                }
            }
            Text {
                objectName: "video_control_bar2/time"
                Layout.preferredWidth: 136
                horizontalAlignment: Text.AlignHCenter
                color: Theme.ink
                text: movieDialog.formatPreviewTime(
                          movieDialog.previewIndex
                          * movieDialog.previewSlideDurationSeconds)
                      + " / " + movieDialog.formatPreviewTime(
                          movieDialog.previewDurationSeconds)
            }
            Text {
                text: "🔊"
                color: Theme.ink
            }
            PicasaSlider {
                objectName: "video_control_bar2/volumeslider"
                Layout.preferredWidth: 70
                from: 0
                to: 1000
                stepSize: 10
                value: typeof controller !== "undefined" && controller
                        && controller.movieVolume !== undefined
                    ? controller.movieVolume : 500
                onMoved: {
                    if (typeof controller !== "undefined" && controller
                            && controller.setMovieVolume)
                        controller.setMovieVolume(Math.round(value))
                    if (moviePreviewMusicLoader.item)
                        moviePreviewMusicLoader.item.volume = value / 1000
                }
            }
            PicasaButton {
                objectName: "video_control_bar2/1to1"
                Layout.preferredWidth: 38
                text: "1:1"
                checkable: true
                // A bekapcsolt állapot a mérce szerint szürke (#5288).
                greyChecked: true
                checked: movieDialog.previewActualSizeEnabled
                ToolTip.text: qsTr("Show actual movie size (don't stretch)")
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.visible: hovered
                onClicked: {
                    movieDialog.previewActualSizeEnabled = checked
                    if (typeof controller !== "undefined" && controller
                            && typeof controller.setMoviePreference === "function")
                        controller.setMoviePreference("actualSize", checked)
                    movieDialog.requestPreviewFrame()
                }
            }
            PicasaButton {
                objectName: "video_control_bar2/fullscreen"
                Layout.preferredWidth: 32
                text: "⛶"
                ToolTip.text: qsTr("Play full screen")
                ToolTip.delay: Theme.tooltipDelay
                ToolTip.visible: hovered
                onClicked: movieDialog.togglePreviewFullscreen()
            }
        }
}
}

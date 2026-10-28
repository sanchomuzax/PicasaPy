import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: root
    anchors.fill: parent
    required property var movieDialog
    required property var options
    property var moviePreviewTimer: null
    property alias movieTabs: movieTabs
    property alias movieAudioOptionBox: movieAudioOptionBox
    property alias movieTransitionBox: movieTransitionBox
    property alias movieSeconds: movieSeconds
    property alias movieOverlapSlider: movieOverlapSlider
    property alias movieSlideText: movieSlideText
    property alias movieFontBox: movieFontBox
    property alias movieTextSizeBox: movieTextSizeBox
    property alias movieTextStyleBox: movieTextStyleBox
    property alias movieBoldBox: movieBoldBox
    property alias movieItalicBox: movieItalicBox
    property alias movieOutlineBox: movieOutlineBox
    property alias movieSlideList: movieSlideList
    property alias movieClipList: movieClipList
    property alias movieSoloClip: movieSoloClip
    readonly property real pagesWidth: moviePages.width

Item {
    id: movieLeftPanel
    objectName: "movieLeftPanel"
    x: 4 * movieDialog.layoutScale
    y: 20 * movieDialog.layoutScale
    width: 276 * movieDialog.layoutScale
    height: 389 * movieDialog.layoutScale

    // A mérce szerint: 2 képpontos kék szegély, világos szürke töltés.
    Rectangle {
        objectName: "movieLeftPanelFrame"
        anchors.fill: parent
        color: Theme.movieBoxFill
        border.color: Theme.movieBoxBorder
        border.width: 2
        radius: 7
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        clip: true
    TabBar {
        id: movieTabs
        objectName: "movieTabs"
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        Layout.maximumWidth: 276 * movieDialog.layoutScale
        Layout.preferredHeight: 25 * movieDialog.layoutScale
        Layout.leftMargin: 1 * movieDialog.layoutScale
        Layout.rightMargin: 1 * movieDialog.layoutScale
        Layout.topMargin: 1 * movieDialog.layoutScale
        MovieTabButton { objectName: "movieTabMotion"; text: qsTr("Movie") }
        MovieTabButton { objectName: "movieTabSlide"; text: qsTr("Slide") }
        MovieTabButton {
            objectName: movieDialog.personMovieMode
                ? "movieTabOptions" : "movieTabClips"
            text: movieDialog.personMovieMode
                ? qsTr("Options")
                : qsTr("Clips (%d)").replace(
                    "%d", String(movieDialog.movieClipSources.length))
        }
    }
    StackLayout {
        id: moviePages
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumWidth: 0
        Layout.maximumWidth: 276 * movieDialog.layoutScale
        Layout.topMargin: 6 * movieDialog.layoutScale
        Layout.leftMargin: 1 * movieDialog.layoutScale
        Layout.rightMargin: 1 * movieDialog.layoutScale
        Layout.bottomMargin: 1 * movieDialog.layoutScale
        currentIndex: movieTabs.currentIndex
        ScrollView {
            id: movieTabPanelMotion
            objectName: "movieTabPanelMotion"
            clip: true
            ScrollBar.vertical: ScrollBar {
                objectName: "movieMotionScrollBar"
            }
            ColumnLayout {
                width: moviePages.width
                spacing: 1

                Text {
                    objectName: "audio_label"
                    text: qsTr("Audio Track:")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                }
                Text {
                    objectName: "movieAudioPathLabel"
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: movieDialog.audioFile.length
                        ? decodeURIComponent(movieDialog.audioFile.split("/").pop())
                        : qsTr("None")
                    color: movieDialog.audioFile.length
                        ? Theme.ink : Theme.picasaGreen
                    elide: Text.ElideMiddle
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        objectName: "movieAddAudioButton"
                        text: qsTr("Load…")
                        Layout.fillWidth: true
                        onClicked: movieDialog.movieDialogs.movieAudioDialog.open()
                    }
                    Button {
                        id: removeAudioButton
                        objectName: "movieRemoveAudioButton"
                        text: qsTr("Clear")
                        Layout.fillWidth: true
                        enabled: movieDialog.audioFile.length > 0
                        // Hangsáv nélkül a felirat szürke, nem a sötét gombszöveg.
                        contentItem: Text {
                            text: removeAudioButton.text
                            font: removeAudioButton.font
                            color: removeAudioButton.enabled
                                ? Theme.ink : Theme.movieDisabledText
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: {
                            movieDialog.audioFile = ""
                            movieDialog.audioFileFromFolderMusic = false
                        }
                    }
                }
                Text {
                    text: qsTr("Options")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.textGray
                }
                PicasaComboBox {
                    id: movieAudioOptionBox
                    objectName: "movieAudioOptionBox"
                    Layout.fillWidth: true
                    enabled: movieDialog.audioFile.length > 0
                    // Hangsáv nélkül a felirat a mért szürke, nem a sötét gombszöveg.
                    palette.disabled.buttonText: Theme.movieOptionDisabledText
                    model: [qsTr("Truncate audio"), qsTr("Fit photos into audio"),
                        qsTr("Loop photos to match audio")]
                    currentIndex: movieDialog.audioOption
                    onActivated: movieDialog.audioOption = currentIndex
                }
                Text {
                    text: qsTr("Transition style:")
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    color: Theme.ink
                }
                PicasaComboBox {
                    id: movieTransitionBox
                    objectName: "movieTransitionBox"
                    Layout.fillWidth: true
                    model: [qsTr("Cut"), qsTr("Dissolve"),
                        qsTr("Dissolve through black"), qsTr("Dissolve through white"),
                        qsTr("Wipe - left"), qsTr("Wipe"), qsTr("Wipe - top"),
                        qsTr("Wipe - bottom"), qsTr("Wipe - up left"),
                        qsTr("Wipe - up right"), qsTr("Wipe - down left"),
                        qsTr("Wipe - down right"), qsTr("Push - left"), qsTr("Push"),
                        qsTr("Push - top"), qsTr("Push - bottom"),
                        qsTr("Circle - inwards"), qsTr("Circle"),
                        qsTr("Pan and Zoom"), qsTr("Pan and Zoom - face"),
                        qsTr("Time Lapse"), qsTr("Rectangle")]
                    currentIndex: movieDialog.transitionIndex
                    onCurrentIndexChanged: {
                        movieDialog.transitionIndex = currentIndex
                        if (typeof controller !== "undefined" && controller
                                && typeof controller.setMovieTransition === "function"
                                && currentIndex >= 0
                                && currentIndex < movieDialog.transitionKeys.length)
                            controller.setMovieTransition(
                                movieDialog.transitionKeys[currentIndex])
                    }
                    onActivated: movieDialog.transitionIndex = currentIndex
                }
                RowLayout {
                    objectName: "movieSecondsRow"
                    Layout.fillWidth: true
                    spacing: 4
                    Item { Layout.fillWidth: true }
                    Text {
                        objectName: "movieSecondsLabel"
                        text: qsTr("Slide Duration:")
                        color: Theme.ink
                    }
                    Text {
                        objectName: "movieSecondsValueLabel"
                        text: qsTr("%1 Sec").arg(
                            ((movieSeconds && movieSeconds.value !== undefined
                                ? movieSeconds.value : 40) / 10).toFixed(1))
                        color: Theme.ink
                    }
                    Item { Layout.fillWidth: true }
                }
                PicasaSlider {
                    id: movieSeconds
                    objectName: "movieSeconds"
                    Layout.preferredWidth: Math.round(parent.width * 0.5)
                    Layout.alignment: Qt.AlignHCenter
                    from: 10; to: 3000; stepSize: 5
                    value: typeof controller !== "undefined" && controller
                        && controller.movieSlideDuration !== undefined
                        ? Math.round(controller.movieSlideDuration * 10) : 40
                    onMoved: {
                        if (typeof controller !== "undefined" && controller
                                && typeof controller.setMovieSlideDuration === "function")
                            controller.setMovieSlideDuration(value / 10.0)
                    }
                    grooveThickness: 9
                    grooveInset: 3
                    handleWidth: 16
                    handleHeight: 22
                    handleRadius: 3
                    handleOffsetY: 2
                    showTicks: false
                }
                RowLayout {
                    objectName: "movieOverlapRow"
                    Layout.fillWidth: true
                    spacing: 4
                    Item { Layout.fillWidth: true }
                    Text {
                        objectName: "movieOverlapLabel"
                        text: qsTr("Overlap")
                        color: Theme.ink
                    }
                    Text {
                        objectName: "movieOverlapValueLabel"
                        text: qsTr("%1 Sec").arg(
                            (movieOverlapSlider
                                && movieOverlapSlider.value !== undefined
                                ? movieOverlapSlider.value : 0.5).toFixed(1))
                        color: Theme.ink
                    }
                    Item { Layout.fillWidth: true }
                }
                PicasaSlider {
                    id: movieOverlapSlider
                    objectName: "movieOverlapSlider"
                    Layout.preferredWidth: Math.round(parent.width * 0.5)
                    Layout.alignment: Qt.AlignHCenter
                    from: 0; to: Math.max(
                        0.1,
                        (movieSeconds && movieSeconds.value !== undefined
                            ? movieSeconds.value : 40) / 10 * 0.9)
                    value: Math.min(0.5, to); stepSize: 0.1
                    grooveThickness: 9
                    grooveInset: 3
                    handleWidth: 16
                    handleHeight: 22
                    handleRadius: 3
                    handleOffsetY: 2
                    showTicks: false
                }
                Loader {
                    objectName: "movieOptionsInMotion"
                    Layout.fillWidth: true
                    active: !movieDialog.personMovieMode
                    sourceComponent: options.optionsControls
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.maximumWidth: moviePages.width
                    Text { text: qsTr("Target file:"); color: Theme.ink }
                    Text {
                        objectName: "movieTargetLabel"
                        Layout.fillWidth: true
                        elide: Text.ElideMiddle
                        text: movieDialog.targetFile.length
                            ? movieDialog.targetFile : qsTr("(not selected)")
                        color: Theme.textGray
                    }
                    Button {
                        objectName: "movieBrowseButton"
                        text: qsTr("Browse...")
                        onClicked: movieDialog.movieDialogs.movieTargetDialog.open()
                    }
                }
                Text {
                    objectName: "movieProjectNote"
                    visible: movieDialog.projektbolNyilt
                    text: qsTr("The movie's pictures and timing come from the project file; the size starts from the default.")
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Text {
                        objectName: "movieCountLabel"
                        text: qsTr("%1 pictures selected.").arg(movieDialog.movieClipSources.length)
                        font.pixelSize: Theme.fontSize
                        color: Theme.textGray
                    }
                    Button {
                        objectName: "rewind"
                        text: qsTr("Back to selected slide")
                        Layout.fillWidth: true
                        ToolTip.text: qsTr("Back to selected slide")
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        onClicked: {
                            if (root.moviePreviewTimer)
                                root.moviePreviewTimer.stop()
                            var selected = movieClipList.currentIndex
                            if (selected < 0
                                    || selected >= movieDialog.movieClipSources.length)
                                selected = 0
                            movieDialog.setPreviewIndex(selected)
                        }
                    }
                }
            }
        }
        ScrollView {
            objectName: "tabpanel2"
            clip: true
            ColumnLayout {
                width: moviePages.width
                spacing: 8
                Text { text: qsTr("Text slide:"); color: Theme.ink }
                TextField {
                    id: movieSlideText
                    objectName: "movieSlideText"
                    Layout.fillWidth: true
                    text: qsTr("Text")
                    onTextChanged: movieDialog.updateSelectedTextSlide()
                    TextFieldContextArea {}
                    onTextEdited: movieDialog.updateSelectedText(text)
                }
                RowLayout {
                    Text { text: qsTr("Font:"); color: Theme.ink }
                    PicasaComboBox {
                        id: movieFontBox
                        objectName: "movieFontBox"
                        Layout.fillWidth: true
                        model: Qt.fontFamilies()
                        onCurrentIndexChanged: movieDialog.updateSelectedTextSlide()
                    }
                }
                RowLayout {
                    Text { text: qsTr("Size:"); color: Theme.ink }
                    PicasaComboBox {
                        id: movieTextSizeBox
                        objectName: "movieTextSizeBox"
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        model: movieDialog.textSizes.map(function(size) {
                            return String(size)
                        })
                        currentIndex: 4
                        onCurrentIndexChanged: movieDialog.updateSelectedTextSlide()
                    }
                }
                RowLayout {
                    Text { text: qsTr("Style:"); color: Theme.ink }
                    PicasaComboBox {
                        id: movieTextStyleBox
                        objectName: "movieTextStyleBox"
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        model: [qsTr("Centered"), qsTr("I'm Feeling Lucky"), qsTr("Caption"),
                            qsTr("Caption - Classic"), qsTr("Gradient - Black"),
                            qsTr("Gradient - White"), qsTr("Transparent - Black"),
                            qsTr("Transparent - White"), qsTr("Scrolling Credits"),
                            qsTr("Music Video - Left"), qsTr("Music Video - Right"),
                            qsTr("Caption - Typewriter")]
                        onCurrentIndexChanged: movieDialog.updateSelectedTextSlide()
                    }
                }
                RowLayout {
                    CheckBox {
                        id: movieBoldBox
                        objectName: "movieBoldBox"
                        text: qsTr("Bold")
                        onToggled: movieDialog.updateSelectedTextSlide()
                    }
                    CheckBox {
                        id: movieItalicBox
                        objectName: "movieItalicBox"
                        text: qsTr("Italic")
                        onToggled: movieDialog.updateSelectedTextSlide()
                    }
                }
                CheckBox {
                    Layout.fillWidth: true
                    id: movieOutlineBox
                    objectName: "movieOutlineBox"
                    text: qsTr("Automatic Outline")
                    onToggled: movieDialog.updateSelectedTextSlide()
                    ToolTip.text: qsTr("Automatic Outline (like movie subtitles)")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        objectName: "movieTextColorButton"
                        text: qsTr("Text color")
                        onClicked: movieDialog.movieDialogs.movieTextColorDialog.open()
                    }
                    Rectangle {
                        objectName: "txcolorpicker_bevel"
                        Layout.preferredWidth: 20
                        Layout.preferredHeight: 20
                        color: movieDialog.textColor
                        border.color: Theme.chromeBorder
                        border.width: 1
                        radius: 2
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        objectName: "movieBackgroundColorButton"
                        text: qsTr("Background color")
                        onClicked: movieDialog.movieDialogs.movieBackgroundColorDialog.open()
                    }
                    Button {
                        objectName: "movieInsertSlideButton"
                        text: qsTr("Insert Text Slide")
                        Layout.fillWidth: true
                        onClicked: movieDialog.openTitleDialog()
                    }
                }
                Button {
                    objectName: "movieRemoveSlideButton"
                    text: qsTr("Remove Selected Slide")
                    Layout.fillWidth: true
                    ToolTip.text: qsTr("Remove the selected slide")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: movieDialog.removeTextSlide()
                }
                Item {
                    objectName: "viewedit"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 150
                    property alias count: movieSlideList.count
                    property alias contentHeight: movieSlideList.contentHeight
                    property alias currentIndex: movieSlideList.currentIndex
                    property alias contentY: movieSlideList.contentY
            ListView {
                id: movieSlideList
                objectName: "movieSlideList"
                anchors.fill: parent
                model: movieDialog.movieSlides
                onCurrentIndexChanged: {
                    movieDialog.loadTextSlide()
                    if (currentIndex >= 0) {
                        movieClipList.currentIndex =
                            movieDialog.movieClipSources.length + currentIndex
                    }
                }
                delegate: ItemDelegate {
                    id: movieSlideDelegate
                    objectName: "movieSlideDelegate" + index
                    width: movieSlideList.width
                    text: qsTr("Text Slide")
                            highlighted: movieDialog.movieSlideSelection.indexOf(index) >= 0
                            MouseArea {
                                id: movieSlidePointer
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton
                                property real pressX: 0
                                property real pressY: 0
                                property bool dragged: false
                                onPressed: function(mouse) {
                                    var selected = movieDialog.movieSlideSelection
                                    if (mouse.modifiers & Qt.ControlModifier)
                                        movieDialog.selectTextSlide(index, mouse.modifiers)
                                    else if (selected.indexOf(index) < 0)
                                        movieDialog.selectTextSlide(index, mouse.modifiers)
                                    else
                                        movieSlideList.currentIndex = index
                                    pressX = mouse.x
                                    pressY = mouse.y
                                    dragged = false
                                }
                                onPositionChanged: function(mouse) {
                                    if (!pressed) return
                                    if (!dragged && Math.abs(mouse.x - pressX)
                                            + Math.abs(mouse.y - pressY)
                                            < Qt.styleHints.startDragDistance)
                                        return
                                    dragged = true
                                    var point = mapToItem(
                                        movieSlideList.contentItem, mouse.x, mouse.y)
                                    if (point.y < movieSlideList.contentY
                                            || point.y >= movieSlideList.contentY
                                                + movieSlideList.height) {
                                        movieDialog.removeTextSlide()
                                        return
                                    }
                                    var rowHeight = movieSlideList.count > 0
                                            ? movieSlideList.contentHeight
                                                / movieSlideList.count : height
                                    var targetIndex = Math.floor(point.y / rowHeight)
                                    targetIndex = Math.max(0, Math.min(
                                        movieSlideList.count - 1, targetIndex))
                                    if (targetIndex !== movieSlideList.currentIndex)
                                        movieDialog.moveTextSlides(targetIndex)
                                }
                                onClicked: function(mouse) {
                                    mouse.accepted = false
                                }
                                onDoubleClicked: movieDialog.editTextSlide(index)
                            }
                        }
                    }
                }
            }
        }
        Item {
            objectName: "movieTabPanelThirdPage"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            ColumnLayout {
                id: movieTabPanelClips
                objectName: "movieTabPanelClips"
                anchors.fill: parent
                spacing: 8
                visible: !movieDialog.personMovieMode
                Button {
                    objectName: "movieGetMoreClipsButton"
                    text: qsTr("Get More...")
                    Layout.fillWidth: true
                    ToolTip.text: qsTr("Get more clips from Photo Library")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: movieDialog.appWindow.openMovieClipCollector()
                }
                Loader {
                    Layout.fillWidth: true
                    active: !movieDialog.personMovieMode
                    sourceComponent: options.filterControls
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        objectName: "movieRecomputeButton"
                        text: qsTr("Recompute")
                        Layout.fillWidth: true
                        onClicked: movieDialog.recomputeMovie()
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Button {
                        objectName: "movieAddClipsButton"
                        text: qsTr("Add selected clips")
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        ToolTip.text: qsTr("Add the selected clip(s) to the end of the movie")
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        onClicked: movieDialog.addSelectedClips()
                    }
                    Button {
                        objectName: "movieDeleteClipButton"
                        text: qsTr("Remove selected clip")
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        ToolTip.text: qsTr("Remove the selected clip(s) from the tray")
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        onClicked: movieDialog.deleteSelectedClip()
                    }
                }
                CheckBox {
                    id: movieSoloClip
                    objectName: "movieSoloClip"
                    text: qsTr("Play selected clip only")
                    Layout.fillWidth: true
                }
                ListView {
                    id: movieClipList
                    objectName: "movieClipList"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: movieDialog.movieFilmstripItems
                    delegate: ItemDelegate {
                        objectName: "movieClipDelegate" + index
                        width: movieClipList.width
                        text: modelData.name
                        onClicked: movieDialog.selectMovieFilmstripItem(index)
                    }
                }
            }
            Loader {
                objectName: "movieTabPanelOptions"
                anchors.fill: parent
                active: movieDialog.personMovieMode
                sourceComponent: options.faceOptionsPage
            }
        }
    }
    }
}
}

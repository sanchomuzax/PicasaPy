import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: root
    required property var movieDialog
    required property real pagesWidth
    property alias optionsControls: movieOptionsControls
    property alias faceOptionsPage: movieFaceOptionsPage
    property alias filterControls: movieFilterControls

Component {
    id: movieOptionsControls
    ColumnLayout {
        width: root.pagesWidth
        spacing: 1
        Text {
            objectName: "moviesize_label"
            text: qsTr("Dimensions")
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            color: Theme.ink
        }
        PicasaComboBox {
            id: movieHeightBox
            objectName: "movieHeightBox"
            Layout.fillWidth: true
            model: ["320x240", "640x480", "800x600",
                "1024x768", "1600x1200", "1280x720 (720p)",
                "1920x1080 (1080p)"]
            currentIndex: movieDialog.movieResolutionIndex
            onCurrentIndexChanged: movieDialog.movieResolutionIndex = currentIndex
            // #4391: a Picasa az arc-film felbontását nem menti vissza;
            // csak a normál film írja a saját kulcsát.
            onActivated: {
                if (!movieDialog.personMovieMode)
                    controller.setMovieResolutionIndex(currentIndex)
                movieDialog.requestPreviewFrame()
            }
        }
        CheckBox {
            id: movieShowCaptions
            objectName: "movieShowCaptions"
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            topPadding: 0
            bottomPadding: 0
            text: qsTr("Show Captions")
            font.pixelSize: Theme.fontSize - 4
            checked: movieDialog.movieShowCaptionsEnabled
            onCheckedChanged:
                movieDialog.movieShowCaptionsEnabled = checked
            onToggled: {
                if (controller && typeof controller.setMoviePreference === "function")
                    controller.setMoviePreference("captions", checked)
                movieDialog.requestPreviewFrame()
            }
        }
        CheckBox {
            id: movieCropToFit
            objectName: "movieCropToFit"
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            topPadding: 0
            bottomPadding: 0
            text: qsTr("Full frame photo crop")
            font.pixelSize: Theme.fontSize - 4
            checked: movieDialog.movieCropToFitEnabled
            onCheckedChanged:
                movieDialog.movieCropToFitEnabled = checked
            onToggled: {
                if (controller && typeof controller.setMoviePreference === "function")
                    controller.setMoviePreference("cropfit", checked)
                movieDialog.requestPreviewFrame()
            }
        }
        CheckBox {
            id: movieShowDates
            objectName: "movieShowDates"
            Layout.fillWidth: true
            text: qsTr("Show Dates")
            checked: movieDialog.movieShowDatesEnabled
            onCheckedChanged:
                movieDialog.movieShowDatesEnabled = checked
            onToggled: {
                movieDialog.requestPreviewFrame()
            }
        }
        CheckBox {
            id: movieRemoveLowResFaces
            objectName: "movieRemoveLowResFaces"
            Layout.fillWidth: true
            text: qsTr("Remove Low Resolution Faces")
            checked: movieDialog.movieRemoveLowResFacesEnabled
            onCheckedChanged:
                movieDialog.movieRemoveLowResFacesEnabled = checked
            onToggled: {
                if (controller && typeof controller.setMoviePreference === "function")
                    controller.setMoviePreference("removeLowResFaces", checked)
            }
        }
        Flow {
            Layout.fillWidth: true
            Layout.maximumWidth: root.pagesWidth
            spacing: 8
            Text {
                objectName: "ordering_header_label"
                text: qsTr("Ordering of Slides:")
                color: Theme.ink
            }
            RadioButton {
                id: movieSmartOrder
                objectName: "movieSmartOrder"
                text: qsTr("Best Transitions")
                checked: movieDialog.movieOrdering === 0
                onCheckedChanged:
                    if (checked) movieDialog.movieOrdering = 0
                onToggled: if (checked) movieDialog.movieOrdering = 0
            }
            RadioButton {
                objectName: "movieAlbumOrder"
                text: qsTr("Album Order")
                checked: movieDialog.movieOrdering === 1
                onCheckedChanged:
                    if (checked) movieDialog.movieOrdering = 1
                onToggled: if (checked) movieDialog.movieOrdering = 1
            }
            RadioButton {
                id: movieChronologicalOrder
                objectName: "movieChronologicalOrder"
                text: qsTr("Chronological")
                checked: movieDialog.movieOrdering === 2
                onCheckedChanged:
                    if (checked) movieDialog.movieOrdering = 2
                onToggled: if (checked) movieDialog.movieOrdering = 2
            }
        }
    }
}
Component {
    id: movieFilterControls
    ColumnLayout {
        width: root.pagesWidth
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "lengthslider_label"
                text: qsTr("Total Photos")
                color: Theme.ink
            }
            Slider {
                id: movieLengthSlider
                objectName: "lengthslider/scaleslider"
                Layout.fillWidth: true
                from: 0; to: 1
                value: movieDialog.movieLengthFactor
                onValueChanged: movieDialog.movieLengthFactor = value
            }
            Text {
                objectName: "movieLengthCount"
                text: String(movieDialog.movieUsedPhotoCount)
                color: Theme.textGray
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "burstslider_label"
                text: movieDialog.movieBurstFactor === 0
                    ? qsTr("Don't filter by time taken")
                    : qsTr("Remove Photos Taken Within %1")
                        .arg(movieDialog.movieBurstThresholdSeconds)
                color: Theme.ink
            }
            Slider {
                id: movieBurstSlider
                objectName: "burstslider/scaleslider"
                Layout.fillWidth: true
                from: 0; to: 1
                value: movieDialog.movieBurstFactor
                onValueChanged: movieDialog.movieBurstFactor = value
            }
        }
    }
}
Component {
    id: movieFaceOptionsPage
    ScrollView {
        clip: true
        ScrollBar.vertical: ScrollBar {
            objectName: "movieOptionsScrollBar"
        }
        ColumnLayout {
            width: root.pagesWidth
            spacing: 8
            Loader {
                Layout.fillWidth: true
                sourceComponent: movieOptionsControls
            }
            Loader {
                Layout.fillWidth: true
                sourceComponent: movieFilterControls
            }
            Button {
                objectName: "movieOptionsGetMoreClipsButton"
                text: qsTr("Get More...")
                Layout.fillWidth: true
                ToolTip.text: qsTr("Get more clips from Photo Library")
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                onClicked: movieDialog.appWindow.openMovieClipCollector()
            }
            Button {
                objectName: "movieOptionsRecomputeButton"
                text: qsTr("Recompute")
                Layout.fillWidth: true
                onClicked: movieDialog.recomputeMovie()
            }
        }
    }
}
}

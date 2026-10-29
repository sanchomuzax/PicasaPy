import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: root
    anchors.fill: parent
    required property var movieDialog
    property alias movieReplaceDialog: movieReplaceDialog
    property alias movieTitleDialog: movieTitleDialog
    property alias movieTargetDialog: movieTargetDialog
    property alias movieAudioDialog: movieAudioDialog
    property alias movieTextColorDialog: movieTextColorDialog
    property alias movieBackgroundColorDialog: movieBackgroundColorDialog
    property alias movieProgressDialog: movieProgressDialog

Dialog {
    id: movieReplaceDialog
    objectName: "movieReplaceDialog"
    modal: true
    title: qsTr("Replace Existing or Create New?")
    closePolicy: Popup.CloseOnEscape
    anchors.centerIn: parent ? Overlay.overlay : undefined

    RowLayout {
        spacing: 8

        PicasaButton {
            objectName: "movieReplaceExistingButton"
            text: qsTr("Replace Existing")
            accent: Theme.picasaGreen
            onClicked: {
                movieReplaceDialog.close()
                movieDialog.replacePreviousMovie()
            }
        }
        PicasaButton {
            objectName: "movieCreateNewButton"
            text: qsTr("Create New")
            onClicked: {
                movieReplaceDialog.close()
                movieDialog.createNewMovie()
            }
        }
        PicasaButton {
            objectName: "movieReplaceCancelButton"
            text: qsTr("Cancel")
            onClicked: movieReplaceDialog.close()
        }
    }
}

MovieTitleDialog {
    id: movieTitleDialog
    textColor: movieDialog.textColor
    backgroundColor: movieDialog.backgroundColor
    previewAspectRatio: {
        var selectedSize = movieDialog.sizeOptions[movieDialog.movieResolutionIndex]
        return selectedSize[0] / selectedSize[1]
    }
    onSlideAdded: function(slide) { movieDialog.addTextSlide(slide) }
    onTextColorRequested: movieTextColorDialog.open()
    onBackgroundColorRequested: movieBackgroundColorDialog.open()
}

FileDialog {
    id: movieTargetDialog
    title: qsTr("Movie")
    fileMode: FileDialog.SaveFile
    defaultSuffix: "mp4"
    nameFilters: [qsTr("MP4 videos (*.mp4)")]
    onAccepted: movieDialog.targetFile = selectedFile.toString()
}

FileDialog {
    id: movieAudioDialog
    objectName: "movieAudioDialog"
    title: qsTr("Audio files")
    fileMode: FileDialog.OpenFile
    nameFilters: [
        Qt.platform.os === "windows"
            ? qsTr("Music files (*.mp3, *.wma)")
            : qsTr("Music files (*.mp3, *.m4a)"),
    ]
    onAccepted: {
        movieDialog.audioFile = selectedFile.toString()
        movieDialog.audioFileFromFolderMusic = false
    }
}

ColorDialog {
    id: movieTextColorDialog
    objectName: "text_picker_panel"
    title: qsTr("Text color")
    selectedColor: movieDialog.textColor
    onAccepted: movieDialog.textColor = selectedColor
}
ColorDialog {
    id: movieBackgroundColorDialog
    objectName: "bkg_picker_panel"
    title: qsTr("Background color")
    selectedColor: movieDialog.backgroundColor
    onAccepted: movieDialog.backgroundColor = selectedColor
}

// A film írása képenként halad — a Picasa is mutatja a haladást;
// a dialógus a movieFinished/movieFailed jelzésre záródik.
Dialog {
    id: movieProgressDialog
    objectName: "movieProgressDialog"
    title: qsTr("Movie")
    modal: true
    closePolicy: Popup.NoAutoClose
    anchors.centerIn: parent
    property int done: 0
    property int total: 0
    ColumnLayout {
        spacing: 8
        Text {
            objectName: "movieProgressText"
            text: qsTr("Creating movie: %1 / %2").arg(
                movieProgressDialog.done).arg(movieProgressDialog.total)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredWidth: 240
            Layout.preferredHeight: 8
            radius: 4
            color: Theme.trackBg
            border.color: Theme.chromeBorder
            Rectangle {
                height: parent.height
                radius: parent.radius
                color: Theme.picasaGreen
                width: movieProgressDialog.total > 0
                       ? parent.width * movieProgressDialog.done
                         / movieProgressDialog.total
                       : 0
            }
        }
    }
}
}

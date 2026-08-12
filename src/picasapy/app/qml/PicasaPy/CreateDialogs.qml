import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Létrehozás menü (#29): képkollázs és mozgófilm a kijelölt képekből.
// Az ExportDialogs.qml mintája szerint: beállítás-dialógus → fájlválasztó
// → háttérszálas munka → eredmény-dialógus (controller-jelzésekre).
Item {
    id: dialogs
    anchors.fill: parent

    // a főablak (a kijelölt sorok forrása)
    required property var appWindow

    // a kollázs-típusok sorrendje a ComboBox-szal egyezik
    readonly property var collageKinds: ["grid", "contact_sheet", "mosaic", "pile"]

    function openCollage() { collageDialog.openForSelection() }
    function openMovie() { movieDialog.openForSelection() }

    Dialog {
        id: collageDialog
        objectName: "collageDialog"
        title: qsTr("Picture Collage...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetFile: ""
        function openForSelection() {
            if (dialogs.appWindow.selectedIndexes.length === 0) return
            open()
        }
        onOpened: standardButton(Dialog.Ok).enabled = Qt.binding(
            function() { return collageDialog.targetFile.length > 0 })
        onAccepted: controller.makeCollage(
            dialogs.appWindow.selectedIndexes,
            dialogs.collageKinds[collageKindBox.currentIndex],
            collageDialog.targetFile)
        ColumnLayout {
            spacing: 10
            Text {
                objectName: "collageCountLabel"
                text: qsTr("%1 pictures selected.").arg(
                    dialogs.appWindow.selectedIndexes.length)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Collage type:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: collageKindBox
                    objectName: "collageKindBox"
                    Layout.preferredWidth: 180
                    model: [qsTr("Picture Grid"), qsTr("Contact Sheet"),
                            qsTr("Frame Mosaic"), qsTr("Picture Pile")]
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Target file:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Text {
                    objectName: "collageTargetLabel"
                    Layout.preferredWidth: 240
                    elide: Text.ElideMiddle
                    text: collageDialog.targetFile.length > 0
                          ? collageDialog.targetFile
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    text: qsTr("Browse...")
                    onClicked: collageTargetDialog.open()
                }
            }
        }
    }

    FileDialog {
        id: collageTargetDialog
        title: qsTr("Picture Collage...")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "jpg"
        nameFilters: [qsTr("JPEG images (*.jpg)")]
        onAccepted: collageDialog.targetFile = selectedFile.toString()
    }

    Dialog {
        id: movieDialog
        objectName: "movieDialog"
        title: qsTr("Movie")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetFile: ""
        // a felbontás-lista indexei → videó-magasság
        readonly property var heightOptions: [720, 1080]
        function openForSelection() {
            if (dialogs.appWindow.selectedIndexes.length === 0) return
            open()
        }
        onOpened: standardButton(Dialog.Ok).enabled = Qt.binding(
            function() { return movieDialog.targetFile.length > 0 })
        onAccepted: {
            movieProgressDialog.done = 0
            movieProgressDialog.total = dialogs.appWindow.selectedIndexes.length
            movieProgressDialog.open()
            controller.exportMovie(
                dialogs.appWindow.selectedIndexes, movieDialog.targetFile,
                movieDialog.heightOptions[movieHeightBox.currentIndex],
                movieSeconds.value / 10.0)
        }
        ColumnLayout {
            spacing: 10
            Text {
                objectName: "movieCountLabel"
                text: qsTr("%1 pictures selected.").arg(
                    dialogs.appWindow.selectedIndexes.length)
                font.pixelSize: Theme.fontSize
                color: Theme.textGray
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Video size:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                ComboBox {
                    id: movieHeightBox
                    objectName: "movieHeightBox"
                    Layout.preferredWidth: 160
                    model: ["720p", "1080p"]
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Seconds per picture:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                SpinBox {
                    id: movieSeconds
                    objectName: "movieSeconds"
                    // tizedmásodperc-felbontás: 1,0–10,0 mp
                    from: 10; to: 100; stepSize: 5; value: 30
                    textFromValue: function(value) {
                        return (value / 10.0).toFixed(1)
                    }
                    valueFromText: function(text) {
                        return Math.round(parseFloat(text) * 10)
                    }
                }
            }
            RowLayout {
                spacing: 8
                Text {
                    text: qsTr("Target file:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                Text {
                    objectName: "movieTargetLabel"
                    Layout.preferredWidth: 240
                    elide: Text.ElideMiddle
                    text: movieDialog.targetFile.length > 0
                          ? movieDialog.targetFile
                          : qsTr("(not selected)")
                    font.pixelSize: Theme.fontSize
                    color: Theme.textGray
                }
                PicasaButton {
                    text: qsTr("Browse...")
                    onClicked: movieTargetDialog.open()
                }
            }
        }
    }

    FileDialog {
        id: movieTargetDialog
        title: qsTr("Movie")
        fileMode: FileDialog.SaveFile
        defaultSuffix: "mp4"
        nameFilters: [qsTr("MP4 videos (*.mp4)")]
        onAccepted: movieDialog.targetFile = selectedFile.toString()
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

    Dialog {
        id: createResultDialog
        objectName: "createResultDialog"
        title: qsTr("Create")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            objectName: "createResultText"
            text: createResultDialog.message
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            wrapMode: Text.WordWrap
            width: 360
        }
    }

    // #459/3: a hiányzó fájl KÜLÖN mondatot kap az eredeti Picasa
    // szövegével — az megmondja, mi történhetett, és a munka a maradékkal
    // elkészül. Az olvashatatlan (de meglévő) fájlok a régi, semleges
    // „kihagyva" mondatban maradnak.
    function _skippedSuffix(skipped, missing) {
        var text = ""
        if (missing > 0)
            text += "\n" + qsTr("%1 picture(s) could not be found and will not be shown. (The missing files must have been moved, renamed or deleted)").arg(missing)
        var unreadable = skipped - missing
        if (unreadable > 0)
            text += "\n" + qsTr("%1 pictures were skipped.").arg(unreadable)
        return text
    }

    Connections {
        target: controller
        function onCollageFinished(path, used, skipped, missing) {
            createResultDialog.message =
                qsTr("Collage saved: %1").arg(path)
                + "\n" + qsTr("%1 pictures used.").arg(used)
                + dialogs._skippedSuffix(skipped, missing)
            createResultDialog.open()
        }
        function onCollageFailed(message) {
            createResultDialog.message =
                qsTr("The collage could not be created.") + "\n" + message
            createResultDialog.open()
        }
        function onMovieProgress(done, total) {
            movieProgressDialog.done = done
            movieProgressDialog.total = total
        }
        function onMovieFinished(path, used, skipped, missing) {
            movieProgressDialog.close()
            createResultDialog.message =
                qsTr("Movie saved: %1").arg(path)
                + "\n" + qsTr("%1 pictures used.").arg(used)
                + dialogs._skippedSuffix(skipped, missing)
            createResultDialog.open()
        }
        function onMovieFailed(message) {
            movieProgressDialog.close()
            createResultDialog.message =
                qsTr("The movie could not be created.") + "\n" + message
            createResultDialog.open()
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

Item {
    id: root
    anchors.fill: parent
    required property var appWindow
    required property bool trayHasPictures
    required property var collageKinds
    required property var collageBorders
    required property var collageBorderCapable
    property alias dialog: collageDialog
    property alias targetPicker: collageTargetDialog
    property alias previewRevision: collageDialog.previewRevision
    function openForSelection() { collageDialog.openForSelection() }

Dialog {
    id: collageDialog
    objectName: "collageDialog"
    title: qsTr("Picture Collage...")
    modal: true
    anchors.centerIn: parent
    standardButtons: Dialog.Ok | Dialog.Cancel
    property string targetFile: ""
    // #922: hány kép lesz ténylegesen a kollázsban — a tálca ELŐBBRE
    // való a kijelölésnél, ugyanúgy, ahogy a vezérlő `_sources_for`-ja
    // dönt (#455). Ebből él a tipp és az OK is.
    readonly property int sourceCount:
        root.trayHasPictures
            ? ((typeof controller !== "undefined" && controller
                && controller.heldCount !== undefined)
                ? controller.heldCount : 0)
            : root.appWindow.selectedIndexes.length
    // #920: élő előnézet — a Kollázs eddig VAKON dolgozott: a
    // felhasználó választott, a program fájlba renderelt, és csak utána
    // derült ki, mit kapott.
    property int previewRevision: 0
    function refreshPreview() {
        if (!(typeof controller !== "undefined" && controller)) return
        controller.requestCollagePreview(
            root.appWindow.selectedIndexes,
            root.collageKinds[collageKindBox.currentIndex],
            root.collageBorders[collageBorderBox.currentIndex])
    }
    function openForSelection() {
        // #922: MINDIG megnyílik. Korábban forrás nélkül némán
        // visszatért, és a kattintás nyomtalanul elnyelődött — az
        // eredeti Picasában ilyen nincs, az megnyitja a lapot és
        // megmondja, mi hiányzik.
        open()
        refreshPreview()
    }
    onOpened: standardButton(Dialog.Ok).enabled = Qt.binding(
        function() {
            return collageDialog.targetFile.length > 0
                   && collageDialog.sourceCount > 0
        })
    onAccepted: {
        if (!(typeof controller !== "undefined" && controller)) return
        controller.makeCollage(
            root.appWindow.selectedIndexes,
            root.collageKinds[collageKindBox.currentIndex],
            collageDialog.targetFile,
            root.collageBorders[collageBorderBox.currentIndex])
    }
    ColumnLayout {
        spacing: 10
        Text {
            objectName: "collageNoSourceHint"
            visible: collageDialog.sourceCount === 0
            text: qsTr("Select pictures in the library first, or put them in the Picture Tray.")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            wrapMode: Text.WordWrap
            Layout.preferredWidth: 320
        }
        Text {
            objectName: "collageCountLabel"
            text: qsTr("%1 pictures selected.").arg(
                root.appWindow.selectedIndexes.length)
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }
        // #920: az élő előnézet — ez az, ami eddig hiányzott
        Image {
            objectName: "collagePreviewImage"
            Layout.preferredWidth: 320
            Layout.preferredHeight: 240
            fillMode: Image.PreserveAspectFit
            cache: false
            visible: collageDialog.sourceCount > 0
            source: collageDialog.previewRevision > 0
                    ? "image://collagepreview/kollazs?rev=" + collageDialog.previewRevision
                    : ""
        }
        Button {
            objectName: "collageShuffleButton"
            text: qsTr("Scramble Collage")
            visible: collageDialog.sourceCount > 0
            onClicked: {
                if (!(typeof controller !== "undefined" && controller)) return
                controller.shuffleCollage()
                collageDialog.refreshPreview()
            }
        }
        RowLayout {
            spacing: 8
            Text {
                text: qsTr("Collage type:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: collageKindBox
                objectName: "collageKindBox"
                Layout.preferredWidth: 180
                // az eredeti Picasa nevei és sorrendje
                model: [qsTr("Picture Pile"), qsTr("Mosaic"),
                        qsTr("Frame Mosaic"), qsTr("Grid"),
                        qsTr("Contact Sheet"), qsTr("Multiple Exposure")]
                onCurrentIndexChanged: collageDialog.refreshPreview()
            }
        }
        RowLayout {
            spacing: 8
            Text {
                text: qsTr("Picture borders:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            PicasaComboBox {
                id: collageBorderBox
                objectName: "collageBorderBox"
                Layout.preferredWidth: 180
                model: [qsTr("None"), qsTr("White Border"), qsTr("Polaroid")]
                enabled: root.collageBorderCapable[collageKindBox.currentIndex]
                onCurrentIndexChanged: collageDialog.refreshPreview()
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
}

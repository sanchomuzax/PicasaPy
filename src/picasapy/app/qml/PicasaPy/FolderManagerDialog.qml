import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Mappakezelő (Eszközök menü + első indítás) — a Picasa 3.9 dialógusának
// MVP-változata: figyelt mappák listája, hozzáadás rendszer-választóval,
// „Eltávolítás a Picasából". (A teljes mappafa há­romállapotú jelölőkkel a
// dizájn-polírozási hiánylistán.)
Dialog {
    id: manager
    objectName: "folderManagerDialog"
    title: qsTr("Folder Manager")
    modal: true
    width: 560
    height: 400
    anchors.centerIn: parent
    standardButtons: Dialog.Ok

    property int selectedRow: -1

    RowLayout {
        anchors.fill: parent
        spacing: 14

        Text {
            Layout.preferredWidth: 200
            Layout.alignment: Qt.AlignTop
            text: qsTr(
                "Choose which folders PicasaPy watches. New and changed "
                + "pictures in watched folders appear automatically.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 6

            Text {
                text: qsTr("Watched folders")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.ink
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#ffffff"
                border.color: Theme.chromeBorder
                ListView {
                    id: watchedList
                    anchors.fill: parent
                    anchors.margins: 1
                    clip: true
                    model: controller.watchedFolders
                    delegate: Rectangle {
                        required property string modelData
                        required property int index
                        width: watchedList.width
                        height: 24
                        color: manager.selectedRow === index
                               ? Theme.selectionBlue : "transparent"
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left
                            anchors.leftMargin: 8
                            text: modelData
                            elide: Text.ElideMiddle
                            width: parent.width - 16
                            font.pixelSize: Theme.fontSize
                            color: manager.selectedRow === index
                                   ? "#ffffff" : Theme.ink
                        }
                        TapHandler {
                            onTapped: manager.selectedRow = index
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}
                }
            }
            RowLayout {
                spacing: 8
                PicasaButton {
                    text: qsTr("Add folder...")
                    onClicked: pickFolder.open()
                }
                PicasaButton {
                    text: qsTr("Remove from Picasa")
                    enabled: manager.selectedRow >= 0
                    onClicked: {
                        controller.removeWatchedFolder(
                            controller.watchedFolders[manager.selectedRow])
                        manager.selectedRow = -1
                    }
                }
                // #146: a régi Picasa figyelt mappáinak felajánlása — a
                // PicasaImportDialog a Main.qml-ben él, a discoveryController
                // globális jelzésén (dialogRequested) keresztül nyílik meg
                PicasaButton {
                    objectName: "adoptPicasaFoldersButton"
                    text: qsTr("Adopt Picasa folders...")
                    onClicked: discoveryController.openImportDialog()
                }
            }
        }
    }

    FolderDialog {
        id: pickFolder
        title: qsTr("Add folder...")
        onAccepted: controller.addWatchedFolder(selectedFolder.toString())
    }
}

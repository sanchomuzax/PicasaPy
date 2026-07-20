import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// Fájlművelet-dialógusok (#15, #150-ben kiemelve a Main.qml-ből):
// átnevezés (F2), áthelyezés mappába, lomtárba törlés megerősítéssel,
// hiba-visszajelzés. A tényleges műveletek a fileOpsController slotjai;
// a sikeres művelet utáni resync a Python-oldali bekötés (wire_fileops)
// dolga.
Item {
    id: dialogs
    anchors.fill: parent

    // a főablak (kijelölés-ürítés a műveletek után)
    required property var appWindow

    function openRename(row) {
        renameDialog.openFor(row)
    }
    function openMove(paths) {
        moveFolderDialog.paths = paths
        if (moveFolderDialog.paths.length > 0) moveFolderDialog.open()
    }
    function openDelete(paths) {
        deleteConfirmDialog.openFor(paths)
    }

    Dialog {
        id: renameDialog
        objectName: "renameDialog"
        title: qsTr("Rename...")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        property string targetPath: ""
        function openFor(row) {
            var p = controller.photos.filePathAt(row)
            if (p.length === 0) return
            targetPath = p
            renameField.text = controller.photos.itemAt(row).name || ""
            open()
            renameField.forceActiveFocus()
            renameField.selectAll()
        }
        onAccepted: {
            if (renameField.text.trim().length > 0)
                fileOpsController.renamePhoto(
                    targetPath, renameField.text.trim())
        }
        TextField {
            id: renameField
            objectName: "renameField"
            width: 300
            font.pixelSize: Theme.fontSize
        }
    }

    FolderDialog {
        id: moveFolderDialog
        objectName: "moveFolderDialog"
        title: qsTr("Move to Folder...")
        property var paths: []
        onAccepted: {
            var dest = selectedFolder.toString()
            for (var i = 0; i < paths.length; ++i)
                fileOpsController.movePhoto(paths[i], dest)
            dialogs.appWindow.clearSelection()
        }
    }

    Dialog {
        id: deleteConfirmDialog
        objectName: "deleteConfirmDialog"
        title: qsTr("Delete from Disk")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Yes | Dialog.No
        property var paths: []
        function openFor(pathList) {
            if (pathList.length === 0) return
            paths = pathList
            open()
        }
        onAccepted: {
            for (var i = 0; i < paths.length; ++i)
                fileOpsController.deletePhoto(paths[i])
            dialogs.appWindow.clearSelection()
        }
        Text {
            text: qsTr("%n picture(s) will be moved to the system trash.",
                       "", deleteConfirmDialog.paths.length)
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Dialog {
        id: fileOpsErrorDialog
        objectName: "fileOpsErrorDialog"
        title: qsTr("File operation failed")
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        property string message: ""
        Text {
            width: 380
            text: fileOpsErrorDialog.message
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
    }

    Connections {
        target: fileOpsController
        function onOperationFailed(operation, message) {
            fileOpsErrorDialog.message = message
            fileOpsErrorDialog.open()
        }
    }
}

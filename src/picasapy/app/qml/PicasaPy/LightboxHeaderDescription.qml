import QtQuick
import QtQuick.Layouts

// A fénytábla fejlécének leírás-sora (#6104): a szerkeszthető mappa-leírás.
// szerkeszthető leírás-sor - Esc/elfogadás után Qt.binding()-gel újra
// be kell kötni, ahogy a PhotoViewer captionField-je is (a gépeléskor
// a Qt eltávolítja a deklaratív kötést a text property-ről). A
// placeholder-szöveg a mezőre fedve jelenik meg, amíg üres.
Item {
    required property var header

    Layout.leftMargin: header.personAlbumFolderMode ? 24 : 28
    Layout.topMargin: header.personAlbumFolderMode ? 22 : 6
    Layout.fillWidth: true
    visible: !header.personAlbumHeaderMode
    implicitHeight: descriptionField.implicitHeight

    TextInput {
        id: descriptionField
        objectName: "folderDescriptionField"
        anchors.left: parent.left
        anchors.right: parent.right
        text: header.description
        color: Theme.folderDate
        font.pixelSize: Theme.fontSize + 1
        selectByMouse: true

        function rebind() {
            text = Qt.binding(function () { return header.description })
        }

        onAccepted: {
            header.descriptionEdited(text)
            rebind()
            focus = false
        }
        Keys.onEscapePressed: (event) => {
            rebind()
            focus = false
            event.accepted = true
        }
    }
    Text {
        anchors.left: parent.left
        text: qsTr("Add a description")
        color: Theme.addDescription
        font.pixelSize: Theme.fontSize + 1
        font.italic: true
        visible: descriptionField.text.length === 0 && !descriptionField.activeFocus
    }
}

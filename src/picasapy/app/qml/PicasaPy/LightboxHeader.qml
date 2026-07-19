import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Indexkép-csoport fejléce — dizajnkézikönyv 08: cím 16px/600 tintával,
// jobbra mono SZINKRON-jelvény, alatta dőlt „Leírás hozzáadása".
ColumnLayout {
    id: header
    property string folderName: ""
    property string dateText: ""
    property string description: ""
    signal descriptionEdited(string text)
    // zöld ▸: a mappa diavetítése (#8) — a bekötés a Main.qml-ben
    signal playRequested()
    spacing: 3

    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        FolderIcon { size: 20; Layout.alignment: Qt.AlignVCenter }
        Text {
            text: header.folderName
            color: Theme.folderTitle
            font.pixelSize: Theme.folderTitleSize
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
        Text {
            text: qsTr("SYNC")
            visible: false   // webalbum-szinkron nem cél; a helye megvan
            color: Theme.picasaGreen
            font.family: Theme.monoFamily
            font.pixelSize: 11
        }
    }

    Text {
        visible: header.dateText !== ""
        text: header.dateText
        color: Theme.folderDate
        font.pixelSize: Theme.fontSize
        Layout.leftMargin: 28
    }

    RowLayout {
        Layout.leftMargin: 28
        Layout.topMargin: 4
        spacing: 6
        Rectangle {
            objectName: "headerPlayButton"
            width: 26; height: 22; radius: 3
            color: headerPlayHover.hovered ? "#f0f0ee" : "#ffffff"
            border.color: Theme.chromeBorder
            Text {
                anchors.centerIn: parent
                text: "▸"; color: Theme.picasaGreen; font.pixelSize: 13
            }
            HoverHandler { id: headerPlayHover }
            TapHandler { onTapped: header.playRequested() }
        }
        Rectangle {
            width: 26; height: 22; radius: 3
            color: "#ffffff"; border.color: Theme.chromeBorder
            Text { anchors.centerIn: parent; text: "☆"; color: "#a0a0a0"; font.pixelSize: 13 }
        }
        PicasaButton {
            text: qsTr("Upload") + " ▾"
            enabled: false
            Layout.preferredHeight: 22
        }
    }

    // szerkeszthető leírás-sor — Esc/elfogadás után Qt.binding()-gel újra
    // be kell kötni, ahogy a PhotoViewer captionField-je is (a gépeléskor
    // a Qt eltávolítja a deklaratív kötést a text property-ről). A
    // placeholder-szöveg a mezőre fedve jelenik meg, amíg üres.
    Item {
        Layout.leftMargin: 28
        Layout.topMargin: 6
        Layout.fillWidth: true
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
}

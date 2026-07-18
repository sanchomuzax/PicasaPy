import QtQuick
import QtQuick.Controls

// Mappa-fejléc a lightboxban: sárga mappa-ikon, barna SZERIF cím, hosszú
// dátum, zöld lejátszó + műveletsor, "Leírás hozzáadása" — Picasa 3.9 minta.
Column {
    id: header
    property string folderName: ""
    property string dateText: ""
    spacing: 2

    Row {
        spacing: 8
        Text { text: "📁"; font.pixelSize: 22 }
        Column {
            spacing: 1
            Text {
                text: header.folderName
                color: Theme.folderTitle
                font.family: "Georgia"
                font.pixelSize: Theme.folderTitleSize
            }
            Text {
                visible: header.dateText !== ""
                text: header.dateText
                color: Theme.folderDate
                font.family: "Georgia"
                font.pixelSize: Theme.fontSize
            }
        }
    }

    Item { width: 1; height: 6 }

    Row {
        spacing: 6
        Rectangle {
            width: 26; height: 22; radius: 3
            color: "#ffffff"; border.color: Theme.chromeBorder
            Text {
                anchors.centerIn: parent
                text: "▶"; color: Theme.playGreen; font.pixelSize: 12
            }
        }
        Rectangle {
            width: 26; height: 22; radius: 3
            color: "#ffffff"; border.color: Theme.chromeBorder
            Text { anchors.centerIn: parent; text: "★"; color: "#c0c0c0"; font.pixelSize: 12 }
        }
        Button {
            text: qsTr("Upload")
            enabled: false
            height: 22
            font.pixelSize: Theme.fontSize
        }
    }

    Item { width: 1; height: 8 }

    Text {
        text: qsTr("Add a description")
        color: Theme.addDescription
        font.pixelSize: Theme.fontSize
    }
}

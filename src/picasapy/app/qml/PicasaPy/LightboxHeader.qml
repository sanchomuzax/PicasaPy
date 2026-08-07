import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Indexkép-csoport fejléce — dizajnkézikönyv 08 + #423 (a Picasa saját
// `headerpanel.tre` respack-forrása szerinti tipográfia és elrendezés):
//   - cím: Georgia 20pt, a fejléc bal szélétől 50px behúzva (a mappa-ikon
//     UTÁN), jobbról a fejléc szélétől 20px-re levágva — hosszú névnél
//     halványuló kifutással, NEM "…"-tal;
//   - dátumsor: Georgia 14pt, ugyanaz a 50px-es bal behúzás;
//   - jobb-felső sarok: „Szinkronizálás az internettel" felirat + kapcsoló
//     (letiltott, funkció nélkül — csak az elrendezés része).
ColumnLayout {
    id: header
    property string folderName: ""
    property string dateText: ""
    property string description: ""
    signal descriptionEdited(string text)
    // zöld ▸: a mappa diavetítése (#8) — a bekötés a Main.qml-ben
    signal playRequested()
    spacing: 3

    // -- címsor: mappa-ikon + cím (50px behúzás) + jobb-felső szinkron-kapcsoló --
    Item {
        id: titleRow
        Layout.fillWidth: true
        implicitHeight: Math.max(titleClip.height, syncRow.implicitHeight) + 4

        FolderIcon {
            id: folderIcon
            size: 20
            anchors.left: parent.left
            anchors.leftMargin: 8
            anchors.verticalCenter: titleClip.verticalCenter
        }

        // a cím levágó/halványító konténere: bal szél 50px, jobb szél a
        // fejléc szélétől 20px-re (a szinkron-sor előtt) — a `#423`
        // respack-kényszer (`album_title`, `album_title_clip`) tükre
        Item {
            id: titleClip
            objectName: "folderTitleClip"
            x: 50
            y: 2
            width: Math.max(
                0, titleRow.width - 50 - 20 - syncRow.implicitWidth - 8)
            height: titleText.implicitHeight
            clip: true

            Text {
                id: titleText
                objectName: "folderTitleText"
                text: header.folderName
                color: Theme.folderTitle
                font.family: "Georgia"
                font.pointSize: 20
                font.weight: Font.DemiBold
            }

            // halványuló kifutás hosszú mappanévnél — NEM "…" (a Picasa
            // eredeti `title_fade0/1` rétegeinek tükre)
            Rectangle {
                objectName: "folderTitleFade"
                visible: titleText.implicitWidth > titleClip.width
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: 24
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop {
                        position: 0.0
                        color: Qt.rgba(
                            Theme.lightboxBg.r, Theme.lightboxBg.g,
                            Theme.lightboxBg.b, 0.0)
                    }
                    GradientStop { position: 1.0; color: Theme.lightboxBg }
                }
            }
        }

        // jobb-felső: „Szinkronizálás az internettel" + kapcsoló — csak
        // elrendezés, letiltott (#423: funkció nélkül, funkció majd később)
        Row {
            id: syncRow
            objectName: "folderSyncRow"
            anchors.right: parent.right
            anchors.top: parent.top
            spacing: 4
            Text {
                objectName: "folderSyncLabel"
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Sync to the web")
                font.pixelSize: 10
                color: Theme.textGray
            }
            Switch {
                objectName: "folderSyncSwitch"
                anchors.verticalCenter: parent.verticalCenter
                enabled: false
                checked: false
            }
        }
    }

    Text {
        objectName: "folderDateText"
        visible: header.dateText !== ""
        text: header.dateText
        color: Theme.folderDate
        font.family: "Georgia"
        font.pointSize: 14
        Layout.leftMargin: 50
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
            color: Theme.contentPanel; border.color: Theme.chromeBorder
            Text { anchors.centerIn: parent; text: "☆"; color: Theme.textGray; font.pixelSize: 13 }
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

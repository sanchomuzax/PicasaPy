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
    // #422: a mappa-kontextusmenü HARMADIK megnyitási pontja — a felmérés
    // szerint a fejlécre jobbklikkelve UGYANAZ a 15 tételes menü jön elő,
    // mint a rács üres területén és a bal panel mappa-során
    signal contextMenuRequested()

    //: #1823: a fejléc-gombok DARABSZÁMOT írnak ki. A bináris erőforrásai
    //: minden fejléc-gombot két alakban tartanak — `albumbutton_save` és
    //: `albumbutton_save%d` —, vagyis üres kijelölésnél a szám nélküli,
    //: kijelölésnél a számos felirat megy ki.
    //:
    //: ⚠️ A `play` gombra ez NEM igaz: a mért listában (`save`, `sstar`,
    //: `sall`, `album`, `cd`, `menu`, `pubaction`) nincs `play%d`. A
    //: diavetítés ezért ikon marad, szám nélkül — a jegy „a play is"
    //: mondata a mérésnek mond ellent.
    property int selectedCount: 0

    //: „Szerkesztések mentése lemezre" (`save_edits`) — a kijelölt képek
    //: szerkesztéseit a FÁJLBA írja. A művelet maga a #444 mentés-
    //: párbeszédéé; ez a gomb csak egy újabb belépési pont hozzá.
    signal saveEditsRequested()

    //: „Csillagozottak kijelölése" (`select_star`) — ugyanaz a parancs,
    //: mint a menüsávban; itt is a jelenlegi mappára hat (#1145).
    signal selectStarredRequested()
    //: #1006: kollázs a fejléc csoportjából. Az eredetiben NÉGY belépési
    //: pont van; nálunk kettő működött (Létrehozás menü, kimeneti sáv), a
    //: két fejléc-gomb hiányzott.
    signal collageRequested()

    //: A számos/szám nélküli alak választása egy helyen, hogy minden
    //: fejléc-gomb ugyanúgy viselkedjen.
    function feliratSzammal(alap) {
        return header.selectedCount > 0
            ? alap + " (" + header.selectedCount + ")" : alap
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: header.contextMenuRequested()
    }
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
        // #1823: eddig ez egy néma díszcsempe volt — se neve, se
        // kezelője. Most a mért `select_star` gomb: a jelenlegi mappa
        // csillagozott képeit jelöli ki.
        PicasaButton {
            objectName: "headerSelectStarredButton"
            text: header.feliratSzammal("☆")
            Layout.preferredHeight: 22
            ToolTip.text: qsTr("Select starred photos")
            ToolTip.visible: hovered
            ToolTip.delay: 500
            onClicked: header.selectStarredRequested()
        }
        // #1823: „szerkesztések mentése lemezre" (`save_edits`) — a
        // fejlécről eddig teljesen hiányzott, pedig a művelet megvan
        // (#444). Üres kijelölésnél tiltott: a mentés a KIJELÖLTEKRE hat.
        PicasaButton {
            objectName: "headerSaveEditsButton"
            text: header.feliratSzammal(qsTr("Save"))
            enabled: header.selectedCount > 0
            Layout.preferredHeight: 22
            ToolTip.text: qsTr("Save edited photos to disk")
            ToolTip.visible: hovered
            ToolTip.delay: 500
            onClicked: header.saveEditsRequested()
        }
        // #1006: `headerpanel/create_collage` — MÉRT 29 × 27
        // (`picasa-create-features.md` 1.10.5).
        //
        // ⚠️ Az eredetiben KÉT panel van: a mappa-fejléc
        // (`headerpanel`) és az ARC-fejléc (`faceheaderpanel`), mindkettőn
        // ugyanez a gomb. A mi felületünkön a személy képei UGYANEBBEN a
        // rácsban, ugyanezzel a fejléccel jelennek meg — nincs külön
        // arc-fejléc. Ez az egy gomb tehát mindkét belépési pontot
        // lefedi; külön arc-fejlécet építeni olyan felületet hozna létre,
        // ami nálunk nem létezik.
        PicasaButton {
            objectName: "headerCollageButton"
            width: 29; height: 27
            Layout.preferredWidth: 29
            Layout.preferredHeight: 27
            ToolTip.text: qsTr("Create a collage from these photos")
            ToolTip.visible: hovered
            ToolTip.delay: 500
            onClicked: header.collageRequested()
            contentItem: Item {
                Image {
                    objectName: "headerCollageIcon"
                    source: "icons/collage-check.svg"
                    width: 16; height: 16
                    sourceSize.width: 16; sourceSize.height: 16
                    fillMode: Image.PreserveAspectFit
                    anchors.centerIn: parent
                }
            }
        }
        PicasaButton {
            objectName: "headerUploadButton"
            text: header.feliratSzammal(qsTr("Upload")) + " ▾"
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

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Címkék-panel (#12, Ctrl+T) — a Picasa jobb oldali „Tags" paneljének mása:
// felül beviteli mező + hozzáadás, alatta a kijelölés címkéi, soronként
// levehető ✕-szel. A panel buta komponens: a címke-listát kívülről kapja
// (`tags`), a módosítást jelekkel kéri — az írást a controller végzi.
Rectangle {
    id: panel

    // a kijelölés címkéinek uniója (controller.keywordsOfRows)
    property var tags: []
    // van-e kijelölt kép — enélkül a bevitel tiltott
    property bool hasSelection: false
    //: #2998: a kijelölésben van írásvédett elem. Az eredeti
    //: (`keywords/readonly_label`) „one or more items"-et mond, tehát
    //: egyetlen ilyen elem is elég — és a bevitelt is tiltja.
    property bool readOnlySelection: false
    readonly property bool cimkezheto: panel.hasSelection
                                       && !panel.readOnlySelection

    signal addRequested(string keyword)
    signal removeRequested(string keyword)
    signal closeRequested()
    // #422: a címke jobbklikk-menüje (Picasa `Tags` menüosztály) —
    // a címke rátétele a TELJES kijelölésre, illetve az ilyen címkéjű
    // elemek keresése; a bekötés a Main.qml-ben (a kijelölés gazdája)
    signal addToSelectionRequested(string keyword)
    signal findTaggedRequested(string keyword)

    // a menüt a sor jobbklikkje nyitja; a célcímkét a menü hordozza
    function openTagContextMenu(keyword) {
        tagContextMenu.keyword = keyword
        tagContextMenu.popup()
    }

    TagContextMenu {
        id: tagContextMenu
        onAddToSelectionRequested: panel.addToSelectionRequested(keyword)
        onFindTaggedRequested: panel.findTaggedRequested(keyword)
        onRemoveRequested: panel.removeRequested(keyword)
    }

    // teszt-horog és a beviteli mező közös útja: üres/whitespace inputra
    // nem megy ki jel, sikeres leadás után a mező kiürül
    function submit() {
        var text = tagInput.text.trim()
        if (text.length === 0 || !panel.hasSelection)
            return
        panel.addRequested(text)
        tagInput.clear()
    }

    color: Theme.panelBg
    border.color: Theme.chromeBorder

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        //: #754: a CÍM és a bezáró gomb a FIÓK közös fejlécében él
        //: (`RightDrawer`), nem a panelben — az eredetiben egy fejléc
        //: van, és annak címe a lap neve.

        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            TextField {
                id: tagInput
                objectName: "tagInput"
                Layout.fillWidth: true
                enabled: panel.cimkezheto
                font.pixelSize: Theme.fontSize
                placeholderText: qsTr("Add a tag...")
                onAccepted: panel.submit()
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
            PicasaButton {
                objectName: "tagAddButton"
                text: "+"
                enabled: panel.cimkezheto && tagInput.text.trim().length > 0
                Layout.preferredWidth: 26
                onClicked: panel.submit()
            }
        }

        Text {
            //: #2998: az eredeti `keywords/readonly_label` megfelelője.
            //: A kijelölés-kérő szöveg elé kerül, mert konkrétabb nála.
            objectName: "tagsReadOnlyNotice"
            visible: panel.hasSelection && panel.readOnlySelection
            Layout.fillWidth: true
            text: qsTr("Tags cannot be modified because one or more items are read-only.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        Text {
            visible: !panel.hasSelection
            Layout.fillWidth: true
            text: qsTr("Select pictures to tag them.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize - 1
            font.italic: true
            color: Theme.textGray
        }

        ListView {
            id: tagList
            objectName: "tagList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: panel.tags
            spacing: 2
            delegate: Rectangle {
                id: tagRow
                required property var modelData
                width: tagList.width
                height: 22
                radius: 3
                color: rowHover.hovered ? "#ffffff" : "transparent"
                border.color: rowHover.hovered
                              ? Theme.chromeBorder : "transparent"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    anchors.rightMargin: 4
                    spacing: 4
                    //: #1132: a címke SAJÁT típus (`icons/label`, szürke
                    //: címke) — eddig a MAPPA aranyát használta, tehát a
                    //: címke ugyanúgy nézett ki, mint egy mappa.
                    LabelIcon {
                        objectName: "tagRowIcon"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        Layout.fillWidth: true
                        text: tagRow.modelData
                        elide: Text.ElideRight
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                    Rectangle {
                        objectName: "tagRemove-" + tagRow.modelData
                        width: 14; height: 14; radius: 7
                        color: removeHover.hovered ? "#c94b3d" : "transparent"
                        Text {
                            anchors.centerIn: parent
                            text: "✕"
                            font.pixelSize: 8
                            color: removeHover.hovered
                                   ? "#ffffff" : Theme.textGray
                        }
                        HoverHandler { id: removeHover }
                        TapHandler {
                            onTapped: panel.removeRequested(tagRow.modelData)
                        }
                    }
                }
                HoverHandler { id: rowHover }
                TapHandler {
                    acceptedButtons: Qt.RightButton
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onSingleTapped: panel.openTagContextMenu(tagRow.modelData)
                }
            }
        }

        // Gyorscímkék (#193) — a Picasa 3 mintájára: 2×4 gombrács a panel
        // alján. A gombok a controller.quickTagButtons-t (tíz elemű lista,
        // "" = üres szlot, a QML "?" jellel jelzi) mutatják; kattintásra a
        // MEGLÉVŐ addRequested jelen át adódnak a kijelöléshez (ugyanaz az
        // út, mint a kézi címke-beírásé — Main.qml köti a controllerhez).
        // A `controller` context property közvetlen elérése itt kivétel a
        // panel „buta komponens" elvéhez képest: a Main.qml forró fájl
        // (nem bővíthető ezzel az adatfolyammal), a mintát viszont más
        // beágyazott QML-ek (LightboxFeed, MainToolbar) is követik.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: Theme.chromeBorder
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: qsTr("Quick tags")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.ink
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                objectName: "quickTagsGearButton"
                width: 18; height: 18; radius: 3
                color: gearHover.hovered ? Theme.chromeBorder : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "⚙"
                    font.pixelSize: 12
                    color: Theme.textGray
                }
                HoverHandler { id: gearHover }
                TapHandler {
                    onTapped: quickTagsConfigDialog.open()
                }
            }
        }

        ColumnLayout {
            id: quickTagsGrid
            objectName: "quickTagsGrid"
            Layout.fillWidth: true
            spacing: 4

            // #1788: 2 sor × 5 gomb (volt 2×4). Az eredetiben TÍZ
            // gyorscímke-hely van — a `quicktagconfig` elemleltára
            // `edit_0` … `edit_9`-et sorol, a kezelő ciklushatára pedig
            // `cmp eax, 0xa`. Nyolc gombbal a kilencedik és tizedik
            // beállított címke sehol nem jelenne meg.
            //
            // EXPLICIT deklaráció, Repeater NÉLKÜL: egy
            // Layout-ba ágyazott Repeater a Qt Quick Layouts sajátossága
            // miatt úgy jelenteti meg a delegáltakat, hogy a QObject-
            // szülőjük a Repeater marad (nem a layout) — findChild(name)
            // ezért a tesztekben nem találná meg őket. A `quickTagButton`
            // helyi komponens (lásd lent) DRY-vá teszi a tíz példányt.
            component QuickTagButton: PicasaButton {
                id: quickTagButton
                required property int slot
                // #305: null-őr — a controller a QML-engine leépítésekor
                // átmenetileg null lehet. #718: a `typeof` azt az esetet is
                // fedi, amikor a panel ELSZIGETELT komponensként (a saját
                // context property nélküli tesztje, ld.
                // test_qml_tags_panel.py) töltődik be — ott a `controller`
                // néven MEG SEM lévő globálisra a puszta `controller ? …`
                // kiértékelés önmagában ReferenceError-t dobna (a `typeof`
                // az egyetlen biztonságos módja egy esetleg nem is létező
                // azonosító ellenőrzésének).
                readonly property string label:
                    (typeof controller !== "undefined" && controller
                        ? controller.quickTagButtons[quickTagButton.slot]
                        : "") || ""
                objectName: "quickTagButton" + quickTagButton.slot
                Layout.fillWidth: true
                //: a mért gombmagasság (`quicktag_*`)
                Layout.preferredHeight: 21
                text: quickTagButton.label.length > 0
                      ? quickTagButton.label : "?"
                font.pixelSize: Theme.fontSize - 1
                enabled: panel.cimkezheto && quickTagButton.label.length > 0
                onClicked: panel.addRequested(quickTagButton.label)
            }

            //: #754: a MÉRT elrendezés 2 · 3 · 2 · 3, nem 5 · 5. A kettes
            //: sorok gombjai 128–129 képpont szélesek, a hármas sorokéi 85,
            //: és az 1. meg a 2. sor közt 3 képpontos elválasztó áll
            //: (`docs/specs/jobb-fiok-meretek.md` 3.). Minden gomb 21 magas.
            RowLayout {
                objectName: "quickTagsRow0"
                Layout.fillWidth: true
                spacing: 2
                QuickTagButton { slot: 0 }
                QuickTagButton { slot: 1 }
            }
            //: `divider` 242 × 3
            Rectangle {
                objectName: "quickTagsDivider"
                Layout.fillWidth: true
                Layout.preferredHeight: 3
                color: Theme.chromeBorder
            }
            RowLayout {
                objectName: "quickTagsRow1"
                Layout.fillWidth: true
                spacing: 2
                QuickTagButton { slot: 2 }
                QuickTagButton { slot: 3 }
                QuickTagButton { slot: 4 }
            }
            RowLayout {
                objectName: "quickTagsRow2"
                Layout.fillWidth: true
                spacing: 2
                QuickTagButton { slot: 5 }
                QuickTagButton { slot: 6 }
            }
            RowLayout {
                objectName: "quickTagsRow3"
                Layout.fillWidth: true
                spacing: 2
                QuickTagButton { slot: 7 }
                QuickTagButton { slot: 8 }
                QuickTagButton { slot: 9 }
            }
        }
    }

    QuickTagsConfigDialog {
        id: quickTagsConfigDialog
        objectName: "quickTagsConfigDialog"
    }
}

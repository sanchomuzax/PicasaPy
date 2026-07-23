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

    signal addRequested(string keyword)
    signal removeRequested(string keyword)
    signal closeRequested()

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

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: qsTr("Tags")
                font.pixelSize: Theme.fontSize + 1
                font.bold: true
                color: Theme.ink
            }
            Item { Layout.fillWidth: true }
            // bezáró ✕ (a Nézet menü / Ctrl+T is zár)
            Rectangle {
                objectName: "tagsPanelClose"
                width: 16; height: 16; radius: 2
                color: closeHover.hovered ? Theme.chromeBorder : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    font.pixelSize: 9
                    color: Theme.textGray
                }
                HoverHandler { id: closeHover }
                TapHandler { onTapped: panel.closeRequested() }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 4
            TextField {
                id: tagInput
                objectName: "tagInput"
                Layout.fillWidth: true
                enabled: panel.hasSelection
                font.pixelSize: Theme.fontSize
                placeholderText: qsTr("Add a tag...")
                onAccepted: panel.submit()
            }
            PicasaButton {
                objectName: "tagAddButton"
                text: "+"
                enabled: panel.hasSelection && tagInput.text.trim().length > 0
                Layout.preferredWidth: 26
                onClicked: panel.submit()
            }
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
                    // címke-ikon (rajzolt, Picasa-minta)
                    Rectangle {
                        width: 10; height: 7; radius: 1
                        color: Theme.folderGold
                        border.color: Theme.folderArrow
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
            }
        }

        // Gyorscímkék (#193) — a Picasa 3 mintájára: 2×4 gombrács a panel
        // alján. A gombok a controller.quickTagButtons-t (8 elemű lista,
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

            // 2 sor × 4 gomb — EXPLICIT deklaráció, Repeater NÉLKÜL: egy
            // Layout-ba ágyazott Repeater a Qt Quick Layouts sajátossága
            // miatt úgy jelenteti meg a delegáltakat, hogy a QObject-
            // szülőjük a Repeater marad (nem a layout) — findChild(name)
            // ezért a tesztekben nem találná meg őket. A `quickTagButton`
            // helyi komponens (lásd lent) DRY-vá teszi a 8 példányt.
            component QuickTagButton: PicasaButton {
                id: quickTagButton
                required property int slot
                readonly property string label:
                    controller.quickTagButtons[quickTagButton.slot] || ""
                objectName: "quickTagButton" + quickTagButton.slot
                Layout.fillWidth: true
                text: quickTagButton.label.length > 0
                      ? quickTagButton.label : "?"
                font.pixelSize: Theme.fontSize - 1
                enabled: panel.hasSelection && quickTagButton.label.length > 0
                onClicked: panel.addRequested(quickTagButton.label)
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                QuickTagButton { slot: 0 }
                QuickTagButton { slot: 1 }
                QuickTagButton { slot: 2 }
                QuickTagButton { slot: 3 }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                QuickTagButton { slot: 4 }
                QuickTagButton { slot: 5 }
                QuickTagButton { slot: 6 }
                QuickTagButton { slot: 7 }
            }
        }
    }

    QuickTagsConfigDialog {
        id: quickTagsConfigDialog
        objectName: "quickTagsConfigDialog"
    }
}

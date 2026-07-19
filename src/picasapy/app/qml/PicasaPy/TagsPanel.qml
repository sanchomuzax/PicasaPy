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
    }
}

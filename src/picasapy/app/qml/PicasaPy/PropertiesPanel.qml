import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Tulajdonságok-panel (#13, Alt+Enter) — a Picasa jobb oldali Properties
// paneljének mása: a kijelölt kép fájl- és EXIF-adatai, CSAK olvasásra.
// Buta komponens: a sorokat kívülről kapja ({label, value} párok listája).
Rectangle {
    id: panel

    // {label, value} sorok (controller.propertiesOf)
    property var entries: []
    property bool hasSelection: false

    signal closeRequested()

    color: Theme.panelBg
    border.color: Theme.chromeBorder

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: qsTr("Properties")
                font.pixelSize: Theme.fontSize + 1
                font.bold: true
                color: Theme.ink
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                objectName: "propertiesPanelClose"
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

        Text {
            visible: !panel.hasSelection
            Layout.fillWidth: true
            text: qsTr("Select a picture to see its properties.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize - 1
            font.italic: true
            color: Theme.textGray
        }

        ListView {
            id: propertyList
            objectName: "propertyList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: panel.hasSelection
            model: panel.entries
            spacing: 4
            delegate: Column {
                required property var modelData
                width: propertyList.width
                spacing: 1
                Text {
                    width: parent.width
                    text: modelData.label
                    font.pixelSize: Theme.fontSize - 2
                    color: Theme.textGray
                }
                Text {
                    width: parent.width
                    text: modelData.value
                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
            }
            ScrollBar.vertical: PicasaScrollBar {}
        }
    }
}

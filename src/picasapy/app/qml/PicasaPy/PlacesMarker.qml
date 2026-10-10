import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A térképjelölő és buborékja. A QtLocationtől független fájl, hogy a
// bélyegkép- és buborékfelület a térképmodul nélküli tesztkörnyezetben is
// ténylegesen megjeleníthető és kattintható legyen.
Item {
    id: root
    objectName: "placesMarkerVisual"

    // {rows: [rácssorok], thumbUrl: image://thumbs/<id>?...}
    property var markerData: ({ rows: [], thumbUrl: "" })
    readonly property bool thumbnailReady: markerImage.status === Image.Ready

    signal markerActivated(int row)
    signal markerSearchRequested(var rows)
    signal markerEraseRequested(var rows)

    width: 260
    height: 162

    Rectangle {
        id: markerBubble
        objectName: "placesMarkerBubble"
        x: 8
        y: 0
        width: 244
        height: 106
        visible: false
        color: Theme.contentPanel
        border.color: Theme.chromeBorder
        radius: 4

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 7
            spacing: 3

            Text {
                objectName: "placesMarkerPhotosHere"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: root.markerData.rows.length === 1
                      ? qsTr("1 photo here:")
                      : qsTr("%d photos here:")
                        .replace("%d", String(root.markerData.rows.length))
                color: Theme.ink
                font.pixelSize: Theme.fontSize
            }

            PicasaButton {
                objectName: "placesMarkerSearchButton"
                Layout.fillWidth: true
                Layout.preferredHeight: 31
                text: qsTr("Search for these photos in Picasa")
                Accessible.name: qsTr("Search for these photos in Picasa")
                ToolTip.text: qsTr("Search for these photos in Picasa")
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                onClicked: {
                    root.markerSearchRequested(root.markerData.rows)
                    markerBubble.visible = false
                }
            }

            PicasaButton {
                objectName: "placesMarkerEraseButton"
                Layout.fillWidth: true
                Layout.preferredHeight: 28
                text: qsTr("Erase location info")
                Accessible.name: qsTr("Erase location info")
                ToolTip.text: qsTr(
                    "Erase map coordinates(i.e., GPS information) from these photos")
                ToolTip.visible: hovered
                ToolTip.delay: Theme.tooltipDelay
                onClicked: {
                    root.markerEraseRequested(root.markerData.rows)
                    markerBubble.visible = false
                }
            }
        }
    }

    Rectangle {
        id: markerFrame
        x: (root.width - width) / 2
        y: 110
        width: 48
        height: 48
        radius: 3
        color: Theme.contentPanel
        border.color: Theme.chromeBorder
        border.width: 2

        TapHandler {
            acceptedButtons: Qt.LeftButton
            onTapped: {
                root.markerActivated(root.markerData.rows[0])
                markerBubble.visible = !markerBubble.visible
            }
        }

        Image {
            id: markerImage
            objectName: "placesMarkerImage"
            anchors.fill: parent
            anchors.margins: 2
            source: root.markerData.thumbUrl
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            mipmap: true
            smooth: true
            sourceSize.width: 64
            sourceSize.height: 64
        }
    }

    Rectangle {
        x: root.width / 2 - width / 2
        y: 154
        width: 2
        height: 8
        color: Theme.brandRed
    }
    Rectangle {
        x: root.width / 2 - width / 2
        y: 149
        width: 8
        height: 8
        radius: 4
        color: Theme.brandRed
        border.color: Theme.contentPanel
        border.width: 1
    }
}

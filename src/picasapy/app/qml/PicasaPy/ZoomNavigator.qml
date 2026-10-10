import QtQuick

// A Picasa nav.tre lebegő áttekintője (#4568). A mini kép a ténylegesen
// megjelenített forrásból készül; a sötét fátyol és a mozgatható keret a
// látható képterületet mutatja, nem a teljes raszter egy becsült részét.
Item {
    id: root
    objectName: "zoomNavigator"

    property url imageSource: ""
    property real imageAspect: 1
    property real imageRotation: 0
    property real zoomFactor: 1
    property real zoomPercent: 100
    property rect viewRect: Qt.rect(0, 0, 1, 1)
    property color outlineColor: Theme.brandBlue

    signal panRequested(real deltaX, real deltaY)
    signal closeRequested()

    readonly property bool quarterTurn: Math.round(Math.abs(imageRotation) / 90) % 2 === 1
    readonly property real displayAspect:
        quarterTurn ? 1 / Math.max(0.01, imageAspect)
                    : Math.max(0.01, imageAspect)
    readonly property real displayImageWidth:
        Math.min(Math.max(80, Math.min(224, parent ? parent.width * 0.28 : 224) - 12),
                 Math.min(140, parent ? Math.max(64, parent.height * 0.24) : 140)
                    * displayAspect)
    readonly property real displayImageHeight:
        displayImageWidth / Math.max(0.01, displayAspect)
    readonly property real localImageWidth:
        quarterTurn ? displayImageHeight : displayImageWidth
    readonly property real localImageHeight:
        quarterTurn ? displayImageWidth : displayImageHeight

    width: displayImageWidth + 12
    height: displayImageHeight + 38
    z: 100

    Rectangle {
        anchors.fill: parent
        color: Theme.panelBg
        border.color: Theme.chromeBorder
        radius: 3
    }

    Item {
        id: previewBox
        objectName: "zoomNavigatorPreview"
        width: root.displayImageWidth
        height: root.displayImageHeight
        anchors.top: parent.top
        anchors.topMargin: 6
        anchors.horizontalCenter: parent.horizontalCenter
        clip: true

        Item {
            id: previewCanvas
            objectName: "zoomNavigatorCanvas"
            width: root.localImageWidth
            height: root.localImageHeight
            anchors.centerIn: parent
            rotation: root.imageRotation
            clip: true

            Image {
                id: previewImage
                objectName: "zoomNavigatorImage"
                anchors.fill: parent
                source: root.imageSource
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                cache: false
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: viewport.y
                color: "#8f2f2f2f"
            }
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: Math.max(0, parent.height - viewport.y - viewport.height)
                color: "#8f2f2f2f"
            }
            Rectangle {
                anchors.left: parent.left
                y: viewport.y
                width: viewport.x
                height: viewport.height
                color: "#8f2f2f2f"
            }
            Rectangle {
                anchors.right: parent.right
                x: viewport.x + viewport.width
                y: viewport.y
                width: Math.max(0, parent.width - x)
                height: viewport.height
                color: "#8f2f2f2f"
            }

            Rectangle {
                id: viewport
                objectName: "zoomNavigatorViewport"
                property color outlineColor: root.outlineColor
                x: root.viewRect.x * parent.width
                y: root.viewRect.y * parent.height
                width: Math.max(1, root.viewRect.width * parent.width)
                height: Math.max(1, root.viewRect.height * parent.height)
                color: "transparent"
                border.width: 2
                border.color: outlineColor
                z: 2
            }

            MouseArea {
                id: viewportDrag
                objectName: "zoomNavigatorViewportDrag"
                x: viewport.x
                y: viewport.y
                width: viewport.width
                height: viewport.height
                z: 3
                cursorShape: Qt.SizeAllCursor

                property real lastX: 0
                property real lastY: 0

                onPressed: function(mouse) {
                    lastX = viewport.x + mouse.x
                    lastY = viewport.y + mouse.y
                }
                onPositionChanged: function(mouse) {
                    if (!pressed || previewCanvas.width <= 0
                            || previewCanvas.height <= 0)
                        return
                    var pointX = viewport.x + mouse.x
                    var pointY = viewport.y + mouse.y
                    var deltaX = (pointX - lastX) / previewCanvas.width
                    var deltaY = (pointY - lastY) / previewCanvas.height
                    lastX = pointX
                    lastY = pointY
                    root.panRequested(deltaX, deltaY)
                }
            }
        }

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.color: Theme.chromeBorder
            z: 4
        }

        Rectangle {
            id: closeButton
            objectName: "zoomNavigatorClose"
            width: 19
            height: 19
            anchors.top: parent.top
            anchors.right: parent.right
            color: Theme.panelBg
            border.color: Theme.chromeBorder
            radius: 2
            z: 5

            Rectangle {
                width: 11
                height: 2
                radius: 1
                anchors.centerIn: parent
                rotation: 45
                color: Theme.ink
            }
            Rectangle {
                width: 11
                height: 2
                radius: 1
                anchors.centerIn: parent
                rotation: -45
                color: Theme.ink
            }
            MouseArea {
                objectName: "zoomNavigatorCloseButton"
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.closeRequested()
            }
        }
    }

    Text {
        id: zoomLabel
        objectName: "zoomNavigatorZoomLabel"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 5
        height: 20
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        color: Theme.ink
        // nav/zoom viseli a hivatalos m_displayfont14 beállítást a nav.tre-ben.
        font.pixelSize: 14
        //: Eredeti Picasa: nav/zoom, ytZoomString::Value — „Zoomed to %3.0f%%”.
        text: qsTr("Zoomed to %1%").arg(Math.round(root.zoomPercent))
    }
}

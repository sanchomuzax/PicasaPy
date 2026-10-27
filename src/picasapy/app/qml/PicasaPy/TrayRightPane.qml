import QtQuick

Item {
    id: trayRightPane
    objectName: "trayRightPane"
    property var trayRoot
    property var trayController
    property var trayBar
    readonly property real starGroupWidth: trayTopRow.starGroupWidth
    readonly property real zoomGroupWidth: trayTopRow.zoomGroupWidth
    readonly property real metadataGroupWidth: trayTopRow.metadataGroupWidth
    readonly property int starTargetRow: trayTopRow.starTargetRow
    readonly property bool starEnabled: trayTopRow.starEnabled

    function activateStar() {
        trayTopRow.activateStar()
    }

    x: trayBar.splitX
    y: 6
    width: Math.max(0, trayBar.width - trayBar.rightMargin - x)
    height: parent.height - y

    TrayTopRow {
        id: trayTopRow
        trayRoot: trayRightPane.trayRoot
        trayBar: trayRightPane.trayBar
    }
    TrayActionArea {
        anchors.fill: parent
        trayRoot: trayRightPane.trayRoot
        actionController: trayRightPane.trayController
        trayBar: trayRightPane.trayBar
    }
}

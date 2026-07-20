import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Lebegő „Teljesítmény-monitor" panel (#211) — az ImportProgressPanel
// (#209) widget-mintájára: szabadon húzható, a fejlécénél fogva; a
// láthatóságát a Main.qml a controller.perfMonitorEnabled-jére köti.
// Kézzel az × gombbal zárható — ez magát a monitorozást is kikapcsolja
// (a felhasználó szándéka: „ne mérjen, ne mutasson").
Rectangle {
    id: panel

    // a Main.qml köti a controller perf*-tulajdonságaira
    property real cpuPercent: 0
    property real rssMb: 0
    property string topActivity: ""
    // a legutóbb mentett diagnosztika-fájl útvonala (a Main.qml tölti ki
    // a saveRequested kezelésekor, a controller.saveDiagnostics() alapján)
    property string lastSavedPath: ""
    signal closeRequested()
    signal saveRequested()

    width: 220
    height: content.implicitHeight + 20
    radius: 4
    color: Theme.trayBg
    border.color: Theme.chromeBorder
    border.width: 1

    Rectangle {
        anchors.fill: parent
        anchors.margins: -1
        z: -1
        radius: panel.radius + 1
        color: "transparent"
        border.color: "#33000000"
    }

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Text {
                text: qsTr("Performance monitor")
                color: Theme.ink
                font.pixelSize: Theme.fontSize
                font.bold: true
                Layout.fillWidth: true
            }
            Text {
                objectName: "perfPanelClose"
                text: "×"
                color: Theme.textGray
                font.pixelSize: Theme.fontSize + 4
                TapHandler { onTapped: panel.closeRequested() }
            }
        }

        Text {
            objectName: "perfPanelCpu"
            Layout.fillWidth: true
            text: qsTr("CPU: %1%").arg(panel.cpuPercent.toFixed(1))
            color: Theme.folderDate
            font.pixelSize: Theme.fontSize
        }

        Text {
            objectName: "perfPanelRss"
            Layout.fillWidth: true
            text: qsTr("Memory: %1 MB").arg(panel.rssMb.toFixed(1))
            color: Theme.folderDate
            font.pixelSize: Theme.fontSize
        }

        Text {
            objectName: "perfPanelActivity"
            Layout.fillWidth: true
            text: panel.topActivity
            color: Theme.textGray
            font.pixelSize: Theme.fontSize - 1
            elide: Text.ElideMiddle
        }

        PicasaButton {
            objectName: "perfPanelSaveButton"
            text: qsTr("Save diagnostics...")
            Layout.fillWidth: true
            onClicked: panel.saveRequested()
        }

        Text {
            id: savedPathText
            objectName: "perfPanelSavedPath"
            Layout.fillWidth: true
            visible: panel.lastSavedPath.length > 0
            text: panel.lastSavedPath
            color: Theme.picasaGreen
            font.pixelSize: Theme.fontSize - 1
            font.underline: savedPathHover.hovered
            wrapMode: Text.WrapAnywhere

            // #217: az útvonal-szöveg kattintható — a napló mappáját
            // nyitja meg a rendszer fájlkezelőjében (a controller globális
            // context property, TrayBar.qml mintájára közvetlenül elérhető
            // innen is, Main.qml-beli bekötés nélkül). Saját, paraméter
            // nélküli függvénybe szervezve (nem közvetlenül onTapped-ben),
            // hogy a funkcionális teszt a beépített TapHandler.tapped()
            // fix (QEventPoint, MouseButton) szignatúrája helyett ezt
            // hívhassa invokeMethod-dal.
            function openSavedPathFolder() {
                controller.openDiagnosticsFolder(panel.lastSavedPath)
            }

            TapHandler {
                objectName: "perfPanelSavedPathTap"
                onTapped: savedPathText.openSavedPathFolder()
            }
            HoverHandler {
                id: savedPathHover
                cursorShape: Qt.PointingHandCursor
            }
        }
    }

    DragHandler {
        target: panel
        xAxis.minimum: 0
        xAxis.maximum: panel.parent ? panel.parent.width - panel.width : 0
        yAxis.minimum: 0
        yAxis.maximum: panel.parent ? panel.parent.height - panel.height : 0
    }
}

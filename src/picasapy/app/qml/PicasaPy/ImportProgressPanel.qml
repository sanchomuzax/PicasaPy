import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Lebegő „Importálás" folyamat-panel (#209) — a Windows-os Picasa 3
// import-visszajelzésének megfelelője. Szabadon mozgatható (a fejlécénél
// fogva húzható); automatikusan jelenik meg nagy szkennelésnél, és a
// szkennelés végén tűnik el (a láthatóságot a Main.qml köti a
// controller.importPanelVisible-re). Kézzel az × gombbal zárható.
Rectangle {
    id: panel

    // a Main.qml köti a controller import*-tulajdonságaira
    property string folderName: ""
    property int doneCount: 0
    property int totalCount: 0
    property int newCount: 0
    signal closeRequested()

    width: 250
    height: content.implicitHeight + 20
    radius: 4
    color: Theme.trayBg
    border.color: Theme.chromeBorder
    border.width: 1

    // finom vetett árnyék helyett halvány kontúr-duplázás (nincs külső lib)
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

        // fejléc: cím + bezárás; a panel ennél fogva húzható
        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Text {
                text: qsTr("Importing")
                color: Theme.ink
                font.pixelSize: Theme.fontSize
                font.bold: true
                Layout.fillWidth: true
            }
            // bezárás — a futó szkennelést nem állítja meg, csak a panelt
            // rejti el (Picasa-minta)
            Text {
                objectName: "importPanelClose"
                text: "×"
                color: Theme.textGray
                font.pixelSize: Theme.fontSize + 4
                TapHandler { onTapped: panel.closeRequested() }
            }
        }

        // az éppen feldolgozott mappa neve
        Text {
            objectName: "importPanelFolder"
            Layout.fillWidth: true
            text: panel.folderName
            color: Theme.folderDate
            font.pixelSize: Theme.fontSize
            elide: Text.ElideMiddle
        }

        // haladás-sáv: kész mappák / összes ismert mappa
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            radius: 4
            color: "#dddddd"
            border.color: Theme.chromeBorder

            Rectangle {
                objectName: "importPanelBarFill"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                radius: parent.radius
                color: Theme.picasaGreen
                width: panel.totalCount > 0
                       ? parent.width * panel.doneCount / panel.totalCount
                       : 0
            }
        }

        Text {
            objectName: "importPanelCounts"
            Layout.fillWidth: true
            text: qsTr("%1 / %2 folders — %3 new photos")
                  .arg(panel.doneCount).arg(panel.totalCount)
                  .arg(panel.newCount)
            color: Theme.textGray
            font.pixelSize: Theme.fontSize - 1
        }
    }

    // húzás bárhol a panelen (a bezárás-gomb TapHandler-e elsőbbséget kap);
    // a szülőn belül tartva, hogy ne lehessen „elveszíteni"
    DragHandler {
        target: panel
        xAxis.minimum: 0
        xAxis.maximum: panel.parent ? panel.parent.width - panel.width : 0
        yAxis.minimum: 0
        yAxis.maximum: panel.parent ? panel.parent.height - panel.height : 0
    }
}

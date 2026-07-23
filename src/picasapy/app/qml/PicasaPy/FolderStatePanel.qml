import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Jobb oldali állapot-panel a Mappakezelőben (#231): a fában kijelölt
// mappához tartozó háromállapotú választó, alatta a figyelt mappák
// Picasa-kompatibilis összegző listája (a korábbi lapos Mappakezelő
// öröksége — így a régről megszokott áttekintés is megmarad).
//
// A választó sorokat SZÁNDÉKOSAN nem QtQuick.Controls RadioButonnal
// rajzoljuk: a RadioButton (AbstractButton) kattintáskor IMPERATÍVAN
// írja a saját `checked` tulajdonságát, ami véglegesen eltörné a
// backendhez kötött deklaratív bindingot (a következő mappa-kijelölésnél
// a kör már nem követné a valós állapotot). Itt a kör-ikon `visible`
// binding-je sosem kap imperatív írást — a kattintás-kezelő KIZÁRÓLAG a
// controllert hívja —, így mindig frissen tükrözi a kijelölt mappa
// tényleges állapotát.
ColumnLayout {
    id: panel
    property var manager
    property string selectedPath: ""
    spacing: 10

    readonly property var stateOptions: [
        { state: "always", label: qsTr("Scan Always") },
        { state: "once", label: qsTr("Scan Once") },
        { state: "none", label: qsTr("Remove from Picasa") }
    ]

    Text {
        Layout.fillWidth: true
        text: panel.selectedPath.length > 0
              ? panel.selectedPath
              : qsTr("Select a folder on the left.")
        wrapMode: Text.WrapAnywhere
        elide: Text.ElideRight
        maximumLineCount: 3
        font.pixelSize: Theme.fontSize
        font.bold: true
        color: Theme.ink
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 2
        enabled: panel.selectedPath.length > 0

        Repeater {
            model: panel.stateOptions
            delegate: RowLayout {
                required property var modelData
                objectName: "folderStateOption:" + modelData.state
                Layout.fillWidth: true
                spacing: 6

                Rectangle {
                    width: 14; height: 14; radius: 7
                    border.width: 1
                    border.color: Theme.chromeBorder
                    color: "#ffffff"
                    Rectangle {
                        anchors.centerIn: parent
                        width: 8; height: 8; radius: 4
                        color: Theme.selectionBlue
                        visible: panel.manager !== undefined
                                 && panel.manager !== null
                                 && panel.manager.stateFor(panel.selectedPath)
                                    === modelData.state
                    }
                }
                Text {
                    text: modelData.label
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: if (panel.manager)
                                   panel.manager.setState(
                                       panel.selectedPath, modelData.state)
                }
            }
        }
    }

    Text {
        text: qsTr("Watched folders")
        font.pixelSize: Theme.fontSize
        font.bold: true
        color: Theme.ink
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: "#ffffff"
        border.color: Theme.chromeBorder

        ListView {
            id: watchedList
            objectName: "folderManagerWatchedList"
            anchors.fill: parent
            anchors.margins: 1
            clip: true
            model: controller.watchedFolders
            delegate: Rectangle {
                required property string modelData
                width: watchedList.width
                height: 22
                color: panel.selectedPath === modelData
                       ? Theme.selectionBlue : "transparent"
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: 6
                    width: parent.width - 12
                    elide: Text.ElideMiddle
                    text: modelData
                    font.pixelSize: Theme.fontSize
                    color: panel.selectedPath === modelData
                           ? "#ffffff" : Theme.ink
                }
                TapHandler {
                    onTapped: if (panel.manager)
                                  panel.manager.selectedPath = modelData
                }
            }
            ScrollBar.vertical: PicasaScrollBar {}
        }
    }
}

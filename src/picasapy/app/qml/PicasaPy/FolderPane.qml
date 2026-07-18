import QtQuick
import QtQuick.Controls

// Bal oldali mappa-lista — Picasa "Folder List": szekció-fejlécek
// (Albumok/Mappák), elemek darabszámmal, acélkék kijelöléssel.
Rectangle {
    id: pane
    color: Theme.panelBg

    property alias foldersModel: folderList.model
    property string selectedPath: ""
    signal folderChosen(string path)
    signal starredChosen()

    Column {
        anchors.fill: parent

        Rectangle {
            width: parent.width; height: 22
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#eef0f2" }
                GradientStop { position: 1.0; color: Theme.panelHeaderBg }
            }
            border.color: Theme.chromeBorder
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 4
                spacing: 4
                Text { text: "▼"; font.pixelSize: 8; color: Theme.panelHeaderText }
                Text {
                    text: qsTr("Albums") + " (1)"
                    font.pixelSize: Theme.fontSize; font.bold: true
                    color: Theme.panelHeaderText
                }
            }
        }

        Rectangle {
            id: starredItem
            width: parent.width; height: 22
            color: pane.selectedPath === "*starred*"
                   ? Theme.panelSelection : "transparent"
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                Text { text: "★"; color: Theme.starYellow; font.pixelSize: Theme.fontSize }
                Text {
                    text: qsTr("Starred photos")
                    font.pixelSize: Theme.fontSize
                    color: pane.selectedPath === "*starred*"
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { pane.selectedPath = "*starred*"; pane.starredChosen() }
            }
        }

        Rectangle {
            width: parent.width; height: 22
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#eef0f2" }
                GradientStop { position: 1.0; color: Theme.panelHeaderBg }
            }
            border.color: Theme.chromeBorder
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 4
                spacing: 4
                Text { text: "▼"; font.pixelSize: 8; color: Theme.panelHeaderText }
                Text {
                    text: qsTr("Folders") + " ("
                          + (folderList.model ? folderList.model.folderCount : 0)
                          + ")"
                    font.pixelSize: Theme.fontSize; font.bold: true
                    color: Theme.panelHeaderText
                }
            }
        }

        ListView {
            id: folderList
            width: parent.width
            height: pane.height - 66
            clip: true
            delegate: Rectangle {
                required property string kind
                required property string name
                required property string path
                required property int count
                width: folderList.width; height: 22
                color: kind === "folder" && pane.selectedPath === path
                       ? Theme.panelSelection : "transparent"

                // évszám-elválasztó: mono címke (dizajnkézikönyv 08)
                Text {
                    visible: kind === "year"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 6
                    text: name
                    font.family: Theme.monoFamily
                    font.pixelSize: Theme.fontSize
                    font.letterSpacing: 0.8
                    color: Theme.panelYearText
                }

                Row {
                    visible: kind === "folder"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 12
                    spacing: 5
                    Text {
                        text: "▸"
                        font.pixelSize: Theme.fontSize - 2
                        color: pane.selectedPath === path
                               ? Theme.panelSelectionText : Theme.folderArrow
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    FolderIcon { size: 13; anchors.verticalCenter: parent.verticalCenter }
                    Text {
                        text: name + " (" + count + ")"
                        font.pixelSize: Theme.fontSize
                        color: pane.selectedPath === path
                               ? Theme.panelSelectionText : Theme.ink
                    }
                }
                MouseArea {
                    enabled: kind === "folder"
                    anchors.fill: parent
                    onClicked: { pane.selectedPath = path; pane.folderChosen(path) }
                }
            }
            ScrollBar.vertical: ScrollBar {}
        }
    }
}

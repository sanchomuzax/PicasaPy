import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Időrend nézet (#24, Ctrl+5) — a Picasa Timeline megfelelője: a teljes
// könyvtár fotói dátum szerinti korszakokra (év/hónap) bontva, csökkenő
// sorrendben (legújabb elöl), lapozható áttekintésben. Csak böngészésre
// való — a kijelölés/lasszó/kontextusmenü a fő rácsé marad; egy fotóra
// kattintva a bekötő (Main.qml) a fő rácsban jeleníti meg (mappaváltás +
// néző-megnyitás), ezt a `photoChosen` jelzi.
Rectangle {
    id: view
    objectName: "timelineView"
    color: Theme.canvasBg

    // {year, month, label, count, photos} dict-ek listája —
    // a TimelineController.periods tükre (a bekötés a Main.qml dolga)
    property var periodsModel: []
    property int thumbSize: 120
    signal closed()
    // egy bélyegképre kattintva: a fotó azonosítója + mappája — a
    // bekötő ebből választja ki a mappát és nyitja meg a nézőt
    signal photoChosen(int photoId, string folderPath)

    // teszt-segéd (#24): a kattintás-kezelő közvetlenül hívható, valódi
    // egéresemény szintetizálása nélkül (a ThumbDelegate.handleClicked mintája)
    function requestOpen(photoId, folderPath) {
        view.photoChosen(photoId, folderPath)
    }

    onVisibleChanged: if (view.visible) periodList.forceActiveFocus()
    Keys.onEscapePressed: view.closed()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            color: Theme.panelHeaderBg
            border.color: Theme.chromeBorder

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12

                Text {
                    text: qsTr("Timeline")
                    font.pixelSize: Theme.fontSize + 2
                    font.bold: true
                    color: Theme.panelHeaderText
                }
                Item { Layout.fillWidth: true }
                PicasaButton {
                    objectName: "timelineCloseButton"
                    text: "✕ " + qsTr("Close")
                    onClicked: view.closed()
                }
            }
        }

        ListView {
            id: periodList
            objectName: "timelinePeriodList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            focus: true
            model: view.periodsModel
            spacing: 0
            ScrollBar.vertical: PicasaScrollBar {}

            // Picasa Timeline: nincs vetíthető korszak → informatív üres állapot
            Text {
                anchors.centerIn: parent
                visible: periodList.count === 0
                text: qsTr("No pictures yet")
                font.pixelSize: Theme.fontSize + 2
                color: Theme.textGray
            }

            delegate: ColumnLayout {
                id: periodDelegate
                required property var modelData
                width: periodList.width
                spacing: 0

                Rectangle {
                    objectName: "timelinePeriodHeader"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 26
                    color: Theme.panelHeaderBg
                    border.color: Theme.chromeBorder

                    Text {
                        objectName: "timelinePeriodLabel"
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: 8
                        text: periodDelegate.modelData.label
                              + " (" + periodDelegate.modelData.count + ")"
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        color: Theme.panelHeaderText
                    }
                }

                // interactive:false — a görgetés a külső ListView-é (a
                // periódus csak a saját magasságára nő, mint a keresési
                // találatok mappánkénti al-rácsa, LightboxFeed.qml mintája)
                GridView {
                    id: periodGrid
                    Layout.fillWidth: true
                    interactive: false
                    readonly property int nominalCellWidth: view.thumbSize + 12
                    readonly property int columns:
                        Math.max(1, Math.floor(width / nominalCellWidth))
                    cellWidth: columns > 0
                        ? Math.floor(width / columns) : nominalCellWidth
                    cellHeight: view.thumbSize + 12
                    height: Math.ceil(
                        periodDelegate.modelData.photos.length
                        / Math.max(1, columns)) * cellHeight
                    model: periodDelegate.modelData.photos

                    delegate: Item {
                        id: cell
                        objectName: "timelineThumbCell"
                        required property var modelData
                        width: periodGrid.cellWidth
                        height: periodGrid.cellHeight

                        Rectangle {
                            anchors.centerIn: parent
                            width: image.paintedWidth + 8
                            height: image.paintedHeight + 8
                            color: Theme.thumbCard
                            border.width: 1
                            border.color: Theme.thumbBorder

                            Image {
                                id: image
                                objectName: "timelineThumbImage"
                                anchors.centerIn: parent
                                width: view.thumbSize
                                height: view.thumbSize
                                source: cell.modelData.thumbUrl
                                fillMode: Image.PreserveAspectFit
                                asynchronous: Qt.platform.pluginName !== "offscreen"
                                cache: true
                                smooth: true
                                mipmap: true
                            }
                            Text {
                                visible: cell.modelData.star === true
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                anchors.margins: 3
                                text: "★"
                                color: Theme.starYellow
                                font.pixelSize: 13
                                style: Text.Outline
                                styleColor: "#00000060"
                            }
                            Rectangle {
                                visible: cell.modelData.isVideo === true
                                anchors.centerIn: parent
                                width: 22; height: 22; radius: 11
                                color: "#000000a0"
                                Text {
                                    anchors.centerIn: parent
                                    text: "▶"; color: "white"; font.pixelSize: 10
                                }
                            }
                            Item {
                                objectName: "timelineEditsFoldMark"
                                visible: cell.modelData.hasEdits === true
                                width: 10; height: 10
                                anchors.top: parent.top
                                anchors.right: parent.right
                                anchors.margins: 1
                                clip: true
                                Rectangle {
                                    width: 14; height: 14
                                    rotation: 45
                                    x: parent.width - width / 2
                                    y: -height / 2
                                    color: Theme.infoBar
                                }
                            }
                        }
                        MouseArea {
                            objectName: "timelineThumbMouseArea"
                            anchors.fill: parent
                            onClicked: view.requestOpen(
                                cell.modelData.id, cell.modelData.folderPath)
                        }
                    }
                }
            }
        }
    }
}

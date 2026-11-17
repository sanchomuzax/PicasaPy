import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// -- előnézeti bélyegkép-rács -------------------------------------
Rectangle {
    required property var hostWindow
    function positionAt(index) {
        previewGrid.positionViewAtIndex(index, GridView.Contain)
    }
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumHeight: 110
    color: Theme.contentPanel
    border.color: Theme.chromeBorder

    // #7178: a bélyegkép helyi menüje. Az eredetiben (`0x00733c70`, 20 bájtos
    // rekordok) négy parancs áll, ebben a sorrendben: Include File, Exclude
    // File, Include All, Exclude All. Ugyanazt a kiválasztási állapotot
    // módosítják, mint a bélyegkép alatti hivatkozás és az Include All /
    // Exclude All gomb: a vezérlő négy metódusát hívják.
    PicasaMenu {
        id: thumbMenu
        objectName: "importSourceThumbMenu"
        // a jobbkattintott bélyegkép forrás-útvonala (a két "File" parancs
        // erre hat)
        property string targetPath: ""

        MenuItem {
            objectName: "importSourceThumbMenuIncludeFile"
            text: qsTr("Include File")
            onTriggered: importSourceController.includeFile(
                thumbMenu.targetPath)
        }
        MenuItem {
            objectName: "importSourceThumbMenuExcludeFile"
            text: qsTr("Exclude File")
            onTriggered: importSourceController.excludeFile(
                thumbMenu.targetPath)
        }
        MenuItem {
            objectName: "importSourceThumbMenuIncludeAll"
            text: qsTr("Include All")
            onTriggered: importSourceController.includeAll()
        }
        MenuItem {
            objectName: "importSourceThumbMenuExcludeAll"
            text: qsTr("Exclude All")
            onTriggered: importSourceController.excludeAll()
        }
    }

    GridView {
        id: previewGrid
        objectName: "importSourcePreviewGrid"
        anchors.fill: parent
        anchors.margins: 4
        clip: true
        cellWidth: 76
        cellHeight: 92
        model: hostWindow.previewItems
        delegate: Rectangle {
            id: thumbFrame
            required property var modelData
            required property int index
            objectName: "importSourceThumb:" + thumbFrame.index
            width: 72
            height: 72
            color: Theme.thumbCard
            border.color: thumbFrame.index
                          === hostWindow.selectedPreviewIndex
                          ? Theme.selectionBlue
                          : (thumbFrame.modelData.duplicate
                             ? Theme.brandRed : Theme.thumbBorder)
            border.width: thumbFrame.index
                          === hostWindow.selectedPreviewIndex
                          || thumbFrame.modelData.duplicate ? 2 : 1
            opacity: thumbFrame.modelData.excluded ? 0.4 : 1.0

            Image {
                anchors.fill: parent
                anchors.margins: 2
                source: thumbFrame.modelData.thumbUrl
                // #1600: a bélyegkép-textúra a Qt gyorsítótárában KÖZÖS a
                // ráccsal, ami mipmapot kér (#83). Eltérő beállítás mellett a Qt
                // „Mipmap settings changed" figyelmeztetést ad, és VISSZAESIK a
                // korábbi szűrésre — a kép nem azzal a szűréssel jelenik meg,
                // amit kértünk (a tulajdonos Windowson hatszor látta).
                smooth: true
                mipmap: true
                fillMode: Image.PreserveAspectFit
                asynchronous: Qt.platform.pluginName !== "offscreen"
                // #441: az előnézet a beállított forgatással mutat —
                // az eredetiben is a MÁR kiegyenesített kép látszott
                rotation: 90 * (thumbFrame.modelData.rotation || 0)
            }

            // #7178: jobbklikk a bélyegképen a helyi menüt nyitja. Csak a
            // jobb gombot fogadja, így a bal gombos vezérlőket (forgatás,
            // csillag, Include/Exclude hivatkozás) nem zavarja.
            MouseArea {
                objectName: "importSourceThumbMenuArea:" + thumbFrame.index
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                onClicked: function (mouse) {
                    thumbMenu.targetPath = thumbFrame.modelData.path
                    thumbMenu.popup(thumbFrame, mouse.x, mouse.y)
                }
            }

            // #441: forgatás és csillagozás MÁR AZ IMPORT ELŐTT — az
            // eredeti import-képernyőn ugyanígy ott volt a két
            // forgató gomb és a csillagozás (`startoggle`).
            Row {
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.margins: 2
                spacing: 2
                Text {
                    objectName: "importRotateLeft:" + thumbFrame.index
                    text: "\u21ba"
                    font.pixelSize: Theme.fontSize
                    color: Theme.brandBlue
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -3
                        cursorShape: Qt.PointingHandCursor
                        onClicked: importSourceController.rotateFile(
                            thumbFrame.modelData.path, -1)

                        PressFeedbackOverlay { pressSource: parent }
                    }
                }
                Text {
                    objectName: "importRotateRight:" + thumbFrame.index
                    text: "\u21bb"
                    font.pixelSize: Theme.fontSize
                    color: Theme.brandBlue
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -3
                        cursorShape: Qt.PointingHandCursor
                        onClicked: importSourceController.rotateFile(
                            thumbFrame.modelData.path, 1)

                        PressFeedbackOverlay { pressSource: parent }
                    }
                }
            }
            Text {
                objectName: "importStar:" + thumbFrame.index
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.margins: 2
                text: "\u2605"
                font.pixelSize: Theme.fontSize
                color: thumbFrame.modelData.starred
                       ? Theme.starYellow : Theme.textGray
                opacity: thumbFrame.modelData.starred ? 1.0 : 0.5
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -3
                    cursorShape: Qt.PointingHandCursor
                    onClicked: importSourceController.toggleStar(
                        thumbFrame.modelData.path)

                    PressFeedbackOverlay { pressSource: parent }
                }
            }

            Text {
                id: toggleLabel
                objectName: "importSourceToggleLabel:" + thumbFrame.index
                anchors.top: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                text: thumbFrame.modelData.excluded
                      ? qsTr("Include") : qsTr("Exclude")
                font.pixelSize: Theme.fontSize - 1
                color: Theme.brandBlue
            }
            MouseArea {
                objectName: "importSourceToggle:" + thumbFrame.index
                anchors.fill: toggleLabel
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    if (thumbFrame.modelData.excluded) {
                        importSourceController.includeFile(
                            thumbFrame.modelData.path)
                    } else {
                        importSourceController.excludeFile(
                            thumbFrame.modelData.path)
                    }
                }

                PressFeedbackOverlay { pressSource: parent }
            }
        }
        ScrollBar.vertical: PicasaScrollBar {}
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// -- előnézeti bélyegkép-rács -------------------------------------
Rectangle {
    id: previewPanelRoot
    required property var hostWindow
    readonly property var selectedItem:
        hostWindow.selectedPreviewIndex >= 0
        && hostWindow.selectedPreviewIndex < hostWindow.previewItems.length
            ? hostWindow.previewItems[hostWindow.selectedPreviewIndex] : null
    property bool fallbackToThumbnail: false
    readonly property string selectedPath: selectedItem ? selectedItem.path : ""

    onSelectedPathChanged: fallbackToThumbnail = false

    function positionAt(index) {
        previewGrid.positionViewAtIndex(index, GridView.Contain)
    }
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumHeight: 110
    color: Theme.contentPanel
    border.color: Theme.chromeBorder

    RowLayout {
        anchors.fill: parent
        anchors.margins: 4
        spacing: 8

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
        Layout.preferredWidth: 168
        Layout.fillHeight: true
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
            border.color: hostWindow.isPreviewSelected(
                              thumbFrame.modelData.path)
                          || thumbFrame.index === hostWindow.selectedPreviewIndex
                          ? Theme.selectionBlue
                          : (thumbFrame.modelData.duplicate
                             ? Theme.brandRed : Theme.thumbBorder)
            border.width: hostWindow.isPreviewSelected(
                              thumbFrame.modelData.path)
                          || thumbFrame.index === hostWindow.selectedPreviewIndex
                          || thumbFrame.modelData.duplicate ? 2 : 1
            opacity: thumbFrame.modelData.excluded ? 0.4 : 1.0

            MouseArea {
                objectName: "importSourceSelect:" + thumbFrame.index
                anchors.fill: parent
                onClicked: hostWindow.togglePreviewSelection(
                    thumbFrame.modelData.path, thumbFrame.index)

                PressFeedbackOverlay { pressSource: parent }
            }

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

            Text {
                objectName: "importSourceSelectedMark:" + thumbFrame.index
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.margins: 3
                visible: hostWindow.isPreviewSelected(
                             thumbFrame.modelData.path)
                text: "✓"
                color: Theme.picasaGreen
                font.pixelSize: Theme.fontSize
                font.bold: true
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

    Rectangle {
        id: largePreviewPane
        objectName: "importSourceLargePreviewPane"
        Layout.fillWidth: true
        Layout.fillHeight: true
        color: Theme.canvasBg
        border.color: Theme.thumbBorder

        Row {
            objectName: "importSourceLargePreviewControls"
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.margins: 6
            spacing: 3
            visible: previewPanelRoot.selectedItem !== null
            z: 1

            PicasaButton {
                objectName: "importSourceLargePreviousButton"
                text: "‹"
                enabled: previewPanelRoot.selectedItem !== null
                         && hostWindow.selectedPreviewIndex > 0
                onClicked: hostWindow.stepPreview(-1)
            }
            PicasaButton {
                objectName: "importSourceLargeNextButton"
                text: "›"
                enabled: previewPanelRoot.selectedItem !== null
                         && hostWindow.selectedPreviewIndex
                                < hostWindow.previewItems.length - 1
                onClicked: hostWindow.stepPreview(1)
            }
            PicasaButton {
                objectName: "importSourceLargeRotateLeftButton"
                text: "↺"
                enabled: previewPanelRoot.selectedItem !== null
                onClicked: importSourceController.rotateFile(
                    previewPanelRoot.selectedItem.path, -1)
            }
            PicasaButton {
                objectName: "importSourceLargeRotateRightButton"
                text: "↻"
                enabled: previewPanelRoot.selectedItem !== null
                onClicked: importSourceController.rotateFile(
                    previewPanelRoot.selectedItem.path, 1)
            }
            PicasaButton {
                objectName: "importSourceLargeStarButton"
                text: previewPanelRoot.selectedItem
                    && previewPanelRoot.selectedItem.starred ? "★" : "☆"
                enabled: previewPanelRoot.selectedItem !== null
                onClicked: importSourceController.toggleStar(
                    previewPanelRoot.selectedItem.path)
            }
            PicasaButton {
                objectName: "importSourceLargeExcludeButton"
                text: previewPanelRoot.selectedItem
                    && previewPanelRoot.selectedItem.excluded
                        ? qsTr("Include") : qsTr("Exclude")
                enabled: previewPanelRoot.selectedItem !== null
                onClicked: {
                    if (previewPanelRoot.selectedItem.excluded)
                        importSourceController.includeFile(
                            previewPanelRoot.selectedItem.path)
                    else
                        importSourceController.excludeFile(
                            previewPanelRoot.selectedItem.path)
                }
            }
        }

        Image {
            objectName: "importSourceLargePreviewImage"
            anchors.fill: parent
            anchors.margins: 8
            // A saját Rectangle-háttér mögé kerülne -1-es z-vel, így a
            // képforrás betöltődne, de a felhasználó csak a háttérszínt látná.
            // A z=0 a panel háttere fölé, az 1-es vezérlősor alá rajzol.
            z: 0
            source: previewPanelRoot.selectedItem
                ? (previewPanelRoot.fallbackToThumbnail
                   || !previewPanelRoot.selectedItem.imageUrl
                   ? previewPanelRoot.selectedItem.thumbUrl
                   : previewPanelRoot.selectedItem.imageUrl)
                : ""
            sourceSize.width: width
            sourceSize.height: height
            smooth: true
            mipmap: true
            fillMode: Image.PreserveAspectFit
            asynchronous: Qt.platform.pluginName !== "offscreen"
            rotation: previewPanelRoot.selectedItem
                ? 90 * (previewPanelRoot.selectedItem.rotation || 0) : 0
            onStatusChanged: {
                if (status === Image.Error
                        && !previewPanelRoot.fallbackToThumbnail
                        && previewPanelRoot.selectedItem
                        && previewPanelRoot.selectedItem.thumbUrl)
                    previewPanelRoot.fallbackToThumbnail = true
            }
        }

        Text {
            objectName: "importSourceFileInfoText"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 8
            elide: Text.ElideMiddle
            text: previewPanelRoot.selectedItem
                ? previewPanelRoot.selectedItem.path : ""
            color: Theme.textGray
            font.pixelSize: Theme.fontSize - 1
        }
    }
    }
}

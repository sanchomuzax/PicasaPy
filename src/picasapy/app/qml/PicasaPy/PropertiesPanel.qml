import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Tulajdonságok-panel (#13, Alt+Enter) — a Picasa jobb oldali Properties
// paneljének mása: a kijelölt kép fájl- és EXIF-adatai, CSAK olvasásra.
// Buta komponens: a sorokat kívülről kapja ({label, value} párok listája).
Rectangle {
    id: panel

    // {label, value} sorok (controller.propertiesOf)
    property var entries: []
    property bool hasSelection: false
    // A keywords-dialógus célja: a fókuszkép fejléce és a kijelölés címkézése.
    property var appController: null
    property var selectedRows: []
    property int focusRow: -1

    readonly property var focusedPhoto:
        panel.appController && panel.focusRow >= 0
        ? (panel.appController.photos.revision,
           panel.appController.photos.itemAt(panel.focusRow))
        : ({})
    readonly property string focusedFileName: {
        if (!panel.focusedPhoto) return ""
        return String(panel.focusedPhoto.name || "")
    }
    readonly property var selectedKeywords:
        panel.appController && panel.selectedRows.length > 0
        ? (panel.appController.photos.revision,
           panel.appController.keywordsOfRows(panel.selectedRows))
        : []

    signal closeRequested()
    signal editTagsRequested()
    signal adjustTimestampRequested()

    property string currentContextType: ""

    function isDateEntry(entry) {
        if (!entry) return false
        var lbl = entry.label || ""
        return lbl === "Camera Date" || lbl === qsTranslate("", "Camera Date")
    }

    function isKeywordsEntry(entry) {
        if (!entry) return false
        var lbl = entry.label || ""
        return lbl === "Keywords" || lbl === "Tags"
            || lbl === qsTranslate("", "Keywords")
            || lbl === qsTr("Tags") || lbl === qsTr("Keywords")
    }

    color: Theme.panelBg
    border.color: Theme.chromeBorder

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        //: #754: a CÍM és a bezáró gomb a FIÓK közös fejlécében él
        //: (`RightDrawer`), nem a panelben — az eredetiben egy fejléc
        //: van, és annak címe a lap neve.

        Text {
            objectName: "propertiesFileTitle"
            visible: panel.hasSelection
            Layout.fillWidth: true
            text: qsTr("Properties of %s:").replace(
                "%s", panel.focusedFileName)
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.ink
        }

        Text {
            visible: !panel.hasSelection
            Layout.fillWidth: true
            text: qsTr("Select a picture to see its properties.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize - 1
            font.italic: true
            color: Theme.textGray
        }

        ListView {
            id: propertyList
            objectName: "propertyList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: panel.hasSelection
            model: panel.entries
            spacing: 4
            delegate: Column {
                required property var modelData
                width: propertyList.width
                spacing: 1
                Text {
                    width: parent.width
                    // A sorforrás a Python API régi címkéit tartja meg;
                    // a panelen az eredeti Picasa feliratai jelennek meg.
                    text: modelData.label === "File Path" ? qsTr("Location")
                        : modelData.label === "Keywords" ? qsTr("Tags")
                        : modelData.label
                    font.pixelSize: Theme.fontSize - 2
                    color: Theme.textGray
                }
                Text {
                    width: parent.width
                    text: modelData.value
                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                }
            }
            ScrollBar.vertical: PicasaScrollBar {}
        }

        RowLayout {
            id: keywordsPropertyRow
            objectName: "keywordsPropertyRow"
            visible: panel.hasSelection
            Layout.fillWidth: true
            spacing: 8

            PicasaButton {
                objectName: "editKeywordsButton"
                text: qsTr("Keywords")
                enabled: panel.appController !== null && panel.focusRow >= 0
                onClicked: panel.editTagsRequested()
            }
            Text {
                objectName: "keywordsPropertyValue"
                Layout.fillWidth: true
                text: panel.selectedKeywords.join(", ")
                elide: Text.ElideRight
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
        }
    }

    KeywordsDialog {
        id: keywordsDialog
        objectName: panel.objectName === "viewerPropertiesPanel"
                    ? "viewerKeywordsDialog" : "keywordsDialog"
        controller: panel.appController
    }

    PicasaMenu {
        id: propertiesContextMenu
        objectName: "propertiesPanelContextMenu"
        parent: panel

        MenuItem {
            objectName: "propertiesMenuEditTags"
            text: qsTr("Edit Tags")
            visible: panel.currentContextType === "keywords"
            onTriggered: panel.editTagsRequested()
        }

        MenuItem {
            objectName: "propertiesMenuAdjustTimestamp"
            text: qsTr("Adjust &Date and Time...")
            visible: panel.currentContextType === "date"
            onTriggered: panel.adjustTimestampRequested()
        }
    }

    MouseArea {
        objectName: "propertiesPanelContextArea"
        parent: panel
        anchors.fill: panel
        z: 10
        visible: panel.visible
        acceptedButtons: Qt.RightButton
        onClicked: function(mouse) {
            panel.currentContextType = ""
            if (!panel.hasSelection) return

            if (keywordsPropertyRow.visible) {
                var kwPt = mapToItem(keywordsPropertyRow, mouse.x, mouse.y)
                if (kwPt.x >= 0 && kwPt.x <= keywordsPropertyRow.width &&
                    kwPt.y >= 0 && kwPt.y <= keywordsPropertyRow.height) {
                    panel.currentContextType = "keywords"
                    propertiesContextMenu.popup()
                    return
                }
            }

            if (propertyList.visible) {
                var pList = mapToItem(propertyList, mouse.x, mouse.y)
                if (pList.x >= 0 && pList.x <= propertyList.width &&
                    pList.y >= 0 && pList.y <= propertyList.height) {
                    var listPt = mapToItem(propertyList.contentItem, mouse.x, mouse.y)
                    var idx = propertyList.indexAt(listPt.x, listPt.y)
                    if (idx >= 0 && panel.entries && idx < panel.entries.length) {
                        var entry = panel.entries[idx]
                        if (panel.isDateEntry(entry)) {
                            panel.currentContextType = "date"
                            propertiesContextMenu.popup()
                            return
                        } else if (panel.isKeywordsEntry(entry)) {
                            panel.currentContextType = "keywords"
                            propertiesContextMenu.popup()
                            return
                        }
                    }
                }
            }
        }
    }
}

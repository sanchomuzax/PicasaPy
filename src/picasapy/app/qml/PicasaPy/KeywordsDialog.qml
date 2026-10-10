import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A PropertiesPanel „Keywords” sorának címkeszerkesztője (#4578).
// A képadatokat és a kijelölést a PropertiesPanel adja; a fájlmódosítást
// kizárólag a KeywordsMixin meglévő műveletei végzik.
Dialog {
    id: root
    objectName: "keywordsDialog"
    title: qsTr("Tags")
    modal: true
    focus: true
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 470
    height: 360

    property var controller: null
    property var rowIndexes: []
    property var photoInfo: ({})
    property var tags: []
    property string dateValue: ""
    readonly property bool thumbnailReady:
        photoThumbnail.status === Image.Ready
    readonly property string photoName: String(root.photoInfo.name || "")
    readonly property string dateText:
        formatDate(root.dateValue || root.photoInfo.takenAt || "")
    readonly property bool readOnlySelection:
        root.controller && root.rowIndexes.length > 0
        ? (root.controller.photos.revision,
           root.controller.selectionReadOnly(root.rowIndexes))
        : false

    function formatDate(value) {
        var raw = String(value || "")
        if (raw.length === 0)
            return ""
        var stamp = new Date(raw.replace(" ", "T"))
        return isNaN(stamp.getTime()) ? raw.slice(0, 10) : stamp.toLocaleDateString()
    }

    function refreshTags() {
        root.tags = root.controller
            ? root.controller.keywordsOfRows(root.rowIndexes)
            : []
        keywordList.currentIndex = -1
    }

    function openFor(rows, focusRow, info) {
        root.rowIndexes = rows ? rows.slice() : []
        root.photoInfo = info || {}
        root.dateValue = root.controller
            ? root.controller.photoDateAt(focusRow) : ""
        addKeywordField.clear()
        root.refreshTags()
        root.open()
    }

    onOpened: addKeywordField.forceActiveFocus()

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        RowLayout {
            objectName: "keywordPhotoHeader"
            Layout.fillWidth: true
            Layout.preferredHeight: 92
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 120
                Layout.preferredHeight: 88
                color: Theme.chromeBorder

                Image {
                    id: photoThumbnail
                    objectName: "keywordPhotoThumbnail"
                    anchors.fill: parent
                    anchors.margins: 1
                    source: root.photoInfo.thumbUrl || ""
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                    smooth: true
                    asynchronous: true
                    cache: true
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 6

                Text {
                    objectName: "keywordPhotoName"
                    Layout.fillWidth: true
                    text: root.photoName
                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                    font.pixelSize: Theme.fontSize
                    font.bold: true
                    color: Theme.ink
                }
                Text {
                    objectName: "keywordPhotoDate"
                    Layout.fillWidth: true
                    text: root.dateText
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
                Item { Layout.fillHeight: true }
            }
        }

        Text {
            objectName: "keywordListHeading"
            text: qsTr("Tags:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }

        ListView {
            id: keywordList
            objectName: "keywordList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 62
            clip: true
            model: root.tags
            spacing: 2

            delegate: Rectangle {
                id: keywordRow
                required property string modelData
                required property int index
                objectName: "keywordListRow" + index
                width: keywordList.width
                height: 24
                radius: 3
                color: index === keywordList.currentIndex
                       ? Theme.panelSelection : "transparent"

                Text {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    verticalAlignment: Text.AlignVCenter
                    text: keywordRow.modelData
                    font.pixelSize: Theme.fontSize
                    color: keywordRow.index === keywordList.currentIndex
                           ? Theme.panelSelectionText : Theme.ink
                }

                TapHandler {
                    onTapped: keywordList.currentIndex = keywordRow.index
                }
            }
            ScrollBar.vertical: PicasaScrollBar {}
        }

        Text {
            objectName: "keywordReadOnlyNotice"
            visible: root.readOnlySelection
            Layout.fillWidth: true
            text: qsTr("Tags cannot be modified because one or more items are read-only.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Text {
                text: qsTr("Add Tag:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            TextField {
                id: addKeywordField
                objectName: "keywordAddField"
                Layout.fillWidth: true
                enabled: !root.readOnlySelection
                font.pixelSize: Theme.fontSize
                onAccepted: addKeywordButton.clicked()
                TextFieldContextArea {}
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8

            PicasaButton {
                id: addKeywordButton
                objectName: "keywordAddButton"
                text: qsTr("Add")
                enabled: !root.readOnlySelection
                         && addKeywordField.text.trim().length > 0
                onClicked: {
                    if (!root.controller || root.rowIndexes.length === 0)
                        return
                    root.controller.addKeywordToRows(
                        root.rowIndexes, addKeywordField.text)
                    addKeywordField.clear()
                    root.refreshTags()
                }
            }
            PicasaButton {
                objectName: "keywordRemoveButton"
                text: qsTr("Remove")
                enabled: !root.readOnlySelection && keywordList.currentIndex >= 0
                onClicked: {
                    if (!root.controller || keywordList.currentIndex < 0)
                        return
                    root.controller.removeKeywordFromRows(
                        root.rowIndexes, root.tags[keywordList.currentIndex])
                    root.refreshTags()
                }
            }
            PicasaButton {
                objectName: "keywordDoneButton"
                text: qsTr("Done")
                onClicked: root.close()
            }
        }
    }
}

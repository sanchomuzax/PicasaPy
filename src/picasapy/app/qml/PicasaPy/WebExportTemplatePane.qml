import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root

    property bool ftpMode: false
    property bool exporting: false
    property var templates: []
    property var htmlTemplateEntries: []
    property int htmlTemplateIndex: 0
    property int templateIndex: 0
    property url templatePreview: ""
    property var templateDisplayName: function (template) {
        return template ? template.name : ""
    }
    property var templateDescription: function (template) {
        return template ? template.description : ""
    }

    signal htmlTemplateSelected(string templateId)
    signal ftpTemplateSelected(int index)

    spacing: 10

    ColumnLayout {
        objectName: "webExportHtmlTemplateSection"
        Layout.fillWidth: true
        spacing: 2
        enabled: !root.exporting
        visible: !root.ftpMode
        Text {
            objectName: "webExportInstruction"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            //: picasapy-origin: picasa
            //: picasapy-origin-key: webexport:webexport/label20.title
            text: qsTr("Click a Template Name to view an example.  When you have made your selection, click Export.")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            ColumnLayout {
                Layout.preferredWidth: 340
                Layout.fillWidth: true
                spacing: 6
                ListView {
                    id: templateList
                    objectName: "webExportTemplateList"
                    property real rowHeight: 34
                    Layout.fillWidth: true
                    Layout.preferredHeight: 7 * rowHeight
                    clip: true
                    model: root.htmlTemplateEntries
                    currentIndex: root.htmlTemplateIndex
                    delegate: ItemDelegate {
                        required property var modelData
                        required property int index
                        width: templateList.width
                        height: templateList.rowHeight
                        text: root.templateDisplayName(modelData)
                        highlighted: ListView.isCurrentItem
                        onClicked: root.htmlTemplateSelected(modelData.id)
                    }
                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }
                }
                Text {
                    objectName: "webExportTemplateDescription"
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: root.templateDescription(
                        root.templates[root.templateIndex])
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.textGray
                }
            }
            Image {
                objectName: "webExportTemplatePreview"
                source: root.templatePreview
                visible: root.templatePreview.toString().length > 0
                // A sablon saját csomagolt preview.svg állománya.
                sourceSize.width: 480
                sourceSize.height: 300
                fillMode: Image.PreserveAspectFit
                Layout.preferredWidth: 280
                Layout.preferredHeight: 175
                Layout.alignment: Qt.AlignTop
            }
        }
    }

    ColumnLayout {
        objectName: "webExportFtpTemplateSection"
        Layout.fillWidth: true
        spacing: 2
        enabled: !root.exporting
        visible: root.ftpMode
        Text {
            text: qsTr("Template:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        PicasaComboBox {
            id: templateBox
            objectName: "webExportTemplateBox"
            Layout.fillWidth: true
            model: root.templates.map(function (template) { return template.name })
            currentIndex: root.templateIndex
            onActivated: root.ftpTemplateSelected(currentIndex)
        }
        Image {
            objectName: "webExportFtpTemplatePreview"
            source: root.templatePreview
            visible: root.templatePreview.toString().length > 0
            sourceSize.width: 320
            sourceSize.height: 200
            fillMode: Image.PreserveAspectFit
            Layout.preferredWidth: 160
            Layout.preferredHeight: 100
            Layout.topMargin: 4
        }
        Text {
            objectName: "webExportFtpTemplateDescription"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: root.templateIndex >= 0
                  && root.templateIndex < root.templates.length
                  ? root.templates[root.templateIndex].description : ""
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
    }
}

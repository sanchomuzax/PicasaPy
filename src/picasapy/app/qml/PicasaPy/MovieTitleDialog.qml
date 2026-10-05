import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A Picasa `titledialog`: title text, font, size and style are confirmed
// before the slide is added to the movie. The movie's Slide tab keeps its
// own controls for editing the selected slide.
Dialog {
    id: titleDialog

    objectName: "movieTitleDialog"
    modal: true
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(520, parent ? parent.width - 32 : 520)
    height: Math.min(560, parent ? parent.height - 32 : 560)
    standardButtons: Dialog.NoButton
    Overlay.modal: Rectangle { color: "#66000000" }
    background: Rectangle {
        color: Theme.chromeBg
        border.color: Theme.chromeBorder
        radius: 4
    }

    property string captionText: ""
    property color textColor: "#ffffff"
    property color backgroundColor: "#000000"
    property real previewAspectRatio: 4 / 3
    readonly property var sizeValues: [
        8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96,
    ]
    readonly property var styleValues: [
        qsTr("Centered"), qsTr("I'm Feeling Lucky"), qsTr("Caption"),
        qsTr("Caption - Classic"), qsTr("Gradient - Black"),
        qsTr("Gradient - White"), qsTr("Transparent - Black"),
        qsTr("Transparent - White"), qsTr("Scrolling Credits"),
        qsTr("Music Video - Left"), qsTr("Music Video - Right"),
        qsTr("Caption - Typewriter"),
    ]
    readonly property var typefaceValues: [
        qsTr("Normal"), qsTr("Bold"), qsTr("Italic"), qsTr("Bold Italic"),
    ]

    signal slideAdded(var slide)
    signal textColorRequested()
    signal backgroundColorRequested()

    function openForCaption(caption, defaults) {
        captionText = String(caption || "")
        captionCheck.checked = false
        var initial = defaults || {}
        titleTextField.text = initial.text || qsTr("Text")
        var fonts = fontFamilyBox.model
        fontFamilyBox.currentIndex = fonts.indexOf(initial.font)
        if (fontFamilyBox.currentIndex < 0)
            fontFamilyBox.currentIndex = fonts.length > 0 ? 0 : -1
        var sizeIndex = sizeValues.indexOf(initial.size)
        sizeList.currentIndex = sizeIndex >= 0 ? sizeIndex : 4
        styleList.currentIndex = initial.style >= 0 ? initial.style : 0
        typefaceList.currentIndex = initial.bold
                ? (initial.italic ? 3 : 1)
                : (initial.italic ? 2 : 0)
        outlineCheck.checked = !!initial.outline
        open()
    }

    function currentSlide() {
        var caption = captionCheck.checked ? captionText : ""
        return {
            text: caption || titleTextField.text || qsTr("Text"),
            font: fontFamilyBox.currentText || "DejaVuSans",
            size: sizeValues[sizeList.currentIndex],
            style: styleList.currentIndex,
            bold: typefaceList.currentIndex === 1
                || typefaceList.currentIndex === 3,
            italic: typefaceList.currentIndex === 2
                || typefaceList.currentIndex === 3,
            outline: outlineCheck.checked,
            textColor: textColor.toString(),
            backgroundColor: backgroundColor.toString(),
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 8

        Text {
            text: qsTr("Text slide:")
            color: Theme.ink
            font.pixelSize: Theme.fontSize
        }
        TextField {
            id: titleTextField
            objectName: "titledialog/captiontext"
            Layout.fillWidth: true
            text: qsTr("Text")
            selectByMouse: true
            TextFieldContextArea {}
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Text {
                text: qsTr("Font:")
                color: Theme.ink
                font.pixelSize: Theme.fontSize
            }
            PicasaComboBox {
                id: fontFamilyBox
                objectName: "titledialog/fontfamily"
                Layout.fillWidth: true
                model: Qt.fontFamilies()
                currentIndex: model.length > 0 ? 0 : -1
            }
            PicasaComboBox {
                id: typefaceList
                objectName: "titledialog/typeface"
                Layout.preferredWidth: 132
                model: titleDialog.typefaceValues
                currentIndex: 0
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Text {
                text: qsTr("Size:")
                color: Theme.ink
                font.pixelSize: Theme.fontSize
            }
            PicasaComboBox {
                id: sizeList
                objectName: "titledialog/sizelist"
                Layout.preferredWidth: 82
                model: titleDialog.sizeValues.map(function(size) {
                    return String(size)
                })
                currentIndex: 4
            }
            Text {
                text: qsTr("Style:")
                color: Theme.ink
                font.pixelSize: Theme.fontSize
            }
            PicasaComboBox {
                id: styleList
                objectName: "titledialog/stylelist"
                Layout.fillWidth: true
                model: titleDialog.styleValues
                currentIndex: 0
            }
        }

        RowLayout {
            Layout.fillWidth: true
            CheckBox {
                id: captionCheck
                objectName: "titledialog/captionchk"
                text: qsTr("Caption")
                enabled: titleDialog.captionText.length > 0
            }
            CheckBox {
                id: outlineCheck
                objectName: "titledialog/outline"
                text: qsTr("Automatic Outline")
            }
            Item { Layout.fillWidth: true }
        }

        RowLayout {
            Layout.fillWidth: true
            Button {
                text: qsTr("Text color")
                onClicked: titleDialog.textColorRequested()
            }
            Button {
                text: qsTr("Background color")
                onClicked: titleDialog.backgroundColorRequested()
            }
        }

        Rectangle {
            id: previewImage
            objectName: "titledialog/previewimage"
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 110
            Layout.preferredHeight: Math.min(
                190, width / Math.max(0.5, titleDialog.previewAspectRatio))
            color: titleDialog.backgroundColor
            border.color: Theme.listPanelBorder
            border.width: 1
            clip: true

            readonly property bool hasBand: [4, 5, 6, 7].indexOf(
                styleList.currentIndex) >= 0

            Rectangle {
                objectName: "titledialog/previewStyleBand"
                visible: previewImage.hasBand
                x: 0
                y: previewText.y - 10
                width: parent.width
                height: previewText.height + 20
                color: [4, 6].indexOf(styleList.currentIndex) >= 0
                    ? "#b4000000" : "#b4ffffff"
            }
            Text {
                id: previewText
                objectName: "titledialog/previewtext"
                x: 16
                width: parent.width - 32
                text: captionCheck.checked && titleDialog.captionText.length > 0
                    ? titleDialog.captionText
                    : (titleTextField.text || qsTr("Text"))
                y: [2, 3, 11].indexOf(styleList.currentIndex) >= 0
                    ? parent.height - height - 12
                    : (parent.height - height) / 2
                wrapMode: Text.WordWrap
                horizontalAlignment: styleList.currentIndex === 9
                    ? Text.AlignLeft
                    : styleList.currentIndex === 10 ? Text.AlignRight
                    : Text.AlignHCenter
                color: [4, 6].indexOf(styleList.currentIndex) >= 0
                    ? "#ffffff"
                    : [5, 7].indexOf(styleList.currentIndex) >= 0
                        ? "#000000" : titleDialog.textColor
                font.family: fontFamilyBox.currentText
                font.pixelSize: titleDialog.sizeValues[sizeList.currentIndex]
                font.weight: [1, 3].indexOf(typefaceList.currentIndex) >= 0
                    ? Font.Bold : Font.Normal
                font.italic: [2, 3].indexOf(typefaceList.currentIndex) >= 0
                style: outlineCheck.checked
                    || [3, 11].indexOf(styleList.currentIndex) >= 0
                    ? Text.Outline : Text.Normal
                styleColor: color === "#000000" ? "#ffffff" : "#000000"
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button {
                objectName: "titledialog/cancel"
                text: qsTr("Cancel")
                onClicked: titleDialog.reject()
            }
            Button {
                objectName: "titledialog/add"
                text: qsTr("Add")
                onClicked: {
                    titleDialog.slideAdded(titleDialog.currentSlide())
                    titleDialog.accept()
                }
            }
        }
    }
}

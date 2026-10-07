import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350/#4447: az egyesített lista a Picasa Windows- és Mac-csoportjait
// mutatja. A kiválasztás QSettings-be kerül, és a könyvtár-szkenner használja.
// #4488: a referencia tartalompanelei 744 px szélesek; a jelölők x=242 px-nél
// indulnak, a sorok pedig 22 px magasak. Az arány a panel szélességéhez köt,
// így az ablakkeret és a futtató betűmetrikája nem tolja el a sort.
ColumnLayout {
    id: root
    spacing: 0
    readonly property real referenceLeftInset: width * (242.0 / 744.0)
    readonly property var filetypeController:
        typeof controller !== "undefined" ? controller : null

    function fileTypeEnabled(group, defaultValue) {
        return root.filetypeController
            ? root.filetypeController.fileTypeEnabled(group)
            : defaultValue
    }

    function setFileTypeEnabled(group, checked) {
        if (root.filetypeController)
            root.filetypeController.setFileTypeEnabled(group, checked)
    }

    Text {
        text: qsTr("Display JPEG files and:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        Layout.topMargin: 8
        verticalAlignment: Text.AlignVCenter
    }

    CheckBox {
        objectName: "optionsFileTypeBmpCheck"
        text: qsTr(".bmp")
        checked: root.fileTypeEnabled("bmp", true)
        onToggled: root.setFileTypeEnabled("bmp", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsFileTypeGifCheck"
        text: qsTr(".gif")
        checked: root.fileTypeEnabled("gif", true)
        onToggled: root.setFileTypeEnabled("gif", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsFileTypePngCheck"
        text: qsTr(".png")
        checked: root.fileTypeEnabled("png", true)
        onToggled: root.setFileTypeEnabled("png", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsFileTypeTgaCheck"
        text: qsTr(".tga")
        checked: root.fileTypeEnabled("tga", true)
        onToggled: root.setFileTypeEnabled("tga", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsFileTypeTiffCheck"
        text: qsTr(".tif, .tiff")
        checked: root.fileTypeEnabled("tiff", true)
        onToggled: root.setFileTypeEnabled("tiff", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsFileTypeWebpCheck"
        text: qsTr(".webp")
        checked: root.fileTypeEnabled("webp", true)
        onToggled: root.setFileTypeEnabled("webp", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsFileTypePsdCheck"
        text: qsTr(".psd (Photoshop)")
        checked: root.fileTypeEnabled("psd", true)
        onToggled: root.setFileTypeEnabled("psd", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    RowLayout {
        spacing: 8
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22

        CheckBox {
            objectName: "optionsFileTypeRawCheck"
            text: qsTr("RAW formats")
            checked: root.fileTypeEnabled("raw", true)
            onToggled: root.setFileTypeEnabled("raw", checked)
            padding: 0
            leftPadding: 0
            Layout.preferredHeight: 22
            contentItem: Text {
                leftPadding: parent.indicator.width + parent.spacing
                text: parent.text
                font: parent.font
                color: Theme.ink
                verticalAlignment: Text.AlignVCenter
            }
        }
        // A referencián a link zárójelben áll, a zárójel nem része a linknek.
        RowLayout {
            spacing: 0

            Text {
                objectName: "optionsFileTypeSupportedFormatsOpenParen"
                text: "("
                color: Theme.ink
                font.pixelSize: Theme.fontSize
            }
            Text {
                id: supportedFormatsLink
                objectName: "optionsFileTypeSupportedFormatsLink"
                text: qsTr("Supported Formats")
                color: Theme.linkBlue
                font.pixelSize: Theme.fontSize
                font.underline: true
                activeFocusOnTab: true
                Accessible.role: Accessible.Link
                Accessible.name: text

                TapHandler {
                    cursorShape: Qt.PointingHandCursor
                    onTapped: supportedRawFormatsDialog.open()
                }
                Keys.onReturnPressed: supportedRawFormatsDialog.open()
                Keys.onEnterPressed: supportedRawFormatsDialog.open()
            }
            Text {
                text: ")"
                color: Theme.ink
                font.pixelSize: Theme.fontSize
            }
        }
    }
    CheckBox {
        objectName: "optionsFileTypeMoviesCheck"
        text: qsTr("Videos (.mov, .mpg, .m4v, .3gp, .avi, ...)")
        checked: root.fileTypeEnabled("movies", true)
        onToggled: root.setFileTypeEnabled("movies", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }
    CheckBox {
        objectName: "optionsFileTypeQuickTimeCheck"
        text: qsTr("Quicktime Movies (.MOV)")
        checked: root.fileTypeEnabled("quicktime", true)
        onToggled: root.setFileTypeEnabled("quicktime", checked)
        padding: 0
        leftPadding: 0
        Layout.fillWidth: true
        Layout.leftMargin: root.referenceLeftInset
        Layout.preferredHeight: 22
        contentItem: Text {
            leftPadding: parent.indicator.width + parent.spacing
            text: parent.text
            font: parent.font
            color: Theme.ink
            verticalAlignment: Text.AlignVCenter
        }
    }

    Item { Layout.fillHeight: true }

    Dialog {
        id: supportedRawFormatsDialog
        objectName: "optionsFileTypeSupportedRawFormatsDialog"
        title: qsTr("RAW formats")
        modal: true
        width: 420
        standardButtons: DialogButtonBox.NoButton

        contentItem: Text {
            objectName: "optionsFileTypeSupportedRawFormatsText"
            text: root.filetypeController
                ? root.filetypeController.supportedRawExtensions().join(", ")
                : ""
            color: Theme.ink
            font.pixelSize: Theme.fontSize
            wrapMode: Text.Wrap
        }

        footer: DialogButtonBox {
            alignment: Qt.AlignRight
            Button {
                text: qsTr("OK")
                onClicked: supportedRawFormatsDialog.close()
            }
        }
    }
}

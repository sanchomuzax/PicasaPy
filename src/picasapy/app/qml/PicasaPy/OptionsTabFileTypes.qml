import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350/#4447: az egyesített lista a Picasa Windows- és Mac-csoportjait
// mutatja. A kiválasztás QSettings-be kerül, és a könyvtár-szkenner használja.
ColumnLayout {
    id: root
    spacing: 8
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
    }

    CheckBox {
        objectName: "optionsFileTypeBmpCheck"
        text: qsTr("BMP")
        checked: root.fileTypeEnabled("bmp", true)
        onToggled: root.setFileTypeEnabled("bmp", checked)
    }
    CheckBox {
        objectName: "optionsFileTypeGifCheck"
        text: qsTr("GIF")
        checked: root.fileTypeEnabled("gif", true)
        onToggled: root.setFileTypeEnabled("gif", checked)
    }
    CheckBox {
        objectName: "optionsFileTypePngCheck"
        text: qsTr("PNG")
        checked: root.fileTypeEnabled("png", true)
        onToggled: root.setFileTypeEnabled("png", checked)
    }
    CheckBox {
        objectName: "optionsFileTypeTgaCheck"
        text: qsTr("TGA")
        checked: root.fileTypeEnabled("tga", true)
        onToggled: root.setFileTypeEnabled("tga", checked)
    }
    CheckBox {
        objectName: "optionsFileTypeTiffCheck"
        text: qsTr("TIFF")
        checked: root.fileTypeEnabled("tiff", true)
        onToggled: root.setFileTypeEnabled("tiff", checked)
    }
    CheckBox {
        objectName: "optionsFileTypeWebpCheck"
        text: qsTr("WEBP")
        checked: root.fileTypeEnabled("webp", true)
        onToggled: root.setFileTypeEnabled("webp", checked)
    }
    CheckBox {
        objectName: "optionsFileTypePsdCheck"
        text: qsTr("PSD")
        checked: root.fileTypeEnabled("psd", true)
        onToggled: root.setFileTypeEnabled("psd", checked)
    }
    RowLayout {
        spacing: 8
        CheckBox {
            objectName: "optionsFileTypeRawCheck"
            text: qsTr("RAW")
            checked: root.fileTypeEnabled("raw", true)
            onToggled: root.setFileTypeEnabled("raw", checked)
        }
        Text {
            text: qsTr("Supported Formats")
            color: Theme.linkBlue
            font.pixelSize: Theme.fontSize
            font.underline: true
        }
    }
    CheckBox {
        objectName: "optionsFileTypeMoviesCheck"
        text: qsTr("Movies")
        checked: root.fileTypeEnabled("movies", true)
        onToggled: root.setFileTypeEnabled("movies", checked)
    }
    CheckBox {
        objectName: "optionsFileTypeQuickTimeCheck"
        text: qsTr("QuickTime")
        checked: root.fileTypeEnabled("quicktime", true)
        onToggled: root.setFileTypeEnabled("quicktime", checked)
    }

    Item { Layout.fillHeight: true }
}

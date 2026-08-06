import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #350: "Printing" fül (options.fen) — a PicasaPy-ban ma nincs nyomtatási
// funkció (`print.fen`/`reviewprint.fen` nem épült meg, alacsony
// prioritású a docs/specs/picasa-fen-dialogs.md 8. szak. szerint),
// ezért a teljes fül tiltott.
ColumnLayout {
    id: root
    spacing: 10
    enabled: false

    Text {
        text: qsTr("Available print sizes:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    Repeater {
        model: 5
        RowLayout {
            spacing: 8
            Text {
                text: qsTr("Print size %1:").arg(index + 1)
                font.pixelSize: Theme.fontSize
                color: Theme.ink
            }
            ComboBox {
                objectName: "optionsPrintSizeCombo" + index
                model: ["4x6", "5x7", "8x10", "Letter", "A4"]
            }
        }
    }

    CheckBox {
        objectName: "optionsPrintHiResPreviewCheck"
        text: qsTr("Use high resolution previews (slower)")
    }

    Text {
        text: qsTr("Printer quality (Windows only):")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    ButtonGroup { id: qualityGroup }
    RadioButton { objectName: "optionsPrintQualityStandardRadio"; text: qsTr("Standard"); ButtonGroup.group: qualityGroup; checked: true }
    RadioButton { objectName: "optionsPrintQualityHighRadio"; text: qsTr("High"); ButtonGroup.group: qualityGroup }

    Text {
        text: qsTr("Resizing algorithm quality:")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }
    ButtonGroup { id: resizeGroup }
    RadioButton { objectName: "optionsPrintResizeGeneralRadio"; text: qsTr("General (Lanczos-3)"); ButtonGroup.group: resizeGroup; checked: true }
    RadioButton { objectName: "optionsPrintResizeSharpRadio"; text: qsTr("Very sharp (Lanczos-8)"); ButtonGroup.group: resizeGroup }

    Item { Layout.fillHeight: true }
}

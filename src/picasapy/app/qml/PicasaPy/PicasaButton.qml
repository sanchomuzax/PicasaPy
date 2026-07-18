import QtQuick
import QtQuick.Controls

// Picasa-stílusú gomb: lekerekített, finom gradiens, 1px szegély.
Button {
    id: control
    property color accent: "transparent"   // pl. Theme.picasaGreen

    font.pixelSize: Theme.fontSize
    padding: 6
    horizontalPadding: 10

    readonly property bool accented: control.accent !== Qt.color("transparent")

    background: Rectangle {
        radius: 3
        border.width: 1
        border.color: control.accented
                      ? Qt.darker(control.accent, 1.3) : "#b5b5b5"
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: control.accented
                       ? Qt.lighter(control.accent, 1.25)
                       : (control.down ? "#d8d8d8" : "#fdfdfd")
            }
            GradientStop {
                position: 1.0
                color: control.accented
                       ? control.accent
                       : (control.down ? "#c8c8c8" : "#e4e4e4")
            }
        }
        // az akcentusos (zöld) gomb letiltva is színes marad — Picasa-minta
        opacity: control.enabled || control.accented ? 1.0 : 0.55
    }

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.accented ? "white"
               : (control.enabled ? Theme.textDark : "#9a9a9a")
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}

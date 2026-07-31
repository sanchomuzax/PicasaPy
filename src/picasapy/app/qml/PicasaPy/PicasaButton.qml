import QtQuick
import QtQuick.Controls

// Picasa-stílusú gomb: lekerekített, finom gradiens, 1px szegély.
//
// #336: a színek TOKENBŐL jönnek, nem hardkódolva. A korábbi változat fix
// világos hátteret rajzolt (#fdfdfd → #e4e4e4), a feliratot viszont a
// témafüggő Theme.textDark-kal — sötét témában ez világos szöveget adott
// világos gombon, azaz a felhasználó ÜRES gombokat látott (Importálás,
// Vissza a könyvtárhoz, E-mail, Nyomtatás, Exportálás).
//
// A tényleges színek nevesített tulajdonságokban élnek, hogy a kontraszt
// tesztelhető legyen (tests/app/test_qml_button_contrast.py) és a logika
// egy helyen maradjon.
Button {
    id: control
    property color accent: "transparent"   // pl. Theme.picasaGreen

    font.pixelSize: Theme.fontSize
    padding: 6
    horizontalPadding: 10

    readonly property bool accented: control.accent !== Qt.color("transparent")

    // --- a gomb tényleges színei (a background/contentItem ezeket használja) ---
    readonly property color surfaceTop: control.accented
        ? Qt.lighter(control.accent, 1.25)
        : (control.down ? Qt.darker(Theme.buttonBg, 1.12)
                        : Qt.lighter(Theme.buttonBg, 1.08))
    readonly property color surfaceBottom: control.accented
        ? control.accent
        : (control.down ? Qt.darker(Theme.buttonBg, 1.22) : Theme.buttonBg)
    readonly property color inkColor: control.accented
        ? "white"
        : (control.enabled ? Theme.ink : Theme.textGray)

    background: Rectangle {
        radius: 3
        border.width: 1
        border.color: control.accented
                      ? Qt.darker(control.accent, 1.3) : Theme.chromeBorder
        gradient: Gradient {
            GradientStop { position: 0.0; color: control.surfaceTop }
            GradientStop { position: 1.0; color: control.surfaceBottom }
        }
        // az akcentusos (zöld) gomb letiltva is színes marad — Picasa-minta
        opacity: control.enabled || control.accented ? 1.0 : 0.55
    }

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.inkColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}

import QtQuick
import QtQuick.Controls

// Picasa-stílusú görgetősáv: keskeny, lapos, szürke fogantyú a Qt
// alap-króm (Fusion) helyett — kézikönyv 06. fejezet, „Görgetősáv
// #CDCDCD — Vezérlők, keretek" (ld. docs/specs/design-guide.md).
//
// Csak a vezérlő maga; a `ScrollBar.vertical: PicasaScrollBar {}` /
// `ScrollBar.horizontal: PicasaScrollBar {}` bekötés az integrátoré
// (Main.qml és a többi meglévő QML forró fájl — #3 issue).
ScrollBar {
    id: control

    // a sín (background) és a fogantyú (contentItem) közös vastagsága;
    // mindkét irányban ugyanaz az érték — a ScrollBar belső elrendezése
    // a görgetés-tengely mentén automatikusan nyújtja a hosszt.
    readonly property real barThickness: 10
    readonly property real handleMargin: 2

    // #323: a sáv NYUGALMI állapotban is látszik, ha van mit görgetni.
    // Korábban az `active`-hoz volt kötve a láthatóság (Qt-alapértelmezés:
    // csak görgetés/hover közben villan fel), ezért a felhasználó gyakorlatilag
    // soha nem látta a görgetősávot. A Picasa sávja állandóan ott van; ez a
    // kötés csak akkor rejti el, ha nincs mit görgetni (size >= 1) vagy a
    // hívó kifejezetten AlwaysOff-ot kért.
    readonly property bool barVisible:
        policy !== ScrollBar.AlwaysOff
        && (policy === ScrollBar.AlwaysOn || size < 1.0)

    policy: ScrollBar.AsNeeded
    minimumSize: 0.06
    padding: 0

    // fogantyú: semleges szürke, hover/press-en enyhén sötétedik
    contentItem: Rectangle {
        implicitWidth: control.barThickness - control.handleMargin * 2
        implicitHeight: implicitWidth
        radius: width / 2
        color: control.pressed
               ? Qt.darker(Theme.chromeBorder, 1.35)
               : (control.hovered
                  ? Qt.darker(Theme.chromeBorder, 1.15)
                  : Theme.chromeBorder)
        opacity: control.barVisible ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation { duration: 150 }
        }
        Behavior on color {
            ColorAnimation { duration: 100 }
        }
    }

    // sín: halványan mindig ott van a fogantyú mögött, interakció közben
    // valamivel erősebb (#323)
    background: Rectangle {
        implicitWidth: control.barThickness
        implicitHeight: control.barThickness
        color: Theme.chromeBg
        opacity: !control.barVisible ? 0.0 : (control.active ? 0.9 : 0.6)

        Behavior on opacity {
            NumberAnimation { duration: 150 }
        }
    }
}

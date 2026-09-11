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

    // #894: a fogantyú a MÉRT átmenetet kapja (`scrollart/base_win`, 15 × 25:
    // VÍZSZINTES átmenet, függőlegesen állandó — tehát egy függőleges sáv
    // hüvelykje):
    //
    //   x0 #B6B6B6 (sötét bal él) · x1 #C7C7C7 → x7 #D9D9D9 → x13 #EDEDED
    //   · x14 #C8C8C8 (jobb él)
    //
    // ⚠️ A Picasa SAJÁT görgetősávot rajzol, és a platformot a RAJZON át
    // követi (külön `_win` és `_mac` réteg, a Mac-változat kisebb). Mi egy
    // rajzot adunk: a windowsos mérést, mert a fejlesztés Linuxon fut, és a
    // `_mac` rétegre nincs platformunk. Ezt itt kimondjuk, hogy ne látsszon
    // kimaradásnak.
    //
    // Az átmenet TENGELYE a sáv irányához igazodik: függőleges sávnál
    // vízszintes (a mérés szerint), vízszintes sávnál elfordítva.
    contentItem: Rectangle {
        implicitWidth: control.barThickness - control.handleMargin * 2
        implicitHeight: implicitWidth
        radius: width / 2
        objectName: "picasaScrollThumb"
        //: a nyomott/hover állapot a mért átmenetet SÖTÉTÍTI, nem cseréli —
        //: az eredeti is ugyanazt a rajzot használja minden állapotban
        readonly property real tonus: control.pressed ? 1.25
                                      : (control.hovered ? 1.1 : 1.0)
        gradient: Gradient {
            orientation: control.horizontal
                         ? Gradient.Vertical : Gradient.Horizontal
            GradientStop {
                position: 0.0
                color: Qt.darker(Theme.scrollThumbEdgeDark, parent.tonus)
            }
            GradientStop {
                position: 0.07
                color: Qt.darker(Theme.scrollThumbEdgeSoft, parent.tonus)
            }
            GradientStop {
                position: 0.5
                color: Qt.darker(Theme.scrollThumbMid, parent.tonus)
            }
            GradientStop {
                position: 0.9
                color: Qt.darker(Theme.scrollThumbLight, parent.tonus)
            }
            GradientStop {
                position: 1.0
                color: Qt.darker(Theme.scrollThumbEdgeSoft, parent.tonus)
            }
        }
        opacity: control.barVisible ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation { duration: 150 }
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

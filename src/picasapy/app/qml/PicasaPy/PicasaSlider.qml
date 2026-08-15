import QtQuick
import QtQuick.Controls

// Picasa-stílusú csúszka: lapos sín + kerek, semleges szürke fogantyú
// — kézikönyv 06. fejezet, „Nagyítás csúszka − + / az indexképek
// méretét szabályozza; semleges szürke fogantyú." A fogantyú színátmenete
// szándékosan megegyezik a PicasaButton nem-akcentusos állapotával, hogy
// a „Vezérlők" család egységes maradjon (ld. docs/specs/design-guide.md).
//
// Csak a vezérlő maga; a bekötés (pl. a nagyítás-csúszka a Main.qml
// tálcájában) az integrátoré — #3 issue.
Slider {
    id: control

    readonly property bool isHorizontal: orientation === Qt.Horizontal

    // #700: a sín vastagsága és a fogantyú mérete a HÍVÓ helyen felülírható.
    // Az alapértékek változatlanok (kerek, 14 px-es fogantyú, 4 px-es sín),
    // ezért minden meglévő csúszka ugyanúgy néz ki, mint eddig; az
    // effekt-paraméter alpanel viszont az eredeti Picasa arányait kéri
    // (9 px-es sín, 16×26-os álló fogantyú — `docs/specs/ui-audit-editor.md`
    // 7.5). A `handleRadius` teszi kerekké vagy szögletessé a fogantyút.
    property real grooveThickness: 4
    property real handleWidth: 14
    property real handleHeight: 14
    property real handleRadius: Math.min(handleWidth, handleHeight) / 2

    // visszafelé kompatibilis alias a NÉGYZETES fogantyú méretére
    readonly property real handleSize: Math.max(handleWidth, handleHeight)

    // #659: a méret a FOGANTYÚVAL együtt értendő. Korábban csak a sín
    // vastagsága számított, ezért a vezérlő doboza 4 képpont magas volt, a
    // 14 képpontos, KÖZÉPRE igazított fogantyú pedig alul-felül 5-5
    // képponttal kilógott belőle — a gépi elrendezés-ellenőr (#656) pontosan
    // ennyit mért. A fogantyú látszólag eddig is ott volt; csak az
    // elrendezés nem foglalta le neki a helyet, ezért a szomszédjaira lógott.
    readonly property real vastagsag: Math.max(
        control.isHorizontal ? control.handleHeight : control.handleWidth,
        control.grooveThickness)

    implicitWidth: isHorizontal ? 120 : vastagsag + leftPadding + rightPadding
    implicitHeight: isHorizontal ? vastagsag + topPadding + bottomPadding : 120

    background: Rectangle {
        x: control.leftPadding + (control.isHorizontal
                                   ? 0 : (control.availableWidth - width) / 2)
        y: control.topPadding + (control.isHorizontal
                                  ? (control.availableHeight - height) / 2 : 0)
        width: control.isHorizontal ? control.availableWidth : control.grooveThickness
        height: control.isHorizontal ? control.grooveThickness : control.availableHeight
        radius: control.grooveThickness / 2
        color: Theme.chromeBg
        border.width: 1
        border.color: Theme.chromeBorder

        // bejárt szakasz — a fogantyúig, ugyanazzal a semleges szürkével
        // kicsit sötétítve, hogy tapintható legyen az érték
        Rectangle {
            radius: parent.radius
            color: Theme.chromeBorder
            anchors.left: control.isHorizontal ? parent.left : undefined
            anchors.bottom: control.isHorizontal ? undefined : parent.bottom
            width: control.isHorizontal
                   ? control.visualPosition * parent.width : parent.width
            height: control.isHorizontal
                    ? parent.height : control.visualPosition * parent.height
        }
    }

    handle: Rectangle {
        x: control.leftPadding + (control.isHorizontal
               ? control.visualPosition * (control.availableWidth - width)
               : (control.availableWidth - width) / 2)
        y: control.topPadding + (control.isHorizontal
               ? (control.availableHeight - height) / 2
               : (1 - control.visualPosition) * (control.availableHeight - height))
        implicitWidth: control.handleWidth
        implicitHeight: control.handleHeight
        radius: control.handleRadius
        border.width: 1
        border.color: control.pressed ? "#8f8f8f" : "#b5b5b5"
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: control.pressed ? "#d8d8d8" : "#fdfdfd"
            }
            GradientStop {
                position: 1.0
                color: control.pressed ? "#c8c8c8" : "#e4e4e4"
            }
        }
        opacity: control.enabled ? 1.0 : 0.55
    }
}

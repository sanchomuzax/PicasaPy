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
    readonly property real grooveThickness: 4
    readonly property real handleSize: 14

    implicitWidth: isHorizontal ? 120 : grooveThickness + leftPadding + rightPadding
    implicitHeight: isHorizontal ? grooveThickness + topPadding + bottomPadding : 120

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
        implicitWidth: control.handleSize
        implicitHeight: control.handleSize
        radius: width / 2
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

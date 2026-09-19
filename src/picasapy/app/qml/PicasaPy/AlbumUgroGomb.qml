import QtQuick
import QtQuick.Controls

// Album-ugró gomb a görgetősáv végén (#857, ADR-015).
//
// Az eredeti `prevalbum` / `nextalbum` gombja 16 × 24, három állapotképpel
// (`scrollart/up` · `pressup` · `hoverup`) és `m_autorepeat`-tel. Mi a sáv
// saját, lapos stílusában rajzoljuk (a rajzot nem hozzuk vissza, ld. a
// döntést), de a VISELKEDÉS a mért: nyomva tartva ismétel.
//
// A kettős nyíl (▲▲ / ▼▼) azt mondja meg, hogy nem egy sorral lép, hanem
// egy egész albumot ugrik — ugyanaz a jelbeszéd, mint az eredetin.
Item {
    id: gomb

    //: felfelé (előző album) vagy lefelé (következő album) mutat-e
    property bool felfele: true
    //: a buboréksúgó szövege — a hívó adja, mert ő tudja, mire ugrik
    property string magyarazat: ""
    //: minden kiváltáskor (kattintás ÉS ismétlés) elsül
    signal aktivalva()

    //: az ismétlés ütemei — az eredeti `m_autorepeat`-je is előbb vár, majd
    //: sűrűn ismétel; ezek a Qt szokásos gomb-értékei
    readonly property int elsoKesleltetes: 300
    readonly property int ismetlesKoz: 100

    implicitWidth: 10
    implicitHeight: 24

    Rectangle {
        anchors.fill: parent
        color: terulet.pressed
            ? Qt.darker(Theme.chromeBg, 1.25)
            : (terulet.containsMouse ? Qt.darker(Theme.chromeBg, 1.1)
                                     : Theme.chromeBg)
    }

    //: a kettős nyíl — két egymás fölötti háromszög, a sáv szélességéhez mérve
    Column {
        anchors.centerIn: parent
        spacing: 1
        Repeater {
            model: 2
            Canvas {
                width: Math.max(5, gomb.width - 4)
                height: 4
                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()
                    ctx.fillStyle = Theme.ink
                    ctx.beginPath()
                    if (gomb.felfele) {
                        ctx.moveTo(width / 2, 0)
                        ctx.lineTo(width, height)
                        ctx.lineTo(0, height)
                    } else {
                        ctx.moveTo(0, 0)
                        ctx.lineTo(width, 0)
                        ctx.lineTo(width / 2, height)
                    }
                    ctx.closePath()
                    ctx.fill()
                }
            }
        }
    }

    MouseArea {
        id: terulet
        objectName: "albumUgroTerulet"
        anchors.fill: parent
        hoverEnabled: true
        onPressed: {
            gomb.aktivalva()
            ismetlo.interval = gomb.elsoKesleltetes
            ismetlo.restart()
        }
        onReleased: ismetlo.stop()
        onCanceled: ismetlo.stop()
    }

    //: #857: `m_autorepeat` — nyomva tartva ismétel. A Qt `Button`
    //: `autoRepeat`-je itt nem használható: ez nem gomb-vezérlő, hanem a
    //: görgetősáv sínjébe ültetett, saját rajzú elem.
    Timer {
        id: ismetlo
        objectName: "albumUgroIsmetlo"
        repeat: true
        interval: gomb.elsoKesleltetes
        onTriggered: {
            interval = gomb.ismetlesKoz
            gomb.aktivalva()
        }
    }

    ToolTip.visible: terulet.containsMouse && gomb.magyarazat !== ""
    ToolTip.text: gomb.magyarazat
    ToolTip.delay: 600
}

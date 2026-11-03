import QtQuick
import QtQuick.Controls

// #2966/#6405: közös háttérművelet-jelző az eszközsáv jobb szélén, a
// keresőmezőtől jobbra, vele egy sorban (a helyét a MainToolbar adja). Mérce az
// eredeti képernyőkép (`research/testdata/screenshot/2026-07-17 20 54 38.png`):
// az 1920 széles ablakban a mező vége x≈1872, a jelző x≈1888-1908, y≈62. Nem a
// mappafejléc szinkronkapcsolója mellett áll; munka közben a verziófelirat
// helyét foglalja el.
//
// Az eredeti Picasa a `thumbui/mainuipanel` vásznán tartott egy kis widgetet:
// alapból REJTVE, és csak háttérművelet közben jelent meg, pörgő jelzővel és
// a megszakítást kérő gombbal. A #3112 a geometriáját a `respack.yt`-ból
// mérte (a könyvtárnézet 800 × 534-es tervezővásznán):
//
//   a jelző helye   x 760-795, y 5-33  ⇒ jobb felül, felülről 5, jobbról 5
//   a jelző mérete  35 × 28            (a maszk és a keret MINDIG látszik)
//   pörgő           26 × 26, középre, alapból rejtett
//   gomb            22 × 28, alapból rejtett
//
// A pörgő és a gomb ugyanabban a 35 × 28-as dobozban ÁLL EGYMÁSON - a
// szélességük összege nagyobb a dobozénál, tehát nem egymás mellett voltak.
// A tulajdonos döntése (2026-11-03, #6474) szerint a gomb a pörgő mellé kerül,
// mert a fedés rosszul néz ki: megszakítható munkánál a jelző szélesebb, a
// pörgő balra, a gomb jobbra áll (lásd a szélesség-konstansokat lent).
//
// ⚠️ Amit ez a komponens NEM állít: hogy a látvány megegyezik az
// eredetivel. A helye és a mérete mért, a rajzolat (maszk, keret, ikon)
// nem - arra referencia-képernyőkép kellene.
Item {
    id: root

    //: fut-e háttérmunka (a küszöbölt busy-állapot)
    property bool working: false
    //: leállítható-e a futó munka - CSAK ettől jelenik meg a gomb
    property bool cancellable: false

    signal cancelRequested()

    // #6474: megszakíthatatlan munkánál a mért 35 × 28; megszakítható munkánál
    // a pörgő és a gomb EGYMÁS MELLETT áll (pörgő x 4-30, gomb x 32-54), köztük
    // 2 px rés, így a gomb nem fedi a pörgőt.
    readonly property int porgoMeret: 26
    readonly property int gombSzelesseg: 22
    readonly property int szegely: 4
    readonly property int koz: 2
    readonly property int keskenyMeret: 35
    readonly property int szelesMeret: szegely + porgoMeret + koz + gombSzelesseg

    width: root.cancellable ? root.szelesMeret : root.keskenyMeret
    height: 28
    visible: root.working

    // a maszk és a keret az eredetiben MINDIG látszik (a jelzőn belül)
    Rectangle {
        id: keret
        objectName: "activityBadgeFrame"
        anchors.fill: parent
        radius: 3
        color: Theme.trayBg
        border.color: Theme.chromeBorder
        border.width: 1
    }

    BusyIndicator {
        id: porgo
        objectName: "activityBadgeSpinner"
        width: root.porgoMeret
        height: root.porgoMeret
        // középen, ha nincs gomb; megszakítható munkánál a bal szélen
        x: root.cancellable ? root.szegely : (root.width - width) / 2
        y: (root.height - height) / 2
        running: root.working
        visible: root.working
    }

    // a megszakítás gombja - az eredetiben a szerkesztő saját példánya
    // (`editpanelactivity`) GOMB NÉLKÜLI, ezért itt sem mindig látszik:
    // csak akkor, ha a futó munkának tényleg van leállítója.
    Item {
        id: gomb
        objectName: "activityBadgeCancel"
        width: root.gombSzelesseg
        height: 28
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        visible: root.working && root.cancellable

        Rectangle {
            anchors.centerIn: parent
            width: 14
            height: 14
            radius: 2
            color: egerEsemeny.containsMouse ? Theme.chromeBorder : "transparent"

            // × jel - a megszakítás jele, felirat nélkül (a doboz 22 × 28)
            Text {
                anchors.centerIn: parent
                text: "✕"
                color: Theme.ink
                font.pixelSize: 10
            }
        }

        MouseArea {
            id: egerEsemeny
            anchors.fill: parent
            hoverEnabled: true
            onClicked: root.cancelRequested()

            PressFeedbackOverlay { pressSource: parent }
        }

        ToolTip.visible: egerEsemeny.containsMouse
        ToolTip.delay: Theme.tooltipDelay
        //: a jobb-felső sarki jelző megszakítás-gombja
        ToolTip.text: qsTr("Stop the background operation")
    }
}

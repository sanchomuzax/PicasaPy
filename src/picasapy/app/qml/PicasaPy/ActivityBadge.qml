import QtQuick
import QtQuick.Controls

// #2966: KÖZÖS háttérművelet-jelző a főablak jobb-felső sarkában.
//
// Az eredeti Picasa ugyanitt tartott egy kis widgetet: alapból REJTVE, és
// csak háttérművelet közben jelent meg — pörgő jelzővel és egy gombbal,
// amivel a művelet megszakítható volt. A #3112 kimérte a geometriáját a
// `respack.yt`-ból (a könyvtárnézet 800 × 534-es tervezővásznán):
//
//   a jelző helye   x 760–795, y 5–33  ⇒ jobb felül, felülről 5, jobbról 5
//   a jelző mérete  35 × 28            (a maszk és a keret MINDIG látszik)
//   pörgő           26 × 26, középre, alapból rejtett
//   gomb            22 × 28, alapból rejtett
//
// A pörgő és a gomb ugyanabban a 35 × 28-as dobozban ÁLL EGYMÁSON — a
// szélességük összege nagyobb a dobozénál, tehát nem egymás mellett voltak.
//
// ⚠️ Amit ez a komponens NEM állít: hogy a látvány megegyezik az
// eredetivel. A helye és a mérete mért, a rajzolat (maszk, keret, ikon)
// nem — arra referencia-képernyőkép kellene.
Item {
    id: root

    //: fut-e háttérmunka (a küszöbölt busy-állapot)
    property bool working: false
    //: leállítható-e a futó munka — CSAK ettől jelenik meg a gomb
    property bool cancellable: false

    signal cancelRequested()

    width: 35
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
        width: 26
        height: 26
        anchors.centerIn: parent
        running: root.working
        visible: root.working
    }

    // a megszakítás gombja — az eredetiben a szerkesztő saját példánya
    // (`editpanelactivity`) GOMB NÉLKÜLI, ezért itt sem mindig látszik:
    // csak akkor, ha a futó munkának tényleg van leállítója.
    Item {
        id: gomb
        objectName: "activityBadgeCancel"
        width: 22
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

            // × jel — a megszakítás jele, felirat nélkül (a doboz 22 × 28)
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
        }

        ToolTip.visible: egerEsemeny.containsMouse
        ToolTip.delay: Theme.tooltipDelay
        //: a jobb-felső sarki jelző megszakítás-gombja
        ToolTip.text: qsTr("Stop the background operation")
    }
}

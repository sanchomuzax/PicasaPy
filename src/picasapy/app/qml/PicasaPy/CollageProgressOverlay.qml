import QtQuick
import QtQuick.Controls

// A kollázs-mentés folyamatjelzője (#949) — spec 9.1.
//
// 224 × 80-as doboz a vászon KÖZEPÉN (`m_centerXY`), alapból REJTETT:
// cím fent, pörgő középen, állapotsor lent. A három belső doboz a mért
// `respack` koordináta (#3392, `picasa-create-features.md` 1.10.4):
// cím (5,6) 213×14 · pörgő (100,24) 29×31 · állapotsor (5,60) 213×14.
//
// A négy szöveg, ahogy az eredeti adja őket:
//
//   „Kollázs létrehozása... inicializálás"  (collage::initializing)
//   „Kollázs létrehozása - %d%%"            (collage::refining_format)
//   „Kollázs létrehozása... leállítás"      (collage::cancelling)
//   „A kollázs kész (kattintson ide)"       (collage::done)
//
// A CÍM a vezérlőtől jön (`collageProgress` második paramétere: melyik
// szakaszban járunk), az ÁLLAPOTSORT viszont itt fogalmazzuk meg a
// százalékból — az a felület dolga, nem a háttérszálé.
//
// ## A Többszörös exponálás saját szövege
//
// A `multiexp` nem elrendez, hanem képeket vetít egymásra, és ezért saját
// folyamatszövege van: „Képek egymásra helyezése" +
// „%1 / %2 feldolgozva". A második számpár a százalékból és a klipek
// darabszámából áll elő — ugyanaz az információ, más alakban; a rajzoló
// nem ad képenkénti visszajelzést, és kitalálni nem fogunk egyet.
Item {
    id: overlay

    // A doboz mérete (spec 9.1) — a vászon mérete NEM befolyásolja.
    implicitWidth: 224
    implicitHeight: 80
    width: implicitWidth
    height: implicitHeight

    visible: false

    //: 0…100. A 100 a „kész" állapot: ilyenkor a doboz kattintható.
    property int percent: 0

    //: A szakasz szövege, a vezérlőtől (`collageProgress` 2. paramétere).
    property string phase: ""

    //: Többszörös exponálásnál más szöveg jár (spec 9.1).
    property bool multiExposure: false

    //: A klipek darabszáma — a „%1 / %2 feldolgozva" nevezője.
    property int total: 0

    //: A dobozra kattintottak: futás közben megszakítás-kérdés, a végén a
    //: kész fájl megkeresése („kattintson ide").
    signal clicked()

    readonly property bool finished: overlay.percent >= 100

    readonly property string statusText: {
        if (overlay.finished)
            return ""
        if (overlay.multiExposure && overlay.total > 0) {
            const kesz = Math.round(overlay.percent / 100 * overlay.total)
            return qsTr("%1 / %2 processed").arg(kesz).arg(overlay.total)
        }
        return qsTr("Creating collage - %1%").arg(overlay.percent)
    }

    Rectangle {
        anchors.fill: parent
        color: Theme.contentPanel
        border.width: 1
        border.color: Theme.chromeBorder
        radius: 3
        opacity: 0.97
    }

    Text {
        objectName: "collageProgressTitle"
        x: 5
        y: 6
        width: 213
        height: 14
        text: overlay.phase
        elide: Text.ElideRight
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: Theme.fontSize
        color: Theme.ink
    }

    BusyIndicator {
        objectName: "collageProgressSpinner"
        x: 100
        y: 24
        width: 29
        height: 31
        running: overlay.visible && !overlay.finished
        // készen a pörgő megáll, de a helye marad — különben a doboz
        // tartalma a legutolsó pillanatban ugrana egyet
        visible: true
    }

    Text {
        objectName: "collageProgressStatus"
        x: 5
        y: 60
        width: 213
        height: 14
        text: overlay.statusText
        elide: Text.ElideRight
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: Theme.fontSize
        color: Theme.textGray
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: overlay.clicked()
    }
}

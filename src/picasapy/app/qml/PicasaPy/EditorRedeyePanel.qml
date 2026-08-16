import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő „Vörösszem" panelje (#445).
//
// A jegy két tényt rögzít az eredeti eszközről, és mindkettő ITT látszik:
//  * AUTOMATIKUS: a panel megnyitásakor a felismerés azonnal lefut, az
//    „Auto" gombbal újrafuttatható, és sikerüzenet kíséri („Picasa has
//    found and corrected red eye(s)").
//  * KÉZI kiegészítés: „You can also draw a square around any red eye that
//    Picasa may have missed." — a téglalap-húzást a hívó (PhotoViewer)
//    végzi a képen, ez a fájl nem ismeri a kép geometriáját (a Retusálás/
//    Vágás panel mintája).
//
// A „Preview changes without square outlines" jelölőnégyzet csak a
// kijelölő-négyzetek RAJZÁT kapcsolja ki az előnézeten — a javításon nem
// változtat, ezért tisztán nézet-állapot (nem megy a kontrollerhez).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "redeyeColumn"
    visible: panel.redeyeActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    // #741: a MÉRT gombgeometria (`docs/specs/szerkeszto-panel-meretek.md`
    // 6.2/7.): `redeyeauto`/`redeyepreview`, `redeyeapply`/`redeyecancel`
    // párban, 98 × 28-as gombokkal (x 38 és 144); a `redeyediscard`
    // („Reset") EGYEDÜL, középen (x 91).
    //
    // #779: a 98 FELSŐ KORLÁT, nem fix méret — fixen a pár 98 + 6 + 98 = 202
    // képpontot követelt az oszloptól, és ezzel a panel minimumát szabta meg.
    // A `fillWidth` + `maximumWidth` a mért méretet adja, valahányszor van rá
    // hely, és csak akkor zsugorít, amikor nincs.
    component ActionButton: PanelButton {
        Layout.fillWidth: true
        Layout.preferredWidth: 98
        Layout.maximumWidth: 98
        Layout.preferredHeight: 28
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Image {
            Layout.preferredWidth: 40
            Layout.preferredHeight: 30
            source: "../../assets/tools/redeye.png"
        }
        Text {
            Layout.fillWidth: true
            text: qsTr("Redeye")
            font.pixelSize: Theme.fontSize + 3
            color: Theme.ink
        }
    }

    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: qsTr("You can also draw a square around any red eye that"
                   + " Picasa may have missed. Click, hold, and drag the"
                   + " mouse around each eye separately to select it. A"
                   + " selection box appears over the area.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // az automatika visszajelzése — a jegy szó szerinti sikerüzenete
    Text {
        objectName: "redeyeAutoResultLabel"
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        visible: panel.redeyeFoundCount >= 0
        text: panel.redeyeFoundCount > 0
              ? qsTr("Picasa has found and corrected red eye(s).")
              : qsTr("No red eye was found automatically.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    Text {
        objectName: "redeyeRegionCountLabel"
        Layout.fillWidth: true
        text: qsTr("Regions selected: %1").arg(panel.redeyeRegionCount)
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // #779: `Layout.fillWidth` NÉLKÜL a jelölőnégyzet a saját (a felirat
    // hosszából adódó) szélességét KÖTELEZŐ minimumként adta az oszlopnak, és
    // ezzel az EGÉSZ panelt szélesebbre feszítette a tartalom-oszlopnál —
    // annál jobban, minél szélesebb a betűkészlet. (A CI tartalék betűjével
    // 18–20, egy 1,5-szeresre nyújtott betűvel már 90 képponttal.) Kitöltővé
    // téve a felirat a rendelkezésre álló helyhez igazodik, a panel
    // minimumát pedig nem húzza föl — ugyanaz a megoldás, amit a szöveg-panel
    // `textFillDisabledCheck`-je használ.
    CheckBox {
        objectName: "redeyeHideOutlinesCheck"
        Layout.fillWidth: true
        text: qsTr("Preview changes without square outlines")
        font.pixelSize: Theme.fontSize - 1
        checked: panel.redeyeHideOutlines
        onToggled: panel.redeyeHideOutlines = checked
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: 98 + 6 + 98
        Layout.alignment: Qt.AlignHCenter
        spacing: 6
        ActionButton {
            objectName: "redeyeAutoButton"
            label: qsTr("Auto")
            onButtonClicked: panel.redeyeAutoRequested()
        }
        ActionButton {
            objectName: "redeyeUndoRegionButton"
            label: qsTr("Undo")
            buttonEnabled: panel.canUndoRedeyeRegion
            onButtonClicked: panel.redeyeUndoRegionRequested()
        }
    }

    // #741: a „Reset" az eredetin egyedül, középen áll (`redeyediscard`)
    ActionButton {
        objectName: "redeyeResetButton"
        label: qsTr("Reset")
        Layout.alignment: Qt.AlignHCenter
        buttonEnabled: panel.redeyeRegionCount > 0
        onButtonClicked: panel.redeyeResetRequested()
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: 98 + 6 + 98
        Layout.alignment: Qt.AlignHCenter
        spacing: 6
        ActionButton {
            objectName: "redeyeApplyButton"
            label: qsTr("Apply") + " ✔"
            onButtonClicked: panel.redeyeApplyRequested()
        }
        ActionButton {
            objectName: "redeyeCancelButton"
            label: qsTr("Cancel") + " ✘"
            onButtonClicked: panel.redeyeCancelRequested()
        }
    }
}

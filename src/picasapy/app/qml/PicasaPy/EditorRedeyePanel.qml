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
//: A „Preview” a jelenlegi körvonal-jelölő nézetállapotát kapcsolja.
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "redeyeColumn"
    visible: panel.redeyeActive
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 6

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
            objectName: "redeyeTitleIcon"
            Layout.preferredWidth: 40
            Layout.preferredHeight: 30
            source: "../../assets/tools/redeye.png"
        }
        Text {
            Layout.fillWidth: true
            objectName: "redeyeTitleText"
            text: qsTr("Redeye Repair")
            font.pixelSize: Theme.fontSize + 3
            color: Theme.ink
        }
    }

    //: #901: a vörösszem-eszköz BEÉPÍTETT útmutatója — az eredetiben
    //: `editpanel/text(redeye tip): redeyetext`.
    //: A szöveg az eredeti szó szerinti angolja (az utolsó két mondat eddig
    //: LEMARADT), a magyar a Picasa saját erőforrásából
    //: (`panel-feliratok-hu.tsv:4989`).
    Item {
        objectName: "redeyeInstructionBlock"
        visible: !panel.redeyeAutoReset
        Layout.fillWidth: true
        Layout.topMargin: 2
        Layout.preferredWidth: 242
        Layout.preferredHeight: 129
        Text {
            id: redeyeGuide
            objectName: "redeyeGuideText"
            visible: !panel.redeyeAutoReset
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            wrapMode: Text.WordWrap
            text: qsTr("Click, hold, and drag the mouse around each eye separately "
                       + "to select it. A selection box appears over the area. "
                       + "Release the mouse to complete your selection. The Photo is "
                       + "displayed with the red-eye removed.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }

        // A keretenkénti visszavonás mondata a hivatalos
        // `RedEye::DragToSelectMessage` erőforrásból.
        Text {
            objectName: "redeyeFrameHintLabel"
            visible: !panel.redeyeAutoReset && !(panel.redeyeFoundCount > 0)
            anchors.top: redeyeGuide.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            wrapMode: Text.WordWrap
            //: picasapy-origin: picasa
            //: picasapy-origin-key: stringres:RedEye::DragToSelectMessage
            text: qsTr("Note: You can click on a box to delete a change.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
    }

    // az automatika visszajelzése — a jegy szó szerinti sikerüzenete
    Text {
        objectName: "redeyeAutoResultLabel"
        Layout.fillWidth: true
        Layout.topMargin: 2
        wrapMode: Text.WordWrap
        visible: !panel.redeyeAutoReset && panel.redeyeFoundCount > 0
        //: #3574: a hivatalos szöveg (`RedEye::AutoFixedMessage`)
        text: qsTr("PicasaPy has found and corrected red eye(s).\n\nNote: You can click on a box to delete a change.\n\nYou can also draw a square around any red eye that PicasaPy may have missed.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    Text {
        objectName: "redeyeAutoRedoLabel"
        Layout.fillWidth: true
        Layout.topMargin: 2
        wrapMode: Text.WordWrap
        visible: panel.redeyeAutoReset
        text: qsTr("Click, hold, and drag the mouse around each eye separately "
                   + "to select it. A selection box appears over the area. "
                   + "Release the mouse to complete your selection. The Photo is "
                   + "displayed with the red-eye removed.\n\n"
                   + "Note: You can click on a box to delete a change.\n\n"
                   + "You can also click 'auto' to reapply the auto-corrections.")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    // A méretspecifikáció 36 px-t hagy az útmutató-blokk után, majd 6 px-t
    // a három gombsor között (`szerkeszto-panel-meretek.md`, 6.2). A külső
    // 6 px-es osztásköz mellé 30 px-es felső margó adja a 36 px-es rést.
    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: 98 + 6 + 98
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: 30
        spacing: 6
        ActionButton {
            objectName: "redeyeAutoButton"
            label: qsTr("Auto")
            buttonEnabled: panel.canReapplyRedeyeAuto
            onButtonClicked: panel.redeyeAutoRequested()
        }
        ActionButton {
            objectName: "redeyePreviewButton"
            label: qsTr("Preview")
            buttonEnabled: panel.redeyeRegionCount > 0
            active: panel.redeyeHideOutlines
            onButtonClicked: panel.redeyeHideOutlines = !panel.redeyeHideOutlines
        }
    }

    // #741: a „Reset" az eredetin egyedül, középen áll (`redeyediscard`).
    ActionButton {
        objectName: "redeyeResetButton"
        label: qsTr("Reset")
        Layout.alignment: Qt.AlignHCenter
        buttonEnabled: panel.redeyeResetAvailable
        onButtonClicked: panel.redeyeResetRequested()
    }

    // #3320: az Alkalmaz/Mégse pár IDE tartozik — az `editpanel.tre`
    // szerint a `redeyeapply`/`redeyecancel` szülője a saját
    // `redeye_well`, nem a kép fölötti `tool_container` (az a
    // `#---Straighen Overlay---` szakaszé). A #3123 egy félreolvasott
    // mérés alapján vitte a képre; a #3234 mérése ezt helyesbítette.
    //
    // #710: a jel a KÖZÖS, RAJZOLT `EditorActionBadge` — a Unicode-glif
    // betűtípusfüggő, és hiányzó glifnél NYOMTALANUL eltűnik.
    RowLayout {
        Layout.fillWidth: true
        Layout.maximumWidth: 98 + 6 + 98
        Layout.alignment: Qt.AlignHCenter
        spacing: 6
        ActionButton {
            objectName: "redeyeApplyButton"
            label: qsTr("Apply")
            buttonEnabled: panel.redeyeRegionCount > 0
            onButtonClicked: panel.redeyeApplyRequested()
            EditorActionBadge {
                objectName: "redeyeApplyIcon"
                tick: true
                anchors.right: parent.right
                anchors.rightMargin: 9
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        ActionButton {
            objectName: "redeyeCancelButton"
            label: qsTr("Cancel")
            onButtonClicked: panel.redeyeCancelRequested()
            EditorActionBadge {
                objectName: "redeyeCancelIcon"
                tick: false
                anchors.right: parent.right
                anchors.rightMargin: 9
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}

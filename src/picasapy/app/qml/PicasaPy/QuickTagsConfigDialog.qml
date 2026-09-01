import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Gyorscímkék konfigurálása (#193, #1788) — a Címkék-panel
// fogaskerék-dialógusa: TÍZ szerkeszthető szövegmező (a 2×5 gombrács
// szlotjai) + két kapcsoló.
//
// ## Miért tíz, és miért OK/Mégse (#1788)
//
// A tízes szám két független mérésből jön: a `quicktagconfig` panel
// elemleltára `edit_0` … `edit_9` mezőket sorol, a kezelő ciklushatára
// pedig `cmp eax, 0xa` (0x0083efa2).
//
// A gombokról a jegy a megvalósítóra bízta a döntést, azzal, hogy ki KELL
// mondani. A döntés: ÁTVESSZÜK az eredeti OK/Mégse mintát — a panelen
// `quicktagconfig/ok` és `quicktagconfig/cancel` vezérlő is van
// (0x0083ea00). A „Bezárás"-nál maradni azért lett elvetve, mert a mezők
// AZONNAL írnak (`onEditingFinished`), tehát egy elgépelt címke
// visszavonhatatlan lenne — a felhasználónak kézzel kellene visszaírnia.
//
// A Mégse úgy vonja vissza, hogy megnyitáskor pillanatfelvételt veszünk a
// vezérlő állapotáról, és elutasításkor visszaírjuk. (Hogy az eredeti
// Mégse PONTOSAN mit állít vissza, nincs kimérve — a jegy is így mondja;
// a „megnyitáskori állapot" a józan olvasat.)
// A `controller`-t közvetlenül hívja (KeywordsMixin) — a Main.qml forró
// fájl, ezért a TagsPanel-lel ellentétben itt nem lehetséges a szokásos
// jel-alapú bekötés; ld. a TagsPanel.qml megjegyzését.
Dialog {
    id: dialog
    title: qsTr("Configure quick tags")
    modal: true
    width: 360
    parent: Overlay.overlay
    anchors.centerIn: parent
    standardButtons: Dialog.Ok | Dialog.Cancel

    // minden megnyitáskor a friss controller-állapotot tükrözi — a
    // szövegmezők onEditingFinished-je írja vissza a controllerbe, nem
    // élő binding (hogy gépelés közben ne írjon minden karakterre)
    function mezok() {
        return [field0, field1, field2, field3, field4,
                field5, field6, field7, field8, field9]
    }

    //: #1788: a megnyitáskori állapot — ebbe tér vissza a Mégse.
    property var kiindulasiCimkek: []
    property bool kiindulasiReserve: false
    property bool kiindulasiAutoFill: false

    function refresh() {
        var fields = dialog.mezok()
        var labels = controller.quickTagConfigLabels
        for (var i = 0; i < fields.length; i++)
            fields[i].text = labels[i] !== undefined ? labels[i] : ""
        reserveCheck.checked = controller.quickTagsReserveRecent
        autoFillCheck.checked = controller.quickTagsAutoFillFrequent
    }

    onOpened: {
        dialog.refresh()
        //: A pillanatfelvétel MÁSOLAT: a `quickTagConfigLabels` minden
        //: olvasáskor új listát ad, de a `slice()` kimondja a szándékot.
        dialog.kiindulasiCimkek = controller.quickTagConfigLabels.slice()
        dialog.kiindulasiReserve = controller.quickTagsReserveRecent
        dialog.kiindulasiAutoFill = controller.quickTagsAutoFillFrequent
    }

    //: #1788: a Mégse VISSZAÁLLÍT. A mezők gépelés közben már írtak a
    //: vezérlőbe, ezért itt nem „elvetni" kell, hanem visszaírni.
    onRejected: {
        for (var i = 0; i < dialog.kiindulasiCimkek.length; i++)
            controller.setQuickTagLabel(i, dialog.kiindulasiCimkek[i])
        controller.setQuickTagsReserveRecent(dialog.kiindulasiReserve)
        controller.setQuickTagsAutoFillFrequent(dialog.kiindulasiAutoFill)
    }

    // a tíz szövegmező közös viselkedése — EXPLICIT tíz példány (nem Repeater):
    // egy Layout-ba ágyazott Repeater a Qt Quick Layouts sajátossága miatt
    // úgy jelenteti meg a delegáltakat, hogy a QObject-szülőjük a Repeater
    // marad (nem a layout) — findChild(objectName) ezért a tesztekben nem
    // találná meg őket (ld. TagsPanel.qml azonos megjegyzése).
    component QuickTagField: TextField {
        id: field
        required property int slot
        objectName: "quickTagField" + field.slot
        Layout.fillWidth: true
        font.pixelSize: Theme.fontSize
        enabled: !(reserveCheck.checked && field.slot < 2)
        placeholderText: field.enabled ? qsTr("Tag") : qsTr("(automatic)")
        onEditingFinished: controller.setQuickTagLabel(field.slot, field.text)
        // #422: jobbklikk-menü (Picasa `Address`)
        TextFieldContextArea {}
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            Layout.fillWidth: true
            text: qsTr(
                "Edit the 10 quick tag buttons shown at the bottom of the "
                + "Tags panel.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 5
            rowSpacing: 6
            columnSpacing: 6

            QuickTagField { id: field0; slot: 0 }
            QuickTagField { id: field1; slot: 1 }
            QuickTagField { id: field2; slot: 2 }
            QuickTagField { id: field3; slot: 3 }
            QuickTagField { id: field4; slot: 4 }
            QuickTagField { id: field5; slot: 5 }
            QuickTagField { id: field6; slot: 6 }
            QuickTagField { id: field7; slot: 7 }
            QuickTagField { id: field8; slot: 8 }
            QuickTagField { id: field9; slot: 9 }
        }

        CheckBox {
            id: reserveCheck
            objectName: "quickTagsReserveRecentCheck"
            Layout.fillWidth: true
            text: qsTr("Reserve the top two buttons for recently used tags")
            onToggled: controller.setQuickTagsReserveRecent(checked)
        }

        CheckBox {
            id: autoFillCheck
            objectName: "quickTagsAutoFillCheck"
            Layout.fillWidth: true
            text: qsTr("Fill the empty boxes above with frequently used tags")
            onToggled: controller.setQuickTagsAutoFillFrequent(checked)
        }
    }
}

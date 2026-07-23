import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Gyorscímkék konfigurálása (#193) — a Címkék-panel fogaskerék-dialógusa:
// 8 szerkeszthető szövegmező (a 2×4 gombrács szlotjai) + két kapcsoló.
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
    standardButtons: Dialog.Close

    // minden megnyitáskor a friss controller-állapotot tükrözi — a
    // szövegmezők onEditingFinished-je írja vissza a controllerbe, nem
    // élő binding (hogy gépelés közben ne írjon minden karakterre)
    function refresh() {
        var fields = [field0, field1, field2, field3,
                      field4, field5, field6, field7]
        var labels = controller.quickTagConfigLabels
        for (var i = 0; i < fields.length; i++)
            fields[i].text = labels[i]
        reserveCheck.checked = controller.quickTagsReserveRecent
        autoFillCheck.checked = controller.quickTagsAutoFillFrequent
    }

    onOpened: dialog.refresh()

    // a 8 szövegmező közös viselkedése — EXPLICIT 8 példány (nem Repeater):
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
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            Layout.fillWidth: true
            text: qsTr(
                "Edit the 8 quick tag buttons shown at the bottom of the "
                + "Tags panel.")
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 4
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

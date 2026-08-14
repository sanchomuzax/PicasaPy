import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// #644: figyelmeztetés, ha egy MÁSIK program (a párhuzamosan futó eredeti
// Picasa) felülírta a nálunk mentett szerkesztéseket.
//
// A Picasa a fotó rekordját a saját adatbázisából írja ki egészben a
// `.picasa.ini`-be; amit a rekordja nem tartalmaz — a mi `filters=`
// láncunkat —, azt elhagyja. A néma eltűnés a legrosszabb változat: a
// felhasználó munkája nyomtalanul vész el. Ez a párbeszéd megmondja, MELYIK
// kép szerkesztése veszett, és fel is ajánlja a visszaállítást a szerkesztés-
// naplóból.
Dialog {
    id: root
    objectName: "editOverwriteDialog"
    modal: true
    anchors.centerIn: parent
    width: Math.min(parent ? parent.width - 80 : 420, 520)
    title: qsTr("Edits overwritten by another program")

    // `[{path, name, chain}]` — a controller.editsOverwritten jelzéséből
    property var items: []

    function show(lost) {
        if (!lost || lost.length === 0) return
        root.items = lost
        root.open()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            objectName: "editOverwriteMessage"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            text: qsTr("Another program changed these pictures and removed the edits you made here:")
        }

        // a nevek felsorolása — hosszú listánál görgethető
        ScrollView {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(root.items.length * 20 + 8, 140)
            clip: true
            Column {
                spacing: 2
                Repeater {
                    model: root.items
                    delegate: Text {
                        required property var modelData
                        text: "• " + modelData.name
                        font.pixelSize: Theme.fontSize
                        color: Theme.ink
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
            // a korlát kimondása: amíg a kétirányú átjárás nincs meg (#643),
            // a Picasa írása nyer — jobb előre tudni, mint utólag
            text: qsTr("While the same folder is open in Picasa, its changes overwrite the edits made here. Restoring writes your edits back.")
        }
    }

    footer: DialogButtonBox {
        Button {
            objectName: "editOverwriteRestoreButton"
            text: qsTr("Restore edits")
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
        }
        Button {
            objectName: "editOverwriteCloseButton"
            text: qsTr("Close")
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
    }

    onAccepted: {
        if (typeof controller === "undefined" || !controller) return
        for (var i = 0; i < root.items.length; ++i)
            controller.restoreOverwrittenEdit(root.items[i].path)
        root.items = []
    }
    onRejected: root.items = []
}

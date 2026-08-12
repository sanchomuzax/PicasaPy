import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Általános, egysoros névbekérő (#422) — a `ConfirmDialog.qml` mintáját
// követő, önálló, signal-alapú komponens.
//
// Az eredeti Picasa is EGY generikus szövegbekérőt (`input.fen`) használ
// minden ilyen kérdéshez; a `NewCollectionDialog` ennek a gyűjtemény-
// specifikus (név-ellenőrző) változata, ez pedig a semleges alak — például
// az „Áthelyezés új személyhez…" parancshoz.
//
// Az OK csak nem üres (nem csak szóközökből álló) névnél él, és a mező
// `Enter`-re is elfogad — a névbekérésnél ez a szokásos elvárás.
Dialog {
    id: root
    objectName: "nameInputDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel

    //: a mező fölötti kérdés
    property string prompt: ""
    //: a mező kezdő tartalma (átnevezésnél a jelenlegi név)
    property string initialName: ""
    //: az elfogadott név — a hívó az `accepted` jelben ezt olvassa
    readonly property string enteredName: nameField.text.trim()

    function openWith(text) {
        root.initialName = text
        nameField.text = text
        root.open()
        nameField.forceActiveFocus()
        nameField.selectAll()
    }
    function openEmpty() { root.openWith("") }

    onOpened: {
        nameField.forceActiveFocus()
        nameField.selectAll()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Text {
            objectName: "nameInputPrompt"
            Layout.fillWidth: true
            visible: root.prompt.length > 0
            text: root.prompt
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            id: nameField
            objectName: "nameInputField"
            Layout.fillWidth: true
            Layout.minimumWidth: 240
            font.pixelSize: Theme.fontSize
            onAccepted: if (root.enteredName.length > 0) root.accept()
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
        }
    }

    // az üres név nem fogadható el — a gomb LÁTHATÓAN tiltott, nem néma no-op
    Component.onCompleted: _syncOk()
    onEnteredNameChanged: _syncOk()
    function _syncOk() {
        var button = root.standardButton(Dialog.Ok)
        if (button) button.enabled = root.enteredName.length > 0
    }
}

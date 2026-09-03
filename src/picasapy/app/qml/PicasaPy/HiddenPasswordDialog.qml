import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A »Rejtett mappák« jelszava (#1637) — KÉT módban: feloldás és beállítás.
//
// ⚠️ A figyelmeztető sor NEM díszítés. A jelszó a PicasaPy felületén belüli
// MEGJELENÍTÉST zárja; a rejtett mappák a lemezen változatlanul ott vannak,
// bármelyik fájlkezelővel elérhetők. Ha ezt nem mondjuk ki, a felhasználó
// valódi adatvédelmet feltételez, ami nincs — ez a jegy (#1637) kifejezett
// követelménye.
//
// A tárolás módját a felhasználó választja:
//   • Picasa-kompatibilis (alapértelmezés) — a windowsos Picasában beállított
//     jelszó itt is nyit, és fordítva. Cserébe a régi, sózatlan lenyomat.
//   • Erős — sózott, lassú származtatás; a windowsos Picasa NEM nyitja meg.
//
// #1748: a `Dialog`-nak rögzített `implicitWidth`-e van, a tördelő `Text`-nek
// pedig rögzített `width`-e — enélkül Fusion stílussal kötési hurok lesz, és
// a párbeszéd szélessége kiszámíthatatlan.
Dialog {
    id: root
    objectName: "hiddenPasswordDialog"
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel
    implicitWidth: 380 + leftPadding + rightPadding

    //: "unlock" = feloldás egy meglévő jelszóval, "set" = új jelszó megadása
    property string mode: "unlock"
    //: a beírt jelszó — a hívó az `accepted` jelben ezt olvassa
    readonly property string enteredPassword: pwField.text
    //: beállításnál: erős (modern) tárolást kért-e a felhasználó
    readonly property bool modernRequested: modernBox.checked
    //: #1637: mindkét mező TAKARVA mutatja a jelszót. Azért külön
    //: tulajdonság, mert az `echoMode` enumot a teszt oldaláról nem lehet
    //: kiolvasni — enélkül a „nem látszik a jelszó" állítás mérhetetlen.
    readonly property bool jelszoRejtve:
        pwField.echoMode !== TextInput.Normal
        && verifyField.echoMode !== TextInput.Normal

    title: mode === "set"
           ? qsTr("Password for hidden folders")
           : qsTr("Hidden folders are locked")

    function openUnlock() { root._open("unlock") }
    function openSet() { root._open("set") }

    function _open(which) {
        root.mode = which
        pwField.text = ""
        verifyField.text = ""
        modernBox.checked = false
        root.open()
        pwField.forceActiveFocus()
    }

    onOpened: pwField.forceActiveFocus()

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        Text {
            objectName: "hiddenPasswordPrompt"
            width: 380
            Layout.preferredWidth: 380
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.ink
            text: root.mode === "set"
                  ? qsTr("Enter a password to use for the hidden folders.")
                  : qsTr("Enter the password to show the hidden folders.")
        }

        TextField {
            id: pwField
            objectName: "hiddenPasswordField"
            Layout.fillWidth: true
            Layout.minimumWidth: 240
            echoMode: TextInput.Password
            font.pixelSize: Theme.fontSize
            onAccepted: if (root._okEngedelyezett()) root.accept()
        }

        TextField {
            id: verifyField
            objectName: "hiddenPasswordVerify"
            visible: root.mode === "set"
            Layout.fillWidth: true
            Layout.minimumWidth: 240
            echoMode: TextInput.Password
            font.pixelSize: Theme.fontSize
            placeholderText: qsTr("Type the password again")
            onAccepted: if (root._okEngedelyezett()) root.accept()
        }

        Text {
            objectName: "hiddenPasswordMismatch"
            visible: root.mode === "set" && pwField.text.length > 0
                     && verifyField.text.length > 0
                     && pwField.text !== verifyField.text
            width: 380
            Layout.preferredWidth: 380
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.brandRed
            text: qsTr("The passwords do not match.")
        }

        CheckBox {
            id: modernBox
            objectName: "hiddenPasswordModern"
            visible: root.mode === "set"
            font.pixelSize: Theme.fontSize
            text: qsTr("Stronger protection (Picasa cannot open it)")
        }

        // ⚠️ Ez a mondat a jegy követelménye — ne töröld optikai okból.
        Text {
            objectName: "hiddenPasswordScopeWarning"
            width: 380
            Layout.preferredWidth: 380
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.brandSlate
            text: qsTr("This only hides the folders inside PicasaPy. The files "
                       + "stay on the disk and can be opened with any file manager.")
        }
    }

    Component.onCompleted: _syncOk()
    onEnteredPasswordChanged: _syncOk()
    onModeChanged: _syncOk()
    Connections {
        target: verifyField
        function onTextChanged() { root._syncOk() }
    }

    function _okEngedelyezett() {
        if (pwField.text.length === 0) return false
        if (root.mode === "set" && pwField.text !== verifyField.text) return false
        return true
    }

    // az OK LÁTHATÓAN tiltott, nem néma no-op (a projekt visszatérő kára)
    function _syncOk() {
        var button = root.standardButton(Dialog.Ok)
        if (button) button.enabled = root._okEngedelyezett()
    }
}

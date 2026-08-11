import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// "Új gyűjtemény…" — egysoros névbekérő dialógus (#320), a felhasználói
// egyéni mappa-gyűjtemények létrehozásához. Önálló, signal-alapú komponens
// (ConfirmDialog.qml mintája) — controller-hívást a hívó (FolderPane.qml)
// végez az `accepted` jelre.
Dialog {
    id: root
    objectName: "newCollectionDialog"
    title: qsTr("New Collection")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel

    // #422: a gyűjtemény ÁTNEVEZÉSE ugyanezt a névbekérőt használja (az
    // eredetiben is egy generikus szövegbekérő szolgál mindkettőt, ld.
    // `input.fen`) — a mező ilyenkor a jelenlegi névvel indul. A hívó
    // dolga eldönteni, létrehozás vagy átnevezés következik.
    property string initialName: ""

    // a beírt gyűjtemény-név — üresen (csak szóköz is) nem fogadható el
    signal created(string name)

    // #461: az eredeti Picasa KÉT hibát különböztet meg — „»%s« is not a
    // valid collection name" és „You already have a collection named »%s«."
    // —, ezért a névbekérő is kettőt mutat, a csendes elutasítás helyett.
    // A választ a controller adja (`validateCollectionName`).
    property string errorText: ""

    function _errorFor(name) {
        if (typeof controller === "undefined" || !controller) return ""
        var code = controller.validateCollectionName(name, root.initialName)
        if (code === "invalid")
            return qsTr("\u201c%1\u201d is not a valid collection name")
                   .replace("%1", name)
        if (code === "duplicate")
            return qsTr("You already have a collection named \u201c%1\u201d.")
                   .replace("%1", name)
        return ""
    }

    onOpened: {
        root.errorText = ""
        nameField.text = root.initialName
        nameField.forceActiveFocus()
        standardButton(Dialog.Ok).enabled = Qt.binding(
            function() { return nameField.text.trim().length > 0 })
    }
    onAccepted: {
        // Az Ok gomb tiltása a szokásos út, de az Enter (TextField.accepted)
        // is közvetlenül accept()-et hív — a védelem itt is fusson, ne csak
        // a gomb enabled-jén.
        var trimmed = nameField.text.trim()
        if (trimmed.length === 0) return
        root.errorText = root._errorFor(trimmed)
        if (root.errorText !== "") {
            // hibás név: a dialógus NYITVA marad, a hiba a mező alatt
            root.open()
            return
        }
        root.created(trimmed)
    }

    ColumnLayout {
        spacing: 8
        Text {
            text: qsTr("Collection name:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            id: nameField
            objectName: "newCollectionNameField"
            Layout.preferredWidth: 260
            onAccepted: if (text.trim().length > 0) root.accept()
            onTextChanged: root.errorText = ""
        }
        Text {
            objectName: "newCollectionErrorText"
            visible: root.errorText !== ""
            Layout.preferredWidth: 260
            wrapMode: Text.WordWrap
            text: root.errorText
            font.pixelSize: Theme.fontSize - 1
            // a Theme-ben nincs hiba-token (hot file) — helyi, mindkét
            // témán olvasható vörös
            color: "#c0392b"
        }
    }
}

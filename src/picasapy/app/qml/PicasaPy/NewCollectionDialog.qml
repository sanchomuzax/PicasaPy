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

    // a beírt gyűjtemény-név — üresen (csak szóköz is) nem fogadható el
    signal created(string name)

    onOpened: {
        nameField.text = ""
        nameField.forceActiveFocus()
        standardButton(Dialog.Ok).enabled = Qt.binding(
            function() { return nameField.text.trim().length > 0 })
    }
    onAccepted: {
        // Az Ok gomb tiltása a szokásos út, de az Enter (TextField.accepted)
        // is közvetlenül accept()-et hív — a védelem itt is fusson, ne csak
        // a gomb enabled-jén.
        var trimmed = nameField.text.trim()
        if (trimmed.length > 0) root.created(trimmed)
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
        }
    }
}

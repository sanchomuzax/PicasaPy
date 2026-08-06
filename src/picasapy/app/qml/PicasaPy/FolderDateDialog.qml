import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// "Mappa dátumának beállítása…" (#320): a mappa dátumának kézi felülírása
// az évszám-szakaszoláshoz — a Picasa is engedi, alapból a mappa
// legrégebbi képe adja a dátumot. Önálló, signal-alapú komponens
// (ConfirmDialog.qml mintája) — a `.picasa.ini`-írást és az újraszinkront
// a hívó (FolderPane.qml) végzi a jelekre.
Dialog {
    id: root
    objectName: "folderDateDialog"
    title: qsTr("Set Folder Date")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel

    // a szerkesztett mappa útvonala — a hívó állítja be open() előtt
    property string folderPath: ""
    // a jelenlegi (esetleg üres) felülírás ISO-alakban, a mező
    // kezdőértékéhez
    property string currentDate: ""

    readonly property var _isoPattern: /^\d{4}-\d{2}-\d{2}$/

    // ÉRVÉNYES ISO 8601 dátummal (Ok gomb) — a mappa dátuma erre áll
    signal dateAccepted(string folderPath, string isoDate)
    // a felülírás törlése — a mappa a legrégebbi kép dátumára áll vissza
    signal dateCleared(string folderPath)

    onOpened: {
        dateField.text = root.currentDate
        dateField.forceActiveFocus()
        standardButton(Dialog.Ok).enabled = Qt.binding(
            function() { return root._isoPattern.test(dateField.text.trim()) })
    }
    onAccepted: {
        // A gomb tiltása a szokásos út, de az Enter (TextField.accepted)
        // is közvetlenül accept()-et hív — a formátum-védelem itt is fusson.
        var trimmed = dateField.text.trim()
        if (root._isoPattern.test(trimmed)) root.dateAccepted(root.folderPath, trimmed)
    }

    ColumnLayout {
        spacing: 8
        Text {
            text: qsTr("Folder date (YYYY-MM-DD):")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            id: dateField
            objectName: "folderDateField"
            Layout.preferredWidth: 160
            placeholderText: "2020-01-15"
            onAccepted: if (root._isoPattern.test(text.trim())) root.accept()
        }
        Text {
            objectName: "folderDateHint"
            visible: dateField.text.length > 0
                     && !root._isoPattern.test(dateField.text.trim())
            text: qsTr("Enter the date as YYYY-MM-DD.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.brandRed
        }
        PicasaButton {
            objectName: "folderDateClearButton"
            text: qsTr("Clear override (use oldest picture)")
            visible: root.currentDate.length > 0
            onClicked: {
                root.dateCleared(root.folderPath)
                root.close()
            }
        }
    }
}

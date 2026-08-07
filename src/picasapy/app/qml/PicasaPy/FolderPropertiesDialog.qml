import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// „Mappaleírás szerkesztése…" — a Picasa `album.fen` dialógusa (#422).
//
// Az eredeti mezősora (docs/specs/picasa-fen-dialogs.md 3.2.):
//   Name:                    edit (filter="filename")
//   Date:                    date + „Automatic date" gomb (egy sorban)
//   Music:                   check + browse (a browse a check-hez kötve)
//   Place taken (optional):  edit
//   Description (optional):  edit, height="3li" (többsoros)
//   [OK] [Mégse]
//
// FONTOS a #422 szempontjából: a mappa DÁTUMA az eredetiben ITT lakik, nem
// a mappa kontextusmenüjében. A korábbi önálló „Mappa dátumának
// beállítása…" menütétel ezért megszűnt, a funkció ide költözött — így a
// menü az eredeti 15 tételes listájával egyezik.
//
// A név, a zene és a helyszín mezője EGYELŐRE nincs bekötve (nincs mögötte
// réteg): a mezők a helyükön vannak, de inaktívak — ugyanaz az elv, mint a
// menük szürke tételeinél (az elrendezés a dizájn része, ld. #416 és a
// design-guide „inaktív menüpont szándékos" pontja).
//
// Önálló, signal-alapú komponens (FolderDateDialog.qml mintája): az
// ini-írást a hívó (FolderPane.qml) végzi a jelekre.
Dialog {
    id: root
    objectName: "folderPropertiesDialog"
    title: qsTr("Edit Folder Description")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel

    // a szerkesztett mappa — a hívó állítja be open() előtt
    property string folderPath: ""
    property string folderName: ""
    // a jelenlegi kézi dátum-felülírás ISO-alakban ("" = nincs, a mappa a
    // legrégebbi képe dátumát használja)
    property string currentDate: ""
    property string currentDescription: ""

    readonly property var _isoPattern: /^\d{4}-\d{2}-\d{2}$/
    // üres dátum is elfogadható: az „automatikus dátum" ága
    readonly property bool _dateValid:
        dateField.text.trim().length === 0
        || root._isoPattern.test(dateField.text.trim())

    // (mappa, ISO-dátum vagy "", leírás) — az Ok gomb
    signal folderPropertiesAccepted(string folderPath, string isoDate, string description)

    onOpened: {
        nameField.text = root.folderName
        dateField.text = root.currentDate
        descriptionField.text = root.currentDescription
        descriptionField.forceActiveFocus()
        standardButton(Dialog.Ok).enabled =
            Qt.binding(function() { return root._dateValid })
    }
    onAccepted: {
        if (!root._dateValid) return
        root.folderPropertiesAccepted(
            root.folderPath, dateField.text.trim(), descriptionField.text)
    }

    ColumnLayout {
        spacing: 10

        // -- Name: ---------------------------------------------------------
        Text {
            text: qsTr("Name:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            id: nameField
            objectName: "folderPropertiesNameField"
            Layout.preferredWidth: 320
            // a mappa átnevezése (fájlrendszer-művelet) még nincs bekötve
            enabled: false
        }

        // -- Date: ---------------------------------------------------------
        Text {
            text: qsTr("Date:")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        RowLayout {
            spacing: 8
            TextField {
                id: dateField
                objectName: "folderPropertiesDateField"
                Layout.preferredWidth: 160
                placeholderText: "2020-01-15"
            }
            PicasaButton {
                // az eredeti „Automatic date" gombja: törli a kézi
                // felülírást, a mappa a legrégebbi képe dátumára áll vissza
                objectName: "folderPropertiesAutomaticDate"
                text: qsTr("Automatic date")
                onClicked: dateField.text = ""
            }
        }
        Text {
            objectName: "folderPropertiesDateHint"
            visible: !root._dateValid
            text: qsTr("Enter the date as YYYY-MM-DD.")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.brandRed
        }

        // -- Music: --------------------------------------------------------
        CheckBox {
            id: musicCheck
            objectName: "folderPropertiesUseMusic"
            text: qsTr("Use music for Slideshow and Movie presentation:")
            // a diavetítés-zene még nincs bekötve
            enabled: false
        }
        RowLayout {
            spacing: 8
            Item { Layout.preferredWidth: 16 }  // az eredeti `spacer indent`
            TextField {
                objectName: "folderPropertiesMusicPath"
                Layout.fillWidth: true
                Layout.preferredWidth: 240
                // az eredeti `<bind attr="enabled" source="usemusic">`
                enabled: musicCheck.checked
            }
        }

        // -- Place taken (optional): ---------------------------------------
        Text {
            text: qsTr("Place taken (optional):")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            objectName: "folderPropertiesLocation"
            Layout.preferredWidth: 320
            // a mappa-szintű helyszín még nincs bekötve
            enabled: false
        }

        // -- Description (optional): ---------------------------------------
        Text {
            text: qsTr("Description (optional):")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        ScrollView {
            Layout.preferredWidth: 320
            // az eredeti height="3li" — három sornyi magas mező
            Layout.preferredHeight: Math.round(Theme.fontSize * 3 * 1.6)
            TextArea {
                id: descriptionField
                objectName: "folderPropertiesDescription"
                wrapMode: TextEdit.Wrap
            }
        }
    }
}

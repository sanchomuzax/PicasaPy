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
    //: A címek MÉRVE: `CEditAlbum::albumTitle` = „Album tulajdonságai",
    //: `CEditAlbum::folderTitle` = „Mappa tulajdonságai"
    //: (`referencia/stringres-en-hu.tsv`). ⚠️ A mappa-ág címe egyelőre a
    //: régi marad — az átvezetése a #422 hatóköre, nem ezé a jegyé.
    title: root.albumMode
        ? qsTr("Album Properties")
        : qsTr("Edit Folder Description")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    standardButtons: Dialog.Ok | Dialog.Cancel

    //: #3173: EGY párbeszéd, KÉT használat — a rajz ugyanaz (`album.fen`),
    //: csak a szerkesztett dolog más. „folder" = mappa (a #422 óta), „album"
    //: = virtuális album. Két másolat helyett egy komponens: ugyanaz az elv,
    //: mint a közös Alkalmaz/Mégse jelnél (#710).
    property string mode: "folder"
    readonly property bool albumMode: root.mode === "album"

    //: a szerkesztett album azonosítója (album módban)
    property string albumToken: ""
    property string albumLocation: ""

    // a szerkesztett mappa — a hívó állítja be open() előtt
    property string folderPath: ""
    property string folderName: ""
    // a jelenlegi kézi dátum-felülírás ISO-alakban ("" = nincs, a mappa a
    // legrégebbi képe dátumát használja)
    //: album módban az album neve (a prefillhez)
    property string albumName: ""
    property string currentDate: ""
    property string currentDescription: ""

    readonly property var _isoPattern: /^\d{4}-\d{2}-\d{2}$/
    // üres dátum is elfogadható: az „automatikus dátum" ága
    readonly property bool _dateValid:
        dateField.text.trim().length === 0
        || root._isoPattern.test(dateField.text.trim())

    // (mappa, ISO-dátum vagy "", leírás) — az Ok gomb
    signal folderPropertiesAccepted(string folderPath, string isoDate, string description)

    //: #3173: album módban a NÉV és a HELYSZÍN is menthető (az `ini/albums`
    //: mind a négy mezőt modellezi), ezért külön jel — a hívó ebből írja az
    //: album definícióját minden érintett mappa ini-jébe.
    signal albumPropertiesAccepted(string token, string name, string isoDate,
                                   string location, string description)

    onOpened: {
        nameField.text = root.albumMode ? root.albumName : root.folderName
        dateField.text = root.currentDate
        locationField.text = root.albumMode ? root.albumLocation : ""
        descriptionField.text = root.currentDescription
        if (root.albumMode) nameField.forceActiveFocus()
        else descriptionField.forceActiveFocus()
        standardButton(Dialog.Ok).enabled =
            Qt.binding(function() { return root._dateValid })
    }
    onAccepted: {
        if (!root._dateValid) return
        if (root.albumMode) {
            root.albumPropertiesAccepted(
                root.albumToken, nameField.text, dateField.text.trim(),
                locationField.text, descriptionField.text)
            return
        }
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
            //: #3173: ALBUM módban a név szerkeszthető (az album neve az
            //: ini-ben áll). Mappánál viszont fájlrendszer-művelet volna, és
            //: az még nincs bekötve — ott marad inaktív.
            enabled: root.albumMode
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
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
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
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
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }

        // -- Place taken (optional): ---------------------------------------
        Text {
            text: qsTr("Place taken (optional):")
            font.pixelSize: Theme.fontSize
            color: Theme.ink
        }
        TextField {
            id: locationField
            objectName: "folderPropertiesLocation"
            Layout.preferredWidth: 320
            //: #3173: ALBUM módban menthető (`location=` az album
            //: definíciójában); mappánál nincs mögötte réteg.
            enabled: root.albumMode
            // #422: jobbklikk-menü (Picasa `Address`)
            TextFieldContextArea {}
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
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

// „Mappa tulajdonságai" — a Picasa `album.fen` dialógusa (#422, #4456).
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
// Önálló, signal-alapú komponens (FolderDateDialog.qml mintája): az
// ini-írást a hívó (FolderPane.qml) végzi a jelekre.
Dialog {
    id: root
    objectName: "folderPropertiesDialog"
    //: A címek MÉRVE: `CEditAlbum::albumTitle` = „Album tulajdonságai",
    //: `CEditAlbum::folderTitle` = „Mappa tulajdonságai"
    //: (`referencia/stringres-en-hu.tsv`).
    title: root.albumMode
        ? qsTr("Album Properties")
        : qsTr("Folder Properties")
    modal: true
    focus: true
    anchors.centerIn: parent ? Overlay.overlay : undefined
    width: 585
    height: 315
    leftPadding: 13
    rightPadding: 13

    //: #3173: EGY párbeszéd, KÉT használat — a rajz ugyanaz (`album.fen`),
    //: csak a szerkesztett dolog más. „folder" = mappa (a #422 óta), „album"
    //: = virtuális album. Két másolat helyett egy komponens: ugyanaz az elv,
    //: mint a közös Alkalmaz/Mégse jelnél (#710).
    property string mode: "folder"
    readonly property bool albumMode: root.mode === "album"

    //: a szerkesztett album azonosítója (album módban)
    property string albumToken: ""
    property string albumLocation: ""
    property bool currentMusicEnabled: false
    property string currentMusicFile: ""

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
    signal folderMusicAccepted(string folderPath, bool useMusic, string musicFile)
    signal albumMusicAccepted(string token, bool useMusic, string musicFile)

    onOpened: {
        nameField.text = root.albumMode ? root.albumName : root.folderName
        dateField.text = root.currentDate
        locationField.text = root.albumMode ? root.albumLocation : ""
        descriptionField.text = root.currentDescription
        musicCheck.checked = root.currentMusicEnabled
        musicPathField.text = root.currentMusicFile
        if (root.albumMode) nameField.forceActiveFocus()
        else descriptionField.forceActiveFocus()
    }
    onAccepted: {
        if (!root._dateValid) return
        if (root.albumMode) {
            root.albumPropertiesAccepted(
                root.albumToken, nameField.text, dateField.text.trim(),
                locationField.text, descriptionField.text)
            root.albumMusicAccepted(
                root.albumToken, musicCheck.checked, musicPathField.text)
            return
        }
        root.folderPropertiesAccepted(
            root.folderPath, dateField.text.trim(), descriptionField.text)
        root.folderMusicAccepted(
            root.folderPath, musicCheck.checked, musicPathField.text)
    }

    footer: DialogButtonBox {
        id: footerButtons
        alignment: Qt.AlignRight
        spacing: 7
        // A Fusion alapértelmezett 6px-es alsó paddingje 7px-es margót ad;
        // a referencián mért 14px-hez 13px kell.
        bottomPadding: 13
        // A DialogButtonBox 10px-es stílus-alapértelmezése a külső margóhoz
        // hozzáadódik; 24px adja a referencián mért 14px-es jobb margót.
        rightPadding: 24

        Button {
            id: okButton
            objectName: "folderPropertiesOkButton"
            text: qsTr("OK")
            width: 85
            height: 24
            enabled: root._dateValid
            DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
        }
        Button {
            id: cancelButton
            objectName: "folderPropertiesCancelButton"
            text: qsTr("Cancel")
            width: 85
            height: 24
            DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
        }
    }

    ColumnLayout {
        // A Picasa sorai közötti 6px-es hézag. A Dátum és a Zene felső
        // ráhagyása megtartja a Name→Date és Date→Music 8px-es térközét;
        // a zeneválasztó utáni sorok így nem csúsznak lefelé.
        spacing: 6

        // -- Name: ---------------------------------------------------------
        RowLayout {
            spacing: 7
            Layout.fillWidth: true
            Text {
                objectName: "folderPropertiesNameLabel"
                text: qsTr("Name:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                Layout.preferredWidth: 205
                Layout.minimumWidth: 205
                Layout.maximumWidth: 205
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                horizontalAlignment: Text.AlignRight
            }
            TextField {
                id: nameField
                objectName: "folderPropertiesNameField"
                Layout.preferredWidth: 347
                Layout.maximumWidth: 347
                Layout.fillWidth: true
                Layout.minimumHeight: 26
                Layout.preferredHeight: 26
                Layout.maximumHeight: 26
                font.pixelSize: Theme.fontSize
                //: #3173: ALBUM módban a név szerkeszthető (az album neve az
                //: ini-ben áll). Mappánál viszont fájlrendszer-művelet volna, és
                //: az még nincs bekötve — ott marad inaktív.
                enabled: root.albumMode
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }

        // -- Date: ---------------------------------------------------------
        RowLayout {
            spacing: 7
            Layout.fillWidth: true
            Layout.topMargin: 2
            Text {
                objectName: "folderPropertiesDateLabel"
                text: qsTr("Date:")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                Layout.preferredWidth: 205
                Layout.minimumWidth: 205
                Layout.maximumWidth: 205
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                horizontalAlignment: Text.AlignRight
            }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                Layout.maximumWidth: 347
                RowLayout {
                    spacing: 8
                    TextField {
                        id: dateField
                        objectName: "folderPropertiesDateField"
                        Layout.preferredWidth: 104
                        Layout.minimumHeight: 26
                        Layout.preferredHeight: 26
                        Layout.maximumHeight: 26
                        font.pixelSize: Theme.fontSize
                        placeholderText: "2020-01-15"
                        // #422: jobbklikk-menü (Picasa `Address`)
                        TextFieldContextArea {}
                    }
                    PicasaButton {
                        // az eredeti „Automatic date" gombja: törli a kézi
                        // felülírást, a mappa a legrégebbi képe dátumára áll vissza
                        objectName: "folderPropertiesAutomaticDate"
                        text: qsTr("Automatic date")
                        Layout.preferredWidth: 139
                        Layout.preferredHeight: 26
                        onClicked: dateField.text = ""
                    }
                }
                Text {
                    id: dateHint
                    objectName: "folderPropertiesDateHint"
                    visible: !root._dateValid
                    text: qsTr("Enter the date as YYYY-MM-DD.")
                    font.pixelSize: Theme.fontSize - 1
                    color: Theme.brandRed
                    Layout.fillWidth: true
                }
            }
        }

        // A pipa és az alá behúzott hangfájl-sor ugyanabba a bal hasábba
        // igazodik; a köztük lévő távolság kisebb, mint a fő soroké.
        ColumnLayout {
            spacing: 2
            Layout.fillWidth: true
            Layout.topMargin: 2
            RowLayout {
                spacing: 7
                Layout.fillWidth: true
                Text {
                    objectName: "folderPropertiesMusicLabel"
                    text: qsTr("Music:")
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                    Layout.preferredWidth: 205
                    Layout.minimumWidth: 205
                    Layout.maximumWidth: 205
                    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                    horizontalAlignment: Text.AlignRight
                }
                CheckBox {
                    id: musicCheck
                    objectName: "folderPropertiesUseMusic"
                    text: qsTr("Use music for Slideshow and Movie presentation:")
                    font.pixelSize: Theme.fontSize
                    //: A hu fordítás hosszabb a mezőoszlopnál; a platform
                    //: betűkészletéhez igazodva csak szükség esetén zsugorodjon,
                    //: ne vágja le a sor végét.
                    Binding {
                        target: musicCheck.contentItem
                        property: "fontSizeMode"
                        value: Text.HorizontalFit
                    }
                    Binding {
                        target: musicCheck.contentItem
                        property: "minimumPixelSize"
                        value: Theme.fontSize - 2
                    }
                    Layout.preferredHeight: 18
                    Layout.fillWidth: true
                    Layout.maximumWidth: 347
                }
            }
            RowLayout {
                spacing: 7
                Layout.fillWidth: true
                Item {
                    Layout.preferredWidth: 205
                    Layout.minimumWidth: 205
                    Layout.maximumWidth: 205
                }
                RowLayout {
                    spacing: 6
                    Layout.fillWidth: true
                    Layout.maximumWidth: 347
                    // 10px + a RowLayout 6px-es köztes hézaga = az eredeti
                    // 16px-es `spacer indent`.
                    Item { Layout.preferredWidth: 10 }
                    TextField {
                        id: musicPathField
                        objectName: "folderPropertiesMusicPath"
                        Layout.fillWidth: true
                        Layout.preferredWidth: 240
                        Layout.minimumHeight: 26
                        Layout.preferredHeight: 26
                        Layout.maximumHeight: 26
                        font.pixelSize: Theme.fontSize
                        // az eredeti `<bind attr="enabled" source="usemusic">`
                        enabled: musicCheck.checked
                        // #422: jobbklikk-menü (Picasa `Address`)
                        TextFieldContextArea {}
                    }
                    PicasaButton {
                        objectName: "folderPropertiesMusicBrowseButton"
                        text: qsTr("Browse...")
                        Layout.preferredWidth: 85
                        Layout.preferredHeight: 26
                        enabled: musicCheck.checked
                        onClicked: musicFileDialog.open()
                    }
                }
            }
        }

        // -- Place taken (optional): ---------------------------------------
        RowLayout {
            spacing: 7
            Layout.fillWidth: true
            Text {
                objectName: "folderPropertiesLocationLabel"
                text: qsTr("Place taken (optional):")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                Layout.preferredWidth: 205
                Layout.minimumWidth: 205
                Layout.maximumWidth: 205
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                horizontalAlignment: Text.AlignRight
            }
            TextField {
                id: locationField
                objectName: "folderPropertiesLocation"
                Layout.preferredWidth: 347
                Layout.maximumWidth: 347
                Layout.fillWidth: true
                Layout.minimumHeight: 26
                Layout.preferredHeight: 26
                Layout.maximumHeight: 26
                font.pixelSize: Theme.fontSize
                //: #3173: ALBUM módban menthető (`location=` az album
                //: definíciójában); mappánál nincs mögötte réteg.
                enabled: root.albumMode
                // #422: jobbklikk-menü (Picasa `Address`)
                TextFieldContextArea {}
            }
        }

        // -- Description (optional): ---------------------------------------
        RowLayout {
            spacing: 7
            Layout.fillWidth: true
            Text {
                objectName: "folderPropertiesDescriptionLabel"
                text: qsTr("Description (optional):")
                font.pixelSize: Theme.fontSize
                color: Theme.ink
                Layout.preferredWidth: 205
                Layout.minimumWidth: 205
                Layout.maximumWidth: 205
                Layout.alignment: Qt.AlignRight | Qt.AlignTop
                Layout.topMargin: 7
                horizontalAlignment: Text.AlignRight
            }
            ScrollView {
                Layout.preferredWidth: 347
                Layout.maximumWidth: 347
                Layout.fillWidth: true
                // az eredeti height="3li" — három sornyi magas mező
                Layout.preferredHeight: 64
                TextArea {
                    id: descriptionField
                    objectName: "folderPropertiesDescription"
                    wrapMode: TextEdit.Wrap
                    font.pixelSize: Theme.fontSize
                    background: Rectangle {
                        color: Theme.controlBase
                        border.color: Theme.chromeBorder
                        border.width: 1
                    }
                    // #422: jobbklikk-menü (Picasa `Address`)
                    TextFieldContextArea {}
                }
            }
        }
    }

    FileDialog {
        id: musicFileDialog
        objectName: "folderPropertiesMusicFileDialog"
        title: qsTr("Audio files")
        fileMode: FileDialog.OpenFile
        nameFilters: [
            Qt.platform.os === "windows"
                ? qsTr("Music files (*.mp3, *.wma)")
                : qsTr("Music files (*.mp3, *.m4a)")
        ]
        onAccepted: {
            var selected = selectedFile.toString()
            if (typeof controller !== "undefined" && controller
                    && typeof controller.localPathFromFileUrl === "function")
                selected = controller.localPathFromFileUrl(selected)
            musicPathField.text = selected
        }
    }
}

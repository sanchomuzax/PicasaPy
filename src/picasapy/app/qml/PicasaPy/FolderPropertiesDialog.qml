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
    bottomPadding: 0

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
    property var renameFolderHandler: null
    property string renameError: ""

    // a szerkesztett mappa — a hívó állítja be open() előtt
    property string folderPath: ""
    property string folderName: ""
    // a jelenlegi kézi dátum-felülírás ISO-alakban ("" = nincs, a mappa a
    // legrégebbi képe dátumát használja)
    //: album módban az album neve (a prefillhez)
    property string albumName: ""
    property string currentDate: ""
    property string currentDescription: ""

    // A dátummező a nyelvi beállítás szerinti alakot mutatja (magyarul
    // `2026. 01. 01.`); a mentett érték ISO-alakú (ÉÉÉÉ-HH-NN), ahogy eddig.
    function _dateFormat() {
        return Qt.locale().dateFormat(Locale.ShortFormat).replace(/y+/, "yyyy")
    }

    // ISO-dátumot a nyelvi alakjára fordít; ami nem ISO, az változatlanul marad
    // (így a hibás régi érték hibaüzenetet ad, nem tűnik üres dátumnak).
    function _isoToField(iso) {
        var reszek = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
        if (!reszek)
            return iso
        return Qt.formatDate(
            new Date(Number(reszek[1]), Number(reszek[2]) - 1, Number(reszek[3])),
            root._dateFormat())
    }

    // A beírt szöveg ISO-dátuma: "" = üres (automatikus dátum), null = hibás.
    // ISO-alakot mindig elfogad; a többi alakban a nyelvi sorrend dönt.
    function _fieldToIso(szoveg) {
        var be = szoveg.trim()
        if (be.length === 0)
            return ""
        var reszek = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(be)
        var mezok = {}
        if (reszek) {
            mezok = { y: reszek[1], M: reszek[2], d: reszek[3] }
        } else {
            var szamok = be.match(/\d+/g)
            var sorrend = root._dateFormat().match(/y+|M+|d+/g)
            if (!szamok || !sorrend || szamok.length !== 3 || sorrend.length !== 3)
                return null
            for (var i = 0; i < 3; ++i)
                mezok[sorrend[i].charAt(0)] = szamok[i]
        }
        if (!mezok.y || mezok.y.length !== 4 || !mezok.M || !mezok.d)
            return null
        var ev = Number(mezok.y)
        var honap = Number(mezok.M)
        var nap = Number(mezok.d)
        var datum = new Date(ev, honap - 1, nap)
        if (datum.getFullYear() !== ev || datum.getMonth() !== honap - 1
                || datum.getDate() !== nap)
            return null
        return ev + "-" + ("0" + honap).slice(-2) + "-" + ("0" + nap).slice(-2)
    }

    // üres dátum is elfogadható: az „automatikus dátum" ága
    readonly property bool _dateValid: root._fieldToIso(dateField.text) !== null

    // a mezőben lévő dátum ISO-alakban (érvénytelennél a mentés úgyis tiltott)
    function _datumIso() {
        return root._fieldToIso(dateField.text) || ""
    }

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
        dateField.text = root._isoToField(root.currentDate)
        locationField.text = root.albumMode ? root.albumLocation : ""
        descriptionField.text = root.currentDescription
        musicCheck.checked = root.currentMusicEnabled
        musicPathField.text = root.currentMusicFile
        root.renameError = ""
        nameField.forceActiveFocus()
        nameField.selectAll()
    }
    onAccepted: {
        if (!root._dateValid) return
        if (root.albumMode) {
            root.albumPropertiesAccepted(
                root.albumToken, nameField.text, root._datumIso(),
                locationField.text, descriptionField.text)
            root.albumMusicAccepted(
                root.albumToken, musicCheck.checked, musicPathField.text)
            return
        }
        root.folderPropertiesAccepted(
            root.folderPath, root._datumIso(), descriptionField.text)
        root.folderMusicAccepted(
            root.folderPath, musicCheck.checked, musicPathField.text)
    }

    function _saveProperties() {
        if (!root._dateValid)
            return
        // Változatlan névnél nincs átnevezés — a dátum/leírás/zene mentése
        // átnevező nélkül is működjön (#4503 OK-tesztje).
        if (!root.albumMode && nameField.text !== root.folderName) {
            if (typeof root.renameFolderHandler !== "function") {
                root.renameError = qsTr("Folder renaming is unavailable.")
                renameErrorDialog.open()
                return
            }
            var result = root.renameFolderHandler(root.folderPath, nameField.text)
            if (!result || result.ok !== true) {
                root.renameError = result && result.error
                    ? result.error : qsTr("Folder renaming is unavailable.")
                renameErrorDialog.open()
                return
            }
            root.folderPath = result.path
            root.folderName = result.name
            nameField.text = result.name
        }
        root.accept()
    }

    MessageDialog {
        id: renameErrorDialog
        objectName: "folderPropertiesRenameErrorDialog"
        title: qsTr("Cannot Rename Folder")
        text: root.renameError
        buttons: MessageDialog.Ok
    }

    footer: Item {
        id: footerArea
        // A lábléc saját, rögzített alsó sávja a tartalomtól függetlenül a
        // párbeszéd alján marad; a fölötte lévő tartalom kapja a maradék helyet.
        implicitHeight: 38

        DialogButtonBox {
            id: footerButtons
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 14
            alignment: Qt.AlignRight
            spacing: 7
            height: 24
            topPadding: 0
            bottomPadding: 0
            // A DialogButtonBox 10px-es stílus-alapértelmezése a külső margóhoz
            // hozzáadódik; 24px adja a referencián mért 14px-es jobb margót.
            rightPadding: 24
            // A gombsort egy rögzített sáv tartja, nem közvetlenül a Dialog
            // footer-e, ezért a Dialog nem köti be magától (#4503). Az OK a saját
            // onClicked-jén át ment és zár (#4482: előbb átnevez), így itt csak a
            // Mégse kötése kell — egy onAccepted kettős mentést adna.
            onRejected: root.reject()

            Button {
                id: okButton
                objectName: "folderPropertiesOkButton"
                text: qsTr("OK")
                width: 85
                height: 24
                enabled: root._dateValid
                DialogButtonBox.buttonRole: DialogButtonBox.NoButton
                onClicked: root._saveProperties()
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
    }

    // A hosszú magyar feliratok a saját oszlopuk teljes szélességét használják.
    // A betűméret marad a témáé; csak a szükséges minimális betűköz segít, hogy
    // más platformon se lógjanak át a párbeszéd határán.
    TextMetrics {
        id: locationLabelMetrics
        font.family: locationLabel.font.family
        font.pixelSize: Theme.fontSize
        font.weight: locationLabel.font.weight
        font.letterSpacing: 0
        text: locationLabel.text
    }
    TextMetrics {
        id: musicLabelMetrics
        font.family: musicCheck.font.family
        font.pixelSize: Theme.fontSize
        font.weight: musicCheck.font.weight
        font.letterSpacing: 0
        text: musicCheck.text
    }
    TextMetrics {
        id: descriptionLabelMetrics
        font.family: descriptionLabel.font.family
        font.pixelSize: descriptionLabel.font.pixelSize
        font.weight: descriptionLabel.font.weight
        font.letterSpacing: 0
        text: descriptionLabel.text
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
                enabled: true
                onAccepted: root._saveProperties()
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
                        placeholderText: root._isoToField("2020-01-15")
                        // a naptár-ikon a mező jobb szélén, az eredetiben is ott
                        rightPadding: 26
                        onAccepted: root._saveProperties()
                        // #422: jobbklikk-menü (Picasa `Address`)
                        TextFieldContextArea {}

                        ToolButton {
                            id: calendarButton
                            objectName: "folderPropertiesDateCalendarButton"
                            anchors.right: parent.right
                            anchors.rightMargin: 1
                            anchors.verticalCenter: parent.verticalCenter
                            width: 24
                            height: 24
                            padding: 0
                            //: #4494: a naptár-gomb súgója (az eredetiben nincs külön felirata)
                            ToolTip.visible: hovered
                            ToolTip.delay: Theme.tooltipDelay
                            ToolTip.text: qsTr("Choose date")
                            onClicked: calendarPopup.openBelow(
                                dateField, root._datumIso())
                            contentItem: Item {
                                Rectangle {
                                    anchors.centerIn: parent
                                    width: 12
                                    height: 11
                                    color: "transparent"
                                    border.color: Theme.ink
                                    border.width: 1
                                    Rectangle {
                                        width: parent.width
                                        height: 3
                                        color: Theme.ink
                                    }
                                }
                            }
                        }
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
                    //: %1 a nyelvi dátumalak mintája (magyarul „2026. 01. 01.”)
                    text: qsTr("Enter the date like this: %1").arg(
                        Qt.formatDate(new Date(2026, 0, 1), root._dateFormat()))
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
                // A jelölő a mezőoszlop bal szélére kerül; a teljes jobb
                // oszlopszélességet megkapja, a felirat a jelölő után indul.
                spacing: 0
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
                    font.letterSpacing: Math.min(
                        0,
                        (
                            contentItem.width
                            - contentItem.leftPadding
                            - contentItem.rightPadding
                            - musicLabelMetrics.advanceWidth
                        ) / Math.max(1, text.length - 1)
                    )
                    rightPadding: 0
                    topPadding: 0
                    bottomPadding: 0
                    Binding {
                        target: musicCheck.contentItem
                        property: "wrapMode"
                        value: Text.NoWrap
                    }
                    Binding {
                        target: musicCheck.contentItem
                        property: "elide"
                        value: Text.ElideNone
                    }
                    Layout.preferredHeight: 18
                    Layout.fillWidth: true
                    Layout.maximumWidth: 354
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
                        onAccepted: root._saveProperties()
                        // az eredeti `<bind attr="enabled" source="usemusic">`
                        enabled: musicCheck.checked
                        background: Rectangle {
                            color: musicPathField.enabled
                                ? Theme.controlBase
                                : musicPathField.palette.button
                            border.color: Theme.chromeBorder
                            border.width: 1
                        }
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
                id: locationLabel
                objectName: "folderPropertiesLocationLabel"
                text: qsTr("Place taken (optional):")
                font.pixelSize: Theme.fontSize
                font.letterSpacing: Math.min(
                    0,
                    (width - locationLabelMetrics.advanceWidth)
                        / Math.max(1, text.length - 1)
                )
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
                onAccepted: root._saveProperties()
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
                id: descriptionLabel
                objectName: "folderPropertiesDescriptionLabel"
                text: qsTr("Description (optional):")
                font.pixelSize: Theme.fontSize
                font.letterSpacing: Math.min(
                    0,
                    (width - descriptionLabelMetrics.advanceWidth)
                        / Math.max(1, text.length - 1)
                )
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

    // #4494: a naptár a dátummező alatt nyílik; a nap a mezőbe kerül, a mentés
    // az OK-ra történik, mint a kézi beírásnál.
    DateCalendarPopup {
        id: calendarPopup
        objectName: "folderPropertiesCalendar"
        parent: root.contentItem
        onDateChosen: function(iso) {
            dateField.text = root._isoToField(iso)
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

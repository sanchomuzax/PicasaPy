import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Emberek-panel (#26) — a Picasa jobb oldali fiókjának NEGYEDIK panelje.
//
// A hely nem találgatás: a binárisban a `rightdrawerpanel/peoplepanel`
// elem a `propertiespanel` · `tagpanel` · `geopanel` mellett áll — abból a
// négyesből nálunk eddig három volt meg (Tulajdonságok, Címkék, Helyek).
// A panel címe az eredetiben `PeoplePanel::title` = „People".
//
// A panel EGY fejlécet és EGY listát mutat (#3566, spec
// `picasa-arcfelismeres.md` 9/b–9/d). A fejlécet az eredetiben a
// `0x00647df0` választja az eredeti szövegforrásából:
//
//   EGYSOROS ág — a szerkesztőben, VAGY (1 eredménysor ÉS nem személy-album):
//     van személy → PeoplePanel::InThis „In this photo:"
//     van kép     → PeoplePanel::Who    „Who is in these photos?"
//     különben    → Text5 (lent)
//   TÖBBSOROS ág — minden más (0 vagy több eredménysor, személy-album):
//     van személy → személy-album ? Known1 „Also in these photos:"
//                                 : Known2 „People in these photos:"
//     van kép     → csoportosítva ? UnnamedCluster : Unnamed
//     különben    → személy-album ? Text4 : Text5
//
// A „Szintén ezeken a fotókon:" tehát NEM második szakasz, hanem a
// személy albumának fejléce ugyanarra a listára. A „van személy" a 9/c
// szerint: a kijelölt képek arcai közül legalább egynek van neve.
//
// Nem jelenítjük meg: a betöltés-feliratokat (Loading1/2, Looking) — a
// `peopleOfRows` szinkron, nálunk nincs betöltési állapot —, és az
// „, %d ellenőrizetlen fájl." utótagot — folyamatos háttér-arcellenőrzés
// híján nincs ilyen számunk.
//
// A panel buta komponens: a listát kívülről kapja, a navigációt jellel
// kéri — a TagsPanel/PropertiesPanel mintája.
Rectangle {
    id: panel
    objectName: "peoplePanel"
    color: Theme.panelBg

    // a kijelölt képeken névvel szereplő emberek (`controller.peopleOfRows`);
    // a lista elemszáma tükrözi a panel eredménysorainak számát
    property var peopleHere: []
    // a kijelölt képek saját, még névtelen arcai
    property var unnamedFacesHere: []
    property var faceScanController: null
    // a nézett SZEMÉLY-album neve — egyébként üres
    property string currentPerson: ""
    property int selectionCount: 0
    property bool folderSelected: true
    // a szerkesztő (néző) példánya: az eredetiben az `editpanel/preview`
    // láthatósága, ilyenkor mindig az egyképes ág fut
    property bool editorView: false
    // #3585 (spec 9/b–9/d): a „Név nélküliek" album nyitva van, és a
    // fejléc váltógombja csoportosított állapotban áll
    property bool unnamedAlbumMode: false
    property bool unnamedGrouped: true
    property int pendingIgnoreFaceId: -1
    property int pendingNewFaceId: -1
    property string pendingNewFaceName: ""
    // A Picasa kézi hozzáadás állapota: ilyenkor a lista és az indítógomb
    // helyén a `manual_frame` útmutatója látszik.
    property bool manualAddActive: false

    signal personChosen(string name)
    signal closeRequested()
    signal manualAddRequested()
    signal manualCancelRequested()

    readonly property bool personAlbum:
        panel.currentPerson.length > 0 && !panel.unnamedAlbumMode
    // A megnevezett személyek tényleges sorai adják az eredménysorszámot. Ha
    // nincs ilyen sor, a rendelkezésre álló kijelölésszám a névtelen ág
    // egyes/többes választója: képeké a főnézetben, arcoké az album nézetében.
    readonly property int resultRowCount:
        panel.people.length > 0 ? panel.people.length : panel.selectionCount
    readonly property bool singlePhotoBranch:
        panel.editorView
        || (panel.resultRowCount === 1 && !panel.personAlbum)
    // a Név nélküliek albumban a kijelölés névtelen arcoké — ott a rács
    // kijelölésének neveit nem mutatjuk
    readonly property var people:
        panel.unnamedAlbumMode ? []
        : panel.personAlbum && !panel.editorView
          ? panel.peopleHere.filter(function(person) {
              return String(person.name).toLowerCase()
                  !== panel.currentPerson.toLowerCase()
          })
          : panel.peopleHere
    readonly property bool hasPeople: panel.people.length > 0
    readonly property bool hasPhotos: panel.selectionCount > 0
    readonly property bool needsFolderSelection:
        !panel.folderSelected && !panel.personAlbum && !panel.unnamedAlbumMode

    readonly property string ignoreConfirmKey: "ignoreFaces"

    function assignNameToFace(faceId, name) {
        if (!panel.faceScanController || !name || !String(name).trim())
            return false
        var assigned = panel.faceScanController.assignNameToFaces(
            [faceId], String(name).trim())
        if (assigned && typeof controller !== "undefined" && controller)
            controller.refreshCollections()
        return assigned
    }

    function _hasPersonNamed(name) {
        var ctl = typeof controller !== "undefined" ? controller : null
        if (!ctl)
            return false
        var entries = ctl.peopleManagerContacts()
        var wanted = String(name).trim().toLocaleLowerCase()
        for (var i = 0; i < entries.length; ++i) {
            if (String(entries[i].name).trim().toLocaleLowerCase() === wanted)
                return true
        }
        return false
    }

    function _openPendingPersonDialog() {
        if (!peopleManagerLoader.item || panel.pendingNewFaceId < 0)
            return
        peopleManagerLoader.item.controller = typeof controller !== "undefined"
            ? controller : null
        peopleManagerLoader.item.faceScanController = panel.faceScanController
        peopleManagerLoader.item.openForFace(
            panel.pendingNewFaceName, panel.pendingNewFaceId)
    }

    function nameFaceFromPanel(faceId, name) {
        var cleanName = String(name || "").trim()
        if (faceId < 0 || !cleanName)
            return
        if (panel._hasPersonNamed(cleanName)) {
            panel.assignNameToFace(faceId, cleanName)
            return
        }
        panel.pendingNewFaceId = faceId
        panel.pendingNewFaceName = cleanName
        if (peopleManagerLoader.status === Loader.Ready)
            panel._openPendingPersonDialog()
        else
            peopleManagerLoader.active = true
    }

    function requestIgnoreFace(faceId) {
        if (!panel.faceScanController || faceId < 0)
            return
        panel.pendingIgnoreFaceId = faceId
        if (typeof confirmSettings !== "undefined" && confirmSettings
                && confirmSettings.isSuppressed(panel.ignoreConfirmKey)) {
            panel.ignorePendingFace()
            return
        }
        dontAskCheck.checked = false
        ignoreConfirm.open()
    }

    function ignorePendingFace() {
        var faceId = panel.pendingIgnoreFaceId
        panel.pendingIgnoreFaceId = -1
        if (faceId < 0 || !panel.faceScanController)
            return 0
        var count = panel.faceScanController.ignoreFaces([faceId])
        if (typeof controller !== "undefined" && controller)
            controller.refreshCollections()
        return count
    }

    // a fejléc (`status_label`); üres, ha az utasítás-szöveg látszik
    readonly property string headerText:
        panel.personAlbum && !panel.editorView && !panel.hasPeople
            ? ""
            : panel.singlePhotoBranch
            ? (panel.hasPeople ? qsTr("In this photo:")
               : panel.hasPhotos ? qsTr("Who is in these photos?")
               : "")
            : (panel.hasPeople
               ? (panel.personAlbum ? qsTr("Also in these photos:")
                                    : qsTr("People in these photos:"))
               : panel.hasPhotos
                 ? (panel.unnamedAlbumMode && panel.unnamedGrouped
                    ? qsTr("Unnamed people in these photos:")
                    : qsTr("Unnamed groups of people:"))
               : "")

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 5
        spacing: 6

        //: #754: a CÍM és a bezáró gomb a FIÓK közös fejlécében él
        //: (`RightDrawer`), nem a panelben.

        Text {
            objectName: "peoplePanelStatusLabel"
            visible: panel.needsFolderSelection && !panel.manualAddActive
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Select a folder to display faces")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        Text {
            objectName: "peoplePanelHeader"
            visible: panel.headerText.length > 0 && !panel.manualAddActive
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: panel.headerText
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        Repeater {
            model: panel.people
            visible: !panel.manualAddActive
            delegate: PeoplePanelRow {
                required property var modelData
                Layout.fillWidth: true
                availableWidth: panel.width - 10
                personName: modelData.name
                photoUrl: modelData.thumbUrl
                onChosen: panel.personChosen(modelData.name)
            }
        }
        Repeater {
            model: panel.unnamedFacesHere
            visible: !panel.manualAddActive
            delegate: PeoplePanelRow {
                required property var modelData
                Layout.fillWidth: true
                availableWidth: panel.width - 10
                unnamedFace: true
                faceId: modelData.faceId
                photoUrl: modelData.thumbUrl
                onNameSubmitted: function(id, name) {
                    panel.nameFaceFromPanel(id, name)
                }
                onIgnoreRequested: function(id) {
                    panel.requestIgnoreFace(id)
                }
            }
        }

        // -- utasítás-szöveg (`instructions`, `peoplepanel_text.tre`), ha
        // nincs fejléc:
        //
        //   Text3 „No people have been found yet…"  — a Név nélküliek
        //                                               album, 0 kijelölés
        //   Text4 „Named people who appear WITH…"   — személy-album
        //   Text5 „People who appear in the currently
        //          selected photos will be listed here." — minden más
        Text {
            objectName: "peoplePanelEmptyText"
            visible: panel.headerText.length === 0
                     && !panel.needsFolderSelection
                     && panel.unnamedFacesHere.length === 0
                     && !panel.manualAddActive
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: panel.unnamedAlbumMode
                  ? qsTr("No people have been found yet. As faces are "
                         + "found and grouped, they will appear in the "
                         + "Unnamed album.")
                  : panel.personAlbum && !panel.singlePhotoBranch
                    ? qsTr("Named people who appear with the currently "
                           + "selected person will be listed here.")
                    : qsTr("People who appear in the currently selected "
                           + "photos will be listed here.")
            font.pixelSize: Theme.fontSize - 1
            font.italic: true
            color: Theme.textGray
        }

        Item { Layout.fillHeight: true }

        PicasaButton {
            objectName: "peoplePanelManualAddButton"
            visible: !panel.manualAddActive
            enabled: panel.selectionCount > 0
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 259
            Layout.preferredHeight: 21
            text: qsTr("Add a person manually")
            onClicked: panel.manualAddRequested()
        }
    }

    Rectangle {
        objectName: "peoplePanelManualFrame"
        visible: panel.manualAddActive
        x: 18
        y: 105
        width: 239
        height: 145
        color: panel.color
        border.color: Theme.buttonBorder
        border.width: 1

        Text {
            objectName: "peoplePanelManualInstructions"
            x: 9
            y: 6
            width: 221
            height: 86
            wrapMode: Text.WordWrap
            text: qsTr("Instructions:\n\n"
                + "1) Manipulate the rectangle to fit the face of the person "
                + "you want to add.\n\n"
                + "You can drag the rectangle to position it, and move its "
                + "sides to refine the shape.\n\n"
                + "2) Click on \"Add a name\" under the rectangle and type "
                + "in the person's name.\n\n"
                + "(Be sure to either press Enter or click on an "
                + "autocompleted name to indicate that you are done)")
            font.pixelSize: Math.max(8, Theme.fontSize - 5)
            color: Theme.textGray
        }

        PicasaButton {
            objectName: "peoplePanelManualCancelButton"
            x: 71
            y: 105
            width: 98
            height: 28
            text: qsTr("Cancel")
            onClicked: panel.manualCancelRequested()
        }
    }

    Dialog {
        id: ignoreConfirm
        objectName: "peoplePanelIgnoreDialog"
        title: qsTr("Ignore People")
        modal: true
        anchors.centerIn: Overlay.overlay
        standardButtons: Dialog.Yes | Dialog.Cancel
        onOpened: standardButton(Dialog.Yes).text = qsTr("Ignore Person")
        onAccepted: {
            if (dontAskCheck.checked && typeof confirmSettings !== "undefined"
                    && confirmSettings)
                confirmSettings.setSuppressed(panel.ignoreConfirmKey, true)
            panel.ignorePendingFace()
        }
        onRejected: panel.pendingIgnoreFaceId = -1

        ColumnLayout {
            spacing: 12
            Label {
                objectName: "peoplePanelIgnoreMessage"
                Layout.preferredWidth: 380
                wrapMode: Text.WordWrap
                text: qsTr("Are you sure you want to move this person to the "
                           + "ignored people album?")
                font.pixelSize: Theme.fontSize
            }
            CheckBox {
                id: dontAskCheck
                objectName: "peoplePanelIgnoreDontAskCheck"
                text: qsTr("Don't ask again, always ignore")
                font.pixelSize: Theme.fontSize
            }
        }
    }

    Loader {
        id: peopleManagerLoader
        objectName: "peoplePanelPeopleManagerLoader"
        active: false
        source: Qt.resolvedUrl("PeopleManagerDialog.qml")
        onLoaded: panel._openPendingPersonDialog()
        onItemChanged: {
            if (item) {
                item.controller = typeof controller !== "undefined"
                    ? controller : null
                item.faceScanController = panel.faceScanController
                item.closed.connect(function() {
                    panel.pendingNewFaceId = -1
                    panel.pendingNewFaceName = ""
                })
            }
        }
    }
}

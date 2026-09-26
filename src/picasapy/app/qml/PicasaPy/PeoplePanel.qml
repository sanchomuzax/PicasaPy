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
//   EGYKÉPES ág — a szerkesztőben, VAGY (1 kép ÉS nem személy-album):
//     van személy → PeoplePanel::InThis „In this photo:"
//     van kép     → PeoplePanel::Who    „Who is in these photos?"
//     különben    → Text5 (lent)
//   TÖBBKÉPES ág — minden más (több kép, 0 kép, személy-album):
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

    // a kijelölt képeken névvel szereplő emberek (`controller.peopleOfRows`)
    property var peopleHere: []
    // a nézett SZEMÉLY-album neve — egyébként üres
    property string currentPerson: ""
    property int selectionCount: 0
    // a szerkesztő (néző) példánya: az eredetiben az `editpanel/preview`
    // láthatósága, ilyenkor mindig az egyképes ág fut
    property bool editorView: false
    // #3585 (spec 9/b–9/d): a „Név nélküliek" album nyitva van, és a
    // fejléc váltógombja csoportosított állapotban áll
    property bool unnamedAlbumMode: false
    property bool unnamedGrouped: true

    signal personChosen(string name)
    signal closeRequested()

    readonly property bool personAlbum:
        panel.currentPerson.length > 0 && !panel.unnamedAlbumMode
    readonly property bool singlePhotoBranch:
        panel.editorView
        || (panel.selectionCount === 1 && !panel.personAlbum)
    // a Név nélküliek albumban a kijelölés névtelen arcoké — ott a rács
    // kijelölésének neveit nem mutatjuk
    readonly property var people:
        panel.unnamedAlbumMode ? [] : panel.peopleHere
    readonly property bool hasPeople: panel.people.length > 0
    readonly property bool hasPhotos: panel.selectionCount > 0

    // a fejléc (`status_label`); üres, ha az utasítás-szöveg látszik
    readonly property string headerText:
        panel.singlePhotoBranch
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
        anchors.margins: 8
        spacing: 6

        //: #754: a CÍM és a bezáró gomb a FIÓK közös fejlécében él
        //: (`RightDrawer`), nem a panelben.

        Text {
            objectName: "peoplePanelHeader"
            visible: panel.headerText.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: panel.headerText
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        Repeater {
            model: panel.people
            delegate: PeoplePanelRow {
                required property var modelData
                Layout.fillWidth: true
                personName: modelData.name
                photoCount: modelData.count
                onChosen: panel.personChosen(modelData.name)
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
    }
}

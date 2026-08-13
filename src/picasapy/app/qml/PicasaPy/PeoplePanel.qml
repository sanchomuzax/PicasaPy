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
// A két szakasz is az eredeti szövegforrásából jön:
//
//   PeoplePanel::InThis  „In this photo:"          — egy kijelölt képnél
//   PeoplePanel::Known2  „People in these photos:" — több kijelölt képnél
//   PeoplePanel::Known1  „Also in these photos:"   — egy SZEMÉLY albumát
//                                                    nézve: kik szerepelnek
//                                                    vele együtt
//
// Az utolsó a családi gyűjtemények természetes navigációja („ki van még
// rajta ezeken a képeken?"), onnan egy kattintással a másik személy
// albumába.
//
// A panel buta komponens: a listákat kívülről kapja, a navigációt jellel
// kéri — a TagsPanel/PropertiesPanel mintája.
Rectangle {
    id: panel
    objectName: "peoplePanel"
    color: Theme.panelBg

    // a kijelölt képeken névvel szereplő emberek (`controller.peopleOfRows`)
    property var peopleHere: []
    // ha épp egy SZEMÉLY albumát nézzük: kik szerepelnek vele együtt
    // (`controller.peopleWith`) — egyébként üres
    property var peopleWith: []
    property string currentPerson: ""
    property int selectionCount: 0

    signal personChosen(string name)
    signal closeRequested()

    // az eredeti szakasz-feliratai (PeoplePanel::InThis / Known2 / Known1)
    readonly property string hereLabel:
        panel.selectionCount > 1 ? qsTr("People in these photos:")
                                 : qsTr("In this photo:")

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "peoplePanelTitle"
                Layout.fillWidth: true
                text: qsTr("People")
                font.pixelSize: Theme.fontSize
                font.bold: true
                color: Theme.ink
            }
            ToolButton {
                objectName: "peoplePanelClose"
                text: "✕"
                onClicked: panel.closeRequested()
            }
        }

        // -- 1. szakasz: akik a kijelölt képeken vannak ------------------
        Text {
            objectName: "peoplePanelHereLabel"
            visible: panel.peopleHere.length > 0
            Layout.fillWidth: true
            text: panel.hereLabel
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        Repeater {
            model: panel.peopleHere
            delegate: PeoplePanelRow {
                required property var modelData
                Layout.fillWidth: true
                personName: modelData.name
                photoCount: modelData.count
                onChosen: panel.personChosen(modelData.name)
            }
        }

        // -- 2. szakasz: akik EGYÜTT szerepelnek a nézett személlyel -----
        Text {
            objectName: "peoplePanelAlsoLabel"
            visible: panel.peopleWith.length > 0
            Layout.fillWidth: true
            topPadding: 6
            text: qsTr("Also in these photos:")
            font.pixelSize: Theme.fontSize - 1
            color: Theme.textGray
        }
        Repeater {
            model: panel.peopleWith
            delegate: PeoplePanelRow {
                required property var modelData
                Layout.fillWidth: true
                personName: modelData.name
                photoCount: modelData.count
                onChosen: panel.personChosen(modelData.name)
            }
        }

        // -- üres állapot: az eredetinek ÖT külön szövege volt aszerint,
        // mit néz éppen a felhasználó (`peoplepanel_text.tre`) — üres
        // listát sosem hagyott. Hármat tudunk értelmezni a mai nézeteinkre:
        //
        //   3. „No people have been found yet…"     — nincs még találat
        //   4. „Named People who appear WITH…"      — személy albuma nyitva
        //   5. „People who appear in the currently
        //       selected photos will be listed here." — van kijelölés
        Text {
            objectName: "peoplePanelEmptyText"
            visible: panel.peopleHere.length === 0 && panel.peopleWith.length === 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: panel.currentPerson.length > 0
                  ? qsTr("Named people who appear with the currently "
                         + "selected person will be listed here.")
                  : panel.selectionCount > 0
                    ? qsTr("People who appear in the currently selected "
                           + "photos will be listed here.")
                    : qsTr("No people have been found yet. As faces are "
                           + "found and grouped, they will appear in the "
                           + "Unnamed album.")
            font.pixelSize: Theme.fontSize - 1
            font.italic: true
            color: Theme.textGray
        }

        Item { Layout.fillHeight: true }
    }
}

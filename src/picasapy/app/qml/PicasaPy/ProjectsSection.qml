import QtQuick
import QtQuick.Layouts

// A bal hasáb PROJEKTEK gyűjteménye (#1029): a Picasa saját projekt-mappái
// (Kollázsok, Filmek, Rögzített videoklipek, …) + az „Exportált képek"
// csomópont (#457).
//
// A projekt-mappákat a `.picasa.ini` `[Picasa]` `P2category=Projects
// (internal)` kulcsa jelöli ki — a `controller.projectFolders` ezt adja
// {path, name, count} elemekként. ⚠️ A `P2category` többi értéke (a
// korpuszban 456-szor `Folders on Disk`) NEM ide tartozik: azok a Mappák
// gyűjteményben maradnak.
//
// Miért külön fájl (#702/#757 mintája): a `FolderPane.qml` rég túlnőtte a
// 800 soros határt, ez a gyűjtemény pedig önálló, jól körülhatárolt egység
// — az `AlbumsSection.qml` kiemelésének mintáját követi. A szekció csak
// ADATOT kap és JELZÉST ad; controller-hivatkozás nincs benne.
ColumnLayout {
    id: section

    property bool collapsed: true
    // #1029: {path, name, count} elemek — a P2category-alapú projekt-mappák
    property var projectFolders: []
    // #457: {path, name} elemek — a felhasználó exportált célmappái
    property var exportedFolders: []
    // a kijelölés-kiemeléshez (a mappalista sorainak mintájára)
    property string selectedPath: ""
    property string selectedAlbumToken: ""
    // #730: a hasáb egységes sormagassága — egyetlen forrásból
    property int rowHeight: 22

    signal toggled()
    signal folderChosen(string path)
    signal folderContextMenuRequested(string path)

    spacing: 0

    // #757/3: album-nézetben a mappa-kijelölés szűnjön meg — enélkül album
    // megnyitásakor KÉT sor látszana egyszerre kijelöltnek (#9).
    function isSelected(path) {
        return section.selectedPath === path && section.selectedAlbumToken === ""
    }

    CollectionHeader {
        Layout.fillWidth: true
        label: qsTr("Projects")
        itemCount: section.projectFolders.length + section.exportedFolders.length
        labelObjectName: "projectsHeader"
        collapsed: section.collapsed
        onToggled: section.toggled()
    }

    // #1029: egy-egy sor projekt-mappánként, névvel és darabszámmal — az
    // eredetiben innen éri el a felhasználó a kész kollázsait.
    Repeater {
        id: projectFolderRepeater
        objectName: "projectFolderRepeater"
        model: section.projectFolders
        delegate: Rectangle {
            id: projectItem
            required property var modelData
            objectName: "projectFolderItem_" + modelData.name
            visible: !section.collapsed
            Layout.fillWidth: true
            Layout.preferredHeight: section.rowHeight
            readonly property bool isSelectedFolder:
                section.isSelected(projectItem.modelData.path)
            // #384: hover ≠ kijelölés — a hover a világosabb jelölő tónus
            color: projectItem.isSelectedFolder
                   ? Theme.panelSelectionActive
                   : (projectMouse.containsMouse ? Theme.panelSelection
                                                 : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                FolderIcon { anchors.verticalCenter: parent.verticalCenter }
                Text {
                    text: projectItem.modelData.name
                          + " (" + projectItem.modelData.count + ")"
                    font.pixelSize: Theme.fontSize
                    color: projectItem.isSelectedFolder
                           || projectMouse.containsMouse
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                id: projectMouse
                anchors.fill: parent
                hoverEnabled: true
                // #732: a projekt-mappa is MAPPA — a saját menüje jár neki
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: function(mouse) {
                    if (mouse.button === Qt.RightButton) {
                        section.folderContextMenuRequested(
                            projectItem.modelData.path)
                        return
                    }
                    section.folderChosen(projectItem.modelData.path)
                }
            }
        }
    }

    // #457: az „Exportált képek" az eredetiben is külön csomópont volt a
    // navigációban — az export így NYOMON KÖVETHETŐ maradt, nem tűnt el a
    // fájlrendszerben. A Projektek gyűjtemény alá kerül, mert ez a
    // felhasználó SAJÁT munkájának eredménye, nem beolvasott könyvtár.
    Text {
        objectName: "exportedPicturesLabel"
        visible: !section.collapsed && section.exportedFolders.length > 0
        Layout.fillWidth: true
        Layout.leftMargin: 12
        text: qsTr("Exported Pictures")
        font.pixelSize: Theme.fontSize - 1
        color: Theme.textGray
    }

    Repeater {
        id: exportedFolderRepeater
        objectName: "exportedFolderRepeater"
        model: section.exportedFolders
        delegate: Rectangle {
            id: exportedItem
            required property var modelData
            objectName: "exportedFolderItem_" + modelData.name
            visible: !section.collapsed
            Layout.fillWidth: true
            Layout.preferredHeight: section.rowHeight
            readonly property bool isSelectedFolder:
                section.isSelected(exportedItem.modelData.path)
            color: exportedItem.isSelectedFolder
                   ? Theme.panelSelectionActive
                   : (exportedMouse.containsMouse ? Theme.panelSelection
                                                  : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 20
                spacing: 5
                FolderIcon { anchors.verticalCenter: parent.verticalCenter }
                Text {
                    text: exportedItem.modelData.name
                    font.pixelSize: Theme.fontSize
                    color: exportedItem.isSelectedFolder
                           || exportedMouse.containsMouse
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                id: exportedMouse
                anchors.fill: parent
                hoverEnabled: true
                // #732: az exportált célmappa is MAPPA — a saját menüje jár
                // neki, nem a hasáb rendezés-menüje
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: function(mouse) {
                    if (mouse.button === Qt.RightButton) {
                        section.folderContextMenuRequested(
                            exportedItem.modelData.path)
                        return
                    }
                    section.folderChosen(exportedItem.modelData.path)
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Layouts

// A bal hasáb ALBUMOK gyűjteménye: fejléc + „Új album" súgó + a
// csillagozott sor + az albumok sorai (#9, #455).
//
// Miért külön fájl (#702/#757): a `FolderPane.qml` rég túlnőtte a 800 soros
// határt, ez a gyűjtemény pedig önálló, jól körülhatárolt egység — a
// `CollectionHeader.qml` kiemelésének mintáját követi. A hasáb csak ADATOT
// ad és JELZÉSEKET kap; controller-hivatkozás ebben a komponensben nincs.
//
// `ColumnLayout`, hogy a hasáb `ColumnLayout`-jába úgy illeszkedjen, ahogy
// a sorok eddig: `Layout.fillWidth` + `Layout.preferredHeight`, spacing 0.
ColumnLayout {
    id: section

    property bool collapsed: false
    // {token, name, count} elemek
    property var albumsModel: []
    property string selectedAlbumToken: ""
    property bool starredActive: false
    // #730: a hasáb egységes sormagassága — egyetlen forrásból
    property int rowHeight: 22

    signal toggled()
    signal starredChosen()
    signal albumChosen(string token)
    signal albumContextMenuRequested(string token, string name)
    // #455: fogd-és-vidd az albumlistára — új album, illetve meglévőbe
    // sorolás. A tényleges munkát a gazda végzi (a névkérő párbeszéd és a
    // kijelölés is ott van).
    signal newAlbumDropped()
    signal photosDroppedOnAlbum(string token)

    spacing: 0

    // Csak SAJÁT fotó-húzást fogadunk el: a külső fájlok ejtése az
    // ImportDropArea dolga (#146), azt nem szabad elorozni.
    function acceptsPhotoDrag(drop) {
        return !!drop && !!drop.source && drop.source.payload === "photos"
    }

    CollectionHeader {
        Layout.fillWidth: true
        label: qsTr("Albums")
        // #9: 1 a csillagozott sorért + az összes virtuális album
        itemCount: 1 + section.albumsModel.length
        labelObjectName: "albumsHeader"
        collapsed: section.collapsed
        onToggled: section.toggled()
    }

    // #455: „You can drag and drop pictures here to make a new album."
    // — az eredeti Picasa ÜRES albumlistáján ez a mondat állt.
    //
    // #757/1: nálunk korábban MINDIG látszott, és 230 képpontos hasábon 58
    // képpontot — 2,6 mappasornyi helyet — vett el a mappalistából. A
    // „lista sosem üres, ott a csillagozott sor" érvelés téves volt: a
    // csillagozott sor nem album, az albumLISTA nagyon is lehet üres. A
    // súgó most az eredeti feltételét követi.
    Text {
        objectName: "albumDropHintText"
        visible: !section.collapsed && section.albumsModel.length === 0
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 8
        wrapMode: Text.WordWrap
        text: qsTr("You can drag and drop pictures here to make a new album.")
        font.pixelSize: Theme.fontSize - 1
        font.italic: true
        color: albumDropArea.containsDrag ? Theme.picasaGreen : Theme.textGray
        topPadding: 4
        bottomPadding: 6

        DropArea {
            id: albumDropArea
            objectName: "albumDropArea"
            anchors.fill: parent
            onDropped: function(drop) {
                if (!section.acceptsPhotoDrag(drop)) return
                drop.accept()
                section.newAlbumDropped()
            }
        }
    }

    Rectangle {
        id: starredItem
        objectName: "starredItem"
        visible: !section.collapsed
        Layout.fillWidth: true
        Layout.preferredHeight: section.rowHeight
        // #384: hover ≠ kijelölés — a hover a korábbi jelölő tónust
        // kapja, a tényleges kijelölés a hitelesebb, sötétebb színt.
        color: section.starredActive ? Theme.panelSelectionActive
               : (starredMouse.containsMouse ? Theme.panelSelection : "transparent")
        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left; anchors.leftMargin: 16
            spacing: 5
            Text { text: "★"; color: Theme.starYellow; font.pixelSize: Theme.fontSize }
            Text {
                text: qsTr("Starred photos")
                font.pixelSize: Theme.fontSize
                color: section.starredActive || starredMouse.containsMouse
                       ? Theme.panelSelectionText : Theme.textDark
            }
        }
        MouseArea {
            id: starredMouse
            anchors.fill: parent
            hoverEnabled: true
            onClicked: section.starredChosen()
        }
    }

    // #9: a virtuális albumok a csillagozott sor ALATT, ugyanabban az
    // Albumok gyűjteményben — mindegyik album név + darabszám sor.
    Repeater {
        id: albumRepeater
        objectName: "albumRepeater"
        model: section.albumsModel
        delegate: Rectangle {
            id: albumItem
            required property var modelData
            objectName: "albumItem_" + modelData.token
            readonly property bool isSelectedAlbum:
                section.selectedAlbumToken === modelData.token
            visible: !section.collapsed
            Layout.fillWidth: true
            Layout.preferredHeight: section.rowHeight
            // #384: hover ≠ kijelölés (ld. starredItem fent)
            color: albumItem.isSelectedAlbum ? Theme.panelSelectionActive
                   : (albumMouse.containsMouse ? Theme.panelSelection : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                Rectangle {
                    width: 10; height: 8
                    radius: 1
                    anchors.verticalCenter: parent.verticalCenter
                    color: Theme.picasaGreen
                }
                Text {
                    text: modelData.name + " (" + modelData.count + ")"
                    font.pixelSize: Theme.fontSize
                    color: albumItem.isSelectedAlbum || albumMouse.containsMouse
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            // #455: meglévő album sorára ejtve a képek ABBA az albumba
            // kerülnek (a „drag pictures here" a listán ÚJ albumot
            // csinál — a kettő nem ugyanaz)
            DropArea {
                objectName: "albumDropArea_" + albumItem.modelData.token
                anchors.fill: parent
                onDropped: function(drop) {
                    if (!section.acceptsPhotoDrag(drop)) return
                    drop.accept()
                    section.photosDroppedOnAlbum(albumItem.modelData.token)
                }
            }
            MouseArea {
                id: albumMouse
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: function(mouse) {
                    // #422: jobbklikk = az album menüje; bal = megnyitás
                    if (mouse.button === Qt.RightButton) {
                        section.albumContextMenuRequested(
                            albumItem.modelData.token,
                            albumItem.modelData.name)
                        return
                    }
                    section.albumChosen(albumItem.modelData.token)
                }
            }
        }
    }
}

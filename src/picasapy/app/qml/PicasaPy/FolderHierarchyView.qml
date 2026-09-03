import QtQuick
import QtQuick.Controls

// A bal panel HIERARCHIKUS (fa) mappanézete — #702.
//
// Az eredeti Picasa bal hasábjának KÉT, egymást kizáró nézetmódja van
// (`thumbui/hviewtoggle`): a lapos lista (`thumbui/flatview`,
// `eMenuView::ID_VIEW_FOLDERS` = „Flat Folder View") és ez a fa
// (`thumbui/folderview`, `eMenuView::ID_VIEW_ALL` = „Tree View").
// Bizonyíték és teljes tételsor: `docs/specs/ui-audit-mainwindow.md` 1.4/1.7.
//
// Ez a komponens KIZÁRÓLAG a fát rajzolja: a nézetmód-váltó gomb és a
// bekötés a `FolderPane`/`Main.qml` dolga (forró fájlok, ld. CONTRIBUTING.md).
//
// A sorokat a `FolderHierarchyController` (Python) adja már kilapítva —
// a csukott ágak gyermekei EL SEM JUTNAK ide. Ez szándékos: a `visible`
// öröklődik, így egy „elrejtett, de létező" gyermeksor néma hibaforrás
// lenne (a teszt is ezért a kirajzolt sorokat nézi, nem property-ket).
//
// NEM a `FolderTreeItem.qml` újrahasznosítása: az a Mappakezelő dialógus
// LUSTÁN, a fájlrendszerből töltő, rekurzív komponense (#231), és a
// dialógus `manager` objektumához kötött. Itt az INDEXELT mappák fája
// kell, részfa-összegzett darabszámmal — más adat, más életciklus.
Item {
    id: root

    // A `FolderHierarchyController` példánya (Python-oldali adatforrás).
    property var hierarchy: null
    // Az éppen kiválasztott mappa útvonala (a kiemeléshez).
    property string selectedPath: ""
    // constants.ui `alist_indent` = 17 — a fa behúzása szintenként
    readonly property int indentStep: 17
    // A gazda hasáb egységes sormagassága (#730) — a hasáb ebből számolja a
    // komponens magasságát is, ezért felülírhatónak kell lennie.
    property int rowHeight: 22

    // #2049: „Indexképek megjelenítése a könyvtárban" — a fasorok fotó-kupac
    // borítója. A `!== undefined` a próbák stub-vezérlőjére véd (#1572).
    property bool albumThumbs:
        (root.hierarchy && root.hierarchy.albumThumbs !== undefined)
            ? root.hierarchy.albumThumbs : false

    signal folderChosen(string path)
    // A `HierFolder` menüosztály három olyan tétele, aminek a rétege a
    // gazdában van (`FUN_00733a40`): a komponens csak jelez, nem cselekszik.
    signal locateOnDiskRequested(string path)
    signal removeFromPicasaRequested(string path)
    signal moveFolderRequested(string path)

    // -- kifelé hívható parancsok ----------------------------------------

    function choose(path) {
        if (!path) return          // a virtuális gyökérsor nem mappa
        root.selectedPath = path
        root.folderChosen(path)
    }

    function toggle(path) {
        if (root.hierarchy) root.hierarchy.toggle(path)
    }

    // `Folder::ID_HIER_FOLDER_EXPAND` — „Expand All"
    function expandAll() {
        if (root.hierarchy) root.hierarchy.expandAll()
    }

    // `Folder::ID_HIER_FOLDER_COLLAPSE` — „Collapse All"
    function collapseAll() {
        if (root.hierarchy) root.hierarchy.collapseAll()
    }

    // A sor jobbklikk-menüje. A delegátumból kiszervezve, névvel hívható
    // függvényként — a `Repeater`/`ListView` delegáltjait a `findChild`
    // nem találja meg, így csak így tesztelhető közvetlenül.
    function openContextMenu(path) {
        contextMenu.folderPath = path
        contextMenu.popup()
    }

    ListView {
        id: list
        objectName: "folderHierarchyList"
        anchors.fill: parent
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        // #730/#702: a bal hasáb EGYETLEN görgetője a gazda `Flickable`-je.
        // A gazda a teljes tartalommagasságot adja ennek a komponensnek,
        // tehát itt nincs mit görgetni — ha viszont a lista `interactive`
        // maradna, elnyelné a görgő-eseményt, és a hasáb nem mozdulna.
        interactive: false
        // #305 null-őr: a vezérlő bekötése előtt is érvényes modell kell
        model: root.hierarchy ? root.hierarchy.rows : []

        delegate: Rectangle {
            id: row
            required property var modelData
            objectName: "hierRow:" + row.modelData.path
            width: list.width
            height: root.rowHeight

            readonly property bool isRoot: row.modelData.kind === "root"
            readonly property bool isSelected:
                !row.isRoot && root.selectedPath === row.modelData.path

            color: row.isSelected ? Theme.panelSelectionActive
                   : (rowMouse.containsMouse ? Theme.selectionBlue : "transparent")

            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 6 + row.modelData.depth * root.indentStep
                spacing: 4

                Text {
                    objectName: "hierArrow:" + row.modelData.path
                    width: 12
                    text: row.modelData.hasChildren
                          ? (row.modelData.expanded ? "▾" : "▸") : ""
                    font.pixelSize: Theme.fontSize - 2
                    color: row.isSelected ? Theme.panelSelectionText
                                          : Theme.folderArrow
                    MouseArea {
                        objectName: "hierArrowMouse:" + row.modelData.path
                        anchors.fill: parent
                        enabled: row.modelData.hasChildren
                        onClicked: root.toggle(row.modelData.path)
                    }
                }

                // #2049: az eredeti a fasorokon nem sárga mappaikont mutat,
                // hanem a mappa első legfeljebb négy fotójából
                // összeállított kis kupacot — de CSAK ha az „Indexképek
                // megjelenítése a könyvtárban" be van kapcsolva
                // (`ShowAlbumThumbnails2`, alapérték 0). Ha nincs borító
                // (kép nélküli mappa), a sor a mappaikonjára esik vissza:
                // az eredeti is helyettesítő ikonokat sorol fel erre az
                // esetre (`0x00761870`: `icons/folder`, `icons/album`, …).
                Item {
                    objectName: "hierFolderCover:" + row.modelData.path
                    visible: !row.isRoot
                    // #2215: a hely a KUPAC arányához igazodik. A 13
                    // képpont a mappaikon mérete; a kupac ennél szélesebb
                    // lehet — mérve 78×62, 84×77, 80×73 (a #2049 kommentje
                    // fordítva tudta: „magasabb, mint széles"). Fix 13-mal
                    // a mappanév ráfolyt volna a kupacra.
                    width: boritoLatszik && borito.implicitHeight > 0
                        ? Math.max(13, Math.ceil(
                            height * borito.implicitWidth / borito.implicitHeight))
                        : 13
                    height: root.rowHeight - 4
                    anchors.verticalCenter: parent.verticalCenter

                    // #2215: a `Ready` ÖNMAGÁBAN nem elég. A szolgáltató
                    // korábban 1×1 átlátszó képet adott, ha nincs borító —
                    // az sikeresen betöltődik, tehát ez a feltétel igaz
                    // lett, és a mappaikon elrejtőzött: a sor üresen
                    // maradt. A szolgáltató ma null képet ad (`Error`), a
                    // méret-ellenőrzés pedig második védelem arra az
                    // esetre, ha valaki visszahozná a helyettesítő képet.
                    readonly property bool boritoLatszik:
                        root.albumThumbs
                        && borito.status === Image.Ready
                        && borito.implicitWidth > 1

                    FolderIcon {
                        objectName: "hierFolderIcon:" + row.modelData.path
                        size: 13
                        visible: !parent.boritoLatszik
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Image {
                        id: borito
                        objectName: "hierFolderCoverImage:" + row.modelData.path
                        anchors.centerIn: parent
                        // A kupac magasabb, mint széles; a fasor magassága
                        // szabja meg, a szélessége ehhez igazodik.
                        height: parent.height
                        fillMode: Image.PreserveAspectFit
                        visible: parent.boritoLatszik
                        asynchronous: true
                        // ⚠️ Üres forrással a `status` `Null` marad, tehát a
                        // kikapcsolt állapotban NEM készül borító: a
                        // szolgáltató meg sem szólal.
                        source: root.albumThumbs
                                ? "image://foldercover/" + row.modelData.path
                                : ""
                    }
                }

                Text {
                    // A nézet-gyökér felirata `ViewRoot::All` = „My Computer"
                    // (magyarul „Sajátgép") — nem valódi mappa neve, ezért
                    // itt, a felületi rétegben él.
                    text: row.isRoot ? qsTr("My Computer") : row.modelData.name
                    font.pixelSize: Theme.fontSize
                    font.bold: row.isRoot
                    color: row.isSelected ? Theme.panelSelectionText : Theme.ink
                }

                Text {
                    // A fában a darabszám a RÉSZFA összes fotója
                    // (ui-audit 1.4: `Sajátgép (1 072)` = 227 + 842 + 3)
                    objectName: "hierCount:" + row.modelData.path
                    text: "(" + row.modelData.count + ")"
                    font.pixelSize: Theme.fontSize
                    color: row.isSelected ? Theme.panelSelectionText
                                          : Theme.folderDate
                }
            }

            MouseArea {
                id: rowMouse
                objectName: "hierRowMouse:" + row.modelData.path
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: function (mouse) {
                    if (mouse.button === Qt.RightButton) {
                        if (!row.isRoot) root.openContextMenu(row.modelData.path)
                        return
                    }
                    if (row.isRoot) root.toggle(row.modelData.path)
                    else root.choose(row.modelData.path)
                }
                onDoubleClicked: root.toggle(row.modelData.path)
            }
        }
    }

    // A `HierFolder` menüosztály — a fa KÖZTES csomópontjának menüje.
    // Öt tétel, a `FUN_00733a40` felépítő rutinból kiolvasva (a teljes
    // mappa-menü ennél jóval bővebb, ld. `FolderContextMenu.qml`).
    PicasaMenu {
        id: contextMenu
        objectName: "hierFolderContextMenu"
        property string folderPath: ""

        MenuItem {
            objectName: "hierMenuExpandAll"
            text: qsTr("Expand All")           // Folder::ID_HIER_FOLDER_EXPAND
            onTriggered: root.expandAll()
        }
        MenuItem {
            objectName: "hierMenuCollapseAll"
            text: qsTr("Collapse All")         // Folder::ID_HIER_FOLDER_COLLAPSE
            onTriggered: root.collapseAll()
        }
        MenuSeparator {}
        MenuItem {
            objectName: "hierMenuLocateOnDisk"
            text: qsTr("Locate on Disk")       // FolderWin::ID_ALBUM_LOCATEONDISK
            onTriggered: root.locateOnDiskRequested(contextMenu.folderPath)
        }
        MenuItem {
            objectName: "hierMenuRemoveFromPicasa"
            text: qsTr("Remove from Picasa...")  // Folder::ID_MANAGE_ALBUM
            onTriggered: root.removeFromPicasaRequested(contextMenu.folderPath)
        }
        MenuItem {
            objectName: "hierMenuMoveFolder"
            text: qsTr("Move Folder...")       // HierFolder::ID_MOVEHIERFOLDER
            onTriggered: root.moveFolderRequested(contextMenu.folderPath)
        }
    }
}

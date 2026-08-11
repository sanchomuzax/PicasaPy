import QtQuick

// Egyetlen mappasor a Mappakezelő fájában (#231) — rekurzív komponens:
// saját maga rajzolja a kinyitó-nyilat + nevet + állapot-ikont, alatta
// pedig (kinyitáskor) a saját gyermekeit, ugyanezzel a komponenssel.
//
// LUSTA betöltés: a gyermek-lista csak az ELSŐ kinyitáskor kerül
// lekérésre a folderTreeController-től (háttérszálon fut, ld.
// folder_tree_controller.py) — a fájlrendszer-olvasás NEM a GUI-szálon
// történik. Az eredmény a globális `childrenLoaded` jelzésen érkezik; ezt
// a sor a saját útvonalára szűrve fogadja (Connections + path-egyezés),
// nem igényel semmilyen szülő-oldali nyilvántartást.
Column {
    id: root
    // útvonal szerint kereshető azonosító (tesztekhez, ld.
    // tests/app/test_qml_folder_manager.py) — a mappák útvonala egyedi,
    // így az objectName is az
    objectName: "folderTreeItem:" + root.path
    property string path: ""
    property string name: ""
    property bool hasChildren: false
    property int depth: 0
    property var manager   // a FolderManagerDialog (kijelölés + állapot)

    property bool expanded: false
    property bool loaded: false
    property var childItems: []

    // #384: constants.ui alist_selcolor_win (#25648B) — a VALÓDI
    // kijelölés a hover/jelölő tónusnál (Theme.selectionBlue = #83a7bd,
    // alist_hicolor_win) sötétebb. A Theme.qml-ben MÉG NINCS erre saját
    // token (hot file, ld. jelentés: Theme.panelSelectionActive) — amíg
    // az integrátor fel nem veszi, itt helyi állandóként él; a csere csak
    // ezt a sort érinti.
    readonly property bool isSelected: root.manager
                                        && root.manager.selectedPath === root.path

    Rectangle {
        id: rowRect
        objectName: "folderTreeRow:" + root.path
        width: root.width
        height: 22
        // hover ≠ kijelölés (#384): a hover a korábbi (jelölő) tónust
        // kapja, a tényleges kijelölés a sötétebb, hiteles színt.
        color: root.isSelected ? Theme.panelSelectionActive
               : (rowMouse.containsMouse ? Theme.selectionBlue : "transparent")

        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            // constants.ui alist_indent = 17 (fa-behúzás szintenként)
            anchors.leftMargin: 6 + root.depth * 17
            spacing: 4

            Text {
                width: 12
                text: root.hasChildren ? (root.expanded ? "▾" : "▸") : ""
                font.pixelSize: Theme.fontSize - 2
                color: root.isSelected ? "#ffffff" : Theme.folderArrow
                MouseArea {
                    anchors.fill: parent
                    enabled: root.hasChildren
                    onClicked: root.toggleExpand()
                }
            }

            FolderIcon { size: 13; anchors.verticalCenter: parent.verticalCenter }

            Text {
                text: root.name
                font.pixelSize: Theme.fontSize
                color: root.isSelected ? "#ffffff" : Theme.ink
            }

            // #543: az eredeti `foldermgr.tre` KÉP-ikonokat használ
            // (`icon_once`/`icon_always`), és külön, átfedő jelvényt az
            // arcfelismerés kikapcsolt állapotára (`nofr_on`/`nofr_off`) —
            // a korábbi egyetlen szöveges karakter helyett.
            FolderStateBadge {
                objectName: "folderTreeGlyph:" + root.path
                anchors.verticalCenter: parent.verticalCenter
                folderState: root.manager ? root.manager.stateFor(root.path) : "none"
                faceExcluded: root.manager
                              ? root.manager.facesExcludedFor(root.path) : false
                tint: root.isSelected ? "#ffffff" : Theme.selectionBlue
            }
        }

        MouseArea {
            id: rowMouse
            objectName: "folderTreeRowMouse:" + root.path
            anchors.fill: parent
            hoverEnabled: true
            onClicked: if (root.manager) root.manager.selectedPath = root.path
        }
    }

    // A gyerek-sorok is FolderTreeItem-ek — mivel EZ a fájl maga a
    // FolderTreeItem definíciója, a típus közvetlen név szerinti
    // hivatkozása önmagára a QML-fordító "recursively instantiated"
    // hibáját váltaná ki. A Loader.source URL-alapú, futásidejű
    // betöltése ezt megkerüli (a fájl önmagát tölti be, típusnév-
    // feloldás nélkül) — ez a szokásos minta rekurzív QML-fákhoz.
    Column {
        id: childColumn
        width: root.width
        visible: root.expanded

        Repeater {
            model: root.expanded ? root.childItems : []
            delegate: Loader {
                id: childLoader
                required property var modelData
                width: childColumn.width
                source: Qt.resolvedUrl("FolderTreeItem.qml")
                onLoaded: {
                    item.path = childLoader.modelData.path
                    item.name = childLoader.modelData.name
                    item.hasChildren = childLoader.modelData.hasChildren
                    item.depth = root.depth + 1
                    item.manager = root.manager
                }
            }
        }
    }

    Connections {
        target: typeof folderTreeController !== "undefined"
                ? folderTreeController : null
        function onChildrenLoaded(loadedPath, children) {
            if (loadedPath === root.path) root.childItems = children
        }
    }

    function toggleExpand() {
        if (!root.hasChildren) return
        root.expanded = !root.expanded
        if (root.expanded && !root.loaded) {
            root.loaded = true
            if (typeof folderTreeController !== "undefined")
                folderTreeController.requestChildren(root.path)
        }
    }
}

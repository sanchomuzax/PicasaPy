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
    property bool draggingFolder: false
    property bool didDragFolder: false
    property string draggedFolderPath: ""

    // #3681: a mentés-üzemmód szűrő-módja — a `FolderPane` közös
    // szerződése (ld. `FolderPane.qml`). Aktív módban a fa a MÉG EL NEM
    // MENTETT mappákra szűkül, pipával. Az őseik pipa nélkül megmaradnak,
    // és az őket tartalmazó ágak kinyitva látszanak — a felhasználó
    // csukott ága sem rejthet el mentendő mappát (`mentesSorok`).
    property bool mentesSzuroAktiv: false
    //: {mappa, nev, darab, fajlok, bajt} sorok — ld. `FolderPane.qml`
    property var mentesMentetlenMappak: []
    //: a bepipált mappák útjai
    property var mentesPipaltMappak: []
    signal mentesPipaldKert(string mappa, bool be)

    readonly property var _mentesUtak:
        root.mentesMentetlenMappak.map(function (sor) { return sor.mappa })
    //: útvonal → a mentetlen mappa sora (darab, fájlnevek)
    readonly property var _mentesTerkep: {
        var terkep = {}
        root.mentesMentetlenMappak.forEach(function (sor) { terkep[sor.mappa] = sor })
        return terkep
    }
    readonly property var _sorok: root.hierarchy ? root.hierarchy.rows : []
    //: a TÉNYLEGESEN kirajzolt sorok — szűrő módban a mentetlen mappák az
    //: őseikkel, egyébként a teljes (nyitott ágak szerinti) fa
    readonly property var _lathatoSorok: {
        //: a fa változására (új mappa, nézetváltás) is frissüljön
        var teljes = root._sorok
        if (!root.mentesSzuroAktiv || !root.hierarchy) return teljes
        return root.hierarchy.mentesSorok(root._mentesUtak)
    }
    //: a gazda (`FolderPane`) ebből számolja a komponens magasságát —
    //: szűrő módban ez KEVESEBB, mint `hierarchy.rows.length`
    readonly property alias rowCount: list.count

    signal folderChosen(string path)
    signal folderDroppedOnFolder(string sourcePath, string targetPath)
    // A képes mappák a FolderPane teljes mappa-menüjét használják; az
    // indexen kívüli, saját képet nem tartalmazó köztes sorok maradnak a
    // HierFolder rövid menüjénél.
    signal folderContextMenuRequested(string path)
    // A `HierFolder` menüosztály három olyan tétele, aminek a rétege a
    // gazdában van (`FUN_00733a40`): a komponens csak jelez, nem cselekszik.
    signal locateOnDiskRequested(string path)
    signal removeFromPicasaRequested(string path)
    signal moveFolderRequested(string path)

    // A forrás nem a virtualizált ListView-sor: a QQuickListView újrahasznosíthatja
    // a delegátumot, miközben a mutató áthalad a fán. Ez az állandó proxy
    // viszi a mappa payloadját a DropArea-ig.
    Item {
        id: folderDragProxy
        objectName: "folderTreeDragProxy"
        x: 0
        y: 0
        width: 1
        height: 1
        visible: root.draggingFolder
        readonly property string payload: "folders"
        readonly property string folderPath: root.draggedFolderPath
        Drag.active: root.draggingFolder
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.hotSpot.x: 0
        Drag.hotSpot.y: 0
    }

    // -- kifelé hívható parancsok ----------------------------------------

    function choose(path) {
        if (!path) return          // a virtuális gyökérsor nem mappa
        root.selectedPath = path
        root.folderChosen(path)
    }

    function toggle(path) {
        //: #3681: szűrő módban a fa alakját a mentetlen mappák adják —
        //: a nyitás/csukás itt nem látszana, csak a rejtett állapotot írná
        if (root.mentesSzuroAktiv) return
        if (root.hierarchy) root.hierarchy.toggle(path)
    }

    //: #3681: a mentetlen mappa fájlnevei a sor végén (ami elfér) — a
    //: `FolderPane.mentesFajlSor` párja
    function mentesFajlSor(path) {
        var sor = root._mentesTerkep[path]
        if (!sor) return ""
        return sor.fajlok.join(", ")
            + (sor.darab > sor.fajlok.length ? ", …" : "")
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
        // #305 null-őr: a vezérlő bekötése előtt is érvényes modell kell.
        // #3681: mentés-szűrő módban a SZŰKÍTETT lista.
        model: root._lathatoSorok

        delegate: Rectangle {
            id: row
            required property var modelData
            objectName: "hierRow:" + row.modelData.path
            width: list.width
            height: root.rowHeight

            readonly property bool isRoot: row.modelData.kind === "root"
            //: #3681: a mentetlen mappa útja a MENTÉS-oldal alakjában — a
            //: `path` a fa alakja (Windowson a köztes szint perjeles), a
            //: mentetlen mappák listája és a pipák ezzel az úttal élnek
            readonly property string mentesUt: row.modelData.mentesUt || ""
            readonly property bool isSelected:
                !row.isRoot && root.selectedPath === row.modelData.path
            //: #3681: szűrő módban csak a mentetlen mappa pipálható — az
            //: ősei és a gyökér nem
            readonly property bool mentesJelolt:
                root.mentesSzuroAktiv && row.mentesUt !== ""
                && root._mentesTerkep[row.mentesUt] !== undefined
            color: row.isSelected ? Theme.panelSelectionActive
                   : (rowMouse.containsMouse ? Theme.selectionBlue : "transparent")

            // #3681: a mentés-szűrő pipája — a sor BAL szélén, egy
            // oszlopban (a lapos lista mintájára), hogy a fa behúzása ne
            // tolja a mappanevet még beljebb. A kattintást a teljes sort
            // lefedő `rowMouse` kezeli (lentebb), a pipa csak TÜKRÖZI az
            // állapotot.
            CheckBox {
                objectName: "hierMentesCheck:" + row.modelData.path
                visible: row.mentesJelolt
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 2
                topPadding: 0
                bottomPadding: 0
                checked: row.mentesUt !== ""
                         && root.mentesPipaltMappak.indexOf(row.mentesUt) >= 0
            }

            Row {
                id: sorTartalom
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                //: szűrő módban a pipák oszlopa előtte áll (a lapos lista
                //: 12 → 34 eltolásával azonos)
                anchors.leftMargin: (root.mentesSzuroAktiv ? 28 : 6)
                                    + row.modelData.depth * root.indentStep
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
                        enabled: row.modelData.hasChildren && !root.mentesSzuroAktiv
                        onClicked: root.toggle(row.modelData.path)
                    }
                }

                // #2049/#2989: az eredeti a fasorokon nem sárga
                // mappaikont mutat, hanem a mappa ELSŐ fotójának kis
                // bélyegképét.
                //
                // ⚠️ #2989: a fában ez NEM a kapcsolótól függ. A tulajdonos
                // 3. felvételén (`research/#2984-indexkepek-mappa-ikonokon/`)
                // a menütétel SZÜRKE, a bélyegképek mégis ott vannak —
                // tehát a `ShowAlbumThumbnails2` kizárólag az egydimenziós
                // listára vonatkozik (`FolderPane.qml`). Ha nincs borító
                // (kép nélküli mappa), a sor a mappaikonjára esik vissza:
                // az eredeti is helyettesítő ikonokat sorol fel erre az
                // esetre (`0x00761870`: `icons/folder`, `icons/album`, …).
                Item {
                    objectName: "hierFolderCover:" + row.modelData.path
                    visible: !row.isRoot
                    // #2989: a hely FIX, a mért 17 × 15 arányában — a kép
                    // aránytartón fér bele. Az eredetin minden sor ikonja
                    // ugyanabban a dobozban ül (a szélesebb képernyőkép
                    // 17 × 12 lett, nem 21 × 15), tehát a nevek EGY
                    // vonalban kezdődnek.
                    readonly property int ikonDoboz: Math.round(height * 17 / 15)
                    width: boritoLatszik ? ikonDoboz : 13
                    height: root.rowHeight - 4
                    anchors.verticalCenter: parent.verticalCenter

                    // #2215/#4876: a `Ready` ÖNMAGÁBAN nem elég. A
                    // szolgáltató borító nélkül SZÁNDÉKOSAN 1×1 átlátszó,
                    // érvényes jelölőt ad (null képre a Qt minden kérésnél
                    // hibasort írna) — az sikeresen betöltődik, ezért a
                    // méretfeltétel (`implicitWidth > 1`) az ELSŐDLEGES
                    // védelem: enélkül a mappaikon elrejtőzne, és a sor
                    // üresen maradna.
                    readonly property bool boritoLatszik:
                        borito.status === Image.Ready
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
                        // #2989: a kép a doboz MINDKÉT méretébe belefér,
                        // aránytartón — a fekvő kép alacsonyabb lesz.
                        width: parent.ikonDoboz
                        height: parent.height
                        fillMode: Image.PreserveAspectFit
                        visible: parent.boritoLatszik
                        asynchronous: true
                        // ⚠️ Üres forrással a `status` `Null` marad, tehát
                        // útvonal nélküli sorra NEM készül kép: a
                        // szolgáltató meg sem szólal.
                        //
                        // #2983: a SAJÁT fotószám is feltétel. A szintetikus
                        // köztes szintek (`C:`, `C:/Users`, a hálózati
                        // gazdanév, és a virtuális gyökér) `own = 0`-sak —
                        // nincs mit kupacba rakni, a kérés viszont minden
                        // ilyen sorra egy „Failed to get image from provider"
                        // naplósort írt a felhasználó konzoljára. A
                        // `count` erre NEM jó: az a RÉSZFA összege, tehát egy
                        // fotó nélküli köztes szinten is pozitív.
                        source: (row.modelData.path !== ""
                                 && row.modelData.own > 0)
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
                    //: #3681: szűrő módban a még el nem mentett fájlok
                    //: száma, és csak a mentetlen mappa során — az ős
                    //: részfa-összege ott félrevezető volna
                    visible: !root.mentesSzuroAktiv || row.mentesJelolt
                    text: "(" + (row.mentesJelolt
                        ? root._mentesTerkep[row.mentesUt].darab
                        : row.modelData.count) + ")"
                    font.pixelSize: Theme.fontSize
                    color: row.isSelected ? Theme.panelSelectionText
                                          : Theme.folderDate
                }
            }

            //: #3681: a mentetlen mappa fájlnevei — ami elfér
            Text {
                objectName: "hierMentesFiles:" + row.modelData.path
                visible: row.mentesJelolt
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: sorTartalom.right
                anchors.leftMargin: 6
                anchors.right: parent.right
                anchors.rightMargin: 6
                elide: Text.ElideRight
                text: row.mentesJelolt ? root.mentesFajlSor(row.mentesUt) : ""
                font.pixelSize: Theme.fontSize - 1
                color: row.isSelected ? Theme.panelSelectionText : Theme.folderDate
            }

            MouseArea {
                id: rowMouse
                objectName: "hierRowMouse:" + row.modelData.path
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: function (mouse) {
                    if (mouse.button === Qt.RightButton) {
                        if (!row.isRoot) {
                            if (row.modelData.own > 0)
                                root.folderContextMenuRequested(
                                    row.modelData.path)
                            else
                                root.openContextMenu(row.modelData.path)
                        }
                        return
                    }
                    if (root.didDragFolder) {
                        root.didDragFolder = false
                        return
                    }
                    // #3681: mentés-szűrő módban a mentetlen sor egy pipa —
                    // a kattintás jelöl/jelöletlenít, nem nyit meg; az ős
                    // és a gyökér sora nem csinál semmit
                    if (root.mentesSzuroAktiv) {
                        if (row.mentesJelolt)
                            root.mentesPipaldKert(
                                row.mentesUt,
                                root.mentesPipaltMappak.indexOf(row.mentesUt) < 0)
                        return
                    }
                    if (row.isRoot) { root.toggle(row.modelData.path); return }
                    root.choose(row.modelData.path)
                }
                onDoubleClicked: root.toggle(row.modelData.path)
            }

            DropArea {
                objectName: "hierFolderDropArea:" + row.modelData.path
                anchors.fill: parent
                enabled: !row.isRoot && !root.mentesSzuroAktiv
                onDropped: function(drop) {
                    var source = drop.source
                    if (!source || source.payload !== "folders"
                            || !source.folderPath
                            || source.folderPath === row.modelData.path)
                        return
                    drop.accept()
                    root.folderDroppedOnFolder(
                        source.folderPath, row.modelData.path)
                }
            }
        }

        DragHandler {
            id: folderDragHandler
            target: null
            onActiveChanged: {
                if (active) {
                    var index = list.indexAt(
                        centroid.pressPosition.x, centroid.pressPosition.y)
                    var source = index >= 0 ? root._lathatoSorok[index] : null
                    if (!source || source.kind !== "folder"
                            || root.mentesSzuroAktiv)
                        return
                    root.draggedFolderPath = String(source.path || "")
                    if (root.draggedFolderPath.length === 0) return
                    root.didDragFolder = false
                    root.draggingFolder = true
                } else {
                    var wasDragging = root.draggingFolder
                    if (wasDragging) folderDragProxy.Drag.drop()
                    root.draggingFolder = false
                    root.draggedFolderPath = ""
                    root.didDragFolder = wasDragging
                    if (wasDragging)
                        Qt.callLater(function() { root.didDragFolder = false })
                }
            }
            onTranslationChanged: {
                var point = list.mapToItem(
                    root, centroid.position.x, centroid.position.y)
                folderDragProxy.x = point.x
                folderDragProxy.y = point.y
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

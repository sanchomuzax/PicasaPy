import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

// Bal oldali gyűjtemény-hasáb — Picasa "Folder List" gyökere (#320): öt
// önálló, csukható gyűjtemény (Albumok/Emberek/Projektek/Mappák/Egyéb),
// mindegyik saját fejléccel; csak a Mappák gyűjtemény tagolt évszám-
// szakaszokra (ld. docs/specs/ui-audit-mainwindow.md, mappafa szakasz).
Rectangle {
    id: pane
    color: Theme.panelBg

    // #384: constants.ui alist_selcolor_win/alist_scatcolor (#25648B) —
    // a VALÓDI kijelölés sötétebb, mint a hover/jelölő tónus
    // (Theme.panelSelection = #83a7bd, alist_hicolor_win). A Theme.qml-ben
    // MÉG NINCS erre saját token (hot file, ld. jelentés:
    // Theme.panelSelectionActive) — amíg az integrátor fel nem veszi, itt
    // helyi állandóként él; a csere csak ezt a sort érinti.

    property alias foldersModel: folderList.model
    property string selectedPath: ""
    property bool starredActive: false
    property bool searchActive: false
    property string searchQuery: ""
    property int searchResultCount: 0
    // #9: az albumok listája ({token, name, count} elemek) és az éppen
    // kiválasztott album token-je (a kijelölés-kiemeléshez)
    property var albumsModel: []
    property string selectedAlbumToken: ""
    // #320: a felhasználó egyéni gyűjteményei ({name, folders} elemek) —
    // a controller.customCollections tükre, a mappasor jobbklikk-menüjéhez
    property var customCollectionsModel: []
    // #26: a bal hasáb Emberek gyűjteménye ({name, count} elemek) és az
    // éppen kiválasztott személy neve (a kijelölés-kiemeléshez) — az
    // albumsModel/selectedAlbumToken mintáját követi.
    property var peopleModel: []
    property string selectedPersonName: ""
    // #26 (3. lépcső): a SAJÁT arcfelismerés „Névtelenek" sora — a
    // People-gyűjteményben él (a Picasa is a személyek mellett mutatta),
    // csak akkor látszik, ha van legalább egy szkennelt, még névtelen arc
    // (modell nélkül ez a szám mindig 0 — a sor eleve rejtve marad).
    property int unnamedFaceCount: 0
    // #449: a háttérben futó arc-beolvasás haladása (−1 = nem fut). Az
    // eredeti Picasa ezt AZ ALBUMLISTÁBAN mutatta, nem modális ablakban —
    // a felhasználót semmi nem blokkolta közben.
    property int faceScanPercent: -1
    property bool unnamedFacesActive: false
    // #26: a „Mellőzött emberek" album (`CAlbumLabel::Ignored`) — az
    // eredetiben is ALBUM volt, tehát látszania kell, ha van tartalma
    property int ignoredFaceCount: 0
    // #457: „Exportált képek" — `[{path, name}]`, az exportált célmappák
    property var exportedFolders: []
    // #1029: a Projektek gyűjtemény mappái — `[{path, name, count}]`, a
    // `.picasa.ini` `[Picasa]` `P2category=Projects (internal)` kulcsából
    // (Kollázsok, Filmek, Rögzített videoklipek, …)
    property var projectFolders: []
    property bool ignoredFacesActive: false
    // #730: a hasáb egységes sormagassága. A mappalista magasságát ebből és
    // a sordarabszámból számoljuk (a lista a görgethető hasábban a teljes
    // tartalmát kirakja), ezért nem maradhat a delegate-be égetett szám.
    readonly property int rowHeight: 22
    // #702: a Mappák gyűjtemény MÁSODIK nézetmódja — a hierarchikus fa. Az
    // eredeti Picasa bal hasábjának két, egymást kizáró módja van
    // (`thumbui/hviewtoggle`): a lapos lista (`eMenuView::ID_VIEW_FOLDERS`)
    // és a fa (`eMenuView::ID_VIEW_ALL`) — ld. ui-audit-mainwindow.md 1.4/1.7.
    // A `hierarchyController` a `FolderHierarchyController` példánya (a
    // gazda köti be). #1454: a nézetmód is ONNAN jön — a `Nézet ▸
    // Mappanézet` „Egyszerű mappanézet"/„Fanézet" tételpárja azt állítja.
    // A kötés felülírható (a hasábot önmagában rajzoló próbák élnek vele),
    // vezérlő nélkül pedig a lapos lista az alapállapot.
    property var hierarchyController: null
    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
    property bool treeViewMode:
        (pane.hierarchyController && pane.hierarchyController.treeView !== undefined)
            ? pane.hierarchyController.treeView : false
    // a fa sorainak száma — a magasságszámításhoz (#305 null-őrrel)
    //: #2049: „Indexképek megjelenítése a könyvtárban" — ugyanaz a
    //: kapcsoló, mint a `Nézet ▸ Mappanézet` menü tételéé. A
    //: `!== undefined` a próbák stub-vezérlőjére véd (#1572).
    readonly property bool albumThumbs:
        (pane.hierarchyController && pane.hierarchyController.albumThumbs !== undefined)
            ? pane.hierarchyController.albumThumbs : false

    readonly property int hierarchyRowCount:
        pane.hierarchyController ? pane.hierarchyController.rows.length : 0
    signal folderChosen(string path)
    signal starredChosen()
    signal albumChosen(string token)
    signal personChosen(string name)
    signal unnamedFacesChosen()
    signal ignoredFacesChosen()
    // #455: fogd-és-vidd az albumlistára — új album, illetve meglévőbe
    // sorolás. A tényleges munkát a gazda végzi (a névkérő párbeszéd és a
    // kijelölés is ott van).
    signal newAlbumDropped()
    signal photosDroppedOnAlbum(string token)

    // #320: a controller friss gyűjtemény-listájának lekérése — a
    // Component.onCompleted-en kívül minden create/rename/delete/move
    // után is meghívandó (#305 null-őrrel).
    function refreshCustomCollections() {
        if (!controller) return
        pane.customCollectionsModel = controller.customCollections
    }

    // #320: a mappasor jobbklikk-menüjének megnyitása — a `MouseArea`
    // delegate-ből (Repeater/ListView-elem, findChild-dal el nem érhető,
    // ld. MEMORY 2026-07-31) kiszervezve pane-szintű, névvel hívható
    // függvénybe, hogy közvetlenül (a valódi kattintás szintetizálása
    // nélkül) tesztelhető legyen.
    // #1595: a Mappa MENÜSÁV-menü ugyanazokat a műveleteket kínálja, mint a
    // mappa helyi menüje — csak a MEGNYITOTT mappára. A párbeszédek és a
    // megerősítések itt élnek, ezért a menüsáv is innen hívja őket: egy
    // művelet, egy út (különben két helyen kellene ugyanazt a
    // megerősítés-szöveget karbantartani).
    function mozgatasMappara(path) {
        if (!path) return
        pane._movingFolder = path
        moveFolderDialog.open()
    }

    function torlesLomtarba(path) {
        if (!path) return
        deleteFolderConfirm.pendingPath = path
        deleteFolderConfirm.message = qsTr(
            "Are you sure you want to move the folder \"%1\" and its "
            + "contents to the Recycle Bin?").arg(
                path.substring(path.lastIndexOf("/") + 1))
        deleteFolderConfirm.open()
    }

    function eltavolitasAPicasabol(path) {
        if (!path) return
        folderContextMenu.folderPath = path
        removeFolderConfirm.open()
    }

    function openFolderContextMenu(path) {
        folderContextMenu.folderPath = path
        folderContextMenu.customCollections = pane.customCollectionsModel
        // #1436: a pipák a mappa TARTALMÁNAK rendezését mutatják — ez a
        // menü (`Folder::SortFolderBy`) a mappa képeit rendezi, nem a
        // mappákat (azt a Mappa ▸ Rendezés `folderSort`-ja állítja, #1454).
        if (controller) {
            folderContextMenu.sortMode = controller.folderPhotoSort
            folderContextMenu.sortReverse = controller.folderPhotoSortReverse
            // #1637: a tétel felirata állapotfüggő („Mappa elrejtése" ↔
            // „Megjelenítés"), tehát a menü NYITÁSAKOR kell megkérdezni.
            // A `!== undefined` a #1572-őr mintája.
            folderContextMenu.folderHidden =
                (controller.isFolderHidden !== undefined)
                    ? controller.isFolderHidden(path) : false
        }
        folderContextMenu.popup()
    }

    // #422: a bal panel saját menüjének megnyitása — a pipák a menü
    // nyitásakor veszik át a vezérlő friss rendezés-állapotát
    function openFolderListContextMenu() {
        if (controller) {
            // #461/3: a BAL HASÁB saját rendezése — az eredetiben ez a
            // menü (`AlbumList`) a hasábot rendezte, nem a rácsot
            folderListContextMenu.sortMode = controller.paneSort
            folderListContextMenu.sortReverse = controller.paneSortReverse
        }
        folderListContextMenu.popup()
    }

    // #422 (4. lépcső): az album / Emberek-album jobbklikk-menüje — a
    // sor-delegátumból (Repeater-elem) kiszervezve pane-szintű, névvel
    // hívható függvénybe, a mappa-menü mintájára
    function openAlbumContextMenu(token, name) {
        albumContextMenu.albumToken = token
        albumContextMenu.albumName = name
        albumContextMenu.popup()
    }
    function openPeopleAlbumContextMenu(name) {
        peopleAlbumContextMenu.personName = name
        peopleAlbumContextMenu.popup()
    }

    // #422 (utolsó menü): a felhasználói gyűjtemény jobbklikk-menüjének
    // megnyitása — az album-menü mintájára, pane-szintű, névvel hívható
    // függvényben (tesztelhetőség).
    function openCollectionContextMenu(name) {
        collectionContextMenu.collectionName = name
        collectionContextMenu.popup()
    }

    // #422: melyik gyűjtemény átnevezése fut éppen a newCollectionDialog-on
    // keresztül — üres string esetén a dialógus a régi
    // "létrehozás" ágon fut (createCollection + esetleg
    // moveFolderToCollection), nem üres esetén az átnevezés ágon
    // (renameCollection). A newCollectionDialog egyetlen példány, ezt a
    // property-t kell megnézni a created(name) jelre.
    property string _renamingCollection: ""

    // Gyűjtemény-csukottság — kezdőérték a collections.py
    // DEFAULT_COLLAPSED-jét tükrözi (controller hiányában is ésszerű).
    property bool albumsCollapsed: false
    property bool peopleCollapsed: true
    property bool projectsCollapsed: true
    property bool foldersCollapsed: false
    property bool otherCollapsed: true

    // #476: a felhasználói gyűjtemények (customCollectionsModel) csukottsága
    // — név → bool térkép, csak memóriában (a controller-perzisztálásra még
    // nincs API, ellentétben a beépített öt gyűjteménnyel fent).
    property var collapsedCollections: ({})

    function isCustomCollectionCollapsed(name) {
        return pane.collapsedCollections[name] === true
    }

    // A toggleCollection mintáját követi, de a `next` állapotot új
    // objektumként írja vissza — a QML csak referenciaváltásra frissíti a
    // Repeater-kötéseket, helyben módosított property var-ra nem.
    function toggleCustomCollection(name) {
        var next = {}
        for (var key in pane.collapsedCollections) next[key] = pane.collapsedCollections[key]
        next[name] = !pane.isCustomCollectionCollapsed(name)
        pane.collapsedCollections = next
    }

    // #461: a gyűjtemény bezárása/megnyitása. A megnyitás mindig azonnali;
    // a BEZÁRÁS előtt viszont — ha utána egyetlen kép sem maradna a rácsban
    // — az eredeti figyelmeztetése jön, „ne kérdezze újra" kapcsolóval
    // (a bináris `DoNotAskOnLastCollectionClose` kulcsának megfelelője).
    function requestCollectionCloseToggle(name, currentlyClosed) {
        if (typeof controller === "undefined" || !controller) return
        if (currentlyClosed) {
            controller.setCollectionClosed(name, false)
            return
        }
        if (controller.closingHidesEverything(name)) {
            closeCollectionConfirm.pendingName = name
            // a szöveg EGY darabban: a `qsTr` kulcsa a teljes string, és a
            // QML-beli összefűzés (`"a" + "b"`) miatt a kulcs nem egyezne a
            // fordításfájl forrásával (a test_i18n_completeness ezt fogja meg)
            closeCollectionConfirm.ask(
                "view/dontAskOnLastCollectionClose",
                qsTr("You are about to close your last collection. No pictures will be shown in the thumbnail area. Do you want to continue?\n\nTo open a collection, double-click its name or click the icon next to it."))
            return
        }
        controller.setCollectionClosed(name, true)
    }

    Component.onCompleted: {
        // #305: null-őr — a controller a QML-engine leépítésekor
        // átmenetileg null lehet (itt: induláskor még nem biztos, hogy
        // kötve van, ha a teszt csak magát a komponenst tölti be).
        if (!controller) return
        pane.albumsCollapsed = controller.isCollectionCollapsed("albums")
        pane.peopleCollapsed = controller.isCollectionCollapsed("people")
        pane.projectsCollapsed = controller.isCollectionCollapsed("projects")
        pane.foldersCollapsed = controller.isCollectionCollapsed("folders")
        pane.otherCollapsed = controller.isCollectionCollapsed("other")
        pane.refreshCustomCollections()
    }

    // #320: a gyűjtemény-lista kívülről (más ablakból, pl. a Mappakezelőből
    // induló módosítás) is változhat — a controller jelzésére frissítünk.
    Connections {
        target: controller
        function onCustomCollectionsChanged() { pane.refreshCustomCollections() }
    }

    // Egy gyűjtemény nyitása/csukása: a helyi állapotot azonnal frissíti
    // (a fejléc-nyíl és a tartalom eltűnése ne várjon a controllerre), a
    // perzisztálás a controlleren át fut (#305: null-őrrel).
    function toggleCollection(name) {
        var next
        if (name === "albums") { pane.albumsCollapsed = !pane.albumsCollapsed; next = pane.albumsCollapsed }
        else if (name === "people") { pane.peopleCollapsed = !pane.peopleCollapsed; next = pane.peopleCollapsed }
        else if (name === "projects") { pane.projectsCollapsed = !pane.projectsCollapsed; next = pane.projectsCollapsed }
        else if (name === "folders") { pane.foldersCollapsed = !pane.foldersCollapsed; next = pane.foldersCollapsed }
        else if (name === "other") { pane.otherCollapsed = !pane.otherCollapsed; next = pane.otherCollapsed }
        else return
        if (controller) controller.setCollectionCollapsed(name, next)
    }

    // Kurzor/görgő léptetés a könyvtárelemek között (#77): a szomszéd
    // mappát a modell adja (az évszám-sorokat átugorva), a kiválasztás a
    // szokásos folderChosen-úton fut. A görgő itt nem görget, hanem a
    // kijelölt mappát lépteti (Picasa-viselkedés); a touchpad kis deltáit
    // egy teljes fokozatig (120) gyűjtjük.
    function stepFolder(delta) {
        if (!folderList.model) return
        var target = folderList.model.neighborFolder(pane.selectedPath, delta)
        if (target !== "" && target !== pane.selectedPath)
            pane.folderChosen(target)
    }
    property real wheelAccum: 0
    function wheelStep(delta) {
        wheelAccum += delta
        while (wheelAccum <= -120) { wheelAccum += 120; stepFolder(1) }
        while (wheelAccum >= 120) { wheelAccum -= 120; stepFolder(-1) }
    }
    // #730: a hasáb görgetése óta a mappalista a teljes tartalmát kirakja,
    // tehát ő maga nem görget — a látótérbe hozás a hasáb közös
    // `paneFlickable`-jének dolga. Csak akkor mozdul, ha tényleg kell, és a
    // tartalom határain belül marad.
    function ensurePaneRowVisible(top, rowHeight) {
        var bottom = top + rowHeight
        var maxY = Math.max(0, paneFlickable.contentHeight - paneFlickable.height)
        if (top < paneFlickable.contentY)
            paneFlickable.contentY = Math.max(0, Math.min(top, maxY))
        else if (bottom > paneFlickable.contentY + paneFlickable.height)
            paneFlickable.contentY =
                Math.max(0, Math.min(bottom - paneFlickable.height, maxY))
    }

    // #1454: a NÉZETMÓD-váltás is nyissa ki a kijelölt mappáig az ágakat.
    // A `revealPath()` eddig csak a `selectedPath` VÁLTOZÁSÁRA futott — a
    // nyitott ágak halmaza viszont induláskor üres, és a `flatten()` a
    // virtuális gyökeret sem tekinti nyitottnak. Fa-módra váltva ezért a
    // hasáb egyetlen összecsukott „Sajátgép" sorra zsugorodott, a kijelölt
    // mappa pedig eltűnt. (A fanézet menüből eddig elérhetetlen volt, így
    // ez a hiba még sosem látszott.)
    onTreeViewModeChanged: {
        if (pane.treeViewMode && pane.hierarchyController)
            pane.hierarchyController.revealPath(pane.selectedPath)
    }

    // a kijelölt mappa maradjon látótérben (kívülről is változhat:
    // kereső-javaslat, feed-görgetés)
    onSelectedPathChanged: {
        // #702: a fa is kövesse a kijelölést, és nyissa ki hozzá az őseit.
        // A kötést NEM elég deklaratívan megadni: a `FolderHierarchyView`
        // `choose()`-a maga is ír a `selectedPath`-ba, ami elszakítaná —
        // utána a kívülről (kereső, rács) érkező váltás nem érne el a fáig.
        folderHierarchyView.selectedPath = pane.selectedPath
        if (pane.treeViewMode && pane.hierarchyController)
            pane.hierarchyController.revealPath(pane.selectedPath)
        if (!folderList.model || !folderList.visible) return
        var row = folderList.model.rowOfPath(pane.selectedPath)
        if (row < 0) return
        folderList.positionViewAtIndex(row, ListView.Contain)
        pane.ensurePaneRowVisible(
            folderList.y + row * pane.rowHeight, pane.rowHeight)
    }

    // #422: jobbklikk a bal panel üres részén — a Picasa `AlbumList`
    // menüosztálya (a mappasorok saját menüje hamarabb elkapja az eseményt,
    // így ez tényleg csak a sorokon kívül fut le).
    TapHandler {
        objectName: "folderPaneContextMenuHandler"
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: pane.openFolderListContextMenu()
    }

    // #730: a hasáb EGÉSZE görgethető. Korábban a `ColumnLayout` az ablak
    // magasságába préselődött, ezért 30 személynél a mappalista magassága
    // 0 px lett, az „Egyéb” fejléc pedig kicsúszott az ablakból. Az eredeti
    // Picasa bal panelének SAJÁT, mindig látszó görgetősávja van
    // (docs/specs/ui-audit-mainwindow.md 3.1) — ez itt a `PicasaScrollBar`.
    Flickable {
        id: paneFlickable
        objectName: "folderPaneFlickable"
        anchors.fill: parent
        clip: true
        contentWidth: width
        contentHeight: paneColumn.height
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: PicasaScrollBar {
            objectName: "folderPaneScrollBar"
            // az eredeti sávja akkor is ott van, amikor nincs mit görgetni
            policy: ScrollBar.AlwaysOn
        }

        ColumnLayout {
            id: paneColumn
            width: paneFlickable.width
            // a magasságot a TARTALOM adja (nem az ablak) — ez a görgethető
            // tartalommagasság forrása is
            height: implicitHeight
            spacing: 0

            // Az Albumok gyűjtemény (fejléc + súgó + csillagozott sor +
            // album-sorok) önálló komponensben él — ld. AlbumsSection.qml.
            AlbumsSection {
                Layout.fillWidth: true
                collapsed: pane.albumsCollapsed
                albumsModel: pane.albumsModel
                selectedAlbumToken: pane.selectedAlbumToken
                starredActive: pane.starredActive
                rowHeight: pane.rowHeight
                onToggled: pane.toggleCollection("albums")
                onStarredChosen: pane.starredChosen()
                onAlbumChosen: function(token) { pane.albumChosen(token) }
                onAlbumContextMenuRequested: function(token, name) {
                    pane.openAlbumContextMenu(token, name)
                }
                onNewAlbumDropped: pane.newAlbumDropped()
                onPhotosDroppedOnAlbum: function(token) {
                    pane.photosDroppedOnAlbum(token)
                }
            }

            CollectionHeader {
                Layout.fillWidth: true
                label: qsTr("People")
                // #26: a `faces=`/`[Contacts2]`-ből aggregált, névvel ellátott
                // személyek száma (arcfelismerés nélkül — a meglévő ini-
                // adatokból, ld. picasapy.index.people).
                itemCount: pane.peopleModel.length
                labelObjectName: "peopleHeader"
                collapsed: pane.peopleCollapsed
                onToggled: pane.toggleCollection("people")
            }

            // #26: egy-egy sor személyenként — az AlbumsSection.qml album-sorainak
            // mintáját követi.
            Repeater {
                id: peopleRepeater
                objectName: "peopleRepeater"
                model: pane.peopleModel
                delegate: Rectangle {
                    id: personItem
                    required property var modelData
                    objectName: "personItem_" + modelData.name
                    readonly property bool isSelectedPerson:
                        pane.selectedPersonName === modelData.name
                    visible: !pane.peopleCollapsed
                    Layout.fillWidth: true
                    Layout.preferredHeight: 22
                    color: personItem.isSelectedPerson ? Theme.panelSelectionActive
                           : (personMouse.containsMouse ? Theme.panelSelection : "transparent")
                    Row {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left; anchors.leftMargin: 16
                        spacing: 5
                        Rectangle {
                            width: 10; height: 10
                            radius: 5
                            anchors.verticalCenter: parent.verticalCenter
                            color: Theme.picasaGreen
                        }
                        Text {
                            text: modelData.name + " (" + modelData.count + ")"
                            font.pixelSize: Theme.fontSize
                            color: personItem.isSelectedPerson || personMouse.containsMouse
                                   ? Theme.panelSelectionText : Theme.textDark
                        }
                    }
                    MouseArea {
                        id: personMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: function(mouse) {
                            // #422: jobbklikk = az Emberek-album menüje
                            if (mouse.button === Qt.RightButton) {
                                pane.openPeopleAlbumContextMenu(
                                    personItem.modelData.name)
                                return
                            }
                            pane.personChosen(personItem.modelData.name)
                        }
                    }
                }
            }

            // #26 (3. lépcső): a „Névtelenek" sor — a személyek listája ALATT,
            // ugyanabban az Emberek gyűjteményben (a personRepeater mintáját
            // követi, de nincs saját modell-elem, csak egy darabszám).
            Rectangle {
                id: unnamedFacesItem
                objectName: "unnamedFacesItem"
                // #26: beolvasás közben a sor AKKOR IS látszik, ha még nulla
                // névtelen arc van — a haladás helye maga ez a tétel
                visible: !pane.peopleCollapsed
                         && (pane.unnamedFaceCount > 0 || pane.faceScanPercent >= 0)
                Layout.fillWidth: true
                Layout.preferredHeight: 22
                color: pane.unnamedFacesActive ? Theme.panelSelectionActive
                       : (unnamedFacesMouse.containsMouse ? Theme.panelSelection : "transparent")
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 16
                    spacing: 5
                    Rectangle {
                        width: 10; height: 10
                        radius: 5
                        anchors.verticalCenter: parent.verticalCenter
                        color: Theme.textDark
                        opacity: 0.45
                    }
                    // #26/#449: az eredeti Picasa a beolvasás haladását MAGÁN
                    // a „Névtelenek" album tételén mutatta („While scanning,
                    // progress information appears in the Unnamed album item"),
                    // nem külön sávban vagy állapotsorban — a hosszú háttérmunka
                    // ott mutatkozik, ahol az eredménye lesz.
                    Text {
                        objectName: "unnamedFacesLabel"
                        text: pane.faceScanPercent >= 0
                              ? qsTr("Scanning for faces... %1% complete")
                                .arg(pane.faceScanPercent)
                              : qsTr("Unnamed") + " (" + pane.unnamedFaceCount + ")"
                        font.pixelSize: Theme.fontSize
                        font.italic: pane.faceScanPercent >= 0
                        color: pane.unnamedFacesActive || unnamedFacesMouse.containsMouse
                               ? Theme.panelSelectionText : Theme.textDark
                    }
                }
                MouseArea {
                    id: unnamedFacesMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    // #732: a „Névtelenek" az eredetiben ALBUM (`PplAlbum`,
                    // ui-audit-context-menus.md A.2), tehát a jobbklikk az
                    // Emberek-album menüjét adja — enélkül az esemény a
                    // hasáb-szintű TapHandlerre esett át, és a RENDEZÉS
                    // menüje nyílt meg helyette.
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: function(mouse) {
                        if (mouse.button === Qt.RightButton) {
                            pane.openPeopleAlbumContextMenu(qsTr("Unnamed"))
                            return
                        }
                        pane.unnamedFacesChosen()
                    }
                }
            }

            // #26: „Mellőzött emberek" — a Névtelenek sora ALATT, ugyanabban a
            // gyűjteményben. Csak akkor látszik, ha van benne valami: üres
            // albummal nem foglaljuk a helyet.
            Rectangle {
                objectName: "ignoredFacesItem"
                visible: !pane.peopleCollapsed && pane.ignoredFaceCount > 0
                Layout.fillWidth: true
                Layout.preferredHeight: 22
                color: pane.ignoredFacesActive ? Theme.panelSelectionActive
                       : (ignoredFacesMouse.containsMouse ? Theme.panelSelection : "transparent")
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 16
                    spacing: 5
                    Rectangle {
                        width: 10; height: 10
                        radius: 5
                        anchors.verticalCenter: parent.verticalCenter
                        color: Theme.textDark
                        opacity: 0.25
                    }
                    Text {
                        objectName: "ignoredFacesLabel"
                        text: qsTr("Ignored people") + " (" + pane.ignoredFaceCount + ")"
                        font.pixelSize: Theme.fontSize
                        color: pane.ignoredFacesActive || ignoredFacesMouse.containsMouse
                               ? Theme.panelSelectionText : Theme.textDark
                    }
                }
                MouseArea {
                    id: ignoredFacesMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    // #732: a „Mellőzött emberek" is ALBUM az eredetiben
                    // (`CAlbumLabel::Ignored`) — ld. a „Névtelenek" sort
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: function(mouse) {
                        if (mouse.button === Qt.RightButton) {
                            pane.openPeopleAlbumContextMenu(
                                qsTr("Ignored people"))
                            return
                        }
                        pane.ignoredFacesChosen()
                    }
                }
            }

            // A Projektek gyűjtemény (fejléc + a P2category-alapú
            // projekt-mappák + az „Exportált képek" csomópont) önálló
            // komponensben él — ld. ProjectsSection.qml (#1029).
            ProjectsSection {
                objectName: "projectsSection"
                Layout.fillWidth: true
                collapsed: pane.projectsCollapsed
                projectFolders: pane.projectFolders
                exportedFolders: pane.exportedFolders
                selectedPath: pane.selectedPath
                selectedAlbumToken: pane.selectedAlbumToken
                rowHeight: pane.rowHeight
                onToggled: pane.toggleCollection("projects")
                onFolderChosen: function(path) { pane.folderChosen(path) }
                onFolderContextMenuRequested: function(path) {
                    pane.openFolderContextMenu(path)
                }
            }

            CollectionHeader {
                Layout.fillWidth: true
                label: qsTr("Folders")
                itemCount: folderList.model ? folderList.model.folderCount : 0
                headerText: pane.searchActive
                            ? qsTr("Search results for \"%1\" (%2)")
                              .arg(pane.searchQuery).arg(pane.searchResultCount)
                            : ""
                labelObjectName: "folderPaneHeader"
                collapsed: pane.foldersCollapsed
                onToggled: pane.toggleCollection("folders")
            }

            ListView {
                id: folderList
                objectName: "folderListView"
                // #702: a lapos lista és a fa KIZÁRJA egymást — az eredeti
                // `thumbui/hviewtoggle` is egyszerre csak az egyiket rajzolja
                visible: !pane.foldersCollapsed && !pane.treeViewMode
                Layout.fillWidth: true
                // #730: a lista a TELJES tartalmát kirakja, a görgetés a
                // hasáb közös `paneFlickable`-jéé. A korábbi
                // `Layout.fillHeight: true` alsó korlát nélkül működött:
                // amint a fölötte lévő sorok kitöltötték az ablakot, a
                // maradék hely — és vele a lista magassága — 0 lett.
                // A sormagasság állandó, ezért a darabszámból pontosan
                // számolható (a `contentHeight`-ra kötés a még meg nem
                // született delegate-ek miatt becsléssel indulna).
                Layout.preferredHeight: folderList.count * pane.rowHeight
                clip: true

                // kurzorgombok, amikor a lista fókuszban van (#77)
                activeFocusOnTab: true
                Keys.onUpPressed: pane.stepFolder(-1)
                Keys.onDownPressed: pane.stepFolder(1)

                // #731: a görgő-léptetés (#77) CSAK a mappalista fölött
                // aktív. Korábban a hasáb GYÖKERÉN ült egy `WheelHandler`,
                // ezért a görgő bárhol a hasáb fölött MÁSIK mappát nyitott
                // meg görgetés helyett. Ez a kezelő a listán mélyebben van,
                // mint a hasáb `paneFlickable`-je, ezért a találati sorrend
                // szerint itt ő kapja meg előbb az eseményt; a hasáb többi
                // része fölött viszont a `paneFlickable` görget.
                WheelHandler {
                    objectName: "folderStepWheelHandler"
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                    onWheel: function(event) { pane.wheelStep(event.angleDelta.y) }
                }

                // A háttér-szinkron utáni modell-frissítés ne nullázza a
                // görgetési pozíciót — enélkül a lista folyton visszaugrik,
                // és nem lehet görgetni. A reset 0-ra ugrása nem írhatja
                // felül a mentett pozíciót (#10, a fotórács mintájára).
                property real savedY: 0
                property bool restoring: false
                onContentYChanged: {
                    if (!restoring && (contentY > 0 || moving))
                        savedY = contentY
                }
                onMovementEnded: savedY = contentY
                Connections {
                    // #305 null-őr: fa-nézetben (és a komponens önálló
                    // betöltésekor) a lapos listának nincs modellje
                    target: folderList.model ? folderList.model : null
                    function onFolderCountChanged() {
                        folderList.restoring = true
                        folderList.contentY = Math.min(
                            folderList.savedY,
                            Math.max(0, folderList.contentHeight
                                        - folderList.height))
                        folderList.restoring = false
                    }
                }
                delegate: Rectangle {
                    required property string kind
                    required property string name
                    required property string path
                    required property int count
                    // #459/5: „jelenleg nem elérhető" mappa (levált NAS-mount,
                    // kihúzott lemez) — a sor bennmarad, csak jelölést kap.
                    required property bool offline
                    //: #1644: „olvasatlan" — új kép került a mappába, amit a
                    //: felhasználó még nem nézett meg. A tulajdonos élő
                    //: megfigyelése szerint az eredeti ilyenkor KÖVÉREN
                    //: szedi a mappa nevét (`albumdata_unread`).
                    required property bool unread
                    width: folderList.width; height: pane.rowHeight
                    // #9: album-nézetben a mappa-kijelölés szűnjön meg — a
                    // hasábon csak az aktív album sora legyen kiemelve.
                    readonly property bool isSelectedFolder:
                        kind === "folder" && pane.selectedPath === path
                        && pane.selectedAlbumToken === ""
                    // #384: hover ≠ kijelölés (ld. AlbumsSection.qml) —
                    // a "year" sorok nem kattinthatók, a MouseArea rájuk
                    // enabled: false, így containsMouse mindig false marad.
                    color: isSelectedFolder ? Theme.panelSelectionActive
                           : (folderRowMouse.containsMouse ? Theme.panelSelection : "transparent")

                    // évszám-elválasztó: arányos betűs címke + vékony
                    // vízszintes elválasztó vonal a panel széléig (audit:
                    // docs/specs/ui-audit-mainwindow.md, mappafa szakasz)
                    //
                    // #1637/2: a „Rejtett mappák" csomópont fejléce
                    // UGYANEZ a sorfajta — címke + vonal, kijelölés nélkül.
                    // Csak a fajtája más (`hidden`), hogy a modell ne
                    // hazudjon évszámot oda, ahol gyűjtemény van.
                    readonly property bool isHeaderRow:
                        kind === "year" || kind === "hidden"
                    Text {
                        id: yearLabel
                        visible: parent.isHeaderRow
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left; anchors.leftMargin: 6
                        text: name
                        font.pixelSize: Theme.fontSize
                        color: Theme.panelYearText
                    }
                    Rectangle {
                        visible: parent.isHeaderRow
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: yearLabel.right; anchors.leftMargin: 6
                        anchors.right: parent.right; anchors.rightMargin: 6
                        height: 1
                        color: Theme.chromeBorder
                    }

                    Row {
                        // Audit (ui-audit-mainwindow.md, mappafa 1.3/8): az
                        // eredeti Picasa mappasorai nem nyithatók (nincs
                        // almappa-szint a lapos Mappák-listában), ezért nincs
                        // nyílglif előttük sem — csak a sárga mappaikon + név.
                        visible: kind === "folder"
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left; anchors.leftMargin: 12
                        spacing: 5
                        // #2049: az eredeti a Mappák-lista sorain nem sárga
                        // mappaikont mutat, hanem a mappa első legfeljebb
                        // négy fotójából összeállított kis kupacot — de
                        // CSAK ha az „Indexképek megjelenítése a
                        // könyvtárban" be van kapcsolva
                        // (`ShowAlbumThumbnails2`, alapérték 0). Ha nincs
                        // borító (kép nélküli mappa), a sor visszaesik a
                        // mappaikonra: az eredeti is helyettesítő ikonokat
                        // sorol fel erre (`0x00761870`: `icons/folder`,
                        // `icons/album`, `icons/smartalbum`, …).
                        Item {
                            objectName: "folderRowCover"
                            width: 13
                            height: 18
                            anchors.verticalCenter: parent.verticalCenter
                            opacity: offline ? 0.45 : 1.0

                            readonly property bool boritoLatszik:
                                pane.albumThumbs && folderRowCoverImage.status === Image.Ready

                            FolderIcon {
                                size: 13
                                visible: !parent.boritoLatszik
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Image {
                                id: folderRowCoverImage
                                objectName: "folderRowCoverImage"
                                anchors.centerIn: parent
                                height: parent.height
                                fillMode: Image.PreserveAspectFit
                                visible: parent.boritoLatszik
                                asynchronous: true
                                // ⚠️ Kikapcsolva ÜRES a forrás, tehát a
                                // szolgáltató meg sem szólal: négy JPEG
                                // dekódolása mappánként nem indul el
                                // feleslegesen.
                                source: pane.albumThumbs
                                        ? "image://foldercover/" + path
                                        : ""
                            }
                        }
                        Text {
                            objectName: "folderRowLabel"
                            text: name + " (" + count + ")"
                            font.pixelSize: Theme.fontSize
                            // #459/5: a nem elérhető mappa dőlt és halvány —
                            // a sor kattintható marad (a bélyegképek a
                            // gyorsítótárból még látszanak), csak jelzi az
                            // állapotot; a részletet a súgószöveg mondja el.
                            font.italic: offline
                            //: #1644: KÖVÉR, ha új kép került a mappába.
                            //: A megnyitáskor áll vissza.
                            font.bold: unread
                            opacity: offline ? 0.55 : 1.0
                            color: isSelectedFolder || folderRowMouse.containsMouse
                                   ? Theme.panelSelectionText : Theme.ink
                        }
                    }
                    ToolTip.visible: offline && folderRowMouse.containsMouse
                    ToolTip.text: qsTr("Currently unavailable — the folder stays in the database, thumbnails come from the cache.")
                    MouseArea {
                        id: folderRowMouse
                        enabled: kind === "folder"
                        hoverEnabled: true
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: function(mouse) {
                            folderList.forceActiveFocus()   // kurzorgombokhoz (#77)
                            if (mouse.button === Qt.RightButton) {
                                pane.openFolderContextMenu(path)
                                return
                            }
                            pane.folderChosen(path)
                        }
                    }
                }
                // #730: a lista SAJÁT görgetősávja megszűnt — a hasáb
                // egészét a `paneFlickable` görgeti, egyetlen sávval (az
                // eredetiben is egy sáv van a bal panelen).
            }

            // #702: ugyanennek a gyűjteménynek a MÁSIK nézetmódja — a
            // hierarchikus fa. A rajzolás a `FolderHierarchyView.qml`-ben
            // van, az adat a `FolderHierarchyController`-ben; itt csak a
            // hasábba illesztés és a jelzések bekötése történik.
            FolderHierarchyView {
                id: folderHierarchyView
                objectName: "folderHierarchyView"
                visible: !pane.foldersCollapsed && pane.treeViewMode
                Layout.fillWidth: true
                // #730: a fa is a TELJES tartalmát kirakja — a hasáb
                // egyetlen görgetője a `paneFlickable` marad. A sorok
                // számát a vezérlő adja (a csukott ágak gyermekei el sem
                // jutnak ide), a sormagasság a hasábé.
                Layout.preferredHeight: pane.hierarchyRowCount * pane.rowHeight
                hierarchy: pane.hierarchyController
                selectedPath: pane.selectedPath
                rowHeight: pane.rowHeight
                onFolderChosen: function(path) { pane.folderChosen(path) }

                // A `HierFolder` menü három tétele, aminek a rétege a
                // gazdában van — ugyanazokra a hívásokra kötve, mint a
                // mappa-menü megfelelő parancsai (FolderContextMenu).
                onLocateOnDiskRequested: function(path) {
                    if (typeof fileOpsController !== "undefined" && fileOpsController)
                        fileOpsController.revealFolder(path)
                }
                onRemoveFromPicasaRequested: function(path) {
                    pane._askRemoveFolder(path)
                }
                onMoveFolderRequested: function(path) {
                    pane._movingFolder = path
                    moveFolderDialog.open()
                }
            }

            // #476: a felhasználói mappa-gyűjtemények (#320 óta léteznek, de
            // eddig sehol nem jelentek meg) — a beépített "Mappák" gyűjtemény
            // ALATT, az "Egyéb" fejléc ELŐTT, gyűjteményenként egy csukható
            // fejléc + a hozzá sorolt mappák sorai (az AlbumsSection/folderList
            // sor-mintáját követve).
            Repeater {
                id: customCollectionsRepeater
                objectName: "customCollectionsRepeater"
                model: pane.customCollectionsModel
                delegate: Column {
                    id: customCollectionItem
                    required property var modelData
                    objectName: "customCollectionItem_" + customCollectionItem.modelData.name
                    Layout.fillWidth: true
                    spacing: 0

                    CollectionHeader {
                        width: customCollectionItem.width
                        label: customCollectionItem.modelData.name
                        itemCount: customCollectionItem.modelData.folders.length
                        labelObjectName: "customCollection_" + customCollectionItem.modelData.name
                        collapsed: pane.isCustomCollectionCollapsed(customCollectionItem.modelData.name)
                        closable: true
                        closed: customCollectionItem.modelData.closed === true
                        onCloseToggled: pane.requestCollectionCloseToggle(
                            customCollectionItem.modelData.name,
                            customCollectionItem.modelData.closed === true)
                        onToggled: pane.toggleCustomCollection(customCollectionItem.modelData.name)
                        onRightClicked: pane.openCollectionContextMenu(
                            customCollectionItem.modelData.name)
                    }

                    Repeater {
                        objectName: "customCollectionFoldersRepeater_" + customCollectionItem.modelData.name
                        model: customCollectionItem.modelData.folders
                        delegate: Rectangle {
                            id: customFolderItem
                            required property var modelData
                            objectName: "customCollectionFolder_" + customFolderItem.modelData
                            readonly property bool isSelectedFolder:
                                pane.selectedPath === customFolderItem.modelData
                                && pane.selectedAlbumToken === ""
                            // #461: a bezárt gyűjtemény tartalma sem a fában, sem a
                            // rácsban nem látszik — a fejléce viszont marad, hogy
                            // vissza lehessen nyitni
                            visible: !pane.isCustomCollectionCollapsed(customCollectionItem.modelData.name)
                                     && customCollectionItem.modelData.closed !== true
                            width: customCollectionItem.width
                            height: 22
                            color: customFolderItem.isSelectedFolder ? Theme.panelSelectionActive
                                   : (customFolderMouse.containsMouse ? Theme.panelSelection : "transparent")
                            Row {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.left: parent.left; anchors.leftMargin: 16
                                spacing: 5
                                FolderIcon { size: 13; anchors.verticalCenter: parent.verticalCenter }
                                Text {
                                    text: customFolderItem.modelData.substring(
                                              customFolderItem.modelData.lastIndexOf("/") + 1)
                                    font.pixelSize: Theme.fontSize
                                    color: customFolderItem.isSelectedFolder || customFolderMouse.containsMouse
                                           ? Theme.panelSelectionText : Theme.ink
                                }
                            }
                            MouseArea {
                                id: customFolderMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                // #732: a gyűjteménybe sorolt mappa ugyanaz
                                // a MAPPA, mint a Mappák-listában — ugyanazt
                                // a menüt kell adnia (egy komponens, több
                                // hívó; ui-audit-context-menus.md 1.b)
                                acceptedButtons: Qt.LeftButton | Qt.RightButton
                                onClicked: function(mouse) {
                                    if (mouse.button === Qt.RightButton) {
                                        pane.openFolderContextMenu(
                                            customFolderItem.modelData)
                                        return
                                    }
                                    pane.folderChosen(customFolderItem.modelData)
                                }
                            }
                        }
                    }
                }
            }

            CollectionHeader {
                Layout.fillWidth: true
                label: qsTr("Other")
                // #320: még nincs kijelölt tartalom-forrás ehhez a
                // gyűjteményhez — a fejléc addig is látszik, üresen.
                itemCount: 0
                labelObjectName: "otherHeader"
                collapsed: pane.otherCollapsed
                onToggled: pane.toggleCollection("other")
            }
        }
    }

    // #320: a mappasor jobbklikk-menüje + a hozzá tartozó két kis
    // dialógus (önálló, signal-alapú komponensek — ld. FolderContextMenu/
    // NewCollectionDialog/FolderDateDialog.qml). A controller-kötést itt,
    // a FolderPane.qml-ben végezzük (nem forró fájl) — a hívott
    // controller-slotok (createCollection, moveFolderToCollection,
    // setFolderDate, clearFolderDate, customCollections) az AppController
    // öröklés-listájának bővítésével válnak élővé (controller.py, forró
    // fájl — az integrátor dolga).
    // #422: a fő ablak a kijelölés-parancsokhoz és a webexport-dialógushoz
    // (a PhotoViewer.qml `Window.window` mintája — így a forró Main.qml-hez
    // nem kell hozzányúlni; önálló példányosításnál egyszerűen hiányzik)
    readonly property var appWindow: Window.window

    AlbumContextMenu {
        id: albumContextMenu
        onSelectAllRequested:
            if (pane.appWindow && pane.appWindow.selectAll) pane.appWindow.selectAll()
        onClearSelectionRequested:
            if (pane.appWindow && pane.appWindow.clearSelection)
                pane.appWindow.clearSelection()
        onInvertSelectionRequested:
            if (pane.appWindow && pane.appWindow.invertSelection)
                pane.appWindow.invertSelection()
        // az album tartalma a jelenlegi mappákból áll — a frissítés a
        // megnyitott mappa újraszinkronja (a mappa-menü mintája)
        onRefreshThumbnailsRequested:
            if (controller) controller.resyncFolder(controller.currentFolder)
        onExportAsHtmlRequested:
            if (pane.appWindow && pane.appWindow.openWebExport)
                pane.appWindow.openWebExport()
    }

    PeopleAlbumContextMenu {
        id: peopleAlbumContextMenu
        onSelectAllRequested:
            if (pane.appWindow && pane.appWindow.selectAll) pane.appWindow.selectAll()
        onClearSelectionRequested:
            if (pane.appWindow && pane.appWindow.clearSelection)
                pane.appWindow.clearSelection()
    }

    FolderListContextMenu {
        id: folderListContextMenu
        // #1454: az „Egyszerűsített fanézet" ugyanazt a kapcsolót billenti,
        // mint a menüsáv `Nézet ▸ Mappanézet` harmadik tétele
        simplifiedTree:
            pane.hierarchyController ? pane.hierarchyController.simplified : false
        // #1767: a Személyek lista rendezése — a `!== undefined` a
        // #1572-őr mintája (a próbák stub-vezérlőjén hiányozhat)
        peopleSort: (controller && controller.peopleSort !== undefined)
            ? controller.peopleSort : "name"
        onPeopleSortRequested: function(mode) {
            if (controller && controller.setPeopleSort !== undefined)
                controller.setPeopleSort(mode)
        }
        onSortModeRequested: function(mode) {
            if (controller) controller.setPaneSort(mode)
        }
        onSortReverseRequested: if (controller) controller.togglePaneSortReverse()
        onSimplifiedTreeRequested:
            if (pane.hierarchyController) pane.hierarchyController.toggleSimplified()
    }

    // #457: melyik mappát mozgatjuk épp (a dialógus elfogadásakor kell)
    property string _movingFolder: ""

    FolderDialog {
        id: moveFolderDialog
        objectName: "moveFolderDialog"
        title: qsTr("Move Folder")
        onAccepted: {
            if (pane._movingFolder.length > 0
                    && typeof fileOpsController !== "undefined"
                    && fileOpsController)
                fileOpsController.moveFolder(
                    pane._movingFolder, moveFolderDialog.selectedFolder)
            pane._movingFolder = ""
        }
    }

    FolderContextMenu {
        id: folderContextMenu
        // #457: „Mappa áthelyezése…" — a célmappát a rendszer
        // mappaválasztójával kérjük be, a mozgatás a kísérőfájlokkal
        // együtt megy (a `.picasa.ini` nálunk az igazságforrás)
        onMoveFolderRequested: {
            pane._movingFolder = folderContextMenu.folderPath
            moveFolderDialog.open()
        }

        // #1638: „Mappa törlése…" — a mappa a LOMTÁRBA kerül a
        // tartalmával együtt. A megerősítés az eredeti szövegével megy, és
        // a mappa NEVÉT tartalmazza, hogy ne lehessen véletlen mást
        // törölni.
        onDeleteFolderRequested: {
            var ut = folderContextMenu.folderPath
            if (ut === "") return
            deleteFolderConfirm.pendingPath = ut
            deleteFolderConfirm.message = qsTr(
                "Are you sure you want to move the folder \"%1\" and its "
                + "contents to the Recycle Bin?").arg(
                    ut.substring(ut.lastIndexOf("/") + 1))
            deleteFolderConfirm.open()
        }

        // #1637: a „Mappa elrejtése / Megjelenítés" — a jelölés az
        // INDEXBE megy, a lemezen semmi nem mozdul. Elrejtés után a mappa
        // eltűnik a hasábról; a Nézet ▸ Rejtett képek kapcsolóval jön
        // vissza, ugyanúgy, mint a rejtett fotók.
        onHideFolderRequested: function(ut) {
            if (controller && ut.length > 0) controller.toggleFolderHidden(ut)
        }

        onMoveToCollectionRequested: function(collectionName) {
            if (controller) controller.moveFolderToCollection(
                folderContextMenu.folderPath, collectionName)
        }
        onNewCollectionRequested: {
            // #422: a létrehozás-ág — a _renamingCollection üresen marad,
            // az initialName is üres (a korábbi átnevezésből esetleg
            // bennragadt értéket felülírjuk)
            pane._renamingCollection = ""
            newCollectionDialog.initialName = ""
            newCollectionDialog.open()
        }

        // #422: az eredeti `album.fen` dialógusa — a mappa DÁTUMA is itt
        // lakik, ezért szűnt meg a külön „Mappa dátumának beállítása…"
        // menütétel
        onEditDescriptionRequested: {
            var path = folderContextMenu.folderPath
            folderPropertiesDialog.folderPath = path
            folderPropertiesDialog.folderName =
                path.substring(path.lastIndexOf("/") + 1)
            folderPropertiesDialog.currentDate =
                controller ? controller.folderDateOverride(path) : ""
            folderPropertiesDialog.currentDescription =
                controller ? controller.folderDescriptionOf(path) : ""
            folderPropertiesDialog.open()
        }

        onSelectAllRequested:
            if (pane.appWindow && pane.appWindow.selectAll) pane.appWindow.selectAll()
        onClearSelectionRequested:
            if (pane.appWindow && pane.appWindow.clearSelection)
                pane.appWindow.clearSelection()
        onInvertSelectionRequested:
            if (pane.appWindow && pane.appWindow.invertSelection)
                pane.appWindow.invertSelection()

        onRefreshThumbnailsRequested:
            if (controller) controller.resyncFolder(folderContextMenu.folderPath)
        // #1436: a mappa TARTALMÁT rendezi (a képeket), nem a mappákat. A
        // korábbi `setFolderSort` a rács MAPPA-sorrendjét állította, ezért
        // tett a menüpont mást, mint amit a neve ígért.
        onSortModeRequested: function(mode) {
            if (controller) controller.setFolderPhotoSort(mode)
        }
        onSortReverseRequested:
            if (controller) controller.toggleFolderPhotoSortReverse()

        onLocateRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController)
                fileOpsController.revealFolder(folderContextMenu.folderPath)
        }
        onRemoveFromPicasaRequested: pane._askRemoveFolder(
            folderContextMenu.folderPath)
        onExportAsHtmlRequested:
            if (pane.appWindow && pane.appWindow.openWebExport)
                pane.appWindow.openWebExport()
    }

    // #1249: az eredeti megerősítés — a MAPPA NEVÉVEL, és kimondja az
    // almappákat („Do you want to remove the folder %s and its
    // subfolders?", `CThumbUI::ManageAlbum`). A név a path utolsó tagja.
    function _askRemoveFolder(path) {
        folderContextMenu.folderPath = path
        var nev = String(path).split(/[\\/]/).filter(Boolean).pop() || path
        removeFolderConfirm.ask(
            "removeFolder",
            qsTr("Do you want to remove the folder %1 and its subfolders?")
                .arg(nev))
    }

    // „Eltávolítás a Picasából…" — a fájlok a lemezen maradnak, csak a
    // könyvtárból kerül ki (#422 → #1249)
    // #1638: a mappa lomtárba tétele — a megerősítés az eredeti szövegével
    ConfirmDialog {
        id: deleteFolderConfirm
        namePrefix: "deleteFolderConfirm"
        property string pendingPath: ""
        title: qsTr("Delete Folder")
        yesText: qsTr("Delete Folder")
        onConfirmed: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                    && deleteFolderConfirm.pendingPath !== "")
                fileOpsController.deleteFolder(deleteFolderConfirm.pendingPath)
            deleteFolderConfirm.pendingPath = ""
        }
        onDenied: deleteFolderConfirm.pendingPath = ""
        onCanceled: deleteFolderConfirm.pendingPath = ""
    }

    ConfirmDialog {
        id: removeFolderConfirm
        namePrefix: "removeFolderConfirm"
        // az eredeti igen-gombja: `CThumbUI:ManageAlbumYesButton`
        yesText: qsTr("Remove Folder")
        onConfirmed: {
            // #1249: a removeWatchedFolder CSAK pontos figyelt-gyökérre
            // hatott — almappán némán semmit nem csinált (a jelentett
            // tünet). A removeFolder a széles változat: gyökérre a teljes
            // meglévő út, almappára index-takarítás + sírkő.
            if (controller && folderContextMenu.folderPath !== "")
                controller.removeFolder(folderContextMenu.folderPath)
        }
    }

    // #461: az utolsó gyűjtemény bezárásának figyelmeztetése — a címe és a
    // gombfelirata is az eredetiből (IDS_CLOSING_LAST_COLLECTION_TITLE,
    // CloseCollection::YesButon).
    ConfirmDialog {
        id: closeCollectionConfirm
        namePrefix: "closeCollectionConfirm"
        property string pendingName: ""
        title: qsTr("Close Last Collection?")
        yesText: qsTr("Close Collection")
        onConfirmed: {
            if (controller && closeCollectionConfirm.pendingName !== "")
                controller.setCollectionClosed(closeCollectionConfirm.pendingName, true)
            closeCollectionConfirm.pendingName = ""
        }
        onDenied: closeCollectionConfirm.pendingName = ""
        onCanceled: closeCollectionConfirm.pendingName = ""
    }

    FolderPropertiesDialog {
        id: folderPropertiesDialog
        onFolderPropertiesAccepted: function(path, isoDate, description) {
            if (!controller) return
            controller.setFolderDescriptionOf(path, description)
            // üres dátum = „automatikus dátum": a felülírás törlése
            if (isoDate.length > 0) controller.setFolderDate(path, isoDate)
            else controller.clearFolderDate(path)
        }
    }

    NewCollectionDialog {
        id: newCollectionDialog
        onCreated: function(name) {
            if (!controller) return
            // #422: ugyanaz a dialógus szolgálja a létrehozást (a
            // FolderContextMenu "Új gyűjtemény…" ága) ÉS az átnevezést (a
            // CollectionContextMenu "Gyűjtemény átnevezése…" ága) — a két
            // használatot a pane._renamingCollection különbözteti meg.
            if (pane._renamingCollection !== "") {
                controller.renameCollection(pane._renamingCollection, name)
                pane._renamingCollection = ""
            } else {
                controller.createCollection(name)
                // Picasa-mintára: a "Move to Collection ▸ New Collection…"-ból
                // indított létrehozás a jobbklikkelt mappát rögtön bele is
                // sorolja az új gyűjteménybe.
                if (folderContextMenu.folderPath !== "")
                    controller.moveFolderToCollection(
                        folderContextMenu.folderPath, name)
            }
            pane.refreshCustomCollections()
        }
    }

    // #422: a gyűjtemény jobbklikk-menüje (átnevezés/eltávolítás/jelszó) —
    // a Collection menüosztály, a #476-ban készült CollectionHeader
    // fejlécre kötve (pane.openCollectionContextMenu).
    CollectionContextMenu {
        id: collectionContextMenu
        onRenameRequested: {
            pane._renamingCollection = collectionContextMenu.collectionName
            newCollectionDialog.initialName = collectionContextMenu.collectionName
            newCollectionDialog.open()
        }
        // #461: az eredeti Picasa szövege kimondja, hogy a mappák NEM
        // vesznek el — az alapértelmezett gyűjteménybe kerülnek. Ez a
        // megnyugtató mondat a lényeg, ezért szó szerint átvesszük.
        onRemoveRequested: removeCollectionConfirm.ask(
            "removeCollection",
            qsTr("Are you sure you want to remove the collection \u201c%1\u201d? "
                 + "All folders in it will be moved to the collection "
                 + "\u201c%2\u201d.")
                .replace("%1", collectionContextMenu.collectionName)
                .replace("%2", qsTr("Folders on Disk")))
    }

    // „Gyűjtemény eltávolítása" megerősítése (#422) — egyedi namePrefix,
    // hogy ne ütközzön a removeFolderConfirm-mal
    ConfirmDialog {
        id: removeCollectionConfirm
        namePrefix: "removeCollectionConfirm"
        onConfirmed: {
            if (controller && collectionContextMenu.collectionName !== "")
                controller.deleteCollection(collectionContextMenu.collectionName)
            pane.refreshCustomCollections()
        }
    }

}

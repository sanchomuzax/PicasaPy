import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A lapos mappalista egy sora, a rejtett gyűjtemény és a húzási célpont.
Rectangle {
    property var folderPane: null
    property var listView: null
    objectName: kind === "hidden" ? "hiddenCollectionHeader" : ""
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
    // #3681: mentés-szűrő módban csak a MENTETLEN mappák
    // maradnak — a többi (és az évszám-/rejtett-fejlécek)
    // 0 magasságú, hogy a lista ne hagyjon üres rést.
    //
    // #3776 átnézés [ALACSONY]: a `mentesKulcs` soronként
    // KÉTSZER hívta ugyanazt a `path`-ot (itt és a
    // darabszám-feliratnál) — egyszeri kiszámítással.
    //
    // #3799: a kulcs a `mentesSzuroAktiv`-tól függ, hogy a
    // szűrő bekapcsolásakor újraszámolódjon. A `mentesKulcs`
    // a `backupController`-t olvassa; a vezérlő bekötése
    // ELŐTT készült sor különben a nyers utat őrizné, a
    // `mentesTerkep` viszont `flat_key`-kulcsú (Windowson
    // kisbetűs, perjeles) — egyik sor sem találna.
    readonly property string mentesKulcsa:
        folderPane.mentesSzuroAktiv && kind === "folder"
        ? folderPane.mentesKulcs(path) : ""
    readonly property bool mentesJelolt:
        folderPane.mentesSzuroAktiv && kind === "folder"
        && folderPane.mentesTerkep[mentesKulcsa] !== undefined
    readonly property bool mentesRejtett:
        folderPane.mentesSzuroAktiv && !mentesJelolt
    visible: !mentesRejtett
    width: listView.width
    height: mentesRejtett ? 0 : folderPane.rowHeight
    // #9: album-nézetben a mappa-kijelölés szűnjön meg — a
    // hasábon csak az aktív album sora legyen kiemelve.
    readonly property bool isSelectedFolder:
        kind === "folder" && folderPane.selectedPath === path
        && folderPane.selectedAlbumToken === ""
    // #384: hover ≠ kijelölés (ld. AlbumsSection.qml) —
    // a "year" sorok nem kattinthatók, a MouseArea rájuk
    // enabled: false, így containsMouse mindig false marad.
    color: folderDropArea.containsDrag ? Theme.listDragTarget
           : (isSelectedFolder ? Theme.panelSelectionActive
           : (kind === "folder" && folderRowMouse.containsMouse
              ? Theme.panelSelection : "transparent"))

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

    // #3681: a mentés-szűrő pipája — csak a mentetlen
    // mappákon látszik. A KATTINTÁST a teljes sort lefedő
    // `folderRowMouse` kezeli (lentebb): a pipa csak
    // TÜKRÖZI az állapotot, hogy egyetlen helyen dőljön el
    // a "pipálás vs. mappanyitás" ág.
    CheckBox {
        objectName: "folderRowMentesCheck"
        visible: parent.mentesJelolt
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left; anchors.leftMargin: 2
        topPadding: 0
        bottomPadding: 0
        checked: folderPane.mentesPipaltMappak.indexOf(path) >= 0
    }
    Row {
        id: folderRowContent
        // Audit (ui-audit-mainwindow.md, mappafa 1.3/8): az
        // eredeti Picasa mappasorai nem nyithatók (nincs
        // almappa-szint a lapos Mappák-listában), ezért nincs
        // nyílglif előttük sem — csak a sárga mappaikon + név.
        visible: kind === "folder"
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: parent.mentesJelolt ? 34 : 12
        spacing: 5
        // #2049: az eredeti a Mappák-lista sorain nem sárga
        // mappaikont mutat, hanem a mappa ELSŐ fotójának
        // kis bélyegképét (#2989) — de az egydimenziós
        // listán CSAK ha az „Indexképek megjelenítése a
        // könyvtárban" be van kapcsolva
        // (`ShowAlbumThumbnails2`, alapérték 0). Ha nincs
        // borító (kép nélküli mappa), a sor visszaesik a
        // mappaikonra: az eredeti is helyettesítő ikonokat
        // sorol fel erre (`0x00761870`: `icons/folder`,
        // `icons/album`, `icons/smartalbum`, …).
        Item {
            objectName: "folderRowCover"
            // #2989: a hely FIX, a mért 17 × 15 arányában —
            // a kép aránytartón fér bele, és a nevek EGY
            // vonalban kezdődnek (a 13 a mappaikon mérete).
            readonly property int ikonDoboz: Math.round(18 * 17 / 15)
            width: boritoLatszik ? ikonDoboz : 13
            height: 18
            anchors.verticalCenter: parent.verticalCenter
            opacity: offline ? 0.45 : 1.0

            // #2215/#4876: a `Ready` önmagában nem elég —
            // a szolgáltató borító hiányában SZÁNDÉKOSAN 1×1
            // átlátszó, érvényes jelölőt ad (null képre a Qt
            // minden kérésnél hibasort írna), ami sikeresen
            // betöltődik. A szélességfeltétel (`> 1`) az
            // ELSŐDLEGES védelem: ettől látszik ilyenkor a
            // mappaikon.
            readonly property bool boritoLatszik:
                folderPane.albumThumbs
                && folderRowCoverImage.status === Image.Ready
                && folderRowCoverImage.implicitWidth > 1

            FolderIcon {
                objectName: "folderRowIcon"
                size: 13
                visible: !parent.boritoLatszik
                anchors.verticalCenter: parent.verticalCenter
            }

            Image {
                id: folderRowCoverImage
                objectName: "folderRowCoverImage"
                anchors.centerIn: parent
                // #2989: EGYETLEN bélyegkép, a dobozba
                // aránytartón beillesztve — nem kupac.
                width: parent.ikonDoboz
                height: parent.height
                fillMode: Image.PreserveAspectFit
                visible: parent.boritoLatszik
                asynchronous: true
                // ⚠️ Kikapcsolva ÜRES a forrás, tehát a
                // szolgáltató meg sem szólal: négy JPEG
                // dekódolása mappánként nem indul el
                // feleslegesen.
                //: #2983: üres útvonalra sem kérünk borítót —
                //: a napló szerint a hasáb hét ilyen kérést
                //: adott ki (album/gyűjtemény-sorok, amiknek
                //: nincs mappa-útvonala), és mindegyik egy
                //: hibasort írt a konzolra.
                source: (folderPane.albumThumbs && path !== "")
                        ? "image://foldercover/" + path
                        : ""
            }
        }
        Text {
            objectName: "folderRowLabel"
            //: #3681: szűrő módban a darabszám a még el nem
            //: mentett fájloké, nem a mappa összes képéé
            text: name + " (" + (parent.parent.mentesJelolt
                  ? folderPane.mentesTerkep[parent.parent.mentesKulcsa].darab
                  : count) + ")"
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
            color: folderDropArea.containsDrag
                   || isSelectedFolder || folderRowMouse.containsMouse
                   ? Theme.panelSelectionText : Theme.ink
        }
    }
    //: #3681: a mentetlen mappa fájlnevei — ami elfér
    Text {
        objectName: "folderRowMentesFiles"
        visible: parent.mentesJelolt
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: folderRowContent.right
        anchors.leftMargin: 6
        anchors.right: parent.right
        anchors.rightMargin: 6
        elide: Text.ElideRight
        text: parent.mentesJelolt ? folderPane.mentesFajlSor(path) : ""
        font.pixelSize: Theme.fontSize - 1
        color: parent.isSelectedFolder || folderRowMouse.containsMouse
               ? Theme.panelSelectionText : Theme.folderDate
    }
    // #2162: TUDATOS ELTÉRÉS — a teljes útvonal a súgóban.
    //
    // Két KÜLÖNBÖZŐ mappa azonos alapnévvel a lapos listán
    // megkülönböztethetetlen volt. Nem elméleti gond: a
    // duplikátum-kereső minden forrásmappában saját
    // „Duplikátumok" alkönyvtárat hoz létre, tehát a
    // felhasználónál rendszeresen keletkezik több ilyen nevű
    // mappa — a tulajdonos ezt hibás duplikációnak látta
    // (#1909 → #1923; a mérés szerint duplikáció NINCS, a
    // `folders.path` egyedi).
    //
    // ⚠️ Az EREDETI ilyenkor SEMMIT nem mutat — három
    // független forrásból mérve (#2162):
    //   1. a szövegtár 3524 bejegyzése közt nincs mappasor-
    //      súgó és nincs útvonal-tipp;
    //   2. a 141 erőforrás-fa közül a mappalistát EGYETLEN
    //      helyen definiálja, a Mappakezelő PÁRBESZÉDBEN
    //      (`foldermgr/foldertree`) — a bal hasáb listájának
    //      nincs saját eleme;
    //   3. a panel-gyökér sem tartalmaz mappalista-elemet.
    //
    // Ezért ez NEM „javítás", hanem kimondott többlet. A
    // LÁTHATÓ felirat változatlan marad (csak az alapnév),
    // tehát a felület az eredetivel egyező; a különbség csak
    // rámutatáskor jelenik meg.
    ToolTip.visible: kind === "folder" && folderRowMouse.containsMouse
    ToolTip.text: offline
        ? path + "\n" + qsTr("Currently unavailable — the folder stays in the database, thumbnails come from the cache.")
        : path
    ToolTip.delay: Theme.tooltipDelay
    MouseArea {
        id: folderRowMouse
        objectName: "folderRowMouse"
        // #3461: a Rejtett mappák fejléce is kap egeret, de
        // CSAK a jobb gombra (helyi menü) — kijelölni nem lehet
        enabled: kind === "folder" || kind === "hidden"
        hoverEnabled: kind === "folder"
        anchors.fill: parent
        // #5105: húzás közben a lista görgetője ne vegye át
        // az egeret — különben a ledobás sosem indul el
        preventStealing: kind === "folder"
        acceptedButtons: kind === "hidden"
            ? Qt.RightButton : (Qt.LeftButton | Qt.RightButton)
        property bool draggingFolder: false
        property bool didDragFolder: false
        property real dragPressX: 0
        property real dragPressY: 0
        readonly property string payload: "folders"
        readonly property string folderPath: path
        // #5105: a húzás „teste" az egeret követő elem —
        // a sor maga nem mozdul, így a DropArea-találat
        // ennek a helyzetét nézi.
        Item {
            id: folderDragProxy
            objectName: "folderDragProxy"
            width: 1; height: 1
            readonly property string payload: "folders"
            readonly property string folderPath: path
            Drag.active: kind === "folder"
                && folderRowMouse.draggingFolder
            Drag.dragType: Drag.Internal
            Drag.supportedActions: Qt.MoveAction
        }
        onPressed: function(mouse) {
            if (kind !== "folder" || mouse.button !== Qt.LeftButton)
                return
            dragPressX = mouse.x
            dragPressY = mouse.y
            draggingFolder = false
            didDragFolder = false
        }
        onPositionChanged: function(mouse) {
            if (!pressed || kind !== "folder") return
            folderDragProxy.x = mouse.x
            folderDragProxy.y = mouse.y
            if (Math.abs(mouse.x - dragPressX)
                    + Math.abs(mouse.y - dragPressY) > 8) {
                draggingFolder = true
                didDragFolder = true
            }
        }
        onReleased: function(mouse) {
            if (draggingFolder) {
                folderDragProxy.Drag.drop()
                draggingFolder = false
                didDragFolder = true
            }
        }
        onClicked: function(mouse) {
            if (kind === "hidden") {
                folderPane.openHiddenCollectionContextMenu(name)
                return
            }
            listView.forceActiveFocus()   // kurzorgombokhoz (#77)
            if (mouse.button === Qt.RightButton) {
                folderPane.openFolderContextMenu(path)
                return
            }
            if (didDragFolder) {
                didDragFolder = false
                return
            }
            // #3681: mentés-szűrő módban a sor egy pipa —
            // a kattintás jelöl/jelöletlenít, nem nyit meg
            if (folderPane.mentesSzuroAktiv) {
                folderPane.mentesPipaldKert(
                    path, folderPane.mentesPipaltMappak.indexOf(path) < 0)
                return
            }
            folderPane.folderChosen(path)
        }
    }
    // #5007: csak a rács saját fotóhúzását fogadjuk el; a
    // külső fájlok importálása továbbra is az ImportDropArea
    // útján történik. A forrás sorait még a mappaváltás
    // előtt adjuk át, mert a sorra engedés meg is nyithatja
    // a célmappát.
    DropArea {
        id: folderDropArea
        objectName: "folderDropArea_" + path
        anchors.fill: parent
        enabled: kind === "folder"
        onDropped: function(drop) {
            var source = drop.source
            if (!source)
                return
            if (source.payload === "folders") {
                if (!source.folderPath || source.folderPath === path)
                    return
                drop.accept()
                folderPane.folderDroppedOnFolder(source.folderPath, path)
                return
            }
            if (source.payload !== "photos" || !source.photoRows
                    || source.photoRows.length === 0) return
            drop.accept()
            folderPane.photosDroppedOnFolder(
                path, source.photoRows.slice())
        }
    }
}

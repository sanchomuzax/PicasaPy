import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Felső eszköztár (#150-ben kiemelve a Main.qml-ből):
// Importálás | szűrők középen | Picasa-hű kereső jobbra + verzió-címke.
// A keresés-változást jelekkel adja tovább — a debounce-olt javaslat-
// frissítés és a kijelölés-ürítés a Main.qml dolga marad.
Rectangle {
    id: toolbar

    //: #2163: a `Ctrl+F` (`searchcontainer/searchbutton`, `0x005e63bb`) a
    //: mezőre viszi a fókuszt és megnyitja a keresési beállításokat. A
    //: gazdának NEM kell ismernie az eszköztár belső elemeit — ez a függvény
    //: a határ.
    function fokuszAKeresore() {
        searchField.forceActiveFocus()
        searchField.selectAll()
        searchOptionsPopup.open()
    }
    objectName: "mainToolbar"
    // #587: a felső sáv magassága a `thumbui.tre` `searchtop` konstansa —
    // 35 képpont. Ez a SÁV magassága (a panelek innen kezdődnek); a
    // `respack.yt` `buttonbarsets` rétegtéglalapja (800 × 37, y = 4) a
    // sáv HÁTTÉRKÉPE, nem a sávhatár. A normatív lap:
    // `docs/specs/konyvtar-ablak-meretek.md` 2. szakasz.
    height: 35
    color: Theme.chromeBg

    // a keresőmező tartalma (a Main a mappa-választásnál olvassa)
    readonly property alias searchText: searchField.text
    // #4137: a kameramappa és a méret tárolása az alkalmazás QSettings-én
    // át történik. A QML-funkcionális próba nem indít valódi kamerát, ezért
    // ott a panel tároló nélkül, nem elérhető állapotban is megnyitható.
    readonly property var captureStorage:
        typeof cameraCaptureController === "undefined"
        ? null : cameraCaptureController
    readonly property bool captureControllerAvailable: captureStorage !== null
    // gépelés a keresőben (már beírt szöveggel)
    signal searchEdited(string text)
    // a törlő × gomb: a mező már üres, a nézet álljon vissza
    signal searchCleared()
    // #23: az "Import" gomb — a megnyitást a Main.qml végzi (ImportSourceDialog)
    signal importRequested()
    //: #1421: az eredeti `newalbum` gombja — ugyanaz a párbeszéd,
    //: mint a Fájl ▸ Új album… (a bináris szerint a menütétel is a
    //: `thumbui/newalbum` kattintást szimulálja, ld. az
    //: eszköztár-viselkedés spec 2. szakaszát).
    signal newAlbumRequested()
    //: #1421: az eredeti `timelinebutton` — ugyanaz a nézetváltás,
    //: mint a Nézet ▸ Időrend (Ctrl+5).
    //: A nézet nyitva van-e — a gomb aktív állapotához. A hívó köti;
    //: alapértéke false, hogy a próbák stub-jain se legyen undefined.
    //: #1421: a `flatview`/`folderview` pár — a bal hasáb lapos vagy
    //: fa elrendezése. A vezérlő a `FolderHierarchyController`, ami
    //: ÖNÁLLÓ context property; a hívó köti be, a próbák stub-jain
    //: nincs rajta — ezért van alapértéke.
    property bool treeViewActive: false
    signal flatViewRequested()
    //: #1421: a `folderviewpopup` (▾) gomb — MÉRVE (a bináris
    //: `0x005e2000` kezelője, `picasa-konyvtar-eszkoztar-viselkedes.md` 4.):
    //: NEM önálló beállítás-panelt nyit, hanem UGYANAZT a lenyíló menüt,
    //: ami a `Nézet ▸ Mappanézet` almenü. A menü ezért NEM készül újra
    //: itt: a jelzést a Main.qml a menüsor meglévő almenüjének
    //: megnyitására fordítja — egy definíció, két belépési pont.
    signal folderViewMenuRequested(var anchorItem)
    signal treeViewRequested()

    function clearSearch() {
        searchField.clear()
    }

    //: #1399: a menüből indított keresés — a szín-menüpontok ezen át írnak a
    //: keresőmezőbe. MÉRVE (`0x0065b7b0`, hat lépés): az eredeti a mező
    //: SZÖVEGÉT állítja, a kurzort a szöveg VÉGÉRE viszi kijelölés nélkül
    //: (`EM_SETSEL 0xFFFF,0xFFFF`), majd lefuttatja a keresést — vagyis
    //: pontosan az történik, mintha a felhasználó beírta volna.
    function keresesSzoveggel(szoveg) {
        searchField.text = szoveg
        searchField.cursorPosition = searchField.text.length
        toolbar.searchEdited(searchField.text)
    }


    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width; height: 1
        color: Theme.chromeBorder
    }
    // #3603: a bal oldali NÉGY gomb fix bal-felső horgonyú (`m_offsetLT`,
    // `thumbui.tre`) — nem egy balról-jobbra folyó sor térközeiből adódik
    // ki, hanem explicit x/y-nal: 6 / 124 / 160 / 225, mind y=9 (a
    // képernyőkép-mérés szerint a gombok teteje a sáv tetejétől 9). A
    // szűrőzóna és a keresőmező az ABLAKSZÉLESSÉG arányában mozog
    // (`searchcontainer.tre` `XConstraint 0,.4,0` … `1,1,-70`), ezért ők
    // sem egy flow-tag részei, hanem a `toolbar.width`-ből számolt x/w —
    // ld. lent `searchContainerLeft`/`searchContainerRight`.
    //
    // A #423 szűk ablakos elrejtése (`toolbarCompact`) csak ott dolgozik,
    // ahol az eredeti képlete már nem fér ki. A négy bal gomb SOHA nem
    // rejtőzik el (fix horgonyúak, 247-ig érnek). A képletben a szűrőzóna
    // és a mező között állandó 16 px van (0,4·W + 222 … 0,4·W + 238), a
    // verziófelirat pedig a mező mögötti 47 px-en él, tehát ezek nem
    // ütközhetnek. Két határ marad:
    //   - a szűrőzóna bal széle (0,4·W − 2) eléri a bal gombsort (247):
    //     W < 622,5;
    //   - a mező (0,6·W − 285 széles) a 120 px-es padló alá szorulna:
    //     W < 675.
    // A küszöb a kettő közül a nagyobb: 675 px. Ez alatt a szűrőzóna
    // elrejtőzik, és a mező a gombsor mögé húzódik a felszabadult helyre
    // (#3603). A főablak legkisebb szélessége (a tálca igénye) ma ennél
    // nagyobb, a küszöb tehát a sáv saját biztosítéka.
    readonly property real leftButtonsRight: 247
    readonly property real searchMinWidth: 120
    readonly property real compactWidth: Math.max(
        (leftButtonsRight + 2) / 0.4,
        (searchMinWidth + 285) / 0.6)
    readonly property bool toolbarCompact: width < compactWidth
    // `searchcontainer.tre:352-355` — a konténer bal/jobb éle
    readonly property real searchContainerLeft: width * 0.4
    readonly property real searchContainerRight: width - 70
    // a látható mező (`searchbase`) jobb széle: a konténeren túl 23-mal
    readonly property real searchBoxRight: searchContainerRight + 23
    Item {
        id: content
        anchors.fill: parent
        PicasaButton {
            objectName: "toolbarImportButton"
            text: qsTr("Import")
            enabled: true
            // #587: az eredeti `importbutton` 111 × 22 (a `respack.yt`
            // mért téglalapja, `konyvtar-ablak-meretek.md` 2. szakasz).
            // A magasság 22 azért fér el a feliratnak, mert a
            // `PicasaButton` függőleges kitöltése 0 (ld. ott a #992
            // kommentjét) — a 12px-es betű teljes sormagassága belefér.
            // #3603: fix bal-felső horgony — x 6, y 9 (`thumbui.tre:452`,
            // képernyőkép-mérve).
            x: 6; y: 9
            width: 111
            height: 22
            //: #1929: `thumbui/importbutton` — az EREDETI súgója, szó
            //: szerint (`referencia/ui-leltar.csv`). Eddig nem volt súgója.
            ToolTip.text: qsTr("Get photos from a camera, scanner, or other media")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: toolbar.importRequested()
        }
        // #1421: az `newalbum` gomb — a FUNKCIÓ már megvolt (a Fájl ▸ Új
        // album… párbeszéde), csak az eszköztárról hiányzott. A bináris
        // szerint a menütétel maga is a `thumbui/newalbum` kattintást
        // szimulálja, tehát a kettő UGYANAZ az út.
        //
        // Mért méret: 29 × 22 (`konyvtar-ablak-meretek.md` 2.). A gomb az
        // eredetiben MINDIG aktív (a `.tre`-ben nincs feltétele).
        //
        // #1421: az `newalbum` gomb — a FUNKCIÓ már megvolt (a Fájl ▸ Új
        // album… párbeszéde), csak az eszköztárról hiányzott. A bináris
        // szerint a menütétel maga is a `thumbui/newalbum` kattintást
        // szimulálja, tehát a kettő UGYANAZ az út.
        //
        // Mért méret: 29 × 22, és az eredetiben IKONOS, nem feliratos
        // (`newalbum_icon` 19 × 14 — `konyvtar-ablak-meretek.md` 2.).
        // ⚠️ Először feliratos gombnak írtam meg: a magyar „Új album" a
        // 29 × 22-be NEM fér bele (a felirat-őr mérte: 15,1 × 24,5 a
        // 19 × 22-es helyen, 2,5 px túllógás). A mért méret tehát maga
        // mondta meg, hogy ikonnak kell lennie — a glif a szűrő-zóna
        // idiómáját követi (★ ▶ ⚲).
        //
        // A gomb az eredetiben MINDIG aktív (a `.tre`-ben nincs feltétele),
        // és szűk ablakban sem rejtőzik el (#3603).
        Item {
            objectName: "toolbarNewAlbumButton"
            // #3603: fix bal-felső horgony — x 124, y 9 (`thumbui.tre:375`).
            x: 124; y: 9
            width: 29
            height: 22
            Rectangle {
                anchors.centerIn: parent
                width: 22; height: 20; radius: 2
                color: "transparent"
                border.width: newAlbumHover.hovered ? 1 : 0
                border.color: Theme.selectionBlue
                Text {
                    anchors.centerIn: parent
                    text: "＋"
                    font.pixelSize: 13
                    color: newAlbumHover.hovered ? Theme.selectionBlue : "#8f8b83"
                }
            }
            //: `newalbum` — az eredeti buboréksúgója
            ToolTip.text: qsTr("Create a new album")
            ToolTip.visible: newAlbumHover.hovered
            ToolTip.delay: Theme.tooltipDelay
            HoverHandler { id: newAlbumHover }
            TapHandler { onTapped: toolbar.newAlbumRequested() }
        }
        // #1421: a `flatview` / `folderview` pár — a NÉZET már megvolt
        // (Nézet ▸ Mappanézet, #1454), csak gomb nem vezetett hozzá.
        //
        // Mért méret: egyenként 30 × 22, egy `hviewtoggle` csoportban
        // (60 × 22) — `konyvtar-ablak-meretek.md` 2.
        //
        // ⚠️ KIZÁRÓ pár, nem két független kapcsoló: pontosan az egyik
        // aktív. Ikonos, mint az eredeti (a `newalbum` tanulsága: a
        // 30 × 22-be felirat nem fér).
        Row {
            objectName: "toolbarFolderViewToggle"
            spacing: 0
            // #3603: fix bal-felső horgony — x 160, y 9 (`thumbui.tre:406-415`).
            x: 160; y: 9
            width: 60
            height: 22
            Rectangle {
                objectName: "toolbarFlatViewButton"
                //: #885: LENYOMÁSRA sül el (`Property mousedown 1`) — az
                //: eredetiben a nézetváltók és a szűrők azonnal hatnak.
                property bool lenyomasra: true
                width: 30; height: 22; radius: 2
                readonly property bool aktiv: !toolbar.treeViewActive
                color: aktiv ? "#ffffff" : "transparent"
                border.width: aktiv ? 1 : 0
                border.color: Theme.selectionBlue
                Text {
                    anchors.centerIn: parent
                    text: "▤"
                    font.pixelSize: 12
                    color: parent.aktiv ? Theme.selectionBlue
                           : (flatViewHover.hovered ? Theme.selectionBlue : "#8f8b83")
                }
                //: `flatview` — az eredeti buboréksúgója
                ToolTip.text: qsTr("Set view to show flat folder structure")
                ToolTip.visible: flatViewHover.hovered
                ToolTip.delay: Theme.tooltipDelay
                HoverHandler { id: flatViewHover }
                TapHandler {
                    //: #885: lenyomásra, nem felengedésre
                    onPressedChanged: if (pressed) toolbar.flatViewRequested()
                }
            }
            Rectangle {
                objectName: "toolbarTreeViewButton"
                //: #885: LENYOMÁSRA sül el (`Property mousedown 1`) — az
                //: eredetiben a nézetváltók és a szűrők azonnal hatnak.
                property bool lenyomasra: true
                width: 30; height: 22; radius: 2
                readonly property bool aktiv: toolbar.treeViewActive
                color: aktiv ? "#ffffff" : "transparent"
                border.width: aktiv ? 1 : 0
                border.color: Theme.selectionBlue
                Text {
                    anchors.centerIn: parent
                    text: "⊞"
                    font.pixelSize: 12
                    color: parent.aktiv ? Theme.selectionBlue
                           : (treeViewHover.hovered ? Theme.selectionBlue : "#8f8b83")
                }
                //: `folderview` — az eredeti buboréksúgója
                ToolTip.text: qsTr("Set view to show folder tree structure")
                ToolTip.visible: treeViewHover.hovered
                ToolTip.delay: Theme.tooltipDelay
                HoverHandler { id: treeViewHover }
                TapHandler {
                    //: #885: lenyomásra, nem felengedésre
                    onPressedChanged: if (pressed) toolbar.treeViewRequested()
                }
            }
        }
        // #1421: a `folderviewpopup` — MÉRT méret 22 × 22, és a mérés
        // szerint ez ÖNÁLLÓ elem, nem a `hviewtoggle` 60 × 22-es csoport
        // része (`konyvtar-ablak-meretek.md` 2.) — a pár csoportja ezért
        // marad 60 széles.
        //
        // A kezelője a binárisban UGYANAZ a scope-kulcsos függvény, mint a
        // páré (`0x00575130`), és a menü tételei a `Nézet ▸ Mappanézet`
        // almenü tételei (spec 4/b) — ezért itt nem építünk új menüt.
        Rectangle {
            objectName: "toolbarFolderViewPopupButton"
            // #3603: fix bal-felső horgony — x 225, y 9 (`thumbui.tre:421`).
            x: 225; y: 9
            width: 22; height: 22; radius: 2
            color: folderViewPopupHover.hovered ? "#ffffff" : "transparent"
            border.width: folderViewPopupHover.hovered ? 1 : 0
            border.color: Theme.selectionBlue
            Text {
                anchors.centerIn: parent
                text: "▾"
                font.pixelSize: 12
                color: folderViewPopupHover.hovered ? Theme.selectionBlue : "#8f8b83"
            }
            //: `folderviewpopup` — a nézet-beállítások lenyílója
            //: #3476: az eredeti `thumbui/folderviewpopup` szövege
            ToolTip.text: qsTr("View options")
            ToolTip.visible: folderViewPopupHover.hovered
            ToolTip.delay: Theme.tooltipDelay
            HoverHandler { id: folderViewPopupHover }
            //: #885: `thumbui/folderviewpopup` — a menü LENYOMÁSRA nyílik
            //: (`Property mousedown 1`); menünyitásnál ez a mért viselkedés.
            TapHandler {
                onPressedChanged: if (pressed) toolbar.folderViewMenuRequested(parent)
            }
        }
        // #4137: belépés a kamera előnézetéhez. A vezérlő nélküli tesztkörnyezet
        // nem kínálja fel; a panel maga jelzi, ha a kamera nem érhető el.
        Rectangle {
            objectName: "toolbarWebcamCaptureButton"
            Accessible.role: Accessible.Button
            Accessible.name: qsTr("Capture")
            enabled: toolbar.captureControllerAvailable
            x: 252; y: 9
            width: 22; height: 22; radius: 2
            color: cameraCaptureHover.hovered ? "#ffffff" : "transparent"
            border.width: cameraCaptureHover.hovered ? 1 : 0
            border.color: Theme.selectionBlue
            Text {
                objectName: "panelroot/capturemovietab"
                anchors.centerIn: parent
                text: "◉"
                font.pixelSize: 13
                color: cameraCaptureHover.hovered ? Theme.selectionBlue : "#8f8b83"
            }
            ToolTip.text: qsTr("Open camera capture panel")
            ToolTip.visible: cameraCaptureHover.hovered
            ToolTip.delay: Theme.tooltipDelay
            HoverHandler { id: cameraCaptureHover }
            TapHandler {
                onTapped: {
                    if (captureMoviePanelLoader.item)
                        captureMoviePanelLoader.item.open()
                    else
                        captureMoviePanelLoader.active = true
                }
            }
        }
        Component {
            id: captureMoviePanelComponent
            CaptureMoviePanelPopup { storage: toolbar.captureStorage }
        }
        Loader {
            id: captureMoviePanelLoader
            objectName: "captureMoviePanelLoader"
            active: false
            sourceComponent: captureMoviePanelComponent
            onLoaded: item.open()
        }
        // #1421: az `timelinebutton` — a NÉZET már megvolt (Nézet ▸ Időrend,
        // Ctrl+5, `timeline_controller.py`), csak az eszköztárról hiányzott.
        //
        // Mért méret: 132 × 28 (`konyvtar-ablak-meretek.md` 2.) — ez az
        // egyetlen FELIRATOS a három kihelyezett gomb közül, ezért fér is
        // bele a szöveg (az `newalbum` 29 × 22-je nem fért, ld. ott).
        //
        // ⚠️ Szűk ablaknál elrejtőzik (#423), és `Layout.minimumWidth: 0`,
        // hogy a zsugorodási sorrend érintetlen maradjon.
        // #1903: az „Időrend" váltógomb ELTÁVOLÍTVA a fejlécből.
        //
        // A tulajdonos élesben jelentette (két képernyőképpel), és a
        // bináris megerősíti: az eredeti Időrend NEM rácsnézet, hanem
        // TELJES KÉPERNYŐS, ANIMÁLT BEMUTATÓ a diavetítő motorján
        // (`oneup/timeline` + `BigSlideshow2`, `0x008037e0`), saját
        // RÁTÉTES vezérlősávval (`overlays/timeline` · `timelinedot` ·
        // `sliderthumb` · `startbutton` · `exit`, `0x007fb210`).
        //
        // ⇒ A fejlécben ilyen gomb az eredetiben NEM LÉTEZIK: az Időrend
        // vezérlői a teljes képernyős rátéten ülnek. Amíg a valódi nézet
        // nincs megépítve, a belépési pont nem kínálhatja fel magát —
        // egy kattintható gomb, ami mást ad, mint amit ígér, rosszabb,
        // mint a hiánya (#936).
        //
        // A `Nézet ▸ Időrend` menütétel HELYE megmarad (az eredetiben
        // létezik), csak inaktív — ld. PicasaMenuBar.qml.
        // #1808 → VISSZAVONVA: a rács-nagyító KAPCSOLÓGOMBJA nincs itt.
        //
        // A gomb `thumbui/loupehit`-ből mért, és a lánca MŰKÖDIK is — a
        // valódi, kirajzolt ablakban mérve: kattintásra `loupeActive`
        // igazra vált, és a rácson NYOMVA HÚZVA megjelenik a 2,5×-ös
        // lencse (`feedLoupe`). Mégis kikerült, mert a felhasználónak
        // élesben **semmit nem csinál**, és ennek két oka van:
        //
        // 1. a kapcsolt állapotot csak egy 29×22-es, feliratlan ikon
        //    színe jelzi — a felületen semmi nem mondja, hogy „a nagyító
        //    fel van húzva";
        // 2. a puszta KATTINTÁS a képen nem csinál semmit: nyomva
        //    HÚZNI kell. Ez a felfedezhetetlen része.
        //
        // A #1808 tesztkészlete ezt nem foghatta meg: mind a tizennégy
        // állítása a QML FORRÁSSZÖVEGÉT olvasta, nem kirajzolt ablakot
        // (0,25 mp alatt lefutott). A lánc végpontjai megvoltak, a
        // felhasználói élmény nem — pontosan a #1662 osztálya.
        //
        // A rács oldali réteg (`LightboxFeed.qml` `feedLoupeArea`)
        // SZÁNDÉKOSAN a helyén marad: működik, mérve van, és a
        // visszakapcsolása egy felfedezhető felülettel külön jegy. Egy
        // kattintható vezérlő, ami mást ad, mint amit ígér, rosszabb,
        // mint a hiánya (#936, #1903).
        //
        // #1911 — A KAPCSOLÓ VISSZAKERÜLT, de NEM IDE, hanem az ALSÓ
        // SÁVBA (`TrayBar.qml`, `trayLoupeButton`). Ez nem áthelyezés
        // ízlés szerint: mérve (`docs/specs/racs-nagyito.md` 1. és 5.)
        // az eredeti belépési pontja a `thumbui/loupehit`, egy 25 × 19-es
        // gomb a `scale_group`-ban, a nagyítás-csúszka ELŐTT — az
        // eszköztárban az EREDETIBEN SINCS ilyen gomb.
        //
        // Ezért marad igaz a fenti „nincs itt", és ezért NE tegye vissza
        // ide egy későbbi kör „hiányzó gombként". A felfedezhetőséget a
        // gomb buboréksúgója adja („húzd a képek fölött"); az eredeti
        // erre nem ad támpontot — mérve külön egérmutatót SEM használ.
        // #423: NEM Column, hanem Item — a "Szűrők" felirat a Picasa
        // `searchcontainer.tre`-jének `filter_label` kényszere szerint
        // (`YConstraint 0, 0, -4`) a csík TETEJÉTŐL −4px-re ül, azaz a
        // csíkon BELÜL, az ikonsor FÖLÉ kicsúszva jelenik meg — nem külön
        // sorba kerül (amit egy Column spacing:0 flow-ja nem tudna
        // kifejezni, mert az mindig a felirat alá, nem fölé/bele tenné
        // a következő sort).
        //
        // #3603: a bal széle `0,4 · W − 2` (`searchcontainer.tre:352-355`,
        // `filterbase` `m_offsetLT`), tehát az ABLAKSZÉLESSÉGGEL mozog —
        // nem a bal gombsor utáni folyó hely.
        Item {
            id: filterZone
            objectName: "toolbarFilterZone"
            x: toolbar.searchContainerLeft - 2
            y: Math.round((toolbar.height - height) / 2)
            // szűk ablaknál a középső szűrő-zóna rejtőzik el — a sáv maga
            // nem törik, csak ez a blokk tűnik el (#423)
            visible: !toolbar.toolbarCompact
            width: filterIconsRow.width
            height: filterIconsRow.y + filterIconsRow.height
            // #839: a szűrők súgója NEM lebegő buborékban jelenik meg, hanem
            // EZEN a feliraton — a `searchcontainer.tre` mind az öt
            // szűrőgombjára ugyanezt a sort adja:
            //
            //   SharedHandler searchcontainer/tip hottip searchcontainer/filter_label
            //
            // (`hottip` = a súgó célja a `filter_label`, nem egy lebegő
            // buborék). Ezért a szűrőkön nincs `ToolTip`: a feliratuk ide
            // kerül, és mutatóelvétel után visszaáll a „Szűrők".
            Text {
                id: filtersLabel
                objectName: "toolbarFiltersLabel"
                anchors.horizontalCenter: parent.horizontalCenter
                y: -4
                //: a mutató alatti szűrő súgója, ha van ilyen
                readonly property string hoveredTip:
                    starFilter.hovered
                        ? qsTr("Show starred photos only")
                        : faceFilterHover.hovered
                            ? qsTr("Show only photos with faces")
                            : movieFilterHover.hovered
                                ? qsTr("Show movies only")
                                : dupeFilterHover.hovered
                                    ? qsTr("Show duplicate files only")
                                    : geoFilterHover.hovered
                                        ? qsTr("Show only photos with geotag")
                                        : dateRangeHover.hovered
                                            ? qsTr("Filter by date range")
                                            : ""
                text: filtersLabel.hoveredTip !== ""
                    ? filtersLabel.hoveredTip : qsTr("Filters")
                // #839: a mért betű `m_displayfont12` (`fontmacros_win.tre`
                // 43–47. sor: `fontsize 12`), nem a korábbi 9.
                font.pixelSize: 12
                color: Theme.textGray
                // a súgó hosszabb a „Szűrők"-nél: a szűrő-zónán belül marad,
                // és inkább levágódik, mint hogy a szomszéd sávot tolja
                width: Math.max(filterIconsRow.width, implicitWidth) > filterIconsRow.width
                    ? filterIconsRow.width : implicitWidth
                elide: Text.ElideRight
                horizontalAlignment: Text.AlignHCenter
            }
            Row {
                id: filterIconsRow
                objectName: "searchgroup"
                y: 9
                spacing: 3

                // szűrő-kapcsolók (kézikönyv 09): ★ ☺ ⚲ ▤ + csúszka;
                // a bekapcsolt szűrő tónusa jelölő kék
                Rectangle {
                    // #305: null-őr — a controller a QML-engine
                    // leépítésekor átmenetileg null lehet
                    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
                    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
                    readonly property bool ctlFilterActive:
                        (controller && controller.filterActive !== undefined)
                            ? controller.filterActive : false
                    objectName: "starFilterButton"
                    width: 22; height: 20; radius: 2
                    //: #839: a MÉRT állapotok — aktívan ZÖLD gomb fehér
                    //: glifával, rámutatva világoszöld, egyébként üres. A
                    //: korábbi fehér doboz + kék keret a MI találmányunk
                    //: volt; a `respack.yt` `globalbuttons_filter_*` három
                    //: állapota mind a zöld családba tartozik (ld. `Theme`).
                    color: ctlFilterActive
                           ? Theme.szuroHatterAktiv
                           : (starFilter.hovered ? Theme.szuroHatterRamutat
                                                 : "transparent")
                    border.width: 0
                    Text {
                        anchors.centerIn: parent
                        objectName: "starFilterGlyph"
                        text: "★"
                        font.pixelSize: 13
                        //: #839: a be/ki állapot a glif TÓNUSA (mérve: a
                        //: maszk bájtra azonos a két rétegben)
                        color: parent.ctlFilterActive
                               ? Theme.szuroGlifBe : Theme.szuroGlifKi
                    }
                    HoverHandler { id: starFilter }
                    TapHandler {
                        //: #885: lenyomásra, nem felengedésre
                        onPressedChanged: if (pressed) {
                            controller.filterActive
                                ? controller.clearFilter()
                                : controller.showStarred()
                        }
                    }
                }
                Item {   // #1830: „arcos képek" — az eredeti `facesearch`
                    objectName: "faceFilter"
                    //: #885: LENYOMÁSRA sül el (`Property mousedown 1`) — az
                    //: eredetiben a nézetváltók és a szűrők azonnal hatnak.
                    property bool lenyomasra: true
                    // ⚠️ HELYESBÍTÉS. Itt korábban helyfoglaló állt, ezzel
                    // az indoklással: „az ini `faces=` adata NINCS az
                    // indexben, ezért ez a szűrő ma nem építhető meg a
                    // meglévő adatokból". Az első fele igaz, a
                    // következtetés téves volt: az „Emberek" gyűjtemény
                    // (`index/people.py`) ÉPP EZT az ini-adatot söpri be
                    // minden hívásnál, és a `person_photos` ugyanezen az
                    // úton ad vissza fotó-rekordokat. A hiányzó darab
                    // egyetlen lekérdezés volt (`photos_with_faces`), nem
                    // egy felismerő motor.
                    //
                    // A megnevezetlen arc is arc: a szűrő nem azt kérdezi,
                    // kit ismerünk fel, hanem hogy van-e bejelölt arc.
                    width: 22; height: 20
                    readonly property bool aktiv:
                        (controller && controller.viewModeName !== undefined)
                            ? controller.viewModeName === "faces" : false
                    Rectangle {
                        anchors.fill: parent
                        radius: 2
                        //: #839: MÉRT állapotok — aktívan zöld gomb (a
                        //: `globalbuttons_filter_p` közepe), egyébként üres
                        color: parent.aktiv
                               ? Theme.szuroHatterAktiv : "transparent"
                        border.width: 0
                    }
                    Text {
                        anchors.centerIn: parent
                        objectName: "faceFilterGlyph"
                        text: "☺"
                        font.pixelSize: 13
                        //: #839: a be/ki állapot a glif TÓNUSA (mérve) —
                        //: kikapcsolva tompa zöld, bekapcsolva fehér
                        color: parent.aktiv
                               ? Theme.szuroGlifBe : Theme.szuroGlifKi
                    }
                    // #839: itt NINCS lebegő ToolTip — a súgó a „Szűrők"
                    // felirat helyén jelenik meg (`hottip`, ld. ott)
                    HoverHandler { id: faceFilterHover }
                    TapHandler {
                        //: #885: lenyomásra, nem felengedésre
                        onPressedChanged: if (pressed) {
                            parent.aktiv
                                ? controller.clearFilter()
                                : controller.showFacesOnly()
                        }
                    }
                }
                Item {   // #1830: „csak filmek" — az eredeti `moviesearch`
                    objectName: "movieFilter"
                    //: #885: LENYOMÁSRA sül el (`Property mousedown 1`) — az
                    //: eredetiben a nézetváltók és a szűrők azonnal hatnak.
                    property bool lenyomasra: true
                    width: 22; height: 20
                    readonly property bool aktiv:
                        (controller && controller.viewModeName !== undefined)
                            ? controller.viewModeName === "videos" : false
                    Rectangle {
                        anchors.fill: parent
                        radius: 2
                        //: #839: MÉRT állapotok — aktívan zöld gomb (a
                        //: `globalbuttons_filter_p` közepe), egyébként üres
                        color: parent.aktiv
                               ? Theme.szuroHatterAktiv : "transparent"
                        border.width: 0
                    }
                    Text {
                        anchors.centerIn: parent
                        objectName: "movieFilterGlyph"
                        text: "▶"
                        font.pixelSize: 11
                        //: #839: a be/ki állapot a glif TÓNUSA (mérve) —
                        //: kikapcsolva tompa zöld, bekapcsolva fehér
                        color: parent.aktiv
                               ? Theme.szuroGlifBe : Theme.szuroGlifKi
                    }
                    // #839: itt NINCS lebegő ToolTip — a súgó a „Szűrők"
                    // felirat helyén jelenik meg (`hottip`, ld. ott)
                    HoverHandler { id: movieFilterHover }
                    TapHandler {
                        //: #885: lenyomásra, nem felengedésre
                        onPressedChanged: if (pressed) {
                            parent.aktiv
                                ? controller.clearFilter()
                                : controller.showVideosOnly()
                        }
                    }
                }
                Item {   // #2174: a duplikátum-kapcsoló (`searchoptions/
                         // dupesearch`). MÉRVE, hogy alapból REJTETT: a
                         // főablak-építő elrejti (`0x0040c8c9`), és csak a
                         // mód bekapcsolása hozza elő — ezért nem lehet
                         // vele BEkapcsolni a módot, csak kivezetni belőle
                         // (a bekapcsolás a menüparancs dolga).
                    objectName: "dupeFilter"
                    //: #885: LENYOMÁSRA sül el (`Property mousedown 1`) — az
                    //: eredetiben a nézetváltók és a szűrők azonnal hatnak.
                    property bool lenyomasra: true
                    width: 22; height: 20
                    readonly property bool aktiv:
                        (controller && controller.viewModeName !== undefined)
                            ? controller.viewModeName === "dupes" : false
                    visible: aktiv
                    Rectangle {
                        anchors.fill: parent
                        radius: 2
                        //: #839: MÉRT állapotok — aktívan zöld gomb (a
                        //: `globalbuttons_filter_p` közepe), egyébként üres
                        color: parent.aktiv
                               ? Theme.szuroHatterAktiv : "transparent"
                        border.width: 0
                    }
                    Text {
                        anchors.centerIn: parent
                        //: két egymásra csúszó lap — a másodpéldány jele
                        text: "⧉"
                        font.pixelSize: 12
                        //: #839: a be/ki állapot a glif TÓNUSA (mérve) —
                        //: kikapcsolva tompa zöld, bekapcsolva fehér
                        color: parent.aktiv
                               ? Theme.szuroGlifBe : Theme.szuroGlifKi
                    }
                    // #839: itt NINCS lebegő ToolTip — a súgó a „Szűrők"
                    // felirat helyén jelenik meg (`hottip`, ld. ott)
                    HoverHandler { id: dupeFilterHover }
                    TapHandler {
                        // KÖZÖS út a menüparanccsal (#1398): az eredetiben a
                        // kapcsoló és az `ID_DUPES` bitre ugyanazt hívja.
                        //: #885: lenyomásra, nem felengedésre
                        onPressedChanged: if (pressed) {
                            parent.aktiv
                                ? controller.clearFilter()
                                : controller.showDuplicateFiles()
                        }
                    }
                }
                Item {   // geo-szűrő (#30) — csak akkor él, ha van geocímkés kép
                    objectName: "geoFilter"
                    //: #885: LENYOMÁSRA sül el (`Property mousedown 1`) — az
                    //: eredetiben a nézetváltók és a szűrők azonnal hatnak.
                    property bool lenyomasra: true
                    width: 22; height: 20
                    readonly property bool ctlHasGeo:
                        controller ? controller.geoMarkerCount > 0 : false
                    // #361: saját helyjelölő-tű SVG a korábbi "⚲"
                    // unicode-glif helyett (a hover/inaktív állapotot most
                    // opacity vezérli — a piros tű már önmagában "geo"-
                    // hangulatú, nem kell a Theme kék hoverje a színhez).
                    Image {
                        objectName: "geoFilterIcon"
                        anchors.fill: parent
                        anchors.margins: 3
                        source: "icons/geo-pin.svg"
                        fillMode: Image.PreserveAspectFit
                        opacity: parent.ctlHasGeo
                                 ? (geoFilterHover.hovered ? 1.0 : 0.85)
                                 : 0.35
                    }
                    // #839: itt NINCS lebegő ToolTip — a súgó a „Szűrők"
                    // felirat helyén jelenik meg (`hottip`, ld. ott)
                    HoverHandler { id: geoFilterHover }
                    TapHandler {
                        enabled: parent.ctlHasGeo
                        //: #885: lenyomásra, nem felengedésre
                        onPressedChanged: if (pressed) {
                            controller.filterActive
                                ? controller.clearFilter()
                                : controller.showGeotagged()
                        }
                    }
                }
                Text {   // mozgókép / méret
                    width: 22; height: 20
                    text: "▤"; font.pixelSize: 12; color: Theme.placeholderText
                    opacity: 0.45
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                Item { width: 6; height: 1 }
                //: #1830: az idő-csúszka — az eredeti `timeslider`.
                //:
                //: ⚠️ NEM tartományt választ, hiába ezt sejti a buboréksúgó
                //: felirata („Filter by date range"): egyetlen érték adja meg
                //: a MEGENGEDETT legnagyobb KORT. A félrevezető felirat az
                //: EREDETI sajátja (`searchcontainer.tre:101–102`), ezért
                //: szó szerint átvesszük — a mért viselkedés a
                //: `app/kor_szuro.py`-ban áll.
                //:
                //: A nulla NEM „nagyon régi", hanem „nincs szűrés" — a
                //: vezérlő nulla értéknél kikapcsolja a szűrőt.
                PicasaSlider {
                    objectName: "dateRangeFilterSlider"
                    width: 90; height: 20
                    from: 0.0
                    to: 1.0
                    anchors.verticalCenter: parent.verticalCenter
                    //: `timecontainer_label` — az eredeti buboréksúgója
                    // #839: a `timecontainer_label` is `hottip
                    // searchcontainer/filter_label` (a `.tre` hatodik ilyen
                    // sora) — a súgó a „Szűrők" felirat helyén jelenik meg
                    HoverHandler { id: dateRangeHover }
                    //: a csúszka mozgatása KÖZBEN nem kérdezünk le: a
                    //: `moved` az elengedésre/lépésre szól, a `valueChanged`
                    //: minden képpontnyi vonszolásra lekérdezné az indexet
                    onMoved: if (controller) controller.setAgeFilter(value)
                }
            }
        }
        // Picasa-hű kereső: fehér mező nagyítóval, törlő ×-szel.
        //
        // #3603: a 388 × 30 (`konyvtar-ablak-meretek.md` 2. szakasz) a
        // `searchcontainer` TERVEZÉSI téglalapja volt, nem a látható
        // mezőé — a látható keret (`searchbase`, `m_offsetLTR`) a mérés
        // szerint 24 magas, és a szélessége az ablaktól függ: bal széle
        // `0,4 · W + 238`, jobb széle `W − 47` (`searchcontainer.tre:352-
        // 355`, a konténer 388-as tervezési szélességéhez mért −23
        // eltolással).
        //
        // A verziófelirat (#706, saját elem — az eredetiben ott semmi
        // nincs) a mező mögötti 47 px-en fér el, ezért a mező jobb széle
        // mindig pontosan `W − 47`. Szűk ablakban (`toolbarCompact`) a bal
        // széle a gombsor mögé kerül, a jobb széle akkor sem mozdul.
        Rectangle {
            id: searchBox
            objectName: "toolbarSearchBox"
            x: toolbar.toolbarCompact
                ? toolbar.leftButtonsRight + 10
                : toolbar.searchContainerLeft + 238
            width: Math.max(0, toolbar.searchBoxRight - x)
            height: 24
            // a képernyőkép-mérés szerint a keret teteje a sáv tetejétől
            // 7 (50 − 43)
            y: 7
            radius: 3
            color: Theme.controlBase
            border.color: Theme.chromeBorder
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                spacing: 5
                Item {   // rajzolt nagyító
                    width: 12; height: 12
                    Rectangle {
                        x: 0; y: 0; width: 9; height: 9; radius: 4.5
                        color: "transparent"
                        border.color: Theme.placeholderText; border.width: 1.5
                    }
                    Rectangle {
                        x: 8; y: 8; width: 4; height: 1.5
                        rotation: 45; color: Theme.placeholderText
                    }
                }
                TextInput {
                    id: searchField
                    objectName: "searchField"
                    Layout.fillWidth: true
                    font.pixelSize: Theme.fontSize
                    color: Theme.ink
                    clip: true
                    verticalAlignment: TextInput.AlignVCenter
                    selectByMouse: true
                    onTextEdited: toolbar.searchEdited(text)
                    Text {
                        visible: searchField.text.length === 0
                                 && !searchField.activeFocus
                        anchors.verticalCenter: parent.verticalCenter
                        text: qsTr("Search")
                        color: Theme.placeholderText
                        font.pixelSize: Theme.fontSize
                    }
                    //: #1526: jobbklikk-menü a keresőmezőn is (a Picasa
                    //: `Address` menüosztálya). A menü MÁR MEGVOLT (#422),
                    //: csak épp arra a mezőre nem volt rákötve, amit a
                    //: felhasználó a leggyakrabban használ — beilleszteni
                    //: eddig csak billentyűvel lehetett ide.
                    TextFieldContextArea {
                        objectName: "searchFieldContextArea"
                    }
                }
                PicasaButton {
                    objectName: "searchbutton"
                    Layout.preferredWidth: 20
                    Layout.preferredHeight: 18
                    visible: searchField.activeFocus
                             || searchField.text.length > 0
                             || searchOptionsPopup.opened
                    text: "⌄"
                    font.pixelSize: 14
                    horizontalPadding: 0
                    Accessible.name: qsTr("Search")
                    onClicked: searchOptionsPopup.opened
                               ? searchOptionsPopup.close()
                               : searchOptionsPopup.open()
                }
                Rectangle {   // törlő gomb, csak ha van mit törölni
                    objectName: "searchClear"
                    visible: searchField.text.length > 0
                    width: 14; height: 14; radius: 7
                    color: searchClearHover.hovered ? "#c94b3d" : "#b0b0b0"
                    Text {
                        anchors.centerIn: parent
                        text: "✕"; color: "white"; font.pixelSize: 8
                        font.bold: true
                    }
                    //: #839: a `searchcontainer.tre` `clearsearch` gombjának
                    //: súgója. A gomb maga már helyesen csak akkor látszik,
                    //: ha van mit törölni (az eredeti `showtarget`-je is
                    //: így viselkedik) — a magyarázat hiányzott róla.
                    ToolTip.text: qsTr("Clear your search")
                    ToolTip.visible: searchClearHover.hovered
                    ToolTip.delay: Theme.tooltipDelay
                    HoverHandler { id: searchClearHover }
                    TapHandler {
                        onTapped: {
                            searchField.clear()
                            toolbar.searchCleared()
                        }
                    }
                }
            }
        }
        Popup {
            id: searchOptionsPopup
            objectName: "searchOptionsPopup"
            x: Math.max(8, searchBox.x + searchBox.width - width)
            y: toolbar.height
            width: 280
            padding: 8
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
            background: Rectangle {
                color: Theme.contentPanel
                border.color: Theme.chromeBorder
                radius: 3
            }
            ColumnLayout {
                objectName: "searchcenter"
                spacing: 5
                Text {
                    objectName: "searchresult"
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: {
                        if (!controller)
                            return ""
                        if (controller.searchActive)
                            return qsTr("Search results for \"%1\" (%2)")
                                .arg(controller.searchQuery)
                                .arg(controller.searchResultCount)
                        return controller.filterStatusText
                    }
                    color: Theme.ink
                    font.pixelSize: Theme.fontSize
                    wrapMode: Text.Wrap
                }
                PicasaButton {
                    objectName: "facesearch"
                    Layout.fillWidth: true
                    text: qsTr("Show only photos with faces")
                    onClicked: if (controller) {
                        controller.viewModeName === "faces"
                            ? controller.clearFilter()
                            : controller.showFacesOnly()
                    }
                }
                PicasaButton {
                    objectName: "dupesearch"
                    Layout.fillWidth: true
                    text: qsTr("Show duplicate files only")
                    onClicked: if (controller) {
                        controller.viewModeName === "dupes"
                            ? controller.clearFilter()
                            : controller.showDuplicateFiles()
                    }
                }
            }
        }
        // Verzió a jobb felső sarokban — halványan, a keresőmező mögötti
        // 47 px-en (#3603). Ide csak a rövid verzió fér („v0.8.590”); a
        // teljes címke a build-azonosítóval (appVersion →
        // version.version_string()) a buboréksúgóban olvasható, hogy
        // továbbra is ellenőrizhető legyen, PONTOSAN melyik commit fut.
        Text {
            id: versionLabel
            objectName: "versionLabel"
            anchors.right: content.right
            anchors.rightMargin: 4
            anchors.verticalCenter: content.verticalCenter
            // a teljes címke, pl. „v0.8.590 (6120.ad7e5c7c)”
            readonly property string fullText: appVersion
            text: String(appVersion).split(" ")[0]
            font.pixelSize: 9
            // #706: rámutatásra és fókuszban aláhúzott — ránézésre is
            // látszódjon, hogy a szám kattintható hivatkozás.
            font.underline: versionHover.hovered || versionLabel.activeFocus
            color: Theme.textGray
            opacity: 0.6
            // billentyűzettel is elérhető (Tab), és Enterrel/szóközzel
            // aktiválható — ld. lent a Keys.onPressed ágat
            activeFocusOnTab: true

            // SAJÁT FUNKCIÓ (#706): a verziószám a GitHub-kiadásokra mutató hivatkozás.
            // #706: a kiadások LISTÁJÁRA visz, nem a futó verzió saját
            // kiadására: fejlesztői példánynál (még ki nem adott build)
            // a `.../releases/tag/v<verzió>` 404-et adna.
            readonly property string releasesUrl:
                "https://github.com/sanchomuzax/PicasaPy/releases/"
            // maga a szám nem árulja el, hova visz — a súgó mondja ki.
            // (Saját property, mert a csatolt `ToolTip.text` a Qt
            // metaobjektumán át nem olvasható ki teszteléskor.)
            readonly property string tooltipText:
                qsTr("View releases on GitHub") + "\n" + fullText

            function openReleases() {
                Qt.openUrlExternally(versionLabel.releasesUrl)
            }

            ToolTip.visible: versionHover.hovered
            ToolTip.text: versionLabel.tooltipText

            ToolTip.delay: Theme.tooltipDelay
            HoverHandler {
                id: versionHover
                objectName: "versionCursor"
                cursorShape: Qt.PointingHandCursor
            }
            TapHandler {
                objectName: "versionTap"
                onTapped: versionLabel.openReleases()
            }
            Keys.onPressed: function (event) {
                if (event.key === Qt.Key_Return
                        || event.key === Qt.Key_Enter
                        || event.key === Qt.Key_Space) {
                    versionLabel.openReleases()
                    event.accepted = true
                }
            }
            // látható fókuszjelölés — billentyűzetes navigációnál a
            // felhasználó lássa, hol jár
            Rectangle {
                objectName: "versionFocusRing"
                anchors.fill: parent
                anchors.margins: -2
                visible: versionLabel.activeFocus
                color: "transparent"
                border.color: Theme.linkBlue
                border.width: 1
                radius: 2
            }
        }
    }
}

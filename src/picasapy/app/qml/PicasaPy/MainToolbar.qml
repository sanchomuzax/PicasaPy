import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Felső eszköztár (#150-ben kiemelve a Main.qml-ből):
// Importálás | szűrők középen | Picasa-hű kereső jobbra + verzió-címke.
// A keresés-változást jelekkel adja tovább — a debounce-olt javaslat-
// frissítés és a kijelölés-ürítés a Main.qml dolga marad.
Rectangle {
    id: toolbar
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
    signal treeViewRequested()

    function clearSearch() {
        searchField.clear()
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width; height: 1
        color: Theme.chromeBorder
    }
    // #423: a sáv MINDIG egyetlen (ma 35px-es) csík marad — a RowLayout maga
    // sosem tördel új sorba, de a régi kötések (fix preferredWidth minden
    // elemen, sehol minimumWidth) szűk ablaknál egymásra csúszó/kilógó
    // elemekhez vezettek, ami vizuálisan "törésnek" hatott. A javítás a
    // zsugorodási sorrendet Layout.minimumWidth-ekkel rögzíti:
    //   1. a bal oldali rugalmas térköz nyeli el az extra helyet elsőként;
    //   2. a keresőmező zsugorodik 300px-ről 120px-ig;
    //   3. a középső szűrő-zóna teljesen elrejtőzik `toolbarCompact` alatt;
    //   4. az "Importálás" gomb és a verzió-címke SOHA nem zsugorodik —
    //      a gomb Layout.minimumWidth == Layout.preferredWidth (fix).
    readonly property bool toolbarCompact: width < 1080
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 8; anchors.rightMargin: 8
        spacing: 10
        PicasaButton {
            objectName: "toolbarImportButton"
            text: qsTr("Import")
            enabled: true
            // #587: az eredeti `importbutton` 111 × 22 (a `respack.yt`
            // mért téglalapja, `konyvtar-ablak-meretek.md` 2. szakasz).
            // A magasság 22 azért fér el a feliratnak, mert a
            // `PicasaButton` függőleges kitöltése 0 (ld. ott a #992
            // kommentjét) — a 12px-es betű teljes sormagassága belefér.
            Layout.preferredWidth: 111
            Layout.minimumWidth: 111
            Layout.preferredHeight: 22
            //: #1929: `thumbui/importbutton` — az EREDETI súgója, szó
            //: szerint (`referencia/ui-leltar.csv`). Eddig nem volt súgója.
            ToolTip.text: qsTr("Get photos from a camera, scanner, or other media")
            ToolTip.visible: hovered
            ToolTip.delay: 500
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
        // ⚠️ Szűk ablaknál elrejtőzik, a szűrő-zóna mintájára (#423): a
        // sávnak egyetlen csíkban kell maradnia, és minden fix szélességű
        // elem a NEM zsugorodó alapot növeli. A rejtés a mi
        // alkalmazkodásunk, nem az eredeti viselkedés.
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
        // A gomb az eredetiben MINDIG aktív (a `.tre`-ben nincs feltétele);
        // szűk ablaknál nálunk elrejtőzik (#423) — ld. a teszt indoklását.
        Item {
            objectName: "toolbarNewAlbumButton"
            visible: !toolbar.toolbarCompact
            Layout.preferredWidth: 29
            Layout.minimumWidth: 0
            Layout.preferredHeight: 22
            Layout.alignment: Qt.AlignVCenter
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
            ToolTip.delay: 500
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
            visible: !toolbar.toolbarCompact
            spacing: 0
            Layout.preferredWidth: 60
            Layout.minimumWidth: 0
            Layout.preferredHeight: 22
            Layout.alignment: Qt.AlignVCenter
            Rectangle {
                objectName: "toolbarFlatViewButton"
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
                ToolTip.delay: 500
                HoverHandler { id: flatViewHover }
                TapHandler { onTapped: toolbar.flatViewRequested() }
            }
            Rectangle {
                objectName: "toolbarTreeViewButton"
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
                ToolTip.delay: 500
                HoverHandler { id: treeViewHover }
                TapHandler { onTapped: toolbar.treeViewRequested() }
            }
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
        Item { Layout.fillWidth: true; Layout.minimumWidth: 0 }
        // #423: NEM Column, hanem Item — a "Szűrők" felirat a Picasa
        // `searchcontainer.tre`-jének `filter_label` kényszere szerint
        // (`YConstraint 0, 0, -4`) a csík TETEJÉTŐL −4px-re ül, azaz a
        // csíkon BELÜL, az ikonsor FÖLÉ kicsúszva jelenik meg — nem külön
        // sorba kerül (amit egy Column spacing:0 flow-ja nem tudna
        // kifejezni, mert az mindig a felirat alá, nem fölé/bele tenné
        // a következő sort).
        Item {
            id: filterZone
            objectName: "toolbarFilterZone"
            Layout.alignment: Qt.AlignVCenter
            Layout.minimumWidth: 0
            // szűk ablaknál a középső szűrő-zóna rejtőzik el — a sáv maga
            // nem törik, csak ez a blokk tűnik el (#423)
            visible: !toolbar.toolbarCompact
            implicitWidth: filterIconsRow.width
            implicitHeight: filterIconsRow.y + filterIconsRow.height
            Text {
                objectName: "toolbarFiltersLabel"
                anchors.horizontalCenter: parent.horizontalCenter
                y: -4
                text: qsTr("Filters")
                font.pixelSize: 9
                color: Theme.textGray
            }
            Row {
                id: filterIconsRow
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
                    width: 22; height: 20; radius: 2
                    color: ctlFilterActive ? "#ffffff" : "transparent"
                    border.width: ctlFilterActive ? 1 : 0
                    border.color: Theme.selectionBlue
                    Text {
                        anchors.centerIn: parent
                        text: "★"
                        font.pixelSize: 13
                        color: parent.ctlFilterActive
                               ? Theme.selectionBlue
                               : (starFilter.hovered ? Theme.starYellow : "#8f8b83")
                    }
                    HoverHandler { id: starFilter }
                    TapHandler {
                        onTapped: controller.filterActive
                                  ? controller.clearFilter()
                                  : controller.showStarred()
                    }
                }
                Text {   // arc-szűrő (3. fázis)
                    // #1830: MÉRVE — az ini `faces=` adata NINCS az
                    // indexben (a `face` tábla kizárólag a felismerésből
                    // származik), ezért ez a szűrő ma nem építhető meg a
                    // meglévő adatokból. Helyfoglaló marad, hogy ne
                    // ígérjen hatástalan kattintást.
                    width: 22; height: 20
                    text: "☺"; font.pixelSize: 13; color: Theme.placeholderText
                    opacity: 0.45
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                Item {   // #1830: „csak filmek" — az eredeti `moviesearch`
                    objectName: "movieFilter"
                    width: 22; height: 20
                    readonly property bool aktiv:
                        (controller && controller.viewModeName !== undefined)
                            ? controller.viewModeName === "videos" : false
                    Rectangle {
                        anchors.fill: parent
                        radius: 2
                        color: parent.aktiv ? "#ffffff" : "transparent"
                        border.width: parent.aktiv ? 1 : 0
                        border.color: Theme.selectionBlue
                    }
                    Text {
                        anchors.centerIn: parent
                        text: "▶"
                        font.pixelSize: 11
                        color: parent.aktiv
                               ? Theme.selectionBlue
                               : (movieFilterHover.hovered
                                  ? Theme.selectionBlue : "#8f8b83")
                    }
                    //: `moviesearch` — az eredeti buboréksúgója
                    ToolTip.text: qsTr("Show movies only")
                    ToolTip.visible: movieFilterHover.hovered
                    ToolTip.delay: 500
                    HoverHandler { id: movieFilterHover }
                    TapHandler {
                        onTapped: parent.aktiv
                                  ? controller.clearFilter()
                                  : controller.showVideosOnly()
                    }
                }
                Item {   // geo-szűrő (#30) — csak akkor él, ha van geocímkés kép
                    objectName: "geoFilter"
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
                    HoverHandler { id: geoFilterHover }
                    TapHandler {
                        enabled: parent.ctlHasGeo
                        onTapped: controller.filterActive
                                  ? controller.clearFilter()
                                  : controller.showGeotagged()
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
                PicasaSlider {
                    width: 90; height: 20
                    enabled: false
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
        Item { width: 20; visible: filterZone.visible }
        // Picasa-hű kereső: fehér mező nagyítóval, törlő ×-szel — a
        // zsugorodási sorrend 2. lépése (#423): a teljes méretétől
        // 120px-ig zsugorodhat, mielőtt bármi máshoz hozzányúlnánk.
        //
        // #587: a teljes méret az eredeti `searchcontainer`-é: 388 × 30
        // (`konyvtar-ablak-meretek.md` 2. szakasz). A `minimumWidth`
        // marad 120 — a zsugorodási sorrendet a #423 rögzítette, ezt a
        // kör nem írja felül.
        Rectangle {
            objectName: "toolbarSearchBox"
            Layout.preferredWidth: 388
            Layout.minimumWidth: 120
            Layout.preferredHeight: 30
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
        // Verzió + build a jobb felső sarokban — halványan, hogy
        // zavartalanul, de bármikor ellenőrizhető legyen, PONTOSAN
        // melyik commit fut (appVersion → version.version_string()).
        Text {
            id: versionLabel
            objectName: "versionLabel"
            Layout.alignment: Qt.AlignVCenter
            Layout.minimumWidth: 0
            text: appVersion
            font.pixelSize: 9
            // #706: rámutatásra és fókuszban aláhúzott — ránézésre is
            // látszódjon, hogy a szám kattintható hivatkozás.
            font.underline: versionHover.hovered || versionLabel.activeFocus
            color: Theme.textGray
            opacity: 0.6
            // billentyűzettel is elérhető (Tab), és Enterrel/szóközzel
            // aktiválható — ld. lent a Keys.onPressed ágat
            activeFocusOnTab: true

            // #706: a kiadások LISTÁJÁRA visz, nem a futó verzió saját
            // kiadására: fejlesztői példánynál (még ki nem adott build)
            // a `.../releases/tag/v<verzió>` 404-et adna.
            readonly property string releasesUrl:
                "https://github.com/sanchomuzax/PicasaPy/releases/"
            // maga a szám nem árulja el, hova visz — a súgó mondja ki.
            // (Saját property, mert a csatolt `ToolTip.text` a Qt
            // metaobjektumán át nem olvasható ki teszteléskor.)
            readonly property string tooltipText:
                qsTr("Kiadások megtekintése a GitHubon")

            function openReleases() {
                Qt.openUrlExternally(versionLabel.releasesUrl)
            }

            ToolTip.visible: versionHover.hovered
            ToolTip.text: versionLabel.tooltipText

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

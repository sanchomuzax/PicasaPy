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
        PicasaButton {
            objectName: "toolbarNewAlbumButton"
            text: qsTr("New Album")
            visible: !toolbar.toolbarCompact
            Layout.preferredWidth: 29
            Layout.minimumWidth: 0
            Layout.preferredHeight: 22
            //: `newalbum` — az eredeti buboréksúgója
            ToolTip.text: qsTr("Create a new album")
            ToolTip.visible: hovered
            ToolTip.delay: 500
            onClicked: toolbar.newAlbumRequested()
        }
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

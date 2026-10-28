import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
            property var toolbar
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

                // szűrő-kapcsolók (kézikönyv 09): ★ ☺ ⚲ + csúszka;
                // a bekapcsolt szűrő tónusa jelölő kék
                Rectangle {
                    // #305: null-őr — a controller a QML-engine
                    // leépítésekor átmenetileg null lehet
                    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
                    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
                    readonly property bool ctlFilterActive:
                        (controller && controller.viewModeName !== undefined)
                            ? controller.viewModeName === "starred" : false
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
                            parent.ctlFilterActive
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
                    readonly property bool ctlCanShowGeo:
                        ctlHasGeo || (controller && controller.filterActive !== undefined
                                      ? controller.filterActive : false)
                    readonly property bool aktiv:
                        (controller && controller.viewModeName !== undefined)
                            ? controller.viewModeName === "geo" : false
                    Rectangle {
                        objectName: "geoFilterBackground"
                        anchors.fill: parent
                        radius: 2
                        color: parent.aktiv
                               ? Theme.szuroHatterAktiv
                               : (geoFilterHover.hovered
                                  ? Theme.szuroHatterRamutat : "transparent")
                        border.width: 0
                    }
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
                        opacity: parent.aktiv
                                 ? 1.0
                                 : (parent.ctlHasGeo
                                    ? (geoFilterHover.hovered ? 1.0 : 0.85)
                                    : 0.35)
                    }
                    // #839: itt NINCS lebegő ToolTip — a súgó a „Szűrők"
                    // felirat helyén jelenik meg (`hottip`, ld. ott)
                    HoverHandler { id: geoFilterHover }
                    TapHandler {
                        enabled: parent.ctlCanShowGeo
                        //: #885: lenyomásra, nem felengedésre
                        onPressedChanged: if (pressed) {
                            parent.aktiv
                                ? controller.clearFilter()
                                : controller.showGeotagged()
                        }
                    }
                }
                // #4532: a korábbi kezelő nélküli „▤" jel innen kikerült —
                // az eredeti szűrőkeresőben nincs ilyen elem, a mozgófilm
                // a saját gombján van (`movieFilter`).
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
                    id: ageFilterSlider
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
                Connections {
                    target: controller
                    function onStatusChanged() {
                        if (controller && controller.viewModeName !== "age")
                            ageFilterSlider.value = 0.0
                    }
                }
            }
        }

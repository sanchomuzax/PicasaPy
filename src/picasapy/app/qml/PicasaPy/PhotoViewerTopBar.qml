import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

        Rectangle {
            id: viewerTopBar
            property var hostViewer: null
            property var hostLeftDrawer: null
            property var hostPhotoArea: null
            property var hostFilmstrip: null
            readonly property var viewer: hostViewer
            readonly property var leftDrawer: hostLeftDrawer
            readonly property var photoArea: hostPhotoArea
            readonly property var filmstrip: hostFilmstrip
            default property alias filmstripContent: filmstripSlot.data
            objectName: "viewerTopBar"
            Layout.fillWidth: true
            visible: !viewer.quickViewerMode
            height: viewer.quickViewerMode ? 0 : 46
            color: Theme.chromeBg
            //: #3663 (átnézés, 2. kör): ez a csoport (Vissza a
            //: könyvtárhoz + a két feltételes szerkesztő-gomb) a sáv BAL
            //: szélén marad — csak a NAVIGÁTOR-csoport (lent) igazodik a
            //: fotóterület közepéhez. Korábban EGY közös `RowLayout`
            //: `anchors.fill: parent`-tel + egyetlen `Layout.fillWidth`
            //: kitöltővel tolta a navigátor-csoportot jobbra — ez a
            //: `Item` a placeholder-hármassal együtt a sáv JOBB SZÉLÉRE
            //: tolta az egészet, nem a fotóterület közepére (a
            //: tulajdonos e köri kifogása).
            RowLayout {
                id: viewerTopBarLeftGroup
                objectName: "viewerTopBarLeftGroup"
                anchors.left: parent.left
                anchors.leftMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8
                // #5762: a külön fájllistás indítás a műveletsáv első
                // három parancsát a spec sorrendjében mutatja. Egy
                // egérkattintás 0,05-ös csúszkalépés, ugyanaz, mint egy
                // görgőkattanás; az 1:1 külön a mért zoom-detentre lép.
                PicasaButton {
                    objectName: "viewerTopBarQuickZoomInButton"
                    visible: viewer.quickViewerMode
                    text: "+"
                    ToolTip.text: qsTr("Zoom In")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.lepjZoom(0.05)
                }
                PicasaButton {
                    objectName: "viewerTopBarQuickZoomOutButton"
                    visible: viewer.quickViewerMode
                    text: "−"
                    ToolTip.text: qsTr("Zoom Out")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.lepjZoom(-0.05)
                }
                PicasaButton {
                    objectName: "viewerTopBarQuickZoomActualButton"
                    visible: viewer.quickViewerMode
                    text: "1:1"
                    ToolTip.text: qsTr("Zoom to 1:1")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.zoomActual()
                }
                // #1993: a MÉRT alak — ikonos, KÉTSOROS gomb.
                //
                // Az ikon az `editpanel/albumview_icon` (17 × 15), színe a
                // sprite domináns kékje, `#5A7BBB`. A felirat a felvételen
                // két sorban áll („Vissza a / könyvtárhoz"), ezért a gomb
                // szélessége kötött — a `PicasaButton` maga tördel (#992).
                //
                // ⚠️ A `◀` glif KIESETT: az ikon váltja ki, nem mellette
                // áll. A tesztek erre külön állítást tesznek.
                PicasaButton {
                    objectName: "viewerBackButton"
                    font.pixelSize: Theme.fontSize
                    text: viewer.quickViewerMode
                        ? qsTr("Edit in PicasaPy") : qsTr("Back to Library")
                    //: #3476: az eredeti `thumbui/albumview` súgója
                    ToolTip.text: viewer.quickViewerMode
                        ? qsTr("Launch PicasaPy")
                        : qsTr("Return to organized thumbnails")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    Layout.preferredWidth: 118
                    Layout.preferredHeight: 34
                    leftPadding: 30
                    onClicked: viewer.kerBezaras()
                    Image {
                        objectName: "viewerBackIcon"
                        source: "icons/viewer-back-arrow.svg"
                        width: 17; height: 15
                        sourceSize.width: 17; sourceSize.height: 15
                        anchors.left: parent.left
                        anchors.leftMargin: 7
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                // #1002 — `editpanel/editcollage`. Az eredetiben `m_hidden`:
                // alapból REJTETT, és csak akkor jön elő, ha a megnyitott
                // képnek van kollázs-projektfájlja. A tulajdonos szava:
                // „Ez a gomb mindig megjelenik, ha megnyitom a kollázst."
                //
                // ⚠️ NEM azonos a `collagepanel::back_to_collage` =
                // „Vissza a kollázshoz" gombbal: az a KÖNYVTÁR lapján áll,
                // és a félbehagyott kollázshoz visz vissza.
                PicasaButton {
                    id: kollazsSzerkesztes
                    objectName: "viewerEditCollageButton"
                    //: `editpanel/editcollage-label`
                    text: qsTr("Edit Collage")
                    font.pixelSize: Theme.fontSize
                    //: `editpanel/editcollage` elemleírása
                    ToolTip.text: qsTr(
                        "Edit the collage from which this image was created")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    //: A null-őr a #305 szabálya: a vezérlő a lebontáskor és a
                    //: komponens-teszteknél hiányozhat (ld. a `viewer`
                    //: gyökerén a `controllerReady`-t).
                    //: #1072: a PISZKOZATON is látszik — a spec 6. szakasza
                    //: és a tulajdonos képernyőképe szerint a visszaút a
                    //: befejezetlen kollázsról is nyitva áll.
                    visible: viewer.currentIsSavedCollage
                             || viewer.currentIsCollageDraft
                    onClicked: viewer.editCollageRequested(viewer.currentFilePath)
                }
                //: #2114 — `editpanel/editslideshow`, a fenti gomb
                //: IKERPÁRJA: ugyanaz a kezelő (`0x00567a00`), ugyanaz a
                //: `m_hidden` alapállapot, csak a másik projekt-fajtára.
                //: A felirat és a buboréksúgó a HIVATALOS magyar szöveg
                //: (`panel-feliratok-hu.tsv:4928` és `:4929`).
                PicasaButton {
                    id: filmSzerkesztes
                    objectName: "viewerEditMovieButton"
                    //: `editpanel/editslideshow-label`
                    text: qsTr("Edit Movie")
                    font.pixelSize: Theme.fontSize
                    //: `editpanel/editslideshow` elemleírása
                    ToolTip.text: qsTr("Edit the movie presentation")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    visible: viewer.currentIsSavedMovie
                    onClicked: viewer.editMovieRequested(viewer.currentFilePath)
                }
            }

            //: #3663 (átnézés, 2. kör): NEM a navigátor-csoport egészének
            //: középpontja igazodik a fotóterület közepéhez, hanem a
            //: FILMSZALAGÉ — mérve (`ui-audit-editor.md` 3/b.1, 1280 px-en):
            //: Play ~530–620, ◀ ~640–665, filmszalag ~670–885 (középpontja
            //: ~777, a fotóterület közepe ~780), ▶ vége 917, A|AB|AA
            //: szegmens 933–1047, fókuszváltó 1057–1091, elrendezés-váltó
            //: 1096–1130. A csoport a filmszalag UTÁN nagyobb tömeget visz
            //: (a három kapcsoló + két segédgomb), tehát a csoport SAJÁT
            //: középpontja NEM esik egybe a fotóterületével — csak a
            //: filmszalagé. A `Math.max` az `viewerTopBarLeftGroup`-ba
            //: ütközést zárja ki keskeny ablaknál, a `Math.min` a sáv jobb
            //: szélén való túlfutást.
            RowLayout {
                id: viewerNavigatorRow
                objectName: "viewerNavigatorRow"
                anchors.verticalCenter: viewerTopBar.verticalCenter
                //: #3663 (átnézés, 2. kör): 5 px — a referencián mért
                //: rések (5/10/16 px, `ui-audit-editor.md` 3/b.1)
                //: átlagához közelebb áll, mint az eredeti `RowLayout`
                //: 8 px-es alapértelmezése; 1280 px-en, öt fotós mappával
                //: mérve mind a négy vizsgált szakasz (▶ vége, szegmens,
                //: fókuszváltó, elrendezés-váltó) ±8 px-en belülre esik.
                spacing: 5
                //: ⚠️ a `photoArea.x` a SAJÁT szülőjéhez (a „fő
                //: képterület” `Rectangle`-höz) képest helyi — az a
                //: `leftDrawer` UTÁN áll ugyanabban a `RowLayout`-ban,
                //: tehát a `viewerTopBar`-ral KÖZÖS (a felső `ColumnLayout`
                //: gyökeréig visszavezethető) koordinátához a
                //: `leftDrawer.width`-öt hozzá kell adni. Enélkül ez a
                //: sáv pontosan a bal fiók szélességével (280 px) balra
                //: tér el a fotóterület közepétől — ugyanaz a hibaosztály,
                //: mint a „Kijelölve” jelvényé (ld. lent a `kepBal`
                //: kommentjét).
                readonly property real fototeruletKozepe:
                    leftDrawer.width + photoArea.x + photoArea.width / 2
                //: a `filmstripSlot.x`/`.width` a `filmstrip` SAJÁT (a sorhoz
                //: képest helyi) pozíciója/szélessége — ebből adódik, hova
                //: kell tolni a TELJES sort, hogy a szalag közepe essen a
                //: fotóterület közepére.
                x: Math.max(
                       viewerTopBarLeftGroup.x + viewerTopBarLeftGroup.width + 12,
                       Math.min(
                           fototeruletKozepe - filmstripSlot.x - filmstripSlot.width / 2,
                           viewerTopBar.width - width - 8))
                PicasaButton {
                    objectName: "viewerPlayButton"
                    visible: !viewer.quickViewerMode
                    text: "▶ " + qsTr("Play")
                    font.pixelSize: Theme.fontSize
                    ToolTip.text: qsTr("Play Slideshow")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.playRequested()
                }
                // #1993: a MÉRT léptető — 30 × 31, KÖR alakú rajz.
                //
                // A kör alakot a `globalbuttons/lfs_n` sprite soronkénti
                // látható szélessége bizonyítja (…29, 30, 30, 30, 30, 30,
                // 30, 30, 29…) — korong, nem lekerekített téglalap.
                //
                // ⚠️ A jegy „kör alakú, KÉK" nyilakat írt. A kör igaz, a
                // kék NEM: a sprite és a felvétel is `#5C`–`#5F` szürkét
                // ad. A KÉK a „Vissza a könyvtárhoz" gomb nyila
                // (`#5A7BBB`) — két különböző elem.
                PicasaButton {
                    objectName: "viewerPrevButton"
                    //: #885: a kép-léptetés LENYOMÁSRA hat az eredetiben
                    //: (`oneup/prev`, `oneup/next` — `Property mousedown 1`).
                    lenyomasra: true
                    //: #4563: `m_autorepeat` — nyomva tartva folyamatosan lép
                    autoRepeat: true
                    onClicked: viewer.previous()
                    enabled: viewer.hasPrevious()
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 31
                    width: 30; height: 31
                    padding: 0
                    background: null
                    contentItem: Item {
                        Image {
                            objectName: "viewerPrevIcon"
                            source: "icons/viewer-step-left.svg"
                            width: 30; height: 31
                            sourceSize.width: 30; sourceSize.height: 31
                            anchors.centerIn: parent
                        }
                    }
                    ToolTip.text: qsTr("Previous Photo")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
                PicasaButton {
                    objectName: "viewerTopBarQuickPlayButton"
                    visible: viewer.quickViewerMode
                    text: "▶ " + qsTr("Play")
                    font.pixelSize: Theme.fontSize
                    ToolTip.text: qsTr("Play Slideshow")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.playRequested()
                }
                // #1905: a szalag CSAK a jelenlegi kép mappáját mutatja.
                //
                // Eddig a teljes rács-modellt listázta. A rács viszont
                // FEED: több mappa fotóit sorolja fel egymás után, a
                // csillag-szűrő és a keresés pedig végképp vegyít. A
                // tulajdonos ezért egy ötképes mappa szerkesztésekor
                // NYOLC elemet látott — köztük egy MÁSIK mappa
                // kollázs-képeit. Az eredetiben (egymás mellé tett
                // felvétel ugyanazon a mappán) pontosan a mappa képei
                // állnak itt.
                //
                // Ugyanaz a szerződés, mint a ◀/▶ léptetésé (#84,
                // `folderNeighbor`): a mappa fotói folytonos tartományt
                // alkotnak, tehát elég a kezdet és a darabszám.
                Item {
                    id: filmstripSlot
                    Layout.minimumWidth: 214
                    Layout.preferredWidth: 214
                    Layout.maximumWidth: 214
                    Layout.preferredHeight: 28
                }
                PicasaButton {
                    objectName: "viewerNextButton"
                    //: #885: a kép-léptetés LENYOMÁSRA hat az eredetiben
                    //: (`oneup/prev`, `oneup/next` — `Property mousedown 1`).
                    lenyomasra: true
                    //: #4563: `m_autorepeat` — nyomva tartva folyamatosan lép
                    autoRepeat: true
                    onClicked: viewer.next()
                    enabled: viewer.hasNext()
                    Layout.preferredWidth: 30
                    Layout.preferredHeight: 31
                    width: 30; height: 31
                    padding: 0
                    background: null
                    contentItem: Item {
                        Image {
                            objectName: "viewerNextIcon"
                            source: "icons/viewer-step-right.svg"
                            width: 30; height: 31
                            sourceSize.width: 30; sourceSize.height: 31
                            anchors.centerIn: parent
                        }
                    }
                    ToolTip.text: qsTr("Next Photo")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                }
                // #5762: a spec 12.8.2-ben szerepel, de a PicasaPy ezt a
                // szolgáltatást (#422) már kivezette; a gomb látható, de
                // nem indít feltöltést.
                PicasaButton {
                    objectName: "viewerTopBarQuickUploadButton"
                    visible: viewer.quickViewerMode
                    enabled: viewer.quickUploadAvailable
                    width: 30; height: 28
                    padding: 0
                    Accessible.name: qsTr("Quick Upload")
                    ToolTip.text: qsTr("Quick Upload")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    contentItem: Image {
                        source: "icons/upload.svg"
                        width: 17; height: 17
                        sourceSize.width: 17; sourceSize.height: 17
                        fillMode: Image.PreserveAspectFit
                    }
                }
                PicasaButton {
                    objectName: "viewerTopBarQuickRotateLeftButton"
                    visible: viewer.quickViewerMode
                    width: 30; height: 28
                    padding: 0
                    ToolTip.text: qsTr("Rotate counter-clockwise")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.rotateRequested(
                        viewer._kijeloltSort(), -1)
                    contentItem: Image {
                        source: "icons/tray-rotate-left.svg"
                        width: 15; height: 17
                        sourceSize.width: 15; sourceSize.height: 17
                        fillMode: Image.PreserveAspectFit
                    }
                }
                PicasaButton {
                    objectName: "viewerTopBarQuickRotateRightButton"
                    visible: viewer.quickViewerMode
                    width: 30; height: 28
                    padding: 0
                    ToolTip.text: qsTr("Rotate clockwise")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.rotateRequested(
                        viewer._kijeloltSort(), 1)
                    contentItem: Image {
                        source: "icons/tray-rotate-right.svg"
                        width: 15; height: 17
                        sourceSize.width: 15; sourceSize.height: 17
                        fillMode: Image.PreserveAspectFit
                    }
                }
                PicasaButton {
                    objectName: "viewerTopBarQuickStarButton"
                    visible: viewer.quickViewerMode
                    width: 30; height: 28
                    padding: 0
                    ToolTip.text: qsTr("Star")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: viewer.starRequested(
                        viewer._kijeloltSort())
                    contentItem: Image {
                        source: viewer.photosModel && viewer.currentIndex >= 0
                            ? (viewer.photosModel.revision,
                               viewer.photosModel.starAt(viewer.currentIndex)
                                 ? "icons/tray-star-on.svg"
                                 : "icons/tray-star.svg")
                            : "icons/tray-star.svg"
                        width: 17; height: 17
                        sourceSize.width: 17; sourceSize.height: 17
                        fillMode: Image.PreserveAspectFit
                    }
                }
                PicasaButton {
                    id: viewerMoreOptionsButton
                    objectName: "viewerTopBarQuickMoreOptionsButton"
                    visible: viewer.quickViewerMode
                    width: 30; height: 28
                    padding: 0
                    Accessible.name: qsTr("More Options")
                    ToolTip.text: qsTr("Click to see more options")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: {
                        var p = viewerMoreOptionsButton.mapToItem(
                            viewer, 0, viewerMoreOptionsButton.height)
                        viewer.openContextMenu(p.x, p.y)
                    }
                    contentItem: Image {
                        source: "icons/tray-more.svg"
                        width: 16; height: 16
                        sourceSize.width: 16; sourceSize.height: 16
                        fillMode: Image.PreserveAspectFit
                    }
                }

                //: #3663: a mért sorrend a filmszalag és a ▶ UTÁN áll — a
                //: #3013 tévesen a Play/◀/szalag/▶ csoport ELÉ tette (a
                //: bináris `editpanel.tre` 1280 px-en: ▶ vége x 917,
                //: szegmens 933–1047, fókuszváltó 1057–1091,
                //: elrendezés-váltó 1096–1130 — mind a szalag JOBB oldalán).
                //:
                //: #3013: a kettős nézet háromszegmenses kapcsolója
                //: (`editpanel/layout_2up_group`), a mért sorrendben és a
                //: hivatalos magyar buboréksúgókkal.
                Row {
                    objectName: "viewerLayoutGroup"
                    // #4562: megtartja a mért kezdőpontot a fix 214 px-es
                    // filmszalag után (▶ vége x=917, a csoport x=933).
                    Layout.leftMargin: 6
                    //: #3663 (átnézés, 2. kör): a szegmens-hármas MÉRT
                    //: teljes szélessége 114 px (933–1047) — a `spacing:0`
                    //: és a 38 px-es szegmensszélesség adja ki pontosan
                    //: (3 × 38 = 114); korábban 26 px-es szegmensekkel és
                    //: 1 px réssel csak 80 px volt, alig olvashatóan apró.
                    spacing: 0
                    //: #3663: a KIRAJZOLT referencián (`Colab EN 33`, a
                    //: felső sáv 933–970 px-es szegmense nagyítva) egy
                    //: vékony szegélyű, önálló KERETES BETŰ áll a
                    //: szegmensben — ez a `respack.yt` `only_1up_icon`
                    //: (20×15) rétegével egyezik. A #3013 plain szöveget
                    //: (`jel: "A"`) adott, amit csak az AKTÍV/hover
                    //: állapotban kapott a `LayoutSegment` saját kerete —
                    //: alapállapotban tehát nem volt keret, ellentétben a
                    //: referenciával. Az `ikon` a `jel`-t váltja.
                    LayoutSegment {
                        objectName: "viewerLayoutOnly1up"
                        nezo: viewer
                        mod: "1up"
                        width: 38
                        ikon: "icons/viewer-layout-a.svg"
                        sugo: qsTr("Show only one picture")
                    }
                    //: #3014: a MÉRT sorrend `only_1up` · `ab_2up` ·
                    //: `aa_2up` (a respack `LS`/`MS`/`RS` szegmensrajza,
                    //: `docs/specs/ui-audit-editor.md` 1. táblája). A
                    //: #3013 fordítva rakta le a két 2-up szegmenst.
                    //:
                    //: #3663: `ab_2up_icon` (27×15) — a referencián (a
                    //: felső sáv 970–1010 px-es szegmense) KÉT KÜLÖN
                    //: keretes betű áll egymás mellett, kis réssel: „A" |
                    //: „B" — nem egyetlen, válaszvonallal kettéosztott
                    //: doboz.
                    LayoutSegment {
                        objectName: "viewerLayoutAb"
                        nezo: viewer
                        mod: "ab"
                        width: 38
                        ikon: "icons/viewer-layout-ab.svg"
                        sugo: qsTr("Show two different pictures")
                    }
                    //: #3663: `aa_2up_icon` (27×15) — az `ab_2up_icon`
                    //: ikerpárja, „A" | „A" felirattal.
                    LayoutSegment {
                        objectName: "viewerLayoutAa"
                        nezo: viewer
                        mod: "aa"
                        width: 38
                        ikon: "icons/viewer-layout-aa.svg"
                        sugo: qsTr("Show the same picture twice")
                    }
                }

                //: #3013: `swap_2up_focus` — csak 2-up módban látszik
                //: #3663 (átnézés, 2. kör): MÉRT szélesség 34 px (1057–1091)
                //: — a korábbi 26 px alig volt olvasható/kattintható.
                LayoutSegment {
                    objectName: "viewerSwapFocus"
                    // A mért 10 px-es rés a csoport után: spacing 5 + margó 5.
                    Layout.leftMargin: 5
                    //: #885: a `.tre` `swap_2up_focus`-én NINCS `mousedown` —
                    //: felengedésre sül el, a három elrendezés-váltóval
                    //: ellentétben.
                    lenyomasra: false
                    nezo: viewer
                    mod: ""
                    width: 34
                    //: #3663: a jegy „felismerhetetlen"-nek jelezte a
                    //: korábbi szövegjelet (`⇄`) — most a mért rajz (ld.
                    //: `ui-audit-editor.md` 3/b.2) szerinti saját ikon.
                    ikon: "icons/viewer-swap-focus.svg"
                    sugo: qsTr("Switch focus between the pictures")
                    visible: viewer.layoutMode !== "1up"
                    function kattints() {
                        viewer.fokuszValt(
                            viewer.aktivOldal === "jobb" ? "bal" : "jobb")
                    }
                }

                //: #3014: `swap_2up_layout` — szintén csak 2-up módban
                //: (`editpanel.tre:1172`, `m_hidden` az alapállapot).
                //: #3663 (átnézés, 2. kör): MÉRT szélesség 34 px
                //: (1096–1130).
                LayoutSegment {
                    objectName: "viewerSwapLayout"
                    //: #885: a `.tre` `swap_2up_layout`-én NINCS `mousedown` —
                    //: felengedésre sül el, a három elrendezés-váltóval
                    //: ellentétben.
                    lenyomasra: false
                    nezo: viewer
                    mod: ""
                    width: 34
                    //: #3663: a jegy „felismerhetetlen"-nek jelezte a
                    //: korábbi szövegjelet (`⬌`/`⬍`) — most a mért rajz
                    //: (ld. `ui-audit-editor.md` 3/b.2) szerinti saját ikon.
                    ikon: "icons/viewer-swap-layout.svg"
                    sugo: qsTr("Switch between horizontal and vertical layout")
                    visible: viewer.layoutMode !== "1up"
                    function kattints() {
                        viewer.fuggolegesElrendezes = !viewer.fuggolegesElrendezes
                    }
                }

                //: #3663: a korábbi `compareButtonA/AB/AA` letiltott
                //: placeholder-hármas (`#6`/`#1857`, a szerkesztés-
                //: összevetés 2. fázisára szánva) TÖRÖLVE — a referencia
                //: (`Colab EN 33`–`35`) nem mutat ilyen sort a kettős nézet
                //: fejlécén, és a valódi A/AB/AA váltó
                //: (`viewerLayoutOnly1up/Ab/Aa`, fent) régóta megvan. A
                //: placeholderek ELŐTT itt álló kitöltő `Item` is velük
                //: távozott: az a spacer ŐKET tolta a sáv jobb szélére, a
                //: `viewerSwapLayout` UTÁN maradva viszont pont az
                //: ELLENKEZŐJÉT érte volna el — saját magát tolta volna a
                //: szélre, a segédgombokat pedig balra, a középre.
            }
        }

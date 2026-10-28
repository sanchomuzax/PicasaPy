import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import PicasaPy.Gpu
import "aranykenyszer.js" as AranyKenyszer

// Egyképes néző — a Picasa 3.9 "Megjelenítés és szerkesztés" képernyője
// alapján (#808080 háttér, felső filmszalag nyilakkal, bal eszközpanel;
// a szerkesztő-gombok a 2. fázisig szürkék). Enter/Jobbra: következő,
// Balra: előző, Esc: vissza a könyvtárba.
Rectangle {
    id: viewer

    // #4639: a főablak súgója közvetlenül ezekből a bekötött
    // Shortcut.sequence értékekből olvassa a néző és a kiegyenesítő sáv
    // billentyűit.
    readonly property var keyboardShortcutSequences: [
        viewerEditWorkflow.drawerShortcutSequence
    ].concat(editorToolBar.keyboardShortcutSequences)

    readonly property bool textEntryHasFocus:
        viewer.Window.window !== null
        && viewer.Window.window.activeFocusItem !== null
        && viewer.Window.window.activeFocusItem.selectedText !== undefined
    //: #3463: a Shift+F1 fejezete (ld. `Main.qml` `helpTopicUnderCursor`)
    property string helpTopic: "features/nezegetes.md"

    // #1816: látszik-e a felirat-sáv. A GYÖKÉREN áll, mert a sáv és a
    // „Make a caption!" helyőrző két külön szülő alatt él.
    // A `!== undefined` a #1572-őr mintája: a próbák stub-vezérlőjén a
    // tulajdonság hiányozhat.
    readonly property bool captionVisible:
        (controller && controller.captionVisible !== undefined)
            ? controller.captionVisible : true

    function billentsdAFeliratot() {
        if (controller && controller.toggleCaptionVisible !== undefined)
            controller.toggleCaptionVisible()
    }

    // #1072: a megnyitott kép útvonala és a KOLLÁZS-ÁLLAPOTA. A két gomb
    // (Kollázs szerkesztése / Létrehozás) ugyanezt kérdezi, ezért itt áll
    // egyszer — a `filePathAt` hívást háromszor beírni néma szétcsúszás.
    //
    // ⚠️ A `collageSavedPath` SZÁNDÉKOS függőség a kifejezésben: az
    // `isCollageDraft` egy slot, nem értesítő tulajdonság, tehát magától
    // soha nem értékelődne újra. A piszkozat befejezésekor viszont épp ez
    // a tulajdonos változik meg — enélkül a „Létrehozás" gomb a kész
    // kollázs fölött is ottmaradna. Kötési hurok nincs: a gomb nem írja.
    readonly property string currentFilePath:
        (viewer.currentIndex >= 0 && viewer.photosModel !== null)
            ? viewer.photosModel.filePathAt(viewer.currentIndex) : ""
    readonly property bool controllerReady:
        typeof controller !== "undefined" && controller ? true : false
    // #4499: a beállítás az állóképes előnézet bal kattintását is
    // vezérli. Önálló néző-próbáknál és részleges vezérlőknél maradjon ki.
    readonly property bool singleClickExitEnabled:
        viewer.controllerReady && controller.singleClickExitEnabled !== undefined
            ? controller.singleClickExitEnabled : false
    readonly property bool currentIsCollageDraft: {
        if (!viewer.controllerReady || viewer.currentFilePath.length === 0)
            return false
        return controller.collageSavedPath !== undefined
               && controller.isCollageDraft(viewer.currentFilePath) === true
    }
    readonly property bool currentIsSavedCollage: {
        if (!viewer.controllerReady || viewer.currentFilePath.length === 0)
            return false
        return controller.collageSavedPath !== undefined
               && controller.hasCollageProject(viewer.currentFilePath) === true
    }

    //: #2114: a megnyitott fájl egy MOZGÓFILM-projekt kimenete-e. A
    //: `currentIsSavedCollage` ikerpárja: az eredetiben a két gomb
    //: (`editpanel/editcollage` és `editpanel/editslideshow`) UGYANABBAN a
    //: kezelőben él (`0x00567a00`), és mindkettő `m_hidden` — csak a
    //: projekt kimenetén jön elő. A feltétel nálunk is ugyanaz: a fájl
    //: mellett ott a projektfájl (`.mxf`, a #3191 írja ki).
    readonly property bool currentIsSavedMovie: {
        if (!viewer.controllerReady || viewer.currentFilePath.length === 0)
            return false
        return controller.hasMovieProject !== undefined
               && controller.hasMovieProject(viewer.currentFilePath) === true
    }

    // #641: mekkora magasság kell ahhoz, hogy a bal panel TELJESEN elférjen
    // — a felső sáv plusz a panel saját igénye. Beégetett szám nincs benne:
    // mindkét tag a saját elemétől jön.
    readonly property real panelPreferredHeight:
        viewerTopBarComponent.height + editorPanel.implicitHeight

    // #703: ennyi kell ahhoz, hogy a Visszavonás/Újra sornak MINDIG legyen
    // helye — a fülek tartalma nélkül. Ez a garancia alsó korlátja: a
    // képernyőhöz igazítás sem mehet ez alá.
    readonly property real minimumUsableHeight:
        viewerTopBarComponent.height + editorPanel.chromeHeight

    // #703: a főablak azon sávjai, amelyek a nézőn KÍVÜL esnek (menüsor,
    // eszköztár-fejléc, alsó tálca) — a néző csak a maradékot kapja meg.
    // A `Main.qml` a menüsort külön hozzáadja az ablak minimumához, ezért
    // itt mindhármat le kell vonni a képernyő-költségvetésből.
    readonly property var hostWindow: viewer.Window.window
    readonly property real windowChromeHeight: {
        var w = viewer.hostWindow
        if (!w) return 0
        var extra = 0
        if (w.menuBar) extra += w.menuBar.height
        if (w.header) extra += w.header.height
        if (w.footer) extra += w.footer.height
        return extra
    }
    // Az ablakkeret és a címsor magassága: a Qt ezt az ablak megjelenése
    // ELŐTT nem közli, márpedig a minimumot már akkor be kell jelenteni.
    // Ezért fenntartott keret. Bőkezűen mérve: inkább vágódjon egy csempesor
    // egy alacsony kijelzőn, mint hogy olyan ablak-minimumot kérjünk, amit a
    // kijelző nem tud kiadni — abból a felhasználó a gombsort egyáltalán nem
    // látja (#703).
    readonly property real windowDecorationAllowance: 56

    // #703: A #641 az ablak minimális magasságára tette a „mindig elfér"
    // garanciát (Main.qml) — csakhogy ezt a bejelentést az ablakkezelő csak
    // akkor tudja teljesíteni, ha a kijelzőre ráfér. Élesben, bélyegképes
    // csempékkel a panel igénye 887 px (a legmagasabb fül, a #571 „Régi
    // effektek", egymaga 799), az ablak minimuma ebből 962 — ez egy 768 vagy
    // 900 képpontos laptop-kijelzőn KIADHATATLAN. Ilyenkor a garancia nem
    // „majdnem" teljesül, hanem sehogy.
    //
    // Ezért a kérés a képernyőhöz igazodik: sosem kérünk többet, mint amennyi
    // ténylegesen van, és sosem kevesebbet, mint amennyi a gombsorhoz kell.
    // Ha emiatt a fül tartalma nem fér ki, azt az EditorPanel a
    // `tabContentTruncated` ágán, vágással kezeli — a gombsor soha nem veszít.
    //
    // Property (nem readonly): a teszt felül tudja írni, hogy a „kicsi
    // kijelző" esetet a futtató gép képernyőjétől függetlenül lehessen mérni.
    property real screenHeightBudget:
        Screen.desktopAvailableHeight - viewer.windowChromeHeight
        - viewer.windowDecorationAllowance

    readonly property real requiredHeight:
        Math.min(viewer.panelPreferredHeight,
                 Math.max(viewer.minimumUsableHeight, viewer.screenHeightBudget))
    color: Theme.viewerBg

    property var photosModel: null
    // #305: null-őr — az editController a QML-engine leépítésekor
    // átmenetileg null lehet, miközben a lenti kötések utoljára
    // kiértékelődnek.
    readonly property var editCtl: editController

    //: #3187: a kettős nézet MÁSODIK felének szerkesztő-vezérlője (saját
    //: előnézet-rekesz). AB módban a másik oldal MÁS fotót mutat, és azt
    //: ugyanúgy a mentett láncával kell látni, mint a rácsban vagy egy
    //: képes nézetben.
    //:
    //: #3014: „aa" módban a NEM kijelölt fél önálló, CSAK MEMÓRIÁBAN élő
    //: szerkesztési állapota (`docs/specs/ui-audit-editor.md` 4/b.1): a két
    //: fél ugyanarról a láncról indul, és egymástól függetlenül szerkeszthető.
    //: Ez a #3013 „bal = szerkesztés előtti" viselkedését váltja fel.
    //: #305-mintájú null-őr: a motor leépítésekor a kontextus eltűnhet.
    readonly property var masodikEditCtl:
        (typeof secondPreview !== "undefined") ? secondPreview : null

    // GPU élő-előnézet (#22): a finetune-csúszkák AKTÍV húzása alatt igaz —
    // az EditorPanel finetunePreview→finetuneCommit életciklusa keretezi
    // (ld. lent, az editorPanel bekötésénél). `gpuFinetuneEligible` a
    // KÉT feltétel: (a) a futtatókörnyezet RHI-alapú grafikai kontextust
    // ad (GPU-képtelen — pl. CI offscreen/software — környezetben ez
    // MINDIG false, néma és biztonságos fallback a rendes CPU-útra), és
    // (b) a jelenlegi szerkesztési lánc GPU-alkalmas
    // (`EditController.gpuPrefixSource` nem üres — ld. ott a feltételt).
    property bool gpuFinetuneActive: false
    // #551: a húzás alatti derítőfény-érték nulla-e. Nem nullánál a
    // finomhangolás nem fejezhető ki csatornánkénti LUT-tal (a Derítőfény
    // világosság-vezérelt), ezért a GPU-réteg ilyenkor NEM jelenhet meg —
    // a CPU-előnézet fut helyette, változatlanul.
    property bool gpuFinetunePointSafe: true
    // #4336: a Nézet-menü és a bal fiók nyila ugyanazt a mentett állapotot
    // használja. Önálló PhotoViewer-próbánál controller nélkül nyitva indul.
    property bool editorControlsVisible:
        (typeof controller !== "undefined" && controller
         && controller.editorControlsVisible !== undefined)
        ? controller.editorControlsVisible : true
    readonly property bool uiTransitionsEnabled:
        !viewer.controllerReady || controller.uiTransitionsEnabled === undefined
            ? true : controller.uiTransitionsEnabled
    // #4183: a szerkesztő bal fiókjának 0…−279 képpontos eltérése. A
    // befoglaló hely vele együtt szűkül, a 280 px-es tartalom pedig balra
    // csúszik és a fiók levágása rejti el.
    property real editorDrawerOffset: editorControlsVisible ? 0 : -279
    // A tényleges átmenet állapota megkülönbözteti az animációt az azonnali
    // végértékre ugrástól; a teszt nem függ a képkockák mintavételezésétől.
    readonly property bool editorDrawerAnimationRunning:
        editorDrawerOffsetAnimation.running
    Behavior on editorDrawerOffset {
        enabled: viewer.uiTransitionsEnabled
        NumberAnimation {
            id: editorDrawerOffsetAnimation
            objectName: "viewerEditorDrawerAnimation"
            duration: 250
            easing.type: Easing.InOutQuad
        }
    }
    function toggleEditorDrawer() { return viewerEditWorkflow.toggleEditorDrawer() }

    readonly property bool gpuCapable: GraphicsInfo.api !== GraphicsInfo.Software
                                        && GraphicsInfo.api !== GraphicsInfo.Unknown
                                        && GraphicsInfo.api !== GraphicsInfo.Null
    readonly property bool gpuFinetuneEligible: viewer.gpuCapable
        && viewer.editCtl && viewer.editCtl.gpuPrefixSource !== ""

    property int currentIndex: -1
    // #4698: Ctrl+F9 az eredeti Picasában a nézőt folyamatosan lépteti.
    // A Timer minden betöltött kép után, a következő eseményciklusban hívja
    // a szokásos `next()` utat. A jelző megkülönbözteti ezt a lépést a kézi
    // lapozástól, amely leállítja az időzítőt.
    property bool ctrlF9AutoStep: false
    function stopCtrlF9AutoAdvance() { return viewerNavigation.stopCtrlF9AutoAdvance() }
    function startCtrlF9AutoAdvance() { return viewerNavigation.startCtrlF9AutoAdvance() }
    Timer {
        id: ctrlF9AutoAdvanceTimer
        objectName: "ctrlF9AutoAdvanceTimer"
        interval: 1
        repeat: true
        onTriggered: {
            if (!viewer.visible) {
                stop()
                return
            }
            // Csak akkor váltunk, ha az aktuális kép már betöltődött. Így a
            // 0/1 ms-os eseményközi ütemezés nem ugorja át a képkockákat.
            if (viewer.isCurrentVideo
                    ? videoLoader.status === Loader.Loading
                    : photo.status === Image.Loading)
                return
            if (!viewer.hasNext()) {
                stop()
                return
            }
            viewer.ctrlF9AutoStep = true
            viewer.next()
            viewer.ctrlF9AutoStep = false
        }
    }
    // a ListView.count reaktív — a rowCount() hívást a QML nem követné
    property int photoCount: filmstrip.count
    // #14: az aktuális elem videó-e — a néző ekkor a lejátszó-nézetet
    // mutatja a fotó-Image helyett (a revision miatt modell-frissülésre
    // is újraértékelődik)
    readonly property bool isCurrentVideo: photosModel
        ? (photosModel.revision,
           photosModel.isVideoAt(currentIndex)) === true
        : false
    signal closed()
    // #8: a felső ▶ Lejátszás gomb — diavetítés az aktuális képtől
    signal playRequested()
    signal starRequested(int row)
    signal rotateRequested(int row, int delta)
    //: #1002: a megnyitott kollázs újranyitása SZERKESZTÉSRE. A néző
    //: csak JELEZ — a lapváltás és a panel feltöltése a gazdáé.
    signal editCollageRequested(string path)
    //: #2114: a film forrásprojektjének újranyitása
    signal editMovieRequested(string path)
    // #422/#4621: a néző törlés-parancsa (Ctrl+Delete és a helyi menü
    // tétele) — a nézetfüggő elágazás (lemezről törlés vagy eltávolítás az
    // albumból) és a megerősítők a Main.qml-ben élnek, ezért a kérés
    // jelként megy kifelé; a célt (az aktív kép sorát) a gazda adja
    signal deleteRequested()
    // #4621: albumból megnyitott képen a törlés-parancs az albumból
    // eltávolít — a helyi menü felirata ezt mutatja (a gazda köti)
    property bool deleteRemovesFromAlbum: false
    // #422: a mentés-szemantika parancsai a nézőből — a gazda (Main.qml)
    // ugyanazokat a megerősítéseket nyitja, mint a rácsban
    signal saveRequested(int row)
    signal revertRequested(int row)
    signal undoAllEditsRequested(int row)
    signal resetFacesRequested()
    //: #2566: a Helyek-panel két művelete a nézőből is a GAZDA
    //: megerősítésén megy át — ugyanazok a párbeszédek, mint a
    //: könyvtár-nézetben (`panelClearGeotagDialog`, `setGeotagDialog`).
    signal clearGeotagRequested(var rows)
    signal setGeotagRequested(var rows, real latitude, real longitude)
    signal dropGeotagRequested(var rows, real latitude, real longitude)
    signal manualFaceAddCancelRequested()
    //: #2566: a fiók két KIVEZETŐ parancsa. Mindkettő a könyvtár tartalmát
    //: cseréli le (keresés, illetve személy-album), amit a néző eltakarna —
    //: ezért nem a néző hajtja végre, hanem a gazda: az zárja a nézőt, és
    //: utána vált nézetet.
    signal findTaggedRequested(string keyword)
    signal personChosen(string name)

    // #192: a Tulajdonságok-panel a nézőben is — a könyvtár-nézet közös
    // kapcsolóját (Main.qml: window.propertiesPanelOpen) követi. A fő
    // ablakot a Window attached property adja, így a (forró) Main.qml-hez
    // nem kell hozzányúlni; önálló (teszt-)példányosításnál a kapcsoló
    // hiányzik → a panel rejtve marad.
    readonly property var appWindow: Window.window
    readonly property bool quickViewerMode: appWindow
        && appWindow.quickViewerLaunch === true
    // A Picasa Web Albums feltöltése kivezetett funkció; a gomb csak
    // képességjelzésként jelenik meg, ezért a kezelőfelület nem aktiválhatja.
    readonly property bool quickUploadAvailable: false
    readonly property bool propertiesOpen: viewer.quickViewerMode ? false
        : (appWindow ? appWindow.propertiesPanelOpen === true : false)

    //: #2566: a jobb fiók MÁSIK HÁROM lapja — a #192 mintája szerint. A
    //: négy kapcsolót a képtálca gombjai és a Nézet menü írják, de eddig
    //: csak a Tulajdonságok panelnek volt párja a nézőben; a másik három a
    //: könyvtár `SplitView`-jében ült, amit a néző elrejt, tehát a gomb
    //: benyomódott és nem történt semmi.
    //:
    //: MÉRVE (`thumbui.tre:526`, `:533`): a `right_drawer` a
    //: `mainuipanel` gyereke, és a szerkesztő-módot leíró
    //: `macros.tre:204` (`m_albumtoggle`) TÉTELESEN sorolja fel, mit rejt
    //: el — a `right_drawer` és a `mainuipanel` NINCS köztük. Az
    //: eredetiben tehát a jobb fiók a szerkesztőben is elérhető.
    //:
    //: ⚠️ TERNÁRIUS, nem `&&`: a JS `&&` a HAMIS operandust adja vissza
    //: (itt `null`-t), amit a Qt nem tud bool-ra kötni.
    readonly property bool tagsOpen: viewer.quickViewerMode ? false
        : (viewer.appWindow ? viewer.appWindow.tagsPanelOpen === true : false)
    readonly property bool placesOpen: viewer.quickViewerMode ? false
        : (viewer.appWindow ? viewer.appWindow.placesPanelOpen === true : false)
    readonly property bool peopleOpen: viewer.quickViewerMode ? false
        : (viewer.appWindow ? viewer.appWindow.peoplePanelOpen === true : false)

    //: #2566: a fiók A NÉZETT KÉPRE hat, nem a rács kijelölésére. A néző
    //: léptetése csak a `selectedIndex`-et írja, a `selectedIndexes`-t nem
    //: (Main.qml `onCurrentIndexChanged`), ezért a rács kijelölésére kötött
    //: panel a nézőben elavult képet mutatna.
    readonly property var drawerRows:
        viewer.currentIndex >= 0 ? [viewer.currentIndex] : []

    // #147/#4572: a mentett keretek csak a facesVisible kapcsolóra látszanak;
    // indexbeli névtelen arcok rejtve maradnak, de kattinthatók. A
    // photosModel.revision és facesEditRevision újraértékeli a lekérdezést.
    property bool facesVisible: false
    function toggleFaces() { viewer.facesVisible = !viewer.facesVisible }
    // #26 (2. kör): arc-téglalap SZERKESZTŐ mód — rajzolás/átnevezés/
    // törlés a nézőben. A szerkesztés bekapcsolása egyben láthatóvá is
    // teszi a kereteket (nincs értelme vakon szerkeszteni).
    property bool facesEditMode: false
    function beginManualFaceAdd() {
        viewer.facesEditMode = true
        viewer.facesVisible = true
        if (viewer.appWindow
                && typeof viewer.appWindow.valtsFiokLapot === "function")
            viewer.appWindow.valtsFiokLapot("people")
    }
    function cancelManualFaceAdd() {
        viewer.manualFaceAddCancelRequested()
    }
    function toggleFacesEdit() {
        if (viewer.facesEditMode)
            viewer.cancelManualFaceAdd()
        else
            viewer.beginManualFaceAdd()
    }
    // az overlay minden sikeres írás (facesOverlay.edited) után növeli —
    // az ini-módosítást a photosModel/index NEM látja, ez a kényszerített
    // újraértékelés-kapcsoló a facesFor() friss lekérdezéséhez
    property int facesEditRevision: 0
    property int manualFaceAddRevision: 0
    Connections {
        target: viewer.appWindow
            ? viewer.appWindow._faceScanController : null
        function onUnnamedCountChanged() { viewer.facesEditRevision += 1 }
    }
    //: #3741: a KIJELÖLT fél fotójáé (`aktivSor`) — kettős nézetben bal
    //: fókusznál ez a bal kép, nem a `currentIndex`-é.
    readonly property var currentFaces: (!photosModel || viewer.aktivSor < 0
                                          || typeof facesHelper === "undefined"
                                          || !facesHelper)
        ? []
        : (photosModel.revision, viewer.facesEditRevision,
           facesHelper.facesFor(photosModel.filePathAt(viewer.aktivSor)))
    readonly property bool hasDetectedFaceHitTargets: {
        var items = viewer.currentFaces
        for (var i = 0; i < items.length; ++i)
            if (items[i].detected === true) return true
        return false
    }

    // -- zoom-állapotgép (#6, #2492): fit / 1:1 / tetszőleges ------------
    //
    // ⚠️ #2492: az igazságforrás a NORMALIZÁLT csúszka-érték (`zoomValue`,
    // [0, 1]), nem a szorzó. Ez az eredeti Picasa mért működése
    // (`docs/specs/ui-audit-editor.md`, „A szerkesztő NAGYÍTÁS-HÁRMASA"):
    // a `FUN_005d1c70` a csúszka értékéből választja ki, melyik gomb az
    // aktív, `0.0` = illesztés és `0.5` = valódi méret. Korábban nálunk a
    // csúszka a SZORZÓT tárolta lineárisan (0,25…8), ezért az „1:1" nem
    // a felezőpontra esett — a tulajdonos ezt jelentette (v0.8.293).
    //
    // zoomValue: 0 = illesztés, 0,5 = valódi méret (100 %), 1 = 400 %.
    property real zoomValue: 0

    // A tálca nagyítás-csúszkája közvetlenül a fenti `zoomValue`-ból kapja
    // az értéket (`Main.qml` → `TrayBar.viewerZoomValue`). Az új komponensek
    // nyilvános aliasait csak ezután deklaráljuk, hogy a gyökér állapotforrása
    // készüljön el előbb a komponenshatáron átvezetett kötések előtt.
    property alias editorPanel: leftDrawer.hostEditorPanel
    property alias cropOverlay: photoArea.hostCropOverlay
    property alias editorToolBar: photoArea.hostEditorToolBar
    property alias effectColorPickArea: photoArea.hostEffectColorPickArea
    property alias facesOverlay: photoArea.hostFacesOverlay
    property alias gpuPrefixImage: photoArea.hostGpuPrefixImage
    property alias kepkockaJelzes: photoArea.hostKepkockaJelzes
    property alias neutralPickArea: photoArea.hostNeutralPickArea
    property alias paintMaskArea: photoArea.hostPaintMaskArea
    property alias photo: photoArea.hostPhoto
    property alias photoElotte: photoArea.hostPhotoElotte
    property alias photoElotteKeret: photoArea.hostPhotoElotteKeret
    property alias photoKeret: photoArea.hostPhotoKeret
    property alias redeyeDragArea: photoArea.hostRedeyeDragArea
    property alias retouchClickArea: photoArea.hostRetouchClickArea
    property alias textClickArea: photoArea.hostTextClickArea
    property alias videoLoader: photoArea.hostVideoLoader

    //: a MÉRT leképezés szerint számolt szorzó az ILLESZTETT mérethez képest
    //: #3013: a KETTŐS NÉZET üzemmódja — `editpanel/layout_2up_group`.
    //: `"1up"` (alapértelmezés, `Property setpressed 1`), `"aa"` (ugyanaz a
    //: kép kétszer, két önálló szerkesztéssel — #3014), `"ab"` (két
    //: különböző kép — a #3014 hozza). Váltani a `modotValt()`-tal kell.
    property string layoutMode: "1up"
    //: melyik oldal az aktív — a „Kijelölve" jelvény ezt mutatja.
    //: #3773: az eredeti Picasában 2-up módba lépéskor a BAL a kijelölt
    //: (a bal a `currentIndex`-et, a jelenlegi képet mutatja) — mérve a
    //: `Colab EN 33` referencia-képen.
    property string aktivOldal: "bal"
    //: #3014: `swap_2up_layout` — a két kép egymás MELLETT (hamis) vagy
    //: egymás ALATT (igaz). Az ütközés-párbeszéd gombfeliratai is ezen
    //: múlnak („Bal/Jobb" vs. „Fent/Lent"), ld. a spec 4. tábláját.
    property bool fuggolegesElrendezes: false
    //: #3014: AB módban a MÁSIK kép rács-sora. `-1` = még nincs külön
    //: választva, ilyenkor a szomszédos kép jön (a filmszalag sorrendje
    //: szerint), hogy a mód bekapcsolva azonnal KÉT KÜLÖNBÖZŐ képet adjon
    //: — ez a mód buboréksúgójának ígérete.
    property int masodikIndex: -1
    onMasodikIndexChanged: {
        if (ctrlF9AutoAdvanceTimer.running && !ctrlF9AutoStep)
            stopCtrlF9AutoAdvance()
    }

    //: #3014: a KIJELÖLT oldal rács-sora — a „Kijelölve" jelvény ezt
    //: mutatja, és a válogató parancsok (albumba tétel) erre hatnak.
    //: Egy kép módban mindig a jelenlegi kép.
    //:
    //: #3187: a SZERKESZTŐ parancsai is ezt a sort célozzák. A fő vezérlő
    //: mindig a kijelölt oldalt szerkeszti, a második rekesz a másikat —
    //: így a szerkesztő-panel 104 kötése változatlan maradt.
    //: ⚠️ Imperatív kezelőben NE ezt a kötött property-t olvasd, hanem a
    //: `_kijeloltSort()`-ot: a kötés újraértékelése nem garantált, mire az
    //: ugyanarra a jelzésre futó kezelő lefut (#218, mérve a #3187-en).
    //: #3773: a BAL fél a `currentIndex`-et mutatja, a JOBB a
    //: `abMasikSor`-t (ld. lent, a `photoElotte`/`photo` forrása) — a
    //: kijelölt sor ezért `jobb` fókusznál `abMasikSor`.
    readonly property int aktivSor: (viewer.layoutMode !== "1up"
                                     && viewer.aktivOldal === "jobb")
        ? viewer.abMasikSor : viewer.currentIndex

    //: #3741: a kijelölt kép a BAL/FELSŐ félen áll (`photoElotte`). Egy
    //: képes módban mindig hamis — az `aktivOldal` a módváltás után is
    //: „bal" maradhat, de ott csak a `photo` látszik.
    readonly property bool balFokusz: viewer.layoutMode !== "1up"
                                      && viewer.aktivOldal === "bal"

    //: #3663: a „Kijelölve" jelvény MÉRT mérete (`Colab EN 33`, 1280×1024)
    //: és a KIRAJZOLT képtől mért rése: a képek síkjával PÁRHUZAMOS
    //: tengelyen (vízszintesben az osztó felé, függőlegesben a bal margó
    //: felé) ~61 px, a MERŐLEGES tengelyen ~27 px.
    readonly property int jelvenySzel: 86
    readonly property int jelvenyMag: 26
    readonly property int jelvenyParhuzamosRes: 61
    readonly property int jelvenyMerolegesRes: 27

    //: #3756: a jelvény a kép MELLETT, a margóban áll — kettős nézetben
    //: mindkét fél fenntartja neki a helyet: vízszintesen FELÜL
    //: (magasság + merőleges rés), függőlegesen BALRA (szélesség +
    //: párhuzamos rés). Ahol a kép saját margója ennél nagyobb (pl. a
    //: #3663 négyzetes képeinél), a kép a helyén marad.
    readonly property int jelvenyHelyFent: viewer.layoutMode !== "1up"
        && !viewer.fuggolegesElrendezes
        ? viewer.jelvenyMag + viewer.jelvenyMerolegesRes : 0
    readonly property int jelvenyHelyBal: viewer.layoutMode !== "1up"
        && viewer.fuggolegesElrendezes
        ? viewer.jelvenySzel + viewer.jelvenyParhuzamosRes : 0

    //: #3756: egy fél képének illesztési doboza a KÉPERNYŐN (forgatás
    //: utáni tengelyekkel) a `keretSzel`×`keretMag` kereten belül, a
    //: jelvény helyének fenntartásával. `arany` a képernyőn látszó
    //: szélesség/magasság (0 = még nem ismert: ilyenkor a teljes keret).
    //: Visszaad: `{szel, mag, dx, dy}` — a doboz mérete és a középpontjának
    //: eltolása a keret közepéhez képest.
    // A fotó geometriai és nagyítási állapota.
    readonly property int texturaEl: viewerGeometry.texturaEl
    readonly property int abMasikSor: viewerGeometry.abMasikSor
    readonly property real zoomFactor: viewerGeometry.zoomFactor
    property alias zoomNavigatorDismissed: viewerGeometry.zoomNavigatorDismissed
    readonly property string zoomMode: viewerGeometry.zoomMode
    property alias panX: viewerGeometry.panX
    property alias panY: viewerGeometry.panY
    readonly property bool photoOverlaysUsable: viewerGeometry.photoOverlaysUsable
    readonly property real zoomDetent: viewerGeometry.zoomDetent
    readonly property rect zoomNavigatorViewRect: viewerGeometry.zoomNavigatorViewRect
    readonly property var forceFitFilters: viewerGeometry.forceFitFilters
    readonly property int valodiSzelesseg: viewerGeometry.valodiSzelesseg

    function illesztesiDoboz(keretSzel, keretMag, arany) { return viewerGeometry.illesztesiDoboz(keretSzel, keretMag, arany) }
    function forrasMeret(index, url) { return viewerGeometry.forrasMeret(index, url) }
    function _betoltesekIrasa() { return viewerGeometry._betoltesekIrasa() }
    function _betolt(kep, par) { return viewerGeometry._betolt(kep, par) }
    function _par(sor, url) { return viewerGeometry._par(sor, url) }
    function _videoE() { return viewerGeometry._videoE() }
    function _photoPar(sor) { return viewerGeometry._photoPar(sor) }
    function _elotoltoPar(irany) { return viewerGeometry._elotoltoPar(irany) }
    function _abMasikSort() { return viewerGeometry._abMasikSort() }
    function forceFitForFilter(filterName) { return viewerGeometry.forceFitForFilter(filterName) }
    function actualZoomFactor() { return viewerGeometry.actualZoomFactor() }
    function skalaErtekbol(v) { return viewerGeometry.skalaErtekbol(v) }
    function setZoomValue(v) { return viewerGeometry.setZoomValue(v) }
    function zoomFit() { return viewerGeometry.zoomFit() }
    function zoomActual() { return viewerGeometry.zoomActual() }
    function lepjZoom(delta) { return viewerGeometry.lepjZoom(delta) }
    function wheelZoom(delta) { return viewerGeometry.wheelZoom(delta) }
    function clampPan() { return viewerGeometry.clampPan() }
    function panFromZoomNavigator(deltaX, deltaY) { return viewerGeometry.panFromZoomNavigator(deltaX, deltaY) }
    function show(index) { return viewerGeometry.show(index) }
    function selectMenuEffect(name) { return viewerGeometry.selectMenuEffect(name) }
    function applyCrop(advance) { return viewerGeometry.applyCrop(advance) }

    PhotoViewerGeometryActions {
        id: viewerGeometry
        hostViewer: viewer
        hostPhotoArea: photoArea
        hostEditController: viewer.editCtl
        nextPreloadImage: viewerOverlayControls.nextPreloadImage
        previousPreloadImage: viewerOverlayControls.previousPreloadImage
    }

    readonly property int masodikSor: viewerEditWorkflow.masodikSor
    property alias aaMunkamenet: viewerEditWorkflow.aaMunkamenet
    property alias aaKiindulas: viewerEditWorkflow.aaKiindulas
    property alias aaFotoId: viewerEditWorkflow.aaFotoId
    property alias aaFolytatas: viewerEditWorkflow.aaFolytatas
    property alias aaKerdesFut: viewerEditWorkflow.aaKerdesFut
    property alias endEditFolytatas: viewerEditWorkflow.endEditFolytatas
    property alias cropNyitaskoriKijeloles:
        viewerEditWorkflow.cropNyitaskoriKijeloles
    property alias tiltSzinkronFut: viewerEditWorkflow.tiltSzinkronFut
    property alias tiltAlkalmazasFut: viewerEditWorkflow.tiltAlkalmazasFut
    property alias tiltErtekNyitaskor: viewerEditWorkflow.tiltErtekNyitaskor

    function _kijeloltSort() { return viewerEditWorkflow._kijeloltSort() }
    function _masodikSort() { return viewerEditWorkflow._masodikSort() }
    function frissitsdAMasodikSzerkesztest() { return viewerEditWorkflow.frissitsdAMasodikSzerkesztest() }
    function frissitsdALemezműveletUtániElőnézetet(utvonalak) { return viewerEditWorkflow.frissitsdALemezműveletUtániElőnézetet(utvonalak) }
    function _cropKijeloles() { return viewerEditWorkflow._cropKijeloles() }
    function _cropNyitaskoriMegjegyez() { return viewerEditWorkflow._cropNyitaskoriMegjegyez() }
    function _cropModosult() { return viewerEditWorkflow._cropModosult() }
    function _aaFelLanca(fel) { return viewerEditWorkflow._aaFelLanca(fel) }
    function _aaAktivFel() { return viewerEditWorkflow._aaAktivFel() }
    function _aaDontes(neKerdezzen) { return viewerEditWorkflow._aaDontes(neKerdezzen) }
    function _aaMegtart(fel) { return viewerEditWorkflow._aaMegtart(fel) }
    function _aaLezaras() { return viewerEditWorkflow._aaLezaras() }
    function _aaNeKerdezzen() { return viewerEditWorkflow._aaNeKerdezzen() }
    function aaKilepesKapu(folytatas) { return viewerEditWorkflow.aaKilepesKapu(folytatas) }
    function _nyitottEszkozModosult() { return viewerEditWorkflow._nyitottEszkozModosult() }
    function _nyitottEszkozLezar(alkalmaz) { return viewerEditWorkflow._nyitottEszkozLezar(alkalmaz) }
    function _eszkozZarasKapu(folytatas, megseEngedve) { return viewerEditWorkflow._eszkozZarasKapu(folytatas, megseEngedve) }
    function modotValt(uj) { return viewerEditWorkflow.modotValt(uj) }
    function _modotValtEszkozUtan(uj) { return viewerEditWorkflow._modotValtEszkozUtan(uj) }
    function fokuszValt(uj) { return viewerEditWorkflow.fokuszValt(uj) }
    function _aaLapozasKapu() { return viewerEditWorkflow._aaLapozasKapu() }
    function kerBezaras() { return viewerEditWorkflow.kerBezaras() }
    function _aaFeleketCserel() { return viewerEditWorkflow._aaFeleketCserel() }
    function beginEditCurrent() { return viewerEditWorkflow.beginEditCurrent() }
    function syncTiltSlider() { return viewerEditWorkflow.syncTiltSlider() }
    function syncPanelFromController() { return viewerEditWorkflow.syncPanelFromController() }

    PhotoViewerEditWorkflow {
        id: viewerEditWorkflow
        hostViewer: viewer
        hostEditController: viewer.editCtl
    }

    property alias wheelAccum: viewerNavigation.wheelAccum
    function next() { return viewerNavigation.next() }
    function previous() { return viewerNavigation.previous() }
    function _vanSzomszed(sor, irany) { return viewerNavigation._vanSzomszed(sor, irany) }
    function hasNext() { return viewerNavigation.hasNext() }
    function hasPrevious() { return viewerNavigation.hasPrevious() }
    function wheelStep(delta) { return viewerNavigation.wheelStep(delta) }
    function urlAt(index) { return viewerNavigation.urlAt(index) }
    function preloadUrlAt(index) { return viewerNavigation.preloadUrlAt(index) }
    function handleReturnPressed() { return viewerNavigation.handleReturnPressed() }
    PhotoViewerNavigation {
        id: viewerNavigation
        hostViewer: viewer
        hostAutoAdvanceTimer: ctrlF9AutoAdvanceTimer
    }

    focus: visible
    // Az Esc az AKTÍV mód-eszközt szakítja meg, és csak ha nincs ilyen,
    // akkor zárja a nézőt — ez az eredeti Picasa viselkedése.
    //
    // #445: a retusálás félbehagyott foltját dobja el (a súgószöveg
    // szerinti irányított klónozás megszakítása).
    // #666: a vágást ugyanúgy meg kell szakítania, mint a panel Mégse
    // gombjának — korábban a néző BEZÁRULT, és a megkezdett vágás elveszett.
    //
    // A logika külön függvényben él, hogy tesztelhető legyen; a billentyű-
    // kötés csak továbbhív (a `test_viewer_escape_666.py` mindkettőt őrzi).
    function handleEscape() {
        if (editorPanel.paramPanelActive)
            editorPanel.cancelParamPanel()
        else if (editorPanel.retouchActive && editorPanel.retouchPatchPending)
            editController.cancelRetouchPatch()
        else if (editorPanel.cropActive)
            editorPanel.cropCancelRequested()
        else if (viewer.facesEditMode)
            viewer.cancelManualFaceAdd()
        else
            viewer.kerBezaras()
    }
    Keys.onEscapePressed: if (!viewer.textEntryHasFocus) viewer.handleEscape()
    Keys.onRightPressed: if (!viewer.textEntryHasFocus) next()
    Keys.onReturnPressed: viewer.handleReturnPressed()
    Keys.onLeftPressed: if (!viewer.textEntryHasFocus) previous()
    // szóköz: videónál lejátszás/szünet (#14) — Picasa-viselkedés
    Keys.onSpacePressed: {
        if (viewer.textEntryHasFocus)
            return
        if (viewer.isCurrentVideo && videoLoader.item)
            videoLoader.item.togglePlayback()
    }
    // F: arc-keretek be/ki (#147) — szövegmezőben (pl. felirat) a saját
    // Keys-kezelés (gépelés) már elfogadja, ide nem buborékol.
    // Shift+F: arc-SZERKESZTŐ mód be/ki (#26, 2. kör).
    //
    // #1418: a törlés a nézőben — akárcsak a rácsban — Ctrl+Delete (a
    // helyi menük rekordjai, docs/specs/picasa-gyorsbillentyuk.md 4.).
    // Ugyanazt az utat hívja, mint a jobbklikk-menü törlés-tétele
    // (onDeleteRequested lent): a gazda nézetfüggő elágazása (#4621).
    //
    // A `Main.qml` `shortcutDeleteFromDiskViewer`-e ezzel egy irányba
    // mutat: ott is `Ctrl+Delete` (#1418). A korábbi, puszta `Delete`
    // a #422 azóta felülírt feltételezéséből jött.
    Keys.onPressed: function(event) {
        if (viewer.textEntryHasFocus)
            return
        if (event.key === Qt.Key_F9
                && event.modifiers === Qt.ControlModifier) {
            if (!event.isAutoRepeat)
                viewer.startCtrlF9AutoAdvance()
            event.accepted = true
        } else if (event.key === Qt.Key_F && event.modifiers === Qt.NoModifier) {
            viewer.toggleFaces()
            event.accepted = true
        } else if (event.key === Qt.Key_F && event.modifiers === Qt.ShiftModifier) {
            viewer.toggleFacesEdit()
            event.accepted = true
        } else if (event.key === Qt.Key_Delete
                   && event.modifiers === Qt.ControlModifier) {
            if (viewer._aktivUt().length > 0)
                viewer.deleteRequested()
            event.accepted = true
        }
    }

    ColumnLayout {
        anchors.fill: parent
        // A gyorsnézet 67 px-es alsó sávját a 12.8.2 koordinátái adják:
        // a vezérlők a 800 px magas referencia-keret 733–769. sorában állnak.
        anchors.bottomMargin: viewer.quickViewerMode ? 67 : 0
        spacing: 0

        // felső sáv: vissza gomb + filmszalag nyilakkal
        PhotoViewerTopBar {
            id: viewerTopBarComponent
            Layout.fillWidth: true
            hostViewer: viewer
            hostLeftDrawer: leftDrawer
            hostPhotoArea: photoArea
            hostFilmstrip: filmstrip
            PhotoViewerFilmstrip {
                id: filmstrip
                hostViewer: viewer
                width: 214
                height: 28
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // bal eszközpanel — Gyakori javítások élesben (#19); a
            // Retusálás/Szöveg és a finomhangolás a #20-ban élesedik
            PhotoViewerLeftDrawer {
                id: leftDrawer
                Layout.preferredWidth: 280 + viewer.editorDrawerOffset
                Layout.minimumWidth: 1
                Layout.maximumWidth: 280
                Layout.fillHeight: true
                hostViewer: viewer
                hostPhotoArea: photoArea
                hostCropOverlay: cropOverlay
                hostCopyCaptionConfirmLoader: viewerContextActions.hostCopyCaptionConfirmLoader
                hostUndoDataLossDialogLoader: viewerContextActions.hostUndoDataLossDialogLoader
                hostMovieResetConfirmLoader: viewerContextActions.hostMovieResetConfirmLoader
                hostKepkockaJelzes: kepkockaJelzes
                hostVideoLoader: videoLoader
            }

            // fő képterület
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: Theme.viewerBg

                WheelHandler {
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                    // #6: Ctrl+görgő = zoom a kép fölött; sima görgő marad a
                    // képek közti lapozás (#77) — a két igény így fér össze
                    onWheel: function(event) {
                        if (event.modifiers & Qt.ControlModifier)
                            viewer.wheelZoom(event.angleDelta.y)
                        else
                            viewer.wheelStep(event.angleDelta.y)
                    }
                }

                PhotoViewerPhotoArea {
                    id: photoArea
                    hostViewer: viewer
                    hostViewerPanArea: viewerOverlayControls.hostViewerPanArea
                    hostEditorPanel: editorPanel
                }

                PhotoViewerOverlayControls {
                    id: viewerOverlayControls
                    anchors.fill: parent
                    hostViewer: viewer
                    hostPhotoArea: photoArea
                }
            }
            PhotoViewerRightPanels {
                hostViewer: viewer
            }
        }
    }

    PhotoViewerQuickToolbar {
        hostViewer: viewer
    }

    readonly property string currentPath: viewerContextActions.currentPath

    function zarjaAFiokot() { viewerContextActions.zarjaAFiokot() }
    function _aktivUt() { return viewerContextActions._aktivUt() }
    function openContextMenu(x, y) {
        viewerContextActions.openContextMenu(x, y)
    }

    PhotoViewerContextActions {
        id: viewerContextActions
        hostViewer: viewer
    }

}

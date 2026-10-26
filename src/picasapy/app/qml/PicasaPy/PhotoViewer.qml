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
        toggleEditorDrawerShortcut.sequence
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
        viewerTopBar.height + editorPanel.implicitHeight

    // #703: ennyi kell ahhoz, hogy a Visszavonás/Újra sornak MINDIG legyen
    // helye — a fülek tartalma nélkül. Ez a garancia alsó korlátja: a
    // képernyőhöz igazítás sem mehet ez alá.
    readonly property real minimumUsableHeight:
        viewerTopBar.height + editorPanel.chromeHeight

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
    function toggleEditorDrawer() {
        if (typeof controller !== "undefined" && controller
                && controller.setEditorControlsVisible !== undefined) {
            controller.setEditorControlsVisible(!controller.editorControlsVisible)
        } else {
            editorControlsVisible = !editorControlsVisible
        }
    }

    // #4696: az eredeti Ctrl+9 ága csak a szerkesztő-előnézetben fut
    // (`picasa-gyorsbillentyuk.md` 10.22). A néző láthatósága ennek a
    // nézetnek a kapuja; a könyvtárban a Shortcut le van tiltva.
    Shortcut {
        id: toggleEditorDrawerShortcut
        sequence: "Ctrl+9"
        enabled: viewer.visible
        onActivated: viewer.toggleEditorDrawer()
    }

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
    function stopCtrlF9AutoAdvance() {
        ctrlF9AutoAdvanceTimer.stop()
    }
    function startCtrlF9AutoAdvance() {
        if (!viewer.visible || !viewer.photosModel || !viewer.hasNext())
            return
        if (!ctrlF9AutoAdvanceTimer.running)
            ctrlF9AutoAdvanceTimer.start()
    }
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
    function illesztesiDoboz(keretSzel, keretMag, arany) {
        var teljes = { szel: keretSzel, mag: keretMag, dx: 0, dy: 0 }
        if (!(arany > 0)) return teljes
        var kepSzel = Math.min(keretSzel, keretMag * arany)
        var kepMag = kepSzel / arany
        var fent = viewer.jelvenyHelyFent
        if (fent > 0 && (keretMag - kepMag) / 2 < fent)
            return { szel: keretSzel, mag: keretMag - fent, dx: 0, dy: fent / 2 }
        var bal = viewer.jelvenyHelyBal
        if (bal > 0 && (keretSzel - kepSzel) / 2 < bal)
            return { szel: keretSzel - bal, mag: keretMag, dx: bal / 2, dy: 0 }
        return teljes
    }

    //: #3877: a `photo`/`photoElotte`/az elő-betöltők textúra-plafonja —
    //: ld. `SlideshowView.qml` `texturaEl` (#3832), ugyanaz a V3D-korlát.
    readonly property int texturaEl: 2560

    //: #3877: a kép `sourceSize`-a — a két betöltési út MÁST kér.
    //:
    //: - Szolgáltatós út (`image://…`): az állandó `texturaEl`-doboz, mint
    //:   a `gpuPrefixImage`-é (#3800). A szolgáltató magától csak kicsinyít
    //:   (`edit_preview.py` `_belefer`), KIVÉVE a képpontot jelölő
    //:   megjelenítési módot (#1576): az a kis képet szándékosan a kért
    //:   dobozra nagyítja, és utána jelöl. Natív méretet kérve a jelölés
    //:   natív méreten készülne, és a kirajzolás szétkenné (mérve: 640×400-as
    //:   PNG, „Túlcsordult képpontok").
    //: - Nyers `file://` út: a Qt fájlbetöltője a kért méretre FELNAGYÍT
    //:   (mérve valódi GPU-n: 1440×2560 és 3000×5333 is 2560×4551), ezért a
    //:   VALÓDI méretből (`pixelWidthAt`/`pixelHeightAt`, #2492) a dobozba
    //:   illő, legfeljebb natív méret kell — a fájlban TÁROLT tájolásban
    //:   (`pixelSidesSwappedAt`), mert a Qt a kért méretet arra alkalmazza.
    //:   Ugyanaz, mint a `SlideshowView.qml` `forrasMeret`-je (#3832).
    function forrasMeret(index, url) {
        var el = viewer.texturaEl
        if (String(url).indexOf("image://") === 0)
            return Qt.size(el, el)
        if (!viewer.photosModel || index < 0
                || typeof viewer.photosModel.pixelWidthAt !== "function")
            return Qt.size(el, 0)
        // a revision-referencia kötelező: a pixelWidthAt/pixelHeightAt
        // Slot-hívás, önmagában nem hoz létre kötés-függőséget (ld.
        // `valodiSzelesseg` ugyanezt a mintát fent)
        var szel = (viewer.photosModel.revision,
                    viewer.photosModel.pixelWidthAt(index))
        var mag = viewer.photosModel.pixelHeightAt(index)
        if (szel <= 0 || mag <= 0)
            return Qt.size(el, 0)
        var w = Math.min(el, szel)
        var h = Math.round(mag * w / szel)
        if (h > el) {
            h = el
            w = Math.round(szel * el / mag)
        }
        if (typeof viewer.photosModel.pixelSidesSwappedAt === "function"
                && viewer.photosModel.pixelSidesSwappedAt(index))
            return Qt.size(h, w)
        return Qt.size(w, h)
    }

    //: #3877: a forrás és a forrásméret EGYÜTT, egyetlen betöltéssel — a
    //: `SlideshowView.qml` `_betolt`-jának mintája (#3832). A Qt az `Image`
    //: `source`-ának ÉS `sourceSize`-ának MINDEN változására tölt; két külön
    //: kötésnél lépéskor mindkettő átfordul, és a kép egyszer a rossz párral
    //: is betöltődik (mérve: lépésenként elemenként 2–3 kérés, köztük egy
    //: 640×400-as kép 1440×2560-nal kérve → 4096×2560). Méretváltáskor
    //: ezért a forrás előbb kiürül (üres forrásra a Qt nem tölt), a méret
    //: beáll, és csak utána jön az új forrás.
    //:
    //: Az elemek `betoltes`-pár változását a `Qt.callLater` fogja össze egy
    //: írássá, a kör végén. Mérve: kettős nézetre váltáskor a `photo` párja
    //: még a `onLayoutModeChanged` ELŐTT kiértékelődik, amikor a második
    //: rekesz előnézete üres — így egyetlen körön belül előbb a nyers fájlt,
    //: aztán a szolgáltató helyőrzőjét, végül a kész képet kérte (3 kérés).
    function _betoltesekIrasa() {
        viewer._betolt(photoElotte, photoElotte.betoltes)
        viewer._betolt(photo, photo.betoltes)
        viewer._betolt(elotoltoKovetkezo, elotoltoKovetkezo.betoltes)
        viewer._betolt(elotoltoElozo, elotoltoElozo.betoltes)
    }
    function _betolt(kep, par) {
        var regi = kep.sourceSize
        var ujMeret = regi.width !== par.meret.width
            || regi.height !== par.meret.height
        if (!ujMeret && kep.source.toString() === String(par.url))
            return
        if (ujMeret) {
            kep.source = ""
            kep.sourceSize = par.meret
        }
        kep.source = par.url
    }

    //: #3877: a (forrás, méret) pár EGY kiértékelésben, ugyanabból a sorból
    //: — a kötött `abMasikSor`/`isCurrentVideo` helyett a friss függvényt
    //: és a modellt kérdezzük (#218), különben a pár egyik fele a régi, a
    //: másik az új képé lehetne.
    function _par(sor, url) {
        return { url: url, meret: viewer.forrasMeret(sor, url) }
    }
    function _videoE() {
        return viewer.photosModel
            ? (viewer.photosModel.revision,
               viewer.photosModel.isVideoAt(viewer.currentIndex)) === true
            : false
    }
    //: #3187/#3773: a `photo` a `sor` (az `abMasikSor`) fotóját mutatja. A
    //: FŐ vezérlő a KIJELÖLT oldalt szerkeszti, tehát egy képes módban (itt
    //: `sor === currentIndex`) és jobb fókusznál a FŐ vezérlő képe jön — a
    //: hozzárendelés a fókusszal cserél. Nyitott szerkesztésnél a
    //: `filters=` láncot alkalmazó `editpreview` szolgáltató rendereli
    //: (`?rev=` cache-buster), egyébként a nyers fájl jön.
    function _photoPar(sor) {
        var url = viewer._videoE() ? ""
            : (viewer.layoutMode === "1up" || viewer.aktivOldal === "jobb"
               ? (viewer.editCtl && viewer.editCtl.previewSource !== ""
                  ? viewer.editCtl.previewSource : viewer.urlAt(sor))
               : (viewer.masodikEditCtl
                  && viewer.masodikEditCtl.previewSource !== ""
                  ? viewer.masodikEditCtl.previewSource : viewer.urlAt(sor)))
        return viewer._par(sor, url)
    }
    function _elotoltoPar(irany) {
        var sor = viewer.photosModel
            ? viewer.photosModel.folderNeighbor(viewer.currentIndex, irany) : -1
        return viewer._par(sor, viewer.photosModel ? viewer.preloadUrlAt(sor) : "")
    }

    //: #3014: a ténylegesen megjelenített másik kép sora. AB módon kívül
    //: mindig a jelenlegi kép (az „aa" mód ugyanazt mutatja kétszer).
    //: #3773: a számítás FÜGGVÉNY (`_abMasikSort`), mert a kijelölt és a
    //: második sort az imperatív kezelők is ebből számolják — a kötött
    //: property ott még a RÉGI értéket adhatja (#218).
    readonly property int abMasikSor: viewer._abMasikSort()

    function _abMasikSort() {
        if (viewer.layoutMode !== "ab") return viewer.currentIndex
        if (viewer.masodikIndex >= 0) return viewer.masodikIndex
        return viewer._vanSzomszed(viewer.currentIndex, 1)
            ? viewer.currentIndex + 1
            : Math.max(0, viewer.currentIndex - 1)
    }

    readonly property real zoomFactor: viewer.skalaErtekbol(viewer.zoomValue)
    property bool zoomNavigatorDismissed: false
    readonly property string zoomMode:
        viewer.zoomValue === 0 ? "fit"
        : viewer.zoomValue === 0.5 ? "actual" : "custom"
    property real panX: 0
    property real panY: 0

    //: #2564: „a fotón értelmezett vezérlők használhatók-e" — EGY helyen
    //: kimondva. Eddig a lebegő `zoomBar` `visible`-je hordozta ezt a
    //: szabályt; a nagyítás-hármas azóta az ALSÓ ESZKÖZSÁVBAN ül
    //: (`TrayBar.qml`), az arc-gombok pedig itt maradtak — a feltételt
    //: ezért a néző GYÖKERÉRŐL kell kiadni, hogy ne íródjon meg kétszer
    //: (#1486 osztálya). A két ág változatlan: videón nincs mit nagyítani
    //: és nincs arc-keret, vágás közben pedig a kép 1:1-re áll vissza.
    readonly property bool photoOverlaysUsable:
        !viewer.isCurrentVideo && !editorPanel.cropActive

    //: #2492: a csúszka BEAKAD a valódi méretnél. `FUN_005d1300`: a
    //: léptetés eredményét a 0,5-höz méri, és az azt átlépő lépés
    //: pontosan ott áll meg.
    readonly property real zoomDetent: 0.5

    // A négy sarok átvitele a fókuszkép helyi koordinátáira a forgatást,
    // a nagyítást, a pásztázást és a kétképes nézet kivágását is leképezi.
    // A geometriai mezők olvasása a kötést minden QML-átrendezéskor frissíti.
    readonly property rect zoomNavigatorViewRect: {
        var image = photoArea.fokuszKep
        var frame = photoArea.fokuszKeret
        if (!image || !frame || image.paintedWidth <= 0
                || image.paintedHeight <= 0 || viewer.zoomFactor <= 0
                || !isFinite(viewer.panX) || !isFinite(viewer.panY))
            return Qt.rect(0, 0, 1, 1)
        var geometryStamp = image.x + image.y + image.width + image.height
                           + image.scale + image.rotation
                           + frame.x + frame.y + frame.width + frame.height
        if (!isFinite(geometryStamp)) return Qt.rect(0, 0, 1, 1)

        var p0 = image.mapFromItem(frame, 0, 0)
        var p1 = image.mapFromItem(frame, frame.width, 0)
        var p2 = image.mapFromItem(frame, 0, frame.height)
        var p3 = image.mapFromItem(frame, frame.width, frame.height)
        var left = Math.min(p0.x, p1.x, p2.x, p3.x)
        var right = Math.max(p0.x, p1.x, p2.x, p3.x)
        var top = Math.min(p0.y, p1.y, p2.y, p3.y)
        var bottom = Math.max(p0.y, p1.y, p2.y, p3.y)
        var contentX = (image.width - image.paintedWidth) / 2
        var contentY = (image.height - image.paintedHeight) / 2
        var x0 = Math.max(0, Math.min(1,
            (left - contentX) / image.paintedWidth))
        var x1 = Math.max(0, Math.min(1,
            (right - contentX) / image.paintedWidth))
        var y0 = Math.max(0, Math.min(1,
            (top - contentY) / image.paintedHeight))
        var y1 = Math.max(0, Math.min(1,
            (bottom - contentY) / image.paintedHeight))
        return Qt.rect(x0, y0, Math.max(0, x1 - x0), Math.max(0, y1 - y0))
    }

    // Ezek a teljes képre ható eszközök megnyitáskor kitöltő nézetet kérnek.
    // Bezáráskor a kitöltő nézet marad: az eredeti nagyítást nem mentjük el.
    readonly property var forceFitFilters: [
        "tilt", "radblur", "radsat", "linblur", "dir_tint",
        "radtint", "dir_sat", "dir_brite", "dir_sharp"
    ]

    function forceFitForFilter(filterName) {
        if (viewer.forceFitFilters.indexOf(filterName) >= 0)
            viewer.zoomFit()
    }

    //: #2492: a kép VALÓDI képpont-mérete a modellből — a `revision`
    //: referencia miatt képváltáskor és mentés után is újraértékelődik.
    readonly property int valodiSzelesseg: viewer.photosModel
        ? (viewer.photosModel.revision,
           viewer.photosModel.pixelWidthAt(viewer.aktivSor)) : 0

    function actualZoomFactor() {
        // Ez a MÉRT képlet `r`-je: a VALÓDI és az ILLESZTETT méret
        // aránya (`docs/specs/ui-audit-editor.md`, „A szerkesztő
        // NAGYÍTÁS-HÁRMASA"). Az eredeti `1to1` buboréksúgója is ezt
        // mondja: „Display Photo at actual size".
        //
        // ⚠️ #2492: KORÁBBAN `photo.sourceSize.width / photo.paintedWidth`
        // állt itt — HIBÁSAN. A Qt olvasáskor a BEÁLLÍTOTT `sourceSize`-t
        // adja vissza, ez az elem pedig 2560-as plafont kap
        // (`sourceSize.width: 2560` lent). Így a képlet a valódi mérettől
        // FÜGGETLENÜL 2560-cal számolt: egy 896 képpont széles képnél
        // ~3,7-es arányt az 1,28 helyett — mérve a tulajdonos
        // képernyőmentésén 3–4-szeres túlnagyítás.
        //
        // Invariáns (#3760): a `paintedWidth` a fájl SZÉLESSÉGÉVEL
        // arányos, a `.picasa.ini` forgatásától függetlenül — a
        // `PreserveAspectFit` a forgatatlan raszter arányával illeszt, a
        // `rotation:` csak utána forgatja a kész dobozt. Ezért az arány
        // forgatott képnél is `valodiSzelesseg / paintedWidth`.
        //: #3741: a fókuszban lévő fél képe — kettős nézetben bal
        //: fókusznál a `photoElotte`.
        var kep = photoArea.fokuszKep
        if (kep.paintedWidth <= 0)
            return 1
        if (viewer.valodiSzelesseg > 0)
            return viewer.valodiSzelesseg / kep.paintedWidth
        // Tartalék, ha az index nem tud méretet adni (frissen felvett kép,
        // vagy olvashatatlan fejléc): a BETÖLTÖTT raszter mérete. Ez a
        // `sourceSize`-plafon miatt legfeljebb kisebb lehet a valódinál —
        // tehát a nagyítás legrosszabb esetben kevesebb, sosem több.
        // NEM a `sourceSize`: az a beállított plafont adná vissza.
        return kep.implicitWidth > 0
            ? kep.implicitWidth / kep.paintedWidth : 1
    }

    //: A MÉRT leképezés (`0x00a601cf`–`0x00a60221`), két folytonos ágon:
    //:
    //:   0 ≤ v < 0,5 :  1 + (2^(2v) − 1) · (r − 1)
    //:   0,5 ≤ v ≤ 1 :  r · 2^(4·(v − 0,5))
    //:
    //: Rögzített pontok: v=0 → 1 (illesztés), v=0,5 → r (100 %),
    //: v=1 → 4r (400 %). A felső fél negyedenként pontosan duplázódik.
    function skalaErtekbol(v) {
        var r = viewer.actualZoomFactor()
        var t = Math.max(0, Math.min(1, v))
        return t < 0.5
            ? 1 + (Math.pow(2, 2 * t) - 1) * (r - 1)
            : r * Math.pow(2, 4 * (t - 0.5))
    }

    function setZoomValue(v) {
        // ⚠️ MÉRT vágás [0, 1]-re (`0x005d13a9` fldz / `0x005d13c6` fld1):
        // az illesztettnél kisebbre és a 400 %-nál nagyobbra nem lehet
        // állítani.
        var uj = Math.max(0, Math.min(1, v))
        if (uj === 0 || viewer.zoomValue === 0)
            zoomNavigatorDismissed = false
        viewer.zoomValue = uj
        if (viewer.zoomValue === 0) { panX = 0; panY = 0 }
        clampPan()
    }
    function zoomFit() {
        zoomNavigatorDismissed = false
        setZoomValue(0)
        panX = 0
        panY = 0
    }
    function zoomActual() { setZoomValue(viewer.zoomDetent) }

    //: #2492: a léptető út a 0,5-ös beakadással. Ha az érték MÁR pontosan
    //: a detenten áll, a lépés elmozdítja (`0x005d1383` — ugyanabban a
    //: lépésben nem mozdul el, tehát a következő lépés viszi tovább).
    function lepjZoom(delta) {
        var regi = viewer.zoomValue
        var uj = Math.max(0, Math.min(1, regi + delta))
        if (regi !== viewer.zoomDetent
                && (regi - viewer.zoomDetent) * (uj - viewer.zoomDetent) < 0)
            uj = viewer.zoomDetent
        setZoomValue(uj)
    }

    //: az egérgörgő egy „kattanása" (120 egység) a csúszka 1/20-a — a
    //: lépésköz a MI választásunk, a beakadás és a vágás a mért.
    function wheelZoom(delta) { lepjZoom((delta / 120) * 0.05) }
    // a kép széle ne szakadjon el a látótértől pásztázáskor
    //: #3741: a fókuszban lévő fél képét és a SAJÁT felét nézi — egy képen
    //: ez a teljes `photoArea`, kettős nézetben a kép fele.
    function clampPan() {
        var kep = photoArea.fokuszKep
        var keret = photoArea.fokuszKeret
        var w = (kep.iniSteps % 2 ? kep.paintedHeight
                                  : kep.paintedWidth) * zoomFactor
        var h = (kep.iniSteps % 2 ? kep.paintedWidth
                                  : kep.paintedHeight) * zoomFactor
        var maxX = Math.max(0, (w - keret.width) / 2)
        var maxY = Math.max(0, (h - keret.height) / 2)
        panX = Math.max(-maxX, Math.min(maxX, panX))
        panY = Math.max(-maxY, Math.min(maxY, panY))
    }

    function panFromZoomNavigator(deltaX, deltaY) {
        var image = photoArea.fokuszKep
        if (!image || viewer.zoomFactor <= 1.01) return
        var origin = image.mapToItem(photoArea, 0, 0)
        var moved = image.mapToItem(
            photoArea,
            deltaX * image.paintedWidth,
            deltaY * image.paintedHeight)
        panX -= moved.x - origin.x
        panY -= moved.y - origin.y
        clampPan()
    }

    function show(index) { currentIndex = index; forceActiveFocus() }

    // A Kép menü egyes egylépéses javításai szerkesztőben a megfelelő
    // panelfület nyitják meg; a könyvtárnézetben a kijelölésre futnak.
    function selectMenuEffect(name) {
        if (name === "autolight" || name === "autocolor"
                || name === "enhance") {
            editorPanel.selectTab(0)
            return true
        }
        if (name === "unsharp" || name === "warm" || name === "grain2") {
            editorPanel.selectTab(2)
            return true
        }
        return false
    }

    // Vágás alkalmazása a kijelölésből. advance=true: Enter-flow —
    // következő kép, vágó-mód megtartva; false: Alkalmaz gomb — a panel
    // visszaáll az eszközrácsra (Picasa-viselkedés).
    function applyCrop(advance) {
        if (!cropOverlay.hasSelection) {
            if (!advance) editorPanel.cropActive = false
            return
        }
        var r = cropOverlay.cropRect
        editController.applyCrop(r.x, r.y, r.width, r.height)
        cropOverlay.resetSelection()
        if (advance) viewer.next()
        else editorPanel.cropActive = false
    }

    // -- szerkesztés (#19): EditController-életciklus --------------------
    // A nézőbe lépés = szerkesztési munkamenet az aktuális képre; kilépéskor
    // a munkamenet zárul. A panel kapcsoló-állapotait az EditController
    // igazságforrásából szinkronizáljuk (a kötést a panel belső átírása
    // megtörné, ezért imperatív sync a toolsChanged-re).
    //: #3187: a MÁSODIK fél munkamenete. AB módban a másik sor fotójára
    //: nyitunk (mentett lánccal), egy képes módban zárjuk. #3014: „aa"
    //: módban ugyanarra a fotóra, CSAK MEMÓRIÁBAN (ld. lent).
    //: #3187 3. lépés: a NEM kijelölt oldal sora. A fő vezérlő a KIJELÖLT
    //: oldalt szerkeszti (`aktivSor`), a második rekesz ezt a másikat kapja —
    //: így a szerkesztő-panel 104 kötése változatlan maradhat, a parancsok
    //: mégis a kijelölt oldalra hatnak.
    readonly property int masodikSor: viewer._masodikSort()

    //: ⚠️ #3187: a KÖTÖTT `aktivSor`/`masodikSor` NEM használható az
    //: imperatív kezelőkben. A #218 óta tudjuk: egy kötött property
    //: újraértékelése nem garantált, mire az UGYANARRA a jelzésre futó
    //: imperatív kezelő lefut — mérve ezen a jegyen is: fókuszváltás után a
    //: `beginEditCurrent()` még a RÉGI `aktivSor`-t látta, és a két oldal
    //: fordítva kapta a rekeszeket. Ezért a két sor-számítás FÜGGVÉNY: a
    //: kötések is ezt hívják (a QML a hívás alatt olvasott property-ket
    //: függőségként követi), a kezelők pedig friss értéket kapnak.
    function _kijeloltSort() {
        //: #3773: a BAL fél a `currentIndex`-et mutatja (ld. `aktivSor`)
        return (viewer.layoutMode !== "1up" && viewer.aktivOldal === "jobb")
            ? viewer._abMasikSort() : viewer.currentIndex
    }

    function _masodikSort() {
        //: #3014: „aa" módban is van második fél — ugyanaz a fotó
        if (viewer.layoutMode === "1up") return -1
        return viewer.aktivOldal === "jobb" ? viewer.currentIndex
                                            : viewer._abMasikSort()
    }

    function frissitsdAMasodikSzerkesztest() {
        if (!viewer.masodikEditCtl) return
        var sor = viewer._masodikSort()
        if (!(viewer.visible && viewer.layoutMode !== "1up"
              && sor >= 0 && photosModel)
                || photosModel.isVideoAt(sor)) {
            viewer._aaLezaras()
            viewer.masodikEditCtl.endEdit()
            return
        }
        var azonosito = photosModel.idAt(sor)
        if (viewer.layoutMode === "aa") {
            //: #3014: a futó „aa" munkamenet ugyanerre a fotóra érintetlen;
            //: MÁSIK fotóra lépve a lapozás kapuja dönt (#3644)
            if (viewer.aaMunkamenet && viewer.aaFotoId === azonosito) return
            if (!viewer._aaLapozasKapu()) return
            viewer.masodikEditCtl.beginEditInMemory(azonosito,
                                                   photosModel.filePathAt(sor))
            //: 4/b.1: a két fél a kép JELENLEGI láncával indul, és ez a
            //: „módosult" próba alapja is
            viewer.aaKiindulas = viewer.masodikEditCtl.chainValue
            viewer.aaFotoId = azonosito
            viewer.aaMunkamenet = true
            return
        }
        viewer._aaLezaras()
        viewer.masodikEditCtl.beginEdit(azonosito, photosModel.filePathAt(sor))
    }

    // A lemezművelet a fájlt és az indexet frissíti. Ha a nyitott nézet egy
    // sikeresen érintett képet mutat, a szerkesztő-előnézetnek is újra kell
    // olvasnia a mostani fájlt és filters= láncot.
    function frissitsdALemezműveletUtániElőnézetet(utvonalak) {
        if (!viewer.visible || !viewer.photosModel || !utvonalak
                || utvonalak.length === 0)
            return

        var sor = viewer._kijeloltSort()
        if (sor >= 0) {
            var utvonal = viewer.photosModel.filePathAt(sor)
            if (utvonalak.indexOf(utvonal) >= 0 && viewer.editCtl)
                viewer.editCtl.beginEdit(
                    viewer.photosModel.idAt(sor), utvonal)
        }

        // A két önálló AB-előnézet is a mentett állapotot mutassa. Az AA
        // második fele memóriás piszkozat, ezért azt a lemezművelet nem írja.
        if (viewer.layoutMode === "ab" && viewer.masodikEditCtl) {
            var masodik = viewer._masodikSort()
            if (masodik >= 0) {
                var masodikUtvonal = viewer.photosModel.filePathAt(masodik)
                if (utvonalak.indexOf(masodikUtvonal) >= 0)
                    viewer.masodikEditCtl.beginEdit(
                        viewer.photosModel.idAt(masodik), masodikUtvonal)
            }
        }
    }

    // -- #3014: az „aa" mód két szerkesztési állapota ---------------------
    //
    // MÉRVE (`docs/specs/ui-audit-editor.md` 4/b, 4/b.1): az eredetiben az
    // „aa" mód két fele két önálló szerkesztési állapot ugyanarról a fotóról.
    // Belépéskor mindkettő a kép jelenlegi láncával indul; „módosult" = a fél
    // lánca ≠ a belépéskori. Kilépéskor döntési tábla dönt, és ha mindkét fél
    // KÜLÖNBÖZŐEN módosult, a `Confirm2up*` párbeszéd kérdez.
    //
    // A MI modellünk: a fő vezérlő a KIJELÖLT felet szerkeszti és írja az
    // ini-t (a szerkesztő-panel kötései így változatlanok), a második rekesz
    // a másikat CSAK MEMÓRIÁBAN. A fókuszváltás a két láncot CSERÉLI; a
    // kilépés a memóriás felet írja ki, ha azt kell megtartani.

    //: van-e futó „aa" munkamenet (a második fél memóriás lánccal)
    property bool aaMunkamenet: false
    //: a belépéskori lánc — MINDKÉT fél „módosult" próbájának alapja
    property string aaKiindulas: ""
    //: melyik fotóra fut a munkamenet (lapozáskor ebből tudjuk, hogy zárni kell)
    property string aaFotoId: ""
    //: a párbeszéd alatt várakozó kilépés (módváltás, lapozás, bezárás,
    //: programzárás) — a VÁLASZ után fut, Mégsére elmarad
    property var aaFolytatas: null
    //: a párbeszéd épp kérdez — amíg válaszra vár, újabb kilépés nem írhatja
    //: felül a várakozót (a lapozás a régi kötésekkel még egyszer ideérhet)
    property bool aaKerdesFut: false

    //: #3651: a „Szerkesztés jóváhagyása" (`endEditModality`) párbeszéd alatt
    //: várakozó módváltás — a VÁLASZ (alkalmaz vagy elvet) után fut.
    property var endEditFolytatas: null

    //: #3651: a Vágás megnyitásakor betöltött kijelölés (a kép mentett
    //: vágása, vagy `null`) — a „módosult" próba ehhez méri a mostanit, így
    //: egy már vágott kép érintetlen Vágás-eszköze nem számít módosultnak.
    property var cropNyitaskoriKijeloles: null

    function _cropKijeloles() {
        if (!cropOverlay.hasSelection) return null
        var r = cropOverlay.cropRect
        return { "x": r.x, "y": r.y, "width": r.width, "height": r.height }
    }

    function _cropNyitaskoriMegjegyez() {
        viewer.cropNyitaskoriKijeloles = viewer._cropKijeloles()
    }

    function _cropModosult() {
        var most = viewer._cropKijeloles()
        var volt = viewer.cropNyitaskoriKijeloles
        if (most === null || volt === null) return most !== volt
        var eps = 1e-6
        return Math.abs(most.x - volt.x) > eps
            || Math.abs(most.y - volt.y) > eps
            || Math.abs(most.width - volt.width) > eps
            || Math.abs(most.height - volt.height) > eps
    }

    //: a fél (`"elso"` = bal/fent, `"masodik"` = jobb/lent) jelenlegi lánca
    function _aaFelLanca(fel) {
        var aFoVezerloE = (fel === "elso") === (viewer.aktivOldal === "bal")
        return aFoVezerloE ? editController.chainValue
                           : viewer.masodikEditCtl.chainValue
    }

    function _aaAktivFel() {
        return viewer.aktivOldal === "bal" ? "elso" : "masodik"
    }

    //: A kilépés döntési táblája (4/b.1). Eredmény: a megtartandó fél
    //: (`"elso"`/`"masodik"`), `""` ha nincs teendő, `"kerdes"` ha a
    //: párbeszéd dönt.
    function _aaDontes(neKerdezzen) {
        var elso = viewer._aaFelLanca("elso")
        var masodik = viewer._aaFelLanca("masodik")
        var elsoMod = elso !== viewer.aaKiindulas
        var masodikMod = masodik !== viewer.aaKiindulas
        if (elsoMod && !masodikMod) return "elso"
        if (!elsoMod && masodikMod) return "masodik"
        if (!elsoMod && !masodikMod) return ""
        if (elso === masodik || neKerdezzen) return viewer._aaAktivFel()
        return "kerdes"
    }

    //: A választott fél láncának véglegesítése. A kijelölt fél lánca már az
    //: ini-ben áll (a fő vezérlő írja); a memóriás felet ki kell írni.
    function _aaMegtart(fel) {
        if (fel === "elso" || fel === "masodik") {
            if (fel !== viewer._aaAktivFel())
                viewer.masodikEditCtl.persistChain()
        }
        viewer.aaMunkamenet = false
        viewer.aaFotoId = ""
    }

    //: VÉGSŐ tartalék, párbeszéd NÉLKÜL — csak olyan kilépésnek, amely nem
    //: ment át az `aaKilepesKapu()`-n (a néző elrejtése egy még nem kapuzott
    //: úton). A „Ne kérdezzen újra" ágát követi: különböző módosításnál az
    //: AKTÍV fél marad. Minden ismert kilépési út a kapun megy át (#3644).
    function _aaLezaras() {
        if (!viewer.aaMunkamenet) return
        viewer._aaMegtart(viewer._aaDontes(true))
    }

    function _aaNeKerdezzen() {
        return typeof confirmSettings !== "undefined" && confirmSettings
            ? confirmSettings.isSuppressed(aaUtkozes.beallitasKulcs) : false
    }

    //: #3014/#3644: az „aa" mód KILÉPÉSI KAPUJA — minden út ezen megy át,
    //: amely az „aa" munkamenetet elhagyja: módváltás, lapozás, a néző
    //: elhagyása és a program bezárása. Mérve (`docs/specs/ui-audit-editor.md`
    //: 4/c.1): az eredetiben a `0x0056aad0` hívói — a módváltás (`0x0056a260`,
    //: `0x0056a680`), a lapozás (`0x00578c30`/`0x00578dc0`), a filmszalag
    //: (`0x005deb29`, `0x005d34ed`) és a programzárás (`SC_CLOSE` →
    //: `0x0057c4e0` → `0x005e45c0`) — Mégsére (`0xf4242`) mind MEGÁLLNAK.
    //:
    //: `true`: nincs (vagy már el is dőlt) a kérdés, a hívó MOST folytathat.
    //: `false`: a párbeszéd nyitva; a `folytatas` a VÁLASZ után fut, Mégsére
    //: elmarad — a hívó ilyenkor NE folytassa.
    function aaKilepesKapu(folytatas) {
        if (!viewer.aaMunkamenet || !viewer.masodikEditCtl) return true
        if (viewer.aaKerdesFut) return false
        var dontes = viewer._aaDontes(viewer._aaNeKerdezzen())
        if (dontes === "kerdes") {
            viewer.aaFolytatas = folytatas
            viewer.aaKerdesFut = true
            aaUtkozes.kerdez(viewer.fuggolegesElrendezes, viewer._aaAktivFel())
            return false
        }
        viewer._aaMegtart(dontes)
        return true
    }

    //: #3651: van-e nyitott ÉS módosult modális eszköz (4/b.1 2. lépés,
    //: `0x005f8d80` — „ha egy modális eszköz nyitva van"). A „módosult" a
    //: panel saját Alkalmaz-gombjának engedélyezettségi feltételét követi
    //: (retusálás/szöveg — a 3/c szakasz szerint ugyanez a kapu nézi az
    //: eszköz állapotát); a vágásnál az, hogy a kijelölés eltér-e a
    //: megnyitáskoritól. A Kiegyenesítés kimarad, mert a 3/c a kapu kérdező
    //: ágát (2-es módkód) csak erre a négy eszközre mérte, az övé nincs lekövetve.
    function _nyitottEszkozModosult() {
        if (editorPanel.cropActive) return viewer._cropModosult()
        if (editorPanel.retouchActive)
            return editorPanel.retouchRegionCount > 0
                || editorPanel.retouchPatchPending
        if (editorPanel.textActive) return editorPanel.textPlacementPending
        if (editorPanel.redeyeActive) return editorPanel.redeyeRegionCount > 0
        return false
    }

    //: #3651: a nyitott eszköz lezárása a saját Alkalmaz/Mégse útján —
    //: ugyanazok a hívások, amiket a panel gombjai indítanak (3/c 3. pont).
    function _nyitottEszkozLezar(alkalmaz) {
        if (editorPanel.cropActive) {
            if (alkalmaz) viewer.applyCrop(false)
            else {
                cropOverlay.resetSelection()
                editorPanel.cropActive = false
            }
        } else if (editorPanel.retouchActive) {
            if (alkalmaz) editController.applyRetouch()
            editorPanel.retouchActive = false
        } else if (editorPanel.textActive) {
            if (alkalmaz) editController.applyText()
            editorPanel.textActive = false
        } else if (editorPanel.redeyeActive) {
            if (alkalmaz) editController.applyRedeye()
            editorPanel.redeyeActive = false
        }
    }

    //: #3651: a „Szerkesztés jóváhagyása" kapu (4/b.1 2. lépés) — az „aa"/
    //: „ab" módba lépés előtt fut, MIUTÁN a 2-up kilépési létra (`aaKilepesKapu`)
    //: már eldőlt. #3693: a fókuszváltás (`fokuszValt`) is ezt hívja,
    //: `megseEngedve = true`-val — a két hívó a 3/c szerint a kapu MÁSIK
    //: argumentumával megy (mód-belépés: nincs Mégse; fókuszváltás: van).
    //: `true`: nincs (vagy már el is dőlt) a kérdés, a hívó MOST folytathat.
    //: `false`: a párbeszéd nyitva; a `folytatas` a VÁLASZ után fut, Mégsére
    //: elmarad. Ha nincs mit kérdezni, a nyitott eszköz akkor is lezárul,
    //: elvetéssel (3/c 2. pont, `0x005f904d` → `0x005f907e`).
    function _eszkozZarasKapu(folytatas, megseEngedve) {
        if (!viewer._nyitottEszkozModosult()) {
            viewer._nyitottEszkozLezar(false)
            return true
        }
        if (typeof confirmSettings !== "undefined" && confirmSettings
                && confirmSettings.isSuppressed(endEditModality.beallitasKulcs)) {
            viewer._nyitottEszkozLezar(true)
            return true
        }
        viewer.endEditFolytatas = folytatas
        endEditModality.kerdez(megseEngedve === true)
        return false
    }

    //: #3014: a kettős nézet üzemmódjának váltása — a szegmensek ezt hívják.
    //: Az „aa" módból kilépve előbb a kapu fut; ha a párbeszéd kell, a váltás
    //: a válaszig vár, és Mégsére elmarad. #3651: „aa"/„ab" módba LÉPÉSKOR
    //: (a 2-up kilépési létra után) a nyitott modális eszköz kérdése jön.
    function modotValt(uj) {
        if (uj === viewer.layoutMode) return
        if (!viewer.aaKilepesKapu(function () { viewer._modotValtEszkozUtan(uj) }))
            return
        viewer._modotValtEszkozUtan(uj)
    }

    function _modotValtEszkozUtan(uj) {
        if ((uj === "aa" || uj === "ab")
                && !viewer._eszkozZarasKapu(function () { viewer.layoutMode = uj }))
            return
        viewer.layoutMode = uj
    }

    //: #3693: a FÓKUSZVÁLTÁS kapuja — a kép kattintása és a „Fókusz
    //: váltása" gomb egyaránt ide fut. Ugyanaz a kapu, mint a mód-váltásnál
    //: (#3651, `_eszkozZarasKapu`), de a 3/c mérés szerint a fókuszváltó
    //: (`0x0056a160`) a kaput `megseEngedve = true`-val hívja: a nyitott ÉS
    //: módosult modális eszköznél a „Szerkesztés jóváhagyása" kérdés VAN
    //: Mégse gombbal — Mégsére a fókusz NEM vált, az eszköz nyitva marad.
    function fokuszValt(uj) {
        if (uj === viewer.aktivOldal) return
        if (!viewer._eszkozZarasKapu(
                function () { viewer.aktivOldal = uj }, true))
            return
        viewer.aktivOldal = uj
    }

    //: #3644: a LAPOZÁS kapuja — a `currentIndex` már az új soron áll, amikor
    //: a váltás ide ér (billentyű, gomb, filmszalag egyaránt). Az eredeti
    //: lapozása ELŐBB kérdez, és Mégsére nem lapoz (`0x00578c30`/
    //: `0x00578dc0` → `0x0056aad0`, `cmp eax, 0xf4242` @ `0x00578c6d`) —
    //: nálunk ezért a párbeszéd idejére a néző visszaáll a munkamenet
    //: fotójára, és a lapozás a VÁLASZ után ismétlődik. `true`: folytatható.
    function _aaLapozasKapu() {
        if (viewer.aaKerdesFut) return false
        var cel = viewer.currentIndex
        if (viewer.aaKilepesKapu(function () { viewer.currentIndex = cel }))
            return true
        var vissza = photosModel ? photosModel.rowOfId(viewer.aaFotoId) : -1
        if (vissza >= 0 && vissza !== viewer.currentIndex)
            viewer.currentIndex = vissza
        return false
    }

    //: #3644: a néző elhagyása („Vissza a könyvtárba" gomb, Esc, a panel
    //: kérése) — előbb az „aa" kapu. Az eredeti itt nem kérdez, de a két fél
    //: állapota ott a nézőn túl is megmarad (`0x00566270` egyiket sem oldja);
    //: nálunk a bezárás mindkét munkamenetet lezárja, ezért a kérdés a
    //: munkát védi, és Mégsére a néző nyitva marad (4/c.1).
    function kerBezaras() {
        if (viewer.aaKilepesKapu(function () { viewer.closed() }))
            viewer.closed()
    }

    //: #3014: „aa" módban a fókuszváltás a két fél LÁNCÁT cseréli: a fő
    //: vezérlő (és vele a szerkesztő-panel) mindig a kijelölt felet tartja.
    //: #3644: a nyitott eszköz a régi fél alkalmazatlan munkáját tartja
    //: (retusálás-folt, vörösszem-régió, vágókeret) — előbb zárul, mint a
    //: néző bezárásakor; a csere után a panel az ÚJ fél értékeit mutatja.
    //: #3649: a festett maszk NEM ürül — a `swapAaFocus` a párral cseréli,
    //: hogy a félkész festés a saját felén megmaradjon. A festés NEM
    //: része a láncnak (`chainValue`), ezért a „van-e mit cserélni"
    //: döntés a `swapAaFocus`-é — a QML itt nem tér ki azonos lánc esetén
    //: sem: a pár nélküli vagy tényleg semmiben nem különböző eset a
    //: vezérlőn belül no-op (code review lelet #3).
    function _aaFeleketCserel() {
        editorPanel.cropActive = false
        editorPanel.tiltActive = false
        editorPanel.retouchActive = false
        editorPanel.textActive = false
        editorPanel.redeyeActive = false
        editController.swapAaFocus()
        viewer.syncTiltSlider()
    }

    AaUtkozesDialog {
        id: aaUtkozes
        onValasztva: function(fel) {
            viewer.aaKerdesFut = false
            viewer._aaMegtart(fel)
            var folytatas = viewer.aaFolytatas
            viewer.aaFolytatas = null
            if (folytatas) folytatas()
        }
        onMegse: {
            viewer.aaKerdesFut = false
            viewer.aaFolytatas = null
        }
    }

    //: #3651: 4/b.1 2. lépés — a nyitott modális eszköz lezárás-kérdése,
    //: mielőtt a kettős nézet „aa"/„ab" módja megnyílna. #3693: ugyanez a
    //: fókuszváltás előtt is; ott a Mégse gomb is elérhető (3/c 2. pont).
    EndEditModalityDialog {
        id: endEditModality
        onEldontve: function(alkalmaz) {
            viewer._nyitottEszkozLezar(alkalmaz)
            var folytatas = viewer.endEditFolytatas
            viewer.endEditFolytatas = null
            if (folytatas) folytatas()
        }
        //: #3693: Mégse — az eszköz nyitva marad, a folytatás elmarad
        onMegse: {
            viewer.endEditFolytatas = null
        }
    }

    //: #3773: jobb fókusznál a JOBB fél (`abMasikSor`) a kijelölt — ha az
    //: cserél (lapozás, filmszalag), a fő vezérlő is vele megy.
    onAbMasikSorChanged: {
        if (viewer.layoutMode === "ab" && viewer.aktivOldal === "jobb")
            viewer.beginEditCurrent()
        viewer.frissitsdAMasodikSzerkesztest()
    }
    onLayoutModeChanged: {
        viewer.beginEditCurrent()            // #3187: a célpont módot vált
        viewer.frissitsdAMasodikSzerkesztest()
    }
    //: #3187: a fókuszváltás ÁTVISZI a szerkesztést a másik oldalra — a fő
    //: vezérlő a kijelöltet kapja, a második rekesz a régi kijelöltet.
    //: #3014: „aa" módban ugyanaz a fotó áll mindkét félen — ott a LÁNCOK
    //: cserélnek, újratöltés helyett (az ini-ben csak a kijelölt fél áll).
    onAktivOldalChanged: {
        //: #3741: a nagyítás a fókuszban lévő félre hat — a másik kép
        //: mérete más, tehát a pásztázás határa is
        Qt.callLater(viewer.clampPan)
        if (viewer.layoutMode === "aa" && viewer.aaMunkamenet
                && viewer.masodikEditCtl) {
            viewer._aaFeleketCserel()
            return
        }
        viewer.beginEditCurrent()
        viewer.frissitsdAMasodikSzerkesztest()
    }

    function beginEditCurrent() {
        //: #3187: a szerkesztett sor a KIJELÖLT oldal sora. Egy képes és
        //: „aa" módban ez maga a jelenlegi kép (az `aktivSor` ott
        //: `currentIndex`-et ad), tehát azokon a módokon semmi nem változik.
        var sor = viewer._kijeloltSort()
        if (!(visible && sor >= 0 && photosModel)) return
        //: #3014: MÁSIK fotóra lépve a futó „aa" munkamenet zárul — még
        //: azelőtt, hogy a fő vezérlő elhagyná a régi fotót. #3644: a lapozás
        //: kapuján át; ha a párbeszéd kérdez, a néző visszaáll a munkamenet
        //: fotójára, és a fő vezérlő ott marad.
        if (viewer.aaMunkamenet) {
            if (viewer.aaFotoId === photosModel.idAt(sor)) {
                //: a fő vezérlő már ezen a fotón áll a kijelölt fél láncával
                //: — újratöltés a visszavonás-vermét dobná el
                if (editController.previewSource !== "") return
            } else if (!viewer._aaLapozasKapu()) {
                return
            }
        }
        // #218: a viewer.isCurrentVideo egy kötött property — a currentIndex
        // váltásakor NEM garantált, hogy már újraértékelődött, mire ez a
        // (szintén a currentIndexChanged-re futó) imperatív függvény lefut,
        // ezért a modellt itt KÖZVETLENÜL kérdezzük le (mindig friss),
        // nem a cache-elt property-t
        if (photosModel.isVideoAt(sor)) {
            // videón nincs képszerkesztés (#14) — az előző kép nyitott
            // munkamenete záruljon, ne lógjon át az előnézete
            editController.endEdit()
            return
        }
        editController.beginEdit(photosModel.idAt(sor),
                                 photosModel.filePathAt(sor))
    }
    // #1598: a megjelenítési mód (`Nézet ▸ Megjelenítési mód`) KIZÁRÓLAG az
    // `editpreview` szolgáltatón át jut a képernyőre. A lenti `photo.source`
    // kötés viszont a NYERS fájl URL-jére esik vissza, ha nincs élő
    // szerkesztési munkamenet (`editCtl.previewSource` üres) — a nyers fájlon
    // pedig a mód nem látszik. Mérve (#1598, a kirajzolt képpontokon): ilyen
    // állapotban a módváltás NÉMÁN elveszik, vagyis a felület olyat kínál,
    // ami nem hat. A tulajdonos jelentése („egyáltalán nem működik egyik
    // sem") pontosan ilyen alakú.
    //
    // A `beginEditCurrent()` a néző megnyitásakor és lapozáskor amúgy is
    // lefut, tehát a visszaesés a rendes úton nem áll elő; a munkamenetet
    // viszont kívülről is le lehet zárni (`endEdit`), és a felhasználó
    // ilyenkor is a menüből vált módot. Ezért a váltás pillanatában
    // ÚJRANYITJUK a munkamenetet, ahelyett hogy a nyers fájl elnyelné.
    //
    // Nem tud körbe járni: a `beginEdit` után a `previewSource` nem üres, a
    // `displayModeChanged` pedig csak VALÓDI módváltásnál szól (ld.
    // `display_mode_controller.py` modul-docstring). Videón nem fut le — ott
    // a fotó-Image rejtett, és a `beginEditCurrent()` is `endEdit`-et hív.
    Connections {
        target: typeof controller !== "undefined" ? controller : null
        function onDisplayModeChanged() {
            if (viewer.visible && !viewer.isCurrentVideo
                    && viewer.editCtl && viewer.editCtl.previewSource === "")
                viewer.beginEditCurrent()
        }
    }

    // Döntés-csúszka szinkronja a mentett tilt-értékkel (#131): a value
    // beállítását elnyomjuk, hogy az onValueChanged NE váltson ki
    // previewTilt-et — a szinkron csak a csúszkát mozgatja, az előnézet
    // már a beginEditCurrent()/_register_preview() óta helyes.
    //: #3234: a szinkron ELNYOMÓJA. Korábban a csúszka saját
    //: `suppressPreview` tulajdonsága volt; a csúszka a sávba költözött,
    //: a szerepe viszont változatlan: a programozott értékadás NE
    //: váltson ki előnézetet.
    property bool tiltSzinkronFut: false
    //: #4058: az Alkalmaz már mentett és újrarenderelt; az ezt követő
    //: eszközbezárás ne kérje le még egyszer a mentett láncot.
    property bool tiltAlkalmazasFut: false
    //: #3234: a döntés értéke az eszköz NYITÁSAKOR — ezt állítja vissza a
    //: sáv Mégse gombja (`tool_cancel`, `Property escapekey 1`).
    property real tiltErtekNyitaskor: 0

    function syncTiltSlider() {
        viewer.tiltSzinkronFut = true
        editorToolBar.csuszkaErtek = editController.tiltParam
        viewer.tiltSzinkronFut = false
        // #448: a Kiegyenesítés-figyelmeztetés a vágó-panelen — a
        // tiltParam a mentett döntés-paraméter, 0.0 = nincs aktív tilt
        editorPanel.straightenActive = editController.tiltParam !== 0
    }
    function syncPanelFromController() {
        // #445: a panel `redeyeActive`-ja a Vágás/Retusálás mintájára
        // ESZKÖZ-nyitást jelent (nem a `redeye` réteg meglétét) — ezért NEM
        // a vezérlő `hasSavedRedeye`-jének tükre; azt onnan felülírni
        // becsukná/kinyitná a panelt a mentett lánc alapján.
        // #2393: a vezérlő tagja korábban szintén `redeyeActive` volt — a
        // névazonosság félrevitte a #1485-öt, ezért kapott beszédes nevet.
        // #448: a tilt-szűrő a láncban változhatott (pl. a felhasználó
        // épp most alkalmazta a Kiegyenesítést) — a figyelmeztetés kövesse
        editorPanel.straightenActive = editController.tiltParam !== 0
        // egygombos javítások (#116): "nyomható-e" tükrözése — a gomb
        // tiltott, amíg ugyanez a szűrő a lánc utolsó eleme
        editorPanel.enhanceEnabled = editController.enhanceEnabled
        editorPanel.autolightEnabled = editController.autolightEnabled
        editorPanel.autocolorEnabled = editController.autocolorEnabled
        // Finomhangolás-csúszkák (#20): a panel binding már frissítette a
        // fillLight/highlights/shadows/colorTemp értékeket a kontrollerből —
        // ez a hívás azokat suppress mellett a csúszkákba is beírja
        editorPanel.syncFinetuneSliders()
        // #450: "Remove all existing text" gomb tiltási állapota
        editorPanel.hasTextOverlay = editController.hasTextOverlay
        editorPanel.textOverlayVisible = editController.textOverlayVisible
        if (editorPanel.textActive)
            editorPanel.textDraftContent = editController.textDraft
        // #450: szöveg-stílus — kitöltés+körvonal szín, körvonal-vastagság,
        // kitöltés ki/be, átlátszóság
        // #464: a Finomhangolás fül pipettája melletti színminta
        editorPanel.neutralColor = editController.neutralColor
        editorPanel.textFillColor = editController.textFillColor
        editorPanel.textOutlineColor = editController.textOutlineColor
        editorPanel.textOutlineThickness = editController.textOutlineThickness
        editorPanel.textFillEnabled = editController.textFillEnabled
        editorPanel.textOpacity = editController.textOpacity
        // #450 (2. lépcső): tipográfia — betűcsalád, méret, B/I/U, igazítás
        // #4966: a katalógus állandó, ezért egyszer kapja meg. A másolat
        // JS-tömböt ad: a nyers hozzárendelés Python-hoz kötött QVariant-ot
        // tárolna, és minden későbbi olvasás újrahívná a getter-t.
        if (editorPanel.fontFamilyCatalogue.length === 0)
            editorPanel.fontFamilyCatalogue = editController.textFontFamilies.slice()
        editorPanel.textFontFamily = editController.textFontFamily
        editorPanel.textFontSize = editController.textFontSize
        editorPanel.fontSizeChoices = editController.fontSizeChoices
        editorPanel.textBold = editController.textBold
        editorPanel.textItalic = editController.textItalic
        editorPanel.textUnderline = editController.textUnderline
        editorPanel.textAlign = editController.textAlign
    }
    onVisibleChanged: {
        if (visible) {
            zoomFit()   // #6: minden belépés illesztett nézetben indul
            beginEditCurrent()
            frissitsdAMasodikSzerkesztest()   // #3187
        } else {
            stopCtrlF9AutoAdvance()
            // a cropActive/retouchActive/textActive lenullázása ELŐBB (még
            // aktív szerkesztés alatt) fut, hogy az onXActiveChanged->
            // exitXTool() még érvényes munkameneten hívódjon; utána zárja
            // az endEdit()
            editorPanel.cropActive = false
            editorPanel.tiltActive = false
            editorPanel.retouchActive = false
            editorPanel.textActive = false
            editorPanel.redeyeActive = false
            //: #3014: a memóriás fél módosítása ne vesszen el a bezáráskor.
            //: #3644: a kilépési utak a kapun (`aaKilepesKapu`) mennek át,
            //: tehát ide már lezárt munkamenettel érnek — ez a tartalék.
            viewer._aaLezaras()
            editController.endEdit()
            //: #3187: a második rekesz munkamenete is záruljon — nyitva
            //: hagyva a szolgáltató gyorsítótárában maradna a képe.
            if (viewer.masodikEditCtl) viewer.masodikEditCtl.endEdit()
        }
    }
    onCurrentIndexChanged: {
        if (ctrlF9AutoAdvanceTimer.running && !ctrlF9AutoStep)
            stopCtrlF9AutoAdvance()
        if (visible) {
            // #3924: a Picasa lapozáskor lezárja a Kiegyenesítést; a rács
            // csak az eszköz nyitott állapotában látszik.
            editorPanel.tiltActive = false
            zoomFit()   // #6: lapozáskor vissza illesztett nézetbe
            beginEditCurrent()
            //: #3773: jobb fókusznál a BAL fél (`currentIndex`) a második
            //: rekeszé — rögzített másik képnél (`masodikIndex`) az
            //: `abMasikSor` nem változik, tehát itt kell utánanyúlni.
            if (viewer.layoutMode === "ab" && viewer.aktivOldal === "jobb"
                    && viewer.masodikIndex >= 0)
                frissitsdAMasodikSzerkesztest()
            // lapozáskor a csúszka az ÚJ kép mentett tilt-értékére áll —
            // suppressPreview miatt ez nem írja felül a preview-t (#131)
            syncTiltSlider()
            // ugyanígy a Finomhangolás-csúszkák is az új kép mentett
            // értékeire állnak (#20)
            editorPanel.syncFinetuneSliders()
            if (editorPanel.cropActive) {
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
                viewer._cropNyitaskoriMegjegyez()
            } else {
                cropOverlay.resetSelection()
            }
            // #148: a Retusálás/Szöveg mód lapozáson át is megtartható —
            // az új képhez újra kell nyitni (a puffer/piszkozat az ÚJ kép
            // mentett állapotával indul, a Vágás mintáját követve)
            if (editorPanel.retouchActive)
                editController.enterRetouchTool()
            if (editorPanel.redeyeActive)
                editController.enterRedeyeTool()
            if (editorPanel.textActive) {
                editController.enterTextTool()
                editorPanel.textDraftContent = editController.textDraft
            }
        }
    }
    Connections {
        target: editController
        function onToolsChanged() { viewer.syncPanelFromController() }
    }
    // Vágás eszköz nyitása/zárása (#71): nyitáskor a lánc crop64 nélküli
    // (teljes, vágatlan) előnézete + a meglévő kijelölés betöltése; záráskor
    // (Mégse) a rendes, crop64-et is tartalmazó előnézet visszaáll
    Connections {
        target: editorPanel
        function onTiltActiveChanged() {
            if (editorPanel.tiltActive)
                viewer.forceFitForFilter("tilt")
            else if (!viewer.tiltAlkalmazasFut
                     && editController.previewSource !== "")
                editController.discardTiltPreview()
        }
        function onParamPanelActiveChanged() {
            if (editorPanel.paramPanelActive)
                viewer.forceFitForFilter(editorPanel.paramEffectName)
        }
        function onCropActiveChanged() {
            if (editorPanel.cropActive) {
                viewer.zoomFit()   // #6: a vágó-overlay illesztett nézetet vár
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
                viewer._cropNyitaskoriMegjegyez()
            } else {
                editController.exitCropTool()
            }
        }
        // #148: a Retusálás/Szöveg mód nyitása/zárása — a Vágás mintáját
        // követve az enter/exit a puffer/piszkozat élő előnézetét kezeli,
        // Alkalmazásig nem ír inibe.
        function onRetouchActiveChanged() {
            if (editorPanel.retouchActive)
                editController.enterRetouchTool()
            else
                editController.exitRetouchTool()
        }
        // #445: a Vörösszem eszköz nyitása/zárása — nyitáskor az automatika
        // AZONNAL lefut az előnézeten (enterRedeyeTool), a kézi téglalapok
        // pedig az Alkalmazásig csak a pufferben élnek.
        function onRedeyeActiveChanged() {
            if (editorPanel.redeyeActive)
                editController.enterRedeyeTool()
            else
                editController.exitRedeyeTool()
        }
        function onTextActiveChanged() {
            if (editorPanel.textActive) {
                editController.enterTextTool()
                editorPanel.textDraftContent = editController.textDraft
            } else {
                editController.exitTextTool()
            }
        }
    }
    // A lapozás a #84 óta a modell mappán-belüli lépését használja: a
    // rács (feed) nézet mappaátlépő listáin (csillag-szűrő, keresés) sem
    // ugorhatunk át a szomszéd mappába — a folderNeighbor a saját mappa
    // határán a jelenlegi indexet adja vissza, tehát nem lép tovább. #4525:
    // kettős nézetben a „Kijelölve” oldalt léptetjük, a másik sort hagyjuk.
    function next() {
        if (!viewer.ctrlF9AutoStep)
            viewer.stopCtrlF9AutoAdvance()
        if (!photosModel) return
        var sor = viewer._kijeloltSort()
        if (sor < 0) return
        var cel = photosModel.folderNeighbor(sor, 1)
        if (viewer.layoutMode === "ab" && viewer.aktivOldal === "jobb")
            viewer.masodikIndex = cel
        else
            viewer.currentIndex = cel
    }
    function previous() {
        viewer.stopCtrlF9AutoAdvance()
        if (!photosModel) return
        var sor = viewer._kijeloltSort()
        if (sor < 0) return
        var cel = photosModel.folderNeighbor(sor, -1)
        if (viewer.layoutMode === "ab" && viewer.aktivOldal === "jobb")
            viewer.masodikIndex = cel
        else
            viewer.currentIndex = cel
    }
    // a ◀/▶ gombok (és Keys.onLeft/Right) enabled-je is a mappahatárt
    // tükrözi: nincs hova lépni, ha a folderNeighbor helyben marad
    function _vanSzomszed(sor, irany) {
        if (!photosModel || sor < 0) return false
        return photosModel.folderNeighbor(sor, irany) !== sor
    }
    function hasNext() {
        return viewer._vanSzomszed(viewer._kijeloltSort(), 1)
    }
    function hasPrevious() {
        return viewer._vanSzomszed(viewer._kijeloltSort(), -1)
    }
    // Egérgörgős lapozás (#77): a nagy nézőben a görgő a képek között
    // lép (Picasa-viselkedés). A touchpad kis deltáit egy teljes
    // görgő-fokozatig (120) gyűjtjük, hogy ne ugráljon több képet.
    property real wheelAccum: 0
    function wheelStep(delta) {
        wheelAccum += delta
        while (wheelAccum <= -120) { wheelAccum += 120; next() }
        while (wheelAccum >= 120) { wheelAccum -= 120; previous() }
    }
    function urlAt(index) {
        return photosModel ? photosModel.fileUrlAt(index) : ""
    }
    // elő-betöltéshez: videót NEM adunk az Image-nek (#14) — a képként
    // dekódolás hibát logolna, a videó elő-betöltése nem a mi dolgunk
    function preloadUrlAt(index) {
        if (!photosModel || photosModel.isVideoAt(index)) return ""
        return urlAt(index)
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
    function handleReturnPressed() {
        if (viewer.textEntryHasFocus)
            return
        // #4500: a kikapcsolt SingleClickExit az állóképes előnézetben
        // Enterrel lép vissza a könyvtárba. Az aktív eszközök saját Enter-
        // útját (pl. sorozat-vágás), a videót és a kettős nézetet meghagyjuk.
        if (!viewer.singleClickExitEnabled
                && !viewer.isCurrentVideo
                && viewer.layoutMode === "1up"
                && !editorPanel.modeToolActive
                && !editorPanel.tiltActive
                && !editorPanel.paramPanelActive
                && !viewer.facesEditMode) {
            viewer.kerBezaras()
            return
        }
        viewer.next()
    }
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
        Rectangle {
            id: viewerTopBar
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
                //: a `filmstrip.x`/`.width` a `filmstrip` SAJÁT (a sorhoz
                //: képest helyi) pozíciója/szélessége — ebből adódik, hova
                //: kell tolni a TELJES sort, hogy a szalag közepe essen a
                //: fotóterület közepére.
                x: Math.max(
                       viewerTopBarLeftGroup.x + viewerTopBarLeftGroup.width + 12,
                       Math.min(
                           fototeruletKozepe - filmstrip.x - filmstrip.width / 2,
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
                PhotoViewerFilmstrip {
                    id: filmstrip
                    hostViewer: viewer
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
                hostCopyCaptionConfirmLoader: copyCaptionConfirmLoader
                hostUndoDataLossDialogLoader: undoDataLossDialogLoader
                hostMovieResetConfirmLoader: movieResetConfirmLoader
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
                    hostViewerPanArea: viewerPanArea
                    hostEditorPanel: editorPanel
                }

                //: #3663: a „Kijelölve” jelvény — a KÉPEN KÍVÜL, a szürke
                //: margóban, a fókuszban lévő fél mellett, az osztó felőli
                //: oldalon (mérve: `docs/specs/ui-audit-editor.md` 3/b.3,
                //: élőben újramérve a `Colab EN 33`–`35` referenciákon).
                //: A #3013 a `photoArea` GYEREKEként, a `photo` ELÉ tette —
                //: ezért időnként a kép ALÁ került (a `photo` később
                //: rajzolódott rá), és a `photoArea` `clip: true`-ja levágta
                //: volna, ha a margóba lógna. Itt, a `photoArea` UTÁN,
                //: TESTVÉRKÉNT áll: garantáltan a kép fölött rajzolódik, és
                //: nem vágja le semmi.
                Rectangle {
                    objectName: "viewerFocusBadge"
                    visible: viewer.layoutMode !== "1up"
                    //: #3663: MÉRT méret (`Colab EN 33`, 1280×1024): 86×26,
                    //: enyhén lekerekített — NEM kapszula (a #3013 `height/2`
                    //: sugara azt adott).
                    width: viewer.jelvenySzel
                    height: viewer.jelvenyMag
                    radius: 4
                    color: Theme.viewerFocusBadgeBg

                    //: #3663: a helyet a KIRAJZOLT kép téglalapjából
                    //: számoljuk (`paintedWidth`/`paintedHeight`), NEM a
                    //: befoglaló `photoElotte`/`photo` dobozból — az utóbbi
                    //: a `photoArea` felét kapja, de a kép azon belül
                    //: KÖZÉPRE igazítva, letterboxolva jelenik meg
                    //: (`PreserveAspectFit`), tehát a doboz éle és a kép
                    //: éle jellemzően NEM esik egybe.
                    readonly property var fokuszKep:
                        viewer.aktivOldal === "bal" ? photoElotte : photo
                    readonly property var fokuszKeret:
                        viewer.aktivOldal === "bal" ? photoElotteKeret : photoKeret
                    //: ⚠️ a `fokuszKep.x`/`.y` a SAJÁT felének keretéhez
                    //: (`fokuszKeret`), az pedig a `photoArea`-hoz KÉPEST
                    //: helyi (a `photo`/`photoElotte` a `photoArea` GYEREKE),
                    //: a jelvény viszont a `photoArea` TESTVÉRE — tehát a
                    //: KÖZÖS szülőhöz képesti koordinátához a `photoArea`
                    //: saját eltolását is hozzá kell adni. Enélkül a jelvény
                    //: pontosan a `photoArea` margójával (itt 14 px) tér el
                    //: a várt helytől — ez okozta az első verzió 14 px-es
                    //: eltérését minden mért esetben.
                    //: #3741: a KÉPERNYŐN látszó méret — 90°/270°-os
                    //: forgatásnál (`iniSteps` páratlan) a kirajzolt
                    //: szélesség és magasság helyet cserél.
                    readonly property bool forgatott: fokuszKep.iniSteps % 2 !== 0
                    readonly property real kepSzel: forgatott
                        ? fokuszKep.paintedHeight : fokuszKep.paintedWidth
                    readonly property real kepMag: forgatott
                        ? fokuszKep.paintedWidth : fokuszKep.paintedHeight
                    readonly property real kepBal: photoArea.x + fokuszKeret.x
                        + fokuszKep.x + (fokuszKep.width - kepSzel) / 2
                    readonly property real kepJobb: kepBal + kepSzel
                    readonly property real kepFent: photoArea.y + fokuszKeret.y
                        + fokuszKep.y + (fokuszKep.height - kepMag) / 2
                    readonly property real kepLent: kepFent + kepMag

                    //: #3663: a `Colab EN 33`/`34` (vízszintes) és `35`
                    //: (függőleges) referenciákon mért rés — mindkét
                    //: elrendezésben ugyanaz a két állandó adja vissza a
                    //: mért 60/62/27/61/26 px-es réseket: a KÉPEK SÍKJÁVAL
                    //: PÁRHUZAMOS tengelyen (vízszintesben az osztó felé,
                    //: függőlegesben a bal margó felé) ~61 px, a MERŐLEGES
                    //: tengelyen (vízszintesben fölfelé a margóba,
                    //: függőlegesben az osztó felé) ~27 px.
                    readonly property int parhuzamosRes: viewer.jelvenyParhuzamosRes
                    readonly property int merolegesRes: viewer.jelvenyMerolegesRes

                    x: viewer.fuggolegesElrendezes
                        ? kepBal - width - parhuzamosRes
                        : (viewer.aktivOldal === "bal"
                           ? kepJobb - parhuzamosRes - width
                           : kepBal + parhuzamosRes)
                    //: #3756: a helyét a két fél illesztése tartja fenn
                    //: (`viewer.illesztesiDoboz`) — álló képnél felül, széles
                    //: képnél függőlegesen balra —, így a jelvény a kép arányától
                    //: függetlenül a mért résen áll, és nem takarja sem a felső
                    //: sávot, sem a bal panelt, sem a képet.
                    y: viewer.fuggolegesElrendezes
                        ? (viewer.aktivOldal === "bal"
                           ? kepLent - merolegesRes - height
                           : kepFent + merolegesRes)
                        : kepFent - height - merolegesRes

                    Text {
                        id: jelvenySzoveg
                        anchors.centerIn: parent
                        text: qsTr("Selected")
                        font.pixelSize: Theme.fontSize - 2
                        font.bold: true
                        color: "#ffffff"
                    }
                }

                // #6: nagyított képen húzással pásztázás; dupla katt = fit.
                // #4499: a bekapcsolt egykattintásos kilépés csak egyképes,
                // nem Kiegyenesítéses illesztett nézetben kapja meg a szabad
                // előnézeti területet; a nagyított pásztázás minden nézetben él.
                MouseArea {
                    id: viewerPanArea
                    objectName: "viewerPanArea"
                    // #4078: a `photoArea` belső rétegében a pásztázó a
                    // képek fölött, a Kiegyenesítés sávja (z=20) alatt áll.
                    // Így a képen húzás — kettős nézetben a képi TapHandler
                    // fölött is — továbbra is pásztáz, a sáv pedig megkapja
                    // a saját kattintásait és csúszkahúzását.
                    parent: photoArea
                    anchors.fill: parent
                    z: 10
                    enabled: (viewer.zoomFactor > 1.01
                              || (viewer.singleClickExitEnabled
                                  && viewer.layoutMode === "1up"
                                  && !editorPanel.tiltActive))
                             && !editorPanel.cropActive
                             && !viewer.isCurrentVideo
                    cursorShape: viewer.zoomFactor > 1.01
                                 ? Qt.OpenHandCursor : Qt.ArrowCursor
                    property real lastX: 0
                    property real lastY: 0
                    property real pendingSingleClickX: 0
                    property real pendingSingleClickY: 0
                    property bool dragged: false
                    property bool exitAfterDoubleClick: false
                    // Tesztből olvasható diagnosztika: a platformfüggő
                    // egéresemény-út vizsgálatához a próba a kezelő ágát és
                    // a lenyomás előtti időzítő-állapotot olvassa ki.
                    property int pressEventCount: 0
                    property bool timerRunningOnLastPress: false
                    property string lastPressBranch: "not-pressed"

                    // #4499: a beállított egykattintásos kilépés a Qt
                    // dupla-kattintási időablakának lejártakor zár. Így a
                    // dupla kattintás második eseménye még a nézőé marad.
                    Timer {
                        id: singleClickExitTimer
                        objectName: "singleClickExitTimer"
                        interval: Qt.styleHints.mouseDoubleClickInterval
                        onTriggered: {
                            if (viewer.singleClickExitEnabled
                                    && viewer.layoutMode === "1up"
                                    && !editorPanel.tiltActive)
                                viewer.kerBezaras()
                        }
                    }

                    // #4083: a nagyított nézet pásztázója fölé került, így
                    // az aktív képi MouseArea-k lenyomását is elkapta. A
                    // lenyomást csak akkor engedjük tovább, ha a ténylegesen
                    // látható/aktív képi átfedő területére esik; a többi
                    // képpont és a képen kívüli sáv továbbra is pásztázható.
                    function benneVan(item, x, y) {
                        if (!item || !item.visible || !item.enabled) return false
                        var pont = item.mapFromItem(viewerPanArea, x, y)
                        return pont.x >= 0 && pont.y >= 0
                               && pont.x < item.width && pont.y < item.height
                    }
                    function aktivAtfedoAlatt(x, y) {
                        return benneVan(paintMaskArea, x, y)
                            || benneVan(neutralPickArea, x, y)
                            || benneVan(effectColorPickArea, x, y)
                            || benneVan(retouchClickArea, x, y)
                            || benneVan(redeyeDragArea, x, y)
                            || benneVan(textClickArea, x, y)
                            || (facesOverlay.editMode
                                && benneVan(facesOverlay, x, y))
                    }
                    function lathatoKepAlatt(item, frame, x, y) {
                        if (!benneVan(item, x, y)) return false
                        var pont = frame.mapFromItem(viewerPanArea, x, y)
                        return pont.x >= 0 && pont.y >= 0
                               && pont.x < frame.width
                               && pont.y < frame.height
                    }
                    function fokuszKattintas(x, y) {
                        if (viewer.layoutMode === "1up") return
                        // Nagyításkor a kép Image-doboza átlóghat a saját
                        // felén, miközben a keret levágja a túlnyúló részt.
                        // A fókuszt csak a ténylegesen látható képrész váltsa.
                        if (lathatoKepAlatt(
                                    photoElotte, photoElotteKeret, x, y)) {
                            viewer.fokuszValt("bal")
                            return
                        }
                        if (lathatoKepAlatt(photo, photoKeret, x, y))
                            viewer.fokuszValt("jobb")
                    }
                    onPressed: function(event) {
                        pressEventCount += 1
                        timerRunningOnLastPress = singleClickExitTimer.running
                        dragged = false
                        if (aktivAtfedoAlatt(event.x, event.y)) {
                            lastPressBranch = "active-overlay"
                            event.accepted = false
                            return
                        }
                        // Windows-on a MouseButtonDblClick eljuthat az
                        // ablakig úgy is, hogy a MouseArea doubleClicked
                        // jelzése kimarad. Az első kattintás időzítője még
                        // fut a második lenyomáskor; ezt a másik eseményutat
                        // is dupla kattintásként zárjuk le.
                        if (singleClickExitTimer.running
                                && Math.abs(event.x - pendingSingleClickX)
                                   <= Qt.styleHints.mouseDoubleClickDistance
                                && Math.abs(event.y - pendingSingleClickY)
                                   <= Qt.styleHints.mouseDoubleClickDistance
                                && viewer.singleClickExitEnabled
                                && viewer.layoutMode === "1up"
                                && !editorPanel.tiltActive) {
                            lastPressBranch = "second-press-exit"
                            singleClickExitTimer.stop()
                            exitAfterDoubleClick = true
                        } else {
                            lastPressBranch = "accepted"
                        }
                        lastX = event.x; lastY = event.y
                    }
                    onPositionChanged: function(event) {
                        if (!pressed) return
                        if (Math.abs(event.x - lastX) + Math.abs(event.y - lastY) > 4)
                            dragged = true
                        if (viewer.zoomFactor > 1.01) {
                            viewer.panX += event.x - lastX
                            viewer.panY += event.y - lastY
                            viewer.clampPan()
                        }
                        lastX = event.x; lastY = event.y
                    }
                    onClicked: function(event) {
                        if (exitAfterDoubleClick) return
                        if (dragged) return
                        if (viewer.singleClickExitEnabled
                                && viewer.layoutMode === "1up"
                                && !editorPanel.tiltActive) {
                            pendingSingleClickX = event.x
                            pendingSingleClickY = event.y
                            singleClickExitTimer.restart()
                            return
                        }
                        fokuszKattintas(event.x, event.y)
                    }
                    onDoubleClicked: function(event) {
                        if (viewer.singleClickExitEnabled
                                && viewer.layoutMode === "1up"
                                && !editorPanel.tiltActive) {
                            singleClickExitTimer.stop()
                            // A MouseArea a második lenyomáskor jelzi a dupla
                            // kattintást. Elfogadott jelzésnél elnyomja a második
                            // kattintás released/clicked jelzéseit is, ezért a
                            // kiengedésre időzített bezárás nem futna le.
                            exitAfterDoubleClick = true
                            // Engedjük kiadni a második kattintás jelzéseit:
                            // az onClicked a fenti jelzővel őrzi a nézőt, az
                            // onReleased pedig a kiengedés UTÁN zárja be.
                            event.accepted = false
                        } else {
                            viewer.zoomFit()
                        }
                    }
                    onReleased: {
                        if (!exitAfterDoubleClick) return
                        exitAfterDoubleClick = false
                        Qt.callLater(function() { viewer.kerBezaras() })
                    }
                }

                BusyIndicator {
                    anchors.centerIn: parent
                    running: photo.status === Image.Loading
                }

                ZoomNavigator {
                    objectName: "zoomNavigator"
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.rightMargin: 8
                    anchors.bottomMargin: captionBar.visible
                        ? captionBar.height + 8 : 8
                    visible: !viewer.quickViewerMode
                             && viewer.zoomFactor > 1.01
                             && !viewer.isCurrentVideo
                             && !viewer.zoomNavigatorDismissed
                    imageSource: photoArea.fokuszKep.source
                    imageAspect: photoArea.fokuszKep.paintedHeight > 0
                        ? photoArea.fokuszKep.paintedWidth
                          / photoArea.fokuszKep.paintedHeight : 1
                    imageRotation: photoArea.fokuszKep.rotation
                    zoomFactor: viewer.zoomFactor
                    zoomPercent: viewer.zoomFactor
                        / Math.max(0.01, viewer.actualZoomFactor()) * 100
                    viewRect: viewer.zoomNavigatorViewRect
                    onPanRequested: function(deltaX, deltaY) {
                        viewer.panFromZoomNavigator(deltaX, deltaY)
                    }
                    onCloseRequested: viewer.zoomNavigatorDismissed = true
                }

                // #1072 — `editpanel/render_now` („Létrehozás"): a PISZKOZAT
                // külön befejező lépése. A `projectutils::draft_collage`
                // szövege erre a gombra hivatkozik: a megosztás és a
                // nyomtatás feltétele, hogy a felhasználó megnyomja.
                //
                // A HELYE mért, nem választott (spec 4.3, `editpanel.tre`):
                // az `overlay_group` gyereke, tehát a kép FÖLÖTTI réteg —
                // a bélyegképen nincs rajta, csak a JPEG-be égetett
                // „PISZKOZAT" felirat. Vízszintesen középen (`m_centerX`),
                // függőlegesen a saját közepe a szülő 87,5%-án
                // (`YConstraint 0.5, 0.875, 0`).
                //
                // ⚠️ Renderelés közben az eredeti ugyanide teszi a
                // „Folyamatban..." feliratot (`editpanel/in_progress_label`)
                // — a kettő EGYMÁS HELYÉRE lép, ezért egyetlen elem
                // felirata változik, nem két külön gomb.
                PicasaButton {
                    id: piszkozatLetrehozas
                    objectName: "viewerCreateNowButton"
                    //: `editpanel/render_now` / `editpanel/in_progress_label`
                    text: viewer.controllerReady && controller.collageRendering
                          ? qsTr("In Progress...") : qsTr("Create Now")
                    enabled: !(viewer.controllerReady
                               && controller.collageRendering)
                    font.pixelSize: Theme.fontSize
                    visible: !viewer.quickViewerMode
                             && viewer.currentIsCollageDraft
                    x: (parent.width - width) / 2
                    y: parent.height * 0.875 - height / 2
                    ToolTip.text: qsTr("Render the final collage from this draft")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    onClicked: controller.finishCollageDraft(
                        viewer.currentFilePath)
                }

                // #2564: a nagyítás-hármas (illesztés · 1:1 · csúszka) ELKERÜLT
                // innen az ALSÓ ESZKÖZSÁVBA (`TrayBar.qml`,
                // `trayViewerZoomRow`) — mérve az `editpanel.tre:1288–1324`
                // horgonyai és a `respack.yt` x-tartományai szerint az
                // eredetiben a könyvtár nagyító + bélyegkép-csúszka
                // párjának a HELYÉN ül, nem a fotó fölött lebegve.
                //
                // Ez a doboz a MI KÉT arc-gombunké maradt (`☺` és `✎`):
                // ezek nincsenek az eredetiben (saját döntés, #147/#26), és
                // a #2564 kifejezetten hatókörön kívül hagyta őket. A
                // lebegő forma nekik marad, mert a fotón értelmezett
                // állapotot kapcsolnak.
                Rectangle {
                    id: facesBar
                    objectName: "viewerFacesBar"
                    //: VÁLTOZATLAN feltétel: ugyanaz, ami a korábbi
                    //: `zoomBar`-t vezérelte — videón nincs arc-keret,
                    //: vágás közben pedig a fotó fölötti réteg tiszta.
                    visible: !viewer.quickViewerMode
                             && viewer.photoOverlaysUsable
                    anchors.right: parent.right
                    anchors.rightMargin: 4
                    //: #2565: a felirat-sáv FÖLÉ, nem rá. A sáv a fotó
                    //: alján végigfut (mérve), és a lebegő doboz eddig
                    //: eltakarta a sáv jobb szélén ülő kukát — a kirajzolt
                    //: képen látszott, számolásból nem derült volna ki.
                    anchors.bottom: captionBar.visible
                                    ? captionBar.top : parent.bottom
                    anchors.bottomMargin: 4
                    width: facesRow.width + 12
                    height: 26
                    radius: 4
                    color: "#00000059"
                    Row {
                        id: facesRow
                        anchors.centerIn: parent
                        spacing: 4
                        // #147: arc-keretek be/ki (F billentyűvel egyenértékű)
                        PicasaButton {
                            objectName: "facesToggleButton"
                            text: "☺"
                            checkable: true
                            checked: viewer.facesVisible
                            width: 26; height: 20
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Show Faces")
                            ToolTip.delay: Theme.tooltipDelay
                            onClicked: viewer.toggleFaces()
                        }
                        // #26 (2. kör): arc-SZERKESZTŐ mód be/ki
                        // (Shift+F billentyűvel egyenértékű) — videónál
                        // nincs értelme, ott letiltjuk.
                        PicasaButton {
                            objectName: "facesEditToggleButton"
                            text: "✎"
                            checkable: true
                            checked: viewer.facesEditMode
                            enabled: !viewer.isCurrentVideo
                            width: 26; height: 20
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Edit Faces")
                            ToolTip.delay: Theme.tooltipDelay
                            onClicked: viewer.toggleFacesEdit()
                        }
                    }
                }
                // szerkeszthető felirat-sor — a model.revision referencia
                // miatt a kötés modell-frissítésnél (pl. mentés után)
                // újraértékelődik, ahogy a forgatás-kötés is (lásd fent).
                // Gépeléskor a Qt eltávolítja a deklaratív kötést a text
                // property-ről (közvetlen C++ írás), ezért elfogadás és
                // Esc után Qt.binding()-gel újra be kell kötni, különben a
                // mező a következő navigáláskor nem frissülne.
                // #1816: a felirat-sáv KÉT vezérlője. Az eredetiben a
                // `captionbutton` („Show/Hide Caption") és a `captiontrash`
                // („Delete this caption") — a `0x0057bb50` kezelő a
                // `captionbutton` · `caption` · `captiontrash` hármast
                // EGYÜTT kezeli.
                //
                // ⚠️ A jegy KÉT belépési pontot ír elő (`editpanel/` és
                // `editoneup/captionbutton`). Nálunk a szerkesztő panel a
                // NÉZŐN BELÜL él (`EditorPanel` ugyanebben a fájlban), tehát
                // ez az EGY sáv mindkét állapotot kiszolgálja — mérve, nem
                // feltételezve: a sáv `visible`-je csak a vágásra és a
                // videóra érzékeny, a szerkesztő nyitottságára nem.
                // #2565 + #2587: a KÉPALÁÍRÁS-SÁV. A mérce a tulajdonos NÉGY
                // felvétele (`research/felirat-ki-bekapcsolva/`, 1920 × 1080,
                // Picasa 3 és PicasaPy, felirat BE és KI állapotban).
                //
                // A `.tre` kényszerei (`editpanel.tre:1238–1266`):
                //   `captionbutton`  `XConstraint 0, 0, 3`   `Y 1, 1, -3`
                //   `caption`        `X 0, 0, 25` … `1, 1, -24`
                //   `captiontrash`   `XConstraint 1, 1, -3`  `Y 1, 1, -3`
                //   `captionbase` / `captionbasetop`: a sáv HÁTTERE
                //     (`predraw 1`), teljes szélességben.
                //
                // ⚠️ A `captionbutton` `hidetarget`-je a `caption` és a
                // `captiontrash` — **magát a gombot nem**. A felvételen ez
                // pontosan így látszik: kikapcsolt feliratnál a SÁV eltűnik,
                // a kapcsoló viszont OTT MARAD a kép bal alsó sarkában.
                // Ezért ül a gomb a fotó-terület rétegén, nem a sávban.
                Item {
                    id: captionBar
                    objectName: "captionBar"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    //: MÉRT magasság: a felvételen a csík y 906…926 (21 px).
                    height: 21
                    visible: viewer.captionVisible && !viewer.quickViewerMode

                    //: `captionbase` + `captionbasetop` — a sáv saját
                    //: háttere. MÉRVE: a felvételen `#c6c6c6`, vagyis a
                    //: KRÓM világosszürkéje, nem a fotó-terület szürkéje és
                    //: nem sötét. Sötét témában a króm sötét párja.
                    Rectangle {
                        id: captionBarBackground
                        objectName: "captionBarBackground"
                        anchors.fill: parent
                        color: Theme.captionBar
                    }

                    TextInput {
                        id: captionField
                        objectName: "captionField"
                        //: `caption`: a két gomb KÖZÖTT, a sáv teljes
                        //: maradékán — az eredetin a felirat a sáv
                        //: közepén áll, FÉLKÖVÉREN és sötéten.
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.leftMargin: 25
                        anchors.rightMargin: 24
                        anchors.verticalCenter: parent.verticalCenter
                        horizontalAlignment: TextInput.AlignHCenter
                        color: Theme.captionBarText
                        font.pixelSize: Theme.fontSize
                        font.bold: true
                        selectByMouse: true
                        text: viewer.photosModel
                            ? (viewer.photosModel.revision,
                               viewer.photosModel.captionAt(viewer._kijeloltSort()))
                            : ""

                        function rebind() {
                            text = Qt.binding(function () {
                                return viewer.photosModel
                                    ? (viewer.photosModel.revision,
                                       viewer.photosModel.captionAt(viewer._kijeloltSort()))
                                    : ""
                            })
                        }

                        onAccepted: {
                            controller.setCaption(viewer._kijeloltSort(), text)
                            rebind()
                            viewer.forceActiveFocus()
                        }
                        Keys.onEscapePressed: (event) => {
                            rebind()
                            viewer.forceActiveFocus()
                            event.accepted = true
                        }
                    }

                    //: A felszólítás a SÁVBAN áll, a felirat helyén — az
                    //: eredetin („Készítsen képaláírást!") ugyanott, ahol a
                    //: kész felirat lenne (a `235707.jpg` felvételen
                    //: közvetlenül összevethető).
                    Text {
                        objectName: "captionPlaceholder"
                        anchors.centerIn: parent
                        text: qsTr("Make a caption!")
                        color: Theme.captionBarText
                        opacity: 0.7
                        font.pixelSize: Theme.fontSize
                        visible: captionField.text.length === 0
                                 && !captionField.activeFocus
                    }

                    ToolButton {
                        objectName: "captionTrashButton"
                        anchors.right: parent.right
                        anchors.rightMargin: 3
                        anchors.verticalCenter: parent.verticalCenter
                        flat: true
                        implicitWidth: 17
                        implicitHeight: 13
                        text: "✕"
                        //: `captiontrash` — az eredeti buboréksúgója
                        ToolTip.text: qsTr("Delete this caption")
                        ToolTip.visible: hovered
                        ToolTip.delay: Theme.tooltipDelay
                        // üres feliratot nincs mit törölni
                        enabled: captionField.text.length > 0
                        contentItem: Text {
                            text: parent.text
                            color: Theme.captionBarText
                            opacity: parent.enabled ? (parent.hovered ? 1 : 0.7) : 0.3
                            font.pixelSize: Theme.fontSize - 2
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Item {}
                        // #1816 DÖNTÉS: NINCS megerősítés. Az eredetiben ez
                        // szemetes-ikon közvetlen hatással, és a művelet nem
                        // lemezromboló: a felirat egyetlen mező,
                        // újragépelhető. A projekt #459-es elve a
                        // megerősítést a lemezt érintő, visszafordíthatatlan
                        // műveletekre tartja fenn. (Az eredetiről ez NINCS
                        // mérve — saját döntés.)
                        onClicked: {
                            controller.setCaption(viewer._kijeloltSort(), "")
                            captionField.rebind()
                        }
                    }
                }

                // #2587: a felirat-KAPCSOLÓ a fotó-terület BAL ALSÓ sarkában,
                // a sáv állapotától FÜGGETLENÜL. A `.tre` szerint a
                // `captionbutton` `hidetarget`-je csak a `caption` és a
                // `captiontrash`; a felvételen kikapcsolt feliratnál is ott
                // áll a kis világos négyzet — ez az EGYETLEN út vissza.
                //
                // MÉRT geometria (`picasa3-felirat-*.jpg`, mindkét állapotban
                // AZONOS): a fehér doboz x 287…303, y 910…922 — vagyis
                // **17 × 13**, a fotó-terület bal szélétől 1 képponttal, a
                // sáv függőleges közepén.
                //
                // KÉT ÁLLAPOT (`editoneup/caption_icon` és
                // `caption_yesicon`, `oneup.tre:112–124`): bekapcsolt
                // feliratnál a dobozban két vízszintes vonal, kikapcsoltnál
                // ÜRES a doboz. A felvételen pontosan ez látszik.
                Rectangle {
                    id: captionToggle
                    objectName: "captionToggleButton"
                    anchors.left: parent.left
                    anchors.leftMargin: 1
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: viewer.captionVisible
                                          ? (captionBar.height - height) / 2 : 4
                    width: 17
                    height: 13
                    radius: 2
                    visible: viewer.photoOverlaysUsable
                             && !viewer.quickViewerMode
                    color: Theme.captionToggleBg
                    border.width: 1
                    border.color: viewer.captionVisible
                                  ? Theme.captionToggleBorder : "transparent"

                    //: `caption_icon`: két vízszintes vonal — CSAK bekapcsolt
                    //: feliratnál (a kikapcsolt állapot doboza üres).
                    Column {
                        anchors.centerIn: parent
                        spacing: 3
                        visible: viewer.captionVisible
                        Repeater {
                            model: 2
                            Rectangle {
                                width: 9
                                height: 1
                                color: Theme.captionToggleBorder
                            }
                        }
                    }

                    ToolTip.text: qsTr("Show/Hide Caption")
                    ToolTip.visible: egerTerulet.containsMouse
                    ToolTip.delay: Theme.tooltipDelay
                    MouseArea {
                        id: egerTerulet
                        anchors.fill: parent
                        //: a MÉRT doboz 17 × 13 — kicsi a kényelmes
                        //: találathoz, ezért az érzékeny terület nagyobb, a
                        //: RAJZ viszont a mért méretű marad
                        anchors.margins: -5
                        hoverEnabled: true
                        onClicked: viewer.billentsdAFeliratot()
                    }
                }


                // elő-betöltés: a szomszédok már dekódolva, mire lépsz —
                // a #84 óta a mappán belüli szomszéd (folderNeighbor), nem
                // a nyers currentIndex±1, hogy ne a szomszéd mappa képét
                // töltsük elő feleslegesen a mappahatárnál
                Image {
                    id: elotoltoKovetkezo
                    objectName: "viewerPreloadNext"
                    visible: false
                    //: #3877: forrás és forrásméret EGYÜTT (`viewer._betolt`);
                    //: a `fillMode` a `photo`/`photoElotte`-é, különben a Qt
                    //: gyorstára nem találna (#3832).
                    readonly property var betoltes: viewer._elotoltoPar(1)
                    onBetoltesChanged: Qt.callLater(viewer._betoltesekIrasa)
                    Component.onCompleted: viewer._betolt(elotoltoKovetkezo, betoltes)
                    fillMode: Image.PreserveAspectFit
                    asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
                }
                Image {
                    id: elotoltoElozo
                    objectName: "viewerPreloadPrev"
                    visible: false
                    readonly property var betoltes: viewer._elotoltoPar(-1)
                    onBetoltesChanged: Qt.callLater(viewer._betoltesekIrasa)
                    Component.onCompleted: viewer._betolt(elotoltoElozo, betoltes)
                    fillMode: Image.PreserveAspectFit
                    asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
                }

                // #4183: a bal fiók függőleges peremén marad, és becsukás
                // után is visszanyitható. A méretet az eredeti mérés adja.
                ToolButton {
                    objectName: "toggle_left_drawer"
                    visible: !viewer.quickViewerMode
                    x: 1
                    anchors.verticalCenter: parent.verticalCenter
                    width: 15
                    height: 16
                    z: 20
                    flat: true
                    text: viewer.editorDrawerOffset === 0 ? "‹" : "›"
                    ToolTip.text: qsTr("Show/Hide Edit Controls")
                    ToolTip.visible: hovered
                    ToolTip.delay: Theme.tooltipDelay
                    contentItem: Text {
                        text: parent.text
                        color: Theme.panelHeaderText
                        font.pixelSize: 17
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Item {}
                    onClicked: viewer.toggleEditorDrawer()
                }
            }

            // #192: Tulajdonságok-panel jobb oldalt — ugyanaz a buta
            // komponens, mint a könyvtár-nézetben (Main.qml), a nézett
            // kép adataival; a bezárás a közös kapcsolót állítja le
            PropertiesPanel {
                objectName: "viewerPropertiesPanel"
                visible: viewer.propertiesOpen
                Layout.preferredWidth: 210
                Layout.minimumWidth: 160
                Layout.fillHeight: true
                hasSelection: viewer.currentIndex >= 0
                appController: (typeof controller !== "undefined")
                               ? controller : null
                selectedRows: viewer.currentIndex >= 0
                              ? [viewer.currentIndex] : []
                focusRow: viewer.currentIndex
                // a photos.revision-nel együtt kötve: modell-frissüléskor
                // (pl. forgatás, felirat-mentés) újraolvas; a controller
                // önálló példányosításnál (tesztek) hiányozhat
                entries: (viewer.propertiesOpen && viewer.photosModel
                          && typeof controller !== "undefined" && controller)
                    ? (viewer.photosModel.revision,
                       controller.propertiesOf(viewer.currentIndex))
                    : []
                onCloseRequested: viewer.zarjaAFiokot()
                onEditTagsRequested: {
                    if (viewer.appWindow
                            && viewer.appWindow.valtsFiokLapot !== undefined)
                        viewer.appWindow.valtsFiokLapot("tags")
                }
            }

            //: #2566: a másik három lap CSAK AKKOR létezik, ha a NÉZŐ
            //: LÁTSZIK, és épp az a lap aktív.
            //:
            //: ⚠️ Ez nem takarékosság, hanem HELYESSÉG. A három komponens a
            //: SAJÁT gyerekeire éget objectName-et (`placesClearButton`,
            //: `peoplePanelClose`, `tagInput` …), amit a példányosítás
            //: helyén nem lehet felülírni. Mohó példányosítással a
            //: `findChild` a nézőbeli MÁSODPÉLDÁNYT találná meg a
            //: könyvtárbeli helyett — a `test_qml_places.py` két őre
            //: azonnal el is bukott rá, mielőtt `Loader`-be került.
            //: Csukott néző mellett így egyetlen példány van, a könyvtáré.
            //:
            //: ⚠️ A `viewer.visible` NEM elhagyható: a fiók lapját a
            //: KÖNYVTÁRBAN is át lehet kapcsolni, és a `tagsOpen` akkor is
            //: igaz — a néző példánya enélkül a könyvtár-nézetben is
            //: felépülne.
            Loader {
                objectName: "viewerTagsPanelLoader"
                active: viewer.tagsOpen && viewer.visible
                visible: viewer.tagsOpen
                Layout.preferredWidth: 190
                Layout.minimumWidth: 150
                Layout.fillHeight: true
                //: Ugyanaz a buta komponens, mint a könyvtárban; a
                //: különbség csak az, hogy MIRE hat: ott a rács
                //: kijelölésére, itt a nézett képre (`drawerRows`).
                sourceComponent: TagsPanel {
                    objectName: "viewerTagsPanel"
                    hasSelection: viewer.currentIndex >= 0
                    //: a photos.revision-nel együtt kötve: címke-írás után
                    //: azonnal frissül (a könyvtári párja ugyanígy)
                    tags: (viewer.photosModel && viewer.controllerReady
                           && viewer.currentIndex >= 0)
                        ? (viewer.photosModel.revision,
                           controller.keywordsOfRows(viewer.drawerRows))
                        : []
                    onAddRequested: function(keyword) {
                        if (viewer.controllerReady)
                            controller.addKeywordToRows(
                                viewer.drawerRows, keyword)
                    }
                    onRemoveRequested: function(keyword) {
                        if (viewer.controllerReady)
                            controller.removeKeywordFromRows(
                                viewer.drawerRows, keyword)
                    }
                    //: a helyi menü „rátétel a kijelölésre" tétele: a
                    //: nézőben a kijelölés EGY kép, tehát ugyanoda fut,
                    //: mint a hozzáadás
                    onAddToSelectionRequested: function(keyword) {
                        if (viewer.controllerReady)
                            controller.addKeywordToRows(
                                viewer.drawerRows, keyword)
                    }
                    //: a találatok a KÖNYVTÁR rácsán jelennek meg, amit a
                    //: néző eltakarna — ezért a gazda zárja a nézőt, és
                    //: ő keres
                    onFindTaggedRequested: function(keyword) {
                        viewer.findTaggedRequested(keyword)
                    }
                    onCloseRequested: viewer.zarjaAFiokot()
                }
            }

            Loader {
                objectName: "viewerPlacesPanelLoader"
                active: viewer.placesOpen && viewer.visible
                visible: viewer.placesOpen
                Layout.preferredWidth: 320
                Layout.minimumWidth: 220
                Layout.fillHeight: true
                sourceComponent: PlacesPanel {
                    objectName: "viewerPlacesPanel"
                    appWindow: viewer.appWindow
                    //: a geocímkézés a NÉZETT képre hat, nem a rács
                    //: kijelölésére (ld. `drawerRows`)
                    targetRows: viewer.drawerRows
                    //: a térkép-jelölőre kattintva a néző lép oda — a
                    //: könyvtárban ugyanez a jel a rács kijelölését mozgatja
                    onPhotoActivated: function(row) { viewer.show(row) }
                    onMarkerSearchRequested: function(rows) {
                        if (!rows || rows.length === 0) return
                        viewer.appWindow.selectedIndexes = rows.slice(0)
                        viewer.show(rows[0])
                    }
                    onClearGeotagRequested: function(rows) {
                        viewer.clearGeotagRequested(rows)
                    }
                    onSetGeotagRequested: function(rows, la, lo) {
                        viewer.setGeotagRequested(rows, la, lo)
                    }
                    onPhotosDroppedRequested: function(rows, la, lo) {
                        viewer.dropGeotagRequested(rows, la, lo)
                    }
                    onCloseRequested: viewer.zarjaAFiokot()
                }
            }

            Loader {
                objectName: "viewerPeoplePanelLoader"
                active: viewer.peopleOpen && viewer.visible
                visible: viewer.peopleOpen
                Layout.preferredWidth: 280
                Layout.minimumWidth: 200
                Layout.fillHeight: true
                //: A nézett kép nevesített emberei.
                sourceComponent: PeoplePanel {
                    objectName: "viewerPeoplePanel"
                    headerRefreshKey: [viewer.drawerRows.join(","),
                        viewer.currentIndex, viewer.peopleOpen,
                        viewer.facesEditMode,
                        viewer.manualFaceAddRevision,
                        viewer.controllerReady
                            ? controller.currentPersonName : "",
                        pendingCount() > 0].join("|")
                    selectionCount: viewer.drawerRows.length
                    faceScanController: viewer.appWindow
                        ? viewer.appWindow._faceScanController : null
                    currentPerson: viewer.controllerReady
                        ? controller.currentPersonName : ""
                    //: #4586: a háttér-arckeresés állapota (spec 9/b)
                    loading: uncheckedCount > 0
                    uncheckedCount: pendingCount()
                    sortingPercent: faceScanController
                        ? faceScanController.sortingPercent : -1
                    peopleHere: (viewer.photosModel && viewer.controllerReady)
                        ? (viewer.appWindow
                           ? viewer.appWindow.peopleFaceRevision : 0,
                           viewer.photosModel.revision,
                           controller.peopleOfRows(viewer.drawerRows))
                        : []
                    unnamedFacesHere:
                        (viewer.photosModel && viewer.controllerReady)
                        ? (viewer.appWindow
                           ? viewer.appWindow.peopleFaceRevision : 0,
                           viewer.appWindow
                           ? viewer.appWindow.unnamedFaceRevision : 0,
                           viewer.photosModel.revision,
                           controller.unnamedFacesOfRows(viewer.drawerRows))
                        : []
                    function pendingCount() {
                        if (!viewer.peopleOpen || !faceScanController
                                || !viewer.photosModel)
                            return 0
                        // a függés az `uncheckedFiles`-en: haladásra újraszámol
                        if (faceScanController.uncheckedFiles <= 0)
                            return 0
                        var paths = []
                        for (var i = 0; i < viewer.drawerRows.length; ++i) {
                            var path = viewer.photosModel.filePathAt(
                                Number(viewer.drawerRows[i]))
                            if (path.length > 0) paths.push(path)
                        }
                        return faceScanController.pendingAmong(paths)
                    }
                    //: #3566: a szerkesztőben mindig az egyképes ág fut
                    //: (az eredetiben az `editpanel/preview` látszik)
                    editorView: true
                    manualAddActive: viewer.facesEditMode
                    //: a személy albuma a KÖNYVTÁR rácsán nyílik — a gazda
                    //: zárja a nézőt, és ő vált (ld. `findTaggedRequested`)
                    onPersonChosen: function(name) { viewer.personChosen(name) }
                    onManualAddRequested: viewer.beginManualFaceAdd()
                    onManualCancelRequested: viewer.cancelManualFaceAdd()
                    onCloseRequested: viewer.zarjaAFiokot()
                }
            }
        }
    }

    // A Slingshot külön ablakának képsávja. A reference frame középpontja
    // x=512, a vezérlők képkockái és sorrendje a spec 12.8.2-ből származik.
    // A 1024×800-as koordinátarendszert középre és az ablak aljához igazítjuk;
    // a spec nem rögzíti a gyorsnézet háttérszínét, ezért a meglévő Theme marad.
    Item {
        id: quickViewerToolbar
        objectName: "viewerQuickToolbar"
        anchors.fill: parent
        visible: viewer.quickViewerMode
        z: 100

        PicasaButton {
            objectName: "viewerQuickZoomInButton"
            x: (parent.width - 1024) / 2 + 253
            y: parent.height - 800 + 744
            width: 29; height: 19
            padding: 0
            text: "+"
            autoRepeat: true
            ToolTip.text: qsTr("Zoom In")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.lepjZoom(0.05)
        }
        PicasaButton {
            objectName: "viewerQuickZoomOutButton"
            x: (parent.width - 1024) / 2 + 283
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            text: "−"
            autoRepeat: true
            ToolTip.text: qsTr("Zoom Out")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.lepjZoom(-0.05)
        }
        PicasaButton {
            objectName: "viewerQuickZoomActualButton"
            x: (parent.width - 1024) / 2 + 312
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            text: "1:1"
            ToolTip.text: qsTr("Zoom to 1:1")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.zoomActual()
        }
        PicasaButton {
            objectName: "viewerQuickLaunchPicasaButton"
            x: (parent.width - 1024) / 2 + 351
            y: parent.height - 800 + 744
            width: 119; height: 19
            leftPadding: 30
            text: qsTr("Edit in PicasaPy")
            ToolTip.text: qsTr("Launch PicasaPy")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.kerBezaras()
            Image {
                source: "icons/viewer-back-arrow.svg"
                width: 17; height: 15
                sourceSize.width: 17; sourceSize.height: 15
                anchors.left: parent.left
                anchors.leftMargin: 7
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        PicasaButton {
            objectName: "viewerQuickPrevButton"
            x: (parent.width - 1024) / 2 + 473
            y: parent.height - 800 + 739
            width: 29; height: 30
            padding: 0
            background: null
            autoRepeat: true
            enabled: viewer.hasPrevious()
            onClicked: viewer.previous()
            ToolTip.text: qsTr("Previous Photo")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                source: "icons/viewer-step-left.svg"
                width: 30; height: 31
                sourceSize.width: 30; sourceSize.height: 31
                anchors.centerIn: parent
            }
        }
        PicasaButton {
            objectName: "viewerQuickPlayButton"
            x: (parent.width - 1024) / 2 + 494
            y: parent.height - 800 + 733
            width: 39; height: 35
            padding: 0
            background: null
            text: "▶"
            Accessible.name: qsTr("Play Slideshow")
            ToolTip.text: qsTr("Play Slideshow")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.playRequested()
        }
        PicasaButton {
            objectName: "viewerQuickNextButton"
            x: (parent.width - 1024) / 2 + 523
            y: parent.height - 800 + 738
            width: 28; height: 30
            padding: 0
            background: null
            autoRepeat: true
            enabled: viewer.hasNext()
            onClicked: viewer.next()
            ToolTip.text: qsTr("Next Photo")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            contentItem: Image {
                source: "icons/viewer-step-right.svg"
                width: 30; height: 31
                sourceSize.width: 30; sourceSize.height: 31
                anchors.centerIn: parent
            }
        }
        PicasaButton {
            objectName: "viewerQuickUploadButton"
            x: (parent.width - 1024) / 2 + 555
            y: parent.height - 800 + 744
            width: 76; height: 19
            padding: 0
            enabled: viewer.quickUploadAvailable
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
            objectName: "viewerQuickRotateLeftButton"
            x: (parent.width - 1024) / 2 + 639
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            ToolTip.text: qsTr("Rotate counter-clockwise")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.rotateRequested(viewer._kijeloltSort(), -1)
            contentItem: Image {
                source: "icons/tray-rotate-left.svg"
                width: 15; height: 17
                sourceSize.width: 15; sourceSize.height: 17
                fillMode: Image.PreserveAspectFit
            }
        }
        PicasaButton {
            objectName: "viewerQuickRotateRightButton"
            x: (parent.width - 1024) / 2 + 668
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            ToolTip.text: qsTr("Rotate clockwise")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.rotateRequested(viewer._kijeloltSort(), 1)
            contentItem: Image {
                source: "icons/tray-rotate-right.svg"
                width: 15; height: 17
                sourceSize.width: 15; sourceSize.height: 17
                fillMode: Image.PreserveAspectFit
            }
        }
        PicasaButton {
            objectName: "viewerQuickStarButton"
            x: (parent.width - 1024) / 2 + 702
            y: parent.height - 800 + 744
            width: 28; height: 19
            padding: 0
            ToolTip.text: qsTr("Star")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: viewer.starRequested(viewer._kijeloltSort())
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
            id: quickViewerMoreOptionsButton
            objectName: "viewerQuickMoreOptionsButton"
            x: (parent.width - 1024) / 2 + 737
            y: parent.height - 800 + 743
            width: 34; height: 21
            padding: 0
            Accessible.name: qsTr("More Options")
            ToolTip.text: qsTr("Click to see more options")
            ToolTip.visible: hovered
            ToolTip.delay: Theme.tooltipDelay
            onClicked: {
                var point = quickViewerMoreOptionsButton.mapToItem(
                    viewer, 0, quickViewerMoreOptionsButton.height)
                viewer.openContextMenu(point.x, point.y)
            }
            contentItem: Image {
                source: "icons/tray-more.svg"
                width: 16; height: 16
                sourceSize.width: 16; sourceSize.height: 16
                fillMode: Image.PreserveAspectFit
            }
        }
    }

    //: #2566: a fiók ürítésének EGYETLEN útja a nézőből. A négy fiók-jelző
    //: SZÁRMAZTATOTT (#1773), közvetlenül nem írható — az ablak függvénye
    //: üríti. A `!== undefined` a #1572-őr mintája: a próbák stub-ablakán
    //: nincs rajta a függvény.
    function zarjaAFiokot() {
        if (viewer.appWindow && viewer.appWindow.ureseidAFiokot !== undefined)
            viewer.appWindow.ureseidAFiokot()
    }

    // -- #422: jobbklikk-menü a nagy képen ---------------------------------
    // A nézőben eddig egyáltalán nem volt kontextusmenü (a Picasa `OneUp`
    // menüosztálya, 17 tétel — ld. ViewerContextMenu.qml). A parancsok a
    // globális context property-ken (controller, fileOpsController) át
    // futnak, a törlés dialógusa pedig jelként megy a Main.qml-nek — így a
    // forró Main.qml csak egyetlen bekötést kap.

    readonly property string currentPath: viewer.photosModel
        && viewer.currentIndex >= 0
        ? viewer.photosModel.filePathAt(viewer.currentIndex) : ""

    //: #4621: az AKTÍV (kijelölt) fél képének útja — A|B módban jobb
    //: fókusszal nem a `currentPath` (bal kép). A helyi menü minden tétele
    //: ezt használja, hogy az egész menü EGY képre vonatkozzon, a törlés
    //: (`_kijeloltSort()`) is. FÜGGVÉNY, mert imperatív kezelők hívják (#218).
    function _aktivUt() {
        var sor = viewer._kijeloltSort()
        return viewer.photosModel && sor >= 0
            ? viewer.photosModel.filePathAt(sor) : ""
    }

    //: #1612: a menü HALASZTOTT — az `ensure()` az első jobbklikkre építi
    //: fel. Mérve: a `viewerContextMenu` 360 QObject, és a legtöbb
    //: munkamenetben a felhasználó egyszer sem jobbklikkel a nagy képen.
    function openContextMenu(x, y) { viewerMenuLoader.ensure().popupForPhoto(viewer, x, y, viewer._aktivUt(), typeof fileOpsController !== "undefined" ? fileOpsController : null) }

    //: #4566: a `movieeditpanel/reset_trim` megerősítése — az eredeti
    //: `CThumbUI::UndomovieEdits` kérdése és `IDS_CONFIRMREVERT_YES_BUTTON`
    //: igen-gombja (`docs/specs/ui-audit-editor.md`, a `reset_trim` szakasza)
    DeferredDialog {
        id: movieResetConfirmLoader
        objectName: "movieResetConfirmDialogLoader"
        anchors.fill: parent
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "movieResetConfirmDialog"
                namePrefix: "movieResetConfirm"
                property int row: -1
                yesText: qsTr("Remove Edits")
                function askFor(sor) {
                    row = sor
                    ask("", qsTr("Remove all movie edits?"))
                }
                onConfirmed: {
                    if (controller && controller.resetMovieTrim !== undefined)
                        controller.resetMovieTrim(row)
                }
            }
        }
    }

    DeferredDialog {
        id: viewerMenuLoader
        objectName: "viewerContextMenuLoader"
        sourceComponent: Component {
        ViewerContextMenu {
        id: viewerMenu
        removesFromAlbum: viewer.deleteRemovesFromAlbum
        // a revision-nel együtt kötve, hogy a menü újranyitáskor friss
        // rejtett-állapotot mutasson (a PhotoContextMenu mintája)
        hidden: viewer.photosModel && viewer.currentIndex >= 0
            ? (viewer.photosModel.revision,
               viewer.photosModel.itemAt(viewer.currentIndex).hidden === true)
            : false
        // #305: null-őr — a controller a leépítéskor átmenetileg null lehet
        albums: typeof controller !== "undefined" && controller
            ? controller.albums : []

        // #422: a mentés-parancsok aktív állapota a NÉZETT képre
        hasEdits: viewer.photosModel && viewer.currentIndex >= 0
            ? (viewer.photosModel.revision,
               viewer.photosModel.itemAt(viewer.currentIndex).hasEdits === true)
            : false
        hasBackup: typeof controller !== "undefined" && controller
                   && viewer.currentIndex >= 0
            ? controller.hasSavedBackup([viewer.currentIndex]) : false

        onSaveRequested: viewer.saveRequested(viewer.currentIndex)
        onRevertRequested: viewer.revertRequested(viewer.currentIndex)
        onUndoAllEditsRequested: viewer.undoAllEditsRequested(viewer.currentIndex)
        onResetFacesRequested: viewer.resetFacesRequested()

        onBackToLibraryRequested: viewer.kerBezaras()
        //: #3014: a KIJELÖLT oldal képe megy az albumba — ez a kettős
        //: nézet válogató munkafolyamata (a jobbik képet egy lépéssel
        //: albumba tenni). Egy kép módban változatlanul a jelenlegi.
        //:
        //: ⚠️ A jegy `TwoUpAddToAlbum` néven külön vezérlőt említett; a
        //: binárisban ilyen sztring NINCS (a `TwoUp` minta mind a hat
        //: találata a `swap_2up_*`/`Confirm2up*` család). Az eredetiben
        //: tehát nincs külön gomb: a MEGLÉVŐ albumba tétel hat a
        //: kijelölt oldalra, amit a „Kijelölve" jelvény mutat.
        onAddToAlbumRequested: function(token) {
            if (typeof controller !== "undefined" && controller)
                controller.addRowsToAlbum([viewer.aktivSor], token)
        }
        onRotateRightRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.rotateRight(viewer.currentIndex)
        }
        onRotateLeftRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.rotateLeft(viewer.currentIndex)
        }
        onHideToggleRequested: {
            if (typeof controller !== "undefined" && controller
                && viewer.currentIndex >= 0)
                controller.toggleHiddenRows([viewer.currentIndex])
        }
        onOpenFileRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer._aktivUt().length > 0)
                fileOpsController.openPhoto(viewer._aktivUt())
        }
        onLocateRequested: function(original) {
            if (typeof fileOpsController !== "undefined" && fileOpsController && viewer._aktivUt().length > 0)
                original ? fileOpsController.revealOriginal(viewer._aktivUt())
                    : fileOpsController.revealPhoto(viewer._aktivUt())
        }
        onCopyFullPathRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer._aktivUt().length > 0)
                fileOpsController.copyFullPath(viewer._aktivUt())
        }
        onDeleteRequested: {
            if (viewer._aktivUt().length > 0)
                viewer.deleteRequested()
        }
        onPropertiesRequested: {
            // #1773: a helyi menü a fiók Tulajdonságok lapjára VÁLT (az
            // eredetiben a négy lap kizáró csoport); ha már az látszik, a
            // nézőben a billentyűhöz hasonlóan zárja a fiókot.
            if (viewer.appWindow
                && viewer.appWindow.valtsFiokLapot !== undefined)
                viewer.appWindow.propertiesPanelOpen
                    ? viewer.appWindow.ureseidAFiokot()
                    : viewer.appWindow.valtsFiokLapot("properties")
        }
    }
        }
    }

    // jobbklikk BÁRHOL a nézőn — a Picasában a nagy kép és a körülötte lévő
    // szürke háttér is ugyanezt a menüt nyitja
    TapHandler {
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: function(point) {
            viewer.openContextMenu(point.position.x, point.position.y)
        }
    }

    // #465 4. pont: a felirat-bemásolás megerősítése (ld.
    // `onTextCopyCaptionRequested`)
    //: #1612: halasztva — a felirat-átvétel megerősítése csak akkor kell, ha
    //: a felhasználó tényleg átveszi a feliratot (mérve: 74 QObject).
    DeferredDialog {
        id: copyCaptionConfirmLoader
        sourceComponent: Component {
            ConfirmDialog {
                namePrefix: "copyCaptionConfirm"
                onConfirmed: editorPanel.textDraftContent = editorPanel.captionText
            }
        }
    }

    // #465: a retus/vörösszem visszavonása ADATOT dob el (nincs „Újra") —
    // az eredeti Picasa két külön szövegével kérdez rá. A döntés-kulcs
    // eszközönként külön, hogy a „Ne kérdezze meg újra" a másikra ne hasson.
    //: #1612: halasztva — a retus/vörösszem visszavonásának megerősítése csak
    //: akkor kell, ha a felhasználó ilyet vissza is von (mérve: 76 QObject).
    DeferredDialog {
        id: undoDataLossDialogLoader
        sourceComponent: Component {
            ConfirmDialog {
                objectName: "undoDataLossDialog"
                namePrefix: "undoDataLoss"
                title: qsTr("Undo")
                function askFor(key, text) { ask("undo-" + key, text) }
                onConfirmed: editController.undo()
            }
        }
    }

    // #2480: a MODÁLIS párbeszédek elhomályosító rétege. Az eredetiben ez
    // az `editpanel/modaldialogblur` (`editpanel.tre:1362`): a `root`
    // közvetlen gyereke (tehát a TELJES szerkesztő fölé kerül, nem a bal
    // panelen belülre), `m_scaleXY` (a teljes vászonra feszül) és
    // `m_hidden` (alapból rejtett — a modális párbeszéd kapcsolja be).
    //
    // A fájl UTOLSÓ gyereke, hogy a rétegrendben minden fölé kerüljön: a
    // bal panel, az előnézet és a felső sáv is alá esik. A Qt maga a
    // párbeszédet még ennél is fölé rajzolja (külön `QQuickOverlay`), tehát
    // a párbeszéd nem homályosodik el.
    //
    // ⚠️ A MÉRTÉK és a SZÍN a MI döntésünk: a `.tre` csak a réteg létét és
    // kiterjedését adja meg, a rajzot a `respack.yt` rétege adná — az nincs
    // kimérve. A választott érték a vászon-háttér 45%-a: elég ahhoz, hogy a
    // fókusz a párbeszédre kerüljön, de a szerkesztő tartalma átlátszik
    // (a felhasználónak látnia kell, mire válaszol).
    //
    // `enabled: false` — a réteg CSAK látvány: a modalitást a Qt biztosítja
    // (a párbeszéd `modal: true`), egy eseményt elnyelő réteg viszont a
    // párbeszéd bezárása utáni első kattintást is elvinné.
    Rectangle {
        objectName: "editorModalDialogBlur"
        anchors.fill: parent
        z: 1000
        enabled: false
        visible: editorPanel.modalDialogOpen
        color: Theme.canvasBg
        opacity: 0.45
    }

}

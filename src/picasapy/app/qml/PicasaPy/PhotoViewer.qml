import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import PicasaPy.Gpu

// Egyképes néző — a Picasa 3.9 "Megjelenítés és szerkesztés" képernyője
// alapján (#808080 háttér, felső filmszalag nyilakkal, bal eszközpanel;
// a szerkesztő-gombok a 2. fázisig szürkék). Enter/Jobbra: következő,
// Balra: előző, Esc: vissza a könyvtárba.
Rectangle {
    id: viewer

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
    readonly property bool gpuCapable: GraphicsInfo.api !== GraphicsInfo.Software
                                        && GraphicsInfo.api !== GraphicsInfo.Unknown
                                        && GraphicsInfo.api !== GraphicsInfo.Null
    readonly property bool gpuFinetuneEligible: viewer.gpuCapable
        && viewer.editCtl && viewer.editCtl.gpuPrefixSource !== ""

    property int currentIndex: -1
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
    // #422: a néző kontextusmenüjének „Törlés lemezről" tétele — a
    // megerősítő dialógus a Main.qml-ben él (FileOpsDialogs), ezért a
    // kérés jelként megy kifelé
    signal deleteRequested(string path)
    // #422: a mentés-szemantika parancsai a nézőből — a gazda (Main.qml)
    // ugyanazokat a megerősítéseket nyitja, mint a rácsban
    signal saveRequested(int row)
    signal revertRequested(int row)
    signal undoAllEditsRequested(int row)
    signal resetFacesRequested()

    // #192: a Tulajdonságok-panel a nézőben is — a könyvtár-nézet közös
    // kapcsolóját (Main.qml: window.propertiesPanelOpen) követi. A fő
    // ablakot a Window attached property adja, így a (forró) Main.qml-hez
    // nem kell hozzányúlni; önálló (teszt-)példányosításnál a kapcsoló
    // hiányzik → a panel rejtve marad.
    readonly property var appWindow: Window.window
    readonly property bool propertiesOpen: appWindow
        && appWindow.propertiesPanelOpen === true

    // #147: csak-olvasás arc-keret overlay — alapból KIKAPCSOLVA (a teljes
    // felismerés/Emberek-panel a #26-ban). currentFaces: FacesHelper.facesFor()
    // eredménye; a photosModel.revision a forgatás-kötés mintájára triggerel
    // újraértékelést; facesHelper hiányában (régi teszt-fixture) üres lista.
    property bool facesVisible: false
    function toggleFaces() { viewer.facesVisible = !viewer.facesVisible }
    // #26 (2. kör): arc-téglalap SZERKESZTŐ mód — rajzolás/átnevezés/
    // törlés a nézőben. A szerkesztés bekapcsolása egyben láthatóvá is
    // teszi a kereteket (nincs értelme vakon szerkeszteni).
    property bool facesEditMode: false
    function toggleFacesEdit() {
        viewer.facesEditMode = !viewer.facesEditMode
        if (viewer.facesEditMode) viewer.facesVisible = true
    }
    // az overlay minden sikeres írás (facesOverlay.edited) után növeli —
    // az ini-módosítást a photosModel/index NEM látja, ez a kényszerített
    // újraértékelés-kapcsoló a facesFor() friss lekérdezéséhez
    property int facesEditRevision: 0
    readonly property var currentFaces: (!viewer.facesVisible || !photosModel
                                          || currentIndex < 0
                                          || typeof facesHelper === "undefined"
                                          || !facesHelper)
        ? []
        : (photosModel.revision, viewer.facesEditRevision,
           facesHelper.facesFor(photosModel.filePathAt(currentIndex)))

    // -- zoom-állapotgép (#6): fit / 1:1 / tetszőleges -------------------
    // zoomFactor: 1.0 = illesztés (fit); a skála az illesztett mérethez
    // képest értendő. A pásztázás (pan) csak nagyításnál él.
    property real zoomFactor: 1.0
    property string zoomMode: "fit"      // "fit" | "actual" | "custom"
    property real panX: 0
    property real panY: 0

    function actualZoomFactor() {
        // 1:1 — a kép saját pixelei ↔ logikai pixelek (a betöltött,
        // sourceSize-plafonolt méret alapján)
        return photo.paintedWidth > 0
            ? photo.sourceSize.width / photo.paintedWidth : 1
    }
    function zoomFit() {
        zoomFactor = 1; zoomMode = "fit"; panX = 0; panY = 0
    }
    function zoomActual() {
        zoomFactor = Math.min(8, Math.max(0.25, actualZoomFactor()))
        zoomMode = "actual"
        clampPan()
    }
    function setZoom(factor) {
        var f = Math.min(8, Math.max(0.25, factor))
        zoomFactor = f
        if (Math.abs(f - 1) < 0.01) { zoomMode = "fit"; panX = 0; panY = 0 }
        else zoomMode = "custom"
        clampPan()
    }
    function wheelZoom(delta) {
        setZoom(zoomFactor * Math.pow(1.2, delta / 120))
    }
    // a kép széle ne szakadjon el a látótértől pásztázáskor
    function clampPan() {
        var w = (photo.iniSteps % 2 ? photo.paintedHeight
                                    : photo.paintedWidth) * zoomFactor
        var h = (photo.iniSteps % 2 ? photo.paintedWidth
                                    : photo.paintedHeight) * zoomFactor
        var maxX = Math.max(0, (w - photoArea.width) / 2)
        var maxY = Math.max(0, (h - photoArea.height) / 2)
        panX = Math.max(-maxX, Math.min(maxX, panX))
        panY = Math.max(-maxY, Math.min(maxY, panY))
    }

    function show(index) { currentIndex = index; forceActiveFocus() }

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

    // a művelet-kulcs magyar gombfelirata (Visszavonás: <művelet>, #59)
    function toolLabel(action) {
        switch (action) {
        case "crop": return qsTr("Crop")
        case "tilt": return qsTr("Straighten")
        case "redeye": return qsTr("Redeye")
        case "retouch": return qsTr("Retouch")
        case "text": return qsTr("Text")
        case "enhance": return qsTr("I'm Feeling Lucky")
        case "autolight": return qsTr("Auto Contrast")
        case "autocolor": return qsTr("Auto Color")
        case "finetune": return qsTr("Fine Tuning")
        // effekt-kulcsok (#20): a lánc bármely elemeként visszavonható
        case "sepia": return qsTr("Sepia")
        case "bw": return qsTr("B&W")
        case "warm": return qsTr("Warmify")
        case "grain2": return qsTr("Film Grain")
        case "tint": return qsTr("Tint")
        case "sat": return qsTr("Saturation")
        case "radblur": return qsTr("Soft Focus")
        case "glow2": return qsTr("Glow")
        case "ansel": return qsTr("Filtered B&W")
        case "radsat": return qsTr("Focal Saturation")
        case "dir_tint": return qsTr("Graduated Tint")
        // ismeretlen (pl. valódi Picasa által írt) szűrő: a nyers név is
        // informatívabb, mint az üres felirat
        default: return action
        }
    }

    // -- szerkesztés (#19): EditController-életciklus --------------------
    // A nézőbe lépés = szerkesztési munkamenet az aktuális képre; kilépéskor
    // a munkamenet zárul. A panel kapcsoló-állapotait az EditController
    // igazságforrásából szinkronizáljuk (a kötést a panel belső átírása
    // megtörné, ezért imperatív sync a toolsChanged-re).
    function beginEditCurrent() {
        if (!(visible && currentIndex >= 0 && photosModel)) return
        // #218: a viewer.isCurrentVideo egy kötött property — a currentIndex
        // váltásakor NEM garantált, hogy már újraértékelődött, mire ez a
        // (szintén a currentIndexChanged-re futó) imperatív függvény lefut,
        // ezért a modellt itt KÖZVETLENÜL kérdezzük le (mindig friss),
        // nem a cache-elt property-t
        if (photosModel.isVideoAt(currentIndex)) {
            // videón nincs képszerkesztés (#14) — az előző kép nyitott
            // munkamenete záruljon, ne lógjon át az előnézete
            editController.endEdit()
            return
        }
        editController.beginEdit(photosModel.idAt(currentIndex),
                                 photosModel.filePathAt(currentIndex))
    }
    // Döntés-csúszka szinkronja a mentett tilt-értékkel (#131): a value
    // beállítását elnyomjuk, hogy az onValueChanged NE váltson ki
    // previewTilt-et — a szinkron csak a csúszkát mozgatja, az előnézet
    // már a beginEditCurrent()/_register_preview() óta helyes.
    function syncTiltSlider() {
        tiltSlider.suppressPreview = true
        tiltSlider.value = editController.tiltParam
        tiltSlider.suppressPreview = false
        // #448: a Kiegyenesítés-figyelmeztetés a vágó-panelen — a
        // tiltParam a mentett döntés-paraméter, 0.0 = nincs aktív tilt
        editorPanel.straightenActive = editController.tiltParam !== 0
    }
    function syncPanelFromController() {
        // #445: a `redeyeActive` a Vágás/Retusálás mintájára ESZKÖZ-nyitást
        // jelent (nem a `redeye` réteg meglétét) — ezért NEM a
        // controller.redeyeActive tükre; azt onnan felülírni becsukná/
        // kinyitná a panelt a mentett lánc alapján.
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
        editorPanel.fontFamilyCatalogue = editController.textFontFamilies
        editorPanel.textFontFamily = editController.textFontFamily
        editorPanel.textFontScale = editController.textFontScale
        editorPanel.textBold = editController.textBold
        editorPanel.textItalic = editController.textItalic
        editorPanel.textUnderline = editController.textUnderline
        editorPanel.textAlign = editController.textAlign
    }
    onVisibleChanged: {
        if (visible) {
            zoomFit()   // #6: minden belépés illesztett nézetben indul
            beginEditCurrent()
        } else {
            // a cropActive/retouchActive/textActive lenullázása ELŐBB (még
            // aktív szerkesztés alatt) fut, hogy az onXActiveChanged->
            // exitXTool() még érvényes munkameneten hívódjon; utána zárja
            // az endEdit()
            editorPanel.cropActive = false
            editorPanel.tiltActive = false
            editorPanel.retouchActive = false
            editorPanel.textActive = false
            editorPanel.redeyeActive = false
            editController.endEdit()
        }
    }
    onCurrentIndexChanged: {
        if (visible) {
            zoomFit()   // #6: lapozáskor vissza illesztett nézetbe
            beginEditCurrent()
            // lapozáskor a csúszka az ÚJ kép mentett tilt-értékére áll —
            // suppressPreview miatt ez nem írja felül a preview-t (#131)
            syncTiltSlider()
            // ugyanígy a Finomhangolás-csúszkák is az új kép mentett
            // értékeire állnak (#20)
            editorPanel.syncFinetuneSliders()
            if (editorPanel.cropActive) {
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
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
        function onCropActiveChanged() {
            if (editorPanel.cropActive) {
                viewer.zoomFit()   // #6: a vágó-overlay illesztett nézetet vár
                editController.enterCropTool()
                cropOverlay.loadSelection(editController.cropSelection)
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
    // határán a jelenlegi indexet adja vissza, tehát nem lép tovább.
    function next() {
        if (!photosModel) return
        currentIndex = photosModel.folderNeighbor(currentIndex, 1)
    }
    function previous() {
        if (!photosModel) return
        currentIndex = photosModel.folderNeighbor(currentIndex, -1)
    }
    // a ◀/▶ gombok (és Keys.onLeft/Right) enabled-je is a mappahatárt
    // tükrözi: nincs hova lépni, ha a folderNeighbor helyben marad
    function hasNext() {
        return photosModel
            ? photosModel.folderNeighbor(currentIndex, 1) !== currentIndex
            : false
    }
    function hasPrevious() {
        return photosModel
            ? photosModel.folderNeighbor(currentIndex, -1) !== currentIndex
            : false
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
        if (editorPanel.retouchActive && editorPanel.retouchPatchPending)
            editController.cancelRetouchPatch()
        else if (editorPanel.cropActive)
            editorPanel.cropCancelRequested()
        else
            viewer.closed()
    }
    Keys.onEscapePressed: viewer.handleEscape()
    Keys.onRightPressed: next()
    Keys.onReturnPressed: next()
    Keys.onLeftPressed: previous()
    // szóköz: videónál lejátszás/szünet (#14) — Picasa-viselkedés
    Keys.onSpacePressed: {
        if (viewer.isCurrentVideo && videoLoader.item)
            videoLoader.item.togglePlayback()
    }
    // F: arc-keretek be/ki (#147) — szövegmezőben (pl. felirat) a saját
    // Keys-kezelés (gépelés) már elfogadja, ide nem buborékol.
    // Shift+F: arc-SZERKESZTŐ mód be/ki (#26, 2. kör).
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_F && event.modifiers === Qt.NoModifier) {
            viewer.toggleFaces()
            event.accepted = true
        } else if (event.key === Qt.Key_F && event.modifiers === Qt.ShiftModifier) {
            viewer.toggleFacesEdit()
            event.accepted = true
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // felső sáv: vissza gomb + filmszalag nyilakkal
        Rectangle {
            id: viewerTopBar
            Layout.fillWidth: true
            height: 46
            color: Theme.chromeBg
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8; anchors.rightMargin: 8
                spacing: 8
                PicasaButton {
                    text: "◀  " + qsTr("Back to Library")
                    font.pixelSize: Theme.fontSize
                    onClicked: viewer.closed()
                }
                Item { Layout.fillWidth: true }
                PicasaButton {
                    objectName: "viewerPlayButton"
                    text: "▶ " + qsTr("Play")
                    font.pixelSize: Theme.fontSize
                    onClicked: viewer.playRequested()
                }
                // #6: A/AB/AA összehasonlító nézetek — placeholder (a
                // szerkesztő-összevetés a 2. fázisban élesedik)
                PicasaButton {
                    objectName: "compareButtonA"
                    text: "A"; enabled: false
                    Layout.preferredWidth: 28
                }
                PicasaButton {
                    objectName: "compareButtonAB"
                    text: "AB"; enabled: false
                    Layout.preferredWidth: 32
                }
                PicasaButton {
                    objectName: "compareButtonAA"
                    text: "AA"; enabled: false
                    Layout.preferredWidth: 32
                }
                PicasaButton {
                    objectName: "viewerPrevButton"
                    text: "◀"; onClicked: viewer.previous()
                    enabled: viewer.hasPrevious()
                    Layout.preferredWidth: 30
                }
                ListView {
                    id: filmstrip
                    Layout.preferredWidth: Math.min(7, viewer.photoCount) * 44
                    Layout.preferredHeight: 38
                    orientation: ListView.Horizontal
                    model: viewer.photosModel
                    currentIndex: viewer.currentIndex
                    highlightMoveDuration: 100
                    clip: true
                    delegate: Rectangle {
                        required property string thumbUrl
                        required property int index
                        width: 42; height: 38
                        color: index === viewer.currentIndex
                               ? Theme.thumbSelection : "transparent"
                        Image {
                            anchors.fill: parent
                            anchors.margins: 2
                            source: thumbUrl
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: Qt.platform.pluginName !== "offscreen"
                        }
                        TapHandler {
                            onTapped: viewer.currentIndex = index
                        }
                    }
                }
                PicasaButton {
                    objectName: "viewerNextButton"
                    text: "▶"; onClicked: viewer.next()
                    enabled: viewer.hasNext()
                    Layout.preferredWidth: 30
                }
                Item { Layout.fillWidth: true }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // bal eszközpanel — Gyakori javítások élesben (#19); a
            // Retusálás/Szöveg és a finomhangolás a #20-ban élesedik
            Rectangle {
                // #411: az EditorPanel.qml implicitWidth-ével összhangban —
                // FIX 280px, nem ablakarányos (ld. az ottani kommentet)
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                // #641: itt NINCS `Layout.minimumHeight`. A #628 azt tette ide,
                // de az visszafelé sült el: a doboz nem zsugorodott a cellára,
                // hanem TÚLNYÚLT rajta, és a panel aljához igazodó
                // Visszavonás/Újra sor kicsúszott a képernyőről. A „mindig
                // elfér" garanciát az ABLAK minimális magassága adja
                // (`Main.qml`, a `viewer.requiredHeight`-ből) — ha az mégsem
                // tartható, a doboz zsugorodik, és a fül TARTALMA veszít, nem
                // a gombsor.
                color: Theme.chromeBg

                EditorPanel {
                    id: editorPanel
                    objectName: "viewerEditorPanel"
                    // videónál a szerkesztő-eszközök nem értelmezettek (#14)
                    enabled: !viewer.isCurrentVideo
                    // #628: a panel a RENDELKEZÉSRE ÁLLÓ magasságot kapja.
                    // Korábban itt fix 420 képpont állt, akármekkora az
                    // ablak — a 3. fül 12 bélyegképes csempéje (3×4, ≈450
                    // px) ebbe soha nem fért bele, ezért lett a görgetés az
                    // alapállapot, és ezért lógott rá a gombsor a
                    // csempékre. A szülő `Layout.fillHeight: true`, tehát a
                    // hely rendelkezésre áll.
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left; anchors.right: parent.right
                    imageAspect: photo.paintedHeight > 0
                                 ? photo.paintedWidth / photo.paintedHeight
                                 : 4 / 3
                    // Visszavonás/Újra — a controller undo-verméből (#59)
                    // #305: null-őr
                    undoAvailable: viewer.editCtl ? viewer.editCtl.canUndo : false
                    undoLabel: viewer.editCtl && viewer.editCtl.canUndo
                               ? qsTr("Undo") + ": "
                                 + viewer.toolLabel(viewer.editCtl.undoAction)
                               : qsTr("Undo")
                    redoAvailable: viewer.editCtl ? viewer.editCtl.canRedo : false
                    redoLabel: viewer.editCtl && viewer.editCtl.canRedo
                               ? qsTr("Redo") + ": "
                                 + viewer.toolLabel(viewer.editCtl.redoAction)
                               : qsTr("Redo")
                    // Finomhangolás (#20): a mentett értékek a kontrollerből —
                    // a syncFinetuneSliders() ezekből tölti a csúszkákat
                    fillLight: viewer.editCtl ? viewer.editCtl.fillLight : 0
                    highlights: viewer.editCtl ? viewer.editCtl.highlights : 0
                    shadows: viewer.editCtl ? viewer.editCtl.shadows : 0
                    colorTemp: viewer.editCtl ? viewer.editCtl.colorTemp : 0
                    // GPU élő-előnézet (#22): amíg a lánc GPU-alkalmas ÉS
                    // van RHI, a húzás a LUT-only gyors utat hívja (a
                    // `GpuPointFilterPreview` réteg jelenik meg a `photo`
                    // fölött) — máskülönben (nincs GPU, vagy a lánc nem
                    // GPU-alkalmas) a rendes, teljes CPU-előnézet fut,
                    // változatlanul.
                    onFinetunePreview: (f, h, s, t) => {
                        // #551: a Derítőfény MÉRT modellje a pixel
                        // VILÁGOSSÁGÁTÓL függ, tehát nem csatornánkénti
                        // LUT — a GPU pontonkénti útja csak f === 0 esetén
                        // adja pontosan ugyanazt a képet, mint a CPU.
                        viewer.gpuFinetuneActive = true
                        viewer.gpuFinetunePointSafe = (f === 0)
                        if (viewer.gpuFinetuneEligible && f === 0)
                            editController.previewFinetuneGpu(f, h, s, t)
                        else
                            editController.previewFinetune(f, h, s, t)
                    }
                    onFinetuneCommit: (f, h, s, t) => {
                        // a húzás végén MINDIG a normál CPU-út menti — az
                        // igazságforrás sosem a GPU-réteg (ld. #22 jegy)
                        viewer.gpuFinetuneActive = false
                        viewer.gpuFinetunePointSafe = true
                        editController.setFinetune(f, h, s, t)
                    }
                    onEffectRequested: (name) => editController.applyEffect(name)
                    // #551: a szín-varázspálca a finetune2 p4 mezőjét írja
                    onColorWandRequested: editController.applyColorWand()
                    onToolActivated: function(tool) {
                        // crop/tilt/retouch/text helyi mód (overlay/
                        // csúszka/kattintás-puffer); a többi azonnali
                        // ini-művelet az EditControlleren át
                        if (tool === "tilt") {
                            // eszköz-nyitáskor a csúszka a MENTETT
                            // tilt-értékről induljon, ne 0-ról (#131)
                            if (editorPanel.tiltActive)
                                viewer.syncTiltSlider()
                        } else if (tool === "crop" || tool === "retouch"
                                   || tool === "text" || tool === "redeye") {
                            // az enter/exit a Connections{target: editorPanel}
                            // blokk onXActiveChanged kezelőiben történik
                        } else {
                            editController.toggleTool(tool)
                        }
                    }
                    // #465: a retus és a vörösszem RÉGIÓ-ADATOT hordoz, és a
                    // visszavonás eldobja — az „Újra" nem hozza vissza.
                    // Az eredeti Picasa ezért külön rákérdez
                    // (IDS_CONFIRM_UNDO_RETOUCH / IDS_CONFIRM_UNDO_REDEYE).
                    onUndoRequested: {
                        var action = editController.undoAction
                        if (action === "retouch")
                            undoDataLossDialog.askFor("retouch", qsTr(
                                "Retouch fixes cannot be recovered with redo."
                                + " Are you sure you want to undo?"))
                        else if (action === "redeye")
                            undoDataLossDialog.askFor("redeye", qsTr(
                                "Redeye fixes cannot be recovered with redo."
                                + " Are you sure you want to undo?"))
                        else
                            editController.undo()
                    }
                    onRedoRequested: editController.redo()
                    onCropRotateRequested: {
                        // rögzített aránynál a fekvő↔álló kapcsoló forgat
                        // (a kijelölés az arány-követéssel formálódik át);
                        // kézi aránynál közvetlenül a kijelölést forgatjuk
                        if (editorPanel.currentAspect > 0)
                            editorPanel.aspectRotated =
                                !editorPanel.aspectRotated
                        else
                            cropOverlay.swapSelectionOrientation()
                    }
                    // arány-választás/Forgatás: a meglévő kijelölés kövesse,
                    // és a #448-as javaslatok is a KIVÁLASZTOTT arányban
                    // szülessenek (egyetlen kezelő — a QML-ben nem lehet
                    // két azonos nevű jel-kezelő ugyanazon az objektumon)
                    onCurrentAspectChanged: {
                        if (cropOverlay.hasSelection
                            && editorPanel.currentAspect > 0)
                            cropOverlay.applyAspect(editorPanel.currentAspect)
                        if (viewer.editCtl)
                            viewer.editCtl.setCropAspect(editorPanel.currentAspect)
                    }
                    onQuickCropRequested: (kind) => cropOverlay.selectPreset(kind)
                    onCropPreviewHold: (held) => cropOverlay.previewHold = held
                    onCropResetRequested: cropOverlay.resetSelection()
                    // #448: a három automatikus javaslat — a választott
                    // téglalap a KIJELÖLÉSBE kerül (nem alkalmazódik
                    // azonnal), hogy a felhasználó még igazíthasson rajta,
                    // és az Alkalmaz/Mégse útja változatlan maradjon.
                    cropSuggestions: viewer.editCtl
                        ? viewer.editCtl.cropSuggestions : []
                    onCropSuggestionChosen: (x, y, w, h) =>
                        cropOverlay.loadSelection(
                            { "x": x, "y": y, "width": w, "height": h })
                    onCropApplyRequested: viewer.applyCrop(false)
                    onCropCancelRequested: {
                        cropOverlay.resetSelection()
                        editorPanel.cropActive = false
                    }
                    // #148/#445: a retusálás pufferének mérete/az Alkalmaz-
                    // gomb engedélyezettsége, a félbehagyott folt ("Refining…")
                    // és a patch-enkénti Undo/Redo/ecsetméret a kontrollerből
                    retouchRegionCount: viewer.editCtl
                        ? viewer.editCtl.retouchPendingCount : 0
                    retouchPatchPending: viewer.editCtl
                        ? viewer.editCtl.retouchPatchPending : false
                    canUndoPatch: viewer.editCtl ? viewer.editCtl.canUndoPatch : false
                    canRedoPatch: viewer.editCtl ? viewer.editCtl.canRedoPatch : false
                    brushSize: viewer.editCtl ? viewer.editCtl.brushSize : 20
                    onBrushSizeEdited: (value) => editController.setBrushSize(value)
                    onRetouchUndoPatchRequested: editController.undoPatch()
                    onRetouchRedoPatchRequested: editController.redoPatch()
                    onRetouchResetRequested: editController.resetPatches()
                    onRetouchApplyRequested: {
                        editController.applyRetouch()
                        editorPanel.retouchActive = false
                    }
                    onRetouchCancelRequested: editorPanel.retouchActive = false
                    // #445: Vörösszem — a kézi régió-puffer és az automatika
                    // találat-száma a kontrollerből
                    redeyeRegionCount: viewer.editCtl
                        ? viewer.editCtl.redeyeRegionCount : 0
                    canUndoRedeyeRegion: viewer.editCtl
                        ? viewer.editCtl.canUndoRedeyeRegion : false
                    redeyeFoundCount: viewer.editCtl
                        ? viewer.editCtl.redeyeFoundCount : -1
                    onRedeyeAutoRequested: editController.runRedeyeAuto()
                    onRedeyeUndoRegionRequested: editController.undoRedeyeRegion()
                    onRedeyeResetRequested: editController.resetRedeyeRegions()
                    onRedeyeApplyRequested: {
                        editController.applyRedeye()
                        editorPanel.redeyeActive = false
                    }
                    onRedeyeCancelRequested: editorPanel.redeyeActive = false
                    // #148: a szöveg-eszköz Alkalmaz-gombja csak akkor
                    // engedélyezett, ha már van kattintott pozíció
                    textPlacementPending: viewer.editCtl
                        ? viewer.editCtl.textHasPlacement : false
                    // #450: "Copy Caption" gomb — a kép model.revision-re
                    // is frissülő mentett feliratát tükrözi (a captionField
                    // mintáját követve fent)
                    captionText: viewer.photosModel
                        ? (viewer.photosModel.revision,
                           viewer.photosModel.captionAt(viewer.currentIndex))
                        : ""
                    onTextDraftEdited: (content) => editController.setTextDraft(content)
                    onTextApplyRequested: {
                        editController.applyText()
                        editorPanel.textActive = false
                    }
                    onTextCancelRequested: editorPanel.textActive = false
                    // #450: a kép feliratát tölti a szövegmezőbe
                    // #465 4. pont: a felirat BEMÁSOLÁSA felülírja a
                    // szövegmező tartalmát — az eredeti Picasa erre
                    // kimondottan figyelmeztet („(This operation is not
                    // undoable)"), mert a beírt szöveg nem szerezhető
                    // vissza. Üres mezőnél nincs mit elveszíteni, ott
                    // szándékosan NEM kérdezünk (a jegy elve: csak ott
                    // ijesztgess, ahol tényleg végleges).
                    onTextCopyCaptionRequested: {
                        if (editorPanel.textDraftContent.length === 0) {
                            editorPanel.textDraftContent = editorPanel.captionText
                            return
                        }
                        copyCaptionConfirm.ask(
                            "copyCaptionOverwrite",
                            qsTr("The caption will replace the text you have "
                                 + "typed. (This operation is not undoable)"))
                    }
                    // #450: az összes (ma: az egyetlen) szövegelem törlése —
                    // a meglévő clearText útvonalon, a szerkesztőeszköz is zárul
                    onTextRemoveAllRequested: {
                        editController.clearText()
                        editorPanel.textDraftContent = ""
                        editorPanel.textActive = false
                    }
                    // #464: a pipetta be/ki kapcsolása — a mintavétel a
                    // `neutralPickArea`-ban történik (a kép fölött)
                    onNeutralPickerToggled: editorPanel.neutralPickerActive =
                        !editorPanel.neutralPickerActive
                    onTextFillColorEdited: (hex) => editController.setTextFillColor(hex)
                    onTextOutlineColorEdited: (hex) => editController.setTextOutlineColor(hex)
                    onTextOutlineThicknessEdited: (value) =>
                        editController.setTextOutlineThickness(Math.round(value))
                    onTextFillEnabledEdited: (value) => editController.setTextFillEnabled(value)
                    onTextOpacityEdited: (value) => editController.setTextOpacity(value)
                    // #450 (2. lépcső): tipográfia — az ÉRTÉKEKET a
                    // syncEditorPanel() tölti (a többi szöveg-stílus
                    // mintájára), itt csak a jelzések mennek vissza
                    onTextFontFamilyEdited: (key) =>
                        editController.setTextFontFamily(key)
                    onTextFontScaleEdited: (value) =>
                        editController.setTextFontScale(value)
                    onTextBoldEdited: (value) => editController.setTextBold(value)
                    onTextItalicEdited: (value) => editController.setTextItalic(value)
                    onTextUnderlineEdited: (value) =>
                        editController.setTextUnderline(value)
                    onTextAlignEdited: (value) => editController.setTextAlign(value)
                }

                ColumnLayout {
                    anchors.top: editorPanel.bottom
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.margins: 10
                    spacing: 6
                    Label {
                        visible: editorPanel.tiltActive && editorPanel.activeTab === 0
                        text: qsTr("Straighten")
                        font.pixelSize: Theme.fontSize
                        color: Theme.textGray
                    }
                    // döntés-csúszka: −1..1 Picasa-egység (±11,5°); húzás
                    // közben élő előnézet (previewTilt, nincs ini-mentés,
                    // #72), elengedéskor ír + tol undo-lépést (setTilt)
                    PicasaSlider {
                        id: tiltSlider
                        objectName: "tiltSlider"
                        visible: editorPanel.tiltActive && editorPanel.activeTab === 0
                        from: -1; to: 1; value: 0
                        // programozott szinkronnál (nyitás/lapozás) NEM
                        // váltunk ki previewTilt-et — az felülírná a
                        // mentett érték előnézetét (#131)
                        property bool suppressPreview: false
                        Layout.fillWidth: true
                        onValueChanged: if (editorPanel.tiltActive && !suppressPreview)
                                            editController.previewTilt(value)
                        onPressedChanged: if (!pressed && editorPanel.tiltActive)
                                              editController.setTilt(value)
                    }
                }
                // élő RGB-hisztogram + fényképezőgép-adat sor (#25): a
                // korábbi placeholder-doboz élesítve — HistogramBox.qml
                HistogramBox {
                    objectName: "viewerHistogramBox"
                    anchors.bottom: parent.bottom
                    anchors.left: parent.left; anchors.right: parent.right
                    anchors.margins: 10
                    height: 150
                    // #305: null-őr
                    histogramData: viewer.editCtl
                        ? viewer.editCtl.histogram : ({ r: [], g: [], b: [] })
                    cameraSummary: viewer.editCtl ? viewer.editCtl.cameraSummary : ""
                }
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

                Item {
                    id: photoArea
                    objectName: "viewerPhotoArea"
                    anchors.fill: parent
                    anchors.margins: 14
                    anchors.bottomMargin: 30
                    // #6 utójavítás (felhasználói hibajelzés): a nagyított
                    // kép NE lógjon ki a képterületből a bal panel / a
                    // felső sáv / a felirat-sor fölé — a QML alapból nem
                    // vág, a zoomhoz kötelező a clip
                    clip: true

                    Image {
                        id: photo
                        objectName: "viewerImage"
                        // videónál a fotó-Image üres és rejtett (#14) — a
                        // videofájlt nem próbáljuk képként dekódolni
                        visible: !viewer.isCurrentVideo
                        // a model.revision referencia miatt a kötés minden
                        // modell-frissítésnél újraértékelődik
                        readonly property int iniSteps: viewer.photosModel
                            ? (viewer.photosModel.revision,
                               viewer.photosModel.rotateAt(viewer.currentIndex))
                            : 0
                        anchors.centerIn: parent
                        // #6: zoom + pásztázás — a skála az illesztett
                        // mérethez képest, az eltolás a pan-állapotból
                        anchors.horizontalCenterOffset: viewer.panX
                        anchors.verticalCenterOffset: viewer.panY
                        scale: viewer.zoomFactor
                        transformOrigin: Item.Center
                        // 90°/270°-nál a befoglaló doboz oldalai cserélődnek
                        width: iniSteps % 2 ? photoArea.height : photoArea.width
                        height: iniSteps % 2 ? photoArea.width : photoArea.height
                        rotation: iniSteps * 90
                        // nyitott szerkesztésnél a filters= láncot alkalmazó
                        // editpreview provider rendereli a képet (?rev=
                        // cache-buster minden módosításnál)
                        // #305: null-őr
                        source: viewer.isCurrentVideo ? ""
                                : (viewer.editCtl && viewer.editCtl.previewSource !== ""
                                   ? viewer.editCtl.previewSource
                                   : viewer.urlAt(viewer.currentIndex))
                        fillMode: Image.PreserveAspectFit
                        // #53: offscreen (teszt) platformon szinkron betöltés —
                        // itt reprodukálódott a GIL-deadlock (a lapozás
                        // setProperty-je vs. az image-provider szál). Szinkron
                        // betöltésnél nincs provider-szál, így nincs holtpont;
                        // produkcióban marad az async.
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                        autoTransform: true   // EXIF-orientáció
                        sourceSize.width: 2560
                    }

                    // GPU élő-előnézet (#22): a `photo` FÖLÖTT, csak akkor
                    // látható, ha `gpuFinetuneActive && gpuFinetuneEligible`
                    // (ld. a fenti property-k docsztringjét). A két rejtett
                    // `Image` a forrás (a finetune2 ELŐTTI kép) és a
                    // 256×1 LUT-textúra betöltője — `smooth: false` a
                    // LUT-on kötelező (egzakt indexelés, ld.
                    // GpuPointFilterPreview.qml). GPU-képtelen
                    // futtatókörnyezetben (`gpuFinetuneEligible` mindig
                    // false) ez a réteg SOSEM válik láthatóvá — a `photo`
                    // Image alatta változatlanul a rendes CPU-előnézetet
                    // mutatja, semmi nem törhet emiatt CI-ban.
                    Image {
                        id: gpuPrefixImage
                        objectName: "gpuPrefixImage"
                        visible: false
                        source: viewer.gpuFinetuneEligible
                                ? viewer.editCtl.gpuPrefixSource : ""
                        asynchronous: Qt.platform.pluginName !== "offscreen"
                        autoTransform: true
                        sourceSize.width: 2560
                    }
                    Image {
                        id: gpuLutImage
                        objectName: "gpuLutImage"
                        visible: false
                        smooth: false
                        cache: false
                        source: viewer.gpuFinetuneEligible
                                ? viewer.editCtl.gpuLutSource : ""
                    }
                    GpuPointFilterPreview {
                        id: gpuFinetunePreview
                        objectName: "gpuFinetunePreview"
                        // #415: NEM `anchors.fill: photo` — az a `photo`
                        // TELJES befoglaló dobozára igazítana (a
                        // rendelkezésre álló terület, `photo.width`/
                        // `photo.height`), nem a `PreserveAspectFit`
                        // fillMode által ténylegesen kirajzolt, letterboxolt
                        // téglalapra. Álló képnél a doboz szélesebb, mint a
                        // kirajzolt kép — a húzás alatt ez a réteg (a `photo`
                        // fölött) a doboz teljes szélességére nyúlt, majd
                        // elrejtésekor (elengedéskor) a helyesen illesztett
                        // `photo` vált újra láthatóvá: ez okozta a
                        // bejelentett "kiugrást". A helyes geometria a
                        // `cropOverlay`/`facesOverlay` mintáját követi —
                        // `paintedWidth`/`paintedHeight`, középre igazítva.
                        x: photo.x + (photo.width - photo.paintedWidth) / 2
                        y: photo.y + (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        rotation: photo.rotation
                        scale: photo.scale
                        transformOrigin: Item.Center
                        // #402: shader-hibánál (shaderOk=false) némán a
                        // CPU-előnézet marad
                        visible: viewer.gpuFinetuneActive && viewer.gpuFinetuneEligible
                                 && viewer.gpuFinetunePointSafe
                                 && gpuFinetunePreview.shaderOk
                        sourceItem: gpuPrefixImage
                        lutItem: gpuLutImage
                        satGain: 1.0
                        bwMix: 0.0
                    }

                    // #14: videó-lejátszó — csak videónál töltődik be, így
                    // a Qt Multimedia hiánya a fotó-nézetet nem érinti
                    Loader {
                        id: videoLoader
                        objectName: "videoLoader"
                        anchors.fill: parent
                        active: viewer.visible && viewer.isCurrentVideo
                        source: "VideoPlayerView.qml"
                    }
                    Binding {
                        target: videoLoader.item
                        property: "source"
                        value: viewer.urlAt(viewer.currentIndex)
                        when: videoLoader.status === Loader.Ready
                              && viewer.isCurrentVideo
                    }
                    Text {
                        objectName: "videoUnavailableText"
                        visible: viewer.isCurrentVideo
                                 && videoLoader.status === Loader.Error
                        anchors.centerIn: parent
                        text: qsTr("Video playback requires the Qt Multimedia module.")
                        color: "#e8e8e8"
                        font.pixelSize: Theme.fontSize
                    }

                    // vágó-overlay a kép TÉNYLEGESEN kirajzolt (letterbox
                    // nélküli) területén. Enter: elfogad + következő kép a
                    // vágó-mód megtartásával (sorozat-vágás, UX-alapelv 1);
                    // Esc: kilép a vágásból. MVP-korlát: ini-forgatott
                    // (rotate=) képnél a koordináták a megjelenített térben
                    // értendők — a forgatás+vágás kombináció a #21-ben pontosodik.
                    CropOverlay {
                        id: cropOverlay
                        parent: photo
                        visible: editorPanel.cropActive
                        aspectRatio: editorPanel.currentAspect
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        onVisibleChanged: {
                            if (visible) forceActiveFocus()
                            else viewer.forceActiveFocus()
                        }
                        // Enter-flow: elfogad ÉS következő kép, a vágó-mód
                        // megtartásával (sorozat-vágás, UX-alapelv 1)
                        onAccepted: function(r) {
                            viewer.applyCrop(true)
                            if (visible) forceActiveFocus()
                        }
                        onCancelled: {
                            cropOverlay.resetSelection()
                            editorPanel.cropActive = false
                        }
                    }

                    // #147/#26: a mentett arc-régiók a kép kirajzolt
                    // (letterbox nélküli) területén — a cropOverlay
                    // mintájára. Szerkesztő módban (facesEditMode) itt
                    // rajzolható/nevezhető/törölhető egy régió.
                    FacesOverlay {
                        id: facesOverlay
                        parent: photo
                        visible: viewer.facesVisible && !editorPanel.cropActive
                                 && !viewer.isCurrentVideo
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        faces: viewer.currentFaces
                        editMode: viewer.facesEditMode
                        imagePath: viewer.photosModel && viewer.currentIndex >= 0
                            ? viewer.photosModel.filePathAt(viewer.currentIndex) : ""
                        onEdited: viewer.facesEditRevision += 1
                    }

                    // #445: a retusálás a Picasa súgószövege szerinti,
                    // KÉTKATTINTÁSOS, irányított klónozás — 1. kattintás a
                    // CÉL kijelölése, egérmozgatás a FORRÁS élő előnézete,
                    // 2. kattintás véglegesíti. `Ctrl`+húzás eközben a
                    // meglévő nagyítás-pásztázó (`viewer.panX`/`panY`/
                    // `clampPan()`, ld. lent a `viewerPanArea`-t) állapotára
                    // ül rá, hogy zoomolt nézetben kattintás nélkül lehessen
                    // odébb húzni a képet.
                    // #464: a „semleges szín" pipetta — amíg aktív, a képre
                    // kattintás színmintát vesz (nem navigál). A kattintás
                    // helyét a KIRAJZOLT képhez képest normálva adjuk át, így
                    // a nagyítástól/illesztéstől független.
                    MouseArea {
                        id: neutralPickArea
                        objectName: "neutralPickArea"
                        parent: photo
                        visible: editorPanel.neutralPickerActive
                        enabled: editorPanel.neutralPickerActive
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        cursorShape: Qt.CrossCursor
                        onClicked: function(mouse) {
                            if (!editController) return
                            editController.pickNeutralColor(
                                mouse.x / Math.max(1, width),
                                mouse.y / Math.max(1, height))
                            editorPanel.neutralPickerActive = false
                        }
                    }

                    MouseArea {
                        id: retouchClickArea
                        objectName: "retouchClickArea"
                        parent: photo
                        visible: editorPanel.retouchActive
                        enabled: editorPanel.retouchActive
                        hoverEnabled: true
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        cursorShape: Qt.CrossCursor
                        property bool ctrlPanning: false
                        property real panLastX: 0
                        property real panLastY: 0
                        onPressed: function(mouse) {
                            if (mouse.modifiers & Qt.ControlModifier) {
                                ctrlPanning = true
                                panLastX = mouse.x; panLastY = mouse.y
                            }
                        }
                        onPositionChanged: function(mouse) {
                            if (width <= 0 || height <= 0) return
                            if (ctrlPanning) {
                                viewer.panX += mouse.x - panLastX
                                viewer.panY += mouse.y - panLastY
                                panLastX = mouse.x; panLastY = mouse.y
                                viewer.clampPan()
                                return
                            }
                            if (editController.retouchPatchPending)
                                editController.previewRetouchSource(
                                    mouse.x / width, mouse.y / height)
                        }
                        onReleased: function(mouse) { ctrlPanning = false }
                        onClicked: function(mouse) {
                            if (width <= 0 || height <= 0) return
                            // Ctrl+húzás UTÁNi felengedés is "clicked"-et vált
                            // ki QML-ben — ez NEM patch-kattintás
                            if (mouse.modifiers & Qt.ControlModifier) return
                            if (editController.retouchPatchPending)
                                editController.commitRetouchPatch(
                                    mouse.x / width, mouse.y / height)
                            else
                                editController.beginRetouchPatch(
                                    mouse.x / width, mouse.y / height)
                        }
                    }
                    // #445: Vörösszem — kézi kijelölés téglalap-húzással
                    // („Click, hold, and drag the mouse around each eye
                    // separately to select it. A selection box appears over
                    // the area."). A már felvett régiókat a kontroller adja
                    // vissza normált [0..1] alakban, ezért a nagyítástól/
                    // illesztéstől függetlenül rajzolhatók. A
                    // `redeyeHideOutlines` a jegy „Preview changes without
                    // square outlines" jelölőnégyzete: csak a RAJZOT tünteti
                    // el, a javítást nem.
                    Item {
                        id: redeyeOverlay
                        objectName: "redeyeOverlay"
                        parent: photo
                        visible: editorPanel.redeyeActive
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight

                        Repeater {
                            model: editorPanel.redeyeHideOutlines
                                   ? []
                                   : (viewer.editCtl
                                      ? viewer.editCtl.redeyeRegions : [])
                            delegate: Rectangle {
                                required property var modelData
                                x: modelData.x * redeyeOverlay.width
                                y: modelData.y * redeyeOverlay.height
                                width: modelData.w * redeyeOverlay.width
                                height: modelData.h * redeyeOverlay.height
                                color: "transparent"
                                border.width: 1
                                border.color: Theme.selectionBlue
                            }
                        }

                        // az ÉPP húzott téglalap (még nincs a pufferben)
                        Rectangle {
                            objectName: "redeyeDragRect"
                            visible: redeyeDragArea.dragging
                                     && !editorPanel.redeyeHideOutlines
                            x: Math.min(redeyeDragArea.startX, redeyeDragArea.lastX)
                            y: Math.min(redeyeDragArea.startY, redeyeDragArea.lastY)
                            width: Math.abs(redeyeDragArea.lastX - redeyeDragArea.startX)
                            height: Math.abs(redeyeDragArea.lastY - redeyeDragArea.startY)
                            color: "transparent"
                            border.width: 1
                            border.color: Theme.selectionBlue
                        }

                        MouseArea {
                            id: redeyeDragArea
                            objectName: "redeyeDragArea"
                            anchors.fill: parent
                            enabled: editorPanel.redeyeActive
                            cursorShape: Qt.CrossCursor
                            property bool dragging: false
                            property real startX: 0
                            property real startY: 0
                            property real lastX: 0
                            property real lastY: 0
                            onPressed: function(mouse) {
                                dragging = true
                                startX = mouse.x; startY = mouse.y
                                lastX = mouse.x; lastY = mouse.y
                            }
                            onPositionChanged: function(mouse) {
                                if (!dragging) return
                                lastX = mouse.x; lastY = mouse.y
                            }
                            onReleased: function(mouse) {
                                dragging = false
                                if (width <= 0 || height <= 0) return
                                // a puszta kattintás (nulla méretű téglalap)
                                // a kontrollerben néma no-op
                                editController.addRedeyeRegion(
                                    Math.min(startX, mouse.x) / width,
                                    Math.min(startY, mouse.y) / height,
                                    Math.abs(mouse.x - startX) / width,
                                    Math.abs(mouse.y - startY) / height)
                            }
                        }
                    }
                    MouseArea {
                        id: textClickArea
                        objectName: "textClickArea"
                        parent: photo
                        visible: editorPanel.textActive
                        enabled: editorPanel.textActive
                        x: (photo.width - photo.paintedWidth) / 2
                        y: (photo.height - photo.paintedHeight) / 2
                        width: photo.paintedWidth
                        height: photo.paintedHeight
                        cursorShape: Qt.CrossCursor
                        onClicked: function(mouse) {
                            if (width <= 0 || height <= 0) return
                            editController.previewTextPlacement(
                                mouse.x / width, mouse.y / height)
                        }
                    }
                }
                // #6: nagyított képen húzással pásztázás; dupla katt = fit.
                // Illesztett nézetben inaktív — az események átmennek rajta.
                MouseArea {
                    objectName: "viewerPanArea"
                    anchors.fill: photoArea
                    enabled: viewer.zoomFactor > 1.01
                             && !editorPanel.cropActive
                             && !viewer.isCurrentVideo
                    cursorShape: enabled ? Qt.OpenHandCursor : Qt.ArrowCursor
                    property real lastX: 0
                    property real lastY: 0
                    onPressed: function(event) {
                        lastX = event.x; lastY = event.y
                    }
                    onPositionChanged: function(event) {
                        if (!pressed) return
                        viewer.panX += event.x - lastX
                        viewer.panY += event.y - lastY
                        lastX = event.x; lastY = event.y
                        viewer.clampPan()
                    }
                    onDoubleClicked: viewer.zoomFit()
                }

                BusyIndicator {
                    anchors.centerIn: parent
                    running: photo.status === Image.Loading
                }

                // #6: alsó zoom-sáv (design-guide hiánylista 4.):
                // illesztés / 1:1 / csúszka — jobb alsó sarok
                Rectangle {
                    id: zoomBar
                    objectName: "viewerZoomBar"
                    visible: !viewer.isCurrentVideo && !editorPanel.cropActive
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: 4
                    width: zoomRow.width + 12
                    height: 26
                    radius: 4
                    color: "#00000059"
                    Row {
                        id: zoomRow
                        anchors.centerIn: parent
                        spacing: 4
                        PicasaButton {
                            objectName: "zoomFitButton"
                            text: "⛶"
                            width: 26; height: 20
                            onClicked: viewer.zoomFit()
                        }
                        PicasaButton {
                            objectName: "zoomActualButton"
                            text: "1:1"
                            width: 30; height: 20
                            onClicked: viewer.zoomActual()
                        }
                        // #147: arc-keretek be/ki (F billentyűvel egyenértékű)
                        PicasaButton {
                            objectName: "facesToggleButton"
                            text: "☺"
                            checkable: true
                            checked: viewer.facesVisible
                            width: 26; height: 20
                            ToolTip.visible: hovered
                            ToolTip.text: qsTr("Show Faces")
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
                            onClicked: viewer.toggleFacesEdit()
                        }
                        PicasaSlider {
                            id: zoomSlider
                            objectName: "zoomSlider"
                            width: 110; height: 20
                            anchors.verticalCenter: parent.verticalCenter
                            from: 0.25; to: 8
                            onMoved: viewer.setZoom(value)
                            // húzás közben a kéz vezet; egyébként az állapot
                            Binding on value {
                                when: !zoomSlider.pressed
                                value: viewer.zoomFactor
                            }
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
                TextInput {
                    id: captionField
                    objectName: "captionField"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 8
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.min(400, photoArea.width)
                    horizontalAlignment: TextInput.AlignHCenter
                    color: "#ffffff"
                    font.pixelSize: Theme.fontSize
                    selectByMouse: true
                    text: viewer.photosModel
                        ? (viewer.photosModel.revision,
                           viewer.photosModel.captionAt(viewer.currentIndex))
                        : ""

                    function rebind() {
                        text = Qt.binding(function () {
                            return viewer.photosModel
                                ? (viewer.photosModel.revision,
                                   viewer.photosModel.captionAt(viewer.currentIndex))
                                : ""
                        })
                    }

                    onAccepted: {
                        controller.setCaption(viewer.currentIndex, text)
                        rebind()
                        viewer.forceActiveFocus()
                    }
                    Keys.onEscapePressed: (event) => {
                        rebind()
                        viewer.forceActiveFocus()
                        event.accepted = true
                    }
                }
                Text {
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 8
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("Make a caption!")
                    color: "#e8e8e8"
                    font.pixelSize: Theme.fontSize
                    visible: captionField.text.length === 0 && !captionField.activeFocus
                }

                // elő-betöltés: a szomszédok már dekódolva, mire lépsz —
                // a #84 óta a mappán belüli szomszéd (folderNeighbor), nem
                // a nyers currentIndex±1, hogy ne a szomszéd mappa képét
                // töltsük elő feleslegesen a mappahatárnál
                Image {
                    visible: false
                    source: viewer.photosModel
                        ? viewer.preloadUrlAt(viewer.photosModel.folderNeighbor(viewer.currentIndex, 1))
                        : ""
                    asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
                    sourceSize.width: 2560
                }
                Image {
                    visible: false
                    source: viewer.photosModel
                        ? viewer.preloadUrlAt(viewer.photosModel.folderNeighbor(viewer.currentIndex, -1))
                        : ""
                    asynchronous: Qt.platform.pluginName !== "offscreen"; autoTransform: true
                    sourceSize.width: 2560
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
                // a photos.revision-nel együtt kötve: modell-frissüléskor
                // (pl. forgatás, felirat-mentés) újraolvas; a controller
                // önálló példányosításnál (tesztek) hiányozhat
                entries: (viewer.propertiesOpen && viewer.photosModel
                          && typeof controller !== "undefined" && controller)
                    ? (viewer.photosModel.revision,
                       controller.propertiesOf(viewer.currentIndex))
                    : []
                onCloseRequested: {
                    if (viewer.appWindow
                        && viewer.appWindow.propertiesPanelOpen !== undefined)
                        viewer.appWindow.propertiesPanelOpen = false
                }
            }
        }
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

    function openContextMenu(x, y) { viewerMenu.popup(viewer, x, y) }

    ViewerContextMenu {
        id: viewerMenu
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

        onBackToLibraryRequested: viewer.closed()
        onAddToAlbumRequested: function(token) {
            if (typeof controller !== "undefined" && controller)
                controller.addRowsToAlbum([viewer.currentIndex], token)
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
                && viewer.currentPath.length > 0)
                fileOpsController.openPhoto(viewer.currentPath)
        }
        onLocateRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer.currentPath.length > 0)
                fileOpsController.revealPhoto(viewer.currentPath)
        }
        onCopyFullPathRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController
                && viewer.currentPath.length > 0)
                fileOpsController.copyFullPath(viewer.currentPath)
        }
        onDeleteRequested: {
            if (viewer.currentPath.length > 0)
                viewer.deleteRequested(viewer.currentPath)
        }
        onPropertiesRequested: {
            if (viewer.appWindow
                && viewer.appWindow.propertiesPanelOpen !== undefined)
                viewer.appWindow.propertiesPanelOpen =
                    !viewer.appWindow.propertiesPanelOpen
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
    ConfirmDialog {
        id: copyCaptionConfirm
        namePrefix: "copyCaptionConfirm"
        onConfirmed: editorPanel.textDraftContent = editorPanel.captionText
    }

    // #465: a retus/vörösszem visszavonása ADATOT dob el (nincs „Újra") —
    // az eredeti Picasa két külön szövegével kérdez rá. A döntés-kulcs
    // eszközönként külön, hogy a „Ne kérdezze újra" a másikra ne hasson.
    ConfirmDialog {
        id: undoDataLossDialog
        objectName: "undoDataLossDialog"
        namePrefix: "undoDataLoss"
        title: qsTr("Undo")
        function askFor(key, text) { ask("undo-" + key, text) }
        onConfirmed: editController.undo()
    }

}

import QtQuick
import QtQuick.Controls

// A szerkesztési munkamenetek, eszközök és döntési párbeszédek.
Item {
    id: editWorkflow
    property var hostViewer: null
    readonly property var viewer: hostViewer
    anchors.fill: parent
    visible: viewer.visible
    readonly property int currentIndex: viewer.currentIndex
    readonly property int abMasikSor: viewer.abMasikSor
    readonly property string layoutMode: viewer.layoutMode
    readonly property string aktivOldal: viewer.aktivOldal
    readonly property bool ctrlF9AutoStep: viewer.ctrlF9AutoStep
    readonly property var photosModel: viewer.photosModel
    readonly property var editorPanel: viewer.editorPanel
    readonly property var cropOverlay: viewer.cropOverlay
    readonly property var editorToolBar: viewer.editorToolBar
    readonly property var drawerShortcutSequence:
        toggleEditorDrawerShortcut.sequence

    function toggleEditorDrawer() {
        if (typeof controller !== "undefined" && controller
                && controller.setEditorControlsVisible !== undefined) {
            controller.setEditorControlsVisible(!controller.editorControlsVisible)
        } else {
            viewer.editorControlsVisible = !viewer.editorControlsVisible
        }
    }

    // #4696: a Ctrl+9 a szerkesztő-előnézetben nyitja/zárja a bal fiókot.
    Shortcut {
        id: toggleEditorDrawerShortcut
        sequence: "Ctrl+9"
        enabled: viewer.visible
        onActivated: viewer.toggleEditorDrawer()
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
//: oldalt szerkeszti (`aktivSor`), a második rekesz ezt a másikat kapja -
//: így a szerkesztő-panel 104 kötése változatlan maradhat, a parancsok
//: mégis a kijelölt oldalra hatnak.
readonly property int masodikSor: viewer._masodikSort()

//: ⚠️ #3187: a KÖTÖTT `aktivSor`/`masodikSor` NEM használható az
//: imperatív kezelőkben. A #218 óta tudjuk: egy kötött property
//: újraértékelése nem garantált, mire az UGYANARRA a jelzésre futó
//: imperatív kezelő lefut - mérve ezen a jegyen is: fókuszváltás után a
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
    //: #3014: „aa" módban is van második fél - ugyanaz a fotó
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
//: a belépéskori lánc - MINDKÉT fél „módosult" próbájának alapja
property string aaKiindulas: ""
//: melyik fotóra fut a munkamenet (lapozáskor ebből tudjuk, hogy zárni kell)
property string aaFotoId: ""
//: a párbeszéd alatt várakozó kilépés (módváltás, lapozás, bezárás,
//: programzárás) - a VÁLASZ után fut, Mégsére elmarad
property var aaFolytatas: null
//: a párbeszéd épp kérdez - amíg válaszra vár, újabb kilépés nem írhatja
//: felül a várakozót (a lapozás a régi kötésekkel még egyszer ideérhet)
property bool aaKerdesFut: false

//: #3651: a „Szerkesztés jóváhagyása" (`endEditModality`) párbeszéd alatt
//: várakozó módváltás - a VÁLASZ (alkalmaz vagy elvet) után fut.
property var endEditFolytatas: null

//: #3651: a Vágás megnyitásakor betöltött kijelölés (a kép mentett
//: vágása, vagy `null`) - a „módosult" próba ehhez méri a mostanit, így
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

//: VÉGSŐ tartalék, párbeszéd NÉLKÜL - csak olyan kilépésnek, amely nem
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

//: #3014/#3644: az „aa" mód KILÉPÉSI KAPUJA - minden út ezen megy át,
//: amely az „aa" munkamenetet elhagyja: módváltás, lapozás, a néző
//: elhagyása és a program bezárása. Mérve (`docs/specs/ui-audit-editor.md`
//: 4/c.1): az eredetiben a `0x0056aad0` hívói - a módváltás (`0x0056a260`,
//: `0x0056a680`), a lapozás (`0x00578c30`/`0x00578dc0`), a filmszalag
//: (`0x005deb29`, `0x005d34ed`) és a programzárás (`SC_CLOSE` →
//: `0x0057c4e0` → `0x005e45c0`) - Mégsére (`0xf4242`) mind MEGÁLLNAK.
//:
//: `true`: nincs (vagy már el is dőlt) a kérdés, a hívó MOST folytathat.
//: `false`: a párbeszéd nyitva; a `folytatas` a VÁLASZ után fut, Mégsére
//: elmarad - a hívó ilyenkor NE folytassa.
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
//: `0x005f8d80` - „ha egy modális eszköz nyitva van"). A „módosult" a
//: panel saját Alkalmaz-gombjának engedélyezettségi feltételét követi
//: (retusálás/szöveg - a 3/c szakasz szerint ugyanez a kapu nézi az
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

//: #3651: a nyitott eszköz lezárása a saját Alkalmaz/Mégse útján -
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

//: #3651: a „Szerkesztés jóváhagyása" kapu (4/b.1 2. lépés) - az „aa"/
//: „ab" módba lépés előtt fut, MIUTÁN a 2-up kilépési létra (`aaKilepesKapu`)
//: már eldőlt. #3693: a fókuszváltás (`fokuszValt`) is ezt hívja,
//: `megseEngedve = true`-val - a két hívó a 3/c szerint a kapu MÁSIK
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

//: #3014: a kettős nézet üzemmódjának váltása - a szegmensek ezt hívják.
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

//: #3693: a FÓKUSZVÁLTÁS kapuja - a kép kattintása és a „Fókusz
//: váltása" gomb egyaránt ide fut. Ugyanaz a kapu, mint a mód-váltásnál
//: (#3651, `_eszkozZarasKapu`), de a 3/c mérés szerint a fókuszváltó
//: (`0x0056a160`) a kaput `megseEngedve = true`-val hívja: a nyitott ÉS
//: módosult modális eszköznél a „Szerkesztés jóváhagyása" kérdés VAN
//: Mégse gombbal - Mégsére a fókusz NEM vált, az eszköz nyitva marad.
function fokuszValt(uj) {
    if (uj === viewer.aktivOldal) return
    if (!viewer._eszkozZarasKapu(
            function () { viewer.aktivOldal = uj }, true))
        return
    viewer.aktivOldal = uj
}

//: #3644: a LAPOZÁS kapuja - a `currentIndex` már az új soron áll, amikor
//: a váltás ide ér (billentyű, gomb, filmszalag egyaránt). Az eredeti
//: lapozása ELŐBB kérdez, és Mégsére nem lapoz (`0x00578c30`/
//: `0x00578dc0` → `0x0056aad0`, `cmp eax, 0xf4242` @ `0x00578c6d`) -
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
//: kérése) - előbb az „aa" kapu. Az eredeti itt nem kérdez, de a két fél
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
//: (retusálás-folt, vörösszem-régió, vágókeret) - előbb zárul, mint a
//: néző bezárásakor; a csere után a panel az ÚJ fél értékeit mutatja.
//: #3649: a festett maszk NEM ürül - a `swapAaFocus` a párral cseréli,
//: hogy a félkész festés a saját felén megmaradjon. A festés NEM
//: része a láncnak (`chainValue`), ezért a „van-e mit cserélni"
//: döntés a `swapAaFocus`-é - a QML itt nem tér ki azonos lánc esetén
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

//: #3651: 4/b.1 2. lépés - a nyitott modális eszköz lezárás-kérdése,
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
    //: #3693: Mégse - az eszköz nyitva marad, a folytatás elmarad
    onMegse: {
        viewer.endEditFolytatas = null
    }
}

//: #3773: jobb fókusznál a JOBB fél (`abMasikSor`) a kijelölt - ha az
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
//: #3187: a fókuszváltás ÁTVISZI a szerkesztést a másik oldalra - a fő
//: vezérlő a kijelöltet kapja, a második rekesz a régi kijelöltet.
//: #3014: „aa" módban ugyanaz a fotó áll mindkét félen - ott a LÁNCOK
//: cserélnek, újratöltés helyett (az ini-ben csak a kijelölt fél áll).
onAktivOldalChanged: {
    //: #3741: a nagyítás a fókuszban lévő félre hat - a másik kép
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
    //: #3014: MÁSIK fotóra lépve a futó „aa" munkamenet zárul - még
    //: azelőtt, hogy a fő vezérlő elhagyná a régi fotót. #3644: a lapozás
    //: kapuján át; ha a párbeszéd kérdez, a néző visszaáll a munkamenet
    //: fotójára, és a fő vezérlő ott marad.
    if (viewer.aaMunkamenet) {
        if (viewer.aaFotoId === photosModel.idAt(sor)) {
            //: a fő vezérlő már ezen a fotón áll a kijelölt fél láncával
            //: - újratöltés a visszavonás-vermét dobná el
            if (editController.previewSource !== "") return
        } else if (!viewer._aaLapozasKapu()) {
            return
        }
    }
    // #218: a viewer.isCurrentVideo egy kötött property - a currentIndex
    // váltásakor NEM garantált, hogy már újraértékelődött, mire ez a
    // (szintén a currentIndexChanged-re futó) imperatív függvény lefut,
    // ezért a modellt itt KÖZVETLENÜL kérdezzük le (mindig friss),
    // nem a cache-elt property-t
    if (photosModel.isVideoAt(sor)) {
        // videón nincs képszerkesztés (#14) - az előző kép nyitott
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
// szerkesztési munkamenet (`editCtl.previewSource` üres) - a nyers fájlon
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
// `display_mode_controller.py` modul-docstring). Videón nem fut le - ott
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
// previewTilt-et - a szinkron csak a csúszkát mozgatja, az előnézet
// már a beginEditCurrent()/_register_preview() óta helyes.
//: #3234: a szinkron ELNYOMÓJA. Korábban a csúszka saját
//: `suppressPreview` tulajdonsága volt; a csúszka a sávba költözött,
//: a szerepe viszont változatlan: a programozott értékadás NE
//: váltson ki előnézetet.
property bool tiltSzinkronFut: false
//: #4058: az Alkalmaz már mentett és újrarenderelt; az ezt követő
//: eszközbezárás ne kérje le még egyszer a mentett láncot.
property bool tiltAlkalmazasFut: false
//: #3234: a döntés értéke az eszköz NYITÁSAKOR - ezt állítja vissza a
//: sáv Mégse gombja (`tool_cancel`, `Property escapekey 1`).
property real tiltErtekNyitaskor: 0

function syncTiltSlider() {
    viewer.tiltSzinkronFut = true
    editorToolBar.csuszkaErtek = editController.tiltParam
    viewer.tiltSzinkronFut = false
    // #448: a Kiegyenesítés-figyelmeztetés a vágó-panelen - a
    // tiltParam a mentett döntés-paraméter, 0.0 = nincs aktív tilt
    editorPanel.straightenActive = editController.tiltParam !== 0
}
function syncPanelFromController() {
    // #445: a panel `redeyeActive`-ja a Vágás/Retusálás mintájára
    // ESZKÖZ-nyitást jelent (nem a `redeye` réteg meglétét) - ezért NEM
    // a vezérlő `hasSavedRedeye`-jének tükre; azt onnan felülírni
    // becsukná/kinyitná a panelt a mentett lánc alapján.
    // #2393: a vezérlő tagja korábban szintén `redeyeActive` volt - a
    // névazonosság félrevitte a #1485-öt, ezért kapott beszédes nevet.
    // #448: a tilt-szűrő a láncban változhatott (pl. a felhasználó
    // épp most alkalmazta a Kiegyenesítést) - a figyelmeztetés kövesse
    editorPanel.straightenActive = editController.tiltParam !== 0
    // egygombos javítások (#116): "nyomható-e" tükrözése - a gomb
    // tiltott, amíg ugyanez a szűrő a lánc utolsó eleme
    editorPanel.enhanceEnabled = editController.enhanceEnabled
    editorPanel.autolightEnabled = editController.autolightEnabled
    editorPanel.autocolorEnabled = editController.autocolorEnabled
    // Finomhangolás-csúszkák (#20): a panel binding már frissítette a
    // fillLight/highlights/shadows/colorTemp értékeket a kontrollerből -
    // ez a hívás azokat suppress mellett a csúszkákba is beírja
    editorPanel.syncFinetuneSliders()
    // #450: "Remove all existing text" gomb tiltási állapota
    editorPanel.hasTextOverlay = editController.hasTextOverlay
    editorPanel.textOverlayVisible = editController.textOverlayVisible
    if (editorPanel.textActive)
        editorPanel.textDraftContent = editController.textDraft
    // #450: szöveg-stílus - kitöltés+körvonal szín, körvonal-vastagság,
    // kitöltés ki/be, átlátszóság
    // #464: a Finomhangolás fül pipettája melletti színminta
    editorPanel.neutralColor = editController.neutralColor
    editorPanel.textFillColor = editController.textFillColor
    editorPanel.textOutlineColor = editController.textOutlineColor
    editorPanel.textOutlineThickness = editController.textOutlineThickness
    editorPanel.textFillEnabled = editController.textFillEnabled
    editorPanel.textOpacity = editController.textOpacity
    // #450 (2. lépcső): tipográfia - betűcsalád, méret, B/I/U, igazítás
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
        //: tehát ide már lezárt munkamenettel érnek - ez a tartalék.
        viewer._aaLezaras()
        editController.endEdit()
        //: #3187: a második rekesz munkamenete is záruljon - nyitva
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
        //: rekeszé - rögzített másik képnél (`masodikIndex`) az
        //: `abMasikSor` nem változik, tehát itt kell utánanyúlni.
        if (viewer.layoutMode === "ab" && viewer.aktivOldal === "jobb"
                && viewer.masodikIndex >= 0)
            frissitsdAMasodikSzerkesztest()
        // lapozáskor a csúszka az ÚJ kép mentett tilt-értékére áll -
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
        // #148: a Retusálás/Szöveg mód lapozáson át is megtartható -
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
    // #148: a Retusálás/Szöveg mód nyitása/zárása - a Vágás mintáját
    // követve az enter/exit a puffer/piszkozat élő előnézetét kezeli,
    // Alkalmazásig nem ír inibe.
    function onRetouchActiveChanged() {
        if (editorPanel.retouchActive)
            editController.enterRetouchTool()
        else
            editController.exitRetouchTool()
    }
    // #445: a Vörösszem eszköz nyitása/zárása - nyitáskor az automatika
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
}

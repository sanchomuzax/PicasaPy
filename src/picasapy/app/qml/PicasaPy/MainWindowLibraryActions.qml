import QtQml
import QtQuick
import QtQuick.Window

// A főablak néző- és könyvtári parancsai.
QtObject {
    id: actions
    required property var hostWindow
    required property var hostController
    required property var hostPhotoViewer
    required property var hostToolbar

    // #1773: a lapváltás EGYETLEN útja. Az aktív lapra kattintás
    // SZÁNDÉKOSAN nem zár be: a bináris a vizsgált ágon feltétel nélkül
    // 1-re állítja a saját gombját (a jegy „nyitott" pontja, ez az
    // alapértelmezés). A fiók ürítése az `ureseidAFiokot()`.
    function valtsFiokLapot(nev) {
        hostWindow.activeDrawerTab = nev
        if (nev !== "") hostWindow.utolsoFiokLap = nev
    }
    function ureseidAFiokot() {
        hostWindow.activeDrawerTab = ""
    }

    //: #2163: a `Ctrl+0` (`thumbui/toggle_right_drawer`, `0x005e6206`) a
    //: jobb fiókot BILLENTI. Bezárás után újranyitva ugyanaz a lap jöjjön
    //: vissza — enélkül a billentés fele-útja adatvesztésnek látszik: a
    //: felhasználó a Címkéket zárta be, és az Emberek nyílna ki.
    property string utolsoFiokLap: "tags"

    //: #2163: a `Ctrl+F` a fejléc keresőmezőjére viszi a fókuszt. A
    //: `header` a nézőben nincs jelen (ld. a `MainToolbar` bekötését),
    //: ezért a null-őr nem formaság.
    function fokuszAKeresore() {
        if (hostToolbar && hostToolbar.fokuszAKeresore) hostToolbar.fokuszAKeresore()
    }

    //: #2163: a `Ctrl+3` (Szerkesztési nézet, `0x005e624f` →
    //: `thumbui/fullview`) UGYANAZT teszi, mint a „Megjelenítés és
    //: szerkesztés" parancs: a kijelölt képet a nézőben nyitja meg, ahol a
    //: szerkesztő panel is ül. Egy belépő, több hívó — a tálca helyi
    //: menüje (#1917) is ezt hívja.
    // #4656: minden tényleges nézőnyitás ezt használja. A teljes képernyő
    // vagy ablakos mód a mentett jelölőt követi; bezáráskor a korábbi
    // ablakállapot áll vissza.
    function openPhotoViewer(row) {
        if (!hostWindow.viewerOpen) {
            hostWindow.visibilityBeforeViewer = hostWindow.visibility
            var fullscreenStartup = hostController
                && hostController.viewerFullscreenStartup !== undefined
                ? hostController.viewerFullscreenStartup : true
            hostWindow.visibility = fullscreenStartup
                ? Window.FullScreen : Window.Windowed
            hostWindow.viewerVisibilityManaged = true
            hostWindow.viewerOpen = true
        }
        hostPhotoViewer.show(row)
    }

    // A közvetlen fájlargumentumos indulás ugyanazt a viewer-ablakmódot
    // használja, mint a Photo Viewer beállítása. Külön függvényben van, hogy
    // a rendes Component.onCompleted út és a QML-funkcióteszt is ezt hívja.
    function startQuickViewer() {
        if (!hostWindow.quickViewerLaunch) return
        hostWindow.visibilityBeforeViewer = hostWindow.visibility
        var fullscreenStartup = hostController
            && hostController.viewerFullscreenStartup !== undefined
            ? hostController.viewerFullscreenStartup : true
        hostWindow.visibility = fullscreenStartup
            ? Window.FullScreen : Window.Windowed
        hostWindow.viewerVisibilityManaged = true
        hostWindow.viewerOpen = true
        hostPhotoViewer.show(0)
    }

    function nezdEsSzerkeszd() {
        if (hostWindow.viewerOpen) return
        var sorok = hostWindow.selectedRows()
        if (sorok.length === 0) return
        hostWindow.openPhotoViewer(sorok[0])
    }

    // #4329: az önálló Kép ▸ Unhide parancs kizárólag a rejtett kijelölt
    // képeket teszi láthatóvá. A toggleHiddenRows csak a rejtett sorokat
    // kapja meg, ezért a vegyes kijelölés látható képei nem rejtődnek el.
    // #4626: a Kép ▸ Hide mindig rejtve hagyja a kijelölést. A már rejtett
    // sorokat kihagyjuk, így a váltó művelet csak látható képeket rejt el.
    // A helyi menük külön megőrzik a Hide/Unhide váltó viselkedést.
    function hideSelection() {
        if (!hostController) return
        var rows = hostWindow.photoActionRows()
        if (rows.length === 0) return
        var visibleRows = []
        for (var i = 0; i < rows.length; ++i) {
            var row = Number(rows[i])
            var photo = hostController.photos.itemAt(row)
            if (photo && photo.hidden !== true) visibleRows.push(row)
        }
        if (visibleRows.length > 0) hostController.toggleHiddenRows(visibleRows)
        if (!hostWindow.viewerOpen) hostWindow.clearSelection()
    }

    function unhideHiddenSelection() {
        if (!hostController) return
        var rows = hostWindow.photoActionRows()
        var hiddenRows = []
        for (var i = 0; i < rows.length; ++i) {
            var row = Number(rows[i])
            var photo = hostController.photos.itemAt(row)
            if (photo && photo.hidden === true) hiddenRows.push(row)
        }
        if (hiddenRows.length === 0) return
        hostController.toggleHiddenRows(hiddenRows)
        if (!hostWindow.viewerOpen) hostWindow.clearSelection()
    }

    //: #2163: a `Ctrl+F7` az eredetiben a `searchoptions/loadsim`-et
    //: kattintja — a MINTA a jelenlegi kép, és a keresés a hozzá
    //: hasonlókat adja (a mag a #1833-ban kész).
    //: #2163: a `Ctrl+F6` a másodpéldány-módot kapcsolja (#1398). A
    //: null-őr FÜGGVÉNYBEN áll, nem a `Shortcut` törzsében: a #1616 őre
    //: egyetlen zárójel-szintet lát, az ágazó törzs láthatatlan neki.
    function masodpeldanyokMutatasa() {
        if (hostController) hostController.showDuplicateFiles()
    }

    //: #2163: a `clearsim` párja — ugyanezért függvény.
    function torolAHasonlosagMintat() {
        if (hostController) hostController.clearSimilarity()
    }

    function keressHasonlot() {
        if (!hostController) return
        var sorok = hostWindow.selectedRows()
        if (sorok.length === 0) return
        hostController.showSimilarTo(sorok[0])
    }

    //: #2163: a `Ctrl+Shift+B` és a `Ctrl+Shift+E` az eredetiben egyetlen
    //: szűrő-alkalmazóba megy (`0x005fe370(panel, "bw"|"enhance")`), ami a
    //: KIJELÖLÉSRE hat — nálunk ez a köteg-szerkesztés útja
    //: (`applyEffectMany`), ugyanaz, amit az Kép ▸ Köteg-szerkesztés
    //: menütételei hívnak. Nincs második ág.
    function kotegEffekt(nev) {
        if (!hostController) return
        var sorok = hostWindow.selectedRows()
        if (sorok.length === 0) return
        hostController.applyEffectMany(sorok, nev)
    }

    function billentsdAFiokot() {
        if (hostWindow.activeDrawerTab !== "") {
            hostWindow.utolsoFiokLap = hostWindow.activeDrawerTab
            hostWindow.ureseidAFiokot()
        } else {
            hostWindow.valtsFiokLapot(hostWindow.utolsoFiokLap)
        }
    }
}

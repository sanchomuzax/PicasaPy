import QtQuick
import "infosav.js" as InfoSav

Rectangle {
    id: infoBar
    objectName: "trayInfoBar"
    property var trayRoot
    property var trayController
    width: parent.width; height: 14
    color: Theme.infoBar
    clip: true

    // SAJÁT FUNKCIÓ (#70): lassan végigvonuló fény-hullám, amíg a
    // PicasaPy a háttérben dolgozik (indexelés, thumbnail-batch). Az
    // eredetiben nincs ilyen vizuális visszajelzés — saját UX-
    // kiegészítés (lista: docs/decisions/vedett-sajat-funkciok.md).
    // XAnimator: a render-szálon fut (a főszálat/GIL-t nem érinti, ld.
    // #53), idle-ben running=false → 0 CPU/GPU. Nem polloz: a
    // controller.isWorking jelzés-alapú (busyChanged).
    Rectangle {
        id: busySweep
        objectName: "busySweep"
        // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
        // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
        visible: (infoBar.trayController && infoBar.trayController.isWorking !== undefined) ? infoBar.trayController.isWorking : false
        width: Math.max(80, infoBar.width / 5)
        height: infoBar.height
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.5; color: "#59ffffff" }
            GradientStop { position: 1.0; color: "transparent" }
        }
        XAnimator on x {
            running: busySweep.visible
            loops: Animation.Infinite
            from: -busySweep.width
            to: infoBar.width
            duration: 1800
        }
    }
    Text {
        id: trayInfoLabel
        objectName: "trayInfoText"
        // #1934 (spec `kek-info-sav.md` 6.): a szövegnek SAJÁT clipje
        // van — `thumbui/clip: infotext_clip`, kényszere
        // `XConstraint 0, 0, 20` / `1, 1, -20` a sávon. A kék HÁTTÉR
        // ettől függetlenül teljes szélességű marad (mérve: a csík
        // sorában a kék x 0…1919, nem-kék képpont 0).
        //
        // A `respack.yt` ugyanerre az elemre `x 183…664`-et tárol, de
        // az MEGDŐLT: az a téglalap nem szimmetrikus (balra 183,
        // jobbra 136, közepe 423,5 a 800-as vásznon), márpedig a
        // szöveg közepe mind a 20 felvételen az ablak közepén áll
        // (|Δ| ≤ 0,5 képpont). A tárolt téglalap a tervezővászon
        // szerzői értéke; ahol az elem kényszert kap, az elrendező
        // felülírja.
        //
        // #2581: a levágás helye mért, ÉS a hárompont is az. A
        // `clip` megmarad vészféknek, de a szöveg már NEM fut bele: a
        // MÉRT kétlépcsős leépülés (`infosav.js`) előbb a `mappa > `
        // előtagot hagyja el, aztán a név KÖZEPÉN vág három ASCII
        // ponttal. A mérés a `docs/specs/kek-info-sav.md` 9.
        // szakaszában áll, két felvétel képpontjaiból.
        //
        // (A #1934 kori „a hárompont a MI döntésünk lenne" kifogás
        // ezzel megszűnt: az eredeti is ezt teszi, csak akkor, ha nem
        // fér ki.)
        x: 20
        width: Math.max(0, parent.width - 40)
        // #3310: a MÉRT felület-betűcsalád tokenje itt kap LÁTHATÓ
        // fogyasztót. Az érték megegyezik azzal, amit az alkalmazás
        // globálisan beállít (`_UI_FONT_FAMILY`, #526), tehát a
        // megjelenés nem változik — a token viszont innentől bizonyítottan
        // arra a családra mutat, amit a felhasználó tényleg lát.
        font.family: Theme.uiFamily
        anchors.verticalCenter: parent.verticalCenter
        horizontalAlignment: Text.AlignHCenter
        clip: true
        // #718: null-őr — a `ctl` mellett az `appWindow` is
        // átmenetileg null lehet az engine-leépítés utolsó kiértékelésekor.
        //
        // #1189: az eredeti `GetSelectionInfo` (`0x0056fbc0`) a
        // KIJELÖLÉSRŐL ír. Nálunk a „minden más" ág a mappa egészének
        // összesítését (`statusText`) mutatta, ezért több kijelölt
        // képnél a mappa adatai maradtak a sávban.
        //
        // #1168 (spec 16.3): a kollázs rajzolása alatt a FŐABLAK is
        // jelez — `CThumbUI::CreateCollageWait` (`0x007f7120`). A
        // várakozás MINDEN mást megelőz: a kollázs lapja közben be is
        // zárulhat, és a felhasználó máshol nézelődik, miközben a munka
        // fut — az eredeti éppen ezért a KÖNYVTÁRNÉZETBEN mondja ki.
        //
        // #455: a nézőn kívül a TÁLCA az elsődleges forrás — a tálca a
        // kijelölés tükre, plusz a máshonnan MEGTARTOTT képek, amiket a
        // rács sorindexei nem is tudnak leírni. Üres tálcánál minden
        // marad a mai ágakon (a `trayInfoText` ilyenkor üres).
        //: a MÉRT leépülés: előtag el, majd a név közepén vágás
        text: InfoSav.lecsokkentve(
                  trayInfoLabel.nyersSzoveg, trayInfoLabel.width,
                  trayInfoLabel.szelessege)

        /** A sáv szövege LEÉPÜLÉS NÉLKÜL — ebből dolgozik az InfoSav. */
        readonly property string nyersSzoveg:
              (!infoBar.trayController || !trayRoot.appWindow) ? ""
              : (trayRoot.photoRevision,
                 (infoBar.trayController.collageRendering === true
                  ? trayRoot.collageWaitText
                  : (trayRoot.appWindow.viewerOpen
                     ? (typeof infoBar.trayController.viewerInfo === "function"
                        ? infoBar.trayController.viewerInfo(trayRoot.viewerIndex) : "")
                     : (trayRoot.trayInfoText !== "" ? trayRoot.trayInfoText
                        : (trayRoot.appWindow.selectedIndexes.length === 1
                           ? infoBar.trayController.photoInfo(
                                 trayRoot.appWindow.selectedIndex)
                           : (trayRoot.appWindow.selectedIndexes.length > 1
                              && typeof infoBar.trayController.selectionInfo
                                  === "function"
                              ? infoBar.trayController.selectionInfo(
                                    trayRoot.appWindow.selectedIndexes)
                              : infoBar.trayController.statusText))))))
        color: Theme.infoBarText
        font.pixelSize: Theme.fontSize
        font.bold: true

        // #2581: a leépülés KÉPPONT-alapú, tehát a saját betűnkkel
        // kell mérni — a karakterszám nem elég (a mérés ezt zárta ki).
        //
        // ⛔ #3289: a mérés NEM írhat QML-tulajdonságot. A korábbi alak
        // egy `TextMetrics` `text`-jébe írt, és onnan olvasta vissza a
        // szélességet — csakhogy a `text:` kötés KIÉRTÉKELÉSE közben írt
        // tulajdonságot a Qt függőségként jegyzi meg, tehát a következő
        // változása újraértékelteti a kötést, és a kör bezárul. A
        // tulajdonos naplójában ez volt a
        // `TrayBar.qml:271 … Binding loop detected for property "text"`.
        //
        // A `FontMetrics.advanceWidth()` FÜGGVÉNYHÍVÁS: semmit nem ír,
        // tehát nem is válhat a kötés függőségévé. Ugyanezt a mintát
        // követi a `PanelButton.qml` fokozat-számolója
        // (`pbtnAlapMetrika`).
        FontMetrics {
            id: infoMetrika
            font: trayInfoLabel.font
        }

        /** Egy sztring szélessége EBBEN a betűben, képpontban. */
        function szelessege(szoveg) {
            return infoMetrika.advanceWidth(szoveg)
        }
    }
}

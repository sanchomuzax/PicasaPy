import QtQuick
import QtQuick.Controls
import PicasaPy

// A szerkesztő MÓD-ESZKÖZEI (vágás / retusálás / vörösszem / szöveg) —
// külön fájlban a #3220 óta (az `EditorPanel.qml` 1295 sorra nőtt, a
// projekt 800-as korlátja fölé).
//
// ⚠️ Viselkedés-azonos kiemelés: az `objectName` (`editorModeToolScroll`),
// a négy panel azonosítói, a láthatóság és a `contentHeight`-számítás
// (#778) változatlanok. A gazda adja be a `panel`-t és a horgonyokat.
//
// ⚠️ A gyerekek `panel:` kötése MINŐSÍTETT (`modeToolScroll.panel`):
// csupaszon a gyerek SAJÁT, még beállítatlan property-jére oldódna fel.
// ---------------- mód-eszközök (vágás/retusálás/vörösszem/szöveg) ----
//
// #464 (felhasználói hibajelentés az effekt-fülekről, ugyanaz az
// osztály): ezek a panelek a tartalmuktól függően MAGASABBAK lehetnek,
// mint a rendelkezésre álló hely — vágás/görgetés nélkül rálógnának a
// panel alján ülő, globális Visszavonás/Újra sorra. Ezért mind a négy
// EGY közös, vágott görgethető területen ül, ami pontosan a gombsorig
// ér. Egyszerre mindig legfeljebb egy látszik (a saját `visible`
// kötése szerint), a görgethető magasság ezért a LÁTHATÓÉ.
Flickable {
    id: modeToolScroll
    //: a gazda adja be (#3220)
    property Item panel
    //: A gazda `textApplyEnabled` kötése a szöveg-panel állapotát olvassa
    //: — a kiemelés után aliasszal adjuk vissza (#3220).
    property alias szovegLap: textModePanel
    objectName: "editorModeToolScroll"
    visible: panel.modeToolActive
    clip: true
    contentWidth: width
    // #778: a négy mód-panel FELSŐ MARGÓVAL ül (`anchors.margins: 10` a
    // saját fájljaikban), ezért a puszta `implicitHeight` kevesebb, mint a
    // tényleges alsó szél — a panel alja pontosan a margónyival lógott ki a
    // görgethető terület aljából, mind a négy módban, minden szélességnél.
    // A gyerek `y`-ját is bele kell számolni; ugyanaz a javítás, amit a
    // fülek `tabContentHeight`-je a #659-ben kapott. Beégetett 10 helyett
    // az `y`-t olvassuk, hogy a margó a panelek fájljaiban maradjon az
    // egyetlen igazságforrás.
    contentHeight: Math.max(
        cropModePanel.visible
            ? cropModePanel.y + cropModePanel.implicitHeight : 0,
        retouchModePanel.visible
            ? retouchModePanel.y + retouchModePanel.implicitHeight : 0,
        redeyeModePanel.visible
            ? redeyeModePanel.y + redeyeModePanel.implicitHeight : 0,
        textModePanel.visible
            ? textModePanel.y + textModePanel.implicitHeight : 0)
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: PicasaScrollBar {}

    // ---- "crop" mód: Fotó vágása ----
    EditorCropPanel {
        id: cropModePanel
        panel: modeToolScroll.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---- "retouch" mód: Retusálás (#148) ----
    // A kattintások kezelését a hívó (PhotoViewer) végzi a képen (ez a
    // fájl nem ismeri a kép geometriáját); a panel a puffer méretét és
    // az Alkalmaz/Mégse gombokat mutatja.
    EditorRetouchPanel {
        id: retouchModePanel
        panel: modeToolScroll.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---- "redeye" mód: Vörösszem (#445) ----
    // Az automatika a panel megnyitásakor lefut; a kézzel húzott
    // téglalapokat a hívó (PhotoViewer) veszi fel a képen.
    EditorRedeyePanel {
        id: redeyeModePanel
        panel: modeToolScroll.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---- "text" mód: Szöveg-overlay (#148) ----
    // A pozicionálás is kattintással történik a képen; a szövegmező itt
    // él, a gépelést a textDraftEdited jel viszi a controllerhez.
    EditorTextPanel {
        id: textModePanel
        panel: modeToolScroll.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }
}

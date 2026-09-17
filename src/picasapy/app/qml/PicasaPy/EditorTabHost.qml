import QtQuick
import PicasaPy

// A szerkesztő HÉT FÜLÉNEK közös területe — külön fájlban a #3220 óta (az
// `EditorPanel.qml` 1295 sorra nőtt, a projekt 800-as korlátja fölé).
//
// ⚠️ Viselkedés-azonos kiemelés: az `objectName` (`editorTabArea`), a fülek
// azonosítói, a láthatósági feltételek és a magasság-számítás
// változatlanok. A gazda adja be a `panel`-t és a horgonyokat — a
// fájl bevett mintája szerint („a láthatóságot és a horgonyokat MINDIG a
// gazda adja meg a használat helyén").
//
// ⚠️ A fülek `panel:` kötése MINŐSÍTETT (`tabHost.panel`). Csupaszon a
// gyerek SAJÁT, még beállítatlan `panel` property-jére oldódik fel, és a
// fülek `undefined`-ra hivatkoznának — a próbák ezt azonnal ki is mutatták
// („Cannot read property 'enabled' of undefined").
//
// A `panel.tabContentHeight` a `children` fölött iterál: a fülek ennek a
// komponensnek a gyerekei, tehát a számítás pontosan ugyanazt látja.
// ---------------- a FÜLEK közös területe (NEM görgethető) ----------
//
// #628 — a #616 visszavonása. A #422 a felhasználó nyomatékos kérésére
// levette a görgethető keretet az effekt-fülekről; a #616 aztán, a
// kilógó gombsort orvosolva, VISSZATETTE. A valódi ok azonban nem a
// fülek mérete volt, hanem egy beégetett szám: a PhotoViewer.qml fix
// 420 képpontot adott a panelnek, akármekkora az ablak. A 3. fül 12
// bélyegképes csempéje (3×4 ≈ 450 px) ennél MINDIG magasabb, ezért a
// görgetés nem szélsőséges eset volt, hanem az alapállapot.
//
// Az eredetiben a panel FIX méretű, és a kényszer-alapú (.tre)
// elrendezésben a rács mindig kifér — görgetés nincs. Nálunk ezt a
// garanciát a panel `implicitHeight`-je adja (ld. lent): az a
// LEGMAGASABB fület is elbírja, a gombsor pedig a tartalmat követi,
// nem fix magasságon ül.
Item {
    id: tabHost
    //: a gazda adja be (#3220) — a terület a panel állapotából számol
    property Item panel
    //: A gazda LOGIKÁJA (`editorpanel_logika.js`) két fülre hivatkozik
    //: névvel: a Finomhangolás csúszkáira és a „Gyakori javítások" fül
    //: arány-választójára. A kiemelés után ezek már nem a gazda
    //: hatókörében élnek, ezért ALIASSZAL adjuk vissza — a logika
    //: változatlan marad (#3220).
    property alias finomhangoloLap: finetunePanel
    property alias gyakoriLap: fixesTab
    objectName: "editorTabArea"
    // a csúszkás alpanel a fülek HELYETT jelenik meg (nem föléjük)
    visible: !panel.modeToolActive && !panel.paramPanelActive
    // #741: a fülterület a fülsávval AZONOS 276 képpontos
    // tartalom-oszlop (x 3..279) — a fülek eddig a teljes 280-ból
    // indultak, és a saját margóikkal együtt 260-ra szűkültek.
    // a terület magassága a LÁTHATÓ fülé — egyszerre legfeljebb egy az.
    // ALAPÁLLAPOTBAN nincs vágás és nincs görgetősáv: a tartalomnak el
    // KELL férnie (#422/#628 — a görgethető keret levételét a felhasználó
    // nyomatékosan kérte, és a #616 visszahozta; nem harmadszor is).
    //
    // #703: EGYETLEN kivétel, a szükség-ág. Ha a kijelző annyira alacsony,
    // hogy a panel nem kaphatja meg az igényét (az ablak minimuma nem
    // lehet nagyobb a képernyőnél), akkor a fül tartalma veszít — soha nem
    // a gombsor. A vágás ilyenkor és csak ilyenkor kapcsol be, és a
    // `panel.tabContentTruncated`-en át MÉRHETŐ, hogy melyik ágon vagyunk.
    height: tabArea.visible
            ? Math.min(panel.tabContentHeight, panel.tabAreaAvailable) : 0
    clip: panel.tabContentTruncated


    // ---------------- 1. fül: "Gyakori javítások" ikonrács ----------------
    // #496: a fül tartalma önálló fájlban (EditorTabCommonFixes.qml) — a
    // láthatóság és a horgonyok itt, a testvér-fülek mintája szerint.
    EditorTabCommonFixes {
        id: fixesTab
        panel: tabHost.panel
        visible: !panel.modeToolActive && panel.activeTab === 0
                 && !panel.paramPanelActive  // #583
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---------------- "finetune" mód: Finomhangolás (#20/#464) ----------
    // #464/#496: a fül tartalma önálló fájlban, a tulajdonos négy
    // képernyőképe szerinti elrendezéssel (ld. ott).
    EditorFinetunePanel {
        id: finetunePanel
        panel: tabHost.panel
        visible: !panel.modeToolActive && panel.activeTab === 1
                 && !panel.paramPanelActive  // #583
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---------------- "effects" mód: Effektek (#20) ----------------
    EditorEffectsTab1 {
        id: effectsTab1
        panel: tabHost.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---------------- "effects2" mód: 4. effekt-fül — zöld ecset,
    // "kreatív effektek" (#328, docs/specs/ui-audit-editor.md 4. fül) ------
    EditorEffectsTab2 {
        id: effectsTab2
        panel: tabHost.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---------------- "effects3" mód: 5. effekt-fül — kék ecset,
    // "művészi effektek" (#328, docs/specs/ui-audit-editor.md 5. fül) ------
    EditorEffectsTab3 {
        id: effectsTab3
        panel: tabHost.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---------------- "retouch" mód: Retusálás (#148) ----------------
    // A Vágás mintáját követi: a kép TELJES panel-területét foglalja el a
    // fülsáv/rács helyett; a kattintások kezelését a hívó (PhotoViewer)
    // végzi a képen (ez a fájl nem ismeri a kép geometriáját), a puffer
    // méretét (retouchRegionCount) és az Alkalmaz/Mégse gombokat mutatja.

    // ---------------- "redeye" mód: Vörösszem (#445) ----------------
    // Az automatika a panel megnyitásakor lefut; a kézzel húzott
    // téglalapokat — a Retusálás mintájára — a hívó (PhotoViewer) veszi fel
    // a képen, ez a fájl a puffer-állapotot és a gombokat mutatja.

    // ---------------- "text" mód: Szöveg-overlay (#148) ----------------
    // A pozicionálás is kattintással történik a képen (a hívó feladata,
    // ld. retouchColumn megjegyzése) — a szövegmező itt él, a tartalom
    // gépelését a textDraftEdited jel viszi a controllerhez.

    // ---------------- 6. fül: a további Glimmer-effektek (#422) --------
    EditorEffectsTab4 {
        id: effectsTab4
        panel: tabHost.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

    // ---------------- 7. fül: örökölt, felület nélküli szűrők (#571) ---
    EditorLegacyTab {
        id: legacyTab
        panel: tabHost.panel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
    }

}

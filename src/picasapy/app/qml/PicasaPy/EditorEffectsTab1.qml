import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 3. füle: a klasszikus effektek rácsa (#20/#315/#537) —
// Élesítés · Szépia · B&W · Warmify · Filmszemcse · Tint · Telítettség ·
// Lágy fókusz · Ragyogás · Szűrt B&W · Fókusz B&W · Átmenetes színezés.
//
// #496: kiemelve az EditorPanel.qml-ből — a gazda-panelre a `panel`
// tulajdonságon át hivatkozik (ld. `EditorCropPanel.qml`).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "effectsColumn"
    visible: !panel.modeToolActive && panel.activeTab === 2 && !panel.paramPanelActive
    opacity: panel.enabled ? 1 : 0.45
    // #741: az effekt-rács MÉRT geometriája (`fx1..fx12`, x 8 / 96 / 184,
    // osztásköz 88, látható csempe 86) a #704 óta helyes — a tartalom-
    // oszlop 276-ra bővülésével ezért a fül margóit kell igazítani, hogy a
    // rács továbbra is 262 képpont széles maradjon (3 × 86 + 2 × 2), az
    // x 8-on kezdve. Szimmetrikus 10-10-es margóval a csempe 86-ról 84-re
    // zsugorodott volna.
    anchors.leftMargin: 5
    anchors.rightMargin: 9
    anchors.topMargin: 10
    spacing: 8

    // #704: NINCS fejlécsáv a rács fölött. Az eredeti Picasa
    // elrendezés-forrásában (`editpanel.tre:428`) az effekt-fül panelének
    // (`editpanel/tabpanel3`) PONTOSAN EGY gyereke van: a rács konténere
    // (`editpanel/fxthumbs`). Szekciócím, fejlécsáv, cím-felirat az `fx*`
    // névtérben nincs — a fülre váltva azonnal a csempék jönnek. A korábbi
    // 22 képpontos, kiemelt hátterű sáv ráadásul abból a panelmagasságból
    // vett el, ami a #703 szerint amúgy is szűkös.

    GridLayout {
        objectName: "effectsGrid"
        // #537: HÁROM oszlop, mint az eredeti Picasa effekt-fülein
        columns: 3
        // #704: a csempék közti térköz az eredetin MÉRT 2 px
        // (`ui-audit-editor.md` 3.2: osztásköz 88 px, csempe 86 px), nem a
        // korábbi 6. A 3 × 86 + 2 × 2 = 262 px pontosan kiadja a panel
        // 261 képpontos tartalom-oszlopát.
        columnSpacing: 2
        rowSpacing: 2
        Layout.fillWidth: true

        // #315: az eredeti Picasa Effektek fülén az Élesítés az ELSŐ
        // gomb — a render/chain.py "unsharp" handlere ismeri, csak a
        // gombja hiányzott.
        PanelButton {
            objectName: "effectUnsharp"
            // #2141: az eredeti 1. csempéje az `unsharp2` (a `0x00c7e5a0` tábla [0]);
            // az `unsharp` a SHIFTes másodlagos, saját felirata
            // „Sharpen (Old)” (#2141)
            label: panel.shiftMasodlagos
                   ? qsTr("Sharpen (Old)") : qsTr("Sharpen")
            //: #2146: Shifttel a MÁSODLAGOS szűrő (unsharp) —
            //: az eredeti csempe-táblája (unsharp2 -> unsharp)
            readonly property string szuro: panel.shiftMasodlagos
                                            ? "unsharp" : "unsharp2"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("unsharp2")
            badge: panel.hasBadge(szuro)
        }
        PanelButton {
            objectName: "effectSepia"
            label: qsTr("Sepia")
            onButtonClicked: if (!panel.tryOpenParamPanel("sepia", label)) panel.effectRequested("sepia")
            thumbSource: panel.effectThumbSource("sepia")
            badge: panel.hasBadge("sepia")
        }
        PanelButton {
            objectName: "effectBw"
            label: qsTr("B&W")
            onButtonClicked: if (!panel.tryOpenParamPanel("bw", label)) panel.effectRequested("bw")
            thumbSource: panel.effectThumbSource("bw")
            badge: panel.hasBadge("bw")
        }
        PanelButton {
            objectName: "effectWarm"
            label: qsTr("Warmify")
            onButtonClicked: if (!panel.tryOpenParamPanel("warm", label)) panel.effectRequested("warm")
            thumbSource: panel.effectThumbSource("warm")
            badge: panel.hasBadge("warm")
        }
        PanelButton {
            objectName: "effectGrain2"
            // #2141: az eredeti 5. csempéje a `PicnikGrain`; a `grain2` nálunk
            // `oneclick`, ezért a csempe JELVÉNYT kapott, holott az
            // eredetin nincs — a `PicnikGrain` módja `effect` (#2141)
            label: panel.shiftMasodlagos
                   ? qsTr("Film Grain (Old)") : qsTr("Film Grain")
            //: #2146: Shifttel a MÁSODLAGOS szűrő (grain) —
            //: az eredeti csempe-táblája (picnikgrain -> grain)
            readonly property string szuro: panel.shiftMasodlagos
                                            ? "grain" : "picnikgrain"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("picnikgrain")
            badge: panel.hasBadge(szuro)
        }
        PanelButton {
            objectName: "effectTint"
            // #2141: az eredeti 6. csempéje a `PicnikTint`; a `tint` a SHIFTes
            // másodlagos, saját felirata „Tint (Old)” (#2141)
            label: panel.shiftMasodlagos
                   ? qsTr("Tint (Old)") : qsTr("Tint")
            //: #2146: Shifttel a MÁSODLAGOS szűrő (tint) —
            //: az eredeti csempe-táblája (picniktint -> tint)
            readonly property string szuro: panel.shiftMasodlagos
                                            ? "tint" : "picniktint"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("picniktint")
            badge: panel.hasBadge(szuro)
        }
        PanelButton {
            objectName: "effectSat"
            label: qsTr("Saturation")
            onButtonClicked: if (!panel.tryOpenParamPanel("sat", label)) panel.effectRequested("sat")
            thumbSource: panel.effectThumbSource("sat")
            badge: panel.hasBadge("sat")
        }
        PanelButton {
            objectName: "effectRadblur"
            label: qsTr("Soft Focus")
            onButtonClicked: if (!panel.tryOpenParamPanel("radblur", label)) panel.effectRequested("radblur")
            thumbSource: panel.effectThumbSource("radblur")
            badge: panel.hasBadge("radblur")
        }
        PanelButton {
            objectName: "effectGlow2"
            label: panel.shiftMasodlagos
                   ? qsTr("Glow (Old)") : qsTr("Glow")
            //: #2146: Shifttel a MÁSODLAGOS szűrő (glow) —
            //: az eredeti csempe-táblája (glow2 -> glow)
            readonly property string szuro: panel.shiftMasodlagos
                                            ? "glow" : "glow2"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("glow2")
            badge: panel.hasBadge(szuro)
        }
        PanelButton {
            objectName: "effectAnsel"
            label: qsTr("Filtered B&W")
            onButtonClicked: if (!panel.tryOpenParamPanel("ansel", label)) panel.effectRequested("ansel")
            thumbSource: panel.effectThumbSource("ansel")
            badge: panel.hasBadge("ansel")
        }
        PanelButton {
            objectName: "effectRadsat"
            label: qsTr("Focal B&W")
            onButtonClicked: if (!panel.tryOpenParamPanel("radsat", label)) panel.effectRequested("radsat")
            thumbSource: panel.effectThumbSource("radsat")
            badge: panel.hasBadge("radsat")
        }
        PanelButton {
            objectName: "effectDirTint"
            label: panel.shiftMasodlagos
                   ? qsTr("Radial Tint") : qsTr("Graduated Tint")
            //: #2146: Shifttel a MÁSODLAGOS szűrő (radtint) —
            //: az eredeti csempe-táblája (dir_tint -> radtint)
            readonly property string szuro: panel.shiftMasodlagos
                                            ? "radtint" : "dir_tint"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("dir_tint")
            badge: panel.hasBadge(szuro)
        }
    }
}

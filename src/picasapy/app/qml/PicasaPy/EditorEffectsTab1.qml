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
    anchors.margins: 10
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
            label: qsTr("Sharpen")
            onButtonClicked: if (!panel.tryOpenParamPanel("unsharp", label)) panel.effectRequested("unsharp")
            thumbSource: panel.effectThumbSource("unsharp")
            appliedCount: panel.effectAppliedCount("unsharp")
        }
        PanelButton {
            objectName: "effectSepia"
            label: qsTr("Sepia")
            onButtonClicked: if (!panel.tryOpenParamPanel("sepia", label)) panel.effectRequested("sepia")
            thumbSource: panel.effectThumbSource("sepia")
            appliedCount: panel.effectAppliedCount("sepia")
        }
        PanelButton {
            objectName: "effectBw"
            label: qsTr("B&W")
            onButtonClicked: if (!panel.tryOpenParamPanel("bw", label)) panel.effectRequested("bw")
            thumbSource: panel.effectThumbSource("bw")
            appliedCount: panel.effectAppliedCount("bw")
        }
        PanelButton {
            objectName: "effectWarm"
            label: qsTr("Warmify")
            onButtonClicked: if (!panel.tryOpenParamPanel("warm", label)) panel.effectRequested("warm")
            thumbSource: panel.effectThumbSource("warm")
            appliedCount: panel.effectAppliedCount("warm")
        }
        PanelButton {
            objectName: "effectGrain2"
            label: qsTr("Film Grain")
            onButtonClicked: if (!panel.tryOpenParamPanel("grain2", label)) panel.effectRequested("grain2")
            thumbSource: panel.effectThumbSource("grain2")
            appliedCount: panel.effectAppliedCount("grain2")
        }
        PanelButton {
            objectName: "effectTint"
            label: qsTr("Tint")
            onButtonClicked: if (!panel.tryOpenParamPanel("tint", label)) panel.effectRequested("tint")
            thumbSource: panel.effectThumbSource("tint")
            appliedCount: panel.effectAppliedCount("tint")
        }
        PanelButton {
            objectName: "effectSat"
            label: qsTr("Saturation")
            onButtonClicked: if (!panel.tryOpenParamPanel("sat", label)) panel.effectRequested("sat")
            thumbSource: panel.effectThumbSource("sat")
            appliedCount: panel.effectAppliedCount("sat")
        }
        PanelButton {
            objectName: "effectRadblur"
            label: qsTr("Soft Focus")
            onButtonClicked: if (!panel.tryOpenParamPanel("radblur", label)) panel.effectRequested("radblur")
            thumbSource: panel.effectThumbSource("radblur")
            appliedCount: panel.effectAppliedCount("radblur")
        }
        PanelButton {
            objectName: "effectGlow2"
            label: qsTr("Glow")
            onButtonClicked: if (!panel.tryOpenParamPanel("glow2", label)) panel.effectRequested("glow2")
            thumbSource: panel.effectThumbSource("glow2")
            appliedCount: panel.effectAppliedCount("glow2")
        }
        PanelButton {
            objectName: "effectAnsel"
            label: qsTr("Filtered B&W")
            onButtonClicked: if (!panel.tryOpenParamPanel("ansel", label)) panel.effectRequested("ansel")
            thumbSource: panel.effectThumbSource("ansel")
            appliedCount: panel.effectAppliedCount("ansel")
        }
        PanelButton {
            objectName: "effectRadsat"
            label: qsTr("Focal Saturation")
            onButtonClicked: if (!panel.tryOpenParamPanel("radsat", label)) panel.effectRequested("radsat")
            thumbSource: panel.effectThumbSource("radsat")
            appliedCount: panel.effectAppliedCount("radsat")
        }
        PanelButton {
            objectName: "effectDirTint"
            label: qsTr("Graduated Tint")
            onButtonClicked: if (!panel.tryOpenParamPanel("dir_tint", label)) panel.effectRequested("dir_tint")
            thumbSource: panel.effectThumbSource("dir_tint")
            appliedCount: panel.effectAppliedCount("dir_tint")
        }
    }
}

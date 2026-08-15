import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 4. füle: a „Kreatív" (zöld ecset) effektek rácsa
// (#329/#516) — Infravörös filmtől a Duo-tone-ig.
//
// #496: kiemelve az EditorPanel.qml-ből — a gazda-panelre a `panel`
// tulajdonságon át hivatkozik (ld. `EditorCropPanel.qml`).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "effectsColumn2"
    visible: !panel.modeToolActive && panel.activeTab === 3 && !panel.paramPanelActive
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
        objectName: "effectsGrid2"
        // #537: HÁROM oszlop, mint az eredeti Picasa effekt-fülein
        columns: 3
        // #704: a csempék közti térköz az eredetin MÉRT 2 px
        // (`ui-audit-editor.md` 3.2: osztásköz 88 px, csempe 86 px), nem a
        // korábbi 6. A 3 × 86 + 2 × 2 = 262 px pontosan kiadja a panel
        // 261 képpontos tartalom-oszlopát.
        columnSpacing: 2
        rowSpacing: 2
        Layout.fillWidth: true

        PanelButton {
            objectName: "effectIr"
            label: qsTr("Infrared Film")
            onButtonClicked: if (!panel.tryOpenParamPanel("ir", label)) panel.effectRequested("ir")
            thumbSource: panel.effectThumbSource("ir")
            appliedCount: panel.effectAppliedCount("ir")
        }
        PanelButton {
            objectName: "effectLomo"
            label: qsTr("Lomo-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("lomo", label)) panel.effectRequested("lomo")
            thumbSource: panel.effectThumbSource("lomo")
            appliedCount: panel.effectAppliedCount("lomo")
        }
        PanelButton {
            objectName: "effectHolga"
            label: qsTr("Holga-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("holga", label)) panel.effectRequested("holga")
            thumbSource: panel.effectThumbSource("holga")
            appliedCount: panel.effectAppliedCount("holga")
        }
        PanelButton {
            objectName: "effectHdr"
            label: qsTr("HDR-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("hdr", label)) panel.effectRequested("hdr")
            thumbSource: panel.effectThumbSource("hdr")
            appliedCount: panel.effectAppliedCount("hdr")
        }
        PanelButton {
            objectName: "effectCinemascope"
            label: qsTr("Cinemascope")
            onButtonClicked: if (!panel.tryOpenParamPanel("cinemascope", label)) panel.effectRequested("cinemascope")
            thumbSource: panel.effectThumbSource("cinemascope")
            appliedCount: panel.effectAppliedCount("cinemascope")
        }
        PanelButton {
            objectName: "effectOrton"
            label: qsTr("Orton-ish")
            onButtonClicked: if (!panel.tryOpenParamPanel("orton", label)) panel.effectRequested("orton")
            thumbSource: panel.effectThumbSource("orton")
            appliedCount: panel.effectAppliedCount("orton")
        }
        PanelButton {
            objectName: "effectSixties"
            label: qsTr("1960s")
            onButtonClicked: if (!panel.tryOpenParamPanel("sixties", label)) panel.effectRequested("sixties")
            thumbSource: panel.effectThumbSource("sixties")
            appliedCount: panel.effectAppliedCount("sixties")
        }
        PanelButton {
            objectName: "effectInvert"
            label: qsTr("Invert Colors")
            onButtonClicked: if (!panel.tryOpenParamPanel("invert", label)) panel.effectRequested("invert")
            thumbSource: panel.effectThumbSource("invert")
            appliedCount: panel.effectAppliedCount("invert")
        }
        PanelButton {
            objectName: "effectHeatMap"
            label: qsTr("Heat Map")
            onButtonClicked: if (!panel.tryOpenParamPanel("heatmap", label)) panel.effectRequested("heatmap")
            thumbSource: panel.effectThumbSource("heatmap")
            appliedCount: panel.effectAppliedCount("heatmap")
        }
        PanelButton {
            objectName: "effectCrossProcess"
            label: qsTr("Cross Process")
            onButtonClicked: if (!panel.tryOpenParamPanel("crossprocess", label)) panel.effectRequested("crossprocess")
            thumbSource: panel.effectThumbSource("crossprocess")
            appliedCount: panel.effectAppliedCount("crossprocess")
        }
        PanelButton {
            objectName: "effectQuantizePalette"
            label: qsTr("Posterize")
            onButtonClicked: if (!panel.tryOpenParamPanel("quantizepalette", label)) panel.effectRequested("quantizepalette")
            thumbSource: panel.effectThumbSource("quantizepalette")
            appliedCount: panel.effectAppliedCount("quantizepalette")
        }
        PanelButton {
            objectName: "effectTwoTone"
            label: qsTr("Duo-Tone")
            onButtonClicked: if (!panel.tryOpenParamPanel("twotone", label)) panel.effectRequested("twotone")
            thumbSource: panel.effectThumbSource("twotone")
            appliedCount: panel.effectAppliedCount("twotone")
        }
    }
}

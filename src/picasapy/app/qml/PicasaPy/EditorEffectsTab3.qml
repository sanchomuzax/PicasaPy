import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 5. füle: a „Művészi" (kék ecset) effektek rácsa
// (#330/#516) — Boosttól a Polaroidig.
//
// #496: kiemelve az EditorPanel.qml-ből — a gazda-panelre a `panel`
// tulajdonságon át hivatkozik (ld. `EditorCropPanel.qml`).
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "effectsColumn3"
    visible: !panel.modeToolActive && panel.activeTab === 4 && !panel.paramPanelActive
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
        objectName: "effectsGrid3"
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
            objectName: "effectBoost"
            label: qsTr("Boost")
            onButtonClicked: if (!panel.tryOpenParamPanel("boost", label)) panel.effectRequested("boost")
            thumbSource: panel.effectThumbSource("boost")
            appliedCount: panel.effectAppliedCount("boost")
        }
        PanelButton {
            objectName: "effectSoften"
            label: qsTr("Soft Focus")
            onButtonClicked: if (!panel.tryOpenParamPanel("soften", label)) panel.effectRequested("soften")
            thumbSource: panel.effectThumbSource("soften")
            appliedCount: panel.effectAppliedCount("soften")
        }
        // #704 (▶KÉP, `2026-07-17 20 56 55.png`, 1. sor 3. csempéje):
        // a Vignetta EZEN a fülön van, a Lágyítás után és a
        // Képpontnagyítás előtt — nem a „További effektek" gyűjtőfülön,
        // ahová a #422 tette. Ezzel ez a fül is 12 csempés, mint a
        // testvérei.
        // #315: a render/chain.py "vignette" kulcsot vár (kisbetűs,
        // casefold), noha az ini-ben a szűrő neve nagybetűs "Vignette"
        // — az EditController.applyEffect is casefold-ol, ezért itt is
        // kisbetűvel küldjük az effectRequested jelet.
        PanelButton {
            objectName: "effectVignette"
            label: qsTr("Vignette")
            onButtonClicked: if (!panel.tryOpenParamPanel("vignette")) panel.effectRequested("vignette")
            thumbSource: panel.effectThumbSource("vignette")
            appliedCount: panel.effectAppliedCount("vignette")
        }
        PanelButton {
            objectName: "effectPixelate"
            label: qsTr("Pixelate")
            onButtonClicked: if (!panel.tryOpenParamPanel("pixelate", label)) panel.effectRequested("pixelate")
            thumbSource: panel.effectThumbSource("pixelate")
            appliedCount: panel.effectAppliedCount("pixelate")
        }
        PanelButton {
            objectName: "effectFocalZoom"
            label: qsTr("Focal Zoom")
            onButtonClicked: if (!panel.tryOpenParamPanel("focalzoom", label)) panel.effectRequested("focalzoom")
            thumbSource: panel.effectThumbSource("focalzoom")
            appliedCount: panel.effectAppliedCount("focalzoom")
        }
        PanelButton {
            objectName: "effectPencilSketch"
            label: qsTr("Pencil Sketch")
            onButtonClicked: if (!panel.tryOpenParamPanel("pencilsketch", label)) panel.effectRequested("pencilsketch")
            thumbSource: panel.effectThumbSource("pencilsketch")
            appliedCount: panel.effectAppliedCount("pencilsketch")
        }
        PanelButton {
            objectName: "effectNeon"
            label: qsTr("Neon")
            onButtonClicked: if (!panel.tryOpenParamPanel("neon", label)) panel.effectRequested("neon")
            thumbSource: panel.effectThumbSource("neon")
            appliedCount: panel.effectAppliedCount("neon")
        }
        PanelButton {
            objectName: "effectComicize"
            label: qsTr("Comicize")
            onButtonClicked: if (!panel.tryOpenParamPanel("comicize", label)) panel.effectRequested("comicize")
            thumbSource: panel.effectThumbSource("comicize")
            appliedCount: panel.effectAppliedCount("comicize")
        }
        PanelButton {
            objectName: "effectBorder"
            label: qsTr("Border")
            onButtonClicked: if (!panel.tryOpenParamPanel("border", label)) panel.effectRequested("border")
            thumbSource: panel.effectThumbSource("border")
            appliedCount: panel.effectAppliedCount("border")
        }
        PanelButton {
            objectName: "effectDropShadow"
            label: qsTr("Drop Shadow")
            onButtonClicked: if (!panel.tryOpenParamPanel("dropshadow", label)) panel.effectRequested("dropshadow")
            thumbSource: panel.effectThumbSource("dropshadow")
            appliedCount: panel.effectAppliedCount("dropshadow")
        }
        PanelButton {
            objectName: "effectMuseumMatte"
            label: qsTr("Museum Matte")
            onButtonClicked: if (!panel.tryOpenParamPanel("museummatte", label)) panel.effectRequested("museummatte")
            thumbSource: panel.effectThumbSource("museummatte")
            appliedCount: panel.effectAppliedCount("museummatte")
        }
        PanelButton {
            objectName: "effectPolaroid"
            label: qsTr("Polaroid")
            onButtonClicked: if (!panel.tryOpenParamPanel("polaroid", label)) panel.effectRequested("polaroid")
            thumbSource: panel.effectThumbSource("polaroid")
            appliedCount: panel.effectAppliedCount("polaroid")
        }
    }
}

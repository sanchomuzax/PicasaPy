import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 6. füle: azok a Glimmer-effektek, amelyek NEM szerepelnek a
// 3–5. fül igazolt listáján (#464 4. pont).
//
// #422 (felhasználói döntés): ezek eddig a három ismert fülre voltak
// szétosztva — attól azok TÖBB gombot tartalmaztak, mint az eredeti, és nem
// fértek ki. A tulajdonos kérése: külön fülön legyenek. Ezzel a 3–5. fül
// pontosan a `docs/specs/ui-audit-context-menus.md`/#464 szerinti
// 12 · 12 · 11 gombot tartalmazza, és görgetés nélkül kifér.
//
// Amint előkerül egy képernyőkép a Picasa 3. effekt-füléről (#464 4. pont),
// az itt szereplő effektek a helyükre kerülhetnek — addig ez a fül tartja
// őket egyben, elveszés nélkül.
ColumnLayout {
    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    objectName: "effectsColumn4"
    // #583: a nyitott paraméter-alpanel alatt a fül elrejtőzik — enélkül
    // a kettő EGYMÁSRA rajzolódott (a testvér effekt-fülek mintája)
    visible: !panel.modeToolActive && panel.activeTab === 5
             && !panel.paramPanelActive
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
        objectName: "effectsGrid4"
        columns: 3
        // #704: a csempék közti térköz az eredetin MÉRT 2 px
        // (`ui-audit-editor.md` 3.2: osztásköz 88 px, csempe 86 px), nem a
        // korábbi 6. A 3 × 86 + 2 × 2 = 262 px pontosan kiadja a panel
        // 261 képpontos tartalom-oszlopát.
        columnSpacing: 2
        rowSpacing: 2
        Layout.fillWidth: true

        // #516: eddig vezérlő és gomb NÉLKÜLI, de a render/ rétegben
        // MÁR bekötött (chain._HANDLERS) effektek
        PanelButton {
            objectName: "effectMatte"
            label: qsTr("Matte")
            onButtonClicked: if (!panel.tryOpenParamPanel("matte")) panel.effectRequested("matte")
            thumbSource: panel.effectThumbSource("matte")
            appliedCount: panel.effectAppliedCount("matte")
        }
        PanelButton {
            objectName: "effectNightVision"
            label: qsTr("Night Vision")
            onButtonClicked: if (!panel.tryOpenParamPanel("nightvision")) panel.effectRequested("nightvision")
            thumbSource: panel.effectThumbSource("nightvision")
            appliedCount: panel.effectAppliedCount("nightvision")
        }
        PanelButton {
            objectName: "effectLocalContrast"
            label: qsTr("Local Contrast")
            onButtonClicked: if (!panel.tryOpenParamPanel("localcontrast")) panel.effectRequested("localcontrast")
            thumbSource: panel.effectThumbSource("localcontrast")
            appliedCount: panel.effectAppliedCount("localcontrast")
        }
        // #516: eddig vezérlő és gomb NÉLKÜLI, de a render/ rétegben
        // MÁR bekötött (chain._HANDLERS) effektek
        PanelButton {
            objectName: "effectRoundedEdges"
            label: qsTr("Rounded Edges")
            onButtonClicked: if (!panel.tryOpenParamPanel("roundededges")) panel.effectRequested("roundededges")
            thumbSource: panel.effectThumbSource("roundededges")
            appliedCount: panel.effectAppliedCount("roundededges")
        }
        PanelButton {
            objectName: "effectPicnikGrain"
            label: qsTr("Film Grain (Fine)")
            onButtonClicked: if (!panel.tryOpenParamPanel("picnikgrain")) panel.effectRequested("picnikgrain")
            thumbSource: panel.effectThumbSource("picnikgrain")
            appliedCount: panel.effectAppliedCount("picnikgrain")
        }
    }

    Item { Layout.fillHeight: true }
}

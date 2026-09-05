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
            onButtonClicked: if (!panel.tryOpenParamPanel("matte", label)) panel.effectRequested("matte")
            thumbSource: panel.effectThumbSource("matte")
            badge: panel.hasBadge("matte")
        }
        PanelButton {
            objectName: "effectNightVision"
            label: qsTr("Night Vision")
            onButtonClicked: if (!panel.tryOpenParamPanel("nightvision", label)) panel.effectRequested("nightvision")
            thumbSource: panel.effectThumbSource("nightvision")
            badge: panel.hasBadge("nightvision")
        }
        PanelButton {
            objectName: "effectLocalContrast"
            label: qsTr("Local Contrast")
            onButtonClicked: if (!panel.tryOpenParamPanel("localcontrast", label)) panel.effectRequested("localcontrast")
            thumbSource: panel.effectThumbSource("localcontrast")
            badge: panel.hasBadge("localcontrast")
        }
        // #516: eddig vezérlő és gomb NÉLKÜLI, de a render/ rétegben
        // MÁR bekötött (chain._HANDLERS) effektek
        PanelButton {
            objectName: "effectRoundedEdges"
            label: qsTr("Rounded Edges")
            onButtonClicked: if (!panel.tryOpenParamPanel("roundededges", label)) panel.effectRequested("roundededges")
            thumbSource: panel.effectThumbSource("roundededges")
            badge: panel.hasBadge("roundededges")
        }
        PanelButton {
            objectName: "effectPicnikGrain"
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
    }

    Item { Layout.fillHeight: true }
}

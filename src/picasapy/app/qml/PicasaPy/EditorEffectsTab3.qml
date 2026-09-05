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
            badge: panel.hasBadge("boost")
        }
        PanelButton {
            objectName: "effectSoften"
            label: qsTr("Soften")
            onButtonClicked: if (!panel.tryOpenParamPanel("soften", label)) panel.effectRequested("soften")
            thumbSource: panel.effectThumbSource("soften")
            badge: panel.hasBadge("soften")
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
            label: panel.shiftMasodlagos
                   ? qsTr("Matte") : qsTr("Vignette")
            //: #2146: Shifttel a MÁSODLAGOS szűrő (matte) —
            //: az eredeti csempe-táblája (vignette -> matte)
            readonly property string szuro: panel.shiftMasodlagos
                                            ? "matte" : "vignette"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("vignette")
            badge: panel.hasBadge(szuro)
        }
        PanelButton {
            objectName: "effectPixelate"
            label: qsTr("Pixelate")
            //: ⚠️ #2146: a MÉRT Shift-pár `pixelate` -> `picnikfocalpixelate`
            //: lenne, de a `render/chain.py` `_HANDLERS` táblájában
            //: NINCS kezelője — alkalmazni sem tudnánk, a kattintás
            //: `ValueError`-t adna. A Shift-ág ezért NEM épült meg
            //: ezen a csempén; a többi nyolcon igen.
            readonly property string szuro: "pixelate"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("pixelate")
            badge: panel.hasBadge("pixelate")
        }
        PanelButton {
            objectName: "effectFocalZoom"
            label: qsTr("Focal Zoom")
            onButtonClicked: if (!panel.tryOpenParamPanel("focalzoom", label)) panel.effectRequested("focalzoom")
            thumbSource: panel.effectThumbSource("focalzoom")
            badge: panel.hasBadge("focalzoom")
        }
        PanelButton {
            objectName: "effectPencilSketch"
            label: qsTr("Pencil Sketch")
            onButtonClicked: if (!panel.tryOpenParamPanel("pencilsketch", label)) panel.effectRequested("pencilsketch")
            thumbSource: panel.effectThumbSource("pencilsketch")
            badge: panel.hasBadge("pencilsketch")
        }
        PanelButton {
            objectName: "effectNeon"
            label: qsTr("Neon")
            onButtonClicked: if (!panel.tryOpenParamPanel("neon", label)) panel.effectRequested("neon")
            thumbSource: panel.effectThumbSource("neon")
            badge: panel.hasBadge("neon")
        }
        PanelButton {
            objectName: "effectComicize"
            label: qsTr("Comic Book")
            onButtonClicked: if (!panel.tryOpenParamPanel("comicize", label)) panel.effectRequested("comicize")
            thumbSource: panel.effectThumbSource("comicize")
            badge: panel.hasBadge("comicize")
        }
        PanelButton {
            objectName: "effectBorder"
            label: panel.shiftMasodlagos
                   ? qsTr("Rounded Edges") : qsTr("Border")
            //: #2146: Shifttel a MÁSODLAGOS szűrő (roundededges) —
            //: az eredeti csempe-táblája (border -> roundededges)
            readonly property string szuro: panel.shiftMasodlagos
                                            ? "roundededges" : "border"
            onButtonClicked: if (!panel.tryOpenParamPanel(szuro, label)) panel.effectRequested(szuro)
            //: ⚠️ A BÉLYEGKÉP az ELSŐDLEGES effekté marad. Hogy az
            //: eredeti Shifttel a másodlagos előnézetét mutatja-e,
            //: NINCS MÉRVE — és hat másodlagos kulcs a mi
            //: bélyegkép-katalógusunkban sincs benne
            //: (`effect_thumbnails.EFFECT_NAMES`), tehát üres
            //: csempét adna. A render-láncban mind a kilenc
            //: megvan, a HÍVÁS tehát működik.
            thumbSource: panel.effectThumbSource("border")
            badge: panel.hasBadge(szuro)
        }
        PanelButton {
            objectName: "effectDropShadow"
            label: qsTr("Drop Shadow")
            onButtonClicked: if (!panel.tryOpenParamPanel("dropshadow", label)) panel.effectRequested("dropshadow")
            thumbSource: panel.effectThumbSource("dropshadow")
            badge: panel.hasBadge("dropshadow")
        }
        PanelButton {
            objectName: "effectMuseumMatte"
            label: qsTr("Museum Matte")
            onButtonClicked: if (!panel.tryOpenParamPanel("museummatte", label)) panel.effectRequested("museummatte")
            thumbSource: panel.effectThumbSource("museummatte")
            badge: panel.hasBadge("museummatte")
        }
        PanelButton {
            objectName: "effectPolaroid"
            label: qsTr("Polaroid")
            onButtonClicked: if (!panel.tryOpenParamPanel("polaroid", label)) panel.effectRequested("polaroid")
            thumbSource: panel.effectThumbSource("polaroid")
            badge: panel.hasBadge("polaroid")
        }
    }
}

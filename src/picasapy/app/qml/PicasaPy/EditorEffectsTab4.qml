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

    Rectangle {
        Layout.fillWidth: true
        height: 22
        color: Theme.panelHeaderBg
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            text: qsTr("More Effects")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.panelHeaderText
        }
    }

    GridLayout {
        objectName: "effectsGrid4"
        columns: 3
        columnSpacing: 6
        rowSpacing: 6
        Layout.fillWidth: true

        // #315: a render/chain.py "vignette" kulcsot vár (kisbetűs,
        // casefold), noha az ini-ben a szűrő neve nagybetűs "Vignette"
        // — az EditController.applyEffect is casefold-ol, ezért itt is
        // kisbetűvel küldjük az effectRequested jelet.
        PanelButton {
            objectName: "effectVignette"
            label: qsTr("Vignette")
            onButtonClicked: if (!panel.tryOpenParamPanel("vignette", label)) panel.effectRequested("vignette")
            thumbSource: panel.effectThumbSource("vignette")
        }
        // #516: eddig vezérlő és gomb NÉLKÜLI, de a render/ rétegben
        // MÁR bekötött (chain._HANDLERS) effektek
        PanelButton {
            objectName: "effectMatte"
            label: qsTr("Matte")
            onButtonClicked: if (!panel.tryOpenParamPanel("matte", label)) panel.effectRequested("matte")
            thumbSource: panel.effectThumbSource("matte")
        }
        PanelButton {
            objectName: "effectNightVision"
            label: qsTr("Night Vision")
            onButtonClicked: if (!panel.tryOpenParamPanel("nightvision", label)) panel.effectRequested("nightvision")
            thumbSource: panel.effectThumbSource("nightvision")
        }
        PanelButton {
            objectName: "effectLocalContrast"
            label: qsTr("Local Contrast")
            onButtonClicked: if (!panel.tryOpenParamPanel("localcontrast", label)) panel.effectRequested("localcontrast")
            thumbSource: panel.effectThumbSource("localcontrast")
        }
        // #516: eddig vezérlő és gomb NÉLKÜLI, de a render/ rétegben
        // MÁR bekötött (chain._HANDLERS) effektek
        PanelButton {
            objectName: "effectRoundedEdges"
            label: qsTr("Rounded Edges")
            onButtonClicked: if (!panel.tryOpenParamPanel("roundededges", label)) panel.effectRequested("roundededges")
            thumbSource: panel.effectThumbSource("roundededges")
        }
        PanelButton {
            objectName: "effectPicnikGrain"
            label: qsTr("Film Grain (Fine)")
            onButtonClicked: if (!panel.tryOpenParamPanel("picnikgrain", label)) panel.effectRequested("picnikgrain")
            thumbSource: panel.effectThumbSource("picnikgrain")
        }
    }

    Item { Layout.fillHeight: true }
}

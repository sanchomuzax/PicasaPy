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

    Rectangle {
        Layout.fillWidth: true
        height: 22
        color: Theme.panelHeaderBg
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 6
            anchors.verticalCenter: parent.verticalCenter
            text: qsTr("Effects")
            font.pixelSize: Theme.fontSize
            font.bold: true
            color: Theme.panelHeaderText
        }
    }

    // #464 (felhasználói hibajelentés): a rács TÖBB gombot tartalmaz,
    // mint amennyi a panel magasságába fér — vágás/görgetés nélkül a
    // csempék RÁLÓGTAK a panel alján ülő, globális Visszavonás/Újra sorra,
    // és a fül alja levágódott. A rács ezért saját, VÁGOTT görgethető
    // területbe került: ami nem fér ki, az elgörgethető, és semmi nem
    // csúszik a gombsor alá.
    Flickable {
        id: effectsScroll
        objectName: "editorEffectsTab1Scroll"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        contentWidth: width
        contentHeight: effectsGridHolder.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: PicasaScrollBar {}

        Item {
            id: effectsGridHolder
            width: effectsScroll.width
            implicitHeight: childrenRect.height

        GridLayout {
            objectName: "effectsGrid"
            // #537: HÁROM oszlop, mint az eredeti Picasa effekt-fülein
            columns: 3
            columnSpacing: 6
            rowSpacing: 6
            width: effectsScroll.width

            // #315: az eredeti Picasa Effektek fülén az Élesítés az ELSŐ
            // gomb — a render/chain.py "unsharp" handlere ismeri, csak a
            // gombja hiányzott.
            PanelButton {
                objectName: "effectUnsharp"
                label: qsTr("Sharpen")
                onButtonClicked: if (!panel.tryOpenParamPanel("unsharp")) panel.effectRequested("unsharp")
                thumbSource: panel.effectThumbSource("unsharp")
            }
            PanelButton {
                objectName: "effectSepia"
                label: qsTr("Sepia")
                onButtonClicked: if (!panel.tryOpenParamPanel("sepia")) panel.effectRequested("sepia")
                thumbSource: panel.effectThumbSource("sepia")
            }
            PanelButton {
                objectName: "effectBw"
                label: qsTr("B&W")
                onButtonClicked: if (!panel.tryOpenParamPanel("bw")) panel.effectRequested("bw")
                thumbSource: panel.effectThumbSource("bw")
            }
            PanelButton {
                objectName: "effectWarm"
                label: qsTr("Warmify")
                onButtonClicked: if (!panel.tryOpenParamPanel("warm")) panel.effectRequested("warm")
                thumbSource: panel.effectThumbSource("warm")
            }
            PanelButton {
                objectName: "effectGrain2"
                label: qsTr("Film Grain")
                onButtonClicked: if (!panel.tryOpenParamPanel("grain2")) panel.effectRequested("grain2")
                thumbSource: panel.effectThumbSource("grain2")
            }
            PanelButton {
                objectName: "effectTint"
                label: qsTr("Tint")
                onButtonClicked: if (!panel.tryOpenParamPanel("tint")) panel.effectRequested("tint")
                thumbSource: panel.effectThumbSource("tint")
            }
            PanelButton {
                objectName: "effectSat"
                label: qsTr("Saturation")
                onButtonClicked: if (!panel.tryOpenParamPanel("sat")) panel.effectRequested("sat")
                thumbSource: panel.effectThumbSource("sat")
            }
            PanelButton {
                objectName: "effectRadblur"
                label: qsTr("Soft Focus")
                onButtonClicked: if (!panel.tryOpenParamPanel("radblur")) panel.effectRequested("radblur")
                thumbSource: panel.effectThumbSource("radblur")
            }
            PanelButton {
                objectName: "effectGlow2"
                label: qsTr("Glow")
                onButtonClicked: if (!panel.tryOpenParamPanel("glow2")) panel.effectRequested("glow2")
                thumbSource: panel.effectThumbSource("glow2")
            }
            PanelButton {
                objectName: "effectAnsel"
                label: qsTr("Filtered B&W")
                onButtonClicked: if (!panel.tryOpenParamPanel("ansel")) panel.effectRequested("ansel")
                thumbSource: panel.effectThumbSource("ansel")
            }
            PanelButton {
                objectName: "effectRadsat"
                label: qsTr("Focal Saturation")
                onButtonClicked: if (!panel.tryOpenParamPanel("radsat")) panel.effectRequested("radsat")
                thumbSource: panel.effectThumbSource("radsat")
            }
            PanelButton {
                objectName: "effectDirTint"
                label: qsTr("Graduated Tint")
                onButtonClicked: if (!panel.tryOpenParamPanel("dir_tint")) panel.effectRequested("dir_tint")
                thumbSource: panel.effectThumbSource("dir_tint")
            }
            // #315: a render/chain.py "vignette" kulcsot vár (kisbetűs,
            // casefold), noha az ini-ben a szűrő neve nagybetűs "Vignette"
            // — az EditController.applyEffect is casefold-ol, ezért itt is
            // kisbetűvel küldjük az effectRequested jelet.
            PanelButton {
                objectName: "effectVignette"
                label: qsTr("Vignette")
                onButtonClicked: if (!panel.tryOpenParamPanel("vignette")) panel.effectRequested("vignette")
                thumbSource: panel.effectThumbSource("vignette")
            }
        }
    }
    }

}

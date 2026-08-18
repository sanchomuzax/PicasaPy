import QtQuick
import QtQuick.Controls

// A „Képszegélyek" sor a kollázs beállítás-lapján (#946).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` 4.2/2–3. — a felirat (3, 67)
// 239 × 15, a csoport (0, 67) 266 × 89, benne HÁROM 62 × 62-es előnézet
// (34 / 103 / 172, 88 — 69 képpontos osztás).
//
// ⚠️ A csoport MIKOR látszik: kizárólag a `themes.capabilities_for` 9. bitje
// dönti el (`borders`), nem témánkénti `if`. Ugyanezt a helyet foglalja a
// térköz-csúszka, tehát a kettő SOHA nem látszik együtt — ez a lap
// legkönnyebben elrontható tulajdonsága.
//
// Ez a komponens a LAP teljes területét kitölti, és a gyerekeit a spec
// lap-relatív koordinátáival helyezi el: így a fájlban álló számok
// egy az egyben a `.tre` számai, és nem kell fejben átváltani.
Item {
    id: picker

    //: A vezérlő (AppController + CollageMixin).
    property var controller: null

    readonly property string currentBorder:
        picker.controller ? picker.controller.collageBorder : "noborder"

    //: A három keret a `.cxf` kulcsaival (`collage.themes.BORDER_THEMES`).
    readonly property var borders: [
        {
            key: "noborder",
            icon: "icons/collage-border-none.svg",
            name: qsTr("None")
        },
        {
            key: "whiteborder",
            icon: "icons/collage-border-white.svg",
            name: qsTr("White Border")
        },
        {
            key: "polaroid",
            icon: "icons/collage-border-polaroid.svg",
            name: qsTr("Polaroid Camera")
        }
    ]

    Text {
        objectName: "collageBordersLabel"
        x: 3
        y: 67
        width: 239
        height: 15
        text: qsTr("Picture Borders")
        font.pixelSize: Theme.fontSize
        color: Theme.ink
        verticalAlignment: Text.AlignVCenter
    }

    Item {
        objectName: "collageBordersGroup"
        x: 0
        y: 67
        width: 266
        height: 89

        Repeater {
            model: picker.borders
            delegate: Rectangle {
                id: gomb
                required property var modelData
                required property int index
                objectName: "collageBorder" + index
                // a csoport (0, 67) — a gombok a LAPHOZ mérve (34/103/172, 88)
                x: 34 + index * 69
                y: 88 - 67
                width: 62
                height: 62
                color: "transparent"
                border.width: gomb.modelData.key === picker.currentBorder ? 2 : 1
                border.color: gomb.modelData.key === picker.currentBorder
                              ? Theme.thumbSelection
                              : (borderHover.hovered ? Theme.thumbHover
                                                     : Theme.chromeBorder)

                Image {
                    anchors.fill: parent
                    anchors.margins: 2
                    source: gomb.modelData.icon
                    sourceSize.width: 62
                    sourceSize.height: 62
                    fillMode: Image.PreserveAspectFit
                }

                HoverHandler { id: borderHover }
                ToolTip.text: gomb.modelData.name
                ToolTip.visible: borderHover.hovered
                ToolTip.delay: 500

                MouseArea {
                    anchors.fill: parent
                    onClicked: if (picker.controller)
                                   picker.controller.setCollageBorder(gomb.modelData.key)
                }
            }
        }
    }
}

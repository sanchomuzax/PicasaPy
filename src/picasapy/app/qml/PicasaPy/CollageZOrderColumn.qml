import QtQuick
import QtQuick.Controls

// A lap JOBB oldalán lebegő négy rétegsorrend-gomb — `z_order_group`
// (#948, a #920 7/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **2.4**, **2.5** és **4.4**;
// a geometria a `picasa-create-features.md` **1.10.4** táblájából
// (17 × 65; 15 × 15-ös gombok, 16 képpontos osztással).
//
// ## ⚠️ Csak a KÖZÉPSŐ kettő ismétel
//
// A `.tre` `m_autorepeat`-et a `move_up`-ra és a `move_down`-ra tesz — a
// `move_top`/`move_bottom`-ra NEM. Ez nem következetlenség: a két szélső
// parancs idempotens (a legfelső képet nem lehet még feljebb tenni),
// ismételve tehát csak villogna, miközben a felhasználó azt hinné,
// történik valami.
//
// A csoport `m_hidden`: kijelöléskor jön elő (ld. `CollageSnapColumn`).
Item {
    id: column
    objectName: "collageZOrderColumn"

    property var controller: null

    implicitWidth: 17
    implicitHeight: 65
    width: implicitWidth
    height: implicitHeight

    readonly property var capabilities:
        column.controller && column.controller.collageCapabilities
            ? column.controller.collageCapabilities : ({})

    readonly property int selectionCount:
        column.controller && column.controller.collageSelection
            ? column.controller.collageSelection.length : 0

    visible: column.selectionCount > 0
             && column.capabilities.selection === true

    //: A négy parancs; az `autoRepeat` a `.tre` `m_autorepeat`-je.
    readonly property var commands: [
        {
            name: "collageMoveTop",
            icon: "icons/collage-move-top.svg",
            hint: qsTr("Move picture to the top of the pile"),
            repeats: false
        },
        {
            name: "collageMoveUp",
            icon: "icons/collage-move-up.svg",
            hint: qsTr("Move picture up in the pile"),
            repeats: true
        },
        {
            name: "collageMoveDown",
            icon: "icons/collage-move-down.svg",
            hint: qsTr("Move picture down in the pile"),
            repeats: true
        },
        {
            name: "collageMoveBottom",
            icon: "icons/collage-move-bottom.svg",
            hint: qsTr("Move picture to the bottom of the pile"),
            repeats: false
        }
    ]

    function run(name) {
        if (!column.controller)
            return
        if (name === "collageMoveTop")
            column.controller.moveSelectionTop()
        else if (name === "collageMoveUp")
            column.controller.moveSelectionUp()
        else if (name === "collageMoveDown")
            column.controller.moveSelectionDown()
        else if (name === "collageMoveBottom")
            column.controller.moveSelectionBottom()
    }

    Repeater {
        model: column.commands
        delegate: PicasaButton {
            required property var modelData
            required property int index

            objectName: modelData.name
            x: 1
            y: 1 + 16 * index
            width: 15
            height: 15
            padding: 0
            horizontalPadding: 0
            autoRepeat: modelData.repeats
            contentItem: Item {
                Image {
                    objectName: modelData.name + "Icon"
                    anchors.centerIn: parent
                    width: 15
                    height: 15
                    source: modelData.icon
                    sourceSize.width: 15
                    sourceSize.height: 15
                    fillMode: Image.PreserveAspectFit
                }
            }
            ToolTip.text: modelData.hint
            ToolTip.visible: hovered
            ToolTip.delay: 500
            onClicked: column.run(modelData.name)
        }
    }
}

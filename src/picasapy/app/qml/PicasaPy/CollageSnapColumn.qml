import QtQuick
import QtQuick.Controls

// A lap BAL oldalán lebegő négy forgatás-igazító gomb —
// `snap_rotation_group` (#948, a #920 7/8 lépcsője).
//
// Spec: `docs/specs/kollazs-panel-ui-spec.md` **2.4**, **4.4** és **7.5**;
// a geometria a `picasa-create-features.md` **1.10.4** táblájából
// (17 × 65; 15 × 15-ös gombok, 16 képpontos osztással).
//
// ## Alapból REJTETT
//
// A `.tre` a csoportra `m_hidden`-t tesz: kijelöléskor jön elő. A régi
// olvasat (a vászon abszolút 383-as x-e) TERVEZŐI alapállás — a kényszer
// (`m_centerY` + `XConstraint 1, 0, -2`) a LAP bal széléhez köti, és a
// képernyőképen sem látszik, amíg nincs kijelölés.
//
// ## ⚠️ A „270 fok" felirat mögött −90,0 áll
//
// A négy parancs értékét a vezérlő `snapRotation` slotja adja
// (`canvas.snap_theta`), nem ez a fájl: a `snap_9` **−90,0 fokot** tárol,
// hogy a `.cxf` a windowsos Picasával oda-vissza olvasható maradjon.
Item {
    id: column
    objectName: "collageSnapColumn"

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

    // `m_hidden` + a maszk 4. bitje (spec 2.4): akkor látszik, ha van
    // kijelölt kép és a téma egyáltalán enged kijelölést.
    visible: column.selectionCount > 0
             && column.capabilities.selection === true

    //: A négy parancs a `canvas.SNAP_COMMANDS` kulcsaival.
    readonly property var commands: [
        {
            key: "snap_12",
            icon: "icons/collage-snap-12.svg",
            hint: qsTr("Align rotation to straight up")
        },
        {
            key: "snap_3",
            icon: "icons/collage-snap-3.svg",
            hint: qsTr("Align rotation to 90 CW")
        },
        {
            key: "snap_6",
            icon: "icons/collage-snap-6.svg",
            hint: qsTr("Align rotation to 180 CW")
        },
        {
            key: "snap_9",
            icon: "icons/collage-snap-9.svg",
            hint: qsTr("Align rotation to 270 CW")
        }
    ]

    //: `snap_12` → `collageSnap12` … a spec 4.4 objectName-jei.
    function nameFor(key) {
        return "collageSnap" + key.substring(5)
    }

    Repeater {
        model: column.commands
        delegate: PicasaButton {
            required property var modelData
            required property int index

            objectName: column.nameFor(modelData.key)
            x: 1
            y: 1 + 16 * index
            width: 15
            height: 15
            padding: 0
            horizontalPadding: 0
            // A forgatás a maszk függvénye (`snapRotation` ugyanezt nézi):
            // ahol a téma nem forgat, a gomb halvány, nem néma.
            enabled: column.capabilities.rotate === true
            contentItem: Item {
                Image {
                    objectName: column.nameFor(modelData.key) + "Icon"
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
            onClicked: if (column.controller)
                           column.controller.snapRotation(modelData.key)
        }
    }
}

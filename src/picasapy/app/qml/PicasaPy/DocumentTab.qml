import QtQuick

// Egyetlen fül a dokumentum-fülsávban (#944, a Kollázs-panel 3/8. szelete).
//
// A méret az eredetiből MÉRT érték: `panelroot/collagetab` (390, 8) 125 × 21
// (`docs/specs/kollazs-panel-ui-spec.md` 3.1). A 29 képpontos sávban a fül
// tehát ALULRA igazodik — a 8 képpontos felső hézag a sáv magasságából és a
// fül magasságából adódik, nem külön beállítás.
//
// A fül SEMMIT nem tud a gazdájáról: nem hivatkozik vissza a sávra, csak
// jelez (`activateRequested`, `closeRequested`). Így a sáv marad az egyetlen
// hely, ahol a bezárási út el van döntve — az ✕ és az `Esc` ugyanoda fut be.
Item {
    id: ful

    //: a fülön megjelenő cím (a rögzített fülnél „Könyvtár”)
    property string title: ""
    //: ez a fül az aktív dokumentum?
    property bool active: false
    //: van-e a fülön ✕ (a könyvtár füle nem zárható)
    property bool closable: false
    //: mentetlen módosítás — a fülön csillag jelzi
    property bool modified: false
    //: az `objectName`-ek előtagja; a funkcionális tesztek szerződése
    property string namePrefix: "documentTab"

    signal activateRequested()
    signal closeRequested()

    objectName: ful.namePrefix

    implicitWidth: 125
    implicitHeight: 21
    width: ful.implicitWidth
    height: ful.implicitHeight

    // Az aktív fül a TARTALOM színét veszi fel (mintha összeérne az alatta
    // lévő lappal), az inaktív a sáv krómszínét.
    Rectangle {
        anchors.fill: parent
        radius: 2
        color: ful.active ? Theme.canvasBg : Theme.chromeBg
        border.width: 1
        border.color: Theme.chromeBorder
    }

    // A fül egésze kattintható. A záró ✕ egérterülete KÉSŐBB következik,
    // ezért az takarja ezt — az ✕-re kattintás nem vált fület.
    MouseArea {
        anchors.fill: parent
        onClicked: ful.activateRequested()
    }

    Text {
        objectName: ful.namePrefix + "Label"
        anchors.left: parent.left
        anchors.leftMargin: 8
        anchors.right: bezaro.left
        anchors.rightMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        elide: Text.ElideRight
        text: ful.modified ? ful.title + " *" : ful.title
        color: Theme.ink
        font.pixelSize: Theme.fontSize
        font.bold: ful.active
    }

    // A záró ✕ — két elforgatott, 1 képpontos vonal, hogy ne függjön
    // betűkészlettől (a felület betűtípusa még nyitott kérdés, ld. Theme.qml).
    Item {
        id: bezaro
        objectName: ful.namePrefix + "Close"
        anchors.right: parent.right
        anchors.rightMargin: 5
        anchors.verticalCenter: parent.verticalCenter
        width: ful.closable ? 13 : 0
        height: ful.closable ? 13 : 0
        visible: ful.closable

        Repeater {
            model: [45, -45]
            Rectangle {
                required property int modelData
                anchors.centerIn: parent
                width: 9
                height: 1
                rotation: modelData
                color: bezaroEger.containsMouse ? Theme.ink : Theme.textGray
            }
        }

        MouseArea {
            id: bezaroEger
            anchors.fill: parent
            hoverEnabled: true
            onClicked: ful.closeRequested()
        }
    }
}

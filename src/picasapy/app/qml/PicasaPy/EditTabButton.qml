import QtQuick
import QtQuick.Controls

// Egy fülgomb a szerkesztő fülsávjában (#338): saját rajzolású ikon,
// buboréksúgó, és a #318 kompatibilitási okból megtartott (de rejtett)
// felirat-Text.
//
// Kattintásra `panel.activeTab` vált; az aktív fül vastagabb kerettel és
// eltérő háttérrel emelkedik ki.
//
// #338: a szöveges fülcímkék a szűk (230px-es) panelen összeszorultak
// („Gyakori javítások" két sorba tört, „Finomhangol…" levágódott) — az
// eredeti Picasa is IKONOS füleket használ (ld. ui-audit-editor.md 1. szak.).
// A jelentést az `EditTabIcon` adja; a teljes nevet a ToolTip mutatja
// hoverre. A `tbtnLabel` Text a #318-as tördelés-teszt és a hozzáférhetőség
// kedvéért MEGMARAD, de rejtve — a szűk fülsávon nem fér el mindkettő.
//
// #496: az `EditorPanel.qml` inline `component`-jéből önálló fájlba emelve.
// A `panel` a gazda EditorPanel — a kattintás ezen át állítja az
// `activeTab`-ot, ahogy korábban a beágyazott komponens tette.
Rectangle {
    id: tbtn
    //: a gazda EditorPanel — a kattintás ezen át állítja az aktív fület
    required property var panel
    required property int tabIndex
    required property string label
    // "wrench" | "sun" | "brush" — melyik ikont rajzolja az EditTabIcon
    required property string iconKind
    property color iconAccent: Theme.iconInk
    property color iconFleck: "transparent"
    // #571: jelzőpont a fülön — a megnyitott kép láncában van olyan
    // effekt, ami erre a fülre tartozik; a felhasználónak tudnia kell,
    // hol nézze meg
    property bool marked: false
    // #741: a fülsáv MÉRT magassága 25 képpont (`respack.yt`: a fülgombok
    // y 45..70). A tényleges `x`/`width`/`height` a gazda `EditorTabBar`-tól
    // jön, amely hézag nélkül osztja szét a tartalom-oszlopot — ezért itt
    // nincs layout-kötés, csak implicit alapérték.
    implicitHeight: 25
    implicitWidth: 39
    color: panel.activeTab === tabIndex ? Theme.contentPanel : Theme.panelHeaderBg
    border.width: 1
    border.color: panel.activeTab === tabIndex ? Theme.selectionBlue : Theme.chromeBorder

    EditTabIcon {
        objectName: tbtn.objectName ? tbtn.objectName + "Icon" : ""
        anchors.centerIn: parent
        // #741: az eredeti fülikonok y 49..68 a 25 képpontos sávban, azaz
        // 16–19 képpont magasak (fülönként 15 × 16 … 25 × 19). A korábbi
        // 22 × 22 nem fért volna a sávba.
        width: 20; height: 18
        kind: tbtn.iconKind
        strokeColor: Theme.iconInk
        accentColor: tbtn.iconAccent
        fleckColor: tbtn.iconFleck
    }
    Rectangle {
        objectName: tbtn.objectName ? tbtn.objectName + "Mark" : ""
        visible: tbtn.marked
        width: 6; height: 6; radius: 3
        color: Theme.picasaGreen
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 3
    }
    // #318 kompatibilitás: rejtett, de a régi tördelés-logikával
    // számolt felirat-Text — a `truncated` így sosem igaz, mert a
    // szélessége nem szorítja a fülgomb keskeny sávjához.
    Text {
        id: tbtnLabel
        objectName: tbtn.objectName ? tbtn.objectName + "Label" : ""
        visible: false
        text: tbtn.label
        font.pixelSize: Theme.fontSize - 3
        wrapMode: Text.WordWrap
        maximumLineCount: 2
        width: Math.max(120, implicitWidth)
    }
    MouseArea {
        id: tabMouse
        anchors.fill: parent
        hoverEnabled: true
        onClicked: panel.activeTab = tbtn.tabIndex
    }
    ToolTip.text: tbtn.label
    ToolTip.visible: tabMouse.containsMouse
    ToolTip.delay: 400
}

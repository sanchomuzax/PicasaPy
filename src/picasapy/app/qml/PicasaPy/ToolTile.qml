import QtQuick
import QtQuick.Layouts

// Egy eszköz-csempe a szerkesztő 1. fülén (#405/#411): nagy, saját rajzú
// SVG-ikon + felirat, „benyomott" (aktív) állapottal.
//
// #496: korábban az EditorPanel.qml-en BELÜL, inline `component`-ként élt —
// a fájl így a 800 soros elv több mint kétszerese volt. A típusnév és a
// használat változatlan (a modul `qmldir`-je regisztrálja), csak a
// definíció költözött.
Item {
    id: tile
    required property string toolName
    required property string label
    // a "icons/<iconFile>.svg" fájlnév (kiterjesztés nélkül) — a
    // panel.qmlDir szerinti "icons/" mappában, ld. #361/#411
    required property string iconFile
    property bool active: false
    property bool tileEnabled: true
    signal activated(string tool)

    Layout.fillWidth: true
    // #405/#411: nagyobb csempe — az ikon a Picasa-mintát követve
    // jóval nagyobb helyet foglal, mint a korábbi 40×30-as PNG-ikon
    Layout.preferredHeight: 84
    // az öröklött enabled is számít (#103): videónál a PhotoViewer az
    // egész panelt tiltja — a csempe ilyenkor vizuálisan is szürkül
    enabled: tile.tileEnabled
    opacity: tile.enabled ? 1 : 0.4

    Rectangle {
        anchors.fill: parent
        radius: 3
        // #314: sem "#cfe4f7", sem "#e8eef4" nem olvasható sötét
        // témában (fix világos árnyalatok) — a jelző-kék tokenből
        // (Theme.selectionBlue) származtatott áttetsző rétegre váltva
        // mindkét témán kontrasztos marad, a hover halványabb az aktívnál.
        color: tile.active
               ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                         Theme.selectionBlue.b, 0.45)
               : (tileMouse.containsMouse && tile.tileEnabled
                  ? Qt.rgba(Theme.selectionBlue.r, Theme.selectionBlue.g,
                            Theme.selectionBlue.b, 0.18)
                  : "transparent")
        border.width: tile.active ? 1 : 0
        border.color: Theme.selectionBlue
    }

    // #411: az ikon területe — SAJÁT rajzú SVG, MINDIG betöltve (nincs
    // aszinkron várakozás/helyőrző-eset, mint a fotó-bélyegképeknél).
    Item {
        id: tileThumbBox
        anchors.top: parent.top
        anchors.topMargin: 4
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 8
        height: 54

        Image {
            id: tileIconImg
            objectName: tile.objectName ? tile.objectName + "Icon" : ""
            anchors.centerIn: parent
            // #411: az ikonok FEKVŐ (3:2) arányúak, mint az eredeti
            // Picasa 44x29-es gombképei — négyzetes dobozban a rajz
            // zsugorodna/torzulna, ezért 3:2 méret + PreserveAspectFit.
            width: 54; height: 36
            fillMode: Image.PreserveAspectFit
            source: "icons/" + tile.iconFile + ".svg"
            sourceSize: Qt.size(108, 72)
            smooth: true
        }
    }
    Text {
        anchors.top: tileThumbBox.bottom
        anchors.topMargin: 4
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width - 2
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        maximumLineCount: 2
        lineHeight: 0.9
        text: tile.label
        font.pixelSize: Theme.fontSize - 2
        color: Theme.textDark
    }
    MouseArea {
        id: tileMouse
        anchors.fill: parent
        hoverEnabled: true
        onClicked: tile.activated(tile.toolName)
    }
}

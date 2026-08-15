import QtQuick

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

    // #741: a MÉRT geometria (`docs/specs/szerkeszto-panel-meretek.md` 3.):
    // a csempekép PONTOSAN 44 × 30 képpont, az oszlopköz 81, a sorköz 64.
    //
    // A 64 a bináris felbontásában: 30 (csempekép) + 14 (felirat) + 20
    // (hézag a következő sorig). Korábban a cella 94 képpont magas volt, és
    // a `rowSpacing: 10`-zel együtt 104 képpontos sorközt adott a 64
    // helyett — három sor × ~40 képpont többlet, ez tolta le a panel alját
    // (#741).
    //
    // A cellát a gazda rács méretezi és helyezi el (`EditorTabCommonFixes`),
    // ezért itt csak az implicit alapérték áll.
    //: a csempekép mérete — `respack.yt` rétegtéglalap (44 × 30)
    readonly property int kepSzelesseg: 44
    readonly property int kepMagassag: 30

    implicitWidth: 80
    implicitHeight: 64
    // az öröklött enabled is számít (#103): videónál a PhotoViewer az
    // egész panelt tiltja — a csempe ilyenkor vizuálisan is szürkül
    enabled: tile.tileEnabled
    opacity: tile.enabled ? 1 : 0.4

    // #741: a kiemelés a CSEMPEKÉP dobozát fedi, nem az egész cellát — az
    // eredetiben a kattintható réteg maga a 44 × 30-as kép, a felirat külön
    // elem alatta. (Kattintani ettől függetlenül a felirattal együtt a
    // teljes cellán lehet, ld. a MouseArea-t lent.)
    Rectangle {
        anchors.fill: tileThumbBox
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
        anchors.horizontalCenter: parent.horizontalCenter
        // #741: a csempekép doboza PONTOSAN akkora, mint a kép — a mérés
        // ebből olvassa ki az oszlop- és sorközt (a cella körülötte áll).
        width: tile.kepSzelesseg
        height: tile.kepMagassag

        Image {
            id: tileIconImg
            objectName: tile.objectName ? tile.objectName + "Icon" : ""
            anchors.fill: parent
            // #411/#741: az ikonok FEKVŐ arányúak, mint az eredeti Picasa
            // 44 × 30-as gombképei — négyzetes dobozban a rajz zsugorodna
            // vagy torzulna, ezért fekvő méret + PreserveAspectFit.
            fillMode: Image.PreserveAspectFit
            source: "icons/" + tile.iconFile + ".svg"
            sourceSize: Qt.size(88, 60)
            smooth: true
        }
    }
    Text {
        id: tileLabel
        objectName: tile.objectName ? tile.objectName + "Label" : ""
        // #741: a felirat a csempekép ALATT, középre zárva
        // (`m_buttonfontCbelow` → `YConstraint 0, 1, 0`).
        anchors.top: tileThumbBox.bottom
        anchors.topMargin: 2
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width
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

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő 1. füle: „Gyakori javítások" — az eredeti Picasa
// csavarkulcs-fülének csempe-rácsa és a Derítőfény-csúszka.
//
// #496: az `EditorPanel.qml`-ből kiemelve. A fájl 800 sor fölé nőtt, és
// minden fül-módosítás ugyanazt a fájlt írta — a többi fül (Finomhangolás,
// effekt-fülek, Régi effektek) mintáját követve ez is önálló komponens.
// A viselkedés VÁLTOZATLAN: a láthatóságot és a horgonyokat — ahogy a
// testvér-füleknél is — a gazda `EditorPanel` adja meg a használat helyén.
ColumnLayout {
    id: fixesRoot

    //: a gazda EditorPanel — az állapot és a jelzések gazdája
    required property var panel

    // #337: a Derítőfény csúszkája a Finomhangolás fülön is ott van, és a
    // kettőt szinkronban kell tartani — a gazda ezen az aliason keresztül
    // éri el (a `EditorFinetunePanel` `fillSlider`-ének mintája).
    property alias fillSlider: fixesFillSlider

    objectName: "toolsColumn"
    // tiltott panel (videó a nézőben, #103): az egész oszlop halvány
    opacity: panel.enabled ? 1 : 0.45
    anchors.margins: 10
    spacing: 8

    // #405: a szöveges "Common Fixes"/"Gyakori javítások" fejléc TÖRÖLVE
    // — az eredeti Picasán a fül alatt NINCS ilyen felirat, a csempék
    // rögtön a fülsáv alatt kezdődnek (ld. #405 issue 4. pontja).

    // #464: a gombkészlet és a sorrend a tulajdonos KÉPERNYŐKÉPÉRŐL
    // (Picasa 3.9, „Gyakori javítások" fül) — ez FELÜLÍRJA a jegy
    // szövegében szereplő korábbi sorrendet, ami feljegyzésből készült:
    //
    //     Vágás · Kiegyenesítés · Vörösszem
    //     Jó napom van · Automatikus kontraszt · Automatikus szín
    //     Retusálás · Szöveg
    //     [kis kép] Derítőfény-csúszka
    //
    // A képen NINCS „Kreatív Kit" csempe (a jegy tévesen sorolta fel), a
    // Derítőfény pedig NEM a gombok közé ékelődik, hanem MINDEGYIK alatt
    // ül. Az egygombos javítás lenyomás után elhalványul (tiltottá
    // válik) — a csempe képe nem változik, csak áttetsző lesz.
    //
    // #741: a rács osztásköze a MÉRT érték
    // (`docs/specs/szerkeszto-panel-meretek.md` 3.): oszlopköz 81, sorköz
    // 64 képpont. A cella 80 × 64, közte 1 képpont — így a 44 képpontos
    // csempekép EGÉSZ számú, 18 képpontos eltolással ül a cella közepén, és
    // nem csúszik el fél képponttal a Derítőfény-sorhoz képest. Korábban a
    // cella 94 magas volt, és a `rowSpacing: 10`-zel együtt 104 képpontos
    // sorközt adott a 64 helyett — ez tolta le a panel alját.
    //
    // A 6 képpontos bal eltolás a fül 10 képpontos margójával együtt épp
    // az eredeti x 37 / 118 / 199 csempe-oszlopokat adja (13 + 6 + 18).
    Item {
        id: toolGrid
        objectName: "fixesToolGrid"
        // A rács a SAJÁT szélességéből méretezi a cellákat, és a csempéket
        // közvetlen `x`/`width` kötéssel helyezi el — nem elrendezés-motorral.
        // Kétszeresen is ez a helyes: az eredeti geometria pontosan adott
        // (nincs mit „elosztani"), és a kötés AZONNAL követi az
        // átméretezést, míg egy beágyazott layout csak a következő
        // rendezési körben — a #656 gépi ellenőr épp ezt a késést fogta meg.
        Layout.leftMargin: 6
        Layout.fillWidth: true
        //: 3 × 80 + 2 × 1 — ennél szélesebb sosem lesz, keskenyebb lehet
        Layout.maximumWidth: 242
        Layout.preferredHeight: 3 * 64

        //: a cellák közti 1 képpont: 80 + 1 = a mért 81 képpontos oszlopköz
        readonly property int cellaKoz: 1
        readonly property int cellaSzelesseg:
            Math.max(44, Math.floor((toolGrid.width - 2 * toolGrid.cellaKoz) / 3))
        readonly property int cellaMagassag: 64

        function cellaX(index) {
            return (index % 3) * (toolGrid.cellaSzelesseg + toolGrid.cellaKoz)
        }
        function cellaY(index) {
            return Math.floor(index / 3) * toolGrid.cellaMagassag
        }

        ToolTile {
            x: toolGrid.cellaX(0); y: toolGrid.cellaY(0)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolCrop"
            toolName: "crop"; label: qsTr("Crop"); iconFile: "vagas"
            active: panel.cropActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            x: toolGrid.cellaX(1); y: toolGrid.cellaY(1)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolTilt"
            toolName: "tilt"; label: qsTr("Straighten")
            iconFile: "kiegyenesites"
            active: panel.tiltActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            x: toolGrid.cellaX(2); y: toolGrid.cellaY(2)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolRedeye"
            toolName: "redeye"; label: qsTr("Redeye"); iconFile: "vorosszem"
            active: panel.redeyeActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        // egygombos javítások (#116): nincs "benyomva" állapot — a gomb
        // tiltott (halvány), amíg ugyanez a szűrő a lánc utolsó eleme
        ToolTile {
            x: toolGrid.cellaX(3); y: toolGrid.cellaY(3)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolEnhance"
            toolName: "enhance"; label: qsTr("I'm Feeling Lucky")
            iconFile: "jo-napom-van"
            tileEnabled: panel.enhanceEnabled
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            x: toolGrid.cellaX(4); y: toolGrid.cellaY(4)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolAutolight"
            toolName: "autolight"; label: qsTr("Auto Contrast")
            iconFile: "auto-kontraszt"
            tileEnabled: panel.autolightEnabled
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            x: toolGrid.cellaX(5); y: toolGrid.cellaY(5)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolAutocolor"
            toolName: "autocolor"; label: qsTr("Auto Color")
            iconFile: "auto-szin"
            tileEnabled: panel.autocolorEnabled
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            x: toolGrid.cellaX(6); y: toolGrid.cellaY(6)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolRetouch"
            toolName: "retouch"; label: qsTr("Retouch")
            iconFile: "retusalas"
            active: panel.retouchActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            x: toolGrid.cellaX(7); y: toolGrid.cellaY(7)
            width: toolGrid.cellaSzelesseg
            height: toolGrid.cellaMagassag
            objectName: "editToolText"
            toolName: "text"; label: qsTr("Text"); iconFile: "szoveg"
            active: panel.textActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
    }

    // #337/#405/#411: Kitöltő fény — az eredeti Picasa Alapvető
    // javítások fülén az ikonrács alatt EZ AZ EGYETLEN csúszka, és a
    // napi használat egyik legfontosabb eszköze. Ugyanaz a beállítás,
    // mint a Finomhangolás fülén: a két csúszka egymást követi
    // (fillLightMoved). A címke a csúszka FÖLÖTT, kompakt (#405 6.
    // pont), a saját ikonnal kiegészítve (#411 9. ikonja: deritofeny).
    // #411 (felhasználói visszajelzés): az eredetiben az ikon és a
    // csúszka EGY EGYSÉG — a képecske közvetlenül a csúszka mellett,
    // azonos sorban ül, a felirat a csúszka fölött. Korábban nálunk a
    // 16x16-os ikon a felirat mellé volt tűzve, a csúszka pedig külön
    // sorban futott — az összetartozás nem látszott.
    //
    // #741: a MÉRT geometria (spec 3. szakasz vége) — a kis kép 44 × 30 és
    // PONTOSAN a csempe-rács 1. oszlopával egy vonalban (x 37) áll, a
    // csúszka 127 × 27 (x 101..228), a felirat a csúszka FÖLÖTT. A fül
    // 10 képpontos bal margójához képest ez 24 képpont eltolás (13 + 24 =
    // 37), a kép és a csúszka között 20 képpont hézag (81 → 101).
    RowLayout {
        Layout.fillWidth: false
        Layout.leftMargin: 24
        spacing: 20
        Image {
            objectName: "fixesFillLightIcon"
            source: "icons/deritofeny.svg"
            fillMode: Image.PreserveAspectFit
            sourceSize: Qt.size(88, 60)
            Layout.preferredWidth: 44
            Layout.preferredHeight: 30
        }
        ColumnLayout {
            Layout.fillWidth: false
            Layout.preferredWidth: 127
            spacing: 2
            Label {
                objectName: "fixesFillLightLabel"
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("Fill Light")
                font.pixelSize: Theme.fontSize - 1
                color: Theme.textGray
            }
            PicasaSlider {
                id: fixesFillSlider
                objectName: "fixesFillSlider"
                Layout.fillWidth: true
                Layout.preferredHeight: 27
                from: 0; to: 1; value: 0
                onValueChanged: panel.fillLightMoved(value)
                onPressedChanged: if (!pressed) panel.fillLightCommitted()
            }
        }
    }

}

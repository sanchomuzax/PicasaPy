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
    GridLayout {
        columns: 3
        columnSpacing: 4
        rowSpacing: 10
        Layout.fillWidth: true

        ToolTile {
            objectName: "editToolCrop"
            toolName: "crop"; label: qsTr("Crop"); iconFile: "vagas"
            active: panel.cropActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            objectName: "editToolTilt"
            toolName: "tilt"; label: qsTr("Straighten")
            iconFile: "kiegyenesites"
            active: panel.tiltActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            objectName: "editToolRedeye"
            toolName: "redeye"; label: qsTr("Redeye"); iconFile: "vorosszem"
            active: panel.redeyeActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        // egygombos javítások (#116): nincs "benyomva" állapot — a gomb
        // tiltott (halvány), amíg ugyanez a szűrő a lánc utolsó eleme
        ToolTile {
            objectName: "editToolEnhance"
            toolName: "enhance"; label: qsTr("I'm Feeling Lucky")
            iconFile: "jo-napom-van"
            tileEnabled: panel.enhanceEnabled
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            objectName: "editToolAutolight"
            toolName: "autolight"; label: qsTr("Auto Contrast")
            iconFile: "auto-kontraszt"
            tileEnabled: panel.autolightEnabled
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            objectName: "editToolAutocolor"
            toolName: "autocolor"; label: qsTr("Auto Color")
            iconFile: "auto-szin"
            tileEnabled: panel.autocolorEnabled
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
            objectName: "editToolRetouch"
            toolName: "retouch"; label: qsTr("Retouch")
            iconFile: "retusalas"
            active: panel.retouchActive
            onActivated: (tool) => panel.handleToolClick(tool)
        }
        ToolTile {
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
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        Image {
            objectName: "fixesFillLightIcon"
            source: "icons/deritofeny.svg"
            fillMode: Image.PreserveAspectFit
            sourceSize: Qt.size(108, 72)
            Layout.preferredWidth: 54
            Layout.preferredHeight: 36
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label {
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
                from: 0; to: 1; value: 0
                onValueChanged: panel.fillLightMoved(value)
                onPressedChanged: if (!pressed) panel.fillLightCommitted()
            }
        }
    }

}

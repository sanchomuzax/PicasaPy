import QtQuick
import QtQuick.Controls

// A Kollázs-panel fülsávja: „Beállítások" és „Képek (N)" (#945).
//
// Geometria a `docs/specs/picasa-create-features.md` 1.10-ből: a sáv
// 276 × 25, a két fül egyenként 92 × 25, egymás mellett hézag nélkül
// (3, 25) és (95, 25) abszolút — a `collageTabBase` tetejétől 5 px-re
// (a `.tre` `tabs: m_offsetL + YConstraint 0,0,5` kényszere).
//
// A második fül felirata FUTÁSIDŐBEN frissül a klip-darabszámmal
// (`collageUI::tab2_title`), minden felvétel/törlés után.
//
// ⚠️ CSAPDA — két felirat-forrás van, és a rossz a feltűnőbb.
// A felület leírófájljában a fül STATIKUS címkéje `Clips` / magyarul
// „Képek" (`picasa-create-features.md` 1.10.6). A futó program ezt
// AZONNAL felülírja a „Klipek (%d)" formátummal; a felülíró rutint
// (`0x0083b890`) négy hely hívja, köztük maga a panelépítés. Ezért áll a
// felhasználó képernyőképén „Klipek (80)".
//
// A magyar fordítás tehát „Klipek (%1)" — a statikus „Képek" NEM jelenik
// meg soha, és a kettő keveréke („Képek (%1)") olyan felirat, ami az
// eredeti programban nem létezik. (Ebbe a #945 első köre beleesett.)
Item {
    id: bar
    objectName: "collageTabBar"

    //: Hány kép van a Klipek lapon — a fülfelirat futásidőben frissül.
    property int clipCount: 0
    property int currentIndex: 0

    implicitWidth: 276
    implicitHeight: 25

    readonly property int tabWidth: 92

    Row {
        anchors.left: parent.left
        anchors.top: parent.top
        spacing: 0

        CollagePanelTabButton {
            objectName: "collageSettingsTabButton"
            width: bar.tabWidth
            height: bar.height
            text: qsTr("Settings")
            checked: bar.currentIndex === 0
            onClicked: bar.currentIndex = 0
        }
        CollagePanelTabButton {
            objectName: "collageClipsTabButton"
            width: bar.tabWidth
            height: bar.height
            // A darabszám a felirat RÉSZE, nem külön jelvény — az eredeti
            // a teljes fülfeliratot írja újra.
            text: qsTr("Clips (%1)").arg(bar.clipCount)
            checked: bar.currentIndex === 1
            onClicked: bar.currentIndex = 1
        }
    }
}

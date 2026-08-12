import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A szerkesztő FÜLSÁVJA (#20, #328, #338, #422, #571): hét egyenlő
// szélességű, ikonos fül. Csak „tools" módban látszik — vágásnál nincs
// értelme.
//
// #496: az `EditorPanel.qml`-ből kiemelve — a fájl a 800 soros korlát fölé
// nőtt. A gombok, a sorrend és az ikonok VÁLTOZATLANOK; a láthatóságot és a
// horgonyokat a gazda adja meg a használat helyén.
RowLayout {
    id: tabBarRoot

    //: a gazda EditorPanel — a fülgombok ezen át állítják az aktív fület
    required property var panel

    spacing: 0

    // #338: csavarkulcs — az eredeti Picasa 1. füle
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabFixes"
        tabIndex: 0
        label: qsTr("Common Fixes")
        iconKind: "wrench"
    }
    // #338: nap — az eredeti Picasa 2. füle
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabFinetune"
        tabIndex: 1
        label: qsTr("Fine Tuning")
        iconKind: "sun"
    }
    // #338: sima ecset — a törzs-effektek (3. fül, nincs szín-minta)
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabEffects"
        tabIndex: 2
        label: qsTr("Effects")
        iconKind: "brush"
        iconAccent: Theme.iconInk
    }
    // #328/#338: 4. fül — ZÖLD ecset ("kreatív effektek"), a docs/specs/
    // ui-audit-editor.md leírása szerint zöld táj-mintával megkülönböztetve.
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabEffects2"
        tabIndex: 3
        label: qsTr("Creative")
        iconKind: "brush"
        iconAccent: Theme.picasaGreen
        iconFleck: Qt.darker(Theme.picasaGreen, 1.4)
    }
    // #328/#338: 5. fül — KÉK ecset ("művészi effektek"), kék ég-mintával.
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabEffects3"
        tabIndex: 4
        label: qsTr("Artistic")
        iconKind: "brush"
        iconAccent: Theme.brandBlue
        iconFleck: Qt.lighter(Theme.brandBlue, 1.6)
    }
    // #422 (felhasználói döntés): 6. fül — azok a Glimmer-effektek,
    // amelyek NEM szerepelnek a 3–5. fül igazolt listáján. Külön fülön,
    // hogy a három ismert fül pontosan az eredeti gombkészletét
    // tartalmazza (és görgetés nélkül kiférjen).
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabEffects4"
        tabIndex: 5
        label: qsTr("More Effects")
        iconKind: "brush"
        iconAccent: Theme.textGray
    }
    // #571 (felhasználói döntés: „Régi effektek"): 7. fül — a Picasa
    // motorjában benne maradt, de a 3.9 felületén NEM elérhető szűrők.
    // TUDATOS eltérés az eredetitől, ld. EditorLegacyTab.qml.
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabLegacy"
        tabIndex: 6
        label: qsTr("Legacy Effects")
        iconKind: "brush"
        iconAccent: Theme.chromeBorder
        marked: tabBarRoot.panel.legacyEffectsPresent
    }
}

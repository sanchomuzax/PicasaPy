import QtQuick

// A szerkesztő FÜLSÁVJA (#20, #328, #338, #422, #571, #741): hét ikonos
// fül, hézag nélkül. Csak „tools" módban látszik — vágásnál nincs értelme.
//
// #496: az `EditorPanel.qml`-ből kiemelve — a fájl a 800 soros korlát fölé
// nőtt. A gombok, a sorrend és az ikonok VÁLTOZATLANOK; a láthatóságot és a
// horgonyokat a gazda adja meg a használat helyén.
//
// #741: a sáv NEM `RowLayout` többé, hanem sima `Item`, amelyben a fülek
// SAJÁT `x`/`width`-tel ülnek. Kétszeresen is ez a helyes:
//
//  * az eredeti fülek pontosan kitöltik a tartalom-oszlopot, hézag nélkül —
//    a layout törtszámú osztása ezt nem tudja garantálni;
//  * egy layout-gyerek szélessége NEM függhet a layout saját szélességétől
//    (körkörös hivatkozás). Amíg `RowLayout` volt, a fülek keskenyebb
//    panelen a 276-ra számolt méretüket tartották meg, és 20 képponttal
//    kilógtak a sávból (a #656 gépi ellenőr fogta meg).
Item {
    id: tabBarRoot

    //: a gazda EditorPanel — a fülgombok ezen át állítják az aktív fület
    required property var panel

    //: hány fül van — a tulajdonosi kivétel (hét, az eredeti öt helyett)
    readonly property int tabCount: 7

    // #741: a fülsáv MÉRT magassága 25 képpont (`respack.yt`: `tabs`,
    // 276 × 25). A gazda csak vízszintesen horgonyozza, a magasság itt dől el.
    readonly property int savMagassag: 25
    implicitHeight: tabBarRoot.savMagassag
    height: tabBarRoot.savMagassag

    // #741: az eredeti öt fül hézag nélkül tölti ki a 276 képpontos
    // oszlopot (55 + 55 + 56 + 55 + 55). Hét fülre ugyanez a szabály
    // `39 · 39 · 40 · 39 · 40 · 39 · 40 = 276`-ot ad.
    //
    // A képlet a KUMULÁLT határok egészre csonkítása: a szomszédos fülek
    // határa így mindig ugyanaz a szám, tehát sem hézag, sem átfedés nem
    // keletkezhet, és az összegük pontosan a sáv szélessége.
    function tabHatar(index) {
        return Math.floor(index * tabBarRoot.width / tabBarRoot.tabCount)
    }
    function tabWidth(index) {
        return tabBarRoot.tabHatar(index + 1) - tabBarRoot.tabHatar(index)
    }

    // #338: csavarkulcs — az eredeti Picasa 1. füle
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabFixes"
        tabIndex: 0
        x: tabBarRoot.tabHatar(0)
        width: tabBarRoot.tabWidth(0)
        height: tabBarRoot.height
        label: qsTr("Common Fixes")
        iconKind: "wrench"
    }
    // #338: nap — az eredeti Picasa 2. füle
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabFinetune"
        tabIndex: 1
        x: tabBarRoot.tabHatar(1)
        width: tabBarRoot.tabWidth(1)
        height: tabBarRoot.height
        label: qsTr("Fine Tuning")
        iconKind: "sun"
    }
    // #338: sima ecset — a törzs-effektek (3. fül, nincs szín-minta)
    EditTabButton {
        panel: tabBarRoot.panel
        objectName: "editTabEffects"
        tabIndex: 2
        x: tabBarRoot.tabHatar(2)
        width: tabBarRoot.tabWidth(2)
        height: tabBarRoot.height
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
        x: tabBarRoot.tabHatar(3)
        width: tabBarRoot.tabWidth(3)
        height: tabBarRoot.height
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
        x: tabBarRoot.tabHatar(4)
        width: tabBarRoot.tabWidth(4)
        height: tabBarRoot.height
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
        x: tabBarRoot.tabHatar(5)
        width: tabBarRoot.tabWidth(5)
        height: tabBarRoot.height
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
        x: tabBarRoot.tabHatar(6)
        width: tabBarRoot.tabWidth(6)
        height: tabBarRoot.height
        label: qsTr("Legacy Effects")
        iconKind: "brush"
        iconAccent: Theme.chromeBorder
        marked: tabBarRoot.panel.legacyEffectsPresent
    }
}

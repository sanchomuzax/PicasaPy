import QtQuick
import QtQuick.Layouts
import PicasaPy

// A szerkesztő GLOBÁLIS Visszavonás/Újra sora (#464), külön fájlban a
// #3220 óta: az `EditorPanel.qml` 1295 sorra nőtt, a projekt saját 800-as
// korlátja fölé, és ez a sor önmagában 120 sor volt — a mért geometriája
// és a hozzá tartozó indoklások miatt.
//
// ⚠️ Viselkedés-azonos kiemelés: az `objectName`-ek (`editorGlobalUndoRow`,
// `editUndoButton`, `editRedoButton`), a mért méretek és a jelzések
// változatlanok. A gazda adja be a `panel`-t és a `tabArea`-t, valamint a
// horgonyokat — a fájl bevett mintája szerint („a láthatóságot és a
// horgonyokat MINDIG a gazda adja meg a használat helyén").
// ---------------- #464: GLOBÁLIS Visszavonás/Újra ----------------
//
// Az eredeti Picasában a pár a panel ALJÁN ül, és NEM fülhöz kötött —
// minden eszközben elérhető. Korábban mind az öt fül saját (azonos)
// gombpárt rajzolt; most egyetlen, a panel aljához horgonyzott sor van,
// és a fül-oszlopok EFÖLÖTT érnek véget (`anchors.bottom`).
// #641: a sor a LÁTHATÓ terület alján ül, mindig. A #628 „lejjebb
// tolódik, ha nem fér el" ága MEGSZŰNT: az eredetiben nincs ilyen, és a
// gyakorlatban azt eredményezte, hogy a sor kicsúszott a képernyőről —
// a felhasználó egyáltalán nem látta a Visszavonás/Újra gombokat.
//
// Ha szűkös a hely, a FÜL TARTALMA veszít, nem a gombsor: a
// Visszavonás/Újra a szerkesztés visszacsinálásának egyetlen útja, egy
// levágott csempesor ennél sokkal kisebb baj. Hogy ez az ág egyáltalán
// ne forduljon elő, az ablak minimális magassága elbírja a panel
// `implicitHeight`-jét (Main.qml).
RowLayout {
    id: undoRow
    objectName: "editorGlobalUndoRow"
    //: a gazda adja be — a sor a panel állapotából számol, de nem ismeri
    //: a panel BELSŐ felépítését (#3220)
    property Item panel
    property Item tabArea
    // #741: a MÉRT geometria — a két gomb x 7..139 és x 144..276,
    // vagyis 132 képpont széles mindkettő, 5 képpont hézaggal, és
    // együtt kitöltik a 276-os tartalom-oszlopot
    // (7 + 132 + 5 + 132 = 276). A sor szélessége ezért 269, a bal
    // margó 7, a jobb 4 — a `fillWidth` innen PONTOSAN 132-t oszt.
    // #616: a sor a FÜL TARTALMA ALATT ül, nem a panel aljára szegezve.
    //
    // A #628/#641/#703 kör azt érte el, hogy a sor mindig a LÁTHATÓ
    // terület alján legyen — ez megakadályozta, hogy kicsússzon a
    // képernyőről, de egy nagy képernyőn (1920×1080, maximalizált ablak)
    // a panel 832 képpont magas, a „Gyakori javítások" fül tartalma
    // viszont csak ~300: a gombsor így **több száz képponttal a tartalom
    // alatt**, egy nagy üres szürke mező túloldalán jelent meg. A
    // felhasználó ezt joggal olvasta úgy, hogy „nincsenek is ott a
    // gombok" — a képernyőképén a fül alatt csak üres terület látszik.
    //
    // Az eredeti Picasában a panel FIX méretű, ezért a gombsor mindig
    // közvetlenül a tartalom alatt van. Nálunk az ablak átméretezhető,
    // ezért a kettő közül a KISEBBIK helyre tesszük:
    //   - a tartalom alja + egy kis rés (ez az eredeti viselkedés), de
    //   - sosem lejjebb, mint a látható terület alja (ez a #641 garancia).
    // Így a gombsor ott van, ahol a felhasználó keresi, és szűk ablakban
    // sem csúszik ki.
    y: {
        var lathatoAlja = panel.visibleHeight - height - 10
        if (!tabArea.visible)
            return Math.max(0, lathatoAlja)
        var tartalomAlatt = tabArea.y + panel.tabContentHeight + 8
        return Math.max(0, Math.min(lathatoAlja, tartalomAlatt))
    }
    spacing: 5
    opacity: panel.enabled ? 1 : 0.45

    //: #2494/#405: a pár EGYFORMA magas, és a magasságot MI számoljuk,
    //: nem a Layout `fillHeight`-je — az Qt-verziófüggően viselkedik
    //: (a CI-n a gomb 28 maradt a kétsoros felirat alatt is, helyben
    //: megnőtt).
    //:
    //: ⚠️ 28 → **26**, és ez NEM mond ellent a #741-nek. A respack
    //: `filter_undo`/`filter_redo` téglalapja (132 × 28) a HELY, amit a
    //: gomb az elrendezésben elfoglal; a KIRAJZOLT gombkeret ennél
    //: minden oldalon 1 képponttal kisebb. Mindkettő MÉRVE a tulajdonos
    //: 1:1 felvételén (`141421.jpg`): a két gomb bal keretének
    //: osztásköze 137 = 132 + 5 hézag (a respack pontosan ennyit mond),
    //: a rajzolt keret viszont 130 × 26. Nálunk ez a `Rectangle` MAGA a
    //: rajzolt keret — nincs külön hely és külön kép —, tehát a
    //: látható értéket kell felvennie: 26.
    //: #2597: a MÉRT magasság, rögzítve. Korábban `Math.max(26, …a két
    //: gomb kért magassága…)` állt itt, és a kért magasság a PLATFORM
    //: betűmetrikáját hordozta: a CI windows-lába 32 képpontot mért (a
    //: mért eredeti 26 helyett), a hosszabb effektneveknél pedig itt is
    //: 36-ra nőtt. Az eredeti a feliratot szorítja a gombhoz, nem
    //: fordítva — ezt a `PanelButton.rogzitettMagassag` végzi.
    readonly property real gombMagassag: 26

    PanelButton {
        id: editUndoBtn
        //: #2597: a gomb a mért 26 képpontot veszi fel, és a felirat
        //: igazodik hozzá (betűillesztés + legfeljebb két sor) — a
        //: magasság így nem függ a platform betűjétől.
        rogzitettMagassag: undoRow.gombMagassag
        objectName: "editUndoButton"
        label: panel.undoLabel
        buttonEnabled: panel.undoAvailable
        //: #741/#2494: a mért, KIRAJZOLT gombmagasság 26 (a respack
        //: 132 × 28-as téglalapja a HELY, ld. a `gombMagassag`-nál).
        //: ALSÓ korlát, nem felső — a felirat itt az effekt
        //: nevét is tartalmazza („Visszavonás: Jó napom van"), ami két
        //: sorra tör, és a rögzített 28 nem engedett neki helyet: a
        //: második sor a gomb alsó keretén kezdődött és 5 képponttal
        //: lelógott (MÉRVE, `235707.jpg`). Egysoros feliratnál a
        //: mért 28 marad, mert a `PanelButton` magától kisebbet adna.
        Layout.preferredHeight: undoRow.gombMagassag
        //: a `minimumHeight` KÖTELEZŐ a Layoutnak — a preferált érték
        //: egymagában elveszhet egy késleltetett elrendezési körben
        //: (mérve: a gomb 28 maradt a kétsoros felirat alatt is)
        Layout.minimumHeight: undoRow.gombMagassag
        onButtonClicked: panel.undoRequested()
    }
    PanelButton {
        id: editRedoBtn
        //: #2597: a gomb a mért 26 képpontot veszi fel, és a felirat
        //: igazodik hozzá (betűillesztés + legfeljebb két sor) — a
        //: magasság így nem függ a platform betűjétől.
        rogzitettMagassag: undoRow.gombMagassag
        objectName: "editRedoButton"
        label: panel.redoLabel
        buttonEnabled: panel.redoAvailable
        // #405: egyenlő szélességű pár (nem egy keskeny + egy kitöltő)
        //: #741/#2494: a mért, KIRAJZOLT gombmagasság 26 (a respack
        //: 132 × 28-as téglalapja a HELY) — ALSÓ korlát, a párja miatt is: a két gomb
        //: egy sorban ül, a magasabbik szabja meg a sor magasságát.
        Layout.preferredHeight: undoRow.gombMagassag
        //: a `minimumHeight` KÖTELEZŐ a Layoutnak — a preferált érték
        //: egymagában elveszhet egy késleltetett elrendezési körben
        //: (mérve: a gomb 28 maradt a kétsoros felirat alatt is)
        Layout.minimumHeight: undoRow.gombMagassag
        onButtonClicked: panel.redoRequested()
    }
}

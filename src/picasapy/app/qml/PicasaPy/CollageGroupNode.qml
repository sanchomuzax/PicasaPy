import QtQuick

// A kollázs CSOPORT-ELEME — `collagepanel/groupnode` (#1170).
//
// Spec: `docs/specs/picasa-kollazs-felulet.md` **2.** (a kapu) és **2/b**
// (mit rajzol).
//
// ## Mi ez, és miért külön elem
//
// A képesség-maszk **6. bitje** (`0x00860470`) azt kapcsolja, hogy a
// csoport-csomópont a szokásos, szülőhöz kötött bejárás helyett **külön
// overlay-ágba** kerüljön (`+0x219` jelző, `0x009e2aa5` bejáró). A bit
// pontosan a három RÁCS-témánál áll: `picturegrid`, `framegrid`,
// `regulargrid`. A Képkupacnál nem — ott a gyűrű (`CollageRing`) a
// kijelölés jele.
//
// Nálunk ez felületi szinten annyit jelent, hogy az elem a képek FÖLÖTT,
// külön rétegben rajzolódik: `z` = `_CSOPORT_Z`, ami magasabb minden
// `CollageNode`-énál (azok `nodeIndex`-et, húzás közben 9999-et adnak).
// Nem lehet a csomópontok gyereke: a csomópont el van forgatva és a
// mérete a képé, a csoport-keret viszont TENGELYPÁRHUZAMOS, és több képet
// fog össze.
//
// ## A rajz — kimérve, nem tervezve
//
// `0x0085fd70`: a csomópont színe `0xFFF85E0F`, `AARRGGBB` sorrendben
// (a bájtsorrend külön kalibrálva, spec 2/b.3) → `#F85E0F`, erős narancs.
// A `ShapeDraw<RectSampler>` `+0x04` mezője **2**, és a raszterező
// képpont-ciklusa (`0x007dec00`) a belső képpontokat **kihagyja** — tehát
// **körvonal, nem kitöltés**, 2 képpont vastagsággal (spec 2/b.5). A
// rutin élsimít is, ezért kell az `antialiasing`.
Rectangle {
    id: csoport

    //: A lap (`CollageSheet`) — tőle jön a képesség-térkép és a mértékegység.
    property var sheet: null

    objectName: "collageGroupNode"

    //: A vezérlő téglalapja LAPEGYSÉGBEN; üres térkép = nincs csoport.
    //: A `!== undefined` őr a #305 szabálya: a geometriai teszt-kettősök
    //: nem viselik ezt a property-t.
    readonly property var box:
        (sheet && sheet.controller && sheet.controller.collageGroupRect !== undefined)
        ? sheet.controller.collageGroupRect : ({})

    //: A `width` egyben a térkép jelenlétének jelzője: üres térképnél
    //: `undefined`. (A vezérlő legalább két kijelölt képnél ad téglalapot —
    //: a küszöb a `collage_model.GROUP_MIN_SELECTION`.)
    readonly property bool vanDoboz: box.width !== undefined

    //: A 6. bit. Témánkénti `if` NINCS: a képesség-térkép dönt.
    //:
    //: ⚠️ A `sheet.capabilities` MAGA is lehet `undefined`, nem csak a
    //: mezője (#305): a lap `controller ? controller.collageCapabilities : ({})`
    //: alakban kötődik, és a geometriai teszt-kettősöknél (#945) van
    //: vezérlő, de nincs rajta `collageCapabilities` — a feltétel igaz ágán
    //: `undefined` jön vissza. A kettős őr enélkül 52 tesztet buktatott
    //: „Cannot read property 'group_overlay' of undefined"-dal.
    readonly property bool engedelyezett:
        (sheet && sheet.capabilities)
        ? sheet.capabilities.group_overlay === true : false

    readonly property real egyseg: sheet ? sheet.unit : 0

    //: Minden `CollageNode` fölött (`nodeIndex`, `Alt` esetén 9999) és a
    //: gyűrűk fölött (10000 + index) is. A kettő sosem látszik együtt — a
    //: gyűrű a Képkupacé, a csoport-keret a rácsoké —, de a réteg így
    //: akkor is egyértelmű, ha valaki a maszkot átírja.
    readonly property int _CSOPORT_Z: 20000

    visible: engedelyezett && vanDoboz && egyseg > 0
    z: _CSOPORT_Z

    x: vanDoboz ? box.x * egyseg : 0
    y: vanDoboz ? box.y * egyseg : 0
    width: vanDoboz ? box.width * egyseg : 0
    height: vanDoboz ? box.height * egyseg : 0

    color: "transparent"
    border.width: 2
    border.color: "#f85e0f"
    antialiasing: true
}

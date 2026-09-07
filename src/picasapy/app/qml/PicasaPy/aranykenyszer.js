// A szerkesztő kijelölő-téglalapjának ARÁNY-KÉNYSZERE (#891).
//
// Miért külön fájl (a `lasso.js` / `scroll.js` / `groups.js` mintája): a
// szabályt HÁROM felület használja — a vágó (`CropOverlay.qml`), a
// vörösszem (`PhotoViewer.qml` `redeyeOverlay`-e) és az arc-hozzáadás
// (`FacesOverlay.qml`) —, az eredetiben is EGYETLEN kezelő
// (`ytSelectionDragHandler`, vftable `0x008da768`) szolgálja ki mindhármat.
//
// Az eredeti a húzás közben három vizsgálatot futtat EGYMÁS UTÁN, és
// mindegyik felülírja az előzőt (`0x00a6fa47`–`0x00a6fa97`):
//
//     push 0x10  ; VK_SHIFT    → fld1        → 1,0
//     push 0x11  ; VK_CONTROL  → [0xcf4cd0]  → 1,3333333
//     push 0x12  ; VK_MENU     → [0xcf3ec4]  → 1,5
//
// tehát **Alt üt Ctrl-t, Ctrl üt Shiftet**. Felengedéskor a mező
// nullázódik (`0x00a6fae6`) — a kényszer PILLANATNYI, nem ragadós mód.
//
// ⚠️ A szorzó NEM abszolút oldalarány. Az alkalmazó (`0x00a6ef20`) a
// `[eax+0x10] / [eax]` hányadost — a KÉP saját szélesség/magasság arányát
// — szorozza meg vele. Shifttel tehát a kijelölés a fénykép arányát veszi
// fel, NEM négyzetet; négyzetet csak négyzetes képen ad.
//
// A függvények tiszta függvények: a bemenetet nem mutálják, új objektumot
// adnak vissza.
.pragma library

/** Shift: a kép saját aránya (szorzó 1,0). */
var SHIFT_SZORZO = 1.0
/** Ctrl: a kép aránya × 4/3 (`0xcf4cd0` = 1,3333333). */
var CTRL_SZORZO = 4 / 3
/** Alt: a kép aránya × 3/2 (`0xcf3ec4` = 1,5). */
var ALT_SZORZO = 1.5

/** A lenyomott módosítókhoz tartozó SZORZÓ; 0 = nincs kényszer.
 *
 * A három vizsgálat sorrendje az eredetiét követi — ezért ír felül az
 * Alt mindent, és ezért veszít a Shift a Ctrl ellen.
 */
function szorzo(shift, ctrl, alt) {
    var ertek = 0
    if (shift) ertek = SHIFT_SZORZO
    if (ctrl) ertek = CTRL_SZORZO
    if (alt) ertek = ALT_SZORZO
    return ertek
}

/** A kényszerített CÉL-ARÁNY (szélesség / magasság); 0 = szabad húzás.
 *
 * A `dobozSzelesseg`/`dobozMagassag` a kép ténylegesen kirajzolt területe
 * — az átfedések pontosan ekkorák, ezért a hányadosuk a kép saját aránya.
 */
function celArany(dobozSzelesseg, dobozMagassag, szorzoErtek) {
    if (szorzoErtek <= 0 || dobozSzelesseg <= 0 || dobozMagassag <= 0)
        return 0
    return (dobozSzelesseg / dobozMagassag) * szorzoErtek
}

/** A módosítókból közvetlenül cél-arányt számol (a hívók kényelmére). */
function celAranyModositokbol(dobozSzelesseg, dobozMagassag, shift, ctrl, alt) {
    return celArany(dobozSzelesseg, dobozMagassag, szorzo(shift, ctrl, alt))
}

/** A húzás téglalapja `{x, y, width, height}` alakban, a KEZDŐPONTHOZ
 * horgonyozva.
 *
 * `arany > 0` esetén a magasságot a szélességből származtatjuk — a
 * horgony a lenyomás pontja marad, a szabad sarok mozog. (Az eredeti
 * horgony-választása — `0x00a6ef7c` négy összehasonlítása — még nyitott
 * kérdés a jegyben; a lenyomási pont a legkevésbé meglepő választás, és
 * ez egyezik a `CropOverlay` eddigi, rögzített arányra írt viselkedésével.)
 */
function aranyraIgazit(x1, y1, x2, y2, arany) {
    var w = Math.abs(x2 - x1)
    var h = Math.abs(y2 - y1)
    if (arany > 0)
        h = w / arany
    return {
        x: (x2 < x1) ? x1 - w : x1,
        y: (y2 < y1) ? y1 - h : y1,
        width: w,
        height: h
    }
}

/** A téglalapot a KÉP dobozán belülre zárja, az arányt megtartva.
 *
 * A származtatott oldal (a magasság) kifuthat a képből — ilyenkor nem
 * elég levágni, mert azzal az arány romlana el: a levágás UTÁN a
 * szélességet is vissza kell venni. A vágó eddig is így számolt, a
 * vörösszem és az arc-téglalap most ugyanezt kapja.
 */
function dobozbaZar(r, arany, dobozSzelesseg, dobozMagassag) {
    var x = Math.max(0, Math.min(dobozSzelesseg, r.x))
    var y = Math.max(0, Math.min(dobozMagassag, r.y))
    var w = Math.min(r.width, dobozSzelesseg - x)
    var h = Math.min(r.height, dobozMagassag - y)
    if (arany > 0) {
        w = Math.min(w, h * arany)
        h = w / arany
    }
    return { x: x, y: y, width: w, height: h }
}

/** Egy lépésben: módosítókból arány, abból a dobozba zárt téglalap. */
function huzottTeglalap(x1, y1, x2, y2, dobozSzelesseg, dobozMagassag,
                        shift, ctrl, alt) {
    var arany = celAranyModositokbol(dobozSzelesseg, dobozMagassag,
                                     shift, ctrl, alt)
    return dobozbaZar(aranyraIgazit(x1, y1, x2, y2, arany), arany,
                      dobozSzelesseg, dobozMagassag)
}

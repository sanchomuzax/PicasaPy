// A kék infó-sáv szövegének LEÉPÜLÉSE, ha nem fér ki (#2581).
//
// Miért külön fájl (a `lasso.js` / `scroll.js` / `groups.js` mintája): ez
// aritmetika, nem felület — külön olvasható, külön mérhető, és a
// `TrayBar.qml` így marad a 800 soros határ alatt. A szélesség-mérést a
// hívó adja be függvényként, ezért a szabály betűtől függetlenül próbálható.
//
// ## A MÉRÉS (docs/specs/kek-info-sav.md 9.)
//
// Két felvétel, UGYANAZ a fájl, UGYANAZ a nézet, más ablakszélesség:
//
//   1920 képpontos ablak: `AI > JonasBen_…0a71328.png` teljesen kiírva
//   ~960 képpontos ablak: `JonasBen_he_sits_...0a71328.png`
//
// Ebből három dolog következik:
//
//   1. a szabály KÉPPONT-alapú (karakterszabály mellett ugyanúgy csonkulna
//      mindkettő — a szomszéd mezők képpontra azonosak, tehát a betű is az);
//   2. a leépülés KÉTLÉPCSŐS: előbb a `mappa > ` előtag marad el, és csak
//      utána vág a névbe (a vágott alak NEM az előtaggal kezdődik);
//   3. a vágás a név KÖZEPÉN történik, három ASCII ponttal — a binárisban
//      nincs `…` (U+2026) literál, és nincs `PathCompactPathEx` sem.
//
// ⚠️ A fej/far arány JELÖLT, nem szerződés. A mért 84 / 142 = 59,2 % a
// 60/40-be fér bele (85,2/56,8), miközben az 50/50 (71/71) és a 2/3–1/3
// (94,7/47,3) a méréssel összeegyeztethetetlen. Egyetlen csonkolt mintából
// ennél többet nem lehet állítani.

.pragma library

/** A mezők elválasztója a sávban — a `formatting.photo_info_text` írja. */
var MEZO_ELVALASZTO = "   "

/** A mappa és a fájlnév közötti jel a `viewerInfo`-ban. */
var ELOTAG_JEL = " > "

/** A vágás jele: HÁROM ASCII PONT, nem `…` (a binárisban `…` nincs). */
var HAROMPONT = "..."

/** A fej aránya a névre maradó szélességből — MÉRT jelölt (ld. fent). */
var FEJ_ARANY = 0.6

/** Levágja a `mappa > ` előtagot az első mezőről, ha van.
 *
 * A keresés az ELSŐ mezőre korlátozódik: a `>` szerepelhet a dátumban vagy
 * egy címkében is, és a mappa-előtag mindig a név előtt áll.
 */
function elotagNelkul(szoveg) {
    var mezok = szoveg.split(MEZO_ELVALASZTO)
    var valto = mezok[0].indexOf(ELOTAG_JEL)
    if (valto < 0)
        return szoveg
    mezok[0] = mezok[0].substring(valto + ELOTAG_JEL.length)
    return mezok.join(MEZO_ELVALASZTO)
}

/** A név KÖZEPÉN vág, hogy az egész sor beférjen `hely` képpontba.
 *
 * `szelesseg(sztring)` a hívó betűjével mér. A fej és a far a MÉRT
 * arányban (`FEJ_ARANY`) osztozik a névre maradó helyen; a far végét
 * megtartjuk, tehát a kiterjesztés megmarad — a felvételen is
 * `…0a71328.png` áll.
 */
function nevKozepenVagva(szoveg, hely, szelesseg) {
    var mezok = szoveg.split(MEZO_ELVALASZTO)
    var nev = mezok[0]
    if (nev.length <= HAROMPONT.length)
        return szoveg          // rövidebb a jelnél — nincs mit nyerni
    var maradek = mezok.slice(1).join(MEZO_ELVALASZTO)
    var maradekHely = maradek === ""
        ? 0 : szelesseg(MEZO_ELVALASZTO + maradek)
    var nevHely = hely - maradekHely - szelesseg(HAROMPONT)
    if (nevHely <= 0) {
        // Ennyire szűk helyen a NÉV már semmit nem tud adni: marad a puszta
        // hárompont. A többi mezőhöz nem nyúlunk — az eredeti sem rövidíti
        // őket, ott a sáv clipje vág (a `.tre` `infotext_clip`-je, #1934).
        mezok[0] = HAROMPONT
        return mezok.join(MEZO_ELVALASZTO)
    }

    var fejHely = nevHely * FEJ_ARANY
    var farHely = nevHely - fejHely

    var fej = ""
    for (var i = 1; i <= nev.length; ++i) {
        if (szelesseg(nev.substring(0, i)) > fejHely)
            break
        fej = nev.substring(0, i)
    }
    var far = ""
    for (var j = 1; j <= nev.length - fej.length; ++j) {
        if (szelesseg(nev.substring(nev.length - j)) > farHely)
            break
        far = nev.substring(nev.length - j)
    }
    // Ha egyetlen karakter sem fér el egyik oldalon sem, marad a puszta
    // jel — ilyenkor is RÖVIDÜLNIE kell, különben a hívó azt hinné, hogy
    // a szöveg befér (a `test_a_vegeredmeny_BEFER` ezt a hibát fogta meg).
    mezok[0] = fej + HAROMPONT + far
    return mezok.join(MEZO_ELVALASZTO)
}

/** A sáv szövege `hely` képpontnyi helyre, a MÉRT kétlépcsős leépüléssel.
 *
 * 1. elfér → változatlanul;
 * 2. nem fér el → elmarad a `mappa > ` előtag;
 * 3. még mindig nem → a név közepén vág.
 */
function lecsokkentve(szoveg, hely, szelesseg) {
    if (szoveg === "" || hely <= 0)
        return szoveg
    if (szelesseg(szoveg) <= hely)
        return szoveg

    var rovid = elotagNelkul(szoveg)
    if (rovid !== szoveg && szelesseg(rovid) <= hely)
        return rovid

    return nevKozepenVagva(rovid, hely, szelesseg)
}

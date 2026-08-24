// Kijelölés-segédfüggvények (#150-ben kiemelve a Main.qml-ből).
// Tiszta függvények: a bemenő listát nem mutálják, új tömböt adnak
// vissza — a hívó (Main.qml) írja vissza a window.selectedIndexes-be.
.pragma library

// Ctrl+katt: az index hozzávétele/elvétele a kijelölésből.
function toggled(selected, index) {
    var s = selected.slice()
    var pos = s.indexOf(index)
    if (pos >= 0) s.splice(pos, 1); else s.push(index)
    return s
}

// Shift+katt: zárt tartomány a horgony és a cél között (irányfüggetlen).
function range(anchor, index) {
    var lo = Math.min(anchor, index)
    var hi = Math.max(anchor, index)
    var r = []
    for (var k = lo; k <= hi; ++k) r.push(k)
    return r
}

// Ctrl+A: minden sor kijelölése.
function allRows(count) {
    var r = []
    for (var k = 0; k < count; ++k) r.push(k)
    return r
}

// A kijelölt sorok: a több-kijelölés, vagy ha az nincs, az utoljára
// kattintott kép (ha van).
function effectiveRows(selectedIndexes, selectedIndex) {
    if (selectedIndexes.length > 0)
        return selectedIndexes
    return selectedIndex >= 0 ? [selectedIndex] : []
}

// #135: a kijelölés stabil (fotó-id) alapú újraképzése háttér-modell-
// frissítés (reset) után — a sor-indexek elcsúszhatnak (beszúrás/törlés/
// átrendeződés), de az id-k nem. A `rowOfId` a modell aktuális
// id→sor leképezése (Python-oldali szereplet); a törölt/eltűnt fotók
// (-1) kiesnek a kijelölésből, a többi a friss sorára kerül.
function remapByIds(ids, rowOfId) {
    var result = []
    for (var k = 0; k < ids.length; ++k) {
        var row = rowOfId(ids[k])
        if (row >= 0) result.push(row)
    }
    return result
}

// #422: „Kiválasztás megfordítása" (Ctrl+I, a mappa-kontextusmenü és a
// Szerkesztés menü tétele): ami ki volt jelölve, az nem lesz, és fordítva.
// A `count` a rács jelenlegi sorszáma — a kimenet mindig növekvő sorrendű.
function inverted(selected, count) {
    var result = []
    for (var row = 0; row < count; ++row)
        if (selected.indexOf(row) === -1) result.push(row)
    return result
}

// #426: „Csillagozottak kijelölése" (Picasa `ID_SELECTSTAR`, Szerkesztés
// menü) — a JELENLEGI nézet csillagos sorai, növekvő sorrendben. A
// `starAt` a modell (`PhotoGridModel`) Slotja — tiszta lekérdezés, nem
// mutál. Szándékosan NEM a Mappák panel „Csillagozott" nézet-szűrője
// (`controller.showStarred()`): az a NÉZETET cseréli, ez csak KIJELÖL.
function starredRows(count, starAt) {
    var result = []
    for (var row = 0; row < count; ++row)
        if (starAt(row)) result.push(row)
    return result
}

// #892/#1222: a Shift+NYÍL EGYESÉVEL bővít — az `index` hozzáadása a
// kijelöléshez, ha még nincs benne. Növekvő sorrendű új tömböt ad, a
// bemenetet nem mutálja.
//
// ⚠️ SZÁNDÉKOSAN nem a `range`. Az eredeti léptető mag (`0x00717eb0`) a
// horgonyból (`[this+0x390]`) lép egyet, Shift esetén a leszedő ágat
// KIHAGYJA (`0x0071805c`), az új elemet kijelöli (`0x007180d6`), és a
// végén a horgonyt is a friss elemre írja (`0x007180da`). Nincs
// „tartomány", csak halmozás — ezért az IRÁNYVÁLTÁS nem zsugorít:
// visszafelé előbb a már kijelölteken sétál vissza, azon túl pedig a
// másik irányba bővít.
//
// A horgony az eredetiben KÉT szerepet visz egyetlen mezőben: a léptetés
// töve ÉS a Shift-KATTINTÁS tartományának töve. Nálunk ez két mező: a
// léptetésé a kurzor (`selectedIndex`, ez lép minden nyílütésnél), a
// kattintásé a `selectionAnchor` (#897, az marad). A látható eredmény
// ugyanaz, mert az eredeti tartomány-magja (`0x00716ae0`) csak KIJELÖL —
// a tartományon kívül már kijelölteket nem szedi le.
function withAdded(selected, index) {
    if (selected.indexOf(index) >= 0) return selected.slice()
    return selected.concat([index]).sort(function (a, b) { return a - b })
}

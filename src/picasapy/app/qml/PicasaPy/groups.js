// A képfolyam MAPPACSOPORT-aritmetikája — tiszta függvények (#1417).
//
// Miért külön fájl (a `lasso.js` / `scroll.js` / `selection.js` mintája,
// #150): ez indexszámítás a `feedGroups` modell fölött, nem felület —
// külön olvasható, külön mérhető, és a `LightboxFeed.qml` így marad a
// 800 soros határ alatt.
//
// A függvények a bemenetet NEM mutálják, új értéket adnak vissza.
.pragma library

/** Hányadik mappacsoportba esik a `row` sorindex; `-1`, ha egyikbe sem.
 *
 * A csoportok a feedben egymás után, hézag nélkül következnek
 * (`start` … `start + count - 1`), de a modell üres is lehet — pl. a
 * QML-engine leépítésekor (#305) —, ezért a null-őr is ide tartozik.
 */
function indexOfRow(groups, row) {
    if (!groups) return -1
    for (var i = 0; i < groups.length; ++i)
        if (row >= groups[i].start
            && row < groups[i].start + groups[i].count)
            return i
    return -1
}

/** Egy csoport `[első, utolsó]` SORINDEXE (zárt intervallum). */
function rangeOf(group) {
    return [group.start, group.start + group.count - 1]
}

/** A `path` útvonalú mappacsoport tartománya; ha nincs ilyen, az ELSŐ
 *  csoporté; üres modellnél `null`.
 *
 * Ez a Home/End hatókörének végső visszaesése (#1147): az eredetiben a
 * művelet a JELENLEGI album (`[+0x2e0]`) kijelölés-csomópontján dolgozik,
 * kijelölés híján tehát a nyitott mappa a hatókör.
 */
function rangeOfPath(groups, path) {
    if (!groups || groups.length === 0) return null
    for (var i = 0; i < groups.length; ++i)
        if (groups[i].path === path) return rangeOf(groups[i])
    return rangeOf(groups[0])
}

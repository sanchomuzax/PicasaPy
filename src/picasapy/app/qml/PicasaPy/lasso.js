// A rács lasszójának SZÁMÍTÁSA — tiszta függvények (#897, #1148).
//
// Miért külön fájl (a `selection.js` mintája, #150): ez geometria és
// halmazművelet, nem felület — külön olvasható, külön mérhető, és a
// `LightboxFeed.qml` így marad a 800 soros határ alatt.
//
// A függvények a bemenetet NEM mutálják, új tömböt/objektumot adnak.
.pragma library

/** A húzás NORMALIZÁLT téglalapja, ami SOHA nem nulla méretű.
 *
 * Az eredeti a kezdő- és a végpontból min/max cserével épít téglalapot,
 * és **ha a két koordináta egyenlő, +1-et ad hozzá**
 * (`0x00719fd6`–`0x0071a012`).
 *
 * ⚠️ Ez nem szépészeti részlet: az elemteszt METSZÉS, szigorúan pozitív
 * területtel (#1148, `0x0071bc90`). A pontosan cellahatáron végighúzott
 * keret tehát nulla széles/magas, és a +1 nélkül EGYETLEN képet sem fogna
 * be — sem balra, sem jobbra.
 */
function normalizedRect(x1, y1, x2, y2) {
    var left = Math.min(x1, x2)
    var right = Math.max(x1, x2)
    var top = Math.min(y1, y2)
    var bottom = Math.max(y1, y2)
    return {
        left: left,
        top: top,
        right: right === left ? left + 1 : right,
        bottom: bottom === top ? top + 1 : bottom
    }
}

/** A kerettel METSZŐ cellák SORINDEXEI (`start` + a cellán belüli hely).
 *
 * A rács egyenletes: `cols` oszlop, `pitch` vízszintes és `cellHeight`
 * függőleges osztás. A `count` a csoport képszáma — a csonka utolsó sor
 * üres helyeire nem esik kép, és a lasszó a csoportból nem lép ki (#1219).
 */
function hitRows(rect, start, count, cols, pitch, cellHeight) {
    var c0 = Math.max(0, Math.floor(rect.left / pitch))
    var c1 = Math.min(cols - 1, Math.floor(rect.right / pitch))
    var r0 = Math.max(0, Math.floor(rect.top / cellHeight))
    var r1 = Math.floor(rect.bottom / cellHeight)
    var result = []
    for (var r = r0; r <= r1; ++r) {
        for (var c = c0; c <= c1; ++c) {
            var idx = r * cols + c
            if (idx < 0 || idx >= count) continue
            var cellLeft = c * pitch
            var cellTop = r * cellHeight
            if (rect.left < cellLeft + pitch && rect.right > cellLeft
                    && rect.top < cellTop + cellHeight
                    && rect.bottom > cellTop)
                result.push(start + idx)
        }
    }
    return result
}

/** A PILLANATFELVÉTEL és a keretbe eső képek összefésülése (#897).
 *
 * A `snapshot` a lasszó indulásakor mentett kijelölés (`[elem+0x5c]`,
 * `0x00719d80`–`0x00719d94`). A húzás minden mozdulata EHHEZ viszonyít,
 * nem a folyamatosan változó állapothoz — ezért nem villog a kijelölés,
 * és ezért áll vissza az eredeti, ha a keretet visszahúzzák.
 *
 * - Shift: a felvételkori kijelöléshez HOZZÁFŰZ;
 * - Ctrl: a keretbe esők a FELVÉTELKORI állapotukhoz képest FORDULNAK;
 * - módosító nélkül: a felvételt eldobja, csak a keretbe esők maradnak.
 */
function merged(snapshot, picked, shift, ctrl) {
    var base = snapshot || []
    var sel = []
    var i
    if (shift) {
        sel = base.slice()
        for (i = 0; i < picked.length; ++i)
            if (sel.indexOf(picked[i]) < 0) sel.push(picked[i])
        return sel
    }
    if (ctrl) {
        for (i = 0; i < base.length; ++i)
            if (picked.indexOf(base[i]) < 0) sel.push(base[i])
        for (i = 0; i < picked.length; ++i)
            if (base.indexOf(picked[i]) < 0) sel.push(picked[i])
        return sel
    }
    return picked.slice()
}

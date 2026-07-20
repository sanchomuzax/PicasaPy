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

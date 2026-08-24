// A képfolyam GÖRGETÉSI számításai — tiszta függvények (#1335).
//
// Miért külön fájl (a `lasso.js` / `selection.js` mintája, #150): ez
// aritmetika, nem felület — külön olvasható, külön mérhető, és a
// `LightboxFeed.qml` így marad a 800 soros határ alatt.
//
// A függvények a bemenetet NEM mutálják, új értéket adnak vissza.
.pragma library

/** A görgethető tartomány FELSŐ határa content-koordinátában.
 *
 * A Flickable csak `[originY, originY + contentHeight - height]` között
 * áll meg magától; ha a tartalom belefér a látótérbe, ez a tartomány
 * egyetlen pont (`originY`).
 */
function maxContentY(originY, contentHeight, height) {
    return originY + Math.max(0, contentHeight - height)
}

/** A kért pozíciót a görgethető tartományra vágja.
 *
 * ⚠️ #1335: e nélkül a nézet tartományon KÍVÜL ragad, és a Flickable csak
 * a KÖVETKEZŐ egérlenyomásra rántja vissza — a rács a kattintás
 * pillanatában megugrik, a kattintás pedig a közben elcsúszott képre esik.
 * (Mérve: `contentY` 101 ott, ahol a maximum 0 volt; egy indexkép
 * középpontja y=175-ről 276-ra ugrott, a húzásból néma, üres kijelölés
 * lett.)
 */
function clampContentY(y, originY, contentHeight, height) {
    return Math.max(
        originY, Math.min(y, maxContentY(originY, contentHeight, height)))
}

/** A sort a látótérbe hozó MINIMÁLIS `contentY` — vágás NÉLKÜL (#96).
 *
 * Csak akkor és annyit mozdul, hogy a `bounds` sáv belógjon a látótérbe;
 * ha a sor már látszik (vagy nincs sávja), a jelenlegi pozíciót adja.
 */
function rowRevealY(bounds, contentY, height) {
    if (!bounds) return contentY
    if (bounds.bottom > contentY + height) return bounds.bottom - height
    if (bounds.top < contentY) return bounds.top
    return contentY
}

/** A LEFELÉ görgetés valódi megállója az utolsó csoport alja alapján (#95).
 *
 * A `contentHeight` a nem-példányosított csoportoknál BECSLÉS — túllőhet a
 * valós tartalom-végen, és üres lapra engedne. Az utolsó csoport VALÓS
 * alja állít meg, amint példányosítva van.
 */
function feedEndStopY(lastY, lastHeight, originY, height) {
    return Math.max(originY, lastY + lastHeight - height)
}

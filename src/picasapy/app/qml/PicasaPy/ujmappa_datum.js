// Az Áthelyezés új mappába ablak kezdő dátuma (#7020).
//
// Az eredeti Picasa 3.9-ben (#7008) a `0x005e9a42` a `0x004ae0a0`-val lekéri
// a kijelölt kép idejét (OLE-nap), a `0x005e9a47` pedig hozzáad `0xcf50c8`
// = 1/86400 napot, vagyis pontosan egy másodpercet. A mappadátum ennek a napi
// része: egy éjfél előtt egy másodperccel készült kép a KÖVETKEZŐ napot adja.
//
// Miért külön fájl (a `selection.js` / `infosav.js` mintája): ez aritmetika,
// nem felület, és a `FileOpsDialogs.qml` már a 800 soros határ fölött van.
//
// A számítás szándékosan NAIV (UTC-alapú) idő: a kép ideje zóna nélküli
// falióra-idő, ezért a helyi időzóna nyári időszámítási átmenete (a hiányzó
// vagy kétszer előforduló óra) nem torzíthatja a napot.

.pragma library

var _IDO = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}):(\d{2}))?/

function _ketjegyu(n) { return (n < 10 ? "0" : "") + n }

// A `takenAt` ("ÉÉÉÉ-HH-NNTóó:pp:mm" vagy szóközös, esetleg csak dátum) +1 mp
// utáni napja ISO-alakban; "" hiányzó vagy érvénytelen időnél (a hívó ilyenkor
// a mai napra esik vissza).
function kepNapja(takenAt) {
    var r = _IDO.exec(String(takenAt === undefined || takenAt === null
                             ? "" : takenAt).trim())
    if (!r)
        return ""
    var ev = Number(r[1]), ho = Number(r[2]), nap = Number(r[3])
    var ora = r[4] === undefined ? 0 : Number(r[4])
    var perc = r[5] === undefined ? 0 : Number(r[5])
    var mp = r[6] === undefined ? 0 : Number(r[6])
    var alap = new Date(Date.UTC(ev, ho - 1, nap, ora, perc, mp))
    // a Date.UTC a hibás értékeket „továbbgörgeti" (február 30. -> március 2.),
    // ezért az azonos visszaolvasás az érvényesség próbája
    if (alap.getUTCFullYear() !== ev || alap.getUTCMonth() !== ho - 1
            || alap.getUTCDate() !== nap || alap.getUTCHours() !== ora
            || alap.getUTCMinutes() !== perc || alap.getUTCSeconds() !== mp)
        return ""
    var kesobb = new Date(alap.getTime() + 1000)
    return kesobb.getUTCFullYear() + "-" + _ketjegyu(kesobb.getUTCMonth() + 1)
        + "-" + _ketjegyu(kesobb.getUTCDate())
}

// Az ablak kezdő dátuma: a kép napja +1 mp-cel; kép ideje nélkül (nincs
// EXIF-dátum és kézi felülírás sem) marad a korábbi viselkedés, a mai nap.
function kezdoDatum(takenAt) {
    var nap = kepNapja(takenAt)
    if (nap !== "")
        return nap
    var ma = new Date()
    return ma.getFullYear() + "-" + _ketjegyu(ma.getMonth() + 1)
        + "-" + _ketjegyu(ma.getDate())
}

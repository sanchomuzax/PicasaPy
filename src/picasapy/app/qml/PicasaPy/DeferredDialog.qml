import QtQuick

// Halasztott párbeszéd (#1720) — a becsomagolt komponens NEM épül fel
// induláskor, csak az első megnyitáskor.
//
// **Miért.** A `Main.qml` több mint húsz párbeszédet deklarált közvetlenül,
// és mind felépült minden indulásnál, akkor is, ha a felhasználó soha nem
// nyitotta meg egyiket sem. Mérve (`docs/benchmarks/2026-08-31-qml-
// peldanyositas-1720.md`): a párbeszédek együtt **4600 QObject**, az
// indulási fa **31%-a**.
//
// **Használat.** A becsomagolt párbeszéd a `sourceComponent`-be kerül; a
// hívó a bevett `open()`-t hívja, minden más metódushoz az `ensure()`-t:
//
//     DeferredDialog {
//         id: printDialog
//         sourceComponent: Component { PrintDialog { } }
//     }
//     …
//     printDialog.open()                       // egyszerű nyitás
//     printDialog.ensure().openForRows(sorok)  // egyéb metódus
//
// **Miért nem néma.** Ha egy hívóhely kimarad az átírásból, az `ensure()`
// nélküli hívás a `Loader`-en `TypeError`-t dob — látható hiba, nem néma
// hatástalanság. A projekt visszatérő kára épp a néma változat volt.
Loader {
    id: root

    // A halasztás lényege: induláskor nincs példány.
    active: false
    // Szinkron létrehozás: az `ensure()` visszatérésekor az `item` kész.
    // (Aszinkron `Loader` mellett a hívó `null`-t kapna.)
    asynchronous: false

    //: Felépíti a párbeszédet, ha még nem áll, és visszaadja.
    function ensure() {
        if (!root.active)
            root.active = true
        return root.item
    }

    //: A bevett nyitási út — `ensure()` + a párbeszéd saját `open()`-je.
    function open() {
        return root.ensure().open()
    }
}

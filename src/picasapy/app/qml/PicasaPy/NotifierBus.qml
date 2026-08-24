pragma Singleton
import QtQuick

// A lebegő értesítősáv JELENLÉT-jelzője (#1129).
//
// Spec: `docs/specs/picasa-lebego-ertesito.md`.
//
// ## Miért van rá szükség
//
// A `collageDesktopBackgroundReady` jelzésnek a #1168 óta VAN fogadója: a
// `CollageDoneNotice`, ami a főablak alján ül, és csak kattintásra tűnik
// el. A #1129 ugyanennek az eseménynek megadja a valódi gazdáját — a
// lebegő sávot (`CNotifierPopup`), ahol a Picasa 3 is megjeleníti.
//
// A kettő EGYSZERRE nem szólalhat meg: a felhasználó ugyanazt kapná
// kétszer, két különböző helyen. A régi értesítést viszont nem lehet
// egyszerűen kivenni, mert a `Main.qml` példányosítja (a gazda módosítása
// az integrátoré). Ezért van ez az egy bites, olvasható kapu:
//
//   * a `PicasaNotifier` induláskor `attached = true`-ra állítja;
//   * a `CollageDoneNotice` csak akkor szólal meg, ha `attached` HAMIS.
//
// Így a sáv bekötése előtt és után is pontosan EGY értesítés van, és a
// váltás a gazda átírása nélkül, magától megtörténik.
QtObject {
    /** Igaz, ha a lebegő értesítősáv példányosítva van a felületen. */
    property bool attached: false
}

# A lebegő értesítősáv (Picasa Notifier)

A Picasa 3 a képernyő jobb szélén egy **kis, lebegő ablakot** villant fel, ha
a háttérben történt valami, amiről a felhasználót értesíteni kell — például
elkészült egy képernyőfelvétel, vagy lefutott egy importálás. Az ablak
független a főablaktól, és **kattintásra elvezet** az eredményhez.

Ez a lap magáról az **ablakról** szól. Az importálás **panelje** (Acquire)
külön lapon van: [picasa-importalas.md](picasa-importalas.md).

## Az ablak azonosítója

| Mi | Érték | Bizonyíték |
|---|---|---|
| osztály | `CNotifierPopup` | erőforrás-kulcs |
| ablaknév (EN) | `Picasa Notifier` | string @ `0x00ca2730` |
| ablaknév (HU) | **Picasa Értesítő** | `CNotifierPopup::window_name` |
| létrehozó függvény | `0x00657300` | az egyetlen hely, ahonnan az ablaknév hivatkozva van |

A létrehozó függvény **csak az ablaknevet** használja — a megjelenített
tartalmat a hívók adják át. Az ablak tehát általános értesítő-tartály, nem
egyetlen esemény célfelülete.

**Bizonyítottsági fok: megerősített.**

## 1. ág — képernyőfelvétel mentése

Ez az ág **képernyőképpel is igazolt** (a tulajdonos futó Picasa 3-ából,
2026-08-20), ezért a legerősebben alátámasztott.

| kulcs | EN | HU | cím |
|---|---|---|---|
| `CThumbUI::screensaved` | Screenshot saved | **A képernyőfelvétel mentése sikerült** | `0x00c8ab74` |
| `CThumbUI::clickview` | click to view | **a megtekintéshez kattintson ide** | `0x00c903a4` |

**Megjelenés a képernyőképen:** kétsoros szöveg — az első sor az esemény,
a második a cselekvési tipp. Az első sor a keskeny ablakban **elvágódik**
(„A képernyőfelvétel mentése si…"), tehát az ablak **fix szélességű**, és
a szöveg nem tördel.

Megjelenítő függvények: `0x0053de70` és `0x0057d080`. Előbbi a
képernyőfelvétel-mentés környezetében dolgozik (`showcapture`,
`AddLocateFile`, `locate`, `indexonly` sztringekkel egy függvényben),
utóbbi kizárólag ezt a két kulcsot használja.

Kapcsolódó, ugyanebből a családból: `Picasa\Screen Captures\`
(`0x00c916f4`) és `Fullscreen capture` (`0x00c916c8`) — a mentés célmappája
és a teljes képernyős felvétel megnevezése.

**Bizonyítottsági fok: megerősített** (kulcs + fordítás + képernyőkép).

## 2. ág — importálás

Az importálás fázisszövegei a `CAcquireUI::` családban élnek; a két
*befejező* állapot neve **maga mondja ki**, hogy értesítőbe megy:

| kulcs | HU | szerep |
|---|---|---|
| `donenotifer` *(a binárisban elgépelve)* | Az importálás elkészült | záró, sikeres |
| `errornotifer` *(elgépelve)* | Hiba történt az importálás során | záró, hibás |

A közbenső fázisok (`loading1`, `loading2`, `reading`, `copying`,
`cleanup`, `finishing`, `AcquiredFiles`, `speedsec`) és a négy hibaszöveg a
[picasa-importalas.md](picasa-importalas.md) „Folyamat és hibák" szakaszában
vannak kigyűjtve — itt nem ismételjük.

⚠️ **Nyitott:** hogy a *közbenső* fázisok a lebegő értesítőben vagy csak az
importálás paneljében látszanak-e, **nincs bizonyítva**. A `notifer` végződés
csak a két záró állapotnál szerepel.

**Bizonyítottsági fok: erős** a két záró állapotra, **feltételes** a
közbensőkre.

## 3. ág — várakozás

| kulcs | EN | HU | cím |
|---|---|---|---|
| `CThumbUI::DelayOpWaiting` | Waiting... | **Várakozás...** | `0x00c90378` |

Közvetlenül a `clickview` előtt áll a szövegtárban (`0x00c90378` →
`0x00c903a4`), tehát a két kulcs egy családba tartozik. Ez a „a művelet még
nem indult el" állapot felirata.

**Bizonyítottsági fok: erős** (szomszédosság + jelentés), a megjelenítő
környezete nincs kimérve.

## Interakció

| Mit | Bizonyíték |
|---|---|
| **kattintás az ablakra → az eredmény megtekintése** | a `clickview` szövege maga (*„a megtekintéshez kattintson ide"*) |
| **bezárás** | a képernyőképen a jobb felső sarokban záró vezérlő látszik |

## Amit NEM sikerült megállapítani

Ezek **nyitott kérdések**, nem elhallgatott részletek:

1. **Geometria** — az ablak mérete, a jobb szélhez képesti pozíciója, a
   belső margók. A `respack.yt` tervezővászon **nincs meg a kutatási
   anyagban**, a `.tre` pedig elrendezést elvileg sem ad
   ([picasa-respack-format.md](picasa-respack-format.md)).
2. **Animáció** — a felhasználó „animált sávnak" írta le. Hogy becsúszik,
   elhalványul, vagy folyamatjelzőt mozgat, **nincs bizonyítva**.
3. **Élettartam** — mennyi ideig marad kint, eltűnik-e magától,
   újrahasznosul-e egymást követő eseményeknél.
4. ~~**Az észlelési ág**~~ — **MEGVAN a szövege és a mechanizmus is**,
   ld. lent a „4. ág — új képek észlelése" szakaszt.
5. **Az események teljes listája** — a `CNotifierPopup` általános tartály;
   hány esemény használja, nincs felmérve. A mostani kör kettőt igazolt
   (képernyőfelvétel, importálás vége).

## 4. ág — új képek észlelése (2026-08-20)

A tulajdonos kérdése — *„valami trigger kell legyen"* — jogos volt, és a
szövegtár meg is adja a hiányzó értesítő-szöveget:

| kulcs | EN | HU | cím |
|---|---|---|---|
| `il_PopupNotifierRec::1` | `%1$d %2$s received` | **`%1$d %2$s érkezett`** | `0x00ca27b0` |
| `il_PopupNotifierRec::2` | picture | **kép** | `0x00ca2764` |
| `il_PopupNotifierRec::3` | pictures | **kép** | `0x00ca2788` |

Mindhármat **ugyanaz a függvény** használja (`0x00658340`), és **csak
ezt a hármat** — tehát ez a függvény kizárólag az „N kép érkezett"
értesítő-rekordot állítja össze. A `PopupNotifierRec` név is ezt mondja:
**rekord** a `CNotifierPopup` számára.

Ez az a szöveg, ami a 4. nyitott kérdésből hiányzott: az értesítő nem csak
képernyőfelvételre és importálásra jön elő, hanem akkor is, ha a program
**új képeket vesz észre**.

### A mechanizmus: Win32 könyvtár-változás értesítés

A `Picasa3.exe` importtáblája (`referencia/binary-index/imports.csv`) a
következőket hozza a `KERNEL32.DLL`-ből:

| import | mit ad |
|---|---|
| `FindFirstChangeNotificationW` | figyelő-fogantyú egy könyvtárra |
| `FindNextChangeNotification` | a fogantyú újrafegyverzése egy esemény után |
| `WaitForMultipleObjects` | több figyelő egyszerre, időkorláttal |

A `FindNextChangeNotification`-t két függvény hívja (`0x007065f0`,
`0x00706680`); az első egy **`WaitForMultipleObjects`-burkoló** —
`0xc4039c` a thunk, és a `0x102`-es visszatérést (`WAIT_TIMEOUT`) külön
ágon kezeli —, tehát a minta a klasszikus **esemény-vezérelt figyelő
hurok**, nem periodikus újraolvasás.

➡️ **A Picasa tehát nem pollozza a mappát: a rendszertől kap értesítést,
és arra villantja fel a lebegő sávot.**

*Bizonyítottsági fok: **megerősített** az értesítő-szövegre és arra, hogy a
három kulcsot egyetlen rekord-építő használja · **megerősített** az
import-táblára (a három API tényleg használatban van) · **feltételes** az,
hogy éppen EZ a figyelő táplálja az „N kép érkezett" rekordot: a
`0x00658340` hívói az indexben nincsenek feloldva, tehát a két oldal
összekötése dekompilációt kíván.*

⚠️ **Amit ez NEM mond meg:** mit tesz a Picasa egy olyan **idegen** képpel,
amit a felhasználó másol a figyelt mappába — csak azt tudjuk, hogy
**észreveszi**. A #1125 döntéséhez (a kollázs felülírja-e a saját
helykitöltőjét) ezért nem ez a szakasz a bizonyíték, hanem a tulajdonos
valódi Kollázsok mappájának mérése (11 JPEG + 11 `.cxf`, **nulla**
párosítatlan fájl).

## Módszertani megjegyzés

A megfejtés **teljes egészében olcsó bizonyítékból** származik (szövegtár +
sztring-xref a bináris indexben), dekompiláció nélkül. A 4. és 5. pont
viszont valószínűleg **célzott dekompilációt** kíván a `0x00657300`
környékén — annak a függvénynek a hívóit kell felderíteni.

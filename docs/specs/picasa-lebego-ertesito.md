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
4. **Az észlelési ág** — a felhasználó szerint akkor is felbukkan, ha a
   Picasa magától vesz észre új képet vagy mappát. Ehhez a figyelt mappák
   (`IDS_MAKE_WATCH`) irányából kell tovább ásni; a mostani körben **nem
   találtam** hozzá tartozó értesítő-szöveget.
5. **Az események teljes listája** — a `CNotifierPopup` általános tartály;
   hány esemény használja, nincs felmérve. A mostani kör kettőt igazolt
   (képernyőfelvétel, importálás vége).

## Módszertani megjegyzés

A megfejtés **teljes egészében olcsó bizonyítékból** származik (szövegtár +
sztring-xref a bináris indexben), dekompiláció nélkül. A 4. és 5. pont
viszont valószínűleg **célzott dekompilációt** kíván a `0x00657300`
környékén — annak a függvénynek a hívóit kell felderíteni.

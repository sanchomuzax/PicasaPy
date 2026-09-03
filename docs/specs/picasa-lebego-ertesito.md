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

1. ~~**Geometria**~~ — **MEGVAN**, ld. a „Geometria — mérve a binárisból"
   szakaszt. (Az első változat tévesen állította, hogy a `respack.yt`
   hiányzik.) ~~Ami ebből még nyitott: az ablak képernyőhöz képesti
   pozíciója.~~ — ✅ **EZ IS MEGVAN**, ugyanezen a lapon lentebb:
   „Dekompiláció — pozicionálás és ablakstílus MEGFEJTVE". Röviden:
   `SPI_GETWORKAREA` (**munkaterület**, nem teljes képernyő) + **144
   képpont** eltolás a szélétől, `WS_EX_TOPMOST | TOOLWINDOW | WINDOWEDGE`,
   és újrahorgonyzás a munkaterület változásakor (`0x00658200`).
   *(A jelölés 2026-08-20 óta elavult volt — a saját későbbi szakaszunk
   válaszolta meg, és senki nem vezette át.)*
2. **Animáció** — a `progressbase`/`progressfill` réteg bizonyítja, hogy van
   folyamatjelző, a dekompiláció pedig **kizárta a Win32 utat**
   (`AnimateWindow`, rétegelt ablak). Ami marad: a `yt` keretrendszer saját
   átmenet-rendszere (`ytCrossFadeColorTransitionNode`) — **nyom, nem
   bizonyíték**.
3. **Élettartam** — az ABLAK singleton (megválaszolva), de hogy egy CELLA
   meddig marad kint, **nyitott**. A `notifier` modulnak nincs `tre:`
   bejegyzése, tehát a viselkedés kódban van.

   ⭐ **2026-08-24 — a negatívum KITERJESZTVE az EGÉSZ binárisra.** A korábbi
   dekompiláció öt függvényben zárta ki a Win32 időzítőt. Az importtábla
   szerint a teljes állományban **mindössze ennyi** időzítő-hívó van:

   | API | hívók |
   |---|---|
   | `SetTimer` | `0x004735c0`, `0x008de1b0` |
   | `KillTimer` | `0x008ddf00`, `0x008de1b0` |
   | `timeSetEvent` | `0x00ab8360` |

   **Egyik sem a notifier moduljában** (`0x0065xxxx`: `0x00655aa0`,
   `0x00656fe0`, `0x00657300`, `0x00658340`). ⇒ **A cella élettartamát
   biztosan NEM Win32 időzítő méri.** A két időzítő-burok ráadásul maga is
   csak **közvetve** hívódik (közvetlen `call` nélkül, vtable-rekeszből), és
   a `0x008dxxxx` — a `yt` keretrendszer — tartományban ül.

   **A következő lépés:** a `yt` keretrendszer saját képkocka-ütemének
   (`ytCrossFadeColorTransitionNode` és társai, `TransitionNodeHandler`)
   végigkövetése — ez már célzott dekompiláció, nem olcsó lánc.
4. ~~**Az észlelési ág**~~ — **MEGVAN a szövege és a mechanizmus is**,
   ld. lent a „4. ág — új képek észlelése" szakaszt.
5. ~~**Az események teljes listája**~~ — **MEGVÁLASZOLVA**: nincs ilyen
   lista. Az ablaknak egyetlen saját rekordja van (`il_PopupNotifierRec`),
   minden más szöveget a hívó ad át. Ld. „Az életciklus és az események".

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

## Geometria — MÉRVE A BINÁRISBÓL (2026-08-20)

⚠️ **Helyesbítés:** e lap első változata azt állította, hogy a `respack.yt`
„nincs meg a kutatási anyagban". **Ez hamis volt** — a fájl megvan
(`research/copy_Picasa_3_7/Picasa3/runtime/respack.yt`, 3,8 MB, Picasa
3.9.141.259), és minden réteget megad. A hiba az volt, hogy nem néztem meg a
saját dokumentációnk által megnevezett útvonalat.

A `notifier` modul **11 rétege**, a 13 bájtos fejlécek `int16 x0,y0,x1,y1`
mezőiből (fájloffsetek a `respack.yt`-ben):

| réteg | x0 | y0 | x1 | y1 | méret | szerep |
|---|---:|---:|---:|---:|---:|---|
| `docbounds` | 0 | 0 | 247 | 45 | **247 × 45** | **az értesítő-cella teljes mérete** |
| `cell1` | 0 | 0 | 247 | 45 | 247 × 45 | egy cella tartalomrétege |
| `cellbase` | 0 | 0 | 13 | 45 | 13 × 45 | bal oldali sáv (teljes magasság) |
| `basedecrect` | 226 | 0 | 247 | 45 | 21 × 45 | **jobb oldali vezérlő-sáv** |
| `close` | 231 | 4 | 242 | 15 | **11 × 11** | bezárás — jobb FELSŐ |
| `collapse` | 231 | 30 | 242 | 41 | **11 × 11** | összecsukás — jobb ALSÓ |
| `gripper` | 233 | 19 | 240 | 26 | 7 × 7 | fogantyú (mozgatás) — jobb KÖZÉP |
| `chat` | 9 | 12 | 29 | 33 | 20 × 21 | ikonhely (üzenet) |
| `globe` | 10 | 14 | 24 | 28 | 14 × 14 | ikonhely (online) |
| `progressbase` | 40 | 10 | 170 | 21 | **130 × 11** | **folyamatjelző sín** |
| `progressfill` | 42 | 12 | 167 | 18 | **125 × 6** | **folyamatjelző kitöltés** |

Az ikonkészlet külön modulban: `tab_notifier_icons/import32` (**32 × 32**) és
`import16` (**16 × 16**) — az importálás ikonja két méretben.

### Amit a geometria eldönt

1. **Az ablak fix szélességű: 247 képpont.** Ez magyarázza, amit a
   tulajdonos képernyőképén látni: a hosszú magyar felirat **elvágódik**.
2. **Három vezérlő van, nem egy** — a jobb szélső 21 képpontos sávban,
   függőlegesen elosztva: **bezárás** (fent), **fogantyú** (közép),
   **összecsukás** (lent).
3. **Van folyamatjelző** (`progressbase` + `progressfill`) — ez az, amit a
   tulajdonos „animált sávnak" látott. A kitöltés 2 képponttal beljebb kezdődik
   (42 vs 40) és 6 képpont magas a 11 képpontos sínben.
4. **Cellás felépítés** (`cellbase`, `cell1`): az értesítő **több bejegyzést**
   tud egymás alatt megjeleníteni, nem csak egyet.
5. Két ikonhely (`chat`, `globe`) mutatja, hogy az értesítő **többféle
   eseményt** szolgál ki — összhangban azzal, hogy általános tartály.

**Bizonyítottsági fok: megerősített** — a méretek a bináris erőforráscsomagból
származnak, nem becslésből.

## Az életciklus és az események — a hívási lánc végigjárva (2026-08-20)

Az `xrefs` tábla feloldja a hívási láncot, amit az első kör nem nézett meg:

```
0x004051b0  →  0x004039f0  →  0x0040bf70  →  0x00657300 (CNotifierPopup)
```

A `0x0040bf70` az **alkalmazás-indítás** függvénye: ugyanott tölti be a
kurzorokat (`pan_hand_normal`, `crosshair`, `rotatecursor`…), a
`Preferences`-t, a `Picasa 3` ablaknevet és az erőforrás-kezelő hibaüzenetét
(`ytResMgr::LoadError`).

➡️ **Az értesítőablak SINGLETON: egyszer jön létre, az indításkor, és végig
él.** Nem eseményenként születik és hal meg — az egyes értesítések **cellák**
benne (`cellbase`, `cell1`).

*Bizonyítottsági fok: megerősített* (egyetlen hívó, és az az indítás).

### Hány eseménye van?

A szövegtár **pontosan egy** saját értesítő-rekordot ismer:

| kulcs | HU |
|---|---|
| `il_PopupNotifierRec::1` | `%1$d %2$s érkezett` |
| `il_PopupNotifierRec::2/3` | kép / kép |

Minden más felirat, ami az ablakban megjelenik, **más családból kölcsönzött**
(`CThumbUI::screensaved`, `CThumbUI::clickview`, `CThumbUI::DelayOpWaiting`,
`CAcquireUI::donenotifer`, `CAcquireUI::errornotifer`).

➡️ **Az ablaknak nincs saját esemény-katalógusa**: egy általános
„N kép érkezett" rekordja van, a többi szöveget a hívó adja át. Ez lezárja az
első kör 5. nyitott kérdését — nem azért, mert megtaláltuk a listát, hanem
mert **bizonyítottan nincs ilyen lista**.

*Bizonyítottsági fok: erős* (a szövegtár teljes, `PopupNotifier`-re három
találat van, és mindhármat ugyanaz a rekord-építő használja).

### Miért NEM olvasható ki az animáció és az élettartam

A `respack.yt`-ben a `notifier` modulnak **csak `layer:` bejegyzései vannak**
— **`tre:` bejegyzése nincs**. A `.tre` a viselkedést és a szülő-gyerek
viszonyt írja le; ha nincs, akkor a viselkedés **kódban van**, nem
erőforrásban.

➡️ Ezért az **animáció** és a **cella élettartama** olcsó úton **elvileg sem**
válaszolható meg. Ez nem kihagyott lépés, hanem a lánc vége: innen **célzott
dekompiláció** következik (`0x00657300` és a cellakezelő).

## Dekompiláció — pozicionálás és ablakstílus MEGFEJTVE, időzítő NINCS (2026-08-20)

Ghidra 12.1.2, teljes autoanalízis (426 mp), Picasa 3.9.141.259
(`sha256=644b7be…3ddc96`). Két célzott próba; a kimenet a privát repóban:
`referencia/dekompilalt-notifier/`.

### Pozitív leletek — az ablak elhelyezkedése

A `0x00657300` (a `CNotifierPopup` létrehozója) ezt teszi:

| cím | hívás | jelentés |
|---|---|---|
| `0x00657353` | `SystemParametersInfoA(0x30, …)` | **`SPI_GETWORKAREA`** — a **munkaterületet** kéri le, nem a képernyőt |
| `0x00657369` | `local_4 + -0x90` | a munkaterület széléhez képest **144 képpont** eltolás |
| `0x0065743c` | `SetWindowLongA(hwnd, -0x14, … \| 0x188)` | `GWL_EXSTYLE` \|= **`WS_EX_TOPMOST` (0x8) + `WS_EX_TOOLWINDOW` (0x80) + `WS_EX_WINDOWEDGE` (0x100)** |
| `0x00657490` | `SetWindowLongA(hwnd, 0, 0x47506e74)` | saját azonosító az ablak extra bájtjaiban (`"GPnt"`) |
| `0x006574a0` | `SetWindowPos` | a végleges elhelyezés |

➡️ **Az ablak a tálcát tiszteletben tartva helyezkedik el** (munkaterület, nem
teljes képernyő), **mindig felül van**, és **nem kap tálcagombot** — pontosan
az a viselkedés, amit a tulajdonos „lebegő sávnak" nevezett.

### Melyik ÉLHEZ képest a 144 képpont (2026-08-24, #1129)

Az első leírás csak annyit mondott, hogy „144 képpont eltolás a szélétől" —
a megvalósításhoz viszont tudni kell, MELYIK széltől. A dekompilátumból ez
kiolvasható: a `SystemParametersInfoA(0x30, …)` a `local_10 … local_4`
egymást követő rekeszekbe írja a `RECT`-et (`left, top, right, bottom`),
tehát a `local_4` a munkaterület **alsó** éle, és a `local_4 + -0x90` ebből
von le 144-et. Az így kapott érték az ablak **felső** éle lesz
(`local_1c = local_4`, `local_14 = local_4 + 1`).

Vízszintesen az induló téglalap `left = 10000` (jobbról-balra író
felületnél `-10001`), vagyis **a képernyőn kívül**, a jobb oldalon — ez a
*parkolóhely*, nem a megjelenési pozíció. Ez egyben a legerősebb közvetett
nyom arra, hogy a felbukkanás **vízszintes becsúszás** lehet; bizonyíték
továbbra sincs rá.

➡️ Amit ebből a #1129 megvalósított: a sáv a munkaterület **jobb** széléhez
igazodik, a **felső** éle pedig a munkaterület aljától **144 képponttal**
feljebb van.

A `0x00658200` ugyanezt tartja karban: `SystemParametersInfoA` +
`IsWindow` + `IsWindowVisible` + `GetWindowRect` — **újrahorgonyzás**, ha a
munkaterület vagy az ablak állapota változik.

*Bizonyítottsági fok: megerősített.*

### Negatív lelet — és ez is válasz

A vizsgált **öt** függvényben (`0x00657300` létrehozó, `0x00658340`
rekord-építő, `0x00658200` pozicionáló, `0x00655e50`, `0x00655950`,
`0x00656fe0`) **nincs**:

- `SetTimer` / `KillTimer` / `WM_TIMER` / `GetTickCount` / `timeGetTime`
  → **az élettartamot nem Win32 időzítő vezérli**;
- `AnimateWindow`, rétegelt ablak (`SetLayeredWindowAttributes`), `AlphaBlend`
  → **az animáció nem Win32 segédfüggvénnyel készül**.

➡️ Mindkettő a program **saját `yt` keretrendszerének** ütemezőjében lehet —
összhangban azzal, hogy a `data_symbols` tartalmaz
`ytCrossFadeColorTransitionNode` (kereszt-áttűnés) osztályt. **Ez a nyom, nem
bizonyíték:** a kapcsolat kimutatása a `yt` átmenet-rendszerének felderítését
kívánja, ami külön menet.

*Bizonyítottsági fok: megerősített (a Win32 út kizárva) · feltételes (hogy a
`yt` átmenet-rendszer adja).*

## Módszertani megjegyzés

A megfejtés **teljes egészében olcsó bizonyítékból** származik (szövegtár +
sztring-xref a bináris indexben), dekompiláció nélkül. A 4. és 5. pont
viszont **célzott dekompilációt** kíván. A hívólánc időközben feloldva
(`0x004051b0 → 0x004039f0 → 0x0040bf70 → 0x00657300`), tehát a következő kör
nem a hívókat keresi, hanem magát a `0x00657300`-at és a cellakezelőt
elemzi — az adja meg az animációt és a cella élettartamát.


## A cella élettartama NEM idővezérelt — a keresési tér bezárva (2026-08-25)

Az „Amit NEM sikerült megállapítani" 3. pontja (a cella élettartama) tovább
szűkült. **Négy negatív és két pozitív lelet.**

### Négy negatív — a notifier nem méri az időt, sehogy

| amit kerestem | eredmény |
|---|---|
| Win32 időzítő a notifierben | **nincs.** A teljes binárisban összesen három időzítő-hívó függvény van (`SetTimer`: `0x004735c0`, `0x008de1b0`; `KillTimer`: `0x008ddf00`, `0x008de1b0`; `timeSetEvent`: `0x00ab8360`) — **egyik sem** a notifier moduljában |
| óra-olvasás a notifierben | **nincs.** A `0x0065xxxx` tartományban hat `QueryPerformanceCounter`-hívó van (`0x00652f50`, `0x00654150`, `0x00654610`, `0x0065a6b0`, `0x0065a700`, `0x0065d010`), de **egyik sem** notifier-függvény (`0x00655950`, `0x00655aa0`, `0x00655e50`, `0x00656fe0`, `0x00657300`, `0x00658200`, `0x00658340`) |
| időtartam-konstans átadása | **nincs** a két külső belépési pont egyikén sem |
| a modul külső felülete | **mindössze KÉT** távoli belépési pont (ld. lent) |

### Két pozitív — mi a modul valódi külső felülete

Az összes `E8`+rel32 hívás feloldva a teljes `.text`-en, majd megszűrve
azokra, amik a `0x00655000`–`0x00659800` tartományba mutatnak **kívülről**:

| belépési pont | külső hívó | mi ez |
|---|---|---|
| `0x00657300` (496 b) | `0x0040c339` | a **létrehozó** — az alkalmazás indulásából |
| **`0x006574f0`** (188 b) | `0x0073f104` | az **export/előzmény-modulból** (`]history:email`, `]history:output`, `]history:export` sztringek a `0x0073f0f0`/`0x0073f320`-ban) |

### ⚠️ HELYESBÍTÉS: a `0x006574f0` NEM „értesítés megjelenítése"

Utasításról utasításra ez történik benne:

```asm
0x006574f1  mov  ebp, [0xc40284]        ; GetCurrentThreadId
0x006574fb  call ebp                    ; rekurzív zár: tulajdonos +0x20, számláló +0x24
0x0065751a  call [0xc4055c]             ; EnterCriticalSection
0x00657535  mov  ecx, [esi+0x90]
0x0065753f  call 0x65a9d0               ; függőben lévő művelet LEMONDÁSA
0x00657544  and  [esi+0x94], 1
0x0065754b  fld  qword ptr [0xcf3a08]   ; <<< 100.0 (double)
0x00657551  mov  [esi+0x90], 0
0x00657565  fstp qword ptr [esp]
0x00657568  call [vtable+0x64]          ; << az érték átadása
…                                        ; a maradék: a zár feloldása
0x00657596  call [0xc402a8]             ; LeaveCriticalSection
```

A `[0xcf3a08]` kiolvasott értéke **100.0**. A notifiernek van
`progressbase`/`progressfill` rétege (ld. a geometria-szakaszt) ⇒ ez
**„a folyamatjelző 100%-ra"**, azaz **befejezés-jelzés** — nem élettartam és
nem „mutasd meg".

### Amit ez kimond

> **A cella élettartama nem idővezérelt, hanem ESEMÉNY-/FOLYAMAT-vezérelt.**
> A gazda (az export/előzmény-modul) jelenti a haladást, és a **100%** a
> befejezés jele. Nincs a modulban semmi, ami másodperceket számolna.

**Ami még nyitva:** mi távolítja el a cellát a 100% UTÁN (magától eltűnik,
a felhasználó kattintására, vagy a következő cella szorítja ki). A keresési
tér viszont bezárult: **nem időzítő és nem óra** — a cella-rekord
másolója (`0x00656a30`, 473 b) egy **float mezőt** visz `+0xc`-n, ez a
következő jelölt.

*Bizonyítottsági fok: **megerősített** a négy negatívumra (import-tábla +
nyers hívásfeloldás a teljes `.text`-en) és a `0x006574f0` szerepére
(diszasszemblálva, a konstans kiolvasva). **Nyitva**: a cella eltávolítása.*

## ✅ A cella élettartama — MEGFEJTVE (2026-08-26)

> ⚠️ **Ez a szakasz MEGDÖNTI a lap korábbi következtetését**, amely szerint
> „nem időzítő és nem óra". **Óra** — csak a notifier modulján **kívül**.
> A korábbi kör a `QueryPerformanceCounter`-hívókat a `0x0065xxxx` modulon
> BELÜL kereste; a negatív találatot az egész mechanizmusra vonatkoztatta.

### Az időforrás — `0x009a5210` (128 b)

Nagyfelbontású 64 bites számláló (`call [0xc40298]` → `fild qword`),
gyorstárazott kezdőértékkel (`0xd678f0`) és frekvenciával (`0xd678e8`)
⇒ **másodperc `double`-ben, az indulás óta**.

*(A pontos API-név nem adható ki: a `0xc40298` nem az importtáblában van,
hanem futásidőben feltöltött mutatótábla.)*

### A határidő írása — `0x00655d20` (291 b)

A cellatömbön lépked (**lépésköz `0xc8` = 200 bájt/cella**), majd:

| cím | művelet |
|---|---|
| `0x00655d96` | `fld dword [ebp+0xc]` — a kért **élettartam** (float, mp), hívási paraméter |
| `0x00655dac` | ha `<= 0` → `[cella+0x12] = 1`, **határidő nélkül** |
| `0x00655dc4` | `call 0x9a5210` — most |
| `0x00655dc9` | `fadd [ebp+0xc]` |
| `0x00655dcc` | `fstp qword [cella+0xb8]` — ⇐ **abszolút határidő** |

### A lejárat ellenőrzése — `0x006575b0` (1714 b), képkockánként

| cím | művelet |
|---|---|
| `0x0065770c` | `call 0x9a5210` — **képkockánként EGYSZER** |
| `0x00657741` | `fcomp [cella+0xb8]` — a határidő 0? → kihagyja |
| `0x0065775a` | `fcomp` — `most` vs határidő |
| `0x00657769` | `call 0x655be0` — ⇐ **a cella eltávolítása** |

Az eltávolító `0x00655be0` (311 b) ugyanazzal a `0xc8`-as lépésközzel
dolgozik (`0x00655c36`), **kritikus szakaszon belül** (`0x00655cc3` /
`0x00655cef`).

### Két külön dolog

**A 100%-ra állítás (`0x006574f0`) NEM távolítja el a cellát.** A cella a
**határidejétől** tűnik el, nem a folyamatjelző állásától.

### A `+0xc` float mező

**[0,1]-re vágott** érték (`0x00659d64  fld1` + `fcom` + `fstp`), a másoló
`0x00656a30:0x00656a46` viszi át. **Nem** az élettartam — az a `+0xb8`.

Jegy: **#1130**.

## ✅ Az animáció ÜTEMFORRÁSA — a vtable 0x60 rekesze (2026-08-30)

A korábbi körök „a `yt` keretrendszer képkocka-üteme" sejtését most az
**RTTI/vtable-tábla igazolja** (olcsó lánc, dekompiláció nélkül):

| vtable | rekesz 25. (0x60) | szerep |
|---|---|---|
| `CBaseNotifier::vftable` (`0x00ca27cc`) | **`0x00656860`** | ős tick — órát olvas (`0x009a5210`), cella-másolót hív (`0x00656a30`) |
| `CNotifierPopup::vftable` (`0x00ca284c`) | **`0x006575b0`** (felülírva) | a Popup tick — a lejárat-ellenőrző (a `0x00655be0` eltávolítóval) |

**Miért nincs közvetlen hívójuk az indexben:** a `0x006575b0`-ra és a
`0x00656860`-ra **egyetlen `call` sem mutat** — mindkettő kizárólag a
**vtable 25. rekeszén (0x60)** keresztül érhető el. A `yt`-keretrendszer
képkocka-ciklusa a csomópontok `[vtable+0x60]` rekeszét hívja minden
képkockán — ez az ütemforrás. *(Ugyanez magyarázza a korábbi negatívumot
is: a Win32-időzítő-kizárás helyes, a tick nem időzítőből, hanem a saját
renderelési ciklusból jön.)*

*Bizonyítottsági fok: **megerősített** (a vtable-rekeszek és a
hívás-hiány az indexből; a rekesz-szerep a dekompilált `0x006575b0`
tartalmából — óra + határidő + eltávolítás, ld. a 2026-08-26-i szakaszt).*


## Az animáció ALAKJA — MÉRVE (#2034, 2026-09-03)

A #1130 2. pontjának maradéka. A válasz **egyik felkínált lehetőség sem**:
nem vízszintes becsúszás és nem áttűnés, hanem **két absztrakt skalársáv
kulcskockás animációja**, cellánként.

### A képkockánkénti tick szerkezete (`0x006575b0`)

A cellák a `[popup+0x90]` tömbben ülnek, **cellánként `0xC8` = 200 bájt**
(`add ebx, 0xc8`, `0x00657893`); a darabszám `[popup+0x94] >> 1`
(`0x0065788b`). Minden cellára, minden képkockán:

| lépés | cím | mit csinál |
|---|---|---|
| lejárat | `0x00657741` | `fldz; fcomp [cella+0xb8]` — ha a határidő > 0 **és** `most > határidő` → `call 0x655be0` (elbocsátás) |
| animáció | `0x0065777e`–`0x006577d9` | ld. lent |
| pozíció | `0x006577ea`–`0x0065782d` | `call 0x655950` a CÉL-pozícióra, majd `[cella+0xb0]`/`[cella+0xb4]` **közvetlen** `mov` |

### A két animált sáv

Cellánként **két** növekvő kulcskocka-tömb: `cella+0x80…0x94` és
`cella+0x98…0xac`. A kulcskocka **40 bájt** (`0x009e6010`: `eax*5*8`), az
utolsó kulcskocka ÉRTÉKE a `[bázis + n·40 − 0x18]` qword.

- **Kiolvasó:** `0x006559b0` — mindkét sáv utolsó értékét egy `float[2]`-be írja.
- **Író:** `0x006558b0` — `t0 = most` (`0x009a5210`), `t1 = most + időtartam`,
  és **mindkét** sávhoz fűz egy kulcskockát (`0x00655900` és `0x0065593b`).

A tick minden képkockán összeveti a sávok aktuális végértékét a **céllal**:

```
0x0065777e  fld dword [0xcf3ed0]   ; −1,0f        → cél[0]
0x0065778e  fld dword [esp+0x20]   ; a cella SORSZÁMA → cél[1]
0x00657796  call 0x6559b0          ; a sávok mostani végértéke
0x0065779f  fcomp qword [0xcf3f58] ; ≠ −1,0 ?
0x006577b0  fld dword [ecx+4]      ; ≠ sorszám ?
0x006577bc  fld dword [0xc7e304]   ; ha bármelyik eltér: időtartam = 0,6 s
0x006577ca  call 0x6558b0          ; új kulcskocka MINDKÉT sávra
0x006577d3  fadd qword [0xc7e328]  ; sorszám += 1,0  (a következő cellához)
```

**Kiolvasott konstansok** — egyik sem becslés:

| cím | típus | érték | mi |
|---|---|---|---|
| `0x00c7e304` | float | **0,6** | az átmenet **hossza másodpercben** |
| `0x00cf3ed0` | float | **−1,0** | az 1. sáv célértéke (állandó) |
| `0x00cf3f58` | double | −1,0 | ugyanez az összehasonlításhoz |
| `0x00c7e328` | double | 1,0 | a sorszám-léptető |

### A GÖRBE — `0x0072df60`, kiolvasva

Az `0x006558b0` a kulcskockába a `0x0072df60` **függvénymutatót** teszi
(`0x006558b3  mov dword ptr [esp], 0x72df60`). Ez maga a lazítás:

```
0x0072df60  fld1 / fcom            ; t ≥ 1 → 1,0     (telítés)
0x0072df78  fldz / fcom            ; t ≤ 0 → 0,0
0x0072dfab  fmul qword [0xc7ea10]  ; u = 8·t          (0xc7ea10 = 8,0)
0x0072dfce  call 0x40eac0          ; exponenciális
```

⇒ **exponenciális lazítás `u = 8·t` skálán**, nem lineáris és nem
koszinuszos. A `0x00c7ea10` = **8,0** kiolvasva.

### Mit jelent ez a felbukkanásra

1. **A vízszintes pozíció nem interpolálódik a tickben:** a
   `[cella+0xb0]`/`[cella+0xb4]` értéket a tick **közvetlen `mov`-val**
   írja (`0x00657827`, `0x0065782d`), miután a `0x00655950` kiszámolta. A
   „képernyőn kívüli parkolóhely" (`left = 10000`, ld. fent) tehát **nem**
   egy vízszintes becsúszás kiindulópontja.
2. **Ami tényleg animálódik:** a két sáv — az egyik célértéke **állandó
   −1,0**, a másiké a cella **sorszáma a veremben**. Amikor egy értesítés
   elbocsátódik és a többi feljebb lép, a sorszám megváltozik, és a cella
   **0,6 s alatt, exponenciális görbével** csúszik az új helyére.

**Bizalmi fok:** a szerkezet, a 0,6 s, a −1,0, a 8,0 és a görbe
**megerősített** (közvetlen kiolvasás). **NINCS MEG:** hogy a rajzoló
oldal a két sávértéket pontosan MELYIK képi mennyiséggé fordítja (eltolás,
átlátszóság, mindkettő) — ez a rajzoló ág olvasása, külön kör.


### A két sáv TELJES állapotgépe — mérve (#2122)

A #2034 megtalálta a két animált skalársávot; ez a szakasz a **teljes
életciklusukat** rögzíti. A `0x006558b0` (a sáv-író) hívási helyeit
kimerítően végigpásztáztam: **pontosan kettő van**.

| esemény | cél (A sáv, B sáv) | időtartam | hol |
|---|---|---|---|
| **létrehozás** | a struktúrák üresek, az érték **0,0** | — | `0x006557a0`, `0x006557b8` |
| **élő cella** (képkockánként) | (**−1,0** , a cella **sorszáma**) | **0,6 s** (`0x00c7e304`) | `0x006577ca` |
| **elbocsátás** | (**0,0** , **0,0**) | **0,3 s** (`0x00c7dcc8`) | `0x00655c98` |

⇒ Az „A" sáv a megjelenéskor **0 → −1**, az eltűnéskor **−1 → 0**; a „B" sáv
**0 → sorszám**, majd vissza 0-ra. **Az eltűnés kétszer gyorsabb, mint a
beállás** (0,3 s vs 0,6 s) — mindkét szám kiolvasva.

**Az elbocsátás egyben** (`0x00655be4`, a `0x00655c80`-tól):

```
0x00655c80  fldz                       ; 0,0
0x00655c83  fst  dword [esp+0x14]      ; cél[0] = 0,0   (A sáv)
0x00655c8b  fstp dword [esp+0x18]      ; cél[1] = 0,0   (B sáv)
0x00655c8f  fld  dword [0xc7dcc8]      ; 0,30 s
0x00655c98  call 0x6558b0
0x00655ca5  mov  byte [cella+0x11], 1  ; „elbocsátás alatt" jelző
0x00655cb0  fstp qword [cella+0xb8]    ; a HATÁRIDŐ nullázva
```

A `+0x11` jelzőt a tick nézi (`0x00657774`): amíg áll, a cellára **nem** állít
új célt — tehát az elbocsátás animációja nem kap ellenparancsot.

**A cella kezdőállapota** (a konstruktor, `0x006556e0`–`0x0065580a`):
`+0x80`/`+0x98` bájt = 0, `+0x88`/`+0xa0` = **0,0**, `+0x90`/`+0x94` és
`+0xa8`/`+0xac` = 0 (üres kulcskocka-tömbök), `+0xb0`/`+0xb4` = 0,0 (pozíció),
`+0xb8` = 0,0 (határidő), **`+0x0c` = −1,0** (`0x00cf3ed0` — ugyanaz a
konstans, amit a tick az A sáv céljának ad), `+0x04` = `0x7FFFFFFF`,
`+0x10` = 1.

**A sáv-struktúra alakja** (a `0x009e6010` fűzőből és a konstruktorból):
`+0x00` bájt jelző · `+0x08` qword **aktuális érték** · `+0x10` tömb-mutató ·
`+0x14` darabszám. A kulcskocka **40 bájt**, és az **első mezője a görbe
függvénymutatója** (`0x006558b3  mov dword ptr [esp], 0x72df60`).

**A kulcskocka-rendszer NEM az értesítőé:** a `0x009e6010` fűzőnek **22**
hívója van a binárisban (`0x0040b290`, `0x005a6e30`, `0x0072e1f0`,
`0x00809cd0`, … ) — általános animált-skalár szolgáltatás.

#### ⛔ NEGATÍV EREDMÉNY, mérve: az értesítő NEM olvassa a sávok értékét

> ⚠️ **A MÉRÉS ÁLL, A KÖVETKEZTETÉS NEM.** A `cella+0x88`/`+0xa0`
> gyorsítótárazott értéket tényleg nem olvassa senki rajzoláshoz — de a rajzoló
> **újra kiértékeli** a sávokat (`0x00658423`, `0x0065903b`, `0x006590b4` →
> `0x00655950`). A sávok jelentése ezzel megvan: ld. lent, „A két sáv
> JELENTÉSE — MEGVÁLASZOLVA (#2122)".

A `0x00654800`–`0x0065AC00` teljes tartományt (a `CNotifierPopup` és a
`CBaseNotifier` MINDEN vtable-metódusa beleesik) végigpásztáztam a
`cella+0x88` és `cella+0xa0` hozzáférésekre. Az összes találat:

| cím | mit csinál |
|---|---|
| `0x006559bc`, `0x006559e7` | a **legutolsó kulcskocka** kiolvasása (`0x006559b0`) |
| `0x006564eb`, `0x006564f7` | cella-**másolás** |
| `0x00656b8e`, `0x00656b95` | cella-**másolás** |
| `0x006557a0`, `0x006557b8` | a **konstruktor** nullázása |

**Rajzoló olvasás nincs köztük.** Ugyanígy a `cella+0xb0`/`+0xb4` (pozíció)
is csak írás és másolás. ⇒ A sávokat **valaki más** fordítja képi
mennyiséggé — a `yt` keretrendszer oldalán.

> **Ami tehát NINCS MEG:** melyik képi mennyiség (eltolás, átlátszóság,
> méret) olvassa a két sávot. A következő lépés a `yt` animált-tulajdonság
> rendszer **kiértékelője**: a `0x009e6010` szomszédságában lévő
> „érték időpillanatban" rutin, és az, hogy a cella melyik rajzoló
> hívásba adja át magát. Jegy: **#2122**.

**Bizalmi fok:** az állapotgép, a két időtartam (0,6 s / 0,3 s), a
kezdőértékek és a negatív pásztázás **megerősített** (közvetlen kiolvasás,
kimerítő keresés a megadott tartományon). A sávok *jelentése* **NINCS
MÉRVE** — a „(x-tényező, rekesz-sorszám)" olvasat kézenfekvő, de
bizonyítatlan, ezért nem is állítjuk.


#### A két sáv JELENTÉSE — MEGVÁLASZOLVA (#2122)

A #2034 és a #2122 köre a sávokat „absztrakt skalársávnak" nevezte, mert a
`cella+0x88` / `+0xa0` (a sávok pillanatnyi értéke) hozzáféréseit végigpásztázva
**nem talált rajzoló olvasást**. A pásztázás helyes volt — a következtetés
nem: a rajzoló **nem a gyorsítótárazott értéket olvassa, hanem újra kiértékeli
a sávokat**.

##### A lánc

```
0x00655950(cella) → out[2 float]
    edi = cella + 0x80 (A sáv) → call 0x009e5e70(t)   ; „érték t időpontban"
    edi = cella + 0x98 (B sáv) → call 0x009e5e70(t)
```

A `0x009e5e70` az **általános kulcskocka-kiértékelő**: ha a sávnak nincs
kulcskockája, a `[sáv+8]`-at adja vissza, egyébként interpolál.

**Két helyen hívják:**

1. a **tick**-ben (`0x006577ea`) — az eredményt összeveti a `cella+0xb0`/`+0xb4`
   párral, és **ha eltér**, beírja (`0x00657827`) és `[esp+0x16] = 1`-et állít.
   A jelzőt a tick vége nézi (`0x00657bda`), és a popup **vtable +0x50**
   metódusát (`0x00658340`) hívja — újrarajzolás. ⇒ a `+0xb0`/`+0xb4` **nem
   rajzolási forrás, hanem VÁLTOZÁS-ŐR** (utolsó ismert pozíció).
2. a **rajzolóban** (`0x00658423` méretezés, `0x0065903b` / `0x006590b4`
   cellaelhelyezés) — itt születik a tényleges képpont-pozíció.

##### A skálázás — ez adja meg a MÉRTÉKEGYSÉGET

A cellaelhelyezésben (`0x0065903b` ága):

```
0x00659040  fild [esp+0x74]        ; = [popup+0x1c0]
0x00659052  fmul [esp+0xdc]        ; × B sáv
0x00659061  fistp …                ; → Y
0x00659069  fild [esp+0x70]        ; = [popup+0x1bc]
0x0065907b  fmul [esp+0xd8]        ; × A sáv
0x0065908a  fistp …                ; → X
```

(`[esp+0x70] = [popup+0x1bc]`, `[esp+0x74] = [popup+0x1c0]`, beállítva a
`0x00658896`–`0x006588d2`-n.)

A `popup+0x1b4` a **`notifier/cell1` réteg** rekesze (ld. a rétegtáblát), a
rétegstruktúra `+8` mezője a **szélesség**, a `+0xc` a **magasság** — ezt a
fogantyú rajzolása bizonyítja (`0x0065879b`: `[esi+8]` szélességből vonja ki a
`[popup+0x1e4]`-et, `[esi+0xc]` a magasság). Tehát:

| mező | mi | érték (respack) |
|---|---|---|
| `popup+0x1bc` | `notifier/cell1` **szélessége** | **247 px** |
| `popup+0x1c0` | `notifier/cell1` **magassága** | **45 px** |
| `popup+0x1e4` | `notifier/basedecrect` **szélessége** | **21 px** |

**Független megerősítés a magasságra:** a kattintáskezelő a cella sorszámát
`(egérY − 2) / [popup+0x1c0]` alakban számolja (`0x00657eb4`) — ez csak akkor
ad sorszámot, ha a mező a **cellamagasság**.

##### A válasz

| sáv | mit szoroz | mit jelent | élő cella célja | elbocsátás célja |
|---|---|---|---|---|
| **A** (`cella+0x80`) | `247 px` (cellaszélesség) | **vízszintes eltolás cellaszélesség-egységben** | **−1,0** = −247 px | 0,0 = 0 px |
| **B** (`cella+0x98`) | `45 px` (cellamagasság) | **függőleges eltolás cellamagasság-egységben** | a cella **sorszáma** = sorszám × 45 px | 0,0 = 0 px |

⇒ **A `−1,0` jelentése: pontosan EGY cellaszélességnyi (247 képpont)
vízszintes eltolás.** A cella tehát a horgonyzási helyétől egy teljes
cellaszélességgel elcsúszva áll meg — ez a **becsúszás**, 0,6 s alatt,
exponenciális görbével; elbocsátáskor 0,3 s alatt csúszik vissza a 0-ra.

##### ⛔ HELYESBÍTÉS a #2034 köréhez

A #2034 köre azt írta: *„A becsúszás-hipotézis MEGDŐLT: a pozíciót
(`cella+0xb0`/`+0xb4`) a tick közvetlen `mov`-val írja (`0x00657827`), tehát a
képernyőn kívüli parkolóhely nem egy vízszintes animáció kiindulópontja."*

**Ez téves volt.** A `mov` valóban közvetlen, de az **általa írt érték a
sáv-kiértékelőtől jön** (`0x006577ea` → `0x00655950`), és a rajzoló amúgy is
újra kiértékel. A becsúszás **valódi**, és a mértéke pontosan egy cellaszélesség.

##### Az RTL-jelző — mért aszimmetria

A cellaelhelyezés a `0x00d678d4` globális bájton ágazik el. Ez a **jobbról
balra (RTL) elrendezés** jelzője: a `0x0098f8af`–`0x0098f8e1` blokk a
`Preferences` / `RTL` beállításkulcsból tölti (`0x00cd8b58` = `"RTL"`,
`0x00c7eafc` = `"Preferences"`). A programban **114** hivatkozás van rá.

**Mérve, aszimmetria:** a nem-RTL ágban (`0x0065903b`) az X-et az **A sáv**
adja (`round(A × 247) + [esp+0xc8]`), az RTL ágban (`0x006590ad`) viszont az X
egy kész értékből jön (`[esp+0xd0]`), és **csak a B sávot** használja. Az Y
mindkét ágban `round(B × 45) + 2`. Ennek az okát nem mértük ki — de a magyar
(balról jobbra) felület mindig a **nem-RTL** ágon megy, tehát a becsúszás
onnan olvasandó.

### A jobb sáv három rétege: EGYIK SEM vezérlő (#2035)

A `respack.yt` három réteget ad a cella jobb szélső, 21 képpontos sávjában
(`close`, `gripper`, `collapse`). A kérdés az volt, mit CSINÁLNAK. A válasz:
**a fogantyú puszta rajz, az összecsukás pedig meg sem jelenik.**

#### A rétegek slotjai — a betöltő (`0x00656fe0`) alapján

| slot | réteg | hivatkozások a `0x00654800`–`0x0065AC00` tartományban |
|---|---|---|
| `popup+0x114` | `notifier/close` | ctor · dtor · **rajz** (`0x006586a2`) |
| `popup+0x13c` | `notifier/collapse` | ctor (`0x00657046`) · dtor (`0x006572d3`) — **más SEMMI** |
| `popup+0x164` | `notifier/cellbase` | 5 |
| `popup+0x18c` | `notifier/gripper` | ctor · név · dtor · **rajz** (`0x0065878e`) |
| `popup+0x1b4` | `notifier/cell1` | 3 |
| `popup+0x1dc` | `notifier/basedecrect` | 4 |
| `popup+0x204` | `notifier/progressbase` | 4 |
| `popup+0x22c` | `notifier/progressfill` | 4 |

A rétegkezelő 0x28 = 40 bájtos; a nevek a `0x00ca268c`–`0x00ca2718`
sztringekből, a `0x00410fa0` értékadóval kerülnek a slotokba.

⇒ **Az `összecsukás` réteg betöltődik és felszabadul, de sosem rajzolódik
ki.** Halott erőforrás — mint a `#1869` kommentelt elemei.

#### Az ablak ÜZENETKEZELŐJE — a teljes lista

A `CNotifierPopup` vtable 11. rekesze, a `0x00657d10` (1253 b), pontosan
**hat** üzenetet kezel:

| érték | üzenet | hol |
|---|---|---|
| `0x201` | **WM_LBUTTONDOWN** | `0x00657e94` |
| `0x214` | WM_SIZING | `0x00657da9` |
| `0x216` | WM_MOVING | `0x00657db0` |
| `0x20` | WM_SETCURSOR | `0x006580db` |
| `0x10` | WM_CLOSE | `0x00658129` |
| `0x18` | WM_SHOWWINDOW | `0x0065815e` |

**NINCS `WM_MOUSEMOVE` (0x200) és NINCS `WM_LBUTTONUP` (0x202).** Húzáshoz
mindkettő kellene — az ablak tehát **nem tud vonszolást megvalósítani**.

A `WM_SETCURSOR` ága egyetlen kurzort tölt: `LoadCursorA(NULL, 0x7F00)` =
**IDC_ARROW** (`0x006580e0`–`0x006580ee`). Méretező vagy mozgató kurzor
sehol.

#### A kattintás — EGYETLEN téglalap, EGYETLEN jelző

```
0x00657e9f  movsx eax, word [msg+0xc]      ; x = LOWORD(lParam)
0x00657ea7  movsx eax, word [msg+0xe]      ; y = HIWORD(lParam)
0x00657eaf  add eax, -2
0x00657eb4  div dword [popup+0x1c0]        ; cellaIndex = (y − 2) / cellaMagasság
0x00657ed8  cmp …                          ; x ∈ [popup+0x12c , +0x11c + +0x12c)
0x00657eea  cmp …                          ; y ∈ [popup+0x130 , +0x120 + +0x130)
0x00657f13  mov byte [cella+0x14], 1       ; ★ az EGYETLEN következmény
```

Nincs külön találati vizsgálat a `close`, a `gripper` vagy a `collapse`
téglalapjára — **egy** doboz, **egy** jelző, a cellasor pedig osztásból jön.

**Bizalmi fok: megerősített.** A hivatkozás-számok kimerítő pásztázásból
valók a megnevezett tartományon (a `CNotifierPopup` és a `CBaseNotifier`
minden vtable-metódusa beleesik); az üzenetlista a kezelő teljes
végigolvasásából.

> **Következmény a megvalósításra:** a **fogantyút KI KELL rajzolni**
> (7 × 7, a cellán belül 233, 19), mert az eredetiben látszik — de
> **nem szabad megfogható vezérlőnek megépíteni**. Az **összecsukást
> egyáltalán nem rajzoljuk ki**. Jegy: **#2133**.

## Elszámolás — az öt eredeti kérdés állapota (2026-09-02, #1130 zárása)

A #1130 törzse még az első kör öt nyitott kérdését sorolta; a lap azóta
mindet megválaszolta. A jegy azért zárható, mert **saját kérdés nem
maradhat „félig nyitva"** — ami tényleg nyitott, annak önálló jegy jár.

| # | kérdés | állapot | hol |
|---|---|---|---|
| 1 | geometria | ✅ **LEZÁRVA** | „Geometria — MÉRVE A BINÁRISBÓL" + „Melyik ÉLHEZ képest a 144 képpont" |
| 2 | animáció | ✅ **LEZÁRVA** (#2034) — ütemforrás ÉS alak | „Az animáció ÜTEMFORRÁSA…" + „Az animáció ALAKJA — MÉRVE" |
| 3 | élettartam | ✅ **LEZÁRVA** | „A cella élettartama — MEGFEJTVE": abszolút határidő `+0xb8`-on, képkockánkénti ellenőrzés |
| 4 | észlelési ág | ✅ **LEZÁRVA** | „4. ág — új képek észlelése" |
| 5 | események listája | ✅ **LEZÁRVA** (bizonyítottan nincs ilyen lista) | „Hány eseménye van?" |

**A 2. pont maradéka** — becsúszik-e vagy áttűnik — a `0x006575b0`
(1714 bájt, a Popup képkockánkénti tickje) teljes diszasszemblálásával
válaszolható meg: ugyanaz a függvény kezeli a lejáratot ÉS a képkockánkénti
állapotot. A parkolóhely (`left = 10000`, ill. `-10001` jobbról-balra író
felületnél) továbbra is **nyom, nem bizonyíték**. Külön jegy: **#2034**.

### Ami a MEGVALÓSÍTÁSBÓL hiányzik

A geometria **három** vezérlőt ad a jobb oldali 21 képpontos sávban; a
`NotifierCell.qml` ebből **egyet** épít meg:

| réteg | méret | nálunk |
|---|---|---|
| `close` (231,4) | 11 × 11 | ✅ megvan |
| `gripper` (233,19) | 7 × 7 | ❌ hiányzik |
| `collapse` (231,30) | 11 × 11 | ❌ hiányzik |

A méret mindkettőnél mérve van, a **viselkedésük nincs** — a fogantyú
mozgatása ütközik a munkaterülethez horgonyzással (`0x00658200`), az
összecsukás célállapotának mérete pedig sehol nincs kimérve. Ezért nem
építjük meg találgatásból. Külön jegy: **#2035**.

#### Az ANIMÁCIÓ — nálunk halványítás, az eredetiben csúszás (#2157)

| | eredeti (mérve) | nálunk ma (mérve) |
|---|---|---|
| megjelenés | **vízszintes csúszás 247 px-en**, 0,6 s, exponenciális (`u = 8·t`) | `opacity` 0 → 1, **0,25 s** (`PicasaNotifier.qml:85`) |
| eltűnés | **visszacsúszás 0-ra**, 0,3 s | `opacity` 1 → 0, **0,5 s** (`:87`) |
| a cella függőleges helye | **animált**: sorszám × 45 px, ugyanaz a görbe | `Column` — azonnal ugrik (`:196`) |
| ütemezés | képkockánkénti tick, a pozíció újraszámolva | Qt `Behavior on opacity` |

Mérve: a `PicasaNotifier.qml`-ben és a `NotifierCell.qml`-ben **nincs**
`x`/`y` animáció — az egyetlen `Behavior` az átlátszóságé
(`notifierFadeAnim`, `:202`). Megvalósítás: **#2157**.

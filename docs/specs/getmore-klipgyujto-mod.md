# A „Továbbiak…" klip-gyűjtő mód (`thumbui/single_action_*`)

**Mi ez:** a Picasa 3 könyvtárablakának egy külön **üzemmódja**. Amikor egy
projektpanelből (kollázs, filmkészítő) képet akarsz behozni, a program a
**Könyvtár lapra vált, a projektet nyitva hagyja**, és a főablak alsó sávjában
megjelenik egy **üzenetsáv** egy visszatérő gombbal. A felhasználó közben
normálisan böngész és jelöl ki; a kijelölés a **képtálcára** kerül, onnan
veszi a projekt.

**A lap a MŰKÖDÉST írja le**, a geometria a végén áll.
Kiváltó: a `thumbui` UI-lefedettségi sor `single_action_*` hármasa
(#1878-as mérés). Testvérlapok:
[`picasa-keptalca.md`](picasa-keptalca.md) (a tálca),
[`picasa-kollazs-felulet.md`](picasa-kollazs-felulet.md) (a kollázs Klipek füle),
[`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md) (a méretlap).

## 1. MI AKTIVÁLJA — két mért belépési pont, HÁROM változat

### 1.1 A belépési pontok

*Forrás: `collagepanel.tre:206` (`collagepanel/getmoreclips`) · `makemoviepanel.tre:416` (`makemoviepanel/addclips`).*

| honnan | elem | felirat (EN / **HU**) | méret |
|---|---|---|---|
| kollázs, Klipek fül | `collagepanel/getmoreclips` | *Get more…* / **„Továbbiak…"** | 166 × 28 |
| filmkészítő | `makemoviepanel/addclips` | *Get More…* / **„Továbbiak…"** | (a `makemoviepanel` lapon) |

Buboréksúgók: `collagepanel/getmoreclips` = *Get more clips from the Library* /
**„További képek beolvasása a könyvtárból"**; `makemoviepanel/addclips` =
*Get more clips from Photo Library* / **„További klipek beolvasása a fotótárból"**.
(Forrás: `collagepaneltext.tre`, `makemoviepaneltext.tre`, és a hivatalos
magyar `referencia/panel-feliratok-hu.tsv` 129–130. és 566/600. sora.)
### 1.2 A visszatérő gomb HÁROM felirata — és pontosan három

A sáv gombja nem egy fix szöveg: **három külön változat** van, mindegyik
saját beállító függvénnyel és saját szövegtár-kulccsal.

| beállító | szövegtár-kulcs | EN | **HU** (hivatalos) | mire vált vissza |
|---|---|---|---|---|
| `0x0056c140` (365 b) | `collagepanel::back_to_collage` | Back to Collage | **„Vissza a kollázshoz"** | `panelroot/collagepanel` + `panelroot/collagetab` |
| `0x0056c2b0` (365 b) | `CMakeMoviePanel::back_to_slideshow` | Back to Movie Maker | **„Vissza a Mozgófilmkészítés párbeszédpanelhez"** | `panelroot/makemoviepanel` + `panelroot/makemovietab` |
| `0x0057ccb0` (274 b) | `thumbui::back_to_previous_tab` | Back to Previous Tab | **„Vissza az előző lapra"** | az előző lap (általános ág) |

**Hogy pontosan három van, ellenőrizhető:** a `single_action_container` és a
`single_action_return` elemnevekre a teljes bináris **négy** függvényt ad
(a fenti három + a `0x005d9cc0` elemnév-tábla); ezen kívül a
`single_action` minta sehol nem fordul elő.

*(A hívók: `0x0053c020` — a parancs-diszpécser, ami az `email`/`print`/
`collage`/`makemovie`/`uploadtogoogle` parancsokat is kezeli — és
`0x0057cdd0`; a filmkészítő ága a `0x0061df10` 12 420 bájtos panelkódból.
A magyar feliratok a `referencia/stringres-en-hu.tsv` 432., 2582. és
3282. soraiban.)*

## 2. MIT CSINÁL — a mód négy szabálya

### 2.1 A projekt lapja NYITVA marad

A visszatérő gomb `panelroot/collagetab` / `panelroot/makemovietab` felé vált
— **lapváltás, nem újranyitás**. A lapváltó ág (`0x005d4ef0`) ugyanabban a
függvényben kezeli a `single_action_container`-t, mint a
`picasatab`/`collagetab`/`makemovietab`/`acquiretab`/`capturemovietab`/`youtab`
lapokat és az `UITransitions`-t.

### 2.2 A kijelölés a KÉPTÁLCÁN keresztül megy a projektbe

A sáv felirata kimondja (`thumbui_text.tre` 202–203):

> *„Select items to add to your project's clips tray, then press the "Back"
> button to return to your project"*
> — hivatalosan: **„Jelölje ki azokat az elemeket, amelyeket a projekt
> kliptálcájára fel szeretne venni, majd a »Vissza« gombra kattintva térjen
> vissza a projekthez"**

Vagyis **nincs külön „hozzáadás" gomb**: a könyvtárbeli kijelölés maga tölti
a tálcát. Ez egybevág a tálca már lekutatott szerződésével
([`picasa-keptalca.md`](picasa-keptalca.md)): a tálca a kijelölés tükre, plusz
a külön megtartott elemek.

### 2.3 A ✕ CSAK ELREJTI a sávot — nem lép ki a módból

Ez a `.tre`-ben deklaratívan áll (`thumbui.tre:661–664`):

```
thumbui/single_action_close: thumbui/single_action_group
m_centerY
m_offsetR
Property hidetarget thumbui/single_action_container
```

A `hidetarget` a felületleíró **saját** mechanizmusa: kattintásra elrejti a
megnevezett elemet, kód nélkül. **Nincs mellette semmilyen kilépő hívás** —
a ✕ tehát nem visz vissza a projekthez és nem szakít meg semmit, csak
**eltünteti az útból az üzenetsávot**. A buboréksúgója (`Cancel "Get more"` /
**„A »Továbbiak« művelet megszakítása"**) ennél többet ígér, mint amit tesz.

### 2.4 A sáv ELTAKARJA az alsó gombsort

A sáv (`296…798`) pontosan a kimeneti terület fölé kerül:

| elem | tervezővászon | mit takar |
|---|---|---|
| `single_action_container` | **296…798**, y 479…519 | — |
| `webupload_rect` („Feltöltés a Google Fotókba") | 294…441, y 484…528 | **eltakarva** |
| `outputs` (Nyomtatás / E-mail / Exportálás) | 373…797, y 480…509 | **eltakarva** |

A rekordfejléc kilencedik bájtja a sávra **247** (a többi vizsgált rétegen
0), és a réteg típusa `decrect(softbevel/flatbevel)` — tehát **átlátszatlan
fedőréteg**, nem keret. ⇒ **Amíg a mód aktív, a felhasználó nem ér el
nyomtatást, e-mailt, exportálást, feltöltést.**

## 3. A sáv GEOMETRIÁJA

### 3.1 A tároló KÉNYSZER-vezérelt, nem fix méretű

`thumbui.tre:669–675`:

```
thumbui/single_action_container: thumbui/basecontrolset
m_offsetT
XConstraint 0, .365, 2      # bal él  = a basecontrolset 36,5%-a + 2
XConstraint 1, 1, -20       # jobb él = a jobb szél − 20
YConstraint 0, 0, 45        # felső él = a tetejétől + 45
YConstraint 1, 1, -2        # alsó él  = az aljától − 2
m_hidden                    # ALAPBÓL REJTETT
```

⚠️ **A `respack.yt`-ben tárolt 502 × 40-es téglalap NEM a futásidejű méret.**
A `basecontrolset` a tervezővásznon `0…800 / 429…534`, amire a kényszer
`294…780 / 474…532`-t ad — a tárolt téglalap `296…798 / 479…519`. A kettő
nem egyezik, és a
[`kek-info-sav.md`](kek-info-sav.md) 6.2-ben méréssel eldöntött szabály
szerint **ilyenkor a kényszer a törvény**.

*Ez helyesbítés:* a [`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md)
5.8 szakasza a sávot **„az »egy művelet« sáv (haladásjelzés)"** néven,
502 × 40-es fix méretként adta ki. A név téves — nem haladásjelzés —, és a
méret sem normatív.

### 3.2 A sáv TARTALMA viszont fix méretű

Ezeknek nincs méret-kényszerük, tehát a tárolt téglalap érvényes:

| elem | méret | kötés (`thumbui.tre`) |
|---|---:|---|
| `single_action_group` | **481 × 30** | `m_centerXY` a tárolóban |
| `single_action_message` | **335 × 26** | `m_offsetL`, `m_displayfont14`, **`Property textalign right`** |
| `single_action_return` | **109 × 43** | `m_offsetR`, `YConstraint 0.5, 0.5, 1` |
| `single_action_close` | **18 × 18** | `m_centerY`, `m_offsetR` |

A `109 × 43`-as gomb **magasabb**, mint a 30 képpontos csoport: a
tervezővásznon a csoport `y 485…515`, a gomb `y 478…521` — fölé és alá is
kilóg 6–7 képponttal. Az üzenet **jobbra igazított**, tehát a gomb felé fut.

### 3.3 A visszatérő gomb NEGYEDIK állapota („throb")

A gomb makrója `button_text_center_throb`, ami a közönséges
`button_text_center`-től **egyetlen sorban** tér el: hozzáveszi a
`globalbuttons/b1_decrect_t` bőrt (27 × 27) negyedik állapotként.

A négy állapot kimérve (a `_n`-hez képest, képpontonkénti eltérés):

| állapot | eltérő képpont / 729 | mi változik |
|---|---:|---|
| `_p` (lenyomva) | 532 | a kitöltés `#E8E8E8` → `#D9DEE3` |
| `_h` (fölé húzva) | 105 | halvány élkiemelés |
| **`_t` („throb")** | **196** | **csak a KERET**: `#BBBBBB` → **`#629BC3`**, belső gyűrű **`#9CC0D9`**; a kitöltés változatlan `#E8E8E8` |

A `throb` valódi futásidejű állapot: a felületleíró ismeri
`Property throb 1` alakban (`button_output_feature.tre`), a bináris pedig
tartalmazza a `throb` tulajdonságnevet (`0x009ca5e0`) és az **`eThrobOff`**
kapcsolót (`0x00601090`; `0x0062b370`-ben `eThrobOff thumbui/webcambutton`
alakban).

#### ⭐ A throb MECHANIZMUSA kimérve (2026-09-05) — és a korábban javasolt út ROSSZ volt

> **Bizonyítottsági fok: megerősített** a mechanizmusra és a
> sztring-leltárra; a konkrét gombra vonatkozó kérdés **BLOKKOLT marad**,
> de sokkal élesebben.

**A jelző helye és kezelői** (mind kiolvasva):

| mi | cím | mit tesz |
|---|---|---|
| a jelző maga | **`elem + 0x35b`**, egy bájt | 1 = throb be |
| a `.tre` `Property throb 1` beállítója | `0x009c7891` | `mov byte [eax+0x35b], 1` — **elemzési időben**, a felületleíróból |
| az **`eThrobOff`** parancs kezelője | `0x00601eb0` | `mov byte [eax+0x35b], **0**` — a parancsnév 10 bájtos összevetése `0x00601e5f`-en |
| futásidejű **bekapcsolás**, NÉVVEL | `0x0062c3ac` (`FUN_0062c340`, 183 b) | a `thumbui/webcambutton` elemre |
| futásidejű bekapcsolás, **név nélkül** | `0x00609251` és `0x00609605` (mindkettő a `FUN_00608da0`-ban, 2261 b) | az elem egy verem-rekeszből jön (`mov edi,[esp+0x34]`), nem literál |

**⛔ HELYESBÍTÉS — a korábban javasolt megszerzési út zsákutca.** A lap
eddig azt írta: *„Megszerzés: célzott Ghidra-kör a `0x00601090`-re
(`eThrobOff`)."* Ez **nem vezethet célra**: a `0x00601090` a
**parancs-diszpécser**, és az `eThrobOff` ága ott a jelzőt **kizárólag
TÖRLI** (`0x00601eb0`, a beírt érték `0`). A bekapcsolásról semmit nem
mond. A helyes cél a **`FUN_00608da0`**.

**Kimerítő sztring-leltár** (nyers bájtkeresés a teljes fájlon,
`[Tt]hrob` mintára): **három** találat, több nincs —
`throb` (`0x00c7cbe4`, a tulajdonságnév), `eThrobOff` (`0x00c9a038`) és
`eThrobOff thumbui/webcambutton` (`0x00c9e058`). **`eThrobOn` NINCS.**

⇒ **A binárisban EGYETLEN elemet nevez meg throb-bal kapcsolatban: a
`thumbui/webcambutton`-t.** A `single_action_return` gombra sem
`Property throb 1` a `.tre`-ben, sem névvel megcímzett parancs nincs.

**✅ LEZÁRVA (2026-09-05, 125. kör) — a visszatérő gomb NEM villog.**
A két név nélküli bekapcsoló (`0x00609251`, `0x00609605`) ugyanabban a
`FUN_00608da0`-ban ül, és az **nem** egy meglévő felületi elemre hat:

| lépés | bizonyíték |
|---|---|
| a függvény **új objektumot gyárt** | `0x00608db1`: `push 0x420` (1056 bájt) → `call 0x0097c5d0` (foglalás), majd `0x00608dca`: `call 0x00608700` (konstruktor) |
| kié a függvény | a `0x00608da0` mutatója a `.rdata`-ban **egyszer** áll: `0x00c80594` ⇒ vtábla-fej `0x00c8058c`, **2. rés** |
| melyik osztályé | a vtábla −4 helyén a COL `0x00cf853c`, `offset = 0` ⇒ **`ytPopupListNodeCreator`** |

⇒ A két bekapcsolás a **frissen létrehozott felugró-lista tételre** hat,
nem a `thumbui` sávjában álló, `.tre`-ből származó gombra. A
`single_action_return` **nem lehet** a célpontjuk.

**Ezzel a teljes bizonyítás:** a gombra (a) a `.tre` nem ír
`Property throb 1`-et, (b) nincs rá névvel megcímzett `eThrobOff`/throb
parancs (a binárisban egyetlen elemnév van, a `thumbui/webcambutton`), és
(c) a két név nélküli bekapcsoló más objektumfajtára hat. ⇒ **A visszatérő
gomb villogása kizárva.** A negyedik (`_t`) bőr rajta **használatlan**.

⚠️ **Amit ez NEM mond meg** (mérve nincs, és NEM is ennek a lapnak a
kérdése): **melyik** felugró-lista tétel villog és **mikor** — a feltétel
(`[esp+0x168]`, illetve `[esp+0xb8]`) a `FUN_00608da0` helyi rekesze,
amelyet egy korábbi hívás tölt fel. A `ytPopupListNodeCreator`
viselkedése külön téma.



## 4. Eredeti / nálunk / teendő

A „nálunk" oszlop **mérés** a `9a4f98ac` main-en.

| | eredeti (mért) | nálunk (mért) | teendő |
|---|---|---|---|
| belépési pont, kollázs | `getmoreclips`, „Továbbiak…", 166 × 28 | **megvan** — `CollageClipsTab.qml:97`, 166 × 28 ✓ | — |
| belépési pont, filmkészítő | `makemoviepanel/addclips` | **nincs film-panel** (a `qml/PicasaPy` mappában egyetlen `*Movie*.qml` sincs) | #432 |
| a jelzés fogadója | lapváltás a Könyvtárra | **megvan** — `Main.qml:1881` | — |
| visszatérő gomb helye | az **alsó sávban**, a kimeneti gombok fölött | **jobbra fent**, a lapsáv alatt (`Main.qml:1900–1911`) | áthelyezni |
| üzenetszöveg | **335 × 26**, jobbra igazított, `displayfont14` | **nincs** | felvenni |
| ✕ elrejtő gomb | **18 × 18**, csak elrejt | **nincs** | felvenni |
| a gombsor eltakarása | a sáv **átlátszatlanul fedi** a Nyomtatás/E-mail/Export/Feltöltés sort | nem takar semmit | eldöntendő a megvalósításkor |
| a gomb felirata | **három** változat (kollázs / film / előző lap) | egy: „Back to Collage" | a másik kettő a saját panelével együtt |
| gombméret | **109 × 43** | `PicasaButton` alapméret | 109 × 43 |

## 5. Nyitott kérdések mérlege

`0 nyílt · 6 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| mi aktiválja a módot | **LEZÁRVA** — két belépési pont, 1.1 |
| hány változata van a visszatérő gombnak | **LEZÁRVA** — pontosan három, 1.2 |
| mi történik a kijelöléssel | **LEZÁRVA** — a tálcán át, külön gomb nélkül, 2.2 |
| mit tesz a ✕ | **LEZÁRVA** — csak elrejti a sávot (`hidetarget`), 2.3 |
| hol van a sáv | **LEZÁRVA** — az alsó sávban, a kimeneti gombok fölött, 2.4/3.1 |
| a sáv mérete | **LEZÁRVA** — a tároló kényszer-vezérelt, a tartalma fix, 3.1–3.2 |
| villog-e a visszatérő gomb | ✅ **LEZÁRVA (2026-09-05), NEGATÍVAN** — a két név nélküli throb-bekapcsoló a `ytPopupListNodeCreator` **2. rése** (`0x00c80594` → vtábla `0x00c8058c`, COL `0x00cf853c`), és **frissen gyártott felugró-lista tételre** hat (`push 0x420` + konstruktor), nem `.tre`-elemre ⇒ a `single_action_return`-t nem érintheti. Korábbi állapot: — a throb jelző az `elem+0x35b`; a `.tre` állítja be, az `eThrobOff` parancs **csak törli** (`0x00601eb0`); futásidőben három hely kapcsolja be, ebből **egy névvel** — és az a `thumbui/webcambutton`. A binárisban `eThrobOn` **nincs**, és a visszatérő gombot **semmi nem nevezi meg**. ⛔ A korábban javasolt `0x00601090` **zsákutca** (az a parancs-diszpécser, csak töröl). **Új út:** a `FUN_00608da0` (virtuális metódus, 0 közvetlen hívó) vtábla-résének felderítése. 3.3 |

## 6. Amit KIZÁRTAM

- **„a `single_action_*` haladásjelző sáv"** — a
  `konyvtar-ablak-meretek.md` 5.8 így nevezte. **Téves:** a felirat, a
  buboréksúgók és a három visszatérő változat mind a klip-gyűjtő módról
  szólnak; haladásra utaló elem (folyamatsáv, százalék, `progress` token)
  nincs a csoportban.
- **„a ✕ kilép a módból"** — nem: a `.tre` `hidetarget`-je csak elrejt.
- **„a sáv fix 502 × 40"** — nem: négy kényszere van, azok döntenek.

*Bizonyítottsági fok: **megerősített** a belépési pontokra, a három
változatra, a feliratokra és a ✕ viselkedésére (mind deklaratív vagy
szövegtári forrásból); **erős** a kijelölés → tálca útra (a felirat + a
tálca már mért szerződése); a throb **mechanizmusa 2026-09-05 óta mérve** (a jelző `elem+0x35b`, a be/ki kapcsolók címmel); a *visszatérő gombra* vonatkozó bekapcsolás **továbbra sincs mérve**.*

---

Jegyek: **#1939** (az üzenetsáv megvalósítása) · **#1153** (a Klipek fül) ·
**#432** (a filmkészítő panel, és vele a második belépési pont).

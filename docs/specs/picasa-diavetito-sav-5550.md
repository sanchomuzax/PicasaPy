# A diavetítő vezérlősávja: kilépés, auto2 és átmenet-választó (#5550)

Ez a lap a #5550 jegy három tételét dolgozza fel. Az előzmény a #5537 kör
lapja (`docs/specs/picasa-diavetito-sav.md`), amely ebben a munkafában nincs
meg; a `git show origin/research/5537-haiku:docs/specs/picasa-diavetito-sav.md`
adja. Ezért ez önálló lap.

Minden állítás mellett cím vagy `fájl:sor` áll. Ami nem igazolható, az
`NINCS MEG`, és mellette az áll, mi kellene hozzá.

## 1. #5550: kilépés, auto2, átmenet-választó

### 1.1 Mit kérdeztünk

1. `exit`: az ikonja (a `.tre` szerint) és a kattintás művelete (melyik ág a
   `0x008032e0`-ban, és mit hív).
2. `auto2`: hol szerepel, és mikor látszik az `auto` helyett.
3. `transtype`: a lista tartalma és sorrendje, és hova íródik a választás.
4. Tételenként: egyezik-e a mai `SlideshowView.qml`.

### 1.2 Forrás és módszer

- Erőforrás: `referencia/tre-eroforrasok/oneup.tre`, `macros.tre`,
  `oneuptext.tre` (fájl:sor).
- Bináris: a `pe_dis.cdis` diszasszembly és a `picasa3-index.sqlite` táblái
  (`functions`, `xrefs`, `string_xrefs`, `rtti`). Vizsgált törzsek:
  `0x008032e0` (kattintás-diszpécser), `0x008037e0` (láthatóság-kezelő),
  `0x00771a10` (átmenet-lista), `0x0075d810` (szerkesztőpanel), `0x00760b00`
  (az írás helye), `0x00401900` és `0x004019b0` (DWORD író és olvasó),
  `0x00407a20` (a kulcs-objektum).
- Mai kód: `src/picasapy/app/qml/PicasaPy/SlideshowView.qml`,
  `src/picasapy/app/controller.py`, `src/picasapy/app/qml/Main.qml`.
- Atlasz (`atlasz_keres.py`): a fenti címekre a meglévő lapok már hivatkoznak
  (`picasa-menu-parancsok-viselkedes.md`, `picasa-create-features.md`
  4.3 és 4.5 szakasz). Ezeket összevetettük, nem ismételtük meg.

### 1.3 Tételenként

#### 1.3.1 `exit` (kilépés)

| elem | eredeti forrás | mai kód | eredmény |
|---|---|---|---|
| felirat | `oneuptext.tre:7-8` (`Label oneup/bcklabel`, „Exit”) | `SlideshowView.qml:990` (`"✕ " + qsTr("Exit")`) | EGYEZIK (a szöveg) |
| ikon: helye | `oneup.tre:28-29` (`oneup/exit_icon: oneup/exit`, `m_buttoniconleft`). A makró (`macros.tre:149-151`): `XConstraint 0, 0, 9`, `YConstraint 0.5, 0.5, 0`, vagyis a bal széltől 9 képpont, függőlegesen középen. | nincs külön ikon-elem; a ✕ jel a szövegben van (`SlideshowView.qml:990`) | ELTÉR |
| ikon: grafika | a `.tre` nem hivatkozik képre az `exit_icon`-on | - | NINCS MEG (a képazonosító; lásd N7) |
| kattintás: ág | `0x00803527`: név-összehasonlítás `oneup/exit`-tel (`0xcbd538`, 11 bájt), `0x0080352d`-`0x0080353b`. A találat ága: `0x00803561`-`0x00803573`. | `SlideshowView.qml:992` (`onClicked: show.stop()`) | lásd a következő sort |
| kattintás: művelet | `0x00803566`: `X = this->vt[+0x24]()`. `0x00803573`: `X->vt[+0x14](0, 0)`, két nulla argumentummal. A `this` a `OneUpUI` objektum: a vtáblát (`0xcbd5c4`) a `0x00802c60` konstruktor tölti be (`0x00802c7f`). A `vt+0x24` = `0x00a6ccf0` = `mov eax, [ecx+0x50]` és `ret` (`0x00a6ccf0`-`0x00a6ccf3`), tehát `X = this->[+0x50]`. | `show.stop()` (`SlideshowView.qml:259`) | NINCS MEG (az `X` osztálya és a `vt+0x14` metódusa) |

**Eredeti / Nálunk / Teendő (kattintás művelet):**

- **Eredeti:** `X->vt[+0x14](0, 0)`, ahol `X = this->[+0x50]`. Az `X`
  osztálya NINCS MEG.
- **Nálunk:** `show.stop()`.
- **Teendő:** nincs jegyjavaslat a műveletre, amíg az `X` osztálya nincs meg.
  A `+0x50` mezőt a vtábla 10. eleme (`vt+0x28` = `0x00a6cd00`, `mov [ecx+0x50], eax`,
  `ret 4`) állítja. Ennek hívóhelye közvetett hívás, a sztring-index nem
  látja (N1).

#### 1.3.2 `auto2`

| elem | eredeti forrás | mai kód | eredmény |
|---|---|---|---|
| hely a `.tre`-ben | `oneup.tre:20-23`: `oneup/auto2: root`, `m_scaleX`, `YConstraint 0, 0, 0`, `YConstraint 1, 1, -97`. A gyökér gyermeke, nem a `stripback`-é. Nincs ikon és nincs rejtő-jelzés. | nincs `auto2` elem | ELTÉR (hiányzik) |
| geometria (meglévő lap) | `picasa-create-features.md:7373-7376`: `vbutton: auto2`, pozíció (0, 0), méret 800 × 14, „a teljes szélességű felső kattintósáv”. Ez a meglévő lap állítása a `respack.yt`-ből. A `respack.yt` nincs a munkafában, ezt ebben a körben nem olvastuk újra (N3). | nincs | ELTÉR (hiányzik) |
| kattintás: ág | `0x00803491`-`0x008034bd`: név-összehasonlítás `oneup/auto2`-vel (`0xcbd51c`, 12 bájt). A találat ága: `0x008034c1`-`0x008034c5`, `call 0x00803110`, az `eax` a `this`. | nincs. A vetítő `MouseArea`-ja (`SlideshowView.qml:898-912`) vetítésen kívül `Qt.NoButton`, és nincs kattintás-művelete. | ELTÉR (az eredetiben kattintás van, nálunk nincs) |
| `auto` ugyanaz a hívás | `0x00803452`-`0x00803480` (`oneup/auto`, `0xcbd510`, 11 bájt). `0x00803486`: `call 0x00803110`, ugyanazzal a `this` argumentummal. | `SlideshowView.qml:1000-1004` (`slideshowPlayButton`, `show.togglePause()`) | az `auto` és az `auto2` ugyanazt a függvényt hívja |
| mikor látszik az `auto` helyett | Név szerinti láthatóság-váltás nincs a `0x008037e0`-ban: az csak `oneup/timeline` (`0xcbd528`) és `oneup/transtype` (`0xcbd54c`) nevet használ. A két név konstans címe (`0xcbd510`, `0xcbd51c`) a sztring-index szerint közvetlen címként csak a `0x008032e0`-ban szerepel. A `.tre`-ben sem az `auto`, sem az `auto2` nem kap rejtő-jelzést. | nincs megfelelő | NINCS MEG (lásd N2) |

**A `0x00803110` törzséhez:** a függvény nem olvassa a lejátszás állapotát.
A `[esi+0x518] = 1` beállítás feltétel nélkül történik (`0x00803131`). Csak a
`0x00801cf0` hívás függ a `[esi+0x3be]` mezőtől (`0x0080311d`-`0x00803127`).
A QML `togglePause()` (`SlideshowView.qml:479`) viszont invertál. Az `auto` és
a `togglePause` egyezését ez a kör nem igazolta (N2). A szóköz-ágat a meglévő
lap írja le: `picasa-menu-parancsok-viselkedes.md:3674` és `:3823`.

#### 1.3.3 `transtype` (átmenet-választó)

**a) A teljes lista a binárisban: 22 belső kulcs.** A `0x00771a10` (934 bájt)
egyszeri, első híváskor lefutó inicializálással épít táblát. Minden kulcs egy `push <kulcs>`, egy `mov eax, <cím>` és egy
`call 0x009ae560` hármas, ebben a sorrendben. Az `i`-edik rekord címe
`0xd34188 + 16·i`, ha `i < 22` (`0x00771d8e`-`0x00771d98`).

| i | belső kulcs | a `push` címe | alapértelmezett angol név | a sztring címe (`mov eax`) |
|---|---|---|---|---|
| 0 | `CTransitions::cut` | `0x00cb2d10` | Cut | `0x00cb2ca0` |
| 1 | `CTransitions::kenburns` | `0x00cb2d24` | Pan and Zoom | `0x00cb2c84` |
| 2 | `CTransitions::dissolve` | `0x00cb2d3c` | Dissolve | `0x00cb2c6c` |
| 3 | `CTransitions::dissolveblack` | `0x00cb2d54` | Dissolve through black | `0x00cb2c44` |
| 4 | `CTransitions::dissolvewhite` | `0x00cb2d70` | Dissolve through white | `0x00cb2c1c` |
| 5 | `CTransitions::wipeleft` | `0x00cb2d8c` | Wipe - left | `0x00cb2c04` |
| 6 | `CTransitions::wiperight` | `0x00cb2da4` | Wipe | `0x00cb2bf0` |
| 7 | `CTransitions::wipeup` | `0x00cb2dbc` | Wipe - top | `0x00cb2bdc` |
| 8 | `CTransitions::wipedown` | `0x00cb2dd4` | Wipe - bottom | `0x00cb2bc0` |
| 9 | `CTransitions::circleout` | `0x00cb2dec` | Circle | `0x00cb2bac` |
| 10 | `CTransitions::circlein` | `0x00cb2e04` | Circle - inwards | `0x00cb2b8c` |
| 11 | `CTransitions::pushleft` | `0x00cb2e1c` | Push - left | `0x00cb2b74` |
| 12 | `CTransitions::pushright` | `0x00cb2e34` | Push | `0x00cb2b60` |
| 13 | `CTransitions::pushtop` | `0x00cb2e4c` | Push - top | `0x00cb2b4c` |
| 14 | `CTransitions::pushdown` | `0x00cb2e64` | Push - bottom | `0x00cb2b30` |
| 15 | `CTransitions::rect` | `0x00cb2e7c` | Rectangle | `0x00ca000c` |
| 16 | `CTransitions::diagwipeur` | `0x00cb2e90` | Wipe - up right | `0x00cb2b0c` |
| 17 | `CTransitions::diagwipedl` | `0x00cb2eac` | Wipe - down left | `0x00cb2aec` |
| 18 | `CTransitions::diagwipedr` | `0x00cb2ec8` | Wipe - down right | `0x00cb2acc` |
| 19 | `CTransitions::diagwipeul` | `0x00cb2ee4` | Wipe - up left | `0x00cb2ab0` |
| 20 | `CTransitions::kenburnsaoi` | `0x00cb2f00` | Pan and Zoom - face | `0x00cb2a90` |
| 21 | `CTransitions::timelapse` | `0x00cb2f1c` | Time Lapse | `0x00cb2a78` |

A `mov eax` cím a `0x009ae560` bemenete. A visszatérési ágat nem követtük
végig, ezért a sztringet alapértelmezettnek nevezzük. A `picasa-create-features.md:6930`
sor a `CTransitions::kenburnsaoi` stringres-bejegyzését említi ugyanezzel a
névvel. A többi név stringres-egyezését ebben a körben nem ellenőriztük.

**b) A választó 7 eleme.** A `0xd342e8` címen 7 dword áll: `0, 1, 2, 6, 9, 12, 15`.
Ezek a 22-es lista indexei. A QML lista (`SlideshowView.qml:100-107`) ugyanebben
a sorrendben ugyanezeket a neveket adja.

| választó-index | belső kulcs (22-es index) | felirat | QML sor | eredmény |
|---|---|---|---|---|
| 0 | cut (0) | Cut | 101 | EGYEZIK |
| 1 | kenburns (1) | Pan and Zoom | 102 | EGYEZIK |
| 2 | dissolve (2) | Dissolve | 103 | EGYEZIK |
| 3 | wiperight (6) | Wipe | 104 | EGYEZIK |
| 4 | circleout (9) | Circle | 105 | EGYEZIK |
| 5 | pushright (12) | Push | 106 | EGYEZIK |
| 6 | rect (15) | Rectangle | 107 | EGYEZIK |

A felugró lista 7 elemű. A `0x0075db71` sor `cmp eax, 0x1c` (28 bájt), a
`0x0075db78` `jb 0x0075d9a0` ugrás a 4 bájtos lépéssel: 7 iteráció. A QML
`model:` (`SlideshowView.qml:1032`) is 7 elemet ad. Eredmény: a lista tartalma
és sorrendje EGYEZIK.

A `SlideshowView.qml:1030` megjegyzés („a 22 soros lista a képernyő alján álló
sáv fölé nyílik”) ELTÉR: a felugró lista 7 soros. A 22 a teljes belső lista.

**c) Hova íródik a választás.**

- Az író a `0x00760b00` (578 bájt). Egyetlen hívója a `0x005d3290`
  (`xrefs`). A meglévő lap szerint a hívó `0x005d3290` az `editoneup/transtype`
  ága (`picasa-create-features.md:6815`).
- Az érték: `[edx+0x320] + [edx+0x2f8]` (`0x00760c33`-`0x00760c39`). Ellenőrzés:
  `cmp edi, 7` (`0x00760c3f`). A 7-es táblából olvas (`0x00760c4c`). Az érték
  a `[esp+0x14]` mezőbe kerül (`0x00760c42`), és a `0x00760ca5` sorban a
  `call 0x00401900` írja ki. Tehát a DWORD a 0-6 választó-index, nem a 22-es index.
- A kulcs: szekció `Preferences` (`0xc7eafc`), értéknév
  `ThumbUISlideShow::transition` (`0xcb22b0`, `0x00760c75`-`0x00760c7a`). A
  kulcs-objektumot a `0x00407a20` hozza létre (`0x00760c98`). A gyökér
  `0x80000001` (HKEY_CURRENT_USER), a `0x00407a3b` sorban. Az alapérték `2`
  (`0x00760c90`), ez a Dissolve.
- Az író `0x00401900`: a `[edi+0xc]` mezőbe írja az értéket (`0x00401917`), majd
  hat argumentummal hívja a `[0xd694f0]` célt (`0x00401969`-`0x00401970`). A
  hat argumentum: a kulcs, az értéknév, 0, a típus (`[edi+0x14]`), az
  adatmutató (`[edi+0xc]`) és a méret (4). Ez egy DWORD-írás. A kulcs
  megnyitása előtt a `0xf003f` (KEY_ALL_ACCESS) jogkör van a verembe
  téve (`0x00401940`), a nyitó függvény a `0x009a4890`.
- Az API-név: NINCS MEG. A `[0xd694f0]` cella tartalma (`0xff009a07`) nem
  olvasható import-névre. Az index import-táblája ezen a helyen hibás: minden
  sora `RegCloseKey`, ugyanazzal a címmel (N5).
- A teljes út (gyökér + `Preferences`): NINCS MEG. A `0x00407a20` a
  `[ebx+0x18]` objektum `vt+4` metódusát hívja (`0x00407a4d`-`0x00407a50`), a
  visszatérése az előtag. Az index két registry-sztringet ad: `Google\Picasa2`
  (`0x00c7eaec`) és `SOFTWARE\Google\Picasa\` (`0x00c7f0c4`). Melyik a valódi
  előtag, az NINCS MEG (N4).
- A `0x00760d19` sorban egy második írás van: értéke 8 vagy 3
  (`0x00760cec`, `0x00760d0d`). Kulcsa NINCS MEG (N6).
- Olvasó: a szerkesztő `0x0075d860` (`call 0x004019b0`). A `cmp eax, 6` és a
  `ja` (`0x0075d865`-`0x0075d872`) miatt a 6-nál nagyobb érték helyett 6 kerül
  be.

**d) Nálunk.** A `controller.py:540-554` a `view/slideshowTransition`
QSettings-kulcsba ír, sztring értékkel. Az alapérték `"dissolve"`
(`controller.py:543`). A beállító a hét kulcsos készletre szűr
(`controller.py:552`; a készlet a `controller.py:120`-ban van). A
`Main.qml:3104-3107` ezt olvassa. A `controller.py:538` szerint a
registry-kulcsok egy az egyben való átvétele nem cél. Eredmény: ELTÉR
(tárolási forma: a binárisban DWORD 0-6, nálunk sztring-kulcs).

**e) Láthatóság (kiegészítés).** A `0x008037e0` a `oneup/timeline` és a
`oneup/transtype` csomópontot kölcsönösen kapcsolja. A jelző:
`f = (0x004019b0 visszatérése == 0) VAGY ([0xd33958] nem 0x10 és nem 0x20) VAGY
(a paraméter-objektum +1 bájtja ≠ 0)` (`0x0080381e`-`0x0080384e`). Ha `f` igaz,
a timeline `vt+0x6c`-t, a transtype `vt+0x68`-at kap. Ha hamis, fordítva
(`0x00803a03`-`0x00803a83`). A `vt+0x68` és `vt+0x6c` jelentése NINCS MEG, a
meglévő lap is nyitottnak írja (`picasa-create-features.md:6890`, N8). Nálunk a
`PicasaComboBox` mindig látszik (`SlideshowView.qml:1027-1040`, nincs
`visible` kötés). ELTÉR.

### 1.4 Egyezik-e a mai `SlideshowView.qml`: összegzés

| # | tétel | mai kód (fájl:sor) | eredmény |
|---|---|---|---|
| 1 | `exit` felirat | `SlideshowView.qml:990` | EGYEZIK |
| 2 | `exit` ikon | `SlideshowView.qml:990` (szöveges ✕) | ELTÉR (grafika NINCS MEG) |
| 3 | `exit` művelet | `SlideshowView.qml:992` (`show.stop()`) | NINCS MEG (az `X` osztálya) |
| 4 | `auto2` elem | nincs (`SlideshowView.qml:898-912`) | ELTÉR (hiányzik) |
| 5 | `auto2` láthatósága | nincs | NINCS MEG |
| 6 | `transtype` lista (7 elem) | `SlideshowView.qml:100-107` | EGYEZIK |
| 7 | `transtype` megjegyzés („22 soros”) | `SlideshowView.qml:1030` | ELTÉR |
| 8 | `transtype` tárolás | `controller.py:540-554` | ELTÉR (DWORD 0-6 és sztring-kulcs) |
| 9 | `transtype` láthatóság | `SlideshowView.qml:1027-1040` | ELTÉR (nálunk mindig látszik) |

**Jegyjavaslatok** (Eredeti / Nálunk / Teendő):

- **`exit` művelet.** Eredeti: `X->vt[+0x14](0, 0)`, `X = this->[+0x50]`.
  Nálunk: `show.stop()`. Teendő: előbb az `X` osztályát kell megtalálni (N1).
- **`exit` ikon.** Eredeti: külön ikon-gyermek, bal oldalon 9 képponttal,
  függőlegesen középen (`oneup.tre:28-29`, `macros.tre:149-151`). Nálunk:
  szöveges ✕ jel (`SlideshowView.qml:990`). Teendő: a grafika azonosítása (N7).
  A `picasapy-research` skill 5. szakasza szerint a felület az eredetit
  követi, ezért ez nem UI-kérdés.
- **`auto2`.** Eredeti: 800 × 14 képpontos felső kattintósáv, amely a
  `0x00803110`-at hívja (geometria: meglévő lap, `picasa-create-features.md:7373-7376`).
  Nálunk: nincs ilyen elem. Teendő: a láthatóság (N2) és a geometria (N3)
  tisztázása, csak utána jegy.
- **`transtype` megjegyzés.** Eredeti: 7 elemű felugró lista (`0x0075db71`).
  Nálunk: a „22 soros” megjegyzés (`SlideshowView.qml:1030`). Teendő: a
  megjegyzés javítása 7 elemre. Csak szöveg, nem viselkedés.
- **`transtype` tárolás.** Eredeti: DWORD 0-6 a
  `Preferences\ThumbUISlideShow::transition` kulcsban (`0x00760ca5`). Nálunk:
  QSettings sztring-kulcs (`view/slideshowTransition`). Teendő: nincs
  kötelező változtatás. Ha a jegy a tárolási formát is kéri, azt a
  `controller.py` döntése dönti el.
- **`transtype` láthatóság.** Eredeti: a timeline és a transtype kölcsönösen
  kizárja egymást (`0x008037e0`). Nálunk: a választó mindig látszik. Teendő:
  N8 nélkül nincs kódjavaslat.

### 1.5 Nyitott kérdések mérlege

Nyitott kérdések: 8 nyílt · 8 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”.

**Lezárva (8):**

- L1: a 22 belső kulcs és sorrendjük (`0x00771a10`).
- L2: a választó 7 eleme és a QML egyezése (`0xd342e8`, `SlideshowView.qml:101-107`).
- L3: a felugró lista 7 elemű (`0x0075db71`).
- L4: a „22 soros” megjegyzés téves (`SlideshowView.qml:1030`).
- L5: az írt érték és helye (`0x00760ca5`, DWORD 0-6).
- L6: az `exit` ága és első hívása (`0x00803527`, `0x00a6ccf0`).
- L7: az `auto` és az `auto2` ugyanazt a függvényt hívja (`0x00803486`, `0x008034c5`).
- L8: az `exit` felirat egyezik (`oneuptext.tre:7-8`).

**Nyílt, mindegyiknek megvan az útja (8):**

- N1: az `exit` `X` objektumának osztálya és a `vt+0x14` metódusa. Út: a
  `this+0x50` beállítójának (`0x00a6cd00`, `vt+0x28`) közvetett hívóhelyének
  megkeresése, és az `X` vtáblájának azonosítása. Örökölt.
- N2: az `auto2` és az `auto` láthatósága egymás helyett. Út: a motor
  láthatósági szabálya, vagy az eredeti Picasa két állapotú felvétele a
  Colab-felmérővel (`picasa-colab-jobs`, `picasapy-research` 1/d). Örökölt.
- N3: az `auto2` geometriája a `respack.yt`-ből. Út: a fájl beszerzése a
  munkafába, majd `tools/picasa/respack.py list`. Új.
- N4: a registry-előtag. Út: a `0x00407a20` `vt+4` metódusa az
  `[ebx+0x18]` objektumon. Új.
- N5: az API-név a `0xd694f0`-n. Út: a PE import-tábla közvetlen olvasása
  a `pe_dis`-szel. Új.
- N6: a `0x00760d19` második írásának kulcsa és értéke. Út: a `0x00760b00`
  objektumának azonosítása. Új.
- N7: az `exit` ikon grafikája. Út: az erőforrás-azonosító megkeresése a
  `respack.yt`-ben. Új.
- N8: a `vt+0x68` és `vt+0x6c` jelentése. Út: a két függvény törzse és
  a `timeline` osztályának azonosítása. Örökölt
  (`picasa-create-features.md:6890`).

**Megjegyzés a számláláshoz.** Az N3-N7 új részkérdések, a skill szerint
gépi úton zárhatók volnának ebben a körben. Ezért a kör a skill szerinti
lezárási feltételt nem teljesíti. A nyitott tételek a hívóhoz kerülnek, aki
dönt, folytatódik-e a kör.

### 1.6 Bizonyítottsági fok

- **Megerősített:** L1-L8 (közvetlen bináris vagy `.tre` bizonyíték).
- **Feltételes:** a `0x00401900` DWORD-író (a hat argumentumos hívás alakja
  alapján). A `0x00760b00` kulcsa (a `0x00407a20` szekció-érték párja),
  amíg a teljes registry-út nincs meg (N4).
- **NINCS MEG:** N1-N8.
- **Független újralevezetés:** nem futott. A `picasapy-research` skill
  szerint lelet-jegy előtt kellene. Jegyet ebben a körben nem nyitottunk.

### 1.7 Amit kizártunk

- A `transtype` nincs a `0x008032e0` kattintás-diszpécserben. A
  `0xcbd54c` név konstans csak a `0x008037e0`-ban szerepel (sztring-index).
- A `0x00803110` törzse önmagában nem invertál: `[esi+0x518] = 1`
  feltétel nélkül. Ezért az `auto` és a QML `togglePause()` egyezése nem
  igazolt (N2 része).
- A 22-es lista nem a felugró lista: a felugró lista 7 elemű (L3).

### 1.8 Reprodukció

```sh
cd ~/picasapy-agent && venv/bin/python -c "import sys; sys.path.insert(0,'eszkozok'); from pe_dis import cdis; print(cdis(0x008032e0, 1400))"
cd ~/picasapy-agent && venv/bin/python eszkozok/atlasz_keres.py 0x008032e0 0x008037e0 0x00803110 0x00760b00 0x0075d810 0x00771a10
```

A `string_xrefs` és a `functions` lekérdezés a `referencia/binary-index/picasa3-index.sqlite`
ellen, `mode=ro` kapcsolattal készült. A kódhoz nem nyúltunk, ezért a
kötelező CI-őrök nem futottak.

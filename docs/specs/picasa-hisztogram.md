# A Picasa hisztogramja — teljes visszafejtés

**Pixelpontos specifikáció.** A hisztogram képét a Picasa egy **256 × 70**-es
bittérképre rajzolja, majd azt feszíti a képernyőn látható **213 × 59**-es
dobozba. A normalizálás **nem a csúcshoz**, hanem az **átlaghoz** történik, a
három csatorna pedig **összeadódva** keveredik.

Ez a lap a `#236` / `histogram-reference.md` kiegészítése: az ott leírt
mérőkészlet a *mi* oldalunkat ellenőrzi, ez a lap az **eredeti algoritmust**
rögzíti.

## 1. Hol van a hisztogram a felületen

Nem önálló panel: a **`nerdview`** („Histogram & Camera Information")
tartalmazza.

| elem | pozíció | méret |
|---|---|---|
| `nerdview/docbounds` | (0, 0) | **238 × 144** |
| `nerdview/nvhead` — „Histogram & Camera Information" | (13, 4) | 100 × 11 |
| `nerdview/histoback` (a doboz háttere) | (**13**, **25**) | **213 × 59** |
| **`nerdview/histo`** — a `histogram(editpanel/previewimage)` csomópont | (**13**, **25**) | **213 × 59** |
| `nerdview/detail1` (bal szöveg-oszlop) | (13, 82) | 138 × 41 |
| `nerdview/detail2` (jobb szöveg-oszlop) | (157, 82) | 69 × 41 |
| ~~`nerdview/floater`~~ · ~~`nerdview/close`~~ | | **kikommentezve** |

Elhelyezés (`editpanel.tre:1026`):

```
editpanel/nerdview_container: root
XConstraint 0, 0, LEFTDRAWEROFFSET, 20
YConstraint 1, 1, -95
```

— a **bal fiók BAL széléhez +20**, és a képernyő aljához **−95**. A
`LEFTDRAWEROFFSET` a fiók be-/kicsúsztatását vezérlő **változó**, nem a
fiók szélessége (ld. 7.1) — a panel tehát a fiókON BELÜL dokkolt.

A `nerdview/histo` a `histoback`-en **középre** ül (`m_centerXY`).

> A hisztogram forrása a `histogram(**editpanel/previewimage**)` argumentum:
> a **megjelenített előnézeti kép**, nem a forrásfájl. Ez egyezik a mi
> megoldásunkkal.

A `#editpanel/histogram` kapcsológomb (37 × 22, a szerkesztő jobb alsó
sarkában) **ki van kommentezva** — a `nerdview` máshonnan jelenik meg.

## 2. Az osztályok

| RTTI | szerep |
|---|---|
| `ytHistoCreator::vftable` (`0x008806f0`) | a `histogram` csomópont-típus gyára; a típusnév-getter a `0x0040aa50` (`"histogram"`) |
| `ytHistoNode::vftable` (`0x008da844`) | maga a csomópont |
| `HistogramHandler::vftable` (`0x00894a14`) | a kattintás-kezelő (`0x005c45e0`) |

A csomópont üzenetkezelője: **`0x009db160`** (652 bájt), a `0x13`-as
üzenetre fut le, és onnan hívja az építőt.

## 3. A hisztogram FELVÉTELE — `0x00a4b960` (718 bájt)

### 3.1 A pufferek

Az objektumban három, egyenként **256 × `int32`** puffer:

| eltolás | csatorna |
|---|---|
| `+0x018` | **R** |
| `+0x418` | **G** |
| `+0x818` | **B** |

### 3.2 A számláló ciklus

```asm
0x00a4b9b2  movzx ecx, byte ptr [eax + 2]       ; R  (a képpont 3. bájtja)
0x00a4b9b6  add   dword ptr [esi + ecx*4 + 0x18],  1
0x00a4b9bf  movzx ecx, byte ptr [eax + 1]       ; G
0x00a4b9c3  add   dword ptr [esi + ecx*4 + 0x418], 1
0x00a4b9d2  movzx ecx, byte ptr [eax]           ; B
0x00a4b9d5  add   dword ptr [esi + ecx*4 + 0x818], 1
0x00a4b9e4  mov   ecx, dword ptr [esi]          ; ← a LÉPÉSKÖZ
0x00a4b9e8  lea   eax, [eax + ecx*4]            ; ugrás `ecx` képponttal
```

**A képpont bájtsorrendje `B, G, R, A`** (a `+2` a vörös).

> ⚠️ **Ritkítás:** az objektum **0. mezője a lépésköz**, és a ciklus
> **vízszintesen ÉS függőlegesen is** ezzel lép (`add ebx, [esi]` a
> sorváltásnál, `0x00a4b9f2`). Ha a lépésköz ≤ 1, egy külön, teljes
> bejárású ciklus fut (`0x00a4b9fb`–`0x00a4ba65`).

### 3.3 A referencia-összeg

A felvétel után **mind a 256 binen** végigmegy (`mov edi, 0x40` = 64
iteráció, **négyszeresen kigöngyölítve** → 256):

```asm
0x00a4ba88  ; csatornánkénti MINIMUM-követés  →  +0xc18 (R), +0xc1c (G), +0xc20 (B)
0x00a4bac6  mov edx, [eax + 0x400]     ; B bin
0x00a4bacc  add edx, [eax]             ; + G bin
0x00a4bace  add edx, [eax - 0x400]     ; + R bin
0x00a4bad4  add dword ptr [esi + 0xc24], edx   ; ← ÖSSZEG
```

A nulla-hármasokat (`R=G=B=0` az adott binen) **kihagyja**.

Végül:

```asm
0x00a4bc27  shr dword ptr [esi + 0xc24], 7      ; ÖSSZEG / 128
```

**`+0xc24` = (Σ minden bin, mindhárom csatorna) / 128.**

Ha `N` a mintavett képpontok száma, akkor `Σ = 3·N`, tehát
**`+0xc24 = 3N/128`**.

## 4. A RAJZOLÁS — `0x00a4bc40` (511 bájt)

### 4.1 A bittérkép: 256 × 70

```asm
0x00a4bc68  mov edx, 0x46        ; 70  ← MAGASSÁG
0x00a4bc6d  mov ecx, 0x100       ; 256 ← SZÉLESSÉG (egy oszlop = egy bin)
0x00a4bc72  call 0x9a9c90        ; a célbittérkép létrehozása
```

### 4.2 A skála — az ÁTLAGHOZ normalizál

```asm
0x00a4bc77  fild  dword ptr [ebx + 0xc24]     ; 3N/128
0x00a4bc8d  fdivr qword ptr [0xcf4bf8]        ; 70.0 / (3N/128)
```

```
skála = 70 / (3N/128) = 8960 / (3N) ≈ 2986,67 / N
```

**Ez a lap legfontosabb állítása.** A normalizálás **nem** a csatorna
csúcsához történik, hanem a **globális átlaghoz**:

| eset | oszlopmagasság |
|---|---|
| egy **átlagos** bin (`N/256` képpont) | `(N/256) · 8960/(3N)` = **11,67 px** a 70-ből |
| a **hatszoros** átlag | **70 px** — a doboz teteje |
| ennél magasabb | **levágva 70-nél** |

### 4.3 A klippelés

```asm
0x00a4bd3e  cmp eax, 0x46 / 0x00a4bd4d  mov esi, 0x46     ; R  → max 70
0x00a4bd52  cmp ecx, 0x46 / 0x00a4bd57  mov ecx, 0x46     ; G  → max 70
0x00a4bd60  cmp edx, 0x46 / 0x00a4bd65  mov ebx, 0x46     ; B  → max 70
```

Csatornánként külön, **70**-nél.

### 4.4 A kirajzoló ciklus — ÖSSZEADÓ keverés

```asm
0x00a4bd92  ecx = [edi+0xc]                 ; a bittérkép magassága (70)
0x00a4bd98  ecx = ecx - y - 1               ; ALULRÓL felfelé
0x00a4bd9d  imul ecx, [edi+4]               ; × sorlépés
0x00a4bda1  add  ecx, bin                   ; + az oszlop
0x00a4bda5  lea  ecx, [ebx + ecx*4]         ; a képpont címe

0x00a4bdaa  add dword ptr [ecx], 0x55550000   ; ha y < R_px
0x00a4bdb6  add dword ptr [ecx], 0x55005500   ; ha y < G_px
0x00a4bdc2  add dword ptr [ecx], 0x55000055   ; ha y < B_px
```

A ciklus `max(R_px, G_px, B_px)`-ig megy.

**Minden csatorna `0x55` = 85 értéket ad hozzá a saját színkomponenséhez
ÉS ugyanennyit az alfához.** A puffer nulláról indul.

### 4.5 Ami ebből a képernyőn látszik

| hány csatorna fedi | ARGB az összeadás után | szorzott alfát feloldva |
|---|---|---|
| **1** (pl. csak R) | `A=85, R=85, G=0, B=0` | **telített vörös, 33 % átlátszatlanság** |
| **2** (pl. R+G) | `A=170, R=85, G=85, B=0` | **fél fényerejű sárga, 67 %** |
| **3** (R+G+B) | `A=255, R=85, G=85, B=85` | **átlátszatlan sötétszürke `#555555`** |

> **A Picasa hisztogramjának jellegzetes megjelenése ebből jön:** ahol
> mindhárom csatorna fed, ott **átlátszatlan sötétszürke** (`#555555`)
> van — nem fehér és nem világosszürke. Ahol egy csatorna dominál, ott
> telített szín, harmadnyi átlátszatlansággal.

### 4.6 A méretre feszítés

A 256 × 70-es bittérkép a **213 × 59**-es dobozba kerül — vagyis
**vízszintesen 0,832×, függőlegesen 0,843×** kicsinyítve. Egy bin tehát
**nem** egy képernyő-oszlop: 256 bin → 213 oszlop.

## 5. Összevetés a PicasaPy-jal

| | eredeti Picasa | PicasaPy | állapot |
|---|---|---|---|
| **normalizálás** | **átlaghoz**: `70/(3N/128)`, klip 70-nél | `histogram_helper.py`: közös `128/(3N)` skála, 1,0-nál klip | ✅ egyezik |
| **keverés** | **összeadó**, `+85` szín és `+85` alfa | `HistogramBitmap.qml`: a +85-ös szorzott-alfa végeredménye | ✅ egyezik |
| **rajzfelbontás** | **256 × 70** bittérkép, utána feszítve | 256 × 70-es belső komponens, utána méretezve | ✅ egyezik |
| **doboz mérete** | **213 × 59** | **213 × 59** | ✅ egyezik |
| **forrás** | a megjelenített **előnézet** | ugyanaz | ✅ egyezik |
| **binek** | 256 | 256 | ✅ egyezik |
| **bájtsorrend** | B, G, R, A | RGB | ✅ egyenértékű |
| **ritkítás** | lépésköz **vízszintesen és függőlegesen** | `stride`-mintavétel 500 000 képpont fölött | hasonló elv, más küszöb |
| **alulról felfelé** | igen | igen (`y: plot.height - height`) | ✅ egyezik |

### Megvalósítási állapot (#864)

A korábbi csúcsnormalizálás és 0,55-ös source-over keverés megszűnt. A
Python-réteg a ténylegesen mintavett `N` alapján adja át a 70 px-re
normalizált magasságot; a QML-réteg a három magasságot legfeljebb három,
egymást nem fedő szakaszra bontja, és közvetlenül a +85-ös RGBA-összeg
végeredményét rajzolja. A teljes 256 × 70-es belső kép képpontos tesztet kap.

*Bizonyítottsági fok: megerősített* — a felvevő ciklus, a
referencia-összeg, a skála-képlet mindkét konstansa (70,0 és a `>>7`), a
klippelés és a három összeadó konstans (`0x55550000`, `0x55005500`,
`0x55000055`) mind nyers utasításszinten kiolvasva; a felületi geometria a
`respack.yt` rectjeiből.

**Ritkítás:** az objektum 0. mezője hívónkénti lépésköz-paraméter; a
`0x00a4b650` burkoló bizonyítottan 1-et ír bele (nincs ritkítás). Más hívók
más értéket adhatnak, de a referenciaösszeg ugyanabból a mintából készül,
mint a binek, ezért a normalizált görbe alakja önkonzisztens. A PicasaPy
500 000 képpont fölötti stride-mintavétele ezt a tulajdonságot megtartja.

## 6. A hisztogram alatti EXIF-blokk — bitre pontosan

A `nerdview` panel alsó része **két, fix szélességű szövegoszlop**.

### 6.1 Geometria (`respack.yt`)

*Forrás: `nerdviewdetail_mac.tre:1` (`nerdview/detail1`) · `nerdviewdetail_mac.tre:4` (`nerdview/detail2`).*

| elem | pozíció | méret |
|---|---|---|
| **`nerdview/detail1`** (bal) | (**13**, **82**) | **138 × 41** |
| **`nerdview/detail2`** (jobb) | (**157**, **82**) | **69 × 41** |

Ebből következik:

- a két oszlop közti **hézag: 6 px** (157 − 13 − 138);
- a teljes szélesség **138 + 6 + 69 = 213** — **pontosan a hisztogram szélessége**;
- a jobb oszlop **pontosan feleakkora**, mint a bal (69 vs 138);
- mindkettő **41 px magas**, `y = 82`-től;
- a hisztogram alja `25 + 59 = 84`, tehát a szövegblokk **2 képponttal
  feljebb kezdődik** — enyhén rálóg.
### 6.2 Tipográfia

| platform | erőforrás | betű |
|---|---|---|
| **Windows** | `nerdviewdetail_win.tre` | **nincs betű-makró** → a rendszer alapértelmezett betűje |
| **Mac** | `nerdviewdetail_mac.tre` | `m_displayfont11` = **Praxis Semi Bold/Heavy, 11 pt, súly 400, betűköz −1** |

A panel fejléce (`nerdview/nvhead`, „Histogram & Camera Information",
13, 4, 100 × 11) **`m_displayfont14`** — ugyanaz a család, **14 pt**.

### 6.3 A HÉT formátum-erőforrás — `il_NerdView::1..7`

A blokk pontosan hét erőforrásból épül. *(A `0x00567e10` másoló függvény
ugyanennyi, **hét** sztringmezőt mozgat — `+0x0c`-től `+0x24`-ig.)*

| # | EN | **HU** | hova |
|---:|---|---|---|
| 1 | `No EXIF data available.` | **`Nincs elérhető EXIF-adat.`** | üres állapot |
| 2 | `%1$s\nFocal Length: %2$3.1fmm\n` | **`%1$s\nFókusztávolság: %2$3.1f mm\n`** | **bal** |
| 3 | `(35mm equivalent: %3.0fmm)\n` | **`(35 milliméteressel egyenértékű: %3.0f mm)\n`** | **bal** |
| 4 | `1/%ds\n` | **`1/%d s\n`** | **jobb** |
| 5 | `%2.1fs\n` | **`%2.1f s\n`** | **jobb** |
| 6 | `f/%3.1f\n` | **`f/%3.1f\n`** | **jobb** |
| 7 | `ISO: %2d` | **`ISO: %2d`** | **jobb** |

### 6.4 Amit a formátumok pontosan előírnak

| mező | formátum | jelentése |
|---|---|---|
| fényképezőgép | `%1$s` | nyers szöveg, **a fókusztávolsággal EGY erőforrásban**, `\n`-nel elválasztva |
| fókusztávolság | **`%3.1f`** | **egy tizedesjegy**, minimum 3 karakter szélesség |
| 35 mm-egyenérték | **`%3.0f`** | **nulla tizedesjegy** |
| exponálás < 1 s | **`1/%d s`** | egész nevező |
| exponálás ≥ 1 s | **`%2.1f s`** | egy tizedesjegy |
| rekesz | **`f/%3.1f`** | **egy tizedesjegy** |
| ISO | **`ISO: %2d`** | egész, minimum 2 karakter, **`\n` NÉLKÜL** (ez az utolsó sor) |

> ⚠️ **A magyar változatban SZÓKÖZ van a mértékegység előtt**, az angolban
> nincs: `%2$3.1f mm` ↔ `%2$3.1fmm`, `1/%d s` ↔ `1/%ds`,
> `%2.1f s` ↔ `%2.1fs`. Ezt **szó szerint** kell átvenni.

> ⚠️ **Nincs vaku-sor.** A hét erőforrás között nem szerepel.

### 6.5 A blokk felépítése

```
detail1 (bal, 138 px):          detail2 (jobb, 69 px):
  <fényképezőgép neve>            1/125 s      ← #4 vagy #5
  Fókusztávolság: 6,7 mm          f/1.7        ← #6
  (35 milliméteressel             ISO: 3200    ← #7
   egyenértékű: 24 mm)
```

EXIF nélküli fájlnál a blokk helyén: **„Nincs elérhető EXIF-adat."**

### 6.6 ❌ Amiben a PicasaPy eltér

`src/picasapy/app/formatting.py:311` (`camera_summary_text`):

| | eredeti Picasa | PicasaPy | eltérés |
|---|---|---|---|
| fókusztávolság | **`%3.1f`** (1 tizedes) | `toString(v, "g", 4)` — **4 értékes jegy** | ⚠️ `6.7` vs `6,700` |
| rekesz | **`f/%3.1f`** (1 tizedes) | `toString(v, "g", 3)` — 3 értékes jegy | ⚠️ `f/1.7` vs `f/1.70` |
| 35 mm-egyenérték szövege | **„(35 milliméteressel egyenértékű: %3.0f mm)"** | „(35 mm-egyenérték: %1 mm)" | ⚠️ **más fordítás** |
| exponálás | `1/%d s` vagy `%2.1f s` | `format_exposure(...)` | ellenőrizendő |
| **vaku-sor** | **NINCS** | `Flash: Fired` / `Flash: Off` | ⚠️ **fölösleges sor** |
| ISO | `ISO: %2d` | `ISO: %1` | a szélesség hiányzik |
| üres állapot | **„Nincs elérhető EXIF-adat."** | üres sztring | ⚠️ hiányzó felirat |
| oszlopszélesség | **138 / 69**, 6 px hézaggal | rugalmas | ⚠️ fix legyen |
| oszlopmagasság | **41 px** mindkettő | rugalmas | ⚠️ fix legyen |

> A Picasa **másik** helyen (`il_PrintExif::3`, a nyomtatási EXIF-blokk)
> **harmadik** fordítást használ ugyanerre: „(35 mm-es ekvivalens:
> %3.0f mm)". A hisztogram alá a **`il_NerdView::3`** való.

*Bizonyítottsági fok: megerősített* — a geometria a `respack.yt` rectjeiből,
a betű a két `nerdviewdetail_*.tre`-ből, a hét formátum a hivatalos magyar
szövegforrásból, és a hét sztringmező a `0x00567e10` másolójából.

## 7. A panel elhelyezése és megjelenítése

### 7.1 A horgonyzás

```
editpanel/nerdview_container: root
XConstraint 0, 0, LEFTDRAWEROFFSET, 20
YConstraint 1, 1, -95

editpanel/nerdview: editpanel/nerdview_container
m_scaleXY
#m_hidden                          ← KIKOMMENTEZVE
```

| megkötés | jelentése |
|---|---|
| `XConstraint 0, 0, LEFTDRAWEROFFSET, 20` | a bal széle a **`root` bal széléhez**, `LEFTDRAWEROFFSET` **+20 px** |
| `YConstraint 1, 1, -95` | az alsó széle a **képernyő aljához**, **−95 px** |
| `m_scaleXY` | a panel a tartójával együtt nyúlik |

**A `LEFTDRAWEROFFSET` nem a fiók szélessége, hanem a fiók
be-/kicsúsztatását vezérlő változó** — ezt három sor mondja ki, egymást
erősítve:

| sor | tartalom | mit mond ki |
|---|---|---|
| `editpanel.tre:1413` | `Handler varbutton LEFTDRAWEROFFSET 0 -279 1 editpanel/previewimage` | a fiók-összecsukó gomb a változót **0 ↔ −279** között billegteti — tehát **eltolás** |
| `editpanel.tre:1421` | `editpanel/insetleft: root` + `XConstraint 0, 0, LEFTDRAWEROFFSET, 279` | a **képterület** `LEFTDRAWEROFFSET + 279`-nél kezdődik → a fiók sávja `[+0, +279]` |
| `editpanel.tre:1233` | `editpanel/editcontrols` … `YConstraint 1, 1, -270` | a fiók vezérlői **270 px-rel az alsó él fölött** végződnek — épp helyet hagyva a 95 + 144 = **239 px**-es panelnek |

A panel bal éle így `LEFTDRAWEROFFSET + 20`, jobb éle `+258` — **a fiók
279 px-es sávján belül**. A panel tehát **a bal fiók alján, a fiókON BELÜL
dokkolt**, és a fiókkal együtt csúszik ki a képernyőről, ha a felhasználó
összecsukja azt. Mérete **238 × 144**.

> **Helyesbítés (#1323).** Ez a szakasz korábban azt írta, hogy a panel „a
> bal fiók jobb pereméhez +20", vagyis a **képterület fölött lebeg**. A #864
> megvalósítása ezt vette át, és a panel a fotó bal alsó sarkára került. A
> fenti három `.tre` sor ezt cáfolja: a `LEFTDRAWEROFFSET` eltolás-változó,
> a panel a fiókon belül dokkolt. A `histogram-reference.md` is ezt erősíti:
> a lebegő korszak sorai (`#nerdview/floater`, `#nerdview/close`) ki vannak
> kommentezve, a 3.9-ben már dokkolt a panel.

> Az elvetett változat (`#editpanel/nerdview_container: editpanel/editbase`,
> `YConstraint 0, 0, 400`) a **szerkesztőterületen belül**, fentről 400
> képpontra tette volna.

### 7.2 A megjelenítés — két kapcsoló, mindkettő rejtve

*Forrás: `thumbui.tre:91` (`thumbui/histogram`).*

| kapcsoló | hol | méret | állapot |
|---|---|---|---|
| **`thumbui/histogram`** | `root`, (375, 316) | **14 × 14** | **`m_hidden`** |
| ~~`editpanel/histogram`~~ | `editpanel/editbase`, (756, 449) | 37 × 22 | **teljesen kikommentezve** |

Mindkettő ugyanazt csinálná:

```
Property showtarget editpanel/nerdview
```

A `#editpanel/histogram` buboréksúgója (szintén kikommentezve):

```
#Tooltip editpanel/histogram
#Show/Hide Histogram & Camera Information
```

**Vagyis a kiadott Picasában nincs látható hisztogram-gomb.** A
`thumbui/histogram` egy **rejtett, 14 × 14-es kattintható terület**, amit a
program programozottan jelenít meg — a panel maga viszont **nincs
alapból elrejtve** (`#m_hidden` a `nerdview`-n ki van kommentezva).

### 7.3 A fejléc szövege

`editpaneltext.tre`:

```
Text nerdview/nvhead
Histogram & Camera Information
```

**Nincs lefordítva** — ahogy a `detail1`/`detail2` formátumai közül is csak
az `il_NerdView::*` család van magyarul (azok viszont hivatalos
fordítással).

> Javasolt magyar: **„Hisztogram és fényképezőgép-adatok"**.

*Bizonyítottsági fok: megerősített* (az `editpanel.tre` 1018–1033. sora, a
`thumbui.tre` 91–93. sora és az `editpaneltext.tre` 35–39. sora).

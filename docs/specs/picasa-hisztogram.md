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

— a **bal fiók jobb széléhez +20**, és a képernyő aljához **−95**.

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

| | eredeti Picasa | PicasaPy | eltérés hatása |
|---|---|---|---|
| **normalizálás** | **átlaghoz**: `70/(3N/128)`, klip 70-nél | **csatornánként a saját csúcsához** (`hist/peak`, `histogram_helper.py:61`) | ⚠️ **alapvető** — nálunk minden csatorna kitölti a dobozt, az eredetiben csak a hatszoros átlag fölött |
| **keverés** | **összeadó**, `+85` szín és `+85` alfa | `opacity: 0.55`, normál source-over (`HistogramBox.qml:130`) | ⚠️ **alapvető** — az eredetiben a hármas fedés `#555555` átlátszatlan |
| **rajzfelbontás** | **256 × 70** bittérkép, utána feszítve | közvetlenül a doboz szélességén, vödrönként egy `Rectangle` | ⚠️ más a lépcsőzés |
| **doboz mérete** | **213 × 59** | a panel szerint változó | igazítandó |
| **forrás** | a megjelenített **előnézet** | ugyanaz | ✅ egyezik |
| **binek** | 256 | 256 | ✅ egyezik |
| **bájtsorrend** | B, G, R, A | RGB | ✅ egyenértékű |
| **ritkítás** | lépésköz **vízszintesen és függőlegesen** | `stride`-mintavétel 500 000 képpont fölött | hasonló elv, más küszöb |
| **alulról felfelé** | igen | igen (`y: plot.height - height`) | ✅ egyezik |

### Miért néz ki teljesen másképp

A két eltérés **egymást erősíti**:

1. **A csúcshoz normalizálás** minden csatornát felnagyít a doboz
   magasságára. Egy tipikus fotón a legmagasabb bin sokszorosa az
   átlagnak, így a mi görbénk **laposabbnak és zajosabbnak** látszik, míg
   az eredeti **a doboz alsó harmadában** marad, és csak a valódi
   csúcsok érik el a tetejét.
2. **A source-over keverés** 0,55-ös átlátszatlansággal **világosít**, az
   összeadó keverés **sötétít és telít**. Ahol mindhárom csatorna fed, mi
   egy világos, mosott színt kapunk, az eredeti **`#555555`** sötétszürkét.

*Bizonyítottsági fok: megerősített* — a felvevő ciklus, a
referencia-összeg, a skála-képlet mindkét konstansa (70,0 és a `>>7`), a
klippelés és a három összeadó konstans (`0x55550000`, `0x55005500`,
`0x55000055`) mind nyers utasításszinten kiolvasva; a felületi geometria a
`respack.yt` rectjeiből.

**Nyitva marad:** a ritkítás **lépésközének** kiszámítása (az objektum
0. mezője) — hol és milyen képlettel áll elő. A hisztogram *alakját* nem
befolyásolja érdemben, a *pontos* bin-értékeket igen.

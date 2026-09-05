# A Mappakezelő (Folder Manager) TELJES specifikációja (2026-08-20)

Ez a lap az eredeti Picasa 3.9.141.259 **Mappakezelő** ablakát írja le
teljesen: elrendezés, átméretezés, a fa, a három állapot, az
arcfelismerés-kapcsoló, a figyelmeztetések, az OK/Mégse szemantikája és a
Súgó. A cél, hogy egy fejlesztő az eredeti program nélkül is pontosan
újraépíthesse.

**Források**

| forrás | mit ad |
|---|---|
| `runtime/respack.yt` → `tre:foldermgr`, `tre:foldermgr_text` | az elrendezés-forrás és a feliratok |
| ugyanaz → `layer:foldermgr/*` 30 rétege | a tervezővászon-geometria és az ikonok |
| `Picasa3.exe` (SHA-256 `644b7bec…`) | a viselkedés: `0x007c0810`, `0x007c27d0`, `0x007c60d0`, `0x007c64a0`, `0x007c5ef0`, `0x007c4df0`, `0x007c6430` |
| `referencia/stringres-en-hu.tsv` | a magyar feliratok |
| **`picasapy-agent` → `referencia/mappakezelo/`** | **a tulajdonos két képernyőképe futó Picasából** (alap 581×518, kézzel nagyított 760×784) |

> ⚠️ A képernyőképek a **privát** repóban vannak
> (`referencia/mappakezelo/mappakezelo-alap.png` és
> `…/mappakezelo-nagyitott.png`). Ha egy állítás ellentmond nekik, **a kép
> az igazság** — az alábbi leírás minden pontja egyezik velük.

---

## 1. Az elrendezés-forrás és a tervezővászon

A dialógus **nem `.fen`**, hanem a yt-keretrendszer respack-ablaka: a
`runtime/` alatt nincs `foldermgr.fen`, viszont van `tre:foldermgr`.

### 1.1 A csomópontfa (`tre:foldermgr`, szó szerint)

```
root
├── foldermgr/base            m_offsetB · m_scaleX
│   ├── left_side             X: 0,0,+4  …  1,.5,0     ← PONTOSAN 50 %
│   │   │                     Y: 0,0,+4  …  1,1,0
│   │   ├── folder_list_label m_offsetLT · font14
│   │   └── foldertree        X: 0,0,+10 … 1,1,0 · Y: 0,0,+20 … 1,1,−60
│   ├── right_side            X: 0,.5,0 … 1,1,−4 · Y: 0,0,+4 … 1,1,0
│   │   ├── instructions_text m_offsetLT · font14
│   │   ├── status_decrect    m_offsetLT   (decrect softbevel/flatbevel)
│   │   │   ├── status_label  m_offsetLT · font14
│   │   │   ├── status_group  m_offsetLT   (buttcontainer)
│   │   │   │   ├── scan_once + scan_once_label   ← Property setpressed 1
│   │   │   │   ├── remove    + remove_label
│   │   │   │   ├── watch     + watch_label
│   │   │   │   └── icon_once / icon_exclude / icon_always
│   │   │   ├── line          m_offsetT · m_scaleX    ← elválasztó vonal
│   │   │   └── frexclude + frexclude_label
│   │   │       ├── nofr_on   m_offsetL · m_centerY
│   │   │       └── nofr_off  m_offsetL · m_centerY · m_hidden
│   │   ├── watched_label     m_offsetLT · font14
│   │   └── watched_folders   m_offsetLT · X: 1,1,−10 · Y: 1,1,−60
│   └── size                  m_offsetRB · Property winsize 1
├── ok      m_offsetRB
├── cancel  m_offsetRB
└── help    m_offsetRB
```

A három rádiógomb és a `frexclude` `m_hit_childlabel`-t visel: **a
feliratra kattintva is elsülnek**.

A `frexclude` deklaratív kötése: `Property hidetarget foldermgr/nofr_on` és
`Property showtarget foldermgr/nofr_off` — a kapcsoló elsülésekor a
keretrendszer **magától** cseréli a két ikont, kód nélkül.

### 1.2 A tervezővászon mért téglalapjai (respack, 13 bájtos fejléc)

| elem | x0 | y0 | x1 | y1 | méret |
|---|---:|---:|---:|---:|---|
| **`docbounds` / `rect: base`** | 0 | 0 | **550** | **450** | **550×450 — a KIINDULÓ ablakméret** |
| `clip: left_side` | 10 | 10 | 285 | 396 | 275×386 |
| `clip: right_side` | 285 | 10 | 545 | 396 | 260×386 |
| `folder_list_label` | 18 | 10 | 236 | 24 | 218×14 |
| `listbox: foldertree` | 10 | 35 | 285 | 396 | 275×361 |
| `text(instructions_text)` | 302 | 10 | 534 | 83 | 232×73 |
| `decrect: status_decrect` | 303 | 97 | 534 | 269 | **231×172** |
| `static: status_label` | 309 | 103 | 527 | 117 | 218×14 |
| `buttcontainer: status_group` | 310 | 125 | 527 | 222 | 217×97 |
| `buttcon: scan_once` | 310 | **130** | 334 | 154 | 24×24 |
| `icon_once` | 340 | 133 | 358 | 147 | 18×14 |
| `static: scan_once_label` | 363 | 133 | 581 | 147 | 218×14 |
| `buttcon: remove` | 310 | **163** | 334 | 187 | 24×24 |
| `icon_exclude` | 341 | 165 | 357 | 182 | 16×17 |
| `static: remove_label` | 363 | 166 | 581 | 180 | 218×14 |
| `buttcon: watch` | 310 | **196** | 334 | 220 | 24×24 |
| `icon_always` | 340 | 197 | 357 | 215 | 17×18 |
| `static: watch_label` | 363 | 199 | 581 | 213 | 218×14 |
| `line` | 306 | 226 | 311 | 229 | 5×3 (vízszintesen nyúlik) |
| `superbutton: frexclude` | 310 | 235 | 340 | 261 | 30×26 |
| `nofr_on` | 315 | 239 | 335 | 258 | 20×19 |
| `nofr_off` | 315 | 239 | 339 | 258 | 24×19 |
| `static: frexclude_label` | 349 | 240 | 567 | 254 | 218×14 |
| `static: watched_label` | 302 | 284 | 520 | 298 | 218×14 |
| `listbox: watched_folders` | 302 | 309 | 537 | 397 | 235×88 |
| `superbutton: ok` | **230** | 410 | 328 | 438 | 98×28 |
| `superbutton: cancel` | **335** | 410 | 433 | 438 | 98×28 |
| `superbutton: help` | **440** | 410 | 538 | 438 | 98×28 |
| `size` | 530 | 434 | 550 | 454 | 20×20 (a vászon alján túlnyúlik) |

**A rádiógombok függőleges osztása 33 képpont** (130 → 163 → 196), a gomb
24×24, és a felirat a gomb jobb szélétől **+29** képponttal kezdődik
(310+24 = 334 → 363).

> ⚠️ A vászonrajz a `left_side` jobb szélét 285-nél (51,8 %) mutatja, de
> **futásidőben az `XConstraint 1, .5, 0` érvényes: pontosan 50 %.** A
> `picasa-respack-format.md` figyelmeztetése (a vászon-koordináták és a
> `.tre` ütközése) itt élesben is számít. A tulajdonos két képernyőképe a
> **50 %-ot** igazolja (kis ablak: ~564 képpont belméret, osztás 290-nél;
> nagy ablak: ~721 képpont, osztás ~385-nél).

### 1.3 A feliratok (`tre:foldermgr_text` + `stringres`)

| elem | angol | magyar (a képernyőképről is) |
|---|---|---|
| `folder_list_label` | Folder List | **Mappalista** |
| `foldermgr/instructions_text` | For each folder, you can choose whether or not to have Picasa find pictures inside it.  You can also pick folders to watch for new pictures. | Minden mappa esetében megadhatja, hogy a Picasa keressen-e bennük képeket. Kijelölhet egyes mappákat is, és beállíthatja, hogy a program figyelje bennük az új képek megjelenését. |
| `status_label` | For the current folder: | **Az aktuális mappa esetében:** |
| `scan_once_label` | Scan Once | **Keresés egyszer** |
| `remove_label` | Remove from Picasa | **Eltávolítás a Picasából** |
| `watch_label` | Scan Always | **Keresés mindig** |
| `frexclude_label` | Face Detection **On** / **Off** (`CFolderMgrDialog::hasfr` / `::nofr`) | **Arcfelismerés bekapcsolva / kikapcsolva** |
| `watched_label` | Watched Folders | **Figyelt mappák** |
| `ok` / `cancel` / `help` | OK / Cancel / Help | **OK / Mégse / Súgó** |
| ablakcím | `foldermgr::title` (`0x005ce590`) | **Mappakezelő** |

*(Az angol szövegben az „inside it." után **két szóköz** van — a
`foldermgr_text.tre` szó szerint így tartalmazza.)*

---

## 2. Átméretezés — mi nyúlik és mi nem

Ezt a tulajdonos két képernyőképe **közvetlenül** igazolja.

### 2.1 A szabályok a `.tre`-ből

*Forrás: `foldermgr.tre` — pl. a `foldermgr/instructions_text` a
`foldermgr.tre:23` sorban áll.*

| elem | vízszintesen | függőlegesen |
|---|---|---|
| `base` | **nyúlik** (`m_scaleX`) | alul rögzítve (`m_offsetB`) |
| `left_side` / `right_side` | mindig **fele-fele**, 4 képpont külső margóval | az ablak aljáig |
| `foldertree` | **nyúlik** | **nyúlik**, az alja `−60` |
| `watched_folders` | **nyúlik** (`−10`) | **nyúlik**, az alja `−60` |
| `foldermgr/instructions_text` | **fix 232** széles | fix 73 magas |
| `status_decrect` (a csoportkeret) | **fix 231** széles | **fix 172** magas |
| `status_group`, a három rádió, a `frexclude` | fix | fix |
| `line` | **nyúlik** (`m_scaleX`) | fix |
| `ok` / `cancel` / `help` | fix 98×28, **jobb-alsó sarokhoz** rögzítve | ua. |
| `size` (fogantyú) | fix 20×20, **jobb-alsó sarokhoz** rögzítve | ua. |

**A `−60` a lista-aljakon pontosan a gombsáv helye**: a gombok teteje a
vászon alsó élétől 40, a magasságuk 28, alattuk 12 — összesen 60.

**A nagyított képernyőképen ez látszik is:** a csoportkeret jobb széle és a
Figyelt mappák lista jobb széle közt **több mint száz képpontnyi üres sáv**
marad, mert a keret nem nyúlik, a lista igen.

### 2.2 Az átméretező fogantyú — `Property winsize 1`

A `.tre`-parszer (`0x009ca5e0`) a kulcsszót a csomópont **`+0x22f`**
bájtjába írja (`0x009cb19d`); a párja, a `windrag` a **`+0x22e`**-be
(`0x009cb122`). *(A `picasa-eger-es-kijeloles.md` 1/b szakasza a
`windrag`-ot „egyetlen szállított `.tre` sem használja" jelzéssel sorolta
fel — a `winsize`-ra ez **nem** áll: itt használatban van.)*

**A `windrag` ág nem azonos a `winsize`-zal.** A `0x009e5590` eseménykezelő
találatkor a `+0x22e` jelzőnél törli a capture-állapotot, az első engedélyezett
leszármazotton virtuális `+0x24` műveletet kér, lefuttatja a
`0x00a57680` capture-felszabadító rutint, majd a cél virtuális `+0x18`
műveletét hívja. A közvetlen `ReleaseCapture`/`WM_SYSCOMMAND(SC_SIZE)`
átadás a `+0x22f` **`winsize`** ágban, a `0x00984350` címen történik; a
`windrag` önálló ablakmozgatását ebből a kódból nem szabad tényként
kimondani.

Az egérlenyomás-kezelő (`0x009e5590`):

```asm
0x009e559c  cmp byte [ebx+0x22d], 0     ; húzható csomópont?
0x009e55a7  cmp byte [ebx+0x22e], 0     ; windrag?
0x009e55b0  cmp byte [ebx+0x22f], 0     ; winsize?
0x009e55b7  jne 0x9e55ce                ;   ha egyik sem → 0xF4241 (nem kezeltem)
...                                     ; találat-vizsgálat a csomópont téglalapjára
0x009e5650  cmp byte [ebx+0x22f], 0
0x009e5657  je  0x9e5683                ;   winsize ág:
0x009e5670  call 0x984350               ;   ← ÁTADÁS A WINDOWSNAK
```

és a `0x00984350` a teljes mechanizmus:

```asm
0x009843b4  push 0x17 / GetSystemMetrics(SM_SWAPBUTTON)
0x009843cb  GetAsyncKeyState(<a „bal" gomb>)
0x009843d1  test ax, 0x8000 / ja        ; ha NINCS lenyomva → nem indul (−1)
0x009843dd  dl = [0xd678d4]             ; jobbról-balra (RTL) elrendezés?
0x009843e9  edx = 8 (LTR) vagy 7 (RTL)
0x009843ec  edx |= 0xf000               ; SC_SIZE | WMSZ_BOTTOMRIGHT = 0xF008
0x009843f3  SendMessage(hwnd, WM_SYSCOMMAND (0x112), 0xF008, 0)
0x009843ff  PostMessage(hwnd, WM_LBUTTONDOWN (0x201), 0, 0)
0x0098440f  PostMessage(hwnd, WM_LBUTTONUP  (0x202), 0, 0)
```

**Vagyis a fogantyú nem méretez maga, hanem átadja a Windows saját modális
méretező hurkának, a JOBB-ALSÓ sarokból** (RTL nyelvnél a bal-alsóból). A
két szintetikus egérüzenet indítja el azonnal a követést.

### 2.3 Van-e minimális méret?

**Nincs saját minimum.** Az ablakeljárás (`0x00920fa0`, 1367 bájt) **nem
kezeli** a `WM_GETMINMAXINFO`-t (`0x24`) — a teljes függvény
diszasszemblálva egyetlen ilyen összehasonlítást sem tartalmaz. A méretet
tehát kizárólag a Windows alapértelmezett minimuma korlátozza, és a
`docbounds` (550×450) a **kiinduló**, nem a legkisebb méret.

*Bizonyítottsági fok: **MEGERŐSÍTVE 2026-08-24** — a korábbi „erős"
minősítés kikötése (*„ha a dialógus más ablakosztályt használna, a keresés
mellémenne"*) **megszűnt**, mert azóta MINDEN ablakosztály át van nézve:*

| ellenőrzés | eredmény |
|---|---|
| a program által regisztrált ablakosztályok száma | **4** (`RegisterClassA` 1 + `RegisterClassExA` 2 + `RegisterClassW` 1) |
| ablakeljárások (a `DefWindowProcA` négy hívója) | `0x0040aed0`, `0x0054c540`, `0x00923e90`, `0x00924170` |
| `cmp …, 0x24` (**WM_GETMINMAXINFO**) mind az ötben (a `0x00920fa0`-val együtt) | **0 darab** |
| `0x214` (**WM_SIZING**) mind az ötben | **0 darab** |
| ugrótáblás üzenet-diszpécser (ami elrejthetné) | **nincs** egyikben sem |
| a talált `0x24` immediate-ek (2 eljárásban, 4 helyen) | **mind veremkeret-eltolás** (`sub esp, 0x24`, `[ebp-0x24]`), egyik sem üzenet-összevetés |

*A negatív állítás tehát nem egy függvényen, hanem a **teljes
ablakeljárás-készleten** áll.*

---

## 3. Az ikonok — és egy MEGDŐLT szín

| réteg | méret | mit ábrázol | szín **a futó programban** |
|---|---|---|---|
| `icon_once` | 18×14 | pipa | **zöld** |
| `icon_exclude` | 16×17 | X | **piros** |
| `icon_always` | 17×18 | körkörös nyíl („C") | **kék** |
| `nofr_on` | 20×19 | arc-sziluett **áthúzva, gyűrűben** | **piros** gyűrű, szürke arc |
| `nofr_off` | 24×19 | arc-sziluett **zöld pipával** | zöld pipa |

> **HELYESBÍTÉS (#1160).** A korábbi `respack.py`-vel kiírt PNG-ken az X KÉK,
> a „C" NARANCS, a `nofr_on` gyűrűje KÉK volt. A futó programban (a
> tulajdonos képernyőképe) piros, kék, illetve piros. A különbséget a nyers
> **BGRA** képpontok téves RGBA-értelmezése okozta; a kicsomagoló most PNG-
> íráskor BGRA→RGBA átalakítást végez, ezért a három PNG is a helyes piros,
> kék, piros színt adja.
>
> Mérés: az `icon_exclude` domináns képpontja a kimeneten `(35, 35, 242)` —
> cserével `(242, 35, 35)` = piros ✔. `icon_always`: `(227, 138, 2)` →
> `(2, 138, 227)` = kék ✔. A zöld pipa `(126, 220, 124)` cserétől
> **változatlan** — ezért nem tűnt fel eddig.
>
> A nem szürke, respack-PNG-ből vett korábbi állítások #1160-as auditja a
> `picasa-respack-format.md` 4.1 szakaszában olvasható.

Az ikonok **kétszer** jelennek meg: a **fában** minden mappa sorában (az
effektív állapot), és a jobb oldali három rádiósor mellett (a jelentésük
magyarázataként).

---

## 4. A fa (`foldertree`)

A képernyőképekről (ez a **hiteles** forrás) olvasva.

### 4.1 A gyökerek

```
▷ ❌ Asztal            (külön, monitor-szerű ikon)
▲ ❌ Képek             (külön, „képek" ikon)
▷ ❌ Dokumentumok      (külön, dokumentum-ikon)
▷ ❌ C:\               (meghajtó-ikon)
▷ ❌ P:\               (hálózati meghajtó ikonja — MÁS, mint a C:\)
```

Tehát: **Asztal, Képek, Dokumentumok, majd MINDEN meghajtó**, a
rendszermappák saját ikonjukkal, a meghajtók típus szerinti ikonnal. A
közönséges mappák egységes sárga mappaikont kapnak.

### 4.2 Egy sor felépítése (balról jobbra)

```
[ kinyitó ▷/▲ vagy üres ]  [ állapot-ikon ]  [ arcfelismerés-jelvény, ha van ]  [ mappaikon ]  [ név ]
```

A kijelölt sor **teljes szélességű, tömör sávval** van kiemelve.

### 4.3 Az effektív állapot ÖRÖKLŐDIK, de felülírható

A nagyított képernyőkép `Képek` alatti részlete (a mérvadó bizonyíték):

```
▲ 🔄🚫 Picasa                      ← Keresés mindig + arcfelismerés kikapcsolva
     🔄🚫 Captured Videos           ← ÖRÖKLI mindkettőt
     🔄🚫 Képernyőfelvételek        ← ÖRÖKLI
     🔄🚫 Kollázsok                 ← ÖRÖKLI
   ▷ ❌   PicasaPy-golden-kit       ← FELÜLÍRVA: Eltávolítás a Picasából
   ▷ ❌   PicasaPy-merokit          ← FELÜLÍRVA
     🔄🚫 Screen Captures           ← ÖRÖKLI
▷ ✅ podcast                        ← Keresés egyszer (KIJELÖLVE)
  ❌ Sanoma Media logo
```

Két szabály, amit ez kimond:

1. **A fában látszó ikon az EFFEKTÍV (örökölt) állapot**, nem csak a
   kifejezetten beállított.
2. **A gyerek felülírhatja a szülőt** — figyelt mappán belül is lehet
   kizárt almappa.

Ugyanez az arcfelismerés-jelvényre: a `Picasa` ki van zárva, a gyerekei
**öröklik** a jelvényt. A kódbeli bizonyíték: 5.4.

---

### 4.4 A fa SOR-RAJZOLÁSA — mért értékek (2026-08-21)

A rajzoló a `0x007c0130` (1035 bájt), amit az ablaknyitó (`0x005ce590`)
állít fel. A használt erőforrások és konstansok:

| mi | honnan | érték |
|---|---|---|
| **sormagasság** | `alist_height` konstans (`0x007c6660`), alapértelmezés `0x16` | **22 képpont** |
| **szintenkénti behúzás** | `alist_indent` (`0x007c04a3`, `0x007c051f`) | **17 képpont** |
| **betű** | `Praxis Semi Bold/Heavy` (`0x007c03b1`), méret `alist_fontsize_win` | **14** |
| **becsukott csomópont nyila** | `arrows2/right` (283 bájt) | ▷ |
| **kinyitott csomópont nyila** | `arrows2/down` (163 bájt) | ▲ |
| **állapot-ikonok** | `icons/folder_manager_scan_once` · `_exclude` · `_watch` | ld. lent |
| **arcfelismerés-jelvény** | `icons/folder_manager_nofr` | ld. lent |

**A `constants.ui` (70 soros szövegfájl) vonatkozó sorai** — ez NEM
respack, tehát a 3. szakasz R↔B cseréje **nem** érinti:

```
alist_height=22
alist_fontsize_win=14
alist_indent=17
alist_bgcolor=0xFFF3F3F3
alist_hicolor_win=0xFF83A7BD
alist_selcolor_win=0xFF25648B
```

> ✅ **A 22 képpontos sormagasság a képernyőképen visszamérve pontos:** a
> nagyított képen tizennégy egymás utáni sor y-koordinátája
> 76, 98, 119, 141, 163, 185, … — a szomszédos különbségek **22** (egy
> helyen 21, kerekítésből).

#### A KIJELÖLT sor színe — ~~mérés, mert a forrásokban nincs~~ MEGVAN A KÓDBAN (2026-08-21)

A kijelölt sor színe **mindkét képernyőképen `#7D8397`** (RGB 125, 131,
151; az alapon 238, a nagyítotton 274 képpont dominanciával). Ez **NEM**
az `alist_selcolor_win` (`#25648B`), és a `constants.ui` egyetlen
konstansa sem áll közel hozzá; a teljes `runtime/` mappában sincs `7D8397`
minta.

> ✅ **A „csak mérésből tudjuk" megszorítás MEGDŐLT.** A sor-rajzoló
> (`0x007c6700`, `CFolderMgrDialog::TreeListDraw` vtable 2. metódusa)
> **kódkonstansként** számolja ki mindkét színt, ugyanazzal az
> ágmentes idiómával, amit a `popuplist` kiemelt soránál is találtunk
> (#894):
>
> ```asm
> 0x007c674d  mov  ecx, [eax + 4]
> 0x007c6750  and  cl, 2              ; a KIJELÖLT bit
> 0x007c6753  neg  cl
> 0x007c6755  sbb  ecx, ecx           ; kijelölt -> 0xFFFFFFFF, egyébként 0
> 0x007c6757  and  ecx, 0xff7f859a
> 0x007c675d  add  ecx, 0xfffdfdfd
> ```
>
> - kijelölt: `0xff7f859a + 0xfffdfdfd` = **`0xFF7D8397`** → **`#7D8397`**
> - nem kijelölt: `0 + 0xfffdfdfd` = **`0xFFFDFDFD`** → **`#FDFDFD`**
>
> A mérés tehát végig helyes volt, és most **független, kódbeli
> megerősítést** kapott. A `test [sor+4], 2` kijelölt-bit ugyanaz, mint a
> `popuplist`-nél — a két lista **egy közös sor-modellt** használ.

#### 4.4/b A sor SORRENDJE és az, hogy MINDIG van állapot-ikon (2026-08-21)

Ez a szakasz a `0x007c6700` szó szerinti olvasásából származik, és a fenti
4.2 vázlatot **normatívvá** teszi. Az erőforrás-mezők azonosítása a
felállítóból (`0x007c0130`, `0x007c03ec`–`0x007c045c`) **közvetlen**, nem
következtetés:

| mező | erőforrás | mi ez |
|---|---|---|
| `[dlg+0x318]` | `arrows2/right` | becsukott nyíl ▷ |
| `[dlg+0x340]` | `arrows2/down` | kinyitott nyíl ▲ |
| `[dlg+0x368]` | `icons/folder_manager_watch` | **kék C** |
| `[dlg+0x390]` | `icons/folder_manager_exclude` | **piros X** |
| `[dlg+0x3b8]` | `icons/folder_manager_scan_once` | **zöld pipa** |
| `[dlg+0x3e0]` | `icons/folder_manager_nofr` | arcfelismerés-jelvény |

**A rajzolás sorrendje egy soron belül, balról jobbra:**

1. **háttér** (`#7D8397` / `#FDFDFD`, ld. fent);
2. **kinyitó nyíl** — `arrows2/right` vagy `arrows2/down`; **levélelemnél
   egyik sem** (a `0x007c6831` ág egyszerűen kihagyja);
3. **állapot-ikon** — a `0x007c68ec`–`0x007c691d` blokk **if / else-if /
   else**, tehát ⚠️ **NINCS olyan ág, amiben egy sor ikon NÉLKÜL
   marad.** Az alapértelmezett (egyik jelző sincs beállítva) ág a
   `[dlg+0x3b8]`;
4. **arcfelismerés-jelvény** (`[dlg+0x3e0]`) — **feltételes, második**
   ikon, az állapot-ikon MELLETT, saját `[dlg+0x3e8]` előretolással;
5. **mappaikon**, majd a **név**.

> ⛔ **Ez a pont buktatta meg a mi megvalósításunkat (#1200):** nálunk a
> jelvény a név UTÁN áll, és a „nincs állapot" esetben **semmit nem
> rajzol**. Az eredetiben az ikon a név ELŐTT van, és **minden sornak van
> ikonja**.

**Az állapot forrása** (`0x007c5c40`): három tagsági keresés
(`0x00492e40`, „benne van-e az útvonal a listában") a `[dlg+0x270]`,
`[dlg+0x280]` és `[dlg+0x288]` listákon, és ha egyik sem dönt, egy
adatbázis-lekérdezés (`0x004ee260`) az 5-ös, illetve 1-es állapotkódra.

**A három ikon mért képe** (a `respack.yt`-ból kicsomagolva, átlátszóság
fölötti átlagos RGB):

| erőforrás | méret | átlagszín | mit ábrázol |
|---|---|---|---|
| `icon_once` / `folder_manager_scan_once` | **18 × 14** | (70, 181, 71) **zöld** | pipa |
| `icon_exclude` / `folder_manager_exclude` | **16 × 17** | (194, 29, 30) **piros** | X |
| `icon_always` / `folder_manager_watch` | **17 × 18** | (26, 108, 164) **kék** | körkörös nyíl („C") |
| `nofr_on` | **20 × 19** | — | arc-sziluett **piros tiltótáblával** = arcfelismerés KI |
| `nofr_off` | **24 × 19** | — | arc-sziluett **zöld pipával** = arcfelismerés BE |

⚠️ A `nofr_*` nevek **fordítva olvasandók**, mint amit a név sugall:
`nofr_on` = „a *nincs-arcfelismerés* be van kapcsolva" = a tiltott
állapot. A `.tre`-ben a `nofr_on` az alapból látható, a `nofr_off`
`m_hidden`, és a `frexclude` gomb `hidetarget`/`showtarget` párja
cseréli őket.

*Bizonyítottsági fok: **megerősített** — mind a mező→erőforrás
hozzárendelés, mind a rajzolási sorrend szó szerinti kódolvasásból; az
ikonok mérete és színe a kicsomagolt képekből mérve.*

**Ami itt NYITVA marad:** hogy a három tagsági lista közül pontosan
melyik jelző (`0x007c5c40` arg2/arg3/arg4 kimenete) tartozik a piros
X-hez és melyik a kék C-hez, a veremaritmetikából **nem dőlt el
egyértelműen** — ezt szándékosan nem találgatom. A gyakorlati sorrendet
a tulajdonos képernyőképe adja meg (nem indexelt mappa → piros X,
figyelt → kék C), és a jobb oldali rádiósor ikonjai amúgy is
egyértelműsítik a szerep→ikon párosítást. Folytatás, ha kell:
`0x007c5c40` argumentumainak pontos leképezése.

#### A fa ikonjai MÁS erőforrások, mint a rádiósoroké

*Forrás: `foldermgr.tre:46` (`foldermgr/icon_always`) · `foldermgr.tre:43` (`foldermgr/icon_exclude`) · `foldermgr.tre:40` (`foldermgr/icon_once`) — és további 1 elem ugyanott.*

| szerep | a jobb oldali rádiósorban | **a fában** | azonos? |
|---|---|---|---|
| Keresés egyszer | `foldermgr/icon_once` (643 b) | `icons/folder_manager_scan_once` (643 b) | **igen** |
| Eltávolítás | `foldermgr/icon_exclude` (978 b) | `icons/folder_manager_exclude` (978 b) | **igen** |
| Keresés mindig | `foldermgr/icon_always` (1068 b) | `icons/folder_manager_watch` (1068 b) | **igen** |
| arcfelismerés | `foldermgr/nofr_on` (1678 b) / `nofr_off` (1818 b) | `icons/folder_manager_nofr` (**1368 b**) | **NEM — harmadik, külön kép** |

*(Ugyanez a négy ikon `gpuploader_icons/` néven is szerepel a csomagban —
a feltöltő is használja őket.)*

*Bizonyítottsági fok: **megerősített** a konstansokra és az
erőforrásnevekre (a kód szó szerint ezeket kéri, a `constants.ui` szöveges
fájl) · **megerősített** a 22 képpontos sormagasságra (kódból ÉS
képernyőképről) · **megerősített** a kijelölés színére mint MÉRÉSRE (két
független képernyőkép), de a forrása ismeretlen.*
### 4.5 Mi történik a fában KATTINTÁSRA

A fa és a „Figyelt mappák" lista eseményeit a `0x007c5830` (971 bájt)
osztja szét, **három** értesítésnév szerint:

| értesítés | mikor | mit csinál |
|---|---|---|
| **`lb_preclick`** | kattintás ELŐTT | csak a fa-listaboxra (`[dlg+0x2f8]`) fut; ha az index változott, a `0x007c9d40`-en át frissít, majd `0x007bfb30` / `0x007c63a0` |
| **`lb_selected`** | a kijelölés megváltozott | → **`0x007c60d0`**: a három rádió és az arcfelismerés-sor újraszámolása a kijelölt mappára (5.2, 5.3), majd `0x007c91c0`, `0x009d2810`, `0x007bf130` |
| **`lb_predouble`** | dupla kattintás ELŐTT | → `0x007c63a0`, ami a fa-csomópont `[+0x290]` jelzőjét 1-re állítja és a `[dlg+0x414]` segédobjektumon a `0x007bf210`-et hívja; siker (`0xF4240`) esetén `0x007c9d40` + `0x009d2210` a listaboxon |

> **Ez zárja le a „mi történik egy fa-sor kijelölésekor" kérdést:** a jobb
> oldali panel teljes újraszámolása **az `lb_selected` értesítésen** lóg,
> nem a rádiógombokon.
>
> A `lb_predouble` ág a `[dlg+0x414]` segédobjektumot kérdezi — ugyanazt,
> amit az ablak bezárása előtt le kell állítani (10/b.2), és amit a
> fa-sorból útvonalat képző `0x007bfcb0` is használ. **Erős** jelölt arra,
> hogy ez a mappák felsorolását (kinyitás/lusta betöltés) végzi, de a
> `0x007bf210` tartalmát nem olvastuk el — ld. 12.

---

## 5. A három állapot és az arcfelismerés-kapcsoló

### 5.1 A jobb oldali panel felépítése

```
┌ status_decrect (süllyesztett keret) ──────────────────┐
│  Az aktuális mappa esetében:                           │
│    ( ) ✅  Keresés egyszer          ← ALAPBÓL bejelölt │
│    ( ) ❌  Eltávolítás a Picasából                     │
│    ( ) 🔄  Keresés mindig                              │
│  ────────────────────────────────────────────────────  │  ← line
│    [🚫] Arcfelismerés kikapcsolva                      │
└────────────────────────────────────────────────────────┘
```

**A sorrend kötött:** Keresés egyszer → Eltávolítás → Keresés mindig (a
vászon y = 130 / 163 / 196). Az alapállapot a `scan_once`
(`Property setpressed 1`).

### 5.2 Az állapotfrissítő — `0x007c60d0(dialógus, útvonal)`

Minden fa-kijelölés után lefut, **mind a három rádiónak külön beállítja a
benyomottságát ÉS az engedélyezettségét** (`[vezérlő+0x20e]`, a `disable`
mező), majd a végén meghívja az arcfelismerés-sor frissítőjét
(`0x007c6382 → 0x007c64a0`).

Minden lekérdezés a `0x00492e40(lista, útvonal)` „benne van-e, hányadik"
kereséssel megy. A listák **KÉT külön objektumon** élnek:

| mező | gazdája | mi ez |
|---|---|---|
| `[lib+0x280]` / `[+0x284]` | **a könyvtár** | a `scanlist.txt` **`+` (befoglaló) gyökerei** — ld. 11. |
| `[lib+0x288]` / `[+0x28c]` | **a könyvtár** | a `scanlist.txt` **`−` (kizáró) gyökerei** |
| `[lib+0x2e0]` / `[+0x2e4]` / `[+0x2e8]` | **a könyvtár** | a `scanlist.txt` **előtag nélküli**, beolvasott mappái |
| `[lib+0x364]` / `[+0x368]` | **a könyvtár** | a **`watchedfolders.txt`** tartalma |
| `[lib+0x3b4]` / `[+0x3b8]` | **a könyvtár** | a **`frexcludefolders.txt`** tartalma |
| `[dlg+0x270]` | a dialógus | az **iPhoto/Apple Photos** oldalág listája |
| `[dlg+0x290]`, `[dlg+0x298]` | a dialógus | az **arcfelismerés-kizárás függő delta-párja** (`0x007c5ef0`) |
| `[dlg+0x2a8]` | a dialógus | a „Keresés mindig" ág függő listája (`0x007c2c11`) |

> ⚠️ **HELYESBÍTÉS a lap első kiadásához képest.** Az első változat mind a
> hat listát a **dialógusnak** tulajdonította. Tévedés: a `0x007c5c40`
> `this`-e (a `0x007c60d0` **második** argumentuma) a **könyvtár**, nem a
> dialógus — ezt a `scanlist.txt` írója/olvasója dönti el, ami ugyanezt a
> `+0x280`/`+0x288` párost használja (`0x004f649f`, `0x004f667a`).

*Bizonyítottsági fok: **megerősített** a könyvtár-oldali mezőkre (a
fájlíró/olvasó szó szerint ezeket használja) · **erős** a dialógus-oldali
pár-értelmezésre.*

### 5.2/b Melyik RÁDIÓ melyik listát írja — mérve (2026-08-21, M1)

A három rádió ága a fa kijelölt sorából útvonalat képez (`0x007bfcb0`),
majd **mind más listán** végzi a `0x00492e40` keresést:

| rádió | az ág kezdete | a mutált lista | cím |
|---|---|---|---|
| **Keresés egyszer** | `0x007c3718` | **`[dlg+0x288]`** | `0x007c375c` |
| **Eltávolítás a Picasából** | `0x007c40fa` | **`[dlg+0x270]`** | `0x007c4184` |
| **Keresés mindig** | `0x007c290a` | **`[dlg+0x2a8]`** *(delta)* **és `[dlg+0x270]`** *(a látható lista, `0x007c2f5b`)* | `0x007c2c11` |
| arcfelismerés-kizárás | — | **`[dlg+0x290]` / `[dlg+0x298]`** | `0x007c5f37`, `0x007c5f4a` |

Az „Eltávolítás" ága ezen felül a **Figyelt mappák listbox** (`[dlg+0x2fc]`)
kijelölését is beszámítja (`0x007c412e`) — vagyis a rádió **onnan is** tud
tételt eltávolítani, nem csak a fából.

> ⚠️ **HELYESBÍTÉS (2026-08-21, M11 — lásd 5.2/d):** a `watchedfolders.txt`
> **NEM** a `[dlg+0x2a8]`-ból íródik. A fájlig vezető lánc:
> `[dlg+0x270]` → az alkalmazó 2. paramétere → `[könyvtár+0x2bc]+0xf8` →
> `0x004f5960`. A `+0x2a8` munkamenet-helyi delta, ami az alkalmazóig el
> sem jut.

> ⚠️ **PONTOSÍTÁS (2026-08-21, M6 — lásd 14.2):** a `[dlg+0x270]` nem csak
> „az Eltávolítás rádió listája". Ez **a jobb oldali „Figyelt mappák" lista
> tényleges tartalma** — a sorrajzoló (`0x007c6ba0`) és a kattintáskezelő
> (`0x007c5a89`) is ezt a tömböt olvassa, `[dlg+0x274]>>1` elemszámmal. A
> „Keresés mindig" a **végére fűz** bele (`0x007c2f5b`), az „Eltávolítás"
> **kivesz** belőle (`0x007c4184`).

Az OK-ra futó alkalmazó **hat argumentumot** kap (`0x007c56fb`–`0x007c571f`):

```asm
push [dlg+0x298]   ; arcfelismeres-delta
push ebx           ; a helyben epitett lista
push [dlg+0x288]   ; „Kereses egyszer" delta
push [dlg+0x280]   ; a par masik fele
push [dlg+0x270]   ; „Eltavolitas" delta
push [dlg+0x268]   ; a CThumbUI
call 0x005cef20
```

majd két feltételes `0x007bfec0` hívás a `[[dlg+0x268]+0x2bc] + 0xf8`
tárolóra (`0x007c5743`, `0x007c5767`).

> ⚠️ **Helyesbítés a lap korábbi állításához:** a `[dlg+0x270]`-t nem
> csak az iPhoto-oldalág használja — **ez az „Eltávolítás" deltája**, és
> a watch-ág iPhoto-útja is ide nyúl. Az iPhoto-ág tehát nem külön lista,
> hanem ugyanez.

**Ami MÉG nincs meg (M1 folytatása):** hogy a `0x005cef20` melyik
argumentumot vezeti a `scanlist.txt` **`+`**, és melyiket a **`−`**
szakaszába. A fájl oldaláról tudjuk, hogy a `+` a `[lib+0x280]`, a `−` a
`[lib+0x288]` (11.3) — a dialógus-oldali delták hozzárendelése az
alkalmazó belsejében dől el.

*Bizonyítottsági fok: **megerősített** a rádió → dialógus-lista
hozzárendelésre és az alkalmazó argumentumaira · **nyitott** a
dialógus-lista → fájlszakasz hozzárendelés.*

### 5.2/c Az OK teljes alkalmazási útja — VÉGIGKÖVETVE (2026-08-21, M1 lezárva)

Az alkalmazó `0x005cef20` **hat argumentumot** kap
(`0x007c56fb`–`0x007c571f`), és ebben a sorrendben dolgozik:

| # | argumentum | mi ez | mit csinál vele |
|---|---|---|---|
| 1 | `[dlg+0x268]` | a `CThumbUI` | ebből képzi a könyvtár-objektumot: `esi = [arg1+0x2bc] + 0xf8` (`0x005cef2e`) |
| 2 | `[dlg+0x270]` | **„Eltávolítás" delta** | **1. ciklus** (`0x005cef64`): minden útvonalát megkeresi a **figyelt** listában (`[lib'+0x364]`, `0x005cef87`), és a **nem** figyeltekre fut a törzs |
| — | — | — | **2. ciklus** (`0x005cf1b2`): végigjárja magát a **figyelt listát** (`[lib'+0x368]>>1` darab) |
| 3 | `[dlg+0x280]` | a beolvasási lista egyik deltája | **`0x004f6a20`** (`0x005cf411`) — ld. lent |
| 4 | `[dlg+0x288]` | a beolvasási lista másik deltája | ugyanoda |
| 5 | `ebx` (helyben épített) | — | `0x00491210` (`0x005cf529`) |
| 6 | `[dlg+0x298]` | **arcfelismerés-delta** | ugyanoda, `0x00491210` |

majd `0x004b9200` (a **`]album:removed`** token, `0x005cf500`) és végül
**`0x0065b840`** (`0x005cf535`) — a **nézet/keresősáv frissítése**.

**A kulcs a `0x005cf411`:**

```asm
0x005cf3eb  mov eax, [esp+0x4c]   ; [dlg+0x288]
0x005cf3ef  mov ecx, [esp+0x48]   ; [dlg+0x280]
0x005cf3f3  mov ebx, [esp+0x1c]   ; a konyvtar-objektum
0x005cf3f7  push eax / push ecx / push edx (kimenet) / push ebx
0x005cf411  call 0x4f6a20          ; <<< a SCANLIST kezeloje (5127 bajt)
```

A `0x004f6a20` **pontosan a `scanlist.txt` írója (`0x004f61c0`) és
olvasója (`0x004f6380`) között ül** — vagyis a **`scanlist.txt` `+` és `−`
szakasza a dialógus `[+0x280]` / `[+0x288]` deltáiból frissül.**

#### A rádió → delta → tároló lánc, teljes egészében

| rádió | a mutált delta | hová vezet |
|---|---|---|
| **Keresés mindig** | `[dlg+0x2a8]` (`0x007c2c11`) | → `watchedfolders.txt` (`[lib'+0x364]`, `0x005cef87`) |
| **Eltávolítás a Picasából** | `[dlg+0x270]` (`0x007c4184`) | → az 1. ciklus: kiveszi a figyelt listából; + `]album:removed` |
| **Keresés egyszer** | `[dlg+0x288]` (`0x007c375c`) | → `0x004f6a20` → **`scanlist.txt`** |
| **arcfelismerés-kapcsoló** | `[dlg+0x290]` / `[dlg+0x298]` | → `0x00491210` → `frexcludefolders.txt` |

> **EGY részlet marad a láncból:** hogy a `0x004f6a20` a 3. paramétert
> (`[dlg+0x280]`) teszi-e a **`+`**, és a 4-et (`[dlg+0x288]`) a **`−`**
> szakaszba, vagy fordítva. A függvény a két listát **paraméterként**
> kapja (`ebp` = 3., `[esp+0x3c]` = 4.), és nem hivatkozik közvetlenül a
> `+0x280`/`+0x288` mezőkre — a polaritás az 5127 bájtos törzsében dől el.
>
> **Az olcsó bizonyítéklánc itt kimerült** (index → xref → célzott
> diszasszemblálás mind lefutott); innentől a teljes törzs átolvasása
> következne. **A megvalósításunkat nem érinti:** mi nem írunk
> `scanlist.txt`-et, és a három állapot jelentése a feliratokból
> egyértelmű. **Csak a Picasa-telepítés ÁTVÉTELÉHEZ (#146) kell**, ahol a
> meglévő fájl `+`/`−` sorait értelmezni kell — ott viszont a **valódi
> mintafájlunk** (`research/testdata/Picasa2/db3/scanlist.txt`: négy `+`
> sor, mind meghajtó-gyökér, nulla `−` sor) önmagában is eligazít.

*Bizonyítottsági fok: **megerősített** a teljes útvonalra (mind a hat
argumentum, mindkét ciklus, a `0x004f6a20`-ra való átadás és a záró
nézetfrissítés) · **nyitott, de hatókörön kívüli** a `+`/`−` polaritás.*

### 5.3 Az arcfelismerés-sor — `0x007c64a0`

```c
// esi = az aktuális mappa útvonala, ebp = a dialógus
szulo        = szulo_utvonal(esi);                  // 0x009a3b50
szulo_kizart = (0x007c5ef0(dlg, szulo, …) != 0);    // [esp+0x16]
sajat_kizart = (0x007c5ef0(dlg, esi,   …) != 0);    // [esp+0x15]

frexclude.pressed  = (sajat_kizart == 0);           // 0x007c65a8 — BENYOMVA = BE
frexclude.disabled = (arg2 != 0) || szulo_kizart || (nincs útvonal);  // 0x007c65d5
frexclude_label    = sajat_kizart ? "Face Detection Off" : "Face Detection On";
```

**Két, a képernyőképeken közvetlenül látható következmény:**

1. **Ha a SZÜLŐ ki van zárva, a kapcsoló LETILTOTT.** Az alap
   képernyőképen a kijelölt `Kollázsok` szülője a kizárt `Picasa`, és a sor
   **kiszürkült**: „Arcfelismerés kikapcsolva". Kizárt szülőn belül tehát
   nem lehet gyereket visszakapcsolni.
2. **Ha nincs kizárva, a kapcsoló él**, és a felirata „Arcfelismerés
   bekapcsolva" — a nagyított képernyőképen a `podcast` mappánál pontosan
   ez látszik.

Az ikoncsere (`nofr_on` ↔ `nofr_off`) **deklaratív**: a `.tre`
`hidetarget`/`showtarget` párja intézi, nem kód.

### 5.4 A kizártság ÖRÖKLŐDÉSE — a kódbeli bizonyíték (`0x007c5ef0`)

A 4.3-ban a képernyőképről olvasott öröklődés a kódban is megvan. A
lekérdező **két listát** néz meg, és ha egyikben sincs találat, **felmegy a
szülőhöz**:

```asm
0x007c5f23  lea ecx, [ebp + 0x290]      ; 1. lista
0x007c5f37  call 0x492e40               ;   benne van az útvonal?  → bl
0x007c5f3f  lea ecx, [ebp + 0x298]      ; 2. lista
0x007c5f4a  call 0x492e40               ;   benne van?             → al
0x007c5f5b  je  0x7c5f6b                ; ha egyikben sincs…
0x007c5f8c  call 0x9a3b50               ;   …az utolsó komponens LEVÁGÁSA
0x007c6037  call 0x7c5ef0               ;   …és REKURZIÓ a szülőre
```

**Az állapot a legközelebbi olyan ős-mappától öröklődik, amelyiknek van
bejegyzése** — pontosan ezt mutatja a képernyőkép (`Picasa` kizárt, három
gyereke örökli, két másik gyerek saját bejegyzéssel felülírja).

---

### 5.2/d A MENTÉSI LÁNC — mi jut el a fájlokig (2026-08-21, M11)

Ez a szakasz a 14.6 nyitott pontját zárja le: mi a viszony a **látható
lista** (`[dlg+0x270]`) és a **„Keresés mindig" delta** (`[dlg+0x2a8]`)
között.

#### A lánc

```
„Keresés mindig" rádió (0x007c290a)
   ├─→ [dlg+0x2a8]   „mindig"-delta, ha még nincs benne  (0x007c2c05)
   └─→ [dlg+0x270]   a LÁTHATÓ „Figyelt mappák" lista     (0x007c2f5b)
                          │
                     OK → 0x007c4df0 → 0x005cef20 2. paraméterként
                          │   (az első ciklus: 0x005cef3e–0x005cf198)
                          ↓
                   [könyvtár+0x2bc] + 0xf8      ← a KÖZÖS scan-lista tároló
                          │   (ugyanaz, amit az első indítás panelje ír — ld.
                          │    picasa-elso-inditas.md 6.5 —, és amit a
                          │    0x007bfec0 is bővít)
                          ├─→ 0x004f5960 → watchedfolders.txt  (0x005cf49b)
                          └─→ 0x004f6a20 → scanlist.txt        (0x005cf411)
```

Az alkalmazó szignatúrája a prológusból (`ret 0x18` = hat dword):

```asm
0x005cef23  mov  eax, dword ptr [esp + 0x30]   ; 1. par = a KÖNYVTÁR ([dlg+0x268])
0x005cef27  mov  ecx, dword ptr [esp + 0x34]   ; 2. par = &[dlg+0x270]
0x005cef2e  mov  esi, dword ptr [eax + 0x2bc]
0x005cef36  add  esi, 0xf8                     ; a közös scan-lista tároló
0x005cef46  mov  dword ptr [esp + 0x1c], esi   ; ezt kapja meg a fájlíró
```

és a fájlíró hívása:

```asm
0x005cf3f3  mov  ebx, dword ptr [esp + 0x1c]   ; = a +0xf8 tároló
0x005cf49a  push ebx
0x005cf49b  call 0x4f5960                      ; watchedfolders.txt
```

#### ⚠️ HELYESBÍTÉS az 5.2/b táblázathoz

Az 5.2/b azt írta: *„mindig = `[dlg+0x2a8]` → `watchedfolders.txt`"*. A
rádió valóban ír a `+0x2a8`-ba, de **a fájlig vezető út nem ezen megy**:

| | eddig így szerepelt | a mérés szerint |
|---|---|---|
| a `watchedfolders.txt` forrása | `[dlg+0x2a8]` | **`[dlg+0x270]`** → a `+0xf8` közös tároló → `0x004f5960` |
| a `[dlg+0x2a8]` szerepe | „a mindig-lista" | **munkamenet-helyi delta**, ami **nem jut el az alkalmazóig** |

A `0x005cef20` hat argumentuma között a **`+0x2a8` nincs ott**
(`0x007c56fb`–`0x007c571f`: `+0x298`, `ebx`, `+0x288`, `+0x280`, `+0x270`,
`[dlg+0x268]`).

#### Mire való akkor a `[dlg+0x2a8]`?

Mind az öt hivatkozása megvan a `0x007b0000`–`0x007d0000` tartományban:

| hely | mit tesz |
|---|---|
| `0x007c01fb` (konstruktor) | nullázás |
| `0x007c0570` (`0x007c0550`-ből) | ürítés / újrainicializálás |
| `0x007c2c05` (a „mindig" rádió) | hozzáfűzés, ha még nincs benne |
| `0x007c09f0` | **iPhoto / Apple Photos** — *hatókörön kívül* |
| `0x007c4df0` `0x007c4e5b`–`0x007c52aa` | az OK-kezelő nyitó ciklusa |

Az OK-kezelő nyitó ciklusa végigmegy a `+0x2a8`-on, és minden útvonalat két
Apple-fotókönyvtár-mintához mér (`0x0099bce0`, `0x0099bf40`); egyezésre
kiveszi a `+0x270`-ből, illetve a `+0x280`-ból, és jelzőt állít, amit az
alkalmazó után két további `0x007bfec0` hívás használ fel
(`0x007c5724`, `0x007c5748`). **Ez teljes egészében az Apple-ág** —
tulajdonosi döntés szerint hatókörön kívül (2026-08-21).

**Következtetés a PicasaPy-ra:** a `[dlg+0x2a8]` **nem kell**. Ami
számít, az a látható lista (`[dlg+0x270]`): az megy be a közös
scan-listába, és abból íródik a `watchedfolders.txt`. Ez egyben azt is
jelenti, hogy **a jobb oldali lista tartalma = amit OK-ra elmentünk** —
nincs rejtett, harmadik igazságforrás.

## 6. A figyelmeztetések és megerősítések

| mikor | erőforráskulcs | magyar szöveg |
|---|---|---|
| **teljes meghajtó** figyelésre állítása | `CFolderMgrDialog::warning` | Egy teljes meghajtó figyelése lelassíthatja a rendszert. Jobb lenne több almappát kiválasztani. Biztosan ezt kívánja tenni? |
| ~~figyelt mappa eltávolítása~~ **HALOTT, ld. 6.3** | `IDS_HOTFOLDER_CONFIRM` (+ `_TITLE`) | Ha egy figyelt mappát eltávolít, a lemezen oda mentett új fájlokat a Picasa nem veszi fel automatikusan. Biztosan ezt szeretné? |
| **OK-ra, ha kizárt mappa arcadata törlődne** | `CFolderMgrDialog::confirmfrexclude` | Biztosan eltávolítja az összes arcot és névcímkét a kihagyott mappákból? |

### 6.1 A meghajtó-figyelmeztetés PONTOS útja

```asm
; a „Keresés mindig" ág, 0x007c290a-tól
0x007c292e  call 0x7bfcb0        ; a kijelölt fa-sorból ÚTVONAL
0x007c294b  call 0x9a3d60        ; ← „ez egy teljes meghajtó?"  (69 bájt, ld. 10.)
0x007c295b  je   0x7c2a6d        ;   ha nem → mehet tovább
0x007c296f  push "CFolderMgrDialog::warning"
0x007c2995  call 0x9bac20        ; Igen/Nem párbeszéd
0x007c299d  test al, al
0x007c299f  jne  0x7c2a6d        ;   IGEN → folytatás
; --- NEM: a választás VISSZAÁLL ---
0x007c29a5  "foldermgr/watch"  → 0xa65060(ctrl, pressed=0, 1)
0x007c29ba  "foldermgr/remove" → [ctrl+0x359] = 1  + „buttontoggle" értesítés
```

> **Ha a felhasználó nemet mond, a Picasa nem „nem csinál semmit", hanem a
> rádiót visszaállítja, és az „Eltávolítás a Picasából" tételt nyomja be.**
> *(Bizonyítottsági fok: **MEGERŐSÍTVE 2026-08-24** — ld. 6.1/b.)*

### 6.1/b A „NEM" ág VÉGIGKÖVETVE — nincs korábbi állapot, amit visszaállítana

A 6.1 kikötése az volt, hogy „nem követtük végig, volt-e korábbi állapotot
visszaállító ág". **Végigkövetve: nincs, és nem is lehet.**

A teljes út a rádió-kattintástól a figyelmeztetésig
(`0x007c28c4` … `0x007c2995`) **egyetlen helyen sem menti el** a korábbi
rádióállást. A veremre csak két érték kerül: `[esp+0x20] = 0` és
`[esp+0x27] = al` (a „teljes meghajtó?" vizsgálat eredménye). Nincs olyan
mező vagy változó, amiből egy korábbi állapot visszaállítható volna.

A „NEM" ág utasításról utasításra:

```asm
0x007c299d  test al, al
0x007c299f  jne  0x7c2a6d          ; IGEN -> folytatás

0x007c29a5  edx = "foldermgr/watch"
0x007c29aa  call 0x9cd110          ; elem lekérése NÉV szerint -> eax
0x007c29af  push 1 · push 0        ; (benyomva = 0)
0x007c29b5  call 0xa65060          ; a „Keresés mindig" KIKAPCSOLÁSA

0x007c29ba  edx = "foldermgr/remove"
0x007c29bf  call 0x9cd110          ; -> ebx
0x007c29c6  cmp  byte [ebx+0x359], 1
0x007c29cd  je   0x7c2a31          ; << ŐRFELTÉTEL: ha MÁR benyomott, kihagyja
0x007c29cf  or   dword [ebx+8], 7  ; érvénytelenítés (újrarajzolás)
0x007c29d5  mov  byte [ebx+0x359], 1   ; BENYOMVA
0x007c29f3  push "buttontoggle"        ; értesítés
```

**Két új részlet:**

1. **A `+0x359` nem állapotmentő mező**, hanem a kapcsológomb **általános
   „benyomva" jelzője** — a binárisban **235 helyen** fordul elő, a
   Mappakezelőn kívül is. Tehát nem egy „korábbi rádióállás" tárolója.
2. **Az „Eltávolítás" benyomása őrfeltételes:** ha az a tétel már benyomott,
   a program **kihagyja** az egész ágat (nincs fölösleges érvénytelenítés és
   nincs `buttontoggle` értesítés).

⇒ **A „NEM" tehát nem visszaállít, hanem FELTÉTEL NÉLKÜL az „Eltávolítás a
Picasából" tételre kapcsol** — akármi volt előtte.

*Mellékesen: a `0x009cd110` egy általánosan hasznos primitív — **felületi
elem lekérése NÉV szerint**.*

*Bizonyítottsági fok: **megerősített** — a teljes út diszasszemblálva, és a
`+0x359` mező szerepe nyers bájtkereséssel (235 előfordulás) tisztázva.*

#**A megerősítő párbeszéd gombkészlete:** a közös burkoló
`0x009bac20(típus, szöveg, igen-felirat, nem-felirat, szülő, …)` hívása itt
`típus = 1`, mindkét felirat `NULL` — a burkoló ilyenkor az `il_Yes` /
`il_No` erőforrásból tölti a feliratokat, azaz **Igen / Nem** gombpár
(`0x009bac47`: `cmp eax, 1` → az „Igen/Nem" ág; `típus ≥ 2` esetén lenne
`il_Cancel`). Ugyanez áll a `confirmfrexclude` párbeszédre.

### 6.3 HELYESBÍTÉS: három szöveg HALOTT ebben a build-ben (M3, 2026-08-21)

A lap 6. szakasza (és a **#543**) azt írta elő, hogy a **figyelt mappa
eltávolításának megerősítését** (`IDS_HOTFOLDER_CONFIRM`) be kell kötni.
**Ez tévedés volt: a 3.9.141.259 soha nem mutatja meg.**

#### Hogyan dőlt el

A Picasa a Win32-erőforrás-sztringeket **egyetlen burkolón** át tölti be:

```asm
; a hivas mintaja mind a 150 helyen:
push <"IDS_NEV" mutato>     ; az i18n-kulcs
push <numerikus azonosito>  ; a .rsrc RT_STRING azonositoja
call 0x009ae710             ; -> LoadStringA(hInst, id, puffer, 0x400)  (0x009ae77e)
```

A `.rsrc` RT_STRING táblájából kibontva **265 sztring** van, köztük:

| azonosító | szöveg |
|---:|---|
| **86** | If you remove a watched folder, new items that you add to that folder on disk will not be automatically added to Picasa. Are you sure you want to do this? |
| **87** | Confirm Remove Watched Folder |
| **100** | Setting Up Watched Folders |

A burkoló **mind a 84 hívójában** végigmérve **95 különböző azonosító**
fordul elő ténylegesen — és **a 86, a 87 és a 100 EGYIK SEM**. A
`stringres`-úton (`0x009ae560`, kulcs szerint) sem hivatkozik rájuk semmi:
a `string_xrefs`-ben a `HOTFOLDER` mintára **egyetlen** találat van, a
`Preferences\HotFolders` **registry-út** — nem a szöveg.

#### Amit ez kimond

1. **Nincs „Figyelt mappák beállítása" folyamatjelző** az OK után. A
   12. szakasz 3. pontja ezzel **tárgytalan**.
2. **Nincs megerősítés a figyelt mappa eltávolításakor.** A szöveg és a
   címe benne van a fordítási készletben, de a kód nem tölti be.
3. A fordítási táblában (`stringres-en-hu.tsv`) való jelenlét **nem
   bizonyítja a használatot** — az a fájl minden fordítható szöveget
   tartalmaz, a halottakat is.

> ⚠️ **Nálunk viszont MEGVAN** (`FolderManagerDialog.qml`,
> `removeWatchedConfirm`) — a #543 alapján építettük be. Ez tehát
> **TÖBB, mint az eredeti**. **Tudatos eltérésként rögzítve — ld.
> `docs/decisions/mappakezelo-eltavolitas-megerosito.md` (ADR-005,
> jegy #1175):** a döntés a megtartás, nem a paritás.

*Bizonyítottsági fok: **megerősített**. A negatív állítás nem
mintavételen alapul: a burkoló MINDEN hívóját (84 függvény, 150 hívás)
végigmértük, és a `stringres`-utat is ellenőriztük.*

## 6.2 iPhoto / Apple Photos — külön ág

A „Keresés mindig" ág a meghajtó-vizsgálat után **kétszer** végez
sztringegyezést a mappanévre: `"iPhoto Library"` (`0x007c2a92`) és
`"Apple Photos Library"` (`0x007c2bda`), és eltérő ágra megy
(`0x007c2f5b`), ami **másik listát** használ (`[dlg+0x270]` a `[+0x2a8]`
helyett). A támogatás két beállításhoz kötött:
`Preferences\iPhotoSupportEnabled` (`0x0047d0e0`) és
`Preferences\ApplePhotosSupportEnabled` (`0x0047d150`); a
könyvtár-felismerő (`0x0099bce0`) az `Originals` és `Masters` almappákat is
nézi.

---

## 7. OK, Mégse, Súgó

### 7.1 A változások CSAK OK-ra érvényesülnek

```asm
; a szétosztóban (0x007c27d0)
; --- OK ---
0x007c285f  mov byte ptr [ebx+0x2f0], 0   ; ← a „ne alkalmazd" jelző TÖRLÉSE
0x007c2866  call 0x7c6430                 ; közös lezáró
; --- Mégse ---
0x007c28c6  jne 0x7c2866                  ; ← EGYENESEN a lezáróra, a jelző MARAD
```

```asm
; a lezáró (0x007c6430)
0x007c646c  cmp byte ptr [edi+0x2f0], 0
0x007c6473  jne 0x7c6482                  ; ha a jelző áll → NEM alkalmaz
0x007c6476  call 0x7c4df0                 ; ← AZ ALKALMAZÁS
0x007c647b  mov byte ptr [edi+0x2f0], 1   ; kétszer ne fusson
```

**Vagyis: a fában és a rádiókon végzett módosítások a dialógus belső
delta-listáiban gyűlnek, és csak az OK írja ki őket; a Mégse eldobja.** Az
`Esc` a Mégsével azonos: az init (`0x007c0810`) a `cancel` gombra
`[+0x384] = 0x1b` (`VK_ESCAPE`) értéket állít (`0x007c0943`).

Az alkalmazó (`0x007c4df0`, 2611 bájt) menete: a listák összevetése, az
iPhoto/Apple Photos beállítások lekérdezése (`0x00987030`), a
listaműveletek (`0x00492e40`, `0x005088f0`), majd — ha kizárt mappákból
arcadatot kell törölni — a **`confirmfrexclude`** párbeszéd (`0x007c54d6`
→ `0x9bac20`), végül `0x007bfec0` háromszor és `0x005cef20`.

### 7.2 A Súgó a WEBRE megy

```asm
0x007c4d23  push "http://picasa.google.com/support/bin/answer.py?answer=11511"
0x007c4d77  push "&hl=%s"        ; + a felület nyelve
```

**A Súgó gomb a böngészőben nyitja meg a Google súgóoldalát**, nem helyi
szöveget mutat. *(A cikk ma már nem él — a PicasaPy-nak saját megoldást
kell adnia, de tudni kell, hogy az eredeti viselkedés ez volt.)*

---

## 8. A „Figyelt mappák" lista

A tulajdonos nagyított képernyőképén a lista teljes tartalma látszik
(nincs görgetősáv, tehát ez mind):

```
Videók
Képek\AI\
Képek\lake\
Képek\Picasa\
Képek\wallpapers\
C:\Users\attila.virag\Pictures\
```

Három szabály olvasható ki:

1. **Csak a KIFEJEZETTEN figyelt mappák szerepelnek** — a `Képek\Picasa\`
   ott van, a gyerekei (`Captured Videos`, `Kollázsok`, …) **nincsenek**,
   pedig a fában ők is a „Keresés mindig" ikont viselik (örökölt állapot,
   4.3).
2. **A megjelenítés vegyes**: ismert gyökér alatti mappák **relatív**
   alakban, záró `\`-sel (`Képek\AI\`), a többi **abszolút** útvonalként
   (`C:\Users\attila.virag\Pictures\`). A `Videók` záró `\` nélkül áll — ez
   a Windows-könyvtár (library) bejegyzés alakja.
3. **A lista tartalmazhat olyan mappát, ami a fában nem is látszik**: a
   `Videók` nem szerepel a fa gyökerei közt (Asztal / Képek / Dokumentumok
   / C:\ / P:\).

A tárolás helye a **registry**: `Preferences\HotFolders` (`0x00418ad0`,
1539 bájt).

*(Mellékesen: a `Képek\…` és a `C:\Users\…\Pictures\` egyszerre való
jelenléte pontosan a #1088-ban leírt eset — a `Képek` OneDrive-ra
átirányítva, a valódi `Pictures` külön.)*

---

## 9. Eredeti / nálunk — a teljes eltéréslista

`src/picasapy/app/qml/PicasaPy/FolderManagerDialog.qml` (322 sor) +
`FolderStatePanel.qml` + `FolderTreeItem.qml` + `FolderStateBadge.qml`.

| # | | eredeti | nálunk |
|---|---|---|---|
| 1 | kiinduló méret | **550×450** (`docbounds`) | 720×480 |
| 2 | minimális méret | **nincs** (megerősítve: mind a 4 ablakosztály átnézve) | ✅ **RENDBEN** — `minimumWidth: 0`, `minimumHeight: 0` (`FolderManagerDialog.qml:20–21`). *(A tábla korábbi `540`/`340` értéke ELAVULT.)* |
| 3 | osztás | **pontosan 50–50 %**, 4 px külső margóval | `Layout.fillWidth` mindkét oldalon (≈50 %), de 10 px margóval |
| 4 | „Mappalista" felirat a fa fölött | **van** (font14) | **nincs** |
| 5 | magyarázó szöveg helye | a **jobb hasáb** tetején, 232 px széles | a dialógus **teljes szélességében**, felül |
| 6 | magyarázó szöveg tartalma | az eredeti kétmondatos szöveg | saját, eltérő szöveg |
| 7 | süllyesztett csoportkeret | `decrect(softbevel/flatbevel)`, **fix 231×172** | `Rectangle { radius: 2 }` |
| 8 | **a rádiók sorrendje** | **Keresés egyszer → Eltávolítás → Keresés mindig** | **Keresés mindig → Keresés egyszer → Eltávolítás** ❌ |
| 9 | rádió-osztás | 33 px, gomb 24×24, felirat +29 px | ad hoc |
| 10 | alapértelmezés | `scan_once` benyomva | nincs kimondva |
| 11 | rádiónkénti **letiltás** | mindhárom külön engedélyezhető/tiltható | nincs |
| 12 | elválasztó vonal | van, **vízszintesen nyúlik** | nincs |
| 13 | arcfelismerés-kapcsoló letiltása | **kizárt SZÜLŐ esetén letiltva** | nincs (mindig kattintható) |
| 14 | kapcsoló-felirat váltása | `Face Detection On/Off` | ✔ megvan |
| 15 | ikonok | zöld pipa / **piros** X / **kék** C + két arc-jelvény | saját rajz (`FolderStateBadge`) |
| 16 | fa gyökerei | Asztal, Képek, Dokumentumok, **minden meghajtó** | `rootPath: "/"` — egyetlen gyökér |
| 17 | rendszermappa-ikonok | külön ikon Asztal/Képek/Dokumentumok/meghajtó | egységes mappaikon |
| 18 | **OK/Mégse szemantika** | **a változás csak OK-ra érvényesül, a Mégse eldobja** | **azonnal alkalmaz** (`applyState` → controller) ❌ |
| 19 | Esc | = Mégse (`[+0x384] = VK_ESCAPE`) | ellenőrizendő |
| 20 | Súgó | **böngésző**, `…answer=11511&hl=<nyelv>` | helyi súgóablak |
| 21 | átméretező fogantyú | látható 20×20 elem a jobb-alsó sarokban, `SC_SIZE` | nincs (natív ablakkeret) |
| 22 | gombsor | OK ‹ Mégse ‹ Súgó, 98×28, jobb-alsó | ✔ ugyanez a sorrend, más méret |
| 22/b | **belepesi pontok** | KET menu: Fajl -> Mappa hozzaadasa a Picasahoz..., es Eszkozok -> Mappakezelo..., **ugyanaz a parancs** (`0x9caa`) | csak az Eszkozok menu; a Fajl menu tetele **halott `placeholder`** (`PicasaMenuBar.qml:158`) |
| 22/c | **OK utani frissites** | a keresosav/nezet frissitese (`0x0065b840`) | nincs kimondva |
| 23 | extra gombok | **nincsenek** | „Add folder…", „Adopt Picasa folders…" |
| 24 | Figyelt mappák lista | csak a kifejezetten figyeltek, vegyes relatív/abszolút alak | teljes útvonalak |
| 25 | figyelmeztetés: teljes meghajtó | ✔ + **nemre az „Eltávolítás" tétel lesz aktív** | ✔ figyelmeztet, a visszaállás nincs |
| 26 | figyelmeztetés: figyelt mappa eltávolítása | ✔ saját címmel | ✔ megvan |
| 27 | `confirmfrexclude` | **OK-kor**, ha kizárt mappa arcadata törlődne | a kapcsolónál kérdez, nem OK-kor |

### 9/b Amit a 2026-08-21-i élő összevetés MÉRT (a tulajdonos képernyőképe + gépi mérés)

A tulajdonos egymás mellett futtatta a kettőt. Ez a szakasz a fenti
listát **mérésre váltja**, mert több tétel időközben javult, más viszont
csak a valódi használatban derült ki. Jegy: **#1200**.

| # | tétel | eredeti | nálunk — MÉRVE | állapot |
|---|---|---|---|---|
| A | **a fa kinyitható-e** | igen, rekurzív fájlrendszer-fa | ❌ **NEM** — a nyílra kattintás nem nyit ki semmit, csak kijelöl | **P1 hiba** |
| B | állapot-ikon minden soron | **mindig** (3 közül 1) | ❌ „nincs állapot" esetben **semmi**; a 4 látható sor ikon nélkül | **P1 hiba** |
| C | az ikon HELYE a sorban | a **név ELŐTT**, a mappaikon előtt | ❌ a név **UTÁN** | hiba |
| D | rádiósorok ikonjai | mindegyik mellett a saját ikonja (`icon_once`/`_exclude`/`_always`) | ❌ nincs ikon, a feliratok **középre** igazítva | hiba |
| E | gombsor | **3 gomb** (OK/Mégse/Súgó), 98×28, jobbra zárva | ❌ **5 gomb** — a sor igénye **556 px** angolul, **618 px** magyarul, az ablak **550 px** → a Súgó kilóg | **P1 hiba** |
| F | bal felirat | „Folder List" / „Mappalista" | ❌ „Mappák" | hiba |
| G | gyökerek neve | honosított (Asztal / Képek / Dokumentumok) | ❌ **angolul** beégetve (`Desktop`/`Pictures`/`Documents`) magyar felületen | hiba |
| H | „Figyelt mappák" lista alakja | rövid, relatív útvonalak (`Képek\AI\`) | ❌ teljes útvonalak, középen `…`-tal csonkolva | eltérés |
| I | ablakméret | 550×450 | ✔ **550×450** | rendben |
| J | rádiók sorrendje | egyszer → eltávolítás → mindig | ✔ ugyanez | rendben (javult) |
| K | Súgó gomb léte | van | ✔ van (csak kilóg, ld. E) | rendben |

**Mérési módszer** az A és E soroknál (mindkettő gépi, nem szemre):

- **A:** valódi `QMouseEvent` a nyíl közepére a Mappakezelő ablakában →
  `expanded` **`false`** maradt, viszont a `selectedPath` beállt. A
  sor-szintű `MouseArea` (`folderTreeRowMouse:*`) a `Rectangle`-ben
  **később** van deklarálva, mint a nyíl `MouseArea`-ja, tehát
  találat-vizsgálatnál **fölötte van** és elnyeli a kattintást.
- **E:** a betöltött ablakban a gombsor `implicitWidth` = **556 px**
  (angol feliratokkal), a Súgó gomb jobb széle **556** — az 550 px-es
  ablakon **kívül**. Magyar feliratokkal, ugyanazzal a betűvel mérve
  `QFontMetricsF`-fel: **617,7 px**, azaz **67,7 px túllógás**.

> ⚠️ **Miért nem fogta meg ezt egyetlen teszt sem?** A
> `tests/app/test_qml_folder_manager.py` a kinyitást a
> `toggleExpand()` **közvetlen hívásával** végzi
> (`_invoke(row_item, "toggleExpand")`), sosem kattint. A függvény
> hibátlan — a **vezérlő** nem érhető el. A zöld készlet tehát pontosan
> azt nem mérte, ami elromlott. Ez a `docs/`-ban már rögzített
> „őr-teszt foga nélkül" minta újabb esete.

---

## 10. A „teljes meghajtó" feltétel — pontosan

`0x009a3d60(útvonal-objektum /*edx*/)`, 69 bájt, teljes egészében:

```c
rest = [obj + 0x410];        // a gyökér UTÁNI útvonalrész
name = [obj + 0x618];        // az utolsó (fájl/mappa-)komponens
if (rest üres  ||  rest kezdete == "\\")   // a minta a 0x00c80910-en: "\"
    return (name üres);      // → IGAZ: ez egy teljes meghajtó
return HAMIS;
```

Vagyis a figyelmeztetés akkor jön elő, ha a kijelölés a **meghajtó
gyökere** (`C:\`, `C:`), és nem jön elő semmilyen almappára.

*Bizonyítottsági fok: **megerősített** (a függvény minden utasítása).*

---

## 10/b Mi AKTIVÁLJA, és MIT INDÍT EL (2026-08-21)

*(A lap első kiadásából ez a két kérdés hiányzott — a tulajdonos vette
észre. A kutatói skill 2/b szakasza azóta kötelezővé teszi.)*

### 10/b.1 A belépési pontok — EGY parancs, KÉT menü

Az `ID_TOOLS_INCLUDEEXCLUDEFOLDERS` azonosító a menüsáv-építőben
(`0x00559150`) **kétszer** szerepel, két külön menüben, **ugyanazzal a
parancsazonosítóval**:

| menü | felirat | rekord | azonosító |
|---|---|---|---|
| **Fájl** | „Add Folder to Picasa…" (`eMenuFile::ID_TOOLS_INCLUDEEXCLUDEFOLDERS`, `0x005591b7`) | `0xd6d988` | **`0x9caa`** (`0xd6d992`) |
| **Eszközök** | „&Folder Manager…" (`eMenuTools::ID_TOOLS_INCLUDEEXCLUDEFOLDERS`, `0x0055c54c`) | `0xd6e850` | **`0x9caa`** (`0xd6e85a`) |

A parancs útja: a szétosztó (`0x005cb990`) a `0x9caa`-t a 104. indexen a
`0x005cbdd1`-re viszi:

```asm
0x005cbdd1  push edi          ; a 2. argumentum: a mod-jelzo
0x005cbdd2  push ebx          ; a CThumbUI
0x005cbdd3  call 0x5ce590
```

és a `0x005ce590(objektum, mód)` **a jelző alapján ágazik**:

```asm
0x005ce597  mov ebx, [esp+0xb90]   ; a MOD (a 2. argumentum)
0x005ce5a9  test bl, bl
0x005ce5b4  je   0x5ce679           ; mod == 0 -> A MAPPAKEZELO MEGNYITASA
0x005ce5ba  mov eax, [ebp+0xeb0]    ; mod != 0 -> a bal panel kijelolt mappaja
```

A `0x005ce590` sztringkészlete elárulja, hogy a **másik** ág egy egészen
külön folyamat: *„Do you want to remove the folder %s and its
subfolders?"*, `CThumbUI::ManageAlbum`, `CThumbUI:ManageAlbumConfirm`,
`CThumbUI:ManageAlbumYesButton`, `Remove Folder`, `\Originals`,
`\Modified` — vagyis **mappa (és almappái) eltávolítása a Picasából**,
megerősítéssel, a szerkesztési biztonsági másolatok mappáit is figyelembe
véve.

> **Két, egymástól független tanulság:**
>
> 1. **Ugyanaz a dialógus két menüből nyílik**, két különböző felirattal —
>    a „Mappa hozzáadása a Picasához…" nem külön funkció, hanem **ugyanez
>    az ablak**.
> 2. **A parancsazonosító nem egyenlő a funkcióval**: a `0x9caa` egy
>    második, mód-jelzős ágon egy teljesen más folyamatot is kiszolgál.

*(Az első indítás („beállítás-varázsló") belépési útját NEM követtük —
ld. 12.)*

### 10/b.2 Amit a dialógus KIFELÉ indít

| mikor | mit indít |
|---|---|
| megnyitáskor | a `[dlg+0x414]` **kritikus szakasszal védett** segédobjektum felállítása; ugyanezt használja a fa-sorból útvonalat képző `0x007bfcb0` |
| „Keresés mindig" teljes meghajtóra | **Igen/Nem párbeszéd** (`CFolderMgrDialog::warning`, `0x009bac20`, típus 1) |
| figyelt mappa eltávolítása | **megerősítő párbeszéd** (`IDS_HOTFOLDER_CONFIRM`, saját címmel) |
| **Súgó** | **külső böngésző** — `answer.py?answer=11511&hl=<nyelv>` |
| **OK** | a lezáró (`0x007c6430`) **először leállítja** a `[dlg+0x414]` objektumot, majd `0x007c4df0`: `confirmfrexclude` párbeszéd (ha kizárt mappa arcadata törlődne) → `0x005cef20` (a **figyelt mappák** összevetése a `[lib+0x364]` listán) → `0x007bfec0` **háromszor** → `0x005088f0` → **`0x0065b840`: a keresősáv/nézet frissítése** |
| **Mégse / Esc** | ugyanaz a lezáró, de az alkalmazás **kimarad** (7.1) |

*Bizonyítottsági fok: **megerősített** a belépési pontokra (a
menüsáv-építő két rekordja, azonos azonosítóval), a parancs útjára és a
mód-jelzős elágazásra · **erős** a kifelé indított műveletek listájára (a
hívások megvannak, néhány célfüggvény szerepe csak a sztringjeiből
ismert).*

---

## 11. Mit CSINÁL a három állapot — a HÁROM lista-fájl

A dialógus felülete önmagában semmit nem mond arról, mi történik a
képekkel. A válasz három egyszerű szövegfájlban van, és **mind a három
megvan valódi mintával** a repóban (`research/testdata/`).

### 11.1 A fájlok

| fájl | hely | mit tárol | író | olvasó |
|---|---|---|---|---|
| **`watchedfolders.txt`** | `Picasa2Albums/` | a **figyelt** mappák | `0x004f5960` | `0x004f5a30` |
| **`frexcludefolders.txt`** | `Picasa2Albums/` | az **arcfelismerésből kizárt** mappák | `0x004f5d90` | `0x004f5e60` |
| **`scanlist.txt`** | `Picasa2/db3/` | a beolvasási lista, **három szakaszban** | `0x004f61c0` | `0x004f6380` |

Mindhárom írás `fopen(…, "w")` + soronkénti `fprintf` — **teljes
újraírás**, nem hozzáfűzés. Az útvonalak **abszolútak, záró `\`-sel**.

### 11.2 A `watchedfolders.txt` és a `frexcludefolders.txt`

Formátum: soronként `"%s\n"` (a formátumsztring a `0x00c7ebe8`-on),
előtag nélkül. Valódi minta a repóból:

```
# research/testdata/Picasa2Albums/watchedfolders.txt
C:\Users\Sancho\Synology\My Pictures\
L:\backup\Xiaomi14T\
L:\backup\Xiaomi14T\DCIM\Camera\

# research/testdata/Picasa2Albums/frexcludefolders.txt
C:\Users\Sancho\Pictures\Picasa\
C:\Users\Sancho\Pictures\
C:\Users\Sancho\Synology\My Pictures\
L:\backup\Xiaomi14T\
```

> **Ez igazolja a 8. szakasz 2. pontját is:** a fájl **abszolút**
> útvonalakat tárol, a „Figyelt mappák" listában látszó rövidített alak
> (`Képek\AI\`) tehát **kizárólag megjelenítési** rövidítés.

### 11.3 A `scanlist.txt` — három szakasz, három formátum

Az író (`0x004f61c0`) egymás után **három** ciklust ír ki, három **külön
formátumsztringgel**:

| sorrend | forrásmező | formátum | cím |
|---|---|---|---|
| 1. | `[lib+0x2e0]`, darab `[+0x2e4]>>1`, kezdet `[+0x2e8]` | `"%s\n"` (`0x00c7ebe8`) | `0x004f6264` |
| 2. | `[lib+0x288]`, darab `[+0x28c]>>1` | **`"-%s\n"`** (`0x00c865ac`) | `0x004f62a4` |
| 3. | `[lib+0x280]`, darab `[+0x284]>>1` | **`"+%s\n"`** (`0x00c865b4`) | `0x004f62e4` |

A parszer (`0x004f6380`) ugyanezt olvassa vissza:
`cmp byte ptr [eax], 0x2d` (`'-'`, `0x004f646d`) → a `[lib+0x288]` listába
(`0x004f649f`); `cmp byte ptr [eax], 0x2b` (`'+'`, `0x004f6648`) → a
`[lib+0x280]`-ba (`0x004f667a`).

Valódi minta (`research/testdata/Picasa2/db3/scanlist.txt`, 372 sor):
**368 előtag nélküli** mappa, **0 darab `-`**, és négy `+` sor a végén:

```
C:\Users\Sancho\Synology\My Pictures\2011\2011-06-03..10 Vitorlázás (O550)\
…
+C:\
+L:\
+E:\
+D:\
```

A fájl írása **kritikus szakasszal védett** és **újrabelépő**
(`0x004f61f3` `GetCurrentThreadId` + számláló) — több szál is hívhatja.

### 11.4 Amit ez KIMOND és amit NEM

**Kimondja:** a Mappakezelő állapotai nem a felületen élnek, hanem ebben a
három fájlban; a beolvasási lista **gyökér-alapú befoglalást/kizárást**
(`+`/`−`) és **konkrét, már ismert mappákat** (előtag nélkül) egyaránt
tárol; a figyelés és az arcfelismerés-kizárás **külön-külön** fájl.

**Nem mondja ki:** hogy a három rádiógomb közül **melyik pontosan melyik
szakaszba ír**. A megfeleltetés kézenfekvő (Keresés mindig →
`watchedfolders.txt`; Eltávolítás → `−` sor; Keresés egyszer → `+` sor
vagy előtag nélküli bejegyzés), de **ez következtetés, nem mérés** — a
kiíró és a rádió közti utat (`0x007c4df0` → `0x005cef20` / `0x007bfec0` /
`0x005088f0`) nem követtük végig utasításszinten. Ld. 12.

*Bizonyítottsági fok: **megerősített** a fájlnevekre, a helyükre, a három
formátumra, a parszer előtag-vizsgálatára és a valódi mintaadatra ·
**feltételes** a rádió → szakasz megfeleltetésre.*

---

### 11.5 Mi történik a MÁR BEOLVASOTT képekkel az „Eltávolítás" után (M2)

**A képek NEM törlődnek.** A mappa adatbázis-rekordja egy **sírkő-tokent**
kap: **`]album:removed`**.

A rutin a `0x004b9200` (254 bájt), amit **két** helyről hívnak: az
OK-alkalmazó (`0x005cef20`) és a Mappakezelőt megnyitó / mappát eltávolító
`0x005ce590`.

```c
// 0x004b9200(this /*eax*/, utvonallista /*[esp+8]*/)
// — kritikus szakasszal vedett es UJRABELEPO (GetCurrentThreadId + szamlalo,
//   ugyanaz a minta, mint a scanlist.txt-nel)
for (i = 0; i < lista.darab; ++i) {
    ha = 0x441cd0(this->db /*[esi+0xc4]*/, &lista[i], &id);  // 0x004b926a
    if (ha != 0) continue;                                   // nincs ilyen mappa
    [db+0x48]->vt[0](id, 0);                                 // 0x004b9288
    0x00444990(db, id, "]album:removed");                    // 0x004b9297
}
```

A `0x00444990` (1343 b) a **token-hozzáadó**: ugyanaz a rutin, amivel egy
**album létrejön** (`0x0055d120`-ból is hívják) — vagyis az eltávolítás a
Picasa saját album-token-rendszerét használja, nem külön törlési utat.

#### Élő adat a repóból

`research/testdata/Picasa2/db3/albumdata_token.pmp` (93 958 bájt) — a
fotó→token tábla valódi tartalma:

| token | darab |
|---|---:|
| `]album:<32 hexa uid>` | **2346** |
| `]history:email`, `]history:upload` | 2 |
| `]screensaver`, `]search`, `]star`, `]updated`, `]unknownface` | 1–1 |
| **`]album:removed`** | **0** |

**A mechanizmus tehát igazolt** (a `]`-tokenek valóban a `*.pmp`
táblában élnek), a konkrét `]album:removed` viszont **ebben a mintában
nem fordul elő** — ez a felhasználó nem távolított el mappát.
*(Ugyanez a tábla azt is megmutatja, hogy az `]history:export` sem
szerepel benne, csak az `]history:email` és `]history:upload` — ld.
`export-parbeszed.md` 9/7.)*

> **Amit ez a PicasaPy-nak jelent:** az „Eltávolítás a Picasából" nem
> destruktív. Nálunk a `controller.removeFolder(path)` **tényleges
> viselkedését** ehhez kell mérni: a képeknek az indexben kell
> maradniuk, csak a mappa kap egy „eltávolított" jelölést. Ha ma
> törlünk, az adatvesztés a felhasználó szemszögéből (a címkék, arcok,
> szerkesztések a rekordhoz tartoznak).

*Bizonyítottsági fok: **megerősített** a mechanizmusra (a rutin minden
utasítása, a két hívó, a token-hozzáadó azonossága az albumkészítővel) ·
**megerősített** arra, hogy a `]`-tokenek a `*.pmp` táblában élnek (valódi
adat) · **nincs mintánk** magára a `]album:removed`-ra.*

---

## 12. Ami NYITVA marad

*(Az iPhoto / Apple Photos ág **szándékosan kívül van a hatókörön** —
tulajdonosi döntés, 2026-08-21. A 6.2 tájékoztatásul marad; nem kérdés.)*

**A lap a FELÜLET viselkedését teljesen leírja. A KÖNYVTÁR-oldali hatás
az alábbi pontokon nincs utasításszinten végigkövetve** *(a 2., 3., 5., 7.
és 8. pont azóta LEZÁRULT — lásd 11.5, 6.3 és 13.)* — egyik sem blokkolja a felület
megépítését, de mindegyikhez döntés kell:

1. ~~**A rádió → lista-szakasz megfeleltetés.**~~ — ✅ **LEZÁRVA
   2026-08-24 (17.)**: az OK-út végigkövetve. `0x007c4df0` → `0x005cef20`,
   ami `watchedfolders.txt` + `]album:removed` sírkő + `frexcludefolders.txt`
   sorrendben ír; a `scanlist.txt` innen **NEM** íródik. A 12.1 saját
   függvény-felsorolása **helyesbítve**: a `0x007bfec0` zárolt listaművelet,
   a `0x005088f0` listaművelet — egyik sem fájlkiíró. Jegy: **#1334**.
2. ~~Mi történik a már beolvasott képekkel az „Eltávolítás" után?~~ —
   **LEZÁRVA** (11.5): nem törlődnek, a mappa `]album:removed` sírkő-tokent
   kap (`0x004b9200`).
3. ~~Az OK utáni újraolvasás / `IDS_SETTING_UP_WATCHED`~~ — **LEZÁRVA,
   NEGATÍV** (6.3): a sztringet a program soha nem tölti be; nincs ilyen
   folyamatjelző.
4. ~~**Az ELSŐ INDÍTÁS belépési útja.**~~ — ✅ **LEZÁRVA, NEGATÍV
   2026-08-24 (18.)**: nincs külön első-indítási út. A megnyitó
   (`0x005ce590`) **pontosan két** hívóval bír, mindkettő a főablak
   parancs-diszpécsere — és a **mód-jelzőjük különbözik** (1 vs 0).
5. ~~**A fa feltöltési szabályai**~~ — **LEZÁRVA** (13.2, 13.4, 13.6):
   **lusta betöltés háttérszálon** (`SetEvent`, `0x007bf378`); a fa a
   rejtett/rendszermappákra **nem szűr** (a kizárás a beolvasóé); a
   **leválasztott hálózati meghajtó MEGJELENIK**, mert a hálózati ágat a
   felsoroló `checkFilesystem=0`-val hívja (`0x007c9fee`).
6. ~~**A „Figyelt mappák" lista interaktivitása**~~ — **LEZÁRVA** (14.):
   **kattintható** (`lb_selected` külön ága, `0x007c5a5f`), a kattintás
   **átállítja a három rádiót és az arcfelismerés-sort** (a közös
   `0x007c60d0`), és a **fa odaugrik** — ha kell, lustán ki is nyílik
   (`0x007bf130` + `SetEvent [dlg+0x550]`). Fordítva a fa kattintása
   **törli a jobb lista kijelölését** (`0x007c5b61`). **Rendezés nincs**:
   a végére fűz (`0x007c2f5b`), a sorrend a betöltési sorrend.

7. ~~**A `0x007bf210` (468 bájt) tartalma**~~ — **LEZÁRVA** (13.2): igen,
   ez a **kinyitás/becsukás kapcsoló**, és ez a lusta betöltés indítója.
8. ~~**Még nem nyitott függvények**~~ — **LEZÁRVA** (13.1, 13.3, 13.5):
   RTTI-ből mind a négy megnevezve — `0x007c6700` = a **bal fa
   sorrajzolója** (`TreeListDraw`), `0x007c6ba0` = a **jobb lista
   sorrajzolója** (`WatchedListDraw`), `0x007c6d30` = a
   **csomópont-hozzáadó**, `0x007bf680` = **csomópont-rekurzió** (nem
   gyökér-felsorolás: a gyökereket a `0x007c9e70` szál adja).
   **HELYESBÍTÉS:** a korábbi „valószínűleg a fa gyökereinek felsorolása"
   feltevés a `0x007bf680`-ra **MEGDŐLT** — a függvényben nincs egyetlen
   fájlrendszer-hívás sem.

Ezen felül **erős, de nem megerősített** két állítás:

- **A minimális méret hiánya** (2.3) — egyetlen ablakosztály
  átvizsgálásán alapuló negatív állítás.
- **A meghajtó-figyelmeztetésre adott „nem" hatása** (6.1) — az utasítások
  egyértelműek, de az őket megelőző ágat nem követtük végig.

*(A kör három korábbi nyitott pontot lezárt: „melyik lista melyik
állapoté" → 5.2, „mi a teljes meghajtó feltétele" → 10., és „hol tárolódik
az állapot" → 12.)*

---

## 13. A fa FELTÖLTÉSE — lusta betöltés, gyökerek, kizárások (2026-08-21)

Ez a szakasz a 12. lista 5., 7. és 8. pontját zárja le. Bizalmi fok:
**megerősített** (utasításszintű bizonyíték minden állításhoz), kivéve ahol
külön jelezve.

### 13.1 A dialógus osztályai — RTTI-ből

Az `rtti` tábla négy belső osztályt ad meg, ezzel a `0x007be…`–`0x007ca…`
tartomány szerepe egy csapásra kiderül:

| RTTI-név | vtable | hozzá tartozó függvények |
|---|---|---|
| `CFolderMgrDialog::CDirArray` | `0x00cb8300` | `0x007bece0`, `0x007becf0`, `0x007bfdf0`, `0x007c9e70` |
| `CFolderMgrDialog::TreeListDraw` | `0x00cb82b8` | `0x007c6660`, **`0x007c6700`** |
| `CFolderMgrDialog::WatchedListDraw` | `0x00cb82c8` | `0x007c6660`, **`0x007c6ba0`** |
| `CFolderMgrDialog::ytVolumeIsExternalFS` | `0x00cb82d8` | **`0x007c84c0`** |

Ezzel a 12.8 „meg nem nyitott függvények" listája **név szerint** megvan:
`0x007c6700` = a **bal fa sorrajzolója**, `0x007c6ba0` = a **jobb „Figyelt
mappák" lista sorrajzolója**, `0x007c6d30` = a **fa-csomópont hozzáadó**
(lásd 13.3), `0x007bf680` = a **csomópont-rekurzió** (13.5).

### 13.2 LUSTA BETÖLTÉS — bizonyítva (a 12.7 lezárása)

A `0x007bf210` (468 b) a **kinyitás/becsukás kapcsoló**. A `lb_predouble`
ág (4.5) ide fut be. Az adatszerkezet a `CDirArray`-ben:

| eltolás | tartalom |
|---|---|
| `[obj+0x140]` | látható sor → elem-index tábla |
| `[obj+0x108]` | elem-index → csomópont-index tábla |
| `[obj+0x110]` | csomópont-tömb, **20 bájt/csomópont** (`lea ecx,[eax+eax*4]` majd `*4`) |
| `[obj+0x118]` | csomópontonkénti **„kinyitva" bájt** (4 bájt lépésköz) |
| `[obj+0x13c]` | **a háttérszál ébresztő eseménye** (Win32 event handle) |
| `[obj+0x154]` | újraszámolt elrendezés-jelző |

A döntés `0x007bf2ee`-nél:

```asm
0x007bf2ee  cmp   byte ptr [edx + eax*4], 0   ; kinyitva?
0x007bf2f5  je    0x7bf36a                    ; NEM -> KINYITÁS
0x007bf2f7  mov   dword ptr [eax], 0          ; IGEN -> BECSUKÁS
0x007bf300  call  0x7bed10                    ; csak újrarendezés (szinkron)
```

A **kinyitás** ága a lényeg:

```asm
0x007bf36a  mov   dword ptr [eax], ebx        ; „kinyitva" = 1
0x007bf36c  test  byte ptr [ecx + 0x10], bl   ; a csomópont +0x10 bitje:
                                              ;   „a gyerekek már be vannak töltve?"
0x007bf36f  jne   0x7bf380                    ; IGEN -> 0x7bed10, szinkron újrarendezés
0x007bf371  mov   eax, dword ptr [esi + 0x13c]
0x007bf378  call  dword ptr [0xc4031c]        ; SetEvent  <-- NEM: felébreszti a szálat
```

**Tehát:** a Picasa **lustán tölt**. Egy csomópont gyerekeit csak az első
kinyitáskor sorolja fel, és azt is **háttérszálon**: a felület nem áll meg,
csak `SetEvent`-et küld. A már betöltött csomópont ki-be csukása
**szinkron és azonnali** — nincs újraolvasás.

A becsukás **nem üríti** a gyerek-listát (a `+0x10` bit marad), tehát a
második kinyitás is azonnali.

### 13.3 A háttérszál: `0x007c9e70`

A szál ciklusa a függvény végén látszik:
`WaitForMultipleObjects` (`0x007ca827`) → `ResetEvent` (`0x007ca878`) →
újra elölről. Ez a `0x007bf210` `SetEvent`-jének párja.

Ébredés után a szál **három hívással** kéri le a meghajtókat a közös
meghajtó-felsorolótól (`0x006dabf0`), majd három rögzített gyökeret ad a
fához a `0x007c6d30` csomópont-hozzáadóval.

**A gyökerek sorrendje, kódból:**

| sorrend | feloldó függvény | shell-kulcs | a képernyőképen |
|---|---|---|---|
| 1. | `0x00996b90` | `Desktop` | **Asztal** |
| 2. | `0x009966a0` | `My Pictures` | **Képek** |
| 3. | `0x00996230` | `Personal` | **Dokumentumok** |
| 4+ | `0x006dabf0` | meghajtók | **C:\\**, **P:\\** |

*(A `0x009966a0` egyszer korábban is meghívódik, `0x007ca006`-nál, egyetlen
paraméterrel — az egy előkészítő útvonal-lekérés, nem csomópont-hozzáadás.
A csomópont-hozzáadások sorrendje `0x007ca02a`, `0x007ca061`, `0x007ca098`.)*

Ez **pontosan egyezik** a felhasználó képernyőképével
(`referencia/mappakezelo/mappakezelo-nagyitott.png`): Asztal → Képek →
Dokumentumok → C:\\ → P:\\.

### 13.4 MEGHAJTÓK — a leválasztott hálózati meghajtó esete (a 12.5 harmadik fele)

A közös felsoroló a **`0x006dabf0`** (1092 b). Szignatúrája a hívási
helyekből egyértelmű (`push` sorrend jobbról balra):

```c
void EnumDrives(Container* out, int driveType, bool checkFilesystem);
```

A törzs egy **betűciklus**:

```asm
0x006dac13  call  GetLogicalDrives          ; bitmaszk
0x006dac1d  mov   al, 0x43                  ; 'C' -- itt kezd
0x006dac1f  mov   dword [esp+0x28], 4       ; a C: bitje
   ...
0x006db007  shl   dword [esp+0x28], 1       ; következő bit
0x006db00b  add   al, 1                     ; következő betű
0x006db00d  cmp   al, 0x5a                  ; 'Z'
0x006db013  jle   0x6dac2b                  ; ciklus
```

**Az `A:` és a `B:` (flopi) soha nem kerül a listába** — a ciklus a `C:`-n
indul.

Meghajtónként:

1. `GetDriveTypeA("X:\")` (`0x006dace3`) — ha **nem egyezik** a kért
   típussal (`0x006dace9` `cmp`), a meghajtó kimarad.
2. Ha a `checkFilesystem` paraméter igaz (`0x006dacf6`):
   `GetVolumeInformationA` (`0x006dad30`). **Ha ez HIBÁVAL tér vissza, a
   meghajtó kimarad** (`0x006dad38 je`).
3. A fájlrendszer nevét háromhoz hasonlítja (`0x006dad42`–`0x006dad7e`):
   **`FAT`, `FAT32`, `NTFS`**. Ami nem ezek egyike, **kimarad**.

A három hívás a Mappakezelő szálában:

| hívás | típus | `checkFilesystem` | jelentés |
|---|---|---|---|
| `0x007c9ec0` | **3** = `DRIVE_FIXED` | **1** | belső lemezek, fájlrendszer-ellenőrzéssel |
| `0x007c9fee` | **4** = `DRIVE_REMOTE` | **0** | **hálózati meghajtók, ellenőrzés NÉLKÜL** |
| `0x007c9ffc` | **2** = `DRIVE_REMOVABLE` | **1** | cserélhető, fájlrendszer-ellenőrzéssel |

**Ez válaszolja meg a leválasztott hálózati meghajtó kérdését:** a
hálózati ágon a Picasa **szándékosan kihagyja** a
`GetVolumeInformation`-t, ezért egy **leválasztott, de leképezett hálózati
meghajtó is megjelenik a fában**. (Ha ellenőrizné, a hívás hibázna, és a
meghajtó eltűnne — a többi ág pont így viselkedik.) A képernyőképen a
`P:\` hálózati ikonnal szerepel.

**Következmény a belső lemezekre:** egy **exFAT** formázású lemez a
`FAT`/`FAT32`/`NTFS` hármas miatt **nem** kerül a fába. Ez a Picasa
korából származó korlát; nálunk nem kell reprodukálni (lásd 13.7).

### 13.5 A `ytVolumeIsExternalFS` predikátum — és miért NEM ellentmondás a neve

> **HELYESBÍTÉS (2026-08-21, M10).** Ez a szakasz korábban azt írta, hogy a
> mért viselkedés (`fs == "NTFS"`) „ellentétesnek hangzik" az osztály
> nevével, és hogy a hívási oldal ismeretlen. **Mindkettő megoldódott** —
> és a válasz egyik része sem szemantikai, hanem **fordítói**.

#### 13.5/a Az osztálycsalád

Az RTTI szerint a `CFolderMgrDialog::ytVolumeIsExternalFS` öröklődési
lánca (bázisosztály-tömb, `0x00d0e0a8`, 7 elem):

```
CFolderMgrDialog::ytVolumeIsExternalFS
  : ytVolumeInfo
      : ytBaseThread : ytSafe : ytBase : ytCriticalBase, IShouldExit
```

A `ytVolumeInfo` **kilencrekeszes** vtable-t definiál; a 0–7. rekesz
öröklött, a **8. rekesz** az osztály saját, **tisztán virtuális**
predikátuma (a bázis 8. rekesze `0x00c07709` = `_purecall`).

Négy leszármazott van, mind ugyanazzal a 0–7 előtaggal:

| osztály | vtable | 8. rekesz | mit vizsgál |
|---|---|---|---|
| `ytVolumeInfo` (bázis) | `0x00c835e0` | `0x00c07709` | `_purecall` |
| `ytVolumeIsNetwork` | `0x00c86d80` | `0x0099c1a0` | `GetDriveTypeA("<betű>:\") == 4` (**DRIVE_REMOTE**) |
| `ytVolumeIsGDrive` | `0x00c83608` | `0x004a01d0` | `fs == "GREDIR"` **vagy** a kötetnév `"googlewebdrive"`-val kezdődik |
| `ytVolumeIsNTFS` | `0x00c86da8` | **`0x007c84c0`** | `fs == "NTFS"` |
| `CFolderMgrDialog::ytVolumeIsExternalFS` | `0x00cb82d8` | **`0x007c84c0`** | *ugyanaz a cím* |

**A rejtély megoldása:** a `ytVolumeIsNTFS` és a
`CFolderMgrDialog::ytVolumeIsExternalFS` 8. rekesze **ugyanarra a címre
mutat**, mert a két függvény lefordított törzse **bájtra azonos**, és a
szerkesztő összevonta őket (MSVC `/OPT:ICF`, azonos COMDAT-összevonás).
A cím tehát **nem bizonyíték** arra, melyik osztály szemantikájáról van
szó — de mivel a törzsek azonosak, a **viselkedés egyértelmű**.

#### 13.5/b A predikátum szignatúrája — a testvérekből levezetve

```c
bool ytVolumeInfo::operator()(ytString* kotetNev /* [esp+4] */,
                              const char* fsNev  /* [esp+8] */);
```

A `ytVolumeIsGDrive` **mindkét** paramétert használja (`0x004a01d6` a
`fsNev`-re, `0x004a01e6` a `kotetNev`-re), a `ytVolumeIsNetwork` csak az
elsőt, a `ytVolumeIsNTFS` csak a másodikat. Ez rögzíti a sorrendet.

A `0x007c84c0` teljes törzse:

```asm
0x007c84c0  mov   eax, dword ptr [esp + 8]   ; fsNev
0x007c84c4  push  0xc86410          ; "NTFS"
0x007c84c9  push  eax
0x007c84ca  call  0xbf697a          ; _stricmp (ld. picasa-program-resources 3.1.2)
0x007c84d2  test  eax, eax
0x007c84d4  sete  al                ; al = (fsNev == "NTFS")
```

#### 13.5/c A Mappakezelőben a példány HASZNÁLATLAN

A `CDirArray` konstruktora (`0x007be9c0`, hívó: `0x007c0130`) a
`+0x84`-es beágyazott mezőbe építi:

```asm
0x007bea10  lea   edi, [esi + 0x84]
0x007bea21  call  0x49fff0          ; ytVolumeInfo konstruktor
0x007bea26  mov   dword ptr [edi], 0xcb82d8   ; a vtable felülírása
```

és a destruktor (`0x007bead0`) bontja le:

```asm
0x007bec6c  lea   eax, [esi + 0x84]
0x007bec78  call  0x4a0160          ; ytVolumeInfo destruktor
```

**Ezen a kettőn kívül a `0x007b0000`–`0x007d0000` tartományban SEHOL nincs
hivatkozás a `+0x84`-es mezőre** — sem 8. rekeszes virtuális hívás, sem
`lea`+`push` (átadás máshová). A bázis konstruktora (`0x0049fff0`, 360 b)
**semmilyen globális nyilvántartásba nem regisztrálja** magát (nincs
`mov dword ptr [0x…]` a törzsében).

**Következtetés:** a Mappakezelő megépíti és lebontja a predikátumot, de
**soha nem hívja meg**. Halott tag — feltehetően egy korábbi, elhagyott
„külső fájlrendszer" ágnak a maradéka.

**Bizalmi fok: erős.** A negatív állítás egy teljes tartomány-átvizsgáláson
alapul (minden `[reg+0x84]` operandus a Mappakezelő függvényeiben), nem
mintavételen. Amit NEM zár ki: ha a példányt egy *más* eltolással
(pl. a dialógusból `dlg+0x498`-ként) érné el valami — erre sem találtunk
hivatkozást.

**A PicasaPy-t nem érinti**: nincs mit reprodukálni.

### 13.6 REJTETT MAPPÁK — két különböző fogalom (a 12.5 második fele)

A Picasában **kettő** van, és a Mappakezelő fájára **egyik sem hat**:

**(a) A könyvtár kizárási listája** — `0x004e4ea0` (361 b) építi, egyszer,
induláskor (`0x004051b0` → `0x00402f90` → `0x004183c0` → `0x004e4ea0`).
Három forrásból áll:

1. **Négy beégetett mappanév** (`0x004fbb90`):
   `thumbs`, `RECYCLER`, `Originals`, `.picasaoriginals`.
2. **A `runtime\filters.txt`** (`0x004e4fc5`), parszer: `0x004fbd30`
   (3392 b). **Hat szakaszt** ismer — a napló-címkéi is megvannak
   (`DS::DirectoryFilters` stb.):
   `DirectoryFilters`, `DirectoryIncludes`, `FileFilters`,
   `FileIncludes`, `BundleFilters-BlackList`, `BundleFilters-WhiteList`.

   **A telepítőben szállított valódi fájl** — megvan helyben
   (`research/copy_Picasa_3_7/Picasa3/runtime/filters.txt`, 13 sor):

   ```
   DirectoryFilters

   windows
   winnt
   temp
   Program Files
   Originals

   DirectoryIncludes

   FileFilters

   FileIncludes
   ```

   Vagyis: az öt kizárt mappanév **`windows`, `winnt`, `temp`,
   `Program Files`, `Originals`**; a másik három szakasz **üres**, a két
   `BundleFilters` szakasz pedig **nincs is a fájlban** (a parszer ismeri,
   a szállított fájl nem használja).

3. **Regisztrációs adatbázisból feloldott útvonalak** — a
   `ytDirScannerWindows` init (`0x006a8660`, 1796 b) négy nevesített
   szűrőt tesz a `Filters` beállítás-csoportba:

   | szűrő neve | forrás |
   |---|---|
   | `IECache` | `SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings\Cache\Paths` → az alkulcsok `Directory` értéke |
   | `ProgramFiles` | `SOFTWARE\Microsoft\Windows\CurrentVersion` → `ProgramFilesDir` |
   | `LocalSettings` | a felhasználó Local Settings mappája |
   | `AppData` | a felhasználó AppData mappája |

**(b) A program saját „rejtett mappa" fogalma** — a `]hidden` adatbázis-token
(11 hivatkozó függvény, pl. `0x0041c340`, `0x004a51f0`) és a
`Preferences\ShowHidden` kapcsoló (olvasói: `0x00440af0`, `0x005c9300`,
`0x005643e0`, `0x0067bda0`). A könyvtárpanel egyik csoportfejléce épp
**`Hidden Folders`** (`0x00402f90`, `0x005ec130`).

**NEGATÍV EREDMÉNY — mindkettőre:** sem a kizárási lista építője
(`0x004e4ea0`), sem a `ShowHidden` négy olvasója **nincs** a Mappakezelő
tartományában (`0x007be…`–`0x007ca…`), és a fa szála (`0x007c9e70`), a
csomópont-hozzáadó (`0x007c6d30`) és a rekurzió (`0x007bf680`) **egyiket
sem hívja**. A kizárás a **könyvtár-beolvasóé**, nem a Mappakezelő fájáé.

**Amit ez jelent:** a Mappakezelő fája a lemez tényleges mappaszerkezetét
mutatja; a `windows` / `temp` / `Program Files` **nem a fából hiányzik,
hanem a beolvasásból**. A Windows „rejtett" attribútumára (`FILE_ATTRIBUTE_HIDDEN`)
sem a fában, sem a kizárási listában **nem találtunk vizsgálatot**.

### 13.7 Eredeti / nálunk / teendő

| # | Viselkedés | Eredeti Picasa | Nálunk (0.8.27) | Teendő |
|---|---|---|---|---|
| 1 | Gyerekek felsorolása | **lusta**, első kinyitáskor, **háttérszálon** | nincs Mappakezelő | lusta + aszinkron modell |
| 2 | Becsukás | csak elrejt, a gyerekek megmaradnak | — | ne dobja el a betöltött ágat |
| 3 | Gyökerek | Asztal, Képek, Dokumentumok, majd meghajtók | — | ez a sorrend, rögzítve |
| 4 | Meghajtóbetűk | **C:–Z:**, az A:/B: kihagyva | — | Linuxon nem alkalmazható; a gyökér `/` és a csatolási pontok |
| 5 | Belső lemez | csak `FAT`/`FAT32`/`NTFS` | — | **NE reprodukáljuk** — korabeli korlát, ext4/btrfs kizárná |
| 6 | Hálózati meghajtó | listázva **ellenőrzés nélkül**, leválasztva is | — | a hálózati csatolást ne stat-oljuk a fa felépítésekor (különben a fa megakad) |
| 7 | Rejtett mappák | a fa **nem** szűr | — | a fa mutassa őket; a szűrés a beolvasóé |
| 8 | Kizárási lista | 4 beégetett + `filters.txt` + 4 regisztrációs útvonal | nincs | Linuxos megfelelő: `.Trash*`, `lost+found`, `.picasaoriginals`, `Originals`, `.thumbnails` + felhasználói lista |

### 13.8 Ami ebből MÉG nyitva marad

- ~~A `filters.txt` `DirectoryIncludes` / `FileIncludes` /
  `BundleFilters-*` szakaszainak szemantikája~~ — **LEZÁRVA** (2026-08-21,
  M9): a mérés a `picasa-program-resources.md` **3.1** szakaszába került.
  Röviden: a `DirectoryIncludes` **eltárolódik** és a **sorrend** miatt
  felülír (mindkét teszt előbb őt nézi); a **`FileIncludes` sorai
  ELDOBÓDNAK** (`0x004fc954`); a `BundleFilters-*` nem lista, hanem egy
  előre feltöltött katalógus (`[obj+0x3e4]`) elemein kapcsol. A
  név-illesztés **teljes, kis-nagybetű-független egyezés**, az
  útvonal-illesztés **kis-nagybetű-független előtag**.
- ~~A `ytVolumeIsExternalFS` predikátum HASZNÁLATA~~ — **LEZÁRVA**
  (2026-08-21, M10 — ld. 13.5): a példány **használatlan**; a
  név/viselkedés feszültség pedig **szerkesztői összevonás** (`/OPT:ICF`),
  nem szemantikai rejtély.

---

## 14. A „Figyelt mappák" lista INTERAKTÍV — és kétirányú a fával (2026-08-21)

Ez a szakasz a 12. lista 6. pontját zárja le (M6). Bizalmi fok:
**megerősített** — minden állítás mögött utasításszintű cím áll.

### 14.1 A két listavezérlő azonosítója

A vezérlő-kötő `0x007c0810` két rekeszbe teszi a listaboxokat:

| rekesz | vezérlő | cím |
|---|---|---|
| `[dlg+0x2f8]` | `foldermgr/foldertree` — a **bal fa** | `0x007c0862` |
| `[dlg+0x2fc]` | `foldermgr/watched_folders` — a **jobb lista** | `0x007c0896` |

Listaboxon belül (`ytListBox`, `0x009d2810` alapján):
`[lb+0x2f8]` = a kijelölt sor **relatív** indexe, `[lb+0x320]` = a
**görgetés-eltolás**; az abszolút sorszám a kettő **összege** — a kód
mindenütt így képzi.

`0x009d2810` = `SetSelection(lb, index, jelző)`: a `-1` **törli a
kijelölést**, és a `lb_preselected` értesítést küldi
(`0x009d284e`, osztály `0x08000002`).

### 14.2 A jobb lista TARTALMA — `[dlg+0x270]`

A sorrajzoló `0x007c6ba0` (`CFolderMgrDialog::WatchedListDraw`) a
gazdadialógusból (`[rajzoló+8]`) olvas:

```asm
0x007c6bb1  mov  ecx, dword ptr [eax + 0x274]
0x007c6bb7  shr  ecx, 1                       ; sorszám
0x007c6bb9  cmp  dword ptr [ebp + 8], ecx      ; a kért sor tartományban van?
```

Ugyanezt a tömböt indexeli a kattintáskezelő (`0x007c5a89`) és az
„Eltávolítás" rádió tartalék-ága (`0x007c4150`).

**Tehát `[dlg+0x270]` (elemszám `[dlg+0x274]>>1`) a jobb oldali lista
tényleges tartalma.** Ez **pontosítja az 5.2/b táblázatot**: ott ez a
tömb csak mint „az Eltávolítás rádió által mutált lista" szerepelt — a
mutáció igaz, de a tömb elsődleges szerepe az, hogy **ez a látható
figyelt-mappa lista**.

**Mit ír bele melyik rádió:**

| rádió | művelet a `[dlg+0x270]`-en | cím |
|---|---|---|
| **Keresés mindig** | `0x00492e40` keresés; ha **nincs benne**, a **végére fűzi** | `0x007c2f5b`–`0x007c2f6f` |
| **Eltávolítás a Picasából** | `0x00492e40` keresés; a megtalált tételt **kiveszi** | `0x007c4184`–`0x007c4195` |

**Rendezés: NINCS.** A hozzáfűzés a tömb **végére** megy, rendező hívás
sehol. A lista tehát a **kezdeti betöltés sorrendjét** (a
`watchedfolders.txt` sorrendje) őrzi, és az újakat **a végén** mutatja.

*(A „Keresés mindig" ága ezen kívül a `[dlg+0x2a8]`-ba is felvesz —
`0x007c2c05`, ha még nincs benne; a kettő szerepének viszonya a 14.5-ben
marad nyitva.)*

### 14.3 KATTINTÁS a jobb listán → a fa követi

Az `lb_selected` kezelő (`0x007c5830`) a küldőt megnézi
(`[értesítés+0x24]`), és **külön ága van a jobb listának**:

```asm
0x007c5a5f  mov  ecx, dword ptr [ebx + 0x2fc]   ; a JOBB lista?
0x007c5a65  cmp  eax, ecx
0x007c5a67  jne  0x7c5af2                       ; nem -> a fa ága
0x007c5a6d  eax = [lista+0x320] + [lista+0x2f8] ; abszolút sorszám
0x007c5a79  ecx = [dlg+0x274] >> 1              ; tartomány-ellenőrzés
0x007c5a83  jae  0x7c5bf0                       ; kilóg -> nincs teendő
0x007c5a89  edx = [dlg+0x270]                   ; a tömb
0x007c5a95  esi = &tömb[eax]                    ; a kiválasztott útvonal
0x007c5a9a  call 0x5c2100                       ; [dlg+0x2ec] := ez az útvonal
0x007c5aa1  call 0x7c60d0(dlg, &[dlg+0x2ec])    ; << KÖZÖS állapotfrissítő (5.2)
0x007c5aae  call 0x7c91c0(&[dlg+0x414], &útvonal)  ; a fában megkeresés
0x007c5ab5  je   0x7c5ad2
0x007c5ab7  ebx = [dlg+0x2f8]
0x007c5ac2  call 0x9d2810(fa, -1, 0)            ; a fa kijelölésének TÖRLÉSE
0x7c5ad2:
0x007c5ad5  call 0x7bf130(&[dlg+0x414], &útvonal)  ; „betöltendő útvonal" beírása
0x007c5ae1  call SetEvent([dlg+0x550])          ; << a háttérszál ébresztése
```

**Három, egymástól független következmény:**

1. **A dialógus aktuális mappája átvált** a kiválasztott figyelt mappára
   (`[dlg+0x2ec]`).
2. **Lefut a közös állapotfrissítő** (`0x007c60d0`, 5.2) — vagyis a jobb
   felső **három rádió és az arcfelismerés-sor is átáll**, pontosan úgy,
   mint amikor a fában kattintasz. **Ez a lista tehát nem díszlet: teljes
   értékű kiválasztó vezérlő.**
3. **A bal fa reagál.** Ha az út **kinyitható** (a `0x007c91c0` `0`-t ad),
   a program kinyitja az összes ősét, majd a `[CDirArray+0x128]`
   „betöltendő útvonal" rekeszbe teszi az utat és felébreszti a
   háttérszálat, azaz **a fa lustán kinyílik odáig** (13.2). Ha **nem**
   (`9`), a fa **kijelölése törlődik**, hogy ne maradjon elavult kiemelés.
   A két érték pontos jelentése: **14.7**.

**Keresztellenőrzés a 13. szakasszal:** az itt ébresztett esemény a
`[dlg+0x550]`, a `CDirArray` pedig a `[dlg+0x414]`-en ül —
`0x414 + 0x13c = 0x550`, vagyis **ugyanaz az esemény**, amit a
`0x007bf210` kinyitás-ág használ. A két szakasz mérése egymást igazolja.

`0x007bf130` (218 b) törzse ezt meg is erősíti: kritikus szakaszon belül
a `[CDirArray+0x128]` sztringmezőt írja felül a kapott útvonallal
(`0x007bf17a`–`0x007bf1b9`).

### 14.4 KATTINTÁS a fában → a jobb lista kijelölése törlődik

A másik ág (`0x007c5af2`-től) szimmetrikus:

```asm
0x007c5af8  jne  0x7c5bf0                       ; nem a fa -> vége
0x007c5b1c  ecx = [dlg+0x2f8]
0x007c5b28  eax = [fa+0x320] + [fa+0x2f8]       ; a fa abszolút sora
0x007c5b42  call 0x7bfcb0(&[dlg+0x414], sor, &út)  ; sor -> útvonal
0x007c5b49  jne  0x7c5b66                       ; hiba -> vége
0x007c5b51  call 0x7c60d0(dlg, &út)             ; ugyanaz a közös frissítő
0x007c5b56  ebx = [dlg+0x2fc]
0x007c5b61  call 0x9d2810(lista, -1, 0)         ; a JOBB lista kijelölésének törlése
```

**Vagyis a két lista kijelölése kölcsönösen kizárja egymást**: mindig
legfeljebb az egyikben van kiemelt sor. (A képernyőképen a fában van a
kiemelés — a `podcast` soron —, a jobb listában nincs.)

### 14.5 Eredeti / nálunk / teendő

| # | Viselkedés | Eredeti | Nálunk (0.8.27) | Teendő |
|---|---|---|---|---|
| 1 | A jobb lista sora | **kattintható**, teljes értékű kiválasztó | nincs Mappakezelő | kattintható lista |
| 2 | Kattintásra | a három rádió + arcfelismerés **átáll** | — | ugyanaz az állapotfrissítő fusson, mint a fánál |
| 3 | Kattintásra | a **fa odaugrik**, szükség esetén **lustán kinyílik** | — | a fa nyissa ki az őseit és jelölje ki a sort |
| 4 | Fában kattintva | a **jobb lista kijelölése törlődik** | — | kölcsönösen kizáró kijelölés |
| 5 | Rendezés | **nincs** — betöltési sorrend + a végére fűzés | — | ne rendezzük ábécébe |
| 6 | „Keresés mindig" | a mappa **azonnal megjelenik** a jobb listában | — | a lista frissüljön OK előtt |
| 7 | „Eltávolítás" | a mappa **azonnal eltűnik** a jobb listából | — | ugyanígy |
| 8 | „Eltávolítás" a fa kijelölése nélkül | a **jobb lista** kijelölésére hat (`0x007c412e`) | — | tartalék-ág kell |

### 14.6 Ami ebből nyitva maradt — MINDKETTŐ LEZÁRVA

- ~~A `[dlg+0x270]` és a `[dlg+0x2a8]` viszonya~~ — **LEZÁRVA**
  (2026-08-21, M11 — ld. **5.2/d**): a `+0x2a8` **munkamenet-helyi delta**,
  ami **nem jut el az alkalmazóig**; a `watchedfolders.txt` a `+0x270` →
  `[könyvtár+0x2bc]+0xf8` → `0x004f5960` láncon íródik. **Az 5.2/b
  táblázata ezen a ponton helyesbítve.**
- ~~A `0x007c91c0` háromértékű visszatérése~~ — **LEZÁRVA** (2026-08-21,
  M12 — ld. **14.7**): **két** érték van, nem három (`0` = siker,
  `9` = kudarc); a `1` egy tömb-növelő rutin helyi változója volt.

### 14.7 A fa-ugratás visszatérése — KÉT érték, nem három (2026-08-21, M12)

> ⚠️ **HELYESBÍTÉS a 14.6-hoz.** Ott „háromértékű visszatérés (`0`, `1`,
> `9`)" szerepelt. **A `1` NEM visszatérési érték** — egy tömb-növelő
> rutin helyi változója (`0x007c96bf mov eax,1` = kezdő kapacitás, utána
> `jmp 0x7c96d2`, nem az epilógusba). A függvény **két** értéket ad.

#### 14.7/a `0x007c91c0` — a belépő

```c
int Reveal(CDirArray* fa, ytString* célÚtvonal);
```

Végigmegy a **látható sorokon** (`[fa+0x7c]` tömb, elemszám
`[fa+0x80]>>1`), és mindegyik sor útvonalára megnézi, hogy **előtagja-e**
a célnak (`0x00987030`, kis-nagybetű-független előtag-teszt — a
szemantikája a `picasa-program-resources.md` 3.1.2-ben mérve):

```asm
0x007c9218  mov  eax, dword ptr [esp + 0x24]   ; a cél útvonal
0x007c921e  call 0x987030                      ; előtag-e a sor útja?
0x007c9225  jne  0x7c924a                      ; IGEN -> a tényleges munka
   ...
0x007c923b  mov  eax, 9                        ; egyetlen sor sem előtag -> 9
0x007c924a  call 0x7c9270                      ; találat -> ennek az értéke
```

#### 14.7/b `0x007c9270` — a rekurzív kinyitó

**Rekurzív** (`0x007c9404 call 0x7c9270`): a cél útvonal **őseit** nyitja
ki egyesével.

```asm
0x007c9404  call 0x7c9270                      ; előbb a SZÜLŐ
0x007c9409  test eax, eax
0x007c940b  jne  0x7c9456                      ; a szülő nem sikerült -> 9
0x007c9416  call 0x40ecd0                      ; a szülő SORÁNAK keresése
0x007c941d  cmp  ebx, -1
0x007c9424  jne  0x7c9479
0x007c9443  mov  eax, 9                        ; nincs ilyen sor -> 9
0x007c9479:
0x007c9479  mov  edx, dword ptr [ebp + 0x118]  ; a „kinyitva" jelzőtömb
0x007c9483  mov  dword ptr [edx + ebx*4], 1    ; << KINYITJA a csomópontot
   ...
0x007c997f  mov  dword ptr [edx + ecx*4], 1    ; << és a célt is
0x007c9993  xor  eax, eax                      ; SIKER -> 0
```

**A teljes visszatérési halmaz `{0, 9}`.** A függvényben pontosan **két**
`jmp 0x7c9995` (az epilógusba) van, mindkettő `eax = 9`-cel; minden más út
a `0x007c9993 xor eax, eax`-ra fut, tehát **0**-t ad.

| érték | jelentés | hol keletkezik |
|---|---|---|
| **0** | **siker** — a cél minden őse „kinyitva" jelzőt kapott | `0x007c9993` |
| **9** | **kudarc** — nincs előtag-sor (`0x007c923b`), vagy a rekurzió elbukott (`0x007c9443`), vagy a ciklus találat nélkül végigfutott (`0x007c946f`) | három hely |

**Keresztellenőrzés:** a `[fa+0x118]` jelzőtömb **ugyanaz**, amit a
13.2 a kinyitás/becsukás kapcsolónál (`0x007bf2ee`) mért. Két, egymástól
függetlenül vizsgált függvény ugyanazt az adatszerkezetet írja.

#### 14.7/c Miért indít a SIKER háttérbetöltést?

A 14.3-beli elágazás így olvasandó:

```asm
0x007c5aae  call 0x7c91c0(&[dlg+0x414], &út)
0x007c5ab3  test eax, eax
0x007c5ab5  je   0x7c5ad2      ; 0 = SIKER
0x007c5ac2  call 0x9d2810(fa, -1, 0)          ; 9 = kudarc -> kijelölés törlése
0x7c5ad2:
0x007c5ad5  call 0x7bf130(&[dlg+0x414], &út)  ; siker -> „betöltendő útvonal"
0x007c5ae1  SetEvent([dlg+0x550])             ;          + a szál ébresztése
```

Ez **nem ellentmondás**: a kinyitás csak **jelzőt állít**
(`[fa+0x118][sor] = 1`), a gyerekek tényleges felsorolása a
**háttérszál** dolga (13.2). Tehát:

- **siker** → a most kinyitott ágak gyerekeit **be kell tölteni** → a
  betöltési kérés + ébresztés;
- **kudarc** → nincs mit mutatni → a fa kijelölése **törlődik**, hogy ne
  maradjon elavult kiemelés.

**A felhasználó szempontjából:** a jobb listában kiválasztott mappa a fában
kinyílik és kijelölődik; ha az útja egyáltalán nincs a fában (pl. egy
azóta leválasztott meghajtón van), a fa **kijelölés nélkül marad** —
hibaüzenet nélkül.

---

## 15. „Eltávolítás a Picasából…" — a MENÜPONT teljes működése (2026-08-22)

*Forrás: `foldermgr.tre:49` (`foldermgr/remove_label`).*

⚠️ **Ez NEM a Mappakezelő rádiógombja.** Két, magyarul majdnem azonos nevű
dolog létezik, és a **hármaspont** különbözteti meg őket:

| | felirat | mi ez |
|---|---|---|
| `foldermgr/remove_label` | „Eltávolítás a Picasából" | a **Mappakezelő rádiógombja** (állapot, ld. 5.) |
| **`Folder::ID_MANAGE_ALBUM`** | **„Eltávolítás a Picasából…"** | **helyi menü / Mappa menü parancsa** — ez a szakasz |
### 15.1 A belépési pontok

A parancskulcs **két** helyen szerepel:

- `Folder::ID_MANAGE_ALBUM` — a **mappa helyi menüje** (`0x007319f0`,
  `0x00733a40`)
- `eMenuLabelFolder::ID_MANAGE_ALBUM` — a menüsáv **Mappa** menüje
  (`0x00559150`)

Mindkettő a `0x005ce590(objektum, mód)` függvényre fut, **`mód != 0`**
argumentummal. *(A `mód == 0` ág ugyanennek a függvénynek a másik fele: az
a **Mappakezelőt nyitja meg** — ld. 10/b.1.)*

### 15.2 A megerősítő párbeszéd — szó szerint

| elem | kulcs | angol | magyar |
|---|---|---|---|
| cím | `CThumbUI:ManageAlbumConfirm` | *Confirm* | — |
| szöveg | `CThumbUI::ManageAlbum` | *Do you want to remove the folder "%s" and its subfolders?* | **Eltávolítja a(z) „%s" mappát és a hozzá tartozó almappákat?** |
| igen-gomb | `CThumbUI:ManageAlbumYesButton` | *Remove Folder* | **Mappa eltávolítása** |
| mégse | `il_Cancel` | *Cancel* | Mégse |

A párbeszédet a `0x009ba4d0` építi, a `0x009bab50` futtatja; **`2`-es
visszatérés = Mégse**, ekkor a függvény `0xF4242`-vel kilép, és **semmi
nem történik** (`0x005ce908`).

⚠️ **A szöveg kimondja, hogy az ALMAPPÁKRA is vonatkozik**, és
**tartalmazza a mappa nevét** (`%s`).

### 15.3 Mi történik jóváhagyás után — a teljes lánc

```
0x005ce946  call 0x0097e4c0            ; köteg kezdete
0x005ce952  add  dword [0xd6793c], 1   ; UI-frissítés elnyomása (mélységszámláló)
…
0x005ced3c  call 0x004f6a20            ; az útvonalkészlet felépítése:
                                       ;   a mappa + "\Originals" + "\Modified"
0x005ced57  call 0x004f5960            ; -> watchedfolders.txt  ÚJRAÍRÁSA
0x005ced79  call 0x004f5d90            ; -> frexcludefolders.txt ÚJRAÍRÁSA
0x005ced90  call 0x004b9200            ; -> ]album:removed  SÍRKŐ (ld. lent)
0x005ceda3  call 0x0047cea0 …          ; iPhoto / Apple Photos ágak (Mac)
0x005cedd9  call 0x0065b840            ; nézet-frissítés (keresősáv)
0x005cee24  sub  dword [0xd6793c], 1   ; köteg vége; ha 0 -> kurzor vissza
```

**Két dolog, amit ki kell emelni:**

1. **A `\Originals` és a `\Modified` almappa is a készlet része** — a
   Picasa a szerkesztési biztonsági másolatok mappáit is eltávolítja
   a mappával együtt.
2. **A művelet KÖTEGELT**: a `[0xd6793c]` mélységszámláló a teljes lánc
   idejére elnyomja a felület frissítését, és csak a végén enged egyetlen
   újrarajzolást — plusz visszaállítja az egérkurzort
   (`LoadCursorA(0, IDC_ARROW)` + `SetCursor`).

### 15.4 ⭐ A lényeg: `]album:removed` — SÍRKŐ, nem törlés

`0x004b9200(adatbázis, útvonallista)`, teljes egészében:

```c
for (i = 0; i < lista.count; ++i) {
    ha (0x00441cd0(albumtábla, &lista[i], &kimenet) != 0)   // MÁR ismert?
        continue;                                           // -> kihagy
    [albumtábla+0x48]->vtbl[0](kimenet, 0);                 // új bejegyzés
    0x00444990(albumtábla, kimenet);   edx = "]album:removed";
}
```

⇒ **A mappa NEM törlődik az adatbázisból — bekerül egy `]album:removed`
tokennel megjelölt bejegyzésként.** Ez sírkő: a beolvasó ebből tudja, hogy
a mappát a felhasználó **szándékosan** vette ki, tehát a következő
végigolvasásnál **nem szabad újra felvenni**.

*Bizonyítottsági fok: **megerősített** — a teljes hívási lánc szó szerint
olvasva, a három írófüggvény a saját fájlnév-sztringjével azonosítva
(`watchedfolders.txt`, `frexcludefolders.txt`, `]album:removed`).*

### 15.5 Eredeti / nálunk / teendő — KÉT MÉRT HIBA

Jegy: **#1249**.

| # | | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|---|
| 1 | **almappára hat-e** | igen (a szöveg is kimondja) | ❌ **SEMMIT NEM CSINÁL** | a helyi menü a `removeFolder`-t hívja, ne a `removeWatchedFolder`-t |
| 2 | **visszajön-e újraolvasáskor** | **nem** — `]album:removed` sírkő védi | ❌ **VISSZAJÖN** | sírkő-tábla kell az indexbe |
| 3 | megerősítő szöveg | tartalmazza a **mappa nevét** és kimondja az **almappákat** | „Remove this folder from PicasaPy? The files stay on disk." | az eredeti szövegre cserélni |
| 4 | igen-gomb felirata | **Mappa eltávolítása** | általános „Igen" | felirat javítása |
| 5 | `\Originals`, `\Modified` | a készlet része | nincs kezelve | ellenőrizni |
| 6 | belépési pontok | **két** menü (helyi + Mappa menü) | helyi menü ✔; menüsáv-tétel ellenőrizendő | — |

**A mérés (2026-08-22), amivel az 1. és 2. sor eldőlt:**

```
_find_root("gyoker")       -> "…/gyoker"      (a figyelt gyökér)
_find_root("gyoker/alma")  -> None            (almappára NINCS találat)

removeWatchedFolder("gyoker/alma")  -> a figyelt gyökerek listája VÁLTOZATLAN
                                       (a metódus a None-on azonnal kilép)

removeFolder("gyoker/alma")         -> az index-ből eltűnik  ✔
ctl.rescan()                        -> az „alma" VISSZAKERÜL  ❌
```

⇒ Az 1. hiba magyarázza a felhasználó által jelentett tünetet
(„a mappa nem tűnik el a bal menüben"): a helyi menü
(`FolderPane.qml:979` és `:729`) a **szűkebb** `removeWatchedFolder`-t
hívja, ami **kizárólag pontos figyelt-gyökér egyezésre** csinál bármit
(`library_controller.py:423–432`).

---

## 16. HOGYAN veszi észre az eredeti az új fájlt? (2026-08-23, #1275)

> ⚠️ **HELYESBÍTVE 2026-08-24-én — a 16.1 szakasz számai TÉVESEK VOLTAK.**
> Az eredeti **használ** változás-értesítést; a leszámlálásom hibás volt.
> A részletes helyesbítés a **16.4** szakaszban. A 16.1–16.3 azért marad
> itt, hogy a hiba visszakereshető legyen — a számait NE használd.

A #1275 kulcskérdése: a futó alkalmazás hogyan veszi észre a figyelt
mappába kívülről bekerülő képet — és mi a helyzet **hálózati meghajtón**.
A bináris egyértelmű választ ad, és ez a válasz **a mi tervezésünket is
eldönti**.

### 16.1 Az eredeti NEM használ operációs rendszer-szintű fájlfigyelést

| API | importálva? | hivatkozás a végrehajtható szakaszokban |
|---|---|---|
| `ReadDirectoryChangesW` | **NINCS importálva** | — |
| `SHChangeNotifyRegister` | **NINCS importálva** | — |
| `FindFirstChangeNotificationW` | igen (`0xc404d0`) | ~~0~~ → **1** (16.4) |
| `FindFirstChangeNotificationA` | igen (`0xc404d8`) | **0** (ez igaz) |
| `FindNextChangeNotification` | igen (`0xc403c0`) | ~~0~~ → **2** (16.4) |
| `FindCloseChangeNotification` | igen (`0xc40368`) | **2** (`0x004e1805` betöltés, `0x004e18ba` hívás) |

⇒ ~~A program lezárná a változás-figyelő fogantyúkat, de soha nem hoz
létre egyet sem.~~ **EZ TÉVES — ld. 16.4.** A `FindNext…` két valódi
hívóval rendelkezik az alkalmazás kódjában, és a fogantyúkat éppen
változás-értesítésként fegyverzi újra.

*(Módszertani megjegyzés: az első keresésem csak a
`call dword ptr [abszolút]` alakot nézte, és emiatt a `FindClose…`-t is
elmulasztotta. A fenti számok a **teljes végrehajtható szakaszok**
minden operandus-hivatkozására vonatkoznak. ⚠️ A `.text` egészének
lineáris diszasszemblálása viszont **elcsúszhat** — pontos
eltolás-kereséshez mindig ismert függvényhatárról indíts,
`annot_disasm.py`-vel.)*

### 16.2 Amit HELYETTE csinál: újraolvasás és összehasonlítás

A mappafigyelés osztálycsaládja (RTTI):

| osztály | szerep |
|---|---|
| `ytDirScanner` / **`ytDirScannerWindows`** | a könyvtárbejáró |
| `ytDirScanner::ScanNotify` | értesítés a bejárás eredményéről |
| **`ytDirScannerChangeList`** / **`ytDirScannerChangeListWindows`** | a **változáslista** — a bejárás eredményének összevetése a korábbi állapottal |

A „változáslista" elnevezés önmagában is árulkodó: nem eseményeket fogad,
hanem **különbséget képez**. Ezt megerősíti a beépített hibakereső
kiíratás (`0x004f25f0`, `Preferences\WriteDirscannerCSV`), ami **három
pillanatképet** ment:

```
dirscanner-start.csv      ; induláskor
dirscanner-up.csv         ; futás közben
dirscanner-shutdown.csv   ; leálláskor
oszlopok: Name,Creation Time,Access Time,Size,Type,Dirty,Valid
```

Ezek pontosan azok a mezők, amikből egy **állapot-összehasonlítás**
elvégezhető (név + időbélyeg + méret + „piszkos" jelző).

A várakozást a `WaitForMultipleObjects` végzi (`0x007065f0` időkorláttal,
`0x00706680` nulla időkorláttal, azaz lekérdezéssel) egy fogantyú-tömbön —
és a 16.4 szerint ezek **igenis** változás-figyelő fogantyúk (a 0. rekesz
kivételével, ami a szál ébresztő/leállító eseménye).

### 16.2/b A hibakereső kiíratás TELJES működése — és a `badfiles.txt` (2026-09-02)

*A 16.2 megnevezte a három CSV-t és az oszlopneveket. Ez a szakasz a
`0x004f25f0` (1952 b) végigolvasásából adja a **működést** — és egy
eddig sehol nem dokumentált **második kimenetet**.*

#### A négy mód — és hogy csak három közülük kapuzott

A függvény `ecx`-ben kapja a **módot**:

| mód | mit ír | a `Preferences\WriteDirscannerCSV` kapu | cím |
|:--:|---|---|---|
| **1** | `dirscanner-start.csv` | **igen** | `0x004f26a9` |
| **2** | `dirscanner-up.csv` | **igen** | `0x004f26d5` |
| **3** | `dirscanner-shutdown.csv` | **igen** | `0x004f26e4` |
| **4** | ugyanaz, mint a 3. | ⭐ **NEM** — a kaput átugorja, és a végén **meg is nyitja** a fájlt (`0x00981280`, `GetSystemDirectoryA`-val indított külső program) | `0x004f2622`–`0x004f262c`, `0x004f2b0d` |

Ha a kulcs nincs beállítva (1–3. mód), a függvény **azonnal visszatér**
(`0x004f2694`) — a CSV nem jön létre. ⇒ **Ez fejlesztői kapcsoló, nem
felhasználói szolgáltatás.**

**Hova:** mindkét kimenet a **`#db3\`** útvonal-tokenre megy
(`0x00c7eeb8`) — vagyis a `…\Google\Picasa2\db3\` mappába, ugyanoda, ahol
a `backups.xml` és a `thumbindex.db` van. A CSV **`"w"` módban**
(`0x00c7ebe4`) nyílik, tehát **teljes újraírás**.

#### A CSV sorformátuma — és mit jelent a hét oszlop

```
Name,Creation Time,Access Time,Size,Type,Dirty,Valid        (fejléc, 0x00c864d4)
"%s",%f,%f,%d,%d,%d,%d                                      (sor,    0x00c8650c)
```

A mezők a bejegyzés-rekordból, a `0x004f2951`–`0x004f295f` push-sorrendje
szerint:

| oszlop | forrás | típus | mi VALÓJÁBAN (2026-09-05, #2304) |
|---|---|---|---|
| `Name` | a bejegyzés neve, **idézőjelek közt** | szöveg | |
| `Creation Time` | `[rekord+0x04]` → `0x0098b650` (FILETIME → `double`) | `%f` | a kép **metaadat-dátuma** |
| `Access Time` | `[rekord+0x0c]` → ugyanaz | `%f` | ⛔ **a NÉV téves** |
| `Size` | `[rekord+0x14]` | `%d` | |
| **`Type`** | `[rekord+0x18]` | `%d` — **értékkészlet lent** | |
| `Dirty` | `[rekord+0x1c]` (bájt) | `%d` | |
| `Valid` | `[rekord+0x1d]` (bájt) | `%d` | |

⚠️ **A két időoszlop NEVE megtévesztő** (2026-09-05, #2304): az
`Access Time` valójában a fájl **utolsó módosítási** ideje
(`ftLastWriteTime`, `0x004e74bd` → `0x004e74dc`), a `Creation Time` pedig
**nem fájlrendszeri idő**, hanem a kép beolvasáskor rögzített
metaadat-dátuma. Levezetés és mérés: `pmp-database.md` 10. szakasz.

⇒ A „piszkos" (`Dirty`) és az „érvényes" (`Valid`) **külön jelző**: a
változáslista tehát nemcsak azt tartja nyilván, hogy egy bejegyzés
megváltozott-e, hanem azt is, hogy **egyáltalán használható-e**.

#### ⭐ A `badfiles.txt` — a MÁSODIK kimenet, eddig sehol nem dokumentálva

Ugyanaz a függvény, a CSV után, **ugyanabba a `#db3\` mappába** kiír egy
`badfiles.txt`-et is (`0x00c86524`, `0x004f299c`), és abban végigmegy az
összes bejegyzésen:

| a `Type` értéke | mit ír | cím |
|:--:|---|---|
| **4** | `%s (badfile)\n` (`0x00c86534`) | `0x004f2a58`–`0x004f2a8a` |
| **5** | `%s (baddirectory)\n` (`0x00c86544`) | `0x004f2aaa`–`0x004f2ad8` |

⇒ **A `Type` oszlop nem pusztán „fájl vagy mappa": a 4 és az 5 azt
jelenti, hogy a Picasa a bejegyzést NEM tudta feldolgozni.** A
könyvtárbejáró tehát **nyilvántartja a hibás fájlokat és mappákat**, és
kérésre ki is listázza őket.

#### ✅ A `Type` további értékei — LEZÁRVA (2026-09-05)

> ⚠️ **Helyesbítés: ez a tétel részben ELAVULT volt.** A `Type = 1`
> (könyvtár) és a `Type = 1001` (arcsablon-bejegyzés) jelentését a
> **`pmp-database.md` 8.1** már **megmérte** két valódi katalóguson — a
> 1001-et halmaz-azonossággal a `facetemplatesV2_index.db` foglalt
> slotjaival (412 = 412). A blokkolás azért maradt itt, mert a választ egy
> MÁSIK lap adta meg. *(A tanulság a `docs/specs/00-index.md`-be is
> átvezetve.)*

**Ami ebben a körben ÚJ — a névfeloldás pontos szabálya**
(`0x004f27f3`–`0x004f2825`, megerősített):

```
ha  rekord.valid (+0x1d) == 0            → a NÉV önmagában a teljes út
ha  rekord.Type  (+0x18) ∈ {1, 5, 25, 1001} → a NÉV önmagában a teljes út
különben                                  → szülő_neve + név
```

A szülőág is feltételes: ha a `+0x20` a rekordszámon kívülre mutat
(`0x004f282e`), vagy a **szülő** `Type`-ja `0` (`0x004f284a`), a Picasa a
`[objektum+0x550]` tartalék sztringre esik vissza — **kivételt nem dob**.

**⭐ A `Type = 1001` és a `+26` mező — a mért anomália MAGYARÁZATA.** A
`pmp-database.md` 8.1 azt mérte, hogy a kis katalógusban **412** bejegyzés
`+26` mezője nem mutat mappa-slotra, és hogy ez a 412 pontosan a
`Type = 1001` halmaz. A bináris megmondja, miért: a szülőlekérdező
**`FUN_004e2990` (66 b, `ret 4`)** így szól —

```
ha index >= rekordszám            → -1
ha rekord.Type == 1001            → -1        (0x004e29bb)
ha rekord.+0x20 == 0xFFFFFFFF     → -1        (0x004e29c7)
különben                          → rekord.+0x20
```

⇒ **arcsablon-bejegyzésen a `+26` mező NEM szülőindex**, és az eredeti
soha nem is olvassa annak. Az anomália tehát nem adathiba.

**A `Type = 5` — „hibás könyvtár", nem „másik fajta könyvtár"** *(erős, nem
megerősített)*. A `badfiles.txt`-írója (`0x004f2a40`–`0x004f2ae0`) a
teljes rekordtömbön végigmegy, és **feltétel nélkül** kiírja a
`Type == 4`-eseket `(badfile)`, a `Type == 5`-ösöket `(baddirectory)`
címkével. Egy `badfiles.txt` nevű fájl nem sorolná fel az összes rendes
mappát; és a mért darabszám is ezt támogatja (`pmp-database.md` 8.1:
**6**, illetve **19** darab a **2 338**, illetve **115** darab `Type = 1`
mellett). ⇒ A `pmp-database.md` „könyvtár (2. fajta)" sora **pontosítandó**.

**A `Type = 25` (`0x19`) — a JELENTÉSE továbbra sincs meg**, de a szerepe
három ponton körülhatárolt:

| hol | mit mond ki |
|---|---|
| `0x004f2822` környéke | a `{1, 5, 25, 1001}` halmaz tagja ⇒ **a neve teljes út** |
| `0x004efbcc`–`0x004efbe4` | a „piszkosra állítás" menetben a `{1, 25}` ágba esik, **de** a 25 és a 26 (`0x1a`) **ki van véve** a `dirty = 1` + hozzáférési idő nullázása alól |
| `0x004ea0e0`–`0x004ea0e8` | az `{5, 25}` páros kihagy egy összesítő ágat |

**Amit hozzá megnéztem, eredmény nélkül:** a `.text` teljes pásztázása
`mov reg,25`, `mov [reg+disp8],25` és `cmp reg,25` alakra — a
könyvtárbejáró tartományában (`0x4e0000`–`0x510000`) **egyetlen ÍRÓ sincs**,
csak olvasók; sztring sem tartozik hozzá. A tulajdonos két katalógusában
**0 előfordulás** (`pmp-database.md` 8.1 típus-táblája). **Megszerzés:** egy
olyan katalógus, amelyben előfordul, **vagy** a `0x004ea0c0` és a
`0x004efbb0` menet célzott dekompilációja.

#### ✅ A `DirscanRegression` kapcsoló — LEZÁRVA (2026-09-05)

> **Bizonyítottsági fok: megerősített.** A teljes ág elolvasva, az
> importált függvények névfeloldásával.

A `0x004e9b00` (649 b) a bejárás **befejező** ága. Ami ott történik:

```
0x004e9cdc  test byte [0x00da03c4], 1     ; már beolvastuk a kulcsot?
0x004e9ce3  jne  0x004e9d2e               ; igen → egyszer-olvasás
0x004e9ce5  or   dword [0x00da03c4], 1
0x004e9cec  push "DirscanRegression"      ; 0x00c86458
0x004e9cf1  push "Preferences"            ; 0x00c7eafc
0x004e9d05  call 0x00407a20               ; a beállítás beolvasása
0x004e9d0e  call 0x004019b0               ; → logikai érték
0x004e9d17  mov  byte [0x00da03c0], al    ; a gyorsítótárazott KAPCSOLÓ
0x004e9d2e  cmp  byte [0x00da03c0], 0
0x004e9d34  je   0x004e9d78               ; ha 0 → semmi nem történik
0x004e9d37  mov  ecx, 4                   ; ⇒ a CSV-író NEGYEDIK módja
0x004e9d3c  call 0x004f25f0
0x004e9d42  call dword [0x00c4023c]       ; ⇒ ExitProcess
```

⇒ **`Preferences\DirscanRegression = 1` esetén a Picasa a bejárás végén
kiírja a 4. módú CSV-t (a `WriteDirscannerCSV` kaput megkerülve), és
azonnal KILÉP** (`ExitProcess`). A kulcsot a folyamat **egyszer** olvassa
be (a `0x00da03c4` bit 0 őrzi), és a `0x00da03c0` bájtban tartja.

Ugyanez a függvény **méri is a bejárást**: `QueryPerformanceCounter`
(`0x004e9b0b`, `0x004e9ba7`, `0x004e9bba`) és
`QueryPerformanceFrequency` (`0x004e9be2`).

⇒ Ez egy **fejlesztői regressziós futtató**: indítsd el a Picasát, hagyd
lefutni a bejárást, kapsz egy CSV-t és egy időmérést, a program kilép.
**A termékre nincs hatása** — a kulcs alapértelmezés szerint hiányzik, és
a felhasználó felületén sehol nem állítható.

#### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| a bejáró nyilvántartja a hibás fájlokat | `Type = 4` | **nincs** — a `scanner/walker.py` minden `OSError`-t **némán elnyel** (`return`/`return None`: 142., 175., 188., 234., 258., 276., 301. sor) | **#1998** |
| a hibás **mappákat** is | `Type = 5` | ua. | ua. |
| kilistázható a hibás bejegyzésekről | `badfiles.txt` | nincs | ua. |
| állapot-pillanatkép hibakereséshez | három CSV, kapcsolóval | nincs | ua. (alacsonyabb prioritás) |

*Bizonyítottsági fok: **megerősített** a négy módra, a kapura, a `#db3\`
helyre, a `"w"` nyitásra, a hét oszlop forrására, a `badfiles.txt`
létére, a 4/5 `Type`-értékre, a névfeloldás szabályára, a
`FUN_004e2990` szülőlekérdezőre és a `DirscanRegression` hatására;
**erős** (nem megerősített) a `Type = 5` = „hibás könyvtár" olvasat;
a `Type = 25` JELENTÉSE **NINCS MEG**.*

#### Nyitott kérdések mérlege (16.2/b)

`0 nyílt · 7 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

*(2026-09-05: a két blokkolt tételből az egyik teljesen lezárult, a másik
háromnegyedéig — csak a `Type = 25` jelentése maradt.)*

| kérdés | állapot |
|---|---|
| mikor írja a három CSV-t | **LEZÁRVA** — mód 1/2/3, a `WriteDirscannerCSV` kapuval |
| hova írja | **LEZÁRVA** — `#db3\`, `"w"` módban |
| mi a sorformátum, honnan a hét oszlop | **LEZÁRVA** — `"%s",%f,%f,%d,%d,%d,%d` + a rekord-eltolások |
| van-e másik kimenet | **LEZÁRVA** — **igen: `badfiles.txt`** |
| mit jelent a `Type` 4 és 5 | **LEZÁRVA** — hibás fájl / hibás mappa |
| mit jelent a `Type` **1** | ✅ **LEZÁRVA** — könyvtár (`pmp-database.md` 8.1, két katalóguson mérve; a tétel itt **elavultan** állt blokkoltként) |
| mit jelent a `Type` **1001** | ✅ **LEZÁRVA** — arcsablon-bejegyzés (ua., halmaz-azonosság a `facetemplatesV2_index.db`-vel, 412 = 412); a `+26` mezője **nem** szülőindex, és az eredeti nem is olvassa annak (`FUN_004e2990`) |
| a névfeloldás pontos szabálya | ✅ **LEZÁRVA** — `valid == 0` vagy `Type ∈ {1, 5, 25, 1001}` ⇒ a név a teljes út; különben szülő + név; hibás szülőnél tartalék sztring, **nem kivétel** (`0x004f27f3`–`0x004f2887`) |
| **mit jelent a `Type` 25 (`0x19`)** | **BLOKKOLT** — a szerepe három ponton körülhatárolt (fent), a jelentése nincs meg. Megnézve: `mov reg,25`, `mov [reg+disp8],25`, `cmp reg,25` teljes `.text`-pásztázás ⇒ a bejáró tartományában **nincs író**; sztring nincs; a tulajdonos két katalógusában **0 előfordulás**. **Megszerzés:** olyan katalógus, amelyben előfordul, vagy a `0x004ea0c0` / `0x004efbb0` menet dekompilációja. |
| **mit csinál a `DirscanRegression`** | ✅ **LEZÁRVA** — a bejárás végén 4. módú CSV + **`ExitProcess`** (`0x004e9d37`–`0x004e9d42`); egyszer olvasott, gyorsítótárazott kapcsoló; a függvény időt is mér. Fejlesztői regressziós futtató, a termékre nincs hatása. |

### 16.3 Amit ez a #1275-re kimond

> ⚠️ **A premissza téves (16.4), a következtetés viszont ÁLL.** Az eredeti
> **egyszerre** figyel eseményt ÉS pollozik. Nincs olyan eseményfigyelés,
> amit *helyette* kellene „utánoznunk" — és épp ezért működik
> hálózati meghajtón is, ahol az eseményalapú figyelés notóriusan
> megbízhatatlan.

**Ebből következik a teendő:** a #1275-öt **nem** a watchdog
„megjavításával** kell megoldani. A helyes irány egy **időzített
újraolvasás** (a figyelt gyökerekre), ami a fájlrendszeri esemény
**mellett**, nem helyette fut — az esemény gyorsítás, a lekérdezés a
garancia. Ez egyben megválaszolja a jegy „ha a hálózati út elvi korlát"
ágát is: **nem korlát, hanem tervezési döntés** — az eredeti is így
oldotta meg.

*Bizonyítottsági fok: **megerősített** az import- és hivatkozás-számokra
(pefile + capstone, teljes végrehajtható szakaszok) és az
osztálynevekre/CSV-mezőkre (RTTI + sztringtár). **Erős**, de nem
megerősített: a lekérdezés **időköze** — konkrét intervallum-konstansot
nem találtam (nincs `…Interval` jellegű `Preferences`-kulcs a
könyvtárbejáróhoz).*

### 16.4 HELYESBÍTÉS — az eredeti IGENIS használ változás-értesítést (2026-08-24)

A 16.1 leszámlálása hibás volt. Az újramérés (`imports` tábla, a
`function_address` mező szerint csoportosítva — ez soronként **egy hívási
helyet** jelent, az üres mezős sor pedig maga az importbejegyzés, nem hívó):

| API | valódi hívási helyek | hol |
|---|---|---|
| `ReadDirectoryChangesW` | — | **nincs importálva** (ez igaz maradt) |
| `SHChangeNotifyRegister` | — | **nincs importálva** (ez igaz maradt) |
| `FindFirstChangeNotificationA` | **0** | — |
| `FindFirstChangeNotificationW` | **1** | `0x009b3000` — de ez **CRT `A`→`W` átalakító burok** (CP_UTF8 = `0xfde9`, `[0xc402e4]`), nem alkalmazáslogika |
| `FindNextChangeNotification` | **2** | `0x007065f0`, `0x00706680` — **alkalmazáskód** |
| `FindCloseChangeNotification` | **2** | `0x004e17f0`, `0x004e1890` — **alkalmazáskód** |

**A figyelő osztály szerkezete kiolvasható** (`0x007065f0`, 120 bájt):

```
[this+0x18] = fogantyú-tömb        [this+0x1c] >> 1 = fogantyúk száma
WaitForMultipleObjects([0xc4039c])  (count, tömb, bWaitAll=FALSE, timeout)
  eredmény == 0x102 (WAIT_TIMEOUT) → -1
  egyébként: tömb[jelzett] → FindNextChangeNotification([0xc403c0])  ← ÚJRAFEGYVERZÉS
```

A bontó oldal (`0x004e17f0`) a tömböt **az 1. rekesztől** zárja
`FindCloseChangeNotification`-nal, a **0. rekeszt kihagyja** — az tehát
más fajta fogantyú (a szál ébresztő/leállító eseménye), az 1..n−1 viszont
**valódi változás-értesítő**.

⇒ **Amit a 16.1 „védekező takarító ágnak" nézett, az a figyelő rendes
bontása.** A `FindNext…` nem hívható olyan fogantyún, amit nem
`FindFirst…` adott.

#### Ami EBBŐL is nyitva maradt

**A létrehozó hívási helyet nem találtam meg.** A `FindFirstChangeNotificationA`
hívó nélküli, a `W` változatot pedig csak a CRT-burok hívja — amit viszont
senki. Két lehetőség maradt, és **nem tudom eldönteni, melyik**:

1. az indexem egy közvetett (`call dword ptr [IAT]`) hívási helyet
   **kihagyott** a `W` változatnál (a `FindNext…` kettőjét megtalálta,
   tehát nem elvi korlát);
2. a fogantyúk **máshonnan** származnak (öröklés, más modul, `LoadLibrary`).

Amit végigpróbáltam: a `0x004e1890` (1744 bájt, a másik `FindClose…`-hívó,
a legvalószínűbb „figyelőhalmaz újraépítése" jelölt) **teljes**
diszasszemblálása — a benne lévő három közvetett hívás `[0xc40368]`
(`FindClose…`) és kétszer `[0xc40560]` (egybájtos karakterosztály-vizsgálat,
`cmp eax, 0xff`), **nincs köztük `FindFirst…`**; továbbá a `0x004e1xxx`
függvénylista átnézése.

#### ⛔ MEGDŐLT: az „1. lehetőség (az index kihagyott egy hívást)" — TELJES .text-PÁSZTÁZÁS (2026-08-30)

A teljes `.text` szekció gépi átpásztázása (capstone, **2 887 292 utasítás**,
`call`-operandusok céljaira szűrve) a négy hívás-családra:

| cél | találatok | hol |
|---|---|---|
| `[0xc404d0]` (FindFirstW-feloldó) | **1** | `0x009b3077` — **a CRT A→W-burkoban** (`0x009b3000`) |
| `0x009b3000` (a burok maga) | **0** — senki nem hívja | — |
| `[0xc403c0]` (FindNext-feloldó) | 2 | `0x00706647`, `0x007066c6` (a két ismert) |
| `[0xc40368]` (FindClose-feloldó) | 1 | `0x004e18ba` (az ismert) |

⇒ **Az index nem hagyott ki semmit:** a `FindFirstChangeNotificationW`
egyetlen hívása a CRT-burkoban van, a burkot pedig **a teljes `.text`-ben
senki sem hívja**. (A `0xc403xx`-feloldók szintén ott vannak; a
`call dword ptr [cím]` alakú hívásokon kívül regiszter-közvetítésű
indirekt hívás nem lehetséges az importált API-khoz — a `WaitForMultipleObjects`
hívásai `[0xc4039c]`-en mennek, az is közvetlen formájú.)

**Következmény:** a fogantyú-tömböt (`[this+0x18]`, `[this+0x1c]`) a `.text`-beli
kód **nem tölti fel** — nincs `FindFirst…`-hívás, ami a tömböt megtöltené. A
`WaitForMultipleObjects` számlálója (`[this+0x1c] >> 1`) üres tömbnél **0**, a
`FindNext…`-újrafegyverzés csak a `WAIT_TIMEOUT`-on kívüli, **jelzett**
fogantyúra futna — jelzett fogantyú pedig nem létezik.

**Tehát a „minden futásban él-e a figyelő" kérdésre a válasz az eddigi
legjobb bizonyítékkal: NEM jön létre a fő EXE-ben** — a 16.1 „az eredeti
nem használ OS-szintű fájlfigyelést" iránya a bizonyítékkal **erősödik**
(igaz, a `FindNext…`/`FindClose…` KÓD benne van a binárisban: öröklött
kód, ami nem kap fogantyút, vagy a fogantyúkat más modul hozza létre —
utóbbihoz pl. a `plugins/` DLL-ek vizsgálata kellene, ami a fő EXE
`GetProcAddress`-feloldásain túl egy külön kör, és a mi megvalósításunkat
nem érinti).

*Bizonyítottsági fok a frissítéssel: **megerősített** a `FindFirst…` hívás
hiányára (a teljes `.text` gépi pásztázása); **nyitva marad** a fogantyúk
más modulból való esetleges származása (nem érinti a teendőt).*

*Bizonyítottsági fok: **megerősített**, hogy a `FindNext…`/`FindClose…`
alkalmazáskódból hívódik és hogy a `0x007065f0` újrafegyverez.
**Eldöntetlen**, hol jön létre a fogantyú, és ezért az is, hogy a figyelő
**minden** futásban él-e.*

#### Amit ez a 16.3 következtetésén NEM változtat

A #1275-re adott teendő (**időzített újraolvasás**, az esemény *mellett*)
**érvényben marad** — sőt a 16.4 megerősíti: az eredeti maga is
**mindkettőt** csinálja. Csak a *premissza* dőlt meg („nincs esemény"),
a *javaslat* nem.

### 16.5 LEZÁRVA — a fogantyú létrehozási helye megvan, a szűrő `0x17`, REKURZÍV (2026-08-24)

A 16.4 nyitva hagyta, hol jön létre a változás-értesítő fogantyú. A választ
egy **nyers bájtkeresés** adta meg, ami immunis a diszasszemblálás
elcsúszására: az importált függvény IAT-rekeszének **minden** `.text`-beli
előfordulását megkerestük, nem csak a `call dword ptr [rekesz]` alakot.

#### A hiányzó láncszem: futásidejű A/W választó

A hívás **nem közvetlenül** az importon át megy, hanem egy
**függvénymutató-változón** (`0xd694fc`) keresztül, amit egy platform-váltó
tölt fel induláskor (`0x00c32f94`–`0x00c32fbf`):

```
call [0xc40450]                     ; platform-lekérdezés
cmp  [0xd6fc58], 0x80000000
jae  0xc32fb5
    mov [0xd694fc], 0x9b3000        ; NT: az A→W burok (0x009b3000)
    ret
0xc32fb5:
    mov eax, [0xc404d8]             ; Win9x: közvetlenül a ...A import
    mov [0xd694fc], eax
```

**Ezért nem találta meg sem az index, sem a `FF 15` mintakeresés:** a
hívási hely operandusa nem az API rekesze, hanem ez a változó.

#### A létrehozás — `0x007062b9`

```
0x007062b2  push 0x17                 ; dwNotifyFilter
0x007062b4  push 1                    ; bWatchSubtree = TRUE   ← REKURZÍV
0x007062b6  push eax                  ; lpPathName
0x007062b7  call dword ptr [0xd694fc] ; FindFirstChangeNotification
0x007062bd  mov  esi, eax
0x007062bf  cmp  esi, -1              ; INVALID_HANDLE_VALUE
```

**A szűrő `0x17` bitenként:**

| bit | érték | jelentés | be? |
|---|---|---|---|
| `FILE_NOTIFY_CHANGE_FILE_NAME` | `0x01` | fájl létrejön/törlődik/átnevezik | ✅ |
| `FILE_NOTIFY_CHANGE_DIR_NAME` | `0x02` | mappa létrejön/törlődik | ✅ |
| `FILE_NOTIFY_CHANGE_ATTRIBUTES` | `0x04` | attribútum változik | ✅ |
| `FILE_NOTIFY_CHANGE_SIZE` | `0x08` | méret változik | ❌ **NINCS** |
| `FILE_NOTIFY_CHANGE_LAST_WRITE` | `0x10` | **utolsó írás ideje** | ✅ |

A teljes figyelő-modul a `0x00706xxx` tartományban ül: létrehozás
`0x007061c0`-ban (1061 bájt), várakozás+újrafegyverzés `0x007065f0`
(időkorláttal) és `0x00706680` (lekérdező, nulla időkorláttal), bontás
`0x004e17f0` / `0x004e1890`.

#### ⚠️ Ez MEGCÁFOLJA a 16.4-ben tett saját helyesbítésemet is

A 16.4 azt írta, hogy a `W` változatot „csak a CRT-burok hívja — amit
viszont senki", és ebből azt, hogy eldöntetlen, él-e a figyelő. **Ez téves
volt:** a burkot a platform-váltó **köti be** a `0xd694fc` mutatóba, és
onnan hívódik. A figyelő **él**.

Ezzel egyidejűleg **igazolódik** a `src/picasapy/ini/photo_touch.py`
fejlécének első tényállítása („a szűrőben benne a `LAST_WRITE` bit,
rekurzívan"), amit a 2026-08-24-i első körben tévesen
„nem ellenőrizhetőnek" minősítettem. Egy korábbi kör ezt **helyesen**
mérte ki; az én két leszámlálásom volt hibás.

**Módszertani tanulság, a következő körnek:** importált API hívási helyeit
**ne** csak a `call dword ptr [IAT]` alakra keresd. Három elrejtő alak van,
mindhárom előfordul ebben a binárisban:
`mov reg,[IAT]` + `call reg` (`0x004e1807`), a platform-váltó
függvénymutató (`0xd694fc`), és az A→W burok. A megbízható módszer az
IAT-rekesz **minden** `.text`-beli 4 bájtos előfordulásának keresése.

*Bizonyítottsági fok: **megerősített** — nyers bájtkeresés a teljes
`.text`-en (elcsúszás-mentes) + a hívási hely diszasszemblálása.*

### 16.6 Nálunk (megvalósítva, #1275 + #1435)

A 16.3 következtetése — **az esemény gyorsítás, a lekérdezés a garancia** —
két lépcsőben épült be.

| réteg | mit fed le | hol |
|---|---|---|
| inotify-figyelő (watchdog) | minden esemény, HELYI lemezen | `scanner/watcher.py` |
| kiválasztott mappa újraolvasása, 10 mp | új / törölt / **helyben átírt** fájl | `app/library_controller.py::_poll_current_folder` |
| feed többi mappája, körbeforgó pecsét | új / törölt fájl, ini-változás | `app/folder_freshness.py` (#1435) |
| teljes rescan, 5 perc | a fa egésze | `LibraryMixin.rescan` |

#### Amiben az eredeti TÖBBET tud nálunk — és miért nem baj

A `0x17` szűrőben benne van a `FILE_NOTIFY_CHANGE_LAST_WRITE` bit, tehát
az eredeti **értesítést kap a helyben átírt fájlról is**. A mi
inotify-figyelőnk ugyanezt megkapja — de **csak helyi lemezen**. Hálózati
megosztáson (a tulajdonos NAS-a) egyik sem kap eseményt, és ott a
lekérdezés marad.

⚠️ **Lemért korlát (#1435):** a helyben átírt fájl a mappa mtime-ját NEM
lépteti (a könyvtárbejegyzés változatlan), ezért

- a **inkrementális** 5 perces rescan kihagyja a mappát (`_make_skip`), és
- a #1435 olcsó pecsétje (mappa-stat + ini-stat) sem látja.

Ezt az esetet hálózati megosztáson jelenleg **csak a kiválasztott mappa**
tízmásodpercenkénti teljes újraolvasása fedi le. A feed többi mappájában
helyben átírt fájl a következő `incremental=False` teljes syncig elavult
marad. Ez tudatos csere: a teljes újraolvasás **fájlonként** ~2 művelet
(mérés), a pecsét **mappánként** 2–3 — a NAS mért 200/mp korlátja mellett
a látszó mappák sűrű teljes újraolvasása valódi kárt okozna.

#### ⚠️ Buktató, amibe a #1435 első köre beleesett

A pecsétnek **bitre ugyanúgy** kell készülnie, mint a tárolt állapotnak
(`scanner/walker.py::_ini_mtime`), különben az érintett mappa pecsétje
soha nem egyezik, tehát **minden körben** megkapja a drága teljes
újraolvasást, és **sosem konvergál** — épp azt a NAS-terhelést okozva,
amit a mechanizmus el akar kerülni.

Konkrétan: az ini-fájlnak **két** neve van (`.picasa.ini`, és a régi
verziók `Picasa.ini`-je, ld. `picasa-ini-format.md`). Az első kör csak az
elsőt nézte. Ezért a pecsét a **második nevet is** megpróbálja (ettől lesz
a felső korlát 3 művelet, nem 2), és őr-teszt rögzíti, hogy a szinkron
után egyik ini-változat mellett sem marad elavult a mappa.

## 17. Az OK MENTÉSI ÚTJA — a 12.1 pont lezárása (2026-08-24)

A 12. lista 1. pontja azt kérte, ami a rádiógombtól a fájlkiíróig vezet.
Az út végigkövetve, és **a 12.1 pont saját függvény-felsorolása helyesbítésre
szorul**.

### 17.1 A lánc

```
CFolderMgrDialog OK-kezelő  (0x007c4df0, 2611 b)
 │   RTTI-igazolás: a függvény hivatkozza a
 │   "CFolderMgrDialog::confirmfrexclude" sztringet
 │
 ├─ mappánkénti ciklus a függőben lévő listán
 │     tömb  [dlg+0x2a8] · darabszám [dlg+0x2ac]
 │     0x00492e40(lista, elem)  → index vagy -1  („benne van-e")
 │     0x005088f0(elem, lista)  → listaművelet (a 0x005094c0 keresővel)
 │     két PISZKOS-jelző:  [esp+0x11]  és  [esp+0x12]
 │
 ├─ a két jelző a 0x007bfec0 hívásait kapuzza
 │     ⚠️ a 0x007bfec0 NEM fájlkiíró (ld. 17.3)
 │
 └─ 0x005cef20 (1679 b) — A TÉNYLEGES MENTÉS, hat argumentummal
        (dlg+0x268, dlg+0x270, dlg+0x280, dlg+0x288, ebx, dlg+0x298)

        0x005cf49b   0x004f5960(ebx)      → watchedfolders.txt
        0x005cf500   0x004b9200(…)        → ]album:removed sírkő
                                            (forrás: [dlg+0x2c0])
        0x005cf529   0x00491210(a, b, c)  → 0x004f5d90 → frexcludefolders.txt
                     kapuzva: a KÉT lista bármelyike nem üres
                     ([esp+0x50]+4 vagy [esp+0x54]+4 ≠ 0)
        0x005cf535   0x0065b840(dlg,0,0,1) → záró lépés
```

### 17.2 Negatív eredmény: a `scanlist.txt` innen NEM íródik

A `scanlist.txt` két kezelője (`0x004f61c0`, `0x004f6380`) **kizárólag**
a `0x004f54b0` és a `0x004183c0` felől hívódik — a Mappakezelő
párbeszédéből **nem érhető el**. Az OK tehát **két** listafájlt ír
(`watchedfolders.txt`, `frexcludefolders.txt`) és a sírköveket, nem hármat.

### 17.3 ⚠️ HELYESBÍTÉS a 12.1 ponthoz

A 12.1 három függvényt nevezett meg kiíróként:
`0x005cef20` / `0x007bfec0` / `0x005088f0`. **Csak az első ír fájlt.**

| függvény | amit a 12.1 mondott | ami valójában |
|---|---|---|
| `0x005cef20` | kiíró | ✅ **igen** — ez a mentés |
| `0x007bfec0` | kiíró | ❌ **zárolt listaművelet**: rekurzív kritikus szakasz (`[obj+0x68]`, tulajdonos-szál `+0x20`, rekurziószám `+0x24`), `EnterCriticalSection` (`[0xc4055c]`); **egyetlen fájlműveletet sem tartalmaz** |
| `0x005088f0` | kiíró | ❌ **listaművelet** a `0x005094c0` keresővel; a lista darabszáma `[lista+4] >> 1` |

### 17.4 Ami a `frexcludefolders.txt` KÉT listájából következik

A `0x00491210` **három** argumentumot kap, és a hívás akkor fut le, ha a
**két** átadott lista bármelyike nem üres. Ez egybevág a lap korábbi
mérésével, hogy a fájl **előjeles** sorformátumot használ (`+%s\n` /
`-%s\n`): a két lista a **hozzáadandó** és az **eltávolítandó** mappák.

*Bizonyítottsági fok: **megerősített** a hívási lánc és a sztring-kötések
(`watchedfolders.txt` → `0x004f5960`, `frexcludefolders.txt` →
`0x004f5d90`, `]album:removed` → `0x004b9200`) — mind sztring-xref és
diszasszemblálás. **Erős, nem megerősített**: hogy a két frexclude-lista
melyike a `+` és melyike a `−` előjelű (a formátumsztringek a hívott
függvényben vannak, nem a hívóban). **Következtetett**: a `0x005088f0`
pontos szemantikája (eltávolítás vs. csak keresés).*

### 17.5 Nálunk (megvalósítva, #1334)

A mentési út a `app/folder_manager_save.py`-ban él (sorrend + kapu, Qt
nélkül), a bekötése a `app/library_controller.py`-ban: a párbeszéd OK-ja
zárójelbe teszi a tételes vezérlőhívásokat
(`beginFolderManagerSave` … `commitFolderManagerSave`), a zárójelen belül
csak a szándék gyűlik, és a végén EGYSZER íródik minden — a mért
sorrendben. Őrök: `tests/app/test_mappakezelo_mentes_1334.py`.

⚠️ **Egy tudatos eltérés.** Nálunk a `scanlist.txt` a HÁROMÁLLAPOTÚ
választó (Keresés mindig / egyszer / Eltávolítás) egyetlen tárhelye, és
a Mappakezelő az egyetlen szerkesztője — a `setFolderManagerState`
tehát továbbra is írja, ha a felhasználó ténylegesen állapotot vált.
A MENTÉSI ÚT nem nyúl hozzá (ezt teszt állítja), de a 17.2 betű
szerinti teljesítése — hogy az OK egyáltalán ne érintse a fájlt —
könyvtár-szintű mentőt kívánna (az eredetiben a `0x004f54b0`), ami
nálunk nincs; enélkül a háromállapotú beállítás elveszne.

## 18. Az ELSŐ INDÍTÁS belépési útja — a 12.4 pont lezárása, NEGATÍV (2026-08-24)

A 12. lista 4. pontja azt kérdezte, melyik kód nyitja meg a párbeszédet az
első indításkor, és ugyanazzal a mód-jelzővel-e. **Nincs külön első-indítási
út.**

### A bizonyíték: a lánc egyetlen pontban szűkül

| lépés | cím | hány hívó |
|---|---|---|
| a párbeszéd **konstruktora** (a három vtable beállítása: `0x00cb81fc`, `0x00cb829c`, `0x00cb82ac` a `0x7c0169`-nél) | `0x007c0130` (1035 b) | **1** — `0x005ce75d` |
| a **megnyitó** | `0x005ce590` (2439 b) | **2** |
| a két hívó | `0x005cbd11` és `0x005cbdd3` | mindkettő a főablak parancs-diszpécserében (`0x005cb990`, 8291 b) |

A keresés **nyers bájtszinten** történt (`E8` + rel32 feloldás a teljes
`.text`-en, plusz a függvénycímre mutató adathivatkozások) — tehát nem
maradhatott ki közvetett hívás.

### A két belépés MÓD-jelzője KÜLÖNBÖZIK

```
0x005cbd0e   push 1     ; mód = 1
0x005cbd10   push ebx
0x005cbd11   call 0x5ce590

0x005cbdd1   push edi   ; mód = 0   (edi a diszpécser elején: xor edi,edi @ 0x005cb9a6)
0x005cbdd2   push ebx
0x005cbdd3   call 0x5ce590
```

⇒ A 10/b.1 két menüs belépési pontja **nem azonos hívás**: az egyik
**1**-es, a másik **0**-s móddal nyit. A mód a `0x005ce590` második
argumentuma.

### Amit ez kimond

> **Az első indításnak NINCS saját kódútja a Mappakezelőhöz.** Ha a
> párbeszéd az első futáskor megjelenik, azt csak úgy teheti, hogy a program
> **elküldi magának a két menüparancs egyikét** — harmadik hívó nem létezik.

**A megvalósításunkra:** nem kell külön „első indítás" ág; elég a két
parancs, és az egyiket induláskor kiváltani, ha a beolvasandó lista üres.
A **mód-jelző különbségét** viszont át kell venni (1 vs 0), mert a két
menüpont nem ugyanaz.

*Bizonyítottsági fok: **megerősített** — a hívási helyek nyers
bájtkereséssel, elcsúszás-mentesen; a mód-értékek diszasszemblálva.
**Nem vizsgáltam**, mit csinál a mód-jelző a `0x005ce590`-en belül — ez
külön kérdés, és nem blokkolja a fenti következtetést.*

## A »Rejtett mappák« JELSZAVA — mérve a binárisból (#1637)

Az eredeti a rejtett mappák gyűjteményét jelszóval védhetővé teszi
(`IDS_PROMPT_HIDDEN_PWD_MESSAGE`, `IDS_WARN_NO_HIDDEN_PWD`). A tárolás
alakja **nem** stílus-kérdés: ettől függ, mit ígérhetünk a felhasználónak.

### A lánc, címekkel

| lépés | cím | mi történik |
|---|---|---|
| jelszó megadása/módosítása | `0x005eb910` (903 b) | „Please enter a password to use for this collection", „Please verify your password", „The passwords did not match." |
| a jelszó feldolgozása | `0x00a4cdd0` | a sztringet és a NUL-ig számolt hosszát adja tovább |
| **a lenyomat** | **`0x00ab3640`** | **MD5** — mind a négy init-konstans egymás után: `0x67452301`, `0xEFCDAB89`, `0x98BADCFE`, `0x10325476` (`0x00ab3667`–`0x00ab367f`); a tömörítő `0x00ab36f0` / `0x00ab37b0` |
| hex-be írás | `0x00a4d420` (330 b) | 16 bájt → **32 karakteres kisbetűs hex**; `push 0x21` (33 = 32 + lezáró), ábécé `0x00cd8f5c` = `"0123456789abcdef"` |
| tárolás | `0x005ebc52` | a kapott sztring a `state` (`0x00c817f0`) / `info` (`0x00c812cc`) kulcs alá kerül |

Az ellenőrző ág külön él: `0x005ec440` és `0x004ab650`
(„Please enter a password to open this collection", `CAlbumState::passprompt`).
A rejtett mappák felajánlását a `0x005ee2a0` végzi (`DoNotConfirmHiddenPwd`,
„Don't Add Password" / „Add Password", és a
„The »Hidden Folders« collection is not currently password protected." szöveg).

⇒ **A tárolt érték a jelszó hex-kódolt MD5-e.** Nem nyílt szöveg és nem
elfedés — de **sózatlan**, tehát mai mércével gyenge: azonos jelszó azonos
lenyomatot ad, és az MD5 gyors, így a nyers erő olcsó.

### Amit ez a védelem NEM ad

A rejtett mappák a lemezen **változatlanul ott vannak**, bármelyik
fájlkezelővel elérhetők. A jelszó a program felületén belüli
**megjelenítést** kapuzza, nem a fájlokat. Aki ezt nem mondja ki a
felhasználónak, valódi adatvédelmet ígér ott, ahol nincs.

### Ami NINCS mérve

- **Hol perzisztálódik** a `state` / `info` érték: a tulajdonos valódi
  adatbázisában (302 `.pmp`) **nincs** jelszó-oszlop, tehát ez külön keresés.
- **Milyen kódolással** megy a nem ASCII jelszó az MD5-be: a hossz NUL-ig
  számolódik (`0x00a4cdd0`), tehát bájtsorozatról van szó, de a kódolás nem
  igazolt. ASCII jelszónál ez közömbös; ékezetesnél a kompatibilitás nem
  bizonyított.
- **Elfelejtett jelszó**: van-e az eredetiben visszaállítás.

*Bizonyítottsági fok: **megerősített** — a négy MD5 init-konstans és a
hex-ábécé közvetlenül olvasva, a hívási lánc diszasszemblálva. A tárolás
HELYE és a nem ASCII kódolás: **nem vizsgálva**, ld. fent.*

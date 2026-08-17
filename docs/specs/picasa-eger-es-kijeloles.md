# Egérműveletek, kijelölés és kattintás-viselkedés a Picasában (2026-08-17)

Ez a lap azt írja le, **mi történik kattintásra** a Picasa felületén: mely
vezérlők sülnek el lenyomásra, hogyan viselkedik a kijelölés a
bélyegkép-rácson, mit csinál a Ctrl és a Shift, és hol vannak a húzható,
ismétlő vagy kurzort váltó elemek.

Források: `runtime/respack.yt` 140 `.tre` viselkedés-leírása,
`Picasa3.exe` (RTTI, importtábla, célzott visszafejtés).

---

## 1. A `.tre` interakciós szótár — mind a 65 tulajdonság

A Picasa felülete **deklaratív**: a `.tre` fájlok nemcsak az elrendezést,
hanem a **viselkedést** is leírják. Az alábbi tulajdonságok fordulnak elő
interakcióhoz kötve.

### 1.1 Elsülés és állapot

| tulajdonság | db | mit jelent |
|---|---:|---|
| **`mousedown 1`** | **49** | **lenyomásra sül el, nem felengedésre** |
| `setpressed 0/1` | 30 | a gomb lenyomott/bekapcsolt állapotban indul |
| `setautorepeat 1/5` | 7 | nyomva tartva **ismétel** (az `5` gyorsabb ütem) |
| `escapekey 1` | 11 | az **Esc** billentyű is elsüti |
| `disable 1` | 3 | letiltva indul |
| `setvisible 0` | 3 | rejtve indul |

### 1.2 Találat (hit-test) és kurzor

| tulajdonság | db | mit jelent |
|---|---:|---|
| `hitchildren 1` | 15 | a **gyerekelemek is** találhatók (nem nyeli el a szülő) |
| `hitbox 1` | 1 | a teljes doboz találati felület |
| `normalcursor 1` | 16 | **marad a nyíl-kurzor** (nem vált kézre) |
| `textcursor 1` | 1 | szövegkurzor (I-alak) |

### 1.3 Más elemek vezérlése — a deklaratív kötések

| tulajdonság | db | mit jelent |
|---|---:|---|
| `hidetarget` | 126 | elsüléskor **elrejt** egy másik elemet |
| `showtarget` | 105 | elsüléskor **megmutat** egy másik elemet |
| `uptarget` | 9 | felengedéskor célzott elem |
| `downtarget` | 1 | lenyomáskor célzott elem |
| `disabletarget` | 4 | letilt egy másik elemet |
| `focustarget` | 4 | fókuszt ad egy másik elemnek |
| `addtofocus` | 21 | fókusz-láncba fűz (Tab-sorrend) |
| `alias` | 7 | **ugyanaz a parancs, másik helyen** (pl. `editpanel/sbutton` = `thumbui/sbutton`) |
| `buddy` | 3 | páros vezérlő (színkerék ↔ csúszka-korong) |
| `prenotify 1` | 2 | a váltás ELŐTT értesít |

### 1.4 Húzás és görgetés

| tulajdonság | db | hol |
|---|---:|---|
| `drag 1` | 2 | `throttle/throttlethumb` — a **görgető csúszka hüvelyk** |
| `slider 0/2/3/5` | 23 | csúszkák |
| `maxrows` | 8 | legördülő lista magassága |
| `handlealphakeys` | 2 | betűleütésre ugrik a listában (`fontfamily`) |

---

## 2. A 49 vezérlő, ami LENYOMÁSRA sül el

Ez a Windows-szabvány ellentéte (ott a gomb felengedésre sül el, és a
lenyomás után elhúzva a kattintás visszavonható). A Picasában a következők
**azonnal**, lenyomásra hatnak:

| csoport | elemek |
|---|---|
| **szerkesztő-fülek** | `editpanel/tab1` … `tab5` |
| **szerkesztő-nézetváltók** | `aa_2up_toggle`, `ab_2up_toggle`, `only_1up_toggle`, `fit`, `1to1` |
| **kép-léptetés** | `oneup/prev`, `oneup/next`, `editoneup/prev`, `editoneup/next` |
| **keresősáv szűrői** | `searchbutton`, `starsearch`, `facesearch`, `moviesearch`, `webview`, `geotagsearch` |
| **jobb oldali fiók kapcsolói** | `thumbui/properties_toggle`, `tags_toggle`, `places_toggle`, `people_toggle` |
| **fejlécsáv** | `headerpanel/play`, `create_movie`, `create_collage`, `select_star`, `sync_options` |
| **szövegformázás** | `edittextpanel/bold`, `italic`, `underline`, `leftalign`, `centeralign`, `rightalign`; `makemoviepanel/bold`, `italic`, `outline` |
| **egyéb** | `thumbui/albumview`, `thumbui/folderviewpopup`, `acquirepanel/sync_options_button`, `add_groups_button`, `compose_mail/ltr`, `rtl`, `compose_share/ltr`, `rtl`, `add_groups_button`, `printpanel/captionoptionsbutton`, `selectprinterbutton` |

**A minta:** ami **nézetet vált vagy menüt nyit**, az lenyomásra hat; ami
**műveletet hajt végre** (Mentés, Mégse, Kollázs létrehozása), az a
szabványos felengedésre.

### 2.1 A mechanizmus a kódban — megerősítve

A `.tre`-parszer (`0x009ca5e0`) a `mousedown` értéket a
`0x009c7800`-on át a csomópont **`+0x35c`** bájtjába írja. Ugyanezt a
mezőt a gomb-csomópont eseménykezelője (`0x00a64050`) **két helyen**
olvassa, két külön ágban:

```asm
; A) a LENYOMÁS ága
0x00a643f8   cmp byte ptr [edi + 0x35c], 0
0x00a643ff   je  0xa6446c            ; ha 0 → nem itt sül el
0x00a64401   ...                      ; ha 1 → ITT sül el

; B) a FELENGEDÉS ága
0x00a64543   push ecx / push eax / push 0x80
0x00a64546   call 0xa63f90            ; TALÁLAT-VIZSGÁLAT (0x80 jelző)
0x00a6454b   test al, al / je …       ; ha a mutató NINCS a gombon → nem sül el
0x00a64556   cmp byte ptr [edi + 0x35c], 0
0x00a6455d   jne 0xa64577            ; ha 1 → már elsült lenyomásra, kihagyja
0x00a6456a   call eax                 ; ha 0 → ITT sül el
```

**Két átvehető szabály:**

1. A `mousedown` **nem ad hozzá** viselkedést, hanem **átteszi** az
   elsülést a lenyomás ágába — egy gomb tehát **soha nem sül el kétszer**.
2. A **felengedés ága találat-vizsgálatot végez** (`0x00a63f90`, `0x80`
   jelző): ha a mutató lenyomás után elhagyta a gombot, **nem sül el**. A
   **lenyomás ágában nincs ilyen ellenőrzés** — ott az elsülés
   visszavonhatatlan. Ez a különbség a `mousedown`-os vezérlők
   „azonnaliságának" ára, és pontosan így kell átvenni.

*Bizonyítottsági fok: megerősített (a mező írása és mindkét olvasása
utasításszinten).*

### 2.2 A tulajdonságok tárolási helye

| `.tre` tulajdonság | csomópont-mező | író |
|---|---|---|
| `mousedown` | **`+0x35c`** | `0x009c7800` |
| `disable` | **`+0x20e`** | a parszer közvetlenül (`0x009cb66d`) |

*(A `+0x20e` mezőt **73 függvény** olvassa — a letiltott állapot tehát
nem egyetlen helyen rajzolódik, hanem minden vezérlőtípus maga kezeli.
Ezért marad nyitott, hogyan néz ki egy letiltott gomb.)*

---

## 3. Módosítóbillentyűk — a pontos modell

```asm
0x0097e4a0   isCtrlDown():
0x0097e4a0     cmp byte ptr [0xd67849], 0     ; globális kapu
0x0097e4a9     xor al, al / ret               ;   ha 0 → HAMIS
0x0097e4ac     push 0x11                      ; VK_CONTROL
0x0097e4ae     call GetAsyncKeyState
0x0097e4b4     shr eax, 0xf / and al, 1
```

A Shift ugyanígy, `0x10`-zel, ugyanazzal a `[0xd67849]` kapuval.

> **A `[0xd67849]` globális kapu**: ha nulla, a program **mindkét
> módosítót lenyomatlannak látja**. Ez a „az ablak nem aktív / a
> billentyűzet nem él" állapot — másolatnál is így kell viselkedni,
> különben egy háttérbe került ablak Ctrl-lel viselkedne.

**Használat:** `GetAsyncKeyState(VK_SHIFT)` 45 helyen, `(VK_CONTROL)` 32
helyen, `(VK_MENU)` 7 helyen. A `GetKeyState` csak **egyszer** — a Picasa
végig az **aszinkron** állapotot kérdezi, tehát a *pillanatnyi* fizikai
billentyűállást, nem az üzenethez tartozót.

---

## 4. A kijelölés-csomópont (`CSelectionNode`)

A rácsos kijelölést a `CSelectionNode` (RTTI, vtable `0x008ad5b4`, **49
bejegyzés**) végzi, a `ytSelectionNode` (30 bejegyzés) leszármazottjaként.

### 4.1 Az elem-rekord mezői

| eltolás | tartalom |
|---|---|
| `[elem+0x59]` | „most változott" jelző |
| `[elem+0x5a]`, `[elem+0x5b]` | horgony / fókusz jelzők |
| **`[elem+0x5d]`** | **KIJELÖLVE** |
| `[elem+0xb4]` | az elem azonosítója (a hívó felé ez megy ki) |

A tároló oldalán: `[this+0x32c]` = az elemek mutatótömbje, `[this+0x330]`
= a darabszám (kettővel osztva használja), `[this+0x390]` = az utolsó
érintett elem azonosítója.

### 4.2 Eseménytábla — 26 esemény

A `0x007199b0` (1951 b) egyetlen `switch`-csel oszt szét; a bájt-térkép a
`0x0071a184`, az ugrótábla a `0x0071a150` címen:

| esemény | ág | mit csinál |
|---:|---|---|
| 1 | `0x00719c37` | (nagy ág — kijelölés-frissítés) |
| 2, 3 | `0x00719ece` | |
| 4 | `0x00719df0` | |
| **5** | `0x00719ace` | **kijelölés-változás** — kiküldi a `"selected"` értesítést |
| 9–13 | `0x007199ec` … `0x00719a44` | mutató-események |
| **13** | `0x00719a44` | **aktiválás** (ld. lent) |
| 21, 23, 26 | `0x0071a077`, `0x0071a090`, `0x0071a0de` | |
| 6–8, 14–20, 22, 24, 25 | `0x0071a141` | **nem kezelt** |

### 4.3 A kattintás pontos szemantikája

A 13. esemény ága (`0x00719a44`), betű szerint:

```c
if (uzenet->flag6C != 0) return;              // szuro
idx = talalat(pont);                          // 0x7194e0
if (idx < 0) return;                          // ures teruletre kattintas
modositó = isCtrlDown() || isShiftDown();     // 0x97e4a0 + VK_SHIFT
elem = elemek[idx];
if (elem->kijelolve && !modositó)             // MAR ki volt jelolve, es nincs modosito
    aktival(elem->azonosito);                 // 0x71b850  ← megnyitas/aktivalas
flag2D2 = 0;  flag2CE = 0;
```

> **Amit ez BIZTOSAN kimond:** az aktiválás (megnyitás) **két feltételhez**
> kötött — az elem **már ki volt jelölve**, és **nincs módosító lenyomva**.
> Ctrl vagy Shift mellett tehát **soha nem aktivál**, csak a kijelölést
> módosítja.
>
> ⚠️ **Amit NEM mond ki:** hogy a 13. esemény egyszeres vagy **dupla**
> kattintás-e. A 26 belső eseménykód jelentése nyitott (ld. lent), ezért
> **nem állítható**, hogy a Picasa egyetlen kattintásra megnyitná a már
> kijelölt képet. A megfigyelhető viselkedés (dupla kattintás nyit) ezzel
> a kóddal is összefér: akkor a „már ki volt jelölve" feltétel egy őr, nem
> a kiváltó ok. **A kérdést az eseménykód-táblázat megfejtése dönti el.**

Az 5. esemény ága (`0x00719ace`) a kijelölés tényleges átállítását végzi,
és a végén egy **`"selected"`** nevű értesítést küld ki (`0xc94970`),
majd a `0x71b810` visszahíváson jelzi a változást.

### 4.4 Billentyűzetes kijelölés-léptetés

```asm
0x00717260   lepes_elore():   Shift?  ->  0x717eb0(+1, !shift)
0x007172a0   lepes_hatra():   Shift?  ->  0x717eb0(-1, !shift)
```

A második argumentum a **„cseréld a kijelölést"** jelző: Shift **nélkül**
igaz (a kijelölés lecserélődik), Shifttel hamis (a kijelölés **bővül**).

---

## 4/b A szerkesztő kijelölő-téglalapja ARÁNYT KÉNYSZERÍT (2026-08-17, #891)

A `ytSelectionDragHandler` 4. slotja (**`0x00a6f450`**, 3488 b) — amit a
`.tre` `Handler selectiondrag` köt a `editpanel/cropselection`,
`redselection` és `addfaceselection` elemhez — húzás közben figyeli a
módosítókat:

```asm
0x00a6fa56  push 0x10 (Shift)  → fld1              → [ebx+0x48] = 1,0
0x00a6fa6f  push 0x11 (Ctrl)   → fld [0xcf4cd0]    → [ebx+0x48] = 1,3333333
0x00a6fa8c  push 0x12 (Alt)    → fld [0xcf3ec4]    → [ebx+0x48] = 1,5
0x00a6faa2  fcomp [ebx+0x48]                        ; 0 → nincs kényszer
0x00a6fadb  call 0xa6f000                           ; alkalmazás
0x00a6fae6  fstp [ebx+0x48]                         ; visszaáll 0-ra
```

A három vizsgálat **egymás után** fut, mindegyik felülírja az előzőt:
**Alt üt Ctrl-t, Ctrl üt Shiftet.** A kényszer **csak a húzás idejére** él.

⚠️ **A szorzó nem abszolút arány**: a `0x00a6ef20` a **kép saját arányára**
szorozza (`[eax+0x10]/[eax]`), majd ahhoz igazítja a téglalapot. Shifttel
tehát a kijelölés **a fénykép arányát** veszi fel, nem négyzetet.

A **27-es (0x1b) eseményre** ugyanez a kezelő **nullázza a téglalapot** és
törli a jelzőit (`0x00a6f481`–`0x00a6f4d7`) — ez a kijelölés-elvetés útja.

> ⛔ **Ez NEM a bélyegkép-rács gumikerete.** A `.tre` szerint a
> `selectiondrag` kizárólag a szerkesztő három téglalapjához van kötve.

## 4/c A billentyűzetes léptetés és a HORGONY (2026-08-17, #892)

A mag: **`0x00717eb0`** (606 b), argumentumai `[ebp+8]` = **irány**
(+1/−1), `[ebp+0xc]` = **„cseréld a kijelölést"** (a hívók a Shift
negáltját adják, `0x0071728c` `sete al`).

```asm
0x00718029  ebx += irány                ; a horgony indexe + irány
0x00718031  ha túlfut → 0x717d10, kilép ; NEM fordul át
0x00718058  cmp byte ptr [ebp+0xc], 0
0x0071805c  je  0x7180a8                ; SHIFT → a leszedő ciklus KIMARAD
0x00718091     [elem+0x5d] = 0          ; egyébként minden korábbi kijelölés le
0x007180d6  [új elem+0x5d] = 1
0x007180da  [this+0x390] = az új azonosítója   ; ← a HORGONY FRISSÜL
```

| mező | jelentés |
|---|---|
| **`[this+0x390]`** | **a horgony** — az utoljára kijelölt elem azonosítója; a kattintás ága is ide ír (`0x00719bb9`) |
| `[elem+0x5d]` | kijelölve |
| `[elem+0x59]` | „ebben a körben változott" |
| `[elem+0x5a]` | elnyomó jelző: ha 1, a `+0x59` nem íródik |

> **A Picasa Shift+nyíl viselkedése ELTÉR az Intézőétől:** nem tartományt
> jelöl a horgonytól, hanem **egyesével bővít**, és **a horgonyt is
> lépteti**.

## 5. Húzás, ejtés, gumikeret

| osztály (RTTI) | vtable | mire |
|---|---|---|
| `ytSelectionDragHandler` | `0x008da768` | **gumikeretes kijelölés** |
| `SelectionDragCreator` | `0x008da754` | a fenti gyártója |
| `ytDragNode` | `0x008e5b9c` | húzható csomópont (**`DoDragDrop`** a 31. slotban, `0x00aa1fb0`) |
| `CSysDragDrop` | `0x008e5c94` | rendszer-szintű fogd-és-vidd |
| `ThumbUIDropper` | `0x0088bbb8` | **a bélyegkép-rács ejtés-fogadója** |
| `DragScaleHandler` | `0x0089b11c` | húzással méretezés (retusálás) |
| `NodeSelectHandler` / `NodeDeselectHandler` | `0x008b9384` / `0x008af3fc` | ki- és leválasztás értesítései |
| `CollageDeselectHandler` | `0x008bf598` | a kollázs-vászon leválasztása |

**`DoDragDrop` egyetlen hívóhelye** `0x00aa1fb0` — tehát a Picasából
kifelé (Explorerbe, más alkalmazásba) **egyetlen** úton lehet húzni.

**`SetCapture` mindössze 2 hívóhely** (`0x00923460`, `0x00a52890`),
`ReleaseCapture` 6 — a program tehát ritkán ragadja meg az egeret; a
húzást a saját csomópont-rendszere követi.

---

## 6. Handler-ek — a tíz viselkedés-kötés

A `.tre`-ben a `Handler <név> <argumentumok>` sor köt egy elemhez egy
kódbeli viselkedést. **Összesen 24 kötés, 10 fajta:**

| handler | db | hol |
|---|---:|---|
| `varbutton` | 11 | `editpanel/fullscreenswitcher`, `thumbui/publishswitcher` — **változó helyű gomb** (argumentuma két eltolás, pl. `publishbottom -105 -212`) |
| **`selectiondrag`** | 4 | `editpanel/redselection`, `cropselection`, `addfaceselection` — **a képre húzott téglalap** (vörösszem, vágás, arc hozzáadása) |
| `textawarecursor` | 2 | `editpanel/previewimage`, `previewimage2` — a kurzor a szöveg fölött vált |
| `keepcentered` | 1 | `editpanel/edittextghost` |
| `multitextnodeselector` | 1 | `editpanel/edittextoverlay` — több szövegdoboz közti választás |
| `dragscale` | 1 | `editpanel/retouchoverlay` |
| `retoucher` | 1 | `editpanel/retouchoverlay` |
| `panelgateway` | 1 | `panelroot/picasatab` |
| **`actascursor`** | 1 | `thumbui/circlecursor` — **egy felületi elem VISELKEDIK kurzorként** (a retusálás körkurzora) |
| **`hsplitoffset`** | 1 | `thumbui/hlistsizer` — **a bal panel és a rács közti húzható elválasztó** |

---

## 7. Ismétlő és kurzort nem váltó vezérlők

**`setautorepeat`** — nyomva tartva ismétel:

| elem | ütem |
|---|---|
| `thumbui/morethumbs`, `thumbui/lessthumbs` | **5** (gyors) |
| `oneup/plusone`, `oneup/minusone`, `editoneup/plusone`, `editoneup/minusone` | 1 |
| `keywords/closebutton` | 1 |

*(A `thumbui/prev` és `thumbui/next` `.tre`-sorai `mousedown 1`-gyel és
`setautorepeat 5`-tel **ki vannak kommentezve** — ezek egy korábbi
viselkedés maradványai.)*

**`normalcursor 1`** — a nyíl-kurzor marad, nem vált kézre (16 elem):
`headerpanel/create_movie`, `create_collage`, `select_star`,
`sync_options`, `websync0`, `websync1` · `faceheaderpanel/websync0` ·
`thumbui/folderviewpopup` · `throttle/pageup`, `throttle/pagedown` ·
`bigslider/bigslider` · `acquirepanel/sync_options_button`,
`add_groups_button` · `compose_share/add_groups_button`, `composeclip`.

**`hitchildren 1`** — a gyerek is található (15 elem): a szerkesztő
**kilenc effekt-csempéje** (`crop`, `redeye`, `enhance`, `picnik`,
`autocolor`, `autolighting`, `horizonadjust`, `edittext`, `retouch`),
a `showtextcheckbox`, a `keywords/closebutton`, és három
`makemoviepanel` jelölőnégyzet.

---

## 8. Az Esc-billentyű — 11 gomb

`Property escapekey 1`: `acquirepanel/acancelbutton` ·
`collagepanel/cancelbutton` · `editpanel/tool_cancel`, `cancel`,
`redeyecancel`, `cropcancel`, `retouchcancel` ·
`edittextpanel/edittextcancel` · `makemoviepanel/cancel` ·
`peoplepanel/manual_cancel` · `printpanel/pcancelbutton`.

Vagyis **minden panelnek van Esc-re kötött Mégse gombja** — a szerkesztő
eszközeinek külön-külön is.

---

## 9. Dupla kattintás

**A `GetDoubleClickTime` NINCS importálva.** A Picasa tehát nem méri maga
a dupla kattintást: a rendszer `WM_LBUTTONDBLCLK` üzenetére támaszkodik
(a `0x00920fa0` ablakeljárás kezeli, a `0x007fde80` és `0x00ab3ff0`
mellett). **A küszöb a rendszerbeállítás** — másolatnál is így kell.

---

## Bizonyítottsági fok

**Megerősített**: a `.tre` tulajdonság-leltár és a 49 `mousedown`-elem (a
fájlok szó szerinti tartalma) · a módosító-billentyű modell és a
`[0xd67849]` kapu · a kijelölés-csomópont eseménytáblája és az „első
kattintás kijelöl, második aktivál" szabály (utasításszinten) · a
`GetDoubleClickTime` hiánya.

**Erős**: a Handler-ek jelentése (a nevük és a hordozó elemük együtt
egyértelmű, de a kódjukat nem követtük végig).

**Nyitott**:

1. **A gumikeretes kijelölés pontos szabálya** — mit tesz a keret
   Ctrl-lel (hozzáad) és Shifttel (tartomány): `ytSelectionDragHandler`
   negyedik slotja, `0x00a6f450`.
2. **A Shift-tartomány horgonya** — a `[elem+0x5a]` / `[elem+0x5b]`
   jelzők szerepe; a `0x00717eb0` (a léptető mag) végigolvasása.
3. **A 26 eseménykód jelentése** — a `WM_*` → belső esemény leképezés; az
   `0x00920fa0` ablakeljárás csak továbbít, a fordítás máshol történik.
4. **A jobbklikk útja** — melyik helyi menü melyik felületrészhez tartozik
   (a `0x005e7c20` és `0x0056c5a0` páros).

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

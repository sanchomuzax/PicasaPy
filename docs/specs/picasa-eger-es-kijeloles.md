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

*Forrás: `editpanel.tre:1124` (`editpanel/sbutton`) · `thumbui.tre:468` (`thumbui/sbutton`).*

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

*Forrás: `throttlethumb_mac.tre:3` (`throttle/throttlethumb`).*

| tulajdonság | db | hol |
|---|---:|---|
| `drag 1` | 2 | `throttle/throttlethumb` — a **görgető csúszka hüvelyk** |
| `slider 0/2/3/5` | 23 | csúszkák |
| `maxrows` | 8 | legördülő lista magassága |
| `handlealphakeys` | 2 | betűleütésre ugrik a listában (`fontfamily`) |

---
## 1/b A motor TELJES tulajdonság-szótára (2026-08-17, #905)

Az 1. szakasz listája a **szállított `.tre` fájlokból** készült. A parszer
(`0x009ca5e0`) kulcsszó-táblája a `.rdata`-ban viszont **teljes**
(fájloffszet 8 898 300 … 8 899 650): **58 `Property` + 13 nyelvi kulcsszó**.

**Nyelvi kulcsszavak:** `Track` · `Edit` · `Zoom` · `Offset` · `Ratio` ·
`XConstraint`/`YConstraint` · `Property` · `break` · `Handler` ·
`Tooltip` · `Help` · `Label` · `Text`.

**Nyolc `Property`-t egyetlen szállított `.tre` sem használ:**

| tulajdonság | korábbi, név-alapú hipotézis |
|---|---|
| `windrag` | az **ablak** húzása a vezérlőnél fogva |
| `textclip` | a szöveg vágása a dobozhoz (a `textwrap` párja) |
| `dither` | színcsökkentéses szórás rajzoláskor |
| `vertslider` | **függőleges** csúszka (a `slider` párja) |
| `enabletarget` | a `disabletarget` ellentéte |
| `multiply` | **szorzó keverés** a csomópont rajzolásánál |
| `alphatest` | átlátszóság-küszöb a **találat-vizsgálathoz** |
| `underlineoffset` | az aláhúzás függőleges eltolása |

> ⚠️ **A `multiply` NEM Glimmer-keverési mód**, hanem `.tre` tulajdonság.
> A kettő könnyen összekeverhető.

*Bizonyítottsági fok: megerősített a szótár teljességére (egyetlen,
összefüggő `.rdata`-tömb) · a nyolc jelentését a következő szakasz a
bináris setterek és fogyasztók alapján pontosítja.*

## 1/c A nyolc, `.tre`-ben nem használt tulajdonság tényleges viselkedése (2026-08-21, #905)

A nyolc kulcsszó a szállított `.tre`-kben valóban nem fordul elő, de a
parszer nem holt névként kezeli őket: a `0x009ca5e0` függvény külön ágat és
settert rendel hozzájuk. A következő táblázat a settert, a közvetlen
fogyasztót és a bizonyítható hatást különíti el; a névből önmagában
következő látványbeli értelmezést nem tekinti bizonyítéknak.

| tulajdonság | bináris út | a bizonyítható hatás | fok |
|---|---|---|---|
| `windrag` | `0x009cb122` → `+0x22e`; eseménykezelő `0x009e5590` | Találatkor a `+0x8c` állapotot törli, az első engedélyezett leszármazotton virtuális `+0x24` műveletet hív, majd `0x00a57680`-n át elengedi a capture-t és a cél akcióját virtuális `+0x18`-on meghívja; kezelt eseményként `0xF4240`-t ad vissza. A `0x00984350`-ben látott közvetlen Windows-méretezés a **`winsize`** ág, nem ez. | erős a vezérlési láncra; feltételes a végső ablak-akcióra |
| `textclip` | `0x009cbd91` → `0x009c7e10` | A csomópont `+0x2f1` bájtjába írja az értéket és a `+0xc` dirty-bitjét beállítja. A teljes közvetlen offset-keresésben további olvasó nem került elő; csak a csomópont-másoló rutin (`0x00a6b9e0`) viszi tovább ezt a bájtot. Szállított `.tre` nélkül tényleges vágási rajzolóág nem bizonyítható. **Ghidra-C (2026-08-30) megerősíti a settert** (`+0x2f1` + dirty); a `multiply` fogyasztó (`0x00a67d40`) a `+0x351`/`+0x350`-et olvassa — az külön jelenség. **A teljes `.text` gépi pásztázása (2026-08-30, 0x2f1-diszplacementre) LEZÁRJA a fogyasztó-kérdést:** 11 találat — az egyetlen OLVASÁS a másolóé (`0x00a6bab0` → `0x00a6bab6` másolás), a két textclip-setter-írás (`0x009c7d96`, `0x009c7e37`), a másoló-cél-írás (`0x00a6bab6`), továbbá `0x007178ab` (másik objektum, film-tartomány) és `0x0085611c` (node-konstruktor, a `+0x2f1` alapértéke **1**). ⇒ a `+0x2f1`-nek a másolón KÍVÜL nincs olvasója — a „nincs vágási rajzolóág" NEGATÍV állítás **megerősített** (a korábban „közepes" fok). | erős a tárolásra; **megerősített** a „nincs fogyasztó” negatív állításra |
| `dither` | `0x009cb5d1` → `0x009c79a0` → `0x009d3d60` | A paramétert `%x`-ként olvassa, alapértéke `0x7F000000`. A setter a `+0x27c` állapotot bekapcsolja, a csomópont `+0x268…+0x274` négy slotjába a packed értékből létrehozott objektumokat teszi, majd virtuális `+0x68` frissítést és gyermek-propagációt indít. A kód ezen az úton nem bizonyít önálló, képpontonkénti ditherelést. | erős a belső hatásra; közepes a végső renderjelentésre |
| `vertslider` | `0x009cb741` → `0x009c7a50` | 12 bájtos `ytVertSliderHandler` példányt foglal, a `ytVertSliderHandler::vftable`-t (`0x00CDA48C`) állítja be, az egynél nagyobb paramétert a handler harmadik slotjába teszi, majd `0x009e4080`-n át a csomópont kezelőlistájára regisztrálja. | erős |
| `enabletarget` | `0x009cadb1` → `0x009c7270` → `0x009c2580` | A célértéket előkészíti (`0x00985ff0`), majd a csomópont célreferencia-tömbjét bővíti és refcountolt pointereit másolja (`+0x3d4`, elemszám/állapot `+0x3d8`). Ez deklaratív célkapcsolat-regisztráció; nem egyszerű, azonnali „enable” hívás és nem a `disabletarget` bitenkénti ellentéte. | erős a tárolási/kapcsolati hatásra |
| `multiply` | `0x009cb911` → `0x009c7b90`; fogyasztó `0x00a67d40` | A csomópont `+0x351` bájtját állítja, eltéréskor dirty-bitet (`+0x8`, `0x2`) jelöl. A renderelő `0x00a67d40` ezen a bájton két külön renderág között választ: nulla esetén a normál, nem nulla esetén az alternatív kompozitálási út fut. Ez a `.tre` renderkapcsoló külön entitás a Glimmer `MultiplyColorMatrix` műveletétől. | erős a renderág-váltásra; közepes a pontos pixelképletre |
| `alphatest` | parser-ág `0x009cba61`; közvetlen írás `0x009cba92` → `ytButtonNode +0x358`; fogyasztó `0x00a64050` | Csak `ytButtonNode` típuson írható. A gomb hit-testje a `+0x358` engedélyezésekor az alpha-maszkot is vizsgálja: `0x00a63f90`-et `0x80` küszöbbel hívja, amely a leképezett bájtot összeveti a küszöbbel. Ez valóban alfa-alapú találatvizsgálat, nem pusztán rajzolási opció. | erős |
| `underlineoffset` | parser-ág `0x009caaa6` → `0x00a6ca10` | A csomópont gyermeklistájában megkeresi az első `ytColorRectNode`-ot, és annak egy négykomponensű, `(1.0, 1.0, float(érték), 0)` alakú struktúráját állítja/használja; eltéréskor a gyermek dirty-bitjét jelöli. A bináris ezen a ponton a color-rect módosítást bizonyítja, az „aláhúzás” végső vizuális szerepét önmagában nem. | erős a belső műveletre; közepes a név szerinti látványra |

**Mérleg:** mind a nyolc kérdés parser- és runtime-szinten megválaszolható
lett. A `textclip`-nél a tárolás bizonyított, de a szállított programban nem
találtunk külön fogyasztót; a `windrag` és az `underlineoffset` végső,
ablak-/rajzszintű látványát a név helyett csak a virtuális célműveletek teljes
dekompilálása tudná tovább szűkíteni. Ez már nem nyitott parser-kérdés, hanem
élő UI-szcenárióval vagy célosztályonkénti további kutatással validálható
finomítás.

## 4/d A vágó-átfedés elsötétítése — `Property negativemode` (2026-08-17, #900)

Öt elem visel `Property negativemode 8f2f2f2f`-et:
`editpanel/cropselection` · `redselection` · `addfaceselection` ·
`faces` · `nav/nav`.

A parszer **hexaként** olvassa, **`0x7F000000`** alapértelmezéssel:

```asm
0x009c79ce  push 0xc82fd4                        ; "%x"
0x009c79d4  mov dword ptr [esp+0x10], 0x7f000000 ; alapértelmezés: fekete, 50 %
0x009c79dc  call 0xc07eef                        ; sscanf
0x009c79eb  call 0x9d3d60                        ; beállítás
```

| összetevő | `8F2F2F2F` |
|---|---|
| alfa | `0x8F` = 143 → **56,1 %** |
| RGB | `#2F2F2F` — **semleges sötétszürke, nem fekete** |

**A kijelölésen kívüli terület tehát nem kioltódik, hanem halványul** — a
levágandó rész kontúrjai olvashatók maradnak.

## 2. A 49 vezérlő, ami LENYOMÁSRA sül el

*Forrás: `acquirepanel.tre:210` (`acquirepanel/sync_options_button`) · `compose_mail.tre:139` (`compose_mail/ltr`) · `compose_share.tre:129` (`compose_share/ltr`) — és további 12 elem ugyanott.*

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
### 2.2 A hét vezérlő, amit CSAK ez a tábla említett — feloldva (2026-09-04, #2093)

A fenti tábla azt mondja meg, **mikor** sül el egy gomb, azt nem, hogy **mit
csinál**. Hét elem csak itt szerepelt az egész specifikációban, ezért a
lefedettségi mérő `feltáratlan`-nak sorolta őket. Az eredeti **saját
felirata és buboréksúgója** viszont megvan — és a projekt szabálya szerint
[a `.tre` szövegforrás az igazságforrás](binaris-regeszet-modszertan.md):
azonosítóból nem következtetünk, ha van hozzá hivatalos felirat.

| elem | hivatalos magyar szöveg | hol áll a `.tre`-ben |
|---|---|---|
| `acquirepanel/sync_options_button` | felirat: **„Opciók"**; buboréksúgó: **„Online opciók"** | `acquirepanel.tre:208` |
| `headerpanel/create_movie` | **„Mozgófilmes prezentáció létrehozása"** | `headerpanel.tre:79` |
| `headerpanel/play` | **„Diavetítés teljes képernyőn"** | `headerpanel.tre:32` |
| `headerpanel/websync0` | **„Feltöltés és a későbbi változások szinkronizálása az internettel"** | `headerpanel.tre:52` |
| `peoplepanel/manual_cancel` | felirat: **„Mégse"** | `peoplepanel.tre:38` |
| `printpanel/captionoptionsbutton` | **„A nyomtatni kívánt fotók szegélyeinek és szövegének beállítása"** | `printpanel.tre:46` |
| `editpanel/weblink` | **„Ugrás az ehhez a fotóhoz társított webhelyre"** | `editpanel.tre:1160` |

**Amit a kód tesz hozzá** (a sztring-xrefek szerint — ezek a függvények a
panelt építik, nem a kattintást kezelik):

| elem | a hivatkozó panel-függvény | mit árul el |
|---|---|---|
| `acquirepanel/sync_options_button` | `0x00518b40` (929 b) | ugyanez a függvény kezeli az `acquirepanel/sync_starred` elemet is ⇒ az „Opciók" a **feltöltési** beállításokat nyitja, köztük a „csak csillagozottak" kapcsolót |
| `editpanel/weblink` | `0x00567a00` (1035 b) | egy csoportban van az `editpanel/quickupload`, `uploadchanges`, `editcollage`, `editslideshow` elemekkel ⇒ a szerkesztő **környezeti műveletsorának** tagja |
| `peoplepanel/manual_cancel` | `0x005d23d0` (1009 b) | az `editpanel/cropselection`, `retouchoverlay`, `edittextoverlay` társaságában ⇒ **átfedés-kezelő** ág; a „Mégse" a kézi arcfelvitelt zárja le |
| `printpanel/captionoptionsbutton` | `0x00743980` (3533 b) | a teljes nyomtatási gombkészlettel együtt (`walletbutton`, `3x5button`, …, `PrintLastSize`) ⇒ a nyomtatási panel saját beállítás-ága — a megvalósítási jegye a **#1780** |

> ⚠️ **Amit ez NEM ad meg:** egyik gomb **kattintás-kezelőjét** sem
> olvastuk ki. A fenti sorok a *felhasználónak látszó* jelentést rögzítik
> (a gyártó saját szövegével) és a panel-hovatartozást — nem a
> végrehajtott kódot. A `headerpanel/create_movie`, `play` és `websync0`
> névre a binárisban **egyetlen sztring-hivatkozás sincs**: azokat a
> fejlécsáv általános, táblavezérelt kezelője kapcsolja.

*Bizonyítottsági fok: **megerősített** a feliratokra és a `.tre`-helyekre
(kiolvasott sorok), **erős** a panel-hovatartozásra (sztring-xref),
**nincs mérve** a kattintás-kezelő.*

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

### 4.2/b Mit JELENTENEK a motor eseménykódjai — viselkedésből (2026-08-18)

A kérdés kétszer akadt el, mert az ablakeljárás felől kerestük
(`0x00920fa0` csak továbbít, és a `[esemény+8]` mezőt nem közvetlen
konstanssal írják). **A harmadik nekifutás megfordította az irányt:** nem
azt kérdeztük, honnan jön a kód, hanem hogy **mit csinálnak rá a
kezelők**.

Gépi vizsgálat: az RTTI-ből mind a **84** `*Handler` osztály 3.
vtable-slotja (az eseménykezelő), és minden kód, ami bennük `cmp`-ben
szerepel.

| kód | hány kezelő | jelentés | mi bizonyítja |
|---:|---:|---|---|
| **1** | 27 | **bal gomb LE** | a `CollageDeselectHandler` erre szünteti meg a kijelölést; a `CollageNodeHandler` erre jelöl ki és indít húzást (`0x00860ad0`) |
| **2, 3** | 24 / 22 | **egérmozgás** — a kettőt minden vizsgált kezelő **azonos ágra** viszi | `0x00860dc6`, `0x008685b4` |
| **4** | 17 | **gomb FEL** | a `RingMoveHandler` itt állítja vissza az átlátszóságot 1,0-ra (`0x008690a3`) |
| **5** | ≥ 2 | **jobb gomb LE → helyi menü** | a `CollageNodeHandler` itt építi a `collagenode_context_*` menüt (`0x00860c5d`) |
| **0x0b** | 1 | **ejtés egy csomópontra** | a két kép cseréje (`0x00860ce7`) |
| **0x13** | 7 | **találat-vizsgálat / kurzorkérés** | téglalapba esést számol, `0xf4241`-gyel tér vissza (`0x00860a31`) |
| **0x1b** | 7 | **elrendezés változott** | a `RingNodeLayoutHandler` itt teszi a gyűrűt a befoglaló téglalap közepére (`0x007e65eb`) |
| **0x1f / 0x20** | 18 / 12 | **belépés / kilépés**, párban | a kezelő eltárolja, majd nullázza a cél-mutatót (`0x008609f9`, `0x00860a12`) |

**A visszatérési értékek is állandóak:** `0xF4240` = *kezeltem*,
`0xF4241` = *nem kezeltem, add tovább*.

**A megfigyelt kódkészlet** (alsó becslés — a pásztázó csak az egyszerű
`mov`+`cmp` mintát követi): 1, 2, 3, 4, 5, 8, 0x0b, 0x0c, 0x0d, 0x0e,
0x0f, 0x11, 0x12, 0x13, 0x17, 0x18, 0x1b, 0x1c, 0x1f, 0x20, 0x21–0x28,
0x2e, 0x41, 0x44, 0x70, 0x80, 0xff.

> ⚠️ **Ez NEM ugyanaz a számozás, mint a 4.2 tábláé.** A 4.2 a
> `CSelectionNode` **saját**, 26 elemű ugrótáblája (`0x0071a150`); az itt
> szereplők a **motor** eseményei, amiket minden `*Handler` megkap.
> A kettőt nem szabad összekeverni: a `CSelectionNode` 5. eseménye
> „kijelölés-változás", a motoré „jobb gomb le".

*Bizonyítottsági fok: **megerősített** a nyolc jelentésre (mindegyikhez
konkrét kezelő-ág tartozik) · **erős** a kódkészletre (alsó becslés).
A `WM_*` → belső leképezés továbbra is ismeretlen — de a jelentések
birtokában **nincs is rá szükség** a megvalósításhoz.*

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

## 4/e A RÁCS lasszójának szabálya: METSZÉS, nem tartalmazás (2026-08-18)

A `picasa-eger-es-kijeloles.md` eddig annyit mondott, hogy a rács lasszója
„más kódúton van". Megvan.

### A lasszó téglalapja (`0x00719f91`, 2./3. esemény)

```
x0 = min(kezdo.x, egér.x)      ; a kezdőpont [ebx+0x27c], [ebx+0x280]
y0 = min(kezdo.y, egér.y)      ;   kerekítve (0x00c29990)
x1 = max(...), y1 = max(...)
ha x0 == x1 → x1 = x0 + 1      ; 0x0071a00b — SOHA nem elfajult
ha y0 == y1 → y1 = y0 + 1      ; 0x0071a012
[ebx+0x29c … 0x2a8] = (x0, y0, x1, y1)
```

### Az elemenkénti teszt (`0x0071bc90`)

Minden elemre kiszámolja a képernyő-téglalapját a pozíciójából
(`[elem+0x88]`, `[elem+0x8c]`) és a méretéből (`[elem+0x3c]`, `[elem+0x40]`),
a `[elem+0x60]` nagyítással szorozva — majd:

```
ix0 = max(elem.x0, lasszo.x0)      ; 0x0071bef7
iy0 = max(elem.y0, lasszo.y0)      ; 0x0071bf05
ix1 = min(elem.x1, lasszo.x1)      ; 0x0071bf0f
iy1 = min(elem.y1, lasszo.y1)      ; 0x0071bf19
ha (ix0 < ix1 ÉS iy0 < iy1)  →  ÉRINTVE               ; 0x0071bf1f–0x0071bf25
```

**Vagyis a lasszó minden olyan elemet megérint, aminek a téglalapja
METSZI a lasszóét** — nem kell, hogy teljesen benne legyen. A metszetnek
**szigorúan pozitív területűnek** kell lennie (érintőleges találat nem
számít).

**Két elem-jelző kizár a tesztből** (`0x0071be19`, `0x0071be26`):
`[elem+0x5a]` és `[elem+0x5b]` — ha bármelyik áll, az elem kimarad.

Ha legalább egy elem érintve lett, a kód **beállítja a „volt húzás"
jelzőt** (`[ebx+0x2d3] = 1`) — ez az, amit a felengedés ága néz, hogy
szűkítsen-e (ld. 4/c és a #897).

*Bizonyítottsági fok: megerősített.*

## 4/f A helyi menük LELTÁRA — melyik menü melyik felületrészé (2026-08-18)

A menük **erőforrásnévvel** épülnek (ugyanaz a minta, mint a kollázsnál).
A binárisból kiszedve, a **birtokló függvénnyel** együtt:

| erőforrásnév | birtokló függvény | felületrész |
|---|---|---|
| `filmstripcontext` | `0x005ba010` | a filmszalag |
| `ThumbUIOutput::AlbumMenu` · `FolderMenu` | `0x00537fb0` | a bélyegkép-rács — **album és mappa KÜLÖN menü** |
| `albumbutton_menu` | `0x005de8e0` | album-gomb |
| `CThumbUI::locatemenu` · `locateondiskmenu` | `0x0056c5a0` | a rács „Megkeresés" almenüje |
| `collagenode_context_single` | `0x0082cb50` | kollázs: **egy** kép |
| `collagenode_context_group` | `0x0082cb50` | kollázs: **több** kép |
| `collagenode_context_document` | `0x0082cb50` | kollázs: a **vászon** |
| `collagenode_context` | `0x0062cda0` | a kollázs-menük gyökere |
| `acquirepanel/delete_menu` · `import_from_menu` | `0x005154f0` | importálás |
| `acquirepanel/subfolder_menu` · `import_folder_menu` | `0x00517f90` | importálás |
| `editpanel/crop_aspect_menu` | `0x005d3290` | a vágó arány-választója |
| `publish/backup_set_menu` | `0x005d3290` | biztonsági mentés |
| `publish/picsizemenu` | `0x0040bf70` | közzététel |
| `uploadsize_menu` | `0x007a0830` | feltöltés |
| `webalbums_menu` | `0x007aa080` | webalbumok |
| `map_menu` | `0x0064e900` | térkép |

**Két tanulság a listából:**

- A **rácsnak két külön helyi menüje van**: `AlbumMenu` és `FolderMenu` —
  ugyanaz a felület, de album- és mappanézetben **más** a menü.
- A **kollázs vászon-menüje `collagenode_context_document`**, és a
  **Többszörös exponálás témánál el van nyomva**: a kezelő
  (`0x0082d3af`–`0x0082d3d0`) lekérdezi a téma kulcsát, és `multiexp`
  esetén **más ágra ugrik**, nem nyitja meg. Ez független megerősítése a
  képesség-maszk 4. bitjének (`multiexp` → nincs kijelölés) — két külön
  kódút mondja ugyanazt.

*Bizonyítottsági fok: megerősített a leltárra és a `multiexp`-elnyomásra.*

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

*Forrás: `editpanel.tre:941` (`editpanel/edittextghost`) · `editpanel.tre:946` (`editpanel/edittextoverlay`) · `editpanel.tre:1401` (`editpanel/fullscreenswitcher`) — és további 7 elem ugyanott.*

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

*Forrás: `editoneup.tre:148` (`editoneup/minusone`) · `editoneup.tre:140` (`editoneup/plusone`) · `keywords.tre:67` (`keywords/closebutton`) — és további 4 elem ugyanott.*

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

**Nyitott** — *ez a lista 2026-08-20-án ÜRESRE fogyott; a négy egykori
tétel mind meg van válaszolva, a hivatkozás azért marad, hogy a következő
kör ne induljon el újra ugyanezen:*

1. ~~**A gumikeretes kijelölés pontos szabálya**~~ — **MEGVAN**: a
   `ytSelectionDragHandler` (`0x00a6f450`) a **szerkesztő** téglalapjaié és
   arányt kényszerít (4/b, #891); a **rács** lasszója külön kódúton van, és
   **metszés-teszttel** dolgozik (4/e), pillanatfelvétellel (#897).
2. ~~**A Shift-tartomány horgonya**~~ — **MEGVAN** (4/c, #892): a horgony a
   `[this+0x390]`; a `[elem+0x5a]` elnyomó jelző (kizár a lasszóból és a
   kijelölésből is), a `[elem+0x5b]` a fókusz-jelző. A `0x00717eb0` teljes
   olvasata a **12.2**-ben (üres kijelölésnél az első/utolsó elemre lép).
3. ~~**A 26 eseménykód jelentése**~~ — **a gyakorlathoz elég megvan**
   (4.2/b): nyolc kód megerősítve a kezelők viselkedéséből. A `WM_*` →
   belső leképezés továbbra sincs meg, de a megvalósításhoz nem kell.
4. ~~**A jobbklikk útja**~~ — **MEGVAN** (4/f): tizenhat helyi menü
   erőforrásneve a birtokló függvénnyel; a rácsnak album- és mappanézetben
   külön menüje van.

---

## 10. A kijelölés HATÓKÖRE: EGY mappa, soha nem a könyvtár (2026-08-20)

Ez a szakasz a lap eddigi legnagyobb hiányát pótolja: eddig leírtuk, **hogyan**
jelöl ki a Picasa, de nem azt, hogy **min**. A válasz megváltoztatja a
Ctrl+A, a Shift-tartomány, a lasszó és a Home/End értelmezését is.

### 10.1 A könyvtárnézet: `CMultiAlbumNode` — mappánként EGY kijelölés-csomópont

A könyvtár („lightbox") bélyegkép-területe a **`CMultiAlbumNode`** osztály
(RTTI-vtábla `0x00cb29d4`). Ez **albumsorok listája**, és **minden sornak
saját `CSelectionNode`-ja van**:

```asm
; a könyvtárnézet Home-kezelője (0x0076a390), a nem-Ctrl ág
0x0076a3b5  mov eax, [esi + 0x2e0]      ; a JELENLEGI album sorindexe
0x0076a3bb  cmp eax, -1
0x0076a3c0  mov ecx, [esi + 0x300]      ; az albumsorok tömbje
0x0076a3c6  mov eax, [ecx + eax*4]      ; a jelenlegi sor
0x0076a3d5  mov esi, [eax + 0x2b4]      ; ← A SOR SAJÁT kijelölés-csomópontja
0x0076a3ea  call 0x718880               ; a Home logikája EZEN a csomóponton
```

| mező | tartalom |
|---|---|
| `CMultiAlbumNode + 0x2e0` | a **jelenlegi** album sorindexe (−1 = nincs) |
| `CMultiAlbumNode + 0x300` | az albumsorok mutatótömbje |
| `albumsor + 0x2b4` | **a sor saját `CSelectionNode`-ja** |
| `CSelectionNode + 0x3c0` | **annak az albumnak/mappának az azonosítója**, amelyikhez a csomópont tartozik |

### 10.2 A `CThumbUI` a JELENLEGI mappa csomópontjára mutat

A `CThumbUI` négy csomópont-mutatót tart: `+0xea0` (a görgető,
`thumbui/albumscroll`), `+0xea4`, `+0xea8` és **`+0xeac`** — ez utóbbi
**a fókuszban lévő mappa/album kijelölés-csomópontja**.

A váltó (`0x0056bc10`) — a „másik mappára került a fókusz" útvonal:

```asm
0x0056bc30  cmp esi, [edi + 0xea4]
0x0056bc36  je  0x56bc43
0x0056bc38  mov edx, [edi + 0xea8]
0x0056bc3e  call 0x718a50               ; ← AZ ELŐZŐ CSOMÓPONT KIJELÖLÉSE TELJESEN LE
...
0x0056bca4  mov esi, [ebx + 0x3c0]      ; az ÚJ csomópont album-azonosítója
0x0056bcac  call 0x56b910               ; „a jelenlegi album megváltozott"
0x0056bd43  mov [edi + 0xeac], ebx      ; ← az új mappa csomópontja lesz a jelenlegi
0x0056bd8c  call 0x537fb0               ; a helyi menük (Album/Folder) újraépítése
```

És a takarító ág (`0x00662b20`), ami akkor fut, ha a nézet listája változik:

```asm
0x00663122  mov eax, [ebp + 0xeac]
0x0066312c  mov eax, [eax + 0x3c0]      ; a csomópont album-azonosítója
0x00663139  call 0x4af790               ; benne van-e még a nézetben?
0x0066313e  cmp eax, -1
0x00663152  call edx                    ; ha NINCS → elengedi
0x00663154  mov [ebp + 0xeac], ebx      ; és nullázza
```

> **Két, egymástól független kódút mondja ki ugyanazt:** a kijelölés-csomópont
> **egyetlen mappához/albumhoz tartozik**, és amint a fókusz átkerül egy másik
> mappára, **a régi mappa kijelölése megszűnik**. A Picasában **nem lehet
> mappákon átnyúló kijelölés** — se kattintással, se Shifttel, se Ctrl+A-val,
> se lasszóval.

*Bizonyítottsági fok: **megerősített** (utasításszinten, két kódút).*

### 10.3 Ebből következik minden más hatóköre

A `CSelectionNode` minden művelete a **saját** elemtömbjén (`+0x32c`,
darabszám `+0x330 >> 1`), illetve a vtábla `+0xb4` (darabszám) / `+0xb8`
(i-edik elem) párosán jár:

| művelet | függvény | hatóköre |
|---|---|---|
| Ctrl+A (Összes kijelölése) | `0x00716f40` | a jelenlegi mappa |
| Ctrl+D (Kijelölés törlése) | `0x00718a50` | a jelenlegi mappa |
| Shift+kattintás tartomány | `0x0071bae0` → `0x00716ae0` | a jelenlegi mappa |
| Shift+Home / Shift+End | `0x00718880` / `0x00718930` → `0x00716ae0` | a jelenlegi mappa |
| lasszó | `0x0071bc90` | a jelenlegi mappa |
| nyilak, Shift+nyíl | `0x00717eb0` | a jelenlegi mappa |

---

## 11. A kijelölés-parancsok: az azonosítótól a kódig (2026-08-20)

### 11.1 A menütételek rekordja

A menüket felépítő függvények (a menüsáv `0x00559150`, a mappa-menü
`0x007319f0`, az album-menü `0x00732160`, az Emberek-menü `0x007359e0`)
**20 bájtos rekordokat** töltenek ki:

| eltolás | tartalom |
|---|---|
| `+0x00` | a honosított felirat (`0x009ae560(kulcs, alapértelmezés)` eredménye) |
| `+0x04` | a **gyorsbillentyű betűje** külön C-sztringként (`"A"`, `"D"`, `"I"`, `"X"`, `"C"`, `"V"`) |
| `+0x08` | 16 bites jelzőmező |
| **`+0x0a`** | **16 bites parancsazonosító** |
| `+0x0c`, `+0x10` | további mezők (a szállított menükben 0) |

⚠️ **Fordítói csapda:** a rekord `+0x04…+0x0a` mezőit a fordító a
**következő** menütétel blokkjában írja ki. Aki blokkonként olvassa a
diszasszemblált kódot, **eggyel elcsúszva** párosítja a feliratot az
azonosítóhoz. A globális címekkel dolgozó menüsáv-építőben
(`0xd6db80`-tól) a rekordhatárok egyértelműek, és a `+0x04` gyorsbillentyű-
betű (`"A"` a Ctrl+A-hoz) **független ellenőrzést** ad.

### 11.2 A négy kijelölés-parancs

| menütétel | erőforráskulcs | azonosító | kezelő | mit hív |
|---|---|---:|---|---|
| **Az összes kijelölése** (Ctrl+A) | `…ID_ALBUM_SELECTALLPICTURES` | **`0x9cb8`** | `0x005e5070` | `0x00716f40([this+0xeac], 1)` |
| **Kiválasztás megfordítása** (Ctrl+I) | `…ID_SELECT_INVERT` | `0x9c47` | — | — |
| **Kijelölés törlése** (Ctrl+D) | `…ID_CLEAR_SELECTION` | **`0x9c90`** | `0x005e5310` | `0x00718a50([this+0xeac])` |
| **Csillagozottak kijelölése** | `…ID_SELECTSTAR` | `0x9d5b` | — | — |

A parancs-szétosztó a `0x005cb990`: `lea eax,[esi-0x9c42]` → bájttérkép
(`0x005cdb34`) → ugrótábla (`0x005cd9fc`). A `0x9cb8` a 118. bejegyzés,
onnan a 39. ágra (`0x005cbcec`) megy, ami a `0x005e5070`-t hívja.

> **A parancs neve maga is beszédes:** a menüsáv „Az összes kijelölése"
> tétele **ugyanazt az `ID_ALBUM_SELECTALLPICTURES` azonosítót** használja,
> mint a mappa- és album-helyimenü „Az összes kép kijelölése" tétele. Egy
> parancs van, és az **album/mappa** hatókörű.

### 11.3 A „mindent kijelöl" mag — `0x00716f40`

```c
void SetAllSelected(CSelectionNode *this /*edi*/, bool ertek /*bl*/) {
    int elso = -1;                                  // esi
    for (i = 0; i < this->count /*[+0x330]>>1*/; ++i) {
        elem = this->items[i];                      // [+0x32c]
        if (elem == NULL) continue;
        if (elem->flag5A == 0) {                    // nem elnyomott elem
            if (elso == -1) elso = elem->id;        // [+0xb4]
            if (elem->selected != ertek && elem->flag5A == 0)
                elem->changed /*+0x59*/ = 1;
            elem->selected /*+0x5d*/ = ertek;
        } else {
            if (elem->selected != 0) elem->changed = 1;
            elem->selected = 0;                     // elnyomott elem SOHA nem lesz kijelölt
        }
    }
    if (ertek != 0) this->anchor /*[+0x390]*/ = elso;   // a horgony az ELSŐ elem
    for (k = 0; k < this->observerCount /*[+0x320]>>1*/; ++k)
        this->observers[k]->vt[1](this);            // EGYETLEN értesítés-kör
}
```

**Ez a teljes ára a Ctrl+A-nak az eredetiben:** egy menet az elemtömbön, egy
értesítés-kör, majd a hívó (`0x005e5070`) **egyetlen** teljes-felület
érvénytelenítése (`0x00a54b70(this, 1, 1, 0.0, {-1,-1,-1,-1}, 1)`).
**Elemenkénti jelzés, elemenkénti lekérdezés, elemenkénti fájlművelet
NINCS.**

### 11.4 A tartomány-mag — `0x00716ae0`

A Shift+kattintás, a Shift+Home/End és a „jelöld ki az egészet" idióma
mind ezt hívja: `0x00716ae0(node, idA, idB, ertek)` — **stdcall, 4
argumentum**, opcionális kimeneti tömb `esi`-ben.

```c
bool tartomanyban = false;
for (i = 0; i < node->count(); ++i) {          // vtábla +0xb4 / +0xb8
    elem = node->itemAt(i);  id = elem->id;    // [+0xb4]
    if (!tartomanyban) {
        if      (id == idA) { tartomanyban = true; idA = -1; }
        else if (id == idB) { tartomanyban = true; idB = -1; /* + horgony */ }
        else continue;                          // még a tartomány előtt
    }
    elem->selected = ertek;                     // [+0x5d]
    ha kell: kimenet.push(id);
    if (id != -1 && (id == idA || id == idB)) break;   // a tartomány vége → KILÉP
}
```

**Egyetlen menet, korai kilépéssel**, tetszőleges irányban (nem kell tudni,
melyik végpont van előrébb). Ha az egyik végpont `-1`, a tartomány a **lista
végéig** tart — erre épül a Shift+End.

---

## 12. Home, End, PageUp, PageDown — a teljes leképezés (2026-08-20)

### 12.1 A billentyűk útja

A `CThumbUI` billentyűkezelője (`0x005c24c0`) egy kis felületre oszt szét,
ami a `CThumbUI + 0x2a4`-en ül; a könyvtárnézetben ezt a `CMultiAlbumNode`
valósítja meg (a vtábla `+0x84`-től kezdődő második táblája):

| billentyű / vezérlő | felület-slot | `CMultiAlbumNode` | függvény |
|---|---|---|---|
| **VK_HOME** (`0x24`) | `+0x00` | vtábla `+0x84` | `0x0076a390` |
| **VK_END** (`0x23`) | `+0x04` | vtábla `+0x88` | `0x0076a400` |
| `throttle/pageup` (görgetősáv-gomb) | `+0x08` | vtábla `+0x8c` | `0x0076a250` |
| `throttle/pagedown` (görgetősáv-gomb) | `+0x0c` | vtábla `+0x90` | `0x0076a2a0` |
| **VK_PRIOR / VK_NEXT** (`0x21`/`0x22`) | `+0x18` | — | egy függvény, `1` = fel, `0` = le |
| `throttle/albumscrolltop` | `+0x20` | — | — |
| **VK_RETURN** (`0x0d`) | `+0x38` | — | — |
| `throttle/nextalbum` | `+0x3c` | — | — |
| `throttle/prevalbum` | `+0x40` | — | — |
| **VK_DELETE** (`0x2e`) | — | — | `0x005c9b00` |

*(A görgetősáv-gombok szétosztója a `0x005de120`, névre illesztve.)*

### 12.2 Home és End — négy viselkedés

`0x0076a390` (Home) és `0x0076a400` (End) **először a Ctrl-t nézi**
(`GetAsyncKeyState(0x11)`, a `[0xd67849]` globális kapuval — 3. szakasz):

| billentyű | mit tesz |
|---|---|
| **Ctrl+Home** | `0x0076a2f0` — a könyvtár **legelejére** görget |
| **Ctrl+End** | az albumlista utolsó eleméhez (`[+0x2c0]` darabszám−1 → `0x004ae180` → `0x00768470`) — az **utolsó mappához** görget |
| **Home** | a jelenlegi mappa csomópontján `0x00718880` |
| **End** | a jelenlegi mappa csomópontján `0x00718930` |

A csomóponti rész (`0x00718880` / `0x00718930`) **a Shiftet nézi**:

```asm
; 0x00718930 (End)
0x00718933  cmp byte ptr [0xd67849], 0      ; billentyűzet-kapu
0x0071893e  je  0x71894f                    ; zárt → nincs Shift
0x00718940  push 0x10 / GetAsyncKeyState    ; Shift?
0x0071894d  jne 0x718964                    ;   igen → tartomány-ág
; --- Shift NÉLKÜL ---
0x0071894f  mov edx, edi / call 0x718a50    ; minden kijelölés le
0x00718956  push edi     / call 0x7172a0    ; lépés −1  → ÜRES kijelölésnél az UTOLSÓ elem
; --- Shifttel ---
0x00718964  mov eax, [edi + 0x390]          ; a horgony
0x0071896a  cmp eax, -1
0x0071897f  je  0x7189ac                    ;   ha nincs horgony → 0x716f40 (mindent kijelöl)
0x0071897d  push 1
0x00718981  push -1                         ; a MÁSIK végpont: „a lista vége"
0x00718983  push eax                        ; a horgony
0x00718984  push edi
0x00718989  call 0x716ae0                   ; ← tartomány a horgonytól a VÉGÉIG
0x0071898e  call 0x71b810                   ; egyetlen értesítés
```

A Home (`0x00718880`) ugyanez, két különbséggel: lépés **+1**, és a
tartomány másik végpontja nem `-1`, hanem az **első elem azonosítója**
(`itemAt(0)->id`) — vagyis a horgonytól **a lista elejéig**.

**A Shift nélküli ág trükkje** a `0x00717eb0`-ban van: ha a kijelölés
**üres**, a léptető nem „a horgonytól" indul, hanem a teljes elemlistából
vesz egyet — `+1` iránynál az **elsőt**, `−1`-nél az **utolsót**
(`0x00717f4e`–`0x00717f7b`). Ezért lesz a „mindent le, majd lépj egyet"
párosból **„ugorj a mappa első/utolsó képére"**.

| billentyű | eredmény a jelenlegi mappán belül |
|---|---|
| **Home** | a kijelölés az **első** képre szűkül |
| **End** | a kijelölés az **utolsó** képre szűkül |
| **Shift+Home** | a horgonytól **a mappa elejéig** kijelöl |
| **Shift+End** | a horgonytól **a mappa végéig** kijelöl |
| **Shift+End horgony nélkül** | a mappa **összes** képe (`0x00716f40`) |

*Bizonyítottsági fok: **megerősített** — a VK-leképezés (`0x005c24c0` és a
görgetősáv `0x005de120`), a Ctrl/Shift-vizsgálatok és a hívott magok
utasításszinten.*

### 12.3 A görgetősáv page-gombjainak lépése

`0x0076a250` / `0x0076a2a0` **kizárólag görget, a kijelöléshez nem nyúl**:

```
lepes = (bélyegkép_magassága / 5) + 90        ; bélyegkép_magassága = [node+0x314] * 144 / 512
0x0076a250:  scrollBy(+lepes)                 ; throttle/pageup
0x0076a2a0:  scrollBy(-lepes)                 ; throttle/pagedown
```

A görgetés **animált** (`0x007300c0`): a lépést a már beütemezett
célpozícióhoz adja hozzá (tehát a gyors ismételt kattintás halmozódik), és
az animáció **időtartama Shifttel más** (`[0xcf4998]` a `[0xcf48b8]`
helyett).

---

## 13. A kijelölés-változás ÁRA — az eredetiben egy menet, nálunk N fájlművelet (2026-08-20)

Ez a szakasz nem az eredetiről szól, hanem a **különbségről**, mert a
felhasználó ezt látja: „azt hittem, halott az app".

### 13.1 Az eredeti

Egy Ctrl+A vagy egy Shift-tartomány az eredetiben:

1. **egy** menet az elemtömbön (`0x00716f40` / `0x00716ae0`),
2. **egy** értesítés-kör a megfigyelőknek (`0x00716f40` vége, ill. `0x0071b810`),
3. **egy** teljes-felület érvénytelenítés (`0x00a54b70`, `{-1,-1,-1,-1}`).

Lemezhez **nem nyúl**, adatbázist **nem kérdez**, elemenkénti visszahívás
**nincs**. Ráadásul a menet hossza **egy mappa** (10.), nem a könyvtár.

### 13.2 Nálunk — mért adat (2026-08-20)

Mérés: `tests/app/qml_functional` `qml_app` fixture, offscreen, helyi
tmpfs-könyvtár, `window.selectAll()` hívása, három ismétlés minimuma.

| sorok | Ctrl+A (bemelegedve) | `hasSavedBackup` kikapcsolva | mindkettő kikapcsolva | **első (hideg) hívás** |
|---:|---:|---:|---:|---:|
| 202 | 47,5 ms | 44,3 ms | 41,4 ms | 205,8 ms |
| 802 | 150,4 ms | 120,7 ms | 85,3 ms | 1 077,3 ms |
| 2 002 | 322,7 ms | 253,6 ms | 208,3 ms | **2 575,1 ms** |

Egyetlen Shift+kattintásos teljes tartomány ugyanennyi (2 002 sornál
356,3 ms) — ugyanaz a kódút.

**Hívásszámlálás egyetlen Ctrl+A-ra** (bármekkora kijelölésnél):

| QML-kötés | hívás / Ctrl+A | soronkénti munkája |
|---|---:|---|
| `controller.hasSavedBackup(selectedIndexes)` (`Main.qml`, `PicasaMenuBar.hasSavedBackup`) | **5×** | `Path.is_dir()` **és** `Path.glob()` a `.picasaoriginals` mappán |
| `controller.peopleOfRows(selectedRows())` (`Main.qml`, `PeoplePanel.peopleHere`) | **3×** | `load_document()` — **egy `.picasa.ini` beolvasása soronként** |

2 002 soros kijelölésnél ez **10 010 `stat()`** és **6 006 ini-beolvasás**
— *egyetlen* billentyűleütésre, a GUI szálán. A `peopleHere` kötése akkor
is lefut, ha az Emberek-panel **be van csukva** (a QML a `visible`-től
függetlenül értékeli a kötéseket).

Helyi tmpfs-en ez „csak" másodperc; a felhasználó gyűjteménye **hálózati
megosztáson** (`/mnt/photo`) van, ahol minden `stat()` és minden
ini-beolvasás egy hálózati körút — ott ugyanez perces nagyságrend.

> ⚠️ **Mechanizmus vs. diagnózis.** A fenti tábla **mérés**, nem
> következtetés: a két slot kikapcsolása 2 002 sornál 322,7 ms-ról
> 208,3 ms-ra visz (a hideg első hívásnál a különbség nagyságrendi). A
> maradék ~208 ms tiszta QML-kötés-újraértékelés — azt a
> `selectedIndexes` tömb-alapú terjesztése okozza, és **külön** mérés kell
> hozzá, hogy melyik kötés.

---

## 14. Lasszó VAGY képhúzás: a trigger GEOMETRIAI, és megvan (2026-08-20)

A #1148 első kiadása ezt „a mi elrendezésünkre vonatkozó, nyitott
UI-döntésnek" nevezte. **Ez tévedés volt** — a bináris pontosan megmondja,
hol a határ. Ez a szakasz a helyesbítés.

### 14.1 A szereposztás: KÉT külön csomópont, nem egy kezelő

```
CSelectionNode  (a rács maga)      ← a KIJELÖLÉS és a LASSZÓ gazdája
 └─ ytDragNode  elemenként          ← a FOGD-ÉS-VIDD gazdája
```

A rács a saját elemeit **`ytDragNode`-ként hozza létre**: a `0x0071abc0`
(a CSelectionNode elem-gyártója) foglal (`0x0097c5d0`), majd a
`0x00aa1b90` `ytDragNode`-konstruktort hívja (`0x0071ac84`). A
`ytDragNode` az egyetlen hely a binárisban, ami a **`"dragstart"`**
értesítést kiküldi (`0x00aa22cd`), és az egyetlen, ami a `DoDragDrop`-hoz
vezető `0x00aa1fb0`-t hordozza (vtábla `+0x78`).

A `CThumbUI` a `"dragstart"` / `"dragstop"` / `"dragcancel"` értesítésekre
csak egy jelzőt állít (`0x005df0b9`: `[CThumbUI+0xdc0] = 1`,
`0x005dfa4b`: `= 0`) — ezt a rajzolás és az **ablakbezárás-tiltás**
(`0x0057c554`: húzás közben az Esc/bezárás nem sül el) olvassa. **A
lasszó–húzás döntésben ez a jelző NEM vesz részt.**

### 14.2 A döntés: a rács a MOZGÁST NEM NYELI EL

A `CSelectionNode` egérmozgás-ága (`0x00719ece`, 2./3. esemény):

```asm
0x00719f38  test cl, cl                    ; élő mozgás?
0x00719f3c  cmp byte ptr [ebx + 0x2ce], 0  ; fut-e MÁR lasszó?
0x00719f43  jne 0x719f91                   ;   igen → a keret frissítése
0x00719f54  push 1 / push ebx
0x00719f5b  call 0x7194e0                  ; TALÁLAT-VIZSGÁLAT
0x00719f67  call 0x719480                  ;   ha elem: kéz-kurzor (IDC_HAND, 0x7f89)
0x00719f71  call 0x71b8a0                  ;   lebegés-értesítés
0x00719f76  mov eax, 0xf4241               ; ← „NEM KEZELTEM, ADD TOVÁBB"
```

**Ez a kulcs.** Ha nincs futó lasszó, a rács a mozgás-eseményt
**visszaadja** (`0xF4241`), és az így jut el a lenyomott elem saját
`ytDragNode`-jához, ami elindítja a húzást. A rács tehát **nem versenyez**
a húzással: vagy lasszózik (mert üres területre nyomtak, és `[+0x2ce]`
áll), vagy félreáll.

A lasszó pedig **kizárólag üres területre** való lenyomásra indul —
a lenyomás-ág (`0x00719c37`) elem-találat esetén a `0x0071bae0`-ra megy
(kijelölés-váltás), és `[+0x2ce]`-t **nem** állítja; üres területnél
viszont pillanatfelvételt ment és `[+0x2ce] = 1` (`0x00719dae`).

> **A trigger tehát egyetlen kérdés: a TALÁLAT-VIZSGÁLAT ad-e elemet.**

### 14.3 A találat-vizsgálat téglalapja: a KIRAJZOLT KÉP, nem a cella

`0x007194e0(csomópont, pont, bool adjIdAzonositot)`:

1. előbb a **csomópont** saját téglalapja (`[+0x2ac]`, `[+0x2b0]`,
   `[+0x2b4]`, `[+0x2b8]`); kívül → `-1`;
2. a pontot átviszi a csomópont transzformációján (`0x009de880`);
3. az elemeken **hátulról előre** halad (`0x0071959d`: `ecx = darab−1`,
   `0x0071973b`: `ecx−−`) — a legfelső nyer;
4. az `[elem+0x5a] != 0` elemeket **kihagyja** (`0x007195f3`);
5. és az elem téglalapját így számolja:

```c
sw = kerekit(elem->w /*[+0x3c]*/ * elem->zoom /*[+0x60]*/);
sh = kerekit(elem->h /*[+0x40]*/ * elem->zoom);
x0 = elem->x /*[+0x88]*/ + (elem->w - sw) * 0.5;   // ← 0.5: [0x00c72150]
y0 = elem->y /*[+0x8c]*/ + (elem->h - sh) * 0.5;
talalat = (x0 <= p.x <= x0 + sw) && (y0 <= p.y <= y0 + sh);
```

A `0.5`-ös szorzó a `0x00c72150`-en álló `double 0.5` — vagyis a
**méretezett elem a saját dobozában KÖZÉPRE igazítva** ad találatot. Ami a
dobozból kilóg a kép mellett, az a találat-vizsgálat szerint **üres
terület**.

### 14.4 A rács elrendezése: a cellák között VAN hézag

A rács elrendezője a `0x0071ca60`. A konfiguráció a
`CSelectionNode + 0x2c8` mutatón lóg:

| mező | jelentés |
|---|---|
| `cfg[0x00]` | a bélyegkép-méret **512-es egységben** (`cella = cfg[0]·144/512` képpont) |
| `cfg[0x08]` | a szélső margó képpontban (vízszintesen és függőlegesen is innen indul) |
| `cfg[0x0c]` | az **arányos** térköz 512-es egységben |
| `cfg[0x14]` | a **fix** térköz képpontban |

```c
cella  = cfg[0]*144 / 512;                       // 0x0071cbf5
res    = (cfg[0x0c] * cfg[0]) / 512 + cfg[0x14]; // 0x0071cbd1–0x0071cbe5
n      = (W - 2*cfg[8] - cella) / (cella + res); // 0x0071cbfc
oszlop = n + 1;                                  // 0x0071cc10
maradek= W - 2*cfg[8] - res*n - cella*oszlop;    // 0x0071cc0c–0x0071cc20
extra  = maradek / oszlop;                       // 0x0071cc36
pitch  = cella + res + extra;                    // 0x0071d2fa–0x0071d31b
```

és az elem a cellán belül **középre kerül**:

```asm
0x0071d2a0  eax = cfg[0]              ; a méret-beállítás
0x0071d2a8  edx = [elem+0x3c]         ; az ELEM tényleges szélessége
0x0071d2ab  eax = eax*9 ; shl 4       ; cfg[0]*144
0x0071d2b3  ecx = edx >> 1            ; elem/2
0x0071d2b5  eax >>= 0xa               ; cella/2
0x0071d2b8  eax -= ecx                ; (cella − elem)/2   ← KÖZÉPRE
0x0071d2c1  ecx = eax + futo_x
0x0071d2ee  [elem+0x88] = ecx
```

*(A `0x0071d296` a sor magasságát az elemek magasságának **maximumaként**
számolja — az elemek tehát nem egyforma méretűek, hanem a kép arányához
igazodnak.)*

**Két, egymástól független forrása van tehát az „üres területnek" a
rácson belül:**

1. a **cellák közti hézag** (`res + extra`, mindig ≥ 0, és a maradék
   szétosztásával rendszerint > 0), és
2. a **cellán belüli levélszekrény-sáv**: a kép arányához igazított elem
   a `cella × cella` dobozban középen ül, a mellette maradó sáv üres.

*(A `0x00573624` a `CThumbUI+0xea4` rácsának adja: `cfg[8] = 4`,
`cfg[0x0c] = 6`, `cfg[0x10] = 6`, kiinduló `cfg[0] = 192`, „automatikus
illesztés" módban `256`-ról 30 körben újraszámolva. Ezek **annak a
csomópontnak** a számai — a könyvtárnézet albumsorai a saját cfg-jüket
kapják; a képlet közös.)*

### 14.5 Amit ebből át kell venni

| | eredeti | nálunk |
|---|---|---|
| a bélyegkép **találati felülete** | a kirajzolt kép téglalapja, a cellán belül középre igazítva | a **teljes cella** (`ThumbDelegate` `MouseArea { anchors.fill: parent }`) |
| a cellák közti hézag | `res + extra`, és a maradék szét van osztva | a `cellWidth` hézagmentesen fedi a sávot |
| ki dönt lasszó/húzás közt | **a találat-vizsgálat** — a rács a mozgást elemtalálatnál nem nyeli el (`0xF4241`) | a `ThumbDelegate` `MouseArea`-ja maga választ (`cell.selected` alapján) |
| a húzás gazdája | elemenkénti `ytDragNode` | ugyanaz a `MouseArea` |

> **Vagyis nincs itt eldöntendő UI-kérdés.** A „pontosan úgy, mint az
> eredeti Picasa" alapértelmezés alkalmazható: a **kép** a húzás felülete,
> a **kép körüli sáv és a cellák közti hézag** a lasszóé.

*Bizonyítottsági fok: **megerősített** — a találat-vizsgálat képlete és a
`0.5`-ös konstans, az elrendezés képletei, a `0xF4241` visszatérés, és az
elem-gyártó `ytDragNode`-hívása mind utasításszinten.*

### 14.6 Amit KIZÁRTUNK a kereséssel

- **Nincs képpont- vagy idő-küszöb a húzás indításához.** A
  `GetSystemMetrics(SM_CXDRAG/SM_CYDRAG = 0x44/0x45)` a teljes
  `.text`-ben **egyszer sem** hívódik meg; a `SetCapture`-nek mindössze
  két hívóhelye van (`0x00923460`, `0x00a52890`), egyik sem a rácsé.
- **A `[CThumbUI+0xdc0]` „húzás folyamatban" jelző nem trigger:**
  mindössze két olvasója van (`0x00570f10` — elrendezés/rajzolás,
  `0x0057c554` — a bezárás tiltása húzás közben).
- **A `.tre` sem dönt:** a 24 `Handler`-kötés között a rácshoz **nincs**
  húzás-kezelő (6. szakasz); a `selectiondrag` a szerkesztő három
  téglalapjáé (4/b).

---

## 15. Miért NEM tud átnyúlni a mappahatáron a Shift-tartomány, a nyilas léptetés és a lasszó (2026-08-22, #1219)

A 10. szakasz kimondta, hogy a kijelölés hatóköre egy mappa. Ez a szakasz
azt bizonyítja, hogy ez **nem egy ellenőrzés, amit be lehetne kapcsolni,
hanem a szerkezet következménye**: a Picasában nincs olyan kódút, amelyen
egy tartomány, egy lasszó vagy egy nyíllépés a saját csomópontján kívüli
elemhez érhetne.

### 15.1 A szerkezet: konténer + mappánként EGY kijelölés-csomópont

`0x0076a390` (`CMultiAlbumNode` vtábla, 33. rés) — a teljes függvény
lényege:

```c
if (this->aktualisSorIndex /* [+0x2e0] */ == -1) return;
sor = this->sorok /* [+0x300] */ [ aktualisSorIndex ];
sel = sor->kijelolesCsomopont /* [+0x2b4] */;
sel->AddRef();
0x00718880(sel);            // a kijelölés-művelet EGYETLEN csomóponton
sel->Release();
```

**Nincs ciklus a `[+0x300]` tömbön.** A feed konténere mindig **pontosan
egy** sor kijelölés-csomópontját éri el: az aktuálisét. A `0x00718880`
pedig épp az a burkoló, amelyik a **tartomány-magot** (`0x00716ae0`) és a
**„mindent kijelöl" magot** (`0x00716f40`) is hívja.

### 15.2 Mind a négy mag CSAK a saját csomópontja elemein megy végig

Mindegyik a csomópont **saját** virtuális `count()` (vtábla `+0xb4`) és
`itemAt(i)` (vtábla `+0xb8`) párján iterál — más csomóponthoz nem fér
hozzá:

| mag | cím | mit csinál |
|---|---|---|
| tartomány (Shift+kattintás, Shift+Home/End) | `0x00716ae0` | `+0xb4`/`+0xb8` (11.4) |
| nyilas léptetés | `0x00717eb0` | `0x00717fd0`–`0x00718012`: a **horgonyt** (`[this+0x390]`) keresi meg a SAJÁT elemlistájában |
| a határ-ág | `0x00717d10` | a saját kijelölt-lista felépítése (`0x00717420`, szintén `+0xb4`/`+0xb8`) |
| lasszó elemenkénti teszt | `0x0071bc90` | a hívás `0x0071a032`: `push ebx` = a **hívó csomópont**; a lasszó téglalapja `[ebx+0x29c]` |

### 15.3 Az egérkezelő MAGA is a kijelölés-csomóponté

A rács teljes egérkezelése — a kattintás-ág (`0x00719a44`), a
kijelölés-ág (`0x00719ace`), a lasszó-téglalap (`0x00719f91`) és a
lasszó-teszt hívása (`0x0071a032`) — a **`0x007199b0`** függvényben van,
ami a **`CSelectionNode` vtábla 29. rése** (öröklik:
`CAlbumSelectionNode`, `CFoundFaceSelectionNode`).

A feed konténere **ugyanezt a 29. rést írja felül** (`0x0076a660`), de az
override **egyetlen kijelölés-műveletet sem végez**: mindössze négy
eseménykódot (`0x13`, `0x0e`, `0x0f`, `0x11`) kezel — nagyítás-csúszka,
`scaleslider/scaleslider` — a többit továbbadja az ős
konténer-szétosztójának (`0x0072f980`).

> **Ebből következik:** az egér lenyomása egy album-sor saját
> kijelölés-csomópontjában landol, és a húzás minden további eseménye
> **ugyanabban** a csomópontban fut le. A lasszó fizikailag nem lát más
> mappa elemeit.

### 15.4 A nyilas léptetés a mappa végén — MÉRVE, nem feltételezve

A #1219 kifejezetten figyelmeztetett, hogy ezt **ne találgassuk** („lehet,
hogy az eredeti átvisz a következő mappára ÉS törli az előzőt"). A válasz
a kódból:

```asm
0x00717fd0–0x00718012   ; a HORGONY ([this+0x390]) indexének megkeresése
                        ; a SAJÁT elemlistában  ->  ebx
0x00718022  eax = irány             ; +1 vagy -1
0x00718025  edx = elemszám
0x00718029  ebx += irány
0x0071802b  edx -= 1                ; elemszám-1
0x00718031  cmp  ebx, edx
0x00718033  jbe  0x718058           ; BELÜL -> normál léptetés
; --- TÚLFUTÁS (mindkét irányban) ---
0x00718035  push 0
0x00718037  push -1
0x00718039  push eax                ; irány
0x0071803a  mov  eax, edi           ; this = UGYANAZ a csomópont
0x0071803c  call 0x717d10
0x0071804a  mov  eax, 0xf4240
            ret  8
```

⚠️ A `jbe` **előjel nélküli** összehasonlítás, ezért a `-1`-re csökkenő
index (`0xFFFFFFFF`) is ide fut: **mindkét vég ugyanezt az ágat járja.**

A `0x00717d10(this, irány, -1, 0)` **ugyanazon a csomóponton** dolgozik,
és a végén:

```asm
0x00717e20  cmp  eax, ebp           ; új index vs. elemszám-1
0x00717e22  jbe  0x717e50           ; belül -> [this+0x2e0] = az elem azonosítója
0x00717e24  cmp  byte ptr [esp+0x34], 0   ; a 3. argumentum = 0
0x00717e29  je   0x717e76
0x00717e76  mov  dword ptr [this+0x2e0], 0xFFFFFFFF   ; ← TÖRLI a jelölőt
```

**Az eredmény: a léptetés MEGÁLL.** Nem lép a következő mappára, nem
fordul át a lista elejére, és **nem jelöl ki semmi újat** — a
„jelenlegi elem" jelölőt (`[this+0x2e0]`) egyszerűen `-1`-re állítja.

*Bizonyítottsági fok: **megerősített** — mind a négy mag, a vtábla-rések
és a határ-ág szó szerinti kódolvasásból.*

### 15.5 Eredeti / nálunk / teendő

| | eredeti (bizonyítva) | nálunk (mérve) | teendő |
|---|---|---|---|
| **Shift+kattintás** | a tartomány-mag a jelenlegi mappa csomópontján fut → **nem léphet ki** | ❌ `Main.qml:323–325` — `Selection.range(selectedIndex, i)` **globális sorindexeken**, mappa-szorítás nélkül | a tartományt a kezdőpont mappacsoportjára szorítani |
| **nyilas léptetés** | a mappa szélén **megáll**, nem lép át és nem jelöl ki újat | ❌ `models.py:538–555` — a balra/jobbra **folytonos**, a fel/le a csoport szélén **szándékosan a szomszéd csoportra ugrik** (a docstring ki is mondja) | a `navigate` álljon meg a csoporthatáron |
| **Shift+nyíl** | **egyesével bővít, és a horgonyt is lépteti** (4/c) | ✅ **JAVÍTVA** (#892/#1222) — `LightboxFeed.qml:67–85` a `Selection.withAdded`-del egyesével bővít, a léptetés töve (a kurzor) lép, a `_csoportraVagva` pedig a mappacsoportban tartja | nincs; a horgony két szerepét nálunk két mező viszi — ld. 15.6 |
| **lasszó** | a lenyomás csomópontjának elemein, metszés-szabállyal | ✅ **MÁR HELYES** — `LightboxFeed.qml:314–335` a kezdő **mappacsoport** `start`/`count` tartományára szorít (`idx < count`), és a csoportok mappánként állnak (`models.py:511–522`) | **nincs teendő a hatókörön**; a lasszó egyéb eltérései a #1148-ban |

> ⚠️ **A #1219 harmadik állítása („a lasszó több mappa képeit is
> befogja") TÉVES.** A `lassoIndexes` levágja a kezdő csoporton kívüli
> indexeket, a csoportok pedig `folder_path`-váltásnál kezdődnek. Ezt a
> #1148 valódi egéreseményes mérése is alátámasztja — ott épp az
> **ellenkezője** szerepel eltérésként („a lasszónk nem lép át
> mappacsoport-határt"). A mostani bizonyítás szerint **a mi
> viselkedésünk az eredetivel egyezik**, tehát a #1148 azon aggálya is
> tárgytalan.

### 15.6 A horgony KÉT szerepe — nálunk két mező (#892/#1222/#897)

Az eredeti egyetlen mezőt (`[this+0x390]`) használ **két** dologra:

1. a **nyilas léptetés töve** — innen indul a lépés (`0x00717ff9`
   visszakeresi az indexét), és ide íródik vissza a friss elem
   (`0x007180da`), tehát **lép**;
2. a **Shift+kattintás tartományának töve** — `0x0071bb34` innen méri a
   tartományt, és a kattintás **nem** lépteti.

Nálunk ez két mező:

| szerep | mező | lép-e? |
|---|---|---|
| a Shift+**nyíl** léptetésének töve | `selectedIndex` (a kurzor) | igen, minden nyílütésnél |
| a Shift+**kattintás** tartományának töve | `LightboxFeed.selectionAnchor` | nem (#897) |

**A látható eredmény ugyanaz**, mert az eredeti tartomány-magja
(`0x00716ae0`) csak **kijelöl**: a tartományon kívül már kijelölt
elemeket nem szedi le. Példa — kattintás az 1.-re, Shift+jobb ×2, majd
Shift+kattintás az 5.-re:

| | tő a kattintáskor | a kattintás eredménye | végállapot |
|---|---|---|---|
| eredeti | 3. (a nyíl léptette) | a 3.–5. kijelölődik, az 1.–2. marad | 1.–5. |
| nálunk | 1. (a horgony nem lépett) | `range(1, 5)` | 1.–5. |

Ezt a #897 `test_a_shift_kattintas_a_horgonytol_jelol` tesztje méri;
a Shift+nyíl saját (irányváltásos) viselkedését a
`tests/app/qml_functional/test_shift_nyil_bovites_892_1222.py`.

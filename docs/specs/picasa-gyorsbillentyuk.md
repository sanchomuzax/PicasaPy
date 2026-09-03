# Gyorsbillentyűk: a teljes tár ÉS a hozzájuk tartozó funkciók (#1154)

> **Mit old meg ez a lap.** Eddig a gyorsbillentyűk szórtan, több
> UI-audit-lapon szerepeltek, és **csak a billentyű** volt leírva — a
> hozzá tartozó parancs nem. Egy billentyűlista önmagában nem
> megvalósítható: attól, hogy tudjuk, hogy a `Ctrl+Shift+O` létezik, még
> nem tudjuk, **mit** csinál, **mikor** tiltott és **mire** hat.
>
> ⚠️ Ugyanaz a hibaalak, amit a `.tre`-nél már megtanultunk: **az
> azonosító nem jelentés.** Egy billentyűkombináció sem az — és ahogy
> alább a **2.4** szakasz kimutatja, **még a szállított keymap saját
> kommentjei sem azok.**

**Kiindulási állapot (2026-08-25, a kör előtt):** a `docs/specs/` alatt
összesen **12 lapon** volt gyorsbillentyű-említés, **59 különböző
kombináció-előfordulással**, de **egyetlen összesített tár sem**, és
**egyetlen billentyűhöz sem tartozott parancsazonosító vagy
visszakereshető bináris cím**. Funkcióleírás — a hat kérdés értelmében —
**0 billentyűhöz** volt meg. Ez a lap a **48 keymap-rekeszt**, a
menüsáv **32** és a helyi menük **44** gyorsbillentyűs rekordját írja le
— egyedi kombinációra vetítve **34 kötést** —, mindegyiket forrással.

---

## 1. A három egymástól független forrás

A gyorsbillentyűk **nem egy helyen** élnek a Picasában. Három forrás van,
és **csak együtt** adnak teljes képet:

| # | forrás | mit ad | hol |
|---|---|---|---|
| **A** | a `SHORTCUTS.XML` erőforrás a `Picasa3i18n.dll`-ben | a **48 átképezhető rekesz** és a hozzájuk tartozó **honosítási átképezés** | PE-erőforrás `XMLF / SHORTCUTS.XML / 1033`, fájleltolás **`0x591ad8`**, 4627 bájt |
| **B** | a menüsáv rekordtáblája | a **ténylegesen kiírt** gyorsbillentyű menütételenként, parancsazonosítóval | `0x00559150` tölti, a tábla a `.data`-ban **`0xd6d960`**-tól |
| **C** | a helyi (jobbklikk-) menük rekordtáblái | a **felület-függő** billentyűk (Enter, Esc, `Ctrl+Delete`, `Ctrl+H`) | 27 építőfüggvény, ld. **4.** |

Az `A` és a `B` **különböző kérdésre válaszol**, és a **2.4**-ben
kimutatott ponton **ellent is mondanak egymásnak**. Ilyenkor a `B`
(a bináris rekordtábla) és a felhasználói képernyőkép a mérvadó.

### 1.1 A `Picasa3i18n.dll`, amiből dolgoztunk

- fájl: `research/copy_Picasa_3_7/Picasa3/Picasa3i18n.dll`, 26 904 904 bájt
- SHA-256: `146ecc3c7f4f5964965be2fe5c5014cf3ee1e87af66324b0ce05bcaf8ec51f6e`
- a `Picasa3.exe` ugyanabból a telepítésből: SHA-256
  `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`
  (megegyezik a bináris-index `meta.json`-jában rögzítettel)

---

## 2. Az `A` forrás: a 48 rekeszes keymap

### 2.1 Hogyan olvassa be a Picasa

| lépés | cím | bizonyíték |
|---|---|---|
| a menüsáv építése **legelőször** a keymapet tölti be | `0x00559150` → `call 0x9a16b0` a `0x00559164`-en | diszasszemblátum |
| a betöltő a **lemezes felülbírálatot** keresi | `0x009a16b0`, a `runtime\shortcuts.xml` sztring `0x00c8c3d4`-en | `string_xrefs` + diszasszemblátum |
| ha nincs ilyen fájl, `eax = 9` hibakóddal tér vissza | `0x009a1776  mov eax, 9` | diszasszemblátum |
| az XML-elemző (SAX-kezelő) | `0x009a0ad0` (2836 bájt) | `string_xrefs` |

Az elemző által ismert szövegek — mind a `0x009a0ad0` xref-jei. A
bináris-index néhány sztringre **a szó belsejébe** mutató címet ad
(a fordító így hivatkozza őket); ilyenkor zárójelben az indexbeli cím
áll, mellette a sztring valódi kezdete:

| sztring | indexbeli xref-cím | a sztring kezdete |
|---|---|---|
| `srckey` | `0x00cd914d` (`rckey`) | `0x00cd914c` |
| `dstkey` | `0x00cd9155` (`stkey`) | `0x00cd9154` |
| `VK_RETURN` | `0x00cd9168` | `0x00cd9168` |
| `VK_HOME` | `0x00cd9175` (`K_HOME`) | `0x00cd9174` |
| `VK_END` | `0x00cd917d` (`K_END`) | `0x00cd917c` |
| `VK_DELETE` | `0x00cd9184` | `0x00cd9184` |
| `VK_MENU` | `0x00cd9191` (`K_MENU`) | `0x00cd9190` |
| `VK_NUMPAD5` | `0x00cd9198` | `0x00cd9198` |
| `shift` | `0x00cd91ac` | `0x00cd91ac` |
| `dshift` | `0x00cd91c0` | `0x00cd91c0` |
| `keymap` | `0x00cd91d1` (`eymap`) | `0x00cd91d0` |
| `shortcuts` | `0x00cd91d8` | `0x00cd91d8` |

A `ctrl` / `alt` / `dctrl` / `dalt` attribútumnevek a fenti sztringek
közötti hézagokban állnak, önálló xref nélkül; a szállított XML-ben
mind a négy előfordul.

> **A `runtime\shortcuts.xml` a szállított telepítésben NINCS meg**
> (a `Picasa3/runtime/` 78 fájlja között nem szerepel). Vagyis ez egy
> **opcionális felülbíráló fájl**; a tényleges keymap a DLL
> erőforrásából jön. Ez nekünk azt jelenti: a felhasználó akár saját
> kiosztást is adhatott volna — de a gyakorlatban a szállított tábla fut.

### 2.2 A rekesz szemantikája: `srckey` → `dstkey`

Egy rekesz alakja:

```xml
<!-- Rotate Clockwise -->
<item srckey="D" dstkey="R" ctrl="1" shift="0" alt="0"></item>
```

- **`srckey`** = amit a felhasználó **lenyom** az adott nyelven,
- **`dstkey`** = a **kanonikus** (angol) billentyű, amire a program
  lefordítja; üres `dstkey` = nincs átképezés, `srckey` maga a kanonikus,
- `ctrl` / `shift` / `alt` = a **forrás**-oldali módosítók,
  `dctrl` / `dshift` / `dalt` = a cél-oldaliak (csak az olasz táblában
  fordulnak elő).

A **sorrend hordozza az azonosságot**: az elemző rekeszenként tölt, és a
rekesz **sorszáma** köti a parancshoz. A `<!-- … -->` kommentek a
honosítóknak szólnak — **adat, nem szerződés** (ld. 2.4).

### 2.3 Nyolc nyelv — és a magyar NEM tartozik közéjük

A DLL 3084 `XMLF` erőforrása közül **pontosan nyolc** a keymap:

| erőforrásnév | fájleltolás | átképezett rekesz |
|---|---|---:|
| `SHORTCUTS.XML` (alap/angol) | `0x591ad8` | 0 |
| `SHORTCUTS_DE.XML` | `0x592cec` | 7 |
| `SHORTCUTS_ES.XML` | `0x593f08` | 11 |
| `SHORTCUTS_FR.XML` | `0x595128` | 2 |
| `SHORTCUTS_IT.XML` | `0x596340` | 11 (+1 extra rekesz) |
| `SHORTCUTS_NL.XML` | `0x597600` | 7 |
| `SHORTCUTS_PT-BR.XML` | `0x59881c` | 10 |
| `SHORTCUTS_RU.XML` | `0x599a3c` | 10 |

Összehasonlításként: a `TOOLTIPS.XML`-ből és a `KEYWORDSTEXT.XML`-ből
**41 nyelvi változat** van, köztük `_HU`. Keymapből **nincs magyar**.

> **Következmény a PicasaPy-ra:** a magyar Picasa az **alap (angol)
> kiosztást** használja. Nálunk tehát **nem kell** magyar-specifikus
> kiosztás; az alaptábla a helyes viselkedés.

A hét honosított tábla **kommentsora bitre azonos** az alapéval (az
olasz kivételével, amely egy 49. rekeszt szúr az elejére
`ctrlalt disable` kommenttel, `srckey="VK_MENU" dstkey="!" ctrl=1 alt=1`
— feltehetően az olasz billentyűzet AltGr-ütközése ellen). Példa a
német táblából: `Ctrl+D` → *Rotate Clockwise* („**D**rehen"),
`Ctrl+Shift+W` → *Black-and-White* („Schwarz-**W**eiß").

### 2.4 ⚠️ A kommentek RÉSZBEN ELAVULTAK — mérve

A keymap kommentjei a **Picasa 2 korabeli** parancsneveket őrzik. Három
helyen a 3.9 tényleges viselkedése **más**, és ezt a `B` forrás és a
felhasználói képernyőkép egybehangzóan mutatja:

| rekesz | a komment szerint | a 3.9-ben ténylegesen (B forrás + képernyőkép) |
|---|---|---|
| 7. `Ctrl+S` | „Save a Copy" | **Mentés** (`ID_FILE_SAVE`); a „Másolat mentése" tételen **nincs** gyorsbillentyű |
| 12. `Ctrl+T` | „Order Prints" | **Címkék panel** (`ID_CAPTAG`, `cmd 0x9d2c`); a „Papírképek rendelése…" tételen **nincs** gyorsbillentyű |
| 26. `Ctrl+W` | „Export as Web Page" | a menütételen **nincs** gyorsbillentyű (`E&xport as HTML Page...`, cím nélkül a rekordban) |

Ezért **nem szabad** a keymap kommentjeiből kiosztást vezetni. A tár
alább ezt a különbséget oszloponként külön jelöli.

### 2.5 A teljes 48 rekesz (alaptábla)

Jelölés a „3.9-ben él?" oszlopban:
**✅** = a `B`/`C` forrásban megtaláltuk a kötést (cím alább),
**⬜** = a 3.9 menüiben és helyi menüiben **nem találtunk** kötést,
**➖** = a rekeszben **nincs billentyű** (üres `srckey`).

| # | keymap-komment | alap billentyű | 3.9-ben él? | mihez kötődik ténylegesen |
|---:|---|---|:--:|---|
| 1 | New label | `Ctrl+N` | ✅ | Fájl ▸ Új album… (`ID_FILE_NEWLABEL`, `cmd 0x9d67`) |
| 2 | Add File to Picasa | `Ctrl+O` | ✅ | Fájl ▸ Fájl felvétele a Picasába… (`cmd 0xe101`) |
| 3 | Import from | `Ctrl+M` | ✅ | Fájl ▸ Importálás forrása… (`cmd 0x9c91`) |
| 4 | Open File in Editor | `Ctrl+Shift+O` | ✅ | Fájl ▸ Fájl(ok) megnyitása szerkesztőben (`cmd 0x9c9b`) |
| 5 | Rename | `F2` | ✅ | Fájl ▸ Átnevezés… (`cmd 0x9d4f`) |
| 6 | Export Picture to Folder | `Ctrl+Shift+S` | ✅ | Fájl ▸ Kép exportálása mappába… (`cmd 0x9c81`) |
| 7 | *Save a Copy* → **Save** | `Ctrl+S` | ✅ | Fájl ▸ **Mentés** (`cmd 0xe103`) — ld. 2.4 |
| 8 | Locate on Disk | `Ctrl+Enter` | ✅ | Fájl ▸ Keresés a lemezen (`cmd 0x9c99`) |
| 9 | Delete from Disk | `Delete` | ✅ | Fájl ▸ Törlés lemezről… (`cmd 0x9c9a`) |
| 10 | Print | `Ctrl+P` | ✅ | Fájl ▸ Nyomtatás… (`cmd 0xe107`) |
| 11 | Email | `Ctrl+E` | ✅ | Fájl ▸ E-mail… (`cmd 0x9c97`) |
| 12 | *Order Prints* → **Tags** | `Ctrl+T` | ✅ | Nézet ▸ **Címkék** (`cmd 0x9d2c`) — ld. 2.4 |
| 13 | Cut | `Ctrl+X` | ✅ | Szerkesztés ▸ Kivágás (`cmd 0x9d39`) |
| 14 | Copy | `Ctrl+C` | ✅ | Szerkesztés ▸ Másolás (`cmd 0x9d3b`) |
| 15 | Paste | `Ctrl+V` | ✅ | Szerkesztés ▸ Beillesztés (`cmd 0x9d3c`) |
| 16 | Select All | `Ctrl+A` | ✅ | Szerkesztés ▸ Az összes kijelölése (`cmd 0x9cb8`) |
| 17 | Invert Selection | `Ctrl+I` | ✅ | Szerkesztés ▸ Kiválasztás megfordítása (`cmd 0x9c47`) |
| 18 | Clear Selection | `Ctrl+D` | ✅ | Szerkesztés ▸ Kijelölés törlése (`cmd 0x9c90`) |
| 19 | Small Thumbnails | `Ctrl+1` | ✅ | Nézet ▸ Kis indexképek (`cmd 0x9c9d`) |
| 20 | Normal Thumbnails | `Ctrl+2` | ✅ | Nézet ▸ Normál indexképek (`cmd 0x9c9c`) |
| 21 | Edit View | `Ctrl+3` | ✅ | Nézet ▸ Szerkesztési nézet (`cmd 0x9c8f`) **és** Kép ▸ Megjelenítés és szerkesztés (`cmd 0x9ca0`) — két külön parancs, egy billentyű |
| 22 | Keywords | `Ctrl+K` | ⬜ | a 3.9 menüiben nincs `Ctrl+K`; a címkepanel a `Ctrl+T`-n van (12.) |
| 23 | Slideshow | `Ctrl+4` | ✅ | Nézet ▸ Diavetítés (`cmd 0x9c9f`) **és** Mappa/Album ▸ Diavetítés megtekintése (`cmd 0x9c6d`) |
| 24 | Timeline | `Ctrl+5` | ✅ | Nézet ▸ Időrend (`cmd 0x9ccc`) |
| 25 | Print Contact Sheet | `Ctrl+Shift+P` | ✅ | Mappa/Album ▸ Indexképek nyomtatása… (`cmd 0x9c94`) |
| 26 | Export as Web Page | `Ctrl+W` | ⬜ | a menütételen nincs kiírt billentyű — ld. 2.4 |
| 27 | Rotate Clockwise | `Ctrl+R` | ✅ | Kép ▸ Forgatás jobbra (`cmd 0x9ca2`) |
| 28 | Rotate Counterclockwise | `Ctrl+Shift+R` | ✅ | Kép ▸ Forgatás balra (`cmd 0x9ca3`) |
| 29 | Properties | `Alt+Enter` | ✅ | Kép ▸ Tulajdonságok (`cmd 0x9ca8`) |
| 30 | Help Contents and Index | `F1` | ✅ | Súgó ▸ Súgó – tartalom és tárgymutató (`cmd 0x9cac`) |
| 31 | Black-and-White | `Ctrl+Shift+B` | ⬜ | a Nézet ▸ Megjelenítési mód ▸ Fekete-fehér tételen nincs kiírt billentyű |
| 32 | I'm Feeling Lucky | `Ctrl+Shift+E` | ⬜ | a Kép ▸ Jó napom van tételen nincs kiírt billentyű |
| 33 | Search | `Ctrl+F` | ⬜ | nincs menütétel-párja (a keresőmező eszköztári) |
| 34 | Hold in Tray | `Ctrl+H` | ✅ | **a tálca helyi menüje** ▸ Kijelölés megtartása (`Tray::ID_PICTURE_HOLDINPICTURETRAY`, `cmd 0x9cca`) |
| 35 | Flip Horizontal | `Ctrl+Shift+H` | ⬜ | a 3.9-ben **nincs ilyen menüparancs** (a szövegtárban sincs „Flip Horizontal" menütétel) |
| 36 | Flip Vertical | `Ctrl+Shift+V` | ⬜ | ugyanaz, mint a 35. |
| 37 | Move to End of Album | ➖ (`ctrl=1`, üres billentyű) | ➖ | a rekesz **kitöltetlen** a szállított táblában |
| 38 | New Album | `Ctrl+N` | ✅ | ugyanaz a billentyű, mint az 1. rekeszé — a két rekesz **ugyanarra a menütételre** mutat |
| 39 | Full Screen Mode | `F11` | ⬜ | nincs menütétel-párja (a teljes képernyő a nézőben és a diavetítésben él) |
| 40 | Select 1st Picture in Album | `Home` | ✅ | a rács `Home`-kezelője, `0x0076a390` → `0x00718880` (ld. `picasa-eger-es-kijeloles.md` 12.) |
| 41 | Select Last Picture in Album | `End` | ✅ | `0x0076a400` → `0x00718930` (ugyanott) |
| 42 | Pause/Play Movie | `/` | ⬜ | a videólejátszás billentyűzete nincs feltárva (ld. 7.) |
| 43 | Rewind Movie | `,` | ⬜ | ugyanaz |
| 44 | Fast Forward Movie | `.` | ⬜ | ugyanaz |
| 45 | Next Picture | ➖ | ✅ | a rekesz üres, de a funkció él: jobbra nyíl (`0x00717eb0`) |
| 46 | Previous Picture | ➖ | ✅ | balra nyíl, ugyanaz a mag |
| 47 | Switch Between Automatic and Manual Modes | ➖ | ⬜ | nem azonosított |
| 48 | Return to Main Library View | ➖ | ✅ | **`Esc`** a nézőben (`OneUp::ID_VIEWALBUM`, `cmd 0x9cc6`) |

**Elszámolás — a „3.9-ben él?" oszlop szerint:** 48 rekesz =
**35 ✅** + **12 ⬜** + **1 ➖** (a 37., amelyhez sem billentyű, sem
kötés nincs).

**Elszámolás a billentyű-oszlop szerint:** 43 rekeszben van billentyű,
**5-ben nincs** (37., 45., 46., 47., 48.). Ezek közül három funkció
**mégis él**, csak **nem átképezhető** billentyűn: jobbra/balra nyíl
(45., 46.) és `Esc` (48.) — a keymap csak betűket, `VK_*` neveket és
írásjeleket tud átképezni, nyilat és `Esc`-et nem.

---

## 3. A `B` forrás: a menüsáv rekordtáblája

### 3.1 A rekord alakja — mérve

A menüsáv-építő (`0x00559150`, 15 495 bájt, egyszer fut le: kapu a
`0x0055916f`-en, `test byte ptr [0xda03a8], 1`) **20 bájtos rekordokat**
tölt a `.data`-ba, `0xd6d960`-tól:

| eltolás | tartalom |
|---|---|
| `+0x00` | a honosított felirat (`0x009ae560(kulcs, angol_alapértelmezés)` eredménye `+4`) |
| `+0x04` | a **gyorsbillentyű szövege** — vagy betű-literál (`"N"`, `"F2"`), vagy szintén honosított kulcs (`CMenuBar::Enter`, `CMenuBar::Delete`) |
| `+0x08` | 16 bites **módosító-jelzőmező** |
| `+0x0a` | 16 bites **parancsazonosító** |
| `+0x0c`, `+0x10` | a szállított menükben 0 |

Egy **csupa nulla** rekord = **elválasztó vonal**.

⚠️ **Fordítói csapda** (a `picasa-eger-es-kijeloles.md` 11.1 is jelzi): a
`+0x04…+0x0a` mezőket a fordító a **következő** menütétel blokkjában írja
ki. Aki blokkonként olvassa a diszasszemblátumot, eggyel elcsúszva
párosít.

### 3.2 A jelzőmező bitjei — mérve, nem következtetve

A feliratot előállító függvény a **`0x00a6b250`** (1068 bájt). A
`0x00a6b3bb`-től induló szakasz szedi szét a jelzőbájtot:

```asm
0x00a6b3bb  mov cl, bl        ; bl = a jelzőbájt
0x00a6b3bd  shr cl, 2
0x00a6b3c0  mov al, bl
0x00a6b3c2  and al, 1         ; 0. bit
0x00a6b3c4  mov dl, bl
0x00a6b3c6  not cl
0x00a6b3c8  and dl, 2         ; 1. bit
0x00a6b3cb  and cl, 1         ; = NEM(2. bit)
```

| bit | érték | jelentés |
|---:|---:|---|
| 0 | 1 | **Shift** |
| 1 | 2 | **Alt** |
| 2 | 4 | **NINCS Ctrl** (fordított logika: `Ctrl` akkor van, ha ez a bit **0**) |

Ellenőrzés: Új album `flags=0` → `Ctrl+N` ✔ · Átnevezés `flags=4` → `F2`
(Ctrl nélkül) ✔ · Fájl(ok) megnyitása `flags=1` → `Ctrl+Shift+O` ✔ ·
Tulajdonságok `flags=6` (Alt + nincs Ctrl) → `Alt+Enter` ✔.

A módosító-előtagok maguk is honosítottak: `ytMenu::CtrlPrefix` =
„Ctrl+" (`0x00ce4a88`), `ytMesu::ShiftPrefix` = „Shift+" (`0x00ce4aa4`,
az elgépelt kulcsnév az eredetiben így van), `ytMenu::AltPrefix` =
„Alt+" (`0x00ce4ac0`).

### 3.3 A menüsáv 32 gyorsbillentyűs rekordja

Mind a 32 sor a `0x00559150` diszasszemblátumából, a rekord címével.
A magyar felirat a `Picasa3i18n.dll` magyar `stringres`-éből
(`referencia/i18n-hu/stringres.xml`), a képernyőkép-ellenőrzés a
`research/testdata/screenshot/2026-07-17 20 55 27…20 55 50.png`
sorozatból.

| rekord | menü | magyar felirat | billentyű | `cmd` |
|---|---|---|---|---|
| `0xd6d960` | Fájl | Új album… | `Ctrl+N` | `0x9d67` |
| `0xd6d99c` | Fájl | Fájl felvétele a Picasába… | `Ctrl+O` | `0xe101` |
| `0xd6d9b0` | Fájl | Importálás forrása… | `Ctrl+M` | `0x9c91` |
| `0xd6d9ec` | Fájl | Fájl(ok) megnyitása szerkesztőben | `Ctrl+Shift+O` | `0x9c9b` |
| `0xd6da28` | Fájl | Átnevezés… | `F2` | `0x9d4f` |
| `0xd6da50` | Fájl | Mentés | `Ctrl+S` | `0xe103` |
| `0xd6dab4` | Fájl | Kép exportálása mappába… | `Ctrl+Shift+S` | `0x9c81` |
| `0xd6dadc` | Fájl | Keresés a lemezen | `Ctrl+Enter` | `0x9c99` |
| `0xd6daf0` | Fájl | Törlés a lemezről… | `Delete` | `0x9c9a` |
| `0xd6db18` | Fájl | Nyomtatás… | `Ctrl+P` | `0xe107` |
| `0xd6db2c` | Fájl | E-mail… | `Ctrl+E` | `0x9c97` |
| `0xd6db80` | Szerkesztés | Kivágás | `Ctrl+X` | `0x9d39` |
| `0xd6db94` | Szerkesztés | Másolás | `Ctrl+C` | `0x9d3b` |
| `0xd6dba8` | Szerkesztés | Beillesztés | `Ctrl+V` | `0x9d3c` |
| `0xd6dc48` | Szerkesztés | Az összes kijelölése | `Ctrl+A` | `0x9cb8` |
| `0xd6dc70` | Szerkesztés | Kiválasztás megfordítása | `Ctrl+I` | `0x9c47` |
| `0xd6dc84` | Szerkesztés | Kijelölés törlése | `Ctrl+D` | `0x9c90` |
| `0xd6dfb4` | Nézet | Kis indexképek | `Ctrl+1` | `0x9c9d` |
| `0xd6dfc8` | Nézet | Normál indexképek | `Ctrl+2` | `0x9c9c` |
| `0xd6dfdc` | Nézet | Szerkesztési nézet | `Ctrl+3` | `0x9c8f` |
| `0xd6e018` | Nézet | Címkék | `Ctrl+T` | `0x9d2c` |
| `0xd6e07c` | Nézet | Diavetítés | `Ctrl+4` | `0x9c9f` |
| `0xd6e090` | Nézet | Időrend | `Ctrl+5` | `0x9ccc` |
| `0xd6e1d4` | Mappa/Album | Diavetítés megtekintése | `Ctrl+4` | `0x9c6d` |
| `0xd6e274` | Mappa/Album | Indexképek nyomtatása… | `Ctrl+Shift+P` | `0x9c94` |
| `0xd6e2b0` | Mappa/Album | Keresés a lemezen | `Ctrl+Enter` | `0x9cba` |
| `0xd6e318` | Mappa/Album | Átnevezés… | `F2` | `0x9d4f` |
| `0xd6e340` | Kép | Forgatás jobbra | `Ctrl+R` | `0x9ca2` |
| `0xd6e354` | Kép | Forgatás balra | `Ctrl+Shift+R` | `0x9ca3` |
| `0xd6e498` | Kép | Megjelenítés és szerkesztés | `Ctrl+3` | `0x9ca0` |
| `0xd6e560` | Kép | Tulajdonságok | `Alt+Enter` | `0x9ca8` |
| `0xd6e9b8` | Súgó | Súgó – tartalom és tárgymutató | `F1` | `0x9cac` |

**Amiben ez több, mint egy lista:** a `cmd` oszlop miatt látszik, hogy
**három billentyű két-két külön parancsot** takar attól függően, melyik
menüből jön:

- `Ctrl+3` → `0x9c8f` (Nézet ▸ Szerkesztési nézet) **vagy** `0x9ca0`
  (Kép ▸ Megjelenítés és szerkesztés),
- `Ctrl+4` → `0x9c9f` (Nézet ▸ Diavetítés) **vagy** `0x9c6d`
  (Mappa/Album ▸ Diavetítés megtekintése),
- `Ctrl+Enter` → `0x9c99` (fájl) **vagy** `0x9cba` (mappa/album).

Fordítva pedig **egy parancs két billentyűn**: a `0x9c9a`
(„törlés a lemezről") a menüsávban `Delete`, a helyi menükben
`Ctrl+Delete` (ld. 4.).

### 3.4 Egy megfigyelt furcsaság: a menüsávban a „Delete" angolul marad

A magyar felületen a **Fájl ▸ Törlés lemezről** melletti billentyű
`Delete` (angolul), a **a kép helyi menüjében** ugyanez `Ctrl+Törlés`
(magyarul) — mindkettő a felhasználó képernyőképén.
Mindkét helyen ugyanaz a kulcs adja a szöveget: `CMenuBar::Delete`
(`0x00c8c494`), amelynek magyar értéke a `stringres`-ben **„Törlés"**.

Alátámasztott magyarázat (nem bizonyított): a menüsáv-tábla
**egyszer**, nagyon korán épül (a `0x0055916f`-es „már megvolt" kapu),
a helyi menük viszont fókuszváltáskor újraépülnek (`0x00537fb0`
hívása a `0x0056bd8c`-en) — a menüsáv így az **angol
alapértelmezéssel** marad. Nálunk ennek nincs következménye: mi
mindkét helyen a magyar nevet írjuk ki.

---

## 4. A `C` forrás: a helyi menük gyorsbillentyűi

A helyi menük ugyanazt a 20 bájtos rekordot töltik, csak a veremben
vagy külön globális blokkban; a tételt hozzáadó függvény a
`0x00a6aee0`, ez hívja a feliratkészítő `0x00a6b250`-t. A `0x00a6aee0`
**27 hívója** közül **kilencben** van gyorsbillentyű, összesen **44
rekordon**:

| építő | melyik menü | gyorsbillentyűk |
|---|---|---|
| `0x00730790` | mappa-nézetbeli **kép** helyi menüje | `Enter` (Megjelenítés és szerkesztés, `0x9ca0`) · `Ctrl+R` · `Ctrl+Shift+R` · `Ctrl+Shift+O` · `Ctrl+S` · `Ctrl+Enter` · **`Ctrl+Delete`** (Törlés a lemezről, `0x9c9a`) · `Alt+Enter` |
| `0x00731050` | album-nézetbeli **kép** helyi menüje | ugyanaz, de a `Ctrl+Delete` felirata **„Eltávolítás az albumból"** (azonos `cmd 0x9c9a`) |
| `0x007319f0` | **mappa** helyi menüje | `Ctrl+A` (`0x9cb8`) · `Ctrl+D` (`0x9c90`) · `Ctrl+I` (`0x9c47`) · `Ctrl+Enter` (`0x9cba`) |
| `0x00732160` | **album** helyi menüje | `Ctrl+A` · `Ctrl+D` · `Ctrl+I` |
| `0x007327a0` | **néző** (OneUp) helyi menüje, tábla `0xd6eb90`-től | **`Esc`** (Visszatérés a könyvtárhoz, `0x9cc6`) · `Ctrl+R` · `Ctrl+Shift+R` · `Ctrl+Shift+O` · `Ctrl+S` · `Ctrl+Enter` · `Ctrl+Delete` · `Alt+Enter` |
| `0x00732ee0` | **képtálca** helyi menüje, tábla `0xd6edd4`-től | **`Ctrl+H`** (Kijelölés megtartása, `0x9cca`) · `Ctrl+R` · `Ctrl+Shift+R` · `Ctrl+Enter` · `Alt+Enter` |
| `0x00733a40` | gyűjtemény/mappalista, tábla `0xd6f164` | `Ctrl+Enter` (`0x9cba`) |
| `0x007355c0` | **Emberek**-album képének helyi menüje, `0xd6f890`-től | `Enter` · `Ctrl+Enter` · `Ctrl+Delete` (Eltávolítás az Emberek albumból) · `Alt+Enter` |
| `0x007359e0` | **Emberek**-album helyi menüje, `0xd6f9d0`-től | `Ctrl+A` · `Ctrl+D` · `Ctrl+I` |

**Négy olyan kombináció van, amely CSAK helyi menüben létezik** — a
menüsávban egyikük sem szerepel: `Enter` (megjelenítés és szerkesztés),
`Esc` (visszatérés a könyvtárhoz), `Ctrl+H` (megtartás a tálcán) és
`Ctrl+Delete` (törlés a lemezről).

**A törlés billentyűje felület-függő** (a `picasa-eger-es-kijeloles.md`
is így írja le): rácsban/nézőben `Ctrl+Delete`, a menüsávban `Delete`.
A `cmd` azonos (`0x9c9a`), tehát **egy parancs, két belépő**.

---

## 5. A hat kérdés funkciónként

A funkció-feltárás módszertana szerint minden vezérlőnél hat kérdés jár.
Az alábbi tábla **32 sorban** mind a **34 egyedi kombinációra**
válaszol (a `Delete`/`Ctrl+Delete` és a `Home`/`End` egy-egy közös
sorban).

⚠️ **Bizonyítottsági fok oszloponként.** A „billentyű", a „felirat" és a
„menü-pár" oszlop **mérve** van (rekordtábla + `stringres` +
képernyőkép). A „mikor tiltott" oszlop **csak ott mérés**, ahol a
képernyőképen a tétel **szürke** — ezt vastagon jelöltük; a többi a menü
szerkezetéből **következtetés**. A „mit csinál", a „mire hat" és a „mit
mutat közben" oszlop ott mérés, ahol kódcím áll mellette
(`0x00716f40`, `0x00718a50`), egyébként a felület megfigyeléséből
származik. Ahol semmink sincs, ott **„nincs mérve"** áll.

| billentyű | felirat | mit csinál | mikor tiltott | mire hat | menü-pár | mit mutat közben |
|---|---|---|---|---|---|---|
| `Ctrl+N` | Új album… | album (címke) létrehozása | soha | könyvtár | Fájl ▸ | modális „Új album" párbeszéd |
| `Ctrl+O` | Fájl felvétele a Picasába… | fájl(ok) felvétele az indexbe | soha | könyvtár | Fájl ▸ | fájlválasztó |
| `Ctrl+M` | Importálás forrása… | importálás eszközről/mappából | soha | könyvtár | Fájl ▸ | Importálás képernyő |
| `Ctrl+Shift+O` | Fájl(ok) megnyitása szerkesztőben | külső szerkesztő indítása | **kép-kijelölés nélkül** (a képernyőképen mappa-kijelölésnél szürke) | a kijelölt fájlok | Fájl ▸ · a kép helyi menüje („Fájl megnyitása") | külső alkalmazás nyílik |
| `F2` | Átnevezés… | fájl/mappa/album átnevezése | nincs kijelölés | kijelölés | Fájl ▸ · Mappa ▸ | Átnevezés párbeszéd |
| `Ctrl+S` | Mentés | a függő szerkesztések kiírása | **ha nincs mentetlen szerkesztés** (a képernyőképen szürke) | a kijelölt kép(ek) | Fájl ▸ · a kép helyi menüje | mentés-folyamatjelző |
| `Ctrl+Shift+S` | Kép exportálása mappába… | méretezett másolat kiírása | nincs kép kijelölve | kijelölés | Fájl ▸ | Exportálás párbeszéd |
| `Ctrl+Enter` | Keresés a lemezen | a fájl/mappa megmutatása az Intézőben | nincs kijelölés | kijelölés | Fájl ▸ · négy helyi menü | Intéző-ablak nyílik |
| `Delete` / `Ctrl+Delete` | Törlés (a) lemezről | törlés a Lomtárba | nincs kijelölés | kijelölés | Fájl ▸ (`Delete`) · helyi menük (`Ctrl+Delete`) | megerősítő párbeszéd |
| `Ctrl+P` | Nyomtatás… | nyomtatási elrendezés | nincs kép | kijelölés | Fájl ▸ | Nyomtatás képernyő |
| `Ctrl+E` | E-mail… | küldés e-mailben | nincs kép | kijelölés | Fájl ▸ | levélküldő párbeszéd |
| `Ctrl+X` | Kivágás | vágólapra + eltávolítás | **nincs mérve** (a képernyőképen aktív) | kijelölés | Szerkesztés ▸ | — |
| `Ctrl+C` | Másolás | vágólapra | **nincs mérve** (a képernyőképen aktív) | kijelölés | Szerkesztés ▸ | — |
| `Ctrl+V` | Beillesztés | vágólapról | **nincs mérve** (a képernyőképen aktív) | aktuális album/mappa | Szerkesztés ▸ | — |
| `Ctrl+A` | Az összes kijelölése | **az aktuális mappa** összes képe (`0x00716f40`) | üres mappa | **egy mappa** (soha nem a könyvtár) | Szerkesztés ▸ · 4 helyi menü | a bélyegképek kijelölt állapotba váltanak, **egy** érvénytelenítéssel |
| `Ctrl+I` | Kiválasztás megfordítása | kijelölés invertálása | üres mappa | egy mappa | Szerkesztés ▸ · 4 helyi menü | — |
| `Ctrl+D` | Kijelölés törlése | kijelölés nullázása (`0x00718a50`) | nincs kijelölés | egy mappa | Szerkesztés ▸ · 4 helyi menü | — |
| `Ctrl+1` | Kis indexképek | bélyegkép-méret előbeállítás | — | könyvtárnézet | Nézet ▸ | a rács átméreteződik, a tétel pipát kap |
| `Ctrl+2` | Normál indexképek | ugyanaz, nagyobb méret | — | könyvtárnézet | Nézet ▸ | pipa a tételen |
| `Ctrl+3` | Szerkesztési nézet / Megjelenítés és szerkesztés | átvált a nagyképes szerkesztőre | **nincs kép kijelölve** (a Nézet-menüben szürke) | a kijelölt kép | Nézet ▸ (`0x9c8f`) · Kép ▸ (`0x9ca0`) | a könyvtár helyére a néző lép |
| `Ctrl+T` | Címkék | a **címkepanel** be/ki | — | jobb oldali panel | Nézet ▸ | a panel becsúszik |
| `Ctrl+4` | Diavetítés | teljes képernyős diavetítés | üres mappa | aktuális mappa/album | Nézet ▸ (`0x9c9f`) · Mappa ▸ (`0x9c6d`) | teljes képernyős vetítés indul |
| `Ctrl+5` | Időrend | idővonal-nézet | — | könyvtár | Nézet ▸ | idővonal-nézetre vált |
| `Ctrl+Shift+P` | Indexképek nyomtatása… | kontaktmásolat nyomtatása | üres mappa | aktuális mappa/album | Mappa ▸ | Nyomtatás képernyő |
| `Ctrl+R` | Forgatás jobbra | +90° forgatás (`.picasa.ini`) | nincs kép | kijelölés | Kép ▸ · 4 helyi menü | a bélyegkép azonnal fordul |
| `Ctrl+Shift+R` | Forgatás balra | −90° forgatás | nincs kép | kijelölés | Kép ▸ · 4 helyi menü | ugyanaz |
| `Alt+Enter` | Tulajdonságok | a tulajdonságpanel be/ki | — | a kijelölt kép | Kép ▸ · 5 helyi menü | a panel becsúszik |
| `F1` | Súgó – tartalom és tárgymutató | súgó megnyitása | soha | — | Súgó ▸ | böngésző/súgóablak |
| `Enter` | Megjelenítés és szerkesztés | a rácsból a nézőbe lép (`0x9ca0`) | nincs kijelölés | a kijelölt kép | **csak** a kép helyi menüje (félkövér = alapértelmezett tétel) | a néző nyílik |
| `Esc` | Visszatérés a könyvtárhoz | a nézőből vissza (`0x9cc6`) | csak nézőben él | — | **csak** a néző helyi menüje | a könyvtár tér vissza |
| `Ctrl+H` | Kijelölés megtartása | a kijelölés rögzítése a képtálcán (`0x9cca`) | üres tálca | képtálca | **csak** a tálca helyi menüje | a tálca tétele „tartott" jelet kap |
| `Home` / `End` | — | az **aktuális mappa** első/utolsó képére szűkíti a kijelölést | — | egy mappa | nincs | a kijelölés ugrik és odagörget |

*(A `Ctrl+Home` / `Ctrl+End` / `Shift+Home` / `Shift+End` /
`PageUp` / `PageDown` / nyilak teljes leképezése — külön mérve — a
[picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) **12.**
szakaszában van; ez a lap nem ismétli meg.)*

---

## 6. Összevetés a mai PicasaPy-jal

Forrás: `src/picasapy/app/qml/Main.qml`,
`src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml`,
`…/DocumentTabStrip.qml`, `…/PhotoViewer.qml`,
`…/SlideshowView.qml`, `…/LightboxFeed.qml`, `…/CollageCanvas.qml`.

**Nálunk ma 20 `Shortcut` elem van**, 18 különböző kombinációval.

| billentyű | eredeti funkció | nálunk | hol |
|---|---|---|---|
| `Ctrl+A` | Az összes kijelölése | ✅ **megvan** | `Main.qml:511` |
| `Ctrl+D` | Kijelölés törlése | ✅ megvan | `Main.qml:512` |
| `Ctrl+I` | Kiválasztás megfordítása | ✅ megvan | `Main.qml:513` |
| `Ctrl+S` | Mentés | ✅ megvan | `Main.qml:518` |
| `Ctrl+R` | Forgatás jobbra | ✅ megvan | `Main.qml:545` |
| `Ctrl+Shift+R` | Forgatás balra | ✅ megvan | `Main.qml:552` |
| `Ctrl+4` | Diavetítés | ✅ megvan | `Main.qml:560` |
| `Ctrl+T` | Címkék panel | ✅ megvan | `Main.qml:565` |
| `Alt+Enter` | Tulajdonságok | ✅ megvan (`Alt+Return`) | `Main.qml:571` |
| `Ctrl+5` | Időrend | ✅ megvan | `Main.qml:589` |
| `F2` | Átnevezés | ✅ megvan | `Main.qml:624` |
| `Ctrl+Shift+S` | Kép exportálása mappába | ✅ megvan | `Main.qml:629` |
| `Ctrl+Delete` | Törlés a lemezről (rács) | ✅ megvan | `Main.qml:637` |
| `Delete` | Törlés a lemezről (néző) | ⚠️ **eltér** – nálunk a `Delete` a **nézőhöz** van kötve, az eredetiben a **menüsávhoz**; a néző helyi menüjében az eredetiben `Ctrl+Delete` van | `Main.qml:645`, `PicasaMenuBar.qml:146` |
| `Ctrl+1` | Kis indexképek | ✅ megvan | `PicasaMenuBar.qml:130` |
| `Ctrl+2` | Normál indexképek | ✅ megvan | `PicasaMenuBar.qml:135` |
| `Ctrl+Enter` | Keresés a lemezen | ✅ megvan (`Ctrl+Return`) | `PicasaMenuBar.qml:140` |
| `Esc` | Visszatérés a könyvtárhoz | ⚠️ **eltér** – nálunk a `DocumentTabStrip` projektlap-váltása, a nézőben `Keys.onEscapePressed` | `DocumentTabStrip.qml:115`, `PhotoViewer.qml:471` |
| `Home` / `End` | első/utolsó kép a mappában | ✅ megvan | `LightboxFeed.qml:218` |
| `Ctrl+N` | Új album | ✅ megvan (#1616) | `PicasaMenuBar.qml` `shortcutNewAlbum` |
| `Ctrl+O` | Fájl felvétele a Picasába | ✅ megvan (#1633) | `PicasaMenuBar.qml:276` |
| `Ctrl+M` | Importálás forrása | ✅ megvan (#1615) | `PicasaMenuBar.qml:263` |
| `Ctrl+Shift+O` | Fájl(ok) megnyitása szerkesztőben | ❌ hiányzik — a felirat #1616 óta NEM hirdeti (a funkció teljesen hiányzik, nem csak a billentyű) | — |
| `Ctrl+P` | Nyomtatás | ✅ megvan (#1472) | `PicasaMenuBar.qml:237` |
| `Ctrl+E` | E-mail | ❌ hiányzik — a felirat #1616 óta NEM hirdeti (a `TrayBar.emailRequested()` jelzés sehova nincs bekötve) | — |
| `Ctrl+X` / `Ctrl+C` / `Ctrl+V` | Kivágás/Másolás/Beillesztés | ❌ hiányzik | — |
| `Ctrl+3` | Szerkesztési nézet / Megjelenítés és szerkesztés | ❌ hiányzik | — |
| `Ctrl+Shift+P` | Indexképek nyomtatása | ✅ megvan (#1590) | `PicasaMenuBar.qml:248` |
| `Ctrl+H` | Kijelölés megtartása a tálcán | ❌ hiányzik | — |
| `F1` | Súgó | ❌ hiányzik | — |
| **`Enter`** | Megjelenítés és szerkesztés (rácsból a nézőbe) | ✅ megvan (#1417) – a rács `Keys.onPressed` ága ugyanazt az `openRequested` jelet adja, mint a dupla kattintás | `LightboxFeed.qml:227` |

**A könyvtár-kiosztáson kívüli billentyűink** — ezek nem ütköznek a
fenti táblával:

- `F` és `Shift+F` az arckeretekhez a nézőben (`PhotoViewer.qml:483`) —
  **saját bővítés**, az eredetiben nincs;
- `Space` a videó lejátszás/szünethez (`PhotoViewer.qml:476`) — a keymap
  42. rekesze ugyanezt a funkciót a `/` billentyűre teszi, de a kötést a
  menükben **nem találtuk meg** (ld. 7.), ezért itt nem mondunk ki
  eltérést;
- `Ctrl+R` / `Ctrl+Shift+R` a diavetítésben (`SlideshowView.qml:92`) — az
  eredeti forgatás-billentyűje, más felületen;
- `Ctrl+A` / `Ctrl+D` / `Delete` a kollázsvásznon
  (`CollageCanvas.qml:222`) — **az eredetivel egyező**, ld.
  [kollazs-panel-ui-spec.md](kollazs-panel-ui-spec.md) 739. sor.

**Számokban — egyedi billentyűkombinációra vetítve.** A menüsáv 32
rekordja **28 egyedi** kombinációt takar (az `F2`, a `Ctrl+3`, a `Ctrl+4`
és a `Ctrl+Enter` két-két menüben is szerepel); ehhez jön a négy csak
helyi menüben élő (`Enter`, `Esc`, `Ctrl+H`, `Ctrl+Delete`) és a rács
`Home` / `End` billentyűje — **összesen 34**.

Ebből nálunk: **20 megvan**, **2 eltér** (`Delete`, `Esc`),
**12 hiányzik**.

---

## 7. Amit ez a kör NEM vizsgált (kimondva)

1. **A billentyűzet-szétosztó maga.** Megtaláltuk, hogy a
   parancsazonosítót a `0x005cb990` szétosztó bontja szét
   (`lea eax,[esi-0x9c42]` → bájttérkép `0x005cdb34` → ugrótábla
   `0x005cd9fc`, ld. `picasa-eger-es-kijeloles.md` 11.2), de **nem**
   fejtettük vissza, hol áll össze a *(billentyű, módosító) → cmd*
   leképezés a menün kívüli billentyűkre. Statikus tömböt kerestünk a
   48 azonosítóból — **nincs** a fájlban (16 és 32 bites mintára is
   nulla találat), tehát kódba írt elágazás.
2. **A 12 ⬜ jelű rekesz** (`Ctrl+K`, `Ctrl+W`, `Ctrl+Shift+B`,
   `Ctrl+Shift+E`, `Ctrl+F`, `Ctrl+Shift+H`, `Ctrl+Shift+V`, `F11`,
   `/`, `,`, `.`, 47.) — ezekhez **nem találtunk** menü- vagy
   helyimenü-kötést. Nem állítjuk, hogy nem működnek: azt állítjuk,
   hogy a **három feltárt forrásban nincsenek**.
3. **A videólejátszó billentyűzete** (`/`, `,`, `.`) — a
   `video_control_bar2/*` felület nincs feltárva.
4. **A szerkesztőpanel saját billentyűi** (`F8`/`F9` említések a
   `ui-audit-editor.md`-ben) — más lap hatóköre.
5. **A párbeszédek `Esc`-kezelése** — a `picasa-eger-es-kijeloles.md`
   8. szakasza (`escapekey 1`, 11 gomb) már leírja.
6. **Mac-változat** (`eMenuFileMac::*`, `eMenuPictureMac::*`) — a
   szövegtárban ott van, de nem célplatform.

---

## 8. Jegyjavaslatok (a hiányzókra, egyenként megvalósítható méretben)

A jegycím-szabály szerint mindegyikben nevesítve van a funkció:

1. **Az Enter billentyű megnyitja a nézőt a bélyegképrácsból** — ma csak
   dupla kattintás nyitja; az eredetiben az `Enter` a helyi menü
   félkövér, alapértelmezett tétele (`cmd 0x9ca0`).
2. **A Ctrl+3 átvált a szerkesztési nézetre** — az eredetiben a Nézet- és
   a Kép-menüből is (`0x9c8f`, illetve `0x9ca0`).
3. ✅ **MEGVAN (#1616).** ~~A Ctrl+N létrehoz egy új albumot a
   menüsávból~~ — a fenti állítás („a menüpont megvan, gyorsbillentyű
   nincs hozzákötve") a mai kódon TÉVES volt: a menütétel is
   `placeholder` volt, nem csak a billentyű hiányzott (MÉRVE:
   `git log -S'menuFileNewAlbum'`). A #1616 mindkettőt bekötötte, a
   meglévő `newAlbumDialog`/`controller.createAlbum` útvonalra.
4. ✅ **MEGVAN** — a Ctrl+O (#1633) és a Ctrl+M (#1615) megnyitja a
   felvétel- és az importálás-párbeszédet.
5. **A Ctrl+Shift+O megnyitja a kijelölt fájlokat külső szerkesztőben** —
   a funkció nálunk teljesen hiányzik. A #1616 a feliratból kivette a
   gyorsbillentyűt (addig hirdetett, de soha nem élt) — ez a jegy
   önmagában továbbra is nyitott.
6. ✅ **A Ctrl+P megvan (#1472).** A Ctrl+E (e-mailezés) továbbra is
   nyitott — a `TrayBar.emailRequested()` jelzés sehova nincs bekötve; a
   #1616 a feliratból kivette a gyorsbillentyűt.
7. **A Ctrl+Shift+P kinyomtatja az indexképeket a mappamenüből.**
8. **A Ctrl+H megtartja a kijelölést a képtálcán** — a tálca helyi menüjének
   egyetlen saját gyorsbillentyűje.
9. **Az F1 megnyitja a súgót** — a Súgó-menüpont ma helyőrző.
10. **A Ctrl+X / Ctrl+C / Ctrl+V a Szerkesztés menüből is működik** —
    ma egyik sincs bekötve.
11. **A törlés gyorsbillentyűje felület szerint válik szét** — az
    eredetiben a menüsávban `Delete`, a rács- és a néző helyi menüjében
    `Ctrl+Delete`; nálunk fordítva van bekötve (rács `Ctrl+Delete`,
    néző `Delete`), és a menüsáv `Delete`-je a rácsra is elsül.

---

## 9. Reprodukció

A keymap-erőforrások kinyerése (a DLL PE-erőforrástáblájából) és a
menürekordok kiolvasása egy-egy rövid szkripttel megismételhető; a
diszasszembláláshoz a privát repó `eszkozok/pe_dis.py`-ja + `capstone`
kell (a gépen lévő `objdump` ARM-célú, i386-ot nem tud). A
menürekord-kiolvasó lényege: a `0x00559150` (illetve a helyimenü-építők)
utasításfolyamán végigmenve követni kell az `esp`-eltolást, a
`0x009ae560(kulcs, alapértelmezés)` hívásokat és a rekordmezőkbe írt
konstansokat — a `+0x04…+0x0a` mezők a **következő** tétel blokkjában
íródnak ki.

---

## 5. A `Delete` billentyű KONTEXTUSFÜGGŐ: albumban nem lemezről töröl (2026-08-27)

A 3.3 szakasz azt írta le, hogy **egy parancs két billentyűn** ül
(`0x9c9a`: menüsávban `Delete`, helyi menükben `Ctrl+Delete`). Kimaradt
belőle a másik irány: **ugyanaz a billentyű két parancson**, a nézettől
függően.

### A bizonyíték

A hivatalos szövegforrásban (`stringres-en-hu.tsv`) a két tétel
**azonos gyorsbillentyűt hirdet**:

| kulcs | angol | magyar |
|---|---|---|
| `IDS_DELETE_FROM_DISK` | `Delete from Disk\tDelete` | `Törlés lemezről\tDelete` |
| `IDS_REMOVE_FROM_LABEL` | `Remove from Album\tDelete` | `Eltávolítás az albumból\tTörlés` |

és a bináris index szerint **ugyanabban a menüépítőben** ülnek —
`0x0056c5a0` és `0x0056e1c0`, ez a `CThumbUI` rács-menüje (ugyanitt van
`CThumbUI::locateondiskmenu`, `ThumbUI::PeopleCMEmpty`,
`IDS_LOCATE_ON_DISK`).

Ezt megerősíti a helyi menük oldaláról a 4. szakasz mérése is: a
`0x00731050` (album-nézetbeli kép helyi menüje) **ugyanazt a
`cmd 0x9c9a`-t** hordozza, csak a felirata **„Eltávolítás az albumból"**;
a `0x007355c0`-n (Emberek-album) pedig „Eltávolítás az Emberek albumból".

**Vagyis a `0x9c9a` parancs jelentése a NÉZETTŐL függ:**

| nézet | a parancs jelentése | mit csinál az adattal |
|---|---|---|
| mappa | Törlés a lemezről | Lomtárba (`SHFileOperationW`, `0x009b1d50`) |
| album | Eltávolítás az albumból | a fájl **marad a lemezen** |
| Emberek-album | Eltávolítás az Emberek albumból | a fájl **marad a lemezen** |

### Amit ez NEM dönt el

A `CThumbUI` menüje `\tDelete`-et hirdet, a 4. szakasz rekord-mérése
viszont a kép helyi menüjére `Ctrl+Delete`-et adott. A kettő **más
felület** (rács-menü vs. kép helyi menüje), de a szétválásuk pontos
határa nincs megmérve — ehhez a `0x0056c5a0` rekord-ciklusának
diszasszemblálása kell. Ez **nem befolyásolja** a fenti megállapítást: a
parancs jelentése akkor is nézetfüggő, ha a billentyű felülete vitatott.

### Nálunk (mérve, 2026-08-27)

`PicasaMenuBar.qml:189-194` — a `Delete` **feltétel nélkül**
`bar.deleteRequested()`-et hív, azaz mindig lemezről töröl. Album-nézetre
**nincs elágazás**. Az „Eltávolítás az albumból" tétel létezik
(`PhotoContextMenu.qml:117`), de a billentyűhöz nincs kötve.

*Bizonyítottsági fok: **megerősített** a parancs nézetfüggő jelentése (a
szövegforrás és a 4. szakasz rekord-mérése egybehangzóan);
**nyitva** a rács-menü és a kép helyi menüje közti billentyű-határ.*

### A menüsáv ága JAVÍTVA (#1608, 2026-08-27)

A `PicasaMenuBar` `Delete` billentyűje és a `Fájl ▸` tétele ettől kezdve
egyetlen közös belépőn (`activateDeleteCommand()`) megy át, és a nézet
szerint ágazik el — a **felirat is** (`deleteCommandText`):

| nézet | felirat | mit hív |
|---|---|---|
| mappa | Törlés lemezről | `deleteRequested()` → Lomtár |
| album | Eltávolítás az albumból | `removeFromAlbumRequested()` |
| Emberek-album | Eltávolítás az Emberek albumból | `removeFromPeopleAlbumRequested()` |

Mérve mindhárom nézetre, valódi billentyűeseménnyel, és a „lemezen marad"
állítás a fájl létezésén (`tests/app/qml_functional/test_album_delete_billentyu_1608.py`).

### A HELYI menü ága — mérve, MÁS a hibaalak (2026-08-27)

A kép helyi menüje (`PhotoContextMenu.qml`) nézetenként mérve:

| nézet | „Törlés lemezről" tétel | eltávolító tétel |
|---|---|---|
| mappa | látszik, `\tCtrl+Delete` | — |
| album | **látszik**, `\tCtrl+Delete` | „Eltávolítás az albumból", **billentyű nélkül** |
| Emberek-album | **látszik**, `\tCtrl+Delete` | „Eltávolítás az Emberek albumból", **billentyű nélkül** |

Az eredetiben (4. szakasz, `0x00731050` és `0x007355c0`) ezekben a
nézetekben **egyetlen** ilyen tétel van: ugyanaz a `Ctrl+Delete`,
**átcímkézve** eltávolításra. Nálunk tehát két eltérés van:

1. album- és Emberek-nézetben **is kínálunk** „Törlés lemezről /
   `Ctrl+Delete`" tételt, amit az eredeti ott nem ad;
2. a `Main.qml` `shortcutDeleteFromDiskGrid` (`Ctrl+Delete` a rácsban)
   **nézettől függetlenül** lemezről töröl — ez a #1608 hibaosztálya a
   másik felületen.

A feliratok maguk HELYESEK, és az eltávolító tételek műveletei is. Ez a
két pont ezért **külön jegy** tárgya; ez a lap rögzíti a mérést.

### A RÁCS ága JAVÍTVA (#1619, 2026-08-27)

**A mai állapot mérése a javítás előtt** (a rács `Ctrl+Delete`-je, valódi
billentyűeseménnyel, a megnyíló megerősítőt is lenyomva):

| nézet | mit tett a rács `Ctrl+Delete`-je | a fájl a lemezen |
|---|---|---|
| mappa | törlés-megerősítőt nyitott, megerősítve a Lomtárba tett | **eltűnt** (helyes) |
| album | UGYANAZT | **eltűnt** — ADATVESZTÉS |
| Emberek-album | UGYANAZT | **eltűnt** — ADATVESZTÉS |

Az album-tagság ráadásul **érintetlen maradt**: a `.picasa.ini`
`albums=` sora megmaradt, tehát a művelet nem is azt tette, amit a
felhasználó kért.

**A javítás.** A `Ctrl+Delete` UGYANAZ a parancs (`0x9c9a`), csak másik
belépő, ezért a #1608-ban készült **közös elágazáson** megy át
(`PicasaMenuBar.activateDeleteCommand()`) — nem másolt logikán, így a
kettő nem tud különböző dolgot csinálni:

| nézet | mit hív | a fájl |
|---|---|---|
| mappa | `deleteRequested()` → Lomtár | törlődik |
| album | `removeFromAlbumRequested()` | **marad** |
| Emberek-album | `removeFromPeopleAlbumRequested()` | **marad** |

A **helyi menü** pedig nézetenként egyetlen, átcímkézett tételt kínál —
ahogy az eredeti `0x00730790` / `0x00731050` / `0x007355c0`:

| nézet | a `Ctrl+Delete`-et viselő tétel | „Törlés lemezről" tétel |
|---|---|---|
| mappa | „Törlés lemezről\tCtrl+Delete" | ez maga |
| album | „Eltávolítás az albumból\tCtrl+Delete" | **nincs** |
| Emberek-album | „Eltávolítás az Emberek albumból\tCtrl+Delete" | **nincs** |

Ez egybevág a `ui-audit-context-menus.md` 6.1-gyel is: az
`AlbumPhoto::ID_FILE_DELETEFROMDISK` felirata a string-táblában **„Remove
from Album"** — vagyis a két tétel az eredetiben EGY parancsrekesz.

Őr: `tests/app/qml_functional/test_racs_ctrl_delete_1619.py` — valódi
`Ctrl+Delete` billentyűeseménnyel ÉS a helyi menüpont aktiválásával, a
megerősítőt végigvive, a „lemezen marad" a `Path.exists()`-en mérve.
Kétirányú mutáció: az elágazást kivéve 6 teszt bukik (köztük a
lemez-szintű), a „soha ne törölj" változattal 5 mappa-nézeti teszt.

*Marad nyitva* (a fentebbi „Amit ez NEM dönt el" szakasz): a `CThumbUI`
rács-menü `\tDelete`-je és a kép helyi menüje `Ctrl+Delete`-je közti
pontos felület-határ.

---

## 10. A `D` forrás: a könyvtárnézet SAJÁT billentyűkezelője (#442, 2026-09-03)

> **Ez a szakasz a 7.1 pontot zárja le.** A 7.1 így szólt: *„nem
> fejtettük vissza, hol áll össze a (billentyű, módosító) → cmd leképezés
> a menün kívüli billentyűkre. Statikus tömböt kerestünk a 48
> azonosítóból — nincs a fájlban … tehát kódba írt elágazás."*
> **A feltevés helyes volt: kódba írt elágazás. Meg is van.**

### 10.1 A kezelő és a két táblája

A könyvtárnézet billentyűkezelője a **`0x005e60d0`**. Nem
accelerator-táblából dolgozik, hanem fordító által generált ugrótáblás
`switch`-ből:

```
0x005e61a8  movsx edi, word ptr [esi+8]            ; a virtuális billentyűkód
0x005e61de  lea eax, [edi - 0xd]
0x005e61e1  cmp eax, 0x6b
0x005e61e4  ja  0x5e65f7                           ; tartományon kívül -> nincs teendő
0x005e61ea  movzx ecx, byte ptr [eax + 0x5e66a4]   ; INDEXTÁBLA, 108 bájt
0x005e61f1  jmp dword ptr [ecx*4 + 0x5e6614]       ; UGRÓTÁBLA, 36 bejegyzés
```

⇒ kezelt tartomány **VK `0x0D`…`0x78`**; indextábla `0x005e66a4`,
ugrótábla `0x005e6614`. Mindkettő közvetlenül kiolvasható — **ezért nem
kellett statikus azonosító-tömb.**

### 10.2 A módosítók

A `[esi+0x10]` bájt három bitje a módosítókat hordozza; a kezelő a
**4-es bitet megköveteli** (`0x005e6178`: `test byte ptr [esi+0x10], 4` /
`jle` a kihagyó ágra). A `0x005c5f90` egy 16 bájtos szerkezetbe teszi őket:

| mező | forrás | hol vizsgálják |
|---|---|---|
| `+0`, `+3` | a **4**-es bit | a belépési kapu |
| `+1`, `+4` | a **2**-es bit | `[esp+0x11]` az ágakban |
| `+2`, `+5` | a **8**-as bit | `[esp+0x12]` az ágakban |
| `+8` | a billentyűkód | – |

**Azonosítás** *(a `Ctrl`-re **megerősített**, ld. 10.9; a `Shift`/`Alt`-ra
**erős**, két független egyezésből)**:** a `3` ág a
`thumbui/fullview`-t kattintja, és a lap 3.3 táblája szerint a
szerkesztési nézet billentyűje `Ctrl+3` ⇒ a **kötelező 4-es bit = `Ctrl`**;
az `R` ág a 2-es bitre ágazik, és a forgatás `Ctrl+R` / `Ctrl+Shift+R` ⇒ a
**2-es bit = `Shift`**, a maradék **8-as bit = `Alt`**.

### 10.3 A teljes kiosztás — mind a 34 ág

A „kattint" azt jelenti, hogy az ág a `0x009cd8a0(elemnév)`-et hívja: ez
feloldja az elemet és meghívja a **vtable `+0x78`** metódusát `(0, 0)`
argumentumokkal.

| billentyű | ág | mit csinál |
|---|---|---|
| `Ctrl+Enter` | `0x005e61f8` | `0x005c8320(panel, 0)` |
| `Ctrl` + VK `0x12` | `0x005e65dc` | `[panel+0xe78]` őr, `[panel+0xe70]` azonosító |
| **`Ctrl+0`** | `0x005e6206` | **kattint: `thumbui/toggle_right_drawer`** |
| `Ctrl+1` | `0x005e6215` | kattint: `thumbui/smallthumbs` |
| `Ctrl+2` | `0x005e6224` | kattint: `thumbui/largethumbs` |
| `Ctrl+3` | `0x005e624f` | kattint: `thumbui/fullview` |
| `Ctrl+4` | `0x005e625e` | `0x005696c0` őr → `(0, panel)` |
| `Ctrl+5` | `0x005e6279` | ugyanaz az őr → `(1, panel)` |
| `Ctrl+6` | `0x005e6294` | `0x00530ad0(panel)` |
| `Ctrl+8` | `0x005e6584` | `0x005e81e0(panel, 2)` |
| **`Ctrl+9`** | `0x005e629f` | `0x00579330` őr → **kattint: `editpanel/toggle_left_drawer`** |
| `Ctrl+A` | `0x005e6471` | `0x00579330` őr → `0x005e5070(panel)` |
| **`Ctrl+Shift+B`** | `0x005e6370` | `0x005fe370(panel, "bw")` |
| `Ctrl+C` / `Ctrl+X` | `0x005e63f5` | `0x005fe9f0`; a `cmp edi, 0x58` választja szét |
| `Ctrl+D` | `0x005e6492` | `0x00579330` őr → `0x005e5310` |
| **`Ctrl+Shift+E`** | `0x005e638b` | `0x005fe370(panel, "enhance")` |
| **`Ctrl+F`** | `0x005e63bb` | **kattint: `searchcontainer/searchbutton`** |
| `Ctrl+G` (+Alt/+Shift) | `0x005e6518` | `[esp+0x12]`/`[esp+0x11]` szerint → `0x0057b050` |
| **`Ctrl+Shift+H`** | `0x005e63d6` | `0x005eef30(panel, 2)` |
| `Ctrl+I` | `0x005e64f6` | `0x00579330` őr → `0x005e5370(panel)` |
| **`Ctrl+K`** **és** `Ctrl+T` | `0x005e650e` | **ugyanaz az ág**: `0x0065ab00` |
| `Ctrl+Shift+L` | `0x005e658e` | `0x004cce10([panel+0x2c4])` |
| `Ctrl+M` | `0x005e63ca` | `0x005d3010(panel)` |
| `Ctrl+N` | `0x005e6462` | kattint: `thumbui/newalbum` |
| `Ctrl+O` (+Shift) | `0x005e6233` | Shifttel `0x005c80e0`, anélkül `0x005feb30` |
| `Ctrl+P` (+Shift) | `0x005e6428` | `0x005696c0` őr + Shift-ág |
| `Ctrl+R` (+Shift) | `0x005e633e` | `0x00562bf0` őr + Shift-ág |
| `Ctrl+S` (+Alt) | `0x005e64b4` | `0x005696c0` őr + `[esp+0x12]` ág |
| `Ctrl+Shift+U` | `0x005e6557` | `0x0047ca60([panel+0x2bc])` |
| **`Ctrl+Shift+V`** | `0x005e6408` | `0x005eef30(panel, 1)` |
| `Ctrl+Shift+Y` | `0x005e6572` | `0x005e5ec0(panel)` |
| `Ctrl+F6` | `0x005e62bb` | `searchoptions/dupesearch` (feloldás `0x009c2fc0`) |
| `Ctrl+F7` | `0x005e62e8` | `searchoptions/loadsim`, azonosító `0x15` |
| `Ctrl+F8` | `0x005e631d` | `searchoptions/clearsim`, azonosító `0x16` |
| `Ctrl+F9` | `0x005e6329` | billenti a `[panel+0xdc4]` bájtot |

### 10.4 ⭐ Ez zárja le a 7.2 pont tizenkét ⬜ rekeszéből HETET

A 7.2 tizenkét olyan keymap-rekeszt sorolt fel, amihez „nem találtunk
menü- vagy helyimenü-kötést". Ebből a `D` forrás **hetet** megold:

| rekesz | hol van a kötése |
|---|---|
| `Ctrl+K` | `0x005e650e` — **ugyanaz az ág, mint a `Ctrl+T`** |
| `Ctrl+Shift+B` | `0x005e6370` — a `bw` szűrő |
| `Ctrl+Shift+E` | `0x005e638b` — az `enhance` szűrő |
| `Ctrl+F` | `0x005e63bb` — `searchcontainer/searchbutton` |
| `Ctrl+Shift+H` | `0x005e63d6` — `0x005eef30(panel, 2)` |
| `Ctrl+Shift+V` | `0x005e6408` — `0x005eef30(panel, 1)` |
| `Ctrl+W` | **NINCS ág** — negatív eredmény, ld. lent |

A maradék öt (`F11`, `/`, `,`, `.`, 47.) **a kezelő tartományán kívül
esik**: az `F11` a `0x7A`, az írásjelek a `0xBC`–`0xBF` tartományban
vannak, a dispatch viszont `0x0D`…`0x78`-ig tart. ⇒ ezek **nem itt**
kötődnek (a videólejátszóra a 7.3 pont áll).

### 10.5 Negatív eredmény, mérve — amire NINCS ág

Az indextábla ezekre a kihagyó ágra (`0x005e65f7`) mutat:
**`Ctrl+7`, `Ctrl+J`, `Ctrl+Q`, `Ctrl+W`, `Ctrl+Z`, `Ctrl+F1`…`Ctrl+F5`**,
és a `0x0E`–`0x2F` tartomány minden billentyűje (`Esc`, `Space`, nyilak,
`Home`/`End`, `PageUp`/`PageDown`, `Insert`, `Delete`) — **egyetlen
kivétellel: VK `0x12`**.

⇒ **Ezekre a PicasaPy se kössön semmit** a könyvtárnézetben.

### 10.6 Az F12 kivétele

A dispatch előtt áll egy külön ág (`0x005e616a`): ha a billentyű
**VK `0x7B` (F12)**, a kezelő `[esp+0x24] = 1`-et állít és **átugorja a
módosító-kaput**. Maga az F12 viszont a dispatch tartományán kívül esik
(`0x7B − 0x0D = 0x6E > 0x6B`), tehát **ez a függvény nem kezeli** — a
jelző máshol hasznosul. *(Hol: NINCS MÉRVE.)*

### 10.7 Nálunk (mérve, 2026-09-03)

A `src/picasapy/app/qml/` **27 `Shortcut` eleme**, 24 különböző
kombinációval: `Ctrl+1`, `Ctrl+2`, `Ctrl+4`, `Ctrl+5`, `Ctrl+A`, `Ctrl+D`,
`Ctrl+Delete`, `Ctrl+I`, `Ctrl+M`, `Ctrl+N`, `Ctrl+O`, `Ctrl+P`, `Ctrl+R`,
`Ctrl+Return`, `Ctrl+S`, `Ctrl+Shift+P`, `Ctrl+Shift+R`, `Ctrl+Shift+S`,
`Ctrl+T`, `Ctrl+X`, `Alt+Return`, `Delete`, `Esc`, `F2`.

A `D` forrás **34 ágából** ezzel **hiányzik**: `Ctrl+0`, `Ctrl+3`,
`Ctrl+6`, `Ctrl+8`, `Ctrl+9`, `Ctrl+C`, `Ctrl+F`, `Ctrl+G`, `Ctrl+K`,
`Ctrl+Shift+B`, `Ctrl+Shift+E`, `Ctrl+Shift+H`, `Ctrl+Shift+L`,
`Ctrl+Shift+U`, `Ctrl+Shift+V`, `Ctrl+Shift+Y`, `Ctrl+F6`, `Ctrl+F7`,
`Ctrl+F8`, `Ctrl+F9` — **húsz**. Bekötés: **#2163**.

### 10.8 Bizonyítottsági fok

**Megerősített:** a dispatch szerkezete, a két tábla címe és tartalma, a
34 ág célcíme, a nyolc elemnév, a `0x009cd8a0` kattintás-szemantika és a
mi oldalunk (mind közvetlen kiolvasás, illetve grep).
**Erős:** a `Ctrl`/`Shift`/`Alt` bit-azonosítás (két független egyezés a
lap 3.3 táblájával).
**Nincs mérve:** a nem-kattintó ágak által hívott függvények *jelentése* —
csak a címük és az argumentumaik szerepelnek; továbbá az F12-jelző
felhasználási helye.

### 10.9 ⛔ HELYESBÍTÉS: a `0x005e60d0` a Ctrl-ÁG, nem a teljes kezelő (#2164, 2026-09-03)

A 10.1 a `0x005e60d0`-t „a könyvtárnézet billentyűkezelőjének" nevezte.
**Pontosabban:** ez a **Ctrl-ág**. A tényleges kezelő a **`0x005e6710`**
(780 b), és **egyetlen** helyről hívja a `0x005e60d0`-t:

```
0x005e680f  mov al, byte ptr [ebx+0x10]
0x005e6812  test al, 4
0x005e6814  jg  0x5e69cc            ; a 4-es bit BE -> a Ctrl-tábla
   …
0x005e69cc  push edi ; mov eax, ebx
0x005e69cf  call 0x5e60d0
```

⇒ **A `Ctrl` azonosítása ezzel MÉRT, nem következtetett.** A 10.2 „erős"
minősítése **megerősítettre** javítva: az az ág megy a Ctrl-táblába,
amelyik a **4-es bitet** megköveteli, a nélküle futó ág pedig a
módosító nélküli billentyűket kezeli (lásd lent).

### 10.10 A MÓDOSÍTÓ NÉLKÜLI billentyűk — a `0x005e6710`-ben

A `0x005e6814` `jg`-je alatt, `WM_KEYDOWN`-ra (`cmp [ebx+4], 0x100`,
`0x005e681d`) a VK-t közvetlen `cmp ax, imm16` láncban vizsgálja
(`movzx eax, word ptr [ebx+8]`, `0x005e6836`):

| billentyű | cím | mit csinál |
|---|---|---|
| **F1** | `0x005e683a` | `0x0057c430(1)` őr → `0x005d0cd0`; egyébként `0x0057c430(2)` őr → **kattint: `editpanel/edithelpbutton`** (`0x00c948c4`) |
| **F2** | `0x005e68fd` | öt őr után (`0x0056c420`, `0x0056c110`, `0x00562d00`, `0x005f2650`, `0x0057c430(4)`) az átnevezés útja: `[edi+0xeac]` → `0x007166c0`, `0x0057d430`, `0x00532ec0` |
| **F3** | `0x005e69a4` | **kattint: `searchcontainer/searchbutton`** (`0x00c8f448`) — ugyanaz az elem, mint a `Ctrl+F` |
| **F4** | `0x005e696c` | `0x009cd110(`**`thumbui/startoggle`**`)` feloldás; ha `[eax+0x20e] == 0`, **kattint** rá (vtable `+0x78`) |
| **F5** | `0x005e6869` | `[edi+0x2c0]` → `0x004a46e0`, `0x00579480(0,1)`, `[ecx+0x166] = 1`, `0x0065b840` |
| **F11** | `0x005e68a0` | vtable `+0x24` kétszer, `[eax+0x3e]` billentése, majd `0x00983fc0` |
| **F12** | `0x005e69c2` | `call 0x005e60d0` — de az F12 a Ctrl-tábla tartományán **kívül** esik (10.6), tehát ott nem történik semmi |

**Bizalmi fok: megerősített** (közvetlen kiolvasás). A hívott függvények
*jelentése* nincs mérve — csak a címük, az őreik és az elemnevek.

### 10.11 ⛔ NEGATÍV EREDMÉNY: nincs MÁSIK ilyen kezelő (#2164)

A #2164 azt kérdezte, hol van a **szerkesztő**, a **diavetítés** és a
**videólejátszó** billentyűkezelője. Három, egymástól független mérés:

1. **A módosító-gépezet egyetlen helyen fut.** A billentyű-kombinációt
   építő `0x005c5f90` és az összevető `0x005c5fc0` **hívóinak száma:
   1 – 1**, mindkettő a `0x005e60d0`-ban (`0x005e61c2`, `0x005e61d1`).
   ⇒ **Átképezhető billentyű-kötés csak a Ctrl-táblában van.**
2. **Ugrótáblás VK-switch csak egy van.** A teljes `.text`-et
   végigpásztáztam a `jmp dword ptr [ecx*4 + imm32]` alakra: **174**
   ugrótáblás `switch` van, ebből **indextáblás** 14, és **egyetlen**
   olyan, amelyik `word ptr [reg+8]`-ból (a VK-ból) indexel: a
   `0x005e61f1` — a Ctrl-tábla.
3. **A videó írásjel-billentyűi sehol.** A `cmp ax, 0xBC` / `0xBE` /
   `0xBF` (`,` `.` `/`) alak — pontosan az, amivel a `0x005e6710` a
   többi VK-t hasonlítja — a `.text`-ben **nulla** előfordulás.
   *(Csak ezt az alakot pásztáztam; 8 vagy 32 bites immediate alakot nem.)*

⇒ **A szerkesztő és a könyvtárnézet EGYAZON kezelőt használja** (a
`0x005e6710` mindkettő állapotát piszkálja: `[edi+0x332f]`, `[edi+0x33a8]`,
`[edi+0x3378]`). A diavetítés és a videólejátszó billentyűi **nem
ugrótáblás kezelőben** vannak — ha vannak, `if`-láncban, más
összehasonlítási alakkal. A 7.3 pont ezzel **szűkül**, de nem zárul le.

### 10.12 ⭐ MELLÉKLELET: a Shift-váltás ÉLŐ, nem a fül felépülésekor (#2141, #2146)

A `0x005e6710` elején egy külön ág fut, **még a VK-vizsgálat előtt**:

```
0x005e6745  cmp dword ptr [ebx+4], 0x102     ; WM_CHAR -> kihagy
0x005e674e  cmp byte ptr [ebx+8], 0x10       ; VK_SHIFT?
0x005e6754  push 0x10 ; call [0xc406f8]      ; GetAsyncKeyState(VK_SHIFT)
0x005e675c  shr eax, 0xf ; and al, 1
0x005e6761  cmp byte ptr [edi+0x33a8], al    ; a panel TÁROLT Shift-jelzője
0x005e6767  je  0x5e6776                     ; ha nem változott -> nincs teendő
0x005e6769  mov eax, dword ptr [edi+0x3378]
0x005e6771  call 0x5d7c20                    ; a CSEMPEÉPÍTŐ újrafuttatása
```

A `0x005d7c20` a csempeépítő, a `[edi+0x33a8]` pedig ugyanaz a Shift-jelző,
amit a `filterdesc-registry.md` „A csempe MÁSODIK szűrője: a SHIFT
kapcsolja be (#2141)" szakasza ír le.

⇒ **HELYESBÍTÉS a #2141 köréhez:** az a kör azt írta, hogy a Shift-állapot
„a fül felépülésekor egyszer" dől el. **Valójában élő:** a
`VK_SHIFT` minden le- és felengedésére (`WM_KEYDOWN`/`WM_KEYUP`, a
`WM_CHAR` kizárva) a program **újraépíti a csempéket**, ha az állapot
megváltozott. A felhasználó tehát **nyomva tartás közben látja átváltani**
a kilenc csempét, és elengedéskor visszaváltani.

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
| `0xd6e318` | Kép ▸ Csoportos szerkesztés | Átnevezés… | `F2` | `0x9d4f` |
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

### 4.1 #4339 — a 44 rekord nézeti határa

A kilenc gyorsbillentyűs építő **a helyi menü birtokosát** azonosítja. A
rekordok kontextusát tehát utasításszinten meg lehet nevezni:

| építő | helyi menü / nézeti kontextus | rekordok billentyűi |
|---|---|---|
| `0x00730790` | mappanézet képe | `Enter`, `Ctrl+R`, `Ctrl+Shift+R`, `Ctrl+Shift+O`, `Ctrl+S`, `Ctrl+Enter`, `Ctrl+Delete`, `Alt+Enter` |
| `0x00731050` | album-nézet képe | ugyanaz a nyolc; a `Ctrl+Delete` felirata azonos `cmd 0x9c9a`-hoz itt „Eltávolítás az albumból” |
| `0x007319f0` | mappa helyi menüje | `Ctrl+A`, `Ctrl+D`, `Ctrl+I`, `Ctrl+Enter` |
| `0x00732160` | album helyi menüje | `Ctrl+A`, `Ctrl+D`, `Ctrl+I` |
| `0x007327a0` | OneUp-néző helyi menüje | `Esc`, `Ctrl+R`, `Ctrl+Shift+R`, `Ctrl+Shift+O`, `Ctrl+S`, `Ctrl+Enter`, `Ctrl+Delete`, `Alt+Enter` |
| `0x00732ee0` | képtálca helyi menüje | `Ctrl+H`, `Ctrl+R`, `Ctrl+Shift+R`, `Ctrl+Enter`, `Alt+Enter` |
| `0x00733a40` | gyűjtemény-/mappalista helyi menüje | `Ctrl+Enter` |
| `0x007355c0` | Emberek-album képe | `Enter`, `Ctrl+Enter`, `Ctrl+Delete`, `Alt+Enter` |
| `0x007359e0` | Emberek-album helyi menüje | `Ctrl+A`, `Ctrl+D`, `Ctrl+I` |

**2026-10-06 — a helyi menümező felirat, a tényleges fogadás nézethez kötött:**
a kilenc építő és 44 rekord táblája továbbra is a menübirtokost adja meg.
A `0x00a6aee0` 20 bájtos rekordjának `+0x04` mezőjét szövegként fűzi
a menütételhez a `0x00a6b250` útján. A `0x00a6ade0` a feliratban
kiírandó billentyűkódot keresi ki és visszaadja a felirat-összeállítónak;
egyetlen közvetlen hívója a `0x00a6b250`. Ebben a helyi
menüépítő/feliratláncban gyorsító-regisztráció nincs. Ez a megállapítás
erre a láncra korlátozott: az importlista `CreateAcceleratorTableA` és
`TranslateAcceleratorA` API-kat is tartalmaz, de a 44 rekorddal való
kapcsolatuk **NINCS MEG**.

A tényleges könyvtárnézeti fogadó a `CThumbUI` vtable billentyűslotjának
`0x005e6710` kezelője. A bizonyított feltételek:

- Ha a `+0x332f` bájt nem nulla, az út a `0x00760970`-re delegál;
  ez csak keydown eseményen kezeli az Escet, a nyilakat és a szóközt,
  valamint a `+0x3330` feltételéhez kötött `0`–`9` ágakat.
- A szerkesztő `+`/`-`/`=`/`_` csúszkaléptetése és a Shift miatti
  csempefrissítés a 3–5. szerkesztőfül látható paneljéhez kötött:
  `0x005f95d0`/`0x005f9690` a `0x009e39b0` láthatósági láncvizsgálatot
  használja. Ez a fókuszobjektum és szülői között megköveteli, hogy a
  `+0x20c` bájt sehol se legyen beállítva.
- A közös `0x00a53b00` továbbító a fókuszolt gyereknek adja az eseményt;
  a CThumbUI saját F- és Enter-ágai csak a továbbítás után futnak a
  dokumentált mód-/állapotkapukkal (`0x005e6710`).
- A `ytPopupListNode` `0x00a64050` kezelője a billentyűeseményt előbb az
  ősnek/gyereknek továbbítja; saját fallback ága csak Esc/Enter/Space.
  A 44 rekord táblázatát nem keresi, ezért nem bizonyítja azok egyedi
  Ctrl/Alt parancs-hozzárendelését.

**Következtetés és fejlesztői irány:** a helyi menüben látható billentyű
feliratát ne tekintsük a billentyű regisztrációjának. A QML oldalon minden
kötéshez rögzítsük a gazdanézetet, a fókuszkaput és az eseményfogadót;
a `CThumbUI` feltételeit ne terjesszük ki a másik nyolc menüépítőre. A
44 menürekord és az egyedi billentyű/parancs-kapcsolat teljesen megfeleltetett
listája továbbra sincs bizonyítva; a globális gyorsító-API importok miatt a
program egészére sem állítható, hogy sehol sem regisztrál gyorsítót.
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
| `F2` | Átnevezés… | kijelölt fájlok tömeges átnevezése (`rename.fen`) | **NINCS MEG: a tiltási feltétel** | fájlok (`rename.fen`: „file(s) selected for rename”) | Fájl ▸ · Kép ▸ Csoportos szerkesztés ▸ | fájlátnevező párbeszéd (`0x005e6710` → `0x00532ec0`) |
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

## 6. Összevetés a PicasaPy-jal

Forrás: `src/picasapy/app/qml/Main.qml`,
`src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml`,
`…/DocumentTabStrip.qml`, `…/PhotoViewer.qml`,
`…/SlideshowView.qml`, `…/LightboxFeed.qml`, `…/CollageCanvas.qml`.

**A #4339-es leltár pillanatfelvétele (2026-10-06, a #4398 előtti forrásállapot):** a `src/picasapy/app/qml` 187 QML-fájljában 53 `Shortcut` deklarációt számoltunk nyolc fájlban; 52 sor adott szó szerinti `sequence`-et, 47 eltérő literális billentyűsorozattal. A 2026-08-25-i 34 kombinációs táblázat és a §6.1 alatti QML-megfigyelések történeti állapotot rögzítenek. A #4398 szerinti aktuális, 54 kötéses leltárt és a fókuszkapukat a §6.2 tartalmazza.

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

**Történeti számok — 2026-08-25-i állapotfelvétel, nem a mai QML-leltár.** A menüsáv 32 rekordja **28 egyedi** kombinációt takar (az `F2`, a `Ctrl+3`, a `Ctrl+4` és a `Ctrl+Enter` két-két menüben is szerepel); ehhez jön a négy csak helyi menüben élő (`Enter`, `Esc`, `Ctrl+H`, `Ctrl+Delete`) és a rács `Home` / `End` billentyűje — **összesen 34**.
A 2026-08-25-i snapshot szerint nálunk: **20 megvan**, **2 eltér** (`Delete`, `Esc`), **12 hiányzik**.


### 6.1 #4339 — helyi menüfelirat, billentyűfogadó és QML-állapot a #4398 előtt (2026-10-06)

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A 44 helyi rekord a kilenc menübirtokos helyi menüben jelenik meg (§4.1). A `+0x04` mező feliratot épít (`0x00a6aee0` → `0x00a6b250`); a `0x00a6ade0` csak a felirathoz oldja fel a billentyűt. A könyvtárnézeti tényleges fogadó a `CThumbUI` `0x005e6710` kezelője, saját fókusz-/nézetfeltételekkel. | A #4398 előtti pillanatfelvétel 53 `Shortcut` deklarációt talált nyolc QML-fájlban. Akkor a főablak `Ctrl+A/D/I/S` kötésein nem volt külön `enabled`/szövegmező-kapu; a `Ctrl+C/X/V` kötéseken volt ilyen. | A helyi menü szövegét ne kezeljük gyorsítóregisztrációnak. Minden billentyűműveletnél dokumentáljuk és érvényesítsük a gazdanézetet, a fókuszt és az eseményfogadót; a szövegmezők vágólapművelete maradjon a mezőé. A #4398 utáni állapotot és a 54 kötés tábláját lásd a §6.2-ben. |
| A könyvtári `CThumbUI` `+0x332f != 0` ág keydownon `Esc`, nyilak, Space és feltételes számjegyek; a szerkesztő `+`/`-`/`=`/`_` és Shift-útja látható 3–5. fülhöz kötött (`0x00760970`, `0x005f95d0`, `0x005f9690`, `0x009e39b0`). | A `Ctrl+Delete` két `Main.qml` kötésre válik szét: rácsban `!viewerOpen && selectedRows().length>0`, nézőben `viewerOpen && currentIndex>=0` (`1441–1463`). A `Ctrl+H` a `TrayBar`-ban csak létező ablak, nézőn kívüli állapot és nem üres kijelölés mellett aktív (`128–134`). A `Ctrl+Return` a menüsávban `photoActionsEnabled` feltételű (`PicasaMenuBar.qml:403–407`). | A QML-kötések hatókörét nézetenként rögzítsük; a billentyű ne fusson le másik nézet vagy üres kijelölés esetén. Az eredeti `+0x332f` bájt szemantikáját (`NINCS MEG`) ne találgassuk. |
| A `ytPopupListNode` `0x00a64050` billentyűfallbackja csak Esc/Enter/Space; a `CThumbUI` saját fogadója a fókuszált gyerek továbbítása után saját kapukkal folytatja. | Az `Enter` nem `Shortcut`: a `LightboxFeed.qml:368–377` csak `selectedIndex >= 0` esetén nyit, a `DocumentTabStrip` Esc-kötése csak aktív projektlap mellett él (`DocumentTabStrip.qml:140–145`), a `PhotoViewer` külön `Keys.onEscapePressed` ágat használ. A QML-literalok között `Ctrl+Shift+O`-hoz nincs `sequence` kötés. | Tartsuk meg a nézeti `Keys`-fogadókat ott, ahol az eredeti is a fókuszált nézetnek továbbít; ne adjunk ezek helyett ablak-szintű kötést. A nyitott `Ctrl+Shift+O` csak külön funkciódöntéssel vehető fel. |

A `Ctrl+Shift+O`-ról ez a mérés csak azt állítja, hogy a mai QML-ben nincs hozzá literális `Shortcut.sequence`; a menükben maradt „Open File” felirat önmagában nem bizonyít aktív funkciót. A 53/8/52/47 leltárforrás egy célzott, teljes `src/picasapy/app/qml/**/*.qml` fájlbejárás; nem futtatási mérés.

### 6.2 #4398 — az aktuális 54 QML-kötés gazdanézete és fókuszkapuja (2026-10-06)

A #4398 elején megadott 53-as szám a #4339 korábbi pillanatfelvétele volt; a jelenlegi forrásban **54 `Shortcut` deklaráció** található ugyanabban a nyolc QML-fájlban. A táblázat minden deklarációt külön sorban rögzít, így az ismétlődő billentyűk sem olvadnak össze. A „gazda” a QML-fogadó; ez nem állítja, hogy a 44 helyi menürekord egyenként össze van kötve ezekkel a fogadókkal.

| # | QML-gazda / kötés | Billentyű | Nézet- és fókuszkapu |
|---:|---|---|---|
| 1 | `Main.qml` — `toggleRightDrawerShortcut` | `Ctrl+0` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 2 | `Main.qml` — `searchShortcut` | `Ctrl+F` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 3 | `Main.qml` — `tagsPanelAltShortcut` | `Ctrl+K` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 4 | `Main.qml` — `editViewShortcut` | `Ctrl+3` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 5 | `Main.qml` — `dupeSearchShortcut` | `Ctrl+F6` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 6 | `Main.qml` — `findSimilarShortcut` | `Ctrl+F7` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 7 | `Main.qml` — `clearSimilarShortcut` | `Ctrl+F8` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 8 | `Main.qml` — `batchBwShortcut` | `Ctrl+Shift+B` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 9 | `Main.qml` — `batchEnhanceShortcut` | `Ctrl+Shift+E` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 10 | `Main.qml` — `helpShortcut` | `F1` | Főablak; nincs fókuszban szövegmező és nincs külön ablakos párbeszéd. |
| 11 | `Main.qml` — `helpContextShortcut` | `Shift+F1` | Főablak; nincs fókuszban szövegmező és nincs külön ablakos párbeszéd. |
| 12 | `Main.qml` — `selectAll` | `Ctrl+A` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 13 | `Main.qml` — `clearSelection` | `Ctrl+D` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 14 | `Main.qml` — `invertSelection` | `Ctrl+I` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 15 | `Main.qml` — Mentés | `Ctrl+S` | Főablak; nincs fókuszban szövegmező. A `Shortcut` deklaráció nem állít be külön nézetkaput. |
| 16 | `Main.qml` — fájlok másolása | `Ctrl+C` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 17 | `Main.qml` — fájlok kivágása | `Ctrl+X` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 18 | `Main.qml` — vágólapról beillesztés | `Ctrl+V` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 19 | `Main.qml` — forgatás jobbra | `Ctrl+R` | Főablak; nincs fókuszban szövegmező. A `Shortcut` deklaráció nem állít be külön nézetkaput. |
| 20 | `Main.qml` — forgatás balra | `Ctrl+Shift+R` | Főablak; nincs fókuszban szövegmező. A `Shortcut` deklaráció nem állít be külön nézetkaput. |
| 21 | `Main.qml` — `flipHorizontalShortcut` | `Ctrl+Shift+H` | Főablak; nincs fókuszban szövegmező. A `Shortcut` deklaráció nem állít be külön nézetkaput. |
| 22 | `Main.qml` — `flipVerticalShortcut` | `Ctrl+Shift+V` | Főablak; nincs fókuszban szövegmező. A `Shortcut` deklaráció nem állít be külön nézetkaput. |
| 23 | `Main.qml` — diavetítés | `Ctrl+4` | Főablak; nincs fókuszban szövegmező. A `Shortcut` deklaráció nem állít be külön nézetkaput. |
| 24 | `Main.qml` — címkékpanel | `Ctrl+T` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 25 | `Main.qml` — tulajdonságpanel | `Alt+Return` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 26 | `Main.qml` — időrend | `Ctrl+5` | Állandóan tiltott (`enabled: false`). |
| 27 | `Main.qml` — átnevezés | `F2` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. A kijelölés kezelőfeltétel, nem külön `Shortcut`-kapu. |
| 28 | `Main.qml` — exportálás mappába | `Ctrl+Shift+S` | Könyvtárnézet; `viewerOpen == false`, nincs fókuszban szövegmező. |
| 29 | `Main.qml` — `shortcutDeleteFromDiskGrid` | `Ctrl+Delete` | Könyvtárnézet; `viewerOpen == false`, nincs szövegfókusz és van kijelölt sor. |
| 30 | `Main.qml` — `shortcutDeleteFromDiskViewer` | `Ctrl+Delete` | Néző; `viewerOpen == true`, nincs szövegfókusz és van aktuális kép. |
| 31 | `Main.qml` — `openInEditorShortcut` | `Ctrl+Shift+O` | Főablakban engedélyezett fotóművelet és nincs szövegfókusz; külön nézetkaput nem deklarál. |
| 32 | `Main.qml` — `emailShortcut` | `Ctrl+E` | Főablakban engedélyezett fotóművelet és nincs szövegfókusz; külön nézetkaput nem deklarál. |
| 33 | `Main.qml` — import párbeszéd súgója | `Shift+F1` | Import párbeszéd nyitva és nincs szövegfókusz. |
| 34 | `DocumentTabStrip.qml` — projektlap visszalépés | `Esc` | Projektlapok vannak, nem könyvtári nézet, nincs szövegfókusz. |
| 35 | `DocumentTabStrip.qml` — projektlap bezárás | `Ctrl+W` | Projektlapok vannak, nem könyvtári nézet, nincs szövegfókusz. |
| 36 | `DocumentTabStrip.qml` — következő projektlap | `Ctrl+Tab` | Projektlapok vannak, nincs folyamatban bezárás-megerősítés és nincs szövegfókusz. |
| 37 | `DocumentTabStrip.qml` — előző projektlap | `Ctrl+Shift+Tab` | Projektlapok vannak, nincs folyamatban bezárás-megerősítés és nincs szövegfókusz. |
| 38 | `DocumentTabStrip.qml` — következő lap | `Ctrl+Right` | Projektlapok vannak, nincs folyamatban bezárás-megerősítés és nincs szövegfókusz. |
| 39 | `DocumentTabStrip.qml` — előző lap | `Ctrl+Left` | Projektlapok vannak, nincs folyamatban bezárás-megerősítés és nincs szövegfókusz. |
| 40 | `EditorToolBar.qml` — kiegyenesítés visszavonása | `Escape` | A szerkesztő eszközsávja látható és nincs szövegfókusz. |
| 41 | `ExportDialogs.qml` — párbeszéd súgója | `Shift+F1` | Export párbeszéd nyitva és nincs szövegfókusz. |
| 42 | `FolderManagerDialog.qml` — `StandardKey.Cancel` | `Escape` | A mappakezelő ablak látható és nincs a saját ablakában szövegfókusz. |
| 43 | `PicasaMenuBar.qml` — `shortcutSmallThumbnails` | `Ctrl+1` | Könyvtárnézet; nincs szerkesztő és nincs szövegfókusz. |
| 44 | `PicasaMenuBar.qml` — `shortcutNormalThumbnails` | `Ctrl+2` | Könyvtárnézet; nincs szerkesztő és nincs szövegfókusz. |
| 45 | `PicasaMenuBar.qml` — `shortcutLocateOnDisk` | `Ctrl+Return` | Engedélyezett fotóművelet és nincs szövegfókusz. |
| 46 | `PicasaMenuBar.qml` — `shortcutDeleteFromDisk` | `Delete` | Engedélyezett fotóművelet és nincs szövegfókusz. |
| 47 | `PicasaMenuBar.qml` — `shortcutPrint` | `Ctrl+P` | Engedélyezett fotóművelet és nincs szövegfókusz. |
| 48 | `PicasaMenuBar.qml` — `shortcutPrintContactSheet` | `Ctrl+Shift+P` | A Mappa-menütétellel azonosan mindig engedélyezett; nincs kijelölési vagy szövegfókusz-kapu. |
| 49 | `PicasaMenuBar.qml` — `shortcutImportFrom` | `Ctrl+M` | Könyvtárnézet; nincs szerkesztő és nincs szövegfókusz. |
| 50 | `PicasaMenuBar.qml` — `shortcutAddFile` | `Ctrl+O` | Könyvtárnézet; nincs szerkesztő és nincs szövegfókusz. |
| 51 | `PicasaMenuBar.qml` — `shortcutNewAlbum` | `Ctrl+N` | Engedélyezett fotóművelet és nincs szövegfókusz. |
| 52 | `TrayBar.qml` — `trayKeepSelectionShortcut` | `Ctrl+H` | Létezik főablak, nem néző, van tálca-kijelölés és nincs szövegfókusz. |
| 53 | `WindowHelp.qml` — általános súgó | `F1` | A súgóablak aktív és nincs benne szövegfókusz. |
| 54 | `WindowHelp.qml` — témasúgó | `Shift+F1` | A súgóablak aktív és nincs benne szövegfókusz. |

A főablak kötéseinél a táblázat a forrásban kifejezett `enabled`-kaput írja le; ahol nincs nézetkapu, ott nem következtetünk a 44 eredeti helyi rekord parancs-hozzárendelésére. Az eredetihez nem igazolt `+0x332f` módjelző szemantikája továbbra is nyitott. `PhotoViewer.qml` nézeti `Keys`-fogadói (`Esc`, nyilak, `Return`, szóköz, `F`, `Shift+F`, `Ctrl+Delete`) szövegfókuszban visszatérnek a mezőnek, `PicasaSlider.qml` pedig csak a `EditorParamPanel.qml` 3–5. látható füléhez kapja meg a `+`, `=`, `-`, `_` léptetés engedélyét.

Az ellenőrző teszt valódi billentyűleütéssel próbálja mind az 54 deklaráció szekvenciáját keresőmező-fókuszban; külön valódi eseményekkel vizsgálja a könyvtári `Ctrl+1` editorbeli tiltását, az editor 2. fülén a négy sliderbillentyű tiltását és a 3. fülön működését, továbbá a kereső-, felirat- és címkemező saját szerkesztőbillentyűit. Ez nem bizonyítja a 44 rekord egyedi parancs-megfeleltetését.
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

Az alábbi lista a 2026-08-25-i állapotfelvétel történeti javaslatait őrzi;
a #4339 szerinti aktuális QML-állapotot a 6.1. szakasz rögzíti. A Ctrl+H
javaslat azóta megvalósult (#4329).

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
8. ✅ **MEGVAN (#4329).** ~~A Ctrl+H megtartja a kijelölést a képtálcán~~ —
   a `TrayBar` kötése létező ablakot, nézőn kívüli állapotot és nem üres
   kijelölést követel meg (aktuális állapot: 6.1. szakasz).
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
| `Ctrl+G` (+Alt/+Shift) | `0x005e6518` | módosító nélkül vagy Alt-tal: nincs művelet; Shift: `0x00600580`; Alt+Shift: `0x0057b050` (10.22) |
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
**`Ctrl+7`, `Ctrl+J`, `Ctrl+Q`, ~~`Ctrl+W`~~, `Ctrl+Z`, `Ctrl+F1`…`Ctrl+F5`**,
*(a `Ctrl+W`-t a lánc egy KORÁBBI szeme fogja el — ld. **10.15**)*,
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

⚙️ **FRISSÍTVE (2026-09-10, #2163): a húszból tíz bekötve, tíz indokkal
kimaradt.** Bekötve: `Ctrl+0` (jobb fiók), `Ctrl+F` (keresés), `Ctrl+K`
(Címkék), `Ctrl+C` (másolás), `Ctrl+3` (Megjelenítés és szerkesztés),
`Ctrl+F6` (másodpéldány-mód, #1398), `Ctrl+F7` / `Ctrl+F8` (hasonlóság-minta
és törlése, #1833), `Ctrl+Shift+B` / `Ctrl+Shift+E` (a `bw` és az `enhance`
szűrő a kijelölésre, a köteg-szerkesztés útján).

Kimaradt a PicasaPyból: `Ctrl+6`, `Ctrl+8`, `Ctrl+9`, `Ctrl+G`,
`Ctrl+Shift+L`, `Ctrl+Shift+U`, `Ctrl+Shift+Y`, `Ctrl+F9`. Az eredeti ágak
hatása a #4643 mérésével részben feltárt; a mai bekötési irányt és a nyitott
részeket a **10.22** rögzíti. **Helyesbítés:** a bal szerkesztőfiók nálunk
létezik (`PhotoViewer.qml`: `editorControlsVisible`, `toggle_left_drawer`;
`PicasaMenuBar.qml`: „Show Edit Controls”), csak a Ctrl+9 kötés hiányzik.
`Ctrl+Shift+H` / `Ctrl+Shift+V` (tükrözés — a művelet a kódbázisban NINCS
meg; külön jegy). A soronkénti elszámolás a #2163 kommentjében áll, a gépi őr a
`tests/app/test_gyorsbillentyu_agak_2163.py`: az bukik, ha olyan billentyűt
kötünk be, amire az eredetiben nincs ág (10.5), és a kivételeket
indoklással kényszeríti ki.

### 10.8 Bizonyítottsági fok

**Megerősített:** a dispatch szerkezete, a két tábla címe és tartalma, a
34 ág célcíme, a nyolc elemnév, a `0x009cd8a0` kattintás-szemantika és a
mi oldalunk (mind közvetlen kiolvasás, illetve grep).
**Erős:** a `Ctrl`/`Shift`/`Alt` bit-azonosítás (két független egyezés a
lap 3.3 táblájával).
**A #4643 előtt nem volt mérve:** a nem-kattintó ágak célfüggvényeinek
jelentése. A 10.22 most rögzíti a kiolvasható hatásokat; a Ctrl+F9 jelző
teljes felhasználói szemantikája, a Ctrl+Alt ágon frissített gyerekobjektum
pontos kirajzolt tartalma és az F12-jelző felhasználási helye továbbra is nyitott.

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
| **F5** | `0x005e6869` | időbélyeg- és állapotfrissítés, `[adatobjektum+0x166] = 1` frissítési kérés, majd kereső-/nézeti frissítés (`0x0065b840`; 10.22) |
| **F11** | `0x005e68a0` | vtable `+0x24` kétszer, `[eax+0x3e]` billentése, majd `0x00983fc0` |
| **F12** | `0x005e69c2` | `call 0x005e60d0` — de az F12 a Ctrl-tábla tartományán **kívül** esik (10.6), tehát ott nem történik semmi |

**Bizalmi fok: megerősített** (közvetlen kiolvasás). A részletes F5
frissítési út a 10.22-ben szerepel; a többi hívott függvény felhasználói
jelentése nincs mérve — csak a címük, az őreik és az elemnevek.

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

### 10.13 A billentyűkezelés LÁNC, nem nézetenkénti kezelő (#2164, 2026-09-03)

A #2164 azt kereste, hol van a **szerkesztő**, a **diavetítés** és a
**videólejátszó** külön billentyűkezelője. **Nincs külön kezelő** — a
`0x005e6710` egy **felelősség-láncot** hív végig, és minden láncszem a
saját billentyűit fogja el. A lánc sorrendben:

| # | cím | mikor hívja | mit fog el |
|---|---|---|---|
| 1 | `0x00760970` | `[panel+0x332f]` igaz | (nem mérve) |
| 2 | — (helyben) | `VK_SHIFT` le/fel | a Shift-csempeváltás (10.12) |
| 3 | **`0x005d2290`** | `0x005f95d0` őr után, `0x005e6784` | a **csúszka-léptetés** (lásd 10.14) |
| 4 | **`0x005b2390`** | `[panel+0xccc]` nem nulla, `0x005e67e5` | a **projektlap-sáv** billentyűi (10.15) |
| 5 | **`0x00a53b00`** | mindig, `0x005e67f4` | általános vezérlő-/szövegbeviteli billentyűk |
| 6 | — (helyben) | `Ctrl` nélkül | F1–F5, F11, F12 (10.10) |
| 7 | `0x005e60d0` | `Ctrl` esetén | a 34 elemes Ctrl-tábla (10.3) |

Minden láncszem `0xf4240`-t (kezelve) vagy `0xf4241`-et (nem kezelve) ad
vissza; a `0x005e6710` az elsőre azonnal kilép.

### 10.14 A CSÚSZKA-LÉPTETÉS — `+` / `=` / `−` / `_`

`0x005d2290`, **`WM_CHAR`** (`0x102`) üzenetre, tehát karakterre, nem
VK-ra:

```
0x005d22ac  cmp eax, 0x2b   ; '+'
0x005d22b1  cmp eax, 0x3d   ; '='
0x005d22b6  cmp eax, 0x2d   ; '-'
0x005d22bb  cmp eax, 0x5f   ; '_'
0x005d22c7  fld dword ptr [0xcf50d8]   ; +0,02
0x005d22d8  fld dword ptr [0xcf50d4]   ; -0,02
0x005d22e2  mov eax, dword ptr [ebp+0x337c]  ; a FÓKUSZBAN LÉVŐ csúszka indexe
0x005d22e8  add eax, 1
0x005d22ee  push 0xc87160              ; "editslider%d/editslider"
```

⇒ **`+` és `=` növeli, `−` és `_` csökkenti a fókuszban lévő csúszkát,
lépésenként ±0,02** (a tartomány 2%-a). A cél az `editslider<N>/editslider`
elem, ahol `N = [panel+0x337c] + 1`.

**Bizalmi fok: megerősített** (a két konstans és a formátumsztring
kiolvasva).

### 10.15 A PROJEKTLAP-SÁV billentyűi — és a `Ctrl+W` MÉGIS létezik

`0x005b2390`, `WM_KEYDOWN`-ra, **`Ctrl` kötelező** (`test cl, 4` / `jle`,
`0x005b239d` — ugyanaz a bit, mint a 10.9-ben):

| billentyű | cím | mit csinál |
|---|---|---|
| **`Ctrl+Left`** | `0x005b23a6` | `0x005b22b0(panel, −1)` — előző lap |
| **`Ctrl+Right`** | `0x005b23b6` | `0x005b22b0(panel, +1)` — következő lap |
| **`Ctrl+Tab`** | `0x005b23c8` | `0x005b22b0(panel, +1)`; **`Shift`-tel** (`test cl, 2`) `−1` |
| **`Ctrl+W`** | `0x005b23dd` | `0x005b31a0(panel, …)` — a `[panel+0x26c]` szerint |

⇒ ⛔ **HELYESBÍTÉS a 10.5-höz.** A 10.5 negatív eredménye azt mondta:
*„`Ctrl+W` … NINCS ág"*. Ez **a Ctrl-táblára igaz**, de a `Ctrl+W`-t a
lánc **korábbi** szeme fogja el (`0x005b2390`), tehát **a billentyű
létezik**. A 10.5 listájából a `Ctrl+W` **törlendő**; a többi (`Ctrl+7`,
`Ctrl+J`, `Ctrl+Q`, `Ctrl+Z`, `Ctrl+F1`…`F5`) továbbra is áll, mert azokat
egyik láncszem sem vizsgálja.

*(Ez egyben megmagyarázza a 7.2 pont `Ctrl+W` rekeszét is: a keymapben ott
van, csak nem menüben és nem a Ctrl-táblában.)*

### 10.16 A VK-láncok TELJES leltára — 20 db a `.text`-ben

A `movsx`/`movzx …, word ptr [reg+8]` (a VK kiolvasása) minden előfordulását
végigpásztáztam, és megtartottam azokat, amelyeket **legalább két**
`cmp reg, imm` követ 0xA0 bájton belül. **Húsz ilyen lánc van**, ezek:

| lánc | gazdafüggvény | a vizsgált billentyűk | mi ez |
|---|---|---|---|
| `0x0052ecfc` | `0x0052ece0` | `D`,`C`,`P`,`S`,`0xbb`,`0x6b` | nem mérve |
| `0x005b23a2` | `0x005b2390` | `←`,`→`,`W` | **projektlap-sáv** (10.15) |
| `0x005d22a8` | `0x005d2290` | `+`,`=`,`−`,`_` | **csúszka-léptetés** (10.14) |
| `0x005e6836` | `0x005e6710` | `F1`,`F5`,`F11` | **a fő kezelő** (10.10) |
| `0x005e68f9` | `0x005e6710` | `F2`,`F4` | ugyanaz |
| `0x006398da` | `0x006398c0` | `Esc`,`Enter` | szövegbeviteli mező (`editcancel`, `editselected`) |
| `0x007366ae` | `0x00736690` | nyilak | szövegbeviteli mező (`edittab`, `editarrow`) |
| `0x0077d3a1` | `0x0077d380` | nyilak, `PageUp/Down`, `Enter` | nem mérve |
| `0x007e13f9` | `0x007e13b0` | nyilak, `Esc` | `buttonmgr/cancel` |
| `0x00808ade`, `0x00808b7c` | `0x00808ac0` | `↑`,`↓`,`Enter`,`Esc` | nem mérve |
| `0x0080906c` | `0x00809050` | `↑`,`↓`,`Enter` | nem mérve |
| `0x00920adf`, `0x00921fe7` | `0x00920a30`, `0x00921de0` | `M`,`m`,`L`,`l` | nem mérve |
| `0x00a53b63` | `0x00a53b00` | saját index+ugrótábla (`0x00a53bb4`/`0x00a53ba8`), VK `0x08`–`0x70`, plusz `Tab` és `Ctrl+A…Z` | **általános vezérlő** (lánc 5.) |
| `0x00aa4e18` | `0x00aa4dd0` | `Home`,`End`,`Delete`,`→` | listavezérlő (`listboxup`, `listboxdown`, …) |
| `0x00ae137c`, `0x00b41267`, `0x00c1609c`, `0x00c160d1` | — | nem billentyű-jellegű | kizárva |

⇒ **A diavetítésnek és a videólejátszónak NINCS saját VK-lánca.** Ez a
negyedik, egymástól független kizárás a 10.11 három mérése után.

### 10.17 Ami a diavetítésről/videóról ekkor még nem volt tudható

> ⛔ **EZ A SZAKASZ MEGDŐLT — a választ a 10.18–10.20 adja meg.**
> A `Space`-nyom **hamis volt**: mind a nyolc `cmp ax, 0x20` hely
> **bitmélység-vizsgálat** (`biBitCount`), nem billentyű (10.20).

- ~~A `Space` billentyű a `.text`-ben **nyolc** helyen szerepel
  `cmp ax, 0x20` alakban (`0x006d6042`, `0x006d605f`, `0x006d7498`,
  `0x006d74e2`, `0x006d7ead`, `0x006d8f9b`, `0x009d713d`, `0x009d732e`),
  de egyik gazdafüggvénynek sincs sztring-hivatkozása.~~
- A keymap `/`, `,`, `.` rekeszeihez (VK `0xBF`, `0xBC`, `0xBE`) **egyetlen
  összehasonlítást sem** találtam: sem `cmp ax, imm16` (10.11), sem a
  húsz lánc egyikében. **Ez az állítás áll.**
- ~~A következő lépés a `0x006d5e90`, `0x006d7410`, `0x006d7e30`,
  `0x006d8eb0` azonosítása.~~ — **tárgytalan** (10.20).

### 10.18 A LÁNC ÖTÖDIK SZEME: minden navigációs billentyű EGY továbbítóba megy (#2164, 2026-09-03)

A 10.13 láncának 5. szeme, a **`0x00a53b00`**, saját index- és ugrótáblát
használ (`0x00a53bb4` / `0x00a53ba8`, VK `0x08`…`0x70`, `edx = vk − 8`,
`cmp edx, 0x68`). A tábla **három** ágra oszt, és ez a teljes tartalma:

| ág | mely billentyűk | mit tesz |
|---|---|---|
| `0x00a53b7d` | **Backspace `0x08`, VK `0x0C`, Enter `0x0D`, Esc `0x1B`, Space `0x20`, PageUp `0x21`, PageDown `0x22`, End `0x23`, Home `0x24`, ←`0x25`, ↑`0x26`, →`0x27`, ↓`0x28`, Insert `0x2D`, Delete `0x2E`, VK `0x2F`, F1 `0x70`** | `push eax; push ecx; call 0x00a582f0` — **továbbítás** |
| `0x00a53b9d` | **Shift `0x10`, Ctrl `0x11`, Alt `0x12`** | **eldobás** (visszatérés) |
| `0x00a53b8a` | minden más | ha `Ctrl` és a billentyű `A`…`Z`, akkor szintén `0x00a582f0`; egyébként tovább a láncon |

Ezen felül `WM_CHAR`-ra a **Tab** (`0x00a53b44`) külön ágon megy
(`0x00a58170`), `Shift`-fel megfordított iránnyal (`test dl, 2`).

**A továbbító (`0x00a582f0`)** nem billentyűt kezel: **eseményobjektumot
épít** (`0x005c5da0`, `0x009dd770`, `0x005de720`), megkülönbözteti a
`WM_KEYUP`-ot (`cmp eax, 0x101`, `0x00a58322`), és a **fókuszban lévő
elemnek** küldi el.

### 10.19 ⛔ EZ A VÁLASZ a #2164-re: a diavetítésnek/videónak NINCS saját kezelője

A navigációs billentyűk **nem nézetenként** vannak lekezelve, hanem
**eseményként a fókuszált elemnek** továbbítva. Ezért nem találtunk
diavetítés- vagy videó-specifikus billentyűkezelőt: **nincs is.**

**Öt egymástól független mérés vezetett ide:**

1. az átképezhető kötés gépezete (`0x005c5f90`, `0x005c5fc0`) **1–1
   hívóval** csak a Ctrl-táblában fut;
2. a teljes `.text` **174** ugrótáblás `switch`-éből **egyetlen** indexel a
   VK-ból (`0x005e61f1`);
3. `cmp ax, 0xBC` / `0xBE` / `0xBF` (`,` `.` `/`): **nulla** előfordulás;
4. a **húsz** VK-összehasonlító lánc (10.16) egyike sem a diavetítésé;
5. **⛔ a `Space`-nyom HAMIS volt** — ld. lent.

### 10.20 ⛔ HELYESBÍTÉS: a nyolc `cmp ax, 0x20` NEM a Space billentyű

A 10.17 azt írta, hogy a `Space` a `.text`-ben nyolc helyen szerepel
`cmp ax, 0x20` alakban, és a következő lépésként a `0x006d5e90`,
`0x006d7410`, `0x006d7e30`, `0x006d8eb0` azonosítását nevezte meg.
**Mind a nyolc hely BITMÉLYSÉG-vizsgálat, nem billentyű:**

- a `0x006d6042`/`0x006d605f` melletti ág `cmp eax, 0x32595559`-t végez —
  ez a **`'YUY2'` FourCC** videóformátum-kód —, és hibával tér vissza:
  `mov eax, 0x8004022a` = **`VFW_E_TYPE_NOT_ACCEPTED`** (DirectShow);
- a vizsgált mező mindenütt **`word ptr [reg+0x0e]`**, ami a
  `BITMAPINFOHEADER` **`biBitCount`** mezője (14. bájt);
- az összehasonlított értékek `1`, `8`, `0x18`, `0x20` = **1, 8, 24 és 32
  bit/képpont** (`0x009d7126`–`0x009d7141`, `0x006d7498`, `0x006d7ead`,
  `0x006d8f9b`).

⇒ A `Space` billentyűre **nincs** külön ág; a 10.17 „következő lépése"
**tárgytalan**, és a négy megnevezett függvény a **videó-formátum
egyeztetése**, nem billentyűkezelés.

### 10.21 Ami ezzel HATÓKÖRÖN KÍVÜLRE kerül

„Melyik elem mit csinál a kapott eseménnyel" — ez **nem** a
billentyűkiosztás kérdése, hanem elemenkénti viselkedés, és a
**`ui-lefedettseg.md`** amúgy is elemenként tartja nyilván. Ezen a lapon
ezért nem nyitunk rá kérdést.

**Bizalmi fok: megerősített** (a két tábla teljes kiolvasása, a
továbbító azonosítása, és a `biBitCount`-helyesbítés közvetlen
kiolvasásból).

### 10.22 #4643 — a Ctrl-ágak, az F5 és a nyitott billentyűk hatása (2026-10-08)

**Módszer:** a megadott függvényhatárokat a helyi SQLite-indexből vettem,
majd az `annot_disasm.py` utasításszinten olvasta ki. A teljes `.text`
operandum-keresése a `paszta.py`-n futott, első műveletként
`paszta.memoria_kapu()` hívással. Az eredeti program futtatására ebben a
munkamenetben nem került sor; futás közbeni viselkedést ezért nem állítok.

| billentyű / ág | cél és kiolvasott hatás | független megerősítés | fok |
|---|---|---|---|
| `Ctrl+6` | `0x005e6294` → `0x00530ad0`: az `AdvancedFeatures` beállítást olvassa, majd a `timeslicer` vezérlő/panel útjára lép. | Az `AdvancedFeatures` és `timeslicer` bináris karakterlánc-hivatkozásai ugyanahhoz a célhoz vezetnek; a teljes létrehozási/felületi hatás futtatás nélkül nincs kimérve. | feltételes |
| `Ctrl+8` | `0x005e6584` → `0x005e81e0(panel, 2)`: a kijelölt képek `]star` állapotát váltja; a `stars/yes` és `stars/no` ágak közül választ, majd frissíti a nézeti állapotot. | A célfüggvény további hívói és külön string-xref rekordjai ugyanazt a csillagvezérlőt és a két állapotot azonosítják. | megerősített |
| `Ctrl+9` | `0x005e629f`: a `0x00579330` szerkesztő-előnézeti őr után kattint az `editpanel/toggle_left_drawer` elemre. | A mai `PhotoViewer.qml` ugyanezt az objektumnevet és az `editorControlsVisible` állapotot tartalmazza; a `PicasaMenuBar.qml` „Show Edit Controls” tétele ugyanezt az állapotot olvassa/állítja. | megerősített |
| `Ctrl+G` | Külön módosító nélkül az ág nem indít műveletet. | A kezelő módosító-ágainak közvetlen kiolvasása; külön második út ehhez a no-ophoz nincs. | feltételes |
| `Ctrl+Shift+G` | `0x005e6547` → `0x00600580`: a Geotag With Google Earth út, telepítés-ellenőrzéssel; hiányzó Google Earthnél telepítési párbeszédet ad, megléténél a kijelölést továbbítja. | A menü-diszpécser független `ID_PICTURE_GEOTAG` útja ugyanarra a `0x00600580` kezelőre jut (`picasa-menu-parancsok-viselkedes.md` 33.1, 33.5). | megerősített |
| `Ctrl+Alt+G` | Az ág nem indít műveletet. | A handler Alt-ágának közvetlen kiolvasása: Shift nélkül kihagyó ágra jut; külön második út ehhez a no-ophoz nincs. | feltételes |
| `Ctrl+Alt+Shift+G` | `0x005e652c` → `0x0057b050`: elkészíti a `ginormous.jpg` kontaktképet és megnyitja. | A külön nyomtatási spec rögzíti a `ginormous.jpg`, „Making The Ginormous Contact Sheet!” és `ShellExecute` nyomokat (`picasa-nyomtatas.md`, „A `ginormous.jpg` út”). | megerősített |
| `Ctrl+Shift+L` | `0x005e658e` a szerverobjektumot a `0x004cce10`-nek adja; a LAN-jelszó és a fix `picasaserver` felhasználó mellett a `0x004cd010` `http://localhost:%d/%s/` URL-t épít, amelyet a handler böngészővel nyit meg. | A webserver-spec külön méri a `LANPassword`, a `picasaserver` felhasználónevet és az URL-alakot (`picasa-beepitett-webszerver.md` 1.). | megerősített |
| `Ctrl+Shift+U` | `0x005e6557` → `0x0047ca60` → `0x006b8710`: üríti/újrainicializálja a két átadott bélyegképtár memóriabeli állapotát. | A hívó tageltolásai a `pmp-database.md` szerint `m_bigThumbs` (`bigthumbs.db`) és `m_previewThumbs` (`previews.db`); a cél belső mutatókat szabadít fel és nulláz. A fájlok törlését nem állítjuk. | megerősített |
| `Ctrl+Shift+Y` | `0x005e6572` → `0x005e5ec0`: feloldja az `overlays/egg` elemet, inicializálja a hozzá tartozó objektumot és aktiváló jelzőt állít. | A `overlays/egg` string-xref és a Ctrl-ág egyetlen célfüggvénye egyezik; a pontos látható animáció futtatás nélkül nincs kimérve. | feltételes |
| `Ctrl+F9` | A `0x005e60d0` billentyűkezelő Ctrl+`0x78` (F9) táblabejegyzése a `0x005e6329` ágra jut. A konstruktor `0x00564b2e` alaphelyzetben 0-ra állítja a `[panel+0xdc4]` bájtot; a `0x005e6329`–`0x005e6333` ág ezt 0/1 között billenti. Ha a `0x00571e50` útján létezik az `editpanel/preview`, annak `[+0x20c]` mezője 0, a kapcsoló 1, és a kijelölési út érvényes értéket ad, akkor ezt összeveti a `[this+0xe64]` aktuális képként használt értékével. Eltéréskor a `CThumbUI` `+0x2c` virtuális metódusát 0 argumentummal hívja; ez a `0x005f89a0`-en át az `editpanel/preview`-hoz tartozó aktuális kép felirat-/törlésállapotának és vezérlőállapotának frissítését kéri. A bináris nem bizonyítja, hogy ez a kijelölt képre váltja-e az előnézeti képet, vagy csak a meglévő előnézet UI-állapotát rajzolja újra. A kapcsoló 0 állásában ez az eltérésre induló frissítő ág kimarad. | A teljes `.text` pásztázás pontosan négy `[reg+0xdc4]` találatot adott (két írás, két olvasás). A `CThumbUI` RTTI/vtábla-útján a slot `0x00578dc0`-hoz vezet; ennek 0 argumentumos ága a `0x005f89a0`-et hívja, amely az `[this+0xe64]` mezőt olvassa. A külön `0x0056a260` szerkesztőút is aktuális képként kezeli ezt a mezőt (`ui-audit-editor.md`, 3. pont). | feltételes |
| `F5` | `0x005e6869`: időbélyeg-frissítés (`0x004a46e0`), állapotfrissítő hívás (`0x00579480(0,1)`), `[adatobjektum+0x166]=1`, majd `0x0065b840` keresővezérlő-frissítés. Az idle út `0x004afcb0` ezt a jelzőt a `0x004aae90` lista-/nézeti állapotfrissítéshez viszi, majd törli. Ez nem bizonyít teljes fájlrendszer-rescant. | A külön `+0x166` olvasó/ürítő út és a `picasa-konyvtar-eszkoztar-viselkedes.md` 6.5 leírása is frissítési kérelemként azonosítja a jelzőt. | megerősített |
| `Ctrl+Alt` (VK `0x12`) | `0x005e65dc`: csak `[panel+0xe78]` engedélyező jelző és érvényes `[panel+0xe70]` azonosító mellett hívja a `0x00571a80`-at. A teljes `.text` pásztázás az `+0xe78` egyetlen olvasójaként ezt a kaput találta. A cél létrehozza/újrahasználja a `[panel+0x31a8]` gyerekobjektumot, beállítja a bélyegkép-azonosítót, majd a `0x00774d60` frissíti annak geometriáját; ez a függvény a VK `0x12` állapotát olvassa és ablakfrissítést kér. A megjelenített tartalom pontos hatása nyitott. | A `PreviewHandler` külön eseményútja (`0x005c24c0`) szintén a `0x00571a80`-at hívja; a `0x00774cf0` testvér callback listabeli azonosítóváltás után ugyanazt a `0x00774d60` frissítőt hívja. Ez az objektumfrissítést támasztja alá, de a látható tartalmat nem nevezi meg. | nyitott |
| Videó: `/`, `,`, `.` | A `CThumbUI` közvetlen VK-ágában nincs ilyen összevetés; az általános eseménylánc a fókuszált gyereknek továbbít. A központi kezelőből nem állítható, hogy ezek lejátszanak vagy keresnek. | A 10.19 szerinti teljes `.text` pontos `cmp ax,0xbc/0xbe/0xbf` keresése nulla találatot adott; a lánc/fókusz továbbítását a 10.18–10.19 külön méri. | feltételes — a videóvezérlő saját hatása nyitott |

**A Ctrl+F9 két független útja.** **A — állapotút:** a teljes `.text`
pásztázás a konstruktor alapérték-írását (`0x00564b2e`), a billentyű-ág
olvasását/írását (`0x005e6329`, `0x005e6333`) és a `CThumbUI` frissítési
útjának olvasását (`0x00572078`) találta. A `0x00571e50` közvetlen
utasításszintű olvasata szerint az aktív jelző, érvényes és az előnézettől
eltérő kijelölés esetén a `[this+0x2a4]` vtable `+0x2c` metódusát 0-val hívja.
**B — a flagtől független célút:** a konstruktorban a `[this+0x2a4]`
mezőbe írt `0x00c90754` vtable `+0x2c` bejegyzése `0x00578dc0`; ennek 0
argumentumos ága a `0x005f89a0`-et hívja. Ez az `[this+0xe64]` aktuális
képként használt értékből frissíti az előnézethez tartozó felirat-/törlés-
és vezérlőállapotot. Ettől külön a `0x0056a260` szerkesztőút is aktuális
képként kezeli az `[this+0xe64]` mezőt (`ui-audit-editor.md`, 3. pont). A két
út egyezik abban, hogy eltéréskor előnézet-UI frissítés indul; az nem dőlt el,
hogy a kijelölt képet tölti-e be, vagy csak a meglévő előnézet állapotát
frissíti.

A többi sor független megerősítése: Google Earth menüparancs-út,
`ginormous.jpg` nyomtatási lelet, webserver konfiguráció/URL-spec, PMP
tageltolások, mai QML fiókállapota, valamint a korábban mért fókusz- és
frissítési út. Ezek a Ctrl+8/9, Ctrl+Shift+G/L/U, Alt-ág kapuja, F5 és a
videókezelő hiányára egyeznek; a Ctrl+6 és Ctrl+Shift+Y teljes felületi
hatása, továbbá a Ctrl+F9 és a Ctrl+Alt-hoz tartozó gyerekobjektum pontos
kirajzolt tartalma nyitva marad.

**A #4699 két útja:** **A:** a `0x005e65dc` → `0x00571a80` → `0x00774d60`
utasításszintű lánc megmutatja az `EnableHover`/azonosító kaput, a gyerekobjektum
azonosítójának beállítását, a VK `0x12` lekérdezését és az ablak újrarajzolását.
**B:** a `PreviewHandler` `0x005c24c0` hívója és a `0x00774cf0` listaváltó
callback ugyanazt a gyerekobjektum-frissítő utat használja külön eseményekből.
Ezek egyeznek abban, hogy a hívás a gyerekobjektumot frissíti, de egyik út sem
azonosítja a pontos kirajzolt tartalmat; ezért a látható hatás nem megerősített.

**Cáfoló kísérlet (15.2):** a videóírásjelekre vonatkozó „nincs közvetlen
VK-ág” állítást szándékosan tágabb mintával próbáltam cáfolni. A teljes
szakaszban talált két `0xbf` bájt-összevetés egyike sem a billentyű-VK
regisztert vizsgálja; mindkettő adatmező-összevetés. Ugyanazzal a pontos
`cmp ax, 0xbc/0xbe/0xbf` mércével ellenőrizve továbbra is nulla a találat.
A Ctrl+9 régi „bal fiók nincs” mondatát a mai QML `toggle_left_drawer` és
`editorControlsVisible` előfordulásai cáfolják; ez független a bináris
ágnevektől. A Ctrl+F9-nél azt a cáfoló feltevést ellenőriztem, hogy a
0-val hívott `0x00578dc0` a következő képre léptet: a függvényben a nem nulla
argumentum külön útja hívja a `0x005d1300`-at, míg a 0 argumentum a
`0x005f89a0` aktuális-előnézet UI-frissítőhöz jut. A hívó ténylegesen 0-t ad
(`0x005720be`), ezért a „következő kép” feltevés nem áll meg. Azt is
ellenőriztem, hogy ez a hívási út közvetlenül átírja-e az `[this+0xe64]`
mezőt: nem találtam ilyen írást a célfüggvényekben, a teljes operandus-
pásztázás `0x005704eb`-nél megtalálta a mező címét adó `lea`-t; az utasítás-
követés mutatja az ezen a címen keresztüli írást (`0x005704fe`). A másik
közvetlen mezőírás `0x005e8c2d` (`e64=e68`, feltételes). Így a képváltás
irányát ebből az útból nem állítom.

**Cáfoló kísérlet (#4699):** azt a kézenfekvő értelmezést, hogy a Ctrl+Alt
egyszerűen a rács-bélyegkép látható keretkiemelését kapcsolja, a
`design-guide.md` 187–188. sorának eredeti-Picasa megfigyelésével vetettem
össze: ott a bélyegképek hover-állapotára „nincs látványos effekt” szerepel.
Ez nem zár ki más gyerekobjektumot vagy rövid idejű felületi változást, de a
keretkiemelés elnevezését nem támasztja alá. A `picasa-linux-mod.md`
„egér-alatti kiemelés” sora ezért csak nyom, nem független bizonyíték.

**Nyitott:**

- `Ghidra-kör kell: 0x00571e50 — a [panel+0xdc4] kapcsoló pontos, felhasználó által látható hatása az előnézet kijelölt képpel való szinkronizálására. [blokkoló]`
- `Ghidra-kör kell: 0x00774d60 — a [CThumbUI+0x31a8] gyerekobjektum pontos kirajzolt tartalma és az Alt-állapot [objektum+0xb4] látható következménye. [blokkoló]`
- `Ghidra-kör kell: 0x00571a80 — a Ctrl+Alt/VK 0x12 ágban az EnableHover és az érvényes elemazonosító mellett végrehajtott felhasználói művelet. [blokkoló]`
- `Ghidra-kör kell: 0x005f89a0 — a Ctrl+F9 eltérési ágának 0 argumentumos célja ténylegesen kijelölt képre váltja-e az előnézeti képet, vagy csak a jelenlegi [this+0xe64] kép UI-állapotát frissíti. [blokkoló]`
- A `Ctrl+6` timeslicer felületének futás közbeni állapota és a Ctrl+Shift+Y `overlays/egg` látható animációja: **NINCS MEG**; célzott eredeti-program próba kell.
- A `/`, `,`, `.` esetleges videóvezérlő-hatása: **NINCS MEG**; a fókuszált gyermek eseményfogadójának útját kell követni, a globális kezelőben nincs saját ág.

**Fejlesztési következmény:** a Ctrl+9-hez külön bekötési jegy javasolható:
a meglévő `PhotoViewer.toggleEditorDrawer` kapjon `Ctrl+9` billentyűutat,
kizárólag a szerkesztőnézetben, a `0x00579330` őrnek megfelelő állapotban.
Az F5-höz külön jegy javasolható: a könyvtár aktuális nézeti/lista-frissítési
útját és keresővezérlőit indítsa, a bizonyított `+0x166` frissítési
kérelemhez igazítva; teljes könyvtári rescan nem következik a binárisból.
A Ctrl+F9-höz a kódban nincs billentyűkötés (`Ctrl+F9`-keresés a
`src/picasapy/app/` QML/Python fájljaiban); a `PhotoViewer.qml` a
`currentIndex` alapján indít szerkesztést (`beginEditCurrent`). A binárisból
igazolt preview-UI frissítőág és a lehetséges képváltás iránya között nincs
elég bizonyíték a hű megvalósítási jegyhez; a Ghidra-kör lezárása után dönthető
el, kell-e külön fejlesztői jegy.

**Bizalmi fok:** a fenti táblában soronkénti. Összesítve **feltételes**, mert
a Ctrl+Alt/VK `0x12` üzleti szemantikája, valamint a videó
gyermekvezérlőjének írásjel-kezelése nincs eldöntve. Futáspróba nem történt.

### 10.23 #4698 és #4699 — a Ctrl+F9 és a Ctrl+Alt vtábla-célja (2026-10-12)

**Módszer.** A vtábla-hívások céljait a bináris bájtjaiból olvastam: a PE
VA-olvasó a `Picasa3.exe` `.rdata`-ját és a `.text`-et, a RTTI-t a
complete-object locatorból (COL) vettem, a diszasszemblálás a `pe_dis.py`
capstone-os modulja. A Ghidra-köteg (`00571e50.c`, `00571a80.c`) csak a
belépési pontokat adta; a célokat a diszasszemblátumban ellenőriztem. Az IAT-
hívások API-neve nincs az indexben, ezeket névtelenül írom le. Futtatás nem
történt.

**A vtábla-hívás típusa (mindkét billentyű).** A `0x005720af`–`0x005720c0`
a `[this+0x2a4]` vtábla `+0x2c` slotját hívja: `lea ecx,[this+0x2a4]`,
`push 0`, `call eax`. A this tehát a **részobjektum** (`this+0x2a4`), az
egyetlen stack-argumentum 0.

- A `0x00c90754` vtábla COL-ja (`0x00cff578`): a teljes objektum
  `.?AVCThumbUI@@`, a this-eltolás `0x2a4`. A `CThumbUI` bázislistájában az
  `mdisp = 0x2a4` a `.?AVINavigation@@`. A `[this+0x2a4]` tehát az
  **INavigation** interfész vtáblája, a `+0x2c` a 11. metódus-slot.
- A `0x00578dc0` a this-et `lea eax,[esi-0x2a4]`-gyel a teljes objektumra
  igazítja, ezért a `[this+0xe64]`-olvasások helyesek. Az argumentumot
  `cmp byte ptr [ebp+8]` olvassa (bool), `ret 4`.

**#4698 — Ctrl+F9 (`[panel+0xdc4]`)**

- **Kapu (`0x00571e50`, `0x00572078`–`0x005720c0`, bájtból):** `[this+0xdc4]` ≠ 0,
  a kiválasztási index (`0x6cfe10`) ≠ −1, és ≠ `[this+0xe64]` (a
  előnézetben látott kép). Ekkor `INavigation::+0x2c(0)` hívódik.
- **A célfüggvény (`0x00578dc0`, arg = 0 ág):** `0x005f89a0(this)`, majd a
  `[this+0x30d4]` módmező 7 ágú jumptable-je, és ha `[this+0xea8] ≠ 0`, a
  `0x5696c0` / `0x717260` / `0x56a9a0` sor.
- **`0x005f89a0` olvasata** (`0x005f89a0`–`0x005f8ab9`):
  1. csak ha az `editpanel/preview` objektum (`0x009c2fc0`, `0xc88a2c`)
     `[+0x20c] == 0`;
  2. a `[this+0xe64]` indexű elem rekordját kéri (`[this+0x2bc]+0x48`
     objektum, vtábla `+0x50`), és ebből bool-t képez;
  3. ezt a `0x009cd7e0`-nek adja (singleton `0xc8eb98`). A string-xref szerint
     ez az `editpanel/caption` és az `editpanel/captiontrash` állapota;
  4. a `[this+0x2ac]+8` slotot hívja a `[this+0xe64]` indexszel;
  5. `0x00579480(0,1)`: nézetfrissítés, a `0x571e50` ugyanezt hívja.
- **Nem ír `[this+0xe64]`-et.** A `0x578dc0` és a `0x5f89a0` teljes
  disasszemblátumában nincs `mov … [… +0xe64]` írás. Ezért **a kijelölt képre
  váltás nem bizonyított**.

**Bizonyított (két független útról):** (a) a kapu és a hívás bájtjai
(`0x571e50` és `0x578dc0`, arg = 0 ág); (b) az `editpanel/caption` és
`editpanel/captiontrash` string-xref-ek a `0x5f89a0`-hoz. Összegezve: a
megjelenített előnézeti kép **felirat- és törlés-állapota** frissül; a
kép nem váltódik.

**Nyitott:** a `[this+0x30d4]` módmező írói és a jumptable ágai (`0x005f8160`:
`editpanel/tab1` és `editpanel/movietab` string-xref, tehát mód 0-ban lehetséges
fülváltás; `0x00569620` és `0x005f8d80`: módok 2, 4, 5, 6); a `0x009cd7e0`, a
`[this+0x2ac]+8` és a `0x00401000` célja (utóbbi névtelen stub).

**Kész, ha:** **nincs.** A felhasználói hatás részben bizonyított (felirat és
törlés-állapot), a kijelölt képre váltás nem; a módágak nincsenek bejárva.
Következő lépés: a `[this+0x30d4]` írói a `.text`-ben (mintára), és a
`0x005f8160` dumpja.

**#4699 — Ctrl+Alt (VK `0x12`)**

- **Kapu (`0x005e65dc`, bájtból):** `[panel+0xe78] ≠ 0` és `[panel+0xe70] ≠ −1`,
  akkor `0x00571a80(panel, [panel+0xe70])`. Az `EnableHover` név a binárisban
  nincs azonosítva; a `[panel+0xe78]` lehet az, a bináris nem nevezi meg.
- **A gyerekobjektum nem CThumbUI, hanem `PopDisplay`.** A `[panel+0x31a8]`
  (0xd0 bájt) konstruktora `0x00774a00`, ami a `PopDisplay` vtáblát
  (`0x00cb36c4`, 9 slot) írja. A `0x00571a80` és az `osszefoglalo.md` #26 e
  objektumot „CThumbUI”-nak nevezi; ez a név pontatlan.
- **Ankerezés és geometria (`0x00571a80`):** újraankerez, ha a gyerek nincs,
  nincs HWND-je, nem látszik, vagy `[child+0xb8] ≠ index`. Ekkor a
  `[child+0x10]` slot (`0x00aa5760`, slot 4) a szülő-rect alapján
  `call [0x00c40814]`-et indít (MoveWindow-alakú: hwnd, x, y, w, h, 1; az
  IAT-név nincs az indexben), majd `0x00774d60(child)`. A `0x00571a80`
  `+0x18`, `+0x1c`, `+0x2c` vtábla-hívásait nem kötöttem a gyerekhez; az
  `osszefoglalo.md` #26 ezt állítja, ezt nem igazoltam.
- **Alt-flag és frissítés (`0x00774d60`):** `[child+0xb4] = !(Alt lenyomva)`
  csak akkor, ha `[0x00d67849] ≠ 0` (a „Picasa az előtérben” jelző,
  `docs/specs/00-index.md` #2224); különben `[child+0xb4] = 1`. Ezután
  `GetClientRect`, indexágak, és `InvalidateRect` + `UpdateWindow` a gyerek
  HWND-n.
- **Olvasó:** a `0x007753f0` (nem vtábla-slot; hívója nincs az indexben)
  olvassa a `[child+0xb4]`-et (`0x0077543c`, `0x00775495`). A kurzor
  `LoadCursor(NULL, 0x7f89)` (IDC_HAND) + `SetCursor` (IAT-név nélkül). Ha
  `[child+0xb4] == 0`, a `[0xd67849] ≠ 0` és az Alt élőben le van nyomva,
  a függvény `10`-zel kilép; egyébként a `0x007754b0`-ágra megy (`0x009805e0`
  és a további hover-feldolgozás).

**Bizonyított:** a kapu, a gyerek típusa (PopDisplay), a rect-hívás, az Alt-
flag írása és az olvasó elágazása. **Nyitott:** a látható tartalom (a
`0x007754b0`-ág és a `+0x18` = `0x009842d0`, `+0x1c` = `0x00774bc0` slotok
rajzolása), a `0x007753f0` hívója, és hogy az ablak `ShowWindow`-zal látszik-e.

**Kész, ha:** **nincs** — a látható hatás nincs megnevezve. Következő lépés: a
`0x007753f0` hívóinak és a `0x00774bc0`/`0x009842d0` dumpja, valamint a
`ShowWindow`-hívás keresése a `0x00571a80`-ban.

### 10.24 #4699 — 2. kör: a PopDisplay vtábla és az Alt-jelző hatása (2026-10-12)

**Módszer.** A `pe_dis.py` capstone-os diszasszembléje (scratch-venv, memóriakapuval),
a PE import-tábla feloldása (675 IAT-slot, így az API-nevek mérve vannak), és a
hivatkozások keresése a `.text`-ben (`E8 rel32` és `imm32`) és a teljes fájlban.
**Natív futtatás nem történt:** a gépen nincs Wine.

**Vtábla `0x00cb36c4` (9 slot), mért célok.** Az eltolás az objektum (`this`)
vtábla-mutatójához képest értendő.

| slot | eltolás | cél | mit csinál (bájtból) |
|---:|---|---|---|
| 0 | `+0x00` | `0x00774ad0` | skaláris destruktor (`flag & 1` → operator delete) |
| 1 | `+0x04` | `0x005abe20` | `[this+0x6c] != 0` (van-e HWND) |
| 2 | `+0x08` | `0x00983840` | Show(bool): ha van HWND, és (nem látszik, vagy minimalizált) → `ShowWindow(h, arg ? 5 : 8)` |
| 3 | `+0x0c` | `0x00775390` | **Hide**: `[this+0xc8] = [this+0xcc] = 0`, `ShowWindow(h, SW_HIDE)` |
| 4 | `+0x10` | `0x00aa5760` | `MoveWindow(h, x, y, w−x, h−y, 1)` a kapott téglalapból |
| 5 | `+0x14` | `0x00983270` | Close(bool): `arg = 0` → `EnumThreadWindows` vagy `PostMessage(WM_CLOSE)`; `arg ≠ 0` → a törlő ág |
| 6 | `+0x18` | `0x009842d0` | **húzás**, nem rajzolás: `ReleaseCapture`; ha a fő gomb le van nyomva → `SendMessage(WM_SYSCOMMAND, 0xF012)` (SC_MOVE\|HTCAPTION) és kattintás-szimuláció |
| 7 | `+0x1c` | `0x00774bc0` | **WndProc** (ld. alább) |
| 8 | `+0x20` | `0x00985550` | a gyermek (`[this+0x64]`) slot 12-jét hívja; gyermek nélkül `1000001` (0xF4241). Nem azonosítva. |

**A WndProc (slot 7) ágai:** `WM_DESTROY` (2) → a szülő `[+0x31a8]` mutatóját nullázza.
`WM_PAINT` (0xF) → `BeginPaint` → ha `rcPaint` nem üres, **`0x009aa720(obj = [this+0x8c], rect)`** → `EndPaint`.
`WM_KEYDOWN`/`WM_SYSKEYDOWN` (0x100/0x104) `VK_RIGHT` (0x27) → `+1`, `VK_LEFT` (0x25) → `−1`;
`WM_MOUSEWHEEL` (0x20A) → a görgetés irányával; mindkettő a `0x774cf0` léptetőbe megy (index a `[this+0xb8]`-ban,
lista `[this+0xc0]`-ban). Minden más üzenet a `0x00984970`-re.

**A rajzoló (`0x009aa720`, bájtból).** `CreateCompatibleDC`, majd a `[obj+0x24]` bitmap kiválasztása, és
**`BitBlt(hdc, x, y, w, h, memdc, …, SRCCOPY 0xCC0020)`**. A keretrajzolás (`GetStockObject(NULL_BRUSH)`,
`CreatePen(PS_INSIDEFRAME, 2)`, `Rectangle`, `Sleep(10)`) csak akkor fut, ha a
`[0x00d6fc4e]` jelző igaz; a jelzőt a `HKCU…\Preferences` alatti **`Debug Blt`** érték adja
(`0x004019b0`, a kulcsnevek `0x00c7eafc` = `Preferences`, `0x00cd951c` = `Debug Blt`).
Tehát a popup **kész bitmapet másol ki**, a keret csak diagnosztikai kapcsolóval jelenik meg.
Az alapértelmezett érték nincs megállapítva.

**`[child+0xb4]` (Alt-jelző): író, olvasó, hatás.**

- **Író: `0x00774d60`** (frissítő). Hívói: `0x00571dfa` (az ankerező `0x00571a80`-ban) és
  `0x00774d4f` (a `0x774cf0` léptetőben). Ha `[0x00d67849] ≠ 0` (a spec szerint: „Picasa az előtérben"),
  `b4 = !(GetAsyncKeyState(VK_MENU) & 0x8000)`; különben `b4 = 1`. Utána `GetClientRect`,
  a `[owner+0x270]` vtábla +0x0C slotja (az elem lekérése a `[this+0xb8]` indexről), `0x9b49c0`,
  `0x9aabf0`, és **`InvalidateRect` + `UpdateWindow`** (→ WM_PAINT). A frissítő **nem** hív `ShowWindow`-t.
- **Olvasó: `0x007753f0`** — a hover-tick (`edi` = a PopDisplay). Közvetlen hívója a `0x00775550`
  wrapper (`QueryPerformanceCounter`-rel időbélyeg, majd `call 0x7753f0`). A wrapper pointere a
  `0x00cb36f0` táblában áll, slot 0-ként; ehhez a táblához `.text`-ben nincs `imm32` író, az
  objektum-típus **nem azonosított**.
- **A tick döntési fája** (ha `IsWindowVisible(hwnd)` igaz; különben `100`-zal kilép):
  1. `SetCursor(LoadCursor(NULL, 0x7F89))` — **IDC_HAND** (32649 = 0x7F89, a `winuser.h` szerint; ez a név
     a headerből jön, nem a bináris azonosításából). Ez az ág minden ticknél lefut.
  2. **`b4 ≠ 0`:** `fg = 0` → kilép (`10`). `fg = 1` → ha a fő egérgomb (`GetSystemMetrics(SM_SWAPBUTTON)`
     szerint `VK_LBUTTON` vagy `VK_RBUTTON`) **nincs** lenyomva → kilép (`10`); lenyomva → HOVER.
  3. **`b4 = 0`:** `fg = 0` → HOVER; `fg = 1` → ha `VK_MENU` (Alt) **most is** le van nyomva → kilép (`10`);
     különben HOVER.
  4. **HOVER (`0x007754b0`):** `0x009805e0` (PeekMessage-ciklus a `0x100–0x109` tartományra, `PM_REMOVE`:
     a billentyű-üzeneteket kiveszi a sorból; ESC esetén `1`-et ad, a visszatérését itt nem használja),
     majd az elem-ág, és **minden ág végén a vtábla slot 3 = Hide** (`0x00775525`).
- A kódban **nincs Ctrl-vizsgálat**: a tickben és a frissítőben csak `VK_MENU` (0x12) szerepel.
  A „Ctrl+Alt" név a spec-ből (`#4699`) jön, a bináris csak az Alt-ot nézi.

**Ellentmondás a 10.23-mal (jelentve, nem írtam át).** A 10.23 szerint a tick Alt nélkül
„egyébként a `0x007754b0`-ágra megy". A mért fa szerint `b4 ≠ 0` mellett a HOVER csak a fő egérgomb
lenyomva tartásakor fut; gomb nélkül kilép. A 10.23 `+0x18` = „rajzolás" címkéje is téves: a slot 6 a
húzás, a rajzoló a slot 7 WM_PAINT-ága.

**Mit lát a felhasználó Ctrl+Alt (Alt) lenyomásakor — mi bizonyított:**

- Alt lenyomva tartva, ha az utolsó frissítés is Alt-tal történt (`b4 = 0`) és a Picasa az előtérben van: a tick
  korán kilép, a HOVER-rejtés nem fut. **A popup marad ott, ahol van**, a kurzor kéz-alakú. Az Alt
  elengedése után a tick HOVER-ágra megy, gomb nélkül is.
- Alt nélkül (`b4 = 1`): a HOVER csak a fő egérgomb lenyomva tartásakor fut.
- **Nem bizonyított:**
  (a) mi jelenik meg a popupban: a `[obj+0x24]` bitmap forrása és a `0x9aabf0` / `0x9b49c0` betöltés nincs végig követve;
  (b) mikor látszik a popup: a slot 2 (Show) hívói nincsenek azonosítva;
  (c) a kiváltó billentyű-üzenet: a `0x005e65dc` egy switch-ágban van, az ugrótábla (`0x005e6617` hivatkozás)
  nincs dekódolva, így nem tudjuk, hogy a lenyomás és az elengedés is frissít-e;
  (d) a popup az Alt-tartás közben mutat-e bármit: ez a rejtés elmaradásából következik, de nem látható.

**Nálunk (grep: `src/picasapy/app`, `qml`):** nincs `EnableHover`, `PopDisplay`, és nincs Alt-tartású
hover-popup. Az Alt-használat: Alt+Enter (Tulajdonságok), kollázs Alt-húzás (`CollageSheet`, `CollageNode`),
arc-kijelölés (`FacesOverlay`), a `PhotoViewer` Alt-kattintása (sor 3958, nem vizsgáltam részletesen).

**Kész, ha: nincs.** A látható hatás (a popup tartalma, megjelenése, az Alt-kiváltás) nincs bizonyítva,
ezért a „hiányzik nálunk" állítás nem alapozható meg. A rejtés-gátlás bizonyított, de önmagában nem
elég egy jegy megnyitásához.

**Következő lépés (ebben a sorrendben):**
1. A `0x005e65dc` switch-tábla dekódolása (az `ugrótábla` és a case üzenetkód), hogy kiderüljön a kiváltó üzenet.
2. A `0x00cb36f0` vtábla objektumának konstruktora (lea-alapú hivatkozás a `.text`-ben).
3. A `0x009aabf0` / `0x009b49c0` (bitmap-betöltés) és a slot 2 (Show) hívóinak felsorolása.
4. A `Preferences\Debug Blt` alapértelmezésének meghatározása (a registry-alapérték, `0x004019b0`).

### 10.25 #4698 és #4699 — 3. kör: a jelző teljes olvasóslistája, a módmező, a popup-bitkép és a kiváltó (2026-10-12)

**Módszer.** `pe_dis` (capstone, scratch-venv), a `paszta.utasitasok()` darabolt
lineáris pásztázása a **teljes `.text`-re** (2 884 879 utasítás, csúcs-RSS 85 MiB,
`systemd-run` 2400 MiB-os plafonnal), bájt-előszűrés (`c4 0d 00 00` = disp32 `0xdc4`;
11 találat: 4 memóriaoperandus, 7 `sub/add esp, 0xdc4` imm), és a `0x30d4`, `0x31a8`,
`0xe70`, `0x24` mintákra ugyanez. A callee-API-neveket az index `imports.csv`
`func_addr` oszlopa adja (függvény → IAT-API); a vtábla-slotokat a `.rdata`-ból
olvastam; a `this`-típust a COL-ból (RTTI). Natív futás nem történt (nincs Wine).

**A) `[this+0xdc4]` (Ctrl+F9-jelző): az összes hivatkozás a `.text`-ben — MÉRVE**

| hely | függvény | utasítás | szerep | `this` |
|---|---|---|---|---|
| `0x00564b2e` | `0x005643e0` | `mov byte [ebp+0xdc4], bl` | **írás** (konstruktor) | `CThumbUI` |
| `0x00572078` | `0x00571e50` | `cmp byte [ebx+0xdc4], 0` | **olvasás** (frissítő kapu) | `CThumbUI` |
| `0x005e6329` | `0x005e60d0` | `cmp byte [ebp+0xdc4], 0` | **olvasás** (toggle) | `CThumbUI` |
| `0x005e6333` | `0x005e60d0` | `mov byte [ebp+0xdc4], cl` | **írás** (toggle: `cl = (flag == 0)`) | `CThumbUI` |

- **A `this`-típus:** a `0x005643e0` konstruktor az `[ebp]`-be a `0x00c9052c` vtáblát
  írja; ennek COL-ja (`0x00cff578`-tól eltérő, `mdisp 0`) a **`.?AVCThumbUI@@`**. A
  `0x00c90754` (az `[this+0x2a4]` INavigation-vtábla) COL-ja ugyanezt a teljes objektumot
  adja (`mdisp 0x2a4`). Tehát mind a négy hivatkozás `CThumbUI`-objektumon van.
- **Konstruktor-írás:** `ebx` a `0x005643eb`-ben `xor ebx, ebx`-szel nulla, és a teljes
  függvényben ezen kívül nincs írás `ebx`-re (az egyetlen más `pop ebx` a `0x005651c3`,
  a `0x00564b2e` után). Tehát a jelző **0-ra inicializálódik**.
- **Mit kapcsol a `0x005e6329`:** a `0x005e60d0` VK-switch táblája (a `0x005e61f1`
  `jmp`; index = `vk − 0xd`, bájttábla `0x005e66a4`, ugrótábla `0x005e6614`) dekódolva:
  **`vk 0x78` (F9) → `0x005e6329`**, `vk 0x12` (Alt) → `0x005e65dc`, `vk 0x11` (Ctrl) → a
  `0x005e65f7` kilépés. Az F9-ág: `flag = !flag` (egyetlen `sete` + `mov`), módosítóellenőrzés
  **nélkül** az ágban.
- **Az ág előtti kapuk (mért):** (i) csak `WM_KEYDOWN` (`0x100`); (ii) a `[esi+0x10]`
  eseményjelző `0x04` bitje kell (`test byte [esi+0x10], 4; jle` a `0x005e6178`-ban; kivétel
  csak az F12, `0x7b`); (iii) a `[this+0x30d4]` módmező **nem** 2, 4 vagy 6 (a `0x005e60e6`
  három `sub 2 / je`-je; mód 2, 4, 6-ban a billentyűkezelő azonnal kilép, minden billentyűre).
  A módosító-bitek a `0x005e61a5`–`0x005e61b8` `setg`-jeiből (bitek `0x08`, `0x02`, `0x04`)
  a `0x005c5f90` 6 bájtos rekordjába és a `0x005c5fc0` keymap-keresésbe mennek (`[this+0xcdc]`
  tábla). **Nem igazolt:** hogy a `0x04` bit a Ctrl-e. A „Ctrl+F9” név a 10.9 szerinti Ctrl-ágból
  jön; ebben a körben a kiváltó üzenet-rekord írója nincs követve.

**B) A `[this+0xdc4]` felhasználói hatása (egy mondatban):** F9 megfordítja a jelzőt;
bekapcsolt jelzőnél a `0x00571e50` frissítésekor, ha a kijelölt index ≠ −1 és ≠ a
`[this+0xe64]` (előnézet), a `0x00578dc0(0)` a megjelenített előnézet **felirat- és
törlés-állapotát** frissíti (`0x005f89a0` → `0x009cd7e0`), a kép **nem** vált — a `[this+0xe64]`-et
sem a `0x578dc0`, sem a `0x5f89a0` nem írja.

**C) A `0x00571e50` kapu (ellenőrizve, a 10.23 pontos):** `0x572043`: `[0xd67914] ≠ 0`,
előnézet-singleton `0x00c88a2c` nem nulla és `[+0x20c] == 0`; `esi = −1`; `0x572078`:
`[this+0xdc4] ≠ 0` → `esi = call 0x6cfe10([[this+0x2bc]+0x346c])`; ha `esi ≠ −1` és
`esi ≠ [this+0xe64]` → `[this+0x2a4]`-vtábla `+0x2c` (`INavigation` 11. slot) `push 0`.

**D) A `0x00578dc0(arg=0)` ága (a 10.23 hívása):** feltételei sorrendben: (1)
`[0xd67914] ≠ 0`, különben `0x578ef8` és a caption-ág kimarad; (2) előnézet-singleton
`[+0x20c] == 0`; (3) `0x00562d00` (kapuzó, `false`; a `0x009e39b0` láthatósági láncot hívja a
`0x00c95f70`, `0x00c95ae4`, `0x00c98adc` singletonokra — **nem azonosított**); (4) `arg == 0` →
`0x005f89a0(this)`; utána a mód-jumptable.

**E) ⛔ A `[this+0x30d4]` módmező a `0x005f89a0`-ban NINCS — a 0x578dc0-ban van.** A
kérdés/feladat szerint a módágak a `0x005f89a0`-ban lennének; a mért szöveg szerint a
`0x005f89a0` egyetlen `0x30d4`-hivatkozást sem tartalmaz (`[ecx+0x2c4]`, `[esi+0x2bc]`,
`[esi+0xe64]`, `[esi+0x2ac]`, `[+0x20c]` van benne). A módágak a **`0x00578dc0`** `0x578e7e`–
`0x578e90` jumptable-jében vannak (`0x00578f34` ugrótábla, `0x00578f40` indexbájtok; a
10.23 ezt helyesen írta, a feladat megfogalmazása nem):

| mód | ág | mit hív (mért) |
|---|---|---|
| 0 | `0x578e97` | `0x005f8160` (fülkezelő; a 10.23 szerinti `editpanel/tab1`/`movietab` ág) |
| 1, 3 | `0x578e9e` | semmit (a `[this+0xc04]`-ág) |
| 2, 4, 5, 6 | `0x578edc` | `0x569620`, majd `0x005f8d80` |
| ≥ 7 | `0x578e9e` | semmit |

- **Mód-író (mért):** `0x00564896` (konstruktor, `ebx = 0` → mód 0 kezdetben) és
  `0x0057c21a` a `0x0057bb50` függvényben: `SetMode(this, flag: byte [+0x30d0], mode: dword)`
  (`[+0x30d0] = flag`, `[+0x30d4] = mode`; a végén az `[ebp+0x10]` az új mód). A `0x0057bb50`
  hívóit nem követtem végig.
- **`0x005f8160` (mód 0), részben:** `[this+0x337c] = 0`; `call 0x50ccd0` eredményére
  switch: `1 → 0x5d7780`, `2 → 0x5d77d0`, `3..5 → 0x5d78d0`, különben dinamikus típus-ellenőrzés
  (`0x00c94b8c`-os üzenet). A `0x50ccd0`, `0x5d7780`, `0x5d77d0`, `0x5d78d0` célja nincs azonosítva.

**F) A PopDisplay vtáblája és a bitkép (#4699).** A `0x00cb36c4` vtábla 9 slotja
(`.rdata`-ból, mért): `0:0x774ad0 1:0x5abe20 2:0x983840 3:0x775390 4:0xaa5760 5:0x983270
6:0x9842d0 7:0x774bc0 8:0x985550`. A `0xcb36c4`-re `.text`-ben csak a `0x00774a00` és a
`0x00774af0` hivatkozik (konstruktor-lánc); más kód nem tesztel vtáblát ilyen cím szerint.

- **`[obj+0x24]` nem a popupon van, hanem a `[popup+0x8c]`-n.** A `0x009aa720` (WM_PAINT
  rajzoló, `0x00774c5f`-ből) `obj = [this+0x8c]`; a `0x00774a00` konstruktor a `+0x8c` részt
  pixel-pufferként állítja be: `+0x08` szélesség, `+0x0c` magasság, `+0x10` bitek mutatója,
  `+0x24` HBITMAP (`0`-ra induló).
- **A bitkép írója: `0x009a9b30`.** Az index szerint ez hívja a **`CreateDIBSection`**-t
  (`GetDC`/`ReleaseDC` mellett; a `0x009a9c2e` `call [0xc40180]` az IAT-hívás, az API-nevet
  az index a `func_addr` oszlopból adja); a `0x009a9c36` `mov [esi+0x24], eax` a hívás után
  írja a HBITMAP-et. A `[esi+0x10]` címe (`lea edi,[esi+0x10]`) a bitek kimeneti mutatóját
  adja (következtetés: a `ppvBits`), a `push 0x28` a BITMAPINFOHEADER mérete. Hibaágon `0`-t ír
  (`0x009a9bba`, `0x009a9c72`).
- **A `0x009a9b30` hívója: `0x009a8a30`** (79 bájt): `[+0x24] = 0`, és ha a `+0x08`/`+0x0c`
  nem nulla, a `0x009a9b30`. A `0x009a8a30`-at a `0x00774d60` (frissítő) `0x0077516e`-nál és a
  `0x007753f0` (hover-tick) `0x00775506`-nál hívja. A konstruktor (`0x00774a52`) méret nélkül
  hívja (nincs allokáció).
- **A tartalom:** a `0x00774d60` a `[this+0xb8]` indexű elemre kéri a `[owner+0x270]` vtábla
  `+0x04` slotját (`owner = [this+0x88]`), a kimenetet a `0x009aabf0` (pixel-másolás) viszi a
  `[popup+0x8c]` bufferbe. **Tehát a bélyegkép az alkalmazás saját elemének képe, nem
  képernyőkép.**

**G) A popup megjelenésének kiváltója (mért út).**
- **Alt-ág:** `0x005e65dc`: `[panel+0xe78] ≠ 0` és `[panel+0xe70] ≠ −1` → `0x00571a80(panel,
  [panel+0xe70])` (`0x005e65f2`).
- **A `0x00571a80` (újraankerez):** `MoveWindow` a popupon (`0x571b32`: `[popup]`-vtábla slot 4),
  `[popup+0xb8] = index` (`0x571de4`), majd **`0x00774d60`** (`0x571dfa`, feltétel nélkül).
- **A `0x00774d60`:** a bitkép-másolás után **`0x00775320`** (`0x7750ca`). A `0x775320`:
  `[this+0x6c]` HWND-re, ha nem látszik vagy minimalizált (a két IAT-hívás sorrendje
  következtetés, lásd H) → **`ShowWindow(h, 5)`** (SW_SHOW). A `[+0xc8]/[+0xcc]` gyorsítótár az `[owner+0x2bc]+0x346c` objektum `+0x80/+0x84`-ből.
  A `0x774d60` korábbi kilépéseit nem tártam fel teljesen.
- **Másodlagos anchor-hívó:** `0x005c29a9` (`0x005c24c0`-ban) `0x571a80(this, [ebx+0x28], −1)`;
  a `−1` miatt az index a `[this+0xe64]`. Kapuja (`0x005c2410`, `0x009c84a0`) nem azonosított.
- **Elrejtés:** a tick végén a **vtábla slot 3** (`0x775390`, `ShowWindow(h, SW_HIDE)`; a hívás
  `0x77552c`-nál), `[+0xc8] = [+0xcc] = 0`.

**H) A `Show(true)` (slot 2 = `0x983840`) hívói — NEM AZONOSÍTOTTAK.**
- A `0x983840` törzse: `[this+0x6c]` HWND; ha `IsWindowVisible == 0` vagy `IsIconic ≠ 0`
  → `ShowWindow(h, arg ? 5 : 8)`. (A két IAT-hívás sorrendje az `imports.csv`-ből nem derül
  ki; a fenti hozzárendelés a törzs elágazásából következik.)
- A **popup-osztály** kódjában (`0x774a00`–`0x775800`) **nincs** `[reg+8]`-slot-2 hívás; a
  `0x571a80` csak slot 4-et hív a popupon; a `0x576a20` (bezárás) slot 5-öt `arg = 1`-gyel, és
  `[this+0x31a8] = 0`-t ír.
- A **`0x983840`-re közvetlen E8-hívás egyetlen** van: `0x009b9a3c` (`0x009b9a30`-ban). Az a
  függvény `[this+0x6c]`-t és `[this+0x88]`-at olvas (a popup elrendezésével egyezik), de nem
  a popup osztálya: a vtáblája nincs azonosítva (a `.text` imm-keresése nem találja a
  `0x009b9a30`-at; a vtáblák a `.rdata`-ban vannak, azt ebben a körben nem kerestem végig).
- **Következtetés:** a popup `Show(true)` ágát a slot 2 virtuális hívása adná, de annak
  hívója nincs azonosítva. A megjelenést a mért út (G) adja: `0x775320` `ShowWindow(5)`-öt.

**I) Kész, ha — mindkét pontra.**
- **#4698 (Ctrl+F9):** a hatás **részben** bizonyított: a jelző olvasói/írói teljesek, a
  felirat- és törlés-állapot-frissítés bizonyított (A–D). **Nincs kész**: a látható állapot
  (a `0x9cd7e0` bool-jának jelentése, a `0x562d00`-gate, a módágak 0/1/3/5) nincs végigkövetve.
  Nálunk a Ctrl+F9-nek nincs megfelelője (`grep`: nincs `F9`/`captiontrash`).
- **#4699 (Ctrl+Alt popup):** a kiváltó lánc (Alt → `0x571a80` → `0x774d60` → `0x775320` →
  SW_SHOW) és a bitkép tartalma (az elem képe) **bizonyított**. **Nincs kész**, mert (a) a
  kurzor-összerendelés nyitott: a `[panel+0xe70]` a `0x0056b6f0`-ban `= [this+0xe64]`-ként
  íródik (`0x0056b731`), az `[this+0xe64]`-et pedig a `0x005704d0` írja (`0x005704fe`,
  `0x00570644`), a `0x56b6f0` argumentuma a `0x00641c80` paramétere (`0x0064255f`), amelynek
  forrása (egérpozíció → elemindex) **nincs követve**; (b) a `Show(true)` hívója nincs
  azonosítva; (c) a `[panel+0xe78]` (az Alt-kapu) írója nincs pásztázva (a konstruktor írja
  `0x00564d1a`-nál). Nálunk nincs `EnableHover` és nincs `PopDisplay` (10.24).

**Következő lépés (ebben a sorrendben):**
1. A `0x00641c80` paraméterének hívóláncja (ki hívja, és honnan jön az elemindex): a
   `0x00641c80` és a `0x005709a0` hívói, az `egérpozíció → index` átalakítás megtalálása.
2. A `0x00562d00` kapu három singletonja (`0x00c95f70`, `0x00c95ae4`, `0x00c98adc`) és a
   `0x009e39b0` láncvizsgálat azonosítása.
3. A `[panel+0xe78]` írói (`.text`-pásztázás `0xe78`-ra) és a `0x005c24c0` kapuja
   (`0x005c2410`, `0x009c84a0`).
4. A `0x00774d60` korábbi kilépéseinek feltárása: a `0x775320` feltétel nélkül fut-e minden
   frissítésnél.

## 11. #4462 — eredeti billentyűk paritása és CI-őre

A mérce a lap korábbi, forráskritikával ellátott táblája: a keymap-komment önmagában nem parancsszerződés. A 3.9 tényleges menürekordja, a 10. szakasz billentyű-dispatch mérése és a 6.2 szakasz mai QML-kötése együtt dönti el, hogy az eredeti billentyű milyen műveletet jelent. A fókuszkapu a #4398 szerinti: a szövegmező saját szerkesztőbillentyűi elsőbbséget kapnak; a könyvtári billentyűk nem szólnak bele a néző vagy a külön párbeszéd billentyűzésébe.

Az állapot mező értékei:

- **megvan és működik** — az eredeti parancsot a jelenlegi QML-útvonal végzi, a felsorolt nézet- és fókuszkapuval;
- **hiányzik** — az eredeti parancsot vagy a billentyűt még nem végzi el a megfelelő mai művelet;
- **nem cél** — a forrás bizonyítja, hogy a keymap-komment nem aktív kötés, az eredeti rekesz üres, vagy a #4443 kivétel él;
- **tisztázandó** — a forrásban nincs elég adat a mai parancs-hozzárendelés megállapításához; itt nem találgatunk.

| # | eredeti billentyű | eredeti parancs a mért 3.9-ben | PicasaPy-kötés / parancs | állapot | nézet- és fókuszkapu | CI-ellenőrzés |
|---:|---|---|---|---|---|---|
| 1 | Ctrl+N | Új album | objectName=shortcutNewAlbum → új album | **megvan és működik** | Főablak; fotóműveleti kapu; szövegfókusz nélkül | tests/app/qml_functional/test_gyorsbillentyuk_1616.py |
| 2 | Ctrl+O | Fájl felvétele | objectName=shortcutAddFile → fájlfelvétel | **megvan és működik** | Könyvtárnézet; nézőn kívül; szövegfókusz nélkül | tests/app/qml_functional/test_gyorsbillentyuk_1616.py |
| 3 | Ctrl+M | Importálás forrása | objectName=shortcutImportFrom → import párbeszéd | **megvan és működik** | Könyvtárnézet; nézőn kívül; szövegfókusz nélkül | tests/app/qml_functional/test_gyorsbillentyuk_1616.py |
| 4 | Ctrl+Shift+O | Kijelölt fájlok megnyitása a rendszer szerkesztőjében | objectName=openInEditorShortcut → alapértelmezett fájlmegnyitó | **megvan és működik** | Főablak; érvényes fotóművelet; szövegfókusz nélkül | tests/app/qml_functional/test_gyorsbillentyuk_1616.py |
| 5 | F2 | Átnevezés | sequence=F2 → átnevezés | **megvan és működik** | Könyvtárnézet; van kijelölés; szövegfókusz nélkül | tests/app/test_qml_fileops_export.py |
| 6 | Ctrl+Shift+S | Kép exportálása mappába | sequence=Ctrl+Shift+S → export párbeszéd | **megvan és működik** | Könyvtárnézet; van kijelölés; szövegfókusz nélkül | tests/app/test_qml_fileops_export.py |
| 7 | Ctrl+S | Mentés | sequence=Ctrl+S → szerkesztés mentése | **megvan és működik** | Főablak; szövegfókusz nélkül; menthető szerkesztés esetén aktív | tests/app/qml_functional/test_photo_menu_commands.py |
| 8 | Ctrl+Enter | Keresés a lemezen | objectName=shortcutLocateOnDisk → fájlkezelő | **megvan és működik** | Érvényes fotóművelet; szövegfókusz nélkül | tests/app/test_kereses_almenu_1613.py |
| 9 | Delete | Törlés lemezről vagy eltávolítás az albumból | objectName=shortcutDeleteFromDisk → nézetfüggő törlési út | **megvan és működik** | Aktív könyvtárnézet; szövegfókusz nélkül; albumtagság szerint vált | tests/app/qml_functional/test_torles_billentyu_felulet_1418.py |
| 10 | Ctrl+P | Nyomtatás | objectName=shortcutPrint → nyomtatási párbeszéd | **megvan és működik** | Főablak; érvényes fotóművelet; szövegfókusz nélkül | tests/app/test_qml_tray_print_email.py |
| 11 | Ctrl+E | E-mail | objectName=emailShortcut → kijelölés e-mailben | **megvan és működik** | Főablak; van kijelölés; szövegfókusz nélkül | tests/app/test_email_controller.py |
| 12 | Ctrl+T | Címkék panel | sequence=Ctrl+T → Címkék fiók | **megvan és működik** | Könyvtárnézet; nézőn kívül; szövegfókusz nélkül | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 13 | Ctrl+X | Kivágás | sequence=Ctrl+X → fájlok kivágása | **megvan és működik** | Könyvtárnézet; van kijelölés; szövegfókusz nélkül | tests/app/test_vagolap_beillesztes_1526.py |
| 14 | Ctrl+C | Másolás | sequence=Ctrl+C → fájlok másolása | **megvan és működik** | Könyvtárnézet; van kijelölés; szövegfókusz nélkül | tests/app/test_vagolap_beillesztes_1526.py |
| 15 | Ctrl+V | Beillesztés | sequence=Ctrl+V → vágólap tartalmának beillesztése | **megvan és működik** | Könyvtárnézet; szövegfókusz esetén a mezőé a billentyű | tests/app/test_vagolap_beillesztes_1526.py |
| 16 | Ctrl+A | Összes kijelölése | sequence=Ctrl+A → könyvtári kijelölés | **megvan és működik** | Könyvtárnézet; szövegfókusz nélkül | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 17 | Ctrl+I | Kiválasztás megfordítása | sequence=Ctrl+I → könyvtári kijelölés megfordítása | **megvan és működik** | Könyvtárnézet; szövegfókusz nélkül | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 18 | Ctrl+D | Kijelölés törlése | sequence=Ctrl+D → könyvtári kijelölés ürítése | **megvan és működik** | Könyvtárnézet; szövegfókusz nélkül | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 19 | Ctrl+1 | Kis indexképek | objectName=shortcutSmallThumbnails → kis méret | **megvan és működik** | Könyvtárnézet; szerkesztő nélkül; szövegfókusz nélkül | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 20 | Ctrl+2 | Normál indexképek | objectName=shortcutNormalThumbnails → normál méret | **megvan és működik** | Könyvtárnézet; szerkesztő nélkül; szövegfókusz nélkül | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 21 | Ctrl+3 | Szerkesztési nézet | sequence=Ctrl+3 → megjelenítés és szerkesztés | **megvan és működik** | Könyvtárnézet; néző nélkül; szövegfókusz nélkül | tests/app/qml_functional/test_enter_megnyit_1417.py |
| 22 | Ctrl+K | A keymap-komment szerint Kulcsszavak; a mért menürekord nem ad hozzá Ctrl+K-t | objectName=tagsPanelAltShortcut → PicasaPy-alias a Címkék panelhez | **nem cél — a 2.4 és 3.3 szerint a komment elavult, a tényleges Picasa-kötés Ctrl+T** | A PicasaPy-alias csak könyvtárnézetben és szövegfókusz nélkül él | tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py |
| 23 | Ctrl+4 | Diavetítés | sequence=Ctrl+4 → diavetítés indítása | **megvan és működik** | Főablak; szövegfókusz nélkül | tests/app/test_qml_slideshow.py |
| 24 | Ctrl+5 | Időrend | sequence=Ctrl+5 → állandóan tiltott | **nem cél — a Ctrl+5 szándékosan inaktív a #4443-ig** | Mindig tiltott | tests/app/test_qml_timeline.py |
| 25 | Ctrl+Shift+P | Indexképek nyomtatása | objectName=shortcutPrintContactSheet → indexkép-nyomtatás | **megvan és működik** | A Mappa-menütétellel azonosan mindig aktív; kijelöléstől és szövegfókusztól független | tests/app/qml_functional/test_indexkep_nyomtatas_1590.py |
| 26 | Ctrl+W | A keymap-komment szerint weboldal export; a mért menüsávban nincs ilyen billentyű | sequence=Ctrl+W → csak projektlap bezárása | **nem cél — a 10.7 szerint az eredeti dispatchben sincs Ctrl+W ág; a projektlap parancsa PicasaPy-funkció** | Csak nyitott projektlapnál; szövegfókusz nélkül | tests/app/qml_functional/test_projektlap_billentyuk_2170.py |
| 27 | Ctrl+R | Forgatás jobbra | sequence=Ctrl+R → aktuális kijelölés vagy nézőkép forgatása | **megvan és működik** | Főablak; szövegfókusz nélkül | tests/app/qml_functional/test_photo_menu_commands.py |
| 28 | Ctrl+Shift+R | Forgatás balra | sequence=Ctrl+Shift+R → aktuális kijelölés vagy nézőkép forgatása | **megvan és működik** | Főablak; szövegfókusz nélkül | tests/app/qml_functional/test_photo_menu_commands.py |
| 29 | Alt+Enter | Tulajdonságok | sequence=Alt+Return → Tulajdonságok panel | **megvan és működik** | Könyvtárnézet; érvényes fotóművelet; szövegfókusz nélkül | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 30 | F1 | Súgó | sequence=F1 → súgó | **megvan és működik** | Főablak vagy súgóablak; helyi ablak aktív; szövegfókusz nélkül | tests/app/qml_functional/test_sugo_bekotes_2054.py |
| 31 | Ctrl+Shift+B | Fekete-fehér kötegelt művelet | objectName=batchBwShortcut → meglévő renderlánc-művelet | **megvan és működik** | Könyvtárnézet; szövegfókusz nélkül | tests/app/test_gyorsbillentyu_agak_2163.py |
| 32 | Ctrl+Shift+E | Jó napom van kötegelt művelet | objectName=batchEnhanceShortcut → meglévő renderlánc-művelet | **megvan és működik** | Könyvtárnézet; szövegfókusz nélkül | tests/app/test_gyorsbillentyu_agak_2163.py |
| 33 | Ctrl+F | Keresés | objectName=searchShortcut → keresőmező | **megvan és működik** | Könyvtárnézet; keresőmező fókuszában a billentyű a mezőé | tests/app/qml_functional/test_shortcut_focus_4398.py |
| 34 | Ctrl+H | Kijelölés megtartása a képtálcán | objectName=trayKeepSelectionShortcut → tálca megtartása | **megvan és működik** | Főablak; nem néző; nem üres tálca-kijelölés; szövegfókusz nélkül | tests/app/qml_functional/test_talca_menu_1917.py |
| 35 | Ctrl+Shift+H | Vízszintes tükrözés | objectName=flipHorizontalShortcut → vízszintes tükrözés | **megvan és működik** | Kijelölés vagy a néző aktuális képe; szövegfókusz nélkül | tests/app/test_gyorsbillentyu_agak_2163.py |
| 36 | Ctrl+Shift+V | Függőleges tükrözés | objectName=flipVerticalShortcut → függőleges tükrözés | **megvan és működik** | Kijelölés vagy a néző aktuális képe; szövegfókusz nélkül | tests/app/test_gyorsbillentyu_agak_2163.py |
| 37 | ➖ (ctrl=1, üres billentyű) | Mozgatás az album végére | Nincs eredeti billentyű; nincs mai kötés | **nem cél — a szállított keymap-rekeszben üres az srckey** | Nincs billentyű | tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py |
| 38 | Ctrl+N | Új album; az 1. rekesz parancsával azonos | objectName=shortcutNewAlbum → ugyanaz az újalbum-útvonal | **megvan és működik** | Az 1. sor kapuja szerint | tests/app/qml_functional/test_gyorsbillentyuk_1616.py |
| 39 | F11 | Teljes képernyős mód | objectName=viewerFullscreenShortcut → nyitott képnéző teljes képernyős módjának váltása | **megvan és működik** | Csak nyitott képnézőben; a diavetítés saját teljes képernyős állapota érintetlen | tests/app/qml_functional/test_viewer_fullscreen_4569.py |
| 40 | Home | Az első kép kijelölése az albumban | Keys=Qt.Key_Home → fókuszált rács első csoportja | **megvan és működik** | A rács kapja az eseményt; szövegfókuszban a mezőé | tests/app/qml_functional/test_home_end_lapozas_1147.py |
| 41 | End | Az utolsó kép kijelölése az albumban | Keys=Qt.Key_End → fókuszált rács utolsó csoportja | **megvan és működik** | A rács kapja az eseményt; szövegfókuszban a mezőé | tests/app/qml_functional/test_home_end_lapozas_1147.py |
| 42 | / | Videó lejátszás/szünet | Nincs igazolt mai kötés | **tisztázandó — a 7. és 10.19. szakasz szerint a videó billentyűzete nincs mérve** | Videólejátszó fókusza szükséges; az eredeti célt nem kötjük ki találgatásból | tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py |
| 43 | , | Videó visszatekerése | Nincs igazolt mai kötés | **tisztázandó — a 7. és 10.19. szakasz szerint a videó billentyűzete nincs mérve** | Videólejátszó fókusza szükséges; az eredeti célt nem kötjük ki találgatásból | tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py |
| 44 | . | Videó előretekerése | Nincs igazolt mai kötés | **tisztázandó — a 7. és 10.19. szakasz szerint a videó billentyűzete nincs mérve** | Videólejátszó fókusza szükséges; az eredeti célt nem kötjük ki találgatásból | tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py |
| 45 | ➖ (nincs billentyű) | Következő kép; az eredeti külön nyílkezelője működik | Keys=Keys.onRightPressed → rács vagy PhotoViewer következő képe | **megvan és működik** | Fókuszált képnézet; nézőben a szövegmező átveszi | tests/app/qml_functional/test_nezo_forrasmeret_3877.py |
| 46 | ➖ (nincs billentyű) | Előző kép; az eredeti külön nyílkezelője működik | Keys=Keys.onLeftPressed → rács vagy PhotoViewer előző képe | **megvan és működik** | Fókuszált képnézet; nézőben a szövegmező átveszi | tests/app/qml_functional/test_nezo_forrasmeret_3877.py |
| 47 | ➖ (nincs billentyű) | Automatikus/kézi mód váltása | Nincs azonosított eredeti parancs vagy mai kötés | **tisztázandó — a forrás nem azonosítja a rekesz műveletét** | Nincs megállapítható kapu; nem találgatunk | tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py |
| 48 | ➖ (nincs billentyű) | Visszatérés a könyvtárnézetbe; a C forrás Esc-kötése | Keys=Keys.onEscapePressed → viewerMenuBackToLibrary út | **megvan és működik** | Néző; aktív szerkesztőművelet előbb megszakad; szövegfókuszban nem zár | tests/app/qml_functional/test_viewer_escape_key_4462.py, tests/app/qml_functional/test_viewer_escape_666.py |

A 22., 26. és 37. sor a keymap-komment/rekesz eltérését rögzíti, nem hibás mai működést. A 39. sor önálló hiány; a 42–44. és 47. sor tisztázandó marad. A #4398 valós QTest.keyClick próbája mind az 54 QML Shortcutot keresőmező-fókusszal ellenőrzi, a paritásőr pedig a 48 eredeti keymap-rekeszt és a QML-horgonyokat tartja számon. A konkrét műveletpróbákat a sorokban hivatkozott meglévő tesztek végzik.

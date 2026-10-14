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

### A NÉZŐ ága — a binárisból kiolvasva, nálunk követi (#4621, 2026-10-11)

A `0x9c9a` diszpécser-kezelője (`0x005cbaef`) felülettől függetlenül a
`0x005c9b00(ui, !Shift, 1, 1)`-et hívja, és a néző helyi menüje is a
`CThumbUI`-é (`0x00595fe0`, vtábla `0x00c906f4`). A nézetfüggés tehát a
nézőre **ugyanúgy** érvényes: albumból megnyitott képen a `Ctrl+Delete`
**eltávolít az albumból** („Elemek eltávolítása” megerősítéssel), mappában
Lomtárba tesz, `Shift`-tel véglegesen töröl; a néző helyi menüjének felirata
is ugyanezen a feltételen vált; nálunk mindhárom néző-belépő a közös elágazáson megy át. Részletek és címek:
`ui-audit-context-menus.md` **D.7**.

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

Kimaradt a PicasaPyból (2026-10-13 állapot): `Ctrl+6`, `Ctrl+8`, `Ctrl+G`,
`Ctrl+Shift+L`, `Ctrl+Shift+U`, `Ctrl+Shift+Y`, `Ctrl+F9`. Az eredeti ágak
hatása a #4643 mérésével részben feltárt; a mai bekötési irányt és a nyitott
részeket a **10.22** rögzíti. **Helyesbítés:** a bal szerkesztőfiók nálunk
létezik (`PhotoViewer.qml`: `editorControlsVisible`, `toggle_left_drawer`;
`PicasaMenuBar.qml`: „Show Edit Controls”). A Ctrl+9 kötés időközben bekerült
(#4696, 0.9.46), az F5 is (#4697) — lásd 10.23.
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
| **F5** | `0x005e6869` | időbélyeg- és állapotfrissítés, `[adatobjektum+0x166] = 1` frissítési kérés, majd kereső-/nézeti frissítés (`0x0065b840`; 10.22) a lánc a lemezt olvasó `0x009a5fa0`-ig megy (10.26) |
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
| `Ctrl+Alt` (VK `0x12`) | `0x005e65dc`: csak `[panel+0xe78]` engedélyező jelző és érvényes `[panel+0xe70]` azonosító mellett hívja a `0x00571a80`-at. A teljes `.text` pásztázás az `+0xe78` egyetlen olvasójaként ezt a kaput találta. A cél létrehozza/újrahasználja a `[panel+0x31a8]` gyerekobjektumot, beállítja a bélyegkép-azonosítót, majd a `0x00774d60` frissíti annak geometriáját. A VK `0x12` állapotát a `0x00774d60` olvassa (nem a `0x00571a80`, ahogy az `osszefoglalo.md` #26 írja), és onnan kér ablakmegjelenítést és újrarajzolást. A gyerekobjektum egy `PopDisplay` (nem CThumbUI): felugró ablak. Részletek: 10.28. | A `PreviewHandler` külön eseményútja (`0x005c24c0`) szintén a `0x00571a80`-at hívja; a `0x00774cf0` testvér callback listabeli azonosítóváltás után ugyanazt a `0x00774d60` frissítőt hívja. A `0x00774d60` a `GetAsyncKeyState(0x12)` alapján rögzíti az Alt-állapotot, majd `ShowWindow(SW_SHOW)` (`0x00775320`) és `InvalidateRect`/`UpdateWindow` következik, ha a gyerek kliensszélessége > 1024 px. A rajzolás (WM_PAINT) egy úton igazolt. | megerősített (két út); a kép tartalma és az Alt-elengedés útja nyitott — 10.28 |
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

- `0x00571e50` — a [panel+0xdc4] kapcsoló felhasználói hatása: **lezárva a 10.23-ban** (a kapcsoló nem szinkronizálja a kijelölést az előnézettel; a felirat-/törlésállapot-frissítés látható része futásteszt nélkül nyitott).
- `Ghidra-kör kell: 0x00774d60 — a [CThumbUI+0x31a8] gyerekobjektum pontos kirajzolt tartalma és az Alt-állapot [objektum+0xb4] látható következménye. [blokkoló]`
- ✅ Lezárva a 10.28-ban: a Ctrl+Alt (VK `0x12`) hatása a `PopDisplay`-felugró ablak megjelenítése (EnableHover + előtérben + >1024 px mellett). Maradék nyitott pontok: a kép forrása, az Alt-elengedés útja, az EnableHover alapértéke.
- `0x005f89a0` — a Ctrl+F9 eltérési ágának 0 argumentumos célja: **lezárva a 10.23-ban** — nem vált képet; a jelenlegi `[this+0xe64]` kép felirat-/törlésállapotát frissíti, és csak akkor, ha a felirat-mező `+0x2c4` jelzője piszkos.
- A `Ctrl+6` timeslicer felületének futás közbeni állapota és a Ctrl+Shift+Y `overlays/egg` látható animációja: **NINCS MEG**; célzott eredeti-program próba kell.
- A `/`, `,`, `.` esetleges videóvezérlő-hatása: **NINCS MEG**; a fókuszált gyermek eseményfogadójának útját kell követni, a globális kezelőben nincs saját ág.

⚠️ *2026-10-13: elavult — a Ctrl+9 (#4696) és az F5 (#4697) bekötése a 0.9.46
kiadásban megvan, lásd 10.23.*

**Fejlesztési következmény (2026-10-08-as állapot):** a Ctrl+9-hez külön bekötési jegy javasolható:
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

### 10.23 #4643 — második kör (2026-10-13): független kiolvasás, a kódállapot és a maradék nyitott pont

**Kiinduló helyzet.** A jegy (menü-audit, #4317) szerint a Ctrl+9 „nálunk nem létezik”, és a Ctrl+G / F5 hatása ismeretlen. A 10.22 óta két dolog változott: a Ctrl+9 (#4696) és az F5 (#4697) bekötése bekerült a 0.9.46 kiadásba (`ced175cd6`, a `01ccd4e44` beolvasással), a Ctrl+G nincs bekötve.

**Módszer.** (1) A bináris SHA-256-ja `644b7bec…dc96`, ami egyezik az index `meta.json` `binary_sha256` mezőjével; a vizsgált példány `research/copy_Picasa_3_7/Picasa3/Picasa3.exe`. (2) A bájtokat `eszkozok/pe_dis.py`-vel olvastam ki (capstone a `~/picasapy-agent/.venv`-ből; hálózatot nem használtam). (3) A billentyűtábla közvetlenül olvasva: indextábla `0x005e66a4`, ugrótábla `0x005e6614`, a VK `0x0D`-tól indexelve (a 10.1 szerinti elrendezés). (4) Bájt-szintű pásztázás a `.text` és `.rdata` teljes tartalmán (`call`/`jmp rel32` és abszolút 32 bites hivatkozás). A két, egymástól független út minden állításnál külön szerepel. Futtatás nem történt.

| billentyű | 1. út (billentyűtábla / közvetlen kód) | 2. út (független) | hatás | fok |
|---|---|---|---|---|
| **Ctrl+9** | VK `0x39` → index 10 → ugrótábla → `0x005e629f`: `call 0x579330` (őr); `test al,al; je 0x5e65f7`; `mov edx, 0xc7fe30` (`editpanel/toggle_left_drawer`); `call 0x9cd8a0` (kattintás) | menü: a `0x0065ab50` `cmp eax, 0x9d6e` ágon (ID_VIEW_EDIT, „Show Edit Controls”) ugyanaz a `0xc7fe30` + `0x9cd8a0`. A menü-CSV és a `picasa-menu-parancsok-viselkedes.md` 37.3 (menühíd) ugyanezt adja. | **a bal szerkesztőfiók átkapcsolása** (a menüpont és a billentyű ugyanazt az objektumot kattintja) | művelet: **megerősített**; az őr pontos jelentése: **nyitott** (lásd alább) |
| **Ctrl+G** (módosító nélkül) | VK `0x47` → index 17 → `0x005e6518`: `cmp [esp+0x12],0` (Alt); `je 0x5e653a`; `cmp [esp+0x11],0` (Shift); `je 0x5e65f7` → nincs hívás | a Shift-ág (`0x600580`, Ctrl+Shift+G) és az Alt+Shift-ág (`0x57b050`) ugyanezekből a bitekből válik szét (10.22 szerint); a Ctrl+G no-op útja nem hív továbbító-függvényt (a `0x5e65f0`→`0x571a80` hívás csak a VK `0x12` ágban van). | **a kezelő ágában nincs művelet** | a kezelő ágán: **megerősített**; a visszatérési kód után a lánc többi tagja: **nyitott** (lásd alább) |
| **F5** | közvetlen kód: `0x005e6869`: `cmp ax, 0x74`; `mov eax,[edi+0x2c0]`; `call 0x4a46e0` (időbélyeg); `call 0x579480(0,1)`; `mov byte [ecx+0x166], 1`; `call 0x65b840` (nézetfrissítés) | vtábla: a `CThumbUI::vftable` (`0x00c9052c`) 12. slotja (`0x00c9055c`) = `0x005e6710`, a fő kezelő; a billentyűtábla F5-re a közös kilépést adja, tehát az F5 a fő kezelőben él | **a `+0x166` jelző beállítása és a nézet/keresősáv frissítése**; az idle-út (`0x004afcfd`: `cmp byte [esi+0x166],0`) `0x4aae90`-nel frissíti a listát, majd `mov byte [esi+0x166],0` (`0x004afd41`) | **megerősített** (a jelző és a hívások); a teljes lemezrescan: **nem igazolt** (lásd alább) |

**A Ctrl+9 őre (`0x005e629f` előtt).** A `0x579330` három feltételt néz: a `0xd67914` globális jelző nem nulla (`cmp dword [0xd67914], 0`, `0x00579330`); az `editpanel/preview` objektum (sztring `0x00c88a2c`, a `0x009c2fc0` keresése) létezik; és a visszatérés `sete` ⇒ **`[objektum+0x20c] == 0`** (`0x0057934a`–`0x00579354`). Ezt a mai kód `enabled: viewer.visible` feltétele közelíti (lásd a mai kódot), de nem azonos vele. A `0xd67914` jelentése és a `+0x20c` bájt szerepe **nincs megfejtve**: a `.text`-ben a `0xd67914` címre **1712** bájt-hivatkozás van, főleg olvasás, és ezt a kört nem tudta szűkíteni.

**A Ctrl+G közös kilépése.** Minden ág a `0x005e65f7` közös kilépésre fut, amely csak a visszatérési kódot állítja: `[esp+0x24] != 0` ⇒ `0xf4240` (kezelve), különben `0xf4241` (tovább). A 10.13 szerint a kezelőlánc többi tagja ezt a kódot olvassa. Azt, hogy a Ctrl+G a `0xf4241` után a láncban kap-e műveletet, **ebben a körben nem követtem végig**. A Ctrl+9 és az F5 is ugyanerre a kilépésre fut, de a műveletük az ágban megtörténik, ezért nem függ ettől.

**A mai kód (2026-10-13, ez a worktree):**

| billentyű | mai kód | teszt | egyezés a bináris hatásával |
|---|---|---|---|
| Ctrl+9 | `PhotoViewer.qml:213` — `Shortcut { sequence: "Ctrl+9"; enabled: viewer.visible; onActivated: viewer.toggleEditorDrawer() }` (#4696) | `tests/app/qml_functional/test_ctrl9_left_drawer_4696.py` (a könyvtárnézetben nincs hatása, a keresőmező fókusza megmarad) | **egyezik** a művelettel; a feltétel (`viewer.visible`) **nem azonos** a binárisban mért őrrel |
| Ctrl+G | nincs `Shortcut` (`grep` a `src/picasapy/app/` alatt: nulla találat) | — | **egyezik** a no-op ággal (a kezelő ágában nincs művelet) |
| F5 | `Main.qml:1163` — `Shortcut { sequence: "F5"; enabled: … könyvtárnézet …; onActivated: controller.resyncFolder(controller.currentFolder) }` (#4697) | `tests/app/qml_functional/test_f5_konyvtar_frissites_4697.py` (a lemezről törölt és az új fájl is felkerül / eltűnik a keresés után) | **a műveleti irány egyezik** (frissítés); **a lemezszinkron TÖBB**, mint amit a bináris jelzőből igazoltunk (lásd alább) |

**Összegzés (következtetés).**

- **Ctrl+9:** a bináris szerint a bal szerkesztőfiókot kapcsolja, a menüpont és a billentyű ugyanazt az objektumot kattintja. A mai kód ezt bekötötte (#4696). **Nincs külön fejlesztési jegy szükség a bekötésre.** Az őr pontos feltétele nyitott, de a mai kód működése ettől nem változik.
- **F5:** a bináris szerint a `+0x166` frissítési jelzőt állítja, és a nézetet/keresősávot frissíti. A mai kód ezt bekötötte (#4697), és lemezszinkront is végez. **A lemezszinkron ellenőrizetlen a binárisból.** Ha kiderül, hogy az eredeti nem szinkronizál lemezt, a mai viselkedés eltér tőle; ez döntés kérdése, nem bizonyítás.
- **Ctrl+G:** a `0x005e60d0` Ctrl-tábla ágában nincs művelet, és a mai kód sem köti be. ⛔ A lánc 5. tagja (`0x00a53b00`) ezt a billentyűt **előbb** kapja meg, és továbbítja: a hatás a 10.24 szerint **nyitott**, nem „nincs művelet”.

**Nyitott pontok** (nevesítve, a kör nem zárta le őket; sajátok, ezért a munkasorba kerülnek):

- `Ctrl+9 őr`: a `0xd67914` globális jelző és az `editpanel/preview+0x20c` bájt jelentése. Következő lépés: a `0xd67914` íróinak és a `+0x20c` íróinak szűkítése (az 1712 találat szűrése a `cmp`-okról az írásokra), és a két eredmény összevetése a mai `viewer.visible` feltétellel.
- `F5 lemezszinkron`: a `0x0065b840` és a `0x004aae90` mélyebb hívási lánca. Ha van benne lemez-bejárás (`FindFirstFile`/`FindNext` vagy ezek belső burkolója), az igazolja a mai szinkront; ha nincs, a mai eltérés dokumentált. Az indexben nincs közvetlen fájlbejárási import ezekben a függvényekben, de ez az index negatív találata, nem bizonyíték.
- `Ctrl+G lánc`: a `0xf4241` után a kezelőlánc következő tagjai (10.13 szerint `0x00a53b00`, `0x005b2390`) kapnak-e Ctrl+G-t. Ez a mai kódban nem számít (nincs Ctrl+G kötés), az eredeti hatás viszont nincs teljesen kizárva.
- **Kimondva:** a fenti három nyitott pont a kutatói szabály szerint nem zárt állapot. Ebben a körben nem volt bizonyíték-költség-keret mindháromra, és egyiket sem tudtam „LEZÁRVA / BLOKKOLT / HATÓKÖRÖN KÍVÜL” állapotba tenni. Ezt a jelentés is kimondja.

**Bizonyítottsági fok (ez a kör):** Ctrl+9 művelet — megerősített (két út); Ctrl+G no-op a kezelő ágában — megerősített (két út); F5 jelző és hívások — megerősített (két út); Ctrl+9 őr jelentése, F5 lemezszinkron, Ctrl+G lánc — nyitott.

**„Kész, ha” (a jegyhez, mérhető feltételekkel):**

- [x] Ágankénti táblázat (kód + bájt, két úton): 10.23 táblázata.
- [x] A Ctrl+9 és az F5 külön fejlesztési jegy: **nem kell**, mert #4696 és #4697 megvalósult (0.9.46). Ez a jegy-kérdés lezárva.
- [x] A §10.7 elavult mondata javítva; a 10.22 „Fejlesztési következmény” elavultként jelölve.
- [ ] A `0xd67914` és a `+0x20c` jelentése két úton kiolvasva (író- és olvasócímekkel), és a mai `viewer.visible` feltétel ehhez igazítva vagy az eltérés indokolva.
- [ ] Az F5 lemezszinkron igazolva a `0x0065b840` láncán, vagy a mai eltérés nevesítve a jegyben mint döntendő.
- [ ] A Ctrl+G `0xf4241` utáni lánc végigkövetve, vagy nevesítve mint nem vizsgált.

### 10.24 #4643 — harmadik kör (2026-10-13): a három nyitott pont, és egy javított állítás

**Kiinduló helyzet.** A 10.23 három nyitott pontot hagyott: a Ctrl+9 őrének jelentését, az F5 lemezszinkronját és a Ctrl+G lánc többi tagját. Ez a kör mindhárommal foglalkozott, két független úton ahol lehetett.

**Módszer.** (1) Teljes `.text`-pásztázás csupasz capstone-nal, index nélkül (`eszkozok/binaris/paszta.py`, darabolt, memóriakapuval): minden memóriaoperandus, amelynek a címe vagy eltolása a keresett érték; minden `call`/`jmp` célja; minden sztring-hivatkozás (`push`/`mov` immediate). (2) A `functions.csv` alapján a függvénykeretek. (3) A `pe_dis.py` disassembly ugyanazokra a bájtokra. Az xref-index negatív találatait nem használtam bizonyítéknak.

**Ctrl+9 őre (`0x00579330`).** A függvény három feltételt néz, sorrendben:

1. `cmp dword [0xd67914], 0` — a `0xd67914` globális mutató nem nulla;
2. `call 0x9c2fc0` a `"editpanel/preview"` sztringgel (VA `0xc88a2c`) — a találat nem nulla;
3. `cmp byte [obj+0x20c], 0; sete al` — az eredmény a `[obj+0x20c] == 0`.

*A `0xd67914` jelentése (megerősített, két út):*
- **Mi:** a Picasa UI-gyökér / név szerinti objektumregiszter singletonja. A `0x9c2fc0` egy sztring-kulcsú hash-keresés ezen: a bucket-tömb a `[reg+0xc]`-n, a bucket-szám a `[reg+4]`-en áll (`0x409df0` a moduló), a láncot a `0x6f9890` sztring-összehasonlítással járja.
- **Élettartam, az összes `.text`-hivatkozásból:** a teljes pásztázás 1712 utasítás-operandust talált a `0xd67914`-re, ebből **pontosan kettő író** (`W`). `0x009c3a36` (`0x9c3860`, a `[0xd67910]` számláló 0→1 átmenetén) állítja be az objektumot; `0x009c3bae` (`0x9c3a80`, a számláló 1→0 átmenetén, a `0x97caf0` hívás után) nullázza. A többi 1710 hivatkozás olvasás. Ezt a kettőt a `0x9c3860`/`0x9c3a80` `jne` ágai szabják meg, nem becslés.
- **Következtetés:** az őr első tagja azt nézi, hogy a regiszter **épp élő-e** (nem tört le). Ez nem nézetfüggő feltétel.

*A `[obj+0x20c]` bájt (megerősített, két út):*
- **Első út (teljes pásztázás):** minden memóriaoperandus, amelynek az eltolása `0x20c` (bármilyen bázisregiszterrel, így a `[reg+0x20c]` és a `[reg+ecx*k+0x20c]` alakok is), **két írás** a teljes `.text`-ben: `0x00c1762a` (`mov [eax+0x20c], ecx`, a `0x00c175d6` függvényben) és `0x00c17812` (`and dword [eax+0x20c], 0`, a `CallCatchBlock` `0x00c17771` kivételkezelő ágában).
- **Második út (a két író kontextusa):** mindkettő a `0xbf0583` hívása után dolgozik, és az a függvény az indexben `__getptd` (az MSVC CRT szálankénti adatblokkja). A `0x00c175d6` egy MSVC C++-kivétel-kódot (`0xe06d7363`, `0x19930520`) ellenőriz, és a szálblokk `+0x20c` mezőjét 1-re állítja; a `CallCatchBlock` visszaállítja 0-ra. **Ezek tehát nem az `editpanel/preview` objektumot írják.**
- **Következtetés:** az `editpanel/preview` objektumán a kód **nem írja** a `+0x20c` bájtot. Ha az objektum létrehozásakor nullázódik (a konstruktor vagy a memória-inicializálás), az őr ettől függetlenül igaz. Ez a nullázás **nincs igazolva**: a konstruktort nem találtam meg. Ezért a `+0x20c` jelentése (a „0 = engedélyezett” értelmezésen túl) **nyitott**.
- **Eltérés a mai kódtól:** a mai `enabled: viewer.visible` feltétel a nézet láthatóságától függ. A binárisban mért őrben nincs ilyen feltétel: ott a regiszter élése és a preview-objektum léte számít, plusz a `+0x20c` bájt. Így a két feltétel eltér: a bináris szerint a fiók átkapcsolható lehet a könyvtárnézetből is, ha a preview-objektum létezik. Ezt nem mértük, mert a könyvtárnézetben a preview-objektum léte nincs igazolva. Ez döntés kérdése, ha a konstruktor-nullázás nem igazolódik.

**F5 lemezszinkronja (`0x0065b840`, `0x004aae90`) — nyitott, de szűkebb.** ⛔ A következő három pont (a mutató-táblák, a „nem oldható fel” és a „3 ugrásig nincs enum”) **a 10.26 szerint elavult**: a táblák feloldva, a lemezbejárás a `0x009a5fa0`-ban megerősített, a nyitott kapuk a 10.26 5. pontjában vannak.

- **Közvetlen hívási lánc (megerősített, a pásztázott `call`-okból):** az F5 kezelője (`0x005e6869`) `call 0x65b840`; a `0x65b840` közvetlen hívása `0x662b20`; onnan `0x67d020` → `0x66f470` → `0x66fae0` → `0x66f810` → **`0x9a5fa0`**.
- **A `0x9a5fa0` egy `"<útvonal>\*.*"` mintát épít:** a `"*.*"` sztring (VA `0xc88d6c`) három helyen hivatkozott (`0x520bce`, `0x9a600b`, `0xa61d12`); a láncban csak a `0x9a600b` (`push 0xc88d6c`, a `0x9a5fa0` függvényben) van, így az F5 útjában lévő, mintát építő függvény ez.
- **Ami nincs igazolva:** a `0x9a5fa0` közvetlen hívásai (`0x401000`, `0x408760`, `0x40eb10`, `0x4139e0`, `0x5c2100`, `0x69d7f0`, `0x97c810`, `0x97caf0`, `0x985af0`, `0x985ff0`, `0x9a51b0`, `0x9a5210`, `0xbef10a`) 3 ugrásig **nem érnek el** FindFirstFile/FindNextFile/SHFileOperation-t. Ugyanakkor a `0x9a5fa0` számos hívása **mutató-táblán** keresztül megy: `call dword [0xc40284]`, `[0xc4055c]`, `[0xc402a8]`, `[0xc40298]`, `[0xc402d0]`, `[0xc4025c]`, `[0xc408fc]`. Ezek célját nem tudtam feloldani: a táblák értékei nem igazodnak utasításhatárra, tehát nem egyszerű függvénymutatók. A 6 ugrásos körben 1670 (a 0x65b840-nél) és 147 (a 0x4aae90-nél) ilyen nem követett hívás van.
- **Következtetés:** a `"\*.*"` minta épülése erős jel arra, hogy az F5 könyvtárat olvas, de ez **nem bizonyítja a lemezbejárást**. A bizonyítás a mutató-táblák célfüggvényének feloldása; amíg az nincs meg, az F5 lemezszinkron **nyitott**. A 10.23 „az indexben nincs fájlbejárási import” megállapítása index-negatív volt, ezért nem bizonyíték.

**Ctrl+G — a 10.23 állítása javítva.** ⛔ A 10.23 („a kezelő ágában nincs művelet”) a `0x005e60d0` Ctrl-tábla ágára igaz, de a lánc sorrendje miatt **a Ctrl+G nem ér el oda először**:

1. A `0x005e67e5` a `0x005b2390`-et hívja (a #4 tag, csak `[panel+0xccc]` esetén; a G-kódot nem vizsgálja, megerősítve).
2. A `0x005e67f4` a `0x00a53b00`-t hívja (a #5 tag, **mindig**). Ennek a belépésénél: `cmp dword [eax+0x20], 0` (nem nulla ⇒ `0xf4241`), és `cmp dword [0xd67858], 0` (nem nulla ⇒ `0xf4240`, kezeltként, művelet nélkül). A kulcskód-ág a `0x00a53b63`-tól egy VK-indexelt táblából ugrik (`[0xa53ba8]`, bájt-index `[0xa53bb4 + VK-8]`); a VK `0x47` (G) és `0x09` (Tab) ugyanazt az ágat kapja (`0xa53b8a`).
3. A `0xa53b8a` ágban, ha a `[eax+0x10]` 4-es bit (Ctrl) be van állítva, és a VK `0x41`–`0x5a` (betű) közé esik, ugrik a `0xa53b7d`-re: `call 0xa582f0`. **Ez a Ctrl+betű továbbítás.** A `0xa582f0` egy billentyű-eseményt épít (`0x9dd770` konstruktor, a vtábla `0xc8b4b0`), majd:
   - `[ebp+0x150]` objektum: `call 0x9e4630`; ha `0xf4240` (kezelt), visszatér kezeltként;
   - `[ebp+0x15c]` (az aktív nézet): `call dword [vtábla+0x74]` (virtuális billentyűkezelő), és a gyermeklista (`[ebp+0x164]`, darabszám `[ebp+0x168]`) elemeire `call 0x9e42b0`. Ha `0xf4240` jön vissza, kezeltként zár.
4. Csak ha mindez `0xf4241`-et ad (a `0x005e67f4` után `0xf4240`/`0xf4246` nélkül), folytatódik a `0x005e680f`: `test al,4` (Ctrl) ⇒ `0x005e69cc`, a 10.13 szerinti #7 tag, a `0x005e60d0` tábla (a `0x005e69cc` belsejét nem néztem végig).

**Következtetés Ctrl+G-re:** a hatás **nem** a 0x5e60d0 Ctrl-táblából dől el, hanem a 3. lépés virtuális billentyűkezelőjéből (a `[ebp+0x15c]` nézet vtábla `+0x74` slotja, és a gyermekei). Ennek a célfüggvénye **nincs feloldva**; ezért a Ctrl+G hatása **nyitott**.

**Másik út, ami NEM dönt:** a `picasa-menu-parancsok.csv` és a `referencia/` alatti adatok közt nincs `Ctrl+G` gyorsbillentyű-definíció (nulla találat). Ez arra utal, hogy nincs menüparancs, amely a Ctrl+G-t kötné, de a billentyű a nézet virtuális kezelőjében is végződhet, ezért ez önmagában nem bizonyíték.

**Bizonyítottsági fok (ez a kör):**

| állítás | út 1 | út 2 | fok |
|---|---|---|---|
| `0xd67914` = élő UI-regiszter, két író (0→1, 1→0) | teljes `.text`-pásztázás (W-szűrés) | a `0x9c3860`/`0x9c3a80` `jne`-ágai és a `0xd67910` számláló | **megerősített** |
| `[obj+0x20c]`-t a preview-objektum nem írja | teljes pásztázás: 2 író, mindkettő `__getptd` kontextus | a két író függvénykerete (`0xc175d6`, `CallCatchBlock`) | **megerősített** (a *preview-objektumra* vonatkozóan); a konstruktor-nullázás **nyitott** |
| F5 hívási lánca `0x65b840` → `0x9a5fa0` (`\*.*` minta) | a `call` gráf pásztázása, 7 lépés | a `"*.*"` sztring-hivatkozásai (3 db) | **megerősített** |
| F5 tényleges lemezbejárása | a 3 ugrásos körben nincs közvetlen enum-import | a mutató-táblák (`[0xc40284]` stb.) **nem oldhatók fel** | **nyitott** |
| Ctrl+G: a Ctrl-tábla (`0x5e60d0`) ágában nincs művelet | a `0x5e60d0` VK-ágainak kiolvasása | — | **megerősített**, de csak erre az ágra |
| Ctrl+G: a láncban kap-e műveletet | a 3. lépés vtábla `+0x74` és gyermekei | — | **nyitott** |

**Mai kód (változatlan ebben a körben):** Ctrl+9 (`PhotoViewer.qml:213`, `viewer.visible` feltétellel) és F5 (`Main.qml:1163`) bekötve (#4696, #4697); Ctrl+G nincs bekötve.

**Nyitott pontok (munkasorba):**

- `Ctrl+9 konstruktor`: az `editpanel/preview` objektum konstruktorának megtalálása, és annak igazolása, hogy a `+0x20c` nullázódik. Ha igen, a bináris őr „a preview létezik és él” szintre egyszerűsödik; ha nem, a `+0x20c` jelentése nyitott.
- `F5 mutató-táblák`: a `[0xc40284]`, `[0xc4055c]`, `[0xc402a8]`, `[0xc40298]`, `[0xc402d0]`, `[0xc4025c]`, `[0xc408fc]` célfüggvényeinek feloldása (az `.rdata` táblák szerkezetének igazolásával), majd a `0x9a5fa0` körének enum-hívás-kereséssel. Ha a tábla célja `FindFirstFile*`/`FindNextFile`, a lemezszinkron igazolt.
- `Ctrl+G nézet-kezelő`: a `[ebp+0x15c]` nézet vtábla `+0x74` slotjának célfüggvénye, és a `0x9e42b0` gyermekkezelő. Ha ez `0xf4240`-et ad Ctrl+G-re, a hatás megvan; ha `0xf4241`, a 0x5e60d0 ág is végigfut.
- `#5 flag`: a `[0xd67858]` és a `[eax+0x20]` jelentése (a #5 tag korai kilépése).

**Kész, ha (a jegyhez, mérhető feltételekkel):**

- [x] A `0xd67914` élettartama és a név szerinti keresés két úton igazolva (10.24).
- [x] A `[obj+0x20c]` írói teljesen felsorolva, és elkülönítve az `__getptd` írásaitól (10.24).
- [ ] A preview-objektum konstruktora és a `+0x20c` nullázása igazolva, vagy a bináris őr eltérése a mai `viewer.visible` feltételtől döntésként nevesítve.
- [ ] Az F5 mutató-táblái feloldva, és a lemezbejárás igazolva vagy kizárva.
- [ ] A Ctrl+G `[ebp+0x15c]` nézet-kezelője feloldva (vtábla +0x74 és `0x9e42b0`), vagy a Ctrl+G hatása nevesítve „nem vizsgált”.
- [x] A 10.23 Ctrl+G „no-op” állítása javítva; a 10.23 Ctrl+G mondata a 10.24-re hivatkozik. (A 10.7 nem módosult, mert ott a Ctrl+G „kimaradt” a mai kódra vonatkozik, nem a binárisra.)

### 10.25 #4698 — a Ctrl+F9 `[panel+0xdc4]` jelzőjének felhasználói hatása (2026-10-13)

**Kérdés:** ki olvassa a jelzőt, és mit kapcsol a felületen? A kiindulás a
10.22 Ctrl+F9 sora és a két „Ghidra-kör kell” nyitott tétel volt.

**Módszer.** (1) A teljes `.text` helyett a bináris-index 20 607 függvénytörzsét
söpörtem végig `capstone`-nal (2 556 882 utasítás), és a `[reg+0xdc4]`,
illetve `[reg+0xe64]` operandusokat gyűjtöttem; a lineáris `.text`-söprés
a `0x0050d53d`-nál kiesett, ezért azt nem használtam. (2) A
`referencia/ghidra-koteg-2026-10-12/00571e50.c` dekompilált kódját
összevetettem az utasításszintű olvasatokkal. (3) A vtable-slotokat és az
IAT-címkéket a PE-fájlból olvastam ki. Futtatás nem történt.

**Lépésenkénti bizonyíték**

| # | Hely | Mit mutat | Független út | Fok |
|---|---|---|---|---|
| 1 | `0x005e61de`–`0x005e61f1` | A billentyűkód-index `vk-0xd`; a `0x78` (F9) indexe `0x6b`, a bájttábla `0x5e66a4+0x6b` = 34, a `0x5e6614` ugrótábla 34. bejegyzése `0x005e6329`. (A F8 `0x005e631d`, a F10 nem ide tartozik.) | a PE-ből számolva (`pefile` + bájttábla); a 10.22 táblázatával egyezik | megerősített |
| 2 | `0x005e6168`–`0x005e6181` | A `[esi+0x10]` módosító-bájt 4-es bitje nélkül a `jle` kilép `0x005e6603`-ba; így F9 csak ezzel a bittel jut el a jelzőig. A bit jelentését (Ctrl) **nem** igazoltam külön. | utasításszint | feltételes |
| 3 | `0x005e6329`–`0x005e6333` | `cmp [ebp+0xdc4],0; sete cl; mov [ebp+0xdc4],cl` — a jelző 0/1 közt billen. | a függvénytörzs-söprés: ez a 2 írás/olvasás egyike | megerősített |
| 4 | `0x005643eb`, `0x00564b2e` | Az ebx=0 (`0x005643eb`), majd `mov [ebp+0xdc4],bl` → alaphelyzet 0. | utasításszint | megerősített |
| 5 | `0x00572078` (fv. `0x00571e50`) | `cmp [ebx+0xdc4],0` — az egyetlen olvasó a `0x00571e50`-ben. | **Ghidra** `00571e50.c` 125. sora (`param_1[0x371]`) **és** capstone-söprés: két külön eszköz ugyanazt adja | megerősített |
| 6 | `0x00571e50` feltételei | `editpanel/preview` létezik (`0x009c2fc0`), `[+0x20c]==0`; a `0x006cfe10(this+0x2bc+0x346c)` érték ≠ `[this+0xe64]`. | Ghidra + asm | megerősített (de lásd nyitott) |
| 7 | `0x005720af`–`0x005720c0` | `[this+0x2a4]` vtable `+0x2c` hívása, argumentum `push 0`. A vtable `0xc90754` (a konstruktor utolsó `+0x2a4` írása `0x005645da`), a `+0x2c` slot a `0x00578dc0`. | a slotot a PE-fájlból olvastam ki | megerősített |
| 8 | `0x00578dc0` | `[ebp+8]==0` ágon `0x00578e79`: `call 0x005f89a0`. Az argumentum nem nulla ága hívja a `0x005d1300`-at (képváltás) — ezt a 0 argumentumú hívás **nem** éri el. | utasításszint | megerősített |
| 9 | `0x005f89a0` | Csak ha `editpanel/preview` látszik; a `editpanel/caption` (`0x00c07db2`) objektum `[+0x2c4]` jelzőjét kell hogy legyen; ha igen: törli, majd a `[this+0x2bc]+0x48` vtable `+0x50` hívásával a `[this+0xe64]` kép rekordját kéri, `editpanel/captiontrash` állapotot állít, a `[this+0x2ac]+8` callbacket a `[this+0xe64]`-gyel hívja, végül `0x00579480(1,0)`. **Nem ír `[this+0xe64]`-et.** | utasításszint | megerősített (a callback célja nyitott) |
| 10 | a `+0xe64` írói | A teljes függvénytörzs-söprésben a `[reg+0xe64]` írása csak két helyen van: a konstruktor (`0x00564cc7`) és `0x005e8c2d` (`0x005e8a70`). A `0x005e8a70` a képváltó út; a 10.22-ben ez már `feltételes` volt. | függvénytörzs-söprés | megerősített |

**Következtetés.** A Ctrl+F9 nem szinkronizálja a kijelölést az előnézettel.
A jelző egy kapcsoló: bekapcsolt állapotban a felület idle-frissítése minden
ciklusban, amikor a kijelölt-azonosító eltér a jelenleg előnézetben lévő kép
indexétől, meghívja a `0x005f89a0`-t. Az a felirat-mező piszkos jelzőjére
frissíti a jelenlegi előnézeti kép felirat- és törlésállapotát. A kép
váltása ezen az úton **nem** történik: a hívás 0 argumentummal megy, a
képváltó `0x005d1300` nem fut, és a `[this+0xe64]` nem íródik. A kapcsoló
0 állásában az eltérési frissítés kimarad.

**Fok:** a kapcsoló, a hívási lánc és az, hogy nem vált képet — **megerősített**
(két független eszköz). A látható felirat-állapot-változás, és az, hogy a
piszkos jelző mikor áll be — **feltételes**, futtatás nélkül nem mérhető.

**Nyitott:**

- A `0x006cfe10` visszatérési értéke: a `[obj+0x60]`/`[obj+0x68]` ágon a `[[obj+0x68]+0x3c]`, különben a `GetCurrentThreadId` érték. A „kijelölt-azonosító” jelentése ebből **nem igazolt**; a `0x006cfe10` zárolt, újrabelépő állapotolvasó (`EnterCriticalSection`/`LeaveCriticalSection`), nem egyszerű kijelölés-lekérdezés. Ha az ágon a szálazonosító jön vissza, az eltérés minden ciklusban fennáll — ez a feltétel-ág is futtatást kíván.
- A `[this+0x2ac]+8` callback célja (a konstruktor végső `+0x2ac` értéke `0xc907ac`) és a `0x00c07db2` (`editpanel/caption`) objektum `+0x2c4` írói: **nyitott**.
- A `0x005e8a70` hívóinak billentyű-hozzárendelése (`0x005e625e`, `0x005e6279` ágak): **nyitott** — ez a képváltó út gazdája.
- A módosító-bit 4 (`[esi+0x10]`) név szerinti megfelelése (Ctrl): **nem igazolt külön**; a 10.22 szerinti Ctrl-hozzárendelés erre épül.
- A látható felirat-/törlésállapot-változás eredeti Picasán való futtatása: **NINCS MEG**; célzott próba kell.
- Az `editpanel/captiontrash` állapot szöveges/vizuális jelentése a QML-oldalon nincs leltározva.

**Gyorsbillentyű-kötés (kódban).** A `src/picasapy/app/` alatt nincs `Ctrl+F9`
kötés (10.22). A binárisból igazolt hatás nem ad elég bizonyítékot egy
felhasználói funkcióhoz: a kapcsoló csak a felirat-frissítés idle-útját
szabályozza. **Fejlesztői al-jegy nem javasolt** a futásteszt és a
`0x005f89a0` callback-célja nélkül.

### 10.31 #4698 — harmadik kör: a Ctrl+F9 jelzőjének felhasználói hatása, és a 0x04 bit forrása (2026-10-13)

**Kérdés:** (1) a `[panel+0xdc4]` jelzőt a Ctrl+F9 billenti; a jelzőt olvasó `0x00572078` kapuban a „0x04 bit” a Ctrl-állapot-e? (2) a `0x00571e50` frissítő mit rajzol/rendez újra a jelző igaz és hamis ágán?

**Helyesbítés a jegy premisszájára.** A `0x00572078` NEM bitteszt. Az `cmp byte ptr [ebx+0xdc4], 0` egy bájt-összehasonlítás (0/1). A „0x04 bit” a billentyű-eseményobjektum `[+0x10]` módosító-bájtjában van (`test byte ptr [esi+0x10], 4` a `0x005e6178`-nál), a két mező külön.

**Módszer.** Minimális PE-olvasó + `capstone` (a venvben nincs `pefile`, csomagot nem telepítettem). Az import-slotokat a `.rdata`-ból oldottam fel (`call dword ptr [slot]`), és a `binary-index/imports.csv`-vel ellenőriztem. Futtatás nem történt.

**Lépésenkénti bizonyíték**

| # | Hely | Mit mutat | Fok |
|---|---|---|---|
| 1 | `0x005e6329`–`0x005e6333` | `cmp byte [ebp+0xdc4],0; sete cl; mov [ebp+0xdc4],cl` — a jelző billen. | megerősített |
| 2 | `0x005e6178`–`0x005e6181` | F9 (`0x78`) csak akkor jut a `0x005e6329`-ig, ha `test byte [esi+0x10],4` igaz (`jle 0x5e6603` kilép). | megerősített |
| 3 | `0x005e69cf` (fv. `0x005e6710` láncán belül) | `call 0x005e60d0` a `Ctrl`-ágon; a `0x005e60d0` a `[esi+0x10]&4`-ot vizsgálja. | megerősített |
| 4 | `0x005e6756` | `push 0x10; call [0xc406f8]` = `GetAsyncKeyState(VK_SHIFT)` a láncban (Shift-csempe, 10.12). **Nem** Ctrl. | megerősített |
| 5 | `0x00a53b8a` | `test byte [eax+0x10],4` — a `0x00a53b00` lánc betű-ága csak bit 4 mellett továbbít (Ctrl+A…Z). A bit jelentését a kód Ctrl-ként használja. | feltételes (a forrás nincs igazolva) |
| 6 | `0x006fe3fa` (fv. `0x006fe3e0`) | `GetKeyState(VK_CONTROL=0x11)` — **a Ctrl-lekérdezés egyetlen IAT-hívása**, de a `0x006fe3e0` másik függvény (`WM_KEYDOWN` + `0x4e`, `WM_SYSCOMMAND` + `0xf060`), nem az eseményobjektum-építő. | megerősített (a függvény másik) |
| 7 | `0x005726a8`–`0x005726c3` (fv. `0x00571e50`) | `push 0x17; call [0xc40840]` = `GetSystemMetrics(SM_MOUSEPRESENT)`, majd `GetAsyncKeyState(VK 1 vagy 0)` (`VK_LBUTTON`). Ha az egér-gomb le van nyomva (`test ax,0x8000`), a `0x572738`-ra ugrik. **Nem Ctrl.** | megerősített |
| 8 | `0x00572078`–`0x005720c0` | `dc4 != 0` ágon: ha az `editpanel/preview` létezik és `[+0x20c]==0`, a `0x006cfe10(this+0x2bc+0x346c)` ≠ `-1` és ≠ `[this+0xe64]` esetén `[this+0x2a4]` vtable `+0x2c` hívása, arg. 0. | megerősített (a feltételek) |
| 9 | `0x006cfe10` | Újrabelépő zár-segéd: `GetCurrentThreadId` (`[0xc40284]` → `0x921a3e`) + `EnterCriticalSection` (`[0xc4055c]` → `0x921b04`). Visszatérés: `[[obj+0x68]+0x3c]`, ha `[obj+0x60]` és `[obj+0x68]` nem nulla; különben a szál-azonosító. **Nem kijelölés-lekérdezés.** | megerősített |
| 10 | `0x005f89a0` (a `+0x2c` slot célja, 10.25 szerint) | Ha az `editpanel/preview` látszik és a `caption` objektum `[+0x2c4]` jelzője be van állítva: törli, a `[this+0x2bc]` vtable-jével frissíti a `[this+0xe64]` képrekordot, a `[this+0x2ac]+8` callbacket `[this+0xe64]`-gyel hívja, végül `0x00579480`. **Nem ír `[this+0xe64]`-et, nem hív `0x005d1300`-at (képváltás).** | megerősített (utasításszint) |

**Következtetés (1).** A 0x04 bit a billentyű-eseményobjektum módosító-bájtjának bitje, és a billentyűlánc Ctrl-jelentéssel használja (5. tétel). Hogy a bitet ki állítja be, a binárisból **nem igazoltam**. Két eszköz is kizárja a 0x6fe3fa-t és a 0x571e50 `GetAsyncKeyState`-jét (6. és 7. tétel): egyik sem az eseményobjektum építője.

**Következtetés (2).** A Ctrl+F9 nem szinkronizálja a kijelölést az előnézettel (a 10.25 eredményét megerősítem). A jelző egy kapcsoló a `0x00571e50` idle-frissítőben: bekapcsolva, az előnézet felirat-/törlésállapotát frissíti a `0x005f89a0`, és **nem vált képet**. A kijelölés-azonosító (`0x006cfe10`) jelentése ettől független: a visszatérés vagy szál-azonosító, vagy egy `[obj+0x68]` mező. Ha szál-azonosító, a feltétel minden ciklusban igaz, és a frissítés minden tick-ben lefut — ez az ág nincs lemérve.

**Fok:** a kapcsoló, a hívási lánc és a „nem vált képet” állítás — **megerősített** (két független eszköz: utasításszintű olvasat és a slot-feloldás). A látható felirat-/törlésállapot-változás, a gyakoriság, és a `0x006cfe10` visszatérési értékének jelentése — **feltételes / NYITOTT**.

**Nyitott (NEM LEZÁRT, a mérleg szerint):**

1. **N1 — a 0x04 bit forrása.** Kell: az eseményobjektumot építő függvény (a `0x005e6710` láncának hívója; a `0x00a582f0` továbbító előtte). Próba: `mov byte ptr [reg+0x10], …` írások a `.text`-ben, és a VK 0x11 lekérdezés minden helye (`push 0x11` + `call [0xc406f8]` — a 2026-10-13-i szűrés 32 találatot adott, ezeket nem néztem végig). **Blokkoló:** nincs; olcsó, de nem fért bele a körbe.
2. **N2 — a `[[obj+0x68]+0x3c]` jelentése.** Kell: a `[obj+0x68]` objektum típusa és a `+0x3c` mező írói. Ettől dől el, hogy a 0x572078 feltétele mikor igaz (kijelölés-eltérés vs. folyamatos).
3. **N3 — a látható hatás.** Kell: Picasa 3.9 (angol, Wine) futtatása Colab-gépen, a Ctrl+F9 kétszer, a felirat-/törlésállapot képernyőképe. Ez `picasa-colab-jobs` feladat (`tipus:…`), nem ebből a körből.

**Amit KIZÁRTAM:**
- a `0x00572078` nem bitteszt (a 0/1 bájt-kapu);
- a `0x006fe3fa` GetKeyState(VK_CONTROL) nem az eseményépítő (másik függvény);
- a `0x00571e50` GetAsyncKeyState-je nem Ctrl (VK_LBUTTON, egérgomb-kapu);
- a `0x006cfe10` nem kijelölés-lekérdezés (zár-segéd, GetCurrentThreadId).

**Kész, ha** (csak ha N1–N3 után megvalósítandó lesz; most NEM javasolt fejlesztői al-jegy):
- [ ] a Colab-futtatásban a Ctrl+F9 után az előnézet felirat-/törlésállapota változik (kép vs. kép), kétszer mérve;
- [ ] N1: a 0x04 bit beállító útja megnevezve, címmel;
- [ ] N2: a `0x006cfe10` visszatérési érték jelentése igazolva, címmel.

### 10.26 #4643 — negyedik kör (2026-10-13): az F5 lemezbejárása

**Kiinduló helyzet.** A 10.24 az F5 lemezszinkronját nyitottnak hagyta, mert a `0x9a5fa0` hívásainak mutató-táblái (`[0xc40284]`, `[0xc4055c]`, `[0xc402a8]`, `[0xc40298]`, `[0xc402d0]`, `[0xc4025c]`, `[0xc408fc]`, és a `[0xd694c4]`/`[0xd694c8]`/`[0xd694cc]`) nem voltak feloldva.

> ⛔ **HELYESBÍTÉS a 10.24-hez.** A 10.24 „a táblák értékei nem igazodnak utasításhatárra, tehát nem egyszerű függvénymutatók” megállapítása **téves** volt. A `.rdata`-beli érték a betöltés *előtti* IAT-tartalom (a loader felülírja), nem függvénycím. A nevet az import-könyvtárból kell venni, nem a fájl bájtjából. A 10.24 „3 ugrásig nincs FindFirstFile” állítása ezért index-negatív volt, és nem bizonyíték.

**Módszer.** (1) A `.rdata` IAT-bejegyzéseket az import-könyvtár (`IMAGE_IMPORT_DESCRIPTOR`, `OriginalFirstThunk` neve) alapján oldottuk fel, nem a fájlbeli értékből. (2) A futásidőben töltött `.data`-slotok íróit a `.text` teljes capstone-pásztázásával kerestük (`eszkozok/binaris/paszta.py`, memóriakapuval), `mov`/`call` operandusra szűrve. (3) A hívási láncot direkt `CALL`-ok szerint, utasításonként ellenőriztük, és a `functions`/`xrefs` index csak kiegészítő volt. (4) A kézzel dekódolt szakaszok `pe_dis.py`-n át olvastak.

**1. A hét IAT-slot (megerősített, két út: import-könyvtár és index-`imports`).**

| slot (VA) | API |
|---|---|
| `0x00c40284` | `KERNEL32!GetCurrentThreadId` |
| `0x00c4055c` | `KERNEL32!EnterCriticalSection` |
| `0x00c402a8` | `KERNEL32!LeaveCriticalSection` |
| `0x00c40298` | `KERNEL32!QueryPerformanceCounter` |
| `0x00c402d0` | `KERNEL32!Sleep` |
| `0x00c4025c` | `KERNEL32!GetLastError` |
| `0x00c408fc` | `USER32!EndPaint` |

A `0x9a5fa0` ezekkel a kritikus szakaszt és az időzítést kezeli (a `GetCurrentThreadId`/`Enter`/`LeaveCriticalSection` párosok), tehát **nem** fájlművelet.

**2. A futásidőben töltött `.data`-slotok (megerősített).** A `[0xd694c4]`, `[0xd694c8]`, `[0xd694cc]` a `.data` virtuális, fájlban nem inicializált része; írójuk **egyedül** a `0x00c326b0` függvény (`0x00c32c2a`–`0x00c32cba`), és mindhárom egy `GetVersion` elágazással dönt (`cmp [0xd6fc58], 0x80000000; jae`):

| slot | NT-ág (`GetVersion` high bit = 0) | 9x-ág (high bit = 1) |
|---|---|---|
| `[0xd694c4]` (keresés kezdete) | `0x009aed50` (UTF-8 → UTF-16, `MultiByteToWideChar` CP 65001, majd `FindFirstFileW`) | `FindFirstFileA` (`0x00c40428`) |
| `[0xd694c8]` (keresés kezdete, kiterjesztett) | `0x009aee90` (ugyanaz, majd `FindFirstFileExW`) | `FindFirstFileExA` (`0x00c404a8`) |
| `[0xd694cc]` (következő elem) | `0x009aeff0` (`FindNextFileW`, `0x00c404b4`) | `FindNextFileA` (`0x00c404bc`) |

**3. Az enumerátor (`0x009a5fa0`, 3608 bájt; megerősített).** Hívásai a `.text`-ből:
- `0x009a6099`: `call [0xd694c4]` — a sima `FindFirstFile*` ág (két argumentum);
- `0x009a6079`: `call [0xd694c8]` — a `FindFirstFileEx*` ág (hat argumentum), csak ha az `arg3 == 0x0040eed0`, és a `[0xd689ec] < 0x80000000` (ezt a jelzőt nem azonosítottuk); egyébként a sima ág fut;
- `0x009a6d4b`: `call [0xd694cc]` — `FindNext*`;
- `0x009a6d5e`: `call [0xc403a8]` — `FindClose`;
- `0x009a60a8`: `GetLastError` hibaágon.

A `0x009a600b` a `"*.*"` sztringet (VA `0x00c88d6c`) fűzi a bemeneti úthoz a `0x00985af0` hívással. Az elválasztó (`\`) beillesztését a `0x00985af0`-ban nem néztem végig.

**4. Az F5 hívási lánca (megerősített, minden hop direkt `CALL`).**

| lépés | hely | cél |
|---|---|---|
| F5 ág | `0x005e6869` (`cmp ax, 0x74`, VK_F5) | |
| flag | `0x005e6892`: `mov byte [obj+0x166], 1` | a frissítési jelző |
| 1 | `0x005e6899` | `0x0065b840` |
| 2 | `0x0065bb1b` | `0x00662b20` |
| 3 | `0x0066315b` | `0x0067d020` |
| 4 | `0x0067d240` | `0x0066f470` |
| 5 | `0x0066f76d` | `0x0066fae0` (feltétel: §5) |
| 6 | `0x0066fba2` | `0x0066f810` (a `0x66fb7d`/`0x66fb84` ugrások is ide érnek) |
| 7 | `0x0066f8b8` | `0x009a5fa0` |

A `0x0066f810` a `0x992ed0` kapuval védi a hívást (`0x0066f88d`): ez attribútum-jellegű lekérdezés (`call [0xd694bc]`, `cmp eax, -1`, `setne`), a `[0xd694bc]` célja **nincs azonosítva**.

**5. Nyitott kapuk (az F5 csak akkor olvas lemezt, ha ezek átmennek).**
- `0x0066f470` → `0x0066fae0` (`0x0066f73e`, `0x0066f768`): az `ebx` a `0x004019b0` visszatérési értéke (`0x0066f6c5`, 211 bájtos segédfüggvény, sztring-objektumot épít). Az F5-nél felvett érték **nem igazolt**.
- `0x00992ed0` → `[0xd694bc]`: a célfüggvény nincs azonosítva; a `setne` eredmény olvasása igazolt.
- A `[obj+0x166]` jelző egyetlen olvasója a `0x004afcfd` (`0x004afcb0`, időzítő-jellegű függvény: `QueryPerformanceCounter` az elején), amely törli (`0x004afd41`). A jelző ~70 helyen íródik. Hogy a `0x004aae90`/`0x004a8a30` ág újraépíti-e a listát, nincs követve.

**Következtetés (F5 lemezszinkron).** A kód **lemezről olvas** az F5 útján: a lánc végén `FindFirstFileW` vagy `FindFirstFileA` (a `GetVersion` szerint), `FindNextFile*`, `FindClose`, a `<bemeneti út>` + `*.*` mintán. Ez a `0x9a5fa0` megerősített tulajdonsága, nem index-következtetés. **Nincs bizonyítva**, hogy minden F5-nél átmegy mind a `0x66f470` ebx-feltétel, mind a `0x992ed0` kapu, és hogy a találatok a listát újraépítik. Ezért a helyes megfogalmazás: „az F5 a mappát a lemezről olvasásra kényszeríti, ha a két kapu átmegy; a kapuk feloldása nyitott”.

**Bizonyítottsági fok (ez a kör):**

| állítás | út 1 | út 2 | fok |
|---|---|---|---|
| hét IAT-slot neve (`KERNEL32`/`USER32`) | import-könyvtár bejárása | index `imports` tábla | **megerősített** |
| `[0xd694c4/c8/cc]` írói: `0x00c326b0` (`GetVersion` ág) | capstone `.text`-pásztázás (`mov`/`call` operandus) | a három író disassembly-je | **megerősített** |
| NT-/9x-wrapperek célja (FindFirst W/ExW/Next W, A-ág) | wrapper disassembly (`call` célok) | IAT-nevek | **megerősített** |
| `0x009a5fa0` hívásai (FindFirst*, FindNext*, FindClose) | `call`-pásztázás `[abs]` operandusokra | IAT-nevek | **megerősített** |
| F5 → `0x009a5fa0` hét direkt hívás | index `xrefs` (CALL-élek) | utasítás-szintű ellenőrzés minden hopnál | **megerősített** |
| `[obj+0x166]=1` az F5 ágban | disassembly `0x005e6892` | a `0x0065b840` argumentumai | **megerősített** |
| `0x66f470 → 0x66fae0` feltétel (`ebx`) | — | — | **nyitott** |
| `[0xd694bc]` (a `0x992ed0` kapu célja) | — | — | **nyitott** |
| F5 után a lista ténylegesen újraépül | — | — | **nyitott** |

**Mai kód:** `Main.qml:1163` az F5-öt köti (#4697). A bináris lemezolvasása és a mai viselkedés egyezése nincs mérve.

**Nyitott pontok (munkasorba):**
- `0x004019b0` visszatérési értéke F5-nél: statikus visszafejtés (sztring-objektum-másoló) vagy futtatás (QEMU-harness, a `kutatoi-allitast-futtatassal-is-ellenorizd` szerint).
- `[0xd694bc]` célja (várhatóan `GetFileAttributes*`) és írói: ugyanaz a `.text`-pásztázás, mint 2. pont.
- A `[obj+0x166]` olvasójának (`0x004afcb0` → `0x004aae90`) hatása: újraépíti-e a listát.
- Dinamikus megerősítés: F5 alatt futó Picasában a `FindFirstFile*` hívásszám > 0 (harness-mérés).

**Kész, ha (F5-re, mérhető):**
- [x] A hét mutató-slot neve két úton igazolva (10.25, 1. pont).
- [x] A `.data`-slotok írói (`0x00c326b0`) és a wrapperek célja igazolva (10.25, 2–3. pont).
- [x] Az F5 → `0x009a5fa0` hívási lánc utasításszinten igazolva (10.25, 4. pont).
- [ ] A `0x66f470` ebx-feltétel és a `0x992ed0` kapu F5-re igazolva (10.25, 5. pont).
- [ ] A `[obj+0x166]` hatása a listára igazolva.
- [ ] Dinamikus mérés: F5 → `FindFirstFile*` hívás a futó Picasában (vagy a kijelentés „csak statikus” jelzéssel marad).

### 10.27 #4643 — ötödik kör (2026-10-13): a Ctrl+G nézetlánca

**Kiinduló helyzet.** A 10.24 szerint a Ctrl+G hatása a `[C+0x15c]` aktív nézet vtábla `+0x74` slotjától és a `0x009e42b0` gyermekkezelőtől függ (`C` = a kulcsszűrő `this`-e, `0x00a582f0` első argumentuma). Ez a kör ezt a láncot követte végig, a 10.26 (F5) mellett.

**Módszer.** (1) A `0x00a53b00`, `0x00a582f0`, `0x009e42b0`, `0x009e4630` és `0x00a576f0` törzsének utasításszintű kiolvasása (capstone, `picasapy-agent` venv). (2) A `+0x15c` mezőt író/olvasó utasítások és a `0x00d67858` globális hivatkozásainak teljes pásztázása, függvényenként (nem index-alapon). (3) A VK `0x47` immediate-ű `cmp`/`sub`/`test` utasításainak teljes pásztázása. (4) A `ytUIDialog`, `CThumbUI`, `SliceUI` vtábla-slotjainak olvasása a vtábla-memóriából (nem a RTTI-listából).

**Láncleírás (a Ctrl+G = VK `0x47`, Ctrl, Shift nélkül, `0x100` keydown).**

1. `0x00a53b00` (a `ytUIDialog` 12. slotja, a `CThumbUI::OnKey` `0x005e6710` és a `SliceUI` `0x0052ece0` ezt hívja): ha `[event+0x20] != 0` ⇒ `0xf4241` (nem kezelt); ha `[0x00d67858] != 0` ⇒ `1000000` (kezelt, a billentyű elnyelődik); egyébként a `default` ág: a Ctrl-bit (`[event+0x10] & 4`) és `0x40 < kód < 0x5b` ⇒ `0x00a582f0`.
2. `0x00a582f0`: ha Shift és Ctrl együtt ⇒ `0xf4241`, nem megy tovább. Egyébként az esemény `0x17` (keydown/char) vagy `0x18` (keyup) típusú ytUIEvent-tet épít (`0x009dd770` konstruktor, vtábla `0x00c8b4b0`), majd:
   - `P = [C+0x150]` (ha nem nulla): `0x009e4630(event)`; ha `0xf4240`, kezelt.
   - `V = [C+0x15c]`: ha `V == 0` ⇒ `return 0`. Ha `[V+0x20e] == 0`: a Ctrl-bit beállítása az eseményen, majd `0x009e42b0(V)`; ha `0xf4240`/`0xf4246` jön vissza, az ág ezzel zár. Különben `V.vtbl[+0x74](V, event, flag)`.
   - Ha még nem kezelt: `C` gyermeklistája (`[C+0x164]`, darabszám `[C+0x168] >> 1`), a `V`-t és a `[child+0x20e] != 0` elemeket kihagyva: elemenként `child.vtbl[+4]()`, `child.vtbl[+0x74](child, event, flag)`, `child.vtbl[+8]()`.
   - `0xf4240` esetén a `0x00a54b70` értesítés (`C`, két egész, egy float), és a kezelt kilépés.
3. `0x009e42b0(this)`: a `[this+0x1a0]` tömb elemeire (darabszám `[this+0x1a4] >> 1`, csak ha ≥ 2) `elem.vtbl[+0xc](elem, arg1, arg2)`; `0xf4240`/`0xf4246`-nál megáll, különben `0xf4241`.
4. `0x00a576f0` (SetActiveView-jelölt, a `ytUIDialog` 31. slotja = `+0x7c`): `[C+0x15c]`-t írja (`mov [edi+0x15c], ebx`, `0x00a57886`), a régi nézetet deaktiválja (`vtbl[+8]`), az újat aktiválja (`vtbl[+4]`, `vtbl[+8]`), közben `0x009e42b0`-t és `vtbl[+0x74]`-et hív. A `0x00a58600` a `[C+0x15c]`-t nullázza.

| állítás | fok |
|---|---|
| A Ctrl+G a `0x00a53b00` default ágán át a `0x00a582f0`-re megy (Ctrl-bit és `0x40 < kód < 0x5b`) | **megerősített**: Ghidra `ghidra-koteg-2026-10-06/00a53b00.c` és a disassembly, két út |
| `0x00a53b00`: `[event+0x20] != 0` ⇒ `0xf4241`; `[0xd67858] != 0` ⇒ `1000000` | **megerősített**: Ghidra-dekompilát és a `0x00a53b13` `cmp dword [0xd67858], 0` |
| `0x00a582f0`: Shift+Ctrl ⇒ `0xf4241`, nincs nézet-továbbítás | **megerősített**: disassembly (`test bl,1` / `test bl,4` / `jle`) |
| `V = [C+0x15c]`, `V.vtbl[+0x74]` hívás, `[V+0x20e]` őr | **megerősített**: disassembly `0x00a5841c`–`0x00a5854e` |
| `0x009e42b0`: gyermektömb `[this+0x1a0]`, `vtbl[+0xc]`, megállás `0xf4240`/`0xf4246`-nál | **megerősített**: disassembly (`0x009e42b0`, 91 bájt) |
| C-gyermeklista (`[C+0x164]`, `[C+0x168]`): `vtbl[+4]`, `[+0x74]`, `[+8]` | **megerősített**: disassembly `0x00a58533`–`0x00a58578` |
| A `ytUIDialog`/`CThumbUI`/`SliceUI` vtábla-slotjai: 12. = kulcsszűrő (`a53b00` / `5e6710` / `52ece0`), 31. = `a576f0` (ytUIDialog, SliceUI), `5fa760` (CThumbUI) | **megerősített**: a vtábla-memória olvasása (`0x00c93f64`, `0x00c9052c`, `0x00c8b97c`), nem csak a RTTI-lista |
| `[C+0x15c]`-t a `0x00a576f0` és a `0x00a58600` írja | **megerősített** a teljes `.text`-pásztázás (84 író a +0x15c-re, függvényenként); a `0x00a58600` hívóit nem néztem végig |
| `[0x00d67858]`: számláló, 35 hivatkozás (≈ 15 növelő/csökkentő pár), olvasói a `0x00a53b00`, `0x00a52890` és más ytUI-függvények | **megerősített** az író/olvasó lista; a számláló *neve* és a pár-szerkezet (pl. `0x00512030`: `sub`, nullánál `IsWindow([0xd6784c])`) **nyitott** |
| `[event+0x20]`: a `0x009dd770` konstruktor 0-ra állítja (`mov [eax+0x20], ecx`, `ecx = 0`) | **megerősített**; a 0-tól eltérő külső írók **nyitottak** |
| VK `0x47` közvetlen összehasonlítása a `.text`-ben: 12 `0x47`-immediate `cmp`/`sub`/`test`; ezek közül a `0x005de810` és `0x0060f1b0` ablaküzenet-kezelő (`case 5`, `0x11`, `0x16`, `0x47` = `WM_WINDOWPOSCHANGED`), a `0x008509d0` és `0x0059c410` típusmező, a `0x00986d40`/`0x00986f00` kisbetű-konverzió (`sub 0x61`, `cmp 0x19`, `sub 0x47`), a `0x004cc9e0` és `0x00ad1040` szövegillesztés | **megerősített** mint *nincs közvetlen VK-0x47 kezelő* a vizsgált hét eset alapján; a `0x0054c540`, `0x007360b0`, `0x007a5c10`, `0x00a99620` **nincs végigolvasva** |
| `P = [C+0x150]` és a `0x009e4630` pre-filter Ctrl+G-re | mechanika **megerősített**; a `P` objektum azonosítása **nyitott** |
| `V.vtbl[+0x74]` célja a könyvtárnézetben | **nyitott**: a `V` osztálya nincs azonosítva |

**Következtetés.** ⛔ **A Ctrl+G könyvtárnézeti hatásáról NEM mondható ki, hogy hatástalan.** A lánc utolsó eleme (`V.vtbl[+0x74]` és a gyermekek kezelői) nem oldható fel, mert az aktív nézet osztálya (`V`) nincs azonosítva. Ami igazolt:

- a Ctrl+G-nek nincs közvetlen kezelője (a vizsgált VK-összehasonlítások között nincs `0x47`);
- minden Ctrl+betű (`0x41`–`0x5a`) ugyanezen a `0x00a582f0` láncon megy, tehát a Ctrl+G hatása csak egy általános (tábla- vagy tartomány-alapú) Ctrl+betű-kezelőből jöhet, és ilyet ebben a körben nem találtunk;
- a `0x00d67858` számláló nem nulla állapotban a Ctrl+G-t (és minden más billentyűt) a `0x00a53b00` elnyeli, mielőtt bármelyik nézet látná.

A 10.24 „Ctrl+G nyitott” állítása ezzel pontosítva: a lánc megvan, a végpont (V osztálya és kezelője) nyitott.

**Nyitott pontok (munkasorba):**

- `V` azonosítása: a `0x00a576f0` virtuális hívóinak (`call [reg+0x7c]`) argumentum-forrása a könyvtárnézetben; a `CThumbUI` saját `+0x7c` (`0x005fa760`) és a `SliceUI` `0x00a576f0`-ja közti különbség.
- `V.vtbl[+0x74]` célja a `V` osztályától függően, és a gyermekei (`0x009e42b0` → `vtbl[+0xc]`, C-lista → `+4`/`+0x74`/`+8`).
- `P = [C+0x150]` azonosítása, és a `0x009e4630` ága Ctrl+G-re.
- `[event+0x20]` külső írói (a nem-konstruktor úton érkező eseményeknél).
- `[0x00d67858]` neve és a párok szerepe (`0x00520fa0` növelő, `0x00512030` csökkentő).
- A négy nem-végigolvasott VK-összehasonlítás (`0x0054c540`, `0x007360b0`, `0x007a5c10`, `0x00a99620`).
- Dinamikus mérés: futó Picasában a könyvtárnézetben Ctrl+G, és ellenőrizni, történik-e bármi (új nézet, kijelölés, figyelmeztetés). Ez az egyetlen út, amely a „hatástalan” kijelentést statikus nélkül is igazolná.

**Kész, ha (Ctrl+G):**

- [x] A Ctrl+G dispatch-lánc (`0x00a53b00` → `0x00a582f0` → `0x009e4630` / `0x009e42b0` / `V.vtbl[+0x74]` / C-lista) utasításszinten igazolva.
- [x] A `[0x00d67858]` és a `[event+0x20]` szerepe a láncban igazolva (a nevük nyitott).
- [x] A VK-0x47 közvetlen kezelő-keresés elvégezve; a negatív eredmény a vizsgált eseteken igazolt.
- [ ] A `V` (könyvtárnézeti aktív nézet) osztálya azonosítva.
- [ ] A `V.vtbl[+0x74]` és a gyermekek Ctrl+G-kezelése igazolva, vagy a teljes lánc `0xf4241`-et ad (kódúton igazolva).
- [ ] Dinamikus mérés: Ctrl+G a könyvtárnézetben, a változás rögzítve.
- Csak ha mindhárom nyitott pont negatív: „a Ctrl+G a könyvtárnézetben hatástalan”.

### 10.28 #4699 — a Ctrl+Alt (VK `0x12`) látható hatása: felugró `PopDisplay`-ablak (2026-10-13)

**Kérdés:** mi látszik Ctrl+Alt (Alt, VK `0x12`) lenyomásakor? A #4643 szerint a `0x00571a80` a gyerekobjektumot „CThumbUI”-ként frissíti; ez pontatlan.

**Módszer.** A Picasa 3.9.141.259 bináris (`644b7bec…dc96`) helyi példányán, futtatás nélkül. A bináris-index `functions` tábláját függvényenként söpörtem capstone-nal: a `.text` egyetlen lineáris söprése a `0x0050d53d` körül megszakad, ezért ott nem használtam. Az IAT-névhez nem volt index-bejegyzés; az API-t az argumentumok alakjából jelölöm (pl. `0x7F89` = IDC_HAND, `0x17` = SM_SWAPBUTTON, `0x12` = VK_MENU), és ezt külön jelzem. Egy korábbi kör (`d164c968f`, a 10.25 szakasz, #4698/#4699) ugyanezt a láncot részben már bejárta; az ellentmondásait lent jelzem.

**Lépésenkénti bizonyíték**

| # | Hely | Mit mutat | Független út | Fok |
|---|---|---|---|---|
| 1 | `0x005e65dc` | `cmp byte [panel+0xe78],0` → `je`; `eax = [panel+0xe70]`; `cmp eax,-1` → `je`; `push eax; push panel; call 0x571a80`. Ez a kapu. | a `+0xe78` egyetlen olvasója a `.text`-ben (szkennelve) | megerősített |
| 2 | `0x00564cd3`, `0x00564d1a` | `push "EnableHover"` (`0xc8e624`), `call 0x4019b0` (HKCU registry-olvasó a `Preferences` ágon), `mov [panel+0xe78], al`. | a `0x005643e0` string-xref-listájában ott van az `EnableHover` (és a `ShowHidden`, `captionmode` stb.) | megerősített; **alapértéke nyitott** (a `0x00564d00` `mov [esp+0x70],1` gyanítható, nem igazolt) |
| 3 | `0x0056b6f0` | ha az új index ≠ `-1` és ≠ `[panel+0xe64]` (aktuális kép), akkor `[panel+0xe70] := [panel+0xe64]`. | az `[+0xe64]` írói (10.25): csak a konstruktor és `0x005e8c2d`, tehát a `0x0056b6f0` nem írja | megerősített (az asm); **a jelentése** („az aktuális kép”) feltételes |
| 4 | `0x00571a80` | `[child+0xb8] := id` (a kapott azonosító); ankerezés (`0x00aa5760` = slot 4, MoveWindow-alak); majd `0x00774d60(child)`. **Nem olvassa a VK `0x12`-t** (a callee-listában nincs `GetAsyncKeyState`). | decompile + asm | megerősített |
| 5 | `0x00774d60` | `GetAsyncKeyState(0x12)` csak `DAT_00d67849 ≠ 0` mellett; `[child+0xb4] := (Alt nincs lenyomva)`; utána `GetClientRect(child)`. | decompile (a callee-lista tartalmazza a `GetAsyncKeyState`-t) + asm (`0x774d60`-on belül) | megerősített |
| 6 | `0x00774f95`–`0x00774f9d` | `cmp [esp+0x24], 0x400` → `jbe 0x7750f8`: **a megjelenítő ág csak ha a gyerek kliensszélessége > 1024 px**. Az `[esp+0x24]` a step-5 `GetClientRect` `right` mezője. | asm + decompile (`if (0x400 < right)`) | megerősített |
| 7 | `0x007750ca` → `0x00775320` | `call 0x775320`: `push 5; push hwnd; call [0xc40890]` = `ShowWindow(hwnd, SW_SHOW)` (feltétel: két ellenőrzés, `0xc40894`, `0xc4088c`). Utána `InvalidateRect(hwnd,0,0)` és `UpdateWindow` (`0x007750d2`). | a vtábla slot 2 (`0x00983840`, `ShowWindow(h, arg?5:8)`, `d164c968f`) ugyanazt az IAT-slotot használja; a `0x775390` `push 0` változata (SW_HIDE) is | megerősített (két út) |
| 8 | `0x00774d60` → owner `+0x260` | a betöltés és a megjelenítés (step 7) csak akkor fut, ha a `FUN_006cfe10` index ≠ `[child+0xb8]`, vagy a téglalap változott (`0x00774fba`–`0x00774ffd`; egyezés esetén a `je 0x7750f8` kihagyja a blokkot). Ha fut: `call [vtbl+0x0]` az `owner+0x260` objektumon `(id, &rect, 0)`-val. Ez a kép betöltésének helye. | asm | megerősített (feltétel és hívás); **a betöltő objektum típusa nyitott** |
| 9 | `0x00774bc0` (WndProc, vtábla slot 7) | `WM_PAINT` (`0xF`) → `0x009aa720`; a `BitBlt`-alakú másolás a `[obj+0x24]` bitképből (`d164c968f`). | egy út (`d164c968f`); ebben a körben nem követtem végig a `0x9aa720`-at | **feltételes** |
| 10 | `0x00cb36ec` (`ytCallback<PopDisplay>`) | periodikus visszahívás: a `0x00775590` konstruktor írja a vtáblát (`0x007755cd`); a vtábla slot 1 = `0x00775550`, amely időbélyeget olvas (8 bájt) és a `0x007753f0`-t hívja (`0x00775572`). | vtábla-szkennelés (`0x00cb36f0`) + asm | megerősített; **a timer-regisztráció** (`0x0097d150`) **nyitott** |
| 11 | `0x007753f0` (a „tick”) | olvassa `[child+0xb4]`-et (`0x0077543c`, `0x00775495`) és `DAT_00d67849`-et (`0x0077544a`, `0x0077549d`); `LoadCursor(NULL, 0x7F89)` + `SetCursor` (IDC_HAND); a fő egérgomb VK-ját a `GetSystemMetrics(0x17)`-ből (cache: `0xd4a490`). Ha nem lép ki, a végén `call [vtbl+0xc]` = slot 3 = `0x00775390`. | asm; a `d164c968f` ugyanezt a döntési fát adja | megerősített (két út) |
| 12 | `0x00775390` (slot 3) | `[child+0xc8] = [child+0xcc] = 0`; `ShowWindow(hwnd, 0)` = **elrejtés** (ugyanaz az IAT-slot, mint a step-7 SW_SHOW). | asm + a vtábla slot-listája | megerősített |
| 13 | `0x00a52e66` | `DAT_00d67849 := wParam ≠ 0` a `0x1C` (WM_ACTIVATEAPP) ágban — ez az „a Picasa az előtérben van” jelző. A `0x005760e0` a főablak létrehozásakor `1`-re állítja (`0x00576419`). | asm + a `00-index.md` #2224 | megerősített (két út) |

**Összefüggő szabályok (a tick-ből, asm szerint):**

- `[child+0xb4] = 0` (az utolsó frissítés Alt-tal történt) és az Alt élőben is le van nyomva → a tick **kilép**: a felugró ablak marad.
- `[child+0xb4] = 0` és az Alt már nincs lenyomva → a tick **elrejt** (slot 3).
- `[child+0xb4] = 1` (az utolsó frissítés Alt nélkül történt) → a tick csak akkor rejt el, ha a fő egérgombot lenyomják.
- A `DAT_00d67849 = 0` (a Picasa nincs az előtérben) → a tick nem enged „kilépést” a rejtés elől (fg=0 ágak).

**Következtetés.** A Ctrl+Alt (VK `0x12`) látható hatása: **felugró `PopDisplay`-ablak** (külön HWND, `ShowWindow(SW_SHOW)`), amely az `[panel+0xe70]` azonosítójú képet rajzolja. Feltételei: (1) a `EnableHover` beállítás be van kapcsolva, (2) az `[e70]` nem `-1`, (3) a Picasa az előtérben van, (4) a gyerekablak kliensszélessége > 1024 px. Alt tartására az ablak marad, a kurzor a felugró ablak fölött kéz-alakú (IDC_HAND). Elrejtés: Alt-elengedés után a tick (ha az utolsó frissítés Alt-tal volt), vagy a fő egérgomb lenyomása (ha Alt nélkül frissítettünk). **Ez nem a rács bélyegképének hover-keretére vonatkozik**: a `design-guide.md` 187–188. sorának „nincs látványos hover-effekt” megállapítása a rácsra szól, és a két jelenség nem ütközik. A `picasa-linux-mod.md` „egér-alatti kiemelés” sora (`EnableHover`) ezzel szemben a PopDisplay-ablakra vonatkozhat; ez utóbbi nincs külön igazolva.

**Egyezés a `d164c968f`-es 10.24-gyel:** a tick döntési fája (`b4`, `DAT_00d67849`, az egérgomb- és Alt-ág) ugyanaz. A `d164c968f` a `0x774d60` frissítőt jelölte az Alt-állapot írójának (`GetAsyncKeyState(VK_MENU)`); ez egyezik a step-5 eredményemmel. Az `osszefoglalo.md` #26 ezzel szemben a `0x00571a80`-nak tulajdonítja a VK `0x12` olvasását: ez téves.

**Fok:** a megjelenítési lánc (kapu → EnableHover → 0x571a80 → 0x774d60 → ShowWindow) és a rejtési szabály **megerősített**, két úton. A kép tartalma (step 8–9) **feltételes**. A futásbeli viselkedés (ablakpozíció, időzítő-periódus) **nincs megmérve**: a gépen nincs Wine, és nem indítottam el a binárist.

**Nyitott:**

- A `EnableHover` alapértéke (ha a kulcs hiányzik): nincs igazolva; a `0x00564d00` `mov [esp+0x70],1` jelölt, de a `0x407a20` konvenciója nincs végigkövetve.
- Az `[e70]` jelentése: a `0x0056b6f0` az aktuális képet (`[e64]`) másolja oda; hogy ez az a kép, amit a felhasználó lát, vagy a legutóbbi előző, **nem dőlt el** (futtatás kell).
- A betöltő objektum az `owner+0x260`-on (step 8): típus és slot 0 nincs azonosítva; így a popup pontos tartalma (méret, átméretezés) **nyitott**.
- Az Alt-elengedés útja: a `WM_KEYUP` eléri-e a `0x005e65dc` kaput? A VK-ugrótábla (`0x005e6617` hivatkozás) nincs dekódolva. Ha nem éri el, a popup a tick-szabályok szerint az Alt-elengedés után is maradhat, amíg a fő egérgombot nem nyomják.
- A `0x0097d150` (a periodikus tick regisztrálása): nincs igazolva, hogy milyen időközzel fut.
- A `0x00774b60` hívója `0x0077524a`-nál: a második `ShowWindow`-útnak nincs azonosított argumentuma (`[esp+0x20]`).
- Futásbeli próba (az eredeti Picasa): **NINCS MEG**; a látható tartalom és az időzítés csak célzott próbával mérhető.

**Megvalósítás-állapot (#4928 → 0.9.89, #4935, `e30b6d5b4`):** lásd a 10.32-t — a fő látványelem megvan, de a feltételrendszer és az elhelyezés nem egyezik a fenti binárisbeli lánccal.

**Kész, ha (ha megépítjük, nem most).** A jegy csak akkor nyitható fejlesztői al-jegynek, ha az első három nyitott pont (EnableHover alapérték, `[e70]` jelentése, Alt-elengedés útja) lezárva van. Addig a feature nem specifikált. Javasolt feltételek:

- [ ] `EnableHover` alapértéke igazolva (a `0x407a20` és a `0x4019b0` alapértékének két független olvasata).
- [ ] Az `[e70]` jelentése igazolva: az Alt-lenyomás pillanatában megjelenő kép azonosítója, két úton (asm + eredeti Picasa futtatás).
- [ ] Alt-elengedés útja igazolva (WM_KEYUP → `0x005e65dc`, vagy annak hiánya).
- [ ] A popup-kép forrása (owner `+0x260` objektum) azonosítva, és a `WM_PAINT`→`BitBlt` út végigkövetve.
- [ ] Megvalósításkor: a billentyű-kötés a `PhotoViewer`/`Main` fókuszkapujával egyezzen; a popup csak akkor jelenjen meg, ha mind a négy feltétel (EnableHover, `[e70]` érvényes, az előtérben, >1024 px) teljesül. Teszt: a feltételek bármelyikének hiányában nincs popup.

### 10.30 #4643 — ötödik kör, második rész (2026-10-13): V, a `+0x74` slot, a négy VK-összehasonlítás

**Kiinduló helyzet.** A 10.27 három nyitott pontja: (1) `V` osztálya, (2) `V.vtbl[+0x74]` célja, (3) a négy nem végigolvasott VK-összehasonlítás (`0x0054c540`, `0x007360b0`, `0x007a5c10`, `0x00a99620`). Ez a rész mindhármat megvizsgálta.

⛔ **Javítás a 10.26-hoz.** A 10.26 nyitott pontjában szereplő „`call [reg+0x7c]`" keresés csak a közvetlen alakot kereste. Ebben a binárisban a virtuális hívás MSVC-módon gyakran kétlépéses: `mov R,[X+0x7c]` … `call R`. Közvetlen alak: **1** találat (`00b50c7f call [esp+0x7c]`, verem-indirekt, nem vtábla). Kétlépéses alak: **154** találat. A vtábla-hívók tehát a kétlépésesek között vannak, a közvetlen keresés erről nem ad képet.

**Módszer.** (a) `.text` függvényenkénti capstone-pásztázás (20 608 függvény, nem egyben): közvetlen `call [R+0x7c]`, kétlépéses `mov R,[X+0x7c]` + `call R` (6 utasításos ablak), közvetlen `call 0x00a576f0`. (b) A `0x00a576f0` vtábla-előfordulásainak keresése a `.rdata`-ban (DWORD-keresés), slot-index és RTTI-név párosítás. (c) A hívási helyek törzsének kiolvasása, és a hívó `this`-ének meghatározása a prológus alapján. (d) A `V`-jelölt osztályok `+0x74` slotjának kiolvasása a vtábla-memóriából. (e) A négy VK-összehasonlító függvény teljes kiolvasása.

**(1) A `0x00a576f0` a ytUIDialog-család SetActiveView-je.** 18 vtáblában szerepel, mindegyikben a 31. slot (`+0x7c`): `SliceUI` (`0x00c8b97c`), `ytUIDialog` (`0x00c93f64`), `CInitialScanDialog`, `ChooseEmailDialog`, `CCollabDialog`, `CBuzzUploadDialog`, `CBaseUploadDialog`, `CFolderMgrDialog`, `CUploadManagerDialog`, `CButtonManagerDialog`, `OneUpUI`, `CTransTimeline::UI`, `QuickTagConfigDlg`, `ComposeDialog`, `CGeoLocateDialog`, `CPrintOptionsDialog`, `CCaptureMoviePanelPopup`, `ytDrawUI`. A `CThumbUI` (`0x00c9052c`) `+0x7c` slotja **`0x005fa760`**, nem a `0x00a576f0`.

Működés (utasításszintű, a 10.26 kiegészítése): `thiscall`, egy verem-argumentum (az új nézet, `ebx`), `ecx` = a konténer `C`. `ebx == 0`: a nézet törlése. `ebx == -1`: a `[C+0x164]` verem tetejére lépés, ha `([C+0x168] & ~1) != 0`. Egyébként `[C+0x15c] := ebx`, a régi nézet `vtbl[+8]`, az új `vtbl[+4]` és `vtbl[+8]` hívása, közben `0x009e42b0` és `vtbl[+0x74]` (a régi nézetre, `(0, ptr, ptr)` aláírással).

**(2) A hívók argumentum-forrása.** A kétlépésesek közül a hívási helyeket a hívó metódusa szerint néztem:

| hívási hely | a hívó | a hívott `+0x7c` | argumentum-forrás | fok |
|---|---|---|---|---|
| `0x00a589aa`/`0x00a589af` | a SliceUI-metódus `0x00a58930` (slot 33; `esi` = a `this`) | `0x00a576f0` | `**[esi+0x164]` (ha `[esi+0x168] & ~1 ≠ 0`), különben `-1` | **megerősített**: utasítások `0x00a58970`–`0x00a589b1` |
| `0x005fca25`–`0x005fca2e` | a CThumbUI-metódus `0x005fa770` (slot 33); `edi` = `[esp+0x1c]`, egy verem-paraméter (konténer) | a `edi` osztályától függ; SliceUI esetén `0x00a576f0` | literál `-1`: vissza az előző nézetre | **megerősített** az argumentum; a `edi` osztálya **nyitott** |
| `0x005dec98` | a CThumbUI-metódus `0x005de8e0` (slot 22); `esi` = `[esp+0x10]` = a `this` (a prológusban `mov [esp+0x10], ecx`) | CThumbUI `+0x7c` = `0x005fa760` | `eax` = 0 (a nyomkövetés kikapcsolva) vagy egy nyomkövető-objektum | **valószínű**: a `this` azonosítása a prológusból, a verem-mélység végig nem ellenőrizve; a célfüggvény ettől **nem** a `0x00a576f0` |
| `0x005df888` | ugyanaz a `0x005de8e0` | a `RTDynamicCast`-ból kapott `ytBasePanel*` `+0x7c` = `0x009e08b0` | `ebx` | **megerősített**: a `dynamic_cast` típusai `ytDrawNode` → `ytBasePanel` (a `0xd3b8a0` és `0xd3b914` TypeDescriptor-nevei); a célfüggvény nem a `0x00a576f0` |

A maradék ~149 kétlépéses hívási hely **nem** lett végigolvasva; osztályuk nyitott.

**Következmény a `V`-re.** A vizsgált hívók között nincs olyan, amely a könyvtárnézetet (CThumbUI-t vagy más nézetet) `this`-ként adná a konténer `SetActiveView`-nek. A `V` osztálya így **nyitott**: a `SliceUI`-beli `-1`/verem-visszalépés és a CThumbUI-beli `-1` nem azonosítja, melyik nézet áll a `[C+0x15c]`-ben a könyvtárnézetben.

**(3) `V.vtbl[+0x74]`.** A `+0x74` slot osztályonként más függvény, és a két hívási alak eltér: a `0x00a576f0`-ban `(0, ptr, ptr)`, a `0x00a582f0`-ban `(event, flag)`. A lehetséges `V`-osztályok `+0x74` célja:

| osztály (`vtbl`) | `+0x74` | méret | mit csinál (részleges olvasás) | VK-összehasonlítás |
|---|---|---|---|---|
| CThumbUI (`0x00c9052c`) | `0x00571e50` | 2352 B | `GetAsyncKeyState` a `DAT_00d4a490` (= 1 vagy 2, a `GetSystemMetrics(0x17)` alapján): **egérgomb**-állapot | nincs `0x47`/`0x39`/`0x74` |
| SliceUI (`0x00c8b97c`) | `0x0052fe80` | 260 B | `double` értékbeállító (`fcomp`/`fstp` `[esi+0x340]`) | nincs |
| ytUIDialog (`0x00c93f64`) | `0x00a54050` | 2839 B | méret-/elrendezés-számítás (`fst [esi+0x188]`) | nincs |

Egyik ismert jelölt sem billentyűkezelő a részleges olvasás alapján. Mivel `V` osztálya nyitott, a `V.vtbl[+0x74]` célja **nyitott**; a három jelölt kizárása nem a teljes `V`-kizárás.

**(4) A négy VK-összehasonlítás.**

| függvény | méret | a `cmp` tárgya | ítélet |
|---|---|---|---|
| `0x0054c540` | 753 | `ebx` = **üzenetkód**: `0x14` (WM_ERASEBKGND), `0x18`, `0x47` (WM_WINDOWPOSCHANGED), `0x0f` (WM_PAINT), `0x200`–`0x204` (egér) | nem billentyű — **negatív** |
| `0x007a5c10` | 247 | `esi` = **üzenetkód**: `0x05` (WM_SIZE), `0x19`, `0x47`, `0x133` (WM_CTLCOLOREDIT) | nem billentyű — **negatív** |
| `0x007360b0` | 1489 | `esi` = üzenet. A `0x100` (WM_KEYDOWN) ágon csak a `0x2e` (VK_DELETE) van kezelve; minden más VK a `0x00984970` alap-kezelőnek megy | a `0x47` nem billentyű; `0x39`/`0x74` nincs összehasonlítva — **negatív**, de a `0x00984970` belső hívásai (`0x982bd0`, `0x983140`, `0x9839a0`, `0x983a60`, `0x984660`) **nem** lettek követve |
| `0x00a99620` | 660 | `cmp byte [esp+0x1a], 0x47` a `'T'`, `'A'`, `'G'` (`0x54`, `0x41`, `0x47`) szövegegyezésben | szövegillesztés, nem billentyű — **negatív** |

Összesen: a 12 ismert `0x47`-immediate összehasonlításból mind a 12 **nem** VK-összehasonlítás (ablaküzenet, típusmező, kisbetű-konverzió, szöveg). `0x39` (Ctrl+9) és `0x74` (F5) egyik négy vizsgált függvényben sincs.

**Következtetés.**

- A Ctrl+G **nincs közvetlen VK-0x47 kezelőben** a teljes listán (12/12 vizsgálva). Ez a kizárás **nem** elég: egy tartomány- vagy táblázat-alapú Ctrl-betű-kezelő a `0x00a582f0` láncon át működne, és annak két végpontja (`V.vtbl[+0x74]`, a C-gyermekek) nyitott.
- Ctrl+9 és F5: a négy vizsgált függvényben nincs kezelő. A `0x00984970` alap-kezelő és a `V`-végpont nyitott.
- A könyvtárnézeti hatás: **nyitott**. Sem kimondható hatás, sem kizárás nincs.

**Bizonyíték-táblázat (összefoglaló)**

| állítás | fok |
|---|---|
| `0x00a576f0` = a ytUIDialog-család slot 31 (`+0x7c`) SetActiveView-je, 18 vtáblában | megerősített (vtábla-memória, DWORD-keresés) |
| `CThumbUI +0x7c = 0x005fa760` | megerősített (vtábla-memória) |
| 154 kétlépéses + 1 verem-indirekt hívási hely; direkt `call 0x00a576f0` nincs | megerősített (pásztázás) |
| SliceUI-hívó `0x00a58930`: argumentum `**[this+0x164]` vagy `-1` | megerősített (disassembly) |
| CThumbUI-hívó `0x005fa770`: `[edi+0x7c](edi, -1)` | megerősített az argumentum; `edi` osztálya **nyitott** |
| CThumbUI `0x005de8e0`: a saját `+0x7c` (`0x005fa760`) és a `ytBasePanel +0x7c` (`0x009e08b0`) — nem a `0x00a576f0` | valószínű (a `this` a prológusból); a `ytBasePanel` megerősített |
| `V` osztálya | **nyitott** |
| `V.vtbl[+0x74]` célja | **nyitott**; a három jelölt (CThumbUI, SliceUI, ytUIDialog) nem billentyűkezelő a részleges olvasás szerint |
| `0x0054c540`, `0x007a5c10`: üzenetkód-kapcsoló | megerősített (disassembly) |
| `0x007360b0`: WM_KEYDOWN-ág, csak VK_DELETE; a többi a `0x00984970`-re | megerősített; a `0x984970` belseje **nyitott** |
| `0x00a99620`: `'T','A','G'` szövegegyezés | megerősített |

**Nyitott pontok (munkasorba):**

- `V` osztálya: a 149 nem végigolvasott kétlépéses hívási hely osztályának azonosítása; vagy annak a konstruktornak / beállító kódnak a megtalálása, amely a könyvtárnézet nézetét a `[C+0x15c]`-be teszi.
- `V.vtbl[+0x74]`: a `V` osztályától függően; a `CThumbUI +0x74` (`0x00571e50`) teljes törzse.
- `0x00984970` (`0x007360b0` alap-kezelője): a belső hívásainak (`0x982bd0`, `0x983140`, `0x9839a0`, `0x983a60`, `0x984660`) követése, Ctrl-betű-ágra.
- Dinamikus mérés (az egyetlen út a „hatástalan” igazolására): futó Picasában a könyvtárnézetben Ctrl+G, Ctrl+9, F5.

**Kész, ha (Ctrl+G, a 10.26 + 10.27 együtt):**

- [x] A dispatch-lánc utasításszinten igazolva (10.26).
- [x] `[0xd67858]` és `[event+0x20]` szerepe a láncban igazolva (10.26).
- [x] A VK-0x47 összehasonlítások mind a 12 vizsgálva; egyik sem billentyű-kezelő (10.27).
- [x] A négy nem-végigolvasott VK-összehasonlítás vizsgálva (10.27).
- [ ] `V` osztálya azonosítva.
- [ ] `V.vtbl[+0x74]` célja és a gyermekei igazolva, vagy kódúton `0xf4241`.
- [ ] Dinamikus mérés a könyvtárnézetben.
- Csak ha mindhárom nyitott pont negatív: „a Ctrl+G a könyvtárnézetben hatástalan”.

### 10.32 #4699 / #4928 — lefedi-e a megvalósítás a 10.28 hatását? (2026-10-13)

**Kérdés:** a `#4928` (0.9.89, `e30b6d5b4` / PR #4935) a jegy kérdését — a Ctrl+Alt látható hatását — lefedi-e, és ha nem, mi a különbség.

**Következtetés:** a **fő látványelem** egyezik: Ctrl+Alt lenyomva tartva felugró nagy előnézet jelenik meg az egér alatti rácselemről, elengedésre eltűnik (`tests/app/qml_functional/test_ctrl_alt_hover_preview_4928.py`, a `ctrlAltHoverPreviewWindow` objektum). **Nem fedi le** a 10.28 feltételrendszerét és elhelyezését: a kapcsoló rossz (buboréksúgó, nem `EnableHover`), a méretküszöb más objektumon van, a kép kiválasztása a 10.28 3. lépésével ellentmond, és az elrejtés késleltetése hiányzik. A #4928 jegy törzse ezt állítja (`EnableHover` + „a spec feltételeit követi”), a kód nem teljesíti.

**Bizonyíték — összevetés (eredeti Picasa 3.9.141 bináris ↔ #4935 kód):**

| Szempont | Bináris (eredeti) | #4935 megvalósítás | Egyezik? |
|---|---|---|---|
| Kapcsoló | `Preferences\EnableHover`, HKCU-olvasás: `push 0xc8e624` (`EnableHover`), `push 0xc7eafc` (`Preferences`), `call 0x4019b0` @ `0x564cd3`–`0x564d16` — **megerősített** | `showTooltipsEnabled` (`appearance_controller.py:185`, kulcs `view/showTooltips`, #4449 Általános fül buboréksúgó); a teszt is ezt kapcsolgatja (`setShowTooltipsEnabled`) | **NEM** — másik beállítás |
| Kapcsoló alapértéke | **NINCS MEG.** A `0x564d00` `mov [esp+0x70],1` a `0x407a20` bemenete; a `0x407a20` hiányzó-kulcs ága nincs végigkövetve. A `0x4019b0` a `RegOpenKeyEx`-burkoló (`0xf003f`), nem ad alapértéket. | nincs összevetve | — |
| Ctrl+Alt bemenet | VK `0x12` + Ctrl-ág `0x005e65dc` (10.22) | Ctrl és Alt együtt a Qt-eseményszűrőben (`eventFilter`, `ctrlAltHeld`) | **egyezik** |
| Előtér | feltétel (10.28) | `grid.appWindow.active` (`LightboxFeed.qml`) | **egyezik** (feltételes) |
| Méretküszöb | a **gyerekablak** kliensszélessége > 1024 px (`GetClientRect(child)`, 10.28 5. lépés) | a **popup-ablak** szélessége > 1024 px (`LightboxFeed.qml`, `visible: … width > 1024`); a popup szélessége a képből jön (≤ 1200 + 24) | **NEM** — más objektum, más szám |
| Kép kiválasztása | `[panel+0xe70]`; a 10.28 3. lépése szerint `[e70] := [e64]`, vagyis az **aktuális kép** indexe (a jelentés feltételes) | `onHoverChanged` → `hoverPreviewRow`: a **kurzor alatti** rácselem | **NEM** — a kurzor-alatti azonosítás a láncból **nem következik**; ez a #4928 premisszája, és a 10.28 3. lépésével ellentmond |
| Elhelyezés | ankerezés a 4. slotra, `MoveWindow`-alak (`0x571a80`, `0x aa5760`); a koordináta **NINCS MEG** | a főablak közepére igazítva | **nem igazolt** |
| Alt-elengedés | Alt-tartás alatt marad; elengedés után a következő tick-en rejt, ha az utolsó frissítés Alt-tal volt (10.28 — a tick-periódus **NINCS MEG**, `0x0097d150`) | `requested` a `ctrlAltHeld`-hez kötött → az elengedés **azonnal** rejt | **NEM** — a tick-késleltetés hiányzik |
| Kurzor | `IDC_HAND` (`0x7f89`) Alt-tartás alatt (10.28) | nincs | **NEM** |
| Egérgomb-elrejtés (Alt nélkül) | fő gomb lenyomása rejt (`0x7754b0`, 10.28) | nincs | **NEM** |
| Videó | **NINCS MEG** | kizárva (`isVideo`) | nincs összevetve |

**Mit jelent a különbség a felhasználónak:** (a) `EnableHover` kikapcsolt eredeti Picasában a popup nem jelenik meg; nálunk a buboréksúgó-kapcsolótól függ — a két kapcsoló független, tehát a viselkedés eltér mindkét irányban; (b) a kép forrása (kurzor vs. aktuális kép) nem igazolt, és ez a legfontosabb nyitott pont a „mit lát a felhasználó” szempontjából.

**Fok:** a fő megjelenés (Ctrl+Alt → felugró kép, elengedésre eltűnik) **megerősített** két úton (bináris: 10.28; kód + teszt: #4935). A feltételrendszer (kapcsoló, méretküszöb) és a képforrás a binárissal **nem egyezik**, ezért az #4935 ezen a ponton eltér a bináris láncától. Az elhelyezés, a tick-késleltetés, a kurzor és a videó **nyitott**.

**Nyitott kérdések mérlege (10.27):**

- `NYITOTT — EnableHover alapértéke` — blokkoló a kapcsoló helyes bekötéséhez. Módszer: a `0x407a20` hiányzó-kulcs ágának végigkövetése (a `0x407a20` `[esp+0x20]`-as paramétere a `DefaultValue` mutató-e), és a `0x4019b0` hívói között egy másik `EnableHover`-olvasó keresése; második út: célzott eredeti-program próba `EnableHover` törölt kulccsal (Wine nincs a gépen, ezért `picasa-colab-jobs` kell, `felhasználóra-vár` nélkül).
- `NYITOTT — a kép forrása: [e70] = aktuális kép vagy kurzor alatti kép` — a `0x56b6f0` / `0x00571a80` lánc egy célzott Colab-próbával dönthető el (Alt-tartás, egér két különböző rácselemen).
- `NYITOTT — Alt-elengedés tick-késleltetése` — a `0x0097d150` periódusa és a `0x0077524a` `ShowWindow`-argumentuma.
- `NYITOTT — elhelyezés` — a `0x00aa5760` slot-geometria kiszámítása `respack`-ből nem adódik; eredeti-program képernyőkép kell.
- `HATÓKÖRÖN KÍVÜL` — nincs tétel. Lezárva: a fő megjelenés (10.28, #4935). Nyitva marad a fenti négy pont.

**Kész, ha — a #4928 eltéréseinek javítása** (fejlesztői al-jegy, ha a két blokkoló pont — EnableHover alapérték, képforrás — eldőlt):

- [ ] a popup-kapcsoló `Preferences\EnableHover` (HKCU, alapérték a bizonyított), nem `view/showTooltips`; a buboréksúgó-kapcsoló nem érinti;
- [ ] `EnableHover` kikapcsolva → nincs popup (teszt a `test_ctrl_alt_hover_preview_4928.py` mintájára);
- [ ] a képforrás a bizonyított azonosító (`[e70]` jelentése szerint), és a teszt két különböző rácselemen ellenőrzi;
- [ ] Alt-elengedés után a késleltetés a mért tick-periódus, nem azonnali;
- [ ] a popup-küszöb (>1024 px) a bizonyított objektumon (gyerekablak), nem a kép méretén;
- [ ] renderelt képernyőkép az eredeti Picasa képével összevetve (a `felhasználóra-vár` csak akkor, ha a Colab-próba nem ad képet).

**Módszertani megjegyzés:** a #4928 jegy a 10.28 feltételeit idézte, de a megvalósítás a `showTooltips` kapcsolót használta, a bináris `EnableHover`-jét nem. A jövőben a megvalósítás-jegy az `EnableHover` olvasóját nevezze meg, és a `test_` fájl egy `EnableHover`-kikapcsolt esetet is tartalmazzon.

### 10.33 #4949 — a küszöb, az alapérték, a képforrás és a tick-periódus lezárása (2026-10-14)

**Kérdés.** A #4949 négy, még nyitott binárisbeli részlete: melyik ablak kliensszélessége kapja a küszöböt; mi az `EnableHover` értéke hiányzó kulcsnál; az `[e70] := [e64]` melyik képhez vezet; és milyen periódussal ellenőrzi a `PopDisplay` visszahívása az Alt állapotát.

**Következtetés.** Az eredeti binárisban a küszöb a `PopDisplay` gyerekablak kliensszélessége, szigorúan `> 0x400` (**1024 px**, a határ QEMU-próbával ellenőrizve); a hiányzó `EnableHover` alapértéke igaz; az előnézet az aktuális képet (`[panel+0xe64]`) kapja; Alt lenyomva tartásakor a callback periódusa `0x0a` (**10 ms**). Az `0x0097d150` a callbacket regisztrálja, nem az időközt tárolja. Az Alt felengedése utáni **tényleges falióra-késleltetés NINCS MEG**: a bináris a következő callbackkor rejt, de a valós ütemezési késés itt nem lett megmérve.

**Bizonyíték és két út.** A binárisbeli címek az eredeti `Picasa3.exe` helyi példányára vonatkoznak. A QEMU-próbák a `qemu_harness/hb.py`-val, az eredeti függvényekkel futottak; nem teljes Picasa-futtatások. A küszöbpróba közvetlenül az eredeti `cmp/jbe` utasításnál állította be a RECT `right` mezőjét. Az alapérték-próba a `0x00408060`-at futtatta; a `0x00985ff0` sztringmásolást és a `0x00401000` takarítást helyettesítő visszatérőkkel kerülte meg, és a globális `atexit` regisztrációt kikapcsoló paramétert adott át. Ez a próba a defaultmezők inicializálását ellenőrzi, nem a Windows Registry hívását. A képmásolási próbában a `0x0056b6f0` három, a vizsgált hozzárendeléshez nem szükséges belső segédhívása (`0x005704d0`, `0x004e40c0`, `0x00570920`) kapott stubot. A tick-próba a `GetAsyncKeyState`, `IsWindowVisible`, `LoadCursorA` és `SetCursor` Win32-hívások célzott helyettesítőit használta. A próbák csak a táblában megnevezett utasítások és adatfolyamok állításait támasztják alá.

| Kérdés | A út — bináris | B út — független ellenőrzés | Eredmény és fok |
|---|---|---|---|
| Küszöb objektuma | `0x00774d60`: a gyerekobjektum HWND-je `[EBX+0x6c]`; `GetClientRect` (`[0xc4081c]`) ezt kapja, a RECT `right` mezője pedig a `0x00774f95` `cmp [esp+0x24],0x400` utasításáig jut. A `jbe` `0x007750f8`-ra ugrik, így a megjelenítő ág csak `right > 0x400` esetén fut. | Az eredeti `cmp/jbe` utasítást QEMU-ban közvetlenül, a RECT `right` mezőjét beállítva futtattam: `1024`-nél a `jbe` feltétel igaz (`ZF=1`); `1025`-nél hamis. A `GetClientRect` híváslánca külön azonosítja, hogy ez a gyerekablak kliens-RECT-je. | **Gyerekablak kliensszélessége > 1024 px** — megerősített. QEMU-korlát: a próba a már kitöltött RECT-et és a határutasítást ellenőrizte, nem hozott létre valódi Windows-ablakot. |
| `EnableHover` hiányzó kulcs | `0x00564d00`: a konstruktor a default helyére `1`-et ír; a mutatót átadja a `0x00407a20`-nak. A `0x00408060` az átadott értéket a registry-objektum értékmezőibe másolja (`[+0x0c]`, `[+0x10]`); a `0x00407a20` hiányzó értékű ága a default feldolgozására jut. A `0x004019b0` alakítja a beállítást logikai értékké, ezt írja a panel `[+0xe78]` mezőjébe (`0x00564d11`–`0x00564d1a`). | QEMU-ban az eredeti `0x00408060`-at a defaultmutatóval futtattam. A `0` bemeneti kontroll eredménye `[+0x0c]=0`, `[+0x10]=0`; az `1` bemeneté mindkét mezőn `1`. Ez ellenőrzi, hogy a mezők a hívó által adott defaultot követik. A hiányzó registry-érték ágát külön az utasításokból követtem végig. | **Kulcs nélkül igaz (`1`)** — megerősített. A QEMU itt a default átadását ellenőrzi, nem a Windows Registry API-t vagy a teljes beállítás-olvasót. |
| Képforrás | `0x0056b6f0`: ha a bemenő index érvényes és eltér `[panel+0xe64]`-től, akkor `[panel+0xe70] := [panel+0xe64]`. A 10.28 3. lépésének külön mezőírói/olvasói lánca az `e64`-et az aktuális kép indexeként azonosítja. | QEMU-ban az eredeti `0x0056b6f0` két különböző, mesterséges bemenő indexet kapott; közben `[e64]` értéke rendre `0x11111111`, majd `0x33333333` volt. `[e70]` rendre az `e64` értékét kapta, nem a bemenő indexet. | **Az aktuális (`e64`) kép, nem a kurzor alatti elem** — megerősített. A szintetikus számok csak a két bemenet megkülönböztetésére szolgáltak. |
| Alt-elengedés callback-periódusa | `0x00775550` meghívja a `0x007753f0` callbacket, és annak visszatérési értékét adja vissza. Látható popup és lenyomott Alt esetén a `0x007753f0` `0x0a`-t ad (`0x0077547f`); a rejtett/inaktív ág `0x64`-et (`0x00775536`). A `0x0097fc30` QPC-delta alapján, az `0x00cf3e10` címen tárolt `1000.0` szorzóval ezredmásodpercekben ütemezi a callback következő futását. A `0x0097d150` csak a callback-objektumot és a regisztrációs jelzőt kapja. | QEMU-ban az eredeti `0x007753f0` Alt-lenyomott ága `0x0a`-val tért vissza; ez megegyezik a scheduler által használt visszatérési értékkel. A `0x0097d150` hívás és a `0x0097fc30` ütemező külön utasításlánca igazolja, hová kerül az intervallum. | **Aktív ellenőrzés: 10 ms; elrejtés a következő tickkor** — megerősített. A felhasználó által érzékelt, valós idejű eltűnési késés: **NINCS MEG**. |

**Cáfoló kísérlet.** A „popup szélessége kapja a küszöböt” olvasatot a `0x00774d60` hívásargumentumával próbáltam cáfolni: a `GetClientRect` argumentuma a gyerekobjektum `[+0x6c]` HWND-je, az összehasonlított `right` pedig ennek kimeneti RECT-jéből jön. A popup saját szélessége nem bemenete ennek az ágnak. A „kurzor alatti index kerül `[e70]`-be” olvasatot két különböző bemenő index és két különböző `[e64]` érték QEMU-próbája cáfolta: az eredeti függvény mindkét esetben `[e64]`-et másolta át. Mindkét cáfoló eredmény egyezik az utasításszintű olvasattal; a küszöb QEMU-próbájának korlátját a fenti sor jelzi.

**Egyezés a jelenlegi megvalósítással (#4950).** A controller már a külön `view/enableHover` beállítást olvassa `True` alapértékkel; a buboréksúgó `view/showTooltips` kulcsa külön marad. A `LightboxFeed.qml` popupja kikapcsolt `enableHover` mellett nem kért, ezt a #4950 tesztje is lefedi. A fennmaradó eltérés: a QML a `hoverPreviewRow` kurzor alatti képét használja, és a küszöb a popup saját `width` mezőjén van. A `ctrlAltHeld` kötés azonnali elrejtést okoz; az eredeti a következő callbackkor rejtett, miközben a látható állapotban a scheduler 10 ms-os callback-periódust kap.

**A #4949 „Kész, ha” pontjainak friss állapota:**

- [x] A popup a saját `EnableHover` beállítását használja, a buboréksúgó nem vezérli (#4950; `appearance_controller.py`, `LightboxFeed.qml`). Hiányzó kulcsnál az eredeti bináris defaultja igaz (`0x00564d00`, `0x00408060`).
- [x] Kikapcsolt beállításnál nincs popup (#4950; `test_ctrl_alt_hover_preview_4928.py`).
- [ ] A `>1024 px` küszöb a gyerekablak kliensszélességén legyen (`GetClientRect(child HWND).right > 0x400`), ne a popup `width` mezőjén.
- [ ] A popup képforrása az aktuális kép (`[panel+0xe64]`), ne a kurzor alatti `hoverPreviewRow`.
- [ ] Elengedéskor az elrejtés az eredeti visszahívás következő tickjén történjen; aktív callback-periódus `10 ms` (`0x007753f0` → `0x0097fc30`). A valós falióra-késésre ne állítson a fejlesztői jegy mérést, mert az **NINCS MEG**.

**A 10.28 és 10.32 státuszának kezelése.** A 10.28/10.32 alatti, e négy pontra vonatkozó „nyitott” bejegyzések a korábbi kutatási pillanatképet őrzik; azok eredményét ez a 10.33-as szakasz váltja fel. A 10.32-ben nyitva hagyott popup-elhelyezés, a `WM_PAINT`/`BitBlt` teljes képútja, a második `ShowWindow` út és a kurzor viselkedése e körnek nem volt kérdése, továbbra is külön nyitott.

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

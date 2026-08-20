# Az „Exportálás mappába" párbeszéd — teljes specifikáció

**Forrás:** `Picasa3/runtime/export.fen` (a párbeszéd **hiteles, teljes
leírója**), a `Picasa3i18n.dll` `54978`-as erőforrása (a magyar
feliratok), a `0x00738c00` kezelőfüggvény (a mentett beállítások), és a
tulajdonos két képernyőképe (2026-08-20).

⚠️ **Ez a lap NORMATÍV, és a leíró bájtra idézhető.** A `.fen` nem
következtetés: ez maga a fájl, amiből a Picasa a párbeszédet felépíti.

---

## 1. A leíró — szó szerint

```xml
<window title="Export to Folder" width="fit" focus="name">
  <labelgroup title="Export location:">
    <group>
      <pathbox name="location"/>
      <button title="Browse..." name="changeloc"/>
    </group>
  </labelgroup>
  <labelgroup title="Name of exported folder:">
    <edit width="fill" name="name" filter="filename"/>
    <check name="addnumbers" title="Add numbers to file names to preserve order"/>
  </labelgroup>
  <labelgroup title="Image size:">
    <radiogroup name="sizeradio">
      <radio title="Use original size"/>
      <radio title="Resize to:"/>
    </radiogroup>
    <group width="fill">
      <bind attr="enabled" source="sizeradio"/>
      <spacer amount="indent"/>
      <edit width="4em" name="sizetext" filter="digits">
        <bind source="size" attr="title" list="320|480|640|800|1024|1200|1600"/>
      </edit>
      <label width="fit" title="pixels"/>
      <slider min="0" max="6" ticks="7" width="fill" name="size"/>
    </group>
  </labelgroup>
  <labelgroup title="Image quality:">
    <group width="fill">
      <popup name="quality" width="10em">
        <item title="Automatic"/>
        <item title="Normal"/>
        <item title="Maximum"/>
        <item title="Minimum"/>
        <item title="Custom"/>
      </popup>
      <multi>
        <bind source="quality" attr="value"/>
        <label title="Preserves original image quality"/>
        <label title="Good balance of quality and size"/>
        <label title="Very large file size, preserves fine detail"/>
        <label title="Smallest file size, some quality loss"/>
        <slider min="0" max="20" ticks="21" name="qualslider" width="fill"/>
      </multi>
    </group>
  </labelgroup>
  <labelgroup title="Export movies using:">
    <radiogroup name="movies">
      <radio title="First frame"/>
      <radio title="Full movie (no resizing)"/>
    </radiogroup>
  </labelgroup>
  <labelgroup title="Watermark:">
    <check title="Add watermark" name="usewatermark"/>
    <group layout="column" width="fill">
      <edit width="fill" name="watermark">
        <bind attr="enabled" source="usewatermark"/>
      </edit>
      <label width="fill" size="small"
             title="Stamp photos with your name, a web domain, or a copyright notice."/>
    </group>
  </labelgroup>
  <buttongroup>
    <button title="Export" type="accept" name="export"/>
    <button title="Cancel" type="cancel"/>
  </buttongroup>
</window>
```

---

## 2. A magyar feliratok — szó szerint, a honosításból

`Picasa3i18n.dll` → `54978`. **Ezeket kell használni, nem újrafordítani.**

| azonosító | magyar |
|---|---|
| `export/window1.title` | **Exportálás mappába** *(pont nélkül!)* |
| `export/labelgroup2.title` | **Exportálási hely:** |
| `export/changeloc.title` | **Tallózás...** |
| `export/labelgroup6.title` | **Az exportált mappa neve:** |
| `export/addnumbers.title` | **Számok hozzáadása a fájlnevekhez a sorrend megőrzése érdekében** |
| `export/labelgroup9.title` | **Képméret:** |
| `export/radio11.title` | **Eredeti méret használata** |
| `export/radio12.title` | **Átméretezés:** |
| `export/bind17.list` | `320\|480\|640\|800\|1024\|1200\|1600` |
| `export/label18.title` | **képpont** |
| `export/labelgroup20.title` | **Képminőség:** |
| `export/item23.title` | **Automatikus** |
| `export/item24.title` | **Normál** |
| `export/item25.title` | **Maximum** |
| `export/item26.title` | **Minimum** |
| `export/item27.title` | **Egyéni** |
| `export/label30.title` | **Megőrzi az eredeti képminőséget** |
| `export/label31.title` | **A minőség és méret megfelelő egyensúlya** |
| `export/label32.title` | **Nagyon nagy méretű fájl, az apró részleteket is megőrzi** |
| `export/label33.title` | **Legkisebb fájlméret, némi minőségvesztés** |
| `export/labelgroup35.title` | **Filmek exportálása:** |
| `export/radio37.title` | **Első képkocka** |
| `export/radio38.title` | **Teljes film (nincs átméretezés)** |
| `export/labelgroup39.title` | **Vízjel:** |
| `export/usewatermark.title` | **Vízjel hozzáadása** |
| `export/label44.title` | **A fotókra rábélyegezheti saját nevét, egy internetes domain nevét vagy egy szerzői jogi közleményt.** |
| `export/export.title` | **Exportálás** |
| `export/button47.title` | **Mégse** |

---

## 3. A viselkedés — amit a kötések előírnak

### 3.1 Az ablak

- **`width="fit"`** — az ablak a tartalomhoz igazodik, nincs rögzített szélesség.
- **`focus="name"`** — indításkor a **mappanév-mező** kap fókuszt, tartalma
  kijelölve (a tulajdonos képernyőképén is így látszik).

### 3.2 Képméret

- `radiogroup` **két** választással; az alapértelmezett az „Eredeti méret
  használata".
- Az átméretező sor **egészében le van tiltva**, amíg a rádió nem az
  „Átméretezés:"-en áll (`<bind attr="enabled" source="sizeradio"/>`).
- A számmező **`filter="digits"`** — csak számjegy írható be.
- **A mező és a csúszka KÖLCSÖNÖSEN kötött**
  (`<bind source="size" attr="title" list="…"/>`): a csúszka 0…6
  pozíciója a hét előbeállítás egyikére áll, és a mezőbe azt írja.
- A csúszka **7 osztásos** (`ticks="7"`), az előbeállítások:
  **320, 480, 640, 800, 1024, 1200, 1600**.
- ⚠️ A mezőbe **tetszőleges szám is beírható** — a lista csak a csúszka
  fogásait adja (a mentett kulcs neve `FileExportCustomSize`).

### 3.3 Képminőség — ITT VAN A LÉNYEG

Öt választás, és a mellette lévő terület **`<multi>`**: mindig **egyetlen**
gyereket mutat, a legördülő értéke szerint.

| választás | ami mellette megjelenik |
|---|---|
| **Automatikus** | „Megőrzi az eredeti képminőséget" |
| **Normál** | „A minőség és méret megfelelő egyensúlya" |
| **Maximum** | „Nagyon nagy méretű fájl, az apró részleteket is megőrzi" |
| **Minimum** | „Legkisebb fájlméret, némi minőségvesztés" |
| **Egyéni** | **CSÚSZKA** — `min=0 max=20 ticks=21`, teljes szélességben |

➡️ **A minőség száma CSAK az „Egyéni" alatt állítható, és CSÚSZKÁVAL, nem
számmezővel.** A másik négy fokozatnál a helyén **magyarázó szöveg** áll.

⚠️ **Az „Automatikus" MÉRT jelentése: megőrzi a forrás kvantálási
tábláit.** A tulajdonos mérőszettjén a forráskép és a Picasa exportjának
JPEG-kvantálási táblája **bájtra azonos**:

```
forrás DQT: 000101010101010101010101010101010202010101010302020202030304
export DQT: 000101010101010101010101010101010202010101010302020202030304
```

Ez nem „valamilyen magas minőség", hanem a **forrás minőségének átvétele**
— pontosan azt teszi, amit a felirata mond.

### 3.4 Filmek exportálása

`radiogroup name="movies"`, két választás: **Első képkocka** /
**Teljes film (nincs átméretezés)**.

⚠️ **Nálunk ez a csoport EGYÁLTALÁN NINCS.**

### 3.5 Vízjel

- Jelölőnégyzet + **alatta** a szövegmező, ami **csak bejelölve engedélyezett**
  (`<bind attr="enabled" source="usewatermark"/>`).
- A mező alatt **kis betűs** magyarázat (`size="small"`).
- A csoport címe **„Vízjel:"** — nálunk nincs ilyen cím.

### 3.6 Gombok

`<buttongroup>`: **Exportálás** (`type="accept"`, alapértelmezett) és
**Mégse** (`type="cancel"`).

---

## 4. A megőrzött beállítások

A `0x00738c00` kezelő ezeket írja/olvassa a `Preferences` alatt —
vagyis **a párbeszéd megjegyzi az előző választást**:

| kulcs | mit tárol |
|---|---|
| `DefaultExportPath` | az exportálási hely |
| `FileExportSize` | a méret-csúszka állása |
| `FileExportCustomSize` | a beírt egyéni méret |
| `FileExportQualityType` | melyik minőség-fokozat (0…4) |
| `FileExportQuality` | az egyéni minőség értéke |
| `FileExportMovie` | a film-rádió állása |
| `ExportWatermark` | a vízjel be/ki |
| `ExportWatermarkText` | a vízjel szövege |
| `ExportAddNumbers` | a számozás be/ki |

**Az alapértelmezett célmappa:** `CExportPrefsDialog::deffolder` =
`Picasa\Exports\` → magyarul **`Picasa\Exportálások\`**.

⚠️ A kezelőben egyetlen 1…100 közötti azonnali konstans van, ami
minőségnek látszik: **85**. Erős jelölt a `FileExportQuality`
alapértékére — ez ugyanaz a szám, ami a PicasaPy párbeszédében ma
látszik.

---

## 5. Eredeti / nálunk / teendő

| | eredeti | nálunk (v0.8.x) | teendő |
|---|---|---|---|
| ablak címe | **Exportálás mappába** | „Exportálás mappába**...**" | a pontokat el |
| hely címkéje | **Exportálási hely:** | „Exportálás helye:" | szó szerint |
| hely mezője | **`pathbox`** (útvonalat mutat) | „(nincs kiválasztva)" szöveg | pathbox |
| számozás szövege | **Számok hozzáadása a fájlnevekhez a sorrend megőrzése érdekében** | „Sorszámozás a fájlnevekben a sorrend megőrzéséhez" | szó szerint |
| **képméret** | **2 rádió + számmező + 7 fogásos CSÚSZKA** | egy legördülő | **átépítés** |
| méret-előbeállítások | 320/480/640/800/1024/1200/1600 | — | átvenni |
| **képminőség** | 5 fokozat + **váltakozó magyarázó szöveg**, és „Egyéni"-nél **21 fogásos csúszka** | legördülő + **nem állítható 85-ös mező** | **átépítés** |
| Normál | **85** | 85 | ✅ nincs teendő |
| Maximális | **193** → skála 0 | 100 → skála 0 | ✅ hatásában azonos |
| Minimális | **65** | **70** | ❌ **65-re javítani** |
| Egyéni csúszka | 0–100 **ötösével**, alap 85, felirat „Egyéni (85)" | nincs csúszka | ❌ pótolni |
| színbontás | fix **4:2:0** | OpenCV alapértelmezés = 4:2:0 | ✅ |
| „Automatikus" jelentése | **a forrás kvantálási tábláinak megőrzése** | fix 92-es közelítés (`exporter.py:83`) | valódi megőrzés |
| **filmek exportálása** | **2 rádió** | **hiányzik** | **pótolni** |
| vízjel | **csoportcím + mező + kis betűs magyarázat** | csak jelölő + mező | pótolni |
| beállítások megőrzése | **9 kulcs a Preferences-ben** | nem vizsgált | ellenőrizni |

---

## 6. Kész, ha

- [ ] Minden felirat a fenti táblából, **szó szerint**.
- [ ] A képméret **rádió + mező + 7 fogásos csúszka**, a hét
      előbeállítással; a sor **le van tiltva**, amíg az „Eredeti méret" az
      aktív.
- [ ] A képminőség **öt fokozat**; a magyarázó szöveg a választással
      **együtt vált**; „Egyéni"-nél a szöveg helyén **21 fogásos csúszka**.
- [ ] Az „Automatikus" a **forrás minőségét őrzi meg** (kvantálási táblák),
      nem fix értéket használ. **Mérce:** a mérőszett bármely képére a
      kimenet DQT-je egyezzen a forráséval.
- [ ] A **„Filmek exportálása"** csoport megvan, két választással.
- [ ] A vízjel-mező **csak bejelölt jelölőnégyzet mellett** aktív, és
      alatta ott a kis betűs magyarázat.
- [ ] A párbeszéd **megjegyzi** az előző beállításokat (9 kulcs).
- [ ] Az alapértelmezett célmappa `Picasa\Exportálások\`.
- [ ] Induláskor a **mappanév-mező** kap fókuszt, tartalma kijelölve.
- [ ] A mappanév-mező **fájlnév-szűrt**, a méretmező **csak számjegy**.

---

## 7. A képminőség öt fokozata — a binárisból kiolvasva (2026-08-20)

*Ez a szakasz a korábbi 1. és 2. nyitott kérdést zárja le. Mérés nem
kellett hozzá: a párbeszéd kódja megadja mind az öt értéket.*

A választás (`ebp` = 0…4) a `0x00739c3f`-nél kezdődő ágon dől el, az
ugrótábla `0x00739ef4`-en áll:

| # | tétel | eredmény | cím |
|---|---|---|---|
| 0 | Automatikus | `[objektum+0xa40] = 1` — **külön logikai jelző** | `0x00739c4d` |
| 1 | Normál | minőség = **85** (`0x55`) | `0x00739caf` |
| 2 | Maximális | minőség = **193** (`0xC1`) | `0x00739ca1` |
| 3 | Minimális | minőség = **65** (`0x41`) | `0x00739ca8` |
| 4 | Egyéni | minőség = **csúszka × 5** | `0x00739c85` |

Az Automatikus és a Normál **ugyanarra a 85-re** megy; a kettőt a
`+0xa40` jelző különbözteti meg.

**A 193 értelme.** A JPEG-kódoló skálázója (`0x00b1cb70`) a szabványos
IJG-képlet: `q<50 → 5000/q`, `50≤q<100 → 2·(100−q)`, **`q≥100 → 0`**
(`0x00b1cb99`). Skála 0 → a kvantálótábla minden eleme 1, azaz a lehető
legjobb JPEG. A 193 tehát **hatásában azonos a 100-zal**.
*(Bizonyítottsági fok: erős. A skálázó viselkedése megerősített, de a
193 útját a párbeszédtől a kódolóig nem követtem végig — ld. lent.)*

**Az Egyéni csúszka leképezése, mindkét irányban:**

| irány | képlet | cím |
|---|---|---|
| betöltés | csúszka = minőség / 5 | `0x007396a9` (`0xCCCCCCCD`, `shr 2`) |
| állításkor | minőség = csúszka × 5 | `0x00739fe6` (`lea eax,[eax+eax*4]`) |

21 fok × 5 = **0, 5, 10 … 100**. Alapérték **85** (`0x0073b14a`
konstruktor és a `FileExportQuality` alapértéke `0x00739642`-nél).

**Az ötödik tétel felirata dinamikus:** `„Custom (%d)"` (`0x00cafa98`,
formázó `0x0073a0c0`) — a `%d` helyén a tényleges szám, ami a csúszka
mozgatásakor azonnal frissül.

**A színbontás fixen 4:2:0** — `0x00b1f85a`: `mov byte [ecx+0x20], 0x22`
(fényesség 2×2), a két színcsatorna `0x11`. Nincs rá beállítás.

### 7.1 Az „Automatikus" mintával is igazolva

A meglévő Picasa-export (30 fájl) mind ugyanazt a kvantálótáblát
használja, és az **bájtra azonos a forrásképekével**:

| | méret | bájt | DQT-összeg (fényesség / szín) |
|---|---|---|---|
| forrás `ansel__alap.jpg` | 960×640 | 61 548 | 221 / 333 |
| Picasa-export ugyanaz | 960×640 | **54 200** | **221 / 333** |

Más a fájlméret → **tényleg újrakódolt**, mégis megtartotta a forrás
tábláit. A táblák pontosan az IJG q=97 skálázásai — ilyen értéket egyik
preset sem tud előállítani, tehát a forrásból jöttek.
➡️ **Automatikus = a forrás kvantálótábláinak átvétele**, nem fix szám.
**Bizonyítottsági fok: megerősített.**

### 7.2 Amit KIZÁRTAM

- ❌ **„Picasa 4:4:4-et ír."** A `0x00b1cbb0`-t fixen `eax=4`-gyel hívják,
  és ebből következtettem rá. Téves: a kódoló `0x00b1f85a`-nál fixen
  `0x22`-t (4:2:0) állít, és a meglévő export SOF-je is 2×2.
- ❌ **„Picasa saját, nem IJG kvantálótáblákat használ."** A hiba az volt,
  hogy a fájlban a tábla **cikcakk sorrendben** áll; természetes sorrendbe
  visszarendezve pontosan az IJG q=97 skálázása, mindkét táblára.

---

## 8. Ami NYITVA marad — ***MIND LEZÁRVA, ld. a 11. szakaszt***

1. **A minőségszám útja a párbeszédtől a kódolóig.** A tárolás helye
   `[objektum+0xa3c]`, a kódoló belépője `0x00b1f870` (a minőség a
   `[esp+0x1c]`-ből jön), a hívó `0x00a97f28`. A közbenső láncot kell
   végigkövetni — ez emelné a 193-as állítást „megerősített" szintre.
2. **A `<multi>` váltásának pontos működése** (átméretezi-e az ablakot,
   ha csúszkára vált). A helye megvan: az elemgyár `0x008dfed0`-ben a
   `multi` ágat `0x008e24f0`-re köti (0x8C bájt, vtábla **`0x00CD00E4`**).
   Azt kell eldönteni, hogy a mérete a **legnagyobb** gyerekhez igazodik-e
   (akkor a párbeszéd nem ugrál) vagy az **aktuálishoz**. A vtábla
   nagyrészt az ős metódusaira mutat, tehát kevés a felülírás.
3. **A film-rádió alapértelmezése** (`FileExportMovie` alapértéke).

---

## 9. AZ ABLAK TÉNYLEGES KINÉZETE — a tulajdonos képernyőképéről mérve

> **Ez a szakasz a `.fen`-t felülírja ott, ahol ellentmondanak.** A `.fen` a
> szerkezetet és a kötéseket adja, a **helyet nem** (`fit`, `fill`, `4em`
> relatív méretek). A tényleges elrendezést csak a futó program mutatja meg.
> Forrás: a tulajdonos képernyőképe a magyar Picasa 3-ról (Windows 11,
> 100 % nagyítás), elmentve:
> `~/picasapy-agent/referencia/export-parbeszed-eredeti.png` (627 × 481).

### 9.1 Az alapelrendezés: KÉTOSZLOPOS űrlap, JOBBRA igazított feliratokkal

Ez a legfontosabb, és a `.fen`-ből **nem** derül ki: a `labelgroup`
felirata **nem a vezérlő fölött**, hanem **tőle balra, jobbra igazítva**
áll, kettősponttal.

| | képpont |
|---|---|
| a felirat-oszlop **jobb** széle | **x = 151** |
| a vezérlő-oszlop **bal** széle | **x = 158** |
| a köztük lévő rés | **7 px** |
| a vezérlők **jobb** széle (mezők) | **x ≈ 606** |
| az ablak teljes mérete (kerettel) | **627 × 481** |

### 9.2 Soronkénti geometria (az ablak bal-felső sarkához képest)

| sor | felirat (jobbra igazítva, x=151-ig) | vezérlő | x | y | méret |
|---|---|---|---|---|---|
| címsor | — | „Exportálás mappába" | 11 | 15 | szöveg; bezáró **X** x≈597–606 |
| 1 | **Exportálási hely:** | `pathbox` | **158** | **46** | **357 × 28** |
| 1 | | **Tallózás…** gomb | **523** | **49** | **82 × 21** |
| 2 | **Az exportált mappa neve:** | `edit` | **158** | **79** | **448 × 26** |
| 3 | *(nincs felirat)* | jelölő **Számok hozzáadása…** | 158 | 112 | jelölő 13 px, felirat x=175-től |
| 4 | **Képméret:** | rádió **Eredeti méret használata** | 158 | 139 | jelölő 13 px |
| 4 | | rádió **Átméretezés:** | 158 | 161 | jelölő 13 px |
| 5 | *(behúzva)* | számmező | ~157 | 187 | ~72 × 25 |
| 5 | | felirat **képpont** | 239 | 194 | 45 × 14 |
| 5 | | **csúszka** | **290** | **187** | **318 × 25** |
| 6 | **Képminőség:** | `popup` | **157** | **232** | **153 × 26** |
| 6 | | **magyarázó szöveg — UGYANEBBEN A SORBAN** | **315** | 240 | szöveg |
| 7 | **Filmek exportálása:** | rádió **Első képkocka** | 158 | 286 | **LETILTVA** |
| 7 | | rádió **Teljes film (nincs átméretezés)** | 158 | 307 | **LETILTVA** |
| 8 | **Vízjel:** | jelölő **Vízjel hozzáadása** | 158 | 335 | |
| 8 | | szövegmező | 158 | ~352 | ~448 × 26, letiltva |
| 8 | | kisbetűs magyarázat, **két sorban** | 158 | 390 | |
| 9 | — | **Exportálás** (alapértelmezett) | **429** | **440** | **83 × 21** |
| 9 | — | **Mégse** | **522** | **440** | **82 × 21** |

A gombok **jobbra igazítva**, az ablak alján; **nincs Súgó gomb** (a
Mappakezelőtől eltérően).

### 9.3 NÉGY viselkedés, ami eddig NEM volt a specben

1. **A magyarázó szöveg a legördülő MELLETT van, nem alatta.** A `.fen`
   `<multi>`-je tehát **soron belüli**: a négy magyarázó felirat és az
   „Egyéni" csúszkája ugyanazt a helyet foglalja el a legördülőtől jobbra.
   ➡️ **Ez megválaszolja a 8. szakasz 2. nyitott kérdését**: a fokozat
   váltása **nem méretezi át** az ablakot, mert a hely fix.
2. **A „Filmek exportálása" rádiók LE VANNAK TILTVA**, ha a kijelölésben
   nincs film. A képernyőképen mindkettő szürke — a `.fen` erre nem ad
   `bind`-ot, tehát futásidejű döntés.
3. **A méret-sor letiltva marad, de az ÉRTÉKET megőrzi.** „Eredeti méret
   használata" mellett a mező szürke, de **1100** áll benne — az előző
   egyéni érték (`FileExportCustomSize`).
4. **Az 1100 nincs a hét előbeállítás között** (320/480/640/800/1024/
   1200/1600). A számmező tehát **szabadon írható**, és a csúszka a hét
   értékre pattan; a kettő nem korlátozza egymást.

Ezen felül: az **exportált mappa nevének szövege induláskor ki van
jelölve** (kék), összhangban a `.fen` `focus="name"`-jével.

---

## 10. A TELJES ESEMÉNYKEZELŐ-TÉRKÉP — minden vezérlő, minden trigger

Négy függvény viszi az egész párbeszédet. Minden vezérlőnév-hivatkozás
címe kiolvasva:

### 10.1 `0x00738c00` — felépítés és beolvasás

| cím | vezérlő | mit csinál |
|---|---|---|
| `0x00738c43` | — | `FileExportSize` beolvasása (alap **3**) |
| `0x00738c88` | — | `FileExportMovie` beolvasása |
| `0x00738cd6` | — | az alapértelmezett mappa: `Picasa\Exports\` |
| `0x00738d16` | — | `DefaultExportPath` |
| `0x00738dfe` | — | `FileExportCustomSize` |
| `0x00738e3f` | — | `FileExportQualityType` |
| `0x00738e80` | — | `ExportAddNumbers` |
| `0x00739053` | `sizeradio` | kötés |
| `0x007390b5` | `movies` | kötés |
| `0x00739113` | `name` | kötés |
| `0x00739151` | `location` | kötés |
| `0x0073918d` | `quality` | kötés |
| `0x007391ea` | `addnumbers` | kötés |
| `0x00739266` | `watermark` | kötés |
| `0x007392e7` | `usewatermark` | kötés |
| `0x007393fc` | `sizetext` | kötés |
| `0x007395dd` | `qualslider` | kötés |
| `0x0073962d` | — | `FileExportQuality` beolvasása, **alap 0x55 = 85** |
| `0x007396a9` | `qualslider` | **csúszka-állás = minőség / 5** |
| `0x0073a0c0` | `quality` 5. tétele | a felirat **„Custom (%d)"** összeállítása |

### 10.2 `0x00739960` — visszaírás a beállításokba

| cím | vezérlő | kulcs |
|---|---|---|
| `0x00739999` | `sizetext` | `FileExportCustomSize` |
| `0x00739a01` | `sizeradio` | `FileExportSize` |
| `0x00739b0d` | `movies` | `FileExportMovie` |
| `0x00739b8b` | `addnumbers` | `ExportAddNumbers` |
| `0x00739c0c` | `quality` | `FileExportQualityType` |
| `0x00739c55` | `qualslider` | — |
| `0x00739d7a` | `usewatermark` | `ExportWatermark` |
| `0x00739dd4` | `watermark` | `ExportWatermarkText` |

### 10.3 `0x00739c3f` — a KÉPMINŐSÉG-legördülő triggere

```
ebp = a kiválasztott tétel (0…4)
0x00739c4d   [objektum+0xa40] = (ebp == 0)      ; „Automatikus" jelző
0x00739c53   ha ebp == 4:                        ; „Egyéni”
0x00739c85       minőség = csúszka × 5
             különben ugrótábla 0x00739ef4:
0x00739caf       0 Automatikus → 85
0x00739caf       1 Normál      → 85
0x00739ca1       2 Maximális   → 193
0x00739ca8       3 Minimális   → 65
0x00739cc0   a FileExportQualityType kiírása
```

### 10.4 `0x00739f70` — a csúszka és a névmező triggere

| ág | cím | mit csinál |
|---|---|---|
| `qualslider` mozgatása | `0x00739fe6` | **minőség = állás × 5**, majd a „Custom (%d)" felirat frissítése (`0x73a0c0`) |
| `name` változása | `0x0073a087` → `0x0073b390` → `0x0073b500` | az exportált mappa nevének átvétele |

### 10.5 A méret és az alapértékek

| cím | mit mond |
|---|---|
| `0x0073b410` | ha a méret-mód `0x3E8` (**1000**), az **egyéni** méret (`+0xa38`) érvényes |
| `0x0073b120` | konstruktor: `+0xa44 = 0`, `+0xa40 = 0` (nem automatikus), `+0xa34 = 0` |
| `0x0073b14a` | konstruktor: **minőség = 0x55 = 85** |
| `0x00b1f85a` | a kódoló színbontása fixen **4:2:0** (`0x22` / `0x11` / `0x11`) |

---

## 11. A NYITOTT KÉRDÉSEK LEZÁRÁSA (2026-08-20, harmadik kör)

### 11.1 A film-rádió alapértéke — **MEGVAN: 0 = „Első képkocka"**

A `FileExportMovie` beolvasása `0x00738c88`-nál:

```
0x00738c88  push 0xcaf974          ; "FileExportMovie"
0x00738c8d  push 0xc7eafc          ; "Preferences"
0x00738c99  lea  ecx, [esp+0x30]   ; ide mutat az alapérték
0x00738c9d  mov  dword [esp+0x30], ebx     ; ebx = 0  (0x00738c12: xor ebx,ebx)
0x00738ca1  call 0x407a20
```

Az alapérték tehát **0**, ami a `radiogroup` **első** tétele:
**„Első képkocka"**.

**Kontroll, hogy ez tényleg alapérték-átadás:** ugyanez a hívás a
`FileExportSize`-nál (`0x00738c43`) a **3**-at teszi ugyanabba a rekeszbe
(`0x00738c58`: `mov dword [esp+0x50], 3`). Ugyanaz a minta, más konstans —
tehát a 0 nem véletlen nullázás, hanem szándékos alapérték.

**Bizonyítottsági fok: megerősített.**

### 11.2 A film-csoport letiltása — **a TÉNY mérve, az OK következtetés**

Eddig szemre mondtam, hogy „szürke". Most **képpontban** mérve, a
képernyőkép legsötétebb 40 képpontjának átlaga vezérlőnként:

| elem | legsötétebb átlag | állapot |
|---|---|---|
| rádió „Eredeti méret használata" | **0,0** | aktív (fekete) |
| jelölő „Számok hozzáadása…" | **0,0** | aktív |
| „Megőrzi az eredeti képminőséget" | **0,0** | aktív |
| jelölő „Vízjel hozzáadása" | **0,0** | aktív |
| **„Filmek exportálása:" CÍMKE** | **0,1** | **AKTÍV — fekete marad!** |
| **rádió „Első képkocka"** | **109,2** | **LETILTVA** |
| **rádió „Teljes film…"** | **109,0** | **LETILTVA** |
| méret-mező „1100" (letiltott sor) | 125,2 | letiltva |
| „képpont" felirat (letiltott sor) | 160,0 | letiltva |

➡️ **Fontos finomítás:** a csoport **címkéje fekete marad**, csak a
**`radiogroup` maga** szürkül el. Tehát nem az egész `labelgroup` van
letiltva, hanem a benne lévő rádiócsoport.

**A binárisban végigkeresve — NÉGY tény, ami az okot NEGATÍVAN dönti el:**

1. **A `.fen`-ben nincs `enabled` kötés a film-csoporton.** Nem az idézetet
   néztem, hanem magát a fájlt (`Picasa3/runtime/export.fen`, 2411 bájt,
   2015-10-13). A méret-csoportnál ott a
   `<bind attr="enabled" source="sizeradio"/>`, a `movies`-nál **nincs**
   semmilyen kötés.
2. **A `.fen`-motor a letiltást KIZÁRÓLAG `<bind attr="enabled">`-ből
   ismeri.** A kötés-attribútum eldöntője a `0x008d2210`: az `attr` értékét
   az `„enabled"` (`0x00ccd33c`) és a `„visible"` (`0x00ccd344`)
   sztringekhez hasonlítja (`0x008d2272`, `0x008d22a9`, `0x008d22fd`,
   `0x008d2334`). Nincs harmadik út.
3. **A `movies` vezérlőnévre a teljes párbeszéd-kódban PONTOSAN KÉT
   hivatkozás van** (`0xca2b64`): a kötés létrehozása `0x007390b5`-nél és a
   beállítás visszaírása `0x00739b0d`-nál. **Egyik sem tilt le semmit.**
   *(A `moviesradio` / `moviesRadio` nevek a `0x007f52b0` / `0x007f5e80`-hoz
   tartoznak — azok a **web-exportáló** saját vezérlői, nem ezek.)*
4. **Nem a kötés típusa okozza.** Vezérlőnként kiolvasva, melyik
   kötés-osztályt kapja:

   | vezérlő | kötés-vtábla | a képernyőképen |
   |---|---|---|
   | `sizeradio` | `0xC7F790` | **aktív** |
   | `quality` | `0xC7F790` | **aktív** |
   | **`movies`** | **`0xC7F790`** | **letiltva** |
   | `addnumbers` | `0xCAA2E8` | aktív |
   | `sizetext`, `watermark` | `0xC8B714` | (a sor tiltva/aktív a kötés szerint) |

   A `movies` **ugyanazt** az osztályt kapja, mint a nem letiltott
   `sizeradio` és `quality` — tehát a különbség nem innen jön.

➡️ **A negatív eredmény, ami ebből következik: az export-párbeszéd SAJÁT
kódja NEM tiltja le a film-rádiókat.** Ezt kimondani többet ér, mint a
korábbi „valószínűleg nincs film a kijelölésben" mondat, mert **kizárja** a
párbeszédet mint helyszínt.

**Ami tehát marad, és hol kell folytatni:** a letiltás vagy a **közös
vezérlő-rétegben** történik (a vezérlő-alaposztály attribútumkezelője
`0x008d1450`, és a `0x008d2210` hívói), vagy a párbeszédet **befogadó
oldalon** — erre a legjobb jelölt a `CExportPrefsPage` (`0x007f6650`),
amely már az export végrehajtásának hibaüzeneteit is viszi.

**Bizonyítottsági fok:** a **tény** (a rádiók letiltva, a címke fekete
marad) **megerősített**, képpontméréssel. A négy fenti kizárás
**megerősített**, címmel. Az **ok** viszont **továbbra sem bizonyított** —
a „nincs film a kijelölésben" magyarázat összefér mindennel, amit tudunk,
de a binárisban **nem találtam meg a helyét**, és ezt nem takarom el.

**A megvalósítást ez NEM blokkolja:** a viselkedés egyértelmű — nincs film
→ a rádiók tiltva, a csoport címkéje aktív marad.

### 11.3 A 193-as érték útja a kódolóig — **a kérdés gyakorlati
következménye NULLA**

A korábbi megfogalmazás („a lánc végigkövetése emelné megerősített
szintre") félrevezető volt, mert azt sugallta, hogy a válasz múlhat rajta.
Nem múlik:

1. A minőség-egész **egyetlen** fogyasztója a JPEG-skálázó
   `0x00b1cb70`, és annak **pontosan egy hívója** van: `0x00b1f8ca`.
2. A skálázó szabálya: `q ≥ 100 → skála 0` (`0x00b1cb99`), a skála 0 pedig
   csupa 1-es kvantálótáblát ad — ez a JPEG-minőség plafonja.
3. **Mi 100-at adunk át, ami ugyanide fut ki.** A kimenet tehát azonos.
4. A 193 csak akkor adna mást, ha valahol egy **100 fölötti értéket
   átalakítanának** (pl. `q -= 100`). Ilyen ág **nincs** — átfésültem az
   export-régiót (`0x00730000`+128 KB), a kódoló-régiót
   (`0x00b1f000`+4 KB), a `0x00a90000`+64 KB-ot és a
   `0x0066f000`+192 KB-ot `cmp/mov 0x64`-re és `0xc1`-re: a `0xC1`-re
   **egyetlen** találat van a teljes export-kódban, a
   `0x00739ca1`-es értékadás maga.

➡️ **Következmény a fejlesztésre: a „Maximális" nálunk maradhat 100.**
Nem közelítés, hanem bizonyíthatóan azonos kimenet.

**Ami formálisan nyitva marad:** a virtuális hívásokon átvezető pontos
hívási lánc a párbeszéd `[objektum+0xa3c]` mezőjétől a kódoló
`0x00b1f870` belépőjéig. **Ez nem befolyásol semmilyen megvalósítási
döntést**, ezért nem nyitott kérdésként, hanem lábjegyzetként tartjuk
számon.

### 11.4 Amit MÉG kimértem menet közben

**Minden Picasa-exportunk „Automatikus"-sal készült.** Ellenőriztem
mindhárom mérőkészlet eredeti exportját: a kvantálótábla a forráséval
**bájtra azonos** (IJG q=97 mindkét oldalon). Ezért a Normál/Maximális/
Minimális fokozatokra **nincs** mintánk — de a 11.3 miatt nincs is rá
szükség.

---

## 12. MI TÖRTÉNIK AZ „EXPORTÁLÁS" GOMB UTÁN — a művelet teljes törvénye

> **Ez a szakasz normatív.** Eddig a lap az ablakot írta le; ez a szakasz
> azt, amit a gomb **csinál**. E nélkül az ablak megépíthető, a funkció nem.

### 12.1 Hova kerül és milyen néven

| | érték | bizonyíték |
|---|---|---|
| a hely alapértéke | a **`DefaultExportPath`** beállítás korábbi értéke; ha nincs elmentve, a honosított **`Picasa\Exportálások\`** | `0x00738d16`; a nyers alapérték `0xCAF984` = `Picasa\Exports\`, a honosítási kulcs `CExportPrefsDialog::deffolder` (`0xCAF994`), betöltés `0x00738cd6` |
| a **mappanév** alapértéke | **a kiválasztott album / mappa neve** | `0x0073b500`: a név a bemeneti szerkezet `+8`-as mezőjéből jön (`0x0073b50b`), és ha nem üres, azt másolja a mezőbe |
| ha a név **ÜRES** | a honosított **`exportálás`** | `0x0073b597`: a `CExportPrefsDialog::exportname` kulcs (`0xCAFB84`) betöltése, angol nyers alapértéke `export` (`0xC81228`); a tartalék beállítása `0x0073b5d8` |
| a végleges útvonal alakja | **`<hely>\<név>\`** — záró visszaperjellel | a `%s\` formátum `0xC967C8`-on, összefűzés `0x0073b638` |
| a mappanév szűrése | `filter="filename"` — fájlnévben tiltott karakter nem írható be | `export.fen` |
| a névmező | induláskor fókuszban, **tartalma kijelölve** | `focus="name"` + képernyőkép |

### 12.2 Ha a célmappa MÁR LÉTEZIK — kérdez, és felülíráskor TÖRÖL

| | magyar szöveg | azonosító |
|---|---|---|
| a kérdés | **„A cél már létezik. Felülírja az új albummal?"** | `CExportPrefsPage::destexists` |
| a kérdés címe | **„Szeretné felülírni?"** | `CExportPrefsPage::overwritetitle` |

⚠️ **Az „igen" nem összefésül, hanem az ELŐZŐ ALBUMOT TÖRLI.** Ezt a
hibaága árulja el: „Belső hiba történt az **előző album törlése** közben."
(`CExportPrefsPage::deleteerror`). A művelet tehát: cél letapogatása →
előző tartalom törlése → új export.

### 12.3 A hibaüzenetek — szó szerint

| helyzet | magyar szöveg | azonosító |
|---|---|---|
| a célmappa nem hozható létre | **„A célkönyvtárat nem lehetett létrehozni."** | `IDS_DESTDIRCANNOCREATE` |
| írási hiba | **„Lemezhiba miatt nem lehetséges az összes fájl írása. Lehet, hogy a lemez megtelt vagy írásvédett."** | `CImageOutput::filewriteerr` |
| fájl-letapogatási hiba | **„Belső hiba történt a fájlok közötti keresés közben."** | `CExportPrefsPage::scanfileerror` |
| könyvtár-letapogatási hiba | **„Belső hiba történt a könyvtárak közötti keresés közben."** | `CExportPrefsPage::scanerror` |
| törlési hiba | **„Belső hiba történt az előző album törlése közben."** | `CExportPrefsPage::deleteerror` |
| könyvtár-eltávolítási hiba | **„Belső hiba történt egy könyvtár eltávolítása közben."** | `CExportPrefsPage::removeerror` |

### 12.4 A folyamatjelző

A haladásjelző felirata **„Exportálás mappába"**
(`CImageOutput::exportprog`, `0x00741840`). Ugyanez a függvény adja az
e-mail- (`Exportálás e-mailbe`) és a képernyővédő-ág feliratát is — tehát
egyetlen közös kimeneti motor, módonként más felirattal.

### 12.5 Az exportált mappa BEKERÜL A KÖNYVTÁRBA

`0x0073f884` az **`IDS_EXPORTED_CATEGORY`** sztringet tölti be:

> **„Exportált képek"** *(angolul: `Exported Pictures`)*

Vagyis az export nem csak fájlokat ír ki: a célmappát **regisztrálja a
könyvtárban**, az **„Exportált képek"** csoport alá — ugyanaz a
mechanizmus, mint amivel a kollázsok a „Projektek" alá kerülnek.
*(A `0x0073f877` feltétele: a kimeneti mód nem 0 és nem 1.)*

### 12.6 A kicsi képeket NEM nagyítja fel

A `UpsizeSmallImages` beállítás beolvasása `0x0073f82b`-nél, az alapérték
a nullázott `esi` → **0**.

➡️ **„Átméretezés: N képpont" esetén az N-nél kisebb kép változatlan
marad**, nem nagyítja fel. Ez alapértelmezés, és nincs rá felületi
kapcsoló — csak a beállításfájlból állítható.

### 12.7 A sorszámozás csak MAPPÁBA exportálásnál él

`0x0073fb96`: `cmp dword [ebx+0x64], 8` — ha a kimeneti mód **nem 8**
(mappába exportálás), a program a sorszámozás-kapcsolót **átugorja** és
nullának veszi (`0x0073fbd1`). Az `ExportAddNumbers` beolvasása
`0x0073fba1`, alapértéke **0** (kikapcsolva).

### 12.8 A felirat és a kulcsszavak ÁTKERÜLNEK a kimeneti fájlba

| adat | hogyan | cím |
|---|---|---|
| **felirat** (`caption`) | átmásolva a kimenetre | `0x00740485` → `0x005ab210` |
| **kulcsszavak** (`keywords`) | **vesszővel** összefűzve | `0x0074050d`, az elválasztó `0x007404b8`: `push 0x2c` = `','` |
| a `.picasa.ini` | a célmappában is íródik | `0x00740295`, `0x007403bc` |

➡️ **Az export nem „nyers kép-kiírás":** a felirat és a kulcsszavak
átkerülnek, és a célmappa saját `.picasa.ini`-t kap.

### 12.9 Kész, ha — a MŰVELETRE

- [ ] a mappanév alapértéke **a forrásmappa neve**, a hely alapértéke a
      `DefaultExportPath`, hiányában `Picasa\Exportálások\`
- [ ] létező cél esetén **kérdés** a fenti két szó szerinti szöveggel, és
      „igen"-re az **előző tartalom törlése** (nem összefésülés)
- [ ] mind a hat hibaüzenet szó szerint, a fenti táblából
- [ ] a folyamatjelző felirata **„Exportálás mappába"**
- [ ] az exportált mappa megjelenik a könyvtárban az **„Exportált képek"**
      csoport alatt
- [ ] a célméretnél **kisebb képet nem nagyít fel**
- [ ] a sorszámozás csak mappába exportálásnál hat, alapból **ki**
- [ ] a **felirat** és a **kulcsszavak** (vesszővel) átkerülnek, és a
      célmappa `.picasa.ini`-t kap

**Bizonyítottsági fok:** a szövegek és az azonosítók **megerősítettek** (a
honosítási táblából, szó szerint); a címekhez kötött viselkedések
**megerősítettek**; a mappanév-alapérték a képernyőképből **erős**.

### 12.10 A SORSZÁM FORMÁTUMA — `%0*d-%s`

A nevet a `0x0073ee70` építi. A formátumsztring a `0xCB0178`-on áll, és
bájtra ez:

```
%0*d-%s
```

A három argumentum, ahogy a kód összerakja:

| argumentum | honnan | cím |
|---|---|---|
| a `*` = **mezőszélesség** | **az összes exportálandó kép darabszámának jegyszáma** — a `0x0073ee81`-es ciklus tízzel osztogatva számolja meg (`0xCCCCCCCD`, `shr 3`) | `0x0073ee81`–`0x0073ee90` |
| a sorszám | `index + 1` → **1-től indul** | `0x0073eeab` |
| a név | az eredeti fájlnév | `0x0073eea6` |

➡️ **A szabály: `<nullákkal feltöltött sorszám><kötőjel><eredeti fájlnév>`,
szóköz nélkül**, és a nullázás **az összlétszámhoz** igazodik:

| hány képet exportálsz | a nevek |
|---|---|
| 7 | `1-kep.jpg`, `2-kep.jpg`, … `7-kep.jpg` |
| 12 | `01-kep.jpg`, `02-kep.jpg`, … `12-kep.jpg` |
| 178 | `001-kep.jpg` … `178-kep.jpg` |

**Bizonyítottsági fok: megerősített** (a formátumsztring bájtra kiolvasva,
a három argumentum összerakása címmel).

### 12.11 Ami a művelet körül MÉG NINCS feltárva

1. A **vízjel rajzolása**: hely, betűtípus, méret, átlátszóság. *(A szöveg
   útja megvan a beállítástól — `ExportWatermarkText`, `0x0073fb2c` — a
   kimeneti beállítás-objektumig `0x0073fb73`/`0x005c2100`; a **rajzolás**
   a renderelési láncban van, azt kell követni.)*
2. A **„Teljes film (nincs átméretezés)"** ág: milyen tárolóba/kodekkel ír.
   *(A `FileExportMovie` fogyasztója `0x0073f3d6`, alapértéke 0.)*
3. Nem JPEG forrás (PNG, TIFF) exportálásakor a **kimeneti formátum**. *(A
   kimeneti motorban `0x0073e000`–`0x00742000` között **nincs** `.jpg`
   sztring, tehát a kiterjesztést a fájlíró réteg dönti el — ott kell
   keresni.)*

---

## 8. A MŰKÖDÉS — a kilenc kérdés (2026-08-21)

A lap eddigi szakaszai a **párbeszéd felületét** írták le (az `export.fen`
alapján). Ez a szakasz azt, **mi történik** — a `picasapy-research` skill
2/b szakaszának kilenc kérdése szerint, a működéssel kezdve.

### 8.0 Függvényleltár — mi a kutatás lefedettsége

Az export-kód **nem egy tartományban** él. A leltár:

| cím | méret | mi ez | megnézve |
|---|---:|---|---|
| `0x005312b0` | 610 | **a párbeszéd megnyitója** (`IDS_DEFAULT_EXPORT`, `Picasa Export`) | ✔ |
| `0x00738c00` | 3035 | a párbeszéd felépítése + a **beállítások BEOLVASÁSA** | ✔ (részben) |
| `0x00739850` | 272 | `changeloc` — a mappaválasztó | ✘ |
| `0x00739960` | 1426 | a **beállítások KIÍRÁSA** | ✘ |
| `0x00739f70` | 324 | `qualslider` — a minőség-csúszka | ✘ |
| `0x0073a0c0` | 117 | `Custom (%d)` — az „Egyéni (N)" felirat | ✔ (korábbi kör) |
| `0x0073a140` | 512 | `ShowUnixPaths`, `wine_get_unix_file_name` — útvonal-megjelenítés | ✘ |
| `0x0073b500` | 459 | `CExportPrefsDialog::exportname` — a célmappa neve | ✘ |
| **`0x0073f320`** | **9396** | **`CImageOutput` — MAGA AZ EXPORT** (mappa, e-mail, képernyővédő közösen) | ✔ (sztringszinten) |
| `0x0073ee70` | 83 | `%0*d-%s` — a sorszámozott fájlnév | ✔ |
| `0x007f6650` | 920 | **`CExportPrefsPage` — a hibaesetek** | ✔ (sztringszinten) |

**Tíz export-függvényből öt van megnyitva**, és a legnagyobb
(`0x0073f320`, 9396 bájt) csak sztringszinten. A maradék öt a 9. szakaszban.

### 8.1 MI AKTIVÁLJA — három belépési pont

| honnan | mi | hova |
|---|---|---|
| **Fájl menü → „Export Picture to Folder…"** | parancs **`0x9c81`** (rekord `0xd6dab4`, azonosító `0xd6dabe`) → a szétosztó 63. indexén `0x005cbaac` | `0x005312b0` |
| **A kimeneti sáv „Exportálás" gombja** | **`outputlayout/folderbutton`** (`0x005dac55`) | `0x005312b0` |
| harmadik út | `0x005e60d0` (1345 b) `0x005e64dd`-ről | `0x005312b0` |

*(A **„Export as HTML Page…"** külön parancs — **`0x9c95`**, rekord
`0xd6e288` —, és NEM ide megy: az a webexport.)*

### 8.2 MIT INDÍT EL kifelé

A `0x005312b0` megnyitja a párbeszédet; az OK az **`CImageOutput`**-ot
(`0x0073f320`) indítja, ami **folyamatjelzőt** mutat:
`CImageOutput::exportprog` = **„Exportálás mappába"**
(e-mail-ágon `::emailprog` = „E-mailbe való exportálás”,
előkészítéskor `::prepareprog` = „Preparing”).

A `CImageOutput` **három kimenetet szolgál ki ugyanazzal a maggal**:
mappa-export, **e-mail** (`temp\email\`, MAPI) és **képernyővédő**
(`Software\Google\Google Photos Screensaver`,
`rundll32.exe desk.cpl,InstallScreenSaver %s`).

### 8.3 MIT ÍR

| tároló | mi | cím |
|---|---|---|
| **kimeneti mappa** | alapértelmezett neve **`Exported Pictures`** | `0x0073f320` |
| **a képfájlok** | a sorszámozott név formátuma **`%0*d-%s`** (`ExportAddNumbers` esetén) | `0x0073ee70` |
| **`.picasa.ini`** | a `caption` és a `keywords` átvitele | `0x0073f320` |
| **`]history:export`** | előzmény-token (a testvérei: `]history:email`, `]history:output`) | `0x0073f320` |
| **registry** (`Preferences\…`) | `FileExportSize`, `FileExportCustomSize`, `FileExportQuality`, `FileExportQualityType`, `FileExportMovie`, `ExportWatermark`, `ExportWatermarkText`, `ExportAddNumbers`, `UpsizeSmallImages`, `EmailExportSize`, `EmailSinglePicture`, `EmailMovie`, `UseHTMLMailer`, `ShadowsHTMLEmail` | `0x00738c00` (olvasás), `0x00739960` (írás) |
| **ideiglenes mappák** | `temp\`, `upload\`, `temp\email\` | `0x0073f320` |

### 8.4 MIKOR érvényesül

A beállítások **kiírója külön függvény** (`0x00739960`), tehát a
mentés nem a beolvasóval közös úton történik — a pontos pillanat
(OK-ra vagy vezérlőnként) a 9. szakasz nyitott pontja.

### 8.5 MI LESZ A MEGLÉVŐ ADATTAL

A célmappa ütközését a **`CExportPrefsPage`** (`0x007f6650`) kezeli:

> **„A cél már létezik. Felülírja az új albummal?"**
> (`CExportPrefsPage::destexists`, cím: `::overwritetitle` = „Szeretné
> felülírni?")

Igen esetén az előző albumot **törli** (`::deleteerror` =
„Belső hiba történt az előző album törlése közben"). Az **eredeti képek
nem módosulnak** — az export új fájlokat ír.

### 8.6 MI FUT LE UTÁNA

Folyamatjelző (`CImageOutput::exportprog`), majd az `]history:export`
token bejegyzése. *(Az indexelés/nézetfrissítés útja a 9. szakasz nyitott
pontja.)*

### 8.7 HIBAESETEK — mind a hét, magyar szöveggel

| kulcs | magyar |
|---|---|
| `CExportPrefsPage::destexists` | A cél már létezik. Felülírja az új albummal? |
| `CExportPrefsPage::overwritetitle` | Szeretné felülírni? |
| `CExportPrefsPage::errortitle` | Hiba |
| `CExportPrefsPage::scanerror` | Belső hiba történt a könyvtárakban való keresés közben. |
| `CExportPrefsPage::scanfileerror` | Belső hiba történt a fájlok közötti keresés közben. |
| `CExportPrefsPage::deleteerror` | Belső hiba történt az előző album törlése közben. |
| `CExportPrefsPage::removeerror` | Belső hiba történt egy könyvtár eltávolítása közben. |
| `CImageOutput::filewriteerr` | Lemezhiba miatt nem lehetséges az összes fájl írása. Lehet, hogy a lemez megtelt vagy írásvédett. |
| `IDS_DESTDIRCANNOCREATE` | A célkönyvtár nem hozható létre. |
| `IDS_NO_IMAGES_TO_SEND` | Nem állt rendelkezésre kép a küldéshez. |

**Tíz hibaág — nálunk egy sincs bekötve.**

### 8.8 HONNAN JÖN INDULÁSKOR AZ ÁLLAPOT

A `0x00738c00` a **registryből** olvassa vissza az összes beállítást
(`Preferences\…`, `0x00407a20`), a célmappát a
`CExportPrefsDialog::deffolder` / `IDS_DEFAULT_EXPORT` adja, és az
útvonal megjelenítését a `ShowUnixPaths` + `wine_get_unix_file_name`
befolyásolja (**Wine-tudatos** — `0x0073a140`).

> ✅ **NYITOTT KÉRDÉS LEZÁRVA — a film-rádió alapértelmezése.** A
> `Preferences\FileExportMovie` értéket a párbeszéd az init elején
> beolvassa (`0x00738c88`–`0x00738cb3`), és a `movies` rádiócsoport
> beállításánál `setne`-vel bináris értékké alakítja
> (`0x007390b1`–`0x007390ba`): **nem nulla → „Full movie (no resizing)",
> nulla vagy hiányzó → „First frame"**. A kétállású csoportnál a `setne`
> eredménye maga a kiválasztott index.
>
> *(Ami ebből NEM következik: mi TILTJA LE a csoportot — ld. 9.)*

### 8.9 …és csak ezután a geometria

A felület leírása a lap 1–7. szakaszában van (az `export.fen`-ből).


## 9. Ami NYITVA marad — és pontosan hol folytassa

**Öt export-függvény nincs megnyitva** (a leltár a 8.0-ban):

1. **`0x0073f320` (9396 b) — a `CImageOutput` törzse.** Sztringszinten
   feltárva (mit ír, milyen hibái vannak), **utasításszinten nem**. Ebből
   következik a 2–4. pont.
2. **Mikor íródnak ki a beállítások** — a `0x00739960` (1426 b)
   végigolvasása; OK-ra, vagy vezérlőnként?
3. **Mi fut le az export UTÁN** — indexelés? nézetfrissítés? Az
   `]history:export` token bejegyzésén túl nem követtük.
4. **A sorszámozás pontos szabálya** — a `%0*d-%s` formátum megvan
   (`0x0073ee70`), de a **szélesség** (`*`) forrása és a kezdőszám nem.
5. **Mi TILTJA LE a film-rádiókat.** A 8.8 az *alapértelmezést* zárta le
   (`Preferences\FileExportMovie` → `setne` → a kiválasztott index), a
   letiltás viszont máshol dől el — a `movies` csoport `disable`
   mezőjét (`+0x20e`) író helyet kell megkeresni, feltehetően a
   kijelölés film-darabszámából.
6. **A `changeloc` (mappaválasztó, `0x00739850`) és a célmappa-név
   képzése (`0x0073b500`)** — a `CExportPrefsDialog::exportname` sablon.
7. **Nincs élő mintaadatunk**: az `]history:export` token a 859 elemű
   `.picasa.ini`-korpuszban **nullaszor** fordul elő, és a
   `research/testdata/` alatt sincs exportált mappa. A token pontos
   alakja tehát **nincs mintával igazolva**.

*(Egyik sem blokkolt: mind gépi úton eldönthető, csak drágább —
utasításszintű olvasás. A munkasorba kerültek.)*

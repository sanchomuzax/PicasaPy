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

#### 12.5/b A megerősítés: „Exported Pictures" egy KATEGÓRIA-tábla tagja (#1565)

A fenti következtetés önmagában egyetlen sztringbetöltésen állt. Független
megerősítés a `FUN_004a1560`-ból: ez a rutin egy **név → honosított címke**
táblát épít, és az `"Exported Pictures"` / `IDS_EXPORTED_CATEGORY` pár
pontosan ugyanabban a felsorolásban áll, mint

| angol név | erőforrás-kulcs |
|---|---|
| `My Albums` | `IDS_GOODCAT` |
| `Folders on Disk` | `IDS_FOLDERS` |
| **`Exported Pictures`** | **`IDS_EXPORTED_CATEGORY`** |
| `Labels` | `IDS_VIRTUALCAT` |
| `From Hello` | `IDS_HELLOCAT` |
| `Downloaded Albums` | `IDS_WEBCAT` |
| `Other Stuff` | `IDS_DEFAULTCAT` |
| `Edited Pictures` | `IDS_PICASAEDITSCAT` |
| `Hidden Folders` | `IDS_HIDDEN` |
| `Projects (internal)` | `IDS_PROJECTS` |

Ezek a `.picasa.ini` **`[Picasa] P2category`** értékei (#1029). Az
„Exported Pictures" tehát nem külön, fájlrendszerből listázó nézet, hanem
ugyanolyan **könyvtár-kategória**, mint a lemezen álló mappáké — a 859
fájlos valódi ini-korpuszban három mappa hordozza is ezt az értéket.

➡️ **Következmény nálunk (#1565):** az exportált mappának az INDEXBEN a
helye, különben a bal hasáb „Exportált képek" sora tartósan üres rácsot
nyit. A megvalósítás a `library_controller.indexExportedFolder`.

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

1. ~~**`0x0073f320` (9396 b) — a `CImageOutput` törzse**~~ —
   **LEZÁRVA** (2026-08-21, ld. a **13.** szakaszt): a váz, a
   mód-elágazás, az ini-írás és az időbélyeg utasításszinten.
2. ~~**Mikor íródnak ki a beállítások**~~ — **LEZÁRVA** (2026-08-21,
   ld. **13.7**): **OK-ra, egyetlen menetben**, a közös párbeszéd-lezáró
   (`0x008d2720`) hívja a `vt[0x164]`-et, ha a lezárási kód **0**. A
   **Mégse** ága a `vt[0x168]`-at hívja, ami a `CExportPrefsDialog`-nál
   az üres tő (`0x00b0d990`, egyetlen `ret`) — **Mégsére semmi nem
   íródik és semmi nem áll vissza**.
3. ~~**Mi fut le az export UTÁN**~~ — **LEZÁRVA** (13.2): a célmappa
   **megnyitása az Intézőben** (`ShellExecuteA`, feltételesen), majd
   `]history:export` token. **Indexelés és nézetfrissítés NINCS** a záró
   ágban — ez a kollázséhoz képest lényeges eltérés.
4. ~~**A sorszámozás pontos szabálya**~~ — **LEZÁRVA** (13.3): a
   szélesség a **kijelölt képek számának jegyszáma**, a sorszám
   **1-től** indul, az elválasztó **kötőjel**, utána a teljes eredeti
   fájlnév.
5. ~~**Mi TILTJA LE a film-rádiókat**~~ — **LEZÁRVA** (2026-08-21, ld.
   **13.10**): **a párbeszéd SAJÁT kódja tiltja**, ha a kijelölésben
   **egyetlen film sincs** (`0x007394b3` → `vt[0x114]("movies", 0)`). A
   filmjelzőt a létrehozó (`0x005312b0`) teszi a `[dlg+0xcd]`-be a
   `0x005c7990` vizsgálóból. **KÉT korábbi állításunk megdőlt** —
   ld. a szakasz elején.
6. ~~**A `changeloc` (mappaválasztó) és a célmappa-név képzése**~~ —
   **LEZÁRVA** (2026-08-21, ld. **13.8**): a gomb nyolc lépése; az
   alapértelmezett mappanév a **szövegtárból** (`export` / magyarul
   **`exportálás`**); a név **fájlnév-tisztításon** megy át
   (`0x009946f0`, tiltott halmaz `\ / : * ? " < > |`); a megjelenített
   útvonal **Wine-észleléssel** és a `ShowUnixPaths` kapcsolóval
   Unix-alakú is lehet (`0x0073a140`).
7. ~~**Nincs élő mintaadatunk** az `]history:export` tokenre~~ —
   **LEZÁRVA** (2026-08-21, ld. **13.9**). **A premissza volt hibás:** az
   `]history:*` **nem ini-token**, hanem az `albumdata_token.pmp`
   egy-egy **album-sorának** tokenje — ezért volt nulla találat az
   ini-korpuszban. A tulajdonos valódi adatbázisában **kettő él belőle**
   (`]history:email` = „Elküldve e-mailben", 294. sor; `]history:upload`
   = „Feltöltve", 295. sor). A token alakja **bizonyított** (a program a
   literált adja át, `0x007414dd`), tehát **exportot kérni a
   felhasználótól NEM kell**.

*(Egyik sem blokkolt: mind gépi úton eldönthető, csak drágább —
utasításszintű olvasás. A munkasorba kerültek.)*

---

## 12.3 A megvalósítás állapota (#1166, 2026-08-22)

A 8. és 12.1 szakasz működés-leletéből ez került be a PicasaPy-ba:

| lelet | állapot |
|---|---|
| `.picasa.ini` `caption` + `keywords` átvitele a célmappába | ✅ `export/exporter.py` `_write_ini_metadata` |
| célmappa-ütközés: kérdés + az ELŐZŐ album törlése | ✅ `exportOverwriteDialog` + `export_photos(purge_existing=…)` |
| a tíz hibaág az eredeti szövegeivel | ✅ `ExportMixin._export_error_text` (fajta → üzenet) |
| a mappanév alapértéke a forrásmappa neve, üresnél „export" | ✅ `defaultExportName()` |
| a hely alapértéke a korábbi, hiányában a képek mappája alatti gyűjtő | ✅ `defaultExportLocation()` + `rememberExportLocation()` |
| film-rádió (`Első képkocka` / `Teljes film`), tárolt alapértékkel | ✅ `exportMovieFull()` + `ExportSettings.movie_full` |
| `%0*d-%s` sorszámozás | ✅ már megvolt (#369), most őrizve |
| három belépési pont ugyanarra a párbeszédre | ✅ már megvolt, most őrizve |

**Ami továbbra sem került be** (kimondva, hogy ne látszódjon késznek):

- az **`]history:export` token**: a 13.9 szerint ez NEM ini-token, hanem
  az `albumdata_token.pmp` album-sora. Nálunk nincs élő PMP-tár, tehát a
  hű megfelelője egy virtuális „Exportálva" gyűjtemény lenne — önálló
  döntés, külön jegy;
- ~~a **képméret- és képminőség-vezérlők átépítése**~~ — **BEKERÜLT**
  (#1138, ld. a **14.** szakaszt);
- a **`scanfile` hibaág** kódútja: a fajta le van képezve az üzenetre, de
  a mi ürítésünk nem külön fájl-letapogatással dolgozik, ezért ma nem tud
  ilyen fajtát előállítani.

⚠️ **Egy eltérés a jegy összefoglalójától:** a #1166 táblája szerint „a
kimeneti mappa alapértelmezett neve `Exported Pictures`". A 12.1 MÉRÉSE
ezt nem támasztja alá: a mappanév alapértéke a **forrásalbum neve**
(`0x0073b500`), üres névnél a honosított `export`
(`CExportPrefsDialog::exportname`), a HELY alapértéke pedig a
`DefaultExportPath`, hiányában `Picasa\Exportálások\`
(`0x00738d16`). Az `Exported Pictures` literál a `CImageOutput`-ban él,
és nincs hozzá honosítási bejegyzés — a párbeszéd alapértékének tehát a
12.1 mérése a forrása, nem az összefoglaló.


## 13. A `CImageOutput` (`0x0073f320`) TÖRZSE — utasításszinten (2026-08-21, E2)

> *(Számozási megjegyzés: a lap 8., 9. és 10. száma korábban kétszer is
> kiosztásra került; ez a szakasz ezért 13., hogy ne ütközzön a 424. sor
> körüli „10. A TELJES ESEMÉNYKEZELŐ-TÉRKÉP"-pel.)*

A 9. szakasz 1. pontja: „sztringszinten feltárva, utasításszinten nem".
Most utasításszinten is megvan a váz — és vele a 3. és 4. pont is.

### 13.1 A függvény szerepe: KÖZÖS kimenet-motor

A 9396 bájtos rutin **négy kimeneti módot** szolgál ki egyetlen törzsben:
**exportálás**, **e-mail**, **feltöltés** és **képernyővédő-telepítés**.
A három ideiglenes mappa mindjárt az elején látszik: `temp\`
(`0x0073f343`), `upload\` (`0x0073f48e`), `temp\email\` (`0x0073f526`).

A módot a **záró elágazás** választja szét (`0x0074145b`-től):

| mód | mit tesz a végén | cím |
|---|---|---|
| **e-mail** | `]history:email` token a célmappára | `0x0074146b` |
| **exportálás** | **`ShellExecuteA(0, "open", <célmappa>, 0, 0, 5)`**, majd `]history:export` token | `0x007414af`, `0x007414dd` |
| **képernyővédő** | registry (`Software\Google\Google Photos Screensaver`, `AppPath`), majd `rundll32.exe desk.cpl,InstallScreenSaver %s` | `0x00741504`, `0x007415c3`–`0x007415e7` |

### 13.2 MI FUT LE AZ EXPORT UTÁN — a 9. szakasz 3. pontja LEZÁRVA

**Két dolog, ebben a sorrendben:**

1. **A célmappa megnyitása az Intézőben.**

   ```asm
   0x007414a8  push 5          ; SW_SHOW
   0x007414aa  push 0          ; lpDirectory
   0x007414ac  push 0          ; lpParameters
   0x007414ae  push eax        ; << a CÉLMAPPA útvonala
   0x007414af  push 0xc80fc0   ; "open"
   0x007414b4  push 0          ; hwnd
   0x007414b6  call dword ptr [0xc405e0]   ; ShellExecuteA
   ```

   **Feltételes**: a `0x00741477` (`cmp byte ptr [esp+0x181], 0`)
   jelzőre ez a lépés kimarad, és helyette a `[esp+0x183]` jelző áll 1-re
   (`0x00741481`).

2. **`]history:export` token** a célmappára — a könyvtárobjektum
   `vt[0x10]`-én át (`0x007414cd`–`0x007414e2`).

**Amit ez KIZÁR:** a záró ágban **nincs** indexelés-hívás és **nincs**
nézetfrissítés — ellentétben a kollázs mentésével, ahol mindkettő ott van
(`picasa-kollazs-felulet.md` 9.1/b 5.). Az exportált mappa tehát a
**figyelt-mappa-mechanizmuson** át kerül be, nem közvetlen paranccsal.

### 13.3 A SORSZÁMOZÁS — a 9. szakasz 4. pontja LEZÁRVA

A `0x0073ee70` mindössze **83 bájt**, és zárt alakban kiolvasható:

```asm
0x0073ee79  mov  dword ptr [esi], 0
0x0073ee7f  jbe  0x73ee92               ; ha a DARABSZÁM 0 -> szélesség 0
0x0073ee81  mov  eax, 0xcccccccd        ; a 10-zel osztás bűvös szorzója
0x0073ee86  mul  ecx
0x0073ee88  add  edi, 1                 ; szélesség++
0x0073ee8b  shr  edx, 3
0x0073ee8e  mov  ecx, edx               ; darabszám /= 10
0x0073ee90  jne  0x73ee81
   ...
0x0073eeab  add  ecx, 1                 ; << a sorszám 1-TŐL indul
0x0073eeaf  push edi                    ; a szélesség
0x0073eeb0  push 0xcb0178               ; "%0*d-%s"
```

```c
szélesség = a KIVÁLASZTOTT KÉPEK SZÁMÁNAK tízes számrendszerbeli jegyszáma;
sprintf(ki, "%0*d-%s", szélesség, index + 1, eredetiNév);
```

| kijelölt képek | a fájlnév alakja |
|---|---|
| 9 | `1-kep.jpg` … `9-kep.jpg` |
| 10 | `01-kep.jpg` … `10-kep.jpg` |
| 100 | `001-kep.jpg` … `100-kep.jpg` |

Elválasztó: **kötőjel**, és utána a **teljes eredeti fájlnév** (a
kiterjesztéssel együtt).

### 13.4 AZ EXPORTÁLT MAPPA `.picasa.ini`-je — csak KÉT kulcs

A kimenet mellé a Picasa ini-t is ír (`0x00740295`, `0x007403bc`;
a régi `Picasa.ini` alak is szerepel, `0x0074031a`), és **képenként
pontosan két kulcsot** tesz bele:

```asm
0x00740485  push 0xc7fad0   ; "caption"
0x0074048f  call 0x5ab210   ; ini-be írás
   ...
0x0074050d  push 0xc81848   ; "keywords"
0x00740517  call 0x5ab210
```

A **kulcsszavak vesszővel** összefűzve (`0x007404b8 push 0x2c` → a
`0x00985c00` karakter-hozzáfűző).

**Szűrő, vágás, csillag NEM kerül bele** — az exportált kép már
kirenderelt, a szerkesztési adatoknak nincs értelme. *(Ez egyben azt is
megmagyarázza, miért nem találtunk `]history:export` tokent a 859 elemű
ini-korpuszban: az exportált mappa ini-je más természetű.)*

### 13.5 AZ IDŐBÉLYEG — minden exportált fájl UGYANAZT kapja

```asm
0x00740c14  call GetSystemTime(&st)             ; EGYSZER, a ciklus ELŐTT
0x00740c27  call SystemTimeToFileTime(&st,&ft)
   ... a képenkénti ciklus ...
0x00740e51  push edx    ; lpLastWriteTime
0x00740e54  push ecx    ; lpLastAccessTime
0x00740e55  push edx    ; lpCreationTime
0x00740e57  call SetFileTime
```

**Mind a három időmező** (létrehozás, utolsó hozzáférés, utolsó írás)
ugyanarra az értékre áll — **az export INDULÁSÁNAK pillanatára** —,
minden exportált fájlon azonosan. Nem a forráskép ideje, és nem is
fájlonként külön „most".

### 13.6 A beállítások OLVASÁSA — és ami a 2. pontból megvan

A `CImageOutput` a beállításokat **olvassa**, nem írja. A sorrend a
törzsben: `EmailExportSize` (`0x0073f36f`), `EmailSinglePicture`,
`EmailMovie`, `FileExportMovie`, `UseHTMLMailer`, `ShadowsHTMLEmail`,
`UpsizeSmallImages`, majd az export-hármas: **`ExportWatermark`**
(`0x0073fae3`), **`ExportWatermarkText`** (`0x0073fb2c`),
**`ExportAddNumbers`** (`0x0073fba1`).

**Az ÍRÓ** a `0x00739960` (1426 b), és ez a **`CExportPrefsDialog`
vtable 89. rekesze** (`0x00c8b764 + 0x164 = 0x00c8b8c8`) — tehát a
dialógus saját metódusa, nem szabad függvény. **Hogy pontosan mikor
hívódik** (OK-ra, vagy vezérlőnként), az továbbra is nyitott: a
`0x164`-es rekeszre a szokásos `mov reg,[reg+0x164]` + `call reg`
mintával a `0x0073…` tartományban nincs találat.

### 13.7 MIKOR íródnak ki a beállítások — OK-ra, EGYSZERRE (2026-08-21, E3)

A 9. szakasz 2. pontja: „a `0x00739960` végigolvasása; **OK-ra, vagy
vezérlőnként?**" — **OK-ra, egyszerre.**

#### A bizonyíték: a KÖZÖS párbeszéd-lezáró

Az író (`0x00739960`) nem szabad függvény, hanem a **`CExportPrefsDialog`
vtable 89. rekesze**: `0x00c8b764 + 0x164 = 0x00c8b8c8`. A rekeszt egyetlen
helyről hívják — a **közös párbeszéd-lezáró**, `0x008d2720` (89 bájt):

```asm
0x008d272e  mov  dword ptr [esi + 0x94], eax   ; a lezárás adata
0x008d2734  mov  dword ptr [esi + 0x98], edi   ; << a LEZÁRÁSI KÓD
0x008d273a  jne  0x8d2758                      ; kód != 0 -> a másik ág
   ; --- kód == 0 (ELFOGADÁS) ---
0x008d273e  mov  eax, dword ptr [edx + 0x164]
0x008d2744  call eax                           ; << a BEÁLLÍTÁSOK KIÍRÁSA
0x008d2748  mov  eax, dword ptr [edx + 0x15c]
0x008d2751  call eax                           ; a záró lépés
   ; --- kód == 1 (MÉGSE) ---
0x008d275f  mov  eax, dword ptr [edx + 0x168]
0x008d2765  call eax                           ; MÁS metódus
0x008d276f  call [edx + 0x15c]
```

**Következmény:** a kilenc beállítás-kulcs **nem vezérlőnként** íródik ki
(a vezérlő-triggerek — 10.3, 10.4 — csak a párbeszéd belső állapotát
frissítik), hanem **egyetlen menetben, a párbeszéd elfogadásakor**.

#### Mégsére NEM történik semmi

A `CExportPrefsDialog` `vt[0x168]` rekesze
(`0x00c8b764 + 0x168 = 0x00c8b8cc`) a **`0x00b0d990`**, ami egyetlen
`ret` — az általános üres tő. Tehát a Mégse ága **sem nem ment, sem nem
állít vissza**: a beállítások egyszerűen érintetlenek maradnak.

*(A `vt[0x15c]` mindkét ágon lefut: `0x008d26d0`, 38 bájtos közös záró
lépés.)*

#### Mit jelent ez a megvalósításnak

| # | Viselkedés | Eredeti | Teendő |
|---|---|---|---|
| 1 | Mikor mentődnek a beállítások | **csak az elfogadáskor**, egy menetben | ne mentsünk vezérlőnként |
| 2 | Mégse | **semmit nem ír és nem állít vissza** | a párbeszéd bezárása elég |
| 3 | Vezérlő-triggerek | csak a párbeszéd belső állapotát frissítik | ugyanígy |

**Bizonyítottsági fok: megerősített** — a rekesz-cím számítással, a hívó
teljes törzsével, és a Mégse-ág üres tövének ellenőrzésével.

### 13.8 A `changeloc` mappaválasztó és a CÉLMAPPANÉV képzése (2026-08-21, E6)

A 9. szakasz 6. pontja. Mindkét fele megvan.

#### 13.8/a A `changeloc` gomb — `0x00739850` (272 b)

| lépés | cím | mit tesz |
|---|---|---|
| 1 | `0x00739878` | vezérlőnév-egyeztetés a `changeloc`-kal |
| 2 | `0x007398cd`–`0x007398d5` | **mappaválasztó megnyitása** egy globális objektum (`0xd67b54`) `vt[0x68]` rekeszén át |
| 3 | `0x007398dd`, `0x007398ed` | ha a visszaadott út **üres**, nem történik semmi |
| 4 | `0x007398f8` | a választott utat a `[dlg+0xc8]` szerkezet `+8` mezőjébe másolja |
| 5 | `0x00739902` | meghívja a **névképzőt** (`0x0073b500`) |
| 6 | `0x00739925` | a végére **egy `\`-t** fűz (a `0xc80910` konstans egyetlen fordított perjel) |
| 7 | `0x00739939` | a **megjelenítendő** alak előállítása (`0x0073a140` — lásd 13.8/c) |
| 8 | `0x00739955` | a párbeszéd lezárása (`0x008d2720` — ld. 13.7) |

#### 13.8/b A célmappanév — `0x0073b500` (`CExportPrefsDialog::exportname`)

```asm
0x0073b512  ; ha a javasolt név ([adat+8]) ÜRES -> a kimenet is üres
0x0073b597  push 0xcafb84   ; "CExportPrefsDialog::exportname"
0x0073b59c  mov  eax, 0xc81228   ; "export"   <- a TARTALÉK érték
0x0073b5a1  call 0x9ae560        ; szövegtár-feloldás
0x0073b5d8  call 0x9946f0        ; << FÁJLNÉV-TISZTÍTÁS
0x0073b631  push 0xc967c8   ; "%s\"
0x0073b638  call 0x40ea90        ; a kimenet += "<név>\"
```

**Két mért tény:**

1. **Az alapértelmezett mappanév a szövegtárból jön**, nem beégetve:
   kulcs `CExportPrefsDialog::exportname`, angolul **`export`**, magyarul
   **`exportálás`** (a `referencia/stringres-en-hu.tsv` szerint).
   *Vagyis magyar felületen az alapértelmezett célmappa neve
   „exportálás", nem „export".*

2. **A név fájlnév-tisztításon megy át.** A `0x009946f0` (808 b, 24 hívó)
   ismeri a Windows tiltott karakterhalmazát: **`\ / : * ? " < > |`**
   (a `0xca6a38` környéki `.rdata`-blokkban). Ugyanez a rutin szolgál ki
   minden más névképzést is a programban.

3. Az összefűzött alak **fordított perjelre végződik** (`"%s\"`).

#### 13.8/c A megjelenített útvonal — Picasa ALATT WINE-T ÉSZLEL

A `0x0073a140` (512 b) a megjelenítendő útvonalat állítja elő, és ez a
kör **váratlan leletet** adott:

```asm
0x0073a193  push 0xca99b4   ; "wine_get_unix_file_name"
0x0073a198  push 0xca99a8   ; "kernel32"
0x0073a19d  call [0xc40238] ; GetModuleHandle
0x0073a1a4  call [0xc40234] ; GetProcAddress
0x0073a1b3  cmp  byte ptr [0xd6fc60], 0    ; a gyorsítótárazott eredmény
0x0073a1bc  push 0xca4cc8   ; "ShowUnixPaths"
0x0073a1c1  push 0xc7eafc   ; "Preferences"
```

A Picasa **futásidőben megnézi, hogy Wine alatt fut-e** (a
`kernel32!wine_get_unix_file_name` létezésével), és ha a
`Preferences\ShowUnixPaths` be van kapcsolva, a felületen **Unix-alakú
útvonalat** mutat a Windows-alak helyett.

*A PicasaPy-ra ez nem közvetlen teendő (nálunk minden út natív), de
megerősíti, hogy a Wine-os futás a Picasa támogatott esete volt.*

### 13.9 Az `]history:export` token — NEM kell export a felhasználótól (2026-08-21, E7)

A 9. szakasz 7. pontja azt írta: *„Nincs élő mintaadatunk… a token
pontos alakja nincs mintával igazolva"*, és exportot kért a
tulajdonostól. **Erre nincs szükség — a kérdés a meglévő anyagból
eldőlt.**

#### A premissza volt hibás: NEM ini-token

Az `]history:*` **nem a `.picasa.ini`-be** kerül, hanem az
**adatbázisba**: az `albumdata_token.pmp` egy-egy **album-sorának** a
tokenje. A 859 elemű ini-korpuszban ezért volt nulla találat — **rossz
helyen kerestünk.** *(A `picasa-mappakezelo.md` 11.5 ezt már 2026-08-21-én
rögzítette; a két lap nem lett összekötve.)*

#### Élő bizonyíték — a tulajdonos valódi adatbázisából

`research/testdata/Picasa2/db3/albumdata_token.pmp` + a párhuzamos
`albumdata_name.pmp` (mindkettő 2371 sor) **sorindexre illesztve**:

| sor | token | a beépített gyűjtemény neve |
|---:|---|---|
| 0 | `]star` | **Csillagozott képek** |
| 292 | `]screensaver` | **Képernyővédő** |
| 293 | `]updated` | **Legutóbb frissítve** |
| **294** | **`]history:email`** | **Elküldve e-mailben** |
| **295** | **`]history:upload`** | **Feltöltve** |
| 2366 | `]search` | **Keresési eredmények** |

**A négyes családból kettő élő mintával megvan.** A hiányzó kettő
(`]history:output`, `]history:export`) egyszerűen azért nincs, mert ez a
felhasználó **soha nem használt Fájl ▸ Exportálást** — e-mailt és
feltöltést igen.

#### A négytagú család és a regisztráló

A négy literál a `.rdata`-ban **egymás után** áll, ami önmagában is
mutatja, hogy egy család:

| token | cím |
|---|---|
| `]history:email` | `0xc81238` |
| `]history:output` | `0xc81248` |
| `]history:upload` | `0xc81258` |
| `]history:export` | `0xc81268` |

Mind a négyet **ugyanaz a regisztráló** hozza létre: a `0x0041c340`
(10499 b), amelyben ott van a **négy csupasz módnév** is (`email`,
`output`, `upload`, `export`) a `]history:` előtag mellett. Ugyanez a
függvény kezeli a teljes `]`-token szótárat:

`]album`, `]album:`, `]album%d`, `]screensaver`, **`]hidden`**,
**`]edited`**, **`]revertable`**, `]web_`, és a négy `]history:`.

**Ezért a token alakja bizonyított**: a program a **literált** adja át
(`0x007414dd push 0xc81268`), és az `]history:email` élő mintája
igazolja, hogy a literál **változtatás nélkül** kerül a táblába.

#### ⚠️ Névcsapda: a `CThumbDB::Exported` kulcs NEM az exportot jelenti

| szövegtár-kulcs | angol | magyar | melyik sor |
|---|---|---|---|
| `CThumbDB::Emailed` | Emailed | **Elküldve e-mailben** | `]history:email` |
| **`CThumbDB::Exported`** | **Uploaded** | **Feltöltve** | **`]history:upload`** |
| `CThumbDB::RecentUpdate` | Recently Updated | Legutóbb frissítve | `]updated` |
| **`IDS_EXPORTED_CATEGORY`** | **Exported Pictures** | **Exportált képek** | az export gyűjteménye |

A `CThumbDB::Exported` kulcs **a feltöltés** gyűjteményét nevezi meg — aki
a kulcsnévből következtet, a rossz gyűjteményt címkézi „exportált"-nak.
Az export gyűjteménye egy **másik** kulcson él
(`IDS_EXPORTED_CATEGORY`), és ugyanez a szöveg szerepel a
`CImageOutput`-ban is (`0x0073f884`).

*(Ez a `tre-szovegforrasok` tanulság újabb esete: **azonosítóból soha ne
állíts jelentést**, ha van hozzá felirat.)*

### 13.10 MI TILTJA LE a film-rádiókat — a párbeszéd SAJÁT kódja (2026-08-21, E1/b)

> ⚠️ **KÉT KORÁBBI ÁLLÍTÁSUNK MEGDŐLT.** A lap eddig azt írta, hogy
> „az export-párbeszéd saját kódja tehát **NEM** tiltja le", és hogy
> „a csoport **címkéje fekete marad**". **Egyik sem igaz.**

#### A lánc — három lépés

**1. A kijelölés vizsgálata a párbeszéd LÉTREHOZÁSAKOR.** A
`0x005312b0` (610 b, `IDS_DEFAULT_EXPORT` / `Picasa Export`) két
vizsgálót futtat a kijelölésre, és az eredményüket a párbeszéd két
bájtjába teszi:

```asm
0x005313aa  call 0x5c7990                 ; „van-e legalább egy FILM?"
0x005313b5  mov  byte ptr [esp + 0x1c], al
0x005313b9  call 0x5c7ab0                 ; „van-e NEM-film?"
0x005313be  mov  dl, byte ptr [esp + 0x14]   ; a mentett első érték vissza
0x005313d9  mov  byte ptr [esp + 0xec], al   ; -> [dlg + 0xcc]
0x005313e0  mov  byte ptr [esp + 0xed], dl   ; -> [dlg + 0xcd]   << EZ a filmjelző
```

**2. A tiltás a párbeszéd FELÉPÍTÉSEKOR** (`0x00738c00`):

```asm
0x007394b3  cmp  byte ptr [ebp + 0xcd], bl   ; bl = 0
0x007394b9  jne  0x7394e8                    ; VAN film -> nem tilt
0x007394bb  push 0xca2b64                    ; "movies"
0x007394d5  mov  edx, dword ptr [edx + 0x114]
0x007394db  push ebx                         ; << az érték: 0 = TILTVA
0x007394e1  call edx                         ; vt[0x114]("movies", 0)
```

**3. A tiltó maga** — `vt[0x114]` = `0x008d2640`, a közös
párbeszéd-alaposztályé:

```asm
0x008d2649  mov  edx, dword ptr [eax + 0xa0]   ; vezérlő keresése NÉV szerint
0x008d2653  call edx
0x008d2659  je   0x8d268c                      ; nincs ilyen -> vége
0x008d2660  test bl, bl                        ; az érték
0x008d2662  jne  0x8d267e                      ; engedélyezés -> ugrás
0x008d2666  mov  edx, dword ptr [eax + 0x13c]  ; TILTÁSKOR: a fókuszált vezérlő
0x008d2670  cmp  eax, edi
0x008d2679  call edx                           ; ha ez volt, a FÓKUSZ ELVÉTELE
0x008d2680  mov  edx, dword ptr [eax + 0xc8]   ; a vezérlő engedélyezés-beállítója
```

#### A filmnek számító fájltípusok — HÉT kód

Mindkét vizsgáló (`0x005c7990` és `0x005c7ab0`) ugyanazt a hét
típuskódot ismeri (`0x005c7a17`–`0x005c7a38`, illetve
`0x005c7b37`–`0x005c7b58`):

> **8, 9, 10, 11, 12, 23 (0x17), 29 (0x1D)**

A két vizsgáló **ellentétes polaritású**:

| függvény | 1-et ad, ha | 0-t ad, ha | hova kerül |
|---|---|---|---|
| `0x005c7990` | van **legalább egy FILM** (`0x005c7a9f`) | egy sincs (`0x005c7a70`) | **`[dlg+0xcd]`** |
| `0x005c7ab0` | van **NEM-film** (`0x005c7bbf`) | mind film (`0x005c7b90`) | `[dlg+0xcc]` |

#### A szabály egy mondatban

> **A „Filmek exportálása" csoport akkor és csak akkor tiltott, ha a
> kijelölésben egyetlen film sincs.**

#### A képernyőkép is ezt mondja — és cáfolja a régi állításunkat

A tulajdonos képernyőképén
(`referencia/export-parbeszed-eredeti.png`) a **„Filmek exportálása:"
csoportcímke ugyanolyan szürke**, mint a két rádió — szemben a fekete
„Képminőség:" és „Vízjel:" címkékkel. Ugyanez a mintázat a letiltott
átméretezés-sorban („1100 **képpont**"). **A csoport tehát a címkéjével
együtt tiltott**, ahogy a keretrendszertől várható.

*(A korábbi „a címke fekete marad" megfigyelés téves volt; a mostani
kör a képet újranézve javította.)*
## 14. A FELÜLET átépítése (#1138, 2026-08-24)

> *(Számozási megjegyzés: a 12.x számok a lapon már kétszer ki vannak
> osztva — ld. a 13. szakasz elején —, ezért ez a szakasz 14.)*

A 12.3 „ami továbbra sem került be" listájáról a felületi tétel lekerült.
Ami a 6. szakasz „Kész, ha" listájából ezzel teljesült:

| „Kész, ha" | állapot | hol |
|---|---|---|
| minden felirat szó szerint a 2. szakaszból | ✅ | `app/i18n/picasapy_hu.ts`; őr: `tests/app/test_export_feliratok_1138.py` (a `.qm`-et tölti be, tehát azt méri, amit a felhasználó lát) |
| képméret: rádió + mező + 7 fogásos csúszka, a sor letiltva | ✅ | `ExportDialogs.qml`; a hét fogás egyetlen forrásból: `app/export_prefs.py` `SIZE_PRESETS` |
| képminőség: öt fokozat, váltakozó magyarázat, „Egyéni"-nél 21 fogásos csúszka | ✅ | `ExportDialogs.qml` — a `<multi>` FIX helyű `Item`, ezért a fokozat váltása nem méretezi át az ablakot (9.3/1) |
| „Automatikus" = a forrás kvantálótábláinak átvétele | ✅ | `export/exporter.py` `_encode_with_source_qtables` (Pillow `qtables=`, 4:2:0); mérce-őr: `tests/export/test_automatikus_minoseg_1138.py` |
| „Filmek exportálása" csoport | ✅ (#1166) — #1138: a **címke is szürkül** (13.10) | `ExportDialogs.qml` |
| vízjel: mező csak bejelölve, alatta kis betűs magyarázat | ✅ | `ExportDialogs.qml` |
| a párbeszéd megjegyzi az előző beállításokat | ✅ | `app/export_prefs.py` + `exportSettings()` / `saveExportSettings()`; a kiírás **egyetlen menetben, csak elfogadáskor** (13.7) |
| alapértelmezett célmappa `Picasa\Exportálások\` | ✅ (#1166) | őrizve |
| a mappanév-mező fókuszban, kijelölt tartalommal | ✅ (#1166) | őrizve |
| mappanév fájlnév-szűrt, méretmező csak számjegy | ✅ | `RegularExpressionValidator`-ok |

**Két kimondott eltérés az eredetitől:**

1. **A „Maximális" nálunk 100, nem 193.** Nem közelítés: a 11.3 szerint a
   kimenet bizonyíthatóan azonos (`q ≥ 100 → skála 0`).
2. **A `FileExportSize` kulcs kettéválik nálunk.** A 10.2 szerint a
   `sizeradio` írja (`0x00739a01`), a 10.1 szerint viszont az alapértéke
   **3** (`0x00738c58`) — egy kétállású rádiócsoport nem lehet 3. A kettő
   nem hozható közös nevezőre a meglévő méréssel, ezért nálunk **két**
   kulcs van: a csúszka állása és a rádió állása. A *viselkedés* hű (a
   párbeszéd mindkettőt megjegyzi); a registry-kulcs egy-az-egyben
   megfeleltetése **nyitva marad**.


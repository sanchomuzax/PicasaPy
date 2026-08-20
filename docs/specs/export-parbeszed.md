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

## 7. Ami NYITVA marad

1. **A „Normál", „Maximum", „Minimum" JPEG-minősége számokban.** A
   kezelőben a `85` az egyetlen jelölt (valószínűleg az „Egyéni"
   alapértéke). A három fokozat értékét **nem olvastam ki** — a
   `0x00738c00` mélyebb szétszedése vagy egy **mérés** döntené el:
   ugyanazt a képet exportálni négy fokozattal, és a kimenetek
   kvantálási tábláit összevetni. **Ez a mérés olcsó, és a tulajdonos
   gépén elvégezhető.**
2. **A 21 fogásos „Egyéni" csúszka leképezése.** 0…20 → milyen
   JPEG-minőség? Lineáris `q = 50 + 2,5·n`? Táblázatos? **Nem mértük.**
   Ugyanaz az exportálásos mérés eldönti.
3. **A `<multi>` váltásának pontos működése** (átméretezi-e az ablakot,
   ha csúszkára vált). A `width="fit"` miatt valószínű, de nem mért.
4. **A film-rádió alapértelmezése** (`FileExportMovie` alapértéke).

⚠️ Az 1. és 2. pont **ugyanazzal az egy méréssel** eldől: exportálni
egy képet mind az öt fokozattal (és az „Egyéni" csúszka néhány
állásával), majd a kimenetek DQT-jét összevetni. Amíg ez nincs meg,
a fokozatok számértéke **feltételes**, és a kódban ki kell mondani.

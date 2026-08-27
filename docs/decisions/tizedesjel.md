# ADR-004: Tizedesjel — a fényképezőgép számai PONT, a könyvtáré területfüggő

Dátum: 2026-08-15 · Státusz: ELFOGADVA · jegy: #664 (2. pont)

## A helyzet

Magyar rendszeren (`LANG=hu_HU.UTF-8`) a Qt alapértelmezett `QLocale`-ja
vesszőt ír tizedesjelnek. A `formatting.py` MINDEN számot ezen a
`QLocale()`-on át formázott, ezért a Tulajdonságok-panel és a
hisztogram-doboz alatti gép-összefoglaló `f/2,8`-at és
`Fókusztávolság: 6,72 mm`-t írt — a tesztek viszont `f/2.8`-at és
`6.72 mm`-t vártak. Nyolc bukó részfutásból kettő emiatt volt piros
(#664), és ezzel a push előtti tesztkapu is használhatatlanná vált.

A kérdés nem az volt, melyik oldalt hallgattassuk el, hanem hogy **mit
látott a magyar Picasa felhasználója.**

## A döntés

**Kétféle szám van, és a kettő máshogy formázódik:**

| számfajta | tizedesjel | hol |
|---|---|---|
| **a fényképezőgép adatai** (rekesz, fókusztávolság, 35 mm-egyenérték, záridő, tárgytávolság, GPS-koordináta és -magasság) | **PONT**, mindig, területi beállítástól függetlenül | `formatting._EXIF_LOCALE` (C-locale) |
| **a könyvtár adatai** (fájlméret, darabszám, eltelt másodperc, dátum és idő) | a felhasználó területi beállítása szerint — magyar rendszeren **VESSZŐ** | `QLocale()`, a hívótól |

Ez pontosan az eredeti Picasa viselkedése. Nem a mi találmányunk, és nem
is kompromisszum: a program két külön úton írta ki a számokat.

## A bizonyíték

### 1. A fényképezőgép-adatok formátumsztringjei — a magyar fordításban is `%3.1f`

A `Picasa3i18n.dll` `il_NerdView::N` sztringjei, a repóban is rögzítve
(`docs/specs/histogram-reference.md`, H.3 szakasz):

| # | angol | hivatalos magyar |
|---|---|---|
| 2 | `%1$s\nFocal Length: %2$3.1fmm\n` | `%1$s\nFókusztávolság: %2$3.1f mm\n` |
| 3 | `(35 mm equivalent: %3.0fmm)\n` | `(35 milliméteressel egyenértékű: %3.0f mm)\n` |
| 5 | `%2.1fs\n` | `%2.1f s\n` |
| 6 | `f/%3.1f\n` | `f/%3.1f\n` |

A fordító a **szöveget** és a szóközt magyarította, a **konverziót** nem —
és nem is tudta volna: a `%f` tizedesjelét futásidőben a C-futtatókörnyezet
dönti el. A `f/%3.1f` sor angolul és magyarul betűre azonos.

### 2. A bináris ezekre nem hív semmilyen területi formázót

A `Picasa3.exe` az EGÉSZ binárisban egyetlen helyről hívja a Windows
területi számformázóját (`GetNumberFormatA`, `KERNEL32.DLL` — a
`referencia/binary-index/imports.csv` szerint egyetlen importhely, egyetlen
hívó függvénnyel). Ennek a segédfüggvénynek öt hívója van; a
fényképezőgép-adatokat kiíró függvények (`il_NerdView`, `il_PrintExif`,
`Aperture: f/%0.1f`, az objektívleírás `f/%.2g-%.2g`-je) **egyik sincs
köztük** — azok a sima printf-burkolót hívják.

### 3. …viszont a fájlméretre igen — a pontot vesszőre cserélve

Az `il_FormatBigMB/GB/TB` ág (`%.1f MB`, `%.1f GB`) előbb `sprintf`-fel
formáz, **majd megkeresi a kapott sztringben a pontot**, és ha metrikus a
területi beállítás (`LOCALE_IMEASURE == '0'`), átadja a
`GetNumberFormat`-nak, ami a felhasználó tizedes- és ezreselválasztóját
teszi bele (a nem törő szóköz kezelésével együtt — épp a magyar/lengyel/
francia locale-ok miatt). Ugyanez fut a darabszámokra
(`il_GetSelectionInfo`: „%s kép", „%s a lemezen"), a keresési találatszámra
és az albumlistára.

Ez kétszeresen bizonyító erejű: egyrészt magyar Windowson a `2.4 GB`
tényleg `2,4 GB` lett, másrészt **maga a kód feltételezi, hogy a `sprintf`
pontot ad** — különben a pontkereső javítóág értelmetlen volna. A program
tehát végig C-locale-ban maradt, azaz minden `%f` alapból pontot írt.

### 4. A GPS-koordináta mindenütt pont

Az `.picasa.ini` `geotag=33.770556,-84.293055` alakja
(`docs/specs/picasa-ini-format.md`) és a Google Earth felé küldött
KML/JS (`<longitude>%f</longitude>`, `picasa.addMarker(%f,%f,%d,%d);`)
egyaránt ponttal ír. Vesszős tizedesjel mellett egy koordinátapár
(`47,5, 19,05`) ráadásul olvashatatlan lenne.

### 5. A nyelv és a területi beállítás a Picasában is különvált

A Picasának saját nyelvválasztója volt (`Lang::hu`), függetlenül a Windows
területi beállításától. Egy magyar nyelvű Picasa amerikai Windowson a
fájlméretet is ponttal írta; magyar Windowson vesszővel. A
fényképezőgép-számok **mindkét esetben** pontosak maradtak — pont
tizedesjellel.

## Mit jelent ez a kódban

- `formatting._EXIF_LOCALE` — modulszintű C-locale. Ezt kapják a
  fényképezőgép-eredetű számok az `exif_entries`-ben és a
  `camera_summary_text`-ben.
- A hívótól érkező `locale` marad mindenütt máshol: `format_size`,
  `long_date`, `photo_info_text` dátuma, `filter_status_text`
  (másodperc, GB), `status_text`.
- A `format_exposure` általános segédfüggvény maradt, a locale-t továbbra
  is a hívó adja — a fotós hívási helyeken az `_EXIF_LOCALE`-t kapja.

## Amit NEM csinálunk

- **Nem tesszük az egész felületet C-locale-ra.** A fájlméret és a
  dátum magyarul magyarul néz ki; ezt az eredeti is így csinálta, és a
  felhasználó is ezt várja.
- **Nem tesszük a tesztet területfüggővé.** Ebben az esetben a TESZT volt
  jó (`f/2.8`, `6.72 mm`) és a formázás rossz — a bizonyíték ezt mondja.
  A tesztek ezért változatlanul maradtak; a termékkód igazodott hozzájuk.

## A vállalt tévedés-irány

A magyar helyesírás szerint a `f/2,8` volna a szabályos. Vállaljuk az
eltérést, mert a rekeszérték nemzetközi fotós jelölés (a gépházon, az
objektíven és a fotós szaknyelvben is `f/2.8`), és mert az eredeti program
bizonyíthatóan így írta. A PicasaPy célja a Picasa újraírása, nem a
helyesírási szabályzat követése ott, ahol a kettő ütközik.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/formatting.py`
- **Őrzi:** `tests/app/test_formatting.py`

# Hisztogram-referencia és Picasa-összevetés (#236)

Ez a dokumentum leírja, hogyan hasonlítjuk össze a PicasaPy hisztogram-
megjelenítését az eredeti Picasa 3.x-ével, egy kicsi, **determinisztikus**
referencia-képkészlet segítségével.

## Miért kell ez?

> ⛔ **HELYESBÍTÉS (2026-08-16):** az alábbi mondat — „Ez a Picasa mintája" —
> **téves**. A Picasa **NEM a csúcshoz normalizál**, hanem az **átlaghoz**,
> és **összeadó** keverést használ, nem átlátszóságot. A visszafejtett,
> pixelpontos algoritmus: [`picasa-hisztogram.md`](picasa-hisztogram.md).

A hisztogram a `src/picasapy/app/histogram_helper.py` `compute_rgb_histogram`
függvényével készül. A normalizálás jelenleg **csatornánként a saját
csúcsához** történik (#232) — vagyis mindhárom görbe (R, G, B) kitölti a doboz
magasságát, egymástól függetlenül. ~~Ez a Picasa mintája~~, de a pontos alakot
gépi teszt nélkül nehéz garantálni. Ezért:

1. előállítunk néhány képet, amelynek hisztogramja **előre, fejben ismert**;
2. egy teszt igazolja, hogy a `compute_rgb_histogram` tényleg a várt alakot
   adja (csúcs-pozíciók / laposság);
3. egy renderelő PNG-be rajzolja a PicasaPy dobozát — ezt vetjük össze a
   felhasználó által **egyszer** elkészített Picasa-golden-screenshotokkal.

## A referencia-képek

A képeket a `tests/support/histogram_reference/generator.py` állítja elő
numpy-val (nincs bináris melléklet a repóban). A készlet 9 kép:

| Név | Kép | Várt hisztogram-alak |
|-----|-----|----------------------|
| `pure_red` | tiszta piros (255,0,0) | R-csúcs a legfelső binben (255); G, B üres (csak a 0-s bin) |
| `pure_green` | tiszta zöld (0,255,0) | G-csúcs a 255-ös binben; R, B a 0-s binben |
| `pure_blue` | tiszta kék (0,0,255) | B-csúcs a 255-ös binben; R, G a 0-s binben |
| `white` | fehér (255,255,255) | mindhárom csatorna csúcsa a 255-ös binben |
| `black` | fekete (0,0,0) | mindhárom csatorna csúcsa a 0-s binben |
| `mid_gray` | középszürke (128,128,128) | mindhárom csatorna csúcsa a 128-as (középső) binben, pontosan fedésben |
| `gray_ramp` | vízszintes szürke rámpa 0→255 | tökéletesen **egyenletes** (lapos) hisztogram mindhárom csatornán |
| `two_tone_64_192` | két-tónusú 50/50 (64 és 192 szürke) | két egyforma magas csúcs a 64-es és 192-es binben, minden csatornán |
| `rgb_gradient` | piros→zöld→kék átmenet | szélesen szórt eloszlás; mindhárom csatorna a teljes 0..255 tartományt bejárja |

A rámpa szélessége szándékosan 256px, hogy minden 0..255 intenzitás pontosan
egyszer forduljon elő oszloponként — így a hisztogram tökéletesen lapos.

Az egyes képek pontos, gép-olvasható várt alakja (csúcs-binek, laposság) a
`ReferenceImage.expected_peaks` / `flat_channels` mezőkben van, és ezt
ellenőrzi a `tests/app/test_histogram_reference.py`.

## A gépi (PicasaPy-oldali) ellenőrzés

Automatikusan fut a tesztcsomagban:

```bash
python3 -m pytest -q tests/app/test_histogram_reference.py
```

Ez a `compute_rgb_histogram`-ot futtatja a referencia-képekre, és igazolja a
dokumentált csúcs-pozíciókat / laposságot. Ha a normalizálási logika (#232)
megváltozik, ezek a tesztek azonnal jeleznek.

## A PicasaPy hisztogram-render PNG-be

A vizuális összevetéshez a `tools/histogram/render_reference.py` PNG-be
rajzolja a PicasaPy hisztogram-dobozát, **ugyanazzal a skálázással és
színvilággal**, mint a QML-oldali `HistogramBox.qml` (oszlopmagasság =
`érték * plot-magasság`, csatornánként 0.55 opacitású, egymásra kevert
piros/zöld/kék oszlopok):

```bash
QT_QPA_PLATFORM=offscreen python3 tools/histogram/render_reference.py \
    --out tools/histogram/out
```

A kimeneti könyvtárban minden képhez két PNG kerül:

- `<név>.png` — a **nyers referencia-kép** (ezt nyitod meg a Picasában);
- `<név>__hist.png` — a **PicasaPy hisztogram-doboz** renderje.

> **Megjegyzés a döntésről:** a golden-rendert nem valódi QML `grabToImage`-dzsel
> készítjük, mert az a headless (offscreen) környezetben törékeny és
> időzítés-függő (ez volt a #232 Canvas-problémájának gyökere is). Helyette a
> hisztogram-ADATOT rajzoljuk a QML-lel azonos képlettel — determinisztikus és
> gyors. A részletes indoklás a szkript docstringjében.

## A felhasználó teendője: Picasa-golden-screenshotok (EGYSZER)

Ezt a lépést elég **egyetlen alkalommal** elvégezni a Windows-os Picasa 3-ban;
utána a golden-képek referenciaként megmaradnak.

1. Futtasd a fenti render-szkriptet, hogy létrejöjjenek a nyers
   referencia-PNG-k (`pure_red.png`, `gray_ramp.png`, …) a `--out` könyvtárban.
2. Másold át ezeket a PNG-ket a Windows-gépre, ahol a Picasa 3 fut.
3. A Picasában nyisd meg egyesével a képeket. A hisztogram a jobb oldali
   panelen jelenik meg (ha nem látszik, kapcsold be a hisztogram-nézetet).
4. Készíts képernyőképet **csak a hisztogram-dobozról** (a doboz kereten
   belüli tartalmáról), és mentsd el a kép nevével, pl.
   `pure_red__picasa.png`, `gray_ramp__picasa.png`.
5. Tedd a `__picasa.png` fájlokat a `__hist.png` fájlok mellé.

## Az összevetés

Nyisd meg egymás mellett a `<név>__hist.png` (PicasaPy) és a
`<név>__picasa.png` (Picasa golden) képeket. Ellenőrizd:

- a **csúcsok ugyanabban a vízszintes pozícióban** vannak-e (bal szél = 0,
  jobb szél = 255);
- a **relatív magasságok** egyeznek-e (mivel mindkét oldal csatornánként a
  saját csúcsához normalizál);
- a lapos eseteknél (`gray_ramp`) mindkét oldal **egyenletesen kitöltött**-e.

Mivel a bin-pozíciókat a `test_histogram_reference.py` már gépi úton
garantálja, a Picasa-golden elsősorban azt igazolja, hogy a **megjelenítés
stílusa** (skálázás, normalizálás, színkeverés) is Picasa-hű — nem csak a
számítás.

## Ha a skála mégis eltér

Ez a tesztcsomag **kizárólag mérőeszköz** — nem javítja a
`histogram_helper.py` normalizálási logikáját (#232). Ha az összevetés során
kiderül, hogy a PicasaPy és a Picasa 3 hisztogram-skálája/alakja **eltér**
(pl. a Picasa globális csúcsra normalizál, nem csatornánkéntire, vagy más a
görbe), azt **ne** ebben a jegyben javítsd ki: nyiss egy **külön GitHub
issue-t** a konkrét eltérés leírásával (melyik referencia-képnél, milyen
irányú a különbség, a két PNG csatolva), és azon a jegyen keresztül döntsön a
felhasználó/csapat a normalizálás módosításáról.

---

# AZ EREDETI PICASA HISZTOGRAM-PANELJE (a binárisból, 2026-08-07)

Eddig a hisztogramunkat **kívülről**, screenshot-összevetéssel próbáltuk
hitelesíteni. A Picasa telepítéséből most előkerült a panel **belső
definíciója**: a `respack.yt` rétegei (`tools/picasa/respack.py`), a `.tre`
elrendezés-forrás és az `.exe` formátum-sztringjei.

A panel belső neve **`nerdview`** („nerd nézet") — a fejlesztők maguk hívták
így.

## H.1 A legfontosabb: MIBŐL számol a Picasa hisztogramot

A réteg típusa és paramétere önmagában megválaszolja a kérdést:

```
layer:nerdview/histogram(editpanel/previewimage): histo
```

A Picasa rajzolómotorjában van egy **beépített `histogram` rétegtípus**,
amelynek paramétere a **forrás-képcsomópont** — és az itt
**`editpanel/previewimage`**, azaz a **szerkesztő ELŐNÉZETI képe**.

Ebből két dolog következik, amit eddig nem tudtunk biztosan:

1. **A hisztogram a SZERKESZTETT képet mutatja**, nem az eredeti fájlt — a
   `filters=` lánc alkalmazása után. Ahogy húzod a derítőfény-csúszkát, a
   hisztogram él.
2. **Az előnézet felbontásán számol**, nem a teljes felbontáson. Ez
   gyakorlati engedmény a sebesség javára; a mi implementációnknak sem kell
   a teljes képet végigolvasnia — elég ugyanaz a preview-puffer, amit
   megjelenítünk.

## H.2 A panel pontos geometriája (képpontban)

> **#512 KORREKCIÓ (utólagos):** a lenti táblázat `#a88974` (meleg barna)
> panelháttér-értékét a #429-es kör kódba is átvitte, de a bejelentő
> **eredeti Picasáról készült képernyőképe világosszürke panelt mutat**, nem
> barnát. A képernyőkép — mint közvetlen vizuális bizonyíték — erősebb, mint
> ez a `respack.yt`-ből visszafejtett táblázat, ezért a kódban (`HistogramBox.qml`)
> a barna helyett a `Theme.chromeBg` (szürke króm-háttér) tokent használjuk.
> A táblázatot alább VÁLTOZATLANUL hagytuk (történeti feljegyzés, a
> geometria-adatok továbbra is hasznosak lehetnek), de a színoszlopnak ez a
> sora **megkérdőjelezett** — vagy rossz réteget olvasott ki a kinyerő
> eszköz, vagy a `respack.yt`-beli RGBA-RLE dekódolás hibázott ezen a
> rekordon. Újra-igazolás nélkül ne hivatkozz erre mint tényre.

A `respack.yt` rétegeinek határoló dobozaiból, közvetlenül:

| elem | pozíció → méret | szín |
|---|---|---|
| `nerdview` panel (`#rect: floater`) | 0,0 → **238×144** | háttér **`#a88974`** (meleg barna!) |
| `static(...): nvhead` — a cím | 13,4 → 100×11 | szöveg `#333333` |
| `rect: histoback` | 13,25 → **213×59** | átlátszó (alátét) |
| **`histogram(...): histo` — a rajzterület** | 13,25 → **213×59** | **`#ffffff` fehér** |
| `text: detail1` — bal oszlop | 13,82 → 138×41 | szöveg `#333333` |
| `text: detail2` — jobb oszlop | 157,82 → 69×41 | szöveg `#333333` |
| `#button: close` | 207,5 → 11×11 | a lebegő korszak maradványa |

Fontos részletek:

- **A rajzterület fehér hátterű**, 213×59 képpont — vagyis erősen **fekvő,
  ~3,6:1 arányú** doboz. A hisztogram tehát alacsony és széles, nem
  négyzetes.
- **A panel háttere `#a88974`**, meleg barna — nem szürke. Ez a Picasa
  szerkesztő-paneljének „bőr" tónusa.
- A kamera-adatok **két oszlopban** állnak (138 px + 69 px), nem egy
  blokkban.
- A szerkesztőbe ágyazva a panel `clip(nerdview)` alatt **238×110**-re van
  vágva — vagyis dokkolt állapotban a kamera-adatok alsó sora levágódik.
- A `.tre` forrásban a lebegő változat sorai **ki vannak kommentezve**
  (`#nerdview/floater: root`, `#Property round 5`, `#nerdview/close: root`):
  a 3.9-ben már dokkolt panel, korábban lekerekített sarkú, zárható
  lebegő ablak volt.
- A cím betűje `m_displayfont14` (a `fontmacros_win` szerint Praxis Semi
  Bold/Heavy, 14 pt).

## H.3 A kamera-adat blokk — pontos formátum

Az `.exe` `il_NerdView::N` format-sztringjei (angol + hivatalos magyar):

| # | angol | magyar |
|---|---|---|
| 1 | `No EXIF data available.` | `Nincs elérhető EXIF-adat.` |
| 2 | `%1$s\nFocal Length: %2$3.1fmm\n` | `%1$s\nFókusztávolság: %2$3.1f mm\n` |
| 3 | `(35 mm equivalent: %3.0fmm)\n` | `(35 milliméteressel egyenértékű: %3.0f mm)\n` |
| 4 | `1/%ds\n` | `1/%d s\n` |
| 5 | `%2.1fs\n` | `%2.1f s\n` |
| 6 | `f/%3.1f\n` | `f/%3.1f\n` |
| 7 | `ISO: %2d` | `ISO: %2d` |

Olvasat:

- A 2. sztring `%1$s`-e a **fényképezőgép neve**, utána új sorban a
  fókusztávolság — tehát a bal oszlop első sora a gép, alatta a mm.
- A záridő **két alakban**: 1 s alatt `1/%d s`, felette `%2.1f s`. Ez
  egyszerű, de fontos részlet — a magyar változatban **szóköz van** a szám
  és az `s` között, az angolban nincs.
- Ha nincs EXIF: **egyetlen sor**, „Nincs elérhető EXIF-adat."
- A gépnév **normalizálva** jelenik meg: az `.exe`-ben ott a
  `NIKON CORPORATION` → `NIKON` és az `OLYMPUS DIGITAL CAMERA` átírás —
  vagyis a Picasa kézzel takarítja a gyártói EXIF-szemetet.
- A mezőcímkék hivatalos magyar megfelelői: `Fényképezőgép` (Camera),
  `Rekesz` (Aperture), `ISO`.

## H.4 Amit ez a mi implementációnkról mond

- A **forrás kérdése eldőlt**: a szerkesztett előnézet a helyes bemenet
  (nálunk ma is ez, de eddig nem volt rá bizonyíték).
- A **doboz aránya** (213×59, fehér alapon) és a **kétoszlopos
  kamera-blokk** átvehető.
- A **normalizálás módja** (csatornánkénti vs globális csúcs) továbbra
  **nem derül ki** a binárisból — a `histogram` rétegtípus a rajzolómotor
  natív kódjában van, nem adatban. Ezt továbbra is a golden-összevetés
  dönti el (ld. a dokumentum eleje).

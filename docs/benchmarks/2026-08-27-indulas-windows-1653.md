# Indulási idő Windowson vs. Linuxon — mérési jegyzőkönyv (#1653)

A tulajdonos jelentése (2026-08-27, **v0.8.127**, Windows, forrásból
futtatva): *„A grafikus felület **33 sec** után kezd el megjelenni, második
indítás **25 sec**."* A fejlesztői gépen (Linux, RPi5) ugyanez **5,18 s**
(`2026-08-27-indulasi-ido-1601.md`), az eredeti Picasa 3 ugyanazon a gépen
**0–2 s**.

Ez a lap azt méri meg, **hol vész el a különbség** — és kimondja azt is,
amit innen nem lehet eldönteni.

## Mérőeszköz és a futások azonosítója

* `scripts/indulas_meres.py` — elindítja a programot alprocesszként
  bekapcsolt indulási idővonallal (`PICASAPY_STARTUP_TIMELINE=1`,
  `src/picasapy/perf/startup_timeline.py`), izolált adat-/gyorstár-
  könyvtárral, üres és szintetikus nagy könyvtárral. A jelentést a
  (mindig UTF-8) fájlból olvassa.
* `.github/workflows/indulas-meres.yml` — ugyanez `ubuntu-latest`-en ÉS
  `windows-latest`-en, offscreen módban, méretenként két egymást követő
  indítással.

**Három független mintavétel**, mind a `perf/1653-windows-indulas` ágon:
`33105401549`, annak újrafuttatása (`98635585153`…), és `33106909777`.
A legelső futás (`33105116153`) 2. indításai HIBÁSAK voltak — a mérőkocsi
az 1. futás jelentését olvasta vissza —, ezek nincsenek benne az
összesítésben; a hibát a `_egy_futas` „csak ÚJ fájlt fogadunk el"
javítása szüntette meg.

## 1. A szakaszos bontás egymás mellett

Ezredmásodperc, három minta minimuma és maximuma. „1. indítás" = hideg
index és hideg lapgyorstár, „2. indítás" = ugyanaz a környezet melegen.

| eset | minták | ÖSSZESEN | import | QML | könyvtár |
|---|---:|---:|---:|---:|---:|
| Linux, üres, 1. indítás | 3 | **1568–3080** | 341–553 | 1062–1614 | 4–5 |
| Linux, üres, 2. indítás | 2 | **991–1360** | 340–546 | 432–752 | 4–6 |
| Linux, 1000 mappa, 1. indítás | 3 | **2931–3394** | 1648–2072 | 999–1164 | 185–237 |
| Linux, 1000 mappa, 2. indítás | 2 | **1526–1580** | 545–558 | 732–779 | 189–193 |
| Windows, üres, 1. indítás | 3 | **3607–4468** | 490–706 | 2580–2774 | 8–11 |
| Windows, üres, 2. indítás | 2 | **1294–2179** | 466–689 | 677–980 | 8–11 |
| Windows, 1000 mappa, 1. indítás | 3 | **5388–7018** | 2244–3679 | 2155–2708 | 9–12 |
| Windows, 1000 mappa, 2. indítás | 2 | **1523–2420** | 558–670 | 803–1010 | 11–11 |

Teljes bontás egyetlen mintából (`33106909777`), hogy a kis tételek is
láthatók legyenek:

| szakasz | lin/0/1 | lin/0/2 | lin/1e3/1 | lin/1e3/2 | win/0/1 | win/0/2 | win/1e3/1 | win/1e3/2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Python- és PySide6-modulok betöltése | 341,3 | 340,0 | 1745,0 | 557,5 | 705,9 | 689,0 | 3044,8 | 558,2 |
| Qt-stílus és platform-kapcsolók | 0,2 | 0,1 | 0,2 | 0,2 | 3,6 | 3,2 | 2,9 | 2,5 |
| Qt-alkalmazás létrehozása | 1,7 | 1,7 | 2,6 | 2,7 | 13,8 | 12,0 | 15,3 | 9,1 |
| felület-betűtípus betöltése | 39,2 | 2,9 | 91,4 | 4,9 | 0,9 | 0,8 | 0,9 | 0,6 |
| fordítás betöltése | 0,1 | 0,1 | 0,1 | 0,1 | 0,4 | 0,2 | 0,3 | 0,1 |
| tárhely előkészítése (zár + migráció) | 1,8 | 179,2 | 4,9 | 2,4 | 8,5 | 344,1 | 7,8 | 28,7 |
| figyelt gyökerek beolvasása | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| hibanapló előkészítése | 0,1 | 0,1 | 0,3 | 0,2 | 0,7 | 0,5 | 0,5 | 0,4 |
| asztali bejegyzés telepítése | 40,2 | 0,2 | 22,6 | 0,4 | 14,7 | 0,7 | 12,3 | 0,5 |
| index megnyitása (séma + migráció) | 4,4 | 0,4 | 4,6 | 0,5 | **119,0** | 1,5 | **108,1** | 1,1 |
| ottragadt mappák takarítása (#58) | 0,1 | 0,1 | 0,3 | 0,1 | 0,9 | 0,3 | 0,5 | 0,2 |
| Kollázsok mappa önjavítása (#1075) | 1,2 | 0,8 | 1,9 | 1,2 | 3,5 | 2,0 | 2,8 | 1,6 |
| exportcélok visszavétele (#1565) | 0,0 | 0,0 | 0,0 | 0,1 | 0,1 | 0,1 | 0,0 | 0,0 |
| index előkészítése — utómunka | 1,8 | 0,1 | 1,6 | 0,1 | 26,1 | 0,5 | 25,2 | 0,4 |
| bélyegkép-gyorstár és fővezérlő | 3,4 | 3,9 | 5,5 | 5,4 | **60,6** | 43,0 | 42,1 | 35,3 |
| a bal hasáb mappafájának betöltése | 0,4 | 0,4 | 0,7 | 0,6 | 2,2 | 2,0 | 1,6 | 1,5 |
| a többi vezérlő létrehozása | 0,2 | 0,2 | 0,3 | 0,3 | 0,5 | 0,4 | 0,4 | 0,4 |
| QML-motor létrehozása és import-útvonalak | 1,6 | 1,7 | 2,1 | 2,2 | 4,2 | 3,3 | 3,2 | 2,6 |
| vezérlők regisztrálása a QML-kontextusban | 2,1 | 2,3 | 4,2 | 3,6 | **43,8** | 40,5 | 32,8 | 31,6 |
| **QML betöltése (Main.qml)** | 1100,7 | 431,6 | 1163,7 | 779,1 | **2579,9** | 980,1 | **2155,0** | 802,8 |
| az ablak első kirajzolt képkockája | 22,5 | 20,6 | 25,5 | 27,5 | 40,1 | 40,5 | 30,5 | 32,3 |
| könyvtár betöltése (a vezérlő indítása) | 3,6 | 3,6 | 218,6 | 189,2 | 11,1 | 11,1 | 9,2 | 10,6 |
| **ÖSSZESEN** | **1567,5** | **990,8** | **3297,4** | **1579,5** | **3643,7** | **2178,6** | **5498,6** | **1523,0** |

### Mit mond ez

1. **A `windows-latest` futó NEM reprodukálja a 33 másodpercet.** A
   legrosszabb windowsos mérésünk **7,0 s** (hideg indítás, 1000 mappa), a
   tipikus **3,6–5,5 s**. A Windows/Linux hányad **1,5–1,8×**, nem 6×.
   ⇒ **A ~6-szoros szorzó nem magától a Windowstól van**, hanem a
   tulajdonos gépének környezetétől.

2. **A Windows-többlet egyenletesen oszlik el a fájlt érintő tételeken.**
   A kis szakaszokon a hányad következetesen 10–30×: `index megnyitása`
   4,4 → 119,0 ms (27×), `vezérlők regisztrálása` 2,1 → 43,8 ms (21×),
   `bélyegkép-gyorstár és fővezérlő` 3,4 → 60,6 ms (18×). Abszolút értékben
   mindez együtt is csak ~0,2 s, de a **jellege** árulkodó: nem egyetlen
   hibás algoritmus, hanem a fájlműveletek egységára.

3. **Két tétel viszi az indulást mindkét platformon:** az importlánc és a
   QML betöltése. Windowson hidegen ez **3,3–3,7 s a 3,6–5,5 s-ból (77–91 %)**.

## 2. Méretfüggő-e? — NEM érdemben

A tulajdonos „egyre lassabb" panasza a méretfüggést tette fő gyanúvá. A
mérés ezt **nem igazolja** a felület megjelenéséig tartó szakaszra:

* Az EGYETLEN valóban méretfüggő szakasz a `könyvtár betöltése (a vezérlő
  indítása)`: Linuxon 4 ms (üres) → **185–237 ms** (1000 mappa). Windowson
  8–11 ms → **9–12 ms**, azaz ott nem is mérhető.
* ⚠️ Ez a szakasz ráadásul az **első kirajzolt képkocka UTÁN** fut
  (`application.py`, `frameSwapped` → `_start_and_finish`), tehát a
  tulajdonos által mért „a felület megjelenik" pillanatba **bele sem
  tartozik**. Ez a #1601 javításának közvetlen következménye.
* A „nagy" lábon látszó nagy importidő (Windowson 2244–3679 ms a 490–706 ms
  helyett) **nem méretfüggés, hanem mérési műtermék**: a mérés előtt épp
  2 000 fájlt hoztunk létre, ami kiszorította a lapgyorstárat. Az importlánc
  a fotókönyvtárat bizonyíthatóan nem olvassa — a `mark_from` a belépési
  ponttól a `run()` első soráig mér.

**Ez a műtermék viszont maga a legfontosabb lelet** (ld. 4. pont).

## 3. Az indulás I/O-terhelése — a döntő szám

`scripts/indulas_meres.py --io-terheles`: mennyi Python-forrást és mennyi
natív kódot kell BEOLVASNI ahhoz, hogy az indulási importlánc lefusson.
Minden sor külön processzben mérve; a natív oldal Windowson
`EnumProcessModules`, Linuxon `/proc/self/maps`.

| import | py fájl | py MB | natív fájl | natív MB |
|---|---:|---:|---:|---:|
| **windows-latest** (`33106909777`) | | | | |
| (semmi) | 61 | 2,8 | 31 | 31,5 |
| `cv2` | 182 | 9,2 | 39 | **138,4** |
| `PySide6.QtQuick` | 96 | 20,9 | 79 | 108,4 |
| `picasapy.app.application` | **565** | **41,1** | 114 | **249,1** |
| **ubuntu-latest** (`33106909777`) | | | | |
| (semmi) | 72 | 5,6 | 23 | 39,5 |
| `cv2` | 196 | 21,0 | 55 | **233,4** |
| `PySide6.QtQuick` | 109 | 26,3 | 87 | 149,3 |
| `picasapy.app.application` | **583** | **58,3** | 149 | **379,6** |
| **RPi5, Debian-csomagolt cv2** | | | | |
| `cv2` | 168 | 16,5 | 390 | **430,7** |
| `picasapy.app.application` | **557** | **51,1** | 434 | **506,4** |

Független ellenőrzés `strace`-szel (RPi5, üres könyvtár, TELJES indulás a
kész ablakig, nem csak az importlánc):

```
openat összesen : 3741   (sikeres 3037, sikertelen 704 = útvonal-keresés)
külön fájl      : 2131
együtt          : 534,9 MB
64 KB alatti    : 1592 fájl
```

A két, egymástól független módszer ugyanazt adja (506,4 MB importlánc vs.
534,9 MB teljes indulás) — a mérés tehát nem módszer-műtermék.

**Az indulás Windowson ~680 fájl / ~290 MB beolvasása** (565 Python-fájl
41 MB + 114 natív modul 249 MB). Ebből a `cv2` egymaga **138 MB (56 %)**.

## 4. A domináns ok — bizonyítékkal

**Az indulás nem processzor-, hanem fájlbeolvasás-korlátos.** Ez nem
következtetés, hanem mérés: ugyanazon a `windows-latest` futón, ugyanazzal
a commit-tal, az importlánc **490 ms** meleg lapgyorstárral és **3679 ms**
hideggel — **7,5-szeres különbség, kizárólag a fájlrendszer állapotától.**
Linuxon ugyanez 341 ms → 2072 ms (6,1×).

Ez pontosan akkora szorzó, amekkora a tulajdonos 33 s-ához kell a mi 5 s-unkból.

⇒ **A domináns ok: a tulajdonos gépén a ~290 MB / ~680 fájl beolvasása
nagyságrendekkel drágább, mint a CI-futón.** A kód nem lassabb ott — a
bájtok kerülnek többe. 290 MB effektív ~10–12 MB/s átvitellel (forgólemez
véletlen hozzáféréssel, minden induláskor újravizsgáló víruskereső, vagy
hálózati meghajtó) pontosan a 25–33 másodperces tartományt adja.

Ezt támasztja alá a második indítás aránya is: nálunk 3,6 s → 1,9 s
(**1,9×** nyereség a meleg gyorstárból), a tulajdonosnál 33 s → 25 s
(**1,3×**). Nála tehát a gyorstár érdemben **nem segít** — ez az AV-újravizsgálat
és a hálózati/lassú tároló jellemző mintája, nem a lassú processzoré.

## 5. Amit innen NEM lehet eldönteni

Ezek a jegyben felsorolt gyanúk közül azok, amelyeket a GitHub-futó
**szerkezetileg nem tud eldönteni** — nem „valószínűtlen", hanem **nem
mérhető innen**:

* **Windows Defender / valós idejű vizsgálat a tulajdonos gépén.** A
  hosztolt futó saját Defender-beállítással és NVMe-lemezzel megy; a
  kizárási listák és a lemez sebessége nem az övé.
* **Hálózati útvonal.** A tulajdonos NAS-on tartja a fotókat. Azt viszont
  **nem tudjuk**, hol van maga a *program* (a forrásfa, a virtuális
  környezet, a PySide6/OpenCV DLL-jei) — pedig a 290 MB abból jön, nem a
  fotókból. Ha a telepítés hálózati vagy lassú meghajtón van, az önmagában
  megmagyarázza a 6×-ot.
* **Valódi GPU és megjelenítő.** A CI offscreen fut. A tulajdonos gépén a
  Qt Quick D3D/RHI-t inicializál és shadereket fordít — ez a mi mérésünkben
  **egyáltalán nem szerepel**, tehát a QML-szakasz nála nagyobb is lehet,
  mint amit mérünk.
* **A tulajdonos könyvtárának valódi mérete.** 1000 mappáig mértünk; a
  méretfüggés eddig elhanyagolható, de a felső határt nem ismerjük.

Amit a mérés **kizár**: hogy a 33 s a fotókönyvtár méretéből, az
indexoldali munkából (a #1601 után), a `.picasa.ini`-söprésből vagy egy
Windows-specifikus algoritmikus hibából jönne. Ezek együtt is
**0,2 s alatt** vannak a windowsos mérésben.

## 6. Miért nincs időalapú őr a CI-n

A jegy időkorlátos őrt kért a Windows-lábra. **Megmértük, és ez nem
járható:** ugyanaz a szakasz ugyanazon a commit-on 490 és 3679 ms között
szór (7,5×), a teljes indulás 3607 és 7018 ms között. Egy küszöb, ami ezt
nem veri ki hamisan, ~10 s-nál lenne — az pedig egy kétszeres lassulást
már nem fogna meg, viszont minden PR-hez 5 perc CI-időt adna.

Helyette **determinisztikus** őr készült — `tests/perf/test_indulas_io_terheles_1653.py` —,
amely a beolvasandó MENNYISÉGET rögzíti (nincs óra, nincs terhelésfüggés),
és a rendes tesztkészlettel minden PR-en lefut. Mutációs bizonyíték a
tesztlap fejlécében: egyetlen `import matplotlib.pyplot` az
`application.py`-ban 557 → 723 modulra viszi az indulást, és az őr bukik.

## 7. Hogyan mérj újra

```bash
# CI, mindkét platformon (az ág beolvasztása után):
gh workflow run indulas-meres.yml --ref main
gh run watch <id>; gh run view <id> --log

# helyben, egy platformon:
python3 scripts/indulas_meres.py --mappa-szam 0    --futasok 2
python3 scripts/indulas_meres.py --mappa-szam 1000 --futasok 2
python3 scripts/indulas_meres.py --importtime
python3 scripts/indulas_meres.py --io-terheles

# az őr:
python3 -m pytest tests/perf/test_indulas_io_terheles_1653.py -q
```

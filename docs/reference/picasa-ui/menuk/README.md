# Az eredeti Picasa 3.9 menüi — referencia-képernyőmentések

A tulajdonos gépén készültek, a magyar nyelvű Picasa 3.9-ből, a `Fájl` menü
megnyitva. Ugyanaz a menü **négy Windows-kijelzőskálázáson** — ettől a
méretek nemcsak leolvashatók, hanem a skálázási törvény is ellenőrizhető.

| fájl | kijelzőskálázás | kép mérete |
|---|---|---|
| `01-fajl-100.png` | 100% | 349 × 548 |
| `01-fajl-125.png` | 125% | 433 × 676 |
| `01-fajl-150.png` | 150% | 520 × 808 |
| `01-fajl-175.png` | 175% | 604 × 944 |

A jegy: **#1774** (a felső menüsor szerkezete és a menük valós szélessége).
A többi menü (Szerkesztés, Nézet, Mappa, Kép, Létrehozás, Eszközök, Súgó)
a tulajdonos `Picasa-3-menuk` mappájában van, ide még nem került be.

## A mért méretek (a `01-fajl-*` képekről)

A popup a `#F9F9F9` háttérről és az azt körülvevő `#E5E5E5` keretről
azonosítható; a szöveg bal széle a legszélső sötét (< 130 szürkeérték)
képpont-oszlop a popup törzsében.

| skálázás | popup teljes szélessége | szöveg bal széle a kerettől | jobb margó az utolsó szövegképpont után |
|---:|---:|---:|---:|
| 100% | **345 px** | **39 px** | 27 px |
| 125% | 430 px | 48 px | 33 px |
| 150% | 515 px | 57 px | 39 px |
| 175% | 601 px | 67 px | 45 px |

⇒ **Minden méret együtt skálázódik a DPI-vel** (345 · 1,25 ≈ 431 a mért 430;
345 · 1,5 ≈ 518 a mért 515; 345 · 1,75 ≈ 604 a mért 601 — az eltérés a
betűmetrika kerekítése). Nincs tehát külön „nagy DPI-s" elrendezés: a
100%-os számok a mérce, a többi ebből jön.

## Amit ez a mi menüinkről mond

A `PicasaMenuBar` ugyanezen menüje mérve (Fusion, magyar fordítás,
`QQuickStyle.setStyle("Fusion")`): **330,3 px**, és a felirat a **26.**
képponton kezdődik (6 px tétel-margó + 20 px pipa-vályú) az eredeti 39-cel
szemben. A mi menüink közül hatot ráadásul a `PicasaMenu.qml` 200 képpontos
alsó korlátja tart mesterségesen szélesen (Indexkép felirata, Mappanézet,
Mozgófilm, Kísérleti, Nyelv, Feltöltés) — az eredetiben ilyen korlát nincs.

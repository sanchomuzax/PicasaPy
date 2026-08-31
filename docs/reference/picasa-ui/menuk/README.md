# Az eredeti Picasa 3.9 menüi — referencia-képernyőmentések

A tulajdonos gépén készültek, a magyar nyelvű Picasa 3.9-ből, menünként
kinyitva. A jegy: **#1774** (a felső menüsor szerkezete és a menük valós
szélessége). A képek a repóban élnek, hogy a felhő-sessionből is mérhetők
legyenek (#326).

| fájl | menü | skálázás |
|---|---|---|
| `01-fajl-100.png` · `-125` · `-150` · `-175` | Fájl | 100 / 125 / 150 / 175% |
| `02-szerkesztes-100.png` | Szerkesztés | 100% |
| `03-nezet-100.png` | Nézet | 100% |
| `04-mappa-100.png` | Mappa | 100% |
| `05-kep-100.png` | Kép | 100% |
| `06-letrehozas-100.png` | Létrehozás | 100% |
| `07-eszkozok-100.png` | Eszközök | 100% |
| `08-sugo-100.png` | Súgó | 100% |

## 1. A menüsor sorrendje — a képekről leolvasva

Minden mentésen látszik a menüsáv is. Együtt kiadják a teljes sorrendet:

**Fájl · Szerkesztés · Nézet · Mappa · Kép · Létrehozás · Eszközök · Súgó**

Ez megegyezik a mai `PicasaMenuBar.qml` sorrendjével. (A szövegtár ábécérendű,
abból a sorrend nem jött volna ki — ld. #1774.)

## 2. A mért méretek (100%)

A popup a `#F9F9F9` háttérről és az azt körülvevő `#E5E5E5` keretről
azonosítható. A „szöveg bal széle" a feliratok leggyakoribb kezdőoszlopa a
popup bal keretétől; a „jobb margó" az utolsó sötét képponttól a jobb keretig.

| menü | popup szélessége | szöveg bal széle | jobb margó |
|---|---:|---:|---:|
| Fájl | **345** | 39 | 26 |
| Nézet | 314 | 38 | 15 |
| Mappa | 314 | 37 | 16 |
| Kép | 310 | 36 | 16 |
| Szerkesztés | 283 | 33 | 26 |
| Súgó | 273 | 36 | 27 |
| Létrehozás | 267 | 37 | 16 |
| Eszközök | **254** | 36 | 15 |

Két állandó olvasható ki:

- **A felirat ~36–39 képponttal beljebb kezdődik** a popup bal keretétől.
  Ez a pipa/ikon-vályú. A `03-nezet-100.png`-n a pipák a **12.** képponton
  kezdődnek, tehát a vályú nagyjából a 12–30. képpont között van, és a
  szöveg csak utána indul — **a pipa és a felirat sosem fedi egymást.**
- **A jobb margó kétféle**: ahol csak gyorsbillentyű van (Fájl, Szerkesztés,
  Súgó) **26–27 px**; ahol almenü-nyíl is (Nézet, Mappa, Kép, Létrehozás,
  Eszközök) **15–16 px** — a nyíl ül a maradék helyen.

## 3. A DPI-skálázás törvénye (a `01-fajl-*` négy változatából)

| skálázás | popup szélessége | szöveg bal széle | jobb margó |
|---:|---:|---:|---:|
| 100% | 345 | 39 | 27 |
| 125% | 430 | 48 | 33 |
| 150% | 515 | 57 | 39 |
| 175% | 601 | 67 | 45 |

Minden méret együtt skálázódik a DPI-vel (345 × 1,25 = 431 a mért 430 ellen;
× 1,5 = 518 a mért 515 ellen; × 1,75 = 604 a mért 601 ellen — az eltérés a
betűmetrika kerekítése). **Nincs külön „nagy DPI-s" elrendezés: a 100%-os
számok a mérce.**

## 4. Összevetés a mai PicasaPy-vel

A `PicasaMenuBar` menüi mérve (Fusion stílus, magyar fordítás):

| menü | eredeti | nálunk | eltérés |
|---|---:|---:|---:|
| Fájl | 345 | 330,3 | −15 |
| Szerkesztés | 283 | 304,0 | **+21** |
| Nézet | 314 | 244,3 | **−70** |
| Mappa | 314 | 249,9 | −64 |
| Kép | 310 | 306,0 | −4 |
| Létrehozás | 267 | 225,0 | −42 |
| Eszközök | 254 | 209,3 | −45 |
| Súgó | 273 | 281,5 | +9 |

Az eltérés **mindkét irányba** kilóg, −70-től +21 képpontig. Egy részét a
nálunk hiányzó menütételek magyarázzák (#1397), a másik részét az, hogy a
szélességünk nem az eredeti szabályából áll elő. A felirat nálunk a **26.**
képponton kezdődik (6 px tétel-margó + 20 px pipa-vályú) az eredeti ~37-tel
szemben, és hat menünk szélességét a `PicasaMenu.qml` 200 képpontos alsó
korlátja adja, nem a tartalom.

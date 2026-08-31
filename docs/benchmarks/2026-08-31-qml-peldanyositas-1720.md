# A QML-komponensek példányosítása — melyik komponens viszi (#1720)

**Mikor:** 2026-08-31 · **Gép:** Raspberry Pi 5, Linux ARM64, 4 mag ·
**Qt:** PySide6 6.8.2.1 · **Platform:** `offscreen` · **Gyorsítótár:** meleg
(`.qmlc` kiírva, minden mérés előtt bejáratva)

A #1719 kettébontotta a QML-betöltés költségét: **fordítás ~3774 ms**
(a #1719 hatóköre) és **példányosítás ~3600 ms**. Ez a lap a MÁSODIKRÓL
szól — arról, ami meleg gyorsítótárral is megmarad.

## 1. Hogyan mértük

A gép a mérés alatt **terhelt volt** (`load average` 6–10, párhuzamos
munkamenetek). Ezért két, egymástól független mérőszámot használtunk, és a
következtetést a determinisztikusra bíztuk:

| mérőszám | mit mond | zaj |
|---|---|---|
| **felépült QObjectek száma** | a példányosítás MUNKAMENNYISÉGE | **nincs** — kétszer futtatva bájtra ugyanaz |
| `engine.load()` ideje | amit a felhasználó vár | ±60% ugyanazon a fán, percek alatt |

⚠️ A #1653/#1689 tanulsága, hogy egy időküszöbre épített őr terhelés alatt
használhatatlan. Az őr (`tests/app/qml_functional/test_qml_peldanyositas_or_1720.py`)
ezért **objektumszámot** mér, nem időt.

**A bontás módszere** (nem becslés, nem tippelés): a betöltött `Main.qml`
objektumfáját bejárjuk, és minden `QObject`-et ahhoz a legfelső saját
komponenshez könyvelünk, amelyik az ág mentén először előfordul. A Qt a
QML-ben definiált típusoknak `<Név>_QMLTYPE_<n>` osztálynevet ad, tehát a
hozzárendelés **egyértelmű és in situ** — nem izolált próbából származik.

Az izolált mérés (`QQmlComponent.create()` fájlonként) is elkészült, de a
ms-értékei terhelés alatt **3×-os szórást** mutattak (`PicasaMenuBar`
858 → 269 ms két kör között), ezért rangsorolásra alkalmatlan. A ms-eket
lentebb az A/B-ablációból származó **0,15 ms/objektum** átváltással adjuk
meg — és ezt a számot MÉRTÜK, nem feltételeztük (ld. 4. pont).

## 2. A bontás — mi épült fel induláskor (a #1720 ELŐTT)

Összesen **20 558 QObject**.

| befoglaló komponens | objektum | a fa %-a | ~ms |
|---|---:|---:|---:|
| `PhotoViewer` (néző + szerkesztő) | 3542 | 17,2% | ~530 |
| `PicasaMenuBar` | 2963 | 14,4% | ~445 |
| `FolderPane` (bal hasáb) | 2494 | 12,1% | ~375 |
| `CollagePanel` | 1751 | 8,5% | ~260 |
| `TagsPanel` | 1596 | 7,8% | ~240 |
| `OptionsDialog` | 1548 | 7,5% | ~230 |
| `FileOpsDialogs` | 1109 | 5,4% | ~165 |
| `ExportDialogs` | 914 | 4,4% | ~135 |
| `PhotoContextMenu` | 507 | 2,5% | ~75 |
| `ImportSourceDialog` | 488 | 2,4% | ~75 |
| a többi 20+ párbeszéd és panel | ~3646 | 17,7% | ~545 |

### A legnagyobb egyetlen tétel KERESZTBE fekszik ezen a táblán

A befoglaló bontás elrejti a valódi bajnokot. Típusonként összesítve:

| típus | példány | objektum | a fa %-a |
|---|---:|---:|---:|
| **`TextFieldContextMenu`** | **40** | **4920** | **23,9%** |
| `PicasaMenuItem` | 119 | 2023 | 9,8% |
| `PicasaButton` | 166 | 1198 | 5,8% |
| `PanelButton` | 58 | 996 | 4,8% |

A `TextFieldContextArea` (#422) **minden** szövegmező alá betett egy hét
tételes jobbklikk-menüt, és mind a **40** felépült induláskor — ~123
objektum darabonként. A felhasználó ezek 99%-át soha meg sem nyitja.

## 3. Mit halasztottunk el

### a) A szövegmezők jobbklikk-menüje — **−5562 objektum**

A `TextFieldContextArea.qml` a menüt `Component`-be tette, és az első
jobbklikkre hozza létre (`createObject(area)` — ugyanaz a szülő, tehát a
`popup()` viselkedése változatlan). **Egyetlen fájl, 40 helyszín.**

### b) Tizenhárom ritkán használt párbeszéd — **−2923 objektum**

Új típus: `PicasaPy/DeferredDialog.qml` (`Loader`, `active: false`). A
becsomagolt párbeszéd az első megnyitáskor épül fel.

`OptionsDialog` · `ExportDialogs` · `ImportSourceDialog` ·
`FolderManagerDialog` · `WebExportDialog` · `PrintDialog` ·
`FaceScanDialog` · `DedupDialog` · `SaveDialogs` · `EditOverwriteDialog` ·
`MoveDatabaseDialog` · `CompactDatabaseDialog` · `AboutDialog`

## 4. A nyereség — azonos módszerrel, előtte/utána

**Munkamennyiség** (determinisztikus):

| | objektum |
|---|---:|
| előtte | 20 558 |
| utána | **12 073** |
| nyereség | **−8485 (−41,3%)** |

**Idő** — a két fát **váltogatva** mértük (`elotte, utana, elotte, …`),
8-8 futás, azonos processzalakban, meleg gyorsítótárral; a váltogatás azért
kell, mert a gép terhelése percek alatt is elmozdul:

| | min | medián | max |
|---|---:|---:|---:|
| előtte | 2524 ms | 3012 ms | 4052 ms |
| utána | **1705 ms** | **2201 ms** | 3061 ms |
| nyereség | **−820 ms (−32%)** | **−811 ms (−27%)** | |

⇒ **0,145 ms/objektum** — ebből az átváltásból származnak a 2. pont
ms-becslései.

Az arány (idő −27…32% vs. objektum −41%) azért nem egyezik, mert a
`engine.load()` idejének egy része **nem** példányosítás: a 141 `.qmlc`
beolvasása és a típusgráf felállítása meleg gyorsítótárral is megtörténik.

## 5. Amit SZÁNDÉKOSAN nem halasztottunk el

Mindegyikre önálló jegy nyílik; itt a mért ok:

| komponens | objektum | miért nem most |
|---|---:|---|
| `PicasaMenuBar` | 2963 | induláskor látszik; a Qt Quick Controls `MenuBar` a `Menu`-ket mohón építi, lustításuk saját kutatás |
| `PhotoViewer` | 2847 | a `window.minimumHeight: photoViewer.requiredHeight` **kötés** induláskor kiértékelődik (#641) — halasztva az ablak minimuma elszállna |
| `FolderPane` | 1660 | induláskor látszik |
| `CollagePanel` | 1334 | a `Loader` `active`-ja a kollázs záródásakor visszabillenne, és a panel a saját `finishSave()`-je közben bomlana le |
| `FileOpsDialogs` | 553 | ⚠️ a `FolderPane.qml:924` `fileOpsController.moveFolder()`-t hív a **fa húzásából** — a haladás- és hibapárbeszéd nélküle NÉMÁN elveszne |
| `CreateDialogs` | 306 | ⚠️ `onCollageFailed` a `CollagePanel` által indított kollázs hibáját is fogadja |
| `PhotoContextMenu` | 507 | egyetlen belépési pont, de 6 tesztfájl közvetlenül keresi meg |

A `FileOpsDialogs` és a `CreateDialogs` sora a lap **legfontosabb
negatív lelete**: mindkettő „nyilvánvaló" `Loader`-jelölt, és mindkettő
némán tett volna tönkre egy működő utat.

## 6. Az őr

`tests/app/qml_functional/test_qml_peldanyositas_or_1720.py` — 17 állítás:

* az objektumszám plafonja **12 500** (mért 12 073 + 3%), alsó korláttal
  (5000) a néma üres mérés ellen;
* mind a 13 halasztott párbeszéd induláskor **nem létezik**;
* a szövegmező-menü induláskor nincs meg, **valódi jobbgombos kattintásra
  viszont felépül és megnyílik**;
* forrásszintű állítás: `TextFieldContextMenu`-t csak a
  `TextFieldContextArea` példányosíthat.

### Mutációs bizonyíték

| mutáció | mit vártunk | mi történt |
|---|---|---|
| `DeferredDialog.active: false` → `true` | a példányosítás-őr bukik | **14 bukás** (13 párbeszéd + az objektumszám) |
| a szövegmező-menü vissza közvetlen deklarációba | a példányosítás-őr bukik | **3 bukás** (objektumszám + két menü-őr) |
| `DeferredDialog.ensure()` nem aktiválja a `Loader`-t | a MŰKÖDÉS-őrök buknak | **29 bukás + 29 hiba** négy tesztfájlban |
| a jobbklikk nem építi fel a menüt | a MŰKÖDÉS-őr bukik | **1 bukás** (a jobbklikk-teszt) |

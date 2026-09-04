# Az alsó kék információs sáv (`thumbui/infotext`)

*Forrás: `Picasa3/runtime/thumbui.tre`, a `Picasa3.exe` bináris index
(`GetSelectionInfo` = `0x0056fbc0`, `BigView` = `0x00566a70`), a
`Picasa3i18n.dll` magyar erőforrásai (`stringres.xml`), valamint valódi
Picasa-képernyőképek. Készült a #1189-hez, 2026-08-22.*

## 1. Mi ez az elem

A könyvtárablak alján, a fotótálca fölött futó kék sáv középre igazított
szövege. A felület leírójában:

```
thumbui/infotext: thumbui/infotext_clip      # thumbui.tre:683
m_offsetT
m_scaleX
m_displayfont12
Property textalign center
Property forceuidirection 1

thumbui/infotext_clip: thumbui/basecontrolset
XConstraint 0, 0, 20
XConstraint 1, 1, -20
```

Tehát: a sáv teljes szélességét kitölti 20-20 képpont margóval,
**középre igazított**, `displayfont12` betűvel. A `.tre` **nem ad hozzá
feliratot** — a tartalmat kód írja.

Két függvény írja:

| függvény | mikor |
|---|---|
| `0x0056fbc0` (`GetSelectionInfo`) | a rácsban, a **kijelölés** alapján |
| `0x00566a70` (`BigView`) | a nagy nézetben, az **épp mutatott kép** alapján |
| `0x005706b0` | a sáv ürítése/beállítása (338 bájt, csak az elemnevet hivatkozza) |

## 2. A `GetSelectionInfo` öt alakja

A függvény öt honosított formátumot használ. A kulcs → magyar szöveg
párosítás a `Picasa3i18n.dll` `stringres.xml`-jéből (mentve:
`referencia/i18n-hu/stringres.xml`):

| kulcs | angol (bináris) | magyar (i18n) |
|---|---|---|
| `il_GetSelectionInfo::1` | `No Selection` | `Nincs kijelölés` |
| `il_GetSelectionInfo::2` | `%s     %s     %dx%d pixels     %s` | `%1$s     %2$s     %3$dx%4$d képpont     %5$s` |
| `il_GetSelectionInfo::3` | `%s pictures` | `%s képek` |
| `il_GetSelectionInfo::4` | `     %s to %s     %s on disk` | `     %1$s-%2$s     %3$s a lemezen` |
| `il_GetSelectionInfo::5` | `     %s      %s on disk` | `     %1$s      %2$s/lemez` |

Az elválasztó **öt szóköz** (a `%s     %s` alakokban is), a `::4`/`::5`
pedig már öt szóközzel **kezdődik** — vagyis a darabszám után fűződik.

### 2.1 A négy üzemmód

| állapot | a sáv tartalma |
|---|---|
| nincs kijelölés | `Nincs kijelölés` (`::1`) |
| **egy** kép | `név     dátum-idő     SZxM képpont     méret` (`::2`) |
| **több** kép, eltérő dátum | `N képek` (`::3`) + `     legkorábbi-legkésőbbi     összméret a lemezen` (`::4`) |
| **több** kép, azonos dátum | `N képek` (`::3`) + `     dátum      összméret/lemez` (`::5`) |

### 2.2 Képernyőképes megerősítés

`research/testdata/screenshot/2026-07-17 20 55 20.png` (magyar Picasa 3):

```
25 képek     2026. január 2., péntek-2026. május 18., hétfő     37,5 MB a lemezen
```

Ugyanabból a sorozatból, egy kijelölt képnél:

```
2026-02-19-18-05-05-202.jpg     2026. 02. 20. 3:28:06     1920x1080 képpont     1,4 MB
```

Ebből két dolog **mérve**, nem következtetve:

1. a **több** kijelöltnél használt dátum **hosszú, napnevessel**
   (`2026. január 2., péntek`), a két végpont között **szóköz nélküli
   kötőjel**;
2. az **egy** kijelöltnél használt dátum **rövid, numerikus, időponttal**
   (`2026. 02. 20. 3:28:06`).

## 3. A nagy nézet (`BigView`, `0x00566a70`)

Ugyanezt az elemet írja, de a saját formátumaival:

| kulcs | magyar |
|---|---|
| `il_BigView::1` | `%1$s     %2$s     %3$dx%4$d képpont     %5$s` |
| `il_BigView::2` | `     (%2$d / %1$d)` |
| `il_BigView::3` | `(nincs)` |
| `il_BigView::4` | `%1$d / %2$d` |

Vagyis a nagy nézetben ugyanaz a négymezős sor fut, **kiegészítve a
sorszámmal** (`(3 / 25)`). A `(nincs)` a hiányzó mező helyőrzője.

## 4. A mi megvalósításunk — tételes összevetés

| eset | eredeti | nálunk | állapot |
|---|---|---|---|
| egy kép | név, dátum-idő, SZxM képpont, méret | ugyanaz (`photoInfo` → `formatting.photo_info_text`) | ✅ megvan |
| **több kép** | `N képek` + dátum(tartomány) + összméret | **a MAPPA egészének** összesítése | ❌ **hiba volt — ez a jegy javítja** (`selectionInfo`) |
| több kép, azonos dátum | külön alak (`::5`) | a dátumtartomány egyetlen dátumra rövidül (`formatting.status_text`) | ✅ egyenértékű |
| nagy nézet | négymezős sor + `(i / N)` | `viewerInfo` — ugyanaz | ✅ megvan |
| nincs kijelölés | `Nincs kijelölés` | a mappa összesítése | ⚠️ **eltér, szándékosan** — ld. 4.1 |

### 4.1 A „nincs kijelölés" eset — miért NEM vettük át

Az eredetiben a bal hasábon **mappát választva a mappa képei
kijelöltté válnak** (a tálca buborékja is ezt mondja: „Kiválasztott mappa
– 25 fotó"), ezért a `Nincs kijelölés` állapot a gyakorlatban ritka.
Nálunk a mappaválasztás nem jelöl ki semmit, így a `Nincs kijelölés`
felirat a sáv **állandó** tartalma lenne — a mappa összesítése
hasznosabb, és pontosan azt az adatot mutatja, amit az eredeti a
mappa-kijelöléskor.

Ha a mappaválasztás egyszer átveszi az eredeti kijelölő viselkedését, ez
az eltérés magától megszűnik. Külön jegy: a mappaválasztás mint kijelölés.

## 5. Amit NEM vizsgáltunk

Kimondva, hogy ne látszódjon késznek:

- **videó** kijelölésekor mit ír a sáv (a `BigView` hivatkozik egy
  `videolink` elemre, de a formátum-ág nincs kimérve);
- **hiányzó/sérült** fájl esetén (a `(nincs)` = `il_BigView::3` helyőrző
  hova kerül pontosan);
- **több mappából** származó kijelölés — az eredetiben ilyen nincs
  (a kijelölés mindig egy mappáé, #1145/#1219), nálunk a mostani
  megvalósítás a kapott sorokat összesíti, mappától függetlenül;
- a sáv **egyéb üzenetei** (folyamatjelzés, hibaüzenet) — a `0x005706b0`
  szerepe csak részben tisztázott.

---

## 6. LEZÁRVA: a szöveg clipje a `.tre`-t követi, nem a `respack` téglalapot (2026-09-02, #1934)

A `thumbui/infotext_clip`-re a két forrásunk mást mondott:

| forrás | mit mond | 800 pontos vásznon |
|---|---|---|
| `respack.yt` rétegfejléc | `x 183 … 664` | 481 széles, **közepe 423,5** |
| `thumbui.tre:690–693` | `XConstraint 0, 0, 20` / `1, 1, -20` a `basecontrolset`-en (`x 0…800`) | `20 … 780`, 760 széles, **közepe 400** |

### 6.1 A döntő mérés: a szöveg KÖZEPE

Az `infotext` `Property textalign center` (`thumbui.tre:687`), tehát a
szöveg a clip közepére ül. A két olvasat közepe a 800-as vásznon
**23,5 képponttal** tér el — 1920 képpont széles ablakra átszámolva
**56 képpont**. Ez bőven mérhető.

Mérve mind a **20** felvételen
(`research/Picasa3-also-talca-ikonok-viselkedese/`, 1920×1080; a fehér
szöveg oszlopkiterjedése a kék csík sávjában, `R>170 ∧ G>190 ∧ B>200`):

```
214629  szöveg 718…1202  közép 960,0   ablakközép 960,0   eltérés  +0,0
214634  szöveg 688…1231  közép 959,5   ablakközép 960,0   eltérés  −0,5
214636  szöveg 791…1128  közép 959,5                       eltérés  −0,5
…  19 felvételen az eltérés  |Δ| ≤ 0,5 képpont
```

*(A huszadik, `…214905.jpg`, kiesik: ott egy másik világos elem is a
sávba lóg, tehát a szövegdoboz nem különíthető el.)*

Ugyanez a szerkesztő fejlécével készült felvételen
(`Picasa3-vs-PicasaPy-fejlec-elteresek`): a szöveg `x 1227…1653`,
közepe **1440**; a Picasa-ablak `962…1918`, közepe **1440** ✓.

⇒ **A clip szimmetrikus a sávra.** A `respack`-olvasat (közép 423,5/800)
`+28` képpontos jobbra tolást követelne az adott ablakban — a mérés
`±0,5`-öt ad. **A `respack` téglalap MEGDŐLT, a `.tre` az igaz.**

### 6.2 Miért NEM ellentmondás

A `respack.yt` téglalapja a **tervezővászon szerzői értéke**. Ahol az
elem kap `XConstraint`-et, ott az elrendező **felülírja**. Ez a lapon
belül is ellenőrizhető: a `filmcontainer_overlay_C` ugyanezt a
kényszerpárt kapja (`0, 0, 20` / `1, 1, -20`), és ott a tárolt téglalap
*egyezik* a kényszerrel (394+20 = 414, 682−20 = 662) — a szerző ott
szinkronban tartotta, az `infotext_clip`-nél nem.

**Szabály ebből:** ha egy elemnek van `XConstraint`/`YConstraint`
kényszere, **a kényszer a törvény**; a `respack` téglalap csak akkor
használható, ha nincs rá kényszer (ilyen a szerkesztő fejlécének minden
mérete, ld. [`szerkeszto-felso-sav.md`](szerkeszto-felso-sav.md) 0.).

### 6.3 Amit ez a mérés NEM dönt el

A clip **szélessége** közvetlenül nem látszik: a leghosszabb mért szöveg
543 képpont (`…214634`), ami **mindkét** olvasatba belefér, tehát vágás
sehol nem áll elő. A `20 / −20` behúzás azért fogadható el, mert a
`respack`-olvasat a **helyre** nézve megdőlt, és a `.tre` az egyetlen
megmaradt forrás.

*Bizonyítottsági fok: **megerősített** a szimmetriára (20-ból 19
felvétel, `|Δ| ≤ 0,5` képpont); **erős** a 20 képpontos behúzásra.*

### 6.4 Teendő nálunk

A mai kódban a szövegnek **nincs külön clipje**, a teljes sávot kapja
(`TrayBar.qml:152` `width: parent.width`). A kék háttér teljes szélessége
**helyes** (mérve: `y = 942`-n a kék `x 0…1919`, nem-kék képpont 0), csak
a **szöveg** clipje hiányzik: `bal + 20 … jobb − 20`.

Jegy: **#1934**.

---

## 7. A CÍMKE-rész a sávon — kimérve (2026-09-04, #1913)

A #1913 2. pontja ezt kérte: a referencia-felvételeken a sáv a **címkézett
képek számát** is kiírja, és a jegy szerint „a forrásminta nem [látszik]…
enélkül a formátum találgatás". **A forrás megvan.**

### A felirat

| kulcs | angol (bináris) | magyar (`stringres.xml`) |
|---|---|---|
| `CThumbUI::GetTagInfo::format` | `Tags: ` | **`Címkék: `** |

Az előállító a **`0x0056f920`** (665 b):

```
0x0056f9cc  push 0x00c8f470          ; "CThumbUI::GetTagInfo::format"  (a KULCS)
0x0056f9d1  mov  eax, 0x00c8f468     ; "Tags: "                        (az angol alapérték)
0x0056f9d6  call 0x009ae560          ; szövegtár-lekérdezés
```

### A címkénkénti alak — BEÉGETETT, nem honosított

```
0x0056fa98  push 0x00c8f494          ; "%s (%d)"
0x0056faa1  call 0x0040ea90          ; sprintf(név, darabszám)
```

⇒ A sáv címke-része: a honosított **`Címkék: `** előtag, majd címkénként
**`<név> (<darabszám>)`**. A zárójeles darabszám formátuma **nincs a
szövegtárban** — beégetett, tehát minden nyelven ugyanaz.

Ez pontosan a felvételen látott alak:

```
67 képek   …   86,5 MB a lemezen   Címkék: AI image (66)
```

⇒ **A #1913 2. pontja LEZÁRVA**: a formátum nem találgatás.

> ⚠️ **A sztring nincs a bináris-index sztringtáblájában.** Sem a
> `CThumbUI::GetTagInfo::format`, sem a `%s (%d)` nem szerepel a
> `string_xrefs`-ben — a hivatkozó függvényt az utasítás-operandusok
> közvetlen átfésülése adta meg. A sztring-xref hiányából tehát **nem
> következik**, hogy a szöveg nincs meg.

### A 3. pont már korábban lezárult

A #1913 3. pontja („a méret-felirat két magyar alakja") **a 2. és 2.1
szakaszban már benne van** (a #1934 köre vitte be): a `::4` a
**dátum-tartományos** alak (`… a lemezen`), a `::5` az **egy dátumos**
(`…/lemez`). A jegyben szereplő feltevés — „nap-számhoz kötés" —
**helyesnek bizonyult**, csak addigra már mérve is volt.

*(A magyar fordítás következetlensége — `a lemezen` vs `/lemez` — a
gyártó saját szövegtárában van így; nem a mi hibánk, és átvételkor
követni kell.)*

---

## 8. A FÜGGŐLEGES TÉRKÖZ a csík és a gombsor közt: **6 képpont** (2026-09-04, #1913)

> ℹ️ **Ez KONTROLL-mérés, nem új eredmény.** A 6 képpontot a **#2173** köre
> már kimérte és be is építette (`TrayBar.qml`, 2026-09-03). Az itteni
> levezetés **függetlenül**, a `respack.yt` rétegfejléceiből jött ki —
> és **ugyanazt** adta. A szám tehát kétszer, két úton igazolt.

A #1913 1. pontja ezt kérte, és kikötötte, hogy a szám a `respack.yt`
rétegtéglalapjaiból jöjjön, ne becslésből („kitalált 3 vagy 5 képpont
később mérésnek látszana").

**Kimérve** a `tools/picasa/respack.py` olvasójával, a
`runtime/respack.yt` 13 bájtos rétegfejléceiből. Az elemek a felületleíróban:
`thumbui.tre:702` (`thumbui/basecontrolset`) · `thumbui.tre:683`
(`thumbui/infotext`) · `thumbui.tre:225` (`thumbui/startoggle`) ·
`thumbui.tre:238` (`thumbui/rotateleft`) · `thumbui.tre:245`
(`thumbui/rotateright`).

| réteg | téglalap | méret |
|---|---|---|
| `thumbui/rect: basecontrolset` *(a teljes vezérlő-sáv)* | (0, **429**)–(800, 534) | 800 × 105 |
| `thumbui/text( ): infotext` *(a kék csík szövege)* | (183, **429**)–(664, **443**) | 481 × 14 |
| `thumbui/clip: infotext_clip` | (183, 429)–(664, 443) | 481 × 14 |
| `thumbui/…: startoggle` *(csillag)* | (289, **449**)–(325, 471) | 36 × 22 |
| `thumbui/…: rotateleft` | (330, 449)–(366, 471) | 36 × 22 |
| `thumbui/…: rotateright` | (367, 449)–(403, 471) | 36 × 22 |

```
a csík ALSÓ éle      443
a gombsor FELSŐ éle  449
                     ---
térköz                 6 képpont
```

⇒ **A kék csík és a gombsor közti függőleges térköz 6 képpont.** A csík a
vezérlő-sáv legtetején ül (mindkettő `y0 = 429`), a gombsor 20 képponttal
lejjebb kezdődik.

### Két melléklelet, ami a bekötésnél számít

1. **A három gomb NEM egyenletesen osztott.** A csillag (289–325) és a
   balra forgatás (330–366) közt **5** képpont van, a két forgatás közt
   (366–367) viszont **1**. A csoportosítás tehát: csillag ▏ szünet ▏
   forgatás-pár.
2. **A gombsor magassága 22 képpont**, a csíké 14 — a kettő nem egyezik,
   tehát a `Column` `spacing`-je önmagában nem elég: a két sor saját
   magassága is mért érték.

*Bizonyítottsági fok: **megerősített** — a számok a `respack.yt`
rétegfejléceinek `int16 x0, y0, x1, y1` mezőiből valók
([`picasa-respack-format.md`](picasa-respack-format.md) 3.).*

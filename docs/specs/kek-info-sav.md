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

## 9. A FÁJLNÉV a sávban: kétlépcsős leépülés, KÉPPONT alapján (2026-09-07, #2581)

*A #2581 három kérdést tett fel: karakterre vagy képpontra vág az eredeti;
mi a vágás aránya; és melyik nézet írja ki a mappa-előtagot. Az első és a
harmadik LEZÁRULT, a második két jelölt közül egyet zár ki.*

### 9.1 A két minta — UGYANAZ a nézet, más ABLAKSZÉLESSÉG

| felvétel | ablak | a sáv első tétele | a név mezője |
|---|---|---|---|
| `picasa3-felirat-bekapcsolva. 223224.jpg` (1920 × 1080, teljes képernyő) | **1920** | `AI > JonasBen_he_sits_on_a_ladder_above_the_clouds_with_a_fishing-ro_0291672e-b6c3-4582-8195-fdadc0a71328.png` | x 493…1036 = **544 px** |
| `141421.jpg` (1920 × 1200, A/B — a bal fél a Picasa) | **≈960** | `JonasBen_he_sits_...0a71328.png` | x 213…361 = **149 px** |

**Ugyanaz a fájl, ugyanaz a nézet, ugyanaz a betű.** Hogy a betű azonos, a
SZOMSZÉD mezők bizonyítják: a dátum **98**, a `896x1344 képpont` **85**, a
`807 KB` **31** képpont — mindhárom pontosan ugyanannyi a két felvételen.

### 9.2 Karakter vagy képpont? — **KÉPPONT**

Ha karakterszámra vágna, ugyanaz a név ugyanúgy csonkulna mindkét
felvételen. Nem így van: a szélesebb ablakban **teljes egészében** kiírja
(544 px), a keskenyebben 149 képpontra vágja. ⇒ **a szabály képpont-alapú.**

A binárisban is ez áll: a `"..."` literál (`0x00cb3ee4`) — a **kimerítő
pásztázás szerint a program EGYETLEN hivatkozott hárompontja** — a
`FUN_00826310`-ben van, és az a függvény
`GetTextExtentExPointA`-val (`0xc40100`) kérdezi meg, **hány karakter fér
el N képpontban**.

### 9.3 A leépülés KÉTLÉPCSŐS

A keskeny ablakban nemcsak a név rövidül, hanem a **`AI > ` mappa-előtag is
eltűnik** — pedig a széles ablakban ott van. A vágott alak
(`JonasBen_he_sits_...`) **nem** az előtaggal kezdődik, tehát nem egyszerű
középső elhagyásról van szó:

1. elfér minden → `mappa > név   dátum   felbontás   méret   (N / i)   címkék`
2. nem fér el → **elmarad a `mappa > ` előtag**
3. még mindig nem fér el → **a név KÖZEPÉN vág**, `...`-tal

⚠️ Ez ugyanaz a csapda, amibe a #2565 belefutott a SZÁMLÁLÓVAL: ott is a
fél szélességű ablak levágását olvastuk hiánynak
(`controller.py`, `viewerInfo` kommentje). A tanulság most másodszor jött
elő: **ablakszélesség nélkül a sáv egyetlen hiányzó eleméből sem szabad
következtetni.**

### 9.4 A vágás aránya — a mérés két jelöltet KIZÁR

A 149 képpontos mezőben (`141421.jpg`, x 213…361):

| rész | tartalom | szélesség |
|---|---|---|
| fej | `JonasBen_he_sits_` (17 karakter) | **84 px** |
| jel | `...` (három ASCII pont, nem `…`) | ≈ **7 px** |
| far | `0a71328.png` (11 karakter) | **58 px** |

A fej/far arány a jel nélkül **84 / 142 = 59,2 %**. Ebből:

* **50/50 KIZÁRVA** — az 71/71 képpontot adna, a mért fej 84;
* **2/3 – 1/3 KIZÁRVA** — az 94,7/47,3-at adna;
* **60/40 megfelel**: 85,2/56,8 — a mérttől kevesebb, mint egy
  karakterszélességnyi (≈5 px) eltérés.

⇒ A 60/40 az egyetlen kerek arány, ami a mérésbe belefér — de **egyetlen
csonkolt mintából ez nem szerződés**. Amit eldöntene: még egy felvétel
ugyanabban a nézetben, MÁS hosszúságú névvel (vagy ugyanez a név más
ablakszélességnél). Addig a 60/40 **jelölt**, nem lelet.

### 9.5 Amit a binárisban KIMERÍTŐEN kizártunk

Hogy a középső vágást ne keresse újra senki egy nem létező Win32-hívásban:

| jelölt | eredmény |
|---|---|
| `PathCompactPathExA/W` (shlwapi) | **nincs importálva** |
| `DrawTextW` `DT_PATH_ELLIPSIS` / `DT_END_ELLIPSIS` | az EGYETLEN `DrawTextW` hívás (`0x008d90a1`) `0xc10` jelzőkkel megy = `DT_WORDBREAK│DT_CALCRECT│DT_NOPREFIX` — **mérés, nem rajzolás**, ellipszis-jelző nincs |
| `…` (U+2026) literál | **nincs**: az egyetlen előfordulás (`0x00cf24fc`) egy CP1252 → UTF-8 átalakító TÁBLÁBAN áll, a `‹ Š ‰ ˆ ‡ † …` sorozat közepén |
| széles (`UTF-16`) `"..."` | **nincs** |
| `%s...%s` alakú formátumsztring | **nincs** (a 122 `"..."`-ra végződő cím közül egyetlenegyre — `0x00cb3ee4` — van hivatkozás) |

⇒ A hárompontot **a program maga fűzi hozzá**, a `FUN_00826310`-ben.

### 9.6 A `FUN_00826310` — amit tud, és amit nem

`(hdc, sztring, maxSzélesség, ki_fej, ki_far, hárompont_kell, ki_szélesség)`

1. `GetTextExtentExPointA`-val megkérdezi, hány karakter fér el;
2. ha minden elfér → fej = a teljes szöveg, far = üres;
3. különben **visszafelé keres egy SZÓKÖZT** (`0x00986310`, a
   `fitCount − 3` pozíciótól, ha a hárompont kell) — tehát **szóhatáron
   vág, ha van**;
4. fej = a vágásig, és ha a hívó kérte, a végére `"..."`;
5. far = a maradék — ez a **következő sor**, nem a név vége.

⇒ Ez önmagában **sorTÖRŐ + VÉG-ellipszis**, nem középső. A középső alakot a
HÍVÓ állítja elő: a fejhez a saját farkát fűzi. A hívó megkeresése nyitott
(a függvényre nincs közvetlen `e8` hívás — vtáblán át hívódik); a 9.4
aránya ezért is marad jelölt.

*Bizonyítottsági fok: **megerősített** a 9.2 és a 9.3 (két felvétel,
képpontra mérve, azonos betűvel igazolva) és a 9.5 (kimerítő pásztázás);
**jelölt** a 9.4 aránya.*

### 9.7 Nálunk: `infosav.js` (#2581, v0.8.330)

A szabály a `src/picasapy/app/qml/PicasaPy/infosav.js`-ben él, tiszta
függvényként — a szélesség-mérőt a hívó adja be, ezért a betűtől
függetlenül próbálható (`tests/app/test_infosav_leepules_2581.py`,
`QJSEngine`, szintetikus betűvel).

| lépcső | mit tesz |
|---|---|
| 0. | elfér → változatlan |
| 1. | `elotagNelkul` — csak az ELSŐ mezőből vágja a `mappa > `-t (a `>` szerepelhet dátumban vagy címkében is) |
| 2. | `nevKozepenVagva` — a névre maradó helyet `FEJ_ARANY = 0.6` szerint osztja fej és far közt, a far a név VÉGE (a kiterjesztés megmarad) |
| határeset | ha egy karakter sem fér el, a név a puszta `...` — a többi mezőhöz nem nyúlunk, ott a sáv clipje vág (6.) |

A `TrayBar.qml` `trayInfoText`-je egy `TextMetrics`-szel mér a saját
betűjével. A `clip: true` vészféknek megmarad.

⚠️ A `FEJ_ARANY` a 9.4 **jelöltje**. Ha egyszer előkerül egy második
csonkolt minta, EZT az egy számot kell átírni — a szerkezet nem függ tőle.

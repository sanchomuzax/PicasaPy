# `respack.yt` — a Picasa bináris erőforráscsomagja (MEGFEJTVE)

**Státusz: 2026-08-06 — teljesen visszafejtve, 100%-os fedéssel.**
*(2026-09-03: a rétegfejléc 8–9. bájtja helyesbítve — ld. 3.0.)*
Ez a fájl korábban a `picasa-program-resources.md` 8. fejezetének
**4. nyitott kérdése** volt („dokumentálatlan, saját bináris konténer,
reverse-engineering nélkül nem állapítható meg"). Most már nem az.

Forrás: `research/copy_Picasa_3_7/Picasa3/runtime/respack.yt` (3,7 MB) és
`runtime/slingshot/respack.yt` (372 KB) — Picasa **3.9.141.259**.
Kicsomagoló: [`tools/picasa/respack.py`](../../tools/picasa/respack.py),
tesztek: `tests/picasa/test_respack.py`.

> **Jogi keret.** A csomagban Google Inc. szerzői jogvédett grafikája és
> szövege van. A **formátum** leírása és a kicsomagoló szabadon
> megosztható; a kinyert **tartalom** nem. A PicasaPy sem grafikát, sem
> `.tre` forrást nem tartalmaz belőle — a saját legális telepítéséből
> mindenki maga csomagolhatja ki, hivatkozási/tanulmányozási célra.

## 1. Szerkezet

```
+0            uint32 LE   a NÉVINDEX bájt-eltolása (a fájl vége felé)
+4 …          adatblokkok egymás után, offset szerint növekvő sorrendben
<index_off>   uint32 LE   bejegyzések darabszáma (N)
              N ×  ( név ASCIIZ , uint32 LE offset )
```

A rekordoknak **nincs hosszmezőjük**: egy blokk a következő bejegyzés
offsetjéig tart (az utolsóé az index kezdetéig). Ezért az indexet
offset szerint rendezni kell a kicsomagolás előtt.

A vizsgált csomagban **2909 bejegyzés**: 2769 rajzi réteg (`layer:…`) és
**140 UI-elrendezés-forrás** (`tre:…`).

## 2. Névtér

| Előtag | Jelentés |
|---|---|
| `layer:<panel>/<elem>` | egy rajzi réteg (ikon, gomb-állapot, keret, tömör kitöltés) |
| `tre:<modul>` | egy `.tre` UI-elrendezés-forrásfájl szövege (ld. 5. pont) |

A `layer:` nevek megegyeznek azzal a névtérrel, amit a `fliprtl.txt`
(RTL-tükrözendő ikonok) és a `buttons/*.pbz` gombfájlok
`<icon src="runtime" name="…">` hivatkozásai használnak — ezzel a két
korábban külön dokumentált fájl is a helyére kerül.

A réteg-nevek gyakran magukban hordják a Photoshop-eredetű vagy a
komponens-generátoros nevet, pl.
`layer:acquirepanel/superbutton(button_notext): rotate2button`,
`layer:thumbui/#Shape 1 copy 2`. A `decrect(...)`, `clip:`, `rect:`,
`bicubic:` prefixek a réteg *fajtáját* jelölik a Picasa rajzolómotorjában.

> ### ⚠️ A `#` a rétegnévben NEM jelent holt kódot
>
> **2909-ből 257 réteg neve tartalmaz `#`-et**, és köztük vannak olyanok,
> amikről bizonyosan tudjuk, hogy kiszállítottak — pl. `#histogram_icon`,
> `adorners/#geo`, `adorners/#people` (utóbbi kettő a felhasználó
> képernyőképein is látszik). A `#` itt **rétegtípus-jelölés**.
>
> **Ne keverd össze** a `.tre` elrendezés-források **sor eleji `#`-jével**,
> ami valódi **megjegyzés** — ott a kikommentezett sor tényleg azt jelenti,
> hogy az elem nem kap pozíciót, tehát nem jelenik meg.
>
> Egy cáfoló kör pontosan ezt a kettőt keverte össze, és két helyes állítást
> minősített tévesen „holt kódnak".

## 3. Rétegrekord

Minden `layer:` blokk 13 bájtos fejléccel indul:

| Eltolás | Típus | Jelentés |
|---|---|---|
| 0 | `int16 LE` | `x0` — a réteg határoló dobozának bal széle |
| 2 | `int16 LE` | `y0` — felső szél |
| 4 | `int16 LE` | `x1` — jobb szél (exkluzív) |
| 6 | `int16 LE` | `y1` — alsó szél (exkluzív) |
| 8 | `uint16 LE` | **ÁTLÁTSZÓSÁG** — 256 = átlátszatlan, 0 = teljesen átlátszó (ld. 3.0) |
| 10 | `uint16 LE` | 0 — tartalék (mind a 2769 rétegen 0) |
| 12 | `uint8` | **kódolás**: 0 = üres, 1 = RLE, 2 = tömör kitöltés |

**A koordináták előjelesek** (`int16`, nem `uint16`) — 17 réteg lóg ki a
vászonból negatív origóval; előjel nélkül olvasva ezek méretei
értelmetlenné válnak. Ez a formátum egyetlen valódi csapdája.

### 3.0 ⛔ HELYESBÍTÉS: a 8–9. bájt átlátszóság (2026-09-03, #2178)

**Ez a lap korábban két külön mezőt írt ide, és mindkettőt tévesen:**

| bájt | a korábbi állítás | valójában |
|---|---|---|
| 8 | „0 (ismeretlen; a mintában végig 0)” | **140 rétegen nem 0** |
| 9 | „1 = normál réteg, 0 = `docbounds`” | a 256 felső bájtja |

A kettő **egyetlen `uint16 LE`**: a réteg átlátszósága, ahol **256 =
átlátszatlan**. A teljes csomagban (2769 réteg) mindössze **tíz**
különböző érték fordul elő, mind 0 és 256 között:

| érték | %-ban | rétegek |
|---|---|---|
| 256 | 100,0% | 2629 |
| 0 | 0,0% | 100 |
| 247 | 96,5% | 1 |
| 242 | 94,5% | 3 |
| 230 | 89,8% | 10 |
| 204 | 79,7% | 9 |
| 179 | 69,9% | 3 |
| 153 | 59,8% | 3 |
| 128 | 50,0% | 2 |
| 77 | 30,1% | 9 |

**Miért látszott igaznak a régi 9. bájtos szabály?** Mert a 0 értékű
rétegek **pontosan a 100 `docbounds` réteg** — azoknak 0 az
átlátszóságuk, és nincs egyetlen 0 értékű, nem-`docbounds` réteg sem.
Véletlen egybeesés, nem szabály; a 8. bájtra adott állítás viszont
nyíltan megdől.

**A részlegesen átlátszó rétegek NEVE igazolja az olvasatot:**
`modalprogress/shadow` (30%), `capturemoviepanelpopup/filmcontainer_overlayL/C/R`
(30%), `overlays/timeline` (50%), `editpanel/rect: refining` — a
„Finomítás…” fátyla (70%), `scratch/rect: highlight` — a képtálca
mappa-tokenjének kék pirulája (70%), `editpanel/rect: captionbase` (80%),
`tooldecrect/tooldecrect` (90%), `searchcontainer/listbox: searchautocomplete`
(95%).

**Fizikai ellenőrzés.** A `scratch/rect: highlight` tömör színe
RGB(46,114,161), átlátszósága 179/256 = 69,9%. Fehér fölött ebből
RGB(109,157,189) jön ki. A tulajdonos felvételén
(`research/Picasa3-also-talca-ikonok-viselkedese/…214629.jpg`, a kék pirula)
**mért** érték: **RGB(107,153,186)** — csatornánként ≤4 eltérés, JPEG-zaj.
Átlátszatlan rétegnél 61/39/25 lenne az eltérés.

**Az osztó 256, nem 255:** a mért értékkészlet maximuma pontosan 256.

⚠️ A [`respack.py`](../../tools/picasa/respack.py) ma **eldobja** ezt a
mezőt, tehát minden réteget átlátszatlanként ad vissza — jegy: **#2178**.
Az `encode_layer` NEM érintett (a fejléc nélküli törzset állítja vissza),
tehát a 3.3 bájtazonossági állítása továbbra is igaz.

### 3.1 Kódolás `2` — tömör kitöltés (1403 réteg)

A fejléc után pontosan **4 bájt BGRA**; a teljes határoló doboz ezzel a
színnel van kitöltve. A rekord így fixen 17 bájt.

### 3.2 Kódolás `1` — RLE, sorhatároktól FÜGGETLENÜL (1365 réteg)

A fejléc után `(uint8 darab, B, G, R, A)` ötösök sorozata: a kép **egyetlen,
folytonos képpont-folyam**, a futamok **átlógnak a sorhatárokon**. A futamok
összege pontosan `(x1−x0) × (y1−y0)` képpont.

> **HELYESBÍTÉS (2026-08-21, #1160).** Ez a leírás korábban tévesen **RGBA**
> sorrendet állított. A nyers `respack.yt` képpontok **BGRA** sorrendűek; a
> kicsomagoló PNG-íráskor alakítja őket RGBA-vá. A nyers dekódolt puffer és a
> visszakódolás BGRA marad, ezért a round-trip bájtra azonos.

> **JAVÍTÁS (2026-08-07).** Ez a leírás korábban azt állította, hogy a futamok
> **sorhatárra igazítottak**. **Tévedés volt.** Az eredeti megfigyelés (az
> `acquirepanel/#rect: center_base` első sora pontosan 801 képpontot ad ki)
> csak véletlen egybeesés volt: az a sor egyszínű, ezért a futam ott ért véget.
> A hibát a **visszakódolási (round-trip) próba** mutatta ki — ld. 3.4.

### 3.3 Kódolás `0` — üres réteg (1 db)

Csak fejléc, adat nélkül — átlátszó helyőrző.

### 3.4 Verifikáció — kétlépcsős

**1. lépcső — kifejtés.** A `tools/picasa/respack.py png` a valódi 3,7 MB-os
csomagon **2769/2769 réteget csomagol ki hibátlanul**, és a képpontszámok
minden rétegnél kiadják a fejléc szerinti méretet.

**2. lépcső — VISSZAKÓDOLÁS (round-trip).** A dekódolt képpontokból
újrakódolva a bájtsort, és összevetve az eredetivel: **1365/1365 RLE-réteg
bájtra azonos**.

Ez a második lépcső a döntő, és **egy hibát ki is mutatott**: az első
próbálkozás (sorhatárra igazított kódolás) 1025 rétegen HOSSZABB bájtsort
adott az eredetinél — ebből derült ki, hogy a futamok valójában átlógnak a
sorokon. A sorfüggetlen kódolással azonnal 100% lett az egyezés.

**Tanulság:** a „minden bejegyzés kifejthető" még nem jelenti, hogy a formátumot
pontosan értjük — csak a **bájthű visszakódolás** bizonyítja. Ez a
`binaris-regeszet-modszertan.md` validációs létrájának legfelső foka.

## 4. Mit ad ez a közösségnek

1. **Az eredeti Picasa teljes ikon- és króm-készlete** pixelpontosan
   kinyerhető (mappa-ikonok, csillag, gomb-állapotok `_n`/`_h`/`_p`
   normál/hover/pressed hármasokban, filmszalag, hisztogram-keretek,
   arcfelismerés-jelvények…). Aki hű újraalkotást épít, végre nem
   képernyőképről mintavételez, hanem az eredetit nézi.
2. **A gomb-állapotok szisztematikus névkonvenciója** (`_n`/`_h`/`_p`,
   `_lg`/`_sm`, `_win`/`_mac`) megmutatja, hány állapotot rajzolt meg a
   Picasa minden vezérlőhöz — ez a hűség mércéje egy QML-stílushoz.
3. **Színpontos referenciák**: a tömör rétegek 4 bájtos BGRA-értékei az
   eredeti UI *pontos* színei (nem screenshot-mintavétel). Pl. a
   `#e8e8e8` króm-háttér közvetlenül itt olvasható.

### 4.1 Színállítás-audit (#1160)

A korábbi RGBA-értelmezés minden nem szürke, a `respack.py`-vel kiírt PNG-ből
vett szín R és B komponensét felcserélte. A publikus specifikációk auditja:

- `picasa-mappakezelo.md`: az `icon_exclude`, `icon_always` és `nofr_on`
  színei a futó Picasa képernyőképével egyeznek; a javított PNG-k immár
  piros, kék, illetve piros eredményt adnak.
- `ui-audit-editor.md`: az `ok_icon` helyes domináns színe `#4A904E`, a
  `cancel_icon`-é `#A14B52`; a régi `#4E904A` és `#524BA1` értékek
  felcserélt csatornákból származtak.
- `design-guide.md`: az érintett tömör-kitöltés tokenek kizárólag szürkék
  (`R=G=B`), ezért értékük változatlan.
- `histogram-reference.md`: a barna rétegszín korábban is megkérdőjelezett
  történeti mérés volt; ebből továbbra sem következik UI-színállítás.

## 5. `.tre` — a Picasa UI-elrendezés-nyelve

A csomagban **140 `tre:` bejegyzés = 296 KB tiszta ASCII forrás** — ez a
Picasa fő ablakának, szerkesztőjének és minden paneljének a
**tényleges elrendezés-forráskódja**. (Korábban ebből egyetlen példány
volt ismert: a `cdautorun/cdgo.tre`.)

### 5.1 Nyelvi elemek

```
#includeonce macros.tre        # előfeldolgozó: include / includeonce
#includesystem fontmacros      # platformfüggő (win/mac) makrókészlet

#define m_centerXY             # makró = constraint-ek csoportja
XConstraint 0.5, 0.5, 0
YConstraint 0.5, 0.5, 0

editpanel/tool_ok: editpanel/tool_container    # elem : SZÜLŐ
m_buttontypecolor3                             # makróhívás
m_offsetR
Property escapekey 1                           # tulajdonság
Handler varbutton publishbottom -105 -212      # eseménykezelő
```

- **Elem : szülő** — a fa deklaratívan, gyerek→szülő irányban épül.
- **`XConstraint a, b, c`** — kényszer alakja: *a szülő `a` arányú pontja*
  a *saját `b` arányú pontjához* `c` képpont eltolással. Ezért
  `0.5, 0.5, 0` = középre igazítás, `0,0,0` + `1,1,0` = szülőre nyújtás,
  és `0, 0, -9999` (`m_render_offscreen`) = képernyőn kívülre lökés, azaz
  „létezik, de nem látszik" — a Picasa így tartott életben rejtett
  gombokat billentyűparancsokhoz.
- **`Property …`** — `hidden`, `usealpha`, `showtarget`/`hidetarget`
  (panelváltás!), `setautorepeat`, `escapekey`, `textalign`, `fontsize`,
  `fontname`, `fontweight`, `fonttrack`, `fontleading`.
- A `*_text.tre` fájlok kizárólag **szövegkötéseket** tartalmaznak:
  `Label <elem>` / `Text <elem>` / `Tooltip <elem>` + a szöveg — ez a
  kapocs a lokalizációhoz (ld. 6. pont).

### 5.2 Miért fontos

- A `showtarget`/`hidetarget` párokból **kiolvasható a teljes
  panel-navigáció** (melyik gomb melyik panelt hozza elő) — a szerkesztő
  öt füle (`editpanel/tab1…tab5` → `tabpanel1…5`), a jobb oldali fiók
  (`rightdrawerpanel/propertiespanel|tagpanel|peoplepanel|geopanel`),
  a hisztogram (`thumbui/histogram` → `editpanel/nerdview`).
- A `#include` gráf megmutatja a **modulhatárokat**: `thumbui.tre` húzza
  be a `printpanel`, `editpanel`, `publish`, `searchoptions`,
  `outputlayout`, `activity`, `tooltips` modulokat — vagyis a Picasa
  komponensbontását, amit egy hű újraírás mintaként vehet.
- A `#`-tel kikommentezett sorok (`##include collagepanel.tre`,
  `###currently not shown in UI###`) **fejlesztői jegyzetek** — látszik,
  mit kapcsoltak ki a végleges buildben.

## 6. Kapcsolat a lokalizációval

A `Picasa3i18n.dll` string-táblájának azonosítói ugyanezt a névteret
használják: `<stringres id="oneup/tllabel.title">`. Így áll össze a
teljes lánc:

```
respack.yt  tre:<modul>       →  elem neve   (elrendezés + viselkedés)
respack.yt  tre:<modul>_text  →  Label/Text/Tooltip kötés
Picasa3i18n.dll  stringres id →  41 nyelvű fordítás
respack.yt  layer:<modul>/…   →  a hozzá tartozó grafika
```

Ez négy, eddig külön kezelt forrást köt egyetlen, gépileg feldolgozható
modellé. Részletek a lokalizációs oldalról: `picasa-hu-terminology.md`.

## 7. `.ytf` — még nyitott

A `runtime/*.ytf` (előre renderelt betűtípus-gyorsítótár) formátuma
továbbra sincs megfejtve, és **nincs is rá szükség**: a PicasaPy natív
rendszerbetűkkel dolgozik. A fájlnév kódolja a paramétereket
(`<család>-<méret>-<skála>-<súly>-<stílus>.ytf`).

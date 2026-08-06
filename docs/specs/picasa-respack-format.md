# `respack.yt` — a Picasa bináris erőforráscsomagja (MEGFEJTVE)

**Státusz: 2026-08-06 — teljesen visszafejtve, 100%-os fedéssel.**
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
`layer:thumbui/#Shape 1 copy 2`. A `#` előtaggal kezdődő és a
`decrect(...)`, `clip:`, `rect:`, `bicubic:` prefixek a réteg *fajtáját*
jelölik a Picasa saját rajzolómotorjában.

## 3. Rétegrekord

Minden `layer:` blokk 13 bájtos fejléccel indul:

| Eltolás | Típus | Jelentés |
|---|---|---|
| 0 | `int16 LE` | `x0` — a réteg határoló dobozának bal széle |
| 2 | `int16 LE` | `y0` — felső szél |
| 4 | `int16 LE` | `x1` — jobb szél (exkluzív) |
| 6 | `int16 LE` | `y1` — alsó szél (exkluzív) |
| 8 | `uint8` | 0 (ismeretlen; a mintában végig 0) |
| 9 | `uint8` | 1 = normál réteg, 0 = a dokumentum határa (`docbounds`) |
| 10 | `uint16 LE` | 0 (ismeretlen) |
| 12 | `uint8` | **kódolás**: 0 = üres, 1 = RLE, 2 = tömör kitöltés |

**A koordináták előjelesek** (`int16`, nem `uint16`) — 17 réteg lóg ki a
vászonból negatív origóval; előjel nélkül olvasva ezek méretei
értelmetlenné válnak. Ez a formátum egyetlen valódi csapdája.

### 3.1 Kódolás `2` — tömör kitöltés (1403 réteg)

A fejléc után pontosan **4 bájt RGBA**; a teljes határoló doboz ezzel a
színnel van kitöltve. A rekord így fixen 17 bájt.

### 3.2 Kódolás `1` — soronkénti RLE (1365 réteg)

A fejléc után `(uint8 darab, R, G, B, A)` ötösök sorozata, sorfolytonosan,
**sorhatárra igazítva** (egy futam soha nem lóg át a következő sorba).
A futamok összege pontosan `(x1−x0) × (y1−y0)` képpont.

Ellenőrző példa (`layer:acquirepanel/#rect: center_base`, 801×325):
`01 00000000 | ff e8e8e8ff | ff e8e8e8ff | ff e8e8e8ff | 23 e8e8e8ff …`
→ 1 + 255 + 255 + 255 + 35 = **801** = a sor szélessége.

### 3.3 Kódolás `0` — üres réteg (1 db)

Csak fejléc, adat nélkül — átlátszó helyőrző.

### 3.4 Verifikáció

A `tools/picasa/respack.py png` a valódi 3,7 MB-os csomagon
**2769/2769 réteget csomagol ki hibátlanul**, egyetlen kihagyás nélkül —
a képpontszámok minden rétegnél pontosan kiadják a fejléc szerinti
méretet. A formátum tehát nem részleges illesztés, hanem teljes.

## 4. Mit ad ez a közösségnek

1. **Az eredeti Picasa teljes ikon- és króm-készlete** pixelpontosan
   kinyerhető (mappa-ikonok, csillag, gomb-állapotok `_n`/`_h`/`_p`
   normál/hover/pressed hármasokban, filmszalag, hisztogram-keretek,
   arcfelismerés-jelvények…). Aki hű újraalkotást épít, végre nem
   képernyőképről mintavételez, hanem az eredetit nézi.
2. **A gomb-állapotok szisztematikus névkonvenciója** (`_n`/`_h`/`_p`,
   `_lg`/`_sm`, `_win`/`_mac`) megmutatja, hány állapotot rajzolt meg a
   Picasa minden vezérlőhöz — ez a hűség mércéje egy QML-stílushoz.
3. **Színpontos referenciák**: a tömör rétegek 4 bájtos RGBA-értékei az
   eredeti UI *pontos* színei (nem screenshot-mintavétel). Pl. a
   `#e8e8e8` króm-háttér közvetlenül itt olvasható.

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

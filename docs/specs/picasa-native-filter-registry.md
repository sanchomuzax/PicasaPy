# A Picasa natív szűrő-nyilvántartása — mind a 42 bejegyzés

Kinyerve a `Picasa3.exe`-ből (3.9.141.259), **disassembler nélkül**: a
szűrő-nevek virtuális címét a PE-szekciótáblából számolva, majd a binárisban
megkeresve a 4 bájtos, little-endian hivatkozásokat. A tábla **16 bájtos
rekordokból** áll:

```
[ név-mutató | fő callback | segéd-callback | 2. segéd-callback ]
```

| szűrő | fő callback | segéd | 2. segéd |
|---|---|---|---|
| `debug` | `0x008f8360` | `0x008f9bf0` | — |
| `autobacklight` | `0x008f7cc0` | — | mag `0x90ac20` fix 0,25/1,0 argumentummal — **implementálva (#567)** |
| `finetune` | `0x008f7cf0` | — | — |
| `finetune2` | `0x008f7ee0` | — | — |
| `autolight` | `0x008f80c0` | — | — |
| `autocolor` | `0x008f82a0` | `0x008f9c60` | — |
| `triple` | `0x008f8a60` | — | — |
| `triple2` | `0x008f8b90` | — | — |
| `triple3` | `0x008f8ce0` | — | — |
| `colorfix` | `0x008f9190` | `0x008f9c60` | — |
| `ansel` | `0x008f8410` | — | — |
| `bw` | `0x008f84c0` | — | — |
| `whitept` | `0x008f9270` | `0x008f9c60` | — |
| `enhance` | `0x008f8840` | — | — |
| `warm` | `0x008f8930` | — | — |
| `blur` | `0x008f89a0` | — | — |
| `tilt` | `0x008f8810` | `0x008f9bf0` | — |
| `glow` | `0x008f8f70` | — | — |
| `glow2` | `0x008f8f70` | — | — |
| `colortemp` | `0x008f8ea0` | — | — |
| `unsharp` | `0x008f8f30` | — | — |
| `unsharp2` | `0x008f8f30` | — | — |
| `tint` | `0x008f9630` | — | — |
| `dir_tint` | `0x008f9880` | `0x008f9bf0` | — |
| `radtint` | `0x008f8730` | `0x008f9bf0` | mag `0x90b370`, maszk-LUT `0x90aeb0` — **implementálva (#565)** |
| `sat` | `0x008f8ff0` | — | — |
| `grain` | `0x008f88e0` | — | — |
| `grain2` | `0x008f88e0` | — | — |
| `sepia` | `0x008f8950` | — | — |
| `rainbow` | `0x008f92d0` | — | — |
| `backlight` | `0x008f8970` | — | — |
| `fill` | `0x008f8970` | — | — |
| `autocontrast` | `0x008f89d0` | — | — |
| `radblur` | `0x008f8520` | `0x008f9bf0` | `0x008f9cf0` |
| `radsat` | `0x008f8680` | `0x008f9bf0` | `0x008f9cf0` |
| `linblur` | `0x008f99c0` | `0x008f9bf0` | — |
| `dir_sat` | `0x008f8fb0` | `0x008f9bc0` | — |
| `dir_brite` | `0x008f9050` | `0x008f9bc0` | — |
| `dir_sharp` | `0x008f9090` | `0x008f9bc0` | — |
| `gamma` | `0x008f8e30` | — | — |
| `contrast` | `0x008f8a20` | — | — |
| `shadow` | `0x008f8ee0` | — | — |

A `radtint` (`0x8f8730`) és az `autobacklight` (`0x8f7cc0`) egyezik a
#565/#567-ben Ghidrával kapott címekkel — **a tábla független
megerősítést kapott**.

## Négy szűrőpár AZONOS műveletre mutat

| közös callback | szűrők |
|---|---|
| `0x008f88e0` | **`grain` = `grain2`** |
| `0x008f8970` | **`backlight` = `fill`** |
| `0x008f8f30` | **`unsharp` = `unsharp2`** |
| `0x008f8f70` | **`glow` = `glow2`** |

Vagyis a „2-es" változatok **nem külön algoritmusok**: ugyanaz a kód fut,
csak a `filterdesc.xml` csúszka-metaadata más (más tartomány/eltolás). Ez
négy implementációt spórol, és egyben azt is megmondja, hogy a
`fill` („Derítőfény") és a `backlight` („Háttérfényjavítás") **ugyanaz**.

## Három közös segédfüggvény

| segéd-callback | kik használják | mire utal |
|---|---|---|
| `0x008f9bc0` | `dir_sat`, `dir_brite`, `dir_sharp` | **közös kétirányú súlytérkép** (balról jobbra / fentről le) — egyszer megírva mind a három megvan |
| `0x008f9bf0` | `debug`, `tilt`, `dir_tint`, `radtint`, `radblur`, `radsat`, `linblur` | közös **geometriai maszk/paraméter-előkészítés** a helyfüggő effektekhez |
| `0x008f9c60` | `autocolor`, `colorfix`, `whitept` | **közös fehérpont/semleges-szín gépezet** — ez a szín-varázspálca (#551) és a pipetta közös magja |

A `0x008f9c60` külön kiemelendő: a mérésből tudjuk, hogy a szín-pálca a
`finetune2` p4 mezőjébe ír referencia-színt, és hogy a semleges-közeli
képpontokból dolgozik. A tábla szerint **ugyanaz a rutin** szolgálja ki az
`autocolor`-t, a `colorfix`-et és a `whitept`-et — tehát egy
implementációval mind a négy belépési pont megvan.

## Hogyan lett kinyerve (megismételhető, Ghidra nélkül)

1. A PE-szekciótáblából fájl-eltolás → virtuális cím leképezés.
2. A szűrő-nevek (`filterdesc.xml`-ből) megkeresése nullával lezárt
   sztringként.
3. A sztring virtuális címének 4 bájtos, little-endian keresése a teljes
   fájlban → ezek a hivatkozási helyek.
4. Az egymás mellett, 16 bájtonként ismétlődő minta felismerése.

A 32 bites, nem-PIE PE-nél a kódba beégetett abszolút címek miatt ez
megbízható. Nem helyettesíti a dekompilálást, de **a belépési pontokat
ingyen megadja**.

## Két hiány a nyilvántartásban (2026-08-15, #711 köre)

### 1. A `desat` — a 43. szűrő, ami nincs a 42 elemű táblában (MEGVALÓSÍTVA, #711)

A fenti tábla a `CGenericFilter` által kezelt szűrőket sorolja. Az RTTI-ben
azonban **két** érdemi kép-szűrő osztály van: a `CGenericFilter` és a
**`CDesaturateFilter`**. Utóbbi saját ini-kulccsal (`desat`), saját
paraméterformátummal (`%c,%f,%f,%f`) él, és **nincs benne a táblában** —
ezért maradt ki a nyilvántartásból.

Renderelése azonos az `ansel`-lel: mindkettő a `0x0090e680` munkafüggvényt
hívja, és annak az egész binárisban **pontosan ez a két hívója van**
(`0x008f8410` = ansel, `0x0050ce70` = desat). Részletek és az egzakt
átváltás: [`picasa-ini-format.md`](picasa-ini-format.md), „A `desat`" szakasz.

### 2. A Filtered B&W-nek VAN erősség-csúszkája — nálunk nincs

A szövegforrások (`referencia/stringres-en-hu.tsv`) három erőforráskulcsot
adnak ehhez a szűrőhöz:

| kulcs | angol | magyar |
|---|---|---|
| `CDesaturateFilter::name` | Filtered B&W | **Szűrt FF** |
| `CDesaturateFilter::strength` | Strength | **Erősség** |
| `CDesaturateFilter::pickcolor` | Pick Color | **Színválasztás** |

Mindkettőt a `0x0050cf90` (899 bájt) hivatkozza — vagyis a szűrő panelje egy
**erősség-csúszkát** és egy **színválasztót** épít.

> ⚠️ **ELVETVE, még ugyanaznap.** Először azt írtam ide, hogy ez hiány a mi
> oldalunkon — **tévedés volt, és a cáfolat a saját anyagunkban feküdt.**
> A `referencia/filteredbw/panel-screenshot-1.png` (eredeti Picasa 3.9,
> 2026-08-10-i referenciakészlet) a **teljes Filtered B&W panelt** mutatja:
> cím, **„Pick Colour" színkorong, Apply/Cancel — és SEMMILYEN csúszka.**
>
> A `CDesaturateFilter::strength` tehát **örökölt erőforrás-szöveg**, ami a
> régi `desat` panelhez tartozott; a 3.9-es `ansel` panel nem használja.
> A mi `FILTER_REGISTRY`-nk (`ansel`, `sliders=()`) **helyes** — nincs mit
> javítani.
>
> *Bizonyítottsági fok: megerősített (elvetés).* Tanulság: erőforrás-kulcs
> puszta létezéséből nem következik, hogy a vezérlő a kiadott verzióban
> meg is jelenik — **előbb a meglévő panel-képet kell megnézni.**

**Ami viszont megerősítést kapott:** a `desat` konstruktora négy mezőt állít
`0,333`-ra (`0x3eaa7efa`), a renderelő pedig három súlyt vesz át. A
2026-08-10-i mérés fehér szűrővel **0,345 / 0,336 / 0,326** csatornasúlyokat
adott (`referencia/README.md`) — gyakorlatilag `1/3` mindhárom. A beégetett
alapérték és a független mérés tehát **egybevág**.

A negyedik `0,333`-as mező szerepe továbbra is **nyitva** (nem az erősség
csúszkája, mert olyan nincs a panelen). *Bizonyítottsági fok: feltételes.*

### 3. Egy 34. Glimmer-művelet, ami eddig nem szerepelt nálunk

A `docs/specs/` 33 `glimmer::*ImageOperation` osztályt dokumentál, és ez a 33
hiánytalanul megvan. Az RTTI-ben azonban van egy **34.**, névtelen
névtérben:

```
_anon_BEC5211C::ResaturateImageOperation::vftable   @ 0x00cf0578
```

- fő képpont-metódusa: `0x00bc4ae0` (1660 bájt);
- egyetlen létrehozója a `0x00bbd630` (588 bájt), ami két attribútumot olvas:
  **`color`** és **`dynamicColorCachePriority`** (utóbbi sem szerepel a
  dokumentációnkban);
- **név szerint sehol nem hivatkozott** — a `Resaturate` karakterlánc nincs a
  binárisban, tehát effekt-XML-ből nem példányosítható; belső segédművelet.

*Bizonyítottsági fok: megerősített* (a létezés és a hívási lánc);
~~**nyitva**, hogy mit csinál és melyik effekt használja — ehhez a `0x00bbd630`
és a `0x00bc4ae0` dekompilálása kell.~~ → **LEZÁRVA Ghidrával (2026-08-30):**
a `0x00bbd630` a konstruktor, ami egy **`ColorMatrixImageOperation`**
(színmátrix) + a `0x00bbd4a0` (a `ResaturateImageOperation::vftable`
példánya, két attribútum: `color` + `dynamicColorCachePriority`) +
`FUN_008eb520` regisztrációból áll. A `0x00bc4ae0` a **Glimmer-üzenet-
sorosító**: a láncot építi (`MaskWithSourceAlphaInstruction`,
`BlendInstruction`, `PopInstruction`) a paraméterezett
színmátrix köré. A művelet **tartalmilag egy színmátrix + maszk/blend
sor**, tehát a `Resaturate` **nem önálló képi algoritmus**, hanem a
színmátrix-motor egy összetett csomagolása (`color` és
`dynamicColorCachePriority` paraméterekkel). A tényleges pixellogika a
vtable egyik metódusában van (a `0x00cf0578`); ~~a `resaturate`-ként való
előfordulás **egyetlen effektnek sem feleltethető meg** (a név nincs a
binárisban) — belső segédművelet.~~ ⛔ **HELYESBÍTVE (2026-09-26, #626):** a `0x00bbd630` a `glimmer::TintImageOperation` vtáblájának 1. rése (attribútum-beolvasó), tehát a `Resaturate` a **`Tint` gyereke**, és négy effekt használja (`CrossProcess`, `Soften`, `ReanimatedEyeColor`, `PicnikTint`). A teljes lánc és a táblaelem (`0x00bce2f0`): `filterdesc-registry.md`, „H) A `Tint` belseje”. *Bizonyítottsági fok: megerősített (a
konstruktor + a sorosító Ghidra-C).*

## A `desat` „negyedik mezője" — NEM LÉTEZIK (2026-08-16)

A #711 egy köre azt írta: *„a `desat` konstruktora **négy** mezőt állít
`0,333`-ra, miközben a renderelő csak **hármat** vesz át (R, G, B) — a
negyedik jó eséllyel az erősség."* A konstruktort utasításszinten kiolvasva
**ez téves**.

### A konstruktor (`0x0050bd70`, 146 bájt) vége betű szerint

```asm
0x0050bdda  fld  dword ptr [0xcf4030]   ; = 0.333f  (fa 7e aa 3e)
0x0050bde0  fst  dword ptr [esi + 0x1c] ; 1.
0x0050bde4  fst  dword ptr [esi + 0x20] ; 2.
0x0050bded  fst  dword ptr [esi + 0x24] ; 3.
0x0050bdf2  fldz                        ; = 0.0
0x0050bdf4  fst  dword ptr [esi + 0x28] ; 4.  ← NULLA
0x0050bdf7  fstp dword ptr [esi + 0x2c] ; 5.  ← NULLA
0x0050bdfa  fstp dword ptr [esi + 0x30] ; 6.  ← NULLA
```

**Három mező kapja a `0,333`-at, és három kapja a nullát.** Nincs negyedik
`0,333`-as mező, tehát nincs mit „erősségként" azonosítani.

### A renderelő pontosan ezt a hármat veszi át

A vtable-rekesz (`0x0050ce70`, 53 bájt):

```asm
cmp byte ptr [ecx + 0x14], 0     ; ENGEDÉLYEZŐ jelző — ha 0, nem csinál semmit
je  vege
push [ecx + 0x24]                ; 3. argumentum
push [ecx + 0x20]                ; 2.
push [ecx + 0x1c]                ; 1.
push eax                         ; a cél
call 0x90e680
```

A `+0x28 … +0x30` nullák **nem kerülnek át** a renderelőnek.

### Amit ez az ini-alakról mond

```
desat=<jelző>,<f>,<f>,<f>          (a szerializálás: "%c,%f,%f,%f")
```

| ini-rekesz | objektum-mező | szerep |
|---|---|---|
| `<jelző>` | `[+0x14]` | engedélyező (ha 0, a szűrő nem fut) |
| 1. float | `[+0x1c]` | R-súly (alap 0,333) |
| 2. float | `[+0x20]` | G-súly (alap 0,333) |
| 3. float | `[+0x24]` | B-súly (alap 0,333) |

**A `desat` átvétele tehát teljesen zárt** — nincs benne azonosítatlan
paraméter. A #711 fejlesztői teendői ezzel a leírással hiánytalanul
elvégezhetők.

*Bizonyítottsági fok: megerősített* (a konstruktor és a vtable-rekesz
utasításszinten; a konstans `0x00cf4030 = 0.333f` a `.rdata`-ból kiolvasva).

## A TELJES natív szűrő-tábla a binárisból (`0x00cd0658`–`0x00cd0958`, 2026-08-16)

A `tint` kezelőjének (`0x008f9630`) visszakeresésekor kiderült, hogy a
mutató egy **rendezett táblában** áll. A tábla **49 rekord**, rekordonként
16 bájt:

```
struct FilterOp {           // 16 bájt
    const char *nev;        // +0
    void       *kezelo;     // +4   (0 = nincs képpont-művelet)
    void       *segedA;     // +8   paraméter-/geometria-értelmező
    void       *segedB;     // +12  csak a radiálisoknál
};
```

**Ez a natív (klasszikus) szűrőmotor teljes névsora** — a `glimmer::`
motor szűrői (`Polaroid`, `RoundedEdges`, `Matte`, `Sixties`, `Neon`,
`NightVision`, `Vignette`…) **nincsenek** benne, azok külön regiszterben
élnek.

### Mind a 49 rekord

| # | cím | név | kezelő | segédA | segédB |
|---:|---|---|---|---|---|
| 1 | `0x00cd0658` | `debug` | `0x008f8360` | `0x008f9bf0` | — |
| 2 | `0x00cd0668` | `crop64` | **0** | — | — |
| 3 | `0x00cd0678` | `crop` | **0** | — | — |
| 4 | `0x00cd0688` | `autobacklight` | `0x008f7cc0` | — | — |
| 5 | `0x00cd0698` | `finetune` | `0x008f7cf0` | — | — |
| 6 | `0x00cd06a8` | `finetune2` | `0x008f7ee0` | — | — |
| 7 | `0x00cd06b8` | `autolight` | `0x008f80c0` | — | — |
| 8 | `0x00cd06c8` | `autocolor` | `0x008f82a0` | `0x008f9c60` | — |
| 9 | `0x00cd06d8` | `rot` | **0** | — | — |
| 10 | `0x00cd06e8` | `redeye` | **0** | — | — |
| 11 | `0x00cd06f8` | `retouch` | **0** | — | — |
| 12 | `0x00cd0708` | `save` | **0** | — | — |
| 13 | `0x00cd0718` | `picnik` | **0** | — | — |
| 14 | `0x00cd0728` | `triple` | `0x008f8a60` | — | — |
| 15 | `0x00cd0738` | `triple2` | `0x008f8b90` | — | — |
| 16 | `0x00cd0748` | `triple3` | `0x008f8ce0` | — | — |
| 17 | `0x00cd0758` | `colorfix` | `0x008f9190` | `0x008f9c60` | — |
| 18 | `0x00cd0768` | `ansel` | `0x008f8410` | — | — |
| 19 | `0x00cd0778` | `bw` | `0x008f84c0` | — | — |
| 20 | `0x00cd0788` | `whitept` | `0x008f9270` | `0x008f9c60` | — |
| 21 | `0x00cd0798` | `enhance` | `0x008f8840` | — | — |
| 22 | `0x00cd07a8` | `warm` | `0x008f8930` | — | — |
| 23 | `0x00cd07b8` | `blur` | `0x008f89a0` | — | — |
| 24 | `0x00cd07c8` | `tilt` | `0x008f8810` | `0x008f9bf0` | — |
| 25 | `0x00cd07d8` | `glow` | **`0x008f8f70`** | — | — |
| 26 | `0x00cd07e8` | `glow2` | **`0x008f8f70`** | — | — |
| 27 | `0x00cd07f8` | `colortemp` | `0x008f8ea0` | — | — |
| 28 | `0x00cd0808` | `unsharp` | **`0x008f8f30`** | — | — |
| 29 | `0x00cd0818` | `unsharp2` | **`0x008f8f30`** | — | — |
| 30 | `0x00cd0828` | `tint` | `0x008f9630` | — | — |
| 31 | `0x00cd0838` | `dir_tint` | `0x008f9880` | `0x008f9bf0` | — |
| 32 | `0x00cd0848` | `radtint` | `0x008f8730` | `0x008f9bf0` | — |
| 33 | `0x00cd0858` | `sat` | `0x008f8ff0` | — | — |
| 34 | `0x00cd0868` | `grain` | **`0x008f88e0`** | — | — |
| 35 | `0x00cd0878` | `grain2` | **`0x008f88e0`** | — | — |
| 36 | `0x00cd0888` | `sepia` | `0x008f8950` | — | — |
| 37 | `0x00cd0898` | `rainbow` | `0x008f92d0` | — | — |
| 38 | `0x00cd08a8` | `backlight` | **`0x008f8970`** | — | — |
| 39 | `0x00cd08b8` | `fill` | **`0x008f8970`** | — | — |
| 40 | `0x00cd08c8` | `autocontrast` | `0x008f89d0` | — | — |
| 41 | `0x00cd08d8` | `radblur` | `0x008f8520` | `0x008f9bf0` | `0x008f9cf0` |
| 42 | `0x00cd08e8` | `radsat` | `0x008f8680` | `0x008f9bf0` | `0x008f9cf0` |
| 43 | `0x00cd08f8` | `linblur` | `0x008f99c0` | `0x008f9bf0` | — |
| 44 | `0x00cd0908` | `dir_sat` | `0x008f8fb0` | `0x008f9bc0` | — |
| 45 | `0x00cd0918` | `dir_brite` | `0x008f9050` | `0x008f9bc0` | — |
| 46 | `0x00cd0928` | `dir_sharp` | `0x008f9090` | `0x008f9bc0` | — |
| 47 | `0x00cd0938` | `gamma` | `0x008f8e30` | — | — |
| 48 | `0x00cd0948` | `contrast` | `0x008f8a20` | — | — |
| 49 | `0x00cd0958` | `shadow` | `0x008f8ee0` | — | — |

### Négy pár OSZTOZIK a kezelőn — vagyis BETŰRE azonos kód

| pár | közös kezelő | mit jelent |
|---|---|---|
| `glow` ↔ `glow2` | `0x008f8f70` | **ugyanaz a ragyogás**, csak más paraméter-verzió |
| `grain` ↔ `grain2` | `0x008f88e0` | **ugyanaz a filmszemcse** |
| `unsharp` ↔ `unsharp2` | `0x008f8f30` | ugyanaz az élesítés |
| `backlight` ↔ `fill` | `0x008f8970` | ugyanaz a derítés (+ `autobacklight` fix 0,25-tel) |

**Ez zárja le a `picasa-ini-format.md` „dekódolatlan" jelölését a `glow`
(v1) és a `grain` (v1) tokenre**: nem külön, ismeretlen algoritmusok —
**bájtra ugyanazt a függvényt** hívják, mint a `2`-es változatuk.

### Hét név, aminek NINCS képpont-kezelője (`kezelő = 0`)

`crop64`, `crop`, `rot`, `redeye`, `retouch`, `save`, `picnik`

A tábla **ismeri** őket (tehát nem „ismeretlen token"), de a
képpont-csővezeték nem csinál velük semmit: geometria- vagy jelző-tokenek,
amiket máshol dolgoz fel a program. A mi `_NOOP_MARKERS` halmazunk ezt már
helyesen tükrözi.

### A két segédoszlop jelentése

| segédA | mely szűrőknél | értelmezés |
|---|---|---|
| `0x008f9bf0` | `debug`, `tilt`, `dir_tint`, `radtint`, `radblur`, `radsat`, `linblur` | **irány/pozíció**-hordozó paraméterek |
| `0x008f9bc0` | `dir_sat`, `dir_brite`, `dir_sharp` | a `dir_*` hármas saját alakja |
| `0x008f9c60` | `autocolor`, `colorfix`, `whitept` | **pipetta-színt** hordozó paraméterek |
| segédB `0x008f9cf0` | **csak** `radblur`, `radsat` | a sugaras kiterjedés |

*Bizonyítottsági fok: megerősített* (a tábla nyersen kiolvasva a
`.rdata`-ból, minden rekordhoz cím).

## A két segédoszlop VALÓDI szerepe: a KÉPEN belüli vezérlők (2026-08-16)

> ⚠️ **Helyesbítés.** A tábla első leírásában a `segédA`/`segédB` oszlopot
> „paraméter-/geometria-**értelmezőnek**" neveztem, és a #317-be is így
> került. **Ez téves volt.** A négy függvény visszafejtése szerint ezek
> **nem** a `filters=` sztringet értelmezik, hanem azt írják le, **mi
> történik, ha a felhasználó a KÉPRE kattint vagy húz**, miközben az adott
> szűrő aktív.

### `0x008f9bf0` — húzható pozíció-fogantyú (103 bájt)

```c
int Handle(Obj *this, POINT *pt, RECT *disp) {
    int w = disp->right - disp->left;   if (!w) return -1;
    int h = disp->bottom - disp->top;   if (!h) return -1;
    float fx = (float)pt->x / w;        // 0..1
    float fy = (float)pt->y / h;        // 0..1
    SetPos(this, fx, fy);               // 0x008f6da0
    this->vtbl[41]();                   // újrarajzolás
    return 0;
}
```

A kattintás helyét **a megjelenített kép méretére normalizálja** (0..1), és
így tárolja. Ezt használja: `debug`, `tilt`, `dir_tint`, `radtint`,
`radblur`, `radsat`, `linblur` — pontosan azok, amiknek **a képen látszó
fogantyújuk** van.

**Következmény a mi oldalunkra:** a `filters=`-ben tárolt pozíció
**arányszám**, nem képpont — ezért marad helyén a hatás, ha a képet
átméretezik. A `disp` a **megjelenített** terület, nem az eredeti kép: a
fogantyút az előnézet méretéhez kell viszonyítani.

### `0x008f9bc0` — a `dir_*` hármas változata (39 bájt)

```c
int Handle(Obj *this, POINT *pt, RECT *disp) {
    if (disp->right == disp->left)   return -1;
    if (disp->bottom == disp->top)   return -1;
    this->vtbl[41]();                // CSAK újrarajzolás
    return 0;
}
```

Érvényes megjelenítési területet vár, de **nem tárol pozíciót** — csak
újrarajzol. Ezt használja: `dir_sat`, `dir_brite`, `dir_sharp`.

### `0x008f9c60` — a pipettás szűrők változata (17 bájt)

```c
int Handle(Obj *this, ...) { this->vtbl[41](); return 0; }
```

Feltétel nélkül újrarajzol. Ezt használja: `autocolor`, `colorfix`,
`whitept` — a **pipettás** hármas. A színfelvétel maga máshol történik; itt
csak a frissítés van.

### `0x008f9cf0` — sugár képpontban (167 bájt), CSAK `radblur` és `radsat`

Ez az egyetlen, ami **értéket ad vissza** (`float`), nem műveletet végez:

```c
float RadiusPx(Obj *this, Params *p) {
    if (!p) return 0.0f;
    int slot = this->[0xe0];                  // melyik csúszka
    if (slot == -1) return 0.0f;
    int idx  = tabla_0xc7d5b8[slot];
    float r  = this->[0x28 + idx*4] + K1;     // K1 = [0xc7e328]
    float w  = (float)p->width  (+2^32 ha negatív)
    float h  = (float)p->height (+2^32 ha negatív)
    return r * K2 * (w vagy h);               // K2 = [0xc72150]
}
```

A **normalizált sugarat képpontra váltja** — ez rajzolja ki a `radblur` és a
`radsat` képen látszó körét. A `segédB` oszlop tehát a **második fogantyú**
(a sugáré), nem a paraméter-alak.

### Összefoglaló táblázat

| oszlop / függvény | mely szűrőknél | mit csinál |
|---|---|---|
| A `0x008f9bf0` | `debug`, `tilt`, `dir_tint`, `radtint`, `radblur`, `radsat`, `linblur` | húzható **pozíció-fogantyú**, 0..1-re normalizálva |
| A `0x008f9bc0` | `dir_sat`, `dir_brite`, `dir_sharp` | csak újrarajzolás, érvényes területtel |
| A `0x008f9c60` | `autocolor`, `colorfix`, `whitept` | csak újrarajzolás (pipettás hármas) |
| B `0x008f9cf0` | `radblur`, `radsat` | **sugár képpontban** — a kör kirajzolásához |
| — (üres) | a többi 35 | nincs képen belüli vezérlő |

*Bizonyítottsági fok: megerősített* (mind a négy függvény teljes egészében
kiolvasva, mindegyik 200 bájt alatt van).

### A sugár képlete kiolvasva — és egy BELSŐ ellentmondás nálunk (2026-08-16)

Az előző szakasz nyitva hagyta, mi van a `0x008f9cf0` csúszka-indexében és a
`0xc7d5b8` átváltótáblában. Mindkettő kiolvasva:

| adat | cím | érték |
|---|---|---|
| átváltótábla | `0xc7d5b8` | **`[0, 1, 2, 5, 1, 2]`**, utána `0x00FF00FF` töltelék |
| K1 (hozzáadás) | `0xc7e328` | **1,0** |
| K2 (szorzó) | `0xc72150` | **0,5** |
| előjel-javító | `0xcf3ac0` | 2³² (előjel nélküli `int` → `float`) |

A választás `min`-re megy: a `fcom`/`test ah,5`/`jp` hármas **mindkét ágon
a kisebbik** felet tartja meg (`0x008f9d58`–`0x008f9d7b`).

```
sugár_képpontban = (paraméter + 1,0) · 0,5 · min(szélesség, magasság)
```

Tehát a tárolt sugár-paraméter **−1 … +1** tartományú, és a kép **rövidebb**
oldalához méretezve **izotróp** (kör alakú) — nem a szélességhez és a
magassághoz külön.

#### ✅ A `radblur` nálunk EGYEZIK

`src/picasapy/render/radial_mask.py:58` — `radius = min(width, height) / 2.0
* (size + 1.0)` — betűre ugyanez a képlet. A `0x0090b050` korábbi
visszafejtéséből származik, és a mostani, **független** úton kiolvasott
konstansok (1,0 és 0,5) megerősítik.

#### ⚠️ A `radsat` nálunk NEM ezt használja (JAVÍTVA — #859, 2026-08-24)

> A lejjebbi lelet ELAVULT: a `radsat` mai (`render/effects.py: apply_radsat`)
> kódja már a `radblur`-rel KÖZÖS `native_radius_pixels`/`pixel_distance_grid`
> segédfüggvényt hívja (`render/radial_mask.py`) — izotróp kör, nem
> tengelyenkénti ellipszis. A `vignette_gain` (`effects.py:100`) VÁLTOZATLAN
> maradt: nyolc eredeti Picasa-export mérése (#859 issue-komment,
> 2026-08-18) megcáfolta az izotróp hipotézist ARRA — annak zónája
> SZÁNDÉKOSAN ellipszis. Az alábbi eredeti lelet a történeti nyom kedvéért
> marad, nem törölve.

`src/picasapy/render/effects.py:58` — a `_radius_grid()` **tengelyenként**
normalizál:

```python
cols = (arange(width)  + 0.5) / width  - x
rows = (arange(height) + 0.5) / height - y
return hypot(rows[:, None], cols[None, :])
```

Ez **anizotróp**: nem szabályos kört rajzol, hanem a kép oldalarányához
nyúlt ellipszist. Egy 4:3-as fotón a hatás zónája érezhetően más alakú,
mint az eredetiben.

A binárisban viszont a `radblur` és a `radsat` **ugyanazt** a `segédB`
függvényt (`0x008f9cf0`) használja — vagyis **azonos, izotróp** sugárral
dolgoznak.

**Ez tehát nem csak eltérés a Picasától: a saját kódunkon belüli
ellentmondás** — a `radblur` izotróp, a `radsat` (és a `vignette_gain`,
`effects.py:100`) anizotróp, holott az eredetiben egyformák.

*Bizonyítottsági fok:* **megerősített** a képletre (a tábla és mindhárom
konstans nyersen kiolvasva, az ágválasztás elemezve) · **megerősített** az
ellentmondásra (a két saját függvényünk kódja).

### Mi választja ki a sugár-paramétert (2026-08-16)

Az előző szakasz nyitva hagyta, mit jelent a `[obj+0xe0]` csúszka-index és
a `0xc7d5b8 = [0, 1, 2, 5, 1, 2]` átváltótábla. **Mindkettő megvan.**

#### A `+0xe0` mező: MELYIK csúszka a sugár

Az alapérték `0xFF` (= −1, „nincs sugár-csúszka"):

```asm
0x008f6997  mov byte ptr [esi + 0xe0], 0xff    ; a konstruktorban
```

És beállítva **akkor és csak akkor**, ha a vezérlő neve **`_sldrRadius`**:

```asm
0x009008c9  cmp  eax, 0xcd1120                 ; "_sldrRadius"
0x009008ce  sete al
0x009008d3  je   0x9008ee                      ; nem a sugár-csúszka → kihagy
0x009008d9  cmp  dword ptr [eax], 1
0x009008e4  mov  al, byte ptr [esp + 0x18]     ; a csúszka SORSZÁMA
0x009008e8  mov  byte ptr [edx + 0xe0], al
```

Egy második hely (`0x008ffafd`) ugyanezt teszi, amikor az elem típusa
`"slider"`.

**Vagyis a `+0xe0` a `_sldrRadius` nevű csúszka sorszáma** a szűrő
csúszkái között — és `0xFF`, ha a szűrőnek nincs sugár-csúszkája. Ezért
adja vissza a `0x008f9cf0` a nullát a `cmp ecx, -1` ágon.

A `_sldrRadius` a `filterdesc.xml` receptjeiben is így szerepel, pl. a
`PencilSketch`-nél: `<BlurImageOperation xblur="{_sldrRadius.value}" …/>`
(4. pont). A binárisban **45 különböző `_sldr…` név** van.

#### Az átváltótábla: csúszka-sorszám → PARAMÉTER-hely

```
0xc7d5b8 = [0, 1, 2, 5, 1, 2]      (utána 0x00FF00FF töltelék)
```

| csúszka sorszáma | a `filters=` láncban hányadik paraméter |
|---:|---:|
| 0 | 0 |
| 1 | 1 |
| 2 | **2** |
| 3 | **5** |
| 4 | 1 |
| 5 | 2 |

#### ✅ Ellenőrizve a két érintett szűrőn

A `radblur` és a `radsat` paraméter-sorrendje `x, y, sugár, erősség`
(`render/chain.py:353` és `:363`) — a sugár tehát a **2.** paraméter.
A táblázat a 2-es sorszámot **2-re** képezi. **Egyezik.**

*Bizonyítottsági fok: megerősített* (a mező alapértéke, mindkét beállító
hely, az átváltótábla nyers tartalma, és a két szűrő paraméter-sorrendje).

## A szűrő-objektum gyára és térképe (2026-08-16)

### A gyár: lineáris keresés a 49 rekordon — `0x008fa16d`

```asm
0x008fa17b  mov esi, 0xcd0658      ; ← a natív szűrő-tábla eleje
0x008fa180  xor edi, edi           ; index
...                                 ; sztring-összehasonlítás a kért névvel
0x008fa23b  add edi, 0x10          ; egy rekord = 16 bájt
0x008fa23e  add esi, 0x10
0x008fa241  cmp edi, 0x310         ; ← 784 = 49 × 16
0x008fa247  jb  0x8fa182
```

**A `0x310`-es korlát független megerősítés a tábla méretére: pontosan
49 rekord.**

### A konstruktor hívása

```asm
0x008fa1e6  push 0xcc              ; ← 204 bájtos objektum
0x008fa1eb  call 0x97c5d0          ; foglalás
0x008fa1f7  push [esi+0xc]         ; segédB      (a tábla +0xc mezője)
0x008fa20b  push [ctx+0x1468]
0x008fa20f  push [ctx+0x1464]
0x008fa214  push [esi+8]           ; segédA      (a tábla +8 mezője)
0x008fa215  mov  edx, [esi+4]      ; a KEZELŐ    (a tábla +4 mezője)
0x008fa218  mov  esi, eax          ; this
0x008fa21a  call 0x8f6ad0          ; a konstruktor (235 bájt)
```

### A 204 bájtos szűrő-objektum térképe

`0x008f6ad0` alapján:

| eltolás | tartalom |
|---|---|
| **`+0x00`** | vtable — **`0xcd184c`** |
| `+0x04` | 0 |
| **`+0x08`** | **a lánc-kontextus** (a hívótól) |
| **`+0x0c`** | **a KEZELŐ** — a tábla `+4` mezője |
| **`+0x10`** | **segédA** — a tábla `+8` mezője (a képen belüli vezérlő) |
| `+0x14`, `+0x18` | 0 |
| `+0x1c` | `[lánc-kontextus + 0x1464]` |
| `+0x20` | `[lánc-kontextus + 0x1468]` |
| **`+0x24`** | **segédB** — a tábla `+0xc` mezője (a sugár-számoló) |
| `+0x28` … | **a `filters=` lánc paraméterei** (a `tint` a `+0x50`-t olvassa színként, `filters-decoded.md`) |
| `+0x58`, `+0x59` | 1 (logikai jelzők) |
| `+0x5c` … `+0x68` | 0 |
| `+0x6c`, `+0x70` | 1.0f, 0.0f |
| `+0x90` | 1 |
| **`+0xe0`** | a **`_sldrRadius`** csúszka sorszáma, alapból `0xFF` |

### Ebből következik: mi a `tint` „virtuális színátalakítása"

A `filters-decoded.md` nyitva hagyta, mi a `ctx` a `tint` callbackjében:

```asm
0x008f96fa  mov  edi, dword ptr [ebp + 0x14]   ; ← MAGA A SZŰRŐ-OBJEKTUM
0x008f9718  mov  eax, dword ptr [edi + 8]      ; → a LÁNC-KONTEXTUS
0x008f971b  test eax, eax
0x008f971d  je   0x8f9736                       ; ha nincs → kimarad
0x008f972a  mov  eax, dword ptr [eax + 8]      ; a kontextus 3. függvénymutatója
0x008f972d  call eax
```

Vagyis a virtuális színátalakítás **nem a szűrő tulajdonsága**, hanem a
**lánc-kontextus** harmadik függvénymutatója — egy **renderelésenkénti
horog**, ami lehet `NULL` is (ilyenkor a lépés kimarad).

Ugyanezt a mintát használja az `ansel` (`0x008f8410`).

**Következmény a mi oldalunkra:** ha a lánc-kontextusban nincs
színátalakítás (a szokásos eset), a `tint` a **nyers** színnel dolgozik,
és a `filters-decoded.md` szerinti öt lépés a teljes recept. A
színátalakítás akkor lép be, ha a renderelés valamilyen külön
színtér-kezelést kap.

*Bizonyítottsági fok: megerősített* (a gyár ciklushatára, a konstruktor
mind a hét mezőértéke, és a `tint` callback három utasítása).

## Az effektpanel színválasztója: eredeti és PicasaPy (#5662, 2026-10-23)

### A két eredeti vezérlőréteg

Az `editpanel/colorwheel%d` effektvezérlőt nem szabad összekeverni a
`colorpickerpanel` felugró panellel. A `0x00653fb0` függvény a
`0x00ca2514` című `colorpickerpanel` típusnevet adja vissza; ez a
panelosztály neve, nem a teljes kattintási út. A Filtered B&W panelépítője
(`0x0050cf90`) hivatkozik a `CDesaturateFilter::pickcolor` és a `Pick Color`
sztringre, a leírófeldolgozó (`0x008ff550`) pedig a `<colorwheel>` mezőt
értelmezi. A 2026-10-24-i Ghidra-kimenet szerint a `0x0050cf90` maga a
panelvezérlőket állítja elő, kezeli a `colorwheel_container`, `colorwheel0`
és `slidercircle0` elemeket, és a paraméterből kapott színkomponensekből
frissíti a színkerék/slider állapotát; nincs benne kattintási koordinátáról
vagy képpontpufferből történő olvasás. Így a színkerék szerkesztőmező és a
felugró választó külön réteg, a `pickcolor` mező pipettakezelőhöz kötése
pedig külön, még nyitott kérdés.

A felugró panel osztályát a `ColorPickerPanel::vftable` azonosítja
(`0x00ca2564`); annak paletta-/MRU-építője `0x00654290`. Ez öt MRU-rekeszhez
olvassa a `Preferences` `picker::mru_%d` értékeit. A `0x00654e30` útja a
kiválasztott színt öt rekeszen át ismétlődés nélkül és eltárolja. A pipetta
viselkedését nem pusztán az ikonból következtetjük: a RTTI a
`BackbufferPickerHandler` és `BitmapPickerHandler` vtable-jét külön névvel
rögzíti (`0x00ca2620`, `0x00ca2648`); metódusaik (`0x00655150`, `0x006553d0`)
képpontszínt vesznek a kattintott koordinátán, majd a panel színbeállító
útjához (`0x00654ab0`, `0x00654c30`) adják. A `pickerpanel.tre` külön a
`globalbuttons/dropper_n` és `dropper_h` pipettagombot tartalmazza. A
geometriát a [`szerkeszto-panel-meretek.md`](szerkeszto-panel-meretek.md)
„A színválasztó komponensei” része már a `pickerpanel.tre` és a `respack.yt`
alapján méri.

### Eredeti | Nálunk | Teendő

| Eredeti | Nálunk | Teendő |
|---|---|---|
<<<<<<< HEAD
| **Belépés.** A Filtered B&W effekt panelépítője (`0x0050cf90`) létrehozza a `CDesaturateFilter::pickcolor` vezérlőt, és a `colorwheel_container`, `colorwheel0`, `slidercircle0` elemeket állítja; a `<colorwheel>` leírót a `0x008ff550` dolgozza fel. A felugró osztály neve `colorpickerpanel` (`0x00653fb0` → `0x00ca2514`). A `pickcolor` kattintásának tényleges, dinamikus célja **NINCS MEG**. | Az effekt színparamétere `EditorParamPanel.qml`-ben `TextColorSwatches`; a „Pick Color” gomb nyitja a `ColorSpectrumPicker` felugrót. | A színparaméter szerkeszthetősége igazolt. A PicasaPy felugró választójával való egyezés és a natív effect→picker eseménykapcsolat **NYITOTT**; a `0x0050cf90` panelépítése önmagában nem bizonyít pipettát. |
| **Pipetta.** A generikus natív választó két külön képpontmintázó kezelőt tartalmaz: `BackbufferPickerHandler` (`0x00655150`) és `BitmapPickerHandler` (`0x006553d0`). A helyi disassembly szerint a bitmap-út kattintási koordinátából képpontindexet számol, a bitmap színét olvassa, majd a `0x00654c30` panelútjára adja; a backbuffer-út a `0x00654ab0` útját hívja. A handler-osztályokat az RTTI a `0x00ca2620`/`0x00ca2648` címeken külön nevezi meg. Ezek általános picker-kezelők; a bekötésük a Filtered B&W `pickcolor` vezérlőjére **NINCS MEG**. | Az effekt `TextColorSwatches` ezt a 8 rögzített színt kínálja: `#ffffff`, `#000000`, `#ff0000`, `#ffff00`, `#00a651`, `#0072bc`, `#ff7f27`, `#a349a4`, továbbá spektrumot és MRU-t. A `pickNeutralColor` kizárólag a `finetune2` semleges színét írja át (`PhotoViewer.qml` → `EditController.pickNeutralColor`); nem érhető el az effekt színmezőjéből. | A natív általános picker mintáz képpontot, a PicasaPy effektmezőjében nincs ilyen út. **Az effekt szintű eltérés nem bizonyított**, mert a natív `pickcolor` bekötése nyitott; ne nyissunk erre fejlesztési jegyet a bekötés igazolása előtt. |
| **Panel és MRU-geometria.** A panel 225×225; az öt `mru_0…4` mező 26×26, x=51, 82, 113, 144, 175; a palettaréteg 181×147 az (20,15) ponton. Forrás: `pickerpanel.tre` + `respack.yt` mérés; a réteg betöltési útja `0x00654290`. Az eredeti MRU-sor y-koordinátája **NINCS MEG**; megszerzés: az öt réteg rect-adatának pontos kiolvasása a `respack.yt`-ből. | A `ColorSpectrumPicker` 225×225; 5 darab 26×26 MRU ugyanazon x-koordinátákon, y=13; spektrum 181×147 az (20,48) ponton. | A panelméret, a rekeszszám, a rekeszméret és x-osztás **EGYEZIK**. Az MRU y-helyzetét nem hasonlítottuk össze, mert az eredeti érték **NINCS MEG**. Az azonos méretű palettaréteg és spektrum helye eltér; a két natív palettakép színkészlete **NINCS MEG**. Megszerzés: a `respack.yt` `pickerpanel/palette_0` és `_1` rétegének dekódolása és a két palettamód működésének mérése. |
| **MRU-beállítás.** A panel `Preferences` alatt a `picker::mru_%d` családot olvassa és írja; öt helyet tart fenn, ismétlődő színt nem hagy a sorban (`0x00654290`, `0x00654e30`). | Öt QSettings-kulcs: `picker/mru_0…4`; az új színt előre teszi, ismétlődést kiszűri (`EditController.recentPickerColors`, `rememberPickerColor`). Üres profilnál a mi kezdeti értékünk `""`. | Az öt tartós, deduplikált MRU **EGYEZIK**. A tárhely-kulcsok neve/névtere eltér. Az eredeti hiányzó kulcsainak első induláskori értéke **NINCS MEG**; megszerzés: tiszta Picasa-profilon a Preferences-értékek mérése vagy a `0x00407a20` / `0x004019b0` alapértékút célzott visszafejtése. |
| **Natív Glimmer-színmezők alapértékei.** Az eredeti `filterdesc.xml` `selectedColor` értékei: Border outer/inner `#000000/#ffffff`; DropShadow shadow/background `#000000/#ffffff`; MuseumMatte outer/inner `#1a0e03/#f0eae4`; Polaroid outer `#e2e2e2`; RoundedEdges és Sixties outer `#ffffff`; TwoTone first/second `#004488/#ffff00`. A leíró színmezőit a `0x008ff550` dolgozza fel. | A PicasaPy `effect_params.py` ugyanezeket az értékeket adja az effektpanelnek. | **EGYEZIK** mind a 11 natív színmező értéke (a két mezős effekteknél mezőnként). |
| **Régi colorwheel új effekt alapértéke.** Az `ansel`, `tint`, `dir_tint`, `radtint` XML-leírójában `<colorwheel>` van; `selectedColor` attribútum nincs. A `<presets>` `pixel` értékét nem tekintjük automatikusan a picker induló színének. | A PicasaPy `effect_params.py` a négy mező kezdőértékének `#ffffff`-et ad. | Az eredeti üres profilú picker induló színe **NINCS MEG**; a `presets/pixel` és a picker megjelenített színének viszonya nem bizonyított. Megszerzés: a natív betöltési út célzott visszafejtése vagy friss profilban mért első megnyitás. Ebből a körből nem állítható alapérték-egyezés vagy eltérés. |
| **Kiválasztás kimenete.** A natív leíró a kiválasztott színt effekt-paraméterként köti a művelethez; az örökölt Filtered B&W `ansel` út `filters=` színparamétere `AARRGGBB` (a láncformátumot lásd a [`picasa-ini-format.md`](picasa-ini-format.md) `desat`/`ansel` részében és a `filterdesc-registry.md` `ImageFilters::PickColor` részében, `0x008fee80`). | A `TextColorSwatches` színt ad vissza az `EditorParamPanel`-nek; az előnézet a `previewEffect` útján frissül, az Alkalmaz az `applyEffectWithParams` útján menti a `filters=` értéket, a Mégse eldobja az előnézetet. A `format_param_values` a legacy színkerekeknél `ffRRGGBB`-t ír. | **EGYEZIK** abban, hogy a kiválasztás az effekt színparaméterét és előnézetét módosítja, majd az alkalmazott láncparaméterbe kerül. A képpontmintázás effekt-szintű egyezése vagy eltérése a nyitott `pickcolor` bekötés miatt **NINCS MEG**; lásd a Pipetta sort. |

**Bizonyítottsági fok: feltételes az effekt szintű viselkedésre; megerősített a két cím funkciójára.** (A) a `0x0050cf90` Ghidra-dekompilátuma a deszaturáló effekt panelmezőit és színkerék-állapotát építi; (B) a külön `0x00655150`/`0x006553d0` disassembly-k és RTTI a generikus picker tényleges képpontolvasó kezelőit azonosítják. Ez alátámasztja, hogy a `0x0050cf90` nem maga a képpontmintázó rutin, de nem bizonyítja, hogy a `pickcolor` esemény nem indítja el máshol a generikus pickert. **Cáfoló kísérlet:** megpróbáltam cáfolni azt az állítást, hogy a `0x0050cf90` saját pixelminta-út. A dekompilátum és a teljes célzott disassembly vezérlőazonosítókat, színkomponensek átvételét és UI-állapotfrissítést mutat; a kattintási koordinátából mintázó művelet viszont a két külön handlerben látható. A cáfolat csak a `0x0050cf90` szerepére érvényes, az effekt bekötése és a nyitás eseményútja nyitott.
=======
| **Belépés.** A Filtered B&W effekt paneljén van `Pick Color` színkerék (`0x0050cf90`, `0x008ff550`; a sztring címe `0x00c87088`). A felugró osztály neve `colorpickerpanel` (`0x00653fb0` → `0x00ca2514`). | Az effekt színparamétere `EditorParamPanel.qml`-ben `TextColorSwatches`; a „Pick Color” gomb nyitja a `ColorSpectrumPicker` felugrót. | **EGYEZIK** a színparaméter szerkeszthetősége. A colorwheel-kattintás és a panelosztály közti natív dinamikus kötés pontos belépési pontja **NINCS MEG**; lásd a nyitott kérdést. |
| **Pipetta.** A natív választóban van képpontot mintázó út: `BackbufferPickerHandler` (`0x00655150`) és `BitmapPickerHandler` (`0x006553d0`), panelen át `0x00654ab0` / `0x00654c30`; az ikonréteg `globalbuttons/dropper_n/_h`. | Az effekt `TextColorSwatches` csak ezt a 8 rögzített színt kínálja: `#ffffff`, `#000000`, `#ff0000`, `#ffff00`, `#00a651`, `#0072bc`, `#ff7f27`, `#a349a4`, továbbá spektrumot és MRU-t. A `pickNeutralColor` kizárólag a `finetune2` semleges színét írja át (`PhotoViewer.qml` → `EditController.pickNeutralColor`); nem érhető el az effekt színmezőjéből. | **ELTÉR.** A generikus effekt-színválasztóba képpontmintázó mód kell, amely a kiválasztott színt a mezőhöz és az effekt előnézetéhez küldi. |
| **Panel és MRU-geometria.** A panel 225×225; az öt `mru_0…4` mező 26×26, x=51, 82, 113, 144, 175, **y=15** (rétegrekord: `pickerpanel/rect: mru_0` = (51,15)-(77,41)); a palettaréteg 181×147 az (20,15) ponton (`pickerpanel/palette_0` és `_1`, rétegrekord). Betöltési út: `0x00654290`. **Bizonyítottsági fok: erős.** A rétegrekord mért (`respack.py list` és a 13 bájtos fejléc); a [respack-formátum 10.2](picasa-respack-format.md) szerint a hely a rétegrekordból jön, a szülő `pickerpanel/base` (12,8) eltolása a binárisban nincs külön visszafejtve. | A `ColorSpectrumPicker` 225×225; 5 darab 26×26 MRU ugyanazon x-koordinátákon, y=13; spektrum 181×147 az (20,48) ponton. | A panelméret, a rekeszszám, a rekeszméret és x-osztás **EGYEZIK**. Az MRU y-helyzete **ELTÉR**: nálunk 13, az eredeti 15 (2 px); javítás: `ColorSpectrumPicker.qml:94`. A palettaréteg helye **ELTÉR**: az eredeti (20,15), nálunk a spektrum (20,48), 33 px. A két palettakép színkészletét és a palettamód-váltót a következő sor méri. |
| **Palettamód és színkészlet.** Két palettakép van: `pickerpanel/palette_0` és `palette_1`, mindkettő 181×147 (rétegrekord). **Váltó:** a `Property palette N` tulajdonság (`N` = 0 vagy 1). A `0x00653ff0` a `palette` nevű tulajdonság sztringjét `%d` formátummal olvassa (`0xca2528` a név, `0xc81844` a formátum), és a `[obj+0x2f8]` mezőbe írja (`0x006540d2`); a `0x00654290` a `%s/palette_%d` névvel csak ezt az egy réteget tölti be. **Alap: 0.** A konstruktor (`0x00654150`) nullázza a mezőt (`0x00654209`), és a `pickerpanel.tre` nem ad tulajdonságot. A `.tre` példányai: `palette 1` csak a `collagepanel/picker_panel` (`bkgcolorpick`) példányon áll; `palette 0` a `makemoviepanel` bkg/text, a `printoptions` border/text és az `edittextpanel` fill/outline példányokon. **Színkészlet (mért, dekódolt pixelek):** a felső 56 sor (0-55) mindkét palettán bájtra azonos: 4996 telt képpont, 204 különböző RGB. Az alatti sorokban (56-146) a `palette_0` 16 380 telt képpontján 15 223 különböző RGB van, átlagos telítettség 59,0%, fényerő 69,2%; a `palette_1`-en 13 880 különböző RGB, telítettség 40,9%, fényerő 61,7%. A `#palette_0 old` és `#palette_1 old` rétegek (180×111) nincsenek a `.tre`-ben, nem töltődnek be. **Bizonyítottsági fok:** a váltó és az alap **erős** (egy kódúton: tulajdonságolvasó, konstruktor-nullázás, `.tre`-példányok); a színkészlet **megerősített** (a pixelek számlálása és a két kirenderelt kép szerkezeti egyezése). | **Egy palettamód van.** A színmező a `ColorSpectrumPicker.qml:113-117` `spectrumField` elemében: `Qt.hsva(hue, 1, 1, 1)` alapszín, rá vízszintes fehér-átlátszó és függőleges átlátszó-fekete átmenet (HSV-négyzet), 181×147 az (20,48) ponton. Nincs felső színsáv és nincs második palettakép. Alatta két vízszintes sáv van (y=198, 181×12; y=213, 181×10), amelyeknek az eredeti `pickerpanel`-rétegkészletben nincs megfelelője. | **ELTÉR**, és a palettamód hiányzik. A két palettakép szerkezetét (felső 56 soros színsáv, alatta a mért átmenet) nálunk nem követjük. Teendő: a spektrumterület kövesse az eredeti szerkezetet. A pixelképet nem másoljuk a repóba: a `respack.py` jogi megjegyzése szerint a kinyert grafika nem terjeszthető; a szerkezetet és a mért színstatisztikát követjük. A `palette` tulajdonság (0/1) bevezetése a `bkgcolorpick` példányhoz a fejlesztői jegy döntése. |
| **MRU-beállítás.** A panel a `Preferences` szakaszból olvassa és írja a `picker::mru_%d` kulcsokat (sablon: `0xca254c`; hívó: `0x00654290` ciklusa, `0x006543d5`); öt helyet tart fenn, ismétlődő színt nem hagy a sorban (`0x00654e30`). **Hiányzó vagy üres kulcs első értéke: `"*"`** (egy bájt, 0x2A). A `0x00407a20` a `0x00407aba`-`0x00407ace` ágon: ha a kulcs nincs, vagy az érték üres, a `0xc7f514` literált adja ki (`push 0xc7f514; mov eax, 1`; a literál tartalma `*`). A `0x80000001` (HKEY_CURRENT_USER) a `0x00407a43` hívásban áll. A `0x004019b0` a kulcsot `0xf003f` (KEY_ALL_ACCESS), majd `0x20019` (KEY_READ) maszkkal nyitja; a visszakapott sztring mutatóját a `0x00654290` az MRU-réteg `+0x268` mezőjébe írja (`0x006543e9`). **Bizonyítottsági fok: erős** (egy kódúton; az ágazás és a literál külön ellenőrizve; futtatott Picasa-mérés nincs). | Öt QSettings-kulcs: `picker/mru_0…4`; az új színt előre teszi, ismétlődést kiszűri (`EditController.recentPickerColors`, `rememberPickerColor`). Üres profilnál a mi kezdeti értékünk `""` (`edit_controller.py:557`), a rekesz átlátszó (`ColorSpectrumPicker.qml:97`). | Az öt tartós, deduplikált MRU **EGYEZIK**. A tárhely-kulcsok neve/névtere eltér. **Üres profil: ELTÉR.** Az eredeti `"*"`, nálunk `""`. A `"*"` megjelenése a rekeszben **NINCS MEG** (az MRU-réteg `+0x268` mezőjének rajzolója nincs visszafejtve), ezért a `""` → `"*"` átállításról még nem születhet döntés; első lépés a rajzoló visszafejtése. |
| **Üres MRU-rekesz rajza (K5).** A `0x00407a20` hiányzó kulcs ága (`0x00407ace`) a `0x00c7f514` címen lévő `2a 00` bájtsort adja (`"*"`). A `0x009a4890` `0x009a490d` utasítása a `0x2a` első bájtot külön kezeli, és a `0x009a4939` ponton nulla EAX-szal tér vissza; a `0x00654290` a `0x004019b0` eredményét a `ytColorRectNode +0x268` színmezőjébe írja (`0x006543de-0x006543e9`). A nullaszínű dinamikus réteg nem rajzol színt (`0x00a66570`, `0x00a65a50`). Alatta az aktív `pickerpanel/mru_0` erőforrás egyszínű, teljesen fedő 26×26-os `#00B2BD` rétege marad; a keretet a `pickerpanel/bezels` adja. Forrás: bináris és `pickerpanel.tre` + `respack.yt` pontos pixelmérés. | A `ColorSpectrumPicker.qml` üres MRU-modellje öt `""`; a delegate `modelData || "transparent"` kitöltést használ, kerettel. | **MEGERŐSÍTETT ELTÉR.** Az eredeti hiányzó kulcs nem ad átlátszó MRU-négyzetet: a statikus színréteg látszik. A `mru_0…4` pontos statikus kitöltése: `#00B2BD`, `#87A2B0`, `#007BC4`, `#00727C`, `#692DAC` (mind 26×26, alpha=255; `respack.yt` pixelmérés). Fejlesztési jegyjavaslat: az üres MRU-rekeszek jelenítsék meg a megfelelő eredeti alapkitöltést. |
| **A paletta alatti sávok (K6).** A `pickerpanel` paletta 181×147-es, `(20,15)`-től `(201,162)`-ig; az aktív `base` réteg `(12,8)`-`(215,179)`. A `.tre`-ben nincs alsó sáv/slider réteg; a `docbounds` alpha=0. A `ColorPickerPanel` vtable-jének 29. bejegyzése megegyezik a `ytDrawNode` megfelelő bejegyzésével (`0x009e3c70`); a panelépítő (`0x00654290`) az öt MRU-színréteget, a `ResCreate`-út (`0x00653ff0`) a palettaképet hozza létre. | `ColorSpectrumPicker.qml` két további sávot rajzol: aktuális szín `y=198, h=12`; hue-gradiens `y=213, h=10` (`ColorSpectrumPicker.qml:150-165`). | **MEGERŐSÍTETT ELTÉR.** Az eredeti panel építési/rajzolási útján és aktív `pickerpanel/*` erőforrásai között nincs a paletta alatti két sávnak megfelelő elem. A két QML-sávhoz fejlesztési jegyjavaslat: eltávolításuk az eredeti panelhez igazodó felugróból. |
| **Natív Glimmer-színmezők alapértékei.** Az eredeti `filterdesc.xml` `selectedColor` értékei: Border outer/inner `#000000/#ffffff`; DropShadow shadow/background `#000000/#ffffff`; MuseumMatte outer/inner `#1a0e03/#f0eae4`; Polaroid outer `#e2e2e2`; RoundedEdges és Sixties outer `#ffffff`; TwoTone first/second `#004488/#ffff00`. A leíró színmezőit a `0x008ff550` dolgozza fel. | A PicasaPy `effect_params.py` ugyanezeket az értékeket adja az effektpanelnek. | **EGYEZIK** mind a 11 natív színmező értéke (a két mezős effekteknél mezőnként). |
| **Régi colorwheel új effekt alapértéke.** Az `ansel`, `tint`, `dir_tint`, `radtint` XML-leírójában `<colorwheel>` van; `selectedColor` attribútum nincs. A `<presets>` `pixel` értékét nem tekintjük automatikusan a picker induló színének. | A PicasaPy `effect_params.py` a négy mező kezdőértékének `#ffffff`-et ad. | Az eredeti üres profilú picker induló színe **NINCS MEG**; a `presets/pixel` és a picker megjelenített színének viszonya nem bizonyított. Megszerzés: a natív betöltési út célzott visszafejtése vagy friss profilban mért első megnyitás. Ebből a körből nem állítható alapérték-egyezés vagy eltérés. (A MRU-rekeszek `"*"` alapértéke más kérdés: az a rekesz tartalma, nem a panel induló színe.) |
| **Kiválasztás kimenete.** A natív leíró a kiválasztott színt effekt-paraméterként köti a művelethez; az örökölt Filtered B&W `ansel` út `filters=` színparamétere `AARRGGBB` (a láncformátumot lásd a [`picasa-ini-format.md`](picasa-ini-format.md) `desat`/`ansel` részében és a `filterdesc-registry.md` `ImageFilters::PickColor` részében, `0x008fee80`). | A `TextColorSwatches` színt ad vissza az `EditorParamPanel`-nek; az előnézet a `previewEffect` útján frissül, az Alkalmaz az `applyEffectWithParams` útján menti a `filters=` értéket, a Mégse eldobja az előnézetet. A `format_param_values` a legacy színkerekeknél `ffRRGGBB`-t ír. | **EGYEZIK** abban, hogy a választás az effekt színparaméterét és előnézetét módosítja, majd az alkalmazott láncparaméterbe kerül. A kiválasztóban történő színmintavétel kivétel: a fenti pipetta-eltérés miatt hiányzik. |

#### Palettamód és színkészlet: mérési szabály

A két natív réteget a `respack.yt` dekódolója 181×147 RGBA-képpé bontja
(rect: `x=[20,201), y=[15,162)`, réteg-alfa: 256/256, RLE-kódolás: 1,
26 607 képpont rétegenként). A nyers rétegadat külön RLE-dekódolásának RGBA-
kimenete bájtról bájtra egyezik a PNG dekódolt RGBA-pixeladataival. A két kép
10 227 egyező és 16 380
eltérő képpontot tartalmaz; az eltérések a fő mezőben vannak (`x=1…180`,
`y=56…146`). Az `y=0…55` felső sáv teljesen azonos.

A színmező belsejének mért szabálya:

```text
H(x) = a két szomszédos, lent felsorolt (x,100) RGB-minta HSL-színárnyalata
       közötti lineáris interpoláció, fokban
L(y) = a két szomszédos, lent felsorolt (90,y) RGB-minta HSL-világossága
       közötti lineáris interpoláció, 0…255 skálán
S0   = 163/253; S1 = 97/253
RGBm(x,y) = round-half-up(sRGB_HSL_to_RGB(H(x), Sm, L(y)/255) × 255)
```

A képlet mérési tartománya mindkét módnál `x=2…179`, `y=56…144`;
a határmaszk és a közös felső grafika nem része a modellnek. A színárnyalat-
horgonyok a `palette_0` `(x,100)` pontjainak egész RGB-értékei, `x =
1,6,11,…,176,180`; a világosság-horgonyok ugyanennek a képnek a `(90,y)`
pixelei, `y = 56,61,…,141,144`. A HSL-értékeket a felsorolt 8 bites
RGB-mérésekből a szabványos, 8 bites sRGB-kódértékeken értelmezett HSL-képlet
adja (`H∈[0°,360°)`, `S,L∈[0,1]`); szabad illesztett paraméter nincs.

```text
H-horgonyok: x:(R,G,B)
1:(213,64,62); 6:(210,64,47); 11:(210,87,47); 16:(210,115,47);
21:(210,143,47); 26:(210,169,47); 31:(210,192,47); 36:(210,209,47);
41:(196,210,47); 46:(175,210,47); 51:(149,210,47); 56:(121,210,47);
61:(95,210,47); 66:(70,210,47); 71:(52,210,47); 76:(47,210,55);
81:(47,210,75); 86:(47,210,102); 91:(47,210,130); 96:(47,210,157);
101:(47,210,183); 106:(47,210,204); 111:(47,204,210); 116:(47,184,210);
121:(47,160,210); 126:(47,132,210); 131:(47,105,210); 136:(47,79,210);
141:(47,59,210); 146:(48,47,210); 151:(67,47,210); 156:(91,47,210);
161:(119,47,210); 166:(148,47,210); 171:(174,47,210); 176:(196,47,210);
180:(212,62,213)

L-horgonyok: y:(R,G,B)
56:(234,250,241); 61:(219,247,232); 66:(199,242,220);
71:(176,238,205); 76:(150,233,189); 81:(124,226,172);
86:(99,221,156); 91:(76,217,143); 96:(58,212,130);
101:(45,209,122); 106:(42,195,114); 111:(38,179,105);
116:(34,158,92); 121:(29,135,79); 126:(24,112,65);
131:(19,89,52); 136:(15,69,41); 141:(11,52,31); 144:(9,44,26)
```

`S0` és `S1` a két kép `(90,100)` színéből adódik: `palette_0` RGB
`(47,210,124)`, `palette_1` RGB `(80,177,125)`; mindkettő HSL-világossága
128,5/255. A nyers erőforrás-képekből számolt belső tartomány hibája:

| Mód | Pontosan egyező pixel | Átlagos abszolút csatornahiba | Maximum csatornahiba |
|---|---:|---:|---:|
| `palette_0` | 4 626 / 15 842 (29,20%) | 0,381475 csatornaszint | 3 csatornaszint |
| `palette_1` | 4 870 / 15 842 (30,74%) | 0,435467 csatornaszint | 3 csatornaszint |

Képletpróba (helyi képpont-koordináta, elvárt RGB): `(90,100)` `#2FD27C` /
`#50B17D`; `(45,100)` `#B4D22F` / `#9FB150`; `(135,100)` `#2F53D2` /
`#5065B1`; `(90,56)` `#EAFAF1` / `#EDF6F1`; `(90,144)` `#092C1A` /
`#10251A` (`palette_0` / `palette_1`). Az egyszerű, egyenletesen léptetett
árnyalat- és lineáris világosságtengely ellenpróbája (H: 0°…300° egyenletesen
x mentén; L: a két y-végpont között lineárisan) rosszabb eredményt ad:
átlagos csatornahiba 4,037 / 3,802, maximum 25 / 19; ezért ez a leegyszerűsítés
nem reprodukálja a mért profilt. A mező szélén (`x=1` vagy `180`, illetve
`y=145…146`) a fenti belső modellre a maximumhiba 19 szintre nő; a képlet
nem állít teljes 181×147 képpontra pontos rajzolást.

A felső sáv 30 közös, egyenként 6×12 képpontos mintából áll (`y=43…54`,
`x=1…180`), ezért képletes színátmenet helyett a mért fix színkészlet kell:
`#63001E, #B10039, #895227, #C47338, #D39815, #E9A518, #FFBD00,
#FFD154, #C8C866, #E3E274, #629C33, #85CD44, #8AB28D, #A8D8AB,
#00727C, #00B2BD, #87A2B0, #A6C7D7, #A9D1E7, #CDE7F6, #007BC4,
#0091E1, #002455, #004BAA, #586695, #778CCA, #38175A, #692DAC,
#C88DAC, #E3A1C4`.

**Bizonyítottsági fok.** A palettamező HSL-szabálya **megerősített**: (A) a
37 árnyalat- és 19 világosság-horgonypontból, szabad paraméter nélkül
felépített tengelyprofil legfeljebb 3 csatornaszint eltéréssel adja vissza
mindkét mód belső mezőjét; (B) független HSL-kalibráció az
`(x+y) mod 5 = 0` képpontokat ellenőrzőhalmaznak kihagyva ugyanott
legfeljebb 2 csatornaszint hibát mért. A bináris út ettől külön
megerősíti, hogy a `palette` egész értéke a statikus `palette_0` / `_1`
erőforrás nevének kiválasztására szolgál, nem a natív futásidejű színképlet
forrása. A pipetta eltérése továbbra is **megerősített**: (A) a natív
handler-metódusok képpontszínt olvasnak és a panel színbeállító útjára adják;
(B) ettől függetlenül a natív `dropper` gombréteg és a handler-osztályok
RTTI-je is létezik. A PicasaPy ellenőrzése két külön úton egyezik: (A) a
teljes színmező QML-útja csak paletta/spektrum/MRU bemenetet köt be; (B) az
egyetlen képpontmintázó slot a `finetune2` semleges színére ír. A natív
nyitási esemény továbbra is nyitott; az MRU-alapérték a fenti MRU-sor szerint lezárult (#5728). A #5734 K5 és K6 válasza **megerősített**: K5-höz (A) a hiányzó beállítás `"*"` alapértékének kiolvasása, a parser külön `0x2a` ága és a `ytColorRectNode` színmezője; (B) ettől függetlenül az aktív, teljesen fedő `mru_0` erőforrás és a `bezels` réteg pontos mérése. K6-hoz (A) a `pickerpanel/*` rétegek pontos listája és határai; (B) a `ColorPickerPanel` vtable-bejegyzésének összevetése a `ytDrawNode`-éval, valamint a panelépítő és `ResCreate` út dinamikus elemkészlete. Cáfoló körként a rejtett régi palettarétegek, a rejtett `mru_5`, a `docbounds` és a releváns egyedi vtable-metódusok is ellenőrizve lettek; egyik sem ad alsó sávot. A natív nyitási esemény, az effektpaletták tényleges színkészlete és a teljesen új picker induló színe továbbra is nyitva marad.
>>>>>>> origin/main

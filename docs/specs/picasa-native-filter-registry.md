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
**nyitva**, hogy mit csinál és melyik effekt használja — ehhez a `0x00bbd630`
és a `0x00bc4ae0` dekompilálása kell.

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

#### ⚠️ A `radsat` nálunk NEM ezt használja

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

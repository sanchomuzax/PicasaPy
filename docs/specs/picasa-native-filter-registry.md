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

### 1. A `desat` — a 43. szűrő, ami nincs a 42 elemű táblában

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

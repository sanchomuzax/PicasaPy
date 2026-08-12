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

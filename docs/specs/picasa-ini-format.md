# Specifikáció: `.picasa.ini` formátum

Forrás: NotebookLM „Picasa metaadatok és adatbázisok dekódolási útmutatója"
(notebook ID: `f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e`), elsődlegesen Franz Buchinger
public domain visszafejtése (Picasa 3.8) és a hozzá tartozó GitHub-gist kommentek.

A PicasaPy **kétirányú** kompatibilitást céloz: ugyanazt a formátumot olvassa és írja,
mint az eredeti Picasa 3.x.

## Általános szabályok

- Rejtett fájl minden figyelt képmappa gyökerében: `.picasa.ini`
  (korai verziókban `Picasa.ini`).
- Szabványos INI szintaxis; a szekciófejlécek a mappában lévő fizikai fájlnevek,
  illetve speciális szekciók (`[Picasa]`, `[Contacts]`, `[Contacts2]`, `[.album:token]`).
- Redundáns tároló: a központi adatbázis ebből + a képek EXIF/XMP adataiból
  teljesen újraépíthető.
- **Round-trip elv (PicasaPy):** minden nem értelmezett kulcsot változatlanul meg kell
  őrizni és visszaírni (pl. `backuphash`, ismeretlen mezők).

## Szekciók

### `[Picasa]` — album-/mappaszintű metaadat
| Kulcs | Példa | Jelentés |
|---|---|---|
| `name` | `Foo Bar birthday` | album neve |
| `category` | `Folders on Disk` | lokális album kategória |
| `P2category` | `Downloaded Albums~otheruserid` | webalbumból letöltött album |
| `<user>_lh` | `joedoe_lh=5620038667642797505` | feltöltött album web-azonosítója |

### `[Contacts]` / `[Contacts2]` — személyek
- `[Contacts]` (Google-fiókkal): `<person_id>=<user>_lh,<hex_id>`
- `[Contacts2]` (csak lokális): `<person_id>=Név;;`  pl. `b8e4117cf1d6615b=Roy Avery;;`
- `person_id`: 64 bites hex. Még nem megerősített / azonosítatlan arc: `ffffffffffffffff`.
- A nevek elsődleges forrása a központi `contacts.xml` (ld. pmp-database.md).

### `[<fájlnév.ext>]` — képbejegyzések
| Kulcs | Példa | Jelentés |
|---|---|---|
| `star` | `yes` | csillagozott |
| `caption` | `dummy` | felirat (JPEG-nél IPTC Caption-be kerül, nem ide!) |
| `keywords` | `beer,empanadas` | címkék (JPEG-nél IPTC Keywords-be) |
| `rotate` | `rotate(1)` | 90°-os forgatás lépések (0–3) |
| `filters` | ld. lentebb | nem-destruktív szerkesztési lánc |
| `redo` | `redo=crop64=1,...;` | visszavonási (redo) verem — megőrzendő! |
| `faces` | `rect64(3f84...),8e62...;` | arcok: rect64 + contact_id párok `;`-vel |
| `albums` | `65d12673f3b51e3f...` | album-tokenek CSV listája |
| `crop` | `crop=rect64(...)` | (előfordul filters-en kívül is) |
| `geotag` | `33.770556,-84.293055` | GPS |
| `width`,`height` | `5184`, `3456` | képméret cache |
| `moddate` | `8094e2826277cd01` | módosítási idő (bináris FILETIME jellegű) |
| `backuphash` | `36003` | dekódolatlan — változatlanul visszaírandó |
| `originhash` | `033f1132c874...` | szerkesztési verem integritás-hash |
| `IIDLIST_<user>_lh` | `4dfe636c9cf4c302` | webre feltöltött kép 64-bit hex ID |
| `screensaver` | `yes` | képernyővédőben szerepel |
| `text`,`textactive` | ld. Buchinger-doksi | szövegfelirat-overlay paraméterei |

### `[.album:<token>]` — virtuális albumok
- `token`: 32 hex karakteres azonosító, pl. `604c294a68b0de9cc9222c4714f289d5`
- Mezők: `name`, `token`, `date` (ISO 8601), `description`, `location`, `<name>_lh`
- A képek `albums=` kulcsa hivatkozik a tokenekre (CSV).
- Ritkán: `[photoid]` szekció `<64-bit id>=Fájlnév.jpg` sorokkal.

## A `filters=` lánc

Pontosvesszővel elválasztott lista, sorrend = alkalmazási sorrend:

```
filters=enhance=1;crop64=1,45930000ba03defe;finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;
```

Bejegyzésformátum: `<azonosító>=1[,<param1>,<param2>...];`

Paramétertípus-jelölés (Buchinger): `!` = float 0..1 (6 tizedes), `!!` = tetszőleges
float, `#` = 32-bit hex szín (pl. `fff7f5f3`), `[]` = rect64 crop téglalap.

| Szűrő | Paraméterek | Leírás |
|---|---|---|
| `crop64` | `1,RECT64` | kivágás |
| `tilt` | `1,!szög,!skála` | döntés + skálázás (levágás elkerülése) |
| `redeye` | `1` | vörösszem-eltávolítás |
| `enhance` | `1` | „I'm Feeling Lucky" automata |
| `autolight` | `1` | auto kontraszt (hisztogram-széthúzás) |
| `autocolor` | `1` | auto színegyensúly (fehérpont) |
| `retouch` | `1` | retusálás |
| `finetune2` | `1,!fill,!highlights,!shadows,#színhő,!ismeretlen` | finomhangolás panel |
| `unsharp2` | `1,!amount` | élesítő maszk |
| `sepia` | `1` | szépia |
| `bw` | `1` | fekete-fehér |
| `warm` | `1` | melegítés |
| `grain2` | `1` | filmszemcse |
| `tint` | `1,!!preserve,#szín` | színezés |
| `sat` | `1,!telítettség` | telítettség |
| `radblur` | `1,!x,!y,!size,!amount` | radiális elmosás |
| `glow2` | `1,!intenzitás,!!sugár` | ragyogás |
| `ansel` | `1,#szín` | művészi f/f színezéssel |
| `radsat` | `1,!x,!y,!sugár,!élesség` | radiális telítettség |
| `dir_tint` | `1,!x,!y,!gradiens,!árnyék,#szín` | irányított színátmenet |

Szöveg-overlay (külön kulcs): `text=1; 136;11;sample text;Aharoni;...` + `textactive=`.

Nyitott kérdés: `finetune2` utolsó paramétere azonosítatlan; `enhance`/`autolight`/
`autocolor` pontos algoritmusa nem publikus → pixelhű validálás szükséges
(ld. research-plan.md).

## `rect64` kódolás (crop + arcok)

`rect64(3f845bcb59418507)` — 16 hex karakter = 4×16 bit: **left, top, right, bottom**.

**FIGYELEM (picasa2digikam-ból validálva):** az érték rövidebb is lehet 16
karakternél — a Picasa elhagyja a vezető nullákat! Dekódolás előtt kötelező a
`zfill(16)` (balról nullákkal feltöltés).

Dekódolás: minden 4-karakteres szegmens → int(hex) / 65536 → relatív [0.0..1.0]
koordináta. Abszolút pixel: left/right × képszélesség, top/bottom × képmagasság.
Megjelenítésnél/exportnál az **EXIF-orientációt** (1/3/6/8) is alkalmazni kell a
koordinátákra (transzformációs képletek: picasa2digikam `rect64.py`).

Ellenőrző példa: `3f845bcb59418507` →
left≈0.248108, top≈0.358566, right≈0.348648, bottom≈0.519638.

Kódolás (írás): round(koord × 65536) → 4 hex jegy, nullákkal feltöltve; a vezető
nullák megőrzendők (a `crop64=1,10000000f1ddff49` példában is).

XMP-konverzió: MWG-RS régió séma + `HierarchicalSubject` `people|Név` címkék
(digiKam/Lightroom/Bridge kompatibilis).

## Írási szabályok (PicasaPy, kétirányú kompatibilitáshoz)

1. Atomikus írás (temp fájl + rename), írás előtti backup.
2. Nem értelmezett kulcsok/szekciók bitre pontos megőrzése.
3. JPEG-nél caption/keywords az IPTC-be, NEM az ini-be (a Picasa is így tesz);
   RAW és egyéb formátumnál az ini-be.
4. `redo=` és `originhash` érintetlenül hagyása, ha a szerkesztési lánc nem változott.
5. Fájl-lock / ütközésdetektálás arra az esetre, ha az eredeti Picasa is fut.

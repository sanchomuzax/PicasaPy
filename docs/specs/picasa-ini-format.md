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
- **Szekciónév-illesztés kis-nagybetű-tűrő (PicasaPy, #296):** a
  fájlbejegyzés-szekciók neve fizikai fájlnév, a Picasa pedig Windows/NAS
  fájlrendszeren fut, ahol a fájlnév kis-nagybetű-független — a `[IMG_1234.JPG]`
  fejléc ugyanazt a képet jelöli, mint a lemezen lévő `IMG_1234.jpg`. A feloldás
  előbb PONTOS egyezést keres, és csak utána esik vissza a kis-nagybetűtől
  független illesztésre (pontos találat mindig nyer). A kulcsneveket ugyanígy,
  kis-nagybetű-tűrően illesztjük. Íráskor **az ini-ben talált eredeti betűzés
  marad a `[...]` fejlécben** (round-trip elv): nem írjuk át a saját
  névváltozatunkra, és nem hozunk létre második szekciót ugyanarra a fájlra.

## Szekciók

### `[encoding]` — kódolás-jelző (Picasa3.exe string-tábla, 2026-08-05)

A `Picasa3.exe` ini-író format-string blokkjából (ld.
`docs/specs/picasa-exe-strings.md`) előkerült szekció, amit a korábbi kutatási
körök nem dokumentáltak:

```
[encoding]
utf8=1
```

Az író-kód literálisan ezt a szekciót írja a `[Picasa]` elé; az `utf8=1`
jelzi, hogy a fájl tartalma UTF-8 kódolású. A PicasaPy-nak meg kell őriznie
(round-trip), és UTF-8 fájl írásakor mindig ki kell adnia.

### `[Picasa]` — album-/mappaszintű metaadat
| Kulcs | Példa | Jelentés |
|---|---|---|
| `name` | `Foo Bar birthday` | album neve |
| `category` | `Folders on Disk` | lokális album kategória |
| `P2category` | `Downloaded Albums~otheruserid` | webalbumból letöltött album |
| `<user>_lh` | `joedoe_lh=5620038667642797505` | feltöltött album web-azonosítója |
| `contactsversion` | — | globális verziószám (kontakt-adatbázis); exe-ből azonosított, élő ini-ben még nem validált — megőrzendő |
| `frversion` | — | globális verziószám (feltehetően arcfelismerés); exe-ből azonosított, élő ini-ben még nem validált — megőrzendő |
| `gpsversion` | — | globális verziószám (GPS-adatok); exe-ből azonosított, élő ini-ben még nem validált — megőrzendő |
| `colorspaceversion` | — | globális verziószám (színtér-adatok); exe-ből azonosított, élő ini-ben még nem validált — megőrzendő |
| `rawversion` | — | globális verziószám (RAW-feldolgozás); exe-ből azonosított, élő ini-ben még nem validált — megőrzendő |
| `date` | `2019-07-04` | **PicasaPy-kiterjesztés (#320), élő Picasa-ini-ben validálandó** — a mappa dátumának KÉZI felülírása (ISO 8601, év-hónap-nap). Nem a hivatalos formátum dokumentált kulcsa: sem a Buchinger-visszafejtés, sem az exe string-tábla nem sorol fel mappa-szintű `date`-et (csak az albumoknál, `[.album:token]` alatt van ilyen). Hiányában a mappa dátuma a legrégebbi kép felvételi ideje (`index/sync.py`). Kód: `picasapy.ini.folder_date`. |

(A verzió-kulcsok forrása: `Picasa3.exe` string-tábla, ld.
`docs/specs/picasa-exe-strings.md` 2. pont — feltehetően adatbázis-migrációs
számlálók, jelentésük tisztázatlan, de round-trip-ben megőrzendők.)

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
| `geotag` | `33.770556,-84.293055` | GPS — szélesség,hosszúság tizedes fokban; a PicasaPy olvassa ÉS írja (#30). A kép helye: `geotag=` > EXIF GPS-IFD; törléskor csak a kulcs tűnik el, a fájl EXIF-je érintetlen. |
| `width`,`height` | `5184`, `3456` | képméret cache |
| `moddate` | `8094e2826277cd01` | módosítási idő (bináris FILETIME jellegű) |
| `backuphash` | `36003` | dekódolatlan — változatlanul visszaírandó |
| `originhash` | `033f1132c874...` | szerkesztési verem integritás-hash |
| `IIDLIST_<user>_lh` | `4dfe636c9cf4c302` | webre feltöltött kép 64-bit hex ID |
| `screensaver` | `yes` | képernyővédőben szerepel |
| `text`,`textactive` | ld. Buchinger-doksi | szövegfelirat-overlay paraméterei |
| `hidden` | `hidden=yes` (feltételezett) | elrejtett kép — exe-ből azonosított (Picasa3.exe string-tábla), élő ini-ben még nem validált |
| `flipped` | `flipped(0)` (format-string) | tükrözés, a `rotate(N)` mintájára; exe-ből azonosított, élő ini-ben még nem validált |
| `edit_width`,`edit_height` | — | szerkesztett (crop utáni) méret cache-elése, feltehetően a `width`/`height` mintájára; exe-ből azonosított, élő ini-ben még nem validált |
| `moviestart`,`movieend` | `moviestart=`, `movieend=` | videó lejátszási/vágási pontok; exe-ből azonosított, élő ini-ben még nem validált |

**Kód-szintű állapot (#348):** a fenti új kulcsok (`[encoding]`/`utf8`, a
`[Picasa]` verziószámok, `hidden`, `flipped(N)`, `edit_width`/`edit_height`,
`moviestart`/`movieend`) mindegyike a meglévő, generikus sor-alapú
round-trip rétegen (`picasapy.ini.document`) megy át — a réteg tartalom-
agnosztikus, ezért ezeket külön kódmódosítás nélkül is bitre pontosan
megőrzi; ezt a `tests/ini/test_new_keys_348.py` teszt zárja le. A `hidden`
kulcs emellett a szinkron-rétegben (`index/sync.py`) tipizált `bool`-ként
is fel van dolgozva (ld. `PhotoRecord.hidden`). A „élő ini-ben még nem
validált" jelölés a fenti kulcsokra egyelőre marad — ehhez tényleges NAS-os
`.picasa.ini`-fájlokban kell megkeresni az előfordulásukat (a jegy 2.
pontja), ami külön, a felhasználó gépén/NAS-án végzendő lépés.

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
| `crop64` | `1,RECT64` | kivágás — a Picasa MELLÉ külön `crop=rect64(...)` kulcsot is ír |
| `tilt` | `1,!szög,!skála` | döntés; a skála-mező élesben jellemzően `0.000000` = „számítsd ki a kitöltő skálát" (#73) |
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
| `tint` | `1,!!preserve[,#szín]` | színezés — a szín OPCIONÁLIS: élő ini-ben megerősítve (#357), hiányában a Picasa az alapértelmezett (fehér) színnel értendő |
| `sat` | `1,!telítettség` | telítettség |
| `radblur` | `1,!x,!y,!size,!amount` | radiális elmosás |
| `glow2` | `1,!intenzitás,!!sugár` | ragyogás |
| `ansel` | `1[,#szín]` | művészi f/f színezéssel — a szín OPCIONÁLIS: élő ini-ben megerősítve (#357) |
| `radsat` | `1,!x,!y,!sugár,!élesség` | radiális telítettség |
| `dir_tint` | `1,!x,!y,!gradiens,!árnyék[,#szín]` | irányított színátmenet — a szín OPCIONÁLIS: élő ini-ben megerősítve (#357) |
| `glow` (v1) | ismeretlen | ragyogás v1 (a `glow2` mellett) — token az exe string-táblájában megerősítve, paraméterezése dekódolatlan |
| `grain` (v1) | ismeretlen | filmszemcse v1 (a `grain2` mellett) — token az exe string-táblájában megerősítve, paraméterezése dekódolatlan |
| `radtint` | ismeretlen | feltehetően a `dir_tint` radiális testvére (`rad`- előtag mint `radsat`/`radblur`) — exe-ből azonosított, paraméterezése dekódolatlan |
| `RoundedEdges` | ismeretlen | önálló szűrő-token (a `Border`/`DropShadow` mellett) — exe-ből azonosított, paraméterezése dekódolatlan |
| `Matte` | ismeretlen | önálló szűrő-token (a `MuseumMatte` és `Vignette` között) — exe-ből azonosított, paraméterezése dekódolatlan |
| `NightVision` | ismeretlen | önálló szűrő-token (a `HeatMap`/`Invert` mellett) — exe-ből azonosított, paraméterezése dekódolatlan |
| `picnik=1;` | — | önálló, boolean jellegű filters-lánc-token (`redeye=1;`/`retouch=1;` mintájára) — exe-ből azonosított, jelentése/előfordulása élő ini-ben validálatlan |

Forrás a fenti (`glow` v1, `grain` v1, `radtint`, `RoundedEdges`, `Matte`,
`NightVision`, `picnik=1;`) sorokhoz: **Picasa3.exe string-tábla** — ld.
`docs/specs/picasa-exe-strings.md` (1. pont). Ezek egyike sem szerepelt eddig
a mért/golden-elemzésben (`filters-decoded.md`), ezért státuszuk
undecoded/uncalibrated: valódi ini-export teszttel kell megerősíteni, hogy
ténylegesen `filters=` tokenként fordulnak-e elő.

Szöveg-overlay (külön kulcs): `text=1; 136;11;sample text;Aharoni;...` + `textactive=`.

### Kiegészítések valódi adatból (2026-07-16, Picasa 3.9-es db3, 13 046 szűrőzött kép)

A Buchinger-táblázatban **nem szereplő** szűrők, élesben megfigyelve:

| Szűrő | Példa | Megjegyzés |
|---|---|---|
| `fill` | `fill=1,0.308411` | kitöltőfény önálló szűrőként (nem csak finetune2-ben) |
| `finetune` | `finetune=1,...` | a finetune2 régebbi, v1 változata |
| `unsharp` | `unsharp=1,0.748538` | az unsharp2 v1 változata |
| `Vignette` | `Vignette=1,...` | **nagybetűs** azonosító! — a parser legyen kis-nagybetű-tűrő |

Gyakorisági sorrend a tesztkészletben: enhance (7 528), autolight (4 707),
crop64 (2 961), fill (2 888), finetune2 (812), tilt (759), redeye (488),
finetune (482), unsharp (469), warm (330), sat (266), Vignette (216).

**Spec-javítás:** a `!` (0..1 float) jelölés nem mindig igaz — élesben
**negatív** értékek is előfordulnak: `tilt=1,-0.114659,...` (dőlésszög) és a
`finetune2` utolsó paramétere (`...,-0.578947;`). A parser fogadjon el
tetszőleges előjeles floatot minden pozícióban.

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

## Arc-részletadat (`facerectdata` / `deferredface`) — 2026-08-06

A `Picasa3.exe` string-táblájában megvan a **pontos formátumsztring**, amivel
a Picasa az arcdetektor részletes kimenetét szerializálja:

```
conf(%.3f),pan(%.3f),leye(%.3f,%.3f),reye(%.3f,%.3f),mouth(%.3f,%.3f)
```

| mező | jelentés |
|---|---|
| `conf` | a detektálás megbízhatósága |
| `pan` | fejfordulás (pán-szög) — a profilba fordulás mértéke |
| `leye`, `reye` | a bal és jobb szem koordinátája (x, y) |
| `mouth` | a száj koordinátája (x, y) |

Mind három tizedesjegyre formázott float. Ez a `rect64()` arc-téglalap
**mellé** tárolt, finomabb geometria: ebből származik a Picasa
arc-indexképeinek pontos vágása és forgatása (a szemvonalra igazítás).

**Honnan jön:** a `plugins/Red.dll` a Google által 2006-ban felvásárolt
**Neven Vision** motorja (`CNevenVisionDLL::IFace`, `vbf_Cascade`,
`vde_LocalPoseDetector`, `epi_PoseEst`, `enn_MlpNet`), a tanított modell a
`plugins/red.cfg` (2,28 MB). Ugyanez a DLL végzi a vörösszem-detektálást is.
Ld. `picasa-program-resources.md`, 4. fejezet.

A PicasaPy szempontjából: importnál ezt a mezőt **változatlanul meg kell
őrizni** (round-trip), de saját detektorral nem reprodukálható — a
`conf`/`pan` értékek a Neven-motor sajátjai.

## Színkereső tokenek (`color:…`) — 2026-08-06

Az `.exe` string-táblája egy tömbben tartalmazza a keresés
**szín-tokenjeit**:

```
color:red  color:orange  color:yellow  color:green  color:blue
color:purple  color:pink  color:black  color:white  color:gray
```

Mellettük az `avgcolor` mezőnév áll — vagyis a Picasa **képenként eltárolta
az átlagszínt**, és a keresősávba írt `color:blue` erre szűrt. Ez a
funkció a magyar UI-ban is elérhető volt, de eddig egyik specünkben sem
szerepelt. A PicasaPy indexe ugyanezt olcsón megteheti (átlagszín →
legközelebbi a 10 névből), és ezzel egy elveszettnek hitt Picasa-képesség
tér vissza.

## Írási szabályok (PicasaPy, kétirányú kompatibilitáshoz)

1. Atomikus írás (temp fájl + rename), írás előtti backup.
2. Nem értelmezett kulcsok/szekciók bitre pontos megőrzése.
3. JPEG-nél caption/keywords az IPTC-be, NEM az ini-be (a Picasa is így tesz);
   RAW és egyéb formátumnál az ini-be.
4. `redo=` és `originhash` érintetlenül hagyása, ha a szerkesztési lánc nem változott.
5. Fájl-lock / ütközésdetektálás arra az esetre, ha az eredeti Picasa is fut.

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
| `P2category` | `Downloaded Albums~otheruserid`, `Projects (internal)` | **gyűjtemény-hovatartozás** (nem csak letöltött album!) — a Picasa a kollázs/film kimeneti mappájába is ezt írja `Projects (internal)` értékkel; igazolva valódi `.cxf`-minta mellől (2026-08-07, #436) |
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
| `backuphash` | `36003` | **MEGFEJTVE (#643)**: az ÍRÁS IDŐPONTJÁBÓL képzett 16 bites érték, nem tartalom-hash — ld. lent |
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
| `radtint` | `1,!x,!y,!feather[,!szín]` | radiális **szorzó**-tint (#565): a fókuszpont körül változatlan, kifelé `forrás × szín / 256`, köbös smoothstep maszkkal; a Feather affin leképezése még kalibrálatlan |
| `RoundedEdges` | ismeretlen | önálló szűrő-token (a `Border`/`DropShadow` mellett) — exe-ből azonosított, paraméterezése dekódolatlan |
| `Matte` | ismeretlen | önálló szűrő-token (a `MuseumMatte` és `Vignette` között) — exe-ből azonosított, paraméterezése dekódolatlan |
| `NightVision` | ismeretlen | önálló szűrő-token (a `HeatMap`/`Invert` mellett) — exe-ből azonosított, paraméterezése dekódolatlan |
| `picnik=1;` | — | önálló, boolean jellegű filters-lánc-token (`redeye=1;`/`retouch=1;` mintájára) — exe-ből azonosított, jelentése/előfordulása élő ini-ben validálatlan |

Forrás a fenti (`glow` v1, `grain` v1, `radtint`, `RoundedEdges`, `Matte`,
`NightVision`, `picnik=1;`) sorokhoz: **Picasa3.exe string-tábla** — ld.
`docs/specs/picasa-exe-strings.md` (1. pont). Ezek egyike sem szerepelt eddig
a mért/golden-elemzésben (`filters-decoded.md`), ezért státuszuk
undecoded/uncalibrated: valódi ini-export teszttel kell megerősíteni, hogy
ténylegesen `filters=` tokenként fordulnak-e elő. Kivétel a `radtint`: annak
paraméterezése és csővezetéke a #565-ben a natív kód visszafejtéséből
megvan (ld. `filters-decoded.md`), csak a Feather csúszka affin leképezése
vár még golden-párra.

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

### Megvalósítás (PicasaPy, #383)

**FONTOS DISCLAIMER:** a Picasa PONTOS HSV-küszöbei (hol a határ pl. `blue`
és `purple` között, mikor számít egy kép `pink`-nek a sima `red`/`purple`
helyett) **nem ismertek és nem mérhetők** — a Picasa 2016 óta nem elérhető,
csak a `color:`/`avgcolor` NÉV maradt fenn az `.exe` string-táblájában. Az
alábbi küszöbök a mi józan implementációnk, NEM rekonstruált Picasa-
viselkedés. A pontos konstansok és a levezetés:
`src/picasapy/color/classify.py`.

Menete:
1. RGB → HSV.
2. Alacsony telítettségnél (S < 0,12) akromatikus ág: `black` (V < 0,20),
   `white` (V > 0,85), egyébként `gray`.
3. A bíbor→vörös átmeneti hue-ívben (330°–355°), közepes telítettség
   (0,12 ≤ S < 0,55) ÉS magas világosság (V ≥ 0,55) mellett: `pink`.
4. Egyébként hue-sáv: `red` (345°–360° és 0°–15°), `orange` (15°–45°),
   `yellow` (45°–70°), `green` (70°–170°), `blue` (170°–255°),
   `purple` (255°–345°).

**Tárolás:** az átlagszín (`avgcolor`, 0xRRGGBB) és a hozzá tartozó
`color_token` NEM a `.picasa.ini`-be kerül (a Picasa sem oda írta —
adatbázis-mező volt), hanem a PicasaPy SQLite-indexébe, egy önálló
`photo_colors` táblába (`src/picasapy/index/colors.py`), a fájl
AZONOSSÁGA szerint kulcsolva (útvonal, mtime_ns, méret) — ugyanaz a minta,
mint a dedup-kereső `photo_hashes` gyorsítótáráé (#294). A tábla **lustán**
jön létre (`CREATE TABLE IF NOT EXISTS`), NEM a `schema.py`
sémaverziózásán át — a `schema.py` forró fájl, sémaverziót csak az
integrátor oszt ki. Ha ez a tábla egy következő verzióban átköltözik a
`schema.py`-ba (pl. hogy `photo_id`-alapú JOIN legyen belőle), az itt
leírt viselkedés (útvonal-kulcs, upsert, lusta létrehozás) megmarad, csak
a DDL helye változik.

**Feltöltés:** a `backfill_colors(conn, limit)` kötegenként (alapból 200
kép) tölti fel a még hiányzó bejegyzéseket — a kis (bélyegkép-méretű,
redukált JPEG-dekódolású) beolvasásból számol átlagszínt, nem a teljes
felbontásból. Ismételt hívásra 0-t ad vissza, ha nincs több teendő — így
háttérszálon, kis kötegekben, az indulást nem blokkolva futtatható
(az induláskori bekötés — pl. `prune_in_background` mintájára — az
integrátor feladata, ld. a #383 jegy jelentését).

**Keresés:** a `color:kék`/`szín:kék` token (mindkét nyelv egyenértékű,
`src/picasapy/index/search_color.py`) a szabadszavas kereséstől
elválasztva kerül feldolgozásra, ÉS kapcsolatban a maradék szöveges
kereséssel; több színtoken egymással VAGY kapcsolatban (egy képnek csak
egy átlagszíne van). Ha egy képre még nincs kiszámolt `color_token` (a
háttér-feltöltés még nem érte el), a kép egyszerűen kimarad a
találatokból — nem hibát dob.

## Egy kövület: a `[LifeScape]` szekció — a formátum ŐSE (2026-08-07)

A telepítés `web/templates/blackfrm/` mappájában ott hever egy **véletlenül
kiszállított** fájl, `xLifescape.ini` néven — a másik hat sablonmappában nincs
párja:

```ini
[LifeScape]
name=blackbg
description=
date=37429.106389
category=Other Pictures
```

Ez **album-metaadat a fejlesztők saját Picasájából**, ami bennmaradt a csomagban.
A `date` **OLE Automation-dátum** (napok 1899-12-30 óta): **37429,106389 →
2002. június 22., 02:33** — vagyis a **LifeScape-korszakból**, jóval a Google
2004-es felvásárlása előttről. (A „Lifescape Solutions Inc." nevet a
registry-kulcsokban is megtaláltuk: `Software\Lifescape Solutions Inc.\Picasa`.)

**Amit a formátum fejlődéséről elárul:**

| akkor (2002, `[LifeScape]`) | ma (`[Picasa]`) |
|---|---|
| `name` | `name` — **változatlan** |
| `description` | a `[.album:]` szekcióba került |
| `date` — **OLE-dátum** (lebegőpontos napszám) | ISO 8601 a `[.album:]`-ban |
| `category` = „Other Pictures" | `category` = „Folders on Disk" stb. |

A **`category`** mező tehát **több mint húsz éve** ugyanazt a szerepet tölti be:
a mappa/album gyűjteménybe sorolását. A mai `P2category` ennek a leszármazottja.
Az „Other Pictures" pedig ott van a mai beépített gyűjtemény-nevek listáján is —
**„Other Stuff"** néven.

**Gyakorlati haszon:** nagyon régi Picasa-könyvtárban előfordulhatnak
`[LifeScape]` szekciójú ini-fájlok. A parszernek ezt **nem kell értenie**, de a
round-trip elv szerint **változatlanul meg kell őriznie** — importnál pedig a
`name`/`category` kiolvasható belőle.

### A `backuphash` — MEGFEJTVE (#643, 2026-08-14)

Eddig „dekódolatlan, változatlanul visszaírandó" volt. A visszafejtés
(`0x00454770` → `0x0098b6e0` → `0x0098b550`) megmutatta, hogy **nem a fájl
tartalmának hash-e**, hanem az **írás időpontjából** képzett érték:

```c
double d = OLE_DATE(most);          // az aktuális helyi idő OLE Automation DATE-ként
uint16_t w[4];  memcpy(w, &d, 8);   // a double négy 16 bites szava
backuphash = w[0] ^ w[1] ^ w[2] ^ w[3];
sprintf(buf, "%d", backuphash);
```

Az OLE-dátum a szokásos képlettel készül, `693703` (`0xa96c7`) alapnappal —
azaz az **1899-12-30 = 0.0** referenciával. Ezt ellenőriztük: a kinyert képlet
erre a dátumra pontosan `0.0`-t ad.

**Miért nem sikerült eddig dekódolni:** mert nincs mit dekódolni a *tartalomból*.
Ugyanaz a fájl két különböző időpontban írva más `backuphash`-t kap.

**Következmények:**

- Az érték **előállítható** — a PicasaPy is tud érvényeset írni.
- Az értéktartomány 0…65535, ami egyezik a megfigyelt `23764` / `36003`
  mintákkal (szimulációval 2015–2026 közötti időpontokra 16 298…62 695).
- **Nem ez okozza a #643-as beolvasási hibát** — a Picasa a szakaszunkat
  akkor sem olvasná be, ha volna benne `backuphash`.

## ⚠️ A beolvasás életciklusa — mikor BEMENET és mikor KIMENET (#643, 2026-08-14)

Ez a szakasz azért van itt, mert a hiánya engedte, hogy a #643-as hiba idáig
jusson: a spec eddig **egy szót sem szólt arról, mikor olvassa be a futó
Picasa a `.picasa.ini`-t.** A formátum ismerete önmagában nem elég — a
round-trip ígérete ezen a ponton dől el.

A megállapítások a `Picasa3.exe` visszafejtéséből származnak (a nyers
dekompilátum és a címek a privát kutatási repóban).

### ⚠️ A Picasa IGENIS figyeli a mappát — helyesbítés (2026-08-15)

Korábban itt az állt, hogy „a `.picasa.ini` nem figyelt fájl". **Ez téves
volt.** A visszafejtés megmutatta, hogy a Picasa `FindFirstChangeNotificationW`
hívással figyeli a mappákat, és a szűrő:

```
push 0x17        ; dwNotifyFilter
push 1           ; bWatchSubtree = TRUE  (REKURZÍV)
push eax         ; az útvonal
call [0x00d694fc]
```

`0x17` = `FILE_NAME | DIR_NAME | ATTRIBUTES | **LAST_WRITE**`.

**A `LAST_WRITE` bit benne van**, és a figyelés rekurzív. Vagyis egy
`.picasa.ini` tartalmi módosítása **kivált operációs rendszer szintű
értesítést** a Picasa felé.

> **Hogyan került elő:** a hívó sokáig nem volt azonosítható, mert a
> `FindFirstChangeNotificationW` burkolóját (`0x009b3000`) egy **futásidőben
> feltöltött függvénymutató-globálon** (`0x00d694fc`) át hívják — a globált
> egy inicializáló csonk tölti fel (`0xc32faa`:
> `mov dword [0x00d694fc], 0x009b3000`). A kereszthivatkozási tábla ezért
> üres volt. A globált olvasó valódi használó: **`0x007061c0`**.

### De az értesítés önmagában nem elég

Az értesítés megérkezik, a `filters=`-ünk mégsem jelenik meg. A rés tehát
**az értesítés után** van: a mappa újrapásztázása **fotónként** dolgozik, és
az egyes fotók újrafeldolgozása a **képfájlhoz** kötött (ld. lent a
betöltő-ágat). A `.picasa.ini` megváltozása értesítést ad, de nem tesz egy
már indexelt fotót „elavulttá".

**Ebből egy megkerülési út is következik, amit érdemes kipróbálni:** ha a
külső író a **képfájl** módosítási idejét is megérinti, a fotó bekerülhet az
újrafeldolgozandók közé — és akkor az ini-t is beolvassa. Ez egy mérhető
kísérlet, nem elmélet.

### Az ini → rekord olvasót csak SZERKESZTÉS/MENTÉS hívja

Az ini-szakaszt rekordba olvasó rutin (`0x00463270`) mind a **48 kulcsot**
beolvassa — a `filters`-t is —, de **pontosan egy hívója van**: az ini ↔
adatbázis szinkron (`0x00467ca0`). Annak a hat hívója pedig kivétel nélkül
szerkesztő/mentő útvonal: retusálás, a szerkesztőpanel alkalmaz/mégse gombja,
filmmentés, a fájlmentő szál. **Mappapásztázó vagy fájlfigyelő hívó nincs
köztük.**

### A kulcsok KÉT csoportra válnak, külön életciklussal

Az ini-feldolgozó (`0x00456610`) egy jelzőbites kapcsolón dönt, és a szakasz
kulcsait két, egymástól független csoportként kezeli:

| bit | csoport | kulcsok |
|---|---|---|
| `flags & 2` | **szerkesztések** | `filters` · `crop` · `rotate` · `bw` · `fix` · `text` · `textactive` · `backuphash` |
| `flags & 1` | **metaadatok** | `rating` · `star` · `caption` · `keywords` · `faces` · `geotag` · `albumlist` · `hidden` · `screensaver` · `suppress` · `onlinechecksum` |

### A betöltő ágon a metaadat-fázis a KÉPFÁJLHOZ van kötve

A fotó-betöltő képenként előbb a **szerkesztés-csoportot** alkalmazza
(`flags = 2`, **feltétel nélkül**), majd feldolgozza a **képfájlt** (EXIF,
bélyegkép, átlagszín), és a **metaadat-csoportot** (`flags = 1`) csak akkor,
ha ez a lépés változást jelez.

> ⚠️ Ebből következik, hogy **ha a Picasa egyáltalán betölti a képet, a
> `filters=`-t beolvassa.** A #643-as hiba oka tehát **nem** tartalmi
> feltétel, hanem az, hogy a betöltő egy **már indexelt** fotóra nem fut le
> újra — az újraindítás sem futtatja végig, mert az adatbázis-gyorsítótárból
> dolgozik. (Hogy mi kényszerítene újraindexelést, az még nyitott.)

### Mit jelent ez a gyakorlatban

| irány | működik? | miért |
|---|---|---|
| Picasa **ír** → külső olvasó | ✅ | az ini a Picasa kimenete, mindig naprakész |
| külső **ír** → futó Picasa **olvassa** | ❌ | nincs olyan hívási út, ami a képfájl érintése nélkül kiváltaná |
| külső ír → Picasa **legközelebbi saját írása** | ⚠️ **adatvesztés** | a szinkron a saját adatbázis-rekordjából írja ki a szakaszt egészben, így a külső kulcsokat felülírja |

> **A round-trip ígéretét ehhez kell igazítani.** A `.picasa.ini` a futó
> Picasa felé **kimenet**, nem bemenet; bemenetté csak az első indexeléskor,
> illetve a képfájl megváltozásakor válik. Egy külső szerkesztő szerkesztései
> **némán elveszhetnek**, ha közben fut a Picasa és hozzáír ugyanahhoz a
> képhez.

**Ami még nyitott:** melyik betöltési fázis viszi konkrétan a `filters`
kulcsot, és mi pontosan a „változás" feltétele a képfájl-feldolgozásban. Ez a
#643 kutatási ága.

## ⚠️ A `filters=` lánc beolvasása SZIGORÚ — mérve (2026-08-15, #685)

Két valódi Picasa-export (178 + 49 kép, 3.9.141.259) tételesen kimérte, hogy
az eredeti **jóval szigorúbb**, mint a mi parszerünk. Minden alábbi esetben a
Picasa **némán elejti a bejegyzést** — nem hibázik, nem jelez, csak a
szerkesztés nem történik meg. Ez a legveszélyesebb hibaosztály: íráskor
elveszíthetjük a felhasználó munkáját anélkül, hogy bármi jelezné.

### 1. A szűrőnév kis-nagybetű-ÉRZÉKENY

| lánc | hatás |
|---|---|
| `tint=1,79.842102,ffff;` | **lefut** (ΔE 37,6) |
| `Tint=…` / `TINT=…` / `tInT=…` | **néma elejtés** (ΔE 0,18 = JPEG-zaj) |
| `Vignette=1,35,1.4,0,00000000;` | **lefut** (ΔE 12,1) |
| `vignette=…` / `VIGNETTE=…` | **néma elejtés** |
| `sepia=1;` | **lefut** (ΔE 21,3) |
| `Sepia=1;` | **néma elejtés** |

Tehát nincs „natív kisbetűs / Glimmer nagybetűs" szabály sem: **minden szűrő
pontosan a saját, regiszterbeli írásmódját várja**, bájtra. A kanonikus alakok
forrása a [`filterdesc-registry.md`](filterdesc-registry.md) táblája.

> **A mi parszerünk `casefold()`-dal illeszt** (`src/picasapy/ini/filters.py`,
> `FilterOp.matches`). Olvasáskor ez megengedő — elfogadunk olyat, amit az
> eredeti nem —, íráskor viszont **kötelező az eredeti alak megőrzése**.

### 2. A felesleges paraméter is néma elejtést okoz

| lánc | hatás |
|---|---|
| `grain2=1;` | **lefut** (ΔE 1,8) |
| `grain2=1,0.500000;` | **néma elejtés** (ΔE 0,18) |
| `grain=1,;` (üresen záró vessző) | **lefut** — ez tolerált |

A `grain2` nem vár paramétert; egy fölösleges szám megöli a bejegyzést. A
záró üres mező viszont nem zavarja. Vagyis a szigorúság a **paraméterek
számára** vonatkozik, nem a szintaxis apró szennyeződéseire.

### 3. A hex színmező: legfeljebb 8 jegy, elölről, vezető nullák nélkül is jó

| lánc vége | eredmény |
|---|---|
| `ffff` | ΔE 37,601 |
| `0000ffff` | ΔE 37,601 — **azonos** |
| `00ffff` | ΔE 37,601 — **azonos** |
| `000000ffff` (10 jegy) | ΔE 106,728 — **azonos a `0000ff`-fel** |
| `ff0000` | ΔE 80,291 |
| `00ff00` | ΔE 91,779 |
| `0000ff` | ΔE 106,728 |

Az első három egyezése bizonyítja, hogy a **vezető nullák elhagyhatók** — a
rejtélyes négyjegyű `ffff` tehát egyszerűen `0x0000ffff`, nem külön kódolás
(#679). A tízjegyű eset pedig azt mutatja, hogy a beolvasó **az első 8 jegyet
veszi** (`000000ffff` → `000000ff` = kék), nem a végét és nem az egészet.

A kontrollok (`ff0000`, `00ff00`, `0000ff`) külön ΔE-t adnak, tehát a mező
tényleg csatornánként számít; a bájtsorrend a natív kódból **`0x00RRGGBB`**
([`filters-decoded.md`](filters-decoded.md), `tint` szakasz).

**Bizonyítottsági fok: mind a három megerősített** — valódi Picasa-export,
csoportonként egyetlen mozgatott változóval.

## Írási szabályok (PicasaPy, kétirányú kompatibilitáshoz)

1. Atomikus írás (temp fájl + rename), írás előtti backup.
2. Nem értelmezett kulcsok/szekciók bitre pontos megőrzése.
3. JPEG-nél caption/keywords az IPTC-be, NEM az ini-be (a Picasa is így tesz);
   RAW és egyéb formátumnál az ini-be.
4. `redo=` és `originhash` érintetlenül hagyása, ha a szerkesztési lánc nem változott.
5. Fájl-lock / ütközésdetektálás arra az esetre, ha az eredeti Picasa is fut.

## A `filters=` név-feloldás a natív kódban — a mérés kódbeli megerősítése (#643, 2026-08-15)

A [mért szigorúságot](#-a-filters-lánc-beolvasása-szigorú--mérve-2026-08-15-685)
a bináris is alátámasztja, két független helyen.

### A szűrő-nyilvántartás táblája

A 42 bejegyzésű regiszter a `.data`-ban, **16 bájtos rekordokban**:

```
0x00cd0720 …            [ segéd-callback | 2. segéd | név-mutató | fő callback ]
```

A nevek a rekordokból kiolvasva pontosan a
[`picasa-native-filter-registry.md`](picasa-native-filter-registry.md)
sorrendjében állnak (`triple`, `triple2`, … `sepia`, … `shadow`). A `.text`
**nem a tábla kezdetére** hivatkozik, hanem a két szélére (`0x00cd0644`,
`0x00cd0968`) — a bejárás láncolt, nem indexelt.

### A névkeresés bájtonként hasonlít — nincs kisbetűsítés

`FUN_008f9fe0` (`0x008f9fe0`) a konténer virtuális keresőjét hívja a névvel,
majd a nem-talált ágon két beégetett nevet próbál. Minden összehasonlítás
**nyers bájt-egyenlőség**:

```c
bVar15 = *pcVar9 == *pcVar4;      // se tolower, se _stricmp
```

Ugyanez a minta a lánc **írójában** (`FUN_008fac40`, `0x008fac40`) is, ahol a
`crop64` és a `rot` ágat választja ki. Vagyis a kis-nagybetű-érzékenység nem
egyetlen hely sajátja, hanem a formátum kezelésének módja.

**Ez a mért eredmény független megerősítése**: a `Tint=` / `vignette=` /
`Sepia=` azért veszett el némán, mert a keresés bájtra hasonlít.
*Bizonyítottsági fok: megerősített (mérés + kód).*

### Nem talált név → `-1`, két beégetett alias után

A nem-talált ág visszatérése `-1`, előtte azonban két név külön kezelést kap:
**`crop`** (a `crop64` felé irányítva) és **`desat`**. A `desat` a binárisban
**pontosan egyszer** fordul elő, épp itt — a nyilvántartásban nincs benne, és
a PicasaPy sem ismeri.
*Bizonyítottsági fok: erős* (a karakterlánc és a hely egyértelmű; hogy
pontosan mire képezi le, még nem visszakövetett).

### ⚠️ MEGFEJTVE: egy hibás bejegyzés MEGSZAKÍTJA a lánc hátralévő részét

A bejáró (`FUN_00907740`, `0x00907740`) így fut:

```c
do {
    ... a kovetkezo ';'-ig tarto darab kivagasa (FUN_009863f0(0x3b)) ...
    local_4 = FUN_00908360(&local_8);      // EGY bejegyzes feldolgozasa
    if (local_4 != 0) goto LAB_00907995;   // <-- HIBA: AZONNALI KILEPES
    ... a kesz szuro-objektum hozzafuzese a listahoz ...
} while (true);

LAB_009079_95:  return local_4;            // a lanc TOBBI resze sosem fut le
```

Az egy-bejegyzés feldolgozó (`FUN_00908360`, `0x00908360`) **nem nullát** ad:

* ha a darabban **nincs `=`** → `return -1`;
* ha a globális gyár (`DAT_00d67f68`, virtuális 1. rekesz) nem tudja
  előállítani a szűrőt — **ide fut be az ismeretlen név**, mert a
  `FUN_008f9fe0` névkeresés nem-talált ága `-1`-et ad —, akkor az objektumot
  eldobja és a hibakódot adja vissza.

**Következmény, betűre:**

> Egy fel nem ismert nevű vagy hibás bejegyzés **nem csak önmagát viszi**: a
> lánc **utána következő** szűrői sem futnak le. Az **előtte** lévők
> megmaradnak, mert azok már a listába kerültek.

Ez pontosan a #643 3. hipotézise, és **egybevág a méréssel**: a
`grain2=1,0.5;` (fölösleges paraméter) és a `Tint=…` (rossz írásmód) egyaránt
hatástalan maradt — egyelemű láncban a megszakadás és az „elejtés"
megkülönböztethetetlen.

*Bizonyítottsági fok: megerősített* (a ciklus, a hibaág és a `-1` visszatérés
is visszakövetve; a mérés független megerősítés).

### ⚠️ Amit ez az ÍRÁS oldalán jelent — kritikus

Ha a PicasaPy egyetlen bejegyzést rosszul ír ki (rossz írásmód, rossz
paraméterszám, hiányzó `=`), akkor az eredeti Picasában **nem az az egy effekt
vész el, hanem az összes utána következő is** — némán. A felhasználó
szerkesztésének a fele tűnik el, hibaüzenet nélkül. Ld. #695.

### A maradék bizonytalanság (mérésre)

**Egy fel nem ismert bejegyzés csak önmagát viszi, vagy a lánc hátralévő
részét is?** Ez a #643 3. hipotézise, és ez dönti el, hogy egy hibás sor
egyetlen effektet ront-e el vagy az egész szerkesztést.

A hívó (`0x0050e460`, 144 bájt) a `-1`-et kapja, őt viszont **függvénymutató-
táblán át** hívják (`.rdata` `0x00c7f728`), így a lánc statikus visszakövetése
innen aránytalanul drága lenne.

**Olcsóbb és biztosabb út: mérés.** Négy kép a következő export-körben:

| kép | lánc | mit dönt el |
|---|---|---|
| A | `sepia=1;bw=1;` | a kétlépéses lánc alapesete |
| B | `nincsilyen=1;bw=1;` | ismeretlen ELSŐ tag — a `bw` átjön-e |
| C | `sepia=1;nincsilyen=1;` | ismeretlen UTOLSÓ tag |
| D | `grain2=1,0.5;bw=1;` | rossz paraméterszám — ugyanaz-e a viselkedés |

Ha B-ben és C-ben is látszik a `bw`, a hibás bejegyzés **csak önmagát viszi**;
ha B-ben nem, a lánc **megszakad** — és akkor a #643 fő gyanúja igazolódik.

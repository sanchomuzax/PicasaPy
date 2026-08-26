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
| `glow` (v1) | **azonos a `glow2`-vel** | ragyogás v1 — a natív szűrő-tábla szerint (`0x00cd07d8`) **ugyanaz a kezelő** (`0x008f8f70`), mint a `glow2`-é; lásd `picasa-native-filter-registry.md` |
| `grain` (v1) | **azonos a `grain2`-vel** | filmszemcse v1 — a natív szűrő-tábla szerint (`0x00cd0868`) **ugyanaz a kezelő** (`0x008f88e0`), mint a `grain2`-é; lásd `picasa-native-filter-registry.md` |
| `radtint` | `1,!x,!y,!feather[,!szín]` | radiális **szorzó**-tint (#565): a fókuszpont körül változatlan, kifelé `forrás × szín / 256`, köbös smoothstep maszkkal; a Feather affin leképezése még kalibrálatlan |
| `RoundedEdges` | **a `Border` csempe 2. üzemmódja** | nem önálló szűrő: az effekt-csempe tábla (`0x00c7e720`) szerint a Szegély csempe második tokenje (sarok-lekerekítés); lásd `ui-audit-editor.md` |
| `Matte` | **a `Vignette` csempe 2. üzemmódja** | nem önálló szűrő: az effekt-csempe tábla (`0x00c7e6d8`) szerint a Vignetta csempe második tokenje; lásd `ui-audit-editor.md` |
| `NightVision` | **a `HeatMap` csempe 2. üzemmódja** | nem önálló szűrő: az effekt-csempe tábla (`0x00c7e690`) szerint a Hőtérkép csempe második tokenje; lásd `ui-audit-editor.md` |
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

Szöveg-overlay (külön kulcs): `text=` + `textactive=`. A régi, rövidített
példa (`text=1; 136;11;sample text;Aharoni;...`) **nem teljes sor** — a
formátum hossz-előtagos és többblokkos, ld. „A `text=` sor formátuma"
szakaszt lent. (A rövidítés első négy mezője utólag igazolódott: a `11`
tényleg a `sample text` bájthossza.)

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

~~Nyitott kérdés: `finetune2` utolsó paramétere azonosítatlan~~ →
**AZONOSÍTVA (2026-08-16), ld. lent.** Az `enhance`/`autolight`/`autocolor`
algoritmusa azóta szintén visszafejtve
([`filters-decoded.md`](filters-decoded.md)).

### A `finetune2` paraméter-sora — mind az öt rekesz azonosítva

A `filterdesc.xml` a szűrő négy csúszkáját és egy színkorongját adja meg;
az ini-sorrend a 4.1 szabály szerint (*numerikusok max 3 → színek → maradék
numerikus*) ebből egyértelműen levezethető:

```
finetune2=1, fill, highlights, shadows, SZÍN(8 hex), színhőmérséklet
```

| rekesz | vezérlő | `filterdesc` | tartomány |
|---:|---|---|---|
| 1 | `Fill Light` | `range 1.0` | `0 … 1` |
| 2 | `Highlights` | `range 0.48` | `0 … 0,48` |
| 3 | `Shadows` | `range 0.48` | `0 … 0,48` |
| 4 | `colorcircle id="0"` | — | `00RRGGBB` (semleges-pipetta) |
| **5** | **`Color Temperature`** | **`range 2.0`, `offset 1.0`** | **`−1 … +1`** |

**Az „azonosítatlan, néha negatív" utolsó paraméter tehát a
színhőmérséklet** — a negatív értékek a hidegebb oldal.

#### Ellenőrzés a valós korpuszon (566 `finetune2` bejegyzés)

| rekesz | mért minimum | mért maximum | medián | negatív |
|---|---:|---:|---:|---:|
| fill | +0,0000 | +0,4444 | 0 | 0 |
| highlights | +0,0000 | **+0,2218** | 0 | 0 |
| shadows | +0,0000 | **+0,3284** | 0 | 0 |
| **színhőmérséklet** | **−0,5789** | **+1,0000** | 0 | **13** |

A mért szélsőértékek **mind beleférnek** a `filterdesc` tartományaiba, és az
5. rekesz az egyetlen, ami **negatívba megy** — pontosan az `offset 1.0`-s,
`−1 … +1`-es tengely szerint.

A 4. rekesz mért értékei a szürke `0x808080` körül szórnak
(`00808080`, `007c8080`, `00848071`, `0084806e`, `00808071` …), ami
megerősíti a **`0x00RRGGBB`** bájtsorrendet is: a `007c8080` kékesebb,
a `00848071` melegebb semlegespont.

*Bizonyítottsági fok: megerősített* (a `filterdesc.xml` deklarációja + 566
valós bejegyzés).

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

Mellettük az `avgcolor` mezőnév áll. Ez a funkció a magyar UI-ban is
elérhető volt, de eddig egyik specünkben sem szerepelt.

### Megvalósítás (PicasaPy, #383, #1480)

> ⚠️ **JAVÍTVA (#1480, 2026-08-26).** Ez a szakasz korábban azt állította,
> hogy a Picasa az **átlagszínt** (`avgcolor`) sorolta be, és hogy a pontos
> küszöbök „nem ismertek és **nem mérhetők**". **Mindkettő téves volt.**
> Az osztályozó egyetlen 752 bájtos függvényben áll a binárisban
> (`0x009dbd10`), és ki lett mérve: a Picasa a kép EGÉSZ raszteréről épít
> **telítettséggel súlyozott hue-hisztogramot**, hét vödörrel, és a
> **legnagyobb vödör nyer**. Az `avgcolor` a keresésnek NEM bemenete —
> ugyanabban a kezelőfüggvényben készül, de külön ágon (`0x004280d8`).
> A teljes bizonyítéklánc: [`picasa-szinkereses.md`](picasa-szinkereses.md).

Menete (mért), képpontonként, végig egész aritmetikával:
1. `MAX = max(R,G,B)`, `Δ = MAX − MIN`; ha `MAX == 0`, a képpont kimarad.
2. `S = Δ·255/MAX`; ha `S <= 50` (≈19,6 %), a képpont kimarad.
3. `H` a szabványos HSV-képlettel, de **1530 egységes** körön, majd
   hatoddal skálázva (`H = H1530/6`, 0…254).
4. `vödör[H/10] += S` — a súly a **telítettség**, nem 1. A hét vödör:
   piros (`H/10` = 0 és 24), narancs (1–3), sárga (4), zöld (5–11),
   kék (12–17), lila (18–21), rózsaszín (22–23). A `H/10 == 25`
   (kb. 353,0–358,8°) egyetlen vödörbe sem kerül — ez az eredeti mért
   **rése**, és reprodukáljuk.
5. A legnagyobb vödör nyer, döntetlennél a magasabb indexű. Ha egyetlen
   vödör sem kapott súlyt, az eredmény a névtábla `−1` ága, ami EGYSZERRE
   három tokent ad: `black`, `white`, `gray` — a fekete/fehér/szürke
   között az eredeti nem tesz különbséget.

**Tárolás:** a kép színtokenjei (`color_tokens`, szóközzel elválasztva) és
az `avgcolor` (0xAARRGGBB, önálló kép-metaadat) NEM a `.picasa.ini`-be kerül (a Picasa sem oda írta —
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
redukált JPEG-dekódolású) beolvasásból dolgozik, nem a teljes
felbontásból. Mért költség (Raspberry Pi 5, 120 kép, helyi lemez):
~68 ms/kép beolvasás+dekódolás, amihez a hisztogram ~21 ms-ot tesz hozzá
egy ~0,2 Mpx-es raszteren; a besorolás tehát nem okoz TOVÁBBI lemez- vagy
hálózati forgalmat, csak processzoridőt. Ismételt hívásra 0-t ad vissza, ha nincs több teendő — így
háttérszálon, kis kötegekben, az indulást nem blokkolva futtatható.

A dekódolhatatlan fájl (törött JPEG, kiterjesztés szerint fényképnek
látszó nem-kép) is KAP bejegyzést, üres tokenlistával — enélkül minden
körben újra jelöltként jött vissza, és a „hívd, amíg 0-t nem ad" hajtó
ciklus soha nem ért volna véget (#1500). A jelölt-lista az útvonal MELLETT
az mtime/méret szerint is szűr, tehát az átszerkesztett kép színe
újraszámolódik.

**A hívó (#1500):** `app/color_index_controller.py` (`ColorIndexMixin`) —
LUSTÁN, az első `color:`/`szín:` keresés pillanatában indul, nem
indításkor: 81 ms/kép mellett egy 50 000 képes gyűjtemény átnézése több
mint egy óra processzoridő, amit nem szabad ráterhelni arra, aki soha nem
használ színkeresést. A háttérszál a `BackgroundWorkerMixin`-en át megy
(#430/#438), megszakítható, és haladást jelez. Hiányos gyorsítótárral
futó színkeresésnél a felület tájékoztató (nem hiba-) sávot mutat: a „0
találat" és a „még nem számoltuk ki" NEM ugyanaz.

**Keresés:** a `color:kék`/`szín:kék` token (mindkét nyelv egyenértékű,
`src/picasapy/index/search_color.py`) a szabadszavas kereséstől
elválasztva kerül feldolgozásra, ÉS kapcsolatban a maradék szöveges
kereséssel; több színtoken egymással VAGY kapcsolatban (egy képnek egy
hue-vödre van; az akromatikus kép viszont mindhárom akromatikus tokenre
illeszkedik). Ha egy képre még nincs kiszámolt színtoken (a
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

### A PicasaPy megvalósítja, de ALAPÉRTELMEZÉSBEN KIKAPCSOLVA (#643 → #1320)

> ⚠️ **Ezt a szakaszt a lap végi „MEGFEJTVE" szakasz felülírja.** Az
> újraolvasás kulcsa a `.picasa.ini` SAJÁT írási ideje
> (`albumdata_inisync`, 99,5%-os mért egyezés), nem a képfájlé. A lenti
> megkerülési út ezért **feltételezett**, és a #1320 óta **opt-in**:
> `PICASAPY_TOUCH_PHOTO_MTIME=1`. Alapértelmezésben a képfájlokhoz hozzá
> sem nyúlunk.

Az `update_document` (`src/picasapy/ini/io.py`) — ha a kapcsoló be van
kapcsolva — a sikeres ini-mentés után megérinti azoknak a fotóknak a
**módosítási idejét**, amelyeknek a szakasza ténylegesen változott. A logika
egy helyen él (`src/picasapy/ini/photo_touch.py`), és mivel az
`update_document` a projekt EGYETLEN ini-írási kapuja, minden író
(szerkesztő, csillag, felirat, arcok, kulcsszavak, csoportos effekt, mentés)
egyformán viselkedik.

| kérdés | válasz |
|---|---|
| mit módosít | **kizárólag az időbélyeget** (`os.utime`) — a fájlt meg sem nyitja, a bájtjai, mérete és jogosultságai érintetlenek |
| az `atime` | megőrizve: előbb `os.stat`, majd a régi `atime` visszaírása az új `mtime` mellé |
| mikor fut | csak SIKERES ini-mentés után, és csak a ténylegesen változott **fotó**-szakaszokra (`[Picasa]`, `[Contacts2]`, `[.album:…]` kimarad) |
| melyik fájlra | az ini MELLETTI, azonos nevű, LÉTEZŐ fájlra; hiányzó képet, alkönyvtárat, `..`-t kihagy |
| milyen érték | „most"; ha a képfájl mtime-ja a jövőben van (NAS-óraeltérés), akkor a jelenleginél 1 másodperccel későbbre — hogy biztosan újabbnak látsszon |
| hibatűrés | az `utime` bukása (írásvédett kép, hálózati megosztás) **naplózott figyelmeztetés**, a mentés érvényes marad |
| bekapcsolás | `PICASAPY_TOUCH_PHOTO_MTIME=1` (`true`/`yes`/`on`/`igen`/`be` is jó). **Hiányában KI** (#1320). Bármi más érték is KI — elgépelésre a biztonságos irányba dőlünk. Környezeti változó, mert az `ini` réteg szándékosan Qt-mentes, és ez kísérleti kapcsoló, nem felhasználói beállítás. |
| láthatóság | bekapcsolt állapotban a modul `INFO` szinten naplózza, hány képfájl időbélyegét írta át és melyik mappában (#1320) |

> ⚠️ **Amit ez NEM állít.** Hogy a valódi, windowsos Picasa emiatt tényleg
> újraindexeli-e a fotót, **Linuxon nem mérhető** — a fejlesztői gépen nincs
> Picasa. A megvalósítás a saját oldalát garantálja (az érintés megtörténik,
> a tartalom nem változik, ez tesztelt:
> `tests/ini/test_photo_touch_643.py`); a Picasa-oldali hatás megerősítése a
> felhasználó párhuzamos windowsos próbájára vár. Amíg az nincs meg, a
> „valós idejű kétirányú átjárás futó Picasával" továbbra sem ígérhető.

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
> dolgozik. (Hogy mi kényszerítene újraindexelést, arra a **képfájl
> mtime-jának megérintése** az egyetlen ismert jelölt — fent; a hatása
> Picasa-oldalon még nincs megmérve.)

### Mit jelent ez a gyakorlatban

| irány | működik? | miért |
|---|---|---|
| Picasa **ír** → külső olvasó | ✅ | az ini a Picasa kimenete, mindig naprakész |
| külső **ír** → futó Picasa **olvassa** | ❌ | nincs olyan hívási út, ami a képfájl érintése nélkül kiváltaná |
| külső ír **+ a képfájl mtime-ját is megérinti** | ⚠️ **kétséges** — ld. lent | ez a levezetett megkerülési út (fent); a PicasaPy már így ír, de **2026-08-24-én két mérés szólt ellene** — ld. „Az mtime-megkerülés mérlege" |
| külső ír → Picasa **legközelebbi saját írása** | ⚠️ **adatvesztés** | a szinkron a saját adatbázis-rekordjából írja ki a szakaszt egészben, így a külső kulcsokat felülírja |

> ⚠️ **A harmadik sor a legfontosabb, és két egyváltozós próba erősítette
> meg.** (1) A Picasa **teljes újraindítása után sem** jelent meg a
> PicasaPy-ban felvitt effekt — tehát nem arról van szó, hogy „nem veszi
> észre a fájlváltozást". (2) Amikor a Picasa **maga írt** a képhez, a mi
> effektünk eltűnt a PicasaPy-ból is — vagyis a szakaszt EGÉSZBEN írja ki a
> `db3`-ból, nem kulcsonként fésüli össze. Ebből az is következik, hogy a
> `backuphash` hiánya **tünet, nem ok**: a Picasa a saját írásakor adott is
> `backuphash`-t, a mi láncunk mégis törlődött.
>
> A mtime-érintés tehát a **beolvastatásra** ad esélyt, a **felülírás elleni
> védelmet** nem oldja meg — az továbbra is a #644-es szerkesztés-napló
> hatásköre.

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

> **Bekötve: #1142.** A nyolcnál hosszabb hexmező korábban kivételt dobott
> nálunk, amitől a lánc EGÉSZ tagja elesett — a `tint=1,79.842102,000000ffff;`
> az eredetiben lefutott (103,54), nálunk nem (0,00). A
> `render/tinting.py::parse_rgb_hex` azóta az első 8 jegyet veszi; ez a
> KÖZÖS hexolvasó, tehát a `tint`, az `ansel`, a `dir_tint`, a `radtint` és
> a Glimmer-effektek színmezőire egyaránt érvényes.

## Írási szabályok (PicasaPy, kétirányú kompatibilitáshoz)

1. Atomikus írás (temp fájl + rename), írás előtti backup.
2. Nem értelmezett kulcsok/szekciók bitre pontos megőrzése.
3. JPEG-nél caption/keywords az IPTC-be, NEM az ini-be (a Picasa is így tesz);
   RAW és egyéb formátumnál az ini-be.
4. `redo=` és `originhash` érintetlenül hagyása, ha a szerkesztési lánc nem változott.
5. Fájl-lock / ütközésdetektálás arra az esetre, ha az eredeti Picasa is fut.
6. **A `filters=` lánc szűrőneve kizárólag a KANONIKUS alakban mehet ki**
   (#695) — soha nem a belső kulcsunk kisbetűs formájában. A kanonikus
   alakok forrása a [`filterdesc-registry.md`](filterdesc-registry.md) 2.
   szakaszának 84 bejegyzése; a kódban ez a
   `src/picasapy/ini/filter_registry.py` `CANONICAL_FILTER_NAMES` listája.
   Amit a regiszter nem ismer (idegen/jövőbeli szűrő), az **változatlanul**
   megy vissza.
7. **A paraméterszám felső korlátja íráskor kikényszerített** (#695): a
   fölös paraméter [mérten](#-a-filters-lánc-beolvasása-szigorú--mérve-2026-08-15-685)
   néma elejtést okoz, ezért a PicasaPy inkább HIBÁT ad
   (`FilterWriteError`), mint hogy csendben kiírjon egy elveszőben lévő
   bejegyzést. A korlát **felső** korlát, nem elvárt darabszám: a hiányzó
   paraméter az eredetiben az alapértékre esik vissza (mérve: `unsharp=1`
   ≡ `unsharp2=1,0.600000`), a záró üres mező (`grain=1,;`) pedig tolerált.

### Az olvasás megengedő MARAD

A szigorítás kizárólag az **író** oldalra vonatkozik. A beolvasás továbbra
is kis-nagybetű-tűrő (`FilterOp.matches`, `casefold`) — a felhasználó
ini-jében bármilyen írásmód előfordulhat (más eszközök, régi verziók), és
azt meg kell értenünk. A két irány összekeverése régi könyvtárakat tenne
olvashatatlanná.

### Hol zár a kapu

| réteg | viselkedés |
|---|---|
| `parse_filters` | változatlan: megőrzi a kapott írásmódot, nem validál |
| `serialize_filters` | változatlan: bájtra pontos, nem kanonizál, nem dob (bélyegkép-kulcs, #301) |
| `serialize_filters_for_write` | kanonizál **és** validál — ez az ini felé menő kapu |
| `EditSession.to_value()` | kanonizál (nem dob): a MÓDOSÍTOTT lánc helyes írásmóddal megy vissza |
| `EditSession.append_effect`/`apply`/`toggle`/`set_*` | kanonizál **és** validál: a saját kezűleg gyártott bejegyzés soha nem lehet néma elejtésű |

A `to_value()` szándékosan nem dob: a láncban maradhatnak idegen eredetű,
hibás paraméterszámú elemek, és azokat a round-trip elv szerint bájtra meg
kell őriznünk (#301) — a validáció ott zár, ahol a bejegyzés keletkezik.

**Amire szándékosan NINCS paraméterszám-korlát** (a regiszterből nem
vezethető le, találgatni pedig tilos): `save`, `crop64`, `crop`, `rot`,
`redeye`, `retouch`, `picnik` (adathordozó `history`/`persist` bejegyzések),
`colorfix`, `whitept` (rejtett „Choose White Point" csúszka + külön
`colorcircle` — nem dönthető el, hány mező ez a láncban),
`PicnikFocalPixelate` (a `filterdesc-registry.md` 4.1 kimondja, hogy nincs
rá valós mintánk), valamint `PicnikTint` és `ReanimatedEyeColor` (festhető
maszkos effektek — nem igazolt, hogy a maszk foglal-e lánc-paramétert).

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

### A mérés megerősítette — valódi Picasa-export, 7 kép (2026-08-15)

A kódból tett jóslatot méréssel ellenőriztük (`tools/golden/make_validation_kit3.py`).
Jelzőeffekt a `bw`, mert a mérőkép szürke sávjait nem, a színfoltokat viszont
látványosan mozdítja.

| kép | lánc | mért ΔE | mi történt |
|---|---|---|---|
| A | `sepia=1;bw=1;` | 17,238 | **mindkettő lefutott** (kontroll) |
| B | `nincsilyen=1;bw=1;` | **0,181** | semmi — a `bw` sem futott le |
| C | `sepia=1;nincsilyen=1;` | 21,251 | **csak a `sepia`** |
| D | `grain2=1,0.5;bw=1;` | **0,181** | semmi |
| E | `sepia;bw=1;` (nincs `=`) | **0,181** | semmi |
| F | `bw=1;` | 10,132 | referencia |
| G | `sepia=1;` | 21,251 | referencia |

Két szigorú azonosság dönti el a kérdést:

* **C ≡ G bájtra** (`max|Δ| = 0`): az ismeretlen **záró** tag a már feldolgozott
  `sepia`-t érintetlenül hagyja — az előtte lévők tényleg megmaradnak.
* **B ≡ D ≡ E bájtra** (ΔE 0,0 páronként), és mindhárom **eltér** az `F`-től
  (ΔE 10,12): egyikben sem futott le a `bw`. A három hibamód — **ismeretlen
  név**, **rossz paraméterszám**, **hiányzó `=`** — tehát **azonosan**
  viselkedik: a lánc feldolgozása ott megáll.

*Bizonyítottsági fok: megerősített, kódból és mérésből egyaránt.* A jóslat a
natív kód olvasásából született, a mérés utólag igazolta — nem fordítva.

### A maradék bizonytalanság

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

## A `desat` — egy szűrőnév, amit nem ismertünk (#643 mellékága, 2026-08-15)

A név-feloldás (`FUN_008f9fe0`) nem-talált ága **két** nevet kezel külön:
`crop` (a `crop64` felé) és **`desat`**. A `desat` a binárisban pontosan
egyszer szerepel karakterláncként (`0x00c86f24`), és négy függvény hivatkozik
rá: `0x0050bd70`, `0x0050be10`, `0x0050e460`, `0x008f9fe0`.

### Mi ez

A `0x0050bd70` (146 bájt) egy **konstruktor**, és mindent elárul:

```c
FUN_00985ff0("%c,%f,%f,%f");                 // a szerializalasi formatum
FUN_00985ff0("desat");                       // az ini-kulcs
FUN_009ae560("CDesaturateFilter::name", …);  // az eroforras-kulcs a felirathoz
*in_EAX = CDesaturateFilter::vftable;
in_EAX[7] = in_EAX[8] = in_EAX[9] = in_EAX[0xc] = 0x3eaa7efa;   // = 0.333f
```

A `0x0050bd70`-hez tartozó szövegek közt ott a **`Filtered B&W`** felirat is —
ez pedig a mi `ansel` szűrőnk emberi neve
([`filterdesc-registry.md`](filterdesc-registry.md)).

**Következtetés:** a `desat` a **Filtered B&W** (`CDesaturateFilter`)
szűrő **másik, örökölt ini-kulcsa**. A paraméterformátuma is más:
`%c,%f,%f,%f` — jelzőkarakter + **három float**, vagyis a szín három
lebegőpontos csatornaként, nem a mai `ansel=1,ffffffff` pakolt hexként.
Az alapértékek négy helyen `0,333` — a három csatorna egyenlő súlya.

### MEGERŐSÍTVE: a `desat` és az `ansel` UGYANAZT a renderelőt hívja

A `CDesaturateFilter` vtable-jének egyik rekesze a **`0x0050ce70`** (53 bájt),
és az egyetlen érdemi dolga, hogy meghívja a **`0x0090e680`** munkafüggvényt.

Ugyanezt a munkafüggvényt hívja az `ansel` callbackje (`0x008f8410`) is:

```c
// FUN_008f8410 — az ansel callback
FUN_0090e680(dst, (szin >> 16 & 0xff) / 255.0f,
                  (szin >>  8 & 0xff) / 255.0f,
                  (szin       & 0xff) / 255.0f);
```

A `0x0090e680`-nak az **egész binárisban pontosan két hívója van**:
`0x008f8410` (ansel) és `0x0050ce70` (desat). Más nincs.

**Vagyis a két kulcs ugyanaz az effekt, ugyanazzal a képpont-művelettel.**
A különbség kizárólag abban van, hogyan érkezik a szín:

| | ini-alak | a szín útja |
|---|---|---|
| `ansel` | `ansel=1,ffffffff` | pakolt hex → `/255.0` → három float |
| `desat` | `desat=<jelző>,<f>,<f>,<f>` | három float **közvetlenül** |

Az átváltás tehát egzakt:

```
desat(r, g, b)  ==  ansel( round(r*255)<<16 | round(g*255)<<8 | round(b*255) )
```

A `desat` alapértékei mindhárom csatornán `0,333` (`0x3eaa7efa`), ami a
`0x555555` körüli semleges szürkének felel meg.

*Bizonyítottsági fok: megerősített* (a közös munkafüggvény és annak
kizárólagos két hívója az indexből visszakeresve).

### Szerkezeti mellékeredmény: csak KÉT kép-szűrő osztály van

Az RTTI-ben mindössze két érdemi kép-szűrő osztály szerepel:
**`CGenericFilter`** (ez viszi a 42 elemű natív regiszter szűrőit, a
callback-táblán át) és **`CDesaturateFilter`**. A `desat` tehát nem „alias",
hanem a **saját osztállyal rendelkező, örökölt megvalósítás** — ezért van
külön ini-kulcsa és külön paraméterformátuma.

### ⚠️ Miért sürgős ez nekünk

A `desat` **nincs a `FILTER_REGISTRY`-nkben**, tehát a parszerünk ismeretlen
névként kezelné. A ma bizonyított lánc-viselkedés miatt
([lásd fentebb](#-megfejtve-egy-hibás-bejegyzés-megszakítja-a-lánc-hátralévő-részét))
ez nem egy effekt elvesztése:

> Egy `desat=` bejegyzést tartalmazó `.picasa.ini`-nél **a lánc utána
> következő összes szűrője is elveszne** nálunk — pontosan az a hibaosztály,
> amit a #643 leírt, csak fordított irányban.

Régi Picasa-telepítésből örökölt mappáknál ez valós kockázat.

### MEGVALÓSÍTVA (#711) — és egy pontosítás a „lánc elveszne" állításhoz

A `desat` regisztrálva lett (`picasapy.ini.filter_registry.CANONICAL_FILTER_NAMES`
+ `MAX_PARAM_COUNTS["desat"] = 3`) és a renderelő oldalon az `ansel`
egzakt megfelelőjeként fut (`picasapy.render.chain._apply_desat_op`, a
fenti `desat(r,g,b) == ansel(...)` átváltással).

**Pontosítás:** a fenti idézet a natív Picasa OLVASÓ oldalára vonatkozó
mérésből (#643) lett átvezetve a PicasaPy-ra, de a saját `apply_filters`
lánc-feldolgozónk a `desat` regisztrálása ELŐTT sem viselkedett így — a
`#301` óta minden ismeretlen nevű bejegyzést némán kihagy, és a lánc TÖBBI
tagját (pl. az utána következő `bw`-t) továbbra is lefuttatja; az
író-oldali kapu (`serialize_filters_for_write`) ugyanígy bájtra megőrizte
az ismeretlen `desat=` bejegyzést és a mögötte állókat. A tesztekkel
(`tests/render/test_desat_711.py`, `TestDesatRoundTrip`) igazolva: ez a
két eset a javítás ELŐTT is zöld volt. Amit a javítás pótolt, az kizárólag
maga a `desat` EFFEKT renderelése (korábban a kép a `desat` szemszögéből
változatlan maradt, csak a `bw` futott le utána) — nem egy lánc-vesztési
hiba.

## Valódi korpusz: 859 `.picasa.ini` egy 43 éves fotógyűjteményből (2026-08-15)

A tulajdonos NAS-án lévő fotómegosztás **csak olvasásra** felcsatolva
végigleltározva. A számok a formátum-ismeretünk **kontrollmintája**:

| | darab |
|---|---:|
| `.picasa.ini` fájl | **859** |
| szekció összesen | 18 801 |
| ebből képfájl-szekció | 17 791 |
| `[Picasa]` / `[Contacts2]` / album-szekció | 733 / 244 / 33 |
| **`filters=` lánc** | **5 658** |
| különböző kulcsfajta | 31 |

### Kulcs-lefedettség: 31-ből 30 dokumentált volt

Gépi összevetés a jelen laphoz: a korpusz **egyetlen** olyan kulcsot
tartalmaz, ami eddig nem szerepelt itt.

**`link=`** — az album `[Picasa]` szekciójában, 16 előfordulás. Értéke egy
**Picasa Web Albums feed-URL**:

```
https://<aldomain>.google.com/data/feed/<projekció>/user/<felhasználó>/albumid/<albumazonosító>?<paraméterek>
```

Ez a megszűnt webalbum-szolgáltatás szinkron-hivatkozása. Adatot nem hordoz a
képről; olvasáskor **változatlanul meg kell őrizni**, írni nem kell.
*Bizonyítottsági fok: megerősített* (16 valós előfordulás, azonos szerkezet;
http és https alak is előfordul).

A többi 30 kulcs mind dokumentált volt — a formátum-leírásunk tehát **valós
adaton is hiánytalan**. (A felhasználó-specifikus `IIDLIST_<fiók>_lh` és
`<fiók>_lh` kulcsok a fiók nevét hordozzák, ezért a példákban általánosítva.)

### Melyik szűrőt használják VALÓBAN — 5 658 lánc alapján

Ez a legfontosabb kimenet: a fejlesztési sorrendet nem a szűrők száma, hanem
a **tényleges használat** kell vezesse.

| szűrő | előfordulás | | szűrő | előfordulás |
|---|---:|---|---|---:|
| `enhance` | **3 045** | | `autocolor` | 54 |
| `autolight` | **2 612** | | `unsharp2` | 27 |
| `fill` | **1 089** | | `Boost` | 22 |
| `crop64` | 801 | | `radblur` | 18 |
| `finetune2` | 561 | | `sepia` | 14 |
| `redeye` | 228 | | `bw` | 10 |
| `Vignette` | 219 | | `dir_tint` | 10 |
| `warm` | 118 | | `Lomo` | 6 |
| `sat` | 110 | | `HDR`, `glow2` | 4–4 |
| `tilt` | 102 | | `tint`, `Holga`, film-jelölők | 2–2 |
| `retouch` | 82 | | `Cinemascope`, `CrossProcess`, `Sixties` | 1–1 |

**Amit ez kimond:** a lánchasználat **erősen a tónus-javítók felé húz**. Az
első három (`enhance`, `autolight`, `fill`) a láncok **több mint felét** adja,
miközben a látványos effektek (`Lomo`, `Holga`, `HDR`, `Sixties`) együtt sem
érik el a 20 előfordulást.

### Negatív eredmény: a `desat` egyszer sem fordul elő

Az 5 658 láncban **nulla** `desat=` bejegyzés van. A #711 kockázata tehát
ezen a gyűjteményen **nem realizálódik** — a kulcs valószínűleg jóval régebbi
(Picasa 2 korabeli) mappákban élne. A javítás ettől még indokolt (a lánc-
megszakadás miatt), de a **prioritása csökkenthető**.

> **Adatvédelem:** a leltár kizárólag **kulcsneveket és darabszámokat**
> összesített. Feliratok, arcnevek, e-mail-címek, fiók- és albumazonosítók
> nem kerültek sem a dokumentációba, sem a repóba. A megosztás
> **csak olvasásra** volt felcsatolva.

## A `text=` sor formátuma — MEGFEJTVE valódi mintából (#371, 2026-08-15)

A jegy eddig **a tulajdonosra várt** („RÁD VÁR"): valódi Picasa-szerkesztés
ini-lenyomata kellett. A 859 fájlos korpuszban **két valódi `text=` sor** van
(egy egyblokkos és egy kétblokkos) — ez elég volt a formátum megfejtéséhez.

### Szerkezet: HOSSZ-ELŐTAGOS, nem sima `;`-vel tagolt

```
text=<blokkok száma>;<blokkhossz>;<szöveghossz>;<szöveg>;<betűtípus>;<geometria>;<stílus>;;<blokkhossz>;…
```

Blokkonként hét mező, majd **két** záró pontosvessző.

| mező | jelentés |
|---|---|
| blokkhossz | a blokk hossza (a szöveghossz-mezőtől a `;;`-ig) |
| **szöveghossz** | a **DEKÓDOLT** szöveg **UTF-8 bájthossza** (ld. lent) |
| szöveg | a felirat, entitásokkal kódolt vezérlőkarakterekkel |
| betűtípus | a betűtípus teljes neve (pl. `Arial`, `Bickham Script Pro Regular`) |
| geometria | `x,y,méret,forgatás` — négy float |
| stílus | `v1,<kitöltő>,<körvonal>,…` — ld. lent |

### ⚠️ A csapda: a szöveg PONTOSVESSZŐT tartalmazhat

A sortörés `&#010;` alakban szerepel — **és ez maga is pontosvesszőre
végződik**. Egy naiv `;`-szerinti szétvágás tehát **elrontja a feliratot**.
Pontosan ezért van a formátumban hossz-előtag: a helyes parszer a
`szöveghossz` alapján lépi át a mezőt, nem elválasztót keres.

**A hossz a dekódolt szövegre vonatkozik.** A valós mintán:
a tárolt alak `&#010;`-t tartalmaz (6 bájt), a bejegyzett hossz viszont az
**újsorra cserélt** változaté — a két mintán 63 és 19 bájt, mindkettő
pontosan egyezik a dekódolt UTF-8 hosszal.
*Bizonyítottsági fok: megerősített* (két független minta, mindkettő stimmel).

#### A `blokkhossz` képlete — LEZÁRVA (#371 megvalósítási kör, 2026-08-25)

Egy korábbi kör *erősnek*, nem *megerősítettnek* jelölte ezt a mezőt, mert a
kétblokkos minta első blokkján „egy karakterrel eltért a kézi számolástól".
**Az eltérés nem egy karakter volt, hanem öt — és rendszeres.** A helyes
képlet a szöveget a **DEKÓDOLT** hosszával számolja:

```
blokkhossz = len(str(szöveghossz)) + 1 + szöveghossz + 1
           + len(betűtípus) + 1 + len(geometria) + 1 + len(stílus) + 1
```

(minden hossz UTF-8 bájtban; a záró `+1` a blokkzáró **első**
pontosvesszője). A döntő eset a kétblokkos minta első blokkja: ott a tárolt
alak `&#010;`-t tartalmaz (6 bájt), a dekódolt újsor 1 — a tárolt hosszal
számolva 192 jönne ki a valódi **187** helyett.

| blokk | tárolt alapú | dekódolt alapú | valódi |
|---|---:|---:|---:|
| egyblokkos minta | 161 | **161** | 161 |
| kétblokkos, 1. blokk | 192 | **187** | 187 |
| kétblokkos, 2. blokk | 126 | **126** | 126 |

*Bizonyítottsági fok: megerősített (3/3 blokk).* Ebből következik, hogy a
mező **levezethető**, tehát a parszernek nincs rá szüksége (a `szöveghossz`
elég), az írónak pedig **újra kell számolnia** — különben egy szerkesztett
felirat hossz-mezője hazudna.

### Geometria — normalizált hely, RADIÁNBAN mért forgatás

```
x, y      0..1 normalizált pozíció a képen
méret     0..1, a kép rövidebb oldalához mérve
forgatás  RADIÁN
```

A forgatás radián voltát a valós adat bizonyítja: a három előforduló érték
`0.000000`, `1.308997` és `-4.712389` — azaz pontosan **0°, 75,000° és
−270,000°**. Kerek fokértékek radiánban; véletlen egybeesés kizárt.
*Bizonyítottsági fok: megerősített.*

### Stílus — két szín `0xAARRGGBB`-ben

```
v1,<kitöltőszín>,<körvonalszín>,128.0,1.0,<a>,1.0,<vastagság>,<b>,49152
```

| minta | kitöltő | körvonal |
|---|---|---|
| egyblokkos | `4294899423` = `0xFFFEF6DF` (krémfehér) | `4278190080` = `0xFF000000` (fekete) |
| kétblokkos | `4292215592` = `0xFFD60328` (bíbor) | `4293454056` = `0xFFE8E8E8` (világosszürke) |

A `<vastagság>` mindkét mintán `700` — ez a **szabványos CSS/GDI félkövér
súly**. A `49152` (`0xC000`) állandó; a `<b>` mező `0` és `258` (`0x102`)
értéket vett fel. *Bizonyítottsági fok: a színek és a súly megerősített;
a `128.0`, az `<a>` és a `<b>` mező jelentése **nyitva**.*

### `textactive=`

Külön kulcs a képszekcióban, 173 előfordulással; a korpuszban **mindenhol
`0`**. Ez a felirat-réteg láthatóságát kapcsolja. Az `1` értékre nincs
mintánk. *Bizonyítottsági fok: erős (a szerep), a `0`/`1` szemantika
feltételes.*

## A retus és a vörösszem régió-adata NINCS az ini-ben (#371, negatív eredmény)

A korpusz 5 658 láncában a `redeye` **228-szor**, a `retouch` **82-szer**
szerepel — de **mindig paraméter nélkül** (`redeye=1;`), és a képszekciókban
**nincs** `redeye=` vagy `retouch=` kulcs a régiókhoz.

**Következtetés:** a Picasa a foltok/régiók koordinátáit **nem a
`.picasa.ini`-be** írja, hanem az adatbázisba (`db3`). Az ini csak azt
rögzíti, hogy a művelet szerepel a láncban.

Ez ellentmond a #371 kiinduló feltevésének (miszerint a régió-formátum az
ini-ből dekódolható lesz). *Bizonyítottsági fok: megerősített* (310 valós
előfordulás, kivétel nélkül).

### …és a `db3`-ban sincs — kimerítő keresés (2026-08-15)

A feltevés az volt, hogy a régiók az adatbázisba kerülnek. **Ez sem igaz.**
A tulajdonos valódi `db3`-ának mind a **36 `imagedata_*` oszlopát**
átvizsgáltuk:

| keresett | hol fordul elő |
|---|---|
| `rect64(` | **kizárólag** `imagedata_deferredface` és `imagedata_deferredregion` — mindkettő **arc**-régió (`rect64(…),<név>` párok) |
| `retouch` / `redeye` | **kizárólag** `imagedata_filters`, és ott is **paraméter nélkül** (544 lánc, `redeye=1,…` alakú **nulla**) |

Megnéztük a `.picasaoriginals/.picasa.ini`-t is (az eredeti kép mellé írt
lenyomatot): ott is csak `filters=autolight=1;redeye=1;` áll, régió nélkül.

**Következtetés (erős hipotézis):** a Picasa a retus-ecsetvonások és a
vörösszem-foltok koordinátáit **egyáltalán nem őrzi meg**. A `redeye=1;` /
`retouch=1;` csak **jelölő**: a mentett/renderelt változat eltér az
eredetitől. Ezt támogatja a `revertable`, `originfast` és `originslow`
oszlopok léte — a visszaállítás az **eredeti fájlból** történik, nem a
műveletek visszajátszásából.

### MEGERŐSÍTVE: a javítás a MENTETT KÉPBE van beleégetve

A korpuszban **113 olyan kép** van, amelynek a lánca vörösszem-javítást
tartalmaz **és** megvan mellette a megőrzött eredeti (`.picasaoriginals/`).
Ez lehetővé tette a közvetlen összevetést — felhasználói próba nélkül.

Három, **kizárólag `redeye=1;`** láncú képen (1280×960) az eredeti és a
mentett változat különbsége:

| kép | eltérő képpont | arány | a foltok |
|---|---:|---:|---|
| A | 177 | 0,014% | 4 folt, 8–10 px, **két párban** (y≈510 és y≈355) |
| B | 152 | 0,012% | 1 folt, 16×14 px |
| C | 246 | 0,020% | 4 folt, 11–14 px, **két párban** (y≈728 és y≈608) |

A foltok **azonos magasságban, párosával** állnak, egymástól 40–55 képpontra —
ez pontosan a szemtávolság. A kép többi része **érintetlen**.

**Következtetés:** a vörösszem-javítás a **mentett JPEG-be van beleégetve**,
az ini pedig csak a csupasz `redeye=1;` jelölőt hordozza. A visszaállítás
ezért az `.picasaoriginals/` (régebben `Originals/`) mappából történik, nem
a művelet visszajátszásából.

*Bizonyítottsági fok: **megerősített*** (kimerítő negatív keresés három
tárolóban + közvetlen pixelösszevetés valódi eredeti/szerkesztett párokon).

### Az export sem alkalmazza újra — és ez implementációs szabály

A tulajdonos ugyanezekről a képekről **exportot** is készített. Az exportált
és a mappában lévő (már javított) fájl különbsége: átlag `|Δ| < 0,5`,
maximum 24, és **egyetlen olyan képpont sincs, ahol az eltérés > 30** — ez
tiszta JPEG-újratömörítési zaj. Az exporttól az **eredetihez** képest viszont
ugyanaz a néhány száz képpont tér el, mint a mentett fájlnál.

**Vagyis a Picasa exportkor nem alkalmazza újra a vörösszem-javítást** — nem
is tudná, koordináta híján —, hanem a már javított képet rendereli tovább.

> **Szabály a PicasaPy-nak:** a `redeye=1;` (és a `retouch=1;`) bejegyzést
> **azonosságként** kell renderelni, ha a bemenet a mappában lévő fájl.
> Ha saját vörösszem-algoritmust futtatnánk rá, **kétszer javítanánk** —
> a Picasa-kimenettől eltérnénk olyan képeken, amiket ő már javított.

### A javítás képpont-művelete — a delta-pixelekből visszafejtve

Három kép 575 megváltozott képpontján, eredeti → javított:

| | R | G | B |
|---|---:|---:|---:|
| **előtte** (átlag) | 108,0 | 51,8 | 40,4 |
| **utána** (átlag) | 54,3 | 45,6 | 41,9 |

- a **vörös csatorna esik** (átlag −53,6, medián −44, maximum −156);
- a zöld alig (−6,1), a kék gyakorlatilag nem változik (+1,5);
- a színesség eltűnik: `|R−G|` átlaga **56,3 → 9,1**.

A leképezés a kimeneti vörösre:

```
R' ≈ max(G, B)
```

a mért eltérés átlaga `+1,6`, szórása `11,0` — a szórást a foltszél
lágyítása és a JPEG-zaj magyarázza; a folt belsejében a közelítés szoros.

*Bizonyítottsági fok: erős* (három kép, 575 képpont; a szélek keveredése és
a JPEG-veszteség miatt a pontos vágás/keverés nem különíthető el).

> ⚠️ **A `max(G, B)` alak MEGDŐLT** — ld. a következő szakaszt. Három képen
> nem volt eldönthető, mert ott a zöld volt a nagyobb a két csatorna közül,
> így `max(G, B) = G`. Huszonnyolc képen a kettő szétválik, és a mérés a
> **kisebbiket** adja.

### A kiválasztási feltétel — 28 kép, 11 952 képpont (#720)

A fenti mérés kibővítve. A korpusz 113 vörösszem-párjából **57** olyan van,
ahol a lánc **csak** `redeye=1;` (más effekt nem torzít); ebből **28** pár
azonos méretű és a `.picasaoriginals` tényleg ugyanannak a képnek a
szerkesztetlen változata. Ez a 28 pár adja a mérést.

**Módszertani megjegyzés a küszöbökről.** A szerkesztett fájl újratömörített
JPEG, ezért mindenhol van zaj. A foltokon kívül mérve ez **átlag 5,9 · 99%:
27 · maximum 39** szint. Ezért számít „biztosan érintett"-nek a **≥ 40**
szintű eltérés és „biztosan érintetlen"-nek a **≤ 8** — a köztes sáv kimarad
az értékelésből.

#### A feltétel egy ARÁNY, nem különbség

A javított foltok köré vont dobozban minden képpontot besorolva, az EREDETI
képpontértékből számolt jelöltmértékek találati aránya:

| mérték | legjobb küszöb | egyezés |
|---|---:|---:|
| **`R / max(G, B)`** | **> 1,67** | **94,4 %** |
| `R / (G + B)` | > 0,91 | 93,6 % |
| HSV-telítettség | > 128 | 91,9 % |
| `Cr` (YCbCr) | > 156 | 86,5 % |
| `R − max(G, B)` | > 52 | 86,1 % |
| `R − (G+B)/2` | > 62,5 | 84,3 % |
| `R` önmagában | — | 70,4 % |

Az **arány-alapú** mértékek nyolc százalékponttal verik a **különbség**-
alapúakat, és tizenhat ponttal a puszta vörös szintet. A `Cr` — amire az
irodalom épít — itt csak a középmezőny.

#### Amit a mérés KIZÁRT

- **Nincs külön csillanás-védelem.** Az érintett képpontok világossága
  99. percentilisben 233, maximuma 255 — világos képpontokat is átír. A
  csillanás mégis megmarad: a fehér fénypont **közel semleges**, tehát az
  aránya ≈ 1, és már a fő feltételen fennakad. A foltokon belüli 87 közel
  semleges, 200 fölötti világosságú képpontból a Picasa **kettőt** írt át
  (2,3 %). Vagyis az `Y > 220` típusú külön szabály **fölösleges**, ha a
  feltétel arány-alapú.
- **Nem kitöltött korong.** Lyukkitöltés + morfológiai zárás után az egyezés
  94,4 %-ról **90,1 %-ra romlik** — a javítás tehát valóban képpontonként
  megy, nem egy összefüggő foltra.
- **Nincs lágy szél.** A javítás erőssége (0 = érintetlen, 1 = teljesen a
  célszintig) mediánban **1,03**, a képpontok **82 %-ánál 0,9 fölött**. Kemény
  csere, nem alfa-keverés. (A szórást a JPEG magyarázza.)

#### A kimenet: közel semleges szürke a KISEBBIK csatorna szintjén

| | R | G | B |
|---|---:|---:|---:|
| **előtte** (átlag) | 119,5 | 41,4 | 46,7 |
| **utána** (átlag) | 37,3 | 34,6 | 34,7 |

A kimenet gyakorlatilag szürke: `|R'−G'|` átlaga **3,2**, `|G'−B'|` **2,1**
(az eredetin ugyanez 78,1 és 10,4). **Mindhárom csatorna elmozdul**, nem csak
a vörös.

A szürke szintjének illesztése (|eltérés| átlaga, ugyanazon a képpont-
halmazon):

| jelölt | |eltérés| |
|---|---:|
| **`min(G, B)`** | **8,03** |
| `G` | 8,78 |
| `(G+B)/2` | 9,78 |
| `B` | 13,54 |
| `max(G, B)` | 14,30 |

A `min(G, B)` és a `G` a JPEG-zajon (5,9) belül van egymáshoz képest — a
korpuszban a képpontok **70 %-ánál `B > G`**, tehát a kettő legtöbbször
egybeesik, és nem választható szét. A `max(G, B)` viszont **mérhetően rossz**:
ugyanazon a halmazon 14,3 a 8,0-val szemben.

```
érintett, ha  R / max(G, B) > ~1,67
akkor         R' = G' = B' ≈ min(G, B)
```

*Bizonyítottsági fok: erős.* 28 kép, 11 952 érintett képpont. Ami **nyitva
marad**: a küszöb rögzített-e vagy adaptív — a képenkénti legjobb küszöb
mediánja 1,57, szórása 0,27, tartománya 1,28–2,29, de ezt a szám a doboz
peremének tartalma is befolyásolja, ezért nem dönthető el ebből.

### Mit jelent ez a PicasaPy-nak

A `retouch=1,<rect64>…` **saját kiterjesztésünk** így nem ütközik semmivel —
a Picasa ezt a mezőt úgysem írja. **Viszont a Picasa nem is fogja
értelmezni**: egy általunk retusált kép a Picasában retusálatlan marad
(illetve a lánc ott megszakad, ld. a lánc-viselkedést fentebb, #643).
Ez **elvi korlát**, nem hiba — a doksiban kimondva, hogy a fejlesztés ne
próbálja „megjavítani".

## Az eredeti képek mentése — KÉT elnevezés, verzióváltással

A Picasa a módosítás előtti eredetit külön mappába menti. A korpuszban
**mindkét** elnevezés előfordul, és élesen elválik időben:

| mappanév | darab | évek |
|---|---:|---|
| `Originals` (látható) | 127 | **2005–2009** |
| `.picasaoriginals` (rejtett) | 54 | **2009–2016** |

A váltás **2009-ben** történt (az egyetlen átfedő év). Egy ini-t olvasó
implementációnak **mindkettőt** ismernie kell, ha a „vissza az eredetihez"
funkciót támogatja. *Bizonyítottsági fok: megerősített* (181 valós mappa).

## A `filterdesc` tartományai a VALÓS korpuszon ellenőrizve (2026-08-16)

859 `.picasa.ini`, **5 658 `filters=` lánc**, **9 147 bejegyzés**, **28**
különböző szűrő. Forrás: a korpusz helyi másolata
(`referencia/ini-korpusz/korpusz.txt` — a NAS teljes bejárása tilos, ld. az
ottani `README.md`-t).

### Gyakoriság és mért paraméter-tartományok

| szűrő | db | mért tartományok |
|---|---:|---|
| `enhance` | **3 045** | paraméter nélküli |
| `autolight` | **2 612** | paraméter nélküli |
| `fill` | 1 089 | p1 `+0,028 … +0,785` |
| `crop64` | 801 | p1 = `rect64` hex |
| `finetune2` | 561 | p1 `0…0,444` · p2 `0…0,222` · p3 `0…0,328` · **p4 = SZÍN** · p5 `−0,579…+1,000` |
| `redeye` | 228 | paraméter nélküli |
| `Vignette` | 219 | p1 `4,386…50,000` · p2 `1,000…1,573` · p3 `0…80,702` · p4 = SZÍN |
| `warm` | 118 | paraméter nélküli |
| `sat` | 110 | p1 `−0,708 … +0,848` |
| `tilt` | 102 | p1 `−1,000 … +0,439` · **p2 mindig 0** |
| `retouch` | 82 | paraméter nélküli |
| `autocolor` | 54 | paraméter nélküli |
| `unsharp2` | 27 | p1 `+0,600 … +3,000` |
| `Boost` | 22 | p1 `9,942 … 50,000` |
| `radblur` | 18 | p1 `0,354…0,799` · p2 `0,359…0,696` · p3 `0,404…1,000` · p4 `−1,000…+0,146` |
| `dir_tint` | 10 | p1…p4 `0,008…1,000` · p5 = SZÍN |
| `Lomo` | 6 | p1 `0…53,216` · p2 `0…47,368` |

### Amit ez igazol

1. **A `filterdesc.xml` tartományai a teljes valós korpuszt lefedik.** Egyetlen
   mért érték sem lóg ki — sem alul, sem felül. A `filterdesc` tehát nem
   „elméleti" dokumentáció, hanem a futásidejű igazságforrás; a
   parser-validáció nyugodtan ráépíthető.
2. **A `tilt` második paramétere a korpuszban MINDIG 0** — 102 előfordulásból
   mind. Ez független megerősítése annak, amit a `filterdesc-registry.md` a
   `filterdesc`-ből olvasott ki: a `tilt` 2. csúszkája **letiltott**
   (`enable="0"`), csak a v1-kompatibilitás miatt van a láncban.
3. **A `sat` a negatív oldalt is használja** (`−0,708`), a `radblur` 4.
   paramétere szintén (`−1,000`) — a „`!` = 0..1 float" jelölés végleg
   elvetendő, ahogy a lap fentebb már írja.
4. **A `finetune2` 5. rekesze a színhőmérséklet** — a mért `−0,579 … +1,000`
   pontosan az `offset 1.0`-s, `−1 … +1`-es tengely.

*Bizonyítottsági fok: megerősített* (859 fájl, 9 147 bejegyzés, gépi
összevetés a `filterdesc.xml` `range`/`offset` értékeivel).

> **Módszertani megjegyzés.** Ez a kör **egyetlen NAS-hozzáférés nélkül**
> futott le: a korpusz helyi másolatból jött. Korábban ugyanez a kérdéstípus
> minden körben végigjárta a hálózati megosztást, és 2026-08-16-án
> **390 napló/mp**-et generált a 200/mp-es korláttal szemben.

## A `filters=` lánc SORRENDJE — nincs kényszer, de van szokás (2026-08-16)

5 658 valós lánc a helyi korpusz-másolatból.

### ❌ Szigorú sorrendi kényszer NINCS

Minden olyan szűrő-pár, ami legalább **15**-ször fordul elő együtt, **mindkét
sorrendben** előfordul. Egyetlen „X mindig Y előtt" szabály sincs.

**Következmény az íróra és a parszerre:** a lánc sorrendje **a felhasználó
szerkesztési sorrendje**, nem szabály. Az írónak nem szabad átrendeznie, a
parszernek nem szabad sorrendet feltételeznie.

*Bizonyítottsági fok: megerősített (negatív eredmény), 5 658 láncon.*

### De a szokásos sorrend erősen kirajzolódik

Átlagos relatív pozíció a láncban (0 = eleje, 1 = vége):

| szűrő | átlagos pozíció | db |
|---|---:|---:|
| `enhance` | **0,126** | 3 045 |
| `autolight` | **0,164** | 2 612 |
| `retouch` | 0,244 | 82 |
| `crop64` | 0,286 | 801 |
| `tilt` | 0,294 | 102 |
| `redeye` | 0,303 | 228 |
| `autocolor` | 0,474 | 54 |
| `warm` | 0,492 | 118 |
| `sat` | 0,593 | 110 |
| `Boost` | 0,667 | 22 |
| `Vignette` | 0,683 | 219 |
| `fill` | 0,712 | 1 089 |
| `finetune2` | **0,813** | 561 |
| `unsharp2` | **0,874** | 27 |

Az **első** tag 45 %-ban `enhance`, 36 %-ban `autolight` — együtt a láncok
**81 %-a** automatikus javítással kezdődik. Az **utolsó** tag leggyakrabban
szintén `enhance`/`autolight` (a sok egyelemű lánc miatt), utána `fill`
(11,6 %) és `finetune2` (6,7 %).

### Egy meglepetés: a vágás NEM elöl van

A `crop64` a láncoknak csak **8,9 %-ában** az első tag, az átlagos pozíciója
**0,286** — vagyis a felhasználók tipikusan **előbb futtatnak egy
automatikát, és utána vágnak**. Ez a mi felületünk sorrend-javaslataira is
tanulság: a vágás nem „első lépés" a valós használatban.

> **Módszertani megjegyzés:** ez a kör is **NAS-hozzáférés nélkül** futott, a
> `referencia/ini-korpusz/korpusz.txt` helyi másolatból.

## Teljes kulcs-leltár a valós korpuszból (2026-08-16)

859 fájl, **46 893 kulcs-sor**, **1 178 különböző kulcsnév**, **14 622**
szekció. Helyi korpusz-másolatból (NAS-hozzáférés nélkül).

### A húsz leggyakoribb kulcs

| kulcs | db | ismerjük? |
|---|---:|---|
| **`backuphash`** | **14 700** | specben ✅, a kódunk **nem írja** (megőrzi) |
| `IIDLIST_<fiók>_lh` | 6 045 | specben említve, kódban nincs |
| `filters` | 5 658 | ✅ teljesen |
| `faces` | 4 973 | ✅ (írás: #26) |
| `star` | 3 095 | ✅ |
| `rotate` | 2 426 | ✅ |
| **`originhash`** | **1 787** | specben **csak említve**, kódban nincs |
| `crop` | 761 | ✅ (`rect64`) |
| `name` | 713 | ✅ (`[contacts2]`) |
| `albums` | 620 | ✅ |
| **`P2category`** | 615 | Picasa 2-örökség, de ma is ÉL: a mappa gyűjtemény-hovatartozása. A `Projects (internal)` értékű mappákat a bal hasáb **Projektek** gyűjteménye listázza (#1029, `picasapy.index.project_folders`); a többi érték (`Folders on Disk` stb.) egyelőre csak megőrzött |
| `date` | 579 | ✅ |
| `onlinechecksum` | 380 | ✅ |
| `caption` | 208 | ✅ |
| `moddate` | 181 | ✅ |
| `category` | 179 | Picasa 2-örökség |
| `textactive` | 173 | ✅ |
| `width` / `height` | 172 / 172 | ✅ |
| `geotag` | 84 | specben, kódban **nincs** |
| `location` | 42 | 1 hely a kódban |

A „hexadecimális nevű" kulcsok (`3e0c6b88a16df349` stb., 20–109 előfordulás)
a `[contacts]` / `[contacts2]` szekciókban élnek: **arc-kapcsolat
azonosítók**.

### Szekciók

| szekció | fájlok |
|---|---:|
| `[picasa]` | **733** (a 859-ből) |
| `[contacts2]` | 244 |
| `[contacts]` | 197 |
| `[photoid]` | 17 |
| `[<fájlnév>]` | a többi 14 000+ |

### ⚠️ A `backuphash` a LEGGYAKORIBB kulcs — gyakoribb, mint a `filters`

14 700 előfordulás 5 658 lánc mellett: **majdnem minden szerkesztett fotó
kap egyet**, és a `[picasa]` szekcióban is megjelenik. A #643 kimutatta, hogy
**előállítható** (az írás időpontjából képzett XOR), de a kódunk ma csak
**megőrzi**, nem írja.

**Ez a leltár azt mutatja, mekkora a tét:** ha egy jövőbeli kör úgy dönt,
hogy írjuk, az a korpusz legsűrűbb kulcsát érinti.

### Amit ez a parszerre mond

**Az 1 178 különböző kulcsnév nagy része adat, nem séma** (arc-azonosítók,
fiókfüggő `IIDLIST_*`). A parszernek tehát **kulcs-agnosztikusnak** kell
lennie: amit nem ismer, azt bájtra megőrizze — ahogy a lap fentebb előírja.
A „ismeretlen kulcs = hiba" megközelítés itt elvileg sem működne.

*Bizonyítottsági fok: megerősített* (859 fájl, gépi leltár).

## A metaadat-ÍRÓ függvény: `0x007d55f0` (2026-08-16)

A `originhash` kulcs nyomán megtalált **egyetlen függvény, ami a fotó-szintű
metaadatokat a `.picasa.ini`-be írja**. 2 681 bájt, és a saját naplózó
sztringjei nevezik meg a lépéseit — ez a leghitelesebb forrásunk a
kulcssorrendre és a formátumokra.

### A KULCSOK ÍRÁSI SORRENDJE (a kódban, betű szerint)

| # | kulcs | fájloffset | megjegyzés |
|---:|---|---|---|
| 1 | `caption` | `0x007d56f0` | |
| 2 | `keywords` | `0x007d5755` | |
| 3 | `geotag` | `0x007d582e` | formátum: `%lf %lf` **vagy** `%lf,%lf` (két ág!) |
| 4 | `faces` | `0x007d5da2` | előtte a kontakt-hurok |
| 5 | **`originhash`** | `0x007d5e74` | |
| 6 | `star` | `0x007d5ec7` | értéke **`yes`** (`0x007d5ec2`) |
| 7 | `onlinechecksum` | `0x007d5f14` | |
| 8 | `photoid` | `0x007d5f71` | |
| 9 | **`origloc`** | `0x007d5fde` | |

**A korpusz megerősíti a sorrendet:** valós fájlokban `caption` →
`originhash` → `onlinechecksum` mindig ebben a relatív sorrendben áll.
(A `rotate`, `backuphash`, `IIDLIST_*`, `filters` **más útvonalon** íródik,
ezért kerül közéjük.)

### `originhash` és `origloc` — PÁR

A két kulcs egymás mellett íródik ugyanabban a függvényben:
az **eredeti fájl** helyét (`origloc`) és tartalom-ujjlenyomatát
(`originhash`) rögzíti — a `.picasaoriginals` / import-forrás követéséhez.

Az `origloc` a **korpuszban 0-szor** fordul elő (859 fájl) — vagyis csak
akkor íródik, ha az eredeti máshol van. Az `originhash` viszont **1 787-szer**
(32 hexa karakter, tehát 128 bites — MD5-alkatú).

### Az arcírás útvonala — a naplósztringek szó szerint

```
0x007d5888  "Writing metadata: Found %d faces"
0x007d59c6  "Processing face %d, person %s, rect %s"
0x007d5aee  "Found person (%s) => contact (%llx)"
0x007d5cbf  "PersistContactToINI failed: err %d"
0x007d5df5  "Writing face string to INI: location %s, value %s"
0x007d5965  "rect(%ld %ld %ld %ld)"        ← BELSŐ alak, nem a fájlformátum
0x007d5638  "%I64x"                        ← a kontakt-azonosító alakja
```

Ez az írás **sorrendjét** is megadja: előbb a kontakt kerül a
`[contacts2]`-be (`PersistContactToINI`), és **csak utána** a `faces=`
hivatkozás. Ha a kontakt-írás hibázik, a `faces=` sor sem íródik ki.

> ⚠️ A `rect(%ld %ld %ld %ld)` **nem** a fájlba írt alak — a fájlban
> `rect64(…)` van. A `rect(...)` a naplóba megy.

*Bizonyítottsági fok: megerősített* (diszasszemblált kód + 859 fájlos korpusz).

## A videó vágópontjai: `moviestart` és `movieend` (2026-08-16)

A `filters=` láncban két olyan kulcs is szerepelhet, ami **csak videóknál**
értelmes. Eddig „paraméter nélküli jelzőként" tartottuk nyilván őket —
**tévesen: hexadecimális értéket hordoznak.**

### A valós korpusz mind a két esete

859 fájlból kettőben szerepelnek:

| fájl | a `filters=` lánc |
|---|---|
| `M4V01960.MP4` | `moviestart=bf0df826;` |
| `M4V01962.MP4` | `movieend=b40728fd;moviestart=80252d;` |

### Amit ez a két sor eldönt

**1. Van paraméterük, és hexadecimális.** Nem jelzők.

**2. A hex NINCS nullákkal feltöltve.** A `80252d` **hat** jegy, nem nyolc.
Ez eltér a szín-paramétertől, ami mindig `%08x` (nyolc jegy) — a
parszernek itt **változó hosszú** hexet kell tűrnie.

**3. A sorrend itt sem kötött:** a `M4V01962.MP4`-nél a `movieend`
**megelőzi** a `moviestart`-ot. (Összhangban a lánc-sorrendről szóló
korábbi lelettel.)

### A feliratuk

| erőforrás | EN | HU |
|---|---|---|
| `filter_moviestart_label0` / `CTimeFilter::startname` | Start Point | **Kezdőpont** |
| `filter_movieend_label0` / `CTimeFilter::endname` | End Point | **Végpont** |

Az osztálynév — `CTimeFilter` — megerősíti, hogy **idő**-szűrőről van szó.

### Mit jelent az érték? (feltételes)

| érték | egész | `/ 2³²` |
|---|---:|---:|
| `bf0df826` | 3 204 604 966 | **0,7461** |
| `80252d` | 8 398 637 | **0,0020** |
| `b40728fd` | 3 020 530 941 | **0,7033** |

A `M4V01962.MP4`-nél így **0,20 %-tól 70,3 %-ig** tart a megtartott
szakasz — értelmes vágás. Időegységként viszont nem értelmezhető:
ezredmásodpercként a kezdőpont 2,3 óra lenne egy családi videóban.

> **Munkahipotézis:** a két érték a klip hosszának **32 bites törtrésze**
> (érték / 2³²), a `rect64` szellemében, ami koordinátánként 16 bites
> törtet használ.
>
> *Bizonyítottsági fok: feltételes* — lásd a következő szakaszt: a klipek
> hosszát azóta kimértük, és ez **két** hipotézist hagyott állva.

### ❌ Nálunk ma hibásan nulla paraméterű

`src/picasapy/ini/filter_registry.py:237–238` — `moviestart: 0`,
`movieend: 0`. A `render/chain.py:176` pedig a `_NOOP_MARKERS` közé sorolja
őket. A round-trip emiatt nem sérül (a nyers sztringet megőrizzük), de a
regiszter **téves adatot** állít, és erre későbbi validáció épülhet.

*Bizonyítottsági fok: megerősített* arra, hogy van paraméterük és
változó hosszú hex (a korpusz két esete) · **feltételes** a jelentésére.

### A vágópontok MÉRÉSE — négyből kettő hipotézis maradt (2026-08-16)

Az érintett klipek hossza `ffprobe`-bal kimérve:

| fájl | hossz |
|---|---:|
| `M4V01960.MP4` | **374,374 s** (6:14) |
| `M4V01962.MP4` | **385,886 s** (6:26) |

*(A harmadik érintett klip — `M4V09238.MP4`, `movieend=e88a1626` — a
gyűjteményben már nincs meg.)*

#### A négy hipotézis a mért hosszakon

| érték | egész | **tört** (`v/2³²·hossz`) | **100 ns** | **µs** | a klip hossza |
|---|---:|---:|---:|---:|---:|
| `bf0df826` (1960 start) | 3 204 604 966 | 279,3 s | 320,5 s | 3 204 s ❌ | 374,4 s |
| `80252d` (1962 start) | 8 398 637 | 0,75 s | 0,84 s | 8,4 s | 385,9 s |
| `b40728fd` (1962 end) | 3 020 530 941 | 271,3 s | 302,0 s | 3 020 s ❌ | 385,9 s |

#### ❌ Kizárva

- **Ezredmásodperc**: a legnagyobb érték 839 óra lenne.
- **Mikroszekundum**: 3 020 s, illetve 3 204 s — **a klipek nyolcszorosa**.

#### ✅ Ami állva maradt — KÉT hipotézis

**(a) A hossz 32 bites törtrésze** (`érték / 2³²`). Mindhárom érték a klipen
belülre esik, és a skála **klip-hossztól független** — nincs felső korlát.

**(b) 100 nanoszekundumos egység** — a Windows `REFERENCE_TIME`, a
DirectShow és a Media Foundation alapegysége. Mindhárom érték a klipen
belülre esik. Egy DirectShow-korabeli Windows-alkalmazásnál (a Picasa az)
ez a legkézenfekvőbb választás.

Az egyetlen szerkezeti ellenérv a (b) ellen: **32 biten a 100 ns-os egység
7 perc 9 másodpercnél elfogy** (`0xFFFFFFFF·10⁻⁷ = 429,5 s`). A két mért
klip 6:14 és 6:26 — épphogy alatta. Ha a Picasa 64 bites mezőt ír `%x`-szel
(a `80252d` hat jegye mutatja, hogy **nincs nullákkal feltöltve**), akkor
nincs plafon, és az ellenérv elesik.

#### A DÖNTŐ mérés, amit el kell végezni

Kell **egy 7 percnél hosszabb klip vágóponttal**, aminek a vágópontja
429 másodperc utánra esik:

- ha az érték **meghaladja** a `0xFFFFFFFF`-et → **(b) igaz**, 100 ns-os idő;
- ha az érték `0xFFFFFFFF` alatt marad, de a klipen belüli **aránya**
  stimmel → **(a) igaz**, törtrész.

A jelenlegi gyűjteményben ilyen klip nincs.

*Bizonyítottsági fok:* **megerősített** a két kizárt hipotézisre (a mért
hosszak nyolcszoros túllépése egyértelmű) · a maradék kettő között a
következő szakasz dönt.

### A vágópont 64 bites, `%I64x` alakban — a skála eldőlt (2026-08-16)

A mérés két hipotézist hagyott állva. **A parszer maga dönti el.**

#### A beolvasó út

```asm
0x0046470a  push 0xc81978          ; "moviestart="
0x00464710  call 0xc07f40          ; strstr(lánc, "moviestart=")
0x0046471e  lea  edx, [esi + 0xb]  ; +11 = a "moviestart=" hossza → az érték
0x00464742  call 0x985ff0          ; a részsztring másolása
0x0046474b  call 0x49fb50          ; ← az ÉRTELMEZŐ
0x00464754  mov  ebx, eax          ; az eredmény ALSÓ 32 bitje
0x00464756  mov  [esp+0x2c], edx   ; az eredmény FELSŐ 32 bitje
```

És az értelmező (`0x0049fb50`, 72 bájt) magja:

```asm
0x0049fb7e  push 0xc82fcc          ; "%I64x"
0x0049fb84  call 0xc07eef          ; sscanf
```

**A vágópont tehát 64 bites, hexadecimálisan tárolt egész** (`%I64x`).

#### Ez dönti el a skálát

| érv | mit mond |
|---|---|
| a mező **64 bites** | a „32 biten a 100 ns 7 perc 9 mp-nél elfogy" ellenérv **elesik** |
| a `%I64x` alak | ez a Windows `LONGLONG` szokásos kiírása; a **`REFERENCE_TIME`** (DirectShow, Media Foundation) pontosan `LONGLONG` **100 ns**-os egységben |
| a törtrész-hipotézis | egy arányt **64 biten, `2³²`-es nevezővel** tárolni értelmetlen — az alsó 32 bit sosem lenne kihasználva |
| a mért értékek | 100 ns-ként mindhárom a klipen **belülre** esik (320,5 s / 374,4 s; 0,84 s és 302,0 s / 385,9 s) |

> **A vágópont 100 nanoszekundumos egységben mért abszolút idő** a klip
> elejétől — a Windows `REFERENCE_TIME`.
>
> `másodperc = érték · 10⁻⁷`

#### A nulla jelentése

```asm
0x00464766  cmp  dword ptr [esp+0x2c], 0   ; felső 32 bit
0x0046476b  ja   0x464775
0x0046476d  test ebx, ebx                   ; alsó 32 bit
0x0046476f  jbe  0x4647fc                   ; nulla → ÁTUGRIK
```

A **0 érték azt jelenti, hogy nincs vágópont** — a szűrő ilyenkor létre sem
jön.

#### Miért nem lehetett méréssel eldönteni

A gyűjteményben **86 videó** szerepel a `.picasa.ini`-kben, négy
formátumban (`mp4` 52, `mpg` 29, `mov` 4, `m4v` 1) — de **mindössze
háromnak** volt valaha vágópontja, és abból kettő maradt meg. Egy hosszabb
videó vágópont nélkül nem mond semmit; a döntést a bináris hozta meg, nem a
mérés.

*Bizonyítottsági fok:* **erős** — a 64 bites `%I64x` alak és a
`REFERENCE_TIME` egyezése, plusz mindhárom mért érték illeszkedése.
Megerősítetté akkor válik, ha előkerül egy `0xFFFFFFFF`-nél nagyobb
(kilenc vagy több jegyű) vágópont: azt a törtrész-hipotézis nem tudná
előállítani.

## Az mtime-megkerülés mérlege — két mérés szól ELLENE (2026-08-24)

A „ha a külső író megérinti a képfájl `mtime`-ját, a Picasa újrafeldolgozza"
feltevés eddig **levezetés** volt, mérés nélkül. Ez a kör nem a windowsos
próbát végezte el, hanem azt kérdezte: **van-e a binárisban egyáltalán olyan
hely, ami módosítási időt hasonlít össze.** A válasz kétszer is nemleges.

### 1. Mind a HÁROM `CompareFileTime`-hívás rendezés-komparátor

| hívó | mit csinál | miből látszik |
|---|---|---|
| `0x00509930` (547 b) | két tömbelem összevetése `[base + i*12 + 4]`-nél | 12 bájtos rekordok, `ret` rendezési eredménnyel |
| `0x00509b60` (176 b) | ugyanaz, rövidebb változat | ugyanaz a rekordlépés |
| `0x009a6e40` (529 b) | **általános listaoszlop-komparátor**: `[this+0xe4]` az oszloptípus; **2** = FILETIME (`CompareFileTime` a `[handle + index*8]` párra), **4** = természetes (számtudatos) szövegrendezés | típuskapcsoló + `ret 4`, −1/0/1 visszatérés |

⇒ A teljes binárisban **egyetlen** `CompareFileTime`-hívás sincs
változásérzékelési szerepben. Mindhárom **megjelenítési rendezés**.

### 2. A könyvtárbejáró gyorsítótár-rekordjában NINCS módosítási idő

A program saját hibakereső CSV-kiíratása (`0x004f25f0`,
`Preferences\WriteDirscannerCSV`) rekordonként ezt írja ki:

```
Name , Creation Time , Access Time , Size , Type , Dirty , Valid
  @0        @+4            @+0xc      @+0x14  @+0x18  @+0x1c  @+0x1d
```

Mindkét időmezőt `0x0098b650` = `FileTimeToSystemTime` alakítja át, tehát
valóban FILETIME-ok — de a program **saját felirata szerint** a
*létrehozási* és a *hozzáférési* idő, **nem a módosítási**. Amit nem tárol
el, azt nem is hasonlíthatja össze később.

### Mit jelent ez — és mit NEM

> **Erős, de nem perdöntő bizonyíték az mtime-út ellen.** Két kiskapu marad:
> (a) egy 64 bites FILETIME **beágyazott** összehasonlítása (`cmp`/`sbb` a két
> duplaszón) nem használ `CompareFileTime`-ot, és importkeresésre láthatatlan;
> (b) a CSV-oszlopfeliratok a *hibakereső* ág feliratai — elvben elavulhattak
> a mögöttük lévő mezőkhöz képest.

**Amit még végigpróbáltam ebben a körben:** a `GetFileAttributesExW` egyetlen
hívója (`0x0072ac80`, 2056 b, `[0xc403c8]` a `0x0072b401`-nél) **csak
méretküszöböt** vizsgál, időbélyeget nem; a `0x009aeff0` =
`FindNextFileW`-burok a teljes `WIN32_FIND_DATAW`-t `rep movsd`-del adja
tovább, tehát a választás lejjebb történik, és a kitöltő helyet **nem
találtam meg**; a `thumbindex.py` `ThumbIndexEntry`-jében nincs időbélyeg.

### A gyakorlati következmény a MI kódunkra

A `src/picasapy/ini/photo_touch.py` **régen alapértelmezésben bekapcsolva**
átírta az éles fotók `mtime`-ját minden ini-írás után, egy olyan feltevés
alapján, ami **soha nem lett Picasa-oldalon megmérve**, és amelynek két
mérés mond ellent. ⇒ **#1320 elvégezve: az alapértelmezés KI**, a modul
opt-in kísérleti kapcsolóvá vált (`PICASAPY_TOUCH_PHOTO_MTIME=1`), és
bekapcsolt állapotban naplózza, hány fájlt érintett. A döntés indoklása:
`docs/decisions/photo-mtime-erintes.md`.

> **Egy helyesbítés helyesbítése.** Ez a szakasz eredetileg azt is állította,
> hogy a modul fejlécének első tényállítása (`FindFirstChangeNotificationW`,
> a szűrőben a `LAST_WRITE` bittel, rekurzívan) „nem ellenőrizhető". **Ez
> tévedés volt:** a `picasa-mappakezelo.md` 16.5 megtalálta a létrehozó
> hívási helyet (`0x007062b9`, szűrő `0x17`, `bWatchSubtree = TRUE`), tehát
> az állítás **megerősített**. A figyelő él — csak épp az értesítés utáni
> frissesség-vizsgálat kulcsa az ini dátuma, nem a képfájlé.

*Bizonyítottsági fok: a három komparátor besorolása **megerősített**
(diszasszemblálva); a CSV-mezőtérkép **megerősített**; az ebből levont
„nincs mtime-összehasonlítás" következtetés **erős**, nem megerősített.*

## ✅ MEGFEJTVE: az újraolvasás kulcsa az INI FÁJL saját dátuma (2026-08-24)

Az előző szakasz azt mutatta ki, hogy a **képfájl** `mtime`-ja nem szerepel a
frissesség-vizsgálatban. A folytatás megtalálta, hogy **mi szerepel helyette** —
és a válasz sokkal egyszerűbb, mint a levezetett megkerülési út.

### A mechanizmus

A Picasa mappánként eltárolja a mappa `.picasa.ini` fájljának
**utolsó írási idejét**, és a következő beolvasáskor ehhez méri a fájlt.

| elem | hol | bizonyíték |
|---|---|---|
| a tárolt érték | `db3/albumdata_inisync.pmp`, PMP-típus **0x04** (u64 = FILETIME), soronként egy mappa | a valódi adatbázisban 2371 sorból **1260** nem nulla |
| a kapcsoló | `Preferences\AlbumIniSync`, **alapértelmezés 1** | `0x00402a90` — az általános beállítás-olvasó (`0x00407a20`) hívása, `mov dword ptr [esp+0x40], 1` a default |
| a fájlidő kiolvasása | `GetFileTime(hFile, &létrehozás, **NULL**, &utolsó_írás)` | `0x00467bdd` (`[0xc40474]`) az ini-szinkron modulban (`0x00467090`); a **hozzáférési időt kifejezetten kihagyja** |
| a beolvasás | az ini-feldolgozó (`0x00456610`) hívása **`flags = 3`** értékkel | `0x00468108`, a `push 3` a `0x004680f9`-nél |

### A bizonyíték: 99,5% bitre egyezés VALÓDI adaton

A felhasználó saját `db3`-ját összevetettem a NAS-on lévő tényleges
`.picasa.ini` fájlok módosítási idejével (célzott `stat`, nem bejárás):

```
összevetve      : 787 mappa   (nem elérhető / nincs ini: 428)
EGYEZIK (≤2 ms) : 783   (99,5%)
eltérő          :   4
```

A négy eltérőből **három** olyan, ahol **az ini az újabb** — vagyis épp
*újraolvasásra vár*; ez a mechanizmus **működését** bizonyítja, nem cáfolja.
A negyedik 1 másodperces eltolás (írás → bélyegzés sorrendje).

Az egyezés 2014-től 2025-ig terjedő mappákon áll fenn, tehát nem egyetlen
beolvasási menet műterméke.

### ⚠️ A `filters` BENNE VAN a szinkronban

A `flags = 3` a lap korábbi szakasza szerint **mindkét kulcscsoport**:

- `flags & 1` — metaadatok (`rating`, `caption`, `keywords`, `faces`, …)
- `flags & 2` — **szerkesztések** (`filters`, `crop`, `rotate`, `bw`, `fix`, `text`, `backuphash`)

Vagyis a szinkron **nem** szűri ki a szerkesztéseket. Ha a `filters=` mégsem
jelenik meg, annak **nem a kiváltás az oka**.

### Amit ez a PicasaPy-ra kimond

> **A helyes lépés: egyszerűen írni a `.picasa.ini`-t.** A fájl írási ideje
> magától megváltozik, ezzel eltér a mappa tárolt `inisync` értékétől, és a
> Picasa a következő beolvasásnál újraolvassa — mindkét kulcscsoporttal.
>
> **A képfájl `mtime`-jának megérintése a mechanizmusnak NEM része.**
> A `photo_touch` modul egy olyan utat valósít meg, ami az eredetiben nem
> létezik. → **#1320 elvégezve (2026-08-24): az alapértelmezés KI.** A modul
> megmarad opt-in kísérleti kapcsolóként
> (`PICASAPY_TOUCH_PHOTO_MTIME=1`), mert a „segít-e mégis?" kérdést csak a
> felhasználó windowsos próbája döntheti el — de amíg nincs mért haszon,
> nem írjuk át az éles archívum időbélyegeit. Indoklás:
> `docs/decisions/photo-mtime-erintes.md`.

### Ami EZUTÁN is nyitva marad

Ha a kiváltás rendben van és a `filters` is hatókörben van, akkor a
felhasználó megfigyelése (a Picasa újraindítás után sem mutatta a
szerkesztésünket) **más okra** vezethető vissza. A legvalószínűbb jelölt a
lap „a `filters=` lánc beolvasása SZIGORÚ" szakasza (**#685**): a Picasa a
formailag nem megfelelő bejegyzést **némán elejti**. Ezt a szálat a #685
viszi tovább — **ez a kérdés nem ebben a körben keletkezett**, hanem a #643
örökségéből, és most **szűkebb** lett: nem a kiváltást kell keresni.

*Bizonyítottsági fok: az `inisync` jelentése **megerősített** (783/787 bitre
egyező valódi adat + a `GetFileTime` hívás a modulban); a `flags = 3`
**megerősített** (diszasszemblálva). **Nem találtam meg** magát az
összehasonlító utasítást — az `inisync` ↔ aktuális fájlidő vetést a
mérésből és a modulból következtetem, nem közvetlen kódolvasásból.*

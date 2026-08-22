# Specifikáció: Picasa központi adatbázis (db3 / PMP)

Forrás: NotebookLM notebook `f70b0a1c-1ef2-4f72-98ae-2bb7e946ba1e`.

A PicasaPy a PMP-adatbázist **csak olvassa** (egyszeri import meglévő Picasa-
telepítésből). A saját központi indexünk SQLite lesz; a kétirányú kompatibilitást
a `.picasa.ini` réteg biztosítja (a Picasa is abból építi újra a saját db-jét).

## Fájlhelyek (Windows-os Picasa telepítés)

| Elem | Útvonal |
|---|---|
| Fő adatbázis | `%LocalAppData%\Google\Picasa2\db3\` |
| Kapcsolatok | `%LocalAppData%\Google\Picasa2\contacts\contacts.xml` |
| Figyelt mappák | `%LocalAppData%\Google\Picasa2Albums\WatchedFolders.txt` |
| Arcfelismerésből kizárt | `%LocalAppData%\Google\Picasa2Albums\FRExcludeFolders.txt` |
| (XP) | `%userprofile%\Local Settings\Application Data\Google\...` |

- `WatchedFolders.txt`: soronként egy abszolút útvonal („Scan Always" mappák).
- Az útvonalak **abszolútak** → importnál útvonal-átíró (path remap) logika kell
  (más gép/meghajtó/OS).
- **#145:** mindkét fájl élesben kisbetűs néven is előfordul
  (`watchedfolders.txt`, `frexcludefolders.txt`) — a PicasaPy kis-nagybetű-
  függetlenül keresi meg őket (`picasapy.scanner.config_files`). A
  `FRExcludeFolders.txt` beolvasása és a benne felsorolt mappák (és alfáik)
  kiszűrése a `picasapy.scanner.exclude` / `scan_tree`/`sync_tree` modulokban
  készült el; a PicasaPy 1. fázisban (arcfelismerés hiányában) ezt teljes
  indexelés-kizárásként értelmezi, nem csak arcfelismerés-kizárásként.

## Meglévő telepítés automatikus felismerése (#146)

A `picasapy.scanner.discovery` modul a fenti fájlhelyeket keresi meg
Linuxon: Wine alatt futó Picasa esetén a `%LocalAppData%` a
`<wine-prefix>/drive_c/users/<felhasználó>/AppData/Local` (újabb Wine) vagy
`.../Local Settings/Application Data` (XP-stílusú profil) alá képeződik le;
ezeket a `discover_installations()` a `~/.wine` alapértelmezett prefixben és
(ha be van állítva) a `WINEPREFIX` környezeti változó prefixében is
végigpásztázza. Emellett a hívó tetszőleges kézi jelölt-mappát is átadhat
(`extra_candidates`) — ez a tipikus NAS-ra másolt db3-könyvtár esete. A
`Google`/`Picasa2`/`Picasa2Albums` alkönyvtárak és a `WatchedFolders.txt`
felismerése kis-nagybetű-független (#145).

Publikus API (`picasapy.scanner`):

- `discover_installations(extra_candidates=(), *, home=None, wineprefix=None) -> tuple[PicasaInstallation, ...]`
  — a felismert telepítések listája (`label`, `picasa2_dir`,
  `picasa2albums_dir`, `watched_folders_file` mezőkkel; bármelyik lehet
  `None`). Duplikátumokat (ugyanaz a könyvtár, két úton felismerve)
  összevonja.
- `propose_watched_folders(installation, remap: PathRemapper) -> tuple[Path, ...]`
  — az adott telepítés `WatchedFolders.txt`-jének beolvasása és
  útvonal-átírása a `pmpimport.PathRemapper`-rel a helyi (pl. NAS-mount)
  megfelelőre; az át nem írható bejegyzéseket kihagyja. Tisztán olvasó,
  mellékhatásmentes függvény — csak *javaslatot* ad, fájlt nem ír, ezért a
  7. rögzített döntésnek megfelelően bármikor, korlátlanul ismételhető.

A tényleges felhasználói jóváhagyás (melyik mappát vegyük át) és a
UI-bekötés (első-indulás dialógus / Mappakezelő-gomb) az integrátor
feladata — ez a modul csak a felderítést és a javaslat-számítást végzi.

## PMP formátum (oszlop-alapú bináris)

- Nem relációs db: minden logikai tábla (`imagedata`, `albumdata`, `catdata`)
  **minden oszlopa külön `.pmp` fájl**.
- Fájlszerkezet: fejléc (oszlop adattípusa: string / float / int + rekordszám),
  utána a nyers rekordok egymás után, **szeparátor nélkül**.
- `thumbindex.db` / `thumbs_index.db`: bináris indexfájlok — a PMP-rekordok és a
  fizikai fájlrendszer (képek/mappák abszolút útvonalai) összerendelése.
- Sérülés esetén a Picasa a `.pmp` fájlokat törli, a `scanlist.txt`,
  `thumbindex.db`, `thumbs_index.db` fájlokat megtartja, és az ini + EXIF/XMP
  adatokból újraépít.

## Validálás valódi adatbázison (2026-07-16) ✅

Egy valódi, 2 GB-os db3 készleten (Picasa 3.9, ~140 758 thumbindex-bejegyzés,
133 089 fájl, 2 371 album) a spec **hibátlanul teljesült**: mind az 54 `.pmp`
fájl fejléce érvényes, a thumbindex bitre pontosan parseolható, az útvonal-
feloldás működik. További, csak éles adatból látható tények:

- **Oszloponként eltérő rekordszám** (sparse táblák): pl. `filters` 140 661,
  `facerect` 7 044, `tags` 124 993. A tábla „hossza" = a leghosszabb oszlop.
- A leghosszabb oszlop (`filetype`, 140 758) **pontosan egyenlő** a thumbindex
  bejegyzésszámával → az 1:1 indexmegfeleltetés igazolt.
- **`crop64` natív u64-ként** tárolódik (bit-pakolt rect64: 4×16 bit L/T/R/B).
- **`facerect`** (u64): **VEGYES oszlop** — valódi `rect64`-et tárol ott,
  ahol megerősített arc-régió van, és `1`-et puszta jelzőként ott, ahol a
  detektálás lefutott, de régió nem került be. Két adatbázison mérve
  (2026-08-22, #26): a névadás nélküli telepítésben **csak 0/1** volt
  (ezért írtuk egy ideig tévesen, hogy „nem geometria"), a nevesített
  telepítésben viszont **629 valódi, geometriailag érvényes rect64**.
  Ld. [`picasa-arcfelismeres.md`](picasa-arcfelismeres.md) 3.3.
- **`facerectdata`** (str): **az arc JELLEMZŐPONTJAI** — megfejtve
  (2026-08-22): `conf(<megbízhatóság>),pan(<fejelfordulás>),leye(x,y),reye(x,y),mouth(x,y)`,
  relatív [0..1] koordinátákkal. A legtöbb soron csak `"1"` jelző áll.
  Ld. `picasa-arcfelismeres.md` 3.4/c.
- **`personalbumid`** (u32): **melyik személy-albumhoz tartozik a kép** —
  az érték az `albumdata` tábla **sorindexe** (a `]facealbum:<N>` token
  N-je). `0` = nincs hozzárendelve.
- **`personalbumrecs` / `…recs2`** (u32): a **javasolt** személy-album
  sorindexe, `0xFFFFFFFF` = nincs javaslat; a hozzá tartozó pontszám a
  **`personalbumrecvalues` / `…values2`** oszlopban (mért tartomány
  ≈ 5 100–6 300). A `2` utótag a `facetemplatesV2` nemzedéké.
- **`albumdata.albumcontactids`** (u64): a személy-album → **kontakt
  azonosítója**; hexben karakterre egyezik a `contacts.xml` `id=`
  mezőjével (**9/9** mérve). ⚠️ Az azonosító **telepítésfüggő** — gépek
  között nem hordozható, importáláskor a **név** az egyeztetés alapja.
- **`peoplealbumchecksum`** / **`albumpeoplechecksum`**: a képzési
  szabályuk **nem dőlt el** → **#1238**.
- **`deferredregion`** (str, ÚJ oszlop — a 2012-es listában nincs): a valódi
  arcadat-hordozó! Formátum: `rect64(<hex>),<Név>;rect64(<hex>),<Név>;...`
  — tisztanevű (nem hash-elt) régiólista. A rect64 hex itt is rövidülhet
  (15 karakteres érték élesben megfigyelve → zfill(16) kötelező).
  **Mérve (2026-08-22):** 10 175 nem üres sor, **13 941 régió**, mind
  geometriailag érvényes; a legtöbb régió **egyetlen soron: 45**. A hexből
  8 jegyűre is lekophat a vezető nulla.
- **`deferredface`** (str) — **a `deferredregion` PÁRJA**, ugyanaz a
  szerkezet, de **hash-elt azonosítóval**:
  `rect64(<hex>),<16 hexjegyű contact_id>`. Mérve: 6 870 sor, **11 128
  régió**. Két szentinel: **`ffffffffffffffff`** = „ismeretlen / nincs
  személyhez rendelve" (a leggyakoribb érték, 2 289 régió) és `0` (698).
  **A két oszlop átfedéséből** (1 588 közös sor, bitre azonos rect64-ek)
  levezethető a `contact_id → név` tábla — és kiderül, hogy a
  `deferredregion` **nem íródik újra kontakt-átnevezéskor**, tehát csak
  pillanatkép. Részletek:
  [`picasa-arcfelismeres.md`](picasa-arcfelismeres.md) 3.4.
- **További új oszlopok** a 2012-es listához képest: `edit_width`,
  `edit_height`, `deferredregion`.
- **`albumdata.date`**: OLE variant time — dekódolása valódi dátumokra
  helyesnek bizonyult.
- A thumbindexben **nem** volt „üres név + érvényes szülő = arc" bejegyzés
  (minden üres név törölt fájl volt) → az arc-bejegyzéses értelmezés
  verziófüggő lehet; ebben a készletben az arcok a `facerect`/`deferredregion`
  oszlopokban élnek.
- Az útvonalak Windows-formátumúak (`C:\Users\...`) → a path-remap réteg
  megkerülhetetlen.

## `contacts.xml`

A személynevek elsődleges, legpontosabb forrása (az ini `[Contacts]`/`[Contacts2]`
szekciói redundánsak/inkonzisztensek lehetnek). Backup-ban: `backup.xml`.
**OPCIONÁLIS**: sok telepítésen sosem jött létre (a felhasználó nem
kapcsolta össze Google-fiókkal a Picasát) — a hiánya nem hiba
(`docs/research-plan.md`).

Szerkezet (Atom feed, `gphoto:` névtér — a mezőnevek a `Picasa3.exe`
string-táblájából igazoltak, ld. `picasa-exe-strings.md`):

```xml
<feed xmlns='http://www.w3.org/2005/Atom'
      xmlns:gphoto='http://schemas.google.com/photos/2007'>
  <entry>
    <gphoto:personid2>b8e4117cf1d6615b</gphoto:personid2>
    <gphoto:fullname>Roy Avery</gphoto:fullname>
    <gaia_id>1234567890</gaia_id>
  </entry>
  ...
</feed>
```

`gphoto:personid2` ↔ a `[Contacts2]` `person_id` kulcsa, `gphoto:fullname`
↔ a név. A `gaia_id` (Google-fiók azonosító) egyelőre csak megőrzött, fel
nem használt mező. Importer: `picasapy.ini.contacts_xml`
(`load_contacts_xml`/`apply_contacts_xml`, #26 2. kör) — a MEGLÉVŐ
`[Contacts2]`-bejegyzések nevét egyezteti (round-trip: az `extra` mezők és
a kulcs írásmódja megmarad), új személyt nem hoz létre (azt az
arc-hozzárendelés, `faces_helper.py`, teszi meg, amikor tényleg
felhasználásra kerül).

## Csak a db-ben élő (újraépítéskor elvesző) adatok — import szempontból kritikus

- Ignorált arcok listája
- Képek egyedi sorrendje mappákban/albumokban
- Videók „date taken" / geotag módosításai
- → Ezeket a PMP-importnak KELL kinyernie, mert az ini-ből nem pótolhatók.

## Ismert hibamódok (az eredeti Picasában)

- „CBlock" hiba: sérült db, csak újraépítéssel javítható.
- Váratlan bezárás → index és fájlrendszer széteshet (rossz thumbnailek).
- Duplikált arckeretek újraépítés után (kézi + automata keret ugyanarra az arcra).
- Compacting: kilépéskor az elavult rekordok törlése/tömörítése.

## Referencia-implementációk a parserhez

| Projekt | Nyelv | Relevancia |
|---|---|---|
| `skisoo/PicasaDBReader` | Java | PMP + thumbindex → CSV (albumdata, catdata, imagedata); arcok kivágása ImageMagick-kel; path-replace támogatás |
| `vosbergw/picasa3meta` | Python | PMP/ini/exiv2 olvasó könyvtár — **a PicasaPy import-modul legjobb kiindulása** |
| `vosbergw/metaSave` | Python | picasa3meta példaalkalmazás: fa bejárása, .meta fájlok |
| `Philipp91/picasa2digikam` | Python | ini + contacts.xml → digiKam SQLite; tanulság: duplikált arcok üres célnál kerülhetők el |
| `bufemc/picasa2xmp` | Python | arcok → XMP MWG-RS sidecar; exiv2 + exiftool függőség |

## A `thumblab` modul: a tárolási réteg első kézből (2026-08-13)

A binárisban benne maradtak a fordító **forrásfájl-nevei**, és ezek megnevezik
a tárolási réteg három összetevőjét:

| forrásfájl | szerep | a bizonyíték ugyanabból a függvényből |
|---|---|---|
| `.\thumblab\CPropertyMap.cpp` | **tulajdonság-térkép** (oszlopalapú tár) | a **`%s_%s.%s`** fájlnév-minta |
| `.\thumblab\CBlockFile.cpp` | **blokkos fájltár** | `CBlockFile::Restore err=%d, %s` |
| `.\thumblab\CIndexer.cpp` | **kereső-index** | `wordhash.dat` + három hibaüzenete |

**A `.pmp` elnevezés kérdése ezzel lezárható.** A `%s_%s.%s` minta pontosan a
`<tábla>_<oszlop>.<kiterjesztés>` képzés, a modul valódi neve pedig
**PropertyMap** — a közösségi „.pmp" rövidítés tehát nem véletlen egybeesés,
hanem ráillik. A fájlnév-séma **első kézből igazolt**; csak maga a betűszó
származik a közösségtől (`skisoo/PicasaDBReader`), a `.pmp` szó szerint
valóban nem szerepel a string-táblákban.

### `wordhash.dat` — a szöveges keresés fordított indexe

A `CIndexer` írja. A három hibaüzenete megadja a szerkezetét:

- „Inconsistent dictionary.PoolSize()" → a szótár **pool-allokált**, a
  fejlécbeli méretnek egyeznie kell a tartalommal,
- „wordhash.dat: incorrect entity count" → a fejlécben **bejegyzés-számláló**,
- „wordhash.dat file: excess data" → a fájl hossza **pontosan meghatározott**.

Nem importálandó (újraépíthető). A tanulság: a szöveges keresés **előre épített
indexből** menjen, ne futásidejű szűréssel — nálunk ez az SQLite FTS5.

### A segédfájlok szerepe

| fájl | szerep |
|---|---|
| `albums.db` | album-nyilvántartás |
| `thumbs.db` · `thumbs2.db` · `bigthumbs.db` · `thumbs_index.db` · `index-thumbs.db` · `thumbindex.db` · `thumbindex.tid` | bélyegkép-gyorstárak több méretben és generációban |
| `previews.db` | nagyobb előnézetek |
| `facetemplates_0.db` · **`facetemplatesV2.db`** · `facetemplates_index.db` | **arc-sablonok, két generációban** — egybevág az `imagedata` `personalbumrecs` / `personalbumrecs2` mezőpárjával, és megmagyarázza a „Frissíteni kell az arcokkal kapcsolatos adatokat" migrációs kérdést |
| `distims.db` | hasonlósági ujjlenyomatok (a ki nem adott hasonlósági kereséshez) |
| `makemoviecache.db` | film-előnézeti gyorstár |
| `wordhash.dat` | szöveges kereső-index (ld. fent) |
| `repository.dat` | ~~a tár fő nyilvántartása~~ → **kulcs→érték tár**, ld. lent |
| `profilephotos.db` · `usernames.dat` | ~~a megszűnt online szolgáltatáshoz~~ → **mérve üres**, ld. lent |
| `starlist.txt` · `saverlist.txt` | az adatbázisból generált **egyszerű listák** (csillagozott, illetve képernyővédő-album), ld. lent |

**Importálás szempontjából mind eldobható.** Az arc-sablonok bináris
modell-adatok, a mi felismerőnkkel nem használhatók — ami átvehető, az a
**név–arc hozzárendelés**, nem a sablon.

### A négy segédfájl — MÉRVE, nem következtetve (2026-08-22)

A fenti négy sor eddig **egymondatos találgatás** volt. A 2026-08-22-i
profilmappa-másolaton (`research/testdata/Picasa2-arcok/`) mind a négy
tényleges tartalma megvan.

#### `repository.dat` — **kulcs→érték tár**, nem „nyilvántartás"

Nem a szokásos 20 bájtos PMP-fejlécet használja, hanem egy **egyszerűbb
alakot**:

```
uint32 magic = 0x3FCCCCCD          (ugyanaz, mint a PMP-nél)
uint32 count                       (a PÁROK száma, mérve: 33)
count × ( kulcs\0  érték\0 )       (null-lezárt UTF-8 sztringek)
```

A 33 pár többsége **mappa-útvonal → `"1"`** (vagyis halmazként használt
kulcsok), de **valódi beállítás is keveredik közéjük**, pl.:

```
[8] 'rawversion'  →  [9] '1.1'
```

⇒ **`repository.dat` = vegyes kulcs→érték tár**: a bejárt/ismert mappák
halmaza + néhány verzió-jellegű beállítás.

#### `usernames.dat` — mérve ÜRES

`8 bájt` összesen: `magic + count = 0`. Vagyis **egyetlen bejegyzés sincs
benne** — ebben a telepítésben nincs bejelentkezett Google-fiók. Ez
**egybevág a `network.log`-gal**, amiben egyetlen fotó-szolgáltatás felé
menő kérés sincs (ld. „A `Picasa2` PROFILMAPPA teljes leltára").
A `profilephotos_0.db` ugyanígy **4 bájt** = csak a magic.

#### `starlist.txt` — a csillagozott képek sima szövegben

50 sor, **CRLF** sorvégekkel, UTF-8 (ékezetes útvonalak), soronként **egy
abszolút útvonal**. ⚠️ **Vegyesen tartalmaz helyi meghajtót és UNC hálózati
útvonalat**:

```
C:\Users\…\Képek\AI\498683ac-….png
P:\testdata\2025-05-xx\IMG_20250501_093058.jpg
\\DS215j\photo\2009\2009-08-20 …\DSC03390.JPG
```

Vagyis a csillagozás **nem csak a `.picasa.ini` `star=yes` kulcsában él** —
a Picasa egy **lapos, teljes listát is vezet** róla. A `saverlist.txt`
(képernyővédő-album) ugyanez a formátum; a mintában **0 bájt**.

#### `scanlist.txt` — a meghajtó-szintű be/kizárás, élő minta

24 bájt, és pontosan ennyi:

```
-G:\
-X:\
-P:\
+C:\
```

Ez **igazolja a `+`/`-` előtag-szabályt** (a `picasa-mappakezelo.md` 11.3
levezetését) a lehető legkisebb valódi mintán: három meghajtó kizárva,
egy engedélyezve.

#### A bélyegkép-szintek mérete ezen a kis készleten

| fájl | méret |
|---|---|
| `previews_0.db` | **42,2 MB** |
| `thumbs_0.db` | 15,1 MB |
| `bigthumbs_0.db` | 12,7 MB |
| `thumbs2_0.db` | 5,4 MB |
| `profilephotos_0.db` | **4 bájt** (üres) |

⚠️ A sorrend **eltér** a nagy készleten mérttől (ott a `bigthumbs` volt a
domináns, 209 MB) — 3 338 képnél az **előnézet** viszi a legtöbb helyet.
A négyszintű gyorsítótár-modell (`picasa-imagedata-rekord.md` / a fenti
„bélyegkép-gyorsítótár NÉGY szintje") ettől érvényes marad.

#### Két oszlop-eltérés a két telepítés között

| oszlop | „A" (nagy, régi) | „B" (kicsi, új) |
|---|---|---|
| `imagedata_tagdate` | — | **van** |
| `imagedata_facequality`, `personalbumrecs*`, `personalbumrecvalues*` | — | **van** |
| `imagedata_suppress` | **van** | — |

⇒ Az oszlopkészlet **nem fix**: a Picasa csak azokat az oszlopfájlokat
hozza létre, amikre ténylegesen szükség volt. Egy importálónak ezért
**minden oszlop hiányát tűrnie kell**.

## PicasaPy saját tárolási terve (munkahipotézis)

- Központi index: **SQLite** — az `imagedata`/`albumdata`/`catdata` logikai
  struktúráját tükröző táblák + thumbnail-cache.
- Igazságforrás (source of truth): a `.picasa.ini` + kép-metaadat (kétirányú kompat).
- Szinkron-modul: fájlrendszer-figyelés; külső ini-változás → db-frissítés,
  app-beli változás → azonnali ini-írás.

## A bélyegkép-gyorsítótár NÉGY szintje — mérve valódi adatbázison (#598, 2026-08-15)

### A szintek és a fájljaik

A `Picasa2/db3/` mappában négy, egymástól független bélyegkép-tár él, mind
`<nev>_0.db` (adat) + `<nev>_index.db` (index) párban, plusz egy közös
`thumbindex.db`. A binárisban a szintek tagnevei egyetlen függvényből
(`0x00415790`) olvashatók ki:

```
m_pinkyThumbs · m_thumbs · m_bigThumbs · m_previewThumbs
```
és ugyanitt a fájlnevek: `thumbs.db`, `thumbs2.db`, `bigthumbs.db`,
`previews.db` (mellettük `albums.db`, `facetemplatesV2.db`).

> ⚠️ **A két felsorolás sorrendje NEM ugyanaz** — a tagnév↔fájlnév párosítást
> az objektum-eltolásokból kell venni, ld. lent („A visszaesési sorrend").
> A `thumbs2.db` a **legkisebb** szint (`m_pinkyThumbs`, 72 px).

### A méretek — VALÓDI adatbázisból mérve

A tulajdonos 2025-12-24-i Picasa-mentése (`picasa-app-settings-backup`,
110 fájl, ~2 GB) mind a négy tárat tartalmazza. A tárolt JPEG-ek
`SOF`-fejlécéből kiolvasott képméretek:

| szint | fájl | adatméret | **leghosszabb oldal** | minta |
|---|---|---:|---:|---:|
| apró („pinky") | `thumbs2_0.db` | 279 MB | **72 px** | 4000 |
| normál | `thumbs_0.db` | 806 MB | **144 px** | 4000 + 3000 |
| nagy | `bigthumbs_0.db` | 208 MB | **288 px** | 2989 + 2219 |
| előnézet | `previews_0.db` | 711 MB | **640 px** | 1396 + 736 |

**A szabály: a hosszabb oldal fixen kötött, a képarány megmarad.** Egy
2:3 arányú álló fotó a normál szinten `96×144`, a nagy szinten `192×288`.

A három bélyegkép-szint **pontosan duplázódik: 72 → 144 → 288.** Az előnézet
kilóg ebből (640), mert az már megjelenítésre készül, nem rácsba.

**Ellenőrzés mélységben:** a méréseket nem csak a fájlok elején végeztük — a
`previews_0.db`-t a 400. MB-tól, a `bigthumbs_0.db`-t a 150.-től, a
`thumbs_0.db`-t a 600.-tól újramintáztuk, és a leghosszabb oldal
**mindenhol ugyanaz** (640 / 288 / 144). Egyetlen kilógó méret sem fordult elő.

*Bizonyítottsági fok: megerősített* (valódi felhasználói adatbázis, két
független mintavételi ponton, több ezer elemű mintákkal).

> **Adatvédelmi megjegyzés:** a mérés kizárólag a JPEG-fejlécek
> **méretadatait** olvasta ki, képtartalmat nem bontott ki és nem mentett.
> Az adatbázis a felhasználó saját fotóiról készült — a repóba nem kerül.

### Amit ez a #598-ra mond

Ma **egyetlen** bélyegkép-szintünk van. Az eredeti négyet használ, és a
méretek nem önkényesek: a 72/144/288 duplázás azt jelenti, hogy a kisebb
szint a nagyobbikból **pontos felezéssel** előállítható — ez a szintek közti
generálást is olcsóvá teszi.

### A visszaesési sorrend — a kérő útvonalról (2026-08-15)

A négy tároló az adatbázis-objektum **fix eltolásain** ül. A párosítást két,
egymástól független hely adja meg a `0x00415790`-en belül: a konstruktorhívások
sora köti az eltolást a **fájlnévhez**, a nyomkövető címkék pedig ugyanazt az
eltolást a **tagnévhez**.

| eltolás | tagnév (címke) | fájl | méret | a címkézés címe |
|---|---|---|---|---|
| `+0x2178` | `m_thumbs` | `thumbs.db` | 144 px | `0x00416ea2` |
| `+0x2224` | `m_pinkyThumbs` | `thumbs2.db` | **72 px** | `0x0041731d` |
| `+0x22d0` | `m_bigThumbs` | `bigthumbs.db` | 288 px | `0x00416fc1` |
| `+0x237c` | `m_previewThumbs` | `previews.db` | 640 px | `0x004170e0` |

A konstruktorhívások: `0x00415ab1`–`0x00415ae6` (mind a négy a `0x006b5d40`-et
hívja, csak a nevet átadva). Figyelem: a **`thumbs2.db` a KISEBB** („pinky",
72 px), nem a második legnagyobb — a fájlnév sorszáma nem a szint sorrendje.

**A négy tagot mindössze 8 függvény érinti** az egész binárisban (a
`.text` teljes végigdiszasszemblálásával, az eltolásokra keresve).

#### Két, egymástól független visszaesési lánc

**Kis szintek** (`0x00425f60`, a bélyegkép-kérő fő munkafüggvénye):

```
m_thumbs (144)          0x00428340 — ha megvan, kész (jne 0x428399)
  → köztes lépés        0x00428382 (azonosítatlan, nem a négy tár egyike)
  → m_pinkyThumbs (72)  0x0042840d — a je 0x428403 ágon
```

**Nagy szintek** (`0x00425df0`, 355 bájt — ez a teljes függvény):

```
m_bigThumbs (288)       0x00425e2b — ha megvan, kész
  → m_previewThumbs     0x00425e80 — a 640-es szint
  → forrásból dekódolás 0x00425eae ([obj+0xf8] → 0x00506830)
```

Az aszimmetria valós: a **nagy** ág fölfelé esik vissza (a 288 hiányában a
640-ből kicsinyít, végül az eredeti fájlból dekódol), a **kis** ág lefelé
(a 144 hiányában a 72-t nagyítja). A nagy ág bemenetére a `0x00428754`-en
tartomány-ellenőrzés is fut a previews-tár indexére.

#### A 72 vs. 144 választás egy logikai kapcsoló

A `0x004290e0` **harmadik argumentuma** dönti el, melyik kis szint kell —
nem a kért képpontméret:

```asm
0x00429123  cmp  byte ptr [esp + 0xa54], al   ; a 3. argumentum
0x0042912d  lea  ecx, [ebp + 0x2224]          ; pinky (72)
0x00429133  jne  0x42913b
0x00429135  lea  ecx, [ebp + 0x2178]          ; thumbs (144)
0x0042913b  call 0x6b6a50
```

*Bizonyítottsági fok: megerősített* (az eltolás↔fájlnév↔tagnév párosítás és
a két elágazás-lánc közvetlenül visszakövetve) · **nyitott**: hogy a fenti
kapcsolót MELYIK felületi vezérlő állítja. A jelző a hívón (`0x004246e9`) is
csak továbbadott paraméter (`[ebp+0x10]`), nem itt születik. A főablak
elrendezésében ott van a `largethumbs` / `smallthumbs` gombpár
([`picasa-fo-ablak-elrendezes.md`](picasa-fo-ablak-elrendezes.md)), ami
kézenfekvő jelölt, de **ezt nem igazoltuk**.

#### Módszertani megjegyzés

A „ki nyúl ehhez a tagmezőhöz?" kérdésre a bináris-index nem válaszol (az
`xrefs` függvényhívásokat és adathivatkozásokat tart nyilván, nem
struktúra-eltolásokat). A `.text` teljes végigdiszasszemblálása az eltolásokra
keresve viszont **1,4 másodperc** helyben (`capstone` + `pefile`), és
mind a 8 érintett függvényt megadja. Általánosan használható fogás.

## Az `imagedata_avgcolor` oszlop — a KÉPLET (2026-08-21, K5)

Az `avgcolor` az egyetlen PMP-oszlop, amit a Picasa **számol**, nem
átvesz. A képlet és az élő adat egymást igazolja.

### A számoló — `0x009ac640` (252 b)

Az indexelő a `0x00425f60`-ban hívja (`0x004280c9`), majd az eredményt
az `"avgcolor"` kulccsal írja az adatbázisba (`0x004280e0` → `0x006a5060`):

```asm
0x004280a8  or   ecx, 0xffffffff       ; a teglalap-parameter: (-1,-1,-1,-1)
0x004280ab  sub  esp, 0x10             ;   = az EGESZ kep
0x004280bb  lea  ecx, [esp + 0xe4]     ; a dekodolt keppuffer
0x004280c9  call 0x9ac640
0x004280d1  push eax                   ; az eredmeny
0x004280d8  push 0xc813f0              ; "avgcolor"
0x004280e0  call 0x6a5060              ; adatbazisba iras
```

**Két előfeltétel** (`0x0042808e`–`0x004280a2`): a kép szélessége **és**
magassága is legalább **2** képpont; egyébként a hívás elmarad.

**Egy kizáró feltétel** a számolóban: ha a pixelformátum-lekérdező
(`0x009aab60`) **3**-at ad, a rutin azonnal **0**-t ad vissza
(`0x009ac656`–`0x009ac65b`).

### A ciklus — négy akkumulátor, csatornánként

```asm
0x009ac6c2  movzx ebp, byte ptr [ecx + 3]   ; a 4. bajt -> eax
0x009ac6c8  movzx ebp, byte ptr [ecx + 2]   ; a 3. bajt -> esi
0x009ac6ce  movzx ebp, byte ptr [ecx + 1]   ; a 2. bajt -> edi
0x009ac6d4  movzx ebp, byte ptr [ecx]       ; az 1. bajt -> [esp+0x14]
0x009ac6d9  add   ecx, 4                    ; kovetkezo 32 bites keppont
```

Egyszerű összegzés, **súlyozás és színtér-átváltás nélkül**.

### Az osztás és a csomagolás

```asm
0x009ac6fc  edx = jobb - bal          ; szelesseg
0x009ac700  ebx = also - felso        ; magassag
0x009ac704  imul edx, ebx             ; N = keppontok szama
0x009ac70b  div ecx                   ; osszeg[3] / N   -> ebx
0x009ac713  div ecx                   ; osszeg[2] / N
0x009ac715  shl ebx, 8 ; or ebx, eax
0x009ac71e  div ecx                   ; osszeg[1] / N
0x009ac720  shl ebx, 8 ; or ebx, eax
0x009ac72e  div ecx                   ; osszeg[0] / N
0x009ac730  shl ebx, 8 ; or eax, ebx
```

> **avgcolor = (átlag[3] << 24) | (átlag[2] << 16) | (átlag[1] << 8) | átlag[0]**
>
> ahol `átlag[k] = (a k. bájt összege) / N`, **egész osztással, tehát
> LEFELÉ CSONKOLVA** — nem kerekítve.

A képpuffer memóriabeli sorrendje BGRA (bájt0=B … bájt3=A), tehát a
tárolt dword **`0xAARRGGBB`**.

### Élő igazolás — `imagedata_avgcolor.pmp`

A valódi adatbázisban (`research/testdata/Picasa2/db3/`, 140 755 sor,
type-kód `0x0001`, 4 bájt/sor):

| megfigyelés | érték |
|---|---|
| nem nulla | 133 454 / 140 755 (a 7 301 nulla = ki nem számolt) |
| különböző értékek | 100 611 |
| felső bájt = `0xFF` | 125 070 |
| felső bájt = `0xFE` | 8 382 |
| egyéb felső bájt | 2 (`0xAC`, `0xB6`) |
| minta | `0xFFACA190`, `0xFFF7F8F9`, `0xFF233428` |

**A `0xFE` a képlet közvetlen következménye.** Ha minden képpont alfája
255, az átlag pontosan 255. Ha **akár egyetlen** képpont alfája kisebb, az
összeg `255·N` alá esik, és a **csonkoló** osztás azonnal **254**-et ad.
Ezért kétcsúcsú az eloszlás, és ezért van csak két, erősen átlátszó
kimaradó. *(Kerekítéssel ez a kettősség nem jönne létre — a képlet és az
élő adat tehát egymást igazolja.)*

A bájtsorrend (`0xAARRGGBB`) **független megerősítése** annak, amit a
kollázs csoport-keretének színénél (`picasa-kollazs-felulet.md` 2/b.3)
a `0xFF7D8397` konstans négy előfordulásából kalibráltunk.

### Ami NINCS mérve

**Melyik felbontású puffert átlagolja** — a teljes felbontású dekódolt
képet vagy az indexelés közben amúgy is előálló bélyegképet. A gyakorlati
különbség csekély (a doboz-szűrős kicsinyítés az átlagot közel pontosan
megőrzi), de bitre pontos egyezéshez számítana.

## Az `albumdata_hascollage` oszlop — MIT jelöl és MIKOR íródik (2026-08-21, K6)

**A kérdés hamis alternatívát kínált** („a forrásképekre vagy a kimeneti
képre?"): **egyikre sem**. A `hascollage` **nem képoszlop, hanem
ALBUM-oszlop** — a fájl neve is ezt mondja
(`albumdata_hascollage.pmp`, PMP-típuskód `0x03` = bájt, egy bájt
albumonként).

> **Jelentése: „ehhez az albumhoz tartozik egy mentett
> `PicasaCollage.cxf` fájl".**

### Az oszlop regisztrálása

A `0x00415790` (7851 b) oszlopregisztráló az `albumdata` táblához
(`0x004158c4`) sorolja, a **`[tábla + 0xe58]`** rekeszbe
(`0x00415a47`–`0x00415a66`). A regisztráló `0x00496020` — más, mint a
sztringoszlopoké (`0x004941f0`), összhangban a bájt-típussal.

### A beíró — `0x0044ead0(tábla, sorindex, érték)`

```asm
0x0044eb26  lea ebx, [esi + 0xe58]              ; a hascollage oszlop
0x0044ed39  mov al, byte ptr [ebp + 0xc]        ; a 2. paraméter = az ÉRTÉK
0x0044ed3c  mov byte ptr [ecx + edx], al        ; beírás (új sor)
   vagy
0x0044ed4a  cmp byte ptr [esi], al              ; ha nem változott -> kilép
0x0044ed4e  mov byte ptr [esi], al              ; beírás (meglévő sor)
0x0044ed5c  call 0x6a2a60                       ; a változás jelzése (mentendő)
```

### MIKOR lesz 1 — fájl-létezés, nem kollázs-mentés

Az album mentése/betöltése (`0x005608f0`, 3912 b):

```asm
0x00561329  call 0x47c3f0(tábla, sor, &útvonal)  ; << az album kollázs-útvonala
0x005613c0  call 0x992ed0(társ)                  ; Exists(társ)?
0x005613f5  call 0x994400(társ, útvonal, 1, 5)   ; ha igen: ATOMI ÁTNEVEZÉS
                                                 ;   (ugyanaz a rutin, amit a
                                                 ;    kollázs-mentés használ, 9.1/b)
0x0056141f  call 0x992ed0(útvonal)               ; Exists(a végleges)?
0x00561426  je   0x56143b                        ; nem -> marad 0
0x00561430  push 1
0x00561436  call 0x44ead0                        ; << hascollage = 1
```

Az útvonalat a **`0x0047c3f0`** (365 b) építi, és a fájlnév mindkét ágán
ugyanaz:

```asm
0x0047c52b  mov  edx, 0xc81b38    ; "PicasaCollage"
0x0047c530  call 0x69d7f0         ; utvonal-osszefuzes
0x0047c535  mov  eax, 0xc81b30    ; ".cxf"
0x0047c53c  call 0x9a3620         ; a kiterjesztes ellenorzese
0x0047c546  call 0x9a3930         ; ha hianyzik, hozzafuzes
```

> A vizsgált fájl: **`<az album mappája>\PicasaCollage.cxf`**

A másik hívó (`0x0055ece0` → `0x0055f1ea`) a **betöltési** ág: a bájtot
egy már beolvasott rekordból másolja át (`0x0055f1de`,
`movzx eax, byte ptr [edx + 0x31]`).

### Élő adat

`research/testdata/Picasa2/db3/albumdata_hascollage.pmp`: **2370 sor,
mind 0**. A tulajdonos könyvtárában tehát **egyetlen albumhoz sem**
tartozik `PicasaCollage.cxf` — összhangban azzal, hogy a
`Picasa2Albums` mappában sincs `.cxf`.

### Következmény a PicasaPy-ra

A `hascollage` **nem a kollázs-mentés mellékterméke**, hanem egy
**album-szintű, fájl-létezésből származtatott jelző**. Aki ezt
reprodukálja, ne a kollázs mentésekor írja, hanem az album
betöltésekor/mentésekor számolja ki a `PicasaCollage.cxf` meglétéből.

---

## A `Picasa2` PROFILMAPPA teljes leltára (2026-08-22)

Eddig a `db3` alkönyvtárat ismertük. A tulajdonos 2026-08-22-én adott egy
**teljes profilmappa-másolatot**, amiben a `db3` melletti mappák is
megvannak — ez a szakasz azokat leltározza. (A másolat helye:
`research/testdata/Picasa2-arcok/`, gitignore-olt.)

### A mappák

| mappa | mit tartalmaz |
|---|---|
| `db3/` | a központi adatbázis (PMP-oszlopok + `.db` blokkfájlok) — ld. fent |
| `contacts/contacts.xml` | a személynevek és azonosítóik |
| `cache/` | **webes HTTP-gyorsítótár** — saját, hatoszlopos PMP-táblával |
| `cache/feeds/<md5>` | a letöltött feed nyers XML-je |
| `runtime/*.ytf` | **futásidőben rasztereltt betűkészletek** (ld. lent) |
| `ioqueue/*.ioq` | három, **üres** művelet-sor: `albumsafe`, `filesafe`, `slingshot` |
| `tmp/` | üres |
| `network.log` | HTTP-napló |
| `network_expwebsites.log` | 0 bájt |

A `Picasa2Albums/` (testvérmappa) a `watchedfolders.txt` és
`frexcludefolders.txt` helye — ld. `picasa-mappakezelo.md` 11.

### A `.ytf` betűkészlet-gyorsítótár: SZÁLLÍTOTT vs. GENERÁLT

A `.ytf` formátum megfejtése a
[`picasa-program-resources.md`](picasa-program-resources.md) 3.5-ben van.
Ami **most derült ki**: kétféle `.ytf` létezik, és a különbség fontos.

| honnan | melyik betűk | darab |
|---|---|---|
| **a programmal szállítva** (`Picasa3/runtime/`) | `Praxis Semi Bold-Heavy`, `Praxis LT Regular`, `HelveticaNeue Condensed`, `HelveticaNeue MediumCond` | **12** |
| **futásidőben generálva** (`%LocalAppData%\…\Picasa2\runtime/`) | **`Arial`** (11, 12, 14, 16, 18, 24 — súly 400/700/**800**/**900**), **`Arial Bold`** (12, 24), **`Georgia`** (14, 20, 24) | **15** |

**Amit ez kimond:** a Picasa a **saját, márkás betűit** (Praxis,
HelveticaNeue) előre rasztereltten szállítja a felület krómjához, a
**rendszerbetűket** (Arial, Georgia) viszont **igény szerint, a felhasználói
profilba** rasztereli. A Georgia (talpas) jelenléte a kollázs/film/nyomtatás
felirataira utal, az Arial a felhasználói tartalomra.

⚠️ A **800-as és 900-as súly** csak a generált oldalon fordul elő — ezek
szintetikus (a rendszer által vastagított) változatok.

*(Egy második, független telepítés `runtime`-ja ugyanennek a részhalmaza —
9 fájl, ugyanezek a családok. A készlet tehát nem véletlenszerű.)*

### A webes gyorsítótár PMP-sémája

Hatoszlopos, soronként egy gyorsítótárazott válasz:

| oszlop | típuskód | mit tárol |
|---|---|---|
| `cacheindex_url` | `0x00` str | a kérés URL-je |
| `cacheindex_key` | `0x00` str | a gyorsítótár-kulcs |
| `cacheindex_fn` | `0x00` str | a `cache/feeds/` alatti fájlnév (MD5-alakú) |
| `cacheindex_etag` | `0x00` str | HTTP ETag |
| `cacheindex_lastfetch` | **`0x02`** | az utolsó letöltés ideje (8 bájt — **új típuskód**, dátum-jellegű) |
| `cacheindex_serial` | `0x01` u32 | sorszám |

⭐ **A `0x02` típuskód eddig nem szerepelt a leltárunkban** (8 bájt/sor,
dátum-gyanús — valószínűleg ugyanaz az OLE variant time, mint az
`albumdata.date`; **nem igazolt**).

### Mit hívogat a Picasa — a TELJES hálózati felület

A 1802 soros `network.log` **mindössze két végpontot** tartalmaz:

| végpont | kérések | mi ez |
|---|---|---|
| `clients2.google.com/service/update2` | **258 POST** | Google Omaha **automatikus frissítés-ellenőrzés** |
| `picasa-readme.blogspot.com/feeds/posts/default` | **91 GET** | a „Picasa readme" **Atom-hírfolyam** (a válasz a `cache/feeds/` alatt) |

Ez a két végpont pontosan a beállítás-alapértékek két kapcsolójához
tartozik (ld. `picasa-arcfelismeres.md` 1.1 és a `0x006e0cb0` alapérték-tábla):
**`AutoUpgradeCheck`/`AutoUpgradeAsk`** → az update2, **`AutoInfoCheck`** →
a blogspot-feed. Mindkettő alapból **bekapcsolva**.

> **Fotó-szolgáltatás felé egyetlen kérés sem ment** ebben a naplóban — a
> webalbum-szinkron itt sosem futott. Az online ág tehát **nem
> elkerülhetetlen**: a Picasa offline is teljes értékű.

A napló fejléce egyben megerősíti a binárisból ismert
naplózási kapcsolókat: `Log level 2, log faces 0` — a `LogFaces`
(`0x009170f0`) tényleg futásidejű kapcsoló.

### `ioqueue` — három, névvel ellátott művelet-sor

`albumsafe.ioq`, `filesafe.ioq`, `slingshot.ioq` — mindhárom **0 bájt** a
mintában. A nevekből: az album- és a fájlműveletek **külön, tartós
sorban** várakoznak (összeomlás-biztos írás), a `slingshot` pedig a
`runtime/slingshot/respack.yt`-tal egy családba tartozó feltöltő-ág.
**A formátumuk nincs feltárva** (üresek) — ha valaha kell, élő,
megszakított művelet közben készült másolat kellene.

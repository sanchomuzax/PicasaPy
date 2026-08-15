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
- **`facerect`** (u64): sok bejegyzésben `0x1` szentinel-érték (nem valós rect;
  jelentése tisztázandó — valszeg „arc detektálva, régió máshol").
- **`facerectdata`** (str): a tesztkészletben teljesen üres.
- **`deferredregion`** (str, ÚJ oszlop — a 2012-es listában nincs): a valódi
  arcadat-hordozó! Formátum: `rect64(<hex>),<Név>;rect64(<hex>),<Név>;...`
  — tisztanevű (nem hash-elt) régiólista. A rect64 hex itt is rövidülhet
  (15 karakteres érték élesben megfigyelve → zfill(16) kötelező).
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
| `repository.dat` | a tár fő nyilvántartása |
| `profilephotos.db` · `usernames.dat` | a megszűnt online szolgáltatáshoz |
| `starlist.txt` · `saverlist.txt` | az adatbázisból generált **egyszerű listák** a kísérőprogramoknak (csillagozott, illetve képernyővédő-album) |

**Importálás szempontjából mind eldobható.** Az arc-sablonok bináris
modell-adatok, a mi felismerőnkkel nem használhatók — ami átvehető, az a
**név–arc hozzárendelés**, nem a sablon.

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

**Nyitva marad:** melyik nézet melyik szintet kéri (a rács kicsi/nagy
bélyegkép-kapcsolója, a tálca, a szerkesztő szalagja), és mi a szintek
közötti visszaesési sorrend, ha egy szint hiányzik. Ehhez a bélyegkép-kérő
út visszakövetése kell — a jelen körben nem érintettük.

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

## PicasaPy saját tárolási terve (munkahipotézis)

- Központi index: **SQLite** — az `imagedata`/`albumdata`/`catdata` logikai
  struktúráját tükröző táblák + thumbnail-cache.
- Igazságforrás (source of truth): a `.picasa.ini` + kép-metaadat (kétirányú kompat).
- Szinkron-modul: fájlrendszer-figyelés; külső ini-változás → db-frissítés,
  app-beli változás → azonnali ini-írás.

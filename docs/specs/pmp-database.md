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

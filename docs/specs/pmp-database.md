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

### A típuskódok TELJES táblája — a binárisból, nem adatból (#2105)

A `Picasa3.exe` RTTI-jében a PMP-oszlopok `CColumn<…>` sablonpéldányok, és a
sablon **harmadik paramétere `0x13320000 + típuskód`** — a `0x1332` ugyanaz a
konstans, ami a fejlécben is ott van. A C++ típusnév magában a sablonban áll,
tehát a tábla **olvasott**, nem következtetett:

| kód | `CColumn` sablonpéldány | típus | méret |
|---|---|---|---|
| `0x00` | `CColumn<ytString,0,322043904>` | sztring | változó |
| `0x01` | `CColumn<unsigned_long,1,322043905>` | előjel nélküli 32 | 4 |
| `0x02` | `CColumn<double,1,322043906>` | **`double`** | 8 |
| `0x03` | `CColumn<signed_char,1,322043907>` | **ELŐJELES** bájt | 1 |
| `0x04` | `CColumn<unsigned___int64,1,322043908>` | előjel nélküli 64 | 8 |
| `0x05` | `CColumn<unsigned_short,1,322043909>` | előjel nélküli 16 | 2 |
| `0x06` | `CColumn<char_const*,1,322043910>` | C-sztring | változó |
| `0x07` | `CColumn<int,1,322043911>` | **ELŐJELES** 32 | 4 |

*(A `ytString` példány második paramétere `0`, a többié `1` — alighanem a
„fix méretű-e" jelző.)*

A korábbi, adatból levezetett négy kódunk (`0x00`, `0x01`, `0x03`, `0x04`)
**mind egyezik** ezzel, tehát a levezetés helyes volt. Két dolgot viszont
csak a bináris mond meg:

1. **A `0x02` `double`** — nem csak „8 bájt, dátum-gyanús". Dátumnál épp ez
   passzol: az OLE variant time is `double`.
2. **A `0x03` és a `0x07` ELŐJELES.** A PicasaPy beolvasója mindkettőt
   előjel nélkül olvasta; a tulajdonos `imagedata_edit_width.pmp`-jében
   (`0x07`, 2914 rekord) a `0xFFFFFFAA` emiatt **4 294 967 210**-ként jött
   vissza **−86** helyett (#2106).

Mind a nyolc kód előfordul a tulajdonos valódi adatbázisában (302 `.pmp`:
`0x00`×38, `0x01`×32, `0x02`×8, `0x03`×16, `0x04`×14, `0x05`×4, `0x06`×2,
`0x07`×4).
- `thumbindex.db`: az **útvonal-index** — a PMP-sorok és a fizikai
  fájlrendszer (képek/mappák abszolút útvonalai) összerendelése.
  Magic `0x40466666`, a bejegyzésszám a `+4`-en.
- `<nev>_index.db` (`thumbs_index.db`, `thumbs2_index.db`,
  `previews_index.db`, `bigthumbs_index.db`, `albums_index.db`,
  `facetemplatesV2_index.db`): **gyorsítótár-indexek**, teljesen más
  formátum — magic `0x3FCCCCCD`, a bejegyzésszám a `+8`-on. Nem
  útvonalakat tárolnak, hanem bájttartományt a párban álló `<nev>_0.db`-be.
  Részletes formátum: „Az `*_index.db` formátum" szakasz lent.
  ⚠️ A két fájl neve megtévesztően hasonló, a tartalmuk semmiben nem az —
  aki a `thumbs_index.db`-t útvonal-indexként olvassa, azonnal elhasal (#1444).
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

### Az `*_index.db` formátum — MÉRVE 11 fájlon, két adatbázison (2026-08-25, #1444)

> **Ez a szakasz JAVÍTJA a lenti ⛔ negatív eredmény 1. pontjának szerkezeti
> állítását.** Az index nem „12 bájtos rekordokból álló hash-tábla": három,
> egyenként darabszámmal előtagolt `uint32`-vektor, és a második-harmadik
> vektor **eltolás és hossz** a párban álló `<nev>_0.db` adatfájlba. Ezzel a
> `sorindex → bélyegkép` leképezés **előáll** — ld. lent.

#### A tényleges elrendezés

```
+0    uint32  magic       = 0x3FCCCCCD   (ugyanaz, mint a .pmp oszlopoké)
+4    uint32  ismeretlen  = 0            (mind a 11 mért fájlban 0)
+8    uint32  n           = bejegyzésszám
+12           uint32 kulcs[n]
              uint32 n                   (vektor-darabszám, ismét)
              uint32 eltolas[n]
              uint32 n                   (vektor-darabszám, ismét)
              uint32 hossz[n]
```

Vagyis: 8 bájt fájlfejléc (magic + egy nulla mező), utána **három,
darabszámmal előtagolt `uint32`-vektor**. A teljes méret ebből
`8 + 3 × (4 + 4n)` = **`20 + 12n`**, maradék nélkül.

#### Mérési bizonyíték — a méret

| fájl | méret | `n` (`+8`) | `20 + 12n` | `12 + 12n` |
|---|---:|---:|---:|---:|
| `arcok/thumbs_index.db` | 40 076 | 3 338 | **40 076** ✅ | 40 068 ✗ |
| `arcok/thumbs2_index.db` | 40 076 | 3 338 | **40 076** ✅ | 40 068 ✗ |
| `arcok/previews_index.db` | 71 672 | 5 971 | **71 672** ✅ | 71 664 ✗ |
| `arcok/bigthumbs_index.db` | 74 048 | 6 169 | **74 048** ✅ | 74 040 ✗ |
| `arcok/albums_index.db` | 1 748 | 144 | **1 748** ✅ | 1 740 ✗ |
| `arcok/facetemplatesV2_index.db` | 40 076 | 3 338 | **40 076** ✅ | 40 068 ✗ |
| `nagy/thumbs_index.db` | 1 689 080 | 140 755 | **1 689 080** ✅ | 1 689 072 ✗ |
| `nagy/thumbs2_index.db` | 1 689 080 | 140 755 | **1 689 080** ✅ | 1 689 072 ✗ |
| `nagy/previews_index.db` | 3 287 072 | 273 921 | **3 287 072** ✅ | 3 287 064 ✗ |
| `nagy/bigthumbs_index.db` | 3 287 072 | 273 921 | **3 287 072** ✅ | 3 287 064 ✗ |
| `nagy/albums_index.db` | 28 472 | 2 371 | **28 472** ✅ | 28 464 ✗ |

(`arcok/` = `research/testdata/Picasa2-arcok/Picasa2/db3/`, `nagy/` =
`research/testdata/Picasa2/db3/`.)

A „12 bájtos fejléc + n × 12 bájtos rekord" olvasat **mind a 11 fájlon
pontosan 8 bájttal kevesebbet** ad — ez a két extra vektor-darabszám. És a
darabszám mind a három vektor előtt tényleg ott áll: a `+8`, a `+12+4n` és a
`+16+8n` eltoláson **mind a 11 fájlban ugyanaz az `n`** áll.

#### Miért látszott hash-nek mind a három mező

A régi olvasat a rekord-ablakot a **kulcsvektoron belül** csúsztatta. A lenti
⛔ szakasz idézett „2. rekordja" — `0xdb3b20b7 0x8b14c30a 0x36fd4724` — a
`+44`, `+48`, `+52` eltoláson ül, ami a helyes olvasatban `kulcs[8]`,
`kulcs[9]`, `kulcs[10]`: **három egymást követő kulcs**, nem egy rekord három
mezője. Ezért tűnt mindhárom mező egyenletesen szórtnak, és ezért fordult elő,
hogy „néhány rekordban mindhárom mező azonos" (egymást követő, azonos kulcsú
slotok — pl. egy fotó és a hozzá tartozó arckivágások).

#### Mit jelent a három vektor

**`eltolas` és `hossz` — MÉRVE, nem következtetve.** A `hossz[i] > 0` slotok
`[eltolas[i], eltolas[i] + hossz[i])` tartományai:

- **egyetlen átfedés sincs** egyik fájlban sem (11/11);
- a legnagyobb végük **bájtra pontosan** a párban álló `<nev>_0.db` mérete
  (11/11) — pl. `arcok/thumbs_index.db` → 15 071 085 = `thumbs_0.db` mérete,
  `nagy/previews_index.db` → 711 231 091 = `previews_0.db` mérete.

Két, egymástól független egyezés 11 fájlon, két adatbázison — ez teszi az
„eltolás + hossz" olvasatot megerősítetté.

A tartományok nem hézagmentesek (pl. `nagy/thumbs_index.db`: 2 729 hézag
133 453 slotra). *Következtetés, nem mérés:* ez felszabadult hely, amit egy
újra-gyorstárazott, hosszabb bélyegkép hagyott maga után.

**`kulcs` — NEM fejtettük meg.** Amit MÉRTÜNK róla:

- `kulcs[i] ≠ 0` és `hossz[i] > 0` a 11-ből 10 fájlon pontosan együtt jár;
  az `arcok/albums_index.db`-ben 9 slotnak (109–117) érvényes tartománya van
  **nulla kulccsal**. → **A „használt-e a slot" próba a `hossz`, nem a kulcs.**
- A `previews_index.db` és a `bigthumbs_index.db` kulcsa a nagy adatbázisban
  **minden használt sloton azonos** (14 531/14 531).
- Ugyanott a `thumbs_index.db` kulcsa **egyetlen sloton sem** egyezik a
  `previews_index.db`-ével (0/14 531) → a kulcs tárankénti, nem globális
  fotó-azonosító.
- Az `arcok/thumbs_index.db`-ben egy fotó sora és a hozzá tartozó
  arckivágás-sorok **ugyanazt a kulcsot** viselik (pl. `0xeaf5d787` a 20.,
  111., 112. és 113. sloton, ahol a 111–113 szülője a 20.).
- A `facetemplatesV2_index.db` kulcsa **minden használt sloton `1`**, a hossz
  pedig állandó 1 044 bájt.

*Következtetés (nem mérés):* a kulcs érvényességi jelző / tartalom- vagy
paraméter-függő hash, amivel a Picasa eldönti, hogy a gyorstárazott blob még
a mai forráshoz tartozik-e. A képzése nincs visszafejtve — aki erre épít,
előbb mérje le.

##### ⛔ HELYESBÍTÉS (2026-09-02): a kulcs NEM tárankénti

A fenti mérési pontok közül a **harmadik** — „a `thumbs_index.db` kulcsa
egyetlen sloton sem egyezik a `previews_index.db`-ével (0/14 531) → a kulcs
tárankénti" — **érvénytelen következtetés**: a két vektor **nem ugyanabban a
réstérben él** (140 755 vs. 273 921 slot a nagy adatbázisban, 3 338 vs. 5 971
az arcokban), tehát a rés szerinti összevetés eleve értelmetlen. Két
különböző hosszú vektort hasonlítottunk össze indexről indexre.

**A helyes összevetés — azonos résterű tárak között:**

| összevetés | réstér | egyező kulcs |
|---|---:|---|
| `thumbs` vs `thumbs2` (arcok) | 3 338 | **3 338 / 3 338** |
| `thumbs` vs `thumbs2` (nagy) | 140 755 | **140 755 / 140 755** |
| `previews` vs `bigthumbs` (nagy) | 273 921 | **273 921 / 273 921** |
| `thumbs` vs `facetemplatesV2` (arcok) | 3 338 | 134 / 3 338 — és ez a 134 **pontosan az üres (könyvtár-) slotok halmaza**, ahol mindkét vektor 0 |
| `thumbs` vs `previews` | 3 338 vs 5 971 | **nem összevethető** |

Vagyis: **a kulcsvektor bitre azonos két olyan tár között, amelyek osztoznak a
réstéren** — akkor is, ha a tárolt blob teljesen más (a `thumbs` 144 képpontos
JPEG-je és a `thumbs2` 72 képpontosa ugyanarra a slotra más bájtokat tesz).

**Ebből következik, amit a fejlesztőnek tudnia kell:**

- a kulcs **nem lehet a tárolt blob ellenőrzőösszege** — különben a `thumbs` és
  a `thumbs2` kulcsa különbözne;
- a kulcs a **forrásfotóra** vonatkozó bélyeg, réshez (sorindexhez) kötve;
- a `facetemplatesV2` kivétel: ott a kulcs a használt slotokon állandó `1`,
  tehát az a tár nem használja a bélyeget.

**Hét kizárt jelölt.** A `thumbs_index.db` kulcsát a 3 204 élő sloton
összevetettük a `imagedata_originfast`, `originslow`, `onlinechecksum`,
`long`, `rotate`, `filetype` és `tagdate` oszlopokkal, alsó és felső 32 biten
egyaránt: **egyetlen egyezés sem** (0/3 204 mind a tizennégy összevetésben).
A kulcs képzése továbbra is **NYITOTT** — de a keresést ezek felé nem érdemes
újra elindítani.

*Bizonyítottsági fok: megerősített* (két adatbázis, négy tár, teljes vektorok).

##### A „csak nőnek, nem zsugorodnak" következtetés MÉRVE (2026-09-02)

A fenti fenntartás — hogy a `previews`/`bigthumbs` vektorban **elavult sorok**
maradnak egy korábbi, nagyobb katalógusból — eddig „következtetés, nem mérés"
volt. Most mérés:

| adatbázis · tár | élő slot | a blokk valódi JPEG (`FFD8`…`FFD9`) | NEM az |
|---|---:|---:|---:|
| nagy · `thumbs` | 133 454 | **133 454** | 0 |
| nagy · `thumbs2` | 133 454 | **133 454** | 0 |
| nagy · `previews` | 14 531 | **14 531** | 0 |
| nagy · `bigthumbs` | 14 531 | **14 531** | 0 |
| arcok · `thumbs` / `thumbs2` | 3 204 / 3 204 | **3 204 / 3 204** | 0 / 0 |
| arcok · `previews` | 1 030 | 814 | **216** |
| arcok · `bigthumbs` | 1 221 | 1 004 | **217** |

Az `arcok` készlet 216 hibás bejegyzéséből **185 a katalóguson túlmutató
sloton ül** (rés-index ≥ 3 338) — a `bigthumbs`-nál ugyanígy 185. Ez pontra
egyezik a fent már rögzített „186 használt slot túlmutat" mérésével
(185 hibás + 1 érvényes = 186). A maradék ~31 hibás bejegyzés a **fájl elejére**
mutat (legnagyobb elavult eltolás 8 482 391, miközben az érvényes bejegyzések
42 143 178-ig érnek): ez a terület azóta **újra fel lett használva**.

**Következmény a beolvasóra (#1446):** a `hossz > 0` próba **nem elegendő**.
Egy elavult sor is „élőnek" látszik, és olyan bájttartományra mutat, amit
azóta más blob foglal el. A beolvasó **ellenőrizze a tartalmat** — a
bélyegkép-tárakban a `FFD8` kezdet és a `FFD9` vég —, és a nem egyezőt hagyja
ki. A tulajdonos valódi mentésében ez a szűrő **egyetlen érvényes bélyegképet
sem dob el** (0 anomália mind a négy tárban).

*Bizonyítottsági fok: megerősített* (két adatbázis, hét tár-mérés).

##### A tároló neve és hibakeresője a binárisból (2026-09-02)

A fenti formátum eddig **kizárólag fájlmérésből** volt levezetve. A bináris
oldal független megerősítése:

| lelet | cím |
|---|---|
| az osztály neve `CBlockFile`, forrásfájlja `.\thumblab\CBlockFile.cpp` | `0x006b8640`, `0x006b9030` |
| a három mező NEVE: `Size,Offset,Checksum\n` fejléc + `%d,%d,%d\n` sorok | `0x006b5e00` |
| a dumpot registry-kulcs kapuzza: `Preferences` ▸ **`Write blockfile CSV`** (nem nulla ⇒ ír) | `0x006b5e07`–`0x006b5e5a` (`0xca8400` + `0xc7eafc`) |
| hibaágak: `CBlockFile::OpenBlock err=%d, %s`, `CBlockFile::Restore err=%d, %s` | `0x006b61e0`, `0x006b9030` |

A CSV **oszlopsorrendje** (Size, Offset, Checksum) NEM azonos a fájlbeli
vektor-sorrenddel (kulcs/„Checksum", eltolás, hossz/„Size") — a dump csak a
mezők **nevét** igazolja, a sorrendjüket nem. A `Restore` ág megléte azt is
megmutatja, hogy az eredeti **számol a sérült blokkfájllal**, és van
helyreállító útja.

#### A sorindex → fájlnév leképezés — MEGVAN

**A slot indexe azonos a `thumbindex.db` sorindexével** (és így a PMP-oszlopok
sorindexével). Három, egymástól független mérés:

1. **`facetemplatesV2_index.db`**: a 412 használt slot indexhalmaza
   **elemről elemre azonos** a `thumbindex.db` 412 arc-rekordjának
   indexhalmazával (üres név + érvényes szülőindex). Nem a darabszám
   egyezik — maga a halmaz.
2. **Az üres slotok könyvtárak.** `arcok`: 134 üres slot, **mind a 134** a
   `thumbindex.db` könyvtár-sora, és egyetlen nem-könyvtár sor sem üres.
   `nagy`: 7 301 üres slot, **mind a 7 301** könyvtár-sor, nem-könyvtár
   egy sem. (A 150, illetve 7 669 könyvtárból 16, illetve 368 mégis kapott
   bélyegképet — ezek a mappa-bélyegképek.)
3. **Darabszám-egyezés a megfelelő tábla sorszámával.**
   `arcok/thumbs_index.db` `n` = 3 338 = a `thumbindex.db` bejegyzésszáma =
   a leghosszabb `imagedata_*.pmp` oszlop. Az `albums_index.db` viszont az
   **album**-tábla sorszámát követi: `n` = 144 (arcok), illetve 2 371 (nagy)
   = a leghosszabb `albumdata_*.pmp` oszlop, mindkét adatbázisban.

A fájlnév tehát: slot `i` → a `thumbindex.db` `i`-edik sora →
`resolve_path()` (a `pmpimport/thumbindex.py`-ban) → teljes Windows-útvonal.
(Az `albums_index.db` sorindexe ennek megfelelően nem képre, hanem albumra
mutat.)

**Két fenntartás, kimondva:**

- A `previews_index.db` / `bigthumbs_index.db` `n`-je **nagyobb**, mint a
  `thumbindex.db` sorszáma (5 971 vs. 3 338; 273 921 vs. 140 758), és az
  `arcok` készletben 186 használt slot a `thumbindex.db` végén **túlmutat**.
  *Következtetés (nem mérés):* ezek a vektorok csak nőnek, zsugorodni nem
  zsugorodnak, így elavult sorok maradnak bennük egy korábbi, nagyobb
  katalógusból. Amíg ez nincs lemérve, a `previews`/`bigthumbs` párosítást
  **ellenőrizni kell**, nem feltételezni.
- A nagy adatbázisban a `thumbs_index.db` `n`-je 140 755, a `thumbindex.db`-é
  és a leghosszabb `imagedata_*.pmp` oszlopé egyaránt 140 758 — **hárommal
  kevesebb**. A gyorsítótár-vektor tehát lemaradhat az útvonal-index mögött;
  a legvégén lévő sorokra nincs slot. Aki `thumbs_index[i]`-t olvas, előbb
  nézze meg, hogy `i < n`.

#### Adatvédelmi megjegyzés

Az `*_index.db` fájlok **kizárólag `uint32`-eket tartalmaznak** — a parszolás
mind a 11 fájlon maradék nélkül elfogyasztotta a teljes fájlt, tehát nincs
bennük fájlnév, sem képtartalom. Maga az adatbázis a felhasználó saját
fotóiról készült, a repóba nem kerül.

### ⛔ NEGATÍV EREDMÉNY: a bélyegkép-tár NEM használható golden-referenciának (2026-08-23)

**A hipotézis, amit ellenőriztem** (a #951 kapcsán): ha a bélyegkép-tár a
Picasa **saját renderelésének** eredményét tárolja, akkor minden
szerkesztett képhez megvan az eredeti program kimenete — vagyis
golden-pár **export kérése nélkül**.

**A hipotézis NEM igazolódott.** Két, egymástól független ok:

#### 1. ~~Az index HASH-alapú — nincs olcsó fájlonkénti párosítás~~ ❌ MEGDŐLT (2026-08-25, #1444)

> ⚠️ **Ez a pont TÉVES volt, és nem áll fenn.** Az akkori olvasat a
> rekord-ablakot a kulcsvektoron belül csúsztatta, ezért látszott mindhárom
> mező hash-nek. A helyes formátum és a bizonyítékok: „Az `*_index.db`
> formátum" szakasz fent.
>
> A tényleges szerkezet **három, darabszámmal előtagolt `uint32`-vektor**
> (kulcs · eltolás · hossz), és a `sorindex → bélyegkép` leképezés **létezik**:
> a slot indexe azonos a `thumbindex.db` sorindexével. Így a fájlonkénti
> párosítás **olcsó**, hash-visszafejtés nélkül.

*Az eredeti (téves) állítás, a nyom kedvéért:* a rekordot 20 bájtos fejléc
utáni 12 bájtos, három hash-mezős egységnek olvastuk (pl. a „2. rekord":
`0xdb3b20b7 0x8b14c30a 0x36fd4724` — valójában `kulcs[8..10]`), és ebből
arra jutottunk, hogy a tár tartalom-címzett. A darabszám-mérés viszont
helyes volt: `thumbs_index.db` **3 338** (= a `thumbindex.db`
bejegyzésszáma), `bigthumbs_index.db` 6 169, `previews_index.db` 5 971.

#### 2. A kontroll-mérés a tartalmi hipotézist sem támogatja

Két készlet, **~200×** eltérő sepia-szerkesztési sűrűséggel:

| készlet | sepia-szerkesztés | szigorú „egyszínű barna" bélyegkép |
|---|---|---|
| kicsi (3 037 sor) | **79** (a szerkesztettek 6,4 %-a) | 23 / 1 166 = **1,97 %** |
| nagy (140 661 sor) | **19** (a szerkesztettek 0,15 %-a) | 101 / 2 988 = **3,38 %** |

Ha a tár a **szerkesztett** képpontokat tárolná, a nagy készletben
nagyságrenddel **kevesebb** sepia-kinézetű bélyegképnek kellene lennie.
**Az arány viszont nem követi a szerkesztési sűrűséget** — sőt, fordított.
A jel tehát a **valóban meleg tónusú eredeti** fényképekből jön (régi
szkennelt kép, naplemente, izzófényes belső), nem a szerkesztésből.

*(A detektor: a számottevő krómájú képpontok hue-jának körkörös
egységessége `R > 0,995`, átlagos hue 15–55°. Ez szigorú, de nyilván nem
hibátlan — épp ezért a **két készlet összevetése** a bizonyíték, nem az
abszolút szám.)*

#### Amit ez kimond

> ⛔ **A bélyegkép-tár ezen az úton NEM váltja ki a felhasználói exportot.**
> A #951 (Finomhangolás kompozit mérése) **továbbra is exportra vár**.

**Ami ettől még nyitva áll — 2026-08-25 óta OLCSÓBBAN:** a fájlonkénti
párosítás már megvan (slot index = `thumbindex.db` sorindex), tehát a
tartalmi kérdés (szerkesztett vs. nyers képpont) **egyetlen, névvel
azonosított képen** eldönthető, kutatási kerülőút nélkül. A 2. pont
(kontroll-mérés) ettől függetlenül **áll**: az továbbra is a tartalmi
hipotézis ellen szól.

*Bizonyítottsági fok: az index szerkezetére vonatkozó 1. pont **megdőlt**
(ld. fent) · **erős** a tartalmi negatív eredményre (két készlet
kontroll-összevetése) — de nem *megerősített*, mert a detektor hibás
pozitívjait nem zártam ki egyenként.*

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

⭐ **A `0x02` típuskód** a binárisból `double` (`CColumn<double,1,322043906>`,
#2105) — a „dátum-gyanú" ezzel megerősítést kapott a TÁROLÁS oldaláról: az
`albumdata.date` OLE variant time-ja is `double`. Hogy ez a mező TÉNYLEG dátum,
az továbbra is a mezőnév és az értéktartomány alapján valószínű, nem igazolt.

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

## Az `albumdata_inisync` oszlop — a `.picasa.ini` ÍRÁSI IDEJE (2026-08-24)

`albumdata_inisync.pmp`, PMP-típuskód **`0x04`** (8 bájtos előjel nélküli
egész), soronként egy albumdata-sor, azaz **mappánként egy érték**.

**A tartalma: a mappa `.picasa.ini` fájljának `LastWriteTime`-ja FILETIME-ként**
(100 ns-os egységek 1601-01-01 óta). Ez az a horgony, amihez a Picasa a
következő beolvasáskor méri a fájlt: ha a lemezen lévő ini **újabb**, a
mappát újra beolvassa.

### Mérés a valódi adatbázison

| | |
|---|---|
| összes sor | 2371 |
| nem nulla | 1260 |
| érvényes FILETIME-tartományban (2004–2036) | 1233 |
| tartományon kívüli („szemét") | **27** — ezekre az oszlop nem értelmezhető |
| összevetve valódi `.picasa.ini` fájllal | 787 (a többi mappa nem elérhető) |
| **bitre egyező (≤2 ms)** | **783 = 99,5%** |

A négy eltérésből három olyan mappa, ahol az **ini az újabb** — vagyis
újraolvasásra vár. A negyedik 1 másodperces eltolás.

Az egyezés 2014–2025 közti mappákon áll fenn, tehát nem egyetlen beolvasási
menet műterméke.

> ⚠️ **Módszertani figyelmeztetés a következő körnek.** Az oszlop első hat
> értéke egyetlen percen belül van, amiből először azt olvastam ki, hogy ez
> „a beolvasási menet pillanata". A teljes oszlop szórása **19 év**. Hat elem
> nem minta.

**Kapcsolódó:** a mechanizmus teljes leírása, a `Preferences\AlbumIniSync`
kapcsoló és a `flags = 3` beolvasás:
`picasa-ini-format.md` → „MEGFEJTVE: az újraolvasás kulcsa az INI FÁJL saját
dátuma".


## Az album-gyorstár és a tábla-jelzők (mérve 2026-08-26)

Három fájl, amit korábbi körök nem dokumentáltak:

| fájl | méret a mintában | mi ez |
|---|---:|---|
| `albumdata_0`, `catdata_0`, `imagedata_0` | **4 bájt** mindegyik | csak a `0x3FCCCCCD` mágikus szám — a logikai tábla **létezés-jelzője**, NEM sorszámláló |
| `albums_index.db` | 28 472 b | **ugyanaz a szerkezet, mint a `thumbs_index.db`**: 20 bájt fejléc + **12 bájtos** rekordok; a darabszám a 8. bájton (**2371**), és `(28 472 − 20)/12 = 2371,0` bitre kijön |
| `albums_0.db` | 7 480 128 b | a hozzá tartozó adattár; fejléc `0x3FCCCCCD` + `93` + `110`; **nincs benne JPEG- vagy PNG-fejléc** (0 találat az első 2 MB-ban), a bájtok 63 %-a nemnulla ⇒ **tömörítetlen** tartalom |

⇒ Létezik **album-szintű** gyorstár, a bélyegkép-gyorstár formátumcsaládjában.

### ⚠️ A `thumbs_index.db` NEM a `thumbindex.db` másik neve

| fájl | magic | szerkezet |
|---|---|---|
| `thumbindex.db` | **`0x40466666`** | névindex: útvonalnév + 26 bájt + szülőindex |
| `thumbs_index.db` | **`0x3FCCCCCD`** | gyorstár: 20 b fejléc + 12 b rekord (`(1 689 080 − 20)/12 = 140 755,0`) |

A két fájl **egyszerre** van jelen a valódi adatmappában. A
`pmpimport/importer.py:94` mégis aliasként kezeli őket — jegy: **#1489**.

---

## Új oszlop: `albumdata_unread` — és valószínűleg ez a KÖVÉR mappanév (2026-08-27)

A tulajdonos élő megfigyelése indította: *„amikor létrejött egy új kép, a
másolat, és a Picasa észrevette és importálta, a mappa neve a bal sávban
kövér (bold) szövegű lett."*

### A mező

| tulajdonság | érték |
|---|---|
| fájl | `albumdata_unread.pmp` |
| PMP-típuskód | **`0x03`** (1 bájt/rekord — a már ismert bájt-típus, ld. `albumdata_hascollage`) |
| rekordszám | 2366 (a tulajdonos valódi adatában) |
| értékkészlet | **logikai**: 2036 × `0`, **330 × `1`** |
| regisztráció | `0x00415790` — a db3 séma-felsoroló, ahol a `token`, `filename`, `category`, `description`, `location`, `hascollage`, `inisync` oszlopok is állnak |

**Ez a mező eddig NEM szerepelt a leltárunkban.**

### Az értelmezés

Az „unread" (olvasatlan) per-album logikai jelölő. A tulajdonos megfigyelése
szerint a mappa neve pontosan akkor lett kövér, amikor a Picasa **új képet
vett észre és importált** a mappába — vagyis a jelölő „ebben a mappában
olyasmi van, amit még nem néztél meg" jelentésű, és a bal hasáb **kövér
szedéssel** jeleníti meg.

Hogy a mennyiség is stimmel: 330 megjelölt album 2366-ból — ez reális arány
egy élő gyűjteményben, ahol a felhasználó nem nézett meg mindent.

*Bizonyítottsági fok: **megerősített** a mező léte, típusa, értékkészlete és
db3-beli regisztrációja. **Erős, de nem megerősített** az összekötés a kövér
szedéssel: a tulajdonos élő megfigyelése és a mező neve támasztja alá, de a
megjelenítő oldalt (melyik rajzoló olvassa) nem mértem. A `Praxis Semi
Bold/Heavy` betűkészlet több UI-függvényben jelen van (`0x0072efa0`,
`0x007ce960` és mások), de nincs bizonyítva, hogy EZ olvassa az `unread`-et.*

---

## A KÉZI (fogd-és-vidd) sorrend NEM a `.picasa.ini`-ben van — hol van?

A tulajdonos élő megfigyelése: *„amennyiben az indexképek sorrendjét
állítom, fogd és vidd egérrel, abban az esetben a Picasa ini nem változik, de
a megváltoztatott sorrend megmarad."*

### Amit KIZÁRTAM — mindegyik mért negatív eredmény

| hipotézis | mi döntötte el |
|---|---|
| a `.picasa.ini`-ben van | **a tulajdonos élő mérése**: a fájl nem változik |
| `Preferences\…` registry-kulcsban van | a `string_xrefs`-ben **nincs** rendezésre utaló `Preferences` kulcs — és ez érvényes negatívum, mert az **ellenpróba működik**: nyolc másik `Preferences\…` kulcsot (`HotFolders`, `Plugins\`, `RSSDownload`, `Buttons\Exclude`, `Buttons\UserConfig`, `AspectRatios`, `PrinterData`) a lekérdezés megtalál |
| külön PMP-oszlopban van | a valódi `Picasa2/db3/` **55 PMP-fájlja** végignézve — nincs `sort`/`order`/`position`/`rank` nevű oszlop |

### Ami MARAD

A sorrendnek a **db3-ban** kell lennie, PMP-oszlopon kívül. A legvalószínűbb
hordozó az **`albums.db`** (a `0x00415790`-ben a PMP-oszlopok mellett
regisztrált külön adatbázisfájl), ahol a sorrend **implicit** lehet: az album
tagsági listájának rekord-sorrendje. Másodlagos jelölt a `thumbindex.db`
(`0x004f2d90`, `0x004f46b0`, `0x004f54b0`).

**A következő konkrét lépés** (nem drága): a tulajdonos készít másolatot a
`db3` mappáról a sorrend átrendezése ELŐTT és UTÁN; a két állapot bináris
összevetése megmutatja, melyik fájl és melyik bájttartomány változott. Ez
eldönti a kérdést dekompiláció nélkül.

*Bizonyítottsági fok: **megerősített** a három kizárás; **feltételes** az
`albums.db` mint hordozó — jelöltként megnevezve, nem bizonyítva.*

### Kiegészítés (2026-08-27, este) — a `db3` KIMERÍTŐEN átnézve

A tulajdonos leadta az élő `db3`-at abban az állapotban, ahol egy képet
kézzel a 4. helyről a 2.-ra húzott. A sorrend **sehol nem található**:

| hol | mi döntötte el |
|---|---|
| `.picasa.ini` | a művelet után is 65 bájt, 19:33-as időbélyeg — érintetlen |
| **mind az 59 `imagedata_*` oszlop** | a négy képünk indexén (2899–2902) végigsöpörve: **egyetlen** oszlopban sincs négy megkülönböztető érték az `avgcolor`-on kívül (az a színátlag) |
| `albums_0.db` / `albums_index.db` | ez **gyorsítótár**, nem tagsági lista: az `albums_index.db` magicje `0x3FCCCCCD`, a 20+12 bájtos gyorsítótár-elrendezés — album-INDEXKÉPEKET tárol |
| `thumbindex.db` | névsorrendben tartja a négy fájlt (`…jpg`, `-001`, `-002`, `-003`) — katalógus, nem megjelenítési sorrend |
| `repository.dat` | mappa-útvonalak jegyzéke |
| `starlist.txt`, `scanlist.txt`, `saverlist.txt`, `tags.txt`, `facetags.txt` | csillagozás, beolvasási lista, mentési sor, címkék — sorrend egyikben sem |
| `Picasa2Albums/` | mindössze `watchedfolders.txt` + `frexcludefolders.txt` |
| `Preferences\…` registry | ellenpróbával igazolt negatívum (nyolc másik kulcsot ugyanaz a lekérdezés megtalál) |

A mappa a teljes `db3`-ban **három** helyen fordul elő:
`albumdata_filename.pmp`, `albumdata_name.pmp`, `thumbindex.db`.

### A binárisból: a kézi sorrend neve „PRIORITÁS"

Amiért a kulcsszavas keresés („sort", „order", „manual") nem talált: a Picasa
ezt **prioritásnak** hívja. A `0x0071c4f0` a rendezési állapotszöveget írja ki,
és hat módot ismer:

| kulcs | felirat (hivatalos magyar) |
|---|---|
| `CSelectionNode::SortDateA` | Rendezés hozzáférési dátum alapján |
| `CSelectionNode::SortDateC` | Rendezés létrehozási dátum alapján |
| `CSelectionNode::SortSize` | Rendezés méret alapján |
| `CSelectionNode::SortName` | Rendezés név alapján |
| `CSelectionNode::SortColor` | Rendezés szín alapján |
| **`CSelectionNode::SortPrior`** | **Rendezés prioritás szerint** |

⚠️ A `catdata_catpri` (kategória-prioritás) oszlop **létezik**, de az a
KATEGÓRIÁKÉ, nem a képeké. Kép-prioritás oszlop a db3 sémájában
(`0x00415790` teljes felsorolása) **nincs**.

### A kézi sorrend tárolási helye — MEGVÁLASZOLVA (2026-08-30)

A tulajdonos által végzett „előtte-utána" bináris összevetés (#1645) eldöntötte
a kérdést.

| helyszín | állapot | bizonyíték |
|---|---|---|
| `.picasa.ini` | **ELVETVE** | a fájl tartalma nem változik az átrendezéskor |
| PMP oszlop | **ELVETVE** | nincs `priority` vagy `sort` nevű oszlop a db3-ban |
| **`albums_0.db`** | **MEGERŐSÍTVE** | ez a fájl hordozza a legtöbb bináris változást |

**A működés elve:** a Picasa a manuális sorrendet nem a képek tulajdonságaként,
hanem az **album/mappa struktúra részeként** tárolja az `albums_0.db` fájlban.
Mivel minden mappa egyben egy albumként is szerepel az adatbázisban, a Picasa
ennek az albumnak a **tagsági listáját** (rekord-sorrendjét) módosítja, amikor
a felhasználó fogd-és-viddel átrendezi a képeket.

Ez a sorrend **lokális**, nem hordozható a `.picasa.ini`-vel, és a Picasa
bezárásakor (a pufferek ürítésekor) kerül kiírásra a `db3`-ba.

---


## A `db3` fájljainak ÉLETCIKLUSA: ki olvassa, ki írja, mikor (2026-08-27)

A tulajdonos kérdésére: *„A többi fájl lekutatását nem végzed el, mikor
olvasódnak vagy íródnak?"* — jogos, ez a „mit csinál az adattal" kérdés.

Az élő `db3` **84 fájlt** tartalmaz: **59 PMP-oszlop** és **25 egyéb**.

### 1. A perzisztencia-modell: BIZTONSÁGOS ÍRÁS két mappán át

A Picasa nem az élő adatbázisba ír közvetlenül. Három mappa van:

| mappa | szerep |
|---|---|
| `#db3\` | az **élő** adatbázis (23 függvény hivatkozik rá) |
| `#tmp\` | az **átmeneti** másolat, ide megy a kiírás |
| `#contacts\` | a névjegyek külön tárolója |

A kiíró (`0x0041ba40`) a `#tmp\`-be ír, majd visszamásol a `#db3\`-ba, és egy
**`_lock.lck`** fájllal jelöli az állapotot. Ha a visszamásolás elbukik, a
zárfájl bennmarad, és a benne lévő szöveg elmagyarázza, mi történt:

> *„The presence of this file indicates that the database has been persisted
> successfully but there was a failure copying these files back to the active
> db directory."*

Ez a minta a mi `ini/` sávunk „atomi írás" elvének a db3-beli megfelelője.

### 2. A kiírás HÁROMFÉLE módon indul

| kiváltó | cím | mit jelent |
|---|---|---|
| **kézi menüparancs** | `0x00577a60`, a parancskezelőből (`0x005cb990`) | végén üzenet: `IDS_DB_SAVED` = **„Adatbázis mentve"**; hibánál `IDS_PERSIST_ERR` |
| **tömörítéssel** | `0x0041b020` (`Always Compact`), `0x00403750` (`compactpercentage`) | a kiírás közben tömörít; a `compactpercentage` a küszöb |
| **aszinkron** | `AsynchronousPersist` beállítás (`0x0041ee10`) | a kiírás háttérszálon fut-e |

### 3. A betöltő verzió-migrációt is végez

A betöltő (`0x0041ee10`, hívója `0x00402f90`) három séma-verziókulcsot olvas
a `Preferences`-ből: **`gpsversion`**, **`colorspaceversion`**,
**`rawversion`**, továbbá a `FixShortPathNames` kapcsolót. Vagyis a db3-nak
**verziózott sémája** van, és a betöltés migrál.

### 4. Fájlonkénti leltár — olvasó, író, időzítés

| fájl | író | olvasó | mikor |
|---|---|---|---|
| `tags.txt` | `0x006c0e00` | `0x006c0f20` | a kiíró/betöltő hívja (perzisztencia) |
| `facetags.txt` | `0x006ba000` | `0x006ba160` | ua. |
| `starlist.txt` | `0x0041ba40`, `0x004a82d0` | — | a kiíróval együtt; teljes útvonalak soronként |
| `saverlist.txt` | `0x0041ba40`, `0x004a82d0`, `0x00531a20` | — | ua. |
| `scanlist.txt` | `0x004f61c0` (hívó `0x004f54b0`) | `0x004f6380` (hívó `0x004183c0`) | a beolvasás-kezelő; formátuma `+`/`-` előtagos meghajtólista |
| `repository.dat` | `0x00414100` (hívói `0x00415790`, `0x004a4c80`) | ua. | a **mappa-útvonalak jegyzéke**; a séma-regisztrálóból |
| `wordhash.dat` | `0x004db4f0` | **`0x004db720`** | a **keresési szóindex** (`.\thumblab\CIndexer.cpp`); az olvasó saját hibaüzenetekkel: *„wordhash.dat file: excess data"*, *„wordhash.dat: incorrect entity count"* |
| `usernames.dat` | `0x00415790` | ua. | a séma-regisztrálóból, a `m_usernameRepository`-hoz |

A `*_index.db` / `*_0.db` párok (thumbs, thumbs2, bigthumbs, previews,
albums, facetemplatesV2, profilephotos) **gyorsítótárak** — a
`0x3FCCCCCD` magic és a 20+12 bájtos index-elrendezés azonosítja őket.

### 5. Az `.ioq` írási sorok

A séma-regisztráló három írási sort is megnevez:
`ioqueue\slingshot.ioq`, `ioqueue\filesafe.ioq`, `ioqueue\albumsafe.ioq`.
Ezek a kiírás előtti pufferek. **Az élő `db3`-ban nem szerepeltek** — vagyis
a Picasa kilépéskor kiüríti őket.

### 6. ⚠️ Egy FÉLREFORDÍTÁS az eredeti magyar felületén

| kulcs | angol | hivatalos magyar | a helyes jelentés |
|---|---|---|---|
| `IDS_PERSIST_ERR` | `Error persisting: %d` | **„Fennálló hiba: %d"** | *„Hiba a mentés során: %d"* |

A fordító a **`persisting`** (kiírás/megőrzés) szót **`persistent`**-nek
(fennálló, tartós) olvasta. Ez a harmadik bizonyított félrefordítás a #620
kettője mellé. **Nálunk a helyes fordítást kell használni** — a felület
egyezésének elve a szó szerinti hibák átvételére nem terjed ki.

*Bizonyítottsági fok: **megerősített** minden cím és fájlnév-hozzárendelés
(bináris index `string_xrefs` + `xrefs`), valamint a két felirat
(`stringres-en-hu.tsv`). **Feltételes** a `starlist.txt`/`saverlist.txt`
irányának „csak író" jellege: olvasót nem találtam hozzájuk, de a negatív
eredményt nem ellenőriztem második lekérdezési alakkal.*

### A leltár utolsó négy fehér foltja — lezárva (2026-08-27)

A körben átadott 86 fájlból négyről nem volt egy szó sem a specekben:

| fájl | mi ez | bizonyíték |
|---|---|---|
| `albumdata_<fiók>_lh.pmp` | az album **online azonosítója** fiókonként. Az `lh` = **Lighthouse**, a Google online fotószolgáltatásának belső neve (`lighthouse://`, `lighthouse://album/%s`, `UploadToLighthouse::YesButton/CancelButton/DontWarn/NonJpegs`) | típus `0x04` (u64), 105 rekord |
| `imagedata_<fiók>_lhlist.pmp` | képenként az online albumok listája, ahova fel lett töltve | típus `0x00` (sztring), 2612 rekord |
| `facetemplatesV2_0.db` + `_index.db` | arcfelismerési sablonok gyorsítótára, **második formátumverzió** | a `0x004887c0` még a V1 neveket ismeri (`facetemplates_0.db`, `facetemplates_index.db`), a séma-regisztráló (`0x00415790`) már a `facetemplatesV2.db`-t — tehát **volt formátumváltás** |

⚠️ **A két `_lh` oszlop neve FIÓKFÜGGŐ**: a Google-fiók nevét tartalmazza
(`albumdata_<fiók>_lh`). Egy beolvasó nem keresheti fix néven — mintára kell
illesztenie (`albumdata_*_lh`, `imagedata_*_lhlist`).

Ezzel a **86-ból 86** fájl azonosítva van abban az értelemben, hogy tudjuk,
MI az. Az életciklusuk viszont nem egyformán feltárt — ld. a következő szakaszt.

### ⛔ AMI MÉG NINCS FELTÁRVA: a gyorsítótárak írási útja

A fenti életciklus-táblázat a **perzisztált** adatra érvényes (PMP-oszlopok,
szöveges listák): ezeket a kiíró `0x0041ba40` írja a `#tmp\`-n át, és a
betöltő `0x0041ee10` olvassa.

**A gyorsítótárakra ez NEM igaz**, és az ő írási útjuk nincs megmérve:

| fájl | mit tudunk | mit NEM |
|---|---|---|
| `thumbs_0.db` + `_index.db` | indexkép-gyorsítótár, `0x3FCCCCCD` magic, 20+12 elrendezés | ki írja, mikor, mi váltja ki az újragenerálást |
| `thumbs2_0.db` + `_index.db` | ua., második méret | ua. |
| `bigthumbs_0.db` + `_index.db` | ua., nagy méret | ua. |
| `previews_0.db` + `_index.db` | előnézetek (18,6 MB — a legnagyobb) | ua. |
| `albums_0.db` + `_index.db` | album-indexképek | ua. |
| `facetemplatesV2_0.db` + `_index.db` | arcsablonok | ua. |
| `profilephotos_0.db` | profilképek (4 bájt = üres) | ua. |
| `thumbindex.db` | **név**-katalógus (`0x40466666` magic), névsorrendben | ki írja és mikor |

Ez a szakasz MEGDŐLT — a mérés elkészült, ld. „A gyorsítótárak ÍRÁSI ÚTJA” alább. Jegy: **#1651**.

---

## A gyorsítótárak ÍRÁSI ÚTJA — megmérve (2026-08-27)

Az előző szakasz még azt írta, hogy ez nincs feltárva. **Most már van.**

### 1. A `thumbindex.db` INDULÁSKOR nyílik

A hívási lánc: a betöltő **`0x0041ee10`** → **`0x004f46b0`** → `0x004f2d90`.

- `0x004f46b0` beolvassa a **`ForceThumbUpdate`** beállítást a `Preferences`-ből
  (ez kényszeríti az indexképek újragenerálását), és a `UseTraceFile`-t;
- `0x004f2d90` kezeli a `thumbindex.db`-t és a **`thumbindex.tid`** kísérőfájlt.

Vagyis az indexkép-katalógus **nem külön eseményre**, hanem a db3 betöltésének
részeként nyílik és ellenőrződik — ugyanabban a lépésben, mint a séma-migráció.

### 2. A gyorsítótár-rekord MEZŐI — kiolvasva a diagnosztikából

A `0x004f25f0` egy diagnosztikai CSV-t tud írni (`WriteDirscannerCSV`
beállítás), és a fejléce **közvetlenül megadja a rekordszerkezetet**:

```
Name,Creation Time,Access Time,Size,Type,Dirty,Valid
"%s",%f,%f,%d,%d,%d,%d
```

| mező | szerep |
|---|---|
| `Name` | a fájl neve |
| `Creation Time`, `Access Time` | lebegőpontos időbélyegek |
| `Size`, `Type` | méret és típus |
| **`Dirty`** | **újra kell írni** |
| **`Valid`** | **érvényes-e még** |

⇒ **Az újragenerálást ez a két jelölő vezérli**, nem közvetlen
mtime-összevetés a rajzoláskor.

### 3. HÁROM pillanat, ahol a szkenner állapota kiíródik

Ugyanaz a függvény három külön fájlnevet ismer:

| fájl | mikor |
|---|---|
| `dirscanner-start.csv` | induláskor |
| `dirscanner-up.csv` | amikor a szkenner „feláll" |
| `dirscanner-shutdown.csv` | leálláskor |

Hívói: `0x004f46b0` (a betöltő útja), `0x004f54b0` (ugyanaz, ami a
`scanlist.txt`-t írja), `0x004e9b00` (`DirscanRegression` — **regressziós
tesztkeret** a szkennerhez).

### 4. A szkenner objektumcsaládja

| cím | név |
|---|---|
| `0x004e2f60` | `Dirscanner` |
| `0x004e9b00` | `DirscanRegression` |
| `0x006a8650` | `ytDirScannerWindows` (platformréteg) |

### 5. ⭐ REJTETT BELSŐ HTTP-SZERVER — eddig ismeretlen

A `0x004ca660` egy **HTTP-útvonaltáblát** tartalmaz, a `0x004c2af0` pedig egy
teljes HTML-oldalt szolgál ki („Picasa %s Debug"):

| útvonal | mire |
|---|---|
| `/albumlist`, `/album`, `/albumfeed` | albumlista és -tartalom |
| `/indexfeed`, `/globalfeed` | RSS-hírcsatornák |
| `/search`, `/msearch` | keresés |
| `/filesigs`, `/albumsigs` | fájl- és album-**aláírások** |
| **`/ge?BBOX=`** | **Google Earth** — befoglaló téglalap szerinti lekérdezés |

A hibakereső lap egy legördülővel a **három tábla** közt vált — `album`,
`file`, `cat` (azaz `albumdata`, `imagedata`, `catdata`) —, szűrőt kínál,
60 másodpercenként frissül, és a sorokban ott a **`Dirty`** oszlop. A képekre
mutató hivatkozás a saját `picasa://showimgtmp/?%d` protokollal nyílik. Van
benne sorkorlát is: *„Wrote maximum number of rows (not exploding your
browser)"*.

Ez magyarázza a `feed.rss` és a `View Online.url` fájlokat is
(`CLighthouseRSS`, `0x005ed650`).

*Bizonyítottsági fok: **megerősített** — minden cím, beállításnév,
útvonal és a CSV-fejléc a bináris index `string_xrefs`/`xrefs` tábláiból.
**Nincs megmérve**: a szerver portja és az, hogy mi kapcsolja be.*

### 5/b A rejtett HTTP-szerver RÉSZLETEI — port és bekapcsolók (2026-08-27)

#### Tizennégy útvonal (a `0x004ca660` táblájából, teljes)

| csoport | útvonalak |
|---|---|
| album | `/albumlist`, `/album`, `/albumfeed` |
| hírcsatorna | `/indexfeed`, `/globalfeed` |
| keresés | `/search`, `/msearch` |
| aláírások | `/filesigs`, `/albumsigs` |
| Google Earth | **`/ge?BBOX=`** |
| egyéb | `/tags`, `/decimate` |
| **hibakereső** | **`/albumdebug`**, **`/dbdebug`** |

#### Médiakiszolgálás — a képek is HTTP-n mennek

A `0x00533de0` három URL-mintát ismer:

```
http://localhost:%d/%s/thumb/%s.jpg
http://localhost:%d/%s/image/%s.jpg
http://localhost:%d/%s/original/%s
```

⇒ a szerver **indexképet, teljes képet és eredetit** is kiszolgál. Az alap
alak (`http://localhost:%d/%s/`) a `0x004cd010`-ben és a `0x0073bd40`-ben is ott van.

#### A kérés-kezelő és a biztonsági kapu (`0x004cbc60`)

| beállítás / szöveg | jelentés |
|---|---|
| **`AllowRemoteWeb`** | ha nincs bekapcsolva, a szerver **csak localhostot** szolgál ki: *„Not allowed, this server supports localhost only."* |
| **`DAVSupport`** | **WebDAV**-támogatás kapcsolója |
| **`EnableTester`** | engedélyezi a `POST /tester` végpontot |
| `WWW-Authenticate: Basic realm="Picasa"` · `Unauthorized` · `Please provide a valid password` | **HTTP Basic hitelesítés** — a szerver jelszót kérhet |
| `GET /favicon.ico` → `image/x-icon` | saját favicont szolgál ki |

Vagyis a Picasa egy **hitelesítéssel és WebDAV-val is rendelkező, hálózatra
kinyitható webszervert** hordoz — alapból localhostra zárva.

#### A PORT — nincs nevesített beállítása

Az összes URL-minta `%d`-t használ, tehát a port **futásidejű érték**. A
`Preferences` kulcsok közt **nincs** port-nevű bejegyzés.

⚠️ Ez **érvényes negatívum**: a nevesített kulcsok megtalálhatók ugyanezzel a
lekérdezéssel (`compactpercentage`, `FRSortThreshold`, `AllowRemoteWeb`,
`DAVSupport`, `EnableTester`), tehát ha lenne `WebPort`-féle kulcs, kijönne.

**Amit ebből NEM szabad következtetni:** hogy nincs port-beállítás. A #1409
tanulsága szerint *konstans hiányából soha ne következtess funkció hiányára* —
az érték lehet **számliterál a kódban** (a sztringtárban láthatatlan), vagy a
rendszertől kért **szabad port** (bind 0-ra). A kettő közti döntéshez a
figyelő felállításának diszasszemblálása kell.

*Bizonyítottsági fok: **megerősített** a tizennégy útvonal, a három
kapcsoló, a Basic hitelesítés és a localhost-korlát. **Nyitva**: a port
konkrét eredete.*

#### A PORT — DISSZASSZEMBLÁLVA (`0x00a5b180`)

Az osztály neve **`CLocalServer`** (RTTI: `CLocalServer::vftable`
`0x00c85814`, metódusa a már ismert kérés-kezelő `0x004cbc60`).

A figyelő felállítása ordinál szerint importált WS2_32-hívásokkal megy
(`Ordinal_2` = `bind`, `Ordinal_13` = `listen`, `Ordinal_9` = `htons`):

```asm
push 0 ; push 1 ; push 2      ; socket(AF_INET=2, SOCK_STREAM=1, 0)
call 0xc06e60
mov  [esi+0x50], eax          ; a socket

lea  edi, [esi+0x64]          ; sockaddr_in
mov  word ptr [edi], 2        ; sin_family = AF_INET
mov  eax, [esi+0x58]          ; a CÍM tagváltozóból
call 0xc06e54                 ; inet_addr / htonl
mov  [esi+0x68], eax          ; sin_addr

movzx ecx, word ptr [esi+0x54]; ⭐ a PORT: 16 bites tagváltozó
call 0xc06e4e                 ; htons()
mov  word ptr [esi+0x66], ax  ; sin_port

push 0x10 ; push edi ; push edx
call 0xc06e72                 ; bind()
test eax, eax
jge  siker
    cmp dword ptr [esi+0x54], 0
    je  hiba                  ; ha MÁR 0 volt → tényleges hiba, -1
    mov dword ptr [esi+0x54], 0   ; ⭐ különben NULLÁZZA a portot
    jmp [vtbl+0x28]               ;    és ÚJRAPRÓBÁLJA
siker:
push 5 ; push eax
call 0xc06e96                 ; listen(sock, backlog=5)
```

**A válasz tehát: nincs rögzített port.** A `CLocalServer` egy preferált
értékkel próbál kötni; ha az foglalt, **nullára állítja a portot és
újrapróbálja** — a 0 a Windows-nak azt jelenti, hogy *adj egy szabad
efemer portot*. Ezért használ **minden** URL-minta `%d`-t a binárisban: a
port futásidőben dől el, statikusan nem is tudható.

További rögzített tények: a figyelési sor hossza **5**; a kötési cím külön
tagváltozóból (`+0x58`) jön, tehát a `localhost`-ra kötés is adat, nem
beégetett érték — ez illeszkedik az `AllowRemoteWeb` kapcsolóhoz.

**Amit korábban NYITVA maradt — LEZÁRVA (2026-08-30): nincs „preferált
kezdőérték".** A `0x004c0d10` / `0x004c0db0` konstruktor **a `+0x54`-et
egyszer sem írja** — a Start (`0x00a5b180`) a `+0x54` mezőt olvassa
(`movzx ecx, word ptr [esi+0x54]`), ami a `0xbf37c0` mamorícentemzés után
**0**. A `bind(0)` a Windows rendszer-szabad portot oszt ki ⇒ a szerver
**minden indításkor a rendszer egy efemer portján áll**; a `%d`-t használó
URL-minták (a `0x004cd010` `http://localhost:%d/%s/` stb.) a ténylegesen
kapott portot szövik az ÚJRA; az „ha foglalt, nullázd és újrapróbálkozz"
ág (`0x00a5b1eb`) gyakorlatilag sosem fut, mert a `%d` porton nincs fix
kedvenc. **Statikusan nincs kézzel beállítható port-bemenet** — a
felhasználónak semmilyen UI-vezérlő nem állíthatja; a
`AllowRemoteWeb` csak a cím-korlátot oldja, a portot nem.

A projekt módszertani óvása („a struktúra-offszet alapú nyom félrevezet")
itt is igaz volt: a `+0x54` mezőt a konstruktorok **szándékosan nem**
inicializálják, mert a rendszer-tényleges-port a cél.

*Bizonyítottsági fok: **megerősített** a teljes felállítási sorrend, a
tartalék-ág, a backlog (a diszasszemblált kódból) és a „nincs preferált
kezdőérték" lezárás (a `0x004c0d10`/`0x004c0db0` konstruktorok
diszasszemblálásából: a `+0x54`-et egyik sem írja, az efemer).*

---

## Az ÖTÖDIK bélyegkép-tár: `albums.db` — a mappák/albumok BORÍTÓJA (2026-09-02)

A lap eddig **négy** bélyegkép-szintet ismert (72 / 144 / 288 / 640 px). Van
egy **ötödik** tár, más céllal és **más formátummal**: az `albums.db` a
mappa-/album-**borítókat** tárolja — azokat a kis képkupacokat, amiket a
bal hasáb fastruktúrája és a tálca „Kiválasztott mappa" tokenje mutat.

A tulajdonos képernyőképe (2026-09-02, futó Picasa 3) mutatja: a
`Mappák` fa több során **nem a sárga mappaikon**, hanem egy pici fotó
látszik; ugyanez a tálcán a „Kiválasztott mappa – 82 fotó" token mellett.

### 1. Hol van a rendszerben

A tár-nevek felsorolása egyetlen függvényben (`0x00415790`) áll, és az
`albums.db` **együtt szerepel** a másik néggyel:

```
thumbs.db · thumbs2.db · bigthumbs.db · previews.db · albums.db · facetemplatesV2.db
m_thumbs  · m_pinkyThumbs · m_bigThumbs · m_previewThumbs · m_albumThumbs · m_facetemplates
```

A kapcsolója: **`Preferences\ShowAlbumThumbnails2`** — a Nézet menü
„Indexképek megjelenítése a könyvtárban" pipája (`0x9cd7`), alapérték **0**.
Ld. [`picasa-konyvtar-eszkoztar-viselkedes.md`](picasa-konyvtar-eszkoztar-viselkedes.md)
4/c. A listaépítő (`0x00761870`) ugyanitt olvassa be induláskor, és ugyanez a
függvény sorolja fel a helyettesítő ikonokat (`icons/folder`, `icons/album`,
`icons/smartalbum`, …) arra az esetre, amikor nincs borító.

### 2. A FORMÁTUM — NEM JPEG, hanem nyers raszter

Az `albums_index.db` a szokásos blokkfájl-index (ld. az `*_index.db`
szakaszt), de a hozzá tartozó **blokkok nem JPEG-ek**:

```
+0   uint32  width
+4   uint32  height
+8   width * height * 4 bájt   — 32 bites képpontok, BGRA sorrendben
```

**Mérés:** a `Picasa2-arcok` adatbázis `albums_index.db`-jében **37 élő
bejegyzés** van, és a `8 + width*height*4 == hossz` azonosság **37/37**
esetben teljesül. JPEG-kezdet (`FFD8`) **0/37**.

A méret **változó és aránytartó**: a leghosszabb oldal a 37 mintában
**72–119** képpont (a leggyakoribb 72: 9 db). Az alfa-csatorna **valódi
átlátszóságot hordoz** (mintánként 1 400–2 200 teljesen átlátszó képpont) —
a borító tehát nem téglalap, hanem egy **kivágott alakzat**.

### 3. Mit ÁBRÁZOL — nem egy fotó, hanem KUPAC

A borítókat kirenderelve (nyers BGRA → PNG, méretezés nélkül) jól látszik:
**egy elülső fotó, mögötte 1–3 további, felfelé-balra kifordítva**, mint egy
kis képhalom. Az átlátszó szél a halom kontúrja.

⇒ **A „mappaikon = a legrégebbi kép mini változata" feltevés MEGDŐLT.** A
borító **összeállított kép**, több fotóból.

*Bizonyítottsági fok: **megerősített** a formátumra (37/37 méret-azonosság)
és arra, hogy összeállított kupac (kirenderelt minták).*

### 4. A borító a MAPPÁHOZ tartozik — az albumtábla során át

Az `albums_index.db` **rés-indexe az `albumdata` tábla sorindexe**, és a
Picasa modelljében a lemezen lévő mappák is albumként szerepelnek. Élő
példa ugyanabból az adatbázisból (a `albumdata_name` / `_token` /
`_filename` oszlopokból):

| rés | név | token | fájl |
|---:|---|---|---|
| 4 | `wallpapers` | `]album:8b6dd1f0…` | `…\Képek\wallpapers\` |
| 5 | `space` | `]album:654529b2…` | `…\Képek\wallpapers\space\` |
| 13 | `volt` | `]album:83439121…` | `…\Képek\AI\volt\` |
| 2 | `Név nélküliek` | `]unknownface` | *(nincs)* |

⇒ A borító **mappánként egy**, és a gyűjtemény-jellegű sorok (pl.
`]unknownface`) is kapnak egyet.

### 5. MELYIK fotókból áll a kupac — MEGVÁLASZOLVA a 7. szakaszban

> ⚠️ **Ez a szakasz korábban azt írta, hogy a kérdés nincs megmérve.**
> A 2026-09-02-i folytatás (6.4 és 7.) végigolvasta a `0x00423500`
> előállítót és a `0x00423780` összeállítót, és megválaszolta. A régi
> szöveget azért hagyjuk itt átfogalmazva, mert a **kudarcba fulladt
> módszer tanulsága** önmagában is érték.

**A válasz:** a kupacba az album SAJÁT elemlistájának első `min(N, 4)`
eleme kerül, és a lista **első** eleme kerül legfelülre. Nem a
legrégebbi, nem a legújabb, nem a csillagozott — a **lista eleje**. A
részletes levezetés, a geometria és az árnyék a **7. szakaszban** áll.

#### Amit előbb megpróbáltunk, és miért NEM döntött

A saját `2025-05-xx` tesztmappánk borítóját (72×114) kirendereltük, az
elülső lap dobozát az alfa-maszkból kivágtuk (49×92, arány 0,533), és
képaláírás-mentes képjel-összevetéssel kerestük a mappa 241 fájlja
között. A legjobb két találat **0,96 és 1,03** hibaértékkel jött —
**nem különül el**, mert a kivágott doboz a mögöttes lapokból is
tartalmaz sávot.

**A tanulság:** a kép-oldali visszafejtés itt elvi korlátba ütközött, a
kód-oldali viszont egyértelmű választ adott. Hasonló kérdésnél érdemes
előbb az előállító függvényt megkeresni, és csak utána mérni a
kimeneten.

### 6. A borító ÉLETCIKLUSA — hol van a kód (2026-09-02, folytatás)

Az előző menet nyitva hagyta, hogy **melyik fotókból** áll a kupac. Ez a
szakasz nem válaszolja meg, de a keresést **egyetlen függvényre szűkíti**, és
közben három új dolgot mér ki.

#### 6.1 A tár a `CThumbDB` `+0x2428` tagja

A hat blokkfájlt egyetlen ciklusszerű részlet nyitja meg a konstruktorban
(`0x00415790`), tagonként `lea edi, [ebp+OFF]; push <fájlnév>; call 0x6b5d40`:

| tag-eltolás | fájl |
|---|---|
| `+0x2178` | `0x00c80dcc` |
| `+0x2224` | `0x00c80dd8` |
| `+0x22d0` | `0x00c80de4` |
| `+0x237c` | `0x00c80df4` |
| **`+0x2428`** | **`albums.db`** (`0x00c80e00`) |

(`0x00415aab`–`0x00415af1`.) A `m_albumThumbs` név ugyanerre a tagra
hivatkozik (`0x00416c4a` + `0x00416c64`).

#### 6.2 A tárat ÉRINTŐ függvények — pontosan tizenöt

A `+0x2428` eltolásra a teljes `.text`-ben **15 függvény** hivatkozik
(nyers bájtkeresés a `0x00002428` konstansra, függvényhatárokhoz rendelve):

| cím | méret | szerep |
|---|---:|---|
| `0x00415790` | 7851 | a hat tár megnyitása (konstruktor) |
| `0x004181b0` | 212 | **bulk** művelet mindegyik táron (`[+0x18]` virtuális) |
| `0x00418290` | 213 | **bulk** művelet mindegyik táron (`[+0x1c]` virtuális) |
| **`0x00423300`** | **505** | **a borító LEKÉRÉSE — „megvan és friss?"** |
| **`0x00423500`** | **632** | ⭐ **a borító ELŐÁLLÍTÁSA** |
| `0x00417770` · `0x0044d540` · `0x004844f0` · `0x00423500` | | további belső hívók |
| `0x00763150` | 11169 | **fogyasztó**: az albumlista rajzolása (`CAlbumList`) |
| `0x0064ae90` | 3278 | fogyasztó: a Személyek panel |
| `0x0074ad40` | 3938 | fogyasztó: az albumfejléc |
| `0x00419d10` · `0x00561840` · `0x00603510` · `0x00603660` | | személy-album ágak |

#### 6.3 ⭐ A gyorstár ÉRVÉNYESSÉGE — és ami ezzel bebizonyosodott

A `0x00423300` menete:

```asm
0x00423481  call 0x6c9d60              ; -> BÉLYEG kiszámítása az albumból
0x00423486  mov ecx, [ebx+0x2490]
0x0042348c  shr ecx, 1                 ; a tár rés-száma
0x0042348e  cmp ecx, esi               ; az album sorindexe belefér-e?
0x00423494  jbe 0x4234d8               ;   nem -> ÚJRAÉPÍTÉS
0x00423496  lea edi, [ebx+0x2428]      ; az album-tár
0x0042349f  call 0x6b66c0              ; -> a sloton TÁROLT kulcs
0x004234a4  cmp eax, [esp+0x10]        ; egyezik a bélyeggel?
0x004234a8  jne 0x4234d8               ;   nem -> ÚJRAÉPÍTÉS
0x004234b0  call 0x4114e0              ;   igen -> a gyorstárazott blob KIOLVASÁSA
…
0x004234de  call 0x423500              ; ÚJRAÉPÍTÉS
```

⇒ **Az `*_index.db` első vektora („kulcs") ÉRVÉNYESSÉGI BÉLYEG.** Ezt a
2026-09-02-i blokkfájl-kör **mérésből** már kimondta (a `thumbs` és a
`thumbs2` kulcsvektora bitre azonos, noha a blobjuk más) — most megvan a
**kód**, ami össze is hasonlítja. A két bizonyíték egymástól független.

Melléklelet: a tár **rés-száma** a `+0x2490` mezőben áll, `>>1`
kódolással — ugyanaz az „elemszám kétszerese" idióma, mint a
`CSelectionNode`-nál.

#### 6.4 A válogatás — MEGVÁLASZOLVA (2026-09-02)

A korábbi kiadás itt még nyitott kérdést jelölt („melyik fotókból áll a
kupac, és milyen sorrendben?"). **A `0x00423500` és a belőle hívott
`0x00423780` végigolvasva megválaszolta.** A teljes algoritmus a **7.
szakaszban** áll; röviden:

- a `0x00423500` a **saját elemlistát** kéri le az albumtól
  (`[[this+0x48]] +0x2c` virtuális hívás, `0x00423521`–`0x00423538`), majd
  ezt a listát adja át a **`0x00423780`** összeállítónak (`0x004236ef`);
- a `0x00423780` a lista **első legfeljebb NÉGY** elemét használja;
- a kupac hátulról előre rajzolódik, tehát a lista **első** eleme kerül
  legfelülre.

Ami eredményül visszajön, azt a `0x004236fa`–`0x00423715` írja be a
gyorstárba: bélyeget számol (`0x6c9d60`), és a `+0x2428` tárba menti
(`0x4115c0`).

---

## 7. A BORÍTÓ ÖSSZEÁLLÍTÁSA — a fotó-kupac teljes algoritmusa (2026-09-02)

> **Bizonyítottság: megerősített.** Minden szám a `Picasa3.exe`
> diszasszemblátumából van kiolvasva (cím + konstanscím), a lágy árnyék
> létét és lefutását pedig **élő adaton** mértük (37 valódi borító a
> `research/testdata/Picasa2-arcok/Picasa2/db3/albums_0.db`-ből).
> Az összeállító: **`0x00423780`**, 2167 bájt.

### 7.1 Bemenet és a fotók KIVÁLASZTÁSA

A `0x00423500` az albumtól lekéri az elemlistát, és azt adja át
paraméterként. A lista a szokásos „tömb + elemszám kétszerese" idióma:

| mező | jelentés | cím |
|---|---|---|
| `[lista+0]` | mutató az elemtömbre | `0x0042385a` |
| `[lista+4] >> 1` | elemszám (`N`) | `0x00423784`, `0x0042378d` |

```asm
0x00423784  mov eax, [eax+4]
0x0042378d  shr eax, 1            ; N
0x00423793  jne 0x4237a7          ; N == 0  ->  4-es hibakóddal kilép
0x004237ab  cmp eax, 4
0x004237be  ja  0x4237c4          ; N > 4   ->  marad a 4
0x004237c0  mov [esp+0x1c], eax   ; különben N
```

⇒ **A kupacba a lista első `min(N, 4)` eleme kerül** — nem véletlen
válogatás, nem a legrégebbi, nem a legújabb: a lista **eleje**, a
`[tömb + i*4]` indexeléssel (`0x0042385c`), `i = 0 … min(N,4)-1`.

> ⛔ **Ezzel a „a legrégebbi képből csinál mini ikont" feltevés MEGDŐLT.**
> A kiválasztás sorrend-alapú, nem dátum-alapú. Hogy az albumtól visszakapott
> lista maga milyen rendezésben áll, azt a `[[album+0x48]] +0x2c` virtuális
> metódus dönti el — az a mappanézet saját rendezése.

### 7.2 A rajzolási SORREND — az első fotó kerül felülre

A rajzoló ciklus **visszafelé** megy:

```asm
0x00423a71  add ebx, -1           ; ebx = N-1 -tól indul
0x00423f45  sub ebx, 1
0x00423f4b  cmp ebx, edi          ; edi = 0
0x00423f4d  jge 0x423aae          ; ... 0-ig
```

⇒ az `N-1` indexű fotó rajzolódik **először** (a kupac alja), a `0`
indexű **utoljára** (a kupac teteje).

### 7.3 A szórás DETERMINISZTIKUS — albumonként ugyanaz

A vetemítés véletlenszerűnek látszik, de **nem az**: a magot az album
tárolóbeli **rés-indexe** adja.

```asm
0x00423a24  mov eax, [esp+0x144]  ; a 0x00423500 2. paramétere = a rés indexe
0x00423a2b  xor eax, 0x133475
0x00423a6c  call 0xc08214         ; srand(mag)
```

A `0x00c08214` = **`srand`** (a magot a `[CRT+0x14]` mezőbe írja), a
`0x00c08221` = **`rand`** — a klasszikus MSVCRT-generátor, kódból
kiolvasva:

```asm
0x00c08229  imul ecx, ecx, 0x343fd
0x00c0822f  add  ecx, 0x269ec3
0x00c0823a  shr  eax, 0x10
0x00c0823d  and  eax, 0x7fff
```

⇒ `seed = seed*0x343FD + 0x269EC3`, a visszaadott érték
`(seed >> 16) & 0x7FFF`.

**A `rand()` kimenetéből `[1,2)` intervallumú lebegőpontos szám lesz** — a
klasszikus kitevő-trükkel, három helyen azonos alakban
(`0x00423bb0`, `0x00423c56`, `0x00423c67`):

```asm
call rand                 ; 0 … 0x7FFF
add  eax, 0x3f8000
shl  eax, 8               ; 0x3F800000 … 0x3FFFFF00  ->  float32: 1.0 … 1.99998
```

**A függvény KÉTSZER járja végig a fotókat**, és a `srand`-ot mindkét
menet elején ugyanazzal a maggal hívja meg (`0x00423a6c`), tehát a két
menet **azonos elrendezést** számol:

| menet | `[esp+0x1c]` | mit csinál |
|---|---|---|
| 0. | 0 | végigméri a befoglaló téglalapot (min/max: `[esp+0x28…0x34]`) |
| 1. | 1 | ténylegesen rajzol a kiszámolt vászonra |

A menetszámláló a `0x00423fb7`–`0x00423fc5`-ön nő (`cmp eax, 2`), a vászon
a 0. menet végén jön létre a befoglaló méretével:

```asm
0x00423f70  sub edx, esi          ; szélesség = maxX - minX
0x00423f72  sub ecx, edi          ; magasság  = maxY - minY
0x00423f75  call 0x9a9c90         ; vászon létrehozása
```

⇒ **a borító mérete nem rögzített** — a kupac befoglaló téglalapja.
(Élő adat: 37 valódi borító, leghosszabb oldal **72–119 képpont**.)

### 7.4 Fotónkénti geometria — a pontos képletek

Jelölés: `i` = a fotó indexe (`0` = legfelső), `w`, `h` = a bélyegkép
mérete, `r₁, r₂, r₃` = a három `rand()`-ból képzett `[1,2)` szám.

| mennyiség | képlet | hol | konstans |
|---|---|---|---|
| középpont | a fotó a `(72, 72)` pontra kerül: eltolás `72 − w/2`, `72 − h/2` | `0x00423b00`–`0x00423b1d` | `72.0` = `0xcf3f90`, `0.5` = `0xc72150` |
| **forgatás** | `α = 0.2 · (r₁ − 1.5)` ⇒ **`α ∈ [−0.1, +0.1) radián = ±5,7296°`** | `0x00423bc5`, `0x00423bd3`, `0x00423bd9` | `1.0` = `0xc7e328`, `0.5` = `0xc72150`, `0.2` = `0xcf4748` |
| **x-eltolás** | `uₓ = 2(r₂ − 1) − 1 ∈ [−1, 1)`, majd `tₓ = 4 · i · uₓ` | `0x00423c98`–`0x00423cd8` | `2.0` = `0xc7d9d0` |
| **y-eltolás** | `t_y = −i · (4·r₃ + 1)`, `r₃ ∈ [1,2)` ⇒ **`t_y ∈ (−9i, −5i]`** | `0x00423cfc`–`0x00423d36` | `−2.0` = `0xcf3b80` |

Következmények, amelyek a képen is látszanak:

1. **A legfelső fotó (`i = 0`) eltolás nélkül, pontosan középen áll** —
   `4·0·uₓ = 0` és `−0·(…) = 0`.
2. Minden további fotó **indexarányosan** csúszik: oldalra legfeljebb
   `±4i` képpont, függőlegesen `5i…9i` képpont **egy irányba** (a
   képlet előjele nem vált) — ezért látszik „lefelé kifutó" kupacnak.
3. **A legalsó fotó (`i = N−1`) NEM kap forgatást.** A forgatás-ág át van
   ugorva rá:

   ```asm
   0x00423ba6  cmp [esp+0x70], ecx   ; (i+1) : N
   0x00423baa  jge 0x423c56          ; i == N-1  ->  a forgatás KIMARAD
   ```

   ⚠️ Ez a `rand()`-sorozatot is eltolja: a legalsó fotóra **két**
   hívás jut, a többire **három**. Bitre pontos újraalkotáskor ez
   számít.

A forgatásmátrix `[cos, −sin, tₓ; sin, cos, t_y; 0, 0, 1]` alakban áll
össze (`0x00423c18`–`0x00423c4d`); a `0x00c29d20` = **`cos`**, a
`0x00c285f0` = **`sin`** (mindkettő a CRT SSE2-elágazó burkolója). Az
egyes részmátrixokat a `0x009e6340` fűzi az addigi transzformációhoz.

> A `72`-es középpont a **munkavászon** origója, nem a kimeneti méret: a
> vászon utólag a befoglaló téglalapra szűkül (7.3), és egy MINDEN fotóra
> azonos eltolás a `max − min` különbségből kiesik. **Bizonyítottság:
> erős** (levezetés, nem külön mérés).

### 7.5 A lágy árnyék — kódból ÉS mérésből

Minden bélyegkép a `0x009a97a0` rajzolón megy át, két lebegőpontos
paraméterrel (`0x00423898`–`0x004238bf`):

```asm
fld dword [0xc7e304]   ; 0.6f
fld dword [0xcf3a58]   ; 5.0f
call 0x9a97a0          ; (kép, 5.0f, 0.6f, 1, 1)
```

A `0x009a97a0` ezeket a `0x00a6e2f0`-nak adja tovább, ami **elárulja a
jelentésüket**:

```asm
0x00a6e2f5  fld   dword [esp+0x18]    ; 0.6
0x00a6e2f9  fmul  qword [0xcf39d0]    ; * 255.0
0x00a6e326  fistp qword [esp+4]
0x00a6e32e  mov   [ecx+4], eax        ; = 153  -> ÁTLÁTSZATLANSÁG (alfa)
0x00a6e337  fld   dword [esp+0x10]    ; 5.0
0x00a6e33b  fstp  dword [ecx+0xc]     ; -> SUGÁR (float, képpont)
```

| paraméter | érték | jelentés | bizonyíték |
|---|---|---|---|
| `0xc7e304` | `0.6f` | árnyék-átlátszatlanság ⇒ **alfa = 153** | `0.6 × 255.0` (`0xcf39d0`) egészre kerekítve, `0x00a6e32e` |
| `0xcf3a58` | `5.0f` | árnyék-**sugár képpontban** | `0x00a6e33b`, és lásd a mérést alább |

**Mérés élő adaton** (37 borító, 288 091 képpont):

- a képpontok **32,2%-a részlegesen átlátszó** (`0 < α < 255`) — ez
  élsimítással nem magyarázható, csak lágy árnyékkal;
- ezek **59%-a feketés** (`max(R,G,B) ≤ 16`) = maga az árnyék, a maradék
  a fotók elsimított, elforgatott éle;
- az alfa-lefutás **egy-egy fotó szélénél kb. 5 képpont széles** —
  például a 3. rés `y=59` sorában balról:
  `0 0 0 1 5 14 35 64 | 210 254 …`, a 7. rés `y=53` sorában
  `0 0 0 0 0 5 22 50 89 | 185 255 …`.
  **Ez független megerősítése az `5.0`-nak.**

⚠️ **Amit NEM tudtunk megmérni:** az árnyék *csúcs*-alfáját (153),
mert a látható árnyék mindig csak a lefutó pereme — a belseje a fotó alatt
van. Az 153 tehát **kódból** van, nem mérésből; a kettő nem mond ellent
egymásnak. A mérőszkript egyszeri, a `research/testdata/` alatti mintákon
bármikor megismételhető.

### 7.6 Amit KIZÁRTUNK

| hipotézis | mi döntötte el |
|---|---|
| „a borító a legrégebbi képből készül" | a válogatás **indexalapú** (`[tömb + i*4]`, `i = 0…3`), dátumot nem olvas — `0x0042385c` |
| „a kupac elrendezése futásonként változik" | `srand(rés ^ 0x133475)` — **albumonként rögzített**, `0x00423a2b` |
| „a borító mérete rögzített (pl. 144×144)" | a vászon a befoglaló téglalap, `0x00423f70`–`0x00423f75`; élő adat: 72–119 képpont |
| „a 32%-nyi félig átlátszó képpont élsimítás" | az alfa-hisztogram egyenletesen lefutó, és a félig átlátszók 59%-a feketés — lágy árnyék |

---

## 8. A `thumbindex.db` és a `*_index.db` BÁJTSZINTŰ formátuma — megfejtve (2026-09-03)

A lap eddig annyit mondott, hogy a `thumbindex.db` „az útvonal-index", és
hogy a slot indexe azonos a PMP-sorindexszel. A **formátumát** nem írta le.
Most igen — és mindkettő **maradék nélkül** kiparszolható.

> ⚠️ **Adatvédelem:** az alábbi számok a tulajdonos valódi katalógusából
> származnak. Konkrét útvonalat, fájlnevet ez a lap **nem** tartalmaz, és
> nem is szabad ide másolni.

### 8.1 `thumbindex.db` — az útvonal-index

```
+0   uint32   magic = 0x40466666      ("ffF@" ASCII-ként)
+4   uint32   rekordszám (N)
+8   N × rekord:
        ASCIIZ  útvonal (változó hosszú, NUL-lezárt)
        +0   uint64  FILETIME — létrehozás
        +8   uint64  FILETIME — hozzáférés
        +16  uint32  méret bájtban
        +20  uint32  típus
        +24  uint8   „dirty"
        +25  uint8   „valid"
        +26  uint32  kiegészítő mező (mappánál 0xFFFFFFFF)
        ⇒ a farok pontosan 30 bájt
```

⭐ **A hét mező PONTOSAN a 2. szakasz diagnosztikai CSV-fejléce:**
`Name, Creation Time, Access Time, Size, Type, Dirty, Valid`. Vagyis a
`WriteDirscannerCSV` kimenete **ugyanennek a rekordnak** a szöveges
kiírása — a bináris rekord és a CSV egy és ugyanaz a szerkezet.

**A `típus` mért értékkészlete:** `5` és `1` = könyvtár, `2` = fájl.
*(A `0xFFFFFFFF` kiegészítő mező mappáknál állandó; fájloknál kis egész.)*

**Ellenőrzés:** a tulajdonos katalógusán a fejléc **140 758** rekordot
ígér, és a parser pontosan ennyit olvas ki — **0 bájt maradékkal**. A
kiterjesztés-eloszlás értelmes (119 483 `jpg`, 7 697 `png`, 7 664
könyvtár, 2 108 `jpeg`, 1 770 `mp4`).

### 8.2 `*_index.db` — NÉGY párhuzamos tömb (HELYESBÍTVE 2026-09-03)

> ⚠️ **Ez a szakasz helyesbíti önmagát.** A lap első, ugyanaznapi kiadása
> „20 bájt fejléc + N × 12 bájtos rekord (`uint64 q` + `uint32 u`)"-t írt le.
> **A szerkezet téves volt.** A két modell **bitre ugyanazt a fájlméretet**
> adja — `20 + 12N` —, ezért a méret-ellenőrzés nem tudta megkülönböztetni
> őket. Az alábbi leírás a bináris ÍRÓ KÓDJÁBÓL jön, nem méret-illesztésből.

#### Az író

A tár-osztály másodlagos vtáblájának (`0x00ca84e8`) **1. rekesze**:
`0x006b7fc0` (786 b). A tár-objektumot a `0x00415ab6` hívás építi
(`0x006b5d40`, 146 b), amely `[edi] = 0x00ca84bc` és `[edi+0x48] =
0x00ca84e8` vtáblákat állítja be.

| cím | mit tesz |
|---|---|
| `0x006b8071` | `fld dword ptr [0x00d678e0]` — a verzió-float betöltése |
| `0x006b807f` | `edi = 0x00c85ef8` → a `"wbS"` fopen-mód sztringje |
| `0x006b8088` | `call 0x009917f0` — fájlmegnyitás írásra |
| `0x006b80a2` | `fwrite(puffer, 4, 1, f)` — **a 4 bájtos verzió** |
| `0x006b81ae` | `call 0x0099c1e0` a `[esi+0x0c]` tárolóra |
| `0x006b81c4` | `call 0x0099c1e0` a `[esi+0x14]` tárolóra |
| `0x006b81de` | `call 0x0099c1e0` a `[esi+0x1c]` tárolóra |
| `0x006b81fc` | `call [[ebx]+0x20]` — a **leszármazott** saját tömbje |

A verzió-float forrása globális: `0x004056c9`-nél
`fld dword ptr [0x00cf50b8]` / `fstp dword ptr [0x00d678e0]`, ahol
`[0x00cf50b8] = 0x3fcccccd` = **1.6**. Ez a konstans a teljes binárisban
**kétszer** fordul elő, és a globálisnak **kilenc** olvasója van — az egyik
épp a `0x006b8073`, azaz ez a metódus.

A tároló-író `0x0099c1e0` (91 b) mindössze ennyit tesz:

| cím | mit tesz |
|---|---|
| `0x0099c1eb` | `esi = [edi+4] >> 1` — **az elemszám** |
| `0x0099c1fd` | `fwrite(&esi, 4, 1, f)` — a darabszám kiírása |
| `0x0099c228` | `fwrite([edi], 4, esi, f)` — `esi` darab **4 bájtos** elem |

⇒ Nincs 12 bájtos rekord. **Négy, egymás után kiírt `uint32`-tömb van,
mindegyik előtt a saját darabszáma.**

#### A formátum

```
+0        float32   verzió           ; a 0x00d678e0 globálból, minden mintában 1.6
          uint32    n0               ; 0. tömb elemszáma — MINDEN mintában 0
          uint32    n1 = N           ; slotszám
          N × uint32   kulcs         ; forrás-azonosító bélyeg (ld. 8.5)
          uint32    n2 = N
          N × uint32   eltolás       ; bájteltolás a <név>_0.db adatfájlban
          uint32    n3 = N
          N × uint32   hossz         ; a blob hossza bájtban; 0 = üres slot
```

#### Az ellenőrzés, ami a méret-egyezésnél erősebb

A **legutolsó `eltolás + hossz`** értéknek meg kell egyeznie a hozzá tartozó
`<név>_0.db` adatfájl méretével. Három független katalóguson:

| index | slot | foglalt | utolsó vég | az adatfájl mérete | egyezik |
|---|---:|---:|---:|---:|:--:|
| `albums_index.db` | 144 | 37 | 1 328 872 | 1 328 872 | ✅ |
| `thumbs_index.db` | 3 338 | 3 204 | 15 071 085 | 15 071 085 | ✅ |
| `thumbs2_index.db` | 140 755 | 133 454 | 279 202 618 | 279 202 618 | ✅ |

Mindhárom fájl **0 bájt maradékkal** parszolható a fenti modellel.
A blobok többsége hézagmentesen követi egymást (`thumbs2`: 128 444 /
133 453 szomszédpár érintkezik) — a hézagok a törölt bejegyzések helyei.

### 8.3 A blobok NYERS JPEG-ek

A `thumbs`, `thumbs2`, `bigthumbs` és `previews` első foglalt blobja
egyaránt `ff d8 ff e0 00 10 4a 46` kezdetű, azaz **JFIF-fejlécű JPEG**.
Nincs saját fejléc, nincs képméret-előtag: az `eltolás`/`hossz` páros
közvetlenül egy JPEG-fájlt határol ki az adatfájlból.

⚠️ **Az `albums.db` KIVÉTEL:** ott a blob 8 bájt fejléc (`uint32 width`,
`uint32 height`) + `w·h·4` bájt **BGRA** — ld. a lap „ÖTÖDIK bélyegkép-tár"
szakaszát. A **keret** (a négy tömb) mind az ötnél azonos; csak a blob
tartalma tér el.

⇒ **A PicasaPy egy `open()` + `seek()` + `read()`-del kiveheti az eredeti
Picasa bélyegképét.** Ehhez a kulcs képzését NEM kell ismerni.

### 8.4 A slot sorszáma MAGA az azonosító — nincs kulcskeresés

A `thumbs`, `thumbs2` és `facetemplatesV2` slotszáma együtt mozog a
`thumbindex.db` rekordszámával:

| katalógus | `thumbindex` N | `thumbs` | `thumbs2` | `facetemplatesV2` | `bigthumbs` | `previews` | `albums` |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 140 758 | 140 755 | 140 755 | — | 273 921 | 273 921 | 2 371 |
| B | 3 338 | **3 338** | **3 338** | **3 338** | 6 169 | 5 971 | 144 |
| C | 2 903 | **2 903** | **2 903** | 2 882 | 6 169 | 5 971 | 125 |

Két katalógusban **pontosan egyenlő**, a harmadikban 3-mal kevesebb (a
`thumbindex` három újabb bejegyzéséhez még nem készült bélyegkép).

⇒ A `<név>_index.db` **nem hash-tábla**: a slot indexe azonos a
`thumbindex.db` rekordsorszámával. *Megerősítő mérés:* `kulcs % slotszám ==
slot` a 3 204 foglalt slotból **0**-ra teljesül, és a slotszám nem
kettőhatvány — nyitott címzésű táblának egyik sem volna igaz.

**A `bigthumbs` és a `previews` UGYANEBBEN az azonosítótérben él** — a
nagyobb slotszámuk túlfoglalás, nem másik tér. A bizonyíték a **legutolsó
FOGLALT slot indexe**:

| katalógus | `thumbindex` N | `bigthumbs` slot | utolsó foglalt idx | foglalt |
|---|---:|---:|---:|---:|
| A | 140 758 | 273 921 | 140 741 | 14 531 |
| B | 3 338 | 6 169 | 3 748 | 1 221 |
| C | 2 903 | 6 169 | **2 902 = N−1** | 399 |

A C katalógusban a legutolsó foglalt slot **pontosan** a `thumbindex` utolsó
rekordja; az A-ban 17-tel alatta van. A tömb tehát a `thumbindex`
sorszámával indexelődik, csak **jóval nagyobbra van foglalva, és sosem
zsugorodik** — a `bigthumbs`/`previews` mindkét kis katalógusban azonos
(6 169 / 5 971), mert közös előzményből örökölték.

A B katalógusban a 3 748 **túllóg** a mai N=3 338-on: ott a `thumbindex`
zsugorodott (részhalmaz-katalógus), és a fölötte maradt bejegyzések
elárvultak. ⇒ **Olvasáskor a slotszám fölé nem szabad indexelni, és az
N-en túli foglalt slotokat el kell dobni.**

### 8.5 Mi a kulcstömb — NEM tartalom-ellenőrzőösszeg

A `thumbs` és a `thumbs2` kulcstömbje **bitre azonos** (3 338 / 3 338
egyezés), miközben a bennük tárolt JPEG-ek különbözőek. ⇒ a kulcs a
**forrásból** származik, nem a tárolt blobból.

A „tartalom-hash" hipotézist **kétirányú mérés cáfolja**:

| irány | `thumbs` | `previews` |
|---|---:|---:|
| ugyanaz a kulcs, de a blobok NEM azonosak | 217 / 217 csoport | 161 / 161 csoport |
| azonos blob, de ELTÉRŐ kulcs | 310 eset | 18 eset |

Egyik irányban sem áll a megfeleltetés. **Elvetve.**

A `thumbindex.db` 30 bájtos farkában sem szerepel: a farok mind a 27
lehetséges eltolásán megnézve egyetlen `uint32` sem esik a kulcshalmazba
20%-nál nagyobb arányban.

**Amit tudunk:** ugyanaz az útvonal **324** esetben visel két különböző
kulcsot (3 204 foglalt slotra 1 532 egyedi útvonal jut) ⇒ a kulcs az
útvonalon **kívül** legalább egy változó bemenetet is használ.

### 8.6 VISSZAVONVA: a korábbi kiadás `q`/`u` mérései

A lap első kiadásának 8.3 és 8.4 szakasza egy 12 bájtos rekord `q` és `u`
mezőjét elemezte. **Ez a két mező nem létezik.** A téves olvasás a
kulcs-, eltolás- és hossztömb egymás melletti bájtjait ragasztotta össze,
ezért az ott közölt kizárások (10 mező-összevetés, 24 hash-kombináció) és
statisztikák (egyediségi arányok, bit-eloszlás) **nem érvényesek** — nem
egy valódi mezőre vonatkoztak. Aki a kulcs képzését kutatja, **ne
támaszkodjon rájuk**, és ne tekintse a felsorolt hash-családokat kizártnak.

⭐ **A visszavont szakaszban ott volt a saját cáfolata is:** a „`q`" felső
bitjeinek 1-aránya `0,33 … 0,16` volt, 0,50 helyett. Ezt a kiadás
érdekességként írta le. Valójában ez pontosan az, amit **kis egész számok
felső bitjeitől** várunk — az eltolás-tömbtől. A ferde bit-eloszlás nem a
hash különössége volt, hanem annak bizonyítéka, hogy a mező **nem hash**.

### 8.7 Ami NYITVA marad

| kérdés | állapot | a következő lépés |
|---|---|---|
| a kulcs képzésének képlete | **NYITOTT** (örökölt) | a kulcstömböt feltöltő kód: a `0x006b7fc0`-t hívó **olvasó** párja, illetve a `[esi+0x0c]` tároló írói |
| mi indexeli a `bigthumbs`/`previews` slotokat | **LEZÁRVA** e körben | ugyanaz az azonosítótér, túlfoglalt tömbbel — ld. 8.4 |

**A kulcs NEM szükséges** ahhoz, hogy a PicasaPy kiolvassa az eredeti
Picasa bélyegkép-gyorsítótárát (8.3–8.4) — csak ahhoz kell, hogy olyan
gyorsítótárat ÍRJUNK, amit a Picasa frissnek fogad el.

*Bizonyítottsági fok: a **formátum megerősített** (az író kódjából olvasva
ÉS három katalóguson maradék nélkül, az adatfájl méretével egyezően
ellenőrizve); a **kulcs képzése NYITOTT**.*

Jegyek: **#2195** (olvasó a két formátumhoz), **#1** (a db3-import gyűjtő).

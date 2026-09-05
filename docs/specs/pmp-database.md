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

### Az `imagedata` oszlop-REGISZTER — 37 oszlop, névvel és tagoffszettel (#2304)

A `FUN_004127c0` (1893 b) regisztrálja az `imagedata` tábla oszlopait: minden
oszlophoz **egy név-sztring és egy tagoffszet** tartozik, egységes fordítási
mintában (`push <név>` → `lea eax, [esi + offszet]` → regisztráló hívás).

Ez a tábla az oszlopkészlet **igazságforrása**: a `.pmp` fájlok megléte
telepítésenként változik (ld. lentebb a két telepítés eltérését), a regiszter
viszont azt mondja meg, mit ISMER a program.

| oszlop | tagoffszet | | oszlop | tagoffszet |
|---|---|---|---|---|
| `parent` | `+0x16c` | | `uid64` | `+0xaa8` |
| `filetype` | `+0x22c` | | `aliasparents` | `+0xb10` |
| `fileflags` | `+0x28c` | | `colorspace` | `+0xc40` |
| **`creation`** | **`+0x358`** | | `personalbumid` | `+0xca0` |
| **`modified`** | **`+0x3c0`** | | `suggestionpersonalbumid` | `+0xd00` |
| **`updated`** | **`+0x428`** | | `facequality` | `+0xd60` |
| `width` | `+0x490` | | `facerect` | `+0xdc0` |
| `height` | `+0x4f0` | | `deferredface` | `+0xe28` |
| `rotate` | `+0x550` | | `deferredregion` | `+0xe88` |
| `flipped` | `+0x618` | | `facerectdata` | `+0xee8` |
| `edit_width` | `+0x678` | | `personalbumrecs` | `+0xf48` |
| `edit_height` | `+0x6d8` | | `personalbumrecvalues` | `+0xfa8` |
| `caption` | `+0x738` | | `personalbumrecs2` | `+0x1008` |
| `filters` | `+0x798` | | `personalbumrecvalues2` | `+0x1068` |
| `textactive` | `+0x858` | | `peoplealbumchecksum` | `+0x10c8` |
| `edited` | `+0x918` | | **`tagdate`** | **`+0x1128`** |
| `revertable` | `+0x978` | | `fdbhash` | `+0x1190` |
| `originslow` | `+0x9d8` | | `backuphash` | `+0x11f0` |
| `originfast` | `+0xa40` | | | |

**Négy dátum-jellegű oszlop van:** `creation`, `modified`, `updated`
(egymás után, `+0x358`/`+0x3c0`/`+0x428`) és `tagdate` (`+0x1128`).

**A lépésköz árulkodó.** A szomszédos oszlopok többnyire `0x60` vagy `0x68`
bájtra vannak egymástól — ez az oszlop-szerkezet mérete. Ahol a lépés `0xc0`
vagy nagyobb (`parent`→`filetype`, `rotate`→`flipped`,
`filters`→`textactive`, `textactive`→`edited`, `aliasparents`→`colorspace`),
ott **regisztrálatlan slot** marad ki: olyan tagok, amelyeket ez a függvény
nem köt névhez. Hogy azok mik, nincs mérve.

> ⛔ **NE keverd össze a rendezés forrásával.** A rendező-hasonlító
> (`FUN_004a7890`) egy MÁSIK objektum oszlopait olvassa: ott a név-oszlop
> `+0xb50`, a dátum-oszlop `+0xc10` (`FUN_004a6dc0` köti be őket). Ezek az
> offszetek **nem szerepelnek** a fenti táblában, és a lépésközük is más —
> tehát a rendezés forrása nem az `imagedata` tábla, hanem egy másik
> szerkezet. A #2304 ezen a ponton tart.

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
~~A kulcs képzése továbbra is **NYITOTT**~~ — **ELAVULT JELÖLÉS, javítva
2026-09-04:** a képlet a **8.10** szakaszban megvan és mérve van. Ez a
bekezdés csak azt rögzíti, hogy ezek az EGYSZERŰ jelöltek külön-külön nem
adják ki — a tényleges képlet összetett.

*Bizonyítottsági fok: megerősített* (két adatbázis, négy tár, teljes vektorok).

##### ⚠️ HELYESBÍTVE — a kulcs képlete NEM volt nyitott (2026-09-04, #1446)

> **Ez a szakasz eredetileg azt állította, hogy a kulcs képzése nyitott, és
> 25 további jelöltet zárt ki. Az állítás TÉVES volt:** ugyanennek a lapnak a
> **8.10** szakasza már 2026-09-03 óta tartalmazza a **teljes képletet**, a
> bináris címeivel. A tévedés oka: a fenti, 8.2-korabeli „a kulcs képzése
> továbbra is NYITOTT" mondat **elavult jelölés** volt, és a kör azt vette
> alapul ahelyett, hogy a lap saját későbbi szakaszát elolvasta volna.
> Az elavult mondatokat ez a kör javította.
>
> Ami a mérésből ÉRVÉNYES marad, az alább áll — kiegészítve a **8.10
> független ellenőrzésével**.

A hét korábban kizárt `imagedata`-oszlop mellé ez a kör **huszonöt további
jelöltet** zárt ki, a tulajdonos valódi adatbázisán (`thumbindex.db`
3338 sor, `thumbs_index.db` ugyanennyi slot), a saját olvasónkkal
(`pmpimport/thumbindex.py`).

**A minta, amin a mérés futott:** a `thumbindex.db` **2776** sora valódi
fotó (nem könyvtár, nem üres slot, van neve, `size > 0`, `creation_filetime > 0`).

**1. A bejegyzés SAJÁT mezőiből képzett jelöltek — mind 0/3188:**

| jelölt | jelölt |
|---|---|
| `creation_filetime` (teljes 64 bit) | `access_filetime` |
| `creation_filetime` alsó 32 bit | felső 32 bit |
| `access_filetime` alsó 32 bit | `size` |
| `cft_lo ^ size` | `cft_lo + size` |
| `cft ^ aft` | `cft_hi ^ cft_lo` |
| `cft_hi + cft_lo` | Unix-időbélyeg (32 bit) |
| Unix-idő `^ size` | `cft / 10^7` |
| `cft >> 16` | `size * 2` |
| a sor indexe | a `kind` mező |

**2. Név- és útvonal-hash jelöltek — mind 0/400:**
négy alak (fájlnév · kisbetűs fájlnév · teljes útvonal · kisbetűs teljes
útvonal) × két kódolás (UTF-8 · UTF-16LE) × négy hash (**CRC32**, **djb2**,
**sdbm**, **FNV-1a**) = **16 kombináció**, egyetlen egyezés nélkül.

**3. ⭐ A kulcs a valódi sorokon EGYEDI: 2776 / 2776, nulla ütközés.**

Ez kizárja azt is, hogy csoportbélyeg legyen (mappa, méret, dátum): egy
csoportbélyeg ütközne. A kulcs **32 bites** (a legnagyobb mért érték
`0xfffebc36`), eloszlása egyenletes (a felső bit 1660/3188 sorban áll,
a páros értékek aránya 1654/3188).

> ⚠️ **Mérési csapda, amibe ez a kör beleesett — a következő kör ne
> ismételje:** ha a szűrés csak az „üres slot" és a „könyvtár" jelzőt
> nézi, **412 helykitöltő sor is átmegy** (üres vagy „ 1" név, `size = 0`,
> `creation_filetime = 0`). Ezek kulcsa ütközik, és a mérés **hamis
> 217 ütközést** mutat. A helyes szűrés a `size > 0` **és**
> `creation_filetime > 0` feltételt is beleveszi.

**Pozitív kontroll az importőrünkre:** az `iter_photo_records` szűrője
(`is_directory` vagy üres név, `importer.py:62`) a valódi adatbázison
**pontosan 2776 sort** enged át — nincs köztük helykitöltő és nincs
arc-rekord. A termékkód szűrése tehát HELYES; a fenti csapda csak az
ad-hoc mérésé volt.

⇒ A kizárások **érvényesek maradnak** — de nem azért, mert a képlet
ismeretlen, hanem mert a képlet **összetett**: egyik egyszerű jelölt sem
adhatta ki. A tényleges képlet a **8.10** szakaszban áll:
`(JS_hash(teljes_út) mod 1 000 231) ^ rol(idő_lo,13) ^ rol(idő_hi,17) ^ rol(méret,18)`.

**A 8.10 FÜGGETLEN ELLENŐRZÉSE (ez a kör, a tulajdonos valódi katalógusán):**

| beállítás | egyezés |
|---|---:|
| a **második** FILETIME (`+8`, a rekord „hozzáférés" mezője), bájtonkénti ASCII-hajtás | **2161 / 2776** |
| ugyanez az **első** FILETIME-mal | **0 / 2776** |
| ugyanez **UTF-16LE** útvonal-kódolással | **0 / 2776** |
| UTF-8 · cp1250 · cp1252 · latin1 kódolással | **mind 2161 / 2776** (azonos, mert a hajtás bájtonkénti) |

⇒ **A képlet és a mezőválasztás MEGERŐSÍTVE.** A kódolás bájtonkénti
(nem széles karakteres); a négy egybájtos kódolás azonos eredménye ezt
mutatja.

⚠️ **Új, MÉRT megfigyelés — 615 sor egyik idővel sem egyezik.** Nem
formátumfüggő (jpg 306 · bmp 206 · png 87 · mp4 10 · tif 3 · jpeg 2), és a
615-ből 393-nál a két FILETIME azonos. A legvalószínűbb magyarázat, hogy
ezeknél a **tárolt ellenőrzőösszeg elavult** a bejegyzés mai
attribútumaihoz képest (a fájl megváltozott, a bélyegkép nem épült újra) —
**de ez NINCS bizonyítva**. ⛔ **BLOKKOLT — de 2026-09-05 óta OLCSÓBBAN
feloldható.** A 8.10 új szakasza szerint a számoló függvénynek **két módja**
van, és a másodikban **nincs útvonal**: `rol(q_lo,13) ^ rol(q_hi,17)`, ahol
`q` a FILETIME egész másodpercre kerekítve. ⇒ **Versengő magyarázat:** a
615 sor nem elavult, hanem **a 2. módban** íródott. **Megszerzés (új, olcsó):**
ugyanazon a katalóguson, a 615 nem egyező sorra újra kell számolni a
`Checksum₂`-t — **új adatgyűjtés nem kell**. A korábbi két út (frissen épült
katalógus, illetve az ÍRÓ ág kimérése) megmarad tartaléknak.


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

### 8.1 `thumbindex.db` — az útvonal-index (HELYESBÍTVE 2026-09-03)

> ⚠️ **Két lényeges javítás az első kiadáshoz képest.** (1) A rekord
> **NEM teljes útvonalat** tárol fájloknál, hanem csak a **nevet** — a
> teljes út a szülőmappa rekordjából áll össze. (2) A `típus` **nem**
> „mappa vagy fájl", hanem **felismert formátumkód**, tizenkét mért
> értékkel. Aki az első kiadás szerint ír parsert, rossz útvonalakat kap.

```
+0   uint32   magic = 0x40466666      ("ffF@" ASCII-ként)
+4   uint32   rekordszám (N)
+8   N × rekord:
        ASCIIZ  NÉV (fájlnál csak a fájlnév; mappánál a teljes,
                „\"-re végződő útvonal) — változó hosszú, NUL-lezárt
        +0   uint64  FILETIME — létrehozás
        +8   uint64  FILETIME — hozzáférés
        +16  uint32  méret bájtban
        +20  uint32  típus — FORMÁTUMKÓD (lásd lentebb)
        +24  uint8   „dirty"
        +25  uint8   „valid"
        +26  uint32  szülőmappa slotindexe, vagy 0xFFFFFFFF
        ⇒ a farok pontosan 30 bájt
```

⭐ **A hét mező PONTOSAN a 2. szakasz diagnosztikai CSV-fejléce:**
`Name, Creation Time, Access Time, Size, Type, Dirty, Valid`. A `Name`
oszlop neve tehát **szó szerint igaz volt** — név, nem útvonal; az első
kiadás olvasta félre.

#### A teljes útvonal összeállítása

| mérés (2 katalógus) | nagy katalógus | kis katalógus |
|---|---:|---:|
| fájl-bejegyzés (`+26 ≠ 0xFFFFFFFF`) | 133 089 | 3 188 |
| ebből a NÉV `\`-t tartalmaz | **0** | **0** |
| a `+26` érvényes, `\`-re végződő mappa-slotra mutat | **133 089 / 133 089** | 2 776 / 3 188 |

⇒ `teljes_út(i) = név(szülő(i)) + név(i)`.

A kis katalógusban hiányzó **412** eset pontosan a `típus = 1001`
bejegyzések halmaza (ld. lentebb) — azok nem fájlok.

#### A `típus` mező — FELISMERT formátum, nem kiterjesztés

| típus | mi | nagy katalógus | kis katalógus |
|---:|---|---:|---:|
| 0 | **üres rekord** (szabad slot) | 5 325 | 16 |
| 1 | könyvtár | 2 338 | 115 |
| 2 | JPEG | 121 593 | 2 424 |
| 3 | GIF | 394 | — |
| 5 | **hibás könyvtár** (a bejáró nem tudta feldolgozni) — *erős, 2026-09-05* | 6 | 19 |
| 6 | BMP | 707 | 206 |
| 8 | AVI | 37 | — |
| 10 | MP4 / MPG / MTS | 2 645 | 17 |
| 11 | WMV | 13 | — |
| 13 | TIFF | — | 3 |
| 14 | PNG | 7 693 | 125 |
| 22 | TGA | 1 | — |
| 31 | WebP | 6 | 1 |
| 1001 | **arcsablon-bejegyzés** (a `+26` mezője NEM szülőindex) | — | 412 |

**A besorolás a TARTALOM alapján történik, nem a kiterjesztésből.** A nagy
katalógusban:

- 33 `.png` **kiterjesztésű** fájl `típus = 2` (JPEG),
- 26 `.jpg` és 4 `.jpeg` `típus = 14` (PNG),
- a hat `típus = 31` (WebP) közül kettő `.jpg`/`.png` nevű.

⇒ Egy átnevezett/rosszul elnevezett fájlt a Picasa a valódi formátuma
szerint jegyez be. A saját olvasónk **ne a kiterjesztésből** következtessen.

#### ⭐ A `típus` FORRÁSA: a fájltípus-tábla 30 ágú kapcsolója (2026-09-05)

> **Bizonyítottsági fok: megerősített** a kapcsolótáblára és az
> ágakhoz tartozó kiterjesztésekre (mind kiolvasott sztring); **erős** a
> tárolt `típus` = ágindex **+ 2** megfeleltetésre (tíz független pont).

A `típus` mező nem a bélyegkép-rétegé: a **fájltípus-táblából** jön, amit a
`Support*` kapcsolók építenek (`konyvtar-ablak-meretek.md`, #2344 lánca:
`0x00402f90` → `0x004183c0` → `0x004e04a0` → **`0x004fadb0`** →
`0x004fa590`). A `0x004fadb0` egy **30 ágú ugrótáblás kapcsoló**:

```asm
0x004fadba  jmp dword ptr [eax*4 + 0x004fb948]
```

A tábla minden ága **kiterjesztés-sztringeket** regisztrál a modul
`+0x3dc` tömbjébe (8 bájtos bejegyzések: `char* kiterjesztés`, `uint32
típusérték` — `0x004fa5b6` / `0x004fa5de`).

| ág | a regisztrált kiterjesztések | tárolt `típus` (ág + 2) |
|---:|---|---:|
| 0 | `.jpg` · `.jpeg` · **`.jpe`** | **2** ✔ mérve |
| 1 | `.gif` | **3** ✔ |
| 4 | `.bmp` | **6** ✔ |
| 5 | `.psd` | 7 |
| 6 | `.avi` · `.divx` | **8** ✔ |
| 7 | `.mov` · `.mp4` | **10** ✔ |
| 8 | `.mpg` · **`.mpeg`** · **`.ty`** | 10 |
| 9 | `.wmv` | **11** ✔ |
| 10 | `.asf` | 12 |
| 11 | `.tif` · `.tiff` | **13** ✔ |
| 12 | `.png` | **14** ✔ |
| 13 | `.mp3` | 15 |
| 14 | `.wav` | 16 |
| 15 | `.wma` | 17 |
| 16 | **dinamikus lista** (`call 0x00a4c720` tölti fel, nem literál) | 18 |
| 17 | `.pal` | 19 |
| 19 | `.url` | 21 |
| 20 | `.tga` | **22** ✔ |
| 25 | `.txt` | 27 |
| 26 | `.cpp` · `.h` · `.cc` | 28 |
| 27 | `.ogg` | 29 |
| 29 | `.webp` | **31** ✔ |
| 2 · 3 · 18 · 21 · **23** · 22 · 24 · 28 | **közös alapeset** (`0x004fb93f`) — **nem regisztrál kiterjesztést** | 4 · 5 · 20 · 23 · **25** · 24 · 26 · 30 |

**A „+2" megfeleltetés bizonyítéka:** a 8.1 típus-táblája a tulajdonos két
katalógusán MÉRTE a tárolt értékeket. Tíz formátumnál az ágindex és a mért
tárolt érték különbsége **mindig pontosan 2** (a ✔-es sorok:
jpg 0→2 · gif 1→3 · bmp 4→6 · avi 6→8 · mp4 7→10 · wmv 9→11 · tif 11→13 ·
png 12→14 · tga 20→22 · webp 29→31). Tíz független egyezés véletlenül
kizárt. *(A kapcsoló feje maga nem mutat eltolást — az `eax`-et a hívó adja,
`0x004e04a0`.)*

⇒ **Kiterjesztés nélküli fájl vagy ismeretlen kiterjesztés esetén a
besoroló `0x3e8 = 1000`-et ad** (`0x004e2c40`, ld. `konyvtar-ablak-meretek.md`).

#### ⭐ Ezzel a `típus = 25` kérdése is eldőlt — NEGATÍV válasz

A `picasa-mappakezelo.md` 16.2/b BLOKKOLT tétele („mit jelent a `Type` 25?")
így **megválaszolható, negatívan**: a 25-ös tárolt érték a **23. ághoz**
tartozik, az pedig a **közös alapeset** — **nem regisztrál egyetlen
kiterjesztést sem**. ⇒ A 25 **nem fájlformátum-típus**. Ez egybevág azzal,
ahol a bejáró használja: a `{1, 5, 25, 1001}` „a név már teljes út" halmaz
és a `{1, 25, 26}` frissítés-mentes család **mind szerkezeti** típus
(könyvtár · hibás könyvtár · arcsablon). ⇒ A 25 is **szerkezeti**, nem
formátum — a pontos szerepe továbbra sincs megnevezve, de a
formátum-irány **kizárva**.

#### `típus = 0` — üres rekord

Mind az 5 325 (illetve 16) ilyen bejegyzésen: a **név üres**, a méret `0`,
a `dirty` és a `valid` `0`, mindkét FILETIME `0`, a `+26` pedig
`0xFFFFFFFF`. ⇒ Ez **szabad slot**, nem tartalom. Ez magyarázza, miért nem
zsugorodnak a slot-tömbök (8.4) és mire való a `valid` bájt.

#### `típus = 1001` — arcsablon

A kis katalógusban a `típus = 1001` bejegyzések halmaza **pontosan
megegyezik** a `facetemplatesV2_index.db` foglalt slotjainak halmazával —
**412 = 412, metszet 412**, azaz halmaz-azonosság, nem csak darabszám.
⇒ Ezek nem lemezes fájlok, hanem az arcfelismerés sablon-bejegyzései,
amelyek ugyanabban az azonosítótérben ülnek, mint a képek.

#### ⭐ A `típus` a NÉVFELOLDÁST is vezérli (2026-09-05)

> **Bizonyítottsági fok: megerősített** a szabályra és a szülőlekérdezőre;
> **erős** a `típus = 5` = „hibás könyvtár" olvasatra. Forrás: a
> könyvtárbejáró névfeloldó ága, `picasa-mappakezelo.md` 16.2/b.

Az eredeti **nem** a `+26` szentinelből dönti el, hogy a név teljes út-e,
hanem a `típus`ból (`0x004f27f3`–`0x004f2825`):

```
ha  valid (+25) == 0                      → a NÉV önmagában a teljes út
ha  típus ∈ {1, 5, 25, 1001}              → a NÉV önmagában a teljes út
különben                                   → szülő_neve + név
```

A szülőág is feltételes: ha a `+26` a rekordszámon kívülre mutat, vagy a
**szülő** típusa `0`, a Picasa egy tartalék sztringre esik vissza —
**kivételt nem dob**.

⭐ **Ez magyarázza a fenti 412-es anomáliát.** A szülőlekérdező
**`FUN_004e2990`** (66 b) a `típus == 1001` esetet **a `+26` beolvasása
ELŐTT** −1-gyel zárja rövidre (`0x004e29bb`). Egy arcsablon-bejegyzés `+26`
mezője tehát **nem szülőindex**, és az eredeti soha nem olvassa annak — a
mért „412 esetben nem mutat mappára" nem adathiba, hanem a formátum
szabálya.

⛔ **Nálunk (mérve):** a `pmpimport/thumbindex.py` `is_directory`-ja a
`+26 == 0xFFFFFFFF` szentinelt nézi (`:57`), a `resolve_path` pedig hibás
szülőindexnél **kivételt dob** (`:231`) — mindkettő eltér az eredeti
szabályától; a beolvasott `kind` mezőt (`:50`) a `src/` **sehol nem
használja**. Jegy: **#2404**.

#### `+26 == 0xFFFFFFFF` — pontos szabály

A jelölő **pontosan** a `típus ∈ {0, 1, 5}` bejegyzéseken áll (nagy
katalógus: 7 669 = 5 325 + 2 338 + 6; kis: 150 = 16 + 115 + 19). A többi
bejegyzésen kis egész (nagy katalógus: 6 … 140 734, 2 305 egyedi érték —
nagyságrendben a mappák száma).

**Ellenőrzés:** a tulajdonos katalógusán a fejléc **140 758** rekordot
ígér, és a parser pontosan ennyit olvas ki — **0 bájt maradékkal**.

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
| a kulcs képzésének képlete | ✅ **MEGVAN** (2026-09-03, ld. 8.10) | — |
| mi indexeli a `bigthumbs`/`previews` slotokat | **LEZÁRVA** e körben | ugyanaz az azonosítótér, túlfoglalt tömbbel — ld. 8.4 |
| hány ellenőrzőösszeg-mód van | ✅ **LEZÁRVA (2026-09-05)** — **kettő**; a 2. útvonal és méret nélküli, másodperc-felbontású (8.10) | — |
| **mikor jut a 2. mód** | ✅ **LEZÁRVA (2026-09-05)** — három feltétel bármelyikére: a hívó 0-t ad · `Type = 0` · nincs szülő (`0x004e3bc2`/`0x004e3bcb`/`0x004e3bd7`) | — |
| mit hasheli az 1. mód | ✅ **LEZÁRVA** — **két** sztringet: a szülő nevét és a sajátot, összefűzés nélkül, ugyanabba az akkumulátorba (`0x004e3bdd`–`0x004e3c0e`) | — |
| **melyik hívó ad KIFEJEZETTEN 0-t** | ✅ **LEZÁRVA (2026-09-05)** — a `ret 0x18` (hat argumentum) szerint szűrve a 93 jelöltből **29** marad; ezekből **10 ad literál `0`-t**, 5 literál `1`-et, 14 futásidejűt. Két 0-s hívó (`FUN_0042f6a0`, `FUN_00793720`) teljesen elolvasva: `CThumbDB` másodlagos felület, **üres második sztringgel** | — |
| mind a 29 jelölt `CThumbDB`-e? | **feltételes** — kettő megerősítve; a többinél a hívási minta azonos (`…, m, 1, 1, m, …`), de nincs külön igazolva | a fogadó típusának ellenőrzése hívóhelyenként |
| **a nem egyező 615 sor oka** | **BLOKKOLT, de olcsóbb** | `Checksum₂` újraszámolása ugyanazon a katalóguson |

**A kulcs NEM szükséges** ahhoz, hogy a PicasaPy kiolvassa az eredeti
Picasa bélyegkép-gyorsítótárát (8.3–8.4) — csak ahhoz kell, hogy olyan
gyorsítótárat ÍRJUNK, amit a Picasa frissnek fogad el.

*Bizonyítottsági fok: a **formátum megerősített** (az író kódjából olvasva
ÉS három katalóguson maradék nélkül, az adatfájl méretével egyezően
ellenőrizve); ~~a **kulcs képzése NYITOTT**~~ — **ELAVULT, javítva 2026-09-04:** a képlet a 8.10-ben megvan és mérve van.*

Jegyek: **#2195** (olvasó a két formátumhoz), **#1** (a db3-import gyűjtő).

### 8.8 Melléklelet: a `onlinechecksum` algoritmusa — MEGFEJTVE, de nem ellenőrizhető

A bélyegkép-kulcs keresése közben a tár-osztály fordítási egységében
találtam **egyetlen** forgatás-alapú hash-t: `0x006b9870` (371 b). **Nem ez
a bélyegkép-kulcs.** Az azonosítást az egyetlen hívója dönti el:
`0x006ecd50` (835 b), amelynek sztringjei `onlinechecksum` és
`LHUpload: Image %d (onlineID = %s) cannot be found in album feed…` ⇒ a
megszűnt **Picasa Web Albums** szinkronjához tartozik.

Mivel a megfejtés készen volt, itt marad — a `imagedata_onlinechecksum`
PMP-oszlop olvasásához kellhet.

#### A sztring-hash

```
h = 0x12345678
minden bájtra:
    ha 'A' <= c <= 'Z':  c += 0x20        # csak az ASCII nagybetűk
    h ^= ((h << 5) + c + (h >> 2))        # 32 biten
h_út = h mod 1000231                      # 0xF4327
```

| cím | mit ad |
|---|---|
| `0x006b98cb` | `ecx = 0x12345678` — a kezdőérték |
| `0x006b98d2`–`0x006b98e2` | `'A'..'Z'` → `+0x20` (kisbetűsítés) |
| `0x006b98e5`–`0x006b98f9` | `h ^= (h<<5) + c + (h>>2)` |
| `0x006b98ff`–`0x006b9917` | osztás-idióma: `mod 0xF4327` = **1 000 231** |

#### Az időbélyeg-tagok

```
mp   = (FILETIME + 5 000 000) / 10 000 000     # egész MÁSODPERC, kerekítve
A    = rol(mp_lo,13) ^ rol(mp_hi,17) ^ <2. paraméter>
B    = rol(ft_hi,17) ^ rol(ft_lo,13)
kulcs_alap = h_út ^ B ^ A
```

| cím | mit ad |
|---|---|
| `0x006b987e` / `0x006b9883` | `+0x4C4B40` (5 000 000) és `/0x989680` (10 000 000) |
| `0x006b988d` | `call 0x00c13b70` — 64 bites osztás |
| `0x006b9892`–`0x006b989a` | `rol 13` / `rol 17` / `xor` / `xor <param2>` |
| `0x006b99c0`–`0x006b99c4` | a végső `xor` a nem-egyező ágon |

#### ⭐ Az érdekes rész: IDŐZÓNA-TOLERÁNS egyeztetés

A függvény nem egyetlen értéket számol, hanem **végigpróbál minden egész
órás időzóna-eltolást −12 h és +12 h között**, és mindegyikre megnézi,
egyezik-e a tárolt ellenőrzőösszeggel:

| cím | mit tesz |
|---|---|
| `0x006b991b` | `ebx = 0xFFFF5740` = **−43 200 s** (−12 óra) |
| `0x006b9920`–`0x006b99a4` | az eltolt időből képzett jelölt kiszámítása |
| `0x006b99a8` | `cmp eax, [esp+0x40]` — összevetés a **várt** összeggel |
| `0x006b99ae` | `add ebx, 0xE10` = **+3 600 s** (egy óra) |
| `0x006b99b4` | `cmp ebx, 0xA8C0` = **+43 200 s** — a ciklus vége |

⇒ Huszonöt jelölt. A Picasa tehát **tudta**, hogy egy fájl időbélyege
időzóna-váltás vagy hordozható meghajtó miatt egész órát ugorhat, és ezt
nem tekintette változásnak. Ez a tervezői döntés önmagában is átvehető.

#### ⛔ Amit NEM tudok róla

**A képlet élő adaton NINCS ellenőrizve.** A `imagedata_onlinechecksum.pmp`
oszlop **mind a három** mintakatalógusban teljesen üres (0 nem üres érték
3 011, illetve 140 661 sorból) — a szolgáltatás megszűnt, a tulajdonos
sosem használta. A `<2. paraméter>` (a `[esp+0x44]`-en érkező keverőérték)
azonosítása ezért **NINCS MEG**; a hívó `0x006ecd50` átvilágítása adná meg.

*Bizonyítottsági fok: az **algoritmus lépései megerősítettek** (címenként
kiolvasva); a **teljes képlet feltételes**, mert nincs hozzá minta.*

### 8.9 A bélyegkép-kulcs: mit zártam ki a VALÓDI kulcstömbön

A 8.6 szakasz visszavonta az előző kör kizárásait, mert azok nem létező
mezőkre vonatkoztak. Ez a szakasz a pótlásuk — mind a **valódi**
kulcstömbön mérve, a `thumbs_index.db` 3 204 foglalt slotján.

| próba | kombináció | egyezés |
|---|---:|---:|
| közvetlen mező-egyezés (méret, mindkét FILETIME fele, `+26`, XOR-párok) | 9 | **0** |
| hash a TÁROLT néven (teljes/kisbetűs/fájlnév/UTF-16 × CRC-32, FNV-1a, FNV-1, djb2, djb2-xor, sdbm, Jenkins, MD5 alsó/felső, SHA-1 alsó) | 60 | **0** |
| hash a **rekonstruált teljes úton** (8.1 szerint) × Picasa-JS-hash, CRC-32, FNV-1a, djb2, sdbm, MD5 | 28 | **0** |
| **minden** numerikus PMP-oszlop (`uint32`, valamint `uint64` alsó/felső fele) | 59 fájl | **0** |

⚠️ **A 60-as sor bemenete a TÁROLT név volt**, ami a 8.1 helyesbítése előtt
tévesen teljes útvonalnak látszott. A 28-as sor az ezzel javított,
összeállított teljes úton futott — szintén nullával.

⇒ A kulcs **nem** az útvonal önmagában, **nem** az időbélyeg vagy a méret
önmagában, és **nem** áll elő egyik ismert PMP-oszlopból sem. Marad a
bináris: a `[this+0x0c]` tárolót feltöltő kód.

### 8.10 ⭐ AZ ELLENŐRZŐÖSSZEG KÉPLETE — MEGVAN

Az „első tömb" (8.2), amit a korábbi körök „kulcsnak" neveztek, a Picasa saját
szóhasználatában **Checksum**. A képlete megvan, és mért.

#### A név a Picasa SAJÁT diagnosztikai kimenetéből

Az osztály neve **`CBlockFile`**, forrása `.\thumblab\CBlockFile.cpp`
(a sztring a `0x006b8640` és a `0x006b9030` függvényben áll). Van hozzá
CSV-kiíró: `0x006b5e00`, „Write blockfile CSV", fejléce

```
Size,Offset,Checksum
```

soronként `%d,%d,%d`. A kiírás sorrendje (`0x006b5ed6`–`0x006b5ef1`,
cdecl, tehát fordított push-sorrend) egyértelműen megfelelteti a
tárolókat:

| objektum-eltolás | a `0x0099c1e0` hívási sorrendjében | CSV-oszlop |
|---|---|---|
| `+0x54` | 1. tömb | **Checksum** |
| `+0x5c` | 2. tömb | **Offset** |
| `+0x64` | 3. tömb | **Size** |

⇒ A 8.2 „kulcs / eltolás / hossz" elnevezése helyes volt; innentől a
Picasa saját nevét használjuk.

#### A képlet

```
Checksum = ( JS_hash(teljes_út) mod 1 000 231 )
           ^ rol(idő_lo, 13)
           ^ rol(idő_hi, 17)
           ^ rol(fájlméret, 18)
```

ahol a `JS_hash` ugyanaz, mint a 8.8-ban:

```
h = 0x12345678
minden bájtra:  ha 'A' <= c <= 'Z': c += 0x20
                h ^= ((h << 5) + c + (h >> 2))       # 32 biten
```

és `idő` a `thumbindex.db` rekordjának **MÁSODIK** FILETIME mezője (`+8`).

| cím | mit ad |
|---|---|
| `0x006b9af8`–`0x006b9b08` | az osztás-idióma: `mod 0xF4327` = **1 000 231** |
| `0x006b9b0a` / `0x006b9b0d` | `edx = [edi+0x10]`, `rol edx, 0x11` (17) |
| `0x006b9b0a` / `0x006b9b10` | `eax = [edi+0x14]`, `rol eax, 0x12` (18) |
| `0x006b9b15` / `0x006b9b18` | `eax = [edi+0x0c]`, `rol eax, 0x0d` (13) |
| `0x006b9b13`–`0x006b9b1d` | a három `xor`, majd `xor ecx, edx` |
| `0x006b9b20`–`0x006b9b23` | `eax = ecx`, `ret 4` |

#### Az ellenőrzés

Pontos, 32 bites egyezés, három független katalóguson:

| katalógus | vizsgált bejegyzés | **pontos egyezés** |
|---|---:|---:|
| nagy (a tulajdonos élő katalógusa) | 133 089 | **48 605** |
| kis „arcok" | 3 188 | **2 161** |
| kis „másolat" | 2 603 | **1 932** |

Negyvennyolcezer véletlen 32 bites egyezés kizárt (várható érték
gyakorlatilag nulla), ezért a képlet **megerősített**.

#### Melyik időbélyeg — és a 8.1 mezőneve pontosításra szorul

A `+0`-s FILETIME-mal számolt egyezések **valódi részhalmazai** a `+8`-cal
számoltaknak (1 337 ⊂ 2 161): a `+0` csak ott „talál", ahol a két bélyeg
amúgy is azonos. ⇒ **A használt mező a `+8`.**

A 8.1 ezt „hozzáférés"-ként nevezi meg (a `WriteDirscannerCSV`
`Access Time` fejléce nyomán). Viselkedése alapján ez az **írás/módosítás**
ideje: a Picasa erre alapozza az elavulás-vizsgálatot, amit a hozzáférési
időre értelmetlen volna. *A CSV-fejléc szava megmarad, de a szerepét itt
mondjuk ki.*

#### ⭐ KÉT ellenőrzőösszeg-mód van — a másodikban NINCS útvonal (2026-09-05)

> **Bizonyítottsági fok: megerősített** a második mód képletére és a
> hívóhelyek számbavételére; **feltételes** arra, hogy ez magyarázza-e a
> lentebb tárgyalt nem egyező sorokat — az még mérés kérdése.

A számoló függvény (`FUN_006b99f0`, 350 b, `ret 4`) **egyetlen
verem-paramétere egy kapcsoló**, és két különböző képletre ágazik el:

```asm
0x006b99f0  cmp byte ptr [esp+4], 0
0x006b99f5  je  0x006b9b26          ; ⇒ MÁSODIK mód
```

**1. mód (kapcsoló ≠ 0) — a fenti, dokumentált képlet.**

**2. mód (kapcsoló = 0), `0x006b9b26`–`0x006b9b4b` — ÚJ:**

```asm
0x006b9b26  mov ecx, [edi+0x0c]      ; a FILETIME alsó 32 bitje
0x006b9b29  mov edx, [edi+0x10]      ; a felső 32 bitje
0x006b9b2e  add ecx, 0x4c4b40        ; +5 000 000  (fél másodperc)
0x006b9b39  adc edx, 0               ; 64 biten
0x006b9b34  push 0x989680            ; 10 000 000  (= 1 másodperc)
0x006b9b3e  call 0x00c13b70          ; 64 bites osztás
0x006b9b43  rol eax, 0x0d            ; rol(hányados_lo, 13)
0x006b9b46  rol edx, 0x11            ; rol(hányados_hi, 17)
0x006b9b49  xor eax, edx
```

```
Checksum₂ = rol( q_lo, 13 ) ^ rol( q_hi, 17 )
            ahol  q = (FILETIME + 5 000 000) / 10 000 000
```

A `FILETIME` 100 ns-os egységekben számol, tehát a `+5 000 000` és a
`/10 000 000` együtt **egész másodpercre kerekít**. ⇒ A második mód
**másodperc-felbontású időbélyeg-lenyomat**, amelyben **sem az útvonal,
sem a fájlméret nem szerepel**.

**Ki melyik módot kéri** — a `.text` teljes `e8 rel32` pásztázása szerint a
függvénynek **hat** hívója van:

| hívó | a kapcsoló |
|---|---|
| `0x00424dd1`, `0x004282f7`, `0x00568206`, `0x00568336`, `0x00602084` | `push 1` — **rögzített 1. mód** |
| **`0x004e3c13`** (`FUN_004e3ab0`, 554 b) | **futásidejű érték** (`[esp+0x1c]` = a függvény 3. paramétere) |

A futásidejű ág forrása egy szinttel feljebb: a `FUN_004e3ab0` egyetlen
hívója a `0x0042a832`, amely a saját 2. paraméterét (`[ebp+0xc]`) adja
tovább; ez a függvény (`FUN_0042a800`) pedig **`CThumbDB` virtuális
metódus**: a mutatója a `0x00c82184` rekeszben áll, a vtábla feje
`0x00c820fc`, a hozzá tartozó COL `0x00cfa164` (`offset = 84`), tehát ez a
`CThumbDB` **másodlagos felülete**, a **34. rés**.

⛔ **Ameddig eljutottam:** a 34. rés hívóit **nem** sikerült kimerítően
megtalálni — a hívás nem `call dword ptr [reg+0x88]` alakban megy
(**0 találat** a teljes `.text`-en), hanem regiszterbe töltve; a
`mov reg,[reg+0x88]` minta viszont **286** helyen áll, és azok túlnyomó
része más szerkezet ugyanazon eltolása. **Megszerzés:** a 286 találat
szűrése arra, melyiket követi `call reg` ugyanabban a bázisblokkban,
vagy a `CThumbDB` felület-térkép (11. szakasz) 34. résének visszakeresése.

#### ⭐ MIKOR választ a Picasa 2. módot — a szabály (2026-09-05, 120. kör)

> **Bizonyítottsági fok: megerősített.** Az egyetlen futásidejű hívóhely
> (`FUN_004e3ab0`) elágazása utasításról utasításra elolvasva.

```asm
0x004e3bbc  mov  ecx, [esp+0x1c]      ; a mód-kapcsoló (a függvény 3. paramétere)
0x004e3bc0  test cl, cl
0x004e3bc2  je   0x004e3c70           ; (1) a kapcsoló 0        → 2. MÓD
0x004e3bc8  cmp  dword [edi+0x18], 0
0x004e3bcb  je   0x004e3c70           ; (2) a rekord Type-ja 0  → 2. MÓD
0x004e3bd1  mov  eax, [edi+0x20]
0x004e3bd4  cmp  eax, -1
0x004e3bd7  je   0x004e3c70           ; (3) nincs szülő          → 2. MÓD
            ; különben: 1. MÓD, a SZÜLŐ rekordjával
0x004e3c70  push ecx                  ; a 2. mód ága
0x004e3c71  xor  ecx, ecx             ; a második sztring-mutató = NULL
0x004e3c73  jmp  0x004e3c13           ; ugyanaz a hívás
```

⇒ **Három feltétel bármelyike a 2. módot választja:** a hívó kifejezetten
0-t ad, **vagy** a bejegyzés `Type`-ja 0 (üres slot), **vagy** nincs
szülője (`+26 == 0xFFFFFFFF`). A 8.1 mérése szerint a szentinel pontosan a
`Type ∈ {0, 1, 5}` halmazon áll ⇒ **a könyvtár-bejegyzések és az üres
slotok mindig a 2. módot kapják**.

#### ⭐ Az 1. mód KÉT sztringet hasheli — így kerül bele a „teljes út"

A számoló két bemeneti sztringet fogad: az `edi` rekord sajátját és az
`ecx`-ben átadottat. Az 1. módú ág (`0x004e3bdd`–`0x004e3c0e`) az `ecx`-be
a **szülő rekord** nevét tölti; ha a szülőindex a rekordszámon kívülre
mutat, a `[objektum+0x550]` **tartalék sztringre** esik vissza
(`0x004e3c08`) — ugyanaz a tartalék, mint a névfeloldásban
(`picasa-mappakezelo.md` 16.2/b).

⇒ A „`JS_hash(teljes_út)`" a gyakorlatban **`JS_hash(szülő_neve ‖ saját_név)`**,
külön összefűzés nélkül: a hurok (`0x006b9a12`–`0x006b9a9e`) a két
sztringet egymás után hajtja bele ugyanabba az akkumulátorba. Aki
kompatibilis gyorsítótárat ír, ezt a **sorrendet** kell eltalálnia.

#### ⭐ KI kéri a 2. módot — legalább két hívó, ÜRES második sztringgel (2026-09-05, 121. kör)

> **Bizonyítottsági fok: megerősített** a két teljesen elolvasott hívóra és
> a számbavételre; **feltételes** arra, hogy a 29 jelöltből mind a
> `CThumbDB` 34. rése.

**A szűrés.** A `CThumbDB` 34. rését hívó kód `call dword ptr [reg+0x88]`
alakban **nem** látszik (0 találat); regiszterbe töltve hív. A
`mov reg,[reg+0x88]` **286** találatából **93**-at követ `call reg`. A
metódus `ret 0x18` (`0x0042a844`) ⇒ **hat verem-argumentum**; a mód a
**2.** (`[ebp+0xc]`), tehát a hívás előtti **5. push**. A 93-ból **29**
gyűjt legalább hat pusht:

| a 2. argumentum (a mód) | darab | néhány cím |
|---|---:|---|
| literál **`0`** | **10** | `0x004245eb` · `0x0042f6c0` · `0x0042f710` · `0x0043bc8e` · `0x0045a966` · `0x00481993` · `0x0064bea8` · `0x006a969f` · `0x006ac079` · `0x00793740` |
| literál **`1`** | 5 | `0x0043bcfe` · `0x004aa47f` · `0x0065b180` · `0x0065b323` · `0x0065b3c3` |
| regiszter (futásidejű) | 14 | `0x00424cd6` · `0x00425297` · … |

**Két hívó teljesen elolvasva** — mindkettő `CThumbDB`, mindkettő 0-t ad:

```asm
; FUN_0042f6a0 (74 b)
0x0042f6a3  push 0x00c7f979          ; ⇒ ÜRES sztring ("")
0x0042f6b8  call 0x00985ff0          ; std::string felépítése belőle
0x0042f6bd  mov  eax, [esi-4]        ; a MÁSODLAGOS felület vtáblája
0x0042f6c0  mov  eax, [eax+0x88]     ; 34. rés
0x0042f6c8  push edx                 ; arg6 = az ÜRES sztring
0x0042f6cd  push 0                   ; arg5
0x0042f6cf  push 1                   ; arg4
0x0042f6d1  push 1                   ; arg3
0x0042f6d3  lea  ecx, [esi-4]        ; this = a másodlagos felület
0x0042f6d6  push 0                   ; arg2 = a MÓD  → 2. MÓD
0x0042f6d8  push edx                 ; arg1
0x0042f6d9  call eax
```

A `FUN_00793720` (70 b) **ugyanez a minta**, ugyanazzal az üres sztringgel
(`0x00c7f979`) és ugyanazzal a `0`-val.

⇒ **A 2. mód akkor jár, ha a hívónak nincs második sztringje.** Az 1. mód
két sztringet hajt a hash-be (ld. lentebb); ha a második üres, a hashelés
értelmetlen volna — a Picasa ilyenkor az **idő-alapú** összeget használja.
A `0x00c7f979` **üres sztring** (a bájt a helyén `0x00`; a szomszédja a
`"full"` literál), tehát ez nem következtetés, hanem kiolvasott érték.

**Amit ez a lenti „nem egyező sorok" tételre jelent:** a 615 sor nem
feltétlenül **elavult** — lehet, hogy **a 2. módban** íródott. ⚠️ **2026-09-05-i SZŰKÍTÉS:** a
fenti szabály szerint a 2. mód automatikusan csak `Type = 0` vagy
szülő nélküli bejegyzésre jut, a 615 sor viszont **mind fájl-típusú**
(jpg 306 · bmp 206 · png 87 · mp4 10 · tif 3 · jpeg 2), tehát VAN szülőjük.
⇒ Náluk a 2. mód **csak úgy** jöhetett szóba, ha a hívó **kifejezetten
0-t adott**. ⭐ **2026-09-05, 121. kör — ez a feltétel TELJESÜL:** a
számbavétel szerint **tíz** hívóhely ad literál `0`-t, és a kettő közülük,
amit teljesen elolvastam, **üres második sztringgel** hívja a 34. rést. ⇒ A
2. mód **nem korlátozódik a szülő nélküli bejegyzésekre** — bármely
bejegyzés kaphatja, ha a hívója így kéri. A magyarázat tehát **újra
kiszélesedett**, és a döntő lépés megint a legolcsóbb: számold ki a
`Checksum₂`-t a 615 sorra. **Megszerzés:** (a) a `Checksum₂` újraszámolása a 615 sorra —
ha egyezik, kész; ha nem, a „elavult" magyarázat erősödik; (b) a
`CThumbDB` 34. rés hívóinak azonosítása.

#### Miért nem egyezik MINDEN bejegyzés — és miért nem hiba ez

Az egyezési arány katalóguskorral csökken:

| katalógus | jelleg | egyezés |
|---|---|---:|
| kis „másolat" | frissen épült | **74,2 %** |
| kis „arcok" | frissen épült | **67,8 %** |
| nagy | évek óta élő | **36,5 %** |

⇒ **Az eltérés maga a jelzés**, amiért a mező létezik: a gyorsítótárban álló
bélyegkép elavult a forrásfájlhoz képest. A `dirty`/`valid` bájt ezt **nem**
jelöli (mind a 121 593 vizsgált JPEG-bejegyzés `dirty=0, valid=1`), tehát az
elavulás felismerése kizárólag az ellenőrzőösszegen múlik.

⚠️ **Amit ez NEM bizonyít:** hogy minden egyes nem egyező bejegyzés
elavult. A katalóguskorral való együttmozgás alátámasztja, de nem
bizonyítja. A döntő kísérlet — egy fájl módosítása a windowsos Picasa
mellett, majd az összeg újramérése — **tulajdonosi közreműködést igényel**;
a leletet nem tartja fel.

*Bizonyítottsági fok: a **képlet megerősített** (a binárisból kiolvasva ÉS
48 605 pontos egyezéssel három katalóguson); az **eltérések oka erős**, de
egyedi szinten nincs bizonyítva.*

### 8.11 A `CBlockFile` NEM bélyegkép-specifikus — négy másik fájl ugyanez

Az író metódus (`0x006b75f0`) **19 hívási helyről** hívódik. Köztük:

| hívó | mire használja |
|---|---|
| `0x0080f830` | **`makemoviecache.db`** — a filmkészítő gyorstára (`makemoviecache\`) |
| `0x007ead60` | a **hasonlóság-kereső adatbázisa** (`CSimSearch::updating`, „Updating similarity database (will be fast next time)") |
| `0x00439a80` | album-tokenek (`]album`, `]screensaver`, `]web_`) |
| `0x004290e0` | `runtime\missing.jpg` |
| `0x00425f60` | geo-nézet (`geoview`, „Use EXIF thumbnails") |

⇒ **A 8.2-ben leírt keret ezekre a fájlokra is érvényes.** Aki megírja a
`*_index.db` olvasóját, ingyen kapja a filmkészítő-gyorstár és a
hasonlóság-adatbázis olvasását is. *(Ezekre a repóban nincs mintafájl —
a formátum-azonosság a közös íróból következik, nem mintából.)*

### 8.12 A `Size` mező 24 BITES — és ebből 16 MB-os blob-korlát következik

A `Size` szót a kód **`& 0xFFFFFF`**-fel maszkolja (CSV-kiíró:
`0x006b5eea`; továbbá `0x006b6bc3` és `0x006b952f`). Az író metódus
**elutasítja** a nagyobb blobot:

```
0x006b75f7   cmp dword ptr [eax], 0xffffff
0x006b7603   ja  0x006b7e3f          ; hibakijárat
```

⇒ Egy blob legfeljebb **16 777 215 bájt**.

**Mérés a felső 8 bitre:** mind a 17 mintaindexben, három katalóguson,
**302 000-nél több** foglalt bejegyzésen a `Size` szó felső nyolc bitje
**nulla**. Élő minta tehát arra, hogy ezek a bitek mit jelentenek, **NINCS
MEG** — de az olvasónak maszkolnia kell, mert a Picasa is maszkol.

⚠️ **A 8.2 ellenőrzése ezzel pontosítva:** a „legutolsó `eltolás + hossz`
= az adatfájl mérete" azonosság a **maszkolt** hosszal is teljesül mind a
17 fájlon (a felső bitek nullák lévén a két számítás itt egybeesik).


---

## 9. Az `albumdata_date.pmp` — a MAPPA saját dátuma, VALÓDI adatból mérve (2026-09-04, #2304)

> **Bizonyítottság: megerősített** — nem a binárisból következtetve, hanem a
> **tulajdonos saját Picasa-adatbázisából** kiolvasva (`Picasa2/db3/`
> mentés, 2026-08-22), és a futó Picasa képernyőmentésével összevetve.
>
> ⚠️ A mentés a tulajdonos magánkatalógusáról készült; **útvonalak és
> mappanevek nem kerülnek ebbe a lapba**, csak a #2304-ben már nyilvános
> `AI` mappa, mint mérési eset.

### 9.1 A kérdés

A #2304 három eltérése ugyanarra a mezőre mutatott: az eredeti a mappa
fejlécében **dátumot** ír („AI — 2023. november 14., kedd"), a bal hasábban
a **2023**-as évcsoport alá teszi, nálunk pedig nincs fejlécdátum, és az
évcsoport **2003**. A kérdés: **honnan veszi az eredeti ezt a dátumot?**

### 9.2 A válasz — `albumdata_date.pmp`, OLE Variant `double`

A mentésből kiolvasva (a `pmpimport.pmp_column` olvasónkkal, 144 sor):

| oszlop | az `AI` mappa sora (index 3) |
|---|---|
| `albumdata_name` | `AI` |
| **`albumdata_date`** | **`45244.72859953704`** |
| `albumdata_category` | `2` |

`45244.72859953704` nap az **1899-12-30**-i Variant-alapponttól ⇒
**2023-11-14 17:29:11**.

⇒ **Pontosan az a nap, amit az eredeti a fejlécben mutat** („2023. november
14., **kedd**" — 2023-11-14 valóban kedd), és pontosan az az év, ami alá a
bal hasábban sorolja. **A fejlécdátum és az évcsoport ugyanabból az egyetlen
mezőből jön.**

### 9.3 ⛔ NEM a képekből számolódik — negatív eredmény

A 144 sor eloszlása ezt kizárja:

- a **virtuális albumok** (az első három sor, `category` 0 és 8) mindegyike
  **ugyanazt** az értéket viseli: `46221.615` → 2026-07-18 14:45:36, ami az
  adatbázis létrehozásának ideje — nem képadat;
- a **lemezen lévő mappák** (`category = 2`) értékei 2009 és 2026 között
  szórnak, mappánként külön;
- az `AI` mappa értéke **egyetlen időpont, másodperc pontossággal** — a
  benne lévő 82 kép felvételi idejéből semmilyen aggregátum (legkorábbi,
  legkésőbbi, medián) nem adna másodperc-pontos „17:29:11"-et.

⇒ A mező a **mappa saját dátuma**, amit a Picasa a `.picasa.ini`
`date=` kulcsába is kiír (ld. [`picasa-ini-format.md`](picasa-ini-format.md);
a `0x0068ac80` formátumsztringje **`date=%f`**, tehát lebegőpontos).

### 9.4 Az `albumdata_category` mért értékei

Ugyanebből a mentésből, a 144 soron:

| érték | mit jelöl (a sorok alapján) |
|---|---|
| `0` | virtuális album (csillagozott, legutóbb frissítve) — `filename` üres |
| `1` | egy lemezmappa, eltérő besorolással *(egyetlen sor a mintában)* |
| `2` | **közönséges lemezmappa** — a `filename` a mappa útvonala |
| `8` | a „Név nélküliek" arc-gyűjtő — `filename` üres |

*Bizonyítottság: **erős*** — az értékkészlet a mintából teljes, a jelentés a
`filename` üres/nem üres mintázatából és a nevekből következik; a bináris
oldali kódtáblát külön nem mértem.

### 9.5 MIT AD MA a mi kódunk (mérve)

| hol | mit ad |
|---|---|
| `index/schema.py:316–318` | `folders.date TEXT`, és a migráció **`MIN(p.taken_at)`-ból** tölti — a **legkorábbi kép** dátuma |
| `ini/folder_date.py:57–72` | a `date=` **Variant-olvasója** (alappont 1899-12-30, tartomány 1…73 500) — a #2309 tette be |
| `index/sync.py:21` | a `read_folder_date_override` be van kötve a szinkronba |

⇒ **A 2003-as évcsoport mechanizmusa ezzel érthető:** ha a `date=` nem
olvasódik ki, a `folders.date` a **legkorábbi kép** dátumára esik vissza —
és egy 2003-as (hibás vagy régi) felvételi idejű kép az egész mappát
2003-hoz sorolja. A #2309 javítása pontosan ezt szünteti meg.

⚠️ **Egy MÉRT eltérés marad:** a `folder_date.py:72` a Variant-időt
`.date().isoformat()`-tal adja vissza, tehát **az időpontot eldobja**. Az
eredeti másodperc pontosságú értéket tárol (`17:29:11`). A fejlécre és az
évcsoportra ez nem hat ki; **holtverseny-feloldásra viszont nálunk nincs
meg az az információ, ami az eredetinél megvan.** *(Hogy az eredeti
használja-e valahol az időrészt, ez a kör NEM mérte.)*

### 9.6 Eredeti / nálunk / teendő

| tétel | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| a mappa dátumának forrása | `albumdata_date` (= `.picasa.ini` `date=`) | `folders.date`, a `date=`-ből, tartalék `MIN(taken_at)` | — (a #2309 megvan) |
| pontosság | **másodperc** | **nap** (`folder_date.py:72`) | eldöntendő: megtartsuk-e az időrészt |
| tartalék, ha nincs `date=` | *nem mérve* — az eredetinél az érték mindig ott van a DB-ben | `MIN(taken_at)` | — |
| a fejlécdátum és az évcsoport | **ugyanaz az egy mező** | ugyanaz a `folders.date` | — |

## MIT AD MA a mi db3-importunk — MÉRVE a tulajdonos VALÓDI adatbázisán (2026-09-04)

> **Bizonyítottság: megerősített.** A mérés a tulajdonos 2026-08-22-i
> `Picasa2` adatmappa-mentésén futott (3338 kép, 65 `.pmp` oszlop), a saját
> `picasapy.pmpimport.pmp_column` olvasónkkal. Adatvédelem: sem útvonal,
> sem fájlnév nem került erre a lapra.

A `src/picasapy/pmpimport/importer.py:22` **hat** oszlopot hasznosít:

```python
_COLUMNS = ("caption", "rotate", "star", "filters", "crop64", "deferredregion")
```

Az alábbi tábla azt mutatja, **mennyi valódi adat áll az egyes
oszlopokban**, és hogy behozzuk-e:

| oszlop | nem üres érték | behozzuk? |
|---|---:|---|
| `imagedata_filters` | **1226** | ✅ |
| `imagedata_crop64` | **488** | ✅ |
| `imagedata_tags` (kulcsszavak) | **342** | ❌ nincs a listán |
| `imagedata_lat` / `imagedata_long` | **219** / **219** | ❌ |
| `imagedata_geoview` | **219** | ❌ |
| `imagedata_backuphash` | 178 | — (nem kell, ld. `picasa-ini-format.md`) |
| `imagedata_tagdate` | **115** | ❌ |
| `imagedata_rotate` | 86 | ✅ |
| `imagedata_caption` | 5 | ✅ |
| `imagedata_text` / `_textactive` | **0** / **0** | ❌ *(üres — ebből a mintából a felirat-réteg nem ellenőrizhető)* |

### ⛔ A `star` oszlop NEM LÉTEZIK a valódi adatbázisban

A mentés **mind a 65** `.pmp` oszlopát kilistázva **nincs
`imagedata_star.pmp`**. A `table.value()` hiányzó oszlopra `None`-t ad
(`src/picasapy/pmpimport/table.py:36–41`), a hívó pedig
`star=bool(table.value("star", …))` (`importer.py:82`) ⇒ **minden kép
csillagozatlanként jön be, némán.**

A csillagozás valójában a **`db3/starlist.txt`**-ben él (ezen a lapon
fentebb: 50 sor, CRLF, soronként egy abszolút útvonal) — a mintában
**50 csillagozott kép**, amelyből az import **nullát** hoz át.

⚠️ **A tesztkészlet ezt nem foghatja meg:** a
`tests/pmpimport/test_importer.py:60` maga **létrehozza** az
`imagedata_star.pmp`-t, tehát a zöld teszt egy olyan adatbázist ír le,
amilyen a valóságban nincs.

*(Hogy MELYIK Picasa-verzió írt valaha `imagedata_star.pmp`-t, ez a mérés
nem mondja meg — a hatókör ez az egy, valódi adatbázis.)*

Jegyek: a csillag-hiba **#2335**, a kulcsszó/helyadat-hiány **#2336**.

---

## Az `albumdata_date` oszlop — a mappa dátuma TÁROLT, nem számított (2026-09-04, #2304)

**Bizalmi fok: megerősített** (bináris + mérés a tulajdonos 2026-08-22-i
katalógus-mentésén, 144 albumsor / 3338 `thumbindex`-bejegyzés).

Ez az oszlop dönti el, mi áll a mappa fejlécében, és a bal hasáb melyik
**évcsoportja** alá kerül a mappa (#2304, 1. és 2. eltérés). A kérdés az
volt, **honnan veszi az eredeti** ezt az értéket.

### A regisztrált albumoszlopok (`0x00415790`)

`token` · `name` · `filename` · **`date`** (`0x00c80d7c`) · `category` ·
`unread` · `description` · `location` · `uid` · `hascollage` · `inisync`.
Ugyanez a `date` sztring a `.picasa.ini` `[Picasa] date=` kulcsa is — a
kettő ugyanaz az érték, két tárolóban.

### Az `autodate` parancs a LEGKORÁBBI elem idejét számolja

A Mappa/Album tulajdonságai lapon van egy **`autodate`** nevű kapcsoló
(`0x00cc1c20`, 8 bájt; a lap függvénye `0x00849750`, „Folder Properties” /
`CEditAlbum::folderTitle`). A kezelője `0x00849dc0`:

| cím | mit tesz |
|---|---|
| `0x00849df4`–`0x00849e30` | a változott tulajdonság nevét a `0x00cc1c20` (`autodate`) sztringgel veti össze |
| `0x00849e3e` | `fld qword ptr [0x00c7ccf8]` — a kimeneti `double` **kezdőértéke `949998.0`** (Variant-napban ≈ 4500. év, tehát „+végtelen” őrszem) |
| `0x00849e54` | `call 0x00441760` — ez számolja ki az értéket |
| `0x00849e5b` | ha a hívás **nem 0**-t ad, a program **nem ír dátumot** |
| `0x00849e77`–`0x00849eb3` | különben a **`date`** tulajdonságot állítja be (virtuális hívás `[eax+0xe8]`) |

A `0x00441760` az album elemein megy végig (`[esp+0xb4]`, elemszám
`= [ecx+4] >> 1`):

- **üres albumnál `-1`-gyel tér vissza** (`0x0044187e`: `or eax,0xffffffff`)
  ⇒ a hívó ilyenkor nem ír dátumot;
- az akkumulátor (`[esp+0x18]`/`[esp+0x1c]`, 64 bites pár) **0-ról indul**
  (`0x00441892`);
- az összehasonlítás `0x004419d6`–`0x004419e6`: `jb`→kihagy, `ja`→tárol,
  egyenlő felső szónál `jbe`→kihagy ⇒ **a KISEBB értéket tartja meg**;
- a végén `0x00441a22` → `0x0098b650` (64 bites idő → `double`), majd
  `0x00441a2e`: `fstp qword ptr [eax]` a kimeneti mutatóra.

⇒ **Az `autodate` a mappa elemeinek LEGKORÁBBI időbélyegét számolja ki.**

### ⛔ De a TÁROLT mappadátum NEM ez — mérve, 23 mappán

Az `autodate` **egyszeri felhasználói parancs**, nem élő szabály. A
katalógus-mentésen a `thumbindex` könyvtár-rekordjaihoz egyértelműen
párosítható **23 mappára** vetettem össze az `albumdata_date`-et a mappában
lévő képek `thumbindex`-időbélyegeivel:

| hipotézis | egyezés |
|---|---:|
| `albumdata_date` == a képek **legkorábbi** ideje | **0 / 23** |
| `albumdata_date` == a képek **legkésőbbi** ideje | **0 / 23** |

A vizsgált mappára (88 kép) tételesen:

| mit | érték |
|---|---|
| tárolt `albumdata_date` | `45244.72859953704` = **2023-11-14 17:29:11** |
| a képek legkorábbi ideje | 2023-05-10 14:29:43 |
| a képek legkésőbbi ideje | 2025-05-21 07:22:23 |
| a mappa saját `thumbindex`-ideje | 2026-03-05 15:32:45 |
| medián / átlag / leggyakoribb nap | egyik sem egyezik |
| **pontos egyezés bármelyik kép idejével** | **nincs** (88-ból 0) |

⇒ **A mappa dátuma PERZISZTÁLT érték**: egyszer beáll, és a tartalom
későbbi változásától **nem** számolódik újra. A 144 albumsorból
**mindnek van dátuma** (0 üres) — az eredetiben tehát **nem létezik
„dátumtalan mappa”**.

### Melléklelet: az állapotsor dátumtartománya IGAZOLVA

A #2304 képernyőmentésén az eredeti állapotsora
„2023. május 10., szerda–2025. május 21., szerda”-t ír. A fenti mérés
szerint a mappa képeinek `thumbindex`-időbélyegei **pontosan** ezt a két
szélsőértéket adják ⇒ az állapotsor tartománya a képek 1. időbélyegének
minimuma és maximuma. Ez **egybevág** a rendezési kulccsal (#2304,
2026-09-04-i mérés), és önálló megerősítése annak.

### Mit NEM mértem

Hogy a mappa **első** dátumát mi írja be (a mappa fájlrendszer-ideje? az
első indexeléskori legkorábbi kép?). Az `autodate` ágat kimértem, az
első beíróét nem — és a windowsos mappaidők a fejlesztői gépről nem
elérhetők. Ez a #2304-ben nyitott kérdésként szerepel.

---

## A mappa-tulajdonságok beállítói: a `CThumbDB` vtábla (2026-09-04, #2304)

**Bizalmi fok: megerősített** (bináris + a bináris index RTTI-táblája).

A 99. kör megtalálta a mappadátum-beállítót (`0x004460a0`), de közvetlen
hívója nem volt. Most megvan, **hol ül**: a `CThumbDB` osztály
virtuális táblájában.

### A tábla és a rés

A bináris index RTTI-táblája szerint **`CThumbDB::vftable` a `0x00c81fa4`**-en
kezdődik (`vtable_rva` `0x00881fa4`). A mutatónk a `0x00c81fb0`-on ül, tehát
a **3. rés** (eltolás `0x0c`) — a visszafelé olvasott vtábla-kezdet és az
index egymástól függetlenül ugyanezt adja.

### A szomszédos rések: tulajdonságonként egy beállító

| rés | cím | méret | sztringje |
|---:|---|---:|---|
| 2 | `0x00443c90` | 1463 b | **`description`** |
| **3** | **`0x004460a0`** | **253 b** | — (`double`, ezért nincs sztringkezelés) |
| 4 | `0x0044fa80` | 1463 b | **`location`** |

⇒ A tábla **tulajdonságonként egy beállítót** tart, és a **`date`** ezek
közé tartozik. A dátum tehát az **adatbázis-rétegé** (`CThumbDB`), nem a
mappa- vagy felületi objektumé — ez magyarázza, miért tölti ugyanaz a hívás
az `albumdata_date` oszlopot **és** a `.picasa.ini`-t (99. kör).

### ⛔ KIMERÍTŐ NEGATÍV: a rést nem hívja senki `call [reg+0x0c]` alakban

A teljes `.text`-et (8 642 912 bájt, `0x00401000`-tól) végigpásztáztam a
`call dword ptr [reg+0x0c]` kódolásaira (`ff 50 0c` … `ff 57 0c`, a
SIB-es `0x54` nélkül): **0 találat.**

A pásztázó helyességét ismert pozitívval ellenőriztem ugyanabban a
futásban: `ff 15` (abszolút hívás) **21 110**, `ff 50` (bármely
eltolással) **951** találat, és a `0x004417fa` bájtjai (`ff 15 5c 05 c4 00`)
pontosan visszaolvashatók.

⇒ A hívás **`mov reg, [vtábla+0x0c]` + `call reg`** alakban történik (ezt a
mintát a `0x00849eab`–`0x00849eb3` — az `autodate` kezelője — meg is
mutatja `[eax+0xe8]`-cal). Ez a forma bájtmintával **nem** különíthető el a
sok ezer szerkezetmező-olvasástól.

### Mit NEM mértem — és mi kell hozzá

Hogy **melyik hívó** süti el először a beállítót egy újonnan felfedezett
mappára.

> ⛔ **HELYESBÍTVE (2026-09-05, 11. szakasz):** az „olcsó lánc kimerült"
> megállapítás **korai** volt. A pásztázás csak a `call [reg+0x0c]` alakot
> nézte, és **kimaradt két lépés**: az `e9`-es (ugró) thunkök és a
> **több-öröklődéses vtáblák** RTTI-beli feloldása. Mindkettő hozott
> eredményt — a beállító **`IThumbDB` interfész-metódus**. A folytatás:
> 11. szakasz.

## 10. A `thumbindex` KÉT IDŐBÉLYEGE — honnan jön, és mikor frissül (2026-09-05, #2304)

A 8.1 leírta a rekord bájtszintű alakját, és a két `uint64` mezőt a Picasa
**saját** diagnosztikai CSV-fejléce szerint nevezte el („Creation Time",
„Access Time"). Ez a szakasz megmondja, **mi tölti** őket, és **mikor
frissülnek** — mert a fejléc egyik neve **félrevezető**.

A kérdést a lap 69. tétele (`picasa-menu-parancsok-viselkedes.md`) hagyta
nyitva: *„az 1. FILETIME a fájl létrehozási vagy módosítási ideje-e a
forrásrendszeren, és frissíti-e a Picasa újraolvasáskor?"* Mindkét felére
van válasz.

### 10.1 A pásztázó CSAK a módosítási időt és a méretet olvassa

A könyvtárbejáró (`FUN_004e62d0`, 6 720 b) a `WIN32_FIND_DATAA`-t a saját
objektumában tartja: a szerkezet az objektum **`+0x208`**-án ül, a
kereső-fogantyú a **`+0x348`**-on, az objektum mérete **`0x34c`**.
*(Igazolás: `0x004e6cac` `lea eax,[ebp+0x208]` a `FindNextFile`-nak, és
`0x004e6cc2` `lea edx,[ebp+0x234]` a névre — `0x208 + 0x2c` pontosan a
`cFileName` eltolása.)*

Az egész pásztázó ebből **négy mezőt** olvas ki:

| mező | eltolás | hol olvassa |
|---|---|---|
| `dwFileAttributes` | `+0x208` | `0x004e6834`, `0x004e6e03`, `0x004e706b`, … |
| **`ftLastWriteTime`** | `+0x21c` / `+0x220` | `0x004e6826`, `0x004e6d6b`, `0x004e6f02`, `0x004e7187`, `0x004e7393`, `0x004e74bd`, `0x004e7541`, `0x004e806e` |
| `nFileSizeLow` | `+0x228` | `0x004e73dc`, `0x004e74b4`, `0x004e7551`, `0x004e8083` |
| `cFileName` | `+0x234` | `0x004e6cc4`, `0x004e8719`, `0x004e8b67`, `0x004e8f3f` |

⛔ **Kimerítő negatív:** a `0x004d0000`–`0x00520000` tartomány teljes
`.text`-pásztázása szerint a **`ftCreationTime` (`+0x20c`)** és a
**`ftLastAccessTime` (`+0x214`)** eltolására **egyetlen hivatkozás sincs**
a bejáró függvénycsoportjában (`0x004e6800`–`0x004e8100`); a `+0x20c`
hét, a `+0x214` hat találata mind a `0x0051xxxx` / `0x004d6xxx`
tartományban, más osztályokban van. A pásztázó **ismert pozitívjai**
(`+0x21c`/`+0x220`/`+0x228`/`+0x234`) ugyanezzel a módszerrel
előjöttek ⇒ a negatív eredmény nem a minta hibája.

*(A `FindFirstFileW`-t egy ANSI-burkoló hívja — `FUN_009aed50`, ami a
`WIN32_FIND_DATAW`-t átmásolja és a két névmezőt
`WideCharToMultiByte`-tal alakítja; a `FindNextFile` a `[0x00d694cc]`
függvénymutatón át megy, ezért nincs közvetlen hívója az indexben.)*

### 10.2 A 2. mező NEM „hozzáférési idő", hanem a fájl MÓDOSÍTÁSI ideje

A változásfigyelő (`0x004e74b2`–`0x004e74e5`) a rekord `+0x0c` és `+0x14`
mezőjét veti össze a **friss** `ftLastWriteTime`-mal és `nFileSizeLow`-val,
és eltérés esetén **felül is írja** őket:

```
0x004e74b2  mov esi, [edx+0x228]     ; nFileSizeLow
0x004e74bb  mov ecx, [edx+0x21c]     ; ftLastWriteTime.lo
0x004e74c1  mov edi, [edx+0x220]     ; ftLastWriteTime.hi
0x004e74ca  cmp ecx, [eax+0x0c] …    ; a rekord 2. időbélyege
0x004e74dc  mov [eax+0x0c], ecx      ; ← felülírás
0x004e74df  mov [eax+0x10], edi
0x004e74e2  mov [eax+0x14], esi      ; méret
```

⇒ **A rekord `+0x0c` mezője a fájl utolsó MÓDOSÍTÁSI ideje** (`mtime`),
nem a hozzáférési ideje. A Picasa saját CSV-fejléce („Access Time") ezen a
ponton **rossz nevet ad** a mezőnek. *(A `picasa-mappakezelo.md` 16.2/b
oszloptáblája az eltolásokat helyesen adja meg; a NÉV az, ami félrevezet.)*

### 10.3 Az 1. mező egyetlen írója: a kép METAADAT-dátuma

A rekord `+0x04` mezőjét egyetlen beállító írja:

| lépés | cím |
|---|---|
| beállító (`objektum` `eax`-ben, `index` + `double*` a veremben) | **`0x004eeb10`** |
| `double` → `SYSTEMTIME` | `0x0098b8f0` |
| `TzSpecificLocalTimeToSystemTime(NULL, …)` | `0x004eeb9e` |
| `SystemTimeToFileTime(&st, rekord+4)` | `0x004eebad` (`add ebp,4` a `0x004eeba4`-en) |
| a DB piszkos-jelzője: `[obj+0x5c]++`, `[obj+0x60] = 1` | `0x004eebb3`–`0x004eebb7` |

⛔ **A beállítónak a TELJES binárisban egyetlen hívója van:**
`0x00427898`, a képbeolvasó `FUN_00425f60`-on belül. A hívási hely:

```
0x00427844  mov edi, 0x37            ; metaadat-tulajdonság azonosítója (55)
0x00427860  call 0x9f05c0            ; kikeresés a kép metaadat-táblájából
0x00427867  jne  …                   ; nincs ilyen tulajdonság → KIMARAD
0x00427869  fld  qword [0xc7ccf8]    ; 949998.0 — a „nincs dátum" őrszem
0x0042787f  call 0x98bc10            ; dátum-szöveg → Variant double
0x00427886  jne  …                   ; nem értelmezhető / őrszem → KIMARAD
0x00427898  call 0x4eeb10            ; ← a beállító
```

⇒ **Az 1. mező NEM fájlrendszeri időbélyeg.** A kép saját metaadatából
vett dátum, a **beolvasás pillanatában** rögzítve — és a pásztázó
**soha nem frissíti** (10.1). A `949998.0` őrszem ugyanaz, mint a mappa
`[Picasa] date=` olvasójáé (`picasa-ini-format.md`).

⭐ **2026-09-05 (#2375) — MEGVAN, melyik mező.** A `0x37`-es tulajdonság az
EXIF **`0x9003` DateTimeOriginal** (a felvétel ideje). A kulcstér nem
azonos a tulajdonságtábla `id` mezőjével: **a kulcs = `id` + 1**, négy
független hívási hellyel igazolva. A teljes kulcstér (176 EXIF- + 55
IPTC-bejegyzés) és a levezetés: **`picasa-metaadat-tulajdonsagok.md`**.
Melléklelet: a beolvasó ugyanitt olvassa a `0x68` = `0xa420`
**ImageUniqueID** és a `0xe4` = **IPTC 2:120 Caption/Abstract** mezőt is —
és mind a hármat a mi `metadata/reader.py`-nk is **ugyanazon a címszámon**
olvassa (`:41`, `:59`, `:63`), tehát a mezőválasztásban nincs eltérés.

**Időzóna-konvenció:** mindkét mező **helyi** időből készül
(`TzSpecificLocalTimeToSystemTime` `NULL` zónával = a gép AKKORI zónája),
tehát a tárolt FILETIME UTC, de a visszaalakításhoz a **helyi** zóna kell.
Ugyanez a lánc futja a `thumbindex` visszatöltésekor is
(`0x004e0aa0`, hívja `0x004f2ef0` ← `0x004f46b0`), ahol a két `double`-ből
`+0x04` és `+0x0c` lesz, a `+0x18`/`+0x1c`/`+0x20`/`+0x21` forrásmezőkből
pedig a méret / típus / dirty / valid.

### 10.4 MÉRÉS a tulajdonos valódi katalógusán (140 758 rekord)

Anyag: `research/testdata/Picasa2/db3/thumbindex.db`. A vizsgálat a
**névbe kódolt felvételi időt** használja külső igazságforrásként
(`YYYYMMDD_HHMMSS` alak, 56 540 fájl), a mezőt UTC→`Europe/Budapest`
váltás után hasonlítva:

| | másodpercre egyezik | percen belül | eltér |
|---|---:|---:|---:|
| **1. mező** | 33 625 (59,5 %) | 51 883 (91,8 %) | 4 143 (7,3 %) |
| 2. mező | 14 348 (25,4 %) | 18 121 (32,1 %) | 37 389 (66,1 %) |

Ahol a két mező **különbözik** (44 030 fájl), az elkülönülés még élesebb:
az 1. mező 60,7 % / 96,9 %, a 2. mező 16,9 % / 20,2 %.

⇒ **Az 1. mező a felvételi idő**, a 2. nem. Ez független megerősítése a
10.3 bináris láncának.

**Két további mérés:**

1. **Az 1. mező soha nem hiányzik.** A 135 433 nem üres rekordból
   `0` darabon nulla az 1. mező; a 2. mező **1 101**-szer nulla — köztük a
   `C:\` gyökéré, amire nincs `FIND_DATA`. ⇒ a 2. mező a pásztázásból jön,
   az 1. nem.
2. **Metaadat-dátum hiányában a két mező egybeesik.** Kiterjesztésenként,
   a nem nulla időbélyegű fájlokon:

   | kiterjesztés | darab | `1. == 2.` |
   |---|---:|---:|
   | `.png` | 33 | **32 (97,0 %)** |
   | `.jpeg` | 2 104 | 1 292 (61,4 %) |
   | `.jpg` | 119 456 | 36 745 (30,8 %) |

   A PNG-k jellemzően nem hordoznak EXIF felvételi dátumot. ⇒ ha a
   `0x37`-es tulajdonság hiányzik, az 1. mező a fájl módosítási idejével
   marad egyenlő. *(A mintaelemszám 33 — ezért **erős**, nem
   megerősített; és a kezdőértéket adó függvényt nem neveztük meg,
   csak a viselkedést mértük.)*

### 10.5 Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| a „Dátum" rendezés kulcsa | metaadat-dátum, ennek hiányában a fájl módosítási ideje | `app/photo_sort.py:66–68`: `taken_at`, ennek hiányában `mtime` — **a SZABÁLY azonos** | — |
| a kulcs **rögzítettsége** | a beolvasáskor **befagy** a DB-be; a pásztázó csak a 2. mezőt frissíti | a rendezéskor **élőben** olvassuk a `mtime`-ot | #2304 |
| a 2. mező neve az olvasónkban | a fájl **módosítási** ideje | `pmpimport/thumbindex.py`: **`modified_filetime`** — átnevezve | ✅ #2373 |
| időzóna | helyi idő → UTC a gép zónájával | az olvasónk nyers `uint64`-et ad; az értelmezés a mezők docstringjében ki van mondva | ✅ #2373 |

> ⛔ **Helyesbítés a 69. tételhez.** Az ottani „eredeti / nálunk" tábla azt
> sugallta, hogy a **tartalék-szabályunk** tér el az eredetitől („nálunk
> EXIF-hiány esetén a mai `mtime`"). A 10.3–10.4 szerint a szabály
> **ugyanaz**; a mért különbség a **rögzítettség**: az eredeti a
> beolvasáskori értéket tárolja és nem frissíti, mi minden rendezéskor a
> pillanatnyi `mtime`-ot olvassuk.

*Bizonyítottsági fok: **megerősített** a pásztázó négy mezőjére és a
kimerítő negatívra (10.1), a 2. mező jelentésére (10.2), a beállító
egyetlen hívójára és az időzóna-láncra (10.3); **erős** az 1. mező
felvételi-idő jellegére (10.4, mérés) és a metaadat-hiányos tartalékra
(n = 33).*

### 10.6 Nyitott kérdések mérlege (10.)

`0 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| az 1. FILETIME létrehozási vagy módosítási idő-e, és frissül-e (69. tétel) | **LEZÁRVA** — egyik sem: beolvasáskori metaadat-dátum, és **nem frissül** (10.1, 10.3) |
| mit jelent valójában a 2. mező | **LEZÁRVA** — a fájl módosítási ideje, a CSV-fejléc neve téves (10.2) |
| mi tölti az 1. mezőt metaadat-dátum hiányában | **LEZÁRVA** — a 2. mezővel egyenlő marad (10.4, erős) |
| melyik metaadat-tulajdonság a `0x37` (55) | **LEZÁRVA (2026-09-05, #2375)** — EXIF `0x9003` DateTimeOriginal; a kulcs = a tulajdonságtábla `id`-je + 1. Lap: `picasa-metaadat-tulajdonsagok.md` |

## 11. A `CThumbDB` INTERFÉSZ-TÉRKÉPE — a mappadátum-beállító `IThumbDB`-metódus (2026-09-05, #2304)

> **Bizalmi fok: megerősített.** Az objektum-kiosztást **két, egymástól
> független forrás** adja ugyanúgy: a konstruktor vtábla-írásai és az
> RTTI osztályhierarchia-leírója.

A 2026-09-04-i szakasz megtalálta a beállítót a `CThumbDB` vtáblájában, de
a hívóját nem — és „kimerült olcsó láncot" jelentett. **Két lánclépés
kimaradt**, és mindkettő adott eredményt.

### 11.1 A kimaradt 1. lépés: az UGRÓ thunkök

A korábbi pásztázás csak `e8`-as (hívó) hivatkozásokat keresett. `e9`-es
(ugró) hivatkozásra pásztázva a három tulajdonság-beállító mindegyikére
**pontosan egy** találat van:

| beállító | thunk | a thunk kódja |
|---|---|---|
| `description` `0x00443c90` | `0x0049f4a0` | `sub ecx, 8` · `jmp 0x00443c90` |
| **`date` `0x004460a0`** | **`0x0049f390`** | `sub ecx, 8` · `jmp 0x004460a0` |
| `location` `0x0044fa80` | `0x0049f310` | `sub ecx, 8` · `jmp 0x0044fa80` |

A három thunk egy **~57 darabos, 8 bájtos thunk-futam** része
(`0x0049f1e0`–`0x0049f59x`; a bináris index mindegyiket külön, 8 bájtos
függvényként listázza). Ez a MSVC **több-öröklődéses `this`-igazító**
thunkjeinek szabványos alakja.

⚠️ **Módszertani tanulság:** a thunk **kezdőcímét** kell keresni az
adatszekciókban, nem az ugrás címét — a vtábla a `0x0049f390`-et tárolja,
nem a `0x0049f393`-at. Az első pásztázásom emiatt adott nullát.

### 11.2 A kimaradt 2. lépés: az RTTI feloldja, MELYIK interfész

A `CThumbDB` **tizenöt** bázisosztályt hoz (RTTI osztályhierarchia-leíró),
és a vtáblák „complete object locator"-ának `offset` mezője megmondja,
melyik bázishoz tartoznak:

| vtábla | `offset` | melyik bázis | tartalmazza a beállítókat? |
|---|---:|---|---|
| `0x00c81f78` | 0 | `CThumbDB` / `ytBaseThread` | nem |
| **`0x00c81fa4`** | **72** | **`IThumbDB`** | **IGEN, közvetlenül** (2/3/4. rés) |
| `0x00c820d0` | 80 | **`IAlbumStore`** | igen, de **thunkön át** |

A thunkök `sub ecx, 8`-a pontosan a **80 − 72 = 8** eltérés ⇒ az azonosítás
számtanilag is zár.

⇒ **A `date`/`description`/`location` beállító nem „a `CThumbDB` egy
metódusa", hanem az `IThumbDB` INTERFÉSZ 2/3/4. metódusa**, amit az
`IAlbumStore` is meghirdet. Ezért nincs egyetlen közvetlen hívása sem: a
hívó **interfész-mutatót** tart, nem `CThumbDB*`-ot.

### 11.3 A `CThumbDB` teljes objektum-kiosztása

A konstruktor (`FUN_00415790`, 7851 b) a `0x004157fd`–`0x00415827`
tartományban írja a vtábla-mutatókat; az értékek **bájtra egyeznek** az
RTTI `mdisp` értékeivel:

| eltolás | vtábla | bázis (RTTI) |
|---:|---|---|
| `+0x00` | `0x00c81f78` | `CThumbDB` / `ytBaseThread` / `IShouldExit` |
| `+0x48` (72) | `0x00c81fa4` | **`IThumbDB`** |
| `+0x4c` (76) | `0x00c820a8` | `IThumbnailSource`, `IThumbnailBase` |
| `+0x50` (80) | `0x00c820d0` | **`IAlbumStore`** |
| `+0x54` (84) | `0x00c820fc` | `IImageStore` |
| `+0x58` (88) | `0x00c821a0` | `IGetImage` |
| `+0x5c` (92) | `0x00c821c8` | `IVirtualFile` |
| `+0x60` (96) | `0x00c81ee8` / `0x00c81ef8` | **`ytINI::CallBack`** |
| `+0x64` (100) | `0x00c82648` | **`IAlbumPersistedCallback`** |

*(A további bázisok — `ytSafe` `+4`, `ytBase` `+4`, `ytCriticalBase` `+5` —
nem hoznak külön vtáblát.)*

⭐ **Két, eddig nem dokumentált szerep:** a `CThumbDB` egyben **`ytINI`
visszahívás** (`+0x60`) és **`IAlbumPersistedCallback`** (`+0x64`) is —
vagyis maga az adatbázis-osztály fogadja az ini-feldolgozó és az
album-perzisztálás értesítéseit.

### 11.4 Hol él a példány

A `FUN_00415790` konstruktornak **három** hívási helye van
(`0x00402fd3`, `0x00467d1b`, `0x0053ff35`). Az elsőnél a lefoglalt méret
**`0x34b0`** (13 488 bájt), és a kapott mutató az alkalmazás-objektum
**`+0x1034`** mezőjébe kerül (`0x00402fdc`).

A `.text`-ben **232** `mov reg, [reg+0x1034]` alakú olvasás van,
**108** függvényben ⇒ a `CThumbDB`-t a program egésze használja.

### 11.5 ⛔ KIMERÍTŐ NEGATÍVOK — pontosan meghatározott hatókörrel

Mindegyik a teljes `.text`-en (8 642 912 bájt, `0x00401000`-tól):

| amit kerestem | találat |
|---|---:|
| `e8` (közvetlen hívás) a három beállítóra | **0** |
| `e9` (ugrás) a három beállítóra | **3** (a 11.1 thunkjei) |
| `call dword ptr [reg+0x0c]` bármely regiszterrel | **0** |
| a beállítók címe adatként (vtábla) | 1–1 (csak `0x00c81fac/b0/b4`) |
| a thunkök címe adatként | 1–1 (csak `0x00c820d8/dc/e0`) |
| **`IAlbumStore` felvétele** (`[app+0x1034]` után `+0x50`) | **0** ⇒ a thunk-vtábla a gyakorlatban HALOTT |
| **`IThumbDB` felvétele** (`[app+0x1034]` után `+0x48`) | **71 hely, 49 függvény** |
| általános `mov r,[r+0x0c]` + `call r` (bármely osztály 3. rése) | **796 hely, 528 függvény** |

⇒ A bájtminta önmagában **nem** különíti el a hívót (528 függvény), de a
két halmaz metszete igen szűk.

### 11.6 A metszet — és egy TÉVES RIASZTÁS, ami tanulságos

Az `IThumbDB`-t felvevő 49 függvény és a 3. rést hívó 528 függvény
metszete **egyetlen** függvény: `FUN_006f5580` (544 b, az online album
törlésének megerősítője).

**Elolvasva: téves riasztás.** A függvény maga is `IThumbDB`-n át hívott
`CThumbDB`-metódus (`0x006f558f`: `mov esi, ecx`, majd `0x006f5593`:
**`lea edi, [esi - 0x48]`** — visszaszámol a valódi objektumra), és a
`0x006f55a8`-on lévő `mov edx,[eax+0x0c]` az **elsődleges** vtábla
(`0x00c81f78`) 3. rése, nem az `IThumbDB`-é.

⇒ **A `lea reg, [reg - 0x48]` a `CThumbDB` interfész-metódusainak
ujjlenyomata** — erre érdemes pásztázni, ha a következő kör a
`CThumbDB`-metódusokat akarja összegyűjteni.

### 11.7 Mit tud a következő kör — a KONKRÉT következő lépés

A 11.5 negatívjai együtt azt mondják: a beállító hívója **nem** az
`[app+0x1034]`-ből veszi az interfészt. Marad két lehetőség:

1. a hívó **tagváltozóban tárolja** az `IThumbDB*`-ot (valaki egyszer
   átadja neki), vagy
2. **paraméterként kapja**.

**A következő lépés ezért:** meg kell keresni, hol **tárolják el** az
`[app+0x1034] + 0x48` értéket (`mov [reg+N], reg` a felvétel után) — a 71
felvételi hely mindegyikén ellenőrizve —, és onnan a tárolót olvasó
osztályokban keresni a 3. rés hívását. Ez **nem** dekompilációt igényel,
csak a 71 hely átnézését.

### 11.8 A beállító alakja

`0x004460a0` prológusa: `[ebp+0x08]` az első veremargumentum,
**`[ebp+0x0c]` egy `double`** (`fld qword ptr [ebp+0x0c]`, `0x004460ba`)
⇒ a dátumot **OLE Variant lebegőpontos** alakban kapja, ahogy a
`.picasa.ini` `[Picasa] date=` sora is tárolja (99. kör).

### 11.9 Nyitott kérdések mérlege (11.)

`1 nyílt (ÖRÖKÖLT) · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| van-e a beállítónak ugró (thunk) hivatkozása | **LEZÁRVA** — igen, 1–1 db, 11.1 |
| melyik interfészhez tartozik a 2/3/4. rés | **LEZÁRVA** — `IThumbDB` (+72), thunkön át `IAlbumStore` (+80), 11.2 |
| mi a `CThumbDB` teljes objektum-kiosztása | **LEZÁRVA** — 11.3, két forrásból |
| hol él a példány | **LEZÁRVA** — `[app+0x1034]`, 11.4 |
| **melyik hívó süti el ELŐSZÖR a dátum-beállítót** | **NYÍLT (örökölt)** — de a keresési tér 528 → 0 releváns találatra szűkült az `[app+0x1034]` úton; a következő lépés a 11.7 (nem dekompiláció) |

## 12. ✅ MEGVAN a mappadátum-beállító MINDKÉT hívója (2026-09-05, #2304)

> **Bizalmi fok: megerősített.** A hívási helyek diszasszemblálva, az
> argumentumok (azonosító · `double` dátum · `bool`) a beállító prológusával
> (11.8) és egymással is összeérnek.

A munkasor legrégebbi nyitott kérdése — *melyik hívó süti el a
mappadátum-beállítót* — **lezárult**. Két hívó van, két külön céllal.

### 12.1 A beállító pontos szignatúrája

`0x004460a0` (`IThumbDB` 3. rés):

| argumentum | hol | mi |
|---|---|---|
| 1. | `[ebp+0x08]` | a mappa/album **azonosítója** |
| 2. | `[ebp+0x0c]` | a **dátum**, OLE Variant `double` |
| 3. | `[ebp+0x14]` | **`bool`** — kapcsolja a MÁSODIK tárolót |

A törzs:

```
0x004460e5  add esi, -0x48        ; vissza a valódi CThumbDB-objektumra
0x004460ea  call 0x004481e0       ; 1. tároló: az ADATBÁZIS — FELTÉTEL NÉLKÜL
0x004460ef  cmp byte ptr [ebp+0x14], 0
0x004460f3  je  0x00446184        ; ha a bool HAMIS → itt vége
0x004460fb… call 0x004543e0       ; 2. tároló: a `.picasa.ini` `date` kulcsa
```

*(A `0x004460cc`-en betöltött sztring szó szerint **`date`** — `0x00c80d7c`.)*

⭐ Az `add esi, -0x48` **független megerősítése** a 11.2-nek: a metódus
`this`-e az `IThumbDB` alobjektum, és a törzs számol vissza a `CThumbDB`-re.

### 12.2 A HELYI, automatikus hívó — `FUN_00441ac0` (110 b)

```
0x00441ae0  fldz · fcomp [esp+0x10]   ; ha a kapott dátum 0 → azonnal kilép
0x00441af7  fld qword [0xc7ccf8]      ; 949998.0 — a „nincs dátum" őrszem
0x00441b08  call 0x00441760           ; ← az AUTODATE-számoló (9. szakasz):
                                      ;   a mappa elemeinek LEGKORÁBBI ideje
0x00441b0d  test eax,eax · jne …      ; ha nem sikerült (üres mappa) → NEM ír
0x00441b17  push eax                  ; eax == 0  ⇒ a bool HAMIS
0x00441b18  mov eax,[edx+0x0c]        ; a 3. rés
0x00441b1b  sub esp,8 · fstp [esp]    ; a kiszámolt dátum
0x00441b21  push edi · mov ecx,esi · call eax
```

⇒ **A helyi mappa dátuma az `autodate` eredménye, és CSAK az adatbázisba
kerül — a `.picasa.ini`-be NEM** (a bool hamis).

**A három hívási helye** (kimerítő `e8`-pásztázás, 3 találat):

| hívó | mit tudunk róla |
|---|---|
| `FUN_00441e00` (207 b), hívás `0x00441ec0` | sztringjei: **„Folders on Disk"**, **„Other Stuff"** — az albumlista két gyűjtőkategóriája ⇒ **a mappa-felvételi út**; hívói: `0x0055ece0`, `0x0055ff80` |
| `FUN_004aa9f0` (1172 b), hívás `0x004aadc9` | hívója: `0x004a8a30` |
| `FUN_0055d320` (947 b), hívás `0x0055d41b` | sztringje: `IDS_NORENAME` ⇒ átnevezési út; hívói: `0x0055d120`, `0x0056bfd0`, `0x006db580`, `0x006f2e50` |

### 12.3 Az ONLINE albumok hívója — `FUN_006f2fc0` (1733 b)

```
0x006f33e5  call 0x0098bbe0       ; a beolvasott dátum érvényes-e
0x006f33ec  je  0x006f3413        ; ha nem → kihagyja
0x006f33ee  call 0x004a0d60       ; ← GetThumbDB() — 19 bájtos AKCESSZOR
0x006f33f3  fld qword [esp+0x90]  ; a hírcsatornából jövő dátum
0x006f3400  lea ecx,[eax+0x48]    ; IThumbDB*
0x006f3405  mov eax,[eax+0x0c]    ; a 3. rés
0x006f3408  push 1                ; ⇒ a bool IGAZ: DB **és** `.picasa.ini`
0x006f340a  sub esp,8 · fstp [esp] · push edx · call eax
```

Egyetlen hívója `0x006f3dd2`, a `FUN_006f3cd0`-ban
(`UploadManager::process_error`, „Failed to upload images") ⇒ az
**online album (Web Albums) szinkron** ága.

### 12.4 ⛔ MIÉRT nem találta meg négy korábbi pásztázás

Három, egymástól független ok — mindegyik módszertani tanulság:

1. **`GetThumbDB()` akcesszor** (`0x004a0d60`, 19 b:
   `mov eax,[0x00d67668]` → `[eax+0x1034]`). A hívási helyen tehát **nincs**
   inline `[app+0x1034]` olvasás ⇒ a 11.5 „71 felvételi hely" listája az
   online hívót **nem tartalmazta**.
2. **A helyi hívó MAGA is `CThumbDB`-metódus**, így a `this` már az
   `IThumbDB` alobjektum ⇒ **nincs `+0x48` igazítás** ⇒ minden `+0x48`-ra
   horgonyzott pásztázás elvétette.
3. A 3. rés hívása **bájtmintával nem szűrhető** (796 hely, 528 függvény).

**Ami eldöntötte — a hívás ALAKJA, nem a fogadó:** a beállító `double`-t vesz
a vermen, tehát a hívás elé kötelezően kikerül a
`sub esp, 8` + `fstp qword ptr [esp]` pár. Erre pásztázva:

| lépés | találat |
|---|---:|
| `sub esp,8` + `fstp [esp]` a teljes `.text`-ben | **356** |
| ebből 3. rés hívásával a közelben | **58** |
| ebből a beállító tényleges hívása (elolvasva) | **2** — a 12.2 és a 12.3 |

*(A 356-ból 2: a szűrés **az argumentum TÍPUSÁRA** épült. Ez általánosítható:
ha a keresett függvény lebegőpontos argumentumot vesz, a `fstp`-minta
erősebb szűrő, mint bármi, ami a fogadó objektumra horgonyoz.)*

### 12.5 Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| a mappa dátumának forrása felvételkor | az `autodate` = a mappa elemeinek legkorábbi ideje (`0x00441760`) | `ini/folder_date.py` — a `.picasa.ini` `date=` sorát olvassa/írja; **automatikus felvételkori számítás nincs mérve** | ld. #2304 |
| hova írja a helyi út | **csak az adatbázisba** (a bool hamis) | nálunk a `.picasa.ini` az igazságforrás | a különbség tudatos, ld. `dontesek.md` |
| hova írja az online út | adatbázis **és** `.picasa.ini` | nincs online album ág | hatókörön kívül |
| üres mappa | `0x00441760` hibát ad ⇒ **nem ír dátumot** | nem mérve | — |

### 12.6 Nyitott kérdések mérlege (12.)

`0 nyílt · 3 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| **melyik hívó süti el a mappadátum-beállítót** | ✅ **LEZÁRVA** — kettő: `FUN_00441ac0` (helyi, autodate, csak DB) és `FUN_006f2fc0` (online album, DB + ini) |
| mit jelent a beállító 3. argumentuma | **LEZÁRVA** — a `.picasa.ini`-írás kapcsolója (12.1) |
| miért nem találták meg a korábbi pásztázások | **LEZÁRVA** — akcesszor + interfész-`this` + bájtminta-zaj (12.4) |
| a `FUN_004aa9f0` és a `FUN_0055d320` pontos felhasználói forgatókönyve | **HATÓKÖRÖN KÍVÜL** — a hívási lánc megvan, de a felületi forgatókönyv megnevezése nem befolyásolja a #2304-et; a `Folders on Disk` út (a mappa-felvétel) igazolva van |

## 13. Az ellenőrzőösszeg-mód BELÉPÉSI PONTJA egyetlen, és `CThumbDB`-é (2026-09-05, #2435)

A munkasor tétele így szólt: *„mind a 29 jelölt `CThumbDB`-e?"* — a 121.
szakasz ugyanis egy **push-számláláson** alapuló jelöltlistából csak kettőt
olvasott végig kézzel. A kérdés eldőlt, **de nem a jelöltlistán keresztül**:
a hívási lánc egyedisége önmagában megadja a választ, számlálás nélkül.

### 13.1 A lánc — kimerítő, mindhárom szinten

| szint | cím | hány belépési pont |
|---|---|---|
| a **számoló** | `0x006b99f0` | **6** közvetlen `e8` hívó (`0x00424dd1`, `0x004282f7`, `0x004e3c13`, `0x00568206`, `0x00568336`, `0x00602084`) |
| a **módválasztó** | `0x004e3ab0` | **1** — `0x0042a832`, és ez a `0x0042a800` törzsében van |
| a **vtábla-metódus** | `0x0042a800` | **0** közvetlen hívó; a címe a **teljes fájlban egyetlen helyen** szerepel: `0x00c82184` |

`0x00c82184` a `0x00c820fc` vtábla **34. rése** — a `CThumbDB` 84-es
objektum-eltolású interfésze (COL `0x00cfa164`, 11.2). A vtábla 40 réses.

⇒ **A futásidejű módválasztásba egyetlen út vezet**, és az a `CThumbDB`
34. rése. Nincs másik hívó, nincs thunk, nincs másik vtábla.

### 13.2 A DÖNTŐ mérés: a hat argumentum egyedi

A `0x0042a800` **`ret 0x18`**-cal tér vissza ⇒ **hat verem-argumentum**.
Megkérdeztem az egész binárist, van-e másik ilyen 34. rés:

| pásztázás | jelölt 34. rés-cél | ebből `ret 0x18` |
|---|---|---|
| vtábla-fej szabállyal (175 vtábla ≥35 réssel) | 49 | **1** — `0x0042a800` |
| ⛳ **kontroll: fej-szabály NÉLKÜL** (minden pozíció, ahol 35 egymás utáni kódmutató áll) | **2233** | **1** — `0x0042a800` |

A kontrollpásztázás szándékosan **maximálisan megengedő**: nem követeli meg,
hogy a talált tömb valódi vtábla legyen. A ret-értéket mindig a függvény
**saját index-határain belül** olvastam, nem lineáris túlfutással.

Az indexben nem szereplő 13 találat egyike sem függvénykezdet — kézzel
ellenőrizve: `0x00558000` egy törzs közepe (`je`-vel kezdődik),
`0x00920fec` **maga a `ret 0x18` bájtsorozat** (egy másik függvény farka),
`0x0092223a` értelmezhetetlen (`xchg`, majd `int3` kitöltés).

⇒ **Bármely hatargumentumú, 34. résen át menő hívás csak a `0x0042a800`-ra
mutathat**, az pedig egyetlen vtáblában él. **A jelöltek `CThumbDB`-k —
megerősített.** *(A kérdés per-hívóhelyes fogadó-elemzés nélkül eldőlt.)*

### 13.3 ⛔ HELYESBÍTÉS: a „29 jelölt" szám nem reprodukálható

A 121. szakasz **29** jelöltet említ (10 literál `0`, 5 literál `1`, 14
futásidejű). Újramérve a szám **a számlálási szabálytól függ**:

| szabály | jelölt |
|---|---|
| push-ok csak a `mov`↔`call` közti 48 bájtban | **17** |
| push-ok a bázisblokk határáig visszafelé | **27** |
| ugyanaz, de a **prológus-regisztermentéseket** levonva | **21** |

A hiba forrása megnevezhető: kilenc találatnál a „hat push" valójában a
**függvény prológusa** volt (`push ebp/ebx/esi/edi` a függvény első ~30
bájtjában), nem argumentum — pl. `0x0043242e` a `0x00432410`-es függvény
30. bájtján áll.

**Ezért a jelöltszám nem is hordoz bizonyítékot** — a 13.2 uniqueness-mérése
igen. A számot ne idézze senki tényként; a 121. szakasz **következtetése**
viszont áll, mert az a *literál* argumentumokon nyugszik, és azok stabilak:
mindhárom számlálási szabály ad **literál `0`**-t adó hívóhelyeket, köztük a
két kézzel végigolvasott `FUN_0042f6a0` (`0x0042f6c0`) és `FUN_00793720`
(`0x00793740`) — mindkettő üres sztringgel (`0x00c7f979`).

### 13.4 A hívás alakja (a két végigolvasott hívóhelyről, MÉRVE)

```
push <kimeneti puffer>   ; arg6
push 0                   ; arg5
push 1                   ; arg4
push 1                   ; arg3
push 0                   ; arg2  <- a MÓD (0 ⇒ a 2. ellenőrzőösszeg-mód)
push <azonosító>         ; arg1
mov  ecx, <CThumbDB+84>  ; this — a másodlagos felület
call [vtábla+0x88]
```

A `0x0042a800` prológusa ezt megerősíti: `mov esi,[ebp+8]` (arg1),
`mov eax,[ebp+0xc]` (arg2), és később `mov byte ptr [ebp+0xc], 0` — az arg2
**bájtként** íródik ⇒ logikai kapcsoló. Minden literál hívóhely `0`-t vagy
`1`-et ad, ami ezzel összefér.

**Bizonyítottsági fok:** a 13.1 és a 13.2 **megerősített** (kimerítő
pásztázás + kontroll); a 13.4 alakja **megerősített** két hívóhelyen,
**erős** a többin (a hívott függvény egyedisége miatt).

### 13.5 Nálunk (MÉRVE)

`src/picasapy/pmpimport/thumbindex.py:169` — a `SlotIndexEntry.checksum`
mezőt **beolvassuk**, de sehol nem **számoljuk ki** és nem hasonlítjuk
össze: a `grep -rn "checksum" src/ --include=*.py` a `thumbindex.py`-n
kívül egyetlen érdemi találatot sem ad, és a mezőt egyedül a
`tests/pmpimport/test_thumbindex_farok_2195.py` érinti. Egyik mód képlete
sincs megvalósítva. → jegy **#2435**.

### 13.6 Nyitott kérdések mérlege (13.)

`0 nyílt · 2 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| **mind a jelölt hívóhely `CThumbDB`-e?** | ✅ **LEZÁRVA** — igen, a 13.2 egyediség-mérése alapján; per-hívóhelyes elemzés nem kell |
| a „29 jelölt" szám helyessége | ✅ **LEZÁRVA (megdőlt)** — a szám szabályfüggő (17/21/27); nem bizonyíték, és nem is szükséges (13.3) |

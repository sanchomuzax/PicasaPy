# A Picasa 3 indulása — a lépéssor a binárisból

**Kérdés:** visszafejthető-e, milyen lépések történnek induláskor? **Igen.**
Ez a lap a mért lépéssort tartalmazza. Párja a `picasa-bezaras-es-kilepes.md`
— eddig a kilépésről volt lapunk, az indulásról nem.

*Bizonyítottsági fok: **megerősített** minden felsorolt lépés (a bináris
index `string_xrefs`/`xrefs` tábláiból és a hivatalos `stringres-en-hu.tsv`-ből).
**Feltételes** a lépések EGYMÁS UTÁNI SORRENDJE — az index a hivatkozásokat
függvényenként adja, nem utasítás-sorrendben. A sorrend eldöntéséhez a
`0x004051b0` diszasszemblálása kell.*

## 1. A hívási lánc teteje

| cím | szerep |
|---|---|
| `0x00401060` | a legkülső burkoló |
| `0x00402960` | vékony burkoló, egyetlen hívása a parancssor-kezelő |
| `0x004bc0c0` | **parancssor- és protokoll-kezelő** |
| `0x004051b0` | **az indulási mag** — a lenti lépések döntő része itt van |
| `0x00406770` | **korábbi telepítés adatainak keresése** (Windows.old) |
| `0x0040b410` / `0x0040b420` | `SplashThread` + az indítókép |

## 2. Parancssor és protokoll (`0x004bc0c0`)

Regisztrációs gyökér: `SOFTWARE\Google\Picasa\`; az előző indítás
argumentumai a **`PreviousArgs`** kulcsba kerülnek.

| kapcsoló / ige | jelentés |
|---|---|
| `/nosplash` | indítókép nélkül |
| `/norestart` | nincs újraindítás |
| `/register`, `/unregister` | héj- és protokoll-regisztráció |
| `/resamplefile` | egyetlen fájl átméretezése (fejsze-mód, felület nélkül) |
| `/StiDevice` | **Still Image** eszköz — a kamera csatlakoztatására indul |
| `email`, `print`, `locate` | igék: közvetlenül egy műveletre indul |
| `picasa://` | saját protokoll-séma |
| `P2GetImageCmd` | kép-lekérési parancs (héj-integráció) |

## 3. Az indulási mag lépései (`0x004051b0`)

### 3.1 Indítási kapuk — mikor NEM indul el

| kulcs | hatás |
|---|---|
| `Picasa2Installing` | telepítés közben nem indul |
| `Picasa2NoLaunch` | az indítás letiltva |

### 3.2 Környezet-előfeltételek, saját üzenettel

| erőforrás | magyar szöveg |
|---|---|
| `IDS_MIN_RES_MSG` | „Ez az alkalmazás legalább 800x600-as képernyőfelbontást igényel 16 bites színmélységgel." |
| `IDS_MMX_MSG` | „Ez az alkalmazás MMX használatára képes processzort igényel." |

A Picasa tehát **ellenőrzi a képernyőt és a processzort, és inkább nem indul el**,
mint hogy rosszul fusson. (Az MMX-feltétel mai gépen tárgytalan.)

### 3.3 Útvonalak és beállítások

`AppLocalDataPath` (a `Preferences` alatt) → `Google\Picasa2` adatmappa;
`AppPath` + `Picasa3.exe` a futtatható útvonala; `Runtime` a
`SOFTWARE\Google\Picasa\Picasa2\Runtime\` alatt (`0x00513d70`, `0x00513e70`).

### 3.4 Nyomkövetés — opcionális naplófájl

`UseTraceFile` = igaz → **`picasatrace.txt`**. Kapcsolóval bekapcsolható
részletes napló; alapból nem ír ilyet.

### 3.5 Honosítás és futásidejű erőforrások

`Picasa3i18n.dll` → `i18n\stringres.xml`, `i18n\langnames.xml`;
majd `runtime\filterdesc.xml` és a `runtime\picnik_effects\` mappa.
**Az effektek receptje tehát INDULÁSKOR töltődik**, nem első használatkor.

### 3.6 Egyéb

- `singlecpu` — egymagos működés kényszerítése (CPU-affinitás)
- `LastUpdateCheck` — a frissítés-ellenőrzés időbélyege
- `{6319A989-7DDA-46C6-8F5F-DAE4E69E48D7}` — GUID, csak itt és a
  `0x004deab0`-ban fordul elő; **feltételesen** az egypéldány-mutex vagy a
  frissítő COM-osztálya. Nincs megmérve, melyik.

## 4. Korábbi telepítés adatainak keresése (`0x00406770`)

Az indulás **két** helyen keres korábbi Picasa-adatot egy megelőző
Windows-telepítésből (a `$$` a felhasználónévre álló helyettesítő):

```
C:\Windows.old\Documents and Settings\$$\Local Settings\Application Data\Google\   (XP-alak)
C:\Windows.old\Users\$$\AppData\Local\Google\                                      (Vista+ alak)
```

és ezeken belül a `Picasa2Albums` mappát, valamint a `#db3\` adatbázist.

Ez **külön funkció** attól, amit a #1402 leír (az adatbázis áthelyezése):
ott a felhasználó mozgatja a saját adatbázisát, itt a program **magától
átveszi** egy korábbi rendszertelepítés adatait.

## 5. Nálunk (mérve, 2026-08-27, `src/picasapy/app/application.py`)

| lépés | eredeti | nálunk |
|---|---|---|
| egypéldány-zár | GUID (feltételes) | ✅ `_acquire_instance_lock` (`:346`) |
| indítókép | `SplashThread`, `/nosplash` | ✅ `_remaining_splash_ms` (`:435`) |
| adat-/gyorsítótár-/beállításmappa | `AppLocalDataPath` | ✅ `_data_dir`/`_cache_dir`/`_config_dir` (`:231`–`:256`) |
| tárolás előkészítése | — | ✅ `_bootstrap_storage` (`:261`) |
| első beolvasás | — | ✅ `_start_initial_scan` (`:443`) |
| hibanapló felajánlása | ✅ (#449) | ✅ `_offer_error_log` (`:322`) |
| **környezet-előfeltétel** | 800×600/16 bit + MMX, saját üzenettel | ❌ nincs |
| **indítási kapuk** | `Picasa2Installing`, `Picasa2NoLaunch` | ❌ nincs |
| **nyomkövetési kapcsoló** | `UseTraceFile` → `picasatrace.txt` | ❌ nincs (az `error_log.py` szándékosan tömör) |
| **korábbi telepítés átvétele** | Windows.old, két alak | ❌ nincs |
| frissítés-ellenőrzés | `LastUpdateCheck` | ❌ nincs (nem is kell — nem frissítünk így) |

## 6. Nyitott kérdés

**A lépések pontos SORRENDJE.** Az index függvényenként adja a
hivatkozásokat, nem utasítás-sorrendben, ezért a fenti csoportosítás
tematikus, nem időrendi. Aki a sorrendre épít, annak előbb a `0x004051b0`-t
kell diszasszemblálnia (`annot_disasm.py 0x004051b0 <méret>`).

# A Picasa 3 indulása — a lépéssor a binárisból

**Kérdés:** visszafejthető-e, milyen lépések történnek induláskor? **Igen.**
Ez a lap a mért lépéssort tartalmazza. Párja a `picasa-bezaras-es-kilepes.md`
— eddig a kilépésről volt lapunk, az indulásról nem.

*Bizonyítottsági fok: **megerősített** minden felsorolt lépés (a bináris
index `string_xrefs`/`xrefs` tábláiból és a hivatalos `stringres-en-hu.tsv`-ből).
**Feltételes** a 3. fejezet teljes lépéssorrendje. Az index a hivatkozásokat
függvényenként adja, nem utasítás-sorrendben. A `0x004051b0` célzott
diszasszemblálása a 6. fejezet indítókép-sorrendjét megerősíti; a teljes
indulási út utasításszintű sorrendje továbbra sincs kibontva.*

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
| egypéldány-zár | GUID (feltételes) | ✅ `_acquire_instance_lock` (`:347`) |
| indítókép | `SplashThread`, `/nosplash` | ✅ `_remaining_splash_ms` (`:435`) |
| adat-/gyorsítótár-/beállításmappa | `AppLocalDataPath` | ✅ `_data_dir`/`_cache_dir`/`_config_dir` |
| tárolás előkészítése | — | ✅ `_bootstrap_storage` (`:262`) |
| első beolvasás | — | ✅ `_start_initial_scan` (`:444`) |
| hibanapló felajánlása | ✅ (#449) | ✅ `_offer_error_log` (`:323`) |
| **környezet-előfeltétel** | 800×600/16 bit + MMX, saját üzenettel | ❌ nincs |
| **indítási kapuk** | `Picasa2Installing`, `Picasa2NoLaunch` | ❌ nincs |
| **nyomkövetési kapcsoló** | `UseTraceFile` → `picasatrace.txt` | ✅ **van, 2026-08-27 óta**: a #1601 indulási idővonala (`perf/startup_timeline.py`, `start_startup_timeline`), alapból kikapcsolva — ugyanaz a minta. A #1654 óta a kapcsoló TARTÓS is (`Súgó ▸ Tesztüzem`, `QSettings` `diagnostics/tesztuzem`, `--tesztuzem`), tehát az eredetihez hasonlóan a KÖVETKEZŐ indulás naplózható — ez az eredeti `UseTraceFile` registry-kapcsolójának pontos megfelelője |
| **korábbi telepítés átvétele** | Windows.old, két alak | ❌ nincs |
| frissítés-ellenőrzés | `LastUpdateCheck` | ❌ nincs (nem is kell — nem frissítünk így) |

## 6. Az indítókép

**Bizalmi fok: feltételes a teljes indítókép viselkedésére.** A szál indítási hívása,
a `ytWindow` osztály és ablaktulajdonságai, a `/nosplash` kapu, valamint a
háttérfájl tartalma két, egymástól külön bejárt bizonyítékúttal megerősített.
Az első ténylegesen kirajzolt képkocka megelőzi-e a főablak első képkockáját, a
teljes rajzolt tartalom, a natív ablak végső mérete és a vizuális eltűnés
pontja futásidejű mérés vagy a lent kért célzott Ghidra-kör nélkül nyitott.

### Indítás és sorrend

A `0x004051b0` indulási mag `0x004058e9` utasítása hívja a `0x00403970`
indítókép-kaput. Ez a `Preferences/usesplashscreen` beállítást alapérték
`1`-gyel olvassa, és a `0x0040beb0`-n keresztül létrehozza, majd a
`0x0097b350` szálindítóval elindítja a `SplashThread` objektumot. A
`0x0040beb0` a `SplashThread::vftable` címét (`0x00c808e4`) írja az
objektumba. A szálindító a `CreateThread` Win32 függvényt hívja.

Ugyanebben a `0x004051b0` függvényben a `0x004058e9` után következik a
`0x004058ef` hívás, majd a `0x0040590e` címen a `0x004039f0`. Ez utóbbi
hozza létre a `ytFrameWindow` főablak-objektumot; a `ytWindow` alap-
konstruktor natív ablakot hoz létre. A hívási sorrend tehát azt bizonyítja,
hogy a splash szál indítása a főablak létrehozási útja előtt van. A
`CreateThread` aszinkron, ezért a szál első képkockájának tényleges
megjelenési sorrendje nem állapítható meg pusztán a hívási sorrendből.

### Ablak és elhelyezés

A `0x0040b420` rajzoló rutin a `0x00982bf0` konstruktorral `ytWindow`
objektumot hoz létre `splash` címmel, majd meghívja az objektum vtable
`+8` metódusát (`0x00983840`), amely a már létrehozott HWND-t
`ShowWindow`-val megjeleníti.

A létrehozó út 1-es ablakmódján a `CreateWindowEx`-nek megfelelő
függvénymutató-hívás paraméterei: stílus `0x84000000`, kiterjesztett stílus
`0x80`, osztálynév `ytWindow`, cím `splash`, szülőablak `0`. A stílus
`WS_POPUP | WS_CLIPSIBLINGS`, a kiterjesztett stílus `WS_EX_TOOLWINDOW`;
címsor- és keretstílus nincs beállítva, és `WS_EX_TOPMOST` sincs a
létrehozási stílusban. Külön `HWND_TOPMOST` elhelyezést a splash útvonalán
nem azonosítottam. Ez tehát keret nélküli felugró ablak, amelynek
mindig felül viselkedése nincs igazolva.

A `0x0040b420` `SystemParametersInfoA` hívása `0x30` paraméterrel lekéri a
képernyő munkaterületét, majd a létrehozási téglalap helyét annak közepéhez
számolja. A `splashbk.jpg` fájl mért mérete `640x235` képpont. A natív
ablak végső pixelmérete `NINCS MEG`: a rutin a képet egy belső rajzi
transzformáción át dolgozza fel a HWND téglalapjának átadása előtt, és ezt
a kimeneti méretre gyakorolt hatást még nem mértem ki.

### Mit rajzol

A betöltött háttérút a `runtime\\splashbk.jpg` (`0x0040b4fd`). A
`Picasa3/runtime/splashbk.jpg` eredeti fájl `640x235` képpont, `44 195`
bájt, RGB JPEG. A megnyitott képen fehér mezőn a Picasa 3 embléma és a
Google szójel látható.

A rajzoló kód a `splash` nevű `ytWindow` objektumot nagy pontosságú
időmérést használó képkocka-útba köti, tehát nem csak egy nyers JPEG
egyszeri másolásáról van szó. A célzott diszasszemblálás közvetlen szövegei
a `Preferences`, `usesplashscreen`, `runtime\\splashbk.jpg` és `splash`;
dinamikus verzió-, szerzői jogi vagy állapotszöveget, betűtípust, színt és
az ilyen szövegek helyét nem azonosítottam. Ezek `NINCS MEG` értékek, nem
negatív bizonyítékok.

### Eltűnés és `/nosplash`

A `0x0040bcf0` futtató a `0x0040b420` rajzolót hívja, majd az animációs
objektum állapotát figyeli; várakozáskor `PeekMessage` és `Sleep(0x64)`
ciklust használ. A `100 ms` a ciklus szünetének bináris értéke, nem a
splash teljes ideje. A `0x00403970` a `0x0040bf20` takarítófüggvényt
regisztrálja, a későbbi főablak-indítási út pedig felszabadítja a
`SplashThread` objektumot. Fix időzítőt a splash teljes idejére,
főablak-megjelenéshez kötött kifakulást vagy a pontos utolsó képkockát nem
bizonyítottam. A dinamikus komponens lezárási feltétele nyitott.

A `/nosplash` kapcsolat megerősített két külön függvényből:

1. A `0x004bc0c0` parancssor-elemző a `/nosplash` egyezésekor az átadott
   struktúra `+4` mezőjét `1`-re állítja (`0x004bc4a9`, `0x004bc4f1`).
   Hívója `0x00402960` a külső indítási struktúra `+4` címét adja át.
2. A `0x00403970` az indítási struktúra `+8` mezőjét ellenőrzi, és nem
   hívja meg a `0x0040beb0` szálindítást, ha a mező nem nulla
   (`0x004039d2`-`0x004039d7`). A parser belső `+4` mezője így a külső
   `+8` mezőnek felel meg.

A `Preferences/usesplashscreen` beállítás ettől független kapu, alapértéke
`1`. A rajzoló ezen felül egy billentyűállapot-ellenőrzést is végez;
annak pontos jelentése nem része a `/nosplash` kapcsoló bizonyítékának.

### Összevetés a PicasaPy-vel

| Eredeti Picasa 3 | PicasaPy jelenlegi indulóképe | Eltérés |
|---|---|---|
| Külön `ytWindow` felugró ablak, saját szálból indítva, a főablak létrehozása előtt | `SplashScreen.qml` elem a QML `ApplicationWindow` rétegén | Nincs vizuális indulókép a fő QML ablak betöltése előtt |
| `splashbk.jpg`, fehér háttéren Picasa 3 embléma és Google szójel | PicasaPy logó, címkártya és téma szerinti háttér | Az eredeti márkajelzés és képkivágás hiányzik |
| Esetleges animációs és szövegréteg még nyitott | Verzió, indulási állapotszöveg, pulzáló pontok, mozgó kék sáv | A PicasaPy biztosan ezeket rajzolja; az eredeti dinamikus tartalom nem bizonyított |
| Az eredeti végső méret és eltűnési animáció nyitott | Kész állapotkor 260 ms-os QML opacitás-animáció | Az eredeti viselkedéshez való egyezés még nem mérhető |

A `Main.qml` `visible: true` ablaka a QML-fa betöltésével jön létre; a
`SplashScreen` csak a `MainWindowPeripheralLayers` részeként létezik. A
`StartupStatus` híd korábban létrejön, de maga a vizuális elem nem létezhet
a `Main.qml` betöltése előtt. A felület jelenlegi formája ezért nem pótolja
az eredeti külön, korábban megjelenő felugró ablakot.

### Nyitott kérdések és következő bináris irány

- A `0x0040b420` teljes rajzi tartalma: van-e a képen kívül verzió-,
  szerzői jogi vagy állapotszöveg; ha van, milyen betű, szín és koordináta.
- A belső képi transzformáció pontos kimeneti mérete és az ablak tényleges
  pixelmérete.
- A `splash` grafikai komponens lezárása, a szál leállításának oka és az
  utolsó képkocka viszonya a főablak megjelenéséhez.

Ghidra-kör kell: 0x0040b420 - a splash ytWindow pontos rajzi tartalma,
transzformációs mérete és animációs lezárási feltétele; a diszasszemblálás
nem azonosította a virtuális grafikai hívások szerepét [blokkoló]

A már létező Ghidra-kimenet a `0x00982bf0` `ytWindow` konstruktorát, a
`0x00983670` létrehozó útját és a `0x004039f0` főablak-építését tartalmazza.
A címekre új kört csak a `0x0040b420` új, eddig meg nem válaszolt
rajzolási kérdésére kérünk; a 40b420 korábbi kimenetei csak hivatkozáslistát
adnak, nem függvénydekompilálást.

## 7. Helyesbítés — a lap egyik sora már íráskor elavult

A 5. szakasz „nyomkövetési kapcsoló" sorát **eredetileg „nincs"-re írtam**.
Húsz perccel korábban azonban beolvadt a #1601 (`perf: indulási idővonal`),
amely pontosan ezt a mintát vezette be: alapból kikapcsolt, opcionálisan
bekapcsolható indulási napló. A sor javítva.

Ez a lap saját példája a projekt szabályára: **a mért állapot romlandó**. Aki
ebből a táblából dolgozik, a „nálunk" oszlopot mérje újra, ne vegye készpénznek.

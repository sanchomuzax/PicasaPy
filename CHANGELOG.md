# Változásnapló

A projekt a [Semantic Versioning](https://semver.org/) elvét követi; a `0.x`
sorozat instabil. A teljes, gépi generálású kiadási jegyzék a
[Releases](https://github.com/sanchomuzax/PicasaPy/releases) oldalon él — ez a
fájl a lényegi, ember által írt kiemeléseket rögzíti.

## [0.4.51] – 2026-07-23

### Javítva
- **Stabil szintetikus golden-alapképek (#278):** a `make_golden_kit.py`
  `synthetic_photos` már nem tesz ±12-es egyenletes zajt a fotószerű
  alapképekre — a zaj a Picasa JPEG-újratömörítése után felfújta a
  golden-diffet a sima tartalmú képeken („eltér" ítélet), miközben a
  chart-alapképek pixelhűek maradtak. Így a tónus-szűrők szintetikus
  fotó-alapképen is értelmes golden-számot adnak.

## [0.4.50] – 2026-07-23

### Hozzáadva
- **Élő haladás-jelző a golden-harnessben (#115):** a `compare_render.py`
  a stderr-en `[index/össz]` számlálót ír képenként — a több perces (nagy
  kit, OneDrive) futás így láthatóan halad, nem tűnik „némán állónak".

## [0.4.49] – 2026-07-23

### Javítva
- **A golden-harness ékezetes útvonalon is olvas (#115):** a
  `compare_render.py` a közös `picasapy.cvimage` bájt-alapú beolvasóját
  használja a cv2.imread helyett — a Windows-os néma Unicode-elnyelés
  (#65/#190 tanulság) itt is kifogva.

## [0.4.48] – 2026-07-23

### Javítva
- **Golden-kit generátor Windowson, fotók nélkül is (#115):** a
  `make_golden_kit.py` fotómappa-argumentuma elhagyható, kevés/hiányzó
  fotónál szintetikus fotó-alapképekkel pótol; OneDrive-tűrő kimenet-
  előkészítés; a harness-doksi példái egysorosak, létező útvonalakkal.

## [0.4.47] – 2026-07-23

### Hozzáadva
- **A Picasa 3.9-es 4–5. effekt-fül mind a 23 `filters=` kulcsa azonosítva
  (#190):** a felhasználó valódi Picasájából gyűjtött mintákból — kulcs-
  táblázat a `filters-decoded.md`-ben, round-trip tesztek a valódi
  láncokkal. A paraméter-jelentések feltérképezése a 2. (gépi) kör dolga.

### Eltávolítva
- `PicasaPy-indito.bat` (felhasználói kérésre).

## [0.4.46] – 2026-07-23

### Hozzáadva
- **`PicasaPy-indito.bat` a repó gyökerében:** dupla kattintásra frissíti
  (git pull) és elindítja az appot Windowson — a felhasználónak nem kell
  parancsokat és mappákat fejben tartania; hibánál emberi nyelvű üzenet.

## [0.4.45] – 2026-07-23

### Javítva
- **Golden-kit ékezetes útvonalon is (#190):** Windowson a cv2 képírás/
  -olvasás némán elnyeli a nem-ASCII útvonalat (pl. „Képek") — a chart-
  képek nem jöttek létre, a generálás érthetetlen helyen bukott. Mostantól
  a kép-IO memóriában kódol (imencode/imdecode), az útvonalat Unicode-
  biztos Python-IO kezeli.

## [0.4.44] – 2026-07-23

### Javítva
- **Golden-kit OneDrive-mappában is (#190):** a meglévő kimeneti mappa
  törlése OneDrive-zárolásnál (WinError 5) eddig elszállt; mostantól
  csak-olvasható attribútum-levétellel és újrapróbálkozással törlünk, ha
  pedig így sem megy, a generálás a meglévő mappába felülírással fut le —
  a kit a felhasználó által választott (akár OneDrive alatti) helyen készül el.

## [0.4.43] – 2026-07-23

### Javítva
- **Golden-kit fotókönyvtár nélkül is (#190):** a
  `make_golden_kit_effects.py` eddig kötelezően valódi fényképet keresett
  a forrásmappában, és üres mappánál elszállt (`IndexError`). Mostantól a
  fotó-argumentum elhagyható, üres mappánál pedig fotószerű szintetikus
  képet generál — a kit pusztán a kimeneti mappa megadásával elkészül.

## [0.4.42] – 2026-07-23

### Hozzáadva
- **100k-s feed-stresszmérés (#142):** ismételhető benchmark-szkript +
  env-kapcsolós stresszteszt a valódi rácson, dokumentált eredményekkel
  (`docs/benchmarks/feed-100k-stressz.md`) — 100 000 fotónál a rács
  0,21 s alatt betölt, a példányosított cellaszám 42–54 közt korlátos,
  a memóriatöbblet ~66 MB; ezzel a #142 teljesítmény-jegy minden pontja
  igazoltan teljesül.

## [0.4.41] – 2026-07-23

### Hozzáadva
- **Golden-kit az új effekt-fülekhez (#190):** `make_golden_kit_effects.py`
  — a Picasa 3.9-es 4–5. effekt-fül mind a 23 effektjéhez beszédes nevű
  referencia-képeket generál (csúszkás effekteknél több beállítással),
  magyar lépésenkénti útmutatóval (`UTMUTATO.md`) a Windows-os Picasában
  végzendő adatgyűjtéshez — ez alapozza meg a `filters=` kulcsok
  dekódolását.

## [0.4.40] – 2026-07-23

### Hozzáadva
- **Teljes Mappakezelő a Picasa 3 mintájára (#231):** önálló, mozgatható/
  átméretezhető ablak OK/Mégse gombokkal; bal oldalon a helyi mappastruktúra
  lusta betöltésű fája állapot-ikonokkal, jobb oldalon háromállapotú választó
  (Keresés mindig / Keresés egyszer / Eltávolítás a Picasából) és a figyelt
  mappák összegző listája; a „Keresés egyszer" egyszeri szkennelést végez
  figyelés nélkül, ahogy az eredeti Picasában.

## [0.4.39] – 2026-07-23

### Javítva
- **Windows-telepítő parancsikonokkal (#67):** az `install.bat` a telepítés
  után Asztal- és Start menü-parancsikont hoz létre a PicasaPy-ikonnal —
  a taskbar-ikon javításának (AppUserModelID, korábban a main-ben) kézzel
  fogható kiegészítése; a végleges .exe-be ágyazott ikon a jövőbeni
  Windows-csomagolási munka része.

## [0.4.38] – 2026-07-23

### Javítva
- **Automatikus csomag-assetek a release-eken (#256):** a `package.yml`
  mostantól a Release workflow lefutása után magától elkészíti és feltölti
  a wheel/sdist/.deb/Windows-zip asseteket (a GITHUB_TOKEN
  rekurzióvédelme miatt a korábbi `release: published` trigger sosem
  sült el); kézi `workflow_dispatch` pótlásra továbbra is használható.

## [0.4.37] – 2026-07-23

### Hozzáadva
- **Gyorscímkék a Címkék-panelen (#193):** 8 konfigurálható gomb (2×4)
  egykattintásos címkézéshez, fogaskerékkel nyíló konfigurációs ablak —
  a felső két gomb automatikusan a legutóbb használt címkéket követi
  (kikapcsolható), az üres mezők gyakran használt címkékkel tölthetők fel;
  a beállítások megőrződnek.

## [0.4.36] – 2026-07-23

### Hozzáadva
- **Csomagolás (#4):** `pip install .`/pipx-telepítés működő `picasapy`
  paranccsal (entry point + QML/ikon/fordítás a wheelben); új `packaging/`
  könyvtár Debian-csomag (.deb) és Windows-zip összeállító szkriptekkel,
  magyar build-útmutatóval; release-publikáláskor a csomagok automatikus
  feltöltése release-assetként (`package.yml`).

## [0.4.35] – 2026-07-23

### Hozzáadva
- **Drag & drop import (#237):** képet az ablakra húzva a kép mappája
  (mappát húzva maga a mappa) figyelt gyökér lesz — deduplikálva, egymásba
  ágyazott utaknál a legfelsővel; nem támogatott elemről visszajelzés-buborék.
- **Tulajdonságok-panel az egyképes nézőben is (#192):** a könyvtár-nézet
  kapcsolóját követi, lapozásra frissül.

### Javítva
- **Ablakpozíció/-méret megjegyzése (#192):** záráskor mentés, induláskor
  visszaállítás — lecsatolt monitor és hibás adat elleni védelemmel;
  maximalizált zárásnál a normál geometria is megőrződik.

### Dokumentáció
- CONTRIBUTING: a feladat-ciklus végének pontosítása (a vállaló session a
  merge–issue-zárás–verzió-bump körig felelős; integrátor híján maga veszi
  át az integrátor szerepet) + i18n-regen buktató rögzítése.

## [0.4.34] – 2026-07-22

### Hozzáadva
- **„Félkész szoftver" figyelmeztetés az indítóképernyőn (#243):** amíg az
  eredeti Picasa effekt-készlete nincs teljesen implementálva, a betöltés
  végén a splash figyelmeztetést és OK gombot mutat — csak az OK
  megnyomása után záródik be, és addig a mögöttes felület nem kattintható.

## [0.4.33] – 2026-07-22

### Javítva
- **Indítóképernyő (#240, éles hibajelentés):** Windowson egyáltalán nem
  látszott — a betöltés az ablak első kirajzolása előtt lezajlott és a
  splash már kifakulva jelent meg; mostantól az első képkocka után indul,
  és legalább 1,5 másodpercig látható. Debianon a hiányzó logó összeejtette
  a kártyát — a logónak fix magassága és raszteres tartalék-képe van, a
  kártya magassága pedig nem függ a kép betöltésétől.

## [0.4.32] – 2026-07-22

### Hozzáadva
- **Indítóképernyő (#189):** PicasaPy-logós splash screen verziószámmal,
  animált betöltési állapotszöveggel és kék „foglalt"-sávval; az app
  használatra kész állapotánál magától eltűnik.
- **`.picasa.ini` ütközésvédelem (#137):** a párhuzamosan futó eredeti
  (Windows-os) Picasa írásai többé nem veszhetnek el — mentés előtti
  ütközés-ellenőrzés, ütközésnél a módosítás biztonságos újrajátszása.
- **Hisztogram-referenciacsomag (#236):** determinisztikus tesztképek és
  automata ellenőrzés a hisztogram-skála Picasa-összevetéséhez.

### Javítva
- **Hisztogram-doboz (#235):** a cím nem vágódik el (2 sorba törhet), a
  fényképezőgép-adatok az eredeti Picasa kétoszlopos, címkézett
  elrendezését követik (35 mm-egyenértékkel).
- **Windows taskbar-ikon (#67):** több méretű `icon.ico` — a hol
  megjelenő / késleltetett taskbar-ikon tünete ellen.
- **Magréteg-duplikációk (#151):** közös kép-segédmodul és ini-helper —
  kevesebb ismétlődő kód, egységes viselkedés.

## [0.4.31] – 2026-07-21

### Javítva
- **Hisztogram VÉGRE rajzol (#232, éles hibajelentés):** a görbe eddig
  soha nem jelent meg — a valódi ok az volt, hogy a csatorna-értékeket
  tuple-ként adtuk át QML-nek, ami ott nem tömbként látszott, így a rajzoló
  minden csatornát kihagyott (a #25/#228 a Canvas-időzítést gyanította,
  tévesen). A vödör-listák mostantól listák, a törékeny Canvas helyett
  pedig mindig-renderelő téglalap-oszlopok rajzolják a kitöltött RGB-görbét,
  címmel; EXIF hiánya esetén „Nincs elérhető EXIF-adat." felirattal.

## [0.4.30] – 2026-07-21

### Javítva
- **Hisztogram azonnal rajzol (#228, éles hibajelentés):** a görbe a kép
  megnyitásakor rögtön megjelenik a megjelenített képből számolva, EXIF
  nélküli képnél is — nem kell hozzá csúszka-mozdulat; a
  „Nincs elérhető fényképezőgép-adat" felirat magyarul jelenik meg.

## [0.4.29] – 2026-07-21

### Javítva
- **Kijelölés-stabilitás (#135):** a kijelölés a fotókat követi, nem a
  sorszámokat — háttér-frissítés közben sem csúszhat át a csillagozás/
  forgatás/export egy másik képre; a korábban flaky navigációs tesztek
  determinisztikusak.

### Hozzáadva
- **Élő hisztogram + fényképezőgép-adatok (#25):** a néző bal alsó doboza
  élesedett — RGB-hisztogram a ténylegesen megjelenített (szerkesztett)
  képből, élő frissítéssel a csúszkák húzása közben, alatta a gép,
  expozíció, rekesz, ISO, gyújtótávolság és vaku adatai.
- **Picasa widget-króm a teljes felületen (#3):** minden görgetősáv és
  csúszka (videó-lejátszó, szerkesztő-panel, tálca) az egyedi, kézikönyv-hű
  Picasa-stílust viseli a Qt alap-kinézet helyett.

## [0.4.28] – 2026-07-21

### Javítva
- **Mappa-eltávolítás futó szkennelés közben (#216, éles hibajelentés):** az
  eltávolítás azonnal megszakítja a szkennelést, az eltávolított mappa képei
  rögtön eltűnnek, a kósza háttér-jelzések elnyelődnek, az Importálás-panel
  nem ragad be.
- **Videó utáni első kép szerkeszthetősége (#218, éles hibajelentés):** a
  videóról képre lapozva a szerkesztő azonnal működik, nem kell egy másik
  képre átlapozni.
- A teljes felület magyar: az új panelek és dialógusok (effekt-fülek,
  export, Importálás-panel, teljesítmény-monitor, Picasa-átvétel) szövegei
  lefordítva.

### Teljesítmény
- **Rács-virtualizálás (#142):** nagy mappáknál a rács csak a látható
  cellákat építi fel (3000 helyett ~42), a teljes nézet-frissítés
  3,4 mp-ről 10 ms-ra csökkent, a mappaváltás pedig nem olvassa újra a
  teljes indexet, ha nem változott — RPi5-en is sima görgetés.

### Hozzáadva
- **Kattintható diagnosztika-útvonal (#217):** a teljesítmény-monitoron a
  mentett napló útvonalára kattintva megnyílik a mappája (Windowson a fájl
  kijelölésével).

## [0.4.27] – 2026-07-20

### Hozzáadva
- **Fokozatos, blokkolásmentes indexelés + lebegő „Importálás" panel (#209):**
  nagy mappaszerkezet hozzáadásakor a képek mappánként, folyamatosan jelennek
  meg (nem egy nagy blokkoló lépésben), a program végig használható marad;
  a húzható panel mutatja az aktuális mappát és a haladást — a Picasa 3
  import-élménye.
- **Teljesítmény-monitor (#211):** a Súgó menüből kapcsolható lebegő panel
  (CPU, memória, aktuális tevékenység) + „Diagnosztika mentése" gomb — a
  mentett naplófájl issue-hoz csatolva célzott hibakeresést tesz lehetővé.
  Kikapcsolva nulla többletköltség; a napló nem tartalmaz teljes
  útvonalakat.

## [0.4.26] – 2026-07-20

### Javítva / Teljesítmény
- **Csillag/felirat/forgatás nem fagyaszt (#141):** az ini-írás és az
  index-frissítés háttérszálon fut, a mappa-resync helyett célzott egy-soros
  frissítéssel; a rács csak az érintett sort frissíti, a görgetés nem ugrik.
  NAS-mappában a több másodperces kattintás-fagyás megszűnt.
- **Watcher-bekötés (#143 lezárás):** fájlváltozásnál mappa-pontos, gyors
  szinkron fut a teljes részfa újrabejárása helyett; az adatbázis-foglaltság
  hibája sem némítja el a szinkront.
- **Export-lezárás (#136):** a szerkesztések (filters=) ténylegesen beleégnek
  az exportált fájlba, és a sikertelen fájlok neve+oka megjelenik az
  eredmény-ablakban.

### Hozzáadva
- **„Összes effektus másolása/beillesztése" (#152 lezárás):** a Kép menü két
  pontja élesítve — egy kép összes effektje átvihető több kijelölt képre,
  visszavonással.

## [0.4.25] – 2026-07-20

### Hozzáadva
- **Effektlánc másolás-beillesztés magja (#152):** a szerkesztő-munkamenet
  API-szinten tudja egy kép összes effektjének átvitelét másik kép(ek)re,
  az ismeretlen bejegyzések bitre pontos megőrzésével és undo-támogatással;
  a Kép menü gombjainak élesítése következik.
- **Picasa widget-króm komponensek (#3):** kézikönyv-hű görgetősáv és
  csúszka (PicasaScrollBar, PicasaSlider) próba-oldallal; a felületre
  bekötés következik.

### Karbantartás
- **A két óriásfájl felbontva (#150):** controller.py 1232 → 528 sor
  (hat al-modulra bontva), Main.qml 1590 → 604 sor (hét komponensre bontva)
  — viselkedés-változás nélkül, a tesztek módosítás nélkül zöldek. Minden
  forrásfájl a 800 soros projektlimit alatt; a párhuzamos munka mostantól
  kevesebb ütközéssel folyhat.

## [0.4.24] – 2026-07-20

### Hozzáadva
- **Finomhangolás + Effektek fülek (#20):** Derítőfény/Kiemelések/Árnyékok/
  Színhőmérséklet csúszkák (finetune2) és a 12 effekt-gomb élesítve a
  szerkesztő-panelen, élő előnézettel, a `filters=` láncba írva; a
  Filmszemcse (grain2) rögzített maggal renderel (nem „villog" újrarajzoláskor).
- **Arc-keretek a nézőben (#147):** a régi Picasa-címkézések (`faces=`)
  keretként + névvel megjeleníthetők — `F` billentyű vagy gomb a zoom-sávban,
  alapból kikapcsolva. (Felismerés nincs — az a 3. fázis.)
- **Meglévő Picasa-telepítés felderítése (#146):** a felderítő API kész
  (Wine-útvonalak + kézi mappa, WatchedFolders-átvétel útvonal-átírással);
  a felajánló dialógus bekötése következik.
- **Golden-összehasonlító harness (#115):** `tools/golden/compare_render.py`
  — a PicasaPy render a valódi Picasa-exportok ellen mérhető (SSIM/ΔE),
  szűrőnkénti pixelhű/közelítés ítélettel.
- Dizájnkézikönyv 2026-07-20-i helyi másolata a repóban.

### Javítva
- **Windows taskbar-ikon (#67):** explicit AppUserModelID — a tálcán a
  PicasaPy-ikon jelenik meg a Python-ikon helyett.

### Teljesítmény
- **Scanner (#143):** fájlonként pontosan egy fájlrendszer-lekérdezés
  (scandir-stat), mappa-mtime-alapú inkrementális újrabejárás és egy-mappás
  sync-út — ismételt átvizsgálásnál 96%-kal kevesebb hálózati művelet
  (NAS-on 50k fotónál ~50 s → ~2 s stat-költség); a bekötés a háttérfigyelő
  ágra következik.

## [0.4.23] – 2026-07-20

### Hozzáadva
- **Hiányzó effekt-renderelők (#149):** a régi Picasa-szerkesztések közül a
  Vignetta (mért maszkkal), Ragyogás (glow/glow2), Árnyalás (tint), Szűrt FF
  (ansel), Lágy fókusz (radblur), Fókuszos FF (radsat) és Színátmenet
  (dir_tint) mostantól megjelenik a nézőben és a bélyegképeken. (A
  Filmszemcse/grain2 véletlen alapú, pixelhűen nem reprodukálható — kihagyva,
  a round-trip őrzi.)
- **Kizárt mappák (#145):** a Picasa `FRExcludeFolders.txt`-jében kizárt
  mappák nem kerülnek az indexbe; a konfigfájl-keresés kis-nagybetű-független
  (`watchedfolders.txt` is működik), és a walker a legacy `Picasa.ini` nevet
  is felismeri.

### Javítva
- **Export (#136):** az exportált JPEG megőrzi az EXIF/IPTC-adatokat (dátum,
  GPS, kameraadat, felirat); változtatás nélküli exportnál bájthű másolás
  (nincs generációs veszteség); videónál megmarad az mtime; az export hibái
  strukturáltan jelződnek (nincs néma elhalás); a `filters=` szerkesztések
  beleégnek a célfájlba.
- **Magréteg-javítások (#151):** `.trashinfo` a fájlmozgatás előtt íródik
  (tele lemeznél sincs árva lomtár-bejegyzés); path-remap casefold-hosszváltozás
  javítva; thumbindex határellenőrzés (`ThumbIndexFormatError` nyers
  IndexError helyett); nem-UTF-8 fájlnevek naplózása; watcher rejtett-mappa
  szűrés relatív úton; watcher debounce felső korlát (30 s).

### Teljesítmény
- **Thumbnail-pipeline (#144):** párhuzamos bélyegkép-generálás (4 szál,
  hideg mappa-megnyitás ~3,2×); szűrt-thumb memóriacache (szerkesztett képes
  mappa görgetése ~100×); méretkorlátos cache-takarító (512 MB) a `~/.cache`
  alatti tárnak; kérésenként eggyel kevesebb fájl-megnyitás (NAS-barát).

## [0.4.22] – 2026-07-20

### Javítva
- **Feed-pozíció — a VALÓDI ok (#173):** a nézőből visszatérve a feed a
  háttér-sync befejezésekor a mappa elejére ugrott. A tényleges ok a
  controllerben volt: a háttér-sync (`syncFinished` → `_reload`) folder-módban
  `selectFolder`-t hívott, ami `folderActivated`-et emittál → a UI a mappa
  tetejére görget. Mostantól a háttér-sync `folderActivated` nélkül frissít
  (a scroll-to-top csak explicit, felhasználói mappa-választásé), így a néző
  bezárása után a görgetési pozíció megmarad. (A 0.4.20/0.4.21-es QML-oldali
  reveal ehhez kiegészítés — a valódi javítás ez.)
- **QML image-provider GIL-deadlock (#53):** a tesztkészlet (Linux/Windows,
  offscreen) nem-determinisztikusan beragadt — az async kép-betöltő szál a
  Python image-providert a GIL-en át hívta, míg a főszál natív Qt-hívásban
  tartotta a GIL-t. Offscreen (teszt) platformon mostantól szinkron a
  kép-betöltés (nincs második szál → nincs holtpont); produkcióban marad az
  async. A korábban ~50–100%-ban beragadó QML-tesztek 10/10 futása, és a
  Windows-CI-láb is stabilan zöld.

## [0.4.21] – 2026-07-20

### Javítva
- **Feed-pozíció (#173, utókövetés):** a nézőből visszatérve a feed a
  háttér-resync **befejezése után is** a megnyitás előtti pozíción marad. Az
  előző (0.4.20-as) fix csak az azonnali frissítést kezelte; a `resyncFolderOfRow`
  háttérszála viszont a végén (a kék „dolgozik" sáv eltűnésekor) küld egy késői
  frissítést, ami eddig visszaugratta a nézetet a mappa elejére. A reveal
  mostantól „ragadós": a késői async frissítésre és a layout beállására is a
  helyes pozíciót tartja, amíg a felhasználó ténylegesen nem görget.

## [0.4.20] – 2026-07-20

### Javítva
- **crop64-lánc rossz kivágása (#130):** a `filters=` láncbeli `crop64` a spec
  szerint csak szerkesztési történet — a tényleges vágást a `crop=` kulcs
  (a lánc effektív, utolsó crop64-e) adja, az eredeti képméretre. A render
  eddig a lánc minden crop64-ét sorban, kaszkádolva alkalmazta → rossz
  kivágás a több crop64-es valódi Picasa-fájlokon. Mostantól az effektusok a
  teljes képre futnak, a vágás egyszer, a végén.
- **Legacy (nem UTF-8) `.picasa.ini` (#133):** a CP1250/latin-1 fájlok három
  hibája javítva — a U+0085/U+2028 kódpont nem töri ketté a sort
  (fantomszekció); ékezetes szöveg legacy fájlba mentése nem omlik el
  (UTF-8-ra váltás, végső esetben explicit `IniSaveError`); az IPTC 1:90
  karakterkészlet-jelölő figyelembevétele csökkenti a mojibake-et.
- **Döntés-csúszka kinullázta a mentett tilt-et (#131):** a döntés-eszköz a
  mentett értékről indul, és aktív eszköz melletti lapozás nem írja felül az
  új kép mentett döntését az előnézetben.
- **Feed-pozíció elveszett a nézőből visszatérve (#173):** a mappa végén álló
  kép megnyitása után visszalépve a feed a megnyitás előtti görgetési
  pozíción marad, nem ugrik a mappa elejére.

## [0.4.19] – 2026-07-20

### Javítva
- **Éles indexkép szerkesztett/vágott képnél (#163, P0):** a `filters=` lánc
  mostantól nagy (a célméret négyszeres) bázison renderel, és csak a
  végeredmény kicsinyül a bélyegkép-méretre — az erős vágás után sem homályos
  a rács legnagyobb fokozatán. A szerkesztett bélyegkép külön, a lánccal
  kulcsolt cache-fájlba kerül.
- **Óriáskép (DecompressionBomb) nem akasztja meg a szinkront (#134):** a
  metaadat-olvasó és a thumbnail-út elkapja a Pillow `DecompressionBombError`-t
  (és a szigorú `DecompressionBombWarning`-ot); egyetlen túl nagy kép többé nem
  dönti el a teljes indexelést.
- **Üres gyökér nem törli az indexet (#132):** ha egy figyelt gyökér elérhető,
  de üres (tipikusan lecsatolt NAS-mount), a szinkron nem takarítja ki a
  korábban felindexelt részfát — a NAS visszatérésekor nincs órákig tartó
  teljes újraépítés.
- **A fájlkezelő-megnyitás hibája eljut a felhasználóhoz (#112):** a „Keresés a
  lemezen" mostantól hibát jelez, ha az `xdg-open` hiányzik vagy nemnulla
  kóddal tér vissza — nem nyeli el némán.

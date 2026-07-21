# Változásnapló

A projekt a [Semantic Versioning](https://semver.org/) elvét követi; a `0.x`
sorozat instabil. A teljes, gépi generálású kiadási jegyzék a
[Releases](https://github.com/sanchomuzax/PicasaPy/releases) oldalon él — ez a
fájl a lényegi, ember által írt kiemeléseket rögzíti.

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

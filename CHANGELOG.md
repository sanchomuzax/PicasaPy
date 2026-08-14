# Változásnapló

A projekt a [Semantic Versioning](https://semver.org/) elvét követi; a `0.x`
sorozat instabil. A teljes, gépi generálású kiadási jegyzék a
[Releases](https://github.com/sanchomuzax/PicasaPy/releases) oldalon él — ez a
fájl a lényegi, ember által írt kiemeléseket rögzíti.

## [0.7.44] – 2026-08-14

### Hozzáadva
- **A Google Earth-export elérhető a menüből (#530).** Eszközök → Geocímke →
  „Exportálás Google Earth-fájlba": a kijelölt képek közül a helyadattal
  rendelkezők térképre kerülnek. A program megmondja, hány kép került ki, és
  hány maradt ki helyadat híján; ha egyiken sincs helyadat, nem készít üres
  fájlt.

## [0.7.43] – 2026-08-14

### Hozzáadva
- **Google Earth-export: a geocímkézett képek kiírása térképre (#530).** A
  program elkészíti a `doc.kml` fájlt és mellé a bélyegképeket, így a
  fotógyűjtemény megnyitható a Google Earthben: minden kép a saját helyén
  jelenik meg, az ikon fölé érve megnő, rákattintva pedig egy buborékban
  látszik a bélyegkép, a felirat és a dátum. A koordináta nélküli képek
  kimaradnak — a program megmondja, hányan. *(A motor és a hívható művelet
  készen van; a menüpont bekötése külön lépés.)*

## [0.7.42] – 2026-08-14

### Hozzáadva
- **A gyűjtemények bezárhatók (#461).** A bal hasábon minden saját gyűjtemény
  neve mellett ott egy kis jelző: rákattintva a gyűjtemény **bezárul**, és a
  benne lévő mappák képei eltűnnek a rácsból, a keresésből és a
  csillag-szűrőből is. Ez nem törlés és nem is összecsukás — a mappák a
  helyükön maradnak, a gyűjtemény bármikor visszanyitható (a jelzőre vagy a
  nevére duplán kattintva). Így a régi archívumok, az exportált képek és a
  ritkán használt források egy kattintással eltehetők az útból. Ha a bezárás
  után egyetlen kép sem maradna látható, a program — az eredeti Picasa
  szövegével — előbb rákérdez.

## [0.7.41] – 2026-08-14

### Javítva
- **A diavetítés windowsos tesztje nem mér félkész állapotot (#519).** A
  vetítés közbeni csillagozás/forgatás háttérszálon fut; a teszt eddig 2
  másodperc után akkor is továbbment, ha a művelet még nem fejeződött be — a
  lassabb windowsos futtatón emiatt ingadozott a CI, és a bukás valódi hibának
  látszott. Mostantól a teszt a művelet befejeződését várja meg, hibaágon
  pedig a tényleges hibaüzenetet írja ki, nem egy félreérthető állítást.

## [0.7.40] – 2026-08-14

### Változott
- **A megszűnt online szolgáltatások menüpontjai véglegesen szürkék (#422).**
  A jobbklikk-menűkben hét olyan tétel volt (Feltöltés Google Fotókba / Picasa
  Webalbumba, Gyorsfeltöltés, Feltöltés tiltása, Online műveletek), ami eddig
  „még nincs bekötve" jelöléssel szerepelt — pedig ezek soha nem lesznek
  bekötve, mert maga a szolgáltatás szűnt meg. A tételek a helyükön maradnak,
  hogy a menük szerkezete egyezzen az eredetivel, de már nem ígérik, hogy
  egyszer működni fognak, és nem számítanak bele a hátralévő munkába.

## [0.7.39] – 2026-08-13

### Javítva
- **Az effekt-fülekről végleg lekerült a görgethető keret (#628).** A
  szerkesztő bal oldali paneljén újra megjelent egy keret, amiben görgetni
  kellett az effektekért — pedig ez a keret egyszer már le lett véve. A hibát
  most nem a tünetnél orvosoltuk: a panel eddig **fix 420 képpont** magas volt,
  akármekkora az ablak, és a 12 effekt-csempe ebbe soha nem fért bele. Mostantól
  a panel az ablakkal együtt nő, a Visszavonás/Újra gombsor a tartalmat követi,
  és a csempékre nem kerülhet rá. Ha az ablak alacsony, a panel kikényszeríti a
  neki szükséges helyet, ahelyett hogy elvágná a tartalmát.

## [0.7.38] – 2026-08-13

### Javítva
- **A töréspontos görbék mostantól úgy hajlanak, ahogy az eredetiben (#629).**
  A Picasa a görbe-töréspontok között sima, köbös átmenetet használ, nálunk
  eddig egyenes szakaszok voltak. Kilenc effektet érintett; a **60-as évek**
  és a **Kinemaszkóp** képén ez akár **21 világossági szint** eltérést jelentett
  — szemmel látható különbség, nem kerekítési zaj. A kétpontos görbét használó
  effektek (Színinvertálás, Neon, Ceruzarajz) kimenete bájtra változatlan.

## [0.7.36] – 2026-08-13

### Hozzáadva
- **A Finomhangolás-csúszkák modelljei mostantól a VALÓDI Picasa-kimenethez
  vannak mérve a tesztkészletben (#551).** Eddig csak néhány kézzel kiírt
  horgonyérték őrizte őket; innentől a Kiemelések, az Árnyékok, a
  Színhőmérséklet mind a hat állása és a szín-varázspálca teljes görbéje
  össze van vetve azzal, amit a Picasa 3.9 ténylegesen kiad. A mérés a
  referencia-fotókból desztillált átlaggörbékből dolgozik (a fotók maguk nem
  kerültek a repóba), a hibakorlátok a mai, mért pontosságból származnak.
  A próba szerint ez elkapja azt a fajta csendes rontást, ami a jegyben
  egyszer már majdnem bekövetkezett: a Színhőmérséklet elutasított natív
  képlete a legkedvezőbb paraméterrel is a korlát 4–19-szeresét hozza.

## [0.7.35] – 2026-08-13

### Hozzáadva
- **Két irányított effekt a natív magokból: „Irányított telítettség" és
  „Irányított fényesség" (#623).** Mindkettő a Picasa saját, dekompilált
  pixelképletét futtatja, nem közelítést: közös lineáris rámpa a két
  csúszkából („Balról jobbra", „Felülről lefelé"), rá a `dir_sat`
  luma-interpolációja, illetve a `dir_brite` köbös tónusgörbéje. A régi
  könyvtárak `filters=` lánca ezentúl ezt a két nevet is megjeleníti,
  kihagyás helyett. A család harmadik tagja (`dir_sharp`) és a `linblur`
  szándékosan kimaradt: ott a dekompilátum nem adja meg a hiányzó
  együtthatót, azt előbb ki kell mérni.

## [0.7.34] – 2026-08-13

### Javítva
- **A „Jó napom van" szinthúzása mostantól az eredeti Picasa geometriáját
  futtatja (#539).** A vágópontokat eddig fix 0,5% / 0,2% percentillel
  közelítettük; helyette a natív algoritmus fut: a hisztogram a kép középső
  90% × 90%-áról készül (a perem kimarad), a vágási küszöb pedig a teljes
  képpontszám 1/200-a, mindkét végén azonosan. A 12 referencia-képpáron az
  átlagos eltérés 2,68-ról 2,61-re csökkent, és a vágópontok maguk is a
  mérttel egyeznek. Külön mérés igazolta, hogy a nagyon szűk csatornákra
  vonatkozó 58 szintes alsó korlát nem illesztési fogás, hanem valódi
  Picasa-viselkedés: a 36 kimért csatornán a ténylegesen alkalmazott
  tartomány sosem ment 58,1 alá.

## [0.7.33] – 2026-08-13

### Javítva
- **Az effekt-fülön a Visszavonás/Újra gombsor rálógott a csempékre
  (#616).** Rövidebb ablakban a 12 csempés rács magasabb volt, mint a hely,
  és a panel alján ülő gombsor ráfeküdt a képekre. A fülek mostantól — a
  mód-eszközökhöz hasonlóan — egy vágott, görgethető területen ülnek, ami
  pontosan a gombsorig ér: a csempék **sosem** érnek a gombok alá. Az
  eredeti Picasa is külön konténerben tartotta a kettőt.

## [0.7.32] – 2026-08-13

### Hozzáadva
- **Sebesség a másolás/áthelyezés haladásjelzőjén (#457).** A számláló
  mellett most már az is látszik, milyen gyorsan halad („12,3 MB/s") —
  ahogy az eredeti Picasa is mutatta. Egy nagy kötegnél ez mondja meg,
  érdemes-e megvárni.
- **Mappa áthelyezése (#457).** A mappa jobbklikk-menüjében eddig
  helyfoglaló volt a „Mappa áthelyezése…" — most működik, és a mappa a
  **kísérőfájlokkal együtt** költözik. Ez nálunk több, mint kényelem: a
  `.picasa.ini` az igazságforrás, enélkül a képek elveszítenék a
  feliratukat, a címkéiket és az arc-hozzárendeléseiket. A program
  megtagadja a rendszermappák mozgatását, és nem enged olyan célt, ahol
  már van azonos nevű mappa — mindkét esetben a forrás érintetlen marad.
## [0.7.31] – 2026-08-13

### Változott
- **A mentés-parancsok a nézőben is működnek (#422).** A Mentés, a
  Visszaállítás, az „Összes szerkesztés visszavonása" és az „Arcok
  alaphelyzetbe állítása" eddig helyfoglaló volt a néző jobbklikk-
  menüjében — most ugyanazt teszik, mint a rácsban és a menüsávban.
  Ugyanaz a parancs nem viselkedhet máshol másképp.
## [0.7.27] – 2026-08-13

### Hozzáadva
- **„Exportált képek" a bal hasábon (#457).** Az exportált célmappák
  mostantól megjelennek a Projektek gyűjtemény alatt, legutóbbi elöl — az
  eredeti Picasa is külön csomópont alá gyűjtötte őket, hogy az export
  **nyomon követhető** maradjon, ne tűnjön el a fájlrendszerben. A már
  törölt mappák maguktól eltűnnek a listából.

## [0.7.25] – 2026-08-13

### Hozzáadva
- **Arcok alaphelyzetbe állítása (#422).** A rács jobbklikk-menüjéből
  minden arc visszahelyezhető a Névtelenek albumba (az arc-csoportok
  törlődnek, a felismerési lenyomatok megmaradnak, tehát nem kell újra
  átnézni a könyvtárat). Az eredetihez hasonlóan **figyelmeztetéssel**
  kérdez rá. Egy dolgot szándékosan **nem** csinál: a fotókba írt
  névcímkékhez nem nyúl — azt az eredeti is külön kérdésként tette fel, és
  az ember által adott név nálunk szent.

### Változott
- **Mentés, Visszaállítás és „Összes szerkesztés visszavonása" a rács
  jobbklikk-menüjéből is (#422).** Eddig ez a három pont helyfoglaló volt
  a menüben, pedig a működésük a Fájl menüből már elérhető volt. Mostantól
  ugyanaz a megerősítés nyílik, mint a menüsávból — egy parancs, egy út.
  Ha nincs mit menteni vagy visszavonni, a tétel **szürke, de látszik**:
  az eredeti Picasa sem tüntette el, hogy a menü magassága állandó
  maradjon.
## [0.7.22] – 2026-08-13

### Változott
- **Az Emberek-panel megmondja, mire számíthatsz (#26).** Üres listánál
  eddig egyetlen általános mondat állt ott; az eredeti Picasa panelje
  viszont **aszerint** magyarázott, mit néz éppen a felhasználó. Most
  nálunk is: személy albumát nézve „…akik a kiválasztott személlyel együtt
  szerepelnek", kijelölt fotóknál „…akik a kijelölt fotókon szerepelnek",
  egyébként pedig az, hogy még nem találtunk embereket.
## [0.7.19] – 2026-08-13

### Változott
- **Kézi arc-hozzáadás az eredeti kétlépéses módján (#26).** Eddig a
  téglalap felhúzása után azonnal felugrott a névkérő, és a téglalapon
  utólag nem lehetett igazítani. Mostantól — ahogy az eredeti Picasa
  utasítása leírta — a **négyszög megmarad és az oldalai húzhatók**, a
  nevet pedig a négyszög alatti **„Név hozzáadása"** felirattal lehet
  megadni. Szerkesztő módban ott az útmutató szöveg is: a gesztus
  önmagában nem felfedezhető.

## [0.7.16] – 2026-08-13

### Hozzáadva
- **Haladásjelzés a másoláshoz és az áthelyezéshez (#457).** Sok fájl
  mozgatásakor eddig „nem történt semmi", amíg a művelet le nem futott.
  Mostantól látszik, **hova** megy, és **hol tart** — az eredeti Picasa
  szövegeivel („Fájlok másolása", „%2 / %1 fájl másolása"). Egyetlen
  fájlnál nem nyílik ablak.

## [0.7.13] – 2026-08-13

### Hozzáadva
- **„Mellőzött emberek" album (#26).** A mellőzött arcok mostantól meg is
  nézhetők: a bal hasáb Emberek gyűjteményében megjelenik a *Mellőzött
  emberek* sor, és onnan a **mellőzés visszavonható**. Az eredeti Picasában
  ez is album volt, nem egyirányú szemetes — most nálunk sem az.

## [0.7.12] – 2026-08-13

### Hozzáadva
- **Név-javaslat az arcokra (#26).** Ha egy névtelen arc eléggé hasonlít
  egy már elnevezett személyre, a program **megkérdezi**: a bélyegképen
  megjelenik a név kérdőjellel, pipa és ✕ gombbal — pontosan úgy, ahogy az
  eredeti Picasa tette. A javaslat soha nem dönt a felhasználó helyett: az
  arc addig névtelen marad, az elvetés pedig csak a javaslatot törli, az
  arcot nem mellőzi.

  Ehhez a hiányzó láncszem is elkészült: eddig semmi nem kötötte a
  felismerési lenyomatot a névhez, ezért a javaslat-ág — bár a matematika
  megvolt — sosem talált el. Az index mostantól eltárolja, melyik arc
  melyik névhez tartozik (séma v12, meglévő indexeknél újraindexelés
  nélkül).

## [0.7.11] – 2026-08-13

### Hozzáadva
- **Mellőzött emberek (#26).** A „Névtelenek" nézetben a kijelölt arcok
  **mellőzhetők** — és a mellőzés nem törlés: ahogy az eredeti Picasában,
  a személy egy külön albumba kerül, tehát vissza is vehető. A program
  előbb rákérdez, az eredeti szövegével: *„Biztosan áthelyezi ezt a
  személyt a Mellőzött emberek albumba?"*

## [0.7.10] – 2026-08-13

### Változott
- **Az arcbeolvasás haladása a „Névtelenek" album tételén (#26).** Eddig
  külön sorban jelent meg; az eredeti Picasa magán az album tételén
  mutatta („While scanning, progress information appears in the Unnamed
  album item"). A tétel az első beolvasáskor is látszik, amikor még nulla
  névtelen arc van.

### Hozzáadva
- **Emberek-panel (#26).** A Nézet → Emberek menüpont mostantól valódi
  panelt nyit a jobb oldalon, a Címkék, a Helyek és a Tulajdonságok
  mellett — az eredeti Picasa is ide tette (a binárisban a
  `rightdrawerpanel/peoplepanel` pont e három mellett áll). Két szakasza
  van, az eredeti szövegeivel: **„Ezen a fotón:"** (a kijelölt képeken
  névvel szereplő emberek) és **„Szintén ezeken a fotókon:"** — ez utóbbi
  azt mutatja, hogy a nézett személlyel kik szerepelnek együtt, és egy
  kattintással át lehet lépni a másik személy albumára. Ez a családi
  gyűjtemények természetes navigációja: „ki van még rajta ezeken a
  képeken?"

## [0.7.9] – 2026-08-12

### Hozzáadva
- **Fogd-és-vidd az albumlistára (#455).** A kijelölt képek a bal hasáb
  albumlistájára húzhatók: a hívogató sorra ejtve **új album** készül
  (ugyanazzal a névkérő ablakkal, mint a menüből), egy meglévő album
  sorára ejtve pedig a képek **abba az albumba** kerülnek. A húzás csak
  már kijelölt képről indul — a ki nem jelölt területen marad a lasszós
  kijelölés.

## [0.7.8] – 2026-08-12

### Hozzáadva
- **Az arcbeolvasás haladása az albumlistában (#449).** Az eredeti Picasa
  nem modális ablakban mutatta a háttérmunkát, hanem a bal hasáb
  albumlistájában („Arcok keresése… 42% kész"), és közben semmi nem
  blokkolta a felhasználót. A sor magától megjelenik és eltűnik.
- **Adatbázis tömörítése (#449).** Az Eszközök → Kísérleti menüből
  elindítható a fotóindex tömörítése (SQLite `VACUUM`), az eredeti Picasa
  „Compacting" ablakának mintájára: megmondja, hogy percekig tarthat, és
  **bármikor megszakítható** — megszakításkor az adatbázis érintetlen
  marad. A haladásjelző szándékosan határozatlan: a `VACUUM` nem mond
  százalékot, kitalálni pedig félrevezetés lenne.

## [0.7.7] – 2026-08-12

### Változott
- **Barátságosabb első indítás (#449).** Üres könyvtárnál eddig rögtön a
  Mappakezelő fája nyílt ki — egy nagy döntés az első percben. Mostantól az
  eredeti Picasa mintáját követjük: **egyetlen kérdés** két választással
  (csak a Dokumentumok, a Képek és az asztal, vagy a teljes saját mappa),
  egyetlen OK gombbal. A program előre megmutatja, mely mappákat fogja
  átnézni, és — ahogy az eredeti is tette — kiírja, hogy **a keresés soha
  nem mozgat és nem másol fájlt**. A mappák később bármikor módosíthatók a
  Mappakezelőben.

### Hozzáadva
- **Hibanapló (#449).** A figyelmeztetések és hibák mostantól fájlba is
  kerülnek (`errorlog.txt` az adatkönyvtárban), és ha az adatbázis
  betöltése hibára fut, a program – ahogy az eredeti Picasa – **felajánlja
  a napló megtekintését**, ahelyett hogy némán összeomlana vagy titokban
  javítana. A napló nem nő korlátlanul: méret fölött indításkor
  elforgatjuk.

## [0.7.6] – 2026-08-12

### Hozzáadva
- **Forgatás és csillagozás már az importálás előtt (#441).** Az
  import-előnézet bélyegképein megjelent két forgató nyíl és egy csillag —
  ahogy az eredeti Picasa import-képernyőjén is —, így a képeket még a
  bemásolás előtt ki lehet egyenesíteni és megjelölni. A jelölés a
  **másolatra** kerül; a kártyán lévő eredeti fájlokhoz a program nem nyúl.
- **Sebesség az import haladásjelzőjén (#441).** A csík mellett mostantól az
  is látszik, milyen gyorsan halad a másolás — ebből lehet megbecsülni,
  mennyi van hátra.
- **Fájltípus-szűrő és korábbi források az importnál (#441).** Beállítható,
  hogy a beolvasás kép- és filmfájlokat, csak képeket, vagy mindent
  keressen; a forrásválasztó pedig felkínálja a **legutóbb használt
  forrásokat**, ahogy az eredeti Picasa is tette.

## [0.7.5] – 2026-08-12

### Hozzáadva
- **Igazi betűtípusok a szöveg-eszközben (#450).** A feliratok eddig egy
  vonalas, „rajzolt" betűkészlettel készültek, amiben nincs betűcsalád,
  félkövér, dőlt vagy aláhúzás. Mostantól valódi TrueType-betűkkel
  rajzolunk: **Arial · Times New Roman · Courier New**, félkövéren, dőlten,
  aláhúzva, és a sorok **balra / középre / jobbra** igazíthatók. A vezérlők
  ott vannak a Szöveg eszköz panelján: betűtípus-lista, méret, F/D/A gombok
  és a három igazítás-gomb. Ha a gépen nem található megfelelő betű, a
  felirat a régi módon jelenik meg — a szöveg-eszköz sosem esik ki.

## [0.7.4] – 2026-08-12

### Hozzáadva
- **Végre menthetők a szerkesztések a fájlokba (#444).** A Fájl menü
  **Mentés** (Ctrl+S) pontja eddig szürke helyfoglaló volt — a motor kész
  volt, csak nem lehetett elindítani. Mostantól él, és vele a másik két
  fokozat is: a **Visszaállítás** (az eredeti jön vissza, a szerkesztések
  elvesznek) és az **Utolsó mentés visszavonása** (a fájl áll vissza, de a
  szerkesztések megmaradnak). Minden mentés előtt biztonsági másolat
  készül.
- **Figyelmeztetés mentés előtt**, ha a képen olyan szerkesztés van, amit a
  program még nem tud megjeleníteni: a mentés azt véglegesen eldobná, ezért
  a program felsorolja őket, és külön rákérdez.

## [0.7.3] – 2026-08-12

### Hozzáadva
- **A kollázs és a film is a képtálca tartalmán dolgozik (#455).** Az
  exportálás után most a másik két gyűjtő-művelet is a tálcára tett képekből
  készül — több mappából összeválogatva —, és a párbeszédek rács-kijelölés
  nélkül is megnyílnak, ha a tálcán van kép. Üres tálcánál minden marad a
  régiben: a kijelölés a forrás.

## [0.7.2] – 2026-08-12

### Hozzáadva
- **A mappába exportálás a képtálca tartalmán dolgozik (#455).** Az eredeti
  Picasában az alsó sáv gombjai nem a pillanatnyi kijelölésre, hanem a
  **tálcára gyűjtött** képekre hatottak — ez a tálca értelme: több mappából
  összeszedni, amit együtt akarunk kezelni. Mostantól nálunk is: ha van
  tartott kép, az exportálás azokat viszi (bármelyik mappából), üres
  tálcánál marad a kijelölés.

## [0.7.1] – 2026-08-12

### Hozzáadva
- **A vágás képarány-listája teljes lett (#448).** A legördülőben mostantól
  ott a **magyarázó alcím** is, ahogy az eredeti Picasában — „Kisméretű
  nyomat", „Letter méretű papír", „CD-borító", „Szélesvásznú képernyő" —,
  bekerült a hiányzó **8.5x11** (Letter) arány, és él a **Jelenlegi
  megjelenítés** tétel is, ami a képernyő arányát veszi át.

## [0.7.0] – 2026-08-12

### Hozzáadva
- **Működik a szín-varázspálca a Finomhangolás fülön (#551).** A gomb eddig
  az „Automatikus szín" szűrőt fűzte a képre; a Picasa saját mentései
  viszont elárulták, hogy a pálca valójában az **Alapszínválasztás** színét
  állítja be automatikusan. Mostantól nálunk is ezt teszi: a program a
  kevéssé telített („szürke-közeli") képpontokból választ viszonyítási
  színt, és azzal veszi ki a színezetet. A tulajdonos 11 mérőképén a
  választott szín a Picasáétól átlagosan ~3 egységgel tér el (0–255-ös
  skálán).

## [0.6.99] – 2026-08-12

### Javítva
- **Az Alapszínválasztás (pipetta) a Picasa saját arányaival dolgozik
  (#551).** Eddig egy csillapított közelítés futott, ami a színezetnek csak
  a felét-háromnegyedét vette ki. A Picasa a viszonyítási színt a **zöldhöz**
  méri (a mentett érték középső bájtja mindig 128), és a program mostantól
  ugyanígy: a semlegesnek jelölt pontból számolt korrekció a valódi Picasa
  eredményétől ~3 %-on belül van. Tényleg szürke pontot kijelölve a kép
  változatlan marad, ahogy eddig is.

## [0.6.98] – 2026-08-12

### Javítva
- **A Derítőfény mostantól a Picasa saját algoritmusa (#551, #575).** Eddig a
  mérésekre illesztett közelítés futott; most a Picasa natív kódjából
  visszafejtett, pontos művelet: egy gamma-görbe, amit a program a képpont
  világosságával **fordítottan arányos** súllyal kever az eredetihez — ezért
  derít a sötét részeken anélkül, hogy a világosakat kimosná. Ugyanez a mag
  hajtja a Derítőfény csúszkát, a „Régi effektek" fülön a két derítő-gombot
  és a `finetune` láncot is.

## [0.6.97] – 2026-08-12

### Javítva
- **A „Régi effektek" fül gombjai végre működnek (#582).** Eddig minden
  gombja hibaüzenetbe futott („Érvénytelen effekt"), mert a fül olyan
  szűrőneveket kínált, amilyeneket a szerkesztő nem fogadott el. Mostantól a
  Derítőfény, az egykattintásos Derítőfény és a Radiális színezés
  alkalmazható is — a Picasa saját alapértékeivel (25%-os derítés, középre
  tett fókuszpont).
- **A szerkesztő effekt-paneljei nem ragadnak be (#583).** Ha egy effekt
  csúszkás panelje nyitva volt, fülváltás után **ott maradt**, és
  rárajzolódott a másik fül csúszkáira. Mostantól fülváltáskor bezárul (a
  beállítás elvész, a mentett kép változatlan), és a „További effektek" meg
  a „Régi effektek" fül sem lóg többé egymásra a nyitott panellel.

## [0.6.96] – 2026-08-12

### Hozzáadva
- **Névütközéskor megkérdezzük, mi legyen (#457/2).** Ha a célmappában már
  van azonos nevű fájl, a program – ahogy az eredeti Picasa – rákérdez:
  **„Másodpéldányok átnevezése"** vagy **„Másodpéldányok kihagyása"**. Ha
  nincs ütközés, nincs kérdés sem. Az áthelyezést a célmappa kiválasztása
  után egy **„Fájlok áthelyezése"** jóváhagyás előzi meg, ugyanúgy, mint
  régen.
- Egy hibás fájl többé nem állítja meg az egész köteget: a többi átmegy, a
  végén pedig **egyetlen** összegzés jön (és az is csak akkor, ha volt
  kihagyott vagy hibás fájl).

## [0.6.95] – 2026-08-12

### Javítva
- **A bal panel rendezése végre a bal panelt rendezi (#461/3).** Az eredeti
  Picasában a bal hasáb **saját jobbklikk-menüje** tartalmazta a „Rendezés
  dátum / név / méret / legutóbbi változtatás alapján" tételeket — vagyis az
  a **hasábot** rendezte. Nálunk ez a menü eddig a **rácsot** állította, a
  hasáb pedig mozdíthatatlan volt. Mostantól két, egymástól független
  beállítás van, ahogy az eredetiben: a **panel saját menüje a panelt**, a
  felső **Nézet ▸ Mappanézet a rácsot** rendezi.
- **Az évszám-fejlécek csak a dátum-nézetben jelennek meg (#461/3).** Név
  vagy méret szerinti rendezésnél ugyanaz az évszám többször, összevissza
  sorrendben bukkant volna fel; ott most sima felsorolás áll.

## [0.6.94] – 2026-08-12

### Karbantartás
- **A szerkesztőpanel szétbontva (#496).** Az `EditorPanel.qml` 1367 sorról
  **786-ra** fogyott, a projekt 800 soros korlátja alá. A tartalom fülenként
  és blokkonként önálló fájlokba került (fülsáv, fülgomb és ikonja, 1. fül,
  csúszkás effekt-alpanel, párbeszédek), a gazda pedig a közös állapotot és a
  fül-váltást tartja. **Viselkedés-változás nincs**: a meglévő szerkesztő-
  tesztek változtatás nélkül zöldek — ez a bizonyíték. Ettől a párhuzamos
  munkában is kevesebb az ütközés: egy fül módosítása már nem írja ugyanazt a
  fájlt, mint a többi.

## [0.6.93] – 2026-08-12

### Javítva
- **A FocalZoom és a Focal Pixelate csúszkái eddig fel voltak cserélve
  (#570).** A natív visszafejtés kimutatta, hogy a fókuszpont után az
  **Impact** következik, nem a **Radius** — a program a harmadik mezőt
  olvasta sugárként, így a két csúszka egymás hatását fejtette ki. Mindkét
  effekt mostantól mind a **hat** paraméterét helyes helyről olvassa, közös
  körmaszkot használ (a Hardness szabja a perem lágyságát), és a Fade a
  szokásos módon zár.

### Hozzáadva
- **A Focal Pixelate (fókuszált képpontnövelés) effekt megjelent (#570).**
  Eddig felismertük, de nem rendereltük. Az eredeti recept szerint készül:
  lekicsinyítés, majd **legközelebbi-szomszéd** visszanagyítás — ettől élesek
  a blokkjai, nem elmosódottak.

## [0.6.92] – 2026-08-12

### Javítva
- **A Comicize (Képregény) effekt az eredeti féltónusos rasztert kapta
  (#569).** A korábbi megvalósítás posterizálással és élkereséssel közelítette
  — de a Picasa effektje nem élkiemelő képregényszűrő, hanem **nyomdai
  raszter**: két, egymáshoz képest fél csempével eltolt pontrács. A pont a
  sötét területeken nagyra nő, a világosokon elfogy, ahogy a valódi
  nyomdatechnikában. A három csúszka (BlurXY, DotContrast, DotFade) mostantól
  a `filterdesc.xml` szerinti szerepét tölti be; a `DotFade = 100` pontosan
  érintetlen képet ad.

## [0.6.91] – 2026-08-12

### Hozzáadva
- **„Régi effektek" fül a szerkesztőben (#571).** A Picasa motorjában benne
  maradt egy csomó szűrő, aminek a 3.9-es felületén **nincs kezelőfelülete**:
  régebbi verziókból örökölt darabok. A motor egy régi `.picasa.ini`-ből még
  alkalmazza őket, de a felhasználó nem tudja előhívni — mostantól nálunk
  igen. **Ez tudatos eltérés az eredetitől**, szándékosan többet adunk.
  - Amelyik effektnek van valódi modellje (`radtint`, `autobacklight`,
    `fill`), az **működik**; a többi **látszik, de szürke** — mert egy régi
    képen ott lehet, és tudni kell róla. A letiltott gombok megmondják, miért
    nem használhatók, és a *halott* név (`focalpixelate`) más magyarázatot kap,
    mint a *még megfejtetlen*.
  - Hogy melyik gomb él, azt a **renderelő** dönti el, nem kézzel írt lista —
    így nem lehet aktívnak látszó, de nem ható gomb.
  - Ha a megnyitott kép láncában ilyen effekt van, a **fül jelzést kap**.

## [0.6.90] – 2026-08-12

### Hozzáadva
- **`autobacklight` effekt (#567).** A régi `.picasa.ini`-láncokban előforduló
  név mostantól renderel: a natív regiszter szerint ez **nem** adaptív
  képelemzés, hanem **fix 25%-os derítőfény** — ugyanaz a mag, mint a
  `backlight`/`fill`, rögzített argumentummal. Külön gombot nem kap a
  felületen, ahogy az eredetiben sem volt.

### Javítva
- **A kisbetűs `focalpixelate` halott bejegyzésként jelenik meg (#567).** A
  Picasa 3.9 natív regiszterében sincs hozzá feldolgozó — konfigurációs
  maradvány, nem „még hiányzó" effekt. A renderjelentés ezt ki is mondja, és
  a név semmiképp nem keveredhet az élő `PicnikFocalPixelate` effekttel.

## [0.6.89] – 2026-08-12

### Javítva
- **Az IR (infravörös film) effekt az EREDETI csővezetékét kapta (#566).** A
  korábbi modell a paraméternevekből következtetett, és három ponton tévedett:
  SCREEN-t kevert LIGHTEN helyett, a zöld izzást a már monokrómmá tett képre
  tette (nem az eredetire), és a **kék csatorna negatív súlyát** teljesen
  figyelmen kívül hagyta. A natív kernel visszafejtése után a záró mátrix
  `Y = −0,5·R + 2,0·G − 0,5·B`; a kék tehát sötétít, ahogy a valódi
  infravörös filmen is.

## [0.6.88] – 2026-08-12

### Hozzáadva
- **`radtint` (Sugaras árnyalás) effekt (#565).** Az utolsó „exe-ből ismert,
  de renderelhetetlen" szűrőnév is megkapta a modelljét — nem találgatásból,
  hanem a natív kód visszafejtéséből: a fókuszpont körül a kép változatlan,
  kifelé egy köbös smoothstep maszk szerint erősödő **szorzó**-színezés fut
  (`forrás × szín / 256`), ami lényegében különbözik a `dir_tint` „szín felé
  keverésétől". Egyetlen paraméter, a Feather csúszka affin leképezése maradt
  feltételezés — ez dokumentáltan jelölve van, golden-párral pontosítható.

## [0.6.87] – 2026-08-12

### Hozzáadva
- **Offline mappa kezelése (#459/5).** A levált NAS-mount vagy kihúzott lemez
  mappája mostantól **bennmarad az indexben** a fotóival együtt — eddig némán
  kiestek belőle. A mappa „jelenleg nem elérhető" jelölést kap a bal hasábon
  (halvány, dőlt sor + súgószöveg), a rá lépéskor pedig a program kimondja,
  mi a helyzet, hibaüzenet-szerű pánik nélkül. A jelölés a mount visszatérése
  után magától elmúlik, újraépítés nélkül. A felismerés szabályát és a
  vállalt tévedés-irányt a `docs/decisions/offline-folders.md` rögzíti.
- **Hiányzó fájlok a kollázsban és a mozgófilmben (#459/3).** A nem található
  kép mostantól **külön mondatot** kap az eredeti Picasa szövegével — az
  megmondja, mi történhetett (elmozdítás, átnevezés, törlés) —, a csupán
  olvashatatlan fájlok pedig a semleges „kihagyva" számban maradnak. A munka
  ezután is a maradékkal készül el, nem áll le.

## [0.6.86] – 2026-08-12

### Hozzáadva
- **„Hozzáadás" gomb a képtálcán (#455).** A böngészés közben, mappákon
  átnyúlóan gyűjtött képek egy lépésben albumba tehetők — az eredeti Picasa
  tálcáján is külön gomb kínálta ezt.

## [0.6.85] – 2026-08-12

### Javítva
- **Visszavontam a görgethető keretet az effekt-fülekről (#422).** Rossz válasz
  volt a tünetre, és nem is kérte senki. A valódi ok az volt, hogy a három
  ismert effekt-fülre olyan effektek is odakerültek, amelyek az eredetin nincsenek
  ott — ezek mostantól **külön, „További effektek" fülön** vannak, a 3–5. fül
  pedig pontosan az eredeti gombkészletét tartalmazza (12 · 12 · 11).

### Hozzáadva
- **Három automatikus vágás-javaslat a Vágás eszközben (#448).** Az eredeti
  Picasa is három kész vágást ajánlott fel; a stratégiák a nevük szerint: szoros
  vágás az arcokra, kompozíció az arcok köré, illetve arc nélkül a
  legrészletgazdagabb terület, a horizontvonal és a szín-domináns terület. A
  javaslat a kijelölésbe kerül, tehát még igazítható rajta az Alkalmaz előtt, és
  a kiválasztott képarányt követi.

## [0.6.84] – 2026-08-12

### Hozzáadva
- **Az Emberek-album kép-parancsai a jobbklikk-menüben (#422).** Személy
  albumában a képre jobbklikkelve mostantól elérhető az „Eltávolítás az
  Emberek albumból" (megerősítéssel — a névcímke csak újbóli felismeréssel
  vagy kézzel állítható vissza) és az „Áthelyezés új személyhez…". Mindkettő
  a teljes kijelölésre hat, mappánként egyetlen írással.
- Új, általános névbekérő párbeszéd, amit a további átnevező parancsok is
  használhatnak.

## [0.6.83] – 2026-08-12

### Javítva
- **Az effekt-fülek csempéi nem csúsznak szét (#422).** A kétsoros feliratú
  gomb (például „Infravörös film") magasabb lett a többinél, a rács sora
  hozzá igazodott, a szomszédos csempék képe pedig felnagyult. A bélyegképes
  gomb mostantól mindig két sornyi feliratot foglal, így a rács egyenletes.
- **Az effekt-csempék felirata a többi csempéével azonos méretű** — eddig
  nagyobb volt.

### Hozzáadva
- **Jobbklikk-menü a szövegmezőkben (#422).** Az eredeti Picasa minden
  szövegmezője alatt ott van a hét tételes menü (Visszavonás · Kivágás ·
  Másolás · Beillesztés · Törlés · Az összes kijelölése · Automatikus
  kitöltés); nálunk eddig egyetlen mezőben sem volt. Az inaktív tételek —
  az eredetihez hasonlóan — szürkén látszanak, nem tűnnek el. A
  jelszó-mezőben szándékosan nincs menü.

## [0.6.82] – 2026-08-12

### Hozzáadva
- **Figyelmeztetés a visszavonás adatvesztéses eseteire (#465).** A retusálás
  és a vörösszem-javítás területadatot hordoz: a visszavonás eldobja, és az
  „Újra" nem hozza vissza. Az eredeti Picasához hasonlóan ezek visszavonása
  mostantól rákérdez — a többi lépésé továbbra sem, hiszen ott van visszaút.
- Az **„Összes szerkesztés visszavonása"** az eredeti két külön szövegét
  használja egy, illetve több kijelölt képre, és **külön figyelmeztet**, ha a
  kijelölésben vörösszem-javítás van.

## [0.6.81] – 2026-08-12

### Hozzáadva
- **A felület betűtípusa az eredeti arányaival (#526).** Az eredeti Picasa a
  kereskedelmi Praxis családot használta, ezt nem szállíthatjuk; a
  helyettesítőt **méréssel** választottuk, nem ránézésre: a két Picasa-
  képernyőképről leolvasott tíz magyar felirat képpont-szélességét vetettük
  össze az öt jelölttel. Az **Open Sans** illeszkedik a legjobban (átlagos
  eltérés 0,92%, a következő jelölt 1,15%), ezért ez került a programba
  (SIL Open Font License 1.1, a licenc mellékelve).

### Belső
- Teszt őrzi, hogy a kilépéskor a szerkesztő háttér-renderelése előbb
  érvénytelenítve, majd korlátos ideig bevárva legyen (#547/#430) — enélkül a
  háttérszál a program leállása közben összeomlást okozhatott.

## [0.6.80] – 2026-08-12

### Javítva
- **Az effekt-beállítások alpanelje sem lóghat rá a Visszavonás sorra (#464).**
  A sok paraméteres effektek (például a Vignetta) beállító-panelje magasabb
  lehet a rendelkezésre álló helynél; ez is vágott, görgethető területre került.
  Ezzel a szerkesztőpanel minden nézete — az öt fül, a négy mód-eszköz és az
  effekt-beállítások — a gombsor fölött ér véget.

## [0.6.79] – 2026-08-12

### Javítva
- **A mód-eszközök panelje sem lóghat rá a Visszavonás sorra (#464).** A vágás,
  a retusálás, a vörösszem és a szöveg panelje ugyanabba a hibába futhatott,
  mint az effekt-fülek: ha a tartalom magasabb a rendelkezésre álló helynél,
  ráúszott a panel alján ülő gombsorra. Mind a négy mostantól közös, vágott
  görgethető területen ül, ami pontosan a gombsorig ér.

## [0.6.78] – 2026-08-12

### Javítva
- **Az indexkép-jelvények végre látszanak is (#463).** A hely-tű és a két
  arc-jelvény („van rajta felismert arc", „névjavaslat vár jóváhagyásra") a
  bélyegkép-kártyában rég készen álltak, és az adat is megvolt a modellben —
  a fő rács viszont nem kötötte be őket, így sosem jelentek meg. Mostantól
  megjelennek; új teszt őrzi, hogy egyetlen jelvény se maradhasson bekötetlenül.

## [0.6.77] – 2026-08-12

### Javítva
- **Az effekt-fülek gombjai nem lógnak rá a Visszavonás sorra (#464).** Mindhárom
  effekt-fül rácsa több gombot tartalmaz, mint amennyi a panel magasságába fér;
  eddig a csempék átfedtek a panel alján ülő Visszavonás/Újra gombsorral, és a
  fül alja levágódott. A rács mostantól saját, vágott görgethető területen ül.
- **A „Gyakori javítások" fül gombjai az eredeti sorrendjében (#464).** A
  tulajdonos képernyőképe alapján: Vágás · Kiegyenesítés · Vörösszem /
  Jó napom van · Automatikus kontraszt · Automatikus szín / Retusálás · Szöveg,
  és mindegyik alatt a Derítőfény-csúszka. A „Kreatív Kit" csempe **eltűnt** —
  az eredeti fülön nincs ilyen gomb (a jegy szövege tévesen sorolta fel).

## [0.6.76] – 2026-08-12

### Javítva
- **A Finomhangolás fül elrendezése az eredeti szerint (#464).** A tulajdonos
  négy képernyőképéről kiderült, hogy a fülön nincs szöveges fejléc, a
  csúszka-feliratok középen állnak, és az „egy gombnyomásos javítás" nem két
  nagy szöveges csempe a csúszkák fölött, hanem **két kis varázspálca-gomb**
  a csúszka-oszlop jobb szélén: az egyik a Kiemelések/Árnyékok párnál (a
  megvilágításhoz), a másik az „Alapszínválasztás" sorában (a színhez).
- Az **Alapszínválasztás** pipettája mellé bekerült a **kijelölt semleges
  színt mutató korong**, ahogy az eredetin is.

## [0.6.75] – 2026-08-11

### Belső
- **A hisztogram-vágópont számítása egyetlen helyre került (#549).** Az
  Automatikus kontraszt (közös) és a „Jó napom van"/csatornánkénti út eddig
  sorról sorra ugyanazt a lépéssort tartalmazta; a #539-es küszöb-finomítás
  így két helyen kényszerült volna módosításra. A viselkedés bájtra
  változatlan. (A jegy 2. és 3. pontja tárgytalanná vált: az ott leírt halott
  ág és float-egyenlőség az Auto Colour #541-es újraírásával eltűnt.)

## [0.6.74] – 2026-08-11

### Javítva
- **A négy Finomhangolás-csúszka újramérve valódi fotón (#551).** Eddig
  szintetikus szürke rámpákon mértünk, és ezért három csúszka modellje hibás
  volt. Az átlagos eltérés a Picasa saját kimenetétől (a JPEG-zaj szintje ~1):
  Kiemelések **23,15 → 1,06**, Árnyékok **19,41 → 0,76**, Derítőfény
  **18,10 → 5,89**, Színhőmérséklet (hideg irány) **20,94 → 5,08**.
- A **Kiemelések** és az **Árnyékok** valójában a fehér- illetve feketepontot
  mozgatja, nem csúcsfényt ment és árnyékot emel — a csúszkák felső határa
  ezért 0,48, a Picasa saját paramétertartománya szerint.
- A **Derítőfény** a pixel világosságától függ, nem a csatorna értékétől: két
  azonos világosságú, eltérő színű képpont ugyanazt a világosítást kapja.
  Emiatt a finomhangolás GPU-gyorsított élő előnézete nem nulla derítőfénynél
  a rendes (pontos) útra vált — a kép így mindig azt mutatja, ami mentődni fog.

## [0.6.73] – 2026-08-11

### Hozzáadva
- **Vörösszem-eszköz: automatikus ÉS kézi, egyszerre (#445).** Az eszköz
  megnyitásakor az automatika azonnal lefut az előnézeten, és kiírja, talált-e
  vörös szemet. Amit a gép kihagyott, azt a felhasználó a képre húzott
  négyzettel pótolhatja — tetszőleges számút, egyenkénti visszavonással és
  Alaphelyzet gombbal. A „Előnézet a kijelölő négyzetek nélkül" jelölőnégyzet
  csak a keretek rajzát tünteti el, a javításon nem változtat. Az Alkalmaz
  gomb ír csak lemezre, egyetlen visszavonható lépésként; Mégse esetén a
  mentett állapot érintetlen marad.
- A kézi négyzetek a `filters=` láncban a `redeye=1,<rect64>…` alakban élnek
  (PicasaPy-saját kiterjesztés, a retusálás bevált mintája szerint). Kézi
  négyzet nélkül a bejegyzés **bájtra a valódi Picasa `redeye=1;` alakja**,
  tehát a kétirányú kompatibilitás sértetlen.

## [0.6.69] – 2026-08-11

### Belső
- **A szerkesztő-panel forrása felbontva (#496).** A 2367 soros
  `EditorPanel.qml`-ből önálló fájlba került a három újrafelhasználható
  vezérlő (eszköz-csempe, panel-gomb, szín-választó), valamint a „Fotó
  vágása", a „Retusálás" és a „Szöveg" panel — **2367 → 1665 sor**. A
  felület viselkedése és a megjelenése változatlan.

## [0.6.68] – 2026-08-11

### Javítva
- **Gyűjtemény-nevek: hibaüzenet a néma elutasítás helyett (#461).** Üres vagy
  már foglalt névnél eddig egyszerűen nem történt semmi; most a névbekérő
  nyitva marad, és megmondja, mi a baj — az eredeti Picasa két külön
  üzenetével.
- **A gyűjtemény törlésének kérdése megnyugtatóan fogalmaz (#461):** kimondja,
  hogy a benne lévő mappák nem vesznek el, hanem a „Mappák a lemezen"
  gyűjteménybe kerülnek — ahogy az eredetiben.

## [0.6.67] – 2026-08-11

### Hozzáadva
- **Semleges szín pipetta a Finomhangolás fülön (#464).** A képre kattintva a
  kijelölt pont lesz a semleges szín — a négy csúszka érintetlen marad.
- A **Finomhangolás fülre visszakerült** az Automatikus szín és az
  Automatikus kontraszt gombja, ahogy az eredetiben is ott volt (szándékos
  ismétlés az első fülről, hogy hangolás közben kéznél legyen).

### Változott
- **A Visszavonás/Újra a panel alján, egyetlen példányban (#464).** Eddig
  mind az öt fül a saját (azonos) gombpárját rajzolta; az eredetiben a pár
  globális, nincs fülhöz kötve.

## [0.6.66] – 2026-08-11

### Hozzáadva
- **Arc-jelvények a bélyegképeken (#463).** A bal felső sarokban jelvény
  mutatja, ha a képen **felismert arc** van, és egy **külön** jelvény azt, ha
  **jóváhagyásra váró névjavaslat** vár rajta — vagyis elintézetlen dolgod van
  a képpel. A két állapot független egymástól, ahogy az eredetiben is. A
  méretarányok az eredeti Picasa réteg-adataiból (14×20 és 20×20).

## [0.6.65] – 2026-08-11

### Javítva
- **Fájlméret az eredeti Picasa magyar formátumai szerint (#526).** Eddig 1 MB
  alatt mindig KB-ban írtuk ki — egy 300 bájtos fájl így „0 KB" volt. Most a
  Picasa saját fokozatait követjük: **bájt és KB egész számra, MB-tól egy
  tizedes**, és megvan a GB/TB fokozat is.

### Megjegyzés
- A Picasa **teljes betűkészlete** (méret- és súlylétra) bekerült a
  stíluskonstansok közé (#526). Maguk a betűtípusok kereskedelmiek, nem
  szállíthatók; a szabad helyettesítő kiválasztása méréssel tartozik eldőlni,
  ezért egyelőre a rendszer alapértelmezése marad.
- A **dátum/idő magyar alakja tudatosan eltér** az eredetitől: a Picasa magyar
  szövegkészletében a dátumformátumok lefordítatlanul maradtak (angol
  sorrend, 12 órás idő) — ez fordítási hiányosság, nem szándékos alak.

## [0.6.64] – 2026-08-11

### Hozzáadva
- **Tulajdonságok-panel: 11 mező helyett a Picasa teljes mezőkészlete (#529).**
  A sorrend az eredeti Picasa saját beállítófájlját követi, és minden mező a
  Picasa magyar feliratát kapta (a program saját szótárából): fényképezőgép
  gyártmánya és típusa külön, **három külön dátum** (fényképezőgép,
  digitalizálás, módosítás), tájolás, vaku, objektív, 35 mm-es
  fókusztávolság, téma távolsága, fehéregyensúly, **fénymérés módja**,
  **exponálási program**, tömörítés, **színtér**, ICC-profil, beágyazott
  bélyegkép, kulcsszavak, **GPS-hármas** és egyedi azonosító. A felsorolt
  értékek is magyarul jelennek meg („Középsúlyos", „Rekesz-előválasztásos
  mód"), nem nyers EXIF-kulcsként. Az adat nélküli mező kimarad.

## [0.6.63] – 2026-08-11

### Javítva
- **Összeomlás-veszély a haladásjelzés cseréjekor (#519/#430).** A
  nyilvántartás lecserélésekor a régi példány felszabadulhatott, miközben
  egy korábban indított háttérszál még jelzett neki — ez Windowson
  hozzáférési hibával (0xC0000005), Linuxon szegmentálási hibával omlik
  össze. A régi példány mostantól életben marad, és leáll.

## [0.6.62] – 2026-08-11

### Javítva
- **Figyelmeztetés csak ott, ahol tényleg nincs visszaút (#465 4. pont).**
  A felirat bemásolása a szövegmezőbe eddig szó nélkül felülírta a beírt
  szöveget — mostantól rákérdez (üres mezőnél nem, ott nincs mit
  elveszíteni). A kártya kiürítésének figyelmeztetése az eredeti Picasa
  szerint **nagybetűs**. A Kukába helyezés továbbra sem ijesztget: az
  valóban visszafordítható.

## [0.6.61] – 2026-08-11

### Javítva
- **Mappakezelő: az eredeti elrendezés és két hiányzó figyelmeztetés (#543).**
  A dialógus mostantól pontosan fele-fele oszt (mint az eredeti), az
  állapot-választó süllyesztett keretbe került „A jelenlegi mappára:"
  felirattal, és van **Súgó** gomb is. A fában szöveges karakter helyett
  **rajzolt jelvény** mutatja az állapotot, és külön jelvény azt, ha a mappa
  az arcfelismerésből ki van hagyva. Az arcfelismerés-kapcsoló felirata
  vált (be/ki), és „Eltávolítás a Picasából" állapotú mappán szürke.
  Új figyelmeztetések: **teljes meghajtó figyelése** lassíthatja a
  rendszert, illetve **figyelt mappa eltávolításakor** a program
  figyelmeztet, hogy az oda később tett képek már nem kerülnek be maguktól.

## [0.6.60] – 2026-08-11

### Javítva
- **A „Jó napom van" szélső eseteken is pontosabb (#539).** A nagyon szűk
  hisztogramú (egyszínű, alacsony kontrasztú) képeket eddig túl agresszíven
  feszítettük ki. A mérés szerint a Picasa ilyenkor korlátozza a nyújtást —
  a 12 referencia-páron az eltérés **5,48 → 2,68**, és ebből a kiugró kép
  hibája **46,0 → 12,4**. A többi tizenegy kép kimenete bájtra változatlan.

## [0.6.59] – 2026-08-11

### Javítva
- **A HDR-ish végre azt csinálja, amit az eredeti (#545).** Az eltérés a
  valódi Picasa-kimenettől **11,2 → 2,45** (kilenc export; az érintetlen kép
  20,85 — vagyis a korábbi változat alig volt jobb a semminél). Két dolog
  hiányzott: az elmosás mértéke a `Sugár` csúszka **fele** (ezt a négy
  sugár-állás egymástól függetlenül ugyanígy adta), és a helyi kontraszt
  mellett az erősséggel arányos **világosítás** is fut. Ugyanez a motor
  hajtja a *Helyi kontraszt* effektet is, az is pontosabb lett.

## [0.6.58] – 2026-08-11

### Javítva
- **Az automatikus szín (Auto Colour) modellje megvan (#541).** A 12 képes
  mérőkészlet három dolgot mondott ki: az effekt tiszta csatornánkénti
  **erősítés** (a feketepont nem mozdul), és az erősítést a kép **semleges**
  (kevéssé telített) képpontjaiból számolt fehéregyensúly adja — a telített
  részletek (virág, égbolt) nem számítanak bele. Az eltérés a valódi
  Picasa-kimenettől **7,45 → 2,35**; az érintetlen kép 5,29, a mért
  erősítésekkel elérhető elméleti alsó korlát 1,08. A korábbi változat tehát
  rosszabb volt, mintha meg sem csináltuk volna az effektet — most a felére
  csökkent a hiba.

## [0.6.57] – 2026-08-11

### Javítva — a háttérszálas szerkesztő-render kódátvizsgálásának találatai
- **A lassú effekt már nem blokkolja a csúszkákat (#546).** A 0.6.55-ös
  megoldás egy közös záron sorosított: ha egy perces effekt renderelése
  közben a felhasználó csúszkát húzott vagy képet váltott, a felület megint
  megállt — csak most egy másik ajtón. A háttér-render mostantól saját,
  lokális munkaterületen dolgozik, közös zár nélkül.
- **Gyors kattintás-sorozat után az UTOLSÓ állapot látszik (#546).** Eddig a
  lemaradó, régebbi renderelés felülírhatta a frissebb képet.
- **A szerkesztő bezárása után a futó renderelés nem éled újra (#546):** a
  lezárt kép nem kerül vissza a gyorsítótárba, és nem frissíti a felületet.
- **Kilépés lassú effekt alatt (#547):** a program most érvényteleníti és
  megvárja a futó renderelést, így nem omolhat össze kilépéskor.
- **A renderelés hibája nem néma többé (#548):** naplózódik, és a felhasználó
  is kap jelzést róla (NAS-on a fájl a művelet közben eltűnhet).
- **A kék csík nem pöröghet örökre (#550):** ha a háttérszál elindítása
  elbukik, a jelzés is lezárul.

## [0.6.56] – 2026-08-10

### Javítva — öt effekt a valódi Picasa-kimenethez kalibrálva (#317)
A felhasználó hat új mérőkészletet exportált (ugyanaz a fotó, csúszkánként
külön mappa). Az effektek eltérése a valódi Picasa-kimenettől:

- **Vignette:** 2,66 → **0,70** (8 export; az érintetlen kép 14,4). Kiderült,
  hogy a ragyogás sugara a dokumentált képlet **fele**, és hogy a
  Lomo/Holga-nál mért 255-ös korlát ide **nem** érvényes.
- **Museum Matte:** a keret vastagsága **pixelben** értendő, nem a rövidebb
  oldal százalékában — eddig egy 2560 széles fotóra 1447 px-es keretet
  rakott 65 helyett (a kép 5454×4596-ra hízott). Most mind a hét export
  mérete pontos, az eltérés **2,01**.
- **Szépia:** 4,40 → **0,89** — a lineáris közelítés helyett a mért
  tónusgörbék.
- **Filtered B&W:** 6,11 → **0,36**. A szín itt **szűrő, nem festék**: a
  kimenet mindig szürke marad (mint a fényképészeti sárga/narancs/vörös
  szűrők), eddig tévesen színezte a képet.
- **Orton-ish:** 4,43 → **2,05** — az elmosás szigmája szintén a fele a
  dokumentáltnak, a fényerő-görbe kitérése pedig ±96 (nem ±75).

### Ismert korlát
- A **HDR-ish** modellje továbbra sem pontos (átlagosan 11,2 az érintetlen
  kép 25,3-ához képest): a mérés szerint globális S-görbe és
  telítettség-emelés is van benne, nem csak lokális kontraszt. Külön jegyen.

## [0.6.55] – 2026-08-10

### Javítva
- **A szerkesztő nem fagy be lassú effekt alatt (#514).** A mentett
  szerkesztési lánc újrarenderelése (effekt hozzáadása, vágás,
  visszavonás…) eddig a felület szálán futott: egy percekig számoló
  effekt alatt a program befagyottnak látszott, és az alsó kék
  haladásjelző csík sem tudott animálni. Mostantól háttérszálon fut, így
  a csík **magától** pörög, a felület pedig végig kezelhető marad. A
  csúszkák élő előnézete szándékosan azonnali (szinkron) maradt.

### Megjegyzés
- A **nyomtatásra készítés** (#514 másik fele) továbbra is a felület
  szálán fut — a Qt nyomtató-rajzolása nem tehető át háttérszálra
  ugyanezzel a mintával, ezért az külön jegyen folytatódik.

## [0.6.54] – 2026-08-10

### Javítva
- **Az effekt-fülek újra három oszlopban rajzolnak (#537).** A 3., 4. és 5.
  szerkesztő-fülön az effekt-csempék két oszlopba tördelődtek, miközben az
  eredeti Picasán — és nálunk az első két fülön — három oszlop van. A
  csempék sorrendje változatlan, csak a szélességük igazodik.

## [0.6.53] – 2026-08-10

### Javítva
- **Automatikus kontraszt (#540): mostantól gyakorlatilag pontos.** Az
  eredeti Picasa kimenetéhez mérve az eltérés **4,54 → 0,62** (12 kép
  közül **ötön bájtra azonos**). Kiderült, hogy ez a művelet **közösen**
  vágja mind a három színcsatornát — ezért nincs fehéregyensúly-hatása,
  tisztán a kontrasztot nyújtja.

### Ismert korlát — őszintén
- **Az automatikus szín (Auto Colour) modellje továbbra sem ismert.** A
  mérés szerint a mostani változat (7,45) és a korábbi (7,82) **egyaránt
  rosszabb, mintha a program meg sem csinálná az effektet** (5,29). A
  mérés azt is kizárta, hogy egyszerű szinthúzásról volna szó. A kód ezt
  kimondja, hogy senki ne hivatkozzon rá készként — a megfejtés külön
  jegyen (#541).

## [0.6.52] – 2026-08-10

### Javítva
- **A „Jó napom van" gomb végre azt csinálja, amit az eredeti (#535):** a
  felhasználó 12 kép-páros Picasa-exportjához mérve az eltérés
  **17,59 → 5,48**. A képek nagy részén ennél is pontosabb: **11 képen az
  átlagos eltérés 1,80**, egyetlen szélső eset húzza fel az átlagot.
- **Mostantól felismeri, mikor NE nyúljon a képhez.** Ha a kép már
  kihasználja a teljes világosság-tartományt, a gomb nem változtat semmit —
  eddig azt is felvilágosította, aminek nem kellett volna.
- **Ez az effekteken is átüt:** öt effekt (Holga, Éjjellátó, Ceruzarajz,
  Hatvanas évek, Cinemascope) a lánca elején ezt az automatikus korrekciót
  használja. A **Holga** eltérése az eredetitől **14,19 → 11,34**.

### Megjegyzés
- A modell a felhasználó referencia-exportjaiból lett megfejtve:
  csatornánként külön, lineáris szinthúzás. A vágási pontokat egyelőre
  rögzített százalékkal közelítjük — ez az egyetlen forrása a maradék
  eltérésnek.

## [0.6.51] – 2026-08-10

### Hozzáadva
- **Az arcfelismerés végre LÁTSZIK is (#26, 3. lépcső):** a bal hasábban az
  Emberek gyűjteményben megjelent a **„Névtelenek"** sor, benne a program
  által megtalált arcokkal, **arcok szerint csoportosítva**
  („Csoportosítás arc szerint" / „Csoportok kibontása").
- **Tömeges névadás:** jelöld ki a hozzád tartozó arcokat, és a **„Név
  hozzáadása"** egyszerre mindnek nevet ad. Az első névadásnál a személy
  megjelenik az **Emberek** gyűjteményben, a név pedig a kép melletti
  `.picasa.ini`-be íródik — ugyanazon az úton, amit a kézi arccímkézés is
  használ.

### Fontos garancia
- **A meglévő névcímkéidhez a program nem nyúl.** Az elnevezett arcok
  szerkezetileg kimaradnak a csoportosításból és a tömeges névadásból is.

### Ismert korlát
- A „Névtelenek" nézetben egyelőre a **teljes fénykép** látszik, nem a
  kivágott, szemvonalra igazított arc — ez külön munka.
- Ha a felismerő modell hiányzik, a „Névtelenek" sor egyszerűen nem jelenik
  meg; minden más változatlanul működik.

## [0.6.50] – 2026-08-10

### Hozzáadva
- **Arcfelismerés — 2. lépcső (#26): a program mostantól felismeri, hogy két
  arc ugyanazé az emberé.** A megtalált arcokhoz „lenyomat" készül, és az
  ismeretlen arcok **maguktól csoportokba rendeződnek** — ez lesz később a
  névadás alapja. Új futásidejű függőség nélkül, az OpenCV-be épített
  motorral.
- A csoportosítás **inkrementális**: egy új kép érkezésekor néhány
  összehasonlítás fut, nem éjszakai újraszámolás.

### Fontos garancia
- **A meglévő névcímkéidhez a program nem nyúl.** A gépi csoportosítás
  kizárólag a **névtelen** arcokon dolgozik — a Picasában felépített
  arccímkéket soha nem értékeli újra, és nem írja felül.

### Megjegyzés
- Ez a lépcső **még nem jelenik meg a felületen**; a névadás, az Emberek-
  albumok és a javaslatok a következő lépcsők. A felismerő modell fájlja
  nincs a programban — ha hiányzik, a lenyomat-számítás csendben kimarad,
  minden más változatlanul működik.

## [0.6.49] – 2026-08-10

### Javítva
- **A hibák eddig CSENDBEN eltűntek (#459):** a szinkron-, album-,
  helyadat- és arccímke-írás hibajelzései léteztek a programban, de
  **egyikük sem volt a felülethez kötve** — így a felhasználó soha nem
  értesült róluk. Mostantól közös hibasáv jelzi őket.

### Hozzáadva
- **Csak-olvasható fájl (#459):** a mentés előtt kiderül, ha a mappa nem
  írható, és a program az eredeti Picasa szövegével szól. *(Az automatikus
  mappa-másolás még nem érhető el — a párbeszéd ezt is kimondja, hogy ne
  maradjon megválaszolhatatlan kérdés.)*
- **Sérült kép (#459):** ha egy fájl nem tölthető be, a program felajánlja
  az **elrejtését** — nem törli, és a döntés a felhasználóé.
- **Kevés lemezhely (#459):** az export, a webexport és az importálás
  **indulás előtt** ellenőrzi a szabad helyet, és szól, ha kevés — így nem
  áll meg félúton.

## [0.6.48] – 2026-08-10

### Javítva
- **A szerkesztett képek kisképe sötétebb volt a nagy képnél (#525):** a
  program az effektet a **már kicsinyített** képre számolta, az eredeti
  Picasa viszont nagyban számolt, és csak utána kicsinyített. Mivel a
  vignetta sugarának felső korlátja rögzített képpontszám, kicsiben ugyanaz
  az effekt jóval szélesebb sötét karikát rajzolt. Mostantól a bélyegkép is
  nagyobb alapméreten készül. Az eredeti Picasa kimenetéhez mérve az
  eltérés **48,3 → 14,1** (Holga), illetve **55,0 → 8,3** (Lomo).
- A korábbi, hibásan sötét bélyegképek **maguktól frissülnek** — nem kell
  kézzel üríteni a gyorsítótárat.

### Megjegyzés
- A szerkesztett képek bélyegképe ezzel kb. **kétszer lassabban** készül el.
  Ez csak a szerkesztett fotókat érinti, háttérben fut, és egyszeri: a
  könyvtár böngészése nem lassul.

## [0.6.47] – 2026-08-08

### Javítva
- **A vignettás effektek most már az eredetihez hasonlítanak (#522, #504):**
  a ragyogás számítása egy közelítő trükk helyett zárt képlettel dolgozik,
  ahogy az eredeti művelet. Az eredeti Picasa kimenetéhez mérve az
  eltérés a **Holgánál 31,6 → 14,2**, a **Lomónál 14,6 → 8,6**
  (viszonyításul: az érintetlen kép eltérése 33,4 és 32,1).
- A **Vignette** tiszta fekete képpontjainak aránya nagy képen
  **8,2% → 0,1%** — a korábbi „befeketedő sarok" gyakorlatilag eltűnt.
- A számítás **sebessége nem romlott**, és már nem függ a ragyogás
  sugarától.

## [0.6.46] – 2026-08-08

### Hozzáadva
- **Az effektek csúszkái és vezérlői megjelentek (#516):** eddig a legtöbb
  effektet csak alapbeállítással lehetett használni. Mostantól 21 effekt
  kapott állítható vezérlőket az eredeti Picasa dokumentált értékei
  szerint — csúszkákat, jelölőnégyzeteket és színválasztókat.
- **Öt effekt eddig egyáltalán nem látszott a felületen** (Matte,
  Éjjellátó, Helyi kontraszt, Lekerekített szélek, Szemcse), pedig a
  motorban készen voltak — ezek most gombot kaptak.
- A képmérettől függő tartományok (sarok-lekerekítés, felirat-magasság) a
  tényleges képméretből számolódnak, nem rögzített értékek.

### Javítva
- **Az effekt-bélyegképek elronthatták a mentett beállításokat:** a
  bélyegkép-készítés minden paramétert számként írt ki, így a **színek és
  a ki/be kapcsolók sérültek** minden színt használó effektnél. Javítva.

## [0.6.45] – 2026-08-08

### Javítva
- **A fekete-fehér effektek színes kimenete (#504):** az eredeti Picasa
  Holga-exportjaihoz mérve kiderült, hogy a kimenetnek **tiszta
  szürkének** kell lennie (minden képponton R=G=B) — a receptben szereplő
  szín nem színez, hanem a szürkítés **csatornasúlyait** hangolja, mint egy
  színszűrő a fekete-fehér film előtt. A mi kódunk ezzel szemben színes
  képet adott. Javítva: a kimenet mostantól valódi szürkeárnyalatos.
  Mérve az eredeti kimenethez: az eltérés **71,0 → 31,6**.

### Ismert korlát
- A referencia-mérés szerint a teljes egyezéshez (~14,6) ez **nem elég**:
  a ragyogás számítási modelljét is le kellene cserélni a fizikailag
  pontosabb változatra, és külön eltérés van az automatikus
  színkorrekcióban is (a mienk sötétít, az eredeti világosít). Mindkettő
  külön munka — ld. #504 és #317.

## [0.6.44] – 2026-08-08

### Javítva
- **A vignettás effektek sötétsége nagy fényképeken (#504):** az eredeti
  Picasa felülről korlátozza a ragyogás sugarát, a mi számításunk viszont
  nem — ezért nagy képen az effektek jóval sötétebbek lettek a kelleténél.
  Eredeti Picasa-exportokhoz mérve: a kimenetünk átlagos eltérése a
  korlát nélkül **41,8**, a korláttal **9,0** volt (viszonyításul az
  érintetlen kép eltérése 32,1 — vagyis korlát nélkül rosszabbak voltunk,
  mintha meg sem csináltuk volna az effektet).
  A korlát mind a hat érintett helyre bekerült, **egy közös pontra**, hogy
  új effektnél se lehessen elfelejteni.
  Mérve, valódi fényképen: a **Holgánál** egy 4000×3000-es képen a tiszta
  fekete képpontok aránya **43% → 11%**, a **Lomónál** 2560 px-en
  **34% → 7%**, a **Vignette**-nél **19% → 7%**.

### Ismert korlát
- **Kis képeken (kb. 1000 képpont alatt) ez nem változtat semmit**, mert
  ott a számított sugár eleve a korlát alatt van. A Holga ilyen méretben
  továbbra is sötét; ennek okát Holga-referenciakép nélkül nem lehet
  eldönteni (a referenciakészlet ma csak a Lomóhoz létezik).

## [0.6.43] – 2026-08-08

### Javítva
- **Hisztogram-panel (#512):** a panel hibás barna hátteret kapott, és a
  görbe rajzterülete **ráfutott a fényképezőgép-adatokra**, ha azok több
  sorba törtek (magyarul jellemzően igen). A panel mostantól az eredeti
  szerinti világosszürke, elkülönülő világos rajzterülettel, és a
  területek elosztása szerkezetileg zárja ki az átfedést — tetszőleges
  hosszúságú szöveg mellett is.
- **Indulási QML-figyelmeztetés (#506):** a szöveg-eszköz színválasztója
  olyan nevet használt, ami ütközött a Qt beépített nevével. Átnevezve; a
  figyelmeztetés eltűnt. A tesztek figyelmeztetés-őre mostantól **elkapja
  ezt a hibaosztályt**, így nem térhet vissza észrevétlenül.

### Dokumentáció
- A `histogram-reference.md` a panel hátterét tévesen dokumentálta
  (innen ered a #429-es barna háttér). A téves sor korrekciós jegyzetet
  kapott, hogy ne lehessen rá tényként hivatkozni.

## [0.6.42] – 2026-08-08

### Megjegyzés
- **Az effekt-színek rendben vannak (#510):** felmerült, hogy három effekt
  (Holga, CrossProcess, NightVision) színénél fel van cserélve a piros és a
  kék. Méréssel kiderült, hogy **nincs hiba**: az effekt-lánc szándékosan
  RGB-térben dolgozik, a be- és kilépési pontok pedig átváltanak. A Holga
  kimenete a valódi feldolgozási úton meleg vörös, ahogy az eredetiben is.
  Az érintett függvények leírása mostantól **kimondja** a színsorrendet,
  hogy ez ne okozzon újabb félreértést.
- **A „Holga-szerű" effekt sötétsége nem programhiba (#504):** a lánc
  minden lépése az eredeti Picasa dokumentált receptje szerint fut. A
  sötétség az effekt hangolásának kérdése (#317), nem hibás számításé.

### Hozzáadva
- Az öt vignettát használó effektre (Lomo, Holga, Vignette, Matte,
  NightVision) **valódi fényképpel** futó tesztek: színsorrend,
  méretfüggetlenség és futásidő-korlát.

## [0.6.41] – 2026-08-08

### Hozzáadva
- **Az alsó kék csík mostantól minden hosszú műveletnél animál (#505):**
  eddig csak a beolvasás és a bélyegkép-betöltés alatt jelzett, minden más
  némán futott. A jelzés egyetlen közös ponton, a háttérmunkák indításánál
  került be, ezért **minden** háttérművelet magától megkapja — a kötegelt
  effektek, az export, az importálás, a duplikátum-keresés, a webexport, a
  csillagozás/forgatás és az arc-szkennelés is. Rövid műveletnél nem
  villan fel (0,3 mp késleltetés), és ha megjelent, nem tűnik el azonnal.
- Ha egy háttérművelet **hibával áll le**, a jelzés akkor is lezárul — a
  csík nem marad örökre pörögve.

### Ismert korlát
- **A szerkesztő effektjei (köztük a Polaroid) továbbra sem jeleznek**,
  mert a képszámítás a felhasználói felület szálán fut. Ott a csík nem is
  tudna animálni. Ugyanez vonatkozik a nyomtatásra készítésre. Ezek
  áthelyezése háttérszálra külön munka.

## [0.6.40] – 2026-08-08

### Javítva
- **Kétszer megjelenő mappa (#507):** ha ugyanazt a mappát két, kicsit
  másképp leírt útvonalon vetted fel figyelésre (szimbolikus linken
  keresztül, vagy `..` szegmenst tartalmazó úton), a program két külön
  bejegyzésként kezelte. Mostantól minden útvonal egységesen normalizálódik
  — Windowson kis-nagybetűtől függetlenül, Linuxon a fájlrendszer
  szabályai szerint.
- **A már meglévő duplikátumok összevonása:** indításkor a program egyszer
  összevonja a korábban duplán bekerült mappákat. Az összevonás
  **adatvesztés nélküli**: ha egy fotónál mindkét oldalon eltérő, valódi
  szerkesztés áll (csillag, felirat, kulcsszó, szűrő, helyadat), akkor a
  program **inkább meghagyja a duplikátumot**, mint hogy bármit felülírjon.

## [0.6.39] – 2026-08-08

### Javítva
- **A „Lomo-szerű" effekt fekete képe és a befagyás (#504):** az effekt
  kimenete teljesen fekete lett, az alkalmazása pedig percekre
  megbénította a programot — és mivel az effekt minden megnyitáskor
  újraszámolódik, az így mentett kép sem nyílt meg. **A képek nem
  sérültek meg**, csak a számítás akadt el. Mindkét ok javítva: a
  vignetta-számítás nagy sugárnál az egész képet befeketítette, a nagy
  elmosás pedig a képmérettel robbanásszerűen lassult.
  Mérve: a Lomo kimenetének átlagos fényessége 0,0 → 52,0, a futásideje
  2000×1500-as képen **37 s → 0,87 s**; a Holgáé 14,6 s → 1,1 s.

### Ismert korlát
- A „Holga-szerű" effekt már nem feketedik és nem lassú, de **továbbra is
  nagyon sötét**. Ez nem a fenti hiba maradéka, hanem az effekt
  hangolásának kérdése (a vignetta sugarai nincsenek dokumentálva az
  eredetiből) — külön munka, ld. #504.

## [0.6.38] – 2026-08-08

### Hozzáadva
- **Arcfelismerés — első lépcső (#26):** megjelent az arcok automatikus
  megtalálásának alapja. A felismerő az OpenCV-be épített motorra épül,
  **új függőség nélkül**, és a Picasáéval azonos öt arcpontot adja, amiből
  a szemvonalra igazított arc-indexkép készül. **A meglévő névcímkéidhez
  nem nyúl:** ahol már van ember által adott név, ott a program nem
  detektál újra — a Picasában felépített arccímkék érintetlenek maradnak.
- A felismerő modell fájlja **nincs a programban**, külön lépésben
  szerezhető be. Ha hiányzik, az arcfelismerés **csendben kikapcsol**, és
  minden más változatlanul működik.

### Megjegyzés
- Ez a lépcső még **nem jelenik meg a felületen** — a csoportosítás, az
  elnevezés és a javaslatok a következő lépcsők.

## [0.6.37] – 2026-08-08

### Hozzáadva
- **Importálás az eredeti munkamenete szerint (#441):**
  - **Célmappa neve három módban** — kézi név, **a felvétel dátuma szerint
    külön mappákba bontva** (ez a Picasa importjának a lelke), vagy a mai
    dátum. A korábbi, szabad szöveges sablon-mezőt ez váltja fel.
  - **„Duplikátumok kizárása"** — a már importált képek kimaradnak, és az
    előnézet kiírja, hány ilyen van.
  - **Egyenkénti válogatás** — a bélyegképeken ki/be kapcsolható, mi jöjjön
    át; plusz „Összes kizárása" / „Összes felvétele".
  - **„Másolás után:" három állapot** — a forrás érintetlenül hagyása, csak
    az átmásolt képek törlése, vagy minden törlése. A két törlő állapothoz
    az eredeti kétlépcsős, egyre erősebb figyelmeztetése tartozik.

### Javítva
- **Az importálás nem törölhet át nem jutott fájlt:** ha a másolás közben
  néhány fájl elbukik, a „minden törlése" ezentúl meghagyja őket a
  forráson — korábban azok is törlődtek volna, pedig épp azok nem kerültek
  át. A törlés továbbra is csak sikeres másolás után fut le.

## [0.6.36] – 2026-08-08

### Módosítva
- **Retusálás az eredeti munkamenete szerint (#445, első lépcső):** a
  foltozás eddig egyetlen kattintással, fix méretű négyzetes területen
  dolgozott. Az eredeti Picasában ez **irányított klónozás** volt: az első
  kattintás kijelöli a javítandó foltot, az egeret mozgatva **élőben
  látszik, mivel fogja pótolni**, a második kattintás pedig véglegesíti.
  Mostantól nálunk is így működik, **kör alakú, állítható méretű ecsettel**
  („Brush Size"), és a foltok **egyenként visszavonhatók** („Undo Patch" /
  „Redo Patch" / „Reset").
- A mentési formátum foltonként rögzíti a cél-pontot, a forrás-pontot és a
  sugarat. A korábbi, téglalapos alakkal mentett szerkesztések továbbra is
  betölthetők és megjelennek — nem vesznek el.

## [0.6.35] – 2026-08-08

### Hozzáadva
- **Vágás: az eredeti képarány-készlet és saját arányok (#448, első
  lépcső):** a vágás-panel arány-listája az eredeti Picasa tényleges
  kulcskészletét követi (4x4, 4x3, 4x6, 5x7, 8x10, 5x3, 9x13, 10x15,
  13x18, 5x8, 16x10, 16x9, négyzet, A4). Mostantól **saját képarány is
  felvehető névvel** (szélesség × magasság), és törölhető is; a program
  megjegyzi a **legutóbb használt arányt**.
- **Figyelmeztetés a kiegyenesítés után:** ha a képen már van
  kiegyenesítés, a vágás-panel az eredeti Picasa szövegével figyelmezteti
  a felhasználót, hogy a vágás pontatlan lehet.

## [0.6.34] – 2026-08-08

### Hozzáadva
- **Mappakezelő: negyedik, önálló arcfelismerés-kapcsoló (#449):** az
  eredeti Picasában a mappa beolvasási állapota (Folyamatos figyelés /
  Egyszeri beolvasás / Eltávolítás) mellett egy **tőlük független**
  kapcsoló döntötte el, hogy az adott mappában fusson-e az arcfelismerés.
  Ez eddig teljesen hiányzott; mostantól a Mappakezelőben külön
  jelölőnégyzet, kikapcsoláskor az eredeti szövegű rákérdezéssel. A
  beállítás a Picasával azonos formátumú `FRExcludeFolders.txt`-be kerül.
  *(Arcfelismerés-motor még nincs a projektben, így a kapcsoló egyelőre a
  kizárási szándékot rögzíti — arcok és névcímkék törlése nem történik.)*

### Javítva
- **Félrevezető dokumentáció az `FRExcludeFolders.txt`-ről:** a
  funkciótérkép azt állította, hogy a fájl a teljes indexelésből zárja ki
  a mappákat. Valójában kizárólag az arcfelismerést érinti — és a program
  korábban egyáltalán nem is használta a fájlt.

## [0.6.33] – 2026-08-08

### Hozzáadva
- **Szöveg-eszköz: kitöltés + körvonal, átlátszóság, felirat-átvétel
  (#450, első lépcső):** a felirat eddig egyetlen színnel készült, így
  tarka hátterű képen olvashatatlan volt. Mostantól külön választható a
  **kitöltés** és a **körvonal** színe, állítható a körvonal vastagsága és
  a szöveg átlátszósága, és bekapcsolható a **csak körvonalas** felirat.
  Két új gomb: a **„Felirat átvétele"** egy kattintással beteszi a kép
  meglévő feliratát a szövegmezőbe, a **„Minden meglévő szöveg törlése"**
  pedig eltávolítja a képre írt szöveget.

## [0.6.32] – 2026-08-08

### Hozzáadva
- **Kuka vs. végleges törlés megkülönböztetése (#457, 1. pont):** a törlés
  eddig minden esetben azt írta, hogy a kép „a rendszer lomtárába kerül" —
  hálózati megosztáson (NAS) azonban a lomtár jellemzően nem elérhető.
  Mostantól a program megnézi, van-e valódi lomtár az adott meghajtón (a
  freedesktop-szabvány szerinti mount-specifikus lomtárat is beleértve), és
  ha nincs, az eredeti Picasa 3 szövegével figyelmeztet: a törlés azonnali
  és nem vonható vissza. Ez a figyelmeztetés külön kulcsot kapott, így a
  „ne kérdezze újra" beállítás a lomtáras esetnél nem némítja el.

## [0.6.31] – 2026-08-08

### Javítva
- **A szerkesztő első fülének gombsora az eredeti szerint (#464):** az
  „Automatikus szín" és az „Automatikus kontraszt" gomb sorrendje fordított
  volt a Picasa 3-hoz képest, és hiányzott a „Kreatív Kit" gomb. Mindkettő
  javítva.
- **Kötegelt effektus: a művelet üres kijelölésnél sem hallgat el:** a
  nem-dolgozó ágak eddig jelzés nélkül tértek vissza, így a hívó örökre
  várt a befejezésre. A tesztek mostantól hangos, leíró hibaüzenettel
  buknak el, ha egy Qt-jel nem érkezik meg.

## [0.6.30] – 2026-08-08

### Hozzáadva
- **„Összes szerkesztés visszavonása" (#465):** a Kép menü eddig szürke
  pontja mostantól működik — a kijelölt képek teljes szerkesztési láncát
  törli, megerősítés után. A művelet egy lépésben visszavonható, és a
  visszavonás a vágást is helyreállítja.

## [0.6.29] – 2026-08-08

### Hozzáadva
- **Képtálca: a képek mappaváltás után is megmaradnak (#455, első lépcső):**
  az alsó sáv eddig csak a pillanatnyi kijelölést tükrözte, így mappát váltva
  minden elveszett. Mostantól a „Megtartás" gombbal több mappából
  gyűjthetők össze képek; a megtartottakat zöld tű jelöli a rácsban, és a
  tálca ürítése rákérdez.

## [0.6.28] – 2026-08-08

### Javítva
- **Hisztogram-panel az eredeti arculatával (#429):** a panel a Picasa meleg
  barna hátterét kapta, a görbe alatt elkülönített fehér rajzterülettel. A
  fényképezőgép neve is az eredeti szerint jelenik meg (a „NIKON
  CORPORATION" mostantól „NIKON").

## [0.6.27] – 2026-08-07

### Hozzáadva
- **Geo-jelvény az indexképeken (#463):** a helyadattal rendelkező képek a
  jobb alsó sarokban piros pin-jelvényt kapnak, mindhárom nézetben.

### Javítva
- **A véletlenszerű összeomlások forrása mind a tíz vezérlőben megszűnt
  (#438):** a háttérben futó műveletek szálai mostantól bevárhatók, közös
  megoldással. Ez a #430-ban javított hiba maradéka volt — ugyanaz a minta
  a program több pontján is megvolt, és időnként összeomlást okozott.

## [0.6.26] – 2026-08-07

### Hozzáadva
- **Gyűjtemény jobbklikk-menüje (#422):** átnevezés és eltávolítás
  (megerősítéssel) a bal panel gyűjtemény-fejlécén. Ezzel az eredeti mind a
  nyolc kontextusmenüje megvan.
- **Csoportos szerkesztés (#425):** a Szerkesztés menü almenüje eddig üres
  és letiltott volt; mostantól hét egykattintásos effektus és a forgatás
  alkalmazható egyszerre a teljes kijelölésre — háttérben, haladásjelzéssel,
  megszakíthatóan, egy lépésben visszavonhatóan.

### Javítva
- **Az effektus-másolás nem viszi át a vágást (#426):** a menü eddig a régi
  motorra hívott, ami a kép-specifikus vágást is átmásolta volna. Emellett a
  „Csillagozottak kijelölése" eddig a nézet szűrőjét váltotta át, ahelyett
  hogy a csillagos képeket kijelölte volna.

## [0.6.25] – 2026-08-07

### Hozzáadva
- **A saját gyűjtemények végre látszanak (#476):** eddig létre lehetett hozni
  egy gyűjteményt és mappákat tenni bele, de utána sehol nem jelent meg.
  Mostantól a bal panelen saját, csukható fejlécet kap, alatta a benne lévő
  mappákkal.

## [0.6.24] – 2026-08-07

### Javítva
- **Megbízhatóbb tesztek (#475):** a háttérműveletre váró teszt-segéd eddig
  csendben továbbengedte a tesztet, ha a művelet nem fejeződött be időben —
  a hiba így máshol, félrevezető üzenettel bukott ki. Mostantól beszédes
  hibát ad, és a türelmi idő a lassú gépekhez igazodik. A javítás rögtön
  kimutatott egy rejtett hibát az egyik saját tesztünkben is.

## [0.6.23] – 2026-08-07

### Hozzáadva
- **Album és Emberek-album jobbklikk-menüje (#422):** a bal panel album-,
  illetve személy-során. Élő a kijelölés-parancsok, az indexképek
  frissítése és a HTML-export; az album törlése/leírása, a névcímkék és a
  webes műveletek — az eredetihez hűen — szürkén láthatók.

## [0.6.22] – 2026-08-07

### Hozzáadva
- **Három új jobbklikk-menü (#422):** a bal panel üres részén a mappalista
  rendezése (dátum, név, méret, legutóbbi változtatás, fordított sorrend);
  a címkéken a címke rátétele a teljes kijelölésre, az ilyen címkéjű képek
  keresése és a címke eltávolítása; a képtálcán a kijelölés megtartása,
  illetve eltávolítása. Egyik menü sem létezett eddig.

## [0.6.21] – 2026-08-07

### Hozzáadva
- **Indexkép jobbklikk-menüje: 7 helyett 19 parancs (#422):** megjelenítés
  és szerkesztés (félkövéren, mint a duplakattintás művelete), forgatás
  mindkét irányba a teljes kijelölésre, fájl megnyitása, teljes elérési út
  másolása és tulajdonságok. A még nem működő parancsok — az eredetihez
  hűen — szürkén láthatók maradnak.
- **Törlés-gyorsbillentyű az eredeti szerint:** a rácsban `Ctrl+Delete`, a
  nézőben sima `Delete` törli a lemezről; a kettő kizárja egymást.

### Megváltozott
- **Az „Átnevezés…" a helyére került (#422):** kikerült a rács jobbklikk-
  menüjéből, mert az eredetiben a Fájl menüben van — ott (és `F2`-vel)
  változatlanul elérhető.
- **Elrejtés/Megjelenítés (#422):** a menüpont mostantól feliratot vált
  pipa helyett, ahogy az eredeti.

## [0.6.20] – 2026-08-07

### Hozzáadva
- **Mappa jobbklikk-menüje: 2 helyett 15 parancs (#422):** kijelölés-
  parancsok, indexképek frissítése, a mappa rendezésének alapja, keresés a
  lemezen, eltávolítás a Picasából (megerősítéssel) és HTML-export. A menü
  mostantól — az eredetihez hűen — **három helyről** nyílik ugyanazzal a
  tartalommal: a bal panel mappa-sorából, a rács üres területéről és a rács
  mappa-fejlécéből.
- **„Mappaleírás szerkesztése…" ablak:** az eredeti Picasa mezősorával
  (név, dátum + automatikus dátum, zene, a felvétel helye, leírás).

### Megváltozott
- **A mappa dátuma a helyére került (#422):** eddig külön menüpont volt a
  mappa jobbklikk-menüjében, az eredetiben viszont a „Mappaleírás
  szerkesztése…" ablakban van. A funkció nem veszett el, csak oda költözött,
  ahol a Picasában is található.

### Javítva
- Két megerősítő ablak együtt már nem zavarja egymást.

## [0.6.19] – 2026-08-07

### Hozzáadva
- **Jobbklikk-menü a nézőben (#422, 1. lépcső):** a nagy képen eddig
  egyetlen kontextusmenü sem nyílt — most megvan az eredeti Picasa mind a
  17 parancsa, a hivatalos magyar feliratokkal. Élesben működik a
  visszatérés a könyvtárhoz, a hozzáadás albumhoz, a forgatás jobbra/balra,
  az elrejtés–megjelenítés, a fájl megnyitása, a keresés a lemezen, a
  törlés lemezről, a teljes elérési út másolása és a tulajdonságok. A még
  nem működő parancsok — az eredetihez hűen — szürkén láthatók maradnak,
  hogy a menü magassága és a tételek helye soha ne ugráljon.

## [0.6.18] – 2026-08-07

### Javítva
- **Véletlenszerű CI-összeomlás megszűnt (#430):** a weboldal-exportálás
  háttérszála eddig akkor is dolgozhatott, amikor a hozzá tartozó objektumot
  már felszámolta a program — ilyenkor a folyamat összeomlott. A szálat
  mostantól be lehet várni, és a teszt le is várja: a hiba forrása
  minimál-programmal reprodukálva és igazoltan megszüntetve. Ugyanez a minta
  további kilenc vezérlőben is jelen van, a javításuk külön feladat (#438).

## [0.6.17] – 2026-08-07

### Javítva
- **A felső eszközsáv nem törik új sorba (#423):** az „Importálás" gomb
  minden ablakszélességen a sáv bal szélén marad — a hely fogytával előbb a
  rugalmas térköz, majd a keresőmező zsugorodik, végül a szűrő-zóna rejtőzik
  el, a sáv magassága viszont változatlan. A „Szűrők" felirat a csíkon belül,
  az ikonsor fölé került.

### Hozzáadva
- **Mappa-fejléc paritás (#423):** cím Georgia 20 pt, dátumsor Georgia 14 pt,
  50 px bal behúzás; hosszú mappanév halványuló kifutással ér véget („…"
  helyett), a jobb-felső sarokban pedig megjelent a „Szinkronizálás az
  internettel" kapcsoló (az elrendezés része, egyelőre letiltva). A menüsáv
  jobb szélén a „Bejelentkezés Google Fiókkal" hivatkozás.

## [0.6.16] – 2026-08-07

### Hozzáadva
- **Az összes effektus másolása/beillesztése (#426):** egy kép teljes
  szerkesztési lánca átvihető tetszőleges számú másik képre — mappánként
  egyetlen `.picasa.ini`-írással, és a teljes köteg egyetlen visszavonási
  lépésként. Amit nem visz át (kivágás, retus, vörösszem, klip-vágópontok),
  azt nem kézi lista, hanem a `filterdesc` regiszter `mode`/`persist`
  jelzőiből származó gépi szabály dönti el. A menüpontok bekötése még
  hátravan, ezért a jegy nyitva marad.

## [0.6.15] – 2026-08-07

### Hozzáadva
- **Helyfoglaló menüpontok jelölése (#416):** a még nem működő menüpontok
  halványabb felirattal és a sor jobb szélén kicsi, világosszürke ponttal
  jelennek meg — ránézésre látszik, mi működik már és mi csak a helye.

### Javítva
- **Derítőfény-csúszka méretugrása (#415):** a húzás alatt megjelenő
  GPU-előnézet a kép befoglaló dobozához igazodott a ténylegesen kirajzolt
  kép helyett, ezért álló képnél a lap széléig szétnyúlt, majd elengedéskor
  visszaugrott. Az előnézet mostantól pontosan a kirajzolt képet fedi.
- **Tálca-teszt a windows-CI-n (#417):** a „széles ablak" eset fix 1280 px
  helyett a komponens mért küszöbéből származik, így betűkészlet- és
  nyelvfüggetlen.

## [0.6.14] – 2026-08-06

### Javítva
- **Szerkesztő-panel szélessége (#411):** fix 280 px, mint az eredetiben —
  a feliratok nem tördelődnek szét.
- **„Gyakori javítások" fül ikonjai (#411):** a felhasználó képe helyett
  saját rajzú ikonok (sötét fotónál a képes csempék egyformák voltak);
  a Kiegyenesítés ikonon segédvonal-rács; fekvő 3:2 arány.
- **A felezett ikonokon LÁTSZIK az effekt (#411):** a Qt SVG-motorja
  némán kihagyta a vágást, ezért a két fél azonos volt; a féloldalak
  mostantól matematikailag elmetszettek, a színek az eredeti ikonokon
  mért arányokból számítva.
- **Derítőfény (#411):** az ikon és a csúszka egy sorban, összetartozó
  egységként, mint az eredetiben.

## [0.6.13] – 2026-08-06

### Javítva
- **Picasa-hű szerkesztő-panel (#405):** az effekt-gombok mostantól a
  SAJÁT KÉPED kis előnézetét mutatják az adott effekttel (mint az
  eredetiben), nem lapos ikont; a fölösleges „Gyakori javítások" fejléc
  eltűnt; a panelarányok, fül-ikonok, a Visszavonás/Újra és a
  Derítőfény-csúszka az eredetihez igazítva.

## [0.6.12] – 2026-08-06

### Javítva
- **Alsó sáv reszponzivitása (#406):** szűk ablaknál (pl. fél képernyő)
  a gombok már nem lógnak ki — a feliratok helyett ikonok jelennek meg,
  a csúszka zsugorodik. A váltás a feliratok TÉNYLEGES szélességét méri,
  így nyelvtől és rendszerbetűtől függetlenül sosem vág le semmit.

## [0.6.11] – 2026-08-06

### Javítva
- **GPU-shader betöltés (#402):** a shader rossz mappában kereste a
  .qsb fájlt — a GPU-előnézet most már ténylegesen elindul; hiba esetén
  némán a CPU-útra áll vissza, napló-zaj nélkül.
- **Arc-szerkesztő (#402):** a névjavaslat-lista QML-horgony-
  figyelmeztetése megszűnt.

## [0.6.10] – 2026-08-06

### Hozzáadva
- **Arc-téglalapok szerkesztése (#26, 2. kör):** a nézőben rajzolható,
  nevezhető és törölhető arc-keretek, Picasa-kompatibilis mentéssel;
  opcionális contacts.xml-import.
- **GPU-előnézet élesítve (#22):** a finomhangolás-csúszkák húzás közben
  GPU-n frissülnek (ahol van rá mód — enélkül minden a régi úton megy).
- **Nyomtatás és E-mail (#32, részleges):** a tálca Print/E-Mail gombjai
  működnek (oldalhoz igazított nyomtatás; küldés a leveleződdel).

## [0.6.9] – 2026-08-06

### Hozzáadva
- **Személyek-gyűjtemény (#26, 1. kör):** a bal hasáb Személyek listája a
  meglévő `.picasa.ini` arc-adatokból; személyre kattintva az ő képei.
- **GPU-előnézet alapok (#22):** shader-alapú élő előnézet a
  leggyakoribb csúszkákra (derítőfény/árnyék/színhő/telítettség/f-f),
  bitre a CPU-útból származó paritással — RPi5-validálásra vár.
- **Effekt-névlista lezárva (#347):** grain v1 egzakt csővezetékkel;
  a maradék mérnivaló a #317-es golden-körben.

## [0.6.8] – 2026-08-06

### Hozzáadva
- **Egzakt effekt-csővezetékek (#381):** a 4–5. effektfül a Picasa eredeti,
  a filterdesc.xml-ből megfejtett lépéssorai és számértékei szerint
  renderel — a korábbi közelítések helyett.
- **Szűrő-regiszter (#382):** mind a 84 eredeti szűrő adatvezérelt
  leírása; tartomány-validáció, teljes-felbontás/lassú/méretváltó
  jelzők a láncban; 26 további régi szűrőnév felismerve.
- **Szín szerinti keresés (#383):** color:-keresőtokenek + átlagszín-index
  (az elveszett Picasa-funkció visszahozása).
- **UI-hűség (#384):** a mappalista három kék állapota, kétszínű
  indexkép-kijelölés-keret az eredeti constants.ui értékei szerint.

## [0.6.7] – 2026-08-06

### Hozzáadva
- **Retusálás és szöveg a szerkesztőben (#148):** kattintásos folt-
  eltávolítás élő előnézettel; szöveg felvitele a képre.
- **Beállítások-dialógus (#350):** a Picasa 8 fülös beállítás-ablaka;
  élőben a nyelv és a törlés-megerősítés, a többi előkészítve.
- **Exportálás weboldalként (#351):** a Picasa sablonnyelvének teljes
  motorja + „fehér" gyári sablon.
- **Egyéni gyűjtemények és kézi mappadátum (#320):** saját gyűjtemények
  a mappafában; a mappa éve kézzel felülírható.

### Javítva
- Indulási QML-figyelmeztetés a MoveDatabaseDialogban (#377).

## [0.6.6] – 2026-08-06

### Hozzáadva
- **A Picasa 3.9 telepítés mély elemzése — négy új/megoldott formátum.**
  - `docs/specs/filterdesc-registry.md`: a Picasa saját szűrő-regisztere
    (`runtime/filterdesc.xml`) feldolgozva — mind a 84 szűrő csúszkáinak
    neve, tartománya és alapértéke, valamint a 33 Glimmer-effekt teljes
    képfeldolgozó-csővezetéke. Lezárja a „4–5. effektfül paraméterei" és a
    „Vignette analitikus modellje" nyitott pontokat.
  - `docs/specs/picasa-respack-format.md` + `tools/picasa/respack.py`: a
    `respack.yt` bináris erőforráscsomag formátuma **teljesen visszafejtve**
    (2769/2769 réteg hibátlanul kicsomagolható), és előkerült benne a Picasa
    UI **140 `.tre` elrendezés-forrásfájlja**.
  - Az arc-részletadat (`conf/pan/leye/reye/mouth`) formátuma és forrása
    (Neven Vision motor a `Red.dll`-ben) dokumentálva.
  - A `constants.ui` hiteles UI-konstansai bekerültek a dizájn-kézikönyvbe;
    a `Picasa3i18n.dll` 41 nyelvű string-táblájának veszteségmentes
    kinyerési módszere rögzítve.

## [0.6.5] – 2026-08-05

### Hozzáadva
- **Tömeges átnevezés (#366)** a Picasa mintája szerint: dátum-/felbontás-
  utótag, élő példa-előnézet, sorszámozás; több kijelölt képnél automatikusan.
- **„Ne kérdezze újra" (#367):** újrafelhasználható megerősítő dialógus
  perzisztens beállítás-tárral; a törlés-megerősítés már ezt használja.
- **Adatbázis áthelyezése (#368):** Eszközök → Kísérleti → Adatbázis
  áthelyezése… — biztonságos költöztetés integritás-ellenőrzéssel; hiba
  esetén minden marad a régiben.
- **Export-extrák (#369):** exportmappa-név, sorszámozás, vízjel,
  minőség-presetek az eredeti Picasa export-dialógusa szerint.

## [0.6.4] – 2026-08-05

### Hozzáadva
- **Retusálás-eszköz alapjai (#148):** folt-eltávolítás OpenCV-inpainttel a
  render-láncban, `.picasa.ini`-kompatibilis tárolással; szöveg-réteg
  parse/serialize + közelítő rajzoló.
- **Saját, Picasa-hű SVG ikonkészlet (#361):** a tálca és az eszköztár
  ikonokat kapott (a Kollázs/Film a tálcáról is indítható); a geo-szűrő
  igazi ikonnal.
- **Dialógus-paritás 1. kör (#350):** átnevezés- és export-dialógus a FEN-
  forrás szerinti feliratokkal; mappafa-finomítások (#320).

### Javítva
- **A 4. fül effekt-paraméterei mostantól eljutnak a rendererhez (#332)** —
  az importált Picasa-szerkesztések nem az alapértékkel renderelődnek.
- **A név-kizárólista miatt üres scan nem számít „elérhetetlen gyökérnek"
  (#358)** — a kizárt mappák indexbejegyzései kitakarítódnak.
- **Az app-ikon ténylegesen nagyobb (#325)** — a korábbi hamis-zöld
  mérőszám helyett pixel-terület-alapú teszttel.

## [0.6.3] – 2026-08-05

### Javítva
- **Éles ini-kompatibilitás (#357):** a `tint`/`ansel`/`dir_tint` szín-
  paramétere opcionális — a Picasa elhagyja, ha az alapértelmezett színnel
  mentett. Eddig ezek az effektek hibával kimaradtak a renderelésből
  (a felhasználó effekt nélkül látta a képet, traceback-spammel); mostantól
  a dokumentált alapértékkel (fehér) futnak.

## [0.6.2] – 2026-08-05

### Hozzáadva
- **Az eredeti Picasa 3.9 programmappa teljes feldolgozása (#345).** Négy új
  spec: a 46 dialógus FEN-szerkezete, az exe ini-kulcs/effekt-leltára, a
  PBZ-gombok + webexport-sablonnyelv, és a hivatalos Picasa-magyar
  terminológia (#346–#351 jegyek ebből).
- **Szkenner-kizárólista** az eredeti `filters.txt` mintájára (#349): a
  `windows`, `temp`, `Originals`, `.picasaoriginals` stb. mappák kimaradnak
  a bejárásból — a szerkesztési eredetik nem duplikálódnak a rácsban.
- **Új effekt-nevek felismerése** a render-láncban (#347 1. lépés): a
  `grain`, `radtint`, `RoundedEdges`, `Matte`, `NightVision` felismerten
  kalibrálatlan, a „nem renderelhető" jelentésbe számít; a `picnik=1;`
  érvényes jelző-token.

### Javítva
- **Hivatalos Picasa-magyar terminológia (#346):** People→Személyek,
  „Készítsen képfeliratot!", Fókusztávolság, Indexképek és további
  szótári igazítások (15 felirat).
- Az exe-ből azonosított új ini-kulcsok (`[encoding]`, verziókulcsok,
  `hidden`, `moviestart`…) round-trip megőrzése teszttel rögzítve (#348).

## [0.6.1] – 2026-07-31

### Hozzáadva
- **Albumtagság szerkesztése (#9 második fele).** A képek jobbklikk-menüjéből
  mostantól **albumba tehetők** („Hozzáadás albumhoz" — a meglévő albumok
  listájával és „Új album…" ponttal), album-nézetben pedig **kivehetők**
  belőle. Az új album a kijelölt képekkel jön létre.
  - A `.picasa.ini`-be írás mindenhol az **ütközésbiztos** úton megy
    (ugyanazon, mint a csillagozás és a geocímke): ha közben az eredeti
    Picasa is írja a fájlt, egyik változtatás sem vész el.
  - **Amit nem értünk, azt nem bántjuk:** a nem ismert kulcsok (pl.
    `backuphash`) változatlanul maradnak — erre teszt is van.
  - A meglévő album nevét a program **soha nem írja át**; az elnevezés a
    felhasználó döntése marad.
  - Több mappát átfogó kijelölésnél az album definíciója minden érintett
    mappa ini-jébe kiíródik — ahogy az eredeti Picasa is teszi.

## [0.6.0] – 2026-07-31

### Hozzáadva
- **Virtuális albumok a bal hasábon (#9).** A Picasában létrehozott albumok
  mostantól megjelennek az **Albumok** gyűjteményben (a Csillagozott sor
  alatt), névvel és darabszámmal; rájuk kattintva a rács az album képeit
  mutatja — akkor is, ha azok több mappából állnak össze.
  - Az adat forrása a `.picasa.ini`: a `[.album:<token>]` szekciók adják a
    nevet és a dátumot, a képek `albums=` kulcsa a tagságot.
  - Az index bővült (séma v8), de a **meglévő könyvtárat nem kell újra
    indexelni**: a táblák üresen jönnek létre, a következő szinkron tölti
    fel őket.
  - Ugyanaz az album több mappa ini-jében is szerepel (a Picasa mindegyikbe
    kiírja) — ezért definíciónként tároljuk és a listában vonjuk össze. Így
    ha egy albumot a Picasában törölsz, itt is eltűnik, akkor is, ha egy
    másik mappa még hivatkozik rá.
  - Az albumtagság **írása** (kép hozzáadása/kivétele) szándékosan külön
    lépés — az a `.picasa.ini` módosításával jár, és önálló körben jön.

## [0.5.4] – 2026-07-31

### Hozzáadva
- **Kitöltő fény a Gyakori javítások fülön (#337).** Az eredeti Picasa
  Alapvető javítások fülén az ikonrács alatt ott a Kitöltő fény csúszka —
  nálunk eddig csak a Finomhangolás fülön volt. Mostantól mindkét helyen
  megvan, de **egy beállításként**: amelyiket húzod, a másik követi, és a
  mentés is közös. Így a napi használat leggyakoribb korrekciója egy
  kattintásnyira van, anélkül hogy két külön értéket kellene fejben tartani.

## [0.5.3] – 2026-07-31

### Változott
- **A szerkesztő Picasa-szerű kinézete (#338).** A felhasználó jelezte, hogy
  „sima gombok vannak a legtöbb fülön, nem tetszik" — jogosan, mert az
  eredetiben egészen más a panel:
  - **Ikonos fülek** a szoros szöveges tabok helyett: csavarkulcs, nap és
    három ecset (a három effekt-fül színben is elkülönül). Az ikonokat a
    program maga rajzolja, nem rendszer-emojival — így RPi5-ön is
    ugyanúgy néznek ki. A teljes név súgó-buborékban jelenik meg.
  - **Bélyegképes effekt-gombok:** minden gombon a SAJÁT fotó látszik az
    adott effekttel, tehát előre látni, mit csinál. A bélyegképek háttérben
    készülnek (nem akasztják meg a felületet) és gyorsítótárazódnak, ezért a
    csúszkák húzása vagy a visszavonás nem számoltatja újra őket. Amíg egy
    kép nem kész, a gomb a régi kinézetét mutatja — sosem villog üresen.

## [0.5.2] – 2026-07-31

### Javítva
- **Sötét téma: üres gombok az eszköztáron és a tálcán (#336).** Az
  Importálás, a Vissza a könyvtárhoz, az E-mail, a Nyomtatás és az
  Exportálás gomb felirata sötét témában eltűnt: a gomb háttere hardkódolt
  világos volt, a felirata viszont témafüggő — világos szöveg világos
  gombon (mért kontraszt **1,07**). A színek mostantól tokenből jönnek, és
  mérhető tulajdonságokban élnek; teszt őrzi mind a négy kombinációt
  (világos/sötét × engedélyezett/tiltott), minimum 3,0 kontraszttal.
  A felület többi hardkódolt színét is átvilágítottuk: azok sötétben
  3,9–13,0 kontraszttal olvashatók, tehát ez volt az egyetlen valódi hiba.

## [0.5.1] – 2026-07-31

### Hozzáadva
- **Effekt-csúszkák (#316):** a paraméteres effekt gombja már nem fix
  erősséggel csap a képre, hanem — az eredeti Picasa módjára — **alpanelt
  nyit csúszkákkal, élő előnézettel**, alul Alkalmaz/Mégse gombbal. Húzás
  közben a kép azonnal követi a beállítást (ini-írás és visszavonás-lépés
  nélkül); az Alkalmaz teszi a láncra, a Mégse nyomtalanul elveti. Húsz
  effekt kapott csúszkát (Élesítés, Telítettség, Vignetta, Ragyogás,
  radiális elmosás/telítettség, Színezés, Színátmenet, és az 5. fül teljes
  készlete); a paraméter nélküli effektek (Szépia, Fekete-fehér, Melegítés,
  Filmszemcse, Színinvertálás) továbbra is egy kattintás.
  A csúszkák tartományai és alapértékei **mért** értékek: a felhasználó
  valódi Picasa-exportjaiból származó ini-mintákból (`filters-decoded.md`).

### Javítva
- **Fordítás-vesztés elhárítva:** a felület magyar szövegeinek egy része
  nem közvetlen `tr()`-hívásból származik, ezért egy gépi fordítás-frissítés
  elavultnak jelölte és kiejtette őket (például a „0 kép” feliratot). A
  fordítás visszaállt, és a tanulság a projekt memóriájába került.

## [0.5.0] – 2026-07-30

A kiadás a felhasználó éles, Windows-os visszajelzései nyomán készült, és
három eredeti Picasa-képernyőkép-csomag (53 kép) szisztematikus auditjára
épül (`docs/specs/ui-audit-menus.md`, `-editor.md`, `-mainwindow.md`).

### Hozzáadva
- **Mind a 36 Picasa-effekt (#328, #329, #330):** az audit kimutatta, hogy az
  eredeti szerkesztőpanelen **öt** fül van (nálunk három volt), és 36 effekt
  (nálunk 13). A hiányzó 23 megkapta a render-implementációját és a gombját:
  a 4. fülön Infravörös film, Lomo, Holga, HDR, Kinemaszkóp, Orton, 60-as
  évek, Színinvertálás, Hőtérkép, Áttűnés, Poszterizálás, Kéttónusú; az 5.
  fülön Felpörgetés, Lágyítás, Képpontnagyítás, Fókusznagyítás, Ceruzarajz,
  Neon, Képregény, Szegély, Árnyékvetés, Múzeumi matt, Polaroid. Ez nemcsak
  hiányzó funkció volt: az ilyen effektet kapott képeket a PicasaPy eddig
  **effekt nélkül** mutatta. A négy keretes effekt méretet növel, ezért a
  lánc a **vágás után** alkalmazza őket.
- **Élesítés és Vignetta (#315):** két támogatott szűrő évek óta UI nélkül
  állt; az Élesítés az eredetiben az Effektek fül első gombja.
- **Picasa-hű gyűjtemények a bal hasábon (#320):** Albumok, Emberek,
  Projektek, Mappák, Egyebek — csukható fejlécekkel, megjegyzett állapottal.
- **Húzható mappapanel (#322):** látható elválasztó, a szélesség megmarad.
- **~44 hiányzó menüpont (#324)** és az első gyorsbillentyűk (#327).

### Javítva
- **Sötét téma (#314):** a splash logója fehér korongot kapott (eddig
  beleolvadt), a tálca ikonjai láthatóvá váltak, és a szerkesztő gombjainak
  feliratai olvashatók (a kontraszt 1,16-ról legalább 3,45-re nőtt).
- **A gombfeliratok nem vágódnak le (#318)** — tördelés az elide helyett.
- **A görgetősáv megjelent (#323):** eddig a Qt alapértelmezése szerint csak
  görgetés közben villant fel, ezért a felhasználó gyakorlatilag sosem látta.
- **A Mappanézet rendezés csak a rácsot rendezi (#321)**, a mappafát nem.
- **Az effekt-paraméterek eljutnak a rendererhez (#332):** ha a Picasában
  elhúzott csúszka értéke ott van az ini-ben, mostantól az érvényesül.

### Dokumentáció
- **Őszinte effekt-státusz (#317):** a 36 effektből 13 mögött van
  golden-mérés, 22 szakirodalmi közelítés, 1 matematikailag pontos. A
  `docs/specs/filters-decoded.md` új táblája ezt kimondja — a kalibráltság
  látszata félrevezető volt.

## [0.4.70] – 2026-07-25

### Hozzáadva
- **Geocímke: Helyek-panel, térkép és szerkesztés (#30):** a képek helye
  mostantól látszik és állítható. A hely két forrásból jön — a
  `.picasa.ini` `geotag=` kulcsa (ez az erősebb) és a fájl EXIF GPS-adata
  —, mindkettő az indexbe kerül (séma v7, migráció újraindexelés nélkül).
  Új **Nézet → Helyek** panel: OpenStreetMap-térkép a látszó képek
  jelölőivel (jelölőre kattintva kijelöli a képet), jobb kattintással a
  kijelölt képek erre a helyre kerülnek, és egy gombbal törölhető a
  geocímke (az EXIF-ben rögzített gépi hely megmarad). A szűrősor
  **geo-ikonja élesedett**: egy kattintással csak a hellyel rendelkező
  képek látszanak. A térkép külön, Loaderrel töltött komponens: QtLocation
  nélküli telepítésen a panel a szerkesztéssel együtt működik, csak a
  térkép helyén jelenik meg magyarázó szöveg.

## [0.4.69] – 2026-07-25

### Hozzáadva
- **Képkollázs és mozgófilm (#29):** a Létrehozás menü két pontja élesedett.
  A **kollázs** négy típust ad — képrács, kontaktmásolat, keretes mozaik és
  (magvas véletlennel, tehát megismételhető) képhalom —, 1600×1200-as
  vászonra, fehér paszpartuval, JPEG-be mentve. A **mozgófilm** MP4-es
  diavetítés-videót ír a kijelölésből (720p/1080p, állítható képenkénti idő,
  automatikus áttűnés), a haladást képenként mutatva. Mindkettő háttérszálon
  fut, egy hibás kép nem viszi el a munkát (a kimaradt képek száma a
  végeredmény-dialógusban látszik), és az ékezetes útvonal is működik
  (bájt-alapú írás, #190 tanulsága).

## [0.4.68] – 2026-07-25

### Hozzáadva
- **Sötét téma (#28):** a Nézet menü új, kapcsolható „Sötét téma" pontja —
  az alapértelmezés továbbra is a világos felület (Picasa-paritás), a
  választás pedig megjegyződik a következő indulásig (QSettings
  `view/darkTheme`). A `Theme.qml` tokenjei párba álltak (világos/sötét),
  a tokennevek változatlanok, így a felület minden rétege — mappafa,
  rács, dialógusok, eszköztár, tálca, néző és a Qt Controls-paletta is —
  egyszerre vált. A márkaszínek (logó) és a fotó fölé kerülő rétegek
  mindkét témában azonosak. A korábban hardkódolt fehér/szürke felületek
  tokenre cserélve (a dizájn-kézikönyv téma-politikája bővült a teljes
  világos/sötét tokentáblával).

## [0.4.67] – 2026-07-24

### Javítva
- **A QML-figyelmeztetés-őr Windowson elhasalt környezeti zajra (#309):** a
  0.4.65-ben bevezetett őr (#305) MINDEN Qt-figyelmeztetésre hibát dobott,
  így a windows-latest CI-lábat olyan üzenetek buktatták, amiknek semmi
  közük a kódhoz (hiányzó fontkönyvtár a runneren, `OpenThemeData() failed`
  offscreen módban, natív stílus testreszabási figyelmeztetése). Az őr
  mostantól kizárólag a QML-SZKRIPTHIBÁKRA hasal el (`TypeError`,
  `ReferenceError`, `SyntaxError`, „Unable to assign", „is not a
  function") — ezek platformfüggetlenül mindig valódi kódhibák. Az
  osztályozó külön modulba került (`tests/support/qml_warning_filter.py`)
  és saját tesztet kapott valódi üzenet-mintákkal mindkét oldalról.

## [0.4.66] – 2026-07-24

### Javítva
- **A duplikátum-kereső használhatóvá vált nagy könyvtáron (#294):** eddig
  feltétel nélkül a TELJES indexelt könyvtárra futott, haladásjelzés és
  megszakítás nélkül — 140 000 képnél az ablak gyakorlatilag némán állt.
  Most: **hatókör-választó** (kijelölés / aktuális mappa+almappák / teljes
  könyvtár), alapból a szűk hatókörrel; **folyamatjelző és Mégse gomb**;
  **redukált dekódolás** a perceptuális hashhez (4000×3000-es fotón
  126,9 ms → 9,3 ms, azonos hash-értékkel); a hash-ek **tárolása az
  indexben** (új `photo_hashes` tábla, séma v6), így az ismételt keresés
  azonnal indul; és **sávos jelöltszűrés** az O(n²) páronkénti összevetés
  helyett (3000 hash: 2,94 s → 0,80 s; több ezer azonos lenyomatú kép
  7,9 s helyett azonnal) — egzakt, hamis negatív nélkül.
- **A dedup-ablak nem veszi el a rács bélyegképeit (#298):** eddig a
  keresés lecserélte a bélyegkép-provider TELJES regisztrációját, amitől a
  mögötte lévő rácson szürke helyőrzők maradhattak. Mostantól saját
  id-sávban, additív regisztrációval dolgozik, és bezáráskor elengedi.

## [0.4.65] – 2026-07-24

### Javítva
- **QML null-őrök (#305):** a `controller` context property a QML-engine
  leépítésekor `null` lesz, miközben a kötések még egyszer kiértékelődnek —
  ez tucatnyi `Cannot read property … of null` figyelmeztetést szült a
  tesztek kimenetében, ami elnyomta a valódi QML-hibákat (a #232-es
  hisztogram-saga tanulsága szerint épp azok bújnak meg ott). Az érintett
  kötések null-őrt kaptak, értelmes alapértékkel — rendes futás közben a
  viselkedés változatlan.

### Hozzáadva
- **QML-figyelmeztetés-őr a tesztekben (#305):** a `qml_functional`
  conftest autouse fixture-je `qInstallMessageHandler`-rel figyeli a
  Qt/QML üzeneteket, és hibára futtatja a tesztet, ha bármilyen
  figyelmeztetés megjelent — így a jelenség nem tud visszaszivárogni.

## [0.4.64] – 2026-07-24

### Változott
- **A README összhangba hozva a kóddal (#299):** az „Amit még nem tud"
  szakasz eddig a *szerkesztő eszközöket* sorolta hiányzóként, holott a
  szerkesztő (20+ szűrő, mentés/Visszaállítás, hisztogram, effekt-vágólap)
  régóta kész és bekötött. A „Fő képességek" kiegészült az Időrend
  nézettel, Exporttal, Duplikátum-kezelővel, Import forrásból funkcióval,
  XMP-exporttal és a Picasa-mappák átvételével; a PMP/db3-import állítása
  pontosítva (olvasó-réteg kész, az indexbe-import a nyitott rész, #1).
- **Teszt-parancs a dokumentációban:** a README és a CONTRIBUTING is a
  `python3 -m pytest`-et ajánlotta — pont azt, amiről a projekt tudja, hogy
  Qt/GIL-deadlockba ragad (#53, #155). Mindkettő a `scripts/run_tests.py`-t
  adja elsődlegesként.

### Hozzáadva
- **Ruff-lint és lefedettség-mérés a CI-ben (#300):** `[tool.ruff]`
  konfiguráció (a ruff alap-négyese + bugbear; a `PL*` család szándékosan
  kimarad), önálló `lint` job a CI-ben, és a `scripts/run_tests.py --cov`
  kapcsoló, ami a darabolt futtatás részfutásait `coverage run -p` alá
  teszi, majd összesít. A 7 forrásbeli bugbear-találat javítva (nem
  elnyomva). Jelenlegi összesített lefedettség: **95%**.

## [0.4.63] – 2026-07-24

### Javítva
- **Kis-nagybetű-tűrő ini-szekciónév (#296):** a szekciónév-keresés eddig
  pontos egyezést várt, miközben a kulcsokat casefold-osan illesztettük. Ha
  az ini `[IMG_1234.JPG]`-t tartalmazott, a fájl viszont `IMG_1234.jpg` volt
  (Windows/NAS: kis-nagybetű-független fájlrendszer), a kép **csillag,
  felirat, forgatás és `filters=` nélkül** indexelődött, íráskor pedig
  második szekció keletkezett ugyanarra a fájlra. Mostantól pontos egyezés →
  casefold-os visszaesés (a pontos találat nyer), és minden író metódus
  ugyanezen a feloldáson megy; az eredeti fejléc-betűzés változatlan marad.
- **Ütközésbiztos ini-írás a fájlműveleteknél (#295):** az áthelyezés, az
  átnevezés és a másolás közvetlen `load`+`save` párost használt az
  ütközésbiztos `update_document` helyett — a párhuzamosan futó eredeti
  Picasa módosítása némán felülíródott. Mindhárom átállítva; részleges
  hibánál magyar, cselekvésre fordítható üzenet, és az `IniConflictError`
  eljut a felhasználóig.
- **Mentés-visszagörgetés (#297):** ha a mentés ini-könyvelése elbukott (pl.
  tartós írásütközés), a kép már tartalmazta a beégetett láncot, de a
  `filters=` is bent maradt — a következő megnyitáskor a renderelő
  másodszor is ráfutott. A képfájl mostantól visszaáll a hiba előtti
  állapotba, mielőtt a kivétel továbbmegy; a `revert` ugyanígy.

## [0.4.62] – 2026-07-24

### Javítva
- **Hibás `filters=` bejegyzés nem dobja el a teljes renderelést (#301):** az
  `apply_filters` eddig csak az ISMERETLEN NEVŰ szűrőket hagyta ki némán; egy
  ismert nevű, de hibás paraméterű op (`tilt=1;` paraméter nélkül,
  `crop64=1,zzz;`) kivételt dobott. A hibatűrés a három hívóból (bélyegkép-
  gyorsítótár, élő előnézet, export) átkerült magába az `apply_filters`-be:
  a hibás op kimarad, a lánc TÖBBI TAGJA lefut, a kivétel a logba kerül.
  Az `EditSession.crop()`/`tilt_param()` hibás értéknél `None`-t ad, így a
  „Paste All Effects" egy sérült, idegen láncon sem száll el.

### Változott
- **EditSession-refaktor (#302):** a `set_crop`/`set_tilt`/`set_finetune`
  háromszor kimásolt „cseréld a helyén, vagy fűzd a végére" ciklusa közös
  helperbe (`_with_single_layer`) került; `session.py` 441 → 378 sor,
  viselkedésváltozás nélkül.

## [0.4.61] – 2026-07-24

### Javítva
- **Symlinkelt mappák bejárása (#303):** a scanner eddig `follow_symlinks=False`
  miatt nem lépett be a symlinkelt almappákba — NAS-os elrendezésnél
  (`~/Kepek/Regi -> /mnt/nas/foto/regi`) a PicasaPy szótlanul nulla képet
  talált ott. A bejárás mostantól követi a symlinkeket, `(st_dev, st_ino)`
  alapú ciklusvédelemmel (symlink-kör és önmagára mutató link is elvágódik,
  figyelmeztetéssel), a törött symlink pedig csendben kimarad.
- **Nagy mappa szinkronja (#304):** a `_prune_photos` a mappa összes
  fájlnevét egyenként paraméterezte egy `NOT IN (…)` listába, ami 32 766
  (`SQLITE_MAX_VARIABLE_NUMBER`) fölött `sqlite3.OperationalError`-ral
  buktatta a szinkront. Helyette ideiglenes tábla + al-SELECT — a
  paraméterszám kötött, az FTS-triggerek változatlanul lefutnak.

## [0.4.60] – 2026-07-24

### Javítva
- **CI-deadlock (#155):** a `tests/app/test_qml_functional.py` (~68 teszt egy
  fájlban) Windowson processzen belül, véletlenszerű helyen deadlockolt
  (#53-as GIL↔Qt osztály: sok QML engine/ablak-életciklus egy processzben).
  A fájl `tests/app/qml_functional/` alá bontva 6 kisebb, témába vágó fájlra
  (közös `qml_app` fixture-rel), amelyeket a darabolt futtató KÜLÖN-KÜLÖN
  processzben futtat — processzenként jóval kevesebb életciklussal. A korábbi
  Windows-kizárás (`_WINDOWS_DEADLOCK_FILES`) törölve, a fájl így minden
  platformon fut. A tesztek tartalma változatlan (tiszta átszervezés).

## [0.4.59] – 2026-07-24

### Hozzáadva
- **Import forrásból (#23):** az eszköztár korábban tiltott „Import" gombja
  élesítve — forrás-mappa (pl. fényképezőgép/kártya, DCIM-szerkezettel is)
  választása, a talált képek bélyegképes előnézete, cél-mappa + dátum-alapú
  mappa-sablon (`{YYYY}/{YYYY}-{MM}-{DD}`, az Időrend nézettel közös
  dátum-feloldással), másolás (nem-destruktív alapértelmezés) vagy áthelyezés,
  haladásjelzéssel. Új `picasapy.fileops.copy` (ütközésbiztos másolás) és
  `picasapy.importsource` (Qt-mentes szkennelés + sablon-logika).

## [0.4.58] – 2026-07-24

### Hozzáadva
- **Duplikátum-kezelő UI (#287):** kezelő-felület a `picasapy.dedup` mag fölé —
  az Eszközök → „Find Duplicates…" pontból indítható. A pontos és hasonló
  csoportok bélyegképes listája; csoportonként a megtartandó kép választható,
  a többi **nem-destruktív alapértelmezéssel** a forrásmappa „Duplikátumok"
  almappájába helyezhető át, vagy a Kukába törölhető.

## [0.4.57] – 2026-07-24

### Hozzáadva
- **Időrend nézet (#24):** a Picasa Timeline megfelelője — a teljes könyvtár
  fotói dátum szerint, korszakokra (év/hónap) bontva, csökkenő sorrendben
  (legújabb elöl) böngészhetők. Belépés: **Ctrl+5** vagy a Nézet → Timeline
  menüpont. Új `picasapy.timeline` mag (GUI-mentes, tesztelt csoportosítás);
  dátum-forrás az EXIF `taken_at`, ennek hiányában (RAW/videó, olvashatatlan
  EXIF) a fájl-mtime.

## [0.4.56] – 2026-07-23

### Hozzáadva
- **Nem-destruktív mentés-mag (#21):** új `picasapy.edit.save` — mentéskor a
  renderelt kép az eredeti helyére kerül, az EREDETI érintetlen példánya a
  `.picasaoriginals` almappába (az első eredetit őrizve), a `.picasa.ini`-ben
  a szerkesztési lánc `redo=`-ba, `originhash` frissül, a `filters=` törlődik
  — mind a round-trip ini-rétegen át (ismeretlen kulcsok bitre megőrizve). A
  `revert` a `.picasaoriginals`-ból állítja vissza az eredetit. Megjegyzés: az
  `originhash` képlete és a `filters→redo` szabály józan, tesztelt feltételezés,
  valódi Picasa-mintán validálandó.

## [0.4.55] – 2026-07-23

### Hozzáadva
- **Duplikátum-kereső mag (#31):** új `picasapy.dedup` modul azonos és hasonló
  képek felderítésére — pontos duplikátumok tartalom-hash-sel (SHA-256,
  méret-előszűréssel), hasonló képek 64 bites dHash + Hamming-távolság
  klaszterezéssel (union-find, alapértelmezett küszöb 10). A `find_duplicates`
  immutábilis, determinisztikus eredményt ad. (A kezelő-UI külön jegy: #287.)

## [0.4.54] – 2026-07-23

### Hozzáadva
- **XMP sidecar-export MWG-RS arcrégiókkal és HierarchicalSubject-tel (#27):**
  új `picasapy.export.xmp` réteg, ami a Picasa-oldali kulcsszavakat, feliratot
  és arcrégiókat digiKam/Lightroom-kompatibilis `.xmp` sidecarba írja — az
  adat így nem ragad a `.picasa.ini`-be (UX-alapelv 5). A `rect64`
  (bal/fel/jobb/alul) régiók a MWG-konvenció szerinti KÖZÉPPONT-alapú,
  normalizált Area-koordinátákra váltanak; a nevesített arcok `People|Név`
  hierarchikus címkeként és `mwg-rs:Regions` régióként is megjelennek. A
  fotó-szintű `xmp_export` réteg a kép melletti `.picasa.ini`-ből olvas
  (kulcsszó/felirat/`faces=` + `[Contacts2]`-névfeloldás), a pixelméretet a
  kép fejlécéből veszi, és atomikusan `<fájlnév>.xmp` sidecart ír. (UI-bekötés
  külön lépés.)

## [0.4.53] – 2026-07-23

### Hozzáadva
- **Paraméter-sweep `.picasa.ini`-generátor a #190 effektjeihez (#190 2. kör):**
  új `tools/golden/make_param_sweep.py` a #190 1. körben azonosított 23
  effekt-kulcshoz előre megírt `.picasa.ini`-variánsokat generál — a fő
  erősség-paramétert a feltételezett tartományán 5 ponton végigléptetve,
  a `.picasa.ini`-t a projekt round-trip ini-rétegén át írva. Így a
  csúszka↔paraméter leképezéshez a felhasználónál csak egy tömeges Picasa-
  export marad (magyar `UTMUTATO.md`-vel). A tényleges csúszka-jelentés az
  export feldolgozásával derül majd ki.

## [0.4.52] – 2026-07-23

### Javítva
- **A PicasaPy-ikon kitölti a vásznat (#267):** a forrás `icon.png`/`icon.ico`
  körüli vastag átlátszó margó levágva, a rajzolat most a vászon ~92%-át
  tölti ki (előtte 82–90%), így a Windows Start menüben / Asztalon nem tűnik
  kisebbnek az eredeti Picasa 3 ikonnál. Új, újrafuttatható
  `tools/regenerate_icon.py`. (A végső vizuális elfogadás a felhasználónál.)

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

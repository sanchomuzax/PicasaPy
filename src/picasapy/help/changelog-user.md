# Mi változott?

Felhasználói szemszögű változásnapló: csak az, ami a képernyőn is
látszik. A részletes, fejlesztői változásnapló a program `CHANGELOG.md`
fájljában van.

## 2026-09-13

**Két kép egymás mellett a nézőben**

- A néző alsó sávjában három kis szegmens jelent meg. Az **Ugyanazon kép
  megjelenítése kétszer** a szerkesztés összehasonlítására való: balra a
  **szerkesztés előtti** kép, jobbra a mostani. A negyedik szegmenssel
  (**Fókusz váltása a képek között**) váltasz a két oldal közt; az
  aktívon **Kijelölve** felirat áll.
- A **Két különböző kép megjelenítése** szegmens látszik, de **még nem
  működik** — szándékosan tiltott, hogy ne tűnjön úgy, mintha elromlott
  volna. Lásd [Nézegetés](features/nezegetes.md).

**Színkezelés használata**

- Új, működő kapcsoló a **Nézet** menüben: figyelembe veszi a képbe
  beágyazott színprofilt (például az Adobe RGB-t), és eszerint alakítja
  át a képet a képernyőre. Alapból ki van kapcsolva, és megmarad a
  következő indításig. A képfájljaidhoz nem nyúl. Lásd
  [Beállítások](features/beallitasok.md).
- A **Mac gamma (1.6)** és a **Lineáris gamma (2.2)** megjelenítési mód
  eddig egymás eredményét adta. Megjavult.

**Egyszerűsített fanézet**

- A **Nézet ▸ Mappanézet ▸ Egyszerűsített fanézet** mostantól tényleg
  szűkít: csak a **figyelt mappáid** ágait mutatja, ahogy az eredeti
  Picasa tette. Eddig csak a hosszú útvonalakat vonta össze, mappát sosem
  rejtett el. Ha a program még nem tudja, melyek a figyelt mappáid, a
  teljes fa marad. Lásd [A könyvtár](features/konyvtar.md).

**Biztonsági mentés**

- A másolás a **háttérben** fut: az ablak közben használható marad.
- Haladásjelző csík és „Másolás (12/340) fájl" alakú számláló mutatja,
  hol tart.
- Új **Megszakítás** gomb. A megszakítás nem veszít el munkát: a
  következő futás pontosan a hiányzókkal folytatja.
- A mentés indításakor a program azt is kiírja, **hány CD-re vagy
  DVD-re** férne az adat. Lemezt továbbra sem ír. Lásd [Képek biztonsági
  mentése](features/biztonsagi-mentes.md).

**Szerkesztő**

- A sok számolást igénylő effektek (Élesítés, Filmszemcse, Ragyogás,
  Képregény, Árnyékvetés, HDR-szerű, Holga-szerű, Lomo-szerű, Neon,
  Orton-szerű, Ceruzarajz, Poszterizálás) mostantól **csúszkahúzás közben
  is a háttérben** számolnak: az ablak nem fagy be, a kép a számolás
  végén frissül, és az alsó kék sávon látszik, hogy dolgozik.
- Az előnézet azoknál az effekteknél, amelyek csak teljes felbontáson
  helyesek, a kép **eredeti méretén** készül el, és csak utána
  kicsinyedik le — így azt látod, ami a kimentett fájlba is kerül.
- A **Neon** effektnek **színválasztója** lett: te adod meg, milyen
  színnel világítsanak a kontúrok. Eddig egy „Intenzitás" csúszka volt a
  helyén, ami valójában a hatás erejét állította.
- A **Lágyítás** két csúszkája a helyes nevet kapta (a lágyítás
  erőssége és a hatás ereje). Az egyik csúszka eddig „Sugár" néven mást
  állított, mint amit a felirata ígért. A csempe neve is **Lágyítás** — a
  súgó eddig tévesen „Lágy fókusz"-ként írta.

**Kollázs**

- A **bepattintó forgatás-igazítás** (a bal oldali kis gombsor és a
  **Forgatás igazítása** almenü) mostantól **minden elrendezésnél**
  működik, nem csak a Képkupacnál — eddig a rácsos típusoknál szürke
  volt. Lásd [Kollázs](features/kollazs.md).

**Jobb oldali fiók**

- A fiók **becsúszva** nyílik és záródik, csukott állapotban pedig
  visszaadja a helyét a könyvtárnak.
- A fiók széle mentén egy **nem látszó, keskeny sáv** is billenti — így
  egérrel is nyitható-zárható, nem csak a menüből, a tálcáról vagy a
  **Ctrl+0** billentyűvel.

**Apróbb változás**

- A nézetváltó gombok, az eszköztár szűrői, a szerkesztő fülei és a
  néző léptető gombjai **a gomb lenyomásakor** hatnak, nem a felengedéskor
  — ahogy az eredeti Picasában.

**Telepítés Windowsra**

- Minden kiadáshoz készül **telepítő** (`PicasaPy-Setup-<verzió>.exe`):
  letöltöd, elindítod, kész — Pythont nem kell telepítened hozzá. Start
  menü bejegyzést és kérésre asztali ikont készít, és a Programok és
  szolgáltatások alól eltávolítható. Lásd [Első
  lépések](getting-started.md).

## 2026-09-12

**Képek biztonsági mentése — új fejezet**

- Az **Eszközök ▸ Képek biztonsági mentése…** mostantól **működik**.
  Nevesített **mentés-készletet** hozol létre: hova mentsen, és mit
  vigyen át (minden fájltípus / minden kép videók nélkül / csak
  fényképezőgép-adatos JPEG-ek). A készlet megjegyzi, mit mentett már el,
  ezért a második futás csak az újat és a megváltozottat másolja.
- A képek mellé a `.picasa.ini` fájlok is átmennek, a cél gyökerébe pedig
  egy `files.txt` lista kerül arról, mi került át. CD-re és DVD-re nem
  tud írni a program: a cél mindig egy mappa. Lásd
  [Képek biztonsági mentése](features/biztonsagi-mentes.md).

**Diavetítés**

- A vetítés mostantól a **teljes ablakot** kitölti: a menüsor, az
  eszköztár és a képtálca a vetítés idejére eltűnik.
- A vezérlősávon **átmenet** választható: Kivágás, Szétoszlás, Szétoszlás
  feketén át, Szétoszlás fehéren át, valamint **Pásztázás és nagyítás**.
- A **Diaidő** a sáv **−** és **+** gombjával 1 és 30 másodperc közt
  állítható.
- Egy gomb körbejárja a feliratmód három állását: a felirat, a fájlnév,
  vagy semmi.
- Mindhárom választás megmarad a következő vetítésre.
- Az áttűnés a **közvetlenül előző** képet mutatja, és a kimenő kép
  átveszi a dia nagyítását és elfordulását.

**Egy jobb oldali fiók négy hasáb helyett**

- A Címkék, az Emberek, a Helyek és a Tulajdonságok panel mostantól
  **ugyanabban a fiókban** vált, közös fejléccel. A fejléc közepén annak
  a panelnek a neve áll, amelyik látszik; balra a **Váltás a kis és a
  nagy oldalpanel közt** gomb, jobbra az **Oldalpanel bezárása**.
- Eddig mind a négy panelnek külön szélessége és külön fejléce volt.

**Tükrözés**

- Két új billentyű: **Ctrl+Shift+H** vízszintesen, **Ctrl+Shift+V**
  függőlegesen tükrözi a kijelölt képeket (a nézőben azt, amit látsz).
  Ugyanaz a billentyű vissza is fordítja. Menüpontja nincs — az eredeti
  Picasában sem volt.
- A tükrözés a kép melletti `.picasa.ini` fájlba kerül, és látszik a
  bélyegképen, a mentésben, az exportált fájlban, a levélmellékletben és
  a weboldal-exportálásban is.

**Rendezés szín szerint**

- A **Mappa rendezése** almenü negyedik szempontja a **Szín**: a színes
  képek jönnek elöl, a szivárvány sorrendjében, utánuk a színtelenek.

**Weboldal-exportálás**

- Egy sablon helyett **hét** van: három háttérszín (fehér, szürke,
  fekete), mindegyik kétféle csempével — sima és passzpartus keretes —,
  valamint egy **XML (gépi)** sablon, ami nem weboldalt, hanem egyetlen
  adatfájlt ír.
- A választó **kis előnézeti rajzot** mutat mindegyikhez.
- A célmappa előre ki van töltve: a képmappádon belüli **Picasa HTML
  exportok**.

**Szerkesztő**

- A **Vörösszem** eszközben egyetlen keretet is ki lehet venni: kattints
  bele. Átfedő kereteknél a később felvett esik ki.
- A **Shift** billentyű most már **élesben is** átváltja az
  effekt-csempéket: elég lenyomni, miközben az effekt-fülön állsz.
- A Vágás, a Vörösszem és a Retusálás panelén az útmutató szövege
  teljesebb lett — a retusálásnál kiderül, hogy nagyított képen a
  **Ctrl** lenyomva tartásával lehet pásztázni.
- A szépia, az életlen maszk, a vignetta és a vetett árnyék a
  visszafejtett eredeti számítást követi, tehát közelebb kerül ahhoz,
  amit a Picasa adott.

**Biztonság és figyelmeztetések**

- Kilépéskor a program **rákérdez**, ha még fut valamilyen háttérmunka —
  például exportálás vagy arcfelismerés. Ez az ablak „X" gombjára is
  vonatkozik, és nem lehet kikapcsolni.
- Az importálás **Minden törlése a kártyáról** választása részletes
  figyelmeztetést ad: hány fájl törlődik, hány marad ki másodpéldány
  miatt, és hányat nem ismer fel a program. Ha a forrást még nem
  pásztázta végig, azt mondja meg — számot nem találgat.
- A **Címkék** panel **előre szól**, ha a kijelölésben írásvédett kép
  van, és nem engedi elkezdeni a gépelést.

**Beállítások**

- Az **Általános** fülön élő lett a **Gyorsítótár ürítése…** gomb:
  rákérdez, majd megmondja, mennyi helyet szabadított fel. A bélyegképek
  szükség szerint újra elkészülnek.
- A bélyegképek több méretben készülnek, ezért a kisebb indexkép-méretek
  **érezhetően gyorsabban** jelennek meg.

**Videók**

- Öt kiterjesztés eddig némán kimaradt a beolvasásból: `.tp`, `.ts`,
  `.m2v`, `.ogg` és `.ogv`. Ezek fájljai ott voltak a mappában, de a
  rácson nem jelentek meg. A **Fájl hozzáadása…** választója is ismeri
  már ugyanazt a listát.
- Ha egy videóhoz a régi Picasában kezdő- és végpontot adtál meg, a
  lejátszás **érvényesíti**: a kezdőpontra ugrik, a végpontnál megáll. A
  pontokat a PicasaPy felületén ma még nem lehet megadni.

**Javítások**

- Az **asztali háttérkép** Windowson is beáll.
- Wayland-asztalon a program megmondja, hogy a `qt6-wayland` csomag
  hiányzik, ahelyett hogy angol hibaüzenettel megállna.
- Az **álló tájolású** fényképek megjelenített mérete számít: helyesen
  kapnak helyet a kollázsban, helyes az 1:1 nagyítás és a felbontás
  felirata.
- A bal hasáb mappasorain **egyetlen** bélyegkép áll a kupac helyett, és
  a fanézetben mindig látszik — ott ezért a menüpont szürke.
- A **Szöveg beillesztése** egyszerre, egy menetben adja a feliratot a
  teljes kijelölésnek, így egyetlen kép sem marad ki.
- Az effekt-csempék jelvényéről eltűnt a mindig „1"-et mutató szám, és a
  jelvény a csempe sarkába került.
- A hisztogram melletti felvételi adatok rövidebb, fotós alakban állnak
  (`6.7 mm`, `f/1.7`, `2.5 s`), és a vaku adata csak a Tulajdonságok
  panelen szerepel — ahogy az eredeti Picasában is.
- A jobb oldali fiók a jobb szélhez igazodik, ezért a méretváltó gomb
  mindkét irányban működik.

## 2026-09-11

**Másodpéldányok: új, gyors nézet**

- Az **Eszközök ▸ Kísérleti ▸ Fájlok másodpéldányainak megjelenítése**
  mostantól **nem ablakot nyit**, hanem szűrt nézetbe visz: a rács csak
  azokat a képeket mutatja, amikből több példány van. Kilépni a zöld sáv
  **Vissza az összes megtekintéséhez** gombjával lehet, vagy a keresősávon
  megjelenő másodpéldány-jelvénnyel. A billentyűje **Ctrl+F6**.
- A korábbi duplikátum-kezelő ablak megmaradt, csak külön menüpontra
  került: **Másodpéldányok kezelése…**.
- A kezelő **Mégse** gombja akkor sem ragad be, ha a keresés épp abban a
  pillanatban ért véget.

**Keresés**

- Működik az eszköztár **idő-csúszkája**: jobbra húzva egyre frissebb
  képek maradnak a rácson, és a zöld sáv kiírja, mit szűrtél („Legfeljebb
  9 hetes képek."). A bal széle kikapcsolja.
- Hat szín menüből is kereshető: **Eszközök ▸ Kísérleti ▸ Keresés…**
  almenü.
- A keresés teljes találatából album lehet: **Eszközök ▸ Kísérleti ▸
  Keresési eredmények mentése…**.
- A keresőmezőn már **jobbgombbal** is elérhető a Beillesztés, a Másolás
  és a többi szövegparancs.

**Címkék és feliratok**

- Egy címke tartalmából rendes album készíthető: **Eszközök ▸ Kísérleti ▸
  Címke megjelenítése albumként…**.
- A **Szerkesztés ▸ Szöveg másolása** és **Szöveg beillesztése** működik:
  egy képfeliratot végig lehet vinni egy egész sorozaton.
- A képtálca fölötti kék csík kiírja, mely **címkék** szerepelnek a
  kijelölésben és hány képen, a dátum és a méret pedig rövidebb alakot
  kap, ha a képek egyazon napról valók.

**Arcok**

- Ha nevet adsz egy arcnak, a program magától a kép mellé írja az arc
  helyét és nevét, hogy más fényképkezelők is felismerjék. A képfájlhoz
  nem nyúl.
- Egy egész mappára is kiíratható: **Eszközök ▸ Kísérleti ▸
  Arcinformációk írása XMP-adatokba…**. Közben látszik a haladás, és
  **Mégse** gombbal megszakítható.

**Asztali háttérkép**

- Új fejezet a súgóban. A **Létrehozás ▸ Beállítás háttérképként…**
  paranccsal egy kijelölt képből, a kollázs-panel **Asztali háttérkép**
  gombjával pedig egy kollázsból lesz háttérkép. Mindkettő másolatot
  készít, és középre helyezi a képet.

**Fájlműveletek**

- Működik a **Szerkesztés ▸ Beillesztés** (**Ctrl+V**): a vágólapra tett
  fájlok a kiválasztott mappába kerülnek. Névütközésnél új nevet kapnak,
  tehát semmi nem íródik felül.

**Új billentyűk**

- **Ctrl+3** a kijelölt képet megnyitja a nézőben, **Ctrl+F6** a
  másodpéldányok nézete, **Ctrl+F7** hasonló képeket keres, **Ctrl+F8**
  törli a hasonlóság-mintát, **Ctrl+Shift+B** fekete-fehérré,
  **Ctrl+Shift+E** pedig „Jó napom van"-nal javítja a kijelölt képeket.

**Megjelenés**

- A bal hasáb bejegyzései saját ikont kaptak: a mappa **kék** (eddig
  sárga volt), a rendes album narancs könyv, a Csillagozott képek zöld
  könyv csillaggal, a projektmappák lila könyv csillaggal, a címke pedig
  szürke címke.
- Albumra kattintva — amíg nincs kijelölt képed — a képtálcán egy
  borítókép áll a felirattal, hogy hány kép van benne.
- A legördülő listák és a görgetősáv az eredeti Picasa rajzát kapták.
- A szerkesztőben megnyíló kérdések mögött a felület elhalványul, hogy
  látszódjon, mire kell válaszolni.
- A szövegráíró panel feliratai a vezérlőik mellé kerültek; az
  átlátszóság-csúszka felirata **Átlátszóság**.
- A **Színinvertálás** csempéjén is ott a kék jelvény, ami az egy
  kattintással ható effekteket jelöli.

**Beállítások**

- A **Beállítások ▸ Általános** fülön a **Duplikátumok észlelése
  importáláskor** kapcsoló működik, és ugyanazt az egy beállítást mutatja,
  mint az importáló ablak **Duplikátumok kizárása** jelölője.

**Gyorsaság**

- Valamivel gyorsabb az indulás: a nagy nézet néhány ritkán használt
  ablaka csak akkor épül fel, amikor tényleg kell.

## 2026-09-10

**Fájlműveletek: a félbemaradt áthelyezés nem hagy kárt**

- Ha egy kép áthelyezése elakadt (zárolt fájl, írásvédett mappa), eddig a
  **másolat már ott volt a célban**, az eredeti pedig a helyén — vagyis a
  képből kettő lett, és a hibaüzenet erről nem szólt. Mostantól a program
  visszatörli a félkész másolatot, és a kép a régi helyén marad. Ugyanez
  a védelem működik a Kukába helyezésnél, a visszaállításnál és a
  megőrzött eredetik költöztetésénél.
- Ha egy **mappa** áthelyezése akadt el menet közben, a célban ott maradt
  a félig átmásolt mappa, és a következő próbálkozás már azzal állt meg,
  hogy „ilyen nevű mappa már létezik". Most a célban nem keletkezik
  semmi, amíg a másolás végig nem ment.

**Diavetítés**

- A **Nézet ▸ Megjelenítési mód** beállításai — köztük a **Projektor mód**
  — végre a vetített képen is hatnak. Eddig csak a nagy nézőben és az
  indexképeken látszottak, pedig a Projektor mód épp a kivetítéshez való.

**Eszköztár**

- A két nézetváltó gomb mellé visszakerült a **▾** gomb, ami a mappanézet
  beállításait nyitja le. Ugyanazt a menüt adja, mint a **Nézet ▸
  Mappanézet**, tehát a két hely nem tud szétcsúszni.

**Kollázs**

- A jobbgombos menü **Forgatás igazítása** almenüje mostantól szürke
  azoknál a típusoknál, amelyek nem forgatnak (Mozaik, Képkockamozaik,
  Rács, Indexkép, Többszörös exponálás). Eddig a menü felkínálta a négy
  szöget, a kattintásra viszont **némán nem történt semmi**. A program
  viselkedése nem változott, csak látszik.
- A **Képkupacban** a fehér szegélyes képek már nem nőnek túl a nekik járó
  helyen: a szegély eddig kifelé nőtt, ezért ezek a képek 5–10%-kal
  nagyobbak voltak a kelleténél. A polaroid keret és a keret nélküli eset
  változatlan.
- A régi Picasával **közben** készített kollázs és film néhány másodperc
  múlva magától megjelenik. Eddig hálózati meghajtón akár percekbe telt,
  mert a program nem kap értesítést a másik gép írásáról.

**Apróságok**

- Ha képeket húzol az albumok listájára, a célsor mostantól kék hátteret
  kap fehér felirattal, mint az eredetiben — eddig csak a szöveg váltott
  zöldre.
- Kicsit gyorsabb az indulás: hét megerősítő kérdés-ablak csak akkor épül
  fel, amikor tényleg kell. A felület viselkedése nem változott.

## 2026-09-09

**Arcok: nincs többé fölösleges újraszkennelés**

- Az arckeresés **megjegyzi, melyik képet nézte már át**, és a következő
  keresés átugorja. Eddig az arc nélküli képeket minden keresés újra
  végigvette, mert nem maradt utánuk nyom. Ha egy kép megváltozik, a
  keresés természetesen újra megnézi.
- Ha a **Mappakezelőben kikapcsolod egy mappára az arcfelismerést**, a
  program az **OK** megnyomásakor rákérdez, és utána törli a mappában és
  az alfáiban **általa talált** arcokat. A **Picasában felvett nevek és
  arckeretek megmaradnak** — azok a te adataid.
- A kikapcsolt mappa képei jelölést kapnak, hogy a keresés ne induljon
  rájuk újra. A jelölés a visszakapcsolás után is megmarad; így viselkedik
  az eredeti Picasa is.

**Szerkesztő**

- A **Lineáris homályosítás** (Régi effektek fül) eddig a legtöbb képen
  **semmit nem csinált**: az éles és a homályos rész határa mindig a kép
  közepére esett, ahol az eredeti Picasa sem nyúl a képhez. Mostantól
  látszik a hatása.
- Az elmosásra épülő effektek — **Ragyogás**, **Lágy fókusz**,
  **Lineáris homályosítás** — számítása az eredeti Picasa saját képletére
  cserélődött. A rajzuk közelebb került az eredetihez; a különbség szabad
  szemmel alig látható.

**Kollázs**

- Az **Indexkép** elrendezése az eredeti Picasa mért képletét követi: a
  cellák mérete és a képek függőleges igazítása igazodott hozzá.

**Mentés**

- A mentés **nem ír többé `originhash` sort** a kép melletti
  `.picasa.ini` fájlba. Az eddig kiírt érték olyan alakú volt, amilyet az
  eredeti Picasa soha nem használ. A már meglévő sorokhoz a program
  változatlanul nem nyúl.

**Apróságok**

- A csúszkák fogantyúja átlós árnyalást kapott, mint az eredetiben, és
  sötét témában is a hozzá illő színt.
- A **Visszavonás** és az **Újra** gomb magassága nem függ többé a
  rendszer betűtípusától. Ha a felirat nem fér ki, a betű kicsinyít és
  legfeljebb két sorba tördel.
- A Mappakezelő arctörlési kérdésében a „kizárt mappák" helyett
  „kihagyott mappák" áll.

## 2026-09-08

**Vágás, vörösszem, arc felvétele: arány a billentyűvel**

- Miközben új keretet húzol, a lenyomott **Shift** a fénykép saját
  arányára köti a keretet, a **Ctrl** egy ennél egyharmaddal, az **Alt**
  egy ennél felével szélesebb arányra. Az Alt üt mindent, a Ctrl a
  Shiftet, és a billentyű felengedése azonnal felszabadítja az arányt.
- A Shift **nem négyzetet ad**, hanem a kép saját arányát — ezt az
  eredeti Picasa is így csinálta.
- Ugyanez a három billentyű működik a vörösszem-keretnél és az arcok
  kézi felvételénél is.

**Néző: a kék információs sáv**

- Ha a szöveg nem fér ki, mostantól **rövidül**, nem vágódik el a sáv
  szélén: előbb elmarad a fájlnév elől a mappanév, utána a fájlnév
  közepébe kerül három pont. A név vége — és vele a kiterjesztés —
  megmarad.

**Effektek és képminőség**

- A **Színátmenet** effekt rajza az eredeti Picasáéhoz igazodott. Eddig
  erősebb beállításokon látványosan mást adott.
- Az **indexképek** a Picasa saját kicsinyítő eljárásával készülnek: a
  nagy kicsinyítések kevésbé recések, a részletek tisztábbak. A már
  elkészült indexképek viszont a régiek maradnak: az új eljárás azokon
  csak akkor látszik, ha maga a fénykép megváltozik.
- A **Képregény** effekt számottevően gyorsabb lett; a rajza
  gyakorlatilag változatlan.
- Windowson néha nem azzal a simítással jelentek meg a bélyegképek az
  importálás, a duplikátum-kereső és a névtelen arcok ablakában, mint a
  rácsban. Ez megszűnt.

**Kollázs és film**

- A kollázs vagy film mentése **nem írja át többé a mappa
  Picasa-adatait**. Eddig egy mentés a mappa `.picasa.ini` fájljának
  minden sorát átírhatta: a régebbi, nem Unicode fájlokban az ékezetes
  feliratok kérdőjelekre romlottak, és a Picasa-adatok fejléce
  megkettőződhetett a fájlban. A meglévő sorok mostantól változatlanul
  maradnak.

## 2026-09-07

**Néző: nagyítás**

- A nagyítás három vezérlője (**illesztés**, **tényleges méret**,
  **csúszka**) az **alsó eszközsávba** került, a panelkapcsolók elé.
- A **tényleges méret** mostantól a kép **valódi képpontjait** használja.
  Eddig egy belső korlát miatt három-négyszeresére is nagyíthatott.
- A csúszka **közepe pontosan a 100 %**, és meg is akad ott, hogy el
  lehessen találni; a jobb széle a négyszeres nagyítás.

**Néző: feliratsáv és információs csík**

- A **feliratsáv** a kép alján végigfut, a felirat középen, a törlő gomb
  a jobb szélén.
- A **be-kikapcsoló** a kép bal alsó sarkában akkor is látszik, ha a sáv
  ki van kapcsolva — eddig gyakorlatilag nem lehetett visszahozni.
- A kék információs csíkban megjelent a **dátum** és a **Címkék**
  felsorolás, és visszakerült a **hányadik kép** számláló.

**Szerkesztés közben is elérhető a jobb oldali fiók**

- A **Címkék**, **Emberek** és **Helyek** panel a szerkesztőben is
  megnyílik. Eddig a gombjuk benyomódott, de nem történt semmi.

**Szerkesztő**

- Kilenc effekt-csempe **másik effektet ad, ha a Shiftet lenyomva tartod
  a fülre váltáskor** — a felirat is átvált, tehát látod, mit kapsz.
  Ilyen pár például az Élesítés → Élesítés (régi) és a Vignetta → Matt.
  A teljes lista: [Effektek](features/effektek.md).
- A vágás **képarány-listája** az eredeti Picasáéhoz igazodott: a
  papírképek méretei centiméterben (5×8, 9×13, 10×15, 13×18, 20×25),
  **A4**, és a képernyő-arányok **4:3**, **16:10**, **16:9**, **5:3**.
- A **Képregény** effekt rajza közelebb került az eredeti Picasáéhoz.

**Könyvtár**

- A rács **nagyítója** mostantól a teljes felbontású képből mutat egy
  darabot 1:1-ben — eddig a kicsinyített indexképet nagyította vissza.
- A program felismeri a `.jpe` fényképeket és az `.mpeg` videókat is.
- A **fájl idejét** a program az első beolvasáskor jegyzi fel, és utána
  nem frissíti. Így a felvételi idő nélküli képek nem ugrálnak a rácsban
  minden mentés vagy másolás után.

**Fájlok és mentés**

- A mentéskor készült **biztonsági másolat együtt mozog a képpel**:
  átnevezés, áthelyezés és másolás után is működik a
  **Visszaállítás**.
- A másolat többé **nem ül rá** egy másik kép ottfelejtett biztonsági
  másolatára — eddig előfordulhatott, hogy egy frissen másolt képhez egy
  idegen kép régi változata tartozott „eredetiként".
- Az egymás utáni mentések pillanatképei külön helyre kerülnek, így egy
  önálló, `…2.jpg`-féle nevű képet nem lehet többé véletlenül egy másik
  kép régi változatával felülírni.

**Hibák, amik eddig némán elvesztek**

- Ha a mappa írásvédett vagy tele a lemez, a program **kiírja a hibát**,
  ahelyett hogy a képernyőn már a mentett állapotot mutatná. Ez a mappa
  leírásánál, a mappa dátumánál, a kulcsszavaknál és a **Minden effekt
  beillesztése** parancsnál egyaránt így van.
- A régi Picasa-adatfájlok beolvasásakor a sérült vagy összekevert
  oszlopokat a program felismeri, és megnevezi a hibát, ahelyett hogy
  rossz értéket hozna be.

**Tesztüzem**

- A **Súgó ▸ Napló elküldése…** mostantól **mindig megkérdezi, hova
  mentse** a naplót, megjegyzi a választott mappát, és a fájl útvonalát
  a vágólapra másolja. Eddig egy beégetett hálózati mappába került, amit
  a legtöbb gépről nem is lehetett elérni.

**Apróságok**

- A jelölőnégyzetes menüpontok felirata nem lóg rá a négyzetre.
- A képtálca **További lehetőségek…** gombja megkapta a hiányzó ikonját.
- Az ablak visszaállított mérete betartja az ablak legkisebb méretét,
  így Windowson nem jön elő minden induláskor egy figyelmeztetés.
- A **Beállítások ▸ E-mail** fülön a felirat az eredeti Picasa szava
  lett: **Levelezőprogram**.

## 2026-09-05

**Nyomtatás**

- Új **Nyomtató telepítése** gomb: a kiválasztott nyomtató saját
  lapbeállító ablakát nyitja meg (papírméret, tájolás, margók), és amit
  ott elfogadsz, azt a következő nyomtatás használja. PDF-be
  nyomtatásnál a gomb szürke.
- A nyomtató neve alatt egy sor kiírja, **milyen lapra** fogsz
  nyomtatni: a papír neve, mérete milliméterben és a tájolása.

**Szöveg a képen**

- A **betűméret** mostantól az eredeti Picasa tizenhat méretéből
  választható (8-tól 96-ig), a korábbi százalékos beállítás helyett. A
  méret a kép magasságához igazodik.
- **Két hiba javult a mentésnél:** eddig a program minden feliratot
  félkövérként mentett, a körvonal vastagsága pedig mindig elveszett.
  Mostantól mindkettő úgy kerül a fájl mellé, ahogy beállítottad. A
  **Körvonal vastagsága** csúszka folyamatosan állítható.

**Szerkesztő**

- Az effekt-csempék előnézete a kép **mostani állapotára** épül: ha már
  fekete-fehérré tetted a képet, a csempék alapja is az. Eddig minden
  csempe a nyers fotót mutatta.
- Hét effekt-csúszka tartománya és alapértéke az eredeti Picasáéhoz
  igazodott. Néhányuk mostantól **negatív irányba is húzható** — az
  ellenkező hatásig —, ami eddig a felületről elérhetetlen volt.

**Billentyűk**

- **Ctrl+0** a jobb oldali panelt kapcsolja be és ki, és megjegyzi,
  melyik lap volt nyitva. **Ctrl+F** a keresőmezőre ugrik, **Ctrl+K** a
  Címkék panelt nyitja.
- A lapok között **Ctrl+Tab**, **Ctrl+Shift+Tab**, **Ctrl+←** és
  **Ctrl+→** léptet (körbe), a **Ctrl+W** bezárja az aktuális
  projektlapot.
- Csúszkán a **+** / **=** növel, a **−** / **_** csökkent.
- A menütételek nagy részén megjelent az **aláhúzott betű**, az eredeti
  magyar Picasa szerint: **Alt**-tal együtt nyitja a menüt.

**Menük**

- A duplikátum-kereső az **Eszközök ▸ Kísérleti** almenübe került, az
  eredeti nevén: **Fájlok másodpéldányainak megjelenítése**. Az
  adatbázis-áthelyezés felirata **Adatbázis helyének kiválasztása…**
  lett.
- A jelölőnégyzetes menütételek pipája nem hazudik többé: eddig
  előfordult, hogy a pipa lekapcsolt, miközben a panel nyitva maradt.

**Könyvtár**

- A **WebP**-képeket a program mostantól észreveszi és indexeli.
- A mappasorra rámutatva buborékban megjelenik a mappa **teljes
  útvonala** — így megkülönböztethető két azonos nevű mappa.
- A felvételi idő nélküli képeket tartalmazó mappák is **kapnak
  dátumot** (a fájl idejéből), így nem maradnak dátum nélkül a rácsban.
- A bal hasáb nem húzható az eredeti Picasáéhoz igazított alsó
  határnál keskenyebbre.
- Ha a kimeneti gombsor nem fér ki, a végén **További lehetőségek…**
  gomb jelenik meg, alatta a kimaradt gombokkal.

## 2026-09-04

**A súgó megnyílik a programból**

- **F1**-et nyomva vagy a **Súgó ▸ Súgó - tartalom és tárgymutató**
  menüponttal ez a súgó nyílik meg, internet nélkül is.
- A súgóban **Vissza** és **Tartalom** gomb segít a mozgásban, a
  szövegben lévő **kék hivatkozások** pedig megnyitják a hivatkozott
  fejezetet.
- A kereső mostantól **fejezetenként egy sort** ad, a fejezet címével és
  egy rövid részlettel; ha a szó többször is előfordul, kiírja a
  darabszámot. Korábban ugyanaz a cím ismétlődött a listában.

**Bal hasáb**

- A három nézet-kapcsoló — a **mappanézet módja**, az **Egyszerűsített
  fanézet** és az **Indexképek megjelenítése a könyvtárban** — mostantól
  **megmarad a következő indításig**. Eddig minden indításnál
  alapállapotba esett.
- Bekapcsolt indexképeknél a mappasorokon a sárga mappaikon helyett a
  mappa fotóiból álló kis **kupac** látszik.
- Az **Egyszerűsített fanézet** a **Nézet ▸ Mappanézet** almenü aljára
  került, ahogy az eredeti Picasában is.
- Bekapcsolt indexképeknél a hasáb sorai nem maradnak üresen.
- A **Projektek** mappái nem szerepelnek kétszer a hasábban.

**Mozgófilm**

- A **Célfájl** megadása már **nem kötelező**: ha üresen hagyod, a
  program a Képek mappád `Picasa` almappáján belüli filmek-mappába ment,
  a forrásmappa nevével, ütközésnél sorszámozva.

**Képtálca**

- A tálcának **saját kijelölése** van: a tálcán egy képre kattintva
  kijelölöd (Ctrl és Shift is működik), és a **Kijelölés eltávolítása**
  ezekre hat, nem a rács kijelölésére.

**Helyek**

- A program megerősítést kér, ha **húsznál több** kép helyét
  változtatnád meg, illetve ha **ötnél több** képről törölnéd a
  geocímkét.
- A helyadatok pontosabban kerülnek a `.picasa.ini`-be, így a windowsos
  Picasa ugyanoda teszi a képet a térképen.

**Szerkesztő**

- A **Régi effektek** fül bevezetője már nem állítja, hogy egyik örökölt
  szűrő sem használható: a huszonegyből tizenhat ma is alkalmazható.
- A **Filmszemcse** és az **Árnyalás** csempe az eredeti Picasa
  elsődleges szűrőjét hívja; a Filmszemcse ezért csúszkás panelt nyit, és
  lekerült róla a kék jelvény.
- A szövegeszközben a választott **betűtípus** és a **félkövér** állás is
  bekerül a `.picasa.ini`-be — eddig minden felirat félkövérként és
  Ariallal íródott ki.

**E-mail**

- Friss telepítésen az **első küldéskor** megjelenik a **Képek küldése
  e-mailben** kérdés a „ne kérdezze meg újra" pipával. Eddig ez a
  párbeszéd csak annak jött elő, aki előtte megnyitotta a Beállításokat.

## 2026-09-03

**Kollázs**

- A **Képfeliratok megjelenítése** kapcsoló mostantól tényleg hat a kész
  kollázsra. Eddig kikapcsolva is a képen maradt a Polaroid-szegélyre
  írt felirat.
- A feliratok ékezetes betűi helyesen jelennek meg. Korábban az „Ő”, „Ű”
  és társaik kérdőjelre cserélődtek.
- A felirat színe a háttérhez igazodik: világos alapon sötét szürke,
  sötét alapon fehér — így sötét hátterű kollázson is olvasható marad.
  A felirat mérete és helye is az eredeti Picasáéhoz igazodik.
- A **Rács vastagsága** csúszka húzása már nem akasztja meg a felületet
  mozaiknál és képkockamozaiknál: az átrendezés akkor fut le, amikor
  megállsz a csúszkával.

## 2026-09-02 — a súgó első kiadása

Ez a súgó első teljes változata. Nem egy adott frissítéshez tartozik,
hanem a program mai állapotát írja le (0.8-as sorozat).

Amit a PicasaPy ma tud:

- **Könyvtár** — figyelt mappák, három mappanézet, albumok,
  gyűjtemények, projektek, rejtett képek, elérhetetlen mappák kezelése.
- **Nézegetés** — egyképes néző összehasonlító móddal, diavetítés,
  videólejátszás.
- **Keresés** — fájlnév, felirat, címke és mappanév szerint, szín
  szerinti keresés (`szín:kék`), négy szűrő az eszköztáron, hasonló
  képek keresése.
- **Rendszerezés** — csillagok, képfeliratok, címkék és gyorscímkék.
- **Emberek** — arckeresés, arccsoportosítás, névadás, mellőzött arcok,
  Emberek panel.
- **Helyek** — térképes geocímkézés, Google Earth-export.
- **Szerkesztő** — hét fül: gyakori javítások, finomhangolás és négy
  effektfül, plusz a régi effektek olvasása. Vágás, kiegyenesítés,
  vörösszem, retusálás, szövegeszköz, hisztogram.
- **Csoportos munka** — csoportos szerkesztés, effektus-vágólap,
  nem-destruktív forgatás.
- **Mentés** — mentés biztonsági másolattal, mentés másként, másolat
  mentése, visszaállítás, utolsó mentés visszavonása.
- **Ki- és bevitel** — importálás forrásból, exportálás mappába,
  HTML-oldal készítése, nyomtatás (papírra és PDF-be), indexkép-nyomtatás,
  küldés e-mailben.
- **Létrehozás** — kollázs hat elrendezéssel, mozgófilm.
- **Karbantartás** — duplikátum-kereső, mappakezelő, adatbázis
  áthelyezése és tömörítése.
- **Megjelenés** — sötét téma, megjelenítési módok, magyar és angol
  nyelv.

Amit még nem tud, azt a
[Ami még nem érhető el](features/meg-nem-erheto-el.md) lap sorolja fel.

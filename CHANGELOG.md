# Változásnapló

A projekt a [Semantic Versioning](https://semver.org/) elvét követi; a `0.x`
sorozat instabil. A teljes, gépi generálású kiadási jegyzék a
[Releases](https://github.com/sanchomuzax/PicasaPy/releases) oldalon él — ez a
fájl a lényegi, ember által írt kiemeléseket rögzíti.

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

# Beállítások, nyelv, megjelenés

## A Beállítások párbeszéd

**Eszközök ▸ Beállítások…** nyitja meg. Kilenc füle van: **Általános**,
**E-mail**, **Fájltípusok**, **Diavetítés**, **Nyomtatás**, **Hálózat**,
**Webalbumok**, **Névcímkék**, **Google Fotók**. Az első nyolc az eredeti
Picasáé, a **Google Fotók** fül a PicasaPy saját kiegészítése.

> **Fontos:** hét fül működik: az **Általános**, az **E-mail**, a
> **Fájltípusok**, a **Diavetítés**, a **Nyomtatás**, a **Névcímkék** és
> a **Google Fotók**.
> A **Hálózat** fülön csak a naplózás működik, a proxy-beállítások
> szürkék. A **Webalbumok** fül **nem működik**: a Picasa Webalbumok
> megszűnt szolgáltatás, a fül csak az eredeti Picasa elrendezését követi.
> Az Általános fülön szürke a **Névtelen használati statisztikák
> küldése a Google részére** és az **Automatikus frissítések** is.

Az ablak alján két gomb áll, ahogy az eredeti Picasában:

- **OK** (vagy az **Enter**) elmenti a füleken végzett változtatásokat,
  és bezárja az ablakot;
- **Mégse** (vagy az **Esc**, illetve az ablak bezárása) elveti őket:
  minden úgy marad, ahogy az ablak megnyitásakor volt.

A beállítások tehát csak az **OK** után lépnek életbe; a **Mégse** az
**Általános** fül **Gyorsítótárban lévő fájlok törlése** jelölőjének
módosítását is elveti. A nyelv az **OK** után sem vált át azonnal, lásd
alább.

Ha az ablakot **keskenyre** húzod, a fülek nem szorulnak össze
olvashatatlanra: a fülsor vízszintesen **görgethetővé** válik, a két
szélén egy-egy **‹** és **›** nyíllal. A kiválasztott fül mindig
láthatóra görög. A **Google Fotók** fül alapméretben sem fér ki mindig:
ilyenkor a **›** nyíllal érheted el.

Az ablak feliratai — a szürke vezérlők feliratai is — az **eredeti Picasa
saját szövegei**, ezért néhol másképp fogalmaznak, mint amit a funkció
alapján várnál.

### Általános fül

**Kezelőfelület:**

- **Speciális effektusok használata** — a felület animációit (például a
  szerkesztő bal fiókjának becsúszását és a pulzáló gombokat) kapcsolja.
  Kikapcsolva a változások egyből, mozgás nélkül történnek. Alapból be
  van kapcsolva.
- **Segédjelölések megjelenítése** — a gombok és vezérlők fölé vitt
  egérnél felbukkanó kis súgócímkék. Kikapcsolva nem jelennek meg.
  Alapból be van kapcsolva.
- **Szerkesztési nézetből való kilépés egy kattintással** — bekapcsolva
  a nagy nézetből egyetlen kattintással visszaléphetsz a
  könyvtárba (képen és videón egyaránt); alapból ehhez dupla
  kattintás kell. Alapból ki van kapcsolva. A kép nagyított
  állapotában a húzás ettől függetlenül a képet mozgatja.

**Fájlok:** a **Másodpéldányok észlelése az importálás során** kapcsoló, a
**Törlés a lemezről megerősítés nélkül**, az **Eltávolítás az albumból
megerősítés nélkül** és a **Gyorsítótárban lévő fájlok törlése** jelölő,
lásd lentebb.

**Nyelv:** lásd a következő szakaszt.

**Importált képek mentési helye:** az importálás alapértelmezett
célmappája. Alapból a **Képek** mappád. A **Tallózás…** gombbal másik
mappát választasz; ezzel nyílik meg ezután az **Importálás** ablak
([Importálás](importalas.md)).

Az **Adatvédelem…** hivatkozás a Google adatvédelmi oldalát nyitja meg a
böngészőben.

### Nyelv

Az **Általános** fülön a **Nyelv:** választóval döntöd el, milyen nyelvű
legyen a felület. Ugyanez elérhető az **Eszközök ▸ Nyelv** menüből is.

A lista **első tétele** az **Alapértelmezett rendszerbeállítás** — utána
zárójelben a gépeden beállított nyelv. Ezt választva a program minden
indításnál a rendszer nyelvéből dönt. Alatta a **41 választható nyelv**
áll, mindegyik **a saját nyelvén** írva (például **English (US)**,
**Magyar**, **Deutsch**). Mind a 41 nyelven **teljes** a felület: az
eredeti Picasa fordításai mellett a PicasaPy saját feliratai is le vannak
fordítva. A párbeszédablakok szabványos gombjai (például **OK**,
**Mégse**) is a választott nyelven jelennek meg, nem a gép
rendszernyelvén.

**Első induláskor** a program felajánlja a rendszered nyelvét: ha a
gép nyelve nem angol, és a PicasaPy tud ilyen nyelvet, egy kérdés
jelenik meg a program ikonjával. A kérdés angolul szól, ahogy az eredeti
Picasában is: azt kérdezi, hogy a program a rendszered nyelvén is
elérhető, és szeretnél-e angolról erre a nyelvre váltani. **Igen** esetén a felület a rendszer nyelvén indul, és
a beállítás az **Alapértelmezett rendszerbeállítás** lesz: ha később a
gép nyelvét átállítod, a program is követi. **Nem** esetén angol marad.
A kérdés csak egyszer jön; a nyelvet később bármikor átállíthatod.

**Később a nyelv nem vált át azonnal.** Amikor a Beállításokban vagy az
Eszközök menüben rákattintasz egy tételre, a
program megkérdezi: „Módosítja a PicasaPy kezelőfelületének nyelvét? A
változás a program következő megnyitásakor lép érvénybe." **Igen** esetén
a választás elmentődik (a Beállítások ablakban csak az **OK** után), és
**a következő indításnál** lép életbe; **Nem** vagy **Mégse** esetén
semmi nem változik. Az eredeti Picasa is így viselkedik.

A választó és a menü **pipája a kért nyelvet mutatja**, tehát a válasz
után a még nem érvényes nyelven áll — így látszik, mi fog betöltődni
legközelebb.

### Törlés megerősítése

Ha bekapcsolod a **Törlés a lemezről megerősítés nélkül** pipát, a
program a törlésnél nem kérdez rá többé. Ugyanezt beállíthatod magában a
törlés-megerősítő ablakban is, a **Ne kérdezzen újból, mindig
távolítsa el** pipával.

### Másodpéldányok észlelése az importálás során

Ha be van kapcsolva, az importálás kihagyja azokat a képeket, amik már
benne vannak a könyvtáradban. Alapból be van kapcsolva, ahogy az eredeti
Picasában; ha egyszer kikapcsolod, a program megjegyzi. Ugyanez a kapcsoló az importáló ablakban
**Duplikátumok kizárása** néven látszik — a két hely **ugyanazt az egy
beállítást** mutatja, tehát amit az egyiken átállítasz, a másikon is
látszik.

### Gyorsítótárban lévő fájlok törlése

Az **Általános** fülön a **Gyorsítótárban lévő fájlok törlése** jelölő
azt dönti el, hogy a program **kilépéskor** kitakarítsa-e a lemezen
tartott bélyegképeket. Alapból ki van kapcsolva. A módosítás az Opciók
ablakban piszkozat marad: az **OK** menti, a **Mégse** elveti. Azonnali
ürítés nincs: a takarítás mindig a program bezárásakor történik.

Egyetlen kép sem vész el: a bélyegképek szükség szerint újra elkészülnek.
A következő indítás után viszont a mappák lassabban nyílnak meg, amíg a
bélyegképek újra fel nem épülnek.

### Fájltípusok fül

A **Megjelenítés: JPEG-fájlok és** sor alatt jelölőnégyzetekkel
választod ki, mely formátumokat vegye fel a könyvtár a JPEG mellé:
**.BMP**, **.GIF**, **.PNG**, **.TGA**, **.TIF, .TIFF**, **.WEBP**,
**.PSD (Photoshop)**, **RAW formátumok**, **Mozgófilmek (.AVI, .MPG,
.ASF, .WMV)** és **Quicktime-filmek (.MOV)**. A **Mozgófilmek** sor
felirata az eredeti Picasa négy formátumát sorolja, de a program a többi
ismert videóformátumot (például .MP4, .M4V, .3GP, .MKV) is ehhez a sorhoz
számítja; csak a .MOV tartozik a külön Quicktime-sorhoz. A
**RAW formátumok** mellett a **Támogatott formátumok** hivatkozás
felsorolja, milyen RAW-kiterjesztéseket ismer a program. A JPEG mindig
része a könyvtárnak.

Alapból **minden formátum be van jelölve**, a **.GIF**, a **.PNG** és a
**.TGA** is. (Az eredeti Picasában ez a három alapból ki volt kapcsolva;
a PicasaPy szándékosan nem követi, hogy egy frissítés után ne tűnjenek el
a meglévő képeid.) Ha korábban már átállítottál egy jelölőt, a program a
te választásodat tartja meg. Amit kikapcsolsz, azt a program a mappák
**következő beolvasásától** nem veszi fel; a fájlok a lemezen maradnak.

### Diavetítés fül

- **Diavetítés ismétlése** — a vetítés a végén elölről kezdi.
  Alapból ki van kapcsolva.
- **Zenelejátszás a diavetítés alatt** — alapból be van kapcsolva.
  Alatta a **Zeneszámok mappájának kiválasztása:** sorban a
  **Tallózás…** gombbal adod meg a zenemappát (a mező csak akkor aktív,
  ha a zenelejátszás be van kapcsolva). Ha a megnyitott mappához a
  mappa leírásában saját zenét adtál meg (lásd
  [Mappakezelő](mappakezelo.md)), a vetítés azt játssza.

### Nyomtatás fül

- **Rendelkezésre álló nyomtatási méretek** — öt választólista. Ezek
  adják a **Nyomtatás** ablakban a méretlista alatti öt gyorsgombot (a
  hatodik, **FullPage** gomb állandó, ezért a listákban nem is
  szerepel). Az alapértékük a számítógéped **területi beállításától**
  függ: metrikus mértékegységnél 10 × 15, 13 × 18, 15 × 20 és
  20 × 25 cm, ötödiknek pedig az **Indexképek**; hüvelykesnél
  Tárcaméret, 3,5 × 5, 4 × 6, 5 × 7 és 8 × 10. A választásod megmarad.
- **Előnézetek:** **Magas minőségű előnézetek használata (lassabb)** —
  a nyomtatási előnézet pontosabb, de lassabban készül el.
- **Nyomtató minősége:** **Kompatibilis (ötven százalékos felbontás)**
  (alapérték) vagy **Magas minőség (teljes felbontás)**. Ez akkor hat,
  ha a **Nyomtatás** ablakban a **Normál** mód van kiválasztva; az
  **Optimalizált** mód mindig teljes felbontással nyomtat.
- **Nyomtatási mintavételezési minőség:** **Általános (Lanczos-3)**
  (alapérték) vagy **Extra éles (Lanczos-8)** — a képet ezzel az
  átméretező szűrővel kicsinyíti a nyomtatás.

A méretek részletei: [Nyomtatás](nyomtatas.md).

### Hálózat fül

A PicasaPy nem használ proxyt, ezért a fül felső része - a **Felhasználónév
a proxyhoz:**, a **Jelszó a proxyhoz:** és a **Hálózati beállítások
automatikus észlelése** - szürke, és nem is lesz rá szükség.

Ami működik, az a naplózás. A **Hálózati események naplózási szintje:**
listából öt fokozat közül választasz:

- **Naplózás letiltása** - nem készül napló;
- **Csak a hibák naplózása** - csak a sikertelen letöltések;
- **Minimális mennyiségű naplóadat** (alapérték) - minden letöltés egy
  rövid sorral;
- **Részletes naplóadatok** - ezen felül a kapott válasz részletei és az
  esetleges átirányítás is;
- **Az összes hálózati információ naplózása** - ezen felül a letöltött
  adat mérete is.

A választott szint megmarad a következő indításra. A **Napló:** mező
mutatja, hova kerül a napló: egy `network.log` nevű fájlba, a program
adatmappájában. A helye nem változtatható, a mező csak olvasható - a
szövegét viszont kimásolhatod.

A program ma egyetlen dolgot tölt le a hálóról: az arcfelismerő fájlját,
ha az valamiért hiányzik a telepítésből (lásd
[Emberek és arcok](emberek.md)). A napló tehát csak ilyenkor bővül -
akkor érdemes elővenni, ha ez a letöltés nem sikerül.

### Névcímkék fül

- **Arcfelismerés bekapcsolása** — a háttérben automatikusan keresi az
  arcokat az új képeken. Alapból be van kapcsolva. Kikapcsolva a futó
  automatikus keresés megáll. Lásd [Emberek](emberek.md).
- **Javaslatok engedélyezése** — a program névjavaslatot tesz a még
  névtelen arcokra, és az arckeresés után magától csoportosítja az
  arcokat. Alapból be van kapcsolva. Alatta két csúszka áll,
  amelyek csak bekapcsolt javaslatoknál használhatók:
  - **Javaslati küszöb:** — minél nagyobb az érték, annál biztosabbnak
    kell lennie a hasonlóságnak, hogy a program nevet javasoljon;
  - **Csoportküszöb:** — minél nagyobb az érték, annál szigorúbban
    gyűjti egy csoportba az arcokat.
  Mindkettő 50 és 95 között, ötösével állítható, és alapból **85**-ön
  áll, mint az eredeti Picasában. Ha korábban átállítottad a
  csoportküszöböt, a csoportosítás ugyanúgy viselkedik, mint addig, csak a
  csúszka most más számot mutathat.
- **Névcímkék tárolása a fotón** — ha be van kapcsolva (alapból be van),
  egy arc elnevezésekor a program az arc adatait a kép mellé egy XMP
  kísérőfájlba is kiírja.

Az **Emberek album indexképeinek feltöltése a Google Címtárba** jelölő
nem része a felületnek: az a szolgáltatás megszűnt.

### Google Fotók fül

Itt adod meg a saját Google-kliensed adatait, és itt jelentkezel be a
Google Fotókba, hogy a képtálca zöld gombjával feltölthess. A lépéseket
lásd: [Feltöltés a Google Fotókba](google-fotok.md).

## A Fotómegjelenítő beállítása

Az **Eszközök ▸ Fotómegjelenítő beállítása…** egy kis ablakot nyit két
jelölőnégyzettel:

- **Teljes képernyős indítás (a Fotómegjelenítő újraindítása után lép
  érvénybe)** — alapból be van jelölve; a választás megmarad. A felirat
  zárójeles része félrevezető: a program újraindítására nincs szükség, a
  beállítás a **következő képnézőnyitástól** hat. A jelölő csak az
  egyszerűsített nézőre (a Fotómegjelenítőre) vonatkozik, vagyis amikor egy
  képet a programon kívülről, fájlból nyitsz meg: bejelölve ez teljes
  képernyőn nyílik, ha nincs bejelölve, ablakban. A könyvtárból megnyitott
  kép mindig a program ablakában marad, a jelölő állásától függetlenül. Az **F11** a megnyitott nézőben bármikor
  átvált teljes képernyő és ablak közt (lásd [Nézegetés](nezegetes.md));
- **Színkezelés használata** — ugyanaz az egyetlen beállítás, mint a
  **Nézet ▸ Színkezelés használata** (lásd lentebb): ha az egyiken
  átállítod, a másikon is látszik.

## Sötét téma

**Nézet ▸ Sötét téma** ki- és bekapcsolható. A választás megmarad a
következő indításig.

Bekapcsolva a felület egésze sötét színekkel rajzol: a gombok, a
beviteli mezők, az idővonal, a címkepanel és a videolejátszó vezérlői is.

## Megjelenítési mód

A **Nézet ▸ Megjelenítési mód** almenüben a képernyőhöz igazítható a
megjelenítés:

- **Automatikus**, **24 bites** vagy **16 bites (szemcsézett)**
  színmélység — az utóbbi úgy mutatja a képet, ahogy egy 16 bites
  képernyő: a színátmenetek finom szemcsézéssel jelennek meg,
  mindig ugyanúgy (részletek: [Nézegetés](nezegetes.md)),
- **LCD fehérpont**,
- **Projektor mód**,
- **Túlcsordult képpontok megjelenítése** — megmutatja, hol égett ki a
  kép,
- **Mac gamma (1.6)** és **Lineáris gamma (2.2)**,
- **Szépia** és **Fekete-fehér** — az egész felület megjelenítésére.

Ezek csak a képernyőn látszó képet módosítják; a fájljaidat nem érintik.
A választott mód mindenütt hat, ahol képet látsz: az indexképeken, a nagy
nézőben és a **diavetítésben** is.

Mostantól **magát a felületet is** követi: a menük, a sávok és a
hátterek ugyanazt a módot viselik, mint a képek — ahogy az eredeti
Picasában. Fekete-fehér vagy szépia módban tehát nem csak a fotó, hanem
a program kinézete is átvált.

## Színkezelés használata

A **Nézet ▸ Színkezelés használata** kapcsolóval azt döntöd el,
figyelembe vegye-e a program a képbe **beágyazott színprofilt**.

Sok fényképezőgép és képszerkesztő beleírja a fájlba, milyen színteret
használt — például Adobe RGB-t az sRGB helyett. Ha ezt senki nem veszi
figyelembe, az ilyen kép fakónak vagy túl élénknek látszik. Bekapcsolva a
PicasaPy a profil szerint alakítja át a képet a képernyőre.

- Alapból **ki van kapcsolva**, és a választásod megmarad a következő
  indításig.
- A **nagy nézőben és a szerkesztőben** látszik a hatása; a képfájlodhoz
  nem nyúl, és a kimentett képet sem változtatja meg.
- Ha a képben nincs profil, vagy már eleve sRGB, semmi nem történik — a
  legtöbb fényképezőgépes JPEG ilyen.
- Átkapcsolás után a kép azonnal újraépül.

## Ami az ablakról megmarad

A PicasaPy megjegyzi és a következő indításnál visszaállítja:

- az ablak méretét és helyét (maximalizált állapotban is),
- a bal hasáb szélességét,
- a sötét témát és a **Színkezelés használata** kapcsolót,
- a kért nyelvet (ez a következő indításnál lép életbe),
- a mappák és a bal hasáb rendezését,
- az indexképek felirat-módját és a feliratsáv állapotát,
- a bal hasáb három nézet-kapcsolóját: a **mappanézet módját**, az
  **Egyszerűsített fanézetet** és az **Indexképek megjelenítése a
  könyvtárban** kapcsolót,
- a rejtett képek megjelenítését,
- a legutóbb megnyitott mappát,
- a gyorscímkéket és a saját képarányokat.

Az indexképek **mérete** viszont **nem marad meg** — ezt minden
indításnál újra be kell állítani.

## A PicasaPy névjegye

A **Súgó ▸ A PicasaPy névjegye** megmutatja a program pontos verzióját.
Ezt érdemes megadni, ha hibát jelentesz.

## Teljesítmény-monitor

**Súgó ▸ Teljesítmény-monitor** egy kis panelt nyit, ami mutatja a
processzor- és memóriahasználatot. A **Diagnosztika mentése…** gombbal
fájlba írható, ha hibát jelentesz.

## Tesztüzem

**Súgó ▸ Tesztüzem (a következő indulást naplózza)** bekapcsolásával a
program a következő induláskor részletes naplót ír arról, mi mennyi ideig
tartott. Ez akkor hasznos, ha lassú indulást jelentesz. Amíg fut, a
menüsorban „TESZTÜZEM — az indulás naplózása folyik" felirat
figyelmeztet rá.

A **Súgó ▸ Napló elküldése…** paranccsal adod tovább a naplót — ez a
menüpont csak akkor látszik, amíg a tesztüzem be van kapcsolva. Mindig
megnyit egy mentés-ablakot, ahol **te választod meg, hova kerüljön** a
fájl; a felkínált név időbélyeges. A program megjegyzi a választott
mappát, tehát legközelebb már ott nyílik, és a kész fájl útvonalát a
vágólapra is másolja, hogy be tudd illeszteni egy üzenetbe.

> Korábban a napló egy előre beégetett hálózati mappába került, amit a
> legtöbb gépről nem is lehetett elérni.

A tesztüzem a `--tesztuzem` kapcsolóval is bekapcsolható indításkor, csak
arra az egy futásra:

```bash
./picasapy --tesztuzem ~/Kepek
```

## A fejléc gombsorának testreszabása

Az **Eszközök ▸ Gombok konfigurálása…** azt állítja be, mely gombok
látszanak a képek fölötti fejlécsávon, és milyen sorrendben. Ugyanez az
ablak nyílik meg, ha a képtálca kimeneti gombsorára jobbgombbal kattintasz,
és a **Gombok konfigurálása…** tételt választod.

Az ablakban két lista van: **Rendelkezésre álló gombok** és **Jelenlegi
gombok**. A **Hozzáadás >>** és a **<< Eltávolítás** mozgat közöttük, a
**Feljebb** és a **Lejjebb** a sorrendet állítja.

Négy gomb rendezhető így: **Teljes képernyős diavetítés**,
**Csillagozott fényképek kijelölése**, **Szerkesztett fényképek mentése
lemezre** és **Fotókollázs készítése**.

A **Visszaállítás alapértelmezettre** az eredeti sorrendet hozza vissza,
a **Mégse** elveti a változtatást. A beállítás megmarad a következő
indításig.

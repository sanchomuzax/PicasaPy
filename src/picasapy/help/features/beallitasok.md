# Beállítások, nyelv, megjelenés

## A Beállítások párbeszéd

**Eszközök ▸ Beállítások…** nyitja meg. Nyolc füle van: **Általános**,
**E-mail**, **Fájltípusok**, **Diavetítés**, **Nyomtatás**, **Hálózat**,
**Webalbumok**, **Névcímkék**.

> **Fontos:** ma két fülön van élő vezérlő. Az **Általános** fülön a
> **nyelv**, a **Törlés a lemezről megerősítés nélkül**, az
> **Eltávolítás az albumból megerősítés nélkül** és a **Duplikátumok
> észlelése importáláskor** kapcsoló, valamint a **Gyorsítótár ürítése…**
> gomb; az **E-mail** fülön a levelezőprogram megválasztása és a küldött
> képek mérete (lásd [Küldés e-mailben](email.md)). A többi vezérlő
> szürke — a helye megvan, de a funkció mögötte még nem készült el. A
> **Bezárás** gomb zárja az ablakot; nincs külön OK, mert az élő
> beállítások azonnal hatnak (a nyelv a kivétel, lásd alább).

Ha az ablakot **keskenyre** húzod, a nyolc fül nem szorul össze
olvashatatlanra: a fülsor vízszintesen **görgethetővé** válik, a két
szélén egy-egy **‹** és **›** nyíllal. A kiválasztott fül mindig
láthatóra görög.

Az ablak feliratai — a szürke vezérlők feliratai is — az **eredeti Picasa
saját szövegei**, ezért néhol másképp fogalmaznak, mint amit a funkció
alapján várnál.

### Nyelv

Az **Általános** fülön a **Nyelv:** választóval döntöd el, milyen nyelvű
legyen a felület. Ugyanez elérhető az **Eszközök ▸ Nyelv** menüből is.

A lista **első tétele** az **Alapértelmezett rendszerbeállítás** — utána
zárójelben a gépeden beállított nyelv. Ezt választva a program minden
indításnál a rendszer nyelvéből dönt. Alatta a választható nyelvek
állnak, mindegyik **a saját nyelvén** írva: **English (US)** és
**Magyar**.

**A nyelv nem vált át azonnal.** Amikor rákattintasz egy tételre, a
program megkérdezi: „Módosítja a Picasa kezelőfelületének nyelvét? A
változás a program következő megnyitásakor lép érvénybe." **Igen** esetén
a választás elmentődik, és **a következő indításnál** lép életbe; **Nem**
vagy **Mégse** esetén semmi nem változik. Az eredeti Picasa is így
viselkedik.

A választó és a menü **pipája a kért nyelvet mutatja**, tehát a válasz
után a még nem érvényes nyelven áll — így látszik, mi fog betöltődni
legközelebb.

### Törlés megerősítése

Ha bekapcsolod a **Törlés a lemezről megerősítés nélkül** pipát, a
program a törlésnél nem kérdez rá többé. Ugyanezt beállíthatod magában a
törlés-megerősítő ablakban is, a **Ne kérdezze meg újra** pipával.

### Duplikátumok észlelése importáláskor

Ha be van kapcsolva, az importálás kihagyja azokat a képeket, amik már
benne vannak a könyvtáradban. Ugyanez a kapcsoló az importáló ablakban
**Duplikátumok kizárása** néven látszik — a két hely **ugyanazt az egy
beállítást** mutatja, tehát amit az egyiken átállítasz, a másikon is
látszik.

### Gyorsítótár ürítése

Az **Általános** fülön a **Gyorsítótár ürítése…** gomb kitakarítja a
lemezen tartott bélyegképeket. A program rákérdez, és a kiürítés után
megmondja, mennyi helyet szabadított fel.

Egyetlen kép sem vész el: a bélyegképek szükség szerint újra elkészülnek.
Közvetlenül utána a mappák lassabban nyílnak meg, amíg a bélyegképek
újra fel nem épülnek.

## Sötét téma

**Nézet ▸ Sötét téma** ki- és bekapcsolható. A választás megmarad a
következő indításig.

## Megjelenítési mód

A **Nézet ▸ Megjelenítési mód** almenüben a képernyőhöz igazítható a
megjelenítés:

- **Automatikus** vagy **24 bites** színmélység,
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
látszanak a képek fölötti fejlécsávon, és milyen sorrendben.

Az ablakban két lista van: **Rendelkezésre álló gombok** és **Jelenlegi
gombok**. A **Hozzáadás >>** és a **<< Eltávolítás** mozgat közöttük, a
**Feljebb** és a **Lejjebb** a sorrendet állítja.

Négy gomb rendezhető így: **Teljes képernyős diavetítés**,
**Csillagozott fényképek kijelölése**, **Szerkesztett fényképek mentése
lemezre** és **Fotókollázs készítése**.

A **Visszaállítás alapértelmezettre** az eredeti sorrendet hozza vissza,
a **Mégse** elveti a változtatást. A beállítás megmarad a következő
indításig.

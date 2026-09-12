# Beállítások, nyelv, megjelenés

## A Beállítások párbeszéd

**Eszközök ▸ Beállítások…** nyitja meg. Nyolc füle van: **Általános**,
**E-mail**, **Fájltípusok**, **Diavetítés**, **Nyomtatás**, **Hálózat**,
**Webalbumok**, **Névcímkék**.

> **Fontos:** ma két fülön van élő vezérlő. Az **Általános** fülön a
> **nyelv**, a **Törlés a lemezről megerősítés nélkül** és a
> **Duplikátumok észlelése importáláskor** kapcsoló, valamint a
> **Gyorsítótár ürítése…** gomb; az **E-mail** fülön a levelezőprogram
> megválasztása és a küldött képek mérete (lásd
> [Küldés e-mailben](email.md)). A többi vezérlő szürke — a helye
> megvan, de a funkció mögötte még nem készült el. A **Bezárás** gomb
> zárja az ablakot; nincs külön OK, mert az élő beállítások azonnal
> hatnak.

### Nyelv

Az **Általános** fülön a **Nyelv** választóval **magyar** és **angol**
között válthatsz. A változás azonnal érvényes.

Ugyanez elérhető az **Eszközök ▸ Nyelv** menüből is.

### Törlés megerősítése

Ha bekapcsolod a **Törlés a lemezről megerősítés nélkül** pipát, a
program a törlésnél nem kérdez rá többé. Ugyanezt beállíthatod magában a
törlés-megerősítő ablakban is, a **Ne kérdezze újra** pipával.

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

## Ami az ablakról megmarad

A PicasaPy megjegyzi és a következő indításnál visszaállítja:

- az ablak méretét és helyét (maximalizált állapotban is),
- a bal hasáb szélességét,
- a sötét témát és a nyelvet,
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

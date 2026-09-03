# Beállítások, nyelv, megjelenés

## A Beállítások párbeszéd

**Eszközök ▸ Beállítások…** nyitja meg. Nyolc füle van: **Általános**,
**E-mail**, **Fájltípusok**, **Diavetítés**, **Nyomtatás**, **Hálózat**,
**Webalbumok**, **Névcímkék**.

> **Fontos:** ma **két beállítás működik** a párbeszédben, mindkettő az
> **Általános** fülön: a **nyelv** és a **Törlés a lemezről megerősítés
> nélkül** kapcsoló. A többi vezérlő szürke — a helye megvan, de a
> funkció mögötte még nem készült el. A **Bezárás** gomb zárja az
> ablakot; nincs külön OK, mert az élő beállítások azonnal hatnak.

### Nyelv

Az **Általános** fülön a **Nyelv** választóval **magyar** és **angol**
között válthatsz. A változás azonnal érvényes.

Ugyanez elérhető az **Eszközök ▸ Nyelv** menüből is.

### Törlés megerősítése

Ha bekapcsolod a **Törlés a lemezről megerősítés nélkül** pipát, a
program a törlésnél nem kérdez rá többé. Ugyanezt beállíthatod magában a
törlés-megerősítő ablakban is, a **Ne kérdezze újra** pipával.

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

## Ami az ablakról megmarad

A PicasaPy megjegyzi és a következő indításnál visszaállítja:

- az ablak méretét és helyét (maximalizált állapotban is),
- a bal hasáb szélességét,
- a sötét témát és a nyelvet,
- a mappák és a bal hasáb rendezését,
- az indexképek felirat-módját és a feliratsáv állapotát,
- a rejtett képek megjelenítését,
- a legutóbb megnyitott mappát,
- a gyorscímkéket és a saját képarányokat.

Az indexképek mérete és a mappanézet módja **nem marad meg** — ezeket
minden indításnál újra be kell állítani.

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
figyelmeztet rá. A **Napló elküldése…** paranccsal adhatod tovább a
naplót.

A tesztüzem a `--tesztuzem` kapcsolóval is bekapcsolható indításkor, csak
arra az egy futásra:

```bash
./picasapy --tesztuzem ~/Kepek
```

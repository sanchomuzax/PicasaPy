# Exportálás

Az exportálás **másolatot** készít: az eredeti képeidhez nem nyúl, hanem
a szerkesztésekkel együtt új fájlokat ír egy másik mappába.

## Exportálás mappába

Indítás: **Fájl ▸ Kép exportálása mappába…** (Ctrl+Shift+S), vagy a
képtálca **Exportálás** gombja.

Beállítható:

- **Exportálási hely** — a célmappa (**Tallózás…**).
- **Az exportált mappa neve** — ide kerülnek a képek.
- **Átméretezés**: **Eredeti méret használata**, vagy add meg a hosszabbik
  oldal képpontban mért méretét. A csúszka mellett a program megírja,
  mire számíts (kisebb fájl és némi minőségromlás, vagy nagy fájl és
  minden részlet).
- **Képminőség**: Minimum, Normál, Maximum, vagy az eredeti minőség
  megőrzése.
- **Filmek exportálása**: **Első képkocka** képként, vagy **Teljes film
  (nincs átméretezés)**.
- **Vízjel hozzáadása** — a képekre rábélyegezhető a neved, egy webcím
  vagy egy szerzői jogi közlemény.
- **Számok hozzáadása a fájlnevekhez** — így a sorrend megmarad, ha a
  célmappát máshol névsorban nyitják meg.

Ha a célmappa már létezik, a program megkérdezi, felülírja-e.

A végén kiírja, hány kép ment ki, és ha volt hiba, hány nem sikerült.

Az exportált mappák a bal hasáb **Projektek ▸ Exportált képek**
bejegyzése alatt maradnak elérhetők.

## Exportálás HTML-oldalként

Weboldalt készít a képekből: indexképek, amikre kattintva a nagy kép
nyílik meg. Indítás: **Mappa ▸ Exportálás HTML-oldalként…**, vagy a mappa
helyi menüjéből.

Beállítható:

- **Oldal címe**,
- **Mentés ide** (**Tallózás…**) — előre kitöltve a képmappádon belüli
  **Picasa HTML exportok** mappával. Ez csak javaslat: a mappát a program
  csak a **Létrehozás** gombra kattintva hozza létre, és bármikor
  átírhatod.
- **Sablon** — a kész oldal kinézete, kis előnézeti rajzzal,
- **Bélyegkép mérete** és **Kép mérete** (vagy eredeti méret),
- **Árnyékolt bélyegképek** és **Árnyékolt képek**.

A **Létrehozás** gomb után a program megírja, hány fájlt írt és hova.

### A hét sablon

Hat galéria-sablon van: három háttérszín, mindegyik kétféle csempével.

| sablon | háttér | csempe |
|---|---|---|
| Fehér | fehér | sima |
| Fehér keret | fehér | passzpartus keret |
| Szürke | szürke | sima |
| Szürke keret | szürke | passzpartus keret |
| Fekete | fekete | sima |
| Fekete keret | fekete | passzpartus keret |

A hetedik, az **XML (gépi)**, nem weboldal: egyetlen `album.xml` fájlt ír
az album és a képek adataival. Akkor jó, ha az adatokat egy másik program
dolgozza fel; böngészőben nem lesz belőle galéria.

## Arcinformációk kísérőfájlba

Az **Eszközök ▸ Kísérleti ▸ Arcinformációk írása XMP-adatokba…** a látott
mappa képei mellé kis kísérőfájlokat ír az elnevezett arcok helyével és
nevével, hogy más fényképkezelők is felismerjék őket. A képfájlokhoz nem
nyúl. Részletek: [Emberek és arcok](emberek.md).

## Google Earth

**Eszközök ▸ Geocímke ▸ Exportálás Google Earth-fájlba** a helyhez kötött
képekből olyan fájlt ír, amit a Google Earth megnyit. Részletek:
[Helyek és geocímkék](helyek.md).

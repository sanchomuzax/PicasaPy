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
- **Képminőség**: **Automatikus** (megőrzi az eredeti képminőséget),
  **Normál** (a minőség és a méret megfelelő egyensúlya), **Maximum**
  (nagyon nagy fájl, az apró részleteket is megőrzi), **Minimum**
  (legkisebb fájl, némi minőségvesztéssel), vagy **Egyéni (N)** — ilyenkor
  csúszkával magad állítod be a minőséget. A **Maximum** teljes
  színfelbontású (4:4:4) JPEG-et ír; az **Automatikus** a forrás
  JPEG-jének színfelbontását megtartja.
- **Filmek exportálása**: **Első képkocka** képként, vagy **Teljes film
  (nincs átméretezés)**.
- **Vízjel hozzáadása** — a képekre rábélyegezhető a neved, egy webcím
  vagy egy szerzői jogi közlemény.
- **Számok hozzáadása a fájlnevekhez** — így a sorrend megmarad, ha a
  célmappát máshol névsorban nyitják meg.

Az exportált képbe a program frissíti a metaadatokat: a módosítás
ideje az export ideje lesz, a kép mérete a kimenet tényleges mérete, a
hiányzó szerző- és készítésidő-mezők pótlódnak, a fényképezőgép saját
adatai pedig megmaradnak. A 300 képpontnál nagyobb JPEG-be a program kis
beágyazott előnézetet is tesz, ahogy az eredeti Picasa.

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

### Saját sablonok

A gyári sablonok mellett a saját `.tpl`-sablonjaidat is használhatod. Tedd
őket a saját (felhasználói) mappádon belül a
`.local/share/picasapy/webexport/templates` mappába — Windowson is ezen a
néven, a felhasználói mappád alatt —, sablononként egy külön almappába. Az almappában legyen egy `index.tpl`
fájl; ha mellette van egy `preview.svg`, az lesz a sablon kis
előnézeti rajza.

A következő megnyitáskor a saját sablonok a gyáriak **után**, a sablonlistában
jelennek meg, és ugyanúgy kiválaszthatók. A listában a neve a sablon
fejlécében megadott név; ha nincs ilyen, az almappa neve. Ha egy saját
sablon almappája ugyanazt a nevet viseli, mint egy gyári sablon, a gyári
marad meg, a saját nem jelenik meg.

Az ablak a tartalmához igazodik, ezért a **Létrehozás** gomb alapméretben is
látszik.

## Arcinformációk kísérőfájlba

Az **Eszközök ▸ Kísérleti ▸ Arcinformációk írása XMP-adatokba…** a látott
mappa képei mellé kis kísérőfájlokat ír az elnevezett arcok helyével és
nevével, hogy más fényképkezelők is felismerjék őket. A képfájlokhoz nem
nyúl. Részletek: [Emberek és arcok](emberek.md).

## Google Earth

**Eszközök ▸ Geocímke ▸ Exportálás Google Earth-fájlba** a helyhez kötött
képekből olyan fájlt ír, amit a Google Earth megnyit. Részletek:
[Helyek és geocímkék](helyek.md).

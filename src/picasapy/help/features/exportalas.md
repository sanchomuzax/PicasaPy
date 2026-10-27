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
beágyazott előnézetet is tesz, ahogy az eredeti Picasa. Ha egy kép
metaadatai olyan terjedelmesek, hogy a kis előnézettel együtt sem férnek
el a JPEG-fájlban, az exportált képből a fényképezőgép adatai (EXIF)
kimaradnak; az eredeti Picasa is így tesz.

Ha a célmappa már létezik, a program megkérdezi, felülírja-e.

A végén kiírja, hány kép ment ki, és ha volt hiba, hány nem sikerült.

Az exportált mappák a bal hasáb **Projektek ▸ Exportált képek**
bejegyzése alatt maradnak elérhetők.

## Exportálás HTML-oldalként

Weboldalt készít a képekből: indexképek, amikre kattintva a nagy kép
nyílik meg. Indítás: **Mappa ▸ Exportálás HTML-oldalként…**, vagy a mappa
helyi menüjéből.

Beállítható:

- **Weboldal címe:**,
- **Mappa:** (**Tallózás…**) - első alkalommal előre kitöltve a
  képmappádon belüli **Picasa HTML exportok** mappával (Windowson a
  Dokumentumok mappádon belüli **Picasa HTML Exports** mappával). Ez csak
  javaslat: a mappát a program csak az **Exportálás** gombra kattintva
  hozza létre, és bármikor átírhatod.
- a **sablonlista**: a kész oldal kinézete (lásd lentebb),
- **Képek exportálása innen:** — a nagy képek mérete: **Eredeti méret**,
  **1024 képpont (nagy képernyőkhöz)**, **800 képpont (nagyméretű
  weboldalakhoz)**, **640 képpont (weboldalakhoz)** — ez az alapérték —
  vagy **320 képpont (e-mailhez)**. Az indexképek méretét és az esetleges
  árnyékot a választott sablon adja, ezeket külön nem állítod.
- **Mozgófilmek exportálása:** — **Első képkocka**: a film első kockája
  állóképként kerül az oldalra, mint egy fénykép; **Teljes mozgófilm**: az
  indexkép az első kocka, rákattintva pedig maga a film nyílik meg (a
  program a filmfájlt változatlanul másolja az oldal mellé). Az a film,
  amelyet a program nem tud beolvasni, kimarad az oldalról.

A méretet, a mozgófilm-módot, a **célmappát** és a **sablont** a program
megjegyzi a következő exportálásig.

Az **Exportálás** gomb után a program megírja, hány fájlt írt és hova. A
**Mégse** bezárja az ablakot.

### A hét sablon

Az ablak középső részén, a „Kattintson a sablonok nevére a minta
megjelenítéséhez." kezdetű sor alatt egy lista áll a hét sablonnal, az
eredeti Picasa sorrendjében és nevén. Egy névre kattintva a lista alatt
megjelenik a sablon rövid leírása, jobbra pedig egy kis előnézeti rajz.
A kijelölt sablon szerint készül az oldal.

| a lista sora | háttér | csempe |
|---|---|---|
| 1. sablon, 2 oldalas, szürke háttér | szürke | sima |
| 2. sablon, 2 oldalas, fekete háttér | fekete | sima |
| 3. sablon, 2 oldalas, fehér háttér | fehér | sima |
| 4. sablon, 1 oldalas, szürke háttér | szürke | keretes |
| 5. sablon, 1 oldalas, fekete háttér | fekete | keretes |
| 6. sablon, 1 oldalas, fehér háttér | fehér | keretes |
| XML-kód | - | - |

A leírások az eredeti Picasa szövegei. A kész oldal felépítése a
sablontól függ:

- Az **1-3. sablon** (2 oldalas) indexképes kezdőoldalt készít; egy
  képre kattintva a nagy kép külön oldalon nyílik meg.
- A **4-6. sablon** (1 oldalas) egyetlen ablakban mutat mindent: **bal
  oldalt** egy keskeny, görgethető sávban sorakoznak az indexképek a
  feliratukkal, **jobb oldalt** a nagy kép látszik. Megnyitáskor az első
  kép áll jobbra; egy indexképre kattintva az a kép jelenik meg a helyén,
  a bal sáv pedig marad.

A sablonok ezen felül a háttérszínben és a csempék kinézetében
különböznek.

Az utolsó, az **XML-kód**, nem weboldal: egyetlen `album.xml` fájlt ír
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

Az ablak a tartalmához igazodik, ezért az **Exportálás** gomb alapméretben is
látszik.

## Közzététel FTP-n

Az **Eszközök ▸ Kísérleti ▸ Közzététel FTP-n keresztül...** paranccsal a
weboldalt nem a gépedre mented, hanem egy FTP-kiszolgálóra, például a
tárhelyedre töltöd fel. Ugyanaz az ablak nyílik meg, mint az
**Exportálás HTML-oldalként…** parancsnál, a címe **Közzététel FTP-n
keresztül...**. A **Mappa:** sor helyén az **FTP-fiók:** választó
áll, mellette a **Kezelés…** gombbal. A cím sora itt **Oldal címe:**, a
sablont pedig nem lista, hanem egy **Sablon:** legördülő választja ki
(alatta a kis előnézettel és a leírással). A képméret és a mozgófilm-mód
ugyanaz, mint fent.

### FTP-fiók felvétele

Ha még nincs fiókod, az ablak megnyitásakor rögtön az **FTP-fiókok
kezelése** ablak nyílik meg. Később a **Kezelés…** gombbal éred el. Mezői:

- **Fiók neve:** - ezen a néven látod a fiókot a választóban;
- **FTP-kiszolgáló:** - a kiszolgáló címe;
- **Felhasználónév:** és **Jelszó:**;
- **Távoli mappa:** - a kiszolgálón ebbe a mappába kerül az oldal. Ha
  nincs ilyen mappa, a program létrehozza.

Az **Új** gomb üres űrlapot ad egy újabb fiókhoz, a **Törlés** törli a
kiválasztottat, a **Mentés** elmenti, a **Mégse** bezárja az ablakot.
Meglévő fiók szerkesztésekor a jelszómezőt üresen hagyhatod: ilyenkor a
korábban mentett jelszó marad meg.

A jelszót a program nem a saját beállításai közé írja, hanem a
számítógéped **rendszerszintű jelszótárába** (kulcstartójába). Ha ilyen
nincs a gépen, a program szól, és a fiókot nem tudja menteni.

### A feltöltés

Válaszd ki a fiókot, és kattints a **Közzététel** gombra. A program
előbb elkészíti az oldalt, majd a fájlokat feltölti a fiók távoli
mappájába. A végén kiírja, hány fájlt töltött fel, és melyik fiókba. A
kiszolgálón már ott lévő fájlokat nem törli, az azonos nevűeket
felülírja. Hiba esetén (például rossz jelszónál vagy elérhetetlen
kiszolgálónál) a program megírja, mi volt a gond.

> A feltöltés hagyományos, **titkosítatlan** FTP-vel megy a szokásos
> (21-es) porton. A jelszó és a fájlok így titkosítatlanul utaznak a
> hálózaton. Titkosított (FTPS vagy SFTP) kapcsolatot a program nem
> ismer.

## Arcinformációk kísérőfájlba

Az **Eszközök ▸ Kísérleti ▸ Arcinformációk írása XMP-adatokba…** a látott
mappa képei mellé kis kísérőfájlokat ír az elnevezett arcok helyével és
nevével, hogy más fényképkezelők is felismerjék őket. A képfájlokhoz nem
nyúl. Részletek: [Emberek és arcok](emberek.md).

## Google Earth

**Eszközök ▸ Geocímke ▸ Exportálás Google Earth-fájlba** a helyhez kötött
képekből olyan fájlt ír, amit a Google Earth megnyit. Részletek:
[Helyek és geocímkék](helyek.md).

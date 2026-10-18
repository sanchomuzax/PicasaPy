# Mozgófilm

A mozgófilm a kijelölt képekből készít videót: a képek egymás után,
megadott ideig látszanak.

## Indítás

Jelöld ki a képeket, majd:

- **Létrehozás ▸ Mozgófilm ▸ Új mozgófilm…**, vagy
- a képtálca **Mozgófilm** gombja, vagy
- a képrács mappafejlécében a kollázs-gomb mellett álló filmgomb
  (*Mozgófilmes prezentáció létrehozása*). Ez nem a kijelölt képekkel
  dolgozik, hanem **az adott fejléc mappájának összes képével** nyitja meg
  a Mozgófilm ablakot. A személyalbum fejlécében nincs ilyen gomb, ott a
  saját filmgombok állnak.

A **Létrehozás ▸ Mozgófilm ▸ A kijelölésben lévő arcokból…**, az
**Az Emberek albumból…** (ehhez nem kell kijelölés) és a személyalbum
fejlécének filmgombjai szintén ezt a panelt nyitják — lásd
[Emberek](emberek.md).

A **Mozgófilm** ablak három füllel nyílik: **Mozgófilm**, **Dia** és
**Klipek**; alul az előnézet és a **Bezárás** / **Mozgófilm létrehozása**
gomb áll. Az előnézet és a lejátszósáv a beállítások **alatt**, görgetés
nélkül látszik.

## A Mozgófilm fül

A fül tetején az áll, hány kép van kijelölve („N kép kijelölve."). Alatta:

- **Méretek** — a film felbontása: 320 × 240, 640 × 480, 800 × 600,
  1024 × 768, 1600 × 1200, 1280 × 720 (720p) vagy 1920 × 1080 (1080p).
  Alapból 640 × 480; amit választasz, a következő filmnél is az marad.
  (Az arcokból készülő filmnél az alap 1024 × 768, és ezt a program nem
  jegyzi meg.)
- **Képváltási stílus** — az átmenet két kép között: **Kivágás** (éles
  váltás), **Szétoszlás**, **Szétoszlás feketén át** / **fehéren át**,
  **Törlés** (a kép beúszik: balra, jobbra, felülről, alulról és
  átlósan), **Tolás**, **Kör**, **Pásztázás és nagyítás**, **Pásztázás
  és nagyítás - arc**, **Gyorsítás** és **Négyszög**. Alapból a
  **Szétoszlás** áll.
- **Átfedés** — mennyire csúsznak egymásba az átmenetnél a képek
  (másodpercben); legfeljebb a dia idejének 90%-a.
- **Dia időtartama:** — mennyi ideig látszik egy kép. 1,0 és 10,0
  másodperc között állítható, fél másodperces lépésekben; az
  alapértelmezés 3,0 másodperc.
- **Célfájl:** — **nem kötelező**. Ha üresen hagyod, a program maga
  dönti el, hova és milyen néven mentse (lásd lentebb). A **Tallózás…**
  gombbal viszont te is megadhatod a helyét. A kimenet MP4-videó.
- **Hangsáv:** — a film zenéje. A **Betöltés…** gombbal választasz
  hangfájlt, a **Törlés** leveszi. Ha a képek egy mappából jönnek, és a
  mappához zenét adtál meg (lásd [Mappakezelő](mappakezelo.md)), az lesz
  alapból a hangsáv. Ugyanígy, ha egy albumból készítesz filmet, és az
  albumhoz be van állítva zene (az **Album tulajdonságai** ablak **Zene:** mezőjében), az album
  zenéje lesz az alap, feltéve hogy a fájl megvan. A **Törlés** ezt is
  leveszi. A **Beállítások**
  listából dönthetsz, mi legyen, ha a zene és a képek hossza nem
  egyezik: **Hangfájl csonkolása**, **Fotók hozzáillesztése a hanghoz**
  vagy **Fotók ismétlése a zene végéig**.
- Jelölők: **Képfeliratok megjelenítése** és **Dátumok megjelenítése**
  (a kép alján látszik a felirat, illetve a felvétel dátuma — feliratnak a
  képhez a PicasaPy-ban írt képfelirat kerül, és csak ha az üres, akkor a
  fájlba más program által írt leírás),
  **Teljes képkockás fotó körbevágása** (a kép kitölti a kockát, a széle
  levágódik, ahelyett hogy fekete sáv maradna) és **Kis felbontású arcok
  eltávolítása**. Ez utóbbi jelölő ma még **nem hat** a filmre: csak a
  film projektfájljába kerül.
- **Diák rendezése:** **A legjobb átmenetek** (új filmnél ez az
  alapérték), **Album szerint** vagy **Időrend**. A **legjobb
  átmenetek** sorrendben a program a színükben egymáshoz közeli képeket
  teszi egymás után, a gyors egymásutánban készült képeket (például egy
  sorozatfelvétel kockáit) pedig a készítési idejük szerint egy csoportban
  kezeli. A készítési időt a kép felvételi adataiból veszi, ha ilyen
  nincs, a fájl dátumából.

Az **OK** helyett a **Mozgófilm létrehozása** gomb indítja a munkát;
célfájl nélkül is nyomható.

## A Dia fül: szöveges dia

A filmbe **szöveges dia** is tehető (például cím vagy stáblista). A **Dia**
fülön a **Szöveg** mezőbe írod a szöveget, majd:

- **Betűtípus:**, **Méret:** és **Stílus:** — a stílus lehet
  **Középre igazított**, **Jó napom van**, **Képfelirat**,
  **Képfelirat - Klasszikus**, **Színátmenet - fekete / Fehér**,
  **Átlátszó - fekete / fehér**, **Gördülő stáblista**, **Zenei videoklip
  - bal / jobb** vagy **Képfelirat - Írógép**;
- **Félkövér**, **Dőlt**, **Automatikus körvonal**, valamint a
  **Szöveg színe** és a **Háttér színe** gomb;
- **Új szöveges dia hozzáadása** — megnyitja a címdia-szerkesztőt: ott
  beírod a szöveget, kiválasztod a betűtípust, a méretet és a stílust
  (a betűtípus **Normál**, **Félkövér**, **Dőlt** vagy **Félkövér dőlt**
  lehet), látod az előnézetet, és a **Hozzáadás** gombbal a filmbe
  teszed; a **Mégse** elveti;
- **A kijelölt dia eltávolítása**.

Három stílus a kész filmben **mozog** is:

- **Jó napom van** - a szöveg oldalra csúszva, áttűnve jelenik meg;
- **Gördülő stáblista** - a szöveg a kép aljáról gördül fel a közepéig;
- **Képfelirat - Írógép** - a szöveg betűnként íródik ki, mint egy
  írógépen.

A dia a **Szöveges dia** névvel kerül a filmszalagra. A **Dia** fül
alján a hozzáadott szöveges diák listája áll: duplán kattintva
szerkeszthető a dia, húzással sorrendbe teheted őket, és ha a listán
kívülre húzol egyet, az eltávolítódik.

## A Klipek fül: a filmszalag

A **Klipek** fülön a film képeit és szöveges diáit látod sorban, a
filmszalagon:

- **Összes fénykép** — csúszka: a kijelölt képek hányadrészét használja
  fel a film; mellette az éppen felhasznált képek száma áll;
- **Ne legyen szűrés a készítés ideje alapján** / **Az utolsó időszak
  képeinek eltávolítása: N** — az időszűrő csúszkája. Ma még **nem
  szűri** a filmet: az értéke csak a film projektfájljába kerül;
- **Újraszámolás** — újraépíti a filmszalagot, és a **Mozgófilm** fülre
  lép. Ha már vettél fel **szöveges diát**, a program előbb rákérdez: „Az új
  film létrehozásakor minden hozzáadott szöveges dia törlődik. Biztosan
  folytatja?" — így nem vész el némán a kézzel felvett dia;
- **Kijelölt klipek hozzáadása** — a könyvtárban kijelölt képeket a film
  végére fűzi;
- **Kijelölt klip eltávolítása** — kiveszi a kijelölt képet (vagy diát)
  a filmből;
- **Csak a kijelölt klip lejátszása** — az előnézet és a film is csak a
  kijelölt képet használja.

Az előnézet alatt egy infósor mutatja a kijelölt kép vagy dia nevét,
méretét és helyét a filmben: például „Szöveges dia  1024x768 képpont
(3 / 12)".

## Az előnézet

Az előnézet a beállítások alatt áll. Az **Előnézet** gomb lejátssza a
filmet (közben **Szünet** lesz belőle). Lejátszáskor az előnézet a
filmhez hasonlóan viselkedik:

- a képek a **Dia időtartama** szerint követik egymást, a **szöveges
  diák** pedig a képek után, a saját szövegükkel, betűtípusukkal és
  színükkel jelennek meg;
- két kép között a kiválasztott **átmenet** látszik, a beállított
  **Átfedés** ideje alatt: a mozgásos stílusok (például a tolás, a kör
  vagy a pásztázás és nagyítás) is ugyanúgy mozognak, mint a kész
  filmben. Az előnézet a film méretével, a **Teljes képkockás fotó
  körbevágása**, a
  feliratok és a dátumok beállításával készül, tehát azt látod, amit a
  film is mutatni fog;
- a **szöveges dia** szövegének, betűjének vagy színének változtatása
  gépelés közben is szinte azonnal látszik az előnézetben;
- ha van **hangsáv**, az az előnézettel együtt szól: a **Szünet** megállítja,
  az ablak bezárása leállítja. A lejátszósáv melletti hangerő-csúszkával
  állítod az előnézet hangerejét; a program megjegyzi a beállítást.
 A **Mozgófilm** fül tetején a
**Vissza a kijelölt diához** gomb a kijelölt képhez ugrik. A két kis
gomb a **Mozgófilm tényleges méretének
megjelenítése (nyújtás nélkül)** és a **Lejátszás teljes képernyőn**.

## Hova kerül a film, ha nem adsz meg célfájlt

- A **mappa** a Képek mappád `Picasa` almappáján belüli filmek-mappa
  (`Filmek`, `Mozgófilmek` vagy `Movies` — ha valamelyik már létezik, a
  program abba ír). Ha ez a mappa nem hozható létre, a rendszer Videók
  mappájába ment.
- A **fájlnév** annak a mappának a nevéből lesz, ahonnan a képek jönnek.
  Ha több különböző mappából válogattál, a program saját alapnevet
  használ.
- Ha ilyen nevű fájl már van ott, a program **sorszámot** tesz a név
  végére.
- Az így megnyitott mappa magától megjelenik a bal hasáb **Projektek**
  csoportjában.

## Készítés közben

Haladásjelző mutatja, hányadik képnél tart. Ha kész, a program kiírja,
hova mentette („A mozgófilm elmentve: …"). Ha nem sikerült, azt is
jelzi.

Az elkészült film a bal hasáb **Projektek** csoportjának filmek-mappájába
kerül.

Ha ugyanabban az ablakban már készítettél egy filmet, és újra a
**Mozgófilm létrehozása** gombra kattintasz, a program megkérdezi:
**Lecseréli a meglévőt, vagy újat hoz létre?** A **Meglévő cseréje** az
előző film helyére írja az újat, az **Új létrehozása** külön fájlba menti,
a **Mégse** (vagy az Esc) pedig nem készít semmit.

## A film újranyitása később

A kész videó mellé a program egy **projektfájlt** is ment (`.mxf`) —
ugyanaz a formátum, amit az eredeti Picasa is használt, a kollázs
`.cxf`-jének megfelelője. Ebben van a képek sorrendje, a diaidő és az
átmenet hossza.

Ha egy korábban elkészített filmet megnyitsz a nézőben, megjelenik a
**Mozgófilm szerkesztése** gomb: ezzel visszatérsz a film képeihez és
beállításaihoz, ahogy a kollázsnál is megszokott. A felbontás ilyenkor
az alapértelmezésről indul — ezt a párbeszéd ki is írja.

## Ha egy kép hiányzik

Ha a kijelölésből időközben eltűnt néhány fájl (áthelyezted,
átnevezted vagy törölted őket), a program szól, hány kép marad ki, és a
többiből elkészíti a filmet.

## Képkocka mentése videóból

Ha nem filmet készítenél, hanem egyetlen képet emelnél ki egy videóból,
azt a nézőben teheted meg — lásd
[Nézegetés](nezegetes.md).

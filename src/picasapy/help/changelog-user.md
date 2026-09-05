# Mi változott?

Felhasználói szemszögű változásnapló: csak az, ami a képernyőn is
látszik. A részletes, fejlesztői változásnapló a program `CHANGELOG.md`
fájljában van.

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

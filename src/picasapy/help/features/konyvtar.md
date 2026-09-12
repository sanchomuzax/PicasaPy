# A könyvtár: mappák, albumok, gyűjtemények

A bal hasáb a könyvtárad térképe. Négy fajta bejegyzés lehet benne.

Mindegyiknek **saját ikonja** van, hogy egy pillantásra lásd, mit
nézel: a mappa **kék** mappaikon, a rendes album **narancs könyv**, a
Csillagozott képek **zöld könyv csillaggal**, a program készítette
projekt-mappák (Kollázsok, Mozgófilmek, Exportált képek) **lila könyv
csillaggal**, a címke pedig **szürke címke**.

A **Nézet ▸ Könyvtárnézet** pipa mutatja, hogy a főablak a könyvtárat
mutatja. Ez ma mindig be van kapcsolva; a párja, a **Szerkesztési
nézet**, még nem készült el.

## Mappák

A **Mappák** csoport a lemezen lévő, tényleges mappákat mutatja. Ha
átnevezel vagy áthelyezel itt valamit, az a lemezen is megtörténik.

A hasáb háromféleképpen nézhet ki. A **Nézet ▸ Mappanézet** almenüben
válthatsz köztük:

- **Egyszerű mappanézet** — egyetlen lapos lista, mindegyik mappa egy sor.
- **Fanézet** — a mappák a lemezen elfoglalt helyük szerint, egymásba
  ágyazva.
- **Egyszerűsített fanézet** — fanézet, de a csak-továbbvezető,
  képet nem tartalmazó szintek összevonva. Ez a kapcsoló az almenü
  **legalján** áll, elválasztva a másik kettőtől.

Az első kettő között az eszköztár két kis nézetváltó gombjával is
válthatsz. A két gomb mellett van egy **▾** gomb is: ez **ugyanazt a
menüt** nyitja le, ami a **Nézet ▸ Mappanézet** almenü — a nézet, a
sorrend és az indexképek kapcsolója tehát egy helyről vezérelhető, és a
két belépési pont nem tud szétcsúszni. Keskeny ablakban a ▾ gomb
elrejtőzik; a menüsorból ilyenkor is elérhető minden.

A hasáb üres részére jobbgombbal kattintva az **Egyszerűsített fanézet**
kapcsoló érhető el.

**Mindhárom beállítás megmarad a következő indításig.**

A hasáb szélessége az elválasztó vonal húzásával állítható, de egy alsó
határnál keskenyebbre nem húzható; ez a határ az eredeti Picasáéval
egyezik.

### Melyik mappa melyik?

Egy mappasor csak a mappa **nevét** mutatja, ezért két azonos nevű mappa
egyformán néz ki. Ha rámutatsz egy sorra, buborékban megjelenik a mappa
**teljes útvonala** — ebből látod, melyikről van szó. (Ilyen helyzet
gyakran adódik: a duplikátum-kereső minden forrásmappában saját
`Duplikátumok` alkönyvtárat hoz létre.)

### Bélyegkép a mappaikon helyett

A **Nézet ▸ Mappanézet ▸ Indexképek megjelenítése a könyvtárban**
bekapcsolásával a hasáb sorain a kék mappaikon helyett a mappa egyik
fotójának kis bélyegképe látszik. Ugyanaz a mappa mindig ugyanazt a képet
kapja, futások között is. Alapból kikapcsolva indul, és a választásod
megmarad.

**A fanézetben ez mindig látszik**, a kapcsolótól függetlenül — ott ezért
a menüpont szürke. A kapcsoló az egyszerű, egyszintű listára vonatkozik.

> A hasáb helyi menüjében is szerepel egy **Indexképek megjelenítése a
> könyvtárban** tétel, de az **még nem működik** — a menüsorból viszont
> igen.

### A mappa dátuma

A rácsban a mappa fejlécében ott áll a mappa dátuma. Ezt a benne lévő
legkorábbi fénykép adja: elsősorban a felvétel ideje a fénykép
EXIF-adatából, és ha az hiányzik — például képgenerátorból származó
képeknél —, akkor a fájl ideje. Így felvételi idő nélküli képeknél sem
marad üresen a fejléc, és a dátum szerinti rendezés is a helyére teszi
az ilyen mappákat.

A fájl idejét a program **az első beolvasáskor jegyzi fel, és utána nem
frissíti**. Ez szándékos: a fájl módosítási idejét sok minden átírja
(mentés, másolás, egy másik program), és enélkül ugyanaz a kép hol a
rács elejére, hol a végére ugrott volna, a mappa fejléc-dátuma pedig
elmozdult volna. Aminek van EXIF-felvételi ideje, arra ez nem hat.

### A mappák sorrendje

A **Nézet ▸ Mappanézet** almenü közepén, illetve a hasáb helyi menüjében
állítható:

- **Rendezés létrehozási dátum alapján**
- **Rendezés a legutóbbi változtatások alapján**
- **Rendezés méret alapján**
- **Rendezés név alapján**
- **Rendezés megfordítása** — mindegyikkel párosítható

### Egy mappán belül a képek sorrendje

A mappára jobbgombbal kattintva a **Mappa rendezése** almenüben: dátum,
név, méret vagy **szín** szerint, a **Fordított sorrend** kapcsolóval
párosítva. Ugyanez a **Mappa** menüben is megvan.

A **Szín** szerinti rendezés a képek uralkodó színe szerint sorakoztat: a
színes képek jönnek elöl, a szivárvány sorrendjében, utánuk a
színtelenek. Ha egy mappát épp most olvasott be a program, a szín szerint
még be nem sorolt képek a lista végén, névsorban állnak; ez magától a
helyére kerül, ahogy a háttérben elkészül a színindex.

## Albumok

Az album **nem mozgat fájlokat** — csak egy összeállítás. Ugyanaz a kép
több albumban is szerepelhet.

- Új albumot a **Fájl ▸ Új album…** (Ctrl+N) paranccsal, az eszköztár
  **+** gombjával, vagy a képek helyi menüjének **Új album…** tételével
  hozol létre.
- Meglévő albumhoz a kép helyi menüjének **Hozzáadás az albumhoz**
  almenüjén át adsz hozzá képet. Ugyanez elérhető a képtálca album-gombjával.
- Kivenni a **Eltávolítás az albumból** paranccsal tudsz.
- Képeket egy meglévő album sorára húzva azok **abba az albumba**
  kerülnek. Amíg egyetlen albumod sincs, az **Albumok** csoport alatt ott
  áll a „Képeket idehúzva új albumot hozhat létre." sor — erre ejtve a
  képeket **új album** készül belőlük. Húzás közben a célsor kék hátteret
  kap, hogy lásd, hova esnek majd a képek.

A **Csillagozott képek** egy állandó album: minden csillaggal megjelölt
képet mutatja.

## Gyűjtemények

A gyűjtemény a mappák rendezésére való: több mappát fogsz össze egy név
alá. A hasábon a gyűjtemény fejlécére kattintva nyitod és csukod.

- **Új gyűjtemény…** a mappa helyi menüjéből, az **Áthelyezés
  gyűjteménybe** almenün át.
- A gyűjtemény fejlécére jobbgombbal kattintva **átnevezheted** vagy
  **eltávolíthatod**. A gyűjtemény eltávolítása a mappáidat nem bántja.

Ha az utolsó nyitott gyűjteményt is bezárnád, a program figyelmeztet:
utána a rács üres lesz, amíg nem nyitsz ki valamit.

## Projektek

A **Projektek** csoportban azok a mappák jelennek meg, amiket maga a
program hoz létre: **Kollázsok**, **Mozgófilmek**, **Exportált képek**.
Ide kerülnek az általad készített kollázsok, filmek és exportok, hogy ne
kelljen keresgélni őket.

Az **Exportált képek** a legutóbbi húsz export célmappáját tartja
számon; a fájlkezelőben törölt vagy átnevezett mappák maguktól
kikerülnek a listából.

## Az indexképek

- **Nézet ▸ Kis indexképek** (Ctrl+1) és **Normál indexképek** (Ctrl+2)
  váltja a méretet. Finomabban a képtálca jobb szélén lévő
  nagyítás-csúszkával állíthatod.
- **Nézet ▸ Indexkép felirata** almenüben választhatod, mi legyen a kép
  alatt: **Egyik sem**, **Fájlnév**, **Képfelirat**, **Címkék** vagy
  **Felbontás**.

### Nagyító a rácson

A képtálca nagyítás-csúszkája mellett balra van egy kis **nagyító**
gomb (buboréksúgója: „Nagyító — húzd a képek fölött"). Bekapcsolva a
gomb kék hátteret kap, és onnantól a rácson **nyomva tartva húzva** egy
kis ablak jelenik meg a kurzor alatt: benne a kép a teljes felbontásból,
1:1-ben, tehát részletesebben, mint maga az indexkép. Puszta kattintásra
nem történik semmi — húzni kell. Ugyanezzel a gombbal kapcsolod ki.

## A képtálca

Az ablak alján lévő tálca mindig a jelenlegi kijelölést mutatja. A kék
csík fölötte kiírja, hány kép van benne, milyen dátumtartományból, és
mekkora helyet foglalnak.

A csíkon a dátum **két alakban** jelenhet meg. Ha a kijelölt képek
mindegyike ugyanarról a napról való, egyetlen dátum áll ott; ha többről,
akkor a legkorábbi és a legkésőbbi dátum. A méret felirata is ehhez
igazodik. A csík végén — ha van mit kiírni — ott áll még, hogy a
kijelölésben **mely címkék** szerepelnek, és hány képen (például
`Címkék: nyaralás (12)`). Címke nélküli kijelölésnél ez a rész elmarad.

A tálca akkor hasznos igazán, ha **több mappából** akarsz képeket
összeszedni — például egy kollázshoz:

- **Kijelölt elemek megőrzése** — rögzíti a mostani tartalmat, így másik
  mappára lépve sem tűnik el. Ettől kezdve az újabb kijelöléseidet
  hozzáadhatod.
- **Törlés a tálcáról** — kiüríti.

### Ha albumra kattintasz

Ha a bal hasábon egy **albumot** választasz ki, és közben egyetlen kép
sincs kijelölve, a tálcán nem bélyegképek sorakoznak, hanem **egyetlen
borítókép** a felirattal, hogy mi van kiválasztva és hány kép van benne
— például `Kiválasztott album - 12 fotó`. Amint kijelölsz egy képet, a
bélyegképek veszik át a helyét. A mappákra ez nem vonatkozik: a
mappanézet megszokott kinézete nem változik.

A tálcának **saját kijelölése** van, a rácsétól függetlenül. A tálcán
egy képre kattintva kijelölöd (kék kerettel jelöli), Ctrl-lal
hozzáveszel vagy elveszel egyet, Shift-tel tartományt jelölsz. A rácsban
végzett kijelölés ezt nem törli.

A tálcán lévő képre jobbgombbal kattintva: **Megjelenítés és
szerkesztés**, forgatás, **Keresés a lemezen**, **Tulajdonságok**,
valamint **Kijelölés eltávolítása** — ez utóbbi a **tálcán** kijelölt
képeket veszi ki a tálcáról. A tálcán a **Kijelölés megtartása**
paranccsal is rögzíthetsz.

A tálca jobb szélén van a **Nagyító** is: rákattintva, majd a képek fölé
húzva nagyítva látod a részleteket.

A tálca kimeneti gombsora (**Nyomtatás**, **E-mail**, **Exportálás**,
**Kollázs**, **Film**) keskeny ablakban nem fér ki egészen. Ilyenkor
a sor végén megjelenik a **További lehetőségek…** gomb, és a ki nem
férő gombok alatta, listában érhetők el.

## Rejtett képek

Egy képet a **kép helyi menüjének Elrejtés** parancsával tüntethetsz el
a nézetből — a fájl a lemezen marad. A rejtett képek előhozásához
kapcsold be a **Nézet ▸ Rejtett képek** pontot; ekkor ugyanennek a helyi
menünek a tétele **Megjelenítés**-re vált, és azzal hozod vissza a képet.

> A **Kép** menü **Megjelenítés** tétele és a mappák helyi menüjének
> **Elrejtés** / **Megjelenítés** párja még **nem működik** — a
> kép-elrejtés a kép helyi menüjéből megy.

## Milyen fájlokat lát a program

A figyelt mappákban a PicasaPy háromféle fájlt vesz észre:

- **Fényképek** — JPEG (a `.jpg`, `.jpeg` és `.jpe` név is), PNG, TIFF,
  BMP, GIF, PSD, TGA és **WebP**.
- **Nyers (RAW) felvételek** — a szokásos gyártói kiterjesztések, például
  CR2, NEF, ARW, DNG, ORF, RAF, RW2.
- **Videók** — például AVI, MOV, MP4, MKV, WMV, MPG, MPEG, 3GP, TS,
  M2V, OGG és OGV.

Minden más fájl (dokumentum, hangfelvétel) láthatatlan marad: a program
nem indexeli és nem is bántja.

## Ha egy mappa nem érhető el

Ha egy figyelt mappa lecsatolt lemezen vagy elérhetetlen hálózati
megosztáson van, a PicasaPy nem felejti el: a képek az adatbázisban
maradnak, az indexképek a gyorstárból jönnek. A mappa megjelölve
látszik, és a program szól, ha egy ilyen képet próbálsz megnyitni vagy
szerkeszteni.

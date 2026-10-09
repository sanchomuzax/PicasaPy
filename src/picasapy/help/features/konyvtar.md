# A könyvtár: mappák, albumok, gyűjtemények

A bal hasáb a könyvtárad térképe. Négy fajta bejegyzés lehet benne.

Mindegyiknek **saját ikonja** van, hogy egy pillantásra lásd, mit
nézel: a mappa **kék** mappaikon, a rendes album **narancs könyv**, a
Csillagozott képek **zöld könyv csillaggal**, a program készítette
projekt-mappák (Kollázsok, Mozgófilmek, Exportált képek) **lila könyv
csillaggal**, a címke pedig **szürke címke**.

A **Nézet ▸ Könyvtárnézet** pipa mutatja, hogy a főablak a könyvtárat
mutatja. Ez a pipa mindig be van kapcsolva. A párja, a **Nézet ▸
Szerkesztési nézet** (Ctrl+3) a kijelölt képet (többnél az elsőt) megnyitja a nézőben, ahol
szerkesztheted — lásd [Nézegetés](nezegetes.md). Ugyanezt teszi a
**Kép ▸ Megjelenítés és szerkesztés** is. Mindkettő szürke, amíg nincs
kijelölt kép. A **Nézet ▸ Szerkesztési vezérlők megjelenítése** kapcsoló
a néző bal oldali szerkesztőpanelét mutatja vagy rejti — lásd [A
szerkesztő](szerkeszto.md).

## Mappák

A **Mappák** csoport a lemezen lévő, tényleges mappákat mutatja. Ha
átnevezel vagy áthelyezel itt valamit, az a lemezen is megtörténik.

A hasáb háromféleképpen nézhet ki. A **Nézet ▸ Mappanézet** almenüben
válthatsz köztük:

- **Egyszerű mappanézet** — egyetlen lapos lista, mindegyik mappa egy sor.
- **Fanézet** — a mappák a lemezen elfoglalt helyük szerint, egymásba
  ágyazva.
- **Egyszerűsített fanézet** — fanézet, de csak a **figyelt mappáid**
  ágaival: ami azokon kívül esik, nem látszik. Az ágakon belül a
  csak-továbbvezető, képet nem tartalmazó szintek össze is vonódnak, hogy
  a hosszú útvonalak egyetlen sorba férjenek. Ez a kapcsoló az almenü
  **legalján** áll, elválasztva a másik kettőtől.

Az első kettő között az eszköztár két kis nézetváltó gombjával is
válthatsz. A két gomb mellett van egy **▾** gomb is: ez **ugyanazt a
menüt** nyitja le, ami a **Nézet ▸ Mappanézet** almenü — a nézet, a
sorrend és az indexképek kapcsolója tehát egy helyről vezérelhető, és a
két belépési pont nem tud szétcsúszni. Keskeny ablakban a ▾ gomb
elrejtőzik; a menüsorból ilyenkor is elérhető minden.

A hasáb üres részére jobbgombbal kattintva a hasáb saját menüje nyílik
meg. Ebben a következők vannak:

- a **rendezés** tételei (név, méret, legutóbbi változtatás, fordított
  sorrend) és az Emberek-lista rendezése,
- az **Egyszerűsített fanézet** kapcsoló,
- az **Indexképek megjelenítése a könyvtárban** kapcsoló — ugyanaz, mint a
  **Nézet ▸ Mappanézet** almenüben,
- a **Gyorsbillentyűk** almenü, benne az **Asztal**: a program az Asztal mappára
  ugrik, ahogy a **Nézet ▸ Mappanézet ▸ Asztal** pont is teszi. (A
  felirat az eredeti Picasa fordításából való; billentyűkhöz nincs köze.)

> Ha a program még nem tudja, melyek a figyelt mappáid, az
> Egyszerűsített fanézet a **teljes fát** hagyja meg — inkább mutat
> többet, mint hogy elrejtse a mappáidat. A figyelt mappákat a
> [Mappakezelőben](mappakezelo.md) állítod be.

**Mindhárom beállítás megmarad a következő indításig.**

### Honnan induljon a fa

A **Nézet ▸ Mappanézet** almenü tetején négy ugrópont áll — ezeket az
eredeti Picasa is ott tartotta:

- **Sajátgép** — a teljes fa, minden mappával;
- **Képek**, **Dokumentumok**, **Asztal** — a fa szintén teljes lesz, de
  a program odaugrik, és kijelöli az adott mappát.

A **Mappák** felirat megmondja, hol állsz: „Alapértelmezett nézet" a
lapos listában, „Sajátgép" a fanézetben, a három ugróponton pedig a
mappa neve.

Ha a választott mappa nincs meg a gépen, nem kapsz hibaüzenetet: a fa a
Sajátgépre áll vissza. A választott kezdőpont megmarad — ahol
kilépéskor jártál, ott indul a program legközelebb is.

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

A hasáb helyi menüjének **Indexképek megjelenítése a könyvtárban** tétele
ugyanezt a kapcsolót állítja, tehát a két hely nem csúszhat szét.

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

### A mappa tulajdonságai

A mappa sorára jobbgombbal kattintva a **Mappaleírás szerkesztése…**
tétel, vagy a megnyitott mappára a **Mappa ▸ Leírás szerkesztése…**
megnyitja a **Mappa tulajdonságai** ablakot. A mezői:

- **Név:** — ide írva a mappát át is nevezheted. Az **OK** gomb átnevezi a
  mappát a lemezen, a benne lévő képek, almappák és a `.picasa.ini` vele
  együtt maradnak. Ha a név foglalt, érvénytelen, vagy a mappa egyik képe
  épp szerkesztés alatt áll, **A mappa nem nevezhető át** címmel ablak
  mondja meg az okot, és semmi nem változik;
- **Dátum:** — a mappa dátuma ÉÉÉÉ-HH-NN alakban. Az **Automatikus dátum**
  gomb törli a kézzel megadott értéket, és a mappa visszaáll a benne lévő
  legkorábbi kép dátumára. Érvénytelen dátumnál az **OK** szürke;
- **Zene:** — a **Zene használata diavetítéshez és mozgófilmes
  prezentációhoz** jelölővel, és a **Tallózás…** gombbal választott hangfájllal
  (Windowson `.mp3` vagy `.wma`, máshol `.mp3` vagy `.m4a`). Ez a zene szól
  a mappa diavetítésénél és a mappából készített filmben. A fájlmező és a
  gomb csak bejelölt jelölővel él;
- **Leírás (opcionális):** — a mappa leírása.

Az **OK** egyszerre menti a nevet, a dátumot, a zenét és a leírást, és
bezárja az ablakot. A **Mégse** semmit nem ment.

Az album tulajdonságai ugyanebben az ablakban nyílnak (lásd lentebb). A
**Felvétel készítésének helye (opcionális):** mező csak albumnál szerkeszthető;
mappánál szürke.

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

### Kézi sorrend: húzd oda, ahova való

A képeket egérrel is átrendezheted: fogd meg a kijelölt képeket, és húzd
őket arra a helyre, ahol állniuk kell. A rács mutatja, hova esnek majd.

Az átrendezés magától a **Kézi sorrend** szempontra állítja a mappát —
ez a **Mappa rendezése** almenü új tétele —, így azonnal látod is, amit
húztál.

A kézi sorrend a mappa mellé, a `.picasa.ini` fájlba kerül. Megmarad a
következő indításig, és a mappával együtt másik gépre is átvihető.

Egy húzás mindig **egy mappán belül** marad: több mappa képeit egyszerre
nem lehet egymás közé rendezni.

### Ugrás a következő mappára a görgetősávról

A rács görgetősávjának tetején és alján egy-egy **kettős nyíl** ül:
**Előző album** és **Következő album**. Ezekkel a rácsban a következő,
illetve az előző **címsorra** ugrasz — vagyis a következő mappa vagy
album elejére —, anélkül, hogy végiggörgetnéd a képeket. Nyomva tartva
ismételnek.

## Albumok

Az album **nem mozgat fájlokat** — csak egy összeállítás. Ugyanaz a kép
több albumban is szerepelhet.

- Új albumot a **Fájl ▸ Új album…** (Ctrl+N) paranccsal, az eszköztár
  **+** gombjával, vagy a képek helyi menüjének **Új album…** tételével
  hozol létre. A program **nem kérdez nevet**: azonnal készít egy
  **Névtelen** albumot a kijelölt képekből, ahogy az eredeti Picasa is
  tette. A nevet utólag bármikor átírod (lásd lentebb). Kijelölés nélkül
  nem történik semmi.
- Meglévő albumhoz a kép helyi menüjének **Hozzáadás az albumhoz**
  almenüjén át adsz hozzá képet. Ugyanez elérhető a képtálca album-gombjával.
- Kivenni a **Eltávolítás az albumból** paranccsal tudsz. A program
  rákérdez — az ablak **Elemek eltávolítása**, a gomb **Kép
  eltávolítása** (több képnél **Képek eltávolítása**) —, és a fájlhoz nem
  nyúl, csak az összeállításból veszi ki. A kérdés a **Beállítások ▸
  Általános** lapon kikapcsolható („Eltávolítás az albumból megerősítés
  nélkül").
- Képeket egy meglévő album sorára húzva azok **abba az albumba**
  kerülnek. Amíg egyetlen albumod sincs, az **Albumok** csoport alatt ott
  áll a „Képeket idehúzva új albumot hozhat létre." sor — erre ejtve a
  képeket **új album** készül belőlük. Húzás közben a célsor kék hátteret
  kap, hogy lásd, hova esnek majd a képek.

A **Csillagozott képek** egy állandó album: minden csillaggal megjelölt
képet mutatja.

### Az album nevének és adatainak átírása

Az album sorára jobbgombbal kattintva az **Albumleírás szerkesztése…**
tétel megnyitja az **Album tulajdonságai** ablakot. Öt mezője van:
**Név**, **Dátum**, **Zene**, **A felvétel helye** és **Leírás**. A mentés minden
olyan mappa `.picasa.ini` fájljába átvezeti a változást, ahol az albumnak
van tagja.

Ugyanez az ablak nyílik meg a mappáknál is (**Mappaleírás
szerkesztése…**) — az eredeti Picasa is egy ablakot használ a kettőre.
Mappánál a mezők kicsit mások (lásd fent, **A mappa tulajdonságai**).

### Az Album menü albumnézetben

A **Mappa** menü parancsai a **megnyitott mappára** hatnak. Ha egy
albumot nyitsz meg, a menüsorban a **Mappa** helyén **Album** áll, ahogy
az eredeti Picasában. Az első tétele, az **Albumleírás szerkesztése…** a
nyitott album **Album tulajdonságai** ablakát nyitja meg (lásd fent).
Mappanézetben ugyanezen a helyen a mappa leírását szerkeszted.

Album vagy Emberek-album nézése közben a program a korábban nézett
mappát megjegyzi, de a menü **Keresés a lemezen**, **Eltávolítás a
Picasából…**, **Áthelyezés…** és **Törlés…** tétele ilyenkor **szürke** —
így véletlenül sem a korábbi mappára hatnak. Ha ilyenkor mappát akarsz
kezelni, előbb kattints a mappára a bal hasábon.

## Gyűjtemények

A gyűjtemény a mappák rendezésére való: több mappát fogsz össze egy név
alá. A hasábon a gyűjtemény fejlécére kattintva nyitod és csukod.

- **Új gyűjtemény…** a mappa helyi menüjéből, az **Áthelyezés
  gyűjteménybe** almenün át.
- A gyűjtemény fejlécére jobbgombbal kattintva **átnevezheted** vagy
  **eltávolíthatod**. A gyűjtemény eltávolítása a mappáidat nem bántja.

Azt, hogy egy mappa melyik gyűjteménybe tartozik, a program a mappa
saját `.picasa.ini` fájljába írja, ahogy az eredeti Picasa is. A
besorolás ezért a mappával együtt költözik, és a program újratelepítése
után is megmarad. Ha egy gyűjteményt eltávolítasz, a mappái visszakerülnek
a **Mappák a lemezen** csoportba.

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

### Kis képek: alapból el vannak rejtve

A rács **alapból csak a nagy képeket mutatja**, ahogy az eredeti Picasa is.
Ami nagyon kicsi — például egy legfeljebb 200 képpont hosszú ikon —, vagy
kis területű és szélsőségesen keskeny sáv, az nem látszik a rácson.
Ha egy kép „eltűnt" a mappából, érdemes ezt ellenőrizni. Videókat és a
mérettel nem rendelkező bejegyzéseket ez nem érint.

A **Nézet ▸ Kis képek** kapcsoló a kisebb képeket is megjeleníti: pipával
látszanak, pipa nélkül (ez az alapállás) nem. A beállítás megmarad a
következő indításig. A fájlokhoz ez nem nyúl, csak azt dönti el, mi kerül a
rácsra.

### Megjelenítési mód az indexképeken

A **Nézet ▸ Megjelenítési mód** almenü választása — köztük a **16 bites
(szemcsézett)** mód — az indexképeken is látszik. Lásd:
[Nézegetés](nezegetes.md).

### Kép húzása másik programba

A rácsból vagy a képtálcáról a képeket **kihúzhatod más programba** is —
például egy levélbe vagy egy fájlkezelő ablakába. A másik program
**fájlként** kapja őket: a kijelölés összes képét, nem csak azt, amelyiket
megfogtad. A tálcáról a tálca **saját kijelölése** megy, akkor is, ha a
képek több mappából valók. A program közben a fájlokat nem módosítja. (A
mappák és albumok közti húzás ettől független, lásd fent.)

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

A **Ctrl+H** ugyanazt csinálja, mint a tálca helyi menüjének
kijelölés-megtartó tétele: rögzíti a kijelölést. Nézőben nem működik.

Ha egy **kollázs** készítése közben a **kollázs lapjáról** a könyvtárba
lépsz, hogy még képeket gyűjts, a tálca fölött egy sáv jelenik meg ezzel
az üzenettel: „Jelölje ki azokat az elemeket, amelyeket a projekt
kliptálcájára fel szeretne venni, majd a »Vissza« gombra kattintva térjen
vissza a projekthez". A **Vissza a kollázshoz** gombbal visszalépsz a
kollázsra, a sáv jobb szélén lévő **×** pedig csak elrejti az üzenetet — a
kollázs lapja nyitva marad. Lásd [Kollázs](kollazs.md).

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

## A képek dátumának módosítása

Ha egy képnek rossz a dátuma — például a gép órája rosszul volt beállítva
—, javíthatod. Jelöld ki a képeket, majd **Eszközök ▸ Dátum és idő
beállítása…**. A **Dátum módosítása – N fotó** ablakban látod az első
kép bélyegképét és a **Jelenlegi fotódátum**át, megadhatod az **Új
fotódátum**ot (a dátumra kattintva naptár nyílik) és az **Új fotó
időpontja**t. Két mód közül választasz:

- **Minden fotó dátumának eltolása ugyanannyival** — a program az első
  kép régi és új dátuma közti különbséget adja hozzá az összes kijelölt
  kép saját idejéhez, tehát a képek közti időkülönbségek megmaradnak;
- **Minden fotó dátumának és idejének beállítása ugyanarra** — mindegyik
  kép ugyanazt a dátumot és időt kapja.

Az **OK** menti a változtatást, ahogy az eredeti Picasa is: az új
felvételi dátumot **beleírja a képfájl EXIF-adataiba**, és a fájl
módosítási idejét is ugyanannyival eltolja. A `.picasa.ini` fájlhoz nem
nyúl. Ezután a program újraolvassa a mappát, így a rács, a dátum szerinti
rendezés és a **Tulajdonságok** panel már az új dátumot mutatja — és
mivel a fájlban van, más program is ezt látja.

Az EXIF-dátum írása **JPEG** képeken működik.

## A Tulajdonságok panel

A jobb oldali fiók (a **Ctrl+0**-val, vagy a fiók szélén lévő keskeny,
nem látható sávra kattintva nyitod és zárod) **Tulajdonságok** panelje
(**Alt+Enter**, vagy a képtálca panelkapcsolójáról) a kijelölt kép adatait mutatja. Legfelül a **Fájl
útvonala**, a **Fájlméret** és a **Méretek** áll, alattuk a felvétel adatai:
a **Fényképezőgép gyártmánya** és **típusa**, a felvétel és a digitalizálás
ideje, a tájolás, a **Vaku** állása, az **Objektív** neve, a
**Fókusztávolság**, az **Exponálási idő**, az **F-érték**, az ISO, a
**Fehéregyensúly**, a **Fénymérés módja**, az **Exponálási program**, a
**Tömörítés** és a **Színtér**, végül a **Kulcsszavak** és a
GPS-koordináták.

A sorrend ugyanaz, mint az eredeti Picasában. Amiről a fájlban nincs adat,
annak **a sora sem jelenik meg** — a panel tehát képenként rövidebb vagy
hosszabb. Videóra ma csak a három felső sor jön ki.

### Az objektív neve

Ha a képben **XMP-adat** is van — ilyet a legtöbb szerkesztőprogram ír a
fájlba —, és abban ott az objektív neve, a program **azt** mutatja, és
tovább nem is keres. Ez az eredeti Picasa sorrendje.

Egyébként: a legtöbb fényképezőgép nem írja le az objektív nevét emberi
nyelven, csak egy azonosítót hagy a fájlban. **Canon- és Nikon-gépek
képein** a program ezt az azonosítót feloldja, és az **Objektív** sorba a
valódi objektívnevet írja — ugyanabból a listából, amit az eredeti Picasa
is használt. Ha egy azonosítóhoz több objektív tartozik, a gyújtótávolság
és a rekesz alapján választ közülük.

Ha a fájl maga is tartalmaz objektívnevet, de a feloldás nem ad találatot, a
fájlban lévő név marad. Ha az sincs, a program a fájlból kiolvasott
gyújtótávolságból és rekeszből állít össze egy nevet — például
`18-55mm f/3.5-5.6`. Más gyártók gépeinél egyelőre az marad, amit a fájl
ír.

### Tömörítés és fehéregyensúly

A **Tömörítés** sor a kép tárolási módját nevezi meg: **Tömörítetlen**,
**JPEG**, **LZW**, **JPEG 2000**, **Veszteség nélküli tömörítés**,
illetve a gyártó-specifikus nyers formátumok (**Nikon NEF-tömörítésű**,
**Sony ARW-tömörítésű**, **Pentax PEF-tömörítésű** és a többi) —
összesen 36-féle kódot ismer fel. Ha a fájlban olyan kód áll, amit a
lista nem ismer, a **számot** írja ki.

Ugyanez áll a **Fehéregyensúly** sorra: **Automatikus** vagy **Kézi**, és
ha a fájl ettől eltérő kódot tárol, a szám látszik. Így a sor akkor sem
marad üresen, ha a fényképezőgép valami szokatlant írt bele.

## Rejtett képek

Egy képet a **Kép ▸ Elrejtés** paranccsal vagy a **kép helyi menüjének
Elrejtés** tételével tüntethetsz el a nézetből — a fájl a lemezen marad.
A **Kép ▸ Elrejtés** csak a kijelölés látható képeit rejti el; ha a
kijelölésben már rejtett kép is van, azt nem hozza elő.
A rejtett képek előhozásához kapcsold be a **Nézet ▸ Rejtett képek**
pontot. Visszahozni a **Kép ▸ Megjelenítés** paranccsal tudod: a
kijelölt képek közül csak a rejtetteket teszi újra láthatóvá, a már
látható képeket nem rejti el. A kép helyi menüjében is ott van, ugyanennek
a tételnek a helyén **Megjelenítés**-re vált.

Egész mappát is elrejthetsz: jelöld ki, majd **Mappa ▸ Elrejtés**, vagy a
mappa helyi menüjében **Mappa elrejtése**. A mappa eltűnik a bal hasábról;
a **Nézet ▸ Rejtett képek** bekapcsolásával a **Rejtett mappák** között
látod viszont. Visszahozni a **Mappa ▸ Megjelenítés** paranccsal tudod, vagy
a mappa helyi menüjének **Mappa megjelenítése** tételével: ehhez
előbb kapcsold be a **Nézet ▸ Rejtett képek** pontot, és jelöld ki a mappát a
**Rejtett mappák** között. A mappa ugyanúgy a
lemezen marad.

### A rejtett mappák jelszava

A **Rejtett mappák** jelszóval zárható le. Ha van jelszó, a **Nézet ▸
Rejtett képek** bekapcsolása előbb ezt kéri.

1. Kapcsold be a **Nézet ▸ Rejtett képek** pontot. A bal hasáb alján
   megjelenik a **Rejtett mappák** fejléc (csak akkor, ha van rejtett
   mappád).
2. Kattints a fejlécre a **jobb** egérgombbal, és válaszd a **Jelszó
   megadása/módosítása…** pontot. (A fejléc csak a jobb gombra válaszol:
   kijelölni nem lehet.)
3. Írd be a jelszót kétszer — a másodikat az **Írja be újra a jelszót**
   mezőbe —, és nyomd meg az **OK**-t. Amíg a két mező nem egyezik, az OK
   szürke, és a párbeszéd kiírja, hogy a jelszavak nem egyeznek.

A mezők alatt egy jelölőnégyzet áll: **Erősebb védelem (a Picasa nem
nyitja meg)**.

- **Bejelöletlenül** (ez az alapértelmezés) a jelszó ugyanúgy tárolódik,
  ahogy a windowsos Picasa tárolta: ha ugyanazokat a mappákat mindkét
  programmal nézed, a jelszó ott is, itt is nyit.
- **Bejelölve** a jelszó erősebben tárolódik, cserébe a windowsos Picasa
  nem tudja megnyitni vele a rejtett mappákat.

Ugyanezen az úton tudod a jelszót később megváltoztatni. Ha már van
beállított jelszó, a párbeszédben megjelenik **A jelszó törlése** gomb is
— ezzel veszed le a zárat.

Ha rossz jelszót írsz be a rejtett képek előhozásakor, a program **Hibás
jelszó** címmel jelzi, és a rejtett mappák rejtve maradnak; az üzenetet
bezárva újra próbálkozhatsz.

> A jelszó csak a PicasaPy felületén rejti el a képeket. A fájlok a
> lemezen változatlanul ott vannak, bármelyik fájlkezelővel megnyithatók.
> Ezt a párbeszéd maga is kiírja.

## Milyen fájlokat lát a program

A figyelt mappákban a PicasaPy háromféle fájlt vesz észre:

- **Fényképek** — JPEG (a `.jpg`, `.jpeg` és `.jpe` név is), PNG, TIFF,
  BMP, GIF, PSD, TGA és **WebP**.
- **Nyers (RAW) felvételek** — a szokásos gyártói kiterjesztések, például
  CR2, NEF, ARW, DNG, ORF, RAF, RW2 (lásd lentebb).
- **Videók** — például AVI, MOV, MP4, MKV, WMV, MPG, MPEG, 3GP, TS,
  M2V, OGG és OGV.

Minden más fájl (dokumentum, hangfelvétel) láthatatlan marad: a program
nem indexeli és nem is bántja.

### A nyers (RAW) fájlok

A nyers fájlokból mostantól **kép is látszik**: a rácson, a nagy
nézőben, a mappák borítóképén és a szerkesztő előnézetén is. A
bélyegkép a gyorstárba is bekerül, tehát másodszorra már gyors.

Nyers fájlt ugyanúgy használhatsz, mint egy JPEG-et: exportálás,
duplikátum-keresés, szín szerinti keresés, kollázs, diavetítés, webre
mentés, importálás és arckeresés — mind elfogadja.

Két dolgot érdemes tudni:

- **A szerkesztés mentése nyers fájlra nem megy**: a program
  hibaüzenetet ad. Nyers fájlt nem lehet visszaírni, az eredeti Picasa
  sem tette. Ha kimentett képet szeretnél, exportálj.
- Ha egy nyers fájlt mégsem sikerül megnyitni (ismeretlen gépmodell,
  sérült fájl), a helyén **helyőrző** látszik — nem néma, üres kép.

## Ha egy mappa nem érhető el

Ha egy figyelt mappa lecsatolt lemezen vagy elérhetetlen hálózati
megosztáson van, a PicasaPy nem felejti el: a képek az adatbázisban
maradnak, az indexképek a gyorstárból jönnek. A mappa megjelölve
látszik, és a program szól, ha egy ilyen képet próbálsz megnyitni vagy
szerkeszteni.

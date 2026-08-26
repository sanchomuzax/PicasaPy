# Változásnapló

A projekt a [Semantic Versioning](https://semver.org/) elvét követi; a `0.x`
sorozat instabil. A teljes, gépi generálású kiadási jegyzék a
[Releases](https://github.com/sanchomuzax/PicasaPy/releases) oldalon él — ez a
fájl a lényegi, ember által írt kiemeléseket rögzíti.

## [Nem kiadott]

### Javítva
- **A csillagozott képek nézete azonnal követi a csillag levételét (#1443).**
  Eddig, ha a **csillagozott** szűrőben állva levetted a csillagot egy képről,
  a kép ottmaradt a listában, amíg más nézetre nem váltottál — vagyis nem azt
  láttad, ami valójában van. Mostantól a kép rögtön kikerül a nézetből, és a
  zöld eredménysáv is a valódi darabszámot mutatja (korábban akkor is
  „2 kép látható" állt ott, amikor egy sem látszott).

## [0.8.101] – 2026-08-26

### Hozzáadva
- **Az arcfelismeréshez szükséges fájlt már a program is le tudja tölteni
  (#1496).** Az **Eszközök ▸ Arcok keresése…** ablak eddig megmondta ugyan,
  hogy hiányzik egy modellfájl és hova kellene másolni — de a fájl
  beszerzése a felhasználóra maradt, így friss telepítésen az **Arcok
  keresése** gomb végig szürke volt. Mostantól a hiányt jelző szöveg
  mellett ott a **Modell letöltése** gomb: megnyomásra a program lehozza a
  szükséges fájlokat (összesen kb. 37 MB), közben mutatja, hol tart, és a
  letöltés bármikor megszakítható. Amint kész, az **Arcok keresése** gomb
  azonnal élővé válik — újraindítás nélkül. Az ablak kiírja, honnan jön a
  fájl (az OpenCV Zoo nyílt forrású projektjéből), mekkora, milyen licenc
  alatt áll, és hova kerül a gépen.
- **A letöltött fájl épségét a program ellenőrzi (#1496).** Egy
  félbeszakadt letöltésből fél fájl marad, és ettől az arckeresés **nem
  hibaüzenetet ad, hanem rossz eredményt** — ami sokkal rosszabb. Ezért a
  program a letöltés végén összeveti a fájl méretét és ujjlenyomatát a
  várttal, és ha nem stimmel, **eldobja**, ahelyett hogy használná; a
  korábban letöltött, jó fájlt egy elrontott újratöltés sem ronthatja el.
  Ha nincs internet, azt is megmondja, ahelyett hogy némán nem történne
  semmi.
### Javítva
- **A szín szerinti keresés eddig semmit nem adott — mostantól működik
  (#1500).** Ha a keresősávba azt írtad, hogy `szín:kék` (vagy
  `color:blue`), a program mindig üres listát mutatott, akármilyen képek
  voltak a gyűjteményben: a színek kiszámolása ugyanis soha nem indult el.
  Mostantól az első ilyen keresésre a program a **háttérben** nekilát
  átnézni a képeket, és amint végzett, **a találati lista magától
  kiegészül** — nem kell újra begépelni a keresést. A munka nem akasztja
  meg a programot, bármikor tovább lehet dolgozni közben, és az alsó
  sávban látszik, hogy dolgozik valamin. Ha közben másra keresel rá, az
  elkészült feltöltés nem rántja vissza a régi találatokat.
- **Megmondja, ha még nem végzett a színek átnézésével (#1500).** Eddig a
  „nincs ilyen színű képem" és az „ezt még ki sem számoltuk" ugyanúgy
  nézett ki: üres lista, semmi magyarázat. Mostantól egy borostyánsárga
  tájékoztató sáv írja ki, hány kép van már átnézve az összesből, és hogy
  a lista magától ki fog egészülni, amint a feldolgozás elkészül. A sávon
  ott a **Leállítás** gomb is: a képek átnézése nagy gyűjteménynél sokáig
  tart, ezért bármikor megállítható — a már kiszámolt színek megmaradnak,
  és a következő színkeresés onnan folytatja.
- **A sérült vagy hibás képfájlok nem lassítják le a színek átnézését
  (#1500).** A megnyithatatlan képeket a program egyszer megjelöli, és
  utána békén hagyja őket, ahelyett hogy minden körben újra és újra
  nekifutna.
- **Az átszerkesztett képek színe frissül (#1500).** Ha egy képet
  megváltoztatsz, a program a következő átnézéskor újraszámolja a színét,
  így nem a régi színével marad kereshető.

## [0.8.100] – 2026-08-26

### Megváltozott
- **A képek alatti sáv az eredeti Picasa elrendezését kapta meg (#1420).**
  Eddig egy 72 képpont magas, egysoros csík volt: a kijelölt képek pici,
  20 × 20 képpontos bélyegképekben sorakoztak benne, a zöld **Feltöltés**
  gomb pedig egészen a jobb szélre volt szorulva, a Nyomtatás/E-mail/
  Exportálás gombok mögé. Mostantól a sáv **105 képpont** magas, és a
  Picasáéval azonos módon oszlik ketté: a bal harmadában egy külön
  keretezett **képtálca** ül (81 képpont magas), amelyben a kijelölt
  képek immár **nagy, jól kivehető bélyegképként** látszanak, jobb szélén
  pedig egymás alatt a három tálca-gomb (megtartás, ürítés, albumhoz
  adás). A jobb oldalon felül a csillag, a két forgatás és a
  nagyítás-csúszka; alattuk — egy vékony elválasztó vonal alatt — a zöld
  **Feltöltés** gomb, közvetlenül utána a Nyomtatás/E-mail/Exportálás
  gombsor, ahogy az eredetiben.
- **A tálca „Albumhoz adás" gombja ikonossá vált (#1420).** Az eredeti
  Picasában ennek a három tálca-gombnak egyikén sincs felirat, csak ikon
  és buboréksúgó — most nálunk is így van; a gomb fölé húzva a súgó
  továbbra is kiírja, mit csinál.
- **Keskenyebb ablakban is használható marad a sáv (#1420).** A program
  ablaka mostantól 900 helyett **800 képpont** szélességig húzható össze
  anélkül, hogy bármelyik alsó gomb kicsúszna a képernyőről.
### Javítva
- **A szín szerinti keresés mostantól úgy válogat, ahogy az eredeti Picasa
  (#1480).** Eddig a program egyetlen színt számolt ki minden képhez — az
  egész kép átlagát —, és azt sorolta be. Egy naplementés fényképnél ez
  például barnás átlagot ad, holott a képen a narancs a meghatározó, így a
  kép nem jött elő a narancsra keresve. Mostantól a program végignézi a
  kép minden képpontját, és azt a színt választja, amelyikből a képen a
  legtöbb, legélénkebb folt van — pontosan úgy, ahogy az eredeti Picasa
  tette. Ennek látható következménye, hogy **más képek jönnek majd elő** a
  `szín:kék`-féle keresésre, mint eddig; a fakó, szürkés képpontok
  egyáltalán nem számítanak bele a döntésbe. A **fekete**, a **fehér** és a
  **szürke** ezentúl ugyanazt a képhalmazt adja: az eredeti sem tett
  köztük különbséget, a színtelen képek mindháromra előjönnek. A korábban
  kiszámolt (rossz módszerrel készült) besorolásokat a program eldobja és
  újraszámolja.

## [0.8.97] – 2026-08-26

### Hozzáadva
- **El lehet indítani az arcok keresését (#1473).** A program eddig
  hirdette az arckeresés haladását a bal hasábban, de magát a keresést
  SEHONNAN nem lehetett elindítani: se menüpont, se gomb nem vezetett
  hozzá, pedig a motorja készen állt. Mostantól az **Eszközök ▸ Arcok
  keresése…** menüpont megnyit egy ablakot, ahonnan a keresés
  elindítható és bármikor meg is szakítható; a megtalált arcok a bal
  hasáb **Névtelenek** albumában várják, hogy nevet adjon nekik. Az ablak
  nem tapad az útba: bezárható, a keresés a háttérben megy tovább, a
  haladás pedig a Névtelenek album mellett látszik. Második lépésként a
  hasonló arcok csoportba is rendezhetők, hogy egyszerre lehessen nevet
  adni nekik. **Fontos:** az arcfelismeréshez egy külön letölthető
  modellfájl kell, ami alapból nincs a program mellett — ha hiányzik, az
  ablak most már **megmondja, mi hiányzik és hova kell tenni**, ahelyett
  hogy némán szürke gombot mutatna. (A modellfájl beszerzésére még nincs
  gomb a programban.)
- **Végre lehet nyomtatni a képeket (#1472).** A **Fájl ▸ Nyomtatás…**
  menüpont eddig szürke volt, a hozzá hirdetett **Ctrl+P** billentyű pedig
  egyáltalán nem működött, és a képek alatti sávban lévő **Nyomtatás** gomb
  is némán semmit nem csinált — pedig a nyomtatás motorja már régóta kész
  volt a program belsejében, csak semmi nem vezetett hozzá. Mostantól a
  menüpont és a **Ctrl+P** a rácsban kijelölt képeket, a képek alatti sáv
  **Nyomtatás** gombja pedig a nagyítós nézetben az éppen látott képet
  küldi nyomtatásra; diavetítés közben mindegyik a vetített képre
  vonatkozik. Az ablakban kiválasztható a nyomtató, és a képek mindig
  **PDF-fájlba** is nyomtathatók — ez akkor is működik, ha egyáltalán
  nincs telepített nyomtató. Megadható, hogy a teljes kép férjen a lapra,
  vagy töltse ki azt vágással, és hogy a lap álló, fekvő vagy a képhez
  igazodó legyen. Egy kép egy lapra kerül. Ha a nyomtatás nem sikerül, az
  ablak most már kiírja, miért — eddig ilyenkor sem történt semmi,
  magyarázat nélkül; és ha egy kijelölt fájlt a program nem tud
  kinyomtatni (például videó vagy nyers fényképezőgép-fájl), akkor
  **néven nevezi**, ahelyett hogy csendben kihagyná a lapját.
  (A **Mappa ▸ Bélyegképek nyomtatása…** továbbra sem működik: az egy
  lapra több képet tenne, amihez még nincs meg a program alatti motor.)

### Módosítva
- **Sokkal kevesebbet olvas a hálózatról a másodpéldány-keresés (#1481).**
  Ha két fénykép fájlmérete véletlenül azonos, a program eddig mindkettőt
  elejétől a végéig végigolvasta, hogy eldöntse, tényleg ugyanaz a kép-e —
  hálózati meghajtón (NAS) ez lassú. Mostantól előbb csak a fájlok elejéből
  és végéből olvas be egy-egy kis darabot (összesen ~33 kilobájtot), ahogy
  az eredeti Picasa is teszi, és a teljes átolvasás csak akkor indul el, ha
  ez a gyors ellenőrzés nem tudta megkülönböztetni a két fájlt. Ugyanez
  gyorsítja az importálásnál a „Másodpéldányok kihagyása" ellenőrzést is.
  A találatok **pontossága nem változik**: a program továbbra is csak akkor
  mond két képet azonosnak, ha bitre azonosak — a gyors ellenőrzés csak
  kizárni tud, kimondani nem.

## [0.8.96] – 2026-08-26

### Javítva
- **Windowson a fanézetre váltás után újra látszik a kiválasztott mappa
  (#1477).** A bal hasáb fanézetében a program eddig csak két szintig
  nyitotta ki a mappák sorát, a kiválasztott mappa pedig eltűnt a
  szemünk elől. Az ok a Windows és a Linux eltérő útvonal-írásmódja volt.
  (A Linuxon futó változatot ez sosem érintette.)

## [0.8.95] – 2026-08-25

### Javítva
- **Nem tűnik el a pipa, ha a menüben a már beállított sorra kattintunk
  (#1468).** Az olyan menücsoportokban, ahol egyszerre csak egy sor lehet
  bejelölve, eddig hibás volt a viselkedés: ha a felhasználó a MÁR aktív
  sorra kattintott, a pipa lekerült róla, és a menü újranyitásakor a
  csoport egyetlen során sem látszott jelölés — hiába volt a beállítás
  érvényben. A hiba mérhetően jelentkezett az **Eszközök ▸ Nyelv** menüben,
  a bal oldali mappalista jobbklikk-menüjének **rendezésében** és a mappák
  jobbklikk-menüjének **„Mappa rendezése"** almenüjében. A **Nézet ▸
  Könyvtárnézet** sorról pedig egyetlen kattintás véglegesen leszedte a
  pipát. Mostantól mindegyikben pontosan azon a soron áll a jelölés,
  amelyik érvényben van — akárhányszor kattintunk rá.
- **A Nézet ▸ Mappanézet menü végre azt csinálja, amit a neve ígér (#1454).**
  Eddig ugyanazt az öt rendezési sort kínálta, mint a Mappa ▸ Rendezés — a
  Picasában viszont ez a menü nem rendez, hanem a bal oldali mappalista
  szerkezetét állítja. Mostantól három sor áll benne: **Egyszerű mappanézet**
  (a megszokott lapos lista), **Fanézet** (a mappák a valódi
  könyvtárszerkezetükben, kinyitható ágakkal) és **Egyszerűsített fanézet**
  (a fában azok a köztes szintek olvadnak össze a gyerekükkel, amelyeknek se
  saját képük, se elágazásuk nincs — például a `/` ▸ `mnt` ▸ `photo` lánc
  egyetlen `/mnt/photo` sorrá; egy képek nélküli, de több almappát tartó
  mappa megmarad külön sornak). Az első kettő egymást váltja, a harmadik
  külön ki-be kapcsolható. A fanézet eddig el volt készülve, de semmilyen
  menüből nem lehetett elérni; a bal hasáb jobbklikk-menüjében az
  „Egyszerűsített fanézet" sor pedig szürke, kattinthatatlan volt — az is
  élővé vált. A mappák rendezése változatlanul ott van, ahol eddig: a Mappa ▸
  Rendezés almenüben és a mappák jobbklikk-menüjében. **A választott nézet
  egyelőre nem marad meg a program bezárása után** — újraindításkor a
  program az Egyszerű mappanézetből indul; a megjegyzése külön munka lesz.

### Belső
- **A menüpipák jelölése már nem függ egy véletlen mellékhatástól (#1468).**
  A **Nézet ▸ Indexkép felirata** és a **Mappa ▸ Rendezés** csoportokban
  ugyanaz a hiba készen állt, de nem látszott: e két beállítás háttérkódja
  akkor is jelez frissítést, ha a választott érték nem változott, és ez
  véletlenül helyrehozta a pipát. Ez a védelem nem volt szándékos, és egy
  későbbi átalakítás némán elvehette volna, ezért mindkét csoport megkapta
  a rendes megoldást. Egy őr-teszt mostantól a teljes felületen figyeli,
  hogy új menücsoport ne kerülhessen be a hibás mintával.
- **A tesztek már nem írják át egymás alól a rendszerfüggvényeket (#1375).**
  A tesztek egy része úgy cserélt ki szabványos függvényeket (fájlmozgatás,
  külső program indítása, lemezműveletek), hogy a csere a futás idejére az
  EGÉSZ programra érvényes volt, nem csak a vizsgált részre. Ebből a
  háttérszálakkal együtt futó tesztek egymás viselkedését írhatták át. A
  felmérés 76 ilyen helyet talált 30 fájlban; ebből 69 állt át a saját
  moduljának fogantyújára, 7 pedig dokumentált kivétel maradt (ezek nem
  kölcsönvett függvények, hanem magának a folyamatnak az állapotai). Egy
  őr-teszt vigyáz rá, hogy a régi alak ne kerüljön vissza. A felhasználó
  ebből semmit nem lát; a haszna az, hogy a hibajelzéseink megbízhatóbbak.

### Javítva
- **Nem omlik össze a program mappaváltáskor, amikor sok bélyegkép készül
  egyszerre (#1457).** Nagyobb mappára váltva a program négy szálon gyártja a
  bélyegképeket, miközben a rács maga is újraépül. Ilyenkor előfordult, hogy
  egy éppen elkészült bélyegképet a program már azután próbált átadni a
  felületnek, hogy az annak helyet adó rácselem eltűnt — ettől a program
  figyelmeztetés nélkül kilépett, és a még el nem mentett munka elveszett. A hiba
  ritka és időzítésfüggő volt: leginkább terhelt gépen, gyors mappaváltáskor
  jött elő. Mostantól a kész bélyegkép átadása és a rácselem eltűnése nem
  csúszhat egymásra, a már eltűnt elemhez tartozó munka pedig csendben
  félreteszi az eredményét.
- **Nem villan fel többé hibaüzenet, amikor a program a háttérben frissíti a
  rácsot (#1440).** A program tízmásodpercenként ránéz a látott mappákra, hogy
  a máshonnan — például a windowsos Picasa 3-ból vagy egy másik gépről —
  érkezett változások maguktól megjelenjenek. Hálózati meghajtón egy ilyen
  frissítés fél percig is eltarthat, és eddig előfordult, hogy közben elindult
  a következő is: a kettő egyszerre akart írni a program belső nyilvántartásába,
  amiből hibaüzenet lett a képernyő alján. Mostantól egyszerre csak egy
  frissítés fut, a közben esedékessé váló mappák pedig sorra kerülnek utána —
  egyetlen mappa sem marad ki. Ráadásul, ha az ellenőrző kör egy akadó hálózati
  meghajtón elidőzik, az épp kiválasztott mappa frissítése emiatt már nem
  csúszik ki.

## [0.8.94] – 2026-08-25

### Javítva
- **Átnevezéskor és áthelyezéskor a kép mostantól magával viszi az eredeti
  változatát is (#1430).** A program — akárcsak a Picasa — a szerkesztést
  belesüti magába a képfájlba, és a szerkesztés előtti változatot egy külön
  almappában őrzi meg: ez az egyetlen visszaút, ha később mégis meggondolod
  magad („Vissza az eredetihez"). Eddig viszont, ha átnevezted a képet vagy
  másik mappába vitted, ez a megőrzött eredeti a régi helyén maradt: az új
  helyen a Vissza az eredetihez már nem talált semmit, a szerkesztés
  véglegessé vált, a régi mappában pedig ott maradt egy fájl, amiről már
  senki nem tudta, kihez tartozik. Mostantól az eredeti — és a mentésenként
  külön megőrzött korábbi változatok is — a képpel együtt költöznek, mindkét
  mappanév alól (a régebbi Picasa-verziók látható `Originals` mappájából és
  az újabbak rejtett `.picasaoriginals` mappájából egyaránt). Ha a
  költöztetés valamiért nem sikerülne — például mert a célhelyen már van egy
  azonos nevű fájl —, a program **el sem kezdi** a műveletet: a kép a helyén
  marad, és egy üzenet megmondja, mi van útban és mit tegyél. Meglévő fájlt
  sosem ír felül.
- **A rács mostantól magától észreveszi a többi mappában történt
  változást is (#1435).** Eddig a program csak azt a mappát olvasta újra
  rendszeresen, amelyiket épp kiválasztottál — pedig a rácson egyszerre
  több mappa képei látszanak. Ha egy másik, ugyanúgy látszó mappába új kép
  került, vagy onnan törlődött egy, az csak jóval később, a program
  ötpercenkénti nagytakarításakor jelent meg. Ez főleg akkor zavaró, ha a
  képek hálózati meghajtón vannak, és egy másik program — például a
  windowsos Picasa 3 — is írja őket: onnan a rendszer nem küld értesítést
  a változásról. Mostantól a program a rácson látszó többi mappát is
  figyeli, körbeforgó rendszerben, mappánként mindössze két apró
  kérdéssel, hogy a hálózati meghajtót ne terhelje.

  Egy eset továbbra sem oldódik meg magától: ha egy **nem kiválasztott**
  mappában egy meglévő kép tartalma cserélődik ki — a fájl neve marad,
  csak a tartalma más —, azt a program még nem veszi észre, mert a mappán
  kívülről semmilyen jel nem látszik ilyenkor. A kiválasztott mappában ez
  az eset is frissül, ahogy eddig.
- **A „Mappa rendezésének alapja ▸ Dátum" végre a mappa KÉPEIT rendezi
  (#1436).** A menüpont eddig nem azt csinálta, amit a neve ígért: nem a
  mappa tartalmát rendezte, hanem azt, hogy a mappák milyen sorrendben
  következzenek egymás után a rácsban — a mappán belüli képsorrend minden
  beállításnál a fájlnevet követte. Mostantól a menü három tétele (Dátum ·
  Név · Méret) a mappa képeit rendezi, **növekvő** sorrendben: dátumnál a
  legrégebbi kép áll elöl és a legújabb a végén, ahogy az eredeti Picasa 3
  is teszi. A „Fordított sorrend" ezt megfordítja, és a választás a
  következő indításkor is megmarad. A dátum a fénykép felvételi ideje
  (EXIF); ha egy képnek nincs ilyen adata, a fájl dátuma dönt. A MAPPÁK
  egymáshoz viszonyított sorrendje továbbra is két külön helyről állítható:
  a rácsé a Nézet ▸ Mappanézet, a bal hasábé a saját jobbklikk-menüje —
  ezekhez a mappa-menü többé nem nyúl.

## [0.8.93] – 2026-08-25

### Javítva
- **A törlés Ctrl+Delete-je mostantól a fotónézőben is működik (#1418).**
  Az eredeti Picasában a lemezről törlés két billentyűn él: a menüsávban
  puszta `Delete`, a jobbklikk-menükben `Ctrl+Delete`. A bélyegkép-rácsban
  ez már korábban is így volt bekötve, a fotónézőben (a kép teljes
  képernyős megnyitásakor) viszont a `Ctrl+Delete` eddig egyáltalán nem
  reagált — csak a jobbklikk-menüből, egérrel lehetett törölni. A
  jobbklikk-menü felirata is a régi, elavult billentyűt (puszta `Delete`)
  mutatta; mostantól `Ctrl+Delete`-et hirdet, és valóban erre reagál.
  A nézőben a puszta `Delete` **többé nem töröl** — az a menüsáv
  billentyűje, a jobbklikk-menüké a `Ctrl+Delete`.
- **A „Visszaállítás" megtalálja a régi, 2009 előtti eredetiket is (#1425).**
  A Picasa a szerkesztés előtti eredetit két különböző nevű mappába mentette:
  a 2009 utáni verziók a rejtett `.picasaoriginals`-ba, a régebbiek a látható
  `Originals`-ba. Eddig csak az újabb nevet ismertük, így a 2005 és 2009
  között szerkesztett képeknél a „Visszaállítás" menütétel szürke maradt —
  minden magyarázat nélkül —, pedig az érintetlen eredeti ott volt a lemezen.
  Mostantól mindkét mappát megnézzük, és ha valamiért egyikben sincs meg a
  kép eredetije, a program érthető magyar mondatban megmondja, hol keresett
  és mikor működik egyáltalán a Visszaállítás. Ha ugyanahhoz a képhez
  mindkét mappában van példány, a régebbi, `Originals`-beli nyer: az az
  időben korábbi, tehát az áll közelebb az érintetlen eredetihez. A mentés
  ezentúl nem készít második „eredetit" sem, ha a régi mappában már van egy.

### Belső
- **A fókuszt kérő tesztek megerősítik, hogy a fókusz tényleg átment
  (#1423).** A `forceActiveFocus()` némán nem csinál semmit, ha a cél
  vezérlő épp nem látható — az így írt teszt zölden fut úgy, hogy semmit
  nem mér. A tesztkészlet mind a hét ilyen hívása át lett mérve: az öt
  billentyűzetes rács-teszt közös, megerősítő segédre került
  (`support/qml_focus.fokuszt_ad`), ami elbukik, ha a fókusz nem ért célba;
  a maradék kettő a verziócímke billentyűzet-elérhetőségét méri, ott a
  helyszínen kimondott állítás a helyénvaló — az egyikük most kapta meg. A
  felhasználó számára a program viselkedése változatlan.

## [0.8.92] – 2026-08-25

### Javítva
- **A hisztogram felirata Windowson sem csonkul (#1344).** A „Hisztogram és
  fényképezőgép-adatok" a windowsos alapbetűvel nem fért a panel sávjába, és
  a vége levágódott volna. A felirat rövidebb lett („Hisztogram és
  fényképadatok"), és ha egy fordítás mégis hosszabb, a betű zsugorodik
  levágás helyett.

## [0.8.90] – 2026-08-25

### Hozzáadva
- **Az `Enter` megnyitja a kijelölt képet a nézőben (#1417).** Eddig csak
  dupla kattintással lehetett megnyitni egy képet a bélyegkép-rácsból, így
  aki billentyűzetről dolgozik, a nyilakkal odaléphetett a képre, de nem
  tudta megnyitni. Mostantól az `Enter` ugyanazt teszi, mint a dupla
  kattintás — pontosan úgy, ahogy az eredeti Picasában, ahol ez a jobbklikk-
  menü félkövér, alapértelmezett tétele. A keresőmezőben, a névbeviteli
  mezőkben és a párbeszédekben az `Enter` változatlanul a saját dolgát végzi.

### Javítva
- **A felső eszközsáv és a keresőmező az eredeti Picasa méretét kapta
  (#587).** A sáv magassága 34 helyett 35 képpont, az „Importálás" gomb
  100 × 24 helyett 111 × 22, a keresőmező pedig 300 × 24 helyett
  388 × 30 — pontosan úgy, ahogy a Picasa saját elrendezés-forrásfájljai
  megadják. A kereső ezzel érezhetően nagyobb és könnyebben eltalálható
  lett. Szűk ablakban a mező ugyanúgy zsugorodik, mint eddig, csak
  nagyobbról indul.

### Javítva
- **A Mappakezelő OK gombja egyszerre, kötött sorrendben ment (#1334).**
  Eddig minden apró változtatás azonnal, külön-külön került lemezre: három
  mappa átállítása háromszor írta újra a figyelt mappák listáját, és az
  arcfelismerésből kihagyott mappák fájlja akkor is íródott, amikor semmi
  nem változott rajta. Mostantól az OK egyetlen mentést végez, pontosan
  abban a sorrendben, ahogy az eredeti Picasa: előbb a figyelt mappák,
  aztán az eltávolított mappák megjelölése, majd — csak ha tényleg
  változott — az arcfelismerésből kihagyott mappák listája, végül a nézet
  frissítése. A program így kevesebbet ír a lemezre, és egy félbeszakadt
  mentés sem hagyhat kevert állapotot a beállításfájlokban.

### Javítva
- **A képre írt felirat mostantól a valódi Picasa formátumában mentődik
  (#371).** Eddig a PicasaPy a saját, rögtönzött alakjában írta a feliratot
  a `.picasa.ini` fájlba — a Windowsos Picasa ezt félreolvasta volna, mert
  nála ugyanazokon a helyeken a felirat hossz-adatai állnak. A formátum
  időközben megfejtődött (859 valódi `.picasa.ini` elemzéséből), és a
  program mostantól pontosan azt írja: a felirat helyét, méretét,
  elforgatását, betűtípusát, valamint a kitöltés és a körvonal színét.
  A színek ezzel meg is maradnak: legközelebbi megnyitáskor visszaállnak,
  nem esnek vissza fehérre és feketére.
- **Többsoros és pontosvesszőt tartalmazó felirat sem sérül (#371).** A
  sortörést a Picasa olyan jelöléssel tárolja, ami maga is pontosvesszőre
  végződik — a régi beolvasónk ezen elvágta a szöveget. Az új beolvasó a
  felirat hosszát használja, így a több bekezdéses és a pontosvesszős
  felirat is hiánytalanul tér vissza.
- **A valódi Picasával készült, több feliratblokkos képek nem csonkulnak
  (#371).** Ha egy képen a Picasa két külön feliratot helyezett el, a
  PicasaPy eddig egyetlen, összekevert szövegként látta. Mostantól
  mindkettőt felismeri, és ha az elsőt átírjuk, a második változatlanul
  megmarad a fájlban. A korábbi PicasaPy-verziókkal mentett feliratok
  továbbra is beolvashatók, és a következő mentéskor átállnak az új
  alakra.

## [0.8.88] – 2026-08-25

### Javítva
- **Az alsó műveletsáv nem lóghat ki az ablakból (#1367).** Amióta a
  műveletgombok az eredeti fix méretét kapták, nem zsugorodnak tovább — egy
  nagyon keskenyre húzott ablakban a jobb szélső gomb kicsúszott a látható
  területről. Az ablak mostantól nem húzható keskenyebbre, mint amennyi a
  sávnak kell.

### Javítva
- **A rácsos kollázsaink újra szerkeszthetők az eredeti Picasában
  (#1036).** A kollázs mentésekor keletkező projektfájlba témánként MÁS
  méretadat tartozik, és a Mozaik, a Képkockamozaik és a Rács témánál
  eddig rosszat írtunk bele — helyenként a valódi érték másfélszeresét.
  A Picasa 3 az ilyen fájltól szerkesztéskor szétesik: óriási,
  felnagyított töredékeket rajzol. A tulajdonos tizenkét eredeti
  kollázsán kimért szabály szerint a rácsos témák a cella szélességét
  írják oda, a Képkupac pedig a csempe befoglaló négyzetét — mostantól
  mindegyik a sajátját kapja. A kollázs kinézetén ez nem változtat: a
  javított mező csak a projektfájl visszaolvasásakor számít.
  A Képkupac ugyanezt a mezőt eddig is helyesen írta; a mérés ezt is
  megerősítette.

### Belső
- **A kiadás nem vár kézi indításra a verzióemelés beolvadása után
  (#1338).** A verzióemelő összefésülést a GitHub szándékosan nem
  tekinti olyan eseménynek, amire munkafolyamatot indítana, így a
  `pyproject.toml` verziója felment, a Releases hasáb viszont nem
  követte: 2026-08-24-én a nap tizennégy kiadását kézzel kellett
  elindítani. Mostantól a verzióemelő PR megnyitásakor elindul egy
  utókövető, ami a beolvadás pillanatában elindítja a kiadót — a
  késleltetés másodpercek, nem fél nap. A negyedórás kiadási őr és a
  napi őrfutás változatlanul a háló mögötte, és az utókövető maga soha
  nem hoz létre kiadást: csak akkor indít, ha a `main` verziójához még
  nincs.
- **A windowsos tesztkörünk újra megbízhatóan jelez (#1381).** Két teszt
  minden ellenőrzési körben pirosan állt a windowsos ágon — nem hiba miatt,
  hanem mert egy linuxos szokást vártak el ott is. Emiatt egy valódi, új
  windowsos hiba beleveszett volna a zajba: kézzel kellett szétválogatni,
  melyik piros az örökölt. A takarítófunkció maga helyesen működött; a
  tesztek mondják ki mostantól, melyik rendszert mérik, és így mindkét
  ellenőrzésen ugyanazt vizsgálják.

## [0.8.86] – 2026-08-24

### Javítva
- **Három szűrő végre úgy viselkedik a képeken, ahogy az eredeti Picasában
  (#1142).** Az eredeti programmal készült képeket összehasonlítva kiderült,
  hogy három szerkesztés fordítva működött nálunk. (1) Az „Elhomályosítás"
  hatását eddig egyszerűen kihagytuk; mostantól lefut, és a képünk az
  eredeti Picasáéval a tömörítési zaj szintjéig egyezik. (2) A színezés
  akkor is működik már, ha a színkód a szokásosnál hosszabb: eddig az ilyen
  képeken a színezés teljesen elmaradt, most — az eredetihez hasonlóan — a
  színkód eleje számít. (3) A „Kockásítás fókuszban" viszont eddig fölösleg
  volt: az eredeti Picasa nem futtatja, ezért mi sem futtatjuk többé — a kép
  változatlan marad, és a szerkesztő meg is mondja, miért.
- **A mentett kollázs-projektfájlból már nem hiányzik három azonosító
  (#1092).** Az eredeti Picasa minden kollázsába beleírja, hogy melyik
  albumból készült (`albumUID`), mikori az az album (`albumDate`), és
  képenként egy azonosítót is elhelyez benne — nálunk mindhárom
  hiányzott. Mostantól kikerülnek a fájlba: az album azonosítója és
  dátuma a képek közös forrásmappájából (a dátum a mappáé, ahogy a
  program nyilvántartja — kézi felülírással együtt —, „2023. november"
  alakban, a felület nyelvén), a képazonosítók pedig a képek
  útvonalából, kiszámíthatóan: ugyanaz a kép mindig ugyanazt kapja. Egy
  Picasával készült kollázs újramentése a fájlban talált eredeti
  azonosítókat változatlanul viszi tovább.
- **Az Indexkép kollázs fejlécében megjelenik az album dátuma (#1092).**
  Az eredeti Picasa a miniatűrök fölé a „9 kép, 2023. november" sort
  írja; nálunk eddig csak a darabszám látszott, ha a kollázs nem
  Picasával készült fájlból nyílt. Most a saját indexképeink is
  hordozzák a dátumot. Ismeretlen dátumú mappánál a régi, csak
  darabszámos alak marad — lógó vessző nélkül.

## [0.8.83] – 2026-08-24

### Hozzáadva
- **A befejezetlen kollázs (piszkozat) végre külön állapot (#1072).** Ha a
  kollázs lapját a „Piszkozat mentése” gombbal zárja be, a Kollázsok
  albumban megjelenő, „PISZKOZAT” feliratú kép mostantól tudja is magáról,
  hogy félkész:
  - a kép megnyitva egy **„Létrehozás”** gomb jelenik meg fölötte — ezzel
    fejezhető be a kollázs, ugyanazon a néven, teljes felbontásban
    (készítés közben a gomb „Folyamatban...” feliratra vált);
  - a **„Kollázs szerkesztése”** gomb a piszkozaton is működik, tehát
    befejezés nélkül is vissza lehet térni a szerkesztéshez;
  - a piszkozat **nem nyomtatható és nem küldhető el e-mailben**; a
    kísérletre az eredeti Picasa magyarázata jelenik meg: a kollázst előbb
    be kell fejezni, de utána is bármikor módosítható.

### Javítva
- **A kollázson a kijelölés gyűrűje az egérmutatót követi (#1000).** Eddig a
  gyűrű a kijelöléstől kezdve folyamatosan a képen ült, és eltakarta azt.
  Mostantól úgy viselkedik, mint az eredeti Picasában: akkor úszik elő, ha
  az egérmutató a képre — vagy a szélétől számított 12 képponton belülre —
  ér, a mutató távozása után még fél másodpercig látszik, majd lassan
  elhalványul. Kép mozgatása, forgatása vagy méretezése közben végig
  látható marad, akkor is, ha a mutató kifut a képből.

### Belső
- **A jegycímek leíróak maradnak (#1378).** Prioritás, állapot,
  commit-előtag és nagybetűs nyomaték nem kerülhet a jegy címébe — arra
  címke van —, és a cím nevezze meg az érintett funkciót, hogy később
  kereshető legyen. Egy őr be is tartatja.

## [0.8.82] – 2026-08-24

### Hozzáadva
- **Lebegő értesítősáv a képernyő jobb szélén (#1129).** A Picasa 3 a
  háttérműveletek végét egy kis, önálló ablakban villantja fel a képernyő
  szélén — nálunk ez a felület eddig egyáltalán nem létezett, a
  háttérműveletek némán futottak le. Mostantól megvan a sáv: a főablaktól
  független, mindig a többi ablak fölött marad, tálcagombot nem foglal, és
  a tálcát tiszteletben tartva a jobb alsó sarok fölé áll be. Egy-egy
  értesítés a saját sorával jelenik meg, a hosszú felirat — az eredetihez
  hasonlóan — elvágódik, nem tördel. Az értesítésre kattintva a program
  odavisz, ahol az eredmény van; van záró gomb is, és néhány másodperc
  után magától eltűnik. Ma két esemény szólal meg benne: az importálás
  befejeződése és hibája, valamint az asztali háttérképnek készült kollázs
  elkészülte (ez utóbbi eddig csak kattintásra tűnt el).

### Belső
- **A platformfüggő tesztek kimondják, melyik platformot mérik (#1217).** A
  program három különböző módon kérdezte meg, milyen rendszeren fut, és a
  tesztek egy része a rendszer globális beállítását írta át — ami átszivárgott
  a többi tesztre, és korábban okozott is elszabaduló hibát. Mostantól egyetlen
  egységes fogantyú van, a tesztek azt cserélik, és a windowsos ágakat a linuxos
  gép is végigméri (eddig ott egyáltalán nem futottak). A viselkedés a
  felhasználó felé változatlan; a cél, hogy a Windows-hibák a fejlesztés közben
  derüljenek ki, ne nála.

## [0.8.81] – 2026-08-24

### Javítva
- **A képfolyam nem ugrik meg a kattintás pillanatában (#1335).** Ha a
  nézet a görgethető tartományon kívülre került (például egy mappára
  ugrás vagy egy billentyűs lépés után), a rács eddig csak a következő
  egérlenyomásra rendeződött vissza a helyére — a kattintás így a közben
  elcsúszott képre esett, a húzásból pedig néma, üres kijelölés lett.
  Mostantól a nézet mindig a görgethető tartományban marad.

## [0.8.80] – 2026-08-24

### Javítva
- **A hisztogram-panel felirata Windowson sem vágódik le (#1344).** A magyar
  „Hisztogram és fényképezőgép-adatok" felirat a windowsos alapbetűvel nem
  fért a 213 képpontos sávba, és a végét levágta volna. Mostantól a betű
  zsugorodik, ahol nem fér el — ahol elfér, ott semmi nem változik.

## [0.8.78] – 2026-08-24

### Javítva
- **A „Hisztogram és fényképezőgép-adatok" felirat és a panel elrendezése
  (#1344).** A felirat már nem félkövér és nem törik két sorba: az eredeti
  Picasához hasonlóan egyetlen, normál vastagságú sor. A panel elemei — a
  felirat, a hisztogram és a két fényképezőgép-adat oszlop — a kimért
  helyükre kerültek, így az oszlopok nem csúsznak el, és a panel mérete a
  szöveg mennyiségétől függetlenül állandó.

### Változott
- **A PicasaPy többé nem írja át a fotók dátumát mentéskor (#1320).** Eddig
  minden szerkesztés (csillag, felirat, effekt, arcok…) után a képfájl
  módosítási dátuma is „mostani"-ra változott, hogy a párhuzamosan futó
  eredeti Picasa észrevegye a változást. Kiderült, hogy erre nincs szükség:
  a Picasa a `.picasa.ini` fájl saját dátumát figyeli, ami a mentéstől
  amúgy is frissül. A fotók dátuma mostantól érintetlen marad, tehát a
  dátum szerinti rendezés és a mentőprogramok nem zavarodnak össze. Aki a
  régi viselkedést akarja, a `PICASAPY_TOUCH_PHOTO_MTIME=1` környezeti
  változóval visszakapcsolhatja — ilyenkor a napló ki is írja, hány fájlt
  érintett.

### Belső
- **Helyben legfeljebb két tesztfutás mehet egyszerre (#1360).** A harmadik
  megvárja, amíg felszabadul egy hely, ahelyett hogy a négymagos gépet
  térdre kényszerítené — a túlterhelésből eddig valódi hiba nélküli
  „ingadozó" bukások lettek. A CI-t nem érinti.

### Javítva
- **Az alsó műveletsor gombjai egyforma méretűek lettek (#1345).** A
  Nyomtatás, E-mail, Exportálás, Megosztás, Kollázs és Film gomb eddig hat
  különböző méretben állt egymás mellett; mostantól mindegyik pontosan
  55 × 36 képpont, egyenlő közökkel — ahogy az eredeti Picasában. A
  feliratuk az ikon alá került, ezért szűk ablakban sem tűnik el többé, és
  a gombok az eredeti sorrendjében állnak. A csoportok között megjelent az
  eredeti elválasztó vonal is.

### Belső
- **A megszakadt tesztfutások maradéka magától eltűnik (#1358).** A futás
  életjelet hagy a saját ideiglenes könyvtárában, így a halott kör maradéka
  azonnal takarítható, nem csak három óra után — és a takarítás minden
  munkamenet indulásakor lefut, nem csak tesztfuttatáskor. Élő futás
  könyvtárához továbbra sem nyúl senki.
- **„SAJÁT FUNKCIÓ" jelölés a nem eredeti Picasa-funkciókra (#1187).**
  Módszertani szabály és kereshető jegyzék
  (`docs/decisions/vedett-sajat-funkciok.md`) azokra a funkciókra, amelyek
  tudatosan eltérnek az eredeti Picasától (pl. a szerkesztő 7 effekt-füle
  az eredeti 5 helyett) — hogy egy későbbi kutatási/hibakeresési kör ne
  minősítse ezeket hibának. Ellenőrző szkript:
  `scripts/check_protected_features.py`. Felhasználói viselkedés nem
  változott.

## [0.8.77] – 2026-08-24

### Hozzáadva
- **A kollázs négy hiányzó viselkedése (#1168).** Üres vásznon a piszkozat
  mentése már nem tűnik el némán, hanem szól, és a lap nyitva marad; az
  asztali háttérkép beállítása előtt a formátum-figyelmeztetés a hivatalos
  szöveggel és a záró kérdéssel jelenik meg; a kollázs rajzolása alatt az
  alsó sáv kiírja, hogy várni kell rá; és a kész háttérkép-értesítésnek
  végre van fogadója.

## [0.8.76] – 2026-08-24

### Javítva
- **A Shift+nyíl az eredeti Picasa szerint bővíti a kijelölést (#892, #1222).**
  Eddig irányváltásnál zsugorított (Intéző-féle tartomány); mostantól
  egyesével bővít, és a másik irányba is bővít, ahogy az eredeti. Az egérrel
  húzott Shift-tartomány változatlan — az a két útvonal szándékosan más.

## [0.8.75] – 2026-08-24

### Javítva
- **A polaroid keret már nem nagyít 29%-ot a képen (#1144).** Az árnyék
  elmosását a kép méretének százalékaként számoltuk, holott az eredeti fix
  képpontértéket használ — emiatt a kimenet 960×640-es képnél 1053×1185 lett
  a helyes 818×950 helyett.

### Belső
- **A CHANGELOG-őr nem engedhet át némán (#1340).** Ha a változást nem tudja
  megmérni (hibás vagy elérhetetlen commit), az nem zöld út többé, hanem
  látható hiba — a sikertelen mérésből korábban „nincs mit ellenőrizni" lett.

## [0.8.74] – 2026-08-24

### Új
- **Megvan az „Exportálás mappába" párbeszéd felülete (#1138).** A képek
  mappába mentésének párbeszédablaka az eredeti Picasa elrendezését követi.

### Belső
- **Kiadás nem mehet ki hamis jegyzettel (#1340).** A felhasználót érintő
  változáshoz mostantól kötelező CHANGELOG-bejegyzés (a CI ellenőrzi), a
  tartalékjegyzet pedig nem állíthatja többé, hogy „nincs látható változás":
  ha nincs emberi összefoglaló, ezt mondja ki, és felsorolja a beolvadt
  munkákat.
- **A CHANGELOG-őr a kötelező ellenőrzésbe került (#1340).** Az első
  változata a lint jobban futott, ami az automatikus beolvasztást nem
  állítja meg — így nem lett volna foga. A verzióemelő automatika saját
  PR-jét viszont nem fogja meg: ott csak a verziósor változik.

## [0.8.73] – 2026-08-24

### Javítva
- **A kivágásnál a kijelölésen kívüli terület helyesen sötétedik el (#900).**
  A kijelölő keret körüli rész az eredeti Picasával azonos sötétítést kap
  (#2F2F2F, 56%-os fedés), így a kivágandó rész tisztán elválik a
  környezetétől.

## [0.8.72] – 2026-08-24

### Új
- **A rácson húzott kijelölőkeret (lasszó) úgy viselkedik, mint az eredetiben
  (#897).** A keret a húzás kezdetén „lefényképezi" a meglévő kijelölést, és
  ahhoz viszonyít: ha visszahúzod a keretet, nem ragad benne kép, Ctrl-lel
  tartva pedig hozzáad a meglévő kijelöléshez. Egérrel Shiftet tartva a
  horgonytól tartományt jelöl ki. Egy már kijelölt képre kattintva a kijelölés
  nem esik szét, így több képet egyben lehet elhúzni. A cellahatáron pontosan
  végighúzott keret sem marad üresen.

## [0.8.71] – 2026-08-24

### Javítva
- **A letiltott gombok végre letiltottnak látszanak (#893).** Az éppen nem
  használható gomb — a zöld, kiemelt gombokat is beleértve — a feliratával
  együtt negyed erősséggel jelenik meg, ahogy az eredeti Picasában. Eddig a
  zöld gombok letiltva is teljes erővel világítottak, a halványítás pedig
  csak a gomb hátterét érintette, a feliratát nem.

## [0.8.70] – 2026-08-24

### Javítva
- **A hisztogrampanel visszakerült a bal fiók aljára (#1323).** A #864
  megvalósítása a képterület fölé, a fotó bal alsó sarkába tette. Az
  eredetiben a panel a fiókon BELÜL dokkolt, és a fiókkal együtt csúszik ki,
  ha a felhasználó összecsukja azt.
- **A radiális telítettség zónája kör lett, nem ellipszis (#859).** Nem
  négyzetes fotón — vagyis gyakorlatilag mindegyiken — a hatás alakja eddig
  eltért az eredetitől: 4:3-nál a vízszintes tengelyen 1,33-szorosan nyúlt.
  A sugarat mostantól ugyanaz a segédfüggvény adja, mint a radiális
  elmosásét, ahogy az eredetiben is. *(A vignetta szándékosan változatlan
  maradt: nyolc eredeti Picasa-exporton végzett mérés szerint annak a zónája
  valóban ellipszis.)*

### Hozzáadva
- **A verziószám kattintható (#706).** A jobb felső sarokban lévő verzió
  mostantól hivatkozás a kiadások oldalára, buboréksúgóval és billentyűzetes
  eléréssel — egy kattintással megnézhető, van-e újabb változat és mi
  változott benne.

### Belső
- **A kiadási folyamat önjavító lett (#1319).** Az automatika csak akkor emel
  verziót, ha az utolsó kiadás óta a program maga változott — dokumentáció-,
  teszt- vagy munkafolyamat-változás önmagában nem szül többé verzióemelő
  PR-t. Az új kiadási őr negyedóránként elrendezi a félbemaradt automatikus
  PR-eket: elindítja a rajtuk elmaradó ellenőrzést, lezárja az elavultakat,
  és hibánál látható jegyet nyit.
- **A kiadási őr a fölösleges verzióemelő PR-t is felismeri (#1324).** Nem
  csak azt zárja le, amit a main lehagyott, hanem azt is, amihez nincs
  kiadandó változás — élesben ez egy olyan 0.8.70-es kiadást előzött volna
  meg, amiben a felhasználó számára semmi nem változott.

## [0.8.69] – 2026-08-24

### Javítva
- **A Névtelen arcok nézete ismét a valódi arcfelismerési vezérlőt használja
  (#1236).** Megszűnt az önmagára mutató QML-kötési hurok, amely miatt a panel
  vezérlő nélkül, látszólag működően, de ténylegesen tétlenül nyílhatott meg.

## [0.8.68] – 2026-08-24

### Javítva
- **A hisztogram ugyanazzal az algoritmussal rajzol, mint az eredeti Picasa
  (#864).** A csatornák magassága már a mintavett képpontok átlagához
  igazodik, a fedések pedig összeadó színkeveréssel készülnek, így a három
  csatorna közös területe a helyes, átlátszatlan sötétszürke. A 256 × 70-es
  belső kép a Picasa 213 × 59-es nézetébe skálázódik, a teljes
  hisztogram- és fényképezőgép-adatpanel pedig az eredeti 238 × 144-es,
  lebegő elrendezést követi.

## [0.8.67] – 2026-08-24

### Javítva
- **A kollázsképek mozgatása többé nem változik át észrevétlen cserévé
  (#990).** A kijelölt kép gyűrűjének húzása most mindig szabad mozgatás,
  míg a kép testéről induló, 10 képpontnál hosszabb vonszolás külön
  cseregesztus. A Ctrl-kattintás csak a kijelölést billenti, ezért nem tud
  véletlenül két képet felcserélni; a korábban másik kártya fölött
  „visszaugró” kép pedig ott marad, ahová a felhasználó húzta.

## [0.8.63] – 2026-08-23

### Javítva
- **Lezárult a kollázs-mentés összeomlásának ügye (#988).** A korábbi
  magyarázat szerint a hiba magában a programban volt: a kollázs
  háttérmunkája és a memória-takarítás akadt volna össze. **A mérés ezt
  megcáfolta** — a mentés 96 egymást követő futásban hibátlan maradt
  akkor is, amikor a takarítást szándékosan a lehető legsűrűbben
  kényszerítettük ki. A tényleges ok a tesztek oldalán volt, és az már
  javítva. Új őr-teszt vigyáz rá, hogy a program oldala ne romolhasson el
  észrevétlenül.

## [0.8.64] – 2026-08-24

### Javítva
- **A főág ellenőrzése nem borul fel többé a kollázs-teszteknél
  (#988).** Az összeomlás (`exit -11`) egy versenyhelyzetből jött: a
  teszt beágyazott várakozása közben a főszál szemétgyűjtést futtatott,
  miközben a kollázs háttérszála épp Qt-jelzést adott át. A védekezés
  eddig egyetlen tesztfájlba volt bemásolva, ezért amint az elhallgatott,
  a testvérfájl kezdett elszállni — ma kétszer is. A védekezés mostantól
  KÖZÖS, és mindhárom érintett fájl azt használja.

## [0.8.62] – 2026-08-23

### Javítva
- **Megszűnt egy ingatag teszt az arc-beolvasás haladásánál (#1233).**
  A teszt időzítéstől függően bukott (húsz futásból egy), mert a
  százalékot a kibocsátás UTÁN olvasta vissza — mire mintát vett, az
  érték már a következő állapoton állt. A termék viselkedése változatlan:
  a hiba a mérésben volt. A hamis riasztás azért káros, mert elveszi az
  időt a valódi hibáktól, és rászoktat az „újrafuttatom" reflexre.

## [0.8.65] – 2026-08-24

### Javítva
- **Egyetlen magyar szó a képarányra: „méretarány" (#982).** A kollázs
  formátum-menüje „méretarány"-t mondott, a vágópanel „képarány"-t —
  ugyanarra a fogalomra. A Picasa saját magyar honosítási táblája dönt:
  ott mind a négy vonatkozó felirat „méretarány" (és ugyanaz az
  `AspectRatioList` lista szolgálja ki a vágóeszközt és a kollázst is),
  tehát a „képarány" a mi saját szóalkotásunk volt. A vágópanel feliratai
  mostantól a hivatalos alakot használják.

## [0.8.66] – 2026-08-24

### Javítva
- **A Fotótálca Kollázs gombja feliratos és van súgója (#1116).** Eddig
  csak ikon volt, felirat és buboréksúgó nélkül — miközben a mellette
  álló Nyomtatás/Exportálás gombunk feliratos, az eredetiben pedig a
  kollázs-gombnak is van felirata („Kollázs") és súgója („Készítsen
  fotókollázst a kijelölt képekből"). Mindkét szöveg a Picasa saját
  honosítási táblájából való, nem új fordítás. A felirat csak akkor jön
  elő, ha bizonyíthatóan elfér: az alap 1280 képpontos ablakban a gomb
  ikon-only marad, a többi felirat viszont ott is megmarad.
- **A tálca szélesség-küszöbe a valós helyigényt tükrözi (#1116).**
  A felirat-független elemek költségvetése alábecsült volt (900 helyett
  1008 a mért érték), így a küszöb elvben nem garantálta, amit ígért —
  1280 képpontnál csak azért nem lógott ki semmi, mert az ablak
  történetesen szélesebb volt a küszöbnél. Újramérve és kerekítve.
- **A fölös paraméterű szűrő-bejegyzést már a megjelenítés is elejti
  (#910).** Az eredeti Picasa az olyan lánc-tagot, amelynek több
  paramétere van, mint amennyit a szűrő ismer (pl.
  `autobacklight=1,0.900000;` vagy `grain2=1,0.500000;` — mindkettőnek
  nulla csúszkája van), némán eldobja. Nálunk eddig csak a MENTÉS
  utasította vissza az ilyet, a megjelenítés viszont lefuttatta — vagyis
  ugyanabból a `.picasa.ini`-ből más képet láttál nálunk, mint a
  Picasában, miközben a mentett fájl végig helyes volt. Mostantól a két
  irány ugyanazt a szabályt követi. Az ismeretlen nevű szűrő útja
  változatlan (a round-trip elv nem sérül), a záró üres mező
  (`grain=1,;`) továbbra is tolerált.

## [0.8.61] – 2026-08-23

### Javítva
- **Az export „Minimális" képminősége 65, nem 70 (#1139).** Az eredeti
  Picasa minőség-legördülőjének három fix fokozata a binárisból pontosan
  kiolvasható; a „Minimális" ága 65-öt állít be, nálunk viszont eddig 70
  szerepelt — vagyis minden „Minimális" beállítással készült exportunk
  eltért az eredetitől. A „Normál" (85) és a „Maximális" változatlan: az
  utóbbi nálunk szándékosan 100 az eredeti 193 helyett, mert a JPEG-kódoló
  minden 100 fölötti értéket ugyanarra a legjobb minőségű kvantálótáblára
  visz — a kettő kimenete azonos.
## [0.8.59] – 2026-08-23

### Javítva
- **A Picasával készült kollázs album-adatai túlélik az újramentést
  (#1274).** A 12 valódi Picasa-mintánk MINDEGYIKÉBEN van `albumUID` és
  `albumDate`; nálunk eddig sem az olvasás, sem a visszaírás nem ismerte
  őket, tehát egy megnyitott és újramentett kollázs elvesztette mindkettőt.
  Mostantól változatlanul mennek vissza. Kitalálni nem találjuk ki őket:
  ami nincs a fájlban, az üres marad.

## [0.8.58] – 2026-08-23

### Javítva
- **A verzióemelő PR nem marad némán jóváhagyásra várva (#1204).** A
  GitHub a bot által nyitott PR-en szándékosan nem indít ellenőrzést, és
  ez eddig jelzés nélkül történt — egyszer a tulajdonos vette észre az
  ottfelejtett PR-t. Mostantól a kiadási automatika élesíti rajta az
  automatikus beolvasztást (a jóváhagyás után magától befejeződik), és
  figyelmeztetést ír a futáslistába és a futás összefoglalójába.

## [0.8.57] – 2026-08-23

### Javítva
- **A látott mappába kívülről bekerülő kép ~10 másodpercen belül
  megjelenik (#1275).** Eddig csak az azonnali fájlfigyelés jelzett, az
  viszont hálózati meghajtón (NAS) gyakran egyáltalán nem küld eseményt —
  ott a következő teljes újraolvasásig, akár 5 percig semmi nem történt.
  Az eredeti Picasa sem eseményt figyel, hanem újraolvas és összehasonlít
  (a bináris a fájlfigyelő API-kat nem is importálja), ezért mostantól az
  **éppen nézett** mappát rendszeresen újraolvassuk. Csak azt az egy mappát:
  a teljes gyűjtemény sűrű pásztázása hálózaton valódi terhelést jelentene.

## [0.8.56] – 2026-08-23

### Javítva
- **A Releases hasábra soha nem megy ki gépi PR-lista.** Ha egy
  verzióhoz nincs CHANGELOG-szakasz (a verzióemelő lánc körönként egy
  kiadást csinál, de a szakaszt az első emelés elviszi), mostantól egy
  őszinte, magyar egymondatos jegyzet megy ki a bot-PR-címek helyett.
  Három kiadás (0.8.53–0.8.55) ment ki így, és utólag javítva lett.

## [0.8.52] – 2026-08-23

### Javítva
- **Az újranyitott kollázs keret-választója is a projektből jön (#1274).**
  A képek kerete eddig is visszajött, a panelé nem — ezért a polaroidos
  kollázs újranyitva „nincs keret"-et mutatott, és a következő felvett kép
  keret nélkül került be. Vegyes keretnél a választó szándékosan a helyén
  marad: egy értéket mutatni ott azt hazudná, hogy a kollázs egységes.
- **Az újranyitott kollázs megtartja a saját képarányát és térközét
  (#1272, #1274).** Eddig a *legutóbb használt* lapformátum ült rá a
  megnyitott projektre — a tulajdonos szava: „mindig az utolsó használt
  képarányt erőlteti rá a korábbi szerkesztésére". A formátum és a térköz
  mostantól a projektfájlból jön vissza, ahogy a téma, a tájolás és a
  háttér is. Ismeretlen formátumnévnél a panel beállítása marad: idegen
  fájl nem teheti használhatatlanná a szerkesztőt.

## [0.8.51] – 2026-08-23

### Javítva
- **Nem keletkezik újabb duplikált „Kollázsok" mappa (#1131).** A Picasa
  gyári mappáinak neve maga is honosított — más nyelvű telepítés más
  mappát hoz létre, a régit nem költözteti át. Mostantól, ha a képmappában
  már van (bármely nyelvű) Kollázsok-mappa, abba mentünk; újat csak akkor
  nyitunk, ha egyik sem létezik. A meglévő mappákhoz nem nyúlunk.

## [0.8.50] – 2026-08-23

### Javítva
- **A szűrőnevek írásmódja mostantól számít (#1141).** Az eredeti Picasa
  kis-nagybetű-érzékenyen olvassa a szerkesztési láncot: a `Tint`, `TINT`
  vagy `Sepia` alak nála nem fut le, csak a kanonikus `tint`, `sepia`,
  `Vignette`. Nálunk eddig lefutott, ezért hat mérőképen látványosan
  eltért a kimenet az eredetitől. A fájl tartalmát ez nem érinti: a
  `.picasa.ini` bájtra ugyanaz marad.

## [0.8.49] – 2026-08-22

### Belső
- **A platformfüggő ágak mind helyettesíthetők (#1217).** Egyetlen napon
  négy jegy bukott ugyanazon a mintán (#1076, #1182, #1206, #1167): a teszt
  hallgatólagosan a fejlesztői gépet feltételezte, és a windows-lábon a
  HELYES natív viselkedésen bukott el. Mostantól minden platform-elágazás
  modulszintű fogantyún (`_platform()`) vagy nevesített `platform=`
  paraméteren megy át, és őr-teszt tartja így.

### Javítva
- **Többszörös exponálás: az újraszerkesztés fekete lapot adott (#1248).** A
  mentett `.cxf` nem sorolta fel a forrásképeket, ezért az újranyitott
  kollázs üres volt, és a mentés azt jelentette, hogy „az összes képet
  eltávolították". Az eredeti Picasa képenként egy, teljes lapos
  csomópontot ír (mérve az `AI7.cxf` mintán) — mostantól mi is.
  ⚠️ A korábban mentett, csomópont nélküli kollázsok nem állíthatók
  helyre: nincs bennük információ a forrásképekről.

## [0.8.48] – 2026-08-22

### Javítva
- **Az „Eltávolítás a Picasából…" almappán is működik, és a mappa nem jön
  vissza (#1249).** A menü eddig almappára némán semmit nem csinált; és
  ami eltűnt, azt a következő újraolvasás visszahozta. Mostantól az
  eredeti „sírkő" jelölés akadályozza meg a visszatérést, az újra
  felvett mappa pedig feloldja. A megerősítő kérdés a mappa nevével és
  az eredeti „Mappa eltávolítása" gombbal jelenik meg.

### Új
- **Az első indítás panelje az eredeti Picasát követi (#1167).** Ha a gépen
  korábbi Picasa-telepítés van, a migrációs kérdés jelenik meg („Frissíti a
  meglévő képtárat…"), és a frissítés a meglévő Picasa-átvételt nyitja; a
  kérdés az eredeti kétlépcsős rendje szerint vált át a keresési választásra.
  A „teljes gép" választás a csatolt köteteket veszi fel (Windowson a
  meghajtókat). Minden szöveg az eredeti Picasa hivatalos magyar
  fordításával jelenik meg.

## [0.8.46] – 2026-08-22

### Javítva
- **A kiadási folyamat percek helyett másodpercek alatt zöldül (#1127).**
  A verzióemelő és a csak CI-konfigurációt érintő változásokra többé nem fut
  le a teljes tesztkészlet — a változatlan kód újratesztelése ~10 percet
  rabolt minden kiadási körből. A védelem nem gyengült: a gyorsút ellenőrzi,
  hogy a változás tényleg csak verzió-fájlokat érint.

## [0.8.45] – 2026-08-22

*(Csak a kiadási folyamat továbbjavítása — felhasználói változás nincs.)*

## [0.8.44] – 2026-08-22

*(Csak kiadási-folyamat változás — felhasználói változás nincs.)*

## [0.8.43] – 2026-08-22

### Új
- **Az exportálás az eredeti Picasa teljes működését követi (#1166).** A
  felirat és a címkék átkerülnek az exportált mappa `.picasa.ini`-jébe; a
  már létező célmappára rákérdez, és igen esetén az előző kimenetet
  eltávolítja; mind a tíz eredeti hibaüzenet megvan; a filmekhez választható
  az „Első képkocka" vagy a „Teljes film" mód.
- **A lasszó (gumikeretes kijelölés) végre használható (#1148).** Üres
  területről indul (telített rácson is), metszés alapján válogat, a Shift
  hozzáfűz, a Ctrl pedig a húzás kezdetéhez képest vált — a keret
  visszahúzása visszavon.

### Javítva
- **A „Keresés egyszer" nem utasít el némán (#1213).** Az eltűnt vagy
  elérhetetlen mappára jelzés érkezik; a már figyelt mappa kérése csendes
  marad, mert azt a folyamatos figyelés úgyis lefedi.
- **Nincs többé SyntaxWarning induláskor (#1242)** — és új őr vigyázza,
  hogy ne is jöhessen vissza.

## [0.8.42] – 2026-08-22

### Javítva
- **A kék állapotsáv több kijelölt képnél a kijelölés darabszámát és
  összméretét mutatja (#1189)** — az eredeti Picasa formátumában.
- **A bal hasáb követi a nézett mappát (#1183).** A rácsban másik mappa
  képére lépve a mappafa kijelölése is átvált, ahogy az eredetiben.
- **A törölt kép bélyegképe nem marad a rácson (#1181).** A futó
  háttér-szinkron alatt kért frissítések eddig némán elvesztek.
- **A kollázs véglegesítése után eltűnik a „PISZKOZAT" felirat a
  bélyegképről (#1186).** A bélyegkép mostantól követi a fájl változását —
  ez minden külső felülírásra igaz, nem csak a kollázsra.
- **Nincs többé induláskori Shortcut-figyelmeztetés Windowson (#1205).**

## [0.8.41] – 2026-08-22

### Új
- **Home / End / PageUp / PageDown a rácsban (#1147)** — mind a nyolc
  eredeti kombináció, a Shift+End a mappa végéig jelöl ki.

### Javítva
- **A kijelölés nem lép át mappahatáron (#1219).** A nyilak, a
  Shift+kattintás és a Shift+nyíl is a mappán belül marad — az eredetiben
  ez szerkezeti szabály, most nálunk is az.
- **A lábléc ikonjai nem nyúlnak meg (#1188).**
- **Két konzol-figyelmeztetés megszűnt (#1185)** — a fájlművelet-ablakok
  kötési hurka és a „null image" üzenet.

## [0.8.40] – 2026-08-22

### Javítva
- **Az „Összes kijelölése" és a „Kijelölés megfordítása" csak a nézett
  mappára hat (#1145)** — eddig a teljes könyvtárat jelölte ki, ami nagy
  gyűjteménynél majdnem lefagyasztotta a programot.

## [0.8.39] – 2026-08-22

### Javítva
- **A Mappakezelő fájában Windowson megjelennek a meghajtók (#1206).**

## [0.8.38] – 2026-08-22

### Javítva
- **A figyelt mappa elutasítása nem néma (#1207).** Ha egy mappa nem
  vehető fel, a program megmondja, miért.

## [0.8.37] – 2026-08-22

### Javítva
- **A „Keresés a lemezen" Windowson a helyes fájlra ugrik (#1152).**

## [0.8.36] – 2026-08-22

### Javítva
- **Windowson a rendszer Lomtárába törlünk (#1182)** — nem egy rejtett
  mappába, ahonnan a Lomtár nem mutatta a törölt képeket.

## [0.8.35] – 2026-08-22

### Javítva
- **A Mappakezelő fája kinyitható, és minden soron van állapot-ikon
  (#1200).**

## [0.8.34] – 2026-08-21

### Dokumentáció
- A Mappakezelő sor-rajzolásának normatív leírása és éles összevetése
  (#1200).

## [0.8.33] – 2026-08-21

### Dokumentáció
- **Lezárult a `.tre` felületleíró nyelv nyolc ritka tulajdonságának
  bináris kutatása (#905).** A specifikáció most setter- és runtime-szinten
  dokumentálja többek között a `windrag`, `vertslider`, `alphatest` és
  `multiply` működését, a bizonyított tényeket különválasztva a végső
  látványra vonatkozó feltételezésektől.

## [0.8.32] – 2026-08-21

### Új
- **A Mappakezelő az eredeti Picasa működését követi (#1161).** A változtatások
  csak az OK gombbal lépnek életbe, a Mégse és az Esc elveti őket. A fa több
  rendszer- és csatolási gyökeret, valamint rejtett mappákat is mutat; az
  egyszeri keresés, a kizárás és a folyamatos figyelés öröklődő állapotai a
  Picasa-kompatibilis `scanlist.txt` fájlban maradnak meg.

### Javítva
- **A Mappakezelő meghajtógyökere Windowson is helyesen azonosítható (#1161).**
  A fa és a figyelt mappák most ugyanazt a kanonikus útvonalat használják,
  ezért a meghajtó már nem látszik tévesen eltávolítottnak.

## [0.8.31] – 2026-08-21

### Javítva
- **A Duo-Tone színei az eredeti Picasa mátrixláncával készülnek (#966).**
  A két tónusszín most a megfelelő fekete-fehér köztes képre kerül, így a
  színes forrás nem torzítja el az eredményt.

## [0.8.29] – 2026-08-21

### Javítva
- **A Picasa felületi erőforrásai helyes színekkel csomagolhatók ki
  (#1160).** A respack BGRA képpontjait korábban RGBA-ként írtuk PNG-be,
  ezért a piros és a kék csatorna felcserélődött. A nyers oda-vissza út
  továbbra is bájthű marad, a kapcsolódó színspecifikációk pedig javítva
  lettek.
- **A szkenner kihagyja a Picasa és a rendszer saját mappáit (#1169).** A
  `thumbs` és `RECYCLER` mappák mellett külön, komponenshatáros
  útvonal-előtag szűrés védi a Linux gyorsítótár-, lomtár- és
  rendszermappáit anélkül, hogy azonos nevű fotómappákat rejtene el.
- **Az átlagszín bitre kompatibilis a Picasával (#1171).** A számítás most
  csonkol, mind a négy csatornát `0xAARRGGBB` alakban tárolja, és a 2×2-nél
  kisebb képeket a Picasa `0` sentinelével jelöli.

## [0.8.28] – 2026-08-21

*(Ide írjuk a felhasználónak szóló mondatokat a jegy PR-jében. A címet a
kiadáskor a `scripts/auto_bump.py` cseréli a verzióra és a dátumra — a
szöveget EMBER írja, mert abból tudja meg a felhasználó, mi változott.)*

## [0.8.27] – 2026-08-20

### Javítva
- **A PISZKOZAT-kép nem marad ott a kész kollázs mellett (#1125).** Ha a
  piszkozatot bezártad, majd később újranyitottad és létrehoztad belőle a
  kollázst, a program ÚJ fájlt írt (`Kollázs1.jpg`), a PISZKOZAT-képet
  pedig ottfelejtette — ezért látszott a listában továbbra is a felirat.
  Mostantól a kész kollázs a helykitöltő helyére lép, ugyanazon a néven.
  ⚠️ A Kollázsok mappába tett **saját képeidhez** nem nyúlunk.
- **A rács vastagsága végre hat a vászonra (#1121).** A beállítás eddig
  eltárolódott, de a kép nem rajzolódott újra, ezért a csúszka húzogatása
  nem csinált semmit.
- **A „Keresés a lemezen…" Windowson és macOS-en is működik (#1104).**
  Eddig linuxos parancsot hívott, tehát máshol egyszerűen nem történt
  semmi — és ez nem csak a kollázst érintette, hanem a fájl- és
  mappa-menüt is.
- **A PISZKOZAT-felirat az eredeti szabálya szerint méreteződik (#1102).**
  Álló lapon a felirat a kép szélén levágódik — ez az eredeti Picasa
  viselkedése, nem hiba.

## [0.8.26] – 2026-08-20

### Javítva
- **⚠️ A Picasával készült kollázsaid képei végre betöltődnek (#1096).** A
  Picasa a projektfájlba nem teljes útvonalat ír, hanem egy rövidített
  alakot (`$My Pictures\…`), amit mi szó szerint próbáltunk fájlnévként
  megnyitni — ezért a régi kollázsaidban **egyetlen kép sem jelent meg**,
  és a hiba **néma** volt: csak üres csempéket láttál.

  Mostantól feloldjuk a rövidített alakot a rendszer szerinti képmappára,
  és mentéskor mi is ezt írjuk — így a fájljaink akkor is jók maradnak, ha
  a képmappád máshova kerül. A hálózati (`$UNC`) alakot felismerjük, de nem
  bontjuk fel: ott látható helykitöltő csempe jelenik meg üres hely helyett.

  A kollázs **háttérképe** ugyanezen a leképezésen megy át, tehát az eredeti
  Picasa fájljain sem esik vissza sima színre.

## [0.8.25] – 2026-08-20

### Belső
- A kollázs háttérmunkája nem ír megosztott állapotot és nem küld jelzést a
  saját szálán: minden a fogadó szálra került, sorba állított kapcsolaton
  át (#988/#999). ⚠️ Ez **nem javítja** a CI-n visszatérő összeomlást — a
  mérés megcáfolta, hogy elég volna —, de három valódi hiányt megszüntet,
  és mindhárom mellett őr-teszt áll.

## [0.8.24] – 2026-08-20

### Javítva
- **⚠️ Windowson végre menthető a kollázs (#1097).** A Kollázsok mappában
  álló, **rejtett** `.picasa.ini`-t nem tudtuk felülírni, ezért minden
  mentés `[Errno 13] Permission denied`-del elbukott. Ráadásul azt írtuk
  ki, hogy *„A kollázs nem készült el"* — holott a kép addigra már a
  lemezen volt. Most a fájl írása a rejtett jelzőt megőrző módon megy, és
  ha mégis gond van vele, az csak figyelmeztetés.
- **A piszkozat háttérképe nem vész el (#1103).** Visszaállításkor a
  program „elfelejtette" a képhátteret és sima színre váltott: a hátteret
  előbb próbáltuk visszatenni, mint ahogy a képek a lapra kerültek, így
  nem találta, melyik kép volt az.
- **Nem hagyunk árva piszkozatot (#1100).** A kész kollázs mellől
  eltakarítjuk a projektfájlt. Enélkül a valódi Picasa elárvult mentésnek
  látta, és egy szürke, `autosave.jpg` nevű helykitöltőt gyártott a
  Kollázsok mappádba.
- **A kollázs a lapon ugyanúgy áll, mint az eredetiben (#1094).** Egy
  korábbi „javítás" a képeket a lapra szorította; a valódi Picasa
  kimenetéből kiderült, hogy az csak a képek KÖZÉPPONTJÁT korlátozza, a
  csempe kilóghat. A hozzátoldás visszavonva.
- **Windowson a natív adatmappákat használjuk (#1076),** és az áthozatal
  nem fut hibára ékezetes felhasználónévnél sem: a másolás nyitva hagyta az
  adatbázis-fájlt, amitől az egész átköltöztetés elbukott volna.
- **A néma hibaüzenetek láthatóak (#1003).**

## [0.8.23] – 2026-08-20

### Hozzáadva
- **A piszkozat végre LÁTSZIK (#1072).** A „Bezárás" gombra a program eddig
  csak a projektfájlt mentette el, képet nem — ezért a friss piszkozat
  **sehol nem jelent meg az indexképek között**, és úgy tűnt, elveszett.
  (Nem veszett el: minden induláskor fel is ajánlotta a visszaállítást.)

  Mostantól a bezárás a kollázs képét is kiírja, **PISZKOZAT** felirattal —
  pontosan úgy, ahogy az eredeti Picasa tette —, és a mappát felveszi az
  indexbe is, hogy a bal hasáb tényleg mutassa. A piszkozatnak egyetlen
  képe van: ha visszaállítod és újra bezárod, ugyanazt írja felül. Amikor
  végül lerendereled a kollázst, a végleges kép a helyére lép.

## [0.8.22] – 2026-08-20

### Javítva
- **⚠️ A kollázsok végre oda kerülnek, ahol a Picasa is keresi őket
  (#1088).** A PicasaPy és a valódi Picasa eddig **két külön mappába**
  dolgozott, ezért nem láttad a PicasaPy-ben a Picasával készült
  kollázsaidat — és fordítva.

  Az ok: a képmappa helyét **kitaláltuk** (a felhasználói mappa +
  „Pictures"), ahelyett hogy megkérdeztük volna a rendszertől. Windowson
  viszont **a rendszer dönti el, melyik a képmappa** — és az a döntés
  követi az átirányítást (nálad OneDrive-ra) és a saját beállításodat is.

  Mostantól a program ugyanazt kérdezi meg, amit az eredeti Picasa:
  a rendszertől kéri el a képmappát.

  ⚠️ **Ha korábban készítettél kollázst a PicasaPy-vel**, azok a régi
  helyen maradtak (`…\Pictures\Picasa\Kollázsok`). A program ezentúl az
  új helyre ír; a régieket kézzel tudod átmásolni, ha kellenek.

## [0.8.21] – 2026-08-20

### Javítva
- **A színezés (Tint) végre az eredeti receptjét követi (#872).** A hat
  lépéséből három hiányzott vagy rosszul működött: a szinthúzás, a
  telítettségfüggő gamma és a színmegtartás („Color Preserve") súlyozása.

  A csúszka mostantól ugyanazt a képet adja, mint az eredeti Picasa —
  különösen az erős színezéseknél és a magas színmegtartás mellett látszik
  a különbség.

  *(A javítás a párhuzamosan dolgozó fejlesztői kör munkája; a kiadásba itt
  került be.)*
- **A piszkozat visszatöltése nem felejti el a hátteret (#1085).** Ha
  képhátteret állítottál be, majd piszkozatként mentetted és később
  visszatöltötted, a háttér **sima színre váltott vissza**. A visszatöltés
  mindent visszahozott — témát, tájolást, árnyékot, képfeliratot, címet —,
  **csak a hátteret nem**, pedig a projektfájl tárolja.

  Ha a háttérként használt kép időközben kikerült a kollázsból, a háttér a
  **beállított színre** esik vissza: üres képhátteret mutatni rosszabb
  volna, és törött hivatkozást nem hagyunk.

### Fejlesztői
- ⚠️ A `test_collage_controller_943.py` várakozó segédje a várakozás
  idejére kikapcsolja a szemétgyűjtőt (#988). **Ez nem a hiba javítása** —
  a veremkiíratás szerint a főszál szemétgyűjtése és a háttérszál
  Qt-jelzése ütközik; a valódi javítás a worker Qt-natívvá tétele, ami
  külön körben fut. Ez addig annyit tesz, hogy a főág CI-je ne legyen
  piros, és a kiadások ne akadjanak el.

## [0.8.20] – 2026-08-20

### Javítva
- **⚠️ A Kollázsok mappa magától visszakerül a Projektek alá (#1075).**
  Ha a Projektek gyűjtemény üres volt, vagy a Kollázsok mappa „eltűnt", a
  program **induláskor magától rendbe teszi** — nem kell hozzá csinálnod
  semmit, csak elindítani.

  Miért kellett: a mappa megjelölését eddig **kizárólag a mentés** végezte,
  tehát visszamenőleg semmi. Két úton lett ebből eltűnt mappa: a **0.8.8
  előtt** készült kollázsok mappájában nincs meg a jelölés, és a frissítés
  nem javította utólag; illetve ha az indexelés egyszer elbukott, a mentés
  némán továbbment, és a mappa **soha többé** nem került be.

  A megjelölés szigorú feltételhez kötött: csak akkor történik meg, ha a
  mappában tényleg a program saját kollázsai vannak (kép + projektfájl
  párban). Egy tetszőleges képmappát soha nem jelöl meg, és a mappában
  található korábbi Picasa-adatot érintetlenül hagyja.

## [0.8.19] – 2026-08-20

### Új
- **„Kollázs szerkesztése" gomb — a kész kollázs újranyitható (#1002).**
  Eddig egy elkészült kollázst nem lehetett tovább szerkeszteni: a kész
  képtől nem vezetett vissza út a panelra.

  Mostantól, ha megnyitod a kollázst a nézőben, a „Vissza a könyvtárhoz"
  mellett megjelenik a **„Kollázs szerkesztése"** gomb. Kattintásra
  visszatölti a projektfájlt a panelra, és a „Létrehozás" **a meglévő
  fájlt írja felül** — ugyanazt a kollázst szerkeszted tovább, nem
  másolatot készítesz.

  A gomb a **projektfájl létéből** látszik, nem abból, hogy „most készült":
  bármikor megnyitod a kollázst, ott lesz.

  Sérült projektfájlnál a program **szól** — nem hiúsul meg némán. A
  megnyitás nem számít módosításnak, tehát a bezárás nem kérdez rá.

## [0.8.18] – 2026-08-20

### Javítva
- **⚠️ A mentett kollázs végre megnyitható a valódi Picasában (#1071).** A
  PicasaPy-vel készített kollázs projektfájlja (`.cxf`) a Picasa 3-ban
  **szerkesztéskor szétesett**: óriási, felnagyított töredékek.

  Az ok: a képek méretét **kimeneti képpontban** írtuk a fájlba, a Picasa
  viszont **lapegységben** olvassa. Az eltérés pontosan a kimeneti
  nagyítás — a szokásos 5120 képpontos lapnál **ötszörös** érték került a
  fájlba.

  Élő mentésen ellenőrizve: a méretek most `337, 337, 337, 337, 303` —
  pontosan azok, amiket az eredeti Picasa írna. Eddig `1685, 1685, …`
  voltak.

  ⚠️ **A korábbi verziókkal mentett `.cxf` fájlok érintettek maradnak** —
  azokat a Picasa továbbra is torzan nyitja meg. A PicasaPy viszont
  helyesen olvassa őket (a méretmezőt nem használja), tehát a kollázs
  itt szerkeszthető és újramenthető.

## [0.8.17] – 2026-08-20

### Javítva
- **Kép hozzáadása és törlése után rendben marad a rács (#996).** A „+"
  gomb az új képet eddig **minden témánál** a Képkupac szórásával tette a
  vászonra — rácsos témánál ettől **kilógott a rácsból**. A „–" gomb pedig
  **lyukat hagyott** a rács közepén.

  Mostantól a rácsos témák újraszámolnak, a Képkupac viszont nem: ott a
  szórás a helyes viselkedés, és az újraszámolás elvenné a kézi
  elrendezésedet. Erre külön ellenőrzés áll — hozzáadáskor és törléskor a
  többi kép **nem mozdul**.

  ⚠️ A **térköz-csúszka** ebből a körből kimaradt: ott az azonnali
  újrarendezés a Mozaiknál csúszkalépésenként fél másodperces keresést
  jelentene, ehhez késleltetés kell. A jegy emiatt nyitva marad.

## [0.8.16] – 2026-08-20

### Javítva
- **Lapformátum- vagy tájolásváltás után újrarendeződik a vászon (#991).**
  Eddig a lap alakja megváltozott, a kártyák viszont a helyükön maradtak:
  kilógtak, összetorlódtak, vagy nagy üres rész maradt. `4:3 → 16:9`
  váltásnál a lap **megrövidül**, és a régi helyükön hagyott kártyák
  kilógtak az aljából.

  ⚠️ A kézi elrendezésed ilyenkor **elveszik** — ez az eredeti Picasa
  viselkedése is (ugyanaz, mint témaváltásnál), és nincs értelme megőrizni:
  a régi helyek a **régi lap alakjához** tartoztak.

  Azonos formátumra vagy tájolásra váltás továbbra sem rendez újra.

## [0.8.15] – 2026-08-20

### Javítva
- **Az „E-Mail" beállításfül végre ment (#1066).** Eddig átállíthattad a
  levelezőprogram-választást és a képméretet, a felület elfogadta — és
  **semmi nem történt**: újranyitásra minden visszaállt.

  Az ok: a beállításokat kezelő rész **soha nem jött létre** a futó
  programban. A felület hivatkozott rá, de egy védőfeltétel mögül, ami
  megakadályozta a hibaüzenetet — és el is rejtette a hiányt.

- **A webexportálás párbeszéde sem volt bekötve (#1066).** Ugyanaz az ok,
  ugyanaz a néma következmény: a sablonlista üresen maradt.

### Fejlesztői
- Új őr: minden felületről hivatkozott vezérlőnek regisztrált párja kell
  legyen. Ez a hibaosztály **néma** — nincs hibaüzenet, nincs kivétel,
  nincs piros teszt, csak egy funkció, ami nem működik. A szándékos
  kivételek **indoklással** szerepelnek, és az elavult kivétel is hiba.

## [0.8.14] – 2026-08-20

### Javítva
- **Windowson és `#`-es fájlnévnél sem marad üres a kollázs csempéje
  (#1019).** A vászon csempéi és a Klipek lap miniatűrjei kézzel fűzött
  fájl-hivatkozást használtak. Windowson ez **érvénytelen hivatkozást** ad
  (a meghajtóbetűt, például a `C:`-t, a rendszer portszámnak nézi), `#`-et
  tartalmazó fájlnévnél pedig **minden rendszeren elvágja a nevet**.

  Mindkét esetben **némán**: nincs hibaüzenet, csak egy üres kép a
  csempe helyén.

  A hivatkozást mostantól a modell adja, a Qt saját szabálya szerint — nem
  a felület találja ki platformonként. Új teszt őrzi, hogy a fában
  **sehol** ne maradjon kézi fűzés.

## [0.8.13] – 2026-08-20

### Javítva
- **Nem ajánlja fel a visszaállíthatatlan piszkozatot (#1064).** Ha a
  piszkozat készítése óta áthelyezted vagy törölted a benne szereplő
  képeket, a program eddig is felajánlotta a visszaállítást — te
  rábólintottál, és csupa üres helykitöltőt kaptál.

  Mostantól csak akkor kérdez, ha **legalább egy kép** megvan. A részleges
  visszaállítás megmarad: a hiányzó képek helykitöltőként jelennek meg, a
  többi munkád viszont visszajön.

  A piszkozatot **nem törli** magától: ha a képek visszakerülnek a helyükre
  (visszacsatolt meghajtó, visszaállított mappa), a felajánlás újra
  előjön.

## [0.8.12] – 2026-08-20

### Javítva
- **A választott háttérkép a mentett kollázson is ott van (#1015).** Eddig
  a „Kép használata" mód a vásznon és a projektfájlban működött, a mentett
  JPEG háttere viszont a beállított **szín** maradt — vagyis a mentett kép
  mást mutatott, mint amit a képernyőn láttál.

  A háttérkép a lapot **kitölti**: arányt tartva nagyít, a túllógó részt
  középről vágja, hogy ne torzuljon — és **tompítva** kerül rá, ugyanúgy,
  ahogy a szerkesztő előnézetében látod. A tompítás mértéke nem becslés: a
  te két kollázsodból mérve pontosan 14,9%. Ha a háttérkép időközben eltűnt
  vagy sérült, a szín marad — egy háttér miatt sosem hiúsulhat meg a
  mentés.

  A szín- és az átlagszín-mód érintetlen.

## [0.8.11] – 2026-08-20

### Javítva
- **A kész kollázst végre megtalálod (#1028).** A létrehozás után eddig a
  lap bezáródott, és ennyi. Mostantól a könyvtár **odaugrik a kész
  képre** (kijelölve), és megjelenik egy **kattintható** üzenet:
  „A kollázs kész (kattintson ide)" — kattintásra nagyban nyílik.

  A szöveg eddig is megvolt a programban, csak a **folyamatjelző sávba**
  írtuk, amit a panel a rá következő pillanatban elrejtett: a helyes
  üzenetet egy villanásra láttad, kattinthatatlanul.

  Nézőt magától nem nyit — az eredeti is csak kijelöl, a nagyban
  megnyitás a te kattintásod.

### Fejlesztői
- **Megvan az „ingadozó" kollázs-teszt gyökéroka (#1018).** A Mozaik
  elrendezés-keresője **időkorlátos**: hány lehetőséget néz meg, az a gép
  pillanatnyi terheltségétől függ. A bájtazonossági őr két külön
  pillanatban futtatta a két ágat, tehát terhelés alatt két KÜLÖNBÖZŐ
  elrendezést hasonlított össze — és „megváltozott a rajz" néven jelentett
  valamit, ami csak a processzorterhelés volt.

  A teszt mostantól lépkedő számlálót ad a keresésnek óra helyett, tehát
  mindig ugyanannyi jelöltet néz meg. Bizonyítva: mesterséges
  hárommagos terhelés alatt **8/8 zöld** (előtte 2/6 bukás). A program
  viselkedése változatlan. Mellékesen a tesztfájl 17 másodpercről 5-re
  gyorsult.

## [0.8.10] – 2026-08-20

### Javítva
- **A Képkupac polaroid csempéi végre egyformák (#1053).** Eddig a polaroid
  keret alakja a fotó oldalarányától függött — egy kollázsban 0,47-től
  1,48-ig terjedő csempék álltak egymás mellett. Az eredeti Picasában a
  polaroid csempe **mindig ugyanolyan alakú** (0,8333), a fotót pedig
  négyzetre vágja, ahogy egy valódi polaroid-kép is négyzetes.

  A keret arányai nálunk is jók voltak (1,145 / 1,374 = 0,8333) — csak
  **rossz alapra** mentek: a fotó saját méretére, nem a csempe négyzetére.
  A tulajdonos két eredeti polaroid kollázsa (18 csempe, két lapformátum,
  több forráskép) mind 0,833-at ad.

  Ez nem szépészeti kérdés: **más alakú csempe más helyre esik.** A mi
  kupacunk ezért lógott ki már 9 képnél is, miközben az eredeti ugyanott
  egyet sem. A biztonsági beszorítás most 9 képből **egyet** mozdít
  három helyett — ugyanannyit, mint keret nélkül.
- **A kupac csempéi egy képponttal nagyobbak voltak a kelleténél (#1059).**
  A méretük a lapszélesség arányából számolt tört értéket **kerekítette**,
  az eredeti viszont **csonkít**. A tulajdonos kollázsainak `scale`
  mezőivel összevetve: kerekítéssel kilencből **egy** érték stimmelt,
  csonkítással **mind a kilenc**. Két külön kollázsfájlon ugyanez.

  Menet közben kiderült, hogy a lap belső szélessége nem „körülbelül 1021",
  ahogy egy korábbi becslés mondta, hanem pontosan **1024** — ezt most
  három mintán mérve tudjuk, nem becsülve.

## [0.8.9] – 2026-08-20

### Javítva
- **A Kollázs lap a szerkesztőből nyitva is látszik (#1055).** Ha a
  szerkesztőből (nézőből) indítottad a kollázst, a lap megnyílt, a kollázs
  el is készült — te viszont közben a **mappanézetet** láttad, a kollázsból
  semmit. A panel a nézőn kívülre van kötve, a nézőt pedig senki nem
  zárta be. Mostantól a kollázs megnyitása elhagyja a nézőt.
- **Visszakapod az automatikusan mentett piszkozatot (#1051).** A program
  eddig is elmentette a félbehagyott kollázst, de **soha nem kínálta
  vissza**: a visszatöltés kódja készen állt, a felület viszont egyetlen
  helyen sem hívta meg. Mostantól induláskor felajánlja.

  Az „Elvetés" **törli** a piszkozatot — ez visszavonhatatlan, ezért az
  `Esc` csak elhalasztja a döntést, és a felajánlás a következő
  indításkor visszatér.

### Fejlesztői
- A tesztek nem írnak többé a valódi `~/Pictures/Picasa/Kollázsok`
  mappába (#1054). Egy fixture odaírt, és a lerakott fájlt utóbb egy
  hibajegy a felhasználó elveszett munkájának nézte. Új, gyökér-szintű őr
  nevezi meg azt a tesztet, amelyik a valódi képmappához nyúl; az őr fogát
  hat teszt állítja.

## [0.8.8] – 2026-08-20

### Javítva
- **A kollázs képei tényleg nem lógnak ki (#1027, #1045).** A 0.8.6
  ugyanezt ígérte, és nem tartotta be: a vágás a **vászonkeretnél**
  történt, nem a **lapnál**, tehát a lapon túlnyúló kép attól még
  látszott. A hozzá tartozó teszt is a rossz követelményt őrizte — az
  zölden állt, miközben a hiba a képernyőn ott volt.

  Most két helyen áll a védelem: a lap **elvágja**, ami túllóg rajta, és a
  Képkupac elrendezése eleve **beszorítja** a csempét a lapra — a
  KERETES mérettel számolva, nem a csupasz fotóéval, tehát a polaroid
  papírszegélye sem lóghat le. 15 képes próbán: 2 kilógó csempéről
  **0**-ra.

  ⚠️ A beszorítás nem semleges: amíg megvan, a Képkupac kissé eltér az
  eredeti Picasáétól. A mélyebb ok — a polaroid csempe méretezése — külön
  jegyen (#1053) fut.
- **A mentett kollázs megjelenik a Projektek alatt (#1046, #1048, #1050).**
  Eddig a mentés után a Projektek gyűjtemény üres maradt. Három dolog
  hiányzott, mind a három megvan: a program most **`.picasa.ini`-t ír** a
  kollázsok mappájába (pontosan olyat, amilyet a valódi Picasa is — se
  többet, se kevesebbet), és a mentett mappát **azonnal beindexeli**, hogy
  ne kelljen újraindítani.
- **A mentés hibája többé nem néma (#1047).** Ha a kollázs mentése
  elszállt, a folyamatjelző eltűnt, és semmi nem történt — a kép nem
  készült el, és erről nem szólt a program. Mostantól megmondja, mi volt a
  baj.
- **Visszakapod az automatikusan mentett piszkozatot (#1051).** A program
  eddig is elmentette a félbehagyott kollázst, de **soha nem kínálta
  vissza**: a visszatöltés kódja készen állt, a felület viszont egyetlen
  helyen sem hívta meg. Mostantól induláskor felajánlja. Az „Elvetés"
  törli a piszkozatot, az `Esc` viszont csak elhalasztja a döntést.

### Fejlesztői
- A tesztek nem írnak többé a valódi `~/Pictures/Picasa/Kollázsok`
  mappába (#1054). Egy fixture hónapokig odaírt — a lerakott fájlt utóbb
  egy hibajegy a felhasználó elveszett munkájának nézte. Új őr nevezi meg
  azt a tesztet, amelyik a valódi képmappához nyúl.

## [0.8.7] – 2026-08-19

### Javítva
- **A mentett kollázs ugyanúgy dől, ahogy a vásznon látod (#1035).** Eddig a
  program a képeket a mentéskor az **ellenkező irányba** forgatta: amit ferdén
  balra dőlve raktál össze, az jobbra dőlve mentődött. A Képkupac legyezőszerű
  dőlése így tükrözve került a kész képre.

  A javítás a rajzolóban van — a projektfájl (`.cxf`) érintetlen maradt, tehát
  a kollázsok továbbra is visszanyithatók az eredeti Picasában. Ellenőrizve:
  mind a nyolc mintafájl bájtra azonosan jár körbe a javítás után is.

## [0.8.6] – 2026-08-19

### Javítva
- **Nem szaggatott többé a kollázs-csempék széle (#1016).** A legzavaróbb a fehér
  keret **belső** éle volt, ahol a fotó a kerettel találkozik — az a csempe
  legnagyobb kontrasztú éle. Mérve, valódi kijelzőn: azon az élen **nulla**
  átmeneti árnyalat volt, most **819**. A keret nélküli csempe külső éle:
  0 → 516.
- **A képek nem lógnak ki a keretből (#1027).** Az elmozgatott csempék eddig
  a vászon fölé, a gombsorra folytak. Mostantól a vászon szélén elvágódnak —
  a négy lebegő gombcsoport viszont sértetlen marad.
- **Kollázs-módban eltűnik a felső eszközsáv és az alsó tálcasáv (#1026).**
  Nem elrejtve: a **könyvtár teljes panelje** adja át a helyét a kollázsnak,
  ahogy az eredetiben is.

  **Ezért a vászon jóval nagyobb lett**: 1280 × 800-as ablakban a lap
  708 × 531-ről **849 × 637**-re nőtt — **+20% él, +44% terület**.

## [0.8.5] – 2026-08-19

### Javítva
- **A Projektek gyűjtemény nem üres többé (#1029).** A bal hasábon a Projektek
  alatt eddig **semmi** nem jelent meg. A projekt-mappákat (Kollázsok, Filmek,
  Mozgófilmek, Rögzített videoklipek) a `.picasa.ini` jelöli meg — ezt a jelölést
  eddig nem olvastuk. A gyűjtemény mostantól nyitva is indul: csukva a javítás
  után is üresnek látszott volna.

  A megoldás a meglévő indexen **azonnal** működik: nem kellett hozzá új
  adatbázis-oszlop, ami csak teljes újraindexelés után töltődött volna fel.
- **Látszik a vetett árnyék az élő vásznon is (#1021).** A 0.8.4-ben az árnyék
  csak a **mentett** képre került rá, a szerkesztés közben nem — a jelölőnégyzet
  kapcsolgatása nem csinált semmit. Mostantól a vásznon is megjelenik, a mentett
  képpel egyező geometriával.

  A megoldás szándékosan **nem** grafikus gyorsítót használ: az ahhoz szükséges
  Qt-modul a fejlesztői gépen nincs telepítve, a tesztgépen viszont igen — így
  a teszt zöld lett volna, a felhasználó pedig továbbra sem lát árnyékot.

## [0.8.4] – 2026-08-19

### Hozzáadva
- **Megjelent a kollázs vetett árnyéka (#977).** Az „Árnyékok rajzolása"
  jelölőnégyzetet eddig be lehetett kapcsolni, a projektfájlba is bekerült —
  **hatása viszont nem volt**, mert árnyék-rajzolás egyáltalán nem létezett.

  Az árnyék **elrendezésenként más**, ahogy az eredetiben is: a Képkupac, a
  Mozaik és a Képkockamozaik 40%-os, a Rács és az Indexkép 60%-os árnyékot
  kap, a Többszörös exponálásnak pedig nincs. Az eltolás és a lágyság is
  elrendezésenként külön képlet szerint áll be.

  A számokat a felhasználó nyolc, eredeti Picasával készített kollázsa
  igazolta: a rekonstruált képek árnyéka a mintáktól átlagosan **0,5–2,3
  árnyalattal** tér el (a 255-ből), a látható árnyékhossz 51 helyett 50
  képpont.

  ⚠️ Egyelőre **csak a mentett képen** látszik; az élő vásznon még nem (#1021).

## [0.8.3] – 2026-08-19

### Javítva
- **A „Kép használata" háttérmód tényleg választ képet (#1009).** Eddig a mód
  bekapcsolása után az előnézet üres maradt, mert képet csak a kijelölésből
  lehetett beállítani. Mostantól a módváltás magától a kollázs első képét
  választja, a kijelölés pedig felülírja.

  ⚠️ Menet közben kiderült, hogy a kép **Windowson soha nem jelent volna meg**,
  ékezetes mappa nélkül sem: a program kézzel fűzött össze egy fájlcímet, amiben
  a meghajtóbetűt a rendszer portszámnak nézte, így a cím érvénytelen lett — és
  a kép némán, hibaüzenet nélkül elmaradt. (Ugyanez a hiba `#` jelet tartalmazó
  fájlnévnél Linuxon is jelentkezett volna. Két további helyen még javítandó:
  #1019.)
- **Nem szaggatottak a keretélek a kollázs-előnézetben (#1010).** A megdöntött
  képek kerete lépcsősen rajzolódott ki. Mérve: egy 5 fokkal elforgatott élen
  nulla átmeneti árnyalat volt, most 466. A mentett képet ez sosem érintette,
  csak az előnézetet.

## [0.8.2] – 2026-08-19

### Javítva
- **A „Megjelenítés és szerkesztés" tényleg megnyitja a szerkesztőt (#1001).**
  A Kollázs-panelen a gomb, a képre adott duplakattintás és a helyi menü
  megfelelő tétele eddig **semmit nem csinált** — a parancs elindult, de nem
  volt, aki fogadja. Mostantól mindhárom megnyitja a kijelölt képet a
  szerkesztőben, és a kollázs lapja közben nyitva marad.

  Menet közben két másik, rejtett akadály is előkerült: a képtálcáról indított
  keresés egy nem létező függvényt hívott, a kijelölés körüli gyűrű pedig
  elnyelte a duplakattintást, így az soha nem jutott el a képig.

### Hozzáadva
- **Őr a néma parancsok ellen (#1003).** Egy új ellenőrzés minden változtatásnál
  megnézi, hogy a program belső üzeneteinek van-e fogadója. Ez a hibafajta —
  amikor egy gomb vagy egy hibaüzenet szó nélkül elvész — egyetlen napon
  háromszor jutott ki kiadásba, mert a tesztek és az átnézés sem fogták meg.
  Mostantól **új** ilyen nem keletkezhet észrevétlenül; a 26 meglévő eset
  dokumentált listán van, ami csak rövidülhet.

## [0.8.1] – 2026-08-19

### Javítva
- **Az elrendezés-választó végre hat a vásznon (#989).** A Kollázs-panelen
  eddig a hat elrendezés közül bármelyiket választottad, a vászon ugyanazt a
  szórt kupacot mutatta — a hat valódi elrendező megvolt a programban, de a
  panel nem használta őket. Mostantól a Képkupac, a Mozaik, a
  Képkockamozaik, a Rács, az Indexkép és a Többszörös exponálás tényleg
  másképp rendezi a képeket, és a mentett kép is az új elrendezést mutatja.

  *(A 0.8.0 kiadási jegyzete ezt már ígérte — tévesen. A hibát a felhasználó
  vette észre az első próbán.)*
- **A magyar gombfeliratok nem lógnak ki és nem csúsznak egymásra (#992).**
  A gombok mérete az angol feliratokra készült, a hosszabb magyar szöveg
  pedig kifolyt rájuk: az „Az összes kijelölés megszüntetése" 182 képpontot
  foglalt egy 100 képpontos gombban, és rátakarta a szomszédját. Ezért nem
  lehetett megtalálni a „Véletlenszerű kollázs" gombot sem. A feliratok
  mostantól tördelnek — teljes betűmérettel, olvashatóan.

## [0.8.0] – 2026-08-19

### Hozzáadva
- **Elkészült a Képkollázs-panel — a kollázs mostantól saját LAP, élő
  vászonnal (#920).** A Létrehozás ▸ Képkollázs megnyit egy külön lapot a
  „Könyvtár" mellett. Ott elrendezést és keretet válthatsz, **megfoghatod és
  elhúzhatod a képeket**, a kijelöltre kerülő gyűrűvel forgathatod és
  méretezheted, egy képet a másikra ejtve kicserélheted, Alt-tal a tetejére
  emelheted — és **a mentett kép pontosan azt mutatja, amit a vásznon
  látsz**. Eddig egyetlen párbeszédablak volt, ahol a kollázs elrendezésébe
  nem lehetett beleszólni.

  A lapon ott a Beállítások (téma, keretsor, térköz, háttér, oldalformátum,
  tájolás), a Klipek lap a képek hozzáadásához és eltávolításához, a vászon
  körüli gombok (kijelölés, rétegsorrend, forgatás-illesztés, keverés) és a
  három helyi menü. A Könyvtár fülre visszaváltva **a böngészés a helyén
  marad**.

  A mentés fájlválasztó nélkül megy a Képek/Picasa/Kollázsok mappába, a JPEG
  mellé `.cxf` piszkozat készül, így a kollázs később is szerkeszthető
  marad — és a piszkozat **összeomlás után sem vész el**.

  Nyolc lépcsőben épült (#942–#949), a bekötést a #985 zárta le.

### Javítva
- **Nem cserélődik ki két kép egy kattintástól (#947).** A képkupac képei
  fedik egymást, és a kijelölő kattintás eddig némán felcserélte a kurzor
  alatti két képet. A csere mostantól csak valódi elhúzás után történik.

## [0.7.79] – 2026-08-18

### Hozzáadva
- **A kollázs vászna életre kelt (#947).** A képeket most már meg lehet fogni
  és elhúzni, a kijelöltre kerülő gyűrűvel forgatni és méretezni, egy képet a
  másikra ejtve kicserélni, és Alt-tal a tetejére emelni. Húzás közben a szög
  és a méretarány kiíródik.
- **Megjelent a „Beállítások" lap (#946).** Egy helyen a téma-választó, a
  keretsor és a térköz, a háttér (szín, kép, a kijelölt kép, átlagszín), az
  oldalformátum és a tájolás — a keretválasztó pedig csak ott jelenik meg,
  ahol az adott elrendezésnek van értelme.

### Javítva
- **Nem cserélődik ki két kép egy egyszerű kattintástól (#947).** A képkupac
  képei fedik egymást, és a kijelölő kattintás eddig némán felcserélte a
  kurzor alatti két képet. A csere mostantól csak valódi elhúzás után,
  ejtéskor történik — ahogy az eredetiben.

## [0.7.78] – 2026-08-18

### Hozzáadva
- **A kollázs saját LAP lett, nem párbeszédablak (#944).** Megjelent a
  dokumentum-fülsáv: a „Könyvtár" mellett külön fülön él a kollázs, oda-vissza
  lehet váltani, és a könyvtár közben megőrzi a helyét. A lap bezárása
  rákérdez, ha mentetlen módosítás van — piszkozatként mentheted, elvetheted,
  vagy nyitva hagyhatod.

## [0.7.77] – 2026-08-18

### Új
- **A Kollázs-panel váza, a helyes méretezéssel (#945).** A készülő kollázs-lap
  csontváza a helyére került: bal oldalt a beállítás-hasáb a két füllel
  („Beállítások" és „Képek (N)"), alatta a négy gomb — Asztali háttérkép,
  Kollázs létrehozása, Alaphelyzet, Bezárás —, jobbra pedig a vászon a lappal.

  A lényeg az, ami **átméretezéskor** történik: a bal hasáb mérete **állandó**,
  és a négy gomb is ugyanott marad, akármekkorára húzod az ablakot — a
  növekedést mind a vászon kapja meg. A lap a vásznon középen ül, és pontosan
  az oldalformátum arányát tartja. Így viselkedik az eredeti Picasa is; a
  szélesre húzott ablakban a hasáb alatt üres sáv marad, nem nyúlnak szét a
  gombok.

  A hasáb és a vászon tartalma (elrendezés-választó, keretek, háttér, illetve a
  mozgatható képek) a következő lépcsőkben érkezik.

## [0.7.76] – 2026-08-18

### Hozzáadva
- **A kollázs piszkozata már nem vész el (#431).** A Picasa szerkesztés közben
  folyamatosan mentett egy piszkozatot, és összeomlás után felajánlotta a
  visszaállítást — ez eddig nálunk teljesen hiányzott. A mentés **atomi**: ha a
  gép a mentés közben áll meg, a KORÁBBI piszkozat épen marad, és egy sérült
  fájl sem akadályozza meg az indulást. (A piszkozat írásának bekötése a
  kollázs-panelbe: #960.)
- **A kollázs-panel csomópont-modellje és vezérlője (#943).** Felület nélküli
  réteg, amire az élő vásznas panel épül.

### Javítva
- **A Boost, a Lomo és a Cinemascope színei az eredetit adják (#903, #904).**
  A kontraszt eddig egy durva közelítésből jött; valójában a Picasa egy
  **101 elemű, kézzel hangolt táblázatot** használ, és a képet nem a
  középszürke, hanem a **negyedtónus** körül feszíti szét. A csúszka felső
  végén az eltérés **ötszörös** volt. A telítettség szintén más: a pozitív
  oldal **háromszoros** erősítést kap, és Haeberli-súlyokkal számol.

  Ennek látható következménye: a **Boost** erős fokozaton mostantól
  világosít és kiégeti a csúcsfényeket, nem sötétít. Ez elsőre hibának tűnt,
  ezért a binárisból ellenőriztük — az eredeti Picasa is pontosan így
  viselkedik (#964).
- **Nem szemetel a napló a Létrehozás ablakánál (#918).** Minden indításkor
  kétszer beírt egy belső figyelmeztetést, ami elfedte a valódi hibákat; a
  visszajelző ablak szélessége ráadásul kiszámíthatatlan volt hosszabb
  üzeneteknél.

## [0.7.75] – 2026-08-18

### Javítva
- **A Finomhangolás Csúcsfények és Árnyékok csúszkája együtt is pontos (#879).**
  Eddig a kettőt egymás után alkalmaztuk, az eredeti Picasa viszont egyetlen
  számolásba vonja össze őket. Amíg csak az egyik csúszkát mozgattad, ez nem
  látszott — amint **mindkettőt** elmozdítottad, a kép láthatóan másképp jött ki,
  mint a Picasában.

  Ez nem ritka eset: valódi fotógyűjtemények mentett beállításai közt a
  Finomhangolás **minden ötödik** használatánál mindkét csúszka aktív. A régi
  számolás ezeken legfeljebb 17 világossági szintet tévedett, a szélső állásban
  pedig 217-et; mostantól bitre az eredetit adja.

  Ugyanez a mag szolgálja ki a Megvilágítási javítások panelt is, tehát a két
  hely innentől ugyanúgy számol.

### Belső
- **A kollázs rajzolója szétvált elrendezésre és rajzolásra (#942).** Eddig a
  kollázs-készítő minden mentéskor ÚJRA kiszámolta, hova kerülnek a képek. Ez
  most még nem látszott, mert a képeket úgysem lehetett kézzel mozgatni — de
  amint a készülő szerkeszthető vásznon (#920) elhúzol egy képet, a mentés
  visszarántotta volna a gépi helyére. Vagyis mást kaptál volna, mint amit a
  képernyőn látsz.

  Mostantól a program külön lépésben rendezi el a képeket és külön lépésben
  rajzolja ki őket, és a mentés is ugyanazt az egyetlen rajzolót használja,
  mint az előnézet. Ami a vásznon áll, az kerül a képre.

  A ma elkészülő kollázsok **képpontra ugyanúgy néznek ki**, mint eddig: egy
  teszt a régi és az új rajzolót egymás mellett futtatja, és mind a hat
  elrendezésre, mindhárom keretre, két térköz-állásban összeveti a kimenetüket
  — egyetlen képpont eltérés sem maradhat. Új mellékhatás: a **nem található
  kép** többé nem tűnik el némán a kollázsból, hanem áthúzott helykitöltő
  csempeként jelenik meg.

## [0.7.74] – 2026-08-18

### Új
- **Élő előnézet a kollázsnál (#920, első lépcső).** Eddig vakon kellett választani:
  kijelölöd az elrendezést, megadod a célfájlt, és csak a mentés után derült ki, mit
  kaptál. Mostantól a párbeszédben **azonnal látszik a kollázs**, és elrendezést vagy
  keretet váltva rögtön frissül.

  Mellé került a **„Véletlenszerű kollázs"** gomb: ugyanazokból a képekből új
  elrendezést kever. Amit az előnézeten látsz, azt kapod mentéskor is.

  Ez az eredeti Picasa teljes kollázs-lapjának első szelete — a szerkeszthető vászon
  (mozgatás, forgatás, átrendezés) még hátravan.

## [0.7.73] – 2026-08-18

### Javítva
- **A Képkollázs menüpont most már tényleg elindul (#936).** A menüpont aktív volt,
  de a kattintás nyomtalanul elveszett: a menü jelzésének egyszerűen nem volt
  fogadója a programban. A képtálca ikonjáról indítva ugyanez a funkció eddig is
  működött — a menüből nem.

  Az előző javítás (#922) a menüpont *engedélyezését* hozta rendbe, ez pedig azt,
  hogy a kattintás el is jusson valahová.

## [0.7.72] – 2026-08-18

### Javítva
- **A kollázs forgatásának két apró eltérése (#921).** A „270 fokra igazítás" a
  projektfájlba eddig más számot írt, mint az eredeti Picasa — a képen ugyanaz
  látszott, de ugyanazt a kollázst a két programban megnyitva elcsúszott volna.
  A húzás közben kijelzett szög pedig ellenkező előjellel jelent meg.

## [0.7.71] – 2026-08-18

### Javítva
- **A kollázs beállításai követik az elrendezést (#923).** Eddig bármelyik
  beállítás bármelyik elrendezéssel kombinálható volt — pedig az eredeti Picasában
  a **képkeret** csak a Képkupacnál és az Indexképnél választható, a **térköz** pedig
  csak a három rácsos elrendezésnél. A panelen a kettő szó szerint ugyanazt a helyet
  foglalja, tehát sosem látszanak együtt.

  Mostantól a keretválasztó kiszürkül ott, ahol az eredetiben sincs, és a program
  nem alkalmaz olyan beállítást, ami az adott elrendezésnél értelmetlen. Az árnyék
  alapértéke is elrendezésenként eltér, ahogy az eredetiben.

- **Az „Automatikus szín" gomb (#759).** Eddig három, egymástól független
  csatorna-erősítést alkalmazott — az eredeti Picasa viszont egy összetett
  színátalakítást használ, amiben a csatornák hatnak egymásra. Ezért nem lehetett
  a régi megközelítéssel közelebb kerülni, akárhogy hangoltuk.

  Az eltérés az eredeti Picasa kimenetétől **a negyedére csökkent**, és már a
  fájlmentésből származó zaj szintje ALATT van — vagyis a különbség ezen a
  mérőanyagon nem is mérhető tovább. Tizenkét összehasonlító képből tíz javult,
  egy sem romlott.

  Mellékesen megszűnt egy régi hiba is: színöntet nélküli képre a program eddig is
  ráigazított egy keveset, most — az eredetihez hasonlóan — érintetlenül hagyja.

## [0.7.70] – 2026-08-18

### Javítva
- **Az „Automatikus szín" gomb (#759).** Eddig három, egymástól független
  csatorna-erősítést alkalmazott — az eredeti Picasa viszont egy összetett
  színátalakítást használ, amiben a csatornák hatnak egymásra. Ezért nem lehetett
  a régi megközelítéssel közelebb kerülni, akárhogy hangoltuk.

  Az eltérés az eredeti Picasa kimenetétől **a negyedére csökkent**, és már a
  fájlmentésből származó zaj szintje ALATT van — vagyis a különbség ezen a
  mérőanyagon nem is mérhető tovább. Tizenkét összehasonlító képből tíz javult,
  egy sem romlott.

  Mellékesen megszűnt egy régi hiba is: színöntet nélküli képre a program eddig is
  ráigazított egy keveset, most — az eredetihez hasonlóan — érintetlenül hagyja.

## [0.7.69] – 2026-08-18

### Javítva
- **A Képkollázs menüpont nem indult el (#922).** Ha a képeket a képtálcára tetted
  (és nem a rácsban jelölted ki), a *Létrehozás ▸ Képkollázs…* menüpont szürke maradt
  — pedig a funkció hibátlanul működött volna. Ugyanez állt a Mozgófilm tételre is.

  Emellett a párbeszéd mostantól **mindig megnyílik**: ha nincs mit betenni, megmondja,
  hogy előbb képeket kell kijelölni vagy a képtálcára tenni. Eddig a kattintás
  nyomtalanul elnyelődött, ami kívülről úgy nézett ki, mintha a program nem reagálna.

## [0.7.68] – 2026-08-17

### Javítva
- **A Színezés effekt (#884).** Eddig a képet egyetlen egyszínű felületre cserélte —
  a fénykép rajzolata teljesen eltűnt alóla. Mostantól úgy működik, mint az eredeti
  Picasában: a kép világosság-viszonyait pontosan megtartja, és csak a színt cseréli
  le, mint egy színszűrő az objektív előtt.

  Az eltérés az eredeti Picasa kimenetétől a huszonketted részére csökkent, és már a
  fájlmentésből származó zaj szintjén van — vagyis gyakorlatilag képpontra egyezik.
  A halványítás csúszkája végig helyesen működik, a maximumon a kép változatlan marad.

  A helyes eljárás az előző körben (#878, Neon) került elő; ez a javítás azt hasznosítja
  a második helyen is, ahol a Picasa ugyanezt a lépést használja.

## [0.7.67] – 2026-08-17

### Új
- **A képkollázs hat eredeti elrendezése (#431).** Eddig négy, saját tervezésű
  elrendezés közül lehetett választani — mostantól az eredeti Picasa mind a hatja
  elérhető, a saját nevével és sorrendjével: **Képkupac · Mozaik · Képkockamozaik ·
  Rács · Indexkép · Többszörös exponálás**.

  Mellé került a **képkeret** választója is: keret nélkül, fehér szegéllyel, vagy
  Polaroid-kerettel.

  A kollázs eddig is működött, de nem az eredeti elrendezéseivel — a Picasa-hű
  számítások készen álltak, csak nem voltak bekötve a felülethez.

## [0.7.66] – 2026-08-17

### Javítva
- **A kiadás nem maradhat el egy pillanatnyi hálózati hiba miatt (#896).**
  Kiderült, hogy a kiadásokat előállító automatika egyetlen átmeneti GitHub-hibától
  feladta, és a kiadás némán elmaradt — pontosan ez történt az előző, 0.7.65-ös
  verzióval, amit kézzel kellett pótolni. A baj alattomos volt: minden más zöldnek
  látszott, és a következő kiadás visszamenőleg el is fedte volna a hiányt.

  Mostantól az automatika többször újrapróbálkozik, egyre hosszabb szünetekkel, és
  ha végül mégsem sikerül, azt hangosan jelzi ahelyett, hogy csendben elhallgatná.
  Ugyanez a védelem került a telepítőcsomagok feltöltésére is, ahol egy hasonló hiba
  eddig úgy hagyta ki a csomagokat, hogy közben sikeresnek jelentette magát.

  Emellé jött egy **napi őrjárat**: naponta egyszer összeveti a program verzióját a
  közzétett kiadásokkal, és pótolja, ha valamelyik lemaradt. Ez arra az esetre is
  védelem, ha az automatika el sem indulna — amit az újrapróbálkozás önmagában nem
  fogna meg.

## [0.7.65] – 2026-08-17

### Javítva
- **A Neon effekt (#878).** A mérőszett legrosszabb elemje volt: a
  kimenetünknek gyakorlatilag semmi köze nem volt a Picasáéhoz (a szerkezeti
  hasonlóságot mérő SSIM lényegében nulla). Kiderült, hogy a modell rossz
  úton indult — élkeresés helyett egy egészen más eljárást használt, és a
  színezés is a fényes részeket festette be a halványak helyett.

  A javítás után a Neon a Picasa saját, binárisból visszafejtett lépéssorát
  követi: az eltérés az eredetihez képest **huszonnegyedére** csökkent, és a
  kép szerkezete immár egyezik. A halványítás csúszkája végig helyesen
  működik, a maximumon a kép bájtra változatlan marad.

  Mellékeredmény: a Picasa **színező lépése** (amit a Színezés effekt is
  használ) is megfejtésre került — az a kép fényességét pontosan megőrzi, és
  csak a színt cseréli. A Színezés átállítása külön jegyen (#884).

## [0.7.64] – 2026-08-16

### Új
- **A kollázs Picasa-hű magja (#431).** Mind a hat elrendezés (Képkupac,
  Mozaik, Képkockamozaik, Rács, Indexkép-ív, Többszörös exponálás), mind a
  három képkeret, és a **`.cxf` projektfájl** írása-olvasása. Fontos: a
  korábbi négy elrendezés saját tervezésű volt, tehát a kollázsból eddig
  **egy sem** követte az eredetit.

  A képletek helyességét két független dolog igazolja: egy valódi `.cxf`
  kilenc mérete **képpontra pontosan** kijön, és a szétszórt kupac
  dőlésszögei maguktól ugyanabba a tartományba esnek, mint az eredetiben.

  A felületi bekötés még hátravan — a kollázs a menüből egyelőre a régi
  elrendezéseket használja.

## [0.7.63] – 2026-08-16

### Új
- **A három vágás-javaslat gombján mostantól látszik, mit kapsz (#448).**
  Eddig csak a nevük állt ott; most kis előnézeti kép mutatja a javasolt
  kivágást — új képfeldolgozás nélkül, a már betöltött előnézetből.

### Dokumentáció
- **A README elavult tényei javítva.** A verziószám 60 kiadásnyit csúszott
  (0.6.1 állt benne); mostantól a jelvény magától a legfrissebb kiadást
  mutatja. Az „amit még nem tud" lista hétből ötöt tévesen sorolt hiányzóként
  — a retusálás és szöveg, a kollázs/film, a geocímke-térkép és az effekt-fülek
  azóta elkészültek. A jegy-hivatkozások kattinthatók.
- **A szerkesztő 1. füljének gombsorrende véglegesen rögzítve (#464)**, saját
  döntés-lapon. A sorrend a tulajdonos képernyőképe szerinti; a bináris
  `respack.yt` koordinátái betűre ugyanezt adják. Kiderült, hogy a korábbi
  ellentmondás oka az volt, hogy **rossz fájlból** következtettünk: az
  `editpanel.tre` a gombok viselkedését írja le, a helyüket nem.

## [0.7.62] – 2026-08-16

### Javítva
- **A szerkesztő eszköz-paneljei (vágás, retusálás, vörösszem, szöveg) minden
  betűmérettel elférnek (#778, #779).** Két valódi hiba volt: a szöveg-panel
  alsó 10 képpontja **görgetve sem volt elérhető**, a vörösszem-panel
  jelölőnégyzete pedig a saját feliratának szélességét kényszerítette az egész
  panelre — szélesebb betűvel ez 91 képpontos kilógást okozott. Windowson a
  szöveg-panel 23 képponttal lógott ki; ez is javult. A panelek mérete
  mostantól **nem függ a betűkészlettől**.

### Belső
- A felület-ellenőr eddig a **rendezés előtti** állapotot mérte, ezért
  tizenhét nem létező hibát jelentett — és egy valódi javítást is elrontottnak
  mutatott. Javítva; az „ismert hibák" listája kiürült.

## [0.7.61] – 2026-08-16

### Javítva
- **A Picasa felülírása többé nem marad észrevétlen (#750).** Ha a program
  ugyanazt a mappát a Picasával együtt használja, a Picasa a saját
  adatbázisából **egészben** újraírhatja a képhez tartozó bejegyzést, és
  ilyenkor a nálunk végzett szerkesztés eltűnik. Eddig ezt csak a szerkesztőben
  vettük észre; mostantól a csoportos effektnél, az effekt-beillesztésnél és a
  lemezre mentésnél is. Két rejtett hiba is javult közben: a napló írása nem
  volt biztonságos megszakadás ellen, és nagy naplónál minden mappaváltás
  fél másodpercet késett.
- **A szöveg-eszköz vezérlői nem lógnak ki a panelből (#775).** A színpaletta
  egyetlen hosszú sorban rajzolta a nyolc színmezőt, és ez az egész panelt
  szélesebbre feszítette. Mostantól két sorban áll.
- **A menüfeliratok betűre az eredeti Picasa magyar szövegét követik (#757).**
  Tíz feliratnál a gyorsbillentyű rossz betűn állt, kettőnél pedig hiányzott a
  szöveg.

### Belső
- A felület-ellenőr mostantól a **bekapcsolt eszköz-módokat** is méri (vágás,
  retusálás, vörösszem, szöveg) — eddig sosem látta őket, mert alapból
  láthatatlanok. Amit talált, az a #778-on és a #779-en fut.

## [0.7.60] – 2026-08-16

### Javítva
- **A „Jó napom van" (enhance) négyszer pontosabban követi az eredetit
  (#721).** Az eltérés 12 valódi Picasa-képpáron mérve **2,48-ról 0,57-re**
  csökkent; a legrosszabb képen 13,03-ról 0,52-re. Kiderült, hogy az
  `enhance` és az „Automatikus kontraszt" nálunk ugyanaz a művelet volt,
  holott az eredetiben nem: az utóbbi közös tartományra vág (megőrzi a
  színegyensúlyt), az előbbi 30%-kal afelé húz.

### Új
- **Fa-mappanézet a bal panelen (#702).** A mappák hierarchikusan is
  megjeleníthetők, saját helyi menüvel (kinyitás, összecsukás, keresés a
  lemezen, eltávolítás, áthelyezés). A nézetmód-váltó még hiányzik, addig a
  lapos lista az alapállapot.
- **Gyorsbillentyűk a bal hasáb menüiben (#757).** Eddig egyetlen `Alt`-os
  gyorsbillentyű sem volt bennük; most mind az öt menü az eredeti betűivel
  működik. Kilenc felirat is javult az eredeti szövegére, és bekerült két
  hiányzó menütétel.
- **Az „Új album" súgószöveg csak üres albumlistán jelenik meg (#757)** —
  eddig mindig ott volt, és 230 képpontos hasábon 2,6 mappasornyi helyet vett
  el.

## [0.7.59] – 2026-08-16

### Javítva
- **A szerkesztő bal panelje az eredeti méreteivel épül (#741).** A csempék
  sorköze 104 képpont volt a mért **64** helyett — három sor × ~40 képpont,
  amit a panel aljáról vett el, ezért csúszott lejjebb a Derítőfény és a
  gombsor. Most a teljes panel a Picasa saját erőforrás-rétegeiből mért
  geometriát követi: csempe 44 × 30, hét fül hézag nélkül kitöltve, a
  csúszkák, gombok és legördülők az eredeti méretükön. **A felső eszköztár
  a szerkesztőben nem látszik többé** — az eredetiben ott csak a „Vissza a
  könyvtárhoz" van.
- **A PicasaPy-ban végzett szerkesztés eljuthat a párhuzamosan futó
  Picasához (#643).** Kiderült, hogy a Picasa a saját adatbázisát tekinti
  igazságforrásnak, és egy már beolvasott fotót a `.picasa.ini` változása nem
  tesz elavulttá — még újraindítás után sem. Mentés után ezért mostantól
  megérintjük a **képfájl módosítási idejét**; a kép tartalma, mérete és
  jogosultsága változatlan marad. (Kikapcsolható:
  `PICASAPY_TOUCH_PHOTO_MTIME=0`.)
- **Nem írható ki olyan szerkesztési lánc, amit az eredeti Picasa eldobna
  (#643).** A Picasa az első hibás lépésnél megáll, és onnantól a lánc többi
  részét sem hajtja végre. Az új ellenőrzés ezt lehetetlenné teszi — és
  végigmérve mind az 57 effektünket: ma egyik sem ír ilyet.

## [0.7.58] – 2026-08-15

### Javítva
- **A bal hasáb végre görgethető (#730).** Eddig semmi nem görgette: ha ~30-nál
  több névvel ellátott személyed volt, a Mappák-lista magassága **nullára
  esett**, az „Egyebek" fejléc pedig kicsúszott az ablakból — a tartalom
  egyszerűen elérhetetlen lett. Mostantól saját, mindig látszó görgetősávja
  van, ahogy az eredetiben.
- **Az egérgörgő a bal hasáb fölött nem nyit meg véletlen mappát (#731).**
  Eddig bárhol görgettél a hasábon, a rács átugrott egy másik mappára. Most a
  hasáb görög; a mappalista fölött pedig — ahogy az eredetiben — lépteti a
  kijelölést.
- **Négy sor jobbklikkje a saját menüjét adja (#732).** A gyűjtemény-mappa, az
  exportált mappa, a „Névtelenek" és a „Mellőzött emberek" sor eddig a hasáb
  rendezés-menüjét nyitotta a sajátja helyett.
- **A `desat` szerkesztés-kulcsot felismerjük és rendereljük (#711).** Egy régi
  `.picasa.ini`-ben ez eddig ismeretlen volt; a Visszavonás gombon mostantól az
  eredeti Picasa saját felirata jelenik meg („Szűrt FF").

## [0.7.57] – 2026-08-15

### Javítva
- **Végre ott vannak a Visszavonás/Újra gombok, ahol keresed őket (#616).**
  A gombsor eddig a panel legaljára volt szegezve. Nagy képernyőn — ahol a
  panel 832 képpont magas, a fül tartalma viszont csak ~300 — ez azt
  jelentette, hogy a gombok **több száz képponttal a csempék alatt**, egy
  nagy üres szürke mező túloldalán ültek: a gyakorlatban eltűntek. Mostantól
  közvetlenül a fül tartalma alatt vannak, de szűk ablakban sem csúsznak ki a
  képernyőről. (Az eredeti Picasa panelje fix méretű, ezért ott mindig a
  tartalom alatt van a sor — a „panel aljára szegezve" a mi hibánk volt.)
- **A GPU-előnézet telítettsége megegyezik a mentett képpel (#696).** A
  pozitív oldalon eddig eltért az, amit a csúszka húzása közben láttál, attól,
  amit a program mentett — átlagosan 3,5–19,3 szinttel; most 0,8–1,4.

## [0.7.56] – 2026-08-15

### Javítva
- **A szerkesztő effekt-füleiről eltűnt a Visszavonás/Újra gombsor (#703).**
  Két oka volt: a program akkora ablakmagasságot kért, amit egy laptop-kijelző
  ki sem tud adni — **és** a tiltott gombok kitöltése pontosan a panel
  háttérszíne volt, tehát két láthatatlan folt volt ott, ahol a gombokat
  kerested. Mindkettő javítva.
- **Az effekt-csempék az eredetit követik (#704).** Eltűnt a fölösleges
  fejlécsáv (az eredetin nincs ilyen), és megjelent az „alkalmazva" jelvény a
  bélyegkép sarkában. A Vignetta a helyére, az 5. fülre került.
- **A paraméter-panel az eredeti elrendezését követi (#700).** A panel címe
  mostantól az effekt **neve** („Holga-szerű"), nem a belső kulcs; a feliratok
  a csúszka fölött, középen, szám nélkül; a gombsor középen, pipa és X ikonnal.
- **A szerkesztésed nem veszhet el a Picasában (#695).** A szűrő nevét eddig
  kisbetűsen írtuk vissza, amit az eredeti Picasa **szó nélkül eldob** — a
  szerkesztés egyszerűen nem történt meg. Mostantól pontosan abban az
  írásmódban írjuk, amit a Picasa vár.
- **A szerkesztés-védelem Windowson némán hatástalan volt (#699).** A napló
  írása és olvasása másképp képezte a fájl útvonalát, ezért soha nem talált
  egyezést.
- Mind a 43 effekt **nevén** nevezve jelenik meg a Visszavonás gombon (#465) —
  eddig 12-nél a belső kulcs látszott („Visszavonás: crossprocess").
- Négy hiányzó tétel a jobbklikk-menükben, a Picasa saját parancstáblája
  szerint (#422).

### Belső
- Gépi UI-lefedettségi tábla: 2020 elem, 74 panel (#707). Eddig minden
  felületi hiba szemrevételezéssel derült ki; innentől lista mondja meg, hol
  vannak a hiányok.

## [0.7.55] – 2026-08-15

### Javítva
- **A szerkesztés-védelem Windowson némán hatástalan volt.** A napló írása és
  olvasása másképp képezte a fájl útvonalát (perjel kontra visszaperjel),
  ezért soha nem talált egyezést — vagyis a program nem szólt volna, ha egy
  másik program felülírja a szerkesztésedet. Mostantól egyetlen közös
  szabály adja a kulcsot mindkét oldalon.

## [0.7.54] – 2026-08-15

### Javítva
- **A program újra elindul (#699).** A 0.7.53 nem indult el: az
  indítóképernyő végtelen ciklusban maradt, ha volt már saját mentett
  szerkesztésed. **Ha a 0.7.53-at telepítetted, frissíts erre a kiadásra.**
  Elnézést kérünk — a hiba azért juthatott ki, mert az ellenőrzéseink egyike
  sem indította el ténylegesen a programot. Mostantól a kiadás előtti
  ellenőrzés **elindítja**, és megbukik, ha az indulás elszáll.

## [0.7.53] – 2026-08-15

### Javítva
- **Nyolc szűrő eddig némán elveszett (#687).** Ha a képet a Picasában a
  Kontraszt, a Gamma, a Színhőmérséklet, az Árnyék, a Derítőfény vagy az
  Automatikus kontraszt csúszkájával szerkesztetted, nálunk a kép
  **szerkesztetlenül** jelent meg. Mind a nyolc rendereli mostantól, a
  mérőtáblán az eredetitől alig megkülönböztethetően.
- **A telítettség csúszkájának pozitív fele félreszámolt (#693).** Kiderült,
  hogy az eredeti ott nem egyszerű erősítést végez, hanem színárnyalat-függő
  görbét — ezért is „lassul be" a hatás a csúszka vége felé. Az eltérés a
  mérőképen **13,3-ról 0,7 szintre** esett, vagyis a JPEG-tömörítés zajába.
- **A Ghoul Eye effekt nem festi át többé az egész képet (#688).** Szem-régió
  nélkül eddig ΔE 57 mértékben elrontott bármilyen fotót; az eredeti ilyenkor
  nem csinál semmit.
- **A szerkesztő-panel három eleme kilógott a helyéről (#659)** — köztük a
  Derítőfény csúszkája, aminek a fogantyúja a szomszédjaira lógott.

### Belső
- A teljesítmény-őrök viszonyítanak, nem stopperolnak (#660): a korábbi
  abszolút határ a gép terheltségét mérte, és hamis hibát jelzett.
- A tartomány-ellenőrzés az irányított és a sugaras szűrőkre is figyel (#669).

## [0.7.52] – 2026-08-15

### Javítva
- **Egy sérült videó a mappában többé nem omlasztja össze a programot (#673).**
  Eddig elég volt egyetlen hibás videófájl: a bélyegképek készítése közben a
  program hibaüzenet nélkül kilépett. A videók dekódolása mostantól egyetlen,
  megbízható úton történik; ha egy videó tényleg olvashatatlan, egyszerűen
  nem kap bélyegképet — és ezt a napló meg is mondja, nem hallgatja el.

### Belső
- A darabolt tesztfutás nem hagy több gigabájtot az ideiglenes könyvtárban
  (#677). Ez nem a futást bukatta el, hanem a párhuzamosan dolgozó másik
  munkamenetet — némán, félrevezető hibával.

## [0.7.51] – 2026-08-15

### Javítva
- **A Ragyogás és a sugaras elmosás mostantól a Picasa saját motorjával
  dolgozik (#668).** Eddig közelítéssel mostunk, és ez látszott is: a
  mérőtáblán és a fotókon egyaránt eltért az eredetitől. A tizenkét
  összehasonlító mintán **mindegyik közelebb került** az eredeti Picasa
  kimenetéhez, egy sem romlott — a sugaras elmosásnál a legnagyobb eltérés
  11,9-ről 0,7 szintre esett.
- **A hibás csúszkaérték nem megy át némán (#669).** Ha egy `.picasa.ini`-ben
  a megengedettnél nagyobb vagy kisebb érték szerepel, a program eddig az
  irányított és a sugaras effekteknél szó nélkül elfogadta. Mostantól ezekre is
  figyelmeztet, és az érték a megengedett tartományra vágva rajzol — a fájl
  maga változatlan marad.

### Belső
- **A fejlesztői gépen újra használható a teljes tesztkészlet (#664).** Nyolc
  bukó részfutásból nulla lett. Ebből a munkából jött elő egy valódi, a
  felhasználót is érintő hiba: egy sérült videó a mappában összeomlaszthatja
  a programot (#673, javítás alatt).
- A fényképezőgép adatai (rekesz, fókusztávolság, GPS) mostantól **ponttal**
  jelennek meg, a fájlméret és a darabszámok viszont a rendszer területi
  beállítása szerint — pontosan úgy, ahogy az eredeti magyar Picasa csinálta
  (`docs/decisions/tizedesjel.md`).

## [0.7.50] – 2026-08-15

### Hozzáadva
- **A négy irányított effekt megjelent (#623).** A `dir_sat`, `dir_brite`,
  `dir_sharp` és a `linblur` eddig némán kimaradt a renderelésből — az így
  szerkesztett képeket a program *effekt nélkül* mutatta. Mostantól
  ténylegesen rajzolnak. Velük együtt bekerült a Picasa **közös elmosó
  motorja** is, amit eddig csak közelítettünk.
- **Az effekt-csúszkák feliratai a Picasa saját szótárából (#600).** Eddig
  részben kitalált nevek álltak rajtuk. Ami a legjobban látszik: a legtöbb
  effekt erősség-csúszkája mostantól **„Fokozat"**, ahogy az eredetiben —
  nem „Elhalványítás".

### Javítva
- **A Melegítés effekt pixelpontos lett (#611).** Eddig közelítő görbe adta a
  meleg tónust; kiderült, hogy az eredeti nem számol semmit, hanem egy
  beégetett táblából olvas. A táblát kinyertük a programból, így a Melegítés
  eredménye **bitre azonos** a régi Picasáéval.
- **Az Esc a vágást szakítja meg, nem a nézőt zárja be (#666).** Vágás
  közben az Esc eddig kidobott a fotónézőből, és a megkezdett vágás elveszett.
- **Az automatikus szinthúzás a natív algoritmust követi (#539).** Az „Auto
  kontraszt" eredménye érezhetően közelebb került az eredetihez; a teljes
  tartományú képek érintetlenül maradnak.

### Belső
- A csomagépítés hibás setuptools-minimuma javítva, és két olyan csapda
  lezárva, amitől a csomag-ellenőrzés helyben **hamisan zöldet** mutathatott
  (#652, #655).

## [0.7.49] – 2026-08-15

### Javítva
- **A Melegítés effekt mostantól pixelpontosan az eredeti (#611).** Eddig egy
  közelítő görbe adta a meleg tónust; kiderült, hogy az eredeti program itt
  nem számol semmit, hanem egy beégetett, 256 elemű táblából olvas. A táblát
  kinyertük a programból, így a Melegítés eredménye **bitre azonos** azzal,
  amit a régi Picasa ad — a hatás a negyed- és középtónusban a legerősebb, a
  fehérpontot pedig enyhén lehúzza, ettől filmes és nem rikító.

## [0.7.48] – 2026-08-14

### Javítva
- **A Névjegyben újra a valódi verzió látszik (#642).** A program hónapokig
  `v0.6.86`-ot mutatott, miközben a friss kiadás 0.7.4x volt — a szám két
  helyen élt, és csak az egyiket emeltük. Ez nem szépséghiba: a
  hibabejelentésekben a kijelzett verzió az egyetlen közös fogódzó, és a
  rossz szám rossz nyomra visz. Mostantól egyetlen forrásból származik, és
  teszt őrzi, hogy ne csúszhasson szét újra.

## [0.7.47] – 2026-08-14

### Javítva
- **Újra látszik a Visszavonás/Újra gombpár a szerkesztő bal panelján
  (#641).** Kisebb ablakban — laptopon a tipikus esetben — a gombsor
  lecsúszott a képernyőről, és egyáltalán nem lehetett hozzáférni. Mostantól
  az ablak nem mehet olyan kicsire, hogy a panel ne férjen el; ha mégis
  szűkös a hely, a **gombsor marad látható**, és a csempék közül vész el egy
  sor — a visszavonás fontosabb. *(A 0.7.39 óta állt fenn.)*

## [0.7.46] – 2026-08-14

### Javítva
- **Nem tűnik el többé némán a szerkesztés, ha közben a Picasa is dolgozik a
  mappán (#644).** Eddig, ha ugyanarra a képre a párhuzamosan futó eredeti
  Picasa is írt, az a PicasaPy-ban készített effektet **nyomtalanul
  letörölte** — a `.picasa.ini` az egyetlen helye volt. Mostantól minden
  mentett szerkesztés bekerül egy saját, tartós naplóba is: ha egy másik
  program felülírja, a program **szól, megmondja melyik képről van szó, és
  egy kattintással visszaállítja**. A napló nem a fotók mappájában él, hanem
  az adatbázis mellett — oda egy másik program nem ír bele.

## [0.7.45] – 2026-08-14

### Változott
- **A felső menüsáv megszűnt webes tételei is véglegesen szürkék (#638).** Tíz
  menüpont (Feltöltéskezelő, Kötegelt feltöltés, Picasa fórumok, Online
  információk, Terméskiadási megjegyzések, Adatvédelmi irányelvek,
  Szolgáltatási feltételek, Közzététel a Bloggeren, Nyomat rendelése,
  Importálás a Google Fotókból) eddig „még nincs bekötve" jelöléssel állt —
  pedig a szolgáltatásuk megszűnt. Mostantól a menüsáv ugyanazt mondja
  róluk, mint a jobbklikk-menü. Ami nálunk megvalósítható maradna (például a
  Frissítések keresése vagy a Súgó), az továbbra is „még jöhet".

## [0.7.44] – 2026-08-14

### Hozzáadva
- **A Google Earth-export elérhető a menüből (#530).** Eszközök → Geocímke →
  „Exportálás Google Earth-fájlba": a kijelölt képek közül a helyadattal
  rendelkezők térképre kerülnek. A program megmondja, hány kép került ki, és
  hány maradt ki helyadat híján; ha egyiken sincs helyadat, nem készít üres
  fájlt.

## [0.7.43] – 2026-08-14

### Hozzáadva
- **Google Earth-export: a geocímkézett képek kiírása térképre (#530).** A
  program elkészíti a `doc.kml` fájlt és mellé a bélyegképeket, így a
  fotógyűjtemény megnyitható a Google Earthben: minden kép a saját helyén
  jelenik meg, az ikon fölé érve megnő, rákattintva pedig egy buborékban
  látszik a bélyegkép, a felirat és a dátum. A koordináta nélküli képek
  kimaradnak — a program megmondja, hányan. *(A motor és a hívható művelet
  készen van; a menüpont bekötése külön lépés.)*

## [0.7.42] – 2026-08-14

### Hozzáadva
- **A gyűjtemények bezárhatók (#461).** A bal hasábon minden saját gyűjtemény
  neve mellett ott egy kis jelző: rákattintva a gyűjtemény **bezárul**, és a
  benne lévő mappák képei eltűnnek a rácsból, a keresésből és a
  csillag-szűrőből is. Ez nem törlés és nem is összecsukás — a mappák a
  helyükön maradnak, a gyűjtemény bármikor visszanyitható (a jelzőre vagy a
  nevére duplán kattintva). Így a régi archívumok, az exportált képek és a
  ritkán használt források egy kattintással eltehetők az útból. Ha a bezárás
  után egyetlen kép sem maradna látható, a program — az eredeti Picasa
  szövegével — előbb rákérdez.

## [0.7.41] – 2026-08-14

### Javítva
- **A diavetítés windowsos tesztje nem mér félkész állapotot (#519).** A
  vetítés közbeni csillagozás/forgatás háttérszálon fut; a teszt eddig 2
  másodperc után akkor is továbbment, ha a művelet még nem fejeződött be — a
  lassabb windowsos futtatón emiatt ingadozott a CI, és a bukás valódi hibának
  látszott. Mostantól a teszt a művelet befejeződését várja meg, hibaágon
  pedig a tényleges hibaüzenetet írja ki, nem egy félreérthető állítást.

## [0.7.40] – 2026-08-14

### Változott
- **A megszűnt online szolgáltatások menüpontjai véglegesen szürkék (#422).**
  A jobbklikk-menűkben hét olyan tétel volt (Feltöltés Google Fotókba / Picasa
  Webalbumba, Gyorsfeltöltés, Feltöltés tiltása, Online műveletek), ami eddig
  „még nincs bekötve" jelöléssel szerepelt — pedig ezek soha nem lesznek
  bekötve, mert maga a szolgáltatás szűnt meg. A tételek a helyükön maradnak,
  hogy a menük szerkezete egyezzen az eredetivel, de már nem ígérik, hogy
  egyszer működni fognak, és nem számítanak bele a hátralévő munkába.

## [0.7.39] – 2026-08-13

### Javítva
- **Az effekt-fülekről végleg lekerült a görgethető keret (#628).** A
  szerkesztő bal oldali paneljén újra megjelent egy keret, amiben görgetni
  kellett az effektekért — pedig ez a keret egyszer már le lett véve. A hibát
  most nem a tünetnél orvosoltuk: a panel eddig **fix 420 képpont** magas volt,
  akármekkora az ablak, és a 12 effekt-csempe ebbe soha nem fért bele. Mostantól
  a panel az ablakkal együtt nő, a Visszavonás/Újra gombsor a tartalmat követi,
  és a csempékre nem kerülhet rá. Ha az ablak alacsony, a panel kikényszeríti a
  neki szükséges helyet, ahelyett hogy elvágná a tartalmát.

## [0.7.38] – 2026-08-13

### Javítva
- **A töréspontos görbék mostantól úgy hajlanak, ahogy az eredetiben (#629).**
  A Picasa a görbe-töréspontok között sima, köbös átmenetet használ, nálunk
  eddig egyenes szakaszok voltak. Kilenc effektet érintett; a **60-as évek**
  és a **Kinemaszkóp** képén ez akár **21 világossági szint** eltérést jelentett
  — szemmel látható különbség, nem kerekítési zaj. A kétpontos görbét használó
  effektek (Színinvertálás, Neon, Ceruzarajz) kimenete bájtra változatlan.

## [0.7.36] – 2026-08-13

### Hozzáadva
- **A Finomhangolás-csúszkák modelljei mostantól a VALÓDI Picasa-kimenethez
  vannak mérve a tesztkészletben (#551).** Eddig csak néhány kézzel kiírt
  horgonyérték őrizte őket; innentől a Kiemelések, az Árnyékok, a
  Színhőmérséklet mind a hat állása és a szín-varázspálca teljes görbéje
  össze van vetve azzal, amit a Picasa 3.9 ténylegesen kiad. A mérés a
  referencia-fotókból desztillált átlaggörbékből dolgozik (a fotók maguk nem
  kerültek a repóba), a hibakorlátok a mai, mért pontosságból származnak.
  A próba szerint ez elkapja azt a fajta csendes rontást, ami a jegyben
  egyszer már majdnem bekövetkezett: a Színhőmérséklet elutasított natív
  képlete a legkedvezőbb paraméterrel is a korlát 4–19-szeresét hozza.

## [0.7.35] – 2026-08-13

### Hozzáadva
- **Két irányított effekt a natív magokból: „Irányított telítettség" és
  „Irányított fényesség" (#623).** Mindkettő a Picasa saját, dekompilált
  pixelképletét futtatja, nem közelítést: közös lineáris rámpa a két
  csúszkából („Balról jobbra", „Felülről lefelé"), rá a `dir_sat`
  luma-interpolációja, illetve a `dir_brite` köbös tónusgörbéje. A régi
  könyvtárak `filters=` lánca ezentúl ezt a két nevet is megjeleníti,
  kihagyás helyett. A család harmadik tagja (`dir_sharp`) és a `linblur`
  szándékosan kimaradt: ott a dekompilátum nem adja meg a hiányzó
  együtthatót, azt előbb ki kell mérni.

## [0.7.34] – 2026-08-13

### Javítva
- **A „Jó napom van" szinthúzása mostantól az eredeti Picasa geometriáját
  futtatja (#539).** A vágópontokat eddig fix 0,5% / 0,2% percentillel
  közelítettük; helyette a natív algoritmus fut: a hisztogram a kép középső
  90% × 90%-áról készül (a perem kimarad), a vágási küszöb pedig a teljes
  képpontszám 1/200-a, mindkét végén azonosan. A 12 referencia-képpáron az
  átlagos eltérés 2,68-ról 2,61-re csökkent, és a vágópontok maguk is a
  mérttel egyeznek. Külön mérés igazolta, hogy a nagyon szűk csatornákra
  vonatkozó 58 szintes alsó korlát nem illesztési fogás, hanem valódi
  Picasa-viselkedés: a 36 kimért csatornán a ténylegesen alkalmazott
  tartomány sosem ment 58,1 alá.

## [0.7.33] – 2026-08-13

### Javítva
- **Az effekt-fülön a Visszavonás/Újra gombsor rálógott a csempékre
  (#616).** Rövidebb ablakban a 12 csempés rács magasabb volt, mint a hely,
  és a panel alján ülő gombsor ráfeküdt a képekre. A fülek mostantól — a
  mód-eszközökhöz hasonlóan — egy vágott, görgethető területen ülnek, ami
  pontosan a gombsorig ér: a csempék **sosem** érnek a gombok alá. Az
  eredeti Picasa is külön konténerben tartotta a kettőt.

## [0.7.32] – 2026-08-13

### Hozzáadva
- **Sebesség a másolás/áthelyezés haladásjelzőjén (#457).** A számláló
  mellett most már az is látszik, milyen gyorsan halad („12,3 MB/s") —
  ahogy az eredeti Picasa is mutatta. Egy nagy kötegnél ez mondja meg,
  érdemes-e megvárni.
- **Mappa áthelyezése (#457).** A mappa jobbklikk-menüjében eddig
  helyfoglaló volt a „Mappa áthelyezése…" — most működik, és a mappa a
  **kísérőfájlokkal együtt** költözik. Ez nálunk több, mint kényelem: a
  `.picasa.ini` az igazságforrás, enélkül a képek elveszítenék a
  feliratukat, a címkéiket és az arc-hozzárendeléseiket. A program
  megtagadja a rendszermappák mozgatását, és nem enged olyan célt, ahol
  már van azonos nevű mappa — mindkét esetben a forrás érintetlen marad.
## [0.7.31] – 2026-08-13

### Változott
- **A mentés-parancsok a nézőben is működnek (#422).** A Mentés, a
  Visszaállítás, az „Összes szerkesztés visszavonása" és az „Arcok
  alaphelyzetbe állítása" eddig helyfoglaló volt a néző jobbklikk-
  menüjében — most ugyanazt teszik, mint a rácsban és a menüsávban.
  Ugyanaz a parancs nem viselkedhet máshol másképp.
## [0.7.27] – 2026-08-13

### Hozzáadva
- **„Exportált képek" a bal hasábon (#457).** Az exportált célmappák
  mostantól megjelennek a Projektek gyűjtemény alatt, legutóbbi elöl — az
  eredeti Picasa is külön csomópont alá gyűjtötte őket, hogy az export
  **nyomon követhető** maradjon, ne tűnjön el a fájlrendszerben. A már
  törölt mappák maguktól eltűnnek a listából.

## [0.7.25] – 2026-08-13

### Hozzáadva
- **Arcok alaphelyzetbe állítása (#422).** A rács jobbklikk-menüjéből
  minden arc visszahelyezhető a Névtelenek albumba (az arc-csoportok
  törlődnek, a felismerési lenyomatok megmaradnak, tehát nem kell újra
  átnézni a könyvtárat). Az eredetihez hasonlóan **figyelmeztetéssel**
  kérdez rá. Egy dolgot szándékosan **nem** csinál: a fotókba írt
  névcímkékhez nem nyúl — azt az eredeti is külön kérdésként tette fel, és
  az ember által adott név nálunk szent.

### Változott
- **Mentés, Visszaállítás és „Összes szerkesztés visszavonása" a rács
  jobbklikk-menüjéből is (#422).** Eddig ez a három pont helyfoglaló volt
  a menüben, pedig a működésük a Fájl menüből már elérhető volt. Mostantól
  ugyanaz a megerősítés nyílik, mint a menüsávból — egy parancs, egy út.
  Ha nincs mit menteni vagy visszavonni, a tétel **szürke, de látszik**:
  az eredeti Picasa sem tüntette el, hogy a menü magassága állandó
  maradjon.
## [0.7.22] – 2026-08-13

### Változott
- **Az Emberek-panel megmondja, mire számíthatsz (#26).** Üres listánál
  eddig egyetlen általános mondat állt ott; az eredeti Picasa panelje
  viszont **aszerint** magyarázott, mit néz éppen a felhasználó. Most
  nálunk is: személy albumát nézve „…akik a kiválasztott személlyel együtt
  szerepelnek", kijelölt fotóknál „…akik a kijelölt fotókon szerepelnek",
  egyébként pedig az, hogy még nem találtunk embereket.
## [0.7.19] – 2026-08-13

### Változott
- **Kézi arc-hozzáadás az eredeti kétlépéses módján (#26).** Eddig a
  téglalap felhúzása után azonnal felugrott a névkérő, és a téglalapon
  utólag nem lehetett igazítani. Mostantól — ahogy az eredeti Picasa
  utasítása leírta — a **négyszög megmarad és az oldalai húzhatók**, a
  nevet pedig a négyszög alatti **„Név hozzáadása"** felirattal lehet
  megadni. Szerkesztő módban ott az útmutató szöveg is: a gesztus
  önmagában nem felfedezhető.

## [0.7.16] – 2026-08-13

### Hozzáadva
- **Haladásjelzés a másoláshoz és az áthelyezéshez (#457).** Sok fájl
  mozgatásakor eddig „nem történt semmi", amíg a művelet le nem futott.
  Mostantól látszik, **hova** megy, és **hol tart** — az eredeti Picasa
  szövegeivel („Fájlok másolása", „%2 / %1 fájl másolása"). Egyetlen
  fájlnál nem nyílik ablak.

## [0.7.13] – 2026-08-13

### Hozzáadva
- **„Mellőzött emberek" album (#26).** A mellőzött arcok mostantól meg is
  nézhetők: a bal hasáb Emberek gyűjteményében megjelenik a *Mellőzött
  emberek* sor, és onnan a **mellőzés visszavonható**. Az eredeti Picasában
  ez is album volt, nem egyirányú szemetes — most nálunk sem az.

## [0.7.12] – 2026-08-13

### Hozzáadva
- **Név-javaslat az arcokra (#26).** Ha egy névtelen arc eléggé hasonlít
  egy már elnevezett személyre, a program **megkérdezi**: a bélyegképen
  megjelenik a név kérdőjellel, pipa és ✕ gombbal — pontosan úgy, ahogy az
  eredeti Picasa tette. A javaslat soha nem dönt a felhasználó helyett: az
  arc addig névtelen marad, az elvetés pedig csak a javaslatot törli, az
  arcot nem mellőzi.

  Ehhez a hiányzó láncszem is elkészült: eddig semmi nem kötötte a
  felismerési lenyomatot a névhez, ezért a javaslat-ág — bár a matematika
  megvolt — sosem talált el. Az index mostantól eltárolja, melyik arc
  melyik névhez tartozik (séma v12, meglévő indexeknél újraindexelés
  nélkül).

## [0.7.11] – 2026-08-13

### Hozzáadva
- **Mellőzött emberek (#26).** A „Névtelenek" nézetben a kijelölt arcok
  **mellőzhetők** — és a mellőzés nem törlés: ahogy az eredeti Picasában,
  a személy egy külön albumba kerül, tehát vissza is vehető. A program
  előbb rákérdez, az eredeti szövegével: *„Biztosan áthelyezi ezt a
  személyt a Mellőzött emberek albumba?"*

## [0.7.10] – 2026-08-13

### Változott
- **Az arcbeolvasás haladása a „Névtelenek" album tételén (#26).** Eddig
  külön sorban jelent meg; az eredeti Picasa magán az album tételén
  mutatta („While scanning, progress information appears in the Unnamed
  album item"). A tétel az első beolvasáskor is látszik, amikor még nulla
  névtelen arc van.

### Hozzáadva
- **Emberek-panel (#26).** A Nézet → Emberek menüpont mostantól valódi
  panelt nyit a jobb oldalon, a Címkék, a Helyek és a Tulajdonságok
  mellett — az eredeti Picasa is ide tette (a binárisban a
  `rightdrawerpanel/peoplepanel` pont e három mellett áll). Két szakasza
  van, az eredeti szövegeivel: **„Ezen a fotón:"** (a kijelölt képeken
  névvel szereplő emberek) és **„Szintén ezeken a fotókon:"** — ez utóbbi
  azt mutatja, hogy a nézett személlyel kik szerepelnek együtt, és egy
  kattintással át lehet lépni a másik személy albumára. Ez a családi
  gyűjtemények természetes navigációja: „ki van még rajta ezeken a
  képeken?"

## [0.7.9] – 2026-08-12

### Hozzáadva
- **Fogd-és-vidd az albumlistára (#455).** A kijelölt képek a bal hasáb
  albumlistájára húzhatók: a hívogató sorra ejtve **új album** készül
  (ugyanazzal a névkérő ablakkal, mint a menüből), egy meglévő album
  sorára ejtve pedig a képek **abba az albumba** kerülnek. A húzás csak
  már kijelölt képről indul — a ki nem jelölt területen marad a lasszós
  kijelölés.

## [0.7.8] – 2026-08-12

### Hozzáadva
- **Az arcbeolvasás haladása az albumlistában (#449).** Az eredeti Picasa
  nem modális ablakban mutatta a háttérmunkát, hanem a bal hasáb
  albumlistájában („Arcok keresése… 42% kész"), és közben semmi nem
  blokkolta a felhasználót. A sor magától megjelenik és eltűnik.
- **Adatbázis tömörítése (#449).** Az Eszközök → Kísérleti menüből
  elindítható a fotóindex tömörítése (SQLite `VACUUM`), az eredeti Picasa
  „Compacting" ablakának mintájára: megmondja, hogy percekig tarthat, és
  **bármikor megszakítható** — megszakításkor az adatbázis érintetlen
  marad. A haladásjelző szándékosan határozatlan: a `VACUUM` nem mond
  százalékot, kitalálni pedig félrevezetés lenne.

## [0.7.7] – 2026-08-12

### Változott
- **Barátságosabb első indítás (#449).** Üres könyvtárnál eddig rögtön a
  Mappakezelő fája nyílt ki — egy nagy döntés az első percben. Mostantól az
  eredeti Picasa mintáját követjük: **egyetlen kérdés** két választással
  (csak a Dokumentumok, a Képek és az asztal, vagy a teljes saját mappa),
  egyetlen OK gombbal. A program előre megmutatja, mely mappákat fogja
  átnézni, és — ahogy az eredeti is tette — kiírja, hogy **a keresés soha
  nem mozgat és nem másol fájlt**. A mappák később bármikor módosíthatók a
  Mappakezelőben.

### Hozzáadva
- **Hibanapló (#449).** A figyelmeztetések és hibák mostantól fájlba is
  kerülnek (`errorlog.txt` az adatkönyvtárban), és ha az adatbázis
  betöltése hibára fut, a program – ahogy az eredeti Picasa – **felajánlja
  a napló megtekintését**, ahelyett hogy némán összeomlana vagy titokban
  javítana. A napló nem nő korlátlanul: méret fölött indításkor
  elforgatjuk.

## [0.7.6] – 2026-08-12

### Hozzáadva
- **Forgatás és csillagozás már az importálás előtt (#441).** Az
  import-előnézet bélyegképein megjelent két forgató nyíl és egy csillag —
  ahogy az eredeti Picasa import-képernyőjén is —, így a képeket még a
  bemásolás előtt ki lehet egyenesíteni és megjelölni. A jelölés a
  **másolatra** kerül; a kártyán lévő eredeti fájlokhoz a program nem nyúl.
- **Sebesség az import haladásjelzőjén (#441).** A csík mellett mostantól az
  is látszik, milyen gyorsan halad a másolás — ebből lehet megbecsülni,
  mennyi van hátra.
- **Fájltípus-szűrő és korábbi források az importnál (#441).** Beállítható,
  hogy a beolvasás kép- és filmfájlokat, csak képeket, vagy mindent
  keressen; a forrásválasztó pedig felkínálja a **legutóbb használt
  forrásokat**, ahogy az eredeti Picasa is tette.

## [0.7.5] – 2026-08-12

### Hozzáadva
- **Igazi betűtípusok a szöveg-eszközben (#450).** A feliratok eddig egy
  vonalas, „rajzolt" betűkészlettel készültek, amiben nincs betűcsalád,
  félkövér, dőlt vagy aláhúzás. Mostantól valódi TrueType-betűkkel
  rajzolunk: **Arial · Times New Roman · Courier New**, félkövéren, dőlten,
  aláhúzva, és a sorok **balra / középre / jobbra** igazíthatók. A vezérlők
  ott vannak a Szöveg eszköz panelján: betűtípus-lista, méret, F/D/A gombok
  és a három igazítás-gomb. Ha a gépen nem található megfelelő betű, a
  felirat a régi módon jelenik meg — a szöveg-eszköz sosem esik ki.

## [0.7.4] – 2026-08-12

### Hozzáadva
- **Végre menthetők a szerkesztések a fájlokba (#444).** A Fájl menü
  **Mentés** (Ctrl+S) pontja eddig szürke helyfoglaló volt — a motor kész
  volt, csak nem lehetett elindítani. Mostantól él, és vele a másik két
  fokozat is: a **Visszaállítás** (az eredeti jön vissza, a szerkesztések
  elvesznek) és az **Utolsó mentés visszavonása** (a fájl áll vissza, de a
  szerkesztések megmaradnak). Minden mentés előtt biztonsági másolat
  készül.
- **Figyelmeztetés mentés előtt**, ha a képen olyan szerkesztés van, amit a
  program még nem tud megjeleníteni: a mentés azt véglegesen eldobná, ezért
  a program felsorolja őket, és külön rákérdez.

## [0.7.3] – 2026-08-12

### Hozzáadva
- **A kollázs és a film is a képtálca tartalmán dolgozik (#455).** Az
  exportálás után most a másik két gyűjtő-művelet is a tálcára tett képekből
  készül — több mappából összeválogatva —, és a párbeszédek rács-kijelölés
  nélkül is megnyílnak, ha a tálcán van kép. Üres tálcánál minden marad a
  régiben: a kijelölés a forrás.

## [0.7.2] – 2026-08-12

### Hozzáadva
- **A mappába exportálás a képtálca tartalmán dolgozik (#455).** Az eredeti
  Picasában az alsó sáv gombjai nem a pillanatnyi kijelölésre, hanem a
  **tálcára gyűjtött** képekre hatottak — ez a tálca értelme: több mappából
  összeszedni, amit együtt akarunk kezelni. Mostantól nálunk is: ha van
  tartott kép, az exportálás azokat viszi (bármelyik mappából), üres
  tálcánál marad a kijelölés.

## [0.7.1] – 2026-08-12

### Hozzáadva
- **A vágás képarány-listája teljes lett (#448).** A legördülőben mostantól
  ott a **magyarázó alcím** is, ahogy az eredeti Picasában — „Kisméretű
  nyomat", „Letter méretű papír", „CD-borító", „Szélesvásznú képernyő" —,
  bekerült a hiányzó **8.5x11** (Letter) arány, és él a **Jelenlegi
  megjelenítés** tétel is, ami a képernyő arányát veszi át.

## [0.7.0] – 2026-08-12

### Hozzáadva
- **Működik a szín-varázspálca a Finomhangolás fülön (#551).** A gomb eddig
  az „Automatikus szín" szűrőt fűzte a képre; a Picasa saját mentései
  viszont elárulták, hogy a pálca valójában az **Alapszínválasztás** színét
  állítja be automatikusan. Mostantól nálunk is ezt teszi: a program a
  kevéssé telített („szürke-közeli") képpontokból választ viszonyítási
  színt, és azzal veszi ki a színezetet. A tulajdonos 11 mérőképén a
  választott szín a Picasáétól átlagosan ~3 egységgel tér el (0–255-ös
  skálán).

## [0.6.99] – 2026-08-12

### Javítva
- **Az Alapszínválasztás (pipetta) a Picasa saját arányaival dolgozik
  (#551).** Eddig egy csillapított közelítés futott, ami a színezetnek csak
  a felét-háromnegyedét vette ki. A Picasa a viszonyítási színt a **zöldhöz**
  méri (a mentett érték középső bájtja mindig 128), és a program mostantól
  ugyanígy: a semlegesnek jelölt pontból számolt korrekció a valódi Picasa
  eredményétől ~3 %-on belül van. Tényleg szürke pontot kijelölve a kép
  változatlan marad, ahogy eddig is.

## [0.6.98] – 2026-08-12

### Javítva
- **A Derítőfény mostantól a Picasa saját algoritmusa (#551, #575).** Eddig a
  mérésekre illesztett közelítés futott; most a Picasa natív kódjából
  visszafejtett, pontos művelet: egy gamma-görbe, amit a program a képpont
  világosságával **fordítottan arányos** súllyal kever az eredetihez — ezért
  derít a sötét részeken anélkül, hogy a világosakat kimosná. Ugyanez a mag
  hajtja a Derítőfény csúszkát, a „Régi effektek" fülön a két derítő-gombot
  és a `finetune` láncot is.

## [0.6.97] – 2026-08-12

### Javítva
- **A „Régi effektek" fül gombjai végre működnek (#582).** Eddig minden
  gombja hibaüzenetbe futott („Érvénytelen effekt"), mert a fül olyan
  szűrőneveket kínált, amilyeneket a szerkesztő nem fogadott el. Mostantól a
  Derítőfény, az egykattintásos Derítőfény és a Radiális színezés
  alkalmazható is — a Picasa saját alapértékeivel (25%-os derítés, középre
  tett fókuszpont).
- **A szerkesztő effekt-paneljei nem ragadnak be (#583).** Ha egy effekt
  csúszkás panelje nyitva volt, fülváltás után **ott maradt**, és
  rárajzolódott a másik fül csúszkáira. Mostantól fülváltáskor bezárul (a
  beállítás elvész, a mentett kép változatlan), és a „További effektek" meg
  a „Régi effektek" fül sem lóg többé egymásra a nyitott panellel.

## [0.6.96] – 2026-08-12

### Hozzáadva
- **Névütközéskor megkérdezzük, mi legyen (#457/2).** Ha a célmappában már
  van azonos nevű fájl, a program – ahogy az eredeti Picasa – rákérdez:
  **„Másodpéldányok átnevezése"** vagy **„Másodpéldányok kihagyása"**. Ha
  nincs ütközés, nincs kérdés sem. Az áthelyezést a célmappa kiválasztása
  után egy **„Fájlok áthelyezése"** jóváhagyás előzi meg, ugyanúgy, mint
  régen.
- Egy hibás fájl többé nem állítja meg az egész köteget: a többi átmegy, a
  végén pedig **egyetlen** összegzés jön (és az is csak akkor, ha volt
  kihagyott vagy hibás fájl).

## [0.6.95] – 2026-08-12

### Javítva
- **A bal panel rendezése végre a bal panelt rendezi (#461/3).** Az eredeti
  Picasában a bal hasáb **saját jobbklikk-menüje** tartalmazta a „Rendezés
  dátum / név / méret / legutóbbi változtatás alapján" tételeket — vagyis az
  a **hasábot** rendezte. Nálunk ez a menü eddig a **rácsot** állította, a
  hasáb pedig mozdíthatatlan volt. Mostantól két, egymástól független
  beállítás van, ahogy az eredetiben: a **panel saját menüje a panelt**, a
  felső **Nézet ▸ Mappanézet a rácsot** rendezi.
- **Az évszám-fejlécek csak a dátum-nézetben jelennek meg (#461/3).** Név
  vagy méret szerinti rendezésnél ugyanaz az évszám többször, összevissza
  sorrendben bukkant volna fel; ott most sima felsorolás áll.

## [0.6.94] – 2026-08-12

### Karbantartás
- **A szerkesztőpanel szétbontva (#496).** Az `EditorPanel.qml` 1367 sorról
  **786-ra** fogyott, a projekt 800 soros korlátja alá. A tartalom fülenként
  és blokkonként önálló fájlokba került (fülsáv, fülgomb és ikonja, 1. fül,
  csúszkás effekt-alpanel, párbeszédek), a gazda pedig a közös állapotot és a
  fül-váltást tartja. **Viselkedés-változás nincs**: a meglévő szerkesztő-
  tesztek változtatás nélkül zöldek — ez a bizonyíték. Ettől a párhuzamos
  munkában is kevesebb az ütközés: egy fül módosítása már nem írja ugyanazt a
  fájlt, mint a többi.

## [0.6.93] – 2026-08-12

### Javítva
- **A FocalZoom és a Focal Pixelate csúszkái eddig fel voltak cserélve
  (#570).** A natív visszafejtés kimutatta, hogy a fókuszpont után az
  **Impact** következik, nem a **Radius** — a program a harmadik mezőt
  olvasta sugárként, így a két csúszka egymás hatását fejtette ki. Mindkét
  effekt mostantól mind a **hat** paraméterét helyes helyről olvassa, közös
  körmaszkot használ (a Hardness szabja a perem lágyságát), és a Fade a
  szokásos módon zár.

### Hozzáadva
- **A Focal Pixelate (fókuszált képpontnövelés) effekt megjelent (#570).**
  Eddig felismertük, de nem rendereltük. Az eredeti recept szerint készül:
  lekicsinyítés, majd **legközelebbi-szomszéd** visszanagyítás — ettől élesek
  a blokkjai, nem elmosódottak.

## [0.6.92] – 2026-08-12

### Javítva
- **A Comicize (Képregény) effekt az eredeti féltónusos rasztert kapta
  (#569).** A korábbi megvalósítás posterizálással és élkereséssel közelítette
  — de a Picasa effektje nem élkiemelő képregényszűrő, hanem **nyomdai
  raszter**: két, egymáshoz képest fél csempével eltolt pontrács. A pont a
  sötét területeken nagyra nő, a világosokon elfogy, ahogy a valódi
  nyomdatechnikában. A három csúszka (BlurXY, DotContrast, DotFade) mostantól
  a `filterdesc.xml` szerinti szerepét tölti be; a `DotFade = 100` pontosan
  érintetlen képet ad.

## [0.6.91] – 2026-08-12

### Hozzáadva
- **„Régi effektek" fül a szerkesztőben (#571).** A Picasa motorjában benne
  maradt egy csomó szűrő, aminek a 3.9-es felületén **nincs kezelőfelülete**:
  régebbi verziókból örökölt darabok. A motor egy régi `.picasa.ini`-ből még
  alkalmazza őket, de a felhasználó nem tudja előhívni — mostantól nálunk
  igen. **Ez tudatos eltérés az eredetitől**, szándékosan többet adunk.
  - Amelyik effektnek van valódi modellje (`radtint`, `autobacklight`,
    `fill`), az **működik**; a többi **látszik, de szürke** — mert egy régi
    képen ott lehet, és tudni kell róla. A letiltott gombok megmondják, miért
    nem használhatók, és a *halott* név (`focalpixelate`) más magyarázatot kap,
    mint a *még megfejtetlen*.
  - Hogy melyik gomb él, azt a **renderelő** dönti el, nem kézzel írt lista —
    így nem lehet aktívnak látszó, de nem ható gomb.
  - Ha a megnyitott kép láncában ilyen effekt van, a **fül jelzést kap**.

## [0.6.90] – 2026-08-12

### Hozzáadva
- **`autobacklight` effekt (#567).** A régi `.picasa.ini`-láncokban előforduló
  név mostantól renderel: a natív regiszter szerint ez **nem** adaptív
  képelemzés, hanem **fix 25%-os derítőfény** — ugyanaz a mag, mint a
  `backlight`/`fill`, rögzített argumentummal. Külön gombot nem kap a
  felületen, ahogy az eredetiben sem volt.

### Javítva
- **A kisbetűs `focalpixelate` halott bejegyzésként jelenik meg (#567).** A
  Picasa 3.9 natív regiszterében sincs hozzá feldolgozó — konfigurációs
  maradvány, nem „még hiányzó" effekt. A renderjelentés ezt ki is mondja, és
  a név semmiképp nem keveredhet az élő `PicnikFocalPixelate` effekttel.

## [0.6.89] – 2026-08-12

### Javítva
- **Az IR (infravörös film) effekt az EREDETI csővezetékét kapta (#566).** A
  korábbi modell a paraméternevekből következtetett, és három ponton tévedett:
  SCREEN-t kevert LIGHTEN helyett, a zöld izzást a már monokrómmá tett képre
  tette (nem az eredetire), és a **kék csatorna negatív súlyát** teljesen
  figyelmen kívül hagyta. A natív kernel visszafejtése után a záró mátrix
  `Y = −0,5·R + 2,0·G − 0,5·B`; a kék tehát sötétít, ahogy a valódi
  infravörös filmen is.

## [0.6.88] – 2026-08-12

### Hozzáadva
- **`radtint` (Sugaras árnyalás) effekt (#565).** Az utolsó „exe-ből ismert,
  de renderelhetetlen" szűrőnév is megkapta a modelljét — nem találgatásból,
  hanem a natív kód visszafejtéséből: a fókuszpont körül a kép változatlan,
  kifelé egy köbös smoothstep maszk szerint erősödő **szorzó**-színezés fut
  (`forrás × szín / 256`), ami lényegében különbözik a `dir_tint` „szín felé
  keverésétől". Egyetlen paraméter, a Feather csúszka affin leképezése maradt
  feltételezés — ez dokumentáltan jelölve van, golden-párral pontosítható.

## [0.6.87] – 2026-08-12

### Hozzáadva
- **Offline mappa kezelése (#459/5).** A levált NAS-mount vagy kihúzott lemez
  mappája mostantól **bennmarad az indexben** a fotóival együtt — eddig némán
  kiestek belőle. A mappa „jelenleg nem elérhető" jelölést kap a bal hasábon
  (halvány, dőlt sor + súgószöveg), a rá lépéskor pedig a program kimondja,
  mi a helyzet, hibaüzenet-szerű pánik nélkül. A jelölés a mount visszatérése
  után magától elmúlik, újraépítés nélkül. A felismerés szabályát és a
  vállalt tévedés-irányt a `docs/decisions/offline-folders.md` rögzíti.
- **Hiányzó fájlok a kollázsban és a mozgófilmben (#459/3).** A nem található
  kép mostantól **külön mondatot** kap az eredeti Picasa szövegével — az
  megmondja, mi történhetett (elmozdítás, átnevezés, törlés) —, a csupán
  olvashatatlan fájlok pedig a semleges „kihagyva" számban maradnak. A munka
  ezután is a maradékkal készül el, nem áll le.

## [0.6.86] – 2026-08-12

### Hozzáadva
- **„Hozzáadás" gomb a képtálcán (#455).** A böngészés közben, mappákon
  átnyúlóan gyűjtött képek egy lépésben albumba tehetők — az eredeti Picasa
  tálcáján is külön gomb kínálta ezt.

## [0.6.85] – 2026-08-12

### Javítva
- **Visszavontam a görgethető keretet az effekt-fülekről (#422).** Rossz válasz
  volt a tünetre, és nem is kérte senki. A valódi ok az volt, hogy a három
  ismert effekt-fülre olyan effektek is odakerültek, amelyek az eredetin nincsenek
  ott — ezek mostantól **külön, „További effektek" fülön** vannak, a 3–5. fül
  pedig pontosan az eredeti gombkészletét tartalmazza (12 · 12 · 11).

### Hozzáadva
- **Három automatikus vágás-javaslat a Vágás eszközben (#448).** Az eredeti
  Picasa is három kész vágást ajánlott fel; a stratégiák a nevük szerint: szoros
  vágás az arcokra, kompozíció az arcok köré, illetve arc nélkül a
  legrészletgazdagabb terület, a horizontvonal és a szín-domináns terület. A
  javaslat a kijelölésbe kerül, tehát még igazítható rajta az Alkalmaz előtt, és
  a kiválasztott képarányt követi.

## [0.6.84] – 2026-08-12

### Hozzáadva
- **Az Emberek-album kép-parancsai a jobbklikk-menüben (#422).** Személy
  albumában a képre jobbklikkelve mostantól elérhető az „Eltávolítás az
  Emberek albumból" (megerősítéssel — a névcímke csak újbóli felismeréssel
  vagy kézzel állítható vissza) és az „Áthelyezés új személyhez…". Mindkettő
  a teljes kijelölésre hat, mappánként egyetlen írással.
- Új, általános névbekérő párbeszéd, amit a további átnevező parancsok is
  használhatnak.

## [0.6.83] – 2026-08-12

### Javítva
- **Az effekt-fülek csempéi nem csúsznak szét (#422).** A kétsoros feliratú
  gomb (például „Infravörös film") magasabb lett a többinél, a rács sora
  hozzá igazodott, a szomszédos csempék képe pedig felnagyult. A bélyegképes
  gomb mostantól mindig két sornyi feliratot foglal, így a rács egyenletes.
- **Az effekt-csempék felirata a többi csempéével azonos méretű** — eddig
  nagyobb volt.

### Hozzáadva
- **Jobbklikk-menü a szövegmezőkben (#422).** Az eredeti Picasa minden
  szövegmezője alatt ott van a hét tételes menü (Visszavonás · Kivágás ·
  Másolás · Beillesztés · Törlés · Az összes kijelölése · Automatikus
  kitöltés); nálunk eddig egyetlen mezőben sem volt. Az inaktív tételek —
  az eredetihez hasonlóan — szürkén látszanak, nem tűnnek el. A
  jelszó-mezőben szándékosan nincs menü.

## [0.6.82] – 2026-08-12

### Hozzáadva
- **Figyelmeztetés a visszavonás adatvesztéses eseteire (#465).** A retusálás
  és a vörösszem-javítás területadatot hordoz: a visszavonás eldobja, és az
  „Újra" nem hozza vissza. Az eredeti Picasához hasonlóan ezek visszavonása
  mostantól rákérdez — a többi lépésé továbbra sem, hiszen ott van visszaút.
- Az **„Összes szerkesztés visszavonása"** az eredeti két külön szövegét
  használja egy, illetve több kijelölt képre, és **külön figyelmeztet**, ha a
  kijelölésben vörösszem-javítás van.

## [0.6.81] – 2026-08-12

### Hozzáadva
- **A felület betűtípusa az eredeti arányaival (#526).** Az eredeti Picasa a
  kereskedelmi Praxis családot használta, ezt nem szállíthatjuk; a
  helyettesítőt **méréssel** választottuk, nem ránézésre: a két Picasa-
  képernyőképről leolvasott tíz magyar felirat képpont-szélességét vetettük
  össze az öt jelölttel. Az **Open Sans** illeszkedik a legjobban (átlagos
  eltérés 0,92%, a következő jelölt 1,15%), ezért ez került a programba
  (SIL Open Font License 1.1, a licenc mellékelve).

### Belső
- Teszt őrzi, hogy a kilépéskor a szerkesztő háttér-renderelése előbb
  érvénytelenítve, majd korlátos ideig bevárva legyen (#547/#430) — enélkül a
  háttérszál a program leállása közben összeomlást okozhatott.

## [0.6.80] – 2026-08-12

### Javítva
- **Az effekt-beállítások alpanelje sem lóghat rá a Visszavonás sorra (#464).**
  A sok paraméteres effektek (például a Vignetta) beállító-panelje magasabb
  lehet a rendelkezésre álló helynél; ez is vágott, görgethető területre került.
  Ezzel a szerkesztőpanel minden nézete — az öt fül, a négy mód-eszköz és az
  effekt-beállítások — a gombsor fölött ér véget.

## [0.6.79] – 2026-08-12

### Javítva
- **A mód-eszközök panelje sem lóghat rá a Visszavonás sorra (#464).** A vágás,
  a retusálás, a vörösszem és a szöveg panelje ugyanabba a hibába futhatott,
  mint az effekt-fülek: ha a tartalom magasabb a rendelkezésre álló helynél,
  ráúszott a panel alján ülő gombsorra. Mind a négy mostantól közös, vágott
  görgethető területen ül, ami pontosan a gombsorig ér.

## [0.6.78] – 2026-08-12

### Javítva
- **Az indexkép-jelvények végre látszanak is (#463).** A hely-tű és a két
  arc-jelvény („van rajta felismert arc", „névjavaslat vár jóváhagyásra") a
  bélyegkép-kártyában rég készen álltak, és az adat is megvolt a modellben —
  a fő rács viszont nem kötötte be őket, így sosem jelentek meg. Mostantól
  megjelennek; új teszt őrzi, hogy egyetlen jelvény se maradhasson bekötetlenül.

## [0.6.77] – 2026-08-12

### Javítva
- **Az effekt-fülek gombjai nem lógnak rá a Visszavonás sorra (#464).** Mindhárom
  effekt-fül rácsa több gombot tartalmaz, mint amennyi a panel magasságába fér;
  eddig a csempék átfedtek a panel alján ülő Visszavonás/Újra gombsorral, és a
  fül alja levágódott. A rács mostantól saját, vágott görgethető területen ül.
- **A „Gyakori javítások" fül gombjai az eredeti sorrendjében (#464).** A
  tulajdonos képernyőképe alapján: Vágás · Kiegyenesítés · Vörösszem /
  Jó napom van · Automatikus kontraszt · Automatikus szín / Retusálás · Szöveg,
  és mindegyik alatt a Derítőfény-csúszka. A „Kreatív Kit" csempe **eltűnt** —
  az eredeti fülön nincs ilyen gomb (a jegy szövege tévesen sorolta fel).

## [0.6.76] – 2026-08-12

### Javítva
- **A Finomhangolás fül elrendezése az eredeti szerint (#464).** A tulajdonos
  négy képernyőképéről kiderült, hogy a fülön nincs szöveges fejléc, a
  csúszka-feliratok középen állnak, és az „egy gombnyomásos javítás" nem két
  nagy szöveges csempe a csúszkák fölött, hanem **két kis varázspálca-gomb**
  a csúszka-oszlop jobb szélén: az egyik a Kiemelések/Árnyékok párnál (a
  megvilágításhoz), a másik az „Alapszínválasztás" sorában (a színhez).
- Az **Alapszínválasztás** pipettája mellé bekerült a **kijelölt semleges
  színt mutató korong**, ahogy az eredetin is.

## [0.6.75] – 2026-08-11

### Belső
- **A hisztogram-vágópont számítása egyetlen helyre került (#549).** Az
  Automatikus kontraszt (közös) és a „Jó napom van"/csatornánkénti út eddig
  sorról sorra ugyanazt a lépéssort tartalmazta; a #539-es küszöb-finomítás
  így két helyen kényszerült volna módosításra. A viselkedés bájtra
  változatlan. (A jegy 2. és 3. pontja tárgytalanná vált: az ott leírt halott
  ág és float-egyenlőség az Auto Colour #541-es újraírásával eltűnt.)

## [0.6.74] – 2026-08-11

### Javítva
- **A négy Finomhangolás-csúszka újramérve valódi fotón (#551).** Eddig
  szintetikus szürke rámpákon mértünk, és ezért három csúszka modellje hibás
  volt. Az átlagos eltérés a Picasa saját kimenetétől (a JPEG-zaj szintje ~1):
  Kiemelések **23,15 → 1,06**, Árnyékok **19,41 → 0,76**, Derítőfény
  **18,10 → 5,89**, Színhőmérséklet (hideg irány) **20,94 → 5,08**.
- A **Kiemelések** és az **Árnyékok** valójában a fehér- illetve feketepontot
  mozgatja, nem csúcsfényt ment és árnyékot emel — a csúszkák felső határa
  ezért 0,48, a Picasa saját paramétertartománya szerint.
- A **Derítőfény** a pixel világosságától függ, nem a csatorna értékétől: két
  azonos világosságú, eltérő színű képpont ugyanazt a világosítást kapja.
  Emiatt a finomhangolás GPU-gyorsított élő előnézete nem nulla derítőfénynél
  a rendes (pontos) útra vált — a kép így mindig azt mutatja, ami mentődni fog.

## [0.6.73] – 2026-08-11

### Hozzáadva
- **Vörösszem-eszköz: automatikus ÉS kézi, egyszerre (#445).** Az eszköz
  megnyitásakor az automatika azonnal lefut az előnézeten, és kiírja, talált-e
  vörös szemet. Amit a gép kihagyott, azt a felhasználó a képre húzott
  négyzettel pótolhatja — tetszőleges számút, egyenkénti visszavonással és
  Alaphelyzet gombbal. A „Előnézet a kijelölő négyzetek nélkül" jelölőnégyzet
  csak a keretek rajzát tünteti el, a javításon nem változtat. Az Alkalmaz
  gomb ír csak lemezre, egyetlen visszavonható lépésként; Mégse esetén a
  mentett állapot érintetlen marad.
- A kézi négyzetek a `filters=` láncban a `redeye=1,<rect64>…` alakban élnek
  (PicasaPy-saját kiterjesztés, a retusálás bevált mintája szerint). Kézi
  négyzet nélkül a bejegyzés **bájtra a valódi Picasa `redeye=1;` alakja**,
  tehát a kétirányú kompatibilitás sértetlen.

## [0.6.69] – 2026-08-11

### Belső
- **A szerkesztő-panel forrása felbontva (#496).** A 2367 soros
  `EditorPanel.qml`-ből önálló fájlba került a három újrafelhasználható
  vezérlő (eszköz-csempe, panel-gomb, szín-választó), valamint a „Fotó
  vágása", a „Retusálás" és a „Szöveg" panel — **2367 → 1665 sor**. A
  felület viselkedése és a megjelenése változatlan.

## [0.6.68] – 2026-08-11

### Javítva
- **Gyűjtemény-nevek: hibaüzenet a néma elutasítás helyett (#461).** Üres vagy
  már foglalt névnél eddig egyszerűen nem történt semmi; most a névbekérő
  nyitva marad, és megmondja, mi a baj — az eredeti Picasa két külön
  üzenetével.
- **A gyűjtemény törlésének kérdése megnyugtatóan fogalmaz (#461):** kimondja,
  hogy a benne lévő mappák nem vesznek el, hanem a „Mappák a lemezen"
  gyűjteménybe kerülnek — ahogy az eredetiben.

## [0.6.67] – 2026-08-11

### Hozzáadva
- **Semleges szín pipetta a Finomhangolás fülön (#464).** A képre kattintva a
  kijelölt pont lesz a semleges szín — a négy csúszka érintetlen marad.
- A **Finomhangolás fülre visszakerült** az Automatikus szín és az
  Automatikus kontraszt gombja, ahogy az eredetiben is ott volt (szándékos
  ismétlés az első fülről, hogy hangolás közben kéznél legyen).

### Változott
- **A Visszavonás/Újra a panel alján, egyetlen példányban (#464).** Eddig
  mind az öt fül a saját (azonos) gombpárját rajzolta; az eredetiben a pár
  globális, nincs fülhöz kötve.

## [0.6.66] – 2026-08-11

### Hozzáadva
- **Arc-jelvények a bélyegképeken (#463).** A bal felső sarokban jelvény
  mutatja, ha a képen **felismert arc** van, és egy **külön** jelvény azt, ha
  **jóváhagyásra váró névjavaslat** vár rajta — vagyis elintézetlen dolgod van
  a képpel. A két állapot független egymástól, ahogy az eredetiben is. A
  méretarányok az eredeti Picasa réteg-adataiból (14×20 és 20×20).

## [0.6.65] – 2026-08-11

### Javítva
- **Fájlméret az eredeti Picasa magyar formátumai szerint (#526).** Eddig 1 MB
  alatt mindig KB-ban írtuk ki — egy 300 bájtos fájl így „0 KB" volt. Most a
  Picasa saját fokozatait követjük: **bájt és KB egész számra, MB-tól egy
  tizedes**, és megvan a GB/TB fokozat is.

### Megjegyzés
- A Picasa **teljes betűkészlete** (méret- és súlylétra) bekerült a
  stíluskonstansok közé (#526). Maguk a betűtípusok kereskedelmiek, nem
  szállíthatók; a szabad helyettesítő kiválasztása méréssel tartozik eldőlni,
  ezért egyelőre a rendszer alapértelmezése marad.
- A **dátum/idő magyar alakja tudatosan eltér** az eredetitől: a Picasa magyar
  szövegkészletében a dátumformátumok lefordítatlanul maradtak (angol
  sorrend, 12 órás idő) — ez fordítási hiányosság, nem szándékos alak.

## [0.6.64] – 2026-08-11

### Hozzáadva
- **Tulajdonságok-panel: 11 mező helyett a Picasa teljes mezőkészlete (#529).**
  A sorrend az eredeti Picasa saját beállítófájlját követi, és minden mező a
  Picasa magyar feliratát kapta (a program saját szótárából): fényképezőgép
  gyártmánya és típusa külön, **három külön dátum** (fényképezőgép,
  digitalizálás, módosítás), tájolás, vaku, objektív, 35 mm-es
  fókusztávolság, téma távolsága, fehéregyensúly, **fénymérés módja**,
  **exponálási program**, tömörítés, **színtér**, ICC-profil, beágyazott
  bélyegkép, kulcsszavak, **GPS-hármas** és egyedi azonosító. A felsorolt
  értékek is magyarul jelennek meg („Középsúlyos", „Rekesz-előválasztásos
  mód"), nem nyers EXIF-kulcsként. Az adat nélküli mező kimarad.

## [0.6.63] – 2026-08-11

### Javítva
- **Összeomlás-veszély a haladásjelzés cseréjekor (#519/#430).** A
  nyilvántartás lecserélésekor a régi példány felszabadulhatott, miközben
  egy korábban indított háttérszál még jelzett neki — ez Windowson
  hozzáférési hibával (0xC0000005), Linuxon szegmentálási hibával omlik
  össze. A régi példány mostantól életben marad, és leáll.

## [0.6.62] – 2026-08-11

### Javítva
- **Figyelmeztetés csak ott, ahol tényleg nincs visszaút (#465 4. pont).**
  A felirat bemásolása a szövegmezőbe eddig szó nélkül felülírta a beírt
  szöveget — mostantól rákérdez (üres mezőnél nem, ott nincs mit
  elveszíteni). A kártya kiürítésének figyelmeztetése az eredeti Picasa
  szerint **nagybetűs**. A Kukába helyezés továbbra sem ijesztget: az
  valóban visszafordítható.

## [0.6.61] – 2026-08-11

### Javítva
- **Mappakezelő: az eredeti elrendezés és két hiányzó figyelmeztetés (#543).**
  A dialógus mostantól pontosan fele-fele oszt (mint az eredeti), az
  állapot-választó süllyesztett keretbe került „A jelenlegi mappára:"
  felirattal, és van **Súgó** gomb is. A fában szöveges karakter helyett
  **rajzolt jelvény** mutatja az állapotot, és külön jelvény azt, ha a mappa
  az arcfelismerésből ki van hagyva. Az arcfelismerés-kapcsoló felirata
  vált (be/ki), és „Eltávolítás a Picasából" állapotú mappán szürke.
  Új figyelmeztetések: **teljes meghajtó figyelése** lassíthatja a
  rendszert, illetve **figyelt mappa eltávolításakor** a program
  figyelmeztet, hogy az oda később tett képek már nem kerülnek be maguktól.

## [0.6.60] – 2026-08-11

### Javítva
- **A „Jó napom van" szélső eseteken is pontosabb (#539).** A nagyon szűk
  hisztogramú (egyszínű, alacsony kontrasztú) képeket eddig túl agresszíven
  feszítettük ki. A mérés szerint a Picasa ilyenkor korlátozza a nyújtást —
  a 12 referencia-páron az eltérés **5,48 → 2,68**, és ebből a kiugró kép
  hibája **46,0 → 12,4**. A többi tizenegy kép kimenete bájtra változatlan.

## [0.6.59] – 2026-08-11

### Javítva
- **A HDR-ish végre azt csinálja, amit az eredeti (#545).** Az eltérés a
  valódi Picasa-kimenettől **11,2 → 2,45** (kilenc export; az érintetlen kép
  20,85 — vagyis a korábbi változat alig volt jobb a semminél). Két dolog
  hiányzott: az elmosás mértéke a `Sugár` csúszka **fele** (ezt a négy
  sugár-állás egymástól függetlenül ugyanígy adta), és a helyi kontraszt
  mellett az erősséggel arányos **világosítás** is fut. Ugyanez a motor
  hajtja a *Helyi kontraszt* effektet is, az is pontosabb lett.

## [0.6.58] – 2026-08-11

### Javítva
- **Az automatikus szín (Auto Colour) modellje megvan (#541).** A 12 képes
  mérőkészlet három dolgot mondott ki: az effekt tiszta csatornánkénti
  **erősítés** (a feketepont nem mozdul), és az erősítést a kép **semleges**
  (kevéssé telített) képpontjaiból számolt fehéregyensúly adja — a telített
  részletek (virág, égbolt) nem számítanak bele. Az eltérés a valódi
  Picasa-kimenettől **7,45 → 2,35**; az érintetlen kép 5,29, a mért
  erősítésekkel elérhető elméleti alsó korlát 1,08. A korábbi változat tehát
  rosszabb volt, mintha meg sem csináltuk volna az effektet — most a felére
  csökkent a hiba.

## [0.6.57] – 2026-08-11

### Javítva — a háttérszálas szerkesztő-render kódátvizsgálásának találatai
- **A lassú effekt már nem blokkolja a csúszkákat (#546).** A 0.6.55-ös
  megoldás egy közös záron sorosított: ha egy perces effekt renderelése
  közben a felhasználó csúszkát húzott vagy képet váltott, a felület megint
  megállt — csak most egy másik ajtón. A háttér-render mostantól saját,
  lokális munkaterületen dolgozik, közös zár nélkül.
- **Gyors kattintás-sorozat után az UTOLSÓ állapot látszik (#546).** Eddig a
  lemaradó, régebbi renderelés felülírhatta a frissebb képet.
- **A szerkesztő bezárása után a futó renderelés nem éled újra (#546):** a
  lezárt kép nem kerül vissza a gyorsítótárba, és nem frissíti a felületet.
- **Kilépés lassú effekt alatt (#547):** a program most érvényteleníti és
  megvárja a futó renderelést, így nem omolhat össze kilépéskor.
- **A renderelés hibája nem néma többé (#548):** naplózódik, és a felhasználó
  is kap jelzést róla (NAS-on a fájl a művelet közben eltűnhet).
- **A kék csík nem pöröghet örökre (#550):** ha a háttérszál elindítása
  elbukik, a jelzés is lezárul.

## [0.6.56] – 2026-08-10

### Javítva — öt effekt a valódi Picasa-kimenethez kalibrálva (#317)
A felhasználó hat új mérőkészletet exportált (ugyanaz a fotó, csúszkánként
külön mappa). Az effektek eltérése a valódi Picasa-kimenettől:

- **Vignette:** 2,66 → **0,70** (8 export; az érintetlen kép 14,4). Kiderült,
  hogy a ragyogás sugara a dokumentált képlet **fele**, és hogy a
  Lomo/Holga-nál mért 255-ös korlát ide **nem** érvényes.
- **Museum Matte:** a keret vastagsága **pixelben** értendő, nem a rövidebb
  oldal százalékában — eddig egy 2560 széles fotóra 1447 px-es keretet
  rakott 65 helyett (a kép 5454×4596-ra hízott). Most mind a hét export
  mérete pontos, az eltérés **2,01**.
- **Szépia:** 4,40 → **0,89** — a lineáris közelítés helyett a mért
  tónusgörbék.
- **Filtered B&W:** 6,11 → **0,36**. A szín itt **szűrő, nem festék**: a
  kimenet mindig szürke marad (mint a fényképészeti sárga/narancs/vörös
  szűrők), eddig tévesen színezte a képet.
- **Orton-ish:** 4,43 → **2,05** — az elmosás szigmája szintén a fele a
  dokumentáltnak, a fényerő-görbe kitérése pedig ±96 (nem ±75).

### Ismert korlát
- A **HDR-ish** modellje továbbra sem pontos (átlagosan 11,2 az érintetlen
  kép 25,3-ához képest): a mérés szerint globális S-görbe és
  telítettség-emelés is van benne, nem csak lokális kontraszt. Külön jegyen.

## [0.6.55] – 2026-08-10

### Javítva
- **A szerkesztő nem fagy be lassú effekt alatt (#514).** A mentett
  szerkesztési lánc újrarenderelése (effekt hozzáadása, vágás,
  visszavonás…) eddig a felület szálán futott: egy percekig számoló
  effekt alatt a program befagyottnak látszott, és az alsó kék
  haladásjelző csík sem tudott animálni. Mostantól háttérszálon fut, így
  a csík **magától** pörög, a felület pedig végig kezelhető marad. A
  csúszkák élő előnézete szándékosan azonnali (szinkron) maradt.

### Megjegyzés
- A **nyomtatásra készítés** (#514 másik fele) továbbra is a felület
  szálán fut — a Qt nyomtató-rajzolása nem tehető át háttérszálra
  ugyanezzel a mintával, ezért az külön jegyen folytatódik.

## [0.6.54] – 2026-08-10

### Javítva
- **Az effekt-fülek újra három oszlopban rajzolnak (#537).** A 3., 4. és 5.
  szerkesztő-fülön az effekt-csempék két oszlopba tördelődtek, miközben az
  eredeti Picasán — és nálunk az első két fülön — három oszlop van. A
  csempék sorrendje változatlan, csak a szélességük igazodik.

## [0.6.53] – 2026-08-10

### Javítva
- **Automatikus kontraszt (#540): mostantól gyakorlatilag pontos.** Az
  eredeti Picasa kimenetéhez mérve az eltérés **4,54 → 0,62** (12 kép
  közül **ötön bájtra azonos**). Kiderült, hogy ez a művelet **közösen**
  vágja mind a három színcsatornát — ezért nincs fehéregyensúly-hatása,
  tisztán a kontrasztot nyújtja.

### Ismert korlát — őszintén
- **Az automatikus szín (Auto Colour) modellje továbbra sem ismert.** A
  mérés szerint a mostani változat (7,45) és a korábbi (7,82) **egyaránt
  rosszabb, mintha a program meg sem csinálná az effektet** (5,29). A
  mérés azt is kizárta, hogy egyszerű szinthúzásról volna szó. A kód ezt
  kimondja, hogy senki ne hivatkozzon rá készként — a megfejtés külön
  jegyen (#541).

## [0.6.52] – 2026-08-10

### Javítva
- **A „Jó napom van" gomb végre azt csinálja, amit az eredeti (#535):** a
  felhasználó 12 kép-páros Picasa-exportjához mérve az eltérés
  **17,59 → 5,48**. A képek nagy részén ennél is pontosabb: **11 képen az
  átlagos eltérés 1,80**, egyetlen szélső eset húzza fel az átlagot.
- **Mostantól felismeri, mikor NE nyúljon a képhez.** Ha a kép már
  kihasználja a teljes világosság-tartományt, a gomb nem változtat semmit —
  eddig azt is felvilágosította, aminek nem kellett volna.
- **Ez az effekteken is átüt:** öt effekt (Holga, Éjjellátó, Ceruzarajz,
  Hatvanas évek, Cinemascope) a lánca elején ezt az automatikus korrekciót
  használja. A **Holga** eltérése az eredetitől **14,19 → 11,34**.

### Megjegyzés
- A modell a felhasználó referencia-exportjaiból lett megfejtve:
  csatornánként külön, lineáris szinthúzás. A vágási pontokat egyelőre
  rögzített százalékkal közelítjük — ez az egyetlen forrása a maradék
  eltérésnek.

## [0.6.51] – 2026-08-10

### Hozzáadva
- **Az arcfelismerés végre LÁTSZIK is (#26, 3. lépcső):** a bal hasábban az
  Emberek gyűjteményben megjelent a **„Névtelenek"** sor, benne a program
  által megtalált arcokkal, **arcok szerint csoportosítva**
  („Csoportosítás arc szerint" / „Csoportok kibontása").
- **Tömeges névadás:** jelöld ki a hozzád tartozó arcokat, és a **„Név
  hozzáadása"** egyszerre mindnek nevet ad. Az első névadásnál a személy
  megjelenik az **Emberek** gyűjteményben, a név pedig a kép melletti
  `.picasa.ini`-be íródik — ugyanazon az úton, amit a kézi arccímkézés is
  használ.

### Fontos garancia
- **A meglévő névcímkéidhez a program nem nyúl.** Az elnevezett arcok
  szerkezetileg kimaradnak a csoportosításból és a tömeges névadásból is.

### Ismert korlát
- A „Névtelenek" nézetben egyelőre a **teljes fénykép** látszik, nem a
  kivágott, szemvonalra igazított arc — ez külön munka.
- Ha a felismerő modell hiányzik, a „Névtelenek" sor egyszerűen nem jelenik
  meg; minden más változatlanul működik.

## [0.6.50] – 2026-08-10

### Hozzáadva
- **Arcfelismerés — 2. lépcső (#26): a program mostantól felismeri, hogy két
  arc ugyanazé az emberé.** A megtalált arcokhoz „lenyomat" készül, és az
  ismeretlen arcok **maguktól csoportokba rendeződnek** — ez lesz később a
  névadás alapja. Új futásidejű függőség nélkül, az OpenCV-be épített
  motorral.
- A csoportosítás **inkrementális**: egy új kép érkezésekor néhány
  összehasonlítás fut, nem éjszakai újraszámolás.

### Fontos garancia
- **A meglévő névcímkéidhez a program nem nyúl.** A gépi csoportosítás
  kizárólag a **névtelen** arcokon dolgozik — a Picasában felépített
  arccímkéket soha nem értékeli újra, és nem írja felül.

### Megjegyzés
- Ez a lépcső **még nem jelenik meg a felületen**; a névadás, az Emberek-
  albumok és a javaslatok a következő lépcsők. A felismerő modell fájlja
  nincs a programban — ha hiányzik, a lenyomat-számítás csendben kimarad,
  minden más változatlanul működik.

## [0.6.49] – 2026-08-10

### Javítva
- **A hibák eddig CSENDBEN eltűntek (#459):** a szinkron-, album-,
  helyadat- és arccímke-írás hibajelzései léteztek a programban, de
  **egyikük sem volt a felülethez kötve** — így a felhasználó soha nem
  értesült róluk. Mostantól közös hibasáv jelzi őket.

### Hozzáadva
- **Csak-olvasható fájl (#459):** a mentés előtt kiderül, ha a mappa nem
  írható, és a program az eredeti Picasa szövegével szól. *(Az automatikus
  mappa-másolás még nem érhető el — a párbeszéd ezt is kimondja, hogy ne
  maradjon megválaszolhatatlan kérdés.)*
- **Sérült kép (#459):** ha egy fájl nem tölthető be, a program felajánlja
  az **elrejtését** — nem törli, és a döntés a felhasználóé.
- **Kevés lemezhely (#459):** az export, a webexport és az importálás
  **indulás előtt** ellenőrzi a szabad helyet, és szól, ha kevés — így nem
  áll meg félúton.

## [0.6.48] – 2026-08-10

### Javítva
- **A szerkesztett képek kisképe sötétebb volt a nagy képnél (#525):** a
  program az effektet a **már kicsinyített** képre számolta, az eredeti
  Picasa viszont nagyban számolt, és csak utána kicsinyített. Mivel a
  vignetta sugarának felső korlátja rögzített képpontszám, kicsiben ugyanaz
  az effekt jóval szélesebb sötét karikát rajzolt. Mostantól a bélyegkép is
  nagyobb alapméreten készül. Az eredeti Picasa kimenetéhez mérve az
  eltérés **48,3 → 14,1** (Holga), illetve **55,0 → 8,3** (Lomo).
- A korábbi, hibásan sötét bélyegképek **maguktól frissülnek** — nem kell
  kézzel üríteni a gyorsítótárat.

### Megjegyzés
- A szerkesztett képek bélyegképe ezzel kb. **kétszer lassabban** készül el.
  Ez csak a szerkesztett fotókat érinti, háttérben fut, és egyszeri: a
  könyvtár böngészése nem lassul.

## [0.6.47] – 2026-08-08

### Javítva
- **A vignettás effektek most már az eredetihez hasonlítanak (#522, #504):**
  a ragyogás számítása egy közelítő trükk helyett zárt képlettel dolgozik,
  ahogy az eredeti művelet. Az eredeti Picasa kimenetéhez mérve az
  eltérés a **Holgánál 31,6 → 14,2**, a **Lomónál 14,6 → 8,6**
  (viszonyításul: az érintetlen kép eltérése 33,4 és 32,1).
- A **Vignette** tiszta fekete képpontjainak aránya nagy képen
  **8,2% → 0,1%** — a korábbi „befeketedő sarok" gyakorlatilag eltűnt.
- A számítás **sebessége nem romlott**, és már nem függ a ragyogás
  sugarától.

## [0.6.46] – 2026-08-08

### Hozzáadva
- **Az effektek csúszkái és vezérlői megjelentek (#516):** eddig a legtöbb
  effektet csak alapbeállítással lehetett használni. Mostantól 21 effekt
  kapott állítható vezérlőket az eredeti Picasa dokumentált értékei
  szerint — csúszkákat, jelölőnégyzeteket és színválasztókat.
- **Öt effekt eddig egyáltalán nem látszott a felületen** (Matte,
  Éjjellátó, Helyi kontraszt, Lekerekített szélek, Szemcse), pedig a
  motorban készen voltak — ezek most gombot kaptak.
- A képmérettől függő tartományok (sarok-lekerekítés, felirat-magasság) a
  tényleges képméretből számolódnak, nem rögzített értékek.

### Javítva
- **Az effekt-bélyegképek elronthatták a mentett beállításokat:** a
  bélyegkép-készítés minden paramétert számként írt ki, így a **színek és
  a ki/be kapcsolók sérültek** minden színt használó effektnél. Javítva.

## [0.6.45] – 2026-08-08

### Javítva
- **A fekete-fehér effektek színes kimenete (#504):** az eredeti Picasa
  Holga-exportjaihoz mérve kiderült, hogy a kimenetnek **tiszta
  szürkének** kell lennie (minden képponton R=G=B) — a receptben szereplő
  szín nem színez, hanem a szürkítés **csatornasúlyait** hangolja, mint egy
  színszűrő a fekete-fehér film előtt. A mi kódunk ezzel szemben színes
  képet adott. Javítva: a kimenet mostantól valódi szürkeárnyalatos.
  Mérve az eredeti kimenethez: az eltérés **71,0 → 31,6**.

### Ismert korlát
- A referencia-mérés szerint a teljes egyezéshez (~14,6) ez **nem elég**:
  a ragyogás számítási modelljét is le kellene cserélni a fizikailag
  pontosabb változatra, és külön eltérés van az automatikus
  színkorrekcióban is (a mienk sötétít, az eredeti világosít). Mindkettő
  külön munka — ld. #504 és #317.

## [0.6.44] – 2026-08-08

### Javítva
- **A vignettás effektek sötétsége nagy fényképeken (#504):** az eredeti
  Picasa felülről korlátozza a ragyogás sugarát, a mi számításunk viszont
  nem — ezért nagy képen az effektek jóval sötétebbek lettek a kelleténél.
  Eredeti Picasa-exportokhoz mérve: a kimenetünk átlagos eltérése a
  korlát nélkül **41,8**, a korláttal **9,0** volt (viszonyításul az
  érintetlen kép eltérése 32,1 — vagyis korlát nélkül rosszabbak voltunk,
  mintha meg sem csináltuk volna az effektet).
  A korlát mind a hat érintett helyre bekerült, **egy közös pontra**, hogy
  új effektnél se lehessen elfelejteni.
  Mérve, valódi fényképen: a **Holgánál** egy 4000×3000-es képen a tiszta
  fekete képpontok aránya **43% → 11%**, a **Lomónál** 2560 px-en
  **34% → 7%**, a **Vignette**-nél **19% → 7%**.

### Ismert korlát
- **Kis képeken (kb. 1000 képpont alatt) ez nem változtat semmit**, mert
  ott a számított sugár eleve a korlát alatt van. A Holga ilyen méretben
  továbbra is sötét; ennek okát Holga-referenciakép nélkül nem lehet
  eldönteni (a referenciakészlet ma csak a Lomóhoz létezik).

## [0.6.43] – 2026-08-08

### Javítva
- **Hisztogram-panel (#512):** a panel hibás barna hátteret kapott, és a
  görbe rajzterülete **ráfutott a fényképezőgép-adatokra**, ha azok több
  sorba törtek (magyarul jellemzően igen). A panel mostantól az eredeti
  szerinti világosszürke, elkülönülő világos rajzterülettel, és a
  területek elosztása szerkezetileg zárja ki az átfedést — tetszőleges
  hosszúságú szöveg mellett is.
- **Indulási QML-figyelmeztetés (#506):** a szöveg-eszköz színválasztója
  olyan nevet használt, ami ütközött a Qt beépített nevével. Átnevezve; a
  figyelmeztetés eltűnt. A tesztek figyelmeztetés-őre mostantól **elkapja
  ezt a hibaosztályt**, így nem térhet vissza észrevétlenül.

### Dokumentáció
- A `histogram-reference.md` a panel hátterét tévesen dokumentálta
  (innen ered a #429-es barna háttér). A téves sor korrekciós jegyzetet
  kapott, hogy ne lehessen rá tényként hivatkozni.

## [0.6.42] – 2026-08-08

### Megjegyzés
- **Az effekt-színek rendben vannak (#510):** felmerült, hogy három effekt
  (Holga, CrossProcess, NightVision) színénél fel van cserélve a piros és a
  kék. Méréssel kiderült, hogy **nincs hiba**: az effekt-lánc szándékosan
  RGB-térben dolgozik, a be- és kilépési pontok pedig átváltanak. A Holga
  kimenete a valódi feldolgozási úton meleg vörös, ahogy az eredetiben is.
  Az érintett függvények leírása mostantól **kimondja** a színsorrendet,
  hogy ez ne okozzon újabb félreértést.
- **A „Holga-szerű" effekt sötétsége nem programhiba (#504):** a lánc
  minden lépése az eredeti Picasa dokumentált receptje szerint fut. A
  sötétség az effekt hangolásának kérdése (#317), nem hibás számításé.

### Hozzáadva
- Az öt vignettát használó effektre (Lomo, Holga, Vignette, Matte,
  NightVision) **valódi fényképpel** futó tesztek: színsorrend,
  méretfüggetlenség és futásidő-korlát.

## [0.6.41] – 2026-08-08

### Hozzáadva
- **Az alsó kék csík mostantól minden hosszú műveletnél animál (#505):**
  eddig csak a beolvasás és a bélyegkép-betöltés alatt jelzett, minden más
  némán futott. A jelzés egyetlen közös ponton, a háttérmunkák indításánál
  került be, ezért **minden** háttérművelet magától megkapja — a kötegelt
  effektek, az export, az importálás, a duplikátum-keresés, a webexport, a
  csillagozás/forgatás és az arc-szkennelés is. Rövid műveletnél nem
  villan fel (0,3 mp késleltetés), és ha megjelent, nem tűnik el azonnal.
- Ha egy háttérművelet **hibával áll le**, a jelzés akkor is lezárul — a
  csík nem marad örökre pörögve.

### Ismert korlát
- **A szerkesztő effektjei (köztük a Polaroid) továbbra sem jeleznek**,
  mert a képszámítás a felhasználói felület szálán fut. Ott a csík nem is
  tudna animálni. Ugyanez vonatkozik a nyomtatásra készítésre. Ezek
  áthelyezése háttérszálra külön munka.

## [0.6.40] – 2026-08-08

### Javítva
- **Kétszer megjelenő mappa (#507):** ha ugyanazt a mappát két, kicsit
  másképp leírt útvonalon vetted fel figyelésre (szimbolikus linken
  keresztül, vagy `..` szegmenst tartalmazó úton), a program két külön
  bejegyzésként kezelte. Mostantól minden útvonal egységesen normalizálódik
  — Windowson kis-nagybetűtől függetlenül, Linuxon a fájlrendszer
  szabályai szerint.
- **A már meglévő duplikátumok összevonása:** indításkor a program egyszer
  összevonja a korábban duplán bekerült mappákat. Az összevonás
  **adatvesztés nélküli**: ha egy fotónál mindkét oldalon eltérő, valódi
  szerkesztés áll (csillag, felirat, kulcsszó, szűrő, helyadat), akkor a
  program **inkább meghagyja a duplikátumot**, mint hogy bármit felülírjon.

## [0.6.39] – 2026-08-08

### Javítva
- **A „Lomo-szerű" effekt fekete képe és a befagyás (#504):** az effekt
  kimenete teljesen fekete lett, az alkalmazása pedig percekre
  megbénította a programot — és mivel az effekt minden megnyitáskor
  újraszámolódik, az így mentett kép sem nyílt meg. **A képek nem
  sérültek meg**, csak a számítás akadt el. Mindkét ok javítva: a
  vignetta-számítás nagy sugárnál az egész képet befeketítette, a nagy
  elmosás pedig a képmérettel robbanásszerűen lassult.
  Mérve: a Lomo kimenetének átlagos fényessége 0,0 → 52,0, a futásideje
  2000×1500-as képen **37 s → 0,87 s**; a Holgáé 14,6 s → 1,1 s.

### Ismert korlát
- A „Holga-szerű" effekt már nem feketedik és nem lassú, de **továbbra is
  nagyon sötét**. Ez nem a fenti hiba maradéka, hanem az effekt
  hangolásának kérdése (a vignetta sugarai nincsenek dokumentálva az
  eredetiből) — külön munka, ld. #504.

## [0.6.38] – 2026-08-08

### Hozzáadva
- **Arcfelismerés — első lépcső (#26):** megjelent az arcok automatikus
  megtalálásának alapja. A felismerő az OpenCV-be épített motorra épül,
  **új függőség nélkül**, és a Picasáéval azonos öt arcpontot adja, amiből
  a szemvonalra igazított arc-indexkép készül. **A meglévő névcímkéidhez
  nem nyúl:** ahol már van ember által adott név, ott a program nem
  detektál újra — a Picasában felépített arccímkék érintetlenek maradnak.
- A felismerő modell fájlja **nincs a programban**, külön lépésben
  szerezhető be. Ha hiányzik, az arcfelismerés **csendben kikapcsol**, és
  minden más változatlanul működik.

### Megjegyzés
- Ez a lépcső még **nem jelenik meg a felületen** — a csoportosítás, az
  elnevezés és a javaslatok a következő lépcsők.

## [0.6.37] – 2026-08-08

### Hozzáadva
- **Importálás az eredeti munkamenete szerint (#441):**
  - **Célmappa neve három módban** — kézi név, **a felvétel dátuma szerint
    külön mappákba bontva** (ez a Picasa importjának a lelke), vagy a mai
    dátum. A korábbi, szabad szöveges sablon-mezőt ez váltja fel.
  - **„Duplikátumok kizárása"** — a már importált képek kimaradnak, és az
    előnézet kiírja, hány ilyen van.
  - **Egyenkénti válogatás** — a bélyegképeken ki/be kapcsolható, mi jöjjön
    át; plusz „Összes kizárása" / „Összes felvétele".
  - **„Másolás után:" három állapot** — a forrás érintetlenül hagyása, csak
    az átmásolt képek törlése, vagy minden törlése. A két törlő állapothoz
    az eredeti kétlépcsős, egyre erősebb figyelmeztetése tartozik.

### Javítva
- **Az importálás nem törölhet át nem jutott fájlt:** ha a másolás közben
  néhány fájl elbukik, a „minden törlése" ezentúl meghagyja őket a
  forráson — korábban azok is törlődtek volna, pedig épp azok nem kerültek
  át. A törlés továbbra is csak sikeres másolás után fut le.

## [0.6.36] – 2026-08-08

### Módosítva
- **Retusálás az eredeti munkamenete szerint (#445, első lépcső):** a
  foltozás eddig egyetlen kattintással, fix méretű négyzetes területen
  dolgozott. Az eredeti Picasában ez **irányított klónozás** volt: az első
  kattintás kijelöli a javítandó foltot, az egeret mozgatva **élőben
  látszik, mivel fogja pótolni**, a második kattintás pedig véglegesíti.
  Mostantól nálunk is így működik, **kör alakú, állítható méretű ecsettel**
  („Brush Size"), és a foltok **egyenként visszavonhatók** („Undo Patch" /
  „Redo Patch" / „Reset").
- A mentési formátum foltonként rögzíti a cél-pontot, a forrás-pontot és a
  sugarat. A korábbi, téglalapos alakkal mentett szerkesztések továbbra is
  betölthetők és megjelennek — nem vesznek el.

## [0.6.35] – 2026-08-08

### Hozzáadva
- **Vágás: az eredeti képarány-készlet és saját arányok (#448, első
  lépcső):** a vágás-panel arány-listája az eredeti Picasa tényleges
  kulcskészletét követi (4x4, 4x3, 4x6, 5x7, 8x10, 5x3, 9x13, 10x15,
  13x18, 5x8, 16x10, 16x9, négyzet, A4). Mostantól **saját képarány is
  felvehető névvel** (szélesség × magasság), és törölhető is; a program
  megjegyzi a **legutóbb használt arányt**.
- **Figyelmeztetés a kiegyenesítés után:** ha a képen már van
  kiegyenesítés, a vágás-panel az eredeti Picasa szövegével figyelmezteti
  a felhasználót, hogy a vágás pontatlan lehet.

## [0.6.34] – 2026-08-08

### Hozzáadva
- **Mappakezelő: negyedik, önálló arcfelismerés-kapcsoló (#449):** az
  eredeti Picasában a mappa beolvasási állapota (Folyamatos figyelés /
  Egyszeri beolvasás / Eltávolítás) mellett egy **tőlük független**
  kapcsoló döntötte el, hogy az adott mappában fusson-e az arcfelismerés.
  Ez eddig teljesen hiányzott; mostantól a Mappakezelőben külön
  jelölőnégyzet, kikapcsoláskor az eredeti szövegű rákérdezéssel. A
  beállítás a Picasával azonos formátumú `FRExcludeFolders.txt`-be kerül.
  *(Arcfelismerés-motor még nincs a projektben, így a kapcsoló egyelőre a
  kizárási szándékot rögzíti — arcok és névcímkék törlése nem történik.)*

### Javítva
- **Félrevezető dokumentáció az `FRExcludeFolders.txt`-ről:** a
  funkciótérkép azt állította, hogy a fájl a teljes indexelésből zárja ki
  a mappákat. Valójában kizárólag az arcfelismerést érinti — és a program
  korábban egyáltalán nem is használta a fájlt.

## [0.6.33] – 2026-08-08

### Hozzáadva
- **Szöveg-eszköz: kitöltés + körvonal, átlátszóság, felirat-átvétel
  (#450, első lépcső):** a felirat eddig egyetlen színnel készült, így
  tarka hátterű képen olvashatatlan volt. Mostantól külön választható a
  **kitöltés** és a **körvonal** színe, állítható a körvonal vastagsága és
  a szöveg átlátszósága, és bekapcsolható a **csak körvonalas** felirat.
  Két új gomb: a **„Felirat átvétele"** egy kattintással beteszi a kép
  meglévő feliratát a szövegmezőbe, a **„Minden meglévő szöveg törlése"**
  pedig eltávolítja a képre írt szöveget.

## [0.6.32] – 2026-08-08

### Hozzáadva
- **Kuka vs. végleges törlés megkülönböztetése (#457, 1. pont):** a törlés
  eddig minden esetben azt írta, hogy a kép „a rendszer lomtárába kerül" —
  hálózati megosztáson (NAS) azonban a lomtár jellemzően nem elérhető.
  Mostantól a program megnézi, van-e valódi lomtár az adott meghajtón (a
  freedesktop-szabvány szerinti mount-specifikus lomtárat is beleértve), és
  ha nincs, az eredeti Picasa 3 szövegével figyelmeztet: a törlés azonnali
  és nem vonható vissza. Ez a figyelmeztetés külön kulcsot kapott, így a
  „ne kérdezze újra" beállítás a lomtáras esetnél nem némítja el.

## [0.6.31] – 2026-08-08

### Javítva
- **A szerkesztő első fülének gombsora az eredeti szerint (#464):** az
  „Automatikus szín" és az „Automatikus kontraszt" gomb sorrendje fordított
  volt a Picasa 3-hoz képest, és hiányzott a „Kreatív Kit" gomb. Mindkettő
  javítva.
- **Kötegelt effektus: a művelet üres kijelölésnél sem hallgat el:** a
  nem-dolgozó ágak eddig jelzés nélkül tértek vissza, így a hívó örökre
  várt a befejezésre. A tesztek mostantól hangos, leíró hibaüzenettel
  buknak el, ha egy Qt-jel nem érkezik meg.

## [0.6.30] – 2026-08-08

### Hozzáadva
- **„Összes szerkesztés visszavonása" (#465):** a Kép menü eddig szürke
  pontja mostantól működik — a kijelölt képek teljes szerkesztési láncát
  törli, megerősítés után. A művelet egy lépésben visszavonható, és a
  visszavonás a vágást is helyreállítja.

## [0.6.29] – 2026-08-08

### Hozzáadva
- **Képtálca: a képek mappaváltás után is megmaradnak (#455, első lépcső):**
  az alsó sáv eddig csak a pillanatnyi kijelölést tükrözte, így mappát váltva
  minden elveszett. Mostantól a „Megtartás" gombbal több mappából
  gyűjthetők össze képek; a megtartottakat zöld tű jelöli a rácsban, és a
  tálca ürítése rákérdez.

## [0.6.28] – 2026-08-08

### Javítva
- **Hisztogram-panel az eredeti arculatával (#429):** a panel a Picasa meleg
  barna hátterét kapta, a görbe alatt elkülönített fehér rajzterülettel. A
  fényképezőgép neve is az eredeti szerint jelenik meg (a „NIKON
  CORPORATION" mostantól „NIKON").

## [0.6.27] – 2026-08-07

### Hozzáadva
- **Geo-jelvény az indexképeken (#463):** a helyadattal rendelkező képek a
  jobb alsó sarokban piros pin-jelvényt kapnak, mindhárom nézetben.

### Javítva
- **A véletlenszerű összeomlások forrása mind a tíz vezérlőben megszűnt
  (#438):** a háttérben futó műveletek szálai mostantól bevárhatók, közös
  megoldással. Ez a #430-ban javított hiba maradéka volt — ugyanaz a minta
  a program több pontján is megvolt, és időnként összeomlást okozott.

## [0.6.26] – 2026-08-07

### Hozzáadva
- **Gyűjtemény jobbklikk-menüje (#422):** átnevezés és eltávolítás
  (megerősítéssel) a bal panel gyűjtemény-fejlécén. Ezzel az eredeti mind a
  nyolc kontextusmenüje megvan.
- **Csoportos szerkesztés (#425):** a Szerkesztés menü almenüje eddig üres
  és letiltott volt; mostantól hét egykattintásos effektus és a forgatás
  alkalmazható egyszerre a teljes kijelölésre — háttérben, haladásjelzéssel,
  megszakíthatóan, egy lépésben visszavonhatóan.

### Javítva
- **Az effektus-másolás nem viszi át a vágást (#426):** a menü eddig a régi
  motorra hívott, ami a kép-specifikus vágást is átmásolta volna. Emellett a
  „Csillagozottak kijelölése" eddig a nézet szűrőjét váltotta át, ahelyett
  hogy a csillagos képeket kijelölte volna.

## [0.6.25] – 2026-08-07

### Hozzáadva
- **A saját gyűjtemények végre látszanak (#476):** eddig létre lehetett hozni
  egy gyűjteményt és mappákat tenni bele, de utána sehol nem jelent meg.
  Mostantól a bal panelen saját, csukható fejlécet kap, alatta a benne lévő
  mappákkal.

## [0.6.24] – 2026-08-07

### Javítva
- **Megbízhatóbb tesztek (#475):** a háttérműveletre váró teszt-segéd eddig
  csendben továbbengedte a tesztet, ha a művelet nem fejeződött be időben —
  a hiba így máshol, félrevezető üzenettel bukott ki. Mostantól beszédes
  hibát ad, és a türelmi idő a lassú gépekhez igazodik. A javítás rögtön
  kimutatott egy rejtett hibát az egyik saját tesztünkben is.

## [0.6.23] – 2026-08-07

### Hozzáadva
- **Album és Emberek-album jobbklikk-menüje (#422):** a bal panel album-,
  illetve személy-során. Élő a kijelölés-parancsok, az indexképek
  frissítése és a HTML-export; az album törlése/leírása, a névcímkék és a
  webes műveletek — az eredetihez hűen — szürkén láthatók.

## [0.6.22] – 2026-08-07

### Hozzáadva
- **Három új jobbklikk-menü (#422):** a bal panel üres részén a mappalista
  rendezése (dátum, név, méret, legutóbbi változtatás, fordított sorrend);
  a címkéken a címke rátétele a teljes kijelölésre, az ilyen címkéjű képek
  keresése és a címke eltávolítása; a képtálcán a kijelölés megtartása,
  illetve eltávolítása. Egyik menü sem létezett eddig.

## [0.6.21] – 2026-08-07

### Hozzáadva
- **Indexkép jobbklikk-menüje: 7 helyett 19 parancs (#422):** megjelenítés
  és szerkesztés (félkövéren, mint a duplakattintás művelete), forgatás
  mindkét irányba a teljes kijelölésre, fájl megnyitása, teljes elérési út
  másolása és tulajdonságok. A még nem működő parancsok — az eredetihez
  hűen — szürkén láthatók maradnak.
- **Törlés-gyorsbillentyű az eredeti szerint:** a rácsban `Ctrl+Delete`, a
  nézőben sima `Delete` törli a lemezről; a kettő kizárja egymást.

### Megváltozott
- **Az „Átnevezés…" a helyére került (#422):** kikerült a rács jobbklikk-
  menüjéből, mert az eredetiben a Fájl menüben van — ott (és `F2`-vel)
  változatlanul elérhető.
- **Elrejtés/Megjelenítés (#422):** a menüpont mostantól feliratot vált
  pipa helyett, ahogy az eredeti.

## [0.6.20] – 2026-08-07

### Hozzáadva
- **Mappa jobbklikk-menüje: 2 helyett 15 parancs (#422):** kijelölés-
  parancsok, indexképek frissítése, a mappa rendezésének alapja, keresés a
  lemezen, eltávolítás a Picasából (megerősítéssel) és HTML-export. A menü
  mostantól — az eredetihez hűen — **három helyről** nyílik ugyanazzal a
  tartalommal: a bal panel mappa-sorából, a rács üres területéről és a rács
  mappa-fejlécéből.
- **„Mappaleírás szerkesztése…" ablak:** az eredeti Picasa mezősorával
  (név, dátum + automatikus dátum, zene, a felvétel helye, leírás).

### Megváltozott
- **A mappa dátuma a helyére került (#422):** eddig külön menüpont volt a
  mappa jobbklikk-menüjében, az eredetiben viszont a „Mappaleírás
  szerkesztése…" ablakban van. A funkció nem veszett el, csak oda költözött,
  ahol a Picasában is található.

### Javítva
- Két megerősítő ablak együtt már nem zavarja egymást.

## [0.6.19] – 2026-08-07

### Hozzáadva
- **Jobbklikk-menü a nézőben (#422, 1. lépcső):** a nagy képen eddig
  egyetlen kontextusmenü sem nyílt — most megvan az eredeti Picasa mind a
  17 parancsa, a hivatalos magyar feliratokkal. Élesben működik a
  visszatérés a könyvtárhoz, a hozzáadás albumhoz, a forgatás jobbra/balra,
  az elrejtés–megjelenítés, a fájl megnyitása, a keresés a lemezen, a
  törlés lemezről, a teljes elérési út másolása és a tulajdonságok. A még
  nem működő parancsok — az eredetihez hűen — szürkén láthatók maradnak,
  hogy a menü magassága és a tételek helye soha ne ugráljon.

## [0.6.18] – 2026-08-07

### Javítva
- **Véletlenszerű CI-összeomlás megszűnt (#430):** a weboldal-exportálás
  háttérszála eddig akkor is dolgozhatott, amikor a hozzá tartozó objektumot
  már felszámolta a program — ilyenkor a folyamat összeomlott. A szálat
  mostantól be lehet várni, és a teszt le is várja: a hiba forrása
  minimál-programmal reprodukálva és igazoltan megszüntetve. Ugyanez a minta
  további kilenc vezérlőben is jelen van, a javításuk külön feladat (#438).

## [0.6.17] – 2026-08-07

### Javítva
- **A felső eszközsáv nem törik új sorba (#423):** az „Importálás" gomb
  minden ablakszélességen a sáv bal szélén marad — a hely fogytával előbb a
  rugalmas térköz, majd a keresőmező zsugorodik, végül a szűrő-zóna rejtőzik
  el, a sáv magassága viszont változatlan. A „Szűrők" felirat a csíkon belül,
  az ikonsor fölé került.

### Hozzáadva
- **Mappa-fejléc paritás (#423):** cím Georgia 20 pt, dátumsor Georgia 14 pt,
  50 px bal behúzás; hosszú mappanév halványuló kifutással ér véget („…"
  helyett), a jobb-felső sarokban pedig megjelent a „Szinkronizálás az
  internettel" kapcsoló (az elrendezés része, egyelőre letiltva). A menüsáv
  jobb szélén a „Bejelentkezés Google Fiókkal" hivatkozás.

## [0.6.16] – 2026-08-07

### Hozzáadva
- **Az összes effektus másolása/beillesztése (#426):** egy kép teljes
  szerkesztési lánca átvihető tetszőleges számú másik képre — mappánként
  egyetlen `.picasa.ini`-írással, és a teljes köteg egyetlen visszavonási
  lépésként. Amit nem visz át (kivágás, retus, vörösszem, klip-vágópontok),
  azt nem kézi lista, hanem a `filterdesc` regiszter `mode`/`persist`
  jelzőiből származó gépi szabály dönti el. A menüpontok bekötése még
  hátravan, ezért a jegy nyitva marad.

## [0.6.15] – 2026-08-07

### Hozzáadva
- **Helyfoglaló menüpontok jelölése (#416):** a még nem működő menüpontok
  halványabb felirattal és a sor jobb szélén kicsi, világosszürke ponttal
  jelennek meg — ránézésre látszik, mi működik már és mi csak a helye.

### Javítva
- **Derítőfény-csúszka méretugrása (#415):** a húzás alatt megjelenő
  GPU-előnézet a kép befoglaló dobozához igazodott a ténylegesen kirajzolt
  kép helyett, ezért álló képnél a lap széléig szétnyúlt, majd elengedéskor
  visszaugrott. Az előnézet mostantól pontosan a kirajzolt képet fedi.
- **Tálca-teszt a windows-CI-n (#417):** a „széles ablak" eset fix 1280 px
  helyett a komponens mért küszöbéből származik, így betűkészlet- és
  nyelvfüggetlen.

## [0.6.14] – 2026-08-06

### Javítva
- **Szerkesztő-panel szélessége (#411):** fix 280 px, mint az eredetiben —
  a feliratok nem tördelődnek szét.
- **„Gyakori javítások" fül ikonjai (#411):** a felhasználó képe helyett
  saját rajzú ikonok (sötét fotónál a képes csempék egyformák voltak);
  a Kiegyenesítés ikonon segédvonal-rács; fekvő 3:2 arány.
- **A felezett ikonokon LÁTSZIK az effekt (#411):** a Qt SVG-motorja
  némán kihagyta a vágást, ezért a két fél azonos volt; a féloldalak
  mostantól matematikailag elmetszettek, a színek az eredeti ikonokon
  mért arányokból számítva.
- **Derítőfény (#411):** az ikon és a csúszka egy sorban, összetartozó
  egységként, mint az eredetiben.

## [0.6.13] – 2026-08-06

### Javítva
- **Picasa-hű szerkesztő-panel (#405):** az effekt-gombok mostantól a
  SAJÁT KÉPED kis előnézetét mutatják az adott effekttel (mint az
  eredetiben), nem lapos ikont; a fölösleges „Gyakori javítások" fejléc
  eltűnt; a panelarányok, fül-ikonok, a Visszavonás/Újra és a
  Derítőfény-csúszka az eredetihez igazítva.

## [0.6.12] – 2026-08-06

### Javítva
- **Alsó sáv reszponzivitása (#406):** szűk ablaknál (pl. fél képernyő)
  a gombok már nem lógnak ki — a feliratok helyett ikonok jelennek meg,
  a csúszka zsugorodik. A váltás a feliratok TÉNYLEGES szélességét méri,
  így nyelvtől és rendszerbetűtől függetlenül sosem vág le semmit.

## [0.6.11] – 2026-08-06

### Javítva
- **GPU-shader betöltés (#402):** a shader rossz mappában kereste a
  .qsb fájlt — a GPU-előnézet most már ténylegesen elindul; hiba esetén
  némán a CPU-útra áll vissza, napló-zaj nélkül.
- **Arc-szerkesztő (#402):** a névjavaslat-lista QML-horgony-
  figyelmeztetése megszűnt.

## [0.6.10] – 2026-08-06

### Hozzáadva
- **Arc-téglalapok szerkesztése (#26, 2. kör):** a nézőben rajzolható,
  nevezhető és törölhető arc-keretek, Picasa-kompatibilis mentéssel;
  opcionális contacts.xml-import.
- **GPU-előnézet élesítve (#22):** a finomhangolás-csúszkák húzás közben
  GPU-n frissülnek (ahol van rá mód — enélkül minden a régi úton megy).
- **Nyomtatás és E-mail (#32, részleges):** a tálca Print/E-Mail gombjai
  működnek (oldalhoz igazított nyomtatás; küldés a leveleződdel).

## [0.6.9] – 2026-08-06

### Hozzáadva
- **Személyek-gyűjtemény (#26, 1. kör):** a bal hasáb Személyek listája a
  meglévő `.picasa.ini` arc-adatokból; személyre kattintva az ő képei.
- **GPU-előnézet alapok (#22):** shader-alapú élő előnézet a
  leggyakoribb csúszkákra (derítőfény/árnyék/színhő/telítettség/f-f),
  bitre a CPU-útból származó paritással — RPi5-validálásra vár.
- **Effekt-névlista lezárva (#347):** grain v1 egzakt csővezetékkel;
  a maradék mérnivaló a #317-es golden-körben.

## [0.6.8] – 2026-08-06

### Hozzáadva
- **Egzakt effekt-csővezetékek (#381):** a 4–5. effektfül a Picasa eredeti,
  a filterdesc.xml-ből megfejtett lépéssorai és számértékei szerint
  renderel — a korábbi közelítések helyett.
- **Szűrő-regiszter (#382):** mind a 84 eredeti szűrő adatvezérelt
  leírása; tartomány-validáció, teljes-felbontás/lassú/méretváltó
  jelzők a láncban; 26 további régi szűrőnév felismerve.
- **Szín szerinti keresés (#383):** color:-keresőtokenek + átlagszín-index
  (az elveszett Picasa-funkció visszahozása).
- **UI-hűség (#384):** a mappalista három kék állapota, kétszínű
  indexkép-kijelölés-keret az eredeti constants.ui értékei szerint.

## [0.6.7] – 2026-08-06

### Hozzáadva
- **Retusálás és szöveg a szerkesztőben (#148):** kattintásos folt-
  eltávolítás élő előnézettel; szöveg felvitele a képre.
- **Beállítások-dialógus (#350):** a Picasa 8 fülös beállítás-ablaka;
  élőben a nyelv és a törlés-megerősítés, a többi előkészítve.
- **Exportálás weboldalként (#351):** a Picasa sablonnyelvének teljes
  motorja + „fehér" gyári sablon.
- **Egyéni gyűjtemények és kézi mappadátum (#320):** saját gyűjtemények
  a mappafában; a mappa éve kézzel felülírható.

### Javítva
- Indulási QML-figyelmeztetés a MoveDatabaseDialogban (#377).

## [0.6.6] – 2026-08-06

### Hozzáadva
- **A Picasa 3.9 telepítés mély elemzése — négy új/megoldott formátum.**
  - `docs/specs/filterdesc-registry.md`: a Picasa saját szűrő-regisztere
    (`runtime/filterdesc.xml`) feldolgozva — mind a 84 szűrő csúszkáinak
    neve, tartománya és alapértéke, valamint a 33 Glimmer-effekt teljes
    képfeldolgozó-csővezetéke. Lezárja a „4–5. effektfül paraméterei" és a
    „Vignette analitikus modellje" nyitott pontokat.
  - `docs/specs/picasa-respack-format.md` + `tools/picasa/respack.py`: a
    `respack.yt` bináris erőforráscsomag formátuma **teljesen visszafejtve**
    (2769/2769 réteg hibátlanul kicsomagolható), és előkerült benne a Picasa
    UI **140 `.tre` elrendezés-forrásfájlja**.
  - Az arc-részletadat (`conf/pan/leye/reye/mouth`) formátuma és forrása
    (Neven Vision motor a `Red.dll`-ben) dokumentálva.
  - A `constants.ui` hiteles UI-konstansai bekerültek a dizájn-kézikönyvbe;
    a `Picasa3i18n.dll` 41 nyelvű string-táblájának veszteségmentes
    kinyerési módszere rögzítve.

## [0.6.5] – 2026-08-05

### Hozzáadva
- **Tömeges átnevezés (#366)** a Picasa mintája szerint: dátum-/felbontás-
  utótag, élő példa-előnézet, sorszámozás; több kijelölt képnél automatikusan.
- **„Ne kérdezze újra" (#367):** újrafelhasználható megerősítő dialógus
  perzisztens beállítás-tárral; a törlés-megerősítés már ezt használja.
- **Adatbázis áthelyezése (#368):** Eszközök → Kísérleti → Adatbázis
  áthelyezése… — biztonságos költöztetés integritás-ellenőrzéssel; hiba
  esetén minden marad a régiben.
- **Export-extrák (#369):** exportmappa-név, sorszámozás, vízjel,
  minőség-presetek az eredeti Picasa export-dialógusa szerint.

## [0.6.4] – 2026-08-05

### Hozzáadva
- **Retusálás-eszköz alapjai (#148):** folt-eltávolítás OpenCV-inpainttel a
  render-láncban, `.picasa.ini`-kompatibilis tárolással; szöveg-réteg
  parse/serialize + közelítő rajzoló.
- **Saját, Picasa-hű SVG ikonkészlet (#361):** a tálca és az eszköztár
  ikonokat kapott (a Kollázs/Film a tálcáról is indítható); a geo-szűrő
  igazi ikonnal.
- **Dialógus-paritás 1. kör (#350):** átnevezés- és export-dialógus a FEN-
  forrás szerinti feliratokkal; mappafa-finomítások (#320).

### Javítva
- **A 4. fül effekt-paraméterei mostantól eljutnak a rendererhez (#332)** —
  az importált Picasa-szerkesztések nem az alapértékkel renderelődnek.
- **A név-kizárólista miatt üres scan nem számít „elérhetetlen gyökérnek"
  (#358)** — a kizárt mappák indexbejegyzései kitakarítódnak.
- **Az app-ikon ténylegesen nagyobb (#325)** — a korábbi hamis-zöld
  mérőszám helyett pixel-terület-alapú teszttel.

## [0.6.3] – 2026-08-05

### Javítva
- **Éles ini-kompatibilitás (#357):** a `tint`/`ansel`/`dir_tint` szín-
  paramétere opcionális — a Picasa elhagyja, ha az alapértelmezett színnel
  mentett. Eddig ezek az effektek hibával kimaradtak a renderelésből
  (a felhasználó effekt nélkül látta a képet, traceback-spammel); mostantól
  a dokumentált alapértékkel (fehér) futnak.

## [0.6.2] – 2026-08-05

### Hozzáadva
- **Az eredeti Picasa 3.9 programmappa teljes feldolgozása (#345).** Négy új
  spec: a 46 dialógus FEN-szerkezete, az exe ini-kulcs/effekt-leltára, a
  PBZ-gombok + webexport-sablonnyelv, és a hivatalos Picasa-magyar
  terminológia (#346–#351 jegyek ebből).
- **Szkenner-kizárólista** az eredeti `filters.txt` mintájára (#349): a
  `windows`, `temp`, `Originals`, `.picasaoriginals` stb. mappák kimaradnak
  a bejárásból — a szerkesztési eredetik nem duplikálódnak a rácsban.
- **Új effekt-nevek felismerése** a render-láncban (#347 1. lépés): a
  `grain`, `radtint`, `RoundedEdges`, `Matte`, `NightVision` felismerten
  kalibrálatlan, a „nem renderelhető" jelentésbe számít; a `picnik=1;`
  érvényes jelző-token.

### Javítva
- **Hivatalos Picasa-magyar terminológia (#346):** People→Személyek,
  „Készítsen képfeliratot!", Fókusztávolság, Indexképek és további
  szótári igazítások (15 felirat).
- Az exe-ből azonosított új ini-kulcsok (`[encoding]`, verziókulcsok,
  `hidden`, `moviestart`…) round-trip megőrzése teszttel rögzítve (#348).

## [0.6.1] – 2026-07-31

### Hozzáadva
- **Albumtagság szerkesztése (#9 második fele).** A képek jobbklikk-menüjéből
  mostantól **albumba tehetők** („Hozzáadás albumhoz" — a meglévő albumok
  listájával és „Új album…" ponttal), album-nézetben pedig **kivehetők**
  belőle. Az új album a kijelölt képekkel jön létre.
  - A `.picasa.ini`-be írás mindenhol az **ütközésbiztos** úton megy
    (ugyanazon, mint a csillagozás és a geocímke): ha közben az eredeti
    Picasa is írja a fájlt, egyik változtatás sem vész el.
  - **Amit nem értünk, azt nem bántjuk:** a nem ismert kulcsok (pl.
    `backuphash`) változatlanul maradnak — erre teszt is van.
  - A meglévő album nevét a program **soha nem írja át**; az elnevezés a
    felhasználó döntése marad.
  - Több mappát átfogó kijelölésnél az album definíciója minden érintett
    mappa ini-jébe kiíródik — ahogy az eredeti Picasa is teszi.

## [0.6.0] – 2026-07-31

### Hozzáadva
- **Virtuális albumok a bal hasábon (#9).** A Picasában létrehozott albumok
  mostantól megjelennek az **Albumok** gyűjteményben (a Csillagozott sor
  alatt), névvel és darabszámmal; rájuk kattintva a rács az album képeit
  mutatja — akkor is, ha azok több mappából állnak össze.
  - Az adat forrása a `.picasa.ini`: a `[.album:<token>]` szekciók adják a
    nevet és a dátumot, a képek `albums=` kulcsa a tagságot.
  - Az index bővült (séma v8), de a **meglévő könyvtárat nem kell újra
    indexelni**: a táblák üresen jönnek létre, a következő szinkron tölti
    fel őket.
  - Ugyanaz az album több mappa ini-jében is szerepel (a Picasa mindegyikbe
    kiírja) — ezért definíciónként tároljuk és a listában vonjuk össze. Így
    ha egy albumot a Picasában törölsz, itt is eltűnik, akkor is, ha egy
    másik mappa még hivatkozik rá.
  - Az albumtagság **írása** (kép hozzáadása/kivétele) szándékosan külön
    lépés — az a `.picasa.ini` módosításával jár, és önálló körben jön.

## [0.5.4] – 2026-07-31

### Hozzáadva
- **Kitöltő fény a Gyakori javítások fülön (#337).** Az eredeti Picasa
  Alapvető javítások fülén az ikonrács alatt ott a Kitöltő fény csúszka —
  nálunk eddig csak a Finomhangolás fülön volt. Mostantól mindkét helyen
  megvan, de **egy beállításként**: amelyiket húzod, a másik követi, és a
  mentés is közös. Így a napi használat leggyakoribb korrekciója egy
  kattintásnyira van, anélkül hogy két külön értéket kellene fejben tartani.

## [0.5.3] – 2026-07-31

### Változott
- **A szerkesztő Picasa-szerű kinézete (#338).** A felhasználó jelezte, hogy
  „sima gombok vannak a legtöbb fülön, nem tetszik" — jogosan, mert az
  eredetiben egészen más a panel:
  - **Ikonos fülek** a szoros szöveges tabok helyett: csavarkulcs, nap és
    három ecset (a három effekt-fül színben is elkülönül). Az ikonokat a
    program maga rajzolja, nem rendszer-emojival — így RPi5-ön is
    ugyanúgy néznek ki. A teljes név súgó-buborékban jelenik meg.
  - **Bélyegképes effekt-gombok:** minden gombon a SAJÁT fotó látszik az
    adott effekttel, tehát előre látni, mit csinál. A bélyegképek háttérben
    készülnek (nem akasztják meg a felületet) és gyorsítótárazódnak, ezért a
    csúszkák húzása vagy a visszavonás nem számoltatja újra őket. Amíg egy
    kép nem kész, a gomb a régi kinézetét mutatja — sosem villog üresen.

## [0.5.2] – 2026-07-31

### Javítva
- **Sötét téma: üres gombok az eszköztáron és a tálcán (#336).** Az
  Importálás, a Vissza a könyvtárhoz, az E-mail, a Nyomtatás és az
  Exportálás gomb felirata sötét témában eltűnt: a gomb háttere hardkódolt
  világos volt, a felirata viszont témafüggő — világos szöveg világos
  gombon (mért kontraszt **1,07**). A színek mostantól tokenből jönnek, és
  mérhető tulajdonságokban élnek; teszt őrzi mind a négy kombinációt
  (világos/sötét × engedélyezett/tiltott), minimum 3,0 kontraszttal.
  A felület többi hardkódolt színét is átvilágítottuk: azok sötétben
  3,9–13,0 kontraszttal olvashatók, tehát ez volt az egyetlen valódi hiba.

## [0.5.1] – 2026-07-31

### Hozzáadva
- **Effekt-csúszkák (#316):** a paraméteres effekt gombja már nem fix
  erősséggel csap a képre, hanem — az eredeti Picasa módjára — **alpanelt
  nyit csúszkákkal, élő előnézettel**, alul Alkalmaz/Mégse gombbal. Húzás
  közben a kép azonnal követi a beállítást (ini-írás és visszavonás-lépés
  nélkül); az Alkalmaz teszi a láncra, a Mégse nyomtalanul elveti. Húsz
  effekt kapott csúszkát (Élesítés, Telítettség, Vignetta, Ragyogás,
  radiális elmosás/telítettség, Színezés, Színátmenet, és az 5. fül teljes
  készlete); a paraméter nélküli effektek (Szépia, Fekete-fehér, Melegítés,
  Filmszemcse, Színinvertálás) továbbra is egy kattintás.
  A csúszkák tartományai és alapértékei **mért** értékek: a felhasználó
  valódi Picasa-exportjaiból származó ini-mintákból (`filters-decoded.md`).

### Javítva
- **Fordítás-vesztés elhárítva:** a felület magyar szövegeinek egy része
  nem közvetlen `tr()`-hívásból származik, ezért egy gépi fordítás-frissítés
  elavultnak jelölte és kiejtette őket (például a „0 kép” feliratot). A
  fordítás visszaállt, és a tanulság a projekt memóriájába került.

## [0.5.0] – 2026-07-30

A kiadás a felhasználó éles, Windows-os visszajelzései nyomán készült, és
három eredeti Picasa-képernyőkép-csomag (53 kép) szisztematikus auditjára
épül (`docs/specs/ui-audit-menus.md`, `-editor.md`, `-mainwindow.md`).

### Hozzáadva
- **Mind a 36 Picasa-effekt (#328, #329, #330):** az audit kimutatta, hogy az
  eredeti szerkesztőpanelen **öt** fül van (nálunk három volt), és 36 effekt
  (nálunk 13). A hiányzó 23 megkapta a render-implementációját és a gombját:
  a 4. fülön Infravörös film, Lomo, Holga, HDR, Kinemaszkóp, Orton, 60-as
  évek, Színinvertálás, Hőtérkép, Áttűnés, Poszterizálás, Kéttónusú; az 5.
  fülön Felpörgetés, Lágyítás, Képpontnagyítás, Fókusznagyítás, Ceruzarajz,
  Neon, Képregény, Szegély, Árnyékvetés, Múzeumi matt, Polaroid. Ez nemcsak
  hiányzó funkció volt: az ilyen effektet kapott képeket a PicasaPy eddig
  **effekt nélkül** mutatta. A négy keretes effekt méretet növel, ezért a
  lánc a **vágás után** alkalmazza őket.
- **Élesítés és Vignetta (#315):** két támogatott szűrő évek óta UI nélkül
  állt; az Élesítés az eredetiben az Effektek fül első gombja.
- **Picasa-hű gyűjtemények a bal hasábon (#320):** Albumok, Emberek,
  Projektek, Mappák, Egyebek — csukható fejlécekkel, megjegyzett állapottal.
- **Húzható mappapanel (#322):** látható elválasztó, a szélesség megmarad.
- **~44 hiányzó menüpont (#324)** és az első gyorsbillentyűk (#327).

### Javítva
- **Sötét téma (#314):** a splash logója fehér korongot kapott (eddig
  beleolvadt), a tálca ikonjai láthatóvá váltak, és a szerkesztő gombjainak
  feliratai olvashatók (a kontraszt 1,16-ról legalább 3,45-re nőtt).
- **A gombfeliratok nem vágódnak le (#318)** — tördelés az elide helyett.
- **A görgetősáv megjelent (#323):** eddig a Qt alapértelmezése szerint csak
  görgetés közben villant fel, ezért a felhasználó gyakorlatilag sosem látta.
- **A Mappanézet rendezés csak a rácsot rendezi (#321)**, a mappafát nem.
- **Az effekt-paraméterek eljutnak a rendererhez (#332):** ha a Picasában
  elhúzott csúszka értéke ott van az ini-ben, mostantól az érvényesül.

### Dokumentáció
- **Őszinte effekt-státusz (#317):** a 36 effektből 13 mögött van
  golden-mérés, 22 szakirodalmi közelítés, 1 matematikailag pontos. A
  `docs/specs/filters-decoded.md` új táblája ezt kimondja — a kalibráltság
  látszata félrevezető volt.

## [0.4.70] – 2026-07-25

### Hozzáadva
- **Geocímke: Helyek-panel, térkép és szerkesztés (#30):** a képek helye
  mostantól látszik és állítható. A hely két forrásból jön — a
  `.picasa.ini` `geotag=` kulcsa (ez az erősebb) és a fájl EXIF GPS-adata
  —, mindkettő az indexbe kerül (séma v7, migráció újraindexelés nélkül).
  Új **Nézet → Helyek** panel: OpenStreetMap-térkép a látszó képek
  jelölőivel (jelölőre kattintva kijelöli a képet), jobb kattintással a
  kijelölt képek erre a helyre kerülnek, és egy gombbal törölhető a
  geocímke (az EXIF-ben rögzített gépi hely megmarad). A szűrősor
  **geo-ikonja élesedett**: egy kattintással csak a hellyel rendelkező
  képek látszanak. A térkép külön, Loaderrel töltött komponens: QtLocation
  nélküli telepítésen a panel a szerkesztéssel együtt működik, csak a
  térkép helyén jelenik meg magyarázó szöveg.

## [0.4.69] – 2026-07-25

### Hozzáadva
- **Képkollázs és mozgófilm (#29):** a Létrehozás menü két pontja élesedett.
  A **kollázs** négy típust ad — képrács, kontaktmásolat, keretes mozaik és
  (magvas véletlennel, tehát megismételhető) képhalom —, 1600×1200-as
  vászonra, fehér paszpartuval, JPEG-be mentve. A **mozgófilm** MP4-es
  diavetítés-videót ír a kijelölésből (720p/1080p, állítható képenkénti idő,
  automatikus áttűnés), a haladást képenként mutatva. Mindkettő háttérszálon
  fut, egy hibás kép nem viszi el a munkát (a kimaradt képek száma a
  végeredmény-dialógusban látszik), és az ékezetes útvonal is működik
  (bájt-alapú írás, #190 tanulsága).

## [0.4.68] – 2026-07-25

### Hozzáadva
- **Sötét téma (#28):** a Nézet menü új, kapcsolható „Sötét téma" pontja —
  az alapértelmezés továbbra is a világos felület (Picasa-paritás), a
  választás pedig megjegyződik a következő indulásig (QSettings
  `view/darkTheme`). A `Theme.qml` tokenjei párba álltak (világos/sötét),
  a tokennevek változatlanok, így a felület minden rétege — mappafa,
  rács, dialógusok, eszköztár, tálca, néző és a Qt Controls-paletta is —
  egyszerre vált. A márkaszínek (logó) és a fotó fölé kerülő rétegek
  mindkét témában azonosak. A korábban hardkódolt fehér/szürke felületek
  tokenre cserélve (a dizájn-kézikönyv téma-politikája bővült a teljes
  világos/sötét tokentáblával).

## [0.4.67] – 2026-07-24

### Javítva
- **A QML-figyelmeztetés-őr Windowson elhasalt környezeti zajra (#309):** a
  0.4.65-ben bevezetett őr (#305) MINDEN Qt-figyelmeztetésre hibát dobott,
  így a windows-latest CI-lábat olyan üzenetek buktatták, amiknek semmi
  közük a kódhoz (hiányzó fontkönyvtár a runneren, `OpenThemeData() failed`
  offscreen módban, natív stílus testreszabási figyelmeztetése). Az őr
  mostantól kizárólag a QML-SZKRIPTHIBÁKRA hasal el (`TypeError`,
  `ReferenceError`, `SyntaxError`, „Unable to assign", „is not a
  function") — ezek platformfüggetlenül mindig valódi kódhibák. Az
  osztályozó külön modulba került (`tests/support/qml_warning_filter.py`)
  és saját tesztet kapott valódi üzenet-mintákkal mindkét oldalról.

## [0.4.66] – 2026-07-24

### Javítva
- **A duplikátum-kereső használhatóvá vált nagy könyvtáron (#294):** eddig
  feltétel nélkül a TELJES indexelt könyvtárra futott, haladásjelzés és
  megszakítás nélkül — 140 000 képnél az ablak gyakorlatilag némán állt.
  Most: **hatókör-választó** (kijelölés / aktuális mappa+almappák / teljes
  könyvtár), alapból a szűk hatókörrel; **folyamatjelző és Mégse gomb**;
  **redukált dekódolás** a perceptuális hashhez (4000×3000-es fotón
  126,9 ms → 9,3 ms, azonos hash-értékkel); a hash-ek **tárolása az
  indexben** (új `photo_hashes` tábla, séma v6), így az ismételt keresés
  azonnal indul; és **sávos jelöltszűrés** az O(n²) páronkénti összevetés
  helyett (3000 hash: 2,94 s → 0,80 s; több ezer azonos lenyomatú kép
  7,9 s helyett azonnal) — egzakt, hamis negatív nélkül.
- **A dedup-ablak nem veszi el a rács bélyegképeit (#298):** eddig a
  keresés lecserélte a bélyegkép-provider TELJES regisztrációját, amitől a
  mögötte lévő rácson szürke helyőrzők maradhattak. Mostantól saját
  id-sávban, additív regisztrációval dolgozik, és bezáráskor elengedi.

## [0.4.65] – 2026-07-24

### Javítva
- **QML null-őrök (#305):** a `controller` context property a QML-engine
  leépítésekor `null` lesz, miközben a kötések még egyszer kiértékelődnek —
  ez tucatnyi `Cannot read property … of null` figyelmeztetést szült a
  tesztek kimenetében, ami elnyomta a valódi QML-hibákat (a #232-es
  hisztogram-saga tanulsága szerint épp azok bújnak meg ott). Az érintett
  kötések null-őrt kaptak, értelmes alapértékkel — rendes futás közben a
  viselkedés változatlan.

### Hozzáadva
- **QML-figyelmeztetés-őr a tesztekben (#305):** a `qml_functional`
  conftest autouse fixture-je `qInstallMessageHandler`-rel figyeli a
  Qt/QML üzeneteket, és hibára futtatja a tesztet, ha bármilyen
  figyelmeztetés megjelent — így a jelenség nem tud visszaszivárogni.

## [0.4.64] – 2026-07-24

### Változott
- **A README összhangba hozva a kóddal (#299):** az „Amit még nem tud"
  szakasz eddig a *szerkesztő eszközöket* sorolta hiányzóként, holott a
  szerkesztő (20+ szűrő, mentés/Visszaállítás, hisztogram, effekt-vágólap)
  régóta kész és bekötött. A „Fő képességek" kiegészült az Időrend
  nézettel, Exporttal, Duplikátum-kezelővel, Import forrásból funkcióval,
  XMP-exporttal és a Picasa-mappák átvételével; a PMP/db3-import állítása
  pontosítva (olvasó-réteg kész, az indexbe-import a nyitott rész, #1).
- **Teszt-parancs a dokumentációban:** a README és a CONTRIBUTING is a
  `python3 -m pytest`-et ajánlotta — pont azt, amiről a projekt tudja, hogy
  Qt/GIL-deadlockba ragad (#53, #155). Mindkettő a `scripts/run_tests.py`-t
  adja elsődlegesként.

### Hozzáadva
- **Ruff-lint és lefedettség-mérés a CI-ben (#300):** `[tool.ruff]`
  konfiguráció (a ruff alap-négyese + bugbear; a `PL*` család szándékosan
  kimarad), önálló `lint` job a CI-ben, és a `scripts/run_tests.py --cov`
  kapcsoló, ami a darabolt futtatás részfutásait `coverage run -p` alá
  teszi, majd összesít. A 7 forrásbeli bugbear-találat javítva (nem
  elnyomva). Jelenlegi összesített lefedettség: **95%**.

## [0.4.63] – 2026-07-24

### Javítva
- **Kis-nagybetű-tűrő ini-szekciónév (#296):** a szekciónév-keresés eddig
  pontos egyezést várt, miközben a kulcsokat casefold-osan illesztettük. Ha
  az ini `[IMG_1234.JPG]`-t tartalmazott, a fájl viszont `IMG_1234.jpg` volt
  (Windows/NAS: kis-nagybetű-független fájlrendszer), a kép **csillag,
  felirat, forgatás és `filters=` nélkül** indexelődött, íráskor pedig
  második szekció keletkezett ugyanarra a fájlra. Mostantól pontos egyezés →
  casefold-os visszaesés (a pontos találat nyer), és minden író metódus
  ugyanezen a feloldáson megy; az eredeti fejléc-betűzés változatlan marad.
- **Ütközésbiztos ini-írás a fájlműveleteknél (#295):** az áthelyezés, az
  átnevezés és a másolás közvetlen `load`+`save` párost használt az
  ütközésbiztos `update_document` helyett — a párhuzamosan futó eredeti
  Picasa módosítása némán felülíródott. Mindhárom átállítva; részleges
  hibánál magyar, cselekvésre fordítható üzenet, és az `IniConflictError`
  eljut a felhasználóig.
- **Mentés-visszagörgetés (#297):** ha a mentés ini-könyvelése elbukott (pl.
  tartós írásütközés), a kép már tartalmazta a beégetett láncot, de a
  `filters=` is bent maradt — a következő megnyitáskor a renderelő
  másodszor is ráfutott. A képfájl mostantól visszaáll a hiba előtti
  állapotba, mielőtt a kivétel továbbmegy; a `revert` ugyanígy.

## [0.4.62] – 2026-07-24

### Javítva
- **Hibás `filters=` bejegyzés nem dobja el a teljes renderelést (#301):** az
  `apply_filters` eddig csak az ISMERETLEN NEVŰ szűrőket hagyta ki némán; egy
  ismert nevű, de hibás paraméterű op (`tilt=1;` paraméter nélkül,
  `crop64=1,zzz;`) kivételt dobott. A hibatűrés a három hívóból (bélyegkép-
  gyorsítótár, élő előnézet, export) átkerült magába az `apply_filters`-be:
  a hibás op kimarad, a lánc TÖBBI TAGJA lefut, a kivétel a logba kerül.
  Az `EditSession.crop()`/`tilt_param()` hibás értéknél `None`-t ad, így a
  „Paste All Effects" egy sérült, idegen láncon sem száll el.

### Változott
- **EditSession-refaktor (#302):** a `set_crop`/`set_tilt`/`set_finetune`
  háromszor kimásolt „cseréld a helyén, vagy fűzd a végére" ciklusa közös
  helperbe (`_with_single_layer`) került; `session.py` 441 → 378 sor,
  viselkedésváltozás nélkül.

## [0.4.61] – 2026-07-24

### Javítva
- **Symlinkelt mappák bejárása (#303):** a scanner eddig `follow_symlinks=False`
  miatt nem lépett be a symlinkelt almappákba — NAS-os elrendezésnél
  (`~/Kepek/Regi -> /mnt/nas/foto/regi`) a PicasaPy szótlanul nulla képet
  talált ott. A bejárás mostantól követi a symlinkeket, `(st_dev, st_ino)`
  alapú ciklusvédelemmel (symlink-kör és önmagára mutató link is elvágódik,
  figyelmeztetéssel), a törött symlink pedig csendben kimarad.
- **Nagy mappa szinkronja (#304):** a `_prune_photos` a mappa összes
  fájlnevét egyenként paraméterezte egy `NOT IN (…)` listába, ami 32 766
  (`SQLITE_MAX_VARIABLE_NUMBER`) fölött `sqlite3.OperationalError`-ral
  buktatta a szinkront. Helyette ideiglenes tábla + al-SELECT — a
  paraméterszám kötött, az FTS-triggerek változatlanul lefutnak.

## [0.4.60] – 2026-07-24

### Javítva
- **CI-deadlock (#155):** a `tests/app/test_qml_functional.py` (~68 teszt egy
  fájlban) Windowson processzen belül, véletlenszerű helyen deadlockolt
  (#53-as GIL↔Qt osztály: sok QML engine/ablak-életciklus egy processzben).
  A fájl `tests/app/qml_functional/` alá bontva 6 kisebb, témába vágó fájlra
  (közös `qml_app` fixture-rel), amelyeket a darabolt futtató KÜLÖN-KÜLÖN
  processzben futtat — processzenként jóval kevesebb életciklussal. A korábbi
  Windows-kizárás (`_WINDOWS_DEADLOCK_FILES`) törölve, a fájl így minden
  platformon fut. A tesztek tartalma változatlan (tiszta átszervezés).

## [0.4.59] – 2026-07-24

### Hozzáadva
- **Import forrásból (#23):** az eszköztár korábban tiltott „Import" gombja
  élesítve — forrás-mappa (pl. fényképezőgép/kártya, DCIM-szerkezettel is)
  választása, a talált képek bélyegképes előnézete, cél-mappa + dátum-alapú
  mappa-sablon (`{YYYY}/{YYYY}-{MM}-{DD}`, az Időrend nézettel közös
  dátum-feloldással), másolás (nem-destruktív alapértelmezés) vagy áthelyezés,
  haladásjelzéssel. Új `picasapy.fileops.copy` (ütközésbiztos másolás) és
  `picasapy.importsource` (Qt-mentes szkennelés + sablon-logika).

## [0.4.58] – 2026-07-24

### Hozzáadva
- **Duplikátum-kezelő UI (#287):** kezelő-felület a `picasapy.dedup` mag fölé —
  az Eszközök → „Find Duplicates…" pontból indítható. A pontos és hasonló
  csoportok bélyegképes listája; csoportonként a megtartandó kép választható,
  a többi **nem-destruktív alapértelmezéssel** a forrásmappa „Duplikátumok"
  almappájába helyezhető át, vagy a Kukába törölhető.

## [0.4.57] – 2026-07-24

### Hozzáadva
- **Időrend nézet (#24):** a Picasa Timeline megfelelője — a teljes könyvtár
  fotói dátum szerint, korszakokra (év/hónap) bontva, csökkenő sorrendben
  (legújabb elöl) böngészhetők. Belépés: **Ctrl+5** vagy a Nézet → Timeline
  menüpont. Új `picasapy.timeline` mag (GUI-mentes, tesztelt csoportosítás);
  dátum-forrás az EXIF `taken_at`, ennek hiányában (RAW/videó, olvashatatlan
  EXIF) a fájl-mtime.

## [0.4.56] – 2026-07-23

### Hozzáadva
- **Nem-destruktív mentés-mag (#21):** új `picasapy.edit.save` — mentéskor a
  renderelt kép az eredeti helyére kerül, az EREDETI érintetlen példánya a
  `.picasaoriginals` almappába (az első eredetit őrizve), a `.picasa.ini`-ben
  a szerkesztési lánc `redo=`-ba, `originhash` frissül, a `filters=` törlődik
  — mind a round-trip ini-rétegen át (ismeretlen kulcsok bitre megőrizve). A
  `revert` a `.picasaoriginals`-ból állítja vissza az eredetit. Megjegyzés: az
  `originhash` képlete és a `filters→redo` szabály józan, tesztelt feltételezés,
  valódi Picasa-mintán validálandó.

## [0.4.55] – 2026-07-23

### Hozzáadva
- **Duplikátum-kereső mag (#31):** új `picasapy.dedup` modul azonos és hasonló
  képek felderítésére — pontos duplikátumok tartalom-hash-sel (SHA-256,
  méret-előszűréssel), hasonló képek 64 bites dHash + Hamming-távolság
  klaszterezéssel (union-find, alapértelmezett küszöb 10). A `find_duplicates`
  immutábilis, determinisztikus eredményt ad. (A kezelő-UI külön jegy: #287.)

## [0.4.54] – 2026-07-23

### Hozzáadva
- **XMP sidecar-export MWG-RS arcrégiókkal és HierarchicalSubject-tel (#27):**
  új `picasapy.export.xmp` réteg, ami a Picasa-oldali kulcsszavakat, feliratot
  és arcrégiókat digiKam/Lightroom-kompatibilis `.xmp` sidecarba írja — az
  adat így nem ragad a `.picasa.ini`-be (UX-alapelv 5). A `rect64`
  (bal/fel/jobb/alul) régiók a MWG-konvenció szerinti KÖZÉPPONT-alapú,
  normalizált Area-koordinátákra váltanak; a nevesített arcok `People|Név`
  hierarchikus címkeként és `mwg-rs:Regions` régióként is megjelennek. A
  fotó-szintű `xmp_export` réteg a kép melletti `.picasa.ini`-ből olvas
  (kulcsszó/felirat/`faces=` + `[Contacts2]`-névfeloldás), a pixelméretet a
  kép fejlécéből veszi, és atomikusan `<fájlnév>.xmp` sidecart ír. (UI-bekötés
  külön lépés.)

## [0.4.53] – 2026-07-23

### Hozzáadva
- **Paraméter-sweep `.picasa.ini`-generátor a #190 effektjeihez (#190 2. kör):**
  új `tools/golden/make_param_sweep.py` a #190 1. körben azonosított 23
  effekt-kulcshoz előre megírt `.picasa.ini`-variánsokat generál — a fő
  erősség-paramétert a feltételezett tartományán 5 ponton végigléptetve,
  a `.picasa.ini`-t a projekt round-trip ini-rétegén át írva. Így a
  csúszka↔paraméter leképezéshez a felhasználónál csak egy tömeges Picasa-
  export marad (magyar `UTMUTATO.md`-vel). A tényleges csúszka-jelentés az
  export feldolgozásával derül majd ki.

## [0.4.52] – 2026-07-23

### Javítva
- **A PicasaPy-ikon kitölti a vásznat (#267):** a forrás `icon.png`/`icon.ico`
  körüli vastag átlátszó margó levágva, a rajzolat most a vászon ~92%-át
  tölti ki (előtte 82–90%), így a Windows Start menüben / Asztalon nem tűnik
  kisebbnek az eredeti Picasa 3 ikonnál. Új, újrafuttatható
  `tools/regenerate_icon.py`. (A végső vizuális elfogadás a felhasználónál.)

## [0.4.51] – 2026-07-23

### Javítva
- **Stabil szintetikus golden-alapképek (#278):** a `make_golden_kit.py`
  `synthetic_photos` már nem tesz ±12-es egyenletes zajt a fotószerű
  alapképekre — a zaj a Picasa JPEG-újratömörítése után felfújta a
  golden-diffet a sima tartalmú képeken („eltér" ítélet), miközben a
  chart-alapképek pixelhűek maradtak. Így a tónus-szűrők szintetikus
  fotó-alapképen is értelmes golden-számot adnak.

## [0.4.50] – 2026-07-23

### Hozzáadva
- **Élő haladás-jelző a golden-harnessben (#115):** a `compare_render.py`
  a stderr-en `[index/össz]` számlálót ír képenként — a több perces (nagy
  kit, OneDrive) futás így láthatóan halad, nem tűnik „némán állónak".

## [0.4.49] – 2026-07-23

### Javítva
- **A golden-harness ékezetes útvonalon is olvas (#115):** a
  `compare_render.py` a közös `picasapy.cvimage` bájt-alapú beolvasóját
  használja a cv2.imread helyett — a Windows-os néma Unicode-elnyelés
  (#65/#190 tanulság) itt is kifogva.

## [0.4.48] – 2026-07-23

### Javítva
- **Golden-kit generátor Windowson, fotók nélkül is (#115):** a
  `make_golden_kit.py` fotómappa-argumentuma elhagyható, kevés/hiányzó
  fotónál szintetikus fotó-alapképekkel pótol; OneDrive-tűrő kimenet-
  előkészítés; a harness-doksi példái egysorosak, létező útvonalakkal.

## [0.4.47] – 2026-07-23

### Hozzáadva
- **A Picasa 3.9-es 4–5. effekt-fül mind a 23 `filters=` kulcsa azonosítva
  (#190):** a felhasználó valódi Picasájából gyűjtött mintákból — kulcs-
  táblázat a `filters-decoded.md`-ben, round-trip tesztek a valódi
  láncokkal. A paraméter-jelentések feltérképezése a 2. (gépi) kör dolga.

### Eltávolítva
- `PicasaPy-indito.bat` (felhasználói kérésre).

## [0.4.46] – 2026-07-23

### Hozzáadva
- **`PicasaPy-indito.bat` a repó gyökerében:** dupla kattintásra frissíti
  (git pull) és elindítja az appot Windowson — a felhasználónak nem kell
  parancsokat és mappákat fejben tartania; hibánál emberi nyelvű üzenet.

## [0.4.45] – 2026-07-23

### Javítva
- **Golden-kit ékezetes útvonalon is (#190):** Windowson a cv2 képírás/
  -olvasás némán elnyeli a nem-ASCII útvonalat (pl. „Képek") — a chart-
  képek nem jöttek létre, a generálás érthetetlen helyen bukott. Mostantól
  a kép-IO memóriában kódol (imencode/imdecode), az útvonalat Unicode-
  biztos Python-IO kezeli.

## [0.4.44] – 2026-07-23

### Javítva
- **Golden-kit OneDrive-mappában is (#190):** a meglévő kimeneti mappa
  törlése OneDrive-zárolásnál (WinError 5) eddig elszállt; mostantól
  csak-olvasható attribútum-levétellel és újrapróbálkozással törlünk, ha
  pedig így sem megy, a generálás a meglévő mappába felülírással fut le —
  a kit a felhasználó által választott (akár OneDrive alatti) helyen készül el.

## [0.4.43] – 2026-07-23

### Javítva
- **Golden-kit fotókönyvtár nélkül is (#190):** a
  `make_golden_kit_effects.py` eddig kötelezően valódi fényképet keresett
  a forrásmappában, és üres mappánál elszállt (`IndexError`). Mostantól a
  fotó-argumentum elhagyható, üres mappánál pedig fotószerű szintetikus
  képet generál — a kit pusztán a kimeneti mappa megadásával elkészül.

## [0.4.42] – 2026-07-23

### Hozzáadva
- **100k-s feed-stresszmérés (#142):** ismételhető benchmark-szkript +
  env-kapcsolós stresszteszt a valódi rácson, dokumentált eredményekkel
  (`docs/benchmarks/feed-100k-stressz.md`) — 100 000 fotónál a rács
  0,21 s alatt betölt, a példányosított cellaszám 42–54 közt korlátos,
  a memóriatöbblet ~66 MB; ezzel a #142 teljesítmény-jegy minden pontja
  igazoltan teljesül.

## [0.4.41] – 2026-07-23

### Hozzáadva
- **Golden-kit az új effekt-fülekhez (#190):** `make_golden_kit_effects.py`
  — a Picasa 3.9-es 4–5. effekt-fül mind a 23 effektjéhez beszédes nevű
  referencia-képeket generál (csúszkás effekteknél több beállítással),
  magyar lépésenkénti útmutatóval (`UTMUTATO.md`) a Windows-os Picasában
  végzendő adatgyűjtéshez — ez alapozza meg a `filters=` kulcsok
  dekódolását.

## [0.4.40] – 2026-07-23

### Hozzáadva
- **Teljes Mappakezelő a Picasa 3 mintájára (#231):** önálló, mozgatható/
  átméretezhető ablak OK/Mégse gombokkal; bal oldalon a helyi mappastruktúra
  lusta betöltésű fája állapot-ikonokkal, jobb oldalon háromállapotú választó
  (Keresés mindig / Keresés egyszer / Eltávolítás a Picasából) és a figyelt
  mappák összegző listája; a „Keresés egyszer" egyszeri szkennelést végez
  figyelés nélkül, ahogy az eredeti Picasában.

## [0.4.39] – 2026-07-23

### Javítva
- **Windows-telepítő parancsikonokkal (#67):** az `install.bat` a telepítés
  után Asztal- és Start menü-parancsikont hoz létre a PicasaPy-ikonnal —
  a taskbar-ikon javításának (AppUserModelID, korábban a main-ben) kézzel
  fogható kiegészítése; a végleges .exe-be ágyazott ikon a jövőbeni
  Windows-csomagolási munka része.

## [0.4.38] – 2026-07-23

### Javítva
- **Automatikus csomag-assetek a release-eken (#256):** a `package.yml`
  mostantól a Release workflow lefutása után magától elkészíti és feltölti
  a wheel/sdist/.deb/Windows-zip asseteket (a GITHUB_TOKEN
  rekurzióvédelme miatt a korábbi `release: published` trigger sosem
  sült el); kézi `workflow_dispatch` pótlásra továbbra is használható.

## [0.4.37] – 2026-07-23

### Hozzáadva
- **Gyorscímkék a Címkék-panelen (#193):** 8 konfigurálható gomb (2×4)
  egykattintásos címkézéshez, fogaskerékkel nyíló konfigurációs ablak —
  a felső két gomb automatikusan a legutóbb használt címkéket követi
  (kikapcsolható), az üres mezők gyakran használt címkékkel tölthetők fel;
  a beállítások megőrződnek.

## [0.4.36] – 2026-07-23

### Hozzáadva
- **Csomagolás (#4):** `pip install .`/pipx-telepítés működő `picasapy`
  paranccsal (entry point + QML/ikon/fordítás a wheelben); új `packaging/`
  könyvtár Debian-csomag (.deb) és Windows-zip összeállító szkriptekkel,
  magyar build-útmutatóval; release-publikáláskor a csomagok automatikus
  feltöltése release-assetként (`package.yml`).

## [0.4.35] – 2026-07-23

### Hozzáadva
- **Drag & drop import (#237):** képet az ablakra húzva a kép mappája
  (mappát húzva maga a mappa) figyelt gyökér lesz — deduplikálva, egymásba
  ágyazott utaknál a legfelsővel; nem támogatott elemről visszajelzés-buborék.
- **Tulajdonságok-panel az egyképes nézőben is (#192):** a könyvtár-nézet
  kapcsolóját követi, lapozásra frissül.

### Javítva
- **Ablakpozíció/-méret megjegyzése (#192):** záráskor mentés, induláskor
  visszaállítás — lecsatolt monitor és hibás adat elleni védelemmel;
  maximalizált zárásnál a normál geometria is megőrződik.

### Dokumentáció
- CONTRIBUTING: a feladat-ciklus végének pontosítása (a vállaló session a
  merge–issue-zárás–verzió-bump körig felelős; integrátor híján maga veszi
  át az integrátor szerepet) + i18n-regen buktató rögzítése.

## [0.4.34] – 2026-07-22

### Hozzáadva
- **„Félkész szoftver" figyelmeztetés az indítóképernyőn (#243):** amíg az
  eredeti Picasa effekt-készlete nincs teljesen implementálva, a betöltés
  végén a splash figyelmeztetést és OK gombot mutat — csak az OK
  megnyomása után záródik be, és addig a mögöttes felület nem kattintható.

## [0.4.33] – 2026-07-22

### Javítva
- **Indítóképernyő (#240, éles hibajelentés):** Windowson egyáltalán nem
  látszott — a betöltés az ablak első kirajzolása előtt lezajlott és a
  splash már kifakulva jelent meg; mostantól az első képkocka után indul,
  és legalább 1,5 másodpercig látható. Debianon a hiányzó logó összeejtette
  a kártyát — a logónak fix magassága és raszteres tartalék-képe van, a
  kártya magassága pedig nem függ a kép betöltésétől.

## [0.4.32] – 2026-07-22

### Hozzáadva
- **Indítóképernyő (#189):** PicasaPy-logós splash screen verziószámmal,
  animált betöltési állapotszöveggel és kék „foglalt"-sávval; az app
  használatra kész állapotánál magától eltűnik.
- **`.picasa.ini` ütközésvédelem (#137):** a párhuzamosan futó eredeti
  (Windows-os) Picasa írásai többé nem veszhetnek el — mentés előtti
  ütközés-ellenőrzés, ütközésnél a módosítás biztonságos újrajátszása.
- **Hisztogram-referenciacsomag (#236):** determinisztikus tesztképek és
  automata ellenőrzés a hisztogram-skála Picasa-összevetéséhez.

### Javítva
- **Hisztogram-doboz (#235):** a cím nem vágódik el (2 sorba törhet), a
  fényképezőgép-adatok az eredeti Picasa kétoszlopos, címkézett
  elrendezését követik (35 mm-egyenértékkel).
- **Windows taskbar-ikon (#67):** több méretű `icon.ico` — a hol
  megjelenő / késleltetett taskbar-ikon tünete ellen.
- **Magréteg-duplikációk (#151):** közös kép-segédmodul és ini-helper —
  kevesebb ismétlődő kód, egységes viselkedés.

## [0.4.31] – 2026-07-21

### Javítva
- **Hisztogram VÉGRE rajzol (#232, éles hibajelentés):** a görbe eddig
  soha nem jelent meg — a valódi ok az volt, hogy a csatorna-értékeket
  tuple-ként adtuk át QML-nek, ami ott nem tömbként látszott, így a rajzoló
  minden csatornát kihagyott (a #25/#228 a Canvas-időzítést gyanította,
  tévesen). A vödör-listák mostantól listák, a törékeny Canvas helyett
  pedig mindig-renderelő téglalap-oszlopok rajzolják a kitöltött RGB-görbét,
  címmel; EXIF hiánya esetén „Nincs elérhető EXIF-adat." felirattal.

## [0.4.30] – 2026-07-21

### Javítva
- **Hisztogram azonnal rajzol (#228, éles hibajelentés):** a görbe a kép
  megnyitásakor rögtön megjelenik a megjelenített képből számolva, EXIF
  nélküli képnél is — nem kell hozzá csúszka-mozdulat; a
  „Nincs elérhető fényképezőgép-adat" felirat magyarul jelenik meg.

## [0.4.29] – 2026-07-21

### Javítva
- **Kijelölés-stabilitás (#135):** a kijelölés a fotókat követi, nem a
  sorszámokat — háttér-frissítés közben sem csúszhat át a csillagozás/
  forgatás/export egy másik képre; a korábban flaky navigációs tesztek
  determinisztikusak.

### Hozzáadva
- **Élő hisztogram + fényképezőgép-adatok (#25):** a néző bal alsó doboza
  élesedett — RGB-hisztogram a ténylegesen megjelenített (szerkesztett)
  képből, élő frissítéssel a csúszkák húzása közben, alatta a gép,
  expozíció, rekesz, ISO, gyújtótávolság és vaku adatai.
- **Picasa widget-króm a teljes felületen (#3):** minden görgetősáv és
  csúszka (videó-lejátszó, szerkesztő-panel, tálca) az egyedi, kézikönyv-hű
  Picasa-stílust viseli a Qt alap-kinézet helyett.

## [0.4.28] – 2026-07-21

### Javítva
- **Mappa-eltávolítás futó szkennelés közben (#216, éles hibajelentés):** az
  eltávolítás azonnal megszakítja a szkennelést, az eltávolított mappa képei
  rögtön eltűnnek, a kósza háttér-jelzések elnyelődnek, az Importálás-panel
  nem ragad be.
- **Videó utáni első kép szerkeszthetősége (#218, éles hibajelentés):** a
  videóról képre lapozva a szerkesztő azonnal működik, nem kell egy másik
  képre átlapozni.
- A teljes felület magyar: az új panelek és dialógusok (effekt-fülek,
  export, Importálás-panel, teljesítmény-monitor, Picasa-átvétel) szövegei
  lefordítva.

### Teljesítmény
- **Rács-virtualizálás (#142):** nagy mappáknál a rács csak a látható
  cellákat építi fel (3000 helyett ~42), a teljes nézet-frissítés
  3,4 mp-ről 10 ms-ra csökkent, a mappaváltás pedig nem olvassa újra a
  teljes indexet, ha nem változott — RPi5-en is sima görgetés.

### Hozzáadva
- **Kattintható diagnosztika-útvonal (#217):** a teljesítmény-monitoron a
  mentett napló útvonalára kattintva megnyílik a mappája (Windowson a fájl
  kijelölésével).

## [0.4.27] – 2026-07-20

### Hozzáadva
- **Fokozatos, blokkolásmentes indexelés + lebegő „Importálás" panel (#209):**
  nagy mappaszerkezet hozzáadásakor a képek mappánként, folyamatosan jelennek
  meg (nem egy nagy blokkoló lépésben), a program végig használható marad;
  a húzható panel mutatja az aktuális mappát és a haladást — a Picasa 3
  import-élménye.
- **Teljesítmény-monitor (#211):** a Súgó menüből kapcsolható lebegő panel
  (CPU, memória, aktuális tevékenység) + „Diagnosztika mentése" gomb — a
  mentett naplófájl issue-hoz csatolva célzott hibakeresést tesz lehetővé.
  Kikapcsolva nulla többletköltség; a napló nem tartalmaz teljes
  útvonalakat.

## [0.4.26] – 2026-07-20

### Javítva / Teljesítmény
- **Csillag/felirat/forgatás nem fagyaszt (#141):** az ini-írás és az
  index-frissítés háttérszálon fut, a mappa-resync helyett célzott egy-soros
  frissítéssel; a rács csak az érintett sort frissíti, a görgetés nem ugrik.
  NAS-mappában a több másodperces kattintás-fagyás megszűnt.
- **Watcher-bekötés (#143 lezárás):** fájlváltozásnál mappa-pontos, gyors
  szinkron fut a teljes részfa újrabejárása helyett; az adatbázis-foglaltság
  hibája sem némítja el a szinkront.
- **Export-lezárás (#136):** a szerkesztések (filters=) ténylegesen beleégnek
  az exportált fájlba, és a sikertelen fájlok neve+oka megjelenik az
  eredmény-ablakban.

### Hozzáadva
- **„Összes effektus másolása/beillesztése" (#152 lezárás):** a Kép menü két
  pontja élesítve — egy kép összes effektje átvihető több kijelölt képre,
  visszavonással.

## [0.4.25] – 2026-07-20

### Hozzáadva
- **Effektlánc másolás-beillesztés magja (#152):** a szerkesztő-munkamenet
  API-szinten tudja egy kép összes effektjének átvitelét másik kép(ek)re,
  az ismeretlen bejegyzések bitre pontos megőrzésével és undo-támogatással;
  a Kép menü gombjainak élesítése következik.
- **Picasa widget-króm komponensek (#3):** kézikönyv-hű görgetősáv és
  csúszka (PicasaScrollBar, PicasaSlider) próba-oldallal; a felületre
  bekötés következik.

### Karbantartás
- **A két óriásfájl felbontva (#150):** controller.py 1232 → 528 sor
  (hat al-modulra bontva), Main.qml 1590 → 604 sor (hét komponensre bontva)
  — viselkedés-változás nélkül, a tesztek módosítás nélkül zöldek. Minden
  forrásfájl a 800 soros projektlimit alatt; a párhuzamos munka mostantól
  kevesebb ütközéssel folyhat.

## [0.4.24] – 2026-07-20

### Hozzáadva
- **Finomhangolás + Effektek fülek (#20):** Derítőfény/Kiemelések/Árnyékok/
  Színhőmérséklet csúszkák (finetune2) és a 12 effekt-gomb élesítve a
  szerkesztő-panelen, élő előnézettel, a `filters=` láncba írva; a
  Filmszemcse (grain2) rögzített maggal renderel (nem „villog" újrarajzoláskor).
- **Arc-keretek a nézőben (#147):** a régi Picasa-címkézések (`faces=`)
  keretként + névvel megjeleníthetők — `F` billentyű vagy gomb a zoom-sávban,
  alapból kikapcsolva. (Felismerés nincs — az a 3. fázis.)
- **Meglévő Picasa-telepítés felderítése (#146):** a felderítő API kész
  (Wine-útvonalak + kézi mappa, WatchedFolders-átvétel útvonal-átírással);
  a felajánló dialógus bekötése következik.
- **Golden-összehasonlító harness (#115):** `tools/golden/compare_render.py`
  — a PicasaPy render a valódi Picasa-exportok ellen mérhető (SSIM/ΔE),
  szűrőnkénti pixelhű/közelítés ítélettel.
- Dizájnkézikönyv 2026-07-20-i helyi másolata a repóban.

### Javítva
- **Windows taskbar-ikon (#67):** explicit AppUserModelID — a tálcán a
  PicasaPy-ikon jelenik meg a Python-ikon helyett.

### Teljesítmény
- **Scanner (#143):** fájlonként pontosan egy fájlrendszer-lekérdezés
  (scandir-stat), mappa-mtime-alapú inkrementális újrabejárás és egy-mappás
  sync-út — ismételt átvizsgálásnál 96%-kal kevesebb hálózati művelet
  (NAS-on 50k fotónál ~50 s → ~2 s stat-költség); a bekötés a háttérfigyelő
  ágra következik.

## [0.4.23] – 2026-07-20

### Hozzáadva
- **Hiányzó effekt-renderelők (#149):** a régi Picasa-szerkesztések közül a
  Vignetta (mért maszkkal), Ragyogás (glow/glow2), Árnyalás (tint), Szűrt FF
  (ansel), Lágy fókusz (radblur), Fókuszos FF (radsat) és Színátmenet
  (dir_tint) mostantól megjelenik a nézőben és a bélyegképeken. (A
  Filmszemcse/grain2 véletlen alapú, pixelhűen nem reprodukálható — kihagyva,
  a round-trip őrzi.)
- **Kizárt mappák (#145):** a Picasa `FRExcludeFolders.txt`-jében kizárt
  mappák nem kerülnek az indexbe; a konfigfájl-keresés kis-nagybetű-független
  (`watchedfolders.txt` is működik), és a walker a legacy `Picasa.ini` nevet
  is felismeri.

### Javítva
- **Export (#136):** az exportált JPEG megőrzi az EXIF/IPTC-adatokat (dátum,
  GPS, kameraadat, felirat); változtatás nélküli exportnál bájthű másolás
  (nincs generációs veszteség); videónál megmarad az mtime; az export hibái
  strukturáltan jelződnek (nincs néma elhalás); a `filters=` szerkesztések
  beleégnek a célfájlba.
- **Magréteg-javítások (#151):** `.trashinfo` a fájlmozgatás előtt íródik
  (tele lemeznél sincs árva lomtár-bejegyzés); path-remap casefold-hosszváltozás
  javítva; thumbindex határellenőrzés (`ThumbIndexFormatError` nyers
  IndexError helyett); nem-UTF-8 fájlnevek naplózása; watcher rejtett-mappa
  szűrés relatív úton; watcher debounce felső korlát (30 s).

### Teljesítmény
- **Thumbnail-pipeline (#144):** párhuzamos bélyegkép-generálás (4 szál,
  hideg mappa-megnyitás ~3,2×); szűrt-thumb memóriacache (szerkesztett képes
  mappa görgetése ~100×); méretkorlátos cache-takarító (512 MB) a `~/.cache`
  alatti tárnak; kérésenként eggyel kevesebb fájl-megnyitás (NAS-barát).

## [0.4.22] – 2026-07-20

### Javítva
- **Feed-pozíció — a VALÓDI ok (#173):** a nézőből visszatérve a feed a
  háttér-sync befejezésekor a mappa elejére ugrott. A tényleges ok a
  controllerben volt: a háttér-sync (`syncFinished` → `_reload`) folder-módban
  `selectFolder`-t hívott, ami `folderActivated`-et emittál → a UI a mappa
  tetejére görget. Mostantól a háttér-sync `folderActivated` nélkül frissít
  (a scroll-to-top csak explicit, felhasználói mappa-választásé), így a néző
  bezárása után a görgetési pozíció megmarad. (A 0.4.20/0.4.21-es QML-oldali
  reveal ehhez kiegészítés — a valódi javítás ez.)
- **QML image-provider GIL-deadlock (#53):** a tesztkészlet (Linux/Windows,
  offscreen) nem-determinisztikusan beragadt — az async kép-betöltő szál a
  Python image-providert a GIL-en át hívta, míg a főszál natív Qt-hívásban
  tartotta a GIL-t. Offscreen (teszt) platformon mostantól szinkron a
  kép-betöltés (nincs második szál → nincs holtpont); produkcióban marad az
  async. A korábban ~50–100%-ban beragadó QML-tesztek 10/10 futása, és a
  Windows-CI-láb is stabilan zöld.

## [0.4.21] – 2026-07-20

### Javítva
- **Feed-pozíció (#173, utókövetés):** a nézőből visszatérve a feed a
  háttér-resync **befejezése után is** a megnyitás előtti pozíción marad. Az
  előző (0.4.20-as) fix csak az azonnali frissítést kezelte; a `resyncFolderOfRow`
  háttérszála viszont a végén (a kék „dolgozik" sáv eltűnésekor) küld egy késői
  frissítést, ami eddig visszaugratta a nézetet a mappa elejére. A reveal
  mostantól „ragadós": a késői async frissítésre és a layout beállására is a
  helyes pozíciót tartja, amíg a felhasználó ténylegesen nem görget.

## [0.4.20] – 2026-07-20

### Javítva
- **crop64-lánc rossz kivágása (#130):** a `filters=` láncbeli `crop64` a spec
  szerint csak szerkesztési történet — a tényleges vágást a `crop=` kulcs
  (a lánc effektív, utolsó crop64-e) adja, az eredeti képméretre. A render
  eddig a lánc minden crop64-ét sorban, kaszkádolva alkalmazta → rossz
  kivágás a több crop64-es valódi Picasa-fájlokon. Mostantól az effektusok a
  teljes képre futnak, a vágás egyszer, a végén.
- **Legacy (nem UTF-8) `.picasa.ini` (#133):** a CP1250/latin-1 fájlok három
  hibája javítva — a U+0085/U+2028 kódpont nem töri ketté a sort
  (fantomszekció); ékezetes szöveg legacy fájlba mentése nem omlik el
  (UTF-8-ra váltás, végső esetben explicit `IniSaveError`); az IPTC 1:90
  karakterkészlet-jelölő figyelembevétele csökkenti a mojibake-et.
- **Döntés-csúszka kinullázta a mentett tilt-et (#131):** a döntés-eszköz a
  mentett értékről indul, és aktív eszköz melletti lapozás nem írja felül az
  új kép mentett döntését az előnézetben.
- **Feed-pozíció elveszett a nézőből visszatérve (#173):** a mappa végén álló
  kép megnyitása után visszalépve a feed a megnyitás előtti görgetési
  pozíción marad, nem ugrik a mappa elejére.

## [0.4.19] – 2026-07-20

### Javítva
- **Éles indexkép szerkesztett/vágott képnél (#163, P0):** a `filters=` lánc
  mostantól nagy (a célméret négyszeres) bázison renderel, és csak a
  végeredmény kicsinyül a bélyegkép-méretre — az erős vágás után sem homályos
  a rács legnagyobb fokozatán. A szerkesztett bélyegkép külön, a lánccal
  kulcsolt cache-fájlba kerül.
- **Óriáskép (DecompressionBomb) nem akasztja meg a szinkront (#134):** a
  metaadat-olvasó és a thumbnail-út elkapja a Pillow `DecompressionBombError`-t
  (és a szigorú `DecompressionBombWarning`-ot); egyetlen túl nagy kép többé nem
  dönti el a teljes indexelést.
- **Üres gyökér nem törli az indexet (#132):** ha egy figyelt gyökér elérhető,
  de üres (tipikusan lecsatolt NAS-mount), a szinkron nem takarítja ki a
  korábban felindexelt részfát — a NAS visszatérésekor nincs órákig tartó
  teljes újraépítés.
- **A fájlkezelő-megnyitás hibája eljut a felhasználóhoz (#112):** a „Keresés a
  lemezen" mostantól hibát jelez, ha az `xdg-open` hiányzik vagy nemnulla
  kóddal tér vissza — nem nyeli el némán.

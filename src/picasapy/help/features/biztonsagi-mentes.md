# Képek biztonsági mentése

A PicasaPy át tudja másolni a fotóidat egy másik meghajtóra vagy egy
hálózati megosztásra. A másolás **nem mozdítja el** az eredetiket, és nem
is módosítja őket.

Indítás: **Eszközök ▸ Képek biztonsági mentése…**

A mentés **nem külön ablakban** nyílik, hanem a **könyvtár alján**
kicsúszó panelen — ugyanott, ahol az [Ajándék CD](ajandek-cd.md) is
dolgozik. A kettő **egyszerre nem lehet nyitva**: ha az egyiket
megnyitod, a másik becsukódik. A panel nyitva tartása mellett a könyvtár
használható marad.

## Mit ment el

A mentés a **figyelt mappáid** teljes tartalmát veszi alapul — ugyanazokat
a mappákat, amiket a [Mappakezelőben](mappakezelo.md) állítottál be. Nem
a kijelölésed és nem az éppen látott mappa számít. Hogy ezekből mi kerül
át, azt a készlet fájlszűrője, illetve a mappák pipája dönti el — lásd
lentebb.

## A mentés-készlet

A mentés egy **készlethez** tartozik. A készlet megjegyzi, hova mentett és
mit mentett már el, így a következő futás **csak az újat és a
megváltozottat** másolja át. Egy nagy fotótár első mentése így hosszú, a
másodiktól kezdve viszont gyors.

Több készletet is létrehozhatsz — például egy teljeset a külső
merevlemezre, és egy szűkebbet egy hálózati mappába.

A panel **két lépésre** oszlik. A bal oldali, **Készlet létrehozása vagy
egy meglévő használata** keretben választod ki a készletet, a jobb
oldali, **Mappák és albumok kijelölése biztonsági másolat készítéséhez**
keretben pedig azt, mi menjen át.

A készletet **legördülő listából** választod; alatta az **Új készlet…**,
a **Készlet módosítása…** és a **Készlet törlése** gomb áll. A
legördülő nem látszik, amíg egyetlen készlet sincs, a **Készlet törlése**
pedig addig nem, amíg csak egy van — az utolsó készletet nem lehet
törölni, csak módosítani.

A panel alján egy sor mutatja, **hova** ment a kiválasztott készlet, és
**mikor futott utoljára** — ha még nem futott, a célhely után „még nem
futott" áll. Másolás közben ugyanitt jelenik meg a haladás.

## Új készlet

Az **Új készlet…** gombbal négy dolgot adsz meg:

- **Mentési készlet** — a készlet neve, amit a listában látsz majd. A
  mező nem üresen indul: az ajánlott név **Saját mentési készlet**.
- **Mentés típusa** — ez dönti el, **milyen** a mentés kimenete:
  - **Lemezről lemezre mentés (külső és hálózati meghajtókhoz)** — a
    képek egy **mappába** másolódnak;
  - **Mentés CD-re vagy DVD-re** — a képek **lemezkép-fájlba** kerülnek.
- **Mentés ide** — a célmappa. A **Kiválasztás…** gombbal ki is válaszd.
  Ez csak a lemezről lemezre mentésnél állítható: a CD/DVD-típusnál a
  program adja a helyet, és mutatja is a mezőben (a Képek mappádon belül
  a *Picasa biztonsági másolat ▸ ISO-k* mappa).
- **Fájlok** — mi kerüljön át:
  - **Minden fájltípus** — fotók, RAW-fájlok és videók;
  - **Minden kép (videók nélkül)**;
  - **Csak JPEG-ek fényképezőgép-adatokkal** — azok a JPEG-ek, amikben
    benne van a fényképezőgép neve. Ezzel a képernyőképek és a letöltött
    képek kimaradnak a mentésből.

A készlet-űrlap **külön felugró ablakban** nyílik, **Mentési készlet**
címmel; az **OK** gomb zárja le, a **Mégse** elveti. Ha a program nem
fogadja el a készletet, az űrlap **nyitva marad**, a beírt adatok
megmaradnak, és a hiba oka ott olvasható.

A **Készlet módosítása…** ugyanezeket a mezőket nyitja meg egy meglévő
készleten — a típusát is átállíthatod. Ilyenkor az ablak címe **Mentési
készlet szerkesztése**, a záró gomb pedig **Módosítás**.

A **Készlet törlése** rákérdez, és a kérdésben **a készlet nevét is
kiírja**; **a már elmentett fájlokat nem bántja**, csak a nyilvántartást
szünteti meg.

## Melyik mappa menjen át

Amíg a mentés-panel nyitva van, **az egész könyvtár átáll mentés-módba**,
és csak azt mutatja, ami még nincs elmentve:

- a **bal hasáb** azokra a mappákra szűkül, amelyekből még nem mentetted
  el mindent — a már teljesen elmentett mappa nem látszik. Ez a lapos
  mappalistára és a fanézetre egyaránt áll; a fán a mentetlen mappák a
  **szülőmappáikkal együtt**, kinyitva jelennek meg, hogy lásd, hol
  vannak. A panel bezárása után a fa ugyanúgy áll, ahogy előtte;
- a **képrács** is csak a **még el nem mentett fájlokat** mutatja. Egy
  félig elmentett mappából tehát csak az újak és a megváltozottak
  látszanak. A panel bezárásakor a rács visszaáll, oda is, ahol előtte
  álltál.

A panel maga is kiírja, mi történik: „A Picasa most azokat a fájlokat
jeleníti meg, amelyekről korábban nem készült biztonsági másolat."

A bal hasábon minden megjelenő mappa előtt **pipa** áll. **Alapból egy
sincs bepipálva** — neked kell megjelölni, mi menjen át:

- kattints a mappák pipájára egyenként, vagy
- a panel **Az összes kijelölése** gombjával jelöld be mindet — az **Az
  összes kijelölés megszüntetése** pedig mindet leveszi.

Amíg egy pipa sincs, a **Biztonsági mentés**/**Írás** gomb szürke.

A lista **a háttérben készül el**, mert a program végigolvassa a
gyűjteményt; amíg számol, **Számítás…** áll a helyén. Készletváltáskor
egyszer újraszámol. Nagy gyűjteménynél ez eltarthat egy ideig, de a
program közben használható marad.

Két eset, amikor a hasábon a mappák helyén egy mondat áll:

- **Készlet létrehozása vagy egy meglévő használata** — még nem
  választottál készletet, tehát nincs mihez hasonlítani;
- **A készlet valamennyi fájljáról készült biztonsági másolat** — ebben a
  készletben már minden el van mentve, nincs mit átvinni. Ugyanez a
  mondat a képrács helyén is megjelenik.

## A mentés futtatása

Válaszd ki a készletet, pipáld be a mappákat, majd kattints a gombra.

A gomb felirata **Biztonsági mentés**, ha van kiválasztott készlet;
mappába mentésnél is ez indítja a másolást.

A program először **megszámolja**, hány fájl menne át, és ezt kiírja.
Mappába mentésnél azt is odaírja, **hány CD-re vagy DVD-re férne** ennyi
adat; lemezkép-mentésnél a „*N* fájl írása lemezképbe…" üzenet jön.

Másolás közben a panelen **haladásjelző csík** fut, az üzenetben pedig a
„Másolás (12/340) fájl" alakú számláló mutatja, hol tart. A program
közben **használható marad**: a másolás a háttérben megy. A végén
megmondja, hány fájl ment át. A záró üzenet mindig ugyanaz — **A mentés
elkészült** —, akkor is, ha nem volt mit átmásolni.

### Megszakítás

Amíg a másolás tart, a panel jobb szélén megjelenik a **Megszakítás**
gomb (az indító gomb ilyenkor szürke). Erre kattintva a program az éppen
futó fájl után abbahagyja.

**A megszakítás nem veszít el munkát:** a már átmásolt fájlok bekerülnek
a nyilvántartásba, tehát a következő futás pontosan a hiányzókkal
folytatja.

Csak a **sikeresen** átmásolt fájl kerül a nyilvántartásba. Ha a mentés
magától szakad félbe — például megtelik a cél, vagy megszűnik a hálózati
kapcsolat —, a következő futás ugyanígy pótolja a hiányzót.

## Mappába vagy lemezképbe

Hogy mappa vagy lemezkép lesz a kimenet, **a készlet típusa** dönti el:

- **lemezről lemezre** típusnál a képek a megadott célmappába
  másolódnak: külső meghajtó, pendrive vagy hálózati megosztás;
- **CD/DVD**-típusnál lemezkép-fájlok készülnek. Ilyenkor a **Lemezre
  írás** gomb mellett megjelenik egy választó, amiben az dönthető el,
  hogy **CD-lemezképbe (ISO)** vagy **DVD-lemezképbe (ISO)** menjen a
  mentés — ez a darabok méretét szabja meg. A választó csak ennél a
  típusnál látszik.

Ha a gyűjtemény nem fér el egy lemezen, **több, sorszámozott lemezkép**
készül (`picasapy-mentes-01.iso`, `-02.iso` és így tovább), pontosan
akkora darabokban, amekkora egy valódi lemezre ráfér. Minden lemezképen
ott vannak a képek a saját mappaszerkezetükben, mellettük a
`.picasa.ini` fájlok, a gyökérben pedig a `files.txt` lista — a mentés
tehát a PicasaPy nélkül is olvasható.

A lemezkép **felcsatolható**, és bármelyik lemezíró programmal lemezre
írható. **A PicasaPy maga nem ír lemezt.**

A végén ezt írja ki: „Kész: *N* fájl, *M* lemezképen."

## Visszaállítás a mentésből

A mentésből a képeket a programon belül is visszaállíthatod — például egy
új gépen, vagy ha az eredetik elvesztek. A mentés-panel jobb szélén, a
**Mégse** gomb mellett áll a **Visszaállítás...** gomb. Másolás közben nem
látszik, a készlet kiválasztásától pedig nem függ.

A gomb a **Mentés visszaállítása** ablakot nyitja meg:

1. Az első mezőbe írd be a mentés helyét, vagy válaszd ki:
   - a **Mappa...** gombbal egy mentési mappát (amilyet a lemezről lemezre
     mentés készít);
   - a **Lemezkép...** gombbal a lemezkép-készlet **első** fájlját
     (`.iso`). Ha a készlet több sorszámozott lemezképből áll
     (`picasapy-mentes-01.iso`, `-02.iso` és így tovább), a program az
     azonos nevű, sorszámozott társakat is megnyitja, és az összesből
     visszaállít.
2. A **Visszaállítás ide:** mezőbe írd be a célmappát, vagy a **Kiválasztás...**
   gombbal válaszd ki. Ha a mappa még nincs meg, a program létrehozza.
3. Kattints a **Visszaállítás** gombra. A **Mégse** bezárja az ablakot;
   amíg a visszaállítás fut, mindkét gomb szürke.

A program csak a **fényképeket és a RAW-fájlokat** állítja vissza, és
mindegyik mellé viszi a mappája `.picasa.ini` fájlját is, így a címkék,
a csillagok és a szerkesztések is megmaradnak. A videókat nem. A képek az
**eredeti mappaszerkezetükben** kerülnek a célmappába.

**Meglévő fájlt nem ír felül.** Ha a célmappában már van egy ugyanolyan
nevű fájl a helyén, azt kihagyja, és érintetlenül hagyja. Ezért nyugodtan
visszaállíthatsz olyan mappába is, ahol már vannak képek: csak a hiányzók
kerülnek oda. A képeket **csak a célmappába** másolja. Ha látni akarod őket a
könyvtárban, vedd fel a célmappát figyelt mappának (lásd
[Mappakezelő](mappakezelo.md)).

Ha a program végzett, az ablak bezárul, és a panelen ez áll: „Visszaállított
fájlok: *N*; már létező fájlok kihagyva: *M*."

A visszaállítás a háttérben fut, a program közben használható marad.

Ha valami nem sikerül, a hiba **pirosan az ablakban** jelenik meg, az ablak
pedig nyitva marad, hogy javíthass:

- „Válassza ki a mentés forrását és a visszaállítási mappát." — valamelyik
  mező üres;
- „A mentés nem állítható vissza: …" — a mondat végén az ok áll, például
  hogy a kiválasztott mappa vagy lemezkép nem mentés, vagy hogy a mentésben
  nem található visszaállítható kép.

Az eredeti Picasa mentéseit is felismeri: az általa írt mappából vagy
lemezképből ugyanígy visszaállíthatsz.

## Mi kerül a célmappába

- A képek, az eredeti **mappaszerkezetet megtartva**.
- A képek mellé a `.picasa.ini` fájlok is. Így a mentés önmagában teljes
  értékű archívum: a címkék, a csillagok és a szerkesztések a képekkel
  együtt maradnak meg.
- A cél gyökerében egy `files.txt` nevű lista arról, mi került át:
  soronként az útvonal, a méret és a módosítás ideje. Ezt bármilyen
  szövegszerkesztővel meg tudod nézni, a PicasaPy nélkül is.

## Ami nincs benne

Az eredeti Picasa maga írta meg a CD-t vagy a DVD-t. A PicasaPy **nem ír
lemezt**: a kimenete mappa vagy lemezkép-fájl. A lemezt ebből egy
tetszőleges lemezíró programmal készíted el. A mentésből a képeket viszont
a PicasaPy vissza is tudja állítani — lásd fentebb.

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
**mikor futott utoljára** — ha még nem futott, azt is kiírja. Másolás
közben ugyanitt jelenik meg a haladás.

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

A készlet-űrlap **külön felugró ablakban** nyílik; a **Módosítás** gomb
zárja le. Ha a program nem fogadja el a készletet, az űrlap **nyitva
marad**, a beírt adatok megmaradnak, és a hiba oka ott olvasható.

A **Készlet módosítása…** ugyanezeket a mezőket nyitja meg egy meglévő
készleten — a típusát is átállíthatod. A **Készlet törlése** rákérdez, és
a kérdésben **a készlet nevét is kiírja**; **a már elmentett fájlokat nem
bántja**, csak a nyilvántartást szünteti meg.

## Melyik mappa menjen át

A jobb oldali keret fölött, a panel és a könyvtár közt egy **mappalista**
jelenik meg: **azok a mappák, amelyekből még nem mentetted el mindent**.
A már teljesen elmentett mappa nem látszik itt. A keret szövege is ezt
mondja: „A Picasa most azokat a fájlokat jeleníti meg, amelyekről
korábban nem készült biztonsági másolat."

Minden mappa előtt **pipa** áll. **Alapból egy sincs bepipálva** — neked
kell megjelölni, mi menjen át:

- kattints a mappák pipájára egyenként, vagy
- a keret alján lévő **Az összes kijelölése** gombbal jelöld be mindet —
  az **Az összes kijelölés megszüntetése** pedig mindet leveszi.

Amíg egy pipa sincs, a **Biztonsági mentés**/**Írás** gomb szürke.

A lista **a háttérben készül el**, mert a program végigolvassa a
gyűjteményt; amíg számol, **Számítás…** áll a helyén. Készletváltáskor
egyszer újraszámol. Nagy gyűjteménynél ez eltarthat egy ideig, de a
program közben használható marad.

Ha a készletből már minden el van mentve, a lista helyén ez áll:
„Minden el volt már mentve."

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

Amíg a másolás tart, a **Biztonsági mentés**/**Írás** gomb helyén
**Megszakítás** áll.
Erre kattintva a program az éppen futó fájl után abbahagyja.

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
tetszőleges lemezíró programmal készíted el.

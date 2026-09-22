# Képek biztonsági mentése

A PicasaPy át tudja másolni a fotóidat egy másik meghajtóra vagy egy
hálózati megosztásra. A másolás **nem mozdítja el** az eredetiket, és nem
is módosítja őket.

Indítás: **Eszközök ▸ Képek biztonsági mentése…**

## Mit ment el

A mentés a **figyelt mappáid** teljes tartalmát veszi alapul — ugyanazokat
a mappákat, amiket a [Mappakezelőben](mappakezelo.md) állítottál be. Nem
a kijelölésed és nem az éppen látott mappa számít. Hogy ezekből mi kerül
át, azt a készlet fájlszűrője dönti el.

## A mentés-készlet

A mentés egy **készlethez** tartozik. A készlet megjegyzi, hova mentett és
mit mentett már el, így a következő futás **csak az újat és a
megváltozottat** másolja át. Egy nagy fotótár első mentése így hosszú, a
másodiktól kezdve viszont gyors.

Több készletet is létrehozhatsz — például egy teljeset a külső
merevlemezre, és egy szűkebbet egy hálózati mappába.

Az ablakban a készletek listája látszik, mindegyik alatt a mentés helye és
az utolsó futás ideje. Ha még egy sincs, ezt írja: „Még nincs
mentés-készlet."

## Új készlet

Az **Új készlet…** gombbal három dolgot adsz meg:

- **Mentési készlet** — a készlet neve, amit a listában látsz majd. A
  mező nem üresen indul: az ajánlott név **Saját mentési készlet**.
- **Mentés ide** — a célmappa. A **Tallózás…** gombbal ki is válaszd.
- **Fájlok** — mi kerüljön át:
  - **Minden fájltípus** — fotók, RAW-fájlok és videók;
  - **Minden kép (videók nélkül)**;
  - **Csak JPEG-ek fényképezőgép-adatokkal** — azok a JPEG-ek, amikben
    benne van a fényképezőgép neve. Ezzel a képernyőképek és a letöltött
    képek kimaradnak a mentésből.

A szerkesztést a **Módosítás** gomb zárja le.

A **Készlet módosítása…** ugyanezt a három mezőt nyitja meg egy meglévő
készleten. A **Készlet törlése** rákérdez; **a már elmentett fájlokat nem
bántja**, csak a nyilvántartást szünteti meg.

## A mentés futtatása

Válaszd ki a készletet a listában, majd **Mentés**.

A program először **megszámolja**, hány fájl menne át, és ezt kiírja —
azt is odaírja, **hány CD-re vagy DVD-re férne** ennyi adat. Ha közben
semmi nem változott, ezt az üzenetet kapod: „Minden el volt már mentve."

Másolás közben a gombok fölött **haladásjelző csík** fut, az üzenetben
pedig a „Másolás (12/340) fájl" alakú számláló mutatja, hol tart. Az
ablak közben **használható marad**: a másolás a háttérben megy, nem
fagyasztja be a programot. A végén megmondja, hány fájl ment át.

### Megszakítás

Amíg a másolás tart, a **Mentés** gomb helyén **Megszakítás** áll. Erre
kattintva a program az éppen futó fájl után abbahagyja.

**A megszakítás nem veszít el munkát:** a már átmásolt fájlok bekerülnek
a nyilvántartásba, tehát a következő futás pontosan a hiányzókkal
folytatja.

Csak a **sikeresen** átmásolt fájl kerül a nyilvántartásba. Ha a mentés
magától szakad félbe — például megtelik a cél, vagy megszűnik a hálózati
kapcsolat —, a következő futás ugyanígy pótolja a hiányzót.

## Mappába vagy lemezképbe

A **Mentés** gomb mellett választod ki, hova készüljön a mentés:

- **Mappába** — a szokásos út: külső meghajtó, pendrive vagy hálózati
  megosztás;
- **CD-lemezképbe (ISO)** vagy **DVD-lemezképbe (ISO)** — a program
  lemezkép-fájlokat ír a célmappába.

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

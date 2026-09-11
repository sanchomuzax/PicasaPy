# Duplikátumok keresése

Két külön eszköz van rá, és más-más célra valók:

- a **másodpéldány-nézet** gyorsan megmutatja, miből van több példány a
  könyvtáradban — böngészésre való;
- a **másodpéldány-kezelő** párbeszéd végigvezet a takarításon, és a
  feleslegeseket a Kukába teszi.

Mindkettő az **Eszközök ▸ Kísérleti** almenüben van. (Az eredeti
Picasában is a Kísérleti almenüben volt a helye.)

## A másodpéldány-nézet

**Eszközök ▸ Kísérleti ▸ Fájlok másodpéldányainak megjelenítése.** Ez
**nem nyit ablakot**: a rács átvált szűrt nézetbe, és csak azokat a
képeket mutatja, amikből több példány van a könyvtárban.

A keresés a teljes könyvtárat átnézi, ezért eltarthat pár másodpercig.
Amíg tart, sárga sáv jelzi: **„Másodpéldányok keresése…"**. Utána a zöld
eredménysávon a **Másodpéldányok** felirat mutatja, hogy ebben a módban
vagy.

Kilépni két módon lehet:

- a zöld sáv **Vissza az összes megtekintéséhez** gombjával, vagy
- a keresősáv szűrő-gombjai közt megjelenő **másodpéldány-jelvényre**
  (két egymásra csúszó lap) kattintva.

Ez a jelvény **csak ebben a módban látszik** — bekapcsolni nem lehet
vele, arra a menüpont (vagy a **Ctrl+F6**) való. Ez az eredeti Picasa
viselkedése.

### Mit tekint másodpéldánynak

Azt, amit az eredeti Picasa: a fájl elejéből és végéből számolt
ujjlenyomatot. Két kép akkor másodpéldány, ha ez az ujjlenyomat
megegyezik — nem a fájlnév és nem a teljes tartalom dönt. A program így
egyetlen fájlt sem olvas végig, ezért gyors marad nagy könyvtárnál is.

Ebbe a nézetbe **csak az azonos fájlok** kerülnek bele. A csak
hasonló, de nem azonos felvételekhez a
[Keresés hasonló képekre](kereses.md) parancs való.

## A másodpéldány-kezelő

**Eszközök ▸ Kísérleti ▸ Másodpéldányok kezelése…** — ez a PicasaPy saját
kiegészítése, az eredeti Picasában nincs ilyen, ezért a menüben kék
felirattal látszik.

### A keresés

A **Keresés helye** választóban:

- **Teljes könyvtár**, vagy
- **Ez a mappa és az almappái**.

A **Duplikátumok keresése** gomb indítja. Közben a program először a
képeket elemzi, majd a fájlokat hasonlítja össze; a haladás végig
látszik, és a **Mégse** gombbal megszakítható. A megszakítás akkor is
azonnal hat, ha a keresés épp abban a pillanatban ért véget — a már
megtalált csoportok megmaradnak.

Ha nem talál semmit, kiírja: „Nincs talált duplikátum."

### Az eredmény

Két csoportban jelennek meg a találatok:

- **Pontos duplikátumok** — teljesen egyforma fájlok.
- **Hasonló képek** — nem azonos, de nagyon hasonló felvételek. A
  csoport mellett a „távolság" szám mutatja, mennyire térnek el: minél
  kisebb, annál hasonlóbbak.

Egy csoportot kinyitva látod a képeket. Válaszd ki, melyiket tartod meg.

### A feloldás

A **Többi törlése a Kukába** gombbal a kijelölt kép marad meg, a többit
a program a rendszer Kukájába helyezi. **Nem töröl véglegesen** — ha
meggondolod magad, a Kukából visszaállíthatók.

A párbeszéd mindig kiírja, hány kép van kijelölve, hogy lásd, mi fog
történni.

## Importáláskor

Az importáló ablak **Duplikátumok kizárása** jelölője azokat a képeket
hagyja ki, amik már benne vannak a könyvtáradban. Ugyanez a beállítás a
**Beállítások ▸ Általános** fülön is megvan **Duplikátumok észlelése
importáláskor** néven — a két hely ugyanazt az egy kapcsolót mutatja.

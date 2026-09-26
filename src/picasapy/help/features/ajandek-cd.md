# Ajándék CD

Az **Ajándék CD** a régi Picasa ajándékozó funkciója: fogod a képtálcára
összegyűjtött képeket, adsz nekik egy nevet és egy méretet, és a program
egyetlen fájlba csomagolja őket, amit lemezre lehet írni.

Indítás: **Létrehozás ▸ Ajándék CD készítése…**

> **A PicasaPy nem ír lemezt.** A kimenet egy **lemezkép-fájl**
> (`.iso`), amit bármelyik lemezíró programmal lemezre égetsz, vagy
> egyszerűen felcsatolsz és úgy nézed meg. Ez az egyetlen eltérés az
> eredetihez képest — a lemezre írást a program helyett a rendszeren
> szokásos lemezíró végzi.

## Amiből dolgozik: a képtálca

Az Ajándék CD **a képtálca elemeit** viszi fel, nem a rács kijelölését —
ugyanúgy, mint a kollázs és a mozgófilm. Előbb tehát gyűjtsd össze a
képeket a tálcára — több mappából a **Kijelölt elemek megőrzése**
gombbal —, és csak utána nyisd meg a menüpontot. A panel maga is ezt
írja: „A program a fent pipával kijelölt elemeket másolja az ajándék
CD-re."

Üres tálcával a **Lemezre írás** gomb szürke — nincs mit felvinni.

## A panel

A panel a **könyvtár alján** nyílik ki, két lépés-keretben:

**Kijelölés és beállítások**

- **Továbbiak hozzáadása…** — visszavisz a könyvtárba, hogy még tehess a
  tálcára. Az addig összegyűjtött elemek megmaradnak.
- **Fotóméret** — mekkora legyen a felvitt kép hosszabb oldala:
  **Eredeti méret**, **640x480**, **800x600** vagy **1600x1200**. A
  kisebbik méretekkel több kép fér egy lemezre, és a címzett gépén
  gyorsabban nyílnak.

**Az ajándék CD elnevezése**

- **CD neve** — ez lesz a lemez neve, **legfeljebb 16 karakter** (a mező
  nem is engedi hosszabbat). Ha üresen hagyod, a fájl neve lesz a lemez
  neve is.

Jobb oldalon a **Lemezre írás** indítja a munkát. A **Mégse** ugyanúgy
visszavisz a könyvtárba, mint a Továbbiak hozzáadása — a tálca tartalmát
egyik sem üríti ki.

## A lemezkép elkészítése

A **Lemezre írás** először megkérdezi, **hova** kerüljön a fájl. A
párbeszéd a **Képek** mappádból indul, és **ISO-fájlok**at ajánl; a
kiterjesztést nem kell beírnod, a program `.iso`-ra végződő nevet készít.

Ezután a munka a **háttérben** folyik: nagy tálcánál az átméretezés és a
lemezkép összeállítása percekig is eltarthat. Amíg tart, a **Lemezre
írás** gomb nem nyomható újra.

A végén a **CD kész** ablak jön elő, benne a kész fájl útvonala:

- a **CD megjelenítése** gomb megnyitja a fájl helyét a fájlkezelőben;
- a **Bezárás** becsukja az ablakot.

Ha valamelyik kép nem került fel, azt is kiírja ugyanitt: „*N* elem nem
került a lemezre." A többi ilyenkor is felkerül — egy hibás fájl nem
állítja le az egészet.

Ha egyetlen kép sem sikerült, csak ennyit kapsz: „A lemezkép nem készült
el."

## Mi kerül a lemezre

- A képek **egyetlen mappában**, aminek a neve **Képek**.
- A képek **JPEG**-ként, a szerkesztéseiddel együtt: a vágás, a forgatás
  és az effektek bele vannak sütve, pontosan úgy, ahogy a rácson látszanak.
  Ami nem JPEG volt, JPEG lesz.
- A **filmek bájtra változatlanul**, átalakítás nélkül.

Ami **nem** kerül rá:

- a `.picasa.ini` fájlok, tehát a feliratok és a címkék nem mennek a
  lemezre — az ajándék CD a képekről szól, nem az adatbázisodról;
- HTML-oldal vagy vetítő program;
- maga a PicasaPy (az eredeti rá tudta tenni a Picasa telepítőjét a
  lemezre; nálunk ez a lehetőség nincs meg).

## Kapcsolódó

- [A könyvtár és a képtálca](konyvtar.md)
- [Exportálás mappába](exportalas.md) — ha csak fájlokat akarsz kimenteni
- [Képek biztonsági mentése](biztonsagi-mentes.md) — ha archiválni akarsz

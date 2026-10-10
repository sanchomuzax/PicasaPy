# Keresés és szűrés

## A keresőmező

Az eszköztár jobb szélén lévő mezőbe gépelve azonnal keres a program.
Keres a **fájlnévben**, a **képfeliratban**, a **címkékben** és a
**mappanévben** is — ha egy mappa neve illeszkedik, a mappa teljes
tartalma találat lesz.

Gépelés közben javaslatok jelennek meg; a bal hasáb pedig a keresésre
szűkül, és mappánként mutatja, hány találat van benne.

A javaslatlistát billentyűzettel is kezelheted, miközben a kurzor a
mezőben van: a **↓** és a **↑** lépked a javaslatok között (a kiemelt sor
mutatja, hol tartasz), az **Enter** megnyitja a kiemeltet, az **Esc**
pedig bezárja a listát. Ha egyik javaslatot sem emelted ki, az Enter
nem választ semmit.

Keresés után a rács fölötti zöld sávon megjelenik a **Vissza az összes
megtekintéséhez** gomb. Erre kattintva kilépsz a keresésből: a mező
kiürül, a bal hasáb pedig újra a teljes mappalistát mutatja.

A mező jobb szélén lévő **×** törli a keresést, és visszaáll az előző
nézet.

A mezőre jobbgombbal kattintva a szokásos szövegszerkesztő parancsok
jönnek elő: **Visszavonás**, **Kivágás**, **Másolás**, **Beillesztés**,
**Törlés** és **Az összes kijelölése**.

### A kereső lenyíló paneljei

Amikor a mezőbe kattintasz, vagy már van benne szöveg, a mező mellett
megjelenik egy kis **⌄** gomb. Ez egy lenyíló panelt nyit (a **Ctrl+F**
is ezt nyitja, miközben a mezőre ugrik), és újra rákattintva csukja.
A panelen:

- egy sor, ami a találatokat összegzi — keresésnél *Találatok a(z) „…"
  kifejezésre (N)*, szűrésnél a szűrő állapota;
- a **Csak az arcokat ábrázoló fotók** gomb: csak az arcot tartalmazó
  képeket mutatja, újra megnyomva kilép a szűrésből;
- a **Csak a másodpéldányok mutatása** gomb: ugyanaz, mint az **Eszközök ▸
  Kísérleti ▸ Fájlok másodpéldányainak megjelenítése** — lásd
  [Duplikátumok keresése](duplikatumok.md).

> A **Nézet ▸ Keresési opciók** menüpont ettől függetlenül **még nem
> működik**: ma csak helyfoglaló, a fenti panel nem kapcsolódik hozzá.

## Keresés szín szerint

A keresőmezőbe színt is írhatsz, a szó elé tett `szín:` (vagy `color:`)
kulcsszóval:

```
szín:kék
```

Elfogadott színek: piros (vörös), narancs (narancssárga), sárga, zöld,
kék, lila (bíbor), rózsaszín, fekete, fehér, szürke. Az angol nevek is
működnek (`color:blue`), és az ékezet nélküli `szin:` alak is.

Hét tétel menüből is elérhető: **Eszközök ▸ Kísérleti ▸ Keresés…**
almenüben a **Piros**, **Narancssárga**, **Sárga**, **Zöld**, **Kék**,
**Lila** és a **Fekete-fehér** — ez utóbbi a sötét, színtelen képeket
keresi (`color:black`). Bármelyikre kattintva a keresés beíródik a keresőmezőbe, és a
rács azonnal a hasonló színű képeket mutatja. Ugyanaz történik, mintha
te gépelted volna be, tehát utólag bővítheted a keresést szöveggel.

A színkeresés összevonható szöveggel: a `szín:kék nyaralás` olyan képeket
ad, amik kékek **és** illeszkednek a „nyaralás" szóra. Két különböző
színt megadva a kettő **vagy** kapcsolatban áll.

A színeket a program a háttérben számolja ki a képekhez. Egy frissen
felvett kép ezért csak kis késéssel jelenik meg a színkeresésben.

## Szűrők az eszköztáron

Az eszköztár közepén, a **Szűrők** felirat mellett négy kapcsoló van.
Mindegyik a jelenlegi nézetet szűkíti, és mindig csak az éppen aktív
szűrő gombja látszik bekapcsoltnak:

- **csillag** — csak a csillagozott képek,
- **arc** — csak azok a képek, amikben arcot talált a program,
- **film** — csak a videók,
- **földgömb** — csak a helyhez kötött (geocímkézett) képek.

Van egy ötödik kapcsoló is, a **másodpéldány-jelvény**, de az alapból
nem látszik: csak akkor jelenik meg, ha a másodpéldány-nézet be van
kapcsolva, és egy kattintással ki is vezet belőle. Lásd
[Duplikátumok keresése](duplikatumok.md).

Szűrés közben zöld sáv jelzi, hány kép látszik; a sávon a **Vissza az
összes megtekintéséhez** gombbal lépsz ki a szűrésből.

A kapcsolók után nincs más gomb: a szűrősáv végén korábban látszott
egy kis „▤" jel, de az nem csinált semmit, ezért kikerült.

Szűk ablakban a szűrő-zóna elrejtőzik, hogy az eszköztár egy sorban
maradjon.

## Az idő-csúszka: „legfeljebb ennyi idős képek"

A szűrők mellett jobbra van egy kis csúszka. A buboréksúgója **Szűrés
dátumtartomány szerint**, de valójában **egyetlen felső korhatárt** ad
meg: minél jobbra húzod, annál frissebb képek maradnak a rácson. (A
félrevezető felirat az eredeti Picasáé, nem fordítási hiba.)

A zöld sávon megjelenik, mit szűrtél — például **„Legfeljebb 9 hetes
képek."** A program a kor nagyságához igazítja a mértékegységet: nap,
hét, hónap vagy év.

A csúszkát **balra, a szélére** húzva kikapcsolod a szűrőt. Ha közben
másik nézetre váltasz (például csillag-szűrőre, keresésre vagy másik
mappára), a csúszka magától alaphelyzetbe, balra áll vissza, és a kor
felirata is eltűnik a zöld sávról.

## Hasonló képek keresése

Jelölj ki egy képet, és nyomd meg a **Ctrl+F7** billentyűt: a **Keresés
hasonló képekre** parancs a kiválasztott képhez hasonló felvételeket gyűjti
össze. (Az eredeti Picasához hasonlóan a kép jobb gombos menüjében ez nem
szerepel.) A
találati fejléc mutatja, melyik kép a minta; a **Minta törlése** gombbal
(**Ctrl+F8**) zárod le a keresést.

Ez nem ugyanaz, mint a másodpéldány-keresés — az azonos fájlokat keres,
lásd [Duplikátumok keresése](duplikatumok.md).

## A keresés eredményének megőrzése albumként

Amíg keresési találatot látsz, az **Eszközök ▸ Kísérleti ▸ Keresési
eredmények mentése…** paranccsal a **teljes találatból** album lesz. Az
album neve a keresés szövege, de bármikor átnevezheted.

Ezer találat felett a program megkérdezi, biztosan létrehozza-e az
albumot — a gomb felirata **Album létrehozása**. Ezer alatt szó nélkül
elkészül.

A menüpont csak akkor él, ha keresési nézetben vagy, és van találat.

## Kijelölés-parancsok

A **Szerkesztés** menüben:

- **Az összes kijelölése** (Ctrl+A)
- **Csillagozottak kijelölése**
- **Kiválasztás megfordítása** (Ctrl+I)
- **Kijelölés törlése** (Ctrl+D)

Egérrel: kattintás, Ctrl+kattintás az egyenkénti hozzávételhez,
Shift+kattintás tartományhoz, és a rács üres részéről indított húzással
lasszóval is jelölhetsz.

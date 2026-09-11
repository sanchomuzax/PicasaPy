# Keresés és szűrés

## A keresőmező

Az eszköztár jobb szélén lévő mezőbe gépelve azonnal keres a program.
Keres a **fájlnévben**, a **képfeliratban**, a **címkékben** és a
**mappanévben** is — ha egy mappa neve illeszkedik, a mappa teljes
tartalma találat lesz.

Gépelés közben javaslatok jelennek meg; a bal hasáb pedig a keresésre
szűkül, és mappánként mutatja, hány találat van benne.

A mező jobb szélén lévő **×** törli a keresést, és visszaáll az előző
nézet.

A mezőre jobbgombbal kattintva a szokásos szövegszerkesztő parancsok
jönnek elő: **Visszavonás**, **Kivágás**, **Másolás**, **Beillesztés**,
**Törlés** és **Az összes kijelölése**.

## Keresés szín szerint

A keresőmezőbe színt is írhatsz, a szó elé tett `szín:` (vagy `color:`)
kulcsszóval:

```
szín:kék
```

Elfogadott színek: piros (vörös), narancs (narancssárga), sárga, zöld,
kék, lila (bíbor), rózsaszín, fekete, fehér, szürke. Az angol nevek is
működnek (`color:blue`), és az ékezet nélküli `szin:` alak is.

Hat szín menüből is elérhető: **Eszközök ▸ Kísérleti ▸ Keresés…**
almenüben a **Piros**, **Narancssárga**, **Sárga**, **Zöld**, **Kék** és
**Lila**. Bármelyikre kattintva a keresés beíródik a keresőmezőbe, és a
rács azonnal a hasonló színű képeket mutatja. Ugyanaz történik, mintha
te gépelted volna be, tehát utólag bővítheted a keresést szöveggel.

A színkeresés összevonható szöveggel: a `szín:kék nyaralás` olyan képeket
ad, amik kékek **és** illeszkednek a „nyaralás" szóra. Két különböző
színt megadva a kettő **vagy** kapcsolatban áll.

A színeket a program a háttérben számolja ki a képekhez. Egy frissen
felvett kép ezért csak kis késéssel jelenik meg a színkeresésben.

## Szűrők az eszköztáron

Az eszköztár közepén, a **Szűrők** felirat mellett négy kapcsoló van.
Mindegyik a jelenlegi nézetet szűkíti:

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

A csúszkát **balra, a szélére** húzva kikapcsolod a szűrőt.

## Hasonló képek keresése

Egy képre jobbgombbal kattintva a **Keresés hasonló képekre** parancs a
kiválasztott képhez hasonló felvételeket gyűjti össze (**Ctrl+F7**). A
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

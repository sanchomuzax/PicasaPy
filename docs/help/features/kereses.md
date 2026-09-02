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

## Keresés szín szerint

A keresőmezőbe színt is írhatsz, a szó elé tett `szín:` (vagy `color:`)
kulcsszóval:

```
szín:kék
```

Elfogadott színek: piros (vörös), narancs (narancssárga), sárga, zöld,
kék, lila (bíbor), rózsaszín, fekete, fehér, szürke. Az angol nevek is
működnek (`color:blue`), és az ékezet nélküli `szin:` alak is.

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

Szűrés közben zöld sáv jelzi, hány kép látszik; a sávon a **Az összes
megtekintése** gombbal lépsz ki a szűrésből.

Szűk ablakban a szűrő-zóna elrejtőzik, hogy az eszköztár egy sorban
maradjon.

## Hasonló képek keresése

Egy képre jobbgombbal kattintva a **Keresés hasonló képekre** parancs a
kiválasztott képhez hasonló felvételeket gyűjti össze. A találati fejléc
mutatja, melyik kép a minta; a **Minta törlése** gombbal zárod le a
keresést.

Ez nem ugyanaz, mint a duplikátum-keresés — az egy külön eszköz, lásd
[Duplikátumok keresése](duplikatumok.md).

## Kijelölés-parancsok

A **Szerkesztés** menüben:

- **Az összes kijelölése** (Ctrl+A)
- **Csillagozottak kijelölése**
- **Kiválasztás megfordítása** (Ctrl+I)
- **Kijelölés törlése** (Ctrl+D)

Egérrel: kattintás, Ctrl+kattintás az egyenkénti hozzávételhez,
Shift+kattintás tartományhoz, és a rács üres részéről indított húzással
lasszóval is jelölhetsz.

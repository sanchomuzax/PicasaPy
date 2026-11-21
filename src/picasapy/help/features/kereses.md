# Keresés és szűrés

## A keresőmező

Az eszköztár jobb szélén lévő mezőbe gépelve azonnal keres a program.
Keres a **fájlnévben**, a **képfeliratban**, a **címkékben**, a
**mappanévben**, az **album nevében**, valamint a kép EXIF-adatai közül a
**szerző** és a **szerzői jog** mezőben is. Ha egy mappa neve illeszkedik,
a mappa teljes tartalma találat lesz; ha egy album neve illeszkedik, az
album képei kerülnek a találatok közé.

Nem kell a mezőbe kattintanod: ha a bélyegképrácson vagy a bal oldali
mappalistán állsz, és leütsz egy betűt, számot vagy jelet, az a
keresőmezőbe kerül, és elindul a keresés. Az ékezetes betű, illetve a
Ctrl vagy Alt billentyűvel együtt leütött gomb nem indít keresést.

### Hogyan értelmezi a beírt szöveget

- Több szó esetén a program **mindegyikre** keres: a `tó nyár` csak
  azokat a képeket adja, amelyekre mindkét szó illik.
- A szó elé tett **mínuszjel** kizár: a `tó -nyár` a tavas képeket adja,
  a nyári képek nélkül.
- A pont, az aláhúzás és a legtöbb írásjel szóelválasztóként számít.
- A **felvétel dátumára** is kereshetsz, kettősponttal tagolva: a
  `2019:03:08` egy napra, a `2019:03` egy hónapra, a `2019` egy évre ad
  találatot.
- Ha a szöveget **`tag:`** (vagy `címke:`) előtaggal kezded, a program
  csak a címkék között keres. Előtag nélkül a fájlnévre, a feliratra, a
  címkékre és a mappanévre is.
- Gépelés közben a program kivárja, amíg megállsz, és csak akkor keres,
  így a gyors gépelés nem lassítja.

A mező háttere jelzi az eredményt: **világoszöld**, ha van találat, és
**halványpiros**, ha nincs. Ha a rejtett képek megjelenítése ki van
kapcsolva, a rejtett képek a találatok számában, a bal oldali listában
és a zöld sávon sem szerepelnek.

### A javaslatlista

Gépelés közben a mező alatt, a mezővel egyező szélességben egy
javaslatlista nyílik. Ebben a beírt szövegre illő **szavak** (címkék és
más keresőszavak), **mappák** és **albumok** állnak. A szósorok mellett
látszik, hány képen szerepel az adott szó, és a gyakoribb szó áll elöl.
Csak olyan album jelenik meg, amelyben van kép.

- Egy **szósorra** kattintva a szó és utána egy szóköz kerül a mezőbe,
  és a keresés lefut.
- Egy **mappát** vagy **albumot** választva arra a mappára vagy albumra
  lépsz, a keresés pedig megmarad.

A bal hasáb közben a keresésre szűkül, és csak azokat a mappákat
mutatja, amelyekben van találat, mappánként a találatok számával. A
találatok összesített sora az **Albumok** csoportban, album ikonnal áll,
például: „Találatok a(z) "tó" kifejezésre (12)". Ezer fölött a
darabszámok ezres tagolással íródnak. Ha nincs találat, a sáv a
**Nincs találat** feliratot mutatja.

A javaslatlistát billentyűzettel is kezelheted, miközben a kurzor a
mezőben van: a **↓** és a **↑** lépked a javaslatok között (a kiemelt sor
mutatja, hol tartasz), az **Enter** megnyitja a kiemeltet. Ha egyik
javaslatot sem emelted ki, az Enter nem választ semmit.

### Kilépés a keresésből

- Az **Esc** először csak a javaslatlistát zárja be. A következő
  **Esc** törli a keresést, a kurzor pedig a mezőben marad.
- A **Ctrl+F** második lenyomása is bezárja a keresést.
- Keresés után a rács fölötti zöld sávon megjelenik a **Vissza az összes
  megtekintéséhez** gomb. Erre kattintva kilépsz a keresésből.
- A mező jobb szélén lévő **×** törli a keresést.

Bármelyik úton lépsz ki, a program visszaállítja a keresés előtti
mappát és a képek kijelölését, a bal hasáb pedig újra a teljes
mappalistát mutatja.

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

Ugyanezt a panelt a **Nézet ▸ Keresési opciók** menüpont is nyitja és
csukja, pontosan úgy, mint a **⌄** gomb. A menüpont előtt pipa áll,
amíg a panel nyitva van.

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

A szűrők a keresőmezőbe írt szöveggel **együtt** szűkítenek: ha közben
keresel is, csak az a kép marad, amely a szűrőnek és a keresésnek is
megfelel. A szűrőgomb kikapcsolása megtartja a keresőszöveget, a szöveg
törlése pedig a bekapcsolt szűrőt. A film szűrőnél is így van: a szöveg
törlése után a filmnézet marad.

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

A csúszka a keresőszöveggel együtt szűr. Ha keresés közben állítod, a
szöveg a mezőben marad, és a csúszka akkor is a helyén marad, ha a
szöveget módosítod vagy törlöd. Ilyenkor a zöld sáv jobb szélén a
**Dátumtartomány:** felirat után látszik a beállított korhatár.

A csúszkát **balra, a szélére** húzva kikapcsolod a szűrőt. Ha másik
mappára vagy másik szűrőre váltasz, a csúszka magától alaphelyzetbe,
balra áll vissza, és a kor felirata is eltűnik a zöld sávról.

## Hasonló képek keresése

Jelölj ki egy képet, és nyomd meg a **Ctrl+F7** billentyűt: a **Keresés
hasonló képekre** parancs a kiválasztott képhez hasonló felvételeket gyűjti
össze. (Az eredeti Picasához hasonlóan a kép jobb gombos menüjében ez nem
szerepel.) A
találati fejléc mutatja, melyik kép a minta; a **Minta törlése** gombbal
(**Ctrl+F8**) zárod le a keresést.

A program az eredeti Picasa módszerével hasonlít: a képek kicsinyített
színképét, színeloszlását és éleit veti össze a mintáéval, és a
könyvtár képeit ez alapján **rangsorolja**. A sorrendben az is számít,
mennyire közel készült egy kép a mintához **időben**: a mintához időben
közelebbi felvételek előrébb kerülnek. A találat a rangsor
első **1000** képe. Az első keresés nagy könyvtárnál lassabb lehet, mert
a program ekkor számolja ki minden kép jellemzőit; ezeket megjegyzi, így
a következő keresés gyorsabb.

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

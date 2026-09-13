# Nézegetés: néző, diavetítés, videó

## Az egyképes néző

A rácsban egy képre duplán kattintva megnyílik a néző. Kilépni a
**Visszatérés a könyvtárhoz** gombbal vagy az Esc billentyűvel tudsz.

A néző alján és szélein a következőket találod:

- **Előző kép** / **Következő kép** léptetés.
- **Diavetítés indítása**.
- **Arcok megjelenítése** (`F` billentyű) és **Arcok szerkesztése**
  (Shift+`F`) — a képen felismert arcok keretei.
- **Kiegyenesítés**, **Visszavonás**, **Újra** — gyors szerkesztő-gombok.
- A kép bal alsó sarkában egy kis világos négyzet: ezzel kapcsolod be és
  ki a **feliratsávot** (lásd [Képfelirat](csillag-felirat-cimke.md)). A
  négyzet akkor is ott marad, ha a sáv ki van kapcsolva — ez az út
  vissza.

A **Ctrl+Delete** a lemezről törli az éppen látott képet (rákérdezéssel).

A képre jobbgombbal kattintva ugyanazok a parancsok érhetők el, mint a
rácsban: forgatás, mentés, visszaállítás, elrejtés, keresés a lemezen,
tulajdonságok, törlés a lemezről.

## Két kép egymás mellett

A néző alsó sávjában, a **Lejátszás** gomb előtt három kis szegmens áll
egymás mellett. Ezek döntik el, hány kép látszik:

| szegmens | mit csinál |
|---|---|
| **Csak egy kép megjelenítése** | a szokásos, egyképes nézet — ez az alapállás |
| **Ugyanazon kép megjelenítése kétszer** | ugyanaz a kép kétszer: **balra a szerkesztés előtti**, jobbra a mostani állapot |
| **Két különböző kép megjelenítése** | **még nem működik** — a szegmens látszik, de nem választható |

Az **Ugyanazon kép megjelenítése kétszer** a szerkesztés
összehasonlítására való: a bal oldalon a nyers fájl van, minden effekt
és javítás nélkül, a jobb oldalon pedig az, amit éppen csinálsz belőle.
Így egy pillantással látod, mennyit változott a kép.

Ha két kép látszik, megjelenik mellettük egy negyedik szegmens is,
**Fókusz váltása a képek között** — ezzel jelölöd ki, melyik oldal az
aktív. Az aktív oldal felső sarkában **Kijelölve** felirat áll.

Videónál a kettős nézet nem használható.

## Nagyítás a nézőben

A nagyítás három vezérlője az **alsó eszközsávban** van, a
panelkapcsolók előtt:

- **Beillesztheti a fotót a megjelenítési területbe** — a teljes kép
  belefér az ablakba;
- **Fotó megjelenítése tényleges méretben** — a kép a saját képpontjain,
  1:1-ben;
- **nagyítás-csúszka** — a kettő közt és azon túl.

A csúszka bal széle az illesztett nézet, a **közepe pontosan a tényleges
méret** (100 %), a jobb széle a négyszeres nagyítás. A csúszka megakad a
tényleges méretnél, hogy pontosan el lehessen találni. Ennél kisebbre és
nagyobbra nem lehet állítani.

A nagyított képet egérrel húzva mozgatod. A képre duplán kattintva
visszaugrik az illesztett nézetbe. Videónál és vágás közben a nagyítás
nem használható.

## A kék információs sáv

Az alsó sáv kék csíkja a könyvtárban a kijelölésről ír; **a nézőben az
éppen látott képről**, ebben a sorrendben: a mappa neve és a fájlnév, a
kép dátuma, a felbontás képpontban, a fájl mérete, a **hányadik kép** a
mappában, végül a **Címkék:** felsorolás.

Ha a szöveg nem fér ki — kisebb ablakban vagy hosszú fájlnévnél —, két
lépésben rövidül:

1. elmarad a fájlnév elől a **mappanév**;
2. ha még mindig hosszú, a **fájlnév közepébe** kerül három pont. Az
   eleje és a vége megmarad, tehát a kiterjesztés is látszik.

A többi adat nem rövidül.

## Diavetítés

Indítás: **Nézet ▸ Diavetítés**, a **Mappa ▸ Diavetítés megtekintése**,
a néző gombja, vagy a **Ctrl+4** billentyű.

A vetítés teljes képernyőre vált, és a program **egész ablakát** kitölti:
a menüsor, az eszköztár és a képtálca a vetítés idejére eltűnik,
kilépéskor visszajön. Vezérlés közben:

| billentyű | mit csinál |
|---|---|
| Szóköz | szünet / folytatás |
| → vagy Enter | következő kép |
| ← | előző kép |
| Ctrl+R | forgatás jobbra |
| Ctrl+Shift+R | forgatás balra |
| Esc | kilépés |

Kilépéskor a rács és a néző arra a képre ugrik, ahol a vetítés
abbamaradt.

### A vezérlősáv

Az egeret megmozdítva a kép alján előjön a vezérlősáv:

- **✕ Kilépés**;
- **◀** előző, **▶** / **❚❚** lejátszás és szünet, **▶▶** következő;
- **↺** és **↻** forgatás — a vetítés közbeni forgatás megmarad;
- **átmenet-választó** (lásd lentebb);
- **feliratmód** gombja — körbejár a három állás közt: a felirat (**T**),
  a fájlnév (**F**), vagy semmi (**—**);
- **★** csillagozás — ez is megmarad;
- **Diaidő** — a **−** és a **+** gombbal 1 és 30 másodperc közt
  állítható, hogy meddig álljon egy kép. A szám a két gomb közt látszik.

A választott átmenet, feliratmód és diaidő **megmarad** a következő
vetítésre és a következő indításig is.

### Átmenetek

A választóban öt átmenet van:

| átmenet | mit csinál |
|---|---|
| Kivágás | nincs átmenet, a következő kép azonnal ott van |
| Szétoszlás | a két kép egymásba úszik |
| Szétoszlás feketén át | az előző kép feketébe halványul, onnan jön elő a következő |
| Szétoszlás fehéren át | ugyanez fehéren keresztül |
| Pásztázás és nagyítás | a kép lassan mozog, és közben egyre nagyobb lesz |

A **Pásztázás és nagyítás** nem a képek közé esik, hanem magán a képen
fut, ezért a **diaidőhöz** igazodik, nem az átmenet hosszához.

### Megjelenítési mód a vetítésben

A **Nézet ▸ Megjelenítési mód** beállítása a vetített képen is látszik —
így a **Projektor mód** ott hat, ahol a legtöbb értelme van. Lásd
[Beállítások](beallitasok.md).

## Videók

A videófájlok ugyanúgy megjelennek a rácsban, mint a képek, és a nézőben
le is játszhatók. A lejátszáshoz a Qt Multimedia modul szükséges; ha
hiányzik, a program fut tovább, csak a lejátszó helyén ezt írja ki:
„A videó-lejátszáshoz a Qt Multimedia modul szükséges."

Az eszköztár szűrőjével csak a videókat is megjelenítheted.

### Az eredeti Picasából hozott vágáspontok

Ha egy videóhoz a régi Picasában megadtál kezdő- és végpontot, a PicasaPy
ezt elolvassa a videó melletti adatokból, és **a lejátszásnál
érvényesíti**:
a kezdőpontra ugrik, a végpontnál megáll, a csúszka pedig csak a
kijelölt szakaszon mozog.

A **fájlhoz nem nyúlunk**, és a vágáspontokat a PicasaPy felületén ma még
**nem lehet megadni vagy módosítani** — csak azt tudjuk használni, ami
már ott van.

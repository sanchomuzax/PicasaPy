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

A néző **összehasonlító módot** is tud: megjelenítheted ugyanazt a képet
kétszer, vagy két különböző képet egymás mellett.

A **Ctrl+Delete** a lemezről törli az éppen látott képet (rákérdezéssel).

A képre jobbgombbal kattintva ugyanazok a parancsok érhetők el, mint a
rácsban: forgatás, mentés, visszaállítás, elrejtés, keresés a lemezen,
tulajdonságok, törlés a lemezről.

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

## Diavetítés

Indítás: **Nézet ▸ Diavetítés**, a **Mappa ▸ Diavetítés megtekintése**,
a néző gombja, vagy a **Ctrl+4** billentyű.

A vetítés valódi teljes képernyőn fut. Vezérlés közben:

| billentyű | mit csinál |
|---|---|
| Szóköz | szünet / folytatás |
| → vagy Enter | következő kép |
| ← | előző kép |
| Ctrl+R | forgatás jobbra |
| Ctrl+Shift+R | forgatás balra |
| Esc | kilépés |

Az egérrel megjelenő vezérlősávon **Kilépés**, **lejátszás/szünet** és
**csillag** gomb van. Ha a vetítés közben csillagozol vagy forgatsz, a
változás megmarad.

Kilépéskor a rács és a néző arra a képre ugrik, ahol a vetítés
abbamaradt.

## Videók

A videófájlok ugyanúgy megjelennek a rácsban, mint a képek, és a nézőben
le is játszhatók. A lejátszáshoz a Qt Multimedia modul szükséges; ha
hiányzik, a program fut tovább, csak a lejátszó helyén ezt írja ki:
„A videó-lejátszáshoz a Qt Multimedia modul szükséges."

Az eszköztár szűrőjével csak a videókat is megjelenítheted.

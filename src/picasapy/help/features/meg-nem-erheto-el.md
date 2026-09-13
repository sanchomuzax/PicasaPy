# Ami még nem érhető el

A PicasaPy menüi az eredeti Picasa 3.9 teljes szerkezetét követik, hogy
ismerős legyen. Emiatt sok olyan tétel is látszik, ami **még nincs
bekötve** — ezek **szürkék**, és nem történik semmi, ha rájuk kattintasz.

Ez a lap felsorolja, mi az, ami ma nem működik, hogy ne keresgélj
fölöslegesen.

## Még nem készült el

**Fájl**

- Fájl(ok) megnyitása szerkesztőben
- E-mail… — a küldés a képtálca **E-mail** gombjával viszont **működik**,
  lásd [Küldés e-mailben](email.md)

**Szerkesztés**

- Szövegmezők helyi menüjében: Automatikus kitöltés

**Nézet**

- Szerkesztési nézet — a **Ctrl+3** billentyű viszont **működik**: a
  kijelölt képet megnyitja a nézőben
- Szerkesztési vezérlők megjelenítése
- Keresési opciók
- Kis képek
- Időrend (Ctrl+5) — a nézet még nem készült el, ezért a menüpont és a
  billentyű is inaktív
- Megjelenítési mód ▸ 16 bites (szemcsézett)

(A **Színkezelés használata** kapcsoló viszont már **működik** — lásd
[Beállítások](beallitasok.md).)

**Mappa**

- Leírás szerkesztése… — a mappa helyi menüjének **Mappaleírás
  szerkesztése…** tétele viszont **működik**
- A mappalista helyi menüjében: Elrejtés, Megjelenítés, Indexképek
  megjelenítése a könyvtárban, Gyorsbillentyűk, Asztal — a **Nézet ▸
  Mappanézet** almenü **Indexképek megjelenítése a könyvtárban** tétele
  viszont **működik**

**Kép**

- Megjelenítés és szerkesztés — a **Ctrl+3** billentyű viszont
  **működik**
- Szöveg megjelenítése, Szöveg elrejtése
- Megjelenítés
- Arcok alaphelyzetbe állítása

**Létrehozás**

- Poszter készítése…
- Hozzáadás a képernyővédőhöz…
- Ajándék CD készítése…

**Eszközök**

- Személyek kezelése…
- Fotómegjelenítő beállítása…
- Képernyővédő konfigurálása…
- Dátum és idő beállítása…
- Gombok konfigurálása…

(A **Képek biztonsági mentése…** tétel viszont már **működik** — lásd
[Képek biztonsági mentése](biztonsagi-mentes.md).)

**Súgó**

- Billentyűkódok — lásd [Billentyűparancsok](billentyuk.md)
- Frissítések keresése

(A **Súgó - tartalom és tárgymutató** tétel és az **F1** billentyű ma
már **működik**: ezt a súgót nyitja meg — lásd
[A beépített súgó](sugo.md).)

**A nézőben**

- **Két különböző kép megjelenítése** — a néző alsó sávjában lévő
  harmadik szegmens. Két *különböző* kép egymás mellé tétele még nem
  készült el; ugyanannak a képnek a szerkesztés előtti és mostani
  állapota viszont **megjeleníthető** egymás mellett, lásd
  [Nézegetés](nezegetes.md).

**Helyi menükben**

- Hozzáadás az Emberek albumhoz
- Beállítás az Emberek album indexképeként
- Mappa felosztása itt…
- Társítás
- Névcímkék hozzáadása
- Album törlése, Albumleírás szerkesztése…, Album rendezésének alapja
- Jelszó megadása/módosítása…
- Az Emberek album törlése, Az Emberek album szerkesztése…
- Feltöltés tiltása — a Picasa Webalbumok megszűnt szolgáltatás
- A **Mappa ▸ Mappa rendezése** almenüben a **Legutóbbi változtatások**
  szerinti rendezés (a bal hasáb helyi menüjéből viszont **működik**)

**Beállítások**

A **Beállítások** párbeszéd nyolc füléből ma kettőn van élő vezérlő:

- **Általános** — a nyelv, a törlés-megerősítés és a duplikátum-észlelés
  kapcsolója, valamint a **Gyorsítótár ürítése…** gomb,
- **E-mail** — a levelezőprogram megválasztása és a küldött képek mérete
  (lásd [Küldés e-mailben](email.md)). Ugyanezen a fülön a videók
  küldési módja és az Outlook-kapcsoló még szürke.

A többi hat fül vezérlői szürkék. A **Diavetítés** fül is köztük van,
pedig a vetítésnek vannak beállításai — azokat magán a vetítés
vezérlősávján állítod, és a program meg is jegyzi őket. Lásd
[Nézegetés](nezegetes.md).

## Megszűnt szolgáltatások — ezek nem is fognak elkészülni

A Google 2016-ban leállította a Picasa online szolgáltatásait. Az alábbi
menüpontok a szerkezet miatt látszanak, de mögöttük **nincs és nem is
lesz** működő szolgáltatás:

- Importálás a Google Fotókból…
- Papírképek rendelése…
- Közzététel a Bloggeren…
- Feltöltéskezelő…, Csoportos feltöltés…, Feltöltés
- Feltöltés a Picasa Webalbumokba…, Feltöltés a Google Fotókba…,
  Gyors feltöltés, Feltöltés blokkolása, Online műveletek
- Picasa-fórumok, Online információ, Termékkiadási tájékoztató,
  Adatvédelmi irányelvek, Általános Szerződési Feltételek
- Megjelenítési mód ▸ Távoli asztal — kifejezetten a windowsos távoli
  asztalhoz készült, nálunk nincs értelme

Ugyanezért nem működik a menüsor jobb szélén látható „Bejelentkezés
Google Fiókkal" felirat sem — az csak az eredeti elrendezés része.

## Amit a program tud, de a felület még nem kínál

- **Virtuális albumok a `.picasa.ini`-ből** — a PicasaPy elolvassa és
  változatlanul megőrzi őket, de böngészni még nem lehet bennük.
- **Régi Picasa-adatbázis behozatala** — a program el tudja olvasni a
  régi Picasa adatfájljait, de az adatok átemelése a saját indexbe még
  nem készült el. A régi telepítés **figyelt mappáit** viszont át tudja
  venni, lásd [Importálás](importalas.md).
- **Névjegyzék írása** — a régi Picasa névjegyzékét olvassuk, de írni még
  nem tudjuk.
- **Videó vágáspontjai** — ha a régi Picasában megadtál egy videóhoz
  kezdő- és végpontot, a lejátszás betartja, de **megadni vagy
  módosítani ma nem lehet** a PicasaPy felületén. Lásd
  [Nézegetés](nezegetes.md).
- **A rejtett mappák jelszava** — a jelszó-kapu megvan a programban (a
  **Nézet ▸ Rejtett képek** bekapcsolása jelszót kérne, ha volna
  beállítva), de **jelszót ma nem lehet megadni a felületről**: a
  **Jelszó megadása/módosítása…** menüpont még nincs bekötve. Amíg ez
  így van, a rejtett képek jelszó nélkül előhozhatók. A rejtés
  egyébként sem védi a fájlokat: azok a lemezen változatlanul ott
  vannak, csak a PicasaPy nézeteiből tűnnek el.

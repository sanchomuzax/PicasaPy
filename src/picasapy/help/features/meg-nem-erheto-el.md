# Ami még nem érhető el

A PicasaPy menüi az eredeti Picasa 3.9 teljes szerkezetét követik, hogy
ismerős legyen. Emiatt néhány olyan tétel is látszik, ami **még nincs
bekötve** — ezek **szürkék**, és nem történik semmi, ha rájuk kattintasz.

Ez a lap felsorolja, mi az, ami ma nem működik, hogy ne keresgélj
fölöslegesen.

> **A szürke szín magában nem jelenti, hogy egy funkció hiányzik.** A
> működő menüpontok is szürkék, amikor **épp nem használhatók** —
> mondjuk kijelölés nélkül, vagy a nézőben. Ilyenkor jelölj ki egy képet,
> vagy térj vissza a könyvtárba, és a tétel felélesedik. Csak az van
> tartósan szürkén, ami ezen a lapon szerepel.

## Még nem készült el

**Nézet**

- Időrend (Ctrl+5) — a nézet még nem készült el, ezért a menüpont és a
  billentyű is inaktív
- Keresési opciók

**Mappa**

- A **Mappa ▸ Mappa rendezése** almenüben a **Legutóbbi változtatások**
  szerinti rendezés (a bal hasáb helyi menüjéből viszont **működik**)

**Eszközök**

- Feltöltés (almenü)

**Súgó**

- Billentyűkódok — a billentyűparancsok listáját itt találod:
  [Billentyűparancsok](billentyuk.md)

(A **Súgó - tartalom és tárgymutató** tétel és az **F1** billentyű
**működik**: ezt a súgót nyitja meg — lásd [A beépített súgó](sugo.md).)

**Helyi menükben**

- Társítás (a kép helyi menüjében és a nézőben)
- Névcímkék hozzáadása (a mappa és az album helyi menüjében)
- Mappa felosztása itt…
- Album törlése, Album rendezésének alapja — az **Albumleírás
  szerkesztése…** viszont **működik**, lásd [A könyvtár](konyvtar.md)
- Jelszó megadása/módosítása… a saját gyűjteményeken — a **Rejtett
  mappák** fejlécén viszont **működik**, lásd [A könyvtár](konyvtar.md)
- Az Emberek album törlése, Az Emberek album szerkesztése…, Beállítás
  az Emberek album indexképeként

**Beállítások**

A **Beállítások** párbeszéd nyolc füléből hat működik: az **Általános**,
a **Fájltípusok**, az **E-mail**, a **Diavetítés**, a **Névcímkék** és a
**Nyomtatás** (lásd [Beállítások](beallitasok.md)). Szürke marad:

- a **Hálózat** fül egésze,
- a **Webalbumok** fül — a Picasa Webalbumok megszűnt szolgáltatás,
- az **Általános** fülön az **Automatikus frissítések** sor és a
  **Névtelen használati statisztikák küldése a Google részére**
  jelölőnégyzet,
- az **E-mail** fülön a **Szövegközi fotók és képfeliratok küldése
  (csak Outlookban)** jelölőnégyzet.

## Megszűnt szolgáltatások — ezek nem is fognak elkészülni

A Google 2016-ban leállította a Picasa online szolgáltatásait. Az alábbi
menüpontok a szerkezet miatt látszanak, de mögöttük **nincs és nem is
lesz** működő szolgáltatás:

- Importálás a Google Fotókból…
- Papírképek rendelése…
- Közzététel a Bloggeren…
- Feltöltéskezelő…, Csoportos feltöltés…, Feltöltés
- Feltöltés a Picasa Webalbumokba…, Feltöltés a Google Fotókba…,
  Gyors feltöltés, Feltöltés tiltása, Online műveletek
- Picasa-fórumok, Online információ, Termékkiadási tájékoztató,
  Adatvédelmi irányelvek, Általános Szerződési Feltételek
- Frissítések keresése — a frissítések ellenőrzése is egy Google-szolgáltatásra
  épült
- Megjelenítési mód ▸ Távoli asztal — kifejezetten a windowsos távoli
  asztalhoz készült, nálunk nincs értelme

Ugyanezért nem működik a menüsor jobb szélén látható „Bejelentkezés
Google Fiókkal" felirat sem — az csak az eredeti elrendezés része.

## Amit a program tud, de a felület még nem kínál

- **Virtuális albumok a `.picasa.ini`-ből** — a PicasaPy elolvassa és
  változatlanul megőrzi őket, de böngészni még nem lehet bennük.
- **Régi Picasa-adatbázis behozatala** — a nevek, a kulcsszavak és a
  helyek átvétele már **működik** (**Eszközök ▸ Import a Picasából…**,
  lásd [Importálás](importalas.md)); a régi adatbázis többi tartalmát
  még nem emeljük át.
- **Névjegyzék írása** — a régi Picasa névjegyzékét olvassuk, de írni még
  nem tudjuk.

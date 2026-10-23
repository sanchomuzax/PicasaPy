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

(A **Súgó** menü tételei közül a **Súgó - tartalom és tárgymutató** az
**F1** billentyűvel együtt, valamint a **Billentyűkódok** **működik**:
az előbbi ezt a súgót nyitja meg — lásd [A beépített súgó](sugo.md) —,
az utóbbi a működő gyorsbillentyűk listáját, lásd
[Billentyűparancsok](billentyuk.md).)

**Helyi menükben**

- Társítás a néző helyi menüjében — a könyvtárban, a kép helyi menüjében
  viszont **működik**, lásd [Fájlműveletek](fajlmuveletek.md)
- Jelszó megadása/módosítása… a saját gyűjteményeken — a **Rejtett
  mappák** fejlécén viszont **működik**, lásd [A könyvtár](konyvtar.md)

**Beállítások**

A **Beállítások** párbeszéd nyolc füléből hat működik: az **Általános**,
a **Fájltípusok**, az **E-mail**, a **Diavetítés**, a **Névcímkék** és a
**Nyomtatás** (lásd [Beállítások](beallitasok.md)). A **Hálózat** fülön
csak a naplózás működik. Szürke marad:

- a **Hálózat** fülön a proxy-beállítások (a két mező és az
  **Hálózati beállítások automatikus észlelése** jelölőnégyzet),
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
- Az **Eszközök ▸ Feltöltés** almenü három tétele: Feltöltés a Google
  Fotókba, Feltöltés közös szerkesztésű webalbumba, Feltöltés a YouTube
  webhelyre. Az almenü kinyílik, de a tételei szürkék.
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

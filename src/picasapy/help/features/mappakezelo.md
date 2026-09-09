# Mappakezelő és figyelt mappák

A PicasaPy csak azokat a mappákat mutatja, amiket megadtál neki. Ezeket
hívjuk **figyelt mappáknak**.

## A Mappakezelő

Megnyitás: **Eszközök ▸ Mappakezelő…** vagy **Fájl ▸ Mappa hozzáadása a
Picasához…**

Bal oldalt a **Mappalista**, jobb oldalt **A jelenlegi mappára**
vonatkozó beállítások. Ha még nem választottál semmit, ez áll ott:
„Jelölj ki egy mappát bal oldalt."

### Beállítások mappánként

- **Keresés mindig** — a program figyeli a mappát, és az új képek
  maguktól megjelennek.
- **Keresés egyszer** — most átnézi, de utána nem figyeli tovább.
- **Eltávolítás a Picasából** — a mappa kikerül a nézetből. A lemezen
  lévő fájlokhoz **nem nyúl**.
- **Arcfelismerés bekapcsolva / kikapcsolva** — mappánként külön
  eldöntheted, keressen-e arcokat. A beállítás a mappára **és az alfáira**
  is vonatkozik.

Az **OK** gomb menti a változtatásokat, a **Mégse** elveti őket.

### Ha kikapcsolod az arcfelismerést

Az **OK** megnyomásakor a program megkérdezi: „Biztosan eltávolítja az
összes arcot és névcímkét a kihagyott mappákból?"

- **Igen** esetén a mappa és az alfái képeiről törlődnek azok az arcok,
  amiket a program maga talált, és a képek jelölést kapnak, hogy a
  következő arckeresés ne nézze meg őket újra.
- A **nevek és arckeretek, amiket még a Picasában vettél fel**,
  megmaradnak: azok a te saját adataid, azokhoz a program nem nyúl.
- **Nem** esetén semmi nem mentődik el — sem az arcfelismerés kapcsolója,
  sem a többi változtatásod —, és a Mappakezelő nyitva marad.

> A jelölés akkor is megmarad, ha **később visszakapcsolod** az
> arcfelismerést a mappára: a már megjelölt képeken a keresés nem indul
> újra. Az eredeti Picasa is így viselkedik. A jelölés visszavonására ma
> nincs parancs a felületen.

### Ha nem sikerül felvenni

A Mappakezelő megmondja, mi a baj:

- „Ez a mappa már figyelve van" — már benne van a listában.
- „Ez a mappa nem nyitható meg" — nincs jogosultságod, vagy nem létezik.
- Egyéb hiba esetén a program kiírja az okot.

### Súgó a párbeszéden belül

A **Súgó** gomb egy rövid, helyben olvasható magyarázatot nyit meg
(„Mappakezelő — Súgó").

## Elérhetetlen mappák

Ha egy figyelt mappa hálózati megosztáson vagy külső lemezen van, és az
épp nincs csatlakoztatva, a hasábon ez látszik: „Jelenleg nem elérhető —
a mappa az adatbázisban marad, a bélyegképek a gyorsítótárból látszanak."

Ilyenkor a képek böngészhetők, de nem nyithatók meg és nem
szerkeszthetők. Amint a lemez visszakerül, minden magától működik tovább.

## Mappa-parancsok a hasábon

A mappára jobbgombbal kattintva:

- **Az összes kép kijelölése**, **Kiválasztás megfordítása**,
  **Kijelölés törlése**
- **Mappa rendezése** — dátum, név, méret, fordított sorrend
- **Indexképek frissítése** — újraolvassa a mappát
- **Mappaleírás szerkesztése…** — név, dátum, hely és leírás; a mappához
  zene is választható a diavetítéshez és a filmhez
- **Mappa elrejtése** / **Mappa megjelenítése**
- **Keresés a lemezen** — megnyitja a fájlkezelőben
- **Áthelyezés gyűjteménybe** — meglévőbe vagy újba
- **Mappa áthelyezése…**, **Mappa törlése…**
- **Eltávolítás a Picasából…** — csak a nézetből veszi ki
- **Exportálás HTML-oldalként…**

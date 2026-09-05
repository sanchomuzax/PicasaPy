# Emberek és arcok

A PicasaPy megkeresi az arcokat a képeiden, csoportokba rendezi őket, és
neveket rendelhetsz hozzájuk. A neveket a `.picasa.ini` fájlba írja, tehát
az eredeti Picasa is látja őket.

## Arcok keresése

**Eszközök ▸ Arcok keresése…** nyitja meg a párbeszédet. Két lépés van
benne:

1. **Arcok keresése** — végigmegy a képeken, és megjelöli az arcokat.
   Közben mutatja a haladást, és bármikor megszakítható. A végén kiírja,
   hány arcot talált és hány képet nézett át.
2. **Arcok csoportosítása** — az egy emberhez tartozónak látszó arcokat
   egy csoportba teszi.

Az arckereséshez a program egy felismerő modellt használ. Ha még nincs
letöltve, a párbeszéd felajánlja a **Modell letöltése** gombot, és mutatja
a letöltés haladását. A letöltés egyszeri.

Az arckeresést mappánként is szabályozhatod, lásd
[Mappakezelő](mappakezelo.md).

## Az Emberek panel

Megnyitás: **Nézet ▸ Emberek**, vagy a képtálca Emberek gombja.

A panel megmutatja, kik szerepelnek az éppen kijelölt képen, és kik
láthatók még a többi kiválasztott képen.

A bal hasáb **Emberek** csoportjában minden névhez tartozik egy album. A
névre jobbgombbal kattintva kijelölheted az összes képét, vagy törölheted
a kijelölést.

## Névtelen arcok

A bal hasáb **Névtelenek** bejegyzése a még el nem nevezett arcokat
gyűjti. Itt:

- A **Csoportosítás arc szerint** kapcsolóval egy emberhez tartozó
  arcokat egyben látod. A **Csoportok kibontása** szétnyitja őket.
- Egy arc alá beírt névvel elnevezed. Ha a program tippel valakire, a név
  mellett kérdőjel áll — egy kattintás elfogadja.
- A **Mellőzés** paranccsal félreteszed azokat az arcokat, amiket nem
  akarsz elnevezni (járókelők, plakátok). A mellőzött arcok a **Mellőzött
  emberek** alá kerülnek, ahonnan a **Mellőzés visszavonása** hozza őket
  vissza.

## Arcok a nézőben

A nézőben az **Arcok megjelenítése** gomb (vagy az `F` billentyű) mutatja
az arckereteket. Az **Arcok szerkesztése** (Shift+`F`) módban a keretekhez
nevet írhatsz.

> Az **Arcok alaphelyzetbe állítása** menüpont **még nem működik**: a
> helye megvan, de az arcadatok törlése mögötte még nincs bekötve.

## Emberek albumok

Az **Áthelyezés új személyhez…** paranccsal egy rosszul besorolt arcot új
névhez rendelhetsz, az **Eltávolítás az Emberek albumból** (Ctrl+Delete)
pedig kiveszi onnan.

> A helyi menü **Beállítás az Emberek album indexképeként** és
> **Hozzáadás az Emberek albumhoz** tétele **még nem működik** — az
> emberalbumok saját borítóképét ma nem lehet megválasztani.

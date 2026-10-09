# Küldés e-mailben

A kijelölt képeket a számítógép saját levelezőprogramjával küldheted
el: a PicasaPy előkészíti a mellékleteket, te a saját ablakában megírod
a levelet, a **Küldés** után pedig megnyílik a levelezőprogramod egy új
levéllel, amiben már ott vannak a képek.

Háromféleképpen indíthatod: a képtálca **E-mail** gombjával, a
**Fájl ▸ E-mail…** paranccsal, vagy a **Ctrl+E** billentyűvel. Az
utóbbi nem sül el, amíg egy szövegmezőbe gépelsz.

## Ahogy történik

1. Jelöld ki a képeket.
2. Indítsd az e-mailezést (gomb, menü vagy Ctrl+E).
3. A program előkészíti a mellékleteket („Mellékletek előkészítése…"),
   és szükség esetén átméretezi a képeket.
4. Megnyílik a **Képek küldése e-mailben** ablak (lásd lent).
5. A **Küldés** gombra a levelezőprogramod új levéllel nyílik meg, a
   képek csatolva.

A mellékletek mindig a **szerkesztett** képet viszik: a forgatás, a
tükrözés és minden szerkesztés bele van égetve, ahogy exportáláskor
([Exportálás](exportalas.md)). **Eredeti méret** esetén sincs
átméretezés, de a szerkesztések itt is benne vannak. Az eredeti fájlt
a küldés nem érinti.

## A levélszerkesztő ablak

Itt állítod össze a levelet:

- **Címzett:** és **Tárgy:** mező, alattuk a levél szövege;
- a mellékletek **kis képei** egy sávban — rákattintva kijelölsz egyet,
  a **×** gomb a kijelöltet **kiveszi a mellékletből** (a kép a
  lemezen marad);
- **Elvetés** — bezárja az ablakot, nem küld semmit;
- **Küldés** — átadja a levelet a levelezőprogramnak.

A címzettet nem kötelező kitölteni: a levelezőprogramban is megadhatod.

A **Címzett:** mezőre jobbgombbal kattintva a helyi menüben ott az
**Automatikus kitöltés** pipás kapcsoló, ahogy az eredeti Picasában. Alapból
be van kapcsolva, és a program megjegyzi, hogyan hagytad.

## Levelezőprogram-választó

Amíg nem döntöttél másképp, az **első küldésnél** a program előbb a
**Válasszon levelezőprogramot** lapot mutatja. Itt a **LEVELEZŐPROGRAM**
tételt hagyod jóvá: a képek a számítógép alapértelmezett
levelezőprogramjában nyílnak meg új levélként. A **Google Mail**
tétel szürke, nem választható: a PicasaPy-nak nincs Google-fiók-kapcsolata.

Ha bejelölöd a **Jegyezze meg ezt a beállítást, ne jelenítse meg a
párbeszédpanelt újra** pipát, legközelebb a program egyből a
levélszerkesztőt nyitja. (Ez ugyanaz a kapcsoló, mint a Beállítások
E-mail fülén — bármikor visszaállíthatod.)

## Beállítások ▸ E-mail

Az **Eszközök ▸ Beállítások… ▸ E-mail** fülön:

- **Levelezőprogram** — **A számítógép alapértelmezett
  levelezőprogramjának használata**, vagy **Minden képküldésnél
  kiválasztom** (ilyenkor mindig megjelenik a választó lap). A **Google
  Fiók használata** szürke.
- **Több kép mérete** — csúszka: ekkora hosszabbik oldalra kicsinyíti a
  képeket küldés előtt. A csúszka mellett a pillanatnyi érték látszik
  képpontban.
- **Egyedülálló képek mérete** — vagy **Több elemmel azonos**, vagy
  **Eredeti méret**.
- **Mozgófilmek küldése másként** — videónál vagy az **Első
  képkocka** megy mellékletként (egy állókép), vagy a **Teljes
  mozgófilm**. A választás megmarad.

Az Outlookos beágyazott képek kapcsolója (**Szövegközi fotók és
képfeliratok küldése (csak Outlookban)**) szürke — ez még nem működik.

## Ha nem indul el a küldés

Ha a rendszereden nincs levelezőprogram beállítva, a program szól:
**Nem található levelezőprogram.** Ha van ugyan, de nem tud mellékletet
fogadni, üres levél nyílik a képek nélkül, és ezt a program külön
jelzi. A mellékletek előkészítésének hibája is megjelenik a felület
tetején, nem vész el némán.

Befejezetlen kollázst nem lehet elküldeni: előbb fejezd be.

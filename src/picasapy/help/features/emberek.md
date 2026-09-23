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

### Egy képet csak egyszer néz át

A program megjegyzi, melyik képen futott már le az arckeresés, és a
következő keresés átugorja azokat. Ez az arc nélküli képekre is
vonatkozik: eddig azokat minden keresés újra átnézte, mert nem maradt
utánuk nyom. Ha a kép később megváltozik — átszerkeszted vagy kicseréled
—, a keresés újra megnézi.

Az arckeresést mappánként is szabályozhatod, lásd
[Mappakezelő](mappakezelo.md). Ha ott kikapcsolod egy mappára, a program
a mappa képeit is megjelöli, hogy a keresés ne induljon rájuk újra — a
részletek ugyanott.

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
- A **További javaslatok keresése** gombbal egyetlen kattintással több
  névjavaslatot kérsz: a program egyszer lejjebb viszi a felismerési
  küszöbét, és újra megnézi, kire tud tippelni. A **tárolt beállítás nem
  változik** — a következő keresés megint a szokásos szigorúsággal fut.
  A mellőzött arcok nézetében ez a gomb nem látszik.

## Arcok a nézőben

A nézőben az **Arcok megjelenítése** gomb (vagy az `F` billentyű) mutatja
az arckereteket. Az **Arcok szerkesztése** (Shift+`F`) módban a keretekhez
nevet írhatsz.

Ebben a módban **új arcot is felvehetsz**: húzz keretet az arc köré, majd
kattints a keret alatt megjelenő **Név hozzáadása** feliratra. A keret a
húzás után megmarad, tehát előbb pontosan ráigazíthatod az arcra.

Húzás közben a **Shift**, a **Ctrl** és az **Alt** megköti a keret
oldalarányát, ugyanúgy, mint a vágónál — a részletek a
[Szerkesztő](szerkeszto.md) fejezetben.

> Az **Arcok alaphelyzetbe állítása** menüpont **még nem működik**: a
> helye megvan, de az arcadatok törlése mögötte még nincs bekötve.

## A nevek átadása más programoknak

Ha nevet adsz egy arcnak, a program a kép mellé — **a képfájl
átírása nélkül** — kiír egy kis kísérőfájlt is, benne az arc helyével és
nevével. Ez magától történik, nem kell kérned. Két szabvány szerint
egyszerre írja ki, hogy a Windows Fotógaléria és a digiKam vagy a
Lightroom is felismerje.

Ha egy fájlt nem sikerül megírni — például mert a mappa írásvédett —, a
program megnevezve jelzi, **a névadás viszont érvényben marad**.

### Egy egész mappára, egyben

Az **Eszközök ▸ Kísérleti ▸ Arcinformációk írása XMP-adatokba…**
paranccsal az **épp látott mappa** összes képére kiíratod ugyanezt.
Hasznos, ha a neveket még a régi Picasában adtad meg, vagy ha
írásvédettség miatt korábban kimaradt néhány kép.

Közben a jobb felső sarokban kis panel mutatja a haladást (**Arccímkék
írása**, alatta hány kép készült el), és a **Mégse** gombbal
megszakítható. A megszakítás után a program megmondja, hány fájlba írt —
azok érvényesek maradnak.

A végén összegzést kapsz: hány fájlba írt, hányat hagyott ki, és ha volt
hiba, mi volt az első.

## Javaslatok jóváhagyása egy személy albumában

Ha egy személy albumát nyitod meg, a rács **kétféle képet mutat**: azokat,
amelyeken a név már rá van írva egy arcra, és azokat, amelyeken a program
még csak **tippel** erre a névre. Így egy helyen látod, mit döntöttél el, és
mi vár még rád. Egy kép akkor is egyszer szerepel, ha több arca hordozza
ugyanazt a javaslatot.

Ha van még el nem döntött javaslat, a fejlécben két gomb jelenik meg:

- **Az összes jóváhagyása (N)** — ráírja a nevet az arcokra; a képek
  ettől bekerülnek a személy albumába. A zárójelben az eldöntetlen
  javaslatok száma áll.
- **Eltávolítás** — csak a javaslatokat veti el. Az arc névtelen marad,
  és egy későbbi keresés újra megvizsgálhatja.

Ha nincs mit eldönteni, ugyanezen a helyen a **További javaslatok
keresése** gomb áll — ugyanaz, mint a Névtelenek nézetben.

### Csak a javaslatokat mutasd

A gombok bal oldalán egy kis, benyomható gomb áll: **Csak a javaslatok
megjelenítése (ha be van kapcsolva)**. Benyomva a rácsban csak azok a
képek maradnak, amelyeken még döntened kell — a már elnevezett arcok
képei eltűnnek. Újra megnyomva mindent visszakapsz.

A gomb akkor is kint marad, ha közben elfogytak a javaslatok, hogy a szűrt,
üres nézetből mindig ki tudj lépni. Az album **minden megnyitása szűrő
nélkül indul**: a szűrő nem marad meg a következő alkalomra. Jóváhagyás
vagy elvetés után viszont igen — a rács frissül, a szűrő állása marad.

## Emberek albumok

Az **Áthelyezés új személyhez…** paranccsal egy rosszul besorolt arcot új
névhez rendelhetsz, a **Hozzáadás az Emberek albumhoz** almenüből pedig egy
már meglévő személyhez teheted át — az almenü a többi személyt sorolja fel.
Az **Eltávolítás az Emberek albumból** (Ctrl+Delete) kiveszi onnan.

> A helyi menü **Beállítás az Emberek album indexképeként** tétele **még
> nem működik** — az emberalbumok saját borítóképét ma nem lehet
> megválasztani.

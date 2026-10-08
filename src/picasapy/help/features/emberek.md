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

Az arcfelismerő a programmal együtt települ, **nem kell hozzá semmit
letöltened** — tiszta telepítés után is azonnal működik. (A párbeszéd
csak akkor mutat **Modell letöltése** gombot, ha a felismerő fájlja
valamiért hiányzik a telepítésből. Ha a fájl megvan, de a program nem
tudja betölteni, ezt írja: „A modellfájl megvan, de a PicasaPy nem tudta
betölteni.", és a részleteket a hibanaplóba teszi.)

A keresés **magától is fut a háttérben**: az új képeken a program
automatikusan arcokat keres. Ez alapból be van kapcsolva; a
**Beállítások ▸ Névcímkék** fülön kikapcsolhatod (lásd
[Beállítások](beallitasok.md)). Ha az arckeresés valamiért nem tud
elindulni, az okát a program a hibanaplóba írja, nem hagyja némán.

A keresés **ritkán jelöl arcot ott, ahol nincs**: egy tájképen vagy
más, arc nélküli felvételen nem jelenik meg téves keret.

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

A panel **egy fejlécet és egy listát** mutat: a kijelölt képeken
megnevezett embereket. A fejléc szövege attól függ, hol állsz és mit
jelöltél ki:

| amikor | a fejléc |
|---|---|
| egy kép van kijelölve (vagy a nézőben állsz), és van rajta név | **Ezen a fotón:** |
| egy kép van kijelölve, és még nincs rajta név | **Ki látható ezeken a fotókon?** |
| több kép, és van rajtuk név | **Személyek ezeken a fotókon:** |
| egy személy albumában (ott egy képnél is ez áll) | **Szintén ezeken a fotókon:** — a lista a nézett személyt nem sorolja fel, csak a vele együtt szereplő többieket |
| több kép, és nincs rajtuk név | **Név nélküli személycsoportok:** |
| a Névtelenek albumban, csoportosított nézetben | **Meg nem nevezett emberek ezeken a fotókon:** |

Ha nincs mit felsorolni, a fejléc helyén egy dőlt mondat mondja meg, mi
kerül majd ide — személy albumában például: „Itt jelennek meg azok az
elnevezett emberek, akik a kiválasztott személlyel együtt szerepelnek."

A lista soraiban **arcképek** állnak: a névvel ellátott embereknél az
arc kis, kivágott képe és mellette a név — a névre kattintva a személy
albumára lépsz. A kijelölt képeken lévő **még névtelen arcok** is
megjelennek a lista végén, egy-egy arcképpel és egy **Név hozzáadása**
mezővel. Írd be a nevet, és nyomj **Entert**: az arc el van nevezve.
Az arckép sarkában lévő **×** (**Személy mellőzése**) a mellőzést
kéri: a program rákérdez, hogy valóban a Mellőzött emberek albumba
kerüljön-e az arc.

A bal hasáb **Emberek** csoportjában minden névhez tartozik egy album. A
névre jobbgombbal kattintva kijelölheted az összes képét, vagy törölheted
a kijelölést.

## Névtelen arcok

A bal hasáb **Névtelenek** bejegyzése a még el nem nevezett arcokat
gyűjti. Itt:

- Az album csoportosítva nyílik: egy emberhez tartozó arcokat egyben
  látod. A fejléc **Csoportok részletes nézete** gombja szétnyitja őket,
  ugyanott a **Csoportosítás arcok szerint** visszacsukja. A gomb alatt
  egy sor mondja meg, mi a következő lépés: „Jelöljön ki valakit, akit
  ismer, és adjon hozzá egy nevet" — szétnyitott csoportoknál azzal is,
  hogy az „x" ikonra kattintva mellőzheted az illetőt. Amíg a program a
  csoportokat számolja, ehelyett ez áll ott: „Az arcok csoportosítása
  folyamatban van, kérjük, várjon…"
- Egy arc alá beírt névvel elnevezed. Ha a program tippel valakire, a név
  mellett kérdőjel áll — egy kattintás elfogadja.
- A **Mellőzés** paranccsal félreteszed azokat az arcokat, amiket nem
  akarsz elnevezni (járókelők, plakátok). Ugyanezt teszi a csempe
  sarkában lévő **✕**. A program rákérdez — „Biztosan áthelyezi ezt a
  személyt a Mellőzött emberek albumba?" —, és a **Ne kérdezzen újból,
  mindig hagyja figyelmen kívül** pipával legközelebb kérdés nélkül
  mellőz. A mellőzött arcok a **Mellőzött emberek** alá kerülnek, ahonnan
  a **Mellőzés visszavonása** hozza őket vissza.
- A **További javaslatok keresése** gombbal egyetlen kattintással több
  névjavaslatot kérsz: a program egyszer lejjebb viszi a felismerési
  küszöbét, és újra megnézi, kire tud tippelni. A **tárolt beállítás nem
  változik** — a következő keresés megint a szokásos szigorúsággal fut.
  A mellőzött arcok nézetében ez a gomb nem látszik.

### A mellőzés az eredeti Picasával is közös

A mellőzést a program **a kép mellé, a `.picasa.ini` fájlba** is
bejegyzi, ugyanazzal a jelöléssel, amit az eredeti Picasa használ. Ennek
két látható következménye van:

- ha egy mappát korábban az **eredeti Picasában** dolgoztál fel, az ott
  mellőzött arcok itt is a **Mellőzött emberek** albumban jelennek meg —
  akkor is, ha a PicasaPy arckeresője magától nem talált ott arcot;
- amit itt mellőzöl, azt az eredeti Picasa is mellőzöttnek látja, és egy
  későbbi arckeresés sem kínálja fel újra.

Mivel a két program arckeresője nem ugyanaz, a keretek nem pontosan
egyeznek: a PicasaPy az egymást nagyrészt átfedő kereteket **ugyanannak
az arcnak** tekinti, és nem mutatja kétszer.

## Személyek kezelése

Az **Eszközök ▸ Személyek kezelése…** egy ablakot nyit, ahol az ismert
személyek névjegyzékét rendezed:

- a bal oldali listában a személyek állnak, fölötte **Keresés:** mező;
- **Új személy** — új, még üres nevű bejegyzést vesz fel;
- **Személy törlése** — kiveszi a kijelöltet a névjegyzékből;
- a kijelölt személynél látod a hozzá tartozó fotók számát és az
  **Ismerős azonosítója:** mezőt, a **Név:** és az **E-mail:** mező
  szerkeszthető; a **Visszaállítás** a kijelölt személy módosításait
  elveti.

A változtatások az **OK** gombra lépnek életbe (a **Mégse** eldobja
őket); az OK addig szürke, amíg valamelyik személy neve üres. A nevek a
közös névjegytárba kerülnek, a mappák `.picasa.ini` fájlja pedig csak
azoknál a mappáknál változik, ahol az érintett személy szerepel. E-mail
címet csak olyan személyhez lehet menteni, akinek már van névcímkéje
valamelyik mappában.

Az ablak három további eleme — **Arccímkék szinkronizálása a Google
Webalbumokkal**, **Online címtár kezelése**, **Névjegyek frissítése** —
szürke: a Google-szolgáltatás megszűnt.

## Arcok a nézőben

A nézőben az **Arcok megjelenítése** gomb (vagy az `F` billentyű) mutatja
az arckereteket. Az **Arcok szerkesztése** (Shift+`F`) módban a keretekhez
nevet írhatsz.

Ebben a módban **új arcot is felvehetsz**: húzz keretet az arc köré, majd
kattints a keret alatt megjelenő **Név hozzáadása** feliratra. A keret a
húzás után megmarad, tehát előbb pontosan ráigazíthatod az arcra — a
képernyőn megjelenő útmutató is ezt írja.

A mellőzött vagy érvénytelen arcra a néző **nem rajzol keretet**, és az
üres névvel húzott kézi négyszöget a program nem menti el.

A név beírását **Enterrel** kell lezárni, vagy rá kell kattintani az
egyik felajánlott névre. Enélkül a program nem tudja, hogy befejezted.

Húzás közben a **Shift**, a **Ctrl** és az **Alt** megköti a keret
oldalarányát, ugyanúgy, mint a vágónál — a részletek a
[Szerkesztő](szerkeszto.md) fejezetben.

### Arcok alaphelyzetbe állítása

A **Kép ▸ Arcok alaphelyzetbe állítása** a **kijelölt képeken** (a
nézőben az aktuális képen) törli az arckereteket — a rájuk írt neveket
és mellőzéseket is —, majd a program a háttérben **újra megkeresi** az
arcokat ugyanezeken a képeken. Más képekhez nem nyúl. A személyek
névjegyzéke megmarad. Nincs külön megerősítés, ezért csak a valóban
kijelölt képeken használd.

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

### Egyenként is dönthetsz: jelölj ki képeket

Nem kell mindent egyszerre elfogadnod vagy elvetned. **Jelöld ki azokat a
képeket a rácsban**, amelyekről dönteni akarsz, és a két gomb csak rájuk
hat:

- A jóváhagyó gomb felirata **Jóváhagyás**-ra rövidül (darabszám nélkül), a
  súgója pedig **Kijelölt javaslatok jóváhagyása** — így látszik, hogy most
  nem az összesre hat.
- Az **Eltávolítás** ugyanígy szűkül; a súgója **Kijelölt javaslatok
  törlése**.

A váltás magától történik: akkor lép be, ha a kijelölt képeken van még el
nem döntött javaslat **erre a névre**. Ha a kijelölésben nincs ilyen — mert
csak már elnevezett képeket jelöltél ki, vagy nem jelöltél ki semmit —, a
gombok a szokott módon az **összes** javaslatra hatnak, és a felirat is
visszaáll.

Más emberek javaslatai akkor sem kerülnek bele, ha ugyanazon a kijelölt
képen vannak: a művelet csak annak a személynek a javaslataira hat, akinek
az albumát épp nyitva tartod. Ha egy képen több arc is ezt a nevet
javasolja, a kijelölése mindegyikre szól.

### Arcra közelítve vagy a teljes képpel

A fejléc **jobb felső sarkában** két kis gomb áll egymás mellett. Ezek
döntik el, mit mutat a rács csempéje:

- **Megjelenítés az arcra közelítve** — a csempéken csak maga az arc
  látszik, kivágva és felnagyítva;
- **Megjelenítés a teljes képre távolítva** — a szokásos bélyegkép, az
  egész felvétel. Ez az alapállás.

Ez **nézet-beállítás**, nem az albumé: amit itt választasz, a következő
személy albumára is érvényes marad, amíg vissza nem váltod.

Kis arcnál a program az **eredeti fájlból** olvassa ki a kivágást, hogy
a csempe ne legyen elmosódott. Videón és nyers (RAW) fájlon marad a
szokásos bélyegkép.

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

A személy albumának fejlécében két filmgomb áll (súgójuk: **Mozgófilm
létrehozása arcokból**). Megnyomásukra a **Filmkészítő** nyílik meg
([Mozgófilm](mozgofilm.md)), és az **összes nem üres személyalbum** képeit
kapja — nem csak a nyitott albumét —, a személyalbumok sorrendjében. A
film alapmérete itt 1024 × 768; ezt a program nem jegyzi meg a következő
filmre.

Az **Áthelyezés új személyhez…** paranccsal egy rosszul besorolt arcot új
névhez rendelhetsz, a **Hozzáadás az Emberek albumhoz** almenüből pedig egy
már meglévő személyhez teheted át — az almenü a többi személyt sorolja fel.
Az **Eltávolítás az Emberek albumból** (Ctrl+Delete) kiveszi onnan.

> A helyi menü **Beállítás az Emberek album indexképeként** tétele **még
> nem működik** — az emberalbumok saját borítóképét ma nem lehet
> megválasztani.

## Film a kijelölt arcokból

A **Létrehozás ▸ Mozgófilm ▸ A kijelölésben lévő arcokból…** a kijelölt
képekkel nyitja meg a [Filmkészítőt](mozgofilm.md), 1024 × 768-as
alapmérettel. A parancs csak kijelölt képnél él. A filmbe ma a képek
egészben kerülnek, nem az arcra vágva.

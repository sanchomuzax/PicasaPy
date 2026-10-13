# Importálás

## Importálás forrásból

Ez a fő út: kártyáról, fényképezőgépről vagy bármilyen mappából
behozhatod a képeket.

Indítás: az eszköztár **Importálás** gombja, vagy **Fájl ▸ Importálás
forrása…** (Ctrl+M).

A párbeszéd felül a **Forrást** kéri (a legutóbbi forrásokat is
felkínálja), alatta megjelenik, mit talált: hány kép és videó van benne.

A **Tallózás…** gomb egy kis menüt nyit:

- **Mappa…** — egy egész mappát választasz forrásnak;
- **Fájlok…** — egy mappán belül egyes fájlokat jelölsz ki (a
  **Fájlok/mappa importálása** ablakban több fájl is kijelölhető). A
  választó szűrője **Kép- és filmfájlok**, **Képfájlok** vagy **Minden
  fájl** lehet. Ilyenkor a forrás mezőjében az első fájl neve áll, mellette
  zárójelben, hány további fájlt választottál. A kijelölésből csak a
  létező kép- és filmfájlok kerülnek az importálandók közé, a **Fájltípusok**
  beállításnak megfelelően.

Ha memóriakártya vagy USB-meghajtó van a géphez csatlakoztatva, a
forrás mellett egy **Cserélhető meghajtók** lista is megjelenik (Windowson
és Linuxon). A tételei „Cserélhető meghajtó (*név*)" alakúak; egyet
kiválasztva az lesz a forrás, és a program rögtön átnézi. Ha nincs ilyen
meghajtó, a lista nem látszik.

### Mit hozzon be

- Az indexképekre kattintva egyenként dönthetsz: **Bevonás** vagy
  **Kizárás**. Az **Összes bevonása** és **Összes kizárása** gomb mindet
  átállítja.
- A **Duplikátumok kizárása** azokat hagyja ki, amik már benne vannak a
  könyvtáradban.
- **Fájltípusok** — képfájlok, filmek, kép- és filmfájlok, vagy minden
  fájl.

### Hova kerüljön

A **Cél** mappát a **Tallózás…** gombbal választod, vagy a korábbi
célmappák közül. Az ablak mindig az **alapértelmezett célmappával**
nyílik. Ez alapból a **Képek** mappád; átállítani az **Eszközök ▸
Beállítások… ▸ Általános** fülön lehet, az **Importált képek mentési
helye:** sor **Tallózás…** gombjával
(lásd [Beállítások](beallitasok.md)). Alatta három lehetőség közül
választasz, hogy a
képek **milyen nevű almappába** kerüljenek:

- **Mappa nevének megadása** — te írod be, az alatta lévő mezőbe;
- **Készítés dátuma (ÉÉÉÉ. HH. NN.)** — minden felvételi nap külön
  mappába kerül;
- **… (ma)** — a mai dátum nevű mappába. A felirat elején mindig a mai
  nap áll, abban az alakban, ahogy a mappa létrejön (például
  `2026-01-31 (ma)`).

Az első lehetőségnél a mappa nevét meg kell adni, mielőtt az importálás
elindulhat. Amíg a mező üres, az importálás nem indul el, és az ablak ezt
írja: „A folytatáshoz írjon be egy új mappanevet, vagy válasszon egy
létező mappát". A név **egyetlen mappanév** lehet: a célmappán kívülre
mutató név (például `../valami`), a teljes útvonal és a mappanévben
tiltott karakterek nem fogadhatók el — ilyenkor sem indul az importálás.

### Másolás után

A **Másolás után** beállítás dönti el, mi történjen a forrással:

- **Kártya érintetlenül hagyása** (alapértelmezés),
- **Csak a másolt fényképek törlése**,
- **Minden törlése a kártyáról**.

A két törlő választásra a program rákérdez, és a válasz **nem vonható
vissza** — ami a kártyáról lemegy, az nem kerül a Lomtárba.

A **Minden törlése a kártyáról** esetén a kérdés tételesen felsorolja,
mibe mész bele:

- hány fájlt töröl az importálás után;
- hány fájl **nem** kerül be, mert már megvan a könyvtáradban;
- hány fájlt **nem ismer fel** a program — ezek is törlődnek. Ide
  tartoznak a fényképezőgép kísérőfájljai és a kártyán lévő egyéb
  fájlok, tehát nem csak képekről van szó.

Ha a forrást még nem pásztázta végig a program, a darabszámot nem
találgatja: ezt írja ki, hogy „ismeretlen számú fájlt fog törölni".
Ilyenkor érdemes megvárni a pásztázás végét, mielőtt igent mondasz.

### Az importálás közben

Haladásjelző sáv mutatja, hol tart (`hány / hányból`), és a sebességet is
kiírja. A végén összesít: hány kép jött be, és hány nem sikerült.

## Webkamerás felvétel

Az eszköztár bal oldalán, a nézetváltó gombok mellett egy kis **◉** gomb
áll (súgója: **Webkamerás felvétel megnyitása**). Megnyomására
a **Rögzítés** ablak nyílik, amiben a számítógéped kamerájáról
készíthetsz állóképet vagy videót:

- a kamera élő képe az ablak közepén látszik; amíg a kamerához nem
  tud csatlakozni, a **Csatlakozás a kamerához**, ha nincs kamera, a
  **Nem érhető el** felirat áll ott;
- **Pillanatkép** — állóképet ment a kamera képéből;
- **Felvétel** — elindítja a videofelvételt, a gomb ekkor
  **Leállítás** feliratú. Felvétel közben a **Szünet** és a
  **Folytatás** gomb szünetelteti, illetve folytatja;
- **Beállítások** — a **Fényképezőgép** és a **Hang** forrásának
  választása, és a **Méret** (320 × 240, 640 × 480, 800 × 600 vagy
  1280 × 720). Az **Alkalmaz** elfogadja, a **Mégse** elveti;
  a választás megmarad. A felső sor **Fényképezőgép** gombja a
  Beállításokból visszavisz az élő képhez;
- a már felvett klipek között a **‹** és **›** gombbal lépkedhetsz,
  a ▶ lejátssza őket;
- **Kész** — bezárja az ablakot (folyó felvételt előbb leállít).

A pillanatképek és a klipek a **Képek/Picasa/Rögzített videoklipek**
mappába kerülnek. Ha nem sikerül előkészíteni a mappát, vagy a rögzítés
hibára fut, az ablak megmondja.

## Fájl vagy mappa felvétele

- **Fájl ▸ Fájl felvétele a Picasába…** (Ctrl+O) — egy vagy több
  konkrét fájl hozzáadása.
- **Fájl ▸ Mappa hozzáadása a Picasához…** — megnyitja a
  [Mappakezelőt](mappakezelo.md), ahol felveheted a figyelt mappák közé.

## Húzd-és-ejtsd

Képeket vagy mappákat közvetlenül az ablakra is húzhatsz. A program
átveszi őket, és jelzi a haladást.

## Átvétel a Picasából

Ha ezen a gépen már volt Picasa, a PicasaPy megtalálja, és felajánlja a
figyelt mappái átvételét — így nem kell mindent újra beállítanod.

A párbeszéd az **Átvétel** gombbal veszi át a listát, a **Most nem**
gombbal kihagyod. Ha a felismerés nem talál semmit, vagy a mappák máshol
vannak (például egy hálózati megosztáson), a **Kézi tallózás…** gombbal
mutathatod meg őket.

Ez a párbeszéd az első indításkor magától megjelenik, később pedig a
Mappakezelőből bármikor újranyitható.

## A régi Picasa adatainak átvétele

Ha ezen a gépen korábban Picasát használtál, a benne megadott **nevek**,
**kulcsszavak** és **helyek** átvehetők a képek mellé.

Indítás: **Eszközök ▸ Import a Picasából…**

Az ablak az **Import a Picasából** címet viseli. Az **Importálás** gomb
indítja az átvételt; amíg fut, az ablak ezt írja: „Nevek, kulcsszavak és
helyek átvétele a Picasából…". A végén megmondja,
mit végzett — például „12 mappa frissült: 342 kulcsszó, 219 hely, 87
név." —, és azt is, hány fotóhoz nem nyúlt hozzá, mert azoknál **már
volt adat**.

Két fontos tulajdonsága van:

- **Meglévő adatot soha nem ír felül.** Ahol a kép mellett már van
  kulcsszó, hely vagy arc, azt érintetlenül hagyja.
- **Bármikor megismételhető** — a kimaradt mappákkal folytatja.

Ha a régi Picasában **jelszót** állítottál be a rejtett mappákra, az
átvétel ezt a jelszót is hozza — de csak akkor, ha a PicasaPy-ban még nem
adtál meg saját jelszót. A sajátodat nem írja felül. A jelszóról
[A könyvtár](konyvtar.md) fejezet „A rejtett mappák jelszava” része szól.

Ha a program nem talál régi Picasa-adatot a gépen, ezt írja ki: „Nem
találtunk Picasa-adatokat ezen a gépen."

### Kézzel megadott Picasa-adatmappa

Alapból a program maga keresi meg a gépen a régi Picasa adatait — ehhez
hagyd üresen a **Picasa2-adatmappa** mezőt. Ha az adatok máshol vannak
(például egy régi gépről átmásolt `Picasa2` mappában, vagy Linuxon egy
windowsos lemezen), a mezőbe írd be, vagy a **Tallózás…** gombbal
válaszd ki a mappát.

Ilyenkor a program azt is tudni akarja, hol vannak most a képek, mert a
régi Picasa windowsos útvonalakat tárolt. Ezt a **meghajtó-leképezés**
két mezőjében adod meg:

- **Windows-útvonal előtagja** — ahogy a régi Picasa ismerte a képek
  helyét, például `C:/Pictures`;
- **A megfelelő helyi mappa** — ahol ugyanezek a képek most vannak,
  például `/home/felhasználó/Képek`.

Kézi adatmappánál **mindkét mezőt** ki kell tölteni; ha valamelyik üres,
az ablak szól: „Adja meg a meghajtó-leképezés mindkét útvonalát."

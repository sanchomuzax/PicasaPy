# Gyakori kérdések és hibaüzenetek

## Általános kérdések

### Átírja a PicasaPy a képeimet?

Nem. A szerkesztéseket a képek melletti `.picasa.ini` fájlba menti, és
minden megjelenítésnél újraszámolja őket. A képfájlba csak akkor ír, ha
te magad kéred a **Fájl ▸ Mentés** paranccsal (és akkor is készít előbb
biztonsági másolatot).

Egy kivétel van: a **képfeliratot** a JPEG-fájl IPTC-mezőjébe is beírja,
hogy más programok is lássák.

### Használhatom a régi Picasát is ugyanazokon a képeken?

Igen. Mindkét program ugyanazt a `.picasa.ini` fájlt olvassa és írja, és
a PicasaPy változatlanul visszaírja azt is, amit ő maga nem ért. Nem
javasolt viszont **egyszerre**, ugyanabban a percben mindkettőben
szerkeszteni ugyanazt a mappát.

### Miért szürke a menü fele?

Mert a menük az eredeti Picasa teljes szerkezetét mutatják, de a
funkciók egy része még nem készült el. A teljes lista:
[Ami még nem érhető el](features/meg-nem-erheto-el.md).

### Hol vannak a képeim, ha törlöm az adatbázist?

A helyükön. Az adatbázis csak gyorsítás — minden fontos adat a képek
mellett van. Töröld nyugodtan, és indítsd újra a programot; újra átnézi
a figyelt mappákat.

### Hogyan váltok magyarról angolra?

**Eszközök ▸ Nyelv ▸ Angol**, vagy a **Beállítások ▸ Általános** fülön a
**Nyelv** választóval. Azonnal hat.

## Hibaüzenetek

### „Ez a mappa jelenleg nem elérhető…"

Egy külső lemez vagy hálózati megosztás nincs csatlakoztatva. A képek
listája és a bélyegképek megmaradnak, de a fájlokat most nem lehet
megnyitni vagy szerkeszteni. Csatlakoztasd a lemezt, és minden működik
tovább — nem kell újra beolvasni semmit.

### „%1 kép nem található, ezért nem jelenik meg."

A fájlokat egy másik programmal elmozdították, átnevezték vagy törölték.
Ha csak átköltöztek, vedd fel az új helyüket a
[Mappakezelőben](features/mappakezelo.md), és a program megtalálja őket.

### „Egy vagy több képet nem lehetett elforgatni a fájltípus miatt."

Videót nem lehet forgatni, és néhány képformátumnál sem működik a
nem-destruktív forgatás.

### „Ez a videó nem játszható le."

Vagy hiányzik a Qt Multimedia modul, vagy a videó formátumát nem ismeri
a rendszer. Linuxon telepítsd a `qml6-module-qtmultimedia` és a
`python3-pyside6.qtmultimedia` csomagot (és a `libpulse0`-t a hanghoz).

### „A térkép-komponens (QtLocation) nem érhető el."

A térkép megjelenítéséhez való Qt-modul hiányzik a rendszeredről. A
geocímkék ettől még olvashatók és törölhetők, csak a térkép nem látszik.

### „Ezeken a képeken olyan szerkesztés van, amit a PicasaPy még nem tud megjeleníteni"

Egy régebbi Picasa-változat effektjét találta meg a `.picasa.ini`-ben. A
program megőrzi, de kirajzolni nem tudja. **Ha mentesz, ez a beállítás
véglegesen elvész** — érdemes ilyenkor inkább nem menteni, hanem
meghagyni a képet szerkesztetlenül. Lásd
[Régi effektek](features/effektek.md).

### „Fájlformázási hiba miatt a fájl nem menthető."

A kép formátumát a program nem tudja kiírni. Próbáld a **Fájl ▸ Mentés
másként…** paranccsal, JPEG vagy WebP formátumban.

### „A fájl mentése nem lehetséges. Már van ilyen nevű fájl."

A választott néven már létezik fájl. Adj másik nevet.

### „A képet nem lehet kicserélni. Próbálja újra másik fájlnévvel."

A cél fájl épp foglalt, vagy nincs rá írási jogod.

### Mentés közben lemezhiba

Ha a lemez megtelt vagy csak olvasható, a program megnevezi az érintett
fájlt. Szabadíts fel helyet, vagy ellenőrizd a mappa jogosultságait.

### „Nincs nyomtatható kép." / „Ezeket a képeket nem lehetett kinyomtatni"

Az elsőnél nincs kijelölve semmi. A másodiknál a felsorolt fájlok nem
olvashatók — nézd meg, léteznek-e még.

### „Előbb jelölj ki képeket a könyvtárban, vagy tedd őket a képtálcára."

Kollázs vagy film készítéséhez legalább egy kép kell.

### „A kollázs nem készült el." / „A mozgófilm nem készült el."

A leggyakoribb ok, hogy a célmappába nincs írási jogod, vagy időközben
eltűntek a felhasznált fájlok. Válassz másik célt, és próbáld újra.

### „Nincsenek exportálható geocímkézett képek"

A kijelölésben egyetlen képnek sincs helye. A földgömb-szűrővel
megnézheted, van-e egyáltalán ilyen képed.

### „Az automatika nem talált vörös szemet."

A program nem talált vörös szemet a képen. Jelöld ki kézzel: húzz keretet
a szem köré a Vörösszem panelben.

### „A keresés nem sikerült" / „A csoportosítás nem sikerült" (arcok)

Az arcfelismerés modellje hiányzik vagy sérült. Nyisd meg újra az
**Eszközök ▸ Arcok keresése…** párbeszédet, és töltsd le a modellt a
**Modell letöltése** gombbal.

### „Nincs elérhető EXIF-adat."

A képfájl nem tartalmaz fényképezőgép-adatokat. Ez nem hiba — sok
szerkesztett vagy letöltött képnél előfordul.

## Ha valami mégis elromlik

A **Súgó ▸ Teljesítmény-monitor** panelen a **Diagnosztika mentése…**
gombbal fájlba mentheted, mi történik a programban. Lassú indulásnál
kapcsold be a **Súgó ▸ Tesztüzem (a következő indulást naplózza)**
pontot, indítsd újra a programot, majd a **Napló elküldése…** paranccsal
add tovább a naplót.

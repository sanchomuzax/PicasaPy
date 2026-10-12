# ADR-016: Az album képsorrendje a kép saját szakaszába kerül (`albumorder=`)

Dátum: 2026-10-12 · Státusz: ELFOGADVA · jegy: #4599 · előzmény: #4884, ADR-014

## A helyzet

A #4599 az album „Sort Album By” almenüjét kéri. A #4884 kutatása
(`docs/specs/album-sorrend.md`) kimérte, mit csinál az eredeti:

- a mappa és az album képsorrendje **tárolt lista**, nem számolt rendezés;
- a lista a központi keresőindex szótárában él (`db3\wordhash.dat`, a
  `]album:<token>` szó rekordindex-listája), **nem** a `.picasa.ini`-ben —
  ini-kulcs a sorrendhez nincs;
- a „Sort Album By” **egyszeri átrendezés**: a listát egyszer rendezi, és
  utána a rendezett lista kézi sorrendként él tovább; rendezési mód nem
  tárolódik.

A PicasaPy-ban ma albumonkénti sorrend **nincs**: az album képei a
`index/albums.py` lekérdezésében mappa-útvonal, majd fájlnév szerint állnak
(`ORDER BY f.path, p.name`). A mappa kézi sorrendjét az ADR-014 óta a
képszakaszok `priority=` kulcsa hordozza (`ini/priority.py`).

Az ADR-014 premisszája — „az eredeti a kézi sorrendet az `albums_0.db`-ben
tartja” — **megdőlt** (#4591: a fájl tartalma borító-raszter; #4884: a
sorrend a `wordhash.dat`-ban van). Az ini-ben tartás mint SAJÁT döntés
ettől még áll, és ez az ADR az albumra ugyanezt az utat választja.

## A kötöttségek

1. **A `.picasa.ini` az igazságforrás**, az SQLite index csak gyorsítótár —
   a sorrend tehát nem élhet csak az indexben.
2. **A `.picasa.ini`-t csak az `ini/` API írja** (sáv-invariáns).
3. **A központi Picasa-adatbázist nem írjuk** (`db3`, köztük a
   `wordhash.dat`): bináris, központi, és a felhasználó futó Picasája is
   használja — az ADR-014 1. érve itt változatlanul áll.
4. **Az album több mappára is szórhat.** A tagság a képszakasz `albums=`
   CSV-kulcsa; az album definíciója (`[.album:<token>]`) minden olyan mappa
   ini-jében megismétlődik, ahol tagja van.
5. **Az eredeti Picasa ugyanazt a fájlt írja**, és nem ismeri a kulcsunkat.

## A lehetőségek

### A) Képenkénti kulcs a kép saját szakaszában — `albumorder=<token>:<hely>,…`

Minden kép a saját szakaszában, az `albums=` mellett, tagságonként egy
helyet hordoz. Az album sorrendje a tagjai helyének rendezése.

| szempont | értékelés |
|---|---|
| több mappára szóró album | **természetes**: minden kép a saját mappája ini-jében tartja a helyét; a helyek egyetlen közös számtérben vannak, tehát a mappák képei tetszőlegesen összefésülhetők |
| átnevezés | a `fileops/rename.py` a szakaszt `with_renamed_section`-nel nevezi át — a kulcs vele megy, **nincs teendő** |
| áthelyezés másik mappába | a `fileops/move.py` a TELJES szakaszt viszi, az ismeretlen sorokkal együtt — a kulcs vele megy, és ez itt **helyes** is (az album sorrendje mappától független) |
| másolás | a `fileops/copy.py` a szakaszt másolja: a példány ugyanazt a helyet kapja, az egyenlőséget az útvonal dönti el — elfogadható |
| egy kézi húzás költsége | felezőpontos beszúrással **egy kulcs, egy ini-írás** (az ADR-014 mintája) |
| az egyszeri átrendezés költsége | minden tag újraszámozva ⇒ annyi ini-írás, ahány mappában van tag |
| Picasa-kockázat | egy ismeretlen kulcs a képszakaszban — **ugyanaz a kockázati osztály, amit a `priority=` az ADR-014 óta hordoz**, újat nem nyit |

### B) Az album-szakaszban egy sorrend-lista — `[.album:<token>]` `order=…`

| szempont | értékelés |
|---|---|
| több mappára szóró album | **rossz**: a szakasz mappánként megismétlődik. Vagy minden példány a teljes listát hordozza (más mappák fájljait relatív útvonallal) és a példányok szétcsúszhatnak, vagy mindegyik csak a saját mappájáét — akkor viszont a mappák közti összefésülés nem írható le |
| átnevezés, áthelyezés | egy fájlművelet **más mappák ini-jét** is írná (a lista minden példányát) — a mai, mappánként szerializált írási modellben ez több fájlra szóló, nem atomi írás |
| értékkódolás | fájlnév-lista egy sorban: vessző, pontosvessző, ékezet mind escape-et kér |
| Picasa-kockázat | **nagyobb, mint A-nál**: az album-szakaszt az eredeti a saját album-adatbázisából (`albumdata`) állítja elő; nincs bizonyíték arra, hogy egy általa nem ismert kulcsot ott megtartana, és egy hosszú lista elvesztése az egész album sorrendjét viszi |

### C) Külön mellékfájl (pl. mappánként egy rejtett JSON)

| szempont | értékelés |
|---|---|
| Picasa-kockázat | **nulla** — az eredeti nem olvassa és nem írja |
| igazságforrás | **megsérti** az alapelvet: a mappa adata két fájlba szakad, és kell egy második író az `ini/`-n kívül |
| több mappára szóró album | ugyanaz a dilemma, mint B-nél (mappánkénti vagy központi fájl) |
| átnevezés, áthelyezés | minden fájlművelet a mellékfájlt is kell, hogy kövesse; ha a **Picasa** nevez át vagy helyez át, a mellékfájl biztosan elavul (A-nál ez csak akkor történik meg, ha a Picasa eldobja az ismeretlen kulcsot) |
| központi változat | a mappával nem utazik — az ADR-014 3. érvével ellentétes |

### D) Az SQLite index — kizárva (1. kötöttség)

## A döntés

**Az A) lehetőség.** Az album sorrendje a tag képek saját szakaszába kerül,
egyetlen `albumorder=` kulcsba, tagságonként egy `<token>:<hely>` párral.

### Miért

1. **A több mappára szóró album csak így írható le tisztán.** A sorrend a
   tagság mellett ül, ugyanabban a szakaszban, mint az `albums=`; az album
   minden tagja a saját helyét hordozza, egy közös számtérben.
2. **A fájlműveletek ingyen viszik.** Az átnevezés és az áthelyezés ma is a
   teljes szakaszt mozgatja (`fileops/rename.py`, `fileops/move.py`), tehát
   a kulcsot is — nincs új, más mappára átnyúló írás.
3. **Nem nyit új kockázati osztályt.** Ismeretlen kulcs a képszakaszban már
   van (`priority=`, ADR-014); ha az eredeti ezt bántaná, a mappa kézi
   sorrendje ma is ugyanígy érintett. A B) nagyobb, a C) más (és az
   alapelvet sértő) kockázatot hozna.
4. **Az igazságforrás és az egyetlen író megmarad**: a kulcsot az `ini/`
   csomag írja, az index csak gyorsítótárazza.

### Miért NEM a `priority=` újrahasznosítása

A mappa és az album sorrendje az eredetiben is **két független lista** (a
mappa és az album külön szó a keresőindexben). Egy kép, amely egy mappában
és két albumban szerepel, három különböző helyen állhat. A `priority=`
marad a mappáé, az `albumorder=` albumonként külön helyet ad.

## A kulcs formátuma

| | |
|---|---|
| kulcs | `albumorder` a **kép** szakaszában |
| érték | vesszővel elválasztott `<token>:<hely>` párok, pl. `albumorder=604c294a68b0de9cc9222c4714f289d5:3.0,65d12673f3b51e3f65d12673f3b51e3f:0.5` |
| token | az album 32 hexa karakteres tokenje, ugyanaz, mint az `albums=`-ben |
| hely | tizedes szám, **pont** tizedesjellel, mindig tizedes alakban (`3.0`, nem `3`) — ugyanaz a szabály, mint a `priority=`-nél (`tizedesjel.md`) |
| érvényes pár | csak az, amelynek tokenje a kép `albums=` kulcsában is szerepel — **a tagságot az `albums=` adja**, az `albumorder=` csak sorrend |
| elárvult pár (token nincs az `albums=`-ben) | olvasáskor figyelmen kívül marad; ha a kép kulcsát egyébként is írjuk, kikerül. Pusztán takarításért nem írunk |
| romlott pár | olvasáskor kimarad (a kép „nincs kézi helyen”); nem dob kivételt |
| hiányzó hely | „nincs kézi hely”: a kép az album **végére** kerül, a mai rend szerint (mappa útvonala, fájlnév) |
| egyenlő hely | mappa útvonala, majd fájlnév dönt — a sorrend determinisztikus |
| üres lista | a kulcs **törlődik** (üres kulcsot a Picasa sem hagy maga után) |

⇒ Egy album, amelynek egyetlen tagja sem hordoz helyet, **pontosan úgy áll,
mint ma** — a bevezetés nem változtat meg egyetlen meglévő albumot sem.

## A műveletek

| művelet | mit ír |
|---|---|
| „Sort Album By” ▸ Név / Dátum / Méret (Shifttel csökkenő), ▸ Fordított | az album **minden** tagja új helyet kap (`1.0 … n`), mappánként egy `update_document`. A mód nem tárolódik — csak a helyek (ahogy az eredetiben a lista) |
| kézi húzás az albumban (külön jegy) | a két szomszéd felezőpontja, **egy** kép, **egy** ini |
| kép kivétele az albumból | az `albums=` tokenjével együtt az `albumorder=` párja is kikerül, ugyanabban az írásban |
| album törlése | a `without_album_everywhere` a párokat is törli |
| kép felvétele az albumba | ha az albumnak már van kézi sorrendje, a kép a legnagyobb hely + 1-et kapja **ugyanabban** az írásban, amely az `albums=`-t bővíti (így a hozzáadás sorrendjében kerül a végére, mint az eredetiben); ha nincs, nem ír helyet |

⚠️ **Több mappára szóró album egyszeri átrendezése nem atomi**: mappánként
külön ini-írás történik. Részleges bukásnál a hiba hangos (melyik mappa
maradt ki), a sorrend determinisztikus marad (a ki nem írt tagok a régi
helyükkel), és a művelet megismételhető. Több fájlra szóló tranzakciót nem
vezetünk be.

## Az index

A hely az indexben **gyorsítótár**: a szinkron a kulcsból tölti, és az
`album_photos` lekérdezés ezzel rendez (hely szerint, a hely nélküliek a
végén, utána útvonal, fájlnév). Ez SQLite-séma-változás (keresztmetsző
szerződés, `index/`), tehát a #4599 megvalósítása nem párhuzamosítható
szabadon más, az indexsémát érintő jeggyel.

## ⚠️ Ez SZÁNDÉKOS ELTÉRÉS a tárolás helyében

A *funkció* (az album tárolt, átrendezhető sorrendje) az eredetiben is
megvan, és a menü tételei is az eredetiéi — ezért a menütételek **nem**
kapnak kék „saját funkció” jelölést. A *tárolás* viszont saját: a kulcsot a
kódban a `vedett-sajat-funkciok.md` szerinti saját-funkció jelölővel kell kimondani, és fel kell venni a
`vedett-sajat-funkciok.md` jegyzékébe.

## ⛔ Amit ez az ADR NEM állít — nyitott kérdések

Egyik alábbi pont sincs élőben mérve. A döntés úgy készült, hogy a
kedvezőtlen válasz se okozzon adatvesztést a Picasa adataiban.

| kérdés | mit tudunk | ha kedvezőtlen |
|---|---|---|
| **NY1** — megőrzi-e az eredeti a képszakasz általa nem ismert kulcsát, amikor ugyanabba a szakaszba ír (pl. csillagot tesz a képre) | **nincs mérve** (ugyanez az ADR-014 nyitott kérdése). Kódszintű utalás: a mappadátum írása kulcsonként egy beállítón megy (`0x0045c0a0`, `picasa-ini-format.md`, „A KÖZÖS beállító”), ami inkább helyben szerkesztésre vall, mint a szakasz újragenerálására — ez nem bizonyíték | az adott mappa tagjainak helye elvész, a képek az album végére esnek, a mai rend szerint. A Picasa saját adata nem sérül; a felhasználó egy újabb rendezéssel visszaállíthatja |
| **NY2** — elviseli-e az eredeti az ismeretlen kulcsot mellékhatás nélkül (nem dobja-e el miatta a szakasz többi kulcsát) | **nincs mérve.** Kódszintű utalás: az ini-értelmező kulcsnév-összevetéssel dolgozik (`0x008fb120`, ADR-014), az illesztetlen név nem talál ágat. A kockázat a `priority=` óta ugyanígy fennáll | ez volna a valódi kár (csillag, szerkesztés elvesztése). Ekkor a `priority=` és az `albumorder=` **együtt** költözik mappánkénti mellékfájlba (C), és ez az ADR felülírandó |
| **NY3** — mit kezd az eredeti egy általunk átrendezett albummal | semmit: az eredeti a saját `wordhash.dat`-listáját mutatja, a kulcsunkat nem olvassa | a két program ugyanazt az albumot **eltérő sorrendben** mutathatja. Ez a tárolás helyéből adódó, vállalt eltérés |

**A következő lépés az NY1–NY2 eldöntésére** (a hívó dönt az indításáról,
ebben a körben NEM indult): Colab-végrehajtós mérés egy tesztmappán, amelynek
ini-jében egy kép szakasza `priority=` és `albumorder=` sort is hordoz; a
Picasa a kép egy ismert kulcsát (csillag) és egy másik képét módosítja, majd
rendesen kilép; a kimenet a mappa `.picasa.ini`-je. Elfogadás: a két sor a
helyén van, és a szakasz többi kulcsa is. Ha a végrehajtó a mappa ini-jét ma
nem adja vissza kimenetként, ahhoz új kimenet-típus kell.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** nincs megvalósítva
- **Őrzi:** nincs őr

# ADR-005: A „figyelt mappa eltávolítása" megerősítő ablak — tudatos eltérés

**Állapot:** eldöntve · **Dátum:** 2026-08-21 · **Döntő:** a kutatói kör,
a projekt „ne kérdezz egyszerű dolgoknál" elve alapján · jegy: #543
(lezárva, téves premisszán), #1161 (a Mappakezelő teljes feltárása)

## A helyzet

A `#543` jegy három „hiányzó figyelmeztetést" sorolt fel az eredeti
Picasa Mappakezelőjéből, köztük az `IDS_HOTFOLDER_CONFIRM`-ot: „Ha egy
figyelt mappát eltávolít, a lemezen oda mentett új fájlokat a Picasa nem
veszi fel automatikusan. Biztosan ezt szeretné?" Ez alapján a
`FolderManagerDialog.qml` megkapta a `removeWatchedConfirm` megerősítő
ablakot.

**2026-08-21-én, az `#1161` átvilágítás M3 lépésében kiderült: ez a
szöveg a Picasa 3.9.141.259-ben SOHA nem jelenik meg.** A Win32
string-betöltő burkoló mind a 84 hívóját (150 hívás) végigmérve 95
ténylegesen betöltött azonosító van — a `86` (`IDS_HOTFOLDER_CONFIRM`),
a `87` (`_TITLE`) és a `100` (`IDS_SETTING_UP_WATCHED`) egyike sem
köztük. A `stringres`-úton sincs rájuk hivatkozás. Részletek:
`docs/specs/picasa-mappakezelo.md` 6.3.

Vagyis a `#543` alapja téves volt, de mire ez kiderült, a jegy már
**lezárt** állapotban volt, és a nálunk megépült viselkedés — a
megerősítő ablak — a helyén maradt.

## A döntés

**A megerősítő ablak MARAD.** Ez tudatosan **több**, mint amit az
eredeti Picasa csinál — nem paritási hiba, nem kell „visszavágni" rá.

**Indoklás:**

- A mappa-eltávolítás nem törli a képeket, de leállítja a figyelést —
  ez visszafordítható, de könnyen véletlen kattintással előidézhető
  művelet, ahol egy megerősítő kérdés valós, alacsony költségű
  védelmet ad.
- A szöveg és a hozzá tartozó fordítás már készen áll (a magyar
  fordítói táblában is szerepel), a kód is megépült — az eltávolítása
  tiszta veszteség lenne funkcióban, nulla nyereségért.
- Ez **nem látvány-** vagy **elrendezés-kérdés** (ahol a projekt
  szabálya szerint kötelező az eredeti pontos követése), hanem egy
  **biztonsági többletlépés** — ugyanabba a kategóriába esik, mint az
  `ADR-003` „Régi effektek" füle: tudatos, dokumentált eltérés.

## Amit ez kizár

Egy jövőbeli kör **ne vegye ki** a `removeWatchedConfirm`-ot „paritás"
címén, és **ne is nyisson rá új jegyet paritás-hiányként** — ez a
viselkedés szándékos.

## Kapcsolódó

- `docs/specs/picasa-mappakezelo.md` 6.3. szakasza — a bizonyíték, hogy
  a szöveg halott az eredetiben.
- `#543` — a jegy, ami alapján a funkció megépült; lezárva, a záró
  komment ezt az ADR-t linkeli.
- `#1161` — a Mappakezelő teljes feltárása, ahol a HELYESBÍTÉS
  megtörtént.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/app/qml/PicasaPy/FolderManagerDialog.qml`
  (a `removeWatchedConfirm` ablak — a döntés TELJES egészében itt él)
- **Őrzi:** `tests/app/test_qml_folder_manager.py`

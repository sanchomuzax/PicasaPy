# ADR-009: A kép fájlideje BEFAGY az első beolvasáskor — a rendezés azt használja

Dátum: 2026-09-06 · Státusz: ELFOGADVA · jegy: #2486 (a #2304 maradéka)

## A helyzet

A rács dátum-rendezésének kulcsa (`app/photo_sort.photo_date`) az EXIF
felvételi idő; ennek hiányában a **fájl ideje**. Eddig ez az **élő**
`mtime` volt, minden beolvasáskor újra kiolvasva. Ettől a sorrend nem a
képekről szólt, hanem arról, mikor nyúlt hozzájuk bárki utoljára.

Két mérés mutatja, hogy ez nem elméleti:

1. **#2304 (2026-09-05, a tulajdonos `AI` mappája).** A mai `photo_sort`
   az első 18 elemet sorrendhelyesen adja (18/18 egyezés a Picasa
   képernyőmentésével), a szétválás oka, hogy **19 fájlnak átíródott az
   `mtime`-ja** — mind ugyanarra az időpontra (`2026-07-19 20:05:39`).
   Pontosan az a halmaz, amit a Picasa 2023 novemberébe fésül. Ugyanez
   magyarázza az állapotsor dátumtartományának végét is (Picasa:
   2025-05-21, nálunk 2026-08-22).
2. **#2491 / ADR-006 (2026-09-06).** A képfájl `mtime`-jának megérintése
   megint **alapértelmezés**: a `.picasa.ini` írása után a
   `ini/photo_touch.py` átírja a változott fotók idejét, mert enélkül a
   párhuzamosan futó, eredeti Picasa nem frissíti a képet. Vagyis a
   jelenség **nem külső baleset**: EXIF nélküli képnél minden saját
   szerkesztésünk elmozdítja a képet a saját rácsunkban.

## Amit az eredeti csinál — mérve, nem feltételezve

A Picasa a képhez tartozó dátumot a **katalógusába fagyasztja** a
beolvasáskor, és a pásztázó soha nem frissíti. Forrás:
`docs/specs/pmp-database.md`

- **10.1** — kimerítő negatív: a pásztázó a `thumbindex`-rekord négy
  mezője közül az 1. FILETIME-ot nem írja;
- **10.3** — az 1. mező beállítójának (`0x004eeb10`) a TELJES binárisban
  **egyetlen** hívója van (`0x00427898`, a képbeolvasóban), és a
  metaadat-dátumot (`0x37` = EXIF `0x9003` DateTimeOriginal) írja be;
- **10.4** — mérés 140 758 rekordon: az 1. mező a felvételi idő
  (91,8 % percen belül), a 2. a fájl `mtime`-ja; és **metaadat-dátum
  hiányában a kettő egybeesik** (PNG-ken 32/33), azaz az 1. mező ilyenkor
  a **beolvasáskori** fájlidő.

⚠️ **Ami a mérésből NEM következik.** A 10.4 fallback-lelete `n = 33`
mintán áll, ezért a spec is **„erős"**, nem „megerősített" fokot ad neki.
A brief felvetette kérdés — *„a `creation` a fájl LÉTREHOZÁSI vagy
MÓDOSÍTÁSI idejéből jön?"* — viszont **el van döntve, és a válasz: egyik
sem.** A 10.3 lánca szerint az 1. mező a kép metaadat-dátuma; ha az
hiányzik, a 2. mezővel marad egyenlő, a 2. mező pedig a 10.2 szerint
bizonyítottan a **módosítási** idő (a Picasa saját CSV-fejlécének „Access
Time" neve téves). Tehát a **módosítási** időt fagyasztjuk, és ez nem
találgatás.

## A döntés

**Igen: a `photos` tábla eltárolja az első látáskori fájlidőt
(`first_seen_mtime_ns`), és minden DÁTUM-szemantikájú olvasó azt
használja az élő `mtime` helyett.**

| | |
|---|---|
| a dátum elsődleges forrása | változatlanul az EXIF `taken_at` |
| a tartalék | **`PhotoRecord.sort_mtime_ns`** = a befagyasztott érték, hiányában az élő `mtime` |
| ki kapja meg | a rács rendezőkulcsa, a mappa-fejléc és az állapotsor dátumtartománya (a `photo_dates`-en át), a mappa indexelt dátuma, az Időrend nézet |
| ki NEM kapja meg | minden olvasó, amely a fájl MOSTANI állapotát kérdezi: a változás-detektálás, a bélyegkép- és dHash-gyorstár kulcsa, a bal hasáb „legutóbbi változtatás" rendezése, a bélyegkép-URL cache-törője |

### Mit nyerünk

- A sorrend **stabil** a külső `mtime`-írásokkal szemben (mentés,
  `rsync`, NAS-szinkron, fájlmásolás) — ez a #2304 mért 19 fájlja.
- A sorrend stabil a **saját szerkesztéseinkkel** szemben is: az ADR-006
  visszafordítása (#2491) óta minden ini-írásunk átírja a képfájl idejét.
  E döntés nélkül a #2491 ára az lett volna, hogy minden szerkesztés
  előreugratja a képet a rácsban.
- **Egyeznek a nézetek.** A rács, a mappa-fejléc, az állapotsor és az
  Időrend ugyanazt a napot mondja ugyanarról a képről. Élő `mtime` mellett
  ez véletlen volt; most szerződés (őr: `TestIdorend`).
- Közelebb kerülünk az eredetihez — a mechanizmus **mért**, nem ízlés.

### Mit veszítünk — kimondva

- **Egy VALÓBAN megváltozott képnél a régi időt tartjuk.** Ha a
  felhasználó lecseréli a fájl tartalmát (más kép ugyanazon a néven), a
  dátum-rendezésben a régi helyén marad. Ezt tudatosan vállaljuk: a
  Picasa is így viselkedik, és az egyezés a projekt mércéje. Aki a
  tényleges változást keresi, a bal hasáb **„legutóbbi változtatás"**
  rendezését kapja — az szándékosan az élő `mtime`-on maradt.
- **Az EXIF-ág NEM fagy be.** A `taken_at`-et minden szinkron
  újraolvassa; az eredeti azt is befagyasztja (10.3). Ez tudatos, szűkebb
  hatókör: a jegy az `mtime`-instabilitásról szól, az EXIF felvételi ideje
  pedig a gyakorlatban nem változik magától. Ha egyszer mégis felmerül, az
  külön lelet lesz — nem itt, hallgatólagosan.

## A MIGRÁCIÓ — a lap legkényesebb pontja

A v16→v17 lépés (`index/schema.py`, `_FIRST_SEEN_MTIME_MIGRATION`):

```sql
ALTER TABLE photos ADD COLUMN first_seen_mtime_ns INTEGER;
UPDATE photos SET first_seen_mtime_ns = mtime_ns;
```

**A meglévő sorok a MAI `mtime`-mal töltődnek fel, nem NULL-lal.** Aminek
a fájlideje ma már át van írva — a #2304 tizenkilenc fájlja —, annál a
**befagyasztott érték is az átírt idő lesz.** Ezt nem szépítjük: a
javítás **nem visszamenőleges**. Amit ad: onnantól nem romlik tovább.

**Miért nem NULL, ahogy a jegy felvetette.** Mert a NULL sosem töltődne
fel: a mappa-szinkron a **változatlan** fotóra nem futtat `UPSERT`-et
(`index/sync.py`, a „Változatlan fájl" ág), tehát a sor épp a fájl
**következő átírásakor** kapna értéket — vagyis pontosan a romlott idő
fagyna be. A NULL-os változat nemcsak nem jobb: rosszabb.

**Miért nem a Picasa `thumbindex`-éből vesszük át.** Ez volna a
legpontosabb forrás, és az olvasónk megvan (`pmpimport/thumbindex.py`,
1. FILETIME). De: (a) a migráció nem tudja, hol van — és van-e — a
felhasználó `db3` könyvtára; (b) a felhasználók többségének nincs Picasa
katalógusa, tehát a lépés nem lehet általános; (c) az átvétel
útvonal-újratérképezést igényel (`PathRemapper`), ami interaktív. Ezért a
migráció **nem** próbálja meg. Nyitott kérdésként lent szerepel: a
`pmpimport` ágon egy KÜLÖN, kézzel indított „vedd át a Picasa dátumait"
lépés a jövőben megadhatja a pontos értéket.

## Visszafelé kompatibilitás — a #2486 3. követelménye

Az igazságforrás a `.picasa.ini`; az index **eldobható és
újraépíthető**. A befagyasztott érték az indexben él, tehát elveszhet:

- **az index törlésekor** — az újraépítés a MAI fájlidőt fagyasztja be,
  vagyis pontosan azt adja, amit a #2486 ELŐTTI kód is adott volna;
- **egy v17 előtti, még nem migrált indexnél** vagy kézzel épített
  rekordnál (tesztek, `webexport`) — a `sort_mtime_ns` az élő `mtime`-ot
  adja vissza.

Mindkét esetben a viselkedés a régi, tehát **nem romlik el semmi**.
Őrizve: `TestVisszaeses`.

## Nyitott kérdések

- A meglévő katalógus pontos dátumainak átvétele a Picasa
  `thumbindex`-éből (külön, kézzel indított lépés a `pmpimport` ágon).
- A `taken_at` befagyasztása (az eredeti azt is fagyasztja) — ma
  szándékosan hatókörön kívül.

## Kötés

*Gépi mezők — a `scripts/check_decision_links.py` őre olvassa. Ha a
megvalósítás átkerül máshova, ITT is vezesd át; az elárvult hivatkozás
hamis biztonságérzetet ad.*

- **Státusz:** ELFOGADVA
- **Megvalósítja:** `src/picasapy/index/schema.py`, `src/picasapy/index/sync.py`, `src/picasapy/index/queries.py`, `src/picasapy/app/photo_sort.py`, `src/picasapy/timeline.py`
- **Őrzi:** `tests/index/test_befagyasztott_fajlido_2486.py`

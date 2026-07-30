# UI-audit: menürendszer (#324)

Forrás: az eredeti **Picasa 3.9** magyar nyelvű felületének 35 képernyőképe
(`2026-07-17 20 54 38.png` … `2026-07-17 21 00 20.png`, végigkattintva minden
felső menün). Összevetve a jelenlegi implementációval:
`src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml` + a hozzá tartozó fordítások
(`src/picasapy/app/i18n/picasapy_hu.ts`, `PicasaMenuBar` kontextus).

A „van-e nálunk" oszlop: **igen** = a menüpont létezik nálunk (akár inaktívan
is — ez a dizájn szándékos része, a QML-fejléc szerint); **nem** = teljesen
hiányzik; **eltérő** = van megfelelője, de más szerkezetben/helyen/névvel.

Megjegyzés a struktúráról: az eredeti Picasában a 4. menü címkéje
**kontextusfüggő** — mappa kijelölésekor „Mappa", albuméknál „Album" (a
tartalom nagyrészt azonos). A PicasaPy-ban ez a menü mindig „Folder"/„Mappa"
címkével fut, nem vált Albumra — ez önmagában egy szerkezeti eltérés, a
táblázatban külön nem soroljuk fel újra az Album-változat tételeit, mert
tartalmilag megegyeznek a Mappa-éval.

---

## 1. Fájl

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Új album... | Ctrl+N | igen | nálunk inaktív (`enabled: false`), gyorsbillentyű nincs |
| Mappa hozzáadása a Picasához... | — | igen | inaktív |
| Fájl felvétele a Picasába... | Ctrl+O | igen | inaktív, gyorsbillentyű nincs |
| Importálás forrása... | Ctrl+M | igen | inaktív, gyorsbillentyű nincs |
| Importálás a Google Fotókból... | — | **nem** | teljesen hiányzik |
| Fájl(ok) megnyitása szerkesztőben | Ctrl+Shift+O | **nem** | hiányzik |
| Áthelyezés új mappába... | — | **nem** | hiányzik |
| Átnevezés... | F2 | igen | megvan, működik (`Rename...`), gyorsbillentyű nincs |
| Mentés | Ctrl+S | igen | inaktív, gyorsbillentyű nincs |
| Visszaállítás | — | igen | inaktív (`Revert`) |
| Mentés másként... | — | **nem** | hiányzik |
| Másolat mentése | — | **nem** | hiányzik |
| Kép exportálása mappába... | Ctrl+Shift+S | igen | megvan, működik, gyorsbillentyű nincs |
| Keresés a lemezen | Ctrl+Enter | igen | megvan, működik (`Locate on Disk`), gyorsbillentyű nincs |
| Törlés lemezről | Delete | igen | megvan, működik (`Delete from Disk`), gyorsbillentyű nincs |
| Nyomtatás... | Ctrl+P | igen | inaktív |
| E-mail... | Ctrl+E | igen | inaktív |
| Papírképek rendelése... | — | **nem** | teljes funkció hiányzik (nyomtatott képek online rendelése) |
| Kilépés | — | igen | megvan, működik |

## 2. Szerkesztés

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Kivágás | Ctrl+X | **nem** | hiányzik (a top-menüből; szövegmezőkben feltehetően OS-szinten működik) |
| Másolás | Ctrl+C | **nem** | hiányzik |
| Beillesztés | Ctrl+V | **nem** | hiányzik |
| Az összes effektus másolása | — | igen | megvan, működik (`Copy All Effects`) |
| Az összes effektus beillesztése | — | igen | megvan, működik (`Paste All Effects`) |
| Szöveg másolása | — | **nem** | hiányzik (feliratszöveg másolása) |
| Szöveg beillesztése | — | **nem** | hiányzik |
| Az összes kijelölése | Ctrl+A | igen | megvan, gyorsbillentyű nincs |
| Csillagozottak kijelölése | — | igen | megvan |
| Kiválasztás megfordítása | Ctrl+I | igen | inaktív nálunk is, gyorsbillentyű nincs |
| Kijelölés törlése | Ctrl+D | igen | megvan, gyorsbillentyű nincs |

## 3. Nézet

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Könyvtárnézet | — | igen | eredetiben inaktív, ha már aktív nézet; nálunk mindig aktív jelölhető tétel (`checked: true`, sosem grayed) |
| Kis indexképek | Ctrl+1 | igen | gyorsbillentyű nincs |
| Normál indexképek | Ctrl+2 | igen | gyorsbillentyű nincs |
| Szerkesztési nézet | Ctrl+3 | igen | inaktív (`Edit View`) |
| Tulajdonságok | — | igen | megvan, működik |
| Címkék | Ctrl+T | igen | gyorsbillentyű nincs |
| Emberek | — | igen | inaktív (`People`) |
| Helyek | — | igen | megvan, működik |
| Szerkesztési vezérlők megjelenítése | — | **nem** | hiányzik (szerkesztő panel láthatóság-kapcsoló) |
| Diavetítés | Ctrl+4 | igen | gyorsbillentyű nincs |
| Időrend | Ctrl+5 | igen | gyorsbillentyű nincs |
| Keresési opciók | — | **nem** | hiányzik |
| Kis képek *(feltehetően „Thumbnails Only")* | — | **nem** | hiányzik; pontos jelentése a képekből nem egyértelmű, valószínűleg mappacím nélküli indexkép-rács |
| Rejtett képek | — | igen | megvan, működik |
| Színkezelés használata | — | **nem** | hiányzik (színprofil-kezelés kapcsoló) |
| Megjelenítési mód ▸ (almenü) | — | **nem** | teljes almenü hiányzik, tartalma a képekből nem derül ki |
| Indexkép felirata ▸ (almenü) | — | igen | `Thumbnail Caption` almenü, tartalma egyezik (Nincs/Fájlnév/Felirat/Címkék/Felbontás) |
| Mappanézet ▸ (almenü) | — | igen | `Folder View` almenü, tartalma egyezik (dátum/változás/méret/név szerint + fordítás) |

**Nálunk van, az eredetiben nincs:** „Dark Theme" (sötét téma) — szándékos
PicasaPy-bővítés, jó helyen van jelölve.

## 4. Mappa / Album

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Leírás szerkesztése... | — | igen | megvan, működik |
| Diavetítés megtekintése | Ctrl+4 | igen | gyorsbillentyű nincs |
| Indexképek frissítése | — | igen | megvan, működik (`Refresh Thumbnails`) |
| Rendezés ▸ (almenü, aktív) | — | **eltérő** | nálunk `Sort By` egyetlen **inaktív** tétel, nem valódi almenü; a tartalom (dátum/legutóbbi változás/méret/név/fordítás) máshol, a Nézet ▸ Mappanézet almenüben már megvan — csak innen hiányzik |
| Elrejtés | — | **nem** | hiányzik (mappa szintű elrejtés — más, mint a Nézet ▸ Rejtett képek) |
| Megjelenítés | — | **nem** | hiányzik (elrejtett mappa visszaállítása) |
| Indexképek nyomtatása... | Ctrl+Shift+P | **nem** | hiányzik |
| Exportálás HTML-oldalként... | — | **nem** | **teljes funkció hiányzik**: a mappa/album exportálása statikus HTML-galériaként |
| Keresés a lemezen | Ctrl+Enter | igen | megvan (`Locate on Disk`), inaktív |
| Eltávolítás a Picasából... | — | igen | megvan (`Remove from Picasa...`), inaktív |
| Áthelyezés... | — | **nem** | hiányzik (mappa áthelyezése a lemezen) |
| Törlés... | — | **nem** | hiányzik (mappa törlése) |

## 5. Kép

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Megjelenítés és szerkesztés | Ctrl+3 | igen | inaktív (`View and Edit`) |
| Csoportos szerkesztés ▸ (almenü) | — | **eltérő** | nálunk `Batch Edit` sima inaktív tétel, nem almenü; az almenü tartalma a képekből nem derül ki |
| Összes szerkesztés visszavonása | — | igen | inaktív (`Undo All Edits`) |
| Elrejtés | — | igen | nálunk egyetlen kapcsoló (`Hide`) a kijelölésre; az eredetiben két külön (inaktívra váltó) tétel van: Elrejtés / Megjelenítés |
| Megjelenítés | — | **eltérő** | ld. fent — nálunk ugyanaz a `Hide` tétel intézi mindkét irányt |
| Arcok alaphelyzetbe állítása | — | **nem** | **teljes funkció hiányzik**: felismert arc-négyzetek pozíciójának visszaállítása (arcfelismerés-előkészítés, 3. fázis témája, de a menüpont már a 3.9-ben is jelen van) |
| Tulajdonságok | Alt+Enter | igen | megvan, működik, gyorsbillentyű nincs |

## 6. Létrehozás

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Beállítás háttérképként... | — | **nem** | hiányzik |
| Poszter készítése... | — | igen | inaktív (`Make a Poster...`) |
| Képkollázs... | — | igen | megvan, működik |
| Hozzáadás a képernyővédőhöz... | — | **nem** | teljes funkció hiányzik |
| Ajándék CD készítése... | — | **nem** | teljes funkció hiányzik |
| Mozgófilm ▸ (almenü) | — | **eltérő** | nálunk `Movie` sima tétel, működik, de az eredetiben almenü — tartalma a képekből nem derül ki |
| Közzététel a Bloggeren... | — | **nem** | teljes funkció hiányzik |

## 7. Eszközök

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Mappakezelő... | — | igen | megvan, működik |
| Feltöltéskezelő... | — | **nem** | hiányzik (eredetiben is inaktív volt ekkor) |
| Személyek kezelése... | — | igen | inaktív (`People Manager...`) |
| Fotómegjelenítő beállítása... | — | **nem** | hiányzik |
| Képernyővédő konfigurálása... | — | **nem** | hiányzik |
| Képek biztonsági mentése... | — | igen | inaktív (`Back Up Pictures...`) |
| Csoportos feltöltés... | — | **nem** | hiányzik |
| Dátum és idő beállítása... | — | igen | inaktív (`Adjust Date and Time...`) |
| Feltöltés ▸ (almenü) | — | **nem** | teljes almenü hiányzik |
| Geocímke ▸ (almenü) | — | **nem** | teljes almenü hiányzik |
| Kísérleti ▸ (almenü) | — | **nem** | teljes almenü hiányzik |
| Gombok konfigurálása... | — | **nem** | hiányzik |
| Beállítások... | — | igen | inaktív (`Options...`) |

**Nálunk van, az eredetiben nincs:** „Duplikátum-kereső..." (#287,
`Find Duplicates...`) — szándékos PicasaPy-bővítés, az eredeti Picasa
3.9-ben nem létezett ilyen beépített funkció.

## 8. Súgó

| eredeti felirat | gyorsbillentyű | van-e nálunk | megjegyzés |
|---|---|---|---|
| Súgó - tartalom és tárgymutató | F1 | igen | inaktív, gyorsbillentyű nincs |
| Billentyűkódok | — | igen | inaktív (`Keyboard Shortcuts`) |
| Picasa-fórumok | — | **nem** | hiányzik (web-link, PicasaPy-nak saját fórum kellene) |
| Online információ | — | **nem** | hiányzik (web-link) |
| Termékkiadási tájékoztató | — | **nem** | hiányzik (web-link, release notes) |
| Adatvédelmi irányelvek | — | **nem** | hiányzik (web-link) |
| Általános Szerződési Feltételek | — | **nem** | hiányzik (web-link) |
| A Picasa eltávolítása | — | **nem** | irreleváns Google-specifikus tétel, nem kell portolni |
| Frissítések keresése | — | igen | inaktív (`Check for Updates`) |
| A Picasa névjegye | — | igen | megvan, működik (`About PicasaPy`) |

**Nálunk van, az eredetiben nincs:** „Performance Monitor" — szándékos
PicasaPy-bővítés (fejlesztői teljesítménymérő panel).

---

## Bónusz észrevétel: jobbklikk kontextusmenük

Két képernyőkép jobbklikk-kontextusmenüt is mutat (mappa a bal panelen, kép
a rácsban). Ezek nem részei a felső menüsávnak, de két, a top-menüből teljesen
hiányzó funkciót fednek fel, amelyek **még kontextusmenüből sem érhetők el
nálunk**, ezért érdemes külön jegyként rögzíteni:

- **„Mappa felosztása itt..."** (Split Folder Here) — egy mappa két
  almappára bontása egy adott képnél; nincs se top-menüben, se nálunk sehol.
- **„Teljes elérési út másolása"** (Copy full path) — a kép teljes fájl­
  elérési útjának vágólapra másolása; nincs se top-menüben, se nálunk sehol.
- **„Társítás" ▸** (Associate with) almenü — fájltípus-társítások kezelése;
  csak kontextusmenüből érhető el az eredetiben is.
- **Forgatás jobbra/balra** (Ctrl+R / Ctrl+Shift+R) — csak kontextusmenüből
  (és feltehetően a rács-eszköztárból) érhető el az eredetiben is, a felső
  Kép menüben nincs — ez tehát *nem* hiányzó menüpont nálunk, csak jelezzük,
  hogy a forgatás nem a Kép-menü hatásköre volt eredetileg sem.

---

## Összegző lista

### Teljesen hiányzó menüpontok (nincs se aktív, se inaktív megfelelőjük)

**Fájl:** Importálás a Google Fotókból…; Fájl(ok) megnyitása szerkesztőben;
Áthelyezés új mappába…; Mentés másként…; Másolat mentése; **Papírképek
rendelése…** (önálló funkció).

**Szerkesztés:** Kivágás / Másolás / Beillesztés; Szöveg másolása / Szöveg
beillesztése.

**Nézet:** Szerkesztési vezérlők megjelenítése; Keresési opciók; Kis képek
(feltehetően „Thumbnails Only"); Színkezelés használata; **Megjelenítési
mód almenü** (teljes tartalommal).

**Mappa:** Elrejtés / Megjelenítés (mappa szinten); Indexképek nyomtatása…;
**Exportálás HTML-oldalként…** (önálló funkció); Áthelyezés…; Törlés….

**Kép:** **Arcok alaphelyzetbe állítása** (önálló funkció).

**Létrehozás:** Beállítás háttérképként…; **Hozzáadás a
képernyővédőhöz…** (önálló funkció); **Ajándék CD készítése…** (önálló
funkció); **Közzététel a Bloggeren…** (önálló funkció).

**Eszközök:** Feltöltéskezelő…; Fotómegjelenítő beállítása…; Képernyővédő
konfigurálása…; Csoportos feltöltés…; **Feltöltés / Geocímke / Kísérleti
almenük** (teljes tartalommal); Gombok konfigurálása….

**Súgó:** Picasa-fórumok; Online információ; Termékkiadási tájékoztató;
Adatvédelmi irányelvek; ÁSZF (ez utóbbi öt inkább web-link, alacsony
prioritás).

### Meglévő, de eltérő szerkezetű/névvel/helyen szereplő tételek

- **Mappa ▸ Rendezés**: nálunk inaktív, sima tétel, holott az eredetiben
  működő almenü — a tényleges rendezési logika nálunk csak a Nézet ▸
  Mappanézet almenüben érhető el, a Mappa menüből hiányzik a bekötés.
- **Kép ▸ Csoportos szerkesztés**: nálunk sima inaktív tétel, az eredetiben
  almenü.
- **Létrehozás ▸ Mozgófilm**: nálunk sima (működő) tétel, az eredetiben
  almenü — a tényleges almenü-tartalom nem ismert a képekből.
- **Kép ▸ Elrejtés/Megjelenítés**: nálunk egy kapcsoló (`Hide`) intézi,
  amit az eredeti két külön (kontextusonként inaktívra váltó) menüpont old meg.
  Funkcionálisan ekvivalens, csak UX-mintázatban tér el.
- **A 4. menü címkéje**: az eredetiben kontextusfüggő (Mappa/Album), nálunk
  mindig „Folder".

### Funkció szintű hiányok (nem csak menüpont, hanem teljes, eddig nem
dokumentált feature az eredeti Picasában)

1. **Exportálás HTML-oldalként…** (mappa/album statikus HTML-galériaként
   való exportja) — sem a `feature-map.md`-ben, sem eddig sehol nem szerepel.
2. **Papírképek rendelése…** (nyomtatott fotók online rendelése) — Google-
   szolgáltatás-függő, valószínűleg tudatosan nem lesz cél, de dokumentálni
   kell, hogy hiányzik.
3. **Arcok alaphelyzetbe állítása** — a 3. fázis (arcfelismerés) előkészítő
   funkciója; eddig a `feature-map.md` arc-fejezete nem említi kifejezetten
   a pozíció-visszaállítást.
4. **Hozzáadás a képernyővédőhöz…** / **Ajándék CD készítése…** / **Beállítás
   háttérképként…** — OS-integrációs funkciók csoportja, teljesen hiányzik a
   tervekből.
5. **Közzététel a Bloggeren…** — külső szolgáltatás-integráció, Google
   Blogger megszűnt státusza miatt valószínűleg elavult, de jelezni kell.
6. **Feltöltés / Geocímke / Kísérleti almenük** az Eszközök menüben — ezek
   tartalma a képekből nem derül ki (nem lettek megnyitva), de már a
   meglétük ténye is azt jelzi, hogy a Google-feltöltés és a geocímkézés
   az eredetiben sokkal részletesebb beállítási felülettel rendelkezett,
   mint amit eddig terveztünk.
7. **Mappa szintű Elrejtés/Megjelenítés** — ez különbözik a már megvalósított
   „Rejtett képek" nézetkapcsolótól: az eredetiben egy egész mappa
   kihagyható a könyvtárból, nem csak képenként rejthető el.

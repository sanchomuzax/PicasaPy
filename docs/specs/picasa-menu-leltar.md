# A menüsor TELJES leltára a binárisból — 189 tétel, 18 névtér

*2026-08-25. Ez a lap **gépi** leltár: a `stringres-en-hu.tsv` `eMenu*`
névtereiből származik, nem képernyőképekből.*

> ⚠️ **Miért kellett a képernyőkép-alapú `ui-audit-menus.md` mellé ez is:**
> az a lap **35 képernyőképből** készült, tehát csak azt látta, ami a
> tulajdonos gépén, az ő állapotában **meg is jelent**. A szövegtár ezzel
> szemben **minden** menütételt tartalmaz — a feltételesen megjelenőket, a
> platformfüggőket és a halottakat is.

## 1. A tizennyolc névtér

A menütételek kulcsa `eMenu<Menü>::ID_<PARANCS>` alakú.

| névtér | tétel | mi ez |
|---|---:|---|
| `eMenuView` | 46 | Nézet |
| `eMenuTools` | 38 | Eszközök |
| `eMenuFile` | 21 | Fájl |
| `eMenuPicture` | 18 | Kép |
| `eMenuLabelFolder` | 14 | Mappa / Album (kontextusfüggő címke) |
| `eMenuEdit` | 14 | Szerkesztés |
| `eMenuHelp` | 11 | Súgó |
| `eMenuCreate` | 8 | Létrehozás |
| `eMenuCreateMovie` | 3 | **almenü**: Létrehozás → Film |
| `eMenuViewWin` · `eMenuViewMac` | 3 + 3 | platformfüggő Nézet-tételek |
| `eMenuFileWin` · `eMenuFileMac` | 2 + 3 | platformfüggő Fájl-tételek |
| `eMenuCreateWin` · `eMenuCreateMac` | 1 + 1 | platformfüggő |
| `eMenuPictureWin` · `eMenuPictureMac` | 1 + 1 | platformfüggő |
| `eMenuHelpMac` | 1 | platformfüggő |
| **összesen** | **189** | |

⇒ A **nyolc főmenü** (Fájl, Szerkesztés, Nézet, Mappa/Album, Kép,
Létrehozás, Eszközök, Súgó) egyezik a képernyőképekkel; a leltár a
**platform-változatokat** és **egy almenüt** (`eMenuCreateMovie`) is
megmutat, amit a képernyőkép-audit nem.

## 2. Lefedettség — 165/189 (87%), újramérve 2026-09-02

Mérés: a menütétel angol ÉS magyar feliratát keresve a **teljes QML-fában**
és a `picasapy_hu.ts`-ben, ékezet-, `&`- és „…"-független
összehasonlítással. (Az első mérés csak a `PicasaMenuBar.qml`-t nézte; a
helyi menük és a más fájlokba került tételek így kimaradtak belőle.)

| menü | összes | nálunk | hiányzik | 2026-08-25-höz képest |
|---|---:|---:|---:|---|
| `eMenuTools` | 38 | 24 | **14** | −4 |
| `eMenuView` | 46 | **46** | **0** | **−9, teljes lett** |
| `eMenuFile` | 21 | 19 | 2 | — |
| `eMenuHelp` | 11 | 10 | 1 | — |
| `eMenuCreateMovie` | 3 | 2 | 1 | — |
| `eMenuPicture` · `eMenuEdit` · `eMenuLabelFolder` · `eMenuCreate` | 54 | **54** | **0** | — |
| platform-változatok (Mac/Win) | 16 | 10 | 6 *(hatókörön kívül)* | −1 |
| **összesen** | **189** | **165** | **24** | **−15** |

⚠️ **A 2026-08-25-i 150/189 (79%) ELAVULT** — a `eMenuView` névtér azóta
teljes lett (#1434, #1595, #1766 köre). Az alábbi 3.1–3.3 csoportosítás a
RÉGI, 39 tételes mérésből származik; a tételek besorolása (hatókörön kívül
/ érdemi) továbbra is érvényes, csak a darabszámok mozdultak.

**Az érdemi hiányra mind van nyitott jegy** (2026-09-02-án ellenőrizve):
#1398 · #1399 · #1401 · #1402 · #1403 · #1404 · #1405 · #1406 · #1408.

## 3. A HIÁNYZÓ 39 tétel, három csoportban

### 3.1 Hatókörön kívül — halott online szolgáltatás vagy más platform (14)

| parancs | felirat | miért |
|---|---|---|
| `ID_GETMYSTUFF` | Importálás a Picasa Webalbumokból… | a szolgáltatás megszűnt |
| `ID_DELETE_EMPTY_ALBUMS` | Üres online albumok törlése… | ua. |
| `ID_TOOLS_COLLAB` | Feltöltés közös szerkesztésű webalbumba | ua. |
| `ID_TOOLS_DOWNLOAD_FACES` | Névcímkék letöltése a Picasa Webalbumokból | ua. |
| `ID_TOOLS_YOUTUBE` | Feltöltés a YouTube webhelyre | külső szolgáltatás |
| `ID_FTPWEB` | Közzététel FTP-n keresztül… | elavult közzétételi mód |
| `ID_PICTURE_GEOTAG` | Geocímkézés a Google Earth programmal… | a Google Earth-integráció megszűnt |
| `ID_VIEW_EARTH` | Megtekintés a Google Earth programban… | ua. |
| `ID_IPHOTOIMPORT` | Importálás az iPhoto alkalmazásból… | Apple-ág, tulajdonosi döntés (2026-08-21) |
| `ID_HELP_UNINSTALL` | A Picasa eltávolítása | telepítő-specifikus |
| `ID_VIEW_MAC` | Mac gamma (1.6) | platform |
| `ID_VIEW_RDESK` | Távoli asztal | platform-specifikus megjelenítés |
| *(+ 2 további Mac-változat)* | | |

### 3.2 ÉRDEMI hiány — feltárandó (18)

Ezek valódi, megépíthető funkciók, és a binárisból feltárhatók:

| # | parancs | felirat | megjegyzés |
|---:|---|---|---|
| 1 | `ID_DUPES` | Fájlok másodpéldányainak megjelenítése | **van `dedup/` csomagunk** — összevetendő |
| 2 | `ID_PASSPORT` | Útlevélkép… | önálló, jól körülhatárolt funkció |
| 3 | `ID_MOVE_DATABASE` | Adatbázis helyének kiválasztása… | infrastruktúra; érinti a `db3` útvonalat |
| 4–7 | `ID_S_GREEN` · `ID_S_ORANGE` · `ID_S_PURPLE` · `ID_S_YELLOW` | Zöld · Narancssárga · Lila · Sárga | **színcímke-rendszer**, négy tétel egyben |
| 8 | `ID_SAVESEARCH` | Keresési eredmények mentése… | a `]search` tokenhez kapcsolódik |
| 9 | `ID_SEARCHTOKEN` | Címke megjelenítése albumként… | ua. |
| 10 | `ID_WRITE_XMP_FACES` | Arcinformációk írása XMP-adatokba… | az arcfelismerés kimenete |
| 11 | `ID_PICTURE_GEOUNTAG` | Geocímkék törlése | a `geotag` ini-kulcshoz |
| 12 | `ID_VIEW_FOLDERS` | Egyszerű mappanézet | a lapos mappanézet |
| 13–18 | `ID_VIEW_16` · `ID_VIEW_NORMAL` · `ID_VIEW_LCD` · `ID_VIEW_LINEAR` · `ID_VIEW_OV` · `ID_VIEW_PROJECTOR` | 16 bites (szemcsézett) · 24 bites · LCD fehérpont · Lineáris gamma (2.2) · Túlcsordult képpontok megjelenítése · Projektor mód | **megjelenítési/gamma-módok** — egy összefüggő készlet |

### 3.3 Almenü-hiány (1)

| parancs | felirat |
|---|---|
| `ID_FACES` (`eMenuCreateMovie`) | A kijelölésben lévő arcokból… |

## 4. Hogyan reprodukálható ez a leltár

```bash
awk -F'\t' '$1 ~ /^eMenu/ {print $1"\t"$2"\t"$3}' \
    ~/picasapy-agent/referencia/stringres-en-hu.tsv | sort
```

*Bizonyítottsági fok: **megerősített** a leltárra (a szállított
szövegtárból). A lefedettség-mérés **erős**: felirat-egyezésen alapul, tehát
egy átfogalmazott menüpontot „hiányzónak" jelölhet — ezért a 3.2 lista
minden tétele külön ellenőrzendő a megvalósítás előtt.*

---

## 5. Az Eszközök menünek NÉGY ALMENÜJE van (2026-08-25)

A `eMenuTools` névtér **nem lapos**: négy kulcs nem `ID_`-vel kezdődik —
ezek az **almenü-fejlécek**:

| kulcs | magyar felirat | mi tartozik alá (a tételekből következtetve) |
|---|---|---|
| `Experimental` | **Kísérleti** | — |
| `Geotag` | **Geocímke** | `ID_PICTURE_GEOTAG`, `ID_PICTURE_GEOUNTAG`, `ID_EXPORT_EARTH`, `ID_VIEW_EARTH` |
| `Searchfor` | **Keresés…** | a hat `ID_S_<szín>`, `ID_SAVESEARCH`, `ID_SEARCHTOKEN`, `ID_DUPES` |
| `Upload` | **Feltöltés** | `ID_TOOLS_UPLOAD`, `ID_TOOLS_UPLOAD_ES`, `ID_TOOLS_BATCH_UPLOAD`, `ID_TOOLS_YOUTUBE`, `ID_TOOLS_COLLAB` |

⚠️ A képernyőkép-alapú audit ezt az **almenü-szerkezetet** nem rögzítette.

*A hozzárendelés bizonyítottsági foka: **erős** — a felirat-szemantikából és
a névterek együtt-tárolásából; a menüépítő kódban nincs végigkövetve.*

## 6. A hat `ID_S_<szín>` = KERESÉS SZÍN SZERINT

**Hat szín**, nem négy (a korábbi hiánylistám kettőt tévesen lefedettnek
jelölt, mert a „Kék"/„Piros" szó máshol előfordul a fordításunkban):

| parancs | HU | | parancs | HU |
|---|---|---|---|---|
| `ID_S_BLUE` | Kék | | `ID_S_PURPLE` | Lila |
| `ID_S_GREEN` | Zöld | | `ID_S_RED` | Piros |
| `ID_S_ORANGE` | Narancssárga | | `ID_S_YELLOW` | Sárga |

**Ez nem színcímkézés, hanem keresés**: a `Searchfor` („Keresés…") almenü
alatt ülnek, és a binárisban ott van hozzá az **`ImageColorSwatch`**
(`0x00bb41c0`) — a színminta-vezérlő.

### Az adatforrás: `imagedata_avgcolor` — MÉRVE valódi adaton

| adatbázis | sor | nem üres | arány |
|---|---:|---:|---:|
| `research/testdata/Picasa2/db3` | 140 755 | **133 454** | **94,8 %** |
| `research/testdata/Picasa2-arcok/…/db3` | 3 335 | 2 792 | 83,7 % |

A tárolt érték **ARGB dword**, alfa mindig `0xff`. Példák:
`0xffaca190` (R 172, G 161, B 144 — meleg bézs), `0xff5a5046`,
`0xfff7f8f9` (majdnem fehér). Ezek hihető **kép-átlagszínek**.

⇒ A Picasa **minden képre** eltárolja az átlagszínt, és a szín szerinti
keresés ezen dolgozik.

*Bizonyítottsági fok: **megerősített** az oszlop létére, típusára és
kitöltöttségére (valódi adaton mérve) és az `ImageColorSwatch` létére.
**Erős, nem megerősített**: hogy a keresés konkrétan ezt az oszlopot
olvassa — a keresőkód nincs végigkövetve odáig.*

---

## 7. A TELJES parancstérkép a menüépítő kódból (2026-08-25)

A 1–6. szakasz a **szövegtárból** dolgozott. Ez a szakasz a **kódból**: a
menüsort egyetlen függvény építi, és abból a **parancsazonosítók** is
kiolvashatók.

### A menüépítő: `0x00559150` — 15 495 bájt

Ez a `CMenuBar` építője; **minden** menüt ez rak össze. A menürekord
felépítése soronként visszaköszön:

```asm
push  <fordítási kulcs>                  ; pl. "eMenuView::ID_VIEW_PROJECTOR"
mov   eax, <alapértelmezett angol felirat>   ; "&Projector Mode"
mov   dword ptr [rek+0x04], ebx          ; gyorsbillentyű-szöveg
mov   word  ptr [rek+0x08], bx           ; gyorsítóbillentyű-módosítók maszkja (8.5)
mov   word  ptr [rek+0x0a], 0x9d20       ; <<< PARANCSAZONOSÍTÓ
mov   dword ptr [rek+0x0c], ebx          ; almenü-tömb
mov   dword ptr [rek+0x10], ebx          ; almenü darabszám
```

*(A `+0x0a` = parancsazonosító itt **igazolódik** — szemben a `Tray` helyi
menü rekordjaival, ahol ugyanez a mező mást hordozott, ld.
`picasa-keptalca.md` 12.)*

### A kinyert térkép: 177 tétel, **140 ellenőrzött parancsazonosítóval**

> 🟢 **HARMADIK, SIKERES KINYERÉS — 2026-09-01 (#1581).** Az oszlop
> **visszakerült** a CSV-be. A korábbi „ne legyen harmadik próbálkozás"
> figyelmeztetés ezzel érvényét vesztette: nem a feladat volt
> megoldhatatlan, hanem a horgony volt rossz.
>
> **A bukás oka (a #1409 lelete).** A fordító a menürekord `+0x04`…`+0x10`
> mezőit a **KÖVETKEZŐ** rekord feliratának betöltése **után** írja ki. Aki
> a `push "…kulcs"`-ot a rá következő `mov word ptr […+0x0a]`-val olvassa
> össze, **egy rekorddal elcsúszik**. A csúszás azért látszott
> „szabálytalannak", mert nem minden rekordot előz meg felirat-betöltés (az
> elválasztók és az almenü-fejek nem), így a hiba hol jelentkezett, hol nem.
>
> **A javított horgony:** `mov dword ptr [REK], eax` — ez adja a rekord
> KEZDŐCÍMÉT, és a `+0x0a` ahhoz tartozik.

#### A kinyerés menete — és miért nem diszasszemblálással

A `.text` adatszigeteket tartalmaz; lineáris dekódolásnál a menüépítő
környékén értelmetlen utasítások jönnek ki (`call 0xb8567ea4`), és a
kinyerés csendben félresiklik. Ehelyett a menüépítő **gépiesen ismételt
sablonjának bájtmintáját** keressük — annak fix a kódolása, tehát nincs
szinkronvesztés:

```asm
68 <kulcs>          push  "<Osztály::ID_NEV>"
B8 <imm32>          mov   eax, <angol felirat>
[csak tárolások]    a MEGELŐZŐ rekord +0x04..+0x10 mezői
E8 <rel32>          call  <fordítás-betöltő>
8B 00 / 83 C4 04 / 3B C3 / 74 0A / 83 C0 04
A3 <REK>            mov   dword ptr [REK], eax    ; <<< a rekord kezdőcíme
```

A `push`-t **csak akkor** fogadjuk el, ha a `call`-ig vezető út kizárólag
tárolásokból áll — vagyis a sablon hiánytalanul kirajzolódik. Ahol nem, a
cella **üresen marad**.

⚠️ **Ez a szigor nem óvatoskodás, hanem mérés.** Kipróbáltam a kényelmes
változatot is („keresd visszafelé a legközelebbi `push`-t"): az **három
különböző azonosítót** adott ugyanarra a kulcsra, és a kimenete pontosan
úgy nézett ki, mint egy jó találat. A laza változat 308, a szigorú 146
párt ad — a különbözet nagy része néma tévedés lett volna.

#### A kontroll: 13 független azonosítóból 13 ✔

A kulcs (`eMenuView::ID_VIEW_LCD`) és az azonosító (`+0x0a` = `0x9d20`)
**két különböző mezőből** jön, ezért az egyezésük valódi kontroll. A
#1409/#1454 által korábban, más úton rögzített azonosítók mind stimmelnek:

`ID_VIEW_16` · `ID_VIEW_PROJECTOR` · `ID_VIEW_MAC` · `ID_VIEW_SEPIA` ·
`ID_VIEW_LINEAR` · `ID_VIEW_NORMAL` · `ID_VIEW_AUTO` · `ID_VIEW_LCD` ·
`ID_VIEW_OV` · `ID_VIEW_RDESK` · `ID_VIEW_FOLDERS` · `ID_VIEW_WATCHED` ·
`ID_VIEW_ALL` — **13/13, eltérés nincs.**

#### ⭐ Amit menet közben megtanultunk: a kulcs a FELIRATOT nevezi meg

`eMenuView::ID_VIEW_BW` **három** rekordon szerepel, három azonosítóval:

| rekord | azonosító | a szomszédai alapján melyik menü |
|---|---|---|
| `0x00d6ddb0` | `0x9d1c` | Nézet (`ID_VIEW_SEPIA`, `ID_CAPNONE` közt) |
| `0x00d6e41c` | `0x9d4c` | Kép (`ID_PICTURE_WARMIFY` `0x9d4d`, `ID_PICTURE_FILM_GRAIN` `0x9d4e` közt) |
| `0x00d6e780` | `0x9da9` | Eszközök (`ID_S_PURPLE` `0x9da8`, `ID_FTPWEB` közt) |

A szomszédos azonosítók számtani folytonossága **függetlenül igazolja**,
hogy három külön parancsról van szó. A `push`-olt sztring tehát **fordítási
kulcs**, nem parancsnév: a „Fekete-fehér" feliratot három menü használja
újra. A CSV maga is három `eMenuView,ID_VIEW_BW` sort tartalmaz — ezért
ezek a sorok **üresen maradnak**: nem tudjuk, melyik sor melyik menüé.

Három ilyen ütközés van (`ID_VIEW_BW`, `ID_CAPTAG`, `ID_PICTURE_UNHIDE`),
összesen 7 CSV-sort érintve.

#### ⚠️ Egy eltérés a korábbi feljegyzésektől: `0x9db7`

A fenti (2026-08-25-ös) bekezdés `ID_VIEW_MYPICTURES = 0x9db7`-et mond
„helyes"-nek. A mostani kinyerés szerint a `0x9db7`-et hordozó rekord
(`0x00d6de44`) felirat-kulcsa **`eMenuViewWin::ID_VIEW_MYDOCS`**, míg
`eMenuViewWin::ID_VIEW_MYPICTURES` a `0x00d6de58` rekordon áll, azonosítója
**`0x9e3a`**. A fentiek fényében ez nem feltétlenül ellentmondás — a kulcs
a feliratot nevezi meg —, de **a `0x9db7` ↔ `ID_VIEW_MYPICTURES` társítás
nem tekinthető megerősítettnek**. NYITOTT.

#### A kinyerő

`scripts/binaris/menu_parancsazonositok.py` — a bináris útját a
`PICASA_EXE` környezeti változó adja. Függősége (`pefile`) **nincs** a
projekt csomaglistáján: ez kutatóeszköz, nem futásidejű kód.

Géppel olvasható alakban: **[`picasa-menu-parancsok.csv`](picasa-menu-parancsok.csv)**
(oszlopok: `menu`, `parancs`, `parancsazonosito`, `felirat_en`, `felirat_hu`).

| névtér | tétel | | névtér | tétel |
|---|---:|---|---|---:|
| `eMenuView` | 48 | | `eMenuHelp` | 10 |
| `eMenuTools` | 36 | | `eMenuCreate` | 7 |
| `eMenuFile` | 19 | | `CMenuBar` | 4 *(gyorsbillentyűk)* |
| `eMenuPicture` | 19 | | `eMenuCreateMovie` | 3 |
| `eMenuLabelFolder` | 13 | | platform-változatok | 7 |
| `eMenuEdit` | 11 | | | |

> **Miért ez a legfontosabb eszköz a további feltáráshoz:** a
> parancsazonosítóval **közvetlenül megtalálható a kezelője** a főablak
> parancs-diszpécserében (`0x005cb990`), tehát bármely menüpont működése
> egy lépésben kereshetővé vált. A menük tényleg „majdnem minden
> funkcióhoz" elvezetnek — ez a térkép az útjelző.

### Példa: a Nézet menü megjelenítési módjai

> 🟢 **JAVÍTVA 2026-08-27-én (#1409).** Az itt korábban állt tábla **egy
> rekorddal el volt csúszva** — pontosan az a hiba, amire ez a szakasz
> feljebb figyelmeztet. A csúszás oka: a fordító a rekord `+0x0a`
> parancsazonosítóját a **KÖVETKEZŐ** rekord feliratának betöltése után
> írja ki, ezért a `push "…kulcs"` és a rá következő `mov word ptr
> […+0x0a]` **nem** tartozik össze. A helyes horgony a `mov dword ptr
> [<cím>], eax` — az adja a rekord kezdőcímét.
>
> 🟢 **A „ne legyen harmadik próbálkozás" tanács ELAVULT.** A javított
> horgonnyal újramérve **épp az a négy horgony, amelyen a korábbi szabály
> 1/4-et adott, mind a négy egyezik**: `ID_VIEW_MYPICTURES` `0x9db7`
> (`0x0055a26d`) · `ID_VIEW_FOLDERS` `0x9db6` (`0x0055a385`) ·
> `ID_VIEW_ALL` `0x9db9` (`0x0055a3cf`) · `ID_VIEW_WATCHED` `0x9db8`
> (`0x0055a671`). A leképezés tehát **nem szabálytalan**. *(A teljes
> oszlop újbóli kinyerése külön jegy tárgya — a szabály ellenőrzött, az
> oszlop nem.)*
>
> Az alábbi tábla **négy független szemantikai horgonnyal is igazolt** (a
> viselkedésből visszafelé, nem a szabályból): `0x9d55` a tiszta fehér
> képpontokat színezi át, `0x9d18` véletlen zajt kever, `0x9d1e`-hez nincs
> átalakító, `0x9dbc`-t a távoli asztal észlelése állítja be. Részletek:
> **[picasa-megjelenitesi-modok.md](picasa-megjelenitesi-modok.md)**.

| parancs | azonosító | felirat |
|---|---|---|
| `ID_VIEW_16` | `0x9d18` | &16-bit (dithered) |
| `ID_VIEW_PROJECTOR` | `0x9d19` | &Projector Mode |
| `ID_VIEW_MAC` | `0x9d1a` | &Mac Gamma (1.6) |
| `ID_VIEW_SEPIA` | `0x9d1b` | &Sepia |
| `ID_VIEW_BW` | `0x9d1c` | &Black and White |
| `ID_VIEW_LINEAR` | `0x9d1d` | Linear &Gamma (2.2) |
| `ID_VIEW_NORMAL` | `0x9d1e` | &24-bit |
| `ID_VIEW_AUTO` | `0x9d1f` | &Automatic |
| `ID_VIEW_LCD` | `0x9d20` | &LCD Whitepoint |
| `ID_VIEW_OV` | `0x9d55` | &Show overflow pixels |
| `ID_VIEW_RDESK` | `0x9dbc` | &Remote Desktop |

A `0x9d18`–`0x9d20` **összefüggő kilences blokk**; az `OV` és az `RDESK`
külön tartományban van, tehát később kerültek be. A **rádió/kapcsoló
kérdés eldőlt**: mind a tizenegy **egyetlen kizáró rádiócsoport** tagja
(`0x00575670`), nincs köztük független kapcsoló.

*Bizonyítottsági fok: **megerősített** a menüépítő címére, a rekord-alakra
és a kinyert azonosítókra (diszasszemblálva + gépi kinyerés). A CSV
**gépi kinyerés eredménye**: ahol az azonosító üres, ott a minta eltért —
az ilyen tételt kézzel kell ellenőrizni (9 tétel a 177-ből... pontosan 32).*

---

## 8. A menürekord `+0x04` és `+0x08` mezője — gyorsbillentyű és ikon (2026-09-09, #2819)

**Bizalmi fok: megerősített.** A 7. szakasz a `+0x0a` (parancsazonosító)
mezőt mérte ki. Ez a szakasz a másik kettőt, a
`picasa-megjelenitesi-modok.md` **9.3** pontjának kérdésére: a
Megjelenítési mód almenüben mind a kettő nulla volt — **a többi menüben
is?**

### 8.1 A módszer és a KONTROLL

A menüépítő (`0x00559150`, 15 495 bájt) törzsét pásztáztam, memóriaplafon
alatt. A rekordokat nem sorrend, hanem **abszolút célcím** szerint
csoportosítottam — a 7. szakaszban leírt „egy rekorddal elcsúszik" csapda
így fel sem merül.

**A rekordot az azonosítja, hogy a `+0x0a` cellájába WORD méretű írás
történt** (ez a parancsazonosító mező alakja). Ez a szűrő a 207
nyers jelöltből **173** valódi rekordot hagy meg.

| mérőszám | érték |
|---|---|
| abszolút címre író utasítás a menüépítőben | 1469 |
| ebből `dword` / `word` | 1123 / 346 |
| nyers rekordkezdet-jelölt (`mov dword [X], eax`) | 207 |
| **valódi rekord** (word-írás a `+0x0a`-ra) | **173** |
| **KONTROLL: nem nulla parancsazonosító** | **162 / 173** |

A kontroll a 7. szakasz 140 ellenőrzött azonosítójával összevethető: a
pásztázó tehát nem üresre fut, a nulla-találatok valódiak.

### 8.2 ⭐ A válasz: VAN gyorsbillentyű és VAN ikon

| mező | nem nulla | a 173-ból |
|---|---|---|
| `+0x04` gyorsbillentyű-szöveg | **24** | 14 % |
| `+0x08` ikonszám (word) | **5** | 3 % |

⚠️ **Módszertani csapda, amibe menet közben beleestem:** a 24-ből
**négyet** nem közvetlen értékként ír a fordító, hanem `eax`-en át
(`mov dword ptr [rek+4], eax`, ahol az `eax`-be előbb a sztringcím
került). Az „olvasd ki az immediate-et" pásztázás ezt a négyet **nem
látja** — 20-at ad 24 helyett. A négy elveszett tétel épp a leghosszabb
billentyűnevek: `Delete` és háromszor `Enter`.

### 8.3 A teljes lista

> ⛔ **2026-09-10 (#2821): EZ A TÁBLA HIÁNYOS.** A „maszk" oszlopot az
> immediate értékre szűrő pásztázás állította elő, ezért **négy rekordnál
> nullát mutat 1 vagy 4 helyett** (a `di` regiszterből írt tételek). A
> javított értékek és a hiba oka a **8.7/c**-ben.

| rekord | parancs | angol felirat | gyorsbillentyű | `+0x08` maszk |
|---|---|---|---|---|
| `0x00d6d960` | `0x9d67` | `&New Album...` | `N` | — |
| `0x00d6d9b0` | `0x9c91` | `&Import From...` | `M` | — |
| `0x00d6da28` | `0x9d4f` | `&Rename...` | `F2` | 4 |
| `0x00d6dadc` | `0x9c99` | `&Locate on Disk` | `Enter` | — |
| `0x00d6daf0` | `0x9c9a` | `&Delete from Disk...` | `Delete` | 4 |
| `0x00d6db18` | `0xe107` | `&Print...` | `P` | — |
| `0x00d6db2c` | `0x9c97` | `&E-Mail...` | `E` | — |
| `0x00d6db80` | `0x9d39` | `Cu&t` | `X` | — |
| `0x00d6db94` | `0x9d3b` | `&Copy` | `C` | — |
| `0x00d6dba8` | `0x9d3c` | `&Paste` | `V` | — |
| `0x00d6dc48` | `0x9cb8` | `Select &All` | `A` | — |
| `0x00d6dc70` | `0x9c47` | `&Invert Selection` | `I` | — |
| `0x00d6dc84` | `0x9c90` | `C&lear Selection` | `D` | — |
| `0x00d6dfb4` | `0x9c9d` | `S&mall Thumbnails` | `1` | — |
| `0x00d6dfc8` | `0x9c9c` | `&Normal Thumbnails` | `2` | — |
| `0x00d6dfdc` | `0x9c8f` | `&Edit View` | `3` | — |
| `0x00d6e018` | `0x9d2c` | `&Tags` | `T` | — |
| `0x00d6e090` | `0x9ccc` | `Ti&meline` | `5` | — |
| `0x00d6e274` | `0x9c94` | `&Print Contact Sheet...` | `P` | 1 |
| `0x00d6e2b0` | `0x9cba` | `&Locate on Disk` | `Enter` | — |
| `0x00d6e318` | `0x9d4f` | `&Rename...` | `F2` | — |
| `0x00d6e354` | `0x9ca3` | `Rotate &Counterclockwise` | — | 1 |
| `0x00d6e498` | `0x9ca0` | `&View and Edit` | `3` | — |
| `0x00d6e560` | `0x9ca8` | `Propert&ies` | `Enter` | 6 |
| `0x00d6e9b8` | `0x9cac` | `&Help Contents and Index` | `F1` | — |

*(A `&Rename...` és a `&Locate on Disk` **kétszer** szerepel — a fő menüben
és egy helyi menüben —, és a két példány mezői eltérnek: a `&Rename...`
csak az egyik helyen kap ikont. A `Propert&ies` az egyetlen, amely
gyorsbillentyűt ÉS ikont is visel.)*

> ⛔ **2026-09-09, MÁSODIK MENET (#2821): A MEZŐ NEM IKON.** A `+0x08` a
> **gyorsítóbillentyű-módosítók bitmaszkja** (`Ctrl+` / `Shift+` / `Alt+`).
> Az olvasója megvan, és az alábbi 8.4 két „nulla olvasás" leletének is
> megvan a magyarázata. A helyes állapot a **8.5** szakaszban; az alábbi
> 8.4/8.4-b MÉRÉSEI állnak, a belőlük vont „ikon" olvasat NEM.

### 8.4 Mit jelentenek a számok az ikonmezőben — RÉSZBEN eldőlt (#2821)

A `+0x08` **word**, és mindössze három érték fordul elő: **1** (kétszer),
**4** (kétszer), **6** (egyszer).

**Amit a #2821 kimért — mindegyik állítás címmel:**

**(a) Egyetlen rekordmezőt sem olvas senki ABSZOLÚT címen.** A 173 rekord
mind a hat mezőjére, a teljes `.text`-en:

| mező | írás | olvasás |
|---|---|---|
| `+0x00` felirat | 346 | **0** |
| `+0x04` gyorsbillentyű | 177 | **0** |
| `+0x08` ikon | 173 | **0** |
| `+0x0a` parancsazonosító | 173 | **0** |
| `+0x0c` almenü-mutató | 173 | **0** |
| `+0x10` darabszám | 173 | **0** |

⇒ a fogyasztás **mutatón át** történik, nem globális címen. *(A `+0x0a`
sora egyben KONTROLL: a parancsazonosítót biztosan olvassa valaki, mégis
nulla — tehát a nulla nem a mező halottságát jelenti, hanem a keresési
alak korlátját.)*

**(b) A rekordtömb pontosan NYOLCSZOR hagyja el a menüépítőt mutatóként**
— a nyolc felső szintű menü tömbfeje:
`0x0055988d`, `0x00559c7c`, `0x0055acb8`, `0x0055b289`, `0x0055ba48`,
`0x0055be1f`, `0x0055ca04`, `0x0055cd89` (`push <tömbfej>` →
`call 0x005590c0`). Ezen felül **11** almenü-mutató kerül a `+0x0c`
mezőkbe (pl. `0x0055abca`: `mov dword ptr [0xd6e128], 0xd6dc98`).

**(c) A `CreateMenu` és a `SetMenu` importot PONTOSAN EGY függvény hívja:**
a menüépítő (`0x00559150`). A `CreatePopupMenu`-t a `0x005590c0` és a
`0x00a6aee0`. ⇒ a menüsor valódi Win32-menü, és ez a lánc építi.

**(d) ⭐ A mért úton NINCS bittérkép a Win32 felé.** Az egyetlen
`MENUITEMINFO`-kitöltő ezen a láncon a `0x00559050` (**3** hívóhely,
indextől független pásztázással: `0x00559122`, `0x005eaf9d`, `0x00a6af93`):

```
0x00559057  mov dword ptr [esp],     0x30    ; cbSize = 48 (MENUITEMINFOA)
0x0055905e  mov dword ptr [esp + 4], 0x15    ; ⭐ fMask
0x00559066  mov dword ptr [esp + 8], 0       ; fType = MFT_STRING
0x00559093  push 0xffff                      ; pozíció = a végére
0x005590a1  call dword ptr [0xd6958c]        ; InsertMenuItem
```

`fMask = 0x15` = `MIIM_STATE (0x01) | MIIM_SUBMENU (0x04) | MIIM_TYPE (0x10)`.
**Hiányzik belőle a `MIIM_BITMAP` (0x80) ÉS a `MIIM_CHECKMARKS` (0x08)** ⇒
ezen az úton a `+0x08` értéke **soha nem jut el a Win32-hez**.

**(e) A teljes `.text` WORD-olvasásai a `+8` eltoláson: 276 találat**, és
egyik sem menürekord (üzenetstruktúrák `[ebx+8]` = `wParam` alsó szava,
FPU-vezérlőszavak `fldcw`, és hasonlók). ⚠️ **Reguláris-kifejezés csapda:**
a `word ptr` **részsztringje** a `dword ptr`-nek — az első futásom ezért
adott 276 helyett több ezer hamis találatot. A minta `(?<![a-z])word ptr`.

### 8.4/b ⛔ Ami NEM dőlt el, és mi dönti el

A per-TÉTEL beszúrás útja nincs meg. A `0x00a6aee0` (378 bájt) **rekurzív**
menüjáró (`0x00a6af5c` önhívás), de **kétmezős** szerkezeten dolgozik
(`[ebp]`, `[ebp+4]`), nem a 20 bájtos rekordon ⇒ **valami átalakítja a
rekordtömböt** ebbe a szerkezetbe, és ezt az átalakítót nem találtam meg.

**A megszerzés útja:** a `0x005590c0` (140 bájt) a tömbfejet a
`0x00a6aee0`-nak adja át (`0x005590cd`–`0x005590e9`). Az átalakítás vagy
ott, vagy a `0x00a6aee0` általam nem kilistázott ágain történik. Ha az
átalakító a `+0x08`-at átveszi, ott derül ki, mit indexel; ha eldobja, a
mező **halott** — és akkor a 7. szakasz „ikon" elnevezése KÖVETKEZTETÉS
marad, nem mérés.

⚠️ **Amit ebből NEM szabad levonni:** hogy a menüben nincs ikon. Csak azt,
hogy a **mért úton** nem jut el bittérkép a Win32-hez. A Picasa saját
menürajzolót is használhat (a `0x00a6aee0` és a `SetMenuInfo` hívások erre
utalnak) — az a `+0x08`-at más úton is elérheti.

### 8.5 Amit ez a mérés NEM mond meg

A menüépítő törzsében 30 további `mov dword [X], eax` írás áll a Súgó
menü tömbjének tartományában (`0x00d6e9d8`…`0x00d6eab8`), amelyeknek
**nincs `+0x0a` word-írásuk**, tehát nem rekordkezdetek. Hogy pontosan mik
(a kinyert értékek a Súgó menü feliratai: `&Keyboard Shortcuts`,
`Picasa &Forums`, `Online &ReadMe`, `Release &Notes`, `Privacy Policy`,
`Terms`, `&Uninstalling Picasa`, `&Check for Updates`, `&About Picasa`),
azt **nem derítettem ki**. A 173-as rekordszám ezért **alsó korlát** a
Súgó menüre nézve.

---

## 8.5 ⭐ A `+0x08` NEM ikon — a gyorsítóbillentyű-módosítók maszkja (2026-09-09, #2821)

**Bizalmi fok: megerősített** a mező jelentésére; **feltételes** az egyes
bitek polaritására (ld. 8.5/d).

### 8.5/a Miért nem találta meg két korábbi pásztázás — két nevezhető ok

Az előző menet (8.4) mind a hat rekordmezőre **nulla olvasást** mért. A
magyarázat nem az volt, hogy a mezők halottak:

**(1) A bejáró ELTOLJA a bázismutatóját.** A `0x00a6aee0` (378 bájt) így
indul:

```
0x00a6aef9  mov ebp, dword ptr [esp + 0x24]   ; a rekordtömb feje
0x00a6aefd  add ebp, 0xc                      ; ⭐ +0x0c-vel ELŐRE tolja
```

Ettől a rekord mezői **negatív eltolással** jelennek meg:

| rekordmező | ahogy a bejáró látja |
|---|---|
| `+0x00` felirat | `[ebp - 0xc]` |
| `+0x04` gyorsbillentyű | `[ebp - 8]` |
| **`+0x08` maszk** | **`[ebp - 4]`** |
| `+0x0a` parancsazonosító | `[ebp - 2]` |
| `+0x0c` almenü-mutató | `[ebp]` |
| `+0x10` almenü-darabszám | `[ebp + 4]` |

A `[reg + 8]` / `[reg + 0xa]` alakra szűrő keresés ezért **elvileg sem**
találhatta meg. *(A `+0x0c`/`+0x10` eltolás azért kapta a nullát, mert
azokra a bejáró `[ebp]` / `[ebp+4]` alakban hivatkozik.)*

**(2) A mezőt BÁJTKÉNT olvassa, holott az építő SZÓKÉNT írja.**

```
0x00559438  mov   word ptr [0xd6da30], 4      ; az ÍRÓ: word
0x00a6b015  movzx ecx, byte ptr [ebp - 4]     ; az OLVASÓ: byte
```

A WORD-méretre szűrő keresés (8.4/e, 276 találat) ezért sem foghatta meg.

### 8.5/b A bejáró három ága — mérve

```
0x00a6af04  cmp dword ptr [ebp - 0xc], ebx    ; felirat == 0 ?
0x00a6af07  jne 0xa6af2e                      ;   nem → tovább
            ...  push 0xffff ; call 0xa6b120  ;   igen → ELVÁLASZTÓ
0x00a6af2e  cmp dword ptr [ebp], ebx          ; almenü-mutató == 0 ?
0x00a6af31  je  0xa6afc3                      ;   igen → LEVÉL (tétel)
0x00a6af5c  call 0xa6aee0                     ;   nem  → REKURZIÓ az almenüre
```

A **levél** ágon olvassa be mind a négy tartalmi mezőt:

```
0x00a6afc3  mov   edx, dword ptr [ebp - 8]    ; +0x04  gyorsbillentyű-szöveg
0x00a6afe8  mov   edx, dword ptr [ebp - 0xc]  ; +0x00  felirat
0x00a6b00d  movzx eax, word ptr [ebp - 2]     ; +0x0a  parancsazonosító
0x00a6b015  movzx ecx, byte ptr [ebp - 4]     ; ⭐ +0x08
0x00a6b02b  call  0xa6b250                    ; a tételbeszúró
```

### 8.5/c ⭐ Mit tesz a `0x00a6b250` a bájttal: BITENKÉNT szétszedi

A `0x00a6b250` (1068 bájt) a bájtot `bl`-ben kapja
(`0x00a6b25c  mov bl, byte ptr [esp + 0x38]`), majd bitenként bontja:

```
0x00a6b3bb  mov cl, bl ; shr cl, 2 ; not cl ; and cl, 1   ; a 2-es bit (0x04)
0x00a6b3c0  mov al, bl ; and al, 1                        ; a 0-as bit (0x01)
0x00a6b3c4  mov dl, bl ; and dl, 2                        ; az 1-es bit (0x02)
```

és három **bit-kapuzott** ág fűzi elé a módosító-előtagokat. A fordítási
kulcsok és az angol alapértelmezések **kiolvasva**:

| ág | teszt | fordítási kulcs | alapértelmezett |
|---|---|---|---|
| `0x00a6b575` | `test bl, 4` | `ytMenu::CtrlPrefix` (`0x00ce4a88`) | **`Ctrl+`** (`0x00ce4a80`) |
| `0x00a6b5a4` | `test bl, 1` | `ytMesu::ShiftPrefix` (`0x00ce4aa4`) | **`Shift+`** (`0x00ce4a9c`) |
| `0x00a6b5d3` | `test bl, 2` | `ytMenu::AltPrefix` (`0x00ce4ac0`) | **`Alt+`** (`0x00ce4ab8`) |

⇒ **A `+0x08` a gyorsítóbillentyű MÓDOSÍTÓ-MASZKJA, nem ikonszám.**
Bittérképet sehol nem tölt be belőle semmi — ez egyben megmagyarázza a
8.4/d leletét (`MENUITEMINFO.fMask = 0x15`, `MIIM_BITMAP` nélkül): nincs
is mit átadni.

**A megfigyelt értékek ezzel értelmet kapnak:** `1` = 0-as bit, `4` = 2-es
bit, `6` = 1-es + 2-es bit. Ez **bitkombináció, nem index** — és épp ezért
nem fordul elő `3`, `5` vagy `7`.

😀 **Melléklelet: elírás az EREDETIBEN.** A Shift-előtag kulcsa
`ytMesu::ShiftPrefix` — a másik kettő `ytMenu::…`. A Google elírta, és így
adta ki. Ha valaha átvesszük ezeket a kulcsokat, ezt **változatlanul** kell
átvenni, különben a fordítás nem talál.

### 8.5/d ⛔ Amit NEM állítok: az egyes bitek polaritása

A `bl` a hármas teszt ELŐTT **újraszámolódik** — nem a nyers mező:

```
0x00a6b451  mov bl, byte ptr [esp + 0x22] ; neg bl ; sbb bl, bl ; and ebx, 2
0x00a6b45c  cmp byte ptr [esp + 0x21], 0  ; setne dl ; or bl, dl
0x00a6b466  cmp byte ptr [esp + 0x20], 0  ; setne al ; sub al, 1 ; and eax, 4 ; or bl, al
```

A három veremzászló a `0x00a6b3ce`–`0x00a6b451` szakaszon áll össze,
amelyben **négy további hívás** is közbejön (`0xa6ade0`, `0x985990`,
`0xc080f0`, `0x5c2100`), tehát **más bemenet is beszól**. Ezt a szakaszt
nem olvastam végig.

**Kontroll-ellenőrzés a mai ismert Picasa-gyorsbillentyűkkel** — a
2-es bit (Ctrl elhagyása) négy ponton egyezik, egy ponton NEM:

| tétel | `+0x08` | mért gyorsbillentyű-szöveg | ismert viselkedés | egyezik? |
|---|---|---|---|---|
| `&New Album...` | 0 | `N` | Ctrl+N | ✅ |
| `&Rename...` | 4 | `F2` | F2 (Ctrl nélkül) | ✅ |
| `Propert&ies` | 6 | `Enter` | Alt+Enter | ✅ |
| `&Locate on Disk` | 0 | `Enter` | Ctrl+Enter | ✅ |
| `&Help Contents and Index` | **0** | `F1` | **F1** (Ctrl nélkül) | ❌ |

⇒ a „0 ⇒ Ctrl+" olvasat **egy ponton megdől**, tehát van még egy tényező.
**Ezért a bit↔módosító táblát NEM adom át szerződésként.**

> ⭐ **FELOLDVA a 8.6-ban (ugyanazon a napon):** a tényező nem a
> funkcióbillentyűk külön ága, hanem az, hogy a három bájt **lekérdezési
> kulcs** egy futásidejű gyorsítóbillentyű-táblába (`0x00a6ade0`), és a
> **tábla** adja a módosítókat. Statikus bit↔módosító tábla ezért nem
> létezik — a kérdés volt rosszul feltéve.

**A megszerzés útja:** a `0x00a6b3ce`–`0x00a6b451` szakasz végigolvasása,
benne a `0xa6ade0` és a `0x5c2100` hívás visszatérési értékének
azonosítása. Egy kör, olcsó.

### 8.5/e A 7. és a 8. szakasz HELYESBÍTÉSE

A 7. szakasz rekord-táblájában a `+0x08` mellett „ikon" áll, és a 8.
szakasz táblájának is „ikon" a fejléce. **Mindkettő téves elnevezés** —
KÖVETKEZTETÉS volt, nem mérés (a `+0x0a`-ra volt bizonyíték). A helyes név:
**gyorsítóbillentyű-módosítók bitmaszkja**. Ugyanez a téves elnevezés áll a
[picasa-megjelenitesi-modok.md](picasa-megjelenitesi-modok.md) 1. szakasz
rekord-táblájában is.

⇒ **Termékhatás:** az öt „ikonos" tétel NEM ikont visel. Ha valaki a
menüsorba ikont tett volna emiatt, az hibás lenne. A tényleges lelet az,
hogy ennek az öt tételnek **más a módosító-készlete**, mint a többinek.

---

## 8.6 A „melyik bit melyik módosító" kérdés ROSSZUL VAN FELTÉVE (2026-09-09, #2821)

**Bizalmi fok: megerősített** a szerkezetre; a kérdés átfogalmazásának oka
utasításszinten kiolvasva.

A 8.5 nyitva hagyta a bit↔módosító **polaritását**, mert a naiv olvasat a
`&Help Contents and Index` tételen megdőlt (maszk `0`, mégis `F1`
módosító nélkül). A hiányzó 133 bájt (`0x00a6b3ce`–`0x00a6b451`)
elolvasva a válasz: **nincs statikus bit↔módosító leképezés.**

### 8.6/a A három bájt egy KÉRDÉS, nem kódolás

A `0x00a6b250` a maszk három bitjét **három külön bájtba** teríti szét, és
mindegyikből **két példányt** készít:

```
0x00a6b3bb  mov cl, bl ; shr cl, 2 ; not cl ; and cl, 1   ; = NOT bit2
0x00a6b3c0  mov al, bl ; and al, 1                        ; = bit0
0x00a6b3c4  mov dl, bl ; and dl, 2                        ; = bit1
0x00a6b3ce  mov byte ptr [esp + 0x24], al   ; ⎫ TARTALÉK példány
0x00a6b3e4  mov byte ptr [esp + 0x23], cl   ; ⎬ (0x23…0x25)
0x00a6b3ec  mov byte ptr [esp + 0x25], dl   ; ⎭
0x00a6b3d2  mov byte ptr [esp + 0x21], al   ; ⎫ MUNKA-példány
0x00a6b3e8  mov byte ptr [esp + 0x20], cl   ; ⎬ (0x20…0x22)
0x00a6b3f0  mov byte ptr [esp + 0x22], dl   ; ⎭
0x00a6b3e0  lea esi, [esp + 0x20]           ; ⭐ a MUNKA-példány CÍME
0x00a6b3f8  call 0xa6ade0                   ; és átadja neki
```

⚠️ **A két példány maga a bizonyíték:** ha a hívott függvény nem
módosíthatná a bájtokat, nem kellene tartalék. Az `esi` **be- és kimenő**
paraméter.

### 8.6/b A hívott függvény TÁBLÁT KERES, nem dekódol

`0x00a6ade0` (162 bájt) egy tárolón iterál, és **soronként négy dolgot**
hasonlít össze:

```
0x00a6adee  mov ebp, dword ptr [eax + 8] ; shr ebp, 1   ; a sorok száma
0x00a6ae00  mov ecx, dword ptr [esi + 8]
0x00a6ae03  cmp dword ptr [eax + 0xc], ecx             ; kulcs egyezés?
0x00a6ae08  mov cl, byte ptr [eax + 3]                 ; a sor 1. bájtja
0x00a6ae0b  movsx ebx, byte ptr [esi]                  ; a KÉRDÉS 1. bájtja
0x00a6ae10  cmp cl, 0xff ; sete dl ; cmp ebx, edx      ; 0xFF = külön eset
0x00a6ae20  mov cl, byte ptr [eax + 4]  / [esi + 1]    ; a 2. bájt
0x00a6ae3a  mov cl, byte ptr [eax + 5]  / [esi + 2]    ; a 3. bájt
```

⇒ a három bájt **lekérdezési kulcs** egy futásidőben feltöltött
gyorsítóbillentyű-táblába, `0xFF` jelöléssel a soroldalon. A **tábla**
mondja meg a tényleges módosítókat, nem a maszk.

### 8.6/c A visszaszámolás IDENTITÁS — csak újraolvasás

A `0x00a6b451`–`0x00a6b473` blokk látszólag újrakódolja a maszkot. Kimérve
**bitre azonosat** ad vissza:

| utasítássor | mit ad |
|---|---|
| `bl = [esp+0x22]` (=bit1) `; neg bl ; sbb bl,bl ; and ebx,2` | bit1 → bit1 |
| `cmp [esp+0x21],0 ; setne dl ; or bl,dl` | bit0 → bit0 |
| `cmp [esp+0x20],0` (=NOT bit2) `; setne al ; sub al,1 ; and eax,4 ; or bl,al` | bit2 → bit2 (kettős tagadás) |

Vagyis a blokk **nem átalakít**, hanem a `0xa6ade0` által esetleg
**módosított** munka-példányt olvassa vissza maszkká.

### 8.6/d Az előtag-fűzés KAPUZOTT — nem minden tételen fut

```
0x00a6b3fd  test al, al
0x00a6b3ff  je 0xa6b475      ; ⭐ ha a táblakeresés NEM talált:
0x00a6b4a3      push 0xffff  ;    beszúrás előtag NÉLKÜL
0x00a6b4a9      call 0xa6b120
0x00a6b4ae      jmp 0xa6b657 ;    és kész
```

A `Ctrl+`/`Shift+`/`Alt+` hármas (8.5/c) tehát **csak akkor** fut le, ha a
táblakeresés talált sort. Ezen az ágon a `test bl, 4` / `1` / `2` hármas
`jne`-vel **átlép**, amikor a bit **be van állítva** — vagyis a bit ott már
azt jelenti, hogy az adott előtag **NEM kell**.

### 8.6/e ⛔ Ezért a 8.5/d kontroll-anomáliája NEM anomália

A `&Help Contents and Index` maszkja `0`, gyorsbillentyűje `F1` Ctrl
nélkül. Statikus leképezéssel ez ellentmondás; **táblakereséssel nem az**:
a Súgó parancsához tartozó tábla-sor a saját módosító-készletét adja, és a
maszk csak a kulcs egy része. Nem kell külön ág a funkcióbillentyűkhöz.

⇒ **A „melyik bit melyik módosító" kérdésre nem lehet táblát adni**, mert a
válasz futásidejű adattól függ. A helyes megfogalmazás: *melyik tábla, ki
tölti fel, és mi a sorformátuma.*

### 8.6/f Ami ebből MÉG hiányzik — pontos következő lépés

> ⭐ **MIND A HÁROM PONT ELDŐLT a 8.7-ben (2026-09-10):** a tábla a
> `runtime\shortcuts.xml` (a fájl megvan a kutatási anyagban), a sor három
> bájtja a `ctrl`/`shift`/`alt` attribútum, és a maszk leképezése
> **12/12** kontrollt kiállt. Az alábbi lépések már megtörténtek.

1. **A tábla tulajdonosa.** A `0xa6ade0` az `eax`-ben kapja a tárolót; a
   hívóban ez `0x00a6b3d6  mov eax, dword ptr [esp + 0x4c]`, tehát a
   `0x00a6b250` egyik paramétere. Vissza kell követni a `0x00a6b250`
   hívási láncán (`0x00a6b02b` a bejáróból).
2. **A kulcs.** `[esi + 8]` = a hívó `[esp + 0x28]`-a, amit a
   `0x00a6b3da  mov dword ptr [esp + 0x28], esi` állít be az AKKORI `esi`
   értékéből. Ezt egy verem-visszakövetés adja meg.
3. **A sorformátum.** A `0xa6ade0` a `+0x3`, `+0x4`, `+0x5` bájtokat és a
   `+0xc` dwordöt olvassa ⇒ a sor legalább 16 bájt; a lépést a
   `shr ebp, 1` és az iteráció adja meg.

⚠️ **Amit NEM állítok:** hogy a maszk bitjei „Ctrl/Shift/Alt"-ot jelentenek.
Csak azt, hogy a **kereső hármas** ilyen sorrendben teszteli őket, ha a
keresés talált. A jelentést a tábla adja.

---

## 8.7 ⭐ MEGVAN: a tábla a `runtime\shortcuts.xml`, és a maszk leképezése 12/12 (2026-09-10, #2821)

**Bizalmi fok: megerősített.** A 8.6 három nyitott pontja mind eldőlt, és a
levezetett leképezés **12/12** független ellenőrzést kiállt.

### 8.7/a A tábla: `runtime\shortcuts.xml`

A tárolót a menüépítő **verem-lokálisa** hordozza, és a konstruktora
nevezi meg a fájlt:

```
0x00559150  sub esp, 0x14
0x00559155  xor ebx, ebx                     ; ⭐ ebx = 0 innentől
0x00559158  lea ecx, [esp + 0x10]            ; a tároló CÍME
0x0055915c  mov dword ptr [esp + 0x10], ebx  ; 0
0x00559160  mov dword ptr [esp + 0x14], ebx  ; 0
0x00559164  call 0x9a16b0                    ; a konstruktor…
     └─ 0x009a16c1  push 0xc8c3d4            ; …és a sztring: 'runtime\shortcuts.xml'
```

⭐ **A fájl MEGVAN a kutatási anyagban:**
`referencia/dekompilalt-617/SHORTCUTS.xml` — 149 sor, 4627 bájt, **48
tétel**. Sorformátuma pontosan az, amit a kereső olvas:

```xml
<!-- Rename -->
<item srckey="VK_F2" dstkey="" ctrl="0" shift="0" alt="0">
```

⇒ a `0x00a6ade0` három összehasonlított bájtja (`[eax+3]`, `[eax+4]`,
`[eax+5]`) a **`ctrl`**, **`shift`**, **`alt`** attribútum, a `+0xc` dword
pedig a kulcs.

### 8.7/b A tároló ÚTJA — kilenc érintés az egész építőben

A `[esp+0x10]` lokálist a 15 495 bájtos építő **pontosan kilencszer**
érinti: egyszer a konstrukciónál, és **nyolcszor** a `call 0x005590c0`
harmadik argumentumaként — **minden felső szintű menünél ugyanazt**. Más
metódust nem hív rá, és többet nem is ír bele.

A nyolc hívás második argumentuma a menü tételszáma:

| menü tömbfeje | tételszám |
|---|---|
| `0xd6d960` | 0x1b = **27** |
| `0xd6db80` | 0x0e = **14** |
| `0xd6dfa0` | 0x17 = **23** |
| `0xd6e1c0` | 0x11 = **17** |
| `0xd6e498` | 0x0b = **11** |
| `0xd6e5b0` | 0x0a = **10** |
| `0xd6e850` | 0x12 = **18** |
| `0xd6e9b8` | 0x0d = **13** |
| **összesen** | **133** |

*(Kereszt-ellenőrzés: a 8.1 szerint 173 rekord van; 173 − 133 = 40 az
almenükben, és 11 almenü-mutató áll a `+0x0c` mezőkben — összefér.)*

### 8.7/c ⛔ ÖNHELYESBÍTÉS: a 8.3 „maszk" oszlopa HIÁNYOS VOLT

A 8.3 táblát az **immediate** értékre szűrő pásztázás állította elő. Újramérve,
a `+0x08` mező forrása szerint:

| a `+0x08` írásának forrása | rekord |
|---|---|
| közvetlen érték (`mov word ptr […], 4`) | **5** |
| `bx` regiszter | **164** |
| **`di` regiszter** | **4** |
| írás nélkül | 0 |

A `bx` **bizonyítottan nulla** (`0x00559155 xor ebx, ebx`, és a builderben
nincs több `ebx`-írás). A `di` **NEM nulla** — élő konstans, amely három
ponton változik:

```
0x00559184  mov edi, 1
0x0055a335  mov edi, 5
0x0055af40  mov edi, 4
0x0055b25a  mov edi, 4
```

⇒ a `di`-ből író **négy** rekord maszkja nem 0, hanem a soronkénti `edi`:

| rekord | felirat | `edi` az írás pillanatában | maszk |
|---|---|---|---|
| `0x00d6d9ec` | `&Open File(s) in an Editor` | 1 | **1** |
| `0x00d6dab4` | `Export Pi&cture to Folder...` | 1 | **1** |
| `0x00d6e318` | `&Rename...` (második példány) | 4 | **4** |
| `0x00d6e9b8` | `&Help Contents and Index` | 4 | **4** |

**A 8.5/d „anomáliája" ezzel megszűnt:** a Súgó maszkja nem 0, hanem **4**.
A hibát az én pásztázóm okozta, nem a bináris.

### 8.7/d ⭐ A LEKÉPEZÉS — és a 12/12 kontroll

| maszk-bit | jelentés |
|---|---|
| **bit0 (1)** | `shift="1"` |
| **bit1 (2)** | `alt="1"` |
| **bit2 (4)** | **`ctrl="0"`** — FORDÍTOTT: a bit azt jelenti, hogy **NINCS** Ctrl |

A fordítást a kód is kimondja: a `0x00a6b3bb` a 2-es bitet
`shr cl, 2` után **`not cl`**-lel fordítja meg, a 0-as és az 1-es bitet nem.
Tervezési okból: a Ctrl a gyakori eset, ezért a `0` jelenti a „van Ctrl"-t.

**Kontroll a `SHORTCUTS.xml` ellen** (a mért maszk vs. a levezetett szabály):

| XML tétel | `srckey` | ctrl/shift/alt | mért maszk | levezetett | egyezik |
|---|---|---|---|---|---|
| New label | `N` | 1/0/0 | 0 | 0 | ✅ |
| Import from | `M` | 1/0/0 | 0 | 0 | ✅ |
| Open File in Editor | `O` | 1/1/0 | 1 | 1 | ✅ |
| Rename | `VK_F2` | 0/0/0 | 4 | 4 | ✅ |
| Export Picture to Folder | `S` | 1/1/0 | 1 | 1 | ✅ |
| Locate on Disk | `VK_RETURN` | 1/0/0 | 0 | 0 | ✅ |
| Delete from Disk | `VK_DELETE` | 0/0/0 | 4 | 4 | ✅ |
| Invert Selection | `I` | 1/0/0 | 0 | 0 | ✅ |
| Timeline | `5` | 1/0/0 | 0 | 0 | ✅ |
| Print Contact Sheet | `P` | 1/1/0 | 1 | 1 | ✅ |
| Properties | `VK_RETURN` | 0/0/1 | 6 | 6 | ✅ |
| Help Contents and Index | `VK_F1` | 0/0/0 | 4 | 4 | ✅ |

**EGYEZÉS: 12 / 12.** *(A 48 XML-tételből 12-nek van a menüben mért maszkja;
a többi tétel nem menüből érhető el, vagy a maszkja `bx` = 0, ami a
„Ctrl, Shift és Alt nélkül nincs" alapesetet adja.)*

### 8.7/e Amit a fejlesztésnek ad

1. **A gyorsbillentyűk igazságforrása egy ADATFÁJL**, nem a kód:
   `runtime\shortcuts.xml`, 48 tétel, `srckey`/`dstkey`/`ctrl`/`shift`/`alt`
   attribútumokkal. **Megvan nálunk**, tehát a teljes készlet átvehető.
2. A menürekord `+0x08` mezője **nem a billentyűt írja le**, csak a
   módosítókat, és a Ctrl bitje **fordított**. Aki a maszkot közvetlenül
   olvassa be, a Ctrl-t az ellenkezőjére kapja.
3. A `dstkey` attribútum szerepe **NINCS megfejtve** — mindenhol üres a
   mintában. Ez marad nyitva.

### 8.7/f Ami nyitva marad

- **A `dstkey` üres attribútum jelentése** (48/48 tételen `""`). A
  megszerzés útja: a `0x009a16b0` XML-elemzőjében a `dstkey` kulcsra
  hivatkozó ág.
- **A `keymap id="0"`** — van-e több keymap, és mi választ közülük? A
  mintában egyetlen `keymap` van.

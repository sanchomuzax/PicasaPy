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
mov   word  ptr [rek+0x08], bx           ; ikon
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

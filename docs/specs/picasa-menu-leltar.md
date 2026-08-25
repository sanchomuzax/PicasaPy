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

## 2. Lefedettség — 150/189 (79%)

Mérés: a magyar (vagy angol) feliratot keresve a
`src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml` + `picasapy_hu.ts`
párosban.

| menü | összes | nálunk | hiányzik |
|---|---:|---:|---:|
| `eMenuTools` | 38 | 20 | **18** |
| `eMenuView` | 46 | 37 | **9** |
| `eMenuFile` | 21 | 19 | 2 |
| `eMenuHelp` | 11 | 10 | 1 |
| `eMenuCreateMovie` | 3 | 2 | 1 |
| `eMenuPicture` · `eMenuEdit` · `eMenuLabelFolder` · `eMenuCreate` | 54 | **54** | **0** |
| Mac-változatok | 9 | 2 | 7 *(hatókörön kívül)* |
| **összesen** | **189** | **150** | **39** |

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

### A kinyert térkép: **177 tétel, 145 parancsazonosítóval**

> 🔴 **A gépi azonosító-kinyerés MEGBUKOTT — az oszlop eltávolítva
> (2026-08-25, ugyanaznap).**
>
> A menüépítőben a **felirat a KÖVETKEZŐ rekord `+0x00` mezőjébe íródik**, a
> fordítás lekérése (`call 0x9ae560`) után — ezért a kulcs↔azonosító párosítás
> kétséges volt. **Kontroll-méréssel eldöntve, független horgonnyal:**
>
> A `picasa-konyvtar-eszkoztar-viselkedes.md` egy korábbi, más úton végzett
> kör alapján rögzíti, hogy `0x9db6` = **`ID_VIEW_FOLDERS`** (&Flat Folder
> View), `0x9db8` = `ID_VIEW_WATCHED`, `0x9db9` = `ID_VIEW_ALL`. A gépi
> kinyerésem viszont `0x9db6`-ra **`ID_VIEW_ALL`**-t mondott, `0x9db9`-re
> pedig `ID_VIEWBYDATE`-et — miközben `ID_VIEW_MYPICTURES` = `0x9db7`
> **helyes** volt.
>
> ⇒ **A tévedés SZABÁLYTALAN**, nem egyenletes egy-rekordos elcsúszás, tehát
> nem javítható egy eltolással. **Egy félig hibás azonosító-térkép rosszabb,
> mint semmilyen**, mert használat közben bizalmat kelt — ezért az oszlopot
> **kivettem** a CSV-ből.
>
> **Ami MEGMARADT és megbízható:** `menu`, `parancs`, `felirat_en`,
> `felirat_hu` — a névterek, a parancsnevek és a feliratok a szövegtárból
> és a menüépítő sztringjeiből jönnek, azokat a kontroll nem érintette.
>
> **Ha valakinek kell egy konkrét parancsazonosító:** keresse ki
> egyenként, a kulcs sztringcímétől indulva a menüépítőben
> (`0x00559150`), és **ellenőrizze független horgonnyal** — pontosan úgy,
> ahogy ez a bekezdés készült.

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

| parancs | azonosító | felirat |
|---|---|---|
| `ID_VIEW_RDESK` | `0x9d18` | &Remote Desktop |
| `ID_VIEW_OV` | `0x9d19` | &Show overflow pixels |
| `ID_VIEW_LINEAR` | `0x9d1a` | Linear &Gamma (2.2) |
| `ID_VIEW_16` | `0x9d1e` | &16-bit (dithered) |
| `ID_VIEW_NORMAL` | `0x9d1f` | &24-bit |
| `ID_VIEW_PROJECTOR` | `0x9d20` | &Projector Mode |
| `ID_VIEW_MAC` | `0x9d55` | &Mac Gamma (1.6) |
| `ID_VIEW_LCD` | `0x9dbc` | &LCD Whitepoint |
| `ID_VIEW_FOLDERS` | *(a kinyerés nem adta)* | &Flat Folder View |

A `0x9d18`–`0x9d20` **összefüggő blokk** — erős jel arra, hogy ezek egy
csoportot alkotnak; a `MAC` és az `LCD` külön tartományban van, tehát
később kerültek be. *(A rádió/kapcsoló besorolás **még nincs kimérve** —
ez a #1409 tárgya.)*

*Bizonyítottsági fok: **megerősített** a menüépítő címére, a rekord-alakra
és a kinyert azonosítókra (diszasszemblálva + gépi kinyerés). A CSV
**gépi kinyerés eredménye**: ahol az azonosító üres, ott a minta eltért —
az ilyen tételt kézzel kell ellenőrizni (9 tétel a 177-ből... pontosan 32).*

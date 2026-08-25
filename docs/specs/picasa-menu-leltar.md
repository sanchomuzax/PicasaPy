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

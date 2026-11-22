# A bal hasáb csoportfejlécei: "Updated <hónap> <év>" és az első sor fölötti fejléc hiánya (#7351)

Issue: #7351 (J8 és J9 a `paritas-folyamat-7326.md` jegyleírásából). Eredeti: Picasa 3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`, kép-alap `0x00400000`.

Módszer: statikus olvasás (capstone a `pe_dis.py`/`picasa_dis.py`-n át, bináris-index, a `tagkereso.py` három tagoffszetre: `0x4e8`, `0xec`, `0x3dc`), két korábbi Ghidra-kimenet újraolvasása (`referencia/ghidra/2026-10-21-idorend-25.txt`, `2026-11-11-6532-colab-004a0720-hivok.txt`) és a szövegtár (`referencia/stringres-en-hu.tsv`). **A Colab-felvételeket (job-802, job-806, tulajdonosi 150933) ebben a körben nem nyitottam meg:** a képek helyben nincsenek (a `/tmp/colab-felmeres` csak a job-651..657 mappákat tartalmazza), a GitHub-hozzáférés pedig ebben a körben tiltott. A lap a felvételek tartalmát a jegy leírásából veszi, és megmondja, hol ellenőrzi őket a bináris, és hol nem.

## 0. Cím-atlasz (kötelező blokk; a szakaszok felsorolását a hely miatt rövidítettem, a `0x…` címek és a találat-lapok a mérő kimenetéből valók)

```
🗺️ Atlasz (`cim-atlasz.tsv`, `atlasz_keres.py`):
- `0x004b3770` (függvény 0x004b3770-0x004b418c): paritas-ellenorzes-archiv-1.md §39; picasa-idorend-bemutato-kutatas.md; picasa-idorend-viselkedes.md §4; picasa-konyvtar-eszkoztar-viselkedes.md §31, §33; ui-audit-mainwindow.md §81
- `0x004b29d0` (függvény 0x004b29d0-0x004b2d49): paritas-ellenorzes-archiv-2.md §33, §34, §39; picasa-idorend-bemutato-kutatas.md; picasa-idorend-viselkedes.md §1, §2, §4
- `0x004b8470` (függvény 0x004b8470-0x004b86c2): paritas-ellenorzes-archiv-2.md §34, §37, §39; picasa-idorend-viselkedes.md §1, §2, §4; ui-audit-mainwindow.md §82
- `0x004b2e10` (függvény 0x004b2e10-0x004b3499): picasa-idorend-viselkedes.md §4; ui-audit-mainwindow.md §81
- `0x00450bd0` (függvény 0x00450bd0-0x004512c7): picasa-idorend-viselkedes.md §4; picasa-menu-parancsok-viselkedes.md §342 (67.2, a negyedik mód)
- `0x0098c780` (függvény 0x0098c780-0x0098c8e8): paritas-ellenorzes.md §111, §114; picasa-idorend-bemutato-kutatas.md
- `0x0098b9e0` (függvény 0x0098b9e0-0x0098ba30): picasa-idorend-bemutato-kutatas.md
```

(Az atlasz a függvényeket már említi, de **egyik lap sem írja le a fejléc-gyártó viselkedését**: a `0x004b3770`-et a korábbi körök "Updated albumépítőnek" vették, lásd a 8. szakasz helyesbítését.)

## Következtetés

**A két jelenség egyetlen függvényből jön: a `0x004b3770`-ből (2588 bájt), a bal hasáb sorépítőjének csoportfejléc-gyártójából.** A `0x004b29d0` hívja minden forrássorra (`0x004b2a87`), közvetlenül az elemsor (`0x004b2ab4`, típus 1) beszúrása ELŐTT, és a lista rendezési módja (`[L+0xd8]`, a `datesort` értéke) dönti el, mit gyárt:

- **0 (dátum):** évszám-fejléc, ha az előző sor éve más. A fejléc szövege a `"%ld"` formátumú év (`0xc82fd8`).
- **1 (legutóbbi változtatás):** `Updated <hónap> <év>` fejléc, ha az előző sor `Hónap Év` szövege (`ytDateTime::Format2`, `0x0098c780`) más, ÉS az év nagyobb, mint 1900. A fejléc a szövegtár `CAlbumBuilder::updated` kulcsa ("Updated ", magyarul **"Frissítve "**) és ugyanannak a dátumnak a `Format2` szövege összefűzve.
- **2 (név), 5 (méret):** nincs fejléc (a függvény a `0x004b3a17`-nél, `cmp ecx, 1; jne`, kilép). Ez egyezik a jegy állításával.
- **3:** külön, útvonal-alapú ág (a `0x004b3cd7`-nél, `cmp [L+0xd8], 3`); a jegynek nem tárgya.

**J9 (az első sor fölött nincs fejléc): bináris-igazolt, mindkét módra.** A builder előző-év mezője (`+8`) minden újraépítés elején `-1` (`0x004b84df`), és minden kategóriaváltáskor visszaáll `-1`-re (`0x004b346f`); a fejléc-gyártó `+8 == -1` esetén a fejléc-ágat kihagyja (`0x004b3802`-`0x004b3809`), és csak az állapotot (előző év, előző szöveg) menti. Tehát **nem "a lista első sora", hanem "egy kategória (itt: Mappák) első sora" fölött nincs fejléc**, és ez a fejléc minden más oka fölött áll.

**J8 két kérdésére a válasz:** (1) a magyar sablon a szövegtárból **`Frissítve `** (`stringres-en-hu.tsv` 188. sor, `CAlbumBuilder::updated`); az angol kulcs `CAlbumBuilder::updated` (`0x004b3ab3`, alapérték `"Updated "`, `0xc83538`). (2) **Az azonos hónapra eső két mappa EGY csoportot kap:** a csoportkulcs a `Format2` sztring, és az előző sorral bájtról bájtra egyező szöveg nem kap új fejlécet (`0x004b3a48`-`0x004b3aa1`). A hónap szemcséje tehát nem feltevés, hanem a kód.

**Ami nincs lezárva (5 blokkolt tétel, lásd a 7. szakaszt):** a hónap-év megjelenítése a Windows regionális beállításától függ (magyar rendszeren a rendszer saját "év. hónap" alakja jöhet, nem a `%s %d`); a dátum nélküli sor nem-első helyen; a "változtatás dátuma" pontos mezője (fotódátum vs fájlidő); a `0x004b34a0` nevesített-dátumsor forrása; két kapufüggvény jelentése.

## 1. Mit ad ma a PicasaPy (mérve, `research/7351-claude`, `f0175ae18`)

- `src/picasapy/app/folder_list_model.py:200-201`: `if sort_mode in ("date", "changed"):` / `lathato = _with_year_separators(rows)`. A `changed` mód is a mappa dátumának **évszámát** írja.
- `folder_list_model.py:184-193`: a `rows` generátor a `folders` sorát `(name, path, count, date, _size, _change, offline, hidden, unread)` alakban bontja, és a `_change` mezőt **eldobja**. A `changed` módú fejlécnek a változtatási idő kell, tehát ezt a generátort bővíteni kell. (A jegy "az `rows` felépítésekor már rendelkezésre áll" mondata a `folders` listára igaz, a `rows`-ra nem.)
- A `_change` értéke: `sorted_folder_rows`, `COALESCE(MAX(p.mtime_ns), 0)` (`folder_list_model.py:52`), azaz a mappa képeinek legnagyobb fájlideje, nanoszekundumban.
- `src/picasapy/app/model_helpers.py:139-172` (`_with_year_separators`): `last_year = None` (:164) és `if year and year != last_year:` / `rows.append(("year", year, "", 0, False, False))` (:168-169) miatt az első dátumos sor fölé is fejléc kerül. A homogén-év ág (:156-161: `len(distinct_years) <= 1 and all(years)`) csak akkor hagyja el a fejléceket, ha minden mappa ugyanabba az évbe esik. A `_folder_year` (:175-180) a dátum híján a név `YYYY` előtagját használja.
- A sor típusa `"year"`; a QML `FolderPaneTreeRow.qml:53` és `:69` a `"year"` és `"hidden"` sorokat nem kattinthatónak kezeli.
- Tesztek, amelyek a mai viselkedést rögzítik: `tests/app/test_folder_sort_split.py:197-200` (`test_changed_view_keeps_them`: `"year" in kinds`), `tests/app/test_models.py:55` (az első sor `"year"`), `:85-133` (sorrend-assertek), `:165-192` (homogén-év: nincs fejléc).
- Fordítás: a `picasapy_hu.ts`-ben nincs `Updated ` / `Frissítve ` sor (grep: csak a `Recently Updated` album és annak menüje találat). A fejléc-előtagnak új, fordítható szöveg kell.

## 2. A fejléc-gyártó helye és állapota

| lépés | cím | mit csinál |
|---|---|---|
| bejárás | `0x004b8470` (ciklus `0x004b85a0`-`0x004b85da`, hívás `0x004b85c8`) | a forrássorok (`[L+0x148]` index-tömb; hogy ez a rendezés eredménye, a #5401 U10 nem zárta le, a hasáb felvételei szerint viszont a rendezett sorrend) minden elemére meghívja a `0x004b29d0`-t |
| builder-állapot | `0x004b84d4`-`0x004b852f` (a veremben, bázis `esp+0x18`) | `+0x00 = -1`, `+0x04 = -1`, **`+0x08 = -1` (előző év)**, `+0x0c = 0` (számláló), `+0x10 = -1`, `+0x14 = 0`, `+0x18 = -1`, **`+0x1c = 0` (bájt)**, **`+0x20 = 0` (előző hónap-év szöveg)**, `+0x48 = L`, `+0x4c = [L+0xc4]`, `+0x50 = [L+0xec]`, `+0x54 = 0` |
| soronként | `0x004b29d0` | kategóriaváltáskor `0x004b2e10` (`0x004b2a40`); majd `0x004b3770` (`0x004b2a87`); végül az elemsor `0x004a0720(1, …)` (`0x004b2ab4`) |
| kategória-fejléc | `0x004b2e10` | típus-3 sort ír (`0x004b2f8c`), a `super:` előtagot használó ágban `+0x1c = 1` (`0x004b2f96`), nem-`super:` ágon `+0x1c = 0` (`0x004b31fd`); **mindig `+0x08 = -1`-re állít** (`0x004b346f`) |
| fejléc-gyártó | `0x004b3770` | lásd lent |
| sor-rekord | `0x004a0720` (184 bájt, 0x38 bájtos rekord) | `+0x0c` a címke, `+0x14` az érték (itt: az év), `+0x30` a **típus** (1 elem, 2 csoportfejléc, 3 kategória-fejléc) |
| dátum-formázó | `0x0098c780` (`ytDateTime::Format2`) | "Hónap Év" szöveg |
| év-kinyerő | `0x0098b9e0` | a dátum éve; érvénytelen dátumra 0 |

**A `0x004b3770` döntési fája** (a `0x004b3770`-`0x004b4186` asm és a Ghidra-dekompiláció egyezik):

```
dt     = (L.mod == 1) ? valtoztatas_datuma(sor)          # 0x00450bd0 (0x004b37b6)
                      : mappa_datuma(sor)                # [[L+0xc4]+0x48] vt+0x20 (0x004b37cb)
nevesített_sor(b, dt)                                    # 0x004b34a0 (0x004b37dc), lásd 7/N4
szoveg = Format2(dt)                                     # 0x0098c780 (0x004b37ea)
ev     = ev_of(dt)                                       # 0x0098b9e0 (0x004b37f4)
ha b.elozo_ev == -1                       -> ÁLLAPOT     # 0x004b3802-0x004b3809
ha b.elozo_szoveg NULL vagy üres          -> ÁLLAPOT     # 0x004b380f-0x004b382a
ha L.mod == 0 és b.elozo_ev != ev és b.flag1c == 0:      # 0x004b3833-0x004b384c
      fejléc(típus 2, érték ev, címke "%ld"(ev))         # 0x004b3857-0x004b3886
különben ha L.mod == 1 és szoveg != b.elozo_szoveg és ev > 1900:
      # 0x004b3a17-0x004b3aad (a 0x76c = 1900 a `cmp ebx, 0x76c; jbe`)
      előtag = tr("CAlbumBuilder::updated", "Updated ")  # 0x004b3ab3-0x004b3abd
      ha az előtag nem ' '-ra végződik: hozzáfűz ' '     # 0x004b3ae1-0x004b3b0a
      címke = előtag + Format2(dt)                       # 0x004b3b0f-0x004b3b30
      fejléc(típus 2, érték ev, címke)                   # 0x004b3b3e-0x004b3b50
ÁLLAPOT: b.elozo_szoveg = szoveg; b.elozo_ev = ev        # 0x004b412e-0x004b416a
```

A megfordítás (`[L+0x165]`, `albumlistflip`) a gyártóban **nem szerepel**: a fejléc a rendezett (és adott esetben megfordított) forrássorrend szerinti "előző sorhoz" képest készül, vagyis a fejléc mindig a csoport első megjelenített sora fölé kerül, megfordítva is.

**A dátum-formázó (`0x0098c780`, `ytDateTime::Format2`):** az init (`0x0098af20`..`0x0098b311`) a `GetLocaleInfoA(0x400, 0x22 = LOCALE_ILDATE, …)` első karakterét a `0xd49f79` jelzőbe teszi (`0x0098b2f8`-`0x0098b30b`: ha `'0'`, a jelző 0). **`ILDATE == '0'` (hónap-nap-év sorrend, pl. `en-US`): a "tartalék" ág**, `0x0098c837`: a `ytDateTime::Format2` szövegtár-kulcs (`%1$s %2$d`, angolul és magyarul azonos) a hónapnévvel (a `0xd337ec + 4*hónap` tábla, 1-alapú; a nevek a szövegtárból jönnek: `January`..`December`) és az évvel. **Más sorrendnél (`'1'` vagy `'2'`)** a gép saját formátuma jön: `GetDateFormatA(0x400, 8 = DATE_YEARMONTH, …)` (`0x0098c7e6`). Az angol Wine-felvétel ("Updated November 2014") az első ágat mutatja.

## 3. Mért tények cím szerint

| állítás | bizonyíték | fok |
|---|---|---|
| a fejléc-gyártó a `0x004b3770`; a `0x004b29d0` hívja soronként, az elemsor előtt | `0x004b2a87` (hívás), `0x004b2ab4` (elemsor, típus 1); Ghidra `idorend-25.txt`, `FUN_004b29d0` | megerősített |
| az első sor fölött nincs fejléc | `0x004b84df` (`+8 = -1`), `0x004b3802`-`0x004b3809` (`cmp eax, -1; je 0x4b3cd7`), `0x004b412e`-`0x004b416a` (állapotmentés) | megerősített |
| kategóriánként újraindul (az első Mappák-sor és minden más kategória első sora) | `0x004b346f` (`mov [ebx+8], -1`, a `0x004b2e10` záró lépése), hívás `0x004b2a40` | megerősített |
| dátum-módban az évszám változása hoz fejlécet, szövege az év | `0x004b3841` (`cmp eax, ebx`), `0x004b3857`-`0x004b385d` (`push 0xc82fd8`, ami `"%ld"`), `0x004b3886` (típus 2, érték EBX = év) | megerősített |
| "legutóbbi változtatás" módban a csoportkulcs a Format2 sztring | `0x004b3a48`-`0x004b3a6c` (bájtpáros-összehasonlítás), `0x004b3a9c`-`0x004b3aa1` (`sete al; test al, al; jne 0x4b3cd7`: egyezésnél nincs fejléc) | megerősített (statikus); futásidejű mérés NINCS MEG (7/N3 melléklet) |
| 1900-nál nem nagyobb évnél nincs "Updated" fejléc | `0x004b3aa7` (`cmp ebx, 0x76c`), `0x004b3aad` (`jbe 0x4b3cd7`) | megerősített |
| a fejléc szövege: előtag + Format2 | `0x004b3ab3`-`0x004b3b30` (kulcs `CAlbumBuilder::updated`, alapérték `"Updated "`, `0xc83538`; szóköz-pótlás `0x004b3b03`) | megerősített |
| magyar előtag `Frissítve ` | `stringres-en-hu.tsv` 188. sor: `CAlbumBuilder::updated`, `Updated `, `Frissítve ` | megerősített |
| név- és méret-módban nincs fejléc | `0x004b3a17` (`cmp ecx, 1; jne 0x4b3cd7`), a 0-s ág `0x004b383b` (`jne 0x4b3a17`) | megerősített |
| az `IDS_LISTUPDATED` ("Updated ") NEM ennek a fejlécnek a forrása | a `CAlbumState` konstruktora (`0x004a1560`, `0x004a16d0`-`0x004a16e6`) a `+0x3dc` tagba teszi; a `[reg+0x3dc]` alakú pásztázásban a CAlbumState-körben a konstruktoron kívül csak a `0x004a3790` érinti (`lea edi, [esi+0x3dc]`, `0x004a3a08`, a szabadítás); a fejléc-gyártó a `CAlbumBuilder::updated` kulcsot használja | erős (a pásztázás nem zárja ki a leszármazott osztályokat) |
| a "változtatás dátuma" egy kép-rekord 64 bites párjának maximuma, OLE-dátumra alakítva | `0x00450bd0`: `0x00450f1c`-`0x00450f36` (64 bites `max`, `[rec+8]` fent, `[rec+4]` lent), `0x00450f67` (`0x0098b650`, FILETIME -> dátum), eredmény `[out]` (`0x00450f73`) | erős; a pár **jelentése** (fotódátum vs fájlidő) NINCS MEG (7/N3) |

## 4. Eredeti | Nálunk | Teendő

| pont | Eredeti (bináris) | Nálunk (mért, 1. szakasz) | Teendő |
|---|---|---|---|
| fejléc `changed` módban | `Updated <hónap> <év>`, csoportkulcs a hónap-év szöveg, csak ha az év > 1900 | a mappa dátumának éve (`folder_list_model.py:200-201`, `_with_year_separators`) | új `_with_month_separators`-szerű lépés a `changed` ágra; a `rows` generátor vigye tovább a `_change`-et |
| fejléc `date` módban | az év, ha az előző sor éve más | ugyanez (`model_helpers.py:168-169`), az első sorra is | az első sor fölött ne legyen |
| első sor | soha nincs fejléc (kategóriánként újraindul) | van (`last_year = None`) | `last_year` kezdőértéke az első sor éve |
| "homogén-év" ág | nincs külön ág: a szabály következménye | van (`model_helpers.py:156-161`) | kivehető; a `test_no_year_row_when_all_folders_share_one_year` változatlanul igaz marad |
| név, méret mód | nincs fejléc | nincs fejléc (`folder_list_model.py:202-206`) | változatlan |
| megfordítás | nincs külön ág | a rendezés után alkalmazódik | változatlan |
| magyar előtag | `Frissítve ` (szövegtár) | nincs a `.ts`-ben | új fordítható szöveg: `Updated ` / `Frissítve ` (a záró szóközzel együtt, vagy külön szóköz-pótlással) |
| hónap-év szövege | EN: `November 2014` (`%s %d`, a hónapnév a szövegtárból); a magyar Windows saját alakja `DATE_YEARMONTH` | nincs | lásd a javasolt döntést a 5. szakaszban |

## 5. Fejlesztői jegytörzsek (a J8 és J9 pontosítva)

### J8. A "legutóbbi változtatás" rendezésnél a csoportfejléc "Updated <Hónap> <Év>"

- **Eredeti:** `changed` módban a hasáb a Mappák kategórián belül csoportfejléceket ír: előtag (`Updated ` angolul, `Frissítve ` magyarul) + a csoport hónap-év szövege. Új fejléc akkor jön, ha az előző megjelenített sor hónap-év szövege más, és az év nagyobb, mint 1900. **Az azonos hónapra eső mappák egy fejlécet osztanak.** Az első sor fölött nincs fejléc (J9). Dátum- (`date`) módban a fejléc az év; név és méret módban nincs fejléc (változatlan).
- **Mit ad ma:** lásd az 1. szakaszt.
- **Teendő:**
  1. a `folder_list_model.py` 184-193. soránál a `rows` generátor vigye tovább a `_change` értékét (nanoszekundum, `MAX(p.mtime_ns)`);
  2. `changed` módban a csoportkulcs a `(év, hónap)` a `_change`-ből; fejléc, ha a kulcs más, mint az előző soré, és az év > 1900; a sor típusa maradhat `"year"` (a QML sorkezelése nem változik), vagy új típus kap, a `FolderPaneTreeRow.qml:53,69` bővítésével;
  3. a fejléc szövege: fordítható előtag + hónap-év. **Javasolt döntés (a jegy hozza meg, a bináris nem dönti el):** angol felület: `<Month> <year>` (a felvétellel egyező, `%s %d`); magyar felület: a szövegtár hónapnevei és a `%1$s %2$d` sablon, `Frissítve Április 2019`, mert ez a bináris tartalék-ága és a szövegtár adata. A Windows-regionális `DATE_YEARMONTH` ágat (magyar rendszeren "2019. április") ne kövessük, és a jegy mondja ki, hogy tudatos eltérés (7/N1);
  4. a kulcsolvasat: a változtatási idő a mai `MAX(mtime_ns)` marad, a 7/N3 kérdés lezárásáig;
  5. `tests/app/test_folder_sort_split.py:197-200` rögzítse az új alakot (a hónap-fejlécet, nem az évet).
- **Kész, ha:** (a) egy renderelt próba a Recent Changes rendezésnél a job-802 25. képpel egyező fejléc-sorrendet és -feliratot adja angol nyelven; (b) egy teszt két azonos hónapú mappára EGY fejlécet vár; (c) egy teszt az első sor fölött nem vár fejlécet; (d) egy teszt az 1900-as vagy korábbi évre nem vár fejlécet; (e) a magyar felület előtagja a `.ts`-ből jön, `Frissítve `.

### J9. A lista első sora fölött ne legyen fejléc

- **Eredeti:** a fejléc-gyártó állapota minden újraépítés és kategóriaváltás elején "nincs előző év" (`-1`), és ilyenkor csak az állapotot menti, fejlécet nem ír (`0x004b3802`-`0x004b3809`). A fejléc tehát csak akkor áll egy sor fölött, ha az előző sor éve (dátum mód) vagy hónap-év szövege (legutóbbi mód) más. Következmény: a "minden mappa ugyanabban az évben" eset külön szabály nélkül fejléc nélküli. A 150933 minta egyezik a szabállyal: a `HS logo` az első sor, nincs fölötte fejléc; a következő, dátumos sor éve (2024) más, tehát megkapja a fejlécet.
- **Mit ad ma:** `model_helpers.py:164` (`last_year = None`), `:168-169`, `:156-161`.
- **Teendő:** az első sor fölé ne kerüljön fejléc (`last_year` kezdőértéke az első sor éve, vagy "volt-e már sor" jelző); a homogén-év ág kivehető; átírandó: `tests/app/test_models.py:55` és a `:85-133` közötti sorrend-assertek. A dátum nélküli sor kezelése a `_folder_year` fallbackjével (:175-180) marad, amíg a 7/N2 nem dönt.
- **Kész, ha:** a Colab 04. kép mintáján (öt mappa, öt év, dátumrendezés) a hasáb első sora a `PicasaTeszt`, fejléc nélkül, utána a `2021` fejléc; a 150933 mintán a `HS logo` után a `2024`; a három eset renderelt próbával (nem csak sorlistával) ellenőrzött.

## 6. Bizonyítottsági fok

- **Megerősített** (a kód és az asm egyezik, két független út: a Ghidra-dekompiláció és a közvetlen utasítás-olvasás): a fejléc-gyártó azonossága, a döntési fa, az első sor szabálya, a name/size módok fejléc nélkülisége, a csoportkulcs a Format2 sztring, a `Frissítve ` előtag.
- **Erős:** az `IDS_LISTUPDATED` nem forrása a fejlécnek; a "változtatás dátuma" mint 64 bites pár maximuma.
- **Feltételes:** a 150933 minta és az algoritmus egyezése feltételezi, hogy a dátum nélküli mappa "dátuma" érvényes tartományú `ytDateTime` (a legvalószínűbb a `0,0`, ami az OLE-naptárban 1899-12-30). Ha a dátum érvénytelen lenne, az `elozo_szoveg` üres maradna, és a `0x004b3814`-`0x004b382a` őr éppen a következő fejlécet nyelné el, ami ellentmond a mintának. Ez a következtetés a mintából jön, nem a binárisból.
- **Független újralevezetés nem készült:** a "megerősített" fok a két független forrásúton alapul.
- **A mechanizmus megfejtése nem azonos a "ettől lesz jó a kimenet" állítással:** a J8 renderelt próbája (a job-802 25. képpel) a bizonyíték a megvalósításra; ezt ebben a körben nem mértem.

## 7. Nyitott kérdések mérlege

```
Nyitott kérdések: 0 nyílt · 7 lezárva · 5 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

**Lezárva (7):** L1 melyik kód képzi a fejléceket (`0x004b3770`) · L2 az előtag kulcsa és magyar alakja · L3 az azonos hónapú mappák egy csoport (erős, statikus) · L4 az első sor fölötti fejléc hiánya, kategóriánként · L5 név- és méret-módban nincs fejléc · L6 a megfordítás nem külön ág · L7 az `IDS_LISTUPDATED` nem forrás (erős).

**Blokkolt (5)** (mind felvehető, a következő irány megnevezve):

- **N1. A hónap-év megjelenítése a regionális beállítástól függ** (`ILDATE`, `0x0098b2f8`): `'0'` esetén `%s %d`, különben `DATE_YEARMONTH`. A felvétel az első ágat mutatja (angol Wine). Magyar területi beállításnál mért kép nincs. Mi kell: Colab-feladat magyar területi beállítással (a végrehajtó ezt támogatja-e, előbb ellenőrizendő; ha nem, a `wine_kodlap` melletti terület-beállítás kiegészítése). Kitől: a Colab-végrehajtó. Addig a J8 a javasolt döntéssel megy.
- **N2. Dátum nélküli sor nem első helyen:** dátum módban a gyártónak itt nincs 1900-as kapuja (`0x004b3841`-`0x004b3886`), tehát ha a dátum nélküli mappa dátuma érvényes `ytDateTime` (0,0 = 1899), akkor `1899` fejlécet kapna. Ilyen felvétel nincs. Mi kell: Colab-minta, amelyben egy dátum nélküli mappa dátumos mappák UTÁN áll (leíró sorrendben a legutolsó). Következő irány még statikusan: a `[[L+0xc4]+0x48]` vt+0x20 cél (a 0. mód dátuma, U24), ami megmondja, mit ad egy dátum nélküli mappára.
- **N3. A "változtatás dátuma" pontos mezője:** a `0x00450bd0` a kép-rekordok `+4/+8` 64 bites párjának maximumát veszi. A korábbi lap (`picasa-idorend-bemutato-kutatas.md` 38.2.121/d) szerint a `+4/+8` az "első dátumpár", amelybe a DBLoader a sikeresen olvasott `DateTimeOriginal`-t írja a fájlidő helyett; a `+0xc/+0x10` a fájlidő. Hogy a `0x00450bd0` rekordtáblája (`[L+0x4e8]`, olvasók: `0x004502e0`, `0x004507e0`, `0x00450bd0`) azonos-e ezzel a rekordtípussal, NINCS MEG, és a `tagkereso.py` `0x4e8`-ra a táblát író függvényt nem találta ebben az osztályban. Mi kell: Colab-kontroll (két mappa, az egyikben régi EXIF-dátum és friss fájlidő; mért a Recent Changes csoport hónapja), vagy statikusan a tábla írójának megkeresése. Hatás: a PicasaPy `MAX(mtime_ns)` jó közelítés-e. Az eltérés a hónap-fejlécet és a rendezést is érintené.
- **N4. A `0x004b34a0` "nevesített dátumsor":** minden sorra, a fejléc-döntés előtt meghívódik, és az `[L+0xec]` objektum (`+0x48` tömb, 32 bájtos elemek: dupla dátum a `+0`, felirat a `+0x10`; a kurzor `b+0x54`) szerint, ha egy elem dátuma 1 napon belül van a sor dátumához, típus-2 sort ír a felirattal (`0x004b3592`-`0x004b35a2`). Hogy mit tartalmaz ez a lista, NINCS MEG (a `[reg+0xec]` alakú írások az osztályban csak a nullázó konstruktort és a szabadító `0x004a3790`-et mutatják). Mi kell: az objektum létrehozójának és feltöltőjének megkeresése. A jegy mintáin nem látszik hatása.
- **N5. A `0x004a8c60` és a `0x00448a10` kapuk jelentése** (`0x004b2a57`-`0x004b2a87`): a fejléc-gyártó csak akkor fut, ha az egyik nulla értéket ad, a másik pedig nem engedi át a sort (`bVar10`). A `0x00448a10` a sor nevét a `Z+0x2e98` szöveggel veti össze. Mely sorokat zárja ki, NINCS MEG; a normál mappasorokra a fejléc-gyártó a jegy mintái szerint lefut.

**Örökölt tételek állása:** a `picasa-idorend-viselkedes.md` **U12** (a `0x004b3770`/`0x004b2e10` EBP/EBX forrása) **lezárva**: EBP a builder, EBX az év (`0x004b37fd`, `mov ebx, eax` a `0x0098b9e0` után). **U24/U32** (a 1. mód sor-értéke és összesítője) **részben**: az összesítő a 64 bites pár maximuma, a FILETIME -> dátum átalakítás a `0x0098b650`; a pár jelentése nyitott (N3).

## 8. Helyesbítés a korábbi lapokhoz

- A `picasa-konyvtar-eszkoztar-viselkedes.md` (a `0x004b3770` "albumépítő" jelölt, "Ghidra-kör kell: 0x004b3770", [blokkoló]) és a `picasa-idorend-bemutato-kutatas.md` 38.2.112-113 ("`Updated` albumépítő", "a `0x004b3770` `Updated ` csoportosító és a `]updated` album azonossága NINCS MEG"): **megdőlt a besorolás.** A `0x004b3770` **sorfejléc-gyártó**, nem albumépítő; a típus-2 sora csoportfejléc (év, vagy "Updated hónap év"), és a `CAlbumBuilder::updated` kulcs ennek az előtagja. A `]updated` / `Recently Updated` album (`0x0055ece0`, `0x004abe70`) ettől független; **az azonosság kérdése lezárva: nem azonos**. A `+0x30 = 4` sor beszúrójának keresésében a `0x004b3770` nem jelölt (#5121).
- Az `ui-audit-mainwindow.md` 1.1 pontjának "ha mind ugyanabba az évbe esik, nem rajzol évszám-fejlécet" megfigyelése **megmarad**, de nem külön szabály, hanem az első-sor szabály következménye (J9).

## 9. Amit kizártam

- **"Az `IDS_LISTUPDATED` adja a fejléc szövegét":** nem; a fejléc a `CAlbumBuilder::updated` kulcsot használja (`0x004b3ab3`).
- **"A csoport szemcséje a nap vagy az hét":** nem; a kulcs a `Format2` sztring (hónap és év).
- **"A fejléc a lista első sora fölött is megjelenik, ha dátumos":** nem; az első sorra a fejléc-ág ki van hagyva.
- **"A megfordítás külön fejléc-logikát visz":** nem; a gyártó nem olvassa az `[L+0x165]`-öt.

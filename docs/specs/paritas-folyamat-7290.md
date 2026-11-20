# A biztonsági mentés teljes folyamata az eredeti Picasával összevetve

Jegy: **#7290** (kutatás). Kör: 2026-11-20. Tárgy: Eszközök ▸ Képek biztonsági
mentése, **folyamatszinten**: minden belépési pont, az ablak, a hatás és a
hibaágak, az eredeti és a PicasaPy között. Bináris: `Picasa3.exe` 3.9.141.259,
SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`,
csak statikus vizsgálat (index + capstone, futtatás nélkül).

A tárgyra már van mély lap: [`biztonsagi-mentes.md`](biztonsagi-mentes.md) (a
fájlok, kulcsok és vezérlők szintje). **Ez a lap azt egészíti ki, ami ott nem
állt**: az egész folyamat egymás mellett, és a mai kód mért állapota. A
`biztonsagi-mentes.md` 6., 12.7, 15.4 és 15.9 szakaszának "Nálunk" oszlopa
2026 szeptemberi, **elavult** (a mentés azóta működik: `src/picasapy/backup/`,
#440, #3504, #3593, #3594, #3681, #3751, #4614), a mérvadó mai állapot itt áll.

## 0. Következtetés

A folyamat **szerkezete egyezik** (egyetlen belépési pont a Tools menüben,
teljes ablakos mentés-mód, mappánkénti pipák, nevesített készletek, három
fájlszűrő, ISO-kimenet a fizikai írás helyett). A **folyamat két helyen nem**:

1. **a "mi van már mentve" döntés** nem azt nézi, amit az eredeti
   (`backuphash` és `BKTag <készlet>-backuphash` összehasonlítása a
   `.picasa.ini`-ben), ezért a **metaadat-szerkesztés** (felirat, kulcsszó,
   forgatás, vágás, geotag, arc) után a kép nálunk **nem** kerül újra mentésre
   (mérve, 4.1);
2. **a hibaágak**: az **írásvédett célfájlt** az eredeti felülírja, nálunk a
   módosult kép **soha nem íródik át, és a felület mégis "Backup Complete"-et
   mond** (mérve, 4.4).

Ezen felül: nincs alapértelmezett készlet és `LastBkSet` (4.3), nincs
lemezhely-ellenőrzés (4.5), a menütétel nincs letiltva nyitott panel mellett
(4.2), a `files.txt` formátuma más (4.6). Nyolc jegytörzs az 5. szakaszban
(J1-J6 fejlesztői, J7-J8 kutatási).

## 1. MIT AD MA (a mai kód mért állapota)

| rész | hol | méret |
|---|---|---:|
| terv, másolás, `files.txt` | `src/picasapy/backup/futtatas.py` | 260 sor |
| fájlszűrő (3 állás) | `backup/szuro.py` | 64 |
| ISO-kimenet, lemezekre osztás | `backup/lemezkep.py`, `burn/iso.py` | 144, 545 |
| visszaállítás (#4614) | `backup/visszaallitas.py`, `iso_olvaso.py` | 349, 186 |
| készlet- és nyilvántartás-tár | `index/backup_sets.py` (SQLite `backup_sets`, `backup_files`) | 227 |
| felületi híd | `app/backup_controller.py` (+ `_runs`, `_sets`) | 275, 197, 232 |
| felület | `BackupHost.qml`, `PublishPanel.qml` | 728, 694 |

Két **mérés** a mai kódon (6. szakasz a parancsokkal):

- **M1 (írásvédett cél):** egy írásvédett (0444) forrásfájl első mentése
  után a cél is 0444. A forrás megváltozik, második futás: **tervezett 1,
  átmásolt 0**, a cél tartalma a régi, és a harmadik terv **újra 1 tételt
  tervez** (soha nem teljesül).
- **M2 (metaadat):** mentés után a `.picasa.ini` képszakasza
  `caption=…` és `backuphash=100 -> 200` változáson megy át: a következő terv
  **0 tételt tervez, 1-et kihagy**.

## 2. Bizonyítási terv eleje: a cím-atlasz válasza

```
🗺️ Atlasz (`cim-atlasz.tsv`, `atlasz_keres.py`):
- 0x0065d010 (függvény 0x0065d010-0x00660c57): picasa-kereses-modok.md, paritas-ellenorzes-archiv-1.md (Small Pictures szűrő); a mentés-szűrő ágat egyik sem írja le
- 0x00670ae6, 0x00670cb3 (függvény 0x006706d0-0x00671197): ajandek-cd-kimenet.md 11.5 (csak az alapnév és hogy a LastBkSet olvasódik), biztonsagi-mentes.md 10.1
- 0x0067834e (függvény 0x00677a70-0x0067862d): biztonsagi-mentes.md 11.1/d (az írásvédettség levétele; a nálunk-mérés nem)
- 0x0056f59c (függvény 0x0056e1c0-0x0056f8f0): a menü-frissítő; a 0x9d38 ágat egy lap sem írja le
- 0x00694450 (függvény 0x00694450-0x006945a2): nincs találat, ÚJ terület
```

Amit ez eldönt: az **alapértelmezett készlet automatikus létrehozása**, a
**`LastBkSet` szerinti kiválasztás**, a **menü-engedélyezés** és a
**bélyegző-ciklus** eddig nem volt leírva. A `0x0065d010` mentés-szűrő ága
szintén új.

## 3. Eredeti / nálunk / teendő

Jelölés: **EGYEZIK** · **ELTÉR** · **HIÁNYZIK** · **TÖBBLET** (nálunk van, az
eredetiben nincs) · **KÍVÜL** (hatókörön kívül) · **NINCS MEG**. A "nálunk"
oszlop **mérés** (kód olvasva, M1 és M2 futtatva); ahol nem mértem, ott kimondva.

### 3.1 Belépési pontok

| # | Eredeti | Nálunk | Állapot, teendő |
|---|---|---|---|
| B1 | Menü: Eszközök ▸ "&Képek biztonsági mentése..." (`eMenuTools::ID_TOOLS_BACKUP`, cmd `0x9d38`, mnemonik `b`, menürekord `0xd6e8dc`, regisztráló `0x00559150`). Kezelő `0x005cb990:0x005cbdee`: a `thumbui/backup` **névparancs** (`0x009cd8a0`), a `0x005d9cc0` (`0x005db77c-0x005db7ee`) a `0x0067be30` panel-konstruktort hívja (`+0x13e`=1, `+0x13f`=0) | `PicasaToolsMenu.qml:75-78` -> `MainMenuBar.qml:317` -> `BackupHost.qml:144-149` | **EGYEZIK** (hely, felirat, mnemonik: #1774) |
| B2 | **Más belépési pont nincs.** A `thumbui/backup` gomb `m_hidden` (`thumbui.tre:95-100`); a sztringre **két** függvény hivatkozik (`0x005cb990`, `0x005d9cc0`); a `0x9d38` azonosítónak a kódban **egyetlen** négybájtos közvetlen értékű előfordulása van (`0x0056f59d`, a menü-frissítő; `38 9d 00 00` bájtpásztázás), a diszpécser ugrótáblán éri el. Gyorsbillentyű, helyi menü, eszköztár-gomb: nincs | egyetlen út: a Tools menü | **EGYEZIK** |
| B3 | **Engedélyezés** (`0x0056f56e-0x0056f5a2`, előkészítés `0x0056e257-0x0056e2e0`): letiltott, ha `[főablak+0x34a4] != 0` (néző nyitva), **vagy** `[főablak+0x30f4] != 0` (a kiadás-panel objektuma **létezik**, vagyis már nyitva van), vagy az `editpanel/preview` látszik és `[esp+0x20]` nulla | `PicasaToolsMenu.qml:77`: `enabled: !bar.editorActive`, ahol `editorActive: hostWindow.viewerOpen` (`MainMenuBar.qml:153`). Nyitott panel mellett **nem** tiltott, `nyisd()` újra futtatható, futó másolás közben is | **RÉSZBEN**: a néző-feltétel egyezik, a "panel már nyitva" nem. -> **J4** |
| B4 | Az **Ajándék-CD** (`thumbui/cdmode`, `0x005db4bc-0x005db4d5`) ugyanazt a panelt nyitja, más mód-bájttal; a `publishswitcher` vált (`0x00679ca0`, `0x0067be30`) | `MainWindowPeripheralLayers.qml:98-116`: az egyik nyitása zárja a másikat | **EGYEZIK** |
| B5 | `auto_backup_prompt` (`0x0060dcc0`) és `desktop_backup` (`0x0096b9c0`) **nem** ennek a funkciónak a belépési pontjai: az első a Google Fotók automatikus mentésének felajánlója (`picasa-fen-dialogs.md` 4.9), a második a Google Fotók feltöltő JSON-ja (`album_title`, `sha1_fullsize`, `hmac_512_*`) | nincs, és nem is kell | **KÍVÜL** (online, megszűnt szolgáltatás) |

### 3.2 Ablak és nézet

| # | Eredeti | Nálunk | Állapot, teendő |
|---|---|---|---|
| W1 | Teljes ablakos mód, fejléc "Backup your photos", bal hasábon a mentetlen mappák pipákkal, jobbra a mentetlen képek rácsa, alul a `publish/backup_group` két lépéssel és Burn / Eject / Cancel gombokkal. A mód-makró (`m_backupcontrolset_enable`, `macros.tre:245`) elrejti a keresősávot, az alsó élet és a logót. Élő felvétel: `Colab EN 24 - Confirm (Back Up Pictures).png` (colab #22) | `BackupHost.qml` + `PublishPanel.qml` (#3504), bal hasáb `MainFolderPane.qml:170-175`, rács `LightboxFeed.qml:83-91`, üres felirat "All Files are backed up in this set" (`FolderPane.qml:223`, `LightboxFeedEmptyState.qml:12`) | **EGYEZIK** a szerkezetre (#3594, #3681, #3751). A keresősáv/él/logó eltűnése **nem újramérve** ebben a körben |
| W2 | **Készlet-előválasztás.** Üres készletlistánál a panel **maga hoz létre** egy "Saját mentési készlet" (`il_BurnPanel::bksetname`) nevű készletet és kiírja a `backups.xml`-t; létező listánál az utoljára használtat (`Preferences\LastBkSet`) választja, ha a név nincs a listában, a 0. indexűt (`0x00670dd5`) | `BackupHost.qml:33` `kivalasztott: -1`; `frissitsd()` (`:203-212`) nem választ; `PublishPanel.qml:350` a legördülő **rejtett** 0 készletnél. Minden nyitásnál kézzel kell választani, első indításnál előbb "New Set" | **HIÁNYZIK**. -> **J3** |
| W3 | Készlet-párbeszéd (`NewBkDialog`: `name`, `files`, `type`, `disk`; cím "Edit Backup Set", gomb "Change"; `0x00678e80`, `0x00679310`, `0x00679570`) | `ujKeszletUrlap()` `BackupHost.qml:214-223` (alapnév #3189), három szűrő-állás, két típus (#3593) | **EGYEZIK** (`biztonsagi-mentes.md` 15.8, 15.9) |
| W4 | Gomb-szabályok: `backup_go` felirata "Biztonsági mentés", ha a készletnév nem üres, különben "Írás" (`0x0067051b-0x00670581`); `deletebackupset` rejtve, ha ≤ 1 készlet (`0x006705c9`); `backup_set_menu` rejtve, ha nincs készlet (`0x0066fdee`) | `PublishPanel.qml:508`, `:377`, `:350` | **EGYEZIK** |
| W5 | Törlés megerősítése (`il_NewBkDialog_delete`, `0x00679ca0`) | `BackupHost.qml:287`, `:715-727` | **EGYEZIK** |
| W6 | **Cancel** (`publish/backup_cancel`, összehasonlítás `0x00679e90`): a `thumbui/publishswitcher` kattintása (`0x0067b73f-0x0067b744`), majd `0x0067be30(0,0,0,0)`: a panel zár, vissza az alapmódba. A kezelőben nincs ág a futó háttérfolyamatra | zárásnál a pipák törlődnek (`BackupHost.qml:87`); a futó másolást a Stop szakítja meg (#3009) | **EGYEZIK**; a Stop **TÖBBLET** |

### 3.3 Hatás (fájl, `.picasa.ini`, index, bal hasáb, rács, kijelölés)

| # | Eredeti | Nálunk | Állapot, teendő |
|---|---|---|---|
| E1 | **A "mentetlen" döntés** a `0x0065d010` keresés-végrehajtóban: képenként a 16 bites `backuphash` (`cx`) és a `<készlet>-backuphash` (`ax`): kihagyja, ha `ax == 0xFFFF` (`0x0065e750`), vagy ha `ax != 0` és `ax == cx` (`0x0065e75c-0x0065e764`); bent marad, ha `ax == 0` (soha nem mentett) vagy eltér. Tartalom-mód: ha `[this+0x3708] == 0` minden kép bent marad, különben a `0x0040f9f0` típus-predikátum dönt (12 típuskód) (`0x0065e771`, `0x0065e79b-0x0065ea97`) | `futtatas.py:131-133`: csak a **kép** (méret, `mtime_ns`) a `backup_files` táblával (`index/backup_sets.py:55-62`); a `.picasa.ini`-t **nem** nézi (M2) | **ELTÉR** (P1). -> **J2** |
| E2 | **Bélyegzés mentés után:** a `0x00694450` a gyűjtemény minden tételén végigmegy (kapu: `[tétel+4] != -1`, `[tétel+0x30] & 2 == 0`), és tételenként a `0x00429cf0`-t hívja: `<készlet>-backuphash` kulcs (`0x00429d1c`), olvasás (`0x00429d3b`), 0 esetén új bélyeg (`0x00429d4d`), kiírás az ini-be (`0x00429d86`) és az adatbázisba (`0x00429d9f`) | a forrás `.picasa.ini`-jét **nem** módosítja; a nyilvántartás csak az indexben (SQLite) | **ELTÉR**. -> **J2** |
| E3 | `backuphash` frissítők metaadat-szerkesztésnél: `rotate` `0x0042c980`, `caption` `0x00437cf0`, `keywords` `0x00455ff0`, `faces` `0x00484820`, `crop` `0x0042b370`, `flipped` `0x0042d7e0`, `geotag` `0x00477ff0` (`picasa-ini-format.md`). **Minden ilyen szerkesztés újra mentendővé teszi a képet** | a PicasaPy is frissíti a sima `backuphash`-t szerkesztéskor (`ini/backuphash.py`, `with_backuphash` hívók), de a mentés **nem olvassa** | **ELTÉR**, ugyanaz a jegy. -> **J2** |
| E4 | Másolás a cél alá, a mappák `.picasa.ini`-jével együtt (a mintalemezen: 22 felhasználói tétel: képek, `.picasa.ini`, `contacts\backup.xml`; `biztonsagi-mentes.md` 13.1). Időbélyeg: `SetFileTime` a másolóban (`0x00677a70` importja) | `futtatas.py:210-236`: `shutil.copy2` (mtime megmarad) és mappánként az ini | **EGYEZIK** (a létrehozási idő Linuxon nem állítható) |
| E5 | **`files.txt`**: író `0x008447b0` (`"w"`, `0x00844855`), fejléc `# Created on %s by %s` (`0x00844930`), `# version: %s` (`0x00844974`), `# platform: %s %s` (`0x008449ba`), tételenként útvonal / felirat (`0x00844a59`, `0x00844aa3`), a mentés-ág `ft,` sort **nem** ír (`0x00693bfc`). Olvasója a `PicasaRestore.exe`, amely két jegyzéknevet keres (`RestoreDialog::cantFind`; a `files.txt` nevet a `FUN_00412550` építi) | `futtatas.py:162-181`: soronként `relatív<TAB>méret<TAB>mtime_ns`; a PicasaPy visszaállítója mindkét alakot olvassa (#4614) | **ELTÉR** (P3). -> **J5** |
| E6 | Készletek tárolása: `db3\backups.xml` (író `0x006759c0`, olvasó `0x00676910`; az alapértelmezett készlet létrehozásakor azonnal kiírva, `0x00670ca8`); utolsó készlet: `Preferences\LastBkSet` | SQLite `backup_sets` (szándékos, `index/backup_sets.py:8-12`); az eredeti készletei **nem** jönnek át | **ELTÉR** (dokumentált tárolási döntés); migrációs hiány -> **J3** opcionális pontja |
| E7 | A Picasa saját adata a mentésben: a mintalemezen `$Application Data\Google\Picasa2\contacts\backup.xml` (`0x0066f2b0` a `contacts.xml`-t másolja `backup.xml`-be, egyetlen hívó `0x0066f58c`) | nincs; a visszaállító a `$Application Data` ágat kihagyja (`visszaallitas.py:60`) | **NINCS MEG**, hogy a **mappába** mentésnél is így van-e. -> **J7** |
| E8 | **Index, bal hasáb, rács, kijelölés:** a lista a mentés után újraszűrődik. A régi paritás-sor (`paritas-ellenorzes-archiv-1.md:1008`, Q37): az eredeti felvételen "2 kép kijelölve", a PicasaPy-ban "kijelölés törlődik" | `keszletekValtoztak` -> `frissitsd()` (`BackupHost.qml:203`); a kijelölés sorsa a nyitáskor: nem kezeli | **NINCS MEG**: a felvételt az IMAPI Confirm-ablak szennyezi (az `EN 24` kép is mutatja). -> **J7** |

### 3.4 Hibák, megszakítás, írásvédett és hálózati hely, visszavonás

| # | Eredeti | Nálunk | Állapot, teendő |
|---|---|---|---|
| H1 | **Írásvédett célfájl:** `GetFileAttributesEx` (`0x00677f6d`), `GetFileAttributes` (`0x0067834e`), `and eax, 0xfffffffe` (`0x0067835d`), `SetFileAttributes` (`0x00678362`), majd `CreateFile(WRITE, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL)` (`0x0067839a`): a jelzőt leveszi és **felülír**; a célt `FILE_ATTRIBUTE_NORMAL`-lal nyitja | `futtatas.py:215-220`: `shutil.copy2` (a módbiteket is másolja), `except OSError: continue`. **M1:** az írásvédett forrásból írásvédett cél lesz, a módosult kép **soha nem íródik át**, minden futás újratervezi | **ELTÉR** (P1). -> **J1** |
| H2 | **A cél megnyitása sikertelen:** `cmp eax,-1` (`0x006783a0`), `GetLastError`, naplósor a `.\yt\ytIO.cpp:417` helyről (`0x006783b8-0x006783cd`), **nincs párbeszéd**, a hurok a következő fájllal folytatódik (`0x006783d9` -> `0x00678425`) | `futtatas.py:217-220`: csendes kihagyás, **nincs napló** | **RÉSZBEN**: a csendes kihagyás egyezik, a napló hiányzik. -> **J1** |
| H3 | **Lemezhely-előellenőrzés:** a háttérfolyamat másolás előtt 64 bites összehasonlítást végez (`0x00678976-0x0067899a`, a jelzőbájt `[esp+0x2f]`), hiány esetén üzenet (`il_BurnPanel::BackgroundProc::4`, `0x006789a1-0x006789ab`, megjelenítő `0x00980700`) és **nincs másolás** (kilép nullával, `0x006789cd`) | nincs ilyen szöveg és ellenőrzés (`grep` nulla találat). Tele lemezen minden fájl az `except OSError`-ba esik, a felület "Backup Complete" | **HIÁNYZIK** (P2). -> **J6** |
| H4 | Záró üzenet `BackupCopy::3` "A mentés elkészült" (`0x00677a70`), a másolás közben `BackupCopy::1` "Fájlok másolása (%2$d/%1$d)", előtte `BackupCopy::2` "Biztonsági mentési adatok frissítése" | `BackupHost.qml:409-414` **mindig** "Backup Complete"; közben "Copying (%1/%2) files", a `.ts`-ben "(%1/%2)" (`picasapy_hu.ts:19900-19902`) | **EGYEZIK** a végszövegre. A helyőrző-sorrend **ELTÉR**: az eredeti magyar felcseréli (összes/kész), nálunk kész/összes. Döntés: marad (az eredeti magyar sorrend nyilvánvaló fordítási hiba), rögzítve itt |
| H5 | Háttérfolyamat-állapotok (`0x00678630`): `BackgroundProc::1` "Biztonsági mentés folyamatban", `::3` "Fájlok előkészítése: %d%%", `::5` "Mentés kész" | egyik szövegre sincs találat (`grep` nulla); a megjelenítés helye és sorrendje **nincs mérve** | **HIÁNYZIK** (P3), a hely **NINCS MEG**. -> **J7** |
| H6 | **Hálózati/NAS cél:** a másoló importjai `GetLastError`, `InterlockedIncrement`, `SetFileTime`; hálózat-specifikus ág nem látszik, de a thunk-táblán át hívott fájlműveleteket nem vizsgáltam | ugyanaz az `except OSError` ág | **NINCS MEG** (nem mérve) |
| H7 | **Visszavonás nincs.** A `RestoreDialog::*` sztringekre a `Picasa3.exe` indexében **nincs** találat; a visszaállítás a lemezre másolt `PicasaRestore.exe` dolga (`0x0066f9f0`: `cdautorun\PicasaRestore.exe`). `RestoreDialog::finished`: "%1$d fájl visszaállítása befejeződött; összesen %2$s." | a BackupHost Restore-ja (#4614): "Restored %1 file(s); skipped %2 existing file(s)." | **TÖBBLET**. A záró szöveg kis eltérése rögzítve, javítás nem kell (nincs eredeti Picasa-beli párja) |
| H8 | **Fizikai lemezírás:** IMAPI2 (`0x00671ef0`, `il_BurnPanel::imapierror`), `nodrives` kérdés ".ISO-fájl létrehozása helyette?" (`0x00673de0`), `BackupGo::1` "A lemez ellenőrzése sikertelen" | a CD/DVD típus ISO-t ír (#2074) | **KÍVÜL**: tulajdonosi döntés 2026-09-18, ld. `biztonsagi-mentes.md` 13. |

## 4. A lelet bizonyítéka

### 4.1 A "mentetlen" döntés a keresési láncban él (`0x0065d010`)

A mentés-nézet az eredetiben **szűrő** a könyvtári lekérdezésben, nem külön
lista. A `0x0065d010` (15 431 bájt, egyetlen hívó: `0x00662220`) a `Preferences`,
`backuphash` (`0x00c80c6c`), `-backuphash` (`0x00c81450`), `Show only big images`
és `BigPictureThreshold` sztringekre hivatkozik. A mentés-szűrő ága:

```
0x0065e2fe  mov eax,[ecx+0xde8]      ; a kiválasztott készlet neve; üres => a szűrő nem fut
                                     ; (0x0065e304-0x0065e31c: null / üres CString => ugrás 0x0065edb8)
0x0065e36c  push 0xc81450            ; "-backuphash": <készlet>-backuphash oszlopnév
0x0065e381  add esi,0xf20            ; az imagedata-oszlopok bázisa [this+0x2bc]+0xf20
0x0065e4a7  push 0xc80c6c            ; "backuphash": a sima oszlop
0x0065e700  ...ciklus az összes képen...
0x0065e733  movzx ecx,word [..]      ; cx = a kép sima backuphash-e (16 bit)
0x0065e74d  movzx eax,word [..]      ; ax = a kép <készlet>-backuphash-e
0x0065e750  cmp ax,0xffff / je 0x65eab2   ; 0xFFFF: kihagy
0x0065e75c  cmp ax,di (0)    / je 0x65e76a   ; 0: soha nem mentett => bent marad
0x0065e761  cmp cx,ax        / je 0x65eab2   ; egyenlő: naprakész => kihagy
0x0065ea9b  [lista+k*4]=kép; k++     ; felvétel a "mentetlen" listába
0x0065eab2  következő kép
```

A **sima** `backuphash` pedig a `0x00454770` közös ini-íróval frissül
(`picasa-ini-format.md`, "A `backuphash`" szakasz): forgatás, felirat,
kulcsszó, arc, vágás, tükrözés, geotag. Láncban: **felirat-szerkesztés ->
új sima `backuphash` -> eltér a készlet-kulcstól -> a kép újra mentendő.** A
lánc két felét **olvastam**, az **élő igazolás** (a mentés-nézet újranyitása
szerkesztés után) **nincs meg**: J7.

### 4.2 Engedélyezés

A `0x0056e1c0` menü-frissítő a `0x9d38` parancsot a `0x0056f56e-0x0056f5a2`
szakaszon engedélyezi: `al = 1` akkor és csak akkor, ha `[edi+0x34a4] == 0`
**és** (`[esp+0x20] != 0` **vagy** `[esp+0x13] == 0`) **és** `[edi+0x30f4] == 0`.
A `[esp+0x13]` az `editpanel/preview` (`0x00c88a2c`) csomópont láthatósága
(a csomópont `+0x20c` bájtja nulla: `0x0056e240-0x0056e265`), az `[edi+0x30f4]`
a főablak panel-objektuma (`ajandek-cd-kimenet.md` 12.3). Az `[esp+0x20]`
összetett állapot (egy másik csomópont láthatósága, egy mód-érték 2/4/6, a
nyomtatás-panel láthatósága `0x0056c110`, `0x0056e292-0x0056e2e0`); **a
jelentését nem bontottam szét**, ezért a B3 sor a két biztosan olvasott
feltételre (`+0x34a4`, `+0x30f4`) épít.

### 4.3 Üres készletlista és `LastBkSet` (`0x006706d0`)

```
0x00670a9c  cmp byte [ebp+0x13e], bl ; je 0x670f34   ; +0x13e == 0: Ajándék-CD ág
0x00670aa8  mov ecx,0xc7eeb8 ("#db3\") ; call 0x676910   ; a készletek beolvasása
0x00670ab6  test [ebp+0x2b4],0xfffffffe              ; a készletek száma nem nulla?
0x00670ae0  jne 0x670cb3                              ; van készlet: ugrás a LastBkSet-re
0x00670ae6  push 0xca4680 ; mov eax,0xca4670 ("My Backup Set") ; call 0x9ae560
0x00670b03  push 0xca4698 ("BKTag ") ; ... call 0x408760  ; belső név = "BKTag " + név
0x00670ca8  push 0xc7eeb8 ; push ebp ; call 0x6759c0    ; a backups.xml KIÍRÁSA
0x00670cb3  push 0xca46a0 ("LastBkSet") ; push 0xc7eafc ("Preferences") ; olvasás
0x00670d63  a nevek összehasonlítása készletenként      ; találat: az az index
0x00670dd5  mov [esp+0x18],ebx (0)                      ; nincs találat: 0. index
```

**Amit nem követtem végig:** az üres vagy hiányzó `LastBkSet` rövidzárát
(`0x00670d2b-0x00670d46`, ugrás `0x00670dd9`-re): az index ott `[esp+0x18]`-ból
jön, amelynek az értékét ez az ág nem állítja. Az `EN 24` felvétel (egyetlen
készlet, az látszik) a "0. készlet" olvasatot támasztja, de ez **feltételes**.

**Élő megerősítés:** az `EN 24` felvételen a legördülő "My Backup Set"-et
mutat, az "Edit Set" aktív, a "Delete Set" szürke (egy készlet).
Az alapértelmezett készlet `diskroot` nélküli, vagyis **CD/DVD típusú**
(`biztonsagi-mentes.md` 2.).

### 4.4 Az írásvédett cél és a hiba csendes elnyelése (M1)

Az eredeti ága `biztonsagi-mentes.md` 11.1/d-ben már le volt írva, de a
**nálunk-mérés** nem. M1 eredménye (6. szakasz): első futás tervezett 1 /
átmásolt 1 / cél mód `0o444`; második futás tervezett 1 / **átmásolt 0** / a
cél tartalma a régi; harmadik terv **1 tétel**. Az ok kettős: a `shutil.copy2`
a módbiteket is másolja (a cél írásvédett lesz), a felülírás pedig
`PermissionError`, amit a `except OSError: continue` (`futtatas.py:217-220`)
némán elnyel, és a felület `onFutasKesz` (`BackupHost.qml:409-414`) mindenképp
"Backup Complete"-et ír.

### 4.5 Lemezhely

A `0x00678630` (1246 bájt) a másolás előtt összehasonlít két 64 bites értéket
(`0x00678988-0x0067899a`: a magas szó `ja`/`jb`, majd az alacsony `jae`), és
ha a feltétel nem teljesül: `BackgroundProc::4` üzenet, kilépés nullával, nincs
másolás. **Nem mért:** a két operandus pontos jelentése és a `[esp+0x2f]`
jelzőbájt forrása (a küszöb: a szükséges méret a szabad helyhez képest, de a
tartalék és a cél típusa nincs kiolvasva).

### 4.6 `files.txt`

Lásd E5. A mentés-ág három soros rekordot ír, `ft,` nélkül. A `files.txt`
**útvonal-stílusa** (a céltól relatív vagy abszolút) valódi kimenet nélkül
nincs kiolvasva: **J7**.

## 5. Javasolt fejlesztői jegytörzsek

Közös: a hívó nyitja meg a jegyeket és a címkéket. A bizonyítottsági fok a 7.
szakaszban.

### J1 (P1, hiba) "Mentés: az írásvédett célfájl nem íródik felül, a kimaradt fájl nincs naplózva"

**MIT AD MA:** M1 (6. szakasz): az írásvédett forrásból írásvédett cél lesz,
a módosult kép soha nem íródik át, minden futás újratervezi, a felület
"Backup Complete".
**Eredeti:** `0x0067834e` (`GetFileAttributes`), `0x00678359` (`test al,1`),
`0x0067835d` (`and eax,0xfffffffe`), `0x00678362` (`SetFileAttributes`),
`0x0067839a` (`CreateFile`, `OPEN_ALWAYS`, `FILE_ATTRIBUTE_NORMAL`). Hibaág:
`0x006783a0` (`cmp eax,-1`), `0x006783b8-0x006783cd` (naplósor
`.\yt\ytIO.cpp:417`), `0x006783d9` -> `0x00678425` (következő fájl).
**Teendő** (`backup/futtatas.py`, `futtasd`): a másolat **ne örökölje** az
írásvédettséget (tartalom és idők másolása, nem a módbitek; az eredeti a célt
`FILE_ATTRIBUTE_NORMAL`-lal nyitja), a meglévő írásvédett cél **írhatóvá tétele
után** íródjon felül; a sikertelen fájlról
`_log.warning` készüljön, a fájl maradjon bélyeg nélkül (ahogy ma).
**Nem mért / nem kell:** külön felhasználói üzenet. Az eredetiben nincs ilyen
szöveg, ezt nem találjuk ki.
**Kész, ha:** (1) az M1 szkript mintájára írt teszt zöld: a második futás
átmásol 1-et, a cél tartalma az új, a harmadik terv 0; (2) rontás-kontroll:
a javítás nélkül a teszt bukik; (3) nem írható célnál a hiba a naplóba kerül,
a futás a többi fájllal folytatódik.

### J2 (P1) "Mentés: a metaadat-szerkesztés után a kép újra mentendő, a készlet-bélyeg a .picasa.ini-be kerül"

**MIT AD MA:** M2: felirat és `backuphash` változás után a terv 0 tétel.
A döntés csak (méret, `mtime_ns`): `futtatas.py:131-133`.
**Eredeti:** döntés `0x0065d010` (`0x0065e36c`, `0x0065e4a7`, `0x0065e750`,
`0x0065e75c`, `0x0065e761`, felvétel `0x0065ea9b`); bélyegző-ciklus
`0x00694450`; bélyeg `0x00429cf0` (`0x00429d1c`, `0x00429d3b`, `0x00429d4d`,
`0x00429d86` -> `0x00454770`, `0x00429d9f`); átnevezés `0x00473fd5`,
`0x0047402f` (hívó `0x0067ae70`).
**Teendő:** (a) a terv a kép `.picasa.ini`-szakaszából olvassa a sima
`backuphash`-t és a `BKTag <készletnév>-backuphash` kulcsot (ini-API,
sáv-invariáns): mentendő, ha a készletkulcs hiányzik vagy 0, vagy eltér a
simától; `0xFFFF` esetén kihagy; (b) a (méret, mtime) ellenőrzés **marad
kiegészítésként** (az eredeti a kívülről módosított fájlt nem veszi észre, ez
nálunk biztonságosabb); (c) sikeres másolás után a forrás `.picasa.ini`-jébe a
sima `backuphash` (ha hiányzik vagy 0: új bélyeg a #5810 képlettel,
`ini/backuphash.py`) és a `BKTag <készletnév>-backuphash` **ugyanazzal az
értékkel**, **csak a sikeresen másolt fájlra**; (d) készlet átnevezésénél az
összes képszakasz kulcsa átneveződik; (e) az eredeti Picasa által írt `BKTag`
kulcsok így beszámítanak (a tulajdonos saját mentésének mintájában 20/20
szakasz hordozta).
**Kész, ha:** teszt: kép + ini, mentés, felirat-szerkesztés a PicasaPy
útján, a terv 1 tételt ad; mentés után az ini-ben a két kulcs egyezik; eredeti
eredetű ini egyező kulcsokkal a tervet 0-ra adja; `0xFFFF` kihagy; átnevezés
után a kulcsok átneveződnek; a #2462 round-trip őr zöld.
**Mellékhatás, kimondva:** a mentés a forrásmappák `.picasa.ini`-it módosítja
(az eredeti is, `biztonsagi-mentes.md` 9.2).

### J3 (P2) "Mentés: alapértelmezett készlet az első megnyitáskor, és az utolsó készlet megjegyzése"

**MIT AD MA:** `kivalasztott: -1` (`BackupHost.qml:33`), a legördülő rejtett
0 készletnél (`PublishPanel.qml:350`), nincs megjegyzett készlet.
**Eredeti:** `0x00670aa8` (olvasás), `0x00670ab6-0x00670ae0` (feltétel),
`0x00670ae6-0x00670af0` (`bksetname`), `0x00670b03-0x00670b25` (`BKTag `+név),
`0x00670ca8-0x00670cae` (kiírás), `0x00670cb3` (`LastBkSet`), `0x00670d63-0x00670dc8`
(keresés), `0x00670dd5` (0. index).
**Teendő:** üres készletlistánál a megnyitás hozzon létre egy "Saját mentési
készlet" (`il_BurnPanel::bksetname`, EN "My Backup Set") nevű, **CD/DVD típusú**
(`cddvd`, célja `lemezkepAlapHely()`) készletet és válassza ki; későbbi
nyitásnál a legutóbb használt készletet válassza név szerint (ha eltűnt, az
elsőt); a készletváltás mentse el az utolsót.
**Opcionális, külön döntés:** az adatmappa `db3\backups.xml`-jének importja
(formátum: `biztonsagi-mentes.md` 2.), ha a tulajdonos migrációt kér.
**Kész, ha:** üres adatbázison az első megnyitás után pontosan 1 készlet van,
kiválasztva; kétszeri megnyitás között a választás megmarad; kattintásos QML-teszt.

### J4 (P3) "Képek biztonsági mentése menütétel: tiltva, ha a kiadás-panel már nyitva van"

**Eredeti:** `0x0056f56e-0x0056f5a2`, `0x0056e257-0x0056e2e0`, a feltétel a 4.2
szerint. **Nálunk:** `PicasaToolsMenu.qml:77`.
**Teendő:** a tétel legyen szürke, amíg a mentés- vagy az Ajándék-CD-panel
nyitva van (a `+0x30f4` az összes üzemmód panelje), a néző-feltétel marad.
**Kész, ha:** nyitott panel mellett `menuToolsBackup.enabled == false`, futó
másolás közben sem nyitható újra; QML-teszt.

### J5 (P3) "Mentés: a files.txt az eredeti nyelvtanban"

**Eredeti:** `0x008447b0` és a 3. szakasz E5 sora. **Nálunk:** `futtatas.py:162-181`.
**Teendő:** az író a háromsoros rekordokat adja (`ft,` nélkül, mint az eredeti
mentés-ág); az olvasó a régi tabos alakot **továbbra is olvassa**. **Függ a
J7-től:** a valódi `files.txt` útvonal-stílusa (relatív vagy abszolút) nincs
kiolvasva.
**Kész, ha:** a kimenet a `PicasaRestore.exe` olvasójának nyelvtanával
(`0x00412550`, `0x0040f7d0`) értelmezhető; a visszaállítás mindkét alakot kezeli.

### J6 (P2) "Mentés: lemezhely-ellenőrzés másolás előtt"

**Eredeti:** `0x00678976-0x0067899a`, üzenet `0x006789a1-0x006789ab`
(`il_BurnPanel::BackgroundProc::4`, HU "Nincs elegendő hely a fájlok
biztonsági mentéséhez"), kilépés `0x006789cd`. **Nálunk:** nincs; tele lemezen
minden fájl csendben kimarad.
**Teendő:** mappába mentésnél, ha `shutil.disk_usage(cél).free` kisebb, mint a
terv összmérete, ne induljon másolás, és a hivatalos szöveg jelenjen meg; a
lemezkép-ágnál a célmappára ugyanez. **Nem kiolvasott:** az eredeti pontos
küszöbe (tartalék van-e), ezt nem találjuk ki.
**Kész, ha:** szimulált kevés hellyel nincs másolás és megjelenik az üzenet.

### J7 (kutatás, Colab-felvétel) "A mentés eredeti futása mappába mentéssel: hatás, leltár, hibák"

Nyitott kérdések, amelyeket csak az eredeti futásából lehet kiolvasni:
(1) a **Disk-to-disk** készlet **Wine alatt is** végigvihető-e (az IMAPI-hiba
csak a CD típusra vonatkozik-e); (2) a célmappa tartalma, a `files.txt`
**útvonal-stílusa**, van-e `$Application Data\…\contacts\backup.xml` (E7);
(3) a forrás `.picasa.ini` mentés után (sima `backuphash` és `BKTag` kulcs);
(4) **felirat-szerkesztés után** a mentés-nézet újranyitva mutatja-e a képet
(a 4.1 lánc élő igazolása); (5) a kijelölés sorsa a nyitáskor (E8, Q37); (6) az
állapotszövegek helye és sorrendje (H5); (7) írásvédett célfájl felülírása (H1).
Eszköz: `colab_felmero.py futtat --lepesek …` (a `picasapy-research` skill 1/d
szakasza). Az (1) a többi előfeltétele; ha nem megy, a (4) és a (7) a
PicasaPy-oldali tesztekből akkor is igazolható a mi oldalunkra.

### J8 (P3, kutatás) "A mentés-nézet típus-predikátuma és a 'Minden kép (videók nélkül)' szűrő"

**Eredeti:** `0x0040f9f0` (66 bájt) igaz a 12 típuskódra: `2, 3, 6, 7, 0xd,
0x1f, 0xe, 0x12, 0x1b, 0x1c, 0x18, 0x16`; hívók `0x00478780`, `0x0047b4d0`,
`0x0047e470`, `0x00522c50`, `0x00532ec0`, `0x0065d010`, `0x00709ad0`.
**Nálunk:** `backup/szuro.py:52-65` ("kép" = nem videó, `media_kind_of`).
**Kérdés:** melyik fájltípus melyik kódot kapja, és egyezik-e a két halmaz.
**Út:** a típuskód-kiosztó függvény keresése (a `[képrekord+0xf8]` oszlop
írója), `kutatasi_dosszie.py` + `pe_dis.py`.

## 6. Mérés: a két futtatás

Környezet: a főmásolat `.venv`-je (az `index` csomag importjához `watchdog`
kell), a munkafa `.bt/` mappájából, `python -I` mellett. Mindkét szkript 20-25 sor, a
`picasapy.backup.tervezd_meg` és `futtasd` valódi hívásával, memória-adatbázison.

```
M1: forrás 0444 -> futtasd -> forrás módosul (0444 marad) -> futtasd -> tervezd_meg
    kimenet: 1. futás: tervezett 1 átmásolt 1 cél mód 0o444
             2. futás: tervezett 1 átmásolt 0 cél tartalma: b'ELSO-VERZIO'
             3. terv:  tervezett 1 kihagyott 0
M2: kép + .picasa.ini("backuphash=100") -> futtasd -> ini("caption=...", "backuphash=200") -> tervezd_meg
    kimenet: 1. futás után a célban: ['.picasa.ini', 'a.jpg', 'files.txt']
             metaadat-szerkesztés után: tervezett 0 kihagyott 1
```

Az M1 és M2 szkriptjét a jegy tesztjeinek kell megtestesítenie (J1, J2).

## 7. Bizonyítottsági fok

| állítás | fok |
|---|---|
| egyetlen belépési pont, `thumbui/backup` rejtett (B1, B2; `0x005cbdee`, `0x005db77c`, `thumbui.tre:96`) | **megerősített** (két függvény, egyetlen közvetlen azonosító-előfordulás, a `.tre` megjegyzés) |
| a menü-engedélyezés feltétele (B3, 4.2) | **megerősített** a kifejezésre; **erős** a `[edi+0x30f4]` jelentésére (az `ajandek-cd-kimenet.md` 12.3 alapján); az `[esp+0x20]` jelentése **NINCS MEG** |
| a "mentetlen" döntés (E1, 4.1) | **megerősített** (utasítások olvasva, a két oszlopnév és az ágak) |
| a lánc "szerkesztés -> sima `backuphash` -> újra mentendő" (E3) | **erős**: két fél olvasva, az élő igazolás hiányzik (J7/4) |
| az alapértelmezett készlet automatikus létrehozása és a `LastBkSet` (W2, 4.3) | **megerősített**: a vezérlési lánc **és** az élő felvétel egybevág |
| az írásvédett cél (H1) | **megerősített** az eredetire (`biztonsagi-mentes.md` 11.1/d), **mért** a nálunk-oldalra (M1) |
| a hely-előellenőrzés (H3) | **erős** a viselkedésre; az operandusok **NINCS MEG** |
| a hibás másolás bélyegzése az eredetiben | **feltételes** (ld. 8.) |

A **független újralevezetés** (#140) a lelet-jegyek megnyitása előtt a hívó
teendője; ezt a kör nem futtatta.

## 8. Nyitott kérdések mérlege

`3 nyílt (nevesített, felvehető jegytörzsben: J7, J8) · 9 lezárva · 0 blokkolt · 2 hatókörön kívül · 0 "csak nyitva"`

| kérdés | állapot |
|---|---|
| mely belépési pontok vannak | **LEZÁRVA**: egyetlen, a Tools menü (B1, B2) |
| mikor tiltott a menütétel | **LEZÁRVA** (B3, 4.2) |
| mi dönti el, hogy egy kép mentetlen | **LEZÁRVA** (E1, 4.1) |
| mi történik üres készletlistánál és újranyitáskor | **LEZÁRVA** (W2, 4.3) |
| mi történik írásvédett célfájllal | **LEZÁRVA** (H1, M1) |
| mi történik, ha a cél megnyitása sikertelen | **LEZÁRVA** (H2) |
| van-e hely-előellenőrzés | **LEZÁRVA** a viselkedésre (H3); az operandusok J6-ban jelölve |
| mit tesz a Mégse | **LEZÁRVA** (W6) |
| van-e Picasán belüli visszaállítás | **LEZÁRVA**: nincs (H7) |
| a hibás másolású fájlt bélyegzi-e az eredeti | **HATÓKÖRÖN KÍVÜL**: a másoló nem állít tétel-jelzőt (a `0x00677a70` utasításai között nincs tétel-írás, mért), a bélyegzőt csak a `+0x30` 2-es bitje kapuzza, az írója **NINCS MEG**. A mi viselkedésünk nem függ tőle: a hibás fájlt **nem** bélyegezzük (J2/c). Döntés: ez a kör, 2026-11-20 (az eredeti feltételezett hibáját szándékosan nem követjük) |
| mit jelent a `<készlet>-backuphash == 0xFFFF` | **HATÓKÖRÖN KÍVÜL**: a mi író sosem ad `0xFFFF`-et, az olvasó paritásból kihagyja (J2/a); ugyanaz a döntés. Út, ha mégis kell: a `0x006a5a60` hívóinak vizsgálata |
| **mappába mentésnél van-e `$Application Data\…\contacts\backup.xml` (E7)**, a `files.txt` útvonal-stílusa, a kijelölés a nyitáskor, az állapotszövegek helye | **NYÍLT, J7** |
| a 12 típuskód és a "Minden kép (videók nélkül)" szűrő egyezése | **NYÍLT, J8** |
| **a lánc élő igazolása** (4.1: felirat-szerkesztés után újra szerepel-e) | **NYÍLT, J7/4** |

## 9. Amit KIZÁRTAM

- **"Több belépési pont van (eszköztár, helyi menü, gyorsbillentyű)"**:
  elvetve, B2 (a gomb `m_hidden`, két hivatkozó függvény, egy azonosító-előfordulás).
- **"Az `auto_backup_prompt` a mentés belépési pontja"** és **"a `desktop_backup`
  a készletek tárolója"**: elvetve, B5 (Google Fotók, online).
- **"A `RestoreDialog::*` a `Picasa3.exe` része"**: elvetve, H7 (az index nem
  ismeri; a `PicasaRestore.exe` szövegei).
- **"A mentés kimenete a `Picasa2Backups` mappa"**: a 2026-09-02-i helyesbítés
  már kizárta (`biztonsagi-mentes.md` 1.1).
- **A 2026-09-03-i és 2026-09-05-i "Nálunk: nincs" sorok** (`biztonsagi-mentes.md`
  6., 12.7, 15.4, 15.9): **elavultak**, a mai kód ezeket megvalósítja. A
  jelölésük a hívó teendője (ez a lap nem módosítja azt a lapot).

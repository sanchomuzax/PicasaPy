# Biztonsági mentés — a MŰKÖDÉS (`publish/backup*`, `backups.xml`)

**Mi ez:** a Picasa 3 „Biztonsági mentés" funkciója (Eszközök menü,
`eMenuTools::ID_TOOLS_BACKUP`). A [`picasa-menu-parancsok-viselkedes.md`](picasa-menu-parancsok-viselkedes.md)
**50.2** a *fogalmat* és a *felületet* rögzítette (nevesített készletek,
új/szerkeszt/töröl, `LastBkSet`). **Ez a lap azt írja le, MIT ÍR A LEMEZRE** —
hova, milyen néven, milyen szerkezetben, és hogyan tudja, mi van már mentve.

Jegy: **#440**.

> ⭐ **A LEMEZRE ÍRÁS oldala külön lapon:**
> [`ajandek-cd-kimenet.md`](ajandek-cd-kimenet.md) — a kimeneti
> beállítások (16 kulcs, köztük az `option_backup`), a lemez önjáró
> tartalma és a **honosított mappanevek** („Biztonsági mentés" / „Képek")
> ott állnak. A két funkció **ugyanazt a csővezetéket** használja; a
> `[ebp+0x13f]` jelzőbit dönti el, melyik ág fut.

## 1. Két állományt ír, két külön helyre

| állomány | hol | mit tartalmaz | író/olvasó |
|---|---|---|---|
| **`backups.xml`** | a Picasa adatmappa **`db3`** almappájában | a **készlet-definíciók** | író `0x006759c0` (1723 b) · olvasó `0x00676910` (223 b) |
| **`files.txt`** | a mentés **célmappájában** | a másolt fájlok listája | `0x00677a70` (3005 b) |

### 1.1 A hely — `…\Google\Picasa2\db3\` (2026-09-02: MEGVAN)

> ⛔ **HELYESBÍTÉS — a lap korábbi 1.1 szakasza KÉT dologban tévedett.**
> Ott ez állt: „a `Picasa2Backups` mappában", és hogy a szülőkönyvtár
> azért nincs mérve, mert a `0x009bfde0` sztring nélküli útvonal-építő.
> **Mindkettő megdőlt** — a bizonyíték lent.

**1. A `0x009bfde0` NEM útvonal-építő, hanem az XML BEHÚZÁSA.**
A 135 bájtos függvény (`0x009bfde0`) mindössze ennyit tesz: 0x50 (**80**)
szóközzel tölt fel egy puffert (`0x009bfe40`: `push 0x50; push 0x20`),
majd a `min(hossz/2, 0x4f)` pozíción lezárja (`0x009bfe4d`–`0x009bfe5c`).
**Hívója az `0x009bfed0`**, ami a nyitó XML-elemet írja
(`%s%s%s%s%s<%s` / `%s<%s`) — a `0x009bfde0` adja hozzá a mélységnek
megfelelő behúzást. Tíznél több, egymástól független hívója van a
binárisban.

**2. A `Picasa2Backups` NEM mappanév, hanem az XML GYÖKÉRELEME.**
A `0x00675af5`-nél a literál (14 karakter) a `0x00985ff0` sztring-építőn
át a **`0x009bfed0`**-be megy — vagyis a fájl első sora
`<Picasa2Backups>`, ugyanúgy, ahogy az `.mxf`-é `<CTransTimeline>`
(2.4/b) és a `.cxf`-é a saját gyökere.

**3. A tényleges könyvtár: a `#db3\` útvonal-token.**

| hívás | mit ad át | cím |
|---|---|---|
| **olvasás** | `mov ecx, 0xc7eeb8` (`#db3\`), majd `call 0x676910` | `0x00670aa8`–`0x00670aaf` |
| **írás** | `push 0xc7eeb8` (`#db3\`), majd `call 0x6759c0` | `0x00670ca8`–`0x00670cae` |

A feloldást a `0x00991b00` (`ytFileUtils.cpp`, 641 b) végzi. **Ugyanez a
helper nyitja a `thumbindex.db`-t** (`0x004f47bf`) **és a
`runtime\winedisable.txt`-t** (`0x006e0709`) — mindkettő helye ismert a
saját mintaadatunkból: `research/testdata/Picasa2/db3/thumbindex.db`,
illetve `…/Picasa2/runtime/`.

⇒ **`backups.xml` és `replicates.xml` a `…\Google\Picasa2\db3\` mappában
van**, a `thumbindex.db` és a `.pmp`-k mellett. *Bizonyítottság:
**megerősített** a `#db3\` átadására; **erős** a `db3` teljes útvonalára
(a mintaadat és a `picasa-indulas.md` adatmappa-mérése alapján).*

### 1.1/b Hogyan nyitja meg a fájlt

- **mód: `"wb"`** (`0x00c7faa4`, `0x00675a50`) — **teljes újraírás**,
  nem hozzáfűzés; a készletlista minden mentéskor újra kiíródik.
- **előbb leveszi a csak-olvasható jelzőt:** `GetFileAttributes`
  (`0x00d694bc`), és ha a 1-es bit áll, `SetFileAttributes` a bit nélkül
  (`0x00d69514`) — `0x00675a18`–`0x00675a2c`.

### 1.2 UGYANEZ a függvény írja a `replicates.xml`-t is

```
0x006759e6  cmp byte ptr [ebp+0x13f], bl   ; egy jelzőbit az objektumon
0x006759ee  mov ecx, 0xca5ba4              ; "replicates.xml"
0x006759f3  jne 0x6759fa                   ;   … ha a bit ÁLL, ez marad
0x006759f5  mov ecx, 0xca5bb4              ; "backups.xml"   (ha a bit NULLA)
```

⇒ a **készlet** és a **replikáció** ugyanazt a szerkezetet használja, csak
más fájlnéven. Aki a mentést megvalósítja, egy szerkezetet ír meg kettő
helyett.

## 2. A `backups.xml` mezői — a bejárás sorrendjében

A függvény a `[ebp+0x2b0]`-ból induló rekordtömböt járja be, és
rekordonként ezeket a kulcsokat írja (a hosszakat a bináris adja meg, a
`0x00985ff0` sztring-építő második paramétereként):

| kulcs | hossz | cím | mikor kerül ki | jelentés |
|---|---:|---|---|---|
| `setname` | 7 | `0x00ca5bd8` | mindig | a készlet neve |
| `diskroot` | 8 | `0x00ca5be0` | **csak ha nem üres** (`0x00675c52` két ellenőrzése) | a mentés célmappája |
| `filter` | 6 | `0x00c843d8` | mindig | a készlet szűrője |
| `type` | 4 | `0x00c83fe4` | mindig | ld. lent |

### 2.1 A `type` — HÁROM tartalom-mód, egy egész mezőből

A rekord `+0x0c` mezője (`0x00675cdd`–`0x00675d74`) dönti el az értéket:

| a `+0x0c` értéke | a kiírt érték | cím |
|---:|---|---|
| **0** | `bkallfiles` | `0x00ca5bec` |
| **1** | `bkonlypics` | `0x00ca5bf8` |
| **2** | `bkonlyexif` | `0x00ca5c04` |

⇒ a mentés **nem csak „minden fájl"**: külön mód van a **csak képekre** és
a **csak EXIF-esekre**. A háromból nálunk **egy sincs**.

## 3. A másolás menete és a HÁROM állapotszöveg

A másoló `0x00677a70` a célmappa útvonalához hozzáfűzi a **`\files.txt`**
nevet (`0x00677ada`, a sztring `0x00ca5c78`, hossz 10), majd végigmegy az
elemeken. A folyamat három, egymást követő állapotot mutat:

| sorrend | szövegtár-kulcs | angol | **hivatalos magyar** |
|---|---|---|---|
| 1. | `il_BurnPanel::BackupCopy::1` | *Copying (%1$d/%2$d) files* | **„Fájlok másolása (%2$d/%1$d)"** |
| 2. | `il_BurnPanel::BackupCopy::2` | *Updating Backup Info* | **„Biztonsági mentési adatok frissítése"** |
| 3. | `il_BurnPanel::BackupCopy::3` | *Backup Complete* | **„A mentés elkészült"** |

⚠️ **A magyar felcseréli a két számot** (`%2$d/%1$d`) — vagyis magyarul
*„Fájlok másolása (összes/kész)"*. Ha a megvalósítás pozíció szerint
helyettesít, **fordítva fog számolni**.

### 3.1 A háttérfolyamat állapotai (`0x00678630`, 1246 b)

| kulcs | angol | magyar |
|---|---|---|
| `il_BurnPanel::BackgroundProc::1` | Backup in Progress | **„Biztonsági mentés folyamatban"** |
| `il_BurnPanel::BackgroundProc::2` | CD in Progress | *(ugyanitt)* |
| `il_BurnPanel::BackgroundProc::3` | Preparing Files %d%% | *(ugyanitt)* |
| `il_BurnPanel::BackgroundProc::4` | Not Enough Disk Space to Backup Files | **„Nincs elegendő hely a fájlok biztonsági mentéséhez"** |
| `il_BurnPanel::BackgroundProc::6` | Disc Done | *(ugyanitt)* |

⇒ **a lemezhely-ellenőrzés az eredetiben megvan**, és a mentés és a
CD-írás **ugyanazon a háttérfolyamaton** osztozik.

## 4. Az alapértelmezett célmappa — és hogy a NEVE fordított

Az „új készlet" párbeszéd (`0x00678be0`, 507 b) az alapértelmezett
célmappát a szövegtárból veszi:

| kulcs | angol | **magyar** |
|---|---|---|
| `il_BurnPanel::DefBkFolder` | `\Picasa Backup\` | **`\Picasa biztonsági másolat\`** |
| `il_BurnPanel::bksetname` | My Backup Set | **„Saját mentési készlet"** |
| `il_NewBkDialog::EditTitle` | Edit Backup Set | **„Mentési készlet szerkesztése"** |
| `il_NewBkDialog::EditOKButton` | Change | **„Módosítás"** |

⇒ **a mappa neve honosított**, tehát magyar Picasánál a lemezen
`Picasa biztonsági másolat` néven jön létre. Ugyanez a függvény kéri a
Wine útvonal-fordítását (`wine_get_unix_file_name`, ld. 50.3).

## 5. ⛔ NÉVCSAPDA: „A program biztonsági másolatot készít ezekről a fájlokról"

A `0x0053a790` (2880 b) ugyanezt a szót használja, de **más funkció**: ez a
**„Mentés lemezre?"** párbeszéd (`CThumbUI::FileSave::message`), ami a
szerkesztések véglegesítésekor jelenik meg, és az **eredeti fájl
félretételéről** szól (`.picasa_originals`), nem a mentés-készletekről.

| kulcs | magyar |
|---|---|
| `CThumbUI::FileSave::messagetagX` | **„A program biztonsági másolatot készít ezekről a fájlokról."** |

**Aki a #440-et építi, ne ezt keresse** — és fordítva: aki a „Mentés
lemezre" ágon dolgozik, ne higgye, hogy a mentés-készlethez nyúl.

## 6. Eredeti / nálunk / teendő

A „nálunk" oszlop **mérés** (`cf48cf39`).

| | eredeti (mért) | nálunk (mért) | teendő |
|---|---|---|---|
| készlet-definíciók tárolása | **`backups.xml`** a `Picasa2Backups` mappában | **nincs** (`grep -rn 'backups.xml\|Picasa2Backups' src/` → 0) | formátum a 2. szakasz szerint |
| a másolt fájlok listája | **`files.txt`** a célmappában | **nincs** (`grep -rn 'files.txt' src/` → 0) | felvenni |
| tartalom-mód | **három** (`bkallfiles` / `bkonlypics` / `bkonlyexif`) | **nincs** | három mód |
| célmappa alapértéke | honosított: **`\Picasa biztonsági másolat\`** | **nincs** | honosított név |
| lemezhely-ellenőrzés | **van** (`BackgroundProc::4`) | **nincs** | felvenni |
| folyamatszöveg | három állapot, magyarul is | **nincs** | a mért szövegek |
| `replicates.xml` | **ugyanaz a szerkezet** | nincs | egy író, két név |

**Mérés módja nálunk**, két lekérdezés-alakkal:

1. `grep -rn 'backups\.xml\|Picasa2Backups\|files\.txt\|bkallfiles' src/` →
   **0 találat**;
2. kontroll: `grep -rniE '\bbackup' src/ --include=*.py --include=*.qml` →
   **79 találat**, de mind az **`.ini`-írás** biztonsági másolata
   (`ini/io.py` `backup=True`, és az azt hívó `fileops/copy.py`,
   `move.py`, `rename.py`) vagy a `backuphash` ini-kulcs — **egyik sem a
   mentés-készlet**.

## 7. Nyitott kérdések mérlege

`0 nyílt · 8 lezárva · 2 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| hova írja a készleteket | **LEZÁRVA** — `backups.xml`, a **`db3`** mappában (1.1) |
| milyen mezőkkel | **LEZÁRVA** — `setname` · `diskroot` (feltételes) · `filter` · `type` (2.) |
| hány tartalom-mód van | **LEZÁRVA** — három (2.1) |
| mi a célmappa alapértéke | **LEZÁRVA** — honosított `\Picasa biztonsági másolat\` (4.) |
| mit ír a célmappába | **LEZÁRVA** — `files.txt` (3.) |
| **melyik könyvtárban van a `backups.xml`** | **LEZÁRVA (2026-09-02)** — a `#db3\` token (`0x00c7eeb8`), átadva írásnál `0x00670ca8`, olvasásnál `0x00670aa8`. **A korábbi „`Picasa2Backups` mappa" olvasat MEGDŐLT** — az a fájl XML-gyökéreleme (1.1). |
| **hogyan tudja, mi van már mentve** | **LEZÁRVA (2026-09-02)** — adatbázis-címke, `BKTag ` + a készlet neve (9.) |
| hogyan nyitja a fájlt | **LEZÁRVA (2026-09-02)** — `"wb"`, előtte leveszi a csak-olvasható jelzőt (1.1/b) |
| **a `files.txt` SORFORMÁTUMA** | **BLOKKOLT, de SZŰKÍTVE (2026-09-02)** — a **megnyitás módja most már mérve** (11.1), a soronkénti írás azonban továbbra sem olvasható ki: a `0x00677f6d` írás-hívás **belső függvénymutatón** át megy (`0xd69518`), nem nevesített importon, ezért a névre keresés nem talál rá. **Megszerzés:** a `0x00677a70` célzott dekompilációja (a `0x00677f6d` hívás argumentumaival), vagy egy valódi `files.txt` egy gépről, ahol futott a mentés. |
| **a `BKTag` címke a `.picasa.ini`-be is kikerül-e** | **BLOKKOLT** — a címke létezése mérve (9.), a TÁROLÓJA nem. ⚠️ **A korpusz nem tudja eldönteni:** a `BKTag`-re nulla találat, de a `keywords=` sorra **is** nulla — a korpusz kulcsszavakat egyáltalán nem tartalmaz, tehát a hiány nem bizonyíték. **Megszerzés:** a `0x00670b25` utáni felhasználó dekompilációja, vagy egy `.picasa.ini` olyan gépről, ahol futott a mentés. |
| **a webre töltés (`replicate`) ága** | **HATÓKÖRÖN KÍVÜL** — a Picasa Web Albums / Google Fotók szolgáltatás megszűnt; a szövegek és a kulcsok a 10. szakaszban a teljesség kedvéért állnak. *(Ez a lap rögzíti a döntést; a `publish` sáv mentés- és CD-ága ettől függetlenül ÉLŐ.)* |
| **mit csinál a Wine-ág másképp** | **HATÓKÖRÖN KÍVÜL** — a `0x00678be0` Wine alatt más célmappát épít (`wine_get_unix_file_name`), de mi **natív Linuxon** futunk, nem Wine alatt; a mi célmappánk a rendszer saját konvenciója szerint áll elő. |

## 8. Amit KIZÁRTAM

- **„a `backuphash` ini-kulcs mondja meg, mi van már mentve"** — nem: a
  `backuphash` az ÍRÁS IDŐPONTJÁBÓL képzett 16 bites érték
  ([`picasa-ini-format.md`](picasa-ini-format.md), #643), nem tartalom-hash
  és nem mentés-nyilvántartás.
- **„a »biztonsági másolat« szöveg a mentés-készletekhez tartozik"** — az
  5. szakasz névcsapdája: a `CThumbUI::FileSave::messagetagX` a
  szerkesztés-mentés párbeszédé.
- **„a `0x009bfde0` útvonal-építő"** — **MEGDŐLT (2026-09-02):** a 135
  bájtos függvény az **XML behúzását** állítja elő (80 szóköz, a mélységre
  csonkolva), és a `0x009bfed0` elem-író hívja. Az 1.1 mondja el, mi
  döntötte el.
- **„a `Picasa2Backups` egy mappa neve"** — **MEGDŐLT (2026-09-02):** a
  `backups.xml` / `replicates.xml` **XML-gyökéreleme**. A tényleges mappa
  a `db3`.
- **„a `publish` panel egésze halott, mert megszűnt a Picasa Web Albums"** —
  az 50.1 már kizárta; ez a lap a mentés-ág **élő** működését adja.

*Bizonyítottsági fok: **megerősített** a fájlnevekre, a négy mezőre, a három
tartalom-módra, a folyamatszövegekre és a honosított mappanévre (a
sztringek és a rájuk mutató utasítások olvasva); **feltételes** a
`Picasa2Backups` szülőkönyvtárára; a `files.txt` **tartalma** nincs mérve.*

## 9. AZ INKREMENTALITÁS MECHANIZMUSA — `BKTag <készletnév>` (2026-09-02)

A panel azt ígéri, hogy *„A Picasa most azokat a fájlokat jeleníti meg,
amelyekről korábban nem készült biztonsági másolat"* (`publish/backuptext2`).
Eddig **nem volt igazolva, mi tartja nyilván**. Most megvan:

**Minden mentési készlethez egy adatbázis-CÍMKE tartozik, `BKTag ` +
a készlet neve.**

| lépés | bizonyíték |
|---|---|
| a `"BKTag "` literál (6 karakter) sztringgé alakul | `0x00670b03`–`0x00670b15` (`0x00ca4698`, `0x00985ff0`, hossz **6**) |
| **összefűzés a készlet nevével** (`0x00408760`) | `0x00670b25` |
| átnevezéskor `"BKTag %s"` formátummal áll elő | `0x00679ca0` (`0x00ca614c`) |
| hiba esetén: **„A mentési készletet nem lehet átnevezni"** (`il_NewBkDlgRenameError`) | `0x00679ca0` |

⇒ **A „mi van már mentve" kérdést nem egy külön nyilvántartás dönti el,
hanem a képekre tett címke.** A nálunk erre használható megfelelő a
`.picasa.ini` `keywords=` / a címke-index — a fejlesztésnek NEM kell külön
mentés-adatbázist építenie.

⚠️ **Amit ez NEM mond meg:** hogy a címke a `.picasa.ini`-be vagy csak az
SQLite-indexbe kerül-e. Lásd a 7. szakasz mérlegét.

### 9.1 Az utoljára használt készlet és az alapértelmezett név

| mit | hol | érték |
|---|---|---|
| az utoljára használt készlet | `Preferences\`**`LastBkSet`** | `0x00670cb3`, `0x006769f0`, `0x0067b7e0` |
| az új készlet alapneve | `il_BurnPanel::bksetname` | `My Backup Set` / **„Saját mentési készlet"** (`0x00670ae6`) |
| az alapértelmezett célmappa | `il_BurnPanel::DefBkFolder` | `\Picasa Backup\` / **„\Picasa biztonsági másolat\"** (`0x00678be0`) |

⭐ **A Picasa Wine alatt is felismeri magát:** a célmappát előállító
`0x00678be0` (507 b) a `kernel32`-ből a **`wine_get_unix_file_name`**
belépési pontot kéri le. Ha megvan, más útvonalat épít. *(A pontos eltérés
NINCS mérve — de a tény, hogy a Picasa Wine-tudatos, önmagában is
használható: a mi Linux-oldalunkon ugyanez a mappa NEM windowsos alakban
kell legyen.)*

## 10. A `publish` SÁV — három mód, egy felület

A `publish` panel **ugyanaz a sáv** három módban; a gombokat a
`0x00679ca0` (6960 b) építi, a „Mehet"/„Kiadás" parancsokat a
`0x0066bf90` (1593 b) fogadja.

| mód | a „mehet" gomb | a „mégse" gomb | további |
|---|---|---|---|
| **Biztonsági mentés** | `publish/backup_go` „Lemezre írás" | `publish/backup_cancel` | `backup_eject` „Kiadás", `newbackupset`, `editbackupset`, `deletebackupset` |
| **Ajándék-CD** | `publish/presentcd_go` „Lemezre írás" | `publish/presentcd_cancel` | `presentcd_eject`, `addmore` „Továbbiak hozzáadása…" |
| **Webre töltés / szinkron** | `publish/replicate_go` „OK" | `publish/replicate_cancel`, `webpublish_cancel` | `rpoptionbox1..3`, `uploadallsync`, `uploadallsize`, `uploadallaccess`, `upgradestorage` |

Közös: `publish/selectall` („Az összes kijelölése"), `publish/selectnone`,
`publish/cancel`, `publish/picsize%d`, és a
**`thumbui/publishswitcher`** — ez váltja a módokat.

### 10.1 A sáv beállításkulcsai (mind a `Preferences` alatt)

| kulcs | melyik mód | hol |
|---|---|---|
| `LastBkSet` | mentés | `0x00670cb3` |
| `CDEraseFirst` | ajándék-CD | `0x006706d0`, `0x00679ca0` |
| `CDLimitSize` | ajándék-CD | ugyanott |
| `CDSlideshow` | ajándék-CD | ugyanott |
| `CDSlideshowInclSetup` | ajándék-CD (a `setup.exe` is felkerüljön-e) | ugyanott |
| `UploadAllSize` | webre töltés | `0x006706d0` |
| `UploadAllSetting` | webre töltés | `0x00679ca0` |

### 10.2 A megerősítő párbeszédek — a hivatalos magyar szöveggel

| mikor | kulcs | magyar |
|---|---|---|
| készlet törlése | `il_NewBkDialog_delete` | **„Biztosan törli a(z) »%s« mentési készletet?"** |
| a készlet-párbeszéd címe | `il_NewBkDialogTitle` | **„Mentési készlet"** |
| a szerkesztő címe / gombja | `il_NewBkDialog::EditTitle` / `::EditOKButton` | **„Mentési készlet szerkesztése"** / **„Módosítás"** |
| átnevezési hiba | `il_NewBkDlgRenameError` | **„A mentési készletet nem lehet átnevezni"** |
| feltöltés hibája / címe | `il_BurnPanel::UploadAllError` / `::UploadAllTitle` | **„Hiba történt az összes feltöltése során: %d"** / **„Az összes feltöltése"** |

⚠️ **Az online eltávolítás kérdése KÉT alakban létezik** — ugyanaz a
jelenség, mint a rács üres állapotánál (`racs-ures-allapot.md`):

| kulcs | angol | magyar |
|---|---|---|
| `RemoveOnlineSelectedAlbums` | Remove these albums from Picasa Web Albums? | **„Eltávolítja ezeket az albumokat a Picasa Webalbumokból?"** |
| **`RemoveOnlineSelectedAlbumsES`** | Remove these albums from Google Photos? | **„Eltávolítja ezeket az albumokat a Google Fotókból?"** |

Az `ES` utótagú a **későbbi** (Google Fotók korszakbeli) változat; a
kettő közti választás ugyanaz a mechanizmus, mint a `LastUserESState`-nél.
**A webes ág megvalósítása HATÓKÖRÖN KÍVÜL** (a szolgáltatás megszűnt) —
a szövegek a teljesség kedvéért állnak itt.

### 10.3 A sáv TÁJÉKOZTATÓ szövegei — teljes lista

Ezeknek **nincs bináris címük**: a `respack.yt` szöveg-rétegei hordozzák
őket, a hivatalos magyar alak a `referencia/panel-feliratok-hu.tsv`-ben
áll (a sorszám a bizonyíték).

| elem | magyar szöveg | forrás |
|---|---|---|
| `publish/backupcdheader2` | „Mappák és albumok kijelölése biztonsági másolat készítéséhez" | `panel-feliratok-hu.tsv:5078` |
| `publish/backuptext2` | „A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban nem készült biztonsági másolat." | `:5080` |
| `publish/backuptext3` | „Jelölje ki azokat a mappákat, amelyekről biztonsági másolatot szeretne készíteni, vagy »Az összes kijelölése« gombra kattintva az összes elemet jelölje ki." | `:5081` |
| `publish/giftcdtext` | „A program a fent pipával kijelölt elemeket másolja az ajándék CD-re. További elemek felvételéhez kattintson az alábbi »Továbbiak hozzáadása« gombra." | `:5061` |
| `publish/backup_help` | „Súgó" | `:5083` |
| `publish/presentcd_help` | „Súgó" | `:5068` |
| `publish/presentcd_cancel` | „Mégse" | `:5070` |
| `publish/label_rpoptionbox1` | „Feltöltés" | `:5092` |
| `publish/label_rpoptionbox2` | „Opciók módosítása" | `:5094` |
| `publish/label_rpoptionbox3` | „Eltávolítás: online elemek" | `:5096` |
| `publish/rpoptionbox1` (buboréksúgó) | „A program feltölti a kijelölt mappákat és/vagy albumokat" | `:5093` |
| `publish/rpoptionbox2` (buboréksúgó) | „A program a jobb oldali menükben választott opciókkal frissíti a kijelölt mappákat és/vagy albumokat az interneten" | `:5095` |
| `publish/rpoptionbox3` (buboréksúgó) | „A program eltávolítja a kijelölt mappákat és/vagy albumokat a Picasa Webalbumokból" | `:5097` |

⚠️ **A `backuptext2` a 9. szakasz ígérete:** ezt a mondatot a `BKTag`
címke teszi igazzá — enélkül a szöveg hazudna.

**A `publish/replicate_button_group`** felirat nélküli tartó (a három
`rpoptionbox` rádiócsoportja); a **`publish/replicate_go`** felirata `OK`,
a **`publish/webpublish_cancel`** és a **`publish/replicate_cancel`**
„Mégse". Mindhárom a webes ághoz tartozik ⇒ **hatókörön kívül** (7.).

---

## 11. A `files.txt` MEGNYITÁSA és a replikáció ikertestvére (2026-09-02)

### 11.1 A `files.txt`-t a Picasa NEM írja felül — OLVASSA is

A 7. szakasz sorformátum-kérdése továbbra is nyitva van, de a **megnyitás
módja** mérve van, és önmagában is megválaszol egy fontos viselkedési
kérdést.

A másoló függvény (`0x00677a70`) a célmappa útvonalához hozzáfűzi a
`\files.txt`-t (`0x00677ada`, a sztring `0x00ca5c78`, hossz 10), majd:

```
0x00677de6   call [0xd69520]        ; CreateFileW-alak, argumentumok jobbról balra:
             push edi   (0)         ;   hTemplateFile
             push 0x80              ;   FILE_ATTRIBUTE_NORMAL
             push 4                 ;   dwCreationDisposition = OPEN_ALWAYS
             push edi   (0)         ;   lpSecurityAttributes
             push 3                 ;   FILE_SHARE_READ | FILE_SHARE_WRITE
             push 0xC0000000        ;   GENERIC_READ | GENERIC_WRITE
             push esi               ;   a fájl útvonala
0x00677dec   cmp eax, -1            ; INVALID_HANDLE_VALUE ellenőrzés
0x00677e31   (hibaág) ugyanez, de dwCreationDisposition = 3 (OPEN_EXISTING)
```

Három dolog következik ebből, mérésként:

1. **`OPEN_ALWAYS`** — ha a fájl létezik, megnyitja; ha nem, létrehozza.
   **Nem csonkolja** (`CREATE_ALWAYS` = 2 lenne).
2. **`GENERIC_READ | GENERIC_WRITE`** — a Picasa **vissza is olvassa** a
   fájlt, nem csak ír bele. Ez illeszkedik a mentés inkrementális
   jellegéhez (9. szakasz, `BKTag`): a `files.txt` a célmappában lévő
   tartalom **nyilvántartása**, amit menetenként frissít.
3. A **csak-olvasható jelzőt itt is leveszi**, ugyanazzal a mintával, mint a
   `backups.xml`-nél (1.1/b): `0x0067834e` lekérdezi az attribútumokat,
   `test al, 1` vizsgálja a `FILE_ATTRIBUTE_READONLY` bitet,
   `and eax, 0xfffffffe` törli, `0x00678362` visszaírja.

> **Bizonyítottsági fok: megerősített** a megnyitási módra (kiolvasott
> argumentum-konstansok). **A sorformátum továbbra sem ismert** — ld. lent,
> miért nem találta meg a szokásos keresés.

**Miért nem elég a sztring-keresés:** az író hívás
(`0x00677f6d`, `call dword ptr [0xd69518]`) **belső függvénymutatón** át megy.
A PE import-táblájának feldolgozásakor a `0xc4025c` → `KERNEL32!GetLastError`
és a `0xc40474` → `KERNEL32!SetFileTime` **feloldódik**, a `0xd69514`,
`0xd69518`, `0xd69520` és `0xd694bc` viszont **nem szerepel az
import-táblában** — futásidőben töltött mutatók. Ezért nincs se
formátum-sztring, se importnév, amire a szokásos lánc ráakadna.

### 11.2 A `replicates.xml` — ugyanaz az író, ugyanaz az öt mező

Az 1.2 eddig annyit mondott, hogy „ugyanez a függvény írja". A mezőlista
mérve **azonos**: a `0x006759c0` (1723 b) sztringkészlete
**egyetlen** halmaz mindkét fájlhoz —

```
Picasa2Backups   (XML-gyökérelem, közös)
setname · diskroot · filter
bkallfiles · bkonlypics · bkonlyexif   (a három tartalom-mód)
```

és az olvasó is közös: `0x00676910` (223 b) mindkét fájlnevet ismeri; a
mező-feldolgozás `0x00676170` (a három mód) és `0x00676760`
(`setname` / `diskroot`).

⚠️ **A `diskroot` csak akkor íródik ki, ha nem üres** (2. szakasz,
`0x00675c52`). A replikációs készletnél tehát ez a mező hiányozhat — a
beolvasónak fel kell készülnie a hiányára.

**Az utoljára használt cél két külön kulcsban él** (`0x0067b7e0`):

| kulcs | mihez |
|---|---|
| `Preferences\LastBkSet` | az utoljára használt **mentési** készlet (9.1) |
| `Preferences\LastReplTarget` | az utoljára használt **replikációs** cél |

### 11.3 A replikáció NÉGY állapotszövege — hivatalos magyar fordítással

| erőforrás-azonosító | angol | magyar |
|---|---|---|
| `il_CReplicateStatusRep` | Replicating | **Replikáció** |
| `il_CReplicateStatus` | %d items scheduled to be copied | **%d elem van másolásra ütemezve** |
| `il_CReplicateStatusItems` | %1$d of %2$d items | **%1$d / %2$d elem** |
| `il_CReplicateStatusDone` | Done | **Kész** |

(`referencia/stringres-en-hu.tsv` 3156–3159. sor.)

### 11.4 ⭐ A `publish` sáv STRUKTURÁLIS KULCSA: `publish/%s_go`

A parancsdiszpécser (`0x005fa770`, 8913 b) a `publish` sáv gombjait
**összerakott névvel** szólítja meg:

```
publish/%s_go        publish/%s_cancel
```

ahol a `%s` a **három mód** egyike, és mindhárom névként ott áll ugyanabban
a függvényben: **`backup` · `presentcd` · `replicate`**.

Ez két dolgot magyaráz meg egyszerre:

1. **A `publish` sáv tényleg egy panel három üzemmóddal** (10. szakasz), és
   ezt most a *kód* is igazolja, nem csak az elemnevek.
2. **Ezért látszik több `publish`-elem „hiányzónak"** a lefedettségi
   mérésben: a nevük a binárisban **nem szerepel literálisan**. Ez pontosan
   az a hamis-pozitív osztály, amit a
   [`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md) 19.
   szakasza „dinamikusan összerakott név" néven ír le — itt egy konkrét,
   mért példával.

Jegy-komment: **#440**.

---

## 12. A LEMEZRE ÍRÁS menete — kapacitás, több lemez, ISO (2026-09-03)

> **Bizonyítottság: megerősített.** Minden szám a diszasszemblátumból, cím
> szerint; minden felhasználói szöveg a `referencia/stringres-en-hu.tsv`
> hivatalos magyar sorából. A 10. szakasz a `publish` SÁVOT írta le
> (gombok, kulcsok); ez a szakasz azt, ami az **OK megnyomása UTÁN** történik.

### 12.1 A lemez használható kapacitása — `0x0066be90` (MÉRT KÉPLET)

A `publish` sáv ezt a függvényt hívja (`0x006740fd`), és 64 bites bájtszámot
kap vissza.

```asm
0x0066bec7  cmp dword ptr [esi+0x94], 0x214      ; kétrétegű lemez?
0x0066bed3  mov dword ptr [ebx+0x180], 0xfd800000 ;   -> 0x1_FD800000
0x0066bedd  mov dword ptr [ebx+0x184], 1          ;      = 8 547 991 552 bájt
…
0x0066bf12  mov eax, 0x29032800                   ; tartalék alapérték
0x0066bf35  push 0x800                            ; szektorméret = 2048
0x0066bf3c  call 0xbf7680                         ; [esi+0x90] × 2048  (64 bites)
0x0066bf47  call 0x666400                         ; DVD-e?
0x0066bf50  add esi, 0xffc18000                   ;   igen: −4 096 000 bájt
0x0066bf58  add esi, 0xfff9c000                   ;   nem:  −409 600 bájt
0x0066bf5e  adc edi, -1
```

| mennyiség | érték | cím |
|---|---|---|
| kétrétegű lemez kapacitása | **8 547 991 552 bájt** (`0x1_FD800000`) | `0x0066bed3`–`0x0066bedd` |
| a kétrétegűt jelző médiatípus | **`0x214`** | `0x0066bec7` |
| szektorméret | **2048 bájt** | `0x0066bf35` |
| **DVD-tartalék** (levonás) | **4 096 000 bájt** = 2000 szektor | `0x0066bf50` (`0xffc18000` = −0x3E8000) |
| **CD-tartalék** (levonás) | **409 600 bájt** = 200 szektor | `0x0066bf58` (`0xfff9c000` = −0x64000) |
| tartalék alapérték, ha a lemez kapacitása nem olvasható | **688 072 704 bájt** (`0x29032800`) | `0x0066bf12`, `0x0066bf78` |

⇒ **`használható = szektorszám × 2048 − tartalék`**, kivéve a `0x214`
típusú (kétrétegű) lemezt, ahol rögzített 8 547 991 552 bájt.

Ugyanez az öt konstans megjelenik a `0x00672380`-ban és a `0x00674460`-ban
is — ott a fordító **beágyazta** ugyanezt a számítást.

### 12.2 „DVD-e?" — `0x00666400` (54 bájt)

Igazat ad hat médiatípus-kódra: **`0x204`, `0x206`, `0x207`, `0x209`,
`0x210`, `0x214`** (`0x00666403`–`0x0066642b`). Minden más CD-ként számít
(a tartalék ekkor 409 600 bájt).

⚠️ **Amit NEM tudunk:** hogy az egyes kódok pontosan melyik lemezfajtát
jelentik (DVD−R / DVD+R / DVD-RW …). Csak a `0x214` van megfejtve
(kétrétegű, a hozzá rendelt kapacitásból). A többi öt kód jelentése
**NINCS MEG** — a megszerzés útja a `CDVDR.yti` bővítmény
(`picasa-program-resources.md` 486.) elemzése.

A médiatípus emberi nevei (`0x006665c0`):
`ytICDVDR::MTNotRec` „Not Recordable Disc" · `MTRec` „Recordable Disc" ·
`MTNotRecIncom` „Incompatible Recordable Disc" · `MTBlank`
„Blank Recordable Disc" · `MTUnknown` „Unknown".

### 12.3 TÖBB LEMEZRE osztás — a Picasa sorszámoz

A mentés **nem fér el kötelezően egy lemezen**; a felület végig kíséri a
lemezcserét. Az első becslés (`0x006740a0`, `il_BurnPanel::InitialCollect::*`,
11 kulcs), a folytatás (`0x00674460`, `InsertNext::*`, 13 kulcs):

| kulcs | hivatalos magyar |
|---|---|
| `InitialCollect::1` | „Tegyen be üres lemezt a(z) %c:\ meghajtóba" |
| `InitialCollect::2` | „Lemez felcímkézése 1. számúként" |
| `InitialCollect::3` | „Ehhez a következő szükséges: " |
| `InitialCollect::4s` / `4p` | „1 DVD %s" / „%d DVD %s" |
| `InitialCollect::5s` / `5p` | „1 CD %s" / „%d CD %s" |
| `InitialCollect::8p` | „%d CD" |
| `InitialCollect::9s` / `9p` | „ vagy 1 DVD %s" / „ vagy %d DVD %s" |
| `InitialCollect::11s` | „1 CD vagy 1 DVD %s" |
| `InsertNext::1` | „Folytatás" |
| `InsertNext::2` | „Helyezzen be egy üres lemezt a(z) %c:\ meghajtóba, majd válassza a »Folytatás« lehetőséget" |
| `InsertNext::10` | „Tegye be az utolsó üres lemezt." |
| `InsertNext::11` | „Ez lesz a(z) %d. számú lemez." |
| `InsertNext::12` | „Tegye be a következő üres lemezt." |
| `InsertNext::13` | **„Ez lesz a(z) %d. számú lemez a(z) %d darabból."** |

⇒ **A lemezek sorszámozottak, és a felület megmondja, hányból hányadik.**
Az „utolsó" külön szöveget kap.

### 12.4 ISO-kimenet — lemez helyett fájlba

| kulcs | hivatalos magyar |
|---|---|
| `InsertNext::7` | „Ezzel a művelettel létrehoz " |
| `InsertNext::7s` / `7p` | „1 ISO." / „%d ISO-fájl" |

⇒ **A Picasa lemezíró nélkül is használható**: ugyanaz a szétosztás, csak a
kimenet ISO-képfájl(ok). Ez a **mi célkörnyezetünkben (Linux/RPi5) a
megvalósítható ág** — hardver nélkül is tesztelhető.

### 12.5 Törlés-figyelmeztetés — `0x006755f0` (283 bájt)

| kulcs | hivatalos magyar |
|---|---|
| `EraseWarn::2` (cím) | „Törölhető lemez" |
| `EraseWarn::1` | „Ezen az újraírható lemezen fájlok vannak.\nA Picasa csak akkor tud a lemezre írni, ha előbb törli a tartalmát.\nTörli a lemezt?" |
| `EraseWarn::yesbutton` | „Lemez törlése" |
| `il_CancelButton` | „Mégse" |

### 12.6 Az írás ÁLLAPOTAI — `0x00672f50` (2634 bájt), 21 kulcs

| kulcs | hivatalos magyar |
|---|---|
| `WriteProgress::10` | „Felkészülés az írásra" |
| `WriteProgress::3` | „Lemez törlése" |
| `WriteProgress::103` | „Lemez törlésének ellenőrzése" |
| `WriteProgress::8` | „Írás... %.1f%% kész" |
| `WriteProgress::9` | „Írás... %2$s / %1$s" |
| `WriteProgress::4` / `::17` | „ %d másodperc van hátra" |
| `WriteProgress::101` | „Felkészülés az ellenőrzésre" |
| `WriteProgress::100` | „Ellenőrzés... %1$s/%2$s" |
| `WriteProgress::16` | „Lemez véglegesítése" |
| `WriteProgress::14` | „A lemez készen van!" |
| `WriteProgress::18` | **„Várakozás a következő lemezre"** |
| `WriteProgress::13` | **„Mentési készlet frissítése"** |
| `WriteProgress::15` | „Az írás kész!" |
| `WriteProgress::5` / `::6` | „Hiba történt a CD írása közben" / „A Picasa nem tudott megfelelően a lemezre írni" |
| `WriteProgress::1` · `::7`/`::11` · `::2`/`::12` | „%d törlése" · „%d véglegesítése" · „CDVDR időzítés" (hibakeresési naplósorok) |

⭐ Két állapot **kapcsolatot teremt a lap többi szakaszával**:
a `::18` a 12.3 lemezcseréjéé, a `::13` pedig a **9. szakasz `BKTag`
címkézését** futtatja — vagyis a készlet inkrementalitása az írás
**befejezésekor** frissül, nem az elején.

### 12.7 Nálunk — MÉRVE (2026-09-03)

| | eredeti | nálunk | teendő |
|---|---|---|---|
| lemezre írás | teljes motor (kapacitás, szétosztás, törlés, ellenőrzés) | **nincs** — a `src/` egyetlen „lemezre írás" találata a szerkesztés-mentés visszavonása (`edit/save.py:320`), nem lemezírás | a hardveres ág célkörnyezetünkben nem tesztelhető |
| ISO-kimenet | `InsertNext::7*` | **nincs** | **ez az implementálható ág** |
| kapacitás-számítás | `szektor × 2048 − tartalék` (12.1) | nincs | átvehető, hardver nélkül is |
| lemez-sorszámozás | „%d. számú lemez a(z) %d darabból" | nincs | átvehető |
| `il_BurnPanel::*` szövegek | 21 + 13 + 11 + 4 kulcs, hivatalos magyarral | csak egy komment hivatkozik rájuk (`PicasaNotifier.qml:304`) | a szövegek készen állnak

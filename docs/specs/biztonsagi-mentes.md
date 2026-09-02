# Biztonsági mentés — a MŰKÖDÉS (`publish/backup*`, `backups.xml`)

**Mi ez:** a Picasa 3 „Biztonsági mentés" funkciója (Eszközök menü,
`eMenuTools::ID_TOOLS_BACKUP`). A [`picasa-menu-parancsok-viselkedes.md`](picasa-menu-parancsok-viselkedes.md)
**50.2** a *fogalmat* és a *felületet* rögzítette (nevesített készletek,
új/szerkeszt/töröl, `LastBkSet`). **Ez a lap azt írja le, MIT ÍR A LEMEZRE** —
hova, milyen néven, milyen szerkezetben, és hogyan tudja, mi van már mentve.

Jegy: **#440**.

## 1. Két állományt ír, két külön helyre

| állomány | hol | mit tartalmaz | író/olvasó |
|---|---|---|---|
| **`backups.xml`** | a **`Picasa2Backups`** mappában | a **készlet-definíciók** | `0x006759c0` (1723 b) |
| **`files.txt`** | a **mentés célmappájában** | a másolt fájlok listája | `0x00677a70` (3005 b) |

### 1.1 A `Picasa2Backups` mappa

A név a binárisból: **`Picasa2Backups`** (`0x00ca5bc0`, 14 karakter, a
`0x006759c0`-ban közvetlenül a `0x009bfde0` hívása után fűzve).

⚠️ **A SZÜLŐKÖNYVTÁR NINCS MÉRVE.** A `0x009bfde0` (135 b) egyetlen
sztringet sem hivatkozik, tehát a mérésből nem derül ki, mihez fűzi. A
projekt korábbi mérése szerint az adatmappa `AppLocalDataPath` →
`Google\Picasa2`, és mellette áll a `Picasa2Albums`
([`picasa-indulas.md`](picasa-indulas.md)) — a `Picasa2Backups` **névalakja
ugyanaz a család**, de hogy tényleg oda kerül, **nincs igazolva**.
*Bizonyítottság: **feltételes**.*

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

`0 nyílt · 5 lezárva · 2 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| hova írja a készleteket | **LEZÁRVA** — `backups.xml`, `Picasa2Backups` (1.1) |
| milyen mezőkkel | **LEZÁRVA** — `setname` · `diskroot` (feltételes) · `filter` · `type` (2.) |
| hány tartalom-mód van | **LEZÁRVA** — három (2.1) |
| mi a célmappa alapértéke | **LEZÁRVA** — honosított `\Picasa biztonsági másolat\` (4.) |
| mit ír a célmappába | **LEZÁRVA** — `files.txt` (3.) |
| **melyik könyvtárban van a `Picasa2Backups`** | **BLOKKOLT** — a `0x009bfde0` (135 b) sztring nélküli útvonal-építő; az olcsó lánc kimerült (sztring-xref, `.tre`, a saját `research/testdata/` — ott **nincs** `backups.xml`, a tulajdonos sosem használta a funkciót). **Megszerzés:** a `0x009bfde0` célzott dekompilációja, vagy egy valódi Picasa-adatmappa, amiben futott a mentés. |
| **a `files.txt` SORFORMÁTUMA** | **BLOKKOLT** — a név és a hely megvan, a soronkénti írás a másoló ciklus mélyén van. **Megszerzés:** a `0x00677a70` (3005 b) célzott dekompilációja. Enélkül az **inkrementalitás** („a Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban nem készült biztonsági másolat") mechanizmusa sincs igazolva. |

## 8. Amit KIZÁRTAM

- **„a `backuphash` ini-kulcs mondja meg, mi van már mentve"** — nem: a
  `backuphash` az ÍRÁS IDŐPONTJÁBÓL képzett 16 bites érték
  ([`picasa-ini-format.md`](picasa-ini-format.md), #643), nem tartalom-hash
  és nem mentés-nyilvántartás.
- **„a »biztonsági másolat« szöveg a mentés-készletekhez tartozik"** — az
  5. szakasz névcsapdája: a `CThumbUI::FileSave::messagetagX` a
  szerkesztés-mentés párbeszédé.
- **„a `publish` panel egésze halott, mert megszűnt a Picasa Web Albums"** —
  az 50.1 már kizárta; ez a lap a mentés-ág **élő** működését adja.

*Bizonyítottsági fok: **megerősített** a fájlnevekre, a négy mezőre, a három
tartalom-módra, a folyamatszövegekre és a honosított mappanévre (a
sztringek és a rájuk mutató utasítások olvasva); **feltételes** a
`Picasa2Backups` szülőkönyvtárára; a `files.txt` **tartalma** nincs mérve.*

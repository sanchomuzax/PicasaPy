# Az Ajándék-CD és a mentő lemez KIMENETE (`il_BurnPanel`)

**Mi ez:** a Picasa 3 „Ajándék CD készítése…" parancsa
(`eMenuTools::…`, felirat *„Create a &Gift CD…"*, `0x00559150`) és a
biztonsági mentés **ugyanazt a kimeneti csővezetéket** használja. Ez a lap
azt írja le, **mi kerül ténylegesen a lemezre**.

Testvérlap: [`biztonsagi-mentes.md`](biztonsagi-mentes.md) (a
készlet-formátum és a másolás).
Jegyek: **#32** (Ajándék-CD) · **#440** (mentés).

## 1. ⭐ A lemez ÖNJÁRÓ — és MINDKÉT platformra

A kiírás **négy külön másoló** függvényen megy át. Mindegyik a telepítés
`cdautorun\` mappájából visz fájlokat a lemez gyökerébe:

| másoló | forrás (a telepítésben) | cél (a lemezen) |
|---|---|---|
| `0x0066fae0` (439 b) | `cdautorun\PicasaCD.exe` | `\PicasaCD.exe` |
| | `cdautorun\Picasa CD Slideshow.app` | `\Picasa CD Slideshow.app` |
| | `cdgo.ui` | `\cdgo.ui` |
| | `cdgo.tre` | `\cdgo.tre` |
| `0x0066f9f0` (232 b) | `cdautorun\PicasaRestore.exe` | `\PicasaRestore.exe` |
| | `cdautorun\Picasa Restore.app` | `\Picasa Restore.app` |
| `0x0066fca0` (308 b) | `setup.exe` | `\setup.exe` |
| | `cdautorun\Download Picasa.url` | `\Download Picasa.url` |
| `0x006919b0` (745 b) | *(generált)* | `\autorun.inf` |

⇒ **A lemezen egy Windows ÉS egy macOS diavetítő, egy Windows ÉS egy macOS
visszaállító, a Picasa telepítője és egy letöltési link van** — a
`.app`-ok mellé a `cdgo.ui`/`cdgo.tre` a vetítő saját felületleírója.

### 1.1 A forrásmappa MEGVAN nálunk — élő minta

`research/copy_Picasa_3_7/Picasa3/cdautorun/`:

```
cdgo.tre                     5 877 B
cdgo.ui                    268 503 B
Download Picasa.url             52 B
PicasaCD.exe             1 898 824 B
PicasaRestore.exe        1 091 912 B
Picasa CD Slideshow.app/     (mappa)
Picasa Restore.app/          (mappa)
```

A `Download Picasa.url` **teljes tartalma** (52 bájt, beolvasva):

```
[InternetShortcut]
URL=http://www.google.com/picasa
```

## 2. Az `autorun.inf` — a pontos sablon

A generáló `0x006919b0` a lemez gyökerébe írja (`\autorun.inf`,
`0x00ca791c`). A formátumsztring **szó szerint** (`0x00ca78f0`, CRLF
sorvégekkel):

```
[autorun]\r\nopen=%s\r\nicon=%s,0\r\nSHELL=OPEN\r\n
```

**Két `%s`, mindkettő a futtatandó program neve** — az `open=` és az
`icon=` ugyanazt kapja, az ikon a program 0. erőforrás-ikonja.

**Kikapcsolható:** `option_noautoruninf` (2. szakasz).

## 3. A kimeneti BEÁLLÍTÁSOK — tizenhat kulcs, egy olvasóban

A `0x0066f470` (923 b) a `Preferences` alól olvassa őket. **Ez a lista
teljes** — a függvény minden sztringje szerepel benne:

| kulcs | cím |
|---|---|
| `option_imagesizelimit` | `0x00ca35c8` |
| `option_jpegquality` | `0x00ca35e0` |
| `option_thumbsize` | `0x00ca35f4` |
| `option_useorig` | `0x00ca3608` |
| `option_backup` | `0x00ca3618` |
| `option_createhtml` | `0x00ca3628` |
| `option_estimate` | `0x00ca363c` |
| `option_inifile` | `0x00ca364c` |
| `option_manifest` | `0x00ca365c` |
| `option_manifestcaptions` | `0x00ca366c` |
| `option_manifestfiletimes` | `0x00ca3684` |
| `option_convertnonjpeg` | `0x00ca36a0` |
| `option_preservemovies` | `0x00ca36b8` |
| `option_noautoruninf` | `0x00ca36d0` |
| `option_isupload` | `0x00ca36e4` |
| `CDSlideshow` · `CDSlideshowInclSetup` | `0x00ca43e8` · `0x00ca43f4` |

**Amit ez elárul a kimenetről** (a kulcsnevek önmagukban):

- **méret és minőség**: felső képméret-korlát, JPEG-minőség, bélyegkép-méret,
  vagy **eredeti** fájl (`useorig`);
- **kísérő adat**: `.picasa.ini` viheti-e (`inifile`), **manifeszt**
  készüljön-e, és abban legyen-e **felirat** (`manifestcaptions`) és
  **fájlidő** (`manifestfiletimes`);
- **HTML-galéria** (`createhtml`);
- **átalakítás**: nem-JPEG konvertálása (`convertnonjpeg`), a **filmek
  megőrzése** (`preservemovies`);
- **méretbecslés** kiírás előtt (`estimate`);
- és három **üzemmód-kapcsoló**: `backup` · `isupload` · `noautoruninf`.

⚠️ **A kulcsok ÉRTÉKKÉSZLETE nincs mérve** — a nevekből a *létezésük*
következik, a megengedett értékek nem. Ld. a 6. szakasz mérlegét.

## 4. A lemez MAPPASZERKEZETE — és a nevek HONOSÍTOTTAK

Ugyanaz a `0x0066f470` két mappanevet kér a szövegtárból, és adja át a
kimeneti objektumnak (`0x0066f4c9`, `0x0066f535` környéke):

| szövegtár-kulcs | angol | **hivatalos magyar** |
|---|---|---|
| `il_BurnPanel::bkfolder` | `Backup` | **„Biztonsági mentés"** |
| `il_BurnPanel::picfolder` | `Pictures` | **„Képek"** |

⇒ **magyar Picasával kiírt lemezen `Biztonsági mentés` és `Képek` nevű
mappák vannak**, nem `Backup`/`Pictures`.

A két ág között ugyanaz a jelzőbit dönt (`[ebp+0x13f]`,
`0x0066f491`), amelyik a `backups.xml` ↔ `replicates.xml` választást is
(`biztonsagi-mentes.md` 1.2) — **egy csővezeték, két üzemmód**.

## 5. A kiírás VÉGE — párbeszéd, és egy fejlesztői maradvány

`0x00673b80` (608 b):

| szövegtár-kulcs | angol | **magyar** |
|---|---|---|
| `il_BurnPanel::DoneDialogTitle` | CD Done | **„CD kész"** |
| `il_BurnPanel::DoneDialogPrompt` | Burn complete! Would you like to eject or show the CD? | **„Az írás kész. Szeretné kiadni vagy megjeleníteni a CD-t?"** |
| `il_BurnPanel::HandleDone::1` | Eject CD | **„CD kiadása"** |
| `il_BurnPanel::HandleDone::2` | Show CD | **„CD megjelenítése"** |

Ugyanitt: `LaunchAutoRun` (a lemez automatikus indítása) — és **egy
fejlesztői maradvány**:

```
C:\Program Files\D-Tools\daemon.exe
-mount 0,"%s"
```

⇒ a Picasa **virtuális meghajtóba tudta csatolni** a kiírt képet
(Daemon Tools), nyilván teszteléshez. Ehhez tartozik a `0x006669a0`-ban
álló, **beégetett** `d:\cdtemp\temp.iso` útvonal — mindkettő
**hatókörön kívül** nálunk, de kimondva, hogy egy következő kör ne
higgye funkciónak.

## 6. Eredeti / nálunk / teendő

A „nálunk" oszlop **mérés** (`e0abfbb3`).

| | eredeti (mért) | nálunk (mért) | teendő |
|---|---|---|---|
| menü-belépési pont | „Create a &Gift CD…" (`0x00559150`) | **halott helyőrző** (`PicasaMenuBar.qml:1329`, `placeholder: true`) | bekötni vagy kimondottan elhalasztani |
| önjáró lemez | Win + Mac vetítő, Win + Mac visszaállító, telepítő, letöltő-link | **nincs** | ld. lent |
| `autorun.inf` | generált, pontos sablon (2.) | **nincs** | Linuxon **tárgytalan** |
| mappanevek | **honosított** (`Biztonsági mentés` / `Képek`) | **nincs** | honosított nevek |
| kimeneti beállítások | **16 kulcs** (3.) | **nincs** | a listából válogatva |
| befejező párbeszéd | „CD kész" + kiadás/megjelenítés | **nincs** | Linux-megfelelő |

**Mérés módja nálunk**, két lekérdezés-alakkal:

1. `grep -rn 'autorun\|PicasaCD\|option_manifest\|option_createhtml\|cdgo' src/`
   → **0 találat**;
2. kontroll `grep -rniE '\bcd\b|lemezre|burn' src/ --include=*.py --include=*.qml`
   → **37 találat**, ezekből érdemi **kettő**:
   - `PicasaMenuBar.qml:1329` — **`PicasaMenuItem { text: qsTr("Make a Gift CD...");
     placeholder: true }`**, vagyis a **menüpont MEGVAN, de halott
     helyőrző** (a #324-es felületi átvilágítás vette fel);
   - `PicasaNotifier.qml:304` — egy megjegyzés, ami helyesen figyelmeztet
     rá, hogy az `il_BurnPanel::Backup*` feliratok a CD-s mentéséi, nem a
     szerkesztés-mentéséi.

   A többi 35 találat érintetlen kontextus (a kollázs „CD Cover"
   lapformátuma, az `ioutil.py` `fsync`-magyarázata, az
   `ini/filter_guard.py` „lemezre juthat" fordulata).

⇒ **A belépési pont tehát megvan, de nem csinál semmit** — ez a
`picasapy-agent` naplójában rögzített „halott menüpont" osztály
(v.ö. #1792, #1775).

⚠️ **A Windows-specifikus rész nem másolható át**: az `autorun.inf`, a
`.exe`-k és a Daemon Tools Linuxon értelmetlenek. **Ami átvehető:** a
mappaszerkezet honosított nevekkel, a 16 beállítás közül a
tartalomra vonatkozók (méret, minőség, `.picasa.ini`, manifeszt, HTML,
filmek), és a befejező visszajelzés.

## 7. Nyitott kérdések mérlege

`0 nyílt · 5 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| mi kerül a lemezre a képeken kívül | **LEZÁRVA** — 1. szakasz, négy másoló |
| mi az `autorun.inf` tartalma | **LEZÁRVA** — pontos sablon (2.) |
| milyen beállítások vannak | **LEZÁRVA** — 16 kulcs, teljes lista (3.) |
| milyen a mappaszerkezet | **LEZÁRVA** — honosított `Backup`/`Pictures` (4.) |
| mi történik a kiírás után | **LEZÁRVA** — párbeszéd + `LaunchAutoRun` (5.) |
| **a 16 beállítás ÉRTÉKKÉSZLETE** | **BLOKKOLT** — a nevek megvannak, a megengedett értékek nem. Az olcsó lánc kimerült: a `.tre` nem tartalmazza őket (nem felületi elemek), a szövegtárban nincsenek, a sztring-xref egyetlen olvasót ad (`0x0066f470`), és azt végigolvastam. **Megszerzés:** a `0x0066f470` (923 b) célzott dekompilációja — ott derül ki, melyik kulcs egész, logikai vagy felsorolás. **A megvalósítást nem blokkolja:** a kulcsok jelentése a nevükből egyértelmű. |
| Daemon Tools / `d:\cdtemp\temp.iso` | **HATÓKÖRÖN KÍVÜL** — fejlesztői teszt-maradvány, nem felhasználói funkció; eldöntötte: ez a kör, 2026-09-02 |

## 8. Amit KIZÁRTAM

- **„az Ajándék-CD csak képeket másol"** — nem: **teljes önjáró lemez**,
  két platform vetítőjével és visszaállítójával.
- **„a lemez mappanevei angolok"** — nem: a szövegtárból jönnek
  (`il_BurnPanel::bkfolder` / `picfolder`), tehát honosítottak.
- **„a `d:\cdtemp\temp.iso` a kimeneti útvonal"** — nem: beégetett
  fejlesztői teszt-út, a Daemon Tools-os csatolás mellett.

*Bizonyítottsági fok: **megerősített** a másolt fájlokra (a forrásmappa
élő mintaként megvan), az `autorun.inf` sablonjára (nyers bájtok), a 16
kulcsra és a honosított mappanevekre; a kulcsok **értékkészlete** nincs
mérve.*

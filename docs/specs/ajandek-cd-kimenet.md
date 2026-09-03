# Az Ajándék-CD és a mentő lemez KIMENETE (`il_BurnPanel`)

**Mi ez:** a Picasa 3 „Ajándék CD készítése…" parancsa
(**`eMenuCreate::ID_BURNCD`** — a **Létrehozás** menü tétele; a belépési
pontok teljes listája a **9.** szakaszban) és a
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
| menü-belépési pont | „Create a &Gift CD…", a **Létrehozás** menüben (9.) | **halott helyőrző** — `PicasaMenuBar.qml:1417`, `placeholder: true` *(a korábbi `:1329` sorszám téves volt: az 1329. sor a kötegelt „Sharpen")* | bekötni vagy kimondottan elhalasztani |
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

`0 nyílt · 7 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

*(2026-09-03: az „értékkészlet" tétel LEZÁRULT, a belépési pontok lezárva
bekerültek, és egy új blokkolt tétel — az ág ↔ üzemmód hozzárendelés — nyílt.)*

| kérdés | állapot |
|---|---|
| mi kerül a lemezre a képeken kívül | **LEZÁRVA** — 1. szakasz, négy másoló |
| mi az `autorun.inf` tartalma | **LEZÁRVA** — pontos sablon (2.) |
| milyen beállítások vannak | **LEZÁRVA** — 16 kulcs, teljes lista (3.) |
| milyen a mappaszerkezet | **LEZÁRVA** — honosított `Backup`/`Pictures` (4.) |
| mi történik a kiírás után | **LEZÁRVA** — párbeszéd + `LaunchAutoRun` (5.) |
| ~~a 16 beállítás ÉRTÉKKÉSZLETE~~ | **LEZÁRVA (2026-09-03)** — a **10.** szakasz: a kulcsok logikai (0/1) vagy egész típusúak, felsorolás nincs; húsz beállító híváshely értéke kiolvasva, köztük `option_jpegquality = 85`. Dekompiláció nem kellett. *(A blokkolás indoka — „a sztring-xref **egyetlen** olvasót ad" — megdőlt: a `0x0068eea0` a második, és épp az az olvasó.)* |
| **a belépési pontok** | **LEZÁRVA (2026-09-03)** — öt, ebből kettő a `.tre`-ben kikommentezve (**9.**) |
| **melyik ÁG melyik üzemmódhoz tartozik** | **BLOKKOLT (2026-09-03)** — a `0x0066f470` három ágon állít értékeket, de a `[ebp+0x13f]` jelzőbit és a `0x0066f546` `test edi, edi` hozzárendelése az üzemmódokhoz (mentés / Ajándék-CD / feltöltés) **NINCS MÉRVE**. **Megszerzés:** a `0x0066f470` (923 b) célzott dekompilációja, VAGY egy valódi kiírt lemez tartalomjegyzéke. Jegy: **#2095**. |
| Daemon Tools / `d:\cdtemp\temp.iso` | **HATÓKÖRÖN KÍVÜL** — fejlesztői teszt-maradvány, nem felhasználói funkció; eldöntötte: ez a kör, 2026-09-02 |

## 8. Amit KIZÁRTAM

- **„az Ajándék-CD csak képeket másol"** — nem: **teljes önjáró lemez**,
  két platform vetítőjével és visszaállítójával.
- **„a lemez mappanevei angolok"** — nem: a szövegtárból jönnek
  (`il_BurnPanel::bkfolder` / `picfolder`), tehát honosítottak.
- **„a `d:\cdtemp\temp.iso` a kimeneti útvonal"** — nem: beégetett
  fejlesztői teszt-út, a Daemon Tools-os csatolás mellett.
- **„a beállításokat a `Preferences` registry-ág tárolja"** — **MEGDŐLT
  (2026-09-03):** a `0x0066f470` ÍR egy objektumba (`SetOption(név, érték)`),
  és `Preferences\option…` alakú sztring a binárisban **nulla** van (10.2).
- **„az Ajándék CD nem fényképexport, hanem egy szállított nézőprogram
  lemezre égetése"** — a
  [`picasa-menu-parancsok-viselkedes.md`](picasa-menu-parancsok-viselkedes.md)
  `ID_BURNCD`-szakaszának állítása **TÚL SZŰK**: a nézőprogram tényleg
  odakerül, de mellette **teljes fényképexport** fut, saját méret-,
  minőség-, manifeszt- és HTML-beállításokkal (3., 10.).
- **„a fejlécsávban van »CD készítése« gomb"** — nem: a
  `headerpanel/create_cd` és a `faceheaderpanel/create_cd` a `.tre`-ben
  **kikommentezve** áll (9.).

*Bizonyítottsági fok: **megerősített** a másolt fájlokra (a forrásmappa
élő mintaként megvan), az `autorun.inf` sablonjára (nyers bájtok), a 16
kulcsra és a honosított mappanevekre; a kulcsok **értékkészlete** nincs
mérve.*

---

## 9. A BELÉPÉSI PONTOK — négy, ebből kettő KIKAPCSOLVA (2026-09-03)

Ez a lap eddig azt írta le, **mi kerül a lemezre**. Azt nem, hogy **honnan
indul** — pedig a visszafejtési sorrend első kérdése ez
([`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md), a
„MI AKTIVÁLJA?" pont), és egy parancsazonosító több menüben is ülhet.

| # | belépési pont | él? | bizonyíték |
|---|---|---|---|
| 1 | **`eMenuCreate::ID_BURNCD`** — a **Létrehozás** menü tétele | ✅ | szövegtár 2602. sor; a menüépítőben (`0x00559150`, 15 495 b) **pontosan egyszer** fordul elő ⇒ **egy** menüben van |
| 2 | **`thumbui/cdmode`** — üzemmód-gomb a fő nézetben | ✅ | `panel-feliratok-hu.tsv` 5157–5158; kezelők: `0x005cb990`, `0x005d9cc0`, `0x005e0f70` |
| 3 | `headerpanel/create_cd` | ❌ **kikommentezve** | `headerpanel.tre:67` és `:69` — `#headerpanel/create_cd: headerpanel/headerbase`; a buboréksúgója is: `headerpaneltext.tre:50` |
| 4 | `faceheaderpanel/create_cd` | ❌ **kikommentezve** | `faceheaderpanel.tre:70`, `:72`; `faceheaderpaneltext.tre:14` |
| 5 | **`publish/presentcd_go`** — a panel saját indítógombja | ✅ | `panel-feliratok-hu.tsv` 5067 |

> ⛔ **HELYESBÍTÉS — a lap fejléce `eMenuTools::…`-t írt.** A szövegtár-kulcs
> **`eMenuCreate::ID_BURNCD`**, tehát a parancs a **Létrehozás** menüben ül,
> nem az Eszközökben. A hivatkozott `0x00559150` a **teljes menüsor
> építője** (15 495 b, minden menü benne van), ezért önmagában nem
> azonosítja a menüt.

### 9.1 A hivatalos magyar feliratok

| elem | angol | **hivatalos magyar** |
|---|---|---|
| `eMenuCreate::ID_BURNCD` | Create a &Gift CD... | **„&Ajándék CD készítése…"** |
| `thumbui/cdmode` (felirat) | Gift CD | **„Ajándék CD"** |
| `thumbui/cdmode` (buboréksúgó) | — | **„CD/DVD létrehozása beépített diavetítéssel ismerősök és családtagok részére"** |
| `publish/presentcd_go` | — | **„Lemezre írás"** |
| `publish/presentcd_help` · `_eject` · `_cancel` | — | **„Súgó" · „Kiadás" · „Mégse"** |

*(A buboréksúgó fontos: kimondja, hogy a lemez célja a **beépített
diavetítés** — ez köti össze a 9. szakaszt az 1.-vel.)*

### 9.2 A két kikommentezett gomb JELENTŐSÉGE

A `#` a `.tre`-ben megjegyzés — ez mérve van
([`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md) 4.1). A bináris a
`create_cd` nevet **ismeri** (`0x005e0f70` sztringkészlete), a felületleíró
viszont **kikapcsolja**. ⇒ **A fejlécsávban NINCS „CD készítése" gomb ebben a
kiadásban**, hiába szerepel a név a kódban.

Ez a
[19. szakasz](binaris-regeszet-modszertan.md) elvetett mérőszámának
**fordítottja**: ott a *név hiánya* nem bizonyította a halottságot; itt a
*név megléte* nem bizonyítja az élő vezérlőt. **Mindkét irányban a
felületleíró dönt, nem a bináris.**

---

## 10. A beállítások ÉRTÉKEI — a 7. szakasz BLOKKOLT tétele LEZÁRVA (2026-09-03)

A 7. szakasz mérlege ezt írta: *„a 16 beállítás ÉRTÉKKÉSZLETE — BLOKKOLT…
a sztring-xref **egyetlen olvasót** ad (`0x0066f470`)… Megszerzés: a
`0x0066f470` célzott dekompilációja."*

**Mindhárom premissza megdőlt.** Dekompiláció nem kellett.

### 10.1 Nem egy függvény van, hanem KETTŐ — és az egyik az OLVASÓ

| függvény | szerep | bizonyíték |
|---|---|---|
| `0x0066f470` (923 b) | **ÍRÓ** — `SetOption(név, érték)` alakban tölti fel a beállítás-objektumot | a hívási minta: `push <érték>; push <névsztring>; mov ecx, esi; call [vtbl+0x20]` (pl. `0x0066f53d`–`0x0066f544`) |
| **`0x0068eea0` (565 b)** | **OLVASÓ / szétosztó** — `(név, érték)` párt kap, és a nevet **tagváltozóra** képezi | `repe cmpsb` a névvel, majd `mov [edx+<offszet>], <érték>` |

A `0x0068eea0`-t a korábbi kör nem vette észre, mert a lap a
`0x0066f470` sztringjeiből dolgozott.

### 10.2 A kulcs → tagoffszet térkép — TELJES, 16 sor

A `0x0068eea0` végigolvasva, minden ág kiolvasva:

| kulcs | tagoffszet |
|---|---|
| `option_useorig` | `+0x454` |
| `option_backup` | `+0x458` |
| `option_convertnonjpeg` | `+0x45c` |
| `option_imagesizelimit` | `+0x460` |
| `option_copysrctotempdest` | `+0x464` |
| `option_thumbsize` | `+0x468` |
| `option_jpegquality` | `+0x46c` |
| `option_createhtml` | `+0x470` |
| `option_preservemovies` | `+0x474` |
| `option_estimate` | `+0x478` |
| `option_inifile` | `+0x47c` |
| `option_manifest` | `+0x480` |
| `option_manifestcaptions` | `+0x484` |
| `option_manifestfiletimes` | `+0x488` |
| `option_isupload` | `+0x48c` |
| `option_noautoruninf` | `+0x490` |

⭐ **Tizenhat kulcs, tizenhat EGYMÁS UTÁNI dword, hézag nélkül**
(`+0x454`…`+0x490`). Ez önmagában igazolja, hogy a lista teljes.

> ⛔ **HELYESBÍTÉS a 3. szakaszhoz — két hiba.**
> 1. Ott **15** `option_*` kulcs áll, és mellettük két **nem-`option_`** név
>    (`CDSlideshow`, `CDSlideshowInclSetup`). A tizenhatodik, hiányzó kulcs:
>    **`option_copysrctotempdest`** (`+0x464`) — csak az olvasóban szerepel.
> 2. A 3. szakasz szerint a `0x0066f470` „a `Preferences` alól olvassa
>    őket". **Nem onnan:** a hívási minta ÍRÁS egy objektumba, és a
>    binárisban **`Preferences\option…` alakú sztring nulla darab van**
>    (kontroll: a nyolc `Preferences\` előtag mind más — `HotFolders`,
>    `Plugins`, `RSSDownload`, `Buttons`, `AspectRatios`, `PrinterData`).

### 10.3 Az értékek — 20 híváshely, kiolvasva

| cím | kulcs | beállított érték |
|---|---|---|
| `0x0066f544` | `option_backup` | `eax` (a `0x0066f535` `xor eax,eax` után **0**) |
| `0x0066f572` | `option_inifile` | **1** |
| `0x0066f59f` | `option_manifest` | **1** |
| `0x0066f5af` | `option_manifestfiletimes` | **1** |
| `0x0066f5d7` | `option_noautoruninf` | **1** |
| `0x0066f5ff` | `option_estimate` | `ecx` |
| `0x0066f614` | `option_imagesizelimit` | `ecx` |
| `0x0066f624` | `option_preservemovies` | **1** |
| `0x0066f634` | `option_isupload` | **1** |
| `0x0066f644` | `option_convertnonjpeg` | **1** |
| `0x0066f68d` | `option_useorig` | `ecx` |
| `0x0066f69d` | `option_preservemovies` | **1** |
| `0x0066f6f3` | `option_convertnonjpeg` | `ebx` |
| `0x0066f756` | `option_manifest` | **1** |
| `0x0066f766` | `option_manifestcaptions` | **1** |
| `0x0066f794` | `option_estimate` | `edi` |
| `0x0066f7a3` | `option_imagesizelimit` | `edi` |
| `0x0066f7b3` | **`option_jpegquality`** | **`0x55` = 85** |
| `0x0066f7c3` | `option_thumbsize` | **0** |
| `0x0066f7d3` | `option_createhtml` | **0** |

**Amit ez eldönt:**

1. A kulcsok **logikai** (0/1) vagy **egész** típusúak — felsorolás nincs
   köztük. A 7. szakasz aggálya („melyik kulcs egész, logikai vagy
   felsorolás") ezzel megválaszolva.
2. ⭐ **`option_jpegquality = 85`** — ugyanaz a szám, amit a Picasa az
   exportálásnál a „Normál" fokozathoz használ
   ([`export-parbeszed.md`](export-parbeszed.md) 7.), és **ugyanaz, amit mi
   is alapértékként adunk** (`src/picasapy/export/exporter.py:62`,
   `jpeg_quality: int = 85`). **Egyezik, nincs teendő.**
3. `option_thumbsize = 0` és `option_createhtml = 0` **ezen az ágon** —
   tehát a HTML-galéria nem alapból készül.

⚠️ **Amit ez NEM dönt el:** hogy melyik ág melyik üzemmódhoz
(mentés / Ajándék-CD / feltöltés) tartozik. Az ágválasztást a
`[ebp+0x13f]` jelzőbit és a `0x0066f546` `test edi, edi` végzi; a
hozzárendelés **NINCS MÉRVE**.

### 10.4 A beállítás-készlet NEM csak a lemezé — az e-mail is használja

A `0x00743030` (716 b) **négy kulcsot** ugyanígy állít
(`option_imagesizelimit`, `option_useorig`, `option_estimate`,
`option_preservemovies`), és mellettük az `EmailSinglePicture`,
`EmailMovie`, `EmailExportSize`, `Gmail` neveket kezeli.

⇒ **Ez egy közös export-beállítás szerkezet**, nem az Ajándék-CD sajátja.
Aki a levélküldést építi, ugyanezt a struktúrát találja meg
([`picasa-email-kuldes.md`](picasa-email-kuldes.md)).

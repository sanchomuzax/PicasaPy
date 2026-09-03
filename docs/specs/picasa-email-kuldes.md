# E-mail-küldés a Picasából

Két erőforráspárból áll: **`choose_mail.tre`** (23 elem) — a küldési mód
választója — és **`compose_mail.tre`** (40 elem) — a **beépített Gmail-
szerkesztő**. A szövegeik a `*_text.tre` párjukban élnek, **angolul**.

## 1. A választó párbeszéd — `choose_mail`

> **„Select how you want to e-mail your photos."**

Két lehetőség, mindegyik cím + magyarázó sor:

| elem | felirat |
|---|---|
| `mail1` | **MAIL CLIENT** |
| `mail1a` | Use my default email program. |
| `mail2` | **Google Mail** |
| `mail2a` | Use my Gmail or Google account. |
| `gmailsignup1` | Don't have Gmail? Get a free account. *(webcím: `http://mail.google.com`)* |
| `remember` | **Remember this setting, don't display this dialog again.** |
| `help` | Help |
| `mailcancel` | Cancel |

Elemek: `picker` · `selectheader` · `selecttext` · `mymail` (+ ikon) ·
`gsender` (+ ikon) · `googsender_icon` · `checkbox` ·
`remember_container` · `prefcontainer` · `helpbutton` (+ ikon) ·
`cancelbutton` (+ ikon).

A „ne kérdezd újra" jelölő a **`DoNotPromptForEmailPref`** kulcsba ír
(`0x006e1100`).

## 2. A beépített Gmail-szerkesztő — `compose_mail`

**Negyven elem.** A Picasa nem csak átadta a képeket a levelezőnek: **saját
üzenetszerkesztője** volt, Gmail-bejelentkezéssel.

| csoport | elemek |
|---|---|
| fejléc | `topstrip` · `topentry` · `to` + `to_text` („To:") · `subject` + `subject_text` („Subject:") |
| üzenet | `compose` · `composeclip` · `content` |
| melléklet | `piccontainer` · `preview` · `picstroke` · `clipicon` · `discardimage` (+ ikon) |
| lapozás | `navleft` (+ ikon) · `navright` (+ ikon) |
| **írásirány** | **`ltr`** (+ ikon) · **`rtl`** (+ ikon) · `bidi_container` |
| fiók | `gmail` · `googlemail` · `curuser` · `changeuser` („Change User") · `logininfo` |
| gombok | `send` / `sendb` („Send") · `discard` / `discardb` („Discard") · fókuszált párjaik (`focsend`, `focsendb`, `focdiscard`, `focdiscardb`) |
| egyéb | `bottomstrip` · `divider` · `infotext` |

> **Kétirányú írás**: a szerkesztő külön **balról-jobbra / jobbról-balra**
> kapcsolót kínált (`ltr` / `rtl`, `bidi_container`) — arab és héber
> felhasználóknak.

> A `discardimage` súgója: „Remove selected image from attachment" — a
> mellékletek **egyenként** eltávolíthatók, a `navleft`/`navright` párral
> lapozva.

## 3. A beállítások (a Beállítások párbeszéd E-mail fülén)

| kulcs | mit |
|---|---|
| `EmailPrepType` | a küldési mód (levelező ↔ Gmail) |
| `EmailExportSize` | a csatolt képek mérete |
| `EmailSinglePicture` | egyetlen kép küldése |
| `EmailMovie` | videó küldése |
| `UseHTMLMailer` | HTML-levél |
| `DoNotPromptForEmailPref` | „ne kérdezd újra" |
| `mailprog` / `defaultmail` / `picsize` | a párbeszéd vezérlői |

A fül feliratai: `IDS_EMAIL_PREFS` → **„E-mail"**,
`IDS_EMAILCLIENTBUTTON` → **„Küldés módja: "**,
`IDS_EMAILCLIENTRADIO` → **„Ezt használom: "**.

### 3/b A méret-beállítás SZEMANTIKÁJA — mérve (2026-09-02)

A fenti tábla eddig csak annyit mondott, hogy az `EmailExportSize` „a csatolt
képek mérete". A kulcs tényleges jelentése a binárisból:

| állítás | bizonyíték |
|---|---|
| `Preferences\EmailExportSize` **közvetlen képpont-érték** (a hosszabb oldal), NEM listaindex | `0x00743030` a `0x407a20` beállítás-olvasóval, majd változtatás nélkül továbbadja |
| az **alapértéke 480** | `mov dword ptr [esp+0x24], 0x1e0` — **három** egymástól független helyen: `0x006e1756`, `0x006e3f2b`, `0x00743094` |
| a **`0` jelentése: eredeti méret** | `option_useorig` = (érték == 0), `0x0074310f`–`0x0074311a` |
| nem nulla értéknél a képkimenet **két** beállítást kap | `option_imagesizelimit` = érték (`0x00743128`) és `option_estimate` = érték (`0x00743137`) |
| `EmailSinglePicture` **kapcsoló** (alapérték 0), nem méret | `0x007430a6` olvasás alapértékkel 0; a `0x007430f6` ágban csak `== 1`-re vizsgálja |
| ha a kimenet darabszáma **1** ÉS `EmailSinglePicture == 1` ⇒ a méret **0 lesz** (eredeti méret) | `0x007430ec` `call [edx+0x38]`, `cmp eax, 1`; majd `0x007430ff` `cmp eax, 1`; `0x00743104` `xor edi, edi` |
| `EmailMovie == 1` ⇒ `option_preservemovies = 1` (a videó teljes egészében megy, nem egy képkocka) | `0x0074313e`–`0x0074315a` |
| a méretre hozott mellékletek a **`temp\email\`** mappába kerülnek | `0x0073f320` |

A teljes döntési sor, ahogy a kód végrehajtja:

```
méret = Preferences\EmailExportSize                  # alapértelmezés: 480
ha (kimenet_darabszám == 1) és (EmailSinglePicture == 1):
    méret = 0                                        # eredeti méret
option_useorig = (méret == 0)
ha méret != 0:
    option_imagesizelimit = méret
    option_estimate       = méret
ha EmailMovie == 1:
    option_preservemovies = 1
```

> **Bizonyítottsági fok: megerősített** minden sorra, **egy kivétellel**: hogy a
> `[edx+0x38]` virtuális hívás pontosan a **küldendő képek darabszámát** adja,
> az **erős**, nem megerősített olvasat (a `cmp eax, 1` és az
> `EmailSinglePicture` név együttes jelentése). Ugyanabban a függvényben a
> `[+0x30]` és a `[+0x34]` szintén darabszám-jellegű (két egymásba ágyazott
> ciklus határa), tehát a szomszédos rések is számlálók.

**Ami NINCS MEG: a Beállítások E-mail fülén a csúszka LÉPÉSEI.** A
`Beállítások` párbeszéd natív Win32 lap (`CGeneralPrefsPage`), a feliratai a PE
erőforrás-táblában élnek, nem a `.tre`/`stringres` anyagban — ezért a
szövegtárból nem jönnek elő. Amit tudunk: a **`%d pixels (for e-mail)`**,
`%d pixels (for Web pages)`, `%d pixels (for large Web pages)` és
`%d pixels (for large monitors)` sablonok **ott vannak** a `Picasa3.exe`
sztringtáblájában (UTF-16-ban megtalálva) — tehát a felirat a számot
**futásidőben** kapja.

**Erős, de nem bizonyított kapcsolat:** az Exportálás párbeszéd
méret-előbeállításai **mérve** `320 | 480 | 640 | 800 | 1024 | 1200 | 1600`
(`export/bind17.list`, ld. [`export-parbeszed.md`](export-parbeszed.md)), és az
`EmailExportSize` alapértéke — **480** — ennek a listának a **második** eleme.
Hogy az E-mail fül csúszkája ugyanezt a hét értéket kínálja-e (plusz az
„eredeti méret" = 0), az **NINCS MÉRVE**. Megszerzése: **egyetlen képernyőkép**
a futó Picasa `Eszközök ▸ Beállítások ▸ E-mail` lapjáról — ott a csúszka
felirata kiírja az aktuális képpontszámot. Jegy: **#2020**.

## 4. Az üzenetek — ezek LE VANNAK fordítva

Ellentétben a `.tre` feliratokkal, az `IDS_EMAIL_*` üzenetek hivatalos
magyar fordítással bírnak:

| erőforrás | HU |
|---|---|
| `IDS_EMAIL_ATTACHMENTLIMIT` | A csatolt képek túl nagyok. Távolítson el néhány mellékletet, vagy válassza az Eszközök menü Beállítások parancsát, és állítsa át a levelezési beállításokat kisebb képek küldésére. |
| `IDS_EMAIL_ATTACHMENTLIMIT_INFO` | A mellékletek túl nagyok… |
| `IDS_EMAIL_REMOVE_ATTACHMENT` | Biztosan eltávolítja ezt a mellékletet? |
| `IDS_EMAIL_REMOVE_ATTACHMENT_YES_BUTTON` | **Melléklet eltávolítása** |
| `IDS_EMAIL_SENDEMPTY` | Az üzenettörzs üres. Biztosan elküldi? |
| `IDS_EMAIL_SENDEMPTY_YES_BUTTON` / `_NO_BUTTON` | **Küldés** / **Küldés mellőzése** |
| `IDS_EMAIL_DISCARD` | Biztosan elveti ezt az üzenetet? |
| `IDS_EMAIL_DISCARD_YES_BUTTON` | **Üzenet elvetése** |
| `IDS_EMAIL_CLEARAC` | Biztosan kiüríti a mentett névjegyalbumot? |
| `IDS_EMAIL_SUCCESS` | Elküldött e-mail |
| `IDS_EMAIL_FAILED` | A küldés sikertelen |
| `IDS_EMAIL_SEND_ATTEMPT_FAILED` | Nem sikerült elküldeni az e-mailt. Próbálkozzon később. |
| `IDS_EMAIL_OUTPUT_PROGRESS_MSG` | Képek exportálása |

**Öt Gmail-bejelentkezési hiba** is le van fordítva:
`LOGINCOOKIES`, `LOGINERROR`, `LOGINFORBIDDEN`, `LOGININCORRECT`,
`RELOGIN`.

## 5. Egy külön futtatható: `PicasaEmailScanner`

`IDS_EMAILSCANNER_EXE` → **`PicasaEmailScanner`** — a Picasa külön
programot telepített a levelezőbe érkező képek beolvasására.

## Amit ebből a PicasaPy visz

A **Gmail-szerkesztő halott**: a bejelentkezési út (cookie-alapú
Gmail-login) rég nem működik. A **levelezőprogramnak átadás** viszont ma is
értelmes: Linuxon `xdg-email`, mellékletekkel.

A **méretkorlát-figyelmeztetés** és a **melléklet-eltávolítás** viszont
átvehető, hivatalos magyar szöveggel.

*Bizonyítottsági fok: megerősített* (a négy erőforrásfájl teljes tartalma
és a 23 `IDS_EMAIL_*` bejegyzés).

## ✅ Az Opciók ▸ E-mail lap — KÉPERNYŐKÉPPEL MÉRVE (2026-09-02, #2020)

A tulajdonos futó Picasa 3-ának két képernyőképe (`research/#2020-email/`)
és a csúszka végigléptetése. Ez a szakasz **mérés**, nem következtetés.

### A csúszka nyolc fokozata

**160 · 320 · 480 · 640 · 800 · 1024 · 1200 · 1600** képpont, az alapérték a
**480** — egyezik a dekompilációval (`EmailExportSize` alapértéke `0x1e0`
három független helyen: `0x006e1756`, `0x006e3f2b`, `0x00743094`).

⚠️ A #350 becsült listája `(640, 800, 1024, 1600, „eredeti")` volt. A mérés
szerint **a 480 (az alapérték), a 160, a 320 és az 1200 mind hiányzott
belőle**, az „eredeti méret" pedig **nincs a csúszkán**.

### A lap valódi szerkezete, hivatalos magyar feliratokkal

```
Levelezőprogram:             (•) Minden képküldésnél kiválasztom
                             ( ) Ezt használom: Microsoft Outlook
                             ( ) A Google Fiók használata

Több kép mérete              [--|-----------]   480 képpont

Egyedülálló képek mérete:    (•) Több elemmel azonos (480 képpont)
                             ( ) Eredeti méret

Mozgófilmek küldése másként: (•) Első képkocka
                             ( ) Teljes mozgófilm

Kimeneti formátum:           [ ] Szövegközi fotók és képfeliratok küldése
                                 (csak Outlookban)
```

Négy dolog, amit ez a szerkezet **eldönt**:

1. **EGY méret-csúszka van**, nem kettő. A második vezérlő rádiógombpár.
2. **A csúszka mellett a pillanatnyi érték szövegként** áll („480 képpont").
3. **A rádiógomb felirata beleírja az aktuális méretet** — élő kötés a
   csúszkához, nem statikus szöveg.
4. A `0` (eredeti méret) az „Eredeti méret" gombról jön, nem a csúszkáról.

### A levelezőprogram-választó párbeszéd

Cím: **„Válasszon levelezőprogramot"**, alcím: *„Válassza ki, hogyan
szeretné e-mailben elküldeni fotóit."* Két ikonos választógomb (Microsoft
Outlook / Google Mail), alattuk link *„Nincs Gmail-fiókja? Nyisson egy
fiókot ingyen."*, majd a jelölőnégyzet **„Jegyezze meg ezt a beállítást, ne
jelenítse meg a párbeszédpanelt újra."** — ez írja át a Levelezőprogram
rádiógombot az Opciók lapon. Gombok: **Súgó** · **Mégse**.

### Nálunk — a #2020 után

| | eredeti | nálunk |
|---|---|---|
| a méret tárolása | képpont | ✅ képpont (`mail/exportSize`) |
| fokozatok | a fenti nyolc | ✅ ugyanaz |
| alapérték | 480 | ✅ 480 |
| érték a csúszka mellett | igen | ✅ |
| „egyedülálló kép" | kapcsoló | ✅ két rádiógomb |
| a gomb feliratában a méret | igen | ✅ élő kötés |
| levelezőprogram-választás | három gomb (Outlook/Google) | ⚠️ **kettő** — Linuxon nincs Outlook- és Google-integrációnk, ezért a rendszer alapértelmezett levelezője marad |
| mozgófilm-ág, Outlook-jelölő | élő | ⚠️ tiltott helyfoglaló — nincs videó-e-mail és Outlook-integráció |

A két ⚠️ **szándékos, platformból következő eltérés**, nem hiány: olyan
integrációt ígérnének, ami nem létezik.

---

## ⭐ 6. HOL tárolódnak a beállítások, és MIT ír a választó párbeszéd (2026-09-03)

A lap eddig felsorolta a beállítás-**kulcsokat** (3. szakasz), de nem mondta
meg, **hol vannak**, mi az **alapértékük**, és **mikor** íródnak. Ez a
szakasz ezt pótolja — és a tároló nem csak az e-mailre igaz, hanem a Picasa
**összes** beállítására.

### 6.1 A tároló: a Windows-registry, `HKEY_CURRENT_USER` alatt

```
HKEY_CURRENT_USER\SOFTWARE\Google\Picasa\Picasa2\Preferences\<kulcs>
```

Ez a teljes útvonal **szó szerint** benne van a binárisban
(`0x00c8ae5c`), és három, egy helyen beállított darabból áll össze —
ezért adnak a kulcsonkénti hívások csak szekció+kulcs párost:

| darab | cím | érték |
|---|---|---|
| registry-bázis | `0x00c7f0c4` | `SOFTWARE\Google\Picasa\` |
| termék-alkulcs | `0x00c7edd0` | `Picasa2` |
| alapértelmezett szekció | `0x00c7eafc` | `Preferences` |
| *(az AppData-almappa, külön célra)* | `0x00c7eaec` | `Google\Picasa2` |
| *(a helyi adatmappa kulcsa)* | `0x00c7ef0c` | `AppLocalDataPath` |

Az összeszerelés az inicializáló blokkban látszik (`0x00407330`:
`0x0040738d`, `0x00407395`, `0x0040739d`; ugyanez a blokk a `0x00541b30`-ban
`0x00541b9b`–`0x00541bab`).

**A `HKEY_CURRENT_USER` konstans kiolvasva:** `mov eax, 0x80000001` —
a beállítás-objektum építőjében (`0x00407a3b`) és a színkezelés
olvasásánál (`0x00541bd8`) egyaránt.

**A teljes útvonal használatban, bizonyítékként:** a `0x00541b30`
így olvassa az `EnableColorManagement`-et:

```
0x00541bc9  push 0xc8ae44            ; "EnableColorManagement"
0x00541bd3  mov  ecx, 0xc8ae5c       ; "SOFTWARE\Google\Picasa\Picasa2\Preferences\"
0x00541bd8  mov  eax, 0x80000001     ; HKEY_CURRENT_USER
0x00541be9  call 0x00408060          ; a beállítás-objektum építője
0x00541bf8  call 0x004019b0          ; ÉRTÉK OLVASÁSA
```

> **Nem fájlban van.** A `research/testdata/` alatti valódi Picasa-adatmappa
> (`Picasa2/`: `cache`, `db3`, `ioqueue`, `runtime`, `tmp`) **egyetlen**
> beállításfájlt sem tartalmaz — se `.ini`, se `.xml`, se `prefs`.

### 6.2 A hozzáférés-készlet

| függvény | méret | mit csinál |
|---|---|---|
| `0x00407a20` | 297 b | beállítás-objektumot épít: `(alapérték, szekció, kulcs)`, `HKEY_CURRENT_USER` |
| `0x00408060` | 319 b | a kulcs-útvonal megnyitása; a háttér-objektum a `+0x18` mezőbe kerül |
| `0x004019b0` | 211 b | **olvasás** (a tárolt érték, vagy az alapérték) |
| `0x00401900` | 171 b | **írás** |
| `0x004018e0` | 23 b | kényelmi burkoló: `(0, "Preferences", kulcs)` |
| `0x00923720` / `0x009237f0` | — | a tényleges `Reg*` API-hívások (`RegCreateKeyExA`/`RegSetValueExA`, ill. `RegOpenKeyExW`/`RegQueryValueEx*`) |

### 6.3 A `Preferences` HÉT alszekciója

A kulcsok nem mind laposak; a binárisban ezek az alszekció-nevek állnak:

| alszekció | cím | mire |
|---|---|---|
| `Preferences\HotFolders` | `0x00c81040` | figyelt mappák |
| `Preferences\Plugins\` | `0x00ca79bc` | bővítmények |
| `Preferences\Buttons\Exclude` | `0x00cb20d8` | a gombsávból kihagyott gombok |
| `Preferences\Buttons\UserConfig` | `0x00cb20f4` | a gombsáv felhasználói összeállítása |
| `Preferences\AspectRatios` | `0x00cb832c` | a vágási oldalarányok |
| `Preferences\PrinterData` | `0x00cc3cd0` | nyomtató-beállítások |
| `Preferences\RSSDownload` | `0x00cab75c` | RSS-letöltés |

### 6.4 A `choose_mail` párbeszéd — MIT ír, MIKOR

**A kapu** (`0x007420f0`, 479 b) minden küldés előtt lefut:

```
0x00742132  mov  dword ptr [esp+0x20], 3   ; EmailPrepType ALAPÉRTÉKE = 3
0x0074213a  call 0x00407a20                ; "Preferences" / "EmailPrepType"
0x00742154  mov  dword ptr [esp+0x20], ebp ; DoNotPromptForEmailPref ALAPÉRTÉKE = 0
0x00742158  call 0x00407a20                ; "Preferences" / "DoNotPromptForEmailPref"
0x0074215d  call 0x004019b0                ; a DoNotPrompt kiolvasása
0x00742168  je   0x007421b3                ; ha 0 → MUTASD a choose_mail-t
0x0074216e  call 0x004019b0                ; különben a tárolt EmailPrepType-ot adja vissza
```

⇒ **Alapértékek, kiolvasva:** `EmailPrepType` = **3**,
`DoNotPromptForEmailPref` = **0**. Vagyis **friss telepítésen az első
küldéskor a párbeszéd MEGJELENIK.**

**Az OK-ág** (`0x0084fb10`, 494 b) a megnyomott gomb nevét `repe cmpsb`-vel
veti össze, és két értéket ismer:

| gomb | elemnév | `EmailPrepType` | cím |
|---|---|---|---|
| „Ezt használom" | `choose_mail/mymail` | **3** | `0x0084fb91`, `0x0084fb96` |
| Google Mail | `choose_mail/gsender` | **5** | `0x0084fbff` |

*(A `choose_mail/cancelbutton` és a `choose_mail/helpbutton` a másik két ág.)*

**A megőrzés szabálya** (`0x0084f6b0`, 237 b) — ez a szakasz lényege:

```
0x0084f6f6  mov bl, byte ptr [eax+0x359]  ; a choose_mail/checkbox állapota
0x0084f6fc  push 0xca9b58                 ; "DoNotPromptForEmailPref"
0x0084f718  call 0x00407a20 …             ; MINDIG kiírja
0x0084f72e  test bl, bl
0x0084f730  je   0x0084f77b               ; ha NINCS bepipálva → kilép
0x0084f732  push 0xca9b48                 ; "EmailPrepType"
0x0084f74b  call 0x00407a20 …             ; CSAK bepipálva írja ki
```

⇒ **A választott mód csak akkor marad meg, ha a „Ne kérdezze újra"
jelölőnégyzet be van pipálva.** A futó munkamenetre viszont a választás
*mindig* érvényes (`0x0084fb96`: `mov dword ptr [edx], 3` — a
memóriabeli állapotba a jelölőnégyzettől függetlenül bekerül).

Az elem, amit a `[eax+0x359]` olvas: **`choose_mail/checkbox`**
(`0x00cc23ec`) — a „Remember this setting, don't display this dialog
again." / **„Ne jelenítse meg többé ezt a párbeszédpanelt"**.

### 6.5 Eredeti / nálunk — MÉRVE

| | eredeti | nálunk (mérve) |
|---|---|---|
| tároló | `HKCU\SOFTWARE\Google\Picasa\Picasa2\Preferences\` | `QSettings` (`email_controller.py:155`) |
| kulcs: a mód | `EmailPrepType` (3 = saját levelező, 5 = Gmail) | `mail/useDefaultClient` (logikai) |
| kulcs: kérdezzen-e | `DoNotPromptForEmailPref` | *ugyanaz a kulcs* — a kettő egybeolvasztva |
| **alapérték: kérdezzen-e** | **0 → KÉRDEZ** | **`True` → NEM kérdez** (`email_controller.py:158`) |
| a kapu | `0x007420f0` | `sendRows()` (`email_controller.py:381`) — helyes |
| Google Mail-ág | `EmailPrepType = 5` | **tudatosan halott** (`EmailChoiceDialog.qml:13`) |

⇒ **Egy mért eltérés marad:** az alapérték. Nálunk friss telepítésen a
választó párbeszéd **soha nem jelenik meg** magától — csak akkor, ha a
felhasználó előbb átállítja az Opciók rádiógombját. Jegy: **#2184**.

*Bizonyítottsági fok: **megerősített*** — a bázis három darabja és az
összeszerelt teljes útvonal is kiolvasva; a `HKEY_CURRENT_USER` konstans
két helyen; az alapértékek, a kapu és a két módérték a diszasszemblyből.

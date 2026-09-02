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

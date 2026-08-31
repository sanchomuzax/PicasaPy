# Bezárás és kilépés az eredeti Picasában — mikor mit zár be az „X"

Ez a lap azt a kérdést válaszolja meg, hogy a jobb felső bezáró gomb (és a
nézetenkénti kilépők) mikor zárják a **teljes alkalmazást**, és mikor csak egy
**funkciót**. UX-részletek, amiket a felület újraépítésénél könnyű elrontani.

Forrás: a `Picasa3.exe` string- és erőforrástáblája, valamint a felület saját
`.tre` leírói. A címek visszakereshetők a
`referencia/binary-index/picasa3-index.sqlite`-ban.

## A lényeg: HÁROM külön szint van, nem egy

A Picasa nem egyetlen „bezárás" fogalommal dolgozik. Három, egymástól
független mechanizmus él egymás mellett:

| szint | mit zár | megerősítés |
|---|---|---|
| **1. Nézet-kilépő** | egy megjelenítési módot (nagy nézet, szerkesztés, diavetítés) | nincs — de van beállítás a kattintásszámra |
| **2. Lap bezárása** | egy *projektet* (kollázs, mozgófilm) | **igen**, három választással |
| **3. Alkalmazás kilépés** | az egész programot | csak feltételesen (folyamatban lévő feltöltés) |

## 1. szint — nézet-kilépők (NEM zárják az appot)

Három külön kilépő vezérlő létezik, mindegyik a saját nézetéhez tartozik:

| vezérlő | nézet | szomszédai a `.tre`-ben |
|---|---|---|
| `oneup/exit` | **nagy nézet** (egy kép) | `oneup/prev` · `next` · `rotateleft` · `star` · `caption` |
| `editoneup/exit` | **szerkesztő nézet** | `editoneup/prev` · `next` · `rotateleft` · `star` · `captionbutton` |
| `overlays/exit` | **diavetítés** | `overlays/left` · `right` · `timeline` · `startbutton` |

Ezek **visszalépnek az előző szintre**, nem zárnak alkalmazást.

> **Beállítás:** `SingleClickExit` — a Beállítások párbeszéd hivatalos magyar
> felirata: **„Szerkesztési nézetből való kilépés egy kattintással"**. Vagyis
> a szerkesztésből való kilépés kattintásszáma **felhasználói döntés**, nem
> beégetett viselkedés.

A szerkesztő nézetnek ezen felül **külön `back` vezérlője** is van
(`editoneup/back`, `editoneup/stripback`) — a kilépés és a visszalépés két
külön dolog.

## 2. szint — lap bezárása (projekt), HÁROM választással

A kollázs- és a filmszerkesztő **lapként** viselkedik, és a lap bezárásakor —
ha van nem mentett módosítás — megerősítést kér. A kollázs változat
(`0x0082c0a0`), hivatalos magyar szöveggel:

> **Cím:** Jóváhagyás…
>
> A jelenlegi kollázs nem mentett módosításokat is tartalmaz.
>
> A lap bezárása előtt menti vagy elveti ezeket? (Megjegyzés: A program a
> piszkozatokat a „Kollázsok" albumba menti.)
>
> A lap nyitva hagyásához kattintson a Mégse gombra.

**Három gomb:** `Piszkozat mentése` · `Módosítások elvetése` · `Mégse`.

A mozgófilm változata (`0x006251f0`) ugyanez a minta, az album-megjegyzés
nélkül.

> ⚠️ **Ez nem kétgombos „Mented? Igen/Nem".** A harmadik választás — „a lap
> nyitva marad" — külön van, és a szöveg ki is mondja. Egy kétgombos
> párbeszéd itt viselkedésbeli eltérés lenne.

## 3. szint — kilépés az alkalmazásból

A kilépés **alapesetben nem kérdez**, de **négy feltételes figyelmeztetés**
létezik (2026-08-15-i kiegészítés; a negyediket — `WarnClosePlugins` — a
2026-08-31-i teljes kör azonosította, ld. (d) lent).

### (a) Folyamatban lévő feltöltés (`0x0067fee0`, `CUploadManagerThread`):

> Uploads are in progress. Would you like to exit now?
> (Uploads will resume next time you run Picasa.)

**Gombok:** `Exit Now` · `Keep Going`. Vagyis a feltöltés **nem blokkolja** a
kilépést, és a következő indításkor folytatódik.

### (b) Folyamatban lévő IMPORT (`IDS_WARNCLOSEACQUIRE`, `0x005e45c0`)

> **A Picasa bezárása előtt importálja a képeket?**

**Gombok:** `Képek importálása` · `Kilépés`.

Vagyis az importálás sem blokkolja a kilépést — csak felajánlja a
befejezését.

### (c) Nem alkalmazott szerkesztés — **ÉL, LEZÁRVA (2026-08-31)**

> **Kilépés előtt alkalmazza a módosításokat a jelenlegi képre?**

A korábbi kör ezt „nincs rá kereszthivatkozás, talán halott szöveg"-ként
hagyta nyitva. **Megdőlt:** a kilépési kapu (`0x0057c4e0`) pontosan erre
az esetre hívja a `0x005e45c0`-ot, és annak szerkesztő-ágában **élő
szövegként** megvan a párja, a `CThumbUI::ConfirmAbandonModifiedEdit`
kulccsal (`0x00c975fc`):

> **Apply changes to current image before proceeding?**
> („Alkalmazza a módosításokat a jelenlegi képre, mielőtt folytatná?")

**Gombok:** `Apply Changes` · `Discard Changes` · `Cancel`
(`CThumbUI::ConfirmAbandonModifiedEditYesButton` / `…NoButton` / `il_Cancel`).

Ez tehát **az `IDS_WARNCLOSEEDIT`-nél** a valódi, megvalósított szöveg:
ugyanaz a kérdés, de „*before proceeding*" szövegváltozattal (az
`IDS_WARNCLOSEEDIT`-ben lévő „before quitting?" változat a szövegtárban
nincs bekötve — az a formás, de fel nem használt változat). A
**`0x005e45c0`** alkalmazó-ágai a tevékeny eszközt jelzik meg
(`editpanel/redeyeapply` · `cropapply` · `edittextpanel/edittextapply` ·
`editpanel/retouchapply`; Picniknél `editpanel/picnikcancel` —
`0x005e499c`–`0x005e4a8c`).

**Mikor jön elő:** aktív szerkesztő-eszköz — a kiváltó feltételek a
kilépési kapuban (`0x0057c4e0`, `0x57c55d`–`0x57c58f`):

| feltétel | bizonyíték |
|---|---|
| import/acquire fut (jelző `[app+0xdc1]`) | `0x0057c55d` |
| szövegátszerkesztés / vágás / vörösszem / arckeret él | `0x00562d00` (sztringjei: `editpanel/edittextoverlay`, `editpanel/cropselection`, `editpanel/redselection`, `peoplepanel/manual_frame`) |
| Picnik-menet aktív | `0x005f2650` (`editpanel/picnikbase`) |
| a `[app+0x2c8]` objektum foglalt (0x751bb0 igaz) | `0x57c578`–`0x57c57e` |
| videó-előnézet él (`previewclip2`) | `0x005696c0` (`editpanel/previewclip2`) |

*(A `0x005e45c0` belül további állapotokat néz: `[app+0x30d4] == 4` →
ugyanaz a `0x00751bb0`; `[app+0x30d4] == 5` → a `0x005f8d80`, a párbeszéd
másik hívóhelye — `0x5e47ce`–`0x5e47f5`.)*

### (d) Folyamatban lévő web-művelet — `WarnClosePlugins` (`0x005e4240`)

A korábbi körök ezt a négy szöveget a szövegtárban látták, de nem találták
meg a hívóját. A `0x0057c4e0`-ből levezetve **a kilépési kapu utolsó
vizsgálata, közvetlenül a leállás előtt**:

> **Figyelmeztetés**
> Ha bezárja a Picasát, azzal leállítja a be nem fejeződött műveleteket.
> Valóban bezárja a programot?

**Gombok:** `Bezárás ennek ellenére` · `Bezárás mellőzése`.
**Cím:** `WarnClosePlugins::Title` („Figyelmeztetés").

A párbeszéd akkor jön elő, ha a webes/online műveletek valamelyike fut
(feltöltő böngésző, web-export munkamenet): a feltétel három jelzőből VAGY
kapcsolatban áll (`0x005e4240`, `0x5e4250`–`0x5e42dd`):

1. `[app+0xed8]` nem nulla ÉS a `0x00699140` foglaltság-kérdezés
   `0xf4240`-ot („foglalt") ad;
2. a `0x00d67904`-nál élő (plugin-)kezelő vtable+0x24 hívása `0xf4240`-ot ad —
   ekkor a `0x009b40a0` begyűjti a műveletek neveit;
3. `[app+0xecc]` jelző: a `+5` bájt vagy a `+0x18` mező nem nulla.

A válasz **`0xf4242` (vétó)** esetén a kapu a kilépés állapotát 3-ról
2-re visszavételezi (`0x0057c5d6`), és az ablak nyitva marad.

> **Pontos jelentése a „be nem fejeződött művelet" listának** (mely
> szolgáltatások neve kerül a párbeszédbe, ha egyáltalán bekerül) ez a
> kör nem oldotta meg — a `0x009b40a0` három sztringpuffert tölt, a
> formátumsztringjét nem találtuk. BLOKKOLT: élő Picasán futtatott
> feltöltés megszakításának képernyőképe döntené el.

### Az `exit_nag` kulcs

Egy `exit_nag` beállításkulcs a `hosting`, `auto_update`, `new_album`,
`watermark` társaságában él (`0x004092e0`, 93 bájt) — ez egy **induláskor
felépített jelzőtábla**, amit az alkalmazás-inicializálás tölt fel
(`0x00409250` ← `0x004039f0`). Nem tartozik hozzá saját szöveg, tehát nem
párbeszéd, hanem **kapcsoló**. A pontos hatását ez a kör nem azonosította.

## A „Ne kérdezzen újra." KÖZÖS jelölőnégyzet

Az `IDS_CLOSE_LAST_CHECK` (**„Ne kérdezzen újra."**) **négy különböző
párbeszédben** ugyanaz az erőforrás:

| cím | mi ez |
|---|---|
| `0x0053a790` | „Lemezre menti a módosításokat?" |
| `0x005d2ad0` | az utolsó gyűjtemény bezárása |
| `0x005ee2a0` | a „Rejtett mappák" jelszó-felajánlása |
| `0x0053b2e0` | (azonosítatlan) |

Vagyis a Picasában az „elnyomható megerősítés" **egységes minta**, nem
dialógusonként külön megoldás. Ezt érdemes nálunk is közös komponensként
megvalósítani.

## Az utolsó gyűjtemény bezárása

Külön megerősítés (`IDS_CLOSING_LAST_COLLECTION_*`):

> **Bezárja a legutóbbi gyűjteményt?**
> Az utolsó gyűjteményének bezárására készül. Az indexképek területén
> egyetlen kép sem lesz látható. Folytatja?
>
> Egy gyűjtemény megnyitásához kattintson duplán a nevére, vagy kattintson a
> mellette lévő ikonra.

Figyelemre méltó, hogy a szöveg **megmondja, hogyan lehet visszacsinálni** —
nem csak figyelmeztet.

## Külön mechanizmus: „Lemezre menti a módosításokat?"

Ez **nem** bezárási párbeszéd, hanem a szerkesztések lemezre írásáé
(`0x0053a790`, `CThumbUI::FileSave::message`):

> **Lemezre menti a módosításokat?**
> *(a párbeszéd hozzáteszi: „A program biztonsági másolatot készít ezekről a
> fájlokról.")*

Elnyomható: **`DoNotAskFileSave`** beállításkulcs.

## ✅ A kilépési kapu teljes sorrendje (`0x0057c4e0`, 2026-08-31)

A **minden** bezárási út közös pontja. A főablak üzenetkezelője
(`0x005e4ac0`) a `WM_SYSCOMMAND` (`0x112`) üzenetben a `SC_CLOSE`
(`0xf060`) paraméterre **közvetlenül ezt** hívja (`0x5e4d87`–`0x5e4d90`).
Alt+F4, a rendszermenü Bezárás és a címsor X-je mind ide érkezik.

A kapu visszatérési értékei — a keretrendszer három állapotkódja:

| kód | jelentés |
|---|---|
| `0xf4240` (1 000 000) | **halasztva** — most nem léphet ki (modális, mód-ablak stb. záródik) |
| `0xf4241` | **elküldve** — a kérést továbbította |
| `0xf4242` | **vétó** — a felhasználó meggondolta magát (párbeszéd „mégse") |

A kapu lépései, sorrendben (minden lépésnél: ha kimenete `0xf4242`,
kilépés-megszakítás; ha halasztás történt, a felhasználó **újra** X-nyomása
indít egy új kört, ami a következő akadályt szedi le — tehát egy
modális + egy figyelmeztetés EGY X-nyomás alatt látszhat):

1. **Mód-ablak zárása először** (`0x57c4e3`–`0x57c513`): ha aktív mód van
   (a `0x00d67858` globális számláló 1–10), annak ablakleírója a
   `0x00d4a4a8`-nál élő tízelemes táblában van — kap egy
   `PostMessage(WM_SYSCOMMAND, SC_CLOSE)`-t. *Ez a magyarázata annak, hogy
   nagy nézetben/diavetítésben az X először a nézetet zárja.*
2. **Modális ablak zárása** (`0x57c519`–`0x57c553`): ha van modális párbeszéd,
   a `CloseModal` (`0x00983140`) vagy **elsüti a `CloseModal` névparancsot**,
   vagy — ha a vezérlő nem vétózza — `PostMessage(modális, WM_CLOSE, 0, 0)`.
   A WM_CLOSE tehát a modális ablakok útja; a főablaké az SC_CLOSE.
3. **`[app+0xdc0]` jelző** beállítva → néma halasztás (`0x57c554`).
4. **Import / szerkesztő-ág** — a fenti (b)/(c) szakasz:
   `0x005e45c0` hívása; `0xf4242`-nél megáll.
5. **`0x579330()`** igaz → `0x00566270` (előnézet/albumnézet lezárása) és halasztás.
6. **Kilépési állapot beállítása** (`0x00d678d8` → `+0x48 = 3`),
7. **`WarnClosePlugins`** (`0x005e4240`) — (d) szakasz; vétónál állapot 3→2.
8. **Leállás indítása** (`0x57c5ed`–`0x57c630`): `0x0040df60(0)`,
   `0x0097d370(app)`, `0x0057d290`, `IsZoomed`-ellenőrzés, majd a
   kilépéskori mentések (ld. lejjebb), és a visszatérési érték 0 — a
   Windows bezárhatja az ablakot.

> **Nálunk hiányzik a 2. lépés párja is:** QML-ben a modális `Dialog`
> bezárása nem egységes „elképzelhető-e most" lekérdezésen fut — lásd
> „A MI oldalunk" szakaszt.

## ✅ A bezárás anatómiája gombonként — minden bezáró vezérlő, névparanccsal

A Picasa felületi nyelvében a bezárás **névparancs** (a `0x009cd8a0`
parancs-forgalmazón át), nem ablaküzenet. A teljes leltár:

| vezérlő | névparancs / üzenet | kiadó függvény | mit zár |
|---|---|---|---|
| **főablak X** (egyéni címsor gomb) | `WM_SYSCOMMAND, SC_CLOSE` | WndProc `0x005e4d87` | a kilépési kapu fut le (kb. lépései) |
| **lap X** (kollázs/film fül) | `<lapid>/close` — a gomb az azonosítóból építi: `"%x" + "/close"` (`0x005b2553`–`0x005b2565`) | `0x005b2410` | egy projekt-lap, háromválasztós megerősítéssel |
| **jobb fiók X** (szerkesztőben) | `rightdrawerpanel/close` | `0x0057bb50` | a jobb oldali információsáv |
| **nav X** | `nav/close` | `0x005de8e0` | a bal navigációs hasáb (keresőkonténer) |
| **toys X** | `toys/close` | `0x005d56e0` | az egyszerű javítások panel eszköze |
| **modális párbeszéd X** | `CloseModal` névparancs, vagy `WM_CLOSE` | `0x00983140` | az aktuális modális ablak |
| **miniböngésző (Helyek)** X | `geo::close_tip` = „Ablak bezárása" | `0x00651580` | a geo/miniböngésző ablak |
| **EXIF-tulajdonságok** | `EXIF::Close` = „Bezárás" | `0x009f4300` | a tulajdonság-panel |
| **egér/billentyű „vissza"** | `WM_APPCOMMAND` (0x319) 1-es parancs → `editpanel/picnikcancel`, ha Picnik él | WndProc `0x5e4e86`–`0x5e4eac` | az online szerkesztés |

A címke-gombok képei egy közös gyárból jönnek: a főablak X-je a
`globalbuttons/square_close_n` / `_h` (hover) / `_p` (lenyomva) hármast
kéri (`0x00648f8f`–`0x00648f9f`), a lap X-je a `tab/close_n` / `_p` / `_h`
hármasát (`0x005b2584`–`0x005b2593`).

## ✅ Kilépéskor MENTÉSEK futnak — nem csak leállás

A kapu 8. lépésében, a szálbontás ELŐTT három mentés fut (sorrendben,
`0x0057c5ed`–`0x57c628`):

| függvény | mit ír | kulcsok |
|---|---|---|
| `0x00575f50` | **főablak-geometria** | `mainwinismax` · `mainwinpos` = `rect(%ld %ld %ld %ld)` |
| `0x00576490` | bélyegkép-méret | `Thumbscale` · `ThumbscalePeople` |
| `0x00576660` | **utolsó nézet** | `LastAlbumSelected` · `LastViewRoot` · `LastViewRoot2` |

(Vagyis a *Fájl → Kilépés menüpont* handlerében is meglévő
`GetWindowRect` (`0x00533bc0`, a `0x005cb990` parancs-diszpécser
`0x9c98`-as esetéből) ugyanebbe a menetbe tartozik: az ablak pozíciója a
kilépés pillanatában rögzül.)

> **Helyesbítés (2026-08-31, második kör):** a Fájl → Kilépés
> parancsazonisítója a javított menü-horgonnyal **`0x9c41`** (nem
> `0x9c98` — az az EPROCESS/„Order Prints" rekordja), és a `0x9c41` esete
> (`0x5cba27`) **`PostMessage(WM_SYSCOMMAND, SC_CLOSE)`**-t küld — tehát
> a menü Kilépés és az X **bizonyítottan ugyanarra a kapura** fut. A
> korábbi kör „a menü útja a kapuig nem volt nyomonkövethető" megjegyzése
> ezzel lezárult. (Az `0x9c98`-as eset — web-panel-lezárás — ettől független
> menütétel; a horgony-módszer határát ld.
> `picasa-menu-parancsok-viselkedes.md` 34.1.)

## Amit ebből érdemes átvenni

1. **Az „X" jelentése szintfüggő.** Nézetben visszalép, lapon projektet zár,
   a főablakon kilép. Egyetlen közös viselkedés nincs.
2. **A projekt-lap bezárása HÁROM választás**, nem kettő.
3. **A szerkesztésből kilépés kattintásszáma beállítás** (`SingleClickExit`),
   nem fix.
4. **A kilépés alapból nem kérdez** — négy feltételes figyelmeztetés van
   (feltöltés, import, aktív szerkesztő-eszköz, web-művelet), és egyik sem
   tiltja meg.
5. **Bezárás előtt a program sorban zárja a rétegeket**: először a mód-ablak,
   aztán a modális párbeszéd, csak aztán jönnek a kérdések.

## Ami nyitva maradt

- Az `exit_nag` kapcsoló pontos hatása (a jelzőtáblát megtaláltuk, a
  felhasználóját nem). — **ÖRÖKÖLT, a munkasorban marad.**
- ~~Él-e még az `IDS_WARNCLOSEEDIT`.~~ **LEZÁRVA (2026-08-31):** él — a
  `CThumbUI::ConfirmAbandonModifiedEdit` kulccsal, „before proceeding?"
  szöveggel, a `0x005e45c0` szerkesztő-ágában; a cím nélküli
  „before quitting?" változat a szövegtárban fel nem használt maradvány.

## ✅ A főablak bezárása MEGSZÜNTETI a háttérszálakat

Három, egymást megerősítő tény:

**1. Nincs „rejtve tovább fut" út.** A főablaknak nincs tálcaikonja
(bizonyítva lent), tehát nincs hova elrejtőznie.

**2. A program egyetlen, lineáris fő függvényből fut** (`0x004051b0`,
2533 bájt): előkészítés → futás → leállás. Ez írja a `CleanExit`
beállításkulcsot is (`0x00403fc0` induláskor, `0x00404070` kilépéskor) —
ebből tudja a következő indítás, hogy előzőleg összeomlás volt-e.

**3. A szálak bontása erőszakos.** A `ytBaseThread` bontó útja
(`0x0097b420`, a vtable 0. slotjából) pontosan ezt a három API-t hívja,
ebben a sorrendben:

```
WaitForSingleObject   →   TerminateThread   →   CloseHandle
```

Vagyis: megvárja a szálat, és **ha nem áll le, kilövi**.

> ⚠️ **Ezt a mintát NE vegyük át.** A `TerminateThread` a Windows egyik
> legdurvább API-ja: nem futtat takarítást, és nyitva hagyhat zárolásokat
> vagy félbeírt fájlt. Ez magyarázhatja a Picasa ismert, kilépéskori
> adatbázis-sérüléseit. A `.picasa.ini`-t és az indexet nálunk **rendezett
> leállítással** kell menteni.

Ez egyben megmagyarázza a feltöltés-figyelmeztetést is (3/a pont): a kilépés
tényleg megszakítaná a feltöltő szálat, ezért kérdez rá a program.

## Mellékes lelet: Wine-felismerés

A `0x00403640` a `kernel32`-ben a `wine_get_unix_file_name` függvényt keresi,
és ettől teszi függővé a `BgFaceDetectThread` beállítást — vagyis a Picasa
**felismeri, ha Wine alatt fut**, és a háttér-arcfelismerést másképp kezeli.

## ✅ A főablaknak NINCS tálcaikonja — bizonyított negatív eredmény

A `Picasa3.exe` **feloldja** a tálcaikon-API-t, de **soha nem hívja meg**.

A feloldó csonk (`0x00c33c22`) a `GetVersion` alapján választ ágat — ez a
Windows 9x/NT korszak öröksége:

```asm
call [0x00c40450]                       ; GetVersion
mov  [0x00d6fc58], eax
cmp  dword [0x00d6fc58], 0x80000000
jae  9x_ag
mov  dword [0x00d695c4], 0x009b2d00     ; NT: ANSI→wide burkoló
ret
9x_ag:
mov  eax, [0x00c405fc]                  ; Shell_NotifyIconA
mov  [0x00d695c4], eax
ret
```

**A bizonyíték:** a `0x00d695c4` globális a teljes binárisban **pontosan
kétszer** fordul elő — mindkétszer a fenti csonkban, ahol *beállítják*.
`call [0x00d695c4]` **sehol nincs**, és a `Shell_NotifyIconA`
IAT-bejegyzésére (`0x00c405fc`) sincs közvetlen hívás.

> **Következtetés:** ez egy közös operációsrendszer-absztrakciós réteg
> maradványa (ugyanaz a csonk-minta, ami a mappafigyelő burkolóját is
> feloldja) — a főprogram nem használja. **A Picasa főablaka nem tesz ikont a
> tálcára.** A tálcaikon a `PicasaPhotoViewer.exe` és a `MovieThumb.exe`
> sajátja.
>
> **A PicasaPy-nak tehát nem kell tálcaikon** a főablak-paritáshoz.

## A MI oldalunk — mért állapot (2026-08-31, #671)

A `src/picasapy/app/qml/Main.qml` `ApplicationWindow`-ja **nem rendelkezik
`onClosing` kezelővel** (mérés: `rg -n "onClosing" src/picasapy/app/qml/` →
csak a `CompactDatabaseDialog.qml:56`-ban van, ami a tömörítés-menetet
szakítja meg). Ezért ma a főablak X-je **feltétel nélkül becsukja a
programot** — nincs réteg-zárás (2. lépés), nincs a négy kilépési
figyelmeztetés, és nincs mód-függő viselkedés.

| pont | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| főablak X | kilépési kapu: 8 lépés (mód-ablak → modális → import → eszköz → web-művelet → leállás-mentések) | **nincs `onClosing`** — azonnali bezárás | `onClosing`-kezelő + kilépési kapu sorrend |
| feltöltés-figyelmeztetés | `Exit Now`/`Keep Going` párbeszéd | nincs (nem mérve futó feltöltéssel — nincs feltöltés nálunk) | nincs mit átvinni, amíg nincs feltöltés |
| import-figyelmeztetés | „Képek importálása"/„Kilépés" | nincs `onClosing`, az import panelnek sincs futás-állapota | az import-állapot jelzője + párbeszéd |
| aktív szerkesztő-eszköz megerősítés | „Alkalmazza a módosításokat…?" (Apply/Discard/Cancel) | nincs; eszközöknél van beépített alkalmazás/elvetés, de kilépésnél nem kérdez | eszköz-mód lekérdezése + párbeszéd |
| web-művelet figyelmeztetés | `WarnClosePlugins` (Bezárás ennek ellenére / mellőzése) | nincs (nincs web-műveletünk) | később, a feltöltővel együtt |
| lap X | `<lapid>/close` → háromválasztós megerősítés | **megvan** — `DocumentTabStrip.qml` + `CollageDialogs.qml` (`Piszkozat mentése`/`Módosítások elvetése`/`Mégse`) | — (kész) |
| utolsó gyűjtemény bezárása | megerősítés + `DoNotAskOnLastCollectionClose` elnyomó-kulcs | `FolderPane.qml:198` `closingHidesEverything()` — a megerősítés él; az elnyomó-kulcs nincs | `DoNotAskOnLastCollectionClose` kulcs felvitele |
| modális lezárás kilépéskor | `CloseModal` / `WM_CLOSE` egyenként, ellenőrzéssel | nincs egységes modális-leltár | a kapu 2. lépése |
| kilépéskori geometria-mentés | `mainwinismax` + `mainwinpos` = `rect(...)` kilépéskor | **megvan** — `window_geometry.py` a `visibilityChanged(Hidden)` jelre menti (`application.py` beköti); kulcsneveink eltérnek, a viselkedés (maximalizált-jelző + négyzetes rect) hasonló | — (kész; a kulcsnevek egyeztetése nem cél) |
| kilépéskori „utolsó nézet" mentés | `LastAlbumSelected` · `LastViewRoot`/`2` | **nem mérve** ebben a körben — az indulás-oldal (#1571/#1706) körébe tartozik | az indulás/indulási kör ki méri |

**A teendő szűkebben:** a megvalósítás maga a `Main.qml`
`onClosing`-kezelője és egy Python-oldali „kilépési kapu" (a
`controller.py`-ban), ami a fenti sorrendben futtatja a vizsgálatokat.
Ez a #671 megvalósítási jegye; a Windows-specifikus API-k (SC_CLOSE,
WM_CLOSE) nálunk QML-szinten egyszerűsítendők. **Megjegyzés a
PySide6-korlátról:** a `window_geometry.py` fejléce rögzíti, hogy a
`closing` jel `QQuickCloseEvent` paraméterét a PySide6 nem tudja
Python-oldalra konvertálni — ezért az „elfogadható-e a bezárás" döntés a
QML-oldali `onClosing`-ben születik, és a Python-kaput jelzésen át
kérdezi. A geometria-mentés ennek a korlátnak a megkerüléseként már a
`visibilityChanged(Hidden)` jelre fut — az új kapunak erre a mintára kell
épülnie.

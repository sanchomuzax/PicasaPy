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

A kilépés **alapesetben nem kérdez**, de **három feltételes figyelmeztetés**
létezik (2026-08-15-i kiegészítés).

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

### (c) Nem alkalmazott szerkesztés (`IDS_WARNCLOSEEDIT`)

> **Kilépés előtt alkalmazza a módosításokat a jelenlegi képre?**

> ⚠️ **Bizonytalan, hogy él-e.** Ez az egyetlen a három közül, amelyre a
> string-kereszthivatkozási tábla **nulla hívót** ad. Vagy közvetett úton
> hivatkozzák, vagy megírt, de már nem használt szöveg. Megvalósítás előtt
> érdemes élő Picasán ellenőrizni.

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

## Amit ebből érdemes átvenni

1. **Az „X" jelentése szintfüggő.** Nézetben visszalép, lapon projektet zár,
   a főablakon kilép. Egyetlen közös viselkedés nincs.
2. **A projekt-lap bezárása HÁROM választás**, nem kettő.
3. **A szerkesztésből kilépés kattintásszáma beállítás** (`SingleClickExit`),
   nem fix.
4. **A kilépés alapból nem kérdez** — csak folyamatban lévő feltöltésnél, és
   akkor sem tiltja meg.

## Ami nyitva maradt

- Az `exit_nag` kapcsoló pontos hatása (a jelzőtáblát megtaláltuk, a
  felhasználóját nem).
- Él-e még az `IDS_WARNCLOSEEDIT` (nincs rá kereszthivatkozás).
*(Ez a szakasz kiürült — mindkét kérdés lezárult, ld. lent.)*

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

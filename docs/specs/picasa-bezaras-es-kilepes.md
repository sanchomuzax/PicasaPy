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

A kilépés **alapesetben nem kérdez**. Egyetlen ismert feltételes
figyelmeztetés van (`0x0067fee0`, `CUploadManagerThread`):

> Uploads are in progress. Would you like to exit now?
> (Uploads will resume next time you run Picasa.)

**Gombok:** `Exit Now` · `Keep Going`. Vagyis a feltöltés **nem blokkolja** a
kilépést, és a következő indításkor folytatódik.

Létezik továbbá egy `exit_nag` **beállításkulcs** (a `hosting`,
`auto_update`, `new_album`, `watermark` társaságában, `0x004092e0`) — a
kilépéskori figyelmeztetés kapcsolója. A konkrét szövegét ez a kör nem
azonosította.

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

- Az `exit_nag` pontos szövege és kiváltó feltétele.
- Zárja-e a főablak „X"-e a háttérfolyamatokat (arcfelismerés, mappafigyelés),
  vagy azok külön élnek — a `Shell_NotifyIconW` (`0x009b2d00`) tálcaikon-
  kezelés jelen van, de a tulajdonosát ez a kör nem azonosította.

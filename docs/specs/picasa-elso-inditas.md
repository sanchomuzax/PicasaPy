# Az ELSŐ INDÍTÁS panelje — `initialscan` (2026-08-21)

Az eredeti Picasa 3.9.141.259 első indításakor **nem a Mappakezelő nyílik
meg**, hanem egy külön, teljes felületű panel: az **`initialscan`**. Ez a
lap azt írja le teljesen.

**Források:** `runtime/respack.yt` → `tre:initialscan` (3167 bájt) és 18
rajzi rétege · `Picasa3.exe` (`0x005b77c0`).

*(A kérdés a Mappakezelő-kör **M4** tételéből jött: „mi az első indítás
belépési útja a Mappakezelőhöz?" — a válasz: **nincs ilyen út**, ld. 4.)*

---

## 1. KÉT változat, egy panel

A `tre:initialscan` **két teljes szövegkészletet** tartalmaz ugyanarra a
felületre (`Text1` és `Text2` előtaggal) — a program a helyzet szerint
választ:

### 1.1 `Text1` — MIGRÁCIÓ (van korábbi Picasa)

| elem | szöveg |
|---|---|
| `text1` | Picasa |
| `text2` | There is an older version of Picasa installed.  Would you like to update your existing picture library, or search your computer for pictures again? |
| `text2a` | Please choose from the following options: |
| `text3` | **Update my existing picture library** |
| `text3a` | Choose this option if you use keywords or custom albums in Picasa 1, and you want to preserve these in Picasa 3. |
| `text4` | **Search my computer for pictures again** |
| `text4a` | Choose this option for a more complete search of your computer, which includes extended picture information.  It will preserve your existing edits and organization, but it will not preserve keywords.  This search may take several minutes. |
| `text5` | Searching for pictures never moves or copies files to new locations. You can choose which folders are displayed by Picasa by using the Folder Manager tool (available from the Tools menu) |
| `ok-label` | **Continue** |

### 1.2 `Text2` — TISZTA TELEPÍTÉS (lemez-beolvasás)

| elem | szöveg |
|---|---|
| `text2` | Picasa is ready to search for pictures on your computer |
| `text2a` | Please choose from the following options: |
| `text3` | **Only search Documents, Pictures, the Desktop, and iPhoto Library** |
| `text3a` | Choose this option if you only store your pictures in these folders. |
| `text4` | **Search my whole computer for pictures** |
| `text4a` | Choose this option if you have pictures stored in various folders across your computer, especially if you have pictures stored on more than one hard drive. |
| `text5` | *(ua., „displayed **in** Picasa" szórenddel)* |
| `ok-label` | **Continue** |

> **A `text5` mindkét változatban ugyanazt ígéri:** a keresés **soha nem
> mozgat és nem másol fájlt**, és a megjelenített mappák a
> **Mappakezelőből** állíthatók („available from the Tools menu").

---

## 2. Geometria (tervezővászon: **640 × 463**)

| elem | x0 | y0 | x1 | y1 | méret |
|---|---:|---:|---:|---:|---|
| `docbounds` / `baseclip` | 0 | 0 | **640** | **463** | a panel mérete |
| `base` | 0 | 0 | 19 | 463 | 19×463 — bal oldali sáv (RLE) |
| `title` (`globalbuttons/logo_n`) | 15 | 13 | 39 | 37 | 24×24 — a Picasa-logó |
| `text1` | 48 | 9 | 620 | 36 | `m_displayfont24` |
| `text2` | 20 | 63 | 620 | 93 | `m_systemfont16` |
| `text2a` | 20 | 103 | 620 | 133 | `m_displayfont14`, **`m_hidden`** |
| `radiogroup` | 20 | 134 | 620 | 337 | 600×203 |
| **`radio_limited`** | 35 | **136** | 65 | 166 | 30×30 |
| `text3` | 71 | 138 | 620 | 161 | `m_systemfont14` |
| `text3a` | 71 | 163 | 620 | 231 | `m_displayfont14` |
| **`radio_complete`** | 35 | **236** | 65 | 266 | 30×30 |
| `text4` | 71 | 238 | 620 | 261 | `m_systemfont14` |
| `text4a` | 71 | 263 | 620 | 337 | `m_displayfont14` |
| **`connector`** | 21 | 150 | 30 | 252 | 9×102 — a két rádiót összekötő rajz |
| `text5` | 20 | 339 | 620 | 408 | `m_displayfont14` |
| **`ok`** („Continue") | **522** | 423 | 620 | 452 | 98×29 |
| `cancel` („No") | 414 | 423 | 512 | 452 | 98×29 — **`m_hidden`** |

**Négy dolog, amit ez kimond:**

1. **A rádiók 100 képpont osztásban** vannak (136 → 236), 30×30-asak, és a
   felirat a rádió jobb szélétől **+6** képponttal kezdődik (65 → 71).
2. Van egy **`connector`** grafika (9×102) a két rádió közt a bal
   szélen — vizuális kapocs, nem szöveg.
3. **A Mégse gomb REJTETT** (`initialscan/cancel: root m_hidden`) — az
   első indításnál **nem lehet kihagyni a választást**, csak a
   „Continue".
4. A `text2a` („Please choose from the following options:") **alapból
   rejtett**, tehát csak az egyik változatban jelenik meg.

A rádiók `m_hit_childlabel`-t viselnek: **a feliratra kattintva is
elsülnek**.

---

## 3. A kód

A tiszta telepítés „csak ezek a mappák" szövegének régebbi alakja
(`"Only search My Documents, My Pictures, and the Desktop"`) a
**`0x005b77c0`** függvényben van — ez a panel kezelője.

*(A két rádió pontos hatása — mit ír a `scanlist.txt` `+` szakaszába a
„whole computer", és mit a szűkített — a `0x005b77c0` végigolvasásán
múlik; ld. 5.)*

---

## 4. Az M4 válasza: az első indítás NEM a Mappakezelőt nyitja

A Mappakezelőnek **két** belépési pontja van, mindkettő menü
(`ID_TOOLS_INCLUDEEXCLUDEFOLDERS`, parancs `0x9caa` — ld.
`picasa-mappakezelo.md` 10/b.1). Az első indítás **külön panelt** mutat,
és a Mappakezelőre csak **szövegben** utal.

*Bizonyítottsági fok: **megerősített** — a `tre:initialscan` szó szerinti
tartalma és a rétegek mért geometriája; a Mappakezelő-oldali negatívum a
parancsazonosító teljes menü-leltárából.*

---

## 5. Ami NYITVA marad

1. **Mit ír a két rádió.** A `0x005b77c0` végigolvasása adná meg, hogy a
   „Search my whole computer" a `scanlist.txt` `+` szakaszába a
   meghajtó-gyökereket teszi-e (a valódi mintánkban `+C:\`, `+L:\`,
   `+E:\`, `+D:\` áll — `picasa-mappakezelo.md` 11.3), és mit tesz a
   szűkített változat.
2. **Mi dönti el, melyik szövegkészlet (`Text1`/`Text2`) jelenik meg** —
   a „van-e korábbi Picasa" vizsgálat helye.
3. **Hol jelenik meg a panel** (saját ablak vagy a főablakba ágyazva), és
   mi történik, ha a felhasználó bezárja az ablakot (a Mégse rejtett).

# A „Létrehozás" menü funkciói — az eredeti működés (2026-08-07)

Forrás: a Picasa 3.9.141.259 telepítése — a `respack.yt`-ből kinyert `.tre`
elrendezés- és szövegforrások (`tools/picasa/respack.py`), a `Picasa3.exe`
string-táblája és a `Picasa3i18n.dll` feliratai.

Eddig ezekről a funkciókról **csak a menüpont neve** volt meg
(`ui-audit-menus.md`, 6. Létrehozás). Itt a tényleges működés.

## 1. Képkollázs (`ID_COLLAGEMAKER`)

### 1.1 Hat kollázs-típus

Az `.exe` `collage::*_desc` sztringjeiből, a belső kulcsokkal együtt:

| kulcs | név | leírás (eredeti) |
|---|---|---|
| `pile` | Picture Pile | „Looks like a pile of scattered pictures" — szétszórt kupac |
| `pack` | Mosaic | „Automatically fit pictures into the page" — automatikus kitöltés |
| `frame` | Frame Mosaic | „A mosaic with a prominent center picture" — mozaik kiemelt középső képpel |
| `grid` | Grid | „Arrange pictures into regular rows and columns" — szabályos rács |
| `csheet` | Contact Sheet | „Thumbnails with an informative header" — indexkép-ív fejléccel |
| `multiexp` | Multiple Exposure | „Superimpose pictures over one another" — egymásra vetítés |

### 1.2 Három képkeret-stílus

| kulcs | név | leírás |
|---|---|---|
| `noborder` | (nincs) | „Just the picture without a border" |
| `whiteborder` | Fehér szegély | „A plain white border" |
| `polaroid` | Polaroid | „Looks like a familiar brand of instant camera" |

A **Polaroid keretnél** külön képfelirat-lehetőség van: *„Show captions as
text on pictures with an »Instant Camera« border"* — vagyis a felirat csak
ennél a keretnél jelenik meg a képen.

### 1.3 Beállítások (a `collagepanel` feliratai)

- **Két fül:** `Settings` (Beállítások) és `Clips` (Klipek).
- **Grid Spacing** csúszka (`None` … `Max.`).
- **Draw Shadows** jelölő — árnyékrajzolás.
- **Show Captions** jelölő (ld. fent).
- **Background Options:** `Solid Color` · `Use Image` · `Use selected`
  (a kijelölt kép legyen a háttér). Az `.exe`-ben a háttér-módok:
  `solid`, `dimmed`, és a **`collage::avgcolor`** — vagyis a kollázs
  háttere lehet a képek **átlagszíne** (ugyanaz az `avgcolor`, amit a
  `color:` keresés is használ, ld. `picasa-ini-format.md`).
- **Page Format:** oldalarány-választó (`Portrait` / `Landscape` + arány-
  lista), és **egyéni oldalarány** felvehető — ehhez tartozik a
  `runtime/customaspectratio.fen` dialógus. A listában szerepel a
  **„Current display"** (a képernyő aktuális mérete).
- **Randomizálók:** `Shuffle Pictures` (sorrend) és `Scramble Collage`
  (elrendezés).

### 1.4 Kép-szintű műveletek a vásznon

Rétegsorrend: `Move to the top of the pile` · `Move picture up` ·
`Move picture down` · `Move to the bottom`. Továbbá `Set as Background`,
`Set as Frame Center`, `Remove` (Del), `Select All` (Ctrl-A),
`Select None` (Ctrl-D).

**Forgatás-illesztés (snap):** a `snap_12` / `snap_3` / `snap_6` / `snap_9`
gombok az óralap szerint 0° / 90° / 180° / 270°-ra igazítanak.
Vonszolás közben a kijelzett értékek formátuma: `Angle: %d` és
`Scale: %d%%` (`collage::angle_format`, `collage::scale_format`).

### 1.5 Mentés, projektfájl, automatikus mentés

- **Kimenet:** JPG a **„Collages"** albumba, a **Projektek** gyűjteményen
  belül (`CCollageManager::CollagesFolder` = `Collages`, tooltip: *„Save as
  a JPG image in the Collages album (within the Projects collection)"*).
- **Projektfájl: `.cxf`** — a kollázs szerkeszthető állapota. Mentéskor
  `.jpg.tmp` és `.cxf.tmp` átmeneti fájlok készülnek.
- **Automatikus mentés + helyreállítás:** `CAutosaveCollageThread`,
  `autosave.cxf`, és a `collage::recoveredautosave` / `lastautosave`
  üzenetek — a Picasa összeomlás után felajánlotta a visszaállítást.
- A kimeneti mappa mellé **`.picasa.ini` készül** `[encoding] utf8=1` és
  `[Picasa] name=…` szekciókkal (az `.exe`-ben közvetlenül az `autosave.cxf`
  után állnak ezek a format-sztringek) — vagyis a projekt-albumok is a
  normál ini-modellt használják.

### 1.6 A `.cxf` tartalma (a szerializált mezőnevekből)

Az `.exe` egy tömbben tartalmazza a kollázs-specifikáció mezőneveit:

```
orientation · portrait · landscape · theme · shadows · captions
albumUID · albumID · theta · scale · background · spacing
albumTitle · albumDate
```

Olvasat: a specifikáció **képenként** tárolja a `theta` (forgatás) és
`scale` (méret) értéket — ezért tud a „kupac" típus pontosan visszaállni —,
album-szinten pedig a témát, tájolást, árnyékot, feliratot, hátteret és
térközt. A `%d:%d:%d:%d` formátum a háttérszínhez tartozik.

### 1.7 Figyelmeztetések (átvehető viselkedés)

- **„Format Mismatch Warning"** — ha az asztali háttérképnek mentesz, de a
  kollázs oldalaránya nem egyezik a képernyőével: *„…This may result in a
  desktop background that does not look as expected. (TIP: Choose »Current
  display« in the Page Format dropdown menu…)"* — gombok: `Set Anyway` /
  `Don't Set`.
- **„Selection Required"** — a Frame Mosaic középső képéhez: *„Please select
  the single image you want to place in the center of the collage BEFORE
  pressing this button."*
- **„Save Skipped"** — ha minden képet eltávolítottál: *„The collage cannot
  be saved because all of the pictures have been removed."*

### 1.8 Menük

`CollageS` (kép a vásznon): Legfelülre / Legalulra helyezés · Beállítás
háttérként · Beállítás képkockaközéppontként · Eltávolítás · Megjelenítés és
szerkesztés. `CollageD` (vászon): Képek összekeverése · Képek szétszórása ·
Az összes kijelölése / kijelölés megszüntetése. `Border`: Egyik sem · Fehér
szegély · Polaroid fényképezőgép. (Ld. `ui-audit-menus.md` K.9.)

## 2. Film készítése (`ID_MAKEMOVIE`, `eMenuCreateMovie`)

### 2.1 Átmenetek — a teljes lista, belső kulccsal

| kulcs | név |
|---|---|
| `cut` | (vágás, átmenet nélkül) |
| `dissolve` | Dissolve |
| `dissolveblack` | Dissolve through black |
| `dissolvewhite` | Dissolve through white |
| `wipeleft` / `wiperight` / `wipeup` / `wipedown` | Wipe – left / right / top / bottom |
| `diagwipeul` / `diagwipeur` / `diagwipedl` / `diagwipedr` | Wipe – up left / up right / down left / down right |
| `pushleft` / `pushright` / `pushtop` / `pushdown` | Push – left / right / top / bottom |
| `circlein` / `circleout` | Circle – inwards / Circle |
| `kenburns` | **Pan and Zoom** (Ken Burns-effekt) |
| `kenburnsaoi` | **Pan and Zoom – face** (arcra fókuszáló Ken Burns) |
| `timelapse` | Time Lapse |

A `kenburnsaoi` külön említést érdemel: a Picasa az **arcfelismerés
eredményét** használta a Ken Burns-mozgás célpontjául.

### 2.2 Beállítások

- **Slide Duration** csúszka — kiírás: `Slide Duration: %s Sec`.
- **Total Photos** csúszka — `Total Photos: %s`.
- **Overlap** (átmenet-hossz) csúszka.
- **Idő-szűrő:** „Don't filter by time taken" … `Remove Photos Taken Within %s`
  — sorozatfelvételek ritkítása.
- **Dimensions** (kimeneti méret), **Show Captions**, **Show Dates**,
  **Full frame photo crop**, **Remove Low Resolution Faces**.
- **Diasorrend:** `Best Transitions` (okos) · `Album Order` · `Chronological`.
- **Hangsáv:** `Load…` / `Clear` + `Options`.

### 2.3 Szöveges dia — 11 stílus

`CMakeMoviePanel::textstyleN`: Caption – Classic · Gradient – Black ·
Gradient – White · Transparent – Black · Transparent – White ·
**Scrolling Credits** · Music Video – Left · Music Video – Right ·
Caption – Typewriter (+ további kettő). Betűbeállítás: család, méret,
`Bold`, `Italic`, és **„Automatic Outline (like movie subtitles)"**.

### 2.4 Projektfájl és automatikus mentés

`autosave.mxf` (`MakeMoviePanel::autosave` / `recoveredautosave`) — a
kollázs `.cxf`-jének megfelelője a filmhez: **`.mxf` a film-projektfájl**.

### 2.5 „Film arcokból"

Az `eMenuCreateMovie` két tétele: **A kijelölésben lévő arcokból…**
(`ID_FACES`) és **Az Emberek albumból…** (`ID_FACESRANDOM`). Az
alapértelmezett cím: „People Movie". Az arc-film külön képfelbontással
dolgozik (`facemakemovieres` vs `makemovieres`).

## 3. A Létrehozás menü többi tétele

| menüpont | ID | mit tudunk |
|---|---|---|
| Poszter készítése… | `ID_POSTER` | dialógusa megvan: `runtime/poster.fen` — nagyítás 200–1000% tíz lépésben, papírméret-választó, **„Overlap tiles"** jelölő; a súgó-szöveg: *„ha nem akarsz vágni, vágd a képet a papír méretére"* |
| Beállítás háttérképként | `ID_WALLPAPER` | egyképes asztali háttér (a kollázs-panelnek külön `Desktop Background` gombja van) |
| Hozzáadás a képernyővédőhöz… | `ID_SCREENSAVER` | a képek `screensaver=yes` ini-kulcsot kapnak (`picasa-ini-format.md`); a `saverlist.txt` tárolja a listát |
| Ajándék CD készítése… | `ID_BURNCD` | a `cdautorun/` mappa tartalma megy a lemezre (Windows autorun + Mac `.app`), dialógus: `runtime/cdchoose.fen` |
| Közzététel a Bloggeren… | `ID_EXPORT_SENDTOBLOGGER` | a `buttons/core-lh2.pbz` `custombutton/blogger` gombja: `verb="hybrid"`, URL `https://photos.blogger.com/picasa-post.g` — a szolgáltatás megszűnt |
| Exportálás TiVo DVR-re… | `ID_TIVO` | a `plugins/ytITivo.yti` plugin (TiVo Desktop-integráció) |
| Indexképek nyomtatása… | `ID_FILE_PRINTCONTACTSHEET` | a Contact Sheet kollázs-típus nyomtatási párja |

## 4. Mit érdemes ebből átvenni

1. A **hat kollázs-típus** és a **három keret** jól definiált, mind
   megvalósítható tisztán geometriából — nincs benne titkos algoritmus.
2. A **`.cxf` mezőnevek** adják a saját projektformátumunk vázát; ha
   ugyanezeket használjuk, egy későbbi `.cxf`-import is nyitva marad.
3. Az **automatikus mentés + helyreállítás** a kollázsnál és a filmnél is
   alapfelszereltség volt — a felhasználó munkája sosem veszett el.
4. Az **átmenet-készlet** (18 darab) és a **11 szövegstílus** kész
   specifikáció a filmkészítőhöz.
5. A **Pan and Zoom – face** az arcfelismerés és a diavetítés
   összekapcsolása — ez a Picasa egyik legkedveltebb apró trükkje.

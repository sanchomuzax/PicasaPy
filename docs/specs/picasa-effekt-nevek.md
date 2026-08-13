# Az effektek nevei és buboréksúgói — a Picasa saját szótára

A `Picasa3i18n.dll` `filter_<szűrő>_label<N>` és `filter_<szűrő>_tooltip<N>`
kulcsai. **83 szűrő**, mind a 41 nyelven — itt az angol és az eredeti magyar.

*(A `filterdesc.xml` 84 szűrőt sorol; a felirat-táblában 83-nak van neve. A
kettő nem ugyanaz a halmaz: a `filterdesc` belső segéd-bejegyzéseket is
tartalmaz, a felirat-tábla viszont csak azt, aminek a felületen neve van.)*

- `label0` = **a szűrő neve** a felületen,
- `label1…N` = **a vezérlői**, a `filters=` láncbeli sorrendben,
- `tooltip0` = a gomb buboréksúgója.

Ez a lap a [`picasa-effekt-feliratok.md`](picasa-effekt-feliratok.md) párja: ott
a 32 Glimmer-effekt vezérlő-szótára (`ImageFilters::`) van, itt **az összes
szűrő neve** — a natív és a rejtett örökölt szűrőké is.

## Miért ez az igazságforrás

A saját elnevezéseink több helyen eltérnek. Néhány példa a mai kódunkból:

| a mi nevünk | az eredeti |
|---|---|
| „Softening" (`blur`) | **Blur** — „Elhomályosítás" |
| „White Point" (`whitept`) | **Whitepoint** — „Fehérpont" |
| „Directional Sharpening" | **Directional Sharpen** — „Irányított élesítés" |
| „Lighting Fixes (v1/v2/v3)" | mindhárom neve **Lighting Fixes** — „Megvilágítási javítások"; a **paramétereik** különböznek, nem a nevük |
| „Focal Pixelate (legacy)" | **Focal Pixelate** — „Képpontnövelés" |

## ⚠️ Az eredeti magyar fordítás NEM mindenhol jó

A szótár értékes, de **nem szentírás** — négy helyen egyértelműen hibás vagy
félrevezető, és ezeket nem szabad átvenni:

| kulcs | az eredeti magyar | mi a baj | javaslat |
|---|---|---|---|
| `CrossProcess` | „Áttűnés" | **félrefordítás**: a cross processing sötétkamrai eljárás (fordított hívó), nem áttűnés | **„Keresztelőhívás"** |
| `radsat` | „Telítetlen egy középpont körül" | **nem mondat** (az angol ige főnévnek fordítva) | **„Telítetlenít egy középpont körül"** |
| `Pixelate` / `PicnikFocalPixelate` | „Képpontnagyítás" / „Képpontnövelés" | a kettő **felcserélhetően hangzik**, pedig más effekt | **„Kockásítás"** és **„Kockásítás fókuszban"** |
| `ReanimatedEyeColor` | „Vámpírszem" | maga a név rendben, de a súgója („nem valódi megjelenésűvé") semmitmondó | súgó: **„Természetellenes színt ad a szemeknek"** |

Máshol a fordítás pontos és idiomatikus (pl. „Lágy fókusz", „Sugaras árnyalás",
„Fokozatos szűrő, hasznos az egeknél") — azokat érdemes szó szerint átvenni,
mert a felhasználó ezeket ismeri a régi programból.

**Szabály:** a szótárból átvett magyar szöveget **olvasd át**, mielőtt a
felületre kerül. Az eredeti fordítás minősége szűrőnként változik.

## A teljes táblázat

| szűrő | név (magyar) | angol | vezérlők |
|---|---|---|---|
| `ansel` | **Szűrt FF** | Filtered B&W | — |
| `autobacklight` | **Derítőfény** | Fill Light | — |
| `autocolor` | **Automatikus szín** | Auto Color | — |
| `autocontrast` | **Automatikus kontraszt** | Auto Contrast | — |
| `autolight` | **Automatikus kontraszt** | Auto Contrast | — |
| `backlight` | **Háttérfényjavítás** | Backlight Fix | **Mennyiség** *(Amount)* |
| `blur` | **Elhomályosítás** | Blur | **Küszöbérték** *(Threshold)* |
| `Boost` | **Felpörgetés** | Boost | — |
| `Border` | **Szegély** | Border | — |
| `bw` | **Fekete-fehér** | B&W | — |
| `Cinemascope` | **Kinemaszkóp** | Cinemascope | — |
| `colorfix` | **Színjavítások** | Color Fixes | **Fehérpont választása** *(Choose White Point)* · **Színhőmérséklet** *(Color Temperature)* |
| `colortemp` | **Színhőmérséklet** | Color Temperature | **Hidegtől a melegig** *(Cool to Warm)* · **Fehérváltás** *(White Shift)* |
| `Comicize` | **Képregény** | Comic Book | — |
| `contrast` | **Kontraszt** | Contrast | **Kontraszt** *(Contrast)* |
| `crop` | **Vágás** | Crop | — |
| `crop64` | **Vágás** | Crop | — |
| `CrossProcess` | **Áttűnés** | Cross Process | — |
| `dir_brite` | **Irányított fényesség** | Directional Brightness | **Balról jobbra** *(Left to Right)* · **Felülről lefelé** *(Top to Bottom)* |
| `dir_sat` | **Irányított telítettség** | Directional Saturation | **Balról jobbra** *(Left to Right)* · **Felülről lefelé** *(Top to Bottom)* |
| `dir_sharp` | **Irányított élesítés** | Directional Sharpen | **Balról jobbra** *(Left to Right)* · **Felülről lefelé** *(Top to Bottom)* |
| `dir_tint` | **Színátmenet** | Graduated Tint | **Lágy perem** *(Feather)* · **Árnyék** *(Shade)* |
| `DropShadow` | **Árnyékvetés** | Drop Shadow | — |
| `enhance` | **Jó napom van** | I'm Feeling Lucky | — |
| `fill` | **Derítőfény** | Fill Light | — |
| `finetune` | **Finomhangolás** | Tuning | **Derítőfény** *(Fill Light)* · **Kiemelések** *(Highlights)* · **Árnyékok** *(Shadows)* · **Színhőmérséklet** *(Color Temperature)* |
| `finetune2` | **Finomhangolás** | Tuning | **Derítőfény** *(Fill Light)* · **Kiemelések** *(Highlights)* · **Árnyékok** *(Shadows)* · **Színhőmérséklet** *(Color Temperature)* |
| `focalpixelate` | **Képpontnövelés fókuszban** | Focal Pixelate | **Képpontméret** *(Pixel Size)* · **Fókuszméret** *(Focal Size)* · **Élkeménység** *(Edge Hardness)* · **Halványítás** *(Fade)* |
| `FocalZoom` | **Fókusznagyítás** | Focal Zoom | — |
| `gamma` | **Gammakorrekció** | Gamma Correct | **Szint** *(Level)* |
| `glow` | **Ragyogás (régi)** | Glow (Old) | **Intenzitás** *(Intensity)* · **Sugár** *(Radius)* |
| `glow2` | **Ragyogás** | Glow | **Intenzitás** *(Intensity)* · **Sugár** *(Radius)* |
| `grain` | **Régi filmszemcse** | Film Grain (Old) | — |
| `grain2` | **Filmszemcse** | Film Grain | — |
| `HDR` | **HDR-szerű** | HDR-ish | — |
| `HeatMap` | **Hőtérkép** | Heat Map | — |
| `Holga` | **Holga-szerű** | Holga-ish | — |
| `Invert` | **Színinvertálás** | Invert Colors | — |
| `IR` | **Infravörös film** | Infrared Film | — |
| `linblur` | **Lineáris homályosítás** | Linear Blur | **Mennyiség** *(Amount)* |
| `LocalContrast` | **Helyi kontraszt** | Local Contrast | — |
| `Lomo` | **Lomo-szerű** | Lomo-ish | — |
| `Matte` | **Matt** | Matte | — |
| `movieend` | **Végpont** | End Point | — |
| `moviestart` | **Kezdőpont** | Start Point | — |
| `MuseumMatte` | **Múzeumi matt** | Museum Matte | — |
| `Neon` | **Neon** | Neon | — |
| `NightVision` | **Éjjellátó** | Night Vision | — |
| `Orton` | **Orton-szerű** | Orton-ish | — |
| `PencilSketch` | **Ceruzarajz** | Pencil Sketch | — |
| `picnik` | **Kreatív készlet** | Creative Kit | — |
| `PicnikFocalPixelate` | **Képpontnövelés** | Focal Pixelate | — |
| `PicnikGrain` | **Filmszemcse** | Film Grain | — |
| `PicnikTint` | **Árnyalás** | Tint | — |
| `Pixelate` | **Képpontnagyítás** | Pixelate | — |
| `Polaroid` | **Polaroid** | Polaroid | — |
| `QuantizePalette` | **Poszterizálás** | Posterize | — |
| `radblur` | **Lágy fókusz** | Soft Focus | **Méret** *(Size)* · **Mennyiség** *(Amount)* |
| `radsat` | **Fókuszos FF** | Focal B&W | **Méret** *(Size)* · **Élesség** *(Sharpness)* |
| `radtint` | **Sugaras árnyalás** | Radial Tint | **Lágy perem** *(Feather)* |
| `rainbow` | **Szivárvány** | Rainbow | — |
| `ReanimatedEyeColor` | **Vámpírszem** | Ghoul Eye | — |
| `redeye` | **Vörösszem** | Red Eye | — |
| `retouch` | **Retusálások** | Retouches | — |
| `rot` | **Forgatás** | Rotate | — |
| `RoundedEdges` | **Kerekített élek** | Rounded Edges | — |
| `sat` | **Telítettség** | Saturation | **Mennyiség** *(Amount)* |
| `save` | **Mentés** | Save | — |
| `sepia` | **Szépia** | Sepia | — |
| `shadow` | **Árnyék és kiemelés** | Shadow & Highlight | **Sugár** *(Radius)* · **Árnyék %** *(Shadow %)* · **Kiemelés %** *(Highlight %)* |
| `Sixties` | **60-as évek** | 1960's | — |
| `Soften` | **Lágyítás** | Soften | — |
| `tilt` | **Kiegyenesítés** | Straighten | — |
| `tint` | **Árnyalás (régi)** | Tint (Old) | **Színek megőrzése** *(Color Preservation)* |
| `triple` | **Megvilágítási javítások** | Lighting Fixes | **Fényesség** *(Brightness)* · **Kontraszt** *(Contrast)* · **Derítőfény** *(Fill Light)* |
| `triple2` | **Megvilágítási javítások** | Lighting Fixes | **Derítőfény** *(Fill Light)* · **Feketepont** *(Black Point)* · **Fehérpont** *(White Point)* |
| `triple3` | **Megvilágítási javítások** | Lighting Fixes | **Derítőfény** *(Fill Light)* · **Kiemelések** *(Highlights)* · **Árnyékok** *(Shadows)* |
| `TwoTone` | **Kéttónusú** | Duo-Tone | — |
| `unsharp` | **Élesítés (régi)** | Sharpen (Old) | **Mennyiség** *(Amount)* |
| `unsharp2` | **Élesítés** | Sharpen | **Mennyiség** *(Amount)* |
| `Vignette` | **Vignetta** | Vignette | — |
| `warm` | **Melegítés** | Warmify | — |
| `whitept` | **Fehérpont** | Whitepoint | **Fehérpont színének kiválasztása** *(Choose Whitepoint Color)* |

### Buboréksúgók

- `ansel` — Olyan képet készít, amely úgy néz ki, mintha fekete-fehér filmmel és színes szűrővel készült volna *(Makes a photo that looks like it was taken with B&W film and a color filter)*
- `blur` — Lágyítja a fotót *(Softens your photo)*
- `Boost` — Színek kiemelése és a kontraszt növelése *(Bring out colors and increase contrast)*
- `Border` — Keret hozzáadása a fotóhoz *(Add a frame to your photo)*
- `bw` — Fekete-fehérré változtatja a fotót *(Makes your photo black and white)*
- `Cinemascope` — A klasszikus filmekhez hasonlóvá teszi a fotót *(Add a little classic movie magic)*
- `Comicize` — Képregényszerű stílus féltónussal *(Comic book style half-toning)*
- `CrossProcess` — Film keresztfeldolgozásának utánzása *(Mimics film cross-processing)*
- `dir_tint` — Fokozatos szűrő, hasznos az egeknél *(A graduated filter, useful for skies)*
- `DropShadow` — A fotó megjelenítése úgy, mintha a háttér előtt lebegne *(Make your photo appear to be floating slightly above the background)*
- `FocalZoom` — Egy központi területen kívül eső részek nagyítása *(Zoom everything outside a central area)*
- `glow` — Áttetsző ragyogást ad a fotónak *(Gives your photo a gauzy glow)*
- `glow2` — Áttetsző ragyogást ad a fotónak *(Gives your photo a gauzy glow)*
- `grain` — Filmszemcse hozzáadása *(Adds film grain)*
- `grain2` — Filmszemcse hozzáadása *(Adds film grain)*
- `HDR` — \"Nagy dinamikatartományú\" hatás emulálása *(Emulate that \"high dynamic range\" look)*
- `HeatMap` — A hőtérképszerű megjelenítést szimulálja *(Simulate heat vision)*
- `Holga` — Olyanná alakítja a fotót, mintha műanyag fényképezőgéppel készítették volna *(Make your photo look like it was taken with a plastic camera)*
- `Invert` — Negatívhoz hasonlóvá alakítja a fotót *(Make your photo look like a negative)*
- `IR` — A fekete-fehér infravörös filmet szimulálja *(Simulate black-and-white infrared film)*
- `LocalContrast` — A képrészletek kiemelése *(Brings out image details)*
- `Lomo` — A Lomo játék fényképezőgépet imitálja *(Imitate the Lomo toy camera)*
- `Matte` — A fotó széleinek világosítása *(Add a light glow to the edges of your photo)*
- `MuseumMatte` — Árnyékos matt keretet ad a fotónak *(Add a shadowed matte frame to your photo)*
- `Neon` — Neonhoz hasonlóvá alakítja a fotót *(Make your photo look like neon)*
- `NightVision` — Az infravörös éjjellátó kamerák képét utánzó hatás *(Mimics infrared night-vision cameras)*
- `Orton` — A Michael Orton-féle hatás utánzása *(Mimic Michael Orton's effect)*
- `PencilSketch` — Ceruzarajzhoz hasonlóvá teszi a fotót *(Make your photo look like it was drawn with a pencil)*
- `PicnikFocalPixelate` — Egy központi területen kívüli vagy belüli részek képpontnövelése *(Pixelate everything inside or outside a central area)*
- `PicnikGrain` — Filmszemcse szimulálása *(Simulate film grain)*
- `PicnikTint` — A fotó színének megváltoztatása *(Change the color of your photo)*
- `Pixelate` — A fotót "kockássá" és alacsony felbontásúvá alakítja *(Make your photo look blocky and low-res)*
- `Polaroid` — A fotót az azonnali előhívásúakhoz hasonló kinézetűvé alakítja *(Give your photo that instant-film look)*
- `QuantizePalette` — A színek számának csökkentése a fotón *(Reduce the number of colors in your photo)*
- `radblur` — Lágyítja a fókuszt egy középpont körül *(Softens focus around a center point)*
- `radsat` — Telítetlen egy középpont körül *(Desaturates around a center point)*
- `radtint` — Árnyalás egy középpont körül *(Tints around a central point)*
- `ReanimatedEyeColor` — A fotón a szemeket nem valódi megjelenésűvé alakítja *(Make the eyes in your photo look icky)*
- `RoundedEdges` — A fotó sarkainak lekerekítése *(Give your photo rounded corners)*
- `sat` — Telítettség növelése vagy csökkentése *(Increases or decreases saturation)*
- `sepia` — Átalakítja a fotót szépia tónusúvá *(Converts photo to sepia tone)*
- `Sixties` — Lekerekített sarkok és meleg, régies ragyogás *(Rounded corners and a warm, aged glow)*
- `Soften` — Lággyá és ragyogóvá alakítja a fotót *(Makes your photo soft and glowy)*
- `tint` — Árnyalt megjelenést ad *(Makes a tinted look)*
- `TwoTone` — Kétszínűvé konvertálja a fotót *(Convert your photo to two colors)*
- `unsharp` — A fotó széleinek élesítése *(Sharpens edges in your photo)*
- `unsharp2` — A fotó széleinek élesítése *(Sharpens edges in your photo)*
- `Vignette` — Besötétíti a fotó széleit *(Darken the edges of your photo)*
- `warm` — A meleg tónusok erősítésével javítja a bőr tónusait *(Improves skintones by boosting warm tones)*

# Az effekt-vezérlők feliratai — a Picasa saját szótára

Az eredeti Picasa `Picasa3i18n.dll`-jének `ImageFilters` osztálya. **69 felirat**,
41 nyelven; itt az angol kulcsszöveg és az eredeti magyar fordítás.

## Hogyan kapcsolódik a `filterdesc.xml`-hez

A `filterdesc.xml`-ben minden vezérlő azonosítója `_sldrXxx` (csúszka),
`_cpkrXxx` (színválasztó), `_clrsw` (színminta), `_chkXxx` (jelölő) alakú.

| azonosító-előtag | mire | példa |
|---|---|---|
| `_sldr` | csúszka | `_sldrBloom` → `Bloom` → **Hamvasság** |
| `_cpkr` | színválasztó | `_cpkrOuter` → `OuterColor` → **Külső szín** |
| `_clrsw` | színminta | effektfüggő (`Vignette` → `VignetteColor`) |
| `_chk` | jelölő | `_chkReverse` → `Reverse` → **Megfordítás** |
| `_msk` | festhető maszk | nincs saját felirat |

> ⚠️ **Az `_sldrXxx` → `ImageFilters::Xxx` leképezés NEM 1:1** — öt vezérlőnél
> a felirat attól függ, MELYIK effekt panelján ül. A pontos döntési fa a
> következő szakaszban; a naiv szabály öt effektnél téves feliratot ad.

## A feloldás az EXE-ben van, és részben effektfüggő (#709)

A vezérlő-azonosítóból a `Picasa3i18n` erőforráskulcsot **nem** a
`filterdesc.xml` adja, hanem három beégetett döntési fa a `Picasa3.exe`-ben
(image base `0x00400000`, Picasa 3.9.141.259,
`sha256:644b7bec…93ddc96` — ugyanaz a bináris, mint a
`referencia/binary-index/picasa3-index.sqlite`-é):

| függvény | mit old fel | hány kulcs |
|---|---|---|
| `0x008fcfa0` (6665 bájt) | csúszkák (`_sldr*`) | 50 |
| `0x008fe9b0` (1224 bájt) | jelölők, rádiógombok (`_chk*`, `_radio*`, `cbLetterbox`) | 8 |
| `0x008fee80` (1737 bájt) | színválasztók, színminta (`_cpkr*`, `_clrsw`) | 11 |

A kódot megelőző adatblokk hármasokban áll (`0x00cd09b8`-tól):
**vezérlő-azonosító · angol tartalék-felirat · erőforráskulcs**. Ahol egy
azonosítóhoz több hármas tartozik, ott a függvény **az effekt `filterdesc.xml`-beli
`id`-jére hasonlít rá** (`repe cmpsb`), és annak alapján választ.

### A négy effektfüggő csúszka

| vezérlő | effekt (`filter id`) | angol felirat | magyar | cím |
|---|---|---|---|---|
| `_sldrBlur` | **Holga** | Blur Edges | **Élhomályosítás** | `0x008fd249` → `0x008fd286` |
| `_sldrBlur` | **Lomo** | Blur Edges | **Élhomályosítás** | `0x008fd2b7` → `0x008fd2f4` |
| `_sldrBlur` | *minden más* (DropShadow, Matte, Vignette, ReanimatedEyeColor) | Size | **Méret** | `0x008fd316` |
| `_sldrContrast` | **HDR** | Strength | **Erősség** | `0x008fd8ff` → `0x008fd8ed` |
| `_sldrContrast` | **PencilSketch** | Strength | **Erősség** | `0x008fd96d` → `0x008fd95b` |
| `_sldrContrast` | *minden más* (LocalContrast, NightVision, TwoTone) | Contrast | **Kontraszt** | `0x008fd97d` |
| `_sldrImpact` | **PicnikFocalPixelate**, **Pixelate** | Pixel Size | **Képpontméret** | `0x008fdeda`, `0x008fdf30` → `0x008fdf6d` |
| `_sldrImpact` | **FocalZoom** | Zoominess | **Suhanás** | `0x008fdfbb` → `0x008fe02a` |
| `_sldrImpact` | **Soften** | Softness | **Lágyítás** | `0x008fe00a` → `0x008fe098` |
| `_sldrImpact` | **Boost** | Strength | **Erősség** | `0x008fe078` → `0x008fe0f2` |
| `_sldrImpact` | *minden más* | Impact | **Hatás** | `0x008fe0d4` |
| `_sldrRadius` | **PicnikFocalPixelate**, **FocalZoom** | Focal Size | **Fókuszméret** | `0x008fe38b`, `0x008fe3de` → `0x008fe3e7` |
| `_sldrRadius` | *minden más* (HDR, LocalContrast, PencilSketch) | Radius | **Sugár** | `0x008fe405` |

### Az effektfüggő színminta (`_clrsw`)

| effekt | angol felirat | magyar | cím |
|---|---|---|---|
| Polaroid, RoundedEdges, Sixties | Background Color | **Háttérszín** | `0x008feed8` |
| Matte | Matte Color | **Matt szín** | `0x008ff072` |
| Vignette | Vignette Color | **Vignetta színe** | `0x008ff104` |
| Neon | Neon Color | **Neonszín** | `0x008ff193` |
| PicnikTint (`Tint`) | Tint Color | **Tinta színe** | `0x008ff1f2` |
| *minden más* | Pick Color | **Színválasztás** | — |

A `_cpkr*` színválasztók ezzel szemben feltétel nélküliek
(`_cpkrOuter`/`Inner`/`Shadow`/`Background`/`Black`/`White`).

### Álnevek (ugyanaz a felirat több azonosítóra)

| azonosítók | közös kulcs | magyar |
|---|---|---|
| `_sldrStr`, `_sldrStrength` | `Strength` | **Erősség** |
| `_sldrColor`, `_sldrColorStrength` | `ColorStrength` | **Színerő** |
| `_sldrBrushSize`, `_brshbtn` (csúszkaként) | `BrushSize` | **Ecsetméret** |

Egy eltérés a puszta névegyezéstől: `_sldrHardness` → `EdgeHardness`
(**Élkeménység**).

*Bizonyítottsági fok: megerősített* — a döntési ágak visszakereshető címmel,
a `Picasa3.exe` diszasszemblált `0x008fcfa0` / `0x008fee80` függvényeiből.

## A teljes szótár

| kulcs | angol | magyar |
|---|---|---|
| `Amount` | Amount | **Mennyiség** |
| `Angle` | Angle | **Szög** |
| `BackgroundColor` | Background Color | **Háttérszín** |
| `BlackColor` | First Color | **Első szín** |
| `Blacks` | Darkness | **Sötétség** |
| `BlendMode` | Blend Mode | **Keverési mód** |
| `Bloom` | Bloom | **Hamvasság** |
| `Blur` | Size | **Méret** |
| `Blur1` | Glow | **Ragyogás** |
| `BlurEdges` | Blur Edges | **Élhomályosítás** |
| `BlurX` | Horizontal Blur | **Vízszintes homályosítás** |
| `BlurXY` | Color Brush | **Színes ecset** |
| `BlurY` | Vertical Blur | **Függőleges homályosítás** |
| `BorderAmount` | Border Amount | **Szegély mennyisége** |
| `Brightness` | Brightness | **Fényerő** |
| `BrushSize` | Brush Size | **Ecsetméret** |
| `CaptionHeight` | Caption Height | **Képfelirat magassága** |
| `ColorOverride` | Color Override | **Színfelülírás** |
| `ColorStrength` | Color Strength | **Színerő** |
| `Contrast` | Contrast | **Kontraszt** |
| `CornerRadius` | Corner Radius | **Sarok sugara** |
| `Darken` | Darken | **Sötétítés** |
| `Definition` | Definition | **Maszatolás** |
| `Distance` | Distance | **Távolság** |
| `DotContrast` | Dot Density | **Pontsűrűség** |
| `DotFade` | Dot Fade | **Ponthalványítás** |
| `EdgeHardness` | Edge Hardness | **Élkeménység** |
| `Eraser` | Eraser | **Radír** |
| `Exposure` | Exposure | **Exponálás** |
| `Fade` | Fade | **Fokozat** |
| `Filter` | Number of Stars | **Csillagok száma** |
| `FocalSize` | Focal Size | **Fókuszméret** |
| `Grain` | Grain | **Szemcsésség** |
| `Hue` | Hue | **Színezet** |
| `Impact` | Impact | **Hatás** |
| `InnerColor` | Inner Color | **Belső szín** |
| `InnerThickness` | Inner Thickness | **Belső keret** |
| `Intensity` | Intensity | **Intenzitás** |
| `Letterbox` | Letterbox | **Postaláda** |
| `Lighten` | Lighten | **Világosítás** |
| `MatteColor` | Matte Color | **Matt szín** |
| `NeonColor` | Neon Color | **Neonszín** |
| `OuterColor` | Outer Color | **Külső szín** |
| `OuterThickness` | Outer Thickness | **Külső keret** |
| `PickColor` | Pick Color | **Színválasztás** |
| `Pinkness` | Pink-ness | **Rózsaszín hatás** |
| `PixelSize` | Pixel Size | **Képpontméret** |
| `Radius` | Radius | **Sugár** |
| `Reverse` | Reverse | **Megfordítás** |
| `Rotate` | Rotate | **Forgatás** |
| `Rotation` | Rotation | **Forgatás** |
| `RoundedCorners` | Rounded Corners | **Sarkok lekerekítése** |
| `Screen` | Lighten | **Világosítás** |
| `Selected` | Selected | **Kijelölve** |
| `ShadowColor` | Shadow Color | **Árnyékszín** |
| `Smoothing` | Detail | **Részletek** |
| `Softness` | Softness | **Lágyítás** |
| `Steps` | Number of Colors | **Színek száma** |
| `Strength` | Strength | **Erősség** |
| `Thin` | Thin | **Vékony** |
| `Threshold` | Threshold | **Küszöbérték** |
| `TintColor` | Tint Color | **Tinta színe** |
| `Tone` | Tone | **Tónus** |
| `TransparentBackground` | Transparent Background | **Átlátszó háttér** |
| `TransparentCorners` | Transparent Corners | **Átlátszó sarkok** |
| `Vibrance` | Vibrance | **Vibrálás** |
| `VignetteColor` | Vignette Color | **Vignetta színe** |
| `WhiteColor` | Second Color | **Második szín** |
| `Zoominess` | Zoominess | **Suhanás** |

## Miért ez az igazságforrás

A vezérlő-feliratokat **nem szabad kitalálni**: több eredeti elnevezés nem
magától értetődő, és a felhasználó a régi programból ezeket ismeri. Néhány
jellegzetes eset:

- `Blur` felirata **Méret**, nem „homályosítás" — a méretet állítja. De a
  **Holga** és a **Lomo** paneljén ugyanez a csúszka **Élhomályosítás**
  (ld. a döntési fát fent).
- `Smoothing` felirata **Részletek** — a nagyobb érték több részletet jelent.
- `Steps` felirata **Színek száma**, `Filter`-é **Csillagok száma**.
- `Fade` felirata **Fokozat** — ez a legtöbb Glimmer-effekt erősség-csúszkája.
- `Bloom` → **Hamvasság**, `Definition` → **Maszatolás**,
  `Zoominess` → **Suhanás**, `Letterbox` → **Postaláda**.

Forrás: a Picasa 3.9 `Picasa3i18n.dll` `stringres` szekciója.
